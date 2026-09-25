---
name: plan
description: Dipanggil frontenddev:lead sesudah hop CONTRACT tercentang di ledger, atau langsung pada lane HOTFIX_MINOR, atau sesudah hop BRIEF dibuka ulang - memecah kerja jadi brief READY atomik dengan rekonsiliasi 3-check, Gate Plan Review, dan approval user, sebelum kode di src ditulis tanpa brief
metadata:
  mode: standard
---

## THE IRON LAW

- Brief lahir `READY` dan tidak pernah menulis status lain; `DONE`/`BLOCKED` milik `architect`.
- Batch brief di-commit hanya sesudah `validate_briefs.py` `PASS` dan — pada lane non-MINOR — ronde `doc-reviewer` terakhir `PASS` atas konten yang sama.
- Approval breakdown hanya lewat jawaban eksplisit user di `AskUserQuestion` yang dimateraikan `chain.py approve --row BRIEF`; diam atau jawaban ambigu bukan persetujuan.
- Tiap brief memikul minimal satu `SC-{n}` (`fulfills`), 1–5 berkas non-test, test co-located, dan Done Criteria biner; test, lint, dan build tidak pernah dijalankan per brief.
- Dilarang membuat, mengubah, atau menghapus berkas di `src/` selama skill ini berjalan.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/check_preconditions.py --taskdir <taskdir> --mode <mode>`.
2. `PASS` (9/9): lanjut. `FAIL`: hentikan dan remediasi — mode tidak sesuai keadaan → pakai mode yang ditunjuk skrip; hop hulu belum tercentang atau berubah sesudah disetujui → kembali ke `frontenddev:lead`; unit `BLOCKED` tanpa `report-<NN>.md` → laporkan bukti yang hilang ke user; profil/adapter → `frontenddev:profile`; tree kotor yang menurut skrip seluruhnya artefak taskdir ini (batch tertunda sesi lalu) → lane non-MINOR: `review_round.py status --ready --gate plan` exit 0 → commit lewat `review_round.py commit` dengan subjek Phase 4 mode-nya, selain itu **jangan commit** — lanjutkan dari Phase 3 butir 2 (validator, lalu Gate Plan Review); lane MINOR → commit hanya bila `validate_briefs.py` `PASS`; lalu ulangi prasyarat; kotoran lain → laporkan ke user. `WARN` plafon revisi habis pada mode REVISE → hanya Phase 5 yang boleh, batch tidak ditulis ulang.
3. Skrip: `chain.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py`; `review_round.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/review_round.py`; `taskdir_state.py` = `${CLAUDE_PLUGIN_ROOT}/skills/lead/scripts/taskdir_state.py`.
4. Baris `Terselesaikan:` menyerahkan `unit_berikutnya`, `lane`, dan `sections` — pakai apa adanya; batas lingkup MINOR (satu berkas fitur, tanpa endpoint/DTO/alur baru) tetap penilaianmu.
5. **Approval tertunda**: batch sudah ter-commit tetapi belum disetujui (`taskdir_state.py` `GATE` mode `REVISE atau approval breakdown tertunda`) → jalankan prasyarat mode REVISE (BRIEF `[ ]`) atau APPEND (BRIEF `[~]`, commit `draft breakdown append` sudah ada), lalu langsung Phase 5 tanpa menulis ulang.
6. **Approval ulang tanpa kerja baru**: BRIEF `[~]` hasil kaskade reopen hulu atau amandemen akar, seluruh brief `DONE`/`BLOCKED` dan tidak ada brief baru yang dibutuhkan → jalankan prasyarat mode APPEND, lalu langsung Phase 5 tanpa menulis brief dan tanpa Plan Review.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — taskdir aktif.
- `mode` — string — `[REQUIRED]` — `CONTRACT` (lane non-MINOR, seri pertama), `MINOR` (lane `HOTFIX_MINOR`, seri pertama), `REVISE` (batch belum disetujui, user meminta revisi), `APPEND` (hop BRIEF dibuka ulang: brief remedi unit `BLOCKED`, brief perbaikan atas `REVIEW.md` `BLOCKED` atau verifikasi penutup merah, atau brief penampung berkas yatim sesudah kontrak dilengkapi). Tidak ada nilai bawaan.
- `max_files_per_unit` — integer — default `5` — kuota berkas non-test per brief (Check L).

## Workflow

### Phase 0 — Sumber Acuan per Mode

- **CONTRACT**: `CONTRACT.md` `APPROVED` adalah cetak biru; `# Execution` (Files Touched, Proposed Units, Acceptance Criteria) dipecah, tidak dirancang ulang.
- **MINOR**: tanpa kontrak, `TASK.md` satu-satunya sumber kriteria. Satu saja dari endpoint baru, query key baru, perubahan DTO, atau cabang state baru → hentikan; lead mengeskalasi lane lewat `chain.py escalate`.
- **REVISE**: poin penolakan user adalah masukan tunggal; brief yang tidak disebut tidak disentuh.
- **APPEND**: brief `DONE`/`BLOCKED` tidak disunting sama sekali, termasuk `total_units`-nya. Unit baru mulai dari `unit_berikutnya`; `total_units` brief baru = jumlah seluruh brief (Check N hanya menagih brief `READY`; seluruh brief terkunci → keseragaman tidak ditagih). Sumber per jenis — dilarang menyusunnya dari subjek commit atau ingatan sesi:
  - **Brief remedi** (unit `BLOCKED`) membawa `remedies: "<NN>"` dan membaca `## Triase`, `## Out of Scope / Mismatch`, dan `## Rollback` `report-<NN>.md` unit asal.
  - **Brief perbaikan** (unit asal `DONE`) tanpa `remedies`; sumbernya `P1` dan SC `belum terbukti` di `REVIEW.md`, atau galat di `.explore/closing-verification.md`, beserta `## Triase`/`## Out of Scope / Mismatch` `report-<NN>.md` unit penyentuhnya. `fulfills` = SC yang diperbaiki; `MODIFY` atas berkas yang di-`CREATE` brief hulu sah (Check R).
  - Lane `HOTFIX_MINOR`: APPEND tetap tunduk batas MINOR; endpoint, DTO, query key, atau cabang state baru → hentikan, `frontenddev:lead` mengeskalasi lane.
