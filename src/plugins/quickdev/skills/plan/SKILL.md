---
name: plan
description: Alur ringan quickdev (repo-profile.md, plan/<task>.md, tanpa taskdir) — menyusun satu berkas rencana plan/<task>.md dari kebutuhan yang sudah jelas lalu meminta approval user. Bukan brief taskdir backenddev/frontenddev; dipanggil eksplisit lewat /quickdev:plan.
disable-model-invocation: true
---

## THE IRON LAW

DILARANG MEMULAI IMPLEMENTASI ATAU MENULIS KODE SUMBER SEBELUM DOKUMEN RENCANA DI PLAN DIREKTORI DISETUJUI USER SECARA EKSPLISIT. SETIAP LANGKAH KERJA PADA DOKUMEN RENCANA WAJIB BERSIFAT ATOMIK DAN MENYEBUTKAN PATH BERKAS TARGET SECARA EKSPLISIT BESERTA BUKTI STRATEGI VERIFIKASI. DILARANG MEMBUAT LANGKAH KERJA YANG MENGGABUNGKAN PERUBAHAN MULTI-LAYER TANPA URUTAN DEPENDENSI YANG JELAS. DOKUMEN RENCANA WAJIB DISIMPAN PADA PATH `<plan_dir>/<task_name>.md` SEBAGAI SINGLE SOURCE OF TRUTH.

## Precondition [REQUIRED]

1. Status `quickdev:explore` dan `quickdev:clarify` dibaca dari percakapan (`EXPLORED`, `CLARIFIED` atau `SKIPPED`) atau dari user, lalu ditulis ke metadata `Gates:` rencana. Keduanya tidak ada di percakapan → Failure path 5; `DILEWATI` hanya atas pilihan eksplisit user.
2. Spesifikasi kebutuhan fungsional, kontrak data API, skema payload, atau alur UI/UX telah terkunci tanpa ambiguitas yang tersisa.
3. Direktori kerja repositori memiliki izin tulis aktif untuk membuat folder `plan/` dan berkas rencana implementasi markdown.
4. Profil repositori pada `profile_path` tersedia sebagai panduan arsitektur dan baseline verifikasi; bila absen, hentikan dan arahkan pemanggil ke `quickdev:profile` (jangan `backenddev:profile`/`frontenddev:profile`) karena perintah baseline rencana wajib diambil dari profil.
5. `python3` (3.9+) tersedia untuk `plan_lock.py`, yang mengunci rencana saat approval.

## Koeksistensi [REQUIRED]

