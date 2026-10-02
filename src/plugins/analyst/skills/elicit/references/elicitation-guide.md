# Panduan Elisitasi — `elicit`

Dibaca di Phase 1 (`SKILL.md`); bagian 2 dipakai tiap giliran Phase 2. Lawan bicara skill ini adalah peminta non-engineer — pemilik bisnis, tim operasional, sales, CS, atau pengguna akhir — sehingga pertanyaan disusun dalam bahasa pekerjaan mereka, bukan bahasa sistem. Tiket `TECH` (peminta engineer) memakai `elicitation-tech.md` sebagai ganti bagian 1–3 dan 6; bagian 4 tetap berlaku.

## 1. Pilar per Tipe

| Pilar | Tipe | Yang digali | Pertanyaan pembuka yang baik |
|---|---|---|---|
| Masalah | FEATURE, IMPROVEMENT | Siapa terdampak, seberapa sering, berapa biaya bila dibiarkan (uang, jam kerja, keluhan) | "Kapan terakhir masalah ini terjadi, dan apa yang harus dikerjakan tim sesudahnya?" |
| Aktor | FEATURE, IMPROVEMENT | Peran yang memakai, menyetujui, dan yang **dilarang** memakai | "Siapa saja yang boleh melakukan ini, dan siapa yang jelas tidak boleh?" |
| Kondisi Saat Ini | FEATURE, IMPROVEMENT | Cara kerja sekarang, termasuk jalan pintas manual di luar sistem | "Tolong ceritakan langkah demi langkah bagaimana ini dikerjakan hari ini." |
| Kondisi Diinginkan | FEATURE, IMPROVEMENT | Cara kerja sesudah selesai, dari sudut pandang orang yang memakainya, beserta bentuk hasilnya (bagian 6) | "Kalau ini sudah jadi, apa yang Anda lakukan dan apa yang Anda lihat — di layar, di berkas unduhan, atau di aplikasi lain?" |
| Aturan Bisnis | FEATURE, IMPROVEMENT | Batas, angka, syarat, urutan, siapa menang bila dua aturan bertabrakan | "Ada batas jumlah, nominal, atau waktu? Apa yang terjadi kalau batas itu dilewati?" |
| Batas Cakupan | semua (opsional di BUG) | Yang sengaja **tidak** dikerjakan sekarang | "Apa yang terkait tapi boleh menunggu fase berikutnya?" |
| Urgensi | semua | Tenggat, pemicu bisnis, dampak bila ditunda | "Apa yang terjadi kalau ini baru selesai bulan depan?" |
| Kasus Khusus | FEATURE, IMPROVEMENT (opsional) | Pengecualian: data kosong, dobel, batal di tengah jalan, lewat batas waktu | "Bagaimana kalau pelanggan membatalkan di tengah proses?" |
| Ukuran Keberhasilan | FEATURE, IMPROVEMENT (opsional) | Angka sebelum dan sesudah | "Angka apa yang akan membuat Anda bilang ini berhasil?" |
| Langkah Reproduksi | BUG | Urutan tindakan persis sampai masalah muncul | "Mulai dari membuka aplikasi, apa saja yang Anda klik?" |
| Yang Diharapkan | BUG | Hasil yang benar menurut peminta | "Seharusnya apa yang muncul?" |
| Yang Terjadi | BUG | Hasil yang benar-benar muncul, kutip teks layar apa adanya | "Apa persisnya tulisan yang muncul?" |
| Dampak | BUG | Siapa terdampak, seberapa sering, ada jalan pintas atau tidak | "Berapa pelanggan yang mengalami ini, dan apakah mereka masih bisa menyelesaikan urusannya?" |
| Lingkungan | BUG (opsional) | Perangkat, aplikasi/halaman, waktu kejadian — sebatas yang dilihat peminta | "Pakai HP atau laptop? Aplikasi atau lewat browser?" |

## 2. Aturan Bertanya

- **Satu giliran, maksimal 3 pertanyaan**, lewat `AskUserQuestion`, masing-masing dengan 2–4 opsi konkret beserta konsekuensi bisnisnya. Opsi `Other` disediakan otomatis — dilarang ditulis.
- **Tanya kejadian, bukan opini.** "Kapan terakhir terjadi?" menghasilkan fakta; "Menurut Anda penting?" menghasilkan kata sifat.
- **Angka dulu, kata sifat belakangan.** Jawaban "banyak", "sering", "cepat" dijawab dengan pertanyaan lanjutan yang meminta angka atau rentang.
- **Dilarang menanyakan solusi teknis** ("pakai notifikasi push atau email?" boleh bila pilihan itu terlihat pengguna; "disimpan di tabel baru?" tidak pernah).
- **Dilarang menanyakan ulang** yang sudah tertulis di permintaan asli atau log.
- **Peminta tidak tahu jawabannya** → tanyakan siapa yang tahu, catat sebagai `Q-{n}` `menunggu: <siapa>`, lanjutkan pilar lain.

## 3. Menerjemahkan Bahasa Teknis dari Peminta

Peminta kadang memakai istilah teknis yang mereka dengar dari tim. Rekam apa adanya di log, lalu rumuskan pilarnya sebagai perilaku:

| Peminta berkata | Pilar menulis |
|---|---|
| "API-nya error 500" | Yang Terjadi: muncul tulisan "Terjadi kesalahan, coba lagi" saat menekan *Bayar* |
| "Tambah kolom status di database" | Kondisi Diinginkan: Admin melihat status pengiriman di daftar pesanan |
| "Kirim webhook ke mitra" | Kondisi Diinginkan: mitra menerima pemberitahuan otomatis saat pesanan lunas |
| "Cache-nya basi" | Yang Terjadi: harga yang tampil masih harga lama sampai halaman dibuka ulang |

