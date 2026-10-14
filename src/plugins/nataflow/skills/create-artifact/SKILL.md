---
name: create-artifact
description: Gunakan ketika user meminta membuat atau memperbarui artifact nataflow — halaman HTML mandiri (laporan, dashboard, diagram, ringkasan, prototipe) yang disimpan ke project nataflow lewat tool MCP artifact dan dibuka anggota project di endpoint render — kontrak halaman satu berkas, gerbang artifact.py, dan upsert ke project milik MCP key, sebelum HTML disimpan ke repo atau dibagikan lewat jalur lain.
argument-hint: "[apa yang ingin ditampilkan | key artifact yang diperbarui]"
---

## THE IRON LAW

ARTIFACT HANYA HIDUP DI SERVER NATAFLOW DAN SELALU MENEMPEL KE PROJECT MILIK MCP KEY. DILARANG MENERBITKAN DRAFT YANG BELUM `PASS` DI `artifact.py check`, DILARANG MENGIRIM ISI SELAIN BERKAS DRAFT APA ADANYA BERSAMA `content_sha256`-NYA, DAN DILARANG MENIMPA ARTIFACT YANG SUDAH ADA TANPA PERSETUJUAN EKSPLISIT USER. DILARANG MENULIS ARTIFACT KE REPO ATAU MENG-COMMIT APA PUN.

## Precondition [REQUIRED]

1. Server MCP nataflow terdaftar di Claude Code user beserta MCP key-nya, dan backend-nya berjalan. Plugin tidak
   mendeklarasikan server dan tidak menyimpan key.
2. Server itu menyediakan `get_project_info`, `list_artifacts`, `get_artifact`, `upsert_artifact`, dan
   `get_document`.
3. `python3` ≥ 3.9 untuk `${CLAUDE_PLUGIN_ROOT}/skills/create-artifact/scripts/artifact.py`.

Repo git tidak wajib. Bila skill dipanggil di dalam repo, `.claude/nataflow.json` di root repo (berkas yang sama
dengan sinkron plugin lain) hanya dibaca untuk field `mcp_server`.

## Koeksistensi [REQUIRED]

- Permintaan menyebut nataflow, project nataflow, atau `/nataflow:create-artifact` → lanjutkan skill ini.
- Permintaan "buat artifact/halaman" tanpa menyebut tujuan, sementara sesi juga punya tool `Artifact` milik
  claude.ai → tanyakan sekali lewat `AskUserQuestion`: *Artifact nataflow (project MCP key)* · *Artifact
  claude.ai*. Jangan memilih sendiri.
- Skill ini tidak mengubah berkas repo, jadi bukan kerja yang digerbangi `backend:tech-lead`, `frontend:lead`,
  atau `quickdev:*`. Teks gerbang engineer `backend`/`frontend` mengecualikan `/nataflow:*` beserta susulannya,
  jadi blok gerbang di konteks sesi tidak menahannya.

## Parameter

- `request` — string — `[REQUIRED]` — isi dan tujuan halaman dari pesan user.
- `key` — string — opsional — kunci artifact kebab-case (maks 80 karakter). Kosong → diturunkan dari `<title>`
  oleh `artifact.py check`.
- `mode` — `auto` | `baru` | `perbarui` — default `auto`: `perbarui` bila user menyebut artifact yang sudah ada
  (key, judul, atau id) atau meminta mengubah artifact, selain itu `baru`.

`<artifact.py>` di bawah adalah `python3 ${CLAUDE_PLUGIN_ROOT}/skills/create-artifact/scripts/artifact.py`.

## Workflow

### Fase 0 — Server dan project

1. `<artifact.py> config --json`. `FAIL` → status `GAGAL: <isi problems apa adanya>`; selesai. `PASS` → pegang
   `mcp_server` dan `draft_dir`.
2. Muat lewat ToolSearch (`select:`) kelima tool `mcp__<mcp_server>__get_project_info`, `…__list_artifacts`,
   `…__get_artifact`, `…__upsert_artifact`, dan `…__get_document`. Salah satu tidak tersedia → `GAGAL: tool
   artifact tidak tersedia di server MCP <mcp_server>`; selesai.
3. `get_project_info` tanpa argumen. Pegang `id` dan `name` project balikannya: `id` itulah `reference_id`
   untuk setiap panggilan artifact, dengan `reference_table` = `project`. Tool galat → `GAGAL: <pesan tool apa
   adanya>`; selesai.

### Fase 1 — Mode

- **baru** → lanjut ke Fase 2 dengan draft kosong.
- **perbarui** → tentukan artifact sasaran:
  - `key` diketahui → `get_artifact` dengan `reference_table`, `reference_id`, dan `key`. Galat `document not
    found` → tanyakan: *Buat artifact baru* · *Batal*.
  - Hanya judul atau deskripsi → `list_artifacts` dengan `reference_table`, `reference_id`, dan
    `include_content` = `false`; cocokkan dengan `key` dan `metadata.title` tiap entri. Tepat satu yang cocok →
    `get_artifact` untuknya. Lebih dari satu → `AskUserQuestion` (satu opsi per kandidat, label `key`,
    deskripsi `metadata.title`). Nol → tanyakan: *Buat artifact baru* · *Batal*.
  - Tulis `content` balikan `get_artifact` apa adanya ke berkas draft (Fase 2 langkah 2), lalu pegang `key`-nya.
    Server, bukan draft lama di disk, selalu menjadi titik awal pembaruan.

### Fase 2 — Draft

1. Muat `references/page-contract.md`.
2. Path draft: `<scratchpad>/nataflow-artifacts/<nama>.html` bila system prompt menyebut direktori scratchpad
   sesi, selain itu `<draft_dir>/<nama>.html`. Draft adalah bahan kerja sementara, bukan salinan resmi.
