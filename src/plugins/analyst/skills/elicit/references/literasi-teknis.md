# Literasi Teknis — `elicit`

Dibaca di Phase 1 (`SKILL.md`) bersama panduan elisitasi; dipakai tiap giliran Phase 2 untuk memilih pertanyaan pilar `Aktor`, `Aturan Bisnis`, `Kondisi Diinginkan`, dan `Kasus Khusus`. Berkas ini **lensa bertanya**, bukan kosakata tiket: engineer akan menanyakan hal-hal di bawah ini sesudah tiket diserahkan, jadi lebih murah bila jawabannya sudah digali dari peminta sekarang. Kolom *Konsep* hanya untuk analis — pertanyaan ke peminta dan isi pilar tetap berbahasa pekerjaan mereka (panduan bagian 3), dan kartu tetap lolos pemindai kebocoran. Tidak dipakai untuk tiket `TECH` — lihat `elicitation-tech.md`.

## 1. Di Balik Layar (backend)

| Konsep | Disentuh bila permintaan… | Tanyakan ke peminta | Jawaban masuk ke |
|---|---|---|---|
| Autentikasi — siapa yang masuk | menyebut mitra, akses dari luar, atau pengguna tanpa akun | "Siapa yang boleh memakai ini tanpa login, dan siapa yang wajib login dulu?" | `Aktor` |
| Otorisasi — batas data per peran | memuat lebih dari satu peran, cabang, tenant, atau gudang | "Peran X melihat data siapa saja? Kalau mencoba membuka data pihak lain, ditolak dengan pesan atau datanya tidak muncul?" | `Aturan Bisnis`, larangan di `Aktor` |
| Daftar — jumlah, halaman, urutan | meminta daftar, riwayat, atau rekap | "Biasanya ada berapa baris? Tampil sekaligus atau per halaman berapa? Urut dari yang terbaru atau yang lain?" | `Aturan Bisnis` |
| Penyaring dan pencarian | menyebut filter, pilih, atau cari | "Filter mana yang boleh dikosongkan? Boleh memilih lebih dari satu nilai sekaligus?" | `Aturan Bisnis` |
| Status dan perpindahannya | menyebut status (Baru, Proses, Selesai, Batal) | "Status apa saja, siapa yang memindahkannya, bisa mundur, dan berubah sendiri atau diubah orang?" | `Aturan Bisnis` |
| Validasi isian | ada form atau isian | "Isian mana yang wajib, batasnya berapa, dan pesan apa yang muncul bila salah?" | `Aturan Bisnis`, `Kasus Khusus` |
| Nilai turunan — total, sisa, persentase | menyebut total, sisa, atau progres | "Dihitung dari apa, dibulatkan bagaimana, dan data yang dibatalkan ikut dihitung atau tidak?" | `Aturan Bisnis` |
| Riwayat perubahan | data dapat diubah atau dihapus | "Perlu terlihat siapa mengubah apa dan kapan?" | `Kondisi Diinginkan` atau `Batas Cakupan` |
| Proses otomatis dan notifikasi | "otomatis", "pengingat", "tiap malam" | "Kapan persisnya berjalan, siapa penerimanya, lewat email atau pemberitahuan di aplikasi?" | `Kondisi Diinginkan`, `Aturan Bisnis` |
| Integrasi dengan aplikasi lain | "lewat API", sistem mitra | "Siapa yang memanggilnya, dan apa yang mereka terima bila permintaannya ditolak?" (panduan bagian 6) | `Aktor`, `Aturan Bisnis` |
| Waktu tunggu | keluhan lambat, data besar | "Paling lama berapa detik boleh menunggu sampai hasilnya muncul?" | `Aturan Bisnis` atau `Ukuran Keberhasilan` |

**Kasus batas** — sapu kelimanya untuk tiap aksi yang mengubah data; kategorinya sama dengan taksonomi kasus batas BRD `backend:business-analysis`, sehingga BRD yang menyerap tiket tidak perlu menanyakannya ulang. Jawabannya masuk `Kasus Khusus`:

1. **Data kosong** — "Belum ada datanya sama sekali, apa yang terlihat?"
2. **Dobel** — "Tombolnya ditekan dua kali, atau dua orang mengubah bersamaan?"
3. **Gagal di tengah** — "Proses terputus di langkah ketiga, apa yang tersisa?"
4. **Lewat waktu** — "Tidak diselesaikan sampai batas waktunya, lalu apa?"
5. **Berubah di luar** — "Akun atau hak aksesnya dicabut saat masih menunggu, bagaimana?"

## 2. Yang Dilihat dan Disentuh (frontend)

Hanya untuk bentuk hasil **layar** atau **laporan** (panduan bagian 6).

| Konsep | Disentuh bila permintaan… | Tanyakan ke peminta | Jawaban masuk ke |
|---|---|---|---|
| Halaman dan navigasi | layar atau menu baru | "Dari menu mana pengguna masuk, dan ke mana sesudah selesai?" | `Kondisi Diinginkan` |
| Prioritas isi layar | layar berisi banyak informasi | "Apa yang harus langsung terlihat tanpa menggulir?" | `Kondisi Diinginkan` |
| Komponen — daftar, isian, konfirmasi | menyebut tabel, form, atau hapus | "Aksi ini perlu konfirmasi dulu? Isian mana yang dipilih dari daftar, mana yang diketik bebas?" | `Kondisi Diinginkan`, `Aturan Bisnis` |
| Keadaan layar | hampir selalu | "Apa yang terlihat saat data kosong, sedang dimuat, gagal dimuat, atau pengguna tidak punya akses?" | `Kasus Khusus` |
| Umpan balik aksi | tombol simpan, kirim, atau hapus | "Sesudah tombol ditekan, apa yang terlihat — pesan berhasil, pindah halaman, atau tetap di tempat?" | `Kondisi Diinginkan` |
| Perangkat | pengguna lapangan, kasir, atau pelanggan | "Dipakai di HP, tablet, atau laptop?" | `Kondisi Diinginkan` |
| Teks layar | label atau pesan baru | "Label dan pesannya persis bagaimana?" | pilar terkait, dikutip apa adanya |

## 3. Batas Pemakaian

- **Hanya konsep yang disentuh.** Pilih dari tabel sesuai permintaan dan bentuk hasilnya: bentuk API tidak menanyakan keadaan layar, bentuk layar tidak menanyakan pemanggil. Aturan bertanya panduan bagian 2 tetap berlaku — maksimal 3 pertanyaan per giliran, opsi konkret, tanya kejadian.
- **Konsep yang tidak ditanyakan bukan fakta.** Dilarang mengisi pilar dengan "biasanya begini" atau praktik terbaik. Jawaban "tidak tahu" → `Q-{n}` seperti biasa; "tidak perlu sekarang" → `Batas Cakupan`.
- **Rancangan dan cara membangun milik engineer.** Letak, warna, dan jenis komponen persis milik `frontend:lead`; penyimpanan, integrasi, dan teknologi milik `backend:tech-lead`. Keduanya ditanyakan hanya bila peminta sendiri menetapkannya.
