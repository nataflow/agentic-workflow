"""L3.4 — pagar mekanis `backenddev:code-implementor`: hook PreToolUse + lease, dan vonis scope mesin."""
import json

import pytest

from conftest import PLUGINS, TD, brief, commit, git, run_script, write_files

GUARD = PLUGINS / "backenddev/hooks/guard_bash.py"
SCOPE = PLUGINS / "backenddev/skills/_common/verify_scope.py"
FINDING = "backenddev/issues/2026-09-05-001-issues.md"
BODY = ("# Brief\n## File scope\n\n**Folder**\n\n| Path folder | Kenapa |\n|---|---|\n| `src/` | x |\n\n"
        "**File**\n\n| Aksi | Path | Anchor | Apa |\n|---|---|---|---|\n"
        "| modify | `src/order.go` | `Submit` | lock |\n| create | `src/lock.go` | — | baru |\n\n## Steps\n1. x\n")
BRIEF = f"{TD}/brief-01-lock.md"
IMPL = "backenddev:code-implementor"


@pytest.fixture
def repo(chain_repo):
    write_files(chain_repo, {FINDING: "# Temuan\n### P1-1\n", ".env.local": "SECRET=1\n"})
    (chain_repo / ".gitignore").write_text(".explore/\n.env.local\n")
    brief(chain_repo, "01", "lock", "READY", body=BODY, finding_source=FINDING)
    commit(chain_repo, "brief")
    return chain_repo


def lease(repo, *args):
    return run_script(GUARD, "lease", *args, cwd=repo)


def hook(repo, cmd=None, agent=IMPL, tool="Bash", file_path=None):
    ti = {"command": cmd} if tool == "Bash" else {"file_path": file_path, "content": "x"}
    data = {"cwd": str(repo), "tool_name": tool, "tool_input": ti, "hook_event_name": "PreToolUse"}
    if agent:
        data.update(agent_type=agent, agent_id="a1")
    return run_script(GUARD, "hook", stdin=json.dumps(data))


def test_hooks_json_registers_guard():
    d = json.loads((PLUGINS / "backenddev/hooks/hooks.json").read_text())
    entry = d["hooks"]["PreToolUse"][0]
    assert entry["matcher"] == "Bash|Edit|Write"
    assert "guard_bash.py" in entry["hooks"][0]["command"]
    assert "SessionStart" in d["hooks"]


def test_lease_lives_outside_worktree(repo):
    out = lease(repo, "--brief", BRIEF)
    assert out.returncode == 0, out.stderr
    assert git(repo, "status", "--porcelain") == ""
    lp = repo / ".git/agentic-workflow/lease-backenddev.json"
    allowed = json.loads(lp.read_text())["allowed"]
    assert {"src/order.go", "src/lock.go", BRIEF, f"{TD}/report-01.md", FINDING} == set(allowed)


def test_lease_empty_scope_refused(repo):
    brief(repo, "02", "kosong", "READY")
    assert lease(repo, "--brief", f"{TD}/brief-02-kosong.md").returncode == 2


@pytest.mark.parametrize("cmd,rc", [
    ("git status --porcelain", 0),
    ("git diff -U0 -- src/order.go", 0),
    (f"git add src/order.go {BRIEF}", 0),
    (f"git add -- src/lock.go {FINDING}", 0),
    ("git commit -m 'fix(order): implement lock'", 0),
    ("git add .", 2),
    ("git add -A", 2),
    ("git add src/*.go", 2),
    ("git add src/../.env.local", 2),
    ("git add -f .env.local", 2),
    ("git commit --amend -m x", 2),
    ("git commit --no-verify -m x", 2),
    ("git commit -a -m x", 2),
    ("git checkout -- .", 2),
    ("git restore src/order.go", 2),
    ("git clean -fd", 2),
    ("git stash", 2),
    ("git reset --hard", 2),
    ("git push", 2),
    ("git -C /tmp add x", 2),
    ("/usr/bin/git clean -fd", 2),
    ("git diff --output=../x", 2),
    ("rm -rf src", 2),
    ("cd src && git add order.go", 2),
    ("git status; rm -rf src", 2),
    ("git commit -m \"$(cat msg)\"", 2),
    ("git log | head", 2),
    ("php artisan migrate", 2),
    ("git commit -m 'tak seimbang", 2),
])
def test_bash_allowlist(repo, cmd, rc):
    lease(repo, "--brief", BRIEF)
    out = hook(repo, cmd)
    assert out.returncode == rc, (cmd, out.stderr)
    if rc == 2:
        assert "guard_bash: DITOLAK" in out.stderr


