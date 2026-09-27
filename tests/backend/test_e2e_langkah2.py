"""Skenario e2e Langkah 2 — brief BLOCKED → pengganti → review → report tuntas.

Langkah LLM disimulasikan dengan suntingan berkas; tiap vonis dibaca dari skrip
yang benar-benar dikirim ke user. Nomor langkah mengikuti tabel skenario di
`issues/02-backenddev-jalan-buntu.md`.
"""
import json

from conftest import BE_SKILLS, TD, be_checks, be_run, brief, commit, git, write_files, load_module

bs = load_module(BE_SKILLS / "_common" / "brief_status.py", "be_brief_status")

def _spec_path(repo):
    """Spec batch di laci `.explore/` taskdir — satu-satunya lokasi yang diterima scaffold (B11)."""
    path = repo / TD / ".explore" / "brief-spec.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


ARCH = "architect/scripts/check_preconditions.py"
REPORT = "report/scripts/check_preconditions.py"
SCAFFOLD = "plan/scripts/scaffold_brief.py"
LEDGER_DONE = "- [x] BRIEF — backend:plan → brief-*.md @ READY 1111111\n"
TASK = ("---\nchain: BRIEF\nlane: DIRECT_BRIEF\nrisk: MINOR\nstatus: ACTIVE\n---\n# Order fix\n\n## Chain\n\n{ledger}\n"
        "## Success Criteria\n\n- [ ] **SC-1**: lock\n- [ ] **SC-2**: endpoint\n\n## Out of Scope\n\n- x — y\n")


def _obj(fulfills):
    return f"# Brief\n## Objective\nCovers: — (PRD absen)\nFulfills: {fulfills}\n"


def _row(nn, unit, **extra):
    return {"nn": nn, "unit": unit, "title": unit, "risk": "MINOR", "fulfills": ["SC-2"],
            "commit_type": "fix", "domain": "order", **extra}


def _implement(repo, name, line):
    bs.set_frontmatter(repo / TD / name, status="DONE")
    write_files(repo, {"src/order.go": (repo / "src/order.go").read_text() + line})
    msg = bs.read_frontmatter(repo / TD / name)["commit_message"]
    commit(repo, msg, "src/order.go", f"{TD}/{name}")


def _fixture(repo):
    """Langkah 0: 01 DONE, 02 BLOCKED (wip + report-02.md), 03 READY, ledger BRIEF [x], tanpa `.explore/`."""
    write_files(repo, {f"{TD}/TASK.md": TASK.format(ledger=LEDGER_DONE)})
    git(repo, "checkout", "-q", "-b", "fix/order")
    brief(repo, "01", "lock", "READY", body=_obj("SC-1"))
    commit(repo, "docs(plan): add 1 briefs for order-fix", f"{TD}/brief-01-lock.md")
    _implement(repo, "brief-01-lock.md", "// lock\n")
    brief(repo, "02", "endpoint", "BLOCKED", body=_obj("SC-2"))
    brief(repo, "03", "recap", "READY", body=_obj("SC-2"))
    write_files(repo, {f"{TD}/report-02.md": "# BLOCKED\nstop condition (d): berkas fiktif\n"})
    commit(repo, "wip(order): brief-02-endpoint [BLOCKED]")
    assert not (repo / TD / ".explore").exists()


