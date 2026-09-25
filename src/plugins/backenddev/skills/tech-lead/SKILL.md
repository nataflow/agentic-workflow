---
name: tech-lead
description: Gunakan ketika ada permintaan kerja baru atau susulan di repo backend - routing lane, risk level, dan taskdir diputuskan dari kode, sebelum brief ditulis atau file src/ diedit
metadata:
  mode: extended
---

## THE IRON LAW

- Lewatkan setiap permintaan kerja baru melalui gerbang ini sebelum kode di `src/` disentuh.
- Tetapkan rute dan risk level, lalu jalankan langkah pertama di giliran yang sama.
- Dilarang membuat, mengedit, atau menghapus berkas kode secara langsung.
- Buktikan setiap keputusan rute dari verifikasi kode aktual, bukan asumsi prompt atau sapuan beruntun di main loop — **isi prompt** tiap dispatch gerbang wajib bersumber dari template `dispatcher/explorer.md` yang terhidrasi penuh, tidak pernah dari prompt yang disusun sendiri.
- Inisialisasi taskdir dan branch sebelum mendelegasikan pekerjaan ke downstream.

## Precondition [REQUIRED]

1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/tech-lead/scripts/check_preconditions.py [--re-entry]`; pakai `--re-entry` hanya saat masuk lewat Fase 5.
2. Evaluasi output skrip secara deterministik:
   - `PASS` (6/6 checks): Lanjutkan ke evaluasi parameter dan workflow gerbang.
   - `FAIL`: Hentikan gerbang dan jalankan tindakan remediasi pada butir yang gagal (profil belum ada → arahkan ke `backenddev:profile`; working tree kotor di luar zona artefak → minta user stash/commit; branch/commands bermasalah → selesaikan prasyarat sebelum membuka taskdir).

## Parameter [REQUIRED]

- `request` — string — `[REQUIRED]` — Permintaan kerja baru atau susulan; tolak permintaan kosong sebelum Fase 0.
- `taskdir` — string — `[OPTIONAL]` — Direktori kerja eksisting pola `backenddev/docs/<YYMMDDhhmm>-<slug>/`; diprovisi ulang di Fase 3 jika belum ada.
- `base_branch` — string — `[OPTIONAL]` — Branch acuan pencabangan; ambil dari profil jika kosong; hentikan jika keduanya kosong/`tidak terdeteksi`.
- `strict_mode` — boolean — default `false` — Naikkan risk level 1 tingkat pada Keputusan 2 jika bernilai `true`.
- `feature_slug` — string — `[OPTIONAL]` — Slug taskdir `<domain>-<jenis-kerja>` kebab-case; turunkan 2–4 kata dari `request` jika kosong.

## Workflow

### Protokol Dispatch — Satu-satunya Jalur ke Subagent

1. **Satu titik sah**: Dispatch hanya pada `code-explorer` (Fase 1 butir 2); dilarang mendispatch agent di luar titik ini.
2. **Predikat pra-panggil**: Muat template `dispatcher/explorer.md`, hidrasi seluruh slotnya, dan audit hasil hidrasinya sebelum subagent berjalan; prompt yang masih memuat slot kurung kurawal mentah dibatalkan, bukan diberangkatkan.
3. **Yang terlarang adalah prompt di luar template, bukan alat peluncurnya**: Template `dispatcher/explorer.md` berisi teks prompt; peluncurannya tetap memakai tool subagent bawaan harness — tidak ada dan tidak pernah ada jalur peluncuran lain. Yang dilarang: memberangkatkan subagent dengan prompt yang disusun sendiri, prompt yang masih memuat slot `{...}` mentah, atau prompt tanpa blok `Format laporan`-nya. Larangan ini mengikat dispatch yang dilakukan gerbang sendiri; skill hilir (`business-analysis`, `system-analysis`, `plan`, `architect`, `debug`) memakai dispatcher template masing-masing dengan aturan yang sama. Jika `dispatcher/explorer.md` gagal dimuat, hentikan gerbang, laporkan kegagalan, dan turun ke sapuan manual berkuota Fase 1 — jangan mengarang prompt penggantinya.

### Gerbang Masuk — Evaluasi Pemicu & Tiga Pengecualian

Evaluasi setiap pesan user, termasuk susulan di tengah sesi:

1. Aktifkan gerbang dan lanjut ke Fase 0 untuk permintaan pemahaman kode, perubahan perilaku, bugfix, audit, eksekusi artefak, susulan cakupan, atau koreksi arah.
2. Jawab langsung di main loop tanpa gerbang hanya untuk 4 pengecualian: jawaban klarifikasi Fase 2 / `## Open questions`, konsep umum bahasa/framework non-repo, operasi VCS murni atas kerja tuntas, atau permintaan yang memanggil/melanjutkan alur plugin lain secara eksplisit (`/analyst:*`, `/quickdev:*`, susulan di tengah skill `analyst:*`/`quickdev:*` yang sedang berjalan) (`references/gate-scope.md` bagian 1).
3. Jangan aktifkan gerbang pada persetujuan `BRD.md`/`PRD.md`: approval dokumen diminta, diproses, dan dikunci `backenddev:analyst` di dalam fase planning, dan rantai berlanjut di dalam skill itu sampai brief `READY` terbit (`references/gate-scope.md` bagian 1 dan 2). Jawaban approval user yang sampai ke main loop diteruskan ke `analyst`, bukan diproses gerbang.
4. Tahan dan proses sebagai pemicu gerbang terpisah jika permintaan baru disisipkan saat rantai berjalan, atau jika objek kerja berupa berkas non-`src/` berefek runtime (`references/gate-lifecycle.md` bagian 5).

