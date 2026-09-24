# Panduan Elisitasi — `elicit`

Dibaca di Phase 2 (`SKILL.md`) sebelum menyusun pertanyaan. Lawan bicara skill ini adalah peminta non-engineer — pemilik bisnis, tim operasional, sales, CS, atau pengguna akhir — sehingga pertanyaan disusun dalam bahasa pekerjaan mereka, bukan bahasa sistem.

## 1. Pilar per Tipe

| Pilar | Tipe | Yang digali | Pertanyaan pembuka yang baik |
|---|---|---|---|
| Masalah | FEATURE, IMPROVEMENT | Siapa terdampak, seberapa sering, berapa biaya bila dibiarkan (uang, jam kerja, keluhan) | "Kapan terakhir masalah ini terjadi, dan apa yang harus dikerjakan tim sesudahnya?" |
| Aktor | FEATURE, IMPROVEMENT | Peran yang memakai, menyetujui, dan yang **dilarang** memakai | "Siapa saja yang boleh melakukan ini, dan siapa yang jelas tidak boleh?" |
| Kondisi Saat Ini | FEATURE, IMPROVEMENT | Cara kerja sekarang, termasuk jalan pintas manual di luar sistem | "Tolong ceritakan langkah demi langkah bagaimana ini dikerjakan hari ini." |
| Kondisi Diinginkan | FEATURE, IMPROVEMENT | Cara kerja sesudah selesai, dari sudut pandang orang yang memakainya | "Kalau ini sudah jadi, apa yang Anda lakukan dan apa yang Anda lihat?" |
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

Bila produk itu sendiri memang teknis (mis. layanan API untuk mitra), istilahnya kosakata bisnis: konfirmasi ke peminta, lalu catat di frontmatter `domain_terms: [API]` `TICKET.md` agar kartu yang ditulis `spec` boleh memakainya. Nama merek bercampur huruf (mis. aplikasi `myPertamina`) diperlakukan sama.

## 4. Rubrik Urgensi → Prioritas

`spec` memetakan pilar `Urgensi` ke `priority` tiket dengan rubrik ini; user boleh menimpanya di persetujuan.

| Prioritas | Salah satu terpenuhi |
|---|---|
| `HIGH` | transaksi/pendapatan terhenti atau bocor; pelanggan tidak dapat menyelesaikan urusan tanpa jalan pintas; tenggat regulasi atau kontrak ≤ 1 bulan |
| `MEDIUM` | ada jalan pintas manual yang memakan jam kerja rutin; tenggat bisnis kuartal ini |
| `LOW` | kenyamanan, konsistensi tampilan, atau permintaan tanpa tenggat |

## 5. Tanda Permintaan Terlalu Besar

Temuan di tengah elisitasi bahwa permintaan memuat lebih dari satu tujuan pengguna yang dapat dirilis terpisah (mis. "cicilan" **dan** "denda keterlambatan" **dan** "laporan piutang") adalah temuan lingkup, bukan pilar tambahan. Hentikan penggalian tujuan kedua, tanyakan ke user lewat `AskUserQuestion` mana yang dikerjakan tiket ini, dan catat sisanya di `Batas Cakupan` dengan alasan `— tiket terpisah`.
