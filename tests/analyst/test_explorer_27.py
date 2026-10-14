"""Langkah 27 — subagent `code-explorer` untuk `analyst:elicit`, `code-scout` sonnet khusus `notulen` (E1–E6).

Explorer read-only tanpa `Write`, sehingga analyst tetap tanpa hook. Format balikan tinggal di berkas agent dan dibaca
dispatcher `elicit`; angka jendela bacanya dipaku ke `code-explorer` backend sumbernya (K14).
"""
import re

import pytest

from conftest import PLUGINS, load_module

ANALYST = PLUGINS / "analyst"
AGENT = ANALYST / "agents" / "code-explorer.md"
SCOUT = ANALYST / "agents" / "code-scout.md"
DISPATCHER = ANALYST / "skills" / "elicit" / "dispatcher" / "explorer.md"
ELICIT = ANALYST / "skills" / "elicit"
INTAKE = ANALYST / "skills" / "intake"
SUMBER = PLUGINS / "backend" / "agents" / "code-explorer.md"
PROSA = (ELICIT / "SKILL.md", ELICIT / "references" / "elicitation-tech.md",
         ELICIT / "references" / "elicitation-guide.md", INTAKE / "SKILL.md", INTAKE / "references" / "batch.md",
         DISPATCHER)
SLOTS = ("{mode}", "{tipe}", "{category}", "{root}", "{batas}", "{kedalaman}", "{pertanyaan}")
ASPEK = ("Perilaku", "Aktor", "Aturan", "Status", "Pesan", "Struktur")
lib = load_module(ANALYST / "skills" / "_common" / "analyst_lib.py", "analyst_lib_27e")


def read(path):
    return path.read_text(encoding="utf-8")


# --- E1: agent ----------------------------------------------------------------------------------

@pytest.mark.regression("27 E1")
def test_e1_explorer_read_only_sonnet_untuk_elicit():
    fm, _ = lib.split_frontmatter(read(AGENT))
    assert fm["name"] == "code-explorer"
    assert [t.strip() for t in fm["tools"].split(",")] == ["Read", "Grep", "Glob"]
    assert fm["model"] == "sonnet" and str(fm["maxTurns"]).isdigit()
    assert "analyst:elicit" in fm["description"] and len(fm["description"]) <= 1536


@pytest.mark.regression("27 E1")
def test_e1_balikan_dan_kuota_di_agent():
    _, body = lib.split_frontmatter(read(AGENT))
    assert "## Code Explorer" in body and "Pemanggilan: <n> dari <20 | 40>" in body
    for section in ("### Ditemukan", "#### P1", "### Tidak ditemukan", "### Belum disisir"):
        assert section in body
    for aspek in ASPEK:
        assert f"- {aspek}:" in body
    assert "`ringkas` 20 pemanggilan" in body and "`menyeluruh` 40" in body
    for kolom in ("Confidence", "Profil", "Kedalaman", "Tipe"):
        assert f"- {kolom}:" in body


@pytest.mark.regression("27 E1")
def test_e1_larangan_dan_tabel_per_tipe():
    _, body = lib.split_frontmatter(read(AGENT))
    for larangan in ("`.env*`", "mendiagnosis penyebab bug", "Dilarang menulis `path:baris` yang tidak kamu baca"):
        assert larangan in body
    for tipe in ("`FEATURE`, `IMPROVEMENT`", "`BUG`", "`TECH` `REFACTOR`", "`TECH` `DATA_MODEL`",
                 "`TECH` `ARCHITECTURE`", "`TECH` `PERFORMANCE`", "`TECH` `DEPENDENCY`"):
        assert f"| {tipe} |" in body, tipe
    assert "${CLAUDE_PLUGIN_ROOT}" not in body


@pytest.mark.regression("27 K14")
def test_k14_jendela_baca_sama_dengan_sumber_backend():
    agent, sumber = read(AGENT), read(SUMBER)
    for angka in ("max(1, L - 15)", "L + 35", "30–50 baris", "100 baris", "120 baris", "3 jendela", "400 baris"):
        assert angka in agent and angka in sumber, angka


