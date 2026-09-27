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
/plugin install analyst@fakhrulnugroho
```

Prasyarat: `python3` ≥ 3.9. `git` opsional (lihat seksi Git). Lihat juga `README.md` di root repo.

## Tiga Skill, Satu Subagent

| Skill | Peran | Menulis | Dikunci oleh |
|---|---|---|---|
| `analyst:intake` | gerbang: wilayah, tipe, ukuran, duplikat, pemulihan ticketdir | — | — |
| `analyst:elicit` | tanya-jawab dengan peminta, direkam tiap giliran | `TICKET.md` — frontmatter + `## Catatan Elisitasi` | `elicitation: CLOSED` + `validate_doc.py --kind elicit` |
| `analyst:spec` | penyusunan kartu, review independen, persetujuan user | `TICKET.md` — kartu di atas catatan | `ticket.py approve` → `READY` |

Hanya `intake` yang muncul di menu `/`. `elicit` dan `spec` ber-`user-invocable: false`: model memanggilnya
lewat tool Skill sesuai keadaan ticketdir, dan pemulihan tiket (melanjutkan elisitasi, merevisi, membuka ulang)
selalu dimulai dari `/analyst:intake`.

`ticket-reviewer` (`agents/ticket-reviewer.md`) adalah pembaca independen read-only yang memvonis draft
kartu `PASS`/`BLOCKED` terhadap catatan elisitasi di berkas yang sama sebelum diajukan ke user; ia didispatch langsung lewat
`skills/spec/dispatcher/reviewer.md`, tanpa skill pembungkus.

## Workflow

```
permintaan ──► intake ──┬─► di luar wilayah (kerja teknis murni) ──► backenddev:tech-lead / frontenddev:lead
                        ├─► status tiket ──────────────────────────► jawaban, berhenti
                        │
                        └─► elicit ─► ticket.py new ─► TICKET.md (elicitation: OPEN)
                              │        tanya-jawab ≤3/giliran, tulis tiap giliran (≤5 giliran per sesi)
                              │        menunggu jawaban pihak lain → TERTAHAN, lanjut di sesi berikutnya
                              │        konfirmasi fakta → elicitation: CLOSED → commit
                              ▼
                            spec ─► kartu DRAFT di atas catatan → validate_doc → ticket-reviewer (≤2 ronde)
                                    → commit → AskUserQuestion → ticket.py approve → READY (+ commit)
                                                                   │
                    ticket_source: <ticketdir>/TICKET.md ke ──┘ backenddev:tech-lead / frontenddev:lead
```

Permintaan yang sudah lengkap tetap melewati `elicit`: fakta diisi dari permintaan asli, dikonfirmasi sekali,
lalu ditutup tanpa satu pertanyaan pun. Dengan begitu `spec` dan `ticket-reviewer` selalu punya satu sumber
kebenaran tertulis.

## Artefak

```
./analyst/
  tickets/
    2609231400-cicilan-pembayaran/
      TICKET.md   satu-satunya artefak yang disunting skill
      review.md   blok `## Ticket Review` terakhir (ditulis `ticket.py review --report`)
```

`TICKET.md` punya dua bagian dengan dua pemilik dan dua status di frontmatter:

```
---
status: DRAFT → READY          ← ticket.py (approve / reopen / cancel)
elicitation: OPEN → CLOSED     ← analyst:elicit
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
| `_common/ticket.py check --gate elicit\|spec` | prasyarat gate atas satu ticketdir; mencetak `root=` (path ticketdir relatif root, bukan cwd) dan, untuk draft, `sidik` (slot prompt reviewer), `review_basi` (bagian yang berubah sesudah review), serta `review_report` |
| `_common/validate_doc.py --kind elicit` | `## Catatan Elisitasi`: struktur, pilar per tipe, log bernomor, `CLOSED` ⇒ nol pilar kosong, nol pertanyaan memblokir, nol baris `Asumsi:`, dan tiap `domain_terms` berjejak di permintaan asli atau log |
| `_common/validate_doc.py --kind ticket` | kartu: struktur per tipe, AC Given/When/Then, BR terpikul AC, nol placeholder, **nol kebocoran teknis** |
| `_common/ticket.py review` | vonis `PASS`/`BLOCKED` **wajib** membawa blok reviewer (`--report`): `- Verdict:` sama dengan `--verdict`, dan `- Sidik:` (disalin reviewer dari prompt) sama dengan sidik `<kartu>/<catatan elisitasi>` di disk — draft yang berubah sesudah dispatch ditolak; blok disimpan ke `review.md`; ditolak bila salah satu validator `FAIL`; plafon 2 ronde per revisi, dibuka ulang bila catatan elisitasi berubah |
| `_common/ticket.py approve` | `READY` hanya bila kedua validator (`ticket`, `elicit`) `PASS`, `elicitation: CLOSED`, **dan** vonis review `PASS` atas sidik kartu dan catatan elisitasi sekarang; menulis `approved_hash` dan `approved_seal` (segel yang dibaca engineer) |
| `_common/ticket.py revise` / `reopen` / `cancel` | plafon 3 revisi per basis fakta; buka ulang tiket `READY`; tutup ticketdir (direktori kosong dihapus; tiket `READY` hanya dengan `--force`; di-commit `docs(ticket): batalkan TICKET <slug>`) |
| `_common/ticket.py ref` | isi `external_ref` pada `DRAFT`/`READY` tanpa `DRIFT`, commit `docs(ticket): ref TICKET <slug>` |

