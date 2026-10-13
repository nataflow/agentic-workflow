<!--
Kerangka laporan `ALUR` fullstack. `explore.py new --jalur ALUR` menyalin seksi di bawah ini ke
`.fullstack/explore/<YYMMDDhhmm>-<slug>.md`, menulis frontmatter (`slug`, `objective`, `jalur`, `kedalaman`, `dibuat`,
`lingkup`, `repo`), dan mengisi tabel `## Repo` dari `scan`. Field `confidence` diisi konteks utama sesudah seluruh
balikan explorer masuk.

Aturan lintas seksi:
1. Komentar penjelas dihapus saat seksi diisi. Seksi yang hanya berisi komentar dianggap kosong oleh `check`.
2. Tiap rujukan kode ditulis `<repo>/<path>:<baris>` (mis. `backend-a/internal/order/service.go:42`) dan hanya berasal
   dari balikan `backend-explorer`/`frontend-explorer`. Konteks utama tidak membaca kode.
3. Tabel tanpa baris ditulis `- Tidak ada.`
4. `confidence`: `high` bila objective terjawab untuk semua repo dan tiap langkah alur berbukti; `medium` bila ada
   `Belum disisir`, repo yang explorer-nya gagal, atau fakta panen yang belum dibuktikan ulang; `low` bila objective
   hanya terjawab sebagian.
-->

## Jawaban

<!-- Penjelasan alur atas objective dalam 5–15 kalimat, bahasa yang dipahami penanya: dari mana alur dimulai, lapisan
apa saja yang dilewati, aturan bisnis yang menentukan hasilnya, dan di mana alur berakhir. Fakta dari
`Tidak ditemukan` dilarang dijadikan klaim "tidak ada". -->

## Repo

<!-- Diisi `explore.py new`. Jangan diubah. -->

## Alur

<!-- Satu subseksi per repo yang ditelusuri, judul `### <repo> (BE)` atau `### <repo> (FE)`. Baris pertama
`- Entry: …` disalin dari balikan explorer, lalu langkah bernomor apa adanya:
1. <Layer> — <apa yang terjadi> — `<repo>/<path>:<baris>`
Repo yang explorer-nya gagal tidak diberi subseksi; ia dicatat di `## Celah` → `### Belum disisir`. -->

## Aturan Bisnis

<!-- Gabungan `### Aturan Bisnis` balikan explorer:
| Repo | Aturan | Bukti |
|---|---|---|
-->

## Permukaan

<!-- Gabungan tabel `### Permukaan` balikan explorer:
| Repo | Permukaan | Detail | Bukti |
|---|---|---|---|
-->

## Celah

### Tidak ditemukan

<!-- Butir `Tidak ditemukan` dari balikan explorer, beserta direktori yang sudah disisir. -->

### Belum disisir

<!-- Butir `Belum disisir`, dan repo yang explorer-nya gagal dua kali (sebut nama repo-nya). -->

## Arahan Lanjut

<!-- Langkah lanjutan untuk user: kerja perubahan kode (`cd <repo>` lalu `backend:tech-lead` atau `frontend:lead`),
jahitan ke repo lain (`TELUSUR`), profil tertinggal (`cd <repo>` lalu `<plugin>:profile`), atau pertanyaan `ALUR`
berikutnya. -->
