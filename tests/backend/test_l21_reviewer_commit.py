"""L2.1 — `code-reviewer` meng-commit baris indeks `backenddev/issues/README.md`; `REVIEW.md` di disk (Langkah 24)."""
import re
import shlex

from conftest import PLUGINS, TD, be_checks, brief, commit, git, land, write_files

BE = PLUGINS / "backend"
REVIEWER = BE / "agents/code-reviewer.md"
DISPATCH = BE / "skills/architect/dispatcher/reviewer.md"
GATE_SCOPE = BE / "skills/tech-lead/references/gate-scope.md"
LIFECYCLE = BE / "skills/architect/references/lifecycle-recovery.md"


def _fase4_git_add() -> list:
    """Argumen `git add` dari baris Fase 4 butir 1 `code-reviewer.md`, taskdir terisi."""
    text = REVIEWER.read_text(encoding="utf-8")
    fase4 = text.split("## Fase 4", 1)[1].split("\n## ", 1)[0]
    line = next(l for l in fase4.splitlines() if l.startswith("1.") and "git add" in l)
    cmd = re.search(r"`(git add [^`]+)`", line).group(1).replace("{taskdir}", TD)
    return shlex.split(cmd)[2:]


def _review_session(repo, *paths):
    land(repo, brief(repo, "01", "lock", "READY"))
    write_files(repo, {f"{TD}/REVIEW.md": "---\nhighest: CLEAN\n---\n# Review\n",
                       "backenddev/issues/README.md":
                           "# Issues Index\n| Date | Issue ID | Target | Severity | Status |\n"})
    if paths:
        commit(repo, "docs(order-fix): add final review report", *paths)


def test_reviewer_staging_leaves_tree_clean(chain_repo):
    _review_session(chain_repo, *_fase4_git_add())
    assert git(chain_repo, "status", "--porcelain") == ""
    assert be_checks(chain_repo, "report/scripts/check_preconditions.py", "--taskdir", TD)[7]["status"] == "PASS"
    assert be_checks(chain_repo, "architect/scripts/check_preconditions.py", "--taskdir", TD)[4]["status"] == "PASS"


def test_staging_line_names_issue_index():
    assert "backenddev/issues/README.md" in _fase4_git_add()
    commit_item = DISPATCH.read_text(encoding="utf-8").split("- Commit:", 1)[1].split("\n- ", 1)[0]
    assert "backenddev/issues/README.md" in commit_item


def test_commit_matrix_owner_single():
    for path in (GATE_SCOPE, LIFECYCLE):
        row = next(l for l in path.read_text(encoding="utf-8").splitlines()
                   if l.startswith("| `{taskdir}/REVIEW.md`"))
        assert "backenddev/issues/README.md" in row and "code-reviewer" in row, path
    assert "catat ke `issues/README.md`" not in LIFECYCLE.read_text(encoding="utf-8")


def test_regression_indeks_tidak_di_commit_gagal(chain_repo):
    _review_session(chain_repo)                                   # REVIEW.md di disk, indeks tertinggal
    assert git(chain_repo, "status", "--porcelain", "-uall").strip() == "?? backenddev/issues/README.md"
    assert be_checks(chain_repo, "report/scripts/check_preconditions.py", "--taskdir", TD)[7]["status"] == "FAIL"
