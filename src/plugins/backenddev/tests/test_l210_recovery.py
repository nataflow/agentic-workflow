"""L2.10 — brief READY yang commit-nya sudah mendarat dikoreksi, bukan didispatch ulang."""
from conftest import TD, be_checks, brief, commit, write_files

ARCH = "architect/scripts/check_preconditions.py"


def test_ready_with_landed_commit_detected(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    write_files(chain_repo, {"src/order.go": "package order\n// lock\n"})
    sha = commit(chain_repo, "fix(order): implement lock", "src/order.go")
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["entry"] == f"KOREKSI:01:{sha}"
    assert "dilarang dispatch ulang" in c3["action"]


def test_landed_sha_exact_subject(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    write_files(chain_repo, {"src/order.go": "package order\n// v2\n"})
    commit(chain_repo, "fix(order): implement lock-v2", "src/order.go")
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["entry"] == "FASE_3:01"
