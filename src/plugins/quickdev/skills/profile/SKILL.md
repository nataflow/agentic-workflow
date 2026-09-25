---
name: profile
description: Alur ringan quickdev (repo-profile.md, plan/<task>.md, tanpa taskdir) — dipanggil eksplisit lewat /quickdev:profile ketika repo belum punya repo-profile.md atau profilnya perlu diperbarui — pemindaian stack, layer, dan baseline verifikasi. Bukan untuk .claude/profile/ milik backenddev/frontenddev.
disable-model-invocation: true
metadata:
  mode: standard
---

## THE IRON LAW

DILARANG MEMBUAT ASUMSI STACK ATAU PERINTAH BASELINE TANPA BUKTI KONFIGURASI NYATA DI FILESYSTEM. SETIAP PERINTAH VERIFIKASI (TYPECHECK, LINT, TEST) WAJIB DIUJI EKSEKUSI MINIMAL SATU KALI UNTUK MEMASTIKAN VALIDITAS RUNTIME, KECUALI `skip_baseline_exec` BERNILAI `true` DAN STATUSNYA DICATAT `SKIPPED`. BERKAS PROFIL YANG DIHASILKAN WAJIB MENGANDUNG SELURUH SECTION HEADER STANDAR DAN PANJANG KESELURUHAN DILARANG MELEBIHI 10.000 KARAKTER. DILARANG MELAKUKAN PERUBAHAN ATAU MEMBUAT BERKAS KODE SUMBER FITUR PADA SKILL INI.

## Precondition [REQUIRED]

