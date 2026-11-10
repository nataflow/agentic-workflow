# Prosedur Sinkron nataflow

Dimuat `analyst:spec` Phase 5 butir 4 sesudah `ticket.py approve` menulis `READY`, `analyst:spec` sesudah `ticket.py cancel` atas tiket yang pernah `READY`, dan `analyst:intake` pada rute sinkron ulang. Hasilnya tepat satu segmen baris penutup: `nataflow <dibuat #<code> | diperbarui #<code> | dibatalkan #<code> | dilewati | GAGAL: <sebab>>`, ditambah ` · review.md <baru | diperbarui | sama>` bila dokumen review ikut terkirim.

`TICKET.md` di disk tetap satu-satunya sumber kebenaran; task nataflow hanya cermin kartunya. Di repo bersinkron, ticketdir diabaikan git (`analyst/tickets/.gitignore` tulisan `ticket.py new`), sehingga cermin inilah satu-satunya salinan kartu di luar disk lokal. Karena itu prosedur ini tidak pernah menulis `TICKET.md`, tidak pernah menurunkan `READY`, dan kegagalannya tidak menahan serah terima ke engineer. Task yang sama menjadi induk workdir taskdir backend/frontend yang berangkat dari tiket ini (`ticket_source`): plugin engineer menurunkan `ticket_key` yang sama persis, menemukan task itu di workspace mana pun, dan menaruh workdir-nya di workspace yang sama. Workspace pilihan user tidak ditulis ke `TICKET.md`; nataflow sendiri yang mencatatnya.


## Langkah

Jalankan `python3 <ticket.py> sync-payload --ticketdir <ticketdir> --push` — `<ticket.py>` adalah path skrip dari Precondition skill pemanggil.

Skrip membaca config dan MCP key, lalu memanggil sendiri tool server nataflow: cari task lewat `ticket_key`, lalu `create_task` (belum ada), `update_task` (sudah ada, termasuk task yang lebih dulu dibuat plugin engineer), atau `update_task_status cancelled` (tiket pernah `READY` lalu dibatalkan; status `done`/`cancelled` tidak ditimpa), beserta `review.md` sebagai dokumen task. Status task tidak pernah dikirim selain pembatalan. Isi kartu tidak pernah lewat konteks model.

Keluarannya tepat satu baris, yang disalin apa adanya sebagai segmen:

- `nataflow dibuat #<code>`, `nataflow diperbarui #<code>`, atau `nataflow dibatalkan #<code>`, ditambah ` · review.md <baru | diperbarui | sama>` bila dokumen review ikut terkirim → selesai.
- `nataflow dilewati` (`.claude/nataflow.json` maupun `analyst/nataflow.json` tidak ada), `nataflow dilewati (task belum ada)` (pembatalan tiket yang belum pernah tercermin), atau `nataflow dilewati (task <status> #<code>)` → selesai.
- `nataflow GAGAL: <sebab>` → selesai. Sebab setup (`.claude/nataflow.local.json` tidak ada, tidak diabaikan git, `url` belum diisi, atau `mcp_server` lama) disampaikan ke user apa adanya bersama bagian Prasyarat di bawah. Task kembar (`<n> task ber-ticket_key sama`) berhenti sebelum tulisan apa pun.
- `nataflow `PILIH_WORKSPACE: <alias> (<uuid>), …` → muncul hanya saat `workspaces` berisi lebih dari satu entri dan task harus dibuat baru (atau induk dokumen repo ditentukan), sebelum tulisan apa pun. Tanyakan workspace tujuan lewat `AskUserQuestion` (satu opsi per alias: label alias, deskripsi UUID), lalu jalankan ulang perintah yang sama dengan `--workspace <alias terpilih>` dan pakai segmen keluarannya.` Task yang sudah dibuat tidak bisa dipindah workspace, sehingga pilihan ini ditanyakan sekali per tiket.

## Larangan

