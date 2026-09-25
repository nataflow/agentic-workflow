# Template Prompt Explorer Kontrak — `code-explorer`, Profil B

Dimuat `system-analysis` sebelum Fase 4, sesudah simbol berubah teridentifikasi: tepat satu dispatch per taskdir, laporan di `{taskdir}/.explore/{slug}-blast.md`, menutup lima dimensi rawan bocor (2, 4, 11, 13, 16) bagian B `references/analysis-protocol.md`. Aturan pendispatch, patokan `Kedalaman`, dan larangan menyalin isi berkas di `explorer-surface.md` berlaku penuh; berkas ini hanya memuat yang khas Profil B. Jangan mencampur kerangka laporannya dengan Profil S dalam satu prompt.

______________________________________________________________________

## Profil B — Blast-Sweep Lima Dimensi (sebelum Fase 4)

````markdown
Objective: petakan dampak perubahan simbol {simbol_berubah} pada lima jalur rawan bocor berikut,
satu temuan berbukti `file:baris` per jalur:
{daftar_dimensi}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug penelusuran: {slug}-blast

Kedalaman: menyeluruh

Berkas laporan: {taskdir}/.explore/{slug}-blast.md

Aturan pelaporan fakta negatif: jalur yang sudah kau sisir dan terbukti tidak menyentuh simbol itu
dilaporkan eksplisit di `### Not Found` beserta direktori yang disisir. Jalur yang belum sempat kau
sisir dicatat di `### Gaps` dengan sebutan "belum disisir". Kedua status itu dilarang ditukar:
pendispatch memakai `### Not Found` sebagai vonis "tidak terdampak" pada impact map, sehingga jalur
yang belum disisir tetapi dilaporkan sebagai tidak ditemukan akan divonis aman tanpa pernah dilihat.

Format laporan: tulis persis tiga seksi berikut, urutan tetap, tanpa seksi tambahan. Rantai
pemanggil penuh dan pemetaan layer tidak diminta di sini — profil ini menagih status per dimensi,
bukan lintasan.

```markdown
### Summary
<Ringkas dampak simbol itu lintas kelima jalur, tanpa memvonis dimensi impact map — vonis milik
pendispatch. Tutup dengan baris: `confidence: high | medium | low`>

### Blast Map
<Satu baris per dimensi yang diminta, seluruhnya hadir meski kosong. Kolom `Status` hanya menerima
tiga nilai: `terdampak`, `disisir bersih`, atau `belum disisir` — jangan mengarang nilai keempat,
dan jangan mengosongkannya>

| Dimensi | Status | Disisir | Bukti Lokasi (`file:line`) | Catatan |
|---|---|---|---|---|
| <nama dimensi apa adanya dari prompt> | `terdampak` \| `disisir bersih` \| `belum disisir` | `<n> berkas` | `<path/ke/Berkas:baris>` | <apa yang menyentuh simbol itu, atau direktori yang sudah disisir> |

Kolom `Disisir` wajib berisi **angka**, bukan frasa. Ia yang membedakan "sudah dilihat dan bersih"
dari "tidak ketemu di pencarian pertama": status `disisir bersih` berangka nol atau tanpa angka
adalah kontradiksi, dan pendispatch memperlakukannya sebagai `belum disisir`. Pada dimensi test,
angkanya adalah jumlah berkas test yang benar-benar kau buka — kumpulkan daftarnya dengan `Glob`
lebih dulu, lalu cari di dalamnya nama simbol **dan** literal path endpoint sebagai string; endpoint
yang hanya muncul di dalam array atau tabel kasus tidak tertangkap pencarian berbasis simbol.

### Risks, Gaps & Not Found
- **Gaps**: <dimensi berstatus `belum disisir`, disebut satu per satu dengan alasan berhentinya>
- **Not Found**: <dimensi berstatus `disisir bersih`, beserta direktori yang sudah disisir>
```

Tulis laporan ke `Berkas laporan` lebih dulu, lalu kembalikan badan laporan yang sama ke context.
````

______________________________________________________________________

### Slot Hidrasi

