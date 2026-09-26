# Langkah 6 — Test & CI (detail)

Versi rinci item L6.1–L6.3 dari `ISSUES.md`. Semua angka, keluaran, dan kutipan di bawah diambil dari repo pada commit `34684ee` dan dijalankan ulang pada 2026-09-24 (Python 3.13.5, git 2.47.3, pytest 9.1.1 di venv scratchpad).

## Tujuan

Memberi jaring pengaman mekanis sebelum dan selama perbaikan Langkah 1–8: tiap skrip Python dan hook punya test yang bisa dijalankan satu perintah, CI menolak regresi, dan satu linter statis menjaga manifest serta rujukan markdown tetap konsisten.

## Prinsip: test ditulis bersamaan dengan tiap langkah

- **Jangan menunggu Langkah 6 selesai.** Fondasi (`pytest.ini`, `tests/conftest.py`, smoke test) dikerjakan hari pertama, sebelum satu baris Langkah 1 disentuh. Sesudah itu, setiap PR perbaikan skrip membawa test-nya sendiri: satu test yang memuat skenario "Bukti" item itu (awalnya `xfail(reason="<ID>: …")`), lalu marker `xfail` dicabut di commit perbaikan. `xfail_strict = true` membuat test yang tiba-tiba lolos (XPASS) menjadi merah, sehingga marker tidak tertinggal.
- **Test karakterisasi sebelum refactor.** Sebelum L5.5 memindahkan kode ke `_common`, rekam keluaran `--json` tiap skrip prasyarat backenddev pada set fixture yang sama; refactor dianggap aman bila keluarannya identik kecuali untuk ID yang memang diperbaiki.
- **Tes hitam-kotak lewat subprocess.** Skrip dipanggil persis seperti skill memanggilnya (`python3 <path> --json` dengan cwd tertentu), bukan lewat import, agar bootstrap `sys.path` relatif `__file__` ikut teruji.

## Urutan pengerjaan

1. **L6.1 fondasi** (0,5 hari): `pytest.ini`, `tests/conftest.py`, tiga test contoh (sudah jalan, lihat L6.1 sub-tugas 6), smoke test parametrik untuk semua skrip.
2. **L6.3 prototipe lint** jadi `scripts/lint_plugins.py` dengan `--ignore` untuk adopsi bertahap (1 hari; prototipe sudah jalan).
3. **L6.2 CI** memakai keduanya (0,5 hari).
4. **Test per skrip mengikuti gelombang Langkah 1–5, lalu 8** (tabel "Urutan skrip yang dites lebih dulu").

## Dependensi dengan langkah lain

| Arah | Langkah/item | Alasan |
|---|---|---|
| L6.1 memblokir | seluruh item skrip L1–L5 dan 8 | "Selesai bila" tiap item skrip diverifikasi lewat test regresi |
| L6.1 memblokir | L5.5 (refactor `_common`) | butuh test karakterisasi sebagai pembanding |
| L6.3 bergantung pada | L7.1 (keputusan sumber versi) | menentukan semantik check M3/M4 |
| L6.3 hijau penuh bila | L7.1, L7.2, X1, L5.5 selesai | check M3/M4, M5, R2, S1 saat ini FAIL |
| L6.2 bergantung pada | L6.1, L6.3, keputusan host CI | repo belum punya remote (`git remote -v` kosong) |

## Estimasi usaha

Fondasi 0,5 hari · lint 1 hari · CI 0,5 hari · test per skrip ±6–8 hari total, tersebar di PR Langkah 1–8 (±1–2 jam per skrip prasyarat sederhana; 0,5–1 hari untuk `backenddev/plan/validate_briefs.py`, `frontenddev/plan/validate_briefs.py`, `frontenddev/_common/chain.py`, dan `frontenddev/_common/precondition_lib.py`).

## Definisi selesai langkah ini

- `python -m pytest` hijau di Python 3.11, 3.12, 3.13 (Linux) dan 3.13 (macOS), dengan minimal satu test normal dan satu test tepi untuk **tiap** skrip di inventaris, plus test regresi untuk setiap ID di kolom "Regresi" matriks yang sudah diperbaiki; ID yang belum diperbaiki berstatus `xfail` beralasan ID.
- Hook diuji di kedua OS: output kosong atau JSON valid, dan vonisnya sama dengan `detect_stack` Python (setelah L1.2).
- `python3 scripts/lint_plugins.py` exit 0 tanpa `--ignore`.
- Workflow CI aktif di host yang dipilih, dan branch utama dilindungi oleh keempat job.

## Keputusan yang dibutuhkan user

1. **Lokasi test:** `tests/` di root repo (disarankan, lihat koreksi L6.1) atau `src/plugins/<plugin>/tests/` seperti usulan `ISSUES.md`.
2. **Host CI:** repo tidak punya remote. YAML di L6.2 ditulis untuk GitHub Actions.
3. **Versi Python minimum untuk pengguna:** skrip sekarang butuh ≥3.9 (`str.removeprefix`, `Path.is_relative_to`). Bila L1.2 memakai `tomllib`, minimum naik ke 3.11. Tentukan apakah pengguna dengan Python 3.9/3.10 (mis. python3 bawaan Xcode Command Line Tools di macOS, perlu dicek di mesin target) tetap didukung; bila ya, tambah 3.9 ke matriks CI dan beri fallback untuk `tomllib`.

## Catatan implementasi (2026-09-25)

Keputusan user: (1) `tests/` di root repo, (2) GitHub Actions, (3) Python ≥3.9. Ketiganya tercatat di `Log Keputusan` `ISSUES.md` (lokal). Suite dijalankan dengan `uvx --python <v> pytest -q` di 3.9, 3.10, 3.11, 3.12, dan 3.13, dan semuanya hijau. Di 3.11–3.13 hasilnya 862 lulus + 2 xfail (A5, A6). Di 3.9/3.10 hasilnya 861 lulus + 1 skip (`test_cargo_workspace_members`, butuh `tomllib`) + 2 xfail. Lint: `python3 scripts/lint_plugins.py` → 24 FAIL, 28 WARN; dengan `--ignore M3,M4,M5,R2` → 0 FAIL.

Status per item:

- **L6.1: bagian repo selesai.** Sisa regresi mengikuti PR Langkah 7–8.
  - Test yang sudah ada (52 berkas dari L1–L5) dipindah dengan `git mv` dari `src/plugins/<p>/tests/` ke `tests/<p>/`. `conftest.py` akar ikut pindah ke `tests/`.
  - `pytest.ini`: `testpaths = tests`, `pythonpath = tests`, `--import-mode=importlib -ra`, `xfail_strict = true`, dan marker `regression(id)`.
  - `tests/test_smoke.py` mencakup **45** skrip ber-`__main__` × 4 keadaan repo (180 kasus). `test_inventaris_lengkap` memaksa skrip baru ikut terdaftar.
  - Smoke langsung menangkap satu bug: `migrate_profile.py --json` (kedua plugin) mencetak stdout kosong dan pesan palsu "bukan milik <plugin>" di repo tanpa profil lama. Bug ini diperbaiki. Kini penyebabnya dibedakan (hilang/rusak/asing), dan kegagalan di mode `--json` tetap berupa JSON.
  - Celah skrip tanpa test ditutup:
    - `tests/analyst/test_ticket.py`: siklus `check → review → approve → reopen → cancel` dan `validate_doc` kedua kind, dengan contoh terisi diambil dari bagian 3 template saat test berjalan (E1, E4, E5, E6, E8, E9), plus A5/A6 sebagai `xfail`.
    - `tests/frontenddev/test_gate_preconditions.py`: prasyarat `plan`, `ui-design`, `review`, dan `task`.
- **L6.2: workflow ditulis, belum aktif.** `.github/workflows/ci.yml` punya empat job:
  - `pytest`: 3.9–3.13 Linux + 3.13 macOS.
  - `hooks`: JSON manifest/hooks.json, shellcheck `git ls-files '*.sh'`, dan test hook.
  - `lint`: dengan `LINT_IGNORE` dan `--base origin/<base_ref>` di PR.
  - `plugin-validate`: `continue-on-error`.

  Workflow baru aktif setelah repo punya remote GitHub, dan branch protection diatur manual di sana. Syntax YAML sudah dicek dengan PyYAML, tetapi workflow belum pernah dijalankan di Actions.
- **L6.3: selesai sebagai skrip.** `exit 0` tanpa `--ignore` menunggu L7.1 (M3/M4), L7.2 (M5), dan X1 (R2). Semua check di tabel sub-tugas 1 ada, termasuk M7 dan F3, dengan satu test per ID (`tests/test_lint_plugins.py`). `test_repo_ini_hanya_gagal_di_check_yang_dijadwalkan` mengunci daftar check yang ditunda, dan daftar itu wajib dikosongkan bersamaan dengan `LINT_IGNORE` CI.

Penyimpangan dari rencana di bawah:

- **Tanpa `tests/builders.py` dan `tests/fixtures/<plugin>/`.** Helper tetap di `tests/conftest.py` (`make_repo`, `be_profile`, `fe_profile`, `fe_chain_repo`, …) mengikuti konvensi L1–L5. Fixture frontenddev ada di `tests/frontenddev/fixtures/`. Fixture fungsi `env`/`git_repo`/`Repo` dari draf `conftest.py` tidak diadopsi, sebab `GIT_ENV` + `make_repo` yang sudah dipakai 800+ test setara fungsinya.
- **Golden karakterisasi (sub-tugas 8) tidak direkam.** L5.5 sudah selesai tanpa golden (lihat catatan 05), jadi pembandingnya tidak lagi relevan.
- **Hook bukan shell lagi.** Sejak L1.2 hook adalah `detect.py`/`guard_bash.py`. Job `hooks` tidak menjalankan shellcheck terhadap hook, melainkan terhadap skrip fixture `.sh`. Matriks macOS dipertahankan untuk git/filesystem BSD. Test kontrak `hooks.json` (sub-tugas 7) tidak dibuat terpisah: smoke menjalankan `detect.py`/`guard_bash.py` persis seperti perintah `hooks.json`, dan H1 memeriksa targetnya.
- **Lint vs prototipe:**
  - S1 kini berbasis AST, sehingga docstring/komentar yang *menyebut* `.gemini` tidak dihitung. Tiga baris di `backenddev/_common/precondition_lib.py` sebelumnya jadi false positive. Terhadap `34684ee`, hasilnya tetap 8 skrip dengan jumlah baris yang sama dengan keluaran prototipe.
  - H1 memahami perintah `python3 "${CLAUDE_PLUGIN_ROOT}/…"`. Mode 100755 hanya ditagih untuk target yang dieksekusi langsung.
  - Check baru **T1** menolak `tests/`, `fixtures/`, `conftest.py`, dan `test_*.py` di dalam plugin (keputusan 1).
  - Regex path `${CLAUDE_PLUGIN_ROOT}` tidak lagi menelan backtick penutup, yang dulu membuat S2 tak pernah menyala.
  - `--json` mengeluarkan `{fail, warn, items}`.
  - S1 tidak lagi di-ignore karena L5.5 sudah bersih.
- **Versi action:** `checkout@v5`, `setup-python@v6`, `setup-node@v5`, dengan Node 22.
- **R2 = 17 baris** (15 di daftar X1 + `frontenddev/…/architect/references/execution-protocol.md:49` dan `:131` yang lahir di Langkah 3–4). Tetap milik X1.
- **Belum dikerjakan:** version bump. M7 terhadap `ba91e7c` menandai keempat plugin karena test dipindah keluar dan `migrate_profile` diubah. Sumber versi menunggu keputusan L7.1.

---

## Inventaris skrip

Dihitung ulang dari `git ls-files` dan `wc -l`; antarmuka diambil lewat AST (`argparse.add_argument`/`add_parser`) di scratchpad. Path relatif `src/plugins/`. `*` = argumen wajib.

**analyst — 3 berkas, 1.057 baris**

