# nataflow

Skill untuk kerja langsung dengan server nataflow lewat MCP, dipanggil skrip plugin sendiri (`python3` stdlib). Berbeda dari sinkron di `analyst`, `backend`,
`frontend`, dan `quickdev` yang mencerminkan berkas repo ke nataflow, isi yang dibuat plugin ini hanya hidup di
server: repo tidak disentuh dan tidak ada yang di-commit.

Saat ini ada satu skill, `create-artifact`.

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install nataflow@nataflow
```

Prasyarat:

- Akses ke server nataflow organisasi (`nataflow-api`, aplikasi terpisah yang tidak ikut marketplace ini): URL
  endpoint MCP `/mcp` dan MCP key dari admin nataflow. Tanpa akses itu plugin ini tidak dapat dipakai.
- `.claude/nataflow.json` (root repo, atau cwd di luar git) berisi `url` endpoint MCP, mis.
  `{"url": "https://api.flow.natakode.id/mcp"}`, dan `.claude/nataflow.local.json` berisi
  `{"mcp_key": "<MCP key>"}` — di repo git berkas key wajib diabaikan git. Server tidak perlu didaftarkan di
  Claude Code. Config lama ber-`mcp_server` ditolak: lihat `MIGRATION_v0.1.1_to_v0.2.0.md`. Dampaknya bagi plugin
  lain: README root, bagian "Server nataflow".
- `python3` ≥ 3.9 (hanya stdlib) untuk `skills/create-artifact/scripts/artifact.py`.
- Repo git tidak wajib.

## `create-artifact`

Mirip Artifact claude.ai: model menulis satu halaman HTML mandiri (laporan, dashboard, diagram, prototipe), lalu
menerbitkannya ke nataflow. Artifact disimpan sebagai `document` ber-`type` `artifact` dan bermimetype
`text/html` di bawah **project milik MCP key**. Endpoint `GET /api/v1/documents/{id}/render` menyajikannya
kepada user login yang berhak atas project, dengan `Content-Security-Policy: sandbox allow-scripts`.

Skill boleh dipicu model (tanpa `disable-model-invocation`), jadi "buatkan artifact nataflow berisi …" cukup.
Pemanggilan eksplisit: `/nataflow:create-artifact <apa yang ditampilkan>`.

```
artifact.py config (get_project_info)  →  [perbarui: artifact.py list / pull]
  →  draft HTML  →  artifact.py check (maks 3 putaran)  →  artifact.py publish (cek tabrakan key → upsert_artifact)
  →  CREATED | UPDATED | UNCHANGED | DIBATALKAN | GAGAL
