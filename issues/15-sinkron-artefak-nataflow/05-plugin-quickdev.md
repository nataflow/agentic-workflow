# Langkah 15 — Perubahan plugin `quickdev`

Rujukan: `01-mcp-tools.md`, yaitu tool T1–T10, kontrak identitas, dan pola pemakaian tool.
**Status:** SELESAI (tahap 2, dikerjakan lebih dulu dari backend sebagai pilot prosedur karena plugin terkecil).
Q1–Q5, Q7–Q13 terpasang; Q6 opsi (a) tanpa perubahan (E3); Q9 lewat payload dua fase (E4). Versi dinaikkan di commit
rilis. Test: `tests/quickdev/test_15_sync.py` (17) dan dua kasus smoke baru; suite penuh 1876 hijau, lint 0 FAIL.

## Peta blast radius (sebelum kode)

| Berkas | Perubahan | Yang bisa pecah |
|---|---|---|
| `skills/_common/plan_lock.py` | Subperintah `sync-payload (--plan <p> \| --repo-profile <p>) [--remote -] [--json]` ditangani sebelum cek berkas rencana, sehingga config absen tetap `SKIP` | Dispatch `globals()[f"cmd_{a.cmd}"]` gagal pada tanda hubung; semua subparser lain mewajibkan `--plan`; cek `path.is_file()` berjalan sebelum subperintah; `die()` berbentuk `{"status","error"}`. Karena itu `sync-payload` diurus di jalur sendiri tanpa mengubah jalur subperintah lama |
| `skills/plan/references/nataflow-sync.md` (baru) | Prosedur dua fase (01 § Protokol), varian rencana dan profil | Lint R1/R2: rujukan dari SKILL memakai `${CLAUDE_PLUGIN_ROOT}/skills/plan/references/…`, dan berkas referensinya sendiri tidak memuat `${CLAUDE_PLUGIN_ROOT}` |
| `skills/plan/SKILL.md` | Fase 4 butir sinkron sesudah `LOCK PASS`; baris `NATAFLOW:` di ringkasan; sinkron sesudah `unlock`; rute sinkron ulang (Q8) | `test_08d_text` d1/d7/d12 dan `test_13_text` q4 (substring dan larangan kutip ganda). Tidak ada test yang mengunci format ringkasan |
| `skills/execute/SKILL.md` | Satu aturan di Konvensi `plan_lock.py`: sesudah tiap `close`/`confirm` PASS jalankan sinkron (Fase 0 butir 3, Fase 1 butir 4, Fase 3 butir 3, Fase 4 butir 1, Failure path 2/5); baris `NATAFLOW:` | `test_13_text` q1–q16 memotong seksi pada `### Fase 0/1/3/4`, `## Guardrails`, dan butir parameter; d5 mengunci substring baris `REGRESI BARU` |
| `skills/profile/SKILL.md` | Fase 4 sinkron `repo-profile.md` ke workspace (Q11); baris `NATAFLOW:` | `test_skill_text` Fase 2 profil (tidak disentuh) |
| `README.md`, `flow/quickdev.md` | Seksi sinkron, tabel subperintah, siklus status | Tidak ada test yang membaca `flow/`. `test_13_text::test_rilis_readme_dan_versi` mengunci versi `0.5.0` (diubah di commit rilis) |
| `tests/test_smoke.py` | `CASES` + `.claude/nataflow.json` di `CORRUPT` | Keadaan `rusak` ikut menguji jalur `FAIL` config pada skrip lain yang membaca config |
| `tests/quickdev/test_15_sync.py` (baru) | Kontrak `sync-payload` (Q13) | — |

Keputusan tambahan: Q8 memakai rute di `plan` ("sinkron ulang `<plan_path>`"), karena `execute` Fase 0 selalu menjalankan
`start` yang bisa menulis blok. "Pernah dikunci" dinilai dari `Approved-At`, bukan `Status:`, sehingga rencana hasil
`unlock` tetap tercermin dengan status `DRAFT` (baris P2 `unlock`).

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
