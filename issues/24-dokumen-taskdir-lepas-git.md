# Langkah 24 — Dokumen taskdir `backend`/`frontend` lepas dari git, nataflow menjadi penyimpan (G1–G5, B1–B12, F1–F14, D1)

Sumber: permintaan user 2026-10-13: dokumen markdown yang dihasilkan plugin sudah tersimpan di nataflow, jadi
dokumen itu di-gitignore dan tidak perlu di-commit lagi. Diperjelas di sesi yang sama:

- Cakupannya hanya taskdir `backenddev/docs/**` dan `frontenddev/docs/**`. `.claude/profile/` tetap di-commit.
- **Mode total**, tidak bersyarat pada `.claude/nataflow.json`.
- **Tanpa fitur tarik** dari nataflow. Kemungkinan melanjutkan rantai dari mesin lain dinilai sangat kecil, dan
  memasukkan dokumen ke git hanya untuk itu justru mengotori riwayat.

Basis kode: commit `e875ff6` (backend 0.14.1, frontend 0.13.1).

**Status (2026-10-13):** RENCANA. Belum ada kode yang diubah. Peta blast radius di bawah disusun dari pembacaan
kode di basis itu. Tiap tahap tetap membuat peta per berkas sebelum menulis kode, seperti Langkah 15.

## Tujuan

1. Tidak ada skill, subagent, maupun skrip yang men-stage atau meng-commit berkas di bawah `backenddev/docs/` dan
   `frontenddev/docs/`. Riwayat git repo user hanya berisi kode, profil, dan dokumen tingkat repo.
2. Setiap gerbang yang sekarang bertumpu pada riwayat git dokumen tetap menegakkan hal yang sama lewat materai
   konten di disk. Batas barunya dinyatakan apa adanya, tidak disembunyikan.
3. Cermin nataflow tetap berjalan: dokumen stabil didorong dari isi disk, bukan dari blob `HEAD`.
4. Repo yang sudah meng-commit dokumen taskdir bisa dimigrasikan sekali jalan.

## Temuan awal (dasar keputusan)

Diverifikasi dengan membaca kedua plugin di basis kode di atas.

**Hampir seluruh integritas rantai berjangkar di riwayat git.** Bila dokumen tidak pernah di-commit, `git log`,
`git show <sha>:<path>`, dan `ls-files` atas dokumen itu kosong. Akibatnya:

| Plugin | Mekanisme | Rumah | Bergantung pada | Akibat bila di-ignore |
|---|---|---|---|---|
| backend | Bukti `DONE` brief (09 E18, 11 H5) | `brief_status.done_sha`, architect check 3 | Commit tempat status READY→DONE sekaligus membawa kode | FAIL "Brief DONE tanpa commit transisi" begitu brief pertama DONE |
| backend | Jalur `KOREKSI` | `brief_status.landed_sha` | Commit yang melahirkan brief (`--diff-filter=A`) | Tidak pernah terpicu, implementor didispatch ulang |
| backend | Kesegaran `REVIEW.md` | `brief_status.review_freshness`, architect, report check 3 | Commit `REVIEW.md` | "REVIEW.md belum ter-commit", architect berputar di FASE_4 selamanya |
| backend | Approval BRD/PRD (11 H17) | `precondition_lib.approval_verdict`, prasyarat `plan`/`system-analysis` | Commit `docs(spec): approve …` | Rantai BRD/PRD macet |
| backend | Anti-tamper brief (11 H3) | `verify_scope.brief_before` | `<sha>^:brief` | Diam-diam mati (jatuh ke salinan disk) |
| backend | Counter turun tangan (09 E20, 11 H13) | `chain_counters.py history` | `git log -- TASK.md` | Diam-diam mati |
| frontend | Ledger approval (12 J44, J46) | `precondition_lib.approval_stamp`/`verify_chain_row`, `chain.py` | Commit approve beserta materai di badan commit | Semua gerbang sesudah `task` FAIL. `approve`/`reopen`/`abandon`/`escalate` gagal di `require_clean`/`commit` |
| frontend | Akar rantai | `check_task_root`, `task_root_sha`, `chain_files` | Commit yang menambahkan `TASK.md` | Terhenti di AKAR, `chain_files` kosong |
| frontend | Plafon dan epoch | `count_subjects`, `revisions_since_open`, `reopen_epoch`, `review_round.presented` | Hitungan subjek commit | Plafon tidak tertegak, atau `review_round open` FAIL permanen sesudah dua ronde |
| frontend | Bukti `DONE` | `done_landed`, `brief_closure` | Commit yang membawa brief DONE dan kode sekaligus | DAG brief macet, `validate_report` check 4 FAIL |
| frontend | Keadaan taskdir | `lead/scripts/taskdir_state.py` | `is_committed(TASK/REPORT)`, kesegaran review | Terhenti di AKAR, PENUTUP, atau LAPORAN TERTUNDA selamanya |
| frontend | Pagar implementor | `hooks/guard_bash.py decide_writer` → `ignored()` | Path tidak di-ignore | Implementor ditolak menulis `report-NN.md` dan brief |
| keduanya | Sinkron nataflow (15 E6) | `sync_payload.py` | Blob `HEAD` | `--taskdir` FAIL "TASK.md belum ter-commit" |
| keduanya | Prosa | ±20 titik commit backend (matriks `gate-scope.md` bagian 3), ±35 titik frontend | `git add` atas path ter-ignore | Exit 1, commit tanpa isi |

**Yang sudah cocok:**

- Pemeriksaan tree bersih (`git status --porcelain`, tanpa `--ignored`) tidak melihat berkas yang di-ignore, jadi
  tetap hijau. `.explore/` memang sudah di-ignore sejak awal.
- Parser ledger, validator dokumen, status `BLOCKED`/`READY`, `read_halt`, lease `guard_bash` backend,
  `symbol_map.py`, dan `run_verification.py` membaca disk atau commit kode.
- `hooks/detect.py` dan `gate_text.py` tidak membaca dokumen taskdir.
- Commit kode per brief tetap ada. Subjeknya (`commit_message` brief, `feat(<slug>): implement unit NN`) cukup
  menjadi jangkar pengganti.

**Preseden:** analyst sudah menjalankan pola ini.

- `analyst_lib.TICKETS_IGNORE` adalah `.gitignore` berisi `*` yang ikut mengabaikan dirinya sendiri.
- `git_commit` melewati path yang di-ignore.
- Approval dijangkarkan pada materai konten `approved_seal`, bukan commit.
- Sinkron membaca `ns.disk_text`.
- Frontend sudah memeriksa materai itu untuk `ticket_source` (`sealed_verdict`/`ticket_seal`).

**Plugin lain tidak berubah.**

- analyst sudah mengabaikan tiketnya bila sinkron dikonfigurasi.
- quickdev mengecualikan `<plan_dir>/` dari pagar tree dan `Tree-Hash`.
- product menyimpan charter di luar cakupan ini.
- `nataflow_sync.py` (byte-identik di empat plugin) sudah punya `disk_text`, jadi tidak perlu disentuh.

