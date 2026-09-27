---
status: DRAFT
elicitation: CLOSED
type: FEATURE
priority: HIGH
slug: cicilan
requester: Rina (Head of Sales)
created: 2026-09-23
external_ref: -
domain_terms: []
revision: 0
review: -
review_round: 0
elicit_hash: 349039f58360
elicit_log: 1
---

# Admin Finance dapat mencatat pembayaran invoice korporat secara cicilan

## Latar Belakang

Invoice korporat di atas Rp 50 juta sering dibayar bertahap, tetapi sistem hanya mengenal status Belum Bayar dan Lunas.

## User Story

Sebagai Admin Finance, saya ingin memecah invoice korporat menjadi beberapa cicilan, agar sisa tagihan selalu akurat.

## Acceptance Criteria

- **AC-1**: Given invoice korporat bernilai Rp 60.000.000, when Admin Finance membuat jadwal 3 cicilan, then invoice menampilkan 3 baris cicilan (BR-1)
- **AC-2**: Given invoice bernilai Rp 40.000.000, when Admin Finance membuka invoice itu, then pilihan "Buat Cicilan" tidak tersedia (BR-1)

## Aturan Bisnis

- **BR-1**: Cicilan hanya untuk invoice pelanggan korporat bernilai minimal Rp 50.000.000.

## Di Luar Cakupan

- Denda keterlambatan — ditunda ke fase berikutnya

## Pertanyaan Terbuka

- Tidak ada.

## Lampiran

- Tidak ada.

## Catatan Elisitasi

### Permintaan Asli

> Pelanggan korporat sering minta bayar invoice besar dicicil. Tolong bikin fitur cicilan.

### Fakta

#### Masalah
Invoice korporat di atas Rp 50 juta sering dibayar bertahap; Finance mencatatnya di spreadsheet.

#### Aktor
- Admin Finance — membuat jadwal cicilan.

#### Kondisi Saat Ini
Invoice hanya berstatus Belum Bayar atau Lunas.

#### Kondisi Diinginkan
Admin Finance dapat memecah satu invoice menjadi beberapa cicilan.

#### Aturan Bisnis
- Cicilan hanya untuk invoice minimal Rp 50.000.000.

#### Batas Cakupan
Hanya pelanggan korporat.

#### Urgensi
Tinggi — dua klien besar menunggu.

#### Kasus Khusus
Tidak dibahas — peminta belum punya contoh.

#### Ukuran Keberhasilan
Tidak dibahas — belum diukur.

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|
| 1 | 2026-09-23 | Invoice mana yang boleh dicicil? | Di atas 50 juta | Rina |

### Pertanyaan Terbuka

- Tidak ada.
