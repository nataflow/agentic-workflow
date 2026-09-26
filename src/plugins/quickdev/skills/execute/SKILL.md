---
name: execute
description: Alur ringan quickdev (repo-profile.md, plan/<task>.md, tanpa taskdir) — menerapkan plan/<task>.md berstatus APPROVED ke kode dan menjalankan verifikasi baseline repo-profile.md; dipanggil eksplisit lewat /quickdev:execute.
disable-model-invocation: true
---

## THE IRON LAW

DILARANG MEMULAI EKSEKUSI JIKA DOKUMEN RENCANA IMPLEMENTASI BELUM BERSTATUS APPROVED SECARA EKSPLISIT. SETIAP PERUBAHAN KODE SUMBER WAJIB MENGIKUTI URUTAN LANGKAH ATOMIK PADA DOKUMEN RENCANA — ATAU TEMUAN `review_findings` YANG BERADA DI DALAM CAKUPAN RENCANA — TANPA MENAMBAHKAN PERUBAHAN DI LUAR CAKUPAN; PERBAIKAN GALAT VERIFIKASI TUNDUK PADA BATAS YANG SAMA. SETELAH SELURUH LANGKAH SELESAI, PERINTAH VERIFIKASI BASELINE (TYPECHECK, LINTER, TEST) WAJIB DIJALANKAN ULANG SECARA LENGKAP DAN MERAIH STATUS LOLOS TANPA REGRESI BARU. DILARANG MENANDAI TUGAS SELESAI TANPA BUKTI LOG VERIFIKASI NYATA.

## Precondition [REQUIRED]

1. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py verify --plan <plan_path>` → `VERIFY PASS`. `FAIL` (bukan APPROVED, tanpa `Plan-Hash`, atau Section 1–5 berubah sesudah disetujui) → hentikan, arahkan ke `quickdev:plan`.
2. Mode dari `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py start` (Fase 0 butir 1). `awal`: `git status --porcelain -uall` tidak memuat perubahan di luar `<plan_dir>/` (direktori `plan_path`) dan `profile_path` — perubahan lain wajib di-commit atau di-stash user lebih dulu agar diff `quickdev:review` hanya berisi hasil eksekusi. `resume`/`remediasi`: perubahan uncommitted diizinkan hanya pada berkas target Section 3, `<plan_dir>/`, dan `profile_path`; berkas lain → hentikan dan tanyakan user. Dilarang meminta user meng-commit atau men-stash kerja parsial: `quickdev:review` membandingkan terhadap `Base-Commit`, bukan `HEAD`.
3. Runtime, compiler, dan package manager yang dibutuhkan (seperti Node/TypeScript, Python, Go, dll.) aktif dan dapat menjalankan script verifikasi baseline.
4. Profil repositori pada `profile_path` tersedia sebagai acuan baseline error yang diakui dan panduan layer; bila absen, hentikan dan arahkan pemanggil ke `quickdev:profile` (jangan `backenddev:profile`/`frontenddev:profile`).
5. Tool `Edit`, `Write`, dan `Bash` tersedia untuk mutasi berkas dan eksekusi perintah verifikasi.
6. `python3` (3.9+) tersedia untuk `plan_lock.py`.

## Koeksistensi [REQUIRED]

- Skill ini bagian dari alur ringan `quickdev` (`repo-profile.md`, `plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backenddev:*` atau `frontenddev:*` sebagai pengganti: `backenddev:profile`/`frontenddev:profile` menulis `.claude/profile/<plugin>/`, bukan `repo-profile.md`, dan tidak memenuhi precondition skill ini.
- Bila konteks sesi memuat blok `<backenddev-tech-lead-gate>` atau `<frontenddev-lead-gate>`:
  - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`, `repo-profile.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
  - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backenddev:tech-lead | frontenddev:lead>` (taskdir + brief)". Jangan memilih sendiri.