- **Akar di semua mode**: tiap unit memikul minimal satu `SC-{n}` `TASK.md` lewat `fulfills`; SC gugur (`~~…~~ — gugur: <alasan>`) tidak dipikul brief aktif, sedangkan brief `DONE` yang dulu memikulnya tetap sah; `## Out of Scope` adalah plafon. `findings` ber-`finding_source` sudah diverifikasi ulang `task` saat akar dikunci; temuan yang kodenya ternyata sudah berubah saat plan → hentikan, `frontenddev:lead` mengamandemen akar.
- Baca field `stack` `index.json` profil, lalu `## Layer taxonomy` dan `## Commands` adapter.

### Phase 1 — Rekonsiliasi 3-Check

1. **Kecocokan repo**: tiap path target diperiksa di source root; `CREATE` bila baru, `MODIFY` bila ada — dengan `Anchor` ekspor top-level yang boleh disentuh. Panen laci `<taskdir>/.explore/*.md` lebih dulu; dispatch `code-explorer` lewat `dispatcher/explorer.md` (`{laci}` = `<taskdir>/.explore/`) hanya untuk unit yang laporannya belum ada. **Kuota sapuan gate**: 2 `Glob`+`Grep` dan 2 read ber-offset; lintas-layer, relasi, atau simbol tak ketemu → dispatch, bukan sapuan ketiga.
2. **Kelengkapan transitif**: tiap berkas logic, view-model, service, atau API layer baru berpasangan test di `files_touched` yang sama.
3. **Baseline terminal**: jalankan perintah `commands.md` profil sekali untuk merekam galat awal; Done Criteria berbunyi "nol galat baru dibanding baseline", bukan "bersih total". Perintah typecheck persis profil (`svelte-check` di repo Svelte, bukan `tsc` saja).

### Phase 2 — Pemecahan Unit & DAG

Pecah per batas layer mengacu `references/slicing-patterns.md`: Unit 01 data & transport (DTO, service, API layer + test), Unit 02 logic (view-model, controller + test), Unit 03 presentasi. Perbaikan terisolasi: 1–2 unit. Tiap brief kompilabel mandiri sesudah mendarat (bagian 4 butir 6b) — gerbang kompilasi per-brief `architect` menagihnya. `depends_on` hanya ke nomor lebih kecil.

### Phase 3 — Tulis Brief & Gate Plan Review