```

- **Server sumber kebenaran.** Draft ditulis ke direktori scratchpad sesi (atau `<tmp>/nataflow-artifacts/`)
  sebagai bahan kerja sementara. Pembaruan selalu berangkat dari `artifact.py pull` (isi `get_artifact` ditulis skrip ke berkas draft), bukan dari draft lama. Isi HTML tidak pernah lewat konteks model.
- **Selalu project.** `reference_table` = `project` dan `reference_id` = `id` balikan `get_project_info`.
  Setiap MCP key terikat ke tepat satu project.
- **Tidak menimpa diam-diam.** Sebelum artifact baru diterbitkan, key-nya dicek dengan `get_document`. Key milik
  artifact lain memicu pertanyaan timpa, `<key>-v2`, atau batal. Key milik dokumen non-artifact hanya
  ditawari `<key>-v2` atau batal, karena `upsert_artifact` akan mengubah dokumen itu jadi artifact.
- **Tidak menghapus.** Skill tidak pernah memanggil `delete_document`.

### Gerbang `artifact.py`

| Subperintah | Keluaran |
|---|---|
| `config [--json]` | `url`, `project_id`, `project_name` (project tunggal milik key), `draft_dir`; `FAIL` bila config/key belum disetel |
| `check --file <draft> [--key <key>] [--json]` | tanpa jaringan: `key` (dari `--key` atau slug `<title>`), `title`, `bytes`, `content_sha256`, `metadata` (`{"title","source"}`), `problems`, `warnings` |
| `list [--json]` | `artifacts` (`key`, `title`) project, tanpa isi |
| `pull --key <key> --file <draft> [--json]` | menulis isi artifact ke berkas draft; `NOT_FOUND` bila tidak ada |
| `publish --file <draft> [--key <key>] [--overwrite] [--json]` | `check`, cek tabrakan `get_document`, lalu `upsert_artifact`: `CREATED`/`UPDATED`/`UNCHANGED` + `id`, atau `TABRAKAN` (artifact lain, butuh `--overwrite`) / `TABRAKAN_DOKUMEN` (dokumen non-artifact, tidak pernah ditimpa) |

Exit 1 hanya untuk `FAIL`; status lain exit 0. `check` gagal bila salah satu berikut terjadi:

- berkas bukan UTF-8, ber-BOM, kosong, atau lebih dari 1 MiB;
- tidak ada `<!doctype html>`, `<meta charset>`, `<meta name="viewport">`, atau `<title>` (maks 120 karakter);
- ada `<script src>` di luar cdnjs, jsDelivr `/npm/`, unpkg, Tailwind CDN, atau jQuery CDN, atau stylesheet di
  luar Google Fonts;
- ada rujukan relatif yang dimuat browser (`<img src="a.png">`, `<link rel="stylesheet" href="a.css">`);
- ada `<input type="password">`;
- skrip inline atau atribut `on*` memakai `localStorage`, `sessionStorage`, `indexedDB`, atau `document.cookie`
  (melempar `SecurityError` di sandbox render);
- `--key` bukan kebab-case (maks 80 karakter), atau judul tidak menghasilkan slug.

Peringatan (tidak menggagalkan): tanpa `prefers-color-scheme`, warna tanpa token `--*` di `:root`,
`alert`/`confirm`/`prompt`, tautan `target="_blank"`, `<form action>` (ketiganya diblokir sandbox), dan judul
lebih dari 6 kata. Kontrak lengkapnya ada di
`skills/create-artifact/references/page-contract.md`.

### Kontrak tool MCP

Tool artifact disediakan server `nataflow-api` dan dipanggil `artifact.py` lewat `nataflow_client` (bukan oleh model):

| Tool | Argumen yang dikirim skill | Balikan yang dipakai |
|---|---|---|
| `get_project_info` | — | `id`, `name` |
| `list_artifacts` | `reference_table`, `reference_id`, `include_content=false` | `key`, `metadata.title` |
| `get_artifact` | `reference_table`, `reference_id`, `key` | `content`, `key`; galat `document not found` bila tidak ada atau bukan artifact |
| `get_document` | `reference_table`, `reference_id`, `key` | `type`, `mimetype`, `metadata.title`; hanya untuk cek tabrakan key |
| `upsert_artifact` | `reference_table`, `reference_id`, `key`, `content`, `content_sha256`, `metadata` | `action` (`created`/`updated`/`unchanged`), `id` |

- `type` dan `mimetype` tidak dikirim: tool artifact mematoknya ke `artifact` dan `text/html`.
- `upsert_artifact` menyimpan `content` persis dan menolak `content_sha256` yang tidak cocok dengan pesan
  `content_sha256 does not match content`. `metadata` menggantikan metadata tersimpan seluruhnya.
- `upsert_artifact` atas key milik dokumen non-artifact menimpanya jadi artifact (perilaku server). Karena
  itu cek tabrakan memakai `get_document`, bukan `get_artifact`.
- `create_artifact` tidak dipakai: tool itu tidak ber-key dan memangkas spasi `content`, sehingga sha256 berubah.
- Balikan tool tidak memuat URL. Endpoint render menuntut header `Authorization: Bearer <token>`, jadi
  konsumennya (frontend) mengambil HTML lewat fetch lalu menampilkannya di `<iframe sandbox srcdoc>`;
  navigasi langsung dari browser ditolak 401.

## Keterbatasan yang Diketahui

- **Artifact adalah potret.** Halaman tidak boleh memanggil API nataflow; datanya disematkan saat ditulis.
- **Tanpa riwayat versi.** `upsert_artifact` menimpa isi; versi lama tidak tersimpan di server.
- **Belum ada tampilan di aplikasi.** Frontend nataflow belum punya layar artifact, jadi saat ini artifact baru
  bisa dibuka lewat request ber-token ke endpoint render.
- **Ukuran dibatasi 1 MiB** karena seluruh isi dikirim sebagai satu argumen tool dan ikut dihitung token.