- Skill ini bagian dari alur ringan `quickdev` (`repo-profile.md`, `plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backenddev:*` atau `frontenddev:*` sebagai pengganti: `backenddev:profile`/`frontenddev:profile` menulis `.claude/profile/<plugin>/`, bukan `repo-profile.md`, dan tidak memenuhi precondition skill ini.
- Bila konteks sesi memuat blok `<backenddev-tech-lead-gate>` atau `<frontenddev-lead-gate>`:
  - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`, `repo-profile.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
  - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backenddev:tech-lead | frontenddev:lead>` (taskdir + brief)". Jangan memilih sendiri.
- `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
- Penanda opt-out `.claude/workflow` (nama plugin yang boleh menggerbangi repo, dipisah spasi/baris): isi `quickdev` membuat hook SessionStart `backenddev`/`frontenddev` diam; isi `frontenddev quickdev` hanya menyalakan hook `frontenddev`.

## Parameter [REQUIRED]

- `task_name` — string — `[REQUIRED]` — nama unik tugas dalam format kebab-case (contoh: `user-auth-jwt`, `order-status-filter`). Bila pemanggil tidak memberikannya, turunkan dari permintaan user dan konfirmasikan bersama draf di Fase 3.
- `task_spec` — string — `[REQUIRED]` — spesifikasi yang disepakati di `quickdev:clarify`; bila tidak dikirim, ambil dari laporan `quickdev:explore` dan spesifikasi `quickdev:clarify` terakhir di percakapan (tidak ada → Failure path 5). Section 1 rencana menjadi satu-satunya sumber spesifikasi bagi `quickdev:execute` dan `quickdev:review`.
- `plan_dir` — string — default `"plan"` — direktori penyimpanan dokumen rencana implementasi di repositori.
- `profile_path` — string — default `"repo-profile.md"` — path profil hasil `quickdev:profile`; bila tidak ditemukan, gunakan fallback `.dev/profile.md`. Bila repo memuat lebih dari satu profil (`git ls-files '*repo-profile.md'`), tanyakan workspace mana lewat `AskUserQuestion`, jangan memakai root diam-diam. Path terpilih ditulis ke metadata `Profile:` sehingga skill hilir membacanya dari rencana.
- `require_test_plan` — boolean — default `true`, **kecuali** baris Test Section 5 profil berstatus `TIDAK_ADA` → default `false` — bila `true`, Section 4 wajib memuat skenario test unit/integration beserta langkah test di Section 3; bila `false`, Section 4 cukup memuat perintah verifikasi baseline. Repo tanpa test runner: Section 4 menulis `Tests: repo tanpa test runner — verifikasi: typecheck/lint/build tercatat + langkah QA manual`. Menambah framework test hanya sebagai langkah rencana eksplisit yang disetujui user.
- `include_rollback` — boolean — default `true` — bila `false`, Section 5 (rollback) tidak ditulis.

## Workflow

### Fase 0 — Inisialisasi & Resolusi Konteks Arsitektur

1. Validasi parameter `task_name` untuk memastikan format kebab-case yang bersih tanpa karakter terlarang:
   - Buat direktori tujuan `plan_dir` (default: `plan/`) pada root repositori jika direktori tersebut belum ada di filesystem.
   - Tetapkan path target berkas dokumen rencana implementasi: `<plan_dir>/<task_name>.md`.
2. Muat aturan arsitektur dari `profile_path`:
   - Identifikasi urutan layer yang berlaku di repositori (contoh Backend: DTO/Schema -> Repository/Model -> Service/Domain -> Controller/Route -> Test; Frontend: Types/Contracts -> API Client/Hooks -> State Store -> UI Components -> Pages/Routes -> Test).
   - Identifikasi perintah verifikasi baseline yang wajib dijalankan pasca-implementasi (typecheck, linter, test runner, production build).
3. Telaah parameter `task_spec` untuk membedah seluruh kebutuhan fungsional, batasan non-fungsional, dan dependensi modul yang harus dirancang.

### Fase 1 — Dekomposisi Langkah Implementasi Atomik

1. Pecah tugas menjadi langkah atomik berurutan dependensi hanya untuk layer yang benar-benar tersentuh `task_spec`; layer yang tidak berubah dilewati, bukan diisi langkah kosong (bugfix satu berkas cukup satu langkah perubahan plus langkah test). Urutan acuan per layer:
   - **Urutan Layer Backend**:
     - *Langkah 1 (Database & Entities)*: Pembuatan migrasi skema database, pembaruan ORM entity model, penambahan tabel/kolom, atau index performa.
     - *Langkah 2 (DTOs & Validation Schemas)*: Definisi interface request/response, validation rules (menggunakan class-validator, Zod, atau Pydantic).
     - *Langkah 3 (Repository & Data Access Layer)*: Pembuatan query database terisolasi, method data access, mapping entity, dan penanganan database constraint.
     - *Langkah 4 (Service & Business Logic)*: Implementasi algoritma logika bisnis, orkestrasi domain, validasi aturan bisnis, dan penanganan custom domain exceptions.
     - *Langkah 5 (Controller & Routing Layer)*: Pembuatan HTTP route handler, middleware attachment (auth/rate-limit), parsing parameter, dan status code mapping.
     - *Langkah 6 (Test Suite & Verification)*: Pembuatan unit test service, mocking repository, dan integration test endpoint API end-to-end.
   - **Urutan Layer Frontend**:
     - *Langkah 1 (Types & API Contracts)*: Definisi interface TypeScript, DTO types, query params, dan skema validasi response payload.
     - *Langkah 2 (API Service Client & Data Fetching)*: Implementasi query/mutation hooks (TanStack React Query, SWR, atau Axios client service).
     - *Langkah 3 (State Management & Store)*: Konfigurasi client store (Zustand, Redux Toolkit, atau context) jika memerlukan sinkronisasi state global antar-komponen.
     - *Langkah 4 (UI Primitive & Feature Components)*: Implementasi komponen visual dengan penanganan cabang state sesuai konvensi profil.
     - *Langkah 5 (Page Container & Routing)*: Integrasi komponen ke halaman rute, sinkronisasi parameter query URL (search/filter/pagination), dan breadcrumbs.
     - *Langkah 6 (Component Tests & Interaction)*: Pembuatan unit test komponen visual, testing library interaction test, dan form validation testing.
2. Pastikan setiap langkah implementasi mencantumkan:
   - File target yang akan dibuat atau diubah (path relatif presisi).
   - Simbol, kelas, atau fungsi yang ditambahkan maupun dimodifikasi.
   - Kriteria selesai (acceptance criteria) per langkah atomik.
3. Bila laporan `quickdev:explore` menyebut modul konsumen terdampak (pemanggil simbol yang signature atau kontraknya berubah), tambahkan langkah "sesuaikan konsumen" dengan berkasnya. `quickdev:execute` hanya boleh memperbaiki galat verifikasi di berkas Section 3, jadi konsumen yang tidak direncanakan membuat eksekusi `BLOCKED`.

### Fase 2 — Penyusunan Dokumen Rencana (`<plan_dir>/<task_name>.md`)

1. Tulis dokumen rencana lengkap ke `<plan_dir>/<task_name>.md` dengan struktur format standar:
   - Header dokumen: `# Implementation Plan — <task_name>`
   - Metadata: baris polos `Kunci: nilai` tepat di bawah H1 (tanpa butir/tebal): `Status: DRAFT`, `Author: quickdev:plan`, `Date: <ISO>`, `Profile: <profile_path>`, `Gates: explore=<EXPLORED|DILEWATI> clarify=<CLARIFIED|SKIPPED|DILEWATI>`. Baris `Approved-At`, `Approval`, dan `Plan-Hash` hanya ditulis `plan_lock.py lock`.
   - Section 1: `## 1. Overview & Objectives` (Tujuan, deskripsi masalah, dan keputusan terkunci dari `clarify` agar spesifikasi tidak bergantung pada riwayat percakapan)
   - Section 2: `## 2. Architecture & Layer Impact` (Tabel modul yang disentuh beserta dampaknya terhadap komponen sekitar)
   - Section 3: `## 3. Atomic Implementation Steps` (Rincian langkah demi langkah bernomor urut dilengkapi checkbox interaktif `- [ ]`)
   - Section 4: `## 4. Verification & Testing Strategy` (Perintah verifikasi baseline aktual dari `profile_path`, ditambah skenario happy path dan edge case bila `require_test_plan: true`)
   - Section 5: `## 5. Rollback & Contingency Strategy` (Langkah mitigasi dan pemulihan; hanya bila `include_rollback: true`)
2. Pastikan format penulisan rencana menggunakan checklist markdown (`- [ ]`) untuk mempermudah pelacakan kemajuan pada gate eksekusi.

### Fase 3 — Presentasi Draf & Permintaan Review User (Approval Gate)

1. Sajikan ringkasan rencana implementasi kepada user secara transparan dan terstruktur:
   - Tampilkan daftar urutan langkah atomik beserta path file target yang akan dimodifikasi.
   - Sorot keputusan desain kunci, perubahan skema database, atau penambahan dependensi baru yang memerlukan perhatian khusus.
   - Informasikan tautan path berkas lengkap pada `<plan_dir>/<task_name>.md` agar user dapat melakukan inspeksi mandiri.
2. Minta persetujuan eksplisit user (Approval Gate):
   - Minta user memberikan persetujuan eksplisit ("approve" / "setuju") atau memberikan poin revisi.
3. Tangani evaluasi respons balik user:
   - **Jika user meminta revisi atau penyesuaian**: Perbarui dokumen `<plan_dir>/<task_name>.md` sesuai feedback, pertahankan `Status: DRAFT`, dan ajukan draf pembaruan untuk review ulang. Rencana yang sudah memuat `## Execution Status`: revisi hanya Section 1–5 lewat Edit terarah; blok itu dan checkbox langkah yang teksnya tidak berubah dipertahankan.
   - **Jika user menyatakan persetujuan eksplisit**: jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py lock --plan <plan_dir>/<task_name>.md --answer "<jawaban user apa adanya>" --profile <profile_path>`. `LOCK FAIL` → perbaiki sebabnya; dilarang menulis `Status: APPROVED` dengan tangan.

### Fase 4 — Penguncian Status Terminal & Handoff

1. Pastikan berkas `<plan_dir>/<task_name>.md` telah berstatus `APPROVED` di filesystem:
   - Pastikan keluaran `LOCK PASS` memuat sidik; `Approved-At`, `Approval`, dan `Plan-Hash` sudah ditulis skrip.
2. Set status terminal `PLAN_APPROVED`.
3. Alirkan dokumen rencana yang telah disetujui ke gate eksekusi: `execute`.

## Guardrails

- MUST NOT melakukan modifikasi, penulisan, atau pembuatan kode sumber fungsional selama gate planning berlangsung.
- MUST NOT mengizinkan transisi status ke `PLAN_APPROVED` tanpa persetujuan eksplisit tertulis dari user.
- MUST NOT membuat langkah implementasi yang ambigu tanpa menyebutkan path berkas target yang pasti.
- MUST NOT melompati seksi strategi pengujian dan verifikasi baseline dalam dokumen rencana.
- MUST NOT mengubah Section 1–5 berkas `APPROVED`. Revisi atas permintaan user: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py unlock --plan <plan_path> --reason "<alasan>"` → revisi → approval ulang (`lock`). Blok `## Execution Status` dipertahankan apa adanya. Rencana `APPROVED` tanpa `Plan-Hash` (format lama) diperlakukan sama: `unlock`, lalu minta user menyetujui ulang.
- Keputusan ruang lingkup fitur dan persetujuan arsitektur rencana implementasi tetap milik mutlak user.

## Output [REQUIRED]

Skill ini menghasilkan dokumen rencana implementasi terstruktur dan status terminal terdefinisi:

1. **Dokumen Rencana Implementasi**:
   - Path: `<plan_dir>/<task_name>.md` (contoh: `plan/user-auth-jwt.md`).
   - Format: Markdown terstruktur dengan 4–5 section utama (Section 5 mengikuti `include_rollback`), checklist atomik, dan status `APPROVED`.
2. **Status Terminal**: `PLAN_APPROVED`
3. **Format Ringkasan Akhir (Maksimal 17 Baris)**:
   ```
   PLAN: <plan_dir>/<task_name>.md
   STATUS: PLAN_APPROVED
   LANGKAH: <n> langkah atomik, <n> berkas target
   LAYER: <daftar layer tersentuh>
   RISIKO: <migrasi skema | dependensi baru | perubahan kontrak publik | ->
   KUNCI: Plan-Hash <12 hex> — Approval "<kutipan jawaban user>"
   GATES: explore=<…> clarify=<…> — profil <profile_path>
   VERIFIKASI: <perintah baseline yang akan dijalankan execute>
   REVISI: <n> putaran sebelum disetujui
   HANDOFF: execute (plan_path=<plan_dir>/<task_name>.md)
   ```

## Failure path

1. **User Menolak Draf Rencana**: Jika user menolak rencana atau meminta perubahan besar pada arsitektur, jangan lanjutkan ke eksekusi; diskusikan alternatif pendekatan, perbarui dokumen draf rencana di `plan/<task-name>.md`, dan ajukan kembali untuk review hingga disetujui.
2. **Nama Task Duplikat / Berkas Plan Sudah Ada**: Jika file `plan/<task-name>.md` telah ada dan berstatus `APPROVED` dari pekerjaan sebelumnya, tawarkan opsi nama task baru (misal: `<task-name>-v2`) atau minta izin eksplisit untuk menimpa draf lama.
3. **Spesifikasi Masih Memiliki Celah / Ambiguitas**: Jika saat perumusan langkah ditemukan celah logika yang belum terjawab, tunda penyelesaian rencana dan tawarkan `quickdev:clarify` untuk detail yang hilang. Kembali ke `quickdev:clarify` maksimal satu kali per tugas; bila celah masih ada sesudahnya, `AskUserQuestion`: *Lanjut dengan asumsi tertulis di Section 1* · *Perkecil lingkup* · *Batal*.
4. **Izin Tulis Direktori Plan Gagal**: Jika pembuatan folder `plan/` atau penulisan berkas gagal karena kendala hak akses, laporkan path tujuan dan instruksikan penyesuaian izin filesystem.
5. **Explore/clarify tidak ada di percakapan**: tanyakan lewat `AskUserQuestion`: *Jalankan `quickdev:explore` dulu (disarankan)* · *Lanjut tanpa explore — saya sebutkan berkas targetnya* · *Batal*. Opsi kedua menulis `Gates: explore=DILEWATI clarify=DILEWATI` dan disebut di Fase 3.

## STYLE

- Gunakan kalimat imperatif aktif dan Observable Predicate pada seluruh alur perancangan dan checkpoint validasi.
- Tuliskan path berkas dan nama fungsi dalam format inline code backticks (contoh: `src/services/auth.service.ts`).
- Gunakan format tabel markdown untuk memetakan dampak modul dan daftar perubahan layer.
- Pertahankan istilah domain teknis (Implementation Plan, Atomic Steps, Layer Impact, Acceptance Criteria, Verification Baseline, Rollback Strategy) tanpa penerjemahan paksa.
- Pastikan kalimat mengalir natural dan padat informasi dengan rasio sinyal terhadap token yang tinggi.
