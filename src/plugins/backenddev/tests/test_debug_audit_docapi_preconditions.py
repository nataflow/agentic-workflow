"""Prasyarat `debug`, `audit`, `document-api`: taskdir kanonik (L5.2), profil & adapter plugin (L5.5)."""
import json

from conftest import be_checks, be_profile, commit

TD = "backenddev/docs/2601011200-refund"


def repo_with(make_repo, **kw):
    root = make_repo({f"{TD}/.keep": "", "src/a.go": "package a\n"})
    be_profile(root, "go", **kw)
    commit(root, "init")
    return root


def test_debug_taskdir_pola_ditegakkan(make_repo):
    root = repo_with(make_repo)
    c = be_checks(root, "debug/scripts/check_preconditions.py", "--root", str(root), "--taskdir", "src",
                  "--symptom", "x")[5]
    assert c["status"] == "FAIL" and "pola kanonik" in c["summary"]
    c = be_checks(root, "debug/scripts/check_preconditions.py", "--root", str(root), "--taskdir", TD,
                  "--symptom", "x")[5]
    assert c["status"] == "PASS"


def test_audit_adapter_dari_plugin(make_repo):
    root = repo_with(make_repo)
    checks = be_checks(root, "audit/scripts/check_preconditions.py", "--root", str(root))
    assert checks[2]["status"] == "PASS" and checks[3]["status"] == "PASS"
    idx = root / ".claude/profile/backenddev/index.json"
    idx.write_text(json.dumps({**json.loads(idx.read_text()), "stack": "cobol"}))
    assert be_checks(root, "audit/scripts/check_preconditions.py", "--root", str(root))[3]["status"] == "FAIL"


def test_document_api_stack_eksplisit_tanpa_profil(make_repo):
    root = make_repo({"src/a.go": "package a\n"})
    commit(root, "init")
    c = be_checks(root, "document-api/scripts/check_preconditions.py", "--root", str(root), "--stack", "go")[2]
    assert c["status"] == "PASS"
    c = be_checks(root, "document-api/scripts/check_preconditions.py", "--root", str(root))[2]
    assert c["status"] == "FAIL" and "--stack kosong" in c["summary"]


def test_profil_kurang_kunci_gagal_di_hulu(make_repo):
    root = make_repo({f"{TD}/.keep": "", "src/a.go": "package a\n"})
    d = be_profile(root, "go")
    data = json.loads((d / "index.json").read_text())
    del data["branch_convention"]
    (d / "index.json").write_text(json.dumps(data))
    commit(root, "init")
    for script, cid, args in (("debug/scripts/check_preconditions.py", 1, ("--taskdir", TD, "--symptom", "x")),
                              ("audit/scripts/check_preconditions.py", 2, ())):
        c = be_checks(root, script, "--root", str(root), *args)[cid]
        assert c["status"] == "FAIL" and "branch_convention" in c["summary"], script
