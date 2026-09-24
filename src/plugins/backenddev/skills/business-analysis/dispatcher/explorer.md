# Template Prompt Explorer Domain — `code-explorer`

Gunakan template ini saat `business-analysis` mendispatch subagent penelusur kode (`code-explorer`) secara langsung, tanpa skill pembungkus.

**Tujuan:** Memotret perilaku as-is satu domain sebagai observasi kode berbukti `file:baris` untuk bahan mentah elisitasi Fase 2 — bukan sebagai aturan target, dan bukan sebagai desain teknis.

**Dispatch setelah:** Fase 1 butir 2 menemui salah satu kondisi: alur menyentuh >1 modul, target luput pada `Grep` pertama, atau kuota sapuan main loop (3 panggilan `Glob`+`Grep`) habis.

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug penelusuran: {slug}

Kedalaman: ringkas

Berkas laporan: {taskdir}/.explore/{slug}.md

Batas pertanyaan: laporkan perilaku sistem yang terbukti berjalan hari ini. Dilarang menyimpulkan
apakah perilaku itu benar, dilarang mengusulkan perilaku target, dan dilarang merancang endpoint,
DTO, maupun skema tabel. Tiap kalimat perilaku wajib bersandar pada bukti `file:baris`; perilaku
yang tidak terbukti dibuang, bukan diperhalus jadi dugaan.

Format laporan: tulis persis empat seksi berikut, urutan tetap, tanpa seksi tambahan. Rantai
pemanggil, pemetaan layer, nama queue/topic, pola cache key, dan skema migrasi sengaja **tidak**
diminta: dokumen yang berdiri di atas laporan ini tunduk pada larangan desain teknis, sehingga
detail itu hanya menambah bahan yang dilarang mendarat.

```markdown
### Summary
<Perilaku domain yang terbukti berjalan hari ini, menjawab objective dalam bahasa yang dialami
aktor. Tutup dengan baris: `confidence: high | medium | low`>

### Rules & Invariants
<Satu baris per aturan, ditulis sebagai kondisi dan konsekuensi yang dieksekusi kode — mis. "order
berstatus X ditolak saat Y" — bukan sebagai ringkasan struktur kelas>
- <kondisi> → <konsekuensi yang dieksekusi kode> — `<path/ke/Berkas:baris>`

### Risks, Gaps & Not Found
- **Gaps**: <cabang perilaku yang belum dapat dipastikan dari pembacaan lokal, atau jalur yang belum disisir — sebut "belum disisir" apa adanya>
- **Not Found**: <aturan/simbol yang dicari tetapi TIDAK ditemukan beserta direktori yang sudah disisir>

### Caveats
<Batas cakupan yang terpaksa dipakai, inkonsistensi perilaku antar-jalur, atau anomali yang perlu
ditanyakan ke user di Fase 2>
```

Tulis laporan ke `Berkas laporan` lebih dulu, lalu kembalikan badan laporan yang sama ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Pertanyaan tunggal yang disusun `business-analysis` Fase 1 | **[REQUIRED]** Satu pertanyaan perilaku domain, bukan daftar. Pertanyaan kosong atau umum ("cek kode", "analisa modul", `TBD`) dihentikan subagent — batalkan dispatch lebih dulu |
| `{taskdir}` | Parameter `taskdir` skill | **[REQUIRED]** Path taskdir aktif apa adanya, mis. `backenddev/docs/2609041530-order-cancel`. Tanpa slot ini subagent tidak punya muara tulis dan menghentikan dispatch |
| `{konteks_diketahui}` | Fakta yang sudah dipegang dari Fase 0 butir 2 dan Fase 1 butir 2 | **[OPTIONAL]** Modul, entity, atau endpoint yang sudah terbukti; subagent tidak menelusurinya ulang. Isi hanya fakta yang belum tertulis di laci `.explore/`: laporan dispatch sebelumnya dipanen sendiri subagent lewat Tahap 0, jadi jangan disalin ulang ke sini. Tidak tersedia → hapus barisnya utuh, bukan disisakan berlabel kosong |
| `{batas_cakupan}` | Baris `.claude/profile/domain-map.md` yang cocok dengan `{objective}` | **[OPTIONAL]** Disalin apa adanya, mis. `modules/order/**`. Dilarang mengarang glob sendiri. Domain tidak terdaftar di sana → hapus barisnya utuh; subagent memakai `source_root` dan mencatat batasnya di `### Caveats` |
| `{slug}` | Slug fitur taskdir ditambah pembeda pertanyaan | **[REQUIRED]** kebab-case, unik per dispatch dalam satu taskdir agar laporan tidak tertukar. Slot ini juga menamai berkas laporan, sehingga slug kembar menimpa laporan dispatch sebelumnya |

