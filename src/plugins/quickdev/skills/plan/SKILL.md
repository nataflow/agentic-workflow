---
name: plan
description: Alur ringan quickdev (plan/<task>.md, tanpa taskdir dan tanpa profil repo) — menelusuri kode terkait, mengklarifikasi celah spesifikasi, lalu menyusun satu berkas rencana plan/<task>.md beserta perintah verifikasinya dan meminta approval user. Bukan brief taskdir backend/frontend; dipanggil eksplisit lewat /quickdev:plan.
disable-model-invocation: true
---

## THE IRON LAW

DILARANG MENULIS KODE SUMBER SEBELUM RENCANA DISETUJUI USER SECARA EKSPLISIT DAN DIKUNCI `plan_lock.py lock`. DILARANG MENCANTUMKAN PATH, SIMBOL, ATAU PERINTAH VERIFIKASI YANG TIDAK TERBUKTI ADA DI REPO. DILARANG MENGISI CELAH SPESIFIKASI DENGAN ASUMSI DIAM-DIAM: CELAH DITANYAKAN, ATAU DITULIS SEBAGAI ASUMSI DI SECTION 1 ATAS PILIHAN USER. SETIAP LANGKAH RENCANA WAJIB ATOMIK, MENYEBUT PATH BERKAS TARGET, DAN BERURUTAN DEPENDENSI. RENCANA DISIMPAN DI `<plan_dir>/<task_name>.md` SEBAGAI SINGLE SOURCE OF TRUTH.

## Precondition [REQUIRED]

1. Permintaan user menyebut fitur, bug, atau area kode yang dapat ditelusuri; bila tidak, tanyakan dulu sebelum Fase 0.
2. Repo dapat dibaca. Pencarian berkas/teks memakai tool `Glob`/`Grep` bila tersedia; bila tidak, Bash baca-saja: `git ls-files | grep -i '<pola>'` (nama berkas), `grep -rn --include='*.<ext>' '<pola>' <dir>` atau `rg -n '<pola>'` bila terpasang (isi). `Read` wajib.
3. Direktori kerja memiliki izin tulis untuk membuat `plan_dir` dan berkas rencana.
4. `python3` (3.12+) tersedia untuk `plan_lock.py`, yang mengunci rencana saat approval dan menjalankan sinkron nataflow.

## Koeksistensi [REQUIRED]

