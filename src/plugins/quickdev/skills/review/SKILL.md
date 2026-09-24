---
name: review
description: Gunakan ketika perubahan kode uncommitted hasil gate execute siap dinilai - penilaian diff terhadap kontrak rencana dan konvensi profil repo, sebelum commit atau merge tanpa laporan temuan
metadata:
  mode: standard
---

## THE IRON LAW

DILARANG MELAPORKAN SATU TEMUAN PUN TANPA BUKTI PATH BERKAS DAN NOMOR BARIS NYATA YANG DIAMBIL DARI ISI DIFF ATAU BERKAS SUMBER. DILARANG MENGUBAH, MENULIS, ATAU MEMPERBAIKI BERKAS KODE SUMBER SELAMA REVIEW BERLANGSUNG — SKILL INI MURNI READ-ONLY. SELURUH PERUBAHAN DALAM CAKUPAN DIFF WAJIB DINILAI TERHADAP TUJUH DIMENSI REVIEW SECARA LENGKAP TANPA MELEWATI DIMENSI MANA PUN. STATUS TERMINAL WAJIB `CHANGES_REQUIRED` BILA TERDAPAT MINIMAL SATU TEMUAN BERSEVERITAS `BLOCKER` ATAU `MAJOR`. KEPUTUSAN COMMIT, MERGE, ATAU RILIS TETAP MILIK MUTLAK USER DAN DILARANG DIAMBIL OLEH SKILL INI.

## Precondition [REQUIRED]

1. Blok penutupan di `plan_path` memuat `Execution Status: COMPLETED`, atau `VERIFICATION_MANUAL_REQUIRED` yang hasil perintah manualnya sudah dikonfirmasi lolos oleh user; selain itu (blok absen atau status lain), hentikan review dan kembalikan pemanggil ke gate `execute`.
2. Direktori kerja adalah git repository valid (`git rev-parse --is-inside-work-tree` bernilai `true`); bila gagal, hentikan dan laporkan blocker environment.
3. Terdapat minimal satu berkas berubah di luar `plan_path` dan `profile_path`, dihitung dari gabungan `git diff HEAD --name-only` dan `git ls-files --others --exclude-standard` (berkas untracked); bila nol, hentikan review dan laporkan status `NO_CHANGES` tanpa menulis temuan rekaan.
4. Dokumen rencana pada `plan_path` (misal `plan/<task-name>.md`) tersedia di filesystem sebagai kontrak pembanding; bila hilang, hentikan dan minta path yang benar kepada user.
5. Berkas profil pada `profile_path` (atau fallback-nya) tersedia sebagai acuan konvensi layer, penamaan, dan baseline verifikasi.

## Parameter [REQUIRED]

- `plan_path` — string — [REQUIRED] — path relatif dokumen rencana berstatus `COMPLETED`; wajib resolve ke berkas markdown nyata di filesystem.
- `profile_path` — string — default `repo-profile.md` — bila tidak ditemukan, gunakan fallback `.dev/profile.md`; bila keduanya absen, precondition 5 gagal.
- `scope_paths` — array<string> — default `[]` — daftar path pembatas cakupan review; nilai kosong berarti seluruh berkas dalam diff dinilai. Setiap entri wajib berada di dalam daftar berkas hasil diff.
- `strict` — bool — default `false` — bila `true`, temuan berseveritas `MINOR` ikut memblokir dan memaksa status `CHANGES_REQUIRED`.
- `include_staged` — bool — default `true` — bila `true`, gunakan `git diff HEAD` (staged + unstaged); bila `false`, gunakan `git diff` (unstaged saja). Berkas untracked selalu ikut dinilai pada kedua nilai karena berkas baru hasil gate `execute` tidak pernah di-stage.

## Workflow

### Fase 1 — Validasi Precondition & Pengumpulan Diff

