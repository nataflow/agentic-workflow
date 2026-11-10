# Prosedur Sinkron nataflow

Dimuat `quickdev:plan` (Fase 4 sesudah `LOCK PASS`, sesudah `unlock`, dan rute sinkron ulang), `quickdev:execute` (sesudah tiap `close`/`confirm` PASS), dan `quickdev:profile` (Fase 4, varian profil). Hasilnya tepat satu segmen untuk baris `NATAFLOW:` ringkasan skill pemanggil: `workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama)`, `repo · <n> dokumen (…)`, `dilewati`, atau `GAGAL: <sebab>`.

Rencana dan profil di disk tetap satu-satunya sumber kebenaran; nataflow hanya cermin. Prosedur ini tidak menulis berkas apa pun, sehingga `Plan-Hash`, `Verified-Hash`, dan `Tree-Hash` tidak basi dan `quickdev:review` tidak menolak rencana yang sudah disinkronkan. Kegagalannya tidak mengubah status terminal skill pemanggil.

`<plan_lock.py>` di bawah adalah perintah `python3 …/skills/_common/plan_lock.py` yang sama dengan yang dipakai skill pemanggil.


## Langkah

Jalankan `<plan_lock.py> sync-payload --plan <plan_path> --push` untuk rencana, atau `<plan_lock.py> sync-payload --repo-profile <target_path> --push` untuk varian profil (`quickdev:profile`).

Skrip membaca config dan MCP key, lalu memanggil sendiri tool server nataflow. Rencana: cari task lewat `workdir_key` (buat bila belum ada), `upsert_workdir` di workspace task induknya, manifest, `upsert_document` hanya bila rencana berbeda, lalu status task (`in_progress` sejak workdir terbit, `done` saat eksekusi `COMPLETED`). Profil: dokumen `profile` di bawah workspace. Isi rencana dan profil tidak pernah lewat konteks model.

Keluarannya tepat satu baris, yang disalin apa adanya sebagai segmen:

- `workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama)` atau `repo · <n> dokumen (…)` → selesai.
- `dilewati` (`.claude/nataflow.json` tidak ada) → selesai.
- `GAGAL: <sebab>` → selesai. Sebab setup (`.claude/nataflow.local.json` tidak ada, tidak diabaikan git, `url` belum diisi, atau `mcp_server` lama) disampaikan ke user apa adanya bersama bagian Prasyarat di bawah. Task kembar (`<n> task ber-workdir_key sama`) dan rencana DRAFT berhenti sebelum tulisan apa pun.
- `PILIH_WORKSPACE: <alias> (<uuid>), …` → muncul hanya saat `workspaces` berisi lebih dari satu entri dan task harus dibuat baru (atau induk dokumen repo ditentukan), sebelum tulisan apa pun. Tanyakan workspace tujuan lewat `AskUserQuestion` (satu opsi per alias: label alias, deskripsi UUID), lalu jalankan ulang perintah yang sama dengan `--workspace <alias terpilih>` dan pakai segmen keluarannya.

## Larangan

- Dilarang memanggil tool MCP nataflow (`mcp__…`) sendiri untuk sinkron ini, menyusun argumen tool, atau menyalin isi dokumen ke chat: `--push` satu-satunya jalur.
- Dilarang mengulang `--push` di giliran yang sama sesudah `GAGAL`; sinkron diulang lewat rute sinkron ulang. Pengulangan aman: skrip selalu mencari lebih dulu, dan tulisan yang gagal tidak pernah diulang otomatis.
- Dilarang membaca, mencetak, atau menyunting `.claude/nataflow.local.json`.
- Dilarang memilih workspace sendiri: `--workspace` hanya menerima alias yang dipilih user.
- Dilarang menulis rencana, profil, atau berkas lain, dan dilarang meng-commit sebagai bagian prosedur ini.
- `GAGAL` tidak mengubah status terminal skill pemanggil. Sinkron diulang lewat `/quickdev:plan` ("sinkron ulang `<plan_path>`"), bukan lewat `unlock` atau eksekusi ulang.

## Prasyarat di luar plugin

- `.claude/nataflow.json` di root repo (ter-commit, tanpa rahasia) mengaktifkan sinkron. Berkas absen → `dilewati`; ada tetapi rusak → `GAGAL`, bukan dilewati. Berkas yang sama dibaca plugin `analyst`, `backend`, `frontend`, dan `nataflow`.
- `.claude/nataflow.local.json` di root repo menyimpan MCP key: `{"mcp_key": "<MCP key nataflow>"}`. Berkas ini tidak pernah di-commit: di repo git ia wajib tercantum di `.gitignore` (baris `.claude/nataflow.local.json`). Berkas absen, tidak diabaikan git, atau sudah ter-track → `GAGAL` sebelum satu panggilan server pun; root non-git tidak dicek ignore. Skill tidak pernah membaca, mencetak, atau menyalin isinya.
- Server nataflow di `url` terjangkau dari mesin ini (`python3` membuka koneksi HTTPS sendiri). Plugin tidak memakai server MCP yang terdaftar di Claude Code untuk sinkron ini.
- Migrasi dari config lama ber-`mcp_server`: lihat `MIGRATION_v0.10.0_to_v0.11.0.md` di root plugin quickdev.

| Field | Wajib | Aturan |
|---|---|---|
| `url` | **ya** | endpoint MCP server nataflow, mis. `https://api.flow.natakode.id/mcp`: `https://` (http hanya untuk `localhost`/`127.0.0.1`), path berakhir di `/mcp`, tanpa kredensial |
| `workspaces` | tidak | objek alias → UUID workspace, urutan entri dipertahankan. Kosong → workspace milik key. Satu entri → dipakai otomatis. Lebih dari satu → user memilih saat task baru dibuat atau dokumen repo disinkron; task yang sudah ada ditemukan di workspace mana pun dalam jangkauan key dan tidak bisa dipindah. Lebih dari satu workspace butuh MCP key ber-scope project |
| `pic_id` | tidak | UUID; kosong → server memakai pemilik key |
| `repo` | tidak | identitas repo di kunci workdir, metadata task, dan dokumen repo; kosong → remote `origin` ternormalisasi, lalu nama direktori root |

Kunci lain → `GAGAL`: `mcp_server` lama (nama server MCP di Claude Code, tidak dipakai lagi — ganti dengan `url`) dan `workspace_id` tunggal lama (ganti dengan `workspaces`) disebut beserta penggantinya. Nilai bukan string, `url` tidak sah, alias tidak sah, UUID tidak sah atau kembar, atau `repo` berspasi juga `GAGAL`.
