# Langkah 15 — Sinkron artefak plugin ke nataflow: kebutuhan tool MCP

Sumber: diskusi desain 2026-09-28, lanjutan `issues/14-sinkron-nataflow-analyst.md` bagian "Di luar cakupan"
(push artefak engineer yang menunggu `update_document`/`get_document`). Basis kode server: `nataflow-api`
`main` @ `cd75d2e`.

**Status (2026-09-28):** sisi server SELESAI. T1–T9 mendarat di `nataflow-api` `main` @ `3e19f78` lewat empat
rantai: `2609281245-mcp-artifact-sync` (T1–T6), `2609281546-artifact-sync-p2-fix` (perbaikan P2 review),
`2609281750-task-status-update` (T7), dan `2609281912-document-mcp-batch-delete` (T8, T9, serta T10 yang teruji
pada induk `workspace`). Status deploy belum tercatat. Sisi plugin dikerjakan di branch `feat/15-sinkron-artefak`
menurut `02-plugin-backend.md`, `03-plugin-frontend.md`, `04-plugin-analyst.md`, dan `05-plugin-quickdev.md`,
dengan keputusan dan protokol di § Pelaksanaan sisi plugin (akhir dokumen ini).

**Status sisi plugin (2026-09-28):** SELESAI di branch `feat/15-sinkron-artefak`, bertahap dengan peta blast radius
di tiap berkas plugin sebelum kode: pustaka bersama (tahap 1), `quickdev` (tahap 2, pilot prosedur), `backend`
(tahap 3), `frontend` (tahap 4), `analyst` (tahap 5), lalu rilis analyst 0.8.0, backend 0.11.0, frontend 0.10.0,
dan quickdev 0.6.0. Suite penuh 1934 hijau (Python 3.9: 1933 + 1 skip `tomllib`), lint `--base main` 0 FAIL,
`claude plugin validate .` lulus. Uji ujung ke ujung terhadap server nataflow yang ter-deploy belum dijalankan.

## Tujuan

Semua artefak yang dihasilkan plugin `analyst`, `backend`, `frontend`, dan `quickdev` ikut tersimpan di
database nataflow lewat server MCP `/mcp`, tanpa menggeser sumber kebenarannya. Disk dan git tetap sumber
kebenaran, dan nataflow hanya cermin, sama seperti sinkron tiket di langkah 14.

## Keputusan desain

| ID | Keputusan | Alasan |
|---|---|---|
| D1 | **Jangkar:** 1 taskdir = 1 **workdir**, dan workdir menunjuk ke 1 **task**. Task itu adalah task tiket analyst bila `TASK.md` membawa `ticket_source`; bila tidak, task baru dibuat dari `TASK.md`. Dokumen taskdir menempel ke workdir. Tiket analyst tetap berupa task, dan dokumennya menempel ke task. | Tabel `workdirs` sudah ada dengan slug unik per workspace, cocok dengan pola taskdir `<YYMMDDhhmm>-<slug>`. Satu tiket bisa melahirkan taskdir backend dan frontend; keduanya bernaung di task yang sama tanpa dokumennya bercampur. |
| D2 | **Waktu push: titik status.** Dokumen dikirim hanya saat stabil: `APPROVED`, brief `READY`/`DONE`/`BLOCKED`/`SUPERSEDED`, `REVIEW`, `REPORT`, rencana quickdev terkunci/tertutup. `DRAFT` tidak dikirim. | Lewat MCP, isi dokumen ditulis ulang model sebagai argumen tool. Satu taskdir nyata (`backenddev/docs/2609280913-task-mcp-metadata/`) berisi 10 berkas ±120 KB, jadi satu dorongan penuh memakan puluhan ribu token output. |
| D3 | **Versi: upsert satu baris per berkas**, dengan kunci `key` = path relatif terhadap jangkar. Riwayat tetap di git. | Idempoten: sinkron ulang tidak membuat baris kembar, dan status dokumen di DB selalu status terakhir. |
| D4 | **Eksekutor:** model memanggil tool MCP dengan argumen yang disusun skrip plugin (`sync-payload`), apa adanya. Kegagalan push tidak menahan rantai. | Warisan 14 K1/K4. Plugin tetap stdlib tanpa kode jaringan, dan layanan cermin yang mati tidak boleh membalik hubungan disk → DB. |
| D5 | **Sinkron tidak menulis berkas apa pun di repo.** | Segel lintas plugin sensitif terhadap isi berkas: `approved_seal` analyst, `Sidik:` commit approve frontend, `Tree-Hash` quickdev, dan kesegaran `REVIEW.md` backend. Karena itu `id` nataflow tidak disimpan di disk; identitas dicari ulang lewat `key`. |