# --- E2: dispatcher -----------------------------------------------------------------------------

@pytest.mark.regression("27 E2")
def test_e2_dispatcher_slot_dan_hidrasi():
    text = read(DISPATCHER)
    assert "agents/code-explorer.md" in text and "`analyst:code-explorer`" in text
    prompt, _, rest = text.partition("### Slot Hidrasi")
    for slot in SLOTS:
        assert slot in prompt, slot
        assert f"| `{slot}` |" in rest, slot
    assert "`TECH` → `menyeluruh`; tipe lain → `ringkas`" in rest


@pytest.mark.regression("27 E2")
def test_e2_penanganan_balikan_memakai_seksi_agent():
    _, body = lib.split_frontmatter(read(AGENT))
    handling = read(DISPATCHER).partition("### Penanganan Balikan")[2]
    for seksi in ("Ditemukan", "Tidak ditemukan", "Belum disisir"):
        assert f"### {seksi}" in body and f"| `{seksi}`" in handling, seksi
    assert "`## Code Explorer`" in handling and "Repo: tanpa kode" in body
    for aspek in ("Perilaku", "Aturan", "Struktur"):
        assert f"`{aspek}`" in handling, aspek


# --- E3/E4: prosa -------------------------------------------------------------------------------

@pytest.mark.regression("27 E3")
def test_e3_prosa_tidak_lagi_memakai_scout():
    for path in PROSA:
        assert "code-scout" not in read(path), path.relative_to(ANALYST)
    assert not (ELICIT / "dispatcher" / "scout.md").exists()


@pytest.mark.regression("27 E3")
def test_e3_nama_agent_ditulis_penuh():
    """K11: nama pendek hanya boleh muncul saat membedakannya dari agent plugin lain."""
    for path in PROSA:
        for no, line in enumerate(read(path).splitlines(), 1):
            if "`code-explorer`" in line:
                assert "plugin" in line, f"{path.relative_to(ANALYST)}:{no}"
    for line in read(ELICIT / "SKILL.md").splitlines() + read(INTAKE / "references" / "batch.md").splitlines():
        for target in re.findall(r"dispatch\w*\s+`([^`]+)`", line):
            assert target == "analyst:code-explorer", line[:80]


@pytest.mark.regression("27 E3")
def test_e3_temuan_konteks_jadi_asumsi_bukan_aturan():
    skill = read(ELICIT / "SKILL.md")
    assert "`Kondisi Saat Ini` tetap diceritakan peminta" not in skill
    assert "**Keadaan sekarang ditulis lebih dulu.**" in skill
    assert "**Aturan sekarang bukan aturan yang diminta.**" in skill
    assert "**KODE LEWAT EXPLORER**" in skill and "**KODE SEBAGAI KONTEKS**" in skill
    assert "`mode: KONTEKS` kedalaman `ringkas`" in skill and "`mode: BUKTI` kedalaman `menyeluruh`" in skill
    assert "tanpa blok `## Code Explorer`" in skill


@pytest.mark.regression("27 E4")
def test_e4_intake_tetap_nol_kode():
    intake = read(INTAKE / "SKILL.md")
    assert "**NOL KODE**" in intake and "`analyst:code-explorer`" in intake
    batch = read(INTAKE / "references" / "batch.md")
    assert "## 6. Penelusuran Kode Awal Batch" in batch and "2 dispatch explorer" in batch


# --- E5: code-scout khusus notulen --------------------------------------------------------------

@pytest.mark.regression("27 E5")
def test_e5_scout_sonnet_khusus_notulen():
    fm, body = lib.split_frontmatter(read(SCOUT))
    assert fm["model"] == "sonnet"
    assert "analyst:notulen" in fm["description"] and "analyst:elicit" not in fm["description"]
    assert "BUKTI" not in body and "- Mode: KONTEKS" in body
    assert "Pemanggilan: <n> dari 8" in body
    notulen = read(ANALYST / "skills" / "notulen" / "dispatcher" / "scout.md")
    assert "BUKTI" not in notulen and "agents/code-scout.md" in notulen