1. Tulis tiap `brief-<NN>-<unit>.md` persis bagian 1 `templates/brief-template.md`: `status: READY`, `based_on` dari `git rev-parse --short HEAD`, `fulfills`, `covers` (kosong pada MINOR), `files_touched`, `verification`, dan lima seksi. Dilarang menulis langkah "jalankan typecheck/test" di seksi 4.
2. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/validate_briefs.py --taskdir <taskdir> [--brief <NN>] [--contract]` per brief lalu per batch — `--contract` pada lane non-MINOR. `FAIL` → perbaiki dan ulangi sampai `PASS`.
3. **Gate Plan Review** (lane non-MINOR): hidrasi `dispatcher/reviewer.md`, jalankan gerbang masuknya (`review_round.py open --gate plan`), dispatch `doc-reviewer` (`subagent_type`: `frontenddev:doc-reviewer`), lalu petakan balikan lewat `### Penanganan Balikan` template itu — termasuk `review_round.py record`. Plafon 2 ronde per putaran, 8 per taskdir — putaran baru dimulai sesudah batch yang lolos ronde `PASS` di-commit (Phase 4) atau sesudah `reopen` yang membuka hop BRIEF; `BLOCKED` apa pun — termasuk yang hanya ber-`BLOCKER [MEKANIS]` — → perbaiki, jalankan validator sampai `PASS`, lalu ronde 2 menyempit atas konten final; konten yang berubah sesudah ronde `PASS` juga menuntut ronde menyempit. Approval menuntut ronde terakhir `PASS` atas konten batch yang persis sama dan tidak didahului `reopen` hop BRIEF sesudah ronde itu; commit Phase 4 (`draft breakdown`, `revise breakdown`, `draft breakdown append`) tidak membatalkan ronde.

### Phase 4 — Batch Commit

Satu commit untuk seluruh brief baru/berubah beserta `REVIEW-PLAN.md` (non-MINOR). Lane non-MINOR commit lewat skrip: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/review_round.py commit --taskdir <taskdir> --gate plan --subject "<subjek tabel>"` — menolak kecuali ronde terakhir `PASS` atas batch dan laporan di disk, men-stage brief + `REVIEW-PLAN.md` sendiri, dan menambah trailer `Review-Round`. Lane MINOR (tanpa ronde): `git add` per path lalu `git commit`. `REVIEW-PLAN.md` ronde terakhir selalu ikut commit yang sama. Bila batch sudah ter-commit lebih dulu (approval tertunda, Precondition 5), commit laporannya sendirian dengan subjek `docs(<slug>): plan review ronde <n>`.

| Mode | Subjek commit |
|---|---|
| CONTRACT / MINOR | `docs(<slug>): draft breakdown (<N> briefs)` |
| REVISE | `docs(<slug>): revise breakdown` |
| APPEND | `docs(<slug>): draft breakdown append (unit <NN>..<MM>, total <N>)` |

Brief `DONE`/`BLOCKED` tidak pernah disunting, jadi tidak pernah ikut di-stage.

### Phase 5 — Approval User

1. Sajikan tabel: Unit, Nama, `files_touched`, `depends_on`, `fulfills`, `covers`, verdict Plan Review.
2. `AskUserQuestion` dengan opsi berkonsekuensi: *Setujui breakdown — lanjut eksekusi* · *Revisi (sebut poinnya)* · *Hentikan*.
3. **Setuju** → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py approve --taskdir <taskdir> --row BRIEF --answer "<jawaban user apa adanya>"`. Skrip memvonis ulang `validate_briefs.py`, `REVIEW-PLAN.md` `PASS` yang merupakan laporan ronde terakhir (bukan basi), dan ronde reviewer terakhir `PASS` atas konten final yang tidak didahului `reopen` hop BRIEF, lalu mencentang ledger dalam satu commit (badan: `Konten disetujui: <sha>` + `Hop: BRIEF`). Pada BRIEF `[~]` tanpa brief `READY` (kaskade/amandemen tanpa kerja baru) skrip hanya memvonis `validate_briefs.py` — approval ulang sah tanpa ronde Plan Review baru.
4. **Revisi** → cek sisa plafon `chain.py revisions --taskdir <taskdir> --row BRIEF` (plafon 2), lalu ulangi Phase 1–5 dengan mode `REVISE`. Plafon habis → hentikan, sajikan poin penolakan berurutan, serahkan ke `frontenddev:lead` Phase 8 (klarifikasi lingkup: amandemen akar, atau `chain.py abandon`).

## Guardrails

