# analyst

Plugin Claude Code yang menjadi jembatan antara **pengguna/stakeholder** dan **engineer**. Perannya gabungan
business analyst, system analyst di level perilaku, dan product owner: menerima permintaan mentah, menggali
faktanya lewat tanya-jawab dengan peminta non-engineer, lalu menerbitkan `TICKET.md` — kartu tiket non-teknis
setara detail kartu Jira/Trello — yang siap diambil tim developer. Untuk perubahan teknis dari lead engineer
(refaktor, relasi data, arsitektur, kinerja, dependensi) ada tipe `TECH`: kartu teknis berbukti `file:baris`
yang mengunci kondisi target sebelum dikerjakan (lihat **Tiket Teknis `TECH`**). `TICKET.md` adalah satu-satunya artefak
yang disunting skill: catatan elisitasi tinggal di dalamnya sebagai seksi terakhir. `review.md` di sebelahnya
adalah jejak vonis reviewer terakhir, hanya ditulis `ticket.py`. Di luar tiket, `analyst:notulen` merapikan
catatan kasar rapat menjadi `NOTULEN.md` tanpa mengarang isinya (lihat **Notulen Rapat**).

Tiga aturan menyetir bentuknya: **tiket menyebut apa dan kenapa, tidak pernah bagaimana**; **fakta berasal
dari peminta, bukan dari tebakan analis**; dan **yang dapat divonis mesin divonis skrip** — struktur,
penomoran, keterpikulan aturan oleh acceptance criteria, kebocoran istilah teknis, dan materai persetujuan.

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install analyst@nataflow
```

Prasyarat: `python3` ≥ 3.9. `git` opsional (lihat seksi Git). Lihat juga `README.md` di root repo.

## Empat Skill, Dua Subagent

| Skill | Peran | Menulis | Dikunci oleh |
|---|---|---|---|
| `analyst:intake` | gerbang: wilayah, tipe, ukuran, batch berurutan hingga 5 tiket, duplikat, pemulihan ticketdir, sinkron ulang nataflow | — | — |
| `analyst:elicit` | tanya-jawab dengan peminta, direkam tiap giliran | `TICKET.md` — `domain_terms` + `## Catatan Elisitasi` (kerangkanya ditulis `ticket.py new`) | `ticket.py close` → `elicitation: CLOSED` + segel catatan |
| `analyst:spec` | penyusunan kartu, review independen, persetujuan user | `TICKET.md` — kartu di atas catatan | `ticket.py approve` → `READY` |
| `analyst:notulen` | catatan kasar rapat → notulen terstruktur, klarifikasi ke pencatat, sinkron opsional | `NOTULEN.md` (kerangkanya ditulis `notulen.py new`) | `notulen.py final` → `FINAL` |

`intake` dan `notulen` muncul di menu `/`. `elicit` dan `spec` ber-`user-invocable: false`: model memanggilnya
lewat tool Skill sesuai keadaan ticketdir, dan pemulihan tiket (melanjutkan elisitasi, merevisi, membuka ulang)
selalu dimulai dari `/analyst:intake`.

`ticket-reviewer` (`agents/ticket-reviewer.md`) adalah pembaca independen read-only yang memvonis draft
kartu `PASS`/`BLOCKED` terhadap catatan elisitasi di berkas yang sama sebelum diajukan ke user; ia didispatch langsung lewat
`skills/spec/dispatcher/reviewer.md`, tanpa skill pembungkus.

`code-scout` (`agents/code-scout.md`) adalah penelusur kode dangkal read-only (`Read`/`Grep`/`Glob`, model
`haiku`, kuota 8 pemanggilan) yang didispatch `elicit` lewat `skills/elicit/dispatcher/scout.md`, maksimal dua kali
per tiket; dalam batch, dispatch pertama semua tiket berjalan paralel di awal batch. Ia hanya melaporkan apa yang ada di kode dan di mana, tanpa flow, alur, atau edge case. Konteks utama
`elicit` tidak membaca kode sendiri. Untuk tiket `TECH` balikannya menjadi bukti `path:baris`; untuk tipe lain
balikannya hanya bahan pertanyaan atau `Asumsi:` yang dikonfirmasi peminta, karena kode menunjukkan apa yang ada,
bukan apa yang diinginkan peminta.