- `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
- Penanda opt-out `.claude/workflow` (nama plugin yang boleh menggerbangi repo, dipisah spasi/baris): isi `quickdev` membuat hook SessionStart `backenddev`/`frontenddev` diam; isi `frontenddev quickdev` hanya menyalakan hook `frontenddev`.

## Parameter [REQUIRED]

- `plan_path` — string — `[REQUIRED]` — path berkas rencana implementasi yang berstatus `APPROVED` (contoh: `plan/user-auth-jwt.md`).
- `profile_path` — string — default: nilai `Profile:` di metadata `plan_path`; bila absen, `repo-profile.md`, lalu `.dev/profile.md`.
- `auto_verify` — boolean — default `true` — bila `true`, menjalankan otomatis perintah verifikasi baseline setelah langkah implementasi tuntas; bila `false`, status akhir `VERIFICATION_MANUAL_REQUIRED`.
- `strict_baseline` — boolean — default `true` — bila `true`, warning lint baru ikut diperlakukan sebagai regresi yang wajib diperbaiki; bila `false`, hanya error typecheck, lint, dan test baru yang memblokir.
- `stop_on_error` — boolean — default `true` — bila `true`, menghentikan eksekusi langkah berikutnya segera saat salah satu langkah atomik mengalami error.
- `update_plan_checklist` — boolean — default `true` — bila `true`, memperbarui tanda checkbox (`- [x]`) pada berkas `plan_path` secara real-time.
- `max_fix_iterations` — integer — default `3` — batas maksimal iterasi perbaikan mandiri saat terjadi kegagalan pada tahap verifikasi baseline.
- `review_findings` — string — default `""` — daftar temuan `quickdev:review` berstatus `CHANGES_REQUIRED` (lokasi, dimensi, rekomendasi). Bila terisi, skill berjalan pada putaran remediasi: yang dikerjakan adalah temuan, bukan langkah rencana. Terisi hanya sesudah user memilih *Remediasi otomatis* di `quickdev:review`; Fase 0 menjalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py start --plan <plan_path> --findings --findings-text "<temuan ringkas>"` (plafon 2 putaran). `START FAIL` plafon → jangan mengubah kode; serahkan temuan tersisa ke user.

## Workflow

### Fase 0 — Validasi Status Rencana & Persiapan Lingkungan

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py start --plan <plan_path>` (tambah `--findings --findings-text "<temuan ringkas>"` bila `review_findings` terisi) sebelum mutasi apa pun. Skrip memanggil `verify`, menurunkan mode dari berkas, dan menulis blok `## Execution Status` (`Status`, `Base-Commit`, `Remediation-Round`, `Findings-<n>`); `Base-Commit` tidak pernah ditimpa:

   | Keadaan `plan_path` | Mode | Tindakan |
   |---|---|---|
   | `verify` FAIL | — | hentikan, ke `quickdev:plan` (Failure path 1) |
   | tanpa blok, nol `[x]` | `awal` | predikat tree bersih Precondition 2; `Base-Commit` = HEAD atau `none` (repo tanpa commit) |
   | blok `IN_PROGRESS`/`BLOCKED`, atau tanpa blok tetapi ada `[x]` | `resume` | butir 2 di bawah; `Base-Note` menandai base yang diisi sesudah sesi putus |
   | blok `COMPLETED` + `--findings` | `remediasi` | butir 5 di bawah; plafon 2 putaran |
   | blok `VERIFICATION_MANUAL_REQUIRED` | `manual` | butir 3 di bawah |
   | blok `COMPLETED`/`COMPLETED (manual)` tanpa temuan | `selesai` | tidak ada kerja; tawarkan `quickdev:review` |

2. Mode `resume`:
   - Pagar tree: `git status --porcelain -uall`; setiap berkas berubah wajib termasuk berkas target Section 3, `<plan_dir>/`, atau `profile_path`. Berkas lain → hentikan dan tanyakan user; jangan ikut di-review sebagai hasil eksekusi.
   - Periksa langkah `[x]` terakhir: berkas targetnya wajib berubah terhadap base (`git diff --stat <Base-Commit> -- <berkas>`, atau `git ls-files --others --exclude-standard -- <berkas>` untuk berkas baru; `Base-Commit: none` → berkas cukup ada). Tidak berubah → centangnya tidak sah: kembalikan ke `[ ]` dan catat di laporan.
   - Lanjutkan Fase 1 dari langkah `[ ]` pertama. Baca ulang berkas target sebelum mengedit karena langkah bisa setengah jadi; edit harus idempoten (jangan menambah blok yang sudah ada).
