# Migrasi `backend` v0.24.1 → v0.25.0

Review lapangan hkm 19–26 Nov 2026 (B1, B2, B3, B10): pangkas giliran user dan retry yang paling sering. Tidak ada
format dokumen yang wajib dimigrasi.

## Yang berubah

- **Simbol di luar anchor tidak lagi menghentikan rantai (B1).** `close_brief.py` memvonisnya `WARN` (exit 0), bukan
  `SYMBOL` (exit 1). `architect` tidak menulis `HALT.md` `verdict: SYMBOL`; daftar simbolnya ditulis ke
  `{taskdir}/.explore/simbol-NN.md` dan dinilai `code-reviewer` di Fase 4 (suntingan pendukung sah atau
  `P1 — simbol di luar anchor`). `STRAY` dan `SCOPE` tetap menahan.
- **`symbol_map.py` lebih tepat (B1).** Deklarasi lama dibandingkan dengan nama berkualifikasi tipe induk
  (`Foo::default`; `impl Trait for Type` dinamai `Type`), fn di blok tipe/`impl` yang lahir di commit yang sama
  masuk `new_declared`, `fn new` Rust dikenali, dan lifecycle test (`@BeforeEach`, `setUp`/`tearDown` di berkas
  test), `main`, serta `default` masuk kunci baru `diabaikan`.
- **`journey.py add` lebih longgar (B2).** Target tetap 280 karakter; 281–360 diterima dengan `WARN` (exit 0), di
  atas 360 ditolak. Titik di backtick, singkatan umum (`mis.`, `dll.`, `e.g.`), dan nomor versi (`v1.`) tidak
  memecah kalimat. Keluaran `PASS` mencetak sisa karakter. Frontend memakai aturan yang sama (0.21.3).
- **Skrip pembaca pengganti `grep`/`sed` `.md` (B3).** `python3 «brief_status.py» --taskdir <taskdir>` mencetak
  tabel status/risk/sidik/tautan/commit tiap brief beserta `HALT.md` dan kesegaran `REVIEW.md`;
  `render_prompt.py --template <dispatcher> --list-slots` mencetak slot tanpa menulis. SKILL `tech-lead`,
  `architect`, dan `plan` mewajibkan `.md` dibaca lewat `Read`.
- **Peta skrip dan perintah lengkap (B10).** SKILL `tech-lead`, `architect`, `plan`, dan `analyst` memetakan
  `«nama.py»` di `references/` ke path tersubstitusi; perintah `render_prompt.py` ditulis lengkap (path template
  absolut dan slot wajib) di titik dispatch.

## Langkah migrasi

Tidak ada. `HALT.md` `verdict: SYMBOL` yang sudah ada tetap menahan rantai dan dicabut seperti `SCOPE`
(`doc_seal.py cabut-halt --alasan "scope diterima user"`). `JOURNEY.md` lama terbaca apa adanya.