| # | Skrip | Baris | Antarmuka | Argumen CLI |
|---|---|---|---|---|
| 1 | `analyst/skills/_common/analyst_lib.py` | 337 | pustaka: `find_root`, `is_git_repo`, `git_commit`, `normalize_ticketdir`, `split_frontmatter`, `clean_value`, `set_frontmatter_field`, `sections`, `headings`, `split_parts`, `content_hash`, `meaningful`, `scan_leaks`, `format_report`, `report_json`; kelas `Checker` | — |
| 2 | `analyst/skills/_common/ticket.py` | 373 | subperintah `state`, `new`, `check`, `review`, `revise`, `approve`, `reopen`, `cancel` | global `--root`; state `--all --ready --json`; new `--slug* --type*{FEATURE,IMPROVEMENT,BUG}`; check `--gate*{elicit,spec} --ticketdir* --reopen --json`; review `--ticketdir* --verdict*{PASS,BLOCKED,DISPATCH_FAILED}`; revise `--ticketdir*`; approve `--ticketdir* --answer* --no-commit`; reopen/cancel `--ticketdir* --reason*` |
| 3 | `analyst/skills/_common/validate_doc.py` | 347 | kelas `DocValidator` (`elicit`: check 0–8; `ticket`: check 1–10) | `--kind*{elicit,ticket} --ticketdir* --root --json` |

**backenddev — 15 berkas, 8.118 baris**

| # | Skrip | Baris | Antarmuka | Argumen CLI |
|---|---|---|---|---|
| 4 | `backenddev/skills/_common/precondition_lib.py` | 107 | `nearest_existing_ancestor`, `probe_writable`, `profile_staleness` | — |
| 5 | `backenddev/skills/analyst/scripts/check_preconditions.py` | 470 | `PreconditionChecker`, 6 check (taskdir, profil, risk, chain×risk, artefak vs chain, git) | `--taskdir --risk --chain(auto) --root --json` |
| 6 | `backenddev/skills/architect/scripts/check_preconditions.py` | 521 | 6 check (taskdir, profil, kesiapan brief, git, dispatcher, lifecycle-recovery) | `--taskdir --base-branch --root --json` |
| 7 | `backenddev/skills/audit/scripts/check_preconditions.py` | 370 | 6 check (source root, profil, adapter, direktori issues, referensi/template, target scope) | `--target-scope --dimensions --root --json` |
| 8 | `backenddev/skills/business-analysis/scripts/check_preconditions.py` | 521 | 8 check | `--taskdir --chain --root --json` |
| 9 | `backenddev/skills/debug/scripts/check_preconditions.py` | 408 | 6 check | `--symptom --taskdir --scope-hint --root --json` |
| 10 | `backenddev/skills/document-api/scripts/check_preconditions.py` | 295 | 5 check | `--domain --base-branch --stack --root --json` |
| 11 | `backenddev/skills/plan/scripts/check_preconditions.py` | 802 | 8 check | `--taskdir --entry-mode --chain --risk --file-scope --root --json` |
| 12 | `backenddev/skills/plan/scripts/scaffold_brief.py` | 584 | kelas `MatrixTool`; mode tulis matriks / tulis brief dari spec / `--append` | `--taskdir* --write-matrix --spec --nn --risk --append --force --root` |
| 13 | `backenddev/skills/plan/scripts/validate_briefs.py` | 1.761 | kelas `BriefValidator`, check S, B, F, L, N, P, D, K, E, C, G, H, I, J; mode ronde review | `--taskdir* --brief --risk --file-scope --review-state --open-round --record-round --include-locked --root --json` |
| 14 | `backenddev/skills/profile/scripts/check_preconditions.py` | 291 | 5 check | `--mode --stack --profile-dir --root --json` |
| 15 | `backenddev/skills/report/scripts/check_preconditions.py` | 436 | 7 check | `--taskdir --base-branch --root --json` |
| 16 | `backenddev/skills/system-analysis/scripts/check_preconditions.py` | 602 | 8 check | `--taskdir --risk-level --chain --root --json` |
| 17 | `backenddev/skills/task/scripts/check_preconditions.py` | 470 | 6 check | `--taskdir --lane --chain --root --json` |
| 18 | `backenddev/skills/tech-lead/scripts/check_preconditions.py` | 480 | 6 check | `--root --re-entry --json` |

**frontenddev — 18 berkas, 5.663 baris**

| # | Skrip | Baris | Antarmuka | Argumen CLI |
|---|---|---|---|---|
| 19 | `frontenddev/skills/_common/precondition_lib.py` | 1.026 | 60 fungsi publik + `FrontmatterError`: deteksi (`detect_stack`, `is_next`, `candidate_manifests`, `read_profile_stack`, `load_profile`, `adapter_path`), git (`find_repo_root`, `git`, `git_ok`, `is_git_repo`, `dirty_lines`, `is_committed`, `last_commit`, `show_at`), frontmatter (`split_frontmatter`, `parse_frontmatter`, `read_status`, `set_frontmatter_field`, `strip_status_line`), TASK/ledger (`sc_ids`, `success_criteria`, `parse_sections`, `task_lane_sections`, `expected_rows`, `read_chain`, `replace_chain_row`, `verify_chain_row`, `check_chain_rows`, `lane_tamper`), rantai (`doc_drift`, `brief_set_drift`, `count_subjects`, `revisions_since_open`, `review_generation`, `chain_files`, `chain_commits`, `review_is_fresh`, `brief_closure`), check bersama (`check_taskdir`, `check_profile`, `check_adapter`, `check_plugin_files`, `check_worktree`, `check_task_root`, `check_pending`, `design_gate_checks`), laporan (`format_report`, `report_json`) | — |
| 20 | `frontenddev/skills/_common/chain.py` | 469 | subperintah `init`, `status`, `verify`, `approve`, `reopen`, `escalate`, `revisions`, `abandon`, `files`; kelas `Chain`, `ChainError`; `content_snapshot` | semua `--taskdir* --root`; approve/reopen/revisions `--row*{FLOW,UI,CONTRACT,BRIEF}`; verify `--rows`; approve `--answer*`; reopen/escalate/abandon `--reason*`; escalate `--lane*{FULL_PIPELINE,FAST_FORWARD,REFACTOR_ARCH,HOTFIX_MINOR} --sections*` |
| 21 | `frontenddev/skills/_common/review_round.py` | 184 | posisional `open`/`record`/`status`; kelas `Rounds` | `cmd* --taskdir* --gate*{contract,plan} --root --verdict{PASS,BLOCKED,DISPATCH_FAILED} --mechanical --semantic` |
| 22 | `frontenddev/skills/_common/validate_doc.py` | 355 | kelas `DocValidator` (`flow`, `ui`, `contract`); `outside_fences`, `body_after`, `sequential` | `--kind*{flow,ui,contract} --taskdir* --root --json` |
| 23 | `frontenddev/skills/architect/scripts/check_preconditions.py` | 348 | `PreconditionChecker` (9 entri `checks` pada input minimum) | `--taskdir* --brief --profile-dir --root --json` |
| 24 | `frontenddev/skills/architect/scripts/validate_review.py` | 271 | kelas `ReviewValidator` (frontmatter, struktur, SC, AC, temuan, verdict) | `--taskdir* --root --json` |
| 25 | `frontenddev/skills/contract/scripts/check_preconditions.py` | 91 | `design_gate_checks(row="CONTRACT")`, 9 check | `--taskdir* --profile-dir --root --json` |
| 26 | `frontenddev/skills/lead/scripts/taskdir_state.py` | 183 | `followups`, `classify`, `main` | `--taskdir --all --root --json` |
| 27 | `frontenddev/skills/plan/scripts/check_preconditions.py` | 251 | 9 check | `--taskdir* --mode* --profile-dir --root --json` |
| 28 | `frontenddev/skills/plan/scripts/validate_briefs.py` | 1.113 | kelas `BriefValidator`, check S, N, D, L, T, F, B, R, V, K, O, E, C, P, G, M; helper `forbidden_run`, `angle_placeholder`, `parse_frontmatter`, `read_section`, `strip_code_fences` | `--taskdir* --brief --contract --max-files(5) --profile-dir --root --json` |
| 29 | `frontenddev/skills/profile/scripts/check_preconditions.py` | 313 | 6 check | `--mode --stack --profile-dir --root --json` |
| 30 | `frontenddev/skills/report/scripts/check_preconditions.py` | 186 | 8 check | `--taskdir* --root --json` |
| 31 | `frontenddev/skills/report/scripts/validate_report.py` | 179 | kelas `ReportValidator`, check 1–6 | `--taskdir* --root --json` |
| 32 | `frontenddev/skills/review/scripts/check_preconditions.py` | 150 | 4 check (target `path`) | `--target* --range --path --taskdir --write --profile-dir --root --json` |
| 33 | `frontenddev/skills/task/scripts/check_preconditions.py` | 142 | 7 check | `--taskdir* --lane* --sections* --finding-source --profile-dir --root --json` |
| 34 | `frontenddev/skills/task/scripts/validate_task.py` | 220 | kelas `TaskValidator` | `--taskdir* --root --amend --json` |
| 35 | `frontenddev/skills/ui-design/scripts/check_preconditions.py` | 91 | `design_gate_checks(row="UI")`, 9 check | `--taskdir* --profile-dir --root --json` |
| 36 | `frontenddev/skills/ux-design/scripts/check_preconditions.py` | 91 | `design_gate_checks(row="FLOW")`, 9 check | `--taskdir* --profile-dir --root --json` |

**Hook shell — 2 berkas, 235 baris:** `backenddev/hooks/tech-lead-gate.sh` (104), `frontenddev/hooks/lead-gate.sh` (131). Keduanya mode git `100755`, membaca stdin JSON, menulis `hookSpecificOutput.additionalContext`.

Total Python: **36 berkas, 14.838 baris** (cocok dengan klaim ±14.800 di `ISSUES.md`). Jumlah check backenddev dihitung dari `def _check_N`; jumlah frontenddev dari panjang `checks[]` pada smoke run di bawah.

**Smoke baseline (sudah dijalankan):** 29 dari 33 skrip ber-CLI (belum: `ticket.py`, `chain.py`, `review_round.py`, `scaffold_brief.py`, yang butuh subperintah/fixture) dipanggil dengan argumen minimum × 4 keadaan repo (repo ber-commit, repo tanpa commit, detached HEAD, bukan repo git). Hasil: **nol traceback**; semua exit 1 dengan JSON valid, kecuali `taskdir_state.py --all --json` yang exit 0 dengan `[]`. Artinya kasus tepi E1–E3 tingkat dasar sudah aman di semua skrip; bug yang tersisa ada di jalur dengan fixture berisi (lihat matriks). Smoke ini layak jadi test parametrik pertama (`tests/test_smoke.py`).

## Urutan skrip yang dites lebih dulu

| Gelombang | Dikerjakan bersama | Skrip |
|---|---|---|
| 0 | hari pertama | fondasi + smoke parametrik semua skrip + 3 test contoh di L6.1 |
| 1 | Langkah 1 | kedua hook; `frontenddev/_common/precondition_lib.py` (`detect_stack`, `read_profile_stack`); `backenddev/profile`, `frontenddev/profile`, `backenddev/tech-lead` check (path profil) |
| 2 | Langkah 2 | `backenddev/report` check (L2.1), `backenddev/architect` check (L2.3, L2.4, L2.10), `scaffold_brief.py` dan `backenddev/validate_briefs.py` (L2.2, L2.7), `backenddev/task` check (L2.5), `backenddev/tech-lead` check (L2.8), `backenddev/analyst` check |
| 3 | Langkah 3 | skrip baru `run_verification.py`, `guard_bash.py`, `verify_scope.py`; `validate_review.py` (bagian verifikasi penutup) |
| 4 | Langkah 4 | `review_round.py`, `chain.py`, `frontenddev/precondition_lib.py` (`review_generation`, `chain_files`), `validate_review.py`, `validate_report.py`, `frontenddev/validate_briefs.py` (Check M), `frontenddev/architect` check |
| 5 | Langkah 5 | **karakterisasi semua 12 skrip prasyarat backenddev sebelum refactor L5.5**; lalu `system-analysis`/`plan`/`business-analysis`/`debug` check (L5.1–L5.4), `frontenddev` `validate_doc`/`validate_briefs`/`validate_task` (L5.6, L5.7), `precondition_lib` (L5.8), `taskdir_state.py`, `analyst_lib.py` (L5.9) |
| 6 | Langkah 8 | `ticket.py`, `analyst/validate_doc.py` (A1–A12); `audit`/`debug`/`document-api`/`profile` check (B3–B7, B10, B14, B16); `frontenddev/review` dan `profile` check (C10, C11, C14), `taskdir_state.py` (C4), `validate_task.py` (C5) |

---

## L6.1 [Tinggi] Tidak ada satu pun test otomatis

- [x] Selesai

**Plugin:** analyst, backenddev, frontenddev (+ hook) · **Estimasi:** fondasi 0,5 hari; matriks penuh ±6–8 hari tersebar · **Bergantung pada:** — · **Memblokir:** L6.2, refactor L5.5, verifikasi "Selesai bila" semua item skrip