**Repo user:** `nataflow-api` punya 20 taskdir dengan 191 berkas ter-track, dan semuanya sudah ber-`REPORT.md`.
Tidak ada rantai yang sedang berjalan, sehingga migrasi bisa langsung dijalankan.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Cakupan:** `backenddev/docs/**` dan `frontenddev/docs/**`. Yang tetap di-commit: `.claude/profile/*`, `backenddev/issues/**` (audit dan indeks review), `docs/api/**`, `frontenddev/reviews/**`. Analyst, quickdev, dan product tidak berubah. | Keputusan user. Profil dibutuhkan hook dan setiap developer. Dokumen tingkat repo bukan milik satu taskdir. |
| K2 | **Total, tidak bersyarat.** Berlaku walau `.claude/nataflow.json` absen. Bila config absen, gerbang masuk mencetak `WARN` bahwa dokumen taskdir hanya ada di disk ini. | Keputusan user ("biar full nataflow"). Satu jalur kode lebih murah dirawat daripada dua. |
| K3 | **Ignore lewat berkas yang mengabaikan dirinya sendiri:** `<prefix>/docs/.gitignore` berisi `*`. Berkas ini ditulis idempoten oleh gerbang masuk dan gerbang `task`, tidak pernah di-commit, dan `.gitignore` akar repo tidak disentuh. | Pola `analyst_lib.TICKETS_IGNORE`. Tidak ada baris `.gitignore` akar yang harus di-commit, dan tidak ada refresh profil hanya demi satu baris. |
| K4 | **Migrasi sekali jalan** untuk repo yang sudah meng-commit dokumen: `git rm -r --cached` atas `<prefix>/docs`, lalu satu commit `chore`, sesudah `AskUserQuestion`. Syaratnya semua taskdir sudah tuntas (ber-`REPORT.md`, `ABANDONED`, atau `DITUTUP`). Taskdir era git yang belum tuntas hanya bisa di-abandon. | Gitignore tidak berlaku untuk berkas yang sudah ter-track. Taskdir lama tidak membawa materai baru, dan menulis ulang materainya dari riwayat git berarti mempertahankan kode lama demi kasus satu kali. |
| K5 | **Pengganti jejak git adalah materai konten di disk**: sidik (sha256) isi dokumen tanpa baris yang sah berubah, ditulis skrip ke frontmatter dokumen atau ke `TASK.md`. Frontend menambah seksi `## Riwayat Rantai` di `TASK.md` yang hanya ditulis `chain.py`/`review_round.py`. Plafon dan epoch dihitung dari seksi itu, bukan dari subjek commit. | Preseden analyst. Materai ikut terkirim ke nataflow bersama dokumennya. Alternatif yang ditolak: (a) jurnal di `<git-dir>/nataflow/`, karena tidak terlihat dan tidak ikut ke nataflow; (b) ref privat `refs/nataflow/*` lewat `commit-tree`, karena plumbing-nya rumit, rapuh terhadap gc dan rebase, dan tetap "git kotor"; (c) mode bersyarat, karena ditolak user. |
| K6 | **Jangkar awal rantai = `base_commit`** (sha `HEAD` saat akar dikunci) di frontmatter `TASK.md`, ditulis skrip. Nilai ini menggantikan "commit yang menambahkan `TASK.md`" (frontend) dan "commit lahir brief" (backend). Sah hanya bila leluhur `HEAD`. Bila bukan, FAIL dengan remedi. | Rentang kode rantai tetap terhitung (`chain_files`, `landed_sha`, `validate_review`). `base_commit` biasanya commit di base branch, jadi tetap menjadi leluhur sesudah branch kerja di-rebase ke base yang lebih baru. |
| K7 | **Bukti `DONE` = status `DONE` di disk + commit kode bersubjek unit sejak `base_commit` yang membawa kode.** Subjek unit adalah `commit_message` brief (backend) atau `feat(<slug>): implement unit NN` (frontend). Koreksi `READY → DONE` cukup berupa suntingan status di disk, tanpa commit. | Commit kode tetap ada dan subjeknya sudah dikunci di brief. `DONE` tulisan tangan tanpa commit kode tetap tertangkap (inti 09 E18). |
| K8 | **Approval = materai di disk.** BRD/PRD backend: skrip menulis `status: APPROVED`, `approved_seal`, dan centang ledger `@ APPROVED <sidik12>`. Hop frontend: `chain.py approve` menulis blok hop di seksi `## Materai` `TASK.md` (`Hop`, `Sidik`, `Review-Round`, `Persetujuan user`, `SC`, waktu) dan centang `@ <sidik12>`. Isi dokumen sekarang wajib sama dengan `Sidik` (tanpa `status:`). | Isi materai commit approve frontend dipindah utuh ke disk. Yang hilang hanya jangkar "tahan rebase dan clone", yang tidak relevan lagi untuk dokumen yang memang tidak ikut clone. |
| K9 | **Kesegaran `REVIEW.md` diukur dari sha `HEAD` yang dinilai reviewer.** Backend sudah menulisnya sebagai ujung `range: <mb>..<HEAD>`. Frontend mendapat field baru `head:` di `review-template.md`, di samping `base`. Review segar bila tidak ada commit kode sesudah sha itu dan himpunan brief beserta statusnya sama dengan saat dinilai. | Menggantikan "commit `REVIEW.md` lebih baru daripada commit brief/kode". Nama field tepatnya ditetapkan di peta blast radius tahap 2. |
| K10 | **Anti-tamper brief (11 H3) = `sidik_kontrak` di frontmatter brief**, sidik `brief_contract(text)` yang ditulis saat brief dikunci (backend: penguncian `plan`; frontend: `chain.py approve BRIEF`). `verify_scope.py` membandingkan kontrak di disk dengan sidik itu, bukan dengan `<sha>^`. | Tetap satu kode untuk kedua plugin, jadi `verify_scope.py` tetap byte-identik. |
| K11 | **`HALT.md` dicabut lewat status, bukan dihapus:** `status: DICABUT` beserta alasan. `read_halt` hanya menganggap HALT aktif bila status bukan `DICABUT`. | Tanpa git, penghapusan tidak meninggalkan jejak, dan berkas yang dihapus tidak bisa ditandai di cermin (G5). |
| K12 | **Commit kode tetap, commit dokumen hilang.** Implementor men-stage kode saja, ditambah `finding_source` di `backenddev/issues/` bila ada. Reviewer backend meng-commit `backenddev/issues/README.md` saja. Skrip `chain.py`/`review_round.py` tidak menjalankan git commit lagi. | Subjek commit kode tidak berubah, jadi `symbol_map.py`, `chain_files`, dan bukti `DONE` K7 tetap bekerja. |
| K13 | **Pagar implementor frontend:** `guard_bash.py` mengecualikan `frontenddev/docs/<taskdir>/brief-*.md` dan `report-NN.md` dari penolakan "path diabaikan git". Path ter-ignore lain tetap ditolak. | Hanya dua berkas itu keluaran sah implementor di taskdir. Pagar "tulisan tak terlihat `verify_scope`" tetap berlaku untuk kode. |
| K14 | **Sinkron membaca disk.** Kriteria "stabil" (D2) dinilai dari status dan materai yang sah, bukan dari keberadaan di `HEAD`. DRAFT tetap tidak didorong. Metadata `commit` diganti `sidik` (sha256 isi) dan `head` (sha `HEAD` saat sinkron). | Tanpa ini cermin mati (15 E6 gugur). `nataflow_sync.disk_text` sudah tersedia, jadi pustaka byte-identik tidak disentuh. |
| K15 | **Regresi tidak dihapus diam-diam.** Tiap test git-based ditulis ulang ke mekanisme materai dengan ID regresinya tetap. Yang memang gugur (pemulihan hitungan ronde dari trailer git: `Brief-Review-Rounds` backend, `Review-Round` frontend) dicatat di bagian "Selisih pelaksanaan" beserta alasannya. | `xfail_strict` dan penandaan `regression("<ID>")` tetap bermakna. |
| K16 | **Versi:** backend 0.15.0, frontend 0.14.0. Perilaku berubah dan repo lama butuh migrasi. | Lint M7. |

## Kontrak

### G — bersama

- **G1 `skills/_common/docs_git.py`**: CLI baru, byte-identik di backend dan frontend seperti `verify_scope.py`.
  Prefix diturunkan dari `--plugin backend|frontend`.
  - `status [--json]`: apakah `<prefix>/docs` sudah di-ignore, daftar berkas yang masih ter-track, taskdir era git
    yang belum tuntas, dan apakah config nataflow ada.
  - `ensure`: tulis `<prefix>/docs/.gitignore` (K3) bila belum di-ignore. No-op di luar repo git.
  - `migrate --answer -`: K4. Ditolak bila ada taskdir belum tuntas. Commit berisi penghapusan dari index saja.
  - Masuk `CASES` `tests/test_smoke.py`, daftar byte-identik di `CLAUDE.md`, dan test kesamaan berkas.
