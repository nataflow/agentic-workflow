"""Lint path profil: tiap plugin engineer hanya merujuk `.claude/profile/<plugin>/` (L1.1)."""
import re

import pytest

from conftest import PLUGINS

ENGINEERS = ("backenddev", "frontenddev")
# Rumah resolver dan detektor — satu-satunya tempat path profil dibentuk.
PY_ALLOWED = {"skills/_common/precondition_lib.py", "hooks/detect.py", "hooks/gate_text.py",
              "skills/profile/scripts/migrate_profile.py"}
PY_HARDCODED = re.compile(r'"\.claude" / "profile"|\.claude/profile"')
# Baris yang memang menyebut lokasi lama.
LEGACY_OK = re.compile(r"MIGRATE|lokasi lama|profil lama|index\.json` lama|plugin lain|migrate_profile|git log --oneline -- \.claude/profile/index\.json")


@pytest.mark.parametrize("plugin", ENGINEERS)
def test_no_hardcoded_profile_path_in_python(plugin):
    root = PLUGINS / plugin
    bad = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if rel in PY_ALLOWED or rel.startswith("tests/"):
            continue
        for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if PY_HARDCODED.search(line):
                bad.append(f"{rel}:{no}: {line.strip()}")
    assert not bad, "\n".join(bad)


@pytest.mark.parametrize("plugin", ENGINEERS)
def test_markdown_profile_paths_namespaced(plugin):
    root = PLUGINS / plugin
    pattern = re.compile(r"\.claude/profile(?!/" + plugin + r")")
    bad = []
    for path in root.rglob("*.md"):
        for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line) and not LEGACY_OK.search(line):
                bad.append(f"{path.relative_to(root).as_posix()}:{no}: {line.strip()[:160]}")
    assert not bad, "\n".join(bad)


def test_no_old_shell_hook_references():
    bad = []
    for path in PLUGINS.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".py", ".json", ".sh"):
            text = path.read_text(encoding="utf-8")
            if "lead-gate.sh" in text:
                bad.append(path.relative_to(PLUGINS).as_posix())
    assert not bad, bad
