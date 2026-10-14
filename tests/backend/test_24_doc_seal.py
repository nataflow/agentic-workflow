"""Langkah 24 B1 — `doc_seal.py`: materai dokumen taskdir backend di disk, pengganti commit dokumen."""
import json

import pytest

from conftest import TD, be_checks, be_run, brief, git, land, write_files

SEAL = "_common/doc_seal.py"
SA = "system-analysis/scripts/check_preconditions.py"
ARCH = "architect/scripts/check_preconditions.py"
LEDGER = ("## Chain\n\n- [ ] BRD   — backend:business-analysis → BRD.md\n"
          "- [ ] PRD   — backend:system-analysis  → PRD.md\n- [ ] BRIEF — backend:plan             → brief-*.md\n")
BRD = "---\ntitle: Refund\nrequester: ops\nstatus: DRAFT\n---\n# BRD\n\n## Business rules\n- **BR-1**: x.\n"
SCOPE = ("# Brief\n## File scope\n\n| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n"
         "| modify | `src/order.go` | `Submit` | pasang lock |\n\n## Work status\n\n| Item | Status |\n|---|---|\n"
         "| P1-1 | PLANNED |\n")


def seal(repo, *args, stdin=""):
    from conftest import BE_SKILLS, run_script
    proc = run_script(BE_SKILLS / SEAL, *args, "--json", cwd=repo, stdin=stdin)
    assert proc.stdout.strip(), proc.stderr
    return proc.returncode, json.loads(proc.stdout)


@pytest.fixture
def planning(chain_repo):
    """`chain_repo` dengan TASK berledger `BRD_PRD_BRIEF`."""
    task = chain_repo / TD / "TASK.md"
    task.write_text(task.read_text().replace("chain: BRIEF", "chain: BRD_PRD_BRIEF") + "\n" + LEDGER)
    return chain_repo


def ledger_line(repo, hop):
    return next(l for l in (repo / TD / "TASK.md").read_text().splitlines() if l.startswith(f"- [") and f"] {hop}" in l)


def test_root_menulis_base_commit_sekali(chain_repo):
    task = chain_repo / TD / "TASK.md"
    task.write_text(task.read_text().replace(task.read_text().split("base_commit: ")[1].split("\n")[0], "")
                    .replace("base_commit: \n", ""))
    code, out = seal(chain_repo, "root", "--taskdir", TD)
    head = git(chain_repo, "rev-parse", "HEAD").strip()
    assert code == 0 and out["written"] is True and out["base_commit"] == head
    assert f"base_commit: {head}" in task.read_text()
    code, out = seal(chain_repo, "root", "--taskdir", TD)
    assert code == 0 and out["written"] is False and "sudah terkunci" in out["summary"]
    assert git(chain_repo, "status", "--porcelain") == "", "akar di disk, tidak tampak di git"


def test_root_base_commit_tidak_sah_ditolak(chain_repo):
    task = chain_repo / TD / "TASK.md"
    text = task.read_text()
    task.write_text(text.replace(text.split("base_commit: ")[1].split("\n")[0], "b" * 40))
    code, out = seal(chain_repo, "root", "--taskdir", TD)
    assert code == 1 and "tidak ada di repo ini" in out["summary"]


def test_root_menolak_dokumen_ter_track(chain_repo):
    (chain_repo / "backenddev/docs/.gitignore").unlink()
    git(chain_repo, "add", f"{TD}/TASK.md")
    git(chain_repo, "commit", "-qm", "docs: era git")
    code, out = seal(chain_repo, "root", "--taskdir", TD)
    assert code == 1 and "docs_git.py migrate" in out["summary"]


