"""`skills/profile/scripts/migrate_profile.py` frontend (mode MIGRATE, L1.1)."""
import json

from conftest import PLUGINS, be_profile, fe_profile, git, run_script, write_files

SCRIPT = PLUGINS / "frontend/skills/profile/scripts/migrate_profile.py"


def test_migrate_moves_only_own_files(make_repo):
    root = make_repo()
    fe_profile(root, "react-vite", legacy=True)
    # sisa profil backend lama yang tertimpa sebagian
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


def test_migrate_tanpa_profil_lama_json_fail(make_repo):
    """Smoke L6.1: tanpa profil lama, `--json` tetap mencetak JSON dan pesannya tidak menuduh profil asing."""
    root = make_repo()
    proc = run_script(SCRIPT, "--json", "--root", str(root))
    assert proc.returncode == 1
    out = json.loads(proc.stdout)
    assert out["status"] == "FAIL" and "tidak ada" in out["error"], out


def test_migrate_index_rusak_disebut_rusak(make_repo):
    root = make_repo({".claude/profile/index.json": "{rusak"})
    proc = run_script(SCRIPT, "--root", str(root))
    assert proc.returncode == 1 and "bukan JSON" in proc.stderr, proc.stderr
