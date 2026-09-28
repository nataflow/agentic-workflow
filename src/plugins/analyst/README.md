# analyst

Plugin Claude Code yang menjadi jembatan antara **pengguna/stakeholder** dan **engineer**. Perannya gabungan
business analyst, system analyst di level perilaku, dan product owner: menerima permintaan mentah, menggali
faktanya lewat tanya-jawab dengan peminta non-engineer, lalu menerbitkan `TICKET.md` — kartu tiket non-teknis
setara detail kartu Jira/Trello — yang siap diambil tim developer. `TICKET.md` adalah satu-satunya artefak
yang disunting skill: catatan elisitasi tinggal di dalamnya sebagai seksi terakhir. `review.md` di sebelahnya
adalah jejak vonis reviewer terakhir, hanya ditulis `ticket.py`.

Tiga aturan menyetir bentuknya: **tiket menyebut apa dan kenapa, tidak pernah bagaimana**; **fakta berasal
dari peminta, bukan dari tebakan analis**; dan **yang dapat divonis mesin divonis skrip** — struktur,
penomoran, keterpikulan aturan oleh acceptance criteria, kebocoran istilah teknis, dan materai persetujuan.

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install analyst@nataflow
```

Prasyarat: `python3` ≥ 3.9. `git` opsional (lihat seksi Git). Lihat juga `README.md` di root repo.

## Tiga Skill, Satu Subagent

| Skill | Peran | Menulis | Dikunci oleh |
|---|---|---|---|
| `analyst:intake` | gerbang: wilayah, tipe, ukuran, duplikat, pemulihan ticketdir, sinkron ulang nataflow | — | — |
| `analyst:elicit` | tanya-jawab dengan peminta, direkam tiap giliran | `TICKET.md` — `domain_terms` + `## Catatan Elisitasi` (kerangkanya ditulis `ticket.py new`) | `ticket.py close` → `elicitation: CLOSED` + segel catatan |
| `analyst:spec` | penyusunan kartu, review independen, persetujuan user | `TICKET.md` — kartu di atas catatan | `ticket.py approve` → `READY` |

Hanya `intake` yang muncul di menu `/`. `elicit` dan `spec` ber-`user-invocable: false`: model memanggilnya
lewat tool Skill sesuai keadaan ticketdir, dan pemulihan tiket (melanjutkan elisitasi, merevisi, membuka ulang)
selalu dimulai dari `/analyst:intake`.

`ticket-reviewer` (`agents/ticket-reviewer.md`) adalah pembaca independen read-only yang memvonis draft
kartu `PASS`/`BLOCKED` terhadap catatan elisitasi di berkas yang sama sebelum diajukan ke user; ia didispatch langsung lewat
`skills/spec/dispatcher/reviewer.md`, tanpa skill pembungkus.

## Workflow

```
permintaan ──► intake ──┬─► di luar wilayah (kerja teknis murni) ──► backend:tech-lead / frontend:lead
                        ├─► status tiket ──────────────────────────► jawaban, berhenti
                        │
                        └─► elicit ─► ticket.py new ─► TICKET.md (kerangka + permintaan asli, elicitation: OPEN)
                              │        tanya-jawab ≤3/giliran, tulis tiap giliran (≤5 giliran per sesi)
                              │        menunggu jawaban pihak lain → TERTAHAN, lanjut di sesi berikutnya
                              │        konfirmasi fakta → ticket.py close (CLOSED + segel catatan + commit)
                              ▼
                            spec ─► kartu DRAFT di atas catatan → validate_doc → ticket-reviewer (≤2 ronde)
                                    → commit → AskUserQuestion → ticket.py approve → READY (+ commit)
                                      → sinkron nataflow bila analyst/nataflow.json ada (gagal ≠ batal READY)
                                                                   │
                    ticket_source: <ticketdir>/TICKET.md ke ──┘ backend:tech-lead / frontend:lead
```

Permintaan yang sudah lengkap tetap melewati `elicit`: fakta diisi dari permintaan asli, dikonfirmasi sekali,
lalu ditutup tanpa satu pertanyaan pun. Dengan begitu `spec` dan `ticket-reviewer` selalu punya satu sumber
kebenaran tertulis.

