# Alur Plugin `backend`

> Plugin `backend` (v0.15.0, `src/plugins/backend/.claude-plugin/plugin.json`) menyediakan 12 skill dan 6 subagent untuk kerja backend lintas-stack: Java Spring, Go, Node, Bun, Rust, PHP, dan CodeIgniter 4. Plugin ini dipakai untuk tiap permintaan kerja di repo backend, yaitu fitur, bugfix, audit, dokumentasi API, maupun pertanyaan tentang kode. Semua permintaan masuk lewat satu gerbang, `backend:tech-lead`. Gerbang itu memutuskan lane, risk level, dan taskdir dari kode aktual sebelum satu brief ditulis atau satu berkas `src/` disentuh. Plugin sengaja dibuat generic: pengetahuan spesifik-repo disimpan di `.claude/profile/backenddev/`, sedangkan pengetahuan spesifik-stack disimpan di adapter `skills/profile/stacks/<stack>.md`. Dokumen taskdir (`backenddev/docs/`) diabaikan git dan tidak pernah di-commit (Langkah 24): keutuhannya dijaga materai di disk yang ditulis `doc_seal.py`, dan cermin nataflow menjadi satu-satunya salinannya di luar mesin kerja. Yang masih di-commit hanya kode dan artefak tingkat repo (profil, laporan audit, indeks issues, `docs/api/`).

Semua path berkas di dokumen ini relatif terhadap `src/plugins/backend/`.

## Peta Komponen

| Komponen | Jenis | Peran singkat | Berkas |
|---|---|---|---|
| `backend:tech-lead` | skill (titik masuk user) | Gerbang tiap permintaan: menentukan lane, risk, taskdir, branch, dan re-entry rantai | `skills/tech-lead/SKILL.md` |
| `backend:profile` | skill (titik masuk user) | Deteksi stack, pemindaian 17 titik arsitektur, dan baseline perintah ke `.claude/profile/backenddev/` | `skills/profile/SKILL.md` |
| `backend:debug` | skill (titik masuk user) | Membuktikan rantai kausal `file:line` lalu menulis `RCA.md` | `skills/debug/SKILL.md` |
| `backend:audit` | skill (titik masuk user) | Menyapu 6 dimensi konvensi arsitektur lalu menulis laporan ke `backenddev/issues/` | `skills/audit/SKILL.md` |
| `backend:document-api` | skill (titik masuk user) | Memetakan endpoint nyata di kode ke `docs/api/<slug>.md` | `skills/document-api/SKILL.md` |
| `backend:architect` | skill (titik masuk user) | Orkestrasi sekuensial brief READY, verifikasi penutup, dan review tunggal | `skills/architect/SKILL.md` |
| `backend:analyst` | skill (`user-invocable: false`) | Orkestrasi rantai TASK/BRD/PRD/brief beserta gerbang approval dokumen | `skills/analyst/SKILL.md` |
| `backend:task` | skill (`user-invocable: false`) | Menulis akar rantai `TASK.md` | `skills/task/SKILL.md` |
| `backend:business-analysis` | skill (`user-invocable: false`) | Hop BRD: elisitasi aturan bisnis ke `BRD.md` DRAFT | `skills/business-analysis/SKILL.md` |
| `backend:system-analysis` | skill (`user-invocable: false`) | Hop PRD: kontrak API, lifecycle, validasi, permission, dan impact map ke `PRD.md` DRAFT | `skills/system-analysis/SKILL.md` |
| `backend:plan` | skill (`user-invocable: false`) | Menerbitkan brief `READY` atomik (hop BRIEF atau jalur RCA) | `skills/plan/SKILL.md` |
| `backend:report` | skill (`user-invocable: false`) | Menulis `REPORT.md` penutup dari diff merge-base | `skills/report/SKILL.md` |
| `code-explorer` | agent | Penelusur bukti `file:line` yang hanya boleh menulis ke laci `.explore/` | `agents/code-explorer.md` |
| `code-implementor` | agent | Menerapkan satu brief READY lalu meng-commit kodenya sendiri; status brief ditulis di disk | `agents/code-implementor.md` |
| `code-reviewer` | agent | Menilai diff merge-base terhadap union brief, menulis `REVIEW.md` di disk, lalu meng-commit baris indeks `backenddev/issues/README.md` | `agents/code-reviewer.md` |
| `brd-reviewer` | agent | Vonis BRD `Approved`/`Issues Found` | `agents/brd-reviewer.md` |
| `prd-reviewer` | agent | Vonis PRD `Approved`/`Issues Found` | `agents/prd-reviewer.md` |
| `brief-reviewer` | agent | Audit helikopter batch brief terhadap TASK/BRD/PRD | `agents/brief-reviewer.md` |
| `detect.py` + `gate_text.py` | hook SessionStart | Menyuntik blok `<backend-tech-lead-gate>` sekali per sesi | `hooks/detect.py`, `hooks/gate_text.py`, `hooks/hooks.json` |
| `guard_bash.py` | hook PreToolUse | Pagar mekanis Bash/Edit/Write untuk explorer, implementor, dan reviewer (fail-closed) | `hooks/guard_bash.py` |
| `check_preconditions.py` | script (per skill) | Prasyarat sebelum fase pertama (exit 0 = PASS, 1 = FAIL) | `skills/<skill>/scripts/check_preconditions.py` |
| `precondition_lib.py` | script | Parser frontmatter, taskdir, chain, status git, dan profil; mengimpor `hooks/detect.py` | `skills/_common/precondition_lib.py` |
| `brief_status.py` | script | Mesin status brief, bukti `DONE` dari commit unit sejak `base_commit`, tautan `supersedes`, kesegaran `REVIEW.md` dari ujung `range:`, dan `HALT.md` (`DICABUT` tidak menahan) | `skills/_common/brief_status.py` |
| `doc_seal.py` | script | Materai dokumen taskdir di disk: `root` (`base_commit`), `approve` (`approved_seal` BRD/PRD + centang ledger), `lock-briefs` (`sidik_kontrak`), `tick --hop BRIEF`, `cabut-halt`, dan `status` | `skills/_common/doc_seal.py` |
| `docs_git.py` | script | Penanda ignore `backenddev/docs/.gitignore`, status, dan migrasi sekali jalan dokumen taskdir yang masih ter-track. Salinan identik dengan `frontend` | `skills/_common/docs_git.py` |
| `validate_doc.py` | script | Self-test mekanis `TASK.md`/`BRD.md`/`PRD.md` | `skills/_common/validate_doc.py` |
| `run_verification.py` | script | Verifikasi `baseline` dan `closing` (vonis relatif baseline) | `skills/_common/run_verification.py` |
| `verify_scope.py` | script | Diff commit dibandingkan dengan `## File scope` brief, dan kontrak brief dengan `sidik_kontrak`-nya | `skills/_common/verify_scope.py` |
| `sync_payload.py` | script | Argumen tool MCP nataflow (task, workdir, dokumen) untuk satu taskdir (isi disk) atau dokumen repo (isi `HEAD`); read-only, dua fase | `skills/_common/sync_payload.py` |
| `nataflow_sync.py` | pustaka | Config `.claude/nataflow.json`, identitas repo, isi disk atau blob `HEAD`, dan diff manifest remote. Salinan identik di keempat plugin | `skills/_common/nataflow_sync.py` |
| Prosedur sinkron nataflow | referensi | Urutan panggilan tool MCP dua fase dan target per titik panggil | `skills/tech-lead/references/nataflow-sync.md` |
| `commit_lib.py` | script | Pesan commit brief dari `commit_template` profil | `skills/_common/commit_lib.py` |
| `chain_counters.py` | script | Plafon loop rantai di `## Counters` `TASK.md`, dengan log tulisan skrip `.explore/counters-log.json` | `skills/analyst/scripts/chain_counters.py` |
| `scaffold_brief.py` | script | Mengunci matriks alokasi, lalu menulis kerangka brief | `skills/plan/scripts/scaffold_brief.py` |
| `validate_briefs.py` | script | Validasi batch dan per-brief, serta state ronde review brief | `skills/plan/scripts/validate_briefs.py` |
| `symbol_map.py` | script | Peta simbol yang disunting satu commit, dicocokkan dengan kolom `Anchor` | `skills/architect/scripts/symbol_map.py` |
| `migrate_profile.py` | script | Memindah profil lama `.claude/profile/` ke `.claude/profile/backenddev/` via `git mv` | `skills/profile/scripts/migrate_profile.py` |
| Adapter stack | referensi | `java-spring`, `go`, `node`, `bun`, `rust`, `php`, `php-codeigniter`. Masing-masing memuat 7 seksi wajib: `## Detection`, `## Commands`, `## Layer taxonomy`, `## Navigation recipes`, `## Audit checklist`, `## API surface`, `## Failure signatures` | `skills/profile/stacks/*.md`, kontrak di `_CONTRACT.md` |

Skill ber-`user-invocable: false` tidak muncul di menu `/`. Untuk memulai, melanjutkan, atau memulihkan rantai, user memanggil `/backend:tech-lead` (README).

## Alur Utama

```mermaid
flowchart TD
    U["Permintaan user"] --> HK["SessionStart: detect.py menyuntik blok backend-tech-lead-gate"]
    HK --> TL["backend:tech-lead — Gerbang Masuk"]
    TL -->|"4 pengecualian: klarifikasi, konsep umum, VCS, /analyst:* /product:* /quickdev:*"| DIRECT["Jawab langsung tanpa gerbang"]
    TL --> F0{"Fase 0: prasyarat --read-only, profil ada?"}
    F0 -->|"profil absen/rusak/lama & rute mengubah kode"| PROF["backend:profile GENERATE / REFRESH / MIGRATE"]
    F0 -->|"ya"| F1["Fase 1: eksplorasi kode — code-explorer atau fast-path ≤3 Glob+Grep"]
    F1 --> F2["Fase 2: klarifikasi AskUserQuestion 1–3 pertanyaan (bila ambigu)"]
    F2 --> K1{"Keputusan 1: lane"}
    K1 -->|EXPLORE_FACT| EF["Jawaban di chat — selesai, tanpa taskdir"]
    K1 -->|PROFILE| PROF
    K1 -->|"lane lain"| K2["Keputusan 2: risk BREAKING / MAJOR / MINOR"]
    K2 --> F3["Fase 3: prasyarat penuh 6/6, taskdir, branch dari base_branch, baseline build"]
    F3 --> F4["Fase 4: framing handoff + langkah pertama"]
    F4 -->|AUDIT_SWEEP| AUD["backend:audit → backenddev/issues/*.md"]
    F4 -->|API_DOCS| DOC["backend:document-api → docs/api/slug.md"]
    F4 -->|DEFECT_RCA| DBG["backend:task (akar) + backend:debug → RCA.md"]
    F4 -->|PLANNING| AN["backend:analyst"]
    F4 -->|EXEC_BRIEF| ARC["backend:architect"]

    AN --> TK["backend:task → TASK.md (akar + ledger Chain), doc_seal root"]
    TK --> CH{"chain"}
    CH -->|BRD_PRD_BRIEF| BA["business-analysis → BRD.md DRAFT (brd-reviewer)"]
    BA --> DG1{"Gerbang dokumen analyst: user setuju?"}
    DG1 -->|"tolak / OQ memblokir"| BA
    DG1 -->|"APPROVED"| SA
    CH -->|PRD_BRIEF| SA["system-analysis → PRD.md DRAFT (prd-reviewer)"]
    SA --> DG2{"Gerbang dokumen analyst: user setuju?"}
    DG2 -->|"tolak / OQ memblokir"| SA
    DG2 -->|"APPROVED"| PL
    CH -->|BRIEF| PL["backend:plan → brief-NN-unit.md READY (brief-reviewer)"]
    PL -->|"pemicu eskalasi"| ESC["analyst Fase 5: naikkan chain"]
    ESC --> SA
    PL --> G6{"analyst Fase 6: 15 predikat"}
    G6 -->|READY_FOR_IMPLEMENTATION| RE["tech-lead Fase 5 — re-entry"]
    G6 -->|NOT_READY_FOR_IMPLEMENTATION| RE

    DBG -->|"RCA ROOT_CAUSE_CONFIRMED via gerbang"| PLR["backend:plan entry_mode RCA"]
    DBG -->|INCONCLUSIVE| USR["Kembali ke user + bukti dibutuhkan"]
    PLR --> RE
    AUD --> RE
    DOC --> RE
    PROF --> RE

    RE -->|"brief READY terkunci"| ARC
    RE -->|"temuan audit terpilih (≤7)"| AN
    RE -->|"NOT_READY / BLOCKED / HALT / P1 — taskdir sama + reentry_reason"| AN

    ARC --> LOOP["Per brief: lease → code-implementor → commit kode → gerbang kompilasi → verify_scope → symbol_map"]
    LOOP -->|"BLOCKED / HALT.md"| RE
    LOOP -->|"semua brief DONE"| CLOSE["Verifikasi penutup build+test (relatif baseline)"]
    CLOSE -->|"merah"| RE
    CLOSE -->|"hijau"| REV["code-reviewer → REVIEW.md (disk) + commit indeks issues"]
    REV -->|P1| RE
    REV -->|"CLEAN / P3 / P2"| SC{"Gerbang Success Criteria TASK.md"}
    SC -->|"ada butir tanpa bukti"| RE
    SC -->|"terpenuhi"| RPT["backend:report → REPORT.md"]
    RPT --> RE
    RE -->|"COMPLETED / COMPLETED (WARNING)"| FIN["Rantai selesai — push/PR/merge hanya atas izin user"]
```

