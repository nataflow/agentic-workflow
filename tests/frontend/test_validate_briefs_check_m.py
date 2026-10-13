"""Check M `validate_briefs.py` — re-entry kontrak mencakup eskalasi dari HOTFIX_MINOR (L4.4). Urutan BLOCKED dan
re-entry dibaca dari `## Riwayat Rantai` (Langkah 24), bukan dari subjek commit."""
import re

import pytest

from conftest import FE_TD, fe_lib, fe_run, write_files

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
    """Kejadian Riwayat persis tulisan `chain.py` (`reopen BRIEF …` atau `eskalasi lane A → B`)."""
    lib = fe_lib()
    p = repo / FE_TD / "TASK.md"
    task = p.read_text(encoding="utf-8")
    n = len(lib.read_history(task)[0]) + 1
    m = re.match(r"eskalasi lane (\S+) → (\S+)", text)
    if m:
        line = lib.history_line(n, "eskalasi", [], [("lane", f"{m.group(1)} → {m.group(2)}"),
                                                     ("sections", "- → architecture"), ("akar", "0" * 12)],
                                ("alasan", text))
    else:
        names = sorted(x.name for x in (repo / FE_TD).glob("brief-*.md"))
        line = lib.history_line(n, "reopen", ["BRIEF"], [("target", "BRIEF"),
                                                         ("berkas", lib.berkas_value(repo, FE_TD, names))],
                                ("alasan", text))
    p.write_text(lib.append_history(task, line), encoding="utf-8")


@pytest.fixture
def minor(make_repo):
    repo = make_repo({f"{FE_TD}/TASK.md": TASK_MINOR + "## Riwayat Rantai\n\n- 1 · akar · base 0000000 · lane "
                      "HOTFIX_MINOR · sections - · akar 000000000000 · waktu 2026-10-13T00:00:00Z\n"})
    mk(repo, "01", "BLOCKED"); mk(repo, "02", "BLOCKED", "01"); mk(repo, "03", "BLOCKED", "01")
    subject(repo, "reopen BRIEF — unit 03 BLOCKED, galat kompilasi baru")     # Riwayat mencatat BLOCKED
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