- **G2 Gerbang masuk** (`tech-lead`, `lead`) dan gerbang `task`: check baru `DOCS_GIT`.
  - Berkas ter-track → `FAIL` dengan rute `MIGRASI` (K4).
  - Selain itu `ensure` berjalan.
  - Config absen → `WARN` (K2).
- **G3 `base_commit`**: ditulis saat akar dikunci (backend: skrip materai B1; frontend: `chain.py init`). Validator
  bersama di `precondition_lib.py` masing-masing plugin (berkas itu memang berbeda antarplugin): ada, berbentuk sha
  penuh, dan leluhur `HEAD`.
- **G4 Sidik konten**: satu fungsi per plugin, setara `ticket_seal`. Isinya sha256 teks tanpa baris `status:` dan
  tanpa field materai itu sendiri, dengan CRLF dinormalkan.
- **G5 Berkas yang dihapus tidak dicerminkan**: key remote yang berkasnya tidak lagi ada di disk tidak didorong, dan
  baris remote dibiarkan dengan isi terakhirnya. Penanda `removed: true` (15 E7) membutuhkan `upsert_document`
  tanpa `content`, yang belum didukung server. Dicatat di Di luar cakupan.

### B — backend

| ID | Perubahan |
|---|---|
| B1 | Skrip materai baru `skills/_common/doc_seal.py` (nama final di peta tahap 2) dengan empat subperintah. `root`: kunci akar, `base_commit` + sidik akar, dan amandemen akar `gate-lifecycle.md` 1a lewat jalur yang sama. `approve --doc BRD\|PRD --answer -` (K8). `briefs`: kunci batch brief, `sidik_kontrak` per brief, dan centang `BRIEF @ READY <sidik12>`. `verify`. |
| B2 | `approval_verdict` memeriksa `approved_seal` terhadap isi, bukan commit `docs(spec): approve`. Dipakai prasyarat `plan` dan `system-analysis`. |
| B3 | `brief_status.done_sha`/`landed_sha` mengikuti K7 dengan rentang `base_commit..HEAD`. Architect check 3 dan entri `KOREKSI:<NN>:<sha>` tetap memakai nama yang sama. |
| B4 | `review_freshness` mengikuti K9. Pemakainya: architect check (rute FASE_4) dan report check 3. |
| B5 | `read_halt`/`halted_nn` mengikuti K11. `scaffold_brief.py` tidak lagi mencetak instruksi `git rm HALT.md`. |
| B6 | `verify_scope.py` mengikuti K10. Suntingan dicerminkan ke frontend (byte-identik). |
| B7 | `chain_counters.py --check` hanya menilai plafon dan kunci. Deteksi nilai turun dari riwayat git gugur (K15). |
| B8 | `validate_briefs.py` `_trailer_rounds` gugur. Lantai ronde hanya dari `.explore/`, yang daya tahannya kini sama dengan dokumen. |
| B9 | `sync_payload.py` mengikuti K14. `TASK.md` tanpa `base_commit` → FAIL "akar belum terkunci". `--repo-docs` tidak berubah. |
| B10 | Prosa. Matriks `gate-scope.md` bagian 3 menjadi matriks penguncian (siapa menulis materai), dan baris commit dokumen dihapus. Yang ikut disunting: `analyst/SKILL.md` dan `chain-rules.md` (jangkar verdict "commit draft" diganti predikat `.explore/review/*.md`, ledger `@ <sidik12>`), `business-analysis`, `system-analysis`, `plan` + `review-and-commit.md`, `architect` + `lifecycle-recovery.md` + dua dispatcher, `agents/code-implementor.md`, `agents/code-reviewer.md`, `report`, `task`, `tech-lead` + `gate-lifecycle.md` + `nataflow-sync.md` + `decisions.md`, dan `profile/SKILL.md` Fase 5 butir 4 (peringatan "artefak lokal" kini menjadi perilaku baku). |
| B11 | Template: `task-template` (`base_commit`), `brd`/`prd-template` (`approved_seal`), `brief` (`sidik_kontrak`), `HALT` (`status`). |
| B12 | Test: fixture `chain_repo`/`land()` di `tests/conftest.py`, ±60 test berbasis git di `tests/backend/` (daftar di peta tahap 2), `test_15_sync_payload.py`, dan `CASES` smoke. |

### F — frontend

| ID | Perubahan |
|---|---|
| F1 | `chain.py init` menulis `base_commit`, dan `check_task_root` memeriksa G3 + validator `TASK`, bukan `is_committed`. `lane_tamper` membaca lane awal + eskalasi dari `## Riwayat Rantai`. |
| F2 | `chain.py approve`/`reopen`/`abandon`/`escalate`/`revisions`/`files` tanpa git commit. Materai ditulis ke `## Materai` (K8), kejadian ditulis ke `## Riwayat Rantai` (K5), dan plafon 3/hop, 6/taskdir, 2 eskalasi, serta 2 revisi dihitung dari Riwayat. |
| F3 | `precondition_lib.py` blok materai (`approval_stamp`, `approval_targets`, `verify_chain_row`, `doc_drift`, `brief_set_drift`, `snapshot_at`, `reopen_epoch`, `revisions_since_open`, `count_subjects`, `locked_brief_problems`) beralih ke materai dan Riwayat di disk. Sidik brief `DONE`/`BLOCKED` saat reopen disimpan di kejadian reopen. |
| F4 | `precondition_lib.py` `task_root_sha`/`chain_commits`/`chain_files` memakai `base_commit`. `done_landed`/`brief_closure` mengikuti K7. `review_is_fresh` mengikuti K9. |
| F5 | `review_round.py`: `commit` menjadi `seal` (tanpa git), dan ronde `PASS` dicatat di state serta Riwayat. Putaran dan epoch dihitung dari Riwayat. `rebuild` dan pendeteksian state hilang lewat trailer gugur (K15). |
| F6 | `lead/scripts/taskdir_state.py`: AKAR = `base_commit` absen atau tidak sah. Tuntas, LAPORAN TERTUNDA, dan PENUTUP dinilai dari status `REPORT.md` dan K9. |
| F7 | `architect/scripts/validate_review.py`: `base` = `base_commit`, `reviewed_at` dibandingkan dengan tanggal commit itu, dan bukti `path:baris` dinilai atas `chain_files` K6. |
| F8 | `plan/scripts/validate_briefs.py` Check M: `_first_blocked`, `_born_after`, dan `_contract_reentries` membaca Riwayat. |
| F9 | `report/scripts/validate_report.py` check 4 dan `review/scripts/check_preconditions.py --target taskdir` memakai `chain_files` K6. |
| F10 | `hooks/guard_bash.py` mengikuti K13. |
| F11 | `sync_payload.py` mengikuti K14. Ledger dibaca dari disk lewat `read_chain` + `verify_chain_row` yang baru. |
| F12 | Prosa (±35 titik di ±15 berkas): `task`, `lead` (+ `lane-routing-matrix.md`, `nataflow-sync.md`), `ux-design`, `ui-design`, `contract` (+ dispatcher reviewer), `plan` (+ dispatcher reviewer), `architect` (+ `execution-protocol.md`: "Commit unit" men-stage kode saja, "Commit BLOCKED" menjadi suntingan status di disk; + dispatcher implementor dan reviewer), `report`, `agents/code-implementor.md`, `agents/code-reviewer.md`, `agents/doc-reviewer.md`, dan `profile/SKILL.md` Fase 5 butir 4. |
| F13 | Template: `task-template` (`base_commit`, `## Materai`, `## Riwayat Rantai`), `review-template` (`base`), `report-template`, `flow-template`, `ui-template`, `brief-template` (`sidik_kontrak`). `review-template` juga mendapat `head` (K9). |
| F14 | Test: fixture `fe_chain_repo`/`fe_approved_chain`/`fe_round`/`fe_minor_chain`/`fe_review_md` dan `tests/frontend/fixtures/minor_chain_reviewed.sh`, ±150–170 test di `tests/frontend/` (seluruh `test_12_ledger` dan `test_review_round`, sebagian besar `test_12_validators`, `test_validate_review`, `test_12_verification`, `test_gate_preconditions`, `test_chain_reopen`, `test_validate_briefs_check_m`, dan lainnya), `test_12_guard.py`, `test_a1_ticket_source.py`, `test_17_tech_handoff.py`, dan `CASES` smoke. |

