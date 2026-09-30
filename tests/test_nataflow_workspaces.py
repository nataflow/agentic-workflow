"""`workspaces` di `.claude/nataflow.json`: beberapa workspace dalam satu project, dipilih saat sinkron.

Nol entri → workspace milik key, satu → otomatis, lebih dari satu → payload membawa `workspace_choices` dan `create`
tanpa `workspace_id` sampai skrip dijalankan ulang dengan `--workspace <alias>`. `lookup` task selalu menjangkau
seluruh project key, dan workdir tidak membawa `workspace_id` (model mengisinya dari task induk).
"""
import json
from pathlib import Path

import pytest

from conftest import BE_SKILLS, FE_SKILLS, FE_TD, PLUGINS, TD, commit, git, load_module, run_script, ticket_review, \
    write_files

WEB = "11111111-2222-3333-4444-555555555555"
MOBILE = "66666666-7777-4888-9999-aaaaaaaaaaaa"
TWO = {"workspaces": {"web": WEB, "mobile": MOBILE}}
CHOICES = [{"alias": "web", "workspace_id": WEB}, {"alias": "mobile", "workspace_id": MOBILE}]

TICKET = PLUGINS / "analyst" / "skills" / "_common" / "ticket.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "analyst" / "fixtures" / "ticket_valid.md"
PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"


@pytest.fixture(scope="module")
def ns():
    return load_module(PLUGINS / "backend" / "skills/_common/nataflow_sync.py", "nataflow_sync_ws")


def config(root, data):
    write_files(root, {".claude/nataflow.json": json.dumps(data)})


def run_json(script, root, *args):
    r = run_script(script, *args, "--json", cwd=root)
    assert "Traceback" not in r.stderr, r.stderr
    return r.returncode, json.loads(r.stdout)


# ── Pustaka ─────────────────────────────────────────────────────────────────

def test_choose_workspace_nol_satu_banyak(ns):
    base = {"mcp_server": "nataflow-api", "pic_id": "", "repo": ""}
    assert ns.choose_workspace(dict(base, workspaces={}), "") == ("", [], [])
    assert ns.choose_workspace(dict(base, workspaces={"web": WEB}), "") == (WEB, [], [])
    assert ns.choose_workspace(dict(base, workspaces=TWO["workspaces"]), "") == ("", CHOICES, [])
    assert ns.choose_workspace(dict(base, workspaces=TWO["workspaces"]), "mobile") == (MOBILE, [], [])


def test_alias_tidak_dikenal_ditolak(ns):
    base = {"mcp_server": "nataflow-api", "pic_id": "", "repo": ""}
    _, _, problems = ns.choose_workspace(dict(base, workspaces=TWO["workspaces"]), "desktop")
    assert "`desktop` tidak ada" in problems[0] and "web, mobile" in problems[0]
    _, _, problems = ns.choose_workspace(dict(base, workspaces={}), "web")
    assert "`workspaces` kosong" in problems[0]


def test_urutan_entri_config_dipertahankan(ns, tmp_path):
    write_files(tmp_path, {".claude/nataflow.json": '{"workspaces": {"zeta": "%s", "alfa": "%s"}}' % (WEB, MOBILE)})
    assert list(ns.load_config(tmp_path)[0]["workspaces"]) == ["zeta", "alfa"]


def test_workspace_id_lama_ditolak_dengan_petunjuk(ns, tmp_path):
    config(tmp_path, {"workspace_id": WEB})
    cfg, problems = ns.load_config(tmp_path)
    assert cfg is None and "`workspace_id` sudah diganti `workspaces`" in problems[0]


def test_workdir_tanpa_workspace(ns):
    assert "workspace_id" not in ns.workdir_args("k", "n", "active", {"source": "x"})


# ── analyst ─────────────────────────────────────────────────────────────────

