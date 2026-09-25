"""Langkah 5 jalur frontenddev — parser bersama `precondition_lib` dan pembacanya (L5.6–L5.9)."""
import importlib.util
import json
import sys

import pytest

from conftest import FE_MINOR_TD, FE_SKILLS, commit, fe_review_md, fe_run, write_files


def load_fe(rel: str, name: str):
    """Muat modul frontenddev lewat path berkas; `precondition_lib` yang diimpornya = milik frontenddev.

    backenddev punya modul bernama sama; impor lewat `sys.path` di satu sesi pytest bisa
    mengambil salinan yang salah dari `sys.modules`.
    """
    saved = sys.modules.get("precondition_lib")
    sys.modules["precondition_lib"] = FE_LIB if rel != "_common/precondition_lib.py" else None
    try:
        spec = importlib.util.spec_from_file_location(name, FE_SKILLS / rel)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        if saved is None:
            sys.modules.pop("precondition_lib", None)
        else:
            sys.modules["precondition_lib"] = saved


FE_LIB = None
FE_LIB = load_fe("_common/precondition_lib.py", "frontenddev_precondition_lib")


# --- L5.8 path non-ASCII dan route group berkurung ------------------------------------------

PROMO_TD = "frontenddev/docs/2601011200-promo"


@pytest.fixture
def promo_repo(make_repo):
    """Rantai `promo`: akar TASK.md, lalu satu commit unit yang menyentuh berkas unicode dan route group."""
    root = make_repo({f"{PROMO_TD}/TASK.md": "---\nstatus: ACTIVE\n---\n# Banner promo\n\n"
                                             "## Success Criteria\n- [ ] **SC-1**: x — verifikasi: test\n"})
    commit(root, "docs(promo): root task")
    write_files(root, {"src/i18n/café.tsx": "export default {}\n",
                       "app/(tabs)/index.tsx": "export default function T(){}\n",
                       "src/components/Kartu Promo.tsx": "export default {}\n"})
    commit(root, "feat(promo): implement unit 01")
    return root


def report_check4(repo, changes: str) -> dict:
    write_files(repo, {f"{PROMO_TD}/REPORT.md":
                       "# Banner promo — Report\n\n## Ringkasan\nBanner promo kini tampil di beranda.\n\n"
                       f"## Perubahan\n{changes}\n"})
    r = fe_run(repo, "report/scripts/validate_report.py", "--taskdir", PROMO_TD, "--json")
    return {c["id"]: c for c in json.loads(r.stdout)["checks"]}[4]


def test_chain_files_unicode_dan_berspasi(promo_repo):
    assert FE_LIB.chain_files(promo_repo, PROMO_TD) == [
        "app/(tabs)/index.tsx", "src/components/Kartu Promo.tsx", "src/i18n/café.tsx"]


@pytest.mark.parametrize("changes", [
    "- Tambah terjemahan bahasa Prancis (src/i18n/café.tsx)\n- Tambah tab beranda baru (app/(tabs))",
    "- Tambah terjemahan bahasa Prancis (src/i18n)\n- Tambah tab beranda baru (app/(tabs)/index.tsx)",
])
def test_report_unicode_dan_route_group_expo_pass(promo_repo, changes):
    changes += "\n- Tambah kartu promo baru (src/components/Kartu Promo.tsx)"
    c4 = report_check4(promo_repo, changes)
    assert c4["status"] == "PASS", c4


def test_bullet_route_group_sveltekit(make_repo):
    root = make_repo({f"{PROMO_TD}/TASK.md": "---\nstatus: ACTIVE\n---\n# Banner promo\n"})
    commit(root, "docs(promo): root task")
    write_files(root, {"src/routes/(app)/+page.svelte": "<h1>x</h1>\n"})
    commit(root, "feat(promo): implement unit 01")
    c4 = report_check4(root, "- Rute promo tampil di beranda (src/routes/(app)/+page.svelte)")
    assert c4["status"] == "PASS", c4


@pytest.mark.parametrize("line,want", [
    ("- Tambah tab (app/(tabs)/index.tsx)", ("Tambah tab", "app/(tabs)/index.tsx")),
    ("- Tab (baru) (app/(tabs)/x.tsx)", ("Tab (baru)", "app/(tabs)/x.tsx")),
    ("- Rute (src/routes/(app)/+page.svelte)", ("Rute", "src/routes/(app)/+page.svelte")),
    ("- Terjemahan (src/i18n)", ("Terjemahan", "src/i18n")),
    ("- Tanpa anotasi", None),
    ("- (src/x.ts)", None),
])
def test_parse_bullet(line, want):
    vr = load_fe("report/scripts/validate_report.py", "fe_validate_report_l58")
    assert vr.parse_bullet(line) == want


