# Template Prompt Explorer Rekonsiliasi Brief — `code-explorer`

Gunakan template ini saat `plan` mendispatch subagent penelusur kode (`code-explorer`) secara langsung.

**Tujuan:** Membuktikan path dan simbol riil satu unit kerja sampai `files_touched` brief dapat ditulis dari bukti `file:baris`, bukan dari asumsi — termasuk vonis apakah unit itu modifikasi atau pembuatan baru.

**Dispatch setelah:** Phase 1 (3 Checks) menandai unit yang rekonsiliasinya melintasi lebih dari satu layer, yang dicari relasi (pemanggil Controller, konsumen DTO, pemilik query key), simbol acuan tak muncul di sapuan pertama, **atau** kuota sapuan habis.

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug artefak: {slug}

Laci: {laci}

Kedalaman: ringkas

Batas pertanyaan: petakan kode yang sudah ada pada unit ini. Dilarang mengusulkan berkas baru,
memecah unit kerja, mengurutkan pengerjaan, maupun merancang perubahan — keempatnya milik
pendispatch. Tiap berkas yang kau sebut wajib bersandar `file:baris` yang kau baca sendiri.

Aturan pelaporan fakta negatif: berkas yang sudah kau sisir dan terbukti tidak menyentuh alur ini
dilaporkan di `### Not Found` beserta direktori yang disisir. Jalur yang belum sempat kau sisir
dicatat di `### Caveats` dengan sebutan "belum disisir". Kedua status itu dilarang ditukar:
pendispatch memakai `### Not Found` sebagai vonis bahwa unit ini pekerjaan pembuatan baru.

Format laporan: kembalikan seksi berikut, urutan tetap, anggaran 400–900 token. Seksi yang tidak
punya temuan dihapus, bukan diisi "tidak ada".

```markdown
### Summary
<2–3 kalimat: bentuk kode unit ini hari ini, dan apakah ia modifikasi atau pembuatan baru. Tutup
dengan baris: `confidence: high | medium | low`>

### Flow
<satu baris rantai aktual di repo, dari rute/layar sampai transport data>

### Layers touched
- <layer>: <NamaSimbol> — <satu baris ringkas; sebut rute, query key, atau ekspor penting>

### Key pointers
- `path/to/File.ext:42` — <catatan 5–10 kata, bukan potongan kode>
(maksimum 8 pointer terpenting; sertakan berkas test yang menguji simbol itu bila ada)

### Rules & constraints
- <aturan render, guard rute, batas framework, atau invariant layer beserta bukti `file:baris`>

### Config / infra
- <alias path, base URL api client, query key factory, env var, provider di root layout>

### Risks
- <side-effect atau konsumen lain yang ikut terdampak bila berkas di atas diubah>

### Caveats
<unknown, ambiguitas kode, jalur yang "belum disisir", atau penyimpangan dari `surface-map.md` profil>

### Not Found
<simbol atau berkas yang dicari tetapi TIDAK ditemukan, beserta direktori yang sudah disisir>

### Full detail
<path Bentuk B yang benar-benar ditulis>
```

Tulis Bentuk B lebih dulu ke laci kerja — `{laci}<slug>.md` bila baris Laci terisi,
`.frontenddev/explore/<YYMMDDhhmm>-<slug>.md` bila kosong — lalu kembalikan laporan di atas ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Simbol atau alur konkret unit bertanda di Phase 1 | **[REQUIRED]** Satu pertanyaan tunggal untuk satu unit. Satu prompt yang memuat beberapa unit membuat laporannya tidak dapat dipetakan balik ke brief mana pun |
| `{slug}` | Slug taskdir ditambah nomor unit | **[REQUIRED]** Format `<slug>-<NN>`. Wajib berbeda antar dispatch — slug kembar membuat laporan unit pertama tertimpa unit kedua |
| `{konteks_diketahui}` | Baris `CONTRACT.md` atau profil yang sudah memetakan unit itu sebagian | **[OPTIONAL]** Isi hanya fakta yang sudah terbukti. Tidak tersedia → hapus barisnya utuh. Isi hanya fakta yang **belum** ada di laci: laporan penelusuran sebelumnya dipanen subagent sendiri di Fase 0b, jadi menyalinnya ke sini membayar dua kali untuk isi yang sama |
| `{laci}` | Taskdir aktif bila sudah ada | **[OPTIONAL]** Isi `<taskdir>/.explore/` supaya laporan mendarat di laci taskdir dan laporan sebelumnya dapat dipanen subagent. Dispatch yang berjalan sebelum taskdir lahir mengosongkannya; subagent jatuh ke `.frontenddev/explore/` |
| `{batas_cakupan}` | `structure.md` profil untuk feature root unit itu | **[OPTIONAL]** Disalin apa adanya, mis. `src/features/orders/**`. Dilarang mengarang glob sendiri |

