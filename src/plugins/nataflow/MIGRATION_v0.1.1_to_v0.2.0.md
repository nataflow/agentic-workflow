# Migrasi `nataflow` v0.1.1 → v0.2.0

Langkah 29: sinkron nataflow pindah dari tool MCP yang dipanggil model ke skrip Python yang memanggil server
sendiri. Isi dokumen tidak lagi lewat konteks model, sehingga sinkron jauh lebih hemat token.

## Yang berubah

- Skrip plugin ini — `artifact.py config | list | pull | publish` — membuka sesi MCP Streamable HTTP sendiri (`python3` stdlib) dan mencetak satu
  baris segmen. Server MCP nataflow yang terdaftar di Claude Code tidak lagi dipakai plugin ini (boleh tetap
  terdaftar untuk keperluan lain).
- `.claude/nataflow.json`: field `mcp_server` **dihapus** dan diganti `url` endpoint MCP yang **wajib** diisi.
  Config yang masih memuat `mcp_server`, atau belum memuat `url`, langsung `GAGAL` dengan pesan migrasi.
- MCP key pindah ke `.claude/nataflow.local.json` (`{"mcp_key": "<key>"}`). Di repo git berkas ini wajib
  diabaikan git: berkas absen, tidak diabaikan, atau sudah ter-track → `GAGAL` sebelum satu panggilan server pun.
  Root non-git (mis. folder multi-repo) tidak dicek ignore.
- Tidak ada fallback: tidak ada env var, dan konfigurasi MCP Claude Code (`~/.claude.json`) tidak dibaca.
- Tanpa `.claude/nataflow.json`, `create-artifact` kini `GAGAL` dengan petunjuk setup (dulu memakai server default `nataflow-api` di Claude Code): artifact selalu butuh `url` dan key.
- `artifact.py` mendapat subperintah `list`, `pull`, dan `publish`; model tidak lagi memuat tool `mcp__…` lewat ToolSearch.

## Langkah migrasi per repo

1. Ubah `.claude/nataflow.json`: hapus `mcp_server`, tambahkan `url`.

   ```json
   {
     "url": "https://api.flow.natakode.id/mcp",
     "workspaces": {"utama": "<uuid workspace>"}
   }
   ```

   `url` wajib `https://` (http hanya untuk `localhost`/`127.0.0.1`), berakhir di path `/mcp`, dan tanpa
   kredensial. Field `workspaces`, `pic_id`, dan `repo` tidak berubah.
2. Buat `.claude/nataflow.local.json` berisi MCP key yang sama dengan yang dulu dipasang di header
   `Authorization` server MCP Claude Code, tanpa awalan `Bearer `:

   ```json
   {"mcp_key": "<MCP key nataflow>"}
   ```

3. Tambahkan baris berikut ke `.gitignore` root repo (lewati untuk root non-git):

   ```
   .claude/nataflow.local.json
   ```

4. Commit `.claude/nataflow.json` dan `.gitignore` saja. Jangan pernah meng-commit `.claude/nataflow.local.json`;
   bila terlanjur ter-track, keluarkan dengan `git rm --cached .claude/nataflow.local.json` dan rotasi key-nya.
5. Verifikasi: Jalankan `/nataflow:create-artifact`; Fase 0 (`artifact.py config`) langsung memvonis setup-nya. Segmen `GAGAL` menyebut langkah yang belum beres.

## Repo terdampak yang diketahui saat rilis

Semua repo di bawah memakai `.claude/nataflow.json` lama. Tanpa migrasi, sinkron (dan `create-artifact`) di
repo itu `GAGAL` begitu plugin versi ini terpasang.

| Repo | Isi config sekarang | Git | Tindakan |
|---|---|---|---|
| `hkm/wms` | `mcp_server` | bukan repo git (root multi-repo) | langkah 1–2; langkah 3–4 tidak berlaku |
| `hkm/orderhub/oms-api` | `mcp_server`, `workspaces` | config tidak ter-track | langkah 1–3 |
| `hkm/orderhub/oms-app` | `workspaces` | config tidak ter-track | langkah 1–3 (hanya tambah `url`) |
| `hkm/wms/wms-dashboard` | `mcp_server`, `workspaces` | config ter-track | langkah 1–4, commit di repo itu |
| `hkm/wms/wms-api` | `mcp_server`, `workspaces` | config tidak ter-track | langkah 1–3 |
| `hkm/wms/wms-rust` | `mcp_server`, `workspaces` | config ter-track | langkah 1–4, commit di repo itu |
