"""Siklus hidup charterdir plugin `product`: guard konteks minimum, mode × ruang kerja, segel, review, approve."""
import json
import os
import re
import subprocess
import sys

from conftest import GIT_ENV, PLUGINS, git, load_module
from product_helpers import (  # noqa: F401  (fixture ws, empty_ws)
    CHARTER,
    TD,
    charter,
    edit,
    empty_ws,
    path_of,
    resolved,
    review_block,
    ws,
)

LIB = load_module(PLUGINS / "product" / "skills" / "_common" / "charter_lib.py", "product_charter_lib")


# ── guard konteks minimum ──

def test_guard_menolak_permintaan_terlalu_umum(empty_ws):
    proc = charter(empty_ws.root, "guard", "--mode", "NEW_PRODUCT", "--lingkup", "keuangan")
    assert proc.returncode == 1
    assert "Untuk siapa (--untuk) kosong" in proc.stdout and "Masalah utama (--masalah) kosong" in proc.stdout


def test_guard_sebutan_orang_umum_hanya_ditolak_untuk_produk_baru(empty_ws):
    args = ("--untuk", "pelanggan", "--masalah", "harus antre lama di kasir", "--lingkup", "menu pembayaran")
    produk = charter(empty_ws.root, "guard", "--mode", "NEW_PRODUCT", *args)
    fitur = charter(empty_ws.root, "guard", "--mode", "NEW_FEATURE", *args)
    assert produk.returncode == 1 and "terlalu umum" in produk.stdout
    assert fitur.returncode == 0, fitur.stdout


def test_guard_json_menyebut_label_mode(empty_ws):
    proc = charter(empty_ws.root, "guard", "--mode", "IMPROVEMENT", "--untuk", "Kasir", "--masalah", "terserah",
                   "--lingkup", "pencatatan penjualan", "--json")
    data = json.loads(proc.stdout)
    assert data["status"] == "FAIL" and data["labels"]["lingkup"] == "Fitur"
    assert data["problems"] == ["Yang salah atau kurang (--masalah) `terserah` terlalu umum"]


def test_keluhan_tanpa_isi_ditolak():
    problems = LIB.context_problems("IMPROVEMENT", {"untuk": "PIC task", "masalah": "kurang", "lingkup": "status task"})
    assert problems == ["Yang salah atau kurang (--masalah) `kurang` terlalu umum"]
    assert LIB.context_problems("IMPROVEMENT", {"untuk": "PIC task", "masalah": "task selesai bisa dibuka lagi",
                                                "lingkup": "status task"}) == []


def test_context_problems_frasa_bersegmen_tetap_sah():
    assert LIB.context_problems("NEW_PRODUCT", {"untuk": "semua cabang toko roti", "masalah": "stok selisih",
                                                "lingkup": "ritel"}) == []


# ── new: mode × ruang kerja ──

def test_new_di_folder_kosong_tanpa_git(empty_ws):
    proc = empty_ws.new()
    assert proc.returncode == 0, proc.stdout
    assert "git=tidak" in proc.stdout and "workspace=EMPTY" in proc.stdout
    text = path_of(empty_ws.root).read_text(encoding="utf-8")
    assert "- **Untuk siapa**: Pemilik UMKM warung makan" in text
    assert "> saya ingin membuat aplikasi keuangan untuk UMKM" in text


def test_new_menolak_konteks_umum_tanpa_menulis(empty_ws):
    proc = charter(empty_ws.root, "new", "--slug", "keuangan", "--mode", "NEW_PRODUCT", "--untuk", "semua orang",
                   "--masalah", "kas berantakan", "--lingkup", "keuangan", "--requester", "Budi", "--request", "x")
    assert proc.returncode == 1 and "konteks minimum" in proc.stdout
    assert not (empty_ws.root / "product").exists()


def test_mode_codebase_ditolak_di_folder_kosong(empty_ws):
    empty_ws.mode = "IMPROVEMENT"
    proc = empty_ws.new()
    assert proc.returncode == 1 and "butuh codebase" in proc.stdout


def test_produk_baru_di_codebase_butuh_konfirmasi(ws):
    if ws.mode == "NEW_PRODUCT":
        (ws.root / "go.mod").write_text("module x\n", encoding="utf-8")
    ws.mode = "NEW_PRODUCT"
    proc = ws.new()
    assert proc.returncode == 1 and "--confirm-workspace" in proc.stdout
    proc = ws.new(extra=("--confirm-workspace",))
    assert proc.returncode == 0, proc.stdout


