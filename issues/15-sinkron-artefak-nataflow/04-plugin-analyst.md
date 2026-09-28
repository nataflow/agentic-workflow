# Langkah 15 — Perubahan plugin `analyst`

Rujukan: `01-mcp-tools.md`, yaitu tool T1–T10, kontrak identitas, dan pola pemakaian tool.
**Status:** SELESAI (tahap 5). A1–A4 dan A6–A9 terpasang; A5 tidak dikerjakan (E2). A6 memakai rute
`analyst:intake` → `analyst:spec` (`cancel_request`) supaya intake tetap tidak menulis berkas; "pernah READY" =
`approved_hash` terisi atau `reopened` > 0. Versi dinaikkan di commit rilis. Test: `tests/analyst/test_ticket_15.py`
(9, termasuk A7 lintas plugin) dan penyesuaian `test_ticket_14.py`; suite penuh 1934 hijau, lint 0 FAIL.

## Peta blast radius (sebelum kode)

| Berkas | Perubahan | Yang bisa pecah |
|---|---|---|
| `skills/_common/analyst_lib.py` | A1: `load_sync_config` mendelegasikan ke `nataflow_sync.load_config(root, "analyst/nataflow.json")`; implementasi lama (`SYNC_KEYS`, `SYNC_DEFAULT_SERVER`, `UUID_RE`) dibuang karena tidak dipakai di tempat lain | `test_ticket_14::test_config_default_dan_nilai_eksplisit` (kesamaan dict persis → kunci `repo` ikut); substring pesan `test_config_rusak_terlapor` tetap terpenuhi pesan pustaka; pesan kini sudah berawalan nama berkas → `ticket.py` tidak menambah awalan lagi |
| `skills/_common/ticket.py` `cmd_sync_payload` | A2 identitas repo dari pustaka; A3 `repo` di metadata `create`/`update` (sesudah `ticket_key`), tidak di `lookup`; A4 `documents: [review.md]` (isi disk, `TICKET_REVIEW`) bila `review_report` sah; A6 tiket `DIBATALKAN` yang pernah READY (`approved_hash` terisi atau `reopened` > 0) → `PASS` berisi `lookup` + `task_status` `cancelled`, tanpa `create`/`update` | `test_ticket_14::test_pass_isi_payload_dari_kartu` (`META_KEYS` dan kesamaan `update`); `test_bukan_ready_ditolak[DIBATALKAN]` tetap `FAIL` karena fixture-nya membatalkan DRAFT yang belum pernah READY; `test_smoke` (keadaan `rusak` kini juga merusak `.claude/nataflow.json`) |
| `skills/spec/references/nataflow-sync.md` | Config bersama + `repo`; langkah `upsert_document` sesudah task; cabang pembatalan (`update_task_status`) | Lint R2 |
| `skills/spec/SKILL.md` | Parameter `cancel_request` + Precondition pembatalan (analog `change_request`); sinkron sesudah `cancel` tiket yang pernah READY (termasuk Phase 5 butir 5); baris `SPEC — BATAL`; Failure path 6 menyebut config bersama | Frontmatter `description` (lint F1/F3: tetap "Dipanggil …" + `user-invocable: false`) |
| `skills/intake/SKILL.md` | Phase 2: baris "Membatalkan tiket" → `analyst:spec` dengan `cancel_request` (intake tetap tidak menulis berkas); rute sinkron ulang menerima `DIBATALKAN` yang pernah READY | Iron Law "gate ini tidak menulis berkas" tetap berlaku |
| `README.md`, `flow/analyst.md` | A8 | `test_a1::test_klaim_analyst_bukan_lagi_manual` (frasa terlarang di README) |
| `tests/analyst/test_ticket_14.py`, `tests/analyst/test_ticket_15.py` (baru), `tests/test_15_nataflow_sync.py` | A9 + A7 (turunan `ticket_key` backend/frontend = analyst; `lookup` ketiganya byte-identik) | — |

## Ringkasan

- **Sudah berjalan sejak langkah 14:** tiket `READY` dicerminkan menjadi task (`create_task`/`update_task`).
  Kartu menjadi `description`, dan metadata `ticket_key` menjadi identitasnya (`skills/spec/references/nataflow-sync.md`,
  `ticket.py sync-payload` `skills/_common/ticket.py:700`).
- **Jangkar tetap task, tanpa workdir.** Tiket bukan taskdir, jadi dokumen analyst menempel langsung ke task
  (`reference_table: task`).
- **Tidak ada perubahan P0.** Sinkron analyst yang ada tetap sah tanpa perubahan apa pun di sini. Perubahan di bawah
  menyelaraskannya dengan pola bersama dan menambah artefak yang belum ikut.
- **Peran baru analyst:** task tiket kini menjadi induk workdir backend/frontend. Kontrak `ticket_key` berubah dari
  detail internal menjadi antarmuka lintas plugin.

## Artefak

