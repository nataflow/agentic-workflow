"""Regresi 12 Tahap 1 sisi backend — `symbolic-ref` reviewer (J3), glob sebelum `--` (J8), dan prasyarat
profile pada workspace `.` (J5). Helper pagar identik dengan frontend (`tests/frontend/test_12_guard.py`)."""
import json

import pytest

from conftest import PLUGINS, be_run, commit, run_script

GUARD = PLUGINS / "backend/hooks/guard_bash.py"
REVIEWER = "backend:code-reviewer"


def hook(repo, cmd, agent=REVIEWER):
    data = {"cwd": str(repo), "tool_name": "Bash", "tool_input": {"command": cmd},
            "hook_event_name": "PreToolUse", "agent_type": agent, "agent_id": "a1"}
    return run_script(GUARD, "hook", stdin=json.dumps(data))


@pytest.fixture
def repo(make_repo):
    root = make_repo({"src/order.go": "package x\n"})
    commit(root, "init")
    return root


@pytest.mark.regression("J3")
@pytest.mark.parametrize("cmd", ["git symbolic-ref HEAD refs/heads/evil", "git symbolic-ref --delete HEAD",
                                 "git symbolic-ref --del refs/remotes/origin/HEAD", "git symbolic-ref -qd HEAD",
                                 "git symbolic-ref -m x HEAD refs/heads/y"])
def test_j3_be_symbolic_ref_tulis_ditolak(repo, cmd):
    r = hook(repo, cmd)
    assert r.returncode == 2 and "DITOLAK" in r.stderr, (cmd, r.stderr)


@pytest.mark.regression("J3")
@pytest.mark.parametrize("cmd", ["git symbolic-ref -q --short HEAD", "git symbolic-ref HEAD"])
def test_j3_be_symbolic_ref_baca_lolos(repo, cmd):
    assert hook(repo, cmd).returncode == 0, cmd


@pytest.mark.regression("J8")
@pytest.mark.parametrize("cmd, code", [("git diff HEAD *", 2), ("git log -1 -- src/*.go", 0),
                                       ('git log --grep "a*b" -1', 0)])
def test_j8_be_glob(repo, cmd, code):
    assert hook(repo, cmd).returncode == code, cmd


@pytest.mark.regression("J5")
def test_j5_be_profile_prasyarat_workspace_titik(make_repo):
    root = make_repo({"package.json": json.dumps({"workspaces": ["."]}),
                      "apps/api/package.json": json.dumps({"dependencies": {"express": "^4"}})})
    commit(root, "init")
    r = be_run(root, "profile/scripts/check_preconditions.py", "--json")
    assert "Traceback" not in r.stdout + r.stderr, r.stderr
    assert json.loads(r.stdout)