## Kondisi server saat ini

Tool yang sudah terdaftar di `internal/adapters/primary/mcp/tools.go`:

| Tool | Letak | Relevansi |
|---|---|---|
| `check_health` | `tools.go:82-101` | Tidak dipakai sinkron |
| `get_project_info` | `tools.go:174-179` | Diagnosa config (key → project) |
| `list_workspace` | `tools.go:181-186` | Diagnosa `workspace_id` config |
| `list_member` | `tools.go:188-194` | Tidak dipakai sinkron |
| `create_document` | `tools.go:197-207` | Ada, tapi induk hanya `project`/`workspace`/`task` dan tanpa kunci identitas, sehingga push ulang membuat baris kembar |
| `list_document` | `tools.go:209-215` | Ada, tapi selalu mengembalikan `content` semua dokumen induk (`tools.go:627-631`), jadi terlalu mahal untuk sekadar mencari dokumen |
| `create_task` | `tools.go:222-232` | Dipakai: task untuk taskdir tanpa tiket |
| `list_task` | `tools.go:234-242` | Dipakai: mencari task tiket lewat saringan metadata `ticket_key` (containment) |
| `update_task` | `tools.go:244-253` | Dipakai analyst. Status, code, dan PIC sengaja tidak bisa diubah |

Celah terhadap tujuan:

- **G1 — workdir belum punya permukaan MCP.** Tabel `workdirs` hanya berisi `id`, `workspace_id`, `name`, dan
  `slug` (`migrations/000017_create_workdirs_table.up.sql`), tanpa tautan ke task, status, atau metadata.
  `WorkdirUseCase` hanya punya `List` (`internal/features/workdir/port.go`), dan `NewMCPAdapter` tidak menerima
  use case workdir (`internal/adapters/primary/mcp/server.go:23-30`).
- **G2 — dokumen tidak bisa menempel ke workdir.** `ReferenceTable.IsValid` hanya menerima `project`,
  `workspace`, dan `task` (`internal/features/document/domain.go`). `resolveScopedParent` juga hanya mengenal
  ketiganya (`internal/features/document/service.go`).
- **G3 — dokumen tidak punya identitas stabil maupun jalur ubah lewat MCP.** Tidak ada `update_document`,
  `get_document`, atau `delete_document`. `DocumentUseCase.Update`/`Delete` hanya dipakai jalur REST ber-JWT.
- **G4 — tidak ada pencarian dokumen yang murah.** Lihat `list_document` di atas.
- **G5 — status task tidak bisa diubah lewat MCP** (`update_task` `tools.go:246`).

## Kontrak identitas

Kontrak ini dipakai bersama oleh tool dan keempat plugin. Nilainya disusun skrip plugin, bukan dirangkai model.

| Unsur | Bentuk | Contoh |
|---|---|---|
| `repo` | `repo` di config sinkron bila diisi. Bila tidak, `git remote get-url origin` yang dinormalkan (tanpa skema, kredensial, dan `.git`). Bila tidak ada remote, nama direktori root repo | `github.com/nataflow/nataflow-api` |
| Kunci workdir | `<source>:<repo>:<path taskdir relatif root>`, dengan `source` ∈ `backenddev`, `frontenddev`, `quickdev` | `backenddev:github.com/nataflow/nataflow-api:backenddev/docs/2609280913-task-mcp-metadata` |
| Nama workdir | Basename taskdir. Untuk quickdev, nama berkas rencana tanpa `.md` | `2609280913-task-mcp-metadata` |
| Kunci dokumen | Path berkas relatif terhadap jangkarnya: relatif taskdir untuk workdir, nama berkas untuk dokumen tiket | `PRD.md`, `brief-04-task-update-for-scope.md` |
| Kunci task tiket | Metadata `{"source":"analyst","ticket_key":<ticketdir>}` dari langkah 14. Plugin engineer menurunkannya dari `ticket_source` di frontmatter `TASK.md` (dirname) | `analyst/tickets/2609231400-cicilan-pembayaran` |
| Kunci task tanpa tiket | Metadata `{"source":<source>,"workdir_key":<kunci workdir>}` | — |

**`type` dokumen** (server menerima huruf kecil `a-z` dengan titik di antara segmen tak kosong, ≤50 karakter —
lihat E11; nilainya ditetapkan plugin):

