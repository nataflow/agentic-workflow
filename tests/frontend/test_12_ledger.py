"""Regresi 12 Tahap 4 — ledger & state `frontend` (J42–J53).

Plafon ronde hilir tidak dibuka ulang oleh reopen/eskalasi hulu (J42); `draft` ulang me-reset hitungan
revisi dan reopen BRIEF tak terlihat penghitungnya (J43); sha ledger tidak tahan rebase/clone dan rantai
TUNTAS yang di-squash divonis DRIFT (J44); `record` menerima laporan reviewer ronde lama (J45); materai
approve dapat diketik tangan atau disisipkan lewat `--answer` (J46); `reopen` menyapu suntingan
menggantung (J47); brief `BLOCKED` dihidupkan lewat reopen (J48); slug kembar (J49); status akar asing
(J50); subperintah atas taskdir yang ditutup (J51); `.bak` pada `save` pertama (J52); path taskdir dan
verdict REVIEW asing di `taskdir_state` (J53).
"""
import json
import subprocess

import pytest

from conftest import FE_FIX, FE_MINOR_TD, FE_SKILLS, FE_TD, GIT_ENV, commit, fe_approved_chain, fe_brief, \
    fe_commit, fe_round, fe_run, git, write_files

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
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): draft CONTRACT.md"))
    ok(approve(repo))


def contract_revise(repo, text):
    edit(repo, CONTRACT, "ambil status.", text)
    fe_round(repo)
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): revise CONTRACT.md"))


def unit_blocked(repo):
    """brief-01 `BLOCKED` beserta `report-01.md`, satu commit milik architect."""
    fe_brief(repo, "01", status="BLOCKED")
    write_files(repo, {f"{FE_TD}/report-01.md":
                       '---\nartifact: UNIT_REPORT\nunit: "01"\nstatus: BLOCKED\n---\n\n# Unit 01\n\n## Triase\n- galat\n'})
    fe_commit(repo, "unit 01 BLOCKED - galat kompilasi baru", B1, f"{FE_TD}/report-01.md")


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


# ------------------------------------------------------------------ J43


@pytest.mark.regression("J43")
def test_j43_draft_ulang_tidak_mereset_revisi(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo)
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): draft CONTRACT.md"))
    for text in ("ambil status v1.", "ambil status v2."):
        edit(repo, CONTRACT, "ambil status", text[:-1] + " —")
        fe_round(repo)
        ok(rr(repo, "commit", "--subject", "docs(orders-lacak): revise CONTRACT.md"))
    assert chain(repo, "revisions", "--row", "CONTRACT").returncode == 1
    edit(repo, CONTRACT, "ambil status", "ambil status v3 —")
    fe_round(repo)
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): draft CONTRACT.md"))   # draft ulang
    r = chain(repo, "revisions", "--row", "CONTRACT")
    assert r.returncode == 1 and "3/2" in r.out, r.out
    assert "AskUserQuestion" in r.out and "abandon" in r.out


@pytest.mark.regression("J43")
def test_j43_reopen_brief_menghentikan_hitungan(fe_chain_repo):
    repo = fe_chain_repo
    contract_approved(repo)
    b1 = fe_brief(repo, "01")
    fe_round(repo, gate="plan")
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): draft breakdown (1 briefs)", gate="plan"))
    for step in ("Tambah tombol Lacak v1.", "Tambah tombol Lacak v2."):
        fe_brief(repo, "01", step=step)
        fe_round(repo, gate="plan")
        ok(rr(repo, "commit", "--subject", "docs(orders-lacak): revise breakdown", gate="plan"))
    ok(approve(repo, "BRIEF"))
    ok(chain(repo, "reopen", "--row", "BRIEF", "--reason", "SC berubah"))
    fe_brief(repo, "01", step="Tambah tombol Lacak v3.")
    fe_round(repo, gate="plan")
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): revise breakdown", gate="plan"))
    r = chain(repo, "revisions", "--row", "BRIEF")
    assert r.returncode == 0 and "1/2" in r.out, r.out
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
def test_j44_rebase_lalu_clone_ledger_tetap_sah(fe_chain_repo, tmp_path):
    repo = fe_chain_repo
    git(repo, "checkout", "-q", "-b", "feat/orders-lacak")
    fe_approved_chain(repo)
    git(repo, "checkout", "-q", "main")
    write_files(repo, {"README.md": "x\n"})
    commit(repo, "chore: readme", "README.md")
    git(repo, "checkout", "-q", "feat/orders-lacak")
    git(repo, "rebase", "-q", "main")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", "--branch", "feat/orders-lacak", f"file://{repo}", str(clone)],
                   check=True, capture_output=True, env={**GIT_ENV, "PATH": "/usr/bin:/bin"})
    r = chain(clone, "verify")
    assert r.returncode == 0, r.out
    assert "EKSEKUSI" in state(clone).out


@pytest.mark.regression("J44")
def test_j44_squash_rantai_tuntas_bukan_drift(fe_minor_chain):
    repo = fe_minor_chain
    commit(repo, "docs(order-checkout): laporkan hasil rantai order-checkout", f"{FE_MINOR_TD}/REPORT.md")
    squash_to_root(repo, "feat: order checkout label (#12)")
    r = state(repo)
    assert "nol taskdir terbuka" in r.out, r.out
    assert "TUNTAS" in state(repo, "--all").out


