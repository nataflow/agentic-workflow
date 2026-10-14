# CHARTER Template — `spec`

Rumah kanonik **kartu enam pilar** di `product/<slug>/CHARTER.md`, ditulis `product:spec` di antara H1 dan
`## Catatan Elisitasi`. Bagian 1 bentuk kartu per mode, bagian 2 aturan yang ditagih
`skills/_common/validate_doc.py --kind charter` dan self-test penulis, bagian 3 contoh terisi `IMPROVEMENT` yang
**tidak** tersalin ke artefak. Frontmatter dan catatan elisitasi milik `skills/discover/templates/charter-skeleton.md`.

---

## 1. Bentuk Kartu

H1 final ≤ 12 kata, lalu enam H2 persis urutan ini, lalu `## Catatan Elisitasi` tanpa disentuh:

````markdown
# <judul inisiatif>

## Purpose

<2–5 kalimat: masalah yang diselesaikan, siapa yang mengalaminya, seberapa sering atau mahal, kenapa sekarang>

## Actors

- **<Nama Peran>** — <tanggung jawab, yang boleh dan tidak boleh dilakukan>

## Business Process

1. **<Aktor>** <aksi>
2. **Sistem** <reaksi yang terlihat>
   - Bila <kondisi cabang>, <yang terjadi>
3. **<Aktor>** <aksi sampai hasil akhir>

## Business Rules

- **BR-1**: <aturan beserta angka atau ambang> — pengecualian: <pengecualian, atau `tidak ada`>

## Success Criteria

- **SC-1**: <indikator> — ukuran: <angka, persen, durasi, atau ambang> <kapan atau bagaimana diukur>

## Scope

### Termasuk

- **S1**: <butir kerja versi pertama>

### Tidak Termasuk

- <yang tidak dikerjakan> — <alasan>
````

Variasi per mode:

| Pilar | `NEW_PRODUCT` | `NEW_FEATURE` | `IMPROVEMENT` |
|---|---|---|---|
| Actors | tanpa tanda | tiap aktor `**<Nama>** [ADA]` atau `[BARU]` | sama dengan `NEW_FEATURE` |
| Business Process | satu daftar langkah | satu daftar langkah | `### Kondisi Sekarang` (minimal satu `` `path:baris` ``) lalu `### Kondisi Target`, masing-masing daftar langkah |
| Business Rules | tanpa tanda | tanpa tanda | tiap aturan `**BR-n** [TETAP]`, `[UBAH]`, atau `[BARU]` |
| Bukti `path:baris` | dilarang | boleh, wajib ada di repo | wajib di Kondisi Sekarang, wajib ada di repo |

Aturan bentuk:

- Tiap butir Actors, `BR-n`, `SC-n`, dan `S<n>` ditulis dalam **satu baris**; validator membaca per baris.
- `Sistem` boleh menjadi aktor langkah tanpa didaftarkan di Actors; aktor lain wajib terdaftar persis.
- Cabang (gagal, batal, ditolak) ditulis sebagai sub-butir berindentasi di bawah langkahnya.
- Tanpa aturan khusus → satu baris `- Tidak ada aturan khusus — <alasan dari catatan>`.
- `S<n>` adalah **ID tetap** untuk serah-terima: kelak tiap butir Scope dipetakan ke tiket tanpa mengubah charter.
  Dilarang menomori ulang butir yang sudah ada di charter yang pernah `APPROVED`. Butir yang dibatalkan pindah ke
  Tidak Termasuk **dengan ID-nya**: `- **S2**: <butir> — <alasan dibatalkan>`. Validator menuntut gabungan ID
  Termasuk dan yang dibatalkan unik dan tanpa celah dari S1; butir baru memakai ID berikutnya sesudah yang terbesar.

---

## 2. Aturan Validasi

Ditagih `validate_doc.py --kind charter` (mekanis):

1. Frontmatter sah, status bukan `ELICITATION`, `revision` bilangan.
2. Satu H1 ≤ 12 kata; enam H2 pilar persis urutan, lalu `## Catatan Elisitasi`; tiap heading sekali.
3. Purpose tidak kosong.
4. Actors: format baris, tanpa nama ganda, `Sistem` tidak didaftarkan; tanda `[ADA]/[BARU]` wajib di mode codebase dan
   dilarang di `NEW_PRODUCT`.
