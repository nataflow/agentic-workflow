"""Prasyarat `business-analysis`: taskdir kanonik (L5.2) dan chain dari frontmatter (L5.4)."""
import pytest

from conftest import be_checks, be_profile, commit, write_files

TD = "backenddev/docs/2601011200-refund"
BA = "business-analysis/scripts/check_preconditions.py"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TD}/TASK.md": "---\nchain: BRD_PRD_BRIEF\n---\n# T\n", "src/a.go": "package a\n"})
    be_profile(root, "go")
    commit(root, "init")
    return root


def ba(repo, *args, td=TD):
    return be_checks(repo, BA, "--root", str(repo), "--taskdir", td, *args)


@pytest.mark.parametrize("td", ["src", ".", "/tmp", "backenddev/docs/2601011200-belum-ada"])
def test_taskdir_non_kanonik_ditolak(repo, td):
    assert ba(repo, "--chain", "BRD_PRD_BRIEF", td=td)[1]["status"] == "FAIL"


@pytest.mark.parametrize("raw", ["brd_prd_brief", '"BRD_PRD_BRIEF"', "BRD_PRD_BRIEF  # dari analyst"])
def test_chain_frontmatter_dinormalkan(repo, raw):
    write_files(repo, {f"{TD}/TASK.md": f"---\nchain: {raw}\n---\n# T\n"})
    assert ba(repo)[7]["status"] == "PASS"


def test_chain_ber_tanda_hubung_galat(repo):
    write_files(repo, {f"{TD}/TASK.md": "---\nchain: BRD-PRD-BRIEF\n---\n# T\n"})
    c = ba(repo)[7]
    assert c["status"] == "FAIL" and "chain 'BRD-PRD-BRIEF' tidak sah" in c["summary"]
