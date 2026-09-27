# Langkah 9 — Robustness Lintas Plugin (E1–E23)

Sumber: review robustness 2026-09-26 (empat reviewer paralel, satu per plugin, rubrik enam dimensi). Semua
temuan di bawah **terbukti lewat probe** di repo sementara, kecuali yang ditandai lain. Basis kode: commit
`0651572`.

## Tujuan

Menutup jalur yang masih bergantung pada disiplin model atau berakhir dengan traceback. Pola yang
berulang di keempat plugin:

1. Skrip mati dengan traceback saat bertemu berkas non-UTF-8, sehingga vonis tidak bisa dibaca.
2. Pemeriksaan bergantung pada subjek commit yang diketik model, padahal subjek itu tidak dijaga skrip.
3. Agent penilai punya `Bash`/`Write`, tetapi larangan memutasi repo hanya tertulis di prosa.

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perbaikan + test → suite penuh hijau → commit.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | E1 | Lintas plugin, murni penanganan galat; dijaga smoke test keadaan `rusak`, yang lalu melindungi tahap berikutnya. |
| 2 | E2–E6 (quickdev) | Satu skrip (`plan_lock.py`) dan tiga SKILL; tanpa ketergantungan plugin lain. |
| 3 | E7–E11 (analyst + penerima) | E8 menyentuh `precondition_lib.py` backenddev **dan** frontenddev; dikerjakan sebelum tahap 4–5 menyentuh berkas yang sama. |
| 4 | E12–E17 (frontenddev) | |
| 5 | E18–E23 (backenddev) | E19 memakai pola hook yang sama dengan E15. |
| 6 | Rilis | Versi keempat plugin naik (lint M7), indeks `ISSUES.md`. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang ada
dan harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| E1 | ±20 titik baca (lihat E1) di keempat plugin, termasuk `hooks/detect.py` (salinan identik be/fe) | 31 dari 47 CLI; hook SessionStart | ya (salinan identik) | `test_smoke.py` (keadaan baru) | Rendah: hanya jalur galat. Titik yang dulu `except OSError → ""` tidak boleh diam-diam membaca berkas rusak sebagai kosong. |
| E2 | `plan_lock.py cmd_start` | execute Fase 0, review Fase 5 | tidak | `test_08d_plan_lock.py` | Rendah: cabang baru hanya untuk `COMPLETED` + langkah `[ ]` tersisa. |
| E3 | `plan_lock.py cmd_lock`, `cmd_verify` | plan Fase 3, execute, review | tidak | `test_08d_plan_lock.py` | Sedang: rencana lama tanpa `## 1.` yang sudah APPROVED kini `VERIFY FAIL`. Memang disengaja (sidiknya kosong). |
| E4 | `plan_lock.py` (`int` aman, tulis atomik) | semua subperintah | tidak | — | Rendah |
| E5 | `plan_lock.py cmd_status`, `cmd_confirm`, `cmd_lock` | review precondition 1 | tidak | `test_08d_plan_lock.py` | Rendah: `status` menambah kunci JSON `consistent`; kunci lama tetap. |
| E6 | `execute/SKILL.md` Fase 3 butir 2, `profile/SKILL.md` Fase 2 | model | tidak | `test_08d_text.py` bila menagih teks lama | Rendah |
| E7 | `ticket.py _commit_failed` | model (pesan) | tidak | — | Rendah |
| E8 | `analyst_lib.py` (fungsi segel), `ticket.py approve`/`classify`, `precondition_lib.py ticket_source_verdict` be **dan** fe | tech-lead check tiket, lead check tiket | **ya**: analyst → be/fe | `test_a1_ticket_source.py` | Sedang: tiket READY lama tanpa `approved_seal` wajib tetap lolos lewat jalur lama. |
| E9 | `ticket.py review`, `spec/SKILL.md`, `spec/dispatcher/reviewer.md`, `agents/ticket-reviewer.md` | model, reviewer | tidak | `test_ticket.py`, `test_ticket_8a.py` (±10 panggilan `review` tanpa `--report`), `test_a1_ticket_source.py` | Sedang: kontrak CLI `review` berubah (wajib `--report` untuk PASS/BLOCKED). |
| E10 | `ticket.py review`, `analyst_lib.git_commit` | model | tidak | — | Rendah |
| E11 | `ticket.py new`/`cancel` | intake, spec | tidak | `test_ticket*.py` (`--type` tetap diterima) | Rendah |
| E12 | fe `precondition_lib.lane_tamper` | `taskdir_state.py`, gate check akar TASK | tidak | `test_08c_taskdir_state.py`, fixture ber-commit akar | Sedang: repo yang commit akarnya bersubjek lain kini dinilai terhadap commit pertama `TASK.md`, bukan diloloskan. |
| E13 | fe `precondition_lib.review_is_fresh` | `taskdir_state.py`, architect & report prasyarat | tidak | `test_08c_review_preconditions.py`, `test_08c_architect_preconditions.py` | Sedang: commit apa pun yang menyentuh brief sesudah REVIEW kini membuatnya basi (dulu hanya subjek `implement unit`). |
| E14 | fe `precondition_lib` (normalisasi subjek) | `chain.py revisions`, plan prasyarat | tidak | `test_chain_reopen.py`, `test_review_round.py` | Rendah |
| E15 | fe `hooks/hooks.json` + `hooks/guard_bash.py` baru, `validate_review.py` | `frontenddev:code-reviewer` | tidak | `test_smoke.py` (inventaris CLI), `test_validate_review.py` | Sedang: hook baru jalan di tiap Bash/Edit/Write, tetapi exit 0 seketika untuk agent lain. |
| E16 | fe `precondition_lib.normalize_taskdir` | 9 pemanggil | tidak | — | Rendah |
| E17 | fe `architect/scripts/check_preconditions.py`, `architect/SKILL.md` | model | tidak | `test_08c_architect_preconditions.py` | Rendah |
| E18 | be `brief_status.landed_sha`, `architect/scripts/check_preconditions.py` | architect resume | tidak | `test_brief_status.py`, `test_architect_preconditions.py` | Sedang: brief `DONE` tanpa commit kini menahan rantai. |
| E19 | be `hooks/guard_bash.py` | `backenddev:code-reviewer` | tidak | `test_l34_guard_bash.py` | Sedang: reviewer yang dulu bebas kini dipagar allowlist. |
| E20 | be `chain_counters.py` | analyst check 7, business/system-analysis | tidak | `test_l213_counters.py` | Rendah |
| E21 | be `lifecycle-recovery.md`, `gate-lifecycle.md`, `architect/scripts/check_preconditions.py` | tech-lead re-entry | tidak | test teks bila ada | Rendah |
| E22 | `run_verification.py` (salinan identik be/fe) | — (docstring) | ya | — | Nihil |
| E23 | 6 berkas `.md` (rujukan) | model, lint R1 | tidak | `test_lint_plugins.py` | Nihil |