1. Verifikasi kelima precondition secara berurutan; setiap kegagalan menghentikan skill seketika dengan pesan blocker spesifik, bukan peringatan lunak.
2. Kumpulkan daftar berkas terdampak dari dua sumber: `git diff HEAD --name-status` (atau `git diff --name-status` bila `include_staged` bernilai `false`) untuk berkas tracked, dan `git ls-files --others --exclude-standard` untuk berkas untracked (catat berstatus `A`). Keluarkan `plan_path` dan `profile_path` dari daftar karena keduanya artefak gate, bukan hasil implementasi.
3. Kumpulkan isi perubahan beserta nomor baris: `git diff HEAD -U3` (atau `git diff -U3` bila `include_staged` bernilai `false`) untuk berkas tracked, dengan pemetaan setiap hunk ke rentang baris berkas hasil; untuk berkas untracked, baca berkas utuh dan perlakukan seluruh barisnya sebagai baris tambahan. Bukti `file:line` wajib merujuk nomor baris berkas hasil.
4. Terapkan filter `scope_paths` bila tidak kosong; catat jumlah berkas yang tersaring keluar sebagai catatan cakupan, jangan diamkan secara senyap.
5. Predikat lanjut: daftar berkas dalam cakupan berjumlah minimal satu. Bila nol setelah filter, hentikan dan laporkan cakupan kosong.

### Fase 2 — Rekonstruksi Kontrak Pembanding

1. Baca `plan_path` dan ekstrak kontrak yang mengikat: daftar langkah atomik, path berkas target yang direncanakan, strategi verifikasi, dan definisi selesai per langkah.
2. Baca `profile_path` dan ekstrak konvensi yang mengikat: struktur layer arsitektur, konvensi penamaan berkas dan simbol, pola error handling, lokasi test suite, serta perintah baseline typecheck, lint, dan test.
3. Susun dua himpunan pembanding secara eksplisit: himpunan berkas yang direncanakan (dari `plan_path`) dan himpunan berkas yang benar-benar berubah (dari Fase 1).
4. Hitung selisih dua arah: berkas berubah tetapi tidak direncanakan (indikasi scope creep) dan berkas direncanakan tetapi tidak berubah (indikasi langkah terlewat).
5. Predikat lanjut: kontrak plan dan konvensi profil terekstrak; selisih dua arah tercatat sebagai daftar kandidat temuan Fase 3.

### Fase 3 — Analisis Tujuh Dimensi

Nilai seluruh berkas dalam cakupan terhadap tujuh dimensi berikut secara berurutan; setiap dimensi wajib menghasilkan verdict eksplisit `CLEAN` atau daftar temuan, dan dilarang ditandai "tidak diperiksa".

1. **Korektness Logika** — kesalahan kondisi boolean, off-by-one, null atau undefined tidak tertangani, race pada operasi asinkron, dan cabang logika yang tidak pernah tereksekusi.
2. **Kepatuhan Kontrak Plan** — perubahan di luar langkah yang direncanakan, langkah rencana yang belum terimplementasi, serta penyimpangan path berkas terhadap `plan_path`.
3. **Konvensi Profil & Layer** — pelanggaran batas layer arsitektur, penamaan simbol menyimpang, dan penempatan berkas di direktori yang salah menurut `profile_path`.
4. **Keamanan** — kredensial atau token terhardcode, input eksternal tanpa validasi, konkatenasi kueri berpotensi injeksi, data sensitif tercetak di log, dan pemeriksaan otorisasi yang hilang.
5. **Error Handling** — blok catch kosong, error tertelan tanpa propagasi, pesan error tanpa konteks aktionable, dan jalur kegagalan yang tidak memiliki penanganan sama sekali.
6. **Kualitas Test** — perubahan perilaku tanpa test pendamping, assertion yang selalu bernilai benar, test bergantung pada state global, dan penghapusan test tanpa penggantian setara.
7. **Regresi Cakupan** — pemanggil simbol yang diubah tetapi tidak ikut disesuaikan, perubahan signature publik yang memutus kontrak konsumen, dan penghapusan kode yang masih dirujuk modul lain.