### Konteks

Hampir semua temuan skrip di `ISSUES.md` (substring match, parser frontmatter, crash, cek terbalik) bisa ditangkap test sederhana. Tanpa test, perbaikan satu skrip bisa merusak skrip lain yang berbagi pola, dan refactor L5.5 (menyatukan kode yang disalin 13–14 kali) berjalan tanpa pembanding.

### Lokasi & kondisi saat ini

- 36 berkas Python (14.838 baris) dan 2 hook shell (235 baris), nol test: tidak ada `test_*.py`, `conftest.py`, `pytest.ini`, `pyproject.toml`, atau `.github/`.
- pytest tidak terpasang di mesin pengembang (`ModuleNotFoundError: No module named 'pytest'`); venv dipakai di scratchpad. `.gitignore` sudah memuat `.venv`, `__pycache__/`, `*.py[cod]`, `.eval`; belum memuat `.pytest_cache/`.
- Skrip membaca kandidat path di `Path.home()` (`~/.claude/plugins/…`, `~/.gemini/…`), jadi test wajib mengisolasi `HOME` supaya hasilnya tidak bergantung pada mesin.
- Menjalankan skrip di tempat menulis `__pycache__` ke dalam `src/` (saat ini 25 direktori `__pycache__`, 37 berkas `.pyc` lokal, semuanya tidak ter-track); test wajib memakai `PYTHONDONTWRITEBYTECODE=1`.
- Skrip fixture agen review masih ada di scratchpad sesi (sementara): `analyst/{happy,edge1..6,env}.sh`, `be-plan/{mkrepo.sh,fill.py}`, `fe-exec/build.sh`, beserta workspace contoh (`be-plan/café`, `be-plan/q"uote`, `be-plan/nogit`, …). Salin sebelum sesi berakhir bila ingin dijadikan dasar builder fixture.

**Koreksi terhadap ISSUES.md:** struktur usulan `src/plugins/<plugin>/tests/` akan ikut terkirim ke pengguna. Dokumentasi Claude Code (plugin-marketplaces, catatan "How plugins are installed"): *"when users install a plugin, Claude Code copies the plugin directory to a cache location, unless the plugin loads in place."* Dan plugins-reference: *"For copied plugins, each installed version is a separate directory in the cache … with its own copy of the plugin's files"*, tanpa mekanisme pengecualian berkas yang disebut. Test dan fixture sebaiknya di `tests/` pada root repo, di luar `source` plugin.

### Rencana perbaikan

1. **Struktur direktori**

   ```
   pytest.ini
   tests/
     conftest.py                 # fixture bersama (sub-tugas 3)
     test_smoke.py               # 29 skrip × 4 keadaan repo: tanpa traceback, JSON valid
     builders.py                 # pembangun artefak domain (sub-tugas 4)
     fixtures/
       analyst/                  # TICKET contoh (diambil dari bagian 3 template saat test)
       backenddev/               # index.json per stack, BRD/PRD/brief contoh, spec.json
       frontenddev/              # index.json per stack, TASK.md berledger, FLOW/UI/CONTRACT contoh
       manifests/                # package.json/go.mod/Cargo.toml/composer.json untuk hook
     analyst/test_ticket.py, test_validate_doc.py, test_analyst_lib.py
     backenddev/test_<skill>_preconditions.py, test_scaffold_brief.py, test_validate_briefs.py
     frontenddev/test_chain.py, test_review_round.py, test_validate_*.py, test_<skill>_preconditions.py
     hooks/test_session_start_hooks.py
   scripts/lint_plugins.py       # L6.3
   ```

   Tambah `.pytest_cache/` ke `.gitignore`.

2. **`pytest.ini`** (persis yang dipakai run di bawah):

   ```ini
   [pytest]
   testpaths = tests
   xfail_strict = true
   addopts = -ra
   markers =
       regression(id): test regresi untuk ID temuan di ISSUES.md
   ```

3. **`tests/conftest.py`** — fixture repo git sementara, helper tulis/commit (CRLF/BOM), runner subprocess dengan cwd yang bisa diatur, isolasi `HOME` dan konfigurasi git. Sudah dijalankan apa adanya:

   <details><summary>tests/conftest.py (176 baris)</summary>

   ```python
   """Fixture bersama test plugin agentic-workflow.

   Semua skrip dijalankan sebagai subprocess (persis seperti skill memanggilnya), dengan
   cwd yang bisa diatur dan HOME/konfigurasi git terisolasi supaya hasil tidak bergantung
   pada mesin pengembang (~/.gitconfig, ~/.claude/plugins, ~/.gemini).
   """
   from __future__ import annotations

   import json
   import os
   import subprocess
   import sys
   from dataclasses import dataclass, field
   from pathlib import Path
   from typing import Iterable, Optional

   import pytest

   REPO = Path(os.environ.get("AW_REPO", Path(__file__).resolve().parents[1])).resolve()
   PLUGINS = REPO / "src" / "plugins"


   # ── lokasi skrip ─────────────────────────────────────────────────────────────

   def skill_script(plugin: str, skill: str, name: str = "check_preconditions.py") -> Path:
       """`src/plugins/<plugin>/skills/<skill>/scripts/<name>`; skill `_common` tanpa `scripts/`."""
       base = PLUGINS / plugin / "skills" / skill
       path = base / name if skill == "_common" else base / "scripts" / name
       assert path.is_file(), f"skrip tidak ada: {path}"
       return path


   def hook_script(plugin: str, name: str) -> Path:
       path = PLUGINS / plugin / "hooks" / name
       assert path.is_file(), f"hook tidak ada: {path}"
       return path


   # ── lingkungan terisolasi ────────────────────────────────────────────────────

   @pytest.fixture
   def env(tmp_path_factory) -> dict:
       home = tmp_path_factory.mktemp("home")
       e = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "CLAUDE_"))}
       e.update({
           "HOME": str(home),
           "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),   # berkas kosong milik test
           "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
           "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
           "LC_ALL": "C.UTF-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
       })
       (home / ".gitconfig").write_text("", encoding="utf-8")
       return e


   # ── repo git sementara ───────────────────────────────────────────────────────

   @dataclass
   class Repo:
       path: Path
       env: dict
       commits: list = field(default_factory=list)

       def git(self, *args: str, check: bool = True) -> str:
           cp = subprocess.run(["git", "-C", str(self.path), *args], env=self.env,
                               capture_output=True, text=True)
           if check and cp.returncode:
               raise AssertionError(f"git {' '.join(args)} gagal: {cp.stderr}")
           return cp.stdout.strip()

       def write(self, rel: str, text: str, *, crlf: bool = False, bom: bool = False) -> Path:
           p = self.path / rel
           p.parent.mkdir(parents=True, exist_ok=True)
           data = text.replace("\n", "\r\n") if crlf else text
           p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + data.encode("utf-8"))
           return p

       def commit(self, msg: str = "test: fixture", paths: Optional[Iterable[str]] = None) -> str:
           self.git("add", "--", *(paths or ["."]))
           self.git("commit", "-q", "--allow-empty", "-m", msg)
           sha = self.git("rev-parse", "HEAD")
           self.commits.append(sha)
           return sha

       def detach(self) -> None:
           self.git("checkout", "-q", "--detach")


   def make_repo(base: Path, env: dict, name: str = "repo", *, git: bool = True,
                 initial_commit: bool = True) -> Repo:
       path = base / name
       path.mkdir(parents=True)
       repo = Repo(path, env)
       if git:
           repo.git("init", "-q", "-b", "main")
           if initial_commit:
               repo.write("README.txt", "fixture\n")
               repo.commit("chore: init")
       return repo


   @pytest.fixture
   def git_repo(tmp_path, env) -> Repo:
       """Repo git dengan satu commit awal di branch `main`."""
       return make_repo(tmp_path, env)


   @pytest.fixture
   def empty_git_repo(tmp_path, env) -> Repo:
       """`git init` tanpa commit (HEAD belum lahir)."""
       return make_repo(tmp_path, env, initial_commit=False)


   @pytest.fixture
   def plain_dir(tmp_path, env) -> Repo:
       """Direktori biasa, bukan repo git."""
       return make_repo(tmp_path, env, git=False)


   @pytest.fixture(params=["repo", "repo dengan spasi", "répo-ünïcode"])
   def odd_repo(request, tmp_path, env) -> Repo:
       """Repo git di path biasa, berspasi, dan unicode."""
       return make_repo(tmp_path, env, request.param)


   # ── runner ───────────────────────────────────────────────────────────────────

   @dataclass
   class Result:
       code: int
       out: str
       err: str

       def json(self) -> dict:
           try:
               return json.loads(self.out)
           except json.JSONDecodeError as exc:  # pesan jelas saat skrip crash di mode --json
               raise AssertionError(f"stdout bukan JSON ({exc}):\n{self.out}\n--- stderr ---\n{self.err}")

       def check(self, cid: int) -> dict:
           """Satu entri `checks[]` dari keluaran `--json` skrip prasyarat."""
           for c in self.json()["checks"]:
               if c["id"] == cid:
                   return c
           raise AssertionError(f"check {cid} tidak ada di keluaran")

       @property
       def traceback(self) -> bool:
           return "Traceback (most recent call last)" in self.err


   def _run(argv: list, *, cwd: Path, env: dict, stdin: Optional[str], timeout: int) -> Result:
       cp = subprocess.run(argv, cwd=cwd, env=env, input=stdin, capture_output=True,
                           text=True, timeout=timeout)
       return Result(cp.returncode, cp.stdout, cp.stderr)


   @pytest.fixture
   def run_script(env):
       """`run_script(path, *args, cwd=..., stdin=None)` → `Result` (python3 yang sama dengan pytest)."""
       def run(script: Path, *args: str, cwd: Path, stdin: Optional[str] = None,
               extra_env: Optional[dict] = None, timeout: int = 60) -> Result:
           e = {**env, **(extra_env or {})}
           return _run([sys.executable, str(script), *args], cwd=cwd, env=e, stdin=stdin, timeout=timeout)
       return run


   @pytest.fixture
   def run_hook(env):
       """Jalankan hook SessionStart dengan stdin `{"cwd": ...}` seperti Claude Code."""
       def run(script: Path, cwd: Path, *, payload: Optional[dict] = None) -> Result:
           body = json.dumps(payload if payload is not None else
                             {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(cwd)})
           return _run(["sh", str(script)], cwd=cwd, env=env, stdin=body, timeout=10)
       return run
   ```

   </details>

   Catatan: `AW_REPO` hanya dipakai untuk menjalankan test dari luar repo (seperti di scratchpad); di repo nilainya default `tests/..`. `GIT_CONFIG_GLOBAL` butuh git ≥2.32.

4. **`tests/builders.py`** — pembangun artefak domain, ditulis sekali dan dipakai banyak test:
   - `ticketdir(repo, slug, *, type, elicitation, status, body)` → `analyst/tickets/<stamp>-<slug>/TICKET.md`; varian `from_template("FEATURE")` yang mengambil contoh terisi dari bagian 3 `skills/spec/templates/ticket-template.md` dan `skills/elicit/templates/elicit-template.md` saat test berjalan, supaya fixture tidak basi ketika template berubah.
   - `be_profile(repo, stack="go", **override)` → `.claude/profile/index.json` + 8 berkas `.md` minimal (`commands.md` berisi tabel perintah); setelah L1.1 menulis ke `.claude/profile/backenddev/`.
   - `be_taskdir(repo, slug, *, chain, risk, lane, docs={"BRD.md": …})` → `backenddev/docs/<stamp>-<slug>/TASK.md` dengan frontmatter `chain:`/`risk:`/`lane:` dan ledger.
   - `be_briefs(repo, taskdir, spec)` → jalankan `scaffold_brief.py` dengan spec contoh (port dari `be-plan/fill.py`).
   - `fe_profile(repo, stack="react-vite")` → 10 berkas profil frontenddev.
   - `fe_taskdir(repo, slug, *, lane, sections)` → `TASK.md` lewat `chain.py init`, lalu dokumen FLOW/UI/CONTRACT dari contoh template dan `chain.py approve --answer "ya"`.
   - `manifest(repo, kind)` → `go.mod`/`package.json`/`Cargo.toml`/`composer.json`/`pom.xml` untuk 7 stack backend dan 4 stack frontend.

