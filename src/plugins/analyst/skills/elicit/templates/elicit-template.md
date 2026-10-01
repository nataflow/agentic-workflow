# ELICIT Template — `elicit`

Rumah kanonik **frontmatter** dan seksi `## Catatan Elisitasi` di `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md` — satu-satunya artefak yang disunting skill; `review.md` di sebelahnya jejak vonis reviewer terakhir, hanya ditulis `ticket.py`. Bagian 1 adalah kerangka yang disalin ke artefak, bagian 2 aturan yang ditagih `skills/_common/validate_doc.py --kind elicit` dan self-test penulis, bagian 3 dan 4 contoh terisi yang **tidak** tersalin ke artefak. `SKILL.md` merujuk ke sini dan dilarang menulis ulang kerangkanya. Seksi kartu di atas catatan (Latar Belakang sampai Lampiran) milik `skills/spec/templates/ticket-template.md`.

`## Catatan Elisitasi` adalah **catatan kerja**, bukan kartu: ia menyimpan permintaan asli, fakta yang sudah terkumpul per pilar, riwayat tanya-jawab, dan pertanyaan yang masih menunggu jawaban. Seksi ini yang membuat elisitasi dapat dilanjutkan lintas sesi, dan satu-satunya masukan tertulis `analyst:spec`. Ia selalu H2 **terakhir**; `spec` menyisipkan kartu di antara H1 dan seksi ini tanpa menyentuh isinya.

---

## 1. Template Kanonik — TICKET.md Awal

`ticket.py new` menulis berkas baru persis kerangka ini — permintaan asli dari `--request`, `request_hash` dihitung skrip — lalu `analyst:elicit` mengisi pilarnya. `tests/analyst/test_ticket_10.py` menagih kerangka skrip sama dengan blok di bawah. Tipe `FEATURE` dan `IMPROVEMENT` (tujuh pilar wajib, dua opsional):

````markdown
---
status: DRAFT
elicitation: OPEN
type: <FEATURE | IMPROVEMENT>
priority: -
slug: <slug ticketdir>
requester: <"nama atau peran peminta">
created: <YYYY-MM-DD>
external_ref: -
domain_terms: []
revision: 0
review: -
review_round: 0
request_hash: <sidik 12 hex permintaan asli>
---

# <judul kerja singkat>

## Catatan Elisitasi

### Permintaan Asli

> <permintaan user apa adanya, tanpa disunting>

### Fakta

#### Masalah
_(belum terjawab)_

#### Aktor
_(belum terjawab)_

#### Kondisi Saat Ini
_(belum terjawab)_

#### Kondisi Diinginkan
_(belum terjawab)_

#### Aturan Bisnis
_(belum terjawab)_

#### Batas Cakupan
_(belum terjawab)_

#### Urgensi
_(belum terjawab)_

#### Kasus Khusus
_(belum terjawab)_

#### Ukuran Keberhasilan
_(belum terjawab)_

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|

### Pertanyaan Terbuka

- Tidak ada.
````

Tipe `BUG` memakai `#### ` pilar berikut di bawah `### Fakta`, urutan persis: `Langkah Reproduksi`, `Yang Diharapkan`, `Yang Terjadi`, `Dampak`, `Urgensi` (wajib), lalu `Lingkungan`, `Batas Cakupan` (opsional). Seksi lain identik.

Tipe `TECH` menambah baris `category: <REFACTOR | DATA_MODEL | ARCHITECTURE | PERFORMANCE | DEPENDENCY>` tepat sesudah `type: TECH` (ditulis `ticket.py new --category`; tipe lain tidak pernah memuatnya), dan memakai pilar berikut, urutan persis: `Masalah Teknis`, `Kondisi Saat Ini`, `Kondisi Target`, `Batasan`, `Batas Cakupan`, `Urgensi` (wajib), lalu `Keputusan`, `Rollout`, `Ukuran Keberhasilan` (opsional). Isi tiap pilar: `references/elicitation-tech.md` bagian 3.

Kepemilikan frontmatter: `type`, `slug`, `requester`, `created`, `request_hash`, dan `elicitation: OPEN` awal ditulis `ticket.py new`; `domain_terms` dan `elicitation: OPEN` saat buka ulang ditulis `elicit`; `elicitation: CLOSED`, `elicit_hash`, dan `elicit_log` ditulis **hanya** `ticket.py close`; `priority`, `external_ref`, dan H1 final ditulis `spec`; `status` (selain `DRAFT` awal), `revision`, `revision_base`, `review`, `review_round`, `approved*`, `reopen*`, `cancel_reason` ditulis **hanya** oleh `ticket.py`; `external_ref` sesudah `READY` hanya lewat `ticket.py ref`. Penulis mana pun menyalin field milik pihak lain apa adanya.

