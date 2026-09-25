"""Regresi Langkah 8.A (A2–A12) — skenario = bagian Reproduksi issues/08a-sisa-lintas-analyst.md.

Fixture `fixtures/ticket_valid.md` = F0: TICKET.md DRAFT sah (elisitasi CLOSED, kartu lolos
kedua validator, belum direview).
"""
import json
from pathlib import Path

import pytest

from conftest import PLUGINS, git, load_module, run_script

COMMON = PLUGINS / "analyst" / "skills" / "_common"
TICKET = COMMON / "ticket.py"
VALIDATE = COMMON / "validate_doc.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
analyst_lib = load_module(COMMON / "analyst_lib.py", "analyst_lib_8a")


class Run:
    """Hasil `run_script` dengan nama pendek: code, out, err, json(), traceback."""

    def __init__(self, proc):
        self.code, self.out, self.err = proc.returncode, proc.stdout, proc.stderr
        self.traceback = "Traceback" in proc.stderr

    def json(self):
        return json.loads(self.out)


@pytest.fixture
def repo(make_repo):
    """Repo git berisi satu TICKET.md DRAFT sah ter-commit."""
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    return root


@pytest.fixture
def plain(make_repo):
    """Ruang kerja tanpa git."""
    return make_repo(name="plain", git_init=False)


def tk(root, *args, cwd=None, stdin=""):
    return Run(run_script(TICKET, *args, cwd=cwd or root, stdin=stdin))


def vd(root, kind):
    return Run(run_script(VALIDATE, "--kind", kind, "--ticketdir", TDIR, cwd=root))


def edit(root, old, new):
    p = root / TDIR / "TICKET.md"
    text = p.read_text(encoding="utf-8")
    assert old in text, old
    p.write_text(text.replace(old, new), encoding="utf-8")


def states(root):
    return {r["ticketdir"]: r["state"] for r in tk(root, "state", "--all", "--json").json()["ticketdirs"]}


def test_fixture_lolos_kedua_validator(repo):
    assert vd(repo, "ticket").code == 0 and vd(repo, "elicit").code == 0


# --- A2 ------------------------------------------------------------------------------------------

@pytest.mark.regression("A2")
def test_a2_review_menolak_elisitasi_rusak(repo):
    edit(repo, "Tinggi — dua klien besar menunggu.", "_(belum terjawab)_")
    assert vd(repo, "elicit").code == 1
    r = tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS")
    assert r.code == 1 and "--kind elicit FAIL" in r.out


@pytest.mark.regression("A2")
def test_a2_approve_menolak_elisitasi_rusak(repo):
    edit(repo, "### Pertanyaan Terbuka\n\n- Tidak ada.\n",
         "### Pertanyaan Terbuka\n\n- **Q-2** [MEMBLOKIR]: Berapa maksimal cicilan? — menunggu: Budi\n")
    p = repo / TDIR / "TICKET.md"          # vonis PASS atas sidik sekarang, seolah tercatat jalur lama
    text = p.read_text(encoding="utf-8")
    digest = f"{analyst_lib.content_hash(text, 'card')}/{analyst_lib.content_hash(text, 'elicit')}"
    p.write_text(analyst_lib.set_frontmatter_field(text, "review", f"PASS @{digest}"), encoding="utf-8")
    r = tk(repo, "approve", "--ticketdir", TDIR, "--answer", "Setujui", "--no-commit")
    assert r.code == 1 and "--kind elicit FAIL" in r.out
    assert "status: DRAFT" in p.read_text(encoding="utf-8")


# --- A3 ------------------------------------------------------------------------------------------

BLOCK = ("## Ticket Review\n- Verdict: BLOCKED\n- Ronde: 1\n- BLOCKER: 0 [MEKANIS] · 1 [SEMANTIK]\n\n"
         "**BLOCKER:**\n- [SEMANTIK] `TICKET.md:30` (fokus #2) — AC tidak teramati — QA tidak bisa menguji\n\n"
         "**ADVISORY:**\n- —\n")


@pytest.mark.regression("A3")
def test_a3_blok_review_tersimpan_dan_verdict_dicocokkan(repo):
    r = tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS", "--report", "-", stdin=BLOCK)
    assert r.code == 1 and "tidak sama" in r.out
    assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "BLOCKED", "--report", "-", stdin=BLOCK).code == 0
    saved = (repo / TDIR / "review.md").read_text(encoding="utf-8")
    assert saved.startswith("<!-- ronde 1/2 · BLOCKED @") and "## Ticket Review" in saved
    assert f"review_report={TDIR}/review.md" in tk(repo, "check", "--gate", "spec", "--ticketdir", TDIR).out