| `type` | Berkas | Plugin |
|---|---|---|
| `task` | `TASK.md` | backend, frontend |
| `brd`, `prd`, `rca`, `halt` | berkas senama | backend |
| `flow`, `ui`, `contract`, `review.plan` | `FLOW.md`, `UI.md`, `CONTRACT.md`, `REVIEW-PLAN.md` | frontend |
| `brief` | `brief-NN-<unit>.md` | backend, frontend |
| `unit.report` | `report-NN.md` | backend, frontend |
| `review`, `report` | berkas senama | backend, frontend |
| `quickdev.plan` | `plan/<task>.md` | quickdev |
| `ticket.review` | `review.md` tiket | analyst |
| `profile`, `audit`, `api.doc`, `adhoc.review` | profil, `backenddev/issues/`, `docs/api/`, `frontenddev/reviews/` | P2, lihat T10 |
| `doc` | cadangan untuk key remote yang tipenya kosong dan nama berkasnya tidak dikenali | backend, frontend |

**Metadata dokumen** (objek JSON, diganti utuh tiap upsert seperti `update_task`): `source`, `repo`, `path`
(relatif root repo), `status` (nilai frontmatter berkas: `APPROVED`, `READY`, `DONE`, dst.), `commit` (sha
terakhir yang menyentuh berkas; kosong bila belum ter-commit, mis. rencana quickdev), `removed` (hanya `true`
untuk berkas yang sudah dihapus dari git, mis. `HALT.md` yang dicabut).

## Daftar tool

Prioritas:

- **P0**: tanpa ini tidak ada satu plugin pun yang bisa menyimpan artefak engineer.
- **P1**: dibutuhkan agar sinkron lengkap, hemat token, dan bisa dipulihkan.
- **P2**: pelengkap atau opsional.

| # | Tool | Jenis | Prioritas | Dipakai plugin | Alasan singkat |
|---|---|---|---|---|---|
| T1 | Perluasan induk dokumen ke `workdir` | ubah domain + `create_document`/`list_document` | **P0** | backend, frontend, quickdev | Tanpa ini dokumen taskdir tidak punya tempat menempel (G2) |
| T2 | `upsert_workdir` | baru | **P0** | backend, frontend, quickdev | Membuat atau memperbarui jangkar taskdir secara idempoten, sekaligus menautkannya ke task (G1) |
| T3 | `upsert_document` | baru | **P0** | semua | Menyimpan satu berkas secara idempoten lewat `key`, dengan penjaga salin-ulang model (G3) |
| T4 | `list_document` ringan | ubah | P1 | semua | Manifest `key` + sha tanpa isi, supaya plugin hanya mendorong berkas yang berubah (G4) |
| T5 | `list_workdir` | baru | P1 | backend, frontend, quickdev | Pemulihan "sinkron ulang", dan melihat workdir saudara dalam satu task |
| T6 | `get_document` | baru | P1 | semua (baca balik) | Verifikasi, dan jalan baca lintas repo di masa depan (mis. frontend membaca `PRD.md` backend) |
| T7 | `update_task_status` | baru | P2 | backend, frontend, analyst, quickdev | Status task mengikuti rantai (G5). Di luar inti "simpan artefak" |
| T8 | `delete_document` | baru | P2 | backend, frontend | Menghapus cermin berkas yang dihapus dari git. Alternatif tanpa tool: metadata `removed: true` lewat T3 |
| T9 | `upsert_documents` (batch) | baru | P2 | backend, frontend | Mengurangi jumlah panggilan saat mendorong satu batch brief. Token tetap sama |
| T10 | Dokumen tingkat repo | pakai T3 | P2 | semua | Profil, laporan audit, `docs/api`, dan review ad-hoc menempel ke `workspace` dengan `key` ber-prefix `repo` |

Tool yang **dipakai apa adanya**: `list_task`, `create_task` (untuk taskdir tanpa tiket dan rencana quickdev),
`update_task` (analyst), `list_workspace`, dan `get_project_info` (diagnosa config).

### T1 [P0] Perluasan induk dokumen ke `workdir`

- **Ubah:** `ReferenceTableWorkdir = "workdir"` di `ReferenceTable.IsValid`. `resolveScopedParent` menerima cabang
  workdir: baca workdir, lalu `checkScopedWorkspace` atas `workdir.WorkspaceID`. `checkParentAccess` (jalur REST)
  menerima cabang yang sama lewat `WorkdirUseCase.GetByID` ber-cek akses. Deskripsi argumen `reference_table` di
  `create_document`/`list_document` menyebut `workdir`. `documentToolError` memetakan `core.ErrWorkdirNotFound`.
- **Kenapa:** keputusan D1. Kolom `reference_table` sudah `VARCHAR(100)` tanpa enum DB, sehingga tidak butuh
  migrasi untuk nilainya.

