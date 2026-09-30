"""Regresi Langkah 14 (N1, N2, N5) — sinkron tiket analyst ke nataflow.

Fixture `fixtures/ticket_valid.md` = TICKET.md DRAFT sah: elisitasi CLOSED dan tersegel, belum direview.
Tiket READY dibentuk lewat jalur `analyst:spec`: review bersidik, lalu `approve`.
"""
import json
from pathlib import Path

import pytest

from conftest import PLUGINS, git, load_module, run_script, ticket_review

COMMON = PLUGINS / "analyst" / "skills" / "_common"
TICKET = COMMON / "ticket.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
TITLE = "Admin Finance dapat mencatat pembayaran invoice korporat secara cicilan"
WS = "a3e1d6c4-1f2b-4c3d-9e8f-7a6b5c4d3e2f"
PIC = "c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f"
# `repo` (15 A3) hanya di metadata create/update, sesudah `ticket_key`; `lookup` tetap dua kunci langkah 14.
META_KEYS = ["source", "ticket_key", "repo", "slug", "type", "priority", "approved", "approved_seal", "reopened"]
lib = load_module(COMMON / "analyst_lib.py", "analyst_lib_14")


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    return root


def tk(root, *args):
    return run_script(TICKET, *args, cwd=root)


def approve(root, ticketdir=TDIR):
    assert ticket_review(root, ticketdir, "PASS").returncode == 0
    r = tk(root, "approve", "--ticketdir", ticketdir, "--answer", "Setujui")
    assert r.returncode == 0, r.stdout + r.stderr


def config(root, data):
    path = root / "analyst" / "nataflow.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def payload(root, ticketdir=TDIR):
    r = tk(root, "sync-payload", "--ticketdir", ticketdir, "--json")
    assert "Traceback" not in r.stderr, r.stderr
    return r.returncode, json.loads(r.stdout)


def edit(root, old, new, ticketdir=TDIR):
    p = root / ticketdir / "TICKET.md"
    body = p.read_text(encoding="utf-8")
    assert old in body, old
    p.write_text(body.replace(old, new, 1), encoding="utf-8")


# --- N1: config sinkron ------------------------------------------------------------------------

@pytest.mark.regression("N1")
def test_config_absen_berarti_tidak_aktif(tmp_path):
    assert lib.load_sync_config(tmp_path) == (None, [])


@pytest.mark.regression("N1")
@pytest.mark.parametrize("raw,needle", [
    ("{", "bukan JSON"),
    ("[]", "harus objek"),
    ('{"server": "nataflow-api"}', "`server` tidak dikenal"),
    ('{"workspace_id": "%s"}' % WS, "`workspace_id` sudah diganti `workspaces`"),
    ('{"workspaces": "ws-1"}', "`workspaces` harus objek"),
    ('{"workspaces": {"web": 5}}', "`workspaces.web` harus string"),
    ('{"workspaces": {"web": "ws-1"}}', "`workspaces.web` `ws-1` bukan UUID"),
    ('{"workspaces": {"web app": "%s"}}' % WS, "alias workspace `web app`"),
    ('{"workspaces": {"a": "%s", "b": "%s"}}' % (WS, WS), "`workspaces.b` mengulang UUID"),
    ('{"pic_id": "bukan-uuid"}', "`pic_id` `bukan-uuid` bukan UUID"),
    (b'{"mcp_server": "\xff"}', "bukan UTF-8"),
])
def test_config_rusak_terlapor(tmp_path, raw, needle):
    config(tmp_path, raw)
    cfg, problems = lib.load_sync_config(tmp_path)
    assert cfg is None and any(needle in p for p in problems), problems


@pytest.mark.regression("N1")
def test_config_default_dan_nilai_eksplisit(tmp_path):
    config(tmp_path, {})
    assert lib.load_sync_config(tmp_path) == (
        {"mcp_server": "nataflow-api", "workspaces": {}, "pic_id": "", "repo": ""}, [])
    config(tmp_path, {"mcp_server": "nataflow-staging", "workspaces": {"utama": WS}, "pic_id": PIC})
    assert lib.load_sync_config(tmp_path) == (
        {"mcp_server": "nataflow-staging", "workspaces": {"utama": WS}, "pic_id": PIC, "repo": ""}, [])


# --- N2: sync-payload --------------------------------------------------------------------------

@pytest.mark.regression("N2")
def test_skip_tanpa_config(repo):
    approve(repo)
    assert payload(repo) == (0, {"status": "SKIP", "enabled": False})
    r = tk(repo, "sync-payload", "--ticketdir", TDIR)
    assert r.returncode == 0 and r.stdout.startswith("SYNC-PAYLOAD SKIP"), r.stdout


@pytest.mark.regression("N2")
def test_config_rusak_fail_keras(repo):
    approve(repo)
    config(repo, "{")
    code, out = payload(repo)
    assert code == 1 and out["status"] == "FAIL", out
    assert "analyst/nataflow.json rusak" in out["problems"][0]


