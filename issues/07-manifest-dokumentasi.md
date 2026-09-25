# Langkah 7 — Manifest & Dokumentasi (detail)

Versi rinci item L7.1–L7.5 dari `ISSUES.md`. Isi diverifikasi terhadap repo pada commit `34684ee` (2026-09-24). Kutipan dokumentasi Claude Code diambil lewat WebFetch pada tanggal yang sama dari `code.claude.com/docs/en/{plugin-marketplaces, plugins-reference, skills, sub-agents, discover-plugins}`. Kutipan itu melewati peringkas WebFetch, jadi cocokkan ulang dengan halaman aslinya sebelum disalin ke README.

## Tujuan

Manifest menjadi satu sumber kebenaran (versi, deskripsi, penulis) yang divonis lint, berkas mati dibuang, dan setiap plugin beserta marketplace-nya punya README yang menjelaskan kapan dipakai, apa yang ditulisnya ke repo pengguna, dan bagaimana plugin-plugin itu hidup berdampingan.

## Urutan pengerjaan

1. **L7.2** hapus `plugin.json` liar (5 menit, tanpa keputusan).
2. **L7.1** putuskan sumber versi dan email, terapkan diff (30 menit).
3. **L7.5** putuskan nasib `metadata`, bersihkan `__pycache__` lokal (15 menit).
4. **L7.4** putuskan `user-invocable: false`, terapkan ke 15 skill, uji manual (1 jam).
5. **L7.3** README terakhir, karena isinya bergantung pada keputusan L1.1 (lokasi profil), L1.3 (koeksistensi), dan L7.1 (kebijakan versi). Bila ingin lebih cepat, tulis sekarang berdasarkan perilaku saat ini dan tandai seksi yang berubah sesudah L1.1/L1.3 (1–1,5 hari).

## Dependensi dengan langkah lain

| Arah | Item | Keterangan |
|---|---|---|
| L7.1 → | L6.3 check M3/M4 | keputusan sumber versi menentukan aturan lint |
| L7.2 → | L6.3 check M5 | |
| L7.4 → | L6.3 check F3 (baru) | hanya bila disetujui |
| L7.5 → | L6.3 check G1 | |
| L7.3 ← | L1.1, L1.3, D1, D2, D7 | README menjelaskan lokasi profil, koeksistensi hook, dan semantik rencana quickdev |
| L7.3 ← | L6.2 | README root memuat cara menjalankan test dan lint |

## Estimasi usaha

±1,5–2 hari total; hampir semuanya untuk L7.3.

## Definisi selesai langkah ini

- `python3 scripts/lint_plugins.py` tanpa temuan M3, M4, M5, G1 (dan F3 bila L7.4 disetujui).
- `claude plugin validate .` lolos di root repo.
- Ada `README.md` di root repo, `src/plugins/backenddev/`, dan `src/plugins/quickdev/` dengan seluruh seksi di L7.3; klaim yang salah di README frontenddev dan analyst sudah diperbaiki.
- Empat baris "Log Keputusan" untuk Langkah 7 terisi (L7.1, L7.3, L7.4, L7.5).

## Keputusan yang dibutuhkan user

1. **L7.1 sumber versi:** `plugin.json` saja (disarankan) atau entri marketplace saja.
2. **L7.1 email kanonik:** `fakhrulnugroho15@gmail.com` (dipakai owner marketplace dan 3 plugin) atau `groupzcode@gmail.com` (dipakai frontenddev).
3. **L7.3 lokasi publikasi repo** (untuk perintah instalasi) dan **kebijakan git artefak quickdev** (`repo-profile.md`, `plan/`: di-commit atau di-gitignore). Tambahan: `plugin.json` menulis `"license": "MIT"` tetapi repo tidak punya berkas `LICENSE`.
4. **L7.4:** sembunyikan 15 skill internal dari menu `/` atau tidak.
5. **L7.5:** pertahankan `metadata.mode` (dengan dokumentasi) atau hapus.

## Catatan implementasi (2026-09-25)

Keputusan: versi hanya di `plugin.json`; email `fakhrulnugroho15@gmail.com`; perintah instalasi dengan placeholder `<owner>/<repo>`; artefak quickdev di-commit; `LICENSE` MIT ditambahkan; ke-15 skill disembunyikan; `metadata` dihapus.

- **L7.1**: `version` dibuang dari keempat entri marketplace dan deskripsi frontenddev disamakan (diff Opsi A). Email frontenddev diganti. Versi keempat plugin belum pernah naik sejak `init`, jadi semuanya dinaikkan satu minor: analyst 0.3.0, backenddev 0.6.0, frontenddev 0.5.0, quickdev 0.2.0.
- **L7.2**: `src/plugins/frontenddev/plugin.json` dihapus.
- **L7.4**: check F3 sudah ada di lint sebagai WARN; kini dinaikkan menjadi FAIL.
- **L7.5**: `__pycache__` di `src/` dibersihkan. Poin 3 rencana keliru menganggap `conftest.py` sudah memasang `PYTHONDONTWRITEBYTECODE`: sesudah suite dijalankan, 17 `.pyc` muncul lagi. Sekarang `conftest.py` memasang `sys.dont_write_bytecode` dan `PYTHONDONTWRITEBYTECODE=1`, dan `find src -name '*.pyc'` kosong sesudah `pytest`.
- **L7.3**: isi README mengikuti kode sesudah L1.1–L1.4, bukan kerangka di atas yang ditulis sebelumnya. Artinya profil per plugin, penanda `.claude/workflow`, `detect.py` Python, hook PreToolUse `guard_bash.py`, baseline quickdev yang meminta izin, dan skill quickdev yang ber-`disable-model-invocation`. Seksi "Keterbatasan" backenddev dan quickdev memuat item 08b/08d yang masih terbuka (D1, D2, D7, B4–B6, B13).
- CI dan `tests/test_lint_plugins.py`: `LINT_IGNORE`/`deferred` tinggal `R2` (X1).
- Verifikasi: `pytest` 862 passed + 2 xfail; `lint_plugins.py --base HEAD` 0 FAIL selain R2; `claude plugin validate .` lolos.
- **Belum diverifikasi manual**: tampilan `/plugin` Installed/Discover (frontenddev 0.5.0 + deskripsi baru), menu `/` tanpa ke-15 skill internal, dan satu alur fixture per plugin yang memanggil skill tersembunyi lewat tool Skill. Ketiganya butuh sesi Claude Code interaktif. Perintah instalasi juga belum diuji pada marketplace hasil publikasi.