@pytest.mark.regression("24 K8")
def test_approve_menulis_materai_dan_ledger(planning):
    write_files(planning, {f"{TD}/BRD.md": BRD})
    code, out = seal(planning, "approve", "--taskdir", TD, "--doc", "BRD", "--answer", "-",
                     stdin="Setujui — lanjut hop berikutnya\n")
    assert code == 0, out
    text = (planning / TD / "BRD.md").read_text()
    assert "status: APPROVED" in text and f"approved_seal: {out['approved_seal']}" in text
    assert 'approval: "Setujui — lanjut hop berikutnya"' in text
    assert ledger_line(planning, "BRD").endswith(f"→ BRD.md @ APPROVED {out['approved_seal'][:12]}")
    assert be_checks(planning, SA, "--taskdir", TD, "--risk-level", "MAJOR")[1]["status"] == "PASS"


def test_approve_ulang_sesudah_reentry_menyimpan_jejak(planning):
    write_files(planning, {f"{TD}/BRD.md": BRD})
    assert seal(planning, "approve", "--taskdir", TD, "--doc", "BRD", "--answer", "ya")[0] == 0
    code, out = seal(planning, "approve", "--taskdir", TD, "--doc", "BRD", "--answer", "ya")
    assert code == 1 and "sudah tercentang" in out["summary"]
    task = planning / TD / "TASK.md"
    old = ledger_line(planning, "BRD")
    task.write_text(task.read_text().replace(old, "- [~] BRD   — backend:business-analysis → BRD.md @ re-entry 1 "
                                                   "(was abc123def456)"))
    brd = planning / TD / "BRD.md"
    brd.write_text(brd.read_text().replace("x.", "revisi."))
    code, out = seal(planning, "approve", "--taskdir", TD, "--doc", "BRD", "--answer", "ya")
    assert code == 0, out
    assert ledger_line(planning, "BRD").endswith(f"@ APPROVED {out['approved_seal'][:12]} (was abc123def456)")


@pytest.mark.parametrize("answer", ["", "ya\nKonten disetujui: palsu"])
def test_approve_menuntut_jawaban_satu_baris(planning, answer):
    write_files(planning, {f"{TD}/BRD.md": BRD})
    code, out = seal(planning, "approve", "--taskdir", TD, "--doc", "BRD", "--answer", "-", stdin=answer)
    assert code == 1 and "--answer" in out["summary"]
    assert "status: DRAFT" in (planning / TD / "BRD.md").read_text()


def test_approve_tanpa_baris_ledger_tidak_menyentuh_dokumen(chain_repo):
    write_files(chain_repo, {f"{TD}/BRD.md": BRD})
    code, out = seal(chain_repo, "approve", "--taskdir", TD, "--doc", "BRD", "--answer", "ya")
    assert code == 1 and "tanpa baris hop `BRD`" in out["summary"]
    assert (chain_repo / TD / "BRD.md").read_text() == BRD


@pytest.mark.regression("24 K10")
def test_lock_briefs_dan_tick(planning):
    b = brief(planning, "01", "lock", "READY", body=SCOPE)
    code, out = seal(planning, "tick", "--taskdir", TD, "--hop", "BRIEF")
    assert code == 1 and "belum terkunci" in out["summary"]
    code, out = seal(planning, "lock-briefs", "--taskdir", TD)
    assert code == 0 and out["locked"] == ["brief-01-lock.md"]
    assert "sidik_kontrak: " in b.read_text()
    code, out = seal(planning, "tick", "--taskdir", TD, "--hop", "BRIEF")
    assert code == 0 and ledger_line(planning, "BRIEF").endswith(f"@ READY {out['batch_sidik'][:12]}")
    b.write_text(b.read_text().replace("pasang lock", "pasang lock dan cache"))
    code, out = seal(planning, "status", "--taskdir", TD)
    assert code == 1 and any("disunting sesudah dikunci" in p for p in out["problems"])