Bila produk itu sendiri memang teknis (mis. layanan API untuk mitra), istilahnya kosakata bisnis: konfirmasi ke peminta — catat sebagai baris log `| n | <tanggal> | Apakah "API" nama produk? | Ya | <peminta> |` — lalu catat di frontmatter `domain_terms: [API]` `TICKET.md` agar kartu yang ditulis `spec` boleh memakainya. Validator menolak istilah `domain_terms` tanpa baris konfirmasi itu, sekalipun istilahnya muncul di permintaan asli. Nama merek bercampur huruf (mis. aplikasi `myPertamina`) diperlakukan sama. Hasil yang diminta berupa API untuk aplikasi lain — bukan produk API — mengikuti bagian 6.

Menerjemahkan istilah **teknis** menjadi perilaku berbeda dengan menerjemahkan **bahasa**. Istilah domain, nama entitas, menu, layar, dan kolom yang dipakai peminta dalam Bahasa Inggris adalah kosakata bisnis mereka dan ditulis apa adanya di pilar, judul, dan kartu, lengkap dengan kapitalisasi seperti yang tampil di layar. Menerjemahkannya membuat tiket terdengar asing bagi peminta dan menyulitkan engineer mencocokkannya dengan layar:

| Peminta berkata | Ditulis | Bukan |
|---|---|---|
| "created at di report order sampai detik" | *Created At* di *Report Order* tampil hingga detik | waktu dibuat di laporan pesanan |
| "invoice yang overdue" | *Invoice* berstatus *Overdue* | tagihan yang jatuh tempo |

## 4. Rubrik Urgensi → Prioritas

`spec` memetakan pilar `Urgensi` ke `priority` tiket dengan rubrik ini; user boleh menimpanya di persetujuan.

| Prioritas | Salah satu terpenuhi |
|---|---|
| `HIGH` | transaksi/pendapatan terhenti atau bocor; pelanggan tidak dapat menyelesaikan urusan tanpa jalan pintas; tenggat regulasi atau kontrak ≤ 1 bulan |
| `MEDIUM` | ada jalan pintas manual yang memakan jam kerja rutin; tenggat bisnis kuartal ini |
| `LOW` | kenyamanan, konsistensi tampilan, atau permintaan tanpa tenggat |

## 5. Tanda Permintaan Terlalu Besar

Temuan di tengah elisitasi bahwa permintaan memuat lebih dari satu tujuan pengguna yang dapat dirilis terpisah (mis. "cicilan" **dan** "denda keterlambatan" **dan** "laporan piutang") adalah temuan lingkup, bukan pilar tambahan. Hentikan penggalian tujuan kedua, tanyakan ke user lewat `AskUserQuestion` mana yang dikerjakan tiket ini, dan catat sisanya di `Batas Cakupan` dengan alasan `— tiket terpisah`. Dalam batch (`intake/references/batch.md`), tujuan kedua yang sudah menjadi tiket lain di batch itu tidak ditanyakan: catat langsung sebagai `<tujuan> — tiket <slug>`.

## 6. Bentuk Hasil

Pilar `Kondisi Diinginkan` diawali satu baris `Bentuk hasil: <layar | API | proses otomatis | laporan>`, diambil dari cara peminta menggambarkan hasilnya. Bentuk yang hanya tersirat ditulis `Asumsi:` dan dikonfirmasi di Phase 4. Bentuk hasil menentukan siapa yang ditulis sebagai pengguna di User Story, bunyi `then` di AC, dan objek judul (`spec` Phase 1):

| Bentuk hasil | Tanda di permintaan | Pengguna di User Story | Peran bisnis (Admin, Tenant, …) | `then` di AC | Contoh judul |
|---|---|---|---|---|---|
| layar | "tampil di menu", "tombol", "halaman" | orang yang membuka layar | pemakai layar itu | teks, tombol, kolom, atau pesan yang terlihat | `Tampilkan QTY Received per produk di daftar Purchase Order` |
| API | "lewat API", "untuk integrasi", "dipanggil aplikasi X" | aplikasi atau tim yang memanggilnya | atas nama siapa permintaan dikirim; batas data per peran dicatat di `Aturan Bisnis` | data yang dikembalikan, atau penolakan beserta pesannya | `Buat API daftar Purchase Order beserta progres penerimaan per produk` |
| proses otomatis | "otomatis", "tiap malam", "kirim pengingat" | peran yang menerima akibatnya | penerima, atau pihak yang dikecualikan | email atau notifikasi yang diterima, atau status yang berubah dan terlihat | `Tambah pengingat jatuh tempo cicilan tiga hari sebelumnya` |
| laporan | "unduh", "Excel", "rekap" | peran yang memakai laporan | pemakai laporan dan batas datanya | kolom, baris, dan total di laporan | `Tambah unduhan Excel rekap penerimaan Purchase Order` |

Bentuk API paling sering salah tulis karena pemakainya bukan orang: "Admin melihat daftar lewat API" mencampur pemanggil dengan peran yang datanya dibatasi. Tanyakan siapa pemanggilnya — layar aplikasi sendiri yang dibangun terpisah, aplikasi mitra, atau sistem lain; peminta tidak tahu → `Q-{n}` `TIDAK MEMBLOKIR` beserta asumsinya. Kata "API" di kartu tetap menuntut `domain_terms: [API]` dan baris konfirmasinya, untuk bentuk ini: `| n | <tanggal> | Apakah hasilnya "API" yang dipanggil aplikasi lain, bukan layar? | Ya | <peminta> |`.