## Artefak

```
./analyst/
  nataflow.json   opsional, ditulis user: mengaktifkan sinkron tiket READY ke nataflow
  tickets/
    2609231400-cicilan-pembayaran/
      TICKET.md   satu-satunya artefak yang disunting skill
      review.md   blok `## Ticket Review` terakhir (ditulis `ticket.py review --report`)
```

`TICKET.md` punya dua bagian dengan dua pemilik dan dua status di frontmatter:

```
---
status: DRAFT → READY          ← ticket.py (approve / reopen / cancel)
elicitation: OPEN → CLOSED     ← ticket.py new / close (analyst:elicit)
...
---
# <judul>                      ← kartu, ditulis analyst:spec
## Latar Belakang … ## Lampiran
## Catatan Elisitasi           ← ditulis analyst:elicit, selalu H2 terakhir
### Permintaan Asli · ### Fakta · ### Log Tanya-Jawab · ### Pertanyaan Terbuka
```

- **Kartu** — Latar Belakang, User Story (`BUG`: Laporan Bug), Acceptance Criteria `AC-{n}`
  Given/When/Then, Aturan Bisnis `BR-{n}` (tiap BR disebut minimal satu AC), Di Luar Cakupan, Pertanyaan
  Terbuka beserta asumsinya, Lampiran. Frontmatter memuat `type`, `priority`, `requester`, dan `external_ref`
  untuk kunci kartu Jira/Trello. Bagian inilah yang disalin ke Jira/Trello.
- **`## Catatan Elisitasi`** — permintaan asli (verbatim), fakta per pilar (`####`), log tanya-jawab
  bernomor, dan pertanyaan terbuka `Q-{n}` berlabel `MEMBLOKIR`/`TIDAK MEMBLOKIR` beserta siapa yang
  ditunggu. Pilar per tipe: `FEATURE`/`IMPROVEMENT` — Masalah, Aktor, Kondisi Saat Ini, Kondisi Diinginkan,
  Aturan Bisnis, Batas Cakupan, Urgensi (+ Kasus Khusus, Ukuran Keberhasilan); `BUG` — Langkah Reproduksi,
  Yang Diharapkan, Yang Terjadi, Dampak, Urgensi (+ Lingkungan, Batas Cakupan). Selama elisitasi berjalan,
  berkas hanya berisi H1 kerja dan seksi ini; `spec` menyisipkan kartu di atasnya tanpa menyentuhnya.

Kerangka kanonik dan contoh terisi: `skills/elicit/templates/elicit-template.md` dan
`skills/spec/templates/ticket-template.md`.

## Penegakan Mekanis

