# Langkah 15 — Perubahan plugin `quickdev`

Rujukan: `01-mcp-tools.md`, yaitu tool T1–T10, kontrak identitas, dan pola pemakaian tool.
**Status:** PEMETAAN, belum dieksekusi.

## Ringkasan

- **Tidak ada taskdir.** Unit kerja quickdev adalah satu berkas rencana `<plan_dir>/<task_name>.md`. Satu rencana
  menjadi satu workdir berkunci `quickdev:<repo>:<path rencana>`, dengan nama `<task_name>`.
- **Task selalu dibuat baru.** Quickdev tidak berintegrasi dengan tiket analyst (`flow/quickdev.md` Handoff Lintas
  Plugin). Task dicari lewat `{"source":"quickdev","workdir_key":…}`; bila belum ada, task dibuat dengan judul H1
  rencana dan deskripsi Section 1 (Overview & Objectives).
- **Titik status datang dari `plan_lock.py`,** satu-satunya penulis `Status:` dan blok `## Execution Status`:
  `lock`, `close`, dan `confirm`.
- **Kendala khas quickdev:** skill tidak meng-commit, sehingga metadata `commit` bisa kosong. Keenam skill ber-
  `disable-model-invocation: true`, jadi sinkron berjalan di dalam skill yang dipanggil user, bukan sebagai skill
  terpisah.

## Artefak yang didorong

| Artefak | `type` | Didorong pada | Prioritas |
|---|---|---|---|
| `plan/<task>.md` (`Status: APPROVED`) | `QUICKDEV_PLAN` | `plan` Fase 4 sesudah `LOCK PASS`. Status workdir `active` | P0 |
| `plan/<task>.md` + blok `## Execution Status` | `QUICKDEV_PLAN` | `execute` Fase 4 sesudah `plan_lock.py close` (`COMPLETED`/`VERIFICATION_MANUAL_REQUIRED`), jalur `close --status BLOCKED` (Fase 0, 1, 3, dan Failure path), serta sesudah `confirm` (`COMPLETED (manual)`). Status workdir: `COMPLETED*` → `done`, `BLOCKED` → `blocked`, selain itu `active` | P0 |
| `plan/<task>.md` sesudah `unlock` | `QUICKDEV_PLAN` | Metadata `status: DRAFT` agar DB tidak tetap menampilkan `APPROVED` | P2 |
| Laporan `review` | — | Saat ini hanya terminal, tanpa berkas (lihat Q6) | P2 |
| `repo-profile.md` | `PROFILE` | Sesudah `profile` menulis profil. Menempel ke workspace (T10) | P2 |

Yang **tidak** didorong: laporan terminal `explore` dan `clarify`, serta `.claude/workflow`.

## Perubahan per bagian

| ID | Bagian | Ubah apa | Kenapa | Prioritas |
|---|---|---|---|---|
| Q1 | `skills/_common/nataflow_sync.py` (baru) | Salinan identik pustaka bersama | Sama dengan B1 backend | P0 |
| Q2 | `skills/_common/plan_lock.py`: subperintah `sync-payload --plan <p> [--remote -] [--json]` | Read-only. Menerbitkan `task` (lookup/create), `workdir` (nama, status dari `execution.Status`, metadata `Plan-Hash`/`Base-Commit`), dan dokumen rencana (isi + `content_sha256`). Rencana yang belum pernah `lock` → `FAIL` | `plan_lock.py` sudah mem-parse `Status:`, blok eksekusi, dan segel (`cmd_status`). Menaruh payload di sana menjaga satu sumber parsing rencana | P0 |
| Q3 | Referensi prosedur `nataflow-sync.md` (baru) | Tujuh langkah di `01` § Pola pemakaian tool | Dipakai `plan` dan `execute` | P0 |
| Q4 | `skills/plan/SKILL.md` Fase 4 | Sesudah `LOCK PASS`, jalankan Q3, lalu tawarkan `/quickdev:execute` | Titik rencana disetujui | P0 |
| Q5 | `skills/execute/SKILL.md` Fase 0 (mode `manual`), Fase 1, Fase 3, Fase 4, dan Failure path | Sesudah tiap `plan_lock.py close`/`confirm` yang berhasil, jalankan Q3 | Titik tutup eksekusi. Semua jalur `close` perlu dorongan, bukan hanya `COMPLETED`, supaya status `blocked` juga tercermin | P0 |
| Q6 | `skills/review/SKILL.md` | **Butuh keputusan:** (a) tetap terminal-only dan tidak didorong, atau (b) review menulis berkas `<plan_dir>/<task_name>.review.md` lalu mendorongnya sebagai `QUICKDEV_REVIEW` | D4 melarang model merangkai isi dokumen sendiri, dan laporan review saat ini bukan berkas. Opsi (b) mengubah sifat read-only `review` | P2 |
| Q7 | Status akhir tiap skill | Tambah segmen `nataflow <…>` di status terminal `plan`/`execute`. Periksa ulang test teks (`tests/quickdev/test_skill_text.py`, `test_08d_text.py`, `test_13_text.py`) | Kegagalan push harus terlihat (D4) | P0 |
| Q8 | Rute "sinkron ulang" | Karena quickdev tidak punya gerbang, rute ini menjadi mode di `execute` Fase 0 (`sinkron ulang <plan_path>`), atau cukup menjalankan Q3 lewat `/quickdev:plan` pada rencana `APPROVED` tanpa mengubahnya. Pilihannya diputuskan saat eksekusi | Jalan ulang untuk `GAGAL` | P1 |
| Q9 | Diff sebelum push | Sama dengan B8 backend (butuh T4) | Rencana dan blok eksekusinya berubah sedikit demi sedikit, sehingga dorongan ulang yang identik bisa dilewati | P1 |
| Q10 | Status task | `execute` mode awal → `in_progress`; `COMPLETED*` → `done`. Butuh T7 | Board mengikuti rencana | P2 |
| Q11 | `skills/profile/SKILL.md` | Dorong `repo-profile.md` ke workspace (T10) | Melengkapi "semua artefak" | P2 |
| Q12 | `README.md`, `flow/quickdev.md`, `.claude-plugin/plugin.json` | Seksi "Sinkron nataflow (opsional)"; Artefak & Siklus Status; Titik Gagal & Pemulihan; naikkan versi | Dokumen mengikuti perilaku | P0 |
| Q13 | Test | `plan_lock.py sync-payload`: rencana `DRAFT` → `FAIL`, pemetaan `execution.Status` → status workdir, rencana belum ter-commit → metadata `commit` kosong, byte-stabil, `SKIP`/`FAIL`; salinan pustaka identik; `CASES` smoke | Mengunci kontrak skrip | P0 |

## Yang tidak berubah

- Segel `Plan-Hash`, `Verified-Hash`, dan `Tree-Hash`. Sinkron tidak menulis berkas (D5), sehingga `review`
  tidak menolak rencana hanya karena sudah disinkronkan.
- Aturan "commit adalah keputusan user". Sinkron tidak meng-commit dan tidak mensyaratkan commit.
- Koeksistensi dengan hook backend/frontend lewat `.claude/workflow`.
