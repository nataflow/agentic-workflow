"""`review_round.py` — ronde reviewer terikat sidik konten + epoch reopen (L4.1), state fail-closed,
jejak ronde di `## Riwayat Rantai` (field `review` kejadian `chain.py draft`, Langkah 24), dan bukti balikan
contract (L4.3)."""
import json

from conftest import FE_TD, fe_brief, fe_draft as draft, fe_evidence as evidence, fe_round as round_, fe_run, \
    write_files

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


# ------------------------------------------------------------------ gate contract


def test_A_revisi_user_disetujui_tanpa_improvisasi(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo)
    assert draft(repo).returncode == 0
    edit(repo); round_(repo)
    r = draft(repo)
    assert r.returncode == 0 and "revisi 1/2" in r.out, r.out
    assert "review contract r1 t2 PASS" in (repo / FE_TD / "TASK.md").read_text(encoding="utf-8")
    r = approve(repo)
    assert r.returncode == 0, r.out


def test_B_draft_dua_ronde_lalu_revisi_masih_boleh_membuka_ronde(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo); assert draft(repo).returncode == 0
    edit(repo)
    round_(repo)                                              # putaran baru sesudah draft diajukan
    assert draft(repo).returncode == 0
    assert approve(repo).returncode == 0


def test_konten_berubah_sesudah_ronde_pass_tetap_ditolak(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo); assert draft(repo).returncode == 0
    edit(repo)                                                # tanpa ronde baru
    r = draft(repo)
    assert r.returncode == 1 and "konten berubah" in r.out, r.out
    r = approve(repo)
    assert r.returncode == 1 and "konten berubah" in r.out


def test_reopen_sesudah_ronde_menuntut_ronde_baru(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo); assert draft(repo).returncode == 0
    assert approve(repo).returncode == 0
    assert chain(repo, "reopen", "--row", "CONTRACT", "--reason", "berkas yatim").returncode == 0
    r = approve(repo)
    assert r.returncode == 1 and "dibuka ulang" in r.out
    round_(repo)                                              # epoch baru: putaran baru
    assert "ronde 1 [epoch 1" in rr(repo, "status").out
    r = approve(repo)
    assert r.returncode == 1 and "chain.py draft" in r.out, r.out        # konten belum tercatat diajukan
    assert draft(repo).returncode == 0
    assert approve(repo).returncode == 0


def test_plafon_dua_ronde_per_putaran_tetap_berlaku(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo, "BLOCKED", semantic=1)
    r = rr(repo, "open")
    assert r.returncode == 1 and "plafon 2 ronde" in r.out


def test_draft_blocked_tidak_mereset_plafon(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo, "BLOCKED", semantic=1)
    edit(repo)
    assert draft(repo).returncode == 1                        # draft yang belum pernah PASS tidak tercatat
    r = rr(repo, "open")
    assert r.returncode == 1 and "plafon 2 ronde" in r.out


def test_ronde_format_lama_menuntut_ronde_baru(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo); assert draft(repo).returncode == 0
    state = repo / STATE
    data = json.loads(state.read_text(encoding="utf-8"))
    for r in data["rounds"]:
        r.pop("epoch"); r.pop("riwayat"); r["generation"] = "contract#0"
    state.write_text(json.dumps(data), encoding="utf-8")
    r = approve(repo)
    assert r.returncode == 1 and "format lama" in r.out


# ------------------------------------------------------------------ gate plan


def plan_ready(repo):
    """CONTRACT disetujui, brief 01 READY tertulis (belum dicatat)."""
    round_(repo); assert draft(repo).returncode == 0
    assert approve(repo).returncode == 0
    return fe_brief(repo, "01")


def test_C_revise_breakdown_disetujui(fe_chain_repo):
    repo = fe_chain_repo
    plan_ready(repo)
    round_(repo, gate="plan"); assert draft(repo, "BRIEF").returncode == 0
    fe_brief(repo, "01", step="Tambah tombol Lacak Paket di OrderDetail.")            # revisi user
    round_(repo, gate="plan"); assert draft(repo, "BRIEF").returncode == 0
    r = approve(repo, "BRIEF")
    assert r.returncode == 0, r.out


