"""15 B2, B8–B10, B12 — `sync_payload.py` backend: argumen tool MCP nataflow untuk taskdir dan dokumen repo."""
import json

import pytest

from conftest import BE_SKILLS, TD, be_run, brief, commit, git, load_module, run_script, write_files

SP = BE_SKILLS / "_common" / "sync_payload.py"
PL = load_module(BE_SKILLS / "_common" / "precondition_lib.py", "be_precondition_lib_sync24")
WS = "11111111-2222-3333-4444-555555555555"
TICKET = "analyst/tickets/2609231400-cicilan-pembayaran"


@pytest.fixture
def repo(chain_repo):
    write_files(chain_repo, {".claude/nataflow.json": json.dumps({"workspaces": {"utama": WS}, "repo": "tim/api"})})
    commit(chain_repo, "chore: aktifkan sinkron nataflow")
    return chain_repo


def sp(repo, *args, stdin=""):
    r = run_script(SP, *args, "--json", cwd=repo, stdin=stdin)
    assert r.stdout.strip(), r.stderr
    return r.returncode, json.loads(r.stdout)


def push(repo, remote="[]", target=("--taskdir", TD)):
    code, out = sp(repo, *target, "--remote", "-", stdin=remote)
    assert code == 0, out
    return out


def keys(out):
    return [d["key"] for d in out["documents"]]


def sealed(text):
    """BRD/PRD `APPROVED` bermaterai utuh, seperti tulisan `doc_seal.py approve` (Langkah 24)."""
    return text.replace("status: APPROVED\n", f"status: APPROVED\napproved_seal: {PL.doc_seal(text)}\n")


def lock(repo):
    r = be_run(repo, "_common/doc_seal.py", "lock-briefs", "--taskdir", TD)
    assert r.returncode == 0, r.stdout + r.stderr


def view(doc, **over):
    v = {"key": doc["key"], "type": doc["type"], "mimetype": "text/markdown",
         "content_sha256": doc["content_sha256"], "metadata": json.loads(doc["metadata"])}
    v.update(over)
    return v


@pytest.mark.regression("15 B12")
def test_skip_tanpa_config(chain_repo):
    assert sp(chain_repo, "--taskdir", TD) == (0, {"status": "SKIP", "enabled": False})


def test_config_rusak_fail(repo):
    write_files(repo, {".claude/nataflow.json": "{"})
    code, out = sp(repo, "--taskdir", TD)
    assert code == 1 and out["problems"][0].startswith(".claude/nataflow.json rusak")


def test_taskdir_tidak_sah_dan_akar_belum_terkunci(repo):
    assert "pola kanonik" in sp(repo, "--taskdir", "backenddev/docs/salah")[1]["problems"][0]
    td = "backenddev/docs/2609241000-baru"
    write_files(repo, {f"{td}/TASK.md": "---\nstatus: ACTIVE\n---\n# Baru\n"})
    assert "akar belum terkunci" in sp(repo, "--taskdir", td)[1]["problems"][0]


@pytest.mark.regression("15 B2")
def test_fase_satu_task_sendiri(repo):
    code, out = sp(repo, "--taskdir", TD)
    assert code == 0 and out["status"] == "PASS"
    key = f"backenddev:tim/api:{TD}"
    assert out["task"]["lookup"] == {"metadata": json.dumps(
        {"source": "backenddev", "workdir_key": key}, separators=(",", ":"))}
    create = out["task"]["create"]
    assert create["title"] == "Order fix" and create["description"].startswith("## Success Criteria")
    assert json.loads(create["metadata"]) == {"source": "backenddev", "workdir_key": key, "repo": "tim/api"}
    assert out["task"]["status"] is None
    wd = out["workdir"]
    assert (wd["key"], wd["name"], wd["status"]) == (key, "2609240900-order-fix", "active")
    assert json.loads(wd["metadata"]) == {"source": "backenddev", "repo": "tim/api", "path": TD,
                                          "chain": "BRIEF", "risk": "MINOR"}
    assert out["list_document"] == {"reference_table": "workdir", "include_content": False}
    assert out["documents_total"] == 1 and '"content":' not in json.dumps(out)


@pytest.mark.regression("24 K14")
def test_pilihan_berkas_stabil_dari_disk(repo):
    prd = sealed("---\nstatus: APPROVED\n---\n# PRD\n")
    write_files(repo, {f"{TD}/BRD.md": "---\nstatus: DRAFT\n---\n# BRD\n", f"{TD}/PRD.md": prd,
                       f"{TD}/RCA.md": "# RCA di disk\n", f"{TD}/.explore/gate-x.md": "catatan\n",
                       f"{TD}/NOTES.md": "bukan artefak\n"})
    brief(repo, "01", "order-lock", "READY")                                   # belum dikunci
    out = push(repo)
    assert keys(out) == ["PRD.md", "RCA.md", "TASK.md"], "DRAFT, brief belum terkunci, .explore/, non-artefak tidak ikut"
    doc = out["documents"][0]
    assert doc["content"] == prd, "isi disk apa adanya"
    meta = json.loads(doc["metadata"])
    assert meta["status"] == "APPROVED" and meta["path"] == f"{TD}/PRD.md" and meta["commit"] == ""
    assert meta["head"] == git(repo, "rev-parse", "HEAD").strip()
    (repo / TD / "PRD.md").write_text(prd.replace("# PRD", "# PRD disunting"), encoding="utf-8")
    assert "PRD.md" not in keys(push(repo)), "APPROVED yang disunting sesudah approve tidak dicerminkan"


