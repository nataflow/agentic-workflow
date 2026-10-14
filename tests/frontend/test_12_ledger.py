"""Regresi 12 Tahap 4 — ledger & state `frontend` (J42–J53), di atas `## Riwayat Rantai` (Langkah 24).

Plafon ronde hilir tidak dibuka ulang oleh reopen/eskalasi hulu (J42); `draft` ulang me-reset hitungan
revisi dan reopen BRIEF tak terlihat penghitungnya (J43); ledger tidak tahan rebase dan rantai TUNTAS yang
di-squash divonis DRIFT (J44); `record` menerima laporan reviewer ronde lama (J45); materai approve dapat
diketik tangan atau disisipkan lewat `--answer` (J46); `reopen` membawa suntingan akar menggantung (J47); brief
`BLOCKED` dihidupkan lewat reopen (J48); slug kembar (J49); status akar asing (J50); subperintah atas taskdir
yang ditutup (J51); `.bak` pada `save` pertama (J52); path taskdir dan verdict REVIEW asing di `taskdir_state`
(J53). Dokumen taskdir tidak di-commit: jejak yang dulu diuji di riwayat git kini diuji di Riwayat.
"""
import json

import pytest

from conftest import FE_MINOR_TD, FE_TD, commit, fe_approved_chain, fe_brief, fe_draft, fe_round, fe_run, git, \
    load_module, FE_SKILLS, write_files

TASK = f"{FE_TD}/TASK.md"
CONTRACT = f"{FE_TD}/CONTRACT.md"
B1 = f"{FE_TD}/brief-01-orders-lacak-button.md"
REVIEW_PLAN = f"{FE_TD}/REVIEW-PLAN.md"
STATE = f"{FE_TD}/.explore/contract-review-state.json"


def chain(repo, *args, td=FE_TD):
    return fe_run(repo, "_common/chain.py", *args, "--taskdir", td)


def rr(repo, *args, gate="contract"):
    return fe_run(repo, "_common/review_round.py", *args, "--taskdir", FE_TD, "--gate", gate)


def state(repo, *args):
    return fe_run(repo, "lead/scripts/taskdir_state.py", "--root", str(repo), *args)


def approve(repo, row="CONTRACT", answer="Setujui"):
    return chain(repo, "approve", "--row", row, "--answer", answer)


def edit(repo, rel, old, new):
    p = repo / rel
    text = p.read_text(encoding="utf-8")
    assert old in text, (rel, old)
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def ok(proc):
    assert proc.returncode == 0, proc.out
    return proc


def contract_approved(repo):
    """CONTRACT disetujui lewat jalur SKILL; brief belum ditulis."""
    fe_round(repo)
    ok(fe_draft(repo))
    ok(approve(repo))


def contract_revise(repo, text):
    edit(repo, CONTRACT, "ambil status.", text)
    fe_round(repo)
    ok(fe_draft(repo))


def unit_blocked(repo):
    """brief-01 `BLOCKED` beserta `report-01.md`, suntingan disk milik architect (tanpa commit, Langkah 24)."""
    fe_brief(repo, "01", status="BLOCKED")
    write_files(repo, {f"{FE_TD}/report-01.md":
                       '---\nartifact: UNIT_REPORT\nunit: "01"\nstatus: BLOCKED\n---\n\n# Unit 01\n\n## Triase\n- galat\n'})


def riwayat(repo):
    return [l for l in (repo / TASK).read_text(encoding="utf-8").split("## Riwayat Rantai", 1)[1].splitlines()
            if l.startswith("- ")]


# ------------------------------------------------------------------ J42


@pytest.mark.regression("J42")
def test_j42_reopen_contract_membuka_putaran_plan(fe_chain_repo):
    repo = fe_chain_repo
    contract_approved(repo)
    fe_brief(repo, "01")
    fe_round(repo, "BLOCKED", gate="plan", semantic=1)
    fe_round(repo, "BLOCKED", gate="plan", semantic=1)
    assert rr(repo, "open", gate="plan").returncode == 1               # plafon putaran habis
    ok(chain(repo, "reopen", "--row", "CONTRACT", "--reason", "DTO kurang (BLOCKER plan)"))
    contract_revise(repo, "ambil status lacak.")
    ok(approve(repo))
    r = rr(repo, "open", gate="plan")
    assert r.returncode == 0, r.out


@pytest.mark.regression("J42")
def test_j42_eskalasi_membuka_putaran_contract(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo, "BLOCKED", semantic=1)
    fe_round(repo, "BLOCKED", semantic=1)
    assert rr(repo, "open").returncode == 1
    ok(chain(repo, "escalate", "--lane", "FULL_PIPELINE", "--sections", "flow,architecture",
             "--reason", "contract menemukan alur baru"))
    r = rr(repo, "open")
    assert r.returncode == 0, r.out


