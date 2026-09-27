"""Regresi 11 H1 — pagar `frontend:code-reviewer` menilai shell seperti bash, bukan seperti `shlex`."""
import json

import pytest

from conftest import PLUGINS, run_script

GUARD = PLUGINS / "frontend/hooks/guard_bash.py"


def hook(repo, cmd):
    data = {"cwd": str(repo), "tool_name": "Bash", "tool_input": {"command": cmd},
            "hook_event_name": "PreToolUse", "agent_type": "frontend:code-reviewer", "agent_id": "a1"}
    return run_script(GUARD, "hook", stdin=json.dumps(data))


@pytest.mark.regression("H1")
@pytest.mark.parametrize("cmd", ["git diff $'--output=/tmp/h1'", "git diff --{out,}put=/tmp/h1",
                                 "git log --format=$HOME", "git status 2>&1"])
def test_h1_fe_ekspansi_shell_ditolak(make_repo, cmd):
    r = hook(make_repo(), cmd)
    assert r.returncode == 2 and "DITOLAK" in r.stderr, (cmd, r.stderr)


@pytest.mark.regression("H1")
@pytest.mark.parametrize("cmd", ['git log -S "Map<K, V>" --oneline', "git show HEAD@{1} --stat"])
def test_h1_fe_kutip_berisi_operator_lolos(make_repo, cmd):
    assert hook(make_repo(), cmd).returncode == 0, cmd