# --- L5.7 `qa manual:` satu aturan di keempat pembaca ---------------------------------------

@pytest.mark.parametrize("line,want", [
    ("x — verifikasi: QA manual: buka", True),
    ("x — verifikasi: qa manual: buka", True),
    ("x — verifikasi: Qa Manual: buka", True),
    ("x — verifikasi: QA  manual: buka", True),
    ("cek QA manual: dulu — verifikasi: test", False),
])
def test_is_manual(line, want):
    assert FE_LIB.is_manual(line) is want


@pytest.mark.parametrize("cell,want", [
    ("QA manual: klik tombol", True), ("qa  Manual: klik", True), ("`QA manual: klik`", True),
    ("test otomatis", False), ("test otomatis, lalu QA manual: cek", False),
])
def test_is_manual_cell(cell, want):
    assert FE_LIB.is_manual_cell(cell) is want


def minor_manual(repo, measure: str, sc_text: str = "tombol order menampilkan label Pesan"):
    """TASK.md `fe_minor_chain` dengan SC-1 beralat ukur `measure`; REVIEW.md memvonisnya PERLU VERIFIKASI MANUAL."""
    task = repo / FE_MINOR_TD / "TASK.md"
    text = task.read_text(encoding="utf-8")
    old = "tombol order menampilkan label Pesan — verifikasi: test `OrderButton.test.tsx` hijau"
    assert old in text
    task.write_text(text.replace(old, f"{sc_text} — verifikasi: {measure}"), encoding="utf-8")
    review = fe_review_md(repo).replace(
        "| `SC-1` | terbukti | `src/features/order/OrderButton.test.tsx:1` |",
        "| `SC-1` | PERLU VERIFIKASI MANUAL | klik tombol order |")
    write_files(repo, {f"{FE_MINOR_TD}/REVIEW.md": review})
    r = fe_run(repo, "architect/scripts/validate_review.py", "--taskdir", FE_MINOR_TD, "--json")
    return {c["id"]: c for c in json.loads(r.stdout)["checks"]}["SC"]


def test_review_perlu_verifikasi_manual_qa_huruf_kecil(fe_minor_chain):
    sc = minor_manual(fe_minor_chain, "qa manual: klik tombol order, lihat label")
    assert sc["status"] == "PASS", sc


def test_review_qa_manual_di_deskripsi_bukan_alat_ukur(fe_minor_chain):
    sc = minor_manual(fe_minor_chain, "test `OrderButton.test.tsx` hijau",
                      sc_text="cek QA manual: dulu tombol order menampilkan label Pesan")
    assert sc["status"] == "FAIL" and "bukan SC ber-alat-ukur" in json.dumps(sc)


def test_report_manual_huruf_kecil_wajib_catatan(fe_minor_chain):
    minor_manual(fe_minor_chain, "qa manual: klik tombol order, lihat label")
    write_files(fe_minor_chain, {f"{FE_MINOR_TD}/REPORT.md":
                                 "# Order button — perbaikan label — Report\n\n## Ringkasan\n\n"
                                 "Tombol order kini berlabel Pesan.\n\n## Perubahan\n\n"
                                 "- tombol order baru beserta test (src/features/order)\n\n"
                                 "## Catatan\n\n- REVIEW.md P2-1: label belum memakai i18n; ditunda\n"})
    r = fe_run(fe_minor_chain, "report/scripts/validate_report.py", "--taskdir", FE_MINOR_TD, "--json")
    c5 = {c["id"]: c for c in json.loads(r.stdout)["checks"]}[5]
    assert c5["status"] == "FAIL" and "SC QA manual tanpa" in c5["summary"], c5


PROMO_TASK = """---
status: ACTIVE
lane: HOTFIX_MINOR
sections: -
created: 2026-01-01
---
# Banner promo

## Description
Perbaiki banner.

## Success Criteria
- [ ] **SC-1**: banner tampil di beranda — verifikasi: {measure}

## Out of Scope
- checkout — di luar permintaan

## Chain
"""


