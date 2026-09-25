"""`review_round.py` — ronde reviewer terikat sidik konten + epoch reopen (L4.1), state fail-closed,
commit bertrailer, dan bukti balikan contract (L4.3)."""
import json

from conftest import FE_TD, fe_brief, fe_commit, fe_run, git, write_files

CONTRACT = f"{FE_TD}/CONTRACT.md"
REVIEW_PLAN = f"{FE_TD}/REVIEW-PLAN.md"
STATE = f"{FE_TD}/.explore/contract-review-state.json"


def rr(repo, *args, gate="contract"):
    return fe_run(repo, "_common/review_round.py", *args, "--taskdir", FE_TD, "--gate", gate)


def chain(repo, *args):
    return fe_run(repo, "_common/chain.py", *args, "--taskdir", FE_TD)


def approve(repo, row="CONTRACT"):
    return chain(repo, "approve", "--row", row, "--answer", "Setujui")


def edit(repo, rel=CONTRACT, old="Tambah tombol.", new="Tambah tombol Lacak di header."):
    p = repo / rel
    p.write_text(p.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def evidence(repo, n, verdict="PASS", mechanical=0, semantic=0):
    rel = f"{FE_TD}/.explore/contract-review-r{n}.md"
    write_files(repo, {rel: f"## Contract Review\n- Verdict: {verdict}\n- Ronde: {n}\n"
                            f"- BLOCKER: {mechanical} [MEKANIS] · {semantic} [SEMANTIK]\n"})
    return rel


def round_(repo, verdict="PASS", gate="contract", mechanical=0, semantic=0):
    opened = rr(repo, "open", gate=gate)
    assert opened.returncode == 0, opened.out
    n = opened.out.split("ronde ")[1].split("/")[0]
    extra = ["--mechanical", str(mechanical), "--semantic", str(semantic)]
    if gate == "plan":
        write_files(repo, {REVIEW_PLAN: f"---\nverdict: {verdict}\nround: \"{n}\"\n---\n\n# Plan Review\n"})
    else:
        extra += ["--evidence", evidence(repo, n, verdict, mechanical, semantic)]
    r = rr(repo, "record", "--verdict", verdict, *extra, gate=gate)
    assert r.returncode == 0, r.out


# ------------------------------------------------------------------ gate contract


def test_A_revisi_user_disetujui_tanpa_improvisasi(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo)
    assert rr(repo, "commit", "--subject", "docs(orders-lacak): draft CONTRACT.md").returncode == 0
    edit(repo); round_(repo)
    r = rr(repo, "commit", "--subject", "docs(orders-lacak): revise CONTRACT.md")
    assert r.returncode == 0 and "Review-Round: contract r1 t2 PASS" in r.out, r.out
    r = approve(repo)
    assert r.returncode == 0, r.out


def test_B_draft_dua_ronde_lalu_revisi_masih_boleh_membuka_ronde(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo); fe_commit(repo, "draft CONTRACT.md")
    edit(repo)
    round_(repo)                                              # putaran baru sesudah draft diajukan
    fe_commit(repo, "revise CONTRACT.md")
    assert approve(repo).returncode == 0


def test_konten_berubah_sesudah_ronde_pass_tetap_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo); fe_commit(repo, "draft CONTRACT.md")
    edit(repo); fe_commit(repo, "revise CONTRACT.md")          # tanpa ronde baru
    r = approve(repo)
    assert r.returncode == 1 and "konten berubah" in r.out


def test_reopen_sesudah_ronde_menuntut_ronde_baru(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo); fe_commit(repo, "draft CONTRACT.md")
    assert approve(repo).returncode == 0
    assert chain(repo, "reopen", "--row", "CONTRACT", "--reason", "berkas yatim").returncode == 0
    r = approve(repo)
    assert r.returncode == 1 and "dibuka ulang" in r.out
    round_(repo)                                              # epoch baru: putaran baru
    assert "ronde 1 [epoch 1" in rr(repo, "status").out
    assert approve(repo).returncode == 0


def test_plafon_dua_ronde_per_putaran_tetap_berlaku(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo, "BLOCKED", semantic=1)
    r = rr(repo, "open")
    assert r.returncode == 1 and "plafon 2 ronde" in r.out


def test_commit_draft_blocked_tidak_mereset_plafon(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo, "BLOCKED", semantic=1)
    edit(repo); fe_commit(repo, "revise CONTRACT.md")          # draft yang belum pernah PASS
    r = rr(repo, "open")
    assert r.returncode == 1 and "plafon 2 ronde" in r.out


def test_ronde_format_lama_menuntut_ronde_baru(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo); fe_commit(repo, "draft CONTRACT.md")
    state = repo / STATE
    data = json.loads(state.read_text(encoding="utf-8"))
    for r in data["rounds"]:
        r.pop("epoch"); r.pop("head"); r["generation"] = "contract#0"
    state.write_text(json.dumps(data), encoding="utf-8")
    r = approve(repo)
    assert r.returncode == 1 and "format lama" in r.out


# ------------------------------------------------------------------ gate plan


def plan_ready(repo):
    """CONTRACT disetujui, brief 01 READY tertulis (belum di-commit)."""
    round_(repo); fe_commit(repo, "draft CONTRACT.md")
    assert approve(repo).returncode == 0
    return fe_brief(repo, "01")


