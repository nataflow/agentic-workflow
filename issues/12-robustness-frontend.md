# Langkah 12 — Robustness Plugin frontend (J1–J58)

Sumber: review robustness plugin `frontend` 2026-09-27 (lima penelusur paralel: hook & pagar, ledger & state,
prasyarat & verifikasi, validator dokumen, orkestrasi & prosa). Tiap temuan Tinggi/Sedang direproduksi di ruang
kerja sementara sebelum masuk berkas ini. Basis kode: commit `b293564` (suite 615 test hijau).

**Status (2026-09-27):** J1–J58 selesai (J10 batal) dalam lima tahap, masing-masing dengan test regresi (`tests/frontend/test_12_{guard,verification,validators,ledger,orchestration}.py`, `tests/backend/test_12_{guard,verification}.py`) yang merah di kode sebelum perbaikan. Suite penuh 1735 passed; lint M7 terhadap `b293564` lolos. Versi: frontend 0.9.0, backend 0.10.0 (guard, `detect.py`, `gate_text.py`, `run_verification.py`, `migrate_profile.py` dikembar).

## Tujuan

Menutup celah yang tersisa di plugin `frontend` sesudah 09/11. Empat pola yang berulang:

1. **Pagar yang dapat ditembus.** Allowlist reviewer menilai token pertama saja (`--no-pager` lalu opsi
   global), mencocokkan flag persis (`-O` vs `-O<cmd>`), dan tidak melihat tulisan subagent ke `.git/` atau
   berkas ter-ignore.
2. **Plafon tanpa jalan keluar** (padanan 11 H27/H28). Ronde reviewer hop hilir tidak dibuka ulang oleh reopen
   hop hulu; "amandemen akar" disebut jalan keluar tetapi tidak me-reset apa pun; verifikasi penutup merah tanpa
   berkas tidak punya rute.
3. **Hijau palsu.** Pipa menelan exit, galat kembar baseline dianggap warisan, brief `BLOCKED` dihitung pemikul
   SC/AC, baris SC/AC/temuan yang salah format hilang diam-diam alih-alih FAIL.
4. **Bukti yang dapat diakali atau rapuh.** Materai approve dapat diketik tangan, sha ledger tidak tahan
   rebase, bukti reviewer ronde lama diterima, `lane_tamper` dilewati dengan meniru subjek akar.

## Urutan pengerjaan