---

## L7.1 [Rendah] Versi, deskripsi, dan email frontenddev tidak sinkron

- [x] Selesai

**Plugin:** keempat plugin (frontenddev paling parah) · **Estimasi:** 30 menit · **Bergantung pada:** keputusan user (sumber versi, email) · **Memblokir:** L6.3 check M3/M4

### Konteks

Dokumentasi Claude Code (plugin-marketplaces, "Version resolution and release channels"):

> "Avoid setting `version` in both `plugin.json` and the marketplace entry. Claude Code always uses the `plugin.json` value without warning, so a stale manifest version can mask a version you set in `marketplace.json`."

> "If you declare `"version": "1.0.0"` in `plugin.json` and push new commits without changing that string, existing users of those sources keep the cached copy, because Claude Code sees the same version. Bump the field on every release, or omit it to fall back to the resolved version."

plugins-reference, baris field `version`: *"If also set in the marketplace entry, `plugin.json` wins."*

Untuk field tampilan berlaku aturan kebalikannya (plugin-marketplaces, "Optional plugin fields"):

> "Both the entry and the plugin's own `plugin.json` can set the display fields `displayName`, `description`, `author`, `homepage`, `repository`, `license`, and `keywords`. In plugin listings and details, before and after install:
> - For a field you set on the entry, users see the entry's value, even when `plugin.json` sets a different one.
> - For a field the entry leaves unset, users see the `plugin.json` value."

Pengecualian yang relevan untuk pengembangan lokal: versi tidak mengunci plugin yang *"loaded in place from a marketplace added as a local directory."*

### Lokasi & kondisi saat ini

| Plugin | `version` plugin.json | `version` marketplace | `description` sama? | `author.email` plugin.json |
|---|---|---|---|---|
| analyst | 0.2.0 | 0.2.0 | ya | fakhrulnugroho15@gmail.com |
| backenddev | 0.5.0 | 0.5.0 | ya | fakhrulnugroho15@gmail.com |
| frontenddev | **0.4.0** | **0.3.0** (`marketplace.json:33`) | **tidak** (`:32`) | **groupzcode@gmail.com** |
| quickdev | 0.1.0 | 0.1.0 | ya | fakhrulnugroho15@gmail.com |

`owner.email` marketplace dan `author.email` keempat entri marketplace = `fakhrulnugroho15@gmail.com`. Deskripsi frontenddev di entri marketplace masih versi lama ("…kontrak arsitektur, review kesesuaian, dan eksekusi lewat brief"), sedangkan `plugin.json` menulis versi baru ("…perencanaan brief, eksekusi sekuensial, review independen, dan laporan — dengan ledger approval dan validator mekanis di tiap gate").

**Koreksi terhadap ISSUES.md:**
- `version` ganda ada di **keempat** plugin, bukan hanya frontenddev; dokumentasi menyarankan menghindari duplikasi itu sama sekali.
- "Claude Code memakai `plugin.json` tanpa peringatan" hanya berlaku untuk `version`. Untuk `description` dan `author`, **nilai entri marketplace yang ditampilkan**, jadi pengguna melihat deskripsi lama frontenddev.
- Versi efektif frontenddev hari ini 0.4.0 (dari `plugin.json`), bukan 0.3.0.

### Rencana perbaikan

