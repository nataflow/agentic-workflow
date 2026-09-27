"""Prasyarat `plan`: status PRD/RCA dari frontmatter (L5.1), taskdir (L5.2), chain/risk (L5.4), path plugin (L5.5)."""
import pytest

from conftest import be_checks, be_profile, commit, write_files

TD = "backenddev/docs/2601011200-refund"
PL = "plan/scripts/check_preconditions.py"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TD}/TASK.md": "---\nchain: BRD_PRD_BRIEF\nrisk: MAJOR\n---\n# T\n",
                      "src/a.go": "package a\n"})
    be_profile(root, "go")
    commit(root, "init")
    return root


def plan(repo, *args, td=TD):
    return be_checks(repo, PL, "--root", str(repo), "--taskdir", td, *args)


def test_prd_approved_kalimat_status_draft(repo):
    write_files(repo, {f"{TD}/PRD.md": "---\ntitle: Refund\nsource_brd: x\nstatus: APPROVED\n---\n# PRD\n\n"
                                        "## Business rules\n- Order dengan status: DRAFT ditolak.\n"})
    commit(repo, "docs(spec): approve PRD refund", f"{TD}/PRD.md")      # 11 H17
    assert plan(repo, "--entry-mode", "PRD", "--chain", "BRD_PRD_BRIEF")[3]["status"] == "PASS"


def test_prd_tanpa_status_frontmatter(repo):
    write_files(repo, {f"{TD}/PRD.md": "---\ntitle: Refund\n---\n# PRD\nstatus: APPROVED\n"})
    c = plan(repo, "--entry-mode", "PRD", "--chain", "BRD_PRD_BRIEF")[3]
    assert c["status"] == "FAIL" and "tanpa kunci `status`" in c["summary"]


def test_rca_confirmed_hipotesis_inconclusive(repo):
    write_files(repo, {f"{TD}/RCA.md": f"---\nstatus: ROOT_CAUSE_CONFIRMED\ntaskdir: {TD}/\n---\n# RCA\n\n"
                                        "## Hipotesis\n- H1 (gugur) — status: INCONCLUSIVE\n"})
    assert plan(repo, "--entry-mode", "RCA", "--chain", "-")[3]["status"] == "PASS"


def test_rca_inconclusive_frontmatter(repo):
    write_files(repo, {f"{TD}/RCA.md": "---\nstatus: INCONCLUSIVE\n---\n# RCA\n"})
    c = plan(repo, "--entry-mode", "RCA", "--chain", "-")[3]
    assert c["status"] == "FAIL" and "berstatus INCONCLUSIVE" in c["summary"]


def test_taskdir_belum_diprovisi(repo):
    c = plan(repo, "--entry-mode", "LANGSUNG", "--chain", "BRIEF", td="backenddev/docs/2601011200-belum-ada")[1]
    assert c["status"] == "FAIL" and "tidak ditemukan" in c["summary"]


@pytest.mark.parametrize("td", ["src", "."])
def test_taskdir_non_kanonik_ditolak(repo, td):
    assert plan(repo, "--entry-mode", "LANGSUNG", "--chain", "BRIEF", td=td)[1]["status"] == "FAIL"


def test_risk_asing_dilaporkan(repo):
    c = plan(repo, "--entry-mode", "LANGSUNG", "--chain", "BRIEF", "--risk", "HIGH", "--file-scope", "src")[8]
    assert c["status"] == "FAIL" and "risk 'HIGH' tidak sah" in c["summary"]


def test_chain_dan_risk_huruf_kecil_dari_task(repo):
    write_files(repo, {f"{TD}/TASK.md": '---\nchain: "brief"\nrisk: minor # plafon\n---\n# T\n'})
    c = plan(repo, "--entry-mode", "LANGSUNG", "--file-scope", "src")[8]
    assert c["status"] == "PASS" and "Chain BRIEF" in c["summary"] and "risk MINOR" in c["summary"]


def test_templat_dan_agent_plugin_tersedia(repo):
    checks = plan(repo, "--entry-mode", "LANGSUNG", "--chain", "BRIEF")
    assert checks[5]["status"] == "PASS" and checks[7]["status"] == "PASS"


# --- B10: jalur RCA menagih risk dan file_scope ------------------------------------------------
RCA_MD = "---\nstatus: ROOT_CAUSE_CONFIRMED\n---\n\n# RCA\n\n## Arah perbaikan\n\n| src/a.go | modify |\n"


@pytest.fixture
def rca_repo(make_repo):
    def _make(task_risk=True):
        fm = "lane: DEFECT_RCA\n" + ("risk: MINOR\n" if task_risk else "")
        root = make_repo({f"{TD}/TASK.md": f"---\n{fm}---\n# T\n", f"{TD}/RCA.md": RCA_MD,
                          "src/a.go": "package a\n"})
        be_profile(root, "go")
        commit(root, "init")
        return root
    return _make


def test_b10_rca_tanpa_file_scope_fail(rca_repo):
    c = plan(rca_repo(), "--entry-mode", "RCA")[8]
    assert c["status"] == "FAIL" and "file_scope kosong pada jalur RCA" in c["summary"]


def test_b10_rca_tanpa_risk_fail(rca_repo):
    c = plan(rca_repo(task_risk=False), "--entry-mode", "RCA", "--file-scope", "src/")[8]
    assert c["status"] == "FAIL" and "Risk tidak sah pada jalur RCA" in c["summary"]


def test_b10_rca_lengkap_pass(rca_repo):
    root = rca_repo()
    c = plan(root, "--entry-mode", "RCA", "--file-scope", "src/")[8]
    assert c["status"] == "PASS" and "risk MINOR" in c["summary"]
    assert plan(root, "--entry-mode", "RCA", "--risk", "MAJOR", "--file-scope", "src/")[8]["status"] == "PASS"
