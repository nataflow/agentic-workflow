# Panduan Elisitasi Enam Pilar

Dimuat `product:discover` Phase 1. Berisi urutan pilar, aturan bertanya, bank pertanyaan per mode, dan arti "terjawab"
untuk tiap pilar. Bentuk catatan dan aturan validasinya milik `templates/charter-skeleton.md`.

## 1. Urutan pilar

Purpose → Actors → Business Process → Business Rules → Scope → Success Criteria.

Success Criteria ditanya **terakhir**: ukuran sukses baru dapat dijawab sesudah masalah, alur, dan batas versi
pertama jelas. Scope ditanya sebelum Success Criteria supaya ukurannya tidak menagih hal yang di luar versi pertama.

Ini urutan **bertanya**, bukan urutan heading. Heading `####` di `### Fakta` tetap persis urutan kerangka
(Purpose, Actors, Business Process, Business Rules, Success Criteria, Scope); validator menolak urutan lain.

## 2. Aturan bertanya

1. Maksimal **3 pertanyaan per giliran** lewat `AskUserQuestion`, satu per pilar, urut menurut bagian 1.
2. Tiap pertanyaan 2–4 **opsi konkret** beserta konsekuensi bisnisnya; opsi *Lainnya* tersedia otomatis. Opsi yang
   bertumpu pada temuan scout ditulis dalam bahasa pengguna ("Saat ini kasir bisa membatalkan transaksi kapan saja.
   Tetap begitu, atau dibatasi hari yang sama?"), tanpa nama berkas atau istilah sistem.
3. Dilarang menanyakan solusi teknis: penyimpanan data, teknologi, integrasi sistem, atau struktur layar internal.
   Pilihan yang **terlihat** pengguna (notifikasi lewat WhatsApp atau email, satu layar atau dua langkah) boleh.
4. "Tidak tahu" atau "tanya si X" → `Q-n` `menunggu: <siapa>`; label `MEMBLOKIR` bila jawabannya mengubah alur,
   aturan, atau batas versi pertama, `TIDAK MEMBLOKIR` bila tidak.
5. "Terserah" bukan fakta. Tawarkan opsi rekomendasi beserta konsekuensinya dan minta dipilih; tetap tidak memilih →
   `Q-n` `MEMBLOKIR`.
6. Istilah peminta dipakai apa adanya dan konsisten lintas pilar; nama layar, menu, peran, dan entitas berbahasa
   Inggris tidak diterjemahkan.

## 3. Arti "terjawab" per pilar

| Pilar | Terjawab bila catatan memuat |
|---|---|
| Purpose | masalah yang diselesaikan, siapa yang mengalaminya, seberapa sering atau mahal, kenapa sekarang |
| Actors | tiap peran yang terlibat, yang boleh dan tidak boleh dilakukannya; mode codebase: peran itu sudah ada atau baru |
| Business Process | pemicu, langkah berurutan beraktor, hasil akhir, dan minimal satu cabang (gagal, batal, ditolak) bila peminta menyebutnya |
| Business Rules | tiap aturan beserta angka atau ambangnya dan pengecualiannya (atau "tidak ada pengecualian"); bila peminta menyatakan tidak ada aturan khusus, kalimat itu dari log |
| Scope | yang masuk versi pertama, yang tidak masuk, dan alasan tiap yang tidak masuk |
| Success Criteria | 1–8 indikator beserta angka, ambang, atau durasi, dan kapan atau bagaimana diukur |

## 4. Bank pertanyaan — `NEW_PRODUCT`

Tidak ada kode untuk dirujuk; seluruh fakta dari peminta.

- **Purpose**: Seberapa sering masalah ini terjadi, dan berapa biayanya (waktu, uang, pelanggan hilang)? Kenapa
  harus sekarang — tenggat, pesaing, keluhan yang menumpuk? Apa yang dipakai sekarang sebagai jalan pintas?
- **Actors**: Siapa saja yang akan memakai produk ini sehari-hari? Siapa yang menyetujui atau mengawasi? Ada pihak
  luar (pelanggan, pemasok, kurir) yang ikut berinteraksi? Apa yang tidak boleh dilakukan tiap peran?
- **Business Process**: Apa pemicu alur utamanya? Langkah apa saja sampai selesai, oleh siapa? Apa yang terjadi bila
  gagal, dibatalkan, atau ditolak di tengah?
- **Business Rules**: Ada batas nominal, jumlah, waktu, atau persetujuan berjenjang? Ada pengecualian untuk peran
  atau kondisi tertentu?
- **Scope**: Dari semua yang dibahas, mana yang **wajib** ada di versi pertama supaya masalah di Purpose sudah
  berkurang? Mana yang bisa menyusul?
- **Success Criteria**: Angka apa yang berubah bila produk ini berhasil (waktu rekap, jumlah kesalahan, transaksi
  tercatat)? Berapa targetnya dan kapan dilihat?

## 5. Bank pertanyaan — `NEW_FEATURE`

Fitur menempel pada aplikasi yang sudah ada. Scout `PETA` `Actors` memberi daftar peran yang sudah ada.

- **Purpose**: Apa yang belum bisa dilakukan sekarang, dan bagaimana pengguna mengakalinya saat ini?
- **Actors**: (dari scout) "Aplikasi sudah punya peran A dan B. Siapa yang memakai fitur ini — salah satunya, atau
  peran baru?" Apa yang tidak boleh dilakukan tiap peran di fitur ini?
- **Business Process**: Dari layar atau menu mana pengguna masuk ke fitur ini? Langkahnya sampai selesai? Apa
  dampaknya ke alur yang sudah ada?
- **Business Rules**: Aturan baru apa yang berlaku? Ada aturan yang sudah ada di aplikasi yang harus tetap dipatuhi
  fitur ini?
- **Scope** dan **Success Criteria**: seperti `NEW_PRODUCT`.

## 6. Bank pertanyaan — `IMPROVEMENT`

Kondisi sekarang dipetakan scout `PETA` untuk `Actors`, `Business Process`, dan `Business Rules`. Tiap temuan yang
dipakai ditulis sebagai `Asumsi: <kalimat> `` `path:baris` `` lalu dikonfirmasi peminta; yang dibantah peminta dicatat
apa adanya beserta bantahannya di log.

- **Purpose**: Apa yang salah atau kurang dari cara kerja sekarang? Siapa yang paling terdampak, seberapa sering?
- **Actors**: (dari scout) "Saat ini yang bisa melakukan X adalah A dan B. Apakah itu berubah?" Peran mana yang
  tetap, berubah haknya, atau baru?
- **Business Process**: (dari scout) "Sekarang alurnya: langkah 1 → 2 → 3. Bagian mana yang bermasalah, dan
  bagaimana seharusnya?" Catatan memisahkan *Kondisi sekarang* dan *Kondisi target*.
- **Business Rules**: (dari scout) "Sekarang aturan X berlaku. Tetap, diubah, atau dihapus?" Tiap aturan ditandai
  tetap, ubah, atau baru di catatan.
- **Scope**: Bagian alur mana yang diubah di versi pertama, dan mana yang sengaja dibiarkan seperti sekarang?
- **Success Criteria**: Angka sekarang berapa, dan targetnya berapa? Tanpa angka sekarang, tanyakan cara
  mengukurnya sebelum perubahan dirilis.

## 7. Satu inisiatif, satu charter

Jawaban yang memunculkan inisiatif kedua yang dapat berjalan terpisah (produk lain, fitur di area lain) → tanyakan
mana yang dikerjakan di charter ini; sisanya dicatat di pilar Scope sebagai tidak termasuk `— charter terpisah`.