**Di luar cakupan (diputuskan, tidak diperbaiki):**

- **Hook yang memblokir Edit `src/` di main loop sebelum gerbang** (be/fe). Main loop tidak bisa membedakan
  kerja rantai dari kerja biasa user di repo yang sama. Pagar di sana akan memblokir penggunaan normal. Yang
  dipagar adalah subagen, lewat `agent_type`.
- **Versi plugin terpasang tertinggal dari source** (`frontenddev:code-implementor` masih ber-`Bash` di sesi
  review). Ini urusan pemasangan (`/plugin update`), bukan kode.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| E1 | Perbaiki di titik asal, dengan pesan yang menyebut berkas. Smoke test mendapat keadaan `rusak` (semua dokumen non-UTF-8) sebagai jaring. | Jaring generik di `main()` tidak tahu berkas mana yang rusak. |
| E8 | Segel baru `approved_seal`: sha256 12 hex atas teks mentah yang dinormalkan (tanpa parser YAML). Tiket tanpa segel (lama) tetap diperiksa lewat subjek commit. | `approved_hash` bergantung pada parser frontmatter analyst. Menyalinnya ke dua plugin lain berisiko tidak identik. |
| E9 | `--report` wajib untuk `PASS`/`BLOCKED`; blok reviewer memuat `- Sidik: <kartu>/<elisitasi>` yang disalin dari prompt dispatch, dan `review` menolak bila berbeda dari sidik disk. | Vonis terikat pada konten yang benar-benar dibaca reviewer. |
| E13 | Basi = ada commit menyentuh `brief-*.md` sesudah commit `REVIEW.md`. | Semua penyentuh brief (unit DONE/BLOCKED, batch plan) memang membatalkan review. Tidak lagi bergantung subjek. |
| E15/E19 | Pagar `code-reviewer` lewat hook PreToolUse (pola L3.4 backenddev), fail-closed. | Prosa saja tidak menahan `git reset --hard`. |
| E14/E18 | Subjek dibandingkan sesudah normalisasi spasi dan huruf. | Menutup near-miss yang terbukti (satu spasi berlebih) tanpa melonggarkan ke regex. |

---