`Kedalaman` **bukan slot**: nilainya dipatok `ringkas` di badan template. Rekonsiliasi menuntut bukti path dan simbol, bukan rantai pemanggil penuh — kedalaman itu sudah dibayar di Gate Contract.

### Aturan untuk Pendispatch

- **Dispatch langsung tanpa skill pembungkus**: seluruh doktrin penelusuran — gerbang masuk, dua fase eksplorasi, formula offset, dan kerangka Bentuk B — duduk di `agents/code-explorer.md`. Dilarang memanggil skill perantara atau menyalin potongan doktrin itu ke dalam prompt.
- **Satu unit per dispatch**: tiap laporan menggantikan sapuan mandiri unit itu. Dilarang menggabung dua unit ke satu `{objective}`.
- **Unit yang sudah jelas tidak berangkat**: unit yang path dan simbolnya sudah terbukti di Gate Contract dikerjakan langsung, tanpa dispatch.
- **Dilarang menyalin isi berkas**: sebutkan path `CONTRACT.md` atau profil; subagent membacanya sendiri secara terisolasi.
- **Read-only mutlak**: dilarang menyuruh subagent memilih slicing, menetapkan urutan DAG, atau menulis langkah implementasi.
- **Periksa `.frontenddev/` terabaikan git**: periksa baris berjangkar `/.frontenddev/` dan `frontenddev/docs/**/.explore/` berlaku — exit code `git check-ignore -q .frontenddev` dan `git check-ignore -q frontenddev/docs/x/.explore/y` keduanya 0, bukan `grep` atas `.gitignore` sebelum dispatch pertama. Belum ada — hentikan dispatch dan rutekan ke `frontend:profile` mode REFRESH, pemilik tunggal baris itu; dilarang menuliskannya sendiri karena gate ini tidak meng-commit `.gitignore`. Tanpa baris itu laporan scratch bocor ke working tree dan merusak gerbang "tree bersih" milik `code-implementor`.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau placeholder `TBD`/`TODO`.

### Penanganan Balikan

`plan` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `plan` |
| --- | --- |
| `confidence: high` atau `medium` | Menggantikan sapuan mandiri unit itu. Turunkan `files_touched` dan section 3 brief dari `### Key pointers` apa adanya. Dilarang membaca ulang berkas yang sudah diringkas explorer |
| `confidence: low`, atau objective tidak terjawab | Ulangi maksimum sekali dengan `{slug}` baru agar laporan lama tidak tertimpa; tetap gagal → sapu manual di bawah kuota Phase 1 dan catat penyimpangannya. Dilarang menulis brief di atas laporan `confidence: low` |
| `### Not Found` terisi | Fakta negatif yang sah: simbolnya memang belum ada, jadi unit ini pekerjaan pembuatan baru. Sesuaikan langkah implementasi brief; dilarang mengarang anchor pada berkas yang belum ada |
| `### Caveats` berbunyi "belum disisir" | Bukan fakta negatif. Jalur itu tetap terbuka — sapu sendiri atau catat sebagai batas; dilarang divonis tidak tersentuh |
| Tidak ada berkas test yang disebut untuk simbol unit | Jangan simpulkan unit itu bebas test. Sapu sendiri direktori test unit itu sebelum mengunci brief — klaim keliru di sini lolos sampai eksekusi |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maksimum sekali, lalu sapu manual |

**Batas serap.** Explorer memetakan berkas yang **ada**; `plan` memutuskan berkas yang **disentuh**. `### Key pointers` adalah bukti, bukan `files_touched` siap salin — tiap baris tetap harus lolos batas slicing dan plafon `Out of Scope` taskdir.

**Subagent mengembalikan:** Ringkasan Bentuk A 400–900 token sesuai blok `Format laporan`, ditutup baris `confidence` pada `### Summary` dan path Bentuk B pada `### Full detail`.
