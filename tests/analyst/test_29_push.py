"""29 S5 — `ticket.py sync-payload --push` dan `notulen.py sync-payload --push` terhadap server MCP palsu."""
import json
from pathlib import Path

import pytest

from conftest import PLUGINS, git, load_module, run_script, ticket_review
from nataflow_fake import FakeMCP, Nataflow, enable_sync

TICKET = PLUGINS / "analyst" / "skills" / "_common" / "ticket.py"
NOTULEN = PLUGINS / "analyst" / "skills" / "notulen" / "scripts" / "notulen.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
NT = load_module(Path(__file__).resolve().parent / "test_notulen_18.py", "notulen_helpers_29")
WEB = "cccccccc-0000-4000-8000-000000000001"
MOBILE = "cccccccc-0000-4000-8000-000000000002"


@pytest.fixture
def fake():
    with FakeMCP() as f:
        yield f, Nataflow(f, workspaces=[WEB])


@pytest.fixture
def repo(make_repo, fake):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    enable_sync(root, fake[0].url, extra={"repo": "tim/produk"})
    return root


def tk(root, *args):
    return run_script(TICKET, *args, cwd=root)


def approve(root):
    assert ticket_review(root, TDIR, "PASS").returncode == 0
    r = tk(root, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    assert r.returncode == 0, r.stdout + r.stderr


def push(script, root, *args):
    r = run_script(script, "sync-payload", *args, "--push", "--json", cwd=root)
    assert "Traceback" not in r.stderr, r.stderr
    return r.returncode, json.loads(r.stdout)


# ── Tiket ────────────────────────────────────────────────────────────────────

@pytest.mark.regression("29 S5")
def test_tiket_dibuat_lalu_diperbarui(repo, fake):
    f, nf = fake
    approve(repo)
    code, out = push(TICKET, repo, "--ticketdir", TDIR)
    assert code == 0 and out["segment"] == "nataflow dibuat #1 · review.md baru", out
    task = nf.tasks[0]
    assert task["metadata"]["ticket_key"] == TDIR and task["status"] == "todo", "analyst tidak mengirim status"
    assert nf.docs[0]["reference_table"] == "task" and nf.docs[0]["key"] == "review.md"
    assert task["description"] not in json.dumps(out), "isi kartu tidak dicetak"
    code, out = push(TICKET, repo, "--ticketdir", TDIR)
    assert out["segment"] == "nataflow diperbarui #1 · review.md sama" and len(nf.tasks) == 1


def test_tiket_task_kembar_gagal_tanpa_tulisan(repo, fake):
    f, nf = fake
    approve(repo)
    nf.add_task({"source": "analyst", "ticket_key": TDIR})
    nf.add_task({"source": "analyst", "ticket_key": TDIR})
    code, out = push(TICKET, repo, "--ticketdir", TDIR)
    assert code == 1 and out["segment"] == "nataflow GAGAL: 2 task ber-ticket_key sama (#1, #2)" and f.writes() == []


def test_tiket_pilih_workspace(repo, fake):
    f, nf = fake
    enable_sync(repo, f.url, extra={"workspaces": {"web": WEB, "mobile": MOBILE}})
    approve(repo)
    code, out = push(TICKET, repo, "--ticketdir", TDIR)
    assert out["status"] == "PILIH_WORKSPACE" and out["segment"].startswith("nataflow PILIH_WORKSPACE: web (")
    assert f.writes() == []
    nf.workspaces.append(MOBILE)
    code, out = push(TICKET, repo, "--ticketdir", TDIR, "--workspace", "mobile")
    assert code == 0 and nf.tasks[0]["workspace_id"] == MOBILE


def test_tiket_dibatalkan(repo, fake):
    f, nf = fake
    approve(repo)
    push(TICKET, repo, "--ticketdir", TDIR)
    assert tk(repo, "cancel", "--ticketdir", TDIR, "--reason", "batal", "--force").returncode == 0
    code, out = push(TICKET, repo, "--ticketdir", TDIR)
    assert code == 0 and out["segment"] == "nataflow dibatalkan #1" and nf.tasks[0]["status"] == "cancelled"
    nf.tasks[0]["status"] = "done"
    assert push(TICKET, repo, "--ticketdir", TDIR)[1]["segment"] == "nataflow dilewati (task done #1)"


def test_tiket_draft_gagal_tanpa_panggilan(repo, fake):
    f, _ = fake
    code, out = push(TICKET, repo, "--ticketdir", TDIR)
    assert code == 1 and out["segment"].startswith("nataflow GAGAL: ") and f.requests == []


# ── Notulen ──────────────────────────────────────────────────────────────────

@pytest.fixture
def notes_root(make_repo, fake):
    root = make_repo(name="plain", git_init=False)
    rel = NT.finalized(root)
    enable_sync(root, fake[0].url, ignore=False)      # root non-git: tanpa cek ignore
    return root, rel


@pytest.mark.regression("29 S5")
def test_notulen_dibuat_tidak_berubah_diperbarui(notes_root, fake):
    f, nf = fake
    root, rel = notes_root
    code, out = push(NOTULEN, root, "--notulendir", rel)
    assert code == 0 and out["segment"] == "nataflow dibuat", out
    doc = nf.docs[0]
    assert (doc["reference_table"], doc["reference_id"], doc["type"]) == ("project", nf.project["id"], "notes.meeting")
    assert push(NOTULEN, root, "--notulendir", rel)[1]["segment"] == "nataflow tidak berubah"
    NT.edit(root, rel, "Rilis dilakukan Jumat.", "Rilis dilakukan Kamis.")
    assert NT.nt(root, "final", "--notulendir", rel, "--answer", "Final")[0] == 0
    assert push(NOTULEN, root, "--notulendir", rel)[1]["segment"] == "nataflow diperbarui"
    assert len(nf.docs) == 1 and "Kamis" in nf.docs[0]["content"]


def test_notulen_kembar_gagal(notes_root, fake):
    f, nf = fake
    root, rel = notes_root
    for key in ("a", "b"):
        nf.add_doc("project", nf.project["id"], key, "notes.meeting", "x", {"source": "analyst", "notulen_key": rel})
    code, out = push(NOTULEN, root, "--notulendir", rel)
    assert code == 1 and out["segment"] == "nataflow GAGAL: 2 dokumen ber-notulen_key sama (a, b)" and f.writes() == []


def test_notulen_tanpa_key_wajib_setup(notes_root, fake):
    root, rel = notes_root
    (root / ".claude/nataflow.local.json").unlink()
    code, out = push(NOTULEN, root, "--notulendir", rel)
    assert code == 1 and "nataflow.local.json tidak ada" in out["segment"] and fake[0].requests == []
