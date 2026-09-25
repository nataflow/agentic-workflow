"""business-analysis, system-analysis, dan plan membaca `chain:` TASK.md yang sama dengan hasil sama (L5.4)."""
import json

import pytest

from conftest import be_profile, be_run, commit, write_files

TD = "backenddev/docs/2601011200-refund"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TD}/.keep": "", "src/a.go": "package a\n"})
    be_profile(root, "go")
    commit(root, "init")
    return root


def payload(repo, script, *args):
    proc = be_run(repo, script, "--root", str(repo), "--taskdir", TD, "--json", *args)
    return json.loads(proc.stdout)


@pytest.mark.parametrize("raw", ["PRD_BRIEF", "prd_brief", '"PRD_BRIEF"', "PRD_BRIEF  # dari analyst"])
def test_tiga_skrip_membaca_chain_sama(repo, raw):
    write_files(repo, {f"{TD}/TASK.md": f"---\nstatus: ACTIVE\nchain: {raw}\nrisk: MAJOR\n---\n# T\n"})
    ba = payload(repo, "business-analysis/scripts/check_preconditions.py")["chain"]
    sa = payload(repo, "system-analysis/scripts/check_preconditions.py", "--risk-level", "MAJOR")["chain"]
    pl = payload(repo, "plan/scripts/check_preconditions.py", "--entry-mode", "PRD")["chain"]
    assert ba == sa == pl == "PRD_BRIEF"


def test_tanda_hubung_galat_sama_di_tiga_skrip(repo):
    write_files(repo, {f"{TD}/TASK.md": "---\nstatus: ACTIVE\nchain: PRD-BRIEF\nrisk: MAJOR\n---\n# T\n"})
    runs = [("business-analysis/scripts/check_preconditions.py", 7, ()),
            ("system-analysis/scripts/check_preconditions.py", 1, ("--risk-level", "MAJOR")),
            ("plan/scripts/check_preconditions.py", 8, ("--entry-mode", "PRD", "--file-scope", "src"))]
    for script, cid, args in runs:
        c = {c["id"]: c for c in payload(repo, script, *args)["checks"]}[cid]
        assert c["status"] == "FAIL" and "chain 'PRD-BRIEF' tidak sah" in c["summary"], script