5. **Matriks test per skrip.** Kode kasus tepi wajib: **E1** bukan repo git · **E2** repo tanpa commit · **E3** detached HEAD · **E4** cwd di subdirektori · **E5** path berspasi/unicode · **E6** CRLF · **E7** BOM · **E8** berkas hilang · **E9** frontmatter rusak. "Semua" = E1–E9 yang relevan untuk skrip itu. Kolom Regresi memetakan ID `ISSUES.md` yang menyentuh skrip tersebut.

   **analyst**

   | Skrip | Kasus normal | Tepi | Regresi |
   |---|---|---|---|
   | `analyst_lib.py` (unit import) | `split_frontmatter` skalar/list/kutip/`#` dalam nilai; `content_hash` stabil terhadap spasi ujung; `scan_leaks` menangkap istilah, mengecualikan kutipan, URL, `domain_terms` | E6, E7, E9 | L5.9 (BOM), A5 (`set_frontmatter_field` tanpa pagar), A7 (nilai kosong jadi `[]`), A8 (nomor baris relatif body) |
   | `ticket.py` | new → TICKET dari template → check elicit → check spec → review PASS → approve (commit) → state READY → reopen → revise sampai plafon 3 → cancel | E1 (`git=tidak`, approve tanpa commit), E2, E3, E4, E5, E6, E7, E8 (ticketdir kosong → KOSONG), E9 | A1 (teks rute di `classify`), A2, A3, A4, A5, A6, A7, A10, A11, A12 (cek `type` tak tercapai) |
   | `validate_doc.py` | contoh terisi template `elicit` dan `ticket` lolos; tiap check digagalkan satu per satu | E6, E7, E8, E9 | A2 (dipakai `approve`), A9, L5.9 (pesan palsu "requester kosong") |

   **backenddev**

   | Skrip | Kasus normal | Tepi | Regresi |
   |---|---|---|---|
   | `_common/precondition_lib.py` | `probe_writable` menguji induk terdekat tanpa membuat direktori; `profile_staleness` SEGAR/BASI | E1, E5 | L5.5 (fungsi baru: `find_repo_root`, `resolve_taskdir`, `check_taskdir`, `read_frontmatter`, `dirty_paths`, `find_agent`, `format_text`/`to_json`), L1.1 (`PROFILE_DIR`) |
   | `analyst` check | 6 check PASS untuk setiap pasangan sah `RISK_CHAINS` | semua | L5.4 (`KeyError: 'PRD_CONVERSION'`; `chain: prd_brief`), L5.5 (`café.md` di taskdir), L1.1, L2.2, L2.13 |
   | `architect` check | brief READY berurutan → PASS; semua DONE + REVIEW sah → tindakan Fase 5 | semua | L2.2 (SUPERSEDED), L2.3 (REVIEW basi), L2.4 (`HALT.md`), L2.10, L5.9 (`status: DONE` di code fence), B3 (`--base-branch`), B6 (filter `.explore`, MERGE_HEAD) |
   | `audit` check | target scope path/diff, dimensi default | E1, E4, E5, E8 | B3, B4 (`source_root` absolut, vonis "diff/PR"), L5.5 |
   | `business-analysis` check | chain BRD_PRD_BRIEF + taskdir kanonik | semua | L5.2, L5.4, L5.5 |
   | `debug` check | taskdir kanonik, adapter memuat failure signatures | E1–E5, E8 | L5.2 (pola taskdir), B3, B5, B7, L5.5 |
   | `document-api` check | profil + adapter + `docs/api` bisa ditulis | E1, E4, E5, E8 | B3, B7, L5.5 |
   | `plan` check | entry mode PRD/LANGSUNG/RCA × chain | semua | L5.1, L5.2, L5.4, B10, L2.2, L5.5 |
   | `scaffold_brief.py` | `--write-matrix` dari spec sah → brief-01..NN; `--append` → NN+1; `--force` pada READY | E1, E4, E5, E6, E8 (laci `.explore` hilang) | L2.2, L2.7, B11 (`--spec -`), B13, B16 (spec list/bukan dict) |
   | `validate_briefs.py` | batch contoh lolos semua check; `--review-state/--open-round/--record-round` | E6, E7, E8, E9 | L2.2 (enum SUPERSEDED), L5.3 (4 kasus Bukti), B13, B16 (`--brief 1`, `--brief 0`), L2.7 |
   | `profile` check | manifest tiap 7 stack → stack benar | E1, E4, E5, E7 (`index.json` ber-BOM) | L1.1 (`package.json` apa pun lolos), B3, B7 |
   | `report` check | REVIEW + semua DONE + tree bersih → PASS | semua | L2.1 (check 7 sesudah reviewer), L2.2, L5.9 (H1 di code fence, BOM), B3, B6 |
   | `system-analysis` check | BRD APPROVED bersih → check 1 PASS (**test nyata di bawah**) | semua | L5.1, L5.2, L5.4, L5.5 |
   | `task` check | TASK.md belum ada; lane/chain sah | semua | L2.5 (resume saat TASK.md ada), L5.5, B16 (`--chain` tanpa nilai), L1.1 |
   | `tech-lead` check | profil lengkap + tree bersih → PASS; `--re-entry` mengizinkan zona artefak kotor | semua | L2.8 (`--read-only`), B14, L5.5, L1.1 |

   **frontenddev**

   | Skrip | Kasus normal | Tepi | Regresi |
   |---|---|---|---|
   | `_common/precondition_lib.py` (unit) | `detect_stack` 4 stack dan penolakan `next`; `read_profile_stack`; `parse_sections`; `read_chain`/`verify_chain_row` | E6, E7, E9 | L1.1, L1.2 (react tanpa Vite; klaim "byte-identik"), L4.1 (`review_generation`), L4.7 (`chain_files`), L5.7 (`is_manual`), L5.8 (`core.quotePath`, `-z`) |
   | `_common/chain.py` | init → approve FLOW/UI/CONTRACT/BRIEF → verify → reopen kaskade → escalate → abandon → files → revisions | E3, E4, E5, E6, E9 | L4.1 (skenario A dan B), L4.5 (reopen dengan frontmatter rusak), L4.9, C3 (CRLF) |
   | `_common/review_round.py` | open → record → status; plafon 2/generasi, 8/taskdir | E8 (state hilang), E9 (JSON rusak) | L4.1, L4.3 (state dipotong; `--mechanical -1`) |
   | `_common/validate_doc.py` | contoh terisi FLOW/UI/CONTRACT lolos | E6, E7, E9 | L5.6, C2 |
   | `architect` check | fase rantai, `depends_on`, kesegaran brief | semua | L4.6, C6 |
   | `validate_review.py` | contoh terisi review-template lolos | E6, E7, E9 | L4.2 (5 contoh Bukti), L3.3 (tabel vs log mesin), L5.7, L5.9 |
   | `contract`/`ui-design`/`ux-design` check | `design_gate_checks` per baris | semua | L1.1 |
   | `taskdir_state.py` | klasifikasi tiap keadaan taskdir | E1, E7, E8 | L5.9, C4 |
   | `plan` check | mode per lane | semua | — (L4.1/L4.8 lewat `review_round.py` dan SKILL) |
   | `validate_briefs.py` | batch contoh lolos 16 check | E6, E7, E9 | L4.4 (Check M), L5.6 |
   | `profile` check | 4 stack; Next ditolak | E1, E4, E5, E7 | L1.1 (FAIL atas profil plugin lain), L1.2, C10 |
   | `report` check | REVIEW PASS/WARNING ter-commit, semua brief tertutup | semua | L4.6 |
   | `validate_report.py` | contoh terisi lolos | E6, E7 | L4.2, L5.7, L5.8 (`app/(tabs)`), C12 |
   | `review` check | target range/path/taskdir | E1, E3, E4, E5 | C11, C14 |
   | `task` check | lane × sections sah; `finding_source` ter-commit | semua | L4.7 |
   | `validate_task.py` | contoh terisi lolos; `--amend` | E6, E7 | L5.6, L5.7, C5 |

   **Hook**

   | Skrip | Kasus normal | Tepi | Regresi |
   |---|---|---|---|
   | `backenddev/hooks/tech-lead-gate.sh` (→ `detect.py` sesudah L1.2) | 7 stack terdeteksi; profil ADA/BELUM ADA | E1, E4, E5 (cwd memuat `"`), stdin tanpa `cwd`, karakter kontrol | L1.1, L1.2 (7 kasus), L1.3, L1.4 |
   | `frontenddev/hooks/lead-gate.sh` | 4 stack; 4 cabang pesan (belum dibuat/tidak sah/tidak lengkap/lengkap) | idem | L1.1, L1.2 (6 kasus), L1.3, L1.4 |

   **Skrip baru dari langkah lain** — test ditulis dalam PR yang sama: `hooks/detect.py` (L1.2), `run_verification.py` (L3.3), `guard_bash.py` dan `verify_scope.py` (L3.4), `symbol_map.py` (L2.9, opsional), `validate_audit.py` (L4.7), `backenddev/_common/validate_doc.py` (B12).

