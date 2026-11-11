"""32 E1–E2 — Profil S mode delta atas laporan gerbang; `plan` memanen laci Profil S/B sebelum mendispatch."""
import re

import pytest

from conftest import BE_SKILLS


def _read(rel):
    return (BE_SKILLS / rel).read_text(encoding="utf-8")


@pytest.mark.regression("32 E1")
def test_profil_s_punya_slot_mode_delta_opsional():
    surface = _read("system-analysis/dispatcher/explorer-surface.md")
    body = surface.split("````markdown", 1)[1].split("````", 1)[0]
    delta = next(l for l in body.splitlines() if "{laporan_gerbang}" in l)
    # satu baris utuh: render menghapusnya bila slot opsional kosong
    assert delta.startswith("Mode delta:") and "### Error Surface" in delta and "jangan menelusuri ulang letaknya" in delta
    row = next(l for l in surface.splitlines() if l.startswith("| `{laporan_gerbang}`"))
    assert "**[OPTIONAL]**" in row and "hapus barisnya utuh" in row
    # kedalaman tetap dipatok
    assert "Kedalaman: menyeluruh" in body


@pytest.mark.regression("32 E1")
def test_protokol_tahap0_mengatur_mode_delta():
    proto = _read("system-analysis/references/analysis-protocol.md")
    assert "**Profil S mode delta (32 E1).**" in proto
    para = proto.split("**Profil S mode delta (32 E1).**", 1)[1].split("\n\n", 1)[0]
    assert "`confidence: low`" in para and "Profil S penuh" in para and "`menyeluruh` tetap dipatok" in para
    assert "`laporan_gerbang` (mode delta)" in proto
    assert "mode delta" in _read("system-analysis/SKILL.md")


@pytest.mark.regression("32 E2")
def test_plan_memanen_laci_sebelum_dispatch():
    sec = _read("plan/references/slicing-and-scan.md").split("### 2A.", 1)[1].split("### 2B.", 1)[0]
    assert sec.index("Panen laci lebih dulu (32 E2)") < sec.index("tandai unit yang butuh penelusuran")
    for wajib in ("**Unit tertutup**", "dimensi 11 `### Blast Map`", "**Celah tercatat**", "dispatch-nya **delta**",
                  "`confidence: low`"):
        assert wajib in sec, wajib
    fase2 = _read("plan/SKILL.md").split("### Fase 2", 1)[1].split("### Fase 3", 1)[0]
    assert re.search(r"tertutup laci tidak didispatch", fase2)
    assert "Dispatch delta (32 E2)" in _read("plan/dispatcher/explorer.md")