3. Tulis (mode `baru`) atau sunting (mode `perbarui`) draft sesuai `request` dan kontrak halaman.
4. Data yang ditampilkan berasal dari percakapan, berkas yang user tunjuk, atau hasil tool di sesi ini. Angka,
   nama, atau fakta yang tidak ada di sumber itu ditanyakan ke user, bukan dikarang.

### Fase 3 — Gerbang

1. `<artifact.py> check --file <draft> --json`, ditambah `--key <key>` bila key berasal dari parameter atau
   dari artifact yang diperbarui.
2. `FAIL` → perbaiki draft sesuai `problems`, lalu jalankan ulang. Maksimal 3 putaran; masih `FAIL` → `GAGAL:
   <problems terakhir>`; selesai tanpa memanggil tool tulis.
3. `warnings` → perbaiki juga, kecuali user sudah meminta lain; sebut sisa peringatan di ringkasan.
4. `PASS` → pegang `key`, `title`, `bytes`, `content_sha256`, dan `metadata` keluaran terakhir apa adanya.

### Fase 4 — Terbit

1. **Tabrakan key (mode `baru`).** `get_document` dengan `reference_table`, `reference_id`, dan `key`. Pakai
   `get_document`, bukan `get_artifact`: `upsert_artifact` menimpa dokumen **apa pun** ber-key sama di induk itu
   dan mengubahnya jadi artifact, sedangkan `get_artifact` menjawab `document not found` untuk dokumen
   non-artifact.
   - Galat `document not found` → lanjut.
   - Ditemukan dengan `type` = `artifact` dan `mimetype` = `text/html` → `AskUserQuestion`: *Timpa artifact
     `<key>` (<metadata.title lama>)* · *Pakai key `<key>-v2`* · *Batal*.
   - Ditemukan dengan `type`/`mimetype` lain → jangan tawarkan timpa. `AskUserQuestion`: *Pakai key
     `<key>-v2`* · *Batal*, dengan keterangan bahwa key itu sudah dipakai dokumen `<type>`.
   - `-v2` → jalankan ulang Fase 3 dengan `--key <key>-v2` lalu langkah ini lagi (naikkan angkanya bila masih
     bertabrakan). Batal → status `DIBATALKAN`; selesai. Galat tool lain → `GAGAL: <pesan tool apa adanya>`.
2. `upsert_artifact` dengan `reference_table` = `project`, `reference_id` = `id` project Fase 0, `key`,
   `content` = isi berkas draft apa adanya, `content_sha256`, dan `metadata` (teks JSON persis seperti tercetak).
3. Galat `content_sha256 does not match content` → baca ulang berkas draft dan kirim sekali lagi tanpa mengubah
   isinya. Gagal lagi, atau galat lain → `GAGAL: <pesan tool apa adanya>`.
4. Pegang `action` (`created`, `updated`, `unchanged`) dan `id` balikan. Balikan tidak memuat isi maupun URL.

## Larangan

- Dilarang memakai `reference_table` selain `project` atau `reference_id` selain `id` dari `get_project_info`.
- Dilarang memakai `upsert_document`/`create_document`/`create_artifact` untuk artifact (`create_artifact` tidak
  ber-key dan memangkas spasi isi sehingga sha256 berubah), dan dilarang memanggil `delete_document`: skill ini
  tidak pernah menghapus artifact. `get_document` hanya untuk cek tabrakan key di Fase 4.
- Dilarang menyunting `key`, `content_sha256`, atau `metadata` keluaran `check`, atau mengetik ulang isi HTML
  dari ingatan saat memanggil `upsert_artifact`.
- Dilarang menyalin draft ke repo, menambah berkas ke `.gitignore`, atau meng-commit. Bila user ingin salinan
  di repo, itu permintaan terpisah di luar skill ini.
- Dilarang menyematkan rahasia (token, MCP key, password, isi `.env`) di halaman: artifact terbaca semua anggota
  project.

## Output [REQUIRED]

Status terminal: `CREATED`, `UPDATED`, `UNCHANGED`, `DIBATALKAN`, atau `GAGAL: <sebab>`.

```
ARTIFACT: <key> · <title>
STATUS: CREATED | UPDATED | UNCHANGED | DIBATALKAN | GAGAL: <sebab>
PROJECT: <nama project> (<id project>)
ID: <id artifact | ->
RENDER: GET /api/v1/documents/<id>/render (butuh header Authorization) | -
UKURAN: <bytes> byte · sha256 <12 hex pertama>
PERINGATAN: <sisa warnings | ->
```

Sesudah blok itu, satu kalimat tentang isi halaman. Jangan menempelkan HTML-nya di chat.

## Failure path

1. **Server MCP mati atau belum terdaftar** (`ECONNREFUSED`, tool tidak ditemukan) → `GAGAL`; sarankan user
   menjalankan backend nataflow atau mendaftarkan server `<mcp_server>` beserta MCP key-nya. Draft tetap di
   path Fase 2 untuk dicoba lagi.
2. **Tool artifact belum ada, tetapi tool dokumen ada** → `GAGAL: server <mcp_server> belum menyediakan tool
   artifact`. Jangan jatuh ke `upsert_document`.
3. **`get_project_info` galat** (key tanpa project, key kedaluwarsa) → `GAGAL: <pesan tool>`; jangan menebak id
   project.
4. **Draft tidak lolos 3 putaran** → `GAGAL` dengan `problems` terakhir dan path draft, supaya user bisa
   memutuskan mengubah isi atau lingkup.
