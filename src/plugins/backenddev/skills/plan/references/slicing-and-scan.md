# Scan Checklist & Slicing Reference — `plan`

12 dimensi scan repositori Fase 2, sapuan dimensi residual lane tanpa PRD, dan strategi pemecahan unit DAG (*slicing*) Fase 3 untuk `backenddev:plan`. Aturan jalur masuk hidup di `entry-rules.md`; uji mandiri rantai brief dan commit agregat di `review-and-commit.md`; kaidah isi brief di `../templates/brief-template.md` bagian 2 — ketiganya tidak ditulis ulang di sini.

## 2. 12-Point Work-Unit Scan (Fase 2)

Jalankan checklist ini secara penuh untuk **setiap unit kerja** sebelum menyusun brief. Kuota sapuan main loop per unit kerja: maksimal 3 panggilan gabungan `Glob`+`Grep`, baca berkas hanya potongan tertarget ≤40 baris, nol berkas dibaca penuh, nol query database, nol `Bash` penelusuran. Lewat dari kuota → fan-out ke bagian 2A.

> **Kuota ini mengikat Fase 2 saja — pemetaan.** Ia menjawab "berkas mana yang tersentuh", dan 40 baris cukup untuk itu. Ia **tidak** berlaku atas Fase 3, yang menjawab pertanyaan berbeda: "snippet apa yang ditulis dan di titik sisip mana". `../templates/brief-template.md` bagian 2 butir 5 menuntut tiap langkah berupa **snippet lengkap dan valid** bertitik sisip konkret; menulisnya tanpa melihat konteks di sekitar anchor adalah mengarang, dan mengarang snippet persis yang dicegah Check B.
>
> **Kuota Fase 3 — penulisan `## Steps`:** pembacaan tertarget hanya atas berkas yang **sudah terdaftar di `## File scope` brief itu**, maksimal 2 potongan per berkas, plafon 120 baris terbaca per brief, nol berkas di luar `## File scope`, nol berkas milik brief lain. Lewat dari plafon berarti briefnya terlalu besar — pecah menurut langit-langit bagian 3A butir 3, jangan naikkan plafonnya.
>
> Laporan `.explore` unit itu dipanen lebih dulu (Fase 3 langkah 3) dan menggantikan sebagian besar pembacaan ini; kuota di atas adalah sisa untuk konteks di sekitar anchor yang tidak terangkut laporan.

1. **Re-verification** (hanya saat `finding_source` terisi): baca kode di `Lokasi` temuan; sudah diperbaiki → tandai `OBSOLETE`, keluarkan dari batch, catat bukti di `## Analysis trace`.
2. **Callers**: `Grep` nama method/endpoint di `source_root`; catat seluruh caller (`file:line`) dan periksa apakah berjalan di dalam atau di luar batas transactional.
3. **Mirrored paths**: cari consumer queue, scheduler, websocket, atau changelog terkait memakai resep di `## Navigation recipes` adapter; masukkan berkasnya ke `## File scope`.
4. **Configuration**: periksa berkas konfigurasi runtime untuk setelan yang mengubah semantik penyimpanan, sesuai daftar di `## Detection` adapter.
5. **Database migration**: definisi skema persistensi berubah → tetapkan nama berkas migrasi mengikuti pola berkas migrasi di `commands.md` profil (baris `migration-status`/`migration-apply`, atau `migration:` pada profil lama) berbasis penanda versi tertinggi, masukkan ke `## File scope` (`create`); tidak berubah → tulis "tidak perlu" beserta alasan di `## Migration`.
6. **Sibling patterns**: identifikasi modul lain berpola serupa yang belum terproteksi; catat di `## Analysis trace` sebagai backlog audit berikutnya, jangan diperbaiki di batch ini.
7. **`PLAUSIBLE` findings** (hanya saat `finding_source` terisi): temuan `PLAUSIBLE` yang blocker-nya belum dijawab user → tandai `DROPPED` dan catat di `## Analysis trace`.
8. **Work-unit grouping**: dua unit kerja yang menyentuh method atau class yang sama wajib digabung ke dalam brief yang sama secara berurutan.
9. **Anchor symbols & relative insertion**: catat simbol anchor (class, field, method) dan posisi relatifnya (misal "sesudah baris X di method Y (~`:84`)"). Dilarang nomor baris mutlak saja.
10. **Reference patterns to imitate**: temukan class/method eksisting yang menjadi cetakan repo (`file:line`).
11. **Cross-brief contracts**: definisikan signature lengkap untuk data/fungsi `Consumes` dan `Produces` pada `## Interfaces`. `Consumes` dilarang merujuk brief dengan `NN` lebih besar.
12. **Affected tests**: **Glob dulu, Grep menyusul.** Kumpulkan daftar berkas test di letak menurut baris `test:` `.claude/profile/backenddev/code-conventions.md` — atau baris `Test` `## Layer taxonomy` adapter bila baris itu absen — lalu cari di dalamnya test yang mem-mock atau menginstansiasi target, **dan** yang menyebut path endpoint sebagai string literal, termasuk di dalam array atau tabel kasus. Berkas test terdampak **wajib masuk `## File scope`** (`modify`). Vonis "tidak ada test terdampak" wajib menyebut jumlah berkas test yang disisir; `Grep` simbol saja meleset pada test yang memanggil endpoint lewat literal, dan berkas semacam itu baru ketahuan sebagai test merah sesudah seluruh brief mendarat.

Butir 3, 5, dan 12 mengisi `## File scope`; butir 1, 6, dan 7 mengisi `## Analysis trace`; butir 8 adalah keputusan slicing bagian 3. Lane tanpa PRD menambahkan sapuan bagian 2B.

### 2A. Fan-Out Explorer Paralel

