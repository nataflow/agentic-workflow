---
name: review
description: Alur ringan quickdev (repo-profile.md, plan/<task>.md, tanpa taskdir) — menilai diff uncommitted hasil quickdev:execute terhadap plan/<task>.md dan repo-profile.md sebelum commit; dipanggil eksplisit lewat /quickdev:review.
disable-model-invocation: true
---

## THE IRON LAW

DILARANG MELAPORKAN SATU TEMUAN PUN TANPA BUKTI PATH BERKAS DAN NOMOR BARIS NYATA YANG DIAMBIL DARI ISI DIFF ATAU BERKAS SUMBER. DILARANG MENGUBAH, MENULIS, ATAU MEMPERBAIKI BERKAS KODE SUMBER SELAMA REVIEW BERLANGSUNG — SKILL INI MURNI READ-ONLY. SELURUH PERUBAHAN DALAM CAKUPAN DIFF WAJIB DINILAI TERHADAP TUJUH DIMENSI REVIEW SECARA LENGKAP TANPA MELEWATI DIMENSI MANA PUN. STATUS TERMINAL WAJIB `CHANGES_REQUIRED` BILA TERDAPAT MINIMAL SATU TEMUAN BERSEVERITAS `BLOCKER` ATAU `MAJOR`. KEPUTUSAN COMMIT, MERGE, ATAU RILIS TETAP MILIK MUTLAK USER DAN DILARANG DIAMBIL OLEH SKILL INI.

## Precondition [REQUIRED]

1. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py verify --plan <plan_path>` → `VERIFY PASS`, **dan** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py status --plan <plan_path> --json` → `execution.Status` ∈ {`COMPLETED`, `COMPLETED (manual)`} **dan** `consistent: true`. `consistent: false` (blok terminal dengan langkah `- [ ]`, atau tanpa `Verification`) → blok tidak ditulis `plan_lock.py close` atau rencana direvisi sesudah selesai; kembalikan ke `quickdev:execute` dan kutip `inconsistency`. `VERIFICATION_MANUAL_REQUIRED` → kembalikan ke `quickdev:execute` (mode `manual`) untuk mencatat konfirmasi user; status lain atau blok absen → kembalikan ke `quickdev:execute`. `verify` FAIL → rencana berubah sesudah approval; hentikan dan arahkan ke `quickdev:plan`.
2. Direktori kerja adalah git repository valid (`git rev-parse --is-inside-work-tree` bernilai `true`); bila gagal, hentikan dan laporkan blocker environment.
3. Terdapat minimal satu berkas berubah di luar `<plan_dir>/` (direktori `plan_path`) dan `profile_path`, dihitung dari gabungan `git diff <BASE> --name-only` dan `git ls-files --others --exclude-standard` (berkas untracked); `<BASE>` ditetapkan di Fase 1 butir 2. Bila nol, hentikan review dan laporkan status `NO_CHANGES` (Failure path 2) tanpa menulis temuan rekaan.
4. Dokumen rencana pada `plan_path` (misal `plan/<task-name>.md`) tersedia di filesystem sebagai kontrak pembanding; bila hilang, hentikan dan minta path yang benar kepada user.
5. Berkas profil pada `profile_path` (atau fallback-nya) tersedia sebagai acuan konvensi layer, penamaan, dan baseline verifikasi.
6. `python3` (3.9+) tersedia untuk `plan_lock.py` (hanya subperintah baca `verify` dan `status`).

## Koeksistensi [REQUIRED]