## Workflow

```
permintaan ──► intake ──┬─► di luar wilayah (kerja teknis kecil) ─► backend:tech-lead / frontend:lead
                        ├─► status tiket ──────────────────────────► jawaban, berhenti
                        │
                        └─► elicit ─► ticket.py new ─► TICKET.md (kerangka + permintaan asli, elicitation: OPEN)
                              │        code-scout (≤2 dispatch per tiket): bukti TECH, atau konteks pertanyaan
                              │        tanya-jawab ≤3/giliran, tulis tiap giliran (≤5 giliran per tiket)
                              │        menunggu jawaban pihak lain → TERTAHAN, lanjut di sesi berikutnya
                              │        konfirmasi fakta → ticket.py close (CLOSED + segel catatan + commit)
                              ▼
                            spec ─► kartu DRAFT di atas catatan → validate_doc → ticket-reviewer (≤2 ronde)
                                    → commit → AskUserQuestion → ticket.py approve → READY (+ commit)
                                      → sinkron nataflow bila .claude/nataflow.json ada (gagal ≠ batal READY)
                                                                   │
                    ticket_source: <ticketdir>/TICKET.md ke ──┘ backend:tech-lead / frontend:lead
```

Permintaan yang sudah lengkap tetap melewati `elicit`: fakta diisi dari permintaan asli, dikonfirmasi sekali,
lalu ditutup tanpa satu pertanyaan pun. Dengan begitu `spec` dan `ticket-reviewer` selalu punya satu sumber
kebenaran tertulis.

**Batch.** Satu pesan berisi 2–5 permintaan menjadi batch, bukan antrian yang harus masuk `intake` satu per
satu:

```
permintaan (2–5 tujuan) ─► intake: pecah, tipe, duplikat, urutan otomatis, slug, peminta sekali
                             │      → blok INTAKE — BATCH
                             ▼
                           elicit: ticket.py new --urutan k/N ×N (semua tersegel di disk)
                             │     code-scout semua tiket paralel dalam satu pesan
                             ▼
                           tiket 1: elicit → spec → READY/ditahan/tertahan ─► tiket 2 ─► … ─► tiket N
                                                                                   ▼
                                                              ringkasan dari ticket.py state --batch <id>
```

Urutan ditentukan tanpa pertanyaan dari kata-kata peminta: prasyarat lebih dulu, lalu urgensi yang disebut,
lalu urutan di pesan. Tiap tiket diselesaikan penuh sebelum tiket berikutnya, satu `AskUserQuestion` hanya
membahas satu tiket (header `Tiket k/N`), dan plafon giliran serta scout berlaku per tiket. Jawaban untuk satu
tiket tidak menjadi fakta tiket lain kecuali dikonfirmasi lewat `Asumsi:`. Tiket yang tertahan tidak menahan
batch, dan sesi berikutnya melanjutkan dari tiket terbuka berurutan terkecil. Aturan lengkap:
`skills/intake/references/batch.md`.

## Artefak

```
./analyst/
  nataflow.json   opsional, format lama; config bersama `.claude/nataflow.json` (keduanya ditulis user)
  tickets/
    2609231400-cicilan-pembayaran/
      TICKET.md   satu-satunya artefak yang disunting skill
      review.md   blok `## Ticket Review` terakhir (ditulis `ticket.py review --report`)
  notulen/
    .gitignore    `*`, ditulis `notulen.py new` tanpa syarat: notulen tidak pernah di-commit
    2610021400-sprint-review/
      NOTULEN.md  notulen rapat beserta `## Catatan Asli`
```

`TICKET.md` punya dua bagian dengan dua pemilik dan dua status di frontmatter:

```
---
status: DRAFT → READY          ← ticket.py (approve / reopen / cancel)
elicitation: OPEN → CLOSED     ← ticket.py new / close (analyst:elicit)
batch: <ticketdir urutan 1>    ← hanya tiket batch, ditulis ticket.py new --urutan
urutan: <k>/<N>                ← (field pembukuan, di luar sidik dan segel)
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
  Yang Diharapkan, Yang Terjadi, Dampak, Urgensi (+ Lingkungan, Batas Cakupan); `TECH` — Masalah Teknis,
  Kondisi Saat Ini, Kondisi Target, Batasan, Batas Cakupan, Urgensi (+ Keputusan, Rollout, Ukuran
  Keberhasilan). Selama elisitasi berjalan,
  berkas hanya berisi H1 kerja dan seksi ini; `spec` menyisipkan kartu di atasnya tanpa menyentuhnya.

