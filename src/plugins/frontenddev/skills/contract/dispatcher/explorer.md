# Template Prompt Explorer Kontrak & Layer — `code-explorer`

Gunakan template ini saat `contract` mendispatch subagent penelusur kode (`code-explorer`) secara langsung.

**Tujuan:** Membuktikan bentuk DTO, batas layer, dan pemilik query key yang sudah ada di repo sebelum kontrak baru dirancang — supaya `CONTRACT.md` berdiri di atas kode aktual, bukan di atas ingatan.

**Dispatch setelah:** Phase 1 (Codebase Exploration & Dependency Tracing) menemukan bahwa penelusuran melintasi lebih dari satu layer, yang dicari relasi (konsumen DTO, pemanggil service, pemilik cache key), simbol acuan tak muncul di sapuan pertama, **atau** kuota sapuan habis.

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug artefak: {slug}

Laci: {laci}

Kedalaman: {kedalaman}

Batas pertanyaan: petakan kontrak dan batas layer yang sudah ada. Dilarang merancang DTO baru,
mengusulkan bentuk endpoint, memutuskan layer shape, atau menulis potongan kode — keempatnya milik
pendispatch. Tiap simbol yang kau sebut wajib bersandar `file:baris` yang kau baca sendiri, dan tipe
DTO diverifikasi dari deklarasi riilnya, bukan disimpulkan dari pemakaian di presentasi.

Format laporan: kembalikan seksi berikut, urutan tetap, anggaran 400–900 token. Seksi yang tidak
punya temuan dihapus, bukan diisi "tidak ada".

```markdown
### Summary
<2–3 kalimat yang langsung menjawab objective. Tutup dengan baris: `confidence: high | medium | low`>

### Flow
<satu baris rantai aktual di repo, dari rute/layar sampai transport data dan DTO sumbernya>

### Layers touched
- <layer>: <NamaSimbol> — <satu baris ringkas; sebut ekspor, tipe balikan, atau query key>

### Key pointers
- `path/to/File.ext:42` — <catatan 5–10 kata, bukan potongan kode>
(maksimum 8 pointer terpenting; dahulukan deklarasi DTO, service transport, dan factory query key)

### Rules & constraints
- <batas layer yang berlaku, guard rute, batas framework, atau invariant beserta bukti `file:baris`>

### Config / infra
- <alias path, base URL api client, query key factory, env var, provider di root layout>

### Risks
- <konsumen DTO atau pemakai simbol yang ikut terdampak bila kontraknya berubah>

### Caveats
<unknown, ambiguitas kode, atau penyimpangan konvensi dari `surface-map.md` profil>

### Not Found
<DTO, endpoint, atau simbol yang dicari tetapi TIDAK ditemukan, beserta direktori yang sudah disisir>

### Full detail
<path Bentuk B yang benar-benar ditulis>
```

Tulis Bentuk B lebih dulu ke laci kerja — `{laci}<slug>.md` bila baris Laci terisi,
`.frontenddev/explore/<YYMMDDhhmm>-<slug>.md` bila kosong — lalu kembalikan laporan di atas ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Simbol, DTO, atau alur data yang belum pasti bentuknya | **[REQUIRED]** Satu pertanyaan fokus tunggal, mis. "bagaimana bentuk DTO response daftar order dan siapa konsumennya" |
| `{slug}` | Slug taskdir ditambah penanda topik | **[REQUIRED]** Kebab-case; ia menamai berkas Bentuk B, jadi slug kembar membuat laporan tertukar |
| `{kedalaman}` | Keputusan pendispatch | **[REQUIRED]** `menyeluruh` bila kontrak menyentuh rantai pemanggil dan konsumen lintas layer; `ringkas` bila hanya butuh satu deklarasi |
| `{konteks_diketahui}` | Fakta dari `FLOW.md`/`UI.md` atau profil | **[OPTIONAL]** Isi hanya fakta yang sudah terbukti. Tidak tersedia → hapus barisnya utuh. Isi hanya fakta yang **belum** ada di laci: laporan penelusuran sebelumnya dipanen subagent sendiri di Fase 0b, jadi menyalinnya ke sini membayar dua kali untuk isi yang sama |
| `{laci}` | Taskdir aktif bila sudah ada | **[OPTIONAL]** Isi `<taskdir>/.explore/` supaya laporan mendarat di laci taskdir dan laporan sebelumnya dapat dipanen subagent. Dispatch yang berjalan sebelum taskdir lahir mengosongkannya; subagent jatuh ke `.frontenddev/explore/` |
| `{batas_cakupan}` | `structure.md` profil untuk feature root terkait | **[OPTIONAL]** Mis. `src/features/orders/**`. Dilarang mengarang glob sendiri |

### Aturan untuk Pendispatch

- **Dispatch langsung tanpa skill pembungkus**: seluruh doktrin penelusuran — gerbang masuk, dua fase eksplorasi, formula offset, dan kerangka Bentuk B — duduk di `agents/code-explorer.md`. Dilarang memanggil skill perantara atau menyalin potongan doktrin itu ke dalam prompt.
- **Satu pertanyaan per dispatch**: dua pertanyaan terpisah didispatch bergantian agar ringkasan tetap padat.
- **Dilarang menyalin isi berkas**: jangan salin isi profil, adapter, `FLOW.md`, `UI.md`, atau kode ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Read-only mutlak**: dilarang menyuruh subagent merancang DTO, memilih layer shape, atau mengusulkan endpoint baru.
- **Ambiguitas monorepo diselesaikan di hulu**: tetapkan app target di `{batas_cakupan}`; subagent dilarang bertanya balik.
- **Periksa `.frontenddev/` terabaikan git**: periksa `.gitignore` memuat baris `.frontenddev/` dan `.explore/` sebelum dispatch pertama. Belum ada — hentikan dispatch dan rutekan ke `frontenddev:profile` mode REFRESH, pemilik tunggal baris itu; dilarang menuliskannya sendiri karena gate ini tidak meng-commit `.gitignore`. Tanpa baris itu laporan scratch bocor ke working tree dan merusak gerbang "tree bersih" milik `code-implementor`.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau placeholder `TBD`/`TODO`.

### Penanganan Balikan

`contract` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `contract` |
| --- | --- |
| `confidence: high` atau `medium` | Pakai pointer `file:baris` sebagai bukti as-is untuk mengisi bentuk DTO dan batas layer. Dilarang membaca ulang berkas yang sudah diringkas explorer |
| `confidence: low`, atau objective tidak terjawab | Pertajam `{objective}` agar menyebut simbol konkret, ulangi maksimum sekali dengan `{slug}` baru; tetap gagal → sapu manual dan catat batasnya di dokumen kontrak. Dilarang mengunci DTO di atas laporan `confidence: low` |
| `### Not Found` terisi | Fakta negatif yang sah: DTO atau endpoint itu memang belum ada, jadi kontraknya pekerjaan baru. Dilarang mengarang bentuk lama yang tidak pernah ada |
| `### Risks` menyebut konsumen di luar fitur | Perluasan blast radius. Catat di kontrak sebagai dampak lintas fitur sebelum bentuk DTO dikunci |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maksimum sekali, lalu sapu manual |

**Subagent mengembalikan:** Ringkasan Bentuk A 400–900 token sesuai blok `Format laporan`, ditutup baris `confidence` pada `### Summary` dan path Bentuk B pada `### Full detail`.