### Fase 0 — Verifikasi Prasyarat Profil Repositori

1. Jalankan skrip `check_preconditions.py`. `FAIL` pada check 1 (profil hilang, milik plugin lain, `index.json` rusak, atau field/dokumen wajib hilang) atau check 5 (`commands.md`) → rute `PROFILE` (Keputusan 1) ke `backenddev:profile` lebih dulu; mode GENERATE / REFRESH / MIGRATE diselesaikan skrip prasyarat `backenddev:profile` sendiri. Sesudah profil tertulis dan dikunci Fase 5, ulangi Fase 0 lalu lanjutkan rute tertunda. `FAIL` lain → hentikan eksekusi dan laporkan butir yang gagal.
2. Baca `.claude/profile/backenddev/index.json` dan `.claude/profile/backenddev/invariants.md`. Check 1 `PASS` yang menyebut lokasi lama `.claude/profile/` → profil masih dibaca dari sana; rute `PROFILE` mode MIGRATE sebelum rute lain, dilarang REFRESH atau GENERATE di atasnya.
3. Profil di `.claude/profile/` milik plugin lain (mis. `frontenddev`) bukan profil backenddev: jangan dibaca sebagai profil ini, jangan ditimpa.
4. Catat invariant zona waktu, response wrapper, dan exception pattern sebagai baseline batas modul, lalu ke Fase 1.

### Fase 1 — Eksplorasi Kode Aktual Sebelum Memutuskan Rute

Delegasikan eksplorasi sebagai jalur utama; gunakan sapuan main loop hanya untuk sisa kuota ringan.

1. **Kuota Sapuan Main Loop**: Batasi maksimal 3 panggilan gabungan `Glob`+`Grep`, pembacaan berkas hanya potongan tertarget ≤40 baris, 0 berkas dibaca penuh, 0 query database, 0 `Bash` penelusuran.
2. **Dispatch Wajib**: Jika satu pemicu mekanis `references/gate-scope.md` bagian 4E aktif, berangkatkan `code-explorer` tanpa sapuan pendahulu: muat `dispatcher/explorer.md`, hidrasi slot `{objective}`, `{konteks_diketahui}`, `{batas_cakupan}`, `{slug}`, dan kirim prompt itu beserta blok `Format laporan`-nya utuh. Tangkap laporannya dari context dan petakan lewat `### Penanganan Balikan` template itu; laporan gagal → `## Failure path` butir 4.
   > Catatan: `{slug}` juga menamai berkas laporan `backenddev/docs/.explore/{slug}.md`. Kerangka seksi laporan hidup di template itu, bukan di `agents/code-explorer.md`.
3. **Sapuan Fast-Path**: Jalankan satu `Glob` domain di bawah `source_root` profil dan sisa kuota untuk `Grep` simbol jika tidak ada pemicu dispatch wajib.
4. **Stop Condition**: Enumerasi tiap permukaan yang disebut `request` — endpoint, modul, aturan, status, atau artefak — lalu hentikan eksplorasi setelah masing-masing berstatus **terbukti** (`file:line` terverifikasi) atau **tercatat belum terbukti**. Permukaan yang belum berstatus apa pun bukan permukaan yang aman: ia tidak pernah dilihat, dan yang tidak masuk `evidence` tidak akan pernah punya `SC-{n}` pemikul di hilir. Satu bukti yang menjawab satu permukaan tidak menutup permukaan lain.
5. Jawab langsung dari temuan Fase 1 dan selesaikan tugas jika permintaan murni pertanyaan faktual (letak simbol, pemanggil, tracing); dilarang membuat taskdir read-only.

