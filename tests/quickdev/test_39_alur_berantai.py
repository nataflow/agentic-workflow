"""Langkah 39 — alur quickdev berantai: commit rencana sesudah approve, plan → execute → review tanpa jeda."""
import re

import pytest

from conftest import PLUGINS, commit, git, run_script

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


@pytest.mark.regression("39 C1")
def test_commit_hanya_berkas_rencana(repo, pl):
    (repo / "app.js").write_text("ubah user\n", encoding="utf-8")
    (repo / "lain.txt").write_text("staged user\n", encoding="utf-8")
    git(repo, "add", "lain.txt")
    assert pl("lock", "--answer", "Setujui & eksekusi").returncode == 0
    r = pl("commit")
    assert r.returncode == 0 and r.stdout.startswith("COMMIT PASS: plan/t.md @"), r.stdout
    assert git(repo, "show", "--name-only", "--format=%s", "HEAD").split() == \
        ["docs(plan):", "setujui", "rencana", "t", "plan/t.md"]
    status = git(repo, "status", "--porcelain")
    assert "A  lain.txt" in status and " M app.js" in status   # index dan working tree user utuh
    assert pl("commit").stdout.startswith("COMMIT SKIP: plan/t.md sudah sama dengan HEAD")
    r = pl("start")                                           # tree kotor milik user tetap dinilai start
    assert r.returncode == 1 and r.stdout.rstrip().endswith("dulu: app.js, lain.txt")


@pytest.mark.regression("39 C1")
def test_commit_tolak_draft_dan_sidik_basi(repo, pl):
    assert pl("commit").stdout.startswith("COMMIT FAIL")
    pl("lock", "--answer", "ok")
    p = repo / "plan" / "t.md"
    p.write_text(p.read_text(encoding="utf-8").replace("kuota", "kuota harian"), encoding="utf-8")
    r = pl("commit")
    assert r.returncode == 1 and r.stdout.startswith("COMMIT FAIL")


@pytest.mark.regression("39 C1")
def test_commit_skip_gitignore_dan_blok_eksekusi(repo, pl):
    (repo / ".gitignore").write_text("plan/\n", encoding="utf-8")
    commit(repo, "abaikan plan", ".gitignore")
    pl("lock", "--answer", "ok")
    r = pl("commit")
    assert r.returncode == 0 and "diabaikan .gitignore" in r.stdout
    (repo / ".gitignore").unlink()
    commit(repo, "lepas", ".gitignore")
    assert pl("start").returncode == 0
    r = pl("commit")
    assert r.returncode == 0 and "Execution Status" in r.stdout and r.stdout.startswith("COMMIT SKIP")


@pytest.mark.regression("39 C1")
def test_commit_skip_bukan_git(make_repo):
    root = make_repo(git_init=False)
    (root / "plan").mkdir()
    (root / "plan" / "t.md").write_text(PLAN, encoding="utf-8")
    run_script(PL, "lock", "--answer", "ok", "--plan", "plan/t.md", cwd=root)
    r = run_script(PL, "commit", "--plan", "plan/t.md", cwd=root)
    assert r.returncode == 0 and r.stdout.startswith("COMMIT SKIP: bukan repo git")


@pytest.mark.regression("39 C1")
def test_commit_gagal_hook_exit_3(repo, pl):
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'error: ditolak hook' >&2\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    pl("lock", "--answer", "ok")
    r = pl("commit")
    assert r.returncode == 3 and r.stdout.startswith("COMMIT GAGAL: error: ditolak hook")
    assert pl("verify").returncode == 0


@pytest.mark.regression("39 C1")
def test_plan_fase5_commit_sebelum_sinkron():
    fase5 = section(skill("plan"), "### Fase 5", "## Guardrails")
    assert fase5.index("plan_lock.py commit") < fase5.index("references/nataflow-sync.md")


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
