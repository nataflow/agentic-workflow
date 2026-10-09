"""Validator CHARTER.md plugin `product`: enam pilar kartu, tanda per mode, ID Scope, ukuran, dan bukti kode."""
import pytest

from product_helpers import TD, charter, edit, empty_ws, validate, ws  # noqa: F401  (fixture)


def _closed_card(ws):
    ws.to_closed()
    ws.write_card()


def _fails(ws, check: str):
    proc = validate(ws.root, "charter")
    assert proc.returncode == 1, proc.stdout
    line = next(l for l in proc.stdout.splitlines() if check in l)
    assert ": FAIL" in line, proc.stdout
    return proc.stdout


def test_kartu_lengkap_lolos_di_ketiga_mode(ws):
    _closed_card(ws)
    proc = validate(ws.root, "charter")
    assert proc.returncode == 0, proc.stdout


def test_kartu_ditolak_selama_elisitasi(ws):
    assert ws.new().returncode == 0
    ws.answer()
    ws.write_card()
    assert "status ELICITATION" in _fails(ws, "Frontmatter")


def test_heading_pilar_wajib_urut(ws):
    _closed_card(ws)
    edit(ws.root, "## Success Criteria", "## Kriteria Sukses")
    _fails(ws, "Struktur")


def test_aktor_proses_wajib_terdaftar(ws):
    _closed_card(ws)
    edit(ws.root, "3. **Sistem** menghitung", "3. **Akuntan** menghitung")
    assert "aktor `Akuntan`" in _fails(ws, "Business Process")


def test_proses_minimal_dua_langkah_berurutan(ws):
    _closed_card(ws)
    edit(ws.root, "4. **Pemilik Warung** melihat", "5. **Pemilik Warung** melihat")
    assert "tidak urut" in _fails(ws, "Business Process")


def test_tanda_aktor_per_mode(ws):
    _closed_card(ws)
    if ws.mode == "NEW_PRODUCT":
        edit(ws.root, "- **Kasir** —", "- **Kasir** [BARU] —")
        assert "NEW_PRODUCT belum punya aktor" in _fails(ws, "Actors")
    else:
        edit(ws.root, "- **Kasir** [BARU] —", "- **Kasir** —")
        assert "tanpa tanda [ADA]/[BARU]" in _fails(ws, "Actors")


def test_improvement_wajib_kondisi_sekarang_dan_target(ws):
    if ws.mode != "IMPROVEMENT":
        pytest.skip("khusus IMPROVEMENT")
    _closed_card(ws)
    edit(ws.root, "### Kondisi Target", "### Kondisi Nanti")
    _fails(ws, "Business Process")


def test_subheading_proses_hanya_untuk_improvement(ws):
    if ws.mode == "IMPROVEMENT":
        pytest.skip("IMPROVEMENT memang bersubheading")
    _closed_card(ws)
    edit(ws.root, "## Business Process\n\n", "## Business Process\n\n### Kondisi Target\n\n")
    assert "hanya untuk mode IMPROVEMENT" in _fails(ws, "Business Process")


def test_aturan_wajib_pengecualian_dan_tanda_improvement(ws):
    _closed_card(ws)
    edit(ws.root, " — pengecualian: tidak ada", "")
    _fails(ws, "Business Rules")
    edit(ws.root, "foto nota\n\n## Success", "foto nota — pengecualian: tidak ada\n\n## Success")
    if ws.mode == "IMPROVEMENT":
        edit(ws.root, "**BR-1** [BARU]:", "**BR-1**:")
        assert "tanpa tanda [TETAP]/[UBAH]/[BARU]" in _fails(ws, "Business Rules")
    else:
        edit(ws.root, "**BR-1**:", "**BR-1** [UBAH]:")
        assert "hanya untuk mode IMPROVEMENT" in _fails(ws, "Business Rules")