Tiap tahap: blast radius (tabel di bawah) → perbaikan + test regresi (merah di kode lama, hijau sesudahnya) →
suite penuh hijau → tahap berikutnya.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | J1–J9 (hook, `guard_bash.py` be/fe, `detect.py` be=fe, `gate_text.py`, pagar penulis fe) | Satu-satunya jalur eksekusi sembarang; berdiri sendiri. |
| 2 | J11–J13, J15–J23 (`run_verification.py` be=fe, `migrate_profile.py` be=fe, prasyarat, `precondition_lib.py`) | Verifikasi penutup dan prasyarat; dipakai validator dan ledger tahap 3–4. |
| 3 | J14, J24–J41 (validator dokumen, pengurai bersama `precondition_lib.py`, template) | Memakai `precondition_lib` tahap 2; mengubah pengurai SC/AC/frontmatter yang dibaca ledger. |
| 4 | J42–J53 (`chain.py`, `review_round.py`, `taskdir_state.py`, prasyarat `task`) | Mengubah bentuk materai approve dan fixture approval yang dipakai tahap 5. |
| 5 | J54–J58 + prosa J42/J43 (SKILL, dispatcher, rujukan, README, `flow/frontend.md`) | Orkestrasi; bergantung pada perilaku skrip tahap 1–4. Versi plugin dinaikkan di sini. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. **Lintas plugin** = berkas identik (dicek `cmp`)
atau pola sama di plugin lain. **Test tersentuh** = test yang ada dan harus tetap hijau atau disesuaikan.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| J1 | fe `hooks/guard_bash.py` (`READ_ONLY_GIT`) | fe `code-reviewer` Bash | tidak (be reviewer sudah menolak `git grep`) | — | Rendah: `git grep` diganti tool Grep |
| J2 | fe `guard_bash.py` `decide_bash` | fe reviewer | tidak (be menolak semua opsi global) | `test_09_robustness.py::test_e15_reviewer_boleh_membaca` (`git --no-pager show` tetap lolos) | Rendah |
| J3 | fe `decide_bash`, be `decide_reviewer_bash` | reviewer be/fe | **ya** — be juga kena | be `test_09_robustness.py` (`symbolic-ref -q --short HEAD` tetap lolos) | Rendah |
| J4 | fe `guard_bash.py` (pagar penulis), `precondition_lib.strip_explore_scratch`, `profile/SKILL.md` Phase 5, 5× `dispatcher/explorer.md`, README | implementor/explorer/doc-reviewer fe, ingest architect, TREE | tidak (be punya lease + B19) | `test_09_robustness.py::test_e15_agent_lain_…`, fixture `conftest.py` `.gitignore` | **Sedang**: brief sah yang menyentuh berkas ter-ignore kini ditolak |
| J5 | `hooks/detect.py` (`candidate_dirs`, glob workspace) | SessionStart be/fe, prasyarat profile be/fe | **ya** — identik | `tests/hooks/test_detect.py::test_detect_py_identik` | Rendah |
| J6 | fe `architect/scripts/validate_review.py` `_check_tree` | architect Phase 4 | tidak | `test_validate_review.py::test_e15_tree_*` | Rendah |
| J7 | fe `guard_bash.py` (`chain.py files` dicocokkan path resolve) | fe reviewer | tidak | `test_09_robustness.py` (param path `chain.py`) | Rendah |
| J8 | `guard_bash.py` `shell_tokens` be/fe (glob sebelum `--`) | semua agent terpagar | **ya** — identik | be `test_l34_guard_bash.py` | Rendah |
| J9 | `detect.py` `opted_out`, `gate_text.py` be/fe | SessionStart be/fe | **ya** | `tests/hooks/test_gate_text.py`, `test_detect.py` | Rendah |
| J11 | `_common/run_verification.py` (`bash -o pipefail`) | architect Phase 0/4 be/fe | **ya** — identik | `test_run_verification.py::test_copies_identical` | Sedang: perintah profil berpipa kini bisa merah |
| J12 | `run_verification.py` (`signatures`, `new_errors` multiset) | idem | **ya** | `test_run_verification.py`, be `test_11_robustness.py` H14 | Rendah |
| J13 | `run_verification.py` (field `head`), fe `validate_review.py --log`, architect prosa | architect Phase 0/4 | **ya** (field; penegakan fe) | `test_validate_review.py` helper `log()` | Sedang: log tanpa `baseline_head` FAIL |
| J14 | `plan/scripts/validate_briefs.py` Check V | plan, approve BRIEF, architect | tidak | — | Rendah |
| J15 | `precondition_lib.py` (`done_landed`, `brief_closure`), architect prasyarat | architect check 4/11, report, `taskdir_state` | tidak (be punya `done_sha`) | fixture `minor_chain_reviewed.sh` (membawa kode) | Rendah |
| J16 | architect prasyarat check 10 (`stack` brief = profil) | ingest architect | tidak | — | Rendah |
| J17 | `precondition_lib.py` (`dirty_lines`, `is_committed`, `check_worktree`) | semua gate, `chain.py approve`, `taskdir_state` | tidak | — | Rendah |
| J18 | `precondition_lib.lane_tamper` (replay riwayat) | semua `check_task_root`, `taskdir_state` | tidak | `test_09_robustness.py` E12 | Sedang: lane/sections yang berubah di luar `escalate` kini RUSAK |
| J19 | `precondition_lib.cli`, profile prasyarat `_resolve_patch` | seluruh CLI fe | tidak (be sudah, H21) | — | Nihil |
| J20 | architect prasyarat (pakai `brief_closure`) | ingest architect | tidak | — | Rendah |
| J21 | `migrate_profile.py`, `precondition_lib.check_profile` (pesan) | profile MIGRATE, semua gate | **ya** — identik | fe/be `test_migrate_profile.py` | Rendah |
| J22 | `precondition_lib.check_worktree` (`own_action`), prasyarat report/architect | report check 7, architect check 8 | tidak | — | Nihil |
| J23 | `run_verification.py` (NAMA ganda, `killpg`, log bertahap) | idem J11 | **ya** | `test_copies_identical`, `test_smoke.py` | Nihil |
| J24 | `validate_briefs.py` G/C/E (`carriers()`) | plan, approve BRIEF, architect | tidak | `test_review_round.py::test_D_…` | Sedang: batch APPEND yang bersandar pada brief BLOCKED FAIL |
| J25 | `task/scripts/validate_task.py` check 2 | akar `task`, `lead --amend` | tidak | — | Rendah |
| J26 | `validate_review.py` (`_check_findings`, `_check_done`, sel `\|`) | architect Phase 4, prasyarat report | tidak | `test_validate_review.py` | Rendah |
| J27 | `validate_briefs.py` Check M (`_blocked_since`) | plan APPEND | tidak | `test_validate_briefs_check_m.py` | Sedang |
| J28 | `precondition_lib.ac_rows`, `validate_doc.py`, `validate_briefs.py` C, `validate_review.py` `_check_ac` | contract, plan, architect | tidak | `test_validate_review.py::test_contoh_template_bagian_3_pass` | Rendah |
| J29 | `validate_briefs.py` R/E, `validate_doc.py`, `validate_task.py` (`inside_root`) | plan, contract, task | pola sama di be (belum diverifikasi) | — | Rendah |
| J30 | `review/scripts/validate_audit.py` `check_shape` | review `--write`, architect | tidak | `test_validate_audit.py` | Rendah |
| J31 | `precondition_lib.py` (`split_frontmatter`, `strip_status_line`, `read_status`) | semua pembaca frontmatter, `chain.py` drift | be sudah (05-3) | `test_parsing_l5.py`, `test_chain_reopen.py`, `test_08c_chain_newline.py` | Sedang |
| J32 | `validate_briefs.py` R/N/S (`CREATE` ganda, `unit` = NN) | plan | padanan 11 H7/H10 | `test_review_round.py::test_D_…` | Rendah |
| J33–J41 | `validate_briefs.py`, `validate_doc.py`, `validate_task.py`, `validate_review.py`, `validate_report.py`, `validate_audit.py`, `task-template.md`, `section_lines`/`read_section` | plan, contract, task, architect, report, review | tidak | `test_09_robustness.py` E16, `test_parsing_l5.py`, `test_validate_review.py`, `test_validate_audit.py` | Rendah |
| J42 | `precondition_lib.reopen_epoch` (hop ≥ gate + `eskalasi lane`) | `review_round`, `chain.approve`, `contract_review_ready` | padanan 11 H27 | `test_review_round.py` (assert epoch) | Sedang: rantai berjalan bisa menuntut satu ronde baru |
| J43 | `precondition_lib.revisions_since_open`, pesan `chain.py`/`review_round.py` | `chain revisions`, gate REVISE | tidak | `test_09_robustness.py` (revisi) | Rendah |
| J44 | `precondition_lib.verify_chain_row` (jangkar = commit approve + `Sidik:`), `chain.py` approve, `taskdir_state.classify` (TUNTAS sebelum DRIFT) | semua `check_chain_rows`, `chain verify/status`, `taskdir_state` | pola analyst E8 | `test_08c_taskdir_state.py`, `test_08c_chain_newline.py` | **Sedang**: materai lama tanpa `Sidik:` FAIL (reopen + approve ulang sekali) |
| J45 | `review_round.record`, `open` (cetak sidik), 2 dispatcher reviewer, `agents/doc-reviewer.md` | gate contract & plan | pola analyst E9/G3 | `conftest.fe_evidence`/`fe_round` → `test_review_round.py`, `test_chain_reopen.py`, `test_gate_preconditions.py` | Sedang: helper fixture berubah |
| J46 | `verify_chain_row` (subjek persis + `Sidik:` + `Review-Round:`), `Chain.approve` (tolak CR/LF) | sama dengan J44 | padanan 11 H17 | sama dengan J44 | Sedang |
| J47 | `Chain.reopen` (`require_clean`) | lead Phase 8, rute DRIFT | tidak | `test_chain_reopen.py` | Rendah |
| J48 | `Chain._approve_brief` (`locked_brief_problems`) | plan APPEND, architect | tidak | `test_review_round.py::test_D_…` | Rendah |
| J49 | task prasyarat (slug unik), `lead/SKILL.md` Phase 5 | task, lead | tidak | test prasyarat task (hitungan n/n) | Rendah |
| J50–J53 | `taskdir_state.classify`/`main`, `Chain` (`require_active`), `Rounds.save` | lead Phase 2, gate | tidak | `test_e1_non_utf8.py`, `test_08c_taskdir_state.py`, `test_review_round.py` | Rendah |
| J54 | `architect/SKILL.md` Phase 4 + Failure 5, `execution-protocol.md` §7 | architect Phase 4 | tidak (`run_verification.py` tidak disentuh) | — | Nihil |
| J55 | `architect/SKILL.md` Phase 4, `execution-protocol.md` §7, `check_worktree` hint | architect Phase 4, TREE | tidak | `test_validate_review.py` E15 | Rendah |
| J56 | 5× `dispatcher/explorer.md` (`git check-ignore`) | lead, ux, ui, contract, plan | tidak | `test_08c_text.py`, `test_lint_plugins.py` | Nihil |
| J57 | `lane-routing-matrix.md` §2/§6, README | lead monorepo | tidak | — | Nihil (guard stack = J16) |
| J58 | `chain.py`, `lead/SKILL.md`, `taskdir_state.py`, `precondition_lib.runnable_briefs`, `validate_briefs.py` Check D, 4× SKILL (`subagent_type`), `review/SKILL.md`, `plan/SKILL.md`, `gate_text.py`, README, `_CONTRACT.md` | lead, architect, plan, hook | `gate_text` per plugin | `test_08c_taskdir_state.py`, `tests/hooks/test_gate_text.py`, `test_validate_briefs_check_m.py` | Rendah: `EKSEKUSI` buntu kini `TERHENTI` |
| Rilis | `plugin.json` fe 0.8.0 → 0.9.0, be 0.9.0 → 0.10.0 (berkas kembar berubah), README, `flow/frontend.md` | — | be | `test_lint_plugins.py` (M7 terhadap `b293564`) | Nihil |

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| J1 | `grep` dikeluarkan dari allowlist git reviewer fe; `-O` di `diff`/`log` tinggal berarti orderfile (baca). | Selaras be; reviewer punya tool Grep. |
| J2 | Semua token sebelum subperintah git wajib `--no-pager`; token berawalan `-` lain ditolak. | Pagar menilai seluruh posisi opsi global, bukan `tok[1]` saja. |
| J3 | `symbolic-ref` hanya bentuk baca: ≤ 1 positional, tanpa `-d`/`--delete`/`-m`. Helper sama di be dan fe. | Menulis HEAD memindah branch tanpa jejak tree. |
| J4 | Lease implementor ala be **tidak** dibawa (L3.4 Opsi B tetap). Hook fe menolak Edit/Write implementor/explorer/doc-reviewer di luar repo, di `.git/**`, atau ter-ignore, kecuali laci berjangkar milik agent; explorer hanya `.explore/` taskdir atau `.frontenddev/explore/`; doc-reviewer hanya `REVIEW-PLAN.md`. Pola ignore profil dijangkarkan. | Menutup kelas tulisan yang tak terlihat `git status`. Tulisan `src/` di luar scope tetap divonis `verify_scope` sesudah unit (batas yang dinyatakan). |
| J5 | Akar crash ditutup (pola `.`/kosong dilewati, glob/`read_text` dibungkus), bukan melonggarkan kondisi diam. | Selaras H36. |
| J8 | Glob (`*?[`) sebelum `--` ditolak; false positive operator dalam kutip dan `-O orderfile` **tetap ditolak** (BATAL). | Fail-closed, keputusan 11 H1. |
| J9 | Pemisah opt-out `[\s,]+`; berkas kosong tetap berarti "tidak ada plugin yang boleh" (BATAL). Profil sendiri ber-`plugin` asing → teks REFRESH, bukan "milik plugin lain". | README mendefinisikan isi berkas sebagai daftar plugin yang boleh. |
| J10 | **BATAL.** | Prefix `agent_type` = `name` di `plugin.json` (`frontend`); `frontenddev:` hanya instalasi lama (Log 09: urusan `/plugin update`). |
| J11 | Perintah dijalankan lewat `bash -o pipefail -c`; tanpa `bash`, `--cmd` ber-`\|` ditolak exit 2. | Exit sebelah kiri pipa tidak boleh hilang. |
| J12 | Tanda bertanda-galat dibandingkan sebagai multiset; tanda ekor H14 tetap himpunan. | Galat kedua yang identik tetap galat baru. |
| J13 | Baseline mencatat `head`; `validate_review --log` menagih `baseline_head` leluhur commit `implement unit` pertama. | Padanan fe untuk kunci merge-base be (3a): akar `TASK.md`. |
| J15 | Transisi `→ DONE` sah hanya bila commit transisinya membawa berkas di luar `frontenddev/` dan `.claude/` (09 E18). | fe tidak punya koreksi brief-saja (11 H5). |
| J16 | `stack` brief ≠ `stack` profil → FAIL di ingest. | Klaim README; selaras `validate_review.py`. |
| J17 | `git status` gagal → `check_worktree` FAIL, `is_committed` False. | "Tree tak terbaca tidak pernah bersih". |
| J18 | `lane_tamper` me-replay riwayat `TASK.md` dari commit penambahan tertua; perubahan lane/sections hanya sah di commit `eskalasi lane` yang monoton. | Subjek dapat ditiru; riwayat tidak. |
| J21 | Berkas tujuan migrasi yang berisi beda → `MigrateError` sebelum apa pun dipindah; identik byte → salinan lama dibuang. | Tidak menimpa suntingan user. |
| J22 | `check_worktree(..., own_action=)` untuk report/architect; **BATAL** untuk `task` (check 3 sudah benar). | — |
| J14 | Operator shell di `verification` sah hanya bila perintah brief **sama persis** dengan perintah profil; sisa argumen sesudah prefiks ditolak bila memuat `;&\|$`\``<>` atau baris baru. | Perintah dijalankan `shell=True`. |
| J24 | Pemikul SC/AC/berkas kontrak hanya brief `READY`/`DONE`. | Selaras Check O. |
| J25 | Baris di `## Success Criteria` yang memuat `SC-\d` tetapi tidak cocok pola → FAIL (di akar; hilir dijaga `chain verify`). | Janji akar tidak boleh hilang diam-diam. |
| J26 | Baris/heading yang tampak data tetapi tak terurai → FAIL; sel dipecah dengan menghormati `\|`. | Verdict tidak boleh turun karena format. |
| J27 | Brief `READY` yang `files_touched`-nya beririsan dengan brief `BLOCKED` belum ter-remedi wajib `remedies`; re-entry kontrak menaikkan plafon hanya sesudah commit `unit <NN> BLOCKED` pertama rantai remedi itu. | Plafon tidak dapat dijebol lewat field yang dihilangkan atau reopen dini. |
| J28 | Satu pengurai `ac_rows()` bersama; baris ber-`AC-n` dengan sel < 4 → FAIL. | Satu fakta, satu pembaca. |
| J29 | Path absolut, segmen `..`, atau hasil `resolve()` di luar root → FAIL. | — |
| J31 | Ikut 05-3: kunci frontmatter ganda → `FrontmatterError`; `strip_status_line` hanya membuang baris `status:` pertama. | Satu nilai, satu vonis. |
| J32 | `CREATE` atas berkas yang sudah di-`CREATE` brief hulu non-BLOCKED → FAIL; `unit` = NN nama berkas. | Selaras 11 H7/H10. |
| J41 | AC `terbukti` wajib bukti (`_evidence_problem`); AC `test otomatis` wajib menunjuk berkas test rantai. README disesuaikan. | Klaim README "divonis dengan bukti" ditegakkan. |
| J42 | Epoch ronde gate = jumlah reopen yang membuka hop gate itu **atau hop di atasnya**, ditambah commit `eskalasi lane`. | Padanan 11 H27: dokumen hulu yang berubah membatalkan ronde hilir. |
| J43 | Hanya `draft` pertama sesudah akar/reopen yang menghentikan hitungan revisi; `draft` berikutnya = revisi. Amandemen akar tidak me-reset hitungan. | Menutup celah reset plafon; jalan keluar plafon = J43 prosa (H28). |
| J44 | Jangkar approval = commit approve (subjek `approve …` + `Hop: R`, terbaru sesudah reopen terakhir); sha ledger wajib sama dengan `Konten disetujui:`-nya; `Sidik:` (hash konten tanpa `status:`) di badan wajib cocok. Rantai TUNTAS/DITUTUP dinilai sebelum ledger. | Tahan rebase dan clone; squash rantai berjalan tetap fail-closed. |
| J46 | Materai sah hanya dengan subjek persis + `Sidik:` (+ `Review-Round:` untuk CONTRACT/BRIEF yang direview); `--answer` ber-CR/LF ditolak. Materai lama tanpa `Sidik:` → FAIL dengan remedi reopen + approve ulang. Validator tidak dijalankan ulang atas sha lama. | Padanan 11 H17; versi validator baru tidak boleh menggugurkan approval lama. |
| J45 | `open` mencetak sidik target; reviewer menggemakan `- Sidik:` (contract) / `sidik:` (`REVIEW-PLAN.md`); `record` mencocokkan dengan snapshot ronde terbuka. | Padanan analyst E9/G3. |
| J47 | `reopen` menuntut `require_clean(TASK, dokumen)`. | Selaras approve/escalate/abandon. |
| J48 | Pada hop `[~]`, brief yang `DONE`/`BLOCKED` di sha `was` wajib tetap sama status dan isinya. | Brief `BLOCKED` tidak pernah naik lagi (README Execution). |
| J49 | Slug yang sudah dipakai taskdir lain ditolak prasyarat `task`; lead menambah sufiks `-2`. | Commit rantai dikenali dari `(<slug>)`. |
| J50–J53 | Status selain `ACTIVE`/`ABANDONED` → RUSAK; `approve`/`reopen`/`escalate` menuntut `ACTIVE`; `save` pertama menulis `.bak`; verdict REVIEW asing → PENUTUP. | — |
| J43/J54 prosa | Plafon ronde/revisi/reopen/eskalasi habis → gate berhenti; lead bertanya `AskUserQuestion`: **rumuskan ulang di taskdir baru** (`chain.py abandon` taskdir lama) atau **hentikan**. Verifikasi penutup: exit 126/127 → REFRESH profil; `TIMEOUT` → ulang sekali dengan `--timeout` 3×, lalu `AskUserQuestion`; MERAH bertanda ekor log → sajikan ke user, brief perbaikan atau hentikan. fe tidak memakai opsi "terima tidak terverifikasi" be (`validate_review` memvonis `TIMEOUT` = `BLOCKED`). | Padanan 11 H15/H28. |
| J55 | Prasyarat architect dijalankan ulang sesudah verifikasi penutup, sebelum dispatch reviewer; tree kotor → sajikan path ke user. Pembersihan otomatis ditolak. | `lint --fix`/snapshot dapat memutasi berkas ter-track. |
| J57 | Koreksi prosa: satu repo, satu profil, satu `target_app` pada satu waktu. | Dukungan profil per-app tidak ada di skrip; guard stack (J16) menegakkan batasnya. |
| J58 | `EXPLORE_FACT` tanpa profil langsung dispatch explorer (H32); `REVIEW_AUDIT` tetap lewat PROFILE; plan tidak menjalankan perintah (baseline milik architect). | — |