def _through_review(repo):
    _fixture(repo)
    # 1 — architect menolak BLOCKED walau brief READY menyusul (L2.2)
    c3 = be_checks(repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "FAIL" and c3["summary"] == "Brief BLOCKED menahan rantai: brief-02-endpoint.md"
    # 2 — gerbang re-entry lolos
    tl = be_checks(repo, "tech-lead/scripts/check_preconditions.py", "--re-entry")
    assert all(c["status"] == "PASS" for c in tl.values()), [c for c in tl.values() if c["status"] != "PASS"]
    # 3 — analyst resume tanpa `task`, buka [~] BRIEF dan naikkan counter reentry (L2.5, L2.13)
    c7 = be_checks(repo, "analyst/scripts/check_preconditions.py", "--taskdir", TD, "--risk", "MINOR")[7]
    assert c7["summary"].startswith("Resume: ledger tercentang penuh — butuh reentry_reason")
    assert be_run(repo, "analyst/scripts/chain_counters.py", "--taskdir", TD, "--bump", "reentry").returncode == 0
    task = repo / TD / "TASK.md"
    task.write_text(task.read_text().replace(
        LEDGER_DONE, "- [~] BRIEF — backend:plan → brief-*.md @ re-entry 1 (was 1111111)\n"))
    commit(repo, "docs(order-fix): re-entry hop BRIEF ke-1", f"{TD}/TASK.md")
    # 4 — pengganti 02 saja ditolak: 03 READY akan berjalan lebih dulu (D2-A)
    spec = _spec_path(repo)
    spec.write_text(json.dumps({"briefs": [_row("04", "endpoint-fix", supersedes=["02"])]}))
    out = be_run(repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--append", "--spec", str(spec))
    assert out.returncode == 1 and "brief READY hilir brief-03" in out.stdout
    # 5 — dengan terbit ulang 03 lolos; matriks lama direkonstruksi dari disk (L2.7)
    spec.write_text(json.dumps({"briefs": [_row("04", "endpoint-fix", supersedes=["02"]),
                                           _row("05", "recap", supersedes=["03"])]}))
    out = be_run(repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--append", "--spec", str(spec))
    assert out.returncode == 0 and "direkonstruksi dari brief di disk" in out.stdout, out.stdout
    # 6 — kerangka pengganti menulis transisi SUPERSEDED dua arah
    for nn in ("04", "05"):
        assert be_run(repo, SCAFFOLD, "--taskdir", TD, "--nn", nn).returncode == 0
    fm = {b["nn"]: b for b in bs.scan_briefs(repo / TD)}
    assert fm["02"]["status"] == fm["03"]["status"] == "SUPERSEDED"
    assert fm["02"]["superseded_by"] == ["04"] and fm["05"]["supersedes"] == ["03"]
    # 7 — validate_briefs: Check C lolos tautan, G tidak menghitung 02/03
    checks = {c["id"]: c for c in json.loads(be_run(repo, "plan/scripts/validate_briefs.py",
                                                    "--taskdir", TD, "--json").stdout)["checks"]}
    assert not any("SUPERSEDED" in d for d in checks["C"]["details"]), checks["C"]
    assert not any("brief terbit `READY`" in d for d in checks["S"]["details"])
    assert checks["G"]["status"] == "PASS", checks["G"]
    # 8 — commit agregat plan; predikat E: READY/DONE/SUPERSEDED bertaut
    commit(repo, "docs(plan): add 2 briefs for order-fix", *(f"{TD}/{b['name']}" for b in fm.values()))
    assert bs.validate_links(bs.scan_briefs(repo / TD)) == []
    # 9 — architect mulai di brief-04, tanpa HALT.md
    checks = be_checks(repo, ARCH, "--taskdir", TD)
    assert checks[3]["entry"] == "FASE_3:04" and checks[7]["status"] == "PASS"
    # 10 — implementor 04 dan 05 DONE
    _implement(repo, "brief-04-endpoint-fix.md", "// endpoint fix\n")
    _implement(repo, "brief-05-recap.md", "// recap\n")
    assert be_checks(repo, ARCH, "--taskdir", TD)[3]["entry"] == "FASE_4"
    # 11 — reviewer meng-commit REVIEW.md + indeks issues (L2.1)
    write_files(repo, {f"{TD}/REVIEW.md": "---\nhighest: CLEAN\n---\n# Review\n",
                       "backenddev/issues/README.md": "# Issues Index\n| Date | Issue ID | Target | Severity | Status |\n"})
    commit(repo, "docs(order-fix): add final review report", f"{TD}/REVIEW.md", "backenddev/issues/README.md")
    assert git(repo, "status", "--porcelain") == ""
    assert be_checks(repo, ARCH, "--taskdir", TD)[3]["entry"] == "FASE_5"


def test_blocked_supersede_review_report(chain_repo):
    repo = chain_repo
    _through_review(repo)
    # 12 — report 7/7, check 4 menghitung SUPERSEDED
    checks = be_checks(repo, REPORT, "--taskdir", TD)
    assert all(c["status"] == "PASS" for c in checks.values()), checks
    assert checks[4]["summary"] == "3 DONE · 2 SUPERSEDED"
    # 13 — REPORT.md terbit → TUNTAS
    write_files(repo, {f"{TD}/REPORT.md": "# Report\n"})
    commit(repo, "docs(order-fix): add chain report")
    assert be_checks(repo, ARCH, "--taskdir", TD)[3]["entry"] == "TUNTAS"


def test_brief_after_review_makes_it_stale(chain_repo):
    """14 — varian negatif: commit brief baru sesudah review → REVIEW basi (L2.3)."""
    repo = chain_repo
    _through_review(repo)
    brief(repo, "06", "audit-log", "DONE", body=_obj("— (berkas yatim)"))
    write_files(repo, {"src/audit.go": "package order\n"})
    commit(repo, "fix(order): implement audit-log")
    c3 = be_checks(repo, ARCH, "--taskdir", TD)[3]
    assert c3["entry"] == "FASE_4" and "REVIEW.md basi" in c3["summary"]
    assert be_checks(repo, REPORT, "--taskdir", TD)[3]["status"] == "FAIL"