@pytest.mark.regression("N2")
@pytest.mark.parametrize("keadaan", ["DRAFT", "DRIFT", "DIBATALKAN", "KOSONG", "RUSAK", "BUKAN_TICKETDIR"])
def test_bukan_ready_ditolak(repo, keadaan):
    config(repo, {})
    ticketdir = TDIR
    if keadaan == "DRIFT":
        approve(repo)
        edit(repo, "sering dibayar bertahap", "kerap dibayar bertahap")
    elif keadaan == "DIBATALKAN":
        assert tk(repo, "cancel", "--ticketdir", TDIR, "--reason", "batal").returncode == 0
    elif keadaan == "KOSONG":
        ticketdir = "analyst/tickets/2609231500-kosong"
        (repo / ticketdir).mkdir(parents=True)
    elif keadaan == "RUSAK":
        (repo / TDIR / "TICKET.md").write_bytes(b"\xff\xfe bukan utf-8\n")
    elif keadaan == "BUKAN_TICKETDIR":
        ticketdir = "analyst/tickets/cicilan"
    code, out = payload(repo, ticketdir)
    assert code == 1 and out["status"] == "FAIL", out
    if keadaan != "BUKAN_TICKETDIR":
        assert f" {keadaan} — hanya tiket READY" in out["problems"][0], out


@pytest.mark.regression("N2")
def test_pass_isi_payload_dari_kartu(repo):
    config(repo, {"workspaces": {"utama": WS}, "pic_id": PIC})
    approve(repo)
    code, out = payload(repo)
    assert code == 0 and out["status"] == "PASS" and out["enabled"] is True, out
    assert out["mcp_server"] == "nataflow-api" and out["ticket_key"] == TDIR

    text = (repo / TDIR / "TICKET.md").read_text(encoding="utf-8")
    fm, body = lib.split_frontmatter(text)
    card = lib.split_parts(body)[0].strip()
    create = out["create"]
    assert list(create) == ["title", "description", "workspace_id", "pic_id", "metadata"]
    assert create["title"] == TITLE
    assert create["description"] == card and create["description"].startswith(f"# {TITLE}\n")
    assert "Catatan Elisitasi" not in create["description"] and "Permintaan Asli" not in create["description"]
    assert (create["workspace_id"], create["pic_id"]) == (WS, PIC)

    meta = json.loads(create["metadata"])
    assert list(meta) == META_KEYS
    assert meta["source"] == "analyst" and meta["ticket_key"] == TDIR and meta["slug"] == "cicilan"
    assert (meta["type"], meta["priority"], meta["reopened"]) == ("FEATURE", "HIGH", 0)
    assert meta["approved"] == fm["approved"] and meta["approved_seal"] == fm["approved_seal"]
    assert create["metadata"] == json.dumps(meta, separators=(",", ":"), ensure_ascii=False)

    assert out["lookup"] == {"metadata": json.dumps(
        {"source": "analyst", "ticket_key": TDIR}, separators=(",", ":"))}
    assert out["update"] == {"title": TITLE, "description": card, "metadata": create["metadata"]}
    assert "status" not in create and "status" not in out["update"]

    again = tk(repo, "sync-payload", "--ticketdir", TDIR, "--json").stdout
    assert again == tk(repo, "sync-payload", "--ticketdir", TDIR, "--json").stdout


@pytest.mark.regression("N2")
def test_external_ref_hanya_bila_diisi_dan_scope_opsional(repo):
    config(repo, {})
    approve(repo)
    _, out = payload(repo)
    assert "external_ref" not in json.loads(out["create"]["metadata"])
    assert list(out["lookup"]) == ["metadata"] and list(out["create"]) == ["title", "description", "metadata"]
    assert tk(repo, "ref", "--ticketdir", TDIR, "--ref", "PROJ-12").returncode == 0
    code, out = payload(repo)
    assert code == 0 and json.loads(out["create"]["metadata"])["external_ref"] == "PROJ-12", out


# --- N5: idempotensi lintas reopen -------------------------------------------------------------

@pytest.mark.regression("N5")
def test_ticket_key_stabil_lintas_reopen(repo):
    config(repo, {})
    approve(repo)
    _, first = payload(repo)
    assert tk(repo, "reopen", "--ticketdir", TDIR, "--reason", "ubah latar belakang").returncode == 0
    edit(repo, "sering dibayar bertahap", "kerap dibayar bertahap")
    approve(repo)
    _, second = payload(repo)
    assert second["ticket_key"] == first["ticket_key"] == TDIR
    assert second["lookup"] == first["lookup"]
    m1, m2 = json.loads(first["create"]["metadata"]), json.loads(second["create"]["metadata"])
    assert m1["approved_seal"] != m2["approved_seal"]
    assert (m1["reopened"], m2["reopened"]) == (0, 1)
    assert "kerap dibayar bertahap" in second["update"]["description"]


@pytest.mark.regression("N5")
def test_tiket_baru_slug_sama_ticket_key_berbeda(repo):
    config(repo, {})
    approve(repo)
    _, old = payload(repo)
    r = tk(repo, "new", "--slug", "cicilan", "--type", "FEATURE", "--requester", "Rina",
           "--request", "Cicilan untuk pelanggan retail juga.")
    assert r.returncode == 0, r.stdout + r.stderr
    new_td = r.stdout.split("NEW PASS: ", 1)[1].split(" · ", 1)[0]
    assert new_td != TDIR and new_td.endswith("-cicilan")
    (repo / new_td / "TICKET.md").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "docs(ticket): tiket kedua")
    approve(repo, new_td)
    _, new = payload(repo, new_td)
    assert new["ticket_key"] == new_td and new["lookup"] != old["lookup"]
    assert json.loads(new["create"]["metadata"])["slug"] == json.loads(old["create"]["metadata"])["slug"]