@pytest.mark.regression("A3")
def test_a3_approve_meng_commit_review_md(repo):
    block = BLOCK.replace("Verdict: BLOCKED", "Verdict: PASS")
    assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS", "--report", "-", stdin=block).code == 0
    assert tk(repo, "approve", "--ticketdir", TDIR, "--answer", "ok").code == 0
    committed = git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert f"{TDIR}/review.md" in committed and f"{TDIR}/TICKET.md" in committed


@pytest.mark.regression("A3")
def test_a3_review_report_basi_tidak_dirujuk(repo):
    assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "BLOCKED", "--report", "-", stdin=BLOCK).code == 0
    assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "BLOCKED").code == 0   # ronde 2 tanpa blok
    assert "review_report=-" in tk(repo, "check", "--gate", "spec", "--ticketdir", TDIR).out


# --- A4 ------------------------------------------------------------------------------------------

@pytest.mark.regression("A4")
def test_a4_ronde_reset_saat_elisitasi_berubah(repo):
    for _ in range(2):
        assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "BLOCKED").code == 0
    edit(repo, "Hanya pelanggan korporat.", "Hanya pelanggan korporat di Jabodetabek.")
    assert "review_basi=elisitasi" in tk(repo, "check", "--gate", "spec", "--ticketdir", TDIR).out
    r = tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS")
    assert r.code == 0 and "ronde 1/2" in r.out
    assert tk(repo, "approve", "--ticketdir", TDIR, "--answer", "ok", "--no-commit").code == 0


@pytest.mark.regression("A4")
def test_a4_kartu_berubah_tetap_kena_plafon(repo):
    for _ in range(2):
        tk(repo, "review", "--ticketdir", TDIR, "--verdict", "BLOCKED")
    edit(repo, "- Denda keterlambatan — ditunda ke fase berikutnya",
         "- Denda keterlambatan — ditunda ke fase berikutnya atas keputusan peminta")
    assert "review_basi=kartu" in tk(repo, "check", "--gate", "spec", "--ticketdir", TDIR).out
    assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS").code == 1


# --- A5 ------------------------------------------------------------------------------------------

@pytest.mark.regression("A5")
def test_a5_set_frontmatter_field_menolak_tanpa_pagar():
    for text in ("# judul\n", "---\nstatus: DRAFT\n# tanpa pagar penutup\n"):
        with pytest.raises(ValueError):
            analyst_lib.set_frontmatter_field(text, "status", "CANCELLED")


@pytest.mark.regression("A5")
def test_a5_cancel_berkas_tanpa_frontmatter(plain):
    rel = "analyst/tickets/2609231500-rusak"
    (plain / rel).mkdir(parents=True)
    (plain / rel / "TICKET.md").write_text("# Tiket\n\n## Catatan Elisitasi\n\nisi\n", encoding="utf-8")
    assert tk(plain, "cancel", "--ticketdir", rel, "--reason", "dibatalkan user").code == 0
    text = (plain / rel / "TICKET.md").read_text(encoding="utf-8")
    assert text.startswith("---\nstatus: CANCELLED\n") and text.rstrip().endswith("isi")
    assert states(plain)[rel] == "DIBATALKAN"


# --- A6 ------------------------------------------------------------------------------------------

@pytest.mark.regression("A6")
def test_a6_new_dan_check_dari_subdir_mencetak_root(repo):
    sub = repo / "src" / "sub"
    sub.mkdir(parents=True)
    r = tk(repo, "new", "--slug", "sub", "--type", "FEATURE", cwd=sub)
    assert r.code == 0 and f"root={repo}" in r.out
    assert not (sub / "analyst").exists()
    assert f"root={repo}" in tk(repo, "check", "--gate", "spec", "--ticketdir", TDIR, cwd=sub).out


# --- A7 ------------------------------------------------------------------------------------------

@pytest.mark.regression("A7")
def test_a7_requester_kosong_gagal_domain_terms_kosong_tetap_list(repo):
    edit(repo, "requester: Rina (Head of Sales)", "requester:")
    edit(repo, "domain_terms: []", "domain_terms:")
    r = vd(repo, "elicit")
    assert r.code == 1 and "requester kosong" in r.out
    assert "[8] domain_terms                   : PASS" in r.out


@pytest.mark.regression("A7")
@pytest.mark.parametrize("value", ["dua", ""])
def test_a7_review_round_rusak_fail_rapi(repo, value):
    edit(repo, "review_round: 0", f"review_round: {value}".rstrip())
    r = tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS")
    assert r.code == 1 and not r.traceback and "bukan bilangan" in r.err


# --- A8 ------------------------------------------------------------------------------------------