**Narasi singkat.**

1. Hook SessionStart menyuntik aturan bahwa `backend:tech-lead` jalan lebih dulu untuk tiap permintaan kerja, termasuk susulan kecil di tengah sesi.
2. `tech-lead` membaca profil, lalu membuktikan permukaan yang diminta dari kode aktual. Pembuktian memakai subagent `code-explorer` bila satu pemicu dispatch aktif; tanpa pemicu, dipakai fast-path berkuota 3. Sesudah itu gerbang memilih tepat satu dari tujuh lane dengan presedensi `PROFILE → EXEC_BRIEF → AUDIT_SWEEP → DEFECT_RCA → PLANNING → API_DOCS → EXPLORE_FACT`.
3. Untuk lane yang mengubah repo (`PLANNING`, `DEFECT_RCA`, `EXEC_BRIEF`, `AUDIT_SWEEP`, `API_DOCS`), gerbang menjalankan prasyarat penuh. Tiga lane pertama lalu memakai ulang atau membuat taskdir `backenddev/docs/<YYMMDDhhmm>-<slug>/`, mencabangkan branch dari `base_branch`, dan menjalankan baseline build. `AUDIT_SWEEP` berjalan di `base_branch` dan `API_DOCS` di branch aktif, keduanya tanpa taskdir dan tanpa branch baru.
4. Lane `PLANNING` diserahkan ke `backend:analyst`. Analyst menurunkan panjang rantai (`chain`) dari dua sumbu, yaitu sumbu bisnis (butuh BRD) dan sumbu kontrak (butuh PRD). Ia lalu menjalankan hop satu per satu dengan gerbang approval user untuk BRD dan PRD, dan menutup dengan 15 predikat `READY_FOR_IMPLEMENTATION`.
5. `backend:architect` mengeksekusi brief secara sekuensial. Tiap brief dikerjakan satu `code-implementor` yang meng-commit kodenya sendiri dan dipagari lease hook. Sesudah semua brief DONE, architect menjalankan verifikasi penutup sekali, mendispatch satu `code-reviewer`, lalu memanggil `backend:report`.
6. Tiap skill hilir pulang ke `tech-lead` Fase 5 (re-entry). Di sana gerbang meng-commit artefak repo yang menunggu (profil, laporan audit, `docs/api/`), mencerminkan taskdir ke nataflow, dan menentukan langkah berikutnya dari tabel "pengirim balik". Kegagalan selalu dikerjakan ulang **di taskdir yang sama** lewat lane `PLANNING` dengan `reentry_reason`.
7. **Dokumen taskdir di luar git.** Prasyarat penuh `tech-lead` menulis penanda `backenddev/docs/.gitignore` (berisi `*`, ikut mengabaikan dirinya sendiri). Repo yang masih menyimpan dokumen taskdir ter-track dirutekan ke migrasi sekali jalan lebih dulu. Setiap titik yang dulu dikunci commit dokumen kini dikunci materai `doc_seal.py`: akar (`base_commit`), approval BRD/PRD (`approved_seal`), batch brief (`sidik_kontrak`), dan penutupan ledger. Bukti `DONE` brief dan kesegaran review dibaca dari commit kode.

## Alur per Skill

### `backend:tech-lead`

- **Pemicu / kapan dipakai**: tiap pesan user berupa permintaan perubahan perilaku, bugfix, audit, eksekusi artefak, susulan cakupan, koreksi arah, atau pertanyaan baca-kode. Pertanyaan baca-kode memakai jalur cepat `references/explore-fact.md`. Ada empat pengecualian yang dijawab tanpa gerbang (`references/gate-scope.md` bagian 1): jawaban klarifikasi, konsep umum non-repo, operasi VCS atas kerja tuntas, dan alur `/analyst:*`, `/product:*`, atau `/quickdev:*` yang dipanggil eksplisit. Persetujuan `BRD.md`/`PRD.md` bukan pemicu; ia diteruskan ke `backend:analyst`.
- **Prasyarat**: `scripts/check_preconditions.py --read-only` di Fase 0. Prasyarat penuh 6 check dijalankan tanpa flag di Fase 3 butir 0, atau dengan `--re-entry` di Fase 5. Keenam check: Profile Index & Invariants, Git Worktree & HEAD State, Git Clean Working Tree, Workspace Write Access, Profile Commands, dan Base Branch & Branch Convention. Check 3 lebih dulu menulis penanda `backenddev/docs/.gitignore`, atau FAIL `MIGRASI` bila berkas `backenddev/docs/` masih ter-track (`references/gate-lifecycle.md` bagian 0). Mode `--read-only` tidak menulis apa pun.
- **Langkah**:
  1. **Fase 0**: jalankan prasyarat read-only. Bila profil absen, pertanyaan baca-kode tetap dijawab dalam mode terdegradasi, sedangkan rute yang mengubah kode diarahkan ke `PROFILE` lebih dulu. Profil di lokasi lama memicu `PROFILE` mode MIGRATE.
  2. **Fase 1**: eksplorasi kode. Kuota main loop maksimal 3 panggilan `Glob`+`Grep`, potongan ≤40 baris, dan tanpa membaca berkas penuh. `code-explorer` wajib didispatch lewat `dispatcher/explorer.md` bila salah satu pemicu aktif: kerja melintasi lebih dari satu layer, yang dicari relasi, simbol tak ditemukan di Glob #1, atau kuota habis. Eksplorasi berhenti sesudah tiap permukaan yang diminta terbukti atau tercatat belum terbukti. Untuk pertanyaan faktual murni, skill menjawab lalu selesai.
  3. **Fase 2**: tepat satu kali `AskUserQuestion` (1–3 pertanyaan), hanya bila rute atau batas modul masih ambigu.
  4. **Keputusan 1 (lane)**: pilih dari tabel `references/decisions.md` bagian 6. Mengarang lane baru dilarang.
  5. **Keputusan 2 (risk)**: `BREAKING` (kontrak eksternal berubah), `MAJOR` (validasi bisnis, transaksi, field opsional baru), atau `MINOR` (perubahan internal terisolasi). Bila ragu, pilih yang lebih tinggi. `strict_mode` menaikkan satu tingkat.
  6. **Fase 3**: prasyarat penuh, lalu provisi taskdir (pakai ulang yang belum tuntas) dan branch `branch_convention`+slug dari `base_branch`. Lane `PLANNING`/`EXEC_BRIEF` juga menjalankan baseline `build`. Lane `DEFECT_RCA` memanggil `backend:task` sesudah branch kerja aktif (prasyarat `task` menolak akar di base atau branch lain). Kegagalan pascaeksekusi di taskdir tanpa ledger `## Chain` dirutekan ke `plan` jalur RCA atau `debug`, bukan `PLANNING`. Plafon `analyst` yang tertembus berakhir di pertanyaan ke user: rumuskan ulang di taskdir baru atau hentikan. Lane `EXEC_BRIEF` tanpa `TASK.md` menjalankan backfill `task`. Laporan explorer disalin ke `<taskdir>/.explore/gate-<slug>.md`.
  7. **Fase 4**: framing handoff deterministik, yaitu Target Skill, Taskdir, File Scope, Risk Level, Acceptance Criteria, Stop Conditions, `evidence`, dan `Finding Source`/`Ticket Source`. Langkah pertama rute dijalankan di giliran yang sama.
  8. **Fase 5 (re-entry)**: prasyarat `--re-entry`, lalu commit artefak repo yang menunggu (profil, laporan `audit`, `docs/api/`) dengan staging path eksplisit, lalu sinkron nataflow (`gate-lifecycle.md` bagian 6 butir 2a: `--repo-docs` untuk pengirim `audit`/`document-api`/`profile`, `--taskdir` untuk lainnya). Langkah lanjut ditentukan dari tabel pengirim balik di bawah. Rute "sinkron ulang taskdir" hanya menjalankan Fase 0 `--read-only` dan prosedur sinkron, tanpa provisi.
- **Subagent yang didispatch**: `code-explorer`, hanya di Fase 1 butir 2 (satu titik sah). Balikan `confidence: low` atau rusak memicu pertajaman objective dan satu kali ulang, lalu sapuan manual.
- **Output / artefak**: blok `### TECH-LEAD GATEWAY DECISION` (Lane, Taskdir, Branch, Bukti, Justifikasi Rute, File Scope, First Action) atau `### TECH-LEAD RE-ENTRY DECISION`. Taskdir, branch, dan laporan laci `backenddev/docs/.explore/<slug>.md` (tidak di-commit).
- **Gerbang & commit**: gerbang hanya meng-commit artefak repo `profile`, `audit`, dan `document-api` di Fase 5 (termasuk `docs: migrate backend profile`), ditambah commit migrasi `chore: lepas backenddev/docs dari git` yang dibuat `docs_git.py migrate` sesudah persetujuan user. Dokumen taskdir tidak pernah di-commit. Amandemen akar `TASK.md` adalah suntingan disk yang lolos `validate_doc.py --kind task` (`base_commit` tetap), dan pencabutan `HALT.md` yang scope-nya diterima user memakai `doc_seal.py cabut-halt` (`status: DICABUT`, berkas tetap). Push, merge, rebase, `gh pr create`, dan `branch -D` dilarang tanpa izin user.
- **Lanjut ke**: skill rute lane, lalu kembali ke Fase 5 sesudah tiap skill hilir selesai.

