<!--
Kerangka laporan `TELUSUR` fullstack. `explore.py new` menyalin seksi di bawah ini ke
`.fullstack/explore/<YYMMDDhhmm>-<slug>.md`, menulis frontmatter (`slug`, `objective`, `dibuat`, `lingkup`, `repo`),
dan mengisi tabel `## Repo` dari `scan`. Field `confidence` diisi konteks utama sesudah seluruh balikan scout masuk.

Aturan lintas seksi:
1. Komentar penjelas dihapus saat seksi diisi. Seksi yang hanya berisi komentar dianggap kosong oleh `check`.
2. Tiap rujukan kode ditulis `<repo>/<path>:<baris>` (mis. `wms/api/internal/order/handler.go:42`) dan hanya berasal
   dari balikan `repo-scout`. Konteks utama tidak membaca kode.
3. Tabel tanpa baris ditulis `- Tidak ada.`
4. `## Jahitan` tidak pernah diketik tangan: jalankan `explore.py seam --report <laporan> --write`.
5. `confidence`: `high` bila semua butir pertanyaan tertutup bukti; `medium` bila ada `Belum disisir`, repo yang
   scout-nya gagal, atau profil BE tanpa `external:` padahal objective menyebut integrasi; `low` bila objective hanya
   terjawab sebagian.
-->

## Jawaban

<!-- Jawaban langsung atas objective dalam 3–8 kalimat, bahasa yang dipahami penanya. Sebut repo yang terlibat dan
alurnya secara permukaan. Fakta dari `Tidak ditemukan` dilarang dijadikan klaim "tidak ada". -->

## Repo

<!-- Diisi `explore.py new`. Jangan diubah selain menambah repo yang ikut disisir di putaran kedua. -->

## Temuan

<!-- Satu subseksi per repo yang di-scout, judul `### <repo> (BE)` atau `### <repo> (FE)`. Baris pertama subseksi
FE adalah `- Base API: …` dan subseksi BE `- Prefix route: …`, disalin dari balikan scout; lalu butir `Ditemukan`. -->

## Endpoint

<!-- Gabungan tabel `### Endpoint` balikan scout BE:
| Repo | Metode | Path | Bukti |
|---|---|---|---|
-->

## Panggilan

<!-- Gabungan tabel `### Panggilan` balikan scout FE dan BE:
| Pemanggil | Target | Metode | Path | Bukti |
|---|---|---|---|---|
-->

## Jahitan

<!-- Ditulis `explore.py seam --write`. -->

## Celah

### Tidak ditemukan

<!-- Butir `Tidak ditemukan` dari balikan scout, beserta direktori yang sudah disisir. -->

### Belum disisir

<!-- Butir `Belum disisir`, repo yang scout-nya gagal dua kali, dan repo berprofil tidak `VALID`. -->

### Belum dipetakan

<!-- Satu butir per jahitan `DUGAAN`/`AMBIGU` yang belum dikonfirmasi user: `<pemanggil>` → `<target>`. -->

## Arahan Lanjut

<!-- Langkah lanjutan untuk user: kerja perubahan kode (`cd <repo>` lalu `backend:tech-lead` atau `frontend:lead`),
repo tanpa profil atau profil tertinggal (`cd <repo>` lalu `<plugin>:profile`), atau pertanyaan TELUSUR berikutnya. -->
