# Prosedur Sinkron nataflow

Dimuat `analyst:spec` Phase 5 butir 4 sesudah `ticket.py approve` menulis `READY`, `analyst:spec` sesudah `ticket.py cancel` atas tiket yang pernah `READY`, dan `analyst:intake` pada rute sinkron ulang. Hasilnya tepat satu segmen baris penutup: `nataflow <dibuat #<code> | diperbarui #<code> | dibatalkan #<code> | dilewati | GAGAL: <sebab>>`, ditambah ` · review.md <baru | diperbarui | sama>` bila dokumen review ikut terkirim.

`TICKET.md` di disk tetap satu-satunya sumber kebenaran; task nataflow hanya cermin kartunya. Di repo bersinkron, ticketdir diabaikan git (`analyst/tickets/.gitignore` tulisan `ticket.py new`), sehingga cermin inilah satu-satunya salinan kartu di luar disk lokal. Karena itu prosedur ini tidak pernah menulis `TICKET.md`, tidak pernah menurunkan `READY`, dan kegagalannya tidak menahan serah terima ke engineer. Task yang sama menjadi induk workdir taskdir backend/frontend yang berangkat dari tiket ini (`ticket_source`): plugin engineer menurunkan `ticket_key` yang sama persis, menemukan task itu di workspace mana pun, dan menaruh workdir-nya di workspace yang sama. Workspace pilihan user tidak ditulis ke `TICKET.md`; nataflow sendiri yang mencatatnya.

## Langkah

1. **Payload.** `python3 <ticket.py> sync-payload --ticketdir <ticketdir> --json` — `<ticket.py>` adalah path skrip dari Precondition skill pemanggil. Baca field `status` keluarannya:
   - `SKIP` (`.claude/nataflow.json` maupun `analyst/nataflow.json` tidak ada di repo) → segmen `nataflow dilewati`; selesai.
   - `FAIL` → segmen `nataflow GAGAL: <isi problems apa adanya>`; selesai.
   - `PASS` dengan `task_status` (tiket pernah `READY` lalu dibatalkan) → pegang `mcp_server`, `lookup`, dan `task_status` apa adanya, lalu lompat ke langkah 5.
   - `PASS` lainnya → pegang `mcp_server`, `lookup`, `create`, `update`, dan `documents` apa adanya. `workspace_choices` ikut ada bila `.claude/nataflow.json` berisi lebih dari satu workspace; baru dipakai di langkah 3.
2. **Tool.** Tool yang dipakai bernama `mcp__<mcp_server>__list_task`, `…__create_task`, `…__update_task`, `…__upsert_document`, dan (cabang pembatalan) `…__update_task_status`. Yang masih tertunda dimuat lebih dulu lewat ToolSearch (`select:` semuanya). Salah satu tidak tersedia → segmen `nataflow GAGAL: server MCP <mcp_server> tidak tersedia`; selesai.
3. **Cari task.** Panggil `list_task` dengan argumen `lookup` apa adanya, lalu hitung task di hasilnya:
   - 0 → bila payload membawa `workspace_choices`, tanyakan dulu workspace tujuan lewat `AskUserQuestion` (satu opsi per entri: label `alias`, deskripsi `workspace_id`), lalu jalankan ulang langkah 1 dengan `--workspace <alias terpilih>` dan pakai `create` keluarannya. Lalu `create_task` dengan argumen `create` apa adanya. Task yang sudah dibuat tidak bisa dipindah workspace, sehingga pilihan ini ditanyakan sekali per tiket.
   - 1 → `update_task` dengan `task_id` = `id` task itu, ditambah argumen `update` apa adanya. Task yang lebih dulu dibuat plugin engineer (metadata `ticket_key` sama) ikut diperbarui menjadi kartu tiket.
   - Lebih dari 1 → jangan memanggil tool tulis apa pun; segmen `nataflow GAGAL: <n> task ber-ticket_key sama (<code tiap task>)`; selesai.