1. **Opsi A — versi hanya di `plugin.json` (disarankan).** Versi naik di commit yang sama dengan perubahan kodenya, dan lint M7 bisa menagih bump per plugin. Diff persis (sudah diuji di salinan scratchpad; semua berkas tetap JSON valid):

   ```diff
   --- a/.claude-plugin/marketplace.json
   +++ b/.claude-plugin/marketplace.json
   @@ -10,7 +10,6 @@
        {
          "name": "analyst",
          "description": "Skill dan subagent jembatan antara pengguna/stakeholder dan engineer: klasifikasi permintaan, elisitasi terarah dengan peminta non-engineer, dan penulisan TICKET.md non-teknis (user story, acceptance criteria, aturan bisnis) setara kartu Jira/Trello — dengan review independen dan persetujuan user sebelum diserahkan ke backenddev/frontenddev",
   -      "version": "0.2.0",
          "source": "./src/plugins/analyst",
          "author": {
            "name": "Fakhrul Nugroho",
   @@ -20,7 +19,6 @@
        {
          "name": "backenddev",
          "description": "Agent dan skill untuk kerja backend lintas-stack (Java Spring, Go, Node, Bun, Rust, PHP, CodeIgniter 4): profiling repo, eksplorasi, audit konvensi, review terhadap kontrak, perencanaan, orkestrasi eksekusi, implementasi, dan analisis kebutuhan",
   -      "version": "0.5.0",
          "source": "./src/plugins/backenddev",
          "author": {
            "name": "Fakhrul Nugroho",
   @@ -29,8 +27,7 @@
        },
        {
          "name": "frontenddev",
   -      "description": "Skill dan subagent untuk kerja frontend lintas-stack (React Vite SPA, React Native/Expo, SvelteKit, Svelte + Vite): profil repo, penelusuran kode, perjalanan antar-layar, bentuk layar, kontrak arsitektur, review kesesuaian, dan eksekusi lewat brief",
   -      "version": "0.3.0",
   +      "description": "Skill dan subagent untuk kerja frontend lintas-stack (React Vite SPA, React Native/Expo, SvelteKit, Svelte + Vite): profil repo, penelusuran kode, perjalanan antar-layar, bentuk layar, kontrak arsitektur, perencanaan brief, eksekusi sekuensial, review independen, dan laporan — dengan ledger approval dan validator mekanis di tiap gate",
          "source": "./src/plugins/frontenddev",
          "author": {
            "name": "Fakhrul Nugroho",
   @@ -40,7 +37,6 @@
        {
          "name": "quickdev",
          "description": "Skill alur kerja ringan untuk repo backend dan frontend: profil repo, penelusuran kode, klarifikasi spesifikasi, rencana satu berkas, eksekusi terverifikasi, dan review diff terhadap rencana — tanpa taskdir maupun subagent",
   -      "version": "0.1.0",
          "source": "./src/plugins/quickdev",
          "author": {
            "name": "Fakhrul Nugroho",
   ```

   Email (bila keputusan = `fakhrulnugroho15@gmail.com`):

   ```diff
   --- a/src/plugins/frontenddev/.claude-plugin/plugin.json
   +++ b/src/plugins/frontenddev/.claude-plugin/plugin.json
   @@ -4,7 +4,7 @@
      "version": "0.4.0",
      "author": {
        "name": "Fakhrul Nugroho",
   -    "email": "groupzcode@gmail.com"
   +    "email": "fakhrulnugroho15@gmail.com"
      },
      "license": "MIT",
      "keywords": [
   ```

   Bila keputusan sebaliknya, ganti 5 kemunculan `fakhrulnugroho15@gmail.com` (owner + 4 entri) di `marketplace.json` dan 3 `plugin.json` lainnya.

   Salinan repo dengan diff ini ditambah L7.2 sudah dilint di scratchpad: **M3, M4, M5 = 0**; sisa FAIL hanya R2 (X1) dan S1 (L5.5).

2. **Opsi B — versi hanya di entri marketplace.** Hapus `"version"` dari keempat `plugin.json`, dan **naikkan** entri frontenddev ke 0.4.0 (jangan biarkan 0.3.0: string versi berubah dari 0.4.0 efektif menjadi 0.3.0 dan terlihat seperti turun versi):

   ```diff
   --- a/.claude-plugin/marketplace.json
   +++ b/.claude-plugin/marketplace.json
   @@ -30,7 +30,7 @@
        {
          "name": "frontenddev",
          "description": "Skill dan subagent untuk kerja frontend lintas-stack (React Vite SPA, React Native/Expo, SvelteKit, Svelte + Vite): profil repo, penelusuran kode, perjalanan antar-layar, bentuk layar, kontrak arsitektur, review kesesuaian, dan eksekusi lewat brief",
   -      "version": "0.3.0",
   +      "version": "0.4.0",
          "source": "./src/plugins/frontenddev",
          "author": {
            "name": "Fakhrul Nugroho",
   --- a/src/plugins/analyst/.claude-plugin/plugin.json
   +++ b/src/plugins/analyst/.claude-plugin/plugin.json
   @@ -1,7 +1,6 @@
    {
      "name": "analyst",
      "description": "…",
   -  "version": "0.2.0",
      "author": {
   ```

   Pola yang sama untuk `backenddev` (`-  "version": "0.5.0",`), `frontenddev` (`-  "version": "0.4.0",`), dan `quickdev` (`-  "version": "0.1.0",`). Deskripsi dan email tetap disinkronkan seperti Opsi A.

3. **Deskripsi:** minimal samakan entri frontenddev dengan `plugin.json` (sudah termasuk di diff Opsi A) dan biarkan lint M4 menagih kesamaan. Alternatif lebih kuat: hapus `description` dan `author` dari keempat entri marketplace, karena dokumentasi menyatakan field yang tidak diisi entri diambil dari `plugin.json`. Pilih ini hanya setelah memeriksa panel `/plugin` → Discover pada marketplace git menampilkan deskripsi dengan benar.
4. **Kebijakan rilis** (ditulis di README root, lihat L7.3): setiap PR yang mengubah `src/plugins/<p>/` menaikkan `version` plugin itu. Ditagih lint M7.
5. Isi "Log Keputusan" `ISSUES.md` baris L7.1.

### Selesai bila

- Lint M3 dan M4 = 0.
- `claude plugin validate .` lolos.
- `/plugin` → Installed/Discover menampilkan frontenddev 0.4.0 dengan deskripsi baru (cek manual sekali).

### Risiko & catatan

- Opsi A menuntut disiplin bump di `plugin.json`; tanpa M7, commit baru tanpa bump tidak sampai ke pengguna (kutipan kedua di Konteks).
- Selama marketplace ditambahkan sebagai direktori lokal, versi tidak mengunci apa pun (plugin dimuat di tempat), jadi efek perubahan ini baru terlihat di marketplace git.

