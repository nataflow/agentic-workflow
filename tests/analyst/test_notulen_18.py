"""Langkah 18 — skill `analyst:notulen`: siklus hidup `notulen.py` (N1–N4, N6).

Notulendir `analyst/notulen/<YYMMDDhhmm>-<slug>/NOTULEN.md` selalu diabaikan git dan tidak pernah di-commit.
`## Catatan Asli` dimateraikan `source_hash`; `final` menyegel badan notulen sebagai `final_hash`, dan suntingan
sesudahnya terbaca `DRIFT`.
"""
import json

import pytest

from conftest import PLUGINS, git, load_module, run_script, write_files

NOTULEN = PLUGINS / "analyst" / "skills" / "notulen" / "scripts" / "notulen.py"
NOTES = "rapat sprint\n- budi: export csv minggu depan\n\nputus: rilis jumat\n"
IGNORE = "analyst/notulen/.gitignore"
FILLED = {
    "## Ringkasan\n\n_(belum ditulis)_": "## Ringkasan\n\nTim menyepakati rilis Jumat dan ekspor CSV untuk Finance.",
    "## Peserta\n\n_(belum ditulis)_": "## Peserta\n\n- Budi (PM)\n- Rina (Finance)",
    "## Agenda\n\n_(belum ditulis)_": "## Agenda\n\n1. Status sprint\n2. Ekspor laporan",
    "## Pembahasan\n\n_(belum ditulis)_": "## Pembahasan\n\n- Finance butuh ekspor CSV untuk rekap bulanan.",
    "## Keputusan\n\n- Tidak ada.": "## Keputusan\n\n- **D-1**: Rilis dilakukan Jumat.",
    "| ID | Tindakan | PIC | Tenggat |\n|---|---|---|---|\n":
        "| ID | Tindakan | PIC | Tenggat |\n|---|---|---|---|\n| A-1 | Siapkan ekspor CSV | Budi | 2026-10-09 |\n"
        "| A-2 | Kabari klien soal jadwal rilis | belum ditentukan | belum ditentukan |\n",
    "## Pertanyaan Terbuka\n\n- Tidak ada.": "## Pertanyaan Terbuka\n\n- **Q-1**: Format tanggal di CSV? — menunggu: Rina",
}
lib = load_module(PLUGINS / "analyst" / "skills" / "_common" / "analyst_lib.py", "analyst_lib_18n")


def nt(root, *args, stdin=""):
    r = run_script(NOTULEN, *args, cwd=root, stdin=stdin)
    return r.returncode, r.stdout + r.stderr


def new(root, slug="sprint-review", notes=NOTES, date="2026-10-02", title="Sprint review Q4"):
    code, out = nt(root, "new", "--slug", slug, "--title", title, "--date", date, "--notes", "-", stdin=notes)
    assert code == 0, out
    return out.split("NEW PASS: ", 1)[1].split(" ·", 1)[0]


def path(root, rel):
    return root / rel / "NOTULEN.md"


def edit(root, rel, old, new_text):
    p = path(root, rel)
    text = p.read_text(encoding="utf-8")
    assert old in text, old
    p.write_text(text.replace(old, new_text, 1), encoding="utf-8")


def fill(root, rel):
    for old, new_text in FILLED.items():
        edit(root, rel, old, new_text)


def checks(root, rel, *extra):
    r = run_script(NOTULEN, "check", "--notulendir", rel, "--json", *extra, cwd=root)
    return r.returncode, {c["id"]: c for c in json.loads(r.stdout)["checks"]}


def failed(root, rel, *extra):
    code, by_id = checks(root, rel, *extra)
    return code, {i: c["summary"] for i, c in by_id.items() if c["status"] == "FAIL"}


def state(root):
    code, out = nt(root, "state", "--json")
    assert code == 0, out
    return {r["notulendir"]: r["state"] for r in json.loads(out)["notulendirs"]}


@pytest.fixture
def repo(make_repo):
    root = make_repo({"README.md": "repo\n"})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    return root


@pytest.fixture
def plain(make_repo):
    return make_repo(name="plain", git_init=False)


# --- N1: new + .gitignore -----------------------------------------------------------------------

@pytest.mark.regression("18 N1")
def test_n1_new_menulis_kerangka_catatan_asli_dan_gitignore(repo):
    rel = new(repo)
    assert (repo / IGNORE).read_text(encoding="utf-8").rstrip().endswith("*")
    assert git(repo, "status", "--porcelain", "-uall") == ""
    text = path(repo, rel).read_text(encoding="utf-8")
    fm, body = lib.split_frontmatter(text)
    assert (fm["type"], fm["slug"], fm["meeting_date"], fm["status"]) == ("meeting", "sprint-review", "2026-10-02",
                                                                          "DRAFT")
    assert body.startswith("# Sprint review Q4\n")
    assert "## Catatan Asli\n\n> rapat sprint\n> - budi: export csv minggu depan\n>\n> putus: rilis jumat\n" in text
    _, by_id = checks(repo, rel)
    assert by_id[3]["status"] == "PASS" and by_id[4]["status"] == "FAIL"


