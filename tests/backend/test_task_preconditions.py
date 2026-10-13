"""Prasyarat `task` backend: taskdir (L5.2), chain (L5.4), dirty -z (L5.5)."""
import pytest

from conftest import be_checks, be_profile, commit, git, write_files

TD = "backenddev/docs/2601011200-refund"
TK = "task/scripts/check_preconditions.py"


@pytest.fixture
def repo(make_repo):
    root = make_repo({"src/a.go": "package a\n"})
    git(root, "checkout", "-q", "-b", "main")
    be_profile(root, "go")
    commit(root, "init")
    # Penanda ignore ditulis prasyarat penuh `tech-lead` (Langkah 24); taskdir hanya di disk.
    write_files(root, {"backenddev/docs/.gitignore": "*\n", f"{TD}/.keep": ""})
    git(root, "checkout", "-q", "-b", "feat/refund")    # 11 H20: akar ditulis di branch kerja taskdir
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


@pytest.mark.regression("24 G2")
def test_dokumen_taskdir_wajib_di_luar_git(repo):
    (repo / "backenddev/docs/.gitignore").unlink()
    c = tk(repo, "--lane", "DIRECT_BRIEF", "--chain", "BRIEF")[5]
    assert c["status"] == "FAIL" and "belum diabaikan git" in c["summary"], c
    git(repo, "add", f"{TD}/.keep")
    git(repo, "commit", "-qm", "docs: era git")
    write_files(repo, {"backenddev/docs/.gitignore": "*\n"})
    c = tk(repo, "--lane", "DIRECT_BRIEF", "--chain", "BRIEF")[5]
    assert c["status"] == "FAIL" and "masih ter-track" in c["summary"] and "tech-lead" in c["action"], c