---

## L7.2 [Rendah] `plugin.json` liar di root frontenddev

- [x] Selesai

**Plugin:** frontenddev · **Estimasi:** 5 menit · **Bergantung pada:** — · **Memblokir:** L6.3 check M5

### Konteks

Dokumentasi plugins-reference: *"The `.claude-plugin/` directory contains the `plugin.json` file."* dan *"The manifest is optional. If omitted, Claude Code auto-discovers components in default locations and derives the plugin name from the directory name."* Dokumentasi tidak menyebut `plugin.json` di root direktori plugin sebagai lokasi manifest.

### Lokasi & kondisi saat ini

- `src/plugins/frontenddev/plugin.json` berisi hanya `{"name": "frontenddev"}` (3 baris), berasal dari commit `init`.
- Tidak dirujuk di mana pun: `grep plugin.json` di semua `.py/.sh/.json` = 0; `md_search "plugin.json"` di seluruh markdown plugin = 0.
- Lint prototipe: `[FAIL] M5 src/plugins/frontenddev/plugin.json`.

**Koreksi terhadap ISSUES.md:** bagian "Kenapa" menyatakan *"bila berkas itu hilang, plugin memuat manifest minimal ini diam-diam"*. Dokumentasi yang dikutip tidak mendukung itu: tanpa `.claude-plugin/plugin.json`, Claude Code melakukan auto-discovery dan menurunkan nama dari direktori. Hasilnya kebetulan sama (nama `frontenddev`), tetapi alasan penghapusan cukup "berkas mati yang menyesatkan pembaca".

### Rencana perbaikan

1. Hapus berkas:

   ```diff
   --- a/src/plugins/frontenddev/plugin.json
   +++ /dev/null
   @@ -1,3 +0,0 @@
   -{
   -  "name": "frontenddev"
   -}
   ```

   `git rm src/plugins/frontenddev/plugin.json`

2. Pastikan lint M5 aktif di CI (hapus `M5` dari `LINT_IGNORE`).

### Selesai bila

- Berkas tidak ada; lint M5 = 0; frontenddev tetap termuat (`/plugin` → Installed tanpa galat dan ke-10 skill-nya tercantum di detail plugin, atau `claude plugin validate .` lolos).

### Risiko & catatan

Tidak ada risiko fungsional yang teridentifikasi.

---

## L7.3 [Rendah] README

- [x] Selesai

**Plugin:** backenddev, quickdev, frontenddev, analyst, root repo · **Estimasi:** 1–1,5 hari · **Bergantung pada:** L1.1, L1.3 (isi seksi profil dan koeksistensi), L7.1 (kebijakan versi), keputusan lokasi publikasi · **Memblokir:** —

### Konteks

Pengguna memasang keempat plugin dari satu marketplace, user-wide. Tanpa README, tidak ada tempat yang menjelaskan plugin mana untuk kerja apa, apa yang ditulis ke repo pengguna, dan kenapa hook dua plugin bisa menyala bersamaan.

### Lokasi & kondisi saat ini

- Ada: `src/plugins/analyst/README.md` (140 baris), `src/plugins/frontenddev/README.md` (303 baris). Tidak ada: README root, `backenddev/README.md`, `quickdev/README.md`, berkas `LICENSE`.
- `frontenddev/README.md`, seksi "Per-Repo Setup" (baris 272–273): `/plugin marketplace add fakhrulnugroho/frontenddev` lalu `/plugin install frontenddev`. Menurut discover-plugins, bentuk `owner/repo` menunjuk *"a GitHub repository that contains a `.claude-plugin/marketplace.json` file"*. Marketplace di repo ini berada di root repo `agentic-workflow` dengan nama `fakhrulnugroho`, dan repo belum punya remote. Jadi baris pertama salah untuk repo ini, kecuali memang ada repo GitHub terpisah `fakhrulnugroho/frontenddev` yang memuat marketplace sendiri (perlu dicek). Bentuk yang benar: `/plugin marketplace add <owner>/<repo>` lalu `/plugin install frontenddev@fakhrulnugroho` (dokumentasi: *"/plugin install plugin-name@marketplace-name"*); untuk salinan lokal: `/plugin marketplace add ./path/ke/agentic-workflow`.
- `frontenddev/README.md`, seksi "Gate Hook": hook *"menyuntik hanya bila repo terdeteksi frontend — profil ada, … — dan diam di tempat lain"*. Salah untuk repo backend yang punya `.claude/profile/index.json` milik backenddev (L1.1): hook frontend menyuntik pesan "TIDAK SAH".
- `frontenddev/README.md:120` menulis `scripts/check_preconditions.py` dan `scripts/taskdir_state.py` tanpa prefix skill (lint R1 WARN).
- `analyst/README.md:131`: baris `| Perubahan kecil satu berkas tanpa taskdir | quickdev |`. "Satu berkas" di deskripsi quickdev berarti **satu berkas rencana** (`plan/<task>.md`); `quickdev:plan` mendukung langkah multi-berkas.

### Rencana perbaikan