Kerangka kanonik dan contoh terisi: `skills/elicit/templates/elicit-template.md` dan
`skills/spec/templates/ticket-template.md`.

## Tiket Teknis `TECH`

Untuk perubahan struktur yang diminta lead engineer dan perlu disepakati sebelum dikerjakan. Kerja teknis
kecil, stacktrace, dan pertanyaan letak kode tetap langsung ke gerbang engineer.

- **Category** (`ticket.py new --category`, wajib): `REFACTOR`, `DATA_MODEL`, `ARCHITECTURE`, `PERFORMANCE`,
  atau `DEPENDENCY`. Category menentukan apa yang wajib tergali dan dipikul AC (mis. `DATA_MODEL` → migrasi
  naik-turun dan nasib data lama).
- **Elisitasi ringkas** (`skills/elicit/references/elicitation-tech.md`): brief lead engineer dipetakan ke pilar,
  tiap klaim kondisi sekarang dibuktikan subagent `code-scout` (kuota 8 `Read`/`Grep`/`Glob`) dan butir yang
  ditemukannya dicatat sebagai `path:baris`, lalu hanya celahnya yang ditanyakan.
- **Kartu**: Latar Belakang, Kondisi Saat Ini (berbukti `path:baris`), Kondisi Target (struktur akhir, bukan
  langkah), Keputusan `D-{n}` (alasan + alternatif), Batasan `C-{n}`, Acceptance Criteria `AC-{n}` dengan
  `— verifikasi:`, Dampak & Rollout, Di Luar Cakupan, Pertanyaan Terbuka, Lampiran.
- **Penegakan**: validator memeriksa tiap `path:baris` ada di disk, tiap `C-{n}` dipikul AC, dan AC berbukti
  verifikasi; pemindai kebocoran teknis tidak berlaku. `ticket-reviewer` membuka sendiri buktinya dan menolak
  langkah implementasi di kartu.
- **Satu repo**: tiket `TECH` tinggal dan diserahkan di repo yang diubah. Perubahan lintas repo menjadi satu tiket
  per repo yang saling merujuk di `## Lampiran`.

## Notulen Rapat

`/analyst:notulen` menerima catatan kasar rapat (ditempel atau berupa berkas) dan menulis
`analyst/notulen/<YYMMDDhhmm>-<slug>/NOTULEN.md`: Ringkasan, Peserta, Agenda, Pembahasan, Keputusan `D-{n}`,
Action Item `A-{n}` (PIC dan tenggat, atau `belum ditentukan`), Pertanyaan Terbuka `Q-{n}`, dan `## Catatan Asli`
apa adanya. Kerangka dan aturan isinya: `skills/notulen/templates/notulen-template.md`.

- **Tanpa mengarang**: isi hanya dari catatan asli atau jawaban pencatat. Butir masuk Keputusan hanya bila dinyatakan
  diputuskan; PIC dan tenggat tidak ditebak. Celah ditanyakan ke pencatat (≤ 3 pertanyaan per giliran, 2 giliran).
- **Final berpersetujuan**: `notulen.py final` menulis `FINAL` dan menyegel isinya (`final_hash`) sesudah validator
  `PASS` dan jawaban eksplisit user. Suntingan sesudahnya terbaca `DRIFT` sampai `final` dijalankan ulang.
- **Tanpa git**: `analyst/notulen/.gitignore` (`*`) ditulis tanpa syarat, dan skripnya tidak pernah meng-commit.
- **Bukan tiket**: notulen tidak membaca kode dan tidak membuat tiket. Permintaan yang muncul di rapat dijadikan tiket
  lewat `/analyst:intake`.

## Penegakan Mekanis

