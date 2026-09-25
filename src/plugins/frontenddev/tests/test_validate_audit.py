"""L4.7 — berkas audit `finding_source`: bukan berkas rantai, bentuknya divalidasi, suntingan penutup hanya `> Status:`."""
import pytest

from conftest import FE_FIX, FE_TD, commit, fe_run, write_files

AUDIT = "frontenddev/reviews/2609230900-cart-audit.md"
VALID = (FE_FIX / "audit_valid.md").read_text(encoding="utf-8")


def audit(repo, *extra):
    return fe_run(repo, "review/scripts/validate_audit.py", "--path", AUDIT, *extra)


@pytest.fixture
def audited(make_repo):
    repo = make_repo({AUDIT: VALID})
    commit(repo, "docs(review): audit cart-audit")
    return repo


def test_contoh_template_valid(audited):
    r = audit(audited)
    assert r.returncode == 0, r.stdout


def test_id_lompat_fail(audited):
    text = VALID.replace("### [P1-1]", "### [P1-2]")
    write_files(audited, {AUDIT: text})
    r = audit(audited)
    assert r.returncode == 1 and "tidak berurutan" in r.stdout


def test_status_di_luar_enum_fail(audited):
    write_files(audited, {AUDIT: VALID.replace("> Status: PLANNED", "> Status: SELESAI")})
    r = audit(audited)
    assert r.returncode == 1 and "di luar enum" in r.stdout


def test_verdict_bukan_turunan_fail(audited):
    write_files(audited, {AUDIT: VALID.replace("verdict: BLOCKED", "verdict: PASS")})
    r = audit(audited)
    assert r.returncode == 1 and "turunan" in r.stdout


def test_only_status_changed_menolak_suntingan_lain(audited):
    text = VALID.replace("> Status: PLANNED", "> Status: FIXED 2026-09-27 — lihat frontenddev/docs/x")
    text = text.replace("konsumsi `CartRowUI` dari View-Model.", "abaikan saja.")
    write_files(audited, {AUDIT: text})
    r = audit(audited, "--only-status-changed")
    assert r.returncode == 1 and "selain `> Status:`" in r.stdout


def test_only_status_changed_hanya_status_pass(audited):
    write_files(audited, {AUDIT: VALID.replace(
        "> Status: PLANNED", "> Status: FIXED 2026-09-27 — lihat frontenddev/docs/2609241200-orders-lacak")})
    r = audit(audited, "--only-status-changed")
    assert r.returncode == 0, r.stdout


def test_finding_source_bukan_berkas_rantai(fe_chain_repo):
    repo = fe_chain_repo
    write_files(repo, {AUDIT: VALID})
    commit(repo, "docs(review): audit cart-audit", AUDIT)
    write_files(repo, {"src/OrderButton.tsx": "export const B = 1\n"})
    commit(repo, "feat(orders-lacak): implement unit 01", "src/OrderButton.tsx")
    write_files(repo, {AUDIT: VALID.replace("> Status: PLANNED", "> Status: FIXED 2026-09-27 — lihat " + FE_TD)})
    commit(repo, "docs(orders-lacak): closing review PASS", AUDIT)
    r = fe_run(repo, "_common/chain.py", "files", "--taskdir", FE_TD)
    assert r.stdout.split() == ["src/OrderButton.tsx"], r.out