@pytest.fixture
def ticket_repo(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    assert ticket_review(root, TDIR, "PASS").returncode == 0
    r = run_script(TICKET, "approve", "--ticketdir", TDIR, "--answer", "Setujui", cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr
    return root


def test_analyst_banyak_workspace_menunggu_pilihan(ticket_repo):
    config(ticket_repo, TWO)
    code, out = run_json(TICKET, ticket_repo, "sync-payload", "--ticketdir", TDIR)
    assert code == 0 and out["workspace_choices"] == CHOICES and out["workspace_id"] == ""
    assert "workspace_id" not in out["create"] and "workspace_id" not in out["lookup"]
    code, chosen = run_json(TICKET, ticket_repo, "sync-payload", "--ticketdir", TDIR, "--workspace", "mobile")
    assert code == 0 and chosen["create"]["workspace_id"] == MOBILE and "workspace_choices" not in chosen
    assert chosen["lookup"] == out["lookup"] and chosen["update"] == out["update"], "pilihan hanya mengubah create"


def test_analyst_satu_atau_nol_workspace_tanpa_pilihan(ticket_repo):
    config(ticket_repo, {"workspaces": {"web": WEB}})
    code, out = run_json(TICKET, ticket_repo, "sync-payload", "--ticketdir", TDIR)
    assert code == 0 and out["create"]["workspace_id"] == WEB and "workspace_choices" not in out
    config(ticket_repo, {})
    code, out = run_json(TICKET, ticket_repo, "sync-payload", "--ticketdir", TDIR)
    assert code == 0 and "workspace_id" not in out["create"] and "workspace_choices" not in out


def test_analyst_alias_salah_fail(ticket_repo):
    config(ticket_repo, TWO)
    code, out = run_json(TICKET, ticket_repo, "sync-payload", "--ticketdir", TDIR, "--workspace", "desktop")
    assert code == 1 and out["status"] == "FAIL" and "`desktop` tidak ada" in out["problems"][0]


def test_analyst_pembatalan_tidak_butuh_pilihan(ticket_repo):
    config(ticket_repo, TWO)
    r = run_script(TICKET, "cancel", "--ticketdir", TDIR, "--reason", "tidak jadi", "--force", cwd=ticket_repo)
    assert r.returncode == 0, r.stdout + r.stderr
    code, out = run_json(TICKET, ticket_repo, "sync-payload", "--ticketdir", TDIR)
    assert code == 0 and out["task_status"]["status"] == "cancelled" and "workspace_id" not in out["lookup"]


# ── backend / frontend ──────────────────────────────────────────────────────

@pytest.mark.parametrize("plugin", ["backend", "frontend"])
def test_engineer_task_dan_dokumen_repo_memilih_workspace(plugin, request):
    root = request.getfixturevalue("chain_repo" if plugin == "backend" else "fe_chain_repo")
    sp = (BE_SKILLS if plugin == "backend" else FE_SKILLS) / "_common" / "sync_payload.py"
    td = TD if plugin == "backend" else FE_TD
    config(root, TWO)
    commit(root, "chore: aktifkan sinkron nataflow", ".claude/nataflow.json")
    code, out = run_json(sp, root, "--taskdir", td)
    assert code == 0 and out["workspace_choices"] == CHOICES
    assert "workspace_id" not in out["task"]["create"] and "workspace_id" not in out["task"]["lookup"]
    assert "workspace_id" not in out["workdir"]
    code, out = run_json(sp, root, "--taskdir", td, "--workspace", "web")
    assert code == 0 and out["task"]["create"]["workspace_id"] == WEB and "workspace_choices" not in out
    code, out = run_json(sp, root, "--repo-docs", "profile")
    assert code == 0 and out["workspace_id"] == "" and out["workspace_choices"] == CHOICES
    code, out = run_json(sp, root, "--repo-docs", "profile", "--workspace", "mobile")
    assert code == 0 and out["workspace_id"] == MOBILE
    code, out = run_json(sp, root, "--repo-docs", "profile", "--workspace", "desktop")
    assert code == 1 and "`desktop` tidak ada" in out["problems"][0]


# ── quickdev ────────────────────────────────────────────────────────────────

def test_quickdev_profil_dan_rencana_memilih_workspace(make_repo):
    root = make_repo({"repo-profile.md": "# profil\n", ".claude/nataflow.json": json.dumps(TWO)})
    commit(root, "init")
    code, out = run_json(PL, root, "sync-payload", "--repo-profile", "repo-profile.md")
    assert code == 0 and out["workspace_choices"] == CHOICES and out["workspace_id"] == ""
    code, out = run_json(PL, root, "sync-payload", "--repo-profile", "repo-profile.md", "--workspace", "web")
    assert code == 0 and out["workspace_id"] == WEB and "workspace_choices" not in out