3. Mode `manual`: tampilkan perintah verifikasi manual dari `Verification` blok, lalu `AskUserQuestion`: *Sudah dijalankan, lolos* · *Gagal (sebut galatnya)* · *Belum*. Hanya opsi pertama yang menjalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py confirm --plan <plan_path> --answer "<jawaban user apa adanya>"`; opsi kedua menjalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py close --plan <plan_path> --status BLOCKED --blocked-step verifikasi --verification "<galat dari user>"`, lalu user memilih: panggil `quickdev:execute` lagi (mode `resume` → langsung Fase 3 dengan galat itu) atau revisi rencana. Tanpa mutasi kode di mode ini.
4. Ekstrak seluruh daftar langkah implementasi atomik dari Section `## 3. Atomic Implementation Steps`:
   - Petakan setiap langkah ke berkas target, tipe mutasi kode (membuat berkas baru, mengedit fungsi/metode, menambahkan tipe DTO, memperbarui query database), dan kriteria selesai.
   - Identifikasi urutan dependensi langkah (contoh: skema database dan DTO wajib selesai sebelum implementasi service atau controller).
   - Baca daftar perintah verifikasi baseline dari Section `## 4. Verification & Testing Strategy` rencana dan tabel Section 5 `profile_path`.
5. Mode `remediasi` (`review_findings` terisi):
   - Petakan setiap temuan ke langkah rencana dan berkas target di Section 3; temuan yang menuntut berkas atau perilaku di luar rencana tidak dikerjakan dan dialihkan ke Failure path 5.
   - Jadikan temuan terpetakan sebagai daftar kerja Fase 1 menggantikan langkah rencana; checklist yang sudah `- [x]` tidak diubah.

### Fase 1 — Eksekusi Langkah Implementasi Atomik (Per-Step Loop)

1. Lakukan iterasi eksekusi untuk setiap langkah implementasi (atau setiap temuan pada putaran remediasi) secara berurutan:
2. **Eksekusi Perubahan Berkas (Code Mutation)**:
   - Berkas baru: buat di direktori layer yang benar sesuai konvensi `profile_path`, dengan impor dependensi yang valid.
   - Berkas eksisting: edit terarah pada blok yang relevan tanpa merusak kode sekitar; pertahankan komentar, anotasi tipe, dan docstring yang tidak terkait perubahan.
3. **Verifikasi Step-Level (Inspeksi Lokal)**:
   - Periksa sintaks berkas valid dan impor modul terhubung tanpa circular dependency.
   - Jika `update_plan_checklist: true`, perbarui checkbox langkah terkait di `plan_path` menjadi `- [x]` setelah mutasi berhasil diterapkan. Hanya baris checkbox Section 3 dan blok `## Execution Status` yang boleh diubah di `plan_path`; teks langkah, Section 1, 2, 4, 5, dan metadata dilarang disentuh.