| Skrip | Memvonis |
|---|---|
| `_common/ticket.py state` | keadaan tiap ticketdir: `KOSONG`, `ELISITASI`, `SPEC`, `DRAFT`, `READY`, `DRIFT`, `RUSAK`, `NAMA_TIDAK_SAH`, `DIBATALKAN`; tiket batch tampil berurutan `urutan` di posisi tiket urutan 1-nya, dan `--batch <id>` menyaring satu batch dalam semua keadaan |
| `_common/ticket.py new` | ticketdir baru beserta `TICKET.md` awal: kerangka persis bagian 1 `elicit-template.md`, permintaan asli dari `--request` sebagai blockquote, dan `request_hash`; ticketdir `KOSONG` ber-slug sama dipakai ulang; `--urutan <k>/<N>` (2 ≤ N ≤ 5, dan `--batch <id>` untuk k ≥ 2) menulis `batch`/`urutan` dan menolak batch tak dikenal, N berbeda, atau urutan kembar; repo git bersinkron nataflow → `analyst/tickets/.gitignore` (`*`) ditulis bila belum ada; `git=ya\|tidak\|diabaikan` |
| `_common/ticket.py close` | satu-satunya penulis `elicitation: CLOSED`: hanya bila `validate_doc.py --kind elicit` `PASS` (bila tidak, berkas dikembalikan); menyegel catatan (`elicit_hash`, `elicit_log`) dan commit `docs(ticket): elisitasi <slug>`; menutup ulang catatan yang berubah sejak segel menuntut baris log baru `Dibuka ulang`; tiket lama tanpa segel diadopsi sekali |
| `_common/ticket.py check --gate elicit\|spec` | prasyarat gate atas satu ticketdir; gate `spec` menolak catatan elisitasi yang berbeda dari segelnya; mencetak `root=` (path ticketdir relatif root, bukan cwd) dan, untuk draft, `ronde` dan `sidik` (slot prompt reviewer), `review_basi` (bagian yang berubah sesudah review), serta `review_report` |
| `_common/validate_doc.py --kind elicit` | frontmatter, termasuk pasangan `batch`/`urutan` yang sah; `## Catatan Elisitasi`: struktur, pilar per tipe, log bernomor, tiap heading sekali, permintaan asli sama dengan `request_hash`; tipe selain `TECH` dilarang memuat `` `path:baris` `` di luar permintaan asli (konteks `code-scout` bukan fakta); `CLOSED` ⇒ nol pilar kosong, nol pertanyaan memblokir, nol `Asumsi:` di mana pun dalam baris, dan tiap `domain_terms` punya baris konfirmasi berjawaban `Ya` di log |
| `_common/validate_doc.py --kind ticket` | kartu: struktur per tipe (tiap heading sekali), AC Given/When/Then, BR terpikul AC, ID `Q-{n}` sama dengan `TIDAK MEMBLOKIR` di catatan, nol placeholder, **nol kebocoran teknis** |
| `_common/ticket.py review` | vonis `PASS`/`BLOCKED` **wajib** membawa blok reviewer (`--report`): `- Verdict:` sama dengan `--verdict`, dan `- Sidik:` (disalin reviewer dari prompt) sama dengan sidik `<kartu>/<catatan elisitasi>` di disk — draft yang berubah sesudah dispatch ditolak; blok wajib konsisten (`- BLOCKER:` = jumlah butir, `PASS` ⇔ nol BLOCKER, `- Ronde:` = ronde yang dicatat); blok disimpan ke `review.md`; ditolak bila salah satu validator `FAIL` atau catatan berbeda dari segelnya; plafon 2 ronde per revisi, dibuka ulang hanya bila catatan elisitasi disegel ulang |
| `_common/ticket.py approve` | `READY` hanya bila kedua validator (`ticket`, `elicit`) `PASS`, `elicitation: CLOSED` dengan catatan sama dengan segelnya, **dan** vonis review `PASS` atas sidik kartu dan catatan elisitasi sekarang; menulis `approved_hash` dan `approved_seal` (segel yang dibaca engineer) |
| `_common/ticket.py commit --stage draft\|tertunda` | satu-satunya jalan commit draft `DRAFT`: `draft` (spec Phase 4, `TICKET.md` + `review.md`, subjek `draft TICKET <slug>` atau `revise TICKET <slug>` sesudah `revise`) dan `tertunda` (elisitasi tertahan, subjek `elisitasi <slug> (tertunda)`); tiket `READY` ditolak |
| `_common/ticket.py revise` / `reopen` / `cancel` | plafon 3 revisi per basis fakta; buka ulang tiket `READY`; tutup ticketdir (direktori kosong dihapus; tiket `READY` hanya dengan `--force`; di-commit `docs(ticket): batalkan TICKET <slug>`) |
| `_common/ticket.py ref` | isi `external_ref` pada `DRAFT`/`READY`; `DRIFT`/`RUSAK` ditolak (subjek `ref TICKET` dibaca penerima tiket lama sebagai tanda terkunci); `READY` di-commit `docs(ticket): ref TICKET <slug>`, `DRAFT` tidak di-commit |
| `_common/ticket.py sync-payload` | argumen tool MCP nataflow untuk tiket `READY` (bukan `DRIFT`/`RUSAK`): `lookup` (`list_task`), `create`, `update` — judul dari H1, deskripsi = kartu tanpa catatan elisitasi, `metadata` teks JSON byte-stabil berkunci `ticket_key`; `documents` (`review.md`); tiket pernah-`READY` yang dibatalkan → `lookup` + `task_status` `cancelled`; `SKIP` tanpa `.claude/nataflow.json` maupun `analyst/nataflow.json`, `FAIL` bila config rusak atau keduanya berbeda isi; read-only, tanpa commit |
| `notulen/scripts/notulen.py state` / `new` | keadaan tiap notulendir (`DRAFT`, `FINAL`, `DRIFT`, `RUSAK`, `NAMA_TIDAK_SAH`); notulendir baru beserta kerangka persis bagian 1 `notulen-template.md`, catatan asli verbatim, `source_hash`, dan `analyst/notulen/.gitignore` |
| `notulen/scripts/notulen.py check` | struktur dan urutan H2, catatan asli sama dengan `source_hash`, seksi isi terisi, `D-{n}`/`A-{n}`/`Q-{n}` berurutan, action item ber-PIC dan bertenggat `YYYY-MM-DD` atau `belum ditentukan`, nol placeholder; `--final` ⇒ nol `Asumsi:` |
| `notulen/scripts/notulen.py final` | satu-satunya penulis `FINAL`: validator `PASS` dan jawaban user tidak kosong; menyegel `final_hash`; tanpa commit |
| `notulen/scripts/notulen.py sync-payload` | argumen dokumen nataflow untuk notulen `FINAL` (bukan `DRAFT`/`DRIFT`): `lookup` (`list_document` bersaring `notulen_key`), `create` (`create_document`, judul `<H1> — <tanggal rapat>`), `update` (`upsert_document` dengan `content_sha256`); isi tanpa frontmatter dan tanpa `## Catatan Asli`; read-only |

