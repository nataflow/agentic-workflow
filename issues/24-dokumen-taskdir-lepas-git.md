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
| K15 | **Regresi tidak dihapus diam-diam.** Tiap test git-based ditulis ulang ke mekanisme materai dengan ID regresinya tetap. Yang memang gugur (09 E20 deteksi counter turun dari riwayat, rebuild trailer `Review-Round`) dicatat di bagian "Selisih pelaksanaan" beserta alasannya. | `xfail_strict` dan penandaan `regression("<ID>")` tetap bermakna. |
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
- **Deteksi counter yang diturunkan tangan (09 E20)** dan pemulihan hitungan ronde dari trailer git gugur (K15).

## Di luar cakupan

- Fitur tarik taskdir dari nataflow (`get_document`/`list_document`) untuk melanjutkan rantai dari mesin lain
  (keputusan user).
- Penanda `removed: true` untuk dokumen yang dihapus (G5). Butuh perubahan server: `upsert_document` menerima
  pembaruan metadata tanpa `content`.
- Dokumen tingkat repo (`backenddev/issues/`, `docs/api/`, `frontenddev/reviews/`), profil, dan plugin analyst,
  quickdev, product, fullstack, nataflow.
