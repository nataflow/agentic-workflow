# Langkah 28 — Status task nataflow mengikuti workdir (backend, frontend, quickdev)

Sumber: permintaan user (2026-10-15): "di tiap plugin agentic workflow yang sync ke nataflow, harus otomatis sync task
juga — terbit workdir → ubah status task jadi in progress; sudah terbit `REPORT.md` dan sudah sync ke nataflow, ubah
task jadi done". User memilih opsi B untuk task tiket analyst (ditutup dari seluruh workdir di bawahnya) dan
memastikan server nataflow sudah menyediakan `list_workdir` (15 T5).

Basis kode: commit `cfea5e6` (analyst 0.17.0, backend 0.17.0, frontend 0.16.0, quickdev 0.9.0).

**Status (2026-10-15):** SELESAI. T1–T4 terpasang; test `tests/test_28_status_task.py` (24, semuanya gagal tanpa
perubahan ini) dan empat asersi lama Langkah 15 yang menyatakan perilaku sebelumnya diperbarui. Rilis: analyst 0.18.0
(salinan `nataflow_sync.py` dan README), backend 0.18.0, frontend 0.17.0, quickdev 0.10.0. product, fullstack, dan
nataflow tidak menyinkron task dan tidak berubah.

## Keadaan sebelum

Status task sudah diturunkan skrip dan dikirim di langkah 7 prosedur sinkron (`update_task_status`), dengan aturan
tidak pernah turun (15 E8): `in_progress` hanya dari `todo`, `done`/`cancelled` dari `todo`/`in_progress`.

| Plugin | Workdir pertama kali terbit | Eksekusi mulai | Taskdir tuntas |
|---|---|---|---|
| backend | task tetap `todo` | `in_progress` (brief `DONE`/`BLOCKED`/`SUPERSEDED`, `report-NN.md`, `HALT.md`, `REVIEW.md`) | task taskdir `done`; task tiket tetap `in_progress` |
| frontend | task tetap `todo` | `in_progress` (brief `DONE`/`BLOCKED`, `report-NN.md`, `REVIEW.md`) | task taskdir `done` (`DITUTUP` → `cancelled`); task tiket tetap `in_progress` |
| quickdev | task tetap `todo` (sesudah `lock`) | `in_progress` (blok `## Execution Status` ada) | `done` saat `COMPLETED*` |

Urutan "sudah tersinkron, baru `done`" sudah dijamin prosedur: langkah 7 berjalan sesudah langkah 6 (dokumen,
termasuk `REPORT.md`, di-upsert), dan tool galat di langkah mana pun menghentikan langkah sesudahnya.

## Perubahan

