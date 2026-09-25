"""L2.8 — gerbang tech-lead: jalur baca-kode `--read-only` dan SKILL.md yang ramping."""
import json

from conftest import BE_SKILLS, be_profile, commit, git, run_hook, run_script, write_files

SCRIPT = BE_SKILLS / "tech-lead/scripts/check_preconditions.py"
GO = "module x\n\ngo 1.22\n"


def _repo(make_repo, profile=True):
    root = make_repo({"go.mod": GO, "src/order.go": "package order\nfunc Submit() {}\n"})
    git(root, "checkout", "-q", "-b", "main")
    if profile:
        be_profile(root, "go")
    commit(root, "base")
    return root


def _run(root, *args):
    proc = run_script(SCRIPT, "--json", "--root", str(root), *args)
    return proc.returncode, {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


def test_read_only_dirty_tree_passes(make_repo):
    root = _repo(make_repo)
    write_files(root, {"src/order.go": "package order\nfunc Submit() {}\n// wip\n"})
    code, checks = _run(root, "--read-only")
    assert code == 0 and "tidak dinilai" in checks[3]["summary"]


def test_read_only_detached_passes(make_repo):
    root = _repo(make_repo)
    git(root, "checkout", "-q", "--detach")
    code, checks = _run(root, "--read-only")
    assert code == 0 and checks[2]["summary"].startswith("HEAD detached")


def test_read_only_missing_commands_passes(make_repo):
    root = _repo(make_repo)
    git(root, "rm", "-q", ".claude/profile/backenddev/commands.md")
    commit(root, "rm commands")
    code, checks = _run(root, "--read-only")
    assert code == 0 and "tidak dinilai" in checks[5]["summary"]


def test_read_only_absent_profile_degraded(make_repo):
    root = _repo(make_repo, profile=False)
    code, checks = _run(root, "--read-only")
    assert code == 0 and "TERDEGRADASI" in checks[1]["summary"]
    assert _run(root)[0] == 1


def test_full_mode_still_fails_dirty(make_repo):
    root = _repo(make_repo)
    write_files(root, {"src/order.go": "package order\nfunc Submit() {}\n// wip\n"})
    code, checks = _run(root)
    assert code == 1 and checks[3]["status"] == "FAIL"


def test_detached_message_reachable(make_repo):
    root = _repo(make_repo)
    git(root, "checkout", "-q", "--detach")
    code, checks = _run(root)
    assert code == 1 and checks[2]["summary"] == "HEAD detached"


def test_skill_size_budget():
    assert len((BE_SKILLS / "tech-lead/SKILL.md").read_text(encoding="utf-8").encode()) <= 14000


def test_hook_mentions_read_only(make_repo):
    root = _repo(make_repo)
    _, payload = run_hook("backenddev", root)
    text = json.dumps(payload)
    assert "read-only" in text
