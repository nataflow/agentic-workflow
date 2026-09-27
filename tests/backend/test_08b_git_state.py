"""B6/B3 — operasi git menggantung dan base branch di prasyarat architect (check 4) dan report (check 7, 8)."""
import os
import subprocess

import pytest

from conftest import GIT_ENV, TD, be_checks, brief, commit, git, write_files

ARCH = "architect/scripts/check_preconditions.py"
REPORT = "report/scripts/check_preconditions.py"


@pytest.fixture
def ready(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs")
    return chain_repo


def _side_branch(repo, name="other", fname="note.txt", text="x\n"):
    git(repo, "checkout", "-q", "-b", name)
    write_files(repo, {fname: text})
    commit(repo, name)
    git(repo, "checkout", "-q", "fix/order-fix")


def _raw_git(repo, *args, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV, **(env or {})})


def test_b6_cherry_pick_kosong_terdeteksi(ready):
    _side_branch(ready)
    write_files(ready, {"note.txt": "x\n"})
    commit(ready, "same")
    _raw_git(ready, "cherry-pick", "other")
    assert git(ready, "status", "--porcelain") == ""
    c = be_checks(ready, ARCH, "--taskdir", TD)[4]
    assert c["status"] == "FAIL" and "cherry-pick" in c["summary"]


def test_b6_merge_no_commit_terdeteksi(ready):
    _side_branch(ready, fname="o.txt")
    git(ready, "merge", "--no-commit", "-s", "ours", "other")
    c = be_checks(ready, ARCH, "--taskdir", TD)[4]
    assert c["status"] == "FAIL" and "merge" in c["summary"]


def test_b6_report_mendeteksi_rebase_edit(ready):
    brief(ready, "01", "lock", "DONE")
    write_files(ready, {f"{TD}/REVIEW.md": "# Review\n", "src/order.go": "package order\n// x\n"})
    commit(ready, "c1")
    write_files(ready, {"a.txt": "a\n"})
    commit(ready, "c2")
    _raw_git(ready, "rebase", "-q", "-i", "HEAD~1", env={"GIT_SEQUENCE_EDITOR": "sed -i.bak 1s/^pick/edit/"})
    c = be_checks(ready, REPORT, "--taskdir", TD)[7]
    assert c["status"] == "FAIL" and "rebase" in c["summary"]


def test_b6_rename_ke_laci_gagal_di_architect(ready):
    (ready / TD / ".explore").mkdir(parents=True, exist_ok=True)
    git(ready, "mv", "src/order.go", f"{TD}/.explore/order.go")
    c = be_checks(ready, ARCH, "--taskdir", TD)[4]
    assert c["status"] == "FAIL" and "src/order.go" in c["summary"]


def test_b6_laci_taskdir_diabaikan(ready):
    write_files(ready, {f"{TD}/.explore/slug-01.md": "x\n", "backenddev/docs/.explore/gate.md": "x\n"})
    assert be_checks(ready, ARCH, "--taskdir", TD)[4]["status"] == "PASS"


def test_b3_architect_base_tidak_resolve(ready):
    c = be_checks(ready, ARCH, "--taskdir", TD, "--base-branch", "does-not-exist")[4]
    assert c["status"] == "FAIL" and "tidak resolve" in c["summary"]


def test_b3_report_menuntut_diff_nyata(chain_repo):
    brief(chain_repo, "01", "lock", "DONE")
    write_files(chain_repo, {f"{TD}/REVIEW.md": "# Review\n"})
    git(chain_repo, "checkout", "-q", "main")
    commit(chain_repo, "langsung di main")
    git(chain_repo, "checkout", "-q", "-B", "fix/order-fix")
    c = be_checks(chain_repo, REPORT, "--taskdir", TD)[8]
    assert c["status"] == "FAIL" and "merge-base = HEAD" in c["summary"]


def test_b3_report_base_tidak_resolve_dan_detached(chain_repo):
    brief(chain_repo, "01", "lock", "DONE")
    write_files(chain_repo, {f"{TD}/REVIEW.md": "# Review\n"})
    commit(chain_repo, "done")
    assert "tidak resolve" in be_checks(chain_repo, REPORT, "--taskdir", TD, "--base-branch", "nope")[8]["summary"]
    git(chain_repo, "checkout", "-q", "--detach")
    assert "Detached HEAD" in be_checks(chain_repo, REPORT, "--taskdir", TD)[8]["summary"]


def test_b3_report_lolos_dengan_diff(chain_repo):
    brief(chain_repo, "01", "lock", "DONE")
    write_files(chain_repo, {f"{TD}/REVIEW.md": "# Review\n"})
    commit(chain_repo, "done")
    c = be_checks(chain_repo, REPORT, "--taskdir", TD)[8]
    assert c["status"] == "PASS", c