1. **`src/plugins/backenddev/README.md` — kerangka** (gaya mengikuti README frontenddev):
   1. *Pembuka* — plugin backend lintas-stack untuk 7 stack: `java-spring`, `go`, `node`, `bun`, `rust`, `php`, `php-codeigniter`. 12 skill, 6 subagent (`brd-reviewer`, `brief-reviewer`, `code-explorer`, `code-implementor`, `code-reviewer`, `prd-reviewer`). Satu gerbang masuk: `backenddev:tech-lead`.
   2. *Prasyarat* — `python3` (skrip saat ini butuh ≥3.9), `git`, repo git dengan `base_branch` jelas; profil `.claude/profile/` (dibuat `backenddev:profile`).
   3. *Instalasi* — perintah marketplace yang benar (poin di Lokasi), `/plugin install backenddev@fakhrulnugroho`.
   4. *Hook SessionStart* — `hooks/tech-lead-gate.sh`, matcher `startup|resume|clear|compact`, timeout 5 detik; menyala bila `.claude/profile/index.json` ada atau manifest memuat penanda framework server (Spring Boot, gin/fiber/echo/chi/mux/grpc-go, hono/elysia + bun, nest/express/fastify/koa/hapi, axum/actix/rocket/warp/poem, CodeIgniter 4, Laravel/Symfony/Slim/Laminas/Yii2); menyuntik satu baris status profil (ADA/BELUM ADA) plus aturan gerbang. Sebut batasan yang diketahui sampai L1.1/L1.2 selesai.
   5. *Skill* — tabel 12 skill: titik masuk user (`tech-lead`, `profile`, `debug`, `audit`, `document-api`, `architect`) vs internal yang dipanggil skill lain (`analyst`, `task`, `business-analysis`, `system-analysis`, `plan`, `report`).
   6. *Lane tech-lead* — tabel dari Keputusan 1 `tech-lead/SKILL.md`: `PROFILE` → `profile`; `EXPLORE_FACT` → selesai di Fase 1; `PLANNING` → `analyst`; `DEFECT_RCA` → `debug`; `EXEC_BRIEF` → `architect`; `AUDIT_SWEEP` → `audit`; `API_DOCS` → `document-api`. Presedensi: `PROFILE → EXEC_BRIEF → AUDIT_SWEEP → DEFECT_RCA → PLANNING → API_DOCS → EXPLORE_FACT`.
   7. *Rantai planning* — matriks chain dari `analyst/references/chain-rules.md` §1.3–1.4: `BRIEF` / `PRD_BRIEF` / `BRD_PRD_BRIEF`; risk `MINOR` → `BRIEF`; `MAJOR` → ketiganya; `BREAKING` → `PRD_BRIEF` atau `BRD_PRD_BRIEF`; lane terminal yang ditulis ke `TASK.md`: `DIRECT_BRIEF` atau `PRD_CONVERSION`. Approval BRD/PRD hanya oleh `backenddev:analyst`.
   8. *Artefak di repo pengguna* — `.claude/profile/` (`index.json` + 8 berkas `.md`); `backenddev/docs/<YYMMDDhhmm>-<slug>/` (`TASK.md`, `BRD.md`, `PRD.md`, `brief-<NN>-<unit>.md`, `RCA.md`, `REVIEW.md`, `REPORT.md`, laci `.explore/` yang di-gitignore); `backenddev/issues/` (laporan audit + indeks); `docs/api/<slug>.md`. Baris `.gitignore` yang ditambahkan `profile`: `.explore/` dan `.backenddev/`.
   9. *Branch & commit* — branch kerja dicabangkan dari `base_branch`, bukan HEAD aktif; staging path eksplisit (tanpa `git add .`/`-A`); siapa meng-commit apa (tech-lead: profil, audit, RCA, dokumentasi API; analyst: approval BRD/PRD; penulis masing-masing: draft dan brief; implementor: kode per brief; reviewer: `REVIEW.md`; report: `REPORT.md`).
   10. *Penegakan mekanis* — tiap skill menjalankan `scripts/check_preconditions.py` sebelum fase pertama (`--json` tersedia; exit 1 = FAIL); `plan` punya `scaffold_brief.py` dan `validate_briefs.py` (check S…J).
   11. *Pemulihan* — re-entry lewat tech-lead Fase 5; matriks recovery architect (`architect/references/lifecycle-recovery.md`).
   12. *Koeksistensi* — dengan frontenddev (profil bersama sampai L1.1), analyst (tiket ditempel sebagai `request`), quickdev (hook dapat membelokkan alur sampai L1.3).
   13. *Keterbatasan yang diketahui* — prosa singkat. Jangan menautkan `ISSUES.md`, karena berkas itu di-gitignore (`.gitignore:7`).
