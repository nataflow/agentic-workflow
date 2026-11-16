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