def test_C_revise_breakdown_disetujui(fe_chain_repo):
    repo = fe_chain_repo
    b1 = plan_ready(repo)
    round_(repo, gate="plan"); fe_commit(repo, "draft breakdown (1 briefs)", b1, REVIEW_PLAN)
    fe_brief(repo, "01", step="Tambah tombol Lacak Paket di OrderDetail.")            # revisi user
    round_(repo, gate="plan"); fe_commit(repo, "revise breakdown", b1, REVIEW_PLAN)
    r = approve(repo, "BRIEF")
    assert r.returncode == 0, r.out


def test_D_append_sesudah_reopen_disetujui(fe_chain_repo):
    repo = fe_chain_repo
    b1 = plan_ready(repo)
    round_(repo, gate="plan"); fe_commit(repo, "draft breakdown (1 briefs)", b1, REVIEW_PLAN)
    assert approve(repo, "BRIEF").returncode == 0
    fe_brief(repo, "01", status="BLOCKED")
    write_files(repo, {f"{FE_TD}/report-01.md":
                       '---\nartifact: UNIT_REPORT\nunit: "01"\nstatus: BLOCKED\n---\n\n# Unit 01\n\n## Triase\n- galat\n'})
    fe_commit(repo, "unit 01 BLOCKED - galat kompilasi baru", b1, f"{FE_TD}/report-01.md")
    assert chain(repo, "reopen", "--row", "BRIEF", "--reason", "unit 01 BLOCKED").returncode == 0
    b2 = fe_brief(repo, "02", step="Perbaiki tombol Lacak di OrderDetail.", remedies="01", total=2)
    round_(repo, gate="plan"); fe_commit(repo, "draft breakdown append (unit 02..02, total 2)", b2, REVIEW_PLAN)
    r = approve(repo, "BRIEF")
    assert r.returncode == 0, r.out
    assert "epoch 1" in rr(repo, "status", gate="plan").out


# ------------------------------------------------------------------ L4.3 — state fail-closed, commit, bukti


def test_state_rusak_fail_keras(fe_chain_repo):
    repo = fe_chain_repo
    write_files(repo, {STATE: '{"gate":"contract","rounds":['})
    r = rr(repo, "open")
    assert r.returncode == 1 and "rusak" in r.out
    assert (repo / STATE).read_text(encoding="utf-8") == '{"gate":"contract","rounds":['


def test_state_bentuk_salah_fail(fe_chain_repo):
    write_files(fe_chain_repo, {STATE: '{"rounds": {}}'})
    r = rr(fe_chain_repo, "open")
    assert r.returncode == 1 and "tidak berbentuk" in r.out


def test_save_atomik_menyimpan_bak(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1)
    before = (repo / STATE).read_text(encoding="utf-8")
    assert rr(repo, "open").returncode == 0
    assert (repo / (STATE + ".bak")).read_text(encoding="utf-8") == before
    assert not (repo / (STATE + ".tmp")).exists()


def test_hitungan_negatif_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    assert rr(repo, "open").returncode == 0
    before = (repo / STATE).read_text(encoding="utf-8")
    r = rr(repo, "record", "--verdict", "BLOCKED", "--mechanical", "-1")
    assert r.returncode == 2 and "tidak boleh negatif" in r.out
    assert (repo / STATE).read_text(encoding="utf-8") == before


def test_state_hilang_dengan_trailer_fail_lalu_rebuild(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo)
    assert rr(repo, "commit", "--subject", "docs(orders-lacak): draft CONTRACT.md").returncode == 0
    (repo / STATE).unlink(); (repo / (STATE + ".bak")).unlink()
    r = rr(repo, "open")
    assert r.returncode == 1 and "hilang padahal git mencatat 2 ronde" in r.out
    r = approve(repo)
    assert r.returncode == 1 and "hilang padahal git mencatat" in r.out
    r = rr(repo, "rebuild")
    assert r.returncode == 0 and "taskdir 2/8" in r.out
    r = approve(repo)
    assert r.returncode == 1 and "REKONSTRUKSI" in r.out
    round_(repo)
    assert "taskdir 3/8" in rr(repo, "status").out
    assert approve(repo).returncode == 0


def test_commit_menolak_ronde_blocked(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1)
    head = git(repo, "rev-parse", "HEAD")
    r = rr(repo, "commit", "--subject", "docs(orders-lacak): draft CONTRACT.md")
    assert r.returncode == 1 and "BLOCKED" in r.out and "jangan commit" in r.out
    assert git(repo, "rev-parse", "HEAD") == head


def test_commit_menolak_subjek_asing(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo)
    r = rr(repo, "commit", "--subject", "docs(orders-lacak): approve CONTRACT.md")
    assert r.returncode == 1 and "subjek wajib" in r.out


def test_pass_contract_butuh_evidence(fe_chain_repo):
    repo = fe_chain_repo
    assert rr(repo, "open").returncode == 0
    r = rr(repo, "record", "--verdict", "PASS")
    assert r.returncode == 1 and "--evidence" in r.out


def test_evidence_berbeda_dari_flag_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    assert rr(repo, "open").returncode == 0
    rel = evidence(repo, 1, "BLOCKED", semantic=2)
    r = rr(repo, "record", "--verdict", "PASS", "--evidence", rel)
    assert r.returncode == 1 and "apa adanya" in r.out


def test_plan_record_menolak_verdict_laporan_berbeda(fe_chain_repo):
    repo = fe_chain_repo
    b1 = plan_ready(repo)
    assert rr(repo, "open", gate="plan").returncode == 0
    write_files(repo, {REVIEW_PLAN: "---\nverdict: BLOCKED\n---\n\n# Plan Review\n"})
    r = rr(repo, "record", "--verdict", "PASS", gate="plan")
    assert r.returncode == 1 and "verdict: BLOCKED" in r.out
    assert b1