4. **Evaluasi Penanganan Error Langkah**: jika penulisan berkas gagal, sintaks rusak, atau terjadi konflik edit dan `stop_on_error: true`, hentikan loop, pertahankan checklist terakhir di `plan_path`, lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py close --plan <plan_path> --status BLOCKED --blocked-step <n> --verification "<penyebab>"`. Kerja parsial dibiarkan di working tree; pemanggilan `quickdev:execute` berikutnya masuk mode `resume`.

### Fase 2 — Kelengkapan Test Suite

1. Cocokkan skenario Section 4 rencana (happy path, edge case, validation error) dengan test yang ditulis pada langkah Fase 1; skenario tanpa test ditulis hanya pada berkas test yang tercantum di rencana. Skenario tanpa berkas test di rencana dicatat sebagai celah rencana di laporan, bukan dibuatkan berkas baru.
2. Bila rencana tidak memuat skenario test (`require_test_plan: false` di `quickdev:plan`), lewati fase ini dan catat `Tests: tidak direncanakan` di laporan. Dilarang memasang framework atau dependensi test yang tidak tercantum di Section 3.
3. Pastikan test assertions memverifikasi data contract, status code HTTP, dan exception mapping secara tepat.

### Fase 3 — Eksekusi Baseline Verifikasi Penuh (Full Verification Gate)

1. Jika `auto_verify: true`, jalankan tiap perintah baseline dari tabel Section 5 `profile_path` (dan Section 4 rencana) secara sequential, dari kolom `Cwd` sebagai `(cd <Cwd> && <perintah>)` dari root repo; `Cwd` kosong (profil lama) → root, dan catat `cwd tidak tercatat` di laporan:
   - **Perintah 1 — Typecheck** (contoh: `pnpm typecheck`, `mypy .`): 0 error baru.
   - **Perintah 2 — Linter** (contoh: `pnpm lint`, `ruff check .`): auto-fix format atau import ordering hanya pada berkas yang disentuh rencana (contoh: `eslint --fix <berkas>`); dilarang menjalankan fixer ke seluruh repo.
   - **Perintah 3 — Unit & Integration Tests** (contoh: `pnpm test`, `pytest`): test baru dan eksisting berstatus `PASSED`. Baris Test profil `TIDAK_ADA` → lewati, catat `test=TIDAK_ADA`, dan sertakan langkah QA manual Section 4 di laporan.
   - **Perintah 4 — Build Check** (bila tercatat di profil, contoh: `pnpm build`, `go build ./...`).
2. Bandingkan per perintah dengan baris Section 5 `profile_path`:
   - `PASSED` → galat apa pun sekarang = regresi.
   - `FAILED` → galat yang penandanya ada di kolom Known issues = bawaan; galat lain = regresi.
   - `SKIPPED` / `TIMEOUT` / `UNVERIFIED_ENV_NOT_READY` → jalankan sekarang. Gagal karena lingkungan (modul/binari hilang) → status akhir `VERIFICATION_MANUAL_REQUIRED`, bukan `COMPLETED`. Jalan tetapi gagal → tidak ada pembanding: laporkan tiap galat di berkas yang disentuh rencana sebagai regresi, sisanya sebagai `UNVERIFIED` di laporan, lalu minta user memutuskan.
   - `TIDAK_ADA` → lewati, catat `<jenis>=TIDAK_ADA`.
   - Profil lama tanpa tabel Section 5 → status tidak diketahui, perlakukan seperti `UNVERIFIED_ENV_NOT_READY` dan sarankan `quickdev:profile mode=REFRESH`.
3. Regresi: perbaiki hanya bila perbaikannya berada di berkas target Section 3 (termasuk berkas test yang tercantum di sana), hingga `max_fix_iterations`; bila masih gagal, alihkan ke Failure path 2. Perbaikan yang menuntut berkas di luar Section 3 → hentikan loop, `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py close --plan <plan_path> --status BLOCKED --blocked-step <n> --verification "<perintah>: <galat> di <berkas:baris> (di luar rencana)"`, dan laporkan ke user. Jalan lanjutnya revisi lewat `quickdev:plan` (`unlock` → tambah langkah → `lock`) lalu `quickdev:execute` mode `resume`.
4. Seluruh verifikasi hijau (atau hanya galat bawaan): lanjutkan ke penutupan.

### Fase 4 — Penyusunan Laporan Eksekusi & Penutupan Tugas

1. Tutup lewat `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py close --plan <plan_path> --status <COMPLETED | VERIFICATION_MANUAL_REQUIRED> --verification "<ringkasan>"`. Skrip memanggil `verify`, menulis/menimpa blok `## Execution Status` (`Status`, `Verification`, `Blocked-Step`, `Timestamp`; `Remediation-Round` ditulis `start`), dan menolak `COMPLETED` bila masih ada `- [ ]`. Dilarang menulis blok itu dengan tangan.
2. Susun laporan ringkasan implementasi komprehensif yang mencakup:
   - Daftar seluruh file baru yang dibuat dan berkas eksisting yang dimodifikasi.
   - Ringkasan log eksekusi verifikasi baseline (Typecheck: PASS, Lint: PASS, Tests: PASS).
   - Catatan instruksi pengujian manual untuk user (jika melibatkan interaksi visual UI atau pengetesan API via cURL/Postman).
