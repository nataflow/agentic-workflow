# Template Prompt Explorer Kontrak — `code-explorer`

Gunakan template ini saat `system-analysis` mendispatch subagent penelusur kode (`code-explorer`) secara langsung, tanpa skill pembungkus.

**Tujuan:** Menutup empat permukaan wajib Fase 1 dan lima jalur rawan bocor pra-Fase 4 dengan bukti `file:baris` yang cukup mengikat untuk dijadikan tabel kontrak — nama field, tipe data, nilai enum, anotasi validasi, boundary otorisasi, dan batas transaksi.

**Dua profil dispatch.** Keduanya memakai agent yang sama dengan tuntutan pelaporan berbeda, dan **kerangka laporannya berbeda**; jangan mencampurnya dalam satu prompt.

| Profil | Dipakai di | Slug | Berkas laporan | Menutup |
| --- | --- | --- | --- | --- |
| **S — Surface** | Fase 1, bagian A `references/analysis-protocol.md` | `{slug}` | `{taskdir}/.explore/{slug}.md` | Empat permukaan wajib (a)–(d) |
| **B — Blast** | Sebelum Fase 4, sesudah simbol berubah teridentifikasi | `{slug}-blast` | `{taskdir}/.explore/{slug}-blast.md` | Lima dimensi rawan bocor (2, 4, 11, 13, 16) |

**Predikat dispatch wajib (tanpa sapuan pendahulu):** permukaan melintasi lebih dari satu layer atau modul; menyentuh mirrored path menurut `## Navigation recipes` adapter; atau kuota sapuan main loop (3 panggilan `Glob`+`Grep`, potongan ≤40 baris) habis sebelum permukaan terpetakan.

______________________________________________________________________

## Profil S — Pemetaan Permukaan (Fase 1)

````markdown
Objective: {objective}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug penelusuran: {slug}

Kedalaman: menyeluruh

Berkas laporan: {taskdir}/.explore/{slug}.md

Permukaan yang wajib terjawab: {permukaan}

Resep navigasi mirrored path: {resep_navigasi}

Resep di atas adalah pola pencarian jalur async milik repositori ini — consumer antrean, job
terjadwal, broadcast websocket, changelog audit. Jalankan tiap resep itu atas simbol yang kau
petakan; berkas yang tersangkut dilaporkan sebagai barisnya sendiri. Resep yang sudah kau jalankan
tanpa hasil masuk `### Not Found` beserta nama resepnya; resep yang belum sempat kau jalankan masuk
`### Gaps` sebagai "belum disisir". Kau tidak dapat menurunkan resep ini sendiri — berkas adapter
stack di luar jangkauan bacamu, dan jalur async yang tidak punya resep tidak pernah tersapu siapa
pun.

Kedalaman bukti yang dituntut: untuk tiap simbol yang kau temukan, laporkan nama field beserta
tipe datanya, nilai enum yang mungkin, anotasi validasi dan otorisasi yang menempel padanya, serta
batas transaksi yang membungkusnya — bukan sekadar letak simbolnya. Kontrak API yang dirancang di
atas laporan ini menjadi mengikat bagi pemanggil di luar sistem, jadi field yang tipenya tidak
terbaca langsung dari kode dicatat di `### Gaps`, bukan ditebak dan bukan disimpulkan dari nama.

Telusuri sampai kedua ujung: rantai pemanggil naik hingga entry point (controller, listener,
scheduler) dan turun hingga persistence atau outbound event. Mirrored path — konsumer async atas
simbol yang sama — wajib dicari, dan ketiadaannya dicatat sebagai fakta negatif di `### Not Found`
beserta direktori yang sudah disisir, bukan didiamkan.

Format laporan: tulis persis delapan seksi berikut, urutan tetap, tanpa seksi tambahan. Kedelapannya
dikonsumsi pendispatch — jangan pangkas satu pun.

