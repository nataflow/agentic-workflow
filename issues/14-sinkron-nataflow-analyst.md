# Langkah 14 — Sinkron tiket analyst ke nataflow (N1–N7)

Sumber: diskusi desain 2026-09-28. Kontrak sisi server dirancang di repo `nataflow-api`, branch
`feat/task-mcp-metadata`: `backenddev/docs/2609280913-task-mcp-metadata/PRD.md` (APPROVED `e090e9d`) beserta
6 brief READY (`e3e12ac`). Basis kode plugin: commit `a4cede4`.

**Status (2026-09-28):** N1–N7 selesai. Test regresi di `tests/analyst/test_ticket_14.py` (21 test: N1, N2, N5)
ditambah dua kasus smoke. Suite penuh 1816 test hijau, subset analyst hijau di Python 3.9, dan lint `--base HEAD`
0 FAIL. Sisi server sudah diimplementasikan di `nataflow-api` branch `feat/task-mcp-metadata` (6 brief DONE,
`1b76b97`), tetapi belum di-merge dan belum di-deploy. Versi: analyst 0.7.0.

Selisih pelaksanaan terhadap Kontrak di bawah:

- Keluaran `--json` selalu memuat `status` (`PASS`/`SKIP`/`FAIL`). `FAIL` berbentuk
  `{"status":"FAIL","enabled":true,"problems":[…]}`, supaya `--json` tetap JSON pada jalur gagal (smoke).
- Segmen `nataflow …` di baris `SPEC — READY` ditempatkan sesudah segmen commit, sebelum `— serahkan ke engineer`.
- `approved_seal` di metadata dihitung ulang dari isi (`ticket_seal`). Nilainya sama dengan field tertulis karena
  gerbang `READY` menolak segel yang berbeda, dan tiket lama tanpa field itu tetap mendapat nilai.
- Smoke keadaan `rusak` ikut merusak `analyst/nataflow.json`, sehingga jalur `FAIL` teruji di keempat keadaan
  repo, bukan hanya jalur `SKIP`.

## Tujuan

Tiket yang di-approve (`ticket.py approve` → `READY`) tercermin sebagai task di nataflow tanpa menggeser
sumber kebenarannya: `TICKET.md` di disk dan git tetap satu-satunya kebenaran, dan nataflow hanya cermin.

1. Approve pertama membuat task (`create_task`); approve ulang sesudah `reopen` memperbarui task yang sama
   (`update_task`), bukan membuat task baru.
2. Isi yang dikirim ditentukan skrip, bukan dirangkai model: judul, kartu, dan metadata penanda tiket
   dihasilkan `ticket.py sync-payload` secara deterministik.
3. Sinkron bersifat opt-in per repo dan tidak pernah menggagalkan approve. Kegagalan push dilaporkan dan
   dapat diulang, sementara tiket tetap `READY`.

## Prasyarat lintas repo

- Rantai `feat/task-mcp-metadata` di `nataflow-api` sudah mendarat dan ter-deploy. Plugin bergantung pada
  tiga permukaan MCP berikut, sesuai PRD tersebut:
  - `create_task` dengan argumen `metadata` (teks JSON objek);
  - `list_task` dengan argumen `metadata` (containment `@>`);
  - `update_task` (`task_id` wajib; `title`/`description`/`metadata` parsial; metadata diganti utuh).