### T2 [P0] `upsert_workdir`

| Argumen | Wajib | Aturan |
|---|---|---|
| `key` | ya | Kunci workdir (lihat Kontrak identitas), ≤255 |
| `name` | ya | Basename taskdir. Slug diturunkan `GenerateSlug` seperti sekarang |
| `workspace_id` | tidak | Aturan `resolveToolWorkspace` (`tools.go:381-390`): key terkunci workspace memaksa nilainya, dan key ber-scope project mewajibkannya |
| `task_id` | tidak | UUID task dalam scope key. Kosong berarti tautan lama dipertahankan |
| `status` | tidak | `active` / `blocked` / `done` / `abandoned` |
| `metadata` | tidak | Teks JSON objek, diganti utuh: `source`, `repo`, `path`, `lane`, `chain`, `risk`, `stack` |

- **Perilaku:** cari berdasarkan `(workspace_id, key)`. Bila belum ada, buat workdir; bila sudah ada, perbarui
  `name`, `task_id`, `status`, dan `metadata`. Balikan berupa `workdirView` (`id`, `key`, `name`, `slug`,
  `task_id`, `status`, `metadata`, stempel waktu) ditambah `action: created | updated`.
- **Prasyarat backend:** migrasi `workdirs` menambah `key VARCHAR(255)` (unik per `workspace_id`), `task_id UUID
  NULL REFERENCES tasks(id) ON DELETE SET NULL`, `status VARCHAR(20)`, dan `metadata JSONB`.
  `WorkdirUseCase.UpsertForScope`. Parameter `workdirUseCase` di `NewMCPAdapter`/`RegisterScopedTools`, dan
  wiring di `cmd/server/main.go`.
- **Kenapa upsert, bukan pola `list → create/update` seperti tiket:** satu panggilan dan atomik, tanpa jendela
  kembar yang di langkah 14 harus dijaga lewat aturan "lebih dari 1 hasil → berhenti".
- **Diputuskan di PRD backend:** (a) apakah task boleh berada di workspace lain dalam project yang sama (tiket
  analyst dan taskdir frontend bisa hidup di workspace berbeda); (b) nasib constraint `uq_workdirs_workspace_slug`,
  karena dua repo dalam satu workspace bisa melahirkan basename taskdir yang sama. Saran: identitas pindah ke `key`,
  dan slug kembar diberi sufiks.

### T3 [P0] `upsert_document`

| Argumen | Wajib | Aturan |
|---|---|---|
| `reference_table` | ya | `project` / `workspace` / `task` / `workdir` |
| `reference_id` | ya | Id induk dalam scope key |
| `key` | ya | Kunci dokumen, ≤255 |
| `type` | ya | Lihat tabel `type` |
| `content` | ya | Isi berkas apa adanya |
| `content_sha256` | tidak (disarankan) | Sha256 hex isi yang dihitung skrip plugin. Bila tidak cocok dengan `content` yang diterima, server menolak tanpa menulis |
| `mimetype` | tidak | Default `text/markdown` |
| `metadata` | tidak | Teks JSON objek, diganti utuh |

- **Perilaku:** cari berdasarkan `(reference_table, reference_id, key)`. Bila belum ada, buat; bila sha isi dan
  metadata sama, jangan menulis (`action: unchanged`); selain itu `SetContent`. Balikan berupa `documentView`
  **tanpa `content`**, ditambah `key`, `content_sha256`, dan `action: created | updated | unchanged`.
- **Prasyarat backend:** migrasi `document` menambah `key VARCHAR(255) NULL`, index unik parsial `(reference_table,
  reference_id, key) WHERE key IS NOT NULL`, dan `content_sha256 CHAR(64)` (diisi ulang saat create/update, termasuk
  lewat REST). `DocumentUseCase.UpsertForScope`.
- **Kenapa `content_sha256` ada di P0:** model menyalin berkas 6–25 KB ke argumen tool. Salinan yang bergeser
  (terpotong, spasi berubah) ditolak server, bukan diam-diam menjadi cermin yang salah. Ini melengkapi larangan
  "kirim apa adanya" di langkah 14 dengan pemeriksaan mekanis.
- **Kenapa balikan tanpa isi:** balikan yang memuat isi menggandakan biaya token tiap push.

### T4 [P1] `list_document` ringan

- **Ubah:** argumen baru `include_content` (boolean, default `true` agar pemanggil lama tidak berubah), serta
  saringan `key`, `type`, dan `metadata` (containment seperti `list_task`). View menambah `key` dan `content_sha256`.
