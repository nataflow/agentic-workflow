"""41 D1–D4 — quickdev: task nataflow acuan, rencana DRAFT tercermin sebelum approval, task `done`, dan dokumen
report berisi ringkasan naratif."""
import json

import pytest

from conftest import PLUGINS, commit, git, run_script, write_files
from nataflow_fake import FakeMCP, Nataflow, ToolError, enable_sync

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
WS = "bbbbbbbb-0000-4000-8000-000000000001"
TICKET = {"source": "analyst", "ticket_key": "analyst/tickets/2611200900-kuota"}
PLAN = """# Implementation Plan — t
Status: DRAFT
Author: quickdev:plan

## 1. Overview & Objectives
Tambah validasi kuota.
- AC-1: kuota habis → 422 `quota exceeded`

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
    root = make_repo({"app.js": "a\n"})
    enable_sync(root, fake[0].url, extra={"repo": "tim/app"})
    commit(root, "init")
    write_files(root, {"plan/t.md": PLAN})
    return root


def pl(repo, *args, stdin=""):
    r = run_script(PL, *args, cwd=repo, stdin=stdin)
    assert "Traceback" not in r.stderr, r.stderr
    return r


def push(repo):
    r = pl(repo, "sync-payload", "--plan", "plan/t.md", "--push", "--json")
    return r.returncode, json.loads(r.stdout)


def lock(repo):
    assert pl(repo, "lock", "--plan", "plan/t.md", "--answer", "setuju").returncode == 0


def execute(repo, summary="Validasi kuota ditambahkan di `checkQuota()`; test lolos."):
    """start → kode berubah → checklist → close COMPLETED → summary."""
    assert pl(repo, "start", "--plan", "plan/t.md").returncode == 0
    write_files(repo, {"app.js": "a\nfunction checkQuota() {}\n", "quota.test.js": "test\n"})
    plan = repo / "plan" / "t.md"
    plan.write_text(plan.read_text(encoding="utf-8").replace("- [ ] 1.", "- [x] 1."), encoding="utf-8")
    assert pl(repo, "close", "--plan", "plan/t.md", "--status", "COMPLETED", "--verification", "test=PASSED")\
        .returncode == 0
    if summary:
        assert pl(repo, "summary", "--plan", "plan/t.md", "--summary", "-", stdin=summary).returncode == 0


def report(nf):
    return next(d for d in nf.docs if d["type"] == "quickdev.report")


# ── D1 task acuan ─────────────────────────────────────────────────────────────

@pytest.mark.regression("41 D1")
def test_task_acuan_dibaca_dan_ditautkan(repo, fake):
    f, nf = fake
    t = nf.add_task(TICKET)
    t.update(title="Batasi kuota upload", description="## Kartu\nPengguna dibatasi 10 berkas.")
    r = pl(repo, "task", "--ref", "#1", "--plan", "plan/t.md")
    assert r.returncode == 0, r.stdout
    assert r.stdout.startswith(f"TASK PASS: #1 · todo · workspace ws · sumber analyst · id {t['id']}")
    assert "JUDUL: Batasi kuota upload" in r.stdout and "Pengguna dibatasi 10 berkas." in r.stdout
    assert f"Nataflow-Task: {t['id']}" in (repo / "plan" / "t.md").read_text(encoding="utf-8")
    assert f.writes() == [], "membaca task acuan tidak menulis apa pun ke server"


@pytest.mark.regression("41 D1")
def test_task_acuan_tidak_dibuat_atau_diubah(repo, fake):
    f, nf = fake
    t = nf.add_task(TICKET)
    t.update(title="Batasi kuota upload", description="kartu tiket")
    assert pl(repo, "task", "--ref", "1", "--plan", "plan/t.md").returncode == 0
    code, out = push(repo)
    assert code == 0 and out["segment"].startswith("task #1 · workdir t · 1 dokumen (1 baru"), out
    assert len(nf.tasks) == 1 and (t["title"], t["description"], t["status"]) == ("Batasi kuota upload",
                                                                                   "kartu tiket", "todo")
    assert nf.workdirs[0]["task_id"] == t["id"]
    assert not {"create_task", "update_task"} & set(f.tool_names())
    lock(repo)
    push(repo)
    assert t["status"] == "in_progress" and "update_task" not in f.tool_names()


@pytest.mark.regression("41 D3")
@pytest.mark.parametrize("saudara,akhir", [(None, "done"), ("active", "in_progress"), ("done", "done")])
def test_task_acuan_done_dengan_aturan_saudara(repo, fake, saudara, akhir):
    f, nf = fake
    t = nf.add_task(TICKET)
    if saudara:
        nf.workdirs.append({"id": "wd-be", "workspace_id": WS, "key": "backenddev:tim/api:2611", "name": "be",
                            "status": saudara, "task_id": t["id"], "metadata": {}})
    assert pl(repo, "task", "--ref", t["id"], "--plan", "plan/t.md").returncode == 0
    lock(repo)
    push(repo)
    execute(repo)
    code, out = push(repo)
    assert code == 0 and t["status"] == akhir, out


@pytest.mark.regression("41 D1")
def test_task_acuan_ditolak(repo, fake):
    f, nf = fake
    nf.add_task(TICKET, status="cancelled")
    r = pl(repo, "task", "--ref", "1", "--plan", "plan/t.md", "--json")
    assert r.returncode == 1 and "cancelled" in json.loads(r.stdout)["problems"][0]
    r = pl(repo, "task", "--ref", "99")
    assert r.returncode == 1 and "task not found" in r.stdout
    assert pl(repo, "task", "--ref", "abc").returncode == 1
    a, b = nf.add_task(TICKET), nf.add_task(TICKET)
    assert pl(repo, "task", "--ref", a["id"], "--plan", "plan/t.md").returncode == 0
    r = pl(repo, "task", "--ref", b["id"], "--plan", "plan/t.md")
    assert r.returncode == 1 and "sudah menaut" in r.stdout
    lock(repo)
    r = pl(repo, "task", "--ref", a["id"], "--plan", "plan/t.md")
    assert r.returncode == 1 and "bukan DRAFT" in r.stdout


def test_task_acuan_tanpa_config(make_repo):
    root = make_repo({"plan/t.md": PLAN})
    r = run_script(PL, "task", "--ref", "1", cwd=root)
    assert r.returncode == 1 and "nataflow.json tidak ada" in r.stdout


@pytest.mark.regression("41 D1")
def test_acuan_menyusul_sesudah_tersinkron_ditolak(repo, fake):
    f, nf = fake
    push(repo)                                         # task milik quickdev #1 lahir saat DRAFT
    t = nf.add_task(TICKET)
    assert pl(repo, "task", "--ref", t["id"], "--plan", "plan/t.md").returncode == 0
    before = len(f.writes())
    code, out = push(repo)
    assert code == 1 and "sudah menempel di task lain (#1)" in out["segment"] and len(f.writes()) == before


# ── D2 rencana DRAFT ──────────────────────────────────────────────────────────

@pytest.mark.regression("41 D2")
def test_task_milik_quickdev_mengikuti_revisi_draft(repo, fake):
    f, nf = fake
    push(repo)
    assert nf.tasks[0]["status"] == "todo"
    push(repo)
    assert "update_task" not in f.tool_names(), "isi sama → tanpa update_task"
    plan = repo / "plan" / "t.md"
    plan.write_text(plan.read_text(encoding="utf-8").replace("Tambah validasi kuota.", "Tambah validasi kuota per "
                                                                                       "pengguna."), encoding="utf-8")
    code, out = push(repo)
    assert code == 0 and "per pengguna" in nf.tasks[0]["description"] and len(nf.tasks) == 1
    assert out["segment"].endswith("(0 baru, 1 diperbarui, 0 sama)")
    lock(repo)
    push(repo)
    assert nf.tasks[0]["status"] == "in_progress"


# ── D4 report dan ringkasan naratif ───────────────────────────────────────────

@pytest.mark.regression("41 D4")
def test_summary_hanya_sesudah_close(repo):
    lock(repo)
    r = pl(repo, "summary", "--plan", "plan/t.md", "--summary", "x")
    assert r.returncode == 1 and "belum ditutup" in r.stdout
    assert pl(repo, "start", "--plan", "plan/t.md").returncode == 0
    assert pl(repo, "summary", "--plan", "plan/t.md", "--summary", "x").returncode == 1
    assert pl(repo, "close", "--plan", "plan/t.md", "--status", "BLOCKED", "--blocked-step", "1",
              "--verification", "galat").returncode == 0
    assert pl(repo, "summary", "--plan", "plan/t.md", "--summary", "  ").returncode == 1
    assert "maksimal 600" in pl(repo, "summary", "--plan", "plan/t.md", "--summary", "x" * 601).stdout
    assert pl(repo, "summary", "--plan", "plan/t.md", "--summary", "-", stdin="Terhenti di langkah 1.").returncode == 0
    assert '- Summary: "Terhenti di langkah 1."' in (repo / "plan" / "t.md").read_text(encoding="utf-8")
    pl(repo, "start", "--plan", "plan/t.md")
    assert "- Summary: -" in (repo / "plan" / "t.md").read_text(encoding="utf-8"), "putaran baru menghapus ringkasan"


@pytest.mark.regression("41 D4")
def test_summary_tidak_membuat_segel_basi(repo):
    lock(repo)
    execute(repo)
    status = json.loads(pl(repo, "status", "--plan", "plan/t.md", "--json").stdout)
    assert status["consistent"] and status["execution"]["Summary"].startswith('"Validasi kuota')


@pytest.mark.regression("41 D4")
def test_report_terbit_sesudah_eksekusi(repo, fake):
    f, nf = fake
    lock(repo)
    push(repo)
    assert len(nf.docs) == 1, "report belum ada selama eksekusi belum ditutup"
    execute(repo)
    code, out = push(repo)
    assert code == 0 and out["segment"].endswith("· 2 dokumen (1 baru, 1 diperbarui, 0 sama)"), out
    assert nf.tasks[0]["status"] == "done"
    doc = report(nf)
    body = doc["content"]
    assert doc["key"] == "t.report.md" and doc["metadata"]["status"] == "COMPLETED"
    assert body.startswith("# Laporan Eksekusi — t\n\nValidasi kuota ditambahkan di `checkQuota()`; test lolos.")
    assert "- AC-1: kuota habis → 422 `quota exceeded`" in body and "- [x] 1. Ubah `app.js`" in body
    assert "| `app.js` | diubah | 1/0 |" in body and "| `quota.test.js` | baru (untracked) | -/- |" in body
    assert "plan/t.md` |" not in body.split("## Berkas Berubah")[1], "direktori rencana tidak dihitung"
    assert "- Verification: test=PASSED" in body
    assert git(repo, "status", "--porcelain", "--", "plan") == "?? plan/\n", "report tidak menulis berkas"
    code, out = push(repo)
    assert out["segment"].endswith("(0 baru, 0 diperbarui, 2 sama)")


@pytest.mark.regression("41 D4")
def test_report_tanpa_summary_tetap_terbit(repo, fake):
    f, nf = fake
    lock(repo)
    execute(repo, summary="")
    push(repo)
    assert "_Tanpa ringkasan naratif" in report(nf)["content"]


@pytest.mark.regression("41 D4")
def test_report_gagal_tidak_menggagalkan_rencana(repo, fake):
    f, nf = fake
    upsert = f.tools["upsert_document"]

    def tolak_report(args):
        if args["type"] == "quickdev.report":
            raise ToolError("invalid input data")
        return upsert(args)

    f.tools["upsert_document"] = tolak_report
    lock(repo)
    execute(repo)
    code, out = push(repo)
    assert code == 0 and out["segment"].endswith("· report GAGAL: upsert_document: invalid input data"), out
    assert [d["type"] for d in nf.docs] == ["quickdev.plan"] and nf.tasks[0]["status"] == "done"