- User sudah mendaftarkan server MCP nataflow di Claude Code, lengkap dengan MCP key, di luar plugin ini.
  Plugin tidak mendeklarasikan `mcpServers` dan tidak pernah menyimpan key.

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perubahan + test → suite penuh hijau → lint.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | N1 (config), N2 (`sync-payload`) | Kontrak mesin lebih dulu; prosa skill di tahap 2 berdiri di atas keluaran skrip. |
| 2 | N3 (prosedur sinkron + `spec` Phase 5), N4 (pemulihan lewat `intake`) | Menyambungkan skrip ke alur model. |
| 3 | N5 (test idempotensi reopen), N6 (smoke + lint) | Mengunci perilaku lintas siklus tiket. |
| 4 | N7 (dokumen + versi) | README, `flow/analyst.md`, `plugin.json` 0.7.0. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang sudah ada
dan harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| N1 | `skills/_common/analyst_lib.py` (`load_sync_config` baru) | `ticket.py sync-payload` | tidak | — | Nihil: fungsi baru, tanpa pemanggil lama. |
| N2 | `skills/_common/ticket.py` (`cmd_sync_payload`, parser subperintah) | `analyst:spec` Phase 5, `analyst:intake` pemulihan | tidak — `ticket_seal`, `SEAL_FIELDS`, `CONTENT_FIELDS` tidak disentuh, sehingga salinan segel di `precondition_lib` backend/frontend tetap identik | `tests/test_smoke.py` (`CASES` bertambah) | Rendah: subperintah baru, read-only, tanpa commit. |
| N3 | `skills/spec/SKILL.md` (Phase 5 langkah 5.4, Output, Failure path), `skills/spec/references/nataflow-sync.md` (baru) | model | tidak | `tests/test_lint_plugins.py` (R-check rujukan) | Sedang: baris penutup `SPEC — READY` bertambah satu segmen yang dibaca manusia, bukan skrip. |
| N4 | `skills/intake/SKILL.md` (rute pemulihan sinkron) | model | tidak | `tests/test_lint_plugins.py` | Rendah |
| N5 | — (test saja) | — | tidak | — | Nihil |
| N6 | `tests/test_smoke.py` | CI | tidak | `test_smoke.py` | Rendah: `--json` wajib valid di empat keadaan repo. |
| N7 | `README.md`, `flow/analyst.md`, `.claude-plugin/plugin.json` | manusia, lint M7 | tidak | `test_lint_plugins.py` | Nihil |

`ticket.py approve`, `ref`, `reopen`, `revise`, `cancel`, kedua validator, dan penerima `ticket_source`
backend/frontend **tidak diubah**. Sinkron berjalan sesudah approve selesai dan tidak menulis ke `TICKET.md`.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Eksekutor:** model memanggil tool MCP nataflow, dengan isi payload diambil verbatim dari `ticket.py sync-payload --json`. Plugin tidak memuat kode jaringan. | Tidak ada preseden jaringan maupun env di `src/plugins/**`, dan plugin wajib stdlib. Skrip tetap menjadi gerbang atas *isi*; model hanya mengirim. |
| K2 | **Identitas:** metadata task memuat `ticket_key` = path ticketdir relatif root (mis. `analyst/tickets/2609231400-cicilan-pembayaran`). Approve ulang memakai `list_task` dengan saringan `{"source":"analyst","ticket_key":…}`: 0 hasil → `create_task`, 1 hasil → `update_task`, lebih dari 1 → berhenti dan laporkan tanpa menulis. Tidak ada tulisan balik ke `TICKET.md`. | Slug bukan identitas: `new` membuat ticketdir baru bertimestamp baru dengan slug sama begitu tiket lama `READY`/batal (`ticket.py:294-304`). `external_ref` tetap milik kunci Jira/Trello dan semantik segel tidak disentuh. |
| K3 | **Opt-in:** berkas `analyst/nataflow.json` di repo user (ter-commit). Absen → sinkron dilewati diam-diam. Ada tetapi rusak → `FAIL` keras. | Deterministik dan terbaca skrip, mengikuti preseden config lokal repo (`.claude/profile/…/index.json`, `.claude/workflow`). Repo yang tidak memakai nataflow tidak terdampak sama sekali. |
| K4 | **Kegagalan push tidak memblokir.** Approve sudah ter-commit sebelum push; kegagalan (tool tidak tersedia, server mati, tool error) dilaporkan di baris penutup, dan sinkron dapat diulang lewat `/analyst:intake`. | Disk dan git sumber kebenaran; menahan `READY` karena layanan cermin mati membalik hubungan itu. |
| K5 | **Isi task:** `title` = H1 kartu; `description` = kartu utuh (H1 sampai akhir `## Lampiran`, via `split_parts(...)[0]`), tanpa `## Catatan Elisitasi`. Status task tidak pernah dikirim. | Selaras README ("hanya kartu yang disalin ke tracker") dan PRD backend (push tidak menyentuh status). |
| K6 | **`update_task` mengirim `title`, `description`, dan `metadata` penuh**; metadata diganti utuh di server. | PRD backend: metadata diganti utuh (tanpa merge); disk sumber kebenaran, jadi objek lengkap selalu dikirim ulang. |