- **Kenapa:** alur hemat yang diinginkan adalah skrip plugin menerbitkan manifest, lalu model memanggil `list_document
  include_content=false` dan menyerahkan hasilnya ke skrip lewat stdin. Skrip kemudian hanya menerbitkan payload
  untuk berkas yang sha-nya berbeda. Sapuan di akhir rantai tanpa T4 berarti mendorong ulang seluruh taskdir.

### T5 [P1] `list_workdir`

- **Argumen:** `workspace_id` (aturan `lockToolWorkspace`), `task_id`, `key`, dan `metadata` (containment).
  Balikan berupa daftar `workdirView`.
- **Kenapa:** rute "sinkron ulang" dan diagnosa memerlukan cara melihat workdir yang sudah ada. Dengan saringan
  `task_id`, pemakai (dan kelak frontend nataflow) juga bisa melihat taskdir backend dan frontend yang bernaung di satu
  tiket. REST `GET /api/v1/workdirs` sudah ada (`internal/adapters/primary/http/router.go:134-136`), jadi aturan
  saringnya dicerminkan.

### T6 [P1] `get_document`

- **Argumen:** `document_id`, atau pasangan `reference_table` + `reference_id` + `key`. Balikan berupa
  `documentView` lengkap dengan `content`.
- **Kenapa:** membaca balik satu dokumen tanpa menarik isi seluruh induk. Ini juga membuka jalan konsumsi lintas repo
  (mis. gate CONTRACT frontend membaca `PRD.md` backend dari nataflow), meski konsumsi itu belum dijadwalkan.

### T7 [P2] `update_task_status`

- **Argumen:** `task_id`, `status` ∈ `todo` / `in_progress` / `done` / `cancelled`. Menulis `task_activity`
  seperti jalur REST pengubah status.
- **Pemakaian:** eksekusi mulai → `in_progress`, `REPORT` terkunci → `done`, taskdir `abandon` atau tiket `cancel`
  → `cancelled`.
