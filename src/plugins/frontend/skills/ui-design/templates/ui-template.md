# UI Template — `ui-design`

Rumah kanonik bentuk `frontenddev/docs/<YYMMDDhhmm>-<slug>/UI.md`. Bagian 1 adalah kerangka yang disalin ke artefak, bagian 2 aturan yang ditagih `skills/_common/validate_doc.py --kind ui` dan self-test penulis, bagian 3 contoh terisi yang **tidak** tersalin ke artefak. `SKILL.md` merujuk ke sini dan dilarang menulis ulang kerangkanya.

---

## 1. Template Kanonik UI.md

````markdown
---
status: DRAFT
slug: <slug>
order: 20
stack: <stack-id>
based_on: <sha 7 digit HEAD saat artefak ditulis> (<YYYY-MM-DD>)
---

# UI Design — <Nama Layar / Fitur>

Rancangan antarmuka, hierarki prioritas informasi, dan enam cabang state untuk <tujuan layar ringkas>.

## 1. Mockup Antarmuka (Layout Mockup ASCII)

```
+--------------------------------------------------+
| [<] <Judul Layar>                       [Aksi]   |
+--------------------------------------------------+
```

## 2. Hierarki Prioritas Informasi (Information Priority)

| Elemen Antarmuka Pengguna | Tingkat Prioritas | Bobot Visual & Penempatan | Alasan Desain |
|---|---|---|---|
| <elemen> | Primary (P1) \| Secondary (P2) \| Tertiary (P3) | <token visual dari `visual.md` profil> | <alasan> |

## 3. Cabang State Tampilan (The 6-State Branches Matrix)

### ST-1. State Normal (Data Terisi / Ready)
- <perilaku>

### ST-2. State Loading (Skeleton Shimmer)
- <perilaku; dimensi skeleton = dimensi konten, CLS aman>

### ST-3. State Kosong (Empty State)
- <judul, teks bantuan, CTA>

### ST-4. State Error (Connection / Server Failure)
- <pesan manusiawi + aksi pemulihan yang memanggil handler Controller>

### ST-5. State Initial / Idle
- <perilaku>

### ST-6. State Stale / Mutating (Optimistic Overlay)
- <perilaku; pencegahan double-submit>

## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)

| Elemen UI | Field Data yang Ditampilkan | Asal Sumber Data | Keterangan & Transformasi |
|---|---|---|---|

## 5. Batasan State Scope & Isolasi Komponen
- **Koordinasi Sentral**: <state yang dipegang Controller layar>
- **Komponen Presentasi Murni**: <komponen anak tanpa query mandiri>
- **Batas Platform**: <dari `## UI & navigation surface` adapter>
````

---

## 2. Aturan Validasi

**Mekanis** — ditagih `validate_doc.py --kind ui`; `FAIL` menahan `chain.py draft` dan `chain.py approve`:

1. **Frontmatter**: `status` hanya `DRAFT` atau `APPROVED` (yang kedua hanya lewat `chain.py approve`); `slug`, `stack` terisi; `order: 20`; `based_on` berpola `<sha 7 digit> (YYYY-MM-DD)`.
2. **Struktur**: tepat satu H1 berawalan `# UI Design — `, dan lima heading `##` persis urutan bagian 1. Seksi 1 memuat blok mockup berpagar.
3. **Cabang state**: heading `### ST-{n}. State <jenis> ...` berurutan dari `ST-1`. **Tiap layar tepat enam ST berurutan** (layar 1 = `ST-1..ST-6`, layar 2 = `ST-7..ST-12`, dst.), satu per jenis cabang: normal, loading, kosong, error, initial, stale/mutating. Urutan di dalam blok bebas. Jenis dibaca dari kata kunci judul (`Normal`/`Ready`, `Loading`/`Skeleton`, `Kosong`/`Empty`, `Error`/`Failure`/`Gagal`, `Initial`/`Idle`, `Stale`/`Mutating`/`Optimistic`). Cabang yang tidak relevan untuk suatu layar tetap ditulis beserta alasannya. Bila lebih dari satu layar, sebut layarnya di judul (`### ST-7. State Normal — Layar 2: Pembayaran`). `validate_doc.py --kind contract` menagih tiap `ST-{n}` dipikul minimal satu AC.
4. **Placeholder**: nol `TBD`/`TODO`/`diisi nanti` dan nol slot `<...>` berspasi di luar blok kode.

