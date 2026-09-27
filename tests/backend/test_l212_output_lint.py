"""L2.12 — rantai selesai ber-P2 punya bentuk keluaran `COMPLETED (WARNING)`."""
from conftest import BE_SKILLS


def test_completed_warning_form_documented():
    text = (BE_SKILLS / "architect/SKILL.md").read_text(encoding="utf-8")
    assert "COMPLETED (WARNING)" in text
    block = text.split("### ARCHITECT EXECUTION REPORT — <BLOCKED | TERTAHAN>", 1)[1]
    review = next(l for l in block.splitlines() if l.startswith("- **Review**:"))
    assert "P2" not in review


def test_gate_maps_warning_as_done():
    text = (BE_SKILLS / "tech-lead/SKILL.md").read_text(encoding="utf-8")
    assert "`COMPLETED (WARNING)`" in text