---

## Tahap 1 — Pagar & hook

- [x] **J1 [Tinggi]** `git grep -O<cmd>` / `--open-files=` menjalankan shell dari reviewer fe (`guard_bash.py:44,89`; `BAD_FLAGS` hanya mencocokkan `-O` persis).
- [x] **J2 [Tinggi]** `git --no-pager --config-env=diff.external=… diff` lolos (`guard_bash.py:84-86` hanya memeriksa `tok[1]`); `--exec-path=`, `--git-dir=`, `--work-tree=` juga.
- [x] **J3 [Sedang]** `git symbolic-ref HEAD refs/heads/x` dan `--delete` lolos di reviewer be dan fe.
- [x] **J4 [Sedang]** Tulisan implementor/explorer/doc-reviewer fe ke `.git/hooks/`, `.env.local`, atau `src/.explore/` tidak terlihat `verify_scope --worktree`; `pre-commit` yang ditulis lalu dijalankan commit architect.
- [x] **J5 [Sedang]** `detect.py` crash pada `"workspaces": ["."]` / `pnpm-workspace.yaml` tak terbaca → hook diam, prasyarat profile traceback (be dan fe).
- [x] **J6 [Rendah]** TREE meloloskan semua `frontenddev/reviews/*.md`, bukan hanya `finding_source` taskdir ini.
- [x] **J7 [Rendah]** `chain.py files` dicocokkan `endswith` → `python3 /tmp/x/skills/_common/chain.py files` lolos.
- [x] **J8 [Rendah]** Glob `*?[` sebelum `--` tidak ditolak (nama berkas bisa menjadi flag).
- [x] **J9 [Rendah]** `.claude/workflow` berpemisah koma dibaca sebagai satu nama; profil sendiri ber-`plugin` asing memberi teks yang saling bertentangan.
- **J10 — BATAL** (lihat Keputusan).

