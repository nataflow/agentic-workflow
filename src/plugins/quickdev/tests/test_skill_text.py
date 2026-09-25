"""Teks SKILL quickdev: namespace, deskripsi, koeksistensi dengan hook engineer (L1.3)."""
import re
from pathlib import Path

import pytest

SKILLS = sorted((Path(__file__).resolve().parents[1] / "skills").glob("*/SKILL.md"))
IDS = [p.parent.name for p in SKILLS]


def _frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    block = text.split("---\n", 2)[1]
    return dict(line.split(": ", 1) for line in block.splitlines() if ": " in line and not line.startswith(" "))


def test_six_skills_present():
    assert IDS == ["clarify", "execute", "explore", "plan", "profile", "review"]


@pytest.mark.parametrize("path", SKILLS, ids=IDS)
def test_no_unnamespaced_gate_refs(path):
    text = path.read_text(encoding="utf-8")
    bad = re.findall(r"[Gg]ate `(?:profile|explore|clarify|plan|execute|review)`|gate berikutnya|gate hilir", text)
    assert not bad, bad


@pytest.mark.parametrize("path", SKILLS, ids=IDS)
def test_descriptions_prefixed(path):
    desc = _frontmatter(path)["description"]
    assert desc.startswith("Alur ringan quickdev")
    assert len(desc) <= 1536
    assert ": " not in desc  # plain scalar YAML


@pytest.mark.parametrize("path", SKILLS, ids=IDS)
def test_koeksistensi_section_present(path):
    text = path.read_text(encoding="utf-8")
    assert "\n## Koeksistensi [REQUIRED]\n" in text
    assert text.index("## Precondition [REQUIRED]") < text.index("## Koeksistensi [REQUIRED]")


@pytest.mark.parametrize("path", SKILLS, ids=IDS)
def test_disable_model_invocation(path):
    """K7: keenam skill quickdev hanya dipanggil eksplisit lewat /quickdev:<skill>."""
    assert _frontmatter(path).get("disable-model-invocation") == "true"


def test_profile_baseline_needs_permission_and_timeout():
    """L3.5 — baseline quickdev:profile dijalankan hanya sesudah izin, bertimeout, tanpa migrasi."""
    root = Path(__file__).resolve().parents[1] / "skills" / "profile"
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    fase2 = text.split("### Fase 2", 1)[1].split("\n### ", 1)[0]
    assert "AskUserQuestion" in fase2 and "TIMEOUT" in fase2 and "timeout" in fase2
    assert fase2.index("AskUserQuestion") < fase2.index("3. Jalankan perintah yang disetujui")
    assert "git status --porcelain" in fase2
    assert "`TIMEOUT`" in text.split("## Output", 1)[1]
    tpl = (root / "references" / "backend-profile-template.md").read_text(encoding="utf-8")
    for line in tpl.splitlines():
        if re.search(r"migrate (dev|deploy)|upgrade head", line):
            assert "Migration Apply Command" in line, line
