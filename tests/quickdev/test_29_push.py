"""29 S4 — `plan_lock.py sync-payload --push`: rencana dan profil quickdev langsung ke server MCP palsu."""
import json

import pytest

from conftest import PLUGINS, commit, run_script, write_files
from nataflow_fake import FakeMCP, Nataflow, enable_sync

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
WS = "bbbbbbbb-0000-4000-8000-000000000001"
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
def fake():
    with FakeMCP() as f:
        yield f, Nataflow(f, workspaces=[WS])


@pytest.fixture
def repo(make_repo, fake):
    root = make_repo({"app.js": "a\n", "repo-profile.md": "# profil\n"})
    commit(root, "init")
    write_files(root, {"plan/t.md": PLAN})
    assert run_script(PL, "lock", "--plan", "plan/t.md", "--answer", "setuju", cwd=root).returncode == 0
    enable_sync(root, fake[0].url, extra={"repo": "tim/app"})
    return root


def push(repo, *args):
    r = run_script(PL, "sync-payload", *args, "--push", "--json", cwd=repo)
    assert "Traceback" not in r.stderr, r.stderr
    return r.returncode, json.loads(r.stdout)


@pytest.mark.regression("29 S4")
def test_rencana_task_workdir_dokumen(repo, fake):
    f, nf = fake
    code, out = push(repo, "--plan", "plan/t.md")
    assert code == 0 and out["segment"] == "workdir t · 1 dokumen (1 baru, 0 diperbarui, 0 sama)", out
    assert nf.tasks[0]["status"] == "in_progress" and nf.tasks[0]["metadata"]["source"] == "quickdev"
    assert nf.docs[0]["key"] == "t.md" and nf.docs[0]["type"] == "quickdev.plan"
    assert "Tambah validasi kuota" not in json.dumps(out)
    code, out = push(repo, "--plan", "plan/t.md")
    assert out["segment"].endswith("(0 baru, 0 diperbarui, 1 sama)") and len(nf.tasks) == 1


def test_task_kembar_berlabel_workdir_key(repo, fake):
    f, nf = fake
    ident = {"source": "quickdev", "workdir_key": "quickdev:tim/app:plan/t.md"}
    nf.add_task(ident)
    nf.add_task(ident)
    code, out = push(repo, "--plan", "plan/t.md")
    assert code == 1 and out["segment"].startswith("GAGAL: 2 task ber-workdir_key sama") and f.writes() == []


def test_profil_ke_workspace(repo, fake):
    f, nf = fake
    code, out = push(repo, "--repo-profile", "repo-profile.md")
    assert code == 0 and out["segment"] == "repo · 1 dokumen (1 baru, 0 diperbarui, 0 sama)"
    assert nf.docs[0]["reference_table"] == "workspace" and nf.docs[0]["reference_id"] == WS


def test_tanpa_config_dilewati(make_repo):
    root = make_repo()
    code, out = push(root, "--plan", "plan/tidak-ada.md")
    assert (code, out["segment"]) == (0, "dilewati")


def test_rencana_draft_gagal_tanpa_panggilan(make_repo, fake):
    f, _ = fake
    root = make_repo({"plan/t.md": PLAN})
    enable_sync(root, f.url)
    code, out = push(root, "--plan", "plan/t.md")
    assert code == 1 and "belum pernah dikunci" in out["segment"] and f.requests == []


def test_push_dan_remote_saling_eksklusif(repo):
    r = run_script(PL, "sync-payload", "--plan", "plan/t.md", "--push", "--remote", "-", cwd=repo)
    assert r.returncode == 2 and "not allowed" in r.stderr
