"""Prasyarat `backenddev:tech-lead`: kepemilikan profil dan zona re-entry (L1.1)."""
import json

from conftest import PLUGINS, be_profile, fe_profile, git, run_script, write_files

SCRIPT = PLUGINS / "backenddev/skills/tech-lead/scripts/check_preconditions.py"
GIN = "module x\n\ngo 1.22\n\nrequire github.com/gin-gonic/gin v1.10.0\n"


def _run(root, *args):
    proc = run_script(SCRIPT, "--json", "--root", str(root), *args)
    return json.loads(proc.stdout)


def _check(out, cid):
    return next(c for c in out["checks"] if c["id"] == cid)


def _committed_repo(make_repo):
    root = make_repo({"go.mod": GIN, "internal/a.go": "package a\n"})
    be_profile(root, "go", source_root="internal")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    return root


def test_reentry_allows_own_profile_dir_only(make_repo):
    root = _committed_repo(make_repo)
    write_files(root, {".claude/profile/backenddev/commands.md": "# changed\n"})
    assert _check(_run(root, "--re-entry"), 3)["status"] == "PASS"
    fe_profile(root, "react-vite")
    assert _check(_run(root, "--re-entry"), 3)["status"] == "FAIL"


def test_reentry_allows_legacy_deletions_during_migrate(make_repo):
    root = make_repo({"go.mod": GIN, "internal/a.go": "package a\n"})
    be_profile(root, "go", legacy=True, source_root="internal")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    migrate = PLUGINS / "backenddev/skills/profile/scripts/migrate_profile.py"
    assert run_script(migrate, "--root", str(root)).returncode == 0
    assert _check(_run(root, "--re-entry"), 3)["status"] == "PASS"


def test_frontend_profile_not_read_as_backend(make_repo):
    """Skenario C terbalik: profil frontenddev di lokasi lama → check 1 FAIL 'tidak ditemukan', bukan field hilang."""
    root = make_repo({"go.mod": GIN})
    fe_profile(root, "react-vite", legacy=True)
    c1 = _check(_run(root), 1)
    assert c1["status"] == "FAIL"
    assert ".claude/profile/backenddev/index.json" in c1["summary"]


def test_fullstack_both_profiles_check1_pass(make_repo):
    root = make_repo({"apps/api/package.json": json.dumps({"dependencies": {"express": "^4"}}),
                      "apps/api/src/a.ts": ""})
    be_profile(root, "node", source_root="apps/api/src")
    fe_profile(root, "react-vite")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    assert _check(_run(root), 1)["status"] == "PASS"
