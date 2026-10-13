"""L2.6 — penanda `> Status: FIXED` di berkas temuan di-stage implementor dan lolos pemeriksa scope."""
import json
import re

from conftest import BE_SKILLS, PLUGINS, TD, be_run, brief, commit, git, write_files, load_module

bs = load_module(BE_SKILLS / "_common" / "brief_status.py", "be_brief_status")

FINDING = "backenddev/issues/2026-09-05-001-issues.md"


def _repo(chain_repo):
    write_files(chain_repo, {FINDING: "# Temuan\n### P1-1 stok negatif\n- file: src/order.go:1\n"})
    brief(chain_repo, "01", "guard", "READY", finding_source=FINDING)
    commit(chain_repo, "base")
    return chain_repo


def test_implementor_staging_includes_finding_source(chain_repo):
    repo = _repo(chain_repo)
    text = (PLUGINS / "backend/agents/code-implementor.md").read_text(encoding="utf-8")
    assert "berkas `finding_source` (hanya bila baru ditandai)" in text
    write_files(repo, {"src/order.go": "package order\n// guard\n"})
    (repo / FINDING).write_text((repo / FINDING).read_text().replace(
        "### P1-1 stok negatif\n", "### P1-1 stok negatif\n> Status: FIXED 2026-09-24 — lihat brief-01\n"))
    brief(repo, "01", "guard", "DONE", finding_source=FINDING)
    sha = commit(repo, "fix(order): implement guard", "src/order.go", FINDING)    # brief tidak di-stage (Langkah 24)
    assert git(repo, "status", "--porcelain") == ""
    assert bs.finding_diff_ok(repo, sha, FINDING)


def test_scope_check_allows_only_fixed_lines(chain_repo):
    repo = _repo(chain_repo)
    (repo / FINDING).write_text((repo / FINDING).read_text() + "> Status: FIXED 2026-09-24 — lihat brief-01\n")
    ok = commit(repo, "fixed only", FINDING)
    assert bs.finding_diff_ok(repo, ok, FINDING)
    (repo / FINDING).write_text((repo / FINDING).read_text().replace("stok negatif", "stok minus")
                                + "> Status: FIXED 2026-09-25 — lihat brief-02\n")
    bad = commit(repo, "fixed + edit", FINDING)
    assert not bs.finding_diff_ok(repo, bad, FINDING)
    assert not bs.finding_diff_ok(repo, bad, "src/order.go")      # berkas tanpa diff di commit itu


def test_scaffold_writes_finding_source(chain_repo):
    write_files(chain_repo, {f"{TD}/.explore/brief-matrix.json": json.dumps({
        "finding_source": FINDING,
        "briefs": [{"nn": "01", "unit": "guard", "title": "guard", "risk": "MINOR", "fulfills": ["SC-1", "SC-2"]}]})})
    out = be_run(chain_repo, "plan/scripts/scaffold_brief.py", "--taskdir", TD, "--nn", "01")
    assert out.returncode == 0, out.stdout + out.stderr
    fm = (chain_repo / TD / "brief-01-guard.md").read_text().split("---")[1]
    assert re.search(rf"^finding_source: {re.escape(FINDING)}$", fm, re.M)