### Fase 2 — Elisitasi & Klarifikasi Terarah

Jalankan tepat 1 kali per pemicu gerbang jika tersisa ambiguitas rute atau batas modul (`references/decisions.md` bagian 2).

1. Lewati Fase 2 langsung ke Keputusan 1 jika Fase 1 membuktikan `file:line` tiap simbol target dan tanpa DTO, endpoint, atau status baru.
2. Panggil `AskUserQuestion` (1–3 pertanyaan per giliran) dengan konsekuensi teknis konkret di tiap opsi bila syarat butir 1 tak terpenuhi. Dilarang menanyakan hal yang sudah terbukti di kode atau meminta izin klise.
3. Naikkan 1 level risiko, pilih opsi blast radius terkecil, dan catat sebagai keputusan gerbang jika balasan user ambigu atau tidak memilih opsi.

### Keputusan 1 — Pemilihan Jalur Kerja (Routing Lane)

Pilih satu dari tujuh jalur kanonik berdasar fakta kode terverifikasi:

| Jalur (Lane) | Kondisi Masuk | Rute Awal | Artefak |
|---|---|---|---|
| **PROFILE** | Profil tidak ada, 1 field/dokumen wajibnya hilang, `index.json` tidak sah, atau profil masih di lokasi lama `.claude/profile/` (MIGRATE) | `profile` | `.claude/profile/backenddev/` |
| **EXPLORE_FACT** | Pertanyaan faktual letak simbol/alur, tanpa mutasi | Selesai di Fase 1 | Jawaban di chat |
| **PLANNING** | Permintaan mengubah perilaku sistem dan brief `READY`-nya belum terbit | `analyst` | `TASK.md` → `BRD.md`/`PRD.md` → `brief-<NN>-<unit>.md` |
| **DEFECT_RCA** | Ada error/stacktrace/test merah, penyebab belum terbukti | `debug` | `RCA.md` |
| **EXEC_BRIEF** | Eksekusi brief `READY` di taskdir eksisting | `architect` | `REVIEW.md` |
| **AUDIT_SWEEP** | Audit kode terhadap 6 dimensi tanpa brief | `audit` | `backenddev/issues/<file>.md` |
| **API_DOCS** | Dokumentasi API diminta, endpoint sudah ada di kode | `document-api` | `docs/api/<slug>.md` |

**Presedensi Lane**: Pilih prioritas menurun jika lebih dari satu kondisi masuk terpenuhi: `PROFILE` → `EXEC_BRIEF` → `AUDIT_SWEEP` → `DEFECT_RCA` → `PLANNING` → `API_DOCS` → `EXPLORE_FACT`. Sebutkan lane yang dikalahkan beserta alasannya di slot `Justifikasi Rute`.

Lane `PLANNING` menampung seluruh kerja perancangan tanpa memilah artefaknya di sini: panjang rantai (`TASK` saja, plus `PRD`, atau plus `BRD`) adalah keputusan `backenddev:analyst` di Fase 1-nya, diturunkan dari `risk` Keputusan 2 dan kepastian kontrak yang terbukti di bukti Fase 1 gerbang. Dilarang menetapkan chain di gerbang atau memanggil `business-analysis`, `system-analysis`, `task`, maupun `plan` secara langsung pada lane ini. Gerbang memanggil `task` sendiri hanya pada lane `DEFECT_RCA` dan backfill `EXEC_BRIEF` (Fase 3 butir 1).

Perbaikan temuan terpilih dari `backenddev/issues/` dan `{taskdir}/REVIEW.md` masuk lewat lane ini juga, bukan lewat rute tersendiri: gerbang menyerahkan temuannya sebagai `request` beserta `evidence`, dan `finding_source` menandai berkas asalnya.

Dilarang mengarang lane baru; turun ke `EXPLORE_FACT` untuk kumpulkan bukti lalu evaluasi ulang tabel.

### Keputusan 2 — Klasifikasi Tingkat Risiko (Risk Level)

Klasifikasikan permintaan yang mengubah kode (lane `PROFILE` dan `EXPLORE_FACT` tanpa risk level; katalog di `references/decisions.md` bagian 3):

