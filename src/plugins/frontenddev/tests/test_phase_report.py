"""L4.6 — `REPORT.md` yang gagal di-commit punya fase `LAPORAN TERTUNDA` dan jalur kunci di architect."""
import subprocess

from conftest import FE_MINOR_TD as TD, fe_run, git

REPORT = f"{TD}/REPORT.md"


def fail_commit(repo):
    """Hook pre-commit gagal → commit report tertahan, berkas tertinggal di index/working tree."""
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text('#!/bin/sh\necho "hook: lint gagal" >&2; exit 1\n')
    hook.chmod(0o755)
    git(repo, "add", REPORT)
    assert subprocess.run(["git", "-C", str(repo), "commit", "-qm", "docs(order-checkout): laporkan hasil rantai"],
                          capture_output=True).returncode != 0


def architect(repo):
    return fe_run(repo, "architect/scripts/check_preconditions.py", "--taskdir", TD).out


def test_report_belum_commit_fase_laporan_tertunda(fe_minor_chain):
    fail_commit(fe_minor_chain)
    out = architect(fe_minor_chain)
    assert "fase=LAPORAN TERTUNDA" in out
    assert "[8] Working tree bersih              : PASS" in out


def test_kotoran_lain_tetap_fail_di_laporan_tertunda(fe_minor_chain):
    fail_commit(fe_minor_chain)
    (fe_minor_chain / "src" / "App.tsx").write_text("export const App = () => 1;\n")
    assert "[8] Working tree bersih              : FAIL" in architect(fe_minor_chain)


def test_taskdir_state_laporan_tertunda(fe_minor_chain):
    fail_commit(fe_minor_chain)
    out = fe_run(fe_minor_chain, "lead/scripts/taskdir_state.py", "--all").out
    assert "LAPORAN TERTUNDA → frontenddev:architect (Phase 5 butir 4)" in out


def test_report_check5_membedakan_tertunda(fe_minor_chain):
    fail_commit(fe_minor_chain)
    out = fe_run(fe_minor_chain, "report/scripts/check_preconditions.py", "--taskdir", TD).out
    assert "tertunda" in out and "Phase 5 butir 4" in out


def test_sesudah_commit_tuntas(fe_minor_chain):
    repo = fe_minor_chain
    fail_commit(repo)
    (repo / ".git" / "hooks" / "pre-commit").unlink()
    git(repo, "commit", "-qm", "docs(order-checkout): laporkan hasil rantai order-checkout")
    assert "fase=TUNTAS" in architect(repo)
    assert "TUNTAS" in fe_run(repo, "lead/scripts/taskdir_state.py", "--all").out
    out = fe_run(repo, "report/scripts/check_preconditions.py", "--taskdir", TD).out
    assert "sudah terbit" in out
