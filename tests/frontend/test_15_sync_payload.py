"""15 F2, F9, F11–F13, F15 — `sync_payload.py` frontend: argumen tool MCP nataflow untuk taskdir dan dokumen repo.
Dokumen taskdir dibaca dari disk (24 K14), bukan dari blob `HEAD`."""
import json
import re

import pytest

from conftest import (FE_MINOR_TD, FE_SKILLS, FE_TD, commit, fe_approved_chain, fe_run, git, run_script,
                      write_files)

SP = FE_SKILLS / "_common" / "sync_payload.py"
WS = "11111111-2222-3333-4444-555555555555"
TICKET = "analyst/tickets/2609231400-cicilan-pembayaran"
CONFIG = {".claude/nataflow.json": json.dumps({"workspaces": {"utama": WS}, "repo": "tim/web"})}


def enable(repo):
    write_files(repo, CONFIG)
    commit(repo, "chore: aktifkan sinkron nataflow", ".claude/nataflow.json")
    return repo


@pytest.fixture
def repo(fe_chain_repo):
    return enable(fe_chain_repo)


def sp(repo, *args, stdin=""):
    r = run_script(SP, *args, "--json", cwd=repo, stdin=stdin)
    assert r.stdout.strip(), r.stderr
    return r.returncode, json.loads(r.stdout)


def push(repo, remote="[]", target=("--taskdir", FE_TD)):
    code, out = sp(repo, *target, "--remote", "-", stdin=remote)
    assert code == 0, out
    return out


def keys(out):
    return [d["key"] for d in out["documents"]]


def view(doc, **over):
    v = {"key": doc["key"], "type": doc["type"], "mimetype": "text/markdown",
         "content_sha256": doc["content_sha256"], "metadata": json.loads(doc["metadata"])}
    v.update(over)
    return v


def chain(repo, *args):
    r = fe_run(repo, "_common/chain.py", *args, "--taskdir", FE_TD)
    assert r.returncode == 0, r.out
    return r


@pytest.mark.regression("15 F15")
def test_skip_tanpa_config(fe_chain_repo):
    assert sp(fe_chain_repo, "--taskdir", FE_TD) == (0, {"status": "SKIP", "enabled": False})


def test_config_rusak_dan_taskdir_tidak_sah(repo):
    assert "bukan taskdir" in sp(repo, "--taskdir", "frontenddev/docs/../x")[1]["problems"][0]
    write_files(repo, {".claude/nataflow.json": "[]"})
    code, out = sp(repo, "--taskdir", FE_TD)
    assert code == 1 and "harus objek JSON" in out["problems"][0]


@pytest.mark.regression("15 F2")
def test_akar_saja_dan_draft_tidak_ikut(repo):
    code, out = sp(repo, "--taskdir", FE_TD)
    assert code == 0 and out["documents_total"] == 1
    key = f"frontenddev:tim/web:{FE_TD}"
    assert out["task"]["lookup"]["metadata"] == json.dumps({"source": "frontenddev", "workdir_key": key},
                                                           separators=(",", ":"))
    create = out["task"]["create"]
    assert create["title"] == "Orders — tombol lacak"
    assert create["description"].startswith("## Description") and "## Chain" not in create["description"]
    wd = out["workdir"]
    assert (wd["key"], wd["status"]) == (key, "active") and out["task"]["status"] is None
    meta = json.loads(wd["metadata"])
    assert meta["lane"] == "FAST_FORWARD" and meta["state"] == "GATE"
    assert keys(push(repo)) == ["TASK.md"], "CONTRACT DRAFT tidak ikut"


@pytest.mark.regression("15 F2")
def test_hop_disetujui_ikut(repo):
    fe_approved_chain(repo)
    out = push(repo)
    assert {"TASK.md", "CONTRACT.md", "brief-01-orders-lacak-button.md"} <= set(keys(out))
    contract = next(d for d in out["documents"] if d["key"] == "CONTRACT.md")
    assert json.loads(contract["metadata"])["status"] == "APPROVED" and contract["type"] == "contract"
    assert "REVIEW-PLAN.md" in keys(out) or not (repo / FE_TD / "REVIEW-PLAN.md").exists()


def test_brief_sebelum_approve_brief_tidak_ikut(repo):
    fe_approved_chain(repo)
    chain(repo, "reopen", "--row", "BRIEF", "--reason", "revisi brief")
    assert not [k for k in keys(push(repo)) if k.startswith("brief-")], "hop BRIEF [~] → brief READY ditahan"


@pytest.mark.regression("15 F2")
def test_drift_tidak_didorong_ulang(repo):
    fe_approved_chain(repo)
    first = push(repo)
    contract = next(d for d in first["documents"] if d["key"] == "CONTRACT.md")
    path = repo / FE_TD / "CONTRACT.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nsuntingan tanpa approve\n", encoding="utf-8")
    out = push(repo, json.dumps([view(contract)]))
    assert "CONTRACT.md" not in keys(out), "hop DRIFT: cermin tetap isi yang disetujui"


@pytest.mark.regression("15 F9")
def test_reopen_mendorong_status_terbaru(repo):
    fe_approved_chain(repo)
    contract = next(d for d in push(repo)["documents"] if d["key"] == "CONTRACT.md")
    chain(repo, "reopen", "--row", "CONTRACT", "--reason", "ubah endpoint")
    (doc,) = [d for d in push(repo, json.dumps([view(contract)]))["documents"] if d["key"] == "CONTRACT.md"]
    assert json.loads(doc["metadata"])["status"] == "DRAFT"


