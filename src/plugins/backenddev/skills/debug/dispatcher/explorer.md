# Template Prompt Explorer Permukaan Kegagalan — `code-explorer`

Gunakan template ini saat `debug` mendispatch subagent penelusur kode (`code-explorer`) secara langsung.

**Tujuan:** Mempersempit permukaan kegagalan jadi daftar kandidat lokasi bertanda `file:line` sebagai bahan siklus hipotesis Fase 3 — bukan untuk menebak sebabnya.

**Dispatch setelah:** Fase 2 butir 2: permukaan menyentuh lebih dari satu package, rantai pemanggil belum jelas, atau batas transaksi perlu ditelusuri. Permukaan yang terlokalisasi dalam satu berkas dan alurnya terbaca jelas dibaca langsung tanpa dispatch (Fase 2 butir 3).

````markdown
Objective: {objective}

Permukaan awal: {permukaan_awal}

Konteks yang sudah diketahui: {konteks_diketahui}

Batas cakupan: {batas_cakupan}

Slug penelusuran: {slug}

Kedalaman: menyeluruh

Berkas laporan: {taskdir}/.explore/{slug}.md

Batas pertanyaan: telusuri dari permukaan awal ke luar dan kembalikan kandidat lokasi. Dilarang
menyimpulkan sebab kegagalan, mengusulkan perbaikan, maupun menunjuk satu kandidat sebagai akar
masalah — vonis kausal milik pendispatch dan hanya sah lewat siklus hipotesis berbukti.

Wajib ditelusuri sampai kedua ujung: rantai pemanggil di atas permukaan awal sampai entry point yang
memicunya, dan sisi yang dipanggilnya sampai batas I/O atau persistensi.

Aturan pelaporan fakta negatif: jalur yang sudah kau sisir dan terbukti tidak menyentuh permukaan itu
dilaporkan eksplisit di `### Not Found` beserta direktori yang disisir. Jalur yang belum sempat kau
sisir dicatat di `### Gaps` dengan sebutan "belum disisir". Kedua status itu dilarang ditukar:
pendispatch memakai `### Not Found` untuk menggugurkan hipotesis, sehingga jalur yang belum disisir
tetapi dilaporkan tidak ditemukan akan menggugurkan hipotesis yang sebenarnya benar.

Format laporan: tulis persis lima seksi berikut, urutan tetap, tanpa seksi tambahan.

```markdown
### Summary
<Bentuk lintasan yang kau temukan dari permukaan awal, menjawab objective tanpa menunjuk sebab.
Tutup dengan baris: `confidence: high | medium | low`>

### Flow & Trace
<Rantai pemanggilan eksekusi aktual dari entry point pemicu hingga batas I/O atau persistensi; satu
hop per baris berbukti file:baris>
- `<path/ke/Berkas:baris>` -> <aksi/pemanggilan method konkret>

### Candidate Locations
<Kandidat lokasi cacat, bukan vonis. Kandidat tanpa `file:baris` konkret dibuang, bukan diturunkan
derajatnya>

| Kandidat | Bukti Lokasi (`file:line`) | Kenapa ia jadi kandidat |
|---|---|---|
| <Kelas.method atau blok konkret> | `<path/ke/Berkas:baris>` | <apa yang membuat baris ini bisa menghasilkan gejala, tanpa menyatakan bahwa ia penyebabnya> |

### Rules, Invariants & Config
<Empat hal berikut wajib disebut eksplisit untuk tiap yang alurnya lewati — keempatnya kerap jadi
tempat cacat bersembunyi tanpa pernah muncul di stacktrace, sehingga alur yang dilaporkan tanpa
menyebutnya menyisakan kandidat yang tak pernah masuk daftar>
- **Batas transaksi**: <di mana dibuka, di mana ditutup, propagasi/isolasi yang menempel> — `<file:baris>`
- **Urutan validasi**: <validasi yang dievaluasi dan urutannya> — `<file:baris>`
- **Mapping ORM**: <relasi, fetch/cascade, kolom yang ikut tersentuh> — `<file:baris>`
- **Wiring komponen**: <bean/provider/qualifier, profil aktif, atau konfigurasi yang menentukan implementasi mana yang terpakai> — `<file:baris>`

### Risks, Gaps & Not Found
- **Gaps**: <jalur yang belum disisir, ditulis "belum disisir" apa adanya; plus batas cakupan yang terpaksa dipakai bila domain tak terdaftar di profil>
- **Not Found**: <jalur yang sudah disisir dan terbukti tidak menyentuh permukaan ini, beserta direktori yang disisir>
```

Tulis laporan ke `Berkas laporan` lebih dulu, lalu kembalikan badan laporan yang sama ke context.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{objective}` | Pertanyaan fokus tunggal yang disusun Fase 2 butir 2 | **[REQUIRED]** Satu pertanyaan bersimbol konkret, bukan gejala mentah. `kenapa error` bukan objective yang sah — subagent menghentikannya |
| `{permukaan_awal}` | Frame terdalam milik `root_namespace` pada stacktrace, Fase 2 butir 1 | **[REQUIRED]** Ditulis `file:baris` atau `Kelas.method`, dipersempit `scope_hint` bila terisi. Tanpa titik pijak ini penelusuran `menyeluruh` melebar ke seluruh `source_root` |
| `{taskdir}` | Parameter `taskdir` skill | **[REQUIRED]** Path taskdir aktif apa adanya, mis. `backenddev/docs/2609041530-order-cancel`. Tanpa slot ini subagent tidak punya muara tulis dan menghentikan dispatch |
| `{konteks_diketahui}` | Fakta terbukti dari Fase 0 dan Fase 1: versi, profil aktif, langkah reproduksi | **[OPTIONAL]** Subagent tidak menelusurinya ulang. Isi hanya fakta yang belum tertulis di laci `.explore/`: laporan dispatch sebelumnya dipanen sendiri subagent lewat Tahap 0, jadi jangan disalin ulang ke sini. Tidak tersedia → hapus barisnya utuh, bukan disisakan berlabel kosong |
| `{batas_cakupan}` | Baris `.claude/profile/domain-map.md` yang cocok dengan permukaan awal | **[OPTIONAL]** Disalin apa adanya. Dilarang mengarang glob sendiri. Domain tidak terdaftar → hapus barisnya utuh; subagent memakai `source_root` dan mencatat batasnya di `### Risks, Gaps & Not Found` |
| `{slug}` | Slug insiden yang sedang diinvestigasi | **[REQUIRED]** kebab-case, unik per dispatch dalam satu sesi investigasi. Slot ini juga menamai berkas laporan, sehingga slug kembar menimpa laporan dispatch sebelumnya |