```mermaid
flowchart TD
    M["Pesan user"] --> X{"Pengecualian (4)?"}
    X -->|ya| J["Jawab langsung"]
    X -->|tidak| P0["Fase 0: check_preconditions --read-only"]
    P0 --> P1{"Pemicu dispatch mekanis aktif?"}
    P1 -->|ya| EXP["code-explorer via dispatcher/explorer.md"]
    P1 -->|tidak| FP["fast-path: 1 Glob + Grep (kuota 3)"]
    EXP --> Q{"Permintaan murni faktual?"}
    FP --> Q
    Q -->|ya| ANS["Format explore-fact bagian 3 — selesai"]
    Q -->|tidak| AMB{"Masih ambigu?"}
    AMB -->|ya| ASK["Fase 2: AskUserQuestion 1x"]
    AMB -->|tidak| D1
    ASK --> D1["Keputusan 1: lane + Keputusan 2: risk"]
    D1 --> PV{"Lane memprovisi?"}
    PV -->|"PROFILE / EXPLORE_FACT"| RUN
    PV -->|ya| FULL["Prasyarat penuh 6/6"]
    FULL -->|FAIL| REM["Remediasi: PROFILE / stash / checkout base_branch / MIGRASI"]
    FULL -->|PASS| TD["Taskdir: pakai ulang atau baru, branch dari base_branch, baseline build"]
    TD --> RUN["Fase 4: framing + First Action di giliran yang sama"]
```

**Tabel pengirim balik Fase 5** (`references/gate-lifecycle.md` bagian 6):

| Pengirim & vonis | Langkah lanjut gerbang |
|---|---|
| `profile` | Commit profil + `.gitignore`, ulangi Fase 0, lanjutkan rute tertunda |
| `analyst` `READY_FOR_IMPLEMENTATION` | Rutekan ke `backend:architect` |
| `analyst` `NOT_READY_FOR_IMPLEMENTATION` | Selesaikan akar masalah, lalu lane `PLANNING` pada taskdir sama dengan `reentry_reason` berisi predikat gagal |
| `analyst` membawa amandemen akar | Tulis ulang `## Success Criteria`/`## Out of Scope` di disk, jalankan `validate_doc.py --kind task` (tanpa commit; `base_commit` tetap), lalu `PLANNING` lagi |
| `debug` `ROOT_CAUSE_CONFIRMED` | `plan` dengan `entry_mode: RCA`, `risk`, dan `file_scope` eksplisit |
| `debug` `INCONCLUSIVE` | Kembali ke user dengan daftar bukti tambahan |
| `plan` jalur RCA, brief READY terkunci (`lock-briefs`) | `backend:architect` pada taskdir sama |
| `plan` jalur RCA membawa pemicu eskalasi | Tanya user. Bila naik, amandemen ke `PRD_BRIEF` lalu `PLANNING` (analyst mulai dari hop PRD) |
| `audit` | Ringkasan per severity, user memilih ≤7 temuan, taskdir baru, lalu `PLANNING` + `finding_source` |
| `architect` `TERTAHAN (scope)` / `HALT.md` `SCOPE`/`SYMBOL` | Tanya user: bila diterima, `doc_seal.py cabut-halt` lalu architect lagi; bila di-reset, user sendiri yang me-reset lalu `PLANNING` |
| `architect` `HALT.md` `COMPILE`/`STRAY` | `PLANNING` pada taskdir sama. `plan` menambah baris `repairs` |
| `architect` severity `P1` | `PLANNING` pada taskdir sama, `finding_source` = `REVIEW.md`, `reentry_reason` = `REVIEW P1: <ID>` |
| `architect` `COMPLETED` / `COMPLETED (WARNING)` | Rantai selesai. Pada WARNING, tawarkan taskdir perbaikan P2 (tidak otomatis) |
| `architect` membawa `Umpan balik profil` | Tanya user. Bila ya, jalankan `backend:profile` dengan `reported_anti_patterns` |
| `document-api` | Commit `docs/api/`, rantai selesai |

### `backend:profile`

- **Pemicu / kapan dipakai**: repo belum punya `.claude/profile/backenddev/`, profil rusak/tidak lengkap/di lokasi lama, konfigurasi berubah, atau gerbang meneruskan `reported_anti_patterns`. Bisa juga dipanggil langsung `/backend:profile`.
- **Prasyarat**: `scripts/check_preconditions.py [--mode] [--stack]`, 6 check. Baris `Terselesaikan: mode <GENERATE | REFRESH | MIGRATE>` menetapkan mode kerja.
- **Langkah**:
  1. **Fase 0**: deteksi stack lewat `hooks/detect.py` atas manifest (root, workspace, `apps/*`, `packages/*`, `services/*`), lalu baca adapter `stacks/<stack>.md`. Nol stack menghentikan skill. Bila ada lebih dari satu stack, user memilih.
  2. **Fase 1**: tentukan mode. GENERATE langsung jalan. REFRESH meminta konfirmasi (kecuali `force`). MIGRATE menjalankan `migrate_profile.py` lalu melompat ke Fase 7.
  3. **Fase 2**: pindai 17 titik arsitektur (`references/scan-guide.md` titik 1–14, `references/convention-scan.md` titik 15–17), dengan anchor `<file>#<simbol>` tanpa nomor baris.
  4. **Fase 3**: wawancara inkonsistensi (Gaya A vs B), konfirmasi konvensi dan anti-pattern, vonis `[MASIH HIDUP]`/`[PUNAH]` saat REFRESH, dan kandidat `[DARI EKSEKUSI]`.
  5. **Fase 4**: baseline nyata untuk `build`, `typecheck`, `lint`, `test`, `test-single`, dan `migration-status`. Perintah yang menyentuh DB, jaringan, atau docker butuh izin via satu `AskUserQuestion`. `migration-apply`, `typecheck-scoped`, dan `typecheck-per-brief` hanya disalin dari adapter.
  6. **Fase 5**: cek state git, peringatkan bila `backenddev/issues/` ikut di-ignore, dan tambahkan baris `.backenddev/` ke `.gitignore` bila belum ter-ignore. Dokumen taskdir (termasuk `.explore/`) diabaikan lewat penanda `docs_git.py`, bukan baris `.gitignore` akar.
  7. **Fase 6**: tulis `index.json` + 8 berkas `.md`.
  8. **Fase 7**: laporan penutup beserta audit field `tidak terdeteksi`.
- **Subagent yang didispatch**: tidak ada.
- **Output / artefak**: `.claude/profile/backenddev/` berisi `index.json` (project, stack, architecture, root_namespace, source_root, commit_convention, commit_template, base_branch, branch_convention) dan `stack.md`, `module-structure.md`, `domain-map.md`, `surface-map.md`, `code-conventions.md`, `anti-patterns.md`, `invariants.md`, `commands.md`. Kemungkinan juga `.gitignore`.
- **Gerbang & commit**: skill ini tidak meng-commit. Slot `Menunggu commit` menyebut path yang di-stage gerbang di Fase 5. Menjalankan `migrate`/`seed`/`reset` atau memperbaiki kode demi baseline hijau dilarang.
- **Lanjut ke**: `backend:tech-lead` (ulangi Fase 0, lanjutkan rute tertunda).

### `backend:analyst`

- **Pemicu / kapan dipakai**: hanya dari gerbang `tech-lead` pada lane `PLANNING`, setelah taskdir terprovisi dan `risk` tertetapkan. Permintaan user langsung dikembalikan ke gerbang.
- **Prasyarat**: `scripts/check_preconditions.py --taskdir --risk [--chain]`, 7 check: Taskdir, Profile & Commit Convention, Risk Level Enum, Chain Enum & Risk Alignment, Artifact vs Chain Consistency, Git Worktree, dan Resume Point. Check 7 (`Resume Point`) menentukan titik masuk Fase 0.
- **Langkah**:
  1. **Fase 0 (resume)**: bila `TASK.md` sudah ada, `task` tidak dipanggil lagi. Chain dan risk dibaca dari frontmatter, dan hop teratas yang `[ ]`/`[~]` dilanjutkan. Bila ledger sudah tercentang penuh, skill butuh `reentry_reason`.
  2. **Fase 1 (derivasi chain)**: vonis sumbu bisnis (5 butir) dan sumbu kontrak (3 butir) dari `references/chain-rules.md`, lalu terapkan matriks. Bisnis aktif + kontrak aktif → `BRD_PRD_BRIEF`. Bisnis nol + kontrak aktif → `PRD_BRIEF`. Keduanya nol → `BRIEF`. Bisnis aktif + kontrak nol tidak sah dan dinaikkan ke `BRD_PRD_BRIEF`. Pasangan `(risk, chain)` diverifikasi: `BREAKING` hanya ber-PRD, dan `MINOR` hanya `BRIEF`. `MINOR` yang sumbu kontraknya aktif dinaikkan ke `MAJOR`.
  3. **Fase 2**: panggil `backend:task`, lalu verifikasi `### TASK ROOT LOCKED` (uji akar 9/9, `base_commit` terkunci) dan isi ledger `## Chain`. Akar yang terkunci di giliran ini langsung disinkron ke nataflow.
  4. **Fase 3**: jalankan hop teratas yang belum tercentang, satu per giliran. `BRD` → `business-analysis`, `PRD` → `system-analysis`, `BRIEF` → `plan`. Verdict reviewer hop dibaca dari `{taskdir}/.explore/review/<brd|prd|brief>.md`, bukan dari chat. Butir 0 menangani re-entry dengan membuka hop pemilik kegagalan menjadi `[~]` sesudah `chain_counters.py --bump reentry` dan `--reset-hop`.
  5. **Fase 4 (gerbang dokumen BRD/PRD)**: predikat masuk berupa blok review `Approved` di `.explore/review/<brd|prd>.md` (draft tidak dikunci terpisah), cek `## Open questions` (≤3, tidak memblokir), ringkasan eksekutif 3–4 kalimat beserta path artefak (bukan salinan isinya), lalu satu `AskUserQuestion`: tiap `BR-DISANGGAH` dan asumsi aktif `sementara dipakai:` sebagai pertanyaan tersendiri, ditambah pertanyaan persetujuan. Bila user setuju, `doc_seal.py approve --doc <BRD|PRD> --answer -` menulis `status: APPROVED`, `approved_seal` (sidik isi yang disetujui), dan jawaban user, lalu mencentang ledger `@ APPROVED <sidik12>` dalam satu langkah, lalu sinkron nataflow sehingga dokumen `APPROVED` tercermin seketika. Bila user menolak, jalankan `--bump reject:<HOP>` (sekaligus menolkan `review_round:<HOP>`) dan ulangi hop. Prasyarat hop berikutnya hanya menerima `APPROVED` yang isinya masih cocok dengan `approved_seal`.
  6. **Fase 4a (kanal amandemen akar)**: bila hop menyentuh `## Success Criteria`/`## Out of Scope`, hop ditahan dan user memilih antara amandemen (diserahkan ke gerbang) atau membuang butir hilir.
  7. **Fase 5 (eskalasi)**: ada 4 pemicu. (1) `plan` LANGSUNG menemukan kontrak baru: `BRIEF → PRD_BRIEF`. (2) risk brief melampaui plafon: `BRIEF → PRD_BRIEF`. (3) sumbu bisnis ternyata aktif: `PRD_BRIEF → BRD_PRD_BRIEF`. (4) kontrak pecah: risk naik dari `MAJOR` ke `BREAKING`. Chain hanya bisa naik.
  8. **Fase 6**: tutup ledger (`doc_seal.py tick --hop BRIEF`, `@ READY <sidik12>`), lalu vonis 15 predikat A–M (TASK ACTIVE, ledger penuh, BRD/PRD APPROVED, brief READY terkunci, keterlacakan SC/AC/BR/EC, nol rujukan hantu, `BR-DISANGGAH` diputuskan, nol Open questions memblokir, Out of Scope dan plafon risk dipatuhi, asumsi mendarat di `## Objective`).
