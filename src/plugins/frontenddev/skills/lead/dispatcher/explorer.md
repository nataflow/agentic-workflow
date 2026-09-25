# Template Prompt Explorer Lokasi Kerja — `code-explorer`

Gunakan template ini saat `lead` mendispatch subagent penelusur kode (`code-explorer`) secara langsung.

**Tujuan:** Menemukan letak fitur, simbol, atau alur yang ditanyakan user sampai punya bukti `file:baris`, sebagai dasar penetapan lane dan slug — bukan sebagai keputusan lane itu sendiri.

**Dispatch setelah:** Salah satu Pemicu Dispatch Wajib Phase 1 aktif (objek kerja melintasi lebih dari satu layer, yang dicari relasi bukan lokasi, simbol tak muncul di `Glob` pertama, atau kuota sapuan main loop habis), **atau** lane `EXPLORE_FACT` dipilih di Phase 3.

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug artefak: {slug}

Laci: {laci}

Kedalaman: {kedalaman}

Batas pertanyaan: petakan kode yang sudah ada. Dilarang menetapkan lane, mengarang slug, mengusulkan
berkas baru, atau merancang perubahan — keempatnya milik pendispatch. Tiap berkas yang kau sebut
wajib bersandar `file:baris` yang kau baca sendiri.

Format laporan: kembalikan seksi berikut, urutan tetap, anggaran 400–900 token. Seksi yang tidak
punya temuan dihapus, bukan diisi "tidak ada".

```markdown
### Summary
<2–3 kalimat yang langsung menjawab objective. Tutup dengan baris: `confidence: high | medium | low`>

### Flow
<satu baris rantai aktual di repo, dari rute/layar sampai transport data>

### Layers touched
- <layer>: <NamaSimbol> — <satu baris ringkas; sebut rute, query key, atau ekspor penting>

### Key pointers
- `path/to/File.ext:42` — <catatan 5–10 kata, bukan potongan kode>
(maksimum 8 pointer terpenting, diurutkan berdasarkan relevansi)

### Rules & constraints
- <aturan render, guard rute, batas framework, atau invariant layer beserta bukti `file:baris`>

### Config / infra
- <alias path, base URL api client, query key factory, env var, provider di root layout>

### Risks
- <side-effect atau konsumen lain yang ikut terdampak bila bagian ini diubah>

### Caveats
<unknown, ambiguitas kode, atau penyimpangan konvensi dari `surface-map.md` profil>

### Full detail
<path Bentuk B yang benar-benar ditulis>
```

Tulis Bentuk B lebih dulu ke laci kerja — `{laci}<slug>.md` bila baris Laci terisi,
`.frontenddev/explore/<YYMMDDhhmm>-<slug>.md` bila kosong — lalu kembalikan laporan di atas ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Pertanyaan user atau simbol yang tidak ketemu di sapuan Phase 1 | **[REQUIRED]** Satu pertanyaan fokus tunggal. Dua pertanyaan terpisah didispatch bergantian, bukan digabung |
| `{slug}` | Slug kandidat atau kata kunci prompt | **[REQUIRED]** Kebab-case; ia menamai berkas Bentuk B, jadi slug kembar membuat laporan tertukar |
| `{kedalaman}` | Keputusan pendispatch | **[REQUIRED]** `ringkas` untuk penentuan lane; `menyeluruh` hanya bila jawaban menuntut rantai pemanggil penuh |
| `{konteks_diketahui}` | Hasil `Glob`/`Grep` sapuan Phase 1 | **[OPTIONAL]** Fakta yang sudah terbukti. Tidak tersedia → hapus barisnya utuh, bukan disisakan berlabel kosong. Isi hanya fakta yang **belum** ada di laci: laporan penelusuran sebelumnya dipanen subagent sendiri di Fase 0b, jadi menyalinnya ke sini membayar dua kali untuk isi yang sama |
| `{laci}` | Taskdir aktif bila sudah ada | **[OPTIONAL]** Isi `<taskdir>/.explore/` supaya laporan mendarat di laci taskdir dan laporan sebelumnya dapat dipanen subagent. Dispatch yang berjalan sebelum taskdir lahir mengosongkannya; subagent jatuh ke `.frontenddev/explore/` |
| `{batas_cakupan}` | `structure.md` profil atau parameter `target_app` | **[OPTIONAL]** Mis. `apps/web/src/**`. Ambiguitas monorepo diselesaikan di sini, bukan oleh subagent |

