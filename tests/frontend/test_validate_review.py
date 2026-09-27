"""L4.2 — `validate_review.py` menilai isi REVIEW.md, bukan hanya bentuknya."""
import json

import pytest

from conftest import FE_MINOR_TD as TD, FE_P2_FINDING, FE_SKILLS, commit, fe_profile, fe_review_md, fe_run, git, write_files

REVIEW = f"{TD}/REVIEW.md"


def validate(repo, *extra):
    r = fe_run(repo, "architect/scripts/validate_review.py", "--taskdir", TD, "--json", *extra)
    return r.returncode, json.loads(r.stdout)


def check(data, cid):
    return next(c for c in data["checks"] if c["id"] == cid)


R1 = dict(verdict="PASS", p2="0", summary_status="PASS", total="- Total Findings: 0 (0 P1, 0 P2, 0 P3)",
          findings="", dims=["PASS"] * 9, reviewed_at="0000-99-99", h1="# Review Findings — ",
          verification="| a | HIJAU | 0 |", sc_evidence="`x`", dim_names=["Layer Boundaries"] + [""] * 8)
R2 = dict(verdict="PASS", p2="0", summary_status="BLOCKED", total="",
          findings="", dims=["P1"] + ["PASS"] * 8, verification="| `build` | MERAH | 0 |", done="tidak terpenuhi")
R3 = dict(taskdir="frontenddev/docs/9999999999-bukan-taskdir-ini", stack="sveltekit")


@pytest.mark.parametrize("over, expected", [
    (R1, {"F": "bukan tanggal kalender", "S": "Review Findings — order-checkout",
          "VP": "bukan perintah ber-backtick", "SC": "tanpa bukti sah"}),
    (R2, {"V": "turunan mekanis `BLOCKED`", "D": "dimensi 1 berstatus `P1`", "SUM": "Total Findings wajib"}),
    (R3, {"F": "`taskdir: frontenddev/docs/9999999999-bukan-taskdir-ini` ≠"}),
], ids=["r1_bentuk_sampah", "r2_kontradiktif", "r3_frontmatter_asing"])
def test_review_kosong_makna_fail(fe_minor_chain, over, expected):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, **over)})
    rc, data = validate(fe_minor_chain)
    assert rc == 1
    for cid, needle in expected.items():
        c = check(data, cid)
        assert c["status"] == "FAIL" and any(needle in d for d in c["details"]), (cid, c)


def test_summary_status_bukan_turunan_fail(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, summary_status="PASS")})
    rc, data = validate(fe_minor_chain)
    assert rc == 1 and any("`Overall Status: PASS` ≠ verdict turunan `WARNING`" in d
                           for d in check(data, "SUM")["details"])


def test_stack_asing_fail(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, stack="sveltekit")})
    rc, data = validate(fe_minor_chain)
    assert rc == 1 and any("stack profil `react-vite`" in d for d in check(data, "F")["details"])


def test_fixture_positif_warning_pass(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain)})
    rc, data = validate(fe_minor_chain)
    assert rc == 0, data
    assert data["derived_verdict"] == "WARNING" and check(data, "LOG")["status"] == "SKIP"


def test_violation_tanpa_dimensi_fail(fe_minor_chain):
    findings = FE_P2_FINDING.replace("Dimensi 5 — ", "")
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, findings=findings)})
    rc, data = validate(fe_minor_chain)
    assert rc == 1 and any("tidak diawali `Dimensi" in d for d in check(data, "T")["details"])


def test_bukti_baris_di_luar_rentang_fail(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(
        fe_minor_chain, sc_evidence="`src/features/order/OrderButton.test.tsx:99`")})
    rc, data = validate(fe_minor_chain)
    assert rc == 1 and check(data, "SC")["status"] == "FAIL"


def test_bukti_perintah_hijau_sah(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, sc_evidence="`test` hijau")})
    assert validate(fe_minor_chain)[0] == 0


def log(repo, *entries):
    """Log mesin `run_verification.py closing`; baseline yang ada diukur di akar `TASK.md` (12 J13)."""
    rel = f"{TD}/.explore/closing-verification.json"
    akar = git(repo, "log", "--diff-filter=A", "--format=%H", "--", f"{TD}/TASK.md").split()[-1]
    rows = [dict(zip(("cmd", "status", "new_errors", "baseline_status"), e)) for e in entries]
    for r in rows:
        if r["baseline_status"] is not None:
            r["baseline_head"] = akar
    write_files(repo, {rel: json.dumps(rows)})
    return rel


def test_log_merah_nol_tanpa_baseline_merah_fail(fe_minor_chain):
    over = dict(verdict="WARNING", verification="| `test` | HIJAU | 0 |\n| `build` | MERAH | 0 |")
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, **over)})
    rc, data = validate(fe_minor_chain, "--log", log(fe_minor_chain, ("test", "HIJAU", 0, "HIJAU"),
                                                     ("build", "MERAH", 0, "HIJAU")))
    assert rc == 1 and any("tanpa baseline merah di log mesin" in d for d in check(data, "LOG")["details"])