- **Subagent yang didispatch**: tidak langsung. Reviewer didispatch skill hop.
- **Output / artefak**: `### PLANNING CHAIN REPORT — READY_FOR_IMPLEMENTATION (15/15)` atau blok `NOT_READY_FOR_IMPLEMENTATION` dengan slot `Verifikasi Manual` (AC bertanda `QA manual:`).
- **Gerbang & commit**: satu-satunya penulis `status: APPROVED` BRD/PRD, lewat `doc_seal.py approve`. Ledger, re-entry, dan eskalasi ditulis ke `TASK.md` di disk. Skill ini tidak men-stage atau meng-commit apa pun, dan tidak menulis isi BRD/PRD/brief.
- **Lanjut ke**: `backend:tech-lead` (yang merutekan ke `architect` atau membuka ulang `PLANNING`).

```mermaid
flowchart TD
    S["Masuk dari tech-lead"] --> R{"TASK.md ada?"}
    R -->|tidak| C1["Fase 1: vonis 2 sumbu → chain, verifikasi pasangan risk-chain"]
    C1 --> C2["Fase 2: backend:task → TASK.md"]
    R -->|"ya, ada hop terbuka"| H
    R -->|"ya, ledger penuh"| RR{"reentry_reason?"}
    RR -->|kosong| FAILX["Berhenti — Failure path 9"]
    RR -->|terisi| OPEN["Buka hop pemilik jadi ~, bump reentry (plafon 2)"]
    OPEN --> H
    C2 --> H{"Hop teratas belum tercentang"}
    H -->|BRD| BA["business-analysis"]
    H -->|PRD| SA["system-analysis"]
    H -->|BRIEF| PL["plan"]
    BA --> ESCQ{"Pemicu eskalasi / amandemen?"}
    SA --> ESCQ
    PL --> ESCQ
    ESCQ -->|eskalasi| E5["Fase 5: transisi chain (plafon 2) → TASK.md di disk"]
    E5 --> H
    ESCQ -->|amandemen akar| A4["Fase 4a: user pilih amandemen atau buang"]
    ESCQ -->|"tidak, hop BRD/PRD"| G4["Fase 4: gerbang dokumen + approval user"]
    ESCQ -->|"tidak, hop BRIEF"| G6["Fase 6: tutup ledger + 15 predikat"]
    G4 -->|"setuju → doc_seal approve: APPROVED + centang ledger"| H
    G4 -->|"tolak (plafon 2) / OQ memblokir"| H
    G6 --> OUT["Laporan → kembali ke tech-lead"]
```

### `backend:task`

- **Pemicu / kapan dipakai**: dipanggil `backend:analyst` (Fase 2) pada lane planning, atau oleh gerbang `tech-lead` pada lane `DEFECT_RCA` dan backfill `EXEC_BRIEF`.
- **Prasyarat**: `scripts/check_preconditions.py --taskdir --lane [--chain] [--ticket-source]`, 7 check. Check "TASK.md Absence" menolak bila `TASK.md` sudah ada. Check 5 menuntut `backenddev/docs/` sudah diabaikan git dan nol berkas ter-track. Tanpa `.claude/nataflow.json`, keluarannya membawa banner `[PERINGATAN]` (JSON `peringatan`) yang disebut ke user sekali, tanpa menggagalkan vonis (24 K2). Check 7 menolak `ticket_source` yang tidak `READY` atau yang disunting sesudah approve.
- **Langkah**:
  1. **Fase 1**: serap 6 slot framing gerbang, baca `commit_convention`, petakan `evidence` ke berkas nyata, dan turunkan H1 `<Domain> — <jenis kerja>`.
  2. **Fase 2**: tulis `## Description` berisi 2–4 kalimat keputusan teknis dengan minimal satu `file:line`.
  3. **Fase 3**: tulis `## Success Criteria` `SC-{n}` (1–7 butir), masing-masing dengan alat ukur sah per lane (`PRD_CONVERSION`, `DIRECT_BRIEF`, `DEFECT_RCA`, `EXEC_BRIEF`). Bila `finding_source` terisi, satu temuan memikul tepat satu SC. Bila `ticket_source` terisi, tiap `TAC-{n}` dipikul SC atau dicatat di Out of Scope.
  4. **Fase 4**: tulis `## Out of Scope` (minimal satu butir).
  5. **Fase 5**: tulis dari `templates/task-template.md` (`status: ACTIVE`, ledger `## Chain` bila chain terisi, tabel `## Counters` kosong), jalankan `validate_doc.py --kind task --fresh`, lalu `doc_seal.py root` menulis `base_commit` = sha `HEAD` ke frontmatter.
- **Subagent yang didispatch**: tidak ada.
- **Output / artefak**: `{taskdir}/TASK.md` dan laporan `### TASK ROOT LOCKED — … · Uji Akar 9/9 lolos`.
- **Gerbang & commit**: tanpa commit. Akar dikunci `doc_seal.py root`, dan rentang kode rantai dihitung sejak `base_commit`. TASK.md tidak punya gerbang approval, dan `TASK.md` yang sudah ada tidak disentuh.
- **Lanjut ke**: `backend:analyst` (lane planning) atau `backend:tech-lead` (lane lain).

### `backend:business-analysis`

- **Pemicu / kapan dipakai**: hop `BRD` pada chain `BRD_PRD_BRIEF`, dipanggil `backend:analyst`.
- **Prasyarat**: `scripts/check_preconditions.py --taskdir --chain`, 8 check.
- **Langkah**:
  1. **Fase 0**: periksa status `BRD.md`. Kunci `## Success Criteria`/`## Out of Scope` TASK sebagai batas atas, dan petakan tiap `BR-{n}` ke minimal satu `SC-{n}`.
  2. **Fase 1**: observasi kode as-is dengan label `Observasi kode: <file:baris>`. Kuota 3 sapuan. `code-explorer` didispatch via `dispatcher/explorer.md` (maksimal 1, naik ke 2 bila lebih dari satu modul) dengan kedalaman `ringkas`.
  3. **Fase 2**: elisitasi 1–3 pertanyaan per giliran atas 6 pilar wajib (Problem, Actors, Current/Target State, Business Rules, Out of Scope) plus 2 pilar opsional. Mode serap tiket tidak menanyakan ulang isi `TICKET.md`.
  4. **Fase 3**: konfirmasi fakta sebelum menulis. Ini bukan gerbang keputusan.
  5. **Fase 4**: tulis `BRD.md` berisi 9 seksi (`status: DRAFT`), dengan `BR-{n}`/`EC-{n}`/`BM-{n}` bernomor permanen. Mode serap tiket menambah `— Asal: TBR-{m}`.
  6. **Fase 5**: jalankan `validate_doc.py --kind brd`, `chain_counters.py --bump review_round:BRD`, dan `brd-reviewer`. Balikan tiap ronde ditulis apa adanya ke `{taskdir}/.explore/review/brd.md`. Draft diserahkan hanya bila `Approved`.
- **Subagent yang didispatch**: `code-explorer` (opsional) dan `brd-reviewer` (vonis `Approved — nol temuan` | `Approved` | `Issues Found`, maksimal 2 ronde).
- **Output / artefak**: `{taskdir}/BRD.md` DRAFT, `{taskdir}/.explore/review/brd.md` (blok `## BRD Review` apa adanya, tidak di-commit), dan `### BUSINESS ANALYSIS SUMMARY` yang merujuk path berkas review itu alih-alih mencetak bloknya.
- **Gerbang & commit**: tanpa commit. Draft final di disk diserahkan hanya sesudah verdict `Approved`. Skill ini dilarang meminta approval user atau menulis `APPROVED`.
- **Lanjut ke**: `backend:analyst` Fase 4 (gerbang dokumen).

### `backend:system-analysis`

- **Pemicu / kapan dipakai**: hop `PRD` pada chain `BRD_PRD_BRIEF` (sesudah BRD APPROVED) atau `PRD_BRIEF`, dengan `risk_level` `MAJOR`/`BREAKING`.
- **Prasyarat**: `scripts/check_preconditions.py --taskdir --risk-level --chain`, 8 check.
- **Langkah**:
  1. **Fase 0**: kunci acuan hulu menurut `chain`, bukan menurut risk. Pada `BRD_PRD_BRIEF`, BRD wajib `APPROVED`. Pada `PRD_BRIEF`, BRD tidak boleh ada.
  2. **Fase 1**: pemetaan as-is sesuai `references/analysis-protocol.md` bagian A. Laporan `gate-*.md` dipanen lebih dulu, lalu `code-explorer` Profil S (`dispatcher/explorer-surface.md`) dan Profil B (`dispatcher/explorer-blast.md`) didispatch dengan kedalaman `menyeluruh`.
  3. **Fase 2**: klarifikasi 1–3 pertanyaan bila pilar belum konkret.
  4. **Fase 3**: kunci 4 pilar kontrak: API contract, status lifecycle, validation policy, dan permission & scope. Kolom `Pesan` error disalin literal dari `### Error Surface`. Pembacaan skema read-only maksimal 5 panggilan.
  5. **Fase 4**: impact map 16 dimensi dan `## Migration requirements` beserta rollback.
  6. **Fase 5**: `## Task breakdown` per unit/modul (bukan path berkas) dan `## Acceptance criteria` Given/When/Then dengan kolom `Dasar` dan `Akar`.
  7. **Fase 6**: tulis `PRD.md` DRAFT.
  8. **Fase 7**: koreksi fakta sebelum review.
  9. **Fase 8**: jalankan `validate_doc.py --kind prd`, `--bump review_round:PRD`, dan `prd-reviewer` (balikan tiap ronde ditulis apa adanya ke `{taskdir}/.explore/review/prd.md`), lalu serahkan draft.
- **Subagent yang didispatch**: `code-explorer` (Profil S/B) dan `prd-reviewer` (maksimal 2 ronde).
- **Output / artefak**: `{taskdir}/PRD.md` DRAFT, `{taskdir}/.explore/review/prd.md` (blok `## PRD Review` apa adanya, tidak di-commit), dan `### SYSTEM ANALYSIS SUMMARY` yang merujuk path berkas review itu. Slot `BR Disanggah` bila ada.
- **Gerbang & commit**: tanpa commit. Draft final di disk diserahkan hanya bila `Approved`. Bila field wajib atau transisi terekspos berubah, skill kembali ke analyst dengan pemicu eskalasi #4. Bila ada pilar bisnis yang tak terjawab, kembali dengan pemicu #3.
- **Lanjut ke**: `backend:analyst` Fase 4.

### `backend:plan`

