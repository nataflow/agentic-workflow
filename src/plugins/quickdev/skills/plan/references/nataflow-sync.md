# Prosedur Sinkron nataflow

Dimuat `quickdev:plan` (Fase 4 sesudah `LOCK PASS`, sesudah `unlock`, dan rute sinkron ulang), `quickdev:execute` (sesudah tiap `close`/`confirm` PASS), dan `quickdev:profile` (Fase 4, varian profil). Hasilnya tepat satu segmen untuk baris `NATAFLOW:` ringkasan skill pemanggil: `workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama)`, `repo · <n> dokumen (…)`, `dilewati`, atau `GAGAL: <sebab>`.

Rencana dan profil di disk tetap satu-satunya sumber kebenaran; nataflow hanya cermin. Prosedur ini tidak menulis berkas apa pun, sehingga `Plan-Hash`, `Verified-Hash`, dan `Tree-Hash` tidak basi dan `quickdev:review` tidak menolak rencana yang sudah disinkronkan. Kegagalannya tidak mengubah status terminal skill pemanggil.

`<plan_lock.py>` di bawah adalah perintah `python3 …/skills/_common/plan_lock.py` yang sama dengan yang dipakai skill pemanggil.

## Langkah — rencana

1. **Payload.** `<plan_lock.py> sync-payload --plan <plan_path> --json`. Baca field `status` keluarannya:
   - `SKIP` (`.claude/nataflow.json` tidak ada di repo) → segmen `dilewati`; selesai.
   - `FAIL` → segmen `GAGAL: <isi problems apa adanya>`; selesai.
   - `PASS` → pegang `mcp_server`, `task`, `workdir`, `list_document`, dan `documents_total` apa adanya. `workspace_choices` ikut ada bila `.claude/nataflow.json` berisi lebih dari satu workspace; baru dipakai di langkah 3.
2. **Tool.** Keenam tool bernama `mcp__<mcp_server>__list_task`, `…__create_task`, `…__update_task_status`, `…__upsert_workdir`, `…__list_document`, dan `…__upsert_document`. Yang masih tertunda dimuat lebih dulu lewat ToolSearch (`select:` keenamnya). Salah satu tidak tersedia → segmen `GAGAL: server MCP <mcp_server> tidak tersedia`; selesai.
3. **Task.** Panggil `list_task` dengan argumen `task.lookup` apa adanya, lalu hitung task di hasilnya:
   - 0 → bila payload membawa `workspace_choices`, tanyakan dulu workspace tujuan lewat `AskUserQuestion` (satu opsi per entri: label `alias`, deskripsi `workspace_id`), lalu jalankan ulang langkah 1 dengan `--workspace <alias terpilih>` dan pakai `task` keluarannya. Lalu `create_task` dengan argumen `task.create` apa adanya; task balikannya dipakai di langkah berikut.
   - 1 → pakai task itu.
   - Lebih dari 1 → jangan memanggil tool tulis apa pun; segmen `GAGAL: <n> task ber-workdir_key sama`; selesai.
4. **Workdir.** `upsert_workdir` dengan argumen `workdir` apa adanya ditambah `task_id` = `id` dan `workspace_id` = `workspace_id` task langkah 3, sehingga workdir selalu berada di workspace task induknya.
5. **Manifest.** `list_document` dengan argumen `list_document` apa adanya ditambah `reference_id` = `id` workdir langkah 4. Serahkan teks balikannya apa adanya lewat stdin:

   ```
   <plan_lock.py> sync-payload --plan <plan_path> --remote - --json <<'QD_EOF'
   <teks balikan list_document apa adanya>
   QD_EOF
   ```

   `FAIL` → segmen `GAGAL: <isi problems apa adanya>`; selesai. `PASS` → pegang `documents` dan `same`.
6. **Dokumen.** Untuk tiap entri `documents`: `upsert_document` dengan entri itu apa adanya ditambah `reference_id` = `id` workdir. Catat `action` balikan (`created`, `updated`, `unchanged`).
7. **Status task.** `task.status` terisi dan `status` task langkah 3 termasuk dalam `task.status.from` → `update_task_status` dengan `task_id` dan `status` = `task.status.status`. Selain itu lewati.
8. **Segmen.** `workdir <workdir.name> · <documents_total> dokumen (<created> baru, <updated> diperbarui, <same + unchanged> sama)`. Tool galat di langkah mana pun → segmen `GAGAL: <pesan tool apa adanya>`, dan langkah sesudahnya tidak dijalankan.

