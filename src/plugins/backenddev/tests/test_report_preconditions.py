"""Prasyarat `report`: H1/heading sadar code fence dan BOM, status brief persis (L5.9)."""
from conftest import TD, be_checks, brief, commit, write_files

RP = "report/scripts/check_preconditions.py"
FENCE = "# Brief\n\n## Steps\n1. Contoh isi berkas state:\n\n```yaml\nstatus: DONE\n```\n"


def rp(repo):
    return be_checks(repo, RP, "--root", str(repo), "--taskdir", TD)


def test_brief_berkutip_bukan_done(chain_repo):
    brief(chain_repo, "01", "lock", '"READY"', FENCE)
    brief(chain_repo, "02", "api", "ready", FENCE)
    c = rp(chain_repo)[4]
    assert c["status"] == "FAIL"
    assert "brief-01-lock.md (READY)" in c["summary"] and "tak terbaca" in c["summary"]


def test_h1_di_code_fence_diabaikan(chain_repo):
    write_files(chain_repo, {f"{TD}/TASK.md": "---\nstatus: ACTIVE\n---\n# Refund\n\n## Description\n"
                                              "```bash\n# jalankan migrasi\nmake migrate\n```\n\n"
                                              "## Success Criteria\n- SC-1\n"})
    assert rp(chain_repo)[2]["status"] == "PASS"


def test_success_criteria_di_code_fence_tidak_terhitung(chain_repo):
    write_files(chain_repo, {f"{TD}/TASK.md": "---\nstatus: ACTIVE\n---\n# Refund\n\n```md\n## Success Criteria\n```\n"})
    c = rp(chain_repo)[2]
    assert c["status"] == "FAIL" and "Success Criteria" in c["summary"]


def test_task_bom_tanpa_frontmatter(chain_repo):
    (chain_repo / TD / "TASK.md").write_bytes("﻿# Refund\n\n## Success Criteria\n- SC-1\n".encode("utf-8"))
    assert rp(chain_repo)[2]["status"] == "PASS"


def test_task_bom_dengan_frontmatter(chain_repo):
    (chain_repo / TD / "TASK.md").write_bytes(
        "﻿---\r\nstatus: ACTIVE\r\n---\r\n# Refund\r\n\r\n## Success Criteria\r\n- SC-1\r\n".encode("utf-8"))
    assert rp(chain_repo)[2]["status"] == "PASS"