Untuk dimensi 7, telusuri pemanggil setiap simbol yang diubah menggunakan pencarian teks pada repositori; dilarang menyimpulkan aman tanpa hasil pencarian nyata.

### Fase 4 — Verifikasi Bukti & Klasifikasi Severity

1. Buka berkas sumber pada setiap baris kandidat temuan dan konfirmasi isinya benar-benar sesuai klaim; buang setiap kandidat yang tidak terkonfirmasi bukti nyata.
2. Klasifikasikan setiap temuan terverifikasi ke satu tingkat severity:
   - `BLOCKER` — cacat yang menyebabkan kegagalan runtime, kehilangan data, celah keamanan, atau pelanggaran kontrak plan yang bersifat fundamental.
   - `MAJOR` — cacat yang menurunkan korektness pada kasus tepi, error handling absen pada jalur nyata, atau regresi kontrak konsumen.
   - `MINOR` — penyimpangan konvensi, penamaan, atau kualitas test yang tidak mengubah perilaku produksi.
3. Deduplikasi temuan berulang pada berkas dan akar masalah yang sama menjadi satu entri dengan daftar lokasi terlampir.
4. Susun rekomendasi perbaikan per temuan dalam bentuk instruksi imperatif dan spesifik; dilarang menuliskan patch kode yang diterapkan langsung ke berkas.
5. Predikat lanjut: setiap temuan memiliki severity, bukti `file:line` terverifikasi, dan satu rekomendasi aktionable.

### Fase 5 — Penentuan Status & Pelaporan

1. Tentukan status terminal: `CHANGES_REQUIRED` bila terdapat minimal satu temuan `BLOCKER` atau `MAJOR`, atau bila `strict` bernilai `true` dan terdapat temuan `MINOR`. Selain itu `REVIEWED`.
2. Sajikan daftar temuan terurut menurun berdasarkan severity, lalu tabel cakupan tujuh dimensi, lalu ringkasan akhir maksimal 17 baris.
3. Bila status `CHANGES_REQUIRED`, serahkan daftar temuan ke gate `execute` lewat parameter `review_findings` (dengan `plan_path` yang sama) untuk remediasi; dilarang memperbaiki sendiri di sesi review.
4. Bila status `REVIEWED`, nyatakan bahwa keputusan commit atau merge menunggu tindakan user.

## Guardrails

- MUST NOT mengedit, menulis, memformat, atau menghapus berkas kode sumber, test, maupun konfigurasi apa pun.
- MUST NOT menjalankan `git commit`, `git stash`, `git checkout`, `git reset`, `git clean`, `git push`, atau perintah git lain yang memutasi state repositori; hanya perintah baca (`git diff`, `git status`, `git log`, `git ls-files`, `git rev-parse`) yang diizinkan.
- MUST NOT mengubah `plan_path`, `profile_path`, atau berkas artefak gate hulu mana pun, termasuk mencentang checklist rencana.
- MUST NOT menyetujui, melakukan merge, atau menyatakan perubahan siap rilis — keputusan itu milik mutlak user.
- MUST NOT melaporkan temuan berbasis dugaan, praktik umum, atau ingatan tanpa bukti baris nyata pada berkas dalam cakupan diff.
- MUST NOT menilai berkas di luar daftar diff atau di luar `scope_paths`, serta dilarang memperluas cakupan review tanpa izin user.
- MUST NOT menurunkan severity temuan demi memperoleh status `REVIEWED`.

## Output [REQUIRED]

Skill ini menghasilkan laporan terminal saja tanpa artefak berkas.

1. **Daftar Temuan** — satu blok per temuan dengan struktur pasti:
   ```
   [BLOCKER] Kredensial database terhardcode
   Lokasi   : src/config/database.ts:42
   Bukti    : const password = "prod_secret_2024"
   Dimensi  : Keamanan
   Dampak   : Kredensial produksi terekspos di riwayat version control
   Rekomendasi: Pindahkan nilai ke environment variable dan baca via config loader
   ```