### D — dokumen dan rilis

**D1** menyunting dokumen dan menutup rilis:

- `flow/backend.md` dan `flow/frontend.md`: artefak, siklus status, dan titik gagal.
- README kedua plugin: tabel subjek commit frontend dan seksi sinkron.
- `README.md` akar.
- `CLAUDE.md`: daftar byte-identik ditambah `docs_git.py`, ringkasan arsitektur backend/frontend.
- Catatan di `issues/15-sinkron-artefak-nataflow/01-mcp-tools.md` bahwa E6 dan E7 digantikan K14 dan G5.
- Naik versi K16, lalu `claude plugin validate .`.

## Tahap pelaksanaan

Suite penuh wajib hijau di akhir tiap tahap. Tahap 1 belum mengaktifkan ignore, jadi test lama tetap berlaku sampai
plugin yang bersangkutan berpindah utuh di tahapnya sendiri.

| Tahap | Isi | Porsi kira-kira |
|---|---|---|
| 1 | G1, G3, dan G4: pustaka dan CLI `docs_git.py` beserta test, belum dipanggil gerbang mana pun | ~10% |
| 2 | Backend: G2 + B1–B12. Ignore aktif untuk `backenddev/docs/` | ~35% |
| 3 | Frontend: G2 + F1–F14. Ignore aktif untuk `frontenddev/docs/` | ~45% |
| 4 | D1, rilis, dan uji ujung ke ujung: satu rantai backend MINOR dan satu rantai frontend di repo scratch dengan `--plugin-dir` dari working tree, lalu migrasi `nataflow-api` dalam simulasi di salinan sementara | ~10% |

## Batas yang dinyatakan apa adanya

- **Materai bukan bukti keaslian.** Materai dan `## Riwayat Rantai` ditulis skrip, tetapi model di runtime yang sama
  bisa menulis ulang keduanya. Yang dijamin: suntingan dokumen yang tidak lewat skrip terdeteksi sebagai drift.
  Batas ini sama dengan analyst (`approved_seal`). Ketahanan terhadap rebase dan clone tidak lagi relevan karena
  dokumennya memang tidak ikut clone.
- **Rantai yang sedang berjalan hanya ada di satu mesin.** DRAFT dan `.explore/` tidak pernah dikirim ke nataflow.
  Disk yang hilang berarti rantai yang sedang berjalan ikut hilang. Dokumen stabil tetap ada di nataflow.
- **Repo tanpa `.claude/nataflow.json`** tidak punya salinan dokumen taskdir di mana pun selain disk lokal (K2).
- **Pemulihan hitungan ronde dari trailer git gugur** (K15): state ronde kini hanya di laci `.explore/`, dengan daya tahan yang sama dengan dokumen taskdir. Deteksi counter yang diturunkan tangan (09 E20) dipertahankan lewat log lokal (hasil tahap 2).

## Di luar cakupan

- Fitur tarik taskdir dari nataflow (`get_document`/`list_document`) untuk melanjutkan rantai dari mesin lain
  (keputusan user).
- Penanda `removed: true` untuk dokumen yang dihapus (G5). Butuh perubahan server: `upsert_document` menerima
  pembaruan metadata tanpa `content`.
- Dokumen tingkat repo (`backenddev/issues/`, `docs/api/`, `frontenddev/reviews/`), profil, dan plugin analyst,
  quickdev, product, fullstack, nataflow.

## Pelaksanaan

### Tahap 1 — peta blast radius (sebelum kode)

| Berkas | Perubahan | Yang bisa pecah |
|---|---|---|
| `backend/skills/_common/docs_git.py` (baru, CLI) | G1: `status`, `ensure`, `migrate --answer - [--terima-terbuka]`, `--json`. Pustaka untuk gerbang tahap 2–3: `docs_prefix`, `docs_ignored`, `ensure_ignored`, `tracked_docs`, `open_legacy_taskdirs`, `head_sha`, `base_commit_problem` (G3) | `test_smoke::test_inventaris_lengkap` (skrip ber-`__main__` wajib masuk `CASES`); jalur `FAIL` di keadaan repo `bukan-git`/`tanpa-commit`/`detached`/`rusak` wajib tetap JSON. Berkas tidak boleh mengimpor `precondition_lib` (berbeda antarplugin), dan prefix tidak boleh diturunkan dari `__file__` saat impor: `load_module` di test membuang modul sebelah, tetapi salinan yang termuat lebih dulu bisa milik plugin lain |
| `frontend/skills/_common/docs_git.py` (baru) | Salinan byte-identik | Test kesamaan baru |
| `tests/test_24_docs_git.py` (baru) | Kontrak CLI dan pustaka, kesamaan dua salinan | — |
| `tests/test_smoke.py` | `CASES`: `status --json` dan `ensure --json` per plugin | Keadaan `rusak` merusak `TASK.md`; `status` wajib memvonisnya terbaca, bukan traceback |
| `CLAUDE.md` | `docs_git.py` masuk daftar salinan byte-identik | — |

Keputusan tambahan:

- **G4 tidak menjadi fungsi baru.** Frontend sudah punya `content_snapshot`/`strip_status_line`, yang menjadi dasar
  `Sidik:` materai approve, dan backend punya pola `ticket_seal`. Sidik konten ditulis di tahap plugin masing-masing di
  atas fungsi yang sudah ada, supaya `Sidik` lama dan baru tetap satu definisi.
- **Taskdir era git yang terbuka** adalah taskdir ber-`TASK.md` tanpa `REPORT.md`, dengan `status` `ACTIVE` atau
  kosong, dan tanpa `base_commit`. Backend tidak punya jalur `abandon`, jadi `migrate` tidak hanya menolak: user bisa
  meneruskan dengan `--terima-terbuka`, yang menyatakan bahwa taskdir itu tidak bisa dilanjutkan. Berkasnya tetap di
  disk.
- **Commit migrasi hanya berisi penghapusan dari index.** `migrate` menolak bila index sudah memuat perubahan lain
  ter-stage, karena `git commit --only <path>` justru men-stage ulang isi working tree path itu.

**Hasil tahap 1:** `docs_git.py` di kedua plugin (byte-identik), `tests/test_24_docs_git.py` (36 test), dua `CASES`
smoke. Suite penuh hijau, subset di Python 3.9 hijau (`Path.write_text(newline=)` baru ada di 3.10, jadi diganti
`write_bytes`), lint 0 FAIL.

### Tahap 2 — peta blast radius backend (sebelum kode)

Inventaris pemanggilan git di skrip backend (`grep` atas `skills/**/*.py` dan `hooks/*.py`). Gerbang berbasis
commit dokumen hanya ada di baris berikut; sisanya membaca disk, membaca commit kode, atau sekadar memeriksa
`rev-parse --is-inside-work-tree`.

**Skrip:**