@pytest.mark.regression("15 F12")
def test_abandon_menjadi_abandoned_dan_cancelled(repo):
    chain(repo, "abandon", "--reason", "user berhenti")
    out = sp(repo, "--taskdir", FE_TD)[1]
    assert out["workdir"]["status"] == "abandoned"
    assert out["task"]["status"] == {"status": "cancelled", "from": ["todo", "in_progress"]}


@pytest.mark.regression("15 F12")
def test_rantai_tuntas_done(fe_minor_chain):
    repo = enable(fe_minor_chain)
    report = repo / FE_MINOR_TD / "REPORT.md"
    text = report.read_text(encoding="utf-8")
    report.unlink()
    out = sp(repo, "--taskdir", FE_MINOR_TD)[1]
    assert out["task"]["status"]["status"] == "in_progress", "unit DONE + REVIEW → eksekusi dimulai"
    assert "REPORT.md" not in keys(push(repo, target=("--taskdir", FE_MINOR_TD))), "REPORT belum ditulis"
    report.write_text(text, encoding="utf-8")
    out = sp(repo, "--taskdir", FE_MINOR_TD)[1]
    assert out["workdir"]["status"] == "done" and json.loads(out["workdir"]["metadata"])["state"] == "TUNTAS"
    assert out["task"]["status"]["status"] == "done"
    docs = push(repo, target=("--taskdir", FE_MINOR_TD))
    assert {"REPORT.md", "REVIEW.md", "report-01.md"} <= set(keys(docs))
    assert {d["type"] for d in docs["documents"] if d["key"] == "report-01.md"} == {"unit.report"}
    assert all(re.fullmatch(r"[a-z]+(\.[a-z]+)*", d["type"]) for d in docs["documents"]), "format type server (15 E11)"


def test_taskdir_bertiket(repo):
    path = repo / FE_TD / "TASK.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "status: ACTIVE\n", f"status: ACTIVE\nticket_source: {TICKET}/TICKET.md\n"), encoding="utf-8")
    out = sp(repo, "--taskdir", FE_TD)[1]
    assert out["task"]["lookup"]["metadata"] == json.dumps({"source": "analyst", "ticket_key": TICKET},
                                                           separators=(",", ":"))


@pytest.mark.regression("15 F13")
def test_dokumen_repo(repo):
    write_files(repo, {"frontenddev/reviews/2609250000-orders.md": "---\nverdict: WARNING\n---\n# audit\n"})
    commit(repo, "docs(review): audit orders", "frontenddev/reviews/2609250000-orders.md")
    docs = push(repo, target=("--repo-docs", "review"))["documents"]
    assert [(d["key"], d["type"]) for d in docs] == [("tim/web/frontenddev/reviews/2609250000-orders.md",
                                                      "adhoc.review")]
    assert json.loads(docs[0]["metadata"])["status"] == "WARNING"
    prof = push(repo, target=("--repo-docs", "profile"))["documents"]
    assert prof and {d["type"] for d in prof} == {"profile"}


def test_byte_stabil_dan_read_only(repo):
    before = git(repo, "status", "--porcelain")
    runs = {run_script(SP, "--taskdir", FE_TD, "--json", cwd=repo).stdout for _ in range(2)}
    assert len(runs) == 1 and git(repo, "status", "--porcelain") == before


@pytest.mark.regression("24 K14")
def test_dokumen_taskdir_dari_disk(repo):
    fe_approved_chain(repo)
    out = push(repo)
    contract = next(d for d in out["documents"] if d["key"] == "CONTRACT.md")
    assert contract["content"] == (repo / FE_TD / "CONTRACT.md").read_text(encoding="utf-8"), "isi disk apa adanya"
    meta = json.loads(contract["metadata"])
    assert meta["commit"] == "" and meta["head"] == git(repo, "rev-parse", "HEAD").strip()
    brief = next(d for d in out["documents"] if d["key"].startswith("brief-"))
    assert "sidik_kontrak: " in brief["content"], "brief yang dicerminkan sudah dikunci approve BRIEF"


@pytest.mark.regression("24 K14")
def test_akar_belum_terkunci_fail(repo):
    task = repo / FE_TD / "TASK.md"
    task.write_text(re_sub_base(task.read_text(encoding="utf-8")), encoding="utf-8")
    code, out = sp(repo, "--taskdir", FE_TD)
    assert code == 1 and "akar belum terkunci" in out["problems"][0]


def re_sub_base(text):
    return re.sub(r"^base_commit: .*\n", "", text, count=1, flags=re.M)


@pytest.mark.regression("24 G5")
def test_berkas_terhapus_tidak_didorong(repo):
    fe_approved_chain(repo)
    first = push(repo)
    plan = [d for d in first["documents"] if d["key"] == "REVIEW-PLAN.md"]
    assert plan, keys(first)
    (repo / FE_TD / "REVIEW-PLAN.md").unlink()
    out = push(repo, json.dumps([view(plan[0])]))
    assert "REVIEW-PLAN.md" not in keys(out), "berkas yang dihapus dibiarkan dengan isi terakhirnya di server"
