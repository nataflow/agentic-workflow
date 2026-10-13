"""Prasyarat frontend `plan`, `ui-design`, `review`, `task` — jalur normal dan tepi (L6.1)."""
import json

import pytest

from conftest import FE_TD, commit, fe_draft, fe_profile, fe_round, fe_run, git, write_files

NEW_TD = "frontenddev/docs/2609250000-orders-baru"


def checks(r) -> dict:
    data = json.loads(r.stdout)
    return {c["id"]: c["status"] for c in data["checks"]}


def contract_approved(repo) -> None:
    """Hop CONTRACT tercentang lewat jalur SKILL: ronde PASS → `chain.py draft` → approve."""
    fe_round(repo)
    r = fe_draft(repo)
    assert r.returncode == 0, r.out
    r = fe_run(repo, "_common/chain.py", "approve", "--taskdir", FE_TD, "--row", "CONTRACT", "--answer", "Setujui")
    assert r.returncode == 0, r.out


# --- plan ----------------------------------------------------------------------------------------

def plan(repo, mode, taskdir=FE_TD, cwd=None):
    return fe_run(cwd or repo, "plan/scripts/check_preconditions.py", "--taskdir", taskdir, "--mode", mode, "--json")


def test_plan_contract_sesudah_contract_disetujui_pass(fe_chain_repo):
    contract_approved(fe_chain_repo)
    r = plan(fe_chain_repo, "CONTRACT")
    assert r.returncode == 0, r.out
    assert set(checks(r).values()) == {"PASS"}


def test_plan_contract_sebelum_hop_contract_fail(fe_chain_repo):
    c = checks(plan(fe_chain_repo, "CONTRACT"))
    assert c[4] == "FAIL"                 # ledger: hop CONTRACT belum berangkat
    assert c[9] == "PASS"                 # draft CONTRACT.md diabaikan git (Langkah 24), tree bersih


def test_plan_mode_minor_ditolak_di_lane_fast_forward(fe_chain_repo):
    contract_approved(fe_chain_repo)
    assert checks(plan(fe_chain_repo, "MINOR"))[3] == "FAIL"


def test_plan_dari_subdirektori(fe_chain_repo):
    """E4."""
    contract_approved(fe_chain_repo)
    r = plan(fe_chain_repo, "CONTRACT", cwd=fe_chain_repo / "src" / "features" / "orders")
    assert r.returncode == 0, r.out


# --- ui-design -----------------------------------------------------------------------------------

def test_ui_design_sections_tanpa_ui_fail(fe_chain_repo):
    c = checks(fe_run(fe_chain_repo, "ui-design/scripts/check_preconditions.py", "--taskdir", FE_TD, "--json"))
    assert c[3] == "FAIL" and c[9] == "PASS"


def test_ui_design_taskdir_bukan_kanonik_fail(fe_chain_repo):
    c = checks(fe_run(fe_chain_repo, "ui-design/scripts/check_preconditions.py", "--taskdir", "src", "--json"))
    assert c[1] == "FAIL"


# --- review --------------------------------------------------------------------------------------

def review(repo, *args):
    return fe_run(repo, "review/scripts/check_preconditions.py", *args, "--json")


def test_review_target_path_pass(fe_chain_repo):
    r = review(fe_chain_repo, "--target", "path", "--path", "src/features/orders")
    assert r.returncode == 0, r.out


@pytest.mark.parametrize("args", [
    ("--target", "path", "--path", "src/tidak-ada"),                 # E8
    ("--target", "diff", "--range", "tidak-ada..HEAD"),
    ("--target", "taskdir", "--taskdir", FE_TD),                     # belum tuntas (REPORT.md absen)
])
def test_review_objek_tidak_tersedia_fail(fe_chain_repo, args):
    assert checks(review(fe_chain_repo, *args))[1] == "FAIL"


def test_review_diff_valid_pass(fe_chain_repo):
    write_files(fe_chain_repo, {"src/features/orders/OrderDetail.tsx": "export const x = 1\n"})
    commit(fe_chain_repo, "feat(orders-lacak): implement unit 01", "src/features/orders/OrderDetail.tsx")
    assert checks(review(fe_chain_repo, "--target", "diff", "--range", "HEAD~1..HEAD"))[1] == "PASS"