2. **Tabel Cakupan Dimensi** — tujuh baris dimensi dengan kolom verdict (`CLEAN` atau jumlah temuan) dan jumlah berkas yang diperiksa.
3. **Status Terminal**: `REVIEWED` | `CHANGES_REQUIRED` | `NO_CHANGES`
4. **Ringkasan Akhir (Maksimal 17 Baris)**:
   ```
   REVIEW: <task-name> — working tree (tracked + untracked)
   STATUS: REVIEWED | CHANGES_REQUIRED | NO_CHANGES
   CAKUPAN: <n> berkas dinilai, <n> berkas tersaring keluar oleh scope_paths
   PLAN: <plan_path> — <n> langkah terverifikasi terimplementasi
   PROFIL: <profile_path>
   TEMUAN: <n> BLOCKER / <n> MAJOR / <n> MINOR
   DIMENSI CLEAN: <daftar dimensi tanpa temuan>
   SCOPE CREEP: <daftar berkas berubah di luar rencana | ->
   LANGKAH TERLEWAT: <daftar langkah rencana tanpa perubahan kode | ->
   MODE: strict=<true|false>, include_staged=<true|false>
   HANDOFF: gate execute (remediasi) | user (keputusan commit/merge) | tidak ada (NO_CHANGES)
   ```

## Failure path

1. **Gate execute belum COMPLETED**: hentikan review, jangan baca diff, dan arahkan pemanggil menyelesaikan implementasi beserta verifikasi baseline di gate `execute`.
2. **Working tree bersih**: bila `git diff HEAD` dan `git ls-files --others --exclude-standard` tidak memuat berkas di luar `plan_path` dan `profile_path`, laporkan status `NO_CHANGES` beserta kemungkinan penyebab (perubahan sudah ter-commit sehingga review perlu menargetkan rentang commit), lalu hentikan tanpa temuan rekaan.
3. **Dokumen rencana hilang atau tidak terbaca**: hentikan dan minta `plan_path` yang benar; dilarang melanjutkan review kontrak berdasarkan rekonstruksi tebakan dari isi diff.
4. **Berkas profil absen**: bila `profile_path` dan fallback `.dev/profile.md` sama-sama tidak ada, hentikan dan arahkan pemanggil menjalankan gate `profile` lebih dahulu.
5. **Diff terlalu besar untuk dinilai utuh**: laporkan jumlah berkas dan baris terdampak, lalu minta user mempersempit lewat `scope_paths`; dilarang menilai sebagian secara diam-diam dan melaporkannya sebagai cakupan penuh.
6. **Berkas biner atau berkas generated dalam diff**: lewati penilaian isi, catat sebagai `SKIPPED (binary/generated)` pada tabel cakupan, dan jangan hitung sebagai berkas bersih.
7. **Bukti baris tidak terkonfirmasi saat Fase 4**: buang kandidat temuan tersebut dari laporan dan catat jumlah kandidat yang gugur pada baris cakupan.

## STYLE

- Gunakan kalimat imperatif aktif dan Observable Predicate pada setiap langkah penilaian dan checkpoint verifikasi.
- Tuliskan path berkas, nomor baris, nama simbol, dan perintah git dalam format inline code backticks (contoh: `src/services/order.service.ts:88`, `git diff HEAD`).
- Sajikan kutipan bukti kode dalam blok kode ringkas maksimal tiga baris per temuan.
- Nyatakan severity dan status terminal dalam huruf kapital tanpa variasi ejaan agar konsisten dengan gate hulu.
- Pertahankan istilah domain teknis (diff, hunk, working tree, staged, severity, blocker, scope creep, regresi, handoff, baseline) tanpa penerjemahan paksa.
- Tulis rekomendasi sebagai instruksi perbaikan, bukan opini naratif atau pujian terhadap kode.
