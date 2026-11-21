# Langkah 41 — `quickdev`: task nataflow acuan, rencana DRAFT tercermin sebelum approval, dan dokumen report (D1–D4)

Sumber: feedback pemakaian quickdev (2026-11-21). Basis kode: commit `bc0e3f4` (quickdev 0.13.0).

**Status (2026-11-21):** SELESAI di branch `feat/quickdev-041-acuan-task-report`; quickdev 0.14.0
(`src/plugins/quickdev/MIGRATION_v0.13.x_to_v0.14.0.md`). Test baru: `tests/quickdev/test_41_acuan_report.py`.
Belum: PR dan uji lapangan.

## Feedback

1. Kalau task sudah ada di nataflow, pakai itu sebagai acuan, dan quickdev jangan membuat task lagi (tidak wajib:
   tanpa acuan, alur lama tetap).
2. Saat `plan` mengajukan approval, dokumen rencana wajib sudah ada di nataflow supaya bisa dibaca di sana.
3. Selesai eksekusi, task menjadi `done`.
4. Terbitkan dokumen report tentang apa yang dikerjakan, dengan ringkasan naratif singkat.

## Keputusan

- **D1 — task acuan.** `plan_lock.py task --ref <code|uuid>` membaca task lewat `get_task` (skrip, MCP key lokal) dan
  mencetak judul, status, workspace, sumber, dan `description` apa adanya; `plan` Fase 0 memakainya sebagai
  `task_spec`. `--plan` menautkannya ke rencana DRAFT sebagai metadata `Nataflow-Task: <uuid>` (UUID, bukan kode:
  kode hanya unik per workspace). Sinkron rencana bertautan memakai `get_task` saja: tidak pernah `create_task`
  maupun `update_task`; statusnya digeser dengan aturan yang sama (`in_progress` sejak `lock`, `done` lewat aturan
  saudara 28 T2 karena task tiket bisa menaungi taskdir backend/frontend). Tautan tidak bisa diganti, hanya
  ditulis saat DRAFT, dan task `cancelled` ditolak. Workdir yang sudah menempel di task lain (rencana yang dulu
  tersinkron tanpa acuan) → `GAGAL` sebelum tulisan apa pun.
- **D2 — DRAFT terdorong sebelum approval** (D2 lama 15 Q13 dibalik). `sync_context` menerima DRAFT tanpa target
  status task (task baru tetap `todo`); `plan` Fase 4 menjalankan prosedur sinkron sebelum ringkasan gerbang dan
  menampilkan baris `NATAFLOW: task #<kode> · …`. Config ada tetapi sinkron `GAGAL` → approval ditahan:
  *Coba lagi* · *Lanjut tanpa cermin nataflow* (keputusan user). Karena task milik quickdev kini lahir saat DRAFT,
  judul/deskripsinya diselaraskan ke rencana terbaru (`get_task` → `update_task` hanya bila berbeda); task acuan
  tidak pernah diselaraskan.
- **D3 — task `done`.** Sudah berjalan sejak 15 Q10 (`COMPLETED*` → `done`, dari `todo`/`in_progress`); tidak ada
  kode baru selain jalur task acuan (aturan saudara).
- **D4 — dokumen report.** Dokumen kedua di workdir: key `<task>.report.md`, tipe `quickdev.report` (didaftarkan user
  di server). Disusun skrip dari disk sesudah blok eksekusi tertutup (`COMPLETED*`, `VERIFICATION_MANUAL_REQUIRED`,
  `BLOCKED`): ringkasan naratif, status/base, AC Section 1, checklist, berkas berubah sejak `Base-Commit` (rumus
  berkas `tree_hash`, tanpa direktori rencana), verifikasi, baseline, temuan review. Ringkasan naratif ditulis
  subperintah baru `plan_lock.py summary --summary -` (1–3 kalimat, ≤ 600 karakter) ke `Summary` blok sesudah
  `close`; subperintah terpisah karena `close` sudah memakai stdin untuk `--verification`. `start` putaran baru
  mengosongkannya. Report yang gagal didorong (mis. tipe belum terdaftar) tidak menggagalkan sinkron rencana:
  segmen ditambah `· report GAGAL: <sebab>`.

## Trade-off yang diterima

- Rencana yang dibatalkan sebelum approval meninggalkan task `todo` di nataflow (penanda abandon di luar lingkup).
- Sinkron di Fase 4 menambah satu putaran panggilan server per revisi draf.
- Isi task acuan masuk konteks model (ia spesifikasinya); isi dokumen yang didorong tetap tidak.
- `nataflow_sync.py` bersama tidak disentuh: `push_plan` milik quickdev menyusun ulang alur `push_workdir` di
  `plan_lock.py`, supaya hanya quickdev yang naik versi.

## Blast radius

`skills/_common/plan_lock.py` (`task`, `summary`, `task_ref`, `changed_files`, `report_text`, `plan_task`,
`push_plan`, `plan_segment`, `sync_context`), SKILL `plan`/`execute`, `skills/plan/references/nataflow-sync.md`,
`README.md`, migrasi 0.14.0, `flow/quickdev.md`, `CLAUDE.md`, `tests/nataflow_fake.py` (`get_task`, saringan `key`
`list_workdir`), `tests/quickdev/test_15_sync.py` (Q13 dibalik), `tests/quickdev/test_29_push.py` (segmen
`task #`), `tests/quickdev/test_41_acuan_report.py`, `tests/test_smoke.py` (kasus `summary`, `task`).