@pytest.mark.regression("15 B9")
def test_status_workdir_dan_task_dari_disk(repo):
    b1 = brief(repo, "01", "order-lock", "READY")
    lock(repo)
    out = sp(repo, "--taskdir", TD)[1]
    assert out["workdir"]["status"] == "active" and out["task"]["status"] is None
    b1.write_text(b1.read_text(encoding="utf-8").replace("status: READY", "status: BLOCKED"), encoding="utf-8")
    out = sp(repo, "--taskdir", TD)[1]
    assert out["workdir"]["status"] == "blocked"
    assert out["task"]["status"] == {"status": "in_progress", "from": ["todo"]}
    write_files(repo, {f"{TD}/REPORT.md": "# Order fix — Report\n"})
    out = sp(repo, "--taskdir", TD)[1]
    assert out["workdir"]["status"] == "done"
    assert out["task"]["status"] == {"status": "done", "from": ["todo", "in_progress"]}


@pytest.mark.regression("15 B2")
def test_taskdir_bertiket_menempel_ke_task_analyst(repo):
    task = (repo / TD / "TASK.md").read_text(encoding="utf-8")
    write_files(repo, {f"{TD}/TASK.md": task.replace("status: ACTIVE\n",
                                                     f"status: ACTIVE\nticket_source: ./{TICKET}/TICKET.md\n"),
                       f"{TD}/REPORT.md": "# laporan\n"})
    commit(repo, "docs: akar bertiket")
    out = sp(repo, "--taskdir", TD)[1]
    ident = {"source": "analyst", "ticket_key": TICKET}
    assert out["task"]["lookup"]["metadata"] == json.dumps(ident, separators=(",", ":"))
    assert json.loads(out["task"]["create"]["metadata"]) == dict(ident, repo="tim/api")
    assert out["task"]["status"]["status"] == "in_progress", "task tiket tidak ditutup oleh satu taskdir (E8)"
    assert json.loads(out["workdir"]["metadata"])["ticket_key"] == TICKET


def test_ticket_source_rusak(repo):
    task = (repo / TD / "TASK.md").read_text(encoding="utf-8")
    write_files(repo, {f"{TD}/TASK.md": task.replace("status: ACTIVE\n", "status: ACTIVE\nticket_source: x.md\n")})
    commit(repo, "docs: akar")
    assert "bukan path" in sp(repo, "--taskdir", TD)[1]["problems"][0]


@pytest.mark.regression("15 B8")
def test_diff_hanya_yang_berbeda(repo):
    b1 = brief(repo, "01", "order-lock", "READY")
    lock(repo)
    first = push(repo)
    assert keys(first) == ["TASK.md", "brief-01-order-lock.md"] and first["same"] == 0
    remote = [view(d) for d in first["documents"]]
    assert push(repo, json.dumps(remote))["documents"] == []
    b1.write_text(b1.read_text(encoding="utf-8").replace("status: READY", "status: DONE"), encoding="utf-8")
    out = push(repo, json.dumps(remote))
    assert keys(out) == ["brief-01-order-lock.md"] and out["same"] == 1


@pytest.mark.regression("24 K11")
def test_halt_dicabut_didorong_berstatus_dicabut(repo):
    write_files(repo, {f"{TD}/HALT.md": "---\nbrief: brief-01\nverdict: SCOPE\n---\n# HALT\n"})
    halt = next(d for d in push(repo)["documents"] if d["key"] == "HALT.md")
    assert sp(repo, "--taskdir", TD)[1]["workdir"]["status"] == "blocked"
    r = be_run(repo, "_common/doc_seal.py", "cabut-halt", "--taskdir", TD, "--alasan", "scope diterima user")
    assert r.returncode == 0, r.stdout
    out = push(repo, json.dumps([view(halt)]))
    (doc,) = [d for d in out["documents"] if d["key"] == "HALT.md"]
    assert json.loads(doc["metadata"])["status"] == "DICABUT" and "removed" not in json.loads(doc["metadata"])
    assert sp(repo, "--taskdir", TD)[1]["workdir"]["status"] == "active", "HALT dicabut → tidak lagi blocked"


