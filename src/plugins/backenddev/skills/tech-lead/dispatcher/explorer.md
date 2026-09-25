# Template Prompt Explorer Gerbang — `code-explorer`

Gunakan template ini saat `tech-lead` mendispatch subagent penelusur kode (`code-explorer`) secara langsung.

**Tujuan:** Membuktikan objek kerja benar-benar ada di kode dan memetakan layer yang disentuhnya, sebagai bukti Keputusan 1 (rute) dan Keputusan 2 (risk level) — bukan sebagai rancangan solusi.

**Dispatch setelah:** Fase 1 butir 2 menemui salah satu dari empat pemicu mekanis di `references/gate-scope.md` bagian 4E. Satu pemicu cukup, dan sapuan main loop dilarang dicoba lebih dulu.

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug penelusuran: {slug}

Kedalaman: ringkas

Berkas laporan: backenddev/docs/.explore/{slug}.md

Batas pertanyaan: laporkan keberadaan dan letak kode yang ditanyakan beserta layer yang dilewatinya.
Dilarang memilih rute pengerjaan, menaksir risk level, mengusulkan perubahan, maupun menilai kualitas
kode yang kau temukan. Tiap pointer wajib bersandar pada `file:baris` yang kau baca sendiri; simbol
yang tidak ditemukan dilaporkan sebagai tidak ditemukan, bukan ditebak dari kemiripan nama.

Pada `### Layers & Surfaces Touched`, sebut tiap layer yang alurnya lewati secara eksplisit beserta
satu pointer per layer — pendispatch memakai jumlah layer itu sebagai predikat pemilihan lane,
sehingga layer yang tidak disebut menurunkan lane tanpa pernah ditimbang.

Format laporan: tulis persis empat seksi berikut, urutan tetap, tanpa seksi tambahan. Rantai
pemanggil penuh dan ekstraksi aturan bisnis sengaja tidak diminta — keduanya milik lane hilir dan
membebani context gerbang tanpa mengubah rute.

```markdown
### Summary
<Jawaban lugas yang langsung menjawab objective: ada atau tidak kode itu, dan di mana. Tutup dengan
baris: `confidence: high | medium | low`>

### Layers & Surfaces Touched
- <Peran/Layer>: `<NamaTipe/Berkas:baris>` — <satu baris ringkas peran dan route mapping/penanda penting>
- <Permukaan Runtime>: `<HTTP | Database | Broker | Cache | Scheduler>` — <detail interface/koneksi yang disentuh>

### Key Pointers & Evidence
| Klaim Faktual | Bukti Lokasi (`file:line`) | Catatan Verifikasi Kode |
|---|---|---|
| <Fakta/perilaku kode yang terbukti> | `<path/ke/Berkas:baris>` | <Konteks logika, batas transaksi, atau return type> |

### Risks, Gaps & Not Found
- **Risiko & Dampak**: <side-effect atau dampak ketergantungan jika bagian kode ini diubah>
- **Gaps**: <cabang yang belum dapat dipastikan, atau jalur yang belum disisir — sebut "belum disisir" apa adanya>
- **Not Found**: <simbol/komponen yang dicari tetapi TIDAK ditemukan beserta direktori yang sudah disisir>
```