@pytest.mark.regression("25 R3")
@pytest.mark.parametrize("reason", ["", "   "])
def test_r3_eskalasi_alasan_kosong_ditolak_tanpa_merusak_riwayat(fe_chain_repo, reason):
    repo = fe_chain_repo
    before = (repo / TASK).read_text(encoding="utf-8")
    r = chain(repo, "escalate", "--lane", "FULL_PIPELINE", "--sections", "flow,architecture", "--reason", reason)
    assert r.returncode == 1 and "`--reason` kosong" in r.out
    assert (repo / TASK).read_text(encoding="utf-8") == before
    ok(chain(repo, "escalate", "--lane", "FULL_PIPELINE", "--sections", "flow,architecture",
             "--reason", "contract menemukan alur baru"))
    s = state(repo, "--json")
    assert "RUSAK" not in s.out


# ------------------------------------------------------------------ J43


@pytest.mark.regression("J43")
def test_j43_draft_ulang_tidak_mereset_revisi(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo)
    ok(fe_draft(repo))
    for text in ("ambil status v1.", "ambil status v2."):
        edit(repo, CONTRACT, "ambil status", text[:-1] + " —")
        fe_round(repo)
        ok(fe_draft(repo))
    r = chain(repo, "revisions", "--row", "CONTRACT")
    assert r.returncode == 1 and "2/2" in r.out and "AskUserQuestion" in r.out and "abandon" in r.out, r.out
    edit(repo, CONTRACT, "ambil status", "ambil status v3 —")
    fe_round(repo)
    r = fe_draft(repo)                                                    # draft ulang = revisi ketiga
    assert r.returncode == 1 and "plafon revisi" in r.out and "abandon" in r.out, r.out


@pytest.mark.regression("J43")
def test_j43_reopen_brief_menghentikan_hitungan(fe_chain_repo):
    repo = fe_chain_repo
    contract_approved(repo)
    b1 = fe_brief(repo, "01")
    fe_round(repo, gate="plan")
    ok(fe_draft(repo, "BRIEF"))
    for step in ("Tambah tombol Lacak v1.", "Tambah tombol Lacak v2."):
        fe_brief(repo, "01", step=step)
        fe_round(repo, gate="plan")
        ok(fe_draft(repo, "BRIEF"))
    assert "2/2" in chain(repo, "revisions", "--row", "BRIEF").out
    ok(approve(repo, "BRIEF"))
    ok(chain(repo, "reopen", "--row", "BRIEF", "--reason", "SC berubah"))
    fe_brief(repo, "01", step="Tambah tombol Lacak v3.")
    fe_round(repo, gate="plan")
    ok(fe_draft(repo, "BRIEF"))                                           # draft pertama putaran sesudah reopen
    r = chain(repo, "revisions", "--row", "BRIEF")
    assert r.returncode == 0 and "0/2" in r.out, r.out
    assert b1


def test_j43_plafon_ronde_menyebut_rute_h28(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo, "BLOCKED", semantic=1)
    fe_round(repo, "BLOCKED", semantic=1)
    r = rr(repo, "open")
    assert r.returncode == 1 and "AskUserQuestion" in r.out and "taskdir baru" in r.out


# ------------------------------------------------------------------ J44


def squash_to_root(repo, msg):
    first = git(repo, "rev-list", "--max-parents=0", "HEAD").strip()
    git(repo, "reset", "-q", "--soft", first)
    git(repo, "commit", "-qm", msg)


@pytest.mark.regression("J44")
def test_j44_rebase_ledger_tetap_sah(fe_chain_repo):
    repo = fe_chain_repo
    git(repo, "checkout", "-q", "-b", "feat/orders-lacak")
    fe_approved_chain(repo)
    git(repo, "checkout", "-q", "main")
    write_files(repo, {"README.md": "x\n"})
    commit(repo, "chore: readme", "README.md")
    git(repo, "checkout", "-q", "feat/orders-lacak")
    git(repo, "rebase", "-q", "main")
    r = chain(repo, "verify")
    assert r.returncode == 0, r.out
    assert "EKSEKUSI" in state(repo).out


@pytest.mark.regression("J44")
def test_j44_squash_rantai_tuntas_bukan_drift(fe_minor_chain):
    repo = fe_minor_chain
    assert "nol taskdir terbuka" in state(repo).out
    squash_to_root(repo, "feat: order checkout label (#12)")
    r = state(repo)
    assert "nol taskdir terbuka" in r.out, r.out
    assert "TUNTAS" in state(repo, "--all").out


