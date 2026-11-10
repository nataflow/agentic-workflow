"""Langkah 31 X1–X3, X5: balikan `code-explorer` berupa amplop ringkas; berkas laporan sumber kebenaran."""
import re

import pytest

from conftest import BE_SKILLS, PLUGINS

AGENT = PLUGINS / "backend" / "agents" / "code-explorer.md"
DISPATCHERS = ("tech-lead/dispatcher/explorer.md", "business-analysis/dispatcher/explorer.md",
               "system-analysis/dispatcher/explorer-surface.md", "system-analysis/dispatcher/explorer-blast.md",
               "plan/dispatcher/explorer.md", "debug/dispatcher/explorer.md")


def _read(path):
    return path.read_text(encoding="utf-8")


@pytest.mark.regression("31 X1")
def test_x1_agent_membalas_amplop_ringkas():
    pelaporan = _read(AGENT).split("## Pelaporan", 1)[1]
    assert "dua muara" not in pelaporan and "isi yang sama ke context" not in pelaporan
    assert "## Explorer Report — <slug>" in pelaporan and "Amplop maksimal 15 baris" in pelaporan
    amplop = pelaporan.split("```markdown", 1)[1].split("```", 1)[0].strip().splitlines()
    assert len(amplop) <= 8
    assert amplop[1].strip().startswith("confidence:") and "permukaan" in amplop[1] and "gaps" in amplop[1]
    assert any(l.strip().startswith("Berkas:") for l in amplop)
    assert "sumber kebenaran tunggal" in pelaporan and "ketiganya wajib sama" in pelaporan


@pytest.mark.regression("31 X2")
@pytest.mark.parametrize("rel", DISPATCHERS)
def test_x2_dispatcher_membaca_seksi_dari_berkas(rel):
    text = _read(BE_SKILLS / rel)
    assert "kembalikan badan laporan yang sama ke context" not in text
    assert "balas hanya dengan amplop ringkas" in text
    assert "**Subagent mengembalikan:** Amplop ringkas `## Explorer Report — <slug>`" in text
    balikan = text.split("### Penanganan Balikan", 1)[1]
    para = next(p for p in balikan.split("\n\n") if p.startswith("**Amplop, lalu seksi dari berkas"))
    format_block = text.split("Format laporan:", 1)[1].split("### Slot Hidrasi", 1)[0]
    headings = set(re.findall(r"^\s*(### [^\n]+?)\s*$", format_block, re.M))
    cited = set(re.findall(r"`(### [^`]+)`", para))
    if "explorer-surface" in rel:  # Profil S merujuk peta seksi lengkapnya
        assert "### Peta Seksi Laporan → Konsumen di PRD" in cited and "### Error Surface" in cited
        cited -= {"### Peta Seksi Laporan → Konsumen di PRD"}
    assert cited and cited <= headings, (cited - headings)


@pytest.mark.regression("31 X3")
def test_x3_gate_scope_tidak_menuntut_laporan_di_context():
    text = _read(BE_SKILLS / "tech-lead/references/gate-scope.md")
    assert "dikembalikan ke context" not in text and "sekaligus dikembalikan" not in text
    assert "amplop ringkas" in text and "### Key Pointers & Evidence` berkas laporan" in text
    assert "amplop pembungkus" not in "".join(_read(BE_SKILLS / r) for r in DISPATCHERS)


@pytest.mark.regression("31 X5")
@pytest.mark.parametrize("rel", ("system-analysis/references/analysis-protocol.md",
                                 "system-analysis/dispatcher/explorer-blast.md",
                                 "system-analysis/dispatcher/explorer-surface.md",
                                 "system-analysis/SKILL.md"))
def test_x5_profil_b_menunggu_amplop_profil_s(rel):
    text = _read(BE_SKILLS / rel)
    assert "Profil B menunggu Profil S" in text
    assert "amplop seluruh" in text and "Async agent launched" in text and "satu pesan" in text


@pytest.mark.regression("31 X5")
def test_x5_prompt_blast_memanen_flow_trace_profil_s():
    text = _read(BE_SKILLS / "system-analysis/dispatcher/explorer-blast.md")
    prompt = text.split("````markdown", 1)[1].split("Format laporan:", 1)[0]
    assert "Panen laporan Profil S" in prompt and "`### Flow & Trace`" in prompt
    guard = _read(BE_SKILLS / "system-analysis/SKILL.md").split("- **DISPATCH RESMI**", 1)[1].split("\n", 1)[0]
    assert "memberangkatkan Profil B sebelum amplop seluruh Profil S kembali" in guard
