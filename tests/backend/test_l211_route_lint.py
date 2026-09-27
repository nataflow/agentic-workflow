"""L2.11 — perbaikan `P1` review berjalan di taskdir yang sama, dengan `reentry_reason`."""
from conftest import BE_SKILLS


def _read(rel):
    return (BE_SKILLS / rel).read_text(encoding="utf-8")


def test_no_new_taskdir_for_p1():
    assert "taskdir baru" not in _read("architect/dispatcher/reviewer.md")

    p1_item = next(l for l in _read("tech-lead/SKILL.md").splitlines()
                   if l.startswith("4. Perlakukan severity `P1`"))
    assert "taskdir yang sama" in p1_item and "reentry_reason" in p1_item

    new_row = next(l for l in _read("tech-lead/references/gate-lifecycle.md").splitlines()
                   if "Buat taskdir bertimestamp baru" in l)
    assert "REPORT.md" in new_row


def test_analyst_accepts_review_p1_trigger():
    assert "temuan `P1` `REVIEW.md`" in _read("analyst/SKILL.md")


def test_lifecycle_p1_row_same_taskdir():
    row = next(l for l in _read("architect/references/lifecycle-recovery.md").splitlines()
               if l.startswith("| **`P1`**"))
    assert "taskdir yang sama" in row and "reentry_reason" in row
