"""L4.6 — `REPORT.md` tertunda (tertulis tetapi tidak lolos `validate_report.py`, mis. penulisan terputus) punya
fase `LAPORAN TERTUNDA` dan jalur pemulihan di architect. Dokumen taskdir tidak di-commit (Langkah 24), jadi
"terbit" berarti lolos validator, bukan ter-commit."""
from conftest import FE_MINOR_TD as TD, fe_run, write_files

REPORT = f"{TD}/REPORT.md"


def cut_off(repo):
    """Penulisan `REPORT.md` terputus: hanya judul dan Ringkasan kosong."""
    write_files(repo, {REPORT: "# Order button — perbaikan label — Report\n\n## Ringkasan\n"})


def architect(repo):
    return fe_run(repo, "architect/scripts/check_preconditions.py", "--taskdir", TD).out


def test_report_tidak_lolos_validator_fase_laporan_tertunda(fe_minor_chain):
    cut_off(fe_minor_chain)
    out = architect(fe_minor_chain)
    assert "fase=LAPORAN TERTUNDA" in out
    assert "[8] Working tree bersih              : PASS" in out


def test_kotoran_lain_tetap_fail_di_laporan_tertunda(fe_minor_chain):
    cut_off(fe_minor_chain)
    (fe_minor_chain / "src" / "App.tsx").write_text("export const App = () => 1;\n")
    assert "[8] Working tree bersih              : FAIL" in architect(fe_minor_chain)


def test_taskdir_state_laporan_tertunda(fe_minor_chain):
    cut_off(fe_minor_chain)
    out = fe_run(fe_minor_chain, "lead/scripts/taskdir_state.py", "--all").out
    assert "LAPORAN TERTUNDA → frontend:architect (Phase 5 butir 4)" in out


def test_report_check5_membedakan_tertunda(fe_minor_chain):
    cut_off(fe_minor_chain)
    out = fe_run(fe_minor_chain, "report/scripts/check_preconditions.py", "--taskdir", TD).out
    assert "tertunda" in out and "Phase 5 butir 4" in out


def test_laporan_lolos_validator_tuntas(fe_minor_chain):
    repo = fe_minor_chain
    assert "fase=TUNTAS" in architect(repo)
    assert "TUNTAS" in fe_run(repo, "lead/scripts/taskdir_state.py", "--all").out
    out = fe_run(repo, "report/scripts/check_preconditions.py", "--taskdir", TD).out
    assert "sudah terbit" in out