| Slot | Profil | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- | --- |
| `{simbol_berubah}` | B | Simbol hasil Fase 1 yang kontraknya berubah | **[REQUIRED]** Nama tipe atau method konkret. Blast-sweep tanpa simbol tertentu adalah sapuan liar dan dilarang berangkat |
| `{daftar_dimensi}` | B | `references/analysis-protocol.md` bagian B nomor **2, 4, 11, 13, 16** | **[REQUIRED]** Salin nama kelima dimensi apa adanya sebagai lima baris berpoin. Dilarang meringkasnya jadi "lima dimensi rawan bocor" — subagent tidak membaca berkas protokol pendispatch, dan nama itu jadi kolom `Dimensi` `### Blast Map` |
| `{taskdir}` | S, B | Parameter `taskdir` skill | **[REQUIRED]** Path taskdir aktif apa adanya, mis. `backenddev/docs/2609041530-order-cancel`. Tanpa slot ini subagent tidak punya muara tulis dan menghentikan dispatch |
| `{konteks_diketahui}` | S, B | Fakta yang sudah terbukti di Fase 0 dan dispatch sebelumnya | **[OPTIONAL]** Cegah penelusuran ulang. Isi hanya fakta yang belum tertulis di laci `.explore/`: laporan dispatch sebelumnya dipanen sendiri subagent lewat Tahap 0, jadi jangan disalin ulang ke sini. Tidak tersedia → hapus barisnya utuh, bukan disisakan berlabel kosong |
| `{batas_cakupan}` | S, B | Baris `.claude/profile/backenddev/domain-map.md` yang cocok | **[OPTIONAL]** Disalin apa adanya. Dilarang mengarang glob. Domain tak terdaftar → hapus barisnya utuh; subagent memakai `source_root` dan mencatatnya di `### Caveats` (Profil S) atau `### Risks, Gaps & Not Found` (Profil B) |
| `{slug}` | S, B | Slug fitur taskdir ditambah pembeda permukaan | **[REQUIRED]** kebab-case, unik per dispatch. Profil B menambahkan sufiks `-blast` yang sudah tertulis di badan template — jangan ditulis dua kali. Slot ini juga menamai berkas laporan, sehingga slug kembar menimpa laporan dispatch sebelumnya |

### Penanganan Balikan

`system-analysis` memetakan balikan sendiri; tidak ada Universal Dispatch Envelope pada jalur ini.

| Balikan subagent | Penanganan `system-analysis` |
| --- | --- |
| `confidence: high` | Pointer `file:line` sah jadi bukti as-is Fase 1 dan dasar langsung kolom tipe Fase 3 |
| `confidence: medium` | Sah sebagai bukti as-is, **tetapi** field kontrak yang bersandar padanya wajib dikonfirmasi di Fase 2 (`AskUserQuestion`) atau turun ke `## Open questions`. Dilarang mengunci tabel kontrak Fase 3 di atasnya tanpa konfirmasi |
| `confidence: low`, atau objective tidak terjawab | Pertajam `{objective}` ke simbol konkret dan ulangi maks sekali dengan `{slug}` baru — slug baru juga mencegah laporan lama tertimpa. Tetap `low` → turun ke sapuan manual di sisa kuota, dan laporkan penyimpangannya pada baris `Explorasi` `## Output` |
| Baris `### Blast Map` berstatus `disisir bersih` | Vonis sah `Tidak terdampak` di `## Impact map` untuk dimensi itu |
| Baris `### Blast Map` berstatus `belum disisir`, atau `### Gaps` menyebut "belum disisir" | **Bukan** fakta negatif dan dilarang divonis `Tidak terdampak`. Tutup dengan dispatch lanjutan, atau naikkan jadi `## Open questions` PRD |
| Dimensi yang diminta tidak muncul sama sekali di `### Blast Map` | Perlakukan sebagai `belum disisir`, bukan sebagai aman. Dimensi yang hilang dari tabel tidak pernah disisir siapa pun |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maks sekali; tetap gagal → sapuan manual di sisa kuota dan laporkan penyimpangannya |

Profil B hanya menyetor tiga seksi, dan `### Blast Map` adalah satu-satunya sumber status per dimensi `## Impact map` — `### Summary`-nya orientasi, bukan vonis.

**Subagent mengembalikan:** Badan laporan tiga seksi sesuai blok `Format laporan` di atas, ditutup baris `confidence: high | medium | low` pada `### Summary`, plus path berkas yang ditulisnya.
