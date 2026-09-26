"""08c C11 + C14 — skill review: objek taskdir = berkas rantai; target path dibatasi ke repo."""
import json
import os

import pytest

from conftest import FE_SKILLS, commit, git, run_script, write_files

SCRIPT = FE_SKILLS / "review" / "scripts" / "check_preconditions.py"
TD = "frontenddev/docs/2609240900-label"


def check1(proc):
    return next(l for l in proc.stdout.splitlines() if l.startswith("[1]"))


@pytest.fixture
def root(make_repo, tmp_path):
    root = make_repo({"src/a.ts": "a\n"})
    git(root, "checkout", "-q", "-b", "main")
    commit(root, "chore: awal")
    (tmp_path / "rahasia").mkdir()
    return root


@pytest.mark.parametrize("path", ["../rahasia", "src/tautan", "{tmp}/rahasia"])
def test_c14_path_di_luar_repo_ditolak(root, path):
    os.symlink("../../rahasia", root / "src" / "tautan")
    proc = run_script(SCRIPT, "--root", str(root), "--target", "path", "--path", path.format(tmp=root.parent))
    assert "FAIL" in check1(proc) and "di luar repo" in check1(proc)


@pytest.mark.parametrize("path", ["src", "./src/", "{root}/src"])
def test_c14_path_di_dalam_repo_diterima(root, path):
    proc = run_script(SCRIPT, "--root", str(root), "--target", "path", "--path", path.format(root=root))
    assert "PASS (path `src`)" in check1(proc)


def test_c11_target_taskdir_hanya_berkas_rantai(root):
    write_files(root, {f"{TD}/TASK.md": "---\nstatus: ACTIVE\n---\n# Label\n"})
    commit(root, "docs(label): kunci TASK sebagai akar rantai")
    write_files(root, {"src/a.ts": "a\nb\n"})
    commit(root, "feat(label): implement unit 01 - label")
    write_files(root, {"src/lain.ts": "c\n"})
    commit(root, "feat: kerja user di luar rantai")
    write_files(root, {f"{TD}/REPORT.md": "# r\n"})
    commit(root, "docs(label): report")
    write_files(root, {"src/sesudah.ts": "d\n"})
    commit(root, "feat(taskdir-lain): implement unit 01 - lain")
    proc = run_script(SCRIPT, "--root", str(root), "--target", "taskdir", "--taskdir", TD, "--json")
    assert json.loads(proc.stdout)["chain_files"] == ["src/a.ts"]
    text = run_script(SCRIPT, "--root", str(root), "--target", "taskdir", "--taskdir", TD).stdout
    assert "1 berkas rantai" in text and f"berkas=chain.py files --taskdir {TD}" in text