- **Pemicu / kapan dipakai**: dipanggil `backend:analyst` dengan `entry_mode: PRD` (sesudah PRD APPROVED) atau `LANGSUNG` (chain `BRIEF`), atau dipanggil gerbang dengan `entry_mode: RCA` (RCA terkonfirmasi).
- **Prasyarat**: `scripts/check_preconditions.py --taskdir --entry-mode [--chain] [--risk] [--file-scope]`, 8 check. Check 3 menolak `entry_mode` kosong. Check 8 menolak jalur RCA tanpa `risk`/`file_scope`.
- **Langkah**:
  1. **Fase 1**: tetapkan jalur masuk dari `entry_mode` apa adanya (`references/entry-rules.md` bagian 1). Jalur `LANGSUNG` berhenti bila menyentuh salah satu dari 5 pemicu eskalasi: kontrak API, transisi status, validation policy, permission/scope, atau side-effect lintas modul.
  2. **Fase 2**: pemetaan 12 dimensi per unit (`references/slicing-and-scan.md`). Unit yang melebihi kuota didelegasikan ke fan-out `code-explorer` (≤4 serentak). Jalur non-PRD juga menjalankan sapuan 7 dimensi residual.
  3. **Fase 3**: tulis `brief-spec.json`, lalu jalankan `scaffold_brief.py --write-matrix` (atau `--append` untuk taskdir ber-brief lama) yang mengunci matriks alokasi `covers`/`fulfills`. Sesudah itu `scaffold_brief.py --nn <NN>` menulis kerangka 10 seksi: Objective, Interfaces, File scope, Out of scope, Steps, Migration, Mirrored paths, Risk & rollback, Work status, dan Analysis trace. Tiap kerangka diisi, lalu `validate_briefs.py --brief <NN>` dijalankan per brief.
  4. **Fase 4**: `validate_briefs.py` atas seluruh batch (predikat mekanis). Check A (source coverage) dan arah baliknya (kecukupan unit) dinilai main loop.
  5. **Fase 5**: `--review-state` → `--open-round` → `brief-reviewer` → `--record-round`, dengan plafon 2 ronde per generasi batch dan 4 per taskdir. Balikan tiap ronde ditulis apa adanya ke `{taskdir}/.explore/review/brief.md`. Lalu `doc_seal.py lock-briefs` (`sidik_kontrak` tiap brief `READY`) dan laporan satu baris; tabel per brief tidak dicetak karena `architect` Fase 2 menyajikannya sebelum eksekusi.
- **Subagent yang didispatch**: `code-explorer` (Fase 2) dan `brief-reviewer` (vonis `Approved`/`Issues Found`, temuan `BLOCKER [MEKANIS|SEMANTIK]` atau `ADVISORY`. Hanya `BLOCKER` yang menahan penguncian).
- **Output / artefak**: `brief-<NN>-<unit>.md` berstatus `READY`, laci `.explore/brief-matrix.md` dan `.explore/review/brief.md`, dan `### BACKEND PLAN GENERATION REPORT — <n> BRIEF READY @ <sidik batch 12 hex> … Check 15/15 · … · review <path>`.
- **Gerbang & commit**: batch dikunci `doc_seal.py lock-briefs` tanpa commit. Brief baru, brief yang di-`SUPERSEDED`, dan pencabutan `HALT.md` bila ada baris `repairs` (`doc_seal.py cabut-halt`) semuanya suntingan disk. Satu-satunya commit adalah penanda `OBSOLETE`/`DROPPED` di berkas `finding_source` (`backenddev/issues/`, dokumen repo): `docs(plan): tandai temuan <ID> untuk <slug>`. `src/` tidak disentuh sama sekali.
- **Lanjut ke**: `backend:analyst` Fase 6 (lane planning), atau `backend:tech-lead` (jalur RCA).

```mermaid
flowchart TD
    A["Prasyarat 8/8"] --> B{"entry_mode"}
    B -->|PRD| B1["Panen PRD.md APPROVED (1D)"]
    B -->|RCA| B2["Panen RCA.md: Arah perbaikan + Regression guard (1C)"]
    B -->|LANGSUNG| B3{"Kena 5 pemicu eskalasi?"}
    B3 -->|ya| ESC["Berhenti → analyst: eskalasi chain #1"]
    B3 -->|tidak| C
    B1 --> C["Fase 2: 12 dimensi + fan-out code-explorer ≤4"]
    B2 --> C
    C --> D["Fase 3.1: scaffold_brief --write-matrix (kunci alokasi)"]
    D -->|FAIL| D
    D --> E["Fase 3.2: scaffold_brief --nn NN → isi 10 seksi"]
    E --> F["validate_briefs --brief NN"]
    F -->|FAIL| E
    F -->|"brief berikutnya"| E
    F --> G["Fase 4: validate_briefs batch + Check A"]
    G -->|FAIL| E
    G --> H["Fase 5: brief-reviewer (ronde ≤2)"]
    H -->|"BLOCKER"| E
    H -->|Approved| I["doc_seal.py lock-briefs (sidik_kontrak)"]
    I --> J["Kembali ke analyst / tech-lead (RCA)"]
```

### `backend:architect`

- **Pemicu / kapan dipakai**: taskdir berisi brief READY (lane `EXEC_BRIEF`, atau sesudah analyst `READY_FOR_IMPLEMENTATION`), atau rantai terputus di tengah eksekusi.
- **Prasyarat**: `scripts/check_preconditions.py --taskdir [--base-branch]`, 7 check. Check 3 menuntut `base_commit` sah lalu memberi `entry` titik masuk, dan check 7 menolak bila `HALT.md` aktif (belum `DICABUT`).
- **Langkah**:
  1. **Fase 0**: serap profil. Baseline verifikasi dikunci ke `git merge-base <base_branch> HEAD` lewat `run_verification.py baseline` (dijalankan di worktree sementara bila HEAD ≠ merge-base) dan disimpan di `.explore/verification-baseline.json`. Working tree harus bersih, dengan pengecualian `.explore/`.
  2. **Fase 1**: traversal brief menurut `entry`. `FASE_3:<NN>` mulai dari brief READY pertama. `FASE_4` berarti `REVIEW.md` belum ada atau basi (commit kode mendarat sesudah ujung `range:`-nya). `FASE_5` berarti `REPORT.md` belum ada. `KOREKSI:<NN>:<sha7>` berarti commit unit ber-`commit_message` sudah mendarat tetapi status brief tertinggal `READY`. `TUNTAS` berarti tidak ada yang perlu dikerjakan. Brief `BLOCKED` menghentikan skill.
  3. **Fase 2**: sajikan tabel rencana (NN, unit, risk, file scope) dan kunci konfigurasi.
  4. **Fase 3 (per brief, sekuensial)**:
     1. Tulis lease dengan `guard_bash.py lease --brief`, dispatch `code-implementor` via `dispatcher/implementor.md` tepat sekali, lalu triase `DONE`/`BLOCKED` memakai matriks bukti disk.
     2. **Gerbang kompilasi**: `run_verification.py closing --cmd typecheck` (relatif baseline) bila `typecheck-per-brief: ya`. Galat baru ditulis ke `HALT.md` dengan `verdict: COMPILE`.
     3. **Pemeriksaan diff**: `git status` bersih (berkas sisa → `HALT.md STRAY`), `verify_scope.py --commit` (berkas di luar scope → `HALT.md SCOPE`, P1), dan `symbol_map.py --anchor` (simbol di luar anchor → `HALT.md SYMBOL`, P1).
     4. Berkas yatim (di luar union File scope) dicatat sebagai P1 lalu dikembalikan ke gerbang.
     5. Cabut lease dengan `lease --clear`.
  5. **Fase 4**: sesudah brief NN tertinggi DONE, jalankan `run_verification.py closing --cmd build --cmd test` sekali. Exit 1 diklasifikasi sebagai 4a (cacat eksekusi) atau 4b (cacat perencanaan / berkas yatim). Bila hijau, dispatch `code-reviewer` via `dispatcher/reviewer.md` tepat sekali.
  6. **Fase 5**: tabel eksekusi, lalu gerbang Success Criteria `TASK.md`. Bila tidak `TERTAHAN`/`BLOCKED`/P1, panggil `backend:report`. Serah-terima ke gerbang.
- **Subagent yang didispatch**: `code-implementor` (satu per brief, tidak pernah paralel) dan `code-reviewer` (satu per putaran rantai).
- **Output / artefak**: `### ARCHITECT EXECUTION REPORT — COMPLETED | COMPLETED (WARNING) | BLOCKED | TERTAHAN`, `HALT.md` bila ada, `.explore/gate-NN.md`, dan `.explore/closing-verification.md`.
- **Gerbang & commit**: architect tidak meng-commit dokumen. `HALT.md` dan koreksi status `READY → DONE` ditulis di disk. Commit susulan dilakukan hanya bila commit kode penulis terbukti gagal. Kode `src/` di-commit `code-implementor`, dan indeks `backenddev/issues/README.md` di-commit `code-reviewer`; `REVIEW.md` dan `REPORT.md` tetap di disk.
- **Lanjut ke**: `backend:report` (bila bersih), lalu `backend:tech-lead`.

```mermaid
flowchart TD
    P["Prasyarat 7/7 + baseline merge-base"] --> T{"entry check 3"}
    T -->|"FASE_3:NN"| L0
    T -->|FASE_4| V
    T -->|FASE_5| RPT
    T -->|"KOREKSI:NN:sha"| K["Koreksi status READY→DONE, jalankan ulang prasyarat"]
    T -->|TUNTAS| DONEX["Laporkan tuntas"]
    L0["Lease → code-implementor brief-NN"] --> TR{"Triase bukti disk"}
    TR -->|"BLOCKED (HENTIKAN)"| F5B["Fase 5: BLOCKED — review dilewati"]
    TR -->|DONE| CG{"Gerbang kompilasi (typecheck-per-brief)"}
    CG -->|"galat baru"| HALT["Tulis HALT.md COMPILE → hentikan"]
    CG -->|"lolos / SKIP"| VS{"git status + verify_scope + symbol_map"}
    VS -->|"sisa berkas"| HS["HALT.md STRAY"]
    VS -->|"luar scope"| HSC["HALT.md SCOPE (P1)"]
    VS -->|"simbol luar anchor"| HSY["HALT.md SYMBOL (P1)"]
    VS -->|"bersih"| NX{"Masih ada brief READY?"}
    NX -->|ya| L0
    NX -->|tidak| V["Fase 4: run_verification closing build+test"]
    V -->|"exit 1"| F4["Klasifikasi 4a eksekusi / 4b perencanaan → tech-lead"]
    V -->|"exit 0"| CR["code-reviewer → REVIEW.md"]
    CR -->|P1| RTL["Kembali ke tech-lead (PLANNING taskdir sama)"]
    CR -->|"CLEAN/P3/P2"| SCG{"Success Criteria terbukti?"}
    SCG -->|tidak| TT["TERTAHAN → tech-lead"]
    SCG -->|ya| RPT["backend:report → REPORT.md"]
    RPT --> OK["COMPLETED → tech-lead"]
```

### `backend:report`

- **Pemicu / kapan dipakai**: dipanggil `backend:architect` Fase 5 sesudah `REVIEW.md` terbit dan seluruh brief tertutup (`DONE` atau `SUPERSEDED` yang bertaut).
- **Prasyarat**: `scripts/check_preconditions.py --taskdir [--base-branch]`, 8 check: Taskdir, Root TASK.md Contract, REVIEW.md Closure Report, All Briefs Closed, Profile Commit Convention, REPORT.md Target Absence, Git Working Tree Cleanliness, dan Base Branch & Merge-Base Diff.
- **Langkah**:
  1. **Fase 0**: prasyarat, lalu baca `base_branch` dan `commit_convention`.
  2. **Fase 1**: pakai H1 `TASK.md` sebagai judul, pasangkan tiap `SC-{n}` dengan bukti, dan baca `REVIEW.md`. Severity P1 menghentikan skill.
  3. **Fase 2**: `git diff --stat $(git merge-base …)..HEAD` adalah satu-satunya sumber `## Perubahan` (2–7 butir per modul). Diff kosong menghentikan skill.
  4. **Fase 3**: `## Ringkasan` tepat satu kalimat. `## Catatan` hanya diisi dari temuan yang belum dituntaskan, penyimpangan scope, dan SC yang belum terbukti. Bila ketiganya kosong, seksi dihapus.
  5. **Fase 4**: tulis dari `templates/report-template.md` ke disk, tanpa commit.
