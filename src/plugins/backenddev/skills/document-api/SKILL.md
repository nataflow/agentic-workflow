---
name: document-api
description: Gunakan ketika user eksplisit meminta dokumentasi API untuk endpoint yang sudah ada di kode - endpoint nyata dipetakan jadi docs/api/, sebelum merilis API tanpa dokumen terverifikasi
---

## THE IRON LAW

- Dokumen ini merekam kode, bukan merancangnya: tiap endpoint, field, dan error code wajib membawa bukti `file:line` nyata di `src/`.
- Klaim tanpa bukti wajib ditandai `UNVERIFIED`, dilarang ditebak atau dibulatkan.
- Perlakukan `src/` sebagai read-only mutlak — ketidakcocokan kode dengan harapan dilaporkan, bukan diperbaiki.
- Dilarang menimpa berkas `docs/api/` yang sudah ada tanpa izin eksplisit user.
- Dilarang menjalankan `git commit`, `git push`, atau membuat branch.

## Precondition [REQUIRED]

1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/document-api/scripts/check_preconditions.py [--domain <domain>] [--base-branch <base_branch>] [--stack <stack>]`.
2. Evaluasi output skrip secara deterministik:
   - `PASS` (5/5 checks): Lanjutkan ke resolusi trigger dan ekstraksi endpoint.
   - `FAIL`: Hentikan eksekusi segera dan jalankan tindakan remediasi pada butir yang gagal (source root tidak dapat dibaca → periksa izin direktori; profil/stack adapter tidak ada → jalankan `backenddev:profile`; direktori docs/api/ tidak dapat ditulis → periksa hak akses).

## Parameter [REQUIRED]

- `domain` — string — `[REQUIRED]` — Deskripsi cakupan API dalam bahasa natural dari user, contoh `management product`. Skill sendiri yang menelusuri lokasi endpoint-nya di `src/`. Hentikan eksekusi dan minta cakupan jika parameter kosong; dilarang berasumsi "seluruh API".
- `base_branch` — string — default: `base_branch` dari `.claude/profile/backenddev/index.json`, lalu `main`, lalu `master` — Hanya dibaca pada mode `POST_CHAIN` untuk membatasi cakupan ke endpoint yang berubah. Turunkan ke cakupan penuh `domain` dan catat sebagai ASUMSI di laporan jika branch tidak ada di `git branch -a`.

## Workflow

### Fase 0 — Resolusi Trigger & Cakupan

1. Jalankan skrip `check_preconditions.py` dengan parameter `domain` dan `base_branch`. Hentikan eksekusi segera jika skrip menghasilkan `FAIL`.
2. Tetapkan mode cakupan yang diminta user: `ON_REQUEST` (user menyebut cakupan langsung) atau `POST_CHAIN` (user meminta cakupan dibatasi ke rantai yang baru selesai). Skill ini tidak pernah berangkat otomatis; kedua mode berawal dari permintaan eksplisit user.
3. Jalankan `git diff --name-only $(git merge-base HEAD <base_branch>)..HEAD` pada mode `POST_CHAIN` dan saring berkas endpoint serta tipe muatannya yang tersentuh. Jadikan daftar hasil saring sebagai himpunan kandidat awal.
4. Pecah `domain` menjadi kata kunci pencarian pada mode `ON_REQUEST` (kata benda domain, sinonim Inggris-Indonesia, bentuk tunggal dan jamak). Contoh `management product` menghasilkan `product`, `products`, `produk`, `catalog`, `item`.
5. Turunkan slug berkas keluaran dari `domain` dalam kebab-case ASCII: `management product` menjadi `management-product`.

### Fase 1 — Penelusuran Endpoint di src/

1. Sisir kode sumber dengan kata kunci Fase 0 pada nama berkas penampung endpoint, nilai prefix path di level deklarasi kelompok, dan nama handler — memakai pola dari `## API surface` adapter.
2. Catat untuk setiap kandidat: path berkas, baris deklarasi kelompok, base path kelompok, dan tiap handler endpoint beserta baris deklarasinya.
3. Telusuri satu tingkat ke hilir: tipe request body, tipe respons (pembungkus generik dibongkar sampai tipe muatannya), dan parameter path maupun query beserta status wajib/opsional dan nilai default.
4. Hentikan eksekusi dan laporkan status `BLOCKED` dengan daftar kata kunci yang sudah dicoba jika himpunan endpoint kosong.

