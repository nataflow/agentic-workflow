---
name: tech-lead
description: Gunakan ketika ada permintaan kerja baru atau susulan di repo backend - routing lane, risk level, dan taskdir diputuskan dari kode, sebelum brief ditulis atau file src/ diedit
---

## THE IRON LAW

- Lewatkan setiap permintaan kerja baru melalui gerbang ini sebelum kode di `src/` disentuh.
- Tetapkan rute dan risk level, lalu jalankan langkah pertama di giliran yang sama.
- Dilarang membuat, mengedit, atau menghapus berkas kode secara langsung.
- Buktikan setiap keputusan rute dari kode aktual; **isi prompt** tiap dispatch gerbang bersumber dari `dispatcher/explorer.md` terhidrasi penuh, tidak pernah dari prompt yang disusun sendiri.
- Inisialisasi taskdir dan branch sebelum delegasi ke hilir.

## Precondition [REQUIRED]

1. Fase 0 (tiap permintaan): `python3 ${CLAUDE_PLUGIN_ROOT}/skills/tech-lead/scripts/check_preconditions.py --read-only`. `FAIL` di sini berarti repo tak terbaca (bukan git, `index.json` rusak) → hentikan dan laporkan.
2. Fase 3 butir 0 (lane `PLANNING`, `DEFECT_RCA`, `EXEC_BRIEF`, `AUDIT_SWEEP`, `API_DOCS`): skrip yang sama tanpa `--read-only`, ditambah `--re-entry` bila masuk lewat Fase 5. `PASS` (6/6) → lanjut. `FAIL` → remediasi: profil (`commands.md`, `base_branch`) bermasalah → rute `PROFILE`; tree kotor di luar zona artefak → minta user stash/commit; HEAD detached → minta checkout `base_branch`.

## Parameter [REQUIRED]

- `request` — string — `[REQUIRED]` — Permintaan kerja baru atau susulan; kosong → tolak.
- `taskdir` — string — `[OPTIONAL]` — Taskdir eksisting `backenddev/docs/<YYMMDDhhmm>-<slug>/`.
- `base_branch` — string — `[OPTIONAL]` — Acuan pencabangan; default dari profil; keduanya kosong → hentikan.
- `strict_mode` — boolean — default `false` — Naikkan risk level 1 tingkat pada Keputusan 2 jika bernilai `true`.
- `feature_slug` — string — `[OPTIONAL]` — Slug `<domain>-<jenis-kerja>`; default 2–4 kata dari `request`.
- `ticket_source` — string — default `""` — Path `TICKET.md` `READY` analyst (`references/gate-scope.md` bagian 4 B-2); jangan ditebak dari `request`.

## Workflow

### Protokol Dispatch — Satu-satunya Jalur ke Subagent

1. **Satu titik sah**: dispatch hanya `code-explorer` di Fase 1 butir 2.
2. **Predikat pra-panggil**: muat `dispatcher/explorer.md`, hidrasi seluruh slotnya, audit hasilnya; prompt yang masih memuat slot `{...}` mentah atau tanpa blok `Format laporan` dibatalkan.
3. **Template adalah teks, bukan peluncur**: gagal dimuat → sapuan manual berkuota; jangan mengarang prompt.

### Gerbang Masuk — Evaluasi Pemicu & Pengecualian

Evaluasi setiap pesan user, termasuk susulan di tengah sesi:

1. Aktifkan gerbang untuk permintaan perubahan perilaku, bugfix, audit, eksekusi artefak, susulan cakupan, atau koreksi arah. Pertanyaan baca-kode murni (letak simbol, pemanggil, tracing) juga lewat gerbang, tetapi hanya menjalankan Fase 0 `--read-only` lalu jalur cepat `references/explore-fact.md`.
2. Jawab langsung tanpa gerbang hanya untuk 4 pengecualian: jawaban klarifikasi Fase 2 / `## Open questions`, konsep umum non-repo, operasi VCS murni atas kerja tuntas, atau alur plugin lain yang dipanggil/dilanjutkan eksplisit (`/analyst:*`, `/quickdev:*`) (`references/gate-scope.md` bagian 1).
3. Persetujuan `BRD.md`/`PRD.md` bukan pemicu: teruskan ke `backend:analyst` (`gate-scope.md` bagian 2).
4. Tahan dan proses sebagai pemicu terpisah jika permintaan baru disisipkan saat rantai berjalan, atau objek kerja berupa berkas non-`src/` berefek runtime (`references/gate-lifecycle.md` bagian 5).

