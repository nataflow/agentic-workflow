---
name: execute
description: Alur ringan quickdev (repo-profile.md, plan/<task>.md, tanpa taskdir) — menerapkan plan/<task>.md berstatus APPROVED ke kode dan menjalankan verifikasi baseline repo-profile.md; dipanggil eksplisit lewat /quickdev:execute.
disable-model-invocation: true
---

## THE IRON LAW

DILARANG MEMULAI EKSEKUSI JIKA DOKUMEN RENCANA IMPLEMENTASI BELUM BERSTATUS APPROVED SECARA EKSPLISIT. SETIAP PERUBAHAN KODE SUMBER WAJIB MENGIKUTI URUTAN LANGKAH ATOMIK PADA DOKUMEN RENCANA — ATAU TEMUAN `review_findings` YANG BERADA DI DALAM CAKUPAN RENCANA — TANPA MENAMBAHKAN PERUBAHAN DI LUAR CAKUPAN. SETELAH SELURUH LANGKAH SELESAI, PERINTAH VERIFIKASI BASELINE (TYPECHECK, LINTER, TEST) WAJIB DIJALANKAN ULANG SECARA LENGKAP DAN MERAIH STATUS LOLOS TANPA REGRESI BARU. DILARANG MENANDAI TUGAS SELESAI TANPA BUKTI LOG VERIFIKASI NYATA.

## Precondition [REQUIRED]

1. Dokumen rencana implementasi pada path `plan_path` (misal: `plan/<task-name>.md`) tersedia di filesystem lokal dan memiliki status `Status: APPROVED`.
2. Status git terverifikasi lewat `git status --porcelain`: pada putaran awal (`review_findings` kosong) keluarannya tidak memuat perubahan selain `plan_path` dan `profile_path` — perubahan lain wajib di-commit atau di-stash user lebih dulu agar diff `quickdev:review` hanya berisi hasil eksekusi; pada putaran remediasi, perubahan uncommitted hasil putaran sebelumnya memang diharapkan dan `plan_path` wajib sudah memuat blok `Execution Status`.
3. Runtime, compiler, dan package manager yang dibutuhkan (seperti Node/TypeScript, Python, Go, dll.) aktif dan dapat menjalankan script verifikasi baseline.
4. Profil repositori pada `profile_path` tersedia sebagai acuan baseline error yang diakui dan panduan layer; bila absen, hentikan dan arahkan pemanggil ke `quickdev:profile` (jangan `backenddev:profile`/`frontenddev:profile`).
5. Tool `Edit`, `Write`, dan `Bash` tersedia untuk mutasi berkas dan eksekusi perintah verifikasi.

## Koeksistensi [REQUIRED]

