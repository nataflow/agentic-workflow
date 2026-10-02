# Template Prompt Penelusur Kode — `code-scout`

Pakai template ini saat `elicit` mendispatch subagent penelusur kode dangkal (`code-scout`) secara langsung.

**Tujuan:** Mengumpulkan bukti `path:baris` (tiket `TECH`) atau konteks singkat tentang apa yang sudah ada di kode (tipe lain) tanpa membaca kode di konteks utama. Hasilnya dipakai sebagai bahan pertanyaan, bukan sebagai fakta dari peminta.

**Dispatch setelah:** `elicit` Phase 1. Brief atau permintaan sudah dipetakan ke pilar, dan `TICKET.md` sudah ditulis sekali.

````markdown
Telusuri kode secara dangkal untuk elisitasi satu tiket analyst.

- Mode: `{mode}`
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
| `{mode}` | Frontmatter `type` `TICKET.md` | **[REQUIRED]** `TECH` → `BUKTI`; tipe lain → `KONTEKS` |
| `{root}` | Baris `root=` keluaran `ticket.py new` atau `check --gate elicit` | **[REQUIRED]** Path absolut |
| `{batas}` | Direktori yang disebut peminta, bila ada | **[OPTIONAL]** `-` bila kosong; dilarang menebak direktori dari nama stack |
| `{pertanyaan}` | `BUKTI`: tiap klaim kondisi sekarang di brief peminta. `KONTEKS`: konsep yang disebut permintaan (layar, menu, laporan, status, data) | **[REQUIRED]** 1–5 butir bernomor `  - P1: …`, memakai kata-kata peminta apa adanya |

### Aturan untuk Pendispatch

**Gerbang masuk**, kegagalan mana pun membatalkan dispatch:

- **Plafon 2 dispatch per sesi elisitasi**: satu di Phase 1, dan satu susulan untuk butir `Belum disisir` atau klaim baru dari jawaban peminta. Dispatch ketiga dilarang. Sisa pertanyaannya ditanyakan ke peminta.
- **Dispatch langsung tanpa skill pembungkus.** Doktrin penelusuran ada di `agents/code-scout.md`. Dilarang menyalin isi tiket ke prompt. Butir `pertanyaan` cukup kata-kata peminta.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Balikan tidak ditulis ke berkas mana pun. Pakai isinya langsung di Phase 1–2:

| Balikan subagent | Penanganan `elicit` |
| --- | --- |
| `Ditemukan`, mode `BUKTI` | Catat `` `path:baris` ``-nya di pilar `Kondisi Saat Ini`. Klaim yang dibantah kode ditanyakan ke peminta di giliran berikutnya, bukan dikoreksi diam-diam |
| `Ditemukan`, mode `KONTEKS` | Bahan menyusun opsi pertanyaan dalam bahasa yang terlihat pengguna, atau baris `Asumsi:` tanpa rujukan berkas. Dilarang ditulis sebagai fakta pilar, dan dilarang menyalin `path:baris` ke catatan (`validate_doc.py --kind elicit` menolaknya) |
| `Tidak ditemukan` | `BUKTI`: klaim tidak terbukti, jadi tanyakan ke peminta. `KONTEKS`: konsepnya mungkin belum ada, jadi tanyakan sebagai kemampuan baru, bukan sebagai fakta |
| `Belum disisir` | Pakai dispatch susulan bila plafon tersisa. Selain itu tanyakan ke peminta |
| `Repo: tanpa kode` | `KONTEKS` → lanjut tanpa konteks kode. `BUKTI` → `ELICIT — TERTAHAN`: tiket `TECH` wajib tinggal di repo yang diubah |
| Payload kosong, tanpa blok `## Code Scout`, atau error | Ulangi sekali (tidak dihitung plafon). Gagal lagi: `KONTEKS` → lanjut tanpa konteks kode; `BUKTI` → `ELICIT — TERTAHAN` dengan sebab "bukti kode tidak dapat dikumpulkan" |

**Subagent mengembalikan:** blok `## Code Scout` dengan `Mode`, `Repo`, `Pemanggilan`, lalu seksi `Ditemukan`, `Tidak ditemukan`, dan `Belum disisir`.
