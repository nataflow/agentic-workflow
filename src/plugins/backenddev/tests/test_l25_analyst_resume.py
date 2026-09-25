"""L2.5 — analyst melanjutkan taskdir ber-TASK.md tanpa memanggil `task` (check 7 Resume Point)."""
from conftest import TD, be_checks, commit, write_files

ANALYST = "analyst/scripts/check_preconditions.py"
TASK = "task/scripts/check_preconditions.py"
LEDGER = {
    "draft": "- [x] PRD — backenddev:system-analysis → PRD.md @ APPROVED a1b2c3d\n- [ ] BRIEF — backenddev:plan → brief-*.md\n",
    "reentry": ("- [x] PRD — backenddev:system-analysis → PRD.md @ APPROVED a1b2c3d\n"
                "- [~] BRIEF — backenddev:plan → brief-*.md @ re-entry 1 (was e4f5g6h)\n"),
    "full": ("- [x] PRD — backenddev:system-analysis → PRD.md @ APPROVED a1b2c3d\n"
             "- [x] BRIEF — backenddev:plan → brief-*.md @ READY e4f5g6h\n"),
}


def _task(repo, ledger):
    write_files(repo, {f"{TD}/TASK.md": ("---\nchain: PRD_BRIEF\nrisk: MAJOR\nstatus: ACTIVE\n---\n# Order split\n"
                                         f"## Success Criteria\n- [ ] **SC-1**: x\n## Chain\n{ledger}")})
    commit(repo, "docs(order-fix): kunci TASK")


def _resume(repo):
    return be_checks(repo, ANALYST, "--taskdir", TD, "--risk", "MAJOR", "--chain", "PRD_BRIEF")[7]


def test_resume_point_new_taskdir(chain_repo):
    (chain_repo / TD / "TASK.md").unlink()
    commit(chain_repo, "rm task")
    c7 = _resume(chain_repo)
    assert c7["status"] == "PASS" and "rantai baru" in c7["summary"]


def test_resume_point_draft_prd(chain_repo):
    ledger = "- [ ] PRD — backenddev:system-analysis → PRD.md\n- [ ] BRIEF — backenddev:plan → brief-*.md\n"
    _task(chain_repo, ledger)
    write_files(chain_repo, {f"{TD}/PRD.md": "---\nstatus: DRAFT\n---\n# PRD\n"})
    commit(chain_repo, "docs(spec): draft PRD order-fix")
    assert _resume(chain_repo)["summary"].startswith("Resume: hop PRD")


def test_resume_point_reentry_marker(chain_repo):
    _task(chain_repo, LEDGER["reentry"])
    assert _resume(chain_repo)["summary"].startswith("Resume: hop BRIEF")


def test_resume_point_full_ledger(chain_repo):
    _task(chain_repo, LEDGER["full"])
    assert "butuh reentry_reason" in _resume(chain_repo)["summary"]


def test_task_precondition_still_rejects_existing_task(chain_repo):
    _task(chain_repo, LEDGER["draft"])
    c3 = be_checks(chain_repo, TASK, "--taskdir", TD, "--lane", "PRD_CONVERSION", "--chain", "PRD_BRIEF")[3]
    assert c3["status"] == "FAIL" and "TASK.md sudah ada" in c3["summary"]