`Kedalaman` **bukan slot**. Nilainya dipatok `ringkas` di badan template; `menyeluruh` adalah wewenang `system-analysis`, dan memakainya di sini menyeret BRD ke rantai pemanggil teknis yang bukan miliknya.

### Aturan untuk Pendispatch

- **Kuota dispatch**: maksimum 1 dispatch per taskdir; naik ke 2 hanya bila Fase 1 sudah membuktikan alurnya menyentuh >1 modul. Kuota habis sementara pertanyaan masih terbuka → tulis kekurangannya sebagai `## Open questions` BRD atau angkat ke elisitasi Fase 2; dilarang dispatch ke-3.
- **Satu pertanyaan per dispatch**: satu dispatch memuat tepat satu `{objective}`. Dua pertanyaan berangkat sebagai dua dispatch ber-`{slug}` berbeda, bukan satu prompt bercabang.
- **Framing domain, bukan teknis**: `{objective}` menanyakan perilaku yang dialami aktor ("kondisi apa yang membuat order ditolak sistem hari ini"), bukan rantai pemanggil ("bagaimana alur order create sampai kirim event queue"). Framing kedua milik `system-analysis`.
- **Dilarang menyalin isi berkas**: jangan salin isi `.claude/profile/` atau berkas kode ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot kurung kurawal `{...}` mentah atau placeholder `TBD`/`TODO`.
- **Profil basi menaikkan tuntutan, bukan menurunkan**: skrip prasyarat mencetak banner `[TERDEGRADASI] profil basi` saat `.claude/profile/` tertinggal di belakang `source_root`. Banner itu aktif → `{batas_cakupan}` dari `domain-map.md` diperlakukan sebagai **dugaan**, bukan batas: laporan yang menutup permukaannya dengan bersandar pada batas itu dinilai setara `confidence: medium`, dan vonis "tidak ada" atas jalur di luar batas itu dilarang. Laporkan banner-nya apa adanya di laporan penutup; dilarang disaring.
- **Blok `Format laporan` ikut berangkat utuh**: kerangka seksi tidak lagi ada di `agents/code-explorer.md`. Prompt yang diberangkatkan tanpa blok itu dihentikan subagent sebagai kegagalan dispatch.
- **Read-only mutlak**: dilarang menyuruh subagent mengubah kode, memilih rute arsitektur, atau merumuskan aturan target. Satu-satunya berkas yang boleh ditulisnya adalah `Berkas laporan`.

### Penanganan Balikan

`business-analysis` memetakan balikan sendiri; tidak ada Universal Dispatch Envelope pada jalur ini.

| Balikan subagent | Penanganan `business-analysis` |
| --- | --- |
| Laporan terisi, `confidence: high` atau `medium` | Serap ke Fase 1 butir 4. Tiap fakta dilabeli `Observasi kode: <file:baris>` sebelum menyentuh BRD |
| `confidence: low`, atau `{objective}` tidak terjawab | **Dilarang diserap sebagai observasi.** Angkat pertanyaannya ke elisitasi Fase 2, atau catat sebagai `## Open questions` BRD |
| `### Not Found` terisi | Fakta negatif yang sah jadi bahan pertanyaan Fase 2 ("apakah aturan ini memang belum pernah ada?"). Dilarang ditafsirkan sebagai aturan yang hilang dan dilarang ditambal asumsi |
| `### Gaps` berbunyi "belum disisir" | Bukan fakta negatif. Jalur itu tetap terbuka: angkat ke Fase 2 atau `## Open questions`, dilarang dinyatakan tidak ada |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maksimum sekali; tetap gagal → lanjutkan Fase 2 tanpa observasi dan catat kendalanya di laporan penutup |

**Batas serap.** Laporan ini adalah **observasi**, bukan aturan bisnis. IRON LAW `SKILL.md` berlaku penuh: tiap fakta masuk BRD hanya berlabel `Observasi kode: <file:baris>`, dan dilarang naik jadi `BR-{n}` tanpa konfirmasi user di Fase 2 atau Fase 3.

**Status berkas laporan.** `{taskdir}/.explore/` adalah zona kerja, bukan artefak rantai: tidak di-stage, tidak di-commit, dan tidak dihitung sebagai working tree kotor oleh gerbang git mana pun. `BRD.md` mengutip `file:baris` kode, bukan path laporan explorer.

**Subagent mengembalikan:** Badan laporan empat seksi sesuai blok `Format laporan` di atas, ditutup baris `confidence: high | medium | low` pada `### Summary`, plus path berkas yang ditulisnya.