Tulis laporan ke `Berkas laporan` lebih dulu, lalu kembalikan badan laporan yang sama ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Pemicu Fase 1 butir 2 yang aktif, dipersempit jadi satu pertanyaan | **[REQUIRED]** Satu pertanyaan tunggal bersimbol konkret, bukan daftar. Pertanyaan umum (`cek kode`, `analisa modul`, `TBD`) dihentikan subagent — pertajam lebih dulu, jangan berangkatkan |
| `{konteks_diketahui}` | Fakta terbukti dari Fase 0 (`.claude/profile/backenddev/`) dan prompt user | **[OPTIONAL]** Modul, entity, atau endpoint yang sudah pasti; subagent tidak menelusurinya ulang. Isi hanya fakta yang belum tertulis di laci `.explore/`: laporan dispatch sebelumnya dipanen sendiri subagent lewat Tahap 0, jadi jangan disalin ulang ke sini. Tidak tersedia → hapus barisnya utuh, bukan disisakan berlabel kosong |
| `{batas_cakupan}` | Baris `.claude/profile/backenddev/domain-map.md` yang cocok dengan `{objective}` | **[OPTIONAL]** Disalin apa adanya, mis. `modules/order/**`. Dilarang mengarang glob sendiri. Domain tidak terdaftar → hapus barisnya utuh; subagent memakai `source_root` dan mencatat batasnya di `### Risks, Gaps & Not Found` |
| `{slug}` | Slug objek kerja yang sedang dirutekan | **[REQUIRED]** kebab-case, unik per dispatch dalam satu giliran gerbang. Slot ini juga menamai berkas laporan, sehingga slug kembar menimpa laporan dispatch sebelumnya |

`Kedalaman` **bukan slot**. Nilainya dipatok `ringkas` di badan template: yang dituntut gerbang adalah satu bukti `file:line` **per permukaan**, dan `menyeluruh` menyeret rantai pemanggil penuh ke context gerbang — persis beban yang dicegah kuota sapuan Fase 1. Cakupan gerbang bertambah lewat jumlah dispatch, bukan lewat kedalaman tiap dispatch. Penelusuran mendalam tetap wewenang `system-analysis` dan `plan`.

`Berkas laporan` **bukan slot bebas**. Gerbang berjalan **sebelum** taskdir diprovisi (Fase 3), dan lane `EXPLORE_FACT` tidak pernah memilikinya, sehingga laporan gerbang mendarat di laci gerbang `backenddev/docs/.explore/` — bukan di `{taskdir}/.explore/` seperti skill hilir. Hanya `{slug}` yang dihidrasi di dalamnya.

### Aturan untuk Pendispatch

- **Satu titik sah, berkuota per permukaan**: dispatch hanya pada Fase 1 butir 2, **satu dispatch per permukaan yang disebut `request`**, plafon **3 per giliran gerbang**. Permukaan keempat dan seterusnya turun ke sapuan manual berkuota, lalu yang tetap tak tertutup dicatat sebagai belum terbukti di slot `Bukti` — bukan didiamkan. Dispatch ulang atas permukaan yang **sudah** tertutup tidak sah kecuali sebagai retry `## Failure path` butir 4.

  Plafon lama satu dispatch per giliran gerbang dikalibrasi untuk stop condition lama, yang berhenti pada bukti pertama apa pun. Stop condition sekarang menagih status per permukaan, dan satu dispatch tidak dapat memenuhinya pada permintaan yang menyentuh dua permukaan — sisanya pasti jatuh ke sapuan manual berkuota 3 `Glob`+`Grep`, dan permukaan yang luput di situ masuk `evidence` sebagai ketiadaan, bukan sebagai gap.
- **Satu pertanyaan per dispatch**: satu dispatch memuat tepat satu `{objective}`. Dua pertanyaan berangkat sebagai dua dispatch ber-`{slug}` berbeda, bukan satu prompt bercabang.
- **Framing rute, bukan desain**: `{objective}` menanyakan letak dan lintasan (`di mana batas transaksi pembatalan order`), bukan solusi (`bagaimana sebaiknya pembatalan order diperbaiki`). Perancangan milik lane hilir.
- **Dilarang menyalin isi berkas**: jangan salin isi `.claude/profile/backenddev/` atau berkas kode ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot kurung kurawal `{...}` mentah atau placeholder `TBD`/`TODO`.
- **Profil basi menaikkan tuntutan, bukan menurunkan**: skrip prasyarat mencetak banner `[TERDEGRADASI] profil basi` saat `.claude/profile/backenddev/` tertinggal di belakang `source_root`. Banner itu aktif → `{batas_cakupan}` dari `domain-map.md` diperlakukan sebagai **dugaan**, bukan batas: laporan yang menutup permukaannya dengan bersandar pada batas itu dinilai setara `confidence: medium`, dan vonis "tidak ada" atas jalur di luar batas itu dilarang. Laporkan banner-nya apa adanya di laporan penutup; dilarang disaring.
- **Blok `Format laporan` ikut berangkat utuh**: kerangka seksi tidak lagi ada di `agents/code-explorer.md`. Prompt yang diberangkatkan tanpa blok itu dihentikan subagent sebagai kegagalan dispatch.
- **Jalur tunggal**: isi prompt tiap dispatch subagent oleh gerbang bersumber hanya dari template ini. Peluncurannya memakai tool subagent bawaan harness — template adalah sumber teks, bukan mekanisme peluncuran. Yang terlarang: prompt yang disusun sendiri, prompt bersisa slot `{...}` mentah, dan prompt tanpa blok `Format laporan`-nya, termasuk dengan dalih tugas ringan.