2. **`src/plugins/quickdev/README.md` — kerangka:**
   1. *Apa & kapan* — alur ringan tanpa taskdir, tanpa subagent, tanpa skrip; satu berkas rencana per tugas, boleh multi-berkas kode. Pakai bila perubahan kecil–menengah dan tidak butuh BRD/PRD/ledger; paling aman hari ini di stack yang tidak dilayani backenddev/frontenddev (mis. Next.js, FastAPI) sampai L1.3 selesai.
   2. *Urutan gate & status terminal* — `profile` (PROFILED) → `explore` (EXPLORED) → `clarify` (CLARIFIED/SKIPPED) → `plan` (PLAN_APPROVED) → `execute` (COMPLETED / VERIFICATION_MANUAL_REQUIRED / BLOCKED) → `review` (REVIEWED / CHANGES_REQUIRED / NO_CHANGES). Selalu panggil dengan prefix: `/quickdev:plan`, dst.
   3. *Artefak* — `repo-profile.md` (default `target_path`; fallback `.dev/profile.md`; maksimal 10.000 karakter; perintah baseline dengan status `PASSED`/`FAILED`/`SKIPPED`/`UNVERIFIED_ENV_NOT_READY`); `plan/<task>.md` (`plan_dir` default `plan`; metadata `Status: DRAFT → APPROVED`, `Author: quickdev:plan`; Section 1–4; checklist langkah; blok penutup `Execution Status`/`Verification`/`Remediation Round`/`Timestamp`).
   4. *Kebijakan git* — `execute` tidak pernah commit dan mensyaratkan working tree bersih selain `plan_path` dan `profile_path` pada putaran awal; `review` read-only (hanya `git diff/status/log/ls-files/rev-parse`); keputusan commit/merge milik user. **Belum ditetapkan** apakah `repo-profile.md` dan `plan/` di-commit atau di-gitignore: keputusan user, lalu tulis di sini.
   5. *Parameter penting* — `skip_baseline_exec` (profile), `require_test_plan` (plan, default `true`), `max_fix_iterations` (execute, default 3), `strict` (review).
   6. *Hidup berdampingan* — hook backenddev/frontenddev menyuntik gerbangnya di repo yang manifestnya cocok; panggil `/quickdev:*` secara eksplisit dan tolak bila model mengarah ke `backenddev:*`/`frontenddev:*` (perilaku setelah L1.3).
   7. *Keterbatasan* — state antargate hidup di percakapan (D7); kunci rencana hanya baris `Status: APPROVED` (D1); `profile` menjalankan test/build tanpa konfirmasi (L3.5); tidak ada jalur resume `execute` sesudah BLOCKED (D2). Perbarui setelah item tersebut diperbaiki.
3. **`README.md` root — kerangka:**
   1. *Isi marketplace* — tabel: plugin, versi efektif (analyst 0.2.0, backenddev 0.5.0, frontenddev 0.4.0, quickdev 0.1.0), satu kalimat fungsi, skill titik masuk (`analyst:intake`, `backenddev:tech-lead`, `frontenddev:lead`, `quickdev:profile`/`quickdev:plan`).
   2. *Instalasi* — `/plugin marketplace add <owner>/<repo>` (atau path lokal), `/plugin install <plugin>@fakhrulnugroho`; catatan bahwa marketplace direktori lokal memuat plugin di tempat dan tidak dikunci versi.
   3. *Memilih plugin* — tabel keputusan: peminta non-engineer/stakeholder → analyst; repo backend 7 stack, kerja berisiko atau butuh kontrak → backenddev; repo React Vite/React Native/SvelteKit/Svelte Vite → frontenddev; perubahan ringan, stack lain, tanpa taskdir → quickdev. Rantai analyst → engineer: tiket `READY` ditempel sebagai permintaan ke `backenddev:tech-lead`/`frontenddev:lead`.
   4. *Koeksistensi* — kedua hook SessionStart jalan paralel; deteksi berbasis manifest; bentrok `.claude/profile/` sampai L1.1; cara memanggil analyst/quickdev secara eksplisit di repo yang ber-hook.
   5. *Prasyarat umum* — `python3`, `git`; tidak ada dependensi pihak ketiga (skrip hanya stdlib).
   6. *Pengembangan* — struktur `src/plugins/*`, `tests/`, `scripts/lint_plugins.py`; cara menjalankan test dan lint (`issues/06-test-ci.md`); kebijakan versi dari L7.1 (bump per PR yang mengubah plugin); `claude plugin validate .` sebelum rilis.
   7. *Lisensi* — keempat `plugin.json` menulis `"license": "MIT"`; tambahkan berkas `LICENSE` di root atau ubah field itu.
4. **Perbaikan README yang ada:**

   ```diff
   --- a/src/plugins/frontenddev/README.md   (seksi Per-Repo Setup)
   -/plugin marketplace add fakhrulnugroho/frontenddev
   -/plugin install frontenddev
   +/plugin marketplace add <owner>/<repo-agentic-workflow>
   +/plugin install frontenddev@fakhrulnugroho
   ```

   Seksi "Gate Hook": ganti "dan diam di tempat lain" dengan perilaku sesudah L1.1, atau sampai L1.1 selesai tambahkan kalimat "di repo yang profilnya dibuat backenddev, hook ini melaporkan profil TIDAK SAH". Baris 120: tulis `skills/<skill>/scripts/check_preconditions.py` dan `skills/lead/scripts/taskdir_state.py`.

   ```diff
   --- a/src/plugins/analyst/README.md   (baris 131)
   -| Perubahan kecil satu berkas tanpa taskdir | `quickdev` |
   +| Perubahan kecil–menengah dengan satu berkas rencana (`plan/<task>.md`), tanpa taskdir | `quickdev` |
   ```

### Selesai bila

- Tiga README baru ada dengan seluruh seksi di atas; tiga perbaikan README lama diterapkan.
- Perintah instalasi di semua README sama dan diuji sekali pada marketplace hasil publikasi (atau path lokal).
- Lint R1 tidak lagi melaporkan `frontenddev/README.md`.

### Risiko & catatan

- Seksi profil, hook, dan koeksistensi akan basi begitu L1.1/L1.3 diterapkan. Tulis README sesudah keputusan L1.1, atau tandai seksi itu jelas sebagai "perilaku saat ini".
- `README.md` di dalam direktori plugin ikut tersalin ke cache pengguna (seluruh direktori plugin disalin); itu diinginkan untuk README, berbeda dengan test (lihat koreksi di `06-test-ci.md` L6.1).

---

## L7.4 [Rendah] Skill internal tidak ditandai

- [x] Selesai

