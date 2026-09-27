"""08c C12 dan C5 — label keluaran validator TASK/REPORT, batas SC aktif 1–7."""
import pytest

from conftest import FE_SKILLS, git, run_script, write_files

TD = "frontenddev/docs/2609240900-label"


@pytest.fixture
def repo(make_repo):
    root = make_repo({"src/a.ts": "a\nb\n"})
    git(root, "checkout", "-q", "-b", "main")
    return root


def task_md(sc_lines, chain=None, desc="Label salah di `src/a.ts:2`."):
    rows = chain or ["- [ ] BRIEF    — frontend:plan          → brief-*.md"]
    return ("---\nstatus: ACTIVE\nlane: HOTFIX_MINOR\nsections: []\ncreated: 2026-09-24\n---\n\n# Label\n\n"
            "## Description\n\n%s\n\n## Success Criteria\n\n%s\n\n## Out of Scope\n\n- Lainnya — di luar lingkup\n\n"
            "## Chain\n\n%s\n" % (desc, "\n".join(sc_lines), "\n".join(rows)))


# --- C12 --------------------------------------------------------------------------------------

@pytest.mark.parametrize("script,label", [("report/scripts/validate_report.py", "REPORT VALIDATION: REPORT.md"),
                                          ("task/scripts/validate_task.py", "TASK VALIDATION: TASK.md")])
def test_c12_label_baris_pertama(repo, script, label):
    write_files(repo, {f"{TD}/TASK.md": "---\nstatus: ACTIVE\n---\n\n# Label\n",
                       f"{TD}/REPORT.md": "# Label — Report\n\n## Ringkasan\n\nSelesai.\n\n## Perubahan\n\n- x (src)\n"})
    first = run_script(FE_SKILLS / script, "--root", str(repo), "--taskdir", TD).stdout.splitlines()[0]
    assert first.startswith(label)


# --- C5 ---------------------------------------------------------------------------------------

def sc(active, dropped):
    lines, n = [], 0
    for _ in range(dropped):
        n += 1
        lines.append(f"- [ ] **SC-{n}**: ~~label {n} — verifikasi: test `A.test.ts` hijau~~ — gugur: amandemen")
    for _ in range(active):
        n += 1
        lines.append(f"- [ ] **SC-{n}**: label {n} benar — verifikasi: test `A.test.ts` hijau")
    return lines


def validate(repo, active, dropped, amend=True):
    chain = ["- [x] BRIEF    — frontend:plan          → brief-*.md @ READY abc1234"] if amend else None
    write_files(repo, {f"{TD}/TASK.md": task_md(sc(active, dropped), chain=chain)})
    args = ["--taskdir", TD, "--root", str(repo)] + (["--amend"] if amend else [])
    return run_script(FE_SKILLS / "task/scripts/validate_task.py", *args)


@pytest.mark.parametrize("active,dropped", [(7, 0), (6, 2), (5, 3), (1, 7)])
def test_c5_amandemen_berulang_lolos(repo, active, dropped):
    proc = validate(repo, active, dropped)
    assert proc.returncode == 0, proc.stdout


@pytest.mark.parametrize("active,dropped", [(8, 0), (0, 3)])
def test_c5_sc_aktif_di_luar_1_sampai_7_gagal(repo, active, dropped):
    proc = validate(repo, active, dropped)
    assert proc.returncode == 1
    assert f"{active} SC aktif, sah 1–7" in proc.stdout


def test_c5_sc_gugur_di_akar_baru_ditolak(repo):
    proc = validate(repo, 3, 1, amend=False)
    assert proc.returncode == 1
    assert "hanya sah pada amandemen akar" in proc.stdout
