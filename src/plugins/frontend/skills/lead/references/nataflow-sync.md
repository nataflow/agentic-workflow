# Prosedur Sinkron nataflow

Dimuat di main loop oleh skill pemilik titik status frontend, tepat saat dokumen taskdir disetujui atau tuntas (tabel di bawah) — bukan ditunda ke akhir rantai. Subagent tidak pernah menjalankannya. Hasilnya tepat satu segmen `nataflow <…>` untuk baris penutup skill pemanggil: `nataflow workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama)`, `nataflow repo · <n> dokumen (…)`, `nataflow dilewati`, atau `nataflow GAGAL: <sebab>`.

Disk (dokumen taskdir) dan git (dokumen tingkat repo) tetap sumber kebenaran; nataflow hanya cermin. Prosedur ini tidak menulis berkas dan tidak meng-commit, sehingga ledger `## Chain`, `## Riwayat Rantai` (materai approve), dan tree bersih tidak tersentuh. Dokumen taskdir tidak di-commit (Langkah 24), jadi isinya dibaca dari disk; nataflow satu-satunya salinannya di luar mesin ini. `GAGAL` tidak menahan gate maupun eksekusi, dan sinkron diulang lewat rute "sinkron ulang taskdir" `frontend:lead`.

`<sync_payload.py>` di bawah adalah `python3 <root plugin frontend>/skills/_common/sync_payload.py`, root yang sama dengan `chain.py` skill pemanggil.

## Titik panggil

| Skill | Titik | Target |
|---|---|---|
| `task` | Phase 4 sesudah `chain.py root` | `--taskdir <taskdir>` |
| `lead` | Keadaan `AKAR` sesudah `chain.py root` tertinggal; Phase 8 sesudah `chain.py reopen`/`escalate`/`abandon`/`amend`; rute "sinkron ulang taskdir" | `--taskdir <taskdir>` |
| `ux-design`, `ui-design`, `contract`, `plan` | Butir **Setuju**, sesudah `chain.py approve` PASS | `--taskdir <taskdir>` |
| `architect` | Phase 4 butir 4, sesudah `REVIEW.md` lolos `validate_review.py` (verdict apa pun); Phase 5 butir 4, sesudah laporan tertunda lolos `validate_report.py` | `--taskdir <taskdir>` |
| `architect` | Sebelum baris `ARCHITECT — …` atau blok `### ARCHITECT — BLOCKED`/`TERTAHAN`, hanya bila putaran itu tidak melewati titik review maupun laporan (rantai berhenti sebelum review, atau `REPORT.md` sudah terbit) | `--taskdir <taskdir>` |
| `report` | Phase 4 sesudah `REPORT.md` lolos `validate_report.py` | `--taskdir <taskdir>` |
| `review` | Sesudah commit laporan `frontenddev/reviews/` | `--repo-docs review` |
| `profile` | Sesudah commit profil (termasuk PATCH) | `--repo-docs profile` |


## Langkah

Jalankan `<sync_payload.py> --taskdir <taskdir> --push`, atau `<sync_payload.py> --repo-docs <review | profile> --push` untuk dokumen repo (target per titik panggil di tabel atas).

Skrip membaca config dan MCP key, memilih dokumen yang stabil, lalu memanggil sendiri tool server nataflow: cari task lewat identitasnya (buat bila belum ada), `upsert_workdir` di workspace task induknya, manifest `list_document`, `upsert_document` hanya untuk dokumen yang berbeda, lalu status task. Task tiket analyst baru ditutup `done` bila seluruh workdir di bawahnya tuntas. Isi dokumen tidak pernah lewat konteks model.

Keluarannya tepat satu baris, yang disalin apa adanya sebagai segmen:

