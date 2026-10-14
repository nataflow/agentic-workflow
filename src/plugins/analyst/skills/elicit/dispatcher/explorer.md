# Template Prompt Penelusur Kode — `analyst:code-explorer`

Pakai template ini saat `elicit` mendispatch subagent penelusur kode `analyst:code-explorer` secara langsung. Nama
agent selalu ditulis penuh: plugin backend dan frontend juga punya agent `code-explorer`, dengan kontrak yang menuntut
laci taskdir dan blok format sendiri.

**Tujuan:** Memahami kondisi kode sekarang di sekitar konsep yang disebut peminta tanpa membaca kode di konteks utama.
Tiket `TECH`: bukti `path:baris` beserta struktur sekarang. Tipe lain: perilaku sekarang dalam bahasa yang terlihat
pengguna (aktor dan izinnya, aturan beserta angkanya, status, pesan), yang ditulis lebih dulu sebagai `Asumsi:` lalu
dikonfirmasi peminta. Hasilnya bahan bertanya, bukan fakta dari peminta.

**Dispatch setelah:** `elicit` Phase 1. Brief atau permintaan sudah dipetakan ke pilar, dan `TICKET.md` sudah ditulis
sekali. Tiket batch: dispatch pertama berjalan di awal batch, sesudah semua `ticket.py new` `PASS` dan sebelum Phase 1
tiket mana pun — satu dispatch per tiket yang membutuhkan, semuanya dalam satu pesan (`intake/references/batch.md`
bagian 6).

````markdown
Telusuri kode untuk elisitasi satu tiket analyst.

- Mode: `{mode}`
- Tipe: `{tipe}`
- Category: `{category}`
- Root: `{root}`
- Batas: `{batas}`
- Kedalaman: `{kedalaman}`
- Pertanyaan:
{pertanyaan}
- Larangan: read-only; dilarang membuka `.env*`, mendiagnosis penyebab bug, atau menyarankan solusi; kuota
  `Read`/`Grep`/`Glob` 20 (`ringkas`) atau 40 (`menyeluruh`).
- Balikan: blok `## Code Explorer` sesuai definisi agent-mu, tanpa teks lain.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{mode}` | Frontmatter `type` `TICKET.md` | **[REQUIRED]** `TECH` → `BUKTI`; tipe lain → `KONTEKS` |
| `{tipe}` | Frontmatter `type` `TICKET.md` | **[REQUIRED]** `FEATURE`, `IMPROVEMENT`, `BUG`, atau `TECH` |
| `{category}` | Frontmatter `category` `TICKET.md` | **[REQUIRED]** untuk `TECH`; `-` untuk tipe lain |
| `{root}` | Baris `root=` keluaran `ticket.py new` atau `check --gate elicit` | **[REQUIRED]** Path absolut |
| `{batas}` | Direktori atau repo anak yang disebut peminta, bila ada | **[OPTIONAL]** `-` bila kosong; dilarang menebak direktori dari nama stack. Root berisi beberapa repo: repo anak yang disebut permintaan |
| `{kedalaman}` | Tipe tiket | **[REQUIRED]** `TECH` → `menyeluruh`; tipe lain → `ringkas` |
| `{pertanyaan}` | `BUKTI`: tiap klaim kondisi sekarang di brief peminta. `KONTEKS`: konsep yang disebut permintaan (layar, menu, laporan, status, data) | **[REQUIRED]** 1–5 butir bernomor `  - P1: …`, memakai kata-kata peminta apa adanya |

### Aturan untuk Pendispatch

**Gerbang masuk**, kegagalan mana pun membatalkan dispatch:

- **Plafon 2 dispatch per tiket**: satu di Phase 1 (tiket batch: di awal batch), dan satu susulan untuk butir `Belum
  disisir` atau klaim dan konsep baru dari jawaban peminta. Dispatch ketiga dilarang. Sisa pertanyaannya ditanyakan
  ke peminta. Dispatch ulang karena balikan hilang dari percakapan (diringkas otomatis, atau sesi baru) tidak
  dihitung, sama seperti ulangan karena gagal.
- **Dispatch langsung tanpa skill pembungkus**, ke `analyst:code-explorer` dengan nama penuh. Doktrin penelusuran ada
  di `agents/code-explorer.md`. Dilarang menyalin isi tiket ke prompt. Butir `pertanyaan` cukup kata-kata peminta.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Balikan tidak ditulis ke berkas mana pun. Pakai isinya langsung di Phase 1–2; balikan tiket batch disimpan di
percakapan berlabel slug tiketnya sampai gilirannya tiba:

| Balikan subagent | Penanganan `elicit` |
| --- | --- |
| `Ditemukan`, mode `BUKTI` | Catat `` `path:baris` ``-nya di pilar `Kondisi Saat Ini`; baris `Struktur` memperkaya kalimatnya. Klaim yang dibantah kode ditanyakan ke peminta di giliran berikutnya berdampingan dengan buktinya, bukan dikoreksi diam-diam |
| `Ditemukan`, mode `KONTEKS` | Baris `Perilaku`, dan baris `Aktor`/`Status` yang menggambarkan keadaan sekarang, ditulis lebih dulu sebagai `Asumsi:` tanpa rujukan berkas di pilar keadaan sekarang (`Kondisi Saat Ini` untuk `FEATURE`/`IMPROVEMENT`; `Langkah Reproduksi` untuk `BUG`, sebatas letak layar dan tombol), lalu dikonfirmasi lewat pertanyaan Phase 2 berbentuk konfirmasi atau koreksi. Baris `Aturan`/`Aktor`/`Pesan` menjadi opsi pertanyaan pilar yang diinginkan (`Aturan Bisnis`, `Aktor`, `Yang Diharapkan`), bukan fakta pilar itu. Dilarang menyalin `path:baris` ke catatan (`validate_doc.py --kind elicit` menolaknya) |
| `Tidak ditemukan` | `BUKTI`: klaim tidak terbukti, jadi tanyakan ke peminta. `KONTEKS`: konsepnya mungkin belum ada, jadi tanyakan sebagai kemampuan baru, bukan sebagai fakta |
| `Belum disisir`, termasuk butir `(sebagian)` | Pakai dispatch susulan bila plafon tersisa. Selain itu tanyakan ke peminta |
| `Repo: tanpa kode` | `KONTEKS` → lanjut tanpa konteks kode. `BUKTI` → `ELICIT — TERTAHAN`: tiket `TECH` wajib tinggal di repo yang diubah |
| `Confidence: low` | Temuan tetap dipakai, tetapi `Asumsi:`-nya ditanyakan terbuka ("Benarkah …, atau …?"), bukan sebagai konfirmasi tunggal |
| Payload kosong, tanpa blok `## Code Explorer`, atau error | Ulangi sekali (tidak dihitung plafon). Gagal lagi: `KONTEKS` → lanjut tanpa konteks kode; `BUKTI` → `ELICIT — TERTAHAN` dengan sebab "bukti kode tidak dapat dikumpulkan" |

**Subagent mengembalikan:** blok `## Code Explorer` dengan `Mode`, `Tipe`, `Repo`, `Profil`, `Kedalaman`,
`Pemanggilan`, `Confidence`, lalu seksi `Ditemukan` (satu `#### P<n>` per butir beserta baris aspeknya),
`Tidak ditemukan`, dan `Belum disisir`.
