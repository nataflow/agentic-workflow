"""Prasyarat `backend:tech-lead`: kepemilikan profil dan zona re-entry (L1.1)."""
import json

from conftest import PLUGINS, be_profile, fe_profile, git, run_script, write_files

SCRIPT = PLUGINS / "backend/skills/tech-lead/scripts/check_preconditions.py"
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
    migrate = PLUGINS / "backend/skills/profile/scripts/migrate_profile.py"
    assert run_script(migrate, "--root", str(root)).returncode == 0
    assert _check(_run(root, "--re-entry"), 3)["status"] == "PASS"


def test_frontend_profile_not_read_as_backend(make_repo):
    """Skenario C terbalik: profil frontend di lokasi lama → check 1 FAIL 'tidak ditemukan', bukan field hilang."""
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


# -- Langkah 5 (L5.5): porcelain -z dan zona artefak per segmen ----------------------------

def test_l55_reentry_berkas_unicode_di_zona_artefak(make_repo):
    from conftest import be_profile, commit, run_script, write_files, BE_SKILLS
    import json as _json
    root = make_repo({"src/a.go": "package a\n"})
    be_profile(root, "go")
    commit(root, "init")
    write_files(root, {"backenddev/docs/2601011200-refund/café.md": "x\n",
                       "backenddev/docs/2601011200-refund/catatan rapat.md": "x\n"})
    proc = run_script(BE_SKILLS / "tech-lead/scripts/check_preconditions.py", "--root", str(root),
                      "--re-entry", "--json")
    c = {c["id"]: c for c in _json.loads(proc.stdout)["checks"]}[3]
    # Langkah 24: penanda ignore ditulis sebelum tree dinilai, jadi dokumen taskdir tidak pernah tampak kotor.
    assert c["status"] == "PASS" and "bersih" in c["summary"], c
    assert (root / "backenddev/docs/.gitignore").is_file()
    write_files(root, {"backenddev/docsx/a.md": "x\n"})
    proc = run_script(BE_SKILLS / "tech-lead/scripts/check_preconditions.py", "--root", str(root),
                      "--re-entry", "--json")
    c = {c["id"]: c for c in _json.loads(proc.stdout)["checks"]}[3]
    assert c["status"] == "FAIL" and "backenddev/docsx/a.md" in c["summary"]


# -- Langkah 24 (G2): dokumen taskdir di luar git -----------------------------------------------

def test_g2_dokumen_ter_track_dirutekan_migrasi(make_repo):
    root = _committed_repo(make_repo)
    write_files(root, {"backenddev/docs/2601011200-refund/TASK.md": "# T\n"})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs: era git")
    c = _check(_run(root), 3)
    assert c["status"] == "FAIL" and c["summary"].startswith("MIGRASI: 1 berkas") and "docs_git.py migrate" in c["action"]
    assert _check(_run(root, "--re-entry"), 3)["status"] == "FAIL"
    assert not (root / "backenddev/docs/.gitignore").exists(), "penolakan tidak menulis penanda ignore"


def test_g2_read_only_tidak_menulis_penanda(make_repo):
    root = _committed_repo(make_repo)
    write_files(root, {"backenddev/docs/2601011200-refund/TASK.md": "# T\n"})
    assert _check(_run(root, "--read-only"), 3)["status"] == "PASS"
    assert not (root / "backenddev/docs/.gitignore").exists()
    assert _check(_run(root), 3)["status"] == "PASS"
    assert (root / "backenddev/docs/.gitignore").is_file()
    assert git(root, "status", "--porcelain") == ""