- `nataflow workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama)` atau `nataflow repo · <n> dokumen (…)` → selesai.
- `nataflow dilewati` (`.claude/nataflow.json` tidak ada) → selesai.
- `nataflow GAGAL: <sebab>` → selesai. Sebab setup (`.claude/nataflow.local.json` tidak ada, tidak diabaikan git, `url` belum diisi, atau `mcp_server` lama) disampaikan ke user apa adanya bersama bagian Prasyarat di bawah. Task kembar (`<n> task ber-… sama`) berhenti sebelum tulisan apa pun.
- `nataflow PILIH_WORKSPACE: <alias> (<uuid>), …` → muncul hanya untuk task baru atau dokumen repo saat `workspaces` berisi lebih dari satu entri, sebelum tulisan apa pun. Tanyakan workspace tujuan lewat `AskUserQuestion` (satu opsi per alias: label alias, deskripsi UUID), lalu jalankan ulang perintah yang sama dengan `--workspace <alias terpilih>` dan pakai segmen keluarannya.

## Larangan

- Dilarang memanggil tool MCP nataflow (`mcp__…`) sendiri untuk sinkron ini, menyusun argumen tool, atau menyalin isi dokumen ke chat: `--push` satu-satunya jalur.
- Dilarang memilih workspace sendiri: `--workspace` hanya menerima alias yang dipilih user.
- Dilarang mengulang `--push` di giliran yang sama sesudah `GAGAL`; sinkron diulang lewat rute sinkron ulang. Pengulangan aman: skrip selalu mencari task lebih dulu, dan tulisan yang gagal tidak pernah diulang otomatis.
- Dilarang membaca, mencetak, atau menyunting `.claude/nataflow.local.json`.
- Dilarang menjalankan prosedur ini dari subagent, menulis berkas, menjalankan `chain.py`, atau meng-commit sebagai bagiannya.

## Prasyarat di luar plugin

- `.claude/nataflow.json` di root repo (ter-commit, tanpa rahasia) mengaktifkan sinkron. Berkas absen → `dilewati`; ada tetapi rusak → `GAGAL`, bukan dilewati. Berkas yang sama dibaca plugin `analyst`, `backend`, `quickdev`, dan `nataflow`.
- `.claude/nataflow.local.json` di root repo menyimpan MCP key: `{"mcp_key": "<MCP key nataflow>"}`. Berkas ini tidak pernah di-commit: di repo git ia wajib tercantum di `.gitignore` (baris `.claude/nataflow.local.json`). Berkas absen, tidak diabaikan git, atau sudah ter-track → `GAGAL` sebelum satu panggilan server pun; root non-git tidak dicek ignore. Skill tidak pernah membaca, mencetak, atau menyalin isinya.
- Server nataflow di `url` terjangkau dari mesin ini (`python3` membuka koneksi HTTPS sendiri). Plugin tidak memakai server MCP yang terdaftar di Claude Code untuk sinkron ini.
- Migrasi dari config lama ber-`mcp_server`: lihat `MIGRATION_v0.17.0_to_v0.18.0.md` di root plugin frontend.

| Field | Wajib | Aturan |
|---|---|---|
| `url` | **ya** | endpoint MCP server nataflow, mis. `https://api.flow.natakode.id/mcp`: `https://` (http hanya untuk `localhost`/`127.0.0.1`), path berakhir di `/mcp`, tanpa kredensial |
| `workspaces` | tidak | objek alias → UUID workspace, urutan entri dipertahankan. Kosong → workspace milik key. Satu entri → dipakai otomatis. Lebih dari satu → user memilih saat task baru dibuat atau dokumen repo disinkron; task yang sudah ada ditemukan di workspace mana pun dalam jangkauan key dan tidak bisa dipindah. Lebih dari satu workspace butuh MCP key ber-scope project |
| `pic_id` | tidak | UUID; kosong → server memakai pemilik key |
| `repo` | tidak | identitas repo di kunci workdir, metadata task, dan dokumen repo; kosong → remote `origin` ternormalisasi, lalu nama direktori root |

Kunci lain → `GAGAL`: `mcp_server` lama (nama server MCP di Claude Code, tidak dipakai lagi — ganti dengan `url`) dan `workspace_id` tunggal lama (ganti dengan `workspaces`) disebut beserta penggantinya. Nilai bukan string, `url` tidak sah, alias tidak sah, UUID tidak sah atau kembar, atau `repo` berspasi juga `GAGAL`.