## Tahap 2 — Verifikasi penutup & prasyarat

- [x] **J11 [Sedang]** `false | cat` → HIJAU (`run_verification.py:66`, `shell=True` tanpa `pipefail`).
- [x] **J12 [Sedang]** Galat baru yang kembar dengan galat baseline dianggap warisan (`:34-58`, perbandingan himpunan).
- [x] **J13 [Sedang]** Baseline tidak terikat commit; `.explore/` yang hilang membuat baseline diukur di atas unit yang sudah mendarat.
- [x] **J15 [Sedang]** Brief `DONE` sah hanya dari subjek commit (09 E18 belum dibawa ke fe).
- [x] **J16 [Sedang]** `stack` brief ≠ `stack` profil tidak ditolak di ingest.
- [x] **J17 [Sedang]** `.git/index` rusak → check 8 "nol perubahan menggantung" (`git()` menelan kegagalan).
- [x] **J18 [Sedang]** `lane_tamper` lolos bila commit meniru subjek `kunci TASK`; ledger bisa ikut dipangkas sehingga gate FLOW/UI terlewati.
- [x] **J19 [Rendah]** `cli()` belum menangkap `OSError` (padanan H21); `profile --mode patch` tanpa git → traceback.
- [x] **J20 [Rendah]** `remedies` siklik → `RecursionError` di ingest architect.
- [x] **J21 [Rendah]** `migrate_profile.py` menimpa berkas tujuan untracked; pesan menyarankan REFRESH alih-alih melanjutkan MIGRATE.
- [x] **J22 [Rendah]** `REPORT.md` tertunda milik rantai sendiri disebut "kerja user" (report, architect).
- [x] **J23 [Rendah]** `run_verification.py`: NAMA `--cmd` ganda saling menimpa; race `killpg`; log dibaca utuh ke memori.