### Fase 0 — Prasyarat Read-Only & Profil

1. Jalankan `check_preconditions.py --read-only`. Tree kotor, HEAD detached, izin tulis, dan `commands.md` tidak dinilai di sini — pindah ke Fase 3 butir 0.
2. Check 1 **TERDEGRADASI** (profil absen): pertanyaan baca-kode dijawab lewat `references/explore-fact.md` tanpa profil, lalu tawarkan `backend:profile`. Rute yang mengubah kode → rute `PROFILE` (Keputusan 1) lebih dulu, lalu ulangi Fase 0 dan lanjutkan rute tertunda.
3. Profil ada: baca `index.json` dan `invariants.md` di `.claude/profile/backenddev/`. Lokasi lama `.claude/profile/` → `PROFILE` mode MIGRATE lebih dulu. Profil plugin lain jangan dibaca atau ditimpa.

### Fase 1 — Eksplorasi Kode Aktual Sebelum Memutuskan Rute

1. **Kuota sapuan main loop**: maksimal 3 panggilan gabungan `Glob`+`Grep`, potongan tertarget ≤40 baris, 0 berkas dibaca penuh, 0 query database, 0 `Bash` penelusuran.
2. **Dispatch wajib**: satu pemicu mekanis `references/gate-scope.md` bagian 4E aktif → berangkatkan `code-explorer` tanpa sapuan pendahulu: hidrasi `{objective}`, `{konteks_diketahui}`, `{batas_cakupan}`, `{slug}` di `dispatcher/explorer.md` (blok `Format laporan` ikut), petakan balikan lewat `### Penanganan Balikan`-nya; gagal → `## Failure path` butir 4.
3. **Fast-path**: tanpa pemicu dispatch — satu `Glob` domain di bawah `source_root`, sisa kuota untuk `Grep` simbol.
4. **Stop condition**: enumerasi tiap permukaan yang disebut `request` — endpoint, modul, aturan, status, artefak — dan berhenti setelah masing-masing **terbukti** (`file:line`) atau **tercatat belum terbukti**. Permukaan tanpa status tidak pernah mendapat `SC-{n}` pemikul.
5. Permintaan murni pertanyaan faktual → jawab dengan format `references/explore-fact.md` bagian 3 dan selesai; dilarang membuat taskdir.

### Fase 2 — Elisitasi & Klarifikasi Terarah

Tepat 1 kali per pemicu, hanya bila tersisa ambiguitas rute atau batas modul (`references/decisions.md` bagian 2). Lewati bila Fase 1 membuktikan `file:line` tiap simbol target tanpa DTO, endpoint, atau status baru. `AskUserQuestion` 1–3 pertanyaan dengan konsekuensi teknis konkret per opsi; balasan ambigu → naikkan 1 level risiko, pilih blast radius terkecil, catat sebagai keputusan gerbang.

### Keputusan 1 — Pemilihan Jalur Kerja (Routing Lane)

Baca `references/decisions.md` bagian 6 **sebelum** memilih lane: tabel kondisi masuk, rute awal, artefak, dan presedensi `PROFILE` → `EXEC_BRIEF` → `AUDIT_SWEEP` → `DEFECT_RCA` → `PLANNING` → `API_DOCS` → `EXPLORE_FACT`. Dilarang mengarang lane baru. Lane `PLANNING` menampung seluruh kerja perancangan, termasuk perbaikan temuan; panjang rantainya diputuskan `backend:analyst`.

### Keputusan 2 — Klasifikasi Tingkat Risiko (Risk Level)

Klasifikasikan permintaan yang mengubah kode menurut `references/decisions.md` bagian 7 (tabel `BREAKING`/`MAJOR`/`MINOR`, `strict_mode`, batas wewenang) dan katalog bagian 3. Ragu di antara dua level → pilih yang lebih tinggi. `risk` diserahkan apa adanya ke `analyst`. Satu-satunya rute langsung ke `plan` di luar lane `PLANNING` adalah `RCA.md` `ROOT_CAUSE_CONFIRMED`, dengan `entry_mode: RCA` eksplisit di slot `First Action`.

### Fase 3 — Inisialisasi Direktori Kerja & Isolasi Branch

Jalankan untuk rute yang menghasilkan artefak rancangan atau kode; lewati pada lane `EXPLORE_FACT` dan `PROFILE`. `AUDIT_SWEEP` (di `base_branch`) dan `API_DOCS` (di branch aktif): butir 0 saja, tanpa branch baru (`decisions.md` bagian 5).

