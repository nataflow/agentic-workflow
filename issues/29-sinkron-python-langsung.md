# Langkah 29 — Sinkron nataflow lewat skrip Python, tanpa tool MCP di konteks model (semua plugin sinkron)

Sumber: permintaan user (2026-11-10): "saya ingin supaya setiap task/document/workdir yang semuanya berbasis file di
local itu bisa di sync ke nataflow tanpa MCP tools, karena akan boros token". User memilih memaksimalkan skrip Python
stdlib di plugin ini alih-alih CLI Go (CLI `cmd/nataflow` dihapus dari repo backend nataflow pada hari yang sama).

Basis kode: commit `6ddce48` (analyst 0.18.0, backend 0.18.0, frontend 0.17.0, quickdev 0.10.0, nataflow 0.1.1).

**Status (2026-11-10):** SELESAI. S1–S7 terpasang; rilis analyst 0.19.0, backend 0.19.0, frontend 0.18.0,
quickdev 0.11.0, nataflow 0.2.0. Panduan migrasi per plugin: `src/plugins/<plugin>/MIGRATION_v<lama>_to_v<baru>.md`.

## Keadaan sebelum

Prosedur `nataflow-sync.md` (5 berkas) menyuruh model menjalankan skrip payload, memuat 6–7 tool `mcp__<mcp_server>__*`
lewat ToolSearch, lalu memanggilnya satu per satu sambil mengoper teks balikan kembali ke skrip lewat stdin. Isi
dokumen lewat konteks model dua kali: sebagai keluaran payload dan sebagai argumen `upsert_document`.
`create-artifact` sama: isi HTML dikirim model sebagai argumen `upsert_artifact`, dan `get_artifact` membawa isi
penuh ke konteks.

## Perubahan

| ID | Isi | Berkas |
|---|---|---|
| S1 | `url` wajib di `.claude/nataflow.json` (`mcp_server` ditolak dengan pesan migrasi); MCP key di `.claude/nataflow.local.json`, `load_key` fail-closed (wajib diabaikan git dan tidak ter-track; root non-git diizinkan) | `nataflow_sync.py` ×5 |
| S2 | Klien MCP Streamable HTTP stdlib: sesi `Mcp-Session-Id`, bearer, JSON/SSE, galat tanpa nilai key, tulisan tidak pernah diulang otomatis | `nataflow_client.py` ×5 |
| S3 | Mesin push bersama (`push_workdir`, `push_repo_docs`, `run_push`, `push_segment`) dan `sync_payload.py --push` | backend, frontend |
| S4 | `plan_lock.py sync-payload --push` (rencana dan profil) | quickdev |
| S5 | `ticket.py sync-payload --push` dan `notulen.py sync-payload --push` | analyst |
| S6 | `artifact.py config` (url, key, project), `list`, `pull`, `publish` (check → cek tabrakan → upsert) | nataflow |
| S7 | Prosedur `nataflow-sync.md` ×5 dan `create-artifact/SKILL.md` menjadi satu perintah; README, `flow/`, MIGRATION | dokumen |

## Keputusan

- **Key terpisah dari config.** `nataflow.json` tetap tanpa rahasia dan boleh di-commit; key di `nataflow.local.json`.
  Tanpa env var dan tanpa fallback `~/.claude.json` (format internal Claude Code, bukan kontrak).
- **Fail-closed.** Config ada tetapi key tidak tersedia → `GAGAL`, bukan dilewati diam-diam.
- **`url` wajib, tanpa default.** Endpoint server tercatat eksplisit per repo.
- **Pilihan workspace tetap milik user.** Skrip keluar `PILIH_WORKSPACE` sebelum tulisan apa pun; model bertanya lalu
  menjalankan ulang dengan `--workspace`.
- **Mode tanpa `--push` dipertahankan** untuk tes dan diagnosis; prosedur hanya memakai `--push`.
- **Satu kesatuan salinan.** `nataflow_sync.py` dan `nataflow_client.py` identik byte di lima lokasi (empat
  `_common/` ditambah `create-artifact/scripts/`), dijaga tes.

## Celah yang diterima

- Tanpa smoke test ke server sungguhan (keputusan user); tes memakai server MCP palsu `tests/nataflow_fake.py` yang
  meniru bentuk balikan `internal/adapters/primary/mcp/tools.go`.
- Sandbox atau izin jaringan Claude Code bisa memblokir `python3` ke `url`; galatnya terbaca sebagai `GAGAL: tidak
  dapat menghubungi <url>`.

## Titik gagal

Galat sesi, transport, atau tool di langkah mana pun → segmen `GAGAL: <pesan>` dan langkah sesudahnya tidak
dijalankan. Sinkron ulang aman: skrip selalu mencari task/dokumen lebih dulu, sehingga tidak membuat kembar.