| Skrip | Memvonis |
|---|---|
| `_common/ticket.py state` | keadaan tiap ticketdir: `KOSONG`, `ELISITASI`, `SPEC`, `DRAFT`, `READY`, `DRIFT`, `RUSAK`, `NAMA_TIDAK_SAH`, `DIBATALKAN` |
| `_common/ticket.py new` | ticketdir baru beserta `TICKET.md` awal: kerangka persis bagian 1 `elicit-template.md`, permintaan asli dari `--request` sebagai blockquote, dan `request_hash`; ticketdir `KOSONG` ber-slug sama dipakai ulang |
| `_common/ticket.py close` | satu-satunya penulis `elicitation: CLOSED`: hanya bila `validate_doc.py --kind elicit` `PASS` (bila tidak, berkas dikembalikan); menyegel catatan (`elicit_hash`, `elicit_log`) dan commit `docs(ticket): elisitasi <slug>`; menutup ulang catatan yang berubah sejak segel menuntut baris log baru `Dibuka ulang`; tiket lama tanpa segel diadopsi sekali |
| `_common/ticket.py check --gate elicit\|spec` | prasyarat gate atas satu ticketdir; gate `spec` menolak catatan elisitasi yang berbeda dari segelnya; mencetak `root=` (path ticketdir relatif root, bukan cwd) dan, untuk draft, `ronde` dan `sidik` (slot prompt reviewer), `review_basi` (bagian yang berubah sesudah review), serta `review_report` |
| `_common/validate_doc.py --kind elicit` | `## Catatan Elisitasi`: struktur, pilar per tipe, log bernomor, tiap heading sekali, permintaan asli sama dengan `request_hash`; `CLOSED` ⇒ nol pilar kosong, nol pertanyaan memblokir, nol `Asumsi:` di mana pun dalam baris, dan tiap `domain_terms` punya baris konfirmasi berjawaban `Ya` di log |
| `_common/validate_doc.py --kind ticket` | kartu: struktur per tipe (tiap heading sekali), AC Given/When/Then, BR terpikul AC, ID `Q-{n}` sama dengan `TIDAK MEMBLOKIR` di catatan, nol placeholder, **nol kebocoran teknis** |
| `_common/ticket.py review` | vonis `PASS`/`BLOCKED` **wajib** membawa blok reviewer (`--report`): `- Verdict:` sama dengan `--verdict`, dan `- Sidik:` (disalin reviewer dari prompt) sama dengan sidik `<kartu>/<catatan elisitasi>` di disk — draft yang berubah sesudah dispatch ditolak; blok wajib konsisten (`- BLOCKER:` = jumlah butir, `PASS` ⇔ nol BLOCKER, `- Ronde:` = ronde yang dicatat); blok disimpan ke `review.md`; ditolak bila salah satu validator `FAIL` atau catatan berbeda dari segelnya; plafon 2 ronde per revisi, dibuka ulang hanya bila catatan elisitasi disegel ulang |
| `_common/ticket.py approve` | `READY` hanya bila kedua validator (`ticket`, `elicit`) `PASS`, `elicitation: CLOSED` dengan catatan sama dengan segelnya, **dan** vonis review `PASS` atas sidik kartu dan catatan elisitasi sekarang; menulis `approved_hash` dan `approved_seal` (segel yang dibaca engineer) |
| `_common/ticket.py revise` / `reopen` / `cancel` | plafon 3 revisi per basis fakta; buka ulang tiket `READY`; tutup ticketdir (direktori kosong dihapus; tiket `READY` hanya dengan `--force`; di-commit `docs(ticket): batalkan TICKET <slug>`) |
| `_common/ticket.py ref` | isi `external_ref` pada `DRAFT`/`READY`; `DRIFT`/`RUSAK` ditolak (subjek `ref TICKET` dibaca penerima tiket lama sebagai tanda terkunci); `READY` di-commit `docs(ticket): ref TICKET <slug>`, `DRAFT` tidak di-commit |
| `_common/ticket.py sync-payload` | argumen tool MCP nataflow untuk tiket `READY` (bukan `DRIFT`/`RUSAK`): `lookup` (`list_task`), `create`, `update` — judul dari H1, deskripsi = kartu tanpa catatan elisitasi, `metadata` teks JSON byte-stabil berkunci `ticket_key`; `SKIP` tanpa `analyst/nataflow.json`, `FAIL` bila config rusak; read-only, tanpa commit |

Kontrak exit `close`/`approve`/`ref`/`cancel`: 0 = tertulis dan ter-commit (atau tanpa git, atau isinya sudah sama
dengan HEAD), 1 = ditolak, 3 = tertulis tetapi commit gagal — baris `COMMIT GAGAL` memuat sebab git dan perintah commit manualnya, lengkap dengan subjeknya.

Pemindai kebocoran teknis menolak istilah sistem (endpoint, database, query, nama framework, `API`, …), path
berkas, `file:baris`, metode dan kode status HTTP, identifier `snake_case`/`camelCase`, dan blok kode di kartu, di luar
`## Lampiran` dan `## Catatan Elisitasi` (permintaan asli dan log adalah kutipan mentah). Istilah, kode status, dan identifier dalam tanda kutip dikecualikan — itu tulisan yang dilihat pengguna — tetapi path berkas, `file:baris`, metode HTTP + path, dan path API tetap ditandai di dalam kutipan. Kata yang bentrok
dengan kosakata bisnis Indonesia (kereta *api*, *skema* cicilan, pengiriman *express*) sengaja tidak didaftar,
dan istilah yang memang kosakata produk (mis. produk API untuk mitra, aplikasi `myPertamina`) diizinkan lewat
`domain_terms` — dicatat oleh elisitasi sesudah dikonfirmasi peminta lewat baris log, baru boleh dipakai kartu.

