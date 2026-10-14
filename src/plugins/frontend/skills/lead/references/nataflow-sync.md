# Prosedur Sinkron nataflow

Dimuat di main loop oleh skill pemilik titik status frontend. Subagent tidak pernah menjalankannya. Hasilnya tepat satu segmen `nataflow <…>` untuk baris penutup skill pemanggil: `nataflow workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama)`, `nataflow repo · <n> dokumen (…)`, `nataflow dilewati`, atau `nataflow GAGAL: <sebab>`.

Disk (dokumen taskdir) dan git (dokumen tingkat repo) tetap sumber kebenaran; nataflow hanya cermin. Prosedur ini tidak menulis berkas dan tidak meng-commit, sehingga ledger `## Chain`, `## Riwayat Rantai` (materai approve), dan tree bersih tidak tersentuh. Dokumen taskdir tidak di-commit (Langkah 24), jadi isinya dibaca dari disk; nataflow satu-satunya salinannya di luar mesin ini. `GAGAL` tidak menahan gate maupun eksekusi, dan sinkron diulang lewat rute "sinkron ulang taskdir" `frontend:lead`.

`<sync_payload.py>` di bawah adalah `python3 <root plugin frontend>/skills/_common/sync_payload.py`, root yang sama dengan `chain.py` skill pemanggil.

## Titik panggil

| Skill | Titik | Target |
|---|---|---|
| `task` | Phase 4 sesudah `chain.py root` | `--taskdir <taskdir>` |
| `lead` | Keadaan `AKAR` sesudah `chain.py root` tertinggal; Phase 8 sesudah `chain.py reopen`/`escalate`/`abandon`/`amend`; rute "sinkron ulang taskdir" | `--taskdir <taskdir>` |
| `ux-design`, `ui-design`, `contract`, `plan` | Butir **Setuju**, sesudah `chain.py approve` PASS | `--taskdir <taskdir>` |
| `architect` | Sekali per putaran, sebelum baris `ARCHITECT — …` atau blok `### ARCHITECT — BLOCKED`/`TERTAHAN` | `--taskdir <taskdir>` |
| `report` | Phase 4 sesudah `REPORT.md` lolos `validate_report.py` | `--taskdir <taskdir>` |
| `review` | Sesudah commit laporan `frontenddev/reviews/` | `--repo-docs review` |
| `profile` | Sesudah commit profil (termasuk PATCH) | `--repo-docs profile` |

## Langkah — taskdir

1. **Payload.** `<sync_payload.py> --taskdir <taskdir> --json`. Baca field `status` keluarannya:
   - `SKIP` (`.claude/nataflow.json` tidak ada di repo) → segmen `nataflow dilewati`; selesai.
   - `FAIL` → segmen `nataflow GAGAL: <isi problems apa adanya>`; selesai.
   - `PASS` → pegang `mcp_server`, `task`, `workdir`, `list_document`, dan `documents_total` apa adanya. `workspace_choices` ikut ada bila `.claude/nataflow.json` berisi lebih dari satu workspace; baru dipakai di langkah 3.
2. **Tool.** Keenam tool bernama `mcp__<mcp_server>__list_task`, `…__create_task`, `…__update_task_status`, `…__upsert_workdir`, `…__list_document`, dan `…__upsert_document`. Yang masih tertunda dimuat lebih dulu lewat ToolSearch (`select:` keenamnya). Salah satu tidak tersedia → segmen `nataflow GAGAL: server MCP <mcp_server> tidak tersedia`; selesai.
3. **Task.** Panggil `list_task` dengan argumen `task.lookup` apa adanya, lalu hitung task di hasilnya:
   - 0 → bila payload membawa `workspace_choices`, tanyakan dulu workspace tujuan lewat `AskUserQuestion` (satu opsi per entri: label `alias`, deskripsi `workspace_id`), lalu jalankan ulang langkah 1 dengan `--workspace <alias terpilih>` dan pakai `task` keluarannya. Lalu `create_task` dengan argumen `task.create` apa adanya; task balikannya dipakai di langkah berikut.
   - 1 → pakai task itu (task tiket analyst, yang bisa juga menaungi taskdir backend, atau task taskdir ini).
   - Lebih dari 1 → jangan memanggil tool tulis apa pun; segmen `nataflow GAGAL: <n> task ber-identitas sama`; selesai.
4. **Workdir.** `upsert_workdir` dengan argumen `workdir` apa adanya ditambah `task_id` = `id` dan `workspace_id` = `workspace_id` task langkah 3, sehingga workdir selalu berada di workspace task induknya.
5. **Manifest.** `list_document` dengan argumen `list_document` apa adanya ditambah `reference_id` = `id` workdir langkah 4. Serahkan teks balikannya apa adanya lewat stdin:

   ```
   <sync_payload.py> --taskdir <taskdir> --remote - --json <<'NATAFLOW_EOF'
   <teks balikan list_document apa adanya>
   NATAFLOW_EOF
   ```

   `FAIL` → segmen `nataflow GAGAL: <isi problems apa adanya>`; selesai. `PASS` → pegang `documents` dan `same`.
