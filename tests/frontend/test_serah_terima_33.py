"""Langkah 33 H1–H2, J2–J3: serah terima konteks di dua titik rantai frontend dan penulis/pembaca journey."""
import re

import pytest

from conftest import FE_SKILLS, PLUGINS, load_module

JOURNEY = FE_SKILLS / "_common" / "journey.py"
MATRIX = "lead/references/lane-routing-matrix.md"


def _read(rel):
    return (FE_SKILLS / rel).read_text(encoding="utf-8")


def _section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def _four_a():
    return _section(_read(MATRIX), "## 4a.", "\n---\n")


def _hops_in(text):
    return set(re.findall(r"journey\.py[»`]? add [^\n]*?--hop ([A-Z_]+)", text))


@pytest.mark.regression("33 H1")
def test_h1_blok_serah_terima_satu_rumah():
    four_a = _four_a()
    for wajib in ("/clear", "/compact", "/model sonnet", "/frontend:lead lanjutkan <taskdir>", "\"lanjut\"",
                  "Pilihannya milik user", "**berhenti**", "dua, dan hanya dua"):
        assert wajib in four_a, wajib
    # dua titik, MINOR tanpa titik CONTRACT tetapi berhenti sebelum architect
    assert "`CONTRACT` disetujui" in four_a and "`HOTFIX_MINOR` tidak punya hop ini" in four_a
    assert "`BRIEF` disetujui (seluruh lane, termasuk `HOTFIX_MINOR`)" in four_a
    # blok hanya ditulis di bagian 4a, gate menunjuknya
    for rel in ("contract/SKILL.md", "plan/SKILL.md", "lead/SKILL.md", "architect/SKILL.md"):
        assert "/frontend:lead lanjutkan" not in _read(rel), rel


@pytest.mark.regression("33 H1")
@pytest.mark.parametrize("rel,phase,end,berikut", [
    ("contract/SKILL.md", "### Phase 6", "## Guardrails", "`plan` berangkat hanya atas pilihan user"),
    ("plan/SKILL.md", "### Phase 5", "## Guardrails", "dilarang memanggil `frontend:architect` sebelum user memilih"),
])
def test_h1_gate_approve_berhenti_di_serah_terima(rel, phase, end, berikut):
    text = _read(rel)
    approval = _section(text, phase, end)
    assert "bagian 4a butir 3" in approval and "**berhenti**" in approval and berikut in approval
    output = text.split("## Output [REQUIRED]", 1)[1]
    first = output.strip().splitlines()[0]
    assert "serah terima sebelum frontend:" in first and "di main loop" not in first
    assert "bagian 4a butir 3" in first


def test_h1_opsi_approve_plan_tidak_menjanjikan_eksekusi():
    assert "*Setujui breakdown* ·" in _read("plan/SKILL.md")
    assert "lanjut eksekusi" not in _read("plan/SKILL.md")


@pytest.mark.regression("33 H2")
def test_h2_lanjutan_lewat_lead_melewati_sapuan():
    four_a = _four_a()
    butir4 = four_a.split("\n4. ", 1)[1]
    for wajib in ("melewati Phase 1", "Phase 3–7", "taskdir_state.py --taskdir <taskdir>", "journey.py» show",
                  "Disk menentukan tujuan, bukan journey", "permintaan baru"):
        assert wajib in butir4, wajib
    phase1 = _section(_read("lead/SKILL.md"), "### Phase 1", "### Phase 2")
    first = phase1.strip().splitlines()[2]
    assert first.startswith("- **Lanjutan serah terima**") and "lewati fase ini dan Phase 3–7" in first
    assert "--taskdir <taskdir>" in first and "journey.py show" in first and "bagian 4a butir 4" in first


@pytest.mark.regression("33 J2")
def test_j2_penulis_journey_memakai_hop_sah():
    mod = load_module(JOURNEY, "fe_journey_33_j2")
    found = {
        "lead/SKILL.md": {"LEAD", "REVIEW"},
        "ux-design/SKILL.md": {"FLOW"},
        "ui-design/SKILL.md": {"UI"},
        "contract/SKILL.md": {"CONTRACT"},
        "plan/SKILL.md": {"BRIEF"},
        "architect/SKILL.md": {"ARCHITECT"},
    }
    for rel, hops in found.items():
        assert _hops_in(_read(rel)) == hops, rel
        assert hops <= set(mod.HOPS), rel
    assert set().union(*found.values()) == set(mod.HOPS)
    # LEAD ditulis sesudah akar terkunci: journey.py menolak taskdir tanpa TASK.md
    phase7 = _section(_read("lead/SKILL.md"), "### Phase 7", "### Phase 8")
    assert phase7.index("TASK ROOT LOCKED") < phase7.index("--hop LEAD")


@pytest.mark.regression("33 J3")
def test_j3_pembaca_journey_dan_disk_menang():
    phase0 = _section(_read("architect/SKILL.md"), "### Phase 0", "### Phase 1")
    assert "journey.py show" in phase0 and "disk menang" in phase0
    four_a = _four_a()
    assert "Journey bukan sumber kebenaran" in four_a and "disk menang" in four_a
    # teks bebas tidak masuk Riwayat Rantai
    doc = JOURNEY.read_text(encoding="utf-8")
    assert "Teks bebas sengaja tidak masuk `## Riwayat Rantai`" in doc


def test_explorer_frontend_effort_medium():
    head = (PLUGINS / "frontend" / "agents" / "code-explorer.md").read_text(encoding="utf-8").split("---")[1]
    assert "\neffort: medium\n" in head and "\nmodel: sonnet\n" in head