- Skill ini bagian dari alur ringan `quickdev` (`plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backend:*` atau `frontend:*` sebagai pengganti langkahnya.
- Bila konteks sesi memuat blok `<backend-tech-lead-gate>` atau `<frontend-lead-gate>`:
  - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
  - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backend:tech-lead | frontend:lead>` (taskdir + brief)". Jangan memilih sendiri.
- `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
- Penanda opt-out `.claude/workflow` (nama plugin yang boleh menggerbangi repo, dipisah spasi, koma, atau baris): isi `quickdev` membuat hook SessionStart `backend`/`frontend` diam; isi `frontend quickdev` hanya menyalakan hook `frontend`. Penawarannya ada di Fase 0 butir 6.

## Parameter [REQUIRED]

- `task_name` — string — `[REQUIRED]` — nama unik tugas dalam kebab-case (contoh: `user-auth-jwt`, `order-status-filter`). Bila tidak diberikan, turunkan dari permintaan user dan konfirmasikan bersama draf di Fase 4.
- `task_spec` — string — default: permintaan user di percakapan — kebutuhan yang akan direncanakan. Section 1 rencana menjadi satu-satunya sumber spesifikasi bagi `quickdev:execute` dan `quickdev:review`.
- `plan_dir` — string — default `"plan"` — direktori penyimpanan rencana di repo.
- `target_dir` — string — default `""` — workspace monorepo yang dikerjakan (contoh: `apps/api`); menjadi root deteksi manifest dan kolom `Cwd` Section 4. Kosong di repo bertanda monorepo (`pnpm-workspace.yaml`, `turbo.json`, `lerna.json`, `go.work`, workspaces di `package.json`) → tanyakan workspace target lewat `AskUserQuestion`.
- `trace_depth` — integer — default mengikuti skala Fase 1 (`kecil` = 1, `standar` = 2), maksimal 4 — kedalaman penelusuran pemanggil dan dependensi simbol.
- `batch_limit` — integer — default `3` — batas pertanyaan klarifikasi per batch (maksimal 4, batas satu panggilan `AskUserQuestion`).
- `require_test_plan` — boolean — default `true`, **kecuali** baris Test Section 4 bernilai `TIDAK_ADA` → default `false` — bila `true`, Section 4 wajib memuat skenario test unit/integration beserta langkah test di Section 3; bila `false`, Section 4 cukup memuat tabel perintah verifikasi.
- `include_rollback` — boolean — default `true` — bila `false`, Section 5 (rollback) tidak ditulis.

## Workflow

### Rute sinkron ulang

User meminta sinkron ulang rencana yang sudah ada ("sinkron ulang `<plan_path>`"), biasanya sesudah segmen `NATAFLOW: GAGAL`: lewati Precondition 1–3 dan Fase 0–5, jalankan prosedur `references/nataflow-sync.md` atas `<plan_path>` apa adanya, lalu tutup dengan satu baris `SINKRON — <plan_path> · nataflow <segmen>`. Rencana tidak disentuh dan status terminal tidak berubah.

### Fase 0 — Konteks Repo & Perintah Verifikasi

1. Validasi `task_name` (kebab-case bersih) dan tetapkan path `<plan_dir>/<task_name>.md`. Berkas sudah ada → `APPROVED` ke Failure path 2; `DRAFT` dilanjutkan sebagai revisi.
2. Pindai manifest di root (atau `target_dir`): Node/TypeScript (`package.json` beserta `scripts`, `tsconfig.json`), Python (`pyproject.toml`, `requirements.txt`, `manage.py`), Go (`go.mod`, `Makefile`), JVM (`pom.xml`, `build.gradle*`), Rust (`Cargo.toml`). Tanda monorepo tanpa `target_dir` → tanyakan workspace (Parameter).
3. Tentukan tipe repo: `frontend` (dependensi UI/rendering), `backend` (framework server REST/gRPC), atau `fullstack` (dependensi frontend **dan** minimal satu berkas route server nyata di paket yang sama, mis. route handler Next, `+server.ts` SvelteKit, `server/api` Nuxt). Framework UI tanpa route server tetap `frontend`.
4. Tentukan perintah verifikasi dari `scripts` atau konfigurasi runner yang benar-benar ada: typecheck, lint, test, build. Jenis tanpa runner dicatat `TIDAK_ADA`, bukan dikarang. Tandai kolom Risiko: `menyentuh DB/jaringan` (test integrasi yang membaca `.env`, docker-compose, Testcontainers, atau `DATABASE_URL`), `menulis artefak` (build), selain itu `-`. Migrasi dan perintah pengubah skema/data tidak pernah dicantumkan sebagai perintah verifikasi.
5. Skill ini tidak menjalankan perintah verifikasi apa pun; baseline diukur `quickdev:execute` sebelum mutasi pertama.
6. Konteks sesi memuat blok `<backend-tech-lead-gate>` atau `<frontend-lead-gate>` dan `.claude/workflow` belum ada → tawarkan sekali penulisan `.claude/workflow` berisi `quickdev` (ditambah nama plugin engineer yang tetap boleh menggerbangi repo, bila ada). Tulis hanya dengan persetujuan user; jangan mencari skrip deteksi plugin lain.

### Fase 1 — Telusur Kode

1. Tetapkan skala dari permintaan dan temuan pertama:
   - **kecil**: ≤2 berkas, tanpa perubahan kontrak publik, skema, atau env → `trace_depth=1`: definisi simbol target, pemanggil langsung, dan test berkas target.
   - **standar**: selain itu → `trace_depth` (default 2): rantai pemanggil per layer (backend: route → middleware → service → data access/ORM → skema; frontend: page/route → komponen → hook/state → API client → DTO/type), konsumen setiap simbol yang signature atau kontraknya berubah (reverse search lintas repo), skema dan relasi DB, env yang dibutuhkan, dan test terkait.
2. Cari nama berkas dengan pola entitas domain + peran layer (contoh: `*order*service*`, `use*Order*`); pola peran tanpa entitas hanya dipakai di direktori yang sudah sempit. Cari teks deklarasi simbol, definisi route, dan query ORM yang relevan, lalu `Read` baris pentingnya.
3. Setiap path dan simbol yang akan masuk rencana wajib terbukti dari pencarian atau `Read` (`path:baris`). Topik tidak ditemukan → perluas direktori dan coba sinonim sekali; tetap nol → Failure path 3. Simbol muncul di lebih dari 10 modul → tanyakan modul target sebelum lanjut.
4. Hasil telusur tidak dilaporkan tersendiri: ia menjadi bahan Fase 2, Section 2, dan Section 3. Catat celah spesifikasi yang ditemukan.

### Fase 2 — Klarifikasi

1. **Fast-path**: input, perilaku, validasi, output, dan trade-off desain sudah pasti dari kode dan permintaan → lanjut ke Fase 3 tanpa pertanyaan basa-basi; catat `KLARIFIKASI: fast-path` di ringkasan.
2. Celah ada → ajukan lewat `AskUserQuestion`, maksimal `batch_limit` pertanyaan per batch dan **2 batch**; dahulukan celah yang memblokir rencana. Setiap pertanyaan menyebut konteks temuan (berkas, endpoint, atau fungsi) dan opsi konkret dengan satu opsi `(Recommended)` yang selaras pola repo yang terbukti. Dilarang bertanya terbuka tanpa opsi, atau mencicil satu per satu.
3. Fokus pertanyaan mengikuti tipe repo:
   - **backend**: path endpoint dan HTTP verb, skema payload dan validasi wajib/opsional, status code tiap kegagalan, dampak tabel/kolom/relasi, scope auth dan permission.
   - **frontend**: alur navigasi dan aksi sesudah submit, tata letak (modal, drawer, inline), cabang state (loading, empty, error), sinkron state URL, perilaku validasi form.
   - **fullstack**: gabungan keduanya dengan prioritas boundary — bentuk payload UI ke route server, error yang ditampilkan UI, dan tempat validasi (klien, server, atau keduanya).
4. Jawaban delegasi ("bebas", "ikuti standar repo") → pilih pola yang terbukti di kode dan tampilkan sebagai satu konfirmasi ringkas sebelum dikunci.
5. Jawaban bertentangan dengan pola repo yang terbukti → jelaskan risikonya dengan bukti `path:baris`, tawarkan alternatif yang selaras, lalu minta konfirmasi final.
6. Celah masih tersisa sesudah batch ke-2 → `AskUserQuestion`: *Lanjut dengan asumsi tertulis di Section 1* · *Perkecil lingkup* · *Batal*.

### Fase 3 — Dekomposisi & Penyusunan Rencana

1. Pecah tugas menjadi langkah atomik hanya untuk layer yang tersentuh; layer yang tidak berubah dilewati. Urutan acuan — backend: skema/migrasi → DTO/validasi → data access → service → controller/route → test; frontend: types/kontrak → API client/hook → state → komponen → page/route → test. Bugfix satu berkas cukup satu langkah perubahan plus langkah test.
2. Setiap langkah mencantumkan berkas target (path relatif presisi), simbol yang ditambah atau diubah, dan kriteria selesai.
3. Konsumen terdampak dari Fase 1 → tambahkan langkah "sesuaikan konsumen" beserta berkasnya. `quickdev:execute` hanya boleh memperbaiki galat verifikasi di berkas Section 3, jadi konsumen yang tidak direncanakan membuat eksekusi `BLOCKED`.
4. Tulis `<plan_dir>/<task_name>.md` (buat `plan_dir` bila belum ada):
   - Header `# Implementation Plan — <task_name>`, lalu metadata baris polos `Kunci: nilai` tepat di bawah H1 (tanpa butir/tebal): `Status: DRAFT`, `Author: quickdev:plan`, `Date: <ISO>`. Baris `Approved-At`, `Approval`, `Hash-Scope`, dan `Plan-Hash` hanya ditulis `plan_lock.py lock`. Sidik mencakup Section 1–5.
   - `## 1. Overview & Objectives` — tujuan, masalah, keputusan Fase 2, asumsi yang dipilih user, dan out of scope, supaya spesifikasi tidak bergantung pada riwayat percakapan.
   - `## 2. Architecture & Layer Impact` — tipe repo, tabel modul yang disentuh dengan bukti `path:baris` dan dampaknya, konsumen terdampak, dan berkas acuan konvensi yang diikuti (berkas sejenis yang sudah ada).
   - `## 3. Atomic Implementation Steps` — langkah bernomor dengan checkbox `- [ ]`.
   - `## 4. Verification & Testing Strategy` — tabel `| Jenis | Perintah | Cwd | Risiko |` dari Fase 0 (typecheck, lint, test, build; `TIDAK_ADA` bila tanpa runner), lalu skenario happy path dan edge case bila `require_test_plan: true`. Repo tanpa test runner: tulis `Tests: repo tanpa test runner — verifikasi: typecheck/lint/build + langkah QA manual`. Menambah framework test hanya sebagai langkah eksplisit Section 3 yang disetujui user.
   - `## 5. Rollback & Contingency Strategy` — langkah mitigasi dan pemulihan; hanya bila `include_rollback: true`.

### Fase 4 — Presentasi Draf & Approval Gate

1. Sajikan **ringkasan gerbang**, bukan isi rencana: baris `PLAN — DRAFT · <plan_dir>/<task_name>.md · <n> langkah · <n> berkas`, lalu 3–4 kalimat — pendekatan, keputusan desain kunci, perubahan skema atau dependensi baru bila ada, dan risiko terbesarnya. Sebut dalam satu frasa: `task_name` hasil turunan, asumsi yang dipilih user, dan perintah verifikasi bertanda `menyentuh DB/jaringan`. Daftar langkah dan path berkas tetap di rencana; dilarang menyalinnya ke chat. User meminta rincian → sajikan section yang diminta saja, lalu ajukan ulang butir 2.
2. Minta persetujuan eksplisit lewat `AskUserQuestion`: *Setujui rencana* · *Revisi (sebut poinnya)*. Persetujuan mencakup izin menjalankan perintah Section 4; perintah bertanda `menyentuh DB/jaringan` tetap ditanyakan `quickdev:execute` sebelum dijalankan. Diam atau jawaban ambigu bukan persetujuan.
3. Tangani respons:
   - **Revisi**: perbarui rencana, pertahankan `Status: DRAFT`, ajukan ulang. Rencana yang sudah memuat `## Execution Status`: revisi hanya Section 1–5 lewat Edit terarah; blok itu dan checkbox langkah yang teksnya tidak berubah dipertahankan, sedangkan langkah yang teksnya berubah dikembalikan ke `- [ ]` supaya `quickdev:execute` mengerjakannya ulang.
   - **Persetujuan eksplisit**: jalankan perintah di bawah dengan jawaban user apa adanya lewat stdin. Heredoc berkutip mencegah shell mengekspansi `` ` `` dan `$`; dilarang memakai kutip ganda. `LOCK FAIL` → perbaiki sebabnya; dilarang menulis `Status: APPROVED` dengan tangan.

     ```
     python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py lock --plan <plan_dir>/<task_name>.md --answer - <<'QD_EOF'
     <jawaban user apa adanya>
     QD_EOF
     ```

### Fase 5 — Penguncian & Handoff

1. Pastikan keluaran `LOCK PASS` memuat sidik; `Approved-At`, `Approval`, `Hash-Scope`, dan `Plan-Hash` sudah ditulis skrip.
2. **Sinkron nataflow**: jalankan prosedur `references/nataflow-sync.md` atas `<plan_dir>/<task_name>.md` apa adanya; hasilnya baris `NATAFLOW:` ringkasan. `GAGAL` tidak membatalkan `PLAN_APPROVED`.
3. Set status terminal `PLAN_APPROVED`.
4. Tawarkan `quickdev:execute` (`/quickdev:execute <plan_dir>/<task_name>.md`, sesudah user meng-commit rencana `APPROVED` bila ingin riwayatnya terlihat); tunggu user.

## Guardrails

- MUST NOT menulis, mengubah, atau membuat kode sumber fungsional selama skill ini berjalan.
- MUST NOT menjalankan perintah verifikasi, build, test, atau migrasi di skill ini; baseline milik `quickdev:execute`.
- MUST NOT mengizinkan transisi ke `PLAN_APPROVED` tanpa persetujuan eksplisit tertulis dari user.
- MUST NOT membuat langkah yang ambigu tanpa path berkas target yang pasti, atau mencantumkan path dan simbol yang tidak terbukti di repo.
- MUST NOT melompati Section 4 (tabel perintah verifikasi).
- MUST NOT mengubah Section 1–5 berkas `APPROVED`. Revisi atas permintaan user: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py unlock --plan <plan_path> --reason - <<'QD_EOF'` (alasan lewat stdin, ditutup `QD_EOF`) → prosedur `references/nataflow-sync.md` (cermin menjadi `DRAFT`) → revisi → approval ulang (`lock`). Blok `## Execution Status` dipertahankan apa adanya. Rencana `APPROVED` tanpa `Plan-Hash` (format lama) diperlakukan sama: `unlock`, lalu minta user menyetujui ulang.
- Keputusan ruang lingkup fitur dan persetujuan arsitektur rencana tetap milik mutlak user.

## Output [REQUIRED]

1. **Dokumen Rencana**: `<plan_dir>/<task_name>.md` (contoh: `plan/user-auth-jwt.md`) dengan 4–5 section (Section 5 mengikuti `include_rollback`), checklist atomik, tabel perintah verifikasi, dan status `APPROVED`.
2. **Status Terminal**: `PLAN_APPROVED`
3. **Format Ringkasan Akhir (Maksimal 17 Baris)**:
   ```
   PLAN: <plan_dir>/<task_name>.md
   STATUS: PLAN_APPROVED
   TIPE: <backend | frontend | fullstack> — skala <kecil | standar>
   LANGKAH: <n> langkah atomik, <n> berkas target
   LAYER: <daftar layer tersentuh>
   KLARIFIKASI: <n> pertanyaan dalam <n> batch | fast-path — asumsi: <n> | -
   RISIKO: <migrasi skema | dependensi baru | perubahan kontrak publik | ->
   KUNCI: Plan-Hash <12 hex> — Approval "<kutipan jawaban user>"
   VERIFIKASI: typecheck=<perintah|TIDAK_ADA> lint=<…> test=<…> build=<…> — DB/jaringan: <daftar | ->
   REVISI: <n> putaran sebelum disetujui
   NATAFLOW: workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama) | dilewati | GAGAL: <sebab>
   HANDOFF: execute (plan_path=<plan_dir>/<task_name>.md)
   ```

## Failure path

1. **User menolak draf**: jangan lanjut ke eksekusi; diskusikan alternatif pendekatan, perbarui draf, dan ajukan ulang hingga disetujui.
2. **Berkas rencana sudah `APPROVED`**: tawarkan nama task baru (`<task_name>-v2`) atau minta izin eksplisit untuk merevisinya lewat `unlock` (Guardrails).
3. **Topik tidak ditemukan di kode**: laporkan hasil nol secara transparan beserta kata kunci alternatif, lalu tanyakan: *Sebutkan berkas atau simbol targetnya* · *Ini fitur baru — rencanakan berkas baru (path ditetapkan bersama user)* · *Batal*. Dilarang mengarang path.
4. **Dialog klarifikasi dibatalkan atau tidak dijawab**: jangan menulis rencana. Sajikan blok `PLAN — TERTAHAN`: keputusan yang sudah terkunci, pertanyaan tersisa beserta opsinya. Pemanggilan `/quickdev:plan` berikutnya melanjutkan dari blok itu.
5. **Izin tulis direktori rencana gagal**: laporkan path tujuan dan minta penyesuaian izin filesystem.

## STYLE

- Gunakan kalimat imperatif aktif dan Observable Predicate pada seluruh alur perancangan dan checkpoint validasi.
- Tuliskan path berkas dan nama fungsi dalam inline code; rujukan bukti dalam format `path:baris` atau `path:baris-baris`.
- Gunakan tabel markdown untuk dampak modul dan perintah verifikasi.
- Pertahankan istilah domain teknis (Implementation Plan, Atomic Steps, Layer Impact, Acceptance Criteria, Fast-Path, Rollback Strategy) tanpa penerjemahan paksa.
- Kalimat padat informasi dengan rasio sinyal terhadap token yang tinggi.