def test_aturan_nihil_beralasan_sah(ws):
    _closed_card(ws)
    p = ws.root / TD / "CHARTER.md"
    text = p.read_text(encoding="utf-8")
    start, end = text.index("- **BR-1**"), text.index("\n\n## Success Criteria")
    p.write_text(text[:start] + "- Tidak ada aturan khusus — peminta tidak menyebut aturan" + text[end:],
                 encoding="utf-8")
    assert validate(ws.root, "charter").returncode == 0


def test_kriteria_sukses_wajib_berangka(ws):
    _closed_card(ws)
    edit(ws.root, "ukuran: ≤ 1 menit sesudah toko tutup, selama 2 minggu pertama", "ukuran: secepatnya")
    assert "tanpa angka" in _fails(ws, "Success Criteria")


def test_scope_id_unik_berurutan_untuk_handoff(ws):
    _closed_card(ws)
    edit(ws.root, "- **S3**:", "- **S2**:")
    assert "tidak unik dan urut" in _fails(ws, "Scope")


def test_scope_tidak_termasuk_beralasan(ws):
    _closed_card(ws)
    edit(ws.root, "- Pengelolaan stok bahan — belum dibutuhkan pada versi pertama", "- Pengelolaan stok bahan")
    assert "tanpa `— <alasan>`" in _fails(ws, "Scope")


def test_placeholder_ditolak(ws):
    _closed_card(ws)
    edit(ws.root, "- **S3**: Laporan laba harian", "- **S3**: <butir kerja>")
    _fails(ws, "Nol placeholder")


def test_bukti_kode_per_mode(ws):
    _closed_card(ws)
    if ws.mode == "NEW_PRODUCT":
        edit(ws.root, "1. **Kasir** mencatat tiap penjualan beserta nominalnya",
             "1. **Kasir** mencatat tiap penjualan beserta nominalnya `src/kasir.go:1`")
        assert "mode NEW_PRODUCT" in _fails(ws, "Bukti kode")
    elif ws.mode == "IMPROVEMENT":
        edit(ws.root, "`src/kasir.go:2`", "`src/kasir.go:99`")
        assert "melampaui" in _fails(ws, "Bukti kode")
        edit(ws.root, " `src/kasir.go:99`", "")
        assert "Kondisi Sekarang tanpa satu pun bukti" in _fails(ws, "Bukti kode")
    else:
        edit(ws.root, "1. **Kasir** mencatat tiap penjualan beserta nominalnya",
             "1. **Kasir** mencatat tiap penjualan beserta nominalnya `src/hilang.go:1`")
        assert "tidak ada" in _fails(ws, "Bukti kode")


def test_bukti_kode_di_catatan_produk_baru_ditolak(empty_ws):
    assert empty_ws.new().returncode == 0
    empty_ws.answer()
    edit(empty_ws.root, "Kasir mencatat penjualan harian.", "Kasir mencatat penjualan harian `src/a.go:1`.")
    proc = validate(empty_ws.root, "notes")
    assert proc.returncode == 1 and "mode NEW_PRODUCT" in proc.stdout


def test_catatan_terbuka_boleh_pilar_kosong_tertutup_tidak(ws):
    assert ws.new().returncode == 0
    assert validate(ws.root, "notes").returncode == 0
    edit(ws.root, "status: ELICITATION", "status: DRAFT")
    proc = validate(ws.root, "notes")
    assert proc.returncode == 1 and "belum terjawab" in proc.stdout


def test_approved_disunting_gagal_konten(ws):
    ws.to_approved()
    assert validate(ws.root, "charter").returncode == 0
    edit(ws.root, "- **S3**: Laporan laba harian", "- **S3**: Laporan laba bulanan")
    _fails(ws, "Konten = yang disetujui")


def test_judul_maksimal_dua_belas_kata(ws):
    _closed_card(ws)
    edit(ws.root, "# Pencatatan keuangan UMKM", "# " + " ".join(["kata"] * 13))
    assert "lebih dari 12 kata" in _fails(ws, "Struktur")


def test_validator_tanpa_charter(empty_ws):
    proc = validate(empty_ws.root, "notes")
    assert proc.returncode == 1 and "tidak ada" in proc.stdout
    assert charter(empty_ws.root, "state").returncode == 0