def test_edit_write_limited_to_lease(repo):
    lease(repo, "--brief", BRIEF)
    assert hook(repo, tool="Write", file_path=str(repo / "src/lock.go")).returncode == 0
    assert hook(repo, tool="Edit", file_path=str(repo / f"{TD}/report-01.md")).returncode == 0
    assert hook(repo, tool="Edit", file_path=str(repo / "src/other.go")).returncode == 2
    assert hook(repo, tool="Write", file_path=str(repo / ".env.local")).returncode == 2
    assert hook(repo, tool="Write", file_path="/etc/passwd").returncode == 2


@pytest.mark.parametrize("agent", [None, "backenddev:code-reviewer", "frontenddev:code-implementor", "Explore"])
def test_other_agents_pass_through(repo, agent):
    assert hook(repo, "git clean -fd", agent=agent).returncode == 0


def test_no_lease_fails_closed(repo):
    lease(repo, "--brief", BRIEF)
    assert lease(repo, "--clear").returncode == 0
    out = hook(repo, "git status --porcelain")
    assert out.returncode == 2 and "lease absen" in out.stderr


def test_garbage_input_is_not_blocking_for_unknown_agent(repo):
    assert run_script(GUARD, "hook", stdin="bukan json").returncode == 0


# --- verify_scope.py ---------------------------------------------------------------------------

def scope(repo, *args):
    return run_script(SCOPE, "--brief", BRIEF, *args, cwd=repo)


def test_scope_commit_pass_and_fail(repo):
    write_files(repo, {"src/order.go": "package order\n// lock\n", "src/lock.go": "package order\n"})
    ok = commit(repo, "fix(order): implement lock", "src/order.go", "src/lock.go")
    out = scope(repo, "--commit", ok)
    assert out.returncode == 0 and out.stdout.startswith("PASS"), out.stdout + out.stderr
    write_files(repo, {"src/other.go": "package order\n"})
    bad = commit(repo, "leak", "src/other.go")
    out = scope(repo, "--commit", bad)
    assert out.returncode == 1 and "src/other.go" in out.stdout


def test_scope_finding_source_only_fixed_marker(repo):
    (repo / FINDING).write_text("# Temuan\n### P1-1\n> Status: FIXED 2026-09-25 — lihat brief-01\n")
    ok = commit(repo, "fixed", FINDING)
    assert scope(repo, "--commit", ok).returncode == 0
    (repo / FINDING).write_text("# Temuan diubah\n### P1-1\n> Status: FIXED 2026-09-25 — lihat brief-01\n")
    bad = commit(repo, "edit", FINDING)
    assert scope(repo, "--commit", bad).returncode == 1


def test_scope_worktree_and_explore_ignored(repo):
    write_files(repo, {"src/order.go": "package order\n// x\n", f"{TD}/.explore/x.md": "x\n"})
    assert scope(repo, "--worktree").returncode == 0
    write_files(repo, {"src/leak/new.go": "package leak\n"})
    out = scope(repo, "--worktree")
    assert out.returncode == 1 and "src/leak/new.go" in out.stdout


def test_scope_bad_sha_is_usage_error(repo):
    assert scope(repo, "--commit", "deadbeef").returncode == 2


def test_architect_uses_lease_and_verify_scope():
    text = (PLUGINS / "backenddev/skills/architect/SKILL.md").read_text(encoding="utf-8")
    assert "guard_bash.py lease --brief" in text and "guard_bash.py lease --clear" in text
    assert "verify_scope.py --brief <brief_path> --commit <sha>" in text
    assert "git show --stat <sha>` dan bandingkan" not in text
    impl = (PLUGINS / "backenddev/agents/code-implementor.md").read_text(encoding="utf-8")
    for word in ("--amend", "--no-verify", "git clean", "git stash", "guard_bash.py"):
        assert word in impl