## Kontrak

### `analyst/nataflow.json`

```json
{
  "mcp_server": "nataflow-api",
  "workspace_id": "a3e1d6c4-1f2b-4c3d-9e8f-7a6b5c4d3e2f",
  "pic_id": "c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f"
}
```

| Field | Wajib | Aturan |
|---|---|---|
| `mcp_server` | tidak | nama server MCP di konfigurasi Claude Code user; default `nataflow-api`. Dipakai model untuk mengenali tool `mcp__<mcp_server>__*`. |
| `workspace_id` | tidak | UUID; diteruskan ke `create_task` dan `list_task`. Wajib diisi bila MCP key user ber-scope project (server menolak `create_task` tanpa `workspace_id` dengan `workspace_id is required for project-scoped key`). |
| `pic_id` | tidak | UUID; diteruskan ke `create_task`. Kosong → server memakai pemilik key. |

Berkas harus berupa objek JSON. Kunci di luar tabel, nilai yang bukan string, atau UUID yang tidak valid
menghasilkan `FAIL`.

### `ticket.py sync-payload --ticketdir <td> [--json]`

Read-only, tanpa commit. Exit: 0 = `PASS` atau `SKIP`, 1 = `FAIL`.

- `SKIP` — `analyst/nataflow.json` tidak ada. JSON: `{"enabled": false}`.
- `FAIL` — config rusak; `TICKET.md` tidak ada; `status` bukan `READY`; `classify` bukan `READY` (mis.
  `DRIFT`/`RUSAK`); atau kartu tanpa H1.
- `PASS` — JSON berbentuk:

```json
{
  "enabled": true,
  "mcp_server": "nataflow-api",
  "ticket_key": "analyst/tickets/2609231400-cicilan-pembayaran",
  "lookup": {
    "workspace_id": "a3e1d6c4-1f2b-4c3d-9e8f-7a6b5c4d3e2f",
    "metadata": "{\"source\":\"analyst\",\"ticket_key\":\"analyst/tickets/2609231400-cicilan-pembayaran\"}"
  },
  "create": {
    "title": "Cicilan pembayaran untuk pelanggan korporat",
    "description": "# Cicilan pembayaran untuk pelanggan korporat\n\n## Latar Belakang\n…\n## Lampiran\n…",
    "workspace_id": "a3e1d6c4-1f2b-4c3d-9e8f-7a6b5c4d3e2f",
    "pic_id": "c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f",
    "metadata": "{\"source\":\"analyst\",\"ticket_key\":\"analyst/tickets/2609231400-cicilan-pembayaran\",\"slug\":\"cicilan-pembayaran\",\"type\":\"FEATURE\",\"priority\":\"HIGH\",\"approved\":\"2026-09-28\",\"approved_seal\":\"3f9a1c…\",\"reopened\":0}"
  },
  "update": {
    "title": "Cicilan pembayaran untuk pelanggan korporat",
    "description": "…",
    "metadata": "{…sama dengan create.metadata…}"
  }
}
```

- `metadata` selalu dikirim sebagai **teks** JSON objek, karena ketiga tool menerimanya sebagai string.
- Kunci metadata: `source` (selalu `analyst`), `ticket_key`, `slug`, `type`, `priority`, `approved`,
  `approved_seal`, `reopened` (0 bila absen), dan `external_ref` hanya bila bukan `-`. `requester` sengaja
  tidak dikirim: nama peminta tetap di disk.