@pytest.mark.regression("18 N1")
def test_n1_gitignore_juga_di_luar_git_dan_milik_user_tidak_ditimpa(plain, repo):
    new(plain)
    assert (plain / IGNORE).is_file()
    write_files(repo, {IGNORE: "# punya user\n!*.md\n"})
    _, out = nt(repo, "new", "--slug", "lain", "--title", "Lain", "--date", "2026-10-02", "--notes", "catatan")
    assert (repo / IGNORE).read_text(encoding="utf-8") == "# punya user\n!*.md\n"
    assert "git=ya" in out and "PERINGATAN" in out


@pytest.mark.regression("18 N1")
@pytest.mark.parametrize("args,stdin,needle", [
    (["--slug", "Bukan Slug", "--title", "x", "--date", "2026-10-02"], NOTES, "bukan kebab-case"),
    (["--slug", "ok", "--title", "  ", "--date", "2026-10-02"], NOTES, "--title kosong"),
    (["--slug", "ok", "--title", "x", "--date", "2026-02-30"], NOTES, "bukan tanggal"),
    (["--slug", "ok", "--title", "x", "--date", "2026-10-02"], " \n﻿\n", "--notes kosong"),
])
def test_n1_masukan_rusak_ditolak(plain, args, stdin, needle):
    code, out = nt(plain, "new", *args, "--notes", "-", stdin=stdin)
    assert code == 1 and needle in out
    assert not (plain / "analyst" / "notulen").exists() or not any(
        p.is_dir() for p in (plain / "analyst" / "notulen").iterdir())


@pytest.mark.regression("18 N1")
def test_n1_slug_kembar_draft_ditolak(plain):
    rel = new(plain)
    code, out = nt(plain, "new", "--slug", "sprint-review", "--title", "x", "--date", "2026-10-02", "--notes", "y")
    assert code == 1 and f"masih terbuka di {rel}" in out


# --- N2: validator ------------------------------------------------------------------------------

@pytest.mark.regression("18 N2")
def test_n2_notulen_lengkap_lolos(plain):
    rel = new(plain)
    fill(plain, rel)
    code, fails = failed(plain, rel)
    assert code == 0 and fails == {}


@pytest.mark.regression("18 N2")
@pytest.mark.parametrize("old,new_text,cid,needle", [
    ("type: meeting", "type: rapat", 1, "bukan meeting"),
    ("## Agenda\n", "## Agenda Rapat\n", 2, "bukan"),
    ("## Pembahasan\n", "## Keputusan\n", 2, "heading ganda"),
    ("> putus: rilis jumat", "> putus: rilis kamis", 3, "berubah sejak"),
    ("- Budi (PM)\n- Rina (Finance)", "Budi dan Rina", 4, "tanpa butir"),
    ("- **D-1**: Rilis", "- **D-2**: Rilis", 5, "tidak berurutan"),
    ("- **D-1**: Rilis dilakukan Jumat.", "- Rilis dilakukan Jumat.", 5, "format rusak"),
    ("| Budi | 2026-10-09 |", "|  | 2026-10-09 |", 6, "PIC kosong"),
    ("| Budi | 2026-10-09 |", "| Budi | minggu depan |", 6, "bukan YYYY-MM-DD"),
    ("| Budi | 2026-10-09 |", "| Budi | 2026-02-30 |", 6, "bukan YYYY-MM-DD"),
    ("| A-2 |", "| A-3 |", 6, "tidak berurutan"),
    (" — menunggu: Rina", "", 7, "format rusak"),
    ("Ekspor laporan", "Ekspor laporan TBD", 8, "TBD"),
])
def test_n2_satu_aturan_satu_gagal(plain, old, new_text, cid, needle):
    rel = new(plain)
    fill(plain, rel)
    edit(plain, rel, old, new_text)
    code, fails = failed(plain, rel)
    assert code == 1 and cid in fails and needle in fails[cid], fails


@pytest.mark.regression("18 N2")
def test_n2_asumsi_sah_di_draft_ditolak_saat_final(plain):
    rel = new(plain)
    fill(plain, rel)
    edit(plain, rel, "- Finance butuh", "- Asumsi: Finance butuh")
    assert failed(plain, rel)[0] == 0
    code, fails = failed(plain, rel, "--final")
    assert code == 1 and set(fails) == {9}


@pytest.mark.regression("18 N2")
def test_n2_placeholder_di_catatan_asli_dibiarkan(plain):
    rel = new(plain, notes="todo: <isi nanti> TBD\n")
    fill(plain, rel)
    assert failed(plain, rel) == (0, {})


# --- N3: final + DRIFT --------------------------------------------------------------------------

