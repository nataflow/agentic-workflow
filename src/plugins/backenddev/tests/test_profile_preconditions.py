"""Prasyarat `backenddev:profile`: deteksi via `detect.py`, kepemilikan, mode MIGRATE (L1.1)."""
import json

from conftest import PLUGINS, be_profile, fe_profile, run_script

SCRIPT = PLUGINS / "backenddev/skills/profile/scripts/check_preconditions.py"
REACT_VITE = json.dumps({"dependencies": {"react": "^19", "react-dom": "^19"}, "devDependencies": {"vite": "^6"}})
GIN = "module x\n\ngo 1.22\n\nrequire github.com/gin-gonic/gin v1.10.0\n"


def _run(root, *args):
    proc = run_script(SCRIPT, "--json", "--root", str(root), *args)
    return proc, json.loads(proc.stdout)


def _check(out, cid):
    return next(c for c in out["checks"] if c["id"] == cid)


def test_frontend_only_repo_fails_check1(make_repo):
    """Skenario D: repo React murni tidak lagi dianggap manifest backend."""
    root = make_repo({"package.json": REACT_VITE})
    fe_profile(root, "react-vite")
    proc, out = _run(root)
    assert proc.returncode == 1
    assert _check(out, 1)["status"] == "FAIL"


def test_legacy_frontend_profile_not_refresh(make_repo):
    root = make_repo({"go.mod": GIN})
    fe_profile(root, "react-vite", legacy=True)
    proc, out = _run(root)
    assert proc.returncode == 0
    assert out["mode"] == "GENERATE"
    assert "milik `frontenddev`" in _check(out, 6)["summary"]


def test_legacy_own_profile_is_migrate(make_repo):
    root = make_repo({"go.mod": GIN})
    be_profile(root, "go", legacy=True)
    _proc, out = _run(root)
    assert out["mode"] == "MIGRATE"


def test_own_profile_is_refresh(make_repo):
    root = make_repo({"go.mod": GIN})
    be_profile(root, "go")
    _proc, out = _run(root)
    assert out["mode"] == "REFRESH"


def test_foreign_profile_in_own_dir_fails(make_repo):
    root = make_repo({"go.mod": GIN})
    be_profile(root, "go", extra={"plugin": "frontenddev"})
    proc, out = _run(root)
    assert proc.returncode == 1
    assert _check(out, 6)["status"] == "FAIL"


def test_profile_dir_other_value_rejected(make_repo):
    """B3: `--profile-dir` selain `.claude/profile/backenddev` ditolak."""
    root = make_repo({"go.mod": GIN})
    proc, out = _run(root, "--profile-dir", "docs/elsewhere")
    assert proc.returncode == 1
    assert _check(out, 3)["status"] == "FAIL"


def test_text_output_prints_resolved_mode(make_repo):
    root = make_repo({"go.mod": GIN})
    proc = run_script(SCRIPT, "--root", str(root))
    assert "Terselesaikan: mode `GENERATE`" in proc.stdout