```markdown
### Summary
<Jawaban lugas dan terstruktur atas objective, menyebut permukaan mana yang tertutup dan mana yang
tidak. Tutup dengan baris: `confidence: high | medium | low`>

### Flow & Trace
<Rantai pemanggilan eksekusi aktual dari titik masuk hingga persistensi/event; satu hop per baris
berbukti file:baris>
- `<path/ke/Berkas:baris>` -> <aksi/pemanggilan method konkret>
- `<path/ke/Berkas:baris>` -> <boundary transaksi, validasi, atau akses repository>
- `<path/ke/Berkas:baris>` -> <penerbitan event, query, atau response mapping>

### Layers & Surfaces Touched
<!-- Nama layer mengikuti gaya arsitektur profil: Handler/Service/Repository pada layered; Adapter driving/Use case/Port/Adapter driven pada hexagonal -->
- <Peran/Layer>: `<NamaTipe/Berkas:baris>` — <satu baris ringkas peran dan route mapping/penanda penting>
- <Permukaan Runtime>: `<HTTP | Database | Broker | Cache | Scheduler>` — <detail interface/koneksi yang disentuh>

### Key Pointers & Evidence
<Kolom `Catatan Verifikasi Kode` wajib memuat tipe data, nilai enum, anotasi validasi/otorisasi, dan
batas transaksi yang menempel pada klaim itu — kolom inilah yang jadi dasar tipe field kontrak>

| Klaim Faktual | Bukti Lokasi (`file:line`) | Catatan Verifikasi Kode |
|---|---|---|
| <Fakta/perilaku kode yang terbukti> | `<path/ke/Berkas:baris>` | <tipe, enum, anotasi validasi/otorisasi, batas transaksi, return type> |

### Rules, Invariants & Config
- **Aturan Bisnis & Invariant**: <business rule, transisi status, atau invariant yang terbaca dari kode beserta bukti file:baris>
- **Konfigurasi & Infra**: <key config, nama queue/topic, pola key cache, profile aktif, atau skema migration>

### Error Surface
<Tiap cabang error yang dapat keluar dari permukaan ini, beserta **literal pesannya apa adanya**.
Salin string persis seperti tertulis di kode — termasuk huruf besar-kecil dan tanda bacanya — jangan
diparafrase, jangan diterjemahkan, dan jangan dirapikan. Tabel `## Error` PRD mengikat pesan ini
sebagai kontrak yang dibaca konsumen, dan pendispatch dilarang membaca berkas sumber untuk
mengambilnya sendiri. Cabang yang pesannya dirakit saat runtime dilaporkan beserta pola perakitnya.
Nol cabang error yang terbukti: tulis `tidak ada` beserta berkas handler yang sudah kau sisir>

| Kondisi | HTTP status / tipe | Literal pesan (apa adanya) | Lokasi (`file:baris`) |
|---|---|---|---|
| <kapan cabang ini diambil> | <`500` \| `ServiceUnavailable` \| nama exception> | `<string persis dari kode>` | `<path/ke/Berkas:baris>` |

### Risks, Gaps & Not Found
- **Risiko & Dampak**: <side-effect atau dampak ketergantungan jika bagian kode ini diubah>
- **Gaps**: <field yang tipenya tidak terbaca langsung, cabang yang belum dapat dipastikan, atau jalur yang belum disisir — sebut "belum disisir" apa adanya>
- **Not Found**: <simbol/mirrored path yang dicari tetapi TIDAK ditemukan beserta direktori yang sudah disisir>

