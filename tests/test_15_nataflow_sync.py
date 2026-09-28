"""15 — pustaka sinkron nataflow bersama `skills/_common/nataflow_sync.py` (B1, F1, Q1, A2).

Salinan identik di keempat plugin, config `.claude/nataflow.json`, identitas repo, isi blob `HEAD`, dan diff
dokumen terhadap manifest remote `list_document include_content=false`.
"""
import hashlib
import json

import pytest

from conftest import PLUGINS, commit, git, load_module, write_files

COPIES = {p: PLUGINS / p / "skills/_common/nataflow_sync.py" for p in ("analyst", "backend", "frontend", "quickdev")}
WS = "11111111-2222-3333-4444-555555555555"


@pytest.fixture(scope="module")
def ns():
    return load_module(COPIES["backend"], "nataflow_sync_15")


@pytest.mark.regression("15 B1")
def test_salinan_identik_di_keempat_plugin():
    blobs = {p: path.read_bytes() for p, path in COPIES.items()}
    assert len(set(blobs.values())) == 1, "salinan nataflow_sync.py berbeda antarplugin"


def test_pustaka_bukan_cli():
    """Pustaka tanpa entri CLI: tidak masuk inventaris smoke dan tidak dipanggil skill langsung."""
    assert "__main__" not in COPIES["backend"].read_text(encoding="utf-8")


# ── Config ──────────────────────────────────────────────────────────────────

def test_config_absen_berarti_nonaktif(ns, tmp_path):
    assert ns.load_config(tmp_path) == (None, [])
    assert ns.load_config(tmp_path, "analyst/nataflow.json") == (None, [])


def test_config_sah_diisi_default(ns, tmp_path):
    write_files(tmp_path, {".claude/nataflow.json": json.dumps({"workspace_id": WS, "repo": "x/y"})})
    config, problems = ns.load_config(tmp_path)
    assert problems == []
    assert config == {"mcp_server": "nataflow-api", "workspace_id": WS, "pic_id": "", "repo": "x/y"}


@pytest.mark.parametrize("raw,needle", [
    ("{", "bukan JSON sah"),
    ("[]", "harus objek JSON"),
    ('{"workspace":"x"}', "kunci `workspace` tidak dikenal"),
    ('{"pic_id":"bukan-uuid"}', "bukan UUID"),
    ('{"mcp_server":1}', "harus string"),
    ('{"repo":"a b"}', "memuat spasi"),
])
def test_config_rusak_bukan_absen(ns, tmp_path, raw, needle):
    write_files(tmp_path, {".claude/nataflow.json": raw})
    config, problems = ns.load_config(tmp_path)
    assert config is None and len(problems) == 1
    assert problems[0].startswith(".claude/nataflow.json rusak — ") and needle in problems[0]


def test_config_bukan_utf8(ns, tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/nataflow.json").write_bytes(b"\xff\xfe{}")
    assert "bukan UTF-8" in ns.load_config(tmp_path)[1][0]


def test_config_lama_diterima_dan_konflik_ditolak(ns, tmp_path):
    legacy = "analyst/nataflow.json"
    write_files(tmp_path, {legacy: json.dumps({"workspace_id": WS})})
    assert ns.load_config(tmp_path, legacy)[0]["workspace_id"] == WS
    write_files(tmp_path, {".claude/nataflow.json": json.dumps({"workspace_id": WS, "mcp_server": "nataflow-api"})})
    assert ns.load_config(tmp_path, legacy)[1] == [], "isi efektif sama → bukan konflik"
    write_files(tmp_path, {".claude/nataflow.json": json.dumps({"mcp_server": "lain"})})
    config, problems = ns.load_config(tmp_path, legacy)
    assert config is None and "berbeda isi" in problems[0]
    write_files(tmp_path, {legacy: "{"})
    assert ns.load_config(tmp_path, legacy)[1][0].startswith("analyst/nataflow.json rusak — ")


# ── Identitas repo ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("url,want", [
    ("https://github.com/nataflow/nataflow-api.git", "github.com/nataflow/nataflow-api"),
    ("https://user:tok@GitHub.com/nataflow/nataflow-api", "github.com/nataflow/nataflow-api"),
    ("git@github.com:nataflow/nataflow-api.git", "github.com/nataflow/nataflow-api"),
    ("ssh://git@github.com:22/nataflow/nataflow-api.git/", "github.com/nataflow/nataflow-api"),
    ("/srv/git/app.git", "/srv/git/app"),
    ("file:///srv/git/app.git", "/srv/git/app"),
])
def test_normalize_remote(ns, url, want):
    assert ns.normalize_remote(url) == want


