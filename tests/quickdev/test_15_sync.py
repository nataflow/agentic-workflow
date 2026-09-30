"""15 Q2, Q10, Q11, Q13 — `plan_lock.py sync-payload`: argumen tool MCP nataflow untuk rencana dan profil quickdev."""
import json

import pytest

from conftest import PLUGINS, commit, git, run_script, write_files

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
WS = "11111111-2222-3333-4444-555555555555"
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
    root = make_repo({"app.js": "a\n", "repo-profile.md": "# profil\n",
                      ".claude/nataflow.json": json.dumps({"workspaces": {"utama": WS}, "repo": "tim/app"})})
    commit(root, "init")
    write_files(root, {"plan/t.md": PLAN})
    return root


def pl(repo, *args, stdin=""):
    return run_script(PL, *args, cwd=repo, stdin=stdin)


def payload(repo, *args, stdin=""):
    r = pl(repo, "sync-payload", *args, "--json", stdin=stdin)
    return r.returncode, json.loads(r.stdout)


def locked(repo):
    assert pl(repo, "lock", "--plan", "plan/t.md", "--answer", "setuju").returncode == 0


@pytest.mark.regression("15 Q2")
def test_skip_tanpa_config_walau_rencana_tidak_ada(make_repo):
    root = make_repo()
    assert payload(root, "--plan", "plan/tidak-ada.md") == (0, {"status": "SKIP", "enabled": False})
    assert pl(root, "sync-payload", "--plan", "x.md").stdout.startswith("SYNC-PAYLOAD SKIP")


def test_config_rusak_fail(repo):
    write_files(repo, {".claude/nataflow.json": '{"workspaces": {"utama": "x"}}'})
    code, out = payload(repo, "--plan", "plan/t.md")
    assert code == 1 and out["status"] == "FAIL" and "bukan UUID" in out["problems"][0]


@pytest.mark.regression("15 Q13")
def test_rencana_draft_ditolak(repo):
    code, out = payload(repo, "--plan", "plan/t.md")
    assert code == 1 and "belum pernah dikunci" in out["problems"][0]


def test_rencana_tidak_ada_dan_bukan_utf8(repo):
    assert "tidak ada" in payload(repo, "--plan", "plan/x.md")[1]["problems"][0]
    (repo / "plan" / "t.md").write_bytes(b"\xff\n")
    assert "bukan UTF-8" in payload(repo, "--plan", "plan/t.md")[1]["problems"][0]


@pytest.mark.regression("15 Q2")
def test_fase_satu_tanpa_isi(repo):
    locked(repo)
    code, out = payload(repo, "--plan", "plan/t.md")
    assert code == 0 and out["status"] == "PASS" and out["mcp_server"] == "nataflow-api"
    key = "quickdev:tim/app:plan/t.md"
    assert out["task"]["lookup"] == {"metadata": json.dumps(
        {"source": "quickdev", "workdir_key": key}, separators=(",", ":"))}
    create = out["task"]["create"]
    assert create["title"] == "Implementation Plan — t"
    assert create["description"].startswith("## 1. Overview & Objectives\nTambah validasi kuota.")
    assert "## 3." not in create["description"]
    assert out["task"]["status"] is None, "belum dieksekusi → status task tidak disentuh"
    wd = out["workdir"]
    assert (wd["key"], wd["name"], wd["status"]) == (key, "t", "active") and "workspace_id" not in wd
    assert out["workspace_id"] == WS and out["task"]["create"]["workspace_id"] == WS
    meta = json.loads(wd["metadata"])
    assert meta["plan_status"] == "APPROVED" and meta["plan_hash"].startswith("sha256:")
    assert out["list_document"] == {"reference_table": "workdir", "include_content": False}
    assert out["documents_total"] == 1 and "documents" not in out
    assert '"content":' not in json.dumps(out) and "Tambah validasi kuota" in out["task"]["create"]["description"]


