# Prosedur Sinkron Notulen ke nataflow

Dimuat `analyst:notulen` Phase 6 sesudah `notulen.py final` menulis `FINAL`, dan pada rute sinkron ulang di Phase 0. Hasilnya tepat satu segmen baris penutup: `nataflow <dibuat | diperbarui | tidak berubah | dilewati | GAGAL: <sebab>>`.

`NOTULEN.md` di disk tetap sumber kebenaran. Dokumen nataflow hanya cermin notulennya. Karena `analyst/notulen/` selalu diabaikan git, cermin inilah satu-satunya salinan notulen di luar disk lokal. Prosedur ini tidak pernah menulis `NOTULEN.md`, tidak pernah menurunkan `FINAL`, dan kegagalannya tidak membatalkan notulen.

Dokumen menempel ke **project** milik MCP key (`reference_table: project`) dengan `type` `notes.meeting`. Identitasnya metadata `notulen_key` = path notulendir. Judul dokumen (`<H1> — <tanggal rapat>`) dikunci saat dokumen pertama dibuat. Server menurunkan key dokumen dari slug judul itu, jadi mengganti H1 sesudahnya tidak mengganti judul di nataflow.


## Langkah

Jalankan `python3 <notulen.py> sync-payload --notulendir <notulendir> --push` — `<notulen.py>` adalah path skrip dari Precondition skill.

Skrip membaca config dan MCP key, lalu memanggil sendiri tool server nataflow: `get_project_info` (key wajib menjangkau tepat satu project; id-nya tidak pernah ditebak), cari dokumen lewat `notulen_key`, lalu `create_document` (belum ada), `upsert_document` ke key dokumen itu (isi berbeda), atau tidak menulis apa pun (sha sama). Isi notulen tidak pernah lewat konteks model.

Keluarannya tepat satu baris, yang disalin apa adanya sebagai segmen:

- `nataflow dibuat`, `nataflow diperbarui`, atau `nataflow tidak berubah` → selesai.
- `nataflow dilewati` (`.claude/nataflow.json` maupun `analyst/nataflow.json` tidak ada) → selesai.
- `nataflow GAGAL: <sebab>` → selesai. Sebab setup (`.claude/nataflow.local.json` tidak ada, `url` belum diisi, atau `mcp_server` lama) disampaikan ke user apa adanya bersama bagian Prasyarat di bawah. Dokumen kembar (`<n> dokumen ber-notulen_key sama`) berhenti sebelum tulisan apa pun. Galat karena judul bentrok dengan dokumen lain di project yang sama dilaporkan apa adanya; user yang memutuskan judul baru (sunting H1, `final` ulang, lalu sinkron ulang).

## Larangan

- Dilarang memanggil tool MCP nataflow (`mcp__…`) sendiri untuk sinkron ini, menyusun argumen tool, atau menyalin isi dokumen ke chat: `--push` satu-satunya jalur.
- Dilarang mengulang `--push` di giliran yang sama sesudah `GAGAL`; sinkron diulang lewat rute sinkron ulang. Pengulangan aman: skrip selalu mencari lebih dulu, dan tulisan yang gagal tidak pernah diulang otomatis.
- Dilarang membaca, mencetak, atau menyunting `.claude/nataflow.local.json`.
- Dilarang mengganti judul sendiri saat slug bentrok.
- Dilarang menulis ke `NOTULEN.md` atau menjalankan subperintah `notulen.py` lain sebagai bagian prosedur ini.
- `GAGAL` tidak menurunkan `FINAL`. Sinkron diulang lewat `/analyst:notulen` ("sinkron ulang notulen `<notulendir>`").

## Prasyarat di luar plugin

- `.claude/nataflow.json` di root repo (atau root ruang kerja non-git) mengaktifkan sinkron, sama dengan config sinkron tiket (`../../spec/references/nataflow-sync.md` bagian Prasyarat). Notulen hanya memakai `url` dan `repo`; `workspaces` dan `pic_id` tidak berlaku karena induknya project.
- MCP key di `.claude/nataflow.local.json` terikat ke satu project, dengan aturan berkas yang sama dengan sinkron tiket (wajib diabaikan git di dalam repo).
