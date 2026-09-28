# Langkah 15 — Perubahan plugin `frontend` (frontenddev)

Rujukan: `01-mcp-tools.md`, yaitu tool T1–T10, kontrak identitas, dan pola pemakaian tool.
**Status:** SELESAI (tahap 4). F1–F15 terpasang; F11 lewat payload dua fase (E4). Tambahan di luar tabel F:
`architect` Phase 5 butir 4 (commit `REPORT.md` tertunda oleh architect) ikut tertangkap aturan sinkron di pembuka
`## Output` architect. Versi dinaikkan di commit rilis. Test: `tests/frontend/test_15_sync_payload.py` (12) + dua
`CASES` smoke; suite penuh 1925 hijau, lint 0 FAIL.

## Peta blast radius (sebelum kode)

| Berkas | Perubahan | Yang bisa pecah |
|---|---|---|
| `skills/_common/sync_payload.py` (baru, CLI) | F2/F9/F11–F13: `--taskdir` \| `--repo-docs review\|profile`, `--remote -`, `--json`. Ledger dibaca lewat `read_chain` + `verify_chain_row`; keadaan lewat subproses `lead/scripts/taskdir_state.py --json` (pola lintas skill yang sudah ada, bukan impor) | `test_smoke` inventaris; `test_profile_paths` (pakai `PROFILE_DIR_REL`); lint R4/S1 |
| `skills/lead/references/nataflow-sync.md` (baru) | Prosedur dua fase + varian dokumen repo | Lint R1 (skill lain merujuknya sebagai `lead/references/nataflow-sync.md`, preseden `lead/references/lane-routing-matrix.md`) dan R2 |
| `skills/task/SKILL.md` Phase 4 | Butir sinkron sesudah commit akar (butir 6 baru, "Catat SHA" menjadi 7); segmen di `### TASK ROOT LOCKED` | Tidak ada rujukan "Phase 4 butir 6"; `validate_task.py` hanya merujuk butir 2 |
| `skills/lead/SKILL.md` | Baris `AKAR` (commit akar tertinggal) + sinkron; rute sinkron ulang di samping tabel Phase 2; Phase 8 sesudah `reopen`/`escalate`/`abandon`/amandemen; segmen di baris `LEAD — …` | `test_j58f` (butir 1 Failure path tidak disentuh); `test_j43` (frasa terlarang); `test_j49`, `test_a1` parameter |
| `skills/{ux-design,ui-design,contract,plan}/SKILL.md` | Butir "Setuju": sinkron sesudah `chain.py approve` PASS; segmen di baris penutup gate | `test_j58d` (`frontend:code-explorer`), `test_j42` (`hop di atasnya`), `test_j58g`; rujukan "Phase 4 butir 3" ux-design tidak terdampak |
| `skills/architect/SKILL.md` | Satu aturan di pembuka `## Output`: sinkron sekali per putaran sebelum baris `ARCHITECT — …` atau blok `BLOCKED`/`TERTAHAN` (menangkap Phase 4 dan Phase 5 butir 4 tanpa menomori ulang); segmen/slot **Nataflow** | "Phase 5 butir 4" dikunci skrip dan 10 prosa → tidak disentuh; `test_j54` (Failure path 5/6), `test_j55`, `test_c9` (hindari "code-reviewer … tepat sekali"), `test_architects_use_runner_not_tail` |
| `skills/report/SKILL.md` Phase 4 | Sinkron sesudah commit `REPORT.md`; segmen di `### REPORT LOCKED` | Tidak ada rujukan bernomor ke butir sesudahnya |
| `skills/review/SKILL.md`, `skills/profile/SKILL.md` | F13: `--repo-docs review`/`profile` sesudah commit; segmen penutup | `test_j58e`, `test_j4_*` (profil) |
| `README.md`, `flow/frontend.md` | Seksi sinkron terpisah dari tabel "Mechanical Enforcement" | `test_j58h` menghitung baris tabel penjaga → `sync_payload.py` tidak dimasukkan ke tabel itu; `test_flow_frontend_menyebut_perilaku_baru`; `test_versi_rilis` (commit rilis) |
| `tests/frontend/test_15_sync_payload.py` (baru), `tests/test_smoke.py` | Kontrak skrip (F15) + dua `CASES` | — |

Keputusan tambahan: hop yang DRIFT juga ditahan dari aturan E7, supaya cermin tidak pernah menampilkan isi yang belum
disetujui berlabel `APPROVED`. Task sendiri: `TUNTAS` → `done`, `DITUTUP` → `cancelled`; task tiket hanya naik ke
`in_progress` (E8). "Eksekusi dimulai" = ada brief `DONE`/`BLOCKED`, `report-NN.md`, `REVIEW.md`, atau `REPORT.md`.