**Semantik** — self-test penulis sebelum `chain.py draft`:

5. Tiap token visual (warna, spacing, radius, tipografi) di seksi 2 berasal dari `visual.md` profil; nilai literal tanpa token dicatat sebagai keputusan eksplisit, bukan diselipkan.
6. Cabang ST-4 menyebut aksi pemulihan yang benar-benar dapat dipanggil (handler Controller), bukan hanya pesan.
7. Batas platform seksi 5 disalin dari adapter stack repo — dilarang menulis aturan mobile untuk repo web atau sebaliknya.
8. Tiap elemen seksi 4 punya asal sumber yang juga muncul di Data Demands `FLOW.md` (bila `sections` memuat `flow`) atau akan dikunci `CONTRACT.md`.

---

## 3. Contoh Terisi — `order-checkout` Screen 1 (tidak tersalin ke artefak)

````markdown
---
status: DRAFT
slug: order-checkout
order: 20
stack: react-vite
based_on: 3f9c2ab (2026-09-23)
---

# UI Design — Ringkasan Keranjang

Rancangan antarmuka, hierarki prioritas informasi, dan enam cabang state untuk layar peninjauan keranjang sebelum bayar.

## 1. Mockup Antarmuka (Layout Mockup ASCII)

```
+--------------------------------------------------+
| [<] Keranjang (3 item)                           |
+--------------------------------------------------+
| [img] Kopi Arabika 250g      x2      Rp 130.000  |
| [img] Filter V60             x1      Rp  45.000  |
+--------------------------------------------------+
| Total                                Rp 175.000  |
| [=============== LANJUT KE PEMBAYARAN ==========] |
+--------------------------------------------------+
```

## 2. Hierarki Prioritas Informasi (Information Priority)

| Elemen Antarmuka Pengguna | Tingkat Prioritas | Bobot Visual & Penempatan | Alasan Desain |
|---|---|---|---|
| CTA Lanjut | Primary (P1) | `button.primary` penuh lebar di bawah | Aksi penyelesaian tugas |
| Total | Primary (P1) | `text.lg` tebal | Angka pengambil keputusan |

## 3. Cabang State Tampilan (The 6-State Branches Matrix)

### ST-1. State Normal (Data Terisi / Ready)
- Daftar item dengan subtotal per baris; CTA aktif.

### ST-2. State Loading (Skeleton Shimmer)
- Tiga baris skeleton setinggi baris item; CTA disabled.

### ST-3. State Kosong (Empty State)
- "Keranjangmu kosong" + CTA *Belanja Sekarang* ke `/`.

### ST-4. State Error (Connection / Server Failure)
- Banner "Gagal memuat keranjang" + *Coba Lagi* memanggil `refetch` dari `useCheckoutPage`.

### ST-5. State Initial / Idle
- Sama dengan ST-2 sampai query pertama berangkat.

### ST-6. State Stale / Mutating (Optimistic Overlay)
- Ubah kuantitas memperbarui baris seketika; rollback bila mutasi gagal; CTA disabled selama mutasi.

## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)

| Elemen UI | Field Data yang Ditampilkan | Asal Sumber Data | Keterangan & Transformasi |
|---|---|---|---|
| Baris item | `name`, `qty`, `subtotalFormatted` | View-Model | `priceCents × qty` diformat Rupiah |

## 5. Batasan State Scope & Isolasi Komponen
- **Koordinasi Sentral**: query keranjang dan mutasi kuantitas di `useCheckoutPage`.
- **Komponen Presentasi Murni**: `CartRow` menerima `CartRowUI` via props.
- **Batas Platform**: fokus keyboard terlihat; breakpoint 640/768/1024 dari adapter.
````