| Artefak | Keadaan sekarang | Sesudah langkah 15 | Prioritas |
|---|---|---|---|
| Kartu `TICKET.md` (H1 s.d. `## Lampiran`) | `description` task | Tetap. Tidak digandakan sebagai dokumen | — |
| `review.md` (blok `## Ticket Review` terakhir) | Tidak dikirim | Dokumen `TICKET_REVIEW`, `key: review.md`, di bawah task | P1 |
| `## Catatan Elisitasi` | Sengaja tidak dikirim (14 K5) | Opsional, opt-in (A5) | P2 |
| Frontmatter (`requester`, pembukuan) | Sengaja tidak dikirim | Tetap tidak dikirim | — |

## Perubahan per bagian

| ID | Bagian | Ubah apa | Kenapa | Prioritas |
|---|---|---|---|---|
| A1 | `skills/_common/analyst_lib.py` (`SYNC_CONFIG`, `load_sync_config`) | Baca `.claude/nataflow.json` (config bersama). `analyst/nataflow.json` tetap diterima demi kompatibilitas, tetapi bila keduanya ada dan isinya berbeda → `FAIL`. Kunci `repo` ditambahkan ke daftar kunci sah | Repo yang memakai analyst + backend/frontend cukup memiliki satu config. Tanpa ini, user harus menjaga dua berkas identik | P1 |
| A2 | `skills/_common/nataflow_sync.py` (baru) + `ticket.py` | Salinan identik pustaka bersama. `ticket.py sync-payload` memakai pembaca config dan identitas repo dari pustaka itu, sementara bentuk keluaran lama (`lookup`/`create`/`update`) dipertahankan byte-demi-byte | Satu aturan untuk empat plugin, ditagih test identitas salinan | P1 |
| A3 | `ticket.py sync-payload`: metadata task | Tambah kunci `repo` di `create.metadata`/`update.metadata`, **tidak** di `lookup` | `ticket_key` adalah path relatif repo, sehingga `repo` membedakan asal di UI dan untuk engineer. `lookup` tidak berubah supaya task lama tanpa `repo` tetap ditemukan (saringan containment) | P1 |
| A4 | `ticket.py sync-payload` + `references/nataflow-sync.md` | Payload menambah `documents: [review.md]` (isi + `content_sha256`). Prosedur menambah langkah sesudah task: `upsert_document` dengan `reference_table: task`, `reference_id` = id task dari langkah 3. Berlaku juga untuk rute sinkron ulang `analyst:intake`. Butuh T3 | `review.md` adalah satu-satunya artefak analyst selain `TICKET.md`, dan berisi bukti review independen yang meloloskan kartu | P1 |
| A5 | Config + `sync-payload` | Opt-in `include_elicitation: true` mendorong `## Catatan Elisitasi` sebagai dokumen `TICKET_NOTES` tanpa frontmatter | 14 K5 sengaja hanya menyalin kartu, dan `requester` tetap di disk. **Butuh keputusan user** apakah catatan elisitasi boleh masuk DB | P2 |
| A6 | `ticket.py cancel` → prosedur sinkron | Tiket `READY` yang dibatalkan (`cancel --force`) → `update_task_status cancelled`. Butuh T7 | Mengisi "sinkron status" dan "pembatalan tiket" yang tercatat di `## Sengaja Belum Ada` README | P2 |
| A7 | Test lintas plugin | Test bahwa turunan `ticket_key` di `sync_payload.py` backend/frontend (dirname `ticket_source`) sama dengan `ticket_key` analyst untuk ticketdir yang sama, mengikuti pola `tests/test_a1_ticket_source.py` | Kalau salah satu sisi berubah, taskdir engineer akan menempel ke task lain atau membuat task kembar | P1 |
| A8 | `README.md`, `flow/analyst.md`, `.claude-plugin/plugin.json` | `## Sinkron nataflow (opsional)`: config bersama, `review.md`. `## Sengaja Belum Ada`: hapus "artefak engineer". Bullet "Cermin nataflow" di Handoff Lintas Plugin: artefak engineer kini menempel ke task yang sama lewat workdir. Naikkan versi | Dokumen mengikuti perilaku | P1 |
| A9 | Test | `tests/analyst/test_ticket_14.py` disesuaikan: config bersama, konflik dua config, `repo` di metadata tapi tidak di `lookup`, `documents` berisi `review.md` dengan sha benar; smoke tetap valid di empat keadaan repo | Mengunci kompatibilitas mundur | P1 |

## Yang tidak berubah

- `ticket.py approve`/`reopen`/`revise`/`ref`, segel `ticket_seal`, kedua validator, dan penerima `ticket_source`
  backend/frontend. Aturan 14 tetap: sinkron tidak menulis `TICKET.md`, `GAGAL` tidak menurunkan `READY`, dan status
  task tidak dikirim oleh analyst kecuali lewat A6.
- `lookup` task (`{"source":"analyst","ticket_key":…}`), supaya task hasil langkah 14 tetap ditemukan.