## Tahap 3 — Validator dokumen

- [x] **J24 [Tinggi]** Brief `BLOCKED` dihitung pemikul SC/AC/berkas kontrak (Check G/C/E) → remedi yang tidak membawa AC lolos approve.
- [x] **J25 [Tinggi]** Baris SC salah format (`- [ ] SC-2:` tanpa `**`) hilang diam-diam dari task, doc, dan briefs.
- [x] **J26 [Tinggi]** Verdict `REVIEW.md` turun karena format (`###[P1-1]`, `[p1-1]`, `\|` di sel, backtick di kolom Brief).
- [x] **J14 [Sedang]** Check V menerima `pnpm test || true`.
- [x] **J27 [Sedang]** Plafon remedi Check M dijebol lewat `remedies` yang dihilangkan atau `reopen CONTRACT` sebelum unit berjalan.
- [x] **J28 [Sedang]** Baris AC tanpa pipa penutup tidak terlihat `validate_doc`.
- [x] **J29 [Sedang]** Path `../` / absolut diterima di `files_touched` dan bukti.
- [x] **J30 [Sedang]** `validate_audit` mengabaikan temuan tanpa judul; `## Summary` tidak dicocokkan.
- [x] **J31 [Sedang]** Kunci frontmatter ganda diterima diam-diam (05-3 hanya di be); `strip_status_line` membuang semua baris `status:`.
- [x] **J32 [Sedang]** `CREATE` ganda antar brief lolos; `unit` tidak dicocokkan dengan nama berkas.
- [x] **J33 [Rendah]** Anchor berisi dua simbol dianggap kosong.
- [x] **J34 [Rendah]** Contoh terisi `task-template.md` gagal di validatornya sendiri.
- [x] **J35 [Rendah]** `validate_report.py` memakai regex placeholder sendiri (`< 300 ms … > 0` FAIL).
- [x] **J36 [Rendah]** Bukti REVIEW yang menunjuk berkas biner memberi pesan "simpan ulang sebagai UTF-8".
- [x] **J37 [Rendah]** `validate_audit --only-status-changed` crash untuk path di luar root; berkas untracked PASS.
- [x] **J38 [Rendah]** Alat ukur `— verifikasi: test` tanpa objek lolos.
- [x] **J39 [Rendah]** Baris Verifikasi Penutup < 3 sel dilewati, tidak dihitung merah.
- [x] **J40 [Rendah]** Normalisasi `./` lama di `validate_briefs`; `validate_doc` tanpa `TASKDIR_PATTERN`; `section_lines`/`read_section` tidak mengenal pagar `~~~`.
- [x] **J41 [Rendah]** Bukti AC tidak ditagih (README berkata sebaliknya); AC `test otomatis` dengan berkas test yang belum ada tidak pernah ditagih ulang.