---

## 2. Aturan Validasi

**Mekanis** — ditagih `validate_doc.py --kind elicit`:

1. **Frontmatter**: `status` `DRAFT` atau `READY` (`CANCELLED` hanya ditulis `ticket.py cancel`); `elicitation` `OPEN` atau `CLOSED`; `type` salah satu `FEATURE | IMPROVEMENT | BUG | TECH`; `category` ada **hanya** pada `TECH`, berisi salah satu `REFACTOR | DATA_MODEL | ARCHITECTURE | PERFORMANCE | DEPENDENCY`; `slug` sama dengan slug nama ticketdir; `created` `YYYY-MM-DD`; `requester` terisi; `domain_terms` berupa list — istilah yang tampak teknis tetapi memang kosakata bisnis produk ini, dikonfirmasi peminta (mis. `[API]` untuk produk API mitra). Hanya istilah di list ini yang lolos pemindai kebocoran kartu.
2. **Struktur**: tepat satu H1; `## Catatan Elisitasi` adalah H2 terakhir, berisi empat H3 persis urutan bagian 1; tiap H2 dan H3 muncul sekali (heading ganda menimpa isi yang pertama).
3. **Permintaan asli**: minimal satu baris blockquote `> `, dan hanya blockquote. Bila frontmatter memuat `request_hash` (ditulis `ticket.py new`), kutipannya sama persis dengan saat dimateraikan.
4. **Pilar**: `####` di bawah `### Fakta` persis daftar tipe itu, berurutan. Pilar yang belum terjawab berisi literal `_(belum terjawab)_` — dilarang dikosongkan. Pilar opsional yang sengaja tidak digali berisi `Tidak dibahas — <alasan>`. Tiap pilar muncul sekali. `CLOSED` menuntut nol `_(belum terjawab)_`.
5. **Log**: tabel berheader lima kolom beserta baris pemisah; baris `| n | YYYY-MM-DD | <pertanyaan> | <jawaban> | <sumber> |` bernomor urut dari 1. Nol baris sah bila permintaan asli sudah menjawab seluruh pilar.
6. **Pertanyaan terbuka**: `- Tidak ada.`, atau baris `- **Q-{n}** [MEMBLOKIR | TIDAK MEMBLOKIR]: <pertanyaan> — menunggu: <siapa>` ber-ID unik. `CLOSED` menuntut nol `MEMBLOKIR`.
7. **Placeholder**: nol `TBD`/`TODO`/`diisi nanti` dan nol slot `<...>` di `### Fakta` dan `### Pertanyaan Terbuka` (`TECH`: di luar blok dan span kode — `List<Project>` di sana tipe, bukan slot). `### Permintaan Asli` dan `### Log Tanya-Jawab` dikecualikan — keduanya kutipan mentah yang dilarang disunting.
8. **Asumsi**: `CLOSED` menuntut nol `Asumsi:` di `### Fakta` — di awal maupun di tengah baris, termasuk bentuk tebal — tiap asumsi dikonfirmasi (labelnya dihapus) atau pilarnya kembali ke Phase 2.
9. **Konfirmasi istilah domain**: `CLOSED` menuntut tiap istilah `domain_terms` punya baris `### Log Tanya-Jawab` berjawaban `Ya` yang mengutip istilahnya: `| n | <tanggal> | Apakah "<istilah>" nama produk? | Ya | <peminta> |`. Kemunculan di `### Permintaan Asli` saja tidak cukup — istilah teknis yang diucapkan peminta justru dirumuskan ulang sebagai perilaku (panduan bagian 3).

**Semantik** — self-test penulis sebelum `elicitation: CLOSED`, tidak dapat ditagih skrip:

