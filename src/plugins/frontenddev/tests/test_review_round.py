"""`review_round.py` — ronde reviewer terikat sidik konten + epoch reopen, bukan subjek commit (L4.1)."""
import json

from conftest import FE_TD, fe_brief, fe_commit, fe_run, write_files

CONTRACT = f"{FE_TD}/CONTRACT.md"
REVIEW_PLAN = f"{FE_TD}/REVIEW-PLAN.md"


def rr(repo, *args, gate="contract"):
    return fe_run(repo, "_common/review_round.py", *args, "--taskdir", FE_TD, "--gate", gate)


def chain(repo, *args):
    return fe_run(repo, "_common/chain.py", *args, "--taskdir", FE_TD)


def approve(repo, row="CONTRACT"):
    return chain(repo, "approve", "--row", row, "--answer", "Setujui")


def edit(repo, rel=CONTRACT, old="Tambah tombol.", new="Tambah tombol Lacak di header."):
    p = repo / rel
    p.write_text(p.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def round_(repo, verdict="PASS", gate="contract", **counts):
    assert rr(repo, "open", gate=gate).returncode == 0
    if gate == "plan":
        write_files(repo, {REVIEW_PLAN: f"---\nverdict: {verdict}\n---\n\n# Plan Review\n\nRonde.\n"})
    extra = [a for k, v in counts.items() for a in (f"--{k}", str(v))]
    r = rr(repo, "record", "--verdict", verdict, *extra, gate=gate)
    assert r.returncode == 0, r.out


# ------------------------------------------------------------------ gate contract


def test_A_revisi_user_disetujui_tanpa_improvisasi(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo); fe_commit(repo, "draft CONTRACT.md")
    edit(repo); round_(repo); fe_commit(repo, "revise CONTRACT.md")
    r = approve(repo)
    assert r.returncode == 0, r.out


def test_B_draft_dua_ronde_lalu_revisi_masih_boleh_membuka_ronde(fe_chain_repo):
    repo = fe_chain_repo
    round_(repo, "BLOCKED", semantic=1); round_(repo); fe_commit(repo, "draft CONTRACT.md")
    edit(repo)
    r = rr(repo, "open")
    assert r.returncode == 0, r.out
    assert rr(repo, "record", "--verdict", "PASS").returncode == 0
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
    r = rr(repo, "open")
    assert r.returncode == 0 and "ronde 1/2" in r.out           # epoch baru: putaran baru
    assert rr(repo, "record", "--verdict", "PASS").returncode == 0
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
    state = repo / FE_TD / ".explore" / "contract-review-state.json"
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