## Tahap 4 — Ledger & state

- [x] **J42 [Tinggi]** Plafon ronde plan tidak dibuka ulang oleh `reopen CONTRACT` (BRIEF `[ ]` tidak ikut kaskade) → approve BRIEF mustahil (padanan H27).
- [x] **J43 [Tinggi]** "Amandemen akar" sesudah plafon habis tidak me-reset apa pun; `draft` ulang justru me-reset hitungan revisi.
- [x] **J44 [Tinggi]** Sha ledger tidak tahan rebase/clone; rantai TUNTAS yang di-squash-merge divonis DRIFT.
- [x] **J45 [Sedang]** `review_round record` menerima laporan reviewer ronde lama.
- [x] **J46 [Sedang]** Commit berbadan `Konten disetujui:/Hop:` yang diketik tangan membuat `chain verify` PASS walau validator FAIL; `--answer` bernewline menyisipkan baris materai.
- [x] **J47 [Sedang]** `reopen` tanpa `require_clean` menyapu suntingan yang menggantung.
- [x] **J48 [Sedang]** Brief `BLOCKED` dihidupkan lewat reopen → `READY` → approve → loop.
- [x] **J49 [Sedang]** Dua taskdir bersolug sama saling mencampur berkas rantai.
- [x] **J50 [Rendah]** `status: DONE` di `TASK.md` → GATE ↔ FAIL bolak-balik.
- [x] **J51 [Rendah]** `reopen` sesudah `abandon` berhasil; `abandon` kedua memberi pesan "commit gagal (hook/lock?)".
- [x] **J52 [Rendah]** `save` pertama tidak menulis `.bak` padahal pesan state rusak menyuruh memulihkan dari `.bak`.
- [x] **J53 [Rendah]** `taskdir_state` masih memakai `.replace("./","")`; verdict REVIEW asing jatuh ke LAPORAN.