- **Subagent yang didispatch**: tidak ada.
- **Output / artefak**: `{taskdir}/REPORT.md` dan `### REPORT LOCKED — … @ <sha>`.
- **Gerbang & commit**: tanpa commit. `REPORT.md` final di disk dan dicerminkan gerbang ke nataflow di Fase 5. Skill ini tidak menerbitkan severity atau temuan baru.
- **Lanjut ke**: `backend:architect`, lalu `backend:tech-lead`.

### `backend:debug`

- **Pemicu / kapan dipakai**: ada stacktrace, exception, HTTP 5xx, atau test merah yang penyebabnya belum diketahui (lane `DEFECT_RCA`). Taskdir dialokasikan gerbang, dan `TASK.md` ditulis `task` saat provisioning.
- **Prasyarat**: `scripts/check_preconditions.py --taskdir [--scope-hint]`, 7 check. `symptom` tidak pernah ditempel ke shell; bila perlu disimpan, ia ditulis ke `.explore/symptom.txt` via `Write`.
- **Langkah**:
  1. **Fase 0**: bila `RCA.md` sudah ada, `ROOT_CAUSE_CONFIRMED` langsung dilaporkan, sedangkan `INCONCLUSIVE` dilanjutkan dari hipotesis yang sudah gugur.
  2. **Fase 1**: normalisasi gejala memakai `## Failure signatures` adapter. Langkah reproduksi wajib dikonfirmasi user.
  3. **Fase 2**: lokalisasi permukaan kegagalan, dengan `code-explorer` via `dispatcher/explorer.md` bila lintas package.
  4. **Fase 3**: siklus hipotesis dan falsifikasi, maksimal 3. Root cause wajib punya minimal satu hipotesis alternatif yang sudah terfalsifikasi.
  5. **Fase 4**: blast radius, `## Arah perbaikan` (kandidat File scope), dan `## Regression guard` (spesifikasi test).
  6. **Fase 5**: ringkasan root cause 3–4 kalimat, lalu `AskUserQuestion` *Setujui root cause* · *Tolak (sebut arah lain)*. Disetujui → tulis `RCA.md` yang memuat rantai kausal lengkap.
- **Subagent yang didispatch**: `code-explorer` (opsional).
- **Output / artefak**: `{taskdir}/RCA.md` berstatus `ROOT_CAUSE_CONFIRMED` atau `INCONCLUSIVE`, dan `### ROOT CAUSE ANALYSIS REPORT`.
- **Gerbang & commit**: skill ini tidak meng-commit, dan `RCA.md` tidak di-commit siapa pun: ia final di disk dan dicerminkan gerbang ke nataflow. Menyentuh `src/`, membuat branch, dan menulis brief dilarang.
- **Lanjut ke**: `backend:tech-lead`. Bila `CONFIRMED`, lanjut ke `backend:plan entry_mode: RCA`. Bila `INCONCLUSIVE`, kembali ke user.

### `backend:audit`

- **Pemicu / kapan dipakai**: kode perlu disapu terhadap 6 dimensi tanpa brief (lane `AUDIT_SWEEP`). Cakupan berupa diff atau PR bukan milik skill ini, melainkan milik `code-reviewer` lewat `architect`.
- **Prasyarat**: `scripts/check_preconditions.py --target-scope [--dimensions]`, 6 check.
- **Langkah**:
  1. **Fase 0**: scoping. Baca profil, `## Audit checklist` adapter, dan `Glob` berkas target, lalu cek indeks `backenddev/issues/README.md` untuk temuan lama.
  2. **Fase 1**: peta cakupan: entry points, batas transaksi, titik mutasi data, dan egress side-effect.
  3. **Fase 2**: sapuan 6 dimensi (`security`, `transaction`, `data`, `persistence`, `concurrency`, `architecture`) ditambah invariant dan anti-pattern profil.
  4. **Fase 3**: gerbang bukti `CONFIRMED`/`PLAUSIBLE`/`DROPPED`. Kandidat tanpa bukti dibuang, tidak diturunkan ke P3. Severity mengikuti `references/findings-contract.md` bagian 1.
  5. **Fase 4**: tulis `backenddev/issues/{yyyy-mm-dd}-{NNN}-issues.md`, juga saat nol temuan, dan tambahkan satu baris di `README.md`.
  6. **Fase 5**: laporan per severity.
- **Subagent yang didispatch**: tidak ada.
- **Output / artefak**: berkas issues, baris indeks, dan `### BACKEND AUDIT SUMMARY`.
- **Gerbang & commit**: skill ini tidak meng-commit; gerbang yang meng-commit. Auditor tidak mengusulkan urutan pengerjaan dan tidak menandai `FIXED`.
- **Lanjut ke**: `backend:tech-lead`. User memilih ≤7 temuan, lalu temuan itu masuk lane `PLANNING` dengan `finding_source`.

### `backend:document-api`

- **Pemicu / kapan dipakai**: user eksplisit meminta dokumentasi API untuk endpoint yang sudah ada (lane `API_DOCS`). Mode `ON_REQUEST` atau `POST_CHAIN` (dibatasi ke diff merge-base).
- **Prasyarat**: `scripts/check_preconditions.py --domain "<domain>"`, 6 check.
- **Langkah**:
  1. **Fase 0**: resolusi mode dan kata kunci, lalu baca `## API surface` adapter.
  2. **Fase 1**: penelusuran endpoint. Himpunan kosong berarti `BLOCKED`.
  3. **Fase 2 (blocking)**: user mengonfirmasi tabel `METHOD | PATH | BERKAS:LINE`.
  4. **Fase 3**: ekstraksi kontrak per endpoint (identitas, auth, parameter, body, response, error) dengan `file:line`. Butir yang tidak bisa dipastikan ditandai `UNVERIFIED`.
  5. **Fase 4**: berkas tujuan `docs/api/<slug>.md`. Berkas yang sudah ada diperbarui secara terarah; overwrite total butuh izin eksplisit.
  6. **Fase 5**: tulis dari `references/api-doc-template.md`, termasuk contoh JSON dan cURL.
  7. **Fase 6**: verifikasi dan laporan.
- **Subagent yang didispatch**: tidak ada.
- **Output / artefak**: `docs/api/<slug>.md` dan `### API DOCUMENTATION REPORT — DOCUMENTED | PARTIAL | BLOCKED`.
- **Gerbang & commit**: skill ini tidak meng-commit. Keputusan commit milik user atau gerbang (Fase 5).
- **Lanjut ke**: `backend:tech-lead` (commit, lalu rantai selesai).

## Subagent

| Agent | Dipanggil oleh | Tools | Input | Output/vonis | Larangan |
|---|---|---|---|---|---|
| `code-explorer` | `tech-lead` (Fase 1), `business-analysis` (Fase 1), `system-analysis` (Profil S/B), `plan` (Fase 2), `debug` (Fase 2) | Read, Grep, Glob, Write | Objective, Slug, Kedalaman `ringkas`/`menyeluruh`, Berkas laporan, Format laporan, konteks, dan batas cakupan dari template `dispatcher/*.md` | Laporan `.explore/<slug>.md` berfrontmatter (`confidence`, `permukaan_diminta`, `permukaan_tertutup`, `gaps_terbuka`), isinya identik dengan balikan ke context | Mengedit kode, menjalankan git/bash, merancang solusi, berdialog; Write hanya ke satu path `Berkas laporan` |
| `code-implementor` | `architect` Fase 3 (satu per brief, sekuensial) | Read, Grep, Glob, Edit, Write, Bash | `brief_path`, `taskdir`, `unit_name`, `adapter_path` | `## Implementor Report — brief-NN-unit`: `DONE` (status brief di disk) + commit kode `commit_message`, atau `BLOCKED` + `report-NN.md` dan status di disk + commit `wip(<domain>): … [BLOCKED]` atas berkas yang sudah tersentuh | Menyentuh berkas di luar `## File scope`, men-stage brief atau dokumen taskdir, build/test, bertanya ke user, `git add .`, amend, push, reset, rantai perintah (ditegakkan hook) |
| `code-reviewer` | `architect` Fase 4 (sekali per putaran) | Read, Grep, Glob, Bash, Write | `taskdir`, `base_branch`, `adapter_path`, `findings_contract` | `REVIEW.md` di disk (`range: <merge-base>..<HEAD>`) + baris `backenddev/issues/README.md` di-commit sendiri (`docs(<slug>): add final review report`), dengan severity tertinggi `CLEAN`/`P3`/`P2`/`P1` | Mengedit `src/`, build/test, bertanya ke user. Menilai rentang `merge-base..HEAD` terhadap union File scope lewat 5 pemeriksaan: scope, koherensi lintas-brief, kelengkapan Steps, migrasi & mirrored paths, dan 6 dimensi |
| `brd-reviewer` | `business-analysis` Fase 5 via `dispatcher/reviewer.md` | Read, Grep, Glob | `taskdir`, `chain`, `ronde` | `## BRD Review`: `Approved — nol temuan` / `Approved` / `Issues Found`, ditulis pemanggil ke `.explore/review/brd.md` | Mengedit dokumen, menulis `APPROVED`, berdialog, memberi rekomendasi yang menambah aturan |
| `prd-reviewer` | `system-analysis` Fase 8 via `dispatcher/reviewer.md` | Read, Grep, Glob | `taskdir`, `chain`, `ronde` | `## PRD Review`: `Approved — nol temuan` / `Approved` / `Issues Found`, ditulis pemanggil ke `.explore/review/prd.md` | Sama dengan `brd-reviewer`; tidak boleh menuntut path berkas `src/` di breakdown |
| `brief-reviewer` | `plan` Fase 5 via `dispatcher/reviewer.md` | Read, Grep, Glob | `taskdir`, `chain`, `ronde`, `target`, `previous_report` | `## Brief Review`: `Approved`/`Issues Found`, dengan `BLOCKER [MEKANIS|SEMANTIK]` dan `ADVISORY`, ditulis pemanggil ke `.explore/review/brief.md` | Menghitung ulang predikat mekanis `validate_briefs.py`, advisory yang menambah kerja |

Semua dispatch memakai template `skills/<skill>/dispatcher/*.md` yang dihidrasi penuh. Prompt yang masih memuat slot `{...}` mentah atau tidak punya blok `Format laporan` dibatalkan.

## Hooks & Guard

**SessionStart**. `hooks.json` menjalankan `python3 hooks/detect.py --plugin backend` dengan matcher `startup|resume|clear|compact` dan timeout 5 detik.

- Hook menyuntik blok `<backend-tech-lead-gate>` sekali per sesi. Teksnya disusun `hooks/gate_text.py` dan berisi stack terdeteksi, status profil, dan aturan gerbang: permintaan apa yang WAJIB lewat `backend:tech-lead`, serta empat pengecualian.
- Hook menyala bila profil `.claude/profile/backenddev/` ada, atau bila manifest memuat penanda framework server (maksimal 200 kandidat, direktori seperti `node_modules`, `vendor`, dan `docs` dilewati). Di tempat lain hook diam.
- Status profil yang dilaporkan: ADA; lokasi lama → MIGRATE; absen atau milik plugin lain → tetap lewat gerbang dan GENERATE ditawarkan; JSON rusak, tanpa stack, field `plugin` asing pada profil sendiri, atau tidak lengkap → REFRESH. Pola workspace `.`/kosong dan manifest yang tak terbaca tidak menghentikan deteksi.
- `detect.py` identik byte-per-byte dengan milik `frontend` dan diimpor `precondition_lib.py`, sehingga vonis hook sama dengan vonis skrip prasyarat.
- Berkas `.claude/workflow` yang tidak memuat `backend` membuat hook diam (opt-out). Nama plugin dipisah spasi, koma, atau baris; berkas kosong berarti tidak ada plugin yang boleh.
- **Root multi-repo** (21 F1): bila cwd bukan repo git dan punya ≥ 2 anak langsung ber-`.git` (mis. `wms/api`, `wms/frontend`), hook tidak menggerbangi. Bloknya hanya menyebut repo backend di antara anak itu (dari profil atau manifest) beserta `/fullstack:explore`, karena skrip prasyarat skill backend butuh repo git. Sejak 23 L5 penunjuk itu mencakup semua pemahaman kode repo anak dari root (peta, alur di dalam satu repo, jahitan lintas repo) dan menyebut bahwa subagent `Explore`/`general-purpose` bawaan tidak dipakai. Root tanpa anak backend diam. Root multi-proyek (`company/<proyek>/<repo>`) di luar jangkauan deteksi dan tetap diam.