### Aturan untuk Pendispatch

- **Dispatch langsung tanpa skill pembungkus**: seluruh doktrin penelusuran — gerbang masuk, dua fase eksplorasi, formula offset, dan kerangka Bentuk B — duduk di `agents/code-explorer.md`. Dilarang memanggil skill perantara atau menyalin potongan doktrin itu ke dalam prompt.
- **Satu pertanyaan per dispatch**: dua pertanyaan terpisah didispatch bergantian agar ringkasan tetap padat.
- **Dilarang menyalin isi berkas**: jangan salin isi berkas `.claude/profile/frontenddev/`, adapter, atau kode ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Read-only mutlak**: dilarang menyuruh subagent mengubah kode, menetapkan lane, atau mengambil keputusan rute arsitektur.
- **Ambiguitas monorepo diselesaikan di hulu**: bila target app (`apps/web` vs `apps/mobile`) belum pasti, tetapkan lebih dulu di `{batas_cakupan}`. Subagent dilarang bertanya balik.
- **Periksa `.frontenddev/` terabaikan git**: sebelum dispatch pertama di sebuah repo, periksa `.gitignore` memuat baris `.frontenddev/` dan `.explore/`. **WHEN** belum ada: hentikan dispatch dan rutekan ke `frontenddev:profile` mode REFRESH — gate itu pemilik tunggal baris tersebut dan meng-commitnya bersama profil. Dilarang menuliskannya sendiri: `.gitignore` yang berubah tanpa pemilik commit menggantung sepanjang taskdir dan merusak gerbang "tree bersih" milik `code-implementor`.
- **Artefak scratch, bukan keputusan**: `.frontenddev/` adalah workdir gitignored — berbeda dari taskdir `./frontenddev/docs/` yang di-commit per gate. Dilarang men-stage atau meng-commit laporan explore.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot kurung kurawal `{...}` mentah atau placeholder `TBD`/`TODO`. Penanda `<...>` di dalam blok `Format laporan` bukan slot — ia diisi subagent.

### Penanganan Balikan

`lead` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `lead` |
| --- | --- |
| `confidence: high` atau `medium` | Pakai pointer `file:baris` sebagai bukti as-is. Tetapkan slug dari path feature root yang dilaporkan, lalu putuskan lane di Phase 3. Dilarang membaca ulang berkas yang sudah diringkas explorer |
| Lane `EXPLORE_FACT` | Jawab user dari laporan itu dan selesai; dilarang membuat taskdir spekulatif untuk kerja read-only |
| `confidence: low`, atau objective tidak terjawab | Dilarang mengarang temuan. Pertajam `{objective}` agar menyebut simbol konkret, ulangi maksimum sekali dengan `{slug}` baru agar laporan lama tidak tertimpa, lalu turun ke sapuan manual dan nyatakan penyimpangannya |
| `### Not Found` terisi | Fakta negatif yang sah: simbolnya memang belum ada, jadi pekerjaan ini pembuatan baru. Tetapkan slug baru berbasis konvensi kebab-case, bukan dari folder yang tidak ada |
| `### Caveats` menyebut profil absen | Alihkan rute ke lane `PROFILE` (`frontenddev:profile`) sebelum melanjutkan penentuan lane |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maksimum sekali; tetap gagal → lanjutkan dengan sapuan manual dan catat penyimpangannya |

**Subagent mengembalikan:** Ringkasan Bentuk A 400–900 token sesuai blok `Format laporan`, ditutup baris `confidence` pada `### Summary` dan path Bentuk B pada `### Full detail`.
