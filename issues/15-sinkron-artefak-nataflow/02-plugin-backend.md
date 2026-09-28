# Langkah 15 — Perubahan plugin `backend` (backenddev)

Rujukan: `01-mcp-tools.md`, yaitu tool T1–T10, kontrak identitas, dan pola pemakaian tool.
**Status:** PEMETAAN, belum dieksekusi.

## Ringkasan

- **Jangkar.** Taskdir `backenddev/docs/<YYMMDDhhmm>-<slug>/` menjadi workdir berkunci
  `backenddev:<repo>:<path taskdir>`. Workdir menunjuk task tiket analyst bila frontmatter `TASK.md` membawa
  `ticket_source`, atau task baru bila tidak.
- **Tiga titik panggil:** `analyst` Fase 2 (akar terkunci), `analyst` Fase 4 (BRD/PRD `APPROVED`), dan
  `tech-lead` Fase 5 (re-entry). Fase 5 menjadi titik sapu karena semua skill hilir (`plan` jalur RCA, `debug`,
  `architect`, `report`, `audit`, `document-api`, `profile`) pulang ke sana (`flow/backend.md` Alur Utama butir 6).
- **Sinkron hanya di main loop.** Subagent (`code-implementor`, `code-reviewer`, `code-explorer`, dan ketiga
  reviewer dokumen) tidak berubah dan tidak memanggil MCP.

## Artefak yang didorong

| Artefak | `type` | Didorong pada | Prioritas |
|---|---|---|---|
| `TASK.md` | `TASK` | Akar terkunci (`analyst` Fase 2 / `tech-lead` Fase 5 untuk lane `DEFECT_RCA` dan backfill `EXEC_BRIEF`); ikut terbawa tiap titik lain bila ledger atau amandemen mengubahnya | P0 |
| `BRD.md`, `PRD.md` | `BRD`, `PRD` | Sesudah commit `docs(spec): approve …` dan centang ledger (`analyst` Fase 4). `DRAFT` tidak didorong | P0 |
| `brief-NN-<unit>.md` | `BRIEF` | `tech-lead` Fase 5: sesudah batch `READY` ter-commit, dan sesudah `architect` (`DONE`/`BLOCKED`/`SUPERSEDED`) | P0 |
| `REVIEW.md`, `REPORT.md` | `REVIEW`, `REPORT` | `tech-lead` Fase 5 sesudah `architect` kembali. `REPORT.md` membuat status workdir `done` | P0 |
| `RCA.md` | `RCA` | `tech-lead` Fase 5 sesudah `debug` kembali dan `RCA.md` di-commit gerbang | P1 |
| `report-NN.md`, `HALT.md` | `UNIT_REPORT`, `HALT` | `tech-lead` Fase 5 sesudah `architect` `BLOCKED`/`TERTAHAN`. `HALT.md` yang dicabut didorong ulang dengan metadata `removed: true` | P1 |
| `backenddev/issues/*.md`, `docs/api/*.md`, `.claude/profile/backenddev/*.md` | `AUDIT`, `API_DOC`, `PROFILE` | `tech-lead` Fase 5 sesudah `audit`/`document-api`/`profile` kembali. Menempel ke workspace (T10) | P2 |

Yang **tidak** didorong: `<taskdir>/.explore/`, `backenddev/docs/.explore/`, dan BRD/PRD `DRAFT`.

## Perubahan per bagian