### Caveats
<Deviasi konvensi kode, inkonsistensi pola modern vs warisan, atau catatan batas cakupan>
```

Tulis laporan ke `Berkas laporan` lebih dulu, lalu kembalikan badan laporan yang sama ke context.
````

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
| `{objective}` | S | Permukaan wajib yang belum tertutup | **[REQUIRED]** Satu simbol atau satu alur konkret, bukan daftar permukaan. Pertanyaan umum ("cek modul order", `TBD`) dihentikan subagent — pertajam ke simbol lebih dulu |
| `{permukaan}` | S | `references/analysis-protocol.md` bagian A, **Empat permukaan wajib** | **[REQUIRED]** Salin huruf dan bunyi permukaan (a)–(d) yang ditutup dispatch ini apa adanya. Dua permukaan boleh digabung hanya bila keduanya bersandar pada simbol yang sama |
| `{resep_navigasi}` | S | Baris `## Navigation recipes` adapter stack `../../profile/stacks/<stack>.md` | **[REQUIRED]** Disalin apa adanya sebagai daftar berpoin, satu resep satu baris. Subagent dilarang membaca berkas adapter (`stacks/_CONTRACT.md` bagian 4), sehingga resep yang tidak disalin ke sini tidak pernah dijalankan — permukaan (d) mirrored path lalu bergantung pada tebakan pola. Adapter tanpa seksi itu → tulis `tidak ada resep terdaftar` apa adanya, jangan mengarang pola |
| `{simbol_berubah}` | B | Simbol hasil Fase 1 yang kontraknya berubah | **[REQUIRED]** Nama tipe atau method konkret. Blast-sweep tanpa simbol tertentu adalah sapuan liar dan dilarang berangkat |
| `{daftar_dimensi}` | B | `references/analysis-protocol.md` bagian B nomor **2, 4, 11, 13, 16** | **[REQUIRED]** Salin nama kelima dimensi apa adanya sebagai lima baris berpoin. Dilarang meringkasnya jadi "lima dimensi rawan bocor" — subagent tidak membaca berkas protokol pendispatch, dan nama itu jadi kolom `Dimensi` `### Blast Map` |
| `{taskdir}` | S, B | Parameter `taskdir` skill | **[REQUIRED]** Path taskdir aktif apa adanya, mis. `backenddev/docs/2609041530-order-cancel`. Tanpa slot ini subagent tidak punya muara tulis dan menghentikan dispatch |
| `{konteks_diketahui}` | S, B | Fakta yang sudah terbukti di Fase 0 dan dispatch sebelumnya | **[OPTIONAL]** Cegah penelusuran ulang. Isi hanya fakta yang belum tertulis di laci `.explore/`: laporan dispatch sebelumnya dipanen sendiri subagent lewat Tahap 0, jadi jangan disalin ulang ke sini. Tidak tersedia → hapus barisnya utuh, bukan disisakan berlabel kosong |
| `{batas_cakupan}` | S, B | Baris `.claude/profile/domain-map.md` yang cocok | **[OPTIONAL]** Disalin apa adanya. Dilarang mengarang glob. Domain tak terdaftar → hapus barisnya utuh; subagent memakai `source_root` dan mencatatnya di `### Caveats` (Profil S) atau `### Risks, Gaps & Not Found` (Profil B) |
| `{slug}` | S, B | Slug fitur taskdir ditambah pembeda permukaan | **[REQUIRED]** kebab-case, unik per dispatch. Profil B menambahkan sufiks `-blast` yang sudah tertulis di badan template — jangan ditulis dua kali. Slot ini juga menamai berkas laporan, sehingga slug kembar menimpa laporan dispatch sebelumnya |

`Kedalaman` **bukan slot** pada kedua profil. Nilainya dipatok `menyeluruh`: kontrak API, transisi status, dan vonis impact map berdiri di atas rantai pemanggil dan jalur cabang yang lengkap, dan `ringkas` berhenti begitu satu bukti menjawab objective — cukup untuk `business-analysis`, tidak cukup untuk mengikat kontrak keluar.

### Aturan untuk Pendispatch