@pytest.mark.regression("25 R6")
def test_r6_architect_squash_rantai_tuntas_bukan_terputus(fe_minor_chain):
    """Commit unit hilang karena squash-merge: architect sejalan dengan `taskdir_state` (TUNTAS), bukan TERPUTUS."""
    repo = fe_minor_chain
    squash_to_root(repo, "feat: order checkout label (#12)")
    out = json.loads(fe_run(repo, "architect/scripts/check_preconditions.py", "--taskdir", FE_MINOR_TD,
                            "--json").stdout)
    c4 = next(c for c in out["checks"] if c["id"] == 4)
    assert out["phase"] == "TUNTAS" and c4["status"] == "PASS", c4


@pytest.mark.regression("J44")
def test_j44_approve_menulis_sidik(fe_chain_repo):
    repo = fe_chain_repo
    contract_approved(repo)
    last = riwayat(repo)[-1]
    assert last.startswith("- 3 · approve CONTRACT · sidik ") and "review contract r1 t1 PASS" in last, last
    assert last.endswith("persetujuan: Setujui") and " sc " in last, last
    assert git(repo, "status", "--porcelain") == "", "approve tidak menyentuh git"


@pytest.mark.regression("J44")
def test_j44_base_commit_bukan_leluhur_fail_closed(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    git(repo, "checkout", "-q", "--orphan", "lain")
    commit(repo, "lain")
    side = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "checkout", "-q", "main")
    task = (repo / TASK).read_text(encoding="utf-8")
    base = task.split("base_commit: ", 1)[1].split("\n", 1)[0]
    (repo / TASK).write_text(task.replace(base, side), encoding="utf-8")
    r = state(repo)
    assert "RUSAK" in r.out and "leluhur" in r.out, r.out


# ------------------------------------------------------------------ J45


@pytest.mark.regression("J45")
def test_j45_evidence_ronde_lama_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo)
    ok(fe_draft(repo))
    edit(repo, CONTRACT, "ambil status.", "ambil status + hapus pesanan (DELETE).")
    opened = ok(rr(repo, "open"))
    assert "sidik " in opened.out
    r = rr(repo, "record", "--verdict", "PASS", "--evidence", f"{FE_TD}/.explore/contract-review-r1.md")
    assert r.returncode == 1 and "Sidik" in r.out, r.out


@pytest.mark.regression("J45")
def test_j45_review_plan_basi_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    contract_approved(repo)
    fe_brief(repo, "01")
    fe_round(repo, gate="plan")
    ok(fe_draft(repo, "BRIEF"))
    fe_brief(repo, "01", step="Tambah tombol Lacak + hapus cache global.")
    ok(rr(repo, "open", gate="plan"))
    r = rr(repo, "record", "--verdict", "PASS", gate="plan")                # REVIEW-PLAN.md ronde lalu
    assert r.returncode == 1 and "sidik" in r.out.lower(), r.out


# ------------------------------------------------------------------ J46


LIB = load_module(FE_SKILLS / "_common/precondition_lib.py", "fe_lib_12_ledger")


@pytest.mark.regression("J46")
def test_j46_materai_tangan_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    edit(repo, CONTRACT, "## 5. Decisions Not Taken", "## 5. TBD")
    assert approve(repo).returncode == 1                                 # jalur resmi menolak
    edit(repo, CONTRACT, "status: DRAFT", "status: APPROVED")
    sidik = LIB.content_snapshot(repo, [CONTRACT])                       # materai tangan bersidik benar
    edit(repo, TASK, "- [ ] CONTRACT — frontend:contract     → CONTRACT.md",
         f"- [x] CONTRACT — frontend:contract     → CONTRACT.md @ APPROVED {sidik[:12]}")
    text = (repo / TASK).read_text(encoding="utf-8")
    sc = LIB.sc_sidik(text)
    (repo / TASK).write_text(text.rstrip("\n") + f"\n- 2 · approve CONTRACT · sidik {sidik} · sc {sc} · "
                             "waktu 2026-10-13T00:00:00Z · persetujuan: ya\n", encoding="utf-8")
    r = chain(repo, "verify", "--rows", "CONTRACT")
    assert r.returncode == 1 and "review contract" in r.out, r.out
    r = fe_run(repo, "plan/scripts/check_preconditions.py", "--taskdir", FE_TD, "--mode", "CONTRACT", "--json")
    assert {c["id"]: c["status"] for c in json.loads(r.stdout)["checks"]}[4] == "FAIL"