@pytest.mark.regression("24 G5")
def test_dokumen_taskdir_yang_hilang_tidak_didorong(repo):
    write_files(repo, {f"{TD}/RCA.md": "# RCA\n"})
    rca = next(d for d in push(repo)["documents"] if d["key"] == "RCA.md")
    (repo / TD / "RCA.md").unlink()
    assert "RCA.md" not in keys(push(repo, json.dumps([view(rca)]))), "isi terakhir dibiarkan di server"


@pytest.mark.regression("15 E11")
def test_type_mengikuti_format_server(repo):
    write_files(repo, {f"{TD}/PRD.md": sealed("---\nstatus: APPROVED\n---\n# PRD\n"), f"{TD}/RCA.md": "# RCA\n",
                       f"{TD}/HALT.md": "---\nverdict: SCOPE\n---\n# HALT\n", f"{TD}/report-01.md": "# r\n",
                       f"{TD}/REVIEW.md": "# review\n", f"{TD}/REPORT.md": "# report\n"})
    docs = push(repo)["documents"]
    assert {d["key"]: d["type"] for d in docs} == {
        "PRD.md": "prd", "RCA.md": "rca", "HALT.md": "halt", "report-01.md": "unit.report",
        "REVIEW.md": "review", "REPORT.md": "report", "TASK.md": "task"}
    prd = next(d for d in docs if d["key"] == "PRD.md")
    write_files(repo, {f"{TD}/PRD.md": "---\nstatus: DRAFT\n---\n# PRD v2\n"})          # tidak lagi terpilih
    (doc,) = [d for d in push(repo, json.dumps([view(prd, type="PRD")]))["documents"] if d["key"] == "PRD.md"]
    assert doc["type"] == "prd", "type remote bergaya lama dinormalkan sebelum dikirim ulang"


def test_dokumen_tercermin_yang_kembali_draft_diperbarui(repo):
    write_files(repo, {f"{TD}/BRD.md": sealed("---\nstatus: APPROVED\n---\n# BRD\n")})
    brd = next(d for d in push(repo)["documents"] if d["key"] == "BRD.md")
    write_files(repo, {f"{TD}/BRD.md": "---\nstatus: DRAFT\n---\n# BRD v2\n"})
    (doc,) = [d for d in push(repo, json.dumps([view(brd)]))["documents"] if d["key"] == "BRD.md"]
    assert json.loads(doc["metadata"])["status"] == "DRAFT" and "removed" not in json.loads(doc["metadata"])


@pytest.mark.regression("15 B10")
def test_dokumen_repo_ke_workspace(repo):
    write_files(repo, {"backenddev/issues/README.md": "# indeks\n", "backenddev/issues/2609-order.md": "# audit\n",
                       "docs/api/order.md": "# API order\n"})
    commit(repo, "docs: audit dan api")
    code, out = sp(repo, "--repo-docs", "audit")
    assert code == 0 and out["workspace_id"] == WS and out["documents_total"] == 2
    assert json.loads(out["list_document"]["metadata"]) == {"source": "backenddev", "repo": "tim/api"}
    docs = push(repo, target=("--repo-docs", "audit"))["documents"]
    assert [d["key"] for d in docs] == ["tim/api/backenddev/issues/2609-order.md", "tim/api/backenddev/issues/README.md"]
    assert {d["type"] for d in docs} == {"audit"} and {d["reference_table"] for d in docs} == {"workspace"}
    assert [d["type"] for d in push(repo, target=("--repo-docs", "api"))["documents"]] == ["api.doc"]
    prof = push(repo, target=("--repo-docs", "profile"))["documents"]
    assert prof and all(d["key"].startswith("tim/api/.claude/profile/backenddev/") for d in prof)
    assert {d["type"] for d in prof} == {"profile"}


def test_dokumen_repo_terhapus_hanya_di_cakupan_jenisnya(repo):
    write_files(repo, {"docs/api/order.md": "# API order\n"})
    commit(repo, "docs: api")
    api = push(repo, target=("--repo-docs", "api"))["documents"][0]
    git(repo, "rm", "-q", "docs/api/order.md")
    git(repo, "commit", "-qm", "docs: hapus api")
    other = dict(view(api), key="tim/api/backenddev/issues/lama.md")
    out = push(repo, json.dumps([view(api), other]), target=("--repo-docs", "api"))
    assert [d["key"] for d in out["documents"]] == ["tim/api/docs/api/order.md"]
    assert json.loads(out["documents"][0]["metadata"])["removed"] is True


def test_byte_stabil_dan_read_only(repo):
    runs = {run_script(SP, "--taskdir", TD, "--json", cwd=repo).stdout for _ in range(2)}
    assert len(runs) == 1
    assert git(repo, "status", "--porcelain") == ""


def test_remote_rusak(repo):
    code, out = sp(repo, "--taskdir", TD, "--remote", "-", stdin="{")
    assert code == 1 and "bukan JSON sah" in out["problems"][0]
