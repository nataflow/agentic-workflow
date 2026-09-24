# Template Prompt Explorer Unit Kerja — `code-explorer`

Gunakan template ini saat `plan` mendispatch subagent penelusur kode (`code-explorer`) secara langsung.

**Tujuan:** Memetakan kode aktual satu unit kerja sampai tiap berkas yang tersentuh punya bukti `file:line`, simbol anchor, dan kelas test terdampak — tiga token yang dituntut `## File scope` brief dan Check I Fase 4.

**Dispatch setelah:** Fase 2 butir 2 menandai unit itu di `references/slicing-and-scan.md` bagian 2A: package-nya tidak terpetakan di profil, rantai pemanggilnya melewati >1 modul, targetnya tak muncul pada `Grep` pertama, **atau** kuota sapuan habis sebelum Stop Condition terpenuhi.

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Resep navigasi mirrored path: {resep_navigasi}

Slug penelusuran: {slug}

Kedalaman: ringkas

Berkas laporan: {taskdir}/.explore/{slug}.md

Batas pertanyaan: petakan kode yang sudah ada pada unit ini. Dilarang mengusulkan berkas baru,
memecah unit kerja, mengurutkan pengerjaan, maupun merancang perubahan — keempatnya milik
pendispatch. Tiap berkas yang kau sebut wajib bersandar `file:baris` yang kau baca sendiri.

Aturan pelaporan fakta negatif: berkas yang sudah kau sisir dan terbukti tidak menyentuh alur ini
dilaporkan di `### Not Found` beserta direktori yang disisir. Jalur yang belum sempat kau sisir
dicatat di `### Gaps` dengan sebutan "belum disisir". Kedua status itu dilarang ditukar: pendispatch
memakai `### Not Found` sebagai vonis bahwa unit ini pekerjaan pembuatan baru, bukan modifikasi.

Resep navigasi mirrored path di atas adalah pola pencarian jalur async milik repositori ini — consumer antrean, job
terjadwal, broadcast websocket, changelog audit. Jalankan tiap resep itu atas simbol yang kau
petakan; berkas yang tersangkut dilaporkan sebagai barisnya sendiri. Resep yang sudah kau jalankan
tanpa hasil masuk `### Not Found` beserta nama resepnya; resep yang belum sempat kau jalankan masuk
`### Gaps` sebagai "belum disisir". Kau tidak dapat menurunkan resep ini sendiri — berkas adapter
stack di luar jangkauan bacamu, dan jalur async yang tidak punya resep tidak pernah tersapu siapa
pun.

Format laporan: tulis persis tiga seksi berikut, urutan tetap, tanpa seksi tambahan. Rantai
pemanggil penuh, pemetaan layer, dan ekstraksi aturan bisnis sengaja tidak diminta — kedalaman itu
sudah dibayar hulu, dan dispatch ini berangkat sampai empat unit serentak.

```markdown
### Summary
<Jawaban lugas atas objective: bentuk kode unit ini hari ini, dan apakah ia modifikasi atau
pembuatan baru. Tutup dengan baris: `confidence: high | medium | low`>

### File Map
<Satu baris per berkas yang alur unit ini sentuh. Kolom `Simbol anchor` adalah kelas atau method
persis tempat alurnya melintas — pendispatch memakainya apa adanya sebagai kolom `Anchor` brief,
sehingga baris tanpa anchor memaksa satu sapuan ulang. Kolom `Test` diisi berkas test yang menguji
anchor itu, atau frasa `tidak ada test` bila sudah kau sisir dan terbukti tidak ada; ketidakpastian
ditulis `belum disisir`, bukan dikosongkan>

| Berkas | Simbol anchor (`file:baris`) | Test yang menguji anchor | Peran dalam alur |
|---|---|---|---|
| `<path/ke/Berkas>` | `<Kelas.method — path/ke/Berkas:baris>` | `<path/ke/BerkasTest>` \| `tidak ada test` \| `belum disisir` | <satu baris peran konkret> |

### Risks, Gaps & Not Found
- **Risiko & Dampak**: <side-effect atau ketergantungan yang ikut terganggu bila berkas di atas diubah>
- **Gaps**: <jalur yang belum disisir, ditulis "belum disisir" apa adanya; plus batas cakupan yang terpaksa dipakai bila domain tak terdaftar di profil>
- **Not Found**: <simbol/berkas yang dicari tetapi TIDAK ditemukan beserta direktori yang sudah disisir>
```