Kontrak exit `close`/`approve`/`ref`/`cancel`/`commit`: 0 = tertulis dan ter-commit (atau tanpa git, isinya sudah sama
dengan HEAD, atau diabaikan `.gitignore`), 1 = ditolak, 3 = tertulis tetapi commit gagal (hook, gpg, index terkunci) — baris `COMMIT GAGAL` memuat sebab git dan perintah commit manualnya, lengkap dengan subjeknya.

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
git bila ada, selain itu di direktori kerja. Di repo git, tiap artefak di-commit atomik oleh `ticket.py` dengan
staging path eksplisit (`docs(ticket): ...`); di luar git, commit dilewati dan disebut di Output.

**Ticketdir yang diabaikan git.** Repo bersinkron nataflow (`.claude/nataflow.json` atau `analyst/nataflow.json`
ada, sah maupun rusak) tidak meng-commit tiketnya: `ticket.py new` menulis `analyst/tickets/.gitignore` berisi `*`
bila belum ada. Berkas itu ikut mengabaikan dirinya sendiri, jadi root `.gitignore` tidak tersentuh dan working tree
yang ditagih gerbang `backend:tech-lead`/`frontend:lead` tetap bersih. `TICKET.md` dan `review.md` tetap ditulis ke
disk; tiap commit atas path yang diabaikan dilewati (`commit diabaikan git`, exit 0), dan `check`/`new` melaporkan
`git=diabaikan`. Aturan yang sama berlaku bila user sendiri mengabaikan `analyst/tickets/` di `.gitignore`; tanpa
sinkron, `new` memperingatkan bahwa tiket hanya ada di disk itu.

- **Yang tetap berjalan**: serah terima dinilai dari `approved_seal` di disk, bukan dari riwayat git, dan
  `sync-payload` membaca disk.