- Skill ini bagian dari alur ringan `quickdev` (`repo-profile.md`, `plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backend:*` atau `frontend:*` sebagai pengganti: `backend:profile`/`frontend:profile` menulis `.claude/profile/<plugin>/`, bukan `repo-profile.md`, dan tidak memenuhi precondition skill ini.
- Bila konteks sesi memuat blok `<backend-tech-lead-gate>` atau `<frontend-lead-gate>`:
  - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`, `repo-profile.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
  - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backend:tech-lead | frontend:lead>` (taskdir + brief)". Jangan memilih sendiri.
- `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
- Penanda opt-out `.claude/workflow` (nama plugin yang boleh menggerbangi repo, dipisah spasi/baris): isi `quickdev` membuat hook SessionStart `backend`/`frontend` diam; isi `frontend quickdev` hanya menyalakan hook `frontend`.

## Parameter [REQUIRED]

- `plan_path` — string — [REQUIRED] — path relatif dokumen rencana yang blok `## Execution Status`-nya `COMPLETED`; wajib resolve ke berkas markdown nyata di filesystem.
- `profile_path` — string — default: nilai `Profile:` di metadata `plan_path`; bila absen, `repo-profile.md`, lalu `.dev/profile.md`; bila semuanya absen, precondition 5 gagal.
- `scope_paths` — array<string> — default `[]` — daftar path pembatas cakupan review; nilai kosong berarti seluruh berkas dalam diff dinilai. Setiap entri wajib berada di dalam daftar berkas hasil diff.
- `strict` — bool — default `false` — bila `true`, temuan berseveritas `MINOR` ikut memblokir dan memaksa status `CHANGES_REQUIRED`.
- `include_staged` — bool — default `true` — bila `true`, gunakan `git diff <BASE>` (committed sejak base + staged + unstaged); bila `false`, gunakan `git diff` (unstaged saja) dan berlaku hanya bila `<BASE>` = `HEAD` — selain itu abaikan dan catat di baris `MODE`. Berkas untracked selalu ikut dinilai pada kedua nilai karena berkas baru hasil `quickdev:execute` tidak pernah di-stage.
- `base_ref` — string — default `""` — commit pembanding. Kosong → `Base-Commit` blok `## Execution Status` `plan_path`; blok tanpa `Base-Commit` → `HEAD`. Terisi → wajib resolve lewat `git rev-parse --verify <base_ref>^{commit}`; bila gagal, hentikan.

## Workflow

### Fase 1 — Validasi Precondition & Pengumpulan Diff

1. Verifikasi keenam precondition secara berurutan; setiap kegagalan menghentikan skill seketika dengan pesan blocker spesifik, bukan peringatan lunak. Bila review dijalankan di sesi yang sama dengan `quickdev:execute`, nyatakan di ringkasan (`MODE: … sesi-sama=ya`) dan sarankan user menjalankan ulang `/quickdev:review` di sesi baru untuk putaran terakhir.
2. Tetapkan `<BASE>`: `base_ref` bila terisi; selain itu `execution.Base-Commit` dari `plan_lock.py status --json`; blok tanpa `Base-Commit` → `HEAD`. `Base-Commit: none` (repo tanpa commit) → `<BASE>` = tree kosong `$(git hash-object -t tree /dev/null)`. `Base-Note` terisi → sebutkan di ringkasan bahwa kerja yang di-commit sebelum base tidak terlihat.
3. Kumpulkan daftar berkas terdampak dari dua sumber: `git diff <BASE> --name-status` (atau `git diff --name-status` bila `include_staged` bernilai `false`) untuk berkas tracked, dan `git ls-files --others --exclude-standard` untuk berkas untracked (catat berstatus `A`). Keluarkan seluruh berkas di bawah `<plan_dir>/` dan `profile_path` dari daftar karena keduanya artefak gate, bukan hasil implementasi.
4. Kumpulkan isi perubahan beserta nomor baris: `git diff <BASE> -U3` (atau `git diff -U3` bila `include_staged` bernilai `false`) untuk berkas tracked, dengan pemetaan setiap hunk ke rentang baris berkas hasil; untuk berkas untracked, baca berkas utuh dan perlakukan seluruh barisnya sebagai baris tambahan. Bukti `file:line` wajib merujuk nomor baris berkas hasil.
5. Terapkan filter `scope_paths` bila tidak kosong; catat jumlah berkas yang tersaring keluar sebagai catatan cakupan, jangan diamkan secara senyap.
6. Predikat lanjut: daftar berkas dalam cakupan berjumlah minimal satu. Bila nol setelah filter, hentikan dan laporkan cakupan kosong.

### Fase 2 — Rekonstruksi Kontrak Pembanding

1. Baca `plan_path` dan ekstrak kontrak yang mengikat: daftar langkah atomik, path berkas target yang direncanakan, strategi verifikasi, dan definisi selesai per langkah. Kontrak = isi `plan_path` yang lolos `verify` (sidik = yang disetujui user; kutipan persetujuan di baris `Approval:`). Temuan putaran sebelumnya ada di baris `Findings-<n>` blok `## Execution Status`.
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
3. Bila status `CHANGES_REQUIRED`: sajikan temuan, lalu `AskUserQuestion`: *Remediasi otomatis (putaran <n+1>/2)* · *Revisi rencana (`quickdev:plan`)* · *Terima apa adanya — keputusan commit di tangan user*. Opsi pertama tidak ditawarkan bila `remediation_round` (dari `plan_lock.py status --json`) sudah 2. Hanya opsi pertama yang memanggil `quickdev:execute` dengan `review_findings` dan `plan_path` yang sama; jawaban user dikutip apa adanya di laporan. Dilarang memperbaiki sendiri di sesi review.
4. Bila status `REVIEWED`, nyatakan bahwa keputusan commit atau merge menunggu tindakan user.

## Guardrails

- MUST NOT mengedit, menulis, memformat, atau menghapus berkas kode sumber, test, maupun konfigurasi apa pun.
- MUST NOT menjalankan `git commit`, `git stash`, `git checkout`, `git reset`, `git clean`, `git push`, atau perintah git lain yang memutasi state repositori; hanya perintah baca (`git diff`, `git status`, `git log`, `git ls-files`, `git rev-parse`, `git hash-object -t tree /dev/null`) yang diizinkan. Dari `plan_lock.py` hanya `verify` dan `status`.
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
   REVIEW: <task-name> — <BASE>..working tree (tracked + untracked)
   STATUS: REVIEWED | CHANGES_REQUIRED | NO_CHANGES
   CAKUPAN: <n> berkas dinilai, <n> berkas tersaring keluar oleh scope_paths
   PLAN: <plan_path> — <n> langkah terverifikasi terimplementasi
   PROFIL: <profile_path>
   TEMUAN: <n> BLOCKER / <n> MAJOR / <n> MINOR
   DIMENSI CLEAN: <daftar dimensi tanpa temuan>
   SCOPE CREEP: <daftar berkas berubah di luar rencana | ->
   LANGKAH TERLEWAT: <daftar langkah rencana tanpa perubahan kode | ->
   MODE: strict=<true|false>, include_staged=<true|false>, sesi-sama=<ya|tidak>, base=<Base-Commit | base_ref | HEAD>
   REMEDIASI: putaran <n>/2 — pilihan user "<jawaban apa adanya>" | -
   HANDOFF: execute (remediasi) | plan (revisi) | user (keputusan commit/merge) | tidak ada (NO_CHANGES)
   ```

## Failure path

1. **`quickdev:execute` belum COMPLETED**: hentikan review, jangan baca diff, dan arahkan pemanggil menyelesaikan implementasi beserta verifikasi baseline di `quickdev:execute`.
2. **Tidak ada perubahan sejak base**: bila `git diff <BASE>` dan `git ls-files --others --exclude-standard` tidak memuat berkas di luar `<plan_dir>/` dan `profile_path`, laporkan `NO_CHANGES`; bila `git log <Base-Commit>..HEAD` tidak kosong sementara `<BASE>` bukan `Base-Commit`, perubahan sudah ter-commit → ulangi dengan `base_ref=<Base-Commit>` (atau commit yang disebut user). Hentikan tanpa temuan rekaan.
3. **Dokumen rencana hilang atau tidak terbaca**: hentikan dan minta `plan_path` yang benar; dilarang melanjutkan review kontrak berdasarkan rekonstruksi tebakan dari isi diff.
4. **Berkas profil absen**: bila `profile_path` dan fallback `.dev/profile.md` sama-sama tidak ada, hentikan dan arahkan pemanggil menjalankan `quickdev:profile` lebih dahulu.
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