@pytest.mark.regression("18 N3")
def test_n3_final_menolak_validator_fail_dan_jawaban_kosong(plain):
    rel = new(plain)
    code, out = nt(plain, "final", "--notulendir", rel, "--answer", "Final")
    assert code == 1 and "validator FAIL" in out
    fill(plain, rel)
    code, out = nt(plain, "final", "--notulendir", rel, "--answer", "  ")
    assert code == 1 and "--answer kosong" in out
    assert lib.split_frontmatter(path(plain, rel).read_text(encoding="utf-8"))[0]["status"] == "DRAFT"


@pytest.mark.regression("18 N3")
def test_n3_final_menyegel_lalu_suntingan_jadi_drift(plain):
    rel = new(plain)
    fill(plain, rel)
    code, out = nt(plain, "final", "--notulendir", rel, "--answer", "Final, sudah benar")
    assert code == 0 and "1 keputusan · 2 action item · 1 Q" in out, out
    fm, _ = lib.split_frontmatter(path(plain, rel).read_text(encoding="utf-8"))
    assert fm["status"] == "FINAL" and len(fm["final_hash"]) == 12 and fm["final_answer"] == "Final, sudah benar"
    assert state(plain) == {rel: "FINAL"}

    edit(plain, rel, "Rilis dilakukan Jumat.", "Rilis dilakukan Kamis.")
    assert state(plain) == {rel: "DRIFT"}
    assert nt(plain, "final", "--notulendir", rel, "--answer", "Final lagi")[0] == 0
    assert state(plain) == {rel: "FINAL"}


@pytest.mark.regression("18 N3")
def test_n3_slug_sama_boleh_sesudah_final(plain):
    rel = new(plain)
    fill(plain, rel)
    assert nt(plain, "final", "--notulendir", rel, "--answer", "Final")[0] == 0
    (plain / rel).rename(plain / "analyst" / "notulen" / "2601010000-sprint-review")
    new(plain)
    assert sorted(state(plain).values()) == ["DRAFT", "FINAL"]


# --- N4: state ----------------------------------------------------------------------------------

@pytest.mark.regression("18 N4")
def test_n4_state_tanpa_direktori_tetap_json(plain):
    code, out = nt(plain, "state", "--json")
    assert code == 0 and json.loads(out)["notulendirs"] == []


@pytest.mark.regression("18 N4")
def test_n4_state_membaca_keadaan_rusak(plain):
    base = plain / "analyst" / "notulen"
    write_files(plain, {"analyst/notulen/catatan-lepas/NOTULEN.md": "x\n",
                        "analyst/notulen/2610020900-kosong/.keep": "",
                        "analyst/notulen/2610020901-status/NOTULEN.md": "---\nstatus: ARSIP\n---\n# x\n"})
    (base / "2610020902-biner").mkdir()
    (base / "2610020902-biner" / "NOTULEN.md").write_bytes(b"\xff\xfe\x00")
    assert state(plain) == {
        "analyst/notulen/2610020900-kosong": "RUSAK",
        "analyst/notulen/2610020901-status": "RUSAK",
        "analyst/notulen/2610020902-biner": "RUSAK",
        "analyst/notulen/catatan-lepas": "NAMA_TIDAK_SAH",
    }


# --- N6: tanpa commit ---------------------------------------------------------------------------

@pytest.mark.regression("18 N6")
def test_n6_notulen_tidak_pernah_di_commit(repo):
    before = git(repo, "rev-list", "--count", "HEAD")
    rel = new(repo)
    fill(repo, rel)
    code, out = nt(repo, "final", "--notulendir", rel, "--answer", "Final")
    assert code == 0 and "tanpa commit" in out
    assert git(repo, "rev-list", "--count", "HEAD") == before
    assert git(repo, "status", "--porcelain", "-uall") == ""


# --- N5: template ↔ skrip -----------------------------------------------------------------------

@pytest.mark.regression("18 N5")
def test_n5_kerangka_skrip_sama_dengan_template():
    template = (PLUGINS / "analyst" / "skills" / "notulen" / "templates" / "notulen-template.md").read_text(
        encoding="utf-8")
    block = template.split("````markdown\n", 1)[1].split("\n````", 1)[0] + "\n"
    mod = load_module(NOTULEN, "notulen_18")
    text = mod.skeleton("sprint-review", "Sprint review Q4", "2026-10-02", "2026-10-03", "catatan kasar")
    fm, _ = lib.split_frontmatter(text)
    expected = (block.replace("<slug>", "sprint-review")
                .replace("meeting_date: <YYYY-MM-DD>", "meeting_date: 2026-10-02")
                .replace("created: <YYYY-MM-DD>", "created: 2026-10-03")
                .replace("<12 hex>", fm["source_hash"])
                .replace("<judul rapat>", "Sprint review Q4")
                .replace("<catatan kasar apa adanya>", "catatan kasar"))
    assert text == expected
    headings = [l[3:] for l in block.splitlines() if l.startswith("## ")]
    assert tuple(headings) == mod.H2
