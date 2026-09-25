"""L3.4 Opsi B — implementor frontenddev tanpa Bash; scope unit divonis `verify_scope.py --worktree`."""
from conftest import PLUGINS, commit, git, run_script, write_files

SCOPE = PLUGINS / "frontenddev/skills/_common/verify_scope.py"
TDF = "frontenddev/docs/2609250900-cart"
BRIEF = f"{TDF}/brief-01-cart.md"


def _frontmatter(path):
    block = path.read_text(encoding="utf-8").split("---\n", 2)[1]
    return dict(l.split(": ", 1) for l in block.splitlines() if ": " in l)


def test_implementor_has_no_bash():
    fm = _frontmatter(PLUGINS / "frontenddev/agents/code-implementor.md")
    tools = [t.strip() for t in fm["tools"].split(",")]
    assert "Bash" not in tools and {"Grep", "Glob", "Read", "Edit", "Write"} <= set(tools)
    text = (PLUGINS / "frontenddev/agents/code-implementor.md").read_text(encoding="utf-8")
    assert "git restore --" not in text and "rm --" not in text


def test_verify_scope_copies_identical():
    be = PLUGINS / "backenddev/skills/_common/verify_scope.py"
    assert SCOPE.read_bytes() == be.read_bytes()


def test_matrix_uses_verify_scope():
    text = (PLUGINS / "frontenddev/skills/architect/references/execution-protocol.md").read_text(encoding="utf-8")
    assert "verify_scope.py --brief <brief_path> --worktree" in text


def test_verify_scope_worktree_files_touched(make_repo):
    repo = make_repo({".gitignore": ".explore/\n", "src/cart.ts": "export {}\n",
                      BRIEF: "---\nstatus: READY\nunit: \"01\"\nfiles_touched:\n  - src/cart.ts\n"
                             "  - src/cart.store.ts\nverification:\n  - pnpm test\n---\n# Brief\n"})
    commit(repo, "init")
    write_files(repo, {"src/cart.ts": "export const a = 1\n", "src/cart.store.ts": "export {}\n",
                       f"{TDF}/report-01.md": "# r\n", f"{TDF}/.explore/n.md": "x\n"})
    out = run_script(SCOPE, "--brief", BRIEF, "--worktree", cwd=repo)
    assert out.returncode == 0, out.stdout + out.stderr
    write_files(repo, {"src/other.ts": "export {}\n"})
    out = run_script(SCOPE, "--brief", BRIEF, "--worktree", cwd=repo)
    assert out.returncode == 1 and "src/other.ts" in out.stdout
    assert git(repo, "status", "--porcelain")