6. **Dokumen.** Untuk tiap entri `documents`: `upsert_document` dengan entri itu apa adanya ditambah `reference_id` = `id` workdir. Catat `action` balikan (`created`, `updated`, `unchanged`).
7. **Status task.** `task.status` terisi dan `status` task langkah 3 termasuk dalam `task.status.from` → `update_task_status` dengan `task_id` dan `status` = `task.status.status`. Selain itu lewati.
8. **Segmen.** `nataflow workdir <workdir.name> · <documents_total> dokumen (<created> baru, <updated> diperbarui, <same + unchanged> sama)`. Tool galat di langkah mana pun → segmen `nataflow GAGAL: <pesan tool apa adanya>`, dan langkah sesudahnya tidak dijalankan.

## Langkah — dokumen repo

Dipakai `review` dan `profile`. Urutannya sama dengan langkah taskdir, dengan perbedaan berikut:

- Langkah 1 memakai `<sync_payload.py> --repo-docs <review | profile> --json`. `PASS` membawa `workspace_id` (ditambah `workspace_choices` bila workspace lebih dari satu), bukan `task`/`workdir`.
- Langkah 2 cukup memuat `list_workspace`, `list_document`, dan `upsert_document`.
- Langkah 3–4 diganti penentuan induk: `workspace_choices` ada → tanyakan dulu workspace tujuan lewat `AskUserQuestion` (satu opsi per entri: label `alias`, deskripsi `workspace_id`), lalu jalankan ulang langkah 1 dengan `--workspace <alias terpilih>`; `workspace_id` keluarannya induknya. `workspace_id` terisi → itu induknya. Kosong tanpa pilihan (`workspaces` tidak diisi) → `list_workspace`, dan tepat satu workspace → `id`-nya; selain itu segmen `nataflow GAGAL: key menjangkau <n> workspace — daftarkan di workspaces .claude/nataflow.json`; selesai.
- Langkah 5–6 memakai `reference_id` = workspace itu, dan perintah `--remote` memakai `--repo-docs` yang sama. Langkah 7 tidak ada.
- Segmen: `nataflow repo · <documents_total> dokumen (<created> baru, <updated> diperbarui, <same + unchanged> sama)`.

## Larangan

- Dilarang menyusun, menyunting, meringkas, atau menerjemahkan nilai argumen di luar keluaran `sync_payload.py`. Satu-satunya nilai dari balikan tool adalah `task_id`, `workspace_id` task untuk `upsert_workdir`, dan `reference_id`. `metadata` dikirim sebagai teks JSON persis seperti tercetak.
- Dilarang memilih berkas sendiri: dokumen gate `DRAFT`, hop yang DRIFT, `.explore/`, dan akar yang belum terkunci sengaja tidak ada di payload. Berkas taskdir yang dihapus dari disk tidak didorong ulang; baris remote-nya dibiarkan dengan isi terakhir.
- Dilarang memanggil `upsert_documents` (batch) atau `delete_document`. Berkas yang dihapus dari git sudah diterbitkan skrip dengan metadata `removed: true`.
- Dilarang memilih workspace sendiri: `workspace_choices` selalu ditanyakan ke user, dan `--workspace` hanya menerima alias yang dipilih user.
- Dilarang mengulang `create_task` sesudah tool galat tanpa `list_task` ulang. Tulisan yang ternyata sampai di server membuat task kembar.
- Dilarang menjalankan prosedur ini dari subagent, menulis berkas, menjalankan `chain.py`, atau meng-commit sebagai bagiannya.

## Prasyarat di luar plugin

- Server MCP nataflow terdaftar di Claude Code user beserta MCP key-nya. Plugin tidak mendeklarasikan server dan tidak menyimpan key.
- `.claude/nataflow.json` di root repo (ter-commit) mengaktifkan sinkron. Berkas ada tetapi rusak → `FAIL`, bukan dilewati. Berkas yang sama dibaca plugin `analyst`, `backend`, dan `quickdev`.

| Field | Wajib | Aturan |
|---|---|---|
| `mcp_server` | tidak | nama server MCP di konfigurasi Claude Code user; default `nataflow-api` |
| `workspaces` | tidak | objek alias → UUID workspace, urutan entri dipertahankan. Kosong → workspace milik key. Satu entri → dipakai otomatis. Lebih dari satu → user memilih saat task baru dibuat atau dokumen repo disinkron; task yang sudah ada ditemukan di workspace mana pun dalam jangkauan key dan tidak bisa dipindah. Lebih dari satu workspace butuh MCP key ber-scope project Tiket dan taskdir di workspace berbeda hanya bisa bertaut bila key ber-scope project |
| `pic_id` | tidak | UUID; kosong → server memakai pemilik key |
| `repo` | tidak | identitas repo di kunci workdir dan dokumen repo; kosong → remote `origin` ternormalisasi, lalu nama direktori root |

Kunci lain (termasuk `workspace_id` tunggal lama — ganti dengan `workspaces`), nilai bukan string, alias tidak sah, UUID tidak sah atau kembar, atau `repo` berspasi → `FAIL`.
