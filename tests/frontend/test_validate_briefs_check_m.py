"""Check M `validate_briefs.py` — re-entry kontrak mencakup eskalasi dari HOTFIX_MINOR (L4.4)."""
import pytest

from conftest import FE_TD, commit, fe_run, write_files

TASK_MINOR = """---
status: ACTIVE
lane: HOTFIX_MINOR
sections: []
created: 2026-09-24
---

# Orders — tombol lacak

## Success Criteria

- [ ] **SC-1**: tombol *Lacak* tampil — verifikasi: test `OrderDetail.test.tsx` hijau

## Chain

"""


def mk(repo, nn, status, remedies=""):
    write_files(repo, {f"{FE_TD}/brief-{nn}-unit.md": f'---\nstatus: {status}\nremedies: "{remedies}"\n---\n'})


def check_m(repo):
    out = fe_run(repo, "plan/scripts/validate_briefs.py", "--taskdir", FE_TD, "--contract").out
    return next(l for l in out.splitlines() if l.startswith("[M]"))


def subject(repo, text):
    p = repo / FE_TD / "TASK.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    commit(repo, f"docs(orders-lacak): {text}", f"{FE_TD}/TASK.md")


@pytest.fixture
def minor(make_repo):
    repo = make_repo({f"{FE_TD}/TASK.md": TASK_MINOR})
    commit(repo, "docs(orders-lacak): kunci TASK sebagai akar rantai")
    mk(repo, "01", "BLOCKED"); mk(repo, "02", "BLOCKED", "01"); mk(repo, "03", "BLOCKED", "01")
    commit(repo, "docs(orders-lacak): unit 03 BLOCKED - galat kompilasi baru")
    return repo


def test_minor_remedi_ketiga_sah_sesudah_escalate(minor):
    subject(minor, "reopen BRIEF — remedi ketiga atas unit 01")
    subject(minor, "eskalasi lane HOTFIX_MINOR → FAST_FORWARD")
    mk(minor, "04", "READY", "01")
    line = check_m(minor)
    assert ": PASS" in line and "3 remedi atas 1 unit asal" in line


def test_minor_remedi_ketiga_tanpa_escalate_fail(minor):
    subject(minor, "reopen BRIEF — remedi ketiga atas unit 01")
    mk(minor, "04", "READY", "01")
    assert ": FAIL" in check_m(minor)


def test_escalate_non_minor_tidak_dihitung(minor):
    subject(minor, "eskalasi lane FAST_FORWARD → FULL_PIPELINE")
    mk(minor, "04", "READY", "01")
    assert ": FAIL" in check_m(minor)


def test_remedi_keempat_sesudah_satu_escalate_fail(minor):
    subject(minor, "eskalasi lane HOTFIX_MINOR → FAST_FORWARD")
    mk(minor, "04", "BLOCKED", "01")
    mk(minor, "05", "READY", "01")
    assert ": FAIL" in check_m(minor)
