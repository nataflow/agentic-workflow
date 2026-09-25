"""`skills/profile/scripts/migrate_profile.py` frontenddev (mode MIGRATE, L1.1)."""
import json

from conftest import PLUGINS, be_profile, fe_profile, git, run_script, write_files

SCRIPT = PLUGINS / "frontenddev/skills/profile/scripts/migrate_profile.py"


def test_migrate_moves_only_own_files(make_repo):
    root = make_repo()
    fe_profile(root, "react-vite", legacy=True)
    # sisa profil backenddev lama yang tertimpa sebagian
    write_files(root, {f".claude/profile/{f}.md": "# x\n"
                       for f in ("module-structure", "domain-map", "code-conventions", "anti-patterns")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    proc = run_script(SCRIPT, "--json", "--root", str(root))
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert len(out["moved"]) == 10
    assert out["leftovers"] == ["anti-patterns.md", "code-conventions.md", "domain-map.md", "module-structure.md"]
    data = json.loads((root / ".claude/profile/frontenddev/index.json").read_text())
    assert data["plugin"] == "frontenddev" and data["stack"] == "react-vite"
    assert not (root / ".claude/profile/index.json").exists()


def test_migrate_untracked_files(make_repo):
    root = make_repo()
    fe_profile(root, "react-vite", legacy=True)
    proc = run_script(SCRIPT, "--root", str(root))
    assert proc.returncode == 0, proc.stderr
    assert (root / ".claude/profile/frontenddev/stack.md").is_file()


def test_migrate_refuses_foreign_profile(make_repo):
    root = make_repo()
    be_profile(root, "node", legacy=True)
    proc = run_script(SCRIPT, "--root", str(root))
    assert proc.returncode != 0
    assert (root / ".claude/profile/index.json").is_file()