Kontrak exit `approve`/`ref`/`cancel`: 0 = tertulis dan ter-commit (atau tanpa git), 1 = ditolak, 3 = tertulis tetapi
commit gagal — baris `COMMIT GAGAL` memuat sebab git dan perintah commit manualnya, lengkap dengan subjeknya.

Pemindai kebocoran teknis menolak istilah sistem (endpoint, database, query, nama framework, `API`, …), path
berkas, `file:baris`, metode dan kode status HTTP, identifier `snake_case`/`camelCase`, dan blok kode di kartu, di luar
`## Lampiran` dan `## Catatan Elisitasi` (permintaan asli dan log adalah kutipan mentah). Teks dalam tanda kutip dikecualikan — itu tulisan yang dilihat pengguna. Kata yang bentrok
dengan kosakata bisnis Indonesia (kereta *api*, *skema* cicilan, pengiriman *express*) sengaja tidak didaftar,
dan istilah yang memang kosakata produk (mis. produk API untuk mitra, aplikasi `myPertamina`) diizinkan lewat
`domain_terms` — dicatat oleh elisitasi sesudah dikonfirmasi peminta, baru boleh dipakai kartu.

Sidik review dihitung per bagian — kartu (beserta `type`, `priority`) dan catatan elisitasi (beserta `type`,
`domain_terms`) — sehingga suntingan di bagian mana pun membuat vonis basi. `approve` memateraikan sidik berkas
utuh (`approved_hash`) dan segel serah-terima (`approved_seal`). Tiket `READY` yang disunting sesudah disetujui terbaca `DRIFT`: sidik atau segelnya tidak lagi sama. Perubahan resmi dimulai
dari `/analyst:intake`, yang merutekan ke `analyst:spec` (reopen) untuk mengulang review dan persetujuan.

## Git

Repo git **tidak** wajib — plugin dapat dipakai di folder dokumen biasa. Ruang kerja berakar di root worktree
git bila ada, selain itu di direktori kerja. Di repo git, tiap artefak di-commit atomik dengan staging path
eksplisit (`docs(ticket): ...`); di luar git, commit dilewati dan disebut di Output.

## Serah Terima ke Engineer

Tiket `READY` diserahkan lewat parameter `ticket_source` = path `<ticketdir>/TICKET.md` ke
`backenddev:tech-lead` dan/atau `frontenddev:lead` (baris penutup `SPEC — READY` memuatnya). Kontraknya:

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
  `backenddev:analyst` tidak menjadwalkan BRD hanya karena fakta itu; bila BRD tetap terbit karena fakta di
  luar tiket, `business-analysis` menyerap `TBR-{n}` tanpa menanyakannya ulang (`— Asal: TBR-{m}`).

`ticket_seal` di `_common/analyst_lib.py` disalin apa adanya ke `_common/precondition_lib.py` backenddev dan
frontenddev (`tests/test_a1_ticket_source.py` menagih ketiganya identik); mengubah segel atau subjek commit
`approve`/`ref` berarti mengubah ketiganya bersamaan.

Engineer menerbitkan `TASK.md` teknisnya sendiri —
lengkap dengan `file:baris`, alat ukur teknis, dan ledger — dari tiket itu. Nama `TICKET.md` sengaja berbeda
dari `TASK.md`: kontraknya bertolak belakang, dan keduanya tidak pernah tinggal di direktori yang sama.

Hook SessionStart `backenddev`/`frontenddev` mengecualikan permintaan yang memanggil atau melanjutkan
`analyst:*`. Panggil `/analyst:intake` untuk memulai; susulan di tengah elisitasi tetap ditangani analyst.
Untuk repo yang hanya memakai analyst, tulis `.claude/workflow` tanpa nama plugin engineer (mis. berisi
`analyst`) — hook kedua plugin engineer lalu diam di repo itu.

## Batas Dengan Plugin Lain

| Kebutuhan | Pakai |
|---|---|
| Menulis tiket dari permintaan pengguna/stakeholder | `analyst` |
| Kontrak teknis, BRD/PRD berjangkar kode, brief implementasi | `backenddev` |
| Alur layar, bentuk layar, kontrak layer frontend | `frontenddev` |
| Perubahan kecil–menengah dengan satu berkas rencana (`plan/<task>.md`), tanpa taskdir | `quickdev` |
| Refaktor, upgrade pustaka, stacktrace dari developer | gerbang engineer, bukan `analyst` |

## Sengaja Belum Ada

- **`split`** — pemecahan epic menjadi beberapa tiket. Sementara ini `intake` memilih satu tujuan per tiket dan
  mengembalikan sisanya sebagai antrian tiket.
- **`acceptance`** — UAT: membaca `REPORT.md` engineer dan memvonis AC tiket dalam bahasa bisnis.
