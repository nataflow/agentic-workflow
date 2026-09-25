"""B4 — prasyarat audit: `source_root` di luar repo tanpa crash, vonis target diff/PR berjangkar, dimensi divalidasi."""
import json

import pytest

from conftest import be_checks, be_profile, be_run, commit

AUDIT = "audit/scripts/check_preconditions.py"


@pytest.fixture
def repo(make_repo):
    root = make_repo({"src/order/service.go": "package order\n"})
    be_profile(root, "go")
    commit(root, "init")
    return root


def _checks(root, *args):
    proc = be_run(root, AUDIT, "--json", "--root", str(root), *args)
    assert "Traceback" not in proc.stderr, proc.stderr
    assert proc.stdout.strip(), proc.stderr
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


def test_b4_source_root_absolut_di_luar_repo_fail_rapi(repo, tmp_path):
    outside = tmp_path / "elsewhere" / "src"
    outside.mkdir(parents=True)
    idx = repo / ".claude/profile/backenddev/index.json"
    idx.write_text(json.dumps({**json.loads(idx.read_text()), "source_root": str(outside)}))
    c = _checks(repo, "--target-scope", "src/order")[1]
    assert c["status"] == "FAIL" and "di luar root" in c["summary"]


@pytest.mark.parametrize("scope", ["src/expr/", "src/pr/x", "src/origin/y"])
def test_b4_path_nyata_tidak_divonis_diff(repo, scope):
    (repo / scope).mkdir(parents=True, exist_ok=True)
    assert _checks(repo, "--target-scope", scope)[6]["status"] == "PASS"


@pytest.mark.parametrize("scope", ["main..HEAD", "main...feat/x", "origin/main", "refs/pull/12/head", "pr/12", "#12",
                                   "diff: src/order/service.go"])
def test_b4_diff_atau_pr_divonis_diff(repo, scope):
    c = _checks(repo, "--target-scope", scope)[6]
    assert c["status"] == "FAIL" and "diff branch/PR" in c["summary"]


def test_b4_path_di_luar_repo_bukan_diff(repo, tmp_path):
    (tmp_path / "a1" / "internal").mkdir(parents=True)
    for scope in ("../a1/internal", str(tmp_path / "a1" / "internal")):
        c = _checks(repo, "--target-scope", scope)[6]
        assert c["status"] == "FAIL" and "di luar root" in c["summary"], scope


def test_b3_target_scope_wajib(repo):
    c = _checks(repo)[6]
    assert c["status"] == "FAIL" and "REQUIRED" in c["summary"]


@pytest.mark.parametrize("dims, status", [("security,foo", "FAIL"), ("all", "PASS"), ("security, data", "PASS")])
def test_b3_dimensi_divalidasi(repo, dims, status):
    c = _checks(repo, "--target-scope", "src/order", "--dimensions", dims)[6]
    assert c["status"] == status, c
