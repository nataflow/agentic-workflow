"""25 R11 — kontrak `report-NN.md` backend: penulis (`code-implementor`) dan pembaca (`architect`) satu suara.

`architect` membaca baris `Umpan balik profil:` dari `report-NN.md` untuk slot penutupnya, dan gerbang
meneruskannya ke `backend:profile` sebagai `reported_anti_patterns`. Dulu kontrak penulisnya tidak menyebut baris
itu dan `lifecycle-recovery.md` mendaftar seksi yang berbeda dari yang ditulis agent, jadi kanal ini tidak pernah
terisi.
"""
import re

import pytest

from conftest import PLUGINS

BE = PLUGINS / "backend"
SECTIONS = ("## Stop condition / Trigger", "## Evidence", "## Working Tree & Partial Changes",
            "## Root Cause & Recommended Action")


def _read(rel):
    return (BE / rel).read_text(encoding="utf-8")


@pytest.mark.regression("25 R11")
def test_r11_penulis_report_menulis_umpan_balik_profil():
    agent = _read("agents/code-implementor.md")
    assert "Umpan balik profil:" in agent
    assert all(f"`{s}`" in agent for s in SECTIONS)


@pytest.mark.regression("25 R11")
def test_r11_pembaca_report_memakai_seksi_penulis():
    recovery = _read("skills/architect/references/lifecycle-recovery.md")
    contract = recovery.split("### Struktur Laporan Kegagalan", 1)[1].split("### ", 1)[0]
    assert all(s in contract for s in SECTIONS), contract
    assert "Umpan balik profil:" in contract
    assert re.search(r"Umpan balik profil:", _read("skills/architect/SKILL.md"))