5. Business Process: langkah `n. **<Aktor>** <aksi>` bernomor urut dari 1, minimal 2 langkah per daftar, aktor
   terdaftar atau `Sistem`; sub-heading hanya di `IMPROVEMENT`, persis `Kondisi Sekarang` lalu `Kondisi Target`.
6. Business Rules: `BR-n` urut dari 1 dengan `— pengecualian:`; tanda wajib di `IMPROVEMENT`, dilarang di mode lain.
7. Success Criteria: 1–8 `SC-n` urut dari 1, tiap `— ukuran:` memuat angka.
8. Scope: `### Termasuk` dengan `S<n>` unik berurutan naik, `### Tidak Termasuk` minimal satu butir beralasan; gabungan ID Termasuk dan `S<n>` yang dibatalkan di Tidak Termasuk tanpa celah dari S1.
9. Nol placeholder di kartu.
10. Bukti kode per tabel bagian 1.
11. Charter `APPROVED`: isi sama dengan yang dimateraikan `approved_hash`.

Self-test semantik penulis sebelum dispatch reviewer (dinilai juga oleh `charter-reviewer`):

12. Tiap kalimat kartu berakar pada pilar atau baris log catatan elisitasi; tidak ada aktor, langkah, aturan,
    ukuran, atau butir Scope karangan analis.
13. Tiap fakta pilar catatan dipikul kartu atau disebut di Tidak Termasuk.
14. Purpose dan Actors konsisten dengan `### Konteks Awal`: segmen dan masalahnya sama.
15. Alur berjalan dari pemicu sampai hasil akhir; tiap aturan muncul di alur sebagai langkah atau cabang yang
    menegakkannya.
16. Tiap SC mengukur berkurangnya masalah di Purpose, bukan selesainya pekerjaan.
17. Tiap `S<n>` dapat dirilis dan diuji sebagai satu butir kerja; butir yang memuat dua tujuan dipecah.
18. Bahasa bisnis: tanpa penyimpanan data, teknologi, endpoint, atau struktur layar internal.

---

## 3. Contoh Terisi `IMPROVEMENT` — `retur-barang` (tidak tersalin ke artefak)

```markdown
# Persingkat persetujuan retur barang di toko cabang

## Purpose

Kepala toko cabang menunggu rata-rata 2 hari untuk menyetujui retur karena setiap retur, sekecil apa pun, harus
disetujui manajer area. Pelanggan yang menunggu sering membatalkan pembelian berikutnya; 30% keluhan bulan lalu
berasal dari retur yang tertunda.

## Actors

- **Kasir** [ADA] — mencatat permintaan retur; tidak boleh menyetujui
- **Kepala Toko** [ADA] — menyetujui retur sampai batas nominal BR-1
- **Manajer Area** [ADA] — menyetujui retur di atas batas BR-1

## Business Process

### Kondisi Sekarang

1. **Kasir** mencatat permintaan retur di layar retur `src/retur/form.go:40-58`
2. **Manajer Area** menyetujui setiap retur dari layar persetujuan `src/retur/approval.go:21`
3. **Kasir** mengembalikan uang sesudah persetujuan

### Kondisi Target

1. **Kasir** mencatat permintaan retur beserta nominalnya
2. **Kepala Toko** menyetujui retur sampai Rp500.000
   - Bila nominal di atas Rp500.000, retur diteruskan ke Manajer Area (BR-1)
3. **Kasir** mengembalikan uang sesudah persetujuan

## Business Rules

- **BR-1** [UBAH]: Retur sampai Rp500.000 cukup disetujui Kepala Toko; di atasnya oleh Manajer Area — pengecualian: barang rusak dari pemasok selalu ke Manajer Area
- **BR-2** [TETAP]: Retur hanya untuk pembelian 7 hari terakhir — pengecualian: tidak ada

## Success Criteria

- **SC-1**: Retur kecil disetujui di toko — ukuran: 80% retur ≤ Rp500.000 disetujui ≤ 2 jam, diukur 1 bulan sesudah rilis
- **SC-2**: Keluhan retur tertunda turun — ukuran: dari 30% menjadi ≤ 10% keluhan bulanan

## Scope

### Termasuk

- **S1**: Persetujuan retur oleh Kepala Toko sampai batas nominal
- **S2**: Penerusan otomatis retur di atas batas ke Manajer Area

### Tidak Termasuk

- Retur lintas cabang — jarang terjadi, tetap lewat Manajer Area seperti sekarang
```