| Level | Pemicu ringkas |
|---|---|
| **`BREAKING`** | Kontrak eksternal berubah: endpoint/DTO eksisting, field wajib baru, transisi status terekspos, event ber-consumer, migrasi destruktif, auth |
| **`MAJOR`** | Validasi bisnis, batas transaksi, query kompleks, field opsional baru |
| **`MINOR`** | Rename lokal, refactor private, tambah test, log tracing, bugfix lokal |

1. **Prinsip Eskalasi**: Pilih level lebih tinggi jika ragu di antara dua klasifikasi.
2. **`strict_mode`**: Naikkan klasifikasi dasar 1 tingkat (`MINOR`→`MAJOR`, `MAJOR`→`BREAKING`, `BREAKING` tetap) jika bernilai `true`, jalankan rute Keputusan 1 dengan level hasilnya, dan laporkan kenaikan secara eksplisit.
3. **Batas Wewenang**: Serahkan `risk` hasil klasifikasi ini ke `backenddev:analyst` sebagai parameter. Panjang rantai perancangan dan eskalasi dinamisnya (DTO atau kolom DB baru yang muncul di tengah pengerjaan) adalah wewenang `analyst`; gerbang tidak memutuskannya dan tidak mengamandemen `TASK.md` karenanya.
4. **Satu rute langsung ke `plan`**: `plan` dipanggil gerbang hanya pada satu jalur di luar lane `PLANNING` — `RCA.md` bervonis `ROOT_CAUSE_CONFIRMED` dari `debug`. Slot `First Action` **wajib menyebut `entry_mode: RCA` eksplisit**; parameter itu tidak punya nilai bawaan dan tidak pernah disimpulkan `plan` dari artefak yang ada di taskdir, sehingga gerbang yang lupa menyebutnya membuat `plan` berhenti di check 3 prasyaratnya. Taskdir wajib sudah berakar `TASK.md` sebelum `plan` berangkat, dan jalur ini memakainya sejak provisioning `DEFECT_RCA`.
5. **Temuan bukan rute langsung**: temuan terpilih dari `backenddev/issues/` maupun `{taskdir}/REVIEW.md` dirutekan ke lane `PLANNING`, dan panjang rantainya diputuskan `backenddev:analyst` dari dua sumbu — bukan ditetapkan gerbang. Temuan yang menyentuh kontrak API, transisi status, aturan validasi, atau permission menerbitkan `PRD.md` lewat sumbu kontrak (`analyst/references/chain-rules.md` bagian 1.2 butir 1 dan 2; `risk: BREAKING` menuntutnya tanpa syarat lain), dan temuan yang membuka aturan bisnis belum disepakati menambah `BRD.md` lewat sumbu bisnis. Gerbang meneruskan `risk` hasil Keputusan 2 ini apa adanya dan berhenti di situ.

### Fase 3 — Inisialisasi Direktori Kerja & Isolasi Branch

Jalankan untuk rute yang menghasilkan artefak rancangan atau kode; lewati pada lane `EXPLORE_FACT` dan `PROFILE` (`references/gate-lifecycle.md`).

1. **Provisi Taskdir**: Tetapkan direktori `backenddev/docs/<YYMMDDhhmm>-<slug>/`; evaluasi `ls backenddev/docs/` sebelum membuat baru (`references/decisions.md` bagian 4).
   - Gunakan kembali direktori jika `taskdir` terisi dan ada di disk; dilarang membuat timestamp baru untuk pekerjaan sama.
   - Dahulukan brief perbaikan via `backenddev:analyst` jika taskdir memuat brief `BLOCKED`.
   - Rutekan ke `backenddev:architect` jika taskdir memuat brief `READY`.
   - Rutekan ke `backenddev:analyst` jika taskdir memuat `BRD.md`/`PRD.md` berstatus `DRAFT`; approval dokumen milik skill itu.
   - Buat taskdir bertimestamp baru untuk permintaan baru, atau jika seluruh brief berstatus `DONE`/`SUPERSEDED` **dan** `REPORT.md` sudah terbit. `REVIEW.md` ber-`P1` bukan rantai selesai — perbaikannya tetap di taskdir itu (Fase 5 butir 4).
   - Penulisan `TASK.md`: pada lane `PLANNING` milik `backenddev:analyst`, taskdir perbaikan temuan termasuk; gerbang berhenti pada provisi direktori. Pada lane `DEFECT_RCA`, panggil `backenddev:task` di sini — sesudah direktori ada, sebelum `debug` berangkat — dengan `lane` `DEFECT_RCA`, `chain` kosong, `risk` Keputusan 2, dan `evidence` berisi `file:line` Fase 1. Taskdir yang sudah memuat `TASK.md` dilewati (`references/gate-lifecycle.md` bagian 1a).
   - Salin laporan `code-explorer` Fase 1 ke laci taskdir begitu direktorinya ada: `mkdir -p <taskdir>/.explore && cp backenddev/docs/.explore/<slug>.md <taskdir>/.explore/gate-<slug>.md`, satu berkas per slug yang dispatch gerbang **ini** hasilkan (`references/gate-lifecycle.md` bagian 1). Tidak ada dispatch Fase 1 → lewati tanpa catatan.