- Dilarang memanggil tool MCP nataflow (`mcp__…`) sendiri untuk sinkron ini, menyusun argumen tool, atau menyalin isi dokumen ke chat: `--push` satu-satunya jalur.
- Dilarang mengulang `--push` di giliran yang sama sesudah `GAGAL`; sinkron diulang lewat rute sinkron ulang. Pengulangan aman: skrip selalu mencari lebih dulu, dan tulisan yang gagal tidak pernah diulang otomatis.
- Dilarang membaca, mencetak, atau menyunting `.claude/nataflow.local.json`.
- Dilarang memilih workspace sendiri: `--workspace` hanya menerima alias yang dipilih user.
- Dilarang menulis ke `TICKET.md` (termasuk `external_ref`) atau menjalankan subperintah `ticket.py` lain sebagai bagian prosedur ini.
- `GAGAL` tidak menurunkan `READY` dan tidak menahan serah terima. Sinkron diulang lewat `analyst:intake` ("sinkron ulang tiket `<ticketdir>`"), bukan lewat `reopen`.

## Prasyarat di luar plugin

- `.claude/nataflow.json` di root repo (ter-commit, tanpa rahasia) mengaktifkan sinkron; berkas yang sama dibaca plugin `backend`, `frontend`, `quickdev`, dan `nataflow`. `analyst/nataflow.json` lama tetap diterima; bila keduanya ada dengan isi berbeda → `GAGAL`. Berkas ada tetapi rusak → `GAGAL`, bukan dilewati. Kehadiran salah satunya (sah maupun rusak) juga membuat `ticket.py new` menulis `analyst/tickets/.gitignore` bila belum ada.
- `.claude/nataflow.local.json` di root repo menyimpan MCP key: `{"mcp_key": "<MCP key nataflow>"}`. Berkas ini tidak pernah di-commit: di repo git ia wajib tercantum di `.gitignore` (baris `.claude/nataflow.local.json`). Berkas absen, tidak diabaikan git, atau sudah ter-track → `GAGAL` sebelum satu panggilan server pun; root non-git tidak dicek ignore. Skill tidak pernah membaca, mencetak, atau menyalin isinya.
- Server nataflow di `url` terjangkau dari mesin ini (`python3` membuka koneksi HTTPS sendiri). Plugin tidak memakai server MCP yang terdaftar di Claude Code untuk sinkron ini.
- Migrasi dari config lama ber-`mcp_server`: lihat `MIGRATION_v0.18.0_to_v0.19.0.md` di root plugin analyst.

| Field | Wajib | Aturan |
|---|---|---|
| `url` | **ya** | endpoint MCP server nataflow, mis. `https://api.flow.natakode.id/mcp`: `https://` (http hanya untuk `localhost`/`127.0.0.1`), path berakhir di `/mcp`, tanpa kredensial |
| `workspaces` | tidak | objek alias → UUID workspace, urutan entri dipertahankan. Kosong → workspace milik key. Satu entri → dipakai otomatis. Lebih dari satu → user memilih saat task baru dibuat atau dokumen repo disinkron; task yang sudah ada ditemukan di workspace mana pun dalam jangkauan key dan tidak bisa dipindah. Lebih dari satu workspace butuh MCP key ber-scope project |
| `pic_id` | tidak | UUID; kosong → server memakai pemilik key |
| `repo` | tidak | identitas repo di kunci workdir, metadata task, dan dokumen repo; kosong → remote `origin` ternormalisasi, lalu nama direktori root |

Kunci lain → `GAGAL`: `mcp_server` lama (nama server MCP di Claude Code, tidak dipakai lagi — ganti dengan `url`) dan `workspace_id` tunggal lama (ganti dengan `workspaces`) disebut beserta penggantinya. Nilai bukan string, `url` tidak sah, alias tidak sah, UUID tidak sah atau kembar, atau `repo` berspasi juga `GAGAL`.
