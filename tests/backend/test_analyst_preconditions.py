"""Prasyarat `analyst` backend: taskdir (L5.2), chain tanpa crash (L5.4), dirty -z (L5.5)."""
import json

import pytest

from conftest import be_profile, be_run, commit, write_files

TD = "backenddev/docs/2601011200-refund"
AN = "analyst/scripts/check_preconditions.py"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TD}/TASK.md": "---\nstatus: ACTIVE\nchain: BRIEF\n---\n# T\n",
                      "backenddev/docs/2601011200-berkas": "x\n", "src/a.go": "package a\n"})
    be_profile(root, "go")
    commit(root, "init")
    return root


def run(repo, *args, td=TD):
    proc = be_run(repo, AN, "--root", str(repo), "--taskdir", td, "--json", *args)
    assert "Traceback" not in proc.stderr, proc.stderr
    return proc, {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


def task(repo, chain):
    write_files(repo, {f"{TD}/TASK.md": f"---\nstatus: ACTIVE\nchain: {chain}\nlane: PRD_CONVERSION\nrisk: MAJOR\n---\n# T\n"})


def test_chain_asing_di_task_json_tetap_valid(repo):
    task(repo, "PRD_CONVERSION")
    proc, checks = run(repo, "--risk", "MAJOR")
    assert proc.returncode == 1
    assert checks[5]["status"] == "FAIL" and "PRD_CONVERSION" in checks[5]["summary"]


def test_chain_huruf_kecil_mendeteksi_brd_nyasar(repo):
    task(repo, "prd_brief")
    write_files(repo, {f"{TD}/BRD.md": "# BRD\n"})
    _, checks = run(repo, "--risk", "MAJOR")
    assert checks[5]["status"] == "FAIL" and "BRD.md" in checks[5]["summary"]


def test_parameter_chain_asing(repo):
    _, checks = run(repo, "--risk", "MAJOR", "--chain", "PRD_CONVERSION")
    assert checks[4]["status"] == "FAIL" and "PRD_CONVERSION" in checks[4]["summary"]
    assert checks[5]["status"] == "FAIL"


def test_parameter_chain_huruf_kecil(repo):
    _, checks = run(repo, "--risk", "MINOR", "--chain", "brief")
    assert checks[4]["status"] == "PASS"


def test_taskdir_berupa_berkas(repo):
    _, checks = run(repo, "--risk", "MAJOR", td="backenddev/docs/2601011200-berkas")
    assert checks[1]["status"] == "FAIL" and "bukan direktori" in checks[1]["summary"]


def test_taskdir_absolut_lewat_symlink(repo, tmp_path):
    link = tmp_path / "repo.link"
    link.symlink_to(repo)
    _, checks = run(repo, "--risk", "MINOR", "--chain", "BRIEF", td=f"{link}/{TD}")
    assert checks[1]["status"] == "PASS"


def test_berkas_unicode_di_taskdir_tidak_kotor(repo):
    write_files(repo, {f"{TD}/café.md": "x\n", f"{TD}/catatan rapat.md": "x\n"})
    _, checks = run(repo, "--risk", "MINOR", "--chain", "BRIEF")
    assert checks[6]["status"] == "PASS", checks[6]


def test_explore_di_luar_docs_tetap_kotor(repo):
    write_files(repo, {"internal/.explore/q.go": "x\n"})
    _, checks = run(repo, "--risk", "MINOR", "--chain", "BRIEF")
    assert checks[6]["status"] == "FAIL" and "internal/.explore/q.go" in checks[6]["summary"]