2. **Isolasi Branch**: Buat branch kerja bercabang langsung dari `base_branch`, bukan dari `HEAD` aktif (`references/gate-lifecycle.md` bagian 2).
   - Hentikan gerbang segera jika `HEAD` detached, workspace bukan repositori git, atau `base_branch` bernilai `tidak terdeteksi`.
3. **Baseline Build**: Jalankan perintah `build` dari `## Commands` profil setelah branch aktif pada lane `PLANNING` atau `EXEC_BRIEF` yang menyentuh `src/`.
   - Laporkan dan minta keputusan user jika baseline build merah sebelum mutasi kode.
   - Catat `Baseline Build: tidak dijalankan` jika skrip build/toolchain tidak tersedia; jangan menggagalkan rute karenanya (`references/gate-lifecycle.md` bagian 3).

### Fase 4 — Framing Delegasi & Serah Terima

1. Sertakan framing deterministik pada tiap handoff: Target Skill, Taskdir, File Scope, Risk Level, Acceptance Criteria, Stop Conditions (`references/gate-scope.md` bagian 4). Isi slot `Risk Level` eksplisit saat menuju `analyst`, dan sertakan bukti `file:line` Fase 1 sebagai `evidence`-nya. Handoff perbaikan temuan memikul satu slot tambahan — `Finding Source`, berisi path berkas laporan beserta ID tiap temuan terpilih (`references/gate-scope.md` bagian 4 B-1) — dan slot itu absen pada handoff lain.
   - Lengkapi seluruh slot dari temuan Fase 1 atau Keputusan 1–2 jika ada slot kosong atau `TBD`. Dilarang menyerahkan `File Scope` seluruh `src/` atau `Acceptance Criteria` tanpa kriteria terukur.
2. Pastikan artefak dikunci penulisnya: `task`, `business-analysis`, `system-analysis`, dan `plan` meng-commit artefaknya sendiri, dan `analyst` mengunci commit approval `BRD.md`/`PRD.md`. Commit kode dikelola rantai `architect`.
3. Jalankan langkah pertama rute yang ditetapkan di giliran yang sama.

### Fase 5 — Re-entry Rantai: Commit Artefak & Langkah Lanjut

Jalankan tiap kali skill hilir menutup dengan instruksi `kembali ke backenddev:tech-lead`:

