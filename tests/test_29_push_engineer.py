"""29 S3 — `sync_payload.py --push` backend dan frontend terhadap server MCP palsu.

Skrip sendiri yang memanggil tool: task → workdir → manifest → dokumen → status task, lalu mencetak satu baris
segmen. Jalur gagal (key, task kembar, pilihan workspace) berhenti sebelum tool tulis mana pun.
"""
import json

import pytest

from conftest import BE_SKILLS, FE_SKILLS, FE_TD, TD, commit, run_script, write_files
from nataflow_fake import FakeMCP, Nataflow, enable_sync

BE = BE_SKILLS / "_common" / "sync_payload.py"
FE = FE_SKILLS / "_common" / "sync_payload.py"
WEB = "aaaaaaaa-0000-4000-8000-000000000001"
MOBILE = "aaaaaaaa-0000-4000-8000-000000000002"
TICKET = "analyst/tickets/2609231400-cicilan-pembayaran"


def run(script, repo, *args):
    r = run_script(script, *args, "--push", "--json", cwd=repo)
    assert "Traceback" not in r.stderr, r.stderr
    return r.returncode, json.loads(r.stdout)


def plain(script, repo, *args):
    r = run_script(script, *args, "--push", cwd=repo)
    assert "Traceback" not in r.stderr, r.stderr
    return r.returncode, r.stdout


@pytest.fixture
def fake():
    with FakeMCP() as f:
        yield f, Nataflow(f, workspaces=[WEB])


@pytest.fixture
def be(chain_repo, fake):
    f, _ = fake
    enable_sync(chain_repo, f.url, extra={"repo": "tim/api"})
    return chain_repo


# ── Key & config ─────────────────────────────────────────────────────────────

def test_tanpa_config_dilewati(chain_repo):
    code, out = run(BE, chain_repo, "--taskdir", TD)
    assert (code, out["status"], out["segment"]) == (0, "SKIP", "dilewati")


def test_tanpa_local_json_gagal_tanpa_panggilan(chain_repo, fake):
    f, _ = fake
    enable_sync(chain_repo, f.url)
    (chain_repo / ".claude/nataflow.local.json").unlink()
    code, out = run(BE, chain_repo, "--taskdir", TD)
    assert code == 1 and out["segment"].startswith("GAGAL: .claude/nataflow.local.json tidak ada")
    assert f.requests == []


def test_local_json_tidak_diabaikan_gagal(chain_repo, fake):
    f, _ = fake
    enable_sync(chain_repo, f.url, ignore=False)
    code, out = run(BE, chain_repo, "--taskdir", TD)
    assert code == 1 and "tidak diabaikan git" in out["segment"] and f.requests == []


def test_config_mcp_server_lama_gagal_dengan_pesan_migrasi(be):
    write_files(be, {".claude/nataflow.json": json.dumps({"mcp_server": "nataflow-api"})})
    code, out = run(BE, be, "--taskdir", TD)
    assert code == 1 and "`mcp_server` sudah diganti `url`" in out["segment"]


# ── Workdir taskdir ──────────────────────────────────────────────────────────

@pytest.mark.regression("29 S3")
def test_task_baru_lalu_sinkron_ulang_sama(be, fake):
    f, nf = fake
    code, out = run(BE, be, "--taskdir", TD)
    assert code == 0, out
    assert out["segment"] == "workdir 2609240900-order-fix · 1 dokumen (1 baru, 0 diperbarui, 0 sama)"
    assert len(nf.tasks) == 1 and nf.tasks[0]["status"] == "in_progress" and nf.tasks[0]["title"] == "Order fix"
    assert nf.workdirs[0]["task_id"] == nf.tasks[0]["id"] and nf.workdirs[0]["workspace_id"] == WEB
    assert [d["key"] for d in nf.docs] == ["TASK.md"]
    task_text = (be / TD / "TASK.md").read_text(encoding="utf-8")
    f.calls.clear()
    code, out = run(BE, be, "--taskdir", TD)
    assert out["segment"].endswith("(0 baru, 0 diperbarui, 1 sama)") and len(nf.tasks) == 1
    assert "upsert_document" not in f.tool_names() and "create_task" not in f.tool_names()
    assert "Success Criteria" not in json.dumps(out), "isi dokumen tidak pernah dicetak"
    assert task_text.splitlines()[-1] not in json.dumps(out)
    code, text = plain(BE, be, "--taskdir", TD)
    assert code == 0 and text == "workdir 2609240900-order-fix · 1 dokumen (0 baru, 0 diperbarui, 1 sama)\n", \
        "tanpa --json: tepat satu baris segmen"


def test_dokumen_berubah_diperbarui(be, fake):
    f, nf = fake
    run(BE, be, "--taskdir", TD)
    write_files(be, {f"{TD}/RCA.md": "# RCA\n"})
    path = be / TD / "TASK.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nTambahan.\n", encoding="utf-8")
    code, out = run(BE, be, "--taskdir", TD)
    assert out["segment"].endswith("· 2 dokumen (1 baru, 1 diperbarui, 0 sama)"), out


def test_task_kembar_gagal_tanpa_tulisan(be, fake):
    f, nf = fake
    ident = {"source": "backenddev", "workdir_key": f"backenddev:tim/api:{TD}"}
    nf.add_task(ident)
    nf.add_task(ident)
    code, out = run(BE, be, "--taskdir", TD)
    assert code == 1 and out["segment"] == "GAGAL: 2 task ber-identitas sama (#1, #2)"
    assert f.writes() == []