10. Tiap fakta berasal dari permintaan asli atau baris log — dilarang mengisi pilar dengan tebakan analis. Fakta yang disimpulkan, bukan dikatakan, ditulis `Asumsi: <...>` dan dikonfirmasi di Phase 4 `SKILL.md`.
11. `Aktor` menyebut peran konkret (Kasir, Admin Cabang, Pembeli), bukan "user". `Aturan Bisnis` berangka atau berkondisi pasti ("maksimal 3 kali per hari"), bukan kata sifat ("secukupnya").
12. Pertanyaan `MEMBLOKIR` ⇔ jawabannya mengubah `Aturan Bisnis`, `Kondisi Diinginkan`, `Batas Cakupan`, (BUG) `Yang Diharapkan`, atau (TECH) `Kondisi Target`/`Batasan`, atau (TECH) bukti kode bertentangan dengan klaim peminta. Selain itu `TIDAK MEMBLOKIR` dan akan dibawa `spec` sebagai asumsi.
13. Nomor `Q-{n}` tidak dipakai ulang sesudah terjawab; jawabannya pindah ke log.
14. Nol istilah teknis rekaan analis. Istilah teknis yang **diucapkan** peminta boleh terekam di log apa adanya, tetapi pilar merumuskannya ulang sebagai perilaku yang dilihat pengguna.
15. `Kondisi Diinginkan` (`FEATURE`/`IMPROVEMENT`) diawali `Bentuk hasil: <layar | API | proses otomatis | laporan>` (panduan bagian 6). Pada bentuk API, `Aktor` menyebut pemanggilnya, dan peran bisnis yang datanya dibatasi tercatat di `Aturan Bisnis`, bukan sebagai pemakai.
16. **`TECH`**: butir 11 dan 14 tidak berlaku — peminta engineer dan istilah teknis adalah bahasanya. Sebagai gantinya: tiap fakta `Kondisi Saat Ini` membawa `` `path:baris` `` yang sudah dibaca di repo ini; `Kondisi Target` berupa struktur akhir, bukan urutan langkah; yang wajib tergali untuk `category`-nya (`references/elicitation-tech.md` bagian 4) tercatat di pilar mana pun.

---

## 3. Contoh Terisi — `cicilan-pembayaran` (tidak tersalin ke artefak)

Keadaan sesudah elisitasi ditutup `ticket.py close`, sebelum `spec` menulis kartu. `request_hash` ditulis `ticket.py new`; `elicit_hash` dan `elicit_log` ditulis `close` — nilainya dihitung skrip, bukan diketik (`tests/analyst/test_ticket.py` menagih contoh ini lolos `check --gate spec`):

````markdown
---
status: DRAFT
elicitation: CLOSED
type: FEATURE
priority: -
slug: cicilan-pembayaran
requester: Rina (Head of Sales)
created: 2026-09-23
external_ref: -
domain_terms: []
revision: 0
review: -
review_round: 0
request_hash: a20e9c1ffc3c
elicit_hash: cd31728655d6
elicit_log: 3
---

# Pembayaran cicilan untuk pelanggan korporat

## Catatan Elisitasi

### Permintaan Asli

> Pelanggan korporat sering minta bayar invoice besar dicicil, sekarang tim finance catat manual di spreadsheet. Tolong bikin fitur cicilan.

### Fakta

#### Masalah
Invoice korporat di atas Rp 50 juta sering dibayar bertahap; tim Finance mencatat cicilan di spreadsheet terpisah sehingga status lunas di sistem tidak akurat. Sekitar 40 invoice per bulan, ±6 jam kerja Finance per minggu untuk rekonsiliasi.

#### Aktor
- Admin Finance — membuat dan mengubah jadwal cicilan.
- Pelanggan Korporat — melihat jadwal dan sisa tagihan di portal.
- Sales — hanya melihat status, dilarang mengubah jadwal.

#### Kondisi Saat Ini
Invoice hanya berstatus Belum Bayar atau Lunas. Pembayaran sebagian dicatat Finance di spreadsheet; portal pelanggan tetap menampilkan Belum Bayar.

#### Kondisi Diinginkan
Bentuk hasil: layar — invoice di aplikasi Finance dan portal pelanggan.
Admin Finance dapat memecah satu invoice menjadi beberapa cicilan bertanggal jatuh tempo; tiap pembayaran mengurangi sisa tagihan dan invoice berstatus Lunas saat sisa nol.

#### Aturan Bisnis
- Cicilan hanya untuk invoice ≥ Rp 50.000.000.
- Maksimal 6 cicilan per invoice; jarak jatuh tempo minimal 14 hari.
- Jadwal tidak dapat diubah sesudah cicilan pertama dibayar.

#### Batas Cakupan
Hanya pelanggan korporat; denda keterlambatan ditunda ke fase berikutnya.

#### Urgensi
Tinggi — dua klien besar menjadikan fitur ini syarat perpanjangan kontrak yang ditandatangani 3 minggu lagi.

#### Kasus Khusus
Pembayaran melebihi nominal cicilan dialokasikan ke cicilan berikutnya.