def test_new_menolak_home_sebagai_ruang_kerja(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = {**os.environ, **GIT_ENV, "HOME": str(home)}
    proc = subprocess.run([sys.executable, str(CHARTER), "--root", str(home), "new", "--slug", "a", "--mode",
                           "NEW_PRODUCT", "--untuk", "Pemilik UMKM", "--masalah", "kas manual", "--lingkup",
                           "keuangan", "--requester", "b", "--request", "c"],
                          capture_output=True, text=True, env=env)
    assert proc.returncode == 1 and "direktori home" in proc.stdout


def test_slug_kembar_ditolak_direktori_kosong_dipakai_ulang(empty_ws):
    (empty_ws.root / TD).mkdir(parents=True)
    first = empty_ws.new()
    assert first.returncode == 0 and "dipakai ulang" in first.stdout
    again = empty_ws.new()
    assert again.returncode == 1 and "sudah dipakai" in again.stdout


def test_state_mengabaikan_subdirektori_kode(empty_ws):
    (empty_ws.root / "product" / "handler").mkdir(parents=True)
    (empty_ws.root / "product" / "handler" / "x.go").write_text("package handler\n", encoding="utf-8")
    empty_ws.mode = "NEW_FEATURE"
    assert empty_ws.new().returncode == 0
    data = json.loads(charter(empty_ws.root, "state", "--json").stdout)
    assert [r["charterdir"] for r in data["charterdirs"]] == [TD]
    assert data["charterdirs"][0]["state"] == "ELICITATION"


# ── close & segel ──

def test_close_menolak_pilar_belum_terjawab_dan_mengembalikan_berkas(ws):
    assert ws.new().returncode == 0
    before = path_of(ws.root).read_text(encoding="utf-8")
    proc = charter(ws.root, "close", "--charterdir", TD)
    assert proc.returncode == 1 and "belum terjawab" in proc.stdout
    assert path_of(ws.root).read_text(encoding="utf-8") == before


def test_close_menyegel_dan_commit(ws):
    ws.to_closed()
    fm = path_of(ws.root).read_text(encoding="utf-8")
    assert "status: DRAFT" in fm and "elicit_log: 2" in fm
    assert "docs(product): elisitasi keuangan-umkm" in git(ws.root, "log", "-1", "--format=%s")


def test_close_menolak_asumsi_dan_pertanyaan_memblokir(ws):
    assert ws.new().returncode == 0
    ws.answer()
    edit(ws.root, "Kasir mencatat penjualan harian.", "Asumsi: kasir mencatat penjualan harian.")
    assert charter(ws.root, "close", "--charterdir", TD).returncode == 1
    edit(ws.root, "Asumsi: kasir", "Kasir")
    edit(ws.root, "### Pertanyaan Terbuka\n\n- Tidak ada.",
         "### Pertanyaan Terbuka\n\n- **Q-1** [MEMBLOKIR]: Berapa batas nota? — menunggu: Budi")
    proc = charter(ws.root, "close", "--charterdir", TD)
    assert proc.returncode == 1 and "MEMBLOKIR" in proc.stdout


def test_konteks_awal_yang_disunting_ditolak(ws):
    assert ws.new().returncode == 0
    ws.answer()
    p = path_of(ws.root)
    p.write_text(re.sub(r"(### Konteks Awal\n\n- \*\*[^*]+\*\*: )", r"\1diubah sesudah new ",
                        p.read_text(encoding="utf-8"), count=1), encoding="utf-8")
    proc = charter(ws.root, "close", "--charterdir", TD)
    assert proc.returncode == 1 and "Konteks Awal berubah" in proc.stdout


def test_catatan_disunting_sesudah_ditutup_ditolak_spec(ws):
    ws.to_closed()
    edit(ws.root, "Kasir mencatat penjualan harian.", "Kasir dan pemilik mencatat penjualan harian.")
    proc = charter(ws.root, "check", "--gate", "spec", "--charterdir", TD)
    assert proc.returncode == 1 and "berubah sesudah ditutup" in proc.stdout


# ── review & approve ──

def test_review_mengikat_sidik_disk(ws):
    ws.to_closed()
    ws.write_card()
    stale = ws.sidik()
    edit(ws.root, "- **S3**: Laporan laba harian", "- **S3**: Laporan laba harian per hari")
    proc = ws.review(sidik=stale)
    assert proc.returncode == 1 and "≠ sidik disk" in proc.stdout


def test_review_menolak_blok_tidak_konsisten(ws):
    ws.to_closed()
    ws.write_card()
    block = review_block("PASS", ws.sidik(), blockers=1)
    proc = charter(ws.root, "review", "--charterdir", TD, "--verdict", "PASS", "--report", "-", stdin=block)
    assert proc.returncode == 1 and "Verdict PASS dengan 1 BLOCKER" in proc.stdout


def test_review_pass_menjadi_keadaan_review(ws):
    ws.to_reviewed()
    row = json.loads(charter(ws.root, "state", "--json").stdout)["charterdirs"][0]
    assert row["state"] == "REVIEW"
    assert (ws.root / TD / "review.md").is_file()


def test_plafon_dua_ronde(ws):
    ws.to_closed()
    ws.write_card()
    assert ws.review("BLOCKED", blockers=1).returncode == 0
    assert ws.review("BLOCKED", rnd=2, blockers=1).returncode == 0
    out = charter(ws.root, "check", "--gate", "spec", "--charterdir", TD).stdout
    assert resolved(out)["ronde"] == "habis"
    proc = ws.review("PASS", rnd=3)
    assert proc.returncode == 1 and "plafon 2 ronde" in proc.stdout


def test_approve_menuntut_review_segar(ws):
    ws.to_closed()
    ws.write_card()
    proc = charter(ws.root, "approve", "--charterdir", TD, "--answer", "Setujui")
    assert proc.returncode == 1 and "bukan `PASS @" in proc.stdout


def test_approve_lalu_drift(ws):
    ws.to_approved()
    assert "docs(product): kunci CHARTER keuangan-umkm APPROVED" in git(ws.root, "log", "-1", "--format=%s")
    tracked = git(ws.root, "show", "--name-only", "--format=", "HEAD").split()
    assert sorted(tracked) == [f"{TD}/CHARTER.md", f"{TD}/review.md"]
    row = json.loads(charter(ws.root, "state", "--all", "--json").stdout)["charterdirs"][0]
    assert row["state"] == "APPROVED"
    edit(ws.root, "- **S3**: Laporan laba harian", "- **S3**: Laporan laba mingguan")
    row = json.loads(charter(ws.root, "state", "--json").stdout)["charterdirs"][0]
    assert row["state"] == "DRIFT"


# ── reopen, revise, cancel ──

def test_reopen_ke_elisitasi_menulis_log_dan_membuka_siklus_baru(ws):
    ws.to_approved()
    proc = charter(ws.root, "reopen", "--charterdir", TD, "--to", "elicitation", "--reason", "batas nota berubah")
    assert proc.returncode == 0, proc.stdout
    text = path_of(ws.root).read_text(encoding="utf-8")
    assert "| 3 |" in text and "| Dibuka ulang | batas nota berubah | product:spec |" in text
    assert "status: ELICITATION" in text
    edit(ws.root, "di atas Rp1.000.000 wajib", "di atas Rp2.000.000 wajib")
    assert charter(ws.root, "close", "--charterdir", TD).returncode == 0
    out = charter(ws.root, "check", "--gate", "spec", "--charterdir", TD).stdout
    assert resolved(out)["ronde"] == "1" and resolved(out)["review_segar"] == "tidak"


def test_close_menolak_catatan_berubah_tanpa_reopen(ws):
    ws.to_closed()
    edit(ws.root, "status: DRAFT", "status: ELICITATION")
    edit(ws.root, "Kasir mencatat penjualan harian.", "Kasir mencatat penjualan tiap jam.")
    proc = charter(ws.root, "close", "--charterdir", TD)
    assert proc.returncode == 1 and "Dibuka ulang" in proc.stdout


def test_reopen_ke_draft_dari_approved(ws):
    ws.to_approved()
    proc = charter(ws.root, "reopen", "--charterdir", TD, "--to", "draft", "--reason", "tambah S4")
    assert proc.returncode == 0
    row = json.loads(charter(ws.root, "state", "--json").stdout)["charterdirs"][0]
    assert row["state"] == "DRAFT"


def test_revise_plafon_tiga(ws):
    ws.to_closed()
    for n in (1, 2, 3):
        assert charter(ws.root, "revise", "--charterdir", TD).returncode == 0
    proc = charter(ws.root, "revise", "--charterdir", TD)
    assert proc.returncode == 1 and "plafon 3 revisi" in proc.stdout


def test_cancel_approved_butuh_force(ws):
    ws.to_approved()
    proc = charter(ws.root, "cancel", "--charterdir", TD, "--reason", "tidak jadi")
    assert proc.returncode == 1 and "--force" in proc.stdout
    proc = charter(ws.root, "cancel", "--charterdir", TD, "--reason", "tidak jadi", "--force")
    assert proc.returncode == 0
    assert "docs(product): batalkan CHARTER keuangan-umkm" in git(ws.root, "log", "-1", "--format=%s")


def test_tanpa_git_tetap_jalan(empty_ws):
    empty_ws.to_approved()
    assert "status: APPROVED" in path_of(empty_ws.root).read_text(encoding="utf-8")


def test_commit_draft(ws):
    ws.to_closed()
    ws.write_card()
    proc = charter(ws.root, "commit", "--charterdir", TD, "--stage", "draft")
    assert proc.returncode == 0, proc.stdout
    assert "docs(product): draft CHARTER keuangan-umkm" in git(ws.root, "log", "-1", "--format=%s")


def test_detect_workspace():
    assert LIB.detect_workspace(PLUGINS)["workspace"] == "CODEBASE"
