"""Teks SKILL quickdev: namespace, deskripsi, koeksistensi dengan hook engineer (L1.3)."""
import re
import pytest

from conftest import PLUGINS

SKILLS = sorted((PLUGINS / "quickdev" / "skills").glob("*/SKILL.md"))
IDS = [p.parent.name for p in SKILLS]


def _frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    block = text.split("---\n", 2)[1]
    return dict(line.split(": ", 1) for line in block.splitlines() if ": " in line and not line.startswith(" "))


@pytest.mark.regression("34 D1")
def test_three_skills_present():
    assert IDS == ["execute", "plan", "review"]


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
    """K7: ketiga skill quickdev hanya dipanggil eksplisit lewat /quickdev:<skill>."""
    assert _frontmatter(path).get("disable-model-invocation") == "true"


@pytest.mark.regression("34 E1")
def test_execute_baseline_needs_permission_and_timeout():
    """L3.5/34 E1 — baseline dipindah ke execute: perintah berisiko ditanya dulu, bertimeout, tanpa migrasi."""
    text = (PLUGINS / "quickdev" / "skills" / "execute" / "SKILL.md").read_text(encoding="utf-8")
    fase0 = text.split("### Fase 0", 1)[1].split("\n### ", 1)[0]
    butir6 = fase0.split("6. Mode `awal`", 1)[1]
    assert "AskUserQuestion" in butir6 and "menyentuh DB/jaringan" in butir6
    assert butir6.index("AskUserQuestion") < butir6.index("plan_lock.py baseline")
    fase3 = text.split("### Fase 3", 1)[1].split("\n### ", 1)[0]
    assert "300000" in fase3 and "TIMEOUT" in fase3 and "pengubah skema/data tidak pernah dijalankan" in fase3


@pytest.mark.regression("34 P2")
def test_plan_tidak_menjalankan_perintah():
    text = (PLUGINS / "quickdev" / "skills" / "plan" / "SKILL.md").read_text(encoding="utf-8")
    assert "MUST NOT menjalankan perintah verifikasi, build, test, atau migrasi di skill ini" in text
    assert "| Jenis | Perintah | Cwd | Risiko |" in text