def validate_task(repo, td=PROMO_TD) -> dict:
    r = fe_run(repo, "task/scripts/validate_task.py", "--root", str(repo), "--taskdir", td, "--json")
    return {c["id"]: c for c in json.loads(r.stdout)["checks"]}


@pytest.mark.parametrize("measure", ["qa manual: buka beranda, lihat banner",
                                     "QA  manual: buka beranda, lihat banner"])
def test_validate_task_alat_ukur_manual_sah(make_repo, measure):
    root = make_repo({f"{PROMO_TD}/TASK.md": PROMO_TASK.format(measure=measure)})
    c3 = validate_task(root)[3]
    assert c3["status"] == "PASS", c3


# --- L5.6 satu pendeteksi placeholder untuk tiga validator ----------------------------------

PLACEHOLDER_ROWS = [
    ("sah", "Saat memuat tampilkan `<Spinner />` di tengah kartu."),
    ("sah", "Saat memuat tampilkan <Skeleton /> tiga baris."),
    ("sah", "Fitur todo list menampilkan butir yang belum selesai."),
    ("sah", "- [ ] **SC-1**: waktu muat < 300 ms dan jumlah item > 0 — verifikasi: test"),
    ("sah", "Props `Record<string, string>` diteruskan ke <OrderRow>."),
    ("slot", "Nama layar: <Nama Layar Utama>"),
    ("slot", "Berkas `src/features/<slug>/api.ts` dibuat."),
    ("slot", "Keputusan: TBD"),
    ("slot", "Alasan diisi nanti."),
]


def doc_verdict(line: str) -> str:
    vdoc = load_fe("_common/validate_doc.py", "fe_validate_doc_l56")
    v = vdoc.DocValidator.__new__(vdoc.DocValidator)
    v.body, v.results = line, []
    v._check_placeholders()
    return v.results[0]["status"]


def brief_verdict(line: str) -> str:
    vbr = load_fe("plan/scripts/validate_briefs.py", "fe_validate_briefs_l56")
    body = "".join(f"{h}\n{line if h.startswith('## 2') else 'isi'}\n\n" for h in vbr.REQUIRED_SECTIONS)
    v = vbr.BriefValidator.__new__(vbr.BriefValidator)
    v.results = []
    v.active = lambda: [{"name": "brief-01-x.md", "body": body}]
    v._check_b_placeholder()
    return v.results[0]["status"]


@pytest.mark.parametrize("want,line", PLACEHOLDER_ROWS)
def test_find_placeholders(want, line):
    assert bool(FE_LIB.find_placeholders(line)) is (want == "slot")


@pytest.mark.parametrize("want,line", PLACEHOLDER_ROWS)
def test_validate_doc_dan_briefs_sama_dengan_pendeteksi(want, line):
    expected = "FAIL" if want == "slot" else "PASS"
    assert doc_verdict(line) == expected
    assert brief_verdict(line) == expected


@pytest.mark.parametrize("line", ['Tombol <Button variant="primary"> di kanan.',
                                  'Tampilkan <Spinner size="sm" /> saat memuat.'])
def test_jsx_berattribut(line):
    assert FE_LIB.find_placeholders(line) == []


def test_todo_huruf_besar_tetap_ditolak():
    assert FE_LIB.find_placeholders("TODO: pastikan label benar") == ["TODO"]


def test_slot_dalam_backtick_hanya_kosakata():
    assert FE_LIB.find_placeholders("Render `<Nama Komponen>` di header.") == []
    assert FE_LIB.find_placeholders("Berkas `brief-<NN>-x.md`.") == ["<NN>"]


def promo_task_check7(root, description_extra: str = "", sc: str = "banner tampil di beranda"):
    text = PROMO_TASK.format(measure="test `promo.test.tsx` hijau").replace("banner tampil di beranda", sc)
    write_files(root, {f"{PROMO_TD}/TASK.md": text.replace("Perbaiki banner.",
                                                            "Perbaiki banner. " + description_extra)})
    return validate_task(root)[7]


def test_validate_task_sc_perbandingan_bukan_placeholder(make_repo):
    c7 = promo_task_check7(make_repo(), sc="waktu muat < 300 ms dan jumlah item > 0, tampil <OrderRow>")
    assert c7["status"] == "PASS", c7


def test_validate_task_slug_dalam_backtick_ditolak(make_repo):
    c7 = promo_task_check7(make_repo(), description_extra="Berkas `src/features/<slug>/api.ts` dibuat.")
    assert c7["status"] == "FAIL" and "<slug>" in c7["summary"], c7