## Langkah — profil

Dipakai `quickdev:profile` sesudah profil tertulis. Urutannya sama dengan langkah rencana, dengan perbedaan berikut:

- Langkah 1 memakai `<plan_lock.py> sync-payload --repo-profile <target_path> --json`. `PASS` membawa `workspace_id` (ditambah `workspace_choices` bila workspace lebih dari satu), bukan `task`/`workdir`.
- Langkah 2 cukup memuat `list_workspace`, `list_document`, dan `upsert_document`.
- Langkah 3–4 diganti penentuan induk: `workspace_choices` ada → tanyakan dulu workspace tujuan lewat `AskUserQuestion` (satu opsi per entri: label `alias`, deskripsi `workspace_id`), lalu jalankan ulang langkah 1 dengan `--workspace <alias terpilih>`; `workspace_id` keluarannya induknya. `workspace_id` terisi → itu induknya. Kosong tanpa pilihan (`workspaces` tidak diisi) → `list_workspace`, dan tepat satu workspace → `id`-nya; selain itu segmen `GAGAL: key menjangkau <n> workspace — daftarkan di workspaces .claude/nataflow.json`; selesai.
- Langkah 5–6 memakai `reference_id` = workspace itu, dan perintah `--remote` memakai `--repo-profile <target_path>`. Langkah 7 tidak ada.
- Segmen: `repo · <documents_total> dokumen (<created> baru, <updated> diperbarui, <same + unchanged> sama)`.

## Larangan

- Dilarang menyusun, menyunting, meringkas, atau menerjemahkan nilai argumen di luar keluaran `sync-payload`. Satu-satunya nilai dari balikan tool adalah `task_id`, `workspace_id` task untuk `upsert_workdir`, dan `reference_id`. `metadata` dikirim sebagai teks JSON persis seperti tercetak, bukan objek yang dirangkai ulang.
- Dilarang memanggil `upsert_documents` (batch) atau `delete_document`: satu dokumen yang meleset tidak boleh menggagalkan dokumen lain, dan cermin tidak pernah dihapus dari sini.
- Dilarang memilih workspace sendiri: `workspace_choices` selalu ditanyakan ke user, dan `--workspace` hanya menerima alias yang dipilih user.
- Dilarang mengulang `create_task` sesudah tool galat tanpa `list_task` ulang. Tulisan yang ternyata sampai di server membuat task kembar.
- Dilarang menulis rencana, profil, atau berkas lain, dan dilarang meng-commit sebagai bagian prosedur ini.
- `GAGAL` tidak mengubah status terminal skill pemanggil. Sinkron diulang lewat `/quickdev:plan` ("sinkron ulang `<plan_path>`"), bukan lewat `unlock` atau eksekusi ulang.

## Prasyarat di luar plugin

- Server MCP nataflow terdaftar di Claude Code user beserta MCP key-nya. Plugin tidak mendeklarasikan server dan tidak menyimpan key.
- `.claude/nataflow.json` di root repo (ter-commit) mengaktifkan sinkron. Berkas ada tetapi rusak → `sync-payload` `FAIL`, bukan dilewati. Berkas yang sama dibaca plugin `analyst`, `backend`, dan `frontend`.

| Field | Wajib | Aturan |
|---|---|---|
| `mcp_server` | tidak | nama server MCP di konfigurasi Claude Code user; default `nataflow-api` |
| `workspaces` | tidak | objek alias → UUID workspace, urutan entri dipertahankan. Kosong → workspace milik key. Satu entri → dipakai otomatis. Lebih dari satu → user memilih saat task baru dibuat atau dokumen repo disinkron; task yang sudah ada ditemukan di workspace mana pun dalam jangkauan key dan tidak bisa dipindah. Lebih dari satu workspace butuh MCP key ber-scope project |
| `pic_id` | tidak | UUID; kosong → server memakai pemilik key |
| `repo` | tidak | identitas repo di kunci workdir dan dokumen repo; kosong → remote `origin` ternormalisasi, lalu nama direktori root |

Kunci lain (termasuk `workspace_id` tunggal lama — ganti dengan `workspaces`), nilai bukan string, alias tidak sah, UUID tidak sah atau kembar, atau `repo` berspasi → `FAIL`.