Sidik review dihitung per bagian — kartu (beserta `type`, `priority`) dan catatan elisitasi (beserta `type`,
`domain_terms`) — sehingga suntingan di bagian mana pun membuat vonis basi. `approve` memateraikan sidik berkas
utuh (`approved_hash`) dan segel serah-terima (`approved_seal`). Tiket `READY` yang disunting sesudah disetujui terbaca `DRIFT`: sidik atau segelnya tidak lagi sama. Catatan elisitasi juga
disegel saat ditutup (`elicit_hash`): hanya elisitasi yang dibuka ulang dan tercatat di log yang boleh mengubahnya,
jadi `spec` tidak dapat menyesuaikan fakta dengan kartunya. Perubahan resmi dimulai
dari `/analyst:intake`, yang merutekan ke `analyst:spec` (reopen) untuk mengulang review dan persetujuan.

## Git

Repo git **tidak** wajib — plugin dapat dipakai di folder dokumen biasa. Ruang kerja berakar di root worktree
git bila ada, selain itu di direktori kerja. Di repo git, tiap artefak di-commit atomik dengan staging path
eksplisit (`docs(ticket): ...`); di luar git, commit dilewati dan disebut di Output.

## Serah Terima ke Engineer

Tiket `READY` diserahkan lewat parameter `ticket_source` = path `<ticketdir>/TICKET.md` ke
`backend:tech-lead` dan/atau `frontend:lead` (baris penutup `SPEC — READY` memuatnya). Kontraknya:

- **Syarat**: frontmatter `status: READY` dan `elicitation: CLOSED`, dan isi berkas sama dengan
  `approved_seal` — di dalam maupun di luar repo git, apa pun subjek commit-nya. Tiket lama tanpa
  `approved_seal` dinilai cara lama: commit terakhir yang menyentuh berkas bersubjek
  `docs(ticket): kunci TICKET <slug> READY` atau `docs(ticket): ref TICKET <slug>`, dan berkasnya bersih.
  Tiket yang disunting sesudah approve ditolak prasyarat `task` kedua plugin (DRIFT) dan dikembalikan ke
  `analyst:spec`.
- **Yang dibaca**: kartu saja (H1 sampai akhir `## Lampiran`); catatan elisitasi hanya jejak, bukan sumber
  kriteria.
- **Namespace**: kartu tetap menulis `AC-{n}`/`BR-{n}`. Di hilir keduanya dirujuk `TAC-{n}`/`TBR-{n}` agar
  tidak bertabrakan dengan `AC-{n}` PRD/CONTRACT dan `BR-{n}` BRD.
- **Keterlacakan**: tiap `TAC-{n}` dipikul minimal satu `SC-{n}` di `TASK.md` engineer, atau tercatat di
  `## Out of Scope` beralasan (mis. porsi frontend). Validator `TASK.md` kedua plugin menagihnya.
- **Kesepakatan aturan**: aktor, kondisi, dan `TBR-{n}` yang tertulis di tiket dihitung sudah disetujui.
  `backend:analyst` tidak menjadwalkan BRD hanya karena fakta itu; bila BRD tetap terbit karena fakta di
  luar tiket, `business-analysis` menyerap `TBR-{n}` tanpa menanyakannya ulang (`— Asal: TBR-{m}`).

`ticket_seal` di `_common/analyst_lib.py` disalin apa adanya ke `_common/precondition_lib.py` backend dan
frontend (`tests/test_a1_ticket_source.py` menagih ketiganya identik); mengubah segel atau subjek commit
`approve`/`ref` berarti mengubah ketiganya bersamaan.

Engineer menerbitkan `TASK.md` teknisnya sendiri —
lengkap dengan `file:baris`, alat ukur teknis, dan ledger — dari tiket itu. Nama `TICKET.md` sengaja berbeda
dari `TASK.md`: kontraknya bertolak belakang, dan keduanya tidak pernah tinggal di direktori yang sama.