- **Delegasi lebih dulu, sapuan belakangan**: predikat dispatch di atas berlaku tanpa sapuan pendahulu. Sapuan main loop adalah sisa kuota ringan, bukan langkah pertama.
- **Kuota dibatasi cakupan, bukan angka**: tiap dispatch wajib menutup minimal satu permukaan wajib yang belum tertutup, ditambah tepat satu dispatch Profil B. Dilarang mendispatch ulang permukaan yang sudah tertutup hanya untuk memastikan, dan dilarang membaca ulang berkas yang sudah diringkas explorer.
- **Satu simbol per dispatch Profil S**: permukaan yang berdiri di simbol berbeda berangkat sebagai dispatch terpisah ber-`{slug}` berbeda, bukan satu prompt bercabang.
- **Blok `Format laporan` milik profilnya sendiri**: kerangka seksi tidak lagi ada di `agents/code-explorer.md`, dan kedua profil memakai kerangka berbeda. Memberangkatkan kerangka Profil S pada dispatch Profil B menghasilkan laporan yang tidak memuat `### Blast Map`, sehingga `## Impact map` kehilangan status per dimensinya. Prompt tanpa blok itu dihentikan subagent sebagai kegagalan dispatch.
- **Resep navigasi disalin, bukan dirujuk**: `{resep_navigasi}` mengikuti perlakuan yang sama dengan `{daftar_dimensi}` — subagent tidak membaca berkas adapter, jadi menyebut path-nya saja membuat resep itu tidak pernah sampai. Ini pengecualian kedua, dan satu-satunya selain itu, atas larangan menyalin isi berkas ke dalam prompt.
- **Dilarang menyalin isi berkas**: jangan salin isi `.claude/profile/`, adapter stack, `BRD.md`, atau berkas kode ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri. Pengecualian tunggal: `{daftar_dimensi}` disalin karena subagent tidak membaca `references/analysis-protocol.md`.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot kurung kurawal `{...}` mentah atau placeholder `TBD`/`TODO`.
- **Profil basi menaikkan tuntutan, bukan menurunkan**: skrip prasyarat mencetak banner `[TERDEGRADASI] profil basi` saat `.claude/profile/` tertinggal di belakang `source_root`. Banner itu aktif → `{batas_cakupan}` dari `domain-map.md` diperlakukan sebagai **dugaan**, bukan batas: laporan yang menutup permukaannya dengan bersandar pada batas itu dinilai setara `confidence: medium`, dan vonis "tidak ada" atas jalur di luar batas itu dilarang. Laporkan banner-nya apa adanya di laporan penutup; dilarang disaring.
- **Read-only mutlak**: dilarang menyuruh subagent merancang kontrak, memilih rute arsitektur, memvonis dimensi impact map, atau mengusulkan perubahan kode. Satu-satunya berkas yang boleh ditulisnya adalah `Berkas laporan`.

### Penanganan Balikan

`system-analysis` memetakan balikan sendiri; tidak ada Universal Dispatch Envelope pada jalur ini.

| Balikan subagent | Penanganan `system-analysis` |
| --- | --- |
| `confidence: high` | Pointer `file:line` sah jadi bukti as-is Fase 1 dan dasar langsung kolom tipe Fase 3 |
| `confidence: medium` | Sah sebagai bukti as-is, **tetapi** field kontrak yang bersandar padanya wajib dikonfirmasi di Fase 2 (`AskUserQuestion`) atau turun ke `## Open questions`. Dilarang mengunci tabel kontrak Fase 3 di atasnya tanpa konfirmasi |
| `confidence: low`, atau objective tidak terjawab | Pertajam `{objective}` ke simbol konkret dan ulangi maks sekali dengan `{slug}` baru — slug baru juga mencegah laporan lama tertimpa. Tetap `low` → turun ke sapuan manual di sisa kuota, dan laporkan penyimpangannya pada baris `Explorasi` `## Output` |
| `### Not Found` terisi | Fakta negatif. Pada **Profil S** ia berarti permukaan wajib belum tertutup: tandai permukaan itu "tak ditemukan" di laporan Fase 1, jangan diperlakukan sebagai permukaan yang aman |
| Baris `### Blast Map` berstatus `disisir bersih` | Vonis sah `Tidak terdampak` di `## Impact map` untuk dimensi itu |
| Baris `### Blast Map` berstatus `belum disisir`, atau `### Gaps` menyebut "belum disisir" | **Bukan** fakta negatif dan dilarang divonis `Tidak terdampak`. Tutup dengan dispatch lanjutan, atau naikkan jadi `## Open questions` PRD |
| Dimensi yang diminta tidak muncul sama sekali di `### Blast Map` | Perlakukan sebagai `belum disisir`, bukan sebagai aman. Dimensi yang hilang dari tabel tidak pernah disisir siapa pun |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maks sekali; tetap gagal → sapuan manual di sisa kuota dan laporkan penyimpangannya |

