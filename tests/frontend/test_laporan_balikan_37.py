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