**PreToolUse**. `hooks.json` menjalankan `python3 hooks/guard_bash.py hook` dengan matcher `Bash|Edit|Write` dan timeout 10 detik. Hook hanya berlaku bila input membawa `agent_type` salah satu dari tiga subagent; panggilan lain lolos (exit 0).

| Subagent | Yang diizinkan | Alasan |
|---|---|---|
| `backend:code-implementor` | Git read-only (`status`, `diff`, `log`, `show`, `rev-parse`, `ls-files`), `git add <path lease>` tanpa flag, `git commit -m`. Edit/Write hanya ke path lease. Karakter meta (`;&|<>` backtick, `$(`, `${`) dan glob (`*?[`) sebelum `--` ditolak | Lease ditulis `architect` (`guard_bash.py lease --brief`) ke `<git-dir>/nataflow/lease-backend.json`, di luar working tree. Isinya File scope brief, berkas brief, `report-NN.md`, dan `finding_source`. Brief dan `report-NN.md` hanya untuk Edit/Write: keduanya diabaikan git dan tidak di-stage. Tanpa lease, semua Bash/Edit/Write ditolak. Bersifat fail-closed: galat internal pun menolak (exit 2) |
| `backend:code-explorer` | Edit/Write hanya ke `backenddev/docs/[<taskdir>/].explore/*.md` | Explorer hanya boleh menulis laporannya sendiri |
| `backend:code-reviewer` | Git read-only ditambah `merge-base` dan `symbolic-ref` bentuk baca (tanpa `-d`/`--delete`/`-m`, ≤ 1 argumen posisi), `ls`, serta `git add`/`git commit -m` dan Edit/Write hanya atas `<taskdir>/REVIEW.md` dan `backenddev/issues/README.md`. Yang ter-commit hanya indeks, karena `REVIEW.md` diabaikan git | Reviewer read-only atas repo kecuali laporannya. `reset`, `checkout`, `push`, build, dan test ditolak |

## Artefak & Siklus Status

**Lokasi artefak di repo pengguna** (README):

```
.claude/profile/backenddev/        index.json + stack.md, module-structure.md, domain-map.md, surface-map.md,
                                   code-conventions.md, anti-patterns.md, invariants.md, commands.md
backenddev/
  docs/                            seluruhnya diabaikan git (Langkah 24)
    .gitignore                     penanda berisi * tulisan docs_git.py, ikut mengabaikan dirinya
    .explore/<slug>.md             laci dispatch gerbang
    <YYMMDDhhmm>-<slug>/           taskdir
      TASK.md  BRD.md  PRD.md  RCA.md
      brief-NN-<unit>.md           READY → DONE | BLOCKED | SUPERSEDED
      report-NN.md                 laporan brief yang gagal (BLOCKED)
      HALT.md                      verdict COMPILE | SCOPE | SYMBOL | STRAY; status DICABUT bila dicabut
      REVIEW.md  REPORT.md
      .explore/                    scratch skill hilir: gate-*.md, brief-spec.json, brief-matrix.md,
                                   verification-baseline.json, closing-verification.md, counters-log.json,
                                   review/<brd|prd|brief>.md (balikan reviewer ronde terakhir)
  issues/                          ter-commit
    README.md                      indeks temuan audit dan review
    <yyyy-mm-dd>-<NNN>-issues.md
docs/api/<slug>.md                 ter-commit
```

**Cermin nataflow (opsional, `.claude/nataflow.json`)**: satu taskdir = satu workdir `backenddev:<repo>:<path taskdir>` yang tertaut ke task tiket analyst (`ticket_source`) atau task baru dari `TASK.md`. Isi dokumen taskdir dibaca dari disk (metadata `commit` kosong, `head` = `HEAD` saat sinkron): `TASK.md` berakar terkunci (`base_commit`), `BRD.md`/`PRD.md` `APPROVED` dengan materai utuh, brief yang sudah dikunci (`sidik_kontrak`) semua status, `RCA.md`, `report-NN.md`, `HALT.md` (termasuk yang dicabut), `REVIEW.md`, dan `REPORT.md`. `.explore/` tidak pernah ikut. Dokumen yang pernah tercermin tetap diperbarui selama berkasnya masih di disk; yang hilang dari disk tidak didorong dan dibiarkan dengan isi terakhirnya di server (24 G5). Tanpa config, dokumen taskdir hanya ada di disk ini (24 K2). Status workdir: `REPORT.md` → `done`, `HALT.md` yang belum dicabut atau brief `BLOCKED` → `blocked`, selain itu `active`. Task naik ke `in_progress` sejak ada jejak eksekusi; task milik taskdir menjadi `done` saat `REPORT.md` terbit, task tiket tidak ditutup dari sini. `backenddev/issues/`, `docs/api/`, dan profil (ter-commit, isi `HEAD`) menjadi dokumen workspace ber-key `<repo>/<path>`; yang dihapus dari git ditandai `removed: true`.

| Artefak | Penulis | Status / isi kunci |
|---|---|---|
| `TASK.md` | `task` (`doc_seal.py root`). Ledger dan eskalasi oleh `analyst`, amandemen dan backfill oleh `tech-lead` | `status: ACTIVE`, `base_commit`, `chain`, `lane` (`PRD_CONVERSION`/`DIRECT_BRIEF`/`DEFECT_RCA`/`EXEC_BRIEF`), `risk`, `## Chain`, `## Description`, `## Success Criteria` (`SC-{n}`), `## Out of Scope`, `## Counters` |
| `BRD.md` | `business-analysis`. `APPROVED` ditulis `analyst` (`doc_seal.py approve`) | `DRAFT` → `APPROVED` + `approved_seal`. 9 seksi, `BR-{n}`/`EC-{n}`/`BM-{n}` |
| `PRD.md` | `system-analysis`. `APPROVED` ditulis `analyst` (`doc_seal.py approve`) | `DRAFT` → `APPROVED` + `approved_seal`. 9 seksi, 4 pilar kontrak, impact map 16 dimensi, `AC-{n}` |
| `brief-NN-<unit>.md` | `plan` (`scaffold_brief.py`, `sidik_kontrak` oleh `doc_seal.py lock-briefs`). Status `DONE`/`BLOCKED` ditulis `code-implementor` di disk | `READY`/`DONE`/`BLOCKED`/`SUPERSEDED`. 10 seksi, `Covers:`/`Fulfills:`, `commit_message`, `sidik_kontrak` |
| `report-NN.md` | `code-implementor` (jalur gagal) | Stop condition, bukti, dan akar masalah |
| `RCA.md` | `debug` | `ROOT_CAUSE_CONFIRMED` / `INCONCLUSIVE` |
| `HALT.md` | `architect`. Dicabut `plan` (baris `repairs`) atau `tech-lead` (scope diterima) lewat `doc_seal.py cabut-halt` | `verdict: COMPILE / SCOPE / SYMBOL / STRAY`. Menahan tiap sesi lewat check 7 architect sampai `status: DICABUT`; berkasnya tidak dihapus |
| `REVIEW.md` | `code-reviewer` | Severity tertinggi `CLEAN`/`P3`/`P2`/`P1`, `range: <merge-base>..<HEAD>`. Dianggap basi bila commit kode mendarat sesudah ujung `range:` |
| `REPORT.md` | `report` | Ringkasan, Perubahan, Catatan. Menandai taskdir tuntas bersama `REVIEW.md` |
| `backenddev/issues/*.md` | `audit`. Baris `> Status: FIXED` ditulis `code-implementor` | Temuan tanpa penanda / `DEFERRED` / `FIXED` / `DROPPED` / `OBSOLETE` |
| `docs/api/<slug>.md` | `document-api` | `DOCUMENTED` / `PARTIAL` (ada `UNVERIFIED`) |

**Siklus status brief** (`skills/architect/references/lifecycle-recovery.md` bagian 1, `skills/_common/brief_status.py`):

```mermaid
stateDiagram-v2
    [*] --> READY : plan scaffold_brief nn
    READY --> DONE : code-implementor, status di disk + commit kode unit
    READY --> DONE : architect koreksi di disk, commit unit ada tapi status tertinggal
    READY --> BLOCKED : code-implementor kena stop condition
    READY --> SUPERSEDED : plan terbit ulang brief hilir
    BLOCKED --> SUPERSEDED : plan brief pengganti ber-supersedes
    DONE --> [*]
    SUPERSEDED --> [*]
```

Bukti `DONE` (24 K7): status `DONE` di disk ditambah commit bersubjek `commit_message` brief di `base_commit..HEAD` yang membawa kode. `DONE` yang ditulis tangan tanpa commit itu ditolak check 3 architect. Brief `DONE` tidak pernah dibuka ulang. Kerja susulan menjadi brief tambahan dengan NN berikutnya, dan brief `DONE` yang ditahan `HALT.md` diperbaiki lewat baris `repairs`. `DEFERRED` bukan status brief: penundaan menghentikan rantai di brief itu, dan statusnya tetap `READY`.

**Siklus status dokumen BRD/PRD dan ledger hop** (`skills/analyst/references/chain-rules.md` bagian 2–4):

```mermaid
stateDiagram-v2
    [*] --> DRAFT : penulis hop menulis, reviewer Approved, draft diserahkan
    DRAFT --> DRAFT : user tolak atau Open questions memblokir, hop diulang
    DRAFT --> APPROVED : analyst Fase 4, user setuju, doc_seal approve
    APPROVED --> APPROVED : hop dibuka re-entry, revisi terbit, gerbang dokumen berjalan ulang
    APPROVED --> [*]
```

Ledger `## Chain` di `TASK.md` berjalan `- [ ]` → `- [x] … @ APPROVED <sidik12>` (BRD/PRD, `doc_seal.py approve`) atau `- [x] BRIEF … @ READY <sidik12>` (`doc_seal.py tick`). Pada re-entry, hop ditandai `- [~] … @ re-entry <n> (was <sidik lama>)`, dan hop di bawahnya kembali `[ ]`.

**Matriks penguncian** (README § Branch dan Commit, `skills/tech-lead/references/gate-scope.md` bagian 3). Dokumen taskdir tidak pernah di-commit; yang di-commit hanya kode dan artefak tingkat repo:

| Pemilik | Yang di-commit | Yang dikunci di disk (tanpa commit) |
|---|---|---|
| `tech-lead` | Profil + `.gitignore` (`docs: init/refresh/migrate backend profile`), laporan audit (`docs(audit): record findings for <target>`), `docs/api/`, migrasi sekali jalan (`chore: lepas backenddev/docs dari git`, lewat `docs_git.py migrate`) | Amandemen akar `TASK.md` (`base_commit` tetap), pencabutan `HALT.md` (`doc_seal.py cabut-halt`) |
| `task` | — | Akar `TASK.md` (`doc_seal.py root`) |
| `business-analysis` / `system-analysis` | — | Draft BRD/PRD final sesudah reviewer `Approved`, tanpa materai |
| `analyst` | — | Approval BRD/PRD (`doc_seal.py approve`), tutup ledger (`doc_seal.py tick`), re-entry dan eskalasi di `TASK.md` |
| `plan` | Penanda `OBSOLETE`/`DROPPED` di `finding_source` (`docs(plan): tandai temuan <ID> untuk <slug>`) | Batch brief (`doc_seal.py lock-briefs`) |
| `code-implementor` | `src/**` (+ `finding_source` bertanda `FIXED`), dengan `commit_message` brief, atau `wip(<domain>): brief-NN-<unit> [BLOCKED]` | Status brief, `report-NN.md` |
| `architect` | — | `HALT.md`, koreksi status `READY → DONE` |
| `code-reviewer` | Baris indeks `backenddev/issues/README.md` (`docs(<slug>): add final review report`) | `REVIEW.md` |
| `report` | — | `REPORT.md` |
| `debug` | — | `RCA.md` |

`audit` dan `document-api` tidak meng-commit sendiri; gerbang yang meng-commit hasilnya. Staging selalu memakai path eksplisit. `git add .`/`-A` dan `git add -f` atas path di bawah `backenddev/docs/` dilarang.

## Handoff Lintas Plugin

- **Dari plugin `analyst`**. Tiket `READY` diserahkan ke `/backend:tech-lead` lewat parameter `ticket_source`, berupa path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md` (`skills/tech-lead/references/gate-scope.md` bagian 4 B-2).
  - Path tidak pernah disimpulkan dari isi `request`. Bila user menempel kartu tanpa path, gerbang menanyakannya.
  - Jalurnya: gerbang → `backend:analyst` (slot `Ticket Source`) → `backend:task`, yang memastikan tiap `TAC-{n}` dipikul `SC-{n}` atau dicatat di `## Out of Scope` (`validate_doc.py` T10). Bila sumbu bisnis tetap aktif, jalur berlanjut ke `business-analysis` dalam mode serap tiket, yang menambah `— Asal: TBR-{m}`.
  - Namespace kartu `AC-{n}`/`BR-{n}` dirujuk sebagai `TAC-{n}`/`TBR-{n}` di artefak backend supaya tidak bertabrakan dengan `AC` milik PRD dan `BR` milik BRD.
  - Tiket `type: TECH` (kartu teknis lead engineer): `D-{n}`/`C-{n}` dirujuk `TD-{n}`/`TC-{n}` dan dihitung disepakati, BRD tidak dijadwalkan (`analyst/references/chain-rules.md` bagian 1.1), dan bukti `path:baris` kartu menjadi titik awal Fase 1, bukan kebenaran final (`tech-lead/references/gate-scope.md` B-2 butir 6).
  - Syarat tiket: frontmatter `status: READY` dan `elicitation: CLOSED`, dan isi berkas sama dengan `approved_seal`. Tiket lama tanpa segel dinilai dari commit terakhir berkas itu, yang harus bersubjek `docs(ticket): kunci TICKET <slug> READY` atau `docs(ticket): ref TICKET <slug>`, dengan berkas bersih. Syarat ini dinilai prasyarat `task` check 7. Bila gagal, tiket dikembalikan ke `analyst:spec`.
  - Skill `backend:analyst` berbeda dari plugin `analyst`.
- **Cermin nataflow**: taskdir bertiket menempel ke task yang sama dengan tiket analyst (metadata `ticket_key` = direktori `ticket_source`), sehingga taskdir backend dan frontend dari satu tiket bernaung di satu task. Config `.claude/nataflow.json` dibaca bersama keempat plugin.
- **`frontend`**: profil terpisah (`.claude/profile/frontenddev/` vs `.claude/profile/backenddev/`). Di repo fullstack, kedua hook menyala dengan deteksinya masing-masing. Deteksi backend hanya membaca `dependencies` server.
- **`quickdev`**: permintaan `/quickdev:*` dilewati gerbang. Repo yang sepenuhnya memakai quickdev menulis `.claude/workflow`.
- **`.claude/workflow`**: berkas teks berisi daftar plugin yang boleh menggerbangi repo (dipisah spasi, koma, atau baris). Bila berkas ada dan tidak memuat `backend`, hook SessionStart backend diam.

## Titik Gagal & Pemulihan

| Kondisi | Penahan | Pemulihan |
|---|---|---|
| Profil absen, rusak, lama, atau tanpa `stack` | `tech-lead` Fase 0, prasyarat semua skill | Lane `PROFILE` (GENERATE/REFRESH/MIGRATE), lalu rute tertunda dilanjutkan |
| Tree kotor di luar zona artefak/`.explore/`, HEAD detached, `base_branch` kosong | Prasyarat penuh `tech-lead`, prasyarat `architect`/`report` | User stash/commit atau checkout `base_branch`. Gerbang tidak menebak branch |
| Berkas `backenddev/docs/` masih ter-track (repo era git) | Prasyarat penuh `tech-lead` check 3 (`MIGRASI`), prasyarat `task` check 5 | `gate-lifecycle.md` bagian 0: `docs_git.py status`, `AskUserQuestion`, lalu `docs_git.py migrate --answer -` (ditambah `--terima-terbuka` bila user menerima taskdir era git yang masih terbuka tidak dilanjutkan). Commit migrasi hanya berisi penghapusan dari index; berkas tetap di disk |
| `TASK.md` tanpa `base_commit` sah (akar belum terkunci, taskdir era git, atau `base_commit` bukan leluhur `HEAD`) | Check 3 architect, `doc_seal.py status`, `sync_payload.py` | Akar baru: `doc_seal.py root`. Taskdir era git tidak dilanjutkan; kerja baru membuka taskdir baru |
| Balikan explorer `confidence: low` atau rusak | Skill pendispatch | Pertajam objective, ulangi sekali, lalu sapuan manual yang dicatat. Temuan tidak dikarang |
| `validate_doc.py` / `validate_briefs.py` FAIL | Penulis dokumen | Perbaiki seluruh pelanggaran dari satu keluaran, lalu jalankan sekali lagi |
| Reviewer `Issues Found` / `BLOCKER` | `business-analysis`, `system-analysis`, `plan` | Revisi, lalu ronde berikutnya (plafon 2 ronde; brief juga 4 per taskdir). Bila plafon habis, artefak diserahkan tanpa penguncian dan ditandai tidak tuntas |
| User menolak BRD/PRD dua kali, OQ memblokir 3 kali, amandemen/re-entry/transisi chain ke-3 | `chain_counters.py` di `## Counters` `TASK.md` | Rantai berhenti, lalu gerbang mengklasifikasi ulang permintaan dari awal (`analyst` Failure path 4, 5, 7, 8, 9) |
| `NOT_READY_FOR_IMPLEMENTATION` | `analyst` Fase 6 | `tech-lead` membuka ulang `PLANNING` pada taskdir sama dengan `reentry_reason` berisi predikat gagal |
| `plan` LANGSUNG / RCA menyentuh pemicu eskalasi | `plan` Fase 1 (`entry-rules.md` 1A/1C) | LANGSUNG: eskalasi chain #1 di analyst. RCA: user memilih naik ke PRD lewat amandemen akar |
| Brief `BLOCKED` | Implementor (`report-NN.md`), matriks bukti disk architect | Rantai berhenti tanpa review. `PLANNING` pada taskdir sama, lalu `plan` menulis pengganti ber-`supersedes` |
| `HALT.md` COMPILE/STRAY | Gerbang kompilasi / `git status` architect | `PLANNING` pada taskdir sama, lalu `plan` menulis baris `repairs` dan mencabut `HALT.md` lewat `doc_seal.py cabut-halt` |
| `HALT.md` SCOPE/SYMBOL (termasuk kontrak brief yang disunting sesudah `sidik_kontrak`) | `verify_scope.py`, `symbol_map.py` | Gerbang bertanya ke user: bila diterima, `doc_seal.py cabut-halt` lalu architect lagi. Bila tidak, user me-reset lalu `PLANNING` |
| Isi `BRD.md`/`PRD.md` berubah sesudah approve (`approved_seal` tidak cocok) | Prasyarat `system-analysis`/`plan` | Re-entry membuka hop itu, lalu gerbang dokumen Fase 4 berjalan lagi. Materai tidak ditulis tangan |
| Verifikasi penutup merah | `run_verification.py closing` exit 1 | 4a cacat eksekusi: `DEFECT_RCA` atau brief perbaikan. 4b cacat perencanaan / berkas yatim: `PLANNING` re-entry, lalu `scaffold_brief.py --append` |
| `REVIEW.md` P1 | `code-reviewer` | Tidak diperbaiki di architect. `PLANNING` pada taskdir sama dengan `finding_source` = `REVIEW.md`. Dihitung ke plafon re-entry |
| `REVIEW.md` basi (commit kode mendarat sesudah ujung `range:`-nya) | Check 3 architect (`entry: FASE_4`), check 3 report | Putaran baru: verifikasi penutup, lalu satu review baru |
| Sesi putus di tengah rantai | `tech-lead` Fase 3 (tabel pemakaian ulang taskdir), `architect` Fase 1 `entry` | Brief READY → architect. Dokumen DRAFT → analyst. BLOCKED/HALT → PLANNING. `REPORT.md` belum ada → `FASE_5`. Taskdir baru hanya dibuat bila semua brief DONE/SUPERSEDED **dan** `REPORT.md` sudah terbit |
| Commit kode atau indeks gagal | Penulis melaporkan `SKIPPED`/`GAGAL` | Architect/gerbang meng-commit susulan dengan format pesan penulisnya dan mencatat penyimpangan. `--no-gpg-sign` dilarang |
| Materai gagal (`doc_seal.py` keluar bukan nol) | Penulis materai (`task`, `analyst`, `plan`, gerbang) | Berkas dipertahankan di disk beserta status jujurnya, keluaran skrip diserahkan ke gerbang. Materai, `status: APPROVED`, dan centang ledger tidak ditulis tangan |
| Disk kerja hilang | — | Rantai yang sedang berjalan ikut hilang (DRAFT dan `.explore/` tidak dicerminkan). Dokumen stabil tetap ada di nataflow; tidak ada fitur tarik balik |
| Worktree baseline tertinggal | `architect` Failure path 10 | `git worktree prune` sebelum mengukur ulang |
| `.claude/nataflow.json` rusak, server MCP mati, tool galat, sha ditolak, atau task beridentitas sama lebih dari satu | Prosedur `nataflow-sync.md` (main loop) | Segmen `GAGAL: <sebab>` di slot **Nataflow**; rantai tetap lanjut. Perbaiki sebabnya lalu `/backend:tech-lead` "sinkron ulang taskdir <slug>" |

Keterbatasan yang diketahui (README, Langkah 24): materai bukan bukti keaslian, karena model di runtime yang sama bisa menulis ulang materai dan dokumennya, dan yang dijamin hanyalah suntingan di luar skrip terdeteksi sebagai drift; tanpa `.claude/nataflow.json` dokumen taskdir hanya ada di disk lokal; filter `.explore` di gerbang git terlalu longgar; merge/rebase yang menggantung belum dideteksi; `commit_message` brief belum menghormati konvensi tiket profil; pola laci `.explore/*.md` ditegakkan hook, tetapi kewajiban menulis persis ke path `Berkas laporan` hanya ditegakkan lewat prompt; hook tidak jalan di Windows yang tidak punya `python3`.