**Plugin:** analyst, backenddev, frontenddev · **Estimasi:** 1 jam + uji manual · **Bergantung pada:** keputusan user · **Memblokir:** L6.3 check F3 (opsional)

### Konteks

Dokumentasi skills ("Frontmatter reference"): `user-invocable` — *"Set to `false` when only Claude should invoke the skill: Claude Code hides it from the `/` menu and doesn't run it when you type `/name`. Use for background knowledge users shouldn't invoke directly. Default: `true`."*

Tabel "Control who invokes a skill":

| Frontmatter | You can invoke | Claude can invoke | When loaded into context |
|---|---|---|---|
| (default) | Yes | Yes | Description always in context, full skill loads when invoked |
| `disable-model-invocation: true` | Yes | No | Description not in context, full skill loads when you invoke |
| `user-invocable: false` | No | Yes | Description always in context, full skill loads when invoked |

### Lokasi & kondisi saat ini

Tidak ada satu pun SKILL yang memakai `user-invocable` atau `disable-model-invocation`. Lima belas skill berdeskripsi "Dipanggil …" (dicek lewat `md_search` di baris 3 frontmatter ke-31 SKILL.md):

| Skill | Deskripsi (kutipan persis, dipotong di "-") |
|---|---|
| `analyst:elicit` | "Dipanggil analyst:intake sesudah tipe dan slug ditetapkan, atau untuk ticketdir berkeadaan ELISITASI, atau analyst:spec saat fakta tiket perlu digali ulang" |
| `analyst:spec` | "Dipanggil analyst:elicit sesudah elisitasi CLOSED, atau analyst:intake untuk ticketdir berkeadaan SPEC/DRAFT/DRIFT dan perubahan tiket READY" |
| `backenddev:analyst` | "Dipanggil gerbang backenddev:tech-lead sesudah lane PLANNING ditetapkan dan taskdir terprovisi" |
| `backenddev:business-analysis` | "Dipanggil backenddev:analyst sebagai hop BRD pada chain BRD_PRD_BRIEF" |
| `backenddev:system-analysis` | "Dipanggil backenddev:analyst pada hop PRD chain BRD_PRD_BRIEF (sesudah BRD APPROVED) atau PRD_BRIEF (tanpa BRD, risk MAJOR/BREAKING)" |
| `backenddev:plan` | "Dipanggil backenddev:analyst (entry_mode PRD sesudah PRD APPROVED, atau LANGSUNG pada chain BRIEF) dan gerbang backenddev:tech-lead (entry_mode RCA dari RCA.md terkonfirmasi)" |
| `backenddev:report` | "Dipanggil backenddev:architect sesudah REVIEW.md terbit dan seluruh brief DONE" |
| `backenddev:task` | "Dipanggil backenddev:analyst pada lane planning, atau gerbang backenddev:tech-lead pada lane DEFECT_RCA dan backfill EXEC_BRIEF" |
| `frontenddev:architect` | "Dipanggil frontenddev:lead ketika ledger taskdir tercentang penuh dan brief READY siap dieksekusi, atau rantai terputus di tengah eksekusi" |
| `frontenddev:contract` | "Dipanggil frontenddev:lead pada setiap lane non-MINOR sesudah hop FLOW/UI yang dijadwalkan tercentang" |
| `frontenddev:plan` | "Dipanggil frontenddev:lead sesudah hop CONTRACT tercentang di ledger, atau langsung pada lane HOTFIX_MINOR, atau sesudah hop BRIEF dibuka ulang" |
| `frontenddev:report` | "Dipanggil frontenddev:architect Phase 5 sesudah REVIEW.md penutup lolos validate_review.py, ter-commit dengan verdict PASS atau WARNING, dan seluruh brief tertutup" |
| `frontenddev:task` | "Dipanggil frontenddev:lead Phase 7 sesudah lane dan taskdir ditetapkan pada lane FULL_PIPELINE, FAST_FORWARD, REFACTOR_ARCH, atau HOTFIX_MINOR" |
| `frontenddev:ui-design` | "Dipanggil frontenddev:lead ketika sections TASK.md memuat ui, sesudah hop FLOW tercentang bila flow ikut dijadwalkan" |
| `frontenddev:ux-design` | "Dipanggil frontenddev:lead ketika sections TASK.md memuat flow" |

Tidak ada README atau SKILL yang menyuruh user memanggil salah satu dari ke-15 skill ini secara langsung (`md_search` pola "user … jalankan/panggil `<skill>`" = 0). README analyst hanya menyarankan `/analyst:intake`.

Tidak dimasukkan (deskripsi "Gunakan ketika …", titik masuk user): analyst `intake`; backenddev `tech-lead`, `profile`, `debug`, `audit`, `document-api`, `architect`; frontenddev `lead`, `profile`, `review`; keenam skill quickdev.

### Rencana perbaikan

1. Tambah satu baris di frontmatter ke-15 SKILL.md di atas, sesudah `description:`. Contoh:

   ```diff
   --- a/src/plugins/backenddev/skills/task/SKILL.md
   +++ b/src/plugins/backenddev/skills/task/SKILL.md
    ---
    name: task
    description: Dipanggil backenddev:analyst pada lane planning, atau gerbang backenddev:tech-lead pada lane DEFECT_RCA dan backfill EXEC_BRIEF - perumusan akar rantai TASK.md berisi kriteria sukses dan batas kerja, ditulis sebelum satu pun skill hilir berangkat
   +user-invocable: false
    metadata:
      mode: compact
    ---
   ```