6. **Test contoh yang sudah dijalankan** terhadap skrip saat ini. Test yang mereproduksi bug ditandai `xfail` dengan ID temuan.

   <details><summary>tests/analyst/test_ticket.py</summary>

   ```python
   """analyst `skills/_common/ticket.py` — subperintah new/state/cancel."""
   import json
   import re

   import pytest

   from conftest import skill_script

   TICKET = skill_script("analyst", "_common", "ticket.py")
   DIR_RE = re.compile(r"^\d{10}-cicilan$")


   def ticketdirs(root):
       base = root / "analyst" / "tickets"
       return sorted(p.name for p in base.iterdir()) if base.is_dir() else []


   def test_new_di_luar_repo_git(plain_dir, run_script):
       r = run_script(TICKET, "new", "--slug", "cicilan", "--type", "FEATURE", cwd=plain_dir.path)
       assert r.code == 0, r.out + r.err
       assert "NEW PASS" in r.out and "git=tidak" in r.out
       [name] = ticketdirs(plain_dir.path)
       assert DIR_RE.match(name)


   def test_new_path_berspasi_dan_unicode(odd_repo, run_script):
       r = run_script(TICKET, "new", "--slug", "cicilan", "--type", "BUG", cwd=odd_repo.path)
       assert r.code == 0, r.out + r.err
       assert "git=ya" in r.out
       assert len(ticketdirs(odd_repo.path)) == 1


   def test_new_dari_subdirektori_menulis_di_root_git(git_repo, run_script):
       sub = git_repo.path / "src" / "features"
       sub.mkdir(parents=True)
       r = run_script(TICKET, "new", "--slug", "cicilan", "--type", "FEATURE", cwd=sub)
       assert r.code == 0, r.out + r.err
       assert len(ticketdirs(git_repo.path)) == 1          # di root git, bukan di cwd
       assert not (sub / "analyst").exists()


   @pytest.mark.xfail(reason="A6: NEW PASS mencetak path relatif root tanpa `root=<abs>`; "
                             "`git add` relatif cwd salah alamat bila cwd di subdirektori")
   def test_new_dari_subdirektori_mencetak_root_absolut(git_repo, run_script):
       sub = git_repo.path / "src"
       sub.mkdir()
       r = run_script(TICKET, "new", "--slug", "cicilan", "--type", "FEATURE", cwd=sub)
       assert f"root={git_repo.path}" in r.out


   @pytest.mark.xfail(reason="A5: cancel menempel `status: CANCELLED` di akhir body berkas "
                             "tanpa frontmatter, melapor PASS, tetapi state tetap RUSAK")
   def test_cancel_berkas_tanpa_frontmatter(git_repo, run_script):
       rel = "analyst/tickets/2609240000-cicilan"
       git_repo.write(f"{rel}/TICKET.md", "# Cicilan\n\n## Catatan Elisitasi\n\nisi\n")
       r = run_script(TICKET, "cancel", "--ticketdir", rel, "--reason", "batal", cwd=git_repo.path)
       state = run_script(TICKET, "state", "--all", "--json", cwd=git_repo.path).json()
       [row] = state["ticketdirs"]
       # Perilaku benar: cancel ditolak dengan pesan jelas, ATAU tiket benar-benar DIBATALKAN.
       assert r.code != 0 or row["state"] == "DIBATALKAN", (r.out, row)


   @pytest.mark.xfail(reason="L5.9: TICKET.md ber-BOM dibaca tanpa frontmatter → RUSAK")
   def test_state_ticket_ber_bom(git_repo, run_script):
       rel = "analyst/tickets/2609240000-cicilan"
       git_repo.write(f"{rel}/TICKET.md",
                      "---\ntype: FEATURE\nelicitation: OPEN\nstatus: DRAFT\n---\n\n"
                      "# Cicilan\n\n## Catatan Elisitasi\n\nisi\n", bom=True)
       [row] = run_script(TICKET, "state", "--json", cwd=git_repo.path).json()["ticketdirs"]
       assert row["state"] == "ELISITASI", row
   ```

   </details>

   <details><summary>tests/backenddev/test_system_analysis_preconditions.py</summary>

   ```python
   """backenddev `system-analysis/scripts/check_preconditions.py` — check 1 (BRD), 3 (taskdir), 6 (git)."""
   import pytest

   from conftest import skill_script

   SCRIPT = skill_script("backenddev", "system-analysis")
   TASKDIR = "backenddev/docs/2609240000-order-refund"


   def brd(status: str, body: str = "") -> str:
       return f"---\ntitle: Refund\nstatus: {status}\n---\n\n# BRD Refund\n\n{body}\n"


   def run(run_script, repo, *extra, cwd=None, taskdir=TASKDIR):
       return run_script(SCRIPT, "--taskdir", taskdir, "--risk-level", "MAJOR",
                         "--chain", "BRD_PRD_BRIEF", "--json", *extra, cwd=cwd or repo.path)


   def test_brd_approved_bersih_pass(git_repo, run_script):
       git_repo.write(f"{TASKDIR}/BRD.md", brd("APPROVED"))
       c = run(run_script, git_repo).check(1)
       assert c["status"] == "PASS", c


   def test_brd_approved_crlf_pass(git_repo, run_script):
       git_repo.write(f"{TASKDIR}/BRD.md", brd("APPROVED"), crlf=True)
       assert run(run_script, git_repo).check(1)["status"] == "PASS"


   def test_brd_draft_fail(git_repo, run_script):
       git_repo.write(f"{TASKDIR}/BRD.md", brd("DRAFT"))
       c = run(run_script, git_repo).check(1)
       assert c["status"] == "FAIL" and "DRAFT" in c["summary"]


   @pytest.mark.xfail(reason="L5.1: `status: draft` dicari sebagai substring di seluruh isi")
   def test_brd_approved_dengan_kalimat_status_draft_di_body(git_repo, run_script):
       git_repo.write(f"{TASKDIR}/BRD.md", brd("APPROVED", "Order dengan status: DRAFT ditolak."))
       assert run(run_script, git_repo).check(1)["status"] == "PASS"


   @pytest.mark.xfail(reason="L5.1: `status: approved` di body meloloskan BRD berstatus REVIEW")
   def test_brd_review_dengan_kalimat_refund_status_approved(git_repo, run_script):
       git_repo.write(f"{TASKDIR}/BRD.md", brd("REVIEW", "Refund status: APPROVED dikirim ke user."))
       assert run(run_script, git_repo).check(1)["status"] == "FAIL"


   @pytest.mark.xfail(reason="L5.2: cek taskdir memakai OR + re.search tak berjangkar; `src` lolos")
   def test_taskdir_bukan_kanonik_ditolak(git_repo, run_script):
       (git_repo.path / "src").mkdir()
       assert run(run_script, git_repo, taskdir="src").check(3)["status"] == "FAIL"


   def test_bukan_repo_git_check6_fail(plain_dir, run_script):
       plain_dir.write(f"{TASKDIR}/BRD.md", brd("APPROVED"))
       c = run(run_script, plain_dir).check(6)
       assert c["status"] == "FAIL", c


   def test_cwd_subdirektori_meresolusi_root_git(git_repo, run_script):
       sub = git_repo.path / "internal" / "order"
       sub.mkdir(parents=True)
       git_repo.write(f"{TASKDIR}/BRD.md", brd("APPROVED"))
       r = run(run_script, git_repo, cwd=sub)
       assert r.json()["root"] == str(git_repo.path)
       assert r.check(1)["status"] == "PASS"
   ```

   </details>

   <details><summary>tests/hooks/test_session_start_hooks.py</summary>

   ```python
   """Hook SessionStart backenddev/frontenddev: bentuk JSON dan vonis deteksi stack."""
   import json

   import pytest

   from conftest import hook_script

   BACKEND = hook_script("backenddev", "tech-lead-gate.sh")
   FRONTEND = hook_script("frontenddev", "lead-gate.sh")


   def context(result) -> str:
       assert result.code == 0, result.err
       assert result.out.strip(), "hook diam (stdout kosong)"
       data = json.loads(result.out)                       # JSON wajib valid
       hso = data["hookSpecificOutput"]
       assert hso["hookEventName"] == "SessionStart"
       return hso["additionalContext"]


   def test_backend_go_gin_menyuntik_json_valid(git_repo, run_hook):
       git_repo.write("go.mod", "module example.com/svc\n\nrequire github.com/gin-gonic/gin v1.10.0\n")
       ctx = context(run_hook(BACKEND, git_repo.path))
       assert "stack terdeteksi: go" in ctx


   def test_backend_diam_di_repo_tanpa_manifest(git_repo, run_hook):
       r = run_hook(BACKEND, git_repo.path)
       assert r.code == 0 and r.out == ""


   def test_frontend_react_vite_menyuntik_json_valid(git_repo, run_hook):
       git_repo.write("package.json", json.dumps({"dependencies": {"react": "^19"},
                                                  "devDependencies": {"vite": "^6"}}))
       ctx = context(run_hook(FRONTEND, git_repo.path))
       assert "stack: react-vite" in ctx


   @pytest.mark.xfail(reason="L1.2: `\"express\"` di devDependencies (mock server Vite) "
                             "membuat hook backend ikut menyala di repo frontend")
   def test_backend_diam_bila_express_hanya_devdependency(git_repo, run_hook):
       git_repo.write("package.json", json.dumps({"dependencies": {"react": "^19"},
                                                  "devDependencies": {"vite": "^6", "express": "^4"}}))
       assert run_hook(BACKEND, git_repo.path).out == ""


   @pytest.mark.xfail(reason="L1.2: hook frontend hanya memeriksa $cwd, bukan toplevel git")
   def test_frontend_menyala_dari_subdirektori(git_repo, run_hook):
       git_repo.write("package.json", json.dumps({"dependencies": {"react": "^19"},
                                                  "devDependencies": {"vite": "^6"}}))
       sub = git_repo.path / "src" / "features"
       sub.mkdir(parents=True)
       assert "react-vite" in context(run_hook(FRONTEND, sub))
   ```

   </details>

   Keluaran nyata (`AW_REPO=<repo> .venv/bin/python -m pytest -p no:cacheprovider`):

   ```
   ============================= test session starts ==============================
   platform linux -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
   rootdir: /tmp/claude-1000/-home-fakhrulnugroho-work-natakode-nataflow-agentic-workflow/d3694b5e-a45f-49bf-8ba3-1a983c306ba0/scratchpad/detail-06
   configfile: pytest.ini
   testpaths: tests
   collected 21 items

   tests/analyst/test_ticket.py .....xxx                                    [ 38%]
   tests/backenddev/test_system_analysis_preconditions.py ...xxx..          [ 76%]
   tests/hooks/test_session_start_hooks.py ...xx                            [100%]

   =========================== short test summary info ============================
   XFAIL tests/analyst/test_ticket.py::test_new_dari_subdirektori_mencetak_root_absolut - A6: NEW PASS mencetak path relatif root tanpa `root=<abs>`; `git add` relatif cwd salah alamat bila cwd di subdirektori
   XFAIL tests/analyst/test_ticket.py::test_cancel_berkas_tanpa_frontmatter - A5: cancel menempel `status: CANCELLED` di akhir body berkas tanpa frontmatter, melapor PASS, tetapi state tetap RUSAK
   XFAIL tests/analyst/test_ticket.py::test_state_ticket_ber_bom - L5.9: TICKET.md ber-BOM dibaca tanpa frontmatter → RUSAK
   XFAIL tests/backenddev/test_system_analysis_preconditions.py::test_brd_approved_dengan_kalimat_status_draft_di_body - L5.1: `status: draft` dicari sebagai substring di seluruh isi
   XFAIL tests/backenddev/test_system_analysis_preconditions.py::test_brd_review_dengan_kalimat_refund_status_approved - L5.1: `status: approved` di body meloloskan BRD berstatus REVIEW
   XFAIL tests/backenddev/test_system_analysis_preconditions.py::test_taskdir_bukan_kanonik_ditolak - L5.2: cek taskdir memakai OR + re.search tak berjangkar; `src` lolos
   XFAIL tests/hooks/test_session_start_hooks.py::test_backend_diam_bila_express_hanya_devdependency - L1.2: `"express"` di devDependencies (mock server Vite) membuat hook backend ikut menyala di repo frontend
   XFAIL tests/hooks/test_session_start_hooks.py::test_frontend_menyala_dari_subdirektori - L1.2: hook frontend hanya memeriksa $cwd, bukan toplevel git
   ======================== 13 passed, 8 xfailed in 0.96s =========================
   ```

   Setiap xfail sudah dicek gagal karena alasan yang benar (`--runxfail --tb=line`), bukan karena fixture rusak. Potongan asli:
   - A6: `assert 'root=/tmp/…/repo' in 'NEW PASS: analyst/tickets/2609241954-cicilan · git=ya\n'`
   - A5: `('CANCEL PASS: analyst/tickets/2609240000-cicilan (TICKET.md)` … `assert (0 != 0 or 'RUSAK' == 'DIBATALKAN'`
   - L5.9: `{'ticketdir': 'analyst/tickets/2609240000-cicilan', 'type': '-', 'title': 'Cicilan', 'state': 'RUSAK', ...}`
   - L5.1 (dua test): `assert 'FAIL' == 'PASS'` dan `assert 'PASS' == 'FAIL'`; L5.2: `assert 'PASS' == 'FAIL'`
   - L1.2 express: `assert '{"hookSpecif...gate>\\n"}}\n' == ''`; L1.2 subdirektori: stdout kosong

7. **Test hook sebagai kontrak.** Selain test vonis, satu test membaca `hooks/hooks.json` tiap plugin, mengganti `${CLAUDE_PLUGIN_ROOT}` dengan path plugin, menjalankan perintahnya untuk setiap direktori di `tests/fixtures/manifests/*`, lalu menuntut stdout kosong atau JSON valid. Test ini tetap berlaku sesudah L1.2 mengganti isi hook dengan `detect.py`. Tambahkan fixture `profile-tab` (stack berisi tab mentah) di PR L1.2; hari ini kasus itu terbukti menghasilkan JSON rusak (`Invalid control character at: line 1 column 139 (char 138)`).

8. **Test karakterisasi (sebelum L5.5).** Helper `assert_golden(result, name)` membandingkan `result.json()` (tanpa field `root`) dengan `tests/golden/<name>.json`; opsi `--update-golden` menulis ulang. Rekam untuk 12 skrip prasyarat backenddev × fixture {kosong, profil lengkap, taskdir DRAFT, taskdir siap eksekusi}. Refactor lolos bila diff golden hanya menyentuh check yang berubah karena ID yang diperbaiki di PR itu.

9. **Cara menjalankan**

   ```sh
   python3 -m venv .venv && . .venv/bin/activate && pip install pytest
   python -m pytest                        # semua
   python -m pytest tests/backenddev -k system_analysis
   python -m pytest --runxfail --tb=line   # lihat bug terbuka gagal apa adanya
   ```

### Selesai bila

- Struktur di sub-tugas 1 ada di repo dan `python -m pytest` hijau (xfail beralasan ID dihitung hijau).
- Tiap baris matriks punya minimal satu test normal dan satu test tepi; tiap ID di kolom Regresi punya test (xfail sampai diperbaiki).
- Smoke test parametrik mencakup ke-33 skrip ber-CLI (36 dikurangi 3 pustaka) di 4 keadaan repo.
- Test karakterisasi backenddev terekam sebelum PR L5.5 pertama.

### Risiko & catatan

- **Fixture yang meniru template bisa basi.** Ambil contoh terisi dari template saat test berjalan (sub-tugas 4), jangan disalin.
- **Test lambat karena git.** Tiap test membuat repo sendiri (±50 ms). Untuk ratusan test, pakai fixture `scope="module"` yang di-`git clone --local` per test, atau `pytest-xdist` di CI.
- **`from conftest import …`** bekerja karena pytest menaruh direktori `conftest.py` di `sys.path` (mode import bawaan). Bila nanti memakai `--import-mode=importlib`, pindahkan helper ke `tests/helpers.py`.
- **Hook bergantung pada `sh`, `sed`, `grep`, `awk` sistem.** Perilaku BSD (macOS) berbeda dari GNU; karena itu matriks CI memuat macOS sampai L1.2 memindahkan deteksi ke Python.

---

## L6.2 [Sedang] CI

- [ ] Selesai

**Plugin:** repo (keempat plugin) · **Estimasi:** 0,5 hari · **Bergantung pada:** L6.1, L6.3, keputusan host CI · **Memblokir:** — (menjadi gerbang merge untuk semua langkah lain)

### Konteks

Test dan lint baru berguna bila dijalankan otomatis di setiap perubahan. Hook shell perlu dijalankan di dua keluarga utilitas (GNU dan BSD), dan skrip harus tetap jalan di versi Python yang didukung.

### Lokasi & kondisi saat ini

- Tidak ada `.github/` maupun konfigurasi CI lain; `git remote -v` kosong.
- **shellcheck 0.11.0** (dipasang lewat `pip install shellcheck-py` di venv scratchpad) terhadap kedua hook: hanya **7 temuan SC2016 (info)**, semuanya backtick markdown yang memang sengaja literal di dalam kutip tunggal. `shellcheck -s sh -S warning` → exit 0; `shellcheck -s sh -e SC2016` → exit 0. Tanpa opsi → exit 1.
- **Validasi JSON output hook**: output normal valid (test di L6.1), tetapi `index.json` dengan tab mentah di `stack` menghasilkan JSON rusak (`python3 -m json.tool` → `Invalid control character at: line 1 column 139 (char 138)`), mengonfirmasi L1.2.
- **Versi Python**: fitur termuda yang dipakai skrip sekarang adalah `str.removeprefix` (1 tempat, `analyst_lib.py`) dan `Path.is_relative_to` (6 skrip backenddev), keduanya 3.9. Belum ada `tomllib`, `match`, atau generik bawaan `list[...]` saat runtime.
- Dokumentasi Claude Code menyediakan validator resmi (plugin-marketplaces, "Validation and testing"): *"From your marketplace directory, validate the JSON syntax: `claude plugin validate .`"*.

### Rencana perbaikan

1. Tambah `.github/workflows/ci.yml` (asumsi GitHub Actions):

   ```yaml
   name: ci

   on:
     push:
       branches: [main]
     pull_request:

   permissions:
     contents: read

   concurrency:
     group: ci-${{ github.ref }}
     cancel-in-progress: true

   env:
     PYTHONDONTWRITEBYTECODE: "1"

   jobs:
     pytest:
       name: pytest (py${{ matrix.python }}, ${{ matrix.os }})
       runs-on: ${{ matrix.os }}
       strategy:
         fail-fast: false
         matrix:
           os: [ubuntu-latest]
           python: ["3.11", "3.12", "3.13"]
           include:
             - os: macos-latest        # sh/sed/grep BSD untuk hook
               python: "3.13"
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: ${{ matrix.python }}
         - run: python -m pip install --upgrade pip pytest
         - run: python -m pytest

     hooks:
       name: hooks (shellcheck + JSON)
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: "3.13"
         - name: shellcheck
           run: |
             command -v shellcheck >/dev/null || { sudo apt-get update && sudo apt-get install -y shellcheck; }
             shellcheck --version
             shellcheck -s sh -S warning src/plugins/*/hooks/*.sh
         - name: manifest & hooks.json = JSON valid
           run: |
             for f in .claude-plugin/marketplace.json src/plugins/*/.claude-plugin/plugin.json src/plugins/*/hooks/hooks.json; do
               python3 -m json.tool "$f" > /dev/null || { echo "JSON rusak: $f"; exit 1; }
             done
         - name: output hook = kosong atau JSON valid (fixture)
           run: |
             python -m pip install pytest
             python -m pytest tests/hooks -q

     lint:
       name: lint plugin
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0              # untuk check bump versi (M7) terhadap base PR
         - uses: actions/setup-python@v5
           with:
             python-version: "3.13"
         - name: lint_plugins.py
           env:
             # Kosongkan bertahap: M3,M4 ← L7.1 · M5 ← L7.2 · R2 ← X1 · S1 ← L5.5
             LINT_IGNORE: M3,M4,M5,R2,S1
           run: python3 scripts/lint_plugins.py --ignore "$LINT_IGNORE"

     plugin-validate:
       name: claude plugin validate
       runs-on: ubuntu-latest
       continue-on-error: true           # perlu verifikasi: butuh login atau tidak
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
           with:
             node-version: "20"
         - run: npm install -g @anthropic-ai/claude-code
         - run: claude plugin validate .
   ```

2. Setelah semua job hijau stabil ±1 minggu: jadikan `pytest`, `hooks`, `lint` status check wajib di branch protection `main`; ubah `plugin-validate` menjadi wajib bila terbukti tidak butuh autentikasi.
3. Saat L1.2 selesai (hook pindah ke Python): pertahankan job macOS hanya bila hook masih memanggil utilitas shell; bila tidak, pindahkan macOS ke jadwal mingguan.
4. Bila keputusan Python minimum = 3.9: tambah `"3.9"` dan `"3.10"` ke matriks dan pastikan `tomllib` punya fallback.

### Selesai bila

- Keempat job jalan di setiap PR; `pytest`, `hooks`, dan `lint` hijau di `main`.
- `LINT_IGNORE` kosong (semua check lint aktif).
- Merge ke `main` tanpa CI hijau ditolak oleh branch protection.

### Risiko & catatan

- **Versi action:** `actions/checkout@v4`, `setup-python@v5`, `setup-node@v4` adalah major yang saya ketahui; periksa major terbaru saat memasang.
- **Duplikasi test hook** (job `pytest` dan `hooks`) disengaja: job `hooks` menjadi gerbang cepat yang namanya jelas di status PR. Hapus salah satunya bila waktu CI jadi masalah.
- **`-S warning`** menyembunyikan temuan level info/style di masa depan juga. Alternatif lebih ketat: `-e SC2016` saja.
- **`claude plugin validate`** memvalidasi struktur marketplace; ia tidak menggantikan lint rujukan markdown (R1/R2) di L6.3.

**Status (2026-09-26):** workflow sudah aktif sejak repo punya remote `origin` (github.com/nataflow/agentic-workflow). Run terakhir di GitHub (`36125890596`, commit `d04b9c0`) **merah** di semua job `pytest`, sedangkan `hooks`, `lint`, dan `plugin-validate` hijau. Log run itu tidak bisa diambil lagi lewat `gh`; penyebab yang sudah dicatat di 08a adalah `test_profile_paths[backenddev]`.

Perbaikan lokal (commit `0ee4e8d`):
- README backenddev lolos lint path profil.
- Fixture `reviewed_at` tidak lagi memakai tanggal literal. Tanggal itu jadi basi keesokan harinya dan membuat 8 test frontenddev merah mulai 2026-09-26.
- Nama dimensi fixture mengikuti C7.
- Test baru mengunci `reviewed_at` sebelum commit akar.

Emulasi keempat job atas HEAD `57e4ef4` dijalankan pada clone `--depth 1`, dengan `HOME` kosong dan tanpa konfigurasi git global. Semuanya hijau:
- JSON manifest;
- `shellcheck -S warning`;
- `lint_plugins.py` 0 FAIL, dan juga 0 FAIL dengan `--base origin/main` sesudah versi naik;
- test hook;
- `pytest` py3.9: 1201 lulus + 1 skip `tomllib`;
- `pytest` py3.13: 1202 lulus, termasuk `test_php_build_keeps_dev` dengan composer terpasang.

**Sisa, menunggu keputusan user:**
- (1) Push `main` ke `origin`. User memilih belum push.
- (2) Branch protection `main` dengan status check `pytest`/`hooks`/`lint`, tanpa `enforce_admins`. User setuju dipasang sesudah run CI pertama hijau.

Checkbox dicentang sesudah keduanya terjadi.

---

## L6.3 [Sedang] Skrip lint plugin

- [x] Selesai

**Plugin:** repo (keempat plugin) · **Estimasi:** 1 hari (prototipe sudah jalan) · **Bergantung pada:** keputusan L7.1 (semantik M3/M4) · **Memblokir:** job `lint` di L6.2; verifikasi "Selesai bila" L7.1, L7.2, L7.5, X1, X2, L5.5

### Konteks

Banyak temuan `ISSUES.md` bersifat statis (versi ganda, manifest liar, `${CLAUDE_PLUGIN_ROOT}` literal di berkas yang dibaca lewat Read, path `.gemini` mati). Satu linter mencegah temuan itu muncul lagi dan memberi daftar kerja yang bisa dicentang.

### Lokasi & kondisi saat ini

- Belum ada `scripts/` di root repo.
- Prototipe `scripts/lint_plugins.py` (269 baris, stdlib saja) dijalankan **read-only** terhadap repo dari scratchpad dengan `python3 -B` (tanpa menulis bytecode). `git status --porcelain` sebelum dan sesudah identik (kosong).
- Hasil: **30 FAIL, 13 WARN**, exit 1. Dengan `--ignore M3,M4,M5,R2,S1` → **0 FAIL, 13 WARN**, exit 0; ditambah `--strict` → exit 1.

**Koreksi terhadap ISSUES.md:**
- Batas 1.536 karakter berlaku untuk **gabungan `description` + `when_to_use` skill** (dokumentasi skills, "Frontmatter reference": *"the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing"*). Dokumentasi yang saya periksa tidak menyebut batas itu untuk agent. Deskripsi terpanjang saat ini 415 karakter (`frontenddev/agents/code-implementor.md`), jauh di bawah batas.
- `version` ganda bukan hanya frontenddev: **keempat** plugin menulis versi di `plugin.json` dan di entri marketplace (tiga sama, frontenddev berbeda). Rinciannya di `issues/07-manifest-dokumentasi.md` L7.1.

### Rencana perbaikan

1. **Daftar check**

   | ID | Memeriksa | Level | Terkait |
   |---|---|---|---|
   | M1 | `marketplace.json`, `plugin.json`, `hooks.json` = JSON valid | FAIL | — |
   | M2 | `source` tiap entri ada; `name` entri = `name` di `plugin.json` | FAIL | — |
   | M3 | `version` hanya di satu tempat (sesuai keputusan L7.1); bila di dua tempat, sebut bedanya | FAIL | L7.1 |
   | M4 | `description`, `author.name`, `author.email` entri = `plugin.json` (atau hanya di satu tempat) | FAIL | L7.1 |
   | M5 | tidak ada `plugin.json` di root plugin | FAIL | L7.2 |
   | M6 | nama marketplace kebab-case dan tidak tercadang | FAIL | — |
   | M7 | *(belum di prototipe)* bila ada berkas berubah di `src/plugins/<p>/` terhadap `--base <ref>`, `version` plugin itu wajib naik | FAIL (PR saja) | L7.1 |
   | F1 | frontmatter SKILL: ada; `description` terisi; `name` = nama direktori; `description`+`when_to_use` ≤1.536; field di luar daftar resmi → WARN; `metadata` wajib map | FAIL/WARN | L7.4, L7.5 |
   | F2 | frontmatter agent: `name`, `description`; `hooks`/`mcpServers`/`permissionMode` → WARN (diabaikan untuk agent plugin); field di luar daftar → WARN | FAIL/WARN | L3.4 |
   | F3 | *(belum di prototipe)* skill berdeskripsi "Dipanggil …" wajib `user-invocable: false` | WARN | L7.4 |
   | R1 | rujukan berkas di backtick (`references/…`, `templates/…`, `dispatcher/…`, `stacks/…`, `agents/…`, `scripts/…`, `…/SKILL.md`) ada; tidak ada di skill ini tapi ada di skill lain → WARN "rujukan singkat" | FAIL/WARN | — |
   | R2 | `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (kecuali baris slot yang menyebut "substitusi") | FAIL | X1 |
   | R3 | idem di `agents/*.md` | WARN | X2 |
   | S0 | semua `.py` bisa di-`compile()` | FAIL | — |
   | S1 | tidak ada `.gemini` atau path repo-dev (`src/plugins/…`) di skrip | FAIL | L5.5, B14 |
   | S2 | skrip yang dirujuk `${CLAUDE_PLUGIN_ROOT}/skills/…/*.py` di SKILL.md ada | FAIL | — |
   | H1 | perintah `hooks.json` menunjuk berkas yang ada dan ber-mode git `100755` | FAIL | — |
   | G1 | bytecode tanpa sumber `.py` (lokal) → WARN; bytecode ter-track di git → FAIL | WARN/FAIL | L7.5 |

   Daftar field resmi diambil dari dokumentasi (diakses 2026-09-24): skill — `name, description, when_to_use, argument-hint, arguments, disable-model-invocation, user-invocable, allowed-tools, disallowed-tools, model, effort, context, agent, background, hooks, paths, shell, metadata, license, compatibility`; agent — `name, description, tools, disallowedTools, model, permissionMode, maxTurns, skills, mcpServers, hooks, memory, background, omitClaudeMd, effort, isolation, color, initialPrompt, experimental`. Dokumentasi sub-agents: *"For security reasons, plugin subagents don't support the `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading agents from a plugin."*

2. **Prototipe** (salin ke `scripts/lint_plugins.py`, lalu tambah M7 dan F3):

   <details><summary>scripts/lint_plugins.py (269 baris, sudah dijalankan)</summary>

   ```python
   #!/usr/bin/env python3
   """Lint statis marketplace `agentic-workflow` (read-only, stdlib saja).

   Pemakaian: python3 scripts/lint_plugins.py [--root DIR] [--strict] [--json] [--ignore M3,R2]
   Exit 1 bila ada FAIL (atau WARN dengan --strict).
   """
   from __future__ import annotations

   import argparse
   import json
   import re
   import subprocess
   import sys
   from pathlib import Path

   SKILL_FIELDS = {"name", "description", "when_to_use", "argument-hint", "arguments",
                   "disable-model-invocation", "user-invocable", "allowed-tools", "disallowed-tools",
                   "model", "effort", "context", "agent", "background", "hooks", "paths", "shell",
                   "metadata", "license", "compatibility"}
   AGENT_FIELDS = {"name", "description", "tools", "disallowedTools", "model", "permissionMode",
                   "maxTurns", "skills", "mcpServers", "hooks", "memory", "background", "omitClaudeMd",
                   "effort", "isolation", "color", "initialPrompt", "experimental"}
   AGENT_IGNORED_IN_PLUGIN = {"hooks", "mcpServers", "permissionMode"}
   DESC_CAP = 1536
   KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
   RESERVED_MARKETPLACES = {"claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
                            "claude-plugins-community", "claude-community", "anthropic-marketplace",
                            "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
                            "npm", "pip", "uv", "cargo", "github", "gh"}
   REF_DIRS = {"references", "templates", "dispatcher", "stacks", "agents", "scripts"}
   TOKEN = re.compile(r"`([^`\s]+)`")
   PLACEHOLDER = re.compile(r"[<>{}*…]|\bNN\b|\bXX\b")
   DEV_PATHS = re.compile(r"\.gemini|['\"/]src['\"]\s*/\s*['\"]plugins|src/plugins/")


   class Report:
       def __init__(self) -> None:
           self.items: list[dict] = []

       def add(self, level: str, check: str, where: str, msg: str) -> None:
           self.items.append({"level": level, "check": check, "where": where, "msg": msg})

       def count(self, level: str) -> int:
           return sum(1 for i in self.items if i["level"] == level)


   def read_json(path: Path, rep: Report, where: str):
       try:
           return json.loads(path.read_text(encoding="utf-8"))
       except (OSError, json.JSONDecodeError) as exc:
           rep.add("FAIL", "M1", where, f"JSON tidak valid: {exc}")
           return None


   def frontmatter(text: str):
       """Subset YAML: `key: value`, map satu tingkat (`key:` + baris berindentasi). None bila tanpa pagar."""
       text = text.lstrip("﻿")
       if not text.startswith("---"):
           return None
       end = text.find("\n---", 3)
       if end == -1:
           return None
       data: dict = {}
       current = None
       for raw in text[3:end].splitlines():
           if not raw.strip() or raw.lstrip().startswith("#"):
               continue
           if raw[:1] in (" ", "\t") and current is not None:
               k, _, v = raw.strip().partition(":")
               if not isinstance(data[current], dict):
                   data[current] = {}
               data[current][k.strip()] = v.strip()
               continue
           key, _, value = raw.partition(":")
           current = key.strip()
           data[current] = value.strip().strip('"').strip("'")
       return data


   def git_tracked(root: Path) -> list[str] | None:
       try:
           out = subprocess.run(["git", "-C", str(root), "ls-files", "-s", "-z"], capture_output=True,
                                text=True, check=True).stdout
       except (OSError, subprocess.CalledProcessError):
           return None
       return [e for e in out.split("\0") if e]


   def lint(root: Path) -> Report:
       rep = Report()
       mp_path = root / ".claude-plugin" / "marketplace.json"
       mp = read_json(mp_path, rep, ".claude-plugin/marketplace.json") or {}
       name = mp.get("name", "")
       if name and (not KEBAB.match(name) or name.lower() in RESERVED_MARKETPLACES):
           rep.add("FAIL", "M6", "marketplace.json", f"nama marketplace `{name}` tidak kebab-case atau tercadang")

       tracked = git_tracked(root) or []
       modes = {e.split("\t", 1)[1]: e.split()[0] for e in tracked}

       plugin_dirs = []
       for entry in mp.get("plugins", []):
           pname = entry.get("name", "?")
           src = root / entry.get("source", "")
           where = f"marketplace:{pname}"
           if not src.is_dir():
               rep.add("FAIL", "M2", where, f"source `{entry.get('source')}` tidak ada")
               continue
           plugin_dirs.append(src)
           pj_path = src / ".claude-plugin" / "plugin.json"
           pj = read_json(pj_path, rep, str(pj_path.relative_to(root))) if pj_path.is_file() else None
           if pj is None:
               rep.add("WARN", "M2", where, "tanpa .claude-plugin/plugin.json (nama diturunkan dari direktori)")
               pj = {}
           if pj.get("name") and pj["name"] != pname:
               rep.add("FAIL", "M2", where, f"nama entri `{pname}` ≠ plugin.json `{pj['name']}`")
           if "version" in entry and "version" in pj:
               same = entry["version"] == pj["version"]
               rep.add("FAIL", "M3", where,
                       f"version di dua tempat (plugin.json {pj['version']}, marketplace {entry['version']})"
                       + ("" if same else " — BERBEDA; Claude Code memakai plugin.json tanpa peringatan"))
           for field in ("description",):
               if field in entry and field in pj and entry[field] != pj[field]:
                   rep.add("FAIL", "M4", where, f"`{field}` entri ≠ plugin.json (listing menampilkan nilai entri)")
           ea, pa = entry.get("author", {}), pj.get("author", {})
           for k in ("name", "email"):
               if k in ea and k in pa and ea[k] != pa[k]:
                   rep.add("FAIL", "M4", where, f"author.{k} entri `{ea[k]}` ≠ plugin.json `{pa[k]}`")
           if (src / "plugin.json").is_file():
               rep.add("FAIL", "M5", f"{src.relative_to(root)}/plugin.json",
                       "plugin.json liar di root plugin (loader hanya membaca .claude-plugin/plugin.json)")

       for pdir in plugin_dirs:
           lint_plugin(root, pdir, rep, modes)
       return rep


   def resolve_ref(token: str, md: Path, pdir: Path) -> bool:
       t = token.replace("${CLAUDE_PLUGIN_ROOT}/", "")
       t = re.sub(r"(:\d+(-\d+)?)+$|#.*$", "", t)
       skill_dir = next((p for p in md.parents if p.parent.name == "skills"), None)
       cands = [md.parent / t, pdir / t, pdir / "skills" / t]
       if skill_dir:
           cands.append(skill_dir / t)
       return any(c.exists() for c in cands)


   def lint_plugin(root: Path, pdir: Path, rep: Report, modes: dict) -> None:
       rel = lambda p: str(p.relative_to(root))  # noqa: E731
       # F1 — frontmatter skill
       for skill_md in sorted(pdir.glob("skills/*/SKILL.md")):
           fm = frontmatter(skill_md.read_text(encoding="utf-8"))
           if fm is None:
               rep.add("FAIL", "F1", rel(skill_md), "frontmatter tidak ada/rusak")
               continue
           if not fm.get("description"):
               rep.add("FAIL", "F1", rel(skill_md), "description kosong")
           if fm.get("name") and fm["name"] != skill_md.parent.name:
               rep.add("WARN", "F1", rel(skill_md), f"name `{fm['name']}` ≠ nama direktori")
           total = len(fm.get("description", "")) + len(fm.get("when_to_use", ""))
           if total > DESC_CAP:
               rep.add("FAIL", "F1", rel(skill_md), f"description+when_to_use {total} > {DESC_CAP} karakter")
           for k in fm:
               if k not in SKILL_FIELDS:
                   rep.add("WARN", "F1", rel(skill_md), f"field tak dikenal `{k}` (diabaikan diam-diam)")
           if "metadata" in fm and not isinstance(fm["metadata"], dict):
               rep.add("WARN", "F1", rel(skill_md), "metadata bukan map (dibuang Claude Code)")
       # F2 — frontmatter agent
       for agent_md in sorted(pdir.glob("agents/*.md")):
           fm = frontmatter(agent_md.read_text(encoding="utf-8"))
           if fm is None or not fm.get("name") or not fm.get("description"):
               rep.add("FAIL", "F2", rel(agent_md), "frontmatter/name/description tidak ada")
               continue
           for k in fm:
               if k in AGENT_IGNORED_IN_PLUGIN:
                   rep.add("WARN", "F2", rel(agent_md), f"`{k}` diabaikan untuk agent plugin")
               elif k not in AGENT_FIELDS:
                   rep.add("WARN", "F2", rel(agent_md), f"field tak dikenal `{k}`")
       # R1/R2 — rujukan dan placeholder di markdown
       for md in sorted(pdir.rglob("*.md")):
           text = md.read_text(encoding="utf-8")
           in_fence = False
           for no, line in enumerate(text.splitlines(), 1):
               if line.lstrip().startswith("```"):
                   in_fence = not in_fence
               for tok in TOKEN.findall(line):
                   segs = set(tok.replace("${CLAUDE_PLUGIN_ROOT}/", "").split("/"))
                   if not (segs & REF_DIRS or tok.endswith("SKILL.md")) or PLACEHOLDER.search(tok):
                       continue
                   if not re.search(r"\.(md|py|sh|json)(:\d+.*)?$", tok):
                       continue
                   if tok.startswith((".claude/", "~/", "/")):
                       continue
                   if not resolve_ref(tok, md, pdir):
                       tail = re.sub(r"(:\d+(-\d+)?)+$", "", tok.replace("${CLAUDE_PLUGIN_ROOT}/", ""))
                       elsewhere = [str(c.relative_to(pdir)) for c in pdir.rglob(Path(tail).name)
                                    if str(c).endswith("/" + tail)]
                       if elsewhere:
                           rep.add("WARN", "R1", f"{rel(md)}:{no}",
                                   f"rujukan singkat `{tok}` tidak ada relatif skill ini; ada di {', '.join(elsewhere[:3])}")
                       else:
                           rep.add("FAIL", "R1", f"{rel(md)}:{no}", f"rujukan `{tok}` tidak ditemukan di plugin")
               if "${CLAUDE_PLUGIN_ROOT}" in line and md.name != "SKILL.md" and "substitusi" not in line:
                   level = "WARN" if md.parent.name == "agents" else "FAIL"
                   check = "R3" if level == "WARN" else "R2"
                   rep.add(level, check, f"{rel(md)}:{no}",
                           "`${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md" + (" (X2)" if level == "WARN" else " (X1)"))
       # S1/S2 — skrip
       for py in sorted(pdir.rglob("*.py")):
           if "__pycache__" in py.parts:
               continue
           src = py.read_text(encoding="utf-8")
           try:
               compile(src, str(py), "exec")
           except SyntaxError as exc:
               rep.add("FAIL", "S0", rel(py), f"SyntaxError: {exc}")
           hits = [n for n, l in enumerate(src.splitlines(), 1) if DEV_PATHS.search(l)]
           if hits:
               rep.add("FAIL", "S1", rel(py), f"path .gemini/repo-dev di {len(hits)} baris (mis. :{hits[0]})")
       for skill_md in sorted(pdir.glob("skills/*/SKILL.md")):
           for m in re.finditer(r"\$\{CLAUDE_PLUGIN_ROOT\}/(skills/[\w./-]+\.py)", skill_md.read_text(encoding="utf-8")):
               if not (pdir / m.group(1)).is_file():
                   rep.add("FAIL", "S2", rel(skill_md), f"skrip `{m.group(1)}` tidak ada")
       # H1 — hooks
       hj = pdir / "hooks" / "hooks.json"
       if hj.is_file():
           data = read_json(hj, rep, rel(hj)) or {}
           for event, groups in data.get("hooks", {}).items():
               for g in groups:
                   for h in g.get("hooks", []):
                       cmd = h.get("command", "")
                       m = re.match(r"\$\{CLAUDE_PLUGIN_ROOT\}/(\S+)", cmd)
                       if not m:
                           continue
                       target = pdir / m.group(1)
                       if not target.is_file():
                           rep.add("FAIL", "H1", rel(hj), f"{event}: `{m.group(1)}` tidak ada")
                       elif modes and modes.get(rel(target)) not in ("100755", None):
                           rep.add("FAIL", "H1", rel(target), "tidak executable di git (mode bukan 100755)")
       # G1 — sisa cache lokal
       for pyc in sorted(pdir.rglob("__pycache__/*.pyc")):
           source = pyc.parent.parent / (pyc.name.split(".")[0] + ".py")
           if not source.is_file():
               rep.add("WARN", "G1", rel(pyc), "bytecode tanpa sumber .py (sisa cache lokal)")
       for path, mode in modes.items():
           if path.startswith(rel(pdir) + "/") and ("__pycache__" in path or path.endswith(".pyc")):
               rep.add("FAIL", "G1", path, "bytecode ter-track di git")


   def main() -> None:
       ap = argparse.ArgumentParser(description=__doc__)
       ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
       ap.add_argument("--strict", action="store_true", help="WARN dihitung gagal")
       ap.add_argument("--json", action="store_true")
       ap.add_argument("--ignore", default="", help="ID check dipisah koma, mis. M3,R2 (adopsi bertahap)")
       args = ap.parse_args()
       rep = lint(Path(args.root).resolve())
       ignored = {c.strip() for c in args.ignore.split(",") if c.strip()}
       rep.items = [i for i in rep.items if i["check"] not in ignored]
       if args.json:
           print(json.dumps(rep.items, indent=2, ensure_ascii=False))
       else:
           for i in sorted(rep.items, key=lambda i: (i["check"], i["where"])):
               print(f"[{i['level']}] {i['check']} {i['where']}: {i['msg']}")
           print(f"LINT: {rep.count('FAIL')} FAIL, {rep.count('WARN')} WARN")
       sys.exit(1 if rep.count("FAIL") or (args.strict and rep.count("WARN")) else 0)


   if __name__ == "__main__":
       main()
   ```

   </details>

3. **Temuan yang ditangkap prototipe hari ini** (keluaran asli, `python3 -B …/lint_plugins.py --root .`):

   ```
   [WARN] G1 src/plugins/frontenddev/skills/lead/scripts/__pycache__/check_preconditions.cpython-313.pyc: bytecode tanpa sumber .py (sisa cache lokal)
   [FAIL] M3 marketplace:analyst: version di dua tempat (plugin.json 0.2.0, marketplace 0.2.0)
   [FAIL] M3 marketplace:backenddev: version di dua tempat (plugin.json 0.5.0, marketplace 0.5.0)
   [FAIL] M3 marketplace:frontenddev: version di dua tempat (plugin.json 0.4.0, marketplace 0.3.0) — BERBEDA; Claude Code memakai plugin.json tanpa peringatan
   [FAIL] M3 marketplace:quickdev: version di dua tempat (plugin.json 0.1.0, marketplace 0.1.0)
   [FAIL] M4 marketplace:frontenddev: `description` entri ≠ plugin.json (listing menampilkan nilai entri)
   [FAIL] M4 marketplace:frontenddev: author.email entri `fakhrulnugroho15@gmail.com` ≠ plugin.json `groupzcode@gmail.com`
   [FAIL] M5 src/plugins/frontenddev/plugin.json: plugin.json liar di root plugin (loader hanya membaca .claude-plugin/plugin.json)
   [WARN] R1 src/plugins/backenddev/skills/analyst/references/chain-rules.md:100: rujukan singkat `dispatcher/reviewer.md` tidak ada relatif skill ini; ada di skills/business-analysis/dispatcher/reviewer.md, skills/plan/dispatcher/reviewer.md, skills/architect/dispatcher/reviewer.md
   [WARN] R1 src/plugins/backenddev/skills/profile/stacks/_CONTRACT.md:97: rujukan singkat `dispatcher/explorer.md` tidak ada relatif skill ini; ada di skills/business-analysis/dispatcher/explorer.md, skills/debug/dispatcher/explorer.md, skills/plan/dispatcher/explorer.md
   [WARN] R1 src/plugins/backenddev/skills/system-analysis/dispatcher/explorer.md:176: rujukan singkat `stacks/_CONTRACT.md` tidak ada relatif skill ini; ada di skills/profile/stacks/_CONTRACT.md
   [WARN] R1 src/plugins/backenddev/skills/tech-lead/references/gate-scope.md:139: rujukan singkat `dispatcher/reviewer.md` tidak ada relatif skill ini; ada di skills/business-analysis/dispatcher/reviewer.md, skills/plan/dispatcher/reviewer.md, skills/architect/dispatcher/reviewer.md
   [WARN] R1 src/plugins/frontenddev/README.md:120: rujukan singkat `scripts/check_preconditions.py` tidak ada relatif skill ini; ada di skills/contract/scripts/check_preconditions.py, skills/report/scripts/check_preconditions.py, skills/task/scripts/check_preconditions.py
   [WARN] R1 src/plugins/frontenddev/README.md:120: rujukan singkat `scripts/taskdir_state.py` tidak ada relatif skill ini; ada di skills/lead/scripts/taskdir_state.py
   [WARN] R1 src/plugins/frontenddev/skills/lead/SKILL.md:159: rujukan singkat `stacks/_CONTRACT.md` tidak ada relatif skill ini; ada di skills/profile/stacks/_CONTRACT.md
   [WARN] R1 src/plugins/frontenddev/skills/profile/stacks/_CONTRACT.md:129: rujukan singkat `references/execution-protocol.md` tidak ada relatif skill ini; ada di skills/architect/references/execution-protocol.md
   [FAIL] R2 src/plugins/backenddev/skills/profile/stacks/_CONTRACT.md:73: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/architect/dispatcher/reviewer.md:53: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/architect/references/execution-protocol.md:14: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/contract/dispatcher/reviewer.md:18: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/contract/dispatcher/reviewer.md:42: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/contract/dispatcher/reviewer.md:43: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/contract/dispatcher/reviewer.md:57: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/contract/references/layer-patterns.md:3: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/lead/references/lane-routing-matrix.md:82: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/plan/dispatcher/reviewer.md:137: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/plan/dispatcher/reviewer.md:138: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/plan/dispatcher/reviewer.md:157: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/profile/stacks/_CONTRACT.md:6: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/profile/stacks/_CONTRACT.md:98: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [FAIL] R2 src/plugins/frontenddev/skills/review/references/nine-dimensions-catalog.md:3: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)
   [WARN] R3 src/plugins/backenddev/agents/code-reviewer.md:25: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X2)
   [WARN] R3 src/plugins/frontenddev/agents/code-reviewer.md:25: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X2)
   [WARN] R3 src/plugins/frontenddev/agents/code-reviewer.md:31: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X2)
   [WARN] R3 src/plugins/frontenddev/agents/contract-reviewer.md:16: `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md (X2)
   [FAIL] S1 src/plugins/backenddev/skills/architect/scripts/check_preconditions.py: path .gemini/repo-dev di 5 baris (mis. :380)
   [FAIL] S1 src/plugins/backenddev/skills/audit/scripts/check_preconditions.py: path .gemini/repo-dev di 2 baris (mis. :187)
   [FAIL] S1 src/plugins/backenddev/skills/business-analysis/scripts/check_preconditions.py: path .gemini/repo-dev di 4 baris (mis. :329)
   [FAIL] S1 src/plugins/backenddev/skills/debug/scripts/check_preconditions.py: path .gemini/repo-dev di 4 baris (mis. :180)
   [FAIL] S1 src/plugins/backenddev/skills/document-api/scripts/check_preconditions.py: path .gemini/repo-dev di 2 baris (mis. :131)
   [FAIL] S1 src/plugins/backenddev/skills/plan/scripts/check_preconditions.py: path .gemini/repo-dev di 16 baris (mis. :459)
   [FAIL] S1 src/plugins/backenddev/skills/system-analysis/scripts/check_preconditions.py: path .gemini/repo-dev di 8 baris (mis. :353)
   [FAIL] S1 src/plugins/backenddev/skills/tech-lead/scripts/check_preconditions.py: path .gemini/repo-dev di 2 baris (mis. :389)
   LINT: 30 FAIL, 13 WARN
   ```

   Pembacaan hasil:
   - **R2 = 15 baris, sama persis dengan daftar X1**; **R3 = 4 baris, sama persis dengan daftar X2**. Empat baris lain yang memuat `${CLAUDE_PLUGIN_ROOT}` di dispatcher (`backenddev/…/implementor.md:40`, `frontenddev/…/implementor.md:71`, `frontenddev/…/architect/dispatcher/reviewer.md:39`, `frontenddev/…/contract/dispatcher/reviewer.md:32`) adalah tabel "Slot Hidrasi" yang menyatakan nilainya "hasil substitusi" dari SKILL.md. Itu pola yang benar, sehingga dikecualikan.
   - **S1 = 43 baris di 8 skrip** (21 baris `.gemini` + 22 baris `"src" / "plugins"`), cocok dengan L5.5.
   - **R1 (temuan baru, bukan di ISSUES.md)**: 8 rujukan singkat lintas-skill. Tidak ada berkas yang benar-benar hilang, tetapi model yang membaca `frontenddev/skills/lead/SKILL.md:159` akan mencari `skills/lead/stacks/_CONTRACT.md` yang tidak ada. Perbaiki dengan menulis path lengkap (`profile/stacks/_CONTRACT.md`) atau `skills/<skill>/…`. Rujukan generik "ketiga `dispatcher/reviewer.md`" boleh dibiarkan WARN.
   - **F1/F2/H1/S0/S2 = 0**: frontmatter ke-31 SKILL dan ke-12 agent valid, `metadata` berbentuk map, hook ada dan executable, semua skrip terkompilasi, semua skrip yang dirujuk SKILL ada.
   - **G1**: satu `.pyc` tanpa sumber (L7.5).

