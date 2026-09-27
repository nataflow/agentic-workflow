"""Resolver profil dan kesegaran profil di `skills/_common/precondition_lib.py` backend."""
import importlib.util
import sys

from conftest import PLUGINS, be_profile, fe_profile, git, write_files

_spec = importlib.util.spec_from_file_location(
    "backend_precondition_lib", PLUGINS / "backend/skills/_common/precondition_lib.py")
lib = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = lib
_spec.loader.exec_module(lib)


def test_resolve_profile_dir_prefers_new_location(make_repo):
    root = make_repo()
    be_profile(root, "go", legacy=True)
    be_profile(root, "go")
    path, note = lib.resolve_profile_dir(root)
    assert path == root / ".claude/profile/backenddev" and note == ""


def test_resolve_profile_dir_legacy_own_with_note(make_repo):
    root = make_repo()
    be_profile(root, "go", legacy=True)
    path, note = lib.resolve_profile_dir(root)
    assert path == root / ".claude/profile" and "MIGRATE" in note


def test_resolve_profile_dir_ignores_foreign_legacy(make_repo):
    root = make_repo()
    fe_profile(root, "react-vite", legacy=True)
    path, note = lib.resolve_profile_dir(root)
    assert path == root / ".claude/profile/backenddev" and note == ""


def test_profile_staleness_ignores_frontend_profile_commits(make_repo):
    root = make_repo({"src/a.go": "package a\n"})
    be_profile(root, "go")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "profile")
    write_files(root, {"src/b.go": "package a\n"})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "code")
    assert lib.profile_staleness(root, "src")[0] == "BASI"
    fe_profile(root, "react-vite")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs: frontend profile")
    assert lib.profile_staleness(root, "src")[0] == "BASI"
