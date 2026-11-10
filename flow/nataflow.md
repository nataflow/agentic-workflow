# Alur Plugin `nataflow`

Peta end-to-end plugin `nataflow`: skill yang bekerja langsung terhadap server nataflow lewat MCP, tanpa
artefak di repo pengguna. Semua panggilan server dijalankan `artifact.py` lewat `nataflow_client.py`
(langkah 29); model tidak memanggil tool MCP dan isi HTML tidak lewat konteksnya.

## Peta Komponen

| Komponen | Path | Peran |
|---|---|---|
| Skill `create-artifact` | `src/plugins/nataflow/skills/create-artifact/SKILL.md` | tulis, nilai, dan terbitkan halaman HTML ke project MCP key |
| Kontrak halaman | `skills/create-artifact/references/page-contract.md` | aturan kerangka, aset, tema, tata letak, sandbox render, dan larangan isi |
| Gerbang | `skills/create-artifact/scripts/artifact.py` | `config` (url, key, project), `check` (kontrak halaman, key, sha256, metadata), `list`, `pull`, `publish` |
| Pustaka bersama | `skills/create-artifact/scripts/nataflow_sync.py`, `nataflow_client.py` | config `url` + MCP key `.claude/nataflow.local.json`, klien MCP; salinan identik plugin sinkron |

Tanpa subagent, tanpa hook, dan tanpa taskdir.

## `nataflow:create-artifact`

```
Fase 0  artifact.py config (url, key, get_project_info) ── FAIL ──→ GAGAL
Fase 1  mode perbarui: artifact.py list → artifact.py pull (isi ke draft)
                            ── NOT_FOUND → tanya: baru | batal
Fase 2  draft HTML (page-contract.md)
Fase 3  artifact.py check  ── FAIL ×3 ───────────────────────────→ GAGAL
Fase 4  artifact.py publish [--overwrite]: check → get_document(key) → upsert_artifact
                            ── TABRAKAN          → tanya: timpa (--overwrite) | -v2 | batal
                            ── TABRAKAN_DOKUMEN  → tanya: -v2 | batal
                            ── batal ──────────────────────────────→ DIBATALKAN
                            ── sha tidak cocok → skrip kirim ulang sekali
        → CREATED | UPDATED | UNCHANGED
```

Pemicu: model atau user (`/nataflow:create-artifact`). Bila sesi juga punya tool `Artifact` claude.ai dan
permintaan tidak menyebut tujuan, skill bertanya sekali.

## Artefak & Siklus Status

| Artefak | Lokasi | Umur |
|---|---|---|
| Draft HTML | `<scratchpad>/nataflow-artifacts/<nama>.html` atau `<tmp>/nataflow-artifacts/` | sementara; tidak pernah dibaca ulang sebagai sumber |
| Artifact | `document` `type=artifact`, `mimetype=text/html` di bawah project MCP key, diidentifikasi `key` | tetap di server; ditimpa oleh upsert berikutnya; dirender di `GET /api/v1/documents/{id}/render` (Bearer, CSP `sandbox allow-scripts`) |

`metadata` artifact: `{"title": <isi <title>>, "source": "nataflow:create-artifact"}`.

## Titik Gagal & Pemulihan

| Gejala | Status | Pemulihan |
|---|---|---|
| `ECONNREFUSED` / tool tidak ditemukan | `GAGAL` | jalankan backend atau daftarkan server MCP, lalu panggil skill lagi; draft masih di disk |
| Hanya tool dokumen yang ada | `GAGAL` | tunggu tool artifact di backend; skill tidak jatuh ke `upsert_document` |
| Draft `FAIL` 3 putaran | `GAGAL` | user mengubah isi/lingkup; `problems` terakhir dilaporkan |
| sha256 ditolak dua kali | `GAGAL` | panggil skill lagi dalam mode `perbarui` atau `baru` |
| Key dipakai dokumen non-artifact | tanya | pakai `<key>-v2`; menimpa tidak ditawarkan karena `upsert_artifact` akan mengubah dokumen itu jadi artifact |