def test_review_path_berspasi(make_repo):
    """E5."""
    root = make_repo({"src/fitur baru/a.ts": "x\n"}, name="repo dengan spasi")
    fe_profile(root, "react-vite")
    assert checks(review(root, "--target", "path", "--path", "src/fitur baru"))[1] == "PASS"


# --- task ----------------------------------------------------------------------------------------

@pytest.fixture
def fresh_repo(make_repo):
    root = make_repo({"src/a.ts": "x\n"})
    git(root, "checkout", "-q", "-b", "main")
    fe_profile(root, "react-vite")
    commit(root, "chore: init")
    (root / NEW_TD).mkdir(parents=True)               # taskdir dibuat lead Phase 5, tidak pernah di-commit
    return root


def task(repo, lane, sections, taskdir=NEW_TD):
    return fe_run(repo, "task/scripts/check_preconditions.py", "--taskdir", taskdir, "--lane", lane,
                  "--sections", sections, "--json")


@pytest.mark.parametrize("lane,sections", [("FULL_PIPELINE", "flow,ui,architecture"),
                                           ("FAST_FORWARD", "architecture"),
                                           ("HOTFIX_MINOR", "")])
def test_task_pasangan_sah_pass(fresh_repo, lane, sections):
    r = task(fresh_repo, lane, sections)
    assert r.returncode == 0, r.out


@pytest.mark.parametrize("lane,sections", [("BOGUS", "ui"), ("HOTFIX_MINOR", "flow,ui")])
def test_task_pasangan_tidak_sah_fail(fresh_repo, lane, sections):
    assert checks(task(fresh_repo, lane, sections))[4] == "FAIL"


def test_task_md_sudah_ada_fail(fe_chain_repo):
    assert checks(task(fe_chain_repo, "FAST_FORWARD", "architecture", taskdir=FE_TD))[3] == "FAIL"


def test_task_bukan_repo_git_fail(make_repo):
    """E1."""
    root = make_repo({f"{NEW_TD}/.keep": ""}, git_init=False)
    fe_profile(root, "react-vite")
    r = task(root, "FAST_FORWARD", "architecture")
    assert r.returncode == 1 and json.loads(r.stdout)["status"] == "FAIL"


def test_task_working_tree_kotor_fail(fresh_repo):
    write_files(fresh_repo, {"src/a.ts": "y\n"})
    assert checks(task(fresh_repo, "FAST_FORWARD", "architecture"))[7] == "FAIL"


@pytest.mark.regression("24 G2")
def test_task_menulis_penanda_ignore(fresh_repo):
    r = task(fresh_repo, "FAST_FORWARD", "architecture")
    assert r.returncode == 0 and checks(r)[10] == "WARN", r.out            # 24 K2: tanpa `.claude/nataflow.json`
    assert "hanya tersimpan di disk" in r.stdout
    assert (fresh_repo / "frontenddev/docs/.gitignore").read_text(encoding="utf-8").rstrip().endswith("*")
    write_files(fresh_repo, {f"{NEW_TD}/TASK.md": "x\n"})
    assert git(fresh_repo, "status", "--porcelain") == ""
    write_files(fresh_repo, {".claude/nataflow.json": "{}\n"})
    commit(fresh_repo, "chore: aktifkan sinkron nataflow", ".claude/nataflow.json")
    assert checks(task(fresh_repo, "FAST_FORWARD", "architecture"))[10] == "PASS"


@pytest.mark.regression("24 G2")
def test_task_dokumen_ter_track_rute_migrasi(fresh_repo):
    write_files(fresh_repo, {"frontenddev/docs/2609010000-lama/TASK.md": "---\nstatus: ACTIVE\n---\n# Lama\n"})
    commit(fresh_repo, "docs: era git")
    r = task(fresh_repo, "FAST_FORWARD", "architecture")
    c = {x["id"]: x for x in json.loads(r.stdout)["checks"]}
    assert r.returncode == 1 and c[10]["status"] == "FAIL" and "MIGRASI" in c[10]["summary"], c[10]
    assert "docs_git.py migrate" in c[10]["action"]