1. Jalankan skrip prasyarat dengan `--re-entry`; berkas kotor di zona artefak (`.claude/profile/backenddev/`, `backenddev/docs/`, `backenddev/issues/`, `docs/api/`, dan — hanya selama masa transisi MIGRATE — penghapusan berkas profil backenddev di lokasi lama `.claude/profile/<berkas>`) memang menunggu commit butir 2. Berkas di `.claude/profile/frontenddev/` atau sisa milik plugin lain di `.claude/profile/` bukan artefak gerbang ini dan tidak ikut di-stage. Identifikasi pengirim balik, baca laporan penutupnya, dan periksa status artefaknya.
2. Commit artefak yang masih menunggu: profil dari `backenddev:profile`, laporan dan indeks `backenddev/issues/` dari `audit`, serta `RCA.md` dari `debug`. Gunakan staging path eksplisit; dilarang `git add .` atau `-A` (`references/gate-scope.md` bagian 3). Stage **tiap path** yang disebut slot `Menunggu commit` laporan pengirim — pada `profile` itu termasuk `.gitignore`, yang memikul baris ignore laci `.explore/` dan `.backenddev/`. Berkas itu tertinggal di luar commit berarti ia tiba di `architect` sebagai working tree kotor, lalu berakhir jadi commit susulan tanpa brief pengklaim yang dihukum `code-reviewer` di penutup taskdir.
3. Tentukan langkah lanjut berdasarkan pengirim balik:
   - Pengirim `backenddev:profile`: Ulangi Fase 0 dan lanjutkan rute tertunda.
   - Pengirim `analyst` bervonis `READY_FOR_IMPLEMENTATION`: Rutekan ke `backenddev:architect`. Bervonis `NOT_READY_FOR_IMPLEMENTATION`: baca predikat yang gagal, selesaikan akar masalahnya lewat `## Failure path` butir 7, lalu berangkatkan ulang lane `PLANNING` pada taskdir yang sama **dengan `reentry_reason` terisi predikat yang gagal beserta ID-nya**; taskdir berledger tercentang penuh yang berangkat tanpa parameter itu tidak punya hop yang dapat dijalankan `analyst` dan berhenti seketika. Dilarang merutekan ke `architect` atas rantai bervonis itu, dan dilarang menyentuh artefak rancangannya sendiri. Menyerahkan rantai tertahan: perlakuan yang sama.
   - Pengirim `analyst` membawa **amandemen akar** yang sudah disetujui user di Fase 4a-nya (`analyst/references/chain-rules.md` bagian 5): tulis ulang butir `## Success Criteria` / `## Out of Scope` `TASK.md` sesuai rumusan yang diserahkan, jalankan ulang butir 2–6 `## Self-test Akar` `task/templates/task-template.md`, commit dengan staging path eksplisit dan subjek `docs(<slug>): amandemen akar TASK`, lalu berangkatkan ulang lane `PLANNING` pada taskdir yang sama. Ini satu-satunya titik gerbang menulis `TASK.md`; dilarang menambah, menghapus, atau menafsirkan ulang butir di luar rumusan yang diserahkan `analyst`.
   - Pengirim `debug` menyerahkan `RCA.md` `ROOT_CAUSE_CONFIRMED`: Rutekan ke `plan` lewat Keputusan 2. Jika `INCONCLUSIVE`: kembalikan ke user dengan daftar bukti tambahan; dilarang merutekan ke `plan`.
   - Pengirim `plan` jalur `RCA` menyerahkan brief `READY` ter-commit: Rutekan ke `backenddev:architect` pada taskdir yang sama. Brief belum terkunci di git atau self-review tidak tuntas: selesaikan akar masalahnya lewat `## Failure path` butir 5 lebih dulu; dilarang memberangkatkan `architect` di atas batch yang belum ter-commit. Ini satu-satunya pengirim balik `plan` yang sampai ke gerbang — lane planning pulang ke `backenddev:analyst`.
   - Pengirim `audit` menyerahkan laporan temuan: Sajikan ringkasan per severity, lalu tanyakan via `AskUserQuestion` temuan yang ditindaklanjuti — seleksi batch beserta filter statusnya mengikuti `references/gate-scope.md` bagian 6, berplafon 7 temuan per taskdir. Temuan terpilih diproses lewat Keputusan 2, lalu Fase 3 memprovisi taskdir baru dan rutekan ke lane `PLANNING` dengan `request` menyebut berkas laporan beserta ID tiap temuan terpilih, `evidence` berisi `file:line` tiap temuan itu, dan `finding_source` berisi path berkas laporannya. Dilarang menetapkan chain di sini.
   - Pengirim `architect` menutup `TERTAHAN (scope brief-NN)`: sajikan berkas atau simbol di luar scope beserta SHA-nya, tanyakan via `AskUserQuestion` apakah commit itu di-reset user atau diterima; diterima → berangkatkan ulang `backenddev:architect` pada taskdir yang sama, di-reset → klasifikasikan ulang brief itu lewat lane `PLANNING`. Dilarang menjalankan reset dari gerbang.
   - Pengirim `architect` menutup severity `P2`, `P3`, atau `CLEAN`: Nyatakan rantai selesai, sebut branch aktif dan taskdir final. Rutekan ke `backenddev:document-api` hanya jika user memintanya eksplisit.
   - Pengirim `architect` mengisi slot **`Umpan balik profil`**: tanyakan lewat `AskUserQuestion` apakah preseden itu ditandai permanen di profil. Ya → jalankan `backenddev:profile` dengan `reported_anti_patterns` berisi entri itu apa adanya, lalu commit profilnya lewat butir 2. Tidak → buang, jangan simpan sebagai catatan. Pertanyaan ini berdiri sendiri dan tidak menahan penutupan rantai. Preseden yang terbukti menyesatkan saat eksekusi tidak pernah tertangkap sapuan statis `profile`; tanpa kanal ini pengetahuannya mati bersama taskdir dan rantai berikutnya menyalin preseden yang sama.
   - Pengirim `document-api` menyerahkan `docs/api/` belum ter-commit: Commit lewat butir 2, lalu nyatakan rantai selesai.