3. Set status terminal `COMPLETED`, atau `VERIFICATION_MANUAL_REQUIRED` bila verifikasi tidak dijalankan otomatis atau lingkungan belum siap (Fase 3 butir 2).
4. Sajikan hasil akhir implementasi kepada user secara transparan.
5. Tawarkan `quickdev:review`: biarkan perubahan tetap uncommitted di working tree dan sebutkan `plan_path` sebagai kontrak pembanding, agar `quickdev:review` dapat menilai diff sejak `Base-Commit` sebelum keputusan commit atau merge diambil user. `VERIFICATION_MANUAL_REQUIRED`: minta user menjalankan perintah manual lalu memanggil `quickdev:execute` lagi (mode `manual`) untuk mencatat konfirmasinya.

## Guardrails

- MUST NOT mengeksekusi perubahan kode jika berkas rencana implementasi belum berstatus `Status: APPROVED`.
- MUST NOT menyimpang dari langkah-langkah yang telah disepakati di dalam dokumen rencana implementasi, termasuk mengubah teks langkah agar cocok dengan hasil kerja.
- MUST NOT membiarkan ada error typecheck, lint, atau failing test yang belum terselesaikan sebelum menyatakan tugas selesai.
- MUST NOT melakukan commit atau merge atas perubahan hasil eksekusi; status `COMPLETED` hanya membuka `quickdev:review`, bukan izin merilis.
- MUST NOT menghapus kode lama secara sembarangan tanpa instruksi eksplisit di dokumen rencana.
- MUST NOT memasang framework/dependensi test yang tidak tercantum di Section 3 rencana.
- MUST NOT menulis `Status`, `Base-Commit`, `Remediation-Round`, `Findings-<n>`, atau `Manual-Confirmation` blok `## Execution Status` dengan tangan; semuanya ditulis `plan_lock.py`.
- MUST NOT memalsukan, memotong, atau mengabaikan log kegagalan verifikasi baseline runtime.
- Seluruh hasil perubahan kode sumber wajib dapat dibuktikan melalui eksekusi perintah verifikasi nyata.

## Output [REQUIRED]

Skill ini menghasilkan perubahan kode sumber yang terverifikasi dan laporan terminal terdefinisi:

1. **Hasil Perubahan Kode & Artefak**:
   - Berkas kode sumber dan test suite baru/termodifikasi di repositori.
   - Dokumen `plan_path` terperbarui dengan seluruh checklist tercentang (`- [x]`) dan satu blok `## Execution Status` terbaru.
   - Log bukti eksekusi perintah verifikasi baseline (Typecheck: PASS, Lint: PASS, Tests: PASS).