## E1 [Tinggi] Berkas non-UTF-8 → traceback di 31 dari 47 CLI
- [x] Selesai — titik asal ditangani per berkas; `cli()` di `precondition_lib` be/fe sebagai jaring 35 skrip;
  `test_smoke.py` keadaan `rusak` (47 CLI) + `tests/test_e1_non_utf8.py`

**Plugin:** semua · **Reproduksi:** probe `scratchpad/probe_utf8.py` (merusak satu dokumen per putaran, menjalankan
seluruh `CASES` `test_smoke.py`).

Titik asal (frame plugin terdalam), dikelompokkan:

- `hooks/detect.py:352 read_index` (be+fe, identik) — `index.json` profil; menjatuhkan 17 skrip prasyarat.
- fe `precondition_lib.py:384 read_status`, `:559 success_criteria`, `:180 typecheck_per_brief`.
- be `precondition_lib.py:323 read_text`; be `validate_doc.py:74`; be `chain_counters.py:82`; be `detect.py:121 go_requires`.
- fe `validate_doc.py:167`, `validate_review.py:113,235`, `validate_report.py:103,104,182`, `validate_task.py:69`, `validate_audit.py:104`.
- analyst `ticket.py:72 read`, `validate_doc.py:89`.
- quickdev `plan_lock.py:57`.
- fe `report/check_preconditions.py`: stdout `--json` tidak valid saat `index.json`/`CONTRACT.md`/`REVIEW.md` rusak.

**Selesai bila:** `test_smoke.py` keadaan `rusak` hijau untuk 47 CLI; titik yang menangkap `OSError` untuk
berkas absen tidak memperlakukan berkas rusak sebagai absen.

## E2 [Tinggi] quickdev: revisi rencana sesudah COMPLETED buntu
- [ ] Selesai

`review` Fase 5 → *Revisi rencana* → `unlock` → langkah baru → `lock` → `start` menghasilkan `mode=selesai`
(`plan_lock.py:166`), dan `close` ditolak karena status bukan IN_PROGRESS. **Perbaikan:** `COMPLETED*` dengan
langkah `[ ]` tersisa → `mode=resume` dan blok kembali ke `IN_PROGRESS`; `Base-Commit` tetap.

## E3 [Tinggi] quickdev: rencana tanpa `## 1.` → sidik kosong
- [ ] Selesai

`body_start = len(lines)` (`plan_lock.py:63`), sidik = sha256 string kosong, Section 1–5 bebas diubah.
**Perbaikan:** `lock` dan `verify` menagih heading `## 1.` sampai `## 5.` dan wilayah sidik tidak kosong.

## E4 [Sedang] quickdev: `Remediation-Round` rusak → traceback; tulis tidak atomik
- [ ] Selesai

`int()` di `:153,:230`. **Perbaikan:** nilai non-angka → FAIL rapi; `save()` menulis ke berkas sementara lalu
`os.replace`.

## E5 [Sedang] quickdev: blok status bisa dipalsukan; `confirm` tanpa `verify`; `lock` menimpa `Profile`
- [ ] Selesai

Blok `## Execution Status` tulisan tangan ber-`COMPLETED` dengan langkah 0/1 lolos `status`. **Perbaikan:**
`status --json` memuat `consistent` (COMPLETED ⇒ semua langkah `[x]`; review precondition 1 menagihnya);
`confirm` memanggil `verify`; `lock` tanpa `--profile` mempertahankan `Profile:` yang ada.

## E6 [Sedang] quickdev: Known issues diringkas → regresi palsu *(belum diverifikasi di sesi nyata)*
- [ ] Selesai

Profil memotong Known issues ke 10 baris; execute hanya mengenali galat bawaan lewat kolom itu.
**Perbaikan:** sel ringkasan (`<n> issue — contoh: …`) diperlakukan seperti baseline tanpa pembanding: galat di
berkas yang disentuh rencana = regresi, sisanya `UNVERIFIED` dan dilaporkan.

## E7 [Tinggi] analyst: pemulihan commit gagal menyarankan commit tanpa subjek kunci
- [ ] Selesai

`_commit_failed` (`ticket.py:379`) mencetak `git commit -- <paths>` tanpa `-m`. Commit manual itu membuat penerima
memvonis DRIFT, dan `approve` ulang ditolak. **Perbaikan:** pesan memuat `-m "<subjek kunci>"`; E8 menghapus
ketergantungan penerima pada subjek untuk tiket bersegel.

## E8 [Tinggi] Penerima tiket: DRIFT bergantung subjek commit; di luar git tanpa cek isi
- [ ] Selesai