## Ringkasan

- **Jangkar.** Taskdir `frontenddev/docs/<YYMMDDhhmm>-<slug>/` menjadi workdir berkunci
  `frontenddev:<repo>:<path taskdir>`. Workdir menunjuk task tiket analyst bila `TASK.md` membawa `ticket_source`,
  atau task baru bila tidak. Taskdir backend dan frontend dari tiket yang sama bernaung di satu task.
- **Berbeda dari backend:** frontend tidak punya titik re-entry tunggal. `lead` hanya dipanggil ulang bila ada
  masalah (Phase 8), sehingga dorongan dipasang di tiap skill pemilik titik status: `task`, empat gate sesudah
  `chain.py approve`, `architect`, `report`, dan `lead` Phase 8.
- **Sinkron hanya di main loop.** Subagent (`code-implementor`, `code-reviewer`, `code-explorer`,
  `contract-reviewer`, `doc-reviewer`) tidak berubah.

## Artefak yang didorong

| Artefak | `type` | Didorong pada | Prioritas |
|---|---|---|---|
| `TASK.md` | `TASK` | Sesudah commit akar (`task` Phase 4, atau `lead` saat meng-commit akar tertinggal); ikut terbawa tiap approve, reopen, escalate, abandon, dan amandemen | P0 |
| `FLOW.md`, `UI.md`, `CONTRACT.md` | `FLOW`, `UI`, `CONTRACT` | Sesudah `chain.py approve --row <ROW>` PASS. `DRAFT` tidak didorong | P0 |
| `brief-<NN>-<unit>.md`, `REVIEW-PLAN.md` | `BRIEF`, `REVIEW_PLAN` | Sesudah `chain.py approve --row BRIEF` PASS. Brief frontend sudah `READY` sejak draft breakdown, jadi syaratnya hop BRIEF `[x]`, bukan status brief | P0 |
| Brief `DONE`/`BLOCKED`, `report-<NN>.md` | `BRIEF`, `UNIT_REPORT` | `architect` Phase 4 sesudah commit `REVIEW.md`, atau saat rantai berhenti (unit BLOCKED, verifikasi merah, berkas yatim) | P0 |
| `REVIEW.md` | `REVIEW` | `architect` Phase 4 sesudah commit `docs(<slug>): closing review <verdict>` | P0 |
| `REPORT.md` | `REPORT` | `report` Phase 4 sesudah commit. Status workdir menjadi `done` | P0 |
| `frontenddev/reviews/*.md`, `.claude/profile/frontenddev/*.md` | `ADHOC_REVIEW`, `PROFILE` | Sesudah `review`/`profile` menulis berkasnya. Menempel ke workspace (T10) | P2 |

Yang **tidak** didorong: `<taskdir>/.explore/`, `.frontenddev/explore/`, dan dokumen gate `DRAFT`.

## Perubahan per bagian

