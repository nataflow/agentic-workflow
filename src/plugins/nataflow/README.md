# nataflow

Skill untuk kerja langsung dengan server nataflow lewat MCP. Berbeda dari sinkron di `analyst`, `backend`,
`frontend`, dan `quickdev` yang mencerminkan berkas repo ke nataflow, isi yang dibuat plugin ini hanya hidup di
server: repo tidak disentuh dan tidak ada yang di-commit.

Saat ini ada satu skill, `create-artifact`.

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install nataflow@nataflow
```

Prasyarat:

- Server MCP nataflow terdaftar di Claude Code user beserta MCP key-nya (default bernama `nataflow-api`), dan
  backend-nya berjalan. Plugin tidak mendeklarasikan server dan tidak menyimpan key.
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
config (artifact.py)  →  get_project_info  →  [perbarui: list_artifacts / get_artifact]
  →  draft HTML  →  check (artifact.py, maks 3 putaran)  →  cek tabrakan key  →  upsert_artifact
  →  CREATED | UPDATED | UNCHANGED | DIBATALKAN | GAGAL
```

- **Server sumber kebenaran.** Draft ditulis ke direktori scratchpad sesi (atau `<tmp>/nataflow-artifacts/`)
  sebagai bahan kerja sementara. Pembaruan selalu berangkat dari `get_artifact`, bukan dari draft lama.
- **Selalu project.** `reference_table` = `project` dan `reference_id` = `id` balikan `get_project_info`.
  Setiap MCP key terikat ke tepat satu project.
- **Tidak menimpa diam-diam.** Sebelum artifact baru diterbitkan, key-nya dicek dengan `get_document`. Key milik
  artifact lain memicu pertanyaan timpa, `<key>-v2`, atau batal. Key milik dokumen non-artifact hanya
  ditawari `<key>-v2` atau batal, karena `upsert_artifact` akan mengubah dokumen itu jadi artifact.
- **Tidak menghapus.** Skill tidak pernah memanggil `delete_document`.

### Gerbang `artifact.py`

| Subperintah | Keluaran |
|---|---|
| `config [--json]` | `mcp_server` (dari `.claude/nataflow.json` root repo bila ada, default `nataflow-api`), `config_source`, `draft_dir` |
| `check --file <draft> [--key <key>] [--json]` | `key` (dari `--key` atau slug `<title>`), `title`, `bytes`, `content_sha256`, `metadata` (`{"title","source"}`), `problems`, `warnings` |

Exit 0 = `PASS`, 1 = `FAIL`. `check` gagal bila salah satu berikut terjadi:

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

Tool artifact berasal dari `nataflow-api` (taskdir `artifact-html-tools`). Yang dipakai skill:

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
- `upsert_artifact` atas key milik dokumen non-artifact menimpanya jadi artifact (keputusan PRD backend). Karena
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
