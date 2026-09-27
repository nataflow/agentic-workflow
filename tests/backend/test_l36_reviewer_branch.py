"""L3.6 — commit laporan reviewer hanya di branch kerja; pesan dari `commit_convention`."""
from conftest import PLUGINS, TD, be_checks, git

ARCH = "architect/scripts/check_preconditions.py"


def _check4(repo):
    return be_checks(repo, ARCH, "--taskdir", TD)[4]


def test_feature_branch_passes(chain_repo):
    assert _check4(chain_repo)["status"] == "PASS"


def test_detached_head_fails(chain_repo):
    git(chain_repo, "checkout", "-q", "--detach")
    c = _check4(chain_repo)
    assert c["status"] == "FAIL" and "Detached HEAD" in c["summary"]


def test_base_branch_fails(chain_repo):
    git(chain_repo, "checkout", "-q", "main")
    c = _check4(chain_repo)
    assert c["status"] == "FAIL" and "`main`" in c["summary"]


def test_base_branch_arg_wins(chain_repo):
    git(chain_repo, "checkout", "-q", "-b", "dev")
    assert be_checks(chain_repo, ARCH, "--taskdir", TD, "--base-branch", "dev")[4]["status"] == "FAIL"


def test_reviewer_text():
    text = (PLUGINS / "backend/agents/code-reviewer.md").read_text(encoding="utf-8")
    assert "7 stop condition" in text and "git symbolic-ref -q --short HEAD" in text
    fase4 = text.split("## Fase 4", 1)[1].split("\n## ", 1)[0]
    assert "commit_convention" in fase4 and "--no-verify" in fase4
    disp = (PLUGINS / "backend/skills/architect/dispatcher/reviewer.md").read_text(encoding="utf-8")
    assert disp.count("commit_convention") >= 2