| ID | Bagian | Ubah apa | Kenapa | Prioritas |
|---|---|---|---|---|
| F1 | `skills/_common/nataflow_sync.py` (baru) | Salinan identik pustaka bersama | Sama dengan B1 backend | P0 |
| F2 | `skills/_common/sync_payload.py` (baru) | CLI read-only `--taskdir <td> [--point <titik>] [--remote -] [--json]`. Aturan pilih berkas: `TASK.md` selalu; `FLOW`/`UI`/`CONTRACT` hanya bila baris ledger-nya `[x]` dan tidak `DRIFT`; brief dan `REVIEW-PLAN.md` bila hop BRIEF `[x]` atau brief sudah `DONE`/`BLOCKED`; `report-<NN>.md`, `REVIEW.md`, dan `REPORT.md` bila ter-commit. Status workdir diturunkan dari `taskdir_state.py`: `TUNTAS` → `done`, `DITUTUP` → `abandoned`, `TERHENTI`/`TEMUAN` → `blocked`, selain itu `active`. Lookup task seperti B2 backend dengan `source: frontenddev` | D4. Memakai ulang `chain.py` (ledger dan `verify`) serta `taskdir_state.py`, supaya definisi "stabil" sama dengan yang dipakai gerbang. Sengaja bukan subperintah `chain.py`, karena `chain.py` adalah satu-satunya penulis ledger sedangkan sinkron read-only | P0 |
| F3 | Referensi prosedur `nataflow-sync.md` (baru) | Tujuh langkah di `01` § Pola pemakaian tool, dengan larangan yang sama dengan B3 backend | Satu prosedur dipakai tujuh titik panggil | P0 |
| F4 | `skills/task/SKILL.md` Phase 4 + `skills/lead/SKILL.md` (commit akar tertinggal, keadaan `AKAR` #5) | Sesudah commit akar, jalankan F3 (`--point root`) | Workdir dan tautan task lahir sejak awal, sehingga board nataflow menunjukkan kerja yang sedang berjalan | P0 |
| F5 | `skills/ux-design/SKILL.md` Phase 5, `ui-design` Phase 6, `contract` Phase 6, `plan` Phase 5 | Butir "Setuju": sesudah `chain.py approve` PASS, jalankan F3 (`--point approve:<ROW>`) | `chain.py approve` adalah satu-satunya titik `APPROVED` (`flow/frontend.md` Alur Utama butir 4) | P0 |
| F6 | `skills/architect/SKILL.md` Phase 4 dan Phase 5 | Sesudah commit `REVIEW.md` dan sebelum baris `ARCHITECT — …` atau blok `### ARCHITECT — BLOCKED`/`TERTAHAN`, jalankan F3 (`--point architect`) | Satu dorongan per putaran eksekusi menangkap status unit, laporan unit, dan review | P0 |
| F7 | `skills/report/SKILL.md` Phase 4 | Sesudah commit `REPORT.md`, jalankan F3 (`--point report`) | Titik tuntas taskdir | P0 |
| F8 | Baris keluaran: handoff `LEAD — …`, `ARCHITECT — COMPLETED …`, penutup `report`, dan penutup tiap gate | Tambah segmen `nataflow <…>` (`01` langkah 7). Periksa ulang test teks (`tests/frontend/test_08c_text.py`, `test_12_orchestration.py`) | Kegagalan push harus terlihat (D4) | P0 |
| F9 | `skills/lead/SKILL.md` Phase 8 | Sesudah `chain.py reopen`/`escalate`/`abandon` atau amandemen akar, jalankan F3. Pada `reopen`, dokumen hop yang dibuka didorong ulang dengan metadata `status` terbaru; pada `abandon`, status workdir menjadi `abandoned` | Tanpa ini, DB tetap menampilkan dokumen `APPROVED` yang sebenarnya sedang dibuka ulang, atau taskdir yang sudah ditutup | P1 |
| F10 | `skills/lead/SKILL.md`: rute "sinkron ulang taskdir `<td>`" | Rute pemulihan yang menjalankan F3 penuh tanpa mengubah keadaan taskdir. Letaknya di samping tabel keadaan Phase 2 | Jalan ulang untuk `GAGAL` (analog 14 N4) | P1 |
| F11 | F2 + F3: diff sebelum push | Sama dengan B8 backend (butuh T4) | Tujuh titik panggil per taskdir, sehingga `TASK.md` saja bisa terkirim ulang tujuh kali tanpa diff | P1 |
| F12 | Status task | `architect` Phase 1 unit pertama → `in_progress`; `report` → `done`; `abandon` → `cancelled`. Butuh T7 | Board mengikuti rantai | P2 |
| F13 | `skills/review/SKILL.md`, `skills/profile/SKILL.md` | Dorong `frontenddev/reviews/*.md` dan profil ke workspace (T10) | Melengkapi "semua artefak" | P2 |
| F14 | `README.md`, `flow/frontend.md`, `.claude-plugin/plugin.json` | Seksi "Sinkron nataflow (opsional)"; di flow: Artefak & Siklus Status, pola tiap gate, `architect`, Titik Gagal & Pemulihan; naikkan versi | Dokumen mengikuti perilaku | P0 |
| F15 | Test | `sync_payload.py`: hop `[x]` vs `DRAFT`, `DRIFT` tidak didorong, brief sebelum approve BRIEF tidak ikut, pemetaan keadaan `taskdir_state` → status workdir, `ticket_source` → `ticket_key`, byte-stabil, `SKIP`/`FAIL`; `CASES` smoke; salinan pustaka identik | Mengunci kontrak skrip | P0 |

## Yang tidak berubah

- `chain.py`, `review_round.py`, dan semua validator. Materai approve (`Konten disetujui:`, `Sidik:`) tidak
  tersentuh karena sinkron tidak menulis berkas (D5).
- Hook `guard_bash.py`, yang matcher-nya hanya `Bash|Edit|Write`.
- Subagent, dispatcher, dan kepemilikan commit.

## Titik gagal

| Gejala | Perilaku |
|---|---|
| Config absen | Segmen `nataflow dilewati` |
| Config rusak / server mati / tool galat / sha ditolak | Segmen `nataflow GAGAL: <sebab>`. Gate dan eksekusi tetap lanjut. Ulang lewat F10 |
| Tiket backend dan frontend memakai `workspace_id` berbeda | Tergantung keputusan T2(a) di `01`. Bila server menolak task lintas workspace → `GAGAL` dengan pesan server |
