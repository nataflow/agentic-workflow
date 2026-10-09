# Template Prompt Penelusur Kode — `code-scout`

Pakai template ini saat `product:init` atau `product:discover` mendispatch subagent `product:code-scout` secara
langsung. Hanya untuk mode `NEW_FEATURE` dan `IMPROVEMENT`; `NEW_PRODUCT` tidak pernah mendispatch scout.

**Tujuan:** Memastikan fitur yang disebut peminta sudah ada atau belum (`CEK_FITUR`), atau memetakan kondisi sekarang
satu pilar (`PETA`) tanpa membaca kode di konteks utama. Hasilnya bahan bertanya, dan bukti `path:baris` untuk
pilar yang dikonfirmasi peminta.

**Dispatch setelah:**

- `CEK_FITUR` — `product:init` Phase 5, sesudah `charter.py guard` `PASS`.
- `PETA` — `product:discover` Phase 1, sesudah `CHARTER.md` ditulis `charter.py new`. Mode `IMPROVEMENT`: tiga
  dispatch (`Actors`, `Business Process`, `Business Rules`) dalam **satu pesan**. Mode `NEW_FEATURE`: satu dispatch
  `Actors` (peran yang sudah ada) dan, bila `--lingkup` menyebut area yang sudah ada, satu dispatch
  `Business Process` atas titik sambungnya.

````markdown
Telusuri kode untuk inisiasi produk.

- Mode: `{mode}`
- Fokus: `{fokus}`
- Root: `{root}`
- Batas: `{batas}`
- Pertanyaan:
{pertanyaan}
- Larangan: read-only; dilarang menyarankan solusi atau menilai kode; kuota 12 pemanggilan `Read`/`Grep`/`Glob`.
- Balikan: blok `## Product Scout` sesuai definisi agent-mu, tanpa teks lain.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{mode}` | gate pendispatch | **[REQUIRED]** `CEK_FITUR` (init) atau `PETA` (discover) |
| `{fokus}` | pilar yang dipetakan | **[REQUIRED]** `Actors`, `Business Process`, `Business Rules`; `-` untuk `CEK_FITUR` |
| `{root}` | `root=` keluaran `check_preconditions.py` (init) atau `charter.py new` / `check --gate discover` (discover) | **[REQUIRED]** Path absolut |
| `{batas}` | direktori yang disebut peminta, bila ada | **[OPTIONAL]** `-` bila kosong; dilarang menebak direktori dari nama stack |
| `{pertanyaan}` | `CEK_FITUR`: satu butir dari `--lingkup`. `PETA`: konsep pilar dalam kata-kata peminta (peran, langkah, aturan yang disebut) | **[REQUIRED]** 1–5 butir bernomor `  - P1: …` |

### Aturan untuk Pendispatch

**Gerbang masuk**, kegagalan mana pun membatalkan dispatch:

- **Plafon per charter**: `CEK_FITUR` satu kali (ditambah satu ulang bila user menyebut nama fitur lain); `PETA`
  maksimal satu per fokus di Phase 1 ditambah **satu** susulan untuk butir `Belum disisir` atau konsep baru dari
  jawaban peminta. Dispatch ulang karena balikan hilang dari percakapan atau karena gagal tidak dihitung.
- **Dispatch langsung tanpa skill pembungkus.** Doktrin penelusuran ada di definisi agent `code-scout`. Dilarang
  menyalin isi charter ke prompt; butir `pertanyaan` cukup kata-kata peminta.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Balikan tidak ditulis utuh ke berkas mana pun:

| Balikan subagent | Penanganan |
| --- | --- |
| `Ditemukan`, `CEK_FITUR` | `product:init` Phase 5 tabel verifikasi mode; balikan diteruskan ke discover sebagai `scout_awal` |
| `Ditemukan`, `PETA` | bahan opsi pertanyaan, atau baris `Asumsi:` beserta `` `path:baris` ``-nya di pilar yang sesuai. Asumsi itu wajib dikonfirmasi peminta sebelum `charter.py close`; sesudah dikonfirmasi, rujukannya tetap dan menjadi bukti kartu |
| `Tidak ditemukan` | `IMPROVEMENT`: tanyakan ke peminta bagaimana kondisi itu berjalan sekarang (mungkin manual, di luar aplikasi). `NEW_FEATURE`: kemampuan itu memang baru |
| `Belum disisir` | dispatch susulan bila plafon tersisa; selain itu tanyakan ke peminta |
| `Repo: tanpa kode` | mode codebase di folder tanpa kode tidak mungkin lolos `charter.py new`; laporkan sebagai galat ruang kerja |
| Payload kosong, tanpa blok `## Product Scout`, atau error | ulangi sekali. Gagal lagi: `NEW_FEATURE` → lanjut tanpa peta kode; `IMPROVEMENT` → `DISCOVER — TERTAHAN` dengan sebab "bukti kode tidak dapat dikumpulkan", karena Kondisi Sekarang kartu `IMPROVEMENT` wajib berbukti `path:baris` |

**Subagent mengembalikan:** blok `## Product Scout` dengan `Mode`, `Fokus`, `Repo`, `Pemanggilan`, lalu seksi
`Ditemukan`, `Tidak ditemukan`, dan `Belum disisir`.
