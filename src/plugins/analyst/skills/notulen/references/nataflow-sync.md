# Prosedur Sinkron Notulen ke nataflow

Dimuat `analyst:notulen` Phase 6 sesudah `notulen.py final` menulis `FINAL`, dan pada rute sinkron ulang di Phase 0. Hasilnya tepat satu segmen baris penutup: `nataflow <dibuat | diperbarui | tidak berubah | dilewati | GAGAL: <sebab>>`.

`NOTULEN.md` di disk tetap sumber kebenaran. Dokumen nataflow hanya cermin notulennya. Karena `analyst/notulen/` selalu diabaikan git, cermin inilah satu-satunya salinan notulen di luar disk lokal. Prosedur ini tidak pernah menulis `NOTULEN.md`, tidak pernah menurunkan `FINAL`, dan kegagalannya tidak membatalkan notulen.

Dokumen menempel ke **project** milik MCP key (`reference_table: project`) dengan `type` `notes.meeting`. Identitasnya metadata `notulen_key` = path notulendir. Judul dokumen (`<H1> — <tanggal rapat>`) dikunci saat dokumen pertama dibuat. Server menurunkan key dokumen dari slug judul itu, jadi mengganti H1 sesudahnya tidak mengganti judul di nataflow.

## Langkah

1. **Payload.** `python3 <notulen.py> sync-payload --notulendir <notulendir> --json`. `<notulen.py>` adalah path skrip dari Precondition skill. Baca field `status`:
   - `SKIP` (`.claude/nataflow.json` maupun `analyst/nataflow.json` tidak ada) → segmen `nataflow dilewati`; selesai.
   - `FAIL` → segmen `nataflow GAGAL: <isi problems apa adanya>`; selesai.
   - `PASS` → pegang `mcp_server`, `lookup`, `create`, dan `update` apa adanya.
2. **Tool.** Tool yang dipakai bernama `mcp__<mcp_server>__get_project_info`, `…__list_document`, `…__create_document`, dan `…__upsert_document`. Yang masih tertunda dimuat lebih dulu lewat ToolSearch (`select:` semuanya). Salah satu tidak tersedia → segmen `nataflow GAGAL: server MCP <mcp_server> tidak tersedia`; selesai.
3. **Project.** `get_project_info` tanpa argumen. `id` balikannya adalah `reference_id` untuk langkah berikutnya. Galat (key tanpa project, key kedaluwarsa) → segmen `nataflow GAGAL: <pesan tool apa adanya>`; selesai. Id project tidak boleh ditebak.
4. **Cari dokumen.** `list_document` dengan argumen `lookup` apa adanya ditambah `reference_id`. Hitung dokumen di hasilnya:
   - 0 → `create_document` dengan argumen `create` apa adanya ditambah `reference_id`.
   - 1 → bandingkan `content_sha256` dokumen itu dengan `update.content_sha256`. Sama → segmen `nataflow tidak berubah`; selesai. Berbeda → `upsert_document` dengan argumen `update` apa adanya ditambah `reference_id` dan `key` = `key` dokumen itu.
   - Lebih dari 1 → jangan memanggil tool tulis apa pun; segmen `nataflow GAGAL: <n> dokumen ber-notulen_key sama (<key tiap dokumen>)`; selesai.
5. **Hasil.** `create_document` sukses → `nataflow dibuat`. `upsert_document` sukses → `nataflow diperbarui`. Galat tool → `nataflow GAGAL: <pesan tool apa adanya>`. Galat karena judul bentrok dengan dokumen lain di project yang sama dilaporkan apa adanya; user yang memutuskan judul baru (sunting H1, `final` ulang, lalu sinkron ulang).

## Larangan

- Dilarang menyusun, menyunting, meringkas, atau menerjemahkan nilai argumen di luar keluaran `sync-payload`. Satu-satunya nilai dari balikan tool adalah `reference_id` dan `key`. `metadata` dikirim sebagai teks JSON persis seperti tercetak.
- Dilarang memakai `reference_table` selain `project`, atau `reference_id` selain `id` dari `get_project_info`.
- Dilarang mengganti judul sendiri saat slug bentrok.
- Dilarang mengulang `create_document` sesudah galat tanpa `list_document` ulang. Tulisan yang ternyata sampai di server membuat dokumen kembar.
- Dilarang mengirim `## Catatan Asli` atau frontmatter notulen. Yang tercermin hanya isi `create.content`/`update.content`.
- Dilarang menulis ke `NOTULEN.md` atau menjalankan subperintah `notulen.py` lain sebagai bagian prosedur ini.
- `GAGAL` tidak menurunkan `FINAL`. Sinkron diulang lewat `/analyst:notulen` ("sinkron ulang notulen `<notulendir>`").

## Prasyarat di luar plugin

- Server MCP nataflow terdaftar di Claude Code user beserta MCP key yang terikat ke satu project. Plugin tidak mendeklarasikan server dan tidak menyimpan key.
- `.claude/nataflow.json` di root repo mengaktifkan sinkron, sama dengan config sinkron tiket (`../../spec/references/nataflow-sync.md` bagian Prasyarat). Notulen hanya memakai `mcp_server` dan `repo`; `workspaces` dan `pic_id` tidak berlaku karena induknya project.