| ID | Bagian | Ubah apa | Kenapa | Prioritas |
|---|---|---|---|---|
| B1 | `skills/_common/nataflow_sync.py` (baru) | Salinan identik pustaka bersama (`01` § Pola pemakaian tool), termasuk pembaca `.claude/nataflow.json` | Satu aturan config, identitas repo, dan sha untuk empat plugin | P0 |
| B2 | `skills/_common/sync_payload.py` (baru) | CLI read-only `--taskdir <td> [--point <titik>] [--remote -] [--json]` yang menerbitkan `task.lookup/create`, `workdir`, dan `documents` (isi + `content_sha256` + metadata). Aturan pilih berkas: `TASK.md` selalu; BRD/PRD hanya `APPROVED`; brief semua status; `RCA.md`, `report-NN.md`, `HALT.md`, `REVIEW.md`, `REPORT.md` bila ada; `.explore/` tidak pernah. Status workdir diturunkan dari disk: `REPORT.md` ada → `done`, `HALT.md` atau brief `BLOCKED` → `blocked`, selain itu `active`. `--point` membatasi pilihan ke berkas titik itu selama T4 belum ada. Lookup task: `ticket_source` → `{"source":"analyst","ticket_key":<dirname>}`, tanpa tiket → `{"source":"backenddev","workdir_key":…}` | D4: isi dan pemilihan berkas ditentukan skrip, bukan dirangkai model. Pembacaan status memakai ulang `brief_status.py` dan parser frontmatter `precondition_lib.py` | P0 |
| B3 | Referensi prosedur `nataflow-sync.md` (baru, diadaptasi dari analyst `skills/spec/references/nataflow-sync.md`) | Tujuh langkah di `01` § Pola pemakaian tool, beserta larangan: menyunting argumen, mengirim argumen di luar payload, mengulang `create_task`/`upsert_*` sesudah galat tanpa `list_task` ulang, dan menjalankan sinkron dari subagent | Satu prosedur dipakai tiga titik panggil | P0 |
| B4 | `skills/analyst/SKILL.md` Fase 2 dan Fase 4 | Fase 2: sesudah `### TASK ROOT LOCKED` terverifikasi, jalankan B3 (`--point root`). Fase 4: sesudah commit approve dan centang ledger, jalankan B3 (`--point approve`) | Kedua titik status ini terjadi di dalam `analyst` tanpa kembali ke gerbang. Tanpa B4, BRD/PRD `APPROVED` baru tercermin di akhir perencanaan | P0 |
| B5 | `skills/tech-lead/SKILL.md` Fase 5 + `references/gate-lifecycle.md` bagian 6 | Sesudah "commit artefak yang menunggu", jalankan B3 atas taskdir pengirim (`--point` sesuai baris tabel pengirim balik) sebelum langkah lanjut ditentukan | Satu titik menangkap brief `READY`/`DONE`/`BLOCKED`, `RCA.md`, `HALT.md`, `REVIEW.md`, `REPORT.md`, dan amandemen akar | P0 |
| B6 | Blok keluaran `### PLANNING CHAIN REPORT` dan `### TECH-LEAD RE-ENTRY DECISION` | Tambah baris `Nataflow: <segmen>` (`01` langkah 7). Periksa ulang test yang mengunci teks `tech-lead`/`analyst` `SKILL.md` (`tests/backend/test_l28_tech_lead.py`, `test_l211_route_lint.py`, `test_l212_output_lint.py`, `test_11_robustness.py`) | Keputusan tidak-memblokir (D4) hanya aman bila kegagalan terlihat | P0 |
| B7 | `tech-lead`: rute "sinkron ulang taskdir `<td>`" | Varian re-entry tanpa lane baru: prasyarat `--read-only`, tanpa provisi taskdir/branch, jalankan B3 penuh (`--point all`), lalu selesai. Catat di `references/gate-scope.md` sebagai permintaan yang tetap lewat gerbang | `GAGAL` tidak menahan rantai, jadi harus ada jalan ulang (analog 14 N4) | P1 |
| B8 | B3 + B2: diff sebelum push | Sisipkan langkah `list_document include_content=false` → `sync_payload.py --remote -`, sehingga hanya berkas ber-sha beda yang dikirim. Bergantung T4 | Fase 5 dilewati berkali-kali per taskdir. Tanpa diff, tiap re-entry mengirim ulang puluhan KB | P1 |
| B9 | `tech-lead` Fase 5: status task | `architect` mulai → `in_progress`; `COMPLETED` → `done`. Bergantung T7 | Board nataflow mengikuti rantai | P2 |
| B10 | `tech-lead` Fase 5: artefak non-taskdir | Pengirim `audit`/`document-api`/`profile` memicu dorongan T10 ke workspace | Melengkapi "semua artefak", tapi bukan bagian rantai task | P2 |
| B11 | `README.md`, `flow/backend.md`, `.claude-plugin/plugin.json` | Seksi "Sinkron nataflow (opsional)" di README; di `flow/backend.md`: Artefak & Siklus Status, `tech-lead` Fase 5, `analyst` Fase 2/4, Titik Gagal & Pemulihan; naikkan versi (lint M7) | Dokumen mengikuti perilaku | P0 |
| B12 | Test | Salinan pustaka identik lintas plugin; `sync_payload.py` (DRAFT dan `.explore/` tidak ikut, `SUPERSEDED` ikut, turunan `ticket_key` dari `ticket_source`, status workdir, keluaran byte-stabil, `SKIP` tanpa config, `FAIL` config rusak); `CASES` di `tests/test_smoke.py` untuk empat keadaan repo | Mengunci kontrak skrip, pola langkah 14 N2/N6 | P0 |

## Yang tidak berubah

- **Kepemilikan commit** (`flow/backend.md` tabel commit) dan seluruh validator. Sinkron berjalan sesudah commit dan
  tidak menulis berkas (D5), sehingga check `Git Clean Working Tree` dan kesegaran `REVIEW.md` tidak terdampak.
- **Hook `guard_bash.py`.** Matcher-nya hanya `Bash|Edit|Write` (`hooks/hooks.json`), jadi panggilan MCP dari main
  loop tidak tersentuh pagar.
- **Subagent dan dispatcher.**

## Titik gagal

| Gejala | Perilaku |
|---|---|
| `.claude/nataflow.json` absen | Segmen `nataflow dilewati`, rantai jalan normal |
| Config rusak / server mati / tool galat / sha ditolak | Segmen `nataflow GAGAL: <sebab>`, rantai lanjut. Ulang lewat B7 |
| `list_task` mengembalikan lebih dari 1 task | `GAGAL` tanpa menulis apa pun |