4. Perlakukan severity `P1` dari `architect` sebagai kerja lanjutan pada **taskdir yang sama**; dilarang memperbaiki di gerbang dan dilarang memprovisi taskdir baru (Fase 3 butir 1 tidak berlaku). Klasifikasikan ulang lewat Keputusan 2, seleksi temuan lewat `references/gate-scope.md` bagian 6, lalu berangkatkan lane `PLANNING` dengan `finding_source` `{taskdir}/REVIEW.md` **dan** `reentry_reason` `REVIEW P1: <ID temuan terpilih>`.
5. Selesaikan akar masalah sesuai `## Failure path` jika skill hilir menutup `BLOCKED` atau rantai terputus; jangan membuat taskdir baru untuk menutupinya.

## Guardrails

- **FASE PLANNING MILIK `analyst`**: Gerbang berhenti pada provisi taskdir, branch, dan penetapan `risk`. Panjang rantai perancangan, penulisan `TASK.md` lane planning, approval `BRD`/`PRD`, dan eskalasi chain milik `backenddev:analyst`. Perbaikan temuan `backenddev/issues/` dan `REVIEW.md` berdiri di dalam batas yang sama: gerbang menyerahkan temuan terpilih beserta `finding_source`, dan dilarang memutuskan sendiri bahwa temuan itu cukup dikerjakan tanpa `PRD.md`. Dilarang memanggil `task`, `business-analysis`, `system-analysis`, atau `plan` langsung dari gerbang pada lane `PLANNING`; `task` dipanggil gerbang hanya di Fase 3 butir 1 dan backfill `EXEC_BRIEF`.
- **PENCABANGAN HANYA DARI BASE BRANCH**: Dilarang mencabangkan branch kerja di atas branch kerja lain; checkout ke `base_branch` terlebih dahulu.
- **COMMIT ARTEFAK MILIK PENULISNYA**: Baris `status: APPROVED` dan commit approval `BRD`/`PRD` ditulis `analyst`; commit draft dan brief milik skill penulisnya. Gerbang meng-commit hanya artefak `profile`, `audit`, `debug`, dan `document-api` yang menunggu di Fase 5. Dilarang commit ulang dokumen yang sudah terkunci atau staging wildcard.
- **DISPATCH GERBANG HANYA LEWAT TEMPLATE**: Protokol dispatch berlaku penuh di setiap dispatch oleh gerbang tanpa pengecualian ukuran tugas, dan satu-satunya **isi prompt** yang sah adalah `dispatcher/explorer.md` terhidrasi penuh. Alat peluncurnya tetap tool subagent bawaan harness — template adalah sumber teks, bukan mekanisme peluncuran, dan tidak ada jalur lain untuk memberangkatkan subagent. Dispatch milik skill hilir diatur skill itu sendiri.
- **LARANGAN GIT DESTRUKTIF**: Dilarang menjalankan `git push`, `git merge`, `git rebase`, `gh pr create`, atau `git branch -D` tanpa otorisasi eksplisit user.
- **KEPUTUSAN DEFINITIF SAAT INI**: Seluruh isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
- **RATIONALIZATION PREVENTION**: Dilarang menganggap perubahan field response sebagai MINOR; menutupi taskdir `BLOCKED` dengan direktori baru; mendispatch implementor tanpa `backenddev:architect`; berasumsi user setuju perubahan breaking tanpa PRD; melanjutkan sapuan setelah kuota Fase 1 habis; menunda inisialisasi branch hingga implementor menulis kode; atau menyusun prompt dispatch sendiri di luar template dengan dalih tugas ringan.

## Output [REQUIRED]

Gerbang menyajikan keputusan, bukan laporan penutup: blok ini tetap utuh di tiap rute karena user menyetujui rutenya di atas blok ini sebelum kerja berangkat.