- **Yang hilang**: riwayat git tiket. Catatan elisitasi, `requester`, dan tiket yang belum `READY` hanya ada di disk
  lokal, karena nataflow hanya menerima kartu `READY` dan `review.md`. `ticket_source` hanya dapat dipakai engineer
  di clone yang sama.
- **Tiket lama**: berkas yang sudah ter-track tetap ter-track dan tetap di-commit (`new` menyebut jumlahnya).
  Melepasnya keputusan user: `git rm -r --cached analyst/tickets` lalu commit.
- **Kembali meng-commit**: ganti isi `analyst/tickets/.gitignore` lalu commit berkasnya. `new` hanya menulis berkas
  itu bila belum ada, jadi menghapusnya saja membuatnya ditulis lagi.

**Notulen tidak pernah di-commit.** `notulen.py new` menulis `analyst/notulen/.gitignore` (`*`) bila belum ada, di
repo git maupun di luar git, dan `notulen.py` tidak punya jalan commit. Isi berkas itu milik user sesudah ditulis;
bila user mengubahnya sehingga notulen tidak lagi diabaikan, `new` memperingatkan, dan commit tetap urusan user.

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
- **Tiket `TECH`**: `D-{n}`/`C-{n}` dirujuk `TD-{n}`/`TC-{n}` dan dihitung disepakati; BRD tidak dijadwalkan;
  bukti `path:baris` kartu adalah titik awal yang dibuktikan ulang gerbang engineer. Hanya gerbang repo tempat
  tiket tinggal yang menerimanya.
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

Tiket `READY` dapat dicerminkan sebagai task di nataflow. `TICKET.md` di disk tetap satu-satunya sumber
kebenaran; task hanya cermin kartunya, dan tidak ada yang ditulis balik ke `TICKET.md`. Repo yang mengaktifkan
sinkron tidak meng-commit tiketnya (lihat Git), sehingga task inilah satu-satunya salinan kartu di luar disk lokal.

- **Aktif per repo** lewat `.claude/nataflow.json` (ter-commit, dibaca juga oleh `backend`, `frontend`, dan
  `quickdev`): `mcp_server` (default `nataflow-api`), `workspaces` (objek alias → UUID workspace;
  kosong → workspace milik key, satu entri → otomatis, lebih dari satu → user memilih saat tiket pertama kali
  disinkron), `pic_id` (UUID; kosong → pemilik key), dan `repo` (default: remote `origin` ternormalisasi). Berkas
  lama `analyst/nataflow.json` tetap diterima; bila keduanya ada dengan isi berbeda → `GAGAL`. Berkas absen →
  sinkron dilewati; ada tetapi rusak (kunci asing termasuk `workspace_id` tunggal lama, nilai bukan string, alias atau UUID tidak
  sah) → `GAGAL`. Workspace pilihan tidak ditulis ke `TICKET.md`; task yang sudah ada ditemukan di workspace mana
  pun dalam jangkauan key, dan taskdir engineer dari tiket itu menaruh workdir-nya di workspace yang sama.
- **Prasyarat di luar plugin**: server MCP nataflow terdaftar di Claude Code beserta MCP key-nya. Plugin tidak
  mendeklarasikan server dan tidak menyimpan key.
- **Kapan**: `analyst:spec` sesudah `approve` (`READY` tertulis, termasuk bila commit-nya gagal). Prosedurnya
  di `skills/spec/references/nataflow-sync.md`: `ticket.py sync-payload` menyusun seluruh argumen, lalu model
  mencari task lewat `list_task` bersaring `{"source":"analyst","ticket_key":<ticketdir>}` — tidak ada →
  `create_task`, satu → `update_task` (judul, kartu, dan metadata dikirim ulang utuh), lebih dari satu →
  berhenti tanpa menulis. Approve ulang sesudah `reopen` memperbarui task yang sama; tiket baru ber-slug sama
  menjadi task baru karena ticketdir-nya berbeda.