- **Kenapa P2:** di luar permintaan "simpan artefak", dan status workdir (T2) sudah mencerminkan keadaan taskdir.
  Aturan bisnis status wajib dicerminkan dengan jalur REST (`backend/CLAUDE.md`, "REST and MCP paths mirror each
  other").

### T8 [P2] `delete_document`

- **Argumen:** `document_id`, atau pasangan induk + `key`.
- **Kenapa P2:** berkas yang dihapus dari git jarang terjadi (mis. `HALT.md` yang di-`git rm`). Cukup ditandai
  metadata `removed: true` lewat T3, tanpa tool baru.

### T9 [P2] `upsert_documents` (batch)

- **Argumen:** `reference_table`, `reference_id`, dan `documents` (larik objek T3, plafon mis. 10). Seluruh larik
  berjalan dalam satu transaksi.
- **Kenapa P2:** hanya mengurangi jumlah panggilan saat batch brief didorong, bukan token.

### T10 [P2] Dokumen tingkat repo

- **Tanpa tool baru:** T3 dengan `reference_table: workspace` dan `key` `<repo>/<path>` untuk profil
  `.claude/profile/<plugin>/`, `repo-profile.md`, `backenddev/issues/*.md`, `docs/api/*.md`, dan
  `frontenddev/reviews/*.md`.
- **Kenapa P2:** artefak ini tidak berada di taskdir dan tidak menjadi bagian rantai kerja satu task.

## Pola pemakaian tool oleh plugin

Keempat plugin memakai urutan panggilan yang sama. Berkas plugin hanya menyebut **kapan** urutan ini dijalankan
dan **berkas mana** yang dipilih.

1. Skrip plugin `sync-payload --json` menghasilkan `SKIP` (config absen), `FAIL` (config rusak atau artefak tidak
   sah), atau `PASS` berisi `mcp_server`, `task`, `workdir`, dan `documents`.
2. Muat tool `mcp__<mcp_server>__*` lewat ToolSearch. Bila tidak tersedia → `GAGAL`.
3. **Task:** `list_task` dengan `lookup` apa adanya. 0 hasil → `create_task`; 1 hasil → pakai `id`-nya; lebih dari
   1 → `GAGAL` tanpa menulis apa pun (aturan langkah 14).
4. **Workdir:** `upsert_workdir` dengan `task_id` dari langkah 3 → `id` workdir. Analyst melewati langkah ini.
5. **(P1, T4)** `list_document include_content=false`, lalu hasilnya diserahkan ke `sync-payload --remote -`, yang
   menyaring dokumen yang sha-nya sudah sama.
6. `upsert_document` per dokumen (atau T9), dengan argumen apa adanya termasuk `content_sha256`.
7. Satu segmen di baris penutup skill: `nataflow <workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s>
   sama) | dilewati | GAGAL: <sebab>>`. `GAGAL` tidak menahan rantai. Dorongan diulang lewat rute "sinkron ulang"
   di gerbang tiap plugin.

**Config bersama.** `.claude/nataflow.json` di repo user (ter-commit), berisi `mcp_server` (default
`nataflow-api`), `workspace_id`, `pic_id`, dan `repo` (opsional, menimpa turunan `git remote`). Berkas absen berarti
sinkron dilewati diam-diam; berkas ada tetapi rusak berarti `FAIL`. Analyst tetap menerima `analyst/nataflow.json`
lama (lihat A1 di `04-plugin-analyst.md`).

**Pustaka bersama.** `skills/_common/nataflow_sync.py` (stdlib) disalin identik ke keempat plugin. Isinya:
pembaca config, identitas repo, kunci workdir/dokumen, sha256, manifest, dan diff terhadap manifest remote.
Salinan identik ditagih test, mengikuti preseden `ticket_seal` (`tests/test_a1_ticket_source.py`) dan
`hooks/detect.py` backend/frontend. Plugin tidak bisa saling mengimpor karena dipasang terpisah.

## Prasyarat backend non-tool

| # | Bagian | Perubahan | Untuk |
|---|---|---|---|
| S1 | `migrations/` | Pasangan `.up/.down` baru: kolom `workdirs` (T2) dan kolom `document` `key` + `content_sha256` beserta index unik (T3) | T2, T3 |
| S2 | `internal/features/workdir/` | Domain (`key`, `task_id`, `status`, `metadata`, aturan validasi), repository `Upsert`/`GetByID`/saringan baru, dan `UpsertForScope`/`ListForScope`/`GetByID` di use case | T1, T2, T5 |
| S3 | `internal/features/document/` | `ReferenceTableWorkdir`, kolom `Key`/`ContentSHA256` di domain + model GORM, `UpsertForScope`, `GetForScope`, dan saringan `ListForScope` | T1, T3, T4, T6 |
| S4 | `internal/adapters/primary/mcp/` | Registrasi tool, view, dan pemetaan galat. Tanda tangan `NewMCPAdapter`/`RegisterScopedTools` bertambah parameter workdir, sehingga pemanggil positional di `server_test.go`/`tools_test.go` perlu disesuaikan | T1–T6 |
| S5 | Cermin REST | Handler dokumen REST menerima induk `workdir`, dan balikannya membawa `key`/`content_sha256`. Aturan workdir (validasi `task_id`, status) tinggal di service, sehingga REST dan MCP memakai aturan yang sama | T1, T3 |
| S6 | `cmd/server/main.go` | Workdir use case diteruskan ke adapter MCP, dan `documentService` menerima dependensi workdir | T1, T2 |
| S7 | Batas ukuran | Memastikan tidak ada batas body HTTP yang memotong isi puluhan KB. Saat ini tidak ada `MaxBytes` di router maupun adapter MCP; plafon `content` tetap diputuskan di PRD | T3, T9 |

## Urutan pengerjaan backend (saran)

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | S1, S2, S3 → T1, T2, T3 (+ S4, S5, S6) | Minimum agar backend/frontend/quickdev bisa mendorong artefak |
| 2 | T4, T5, T6 | Efisiensi token dan pemulihan. Plugin bisa jalan tanpa ini dengan mendorong per titik status |
| 3 | T7, T8, T9, T10 | Pelengkap |

Tahap 1 diperkirakan berisiko `MAJOR` (kontrak MCP baru, migrasi, field opsional baru), sehingga rantai backend
membutuhkan PRD.

Urutan sisi plugin sesudah tahap 1 mendarat: pustaka bersama + config → `backend` → `frontend` → `quickdev` →
`analyst`. Sinkron analyst sudah berjalan sejak langkah 14, dan perubahannya di sini hanya P1/P2.

## Risiko & catatan

- **Biaya token.** Tiap push = ukuran berkas sebagai token output. D2 dan T4 adalah dua rem utamanya. Tanpa T4,
  plugin harus memilih berkas per titik status secara ketat (lihat berkas plugin).
- **Kesetiaan salinan.** Tanpa `content_sha256` (T3), cermin bisa berbeda diam-diam dari disk.
- **`ticket_key` tidak memuat repo.** Tiket dengan path sama di dua repo akan bertabrakan saat dicari. Kemungkinannya
  kecil (timestamp menit + slug), dan aturan "lebih dari 1 hasil → GAGAL" tetap berlaku. Lihat A3 di
  `04-plugin-analyst.md`.
- **Konsumen UI.** `nataflow-frontend` belum punya layar workdir maupun dokumen per workdir. Itu kerja lintas repo
  terpisah dan tidak menahan sinkron.

## Di luar cakupan

- Tarik balik (DB → disk) dan penyuntingan dokumen dari UI nataflow. Arah sinkron hanya disk → DB.
- Pendaftaran server MCP dan penyimpanan key tetap tanggung jawab user (`claude mcp add …`).
- Artefak scratch yang tidak di-commit: `.explore/`, `.frontenddev/explore/`, laporan terminal explore/clarify
  quickdev.

## Pelaksanaan sisi plugin

### Selisih kontrak server terhadap dokumen ini

Dibaca dari PRD dan REPORT keempat rantai di atas serta `internal/adapters/primary/mcp/tools.go` @ `3e19f78`.

- **T2 (a) diputuskan:** task boleh berada di workspace lain dalam project yang sama bila MCP key ber-scope project.
  Key yang terkunci workspace menuntut task di workspace kunci. **(b):** constraint slug dipertahankan, slug kembar
  diberi sufiks `-2`, `-3`, dst., dan slug tidak berubah saat `name` diperbarui.
- **T3:** `content` yang absen ditolak (`content is required`), sedangkan `content: ""` sah. `metadata` kosong
  mempertahankan nilai lama. Sha yang tidak cocok ditolak (`content_sha256 does not match content`) sebelum database
  disentuh. `unchanged` bila sha, `type`, `mimetype`, dan metadata efektif sama (kesetaraan `jsonb`).
- **T4:** `list_document` membalikkan larik JSON `documentView` (`key`, `type`, `mimetype`, `content_sha256`,
  `metadata` sebagai objek), tanpa `content` bila `include_content=false`.
- **T9:** 1–10 dokumen, all-or-nothing. Review server mencatat risiko deadlock pada dua batch paralel dengan key
  beririsan (OPEN).
- **S7:** muatan 25 KB terbukti tiba utuh, dan tidak ada plafon `content`.
- Semua argumen `metadata` (task, workdir, dokumen) berupa **teks** JSON, sama dengan langkah 14.
- **`type` (E11):** sejak backend `d8bc1d6` (`document-type-format`) `type` wajib cocok `^[a-z]+(\.[a-z]+)*$`
  di `create_document`, `upsert_document`, dan `upsert_documents`; nilai lain ditolak `invalid input data`. Filter
  `type` `list_document` tetap kesamaan persis tanpa validasi.

### Keputusan pelaksanaan

| ID | Keputusan | Alasan |
|---|---|---|
| E1 | Item P2 ikut di langkah ini: B9, B10, F12, F13, Q10, Q11, A6 | Keputusan user. T7 dan T10 sudah tersedia di server |
| E2 | A5 tidak dikerjakan: `## Catatan Elisitasi` tetap tidak masuk DB | Keputusan user; 14 K5 tetap berlaku |
| E3 | Q6 opsi (a): laporan `review` quickdev tetap terminal saja | Keputusan user |
| E4 | Payload dua fase menggantikan `--point`. Panggilan pertama menerbitkan task, workdir, dan argumen manifest tanpa isi dokumen; `--remote -` menerbitkan isi hanya untuk dokumen yang berbeda dari manifest remote | `--point` hanya dibutuhkan "selama T4 belum ada" (B2). Semua titik panggil memakai satu perintah yang sama, tanpa daftar berkas per titik |
| E5 | `upsert_document` per dokumen, bukan `upsert_documents` | Batch bersifat all-or-nothing, sehingga satu salinan yang meleset menggagalkan semuanya. Risiko deadlock batch di server masih OPEN |
| E6 | Isi dokumen taskdir backend/frontend diambil dari blob `HEAD`, bukan working tree. Berkas yang belum pernah ter-commit tidak didorong. Quickdev dan analyst memakai isi disk. **Untuk dokumen taskdir digantikan Langkah 24 K14** (`issues/24-dokumen-taskdir-lepas-git.md`): dokumen taskdir tidak lagi di-commit, jadi isinya dibaca dari disk, kriteria stabil dinilai dari status dan materai, metadata `commit` kosong, dan `head` = `HEAD` saat sinkron. Dokumen tingkat repo tetap dari `HEAD` | D2: hanya yang stabil yang didorong, dan metadata `commit` selalu cocok dengan isinya. Quickdev tidak meng-commit, dan analyst boleh berjalan tanpa git |
| E7 | Dokumen yang pernah tercermin tetap dicerminkan. Key remote yang tidak lagi terpilih tetapi berkasnya masih ada di `HEAD` didorong dengan status terbarunya. Berkas yang sudah dihapus dari git didorong ulang dari versi terakhirnya dengan `removed: true`. T8 tidak dipakai. **Untuk dokumen taskdir digantikan Langkah 24 G5**: key remote yang berkasnya masih di disk tetap didorong dengan status terbarunya, tetapi berkas yang hilang dari disk tidak didorong dan barisnya dibiarkan dengan isi terakhir (tanpa riwayat git, versi terakhirnya tidak tersedia). `removed: true` tetap berlaku untuk dokumen tingkat repo | Satu aturan untuk F9 (hop yang dibuka ulang) dan B2 (`HALT.md` yang dicabut). Riwayat keberadaan dokumen tidak hilang dari cermin |
| E8 | Status task (T7) diturunkan skrip beserta syarat asalnya: `in_progress` hanya dari `todo`, sedangkan `done`/`cancelled` dari `todo`/`in_progress`. Plugin engineer hanya pernah menaikkan task tiket analyst ke `in_progress` | Satu task tiket bisa menaungi taskdir backend dan frontend, jadi satu taskdir selesai belum berarti tiket selesai. Status tidak pernah diturunkan dari `done`/`cancelled` |
| E9 | Task tiket yang belum ada di nataflow dibuat plugin engineer dengan metadata `{"source":"analyst","ticket_key":…,"repo":…}` | `lookup` analyst menemukan task itu (containment), lalu `update_task` analyst menimpa judul, deskripsi, dan metadatanya. Tidak ada task kembar |
| E10 | Dokumen tingkat repo (T10) memakai `workspace_id` config. Bila kosong, `list_workspace` harus mengembalikan tepat satu workspace | Key yang terkunci workspace tidak perlu `workspace_id` di config |
| E11 | Nilai `type` dokumen memakai format server: huruf kecil, `_` lama menjadi `.` (`UNIT_REPORT` → `unit.report`). `check_documents` menolak `type` di luar pola sebelum dikirim. `type` remote bergaya lama yang dipakai ulang untuk key tercermin (E7) dinormalkan lewat `remote_type`, sehingga baris lama diperbarui ke format baru pada sinkron berikutnya | Server menolak huruf besar dan `_` sejak `d8bc1d6`; pemetaan mekanis membuat nilai lama dan baru bisa diturunkan satu arah tanpa tabel |

### Protokol (menggantikan § Pola pemakaian tool)

**Taskdir dan rencana** (backend, frontend, quickdev):

1. `sync-payload … --json` → `SKIP` (config absen), `FAIL` (config rusak atau artefak tidak sah), atau `PASS` berisi
   `mcp_server`, `task` (`lookup`, `create`, `status`), `workdir`, `list_document`, dan `documents_total`, tanpa isi.
2. Muat tool `mcp__<mcp_server>__*` lewat ToolSearch. Ada yang tidak tersedia → `GAGAL`.
3. `list_task` dengan `task.lookup` apa adanya: 0 → `create_task` dengan `task.create`; 1 → pakai `id`-nya; lebih dari
   1 → `GAGAL` tanpa menulis apa pun.
4. `upsert_workdir` dengan argumen `workdir` ditambah `task_id` → `id` workdir.
5. `list_document` dengan argumen `list_document` ditambah `reference_id` = `id` workdir. Teks balikannya diserahkan
   apa adanya ke `sync-payload … --remote - --json` lewat stdin, yang menerbitkan `documents` (argumen
   `upsert_document` tanpa `reference_id`) beserta hitungan `same`.
6. `upsert_document` per dokumen dengan `reference_id` = `id` workdir.
7. `task.status` terisi dan status task dari langkah 3 termasuk `task.status.from` → `update_task_status`.
8. Satu segmen di baris penutup: `nataflow workdir <nama> · <n> dokumen (<c> baru, <u> diperbarui, <s> sama) |
   dilewati | GAGAL: <sebab>`.

**Dokumen tingkat repo** (`--repo-docs <jenis>`): langkah 1–2, lalu `reference_id` workspace dari payload (kosong →
`list_workspace`, tepat 1 hasil), kemudian langkah 5, 6, dan 8 dengan induk `workspace`. Segmen:
`nataflow repo · <n> dokumen (…)`.

**Analyst:** langkah 14 tetap berlaku, ditambah `upsert_document` untuk `review.md` di bawah task (A4) dan
`update_task_status cancelled` untuk tiket READY yang dibatalkan (A6).
