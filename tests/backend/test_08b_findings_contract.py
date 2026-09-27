"""B1/B2/B18 — satu kontrak temuan (severity, ID, index) dirujuk audit, reviewer, dan architect."""
import re

import pytest

from conftest import PLUGINS

BE = PLUGINS / "backend"
CONTRACT = BE / "skills/audit/references/findings-contract.md"
INDEX_HEADER = "| Tanggal | File | Target | P1 | P2 | P3 | Status |"


def _md_files():
    return sorted(p for p in BE.rglob("*.md") if p != CONTRACT)


def test_b1_header_index_hanya_di_kontrak():
    assert INDEX_HEADER in CONTRACT.read_text(encoding="utf-8")
    bad = [str(p.relative_to(BE)) for p in _md_files() if INDEX_HEADER in p.read_text(encoding="utf-8")]
    assert not bad, bad


@pytest.mark.parametrize("pattern", [r"Date \| Issue ID", r"SEC-01", r"diff: ", r"\*\*P[123] \((Critical|Major|Minor)"])
def test_b1_b2_bentuk_lama_hilang(pattern):
    bad = [f"{p.relative_to(BE)}" for p in [CONTRACT, *_md_files()]
           if re.search(pattern, p.read_text(encoding="utf-8"))]
    assert not bad, bad


@pytest.mark.parametrize("rel", ["agents/code-reviewer.md", "skills/architect/dispatcher/reviewer.md",
                                 "skills/architect/SKILL.md", "skills/audit/SKILL.md",
                                 "skills/audit/templates/issues-template.md",
                                 "skills/architect/references/lifecycle-recovery.md"])
def test_b2_severity_dirujuk_bukan_disalin(rel):
    text = (BE / rel).read_text(encoding="utf-8")
    assert "findings-contract.md" in text or "{findings_contract}" in text, rel
    assert not re.search(r"^- \*\*P[123]\*\* —", text, re.M), f"{rel}: definisi severity tandingan"


def test_b2_invariant_dan_scope_p1_di_kontrak():
    row = next(l for l in CONTRACT.read_text(encoding="utf-8").splitlines() if l.startswith("| P1 |"))
    assert "`## Invariants`" in row and "`## File scope`" in row


def test_b18_amplop_reviewer_lima_baris():
    text = (BE / "agents/code-reviewer.md").read_text(encoding="utf-8")
    block = text.split("## Format Output", 1)[1].split("```markdown\n", 1)[1].split("```", 1)[0]
    lines = [l for l in block.splitlines() if l.strip()]
    assert len(lines) == 5 and lines[0] == "## Reviewer Report — {taskdir}"
    assert "- Status: DONE | BLOCKED" in block and "backenddev/docs/<taskdir>" not in block
    assert "Status: PASS" not in text
    assert "Triase `COMPLETED`" not in (BE / "skills/architect/SKILL.md").read_text(encoding="utf-8")