Hook SessionStart `backend`/`frontend` mengecualikan permintaan yang memanggil atau melanjutkan
`analyst:*`. Panggil `/analyst:intake` untuk memulai; susulan di tengah elisitasi tetap ditangani analyst.
Untuk repo yang hanya memakai analyst, tulis `.claude/workflow` tanpa nama plugin engineer (mis. berisi
`analyst`) — hook kedua plugin engineer lalu diam di repo itu.

## Sinkron nataflow (opsional)

Tiket `READY` dapat dicerminkan sebagai task di nataflow. `TICKET.md` di disk dan git tetap satu-satunya
sumber kebenaran; task hanya cermin kartunya, dan tidak ada yang ditulis balik ke `TICKET.md`.

- **Aktif per repo** lewat `analyst/nataflow.json` (ter-commit): `mcp_server` (default `nataflow-api`),
  `workspace_id` (UUID; wajib bila MCP key ber-scope project), `pic_id` (UUID; kosong → pemilik key). Berkas
  absen → sinkron dilewati; ada tetapi rusak (kunci asing, nilai bukan string, UUID tidak sah) → `GAGAL`.
- **Prasyarat di luar plugin**: server MCP nataflow terdaftar di Claude Code beserta MCP key-nya. Plugin tidak
  mendeklarasikan server dan tidak menyimpan key.
- **Kapan**: `analyst:spec` sesudah `approve` (`READY` tertulis, termasuk bila commit-nya gagal). Prosedurnya
  di `skills/spec/references/nataflow-sync.md`: `ticket.py sync-payload` menyusun seluruh argumen, lalu model
  mencari task lewat `list_task` bersaring `{"source":"analyst","ticket_key":<ticketdir>}` — tidak ada →
  `create_task`, satu → `update_task` (judul, kartu, dan metadata dikirim ulang utuh), lebih dari satu →
  berhenti tanpa menulis. Approve ulang sesudah `reopen` memperbarui task yang sama; tiket baru ber-slug sama
  menjadi task baru karena ticketdir-nya berbeda.
- **Isi**: judul = H1 kartu; deskripsi = kartu (H1 sampai akhir `## Lampiran`) tanpa catatan elisitasi;
  metadata `source`, `ticket_key`, `slug`, `type`, `priority`, `approved`, `approved_seal`, `reopened`, dan
  `external_ref` bila terisi. Status task tidak pernah dikirim; `requester` tetap di disk.
- **Gagal tidak memblokir**: baris penutup `SPEC — READY` memuat segmen `nataflow <dibuat #<code> | diperbarui
  #<code> | dilewati | GAGAL: <sebab>>`. `GAGAL` tidak menurunkan `READY`; ulangi lewat `/analyst:intake`
  ("sinkron ulang tiket `<ticketdir>`").

## Batas Dengan Plugin Lain

| Kebutuhan | Pakai |
|---|---|
| Menulis tiket dari permintaan pengguna/stakeholder | `analyst` |
| Kontrak teknis, BRD/PRD berjangkar kode, brief implementasi | `backend` |
| Alur layar, bentuk layar, kontrak layer frontend | `frontend` |
| Perubahan kecil–menengah dengan satu berkas rencana (`plan/<task>.md`), tanpa taskdir | `quickdev` |
| Refaktor, upgrade pustaka, stacktrace dari developer | gerbang engineer, bukan `analyst` |

## Sengaja Belum Ada

- **`split`** — pemecahan epic menjadi beberapa tiket. Sementara ini `intake` memilih satu tujuan per tiket dan
  mengembalikan sisanya sebagai antrian tiket.
- **`acceptance`** — UAT: membaca `REPORT.md` engineer dan memvonis AC tiket dalam bahasa bisnis.
- **Sinkron nataflow lanjutan** — status task (`cancel` → dibatalkan, selesai engineer → selesai), artefak
  engineer (`TASK.md`, `PRD.md`, brief, `REPORT.md`) sebagai dokumen, dan penghapusan task saat tiket dibatalkan.
  Sinkron sekarang hanya membuat dan memperbarui isi task.