@pytest.mark.regression("J44")
def test_j44_approve_menulis_sidik(fe_chain_repo):
    repo = fe_chain_repo
    contract_approved(repo)
    body = git(repo, "log", "-1", "--format=%b")
    assert "Sidik: " in body and "Review-Round: contract r1 t1 PASS" in body, body


def test_j44_squash_rantai_berjalan_fail_closed(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    squash_to_root(repo, "wip")
    r = chain(repo, "verify")
    assert r.returncode == 1 and "reopen" in r.out, r.out


# ------------------------------------------------------------------ J45


@pytest.mark.regression("J45")
def test_j45_evidence_ronde_lama_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo)
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): draft CONTRACT.md"))
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
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): draft breakdown (1 briefs)", gate="plan"))
    fe_brief(repo, "01", step="Tambah tombol Lacak + hapus cache global.")
    ok(rr(repo, "open", gate="plan"))
    r = rr(repo, "record", "--verdict", "PASS", gate="plan")                # REVIEW-PLAN.md ronde lalu
    assert r.returncode == 1 and "sidik" in r.out.lower(), r.out


# ------------------------------------------------------------------ J46


def hand_stamp(repo, row_line_old, row_line_new, sha, row="CONTRACT", subject="docs(orders-lacak): approve CONTRACT.md"):
    edit(repo, TASK, row_line_old, row_line_new)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", subject, "-m", f"Persetujuan user: ya\nKonten disetujui: {sha}\nHop: {row}")


@pytest.mark.regression("J46")
def test_j46_materai_tangan_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    edit(repo, CONTRACT, "## 5. Decisions Not Taken", "## 5. TBD")
    sha = fe_commit(repo, "draft CONTRACT.md")
    assert approve(repo).returncode == 1                                 # jalur resmi menolak
    edit(repo, CONTRACT, "status: DRAFT", "status: APPROVED")
    hand_stamp(repo, "- [ ] CONTRACT — frontend:contract     → CONTRACT.md",
               f"- [x] CONTRACT — frontend:contract     → CONTRACT.md @ APPROVED {sha}", sha)
    r = chain(repo, "verify", "--rows", "CONTRACT")
    assert r.returncode == 1 and "Sidik" in r.out, r.out
    r = fe_run(repo, "plan/scripts/check_preconditions.py", "--taskdir", FE_TD, "--mode", "CONTRACT", "--json")
    assert {c["id"]: c["status"] for c in json.loads(r.stdout)["checks"]}[4] == "FAIL"


@pytest.mark.regression("J46")
def test_j46_answer_bernewline_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo)
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): draft CONTRACT.md"))
    head = git(repo, "rev-parse", "HEAD")
    r = approve(repo, answer="ya\nKonten disetujui: 0000000\nHop: BRIEF")
    assert r.returncode == 1 and "baris" in r.out, r.out
    assert git(repo, "rev-parse", "HEAD") == head


# ------------------------------------------------------------------ J47


@pytest.mark.regression("J47")
def test_j47_reopen_tree_kotor_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    edit(repo, TASK, "## Out of Scope", "- [ ] **SC-2**: TBD lingkup liar\n\n## Out of Scope")
    edit(repo, CONTRACT, "ambil status.", "ambil status + endpoint baru tanpa review.")
    head = git(repo, "rev-parse", "HEAD")
    r = chain(repo, "reopen", "--row", "CONTRACT", "--reason", "uji")
    assert r.returncode == 1 and "stash" in r.out, r.out
    assert git(repo, "rev-parse", "HEAD") == head
    assert "- [x] CONTRACT" in (repo / TASK).read_text(encoding="utf-8")


# ------------------------------------------------------------------ J48


@pytest.mark.regression("J48")
def test_j48_brief_blocked_tidak_dapat_dihidupkan(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    unit_blocked(repo)
    ok(chain(repo, "reopen", "--row", "BRIEF", "--reason", "unit 01 BLOCKED"))
    fe_brief(repo, "01", status="READY")                                 # dihidupkan, bukan remedi
    fe_round(repo, gate="plan")
    ok(rr(repo, "commit", "--subject", "docs(orders-lacak): draft breakdown append (unit 01..01, total 1)",
          gate="plan"))
    r = approve(repo, "BRIEF")
    assert r.returncode == 1 and "brief-01" in r.out and "BLOCKED" in r.out, r.out


# ------------------------------------------------------------------ J49


@pytest.mark.regression("J49")
def test_j49_slug_kembar_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_commit(repo, "draft CONTRACT.md")
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
    commit(repo, "docs(orders-lacak): tandai selesai", TASK)
    r = state(repo)
    assert "RUSAK" in r.out and "`DONE`" in r.out, r.out


@pytest.mark.regression("J51")
def test_j51_reopen_sesudah_abandon_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    ok(chain(repo, "abandon", "--reason", "user berhenti"))
    head = git(repo, "rev-parse", "HEAD")
    r = chain(repo, "reopen", "--row", "BRIEF", "--reason", "x")
    assert r.returncode == 1 and "ABANDONED" in r.out, r.out
    assert git(repo, "rev-parse", "HEAD") == head


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
    commit(repo, "docs(order-checkout): closing review LULUS", f"{FE_MINOR_TD}/REVIEW.md")
    r = state(repo, "--taskdir", FE_MINOR_TD)
    assert "PENUTUP" in r.out and "LULUS" in r.out, r.out
