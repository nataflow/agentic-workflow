"""Langkah 39 — alur quickdev berantai: plan → execute → review tanpa jeda.

Commit rencana sesudah approve (39 C1) diganti rencana di luar git dan commit hasil di akhir review (Q1, Q2):
`test_lapangan_q1_q2_q4.py`."""
import re

import pytest

from conftest import PLUGINS, commit, run_script

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
SK = PLUGINS / "quickdev" / "skills"
PLUGINS_QD = PLUGINS / "quickdev"
PLAN = """# Implementation Plan — t
Status: DRAFT
Author: quickdev:plan

## 1. Overview & Objectives
Tambah validasi kuota.

## 3. Atomic Implementation Steps
- [ ] 1. Ubah `app.js`: tambah `checkQuota()`

## 4. Verification & Testing Strategy
- `npm test`
"""


@pytest.fixture
def repo(make_repo):
    root = make_repo({"app.js": "a\n"})
    commit(root, "init")
    (root / "plan").mkdir()
    (root / "plan" / "t.md").write_text(PLAN, encoding="utf-8")
    return root


@pytest.fixture
def pl(repo):
    return lambda *a: run_script(PL, *a, "--plan", "plan/t.md", cwd=repo)


def skill(name):
    return (SK / name / "SKILL.md").read_text(encoding="utf-8")


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


@pytest.mark.regression("39 A1")
def test_plan_approval_tiga_opsi_dan_rantai_execute():
    fase4 = section(skill("plan"), "### Fase 4", "### Fase 5")
    assert "*Setujui & eksekusi*" in fase4 and "*Setujui saja*" in fase4 and "*Revisi" in fase4
    fase5 = section(skill("plan"), "### Fase 5", "## Guardrails")
    assert "Skill" in fase5 and "`quickdev:execute`" in fase5


@pytest.mark.regression("39 A2")
def test_execute_completed_berantai_ke_review():
    fase4 = section(skill("execute"), "### Fase 4", "## Guardrails")
    assert "`COMPLETED`" in fase4 and "`quickdev:review`" in fase4 and "tanpa bertanya" in fase4


@pytest.mark.regression("Q5")
def test_remediasi_berantai_dari_pilihan_user():
    """39 A3 (remediasi diketik user) dibalik Q5: pilihan perbaiki di review memanggil execute langsung."""
    fase5 = section(skill("review"), "### Fase 5", "## Guardrails")
    assert "*Perbaiki semua temuan — remediasi putaran <n+1>/2 (Recommended)*" in fase5
    assert "*Perbaiki semua temuan minor (Recommended)*" in fase5
    assert re.search(r"langsung panggil tool `Skill` dengan `quickdev:execute`", fase5)
    assert "remediasi adalah keputusan user" not in fase5 and "untuk diketik user" not in fase5
    assert "Dilarang memperbaiki sendiri di sesi review" in fase5


@pytest.mark.regression("Q5")
def test_reviewed_minor_pertanyaan_gabungan_dan_plafon():
    fase5 = section(skill("review"), "### Fase 5", "## Guardrails")
    butir4 = section(fase5, "4. Bila status `REVIEWED`", "5. **Tawaran commit**")
    for opt in ("*Perbaiki semua temuan minor (Recommended)*", "*Commit di branch aktif*", "*Commit di branch baru*",
                "*Jangan dulu*"):
        assert opt in butir4, opt
    assert "`MINOR`" in butir4 and "belum 2" in butir4 and "sudah 2" in fase5
    assert "HANDOFF: execute (remediasi, dipanggil langsung)" in section(skill("review"), "## Output", "## Failure")
    assert (PLUGINS_QD / "MIGRATION_v0.15.x_to_v0.16.0.md").is_file()


@pytest.mark.regression("Q5")
def test_remediasi_temuan_minor_dari_reviewed_diterima_start(repo, pl):
    """Remediasi MINOR dari REVIEWED memakai jalur skrip yang sama dengan CHANGES_REQUIRED: cukup blok COMPLETED."""
    assert pl("lock", "--answer", "setuju").returncode == 0
    assert pl("start").returncode == 0
    plan = repo / "plan" / "t.md"
    plan.write_text(plan.read_text(encoding="utf-8").replace("- [ ] 1.", "- [x] 1."), encoding="utf-8")
    (repo / "app.js").write_text("a\nb\n", encoding="utf-8")
    assert pl("close", "--status", "COMPLETED", "--verification", "npm test PASS").returncode == 0
    r = pl("start", "--findings", "--findings-text", "[MINOR] app.js:2 nama helper tidak konsisten")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "remediasi" in r.stdout and "1/2" in r.stdout