| ID | Plugin | Bagian | Perubahan |
|---|---|---|---|
| T1 | backend, frontend, quickdev | `sync_payload.py` (be, fe), `plan_lock.py sync-payload` | Status task fase pertama selalu `in_progress` begitu payload `PASS` — payload taskdir menolak akar tanpa `base_commit` dan rencana quickdev yang belum pernah `lock`, jadi `PASS` berarti workdir terbit. Penanda `started` (jejak eksekusi) dihapus |
| T2 | backend, frontend, pustaka bersama | `sync_payload.py --workdirs`, `nataflow_sync.py` (`parse_workdirs`, `read_workdirs`, `sibling_task_status`, `WORKDIR_FINAL`) | Task tiket dengan workdir ini tuntas (backend `done`; frontend `done`/`abandoned`) → payload membawa `task.siblings: true`. Fase `--workdirs -` membaca balikan `list_workdir task_id` dan menerbitkan `task_status`: `done` bila seluruh workdir task itu `done`/`abandoned` dan sedikitnya satu `done`, selain itu status fase pertama |
| T3 | backend, frontend | `tech-lead/references/nataflow-sync.md`, `lead/references/nataflow-sync.md` | Langkah 2 memuat tujuh tool (ditambah `list_workdir`); langkah 7 memanggil `list_workdir` (`task_id` + `workspace_id` task langkah 3) hanya bila `task.siblings`, lalu menyerahkan balikannya ke `--workdirs -`; Larangan melarang model memutuskan status task tiket sendiri |
| T4 | semua di atas, analyst | README backend/frontend/quickdev/analyst, `flow/{backend,frontend,quickdev,analyst}.md`, `tests/test_smoke.py` | Aturan status baru; butir "status task selesai saat seluruh engineer tuntas" dihapus dari `## Sengaja Belum Ada` analyst; kasus smoke `--workdirs -` |

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | `in_progress` sejak workdir terbit, termasuk selama fase perancangan (BRD/PRD/FLOW/UI/CONTRACT) | Permintaan user. Status diturunkan ulang dari disk di tiap sinkron, jadi sinkron akar yang `GAGAL` tetap menaikkan task di sinkron berikutnya atau lewat rute "sinkron ulang" |
| K2 | Task tiket ditutup dari seluruh workdir di bawahnya (opsi B), menggantikan bagian 15 E8 "plugin engineer hanya menaikkan task tiket ke `in_progress`" | Satu tiket bisa menaungi taskdir backend dan frontend; menutup tiket dari satu `REPORT.md` (opsi A) membuatnya `done` terlalu dini, dan sinkron frontend berikutnya tidak bisa membukanya lagi karena status tidak pernah turun. Aturan tidak pernah turun dipertahankan |
| K3 | `abandoned` dihitung tuntas, tetapi penutupan butuh sedikitnya satu workdir `done`; semua `abandoned` → task tidak diubah | Workdir yang ditutup tidak menyisakan kerja, tetapi tiket tanpa satu pun hasil bukan tiket selesai. Pembatalan tiket tetap milik analyst (`ticket.py cancel` → `cancelled`) |
| K4 | Status workdir ini dibaca dari disk, bukan dari balikan; workdir ini wajib ada di balikan | `upsert_workdir` baru saja menulis status disk. Kehadirannya membuktikan balikan milik task induk yang benar, sehingga `task_id` yang salah gagal (`FAIL`) alih-alih menutup task lain |
| K5 | `list_workdir` hanya dipanggil bila payload membawa `task.siblings`; keputusan di skrip | Task milik taskdir hanya punya satu workdir, dan task tiket yang workdir-nya belum tuntas tidak mungkin ditutup — panggilan ekstra hanya di titik penutupan. Model menyerahkan teks balikan apa adanya, seperti `--remote` (15 D4) |
| K6 | `list_workdir` memakai `workspace_id` task induk | Workdir selalu ditaruh di workspace task induknya (`upsert_workdir` langkah 4), jadi seluruh saudara ada di workspace itu, baik untuk key terkunci workspace maupun ber-scope project |
| K7 | Status workdir kosong atau tak dikenal dibaca `active`; workdir tanpa `key` (dibuat di luar sinkron) ikut dihitung lewat `id` | Konservatif: keadaan yang tidak jelas tidak pernah ikut menutup task |

## Celah yang diterima

- **Taskdir saudara yang belum terbit.** Tiket untuk backend dan frontend yang baru punya workdir backend menjadi
  `done` begitu backend tuntas. Taskdir frontend yang dibuka sesudahnya bernaung di task `done` dan tidak membukanya
  lagi (status tidak pernah turun). Tiket tidak mencatat plugin mana yang diharapkan mengerjakannya.
- **Taskdir backend tanpa `REPORT.md`.** Jalur `debug`/`RCA` yang berhenti di `RCA.md` kini membuat task
  `in_progress` (sebelumnya `todo`) tanpa titik penutupan dari plugin.
- **Paginasi `list_workdir`.** Balikan dibaca sebagai satu daftar utuh. Bila server memotongnya per halaman dan
  workdir yang belum tuntas jatuh di halaman lain, task bisa tertutup terlalu dini. Task tiket lazimnya hanya punya
  satu atau dua workdir.

## Titik gagal

`--workdirs` `FAIL` (balikan bukan JSON, bukan larik, entri tanpa `key`/`id`, atau workdir ini tidak ada) → segmen
`GAGAL: <sebab>`; dokumen sudah terkirim di langkah 6, status task tidak ditulis, dan rute "sinkron ulang taskdir"
mengulang seluruh prosedur. Server tanpa `list_workdir` → `GAGAL: server MCP <mcp_server> tidak tersedia` di langkah 2.
