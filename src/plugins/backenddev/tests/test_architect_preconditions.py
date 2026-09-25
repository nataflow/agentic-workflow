"""Prasyarat `architect`: status brief dari frontmatter saja (L5.9), taskdir (L5.2), dirty/agent (L5.5)."""
import pytest

from conftest import TD, be_checks, brief, commit, write_files

AR = "architect/scripts/check_preconditions.py"
FENCE = "# Brief\n\n## Steps\n1. Contoh isi berkas state:\n\n```yaml\nstatus: DONE\n```\n"


def ar(repo, td=TD):
    return be_checks(repo, AR, "--root", str(repo), "--taskdir", td)


def test_status_berkutip_tidak_dibaca_dari_code_fence(chain_repo):
    brief(chain_repo, "01", "lock", '"READY"', FENCE)
    brief(chain_repo, "02", "api", '"READY"', FENCE)
    commit(chain_repo, "docs: briefs")
    c = ar(chain_repo)[3]
    assert c["status"] == "PASS" and c["entry"] == "FASE_3:01", c


def test_status_huruf_kecil_tak_terbaca(chain_repo):
    brief(chain_repo, "01", "lock", "ready", FENCE)
    commit(chain_repo, "docs: briefs")
    c = ar(chain_repo)[3]
    assert c["status"] == "FAIL" and "tak terbaca" in c["summary"] and "brief-01-lock.md" in c["summary"]
    assert "`ready`" in c["summary"]


def test_blocked_disebut(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    brief(chain_repo, "02", "api", "READY")
    brief(chain_repo, "03", "db", "BLOCKED")
    commit(chain_repo, "docs: briefs")
    c = ar(chain_repo)[3]
    assert c["status"] == "FAIL" and "BLOCKED" in c["summary"] and "brief-03-db.md" in c["summary"]


def test_laci_explore_bukan_kotor(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs: briefs")
    write_files(chain_repo, {f"{TD}/.explore/q.md": "x\n"})
    assert ar(chain_repo)[4]["status"] == "PASS"
    write_files(chain_repo, {"src/lain.go": "package order\n"})
    assert ar(chain_repo)[4]["status"] == "FAIL"


@pytest.mark.parametrize("td", ["src", "backenddev/docs/2609240900-belum-ada"])
def test_taskdir_ditolak(chain_repo, td):
    assert ar(chain_repo, td)[1]["status"] == "FAIL"
