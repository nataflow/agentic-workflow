"""Langkah 39 — alur quickdev berantai: plan → execute → review tanpa jeda.

Commit rencana sesudah approve (39 C1) diganti rencana di luar git dan commit hasil di akhir review (Q1, Q2):
`test_lapangan_q1_q2_q4.py`."""
import re

import pytest

from conftest import PLUGINS, commit, run_script

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
SK = PLUGINS / "quickdev" / "skills"
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


@pytest.mark.regression("39 A3")
def test_remediasi_tetap_diketik_user():
    fase5 = section(skill("review"), "### Fase 5", "## Guardrails")
    assert "/quickdev:execute <plan_path>" in fase5
    assert not re.search(r"memanggil `quickdev:execute`(?! sendiri)", fase5)