0. **Prasyarat penuh**: jalankan `check_preconditions.py` tanpa `--read-only` sebelum provisi apa pun. `FAIL` → `## Failure path` butir 1–2.
1. **Provisi taskdir** `backenddev/docs/<YYMMDDhhmm>-<slug>/` menurut tabel `references/gate-lifecycle.md` bagian 1 dan `references/decisions.md` bagian 4: pakai ulang taskdir yang ada; brief `BLOCKED` atau `HALT.md` → lane `PLANNING` taskdir sama dengan `reentry_reason` — kecuali taskdir **tanpa ledger `## Chain`** (rute `plan` jalur `RCA`/`debug`, bagian 1); brief `READY` → `architect`; `BRD.md`/`PRD.md` `DRAFT` → `analyst`; taskdir baru hanya untuk permintaan baru, bila seluruh brief `DONE`/`SUPERSEDED` **dan** `REPORT.md` terbit, atau lewat `## Failure path` butir 7. Salin laporan explorer ke `<taskdir>/.explore/gate-<slug>.md`.
2. **Isolasi branch**: cabangkan dari `base_branch`, bukan dari `HEAD` aktif (`references/gate-lifecycle.md` bagian 2).
   - 2a. **Akar `DEFECT_RCA`**, sesudah branch aktif: panggil `backend:task` (`chain` kosong, `risk` Keputusan 2, `evidence` Fase 1) kecuali `TASK.md` sudah ada (bagian 1a).
3. **Baseline build**: lane `PLANNING`/`EXEC_BRIEF` yang menyentuh `src/` → jalankan `build` profil sesudah branch aktif; merah → minta keputusan user; toolchain tidak tersedia → catat `tidak dijalankan` (`gate-lifecycle.md` bagian 3).

### Fase 4 — Framing Delegasi & Serah Terima

1. Sertakan framing deterministik tiap handoff: Target Skill, Taskdir, File Scope, Risk Level, Acceptance Criteria, Stop Conditions (`references/gate-scope.md` bagian 4), plus `evidence` `file:line` Fase 1, dan slot `Finding Source` (perbaikan temuan, bagian 4 B-1) atau `Ticket Source` (tiket analyst, B-2). Dilarang `File Scope` seluruh `src/` atau slot `TBD`.
2. Artefak dikunci penulisnya (`gate-scope.md` bagian 3); commit kode milik rantai `architect`.
3. Jalankan langkah pertama rute di giliran yang sama.

### Fase 5 — Re-entry Rantai: Commit Artefak & Langkah Lanjut

1. Jalankan prasyarat penuh dengan `--re-entry` (zona artefak yang boleh kotor: `references/gate-lifecycle.md` bagian 6 butir 1).
2. Commit artefak yang menunggu (profil, laporan `audit`, `RCA.md`, `docs/api/`) dengan staging path eksplisit tiap path slot `Menunggu commit` pengirim (`references/gate-scope.md` bagian 3).
3. Tentukan langkah lanjut dari tabel pengirim balik `references/gate-lifecycle.md` bagian 6 butir 3 (mis. `architect` `COMPLETED (WARNING)` = rantai selesai).
4. Perlakukan severity `P1` dari `architect` sebagai kerja lanjutan pada **taskdir yang sama**; dilarang memperbaiki di gerbang dan dilarang memprovisi taskdir baru. Klasifikasikan ulang lewat Keputusan 2, seleksi temuan lewat `references/gate-scope.md` bagian 6, lalu berangkatkan lane `PLANNING` dengan `finding_source` `{taskdir}/REVIEW.md` **dan** `reentry_reason` `REVIEW P1: <ID temuan terpilih>` (taskdir tanpa ledger: Fase 3 butir 1).
5. Skill hilir menutup `BLOCKED` atau rantai terputus → selesaikan akar masalah sesuai `## Failure path`; jangan menutupinya dengan taskdir baru.

## Guardrails

