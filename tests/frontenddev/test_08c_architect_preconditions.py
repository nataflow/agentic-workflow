"""08c C6 — Check 13 memfilter commit unit per slug; Check 9 mendeteksi rebase/am lewat --git-path."""
import subprocess

from conftest import FE_SKILLS, commit, git, run_script, write_files

SCRIPT = FE_SKILLS / "architect" / "scripts" / "check_preconditions.py"
TD = "frontenddev/docs/2609240900-label"


def line(proc, cid):
    return next(l for l in proc.stdout.splitlines() if l.startswith(f"[{cid}]"))


def setup(make_repo):
    root = make_repo({"src/a.ts": "a\n", "src/b.ts": "b1\nb2\nb3\n"})
    git(root, "checkout", "-q", "-b", "main")
    sha = commit(root, "chore: awal")
    write_files(root, {f"{TD}/brief-01-a.md":
                       f"---\nstatus: READY\nbased_on: {sha} (2026-09-24)\nfiles_touched: [src/a.ts]\n---\n\n# Brief\n"})
    commit(root, "docs(label): draft breakdown")
    return root


def check(root, *args):
    return run_script(SCRIPT, "--root", str(root), "--taskdir", TD, *args)


def test_c6_implement_unit_taskdir_lain_tetap_asing(make_repo):
    root = setup(make_repo)
    write_files(root, {"src/a.ts": "a\nx\n"})
    commit(root, "feat(taskdir-lain): implement unit 03 - lain")
    assert "WARN" in line(check(root, "--brief", "01"), 13)


def test_c6_implement_unit_taskdir_sendiri_dikecualikan(make_repo):
    root = setup(make_repo)
    write_files(root, {"src/a.ts": "a\nx\n"})
    commit(root, "feat(label): implement unit 02 - label")
    assert "PASS" in line(check(root, "--brief", "01"), 13)


def test_c6_git_am_berhenti_di_worktree_terdeteksi(make_repo, tmp_path):
    root = setup(make_repo)
    git(root, "checkout", "-q", "-b", "donor")
    write_files(root, {"src/b.ts": "b1\nB2\nb3\n"})
    commit(root, "ubah b2")
    patch = git(root, "format-patch", "-1", "-o", str(tmp_path)).strip()
    git(root, "checkout", "-q", "main")
    write_files(root, {"src/b.ts": "b1\nbX\nb3\n"})
    commit(root, "ubah b2 di main")
    wt = tmp_path / "wt"
    git(root, "worktree", "add", "-q", str(wt), "-b", "wt")
    subprocess.run(["git", "-C", str(wt), "-c", "user.name=t", "-c", "user.email=t@t", "am", patch],
                   capture_output=True)
    assert (root / ".git" / "worktrees" / "wt" / "rebase-apply").exists()
    proc = check(wt)
    assert "FAIL" in line(proc, 9) and "rebase" in line(proc, 9)
