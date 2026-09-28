# Prosedur Sinkron nataflow

Dimuat `analyst:spec` Phase 5 butir 4 sesudah `ticket.py approve` menulis `READY`, dan `analyst:intake` pada rute sinkron ulang. Hasilnya tepat satu segmen baris penutup: `nataflow <dibuat #<code> | diperbarui #<code> | dilewati | GAGAL: <sebab>>`.

`TICKET.md` di disk dan git tetap satu-satunya sumber kebenaran; task nataflow hanya cermin kartunya. Karena itu prosedur ini tidak pernah menulis `TICKET.md`, tidak pernah menurunkan `READY`, dan kegagalannya tidak menahan serah terima ke engineer.

## Langkah

1. **Payload.** `python3 <ticket.py> sync-payload --ticketdir <ticketdir> --json` — `<ticket.py>` adalah path skrip dari Precondition skill pemanggil. Baca field `status` keluarannya:
   - `SKIP` (`analyst/nataflow.json` tidak ada di repo) → segmen `nataflow dilewati`; selesai.
   - `FAIL` → segmen `nataflow GAGAL: <isi problems apa adanya>`; selesai.
   - `PASS` → pegang `mcp_server`, `lookup`, `create`, dan `update` apa adanya untuk langkah berikut.
2. **Tool.** Ketiga tool bernama `mcp__<mcp_server>__list_task`, `mcp__<mcp_server>__create_task`, dan `mcp__<mcp_server>__update_task`. Yang masih tertunda dimuat lebih dulu lewat ToolSearch (`select:` ketiganya). Salah satu tidak tersedia → segmen `nataflow GAGAL: server MCP <mcp_server> tidak tersedia`; selesai.
3. **Cari task.** Panggil `list_task` dengan argumen `lookup` apa adanya, lalu hitung task di hasilnya:
   - 0 → `create_task` dengan argumen `create` apa adanya.
   - 1 → `update_task` dengan `task_id` = `id` task itu, ditambah argumen `update` apa adanya.
   - Lebih dari 1 → jangan memanggil tool tulis apa pun; segmen `nataflow GAGAL: <n> task ber-ticket_key sama (<code tiap task>)`; selesai.
4. **Hasil.** Tool mengembalikan task → segmen `nataflow dibuat #<code>` atau `nataflow diperbarui #<code>`, dari field `code` task balikan (tanpa `code` → `id`). Tool mengembalikan galat → segmen `nataflow GAGAL: <pesan tool apa adanya>`.

## Larangan

- Dilarang menyusun, menyunting, meringkas, atau menerjemahkan nilai argumen di luar keluaran `sync-payload`. `metadata` dikirim sebagai teks JSON persis seperti tercetak, bukan objek yang dirangkai ulang.
- Dilarang mengirim argumen `status` maupun argumen lain yang tidak ada di `lookup`/`create`/`update`: status task bukan milik analyst.
- Dilarang mengulang `create_task` sesudah tool galat tanpa `list_task` ulang. Tulisan yang ternyata sampai di server membuat task kembar.
- Dilarang menulis ke `TICKET.md` (termasuk `external_ref`) atau menjalankan subperintah `ticket.py` lain sebagai bagian prosedur ini.
- `GAGAL` tidak menurunkan `READY` dan tidak menahan serah terima. Sinkron diulang lewat `analyst:intake` ("sinkron ulang tiket `<ticketdir>`"), bukan lewat `reopen`.

## Prasyarat di luar plugin

- Server MCP nataflow terdaftar di Claude Code user beserta MCP key-nya. Plugin tidak mendeklarasikan server dan tidak menyimpan key.
- `analyst/nataflow.json` di root repo (ter-commit) mengaktifkan sinkron. Berkas ada tetapi rusak → `sync-payload` `FAIL`, bukan dilewati.

| Field | Wajib | Aturan |
|---|---|---|
| `mcp_server` | tidak | nama server MCP di konfigurasi Claude Code user; default `nataflow-api` |
| `workspace_id` | tidak | UUID; wajib bila MCP key ber-scope project (server menolak `create_task` tanpa workspace) |
| `pic_id` | tidak | UUID; kosong → server memakai pemilik key |

Kunci lain, nilai bukan string, atau UUID tidak sah → `FAIL`.