| Berkas | Perubahan | Yang bisa pecah |
|---|---|---|
| `skills/_common/doc_seal.py` (baru, CLI) | B1, enam subperintah. `root`: tulis `base_commit` = `HEAD` ke frontmatter `TASK.md`. `approve --doc BRD\|PRD --answer -`: `DRAFT` → `APPROVED` + `approved_seal`, lalu centang ledger `@ APPROVED <sidik12>`. `lock-briefs`: tulis `sidik_kontrak` ke tiap brief `READY`. `tick --hop BRIEF`: centang `BRIEF @ READY <sidik12>`. `cabut-halt --alasan`: `HALT.md` `status: DICABUT`. `status [--json]`: vonis semua materai | `test_smoke::test_inventaris_lengkap` (masuk `CASES`), lint S1/R |
| `skills/_common/precondition_lib.py` | B2: `doc_seal(text)` (sidik isi tanpa baris `status`/`approved_*`). `approval_verdict` memeriksa `approved_seal`, bukan commit `docs(spec): approve`. Helper `task_base_commit(taskdir)` | `test_11_robustness` H17 (×3), `test_system_analysis_preconditions` (3), `test_plan_preconditions` (1) |
| `skills/_common/brief_status.py` | B3: `landed_sha` merentang `base_commit..HEAD` (bukan commit lahir brief). `done_sha` = commit unit bersubjek `commit_message` yang membawa kode, karena transisi status tidak lagi ada di riwayat. B4: `review_freshness` dari ujung `range:` `REVIEW.md` (tidak ada commit kode sesudahnya). B5: `read_halt` mengabaikan `status: DICABUT` | `test_brief_status` (2), `test_l23_stale_review` (5), `test_l210_recovery` (2), `test_09_robustness` E18 (×3), `test_11_robustness` H5 (×2), `test_l22_supersede`, `test_l24_halt` |
| `skills/architect/scripts/check_preconditions.py` | Check 3: `base_commit` wajib sah sebelum pemindaian brief. Pesan "DONE tanpa commit transisi" menjadi "DONE tanpa commit unit". Docstring check 7 HALT | `test_09_robustness` E18, `test_l210_recovery`, `test_e2e_langkah2` |
| `skills/report/scripts/check_preconditions.py` | Check 3 memakai `review_freshness` baru (pesan "REVIEW.md belum ter-commit" hilang) | `test_report_preconditions`, `test_l23_stale_review` |
| `skills/plan/scripts/check_preconditions.py`, `skills/system-analysis/scripts/check_preconditions.py` | Pesan FAIL approval: "tidak terikat materai approve", remedi `doc_seal.py approve` | idem B2 |
| `skills/_common/verify_scope.py` (+ salinan frontend) | B6: brief ber-`sidik_kontrak` → suntingan kontrak dinilai terhadap sidik itu, di mode `--commit` maupun `--worktree`. Brief tanpa sidik tetap memakai jalur git lama, karena frontend baru pindah di tahap 3. `brief_contract` mengosongkan baris `sidik_kontrak:` | `test_11_robustness` H3 (×3), `test_12_verification` kedua plugin (salinan identik) |
| `skills/analyst/scripts/chain_counters.py`, `skills/analyst/scripts/check_preconditions.py` | B7: `history`/`tampered` dibuang, `--check` hanya plafon dan kunci | `test_09_robustness` E20 (×4), `test_11_robustness` H13 |
| `skills/plan/scripts/validate_briefs.py` | B8: `_trailer_rounds` dan baris `trailer` di keluaran `--review-state` dibuang | `test_l27_plan_state` (2) |
| `skills/plan/scripts/scaffold_brief.py` | Instruksi `git rm HALT.md` menjadi `doc_seal.py cabut-halt`, dan catatan "stage bersama di commit agregat" dibuang | `test_l24_halt`, `test_l22_supersede` |
| `skills/_common/sync_payload.py` | B9: dokumen dari disk (`ns.disk_text`). `TASK.md` tanpa `base_commit` → FAIL "akar belum terkunci". BRD/PRD hanya bila `APPROVED` dengan `approved_seal` cocok. Brief hanya bila ber-`sidik_kontrak`. Metadata `commit` kosong dan `head` = `HEAD`. Key remote yang berkasnya hilang tidak didorong (G5). `HALT.md` `DICABUT` tidak membuat workdir `blocked` | `test_15_sync_payload` (±14 dari 16), `CASES` smoke |
| `skills/tech-lead/scripts/check_preconditions.py` | G2 di check 3: berkas `backenddev/docs/` yang masih ter-track → FAIL rute `MIGRASI`; selain itu `docs_git.ensure_ignored` sebelum menilai tree kotor (mode penuh dan `--re-entry`; mode `--read-only` tidak menulis). `backenddev/docs/` keluar dari `RE_ENTRY_ALLOWED_PREFIXES` | `test_l28_tech_lead`, test re-entry |
| `skills/task/scripts/check_preconditions.py` | Check git: `backenddev/docs/` wajib sudah diabaikan dan nol berkas ter-track | `test_11_robustness` H20, `test_a1_ticket_source`, `test_17_tech_handoff` |
| `hooks/guard_bash.py` | Tidak berubah. Lease sudah memuat brief dan `report-NN.md` dari disk, dan reviewer tetap boleh `git add` atas `backenddev/issues/README.md` | `test_l34_guard_bash` (tetap) |

**Prosa** (±20 titik commit dokumen di ±30 berkas). Arah perubahan: "commit" dokumen taskdir diganti "kunci" lewat
skrip, atau dihapus bila tidak ada yang perlu dikunci.

| Berkas | Perubahan |
|---|---|
| `skills/tech-lead/references/gate-scope.md` bagian 3 | Matriks kepemilikan commit menjadi matriks penguncian. Baris dokumen taskdir berganti skrip materai atau "tanpa kunci (disk)". Baris `REVIEW.md` tetap menyebut `backenddev/issues/README.md` dan `code-reviewer` (`test_l21`) |
| `skills/tech-lead/SKILL.md` | Fase 3 (ensure/migrasi), Fase 5 (artefak taskdir tidak di-commit), dan kalimat commit `HALT`. Anggaran 14000 byte (sisa 7 byte): penambahan dibayar pemadatan |
| `skills/tech-lead/references/gate-lifecycle.md` | 1a amandemen akar tanpa commit, bagian 6 (commit artefak hanya dokumen tingkat repo dan profil), pencabutan HALT lewat `doc_seal.py cabut-halt`, dan "reset" HALT |
| `skills/tech-lead/references/nataflow-sync.md`, `decisions.md` | Sinkron dari disk; kalimat commit |
| `skills/task/SKILL.md`, `templates/task-template.md` | Fase 5: `doc_seal.py root` menggantikan commit. Template mendapat `base_commit`, dan contoh ledger `@ APPROVED <sidik12>` |
| `skills/analyst/SKILL.md`, `references/chain-rules.md` | Jangkar verdict tanpa commit draft. Approval lewat `doc_seal.py approve`. Ledger, re-entry, dan eskalasi tanpa commit `TASK.md`. Tutup ledger lewat `doc_seal.py tick --hop BRIEF` |
| `skills/business-analysis/SKILL.md`, `skills/system-analysis/SKILL.md` | "Commit draft" diganti "draft dikunci di disk", tanpa commit |
| `skills/plan/SKILL.md`, `references/review-and-commit.md`, `templates/brief-template.md` | Commit agregat diganti `doc_seal.py lock-briefs`. Trailer `Brief-Review-Rounds` dibuang. HALT dicabut lewat skrip |
| `skills/architect/SKILL.md`, `references/lifecycle-recovery.md`, `dispatcher/implementor.md`, `dispatcher/reviewer.md` | Commit HALT dan koreksi status diganti suntingan disk. Matriks bukti disk, kesegaran review, dan "reset" HALT |
| `agents/code-implementor.md` | Stage kode + `finding_source` saja, brief tidak di-stage. Status `DONE` ditulis ke disk sebelum commit (`test_l26` memaku frasa `finding_source`) |
| `agents/code-reviewer.md` | `git add backenddev/issues/README.md` saja; `REVIEW.md` ditulis tanpa commit (`test_l21`, `test_l36`, `test_h31`) |
| `skills/report/SKILL.md`, `skills/debug/SKILL.md`, `skills/audit/SKILL.md`, `skills/document-api/SKILL.md`, `skills/profile/SKILL.md` | `REPORT.md`/`RCA.md` tidak di-commit. Profil Fase 5 butir 4 (peringatan "artefak lokal") menjadi perilaku baku |
| `README.md` | Seksi commit dan seksi sinkron |

