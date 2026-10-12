# Template Prompt Penelusur Kode — `code-scout` untuk Notulen

Pakai template ini saat `notulen` mendispatch subagent penelusur kode dangkal (`code-scout`) secara langsung.

**Tujuan:** Mengumpulkan konteks singkat tentang istilah, singkatan, layar, menu, laporan, atau fitur yang disebut
catatan rapat, tanpa membaca kode di konteks utama. Hasilnya dipakai sebagai bahan pertanyaan klarifikasi ke
pencatat, bukan sebagai isi notulen.

**Dispatch setelah:** `notulen` Phase 1 `NEW PASS` (atau Phase 0 untuk notulen `DRAFT` yang dilanjutkan), di awal
Phase 2, dan hanya bila catatan menyebut konsep sistem atau produk. Subagent berjalan sementara Phase 2 menata ulang,
dan balikannya baru dipakai di Phase 3.

````markdown
Telusuri kode secara dangkal untuk klarifikasi satu notulen rapat analyst.

- Mode: `KONTEKS`
- Root: `{root}`
- Batas: `{batas}`
- Pertanyaan:
{pertanyaan}
- Larangan: read-only; berhenti di bukti pertama tiap butir; dilarang menelusuri flow, alur, edge case, atau
  menyarankan solusi; kuota 8 pemanggilan `Read`/`Grep`/`Glob`.
- Balikan: blok `## Code Scout` sesuai definisi agent-mu, tanpa teks lain.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{root}` | Baris `root=` keluaran `notulen.py new`, atau kunci `root` `notulen.py state --json` | **[REQUIRED]** Path absolut |
| `{batas}` | Direktori yang disebut catatan atau pencatat, bila ada | **[OPTIONAL]** `-` bila kosong; dilarang menebak direktori dari nama stack |
| `{pertanyaan}` | Konsep sistem yang disebut catatan: singkatan atau nama yang ambigu, layar, menu, laporan, status, data, fitur | **[REQUIRED]** 1–5 butir bernomor `  - P1: …`, memakai kata-kata catatan apa adanya |

Mode selalu `KONTEKS`. Notulen merekam rapat, bukan membuktikan klaim, jadi mode `BUKTI` tidak dipakai di sini.

### Aturan untuk Pendispatch

**Gerbang masuk**, kegagalan mana pun membatalkan dispatch:

- **Ada konsep sistem.** Catatan tanpa istilah produk atau sistem (rapat anggaran, rekrutmen, jadwal acara) tidak
  di-scout. Kode tidak bisa menjelaskan isi rapat semacam itu.
- **Plafon 2 dispatch per notulen**: satu di awal Phase 2, dan satu susulan sebelum giliran klarifikasi kedua untuk
  butir `Belum disisir` atau istilah baru dari jawaban pencatat. Dispatch ketiga dilarang. Sisa pertanyaannya
  ditanyakan ke pencatat. Dispatch ulang karena balikan hilang dari percakapan (diringkas otomatis, atau sesi baru)
  tidak dihitung, sama seperti ulangan karena gagal.
- **Dispatch langsung tanpa skill pembungkus.** Doktrin penelusuran ada di `agents/code-scout.md`. Dilarang menyalin
  catatan rapat, nama peserta, atau isi pembahasan ke prompt, karena notulen bisa memuat info sensitif. Butir
  `pertanyaan` cukup istilahnya.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Balikan tidak ditulis ke berkas mana pun, termasuk `NOTULEN.md`. Pakai isinya langsung di Phase 3:

| Balikan subagent | Penanganan `notulen` |
| --- | --- |
| `Ditemukan` | Bahan menyusun opsi pertanyaan dalam bahasa yang terlihat pengguna, misalnya "INV" ditawarkan sebagai opsi "layar Invoice". Boleh juga ditulis sebagai baris `Asumsi:` di Pembahasan, tanpa rujukan berkas, yang wajib dikonfirmasi pencatat sebelum `final`. Dilarang ditulis sebagai isi notulen, dan dilarang menyalin `path:baris` ke notulen (`notulen.py check` menolaknya) |
| `Tidak ditemukan` | Dilarang menyimpulkan apa pun ke notulen, termasuk "fitur itu belum ada". Bila istilahnya tetap ambigu, tanyakan ke pencatat tanpa opsi dari kode |
| `Belum disisir` | Pakai dispatch susulan bila plafon tersisa. Selain itu tanyakan ke pencatat |
| `Repo: tanpa kode` | Lanjut tanpa konteks kode |
| Payload kosong, tanpa blok `## Code Scout`, atau error | Ulangi sekali (tidak dihitung plafon). Gagal lagi → lanjut tanpa konteks kode. Kegagalan scout tidak pernah menahan notulen |

**Subagent mengembalikan:** blok `## Code Scout` dengan `Mode`, `Repo`, `Pemanggilan`, lalu seksi `Ditemukan`,
`Tidak ditemukan`, dan `Belum disisir`.