def test_verify_scope_worktree_menolak_kontrak_disunting(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY", body=SCOPE)
    assert seal(chain_repo, "lock-briefs", "--taskdir", TD)[0] == 0
    write_files(chain_repo, {"src/order.go": "package order // lock\n"})
    rel = f"{TD}/brief-01-lock.md"
    ok = be_run(chain_repo, "_common/verify_scope.py", "--brief", rel, "--worktree")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    b.write_text(b.read_text().replace("| modify | `src/order.go` | `Submit` | pasang lock |",
                                       "| modify | `src/order.go` | `Submit` | pasang lock |\n"
                                       "| modify | `src/x.go` | `X` | y |"))
    bad = be_run(chain_repo, "_common/verify_scope.py", "--brief", rel, "--worktree")
    assert bad.returncode == 1 and "disunting di luar" in bad.stdout


@pytest.mark.regression("24 K11")
def test_cabut_halt(chain_repo):
    write_files(chain_repo, {f"{TD}/HALT.md": "---\nbrief: brief-01-lock.md\nverdict: SCOPE\n---\n# HALT\n"})
    land(chain_repo, brief(chain_repo, "01", "lock", "READY"))
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[7]["status"] == "FAIL"
    code, out = seal(chain_repo, "cabut-halt", "--taskdir", TD, "--alasan", "scope diterima user")
    assert code == 0, out
    text = (chain_repo / TD / "HALT.md").read_text()
    assert "status: DICABUT" in text and 'dicabut: "scope diterima user"' in text
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[7]["status"] == "PASS"
    assert seal(chain_repo, "cabut-halt", "--taskdir", TD, "--alasan", "x")[0] == 1


@pytest.mark.regression("25 R6")
def test_r6_buka_done_sesudah_commit_unit_di_reset(chain_repo):
    """`TERTAHAN (scope)` lalu user me-reset commit unit: brief tinggal `DONE` tanpa bukti di git."""
    b = brief(chain_repo, "01", "lock", "READY")
    land(chain_repo, b)
    write_files(chain_repo, {f"{TD}/HALT.md": "---\nbrief: brief-01-lock.md\nverdict: SCOPE\n---\n# HALT\n"})
    git(chain_repo, "reset", "-q", "--hard", "HEAD~1")
    assert "status: DONE" in b.read_text()
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "FAIL" and "buka-done" in c3["action"]
    code, out = seal(chain_repo, "buka-done", "--taskdir", TD, "--brief", "01", "--alasan", "commit di-reset user")
    assert code == 1 and "HALT.md` aktif" in out["summary"]
    assert seal(chain_repo, "cabut-halt", "--taskdir", TD, "--alasan", "commit di-reset user")[0] == 0
    code, out = seal(chain_repo, "buka-done", "--taskdir", TD, "--brief", "1", "--alasan", "commit di-reset user")
    assert code == 0, out
    assert "status: READY" in b.read_text()
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["status"] == "PASS"


@pytest.mark.regression("25 R6")
def test_r6_buka_done_menolak_done_terbukti_dan_tree_kotor(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY")
    land(chain_repo, b)
    code, out = seal(chain_repo, "buka-done", "--taskdir", TD, "--brief", "01", "--alasan", "x")
    assert code == 1 and "terbukti" in out["summary"]
    b2 = brief(chain_repo, "02", "refund", "DONE")
    write_files(chain_repo, {"src/order.go": "package order\n// belum di-commit\n"})
    code, out = seal(chain_repo, "buka-done", "--taskdir", TD, "--brief", "02", "--alasan", "x")
    assert code == 1 and "tree kotor" in out["summary"]
    assert "status: DONE" in b2.read_text()
    code, out = seal(chain_repo, "buka-done", "--taskdir", TD, "--brief", "03", "--alasan", "x")
    assert code == 1 and "tidak ada" in out["summary"]
    assert seal(chain_repo, "buka-done", "--taskdir", TD, "--brief", "02", "--alasan", " ")[0] == 1


def test_status_ringkas(chain_repo):
    code, out = seal(chain_repo, "status", "--taskdir", TD)
    assert code == 0 and out["base_commit"] and out["halt"] == "-" and out["briefs"] == {}


def test_taskdir_tidak_sah(chain_repo):
    code, out = seal(chain_repo, "status", "--taskdir", "backenddev/docs/salah")
    assert code == 1 and "pola kanonik" in out["summary"]