`ticket_source_verdict` (be/fe `precondition_lib.py`): di luar git langsung PASS; di dalam git, commit suntingan
yang meniru subjek kunci ikut lolos. **Perbaikan:** `approve` menulis `approved_seal`; penerima menghitung segel yang
sama dan membandingkan; tanpa segel → jalur lama.

## E9 [Sedang] analyst: gerbang reviewer tiket bisa dilewati
- [ ] Selesai

`review --verdict PASS` tanpa `--report` diterima (`ticket.py:297`), dan sidik dicatat saat `review` dijalankan,
bukan saat reviewer membaca. **Perbaikan:** lihat Keputusan E9.

## E10 [Rendah] analyst: `--report` path hilang → traceback; pesan commit gagal memuat repr
- [ ] Selesai

## E11 [Rendah] analyst: `new --type` tidak dipakai; `cancel` tiket READY tanpa jaga
- [ ] Selesai

**Perbaikan:** `--type` menjadi opsional dan tercatat di keluaran `new` (elicit tetap penulis `type:`); `cancel`
READY menuntut `--force` dan meng-commit pembatalannya di repo git.

## E12 [Sedang] frontenddev: `lane_tamper` lolos tanpa commit `kunci TASK`
- [ ] Selesai

`precondition_lib.py:1057`: tanpa commit bersubjek persis, tidak ada pembanding → `""`. **Perbaikan:** pembanding
cadangan = commit pertama yang menambahkan `TASK.md`.

## E13 [Sedang] frontenddev: `review_is_fresh` bergantung subjek `implement unit`
- [ ] Selesai

## E14 [Rendah] frontenddev: `revisions_since_open` peka typo subjek
- [ ] Selesai

## E15 [Sedang] frontenddev: `code-reviewer` bisa memutasi repo
- [ ] Selesai

Tools `Read, Grep, Glob, Bash, Write, Edit`; batasnya hanya di `agents/code-reviewer.md:83-84`. **Perbaikan:** hook
PreToolUse `guard_bash.py` (Bash: git baca, `ls`, `chain.py files`; Write: `<taskdir>/REVIEW.md`; Edit:
`frontenddev/reviews/*.md`), dan `validate_review.py` menagih tree bersih selain `REVIEW.md` dan finding source.

## E16 [Rendah] frontenddev: `normalize_taskdir` tidak menolak `..`
- [ ] Selesai

## E17 [Rendah] frontenddev: dua pengklasifikasi state, nama berbeda
- [ ] Selesai

`taskdir_state.py` `TEMUAN` vs architect `TERHENTI (REVIEW BLOCKED)` untuk keadaan yang sama.

## E18 [Tinggi] backenddev: `landed_sha` membandingkan subjek persis
- [ ] Selesai

Satu spasi berlebih → `FASE_3:01`, brief yang sudah mendarat di-dispatch ulang; brief `DONE` tanpa commit
dipercaya. **Perbaikan:** normalisasi subjek; `DONE` tanpa commit mendarat → keadaan koreksi, bukan lanjut.

## E19 [Tinggi] backenddev: `code-reviewer` bisa `git reset --hard`
- [ ] Selesai

`guard_bash.py` hanya memagar implementor dan explorer. **Perbaikan:** kebijakan reviewer: git baca +
`merge-base`/`symbolic-ref`, `ls`, `git add`/`git commit -m` hanya atas `<taskdir>/REVIEW.md` dan
`backenddev/issues/README.md`; Write hanya kedua path itu.

## E20 [Sedang] backenddev: `chain_counters` — baris tak dikenal → `KeyError`; nilai bisa diturunkan tangan
- [ ] Selesai

**Perbaikan:** baris tak dikenal → FAIL rapi; `--check` membandingkan dengan riwayat git `TASK.md`: kunci global tidak
pernah turun, kunci ber-hop hanya turun di versi yang sama dengan kenaikan `reentry`.

## E21 [Sedang] backenddev: rute SYMBOL bertentangan
- [ ] Selesai

`architect/SKILL.md:89` dan `gate-lifecycle.md` (butir TERTAHAN) memperlakukan SYMBOL seperti SCOPE, sedangkan
`lifecycle-recovery.md:146`, `gate-lifecycle.md:115`, dan pesan `architect/scripts/check_preconditions.py:371`
menggolongkannya bersama COMPILE/STRAY. **Keputusan:** SYMBOL = SCOPE (user memutuskan terima atau reset).

## E22 [Rendah] `run_verification.py` merujuk `validate_review.py` yang tidak ada di backenddev
- [ ] Selesai

## E23 [Rendah] 6 WARN lint R1: rujukan singkat ambigu
- [ ] Selesai