Sesudah daftar unit kerja terkunci di Fase 1, tandai unit yang butuh penelusuran — package-nya tidak terpetakan di profil, rantai pemanggilnya melewati lebih dari 1 modul, targetnya tak muncul pada `Grep` pertama, **atau** kuota sapuan habis sebelum Stop Condition terpenuhi.

Berangkatkan unit bertanda **dalam satu giliran paralel** lewat template `../dispatcher/explorer.md`, satu dispatch `code-explorer` per unit, maksimal **4 serentak**; sisanya di gelombang berikutnya. Hidrasi `{objective}` dengan simbol atau alur konkret unit itu, `{taskdir}` dengan taskdir aktif, dan `{slug}` dengan `<slug>-<NN>` — `{slug}` juga menamai berkas laporan `{taskdir}/.explore/{slug}.md`. Blok `Format laporan` template ikut berangkat utuh; slot hidrasi selengkapnya, patokan `Kedalaman`, serta penanganan balikan ada di template itu. Tiap laporan menggantikan sapuan mandiri unit itu; unit tak bertanda disapu sendiri di bawah kuota Fase 2.

- Balikan `confidence: low`, payload kosong, atau format rusak → ulangi maksimal sekali; tetap gagal → catat di `## Analysis trace` lalu sapu manual.
- Dilarang menebak file, mendispatch explorer untuk unit yang sudah jelas dari profil, menyamakan `{slug}` antar dispatch segelombang, maupun membaca ulang berkas yang sudah diringkas explorer.

### 2B. Sapuan Dimensi Residual — lane tanpa PRD

Tujuh dimensi berikut adalah selisih antara 12 butir di atas dan 16 dimensi `## Impact map` PRD. Di jalur `PRD` ketujuhnya sudah divonis hulu dan **dilewati di sini**; di jalur `LANGSUNG` dan `RCA` tidak ada yang pernah memvonisnya, jadi sapuan ini wajib.

Dijalankan **sekali per batch** — bukan per unit kerja — sesudah daftar unit terkunci, di bawah kuota tambahan maksimal 2 panggilan gabungan `Glob`+`Grep`. Tiap dimensi divonis `terdampak` atau `tidak relevan`, dan **kedua vonis wajib membawa simbol konkret** (`file:line`, nama cache, nama enum, nama properti) — prosa penafian tanpa simbol ditolak, sama seperti lima dimensi rawan bocor di PRD.

1. **Cache yang di-invalidate**: entri cache yang memuat data target dan titik invalidasinya.
2. **Integrasi eksternal**: pemanggilan keluar (HTTP client, SDK, webhook) yang mengangkut field target.
3. **Feature flag & fallback**: flag yang menyelubungi jalur target, beserta perilaku saat flag mati.
4. **Kompatibilitas enum & serialisasi**: nilai enum atau bentuk payload yang berubah dan consumer lama yang membacanya.
5. **Dokumentasi API & OpenAPI**: berkas spesifikasi atau anotasi yang ikut basi.
6. **Pesan error & i18n**: kunci pesan atau berkas terjemahan yang bertambah/berubah.
7. **Dampak query & indexing**: query yang berubah rencana eksekusinya, dan index penunjang yang dibutuhkan.

Penyaluran vonis: dimensi `terdampak` yang menuntut perubahan berkas masuk `## File scope` brief penampungnya; yang hanya perlu diawasi masuk `## Risk & rollback`. Seluruh vonis `tidak relevan` beserta simbol sapuannya dicatat satu baris per dimensi di `## Analysis trace` brief pertama batch.

**Pintu eskalasi**: dimensi 3 atau 4 bervonis `terdampak` berarti kontrak keluar berubah — berhenti dan terapkan 5 pemicu eskalasi `entry-rules.md` bagian 1A, jangan diselesaikan di brief MINOR.

## 3. Strategi Pemecahan Unit (Slicing) & Linear DAG (Fase 3)

### A. Aturan 3-Lapis Batas Slicing

1. **Lantai — titik hijau mandiri**: setiap brief wajib berakhir pada kondisi kode yang **tetap kompilabel dan konsisten** tanpa menunggu brief berikutnya. Dilarang memecah unit bila pemecahannya merusak kompilasi atau test.
2. **Panduan — satu pesan commit**: tujuan brief yang tidak dapat ditulis dalam satu kalimat pesan commit tanpa kata sambung "dan" wajib dipecah menjadi 2 brief.
3. **Langit-langit — 5 langkah / 4 file kode**: satu brief yang memuat **lebih dari 5 langkah `## Steps`** atau **lebih dari 4 file kode di `## File scope`** wajib dipecah menjadi brief terpisah. *(File test tidak dihitung dalam limit 4 file.)*

Pecah kandidat yang melampaui langit-langit menjadi dua brief berurutan; gabungkan kembali ke satu brief bila pemecahan itu merusak kompilasi antar langkah, dan catat alasan penggabungannya di `## Analysis trace`.

### B. Linear DAG & Hierarki Lapisan

- Dependensi antar-brief mengalir satu arah tanpa siklus (`brief-01` → `brief-02` → `brief-03`).
- File yang sama boleh dimodifikasi di beberapa brief berurutan, tetapi simbol anchor (method/field) tidak boleh tumpang tindih di direktori yang sama.
- Urutan implementasi mengikuti `## Layer taxonomy` adapter stack pada sub-bagian yang sesuai `architecture:` profil — urutan `hexagonal` (domain → port → use case → adapter driven → adapter driving → wiring) berbeda dari `layered`, dan brief yang memakai urutan gaya lain menaruh port sesudah implementornya. Rincian tiap lapisan dan jebakannya dibaca di sana, bukan dari kebiasaan stack lain. Dua lapisan penutup yang selalu ada: `Tests` lalu `Mirrored Paths`.
