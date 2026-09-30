# Kontrak Halaman Artifact

Dimuat `nataflow:create-artifact` Fase 2 sebelum draft ditulis. Artifact adalah **satu berkas HTML mandiri** yang
disajikan endpoint render nataflow apa adanya sebagai `text/html` kepada user login project. Tidak ada berkas
pendukung, tidak ada kerangka yang dibungkuskan server, dan tidak ada build step.

Aturan bertanda **[gerbang]** ditagih `artifact.py check` (FAIL). Aturan bertanda **[peringatan]** dicetak
sebagai `WARN` dan tetap wajib diperbaiki kecuali user memintanya lain. Sisanya tanggung jawab penulis.

## Kerangka

- **[gerbang]** Baris pertama `<!doctype html>`; `<html lang="id">` (atau bahasa isi); `<meta charset="utf-8">`;
  `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- **[gerbang]** `<title>` berisi nama 2–4 kata (maks 120 karakter). Judul inilah yang menjadi `metadata.title`
  dan asal `key` bila user tidak menyebut key. Bukan "Nama: penjelasan" — penjelasan masuk ke isi halaman.
- Satu `<main>` berisi konten; heading berjenjang (`h1` sekali).

## Aset

- **[gerbang]** Semua CSS, JS, gambar, dan data disematkan inline. Gambar kecil boleh `data:` URI; ukuran total
  berkas maksimal 1 MiB karena isi dikirim utuh sebagai argumen tool MCP.
- **[gerbang]** `<script src>` eksternal hanya dari `https://cdnjs.cloudflare.com/` (utamakan),
  `https://cdn.jsdelivr.net/npm/`, `https://unpkg.com/`, `https://cdn.tailwindcss.com`, atau
  `https://code.jquery.com/`. Stylesheet eksternal hanya Google Fonts (`https://fonts.googleapis.com/`).
  Pin versi pustaka di URL.
- **[gerbang]** Tidak ada rujukan relatif (`src="chart.js"`, `href="style.css"`): tidak ada berkas lain di
  sebelah halaman.
- Jangan memanggil API nataflow atau layanan lain yang butuh kredensial dari halaman. Data yang ditampilkan
  disematkan saat artifact ditulis; artifact adalah potret, bukan klien live.

## Tema

- **[peringatan]** Warna didefinisikan sebagai token `--*` di `:root`, lalu didefinisikan ulang untuk mode gelap
  di bawah `@media (prefers-color-scheme: dark)` yang dijaga `:root:not([data-theme="light"])`, dan sekali lagi
  di `:root[data-theme="dark"]`.
- `body` memakai `background` dan `color` eksplisit dari token, bukan bawaan browser.
- Kontras teks terhadap latar minimal 4.5:1 di kedua tema.

## Tata Letak

- Layout bekerja di lebar ponsel: gutter samping 16px, tidak ada scroll horizontal halaman. Tabel lebar dibungkus
  kontainer `overflow-x: auto`.
- Lebar baca teks panjang dibatasi (`max-width` sekitar 72ch).
- Grafik diberi label sumbu, satuan, dan keterangan; jangan hanya mengandalkan warna untuk membedakan seri.

## Perilaku

- **[peringatan]** `localStorage`/`sessionStorage` hanya untuk kenyamanan per penonton (tab terakhir, filter),
  setiap akses dibungkus `try/catch`, dan halaman tetap benar tanpa storage.
- Tidak ada state yang harus tersimpan bersama antar-penonton: artifact nataflow tidak punya database.

## Larangan Isi

- **[gerbang]** Tidak ada `<input type="password">` atau form lain yang mengumpulkan kredensial atau data
  pembayaran.
- Tidak meniru organisasi atau orang nyata (nama, merek, byline, domain) dan tidak memuat rekaman, kuitansi, atau
  ulasan palsu yang disajikan sebagai asli.
- Tidak memuat rahasia: token, MCP key, password, isi `.env`, atau data pribadi yang tidak diminta user.