```markdown
### TECH-LEAD GATEWAY DECISION
- **Lane**    : <satu lane persis seperti enum kolom pertama Keputusan 1> · Risk <BREAKING | MAJOR | MINOR | tanpa risk level>
- **Taskdir** : backenddev/docs/<YYMMDDhhmm>-<slug>/ | tidak dialokasikan
- **Branch**  : <nama-branch> dari <base_branch> | tetap di <base_branch> · Baseline build <hijau | merah | tidak dijalankan>
- **Bukti**   : `<file:baris>` dari Fase 1 · `code-explorer` <slug> @ `backenddev/docs/.explore/<slug>.md` | fast-path <n>/3 · Permukaan <n tertutup>/<n diminta> · belum terbukti: <daftar | nihil>
- **Justifikasi Rute**: lane terpilih vs lane yang dikalahkan beserta alasannya | tunggal · mitigasi blast radius · penyimpangan eksplorasi bila ada
- **File Scope**: <package atau modul target terisolasi>
- **First Action**: <Skill dan langkah pertama yang langsung dieksekusi — sebut tiap parameter tanpa nilai bawaan; pada rute `RCA` itu `entry_mode: RCA`, yang tanpanya `plan` berhenti di check 3 prasyaratnya>
```

Pada re-entry Fase 5, ganti blok itu dengan `### TECH-LEAD RE-ENTRY DECISION` berisi empat slot: **Pengirim Balik**, **Artefak Commit** (`<path> @ <sha>` | `dikunci penulisnya` | `tidak ada`), **Status Rantai** (`LANJUT` | `SELESAI` | `TERTAHAN`), dan **Langkah Lanjut**.

**Serah-terima.** Tutup gerbang satu baris: `Rute: <urutan-skill> | Slug: <slug> | Taskdir: <path> | Risiko: <risk>`.

## Failure path

1. **Profil Hilang / Tak Terparsing**: Jika profil tidak ada, atau modul, invariant, `base_branch`, dan `branch_convention` tidak terbaca atau `tidak terdeteksi` → hentikan gerbang, arahkan ke `backenddev:profile`, tunda pembuatan taskdir. Dilarang menebak branch acuan.
2. **Git Tak Siap**: Jika working tree kotor di luar zona artefak → tampilkan berkas uncommitted dan minta user stash/commit; artefak gerbang tidak pernah di-stash. Jika `HEAD` detached atau workspace bukan repo git → hentikan sebelum Fase 3, minta checkout ke `base_branch`. Jika nama branch bentrok → tambah suffix `-v2` dan konfirmasikan ke user.
3. **Konflik Taskdir**: Jika ada brief `BLOCKED` di taskdir aktif → perbaiki penyebabnya sebelum membuat taskdir baru.
4. **Balikan Explorer Gagal**: Jika `code-explorer` mengembalikan `confidence: low`, objective tak terjawab, payload kosong, atau format rusak → pertajam `{objective}` agar menyebut simbol konkret, ulangi maksimal sekali, lalu turun ke sapuan manual dan catat penyimpangannya di slot `Bukti`. Dilarang mengarang temuan.
5. **Commit Hulu Gagal**: Jika laporan hilir menyatakan commit draft atau brief gagal → commit berkas tersebut di gerbang menggunakan format pesan penulisnya, catat penyimpangan di laporan re-entry.
6. **Ambiguitas Ekstrem**: Jika 3 pertanyaan klarifikasi tidak dijawab → pilih rute dengan blast radius terkecil, naikkan `risk` satu tingkat, dan serahkan ke lane `PLANNING`.
7. **Rantai Planning Tertahan**: Jika `analyst` menutup dengan rantai tertahan atau bervonis `NOT_READY_FOR_IMPLEMENTATION` (akar gagal terkunci, hop gagal menerbitkan artefak, verdict reviewer bukan `Approved`, approval ditolak berulang, pertanyaan terbuka tak kunjung tuntas, eskalasi melampaui plafon, amandemen akar melampaui plafon, atau salah satu dari 15 predikat gerbang Fase 6 gagal) → selesaikan akar masalah yang dilaporkannya, lalu berangkatkan ulang lane `PLANNING` pada taskdir yang sama dengan `reentry_reason` terisi. Dilarang membuat taskdir baru untuk menutupinya atau menambal artefak rancangan sendiri. Plafon re-entry dua kali per taskdir dipegang `analyst` (`## Failure path` butir 9-nya); rantai yang menembusnya kembali ke gerbang untuk diklasifikasi ulang dari awal, bukan diberangkatkan ketiga kalinya.

## STYLE

- Gunakan fase bernomor dan kalimat imperatif aktif yang tegas tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku dan istilah teknis asli stack.
- Sajikan temuan berbasis predikat nyata kode (`file:line`).
- Tulis nama lane, risk level, dan status artefak persis seperti enum tabel keputusan.
