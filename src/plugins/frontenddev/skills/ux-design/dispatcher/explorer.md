# Template Prompt Explorer Rute & Navigasi — `code-explorer`

Gunakan template ini saat `ux-design` mendispatch subagent penelusur kode (`code-explorer`) secara langsung.

**Tujuan:** Membuktikan rute, parameter, guard, dan sumber data yang sudah ada di repo sebelum alur pengguna dirancang — supaya `FLOW.md` berdiri di atas navigasi aktual, bukan di atas asumsi.

**Dispatch setelah:** Phase 0 (Navigation Orientation & Profile Ingestion) menemukan bahwa rute atau alur yang ditanyakan melintasi lebih dari satu berkas, yang dicari relasi (pemanggil rute, pemilik guard, sumber data layar), simbol acuan tak muncul di sapuan pertama, **atau** kuota sapuan habis.

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug artefak: {slug}

Laci: {laci}

Kedalaman: {kedalaman}

Batas pertanyaan: petakan rute, parameter, guard, dan sumber data yang sudah ada. Dilarang merancang
alur baru, mengusulkan langkah pengguna, menetapkan deep-link baru, atau menulis potongan kode —
keempatnya milik pendispatch. Tiap rute yang kau sebut wajib bersandar `file:baris` yang kau baca
sendiri.

Format laporan: kembalikan seksi berikut, urutan tetap, anggaran 400–900 token. Seksi yang tidak
punya temuan dihapus, bukan diisi "tidak ada".

```markdown
### Summary
<2–3 kalimat yang langsung menjawab objective. Tutup dengan baris: `confidence: high | medium | low`>

### Flow
<satu baris rantai navigasi aktual: rute -> layar -> orkestrasi -> sumber data>

### Layers touched
- <layer>: <NamaSimbol> — <satu baris ringkas; sebut rute, parameter, atau guard>

### Key pointers
- `path/to/File.ext:42` — <catatan 5–10 kata, bukan potongan kode>
(maksimum 8 pointer terpenting; dahulukan berkas rute, guard, dan pembaca parameter URL)

### Rules & constraints
- <guard rute, redirect, aturan deep-link, batas framework, atau invariant beserta bukti `file:baris`>

### Config / infra
- <konfigurasi router, pola parameter dinamis, search params, alias path, env var>

### Risks
- <alur atau layar lain yang ikut terdampak bila rute ini diubah>

### Caveats
<unknown, ambiguitas kode, atau penyimpangan konvensi dari `surface-map.md` profil>

### Not Found
<rute, guard, atau simbol yang dicari tetapi TIDAK ditemukan, beserta direktori yang sudah disisir>

### Full detail
<path Bentuk B yang benar-benar ditulis>
```

Tulis Bentuk B lebih dulu ke laci kerja — `{laci}<slug>.md` bila baris Laci terisi,
`.frontenddev/explore/<YYMMDDhhmm>-<slug>.md` bila kosong — lalu kembalikan laporan di atas ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Rute, layar, atau alur konkret yang belum pasti bentuknya | **[REQUIRED]** Satu pertanyaan fokus tunggal, mis. "rute mana yang menampilkan detail order dan parameter apa yang dibacanya" |
| `{slug}` | Slug taskdir ditambah penanda alur | **[REQUIRED]** Kebab-case; ia menamai berkas Bentuk B, jadi slug kembar membuat laporan tertukar |
| `{kedalaman}` | Keputusan pendispatch | **[REQUIRED]** `ringkas` untuk memastikan satu rute; `menyeluruh` bila alur menuntut rantai layar dan konsumennya |
| `{konteks_diketahui}` | Baris `surface-map.md` profil yang sudah memetakan rute itu | **[OPTIONAL]** Isi hanya fakta yang sudah terbukti. Tidak tersedia → hapus barisnya utuh. Isi hanya fakta yang **belum** ada di laci: laporan penelusuran sebelumnya dipanen subagent sendiri di Fase 0b, jadi menyalinnya ke sini membayar dua kali untuk isi yang sama |
| `{laci}` | Taskdir aktif bila sudah ada | **[OPTIONAL]** Isi `<taskdir>/.explore/` supaya laporan mendarat di laci taskdir dan laporan sebelumnya dapat dipanen subagent. Dispatch yang berjalan sebelum taskdir lahir mengosongkannya; subagent jatuh ke `.frontenddev/explore/` |
| `{batas_cakupan}` | `structure.md` profil untuk direktori rute | **[OPTIONAL]** Mis. `src/routes/**` atau `apps/mobile/src/**`. Dilarang mengarang glob sendiri |

### Aturan untuk Pendispatch

- **Dispatch langsung tanpa skill pembungkus**: seluruh doktrin penelusuran — gerbang masuk, dua fase eksplorasi, formula offset, dan kerangka Bentuk B — duduk di `agents/code-explorer.md`. Dilarang memanggil skill perantara atau menyalin potongan doktrin itu ke dalam prompt.
- **Satu pertanyaan per dispatch**: dua pertanyaan terpisah didispatch bergantian agar ringkasan tetap padat.
- **Dilarang menyalin isi berkas**: jangan salin isi profil, adapter, atau kode ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Read-only mutlak**: dilarang menyuruh subagent merancang alur, menetapkan deep-link, atau memutuskan urutan langkah pengguna.
- **Ambiguitas monorepo diselesaikan di hulu**: tetapkan app target di `{batas_cakupan}` — konvensi rute web dan mobile berbeda, dan subagent dilarang bertanya balik.
- **Periksa `.frontenddev/` terabaikan git**: periksa `.gitignore` memuat baris `.frontenddev/` dan `.explore/` sebelum dispatch pertama. Belum ada — hentikan dispatch dan rutekan ke `frontenddev:profile` mode REFRESH, pemilik tunggal baris itu; dilarang menuliskannya sendiri karena gate ini tidak meng-commit `.gitignore`. Tanpa baris itu laporan scratch bocor ke working tree dan merusak gerbang "tree bersih" milik `code-implementor`.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau placeholder `TBD`/`TODO`.

### Penanganan Balikan

`ux-design` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `ux-design` |
| --- | --- |
| `confidence: high` atau `medium` | Pakai pointer `file:baris` sebagai bukti as-is untuk menulis rute dan Data Demand di `FLOW.md`. Dilarang membaca ulang berkas yang sudah diringkas explorer |
| `confidence: low`, atau objective tidak terjawab | Pertajam `{objective}` agar menyebut rute atau simbol konkret, ulangi maksimum sekali dengan `{slug}` baru; tetap gagal → sapu manual dan catat batasnya di dokumen alur |
| `### Not Found` terisi | Fakta negatif yang sah: rute itu memang belum ada, jadi alurnya pekerjaan baru. Dilarang menulis `FLOW.md` seolah rutenya sudah tersedia |
| `### Rules & constraints` menyebut guard atau redirect | Serap sebagai batas alur wajib; alur yang mengabaikannya akan patah di runtime |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maksimum sekali, lalu sapu manual |

**Subagent mengembalikan:** Ringkasan Bentuk A 400–900 token sesuai blok `Format laporan`, ditutup baris `confidence` pada `### Summary` dan path Bentuk B pada `### Full detail`.
