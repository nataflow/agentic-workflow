"""Prasyarat `task` backenddev: taskdir (L5.2), chain (L5.4), dirty -z (L5.5)."""
import pytest

from conftest import be_checks, be_profile, commit, write_files

TD = "backenddev/docs/2601011200-refund"
TK = "task/scripts/check_preconditions.py"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TD}/.keep": "", "src/a.go": "package a\n"})
    be_profile(root, "go")
    commit(root, "init")
    return root


def tk(repo, *args, td=TD):
    return be_checks(repo, TK, "--root", str(repo), "--taskdir", td, *args)


def test_berkas_unicode_di_taskdir_tidak_kotor(repo):
    write_files(repo, {f"{TD}/café.md": "x\n", f"{TD}/catatan rapat.md": "x\n"})
    assert tk(repo, "--lane", "DIRECT_BRIEF", "--chain", "BRIEF")[5]["status"] == "PASS"


def test_kotor_di_luar_taskdir_tetap_dilaporkan(repo):
    write_files(repo, {"src/b.go": "package a\n"})
    c = tk(repo, "--lane", "DIRECT_BRIEF", "--chain", "BRIEF")[5]
    assert c["status"] == "FAIL" and "src/b.go" in c["summary"]


def test_chain_huruf_kecil_dan_asing(repo):
    assert tk(repo, "--lane", "DIRECT_BRIEF", "--chain", "brief")[6]["status"] == "PASS"
    c = tk(repo, "--lane", "DIRECT_BRIEF", "--chain", "PRD_CONVERSION")[6]
    assert c["status"] == "FAIL" and "PRD_CONVERSION" in c["summary"]


@pytest.mark.parametrize("td", ["src", ".", "backenddev/docs/2601011200-belum-ada"])
def test_taskdir_non_kanonik_ditolak(repo, td):
    assert tk(repo, "--lane", "DIRECT_BRIEF", "--chain", "BRIEF", td=td)[1]["status"] == "FAIL"