def test_task_ada_dipakai_dan_status_tidak_diturunkan(be, fake):
    f, nf = fake
    t = nf.add_task({"source": "backenddev", "workdir_key": f"backenddev:tim/api:{TD}"}, status="done",
                    workspace_id=MOBILE)
    code, out = run(BE, be, "--taskdir", TD)
    assert code == 0 and len(nf.tasks) == 1
    assert nf.workdirs[0]["workspace_id"] == MOBILE, "workdir di workspace task induknya"
    assert t["status"] == "done" and "update_task_status" not in f.tool_names()


def test_pilih_workspace_sebelum_task_baru(be, fake):
    f, nf = fake
    enable_sync(be, f.url, extra={"repo": "tim/api", "workspaces": {"web": WEB, "mobile": MOBILE}})
    code, out = run(BE, be, "--taskdir", TD)
    assert code == 0 and out["status"] == "PILIH_WORKSPACE"
    assert out["workspace_choices"] == [{"alias": "web", "workspace_id": WEB}, {"alias": "mobile", "workspace_id": MOBILE}]
    assert out["segment"].startswith("PILIH_WORKSPACE: web (") and "--workspace" in out["segment"]
    assert f.writes() == []
    nf.workspaces.append(MOBILE)
    code, out = run(BE, be, "--taskdir", TD, "--workspace", "mobile")
    assert code == 0 and nf.tasks[0]["workspace_id"] == MOBILE and nf.workdirs[0]["workspace_id"] == MOBILE


def test_task_tiket_done_hanya_bila_seluruh_workdir_tuntas(be, fake):
    f, nf = fake
    path = be / TD / "TASK.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "status: ACTIVE\n", f"status: ACTIVE\nticket_source: {TICKET}/TICKET.md\n"), encoding="utf-8")
    write_files(be, {f"{TD}/REPORT.md": "# Order fix — Report\n"})
    t = nf.add_task({"source": "analyst", "ticket_key": TICKET}, status="in_progress")
    nf.workdirs.append({"id": "fe-1", "workspace_id": WEB, "key": "frontenddev:tim/web:x", "name": "x",
                        "status": "active", "task_id": t["id"], "metadata": {}})
    code, out = run(BE, be, "--taskdir", TD)
    assert code == 0 and t["status"] == "in_progress", "workdir frontend masih active"
    assert "list_workdir" in f.tool_names()
    nf.workdirs[0]["status"] = "done"
    run(BE, be, "--taskdir", TD)
    assert t["status"] == "done"


def test_galat_tool_di_tengah_jalan(be, fake):
    f, nf = fake

    def boom(_a):
        from nataflow_fake import ToolError
        raise ToolError("invalid input data")
    f.tools["upsert_workdir"] = boom
    code, out = run(BE, be, "--taskdir", TD)
    assert code == 1 and out["segment"] == "GAGAL: upsert_workdir: invalid input data"
    assert "list_document" not in f.tool_names(), "langkah sesudah galat tidak dijalankan"


def test_server_mati(be):
    enable_sync(be, "http://127.0.0.1:9/mcp", extra={"repo": "tim/api"})
    code, out = run(BE, be, "--taskdir", TD)
    assert code == 1 and out["segment"].startswith("GAGAL: tidak dapat menghubungi http://127.0.0.1:9/mcp")


# ── Dokumen repo ─────────────────────────────────────────────────────────────

def test_dokumen_repo_workspace_tunggal_key(be, fake):
    f, nf = fake
    write_files(be, {"backenddev/issues/2609250000-audit.md": "# audit\n"})
    commit(be, "docs(audit): x", "backenddev/issues/2609250000-audit.md")
    code, out = run(BE, be, "--repo-docs", "audit")
    assert code == 0 and out["segment"] == "repo · 1 dokumen (1 baru, 0 diperbarui, 0 sama)"
    assert "list_workspace" in f.tool_names() and nf.docs[0]["reference_id"] == WEB


def test_dokumen_repo_key_banyak_workspace_gagal(be, fake):
    f, nf = fake
    nf.workspaces.append(MOBILE)
    code, out = run(BE, be, "--repo-docs", "audit")
    assert code == 1 and "key menjangkau 2 workspace" in out["segment"] and f.writes() == []


def test_dokumen_repo_pilih_workspace_tanpa_panggilan(be, fake):
    f, nf = fake
    enable_sync(be, f.url, extra={"repo": "tim/api", "workspaces": {"web": WEB, "mobile": MOBILE}})
    code, out = run(BE, be, "--repo-docs", "audit")
    assert out["status"] == "PILIH_WORKSPACE" and f.calls == []


# ── Frontend ─────────────────────────────────────────────────────────────────

@pytest.mark.regression("29 S3")
def test_frontend_push_berawalan_nataflow(fe_chain_repo, fake):
    f, nf = fake
    enable_sync(fe_chain_repo, f.url, extra={"repo": "tim/web"})
    code, out = run(FE, fe_chain_repo, "--taskdir", FE_TD)
    assert code == 0, out
    assert out["segment"].startswith("nataflow workdir ") and "(1 baru, 0 diperbarui, 0 sama)" in out["segment"]
    assert nf.tasks[0]["status"] == "in_progress" and nf.docs[0]["key"] == "TASK.md"
    assert run(FE, fe_chain_repo, "--taskdir", FE_TD)[1]["segment"].endswith("(0 baru, 0 diperbarui, 1 sama)")


def test_frontend_tanpa_config_dilewati(fe_chain_repo):
    assert run(FE, fe_chain_repo, "--taskdir", FE_TD)[1]["segment"] == "nataflow dilewati"