2. **Status Terminal**: `COMPLETED` | `VERIFICATION_MANUAL_REQUIRED` | `BLOCKED` — `COMPLETED` (atau `COMPLETED (manual)`) membuka `quickdev:review` atas diff sejak `Base-Commit` terhadap `plan_path`; `VERIFICATION_MANUAL_REQUIRED` menahan `quickdev:review` sampai user menjalankan perintah manual dan `quickdev:execute` (mode `manual`) mencatat konfirmasinya; `BLOCKED` tidak membuka `quickdev:review` — user memilih: lanjut (panggil `quickdev:execute` lagi → mode `resume`), revisi rencana (`quickdev:plan`; blok `## Execution Status` dipertahankan), atau rollback (hanya atas perintah eksplisit user).
3. **Format Ringkasan Akhir (Maksimal 17 Baris)**:
   ```
   EXECUTE: <plan_path> — putaran <awal | resume dari langkah n/m | remediasi ke-n/2 | manual>
   BASE: <Base-Commit> <(Base-Note) | >
   STATUS: COMPLETED | VERIFICATION_MANUAL_REQUIRED | BLOCKED
   LANGKAH: <n>/<n> tercentang
   REMEDIASI: <n>/<n> temuan review_findings tertangani | -
   BERKAS: <n> baru, <n> diubah (uncommitted)
   VERIFIKASI: typecheck=<status> lint=<status> test=<status> build=<status>  (status boleh bawaan(n) atau TIDAK_ADA)
   REGRESI BARU: <n> | - — di luar rencana: <daftar berkas> | -
   ITERASI PERBAIKAN: <n>/<max_fix_iterations>
   HANDOFF: review (plan_path) | user (perintah manual atau blocker)
   ```

## Failure path

1. **Rencana Belum Terkunci atau Berubah**: Jika `verify` FAIL (`DRAFT`, tanpa `Plan-Hash`, atau Section 1–5 berubah sesudah approval), hentikan eksekusi segera, jangan lakukan mutasi kode, dan arahkan pemanggil memulihkan teks rencana atau memperoleh persetujuan ulang user di `quickdev:plan` (`unlock` → revisi → `lock`).
2. **Kegagalan Verifikasi Baseline Pasca-Implementasi**: Jika verifikasi typecheck atau test menghasilkan error setelah mutasi kode:
   - Analisis pesan stack trace error secara mendalam untuk menemukan akar masalah.
   - Terapkan perbaikan terarah pada baris kode yang bermasalah **di berkas target Section 3**; di luar itu → Fase 3 butir 3.
   - Jalankan ulang verifikasi; jika tetap gagal setelah `max_fix_iterations` iterasi, tutup `BLOCKED` lewat `plan_lock.py close`, laporkan rincian blocker, dan tawarkan opsi rollback — dilarang menjalankan rollback (`git checkout`, `git reset`, `git stash`, hapus berkas) tanpa persetujuan eksplisit user.
3. **Konflik File / Berkas Target Hilang**: Jika berkas target yang tercantum di rencana tidak ditemukan di filesystem, periksa kembali path relatif atau buat berkas jika memang direncanakan sebagai berkas baru.
4. **Restriksi Eksekusi Perintah Terminal**: Jika environment tidak mengizinkan eksekusi perintah baseline otomatis, catat status `VERIFICATION_MANUAL_REQUIRED` dan berikan daftar perintah manual yang harus dijalankan user secara mandiri.
5. **Temuan Review di Luar Cakupan Rencana**: Jika temuan pada `review_findings` menuntut perubahan berkas atau perilaku yang tidak ada di rencana, jangan kerjakan temuan itu; selesaikan temuan yang berada di dalam rencana, set status `BLOCKED` dengan daftar temuan di luar rencana, dan arahkan pemanggil merevisi rencana lewat `quickdev:plan` sebelum putaran remediasi berikutnya.
6. **Plafon Remediasi Habis**: `start --findings` menolak putaran ke-3. Jangan mengubah kode; sajikan temuan tersisa ke user untuk diputuskan (terima apa adanya, revisi rencana, atau perbaikan manual).

## STYLE

- Gunakan kalimat imperatif aktif dan Observable Predicate pada seluruh langkah mutasi kode dan checkpoint verifikasi.
- Tuliskan path file, nama simbol, dan perintah verifikasi dalam format inline code backticks (contoh: `pnpm test`, `src/services/order.service.ts`).
- Sajikan log bukti verifikasi secara terstruktur menggunakan format blok kode ringkas.
- Pertahankan istilah domain teknis (Code Mutation, Atomic Step, Checklist, Verification Baseline, Typecheck, Linter, Test Suite, Rollback, Handoff) tanpa penerjemahan paksa.
- Pastikan kalimat mengalir natural dan padat informasi dengan rasio sinyal terhadap token yang tinggi.
