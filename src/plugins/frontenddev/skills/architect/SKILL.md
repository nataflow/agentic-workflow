---
name: architect
description: Dipanggil frontenddev:lead ketika ledger taskdir tercentang penuh dan brief READY siap dieksekusi, atau rantai terputus di tengah eksekusi - orkestrasi sekuensial implementor, gerbang kompilasi, verifikasi penutup, dan satu review independen, sebelum rantai dilaporkan tanpa bukti disk
user-invocable: false
---

## THE IRON LAW

- Jalankan brief satu per satu, sekuensial, lewat `code-implementor`; dilarang menyentuh `src/` dari main loop, dan dilarang mendispatch dua implementor bersamaan.
- Status unit divonis dari **disk** — `report-<NN>.md`, `git status`, dan hunk anchor — bukan dari kata balikan subagent. Kenaikan status brief dan commit-nya adalah satu langkah.
- Lint, test, dan build berjalan tepat sekali, di penutup; typecheck per unit hanya bila `typecheck_per_brief` prasyarat bernilai `ya` (profil, fallback adapter), dan divonis relatif baseline.
- Dispatch `code-reviewer` sekali per penutup; dispatch ulang **maksimal satu kali**, hanya bila `REVIEW.md` absen atau `validate_review.py` `FAIL` (`dispatcher/reviewer.md` Penanganan Balikan). Gagal kedua kalinya → Failure path 6. `REVIEW.md` di-commit hanya sesudah `validate_review.py` `PASS`. Review ulang (sesudah brief perbaikan) menimpa `REVIEW.md` utuh.
- Rantai yang berhenti `BLOCKED` tidak pernah direview dan tidak pernah dilaporkan tuntas. Cacat yang ditemukan di penutup diperbaiki di taskdir yang sama, tidak pernah dipindah ke taskdir baru.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/architect/scripts/check_preconditions.py --taskdir <taskdir>`.
2. `PASS` (9/9): lanjut. `FAIL`: hentikan dan kembalikan butir gagal beserta tindakannya ke `frontenddev:lead` — ledger belum tercentang atau berubah sesudah disetujui → gate pemiliknya atau `chain.py reopen`; brief `BLOCKED` tanpa remedi → `chain.py reopen --row BRIEF` lalu `plan` APPEND; profil/adapter → `frontenddev:profile`; tree kotor atau detached HEAD → laporkan ke user, jangan di-stash.
3. Baris `Terselesaikan:` menetapkan titik masuk: `fase=EKSEKUSI` → Phase 1 dengan `unit_berikutnya`; `PENUTUP` → Phase 4 (juga `REVIEW.md` basi — lebih tua daripada `implement unit` terakhir — atau yang tidak lagi lolos `validate_review.py`, mis. sesudah amandemen SC; review ulang menimpanya); `LAPORAN` → Phase 5 butir 2; `TERHENTI (REVIEW BLOCKED)` → Phase 5 butir 1; `TERHENTI (brief-NN BLOCKED)` atau `TERHENTI (DAG)` → Check 4 `FAIL`, butir 2 berlaku; `LAPORAN TERTUNDA` → Phase 5 butir 4; `TUNTAS` → laporkan apa adanya tanpa mendispatch siapa pun.
4. Skrip: `chain.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py`; `validate_review.py` = `${CLAUDE_PLUGIN_ROOT}/skills/architect/scripts/validate_review.py`; `check_preconditions.py` = `${CLAUDE_PLUGIN_ROOT}/skills/architect/scripts/check_preconditions.py`; `verify_scope.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/verify_scope.py`; `run_verification.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py`; `review-template.md` = `${CLAUDE_PLUGIN_ROOT}/skills/architect/templates/review-template.md`; `adapter` = `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md`. Di `dispatcher/*.md` dan `references/*.md`, `«nama»` berarti path absolut dari peta ini.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — taskdir aktif dari handoff `frontenddev:lead`.
- `max_dispatch_retry` — integer — default `1` — ulang dispatch hanya pada cabang "laporan absen atau rusak, tree selain itu bersih"; cabang lain dilarang retry.

## Workflow

### Phase 0 — Serap Profil & Baseline

1. Serap `stack` dari `.claude/profile/frontenddev/index.json`, perintah dari `commands.md`, dan `typecheck_per_brief` dari baris `Terselesaikan:` prasyarat (nilai profil `commands.md` bila ada, fallback baris `## Commands` adapter `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md`); dilarang membaca adapter sendiri untuk keputusan ini.
2. Ambil baseline seluruh perintah `commands.md` profil (typecheck, lint, test, build) sekali, sebelum implementor pertama: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py baseline --taskdir <taskdir> --cmd typecheck='<…>' --cmd lint='<…>' --cmd test='<…>' --cmd build='<…>'` lewat Bash `run_in_background: true`, lalu tunggu notifikasi selesainya. Skrip menyimpan exit code, durasi, dan tanda galat tiap perintah ke `{taskdir}/.explore/verification-baseline.json`; baseline yang sudah ada dipakai ulang (re-entry), tidak diukur ulang. Merah di sini bukan alasan berhenti — ia yang membuat gerbang kompilasi dan verifikasi penutup dapat memvonis galat **baru**.
3. Sajikan rantai sebelum implementor pertama berangkat: tabel `NN`, unit, status, `files_touched`, `depends_on`. Dilarang menahan rantai untuk meminta otorisasi commit — persetujuan breakdown sudah dimateraikan di ledger.

### Phase 1 — Ingest

Jalankan skrip prasyarat dengan `--brief <unit_berikutnya>` (`references/execution-protocol.md` bagian 1). `FAIL` menahan dispatch; `WARN` kesegaran disebut ke user lalu lanjut.

### Phase 2 — Dispatch & Triase Unit

1. Hidrasi `dispatcher/implementor.md` dengan `{ taskdir, brief_path, unit_name, report_path, adapter_path }` — `adapter_path` = `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md` — lalu dispatch `code-implementor` lewat tool `Agent` (`subagent_type`: `frontenddev:code-implementor`) tepat sekali.
2. Jalankan matriks bukti disk bagian 3 atas `report-<NN>.md` dan `git status --porcelain`, termasuk pemeriksaan anchor tiap berkas `MODIFY`. Ambil tindakan persis baris yang berlaku: **commit unit**, **commit BLOCKED**, retry sekali, atau HENTIKAN.
3. Commit unit mendarat → gerbang kompilasi bagian 5 (bila `ya`). Galat baru → `BLOCKED` retroaktif menurut bagian 5.
4. Unit `BLOCKED` → rantai berhenti; lompat ke Output `BLOCKED`. Phase 4 dilewati utuh.
5. Unit `DONE` → jalankan ulang skrip prasyarat rantai; `fase=EKSEKUSI` → kembali ke Phase 1 dengan `unit_berikutnya` baru, `fase=PENUTUP` → Phase 4.

### Phase 3 — Berkas Yatim Selama Rantai

Berkas yang muncul di diff unit, di galat kompilasi, atau di `REVIEW.md` sementara ia di luar **union** `files_touched` seluruh brief adalah cacat perencanaan. Dilarang mengarang brief penampungnya dan dilarang memperluas `files_touched` brief yang sudah `DONE`. Hentikan rantai dan kembalikan ke `frontenddev:lead` dengan rute kontrak bagian 7: `chain.py reopen --row CONTRACT` (kaskade membuka BRIEF) → `contract` melengkapi Files Touched → approve → `plan` APPEND. Lane `HOTFIX_MINOR` tak punya hop CONTRACT: `chain.py reopen --row BRIEF` → `chain.py escalate --lane FAST_FORWARD --sections architecture` → `contract` → `plan` APPEND.

### Phase 4 — Verifikasi Penutup & Review Tunggal

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py closing --taskdir <taskdir> --cmd <nama>='<perintah>' …` untuk seluruh perintah `commands.md` profil (nama sama dengan baseline Phase 0) plus `verification` brief yang belum tercakup, sekali, lewat Bash `run_in_background: true`. Dilarang memipe keluaran ke `tail`/`head` atau menyimpulkan vonis dari teks log. Skrip menulis `{taskdir}/.explore/closing-verification.md` (bagian 7); exit 0 = tidak ada merah baru, exit 1 = `TIMEOUT` atau galat baru > 0, exit 2 = pemanggilan salah. `MERAH` bergalat baru 0 adalah warisan baseline, bukan alasan berhenti. Exit 1 → klasifikasikan tiap berkas galat: cacat eksekusi (di dalam union → `chain.py reopen --row BRIEF` → `plan` APPEND brief perbaikan, di taskdir yang sama) atau berkas yatim (di luar union → Phase 3), lalu berhenti tanpa reviewer.
2. Hijau → hidrasi `dispatcher/reviewer.md` dengan `{ taskdir, base, verification_log, template, finding_source, adapter_path, chain_py }` — `base` = commit akar `TASK.md`, divonis `validate_review.py` — dan dispatch `code-reviewer` (`subagent_type`: `frontenddev:code-reviewer`); ulang maksimal sekali sesuai Penanganan Balikan `dispatcher/reviewer.md`.
3. Jalankan `validate_review.py --taskdir <taskdir> --log <taskdir>/.explore/closing-verification.json` (log mesin `run_verification.py` butir 1 — tabel `## Verifikasi Penutup` wajib identik dengannya) dan petakan hasilnya lewat `### Penanganan Balikan` template itu. `PASS` → bila `finding_source` ada dan berubah, `python3 ${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/validate_audit.py --path <finding_source> --only-status-changed` lebih dulu (`FAIL` → `git restore -- <finding_source>` dan catat di Output; berkasnya tidak ikut di-stage); lalu `git add {taskdir}/REVIEW.md [<finding_source>]` dan commit `docs(<slug>): closing review <verdict>`.

### Phase 5 — Laporan & Umpan Balik Profil

1. Verdict `BLOCKED` → rantai berhenti di sini dan kembali ke `frontenddev:lead`; perbaikannya di taskdir yang sama: `P1` dan SC `belum terbukti` → `chain.py reopen --row BRIEF` → `plan` APPEND brief perbaikan (tanpa `remedies`) → Phase 1 → Phase 4 ulang; berkas yatim → Phase 3. Dilarang memanggil `report`.
2. Verdict `PASS`/`WARNING` → kumpulkan baris `preseden menyesatkan` dari seluruh `report-<NN>.md` dan `## Umpan balik profil` `REVIEW.md`. Ada isinya → tanyakan sekali lewat `AskUserQuestion`: tandai permanen di profil, atau buang. Yang disetujui diteruskan ke `frontenddev:profile` lewat `reported_drift`.
3. Panggil `frontenddev:report` dengan `{ taskdir }`; ia menulis dan meng-commit `REPORT.md` sendiri. `REPORT.md` ada dan ter-commit → catat `dilewati (sudah terbit)`; ada tetapi belum ter-commit → butir 4.
4. **Laporan tertunda** (fase `LAPORAN TERTUNDA` — `report` menulis `REPORT.md` tetapi commit-nya gagal): jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/report/scripts/validate_report.py --taskdir <taskdir>`. `PASS` → `git add {taskdir}/REPORT.md` lalu commit `docs(<slug>): laporkan hasil rantai <slug>`; commit gagal → periksa penyebabnya (hook/lock), ulangi sekali, dilarang `--no-verify`, tetap gagal → laporkan ke user. `FAIL` → hapus `REPORT.md` yang belum ter-track (ter-track: `git restore -- {taskdir}/REPORT.md`), panggil `frontenddev:report` sekali lagi; gagal lagi → laporkan ke user.

## Guardrails

- **STRICT NON-AUTHORING**: dilarang membuat, mengedit, atau menghapus berkas di `src/` dari main loop, termasuk "perbaikan kecil" atas temuan review.
- **SEKUENSIAL MUTLAK**: dispatch berikutnya berangkat hanya sesudah commit unit sebelumnya mendarat dan tree kembali bersih.
- **COMMIT EKSPLISIT**: staging per path — `git add .`/`-A` dilarang; `.explore/` tidak pernah di-stage.
- **LARANGAN GIT MUTASI**: dilarang `git push`, `merge`, `rebase`, `reset --hard`, dan `revert` tanpa instruksi eksplisit user.
- **DISPATCH LEWAT TEMPLATE RESMI**: `code-implementor` hanya lewat `dispatcher/implementor.md`, `code-reviewer` hanya lewat `dispatcher/reviewer.md`; dilarang menyusun prompt sendiri atau menyalin isi brief ke prompt.
- **FAIL-FAST ON BLOCKED**: satu unit `BLOCKED` menghentikan rantai; dilarang melompat ke `NN+1`, dan dilarang memindahkan sisa pekerjaan ke taskdir baru.
- **RATIONALIZATION PREVENTION**:
  - "Balikan bilang DONE" bukan bukti — matriks bagian 3 yang memutuskan.
  - "Test-nya cepat, jalankan per unit biar yakin" — dilarang; hanya typecheck, hanya bila adapter `ya`.
  - "Temuan P2 sepele, saya tambal sekalian" — dilarang; perbaikan lewat brief perbaikan, bukan main loop.
  - "Review bilang PASS tapi validator FAIL, saya rapikan REVIEW.md-nya" — dilarang; dispatch ulang sekali atau laporkan tidak tuntas (Failure path 6).
  - "Berkas yatim cuma satu import, tambahkan ke brief DONE saja" — dilarang; rute kontrak.

## Output [REQUIRED]

Rantai bersih — seluruh brief `DONE`, verifikasi hijau, review `PASS`/`WARNING`, `REPORT.md` terbit — tutup satu baris: `ARCHITECT — COMPLETED · <taskdir> · Brief <n>/<n> DONE · Verifikasi PASS · Review <PASS|WARNING> (P2 <n>) · REVIEW.md @ <sha> · REPORT.md @ <sha>`, ditambah baris `Umpan balik profil` bila ada. Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### ARCHITECT — <BLOCKED | TERTAHAN>
- **Rantai**: <taskdir> · Brief <n>/<m> DONE · berhenti di brief-<NN> | di penutup
- **Sebab**: <baris matriks bagian 3 | galat kompilasi baru | verifikasi penutup MERAH | review BLOCKED>
- **Cacat eksekusi**: <brief-NN · berkas · galat> | —
- **Berkas yatim**: <path · brief penyentuh terakhir @ sha> | —
- **Review**: <PASS | WARNING | BLOCKED> · REVIEW.md @ <sha> | tidak dinilai (rantai terhenti)
- **Rute**: <chain.py reopen --row BRIEF → plan APPEND (remedi | perbaikan) | chain.py reopen --row CONTRACT → contract → plan APPEND | MINOR: reopen BRIEF → escalate FAST_FORWARD>
- **Umpan balik profil**: <file:baris — pola → pengganti> | —
```

**Serah-terima.** `Rantai selesai — kembali ke frontenddev:lead di main loop.` Dilarang membuka rantai baru sendiri.

## Failure path

1. **Tree kotor sebelum dispatch pertama**: hentikan di Precondition; kotoran yang bukan milik rantai adalah kerja user.
2. **Laporan unit absen atau rusak, tree selain itu bersih**: kegagalan dispatch — hapus `report-<NN>.md` rusak yang belum ter-commit (Check 12 menuntut ia absen), lalu ulangi sebanyak `max_dispatch_retry` dengan slot sama; brief tetap `READY`.
3. **Laporan unit absen, tree kotor**: HENTIKAN, tampilkan berkas kotor, eskalasi ke user; dilarang retry, rollback otomatis, dan commit.
4. **Commit unit gagal** (hook, lock): ulangi sekali sesudah memeriksa penyebabnya; tetap gagal → hentikan dan serahkan riwayat git ke user. Dilarang `--no-verify`.
5. **Perintah verifikasi melewati batas waktu**: `run_verification.py` membunuh pohon prosesnya pada `--timeout` (default 300 detik) dan mencatat `TIMEOUT` — bernilai merah; klasifikasi Phase 4 butir 1 tetap berjalan.
6. **Reviewer gagal dua kali**: sebelum berhenti, bersihkan tree — buang `REVIEW.md` yang tidak sah (`git restore -- {taskdir}/REVIEW.md` bila ter-track, hapus bila baru) dan pulihkan suntingan `finding_source` yang belum ter-commit (`git restore -- <finding_source>`); lalu laporkan review tidak tuntas. `REPORT.md` tidak dipanggil.
7. **Detached HEAD, rebase, atau `git am` yang berhenti**: hentikan di Precondition; minta user kembali ke branch sah.

## STYLE

- Kalimat imperatif aktif, Bahasa Indonesia baku, istilah git dan stack dipertahankan.
- Sha ringkas 7 karakter di tabel dan Output.
- Rujuk `references/execution-protocol.md` per bagian bernomor; dilarang menyalin tabelnya ke sini.