- **Isi**: judul = H1 kartu; deskripsi = kartu (H1 sampai akhir `## Lampiran`) tanpa catatan elisitasi;
  metadata `source`, `ticket_key`, `repo`, `slug`, `type`, `priority`, `approved`, `approved_seal`, `reopened`,
  `category` (tiket `TECH`), dan `external_ref` bila terisi (`repo` tidak ikut saringan pencarian, supaya task lama tetap ditemukan).
  `review.md` (blok `## Ticket Review` terakhir) menempel ke task sebagai dokumen `ticket.review`. Catatan
  elisitasi dan `requester` tetap di disk.
- **Pembatalan**: `/analyst:intake` ("batalkan tiket …") merutekan ke `analyst:spec`, yang menjalankan
  `ticket.py cancel` (`--force` untuk tiket `READY` atas konfirmasi eksplisit). Tiket yang pernah `READY` lalu
  dibatalkan membuat task cerminnya `cancelled`; itu satu-satunya status task yang dikirim analyst.
- **Induk kerja engineer**: taskdir `backend`/`frontend` yang berangkat dari `ticket_source` tiket ini menempel
  ke task yang sama sebagai workdir, beserta artefaknya (`TASK.md`, PRD, brief, `REVIEW.md`, `REPORT.md`).
- **Gagal tidak memblokir**: baris penutup `SPEC — READY` memuat segmen `nataflow <dibuat #<code> | diperbarui
  #<code> | dilewati | GAGAL: <sebab>>`. `GAGAL` tidak menurunkan `READY`; ulangi lewat `/analyst:intake`
  ("sinkron ulang tiket `<ticketdir>`").
- **Notulen**: notulen `FINAL` dicerminkan sebagai dokumen `notes.meeting` di bawah **project** MCP key
  (`get_project_info`), lewat prosedur `skills/notulen/references/nataflow-sync.md`. Identitasnya metadata
  `notulen_key` = path notulendir: `list_document` lebih dulu, lalu `create_document` (judul dikunci saat dibuat) atau
  `upsert_document` ke key yang ditemukan, dan dilewati bila `content_sha256` sama. `workspaces` dan `pic_id` tidak
  berlaku. `GAGAL` tidak menurunkan `FINAL`; ulangi lewat `/analyst:notulen` ("sinkron ulang notulen `<notulendir>`").

## Batas Dengan Plugin Lain

| Kebutuhan | Pakai |
|---|---|
| Menulis tiket dari permintaan pengguna/stakeholder | `analyst` |
| Merapikan catatan kasar rapat menjadi notulen | `analyst` (`notulen`) |
| Mengunci perubahan struktur dari lead engineer sebelum dikerjakan | `analyst` (tipe `TECH`) |
| Kontrak teknis, BRD/PRD berjangkar kode, brief implementasi | `backend` |
| Alur layar, bentuk layar, kontrak layer frontend | `frontend` |
| Perubahan kecil–menengah dengan satu berkas rencana (`plan/<task>.md`), tanpa taskdir | `quickdev` |
| Refaktor kecil, stacktrace dari developer, pertanyaan letak kode | gerbang engineer, bukan `analyst` |

## Sengaja Belum Ada

- **`split`** — pemecahan epic menjadi beberapa tiket beserta ketergantungan formal antar-tiket. Sementara ini
  `intake` memecah permintaan per tujuan pengguna, memproses hingga 5 tujuan sebagai batch berurutan, dan
  mengembalikan sisanya sebagai antrian tiket.
- **Batch lanjutan** — review tiket ke-k berjalan paralel dengan elisitasi tiket berikutnya, pertanyaan gabungan
  lintas tiket, dan batch lebih dari 5 tiket.
- **`acceptance`** — UAT: membaca `REPORT.md` engineer dan memvonis AC tiket dalam bahasa bisnis.
- **Notulen ke tiket** — seksi calon tiket di notulen dan serah terima `D-{n}`/`A-{n}` ke `/analyst:intake`;
  notulen dari transkrip atau rekaman rapat; reviewer independen untuk notulen.
- **`code-scout` di luar elisitasi** — penentuan wilayah backend/frontend di `intake` dan pemeriksaan kartu di `spec`.
- **Sinkron nataflow lanjutan** — status task selesai saat seluruh engineer tuntas (plugin engineer hanya
  menaikkannya ke `in_progress`, karena satu tiket bisa menaungi taskdir backend dan frontend), penghapusan task
  saat tiket dibatalkan, dan catatan elisitasi sebagai dokumen (sengaja tidak dikirim).
