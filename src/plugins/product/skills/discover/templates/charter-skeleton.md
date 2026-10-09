# CHARTER Skeleton — `discover`

Rumah kanonik **frontmatter** dan seksi `## Catatan Elisitasi` di `product/<slug>/CHARTER.md` — satu-satunya artefak
yang disunting skill; `review.md` di sebelahnya jejak vonis reviewer terakhir, hanya ditulis `charter.py`. Bagian 1
kerangka yang ditulis skrip, bagian 2 aturan yang ditagih `skills/_common/validate_doc.py --kind notes` dan self-test
penulis, bagian 3 contoh terisi yang **tidak** tersalin ke artefak. Kartu enam pilar di atas catatan milik
`skills/spec/templates/charter-template.md`.

`## Catatan Elisitasi` adalah **catatan kerja**: konteks minimum yang lolos guard, permintaan asli, fakta per pilar,
riwayat tanya-jawab, dan pertanyaan yang masih menunggu jawaban. Seksi ini yang membuat elisitasi dapat dilanjutkan
lintas sesi, dan satu-satunya masukan tertulis `product:spec`. Ia selalu H2 **terakhir**; `spec` menyisipkan kartu di
antara H1 dan seksi ini tanpa menyentuh isinya.

---

## 1. Template Kanonik — CHARTER.md Awal

`charter.py new` menulis berkas baru persis kerangka ini — Konteks Awal dari `--untuk`/`--masalah`/`--lingkup`,
permintaan asli dari `--request`, kedua sidik dihitung skrip — lalu `product:discover` mengisi pilarnya.
`tests/product/test_discover_skeleton.py` menagih kerangka skrip sama dengan blok di bawah. Mode `NEW_PRODUCT`:

````markdown
---
status: ELICITATION
mode: <NEW_PRODUCT | NEW_FEATURE | IMPROVEMENT>
slug: <slug charterdir>
requester: <"nama atau peran peminta">
created: <YYYY-MM-DD>
revision: 0
review: -
review_round: 0
context_hash: <sidik 12 hex Konteks Awal>
request_hash: <sidik 12 hex permintaan asli>
elicit_hash: -
elicit_log: 0
---

# <judul kerja singkat>

## Catatan Elisitasi

### Konteks Awal

- **Untuk siapa**: <segmen pengguna utama>
- **Masalah utama**: <masalah yang diselesaikan>
- **Domain**: <domain atau konteks pakai>

### Permintaan Asli

> <permintaan user apa adanya, tanpa disunting>

### Fakta

#### Purpose
_(belum terjawab)_

#### Actors
_(belum terjawab)_

#### Business Process
_(belum terjawab)_

#### Business Rules
_(belum terjawab)_

#### Success Criteria
_(belum terjawab)_

#### Scope
_(belum terjawab)_

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|

### Pertanyaan Terbuka

- Tidak ada.
````

Mode codebase memakai label Konteks Awal berikut, urutan persis; seksi lain identik:

| Mode | Butir 1 (`--untuk`) | Butir 2 (`--masalah`) | Butir 3 (`--lingkup`) |
|---|---|---|---|
| `NEW_FEATURE` | `Pengguna` | `Yang belum bisa dilakukan` | `Area` |
| `IMPROVEMENT` | `Yang terdampak` | `Yang salah atau kurang` | `Fitur` |

Kepemilikan frontmatter: `mode`, `slug`, `requester`, `created`, `context_hash`, `request_hash`, dan
`status: ELICITATION` awal ditulis `charter.py new`; `status: DRAFT` dari elisitasi, `elicit_hash`, dan `elicit_log`
ditulis **hanya** `charter.py close`; `status` lain, `revision`, `revision_base`, `review`, `review_round`,
`approved*`, `approval`, `reopen*`, dan `cancel_reason` ditulis **hanya** `charter.py`; H1 final ditulis `spec`.
Penulis mana pun menyalin field milik pihak lain apa adanya.

---

## 2. Aturan Validasi

Ditagih `validate_doc.py --kind notes` (mekanis) — dilarang menulis ulang aturannya di `SKILL.md`:

1. Frontmatter: `status` ELICITATION/DRAFT/APPROVED, `mode` sah, `slug` = nama charterdir, `created` YYYY-MM-DD,
   `requester` terisi, `context_hash` dan `request_hash` sidik 12 hex.