### Fase 2 — Konfirmasi Cakupan ke User [REQUIRED]

Fase ini blocking. Tampilkan daftar temuan sebagai tabel `METHOD | PATH | BERKAS:LINE`, lalu tanyakan dalam satu batch: mana yang masuk cakupan, apakah ada endpoint yang terlewat, dan apakah cakupan sudah final. Buang endpoint yang ditolak user dari himpunan dan catat di baris `SKIPPED` laporan akhir. Dilarang melanjutkan ke ekstraksi kontrak sebelum user menyatakan daftar final.

### Fase 3 — Ekstraksi Kontrak per Endpoint

Untuk setiap endpoint dalam daftar final, ekstrak dari kode dan sertai bukti `file:line`:

1. **Identitas**: HTTP method, path lengkap (base path kelas digabung path method), ringkasan satu kalimat dari nama handler dan komentar dokumentasinya bila ada.
2. **Auth**: Deklarasi otorisasi per endpoint menurut `## API surface` adapter. Cari aturan pola URL di konfigurasi keamanan jika tidak ada di handler. Tulis `UNVERIFIED` jika tidak ditemukan.
3. **Parameter**: Tiap parameter path dan query (nama, tipe, wajib atau opsional, nilai default).
4. **Request body**: Field tipe request beserta tipe datanya dan constraint validasinya, diterjemahkan menjadi aturan yang dapat dibaca manusia.
5. **Response sukses**: Status HTTP menurut resep adapter (default `200` bila tidak dideklarasikan) dan field tipe respons.
6. **Error**: Status dan kode dari kegagalan yang dilempar handler, dipetakan lewat mekanisme penanganan error terpusat repo.

Bongkar field yang tipenya bersarang maksimal 2 tingkat; rujuk tingkat lebih dalam sebagai nama tipe. Tulis `UNVERIFIED` beserta alasan singkat untuk setiap butir yang tidak dapat dipastikan dari kode.

### Fase 4 — Resolusi Berkas Tujuan & Izin Overwrite [REQUIRED]

1. Tetapkan berkas tujuan `docs/api/<slug>.md`. Buat `docs/api/` jika belum ada.
2. Lanjut menulis baru jika berkas belum ada di disk.
3. Baca isi berkas jika sudah ada, bandingkan per endpoint, lalu tampilkan rencana perubahan sebagai daftar `TAMBAH | UBAH | TETAP | HILANG DI KODE`. Gunakan update terarah sebagai default aksi untuk mempertahankan seksi manual di luar blok endpoint. Jalankan overwrite total hanya setelah user mengizinkannya secara eksplisit.

### Fase 5 — Penulisan Dokumen

Baca `references/api-doc-template.md` sebelum menulis berkas keluaran, lalu isi kerangkanya dengan hasil Fase 3. Tulis berkas sebagai satu aksi tuntas; dilarang meninggalkan dokumen separuh jadi. Urutkan endpoint berdasarkan base path lalu method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`). Tulis satu blok ```json di bawah tabel request body dan tabel response sukses berisi contoh payload yang dibangun dari field, tipe, dan aturan validasi hasil Fase 3; lewati blok JSON jika tabel tanpa baris. Bangun setiap contoh cURL dari path, header auth, dan field request nyata hasil ekstraksi.

### Fase 6 — Verifikasi & Laporan

1. Verifikasi tiap endpoint di dokumen memiliki baris bukti `file:line` atau penanda `UNVERIFIED`.
2. Verifikasi jumlah endpoint di dokumen sama dengan jumlah daftar final Fase 2 dikurangi yang ditolak.
3. Tetapkan status terminal lalu sajikan laporan sesuai `## Output`.

## Guardrails

- Dilarang mengedit, membuat, memindahkan, atau menghapus berkas apa pun di `src/`, berkas manifest, maupun berkas konfigurasi runtime. Kode adalah read-only mutlak.
- Dilarang mengarang endpoint, path, field, status HTTP, atau error code. Beri tanda `UNVERIFIED` untuk setiap butir tanpa bukti `file:line`.
- Dilarang menjalankan `git commit`, `git push`, `git checkout -b`, atau mengubah state git. Perintah git yang diizinkan hanya yang read-only: `git diff`, `git merge-base`, `git branch -a`, `git status`.
- Dilarang menimpa berkas `docs/api/*.md` yang sudah ada tanpa izin eksplisit user pada Fase 4.
- Dilarang menjalankan build, test, atau menyalakan aplikasi untuk memastikan perilaku endpoint.
- Dilarang menulis dokumen untuk endpoint yang belum ada di kode, termasuk endpoint yang baru direncanakan di PRD atau brief.
- **KEPUTUSAN DEFINITIF SAAT INI**: Seluruh isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
- Keputusan milik mutlak user: cakupan `domain` final, izin overwrite berkas, dan keputusan commit atas dokumen yang dihasilkan.