def test_fase_dua_isi_disk_dan_diff(repo):
    locked(repo)
    code, out = payload(repo, "--plan", "plan/t.md", "--remote", "-", stdin="[]")
    assert code == 0 and out["same"] == 0
    (doc,) = out["documents"]
    disk = (repo / "plan" / "t.md").read_text(encoding="utf-8")
    assert doc["content"] == disk and doc["key"] == "t.md" and doc["type"] == "quickdev.plan"
    assert doc["reference_table"] == "workdir" and "reference_id" not in doc
    meta = json.loads(doc["metadata"])
    assert (meta["status"], meta["commit"], meta["path"]) == ("APPROVED", "", "plan/t.md"), "belum ter-commit"
    remote = [{"key": "t.md", "type": "quickdev.plan", "mimetype": "text/markdown",
               "content_sha256": doc["content_sha256"], "metadata": meta}]
    code, out = payload(repo, "--plan", "plan/t.md", "--remote", "-", stdin=json.dumps(remote))
    assert out["documents"] == [] and out["same"] == 1


@pytest.mark.regression("15 Q10")
@pytest.mark.parametrize("close,wd_status,task_status", [
    ("COMPLETED", "done", "done"), ("BLOCKED", "blocked", "in_progress"),
    ("VERIFICATION_MANUAL_REQUIRED", "active", "in_progress")])
def test_status_dari_blok_eksekusi(repo, close, wd_status, task_status):
    locked(repo)
    assert pl(repo, "start", "--plan", "plan/t.md").returncode == 0
    if close != "BLOCKED":
        (repo / "plan" / "t.md").write_text(
            (repo / "plan" / "t.md").read_text(encoding="utf-8").replace("- [ ] 1.", "- [x] 1."), encoding="utf-8")
    args = ["--blocked-step", "1"] if close == "BLOCKED" else []
    assert pl(repo, "close", "--plan", "plan/t.md", "--status", close, "--verification", "ok", *args).returncode == 0
    out = payload(repo, "--plan", "plan/t.md")[1]
    assert out["workdir"]["status"] == wd_status
    assert out["task"]["status"]["status"] == task_status
    assert json.loads(out["workdir"]["metadata"])["execution"] == close


def test_unlock_tetap_tercermin_sebagai_draft(repo):
    locked(repo)
    assert pl(repo, "unlock", "--plan", "plan/t.md", "--reason", "revisi").returncode == 0
    out = payload(repo, "--plan", "plan/t.md", "--remote", "-", stdin="[]")[1]
    assert json.loads(out["documents"][0]["metadata"])["status"] == "DRAFT"


def test_byte_stabil_dan_tidak_menulis(repo):
    locked(repo)
    before = (repo / "plan" / "t.md").read_bytes()
    runs = {pl(repo, "sync-payload", "--plan", "plan/t.md", "--json").stdout for _ in range(2)}
    assert len(runs) == 1
    assert (repo / "plan" / "t.md").read_bytes() == before
    assert git(repo, "status", "--porcelain") == "?? plan/\n"


def test_commit_terisi_bila_rencana_ter_commit(repo):
    locked(repo)
    sha = commit(repo, "docs: rencana", "plan/t.md")
    doc = payload(repo, "--plan", "plan/t.md", "--remote", "-", stdin="[]")[1]["documents"][0]
    assert json.loads(doc["metadata"])["commit"].startswith(sha)


@pytest.mark.regression("15 Q11")
def test_profil_ke_workspace(repo):
    code, out = payload(repo, "--repo-profile", "repo-profile.md")
    assert code == 0 and out["workspace_id"] == WS
    assert out["list_document"]["reference_table"] == "workspace"
    assert json.loads(out["list_document"]["metadata"]) == {"source": "quickdev", "repo": "tim/app"}
    (doc,) = payload(repo, "--repo-profile", "repo-profile.md", "--remote", "-", stdin="[]")[1]["documents"]
    assert (doc["reference_table"], doc["key"], doc["type"]) == ("workspace", "tim/app/repo-profile.md", "profile")
    assert doc["content"] == "# profil\n"


def test_remote_rusak_dan_path_di_luar_root(repo, tmp_path):
    locked(repo)
    code, out = payload(repo, "--plan", "plan/t.md", "--remote", "-", stdin="bukan json")
    assert code == 1 and "bukan JSON sah" in out["problems"][0]
    outside = tmp_path / "luar.md"
    outside.write_text("x", encoding="utf-8")
    assert "di luar root" in payload(repo, "--plan", str(outside))[1]["problems"][0]


def test_subperintah_lama_tidak_berubah(repo):
    r = pl(repo, "status", "--plan", "plan/t.md", "--json")
    assert r.returncode == 0 and json.loads(r.stdout)["status"] == "DRAFT"
    assert "FAIL" in pl(repo, "verify", "--plan", "plan/x.md").stderr