`Kedalaman` **bukan slot**. Nilainya dipatok `menyeluruh` di badan template: ketiga pemicu dispatch Fase 2 butir 2 seluruhnya pertanyaan rantai, dan `ringkas` berhenti pada kemunculan pertama — persis memotong rantai pemanggil yang jadi alasan dispatch itu berangkat.

### Aturan untuk Pendispatch

- **Satu pertanyaan per dispatch**: satu dispatch memuat tepat satu `{objective}`. Dua permukaan berangkat sebagai dua dispatch ber-`{slug}` berbeda, bukan satu prompt bercabang.
- **Dispatch hanya untuk pertanyaan rantai**: permukaan yang terbaca jelas dalam satu berkas dibaca sendiri. Mendispatch untuk berkas tunggal membakar giliran tanpa menambah jangkauan.
- **Framing lokasi, bukan sebab**: `{objective}` menanyakan lintasan dan letak (`siapa yang membuka transaksi sebelum OrderService.cancel dipanggil`), bukan diagnosis (`kenapa order gagal dibatalkan`). Diagnosis milik siklus hipotesis Fase 3.
- **Dilarang menyalin isi berkas**: jangan salin isi `.claude/profile/`, berkas kode, atau log mentah panjang ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot kurung kurawal `{...}` mentah atau placeholder `TBD`/`TODO`.
- **Blok `Format laporan` ikut berangkat utuh**: kerangka seksi tidak lagi ada di `agents/code-explorer.md`. Prompt yang diberangkatkan tanpa blok itu dihentikan subagent sebagai kegagalan dispatch.
- **Read-only mutlak**: dilarang menyuruh subagent mengubah kode, menjalankan reproduksi, atau menambal cacat yang ia temukan. Satu-satunya berkas yang boleh ditulisnya adalah `Berkas laporan`.

### Penanganan Balikan

`debug` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `debug` |
| --- | --- |
| Laporan terisi, `confidence: high` atau `medium` | Susun daftar kandidat Fase 2 butir 5 dari `### Candidate Locations`. Kandidat tanpa `file:line` konkret dibuang, bukan diturunkan derajatnya |
| `confidence: low`, atau `{objective}` tidak terjawab | Perbaiki `{objective}` jadi satu pertanyaan bersimbol konkret dan dispatch ulang sekali dengan `{slug}` baru agar laporan lama tidak tertimpa. Tetap gagal → lanjutkan dengan pembacaan kode manual dan catat keterbatasannya di `## Rantai kausal` |
| `### Rules, Invariants & Config` tidak menyebut salah satu dari empat butirnya | Jangan simpulkan butir itu tidak ada di alur. Sapu sendiri atau dispatch ulang sekali — batas transaksi dan wiring yang tak pernah dilihat adalah kandidat yang tak pernah masuk daftar |
| `### Not Found` terisi | Fakta negatif yang sah: jalur tersisir dan bersih menggugurkan hipotesis yang menyandarinya. Catat sebagai bukti negatif di `## Rantai kausal` — hipotesis yang gugur berbukti lebih berharga daripada yang dibiarkan menggantung |
| `### Gaps` berbunyi "belum disisir" | Bukan fakta negatif. Dilarang dipakai menggugurkan hipotesis mana pun; jalur itu tetap kandidat terbuka sampai ada yang menyisirnya |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Ulangi maksimum sekali; tetap gagal → lanjutkan pembacaan kode manual dan catat kendalanya di `## Rantai kausal` |

**Batas serap.** Laporan ini mempersempit pencarian, bukan menggantikan pembacaan. `RCA.md` berstatus `ROOT_CAUSE_CONFIRMED` menuntut tiap tautan `## Rantai kausal` berdiri di atas baris kode yang benar-benar dibaca — pointer explorer menunjukkan baris mana yang layak dibaca, dan menyalinnya jadi vonis kausal tanpa membacanya menghasilkan RCA yang tampak berbukti padahal tidak. Seksi `### Rules, Invariants & Config` dibaca sebagai kandidat hipotesis, bukan sebagai sebab yang sudah tervalidasi.

**Status berkas laporan.** `{taskdir}/.explore/` adalah zona kerja, bukan artefak rantai: tidak di-stage, tidak di-commit — `debug` memang dilarang menjalankan git commit — dan tidak dihitung sebagai working tree kotor oleh gerbang git mana pun. `RCA.md` mengutip `file:baris` kode, bukan path laporan explorer.

**Subagent mengembalikan:** Badan laporan lima seksi sesuai blok `Format laporan` di atas, ditutup baris `confidence: high | medium | low` pada `### Summary`, plus path berkas yang ditulisnya.