def test_repo_identity_urutan_sumber(ns, make_repo):
    root = make_repo(name="nama-dir")
    config = {"repo": ""}
    assert ns.repo_identity(root, config) == "nama-dir"
    git(root, "remote", "add", "origin", "git@example.com:tim/app.git")
    assert ns.repo_identity(root, config) == "example.com/tim/app"
    assert ns.repo_identity(root, {"repo": "tim/app"}) == "tim/app"


# ── Isi berkas ──────────────────────────────────────────────────────────────

def test_head_text_hanya_isi_ter_commit(ns, make_repo):
    root = make_repo({"td/A.md": "satu\r\n"})
    assert ns.head_text(root, "td/A.md") == (None, ""), "belum ter-commit → tidak didorong"
    sha = commit(root, "init")
    (root / "td/A.md").write_text("disunting\n", encoding="utf-8")
    assert ns.head_text(root, "td/A.md") == ("satu\r\n", ""), "isi HEAD, bukan working tree"
    assert ns.last_commit(root, "td/A.md").startswith(sha)
    (root / "td/B.md").write_bytes(b"\xff\n")
    commit(root, "b", "td/B.md")
    text, problem = ns.head_text(root, "td/B.md")
    assert text is None and "bukan UTF-8" in problem


def test_head_text_bukan_git(ns, tmp_path):
    (tmp_path / "A.md").write_text("x", encoding="utf-8")
    assert ns.head_text(tmp_path, "A.md") == (None, "")
    assert ns.last_commit(tmp_path, "A.md") == ""


def test_removed_text_versi_terakhir(ns, make_repo):
    root = make_repo({"td/HALT.md": "halt v1\n"})
    commit(root, "halt")
    write_files(root, {"td/HALT.md": "halt v2\n"})
    commit(root, "halt 2")
    git(root, "rm", "-q", "td/HALT.md")
    git(root, "commit", "-qm", "cabut halt")
    text, sha = ns.removed_text(root, "td/HALT.md")
    assert text == "halt v2\n" and sha == git(root, "rev-parse", "HEAD").strip()
    assert ns.removed_text(root, "td/tidak-pernah.md") == (None, "")


def test_frontmatter_dan_h1(ns):
    text = '---\nstatus: "APPROVED"\nrisk: MAJOR\n---\n\n# Judul Kerja\n\n## Seksi\n'
    assert ns.frontmatter_value(text, "status") == "APPROVED"
    assert ns.frontmatter_value(text, "lane") == ""
    assert ns.h1_title(text) == "Judul Kerja"
    assert ns.frontmatter_value("# tanpa frontmatter\nstatus: X\n", "status") == ""


# ── Argumen tool ────────────────────────────────────────────────────────────

def test_document_sha_sama_dengan_server(ns):
    content = "baris satu\r\nbaris dua — ünïcode\n"
    doc = ns.document("workdir", "TASK.md", "TASK", content, ns.doc_meta("backenddev", "r", "td/TASK.md", "ACTIVE", "abc"))
    assert doc["content_sha256"] == hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert doc["metadata"] == '{"source":"backenddev","repo":"r","path":"td/TASK.md","status":"ACTIVE","commit":"abc"}'
    assert "reference_id" not in doc and doc["reference_table"] == "workdir"


