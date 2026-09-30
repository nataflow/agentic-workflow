"""Smoke: setiap skrip ber-CLI × 4 keadaan repo tanpa traceback, `--json` selalu JSON valid (L6.1).

Argumen minimum dipilih supaya skrip menempuh jalur normalnya sampai check pertama yang
gagal, bukan berhenti di argparse. Keadaan repo: ber-commit, tanpa commit, detached HEAD,
dan bukan repo git (E1–E3). Skrip dipanggil dengan cwd = repo sementara, persis seperti
skill memanggilnya.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import GIT_ENV, PLUGINS, git

BE_TD = "backenddev/docs/2609250000-smoke"
FE_TD = "frontenddev/docs/2609250000-smoke"
AN_TD = "analyst/tickets/2609250000-smoke"
HOOK_STDIN = "SESSION"  # diganti payload SessionStart ber-cwd repo
BASH_STDIN = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                         "tool_input": {"command": "ls"}})

# (path relatif src/plugins, argumen, stdout wajib JSON?, stdin)
CASES = [
    ("analyst/skills/_common/ticket.py", ["state", "--all", "--json"], True, None),
    ("analyst/skills/_common/ticket.py", ["sync-payload", "--ticketdir", AN_TD, "--json"], True, None),
    ("analyst/skills/_common/ticket.py", ["commit", "--ticketdir", AN_TD, "--stage", "draft"], False, None),
    ("analyst/skills/_common/validate_doc.py", ["--kind", "elicit", "--ticketdir", AN_TD, "--json"], True, None),

    ("nataflow/skills/create-artifact/scripts/artifact.py", ["config", "--json"], True, None),

    ("backend/hooks/detect.py", ["--plugin", "backend"], "hook", HOOK_STDIN),
    ("backend/hooks/guard_bash.py", ["hook"], "hook", BASH_STDIN),
    ("backend/skills/_common/validate_doc.py", ["--kind", "task", "--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/_common/sync_payload.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/_common/sync_payload.py", ["--repo-docs", "audit", "--json"], True, None),
    ("backend/skills/_common/run_verification.py", ["closing", "--taskdir", BE_TD, "--cmd", "test=true"], False, None),
    ("backend/skills/_common/verify_scope.py", ["--brief", f"{BE_TD}/brief-01.md", "--worktree"], False, None),
    ("backend/skills/analyst/scripts/chain_counters.py", ["--taskdir", BE_TD, "--check"], False, None),
    ("backend/skills/analyst/scripts/check_preconditions.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/architect/scripts/check_preconditions.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/architect/scripts/symbol_map.py", ["--sha", "HEAD", "--path", "README.txt"], False, None),
    ("backend/skills/audit/scripts/check_preconditions.py", ["--json"], True, None),
    ("backend/skills/business-analysis/scripts/check_preconditions.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/debug/scripts/check_preconditions.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/document-api/scripts/check_preconditions.py", ["--domain", "order", "--json"], True, None),
    ("backend/skills/plan/scripts/check_preconditions.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/plan/scripts/scaffold_brief.py", ["--taskdir", BE_TD, "--nn", "1"], False, None),
    ("backend/skills/plan/scripts/validate_briefs.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/profile/scripts/check_preconditions.py", ["--json"], True, None),
    ("backend/skills/profile/scripts/migrate_profile.py", ["--json"], True, None),
    ("backend/skills/report/scripts/check_preconditions.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/system-analysis/scripts/check_preconditions.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/task/scripts/check_preconditions.py", ["--taskdir", BE_TD, "--json"], True, None),
    ("backend/skills/tech-lead/scripts/check_preconditions.py", ["--json"], True, None),

    ("frontend/hooks/detect.py", ["--plugin", "frontend"], "hook", HOOK_STDIN),
    ("frontend/hooks/guard_bash.py", ["hook"], "hook", BASH_STDIN),
    ("frontend/skills/_common/chain.py", ["status", "--taskdir", FE_TD], False, None),
    ("frontend/skills/_common/review_round.py", ["status", "--taskdir", FE_TD, "--gate", "plan"], False, None),
    ("frontend/skills/_common/run_verification.py", ["closing", "--taskdir", FE_TD, "--cmd", "test=true"], False, None),
    ("frontend/skills/_common/sync_payload.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/_common/sync_payload.py", ["--repo-docs", "review", "--json"], True, None),
    ("frontend/skills/_common/validate_doc.py", ["--kind", "flow", "--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/_common/verify_scope.py", ["--brief", f"{FE_TD}/brief-01.md", "--worktree"], False, None),
    ("frontend/skills/architect/scripts/check_preconditions.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/architect/scripts/validate_review.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/contract/scripts/check_preconditions.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/lead/scripts/taskdir_state.py", ["--all", "--json"], True, None),
    ("frontend/skills/plan/scripts/check_preconditions.py", ["--taskdir", FE_TD, "--mode", "CONTRACT", "--json"], True, None),
    ("frontend/skills/plan/scripts/validate_briefs.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/profile/scripts/check_preconditions.py", ["--json"], True, None),
    ("frontend/skills/profile/scripts/migrate_profile.py", ["--json"], True, None),
    ("frontend/skills/report/scripts/check_preconditions.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/report/scripts/validate_report.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/review/scripts/check_preconditions.py", ["--target", "path", "--path", "src", "--json"], True, None),
    ("frontend/skills/review/scripts/validate_audit.py", ["--path", "frontenddev/reviews/2609250000-smoke.md"], False, None),
    ("frontend/skills/task/scripts/check_preconditions.py",
     ["--taskdir", FE_TD, "--lane", "FULL_PIPELINE", "--sections", "flow,ui", "--json"], True, None),
    ("frontend/skills/task/scripts/validate_task.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/ui-design/scripts/check_preconditions.py", ["--taskdir", FE_TD, "--json"], True, None),
    ("frontend/skills/ux-design/scripts/check_preconditions.py", ["--taskdir", FE_TD, "--json"], True, None),

    ("quickdev/skills/_common/plan_lock.py", ["status", "--plan", "plan/smoke.md", "--json"], True, None),
    ("quickdev/skills/_common/plan_lock.py", ["sync-payload", "--plan", "plan/smoke.md", "--json"], True, None),
    ("quickdev/skills/_common/plan_lock.py", ["sync-payload", "--repo-profile", "repo-profile.md", "--json"], True,
     None),
]

STATES = ["commit", "tanpa-commit", "detached", "bukan-git", "rusak"]

# Keadaan `rusak` (09 E1): tiap dokumen yang dibaca skrip ada, ter-commit, dan berisi byte non-UTF-8.
# Skrip wajib gagal dengan vonis terbaca, bukan traceback, dan `--json` tetap JSON.
NOT_UTF8 = b"\xff\xfe\x80 bukan utf-8 \xc3\x28\n"
CORRUPT = [f"{td}/{doc}" for td in (BE_TD, FE_TD) for doc in
           ("TASK.md", "brief-01.md", "REVIEW.md", "REPORT.md")] + [
    f"{BE_TD}/BRD.md", f"{BE_TD}/PRD.md", f"{BE_TD}/HALT.md", f"{BE_TD}/RCA.md",
    f"{FE_TD}/FLOW.md", f"{FE_TD}/UI.md", f"{FE_TD}/CONTRACT.md", f"{AN_TD}/TICKET.md", "analyst/nataflow.json",
    ".claude/nataflow.json",
    "frontenddev/reviews/2609250000-smoke.md", "plan/smoke.md", "repo-profile.md",
    ".claude/profile/backenddev/index.json", ".claude/profile/backenddev/commands.md",
    ".claude/profile/frontenddev/index.json", ".claude/profile/frontenddev/commands.md",
    "go.mod", "package.json", "Cargo.toml", "build.gradle", ".claude/workflow",
]


def _repo(tmp_path: Path, state: str) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    if state == "bukan-git":
        return root
    git(root, "init", "-q", "-b", "main")
    if state == "tanpa-commit":
        return root
    (root / "README.txt").write_text("fixture\n", encoding="utf-8")
    if state == "rusak":
        for rel in CORRUPT:
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_bytes(NOT_UTF8)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "chore: init")
    if state == "detached":
        git(root, "checkout", "-q", "--detach")
    return root


def _env(tmp_path: Path) -> dict:
    home = tmp_path / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "CLAUDE_"))}
    env.update(GIT_ENV, HOME=str(home), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    return env


def test_inventaris_lengkap():
    """Skrip ber-`__main__` baru wajib ditambahkan ke CASES."""
    listed = {rel for rel, *_ in CASES}
    found = {p.relative_to(PLUGINS).as_posix() for p in PLUGINS.rglob("*.py")
             if "__pycache__" not in p.parts and "__main__" in p.read_text(encoding="utf-8")}
    assert found == listed, {"belum di CASES": sorted(found - listed), "tidak ada": sorted(listed - found)}


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("rel,args,wants_json,stdin", CASES, ids=[c[0] for c in CASES])
def test_smoke(tmp_path, rel, args, wants_json, stdin, state):
    root = _repo(tmp_path, state)
    if stdin == HOOK_STDIN:
        stdin = json.dumps({"hook_event_name": "SessionStart", "source": "startup", "cwd": str(root)})
    proc = subprocess.run([sys.executable, str(PLUGINS / rel), *args], cwd=root, input=stdin or "",
                          capture_output=True, text=True, env=_env(tmp_path), timeout=60)
    out = proc.stdout + proc.stderr
    assert "Traceback (most recent call last)" not in out, out
    assert proc.returncode in (0, 1, 2), (proc.returncode, out)
    if wants_json is True:
        json.loads(proc.stdout)
    elif wants_json == "hook":
        assert proc.returncode == 0, out
        if proc.stdout.strip():
            json.loads(proc.stdout)