- Kunci yang nilainya kosong di config (`workspace_id`, `pic_id`) dihilangkan dari `lookup`/`create`.

### Baris penutup `analyst:spec`

Segmen baru ditambahkan di akhir baris `SPEC — READY …`:
`· nataflow <dibuat #<code> | diperbarui #<code> | dilewati | GAGAL: <pesan tool apa adanya>>`.

---

## N1 [Tinggi] Config sinkron belum ada
- [x] Selesai

Tidak ada tempat menyatakan bahwa repo memakai nataflow maupun workspace tujuannya. **Perubahan:**
`analyst_lib.load_sync_config(root) -> (config | None, problems)` membaca `analyst/nataflow.json` (letaknya
sejajar `TICKETS_DIR`), memvalidasi skema tabel Kontrak, dan mengembalikan `None` bila berkas tidak ada.
UUID divalidasi dengan pola stdlib (`re`), tanpa impor pihak ketiga. **Test:** absen → `None`; JSON rusak,
bukan objek, kunci asing, nilai non-string, dan UUID tidak valid → masalah terlapor; `mcp_server` default
`nataflow-api`.

## N2 [Tinggi] Payload push dirangkai model
- [x] Selesai

Tanpa skrip, model menyusun judul, deskripsi, dan metadata sendiri, sehingga isinya bisa bergeser dari kartu
yang di-approve. **Perubahan:** subperintah `ticket.py sync-payload` sesuai Kontrak. Deskripsi diambil dari
`split_parts(split_frontmatter(text)[1])[0]`; judul dari `title_of()`; gerbang `READY` memakai `classify()`
yang sama dengan `ref`. `metadata` dirangkai dengan `json.dumps(..., separators=(",", ":"),
ensure_ascii=False)` agar byte-stabil. **Test:** `SKIP` tanpa config; `FAIL` untuk config rusak, `DRAFT`,
`DRIFT`, `CANCELLED`, dan ticketdir kosong; `PASS` untuk `description` sama persis dengan kartu (tanpa
`## Catatan Elisitasi`), `title` sama dengan H1, `metadata` ter-parse sebagai objek berkunci persis Kontrak,
`lookup.metadata` hanya `source` + `ticket_key`, `external_ref` ikut hanya bila bukan `-`, dan keluaran
identik pada dua pemanggilan berturut-turut.

## N3 [Tinggi] Tidak ada langkah push di `spec`
- [x] Selesai

`skills/spec/SKILL.md:71` (approve) langsung disusul baris penutup `:93`. **Perubahan:**

1. Referensi baru `skills/spec/references/nataflow-sync.md` memuat prosedur sinkron, dipakai `spec` maupun
   `intake`:
   1. `ticket.py sync-payload --ticketdir <td> --json`. `enabled: false` → segmen `nataflow dilewati`, selesai.
      `FAIL` → segmen `nataflow GAGAL: <baris FAIL>`, selesai.
   2. Pastikan tool `mcp__<mcp_server>__list_task`, `create_task`, dan `update_task` tersedia (muat lewat
      ToolSearch bila tertunda). Tidak tersedia → `GAGAL: server MCP <mcp_server> tidak tersedia`.
   3. `list_task` dengan argumen `lookup` apa adanya. Hasil 0 → `create_task` dengan argumen `create` apa
      adanya. Hasil 1 → `update_task` dengan `task_id` = `id` hasil itu ditambah argumen `update` apa adanya.
      Hasil lebih dari 1 → jangan menulis; segmen `GAGAL: <n> task ber-ticket_key sama (<code…>)`.
   4. Tool error → segmen `GAGAL: <pesan tool apa adanya>`. Sukses → `dibuat #<code>` / `diperbarui #<code>`.
   5. **Dilarang** menyusun atau menyunting nilai argumen di luar keluaran skrip, mengirim `status`, maupun
      mengulang `create_task` sesudah tool error tanpa `list_task` ulang.