**Test:** `tests/conftest.py` `chain_repo` ditulis ulang. `TASK.md` tidak di-commit,
`backenddev/docs/.gitignore` (`*`) ada, dan `base_commit` diisi `HEAD` sesudah commit awal. `land()` men-commit kode
saja dan menulis `DONE` di disk. Test berbasis git dokumen ditulis ulang ke mekanisme materai dengan ID regresi
yang sama (K15). E20 (deteksi counter turun dari riwayat) dan trailer `Brief-Review-Rounds` gugur dan dicatat.
Test baru: `tests/backend/test_24_doc_seal.py`.

**Hasil tahap 2 (2026-10-13):** backend berpindah utuh. `doc_seal.py` (6 subperintah) dan
`tests/backend/test_24_doc_seal.py` (13 test). ±40 test lama ditulis ulang ke mekanisme materai dengan ID
regresinya tetap, ditambah test baru 24 G2 (`test_task_preconditions`, `test_tech_lead_preconditions`), 24 K11,
dan 24 G5 (`test_15_sync_payload`). Suite penuh hijau (2566 passed), subset backend di Python 3.9 hijau, dan lint
0 FAIL.

Selisih pelaksanaan terhadap peta:

- **09 E20 tidak gugur.** Deteksi counter yang diturunkan tangan dipertahankan lewat log tulisan skrip
  `<taskdir>/.explore/counters-log.json` (tabel sesudah tulis beserta operasinya), menggantikan `git log -- TASK.md`.
  Entri `reset:<HOP>` hanya sah bila tepat didahului `bump:reentry`, sesuai urutan re-entry Fase 3 butir 0. K15
  dan bagian Batas disesuaikan: yang gugur hanya pemulihan hitungan ronde brief dari trailer git.
- **`finding_diff_ok` dipertahankan.** Fungsi ini tidak berkaitan dengan dokumen taskdir (`backenddev/issues/`
  tetap ter-commit), dan `test_l26` masih mengujinya.
- **`ensure_ignored` tidak menulis apa pun di luar repo git**, supaya check 3 `tech-lead` di folder non-git tidak
  meninggalkan `backenddev/docs/.gitignore`.
- **`approved_seal` mengecualikan field `approval`** (jawaban user, pola analyst `clean_value`), sehingga approve
  ulang atas isi yang sama menghasilkan sidik yang sama.
- **`doc_seal.py approve` menerima `status: APPROVED`** selama hop ledger-nya belum `[x]`. Jalur re-entry membuka hop
  `[~]` tanpa menurunkan status dokumen (`analyst` Fase 3 butir 0), jadi approve ulang sesudah revisi harus lolos.
- **`profile` Fase 5 tidak lagi menulis baris `.explore/`.** Laci `.explore/` berada di bawah `backenddev/docs/`, dan
  penanda `backenddev/docs/.gitignore` milik `docs_git.py` sudah menutupnya. Butir 2 kini memperingatkan bila
  `backenddev/issues/` ikut di-ignore.
- **`plan` tetap punya satu commit**: penanda `OBSOLETE`/`DROPPED` di berkas `finding_source`
  (`backenddev/issues/`, dokumen repo), dengan subjek `docs(plan): tandai temuan <ID> untuk <slug>`.
- **Riwayat amandemen akar** tidak lagi tersimpan di luar isi terakhir `TASK.md`, hitungan `root_amendment`, dan
  cermin nataflow; seksi `## Amendments` tetap dilarang (`gate-lifecycle.md` bagian 1a).
- **Helper test `commit()` tanpa path** tidak membuat commit bila tidak ada yang ter-stage, karena dokumen taskdir
  yang ditulis test kini diabaikan git. Path eksplisit yang di-ignore tetap gagal di `git add`.

### Tahap 3 — peta blast radius frontend (sebelum kode)

Inventaris pemanggilan git di skrip frontend (`grep` atas `skills/**/*.py` dan `hooks/*.py`). Hampir seluruh
integritas rantai frontend dibaca dari subjek dan badan commit dokumen `TASK.md`. Karena itu tahap ini mengganti
satu sumber kebenaran dengan sumber lain, bukan menambal titik per titik.

**Keputusan rancangan** (dari pembacaan kode, menajamkan K5, K8, K9, K10, K13, dan K15):

- **Satu seksi `## Riwayat Rantai` di `TASK.md`, tanpa seksi `## Materai` terpisah.** Materai approve adalah
  kejadian `approve` di Riwayat. Dengan begitu `approval_stamp` tetap bekerja seperti pembacaan `git log`: pindai
  mundur, `reopen` yang membuka hop itu → hop tidak bermaterai, `approve` hop itu → materainya. Satu baris per
  kejadian, bernomor urut, dan hanya ditulis `chain.py`:

  ```text
  ## Riwayat Rantai

  - 1 · akar · base 1a2b3c4 · lane FAST_FORWARD · sections architecture · akar 0123456789ab · 2026-10-13T10:00:00Z
  - 2 · draft CONTRACT · sidik 0123456789ab · review contract r1 t1 PASS 0123456789ab · 2026-10-13T10:05:00Z
  - 3 · approve CONTRACT · sidik 0123…(40) · review contract r1 t1 PASS 0123456789ab · sc 0123456789ab · 2026-…Z · persetujuan: Setujui
  - 4 · reopen BRIEF · target BRIEF · berkas brief-01-a.md=DONE:0123456789ab;brief-02-b.md=BLOCKED:… · 2026-…Z · alasan: …
  - 5 · eskalasi · lane HOTFIX_MINOR → FAST_FORWARD · sections - → architecture · akar … · 2026-…Z · alasan: …
  ```

  Teks bebas (`persetujuan:`, `alasan:`) selalu di ujung baris dan wajib satu baris (12 J46 tetap berlaku). Nomor
  yang tidak berurut, field ganda, atau baris tak terurai membuat Riwayat dinyatakan rusak, dan semua gerbang
  menolak dengan remedi `frontend:lead`.
- **Subperintah `chain.py` baru menggantikan commit dokumen.**
  - `root`: kunci akar. Menulis `base_commit` = `HEAD` dan kejadian `akar` (lane, sections, sidik akar). Mengganti
    commit `kunci TASK sebagai akar rantai`.
  - `amend --reason`: amandemen akar. Menjalankan `validate_task.py --amend` sendiri, lalu mencatat sidik akar baru.
    Mengganti commit `amandemen akar TASK`.
  - `draft --row`: catat draft atau revisi hop. Validator gate harus `PASS`. Untuk CONTRACT, dan BRIEF lane
    non-MINOR yang punya brief `READY`, ronde reviewer terakhir juga harus `PASS` atas konten itu, dan field
    `review` ikut dicatat. Mengganti `git commit` draft `FLOW.md`/`UI.md`/brief MINOR dan `review_round.py commit`.
- **Sidik akar** (sha1 frontmatter tanpa `status:` + isi sebelum `## Chain`) menggantikan `is_committed(TASK.md)`
  di `check_task_root`. Suntingan akar di luar `amend`/`escalate` → FAIL dengan remedi amandemen akar. Tanpa
  pengganti ini, akar frontend yang dulu terkunci commit bisa disunting diam-diam.
