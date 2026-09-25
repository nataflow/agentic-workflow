"""`skills/profile/scripts/migrate_profile.py` backenddev (mode MIGRATE, L1.1)."""
import json

from conftest import PLUGINS, be_profile, fe_profile, git, run_script

SCRIPT = PLUGINS / "backenddev/skills/profile/scripts/migrate_profile.py"


def test_migrate_moves_only_own_files(make_repo):
    root = make_repo({".claude/profile/visual.md": "# fe leftover\n"})
    be_profile(root, "go", legacy=True)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    proc = run_script(SCRIPT, "--json", "--root", str(root))
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert len(out["moved"]) == 9
    assert out["leftovers"] == ["visual.md"]
    data = json.loads((root / ".claude/profile/backenddev/index.json").read_text())
    assert data["plugin"] == "backenddev"
    status = git(root, "status", "--porcelain")
    assert "R  .claude/profile/stack.md -> .claude/profile/backenddev/stack.md" in status


def test_migrate_refuses_foreign_profile(make_repo):
    root = make_repo()
    fe_profile(root, "react-vite", legacy=True)
    proc = run_script(SCRIPT, "--root", str(root))
    assert proc.returncode != 0


def test_migrate_refuses_when_new_location_exists(make_repo):
    root = make_repo()
    be_profile(root, "go", legacy=True)
    be_profile(root, "go")
    proc = run_script(SCRIPT, "--root", str(root))
    assert proc.returncode != 0
