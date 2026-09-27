# Template Prompt Explorer Layar & Cabang State — `code-explorer`

Gunakan template ini saat `ui-design` mendispatch subagent penelusur kode (`code-explorer`) secara langsung.

**Tujuan:** Membuktikan komponen layar, sumber props, dan cabang state yang sudah ada di repo sebelum mockup dirancang — supaya `UI.md` berdiri di atas komponen aktual, bukan di atas ingatan.

**Dispatch setelah:** Phase 0 (Data Prerequisites & Profile Ingestion) menemukan bahwa layar yang ditanyakan melintasi lebih dari satu berkas, yang dicari relasi (pemilik props, sumber state, konsumen view-model), simbol acuan tak muncul di sapuan pertama, **atau** kuota sapuan habis.

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug artefak: {slug}

Laci: {laci}

Kedalaman: {kedalaman}

Batas pertanyaan: petakan komponen, props, dan cabang state yang sudah ada. Dilarang merancang
layout baru, mengusulkan komponen pengganti, menetapkan cabang state baru, atau menulis JSX/markup —
keempatnya milik pendispatch. Tiap komponen yang kau sebut wajib bersandar `file:baris` yang kau baca
sendiri.

Format laporan: kembalikan seksi berikut, urutan tetap, anggaran 400–900 token. Seksi yang tidak
punya temuan dihapus, bukan diisi "tidak ada".

```markdown
### Summary
<2–3 kalimat yang langsung menjawab objective. Tutup dengan baris: `confidence: high | medium | low`>

### Flow
<satu baris rantai aktual: layar -> orkestrasi -> view-model -> props yang dirender>

### Layers touched
- <layer>: <NamaSimbol> — <satu baris ringkas; sebut komponen, tipe props, atau state>

### Key pointers
- `path/to/File.ext:42` — <catatan 5–10 kata, bukan potongan kode>
(maksimum 8 pointer terpenting; dahulukan komponen layar, tipe `*UI`, dan cabang state yang ada)

### Rules & constraints
- <cabang state yang sudah ditangani, batas framework, design token, atau invariant beserta bukti `file:baris`>

### Config / infra
- <letak design token, komponen bersama, provider tema, breakpoint atau safe area>

### Risks
- <layar atau komponen lain yang ikut terdampak bila komponen ini diubah>

### Caveats
<unknown, ambiguitas kode, atau penyimpangan konvensi dari `surface-map.md` profil>

### Not Found
<komponen, tipe props, atau cabang state yang dicari tetapi TIDAK ditemukan, beserta direktori yang sudah disisir>

### Full detail
<path Bentuk B yang benar-benar ditulis>
```

Tulis Bentuk B lebih dulu ke laci kerja — `{laci}<slug>.md` bila baris Laci terisi,
`.frontenddev/explore/<YYMMDDhhmm>-<slug>.md` bila kosong — lalu kembalikan laporan di atas ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Layar, komponen, atau state konkret yang belum pasti bentuknya | **[REQUIRED]** Satu pertanyaan fokus tunggal, mis. "komponen mana yang merender daftar order dan props apa yang diterimanya" |
| `{slug}` | Slug taskdir ditambah penanda layar | **[REQUIRED]** Kebab-case; ia menamai berkas Bentuk B, jadi slug kembar membuat laporan tertukar |
| `{kedalaman}` | Keputusan pendispatch | **[REQUIRED]** `ringkas` untuk memastikan satu komponen; `menyeluruh` bila layar menuntut rantai konsumen dan sumber propsnya |
| `{konteks_diketahui}` | Baris `FLOW.md` atau profil yang sudah memetakan layar itu | **[OPTIONAL]** Isi hanya fakta yang sudah terbukti. Tidak tersedia → hapus barisnya utuh. Isi hanya fakta yang **belum** ada di laci: laporan penelusuran sebelumnya dipanen subagent sendiri di Fase 0b, jadi menyalinnya ke sini membayar dua kali untuk isi yang sama |
| `{laci}` | Taskdir aktif bila sudah ada | **[OPTIONAL]** Isi `<taskdir>/.explore/` supaya laporan mendarat di laci taskdir dan laporan sebelumnya dapat dipanen subagent. Dispatch yang berjalan sebelum taskdir lahir mengosongkannya; subagent jatuh ke `.frontenddev/explore/` |
| `{batas_cakupan}` | `structure.md` profil untuk direktori komponen | **[OPTIONAL]** Mis. `src/features/orders/components/**`. Dilarang mengarang glob sendiri |

### Aturan untuk Pendispatch

- **Dispatch langsung tanpa skill pembungkus**: seluruh doktrin penelusuran — gerbang masuk, dua fase eksplorasi, formula offset, dan kerangka Bentuk B — duduk di `agents/code-explorer.md`. Dilarang memanggil skill perantara atau menyalin potongan doktrin itu ke dalam prompt.
- **Satu pertanyaan per dispatch**: dua pertanyaan terpisah didispatch bergantian agar ringkasan tetap padat.
- **Dilarang menyalin isi berkas**: jangan salin isi profil, adapter, `FLOW.md`, atau kode ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Read-only mutlak**: dilarang menyuruh subagent merancang layout, memilih komponen pengganti, atau menetapkan cabang state baru.
- **Ambiguitas monorepo diselesaikan di hulu**: tetapkan app target di `{batas_cakupan}` — komponen web dan mobile berbeda, dan subagent dilarang bertanya balik.
- **Periksa `.frontenddev/` terabaikan git**: periksa `.gitignore` memuat baris `.frontenddev/` dan `.explore/` sebelum dispatch pertama. Belum ada — hentikan dispatch dan rutekan ke `frontend:profile` mode REFRESH, pemilik tunggal baris itu; dilarang menuliskannya sendiri karena gate ini tidak meng-commit `.gitignore`. Tanpa baris itu laporan scratch bocor ke working tree dan merusak gerbang "tree bersih" milik `code-implementor`.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau placeholder `TBD`/`TODO`.

### Penanganan Balikan

`ui-design` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `ui-design` |
| --- | --- |
| `confidence: high` atau `medium` | Pakai pointer `file:baris` sebagai bukti as-is untuk menulis mockup dan cabang state di `UI.md`. Dilarang membaca ulang berkas yang sudah diringkas explorer |
| `confidence: low`, atau objective tidak terjawab | Pertajam `{objective}` agar menyebut komponen konkret, ulangi maksimum sekali dengan `{slug}` baru; tetap gagal → sapu manual dan catat batasnya di dokumen UI |
| `### Not Found` terisi | Fakta negatif yang sah: komponennya memang belum ada, jadi layar itu pekerjaan baru. Dilarang menulis `UI.md` seolah komponennya sudah tersedia |
| `### Rules & constraints` menyebut cabang state yang sudah ditangani | Serap apa adanya; enam cabang state `UI.md` dinilai terhadap yang sudah ada, bukan ditulis ulang dari nol |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maksimum sekali, lalu sapu manual |

**Subagent mengembalikan:** Ringkasan Bentuk A 400–900 token sesuai blok `Format laporan`, ditutup baris `confidence` pada `### Summary` dan path Bentuk B pada `### Full detail`.