@pytest.mark.regression("J46")
def test_j46_answer_bernewline_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo)
    ok(fe_draft(repo))
    before = (repo / TASK).read_text(encoding="utf-8")
    r = approve(repo, answer="ya\n- 9 · approve BRIEF · sidik 0000000")
    assert r.returncode == 1 and "baris" in r.out, r.out
    assert (repo / TASK).read_text(encoding="utf-8") == before


# ------------------------------------------------------------------ J47


@pytest.mark.regression("J47")
def test_j47_reopen_akar_menggantung_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    edit(repo, TASK, "## Out of Scope", "- [ ] **SC-2**: TBD lingkup liar\n\n## Out of Scope")
    before = (repo / TASK).read_text(encoding="utf-8")
    r = chain(repo, "reopen", "--row", "CONTRACT", "--reason", "uji")
    assert r.returncode == 1 and "chain.py amend" in r.out, r.out
    assert (repo / TASK).read_text(encoding="utf-8") == before
    assert "- [x] CONTRACT" in before


# ------------------------------------------------------------------ J48


@pytest.mark.regression("J48")
def test_j48_brief_blocked_tidak_dapat_dihidupkan(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    unit_blocked(repo)
    ok(chain(repo, "reopen", "--row", "BRIEF", "--reason", "unit 01 BLOCKED"))
    fe_brief(repo, "01", status="READY")                                 # dihidupkan, bukan remedi
    fe_round(repo, gate="plan")
    ok(fe_draft(repo, "BRIEF"))
    r = approve(repo, "BRIEF")
    assert r.returncode == 1 and "brief-01" in r.out and "BLOCKED" in r.out, r.out


# ------------------------------------------------------------------ J49


@pytest.mark.regression("J49")
def test_j49_slug_kembar_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    td2 = "frontenddev/docs/2609251000-orders-lacak"
    (repo / td2).mkdir(parents=True)
    r = fe_run(repo, "task/scripts/check_preconditions.py", "--taskdir", td2, "--lane", "FAST_FORWARD",
               "--sections", "architecture", "--json")
    checks = {c["id"]: c for c in json.loads(r.stdout)["checks"]}
    assert checks[9]["status"] == "FAIL" and "2609241200-orders-lacak" in checks[9]["summary"], checks
    assert r.returncode == 1


# ------------------------------------------------------------------ J50–J53


@pytest.mark.regression("J50")
def test_j50_status_akar_asing_rusak(fe_chain_repo):
    repo = fe_chain_repo
    edit(repo, TASK, "status: ACTIVE", "status: DONE")
    r = state(repo)
    assert "RUSAK" in r.out and "`DONE`" in r.out, r.out


@pytest.mark.regression("J51")
def test_j51_reopen_sesudah_abandon_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    ok(chain(repo, "abandon", "--reason", "user berhenti"))
    before = (repo / TASK).read_text(encoding="utf-8")
    r = chain(repo, "reopen", "--row", "BRIEF", "--reason", "x")
    assert r.returncode == 1 and "ABANDONED" in r.out, r.out
    assert (repo / TASK).read_text(encoding="utf-8") == before


@pytest.mark.regression("J51")
def test_j51_abandon_ganda_pesan_jelas(fe_chain_repo):
    repo = fe_chain_repo
    ok(chain(repo, "abandon", "--reason", "user berhenti"))
    r = chain(repo, "abandon", "--reason", "user berhenti")
    assert r.returncode == 1 and "sudah" in r.out and "hook/lock" not in r.out, r.out


@pytest.mark.regression("J52")
def test_j52_save_pertama_menulis_bak(fe_chain_repo):
    repo = fe_chain_repo
    ok(rr(repo, "open"))
    assert (repo / (STATE + ".bak")).read_text(encoding="utf-8") == (repo / STATE).read_text(encoding="utf-8")


@pytest.mark.regression("J53")
def test_j53_taskdir_di_luar_docs_rusak(fe_chain_repo):
    repo = fe_chain_repo
    other = "arsip/2609241200-orders-lacak"
    write_files(repo, {f"{other}/TASK.md": (repo / TASK).read_text(encoding="utf-8")})
    commit(repo, "docs(orders-lacak): arsip", f"{other}/TASK.md")
    r = state(repo, "--taskdir", f"./{other}")
    assert "RUSAK" in r.out and "GATE" not in r.out, r.out


@pytest.mark.regression("J53")
def test_j53_verdict_review_asing_penutup(fe_minor_chain):
    repo = fe_minor_chain
    (repo / FE_MINOR_TD / "REPORT.md").unlink()
    edit(repo, f"{FE_MINOR_TD}/REVIEW.md", "verdict: PASS", "verdict: LULUS")
    r = state(repo, "--taskdir", FE_MINOR_TD)
    assert "PENUTUP" in r.out and "LULUS" in r.out, r.out
