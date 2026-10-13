"""Regresi Langkah 15 (A1–A4, A6, A7, A9) — sinkron analyst selaras pustaka bersama, `review.md`, pembatalan,
dan `ticket_key` yang sama persis di plugin engineer.

Tiket READY dibentuk lewat jalur `analyst:spec` (review bersidik, lalu `approve`) dari `fixtures/ticket_valid.md`.
"""
import hashlib
import json
from pathlib import Path

import pytest

from conftest import PLUGINS, commit, git, run_script, ticket_review, write_files

TICKET = PLUGINS / "analyst" / "skills" / "_common" / "ticket.py"
BE_SP = PLUGINS / "backend" / "skills" / "_common" / "sync_payload.py"
FE_SP = PLUGINS / "frontend" / "skills" / "_common" / "sync_payload.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
WS = "a3e1d6c4-1f2b-4c3d-9e8f-7a6b5c4d3e2f"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    git(root, "remote", "add", "origin", "https://github.com/tim/produk.git")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    return root


def tk(root, *args):
    return run_script(TICKET, *args, cwd=root)


def approve(root):
    assert ticket_review(root, TDIR, "PASS").returncode == 0
    r = tk(root, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    assert r.returncode == 0, r.stdout + r.stderr


def shared(root, data):
    write_files(root, {".claude/nataflow.json": json.dumps(data)})


def legacy(root, data):
    write_files(root, {"analyst/nataflow.json": json.dumps(data)})


def payload(root):
    r = tk(root, "sync-payload", "--ticketdir", TDIR, "--json")
    assert "Traceback" not in r.stderr, r.stderr
    return r.returncode, json.loads(r.stdout)


# --- A1: config bersama -----------------------------------------------------------------------

@pytest.mark.regression("15 A1")
def test_config_bersama_mengaktifkan_sinkron(repo):
    approve(repo)
    assert payload(repo)[1]["status"] == "SKIP"
    shared(repo, {"workspaces": {"utama": WS}})
    code, out = payload(repo)
    assert code == 0 and out["create"]["workspace_id"] == WS and "workspace_id" not in out["lookup"]


@pytest.mark.regression("15 A1")
def test_config_lama_sama_isi_diterima_berbeda_ditolak(repo):
    approve(repo)
    legacy(repo, {"workspaces": {"utama": WS}})
    shared(repo, {"workspaces": {"utama": WS}})
    assert payload(repo)[0] == 0
    shared(repo, {"workspaces": {"utama": WS}, "mcp_server": "nataflow-staging"})
    code, out = payload(repo)
    assert code == 1 and "berbeda isi" in out["problems"][0]


# --- A2/A3: identitas repo --------------------------------------------------------------------

@pytest.mark.regression("15 A3")
def test_repo_di_metadata_bukan_di_lookup(repo):
    shared(repo, {})
    approve(repo)
    _, out = payload(repo)
    assert json.loads(out["create"]["metadata"])["repo"] == "github.com/tim/produk"
    assert out["update"]["metadata"] == out["create"]["metadata"]
    assert json.loads(out["lookup"]["metadata"]) == {"source": "analyst", "ticket_key": TDIR}
    shared(repo, {"repo": "tim/produk"})
    assert json.loads(payload(repo)[1]["create"]["metadata"])["repo"] == "tim/produk"


# --- A4: review.md ----------------------------------------------------------------------------

@pytest.mark.regression("15 A4")
def test_review_md_sebagai_dokumen_task(repo):
    shared(repo, {})
    approve(repo)
    (doc,) = payload(repo)[1]["documents"]
    disk = (repo / TDIR / "review.md").read_bytes().decode("utf-8")
    assert (doc["reference_table"], doc["key"], doc["type"]) == ("task", "review.md", "ticket.review")
    assert doc["content"] == disk and doc["content_sha256"] == hashlib.sha256(disk.encode("utf-8")).hexdigest()
    meta = json.loads(doc["metadata"])
    assert (meta["source"], meta["path"], meta["status"]) == ("analyst", f"{TDIR}/review.md", "PASS")
    assert meta["commit"] == git(repo, "log", "-1", "--format=%H", "--", f"{TDIR}/review.md").strip()
    assert "reference_id" not in doc


def test_elisitasi_tetap_tidak_dikirim(repo):
    """A5 tidak diambil (E2): catatan elisitasi tidak pernah menjadi dokumen."""
    shared(repo, {})
    approve(repo)
    out = payload(repo)[1]
    assert [d["key"] for d in out["documents"]] == ["review.md"]
    sent = [out["create"]["description"], out["update"]["description"]] + [d["content"] for d in out["documents"]]
    assert not any("## Catatan Elisitasi" in s for s in sent)


# --- A6: pembatalan ---------------------------------------------------------------------------

@pytest.mark.regression("15 A6")
def test_tiket_ready_dibatalkan_menjadi_cancelled(repo):
    shared(repo, {"workspaces": {"utama": WS}})
    approve(repo)
    lookup = payload(repo)[1]["lookup"]
    assert tk(repo, "cancel", "--ticketdir", TDIR, "--reason", "tidak jadi", "--force").returncode == 0
    code, out = payload(repo)
    assert code == 0 and out["lookup"] == lookup
    assert out["task_status"] == {"status": "cancelled", "from": ["todo", "in_progress"]}
    assert not {"create", "update", "documents"} & set(out), "task yang dibatalkan tidak diperbarui isinya"


@pytest.mark.regression("15 A6")
def test_pernah_ready_lalu_dibuka_ulang_dan_dibatalkan(repo):
    shared(repo, {})
    approve(repo)
    assert tk(repo, "reopen", "--ticketdir", TDIR, "--reason", "ubah").returncode == 0
    assert tk(repo, "cancel", "--ticketdir", TDIR, "--reason", "batal", "--no-commit").returncode == 0
    assert payload(repo)[1]["task_status"]["status"] == "cancelled"


def test_draft_dibatalkan_tetap_fail(repo):
    shared(repo, {})
    assert tk(repo, "cancel", "--ticketdir", TDIR, "--reason", "batal").returncode == 0
    code, out = payload(repo)
    assert code == 1 and " DIBATALKAN — hanya tiket READY" in out["problems"][0]


# --- A7: ticket_key lintas plugin -------------------------------------------------------------

@pytest.mark.regression("15 A7")
def test_lookup_tiket_sama_di_analyst_backend_frontend(repo):
    """Taskdir backend dan frontend dari tiket yang sama wajib menemukan task analyst yang sama: `lookup`
    ketiganya byte-identik. Bila salah satu sisi mengubah turunan `ticket_key`, workdir menempel ke task lain
    atau melahirkan task kembar."""
    shared(repo, {"workspaces": {"utama": WS}})
    approve(repo)
    source = f"ticket_source: {TDIR}/TICKET.md\n"
    be_td, fe_td = "backenddev/docs/2609241000-cicilan-api", "frontenddev/docs/2609241000-cicilan-ui"
    write_files(repo, {
        f"{be_td}/TASK.md": (f"---\nstatus: ACTIVE\nchain: BRIEF\nrisk: MINOR\n{source}"     # akar backend terkunci (24)
                             f"base_commit: {git(repo, 'rev-parse', 'HEAD').strip()}\n---\n# Cicilan API\n"),
        f"{fe_td}/TASK.md": (f"---\nstatus: ACTIVE\nlane: FAST_FORWARD\nsections: [architecture]\n{source}---\n"
                             "# Cicilan UI\n"),
    })
    commit(repo, "docs: akar engineer", be_td, fe_td)
    analyst = payload(repo)[1]["lookup"]
    backend = json.loads(run_script(BE_SP, "--taskdir", be_td, "--json", cwd=repo).stdout)["task"]["lookup"]
    frontend = json.loads(run_script(FE_SP, "--taskdir", fe_td, "--json", cwd=repo).stdout)["task"]["lookup"]
    assert analyst == backend == frontend