1. Repositori target berada pada direktori kerja lokal yang dapat diakses dengan izin baca dan eksekusi perintah terminal.
2. File konfigurasi proyek (seperti `package.json`, `tsconfig.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, atau `pom.xml`) tersedia di root repositori atau di `workspace_dir`.
3. Package manager dan runtime terkait (seperti `node`, `pnpm`, `npm`, `yarn`, `python`, `go`) telah terpasang di environment kerja.
4. Berkas acuan template profil `references/backend-profile-template.md` dan `references/frontend-profile-template.md` tersedia di subdirektori references skill.

## Koeksistensi [REQUIRED]

- Skill ini bagian dari alur ringan `quickdev` (`repo-profile.md`, `plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backenddev:*` atau `frontenddev:*` sebagai pengganti: `backenddev:profile`/`frontenddev:profile` menulis `.claude/profile/<plugin>/`, bukan `repo-profile.md`, dan tidak memenuhi precondition skill ini.
- Bila konteks sesi memuat blok `<backenddev-tech-lead-gate>` atau `<frontenddev-lead-gate>`:
  - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`, `repo-profile.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
  - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backenddev:tech-lead | frontenddev:lead>` (taskdir + brief)". Jangan memilih sendiri.
- `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
- Penanda opt-out `.claude/workflow` (nama plugin yang boleh menggerbangi repo, dipisah spasi/baris): isi `quickdev` membuat hook SessionStart `backenddev`/`frontenddev` diam; isi `frontenddev quickdev` hanya menyalakan hook `frontenddev`.

## Parameter [REQUIRED]

- `type` — string — default `"auto"` — tipe repositori yang dipindai (`"backend"`, `"frontend"`, `"auto"`). Jika `"auto"`, skill menentukan tipe secara otomatis dari dependensi utama.
- `target_path` — string — default `"repo-profile.md"` — path file keluaran untuk profil repositori yang dihasilkan (contoh: `repo-profile.md` atau `.dev/profile.md`).
- `mode` — string — default `"GENERATE"` — mode operasi pemindaian (`"GENERATE"` untuk pembuatan profil baru dari nol, `"REFRESH"` untuk pembaruan profil yang telah ada).
- `skip_baseline_exec` — boolean — default `false` — bila `true`, melewati eksekusi perintah verifikasi runtime jika lingkungan berjalan pada restricted sandbox.
- `workspace_dir` — string — default `""` — workspace yang diprofilkan pada monorepo (contoh: `apps/api`); satu workspace per profil, dengan `target_path` berbeda per workspace yang diteruskan sebagai `profile_path` ke skill quickdev hilir (`quickdev:explore`, `quickdev:plan`, …).

## Workflow

### Fase 0 — Deteksi Mode & Pindai File Konfigurasi

1. Periksa keberadaan berkas profil pada path tujuan `target_path`:
   - Belum ada + `"GENERATE"`: lanjutkan pemindaian penuh dari awal (cold start).
   - Sudah ada + `"REFRESH"`: baca profil eksisting, pertahankan catatan kustom user, dan perbarui bagian yang mengalami drift.
   - Sudah ada + `"GENERATE"`: hentikan sebelum menimpa; tanyakan user apakah beralih ke `"REFRESH"` atau menimpa profil lama.
   - Belum ada + `"REFRESH"`: beralih ke `"GENERATE"` dan catat peralihan itu di ringkasan akhir.
2. Pindai root repositori untuk mendeteksi berkas manifes dan konfigurasi arsitektur:
   - Node/TypeScript ecosystem: `package.json`, `tsconfig.json`, `vite.config.ts`, `next.config.js`, `nest-cli.json`, `turbo.json`.
   - Python ecosystem: `pyproject.toml`, `requirements.txt`, `Pipfile`, `alembic.ini`, `setup.py`, `manage.py`.
   - Go ecosystem: `go.mod`, `go.sum`, `Makefile`.
   - Java/Kotlin ecosystem: `pom.xml`, `build.gradle`, `build.gradle.kts`.
   - Rust ecosystem: `Cargo.toml`, `Cargo.lock`.
3. Tentukan klasifikasi arsitektur repositori secara otomatis:
   - **Frontend Repository**: Ditandai oleh dependensi library UI dan rendering seperti `react`, `next`, `vue`, `nuxt`, `svelte`, `@angular/core`, `vite`, `tailwindcss`, `shadcn`.
   - **Backend Repository**: Ditandai oleh dependensi server dan framework REST/gRPC seperti `@nestjs/core`, `express`, `fastify`, `fastapi`, `django`, `flask`, `gin-gonic/gin`, `spring-boot`, `fiber`.
   - **Fullstack / Monorepo Workspace**: Ditandai oleh struktur direktori gabungan seperti `apps/web`, `apps/api`, `packages/ui`, atau workspace manifest (`pnpm-workspace.yaml`, `lerna.json`, `turborepo`). Profil dibuat per workspace: bila `workspace_dir` kosong, tanyakan workspace target ke user lewat `AskUserQuestion`, klasifikasikan workspace itu sebagai backend atau frontend, lalu jadikan direktorinya root pemindaian Fase 1–2.
4. Jika parameter `type` disetel eksplisit ke `"backend"` atau `"frontend"`, utamakan template pilihan user tersebut di atas deteksi otomatis.

### Fase 1 — Analisis Dependensi & Pemetaan Layer Arsitektur

1. Bedah struktur folder di dalam `src/` atau root direktori untuk memetakan pembagian layer tanggung jawab kode:
   - Untuk **Backend**:
     - Petakan controller / routing layer (contoh: `src/controllers/`, `src/routes/`, `app/api/`, `cmd/server/handlers/`).
     - Petakan service / domain usecase layer (contoh: `src/services/`, `src/usecases/`, `app/domain/`, `internal/service/`).
     - Petakan repository / data access layer (contoh: `src/repositories/`, `src/models/`, `src/infrastructure/`, `internal/store/`).
     - Petakan DTO / entity / validation schema (contoh: `src/dtos/`, `src/schemas/`, `src/entities/`, `pkg/models/`).
     - Identifikasi engine database, query builder, dan ORM yang digunakan (misal: PostgreSQL + Prisma, MySQL + TypeORM, MongoDB + Mongoose, SQLite + Drizzle, PostgreSQL + SQLAlchemy).
     - Identifikasi mekanisme autentikasi dan middleware (misal: Passport JWT, Guard dekorator, interceptor logging).
   - Untuk **Frontend**:
     - Petakan page / view routing layer (contoh: `src/pages/`, `src/app/`, `src/views/`, `src/routes/`).
     - Petakan component hierarchy (contoh: `src/components/ui/` primitives, `src/components/common/`, `src/features/*/components/` domain widgets).
     - Petakan view-model / custom hooks (contoh: `src/hooks/`, `src/features/*/hooks/`).
     - Petakan API service client (contoh: `src/services/`, `src/api/`, `src/lib/api-client.ts`, `src/utils/axios.ts`).
     - Identifikasi library state management (contoh: Zustand, Redux Toolkit, TanStack React Query, Jotai, Pinia).
     - Identifikasi paradigma styling dan design tokens (contoh: Tailwind CSS, CSS Modules, Styled Components, shadcn/ui).
2. Catat seluruh alias path compiler (seperti `@/* -> src/*`, `@components/* -> src/components/*`) dari `tsconfig.json` atau `pyproject.toml`.

### Fase 2 — Eksekusi Baseline Verifikasi Nyata

1. Identifikasi perintah verifikasi standar dari deklarasi scripts atau config runner:
   - Perintah Typecheck: `pnpm typecheck`, `npm run typecheck`, `npx tsc --noEmit`, `mypy .`, atau `go vet ./...`.
   - Perintah Linter: `pnpm lint`, `npm run lint`, `eslint .`, `ruff check .`, atau `golangci-lint run`.
   - Perintah Unit & Integration Test: `pnpm test`, `npm test`, `vitest run`, `jest`, `pytest`, atau `go test ./...`.
   - Perintah Build / Bundle Check: `pnpm build`, `npm run build`, `vite build`, atau `go build ./...`.
2. Jalankan setiap perintah verifikasi tersebut minimal 1 kali secara nyata via terminal runner (kecuali `skip_baseline_exec: true`):
   - Catat status eksekusi (`PASSED` atau `FAILED`; `SKIPPED` bila `skip_baseline_exec: true`) beserta durasi waktu running.
   - Tangkap baseline issues eksisting: jika terdapat error atau peringatan bawaan (misal: 2 lint warnings atau 1 skipped test), dokumentasikan secara transparan pada profil agar tidak menjadi false positive saat regresi di gate implementasi.
3. Dilarang mencatat perintah verifikasi rekaan yang tidak dapat dieksekusi di runtime aktual repositori.

### Fase 3 — Penyusunan Dokumen Profil Repositori

1. Muat template acuan yang sesuai dari subdirektori references:
   - Gunakan struktur backend jika klasifikasi adalah backend (`references/backend-profile-template.md`).
   - Gunakan struktur frontend jika klasifikasi adalah frontend (`references/frontend-profile-template.md`).
2. Isi setiap section header dengan data konkret hasil pemindaian dan eksekusi Fase 0–2:
   - Wajib menyertakan keenam section header template terpilih dengan teks heading persis.
   - Cantumkan fakta nyata, path relatif konkret, nama library spesifik, dan perintah baseline terverifikasi.
   - Cantumkan aturan arsitektur khusus yang ditemukan di repo (misal: larangan direct database access dari controller).
3. Ukur total karakter profil repositori yang dihasilkan:
   - Pastikan berkas di `target_path` berada di bawah 10.000 karakter (hasil `wc -m < <target_path>` kurang dari 10000).
   - Jika draf melebihi 10.000 karakter, lakukan peringkasan pada bagian daftar file panjang dengan menggunakan representasi path pola glob (contoh: gunakan `src/features/*` daripada mendaftarkan puluhan file satu per satu).
4. Tulis hasil profil ke `target_path` (default: `repo-profile.md`).

### Fase 4 — Validasi Integritas & Transisi Handoff

1. Lakukan audit verifikasi berkas keluaran pada `target_path`:
   - Pastikan berkas berhasil dibuat di filesystem, tidak kosong, dan berformat markdown valid.
   - Pastikan seluruh 6 section header hadir dan perintah baseline terbukti valid.
   - Pastikan ukuran berkas memenuhi batas kuota (< 10.000 karakter).
2. Set status terminal `PROFILED` dan laporkan ringkasan metadata profil ke user.
3. Bila konteks sesi memuat blok `<backenddev-tech-lead-gate>` atau `<frontenddev-lead-gate>` (atau `python3 <plugin>/hooks/detect.py --explain` menunjukkan hook engineer aktif), tawarkan penulisan penanda opt-out `.claude/workflow` berisi `quickdev` (ditambah nama plugin engineer yang tetap boleh menggerbangi repo, bila ada) agar hook engineer diam di repo ini. Tulis berkas itu hanya dengan persetujuan user.
4. Tawarkan `quickdev:explore`; tunggu user.

## Guardrails

- MUST NOT mengasumsikan framework, arsitektur, atau perintah test tanpa bukti file konfigurasi nyata di repositori.
- MUST NOT mengabaikan eksekusi baseline verifikasi saat membuat atau memperbarui profil (kecuali eksplisit di-skip).
- MUST NOT membiarkan ukuran berkas profil melebihi 10.000 karakter (`wc -m`).
- MUST NOT menghapus atau mengubah section header wajib yang telah distandardisasi dalam template acuan.
- MUST NOT melakukan modifikasi atau penambahan pada kode sumber fungsional repositori dalam skill ini.
- MUST NOT menulis profil ke path sembarangan di luar parameter `target_path` yang telah disepakati.

## Output [REQUIRED]

Skill ini menghasilkan berkas profil repositori terstruktur dan laporan terminal terdefinisi:

1. **Berkas Keluaran**:
   - Path: `<target_path>` (default: `repo-profile.md`).
   - Format: Markdown terstruktur dengan 6 section header lengkap, ukuran < 10.000 karakter.
2. **Status Terminal**: `PROFILED`
3. **Format Ringkasan Akhir (Maksimal 17 Baris)**:
   ```
   PROFILE: <target_path> — mode <GENERATE | REFRESH> — workspace <workspace_dir | root>
   STATUS: PROFILED
   TIPE: <backend | frontend> — sumber <parameter type | deteksi manifes>
   STACK: <runtime> / <framework> / <package manager>
   LAYER: <n> layer terpetakan — <daftar path layer ringkas>
   BASELINE: typecheck=<status> lint=<status> test=<status> build=<status>
   ISSUE BAWAAN: <ringkasan error/warning baseline eksisting | ->
   UKURAN: <n> karakter (batas 10.000)
   HANDOFF: explore
   ```
   Nilai `<status>`: `PASSED`, `FAILED`, `SKIPPED` (via `skip_baseline_exec`), atau `UNVERIFIED_ENV_NOT_READY`.

## Failure path

1. **File Konfigurasi Proyek Tidak Ditemukan**: Jika root repositori tidak memuat file konfigurasi yang dikenali, laporkan kegagalan deteksi stack, tawarkan opsi penentuan manual via parameter `type`, dan hentikan eksekusi sebelum menulis profil kosong.
2. **Eksekusi Perintah Baseline Mengalami Error Fatal**: Jika perintah typecheck/lint/test menghasilkan error runtime karena dependensi belum terpasang (misal: modul node_modules tidak ditemukan), instruksikan user untuk menjalankan instalasi package manager terlebih dahulu, atau catat status `UNVERIFIED_ENV_NOT_READY` pada seksi baseline profil.
3. **Ukuran Profil Melebihi Kuota Plafon 10.000 Karakter**: Jika draf profil melebihi kuota 10.000 karakter, pangkas deskripsi narasi panjang menjadi ringkasan bullet-points padat dan gunakan format tabel ringkas untuk pemetaan layer.
4. **Izin Tulis Filesystem Gagal**: Jika penulisan ke `target_path` gagal karena restriksi akses atau direktori induk belum dibuat, buat direktori induk secara otomatis atau laporkan error permission ke user.

## STYLE

- Gunakan kalimat imperatif aktif dan Observable Predicate pada setiap langkah instruksi workflow.
- Tuliskan nama package, path file, dan perintah terminal dalam format inline code backticks.
- Pertahankan teks section header berbahasa Inggris persis seperti template terpilih; header backend dan frontend berbeda, jangan dicampur.
- Tingkatkan rasio sinyal terhadap token dengan menyajikan langkah kerja teknis yang presisi tanpa basa-basi naratif.