- **SUMBER HULU TERCENTANG**: dilarang memecah brief di atas hop hulu yang belum `[x]` atau yang kontennya berubah sesudah disetujui — prasyarat skrip menagih keduanya.
- **KUOTA & CO-LOCATION**: 1–5 berkas non-test per unit; logic baru berpasangan test di brief yang sama.
- **DONE CRITERIA BINER**: butir terminal bertanda `(verifikasi penutup)` dan relatif baseline; kalimat umum "fitur bekerja" dilarang.
- **NO PER-UNIT VERIFICATION**: dilarang menulis instruksi menjalankan typecheck, lint, test, atau build di brief mana pun.
- **ADAPTER NAMING ONLY**: path dan perintah mengikuti adapter `stack`; nama berkas stack lain adalah cacat Check K.
- **PENELUSURAN LEWAT DISPATCH**: sapuan di atas kuota didelegasikan ke `code-explorer` lewat `dispatcher/explorer.md`; dilarang menyusun prompt sendiri.
- **REMEDI BERPLAFON**: maksimal 2 brief remedi per unit asal (Check M), ditambah satu per `reopen ... CONTRACT` yang sudah terjadi; remedi ketiga tanpa re-entry kontrak dilarang — cacatnya di kontrak, rutekan `chain.py reopen --row CONTRACT` lewat lead (lane MINOR: `reopen --row BRIEF` lalu `escalate --lane FAST_FORWARD --sections architecture`).
- **BATCH COMMIT ONLY**: dilarang commit per brief; dilarang menahan commit menunggu persetujuan.
- **RATIONALIZATION PREVENTION**:
  - "Semua digabung satu brief biar cepat" — brief besar membebani implementor dan menyulitkan rollback.
  - "Test pendamping tidak perlu masuk `files_touched`" — implementor dilarang menyentuh berkas di luar daftar.
  - "Baseline ada galat, jadi saya lewati" — tanpa baseline, galat warisan tak dapat dibedakan dari regresi.
  - "Reviewer sudah PASS, saya rapikan sedikit lalu langsung minta approval" — `chain.py approve` menolak konten yang berubah sesudah ronde `PASS`.
  - "Unit ini tidak memikul SC mana pun, tapi perlu untuk kebersihan" — perluasan lingkup; Check G menolaknya.
  - "Satu grep lagi untuk memastikan path" — kuota mekanis; sapuan berikutnya milik explorer.
  - "Sekalian saya rapikan brief DONE agar selaras" — brief `DONE`/`BLOCKED` tertutup; koreksi lahir sebagai brief baru.

## Output [REQUIRED]

Breakdown disetujui — tutup satu baris: `PLAN — BRIEF @ READY <sha> · <N> brief (<n> baru) · Plan Review <PASS ronde n | dilewati (MINOR)> — lanjut ke frontenddev:architect di main loop.` Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### PLAN — <MENUNGGU REVISI | TERTAHAN>
- **Taskdir**: <taskdir> · mode <mode> · <N> brief
- **Validator**: <PASS | FAIL (<check>)>
- **Plan Review**: <verdict ronde n · <n> BLOCKER [SEMANTIK] tersisa> | dilewati (MINOR)
- **Plafon**: <revisi n/2 · ronde n/2 (taskdir n/8)> | —
- **Rute**: <revisi di plan | frontenddev:lead Phase 8 (reopen CONTRACT / escalate / amandemen akar / abandon)>
```

## Failure path

1. **Hop hulu belum sah**: hentikan di Precondition; kembali ke `frontenddev:lead` yang merutekan ke gate pemiliknya.
2. **Kegagalan rekonsiliasi path**: berkas yang diasumsikan ada tidak ditemukan → sesuaikan brief; simbol acuan hilang total → dispatch explorer; tetap tidak ada → tanyakan path riil ke user.
3. **Baseline terminal crash** (env belum siap): catat galat mentah, tandai baseline `UNVERIFIED_ENV_NOT_READY`, Done Criteria menyebut keadaan itu apa adanya.
4. **Batch commit gagal** (hook, lock): perbaiki penyebabnya dan ulangi commit yang sama sebelum approval diajukan; dilarang `--no-verify`. State ronde rusak/hilang → pulihkan dari `.bak`, atau `review_round.py rebuild` bila trailer mencatat ronde; dilarang menulis state dengan tangan.
5. **Siklus dependensi**: refaktor DAG menjadi rantai linier satu arah.
6. **Adapter tidak ditemukan**: hentikan; arahkan ke `frontenddev:profile` — brief tanpa penamaan adapter tidak boleh lahir.
7. **Plafon ronde Plan Review habis dengan BLOCKER tersisa**: jangan commit; sajikan BLOCKER ke user dan rutekan ke gate pemilik lewat `frontenddev:lead`.

## STYLE

- Imperatif aktif; Done Criteria biner; snippet interface TypeScript konkret di seksi 2 tanpa elipsis.
- Rujuk template dan referensi per bagian bernomor; dilarang menyalin kerangka brief ke sini.