Tulis laporan ke `Berkas laporan` lebih dulu, lalu kembalikan badan laporan yang sama ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Simbol atau alur konkret unit bertanda di Fase 1 | **[REQUIRED]** Satu pertanyaan tunggal untuk satu unit. Satu prompt yang memuat beberapa unit membuat laporannya tidak dapat dipetakan balik ke brief mana pun |
| `{taskdir}` | Parameter `taskdir` skill | **[REQUIRED]** Path taskdir aktif apa adanya, mis. `backenddev/docs/2609041530-order-cancel`. Tanpa slot ini subagent tidak punya muara tulis dan menghentikan dispatch |
| `{konteks_diketahui}` | Baris profil yang sudah memetakan unit itu sebagian | **[OPTIONAL]** Package, entity, atau endpoint yang sudah terbukti. Isi hanya fakta yang belum tertulis di laci `.explore/`: laporan dispatch sebelumnya dipanen sendiri subagent lewat Tahap 0, jadi jangan disalin ulang ke sini. Tidak tersedia → hapus barisnya utuh, bukan disisakan berlabel kosong |
| `{batas_cakupan}` | Baris `.claude/profile/domain-map.md` yang cocok dengan unit itu | **[OPTIONAL]** Disalin apa adanya, mis. `modules/order/**`. Dilarang mengarang glob sendiri. Domain tidak terdaftar → hapus barisnya utuh; subagent memakai `source_root` dan mencatat batasnya di `### Risks, Gaps & Not Found` |
| `{resep_navigasi}` | Baris `## Navigation recipes` adapter stack `../../profile/stacks/<stack>.md` | **[REQUIRED]** Disalin apa adanya sebagai daftar berpoin, satu resep satu baris. Subagent dilarang membaca berkas adapter, sehingga resep yang tidak disalin ke sini tidak pernah dijalankan dan dimensi 3 (mirrored path) scan Fase 2 disapu tanpa polanya. Adapter tanpa seksi itu → tulis `tidak ada resep terdaftar` apa adanya |
| `{slug}` | Slug taskdir ditambah nomor unit | **[REQUIRED]** Format `<slug>-<NN>`, `NN` dua digit nomor unit. Wajib berbeda antar dispatch dalam satu gelombang — slug kembar membuat dua laporan tertukar, dan karena slot ini juga menamai berkas laporan, laporan unit pertama tertimpa unit kedua |

`Kedalaman` **bukan slot**. Nilainya dipatok `ringkas` di badan template: fan-out ini memberangkatkan sampai 4 unit serentak, dan `menyeluruh` mengalikan rantai pemanggil penuh dengan jumlah unit sekaligus. Kedalaman yang dituntut kontrak sudah dibayar hulu — jalur `PRD` mewarisi `## Impact map` 16 dimensi dari `system-analysis`.

### Aturan untuk Pendispatch

- **Fan-out berkuota**: satu dispatch per unit bertanda, **maksimum 4 serentak** dalam satu giliran paralel; sisanya di gelombang berikutnya. Unit tak bertanda disapu sendiri di bawah kuota Fase 2 dan dilarang didispatch.
- **Satu unit per dispatch**: tiap laporan menggantikan sapuan mandiri unit itu. Dilarang menggabung dua unit ke satu `{objective}` demi menghemat gelombang.
- **Unit yang sudah jelas tidak berangkat**: unit yang package dan anchornya sudah terpetakan di profil dikerjakan langsung, tanpa dispatch.
- **Resep navigasi disalin, bukan dirujuk**: `{resep_navigasi}` adalah pengecualian atas larangan menyalin isi berkas ke dalam prompt — subagent dilarang membaca adapter stack, sehingga resep yang hanya dirujuk path-nya tidak pernah sampai dan jalur async dicari tanpa pola.
- **Dilarang menyalin isi berkas**: jangan salin isi `.claude/profile/` atau berkas kode ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot kurung kurawal `{...}` mentah atau placeholder `TBD`/`TODO`.
- **Profil basi menaikkan tuntutan, bukan menurunkan**: skrip prasyarat mencetak banner `[TERDEGRADASI] profil basi` saat `.claude/profile/` tertinggal di belakang `source_root`. Banner itu aktif → `{batas_cakupan}` dari `domain-map.md` diperlakukan sebagai **dugaan**, bukan batas: laporan yang menutup permukaannya dengan bersandar pada batas itu dinilai setara `confidence: medium`, dan vonis "tidak ada" atas jalur di luar batas itu dilarang. Laporkan banner-nya apa adanya di laporan penutup; dilarang disaring.
- **Blok `Format laporan` ikut berangkat utuh**: kerangka seksi tidak lagi ada di `agents/code-explorer.md`. Prompt yang diberangkatkan tanpa blok itu dihentikan subagent sebagai kegagalan dispatch.
- **Read-only mutlak**: dilarang menyuruh subagent mengubah kode, memilih slicing, atau menetapkan urutan DAG. Satu-satunya berkas yang boleh ditulisnya adalah `Berkas laporan`.