2. `spec` Phase 5 langkah 5.4 memuat referensi itu tepat sesudah `approve` PASS, termasuk exit 3 (READY
   tertulis, commit gagal), sebelum baris penutup. `approve` FAIL → langkah ini tidak berjalan.
3. Output dan Failure path `spec` menyebut segmen baru dan menegaskan bahwa `GAGAL` tidak menurunkan
   `READY`.

**Test:** lint R-check atas rujukan `references/nataflow-sync.md`; tidak ada test perilaku model.

## N4 [Sedang] Push yang gagal tidak punya jalan ulang
- [x] Selesai

Server mati saat approve berarti tiket `READY` tanpa task, dan `spec` menolak tiket `READY` kecuali lewat
`reopen`. **Perubahan:** `analyst:intake` menambah rute "sinkron ulang tiket `<ticketdir>`" untuk tiket
berkeadaan `READY` (bukan `DRIFT`): jalankan prosedur `nataflow-sync.md` apa adanya tanpa `reopen`, lalu
tutup dengan baris `SINKRON — <ticketdir> · nataflow <…>`. Tiket `DRIFT` tetap dirutekan ke `spec` (reopen)
seperti sekarang. **Test:** lint R-check.

## N5 [Sedang] Idempotensi lintas `reopen` tidak terkunci test
- [x] Selesai

Keputusan K2 bergantung pada `ticket_key` yang stabil sepanjang `approve → reopen → review → approve`.
**Test (tanpa perubahan kode):** siklus penuh memakai `ticket_review`; `ticket_key` dan `lookup` identik di
kedua `sync-payload`, sedangkan `approved_seal` dan `reopened` berubah. Tiket baru ber-slug sama sesudah yang
lama `READY` menghasilkan `ticket_key` berbeda.

## N6 [Rendah] Smoke dan lint untuk CLI baru
- [x] Selesai

`tests/test_smoke.py` hanya memuat `ticket.py state`. **Perubahan:** tambah
`("analyst/skills/_common/ticket.py", ["sync-payload", "--ticketdir", AN_TD, "--json"], …)` ke `CASES`, agar
`--json` tetap valid di keempat keadaan repo (normal, tanpa commit, detached HEAD, bukan repo git).
`python3 scripts/lint_plugins.py` hijau tanpa `LINT_IGNORE` baru.

## N7 [Rendah] Dokumen dan versi
- [x] Selesai

- `README.md` analyst: baris `sync-payload` di `## Penegakan Mekanis`, seksi baru `## Sinkron nataflow
  (opsional)` (config, prasyarat server MCP, perilaku gagal), dan `## Sengaja Belum Ada` menyebut sinkron
  status, artefak engineer, dan pembatalan tiket.
- `flow/analyst.md`: langkah 5.4 di `### analyst:spec`, sequence diagram approve, baris config di
  `## Artefak & Siklus Status`, rute pemulihan di `### analyst:intake`, dan baris push gagal di
  `## Titik Gagal & Pemulihan`.
- `src/plugins/analyst/.claude-plugin/plugin.json` → `0.7.0` (lint M7), dalam commit `chore(release)`
  tersendiri.

## Di luar cakupan (fase berikutnya)

- Sinkron status: `cancel` → `cancelled`, selesai engineer → `done`. PRD backend belum membuka jalur ubah
  status.
- Push artefak engineer (`TASK.md`, `PRD.md`, brief, `REPORT.md`) sebagai dokumen, yang menunggu
  `update_document`/`get_document` di server.
- Push dari plugin `backend`/`frontend`, dan penghapusan task saat tiket dibatalkan.
- Pendaftaran server MCP dan penyimpanan key: tanggung jawab user (`claude mcp add …`), bukan plugin.
