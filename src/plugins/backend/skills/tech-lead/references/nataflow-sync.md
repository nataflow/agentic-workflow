# Prosedur Sinkron nataflow

Dimuat di main loop oleh skill pemilik titik status backend, tepat saat dokumen taskdir disetujui atau tuntas (tabel di bawah), dan oleh `backend:tech-lead` Fase 5 sebagai sapuan serta rute "sinkron ulang". Subagent tidak pernah menjalankannya. Hasilnya tepat satu segmen untuk slot **Nataflow**: `workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama)`, `repo · <n> dokumen (…)`, `dilewati`, atau `GAGAL: <sebab>`.

Dokumen taskdir hanya ada di disk dan tidak pernah di-commit (Langkah 24); nataflow satu-satunya salinannya di luar mesin ini. Dokumen tingkat repo (audit, API, profil) tetap ter-commit. Prosedur ini tidak menulis berkas dan tidak meng-commit, sehingga check `Git Clean Working Tree`, kesegaran `REVIEW.md`, dan materai approve tidak tersentuh. `GAGAL` tidak menahan rantai: langkah lanjut ditentukan seperti biasa, dan sinkron diulang lewat rute "sinkron ulang".

`<sync_payload.py>` di bawah adalah `python3 <root plugin backend>/skills/_common/sync_payload.py`, root yang sama dengan skrip prasyarat skill pemanggil.

## Target per titik panggil

| Titik | Dokumen yang baru disetujui / tuntas | Target |
|---|---|---|
| `task` Fase 5 butir 5, sesudah `doc_seal.py root` (semua lane) | `TASK.md` | `--taskdir <taskdir>` |
| `analyst` Fase 4 butir 4, sesudah `doc_seal.py approve` | `BRD.md` / `PRD.md` `APPROVED` | `--taskdir <taskdir>` |
| `analyst` Fase 6 butir 0, sesudah `doc_seal.py tick --hop BRIEF` | batch brief terkunci `READY` | `--taskdir <taskdir>` |
| `architect` Fase 4 butir 2, sesudah `REVIEW.md` terbit | `REVIEW.md`, status brief | `--taskdir <taskdir>` |
| `report` Fase 4 butir 4, sesudah `REPORT.md` tertulis | `REPORT.md` | `--taskdir <taskdir>` |
| `architect`, sebelum laporan penutup putaran yang tidak melewati review maupun `report` | status brief, `report-NN.md`, `HALT.md` | `--taskdir <taskdir>` |
| `tech-lead` Fase 5, pengirim `plan` jalur `RCA`, `debug`, atau `analyst` selain `READY_FOR_IMPLEMENTATION` | brief jalur `RCA`, `RCA.md`, ledger | `--taskdir <taskdir pengirim>` |
| `tech-lead` Fase 5, pengirim `audit` / `document-api` / `profile` | laporan audit, `docs/api/`, profil | `--repo-docs audit` / `api` / `profile` |
| Rute "sinkron ulang taskdir `<td>`" | seluruh taskdir | `--taskdir <td>`; tambahkan `--repo-docs` yang diminta user bila ada |

`tech-lead` Fase 5 tidak menyinkron ulang pengirim yang sudah menyinkron sesudah mutasi disk terakhirnya — `architect`, dan `analyst` bervonis `READY_FOR_IMPLEMENTATION`: segmen laporannya disalin ke slot **Nataflow** (`gate-lifecycle.md` bagian 6 butir 2a).


## Langkah

Jalankan `<sync_payload.py> --taskdir <taskdir> --push`, atau `<sync_payload.py> --repo-docs <audit | api | profile> --push` untuk dokumen repo (target per titik panggil di tabel atas).

Skrip membaca config dan MCP key, memilih dokumen yang stabil, lalu memanggil sendiri tool server nataflow: cari task lewat identitasnya (buat bila belum ada), `upsert_workdir` di workspace task induknya, manifest `list_document`, `upsert_document` hanya untuk dokumen yang berbeda, lalu status task. Task tiket analyst baru ditutup `done` bila seluruh workdir di bawahnya tuntas. Isi dokumen tidak pernah lewat konteks model.

Keluarannya tepat satu baris, yang disalin apa adanya sebagai segmen:

- `workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama)` atau `repo · <n> dokumen (…)` → selesai.
- `dilewati` (`.claude/nataflow.json` tidak ada) → selesai.
- `GAGAL: <sebab>` → selesai. Sebab setup (`.claude/nataflow.local.json` tidak ada, tidak diabaikan git, `url` belum diisi, atau `mcp_server` lama) disampaikan ke user apa adanya bersama bagian Prasyarat di bawah. Task kembar (`<n> task ber-… sama`) berhenti sebelum tulisan apa pun.
- `PILIH_WORKSPACE: <alias> (<uuid>), …` → muncul hanya untuk task baru atau dokumen repo saat `workspaces` berisi lebih dari satu entri, sebelum tulisan apa pun. Tanyakan workspace tujuan lewat `AskUserQuestion` (satu opsi per alias: label alias, deskripsi UUID), lalu jalankan ulang perintah yang sama dengan `--workspace <alias terpilih>` dan pakai segmen keluarannya.

## Larangan

- Dilarang memanggil tool MCP nataflow (`mcp__…`) sendiri untuk sinkron ini, menyusun argumen tool, atau menyalin isi dokumen ke chat: `--push` satu-satunya jalur.
- Dilarang memilih workspace sendiri: `--workspace` hanya menerima alias yang dipilih user.
- Dilarang mengulang `--push` di giliran yang sama sesudah `GAGAL`; sinkron diulang lewat rute sinkron ulang. Pengulangan aman: skrip selalu mencari task lebih dulu, dan tulisan yang gagal tidak pernah diulang otomatis.
- Dilarang membaca, mencetak, atau menyunting `.claude/nataflow.local.json`.
- Dilarang menjalankan prosedur ini dari subagent, menulis berkas, atau meng-commit sebagai bagiannya.

## Prasyarat di luar plugin

- `.claude/nataflow.json` di root repo (ter-commit, tanpa rahasia) mengaktifkan sinkron. Berkas absen → `dilewati`; ada tetapi rusak → `GAGAL`, bukan dilewati. Berkas yang sama dibaca plugin `analyst`, `frontend`, `quickdev`, dan `nataflow`.
- `.claude/nataflow.local.json` di root repo menyimpan MCP key: `{"mcp_key": "<MCP key nataflow>"}`. Berkas ini tidak pernah di-commit: di repo git ia wajib tercantum di `.gitignore` (baris `.claude/nataflow.local.json`). Berkas absen, tidak diabaikan git, atau sudah ter-track → `GAGAL` sebelum satu panggilan server pun; root non-git tidak dicek ignore. Skill tidak pernah membaca, mencetak, atau menyalin isinya.
- Server nataflow di `url` terjangkau dari mesin ini (`python3` membuka koneksi HTTPS sendiri). Plugin tidak memakai server MCP yang terdaftar di Claude Code untuk sinkron ini.
- Migrasi dari config lama ber-`mcp_server`: lihat `MIGRATION_v0.18.0_to_v0.19.0.md` di root plugin backend.

| Field | Wajib | Aturan |
|---|---|---|
| `url` | **ya** | endpoint MCP server nataflow, mis. `https://api.flow.natakode.id/mcp`: `https://` (http hanya untuk `localhost`/`127.0.0.1`), path berakhir di `/mcp`, tanpa kredensial |
| `workspaces` | tidak | objek alias → UUID workspace, urutan entri dipertahankan. Kosong → workspace milik key. Satu entri → dipakai otomatis. Lebih dari satu → user memilih saat task baru dibuat atau dokumen repo disinkron; task yang sudah ada ditemukan di workspace mana pun dalam jangkauan key dan tidak bisa dipindah. Lebih dari satu workspace butuh MCP key ber-scope project |
| `pic_id` | tidak | UUID; kosong → server memakai pemilik key |
| `repo` | tidak | identitas repo di kunci workdir, metadata task, dan dokumen repo; kosong → remote `origin` ternormalisasi, lalu nama direktori root |

Kunci lain → `GAGAL`: `mcp_server` lama (nama server MCP di Claude Code, tidak dipakai lagi — ganti dengan `url`) dan `workspace_id` tunggal lama (ganti dengan `workspaces`) disebut beserta penggantinya. Nilai bukan string, `url` tidak sah, alias tidak sah, UUID tidak sah atau kembar, atau `repo` berspasi juga `GAGAL`.