def test_log_berbeda_dari_tabel_fail(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain)})
    rc, data = validate(fe_minor_chain, "--log", log(fe_minor_chain, ("test", "MERAH", 2, "HIJAU"),
                                                     ("lint", "HIJAU", 0, None)))
    details = check(data, "LOG")["details"]
    assert rc == 1 and any("≠ log mesin MERAH/2" in d for d in details)
    assert any("`lint` di log mesin absen dari tabel" in d for d in details)


def test_log_identik_pass(fe_minor_chain):
    # `--log` = architect Phase 4, sebelum REPORT.md ditulis (fixture memodelkan fase report).
    (fe_minor_chain / TD / "REPORT.md").unlink()
    write_files(fe_minor_chain, {REVIEW: fe_review_md(
        fe_minor_chain, verification="| `test` | HIJAU | 0 |\n| `build` | MERAH | 0 |")})
    rc, data = validate(fe_minor_chain, "--log", log(fe_minor_chain, ("test", "HIJAU", 0, "HIJAU"),
                                                     ("build", "MERAH", 0, "MERAH")))
    assert rc == 0, data


def test_reviewed_at_sebelum_commit_akar_fail(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, reviewed_at="2000-01-01")})
    rc, data = validate(fe_minor_chain)
    c = check(data, "F")
    assert rc == 1 and any("`reviewed_at: 2000-01-01` lebih awal dari commit akar" in d for d in c["details"]), c


def test_contoh_template_bagian_3_pass(make_repo):
    """Contoh terisi `review-template.md` bagian 3, di repo yang berkas rantai dan kontraknya cocok."""
    tmpl = (FE_SKILLS / "architect/templates/review-template.md").read_text(encoding="utf-8")
    example = tmpl.split("## 3. Contoh Terisi", 1)[1].split("````markdown\n", 1)[1].split("\n````", 1)[0] + "\n"
    task = ("---\nstatus: ACTIVE\nlane: FAST_FORWARD\nsections: [architecture]\ncreated: 2026-09-23\n---\n\n"
            "# Checkout\n\n## Success Criteria\n\n"
            "- [ ] **SC-1**: konfirmasi pesanan — verifikasi: test `CheckoutPage.test.tsx` hijau\n"
            "- [ ] **SC-2**: state checkout — verifikasi: test `useCheckoutPage.test.ts` hijau\n\n## Chain\n\n")
    contract = ("---\nstatus: APPROVED\n---\n\n# Contract\n\n## 5. Acceptance Criteria\n\n"
                "| ID | Skenario | Cara verifikasi | Sumber |\n|---|---|---|---|\n"
                + "".join(f"| `AC-{i}` | s | t | `SC-1` |\n" for i in range(1, 6)))
    repo = make_repo({f"{TD}/TASK.md": task})
    fe_profile(repo, "react-vite")
    git(repo, "commit", "-q", "--allow-empty", "-m", "init")
    commit(repo, "docs(order-checkout): kunci TASK sebagai akar rantai", f"{TD}/TASK.md")
    base = git(repo, "rev-parse", "--short=7", "HEAD").strip()
    lines = "".join(f"// {i}\n" for i in range(50))
    src = {f"src/features/checkout/{p}": lines for p in
           ("pages/CheckoutPage.test.tsx", "hooks/useCheckoutPage.test.ts", "pages/CheckoutPage.tsx")}
    write_files(repo, {**src, f"{TD}/CONTRACT.md": contract})
    commit(repo, "feat(order-checkout): implement unit 01", *src, f"{TD}/CONTRACT.md")
    born = git(repo, "log", "-1", "--format=%cs", base).strip()
    example = example.replace("base: 540364c", f"base: {base}").replace("reviewed_at: 2026-09-25", f"reviewed_at: {born}")
    write_files(repo, {REVIEW: example})
    rc, data = validate(repo)
    assert rc == 0, [c for c in data["checks"] if c["status"] == "FAIL"]
    assert data["derived_verdict"] == "WARNING"


@pytest.mark.regression("E15")
def test_e15_tree_kotor_sesudah_reviewer_fail(fe_minor_chain):
    (fe_minor_chain / TD / "REPORT.md").unlink()
    write_files(fe_minor_chain, {REVIEW: fe_review_md(
        fe_minor_chain, verification="| `test` | HIJAU | 0 |\n| `build` | MERAH | 0 |"),
        "src/features/order/OrderButton.tsx": "export const X = 1\n"})
    rc, data = validate(fe_minor_chain, "--log", log(fe_minor_chain, ("test", "HIJAU", 0, "HIJAU"),
                                                     ("build", "MERAH", 0, "MERAH")))
    c = check(data, "TREE")
    assert rc == 1 and any("OrderButton.tsx" in d for d in c["details"]), c


@pytest.mark.regression("E15")
def test_e15_tree_tanpa_log_skip(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain)})
    _, data = validate(fe_minor_chain)
    assert check(data, "TREE")["status"] == "SKIP"
