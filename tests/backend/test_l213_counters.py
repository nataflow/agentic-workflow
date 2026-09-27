"""L2.13 — plafon loop analyst dimateraikan di `## Counters` `TASK.md` oleh `chain_counters.py`."""
from conftest import BE_SKILLS, TD, be_checks, run_script

SCRIPT = BE_SKILLS / "analyst/scripts/chain_counters.py"
TASK = ("---\nchain: PRD_BRIEF\nrisk: MAJOR\nstatus: ACTIVE\n---\n# Order\n\n## Chain\n\n"
        "- [ ] PRD — backend:system-analysis → PRD.md\n- [ ] BRIEF — backend:plan → brief-*.md\n\n"
        "## Success Criteria\n\n- [ ] **SC-1**: x\n\n## Out of Scope\n\n- y — z\n")


def _run(repo, *args):
    return run_script(SCRIPT, "--taskdir", str(repo / TD), *args)


def _task(repo, text=TASK):
    (repo / TD / "TASK.md").write_text(text, encoding="utf-8")
    return repo / TD / "TASK.md"


def test_bump_until_ceiling(chain_repo):
    task = _task(chain_repo)
    assert _run(chain_repo, "--bump", "reject:PRD").returncode == 0
    assert _run(chain_repo, "--bump", "reject:PRD").returncode == 0
    third = _run(chain_repo, "--bump", "reject:PRD")
    assert third.returncode == 1 and "3/2" in third.stdout
    assert "| reject:PRD | 2 | 2 |" in task.read_text()


def test_counters_survive_rewrite(chain_repo):
    task = _task(chain_repo)
    _run(chain_repo, "--bump", "reentry")
    _run(chain_repo, "--bump", "review_round:PRD")
    text = task.read_text()
    assert text.startswith(TASK)
    assert "| reentry | 1 | 2 |\n| review_round:PRD | 1 | 2 |" in text
    _run(chain_repo, "--bump", "reentry")
    assert task.read_text().startswith(TASK) and "| reentry | 2 | 2 |" in task.read_text()


def test_unknown_key_rejected(chain_repo):
    _task(chain_repo)
    assert _run(chain_repo, "--bump", "retries").returncode == 1
    assert _run(chain_repo, "--bump", "reject").returncode == 1          # kunci ber-hop tanpa hop
    assert _run(chain_repo, "--bump", "reentry:PRD").returncode == 1     # kunci taskdir ber-hop


def test_check_reports_over_ceiling(chain_repo):
    _task(chain_repo, TASK + "\n## Counters\n\n| Kunci | Nilai | Plafon |\n|---|---|---|\n| oq_return:BRD | 3 | 2 |\n")
    out = _run(chain_repo, "--check")
    assert out.returncode == 1 and "oq_return:BRD" in out.stdout


def test_reset_hop_clears_reopened_and_downstream(chain_repo):
    task = _task(chain_repo)
    for key in ("review_round:PRD", "review_round:PRD", "reject:BRIEF", "reentry"):
        _run(chain_repo, "--bump", key)
    assert _run(chain_repo, "--reset-hop", "PRD").returncode == 0
    text = task.read_text()
    assert "review_round:PRD" not in text and "reject:BRIEF" not in text and "| reentry | 1 | 2 |" in text


def test_analyst_check7_prints_counters(chain_repo):
    _task(chain_repo)
    _run(chain_repo, "--bump", "reentry")
    c7 = be_checks(chain_repo, "analyst/scripts/check_preconditions.py", "--taskdir", TD, "--risk", "MAJOR")[7]
    assert "Counters: reentry 1/2" in c7["summary"]