## Output [REQUIRED]

Artefak `docs/api/<slug>.md` mengikuti `references/api-doc-template.md` — dilarang menyalin strukturnya ke sini. `DOCUMENTED` — seluruh endpoint daftar final terekam dengan bukti `file:line` — → tutup satu baris tanpa blok: `### API DOCUMENTATION REPORT — DOCUMENTED · docs/api/<slug>.md · <n> endpoint · mode <BARU | UPDATE TERARAH | OVERWRITE>`. Selain itu, sajikan:

```markdown
### API DOCUMENTATION REPORT — <PARTIAL | BLOCKED>
- **Artefak** : docs/api/<slug>.md · mode <BARU | UPDATE TERARAH | OVERWRITE (diizinkan user)> | tidak ada berkas ditulis
- **Endpoint**: <n> terdokumentasi · <n> UNVERIFIED · <n> SKIPPED
- **UNVERIFIED**: <daftar butir + alasan>
- **ASUMSI**  : <daftar asumsi> | —
```

`PARTIAL` berarti dokumen tertulis namun memuat minimal satu butir `UNVERIFIED`; `BLOCKED` berarti tidak ada berkas yang ditulis.

**Serah-terima.** `Dokumentasi API selesai — berkas belum di-commit; keputusan commit milik user atau gerbang backenddev:tech-lead.`

## Failure path

- Nol endpoint ditemukan untuk `domain`: Laporkan `BLOCKED` berisi daftar kata kunci yang dicoba dan minta user menunjuk berkas endpoint secara langsung. Jangan tulis berkas kosong.
- `domain` ambigu sehingga cocok dengan dua kelompok endpoint tak berkaitan: Tampilkan kedua kelompok pada Fase 2 dan minta user memilih. Dilarang menggabungkan keduanya diam-diam.
- `base_branch` tidak ada saat trigger `POST_CHAIN`: Turunkan ke cakupan penuh `domain`, catat sebagai ASUMSI, dan lanjutkan alur.
- User menolak overwrite berkas yang sudah ada: Hentikan penulisan, sajikan rencana perubahan Fase 4 sebagai laporan, dengan status `BLOCKED`.
- Kode dan dokumen lama bertentangan: Kode menang. Catat entri lama sebagai `HILANG DI KODE` pada rencana Fase 4; jangan hapus sepihak seksi manual buatan user.
- Endpoint ditemukan namun tipe muatannya berada di modul eksternal yang tidak dapat dibaca: Dokumentasikan identitas endpoint, tandai bagian body `UNVERIFIED`, dengan status `PARTIAL`.
- Sesi terputus setelah berkas ditulis: Baca berkas yang ada lalu lanjutkan dari Fase 4 sebagai update terarah; dilarang menulis ulang dari awal.

## STYLE

- Gunakan fase bernomor dan kalimat perintah imperatif aktif yang tegas dan to the point tanpa konstruksi bersyarat WHEN/THEN.
- Tulis dokumen keluaran dalam bahasa Indonesia dengan istilah teknis HTTP, framework, dan nama simbol tetap dalam bahasa Inggris apa adanya.
- Nama path, field, kelas, dan anotasi selalu dibungkus backtick agar dapat disalin persis.
- Satu endpoint satu blok; dilarang menggabungkan dua endpoint dalam satu blok meski hanya beda HTTP method.
- Contoh cURL memakai placeholder eksplisit `<base-url>` dan `<token>`, tidak pernah memuat kredensial nyata dari repo.
- Nilai pada contoh JSON diturunkan dari tipe dan anotasi validasi tiap field, bukan disalin dari data nyata, seed, atau kredensial di repo. Field opsional tetap ditampilkan agar bentuk payload utuh terbaca.
- Bukti ditulis dengan resep `path/ke/Berkas:42`, bukan deskripsi naratif lokasi.
