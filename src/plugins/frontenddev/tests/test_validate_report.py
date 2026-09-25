"""L4.2 — `validate_report.py` menolak REPORT kosong makna dan menagih temuan REVIEW yang belum tuntas."""
import json

from conftest import FE_MINOR_TD as TD, fe_review_md, fe_run, write_files

REPORT_HEAD = "# Order button — perbaikan label — Report\n\n## Ringkasan\n\n"
GOOD_CHANGES = "## Perubahan\n\n- tombol order baru beserta test (src/features/order)\n"


def validate(repo):
    r = fe_run(repo, "report/scripts/validate_report.py", "--taskdir", TD, "--json")
    return r.returncode, {c["id"]: c for c in json.loads(r.stdout)["checks"]}


def setup(repo, report, **review):
    write_files(repo, {f"{TD}/REVIEW.md": fe_review_md(repo, **review), f"{TD}/REPORT.md": report})


def test_r4_temuan_planned_absen_dari_catatan_fail(fe_minor_chain):
    setup(fe_minor_chain, REPORT_HEAD + "Tombol order kini berlabel Pesan.\n\n" + GOOD_CHANGES)
    rc, checks = validate(fe_minor_chain)
    assert rc == 1 and "temuan P2-1 belum dituntaskan" in checks[5]["summary"]


def test_r5_report_selesai_fail(fe_minor_chain):
    setup(fe_minor_chain, REPORT_HEAD + "Selesai.\n\n## Perubahan\n\n- x (src)\n")
    rc, checks = validate(fe_minor_chain)
    assert rc == 1
    assert "terlalu umum" in checks[3]["summary"]
    assert "< 3 kata" in checks[4]["summary"] and "direktori tingkat atas" in checks[4]["summary"]


def test_positif_catatan_menyebut_temuan_pass(fe_minor_chain):
    setup(fe_minor_chain, REPORT_HEAD + "Tombol order kini berlabel Pesan.\n\n" + GOOD_CHANGES
          + "\n## Catatan\n\n- REVIEW.md P2-1: label belum memakai i18n; ditunda ke rantai berikutnya\n")
    rc, checks = validate(fe_minor_chain)
    assert rc == 0, checks
    r = fe_run(fe_minor_chain, "report/scripts/validate_report.py", "--taskdir", TD)
    assert r.stdout.startswith("REPORT VALIDATION: [PASS]")


def test_temuan_fixed_tidak_ditagih(fe_minor_chain):
    from conftest import FE_P2_FINDING
    fixed = FE_P2_FINDING.replace("> Status: PLANNED", "> Status: FIXED 2026-09-25 — lihat " + TD)
    setup(fe_minor_chain, REPORT_HEAD + "Tombol order kini berlabel Pesan.\n\n" + GOOD_CHANGES, findings=fixed)
    assert validate(fe_minor_chain)[0] == 0