- **Revisi** dihitung sebagai draft ke-2 dan seterusnya sejak `reopen` apa pun atau `approve` hop itu. Ini setara
  dengan hitungan subjek `revise` + `draft` berulang yang lama.
- **Pemulihan ronde tetap ada (K15 frontend tidak menggugurkan apa pun).** Field `review <gate> r<n> t<total>` di
  kejadian `draft`/`approve` menggantikan trailer `Review-Round`. `committed_rounds`, deteksi state yang terpotong,
  dan `rebuild` membaca Riwayat.
- **`presented`** (putaran ronde): ronde `PASS` dianggap sudah diajukan bila ada kejadian `draft` hop gate itu
  sesudah ronde dibuka (`riwayat` = jumlah kejadian saat `open`) dengan sidik yang sama. Ronde format lama yang
  hanya ber-`head` dianggap belum diajukan (konservatif).
- **Approve:**
  - Approve hop dokumen menuntut kejadian `draft` terakhir hop itu sesudah reopen terakhirnya bersidik sama dengan
    isi disk. Ini pengganti `require_clean`: konten yang disetujui adalah konten yang tercatat diajukan.
  - Approve BRIEF tanpa brief `READY` (approval ulang tanpa kerja baru) tidak menuntut draft.
  - Approve BRIEF menulis `sidik_kontrak` ke tiap brief `READY` (K10). Kejadiannya memuat sidik per berkas dan
    status, sidik agregat, `brief` (sidik brief saja, pembanding `Review-Round`), dan `sc`.
- **`strip_status_line` juga membuang baris `sidik_kontrak:` pertama di frontmatter.** Penulisan sidik saat approve
  tidak boleh mengubah sidik konten yang sudah direview.
- **Bukti `DONE` (K7):** brief `DONE` di disk ditambah commit `<type>(<slug>): implement unit <NN>` di
  `base_commit..HEAD` yang membawa kode. Urutan architect: status `DONE` di disk lebih dulu, lalu commit kode.
  Terputus di antaranya → matriks bukti disk.
- **Kesegaran review (K9):** field `head:` baru di `REVIEW.md`. Review segar bila `head` leluhur `HEAD` dan tidak ada
  commit rantai (`(<slug>)`) pembawa kode sesudahnya.
- **Keadaan taskdir:**
  - `TUNTAS`: `REPORT.md` lolos `validate_report.py`. `LAPORAN TERTUNDA`: `REPORT.md` ada tetapi gagal validator.
  - Pemeriksaan `TUNTAS` sebelum ledger (12 J44, demi squash-merge) dibuang, karena materai kini di disk.
  - Taskdir era git tanpa `base_commit`:
    - ber-`REPORT.md` → `TUNTAS` (warisan);
    - ber-centang atau ber-artefak → `RUSAK`, rute `chain.py abandon`;
    - selain itu → `AKAR` (kunci akar).
- **Pagar implementor (K13):** pengecualian hanya `frontenddev/docs/<taskdir>/report-NN.md`. Implementor frontend
  tidak pernah menyunting brief (`agents/code-implementor.md` [FORBIDDEN]); status ditulis architect.
- **G2 di frontend:**
  - `lead` tidak punya skrip prasyarat. `taskdir_state.py` (Phase 2) keluar `FAIL` dengan rute `MIGRASI` bila
    `frontenddev/docs/` masih ter-track. Ia tetap read-only: `sync_payload` memanggilnya.
  - Check 10 baru di prasyarat `task` menjalankan `ensure_ignored`.
  - Cabang "kotoran milik taskdir sendiri" di `check_worktree` dibuang, karena dokumen taskdir tidak pernah lagi
    tampak kotor.

**Skrip:**

| Berkas | Perubahan | Yang bisa pecah |
|---|---|---|
| `skills/_common/precondition_lib.py` | Blok Riwayat baru: `read_history`, `history_problem`, `root_sidik`, `sc_sidik`, `history_line`. `check_task_root`: Riwayat + `base_commit` + sidik akar, bukan `is_committed`. `lane_tamper` me-replay Riwayat. `reopen_epoch`, `revisions_since_open`, `approval_stamp`, `verify_chain_row`, `brief_set_drift`, `doc_drift`, dan `locked_brief_problems` membaca Riwayat. `task_root_sha` = `base_commit`. `done_landed` mengikuti K7. `review_is_fresh` mengikuti K9. `check_worktree` tanpa cabang kotoran sendiri. Dibuang: `show_at`, `snapshot_at`, `gate_targets_at`, `count_subjects`, `_log_entries`, `stamp_fields`, `approve_subject_ok`, `review_required_at`, `_status_at`, `is_committed` | test_12_ledger (±40), test_12_validators, test_12_verification (`is_committed`, `lane_tamper`), test_09_robustness (`lane_tamper`, `review_is_fresh`, `revisions_since_open`), test_gate_preconditions, test_chain_reopen |
| `skills/_common/chain.py` | `init` tanpa perubahan. `root`, `amend`, `draft` baru. `approve`, `reopen`, `abandon`, `escalate` menulis disk + Riwayat, tanpa `git add`/`commit`. `files` dan `revisions` membaca Riwayat. Plafon dari Riwayat | test_12_ledger, test_chain_reopen, test_08c_chain_newline, `fe_chain_repo`/`fe_approved_chain`/`fe_minor_chain` |
| `skills/_common/review_round.py` | `commit` dibuang (digantikan `chain.py draft`). `epoch`, `presented`, `committed_rounds`, dan `rebuild` dari Riwayat. Ronde mencatat `riwayat`, bukan `head` | test_review_round (±30) |
| `skills/lead/scripts/taskdir_state.py` | Urutan vonis baru (lihat Keputusan). Keluar `FAIL` `MIGRASI` bila dokumen masih ter-track | test_08c_taskdir_state, test_phase_report, test_12_orchestration |
| `skills/architect/scripts/check_preconditions.py` | `implemented` = `report-NN.md` + `done_landed` K7. `LAPORAN TERTUNDA` dari `validate_report.py`. `check_worktree` tanpa `allow`/`own_action` | test_08c_architect_preconditions, test_12_orchestration |
| `skills/architect/scripts/validate_review.py` | `base` = `base_commit`, `head` wajib leluhur `HEAD`, dan `reviewed_at` dibandingkan dengan tanggal `base_commit`. `_first_unit` sejak `base_commit` | test_validate_review, test_08c_text, `fe_review_md` |
| `skills/plan/scripts/validate_briefs.py` | Check M: `_first_blocked`, `_born_after`, dan `_contract_reentries` membaca kejadian `reopen` Riwayat | test_validate_briefs_check_m |
| `skills/plan/scripts/check_preconditions.py` | Mode REVISE: `revisions_since_open` baru | test_gate_preconditions |
| `skills/report/scripts/check_preconditions.py` | Check 3: `REVIEW.md` tanpa `is_committed`. Check 5: tertunda = gagal `validate_report.py`. Check 7 tanpa `own_action` | test_08c_task_report, test_phase_report |
| `skills/review/scripts/check_preconditions.py`, `skills/report/scripts/validate_report.py` | `chain_files` sejak `base_commit` (tanpa perubahan kode bila `task_root_sha` sudah bermakna baru) | test_08c_review_preconditions, test_validate_report, test_parsing_l5 |
| `skills/task/scripts/check_preconditions.py` | Check 5: `finding_source` ter-track dan bersih tanpa `is_committed`. Check 10 baru: G2 | test_a1_ticket_source, test_17_tech_handoff |
| `skills/task/scripts/validate_task.py` | Heading sah: empat heading lama, ditambah `## Riwayat Rantai` opsional di ujung. `base_commit` di frontmatter | test_08c_task_report |
| `skills/_common/sync_payload.py` | K14 seperti backend. `TASK.md` tanpa akar terkunci → FAIL | test_15_sync_payload, smoke |
| `hooks/guard_bash.py` | K13: `report-NN.md` taskdir dikecualikan dari penolakan "diabaikan git" | test_12_guard |
| `skills/_common/verify_scope.py` | Tidak berubah (sudah ber-`sidik_kontrak` sejak tahap 2) | — |

