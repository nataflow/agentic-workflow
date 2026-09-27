"""Prasyarat `frontend:profile` dan skrip hilir: kepemilikan profil dan mode MIGRATE (L1.1)."""
import json

from conftest import PLUGINS, be_profile, fe_profile, git, run_script

SCRIPT = PLUGINS / "frontend/skills/profile/scripts/check_preconditions.py"
UX = PLUGINS / "frontend/skills/ux-design/scripts/check_preconditions.py"
REACT_VITE = json.dumps({"dependencies": {"react": "^19", "react-dom": "^19"}, "devDependencies": {"vite": "^6"}})
FULLSTACK = {
    "package.json": json.dumps({"private": True, "workspaces": ["apps/*"]}),
    "apps/web/package.json": REACT_VITE,
    "apps/api/package.json": json.dumps({"dependencies": {"express": "^4"}}),
}


def _run(root, *args):
    proc = run_script(SCRIPT, "--json", "--root", str(root), *args)
    return proc, json.loads(proc.stdout)


def _check(out, cid):
    return next(c for c in out["checks"] if c["id"] == cid)


def test_foreign_profile_in_own_dir_fails(make_repo):
    root = make_repo({"package.json": REACT_VITE})
    fe_profile(root, "react-vite", extra={"plugin": "backenddev"})
    proc, out = _run(root)
    assert proc.returncode == 1
    assert _check(out, 6)["status"] == "FAIL"
    assert "milik `backenddev`" in _check(out, 6)["summary"]


def test_legacy_own_profile_resolves_mode_migrate(make_repo):
    root = make_repo({"package.json": REACT_VITE})
    fe_profile(root, "react-vite", legacy=True)
    proc, out = _run(root)
    assert proc.returncode == 0
    assert out["mode"] == "MIGRATE"


def test_legacy_backend_profile_is_not_refresh(make_repo):
    """Skenario C: profil backend di lokasi lama → GENERATE ke direktori sendiri, bukan REFRESH."""
    root = make_repo(FULLSTACK)
    be_profile(root, "node", legacy=True, source_root="apps/api")
    proc, out = _run(root)
    assert proc.returncode == 0
    assert out["mode"] == "GENERATE"
    assert "milik `backenddev`" in _check(out, 6)["summary"]
    assert out["profile_dir"] == ".claude/profile/frontenddev"


def test_own_profile_is_refresh(make_repo):
    root = make_repo({"package.json": REACT_VITE})
    fe_profile(root, "react-vite")
    _proc, out = _run(root)
    assert out["mode"] == "REFRESH"


def test_profile_dir_other_value_rejected(make_repo):
    root = make_repo({"package.json": REACT_VITE})
    proc, out = _run(root, "--profile-dir", "docs/elsewhere")
    assert proc.returncode == 1
    assert _check(out, 3)["status"] == "FAIL"


def test_cra_out_of_scope_reason(make_repo):
    root = make_repo({"package.json": json.dumps({"dependencies": {"react": "^18", "react-scripts": "5"}})})
    proc, out = _run(root)
    assert proc.returncode == 1
    assert "react-scripts" in _check(out, 1)["summary"]


def test_downstream_ignores_backend_profile(make_repo):
    """ux-design tidak lagi membaca profil backend sebagai profil frontend."""
    root = make_repo(FULLSTACK)
    be_profile(root, "node", legacy=True, source_root="apps/api")
    out = json.loads(run_script(UX, "--json", "--root", str(root), "--taskdir",
                                "frontenddev/docs/2601010000-x").stdout)
    c5 = _check(out, 5)
    assert c5["status"] == "FAIL"
    assert ".claude/profile/frontenddev/" in c5["summary"]


def test_downstream_reads_own_profile_in_fullstack(make_repo):
    root = make_repo(FULLSTACK)
    be_profile(root, "node", source_root="apps/api")
    fe_profile(root, "react-vite")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    out = json.loads(run_script(UX, "--json", "--root", str(root), "--taskdir",
                                "frontenddev/docs/2601010000-x").stdout)
    assert _check(out, 5)["status"] == "PASS"
    assert _check(out, 6)["status"] == "PASS"


def test_downstream_legacy_own_profile_notes_migrate(make_repo):
    root = make_repo({"package.json": REACT_VITE})
    fe_profile(root, "react-vite", legacy=True)
    out = json.loads(run_script(UX, "--json", "--root", str(root), "--taskdir",
                                "frontenddev/docs/2601010000-x").stdout)
    c5 = _check(out, 5)
    assert c5["status"] == "PASS" and "MIGRATE" in c5["summary"]