- Skill ini bagian dari alur ringan `quickdev` (`repo-profile.md`, `plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backenddev:*` atau `frontenddev:*` sebagai pengganti: `backenddev:profile`/`frontenddev:profile` menulis `.claude/profile/<plugin>/`, bukan `repo-profile.md`, dan tidak memenuhi precondition skill ini.
- Bila konteks sesi memuat blok `<backenddev-tech-lead-gate>` atau `<frontenddev-lead-gate>`:
  - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`, `repo-profile.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
  - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backenddev:tech-lead | frontenddev:lead>` (taskdir + brief)". Jangan memilih sendiri.
- `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
- Penanda opt-out `.claude/workflow` (nama plugin yang boleh menggerbangi repo, dipisah spasi/baris): isi `quickdev` membuat hook SessionStart `backenddev`/`frontenddev` diam; isi `frontenddev quickdev` hanya menyalakan hook `frontenddev`.

## Parameter [REQUIRED]

- `plan_path` — string — `[REQUIRED]` — path berkas rencana implementasi yang berstatus `APPROVED` (contoh: `plan/user-auth-jwt.md`).
- `profile_path` — string — default `"repo-profile.md"` — path profil hasil `quickdev:profile`; bila tidak ditemukan, gunakan fallback `.dev/profile.md`.
- `auto_verify` — boolean — default `true` — bila `true`, menjalankan otomatis perintah verifikasi baseline setelah langkah implementasi tuntas; bila `false`, status akhir `VERIFICATION_MANUAL_REQUIRED`.
- `strict_baseline` — boolean — default `true` — bila `true`, warning lint baru ikut diperlakukan sebagai regresi yang wajib diperbaiki; bila `false`, hanya error typecheck, lint, dan test baru yang memblokir.
- `stop_on_error` — boolean — default `true` — bila `true`, menghentikan eksekusi langkah berikutnya segera saat salah satu langkah atomik mengalami error.
- `update_plan_checklist` — boolean — default `true` — bila `true`, memperbarui tanda checkbox (`- [x]`) pada berkas `plan_path` secara real-time.
- `max_fix_iterations` — integer — default `3` — batas maksimal iterasi perbaikan mandiri saat terjadi kegagalan pada tahap verifikasi baseline.
- `review_findings` — string — default `""` — daftar temuan `quickdev:review` berstatus `CHANGES_REQUIRED` (lokasi, dimensi, rekomendasi). Bila terisi, skill berjalan pada putaran remediasi: yang dikerjakan adalah temuan, bukan langkah rencana.

## Workflow

### Fase 0 — Validasi Status Rencana & Persiapan Lingkungan

1. Baca berkas rencana implementasi pada path `plan_path`:
   - Periksa header metadata: Pastikan memuat baris `Status: APPROVED`.
   - Jika berkas masih berstatus `Status: DRAFT` atau belum disetujui user, hentikan eksekusi seketika dan instruksikan pemanggil untuk menyelesaikan gate persetujuan di `plan`.
2. Ekstrak seluruh daftar langkah implementasi atomik dari Section `## 3. Atomic Implementation Steps`:
   - Petakan setiap langkah ke berkas target, tipe mutasi kode (membuat berkas baru, mengedit fungsi/metode, menambahkan tipe DTO, memperbarui query database), dan kriteria selesai.
   - Identifikasi urutan dependensi langkah (contoh: skema database dan DTO wajib selesai sebelum implementasi service atau controller).
3. Baca daftar perintah verifikasi baseline dari Section `## 4. Verification & Testing Strategy` pada rencana implementasi dan `profile_path`.
4. Bila `review_findings` terisi (putaran remediasi):
   - Petakan setiap temuan ke langkah rencana dan berkas target di Section 3; temuan yang menuntut berkas atau perilaku di luar rencana tidak dikerjakan dan dialihkan ke Failure path 5.
   - Jadikan temuan terpetakan sebagai daftar kerja Fase 1 menggantikan langkah rencana; checklist yang sudah `- [x]` tidak diubah.

### Fase 1 — Eksekusi Langkah Implementasi Atomik (Per-Step Loop)

1. Lakukan iterasi eksekusi untuk setiap langkah implementasi (atau setiap temuan pada putaran remediasi) secara berurutan:
2. **Eksekusi Perubahan Berkas (Code Mutation)**:
   - Berkas baru: buat di direktori layer yang benar sesuai konvensi `profile_path`, dengan impor dependensi yang valid.
   - Berkas eksisting: edit terarah pada blok yang relevan tanpa merusak kode sekitar; pertahankan komentar, anotasi tipe, dan docstring yang tidak terkait perubahan.
3. **Verifikasi Step-Level (Inspeksi Lokal)**:
   - Periksa sintaks berkas valid dan impor modul terhubung tanpa circular dependency.
   - Jika `update_plan_checklist: true`, perbarui checkbox langkah terkait di `plan_path` menjadi `- [x]` setelah mutasi berhasil diterapkan.
4. **Evaluasi Penanganan Error Langkah**: jika penulisan berkas gagal, sintaks rusak, atau terjadi konflik edit dan `stop_on_error: true`, hentikan loop, pertahankan checklist terakhir di `plan_path`, dan set status `BLOCKED` beserta langkah penyebabnya.

### Fase 2 — Kelengkapan Test Suite

1. Cocokkan skenario Section 4 rencana (happy path, edge case, validation error) dengan test yang ditulis pada langkah Fase 1; skenario tanpa test ditulis hanya pada berkas test yang tercantum di rencana. Skenario tanpa berkas test di rencana dicatat sebagai celah rencana di laporan, bukan dibuatkan berkas baru.
2. Bila rencana tidak memuat skenario test (`require_test_plan: false` di `quickdev:plan`), lewati fase ini dan catat `Tests: tidak direncanakan` di laporan.
3. Pastikan test assertions memverifikasi data contract, status code HTTP, dan exception mapping secara tepat.

### Fase 3 — Eksekusi Baseline Verifikasi Penuh (Full Verification Gate)

1. Jika `auto_verify: true`, jalankan perintah baseline persis seperti tercatat di `profile_path` (dan Section 4 rencana) secara sequential:
   - **Perintah 1 — Typecheck** (contoh: `pnpm typecheck`, `mypy .`): 0 error baru.
   - **Perintah 2 — Linter** (contoh: `pnpm lint`, `ruff check .`): auto-fix format atau import ordering hanya pada berkas yang disentuh rencana (contoh: `eslint --fix <berkas>`); dilarang menjalankan fixer ke seluruh repo.
   - **Perintah 3 — Unit & Integration Tests** (contoh: `pnpm test`, `pytest`): test baru dan eksisting berstatus `PASSED`.
   - **Perintah 4 — Build Check** (bila tercatat di profil, contoh: `pnpm build`, `go build ./...`).
2. Bandingkan hasil dengan baseline bawaan di `profile_path`:
   - Error baru di luar baseline: diagnosa dan perbaiki di tempat hingga `max_fix_iterations`; bila masih gagal, alihkan ke Failure path 2.
   - Seluruh verifikasi hijau: lanjutkan ke penutupan.

### Fase 4 — Penyusunan Laporan Eksekusi & Penutupan Tugas

1. Perbarui status akhir pada dokumen `plan_path`:
   - Tulis blok penutupan di akhir berkas — timpa blok lama bila sudah ada, jangan menambah blok kedua: `Execution Status: <status terminal>`, `Verification: <ringkasan hasil>`, `Remediation Round: <0 | n>`, `Timestamp: <ISO-Date>`.
2. Susun laporan ringkasan implementasi komprehensif yang mencakup:
   - Daftar seluruh file baru yang dibuat dan berkas eksisting yang dimodifikasi.
   - Ringkasan log eksekusi verifikasi baseline (Typecheck: PASS, Lint: PASS, Tests: PASS).
   - Catatan instruksi pengujian manual untuk user (jika melibatkan interaksi visual UI atau pengetesan API via cURL/Postman).
3. Set status terminal `COMPLETED`, atau `VERIFICATION_MANUAL_REQUIRED` bila verifikasi tidak dijalankan otomatis.
4. Sajikan hasil akhir implementasi kepada user secara transparan.
5. Tawarkan `quickdev:review`: biarkan perubahan tetap uncommitted di working tree dan sebutkan `plan_path` sebagai kontrak pembanding, agar `quickdev:review` dapat menilai diff sebelum keputusan commit atau merge diambil user.

## Guardrails

- MUST NOT mengeksekusi perubahan kode jika berkas rencana implementasi belum berstatus `Status: APPROVED`.
- MUST NOT menyimpang dari langkah-langkah yang telah disepakati di dalam dokumen rencana implementasi.
- MUST NOT membiarkan ada error typecheck, lint, atau failing test yang belum terselesaikan sebelum menyatakan tugas selesai.
- MUST NOT melakukan commit atau merge atas perubahan hasil eksekusi; status `COMPLETED` hanya membuka `quickdev:review`, bukan izin merilis.
- MUST NOT menghapus kode lama secara sembarangan tanpa instruksi eksplisit di dokumen rencana.
- MUST NOT memalsukan, memotong, atau mengabaikan log kegagalan verifikasi baseline runtime.
- Seluruh hasil perubahan kode sumber wajib dapat dibuktikan melalui eksekusi perintah verifikasi nyata.

## Output [REQUIRED]

Skill ini menghasilkan perubahan kode sumber yang terverifikasi dan laporan terminal terdefinisi:

1. **Hasil Perubahan Kode & Artefak**:
   - Berkas kode sumber dan test suite baru/termodifikasi di repositori.
   - Dokumen `plan_path` terperbarui dengan seluruh checklist tercentang (`- [x]`) dan satu blok penutupan `Execution Status` terbaru.
   - Log bukti eksekusi perintah verifikasi baseline (Typecheck: PASS, Lint: PASS, Tests: PASS).
2. **Status Terminal**: `COMPLETED` | `VERIFICATION_MANUAL_REQUIRED` | `BLOCKED` — `COMPLETED` membuka `quickdev:review` atas diff working tree terhadap `plan_path`; `VERIFICATION_MANUAL_REQUIRED` menahan `quickdev:review` sampai user menjalankan perintah manual dan mengonfirmasi hasilnya; `BLOCKED` tidak membuka `quickdev:review` — user memilih lanjut perbaiki, revisi rencana di `quickdev:plan`, atau rollback.
3. **Format Ringkasan Akhir (Maksimal 17 Baris)**:
   ```
   EXECUTE: <plan_path> — putaran <awal | remediasi ke-n>
   STATUS: COMPLETED | VERIFICATION_MANUAL_REQUIRED | BLOCKED
   LANGKAH: <n>/<n> tercentang
   REMEDIASI: <n>/<n> temuan review_findings tertangani | -
   BERKAS: <n> baru, <n> diubah (uncommitted)
   VERIFIKASI: typecheck=<status> lint=<status> test=<status> build=<status>
   REGRESI BARU: <n> | -
   ITERASI PERBAIKAN: <n>/<max_fix_iterations>
   HANDOFF: review (plan_path) | user (perintah manual atau blocker)
   ```

## Failure path

1. **Rencana Belum Berstatus APPROVED**: Jika `plan_path` masih berstatus `DRAFT` atau ditolak, hentikan eksekusi segera, jangan lakukan mutasi kode, dan arahkan pemanggil untuk memperoleh persetujuan user di `quickdev:plan`.
2. **Kegagalan Verifikasi Baseline Pasca-Implementasi**: Jika verifikasi typecheck atau test menghasilkan error setelah mutasi kode:
   - Analisis pesan stack trace error secara mendalam untuk menemukan akar masalah.
   - Terapkan perbaikan terarah pada baris kode yang bermasalah.
   - Jalankan ulang verifikasi; jika tetap gagal setelah `max_fix_iterations` iterasi, set status `BLOCKED`, laporkan rincian blocker, dan tawarkan opsi rollback — dilarang menjalankan rollback (`git checkout`, `git reset`, `git stash`, hapus berkas) tanpa persetujuan eksplisit user.
3. **Konflik File / Berkas Target Hilang**: Jika berkas target yang tercantum di rencana tidak ditemukan di filesystem, periksa kembali path relatif atau buat berkas jika memang direncanakan sebagai berkas baru.
4. **Restriksi Eksekusi Perintah Terminal**: Jika environment tidak mengizinkan eksekusi perintah baseline otomatis, catat status `VERIFICATION_MANUAL_REQUIRED` dan berikan daftar perintah manual yang harus dijalankan user secara mandiri.
5. **Temuan Review di Luar Cakupan Rencana**: Jika temuan pada `review_findings` menuntut perubahan berkas atau perilaku yang tidak ada di rencana, jangan kerjakan temuan itu; selesaikan temuan yang berada di dalam rencana, set status `BLOCKED` dengan daftar temuan di luar rencana, dan arahkan pemanggil merevisi rencana lewat `quickdev:plan` sebelum putaran remediasi berikutnya.

## STYLE

- Gunakan kalimat imperatif aktif dan Observable Predicate pada seluruh langkah mutasi kode dan checkpoint verifikasi.
- Tuliskan path file, nama simbol, dan perintah verifikasi dalam format inline code backticks (contoh: `pnpm test`, `src/services/order.service.ts`).
- Sajikan log bukti verifikasi secara terstruktur menggunakan format blok kode ringkas.
- Pertahankan istilah domain teknis (Code Mutation, Atomic Step, Checklist, Verification Baseline, Typecheck, Linter, Test Suite, Rollback, Handoff) tanpa penerjemahan paksa.
- Pastikan kalimat mengalir natural dan padat informasi dengan rasio sinyal terhadap token yang tinggi.
