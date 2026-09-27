# ELICIT Template — `elicit`

Rumah kanonik **frontmatter** dan seksi `## Catatan Elisitasi` di `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md` — satu-satunya artefak yang disunting skill; `review.md` di sebelahnya jejak vonis reviewer terakhir, hanya ditulis `ticket.py`. Bagian 1 adalah kerangka yang disalin ke artefak, bagian 2 aturan yang ditagih `skills/_common/validate_doc.py --kind elicit` dan self-test penulis, bagian 3 contoh terisi yang **tidak** tersalin ke artefak. `SKILL.md` merujuk ke sini dan dilarang menulis ulang kerangkanya. Seksi kartu di atas catatan (Latar Belakang sampai Lampiran) milik `skills/spec/templates/ticket-template.md`.

`## Catatan Elisitasi` adalah **catatan kerja**, bukan kartu: ia menyimpan permintaan asli, fakta yang sudah terkumpul per pilar, riwayat tanya-jawab, dan pertanyaan yang masih menunggu jawaban. Seksi ini yang membuat elisitasi dapat dilanjutkan lintas sesi, dan satu-satunya masukan tertulis `analyst:spec`. Ia selalu H2 **terakhir**; `spec` menyisipkan kartu di antara H1 dan seksi ini tanpa menyentuh isinya.

---

## 1. Template Kanonik — TICKET.md Awal

`analyst:elicit` menulis berkas baru persis kerangka ini. Tipe `FEATURE` dan `IMPROVEMENT` (tujuh pilar wajib, dua opsional):

````markdown
---
status: DRAFT
elicitation: OPEN
type: <FEATURE | IMPROVEMENT>
priority: -
slug: <slug ticketdir>
requester: <nama atau peran peminta>
created: <YYYY-MM-DD>
external_ref: -
domain_terms: []
revision: 0
review: -
review_round: 0
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

Kepemilikan frontmatter: `elicitation`, `type`, `slug`, `requester`, `created`, `domain_terms` ditulis `elicit`; `priority`, `external_ref`, dan H1 final ditulis `spec`; `status` (selain `DRAFT` awal), `revision`, `revision_base`, `review`, `review_round`, `approved*`, `reopen*`, `cancel_reason` ditulis **hanya** oleh `ticket.py`; `external_ref` sesudah `READY` hanya lewat `ticket.py ref`. Penulis mana pun menyalin field milik pihak lain apa adanya.

---

## 2. Aturan Validasi

**Mekanis** — ditagih `validate_doc.py --kind elicit`:

1. **Frontmatter**: `status` `DRAFT` atau `READY` (`CANCELLED` hanya ditulis `ticket.py cancel`); `elicitation` `OPEN` atau `CLOSED`; `type` salah satu `FEATURE | IMPROVEMENT | BUG`; `slug` sama dengan slug nama ticketdir; `created` `YYYY-MM-DD`; `requester` terisi; `domain_terms` berupa list — istilah yang tampak teknis tetapi memang kosakata bisnis produk ini, dikonfirmasi peminta (mis. `[API]` untuk produk API mitra). Hanya istilah di list ini yang lolos pemindai kebocoran kartu.
2. **Struktur**: tepat satu H1; `## Catatan Elisitasi` adalah H2 terakhir, berisi empat H3 persis urutan bagian 1.
3. **Permintaan asli**: minimal satu baris blockquote `> `, dan hanya blockquote.
4. **Pilar**: `####` di bawah `### Fakta` persis daftar tipe itu, berurutan. Pilar yang belum terjawab berisi literal `_(belum terjawab)_` — dilarang dikosongkan. Pilar opsional yang sengaja tidak digali berisi `Tidak dibahas — <alasan>`. `CLOSED` menuntut nol `_(belum terjawab)_`.
5. **Log**: tabel berheader lima kolom beserta baris pemisah; baris `| n | YYYY-MM-DD | <pertanyaan> | <jawaban> | <sumber> |` bernomor urut dari 1. Nol baris sah bila permintaan asli sudah menjawab seluruh pilar.
6. **Pertanyaan terbuka**: `- Tidak ada.`, atau baris `- **Q-{n}** [MEMBLOKIR | TIDAK MEMBLOKIR]: <pertanyaan> — menunggu: <siapa>` ber-ID unik. `CLOSED` menuntut nol `MEMBLOKIR`.
7. **Placeholder**: nol `TBD`/`TODO`/`diisi nanti` dan nol slot `<...>` di `### Fakta` dan `### Pertanyaan Terbuka`. `### Permintaan Asli` dan `### Log Tanya-Jawab` dikecualikan — keduanya kutipan mentah yang dilarang disunting.
8. **Asumsi**: `CLOSED` menuntut nol baris `Asumsi:` di `### Fakta` — tiap asumsi dikonfirmasi (labelnya dihapus) atau pilarnya kembali ke Phase 2.
9. **Jejak istilah domain**: `CLOSED` menuntut tiap istilah `domain_terms` muncul di `### Permintaan Asli` atau di baris `### Log Tanya-Jawab` (baris konfirmasinya).

**Semantik** — self-test penulis sebelum `elicitation: CLOSED`, tidak dapat ditagih skrip:

10. Tiap fakta berasal dari permintaan asli atau baris log — dilarang mengisi pilar dengan tebakan analis. Fakta yang disimpulkan, bukan dikatakan, ditulis `Asumsi: <...>` dan dikonfirmasi di Phase 4 `SKILL.md`.
11. `Aktor` menyebut peran konkret (Kasir, Admin Cabang, Pembeli), bukan "user". `Aturan Bisnis` berangka atau berkondisi pasti ("maksimal 3 kali per hari"), bukan kata sifat ("secukupnya").
12. Pertanyaan `MEMBLOKIR` ⇔ jawabannya mengubah `Aturan Bisnis`, `Kondisi Diinginkan`, `Batas Cakupan`, atau (BUG) `Yang Diharapkan`. Selain itu `TIDAK MEMBLOKIR` dan akan dibawa `spec` sebagai asumsi.
13. Nomor `Q-{n}` tidak dipakai ulang sesudah terjawab; jawabannya pindah ke log.
14. Nol istilah teknis rekaan analis. Istilah teknis yang **diucapkan** peminta boleh terekam di log apa adanya, tetapi pilar merumuskannya ulang sebagai perilaku yang dilihat pengguna.

---

## 3. Contoh Terisi — `cicilan-pembayaran` (tidak tersalin ke artefak)

Keadaan sesudah elisitasi ditutup, sebelum `spec` menulis kartu:

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
elicit_hash: 1b0cbb4c40c4
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