**Prosa** (±120 sebutan `commit` di ±40 berkas, mayoritas commit dokumen). Arah perubahannya sama dengan backend.

| Berkas | Perubahan |
|---|---|
| `skills/task/SKILL.md`, `templates/task-template.md` | Phase 4 butir 5: `chain.py root` menggantikan commit. Template mendapat `base_commit` dan `## Riwayat Rantai` |
| `skills/lead/SKILL.md`, `references/lane-routing-matrix.md`, `references/nataflow-sync.md` | Rute `MIGRASI`, keadaan baru (`LAPORAN TERTUNDA`, `TUNTAS`, warisan), amandemen akar lewat `chain.py amend`, plafon dari Riwayat |
| `skills/ux-design/SKILL.md`, `skills/ui-design/SKILL.md` | Commit draft/revisi → `chain.py draft` |
| `skills/contract/SKILL.md`, `dispatcher/reviewer.md` | `review_round.py commit` → `chain.py draft`. Materai approve di Riwayat |
| `skills/plan/SKILL.md`, `dispatcher/reviewer.md`, `templates/brief-template.md` | Tabel subjek commit Phase 4 → `chain.py draft --row BRIEF`. Brief mendapat `sidik_kontrak` |
| `skills/architect/SKILL.md`, `references/execution-protocol.md`, `dispatcher/implementor.md`, `dispatcher/reviewer.md`, `templates/review-template.md` | Commit unit men-stage kode saja (status `DONE` di disk lebih dulu). Commit BLOCKED menjadi suntingan disk. `REVIEW.md` tanpa commit (field `head`). Phase 5 butir 4 tanpa commit |
| `skills/report/SKILL.md`, `skills/review/SKILL.md`, `skills/profile/SKILL.md` | `REPORT.md` tidak di-commit. Profil Fase 5: baris `.explore/` diganti penanda `docs_git.py` |
| `agents/code-implementor.md`, `agents/code-reviewer.md`, `agents/doc-reviewer.md`, `agents/contract-reviewer.md` | Kalimat commit |
| `README.md` (plugin) | Tabel subjek commit, `chain.py`, keadaan taskdir, sinkron |

**Test:** fixture `fe_chain_repo` ditulis ulang (`frontenddev/docs/.gitignore`, `chain.py root`, `CONTRACT.md` DRAFT
di disk), begitu juga `fe_approved_chain` (`chain.py draft` menggantikan `review_round.py commit`), `fe_brief`,
`fe_review_md` (`head`), dan `minor_chain_reviewed.sh` (tanpa `git add` dokumen, `chain.py root`/`draft`, commit
kode saja, `REVIEW.md` ber-`head`). Test berbasis git dokumen ditulis ulang ke Riwayat dengan ID regresi yang sama.
Test baru: `tests/frontend/test_24_riwayat.py` (format dan keutuhan Riwayat, `root`/`amend`/`draft`, sidik akar,
K13, dan G2 frontend).

**Hasil tahap 3 (2026-10-13):** frontend berpindah utuh.

- Riwayat Rantai dan `chain.py root`/`amend`/`draft` sudah berjalan. `review_round.py commit` gugur.
- `tests/frontend/test_24_riwayat.py` baru (11 test). Test berbasis git dokumen ditulis ulang ke Riwayat dengan ID
  regresinya tetap: J27, J42–J53, E12–E14, L4.x, 15 F2–F15.
- Test baru 24 G2 (`test_gate_preconditions`, `test_08c_taskdir_state`), 24 K9 (`test_validate_review`,
  `test_09_robustness`), 24 K13 (`test_12_guard`), dan 24 K14/G5 (`test_15_sync_payload`).
- Suite penuh hijau dan lint 0 FAIL.

Selisih pelaksanaan terhadap peta:

- **Pemeriksaan `TUNTAS` dini dipertahankan, dengan kriteria disk.** Kriterianya: `REVIEW.md` `PASS`/`WARNING`,
  ledger tercentang penuh, nol brief `READY`, dan `REPORT.md` ada. Lalu salah satu dari dua: review segar dan
  laporan lolos `validate_report.py`, atau `head` review tidak lagi leluhur `HEAD`.
  - Alasannya: tanpa pemeriksaan ini, rantai tuntas yang di-squash-merge kehilangan commit `implement unit`-nya.
    Rantai itu lalu divonis `PENUTUP` selamanya (`test_j44_squash_rantai_tuntas_bukan_drift`).
  - Unit yang ditambah sesudah review normal tetap membasikan review tanpa menulis ulang riwayat, jadi rantai yang
    dilanjutkan tetap divonis lewat ledger.
- **Mutasi `chain.py` menolak akar yang sidiknya tidak utuh.** Ini berlaku untuk `approve`, `reopen`, `draft`, dan
  `escalate`, dan menjadi padanan 12 J47: dulu `reopen` menolak tree kotor; kini suntingan akar yang menggantung
  diselesaikan lewat `amend` lebih dulu, tidak dibawa diam-diam.
- **Kesegaran review menghitung semua commit pembawa kode sesudah `head`**, bukan hanya commit rantai `(<slug>)`.
  Yang dinilai berkas yang disentuh, bukan subjek yang diketik (09 E13). Commit yang hanya menyentuh `frontenddev/`
  atau `.claude/` tidak membasikannya.
- **`task_root_sha` jatuh ke commit penambahan `TASK.md` untuk taskdir era git tanpa `base_commit`.** Riwayatnya
  tetap ada sesudah `docs_git.py migrate`. Dengan begitu review ad-hoc `--target taskdir` dan laporan atas taskdir
  lama tetap punya rentang.
- **`strip_status_line` membuang baris `sidik_kontrak:` beserta newline di depannya.**
  `set_frontmatter_field` menambahkan field baru di ujung frontmatter, dan versi pertama menyisakan baris kosong.
  Akibatnya sidik brief bergeser sesudah approve. Bug ini tertangkap `test_c4_blocked_tanpa_remedi_menang_atas_ready`
  dan kini dipaku `test_strip_sidik_kontrak_baris_terakhir_frontmatter`.
- **`chain.py draft` menegakkan plafon revisi.** Dulu hanya `chain.py revisions` yang menghitung, dan commit
  `revise` ketiga tetap lolos.
- **Profil frontend tetap menulis baris `frontenddev/docs/**/.explore/`.** Penanda `frontenddev/docs/.gitignore`
  sudah menutupnya, sehingga baris itu kini lapis cadangan bagi repo yang belum membuka taskdir. Pola berjangkar di
  prosa explorer tetap dipaku 12 J4. Backend membuang baris `.explore/`-nya di tahap 2 karena backend tidak punya
  laci akar `.backenddev/` yang dipakai sebelum taskdir ada.
- **Pemulihan ronde tidak gugur di frontend.** Field `review` di kejadian `draft`/`approve` menggantikan trailer
  `Review-Round`, jadi `committed_rounds` dan `rebuild` tetap bekerja. K15 untuk frontend kosong.
- **`check_worktree` tidak lagi menerima `allow`/`own_action`.** Dokumen taskdir tidak pernah tampak kotor, jadi
  cabang "kotoran milik taskdir sendiri" dibuang beserta parameternya.
- **K2 (`WARN` tanpa `.claude/nataflow.json`)** baru berlaku di `docs_git.py status` dan check 10 prasyarat `task`
  frontend. Gerbang masuk backend menyusul di tahap 4.