### Penanganan Balikan

`tech-lead` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `tech-lead` |
| --- | --- |
| Laporan terisi, `confidence: high` atau `medium` | Pakai pointer `file:line` sebagai bukti Keputusan 1 dan Keputusan 2. Dilarang membaca ulang berkas yang sudah diringkas explorer, termasuk membuka ulang berkas laporan yang isinya sudah ada di context |
| `confidence: low`, atau `{objective}` tidak terjawab | Pertajam `{objective}` agar menyebut simbol konkret dan dispatch ulang tepat sekali dengan `{slug}` baru agar laporan lama tidak tertimpa. Tetap gagal → turun ke sapuan manual berkuota Fase 1 dan catat penyimpangannya di slot `Bukti`. Dilarang mengarang temuan |
| `### Not Found` terisi | Fakta negatif yang sah: simbol yang user sebut tidak ada di batas cakupan. Angkat sebagai pertanyaan klarifikasi ke user sebelum menetapkan rute; dilarang ditafsirkan sebagai izin membuat kode baru diam-diam |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent — subagent belum tentu pernah berangkat. Ikuti `## Failure path` butir 4 |

**Angka permukaan milik gerbang, bukan milik laporan.** Slot `Bukti` menuntut `Permukaan <n tertutup>/<n diminta>`, dan kedua angka itu diturunkan dari enumerasi Fase 1 butir 4 gerbang sendiri disandingkan dengan `### Key Pointers & Evidence`, `### Not Found`, dan `### Gaps` badan laporan. Frontmatter berkas laporan memuat angka serupa, tetapi ia tidak ikut kembali ke context — ia bahan panen Tahap 0 dispatch berikutnya — dan membuka berkasnya untuk memungutnya melanggar larangan membaca ulang di tabel atas.

**Batas serap.** Laporan ini bukti rute, bukan rancangan. Slot `File Scope` di laporan rute diisi **batas modul** hasil `### Layers & Surfaces Touched`, bukan daftar berkas yang akan disentuh — penetapan berkas adalah wewenang `plan`.

**Status berkas laporan.** `backenddev/docs/.explore/` adalah zona kerja gerbang, bukan artefak rantai: tidak di-stage, tidak di-commit, dan tidak dihitung sebagai working tree kotor oleh gerbang git mana pun. Ia dilarang dirujuk sebagai sumber dari `TASK.md`, `BRD.md`, `PRD.md`, maupun brief — dokumen rantai mengutip `file:line` kode, bukan path laporan explorer. Salinannya mendarat di `{taskdir}/.explore/gate-<slug>.md` saat Fase 3 memprovisi taskdir (`references/gate-lifecycle.md` bagian 1), supaya skill hilir memanennya lewat Tahap 0 tanpa menyisir laci gerbang; salinan itu berstatus laci kerja yang sama.

**Subagent mengembalikan:** Badan laporan empat seksi sesuai blok `Format laporan` di atas, ditutup baris `confidence: high | medium | low` pada `### Summary`, plus path berkas yang ditulisnya.