## Tahap 5 — Orkestrasi & prosa

- [x] **J54 [Tinggi]** Verifikasi penutup merah tanpa berkas (TIMEOUT, ekor log, 126/127) tidak punya rute; PENUTUP berulang (prosa H15 belum dibawa).
- [x] **J55 [Sedang]** Artefak build/test di tree membuat TREE FAIL → PENUTUP berulang.
- [x] **J56 [Sedang]** Dispatcher explorer memeriksa baris `.gitignore`, profile memakai `git check-ignore` → loop REFRESH.
- [x] **J57 [Sedang]** Profil per-app di monorepo dijanjikan prosa tetapi tidak didukung skrip.
- [x] **J58 [Rendah]** Bundel: pesan "Phase 7" di `chain.py`; RUSAK tanpa jalan keluar; `TERHENTI (DAG)` divonis `EKSEKUSI` (remedi ber-`depends_on` unit asalnya); `subagent_type` explorer tidak disebut; kontradiksi adapter hilang di review; `EXPLORE_FACT`/`REVIEW_AUDIT` dipaksa lewat PROFILE penuh (H32); plan Phase 1 menjalankan semua perintah; hitungan README.
- [x] **Prosa J42/J43**: jalan keluar plafon = `AskUserQuestion` taskdir baru / hentikan.
- [x] **Rilis**: README, `flow/frontend.md`, versi fe 0.9.0 dan be 0.10.0, Log Keputusan `ISSUES.md`.