def test_D_append_sesudah_reopen_disetujui(fe_chain_repo):
    repo = fe_chain_repo
    plan_ready(repo)
    round_(repo, gate="plan"); assert draft(repo, "BRIEF").returncode == 0
    assert approve(repo, "BRIEF").returncode == 0
    fe_brief(repo, "01", status="BLOCKED")
    write_files(repo, {f"{FE_TD}/report-01.md":
                       '---\nartifact: UNIT_REPORT\nunit: "01"\nstatus: BLOCKED\n---\n\n# Unit 01\n\n## Triase\n- galat\n'})
    assert chain(repo, "reopen", "--row", "BRIEF", "--reason", "unit 01 BLOCKED").returncode == 0
    fe_brief(repo, "02", step="Perbaiki tombol Lacak di OrderDetail.", remedies="01", total=2)
    round_(repo, gate="plan"); assert draft(repo, "BRIEF").returncode == 0
    r = approve(repo, "BRIEF")
    assert r.returncode == 0, r.out
    assert "epoch 1" in rr(repo, "status", gate="plan").out


# ------------------------------------------------------------------ L4.3 — state fail-closed, draft, bukti


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


def test_state_hilang_dengan_riwayat_fail_lalu_rebuild(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo)
    assert draft(repo).returncode == 0
    (repo / STATE).unlink(); (repo / (STATE + ".bak")).unlink()
    r = rr(repo, "open")
    assert r.returncode == 1 and "hilang padahal `## Riwayat Rantai` mencatat 2 ronde" in r.out, r.out
    r = approve(repo)
    assert r.returncode == 1 and "hilang padahal `## Riwayat Rantai` mencatat" in r.out
    r = rr(repo, "rebuild")
    assert r.returncode == 0 and "taskdir 2/8" in r.out
    r = approve(repo)
    assert r.returncode == 1 and "REKONSTRUKSI" in r.out
    round_(repo)
    assert "taskdir 3/8" in rr(repo, "status").out
    assert approve(repo).returncode == 0


def test_draft_menolak_ronde_blocked(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1)
    before = (repo / FE_TD / "TASK.md").read_text(encoding="utf-8")
    r = draft(repo)
    assert r.returncode == 1 and "BLOCKED" in r.out, r.out
    assert (repo / FE_TD / "TASK.md").read_text(encoding="utf-8") == before


def test_subperintah_commit_tidak_ada_lagi(fe_chain_repo):
    """Langkah 24: draft dicatat `chain.py draft`; `review_round.py` tidak pernah menjalankan git commit."""
    repo = fe_chain_repo
    round_(repo)
    r = rr(repo, "commit")
    assert r.returncode == 2 and "invalid choice" in r.out


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


# ------------------------------------------------------------------ L4.8 — artefak tertunda tidak dicatat tanpa PASS


def test_status_ready_blocked_exit1(fe_chain_repo):
    round_(fe_chain_repo, "BLOCKED", semantic=2)
    r = rr(fe_chain_repo, "status", "--ready")
    assert r.returncode == 1 and "ronde review `contract` terakhir ber-verdict `BLOCKED`" in r.out


def test_status_ready_pass_konten_berubah_exit1(fe_chain_repo):
    round_(fe_chain_repo); edit(fe_chain_repo)
    r = rr(fe_chain_repo, "status", "--ready")
    assert r.returncode == 1 and "konten berubah" in r.out


def test_status_ready_pass_sama_exit0(fe_chain_repo):
    round_(fe_chain_repo)
    r = rr(fe_chain_repo, "status", "--ready")
    assert r.returncode == 0 and r.out.strip().endswith("siap diajukan: ya")


def test_prasyarat_contract_tidak_menyuruh_catat_draft_blocked(fe_chain_repo):
    round_(fe_chain_repo, "BLOCKED", semantic=2)
    r = fe_run(fe_chain_repo, "contract/scripts/check_preconditions.py", "--taskdir", FE_TD)
    assert "Jangan catat draft" in r.out and "chain.py draft" not in r.out
    assert "belum layak diajukan" in r.out
