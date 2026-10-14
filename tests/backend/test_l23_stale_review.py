"""L2.3 — REVIEW.md basi (kode mendarat sesudahnya) memaksa review ulang, bukan Fase 5."""
from conftest import TD, be_checks, be_run, brief, commit, git, land, write_files

ARCH = "architect/scripts/check_preconditions.py"
REPORT = "report/scripts/check_preconditions.py"


def _reviewed(repo, highest="P1"):
    """Dua unit mendarat (commit kode bersubjek `commit_message`), lalu REVIEW.md menilai HEAD itu (`range:`)."""
    git(repo, "checkout", "-qb", "fix/order")
    base = git(repo, "rev-parse", "HEAD").strip()
    land(repo, brief(repo, "01", "lock", "READY"), line="// v1\n")
    land(repo, brief(repo, "02", "endpoint", "READY"), line="// v2\n")
    head = git(repo, "rev-parse", "HEAD").strip()
    write_files(repo, {f"{TD}/REVIEW.md": f"---\nrange: {base[:7]}..{head[:7]} (2 commit)\nhighest: {highest}\n---\n"
                                          "# Review\n"})


def _land_fix(repo):
    land(repo, brief(repo, "03", "endpoint-fix", "READY"), line="// fix P1\n")


def test_stale_review_routes_to_phase4(chain_repo):
    _reviewed(chain_repo)
    _land_fix(chain_repo)
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "PASS" and c3["entry"] == "FASE_4"
    assert "REVIEW.md basi" in c3["summary"]


def test_fresh_review_routes_to_phase5(chain_repo):
    _reviewed(chain_repo, "CLEAN")
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["entry"] == "FASE_5"


def test_review_and_report_tuntas(chain_repo):
    _reviewed(chain_repo, "CLEAN")
    write_files(chain_repo, {f"{TD}/REPORT.md": "# Report\n"})
    commit(chain_repo, "docs(order-fix): add chain report")
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["entry"] == "TUNTAS"


def test_action_printed_on_pass(chain_repo):
    _reviewed(chain_repo, "CLEAN")
    out = be_run(chain_repo, ARCH, "--taskdir", TD).stdout
    assert "* Titik masuk: Lompat ke Fase 5" in out


def test_report_rejects_stale_review(chain_repo):
    _reviewed(chain_repo)
    _land_fix(chain_repo)
    c3 = be_checks(chain_repo, REPORT, "--taskdir", TD)[3]
    assert c3["status"] == "FAIL" and "REVIEW.md basi" in c3["summary"]
