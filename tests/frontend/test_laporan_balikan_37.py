"""Langkah 37 — laporan unit lewat balikan: implementor frontend tidak menulis `report-NN.md`; `architect` menyimpannya
hanya untuk unit tak bersih (U1–U5).

Harness Claude Code menolak subagent menulis berkas laporan ("Subagents should return findings as text"), sehingga
dulu tiap unit berakhir di baris "laporan absen + tree kotor → HENTIKAN" matriks bukti disk.
"""
import pytest

from conftest import PLUGINS

FE = PLUGINS / "frontend"


def _read(rel):
    return (FE / rel).read_text(encoding="utf-8")


# ------------------------------------------------------------------ U1 — implementor tanpa berkas laporan

@pytest.mark.regression("37 U1")
def test_u1_implementor_tidak_menulis_berkas_laporan():
    agent = _read("agents/code-implementor.md")
    assert "report_path" not in agent
    assert "TIDAK ADA BERKAS LAIN YANG BOLEH DITULIS — TERMASUK BERKAS LAPORAN" in agent
    assert "Laporannya cukup di chat saja" not in agent
    desc = agent.split("---\n", 2)[1]
    assert "menulis report-NN.md" not in desc and "balikan" in desc


@pytest.mark.regression("37 U1")
def test_u1_dispatcher_tanpa_slot_report_path():
    tpl = _read("skills/architect/dispatcher/implementor.md")
    assert "{report_path}" not in tpl
    assert "Format laporan (balikan):" in tpl
    assert "REPORT <unit_name>:" not in tpl


# ------------------------------------------------------------------ U2 — architect menyimpan laporan unit tak bersih

def _bagian(n):
    proto = _read("skills/architect/references/execution-protocol.md")
    return proto.split(f"## {n}.", 1)[1].split(f"## {n + 1}.", 1)[0]


@pytest.mark.regression("37 U2")
def test_u2_kontrak_laporan_ditulis_architect_salin_persis():
    b4 = _bagian(4)
    assert "**menyalin persis**" in b4 and "satu-satunya tambahan miliknya `## Triase`" in b4
    assert "hanya untuk unit tak bersih" in b4
    for pemicu in ("balikan `status: FAILED`", "unit turun ke `BLOCKED`", "`architect` menulis `## Triase`",
                   "`## Out of Scope / Mismatch` balikan bukan `- Tidak ada`"):
        assert pemicu in b4, pemicu
    assert "Unit bersih tidak meninggalkan berkas laporan" in b4


@pytest.mark.regression("37 U2")
def test_u2_matriks_berporos_pada_balikan():
    b3 = _bagian(3)
    assert "| Balikan (laporan unit) | Disk vs `files_touched` | Tindakan |" in b3
    assert "Balikan implementor (laporan unit) adalah klaim subagent" in b3
    assert "hapus `report-<NN>.md` rusak" not in b3
    assert "simpan dulu bila unit tidak bersih (bagian 4)" in b3
    b5 = _bagian(5)
    assert "simpan `report-<NN>.md` dengan `## Triase`" in b5 and "sesi terputus" in b5


@pytest.mark.regression("37 U2")
def test_u2_skill_architect_selaras():
    skill = _read("skills/architect/SKILL.md")
    assert "report_path" not in skill
    assert "atas balikan implementor dan `git status --porcelain`" in skill
    assert "**Balikan implementor absen, rusak, atau terpotong, tree bersih**" in skill
    assert "hapus `report-<NN>.md` rusak" not in skill


# ------------------------------------------------------------------ U3 — prasyarat architect

@pytest.mark.regression("37 U3")
def test_u3_terputus_divonis_dari_tree_saja():
    from conftest import load_module
    mod = load_module(FE / "skills" / "architect" / "scripts" / "check_preconditions.py", "cp_arch_37")
    aksi = mod.TERPUTUS_ACTION.format(nn="03")
    assert "dari tree saja" in aksi and "hapus `report-03.md` sisa" in aksi
    assert "laporan absen/rusak" not in aksi and "laporan FAILED" not in aksi
    assert not hasattr(mod.Checker if hasattr(mod, "Checker") else object, "_warn_missing_reports")
    assert "missing_reports" not in (FE / "skills" / "architect" / "scripts" / "check_preconditions.py").read_text(
        encoding="utf-8")


@pytest.mark.regression("37 U3")
def test_u3_prosa_terputus_dan_check_4_selaras():
    b3 = _bagian(3)
    assert "divonis dari tree saja (37 U3)" in b3 and "Check 4 `PASS`" in b3
    assert "Check 4 hanya `WARN`" not in b3
    assert "laporan unit tidak dinilai" in _bagian(1)


@pytest.mark.regression("37 U3")
def test_u3_plan_tetap_menuntut_laporan_unit_blocked(fe_chain_repo):
    """K3: unit `BLOCKED` selalu disimpan laporannya oleh architect — Check 5 `plan` tetap menagihnya."""
    import json
    from conftest import FE_TD, fe_approved_chain, fe_brief, fe_run, write_files
    repo = fe_chain_repo
    fe_approved_chain(repo)
    fe_brief(repo, "01", status="BLOCKED")

    def c5():
        r = fe_run(repo, "plan/scripts/check_preconditions.py", "--taskdir", FE_TD, "--mode", "APPEND", "--json")
        return next(c for c in json.loads(r.stdout)["checks"] if c["id"] == 5)

    assert c5()["status"] == "FAIL" and "01" in c5()["summary"]
    write_files(repo, {f"{FE_TD}/report-01.md":
                       '---\nartifact: UNIT_REPORT\nunit: "01"\nstatus: FAILED\n---\n\n# Unit 01\n\n## Triase\n- x\n'})
    assert c5()["status"] == "PASS"


# ------------------------------------------------------------------ U4 — reviewer

@pytest.mark.regression("37 U4")
def test_u4_reviewer_membaca_ditunda_dari_brief():
    reviewer = _read("agents/code-reviewer.md")
    assert "seksi `## 5. Done Criteria & Verification Baseline` tiap brief `DONE`" in reviewer
    assert "tiap butir terminal seksi 5 brief `DONE` divonis dari `{verification_log}`" in reviewer
    assert "tiap butir `DITUNDA` di `report-<NN>.md`" not in reviewer
    assert "absennya berarti nihil" in reviewer
    phase5 = _read("skills/architect/SKILL.md").split("### Phase 5", 1)[1]
    assert "`report-<NN>.md` yang ada" in phase5
