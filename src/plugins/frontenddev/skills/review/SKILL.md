---
name: review
description: Gunakan ketika kode frontend di luar rantai taskdir aktif perlu dinilai (lane REVIEW_AUDIT) - rentang commit, direktori fitur, atau taskdir yang sudah tuntas dinilai terhadap 9 dimensi dan konvensi profile, sebelum perbaikan diajukan sebagai kerja baru; review penutup taskdir aktif milik frontenddev:architect
metadata:
  mode: standard
---

## THE IRON LAW

- Read-only mutlak atas `src/`; perbaikan diajukan sebagai permintaan kerja baru lewat `frontenddev:lead`, tidak pernah ditulis di sini.
- Skill ini tidak pernah menulis `<taskdir>/REVIEW.md` dan tidak pernah menilai taskdir yang masih berjalan — itu `frontenddev:architect` + `code-reviewer`.
- Tiap temuan P1–P3 berjangkar `file:baris` dan cuplikan kode aktual; kandidat tanpa bukti dibuang, tidak diturunkan severity-nya.
- Sembilan dimensi dievaluasi lengkap terhadap profil dan `## Review checklist` adapter stack repo; dilarang menurunkan P1 (DTO bocor, side-effect di API layer).

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/check_preconditions.py --target <diff|path|taskdir> [--range A..B] [--path <p>] [--taskdir <t>] [--write]`.
2. `PASS`: lanjut. `FAIL`: hentikan dan remediasi — target di luar enum atau taskdir belum tuntas → taskdir aktif dinilai `frontenddev:architect`, bukan di sini; rentang/path tidak ada → perbaiki parameter; profil/adapter → `frontenddev:profile`; `--write` dengan tree kotor → laporkan ke user.

## Parameter [REQUIRED]

- `target` — string — `[REQUIRED]` — `diff` (rentang commit, default `HEAD~1..HEAD`), `path` (direktori fitur atau berkas), `taskdir` (taskdir yang sudah `REPORT.md`, dinilai ulang sejak akarnya).
- `range` / `path` / `taskdir` — string — pasangan `target`.
- `write` — boolean — default `false` — terbitkan temuan ke `frontenddev/reviews/` agar dapat menjadi `finding_source`.
- `run_verification` — boolean — default `false` — jalankan `commands.md` profil sebagai bukti tambahan dimensi 9; ad-hoc review tidak wajib menjalankannya.

## Workflow

### Phase 0 — Lingkup & Acuan

- Tetapkan objek: `git diff <range> --name-only`, isi `path`, atau rentang `akar..HEAD` taskdir tuntas (kecualikan `frontenddev/docs/**`, `.claude/**`).
- Baca `index.json` (`stack`), `layer-adoption.md`, `stack.md`, `invariants.md`, `drift.md` profil, lalu `## Review checklist` dan `## Failure signatures` adapter. `CONTRACT.md` taskdir tuntas dibaca bila `target: taskdir`.

### Phase 1 — Verifikasi Terminal (opsional)

`run_verification: true` → jalankan `commands.md` profil sekali, bedakan galat baru dari baseline profil, dan baca kolom **Cakupan yang TIDAK Diperiksa** sebelum menyimpulkan. Galat baru menjadi temuan P1 dimensi 9.

### Phase 2 — Sembilan Dimensi

Nilai baris yang berubah (target `diff`/`taskdir`) atau berkas di `path` terhadap `references/nine-dimensions-catalog.md` dan predikat adapter: 1 Layer Boundaries · 2 Data Flow & DTO · 3 API Layer · 4 State Scope · 5 Enam Cabang State · 6 Platform & Framework · 7 Error Handling · 8 Performance & Leaks · 9 Test Quality. Adapter menang bila keduanya menyebut butir yang sama. Katalog ini kembaran `agents/code-reviewer.md` Fase 2 — perubahan definisi menyentuh keduanya.

### Phase 3 — Triase & Severity

P1 blokir merge (DTO bocor, side-effect API layer, `any`, test tanpa assertion, galat baru, batas framework P1 adapter) · P2 peringatan arsitektur · P3 saran. Verdict: `BLOCKED` ⇔ P1 > 0; `WARNING` ⇔ P2 > 0; selain itu `PASS`. Berkas *Pola Acuan* yang memakai pola usang dicatat `<file:baris> — preseden menyesatkan — <pola> → <pengganti>`, bukan P2 biasa.

### Phase 4 — Laporan

- Tanpa `write`: sajikan laporan chat mengikuti `references/review-checklist.md` bagian 2.
- `write: true`: tulis `frontenddev/reviews/<YYMMDDhhmm>-<slug>.md` persis `templates/audit-template.md` — temuan ber-ID `P{n}-{m}` ber-`> Status: PLANNED` — lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/validate_audit.py --path <berkas>` sampai `PASS`, `git add <berkas>`, dan commit `docs(review): audit <slug>`. Sebut path-nya sebagai calon `finding_source` untuk `frontenddev:lead`.

## Guardrails

- **READ-ONLY**: satu-satunya berkas yang boleh ditulis adalah `frontenddev/reviews/<berkas>` pada `write: true`.
- **BUKTI BARIS NYATA**: tiap temuan memuat Location, Violation, Evidence, Recommendation lengkap.
- **ONE ADAPTER**: predikat stack dari `## Review checklist` adapter `stack` profil; dilarang menghakimi repo Svelte dengan rule hook React.
- **BASELINE HONESTY**: galat pre-existing dibedakan dari regresi.
- **RATIONALIZATION PREVENTION**:
  - "Sekalian saya perbaiki DTO yang bocor" — reviewer independen; perbaikan adalah kerja baru.
  - "Taskdir ini hampir selesai, saya review saja di sini" — review penutup milik `architect`; dua penulis `REVIEW.md` menghasilkan dua vonis untuk satu rantai.
  - "Temuan P2 saya hapus biar cepat" — menyembunyikan temuan menumpuk utang.
  - "Test hijau berarti tipe aman" — adapter mencatat cakupan yang tidak diperiksa test.

## Output [REQUIRED]

Tutup satu baris: `REVIEW (<target>) — <PASS | WARNING | BLOCKED> · <x> P1, <y> P2, <z> P3 · <chat | frontenddev/reviews/<berkas> @ <sha>>`. Temuan P1/P2 disertai kalimat: `Perbaikan diajukan lewat frontenddev:lead dengan finding_source <path>.`

## Failure path

1. **Rentang/path tidak resolve**: hentikan di Precondition.
2. **Perintah verifikasi macet** (>60 detik): tandai `UNVERIFIED / TIMEOUT`, lanjutkan sembilan dimensi.
3. **Diff >50 berkas**: nilai per direktori fitur, laporkan modular.
4. **Nomor baris bergeser**: lokalisasi ulang lewat `Grep` sebelum mencatat bukti.
5. **Adapter tidak ditemukan**: jalankan dimensi generik saja, tandai dimensi 6 `UNVERIFIED`, sarankan `frontenddev:profile`.

## STYLE

- Imperatif aktif; `file:baris` presisi; cuplikan minimal.
- Klasifikasi P1/P2/P3 objektif berakar sembilan dimensi; rekomendasi konkret per temuan.