4. **Dokumen.** Untuk tiap entri `documents` (`review.md`): `upsert_document` dengan entri itu apa adanya ditambah `reference_id` = `id` task balikan langkah 3. Catat `action` balikannya (`created` → `baru`, `updated` → `diperbarui`, `unchanged` → `sama`). Lanjut ke langkah 6.
5. **Pembatalan.** `list_task` dengan `lookup` apa adanya:
   - 0 → segmen `nataflow dilewati (task belum ada)`; selesai.
   - 1 → status task itu termasuk `task_status.from` → `update_task_status` dengan `task_id` dan `status` = `task_status.status`; selain itu tidak ada yang ditulis.
   - Lebih dari 1 → segmen `nataflow GAGAL: <n> task ber-ticket_key sama`; selesai.
6. **Hasil.** Tool mengembalikan task → segmen `nataflow dibuat #<code>`, `nataflow diperbarui #<code>`, atau `nataflow dibatalkan #<code>` (status task tidak ditimpa → `nataflow dilewati (task <status> #<code>)`), dari field `code` task balikan (tanpa `code` → `id`). Tool mengembalikan galat → segmen `nataflow GAGAL: <pesan tool apa adanya>`.

## Larangan

- Dilarang menyusun, menyunting, meringkas, atau menerjemahkan nilai argumen di luar keluaran `sync-payload`. Satu-satunya nilai dari balikan tool adalah `task_id` dan `reference_id`. `metadata` dikirim sebagai teks JSON persis seperti tercetak, bukan objek yang dirangkai ulang.
- Dilarang mengirim argumen `status` di `create_task`/`update_task`, maupun argumen lain yang tidak ada di keluaran skrip. Satu-satunya perubahan status task dari analyst adalah `task_status` pembatalan.
- Dilarang memilih workspace sendiri: `workspace_choices` selalu ditanyakan ke user, dan `--workspace` hanya menerima alias yang dipilih user.
- Dilarang mengulang `create_task` sesudah tool galat tanpa `list_task` ulang. Tulisan yang ternyata sampai di server membuat task kembar.
- Dilarang mengirim `## Catatan Elisitasi` atau frontmatter tiket sebagai dokumen: yang tercermin hanya kartu dan `review.md`.
- Dilarang menulis ke `TICKET.md` (termasuk `external_ref`) atau menjalankan subperintah `ticket.py` lain sebagai bagian prosedur ini.
- `GAGAL` tidak menurunkan `READY` dan tidak menahan serah terima. Sinkron diulang lewat `analyst:intake` ("sinkron ulang tiket `<ticketdir>`"), bukan lewat `reopen`.

## Prasyarat di luar plugin

- Server MCP nataflow terdaftar di Claude Code user beserta MCP key-nya. Plugin tidak mendeklarasikan server dan tidak menyimpan key.
- `.claude/nataflow.json` di root repo (ter-commit) mengaktifkan sinkron; berkas yang sama dibaca plugin `backend`, `frontend`, dan `quickdev`. `analyst/nataflow.json` lama tetap diterima; bila keduanya ada dengan isi berbeda → `FAIL`. Berkas ada tetapi rusak → `FAIL`, bukan dilewati. Kehadiran salah satunya (sah maupun rusak) juga membuat `ticket.py new` menulis `analyst/tickets/.gitignore` bila belum ada.

| Field | Wajib | Aturan |
|---|---|---|
| `mcp_server` | tidak | nama server MCP di konfigurasi Claude Code user; default `nataflow-api` |
| `workspaces` | tidak | objek alias → UUID workspace, urutan entri dipertahankan. Kosong → workspace milik key. Satu entri → dipakai otomatis. Lebih dari satu → user memilih saat task baru dibuat atau dokumen repo disinkron; task yang sudah ada ditemukan di workspace mana pun dalam jangkauan key dan tidak bisa dipindah. Lebih dari satu workspace butuh MCP key ber-scope project |
| `pic_id` | tidak | UUID; kosong → server memakai pemilik key |
| `repo` | tidak | identitas repo di metadata task (`repo`); kosong → remote `origin` ternormalisasi, lalu nama direktori root |

Kunci lain (termasuk `workspace_id` tunggal lama — ganti dengan `workspaces`), nilai bukan string, alias tidak sah, UUID tidak sah atau kembar, atau `repo` berspasi → `FAIL`.