### Peta Seksi Laporan → Konsumen di PRD

Berbeda dari `business-analysis` yang hanya menerima empat seksi, Profil S mengonsumsi kedelapannya. Tiap seksi punya pemilik fase yang pasti:

| Seksi laporan Profil S | Konsumen |
| --- | --- |
| `### Summary` | Predikat cukup-tidaknya permukaan tertutup; baris `confidence` menentukan baris **Penanganan Balikan** di atas |
| `### Flow & Trace` | Fase 3 pilar **status lifecycle** dan urutan evaluasi **validation policy**; tiap hop jadi bukti transisi dan titik validasi |
| `### Layers & Surfaces Touched` | Fase 5 `## Task breakdown` — unit perubahan dinamai dari layer dan permukaan runtime di sini |
| `### Key Pointers & Evidence` | Fase 3 pilar **API contract**; kolom bukti jadi dasar tipe field, aturan validasi per field, dan tabel error |
| `### Rules, Invariants & Config` | Fase 4 `## Impact map` dan `## Migration requirements`; nama queue/topic, pola cache key, dan skema migrasi diambil dari sini |
| `### Error Surface` | Fase 3 tabel `## Error` pilar **API contract** — kolom `Pesan` disalin dari sini apa adanya. Ini satu-satunya rumah literal pesan yang sah: guardrail **NOL SENTUHAN KODE** melarang `system-analysis` membaca berkas sumber, sehingga pesan yang tidak sampai lewat seksi ini tidak punya jalur perolehan lain selain dikarang. Kosong atau `belum disisir` → tulis `<belum terbukti>` di kolom `Pesan` dan naikkan ke `## Open questions`, jangan diisi tebakan |
| `### Risks, Gaps & Not Found` | Fase 4 vonis dimensi; sisa `Gaps` turun jadi `## Open questions` PRD |
| `### Caveats` | Fase 7 daftar fakta yang dikoreksi user; deviasi konvensi disebut apa adanya, tidak dinormalkan diam-diam |

Profil B hanya menyetor tiga seksi, dan `### Blast Map` adalah satu-satunya sumber status per dimensi `## Impact map` — `### Summary`-nya orientasi, bukan vonis.

**Jebakan path berkas.** Laporan explorer memuat path `src/` konkret. Path itu adalah **bukti**, bukan bahan tulis: sah dikutip sebagai `file:line` di seksi kontrak dan konfirmasi fakta, tetapi dilarang mendarat di `## Task breakdown` maupun `## Acceptance criteria` — guardrail **NOL PENETAPAN BERKAS** berlaku penuh, dan pemilihan berkas beserta penamaannya tetap wewenang tunggal `plan`.

**Status berkas laporan.** `{taskdir}/.explore/` adalah zona kerja, bukan artefak rantai: tidak di-stage, tidak di-commit, dan tidak dihitung sebagai working tree kotor oleh gerbang git mana pun. `PRD.md` mengutip `file:baris` kode, bukan path laporan explorer.

**Subagent mengembalikan:** Badan laporan sesuai blok `Format laporan` profil yang berangkat — delapan seksi pada Profil S, tiga seksi pada Profil B — ditutup baris `confidence: high | medium | low` pada `### Summary`, plus path berkas yang ditulisnya.
