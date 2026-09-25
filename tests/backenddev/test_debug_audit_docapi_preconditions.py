"""Prasyarat `debug`, `audit`, `document-api`: taskdir kanonik (L5.2), profil & adapter plugin (L5.5)."""
import json

import pytest

from conftest import PLUGINS, be_checks, be_profile, be_run, commit, load_module

TD = "backenddev/docs/2601011200-refund"


def repo_with(make_repo, **kw):
    root = make_repo({f"{TD}/.keep": "", "src/a.go": "package a\n"})
    be_profile(root, "go", **kw)
    commit(root, "init")
    return root


def test_debug_taskdir_pola_ditegakkan(make_repo):
    root = repo_with(make_repo)
    c = be_checks(root, "debug/scripts/check_preconditions.py", "--root", str(root), "--taskdir", "src")[5]
    assert c["status"] == "FAIL" and "pola kanonik" in c["summary"]
    c = be_checks(root, "debug/scripts/check_preconditions.py", "--root", str(root), "--taskdir", TD)[5]
    assert c["status"] == "PASS"


def test_audit_adapter_dari_plugin(make_repo):
    root = repo_with(make_repo)
    checks = be_checks(root, "audit/scripts/check_preconditions.py", "--root", str(root))
    assert checks[2]["status"] == "PASS" and checks[3]["status"] == "PASS"
    idx = root / ".claude/profile/backenddev/index.json"
    idx.write_text(json.dumps({**json.loads(idx.read_text()), "stack": "cobol"}))
    assert be_checks(root, "audit/scripts/check_preconditions.py", "--root", str(root))[3]["status"] == "FAIL"


def test_b3_document_api_wajib_profil(make_repo):
    """B3: `--stack`/`--base-branch` dihapus; stack hanya dari profil."""
    root = make_repo({"src/a.go": "package a\n"})
    commit(root, "init")
    DOC = "document-api/scripts/check_preconditions.py"
    assert be_run(root, DOC, "--root", str(root), "--stack", "go").returncode == 2
    assert be_run(root, DOC, "--root", str(root), "--domain", "x", "--base-branch", "main").returncode == 2
    c = be_checks(root, DOC, "--root", str(root), "--domain", "order")[2]
    assert c["status"] == "FAIL" and "index.json" in c["summary"]
    be_profile(root, "go")
    checks = be_checks(root, DOC, "--root", str(root), "--domain", "order")
    assert checks[2]["status"] == "PASS" and "## API surface" in checks[2]["summary"]
    assert all(c["status"] == "PASS" for c in checks.values()) and len(checks) == 6


def test_b3_document_api_domain_wajib(make_repo):
    root = repo_with(make_repo)
    for args in ((), ("--domain", "  ")):
        c = be_checks(root, "document-api/scripts/check_preconditions.py", "--root", str(root), *args)[6]
        assert c["status"] == "FAIL" and "domain kosong" in c["summary"]


def test_profil_kurang_kunci_gagal_di_hulu(make_repo):
    root = make_repo({f"{TD}/.keep": "", "src/a.go": "package a\n"})
    d = be_profile(root, "go")
    data = json.loads((d / "index.json").read_text())
    del data["branch_convention"]
    (d / "index.json").write_text(json.dumps(data))
    commit(root, "init")
    for script, cid, args in (("debug/scripts/check_preconditions.py", 1, ("--taskdir", TD)),
                              ("audit/scripts/check_preconditions.py", 2, ())):
        c = be_checks(root, script, "--root", str(root), *args)[cid]
        assert c["status"] == "FAIL" and "branch_convention" in c["summary"], script


# --- B5 / B3 (debug) / B7a ---------------------------------------------------------------------
DEBUG = "debug/scripts/check_preconditions.py"


def test_b5_symptom_tidak_lagi_diterima(make_repo):
    root = repo_with(make_repo)
    r = be_run(root, DEBUG, "--root", str(root), "--taskdir", TD, "--symptom", "x")
    assert r.returncode == 2 and "unrecognized arguments" in r.stderr


def test_b5_debug_lolos_tanpa_symptom(make_repo):
    root = repo_with(make_repo)
    checks = be_checks(root, DEBUG, "--root", str(root), "--taskdir", TD)
    assert all(c["status"] == "PASS" for c in checks.values()) and len(checks) == 7


@pytest.mark.parametrize("hint, status", [("-", "PASS"), ("", "PASS"), ("src/a.go", "PASS"), ("src", "PASS"),
                                          ("/tidak/ada", "FAIL"), ("src/b.go", "FAIL"), ("../luar", "FAIL")])
def test_b3_debug_scope_hint(make_repo, hint, status):
    root = repo_with(make_repo)
    (root.parent / "luar").mkdir(exist_ok=True)
    c = be_checks(root, DEBUG, "--root", str(root), "--taskdir", TD, "--scope-hint", hint)[7]
    assert c["status"] == status, c


def test_b7_adapter_tanpa_failure_signatures(tmp_path):
    lib = load_module(PLUGINS / "backenddev/skills/_common/precondition_lib.py", "pl_b7")
    stacks = tmp_path / "skills/profile/stacks"
    stacks.mkdir(parents=True)
    (stacks / "go.md").write_text("# go\n\n## Commands\n\n```\n## Failure signatures\n```\n")
    path, err = lib.stack_adapter_section("go", "## Failure signatures", base=tmp_path)
    assert path is None and "tanpa seksi" in err
    (stacks / "go.md").write_text("# go\n\n## Failure signatures\n\n- x\n")
    assert lib.stack_adapter_section("go", "## Failure signatures", base=tmp_path)[0] is not None
    assert "tidak ditemukan" in lib.stack_adapter_section("cobol", "## Failure signatures", base=tmp_path)[1]