@pytest.mark.regression("A8")
def test_a8_nomor_baris_kebocoran_relatif_berkas(repo):
    edit(repo, "hanya mengenal status Belum Bayar dan Lunas.", "hanya menyimpan status di database.")
    text = (repo / TDIR / "TICKET.md").read_text(encoding="utf-8")
    lineno = next(i for i, l in enumerate(text.splitlines(), 1) if "database" in l)
    assert f"baris {lineno}: istilah teknis «database»" in vd(repo, "ticket").out


# --- A9 ------------------------------------------------------------------------------------------

@pytest.mark.regression("A9")
def test_a9_closed_dengan_asumsi_gagal(repo):
    edit(repo, "Hanya pelanggan korporat.\n", "Asumsi: hanya pelanggan korporat.\n")
    r = vd(repo, "elicit")
    assert r.code == 1 and "[9] Asumsi terkonfirmasi" in r.out


@pytest.mark.regression("A9")
def test_a9_open_dengan_asumsi_lolos(repo):
    edit(repo, "Hanya pelanggan korporat.\n", "Asumsi: hanya pelanggan korporat.\n")
    edit(repo, "elicitation: CLOSED", "elicitation: OPEN")
    assert vd(repo, "elicit").code == 0


@pytest.mark.regression("A9")
def test_a9_domain_term_wajib_berjejak(repo):
    edit(repo, "domain_terms: []", "domain_terms: [API]")
    r = vd(repo, "elicit")
    assert r.code == 1 and "tanpa jejak di Permintaan Asli/Log: API" in r.out
    row = "| 1 | 2026-09-23 | Invoice mana yang boleh dicicil? | Di atas 50 juta | Rina |"
    edit(repo, row, row + '\n| 2 | 2026-09-23 | Apakah "API" nama produk mitra? | Ya | Rina |')
    assert vd(repo, "elicit").code == 0


# --- A10 -----------------------------------------------------------------------------------------

@pytest.mark.regression("A10")
def test_a10_nama_tidak_sah_dan_cancel_kosong(plain):
    (plain / "analyst/tickets/draft-lama").mkdir(parents=True)
    (plain / "analyst/tickets/2609231600-kosong").mkdir()
    assert states(plain)["analyst/tickets/draft-lama"] == "NAMA_TIDAK_SAH"
    assert tk(plain, "new", "--slug", "lama", "--type", "FEATURE").code == 0
    r = tk(plain, "cancel", "--ticketdir", "analyst/tickets/2609231600-kosong", "--reason", "x")
    assert r.code == 0 and not (plain / "analyst/tickets/2609231600-kosong").exists()


@pytest.mark.regression("A10")
def test_a10_cancel_direktori_tanpa_ticket_berisi_berkas_lain_ditolak(plain):
    d = plain / "analyst/tickets/2609231600-sisa"
    d.mkdir(parents=True)
    (d / "catatan.txt").write_text("x", encoding="utf-8")
    assert tk(plain, "cancel", "--ticketdir", "analyst/tickets/2609231600-sisa", "--reason", "x").code == 1
    assert d.is_dir()


# --- A11 -----------------------------------------------------------------------------------------

@pytest.mark.regression("A11")
def test_a11_commit_gagal_informatif_dan_exit_3(repo):
    git(repo, "rm", "-rq", "--cached", "analyst")
    (repo / ".gitignore").write_text("analyst/\n", encoding="utf-8")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "chore: ignore analyst")
    assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS").code == 0
    r = tk(repo, "approve", "--ticketdir", TDIR, "--answer", "ok")
    assert r.code == 3 and "ignored" in r.out and "hint:" not in r.out


@pytest.mark.regression("A11")
def test_a11_git_error_line():
    assert analyst_lib.git_error_line("hint: a\nfatal: index.lock ada\nhint: b") == "fatal: index.lock ada"


# --- A12 -----------------------------------------------------------------------------------------

@pytest.mark.regression("A12")
def test_a12_type_huruf_kecil_diterima(plain):
    assert tk(plain, "new", "--slug", "x", "--type", "bug").code == 0


@pytest.mark.regression("A12")
def test_a12_ref_sesudah_ready_tanpa_drift_dan_ter_commit(repo):
    assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS").code == 0
    assert tk(repo, "approve", "--ticketdir", TDIR, "--answer", "ok").code == 0
    assert tk(repo, "ref", "--ticketdir", TDIR, "--ref", "FIN-123").code == 0
    assert states(repo)[TDIR] == "READY"
    assert git(repo, "log", "-1", "--format=%s").strip() == "docs(ticket): ref TICKET cicilan"
    assert 'external_ref: "FIN-123"' in (repo / TDIR / "TICKET.md").read_text(encoding="utf-8")