def test_doc_meta_removed_dan_commit_kosong(ns):
    meta = ns.doc_meta("quickdev", "r", "plan/a.md", removed=True)
    assert meta == {"source": "quickdev", "repo": "r", "path": "plan/a.md", "commit": "", "removed": True}


def test_task_args_repo_hanya_di_create(ns):
    config = {"mcp_server": "nataflow-api", "workspace_id": WS, "pic_id": "", "repo": ""}
    args = ns.task_args(config, {"source": "analyst", "ticket_key": "analyst/tickets/2609231400-x"}, "r", "T", "D")
    assert args["lookup"] == {"workspace_id": WS, "metadata": '{"source":"analyst","ticket_key":"analyst/tickets/2609231400-x"}'}
    assert list(args["create"]) == ["title", "description", "workspace_id", "metadata"]
    assert json.loads(args["create"]["metadata"])["repo"] == "r"


def test_task_status_tidak_pernah_turun(ns):
    assert ns.task_status("in_progress") == {"status": "in_progress", "from": ["todo"]}
    assert "done" not in ns.task_status("done")["from"]
    assert ns.task_status("") is None


def test_batas_server_diperiksa_lebih_dulu(ns):
    docs = [ns.document("workdir", "k" * 256, "T" * 51, "", {}), ns.document("workdir", "a", "T", "", {}),
            ns.document("workdir", "a", "T", "", {})]
    problems = ns.check_documents(docs)
    assert len(problems) == 3
    assert ns.workdir_problems("k" * 256, "n", "active") and ns.workdir_problems("k", "n", "selesai")
    assert ns.workdir_problems("k", "n", "blocked") == []


# ── Manifest remote ─────────────────────────────────────────────────────────

def _remote_view(doc, **over):
    view = {"id": "x", "reference_table": "workdir", "reference_id": "w", "key": doc["key"], "type": doc["type"],
            "mimetype": "text/markdown", "content_sha256": doc["content_sha256"].upper(),
            "metadata": json.loads(doc["metadata"]), "created_by_id": "u", "created_at": "t", "updated_at": "t"}
    view.update(over)
    return view


def test_split_remote_aturan_unchanged(ns):
    a = ns.document("workdir", "TASK.md", "TASK", "a", {"status": "ACTIVE"})
    b = ns.document("workdir", "PRD.md", "PRD", "b", {"status": "APPROVED"})
    c = ns.document("workdir", "brief-01-x.md", "BRIEF", "c", {"status": "READY"})
    d = ns.document("workdir", "REPORT.md", "REPORT", "d", {})
    remote_text = json.dumps([_remote_view(a), _remote_view(b, metadata={"status": "DRAFT"}),
                              _remote_view(c, type="LAIN"), {"key": None, "content_sha256": "x"}])
    remote, problems = ns.read_remote("-", remote_text)
    assert problems == [] and set(remote) == {"TASK.md", "PRD.md", "brief-01-x.md"}
    push, same = ns.split_remote([a, b, c, d], remote)
    assert [p["key"] for p in push] == ["PRD.md", "brief-01-x.md", "REPORT.md"] and same == 1


def test_remote_metadata_string_dan_bungkus(ns):
    a = ns.document("workdir", "TASK.md", "TASK", "a", {"status": "ACTIVE"})
    wrapped = json.dumps({"documents": [_remote_view(a, metadata=a["metadata"])]})
    remote, _ = ns.read_remote("-", wrapped)
    assert ns.split_remote([a], remote) == ([], 1)


@pytest.mark.parametrize("text,needle", [("", "kosong"), ("bukan json", "bukan JSON sah"),
                                          ('{"x":1}', "harus larik"), ("[1]", "bukan objek")])
def test_remote_rusak(ns, text, needle):
    remote, problems = ns.read_remote("-", text)
    assert remote is None and needle in problems[0]


def test_remote_dari_berkas(ns, tmp_path):
    (tmp_path / "r.json").write_text("[]", encoding="utf-8")
    assert ns.read_remote(str(tmp_path / "r.json"), "") == ({}, [])