- **FASE PLANNING MILIK `analyst`**: gerbang berhenti pada provisi taskdir, branch, dan `risk`. Dilarang memanggil `task`, `business-analysis`, `system-analysis`, atau `plan` langsung pada lane `PLANNING`, dan dilarang memutuskan temuan cukup dikerjakan tanpa `PRD.md`.
- **PENCABANGAN HANYA DARI BASE BRANCH**: dilarang mencabangkan di atas branch kerja lain.
- **COMMIT ARTEFAK MILIK PENULISNYA**: gerbang meng-commit hanya artefak `profile`, `audit`, `debug`, `document-api` di Fase 5, amandemen akar `TASK.md`, dan pencabutan `HALT.md` scope yang diterima user. Dilarang commit ulang dokumen terkunci atau staging wildcard.
- **LARANGAN GIT DESTRUKTIF**: dilarang `git push`, `git merge`, `git rebase`, `gh pr create`, atau `git branch -D` tanpa otorisasi eksplisit user.
- **RATIONALIZATION PREVENTION**: dilarang menganggap perubahan field response sebagai MINOR; menutupi taskdir `BLOCKED` dengan direktori baru; mendispatch implementor tanpa `architect`; berasumsi user setuju breaking tanpa PRD; melanjutkan sapuan setelah kuota habis; atau meminta stash/commit untuk pertanyaan baca-kode.

## Output [REQUIRED]

Jalur `EXPLORE_FACT` memakai format `references/explore-fact.md` bagian 3.

```markdown
### TECH-LEAD GATEWAY DECISION
- **Lane**    : <enum lane Keputusan 1> · Risk <BREAKING | MAJOR | MINOR | tanpa risk level>
- **Taskdir** : backenddev/docs/<YYMMDDhhmm>-<slug>/ | tidak dialokasikan
- **Branch**  : <nama-branch> dari <base_branch> | tetap di <base_branch | branch aktif> · Baseline build <hijau | merah | tidak dijalankan>
- **Bukti**   : `<file:baris>` · `code-explorer` <slug> @ `backenddev/docs/.explore/<slug>.md` | fast-path <n>/3 · Permukaan <n tertutup>/<n diminta> · belum terbukti: <daftar | nihil>
- **Justifikasi Rute**: lane terpilih vs yang dikalahkan | tunggal · mitigasi blast radius
- **File Scope**: <package atau modul target terisolasi>
- **First Action**: <skill dan langkah pertama — sebut tiap parameter tanpa nilai bawaan; rute `RCA` wajib `entry_mode: RCA`>
```

Re-entry Fase 5 memakai `### TECH-LEAD RE-ENTRY DECISION` berslot **Pengirim Balik**, **Artefak Commit** (`<path> @ <sha>` | `dikunci penulisnya` | `tidak ada`), **Status Rantai** (`LANJUT` | `SELESAI` | `TERTAHAN`), dan **Langkah Lanjut**. Tutup gerbang satu baris: `Rute: <urutan-skill> | Slug: <slug> | Taskdir: <path> | Risiko: <risk>`.

## Failure path

1. **Profil hilang / tak terparsing** (prasyarat penuh): rute `PROFILE`, tunda taskdir. Dilarang menebak branch acuan.
2. **Git tak siap** (prasyarat penuh): tree kotor di luar zona artefak → minta stash/commit (artefak gerbang tidak di-stash); HEAD detached → checkout `base_branch`; branch bentrok → suffix `-v2`.
3. **Konflik taskdir**: brief `BLOCKED` di taskdir aktif → perbaiki penyebabnya (lane `PLANNING`, taskdir sama) sebelum membuat taskdir baru.
4. **Balikan explorer gagal** (`confidence: low`, payload rusak): pertajam `{objective}`, ulangi sekali, lalu sapuan manual dicatat di slot `Bukti`. Dilarang mengarang temuan.
5. **Commit hulu gagal**: commit berkasnya di gerbang dengan format pesan penulisnya, catat penyimpangan di laporan re-entry.
6. **Ambiguitas ekstrem** (3 pertanyaan tak dijawab): blast radius terkecil, naikkan `risk` satu tingkat, serahkan ke lane `PLANNING`.
7. **Rantai planning tertahan** (`analyst` bervonis `NOT_READY_FOR_IMPLEMENTATION`): selesaikan akar yang dilaporkan, lalu berangkatkan ulang lane `PLANNING` pada taskdir yang sama dengan `reentry_reason` terisi. Dilarang membuat taskdir baru atau menambal artefak rancangan sendiri. **Plafon tertembus** (`analyst` Failure path 4, 5, 7–9) → `AskUserQuestion`: **rumuskan ulang di taskdir baru** atau **hentikan** (`gate-lifecycle.md` bagian 1).

## STYLE

- Imperatif aktif, Bahasa Indonesia baku, temuan ber-`file:line`, enum persis tabel keputusan.
