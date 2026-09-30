# Alur Plugin `nataflow`

Peta end-to-end plugin `nataflow`: skill yang bekerja langsung terhadap server nataflow lewat MCP, tanpa
artefak di repo pengguna.

## Peta Komponen

| Komponen | Path | Peran |
|---|---|---|
| Skill `create-artifact` | `src/plugins/nataflow/skills/create-artifact/SKILL.md` | tulis, nilai, dan terbitkan halaman HTML ke project MCP key |
| Kontrak halaman | `skills/create-artifact/references/page-contract.md` | aturan kerangka, aset, tema, tata letak, dan larangan isi |
| Gerbang | `skills/create-artifact/scripts/artifact.py` | `config` (server MCP, direktori draft) dan `check` (kontrak halaman, key, sha256, metadata) |

Tanpa subagent, tanpa hook, tanpa taskdir, dan tanpa `nataflow_sync.py`.

## `nataflow:create-artifact`

```
Fase 0  artifact.py config  ── FAIL ─────────────────────────────→ GAGAL
        ToolSearch 4 tool   ── tidak ada ────────────────────────→ GAGAL
        get_project_info    ── galat ────────────────────────────→ GAGAL
Fase 1  mode perbarui: list_artifacts → get_artifact → isi ke draft
Fase 2  draft HTML (page-contract.md)
Fase 3  artifact.py check  ── FAIL ×3 ───────────────────────────→ GAGAL
Fase 4  mode baru: get_artifact(key) ── ada → tanya: timpa | -v2 | batal → DIBATALKAN
        upsert_artifact(project, id, key, content, sha256, metadata)
                            ── sha tidak cocok → kirim ulang sekali
        → CREATED | UPDATED | UNCHANGED
```

Pemicu: model atau user (`/nataflow:create-artifact`). Bila sesi juga punya tool `Artifact` claude.ai dan
permintaan tidak menyebut tujuan, skill bertanya sekali.

## Artefak & Siklus Status

| Artefak | Lokasi | Umur |
|---|---|---|
| Draft HTML | `<scratchpad>/nataflow-artifacts/<nama>.html` atau `<tmp>/nataflow-artifacts/` | sementara; tidak pernah dibaca ulang sebagai sumber |
| Artifact | `document` `text/html` di bawah project MCP key, diidentifikasi `key` | tetap di server; ditimpa oleh upsert berikutnya |

`metadata` artifact: `{"title": <isi <title>>, "source": "nataflow:create-artifact"}`.

## Titik Gagal & Pemulihan

| Gejala | Status | Pemulihan |
|---|---|---|
| `ECONNREFUSED` / tool tidak ditemukan | `GAGAL` | jalankan backend atau daftarkan server MCP, lalu panggil skill lagi; draft masih di disk |
| Hanya tool dokumen yang ada | `GAGAL` | tunggu tool artifact di backend; skill tidak jatuh ke `upsert_document` |
| Draft `FAIL` 3 putaran | `GAGAL` | user mengubah isi/lingkup; `problems` terakhir dilaporkan |
| sha256 ditolak dua kali | `GAGAL` | panggil skill lagi dalam mode `perbarui` atau `baru` |