### Penanganan Balikan

`plan` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `plan` |
| --- | --- |
| Laporan terisi, `confidence: high` atau `medium` | Menggantikan sapuan mandiri unit itu. Turunkan `## File scope` dan kolom `Anchor` dari `### File Map`. Dilarang membaca ulang berkas yang sudah diringkas explorer |
| `confidence: low`, atau `{objective}` tidak terjawab | Ulangi maksimum sekali dengan `{slug}` baru agar laporan lama tidak tertimpa; tetap gagal → catat di `## Analysis trace` lalu sapu manual di bawah kuota Fase 2. Dilarang menulis brief di atas laporan `confidence: low` |
| Kolom `Test` berbunyi `tidak ada test`, `belum disisir`, atau kosong | Jangan simpulkan unit itu bebas test. Sapu sendiri direktori test unit itu sebelum mengunci brief — Check I menagih berkas test di `## File scope` tiap `AC-{n}` bertanda `test otomatis`, dan klaim keliru di sini lolos sampai eksekusi |
| Baris `### File Map` tanpa `Simbol anchor` | Anchor adalah kolom wajib brief. Dispatch ulang sekali dengan `{objective}` yang menyebut simbolnya, atau sapu sendiri; dilarang mengarang anchor |
| `### Not Found` terisi | Fakta negatif yang sah: simbolnya memang belum ada, jadi unit itu pekerjaan pembuatan baru. Sesuaikan `## Steps` brief; dilarang mengarang anchor pada berkas yang belum ada |
| `### Gaps` berbunyi "belum disisir" | Bukan fakta negatif. Jalur itu tetap terbuka — sapu sendiri atau catat sebagai batas di `## Analysis trace`. Dilarang divonis tidak tersentuh |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maksimum sekali; tetap gagal → catat di `## Analysis trace` lalu sapu manual |

**Batas serap.** Explorer memetakan berkas yang **ada**; `plan` memutuskan berkas yang **disentuh**. `### File Map` adalah bukti, bukan `## File scope` siap salin — tiap baris tetap harus lolos batas slicing bagian 3 dan plafon `## Out of Scope` `TASK.md`. Vonis `terdampak` pada dimensi 3 atau 4 sapuan residual menghentikan penulisan batch dan memicu lima pemicu eskalasi `references/entry-rules.md` bagian 1A.

**Status berkas laporan.** `{taskdir}/.explore/` adalah zona kerja, bukan artefak rantai: tidak di-stage, tidak di-commit — commit skill ini tetap terbatas pada `brief-*.md` dengan staging path eksplisit — dan tidak dihitung sebagai working tree kotor oleh gerbang git mana pun. Brief mengutip `file:baris` kode, bukan path laporan explorer.

**Laci dipakai bersama.** Selain laporan `code-explorer`, `plan` menaruh dua berkas kerjanya sendiri di laci yang sama: `brief-matrix.md`/`brief-matrix.json` (matriks alokasi Fase 3 langkah 1) dan `brief-review-state.json` (materai ronde self-review Fase 5). Keduanya berstatus laci kerja yang sama persis — tidak di-stage, tidak di-commit, tidak dihitung working tree kotor — dan diletakkan di sini justru karena laci ini sudah dikecualikan tiap gerbang git di rantai. Nama berkasnya berawalan `brief-`, sehingga tidak pernah bertabrakan dengan `{slug}` dispatch explorer mana pun.

**Panen ulang oleh penulis brief.** Laporan di laci ini dibaca dua kali: sekali saat balikannya datang di Fase 2, sekali lagi oleh Fase 3 langkah 3 tepat sebelum `## File scope` dan `## Steps` brief unit itu diisi. Larangan "membaca ulang berkas yang sudah diringkas explorer" pada tabel di atas menyasar **berkas sumber** yang diringkas, bukan laporan ringkasannya — laporan itu justru satu-satunya rumah bukti `file:baris` yang bertahan melewati batas sesi, dan penulis yang kehilangan keduanya akan mengarang anchor.

**Subagent mengembalikan:** Badan laporan tiga seksi sesuai blok `Format laporan` di atas, ditutup baris `confidence: high | medium | low` pada `### Summary`, plus path berkas yang ditulisnya.