#### Ukuran Keberhasilan
Jam rekonsiliasi Finance turun dari ±6 jam menjadi ≤1 jam per minggu.

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|
| 1 | 2026-09-23 | Invoice mana yang boleh dicicil? | Di atas 50 juta, korporat saja | Rina |
| 2 | 2026-09-23 | Berapa cicilan maksimal? | 6, jarak minimal 2 minggu | Rina |
| 3 | 2026-09-24 | Jadwal boleh diubah? | Tidak sesudah cicilan pertama dibayar | Budi (Finance) |

### Pertanyaan Terbuka

- **Q-2** [TIDAK MEMBLOKIR]: Apakah pelanggan menerima pengingat sebelum jatuh tempo? — menunggu: Rina
````

Pembanding pilar yang **gugur** di butir 11: `#### Aturan Bisnis` berisi `Cicilan untuk invoice yang nominalnya besar` — kata sifat tanpa ambang; engineer tidak dapat mengujinya.

---

## 4. Contoh Terisi `TECH` — `relasi-project-workspace` (tidak tersalin ke artefak)

Tiket `TECH` `DATA_MODEL` dari lead engineer, sesudah `ticket.py close`. Bukti `path:baris` menunjuk berkas repo tempat tiket tinggal (`tests/analyst/test_ticket_17.py` menagih contoh ini, bersama kartu bagian 4 `ticket-template.md`, lolos kedua validator dan `check --gate spec`):

````markdown
---
status: DRAFT
elicitation: CLOSED
type: TECH
category: DATA_MODEL
priority: -
slug: relasi-project-workspace
requester: "Budi (Lead Engineer)"
created: 2026-10-01
external_ref: -
domain_terms: []
revision: 0
review: -
review_round: 0
request_hash: e0670009f586
elicit_hash: e200a21aa9e2
elicit_log: 3
---

# Relasi project dan workspace

## Catatan Elisitasi

### Permintaan Asli

> Project perlu bisa ada di lebih dari satu workspace. Sekarang workspace_id nempel di projects, tolong rapikan jadi many-to-many. Kontrak API jangan berubah.

### Fakta

#### Masalah Teknis
Relasi project–workspace satu-ke-banyak memaksa tim menduplikasi project untuk kebutuhan lintas workspace; tiga kali terjadi kuartal ini dan tiap duplikasi memecah riwayat task.

#### Kondisi Saat Ini
- Kolom `workspace_id` menempel di model project (`internal/project/model.go:12`).
- Query daftar project memfilter langsung ke kolom itu (`internal/project/repository.go:40-48`).

#### Kondisi Target
Tabel penghubung `project_workspaces` berprimary key gabungan; kolom `workspace_id` di `projects` dihapus sesudah backfill.

#### Batasan
Bentuk respons daftar project di REST dan MCP tidak berubah; migrasi wajib reversible tanpa kehilangan data.

#### Batas Cakupan
Izin per workspace atas project ditunda ke tiket terpisah.

#### Urgensi
Fitur berbagi project kuartal depan bergantung pada relasi ini.

#### Keputusan
Tabel penghubung dipilih karena FK dan indeks tetap ditegakkan database; kolom array `workspace_ids` ditolak karena tanpa FK.

#### Rollout
Dua rilis: tambah tabel beserta backfill dan ubah repository, lalu hapus kolom lama di rilis berikutnya. Migrasi turun hanya sah selama rilis 1, sebelum fitur berbagi dibuka.

#### Ukuran Keberhasilan
Tidak dibahas — acceptance criteria sudah memuat alat ukurnya.

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|
| 1 | 2026-10-01 | Data lama: tiap project dipindah ke tabel penghubung dengan workspace sekarang? | Ya, backfill satu baris per project | Budi (Lead Engineer) |
| 2 | 2026-10-01 | Kolom lama dihapus di rilis yang sama atau berikutnya? | Berikutnya, supaya bisa mundur | Budi (Lead Engineer) |
| 3 | 2026-10-01 | Bila migrasi turun sesudah ada project bertaut ke dua workspace, tautan mana yang dipertahankan? | Migrasi turun hanya sah selama rilis 1, sebelum fitur berbagi dibuka; saat itu tiap project masih satu tautan | Budi (Lead Engineer) |

### Pertanyaan Terbuka

- Tidak ada.
````

Pembanding pilar yang **gugur** di butir 16: `#### Kondisi Saat Ini` berisi `Relasinya masih one-to-many di model project` — klaim tanpa `path:baris`; reviewer dan engineer tidak dapat memastikan analyst benar-benar membacanya.