4. **Tambahan sebelum dipakai CI:** M7 (bump versi terhadap `--base`, dijalankan hanya di PR) dan F3 (`user-invocable: false` untuk skill "Dipanggil …", bila L7.4 disetujui). Tambahkan test untuk lint itu sendiri di `tests/test_lint_plugins.py` dengan marketplace mini di `tmp_path` (satu kasus per ID check).

5. **Adopsi bertahap:** CI memulai dengan `--ignore M3,M4,M5,R2,S1`. Hapus ID dari daftar di PR yang memperbaikinya: M3/M4 ← L7.1, M5 ← L7.2, R2 ← X1, S1 ← L5.5. Setelah R1 dan R3 dibereskan, aktifkan `--strict`.

### Selesai bila

- `scripts/lint_plugins.py` ada di repo beserta test-nya, dengan semua check di tabel sub-tugas 1 (termasuk M7 dan F3).
- `python3 scripts/lint_plugins.py` exit 0 tanpa `--ignore`; target akhirnya `--strict` juga exit 0.
- Job `lint` di CI memakai skrip ini.

### Risiko & catatan

- **Parser frontmatter sederhana** (subset YAML, map satu tingkat). Cukup untuk frontmatter repo ini; bila nanti ada list YAML multi-baris (mis. `allowed-tools` sebagai list), perluas parser atau pakai PyYAML khusus di CI.
- **Daftar field resmi bisa bertambah.** Field baru dari Claude Code akan muncul sebagai WARN, bukan FAIL, supaya lint tidak memblokir tanpa alasan.
- **Catatan untuk X2 (di luar cakupan berkas ini):** tabel plugins-reference yang saya ambil lewat WebFetch memuat baris *"Skill and agent content | Anywhere the placeholder appears"* untuk `${CLAUDE_PLUGIN_ROOT}`. Bila kutipan ini akurat, substitusi di badan agent kini terdokumentasi, dan klaim "tidak terdokumentasi resmi" di X2 perlu ditinjau ulang. Karena itu R3 tetap WARN. Dokumen itu tidak menyebut berkas yang dibaca belakangan lewat Read, jadi R2/X1 tetap FAIL.
- **Heuristik "substitusi"** untuk pengecualian R2 bergantung pada kata dalam baris. Bila X1 diperbaiki dengan pola slot, pertahankan kata itu di tabel slot atau ganti heuristik dengan penanda eksplisit (mis. komentar `<!-- slot -->`).
