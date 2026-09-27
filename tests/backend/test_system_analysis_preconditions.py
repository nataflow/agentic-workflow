"""Prasyarat `system-analysis`: status BRD dari frontmatter (L5.1), taskdir kanonik (L5.2), chain (L5.4)."""
import pytest

from conftest import be_checks, be_profile, commit, write_files

TD = "backenddev/docs/2601011200-refund"
SA = "system-analysis/scripts/check_preconditions.py"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TD}/TASK.md": "---\nchain: BRD_PRD_BRIEF\n---\n# T\n", "src/a.go": "package a\n"})
    be_profile(root, "go")
    commit(root, "init")
    return root


def sa(repo, td=TD, *extra):
    return be_checks(repo, SA, "--root", str(repo), "--taskdir", td, "--risk-level", "MAJOR", *extra)


def brd(repo, text):
    write_files(repo, {f"{TD}/BRD.md": text})


def test_brd_approved_dengan_kalimat_status_draft_di_body(repo):
    brd(repo, "---\ntitle: Refund\nrequester: ops\nstatus: APPROVED\n---\n# BRD\n\n## Business rules\n"
              "- **BR-1**: Order dengan status: DRAFT ditolak.\n")
    commit(repo, "docs(spec): approve BRD refund", f"{TD}/BRD.md")      # 11 H17: APPROVED terikat commit approve
    assert sa(repo)[1]["status"] == "PASS"


def test_brd_review_dengan_kalimat_refund_status_approved(repo):
    brd(repo, "---\ntitle: Refund\nrequester: ops\nstatus: REVIEW\n---\n# BRD\n\n## Business rules\n"
              "- **BR-1**: Refund status: APPROVED hanya oleh supervisor.\n")
    c = sa(repo)[1]
    assert c["status"] == "FAIL" and "REVIEW" in c["summary"]


def test_brd_tanpa_status_frontmatter(repo):
    brd(repo, "---\ntitle: Refund\nrequester: ops\n---\n# BRD\n\nRefund status: APPROVED\n")
    c = sa(repo)[1]
    assert c["status"] == "FAIL" and "tanpa kunci `status`" in c["summary"]


def test_brd_bom_crlf_approved(repo):
    (repo / TD / "BRD.md").write_bytes(
        b"\xef\xbb\xbf---\r\ntitle: R\r\nrequester: ops\r\nstatus: APPROVED\r\n---\r\n# BRD\r\n")
    commit(repo, "docs(spec): approve BRD refund", f"{TD}/BRD.md")
    assert sa(repo)[1]["status"] == "PASS"


def test_brd_draft_tetap_ditolak(repo):
    brd(repo, "---\nstatus: DRAFT\n---\n# BRD\n")
    c = sa(repo)[1]
    assert c["status"] == "FAIL" and "DRAFT" in c["summary"]


@pytest.mark.parametrize("td", ["src", ".", "backenddev/docs/2601011200-belum-ada"])
def test_taskdir_bukan_kanonik_ditolak(repo, td):
    assert sa(repo, td)[3]["status"] == "FAIL"


def test_chain_asing_dilaporkan(repo):
    write_files(repo, {f"{TD}/TASK.md": "---\nchain: PRD-BRIEF\n---\n# T\n"})
    c = sa(repo)[1]
    assert c["status"] == "FAIL" and "PRD-BRIEF" in c["summary"]


def test_profil_tanpa_base_branch_ditolak(repo):
    import json
    idx = repo / ".claude/profile/backenddev/index.json"
    data = json.loads(idx.read_text())
    del data["base_branch"]
    idx.write_text(json.dumps(data))
    c = sa(repo)[2]
    assert c["status"] == "FAIL" and "base_branch" in c["summary"]