2. Tambah check F3 di lint (skill berdeskripsi "Dipanggil" wajib `user-invocable: false`) agar skill internal baru ikut tertandai.
3. Tulis di README tiap plugin: skill internal tidak muncul di menu `/`; untuk debugging, panggil lewat gerbangnya (`backenddev:tech-lead`, `frontenddev:lead`, `analyst:intake`).
4. Uji manual sekali per plugin: menu `/` tidak menampilkan ke-15 skill; satu alur fixture (tech-lead → analyst → task; lead → task → plan; intake → elicit → spec) tetap berjalan, artinya model masih bisa memanggilnya lewat tool Skill.

### Selesai bila

- Ke-15 skill punya `user-invocable: false`; menu `/` hanya menampilkan titik masuk; alur uji manual berjalan; lint F3 hijau.

### Risiko & catatan

| Untung | Rugi |
|---|---|
| Menu `/` lebih pendek; `/backenddev:plan` dan `/frontenddev:plan` tidak lagi bersaing dengan `/quickdev:plan` di menu | Tidak bisa memanggil skill internal secara manual untuk debugging atau pemulihan; mengetik `/backenddev:task` tidak menjalankan apa pun |
| User tidak melewati gerbang (tech-lead/lead/intake) lewat menu | `frontenddev:architect` juga dipakai untuk "rantai terputus di tengah eksekusi"; pemulihan harus lewat `frontenddev:lead`, dan lead memang merutekan ke sana |
| Selaras dengan instruksi hook bahwa gerbang jalan lebih dulu | **Tidak menghemat context:** deskripsi tetap selalu dimuat (baris ketiga tabel dokumentasi), dan tidak mengubah pilihan model antar-plugin (masalah L1.3 tetap ada) |

Alternatif: tandai hanya skill yang tidak pernah berguna dipanggil manual (`business-analysis`, `system-analysis`, `report`, `task`, `ui-design`, `ux-design`, `contract`), dan biarkan `plan`, `architect`, `analyst`, `elicit`, `spec` terlihat untuk pemulihan.

---

## L7.5 [Rendah] Field tidak dikenal dan sisa cache lokal

- [x] Selesai

**Plugin:** keempat plugin · **Estimasi:** 15 menit · **Bergantung pada:** keputusan user (nasib `metadata`) · **Memblokir:** L6.3 check G1

### Konteks

Dokumentasi skills ("Frontmatter reference") kini memuat `metadata`: *"Free-form YAML map for your own key-value data, such as entitlement or catalog fields, read by your own tooling from `SKILL.md`. Claude Code doesn't act on its contents, and drops a value that isn't a map. Don't reuse frontmatter field names such as `paths` as keys."* Untuk field yang benar-benar tidak dikenal: *"A field name must match the table exactly, hyphens included: Claude Code ignores a field it doesn't recognize without reporting an error."*

### Lokasi & kondisi saat ini

- Ke-31 SKILL.md memuat `metadata:` berupa map satu kunci `mode`. Nilainya tidak seragam: `standard` (23 skill), `compact` (6: backenddev `business-analysis`, `report`, `system-analysis`, `task`; frontenddev `report`, `task`), `extended` (2: backenddev `tech-lead`, frontenddev `lead`).
- Tidak ada skrip, agent, atau markdown plugin yang membaca `metadata`/`mode` (`md_search` hanya menemukan baris frontmatter itu sendiri).
- Lint prototipe: F1 = 0 (tidak ada field tak dikenal; `metadata` berbentuk map).
- `src/plugins/frontenddev/skills/lead/scripts/__pycache__/check_preconditions.cpython-313.pyc` tanpa `check_preconditions.py` (lint G1 WARN). Selain itu ada `__pycache__` lokal di hampir semua direktori skrip; semuanya tidak ter-track (`.gitignore`: `__pycache__/`, `*.py[cod]`). Kemungkinan terbentuk karena skrip dijalankan di tempat, misalnya dari marketplace direktori lokal yang memuat plugin di tempat.

**Koreksi terhadap ISSUES.md:** `metadata` **adalah field resmi** menurut dokumentasi saat ini (map bebas yang tidak ditindaklanjuti Claude Code), bukan "bukan field resmi". Nilainya juga bukan selalu `mode: standard`, melainkan tiga nilai berbeda.

### Rencana perbaikan

1. Pilih salah satu:
   - **Pertahankan** (disarankan bila `mode` memang label ukuran SKILL untuk penulis): tambahkan satu paragraf di README root, seksi Pengembangan: "`metadata.mode` = label gaya penulisan SKILL (`compact`/`standard`/`extended`); tidak dibaca Claude Code maupun skrip."
   - **Hapus** dari ke-31 SKILL.md:

     ```diff
      ---
      name: <skill>
      description: …
     -metadata:
     -  mode: standard
      ---
     ```

2. Bersihkan cache lokal (tidak ter-track, aman):

   ```sh
   find src -name __pycache__ -type d -prune -exec rm -rf {} +
   ```

3. Cegah terulang: test memakai `PYTHONDONTWRITEBYTECODE=1` (sudah di `conftest.py` L6.1); lint G1 memberi FAIL bila bytecode pernah ter-track.

### Selesai bila

- Keputusan `metadata` tercatat dan diterapkan; lint G1 = 0; `find src -name '*.pyc'` kosong setelah menjalankan test.

### Risiko & catatan

- `__pycache__` akan muncul lagi setiap kali skrip dijalankan di tempat. Itu tidak berbahaya (di-gitignore), tetapi G1 WARN akan kembali bila berkas `.py` dipindah atau dihapus tanpa membersihkan cache-nya.