2. Satu H1; `## Catatan Elisitasi` H2 terakhir dengan lima H3 persis urutan bagian 1, tiap heading sekali.
3. `### Konteks Awal`: tiga butir berlabel mode itu, masing-masing lolos guard konteks minimum, dan sama dengan
   yang dimateraikan `context_hash`.
4. `### Permintaan Asli`: blockquote `> `, sama dengan yang dimateraikan `request_hash`.
5. Enam pilar `####` persis urutan bagian 1; catatan tertutup (status selain ELICITATION) menuntut keenamnya terisi.
6. Log: header lima kolom, baris `| n | YYYY-MM-DD | pertanyaan | jawaban | sumber |` bernomor urut dari 1.
7. Pertanyaan terbuka: `- **Q-n** [MEMBLOKIR | TIDAK MEMBLOKIR]: <tanya> — menunggu: <siapa>` atau `- Tidak ada.`;
   catatan tertutup tanpa `MEMBLOKIR`.
8. Nol placeholder di luar Permintaan Asli dan Log.
9. Catatan tertutup tanpa satu pun `Asumsi:` di `### Fakta`.
10. `NEW_PRODUCT`: nol rujukan `path:baris`. Mode codebase: tiap rujukan ada di repo.

Self-test semantik penulis sebelum `charter.py close` (tidak dapat ditagih skrip):

11. Tiap kalimat pilar berasal dari permintaan asli atau baris log; yang disimpulkan analis masih berlabel `Asumsi:`.
12. **Purpose** menyebut masalah, siapa yang mengalaminya, dan kenapa sekarang — bukan daftar fitur.
13. **Actors** menyebut tiap peran beserta yang boleh dan tidak boleh dilakukannya; mode codebase menandai peran
    yang sudah ada di aplikasi (dari balikan scout yang dikonfirmasi) dan yang baru.
14. **Business Process** punya pemicu, langkah berurutan beraktor, dan hasil akhir; `IMPROVEMENT` memisahkan
    kondisi sekarang (berbukti) dari kondisi target.
15. **Business Rules** memuat angka dan ambang yang diucapkan peminta, beserta pengecualiannya atau pernyataan
    eksplisit "tidak ada pengecualian".
16. **Success Criteria** berangka dan terkait masalah di Purpose — bukan "fitur selesai dibuat".
17. **Scope** memisahkan yang masuk versi pertama dari yang tidak, beserta alasannya.

---

## 3. Contoh Terisi — `kasir-umkm` (tidak tersalin ke artefak)

```markdown
### Konteks Awal

- **Untuk siapa**: Pemilik warung makan dan kasirnya
- **Masalah utama**: kas dicatat di buku tulis sehingga laba harian tidak diketahui
- **Domain**: keuangan usaha mikro

### Permintaan Asli

> saya ingin membuat aplikasi keuangan untuk UMKM

### Fakta

#### Purpose
Pemilik warung makan tidak tahu laba harian karena penjualan dan belanja dicatat di buku tulis yang sering tidak
lengkap; dua pemilik yang ditanya kehilangan rata-rata 1 jam tiap malam untuk merekap.

#### Actors
Pemilik warung mencatat belanja dan melihat laba; tidak mencatat penjualan. Kasir mencatat penjualan; tidak boleh
melihat laba.

#### Business Process
Kasir mencatat tiap penjualan saat transaksi; pemilik mencatat belanja harian; sesudah warung tutup pemilik melihat
laba hari itu.

#### Business Rules
Belanja di atas Rp1.000.000 wajib disertai foto nota; tidak ada pengecualian.

#### Success Criteria
Pemilik mengetahui laba hari itu dalam 5 menit sesudah warung tutup, tanpa merekap manual.

#### Scope
Versi pertama: catat penjualan, catat belanja, laba harian. Stok bahan dan multi-cabang belum — tiket terpisah nanti.

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|
| 1 | 2026-10-09 | Siapa yang mencatat penjualan? | Kasir, saat transaksi | Budi (PO) |
| 2 | 2026-10-09 | Bolehkah kasir melihat laba? | Tidak | Budi (PO) |
| 3 | 2026-10-09 | Kapan disebut berhasil? | Laba ketahuan ≤ 5 menit sesudah tutup | Budi (PO) |

### Pertanyaan Terbuka

- **Q-1** [TIDAK MEMBLOKIR]: Apakah laba perlu dibandingkan dengan hari sebelumnya? — menunggu: Budi (PO)
```
