# BRD template — `business-analysis`

Dipakai di Fase 4 (`SKILL.md`) sebagai isi file `backenddev/docs/<YYMMDDhhmm>-<slug>/BRD.md`. Ikuti struktur ini persis — sembilan nama seksi dan urutannya adalah kontrak yang dibaca `system-analysis`. Jangan mengganti, menambah, atau menghapus seksi.

```markdown
---
title: <nama fitur/topik singkat>
requester: <nama/role yang meminta>
status: DRAFT
---

# BRD: <title> — <yyyy-mm-dd>

## Problem
<masalah inti yang dihadapi, siapa yang paling merasakan dampak turunannya, dan seberapa sering terjadi (tiap transaksi | beban puncak | insidental)>

Biaya pembiaran:
- Finansial: <selisih saldo, denda SLA, kehilangan penjualan — berangka atau bersatuan; atau "nihil" beserta alasannya>
- Operasional: <jam kerja manual terbuang untuk rekonsiliasi; atau "nihil" beserta alasannya>
- Integritas data: <data menggantung tanpa pemilik, status entity tidak sinkron; atau "nihil" beserta alasannya>

## Actors
- **<peran konkret>** (primer | approver | sistem | terlarang) — boleh: <aksi yang diizinkan>; dilarang: <aksi yang tegas dilarang>
- **<peran berikutnya>** (…) — boleh: <…>; dilarang: <…>

<Istilah generik "user" dilarang. Wajib memuat minimal satu peran berjenis `terlarang`. Skenario pencabutan atau perpindahan hak akses di tengah transaksi berjalan ditulis sebagai `EC-{n}` berkategori `status-eksternal`, bukan di sini.>

## Current state
<alur yang berjalan saat ini langkah demi langkah, termasuk proses manual di luar sistem. Pernyataan hasil baca kode wajib ditandai "Observasi kode" + `file:line`; jangan ditulis seolah-olah aturan bisnis>

## Target state
<alur bisnis baru yang diinginkan langkah demi langkah, apa yang berubah secara spesifik bagi tiap aktor, dan apakah menggantikan alur lama secara penuh atau bertahap>

## Business rules
- **BR-1**: <aturan bisnis deterministik yang harus selalu benar: Kondisi -> Syarat -> Invariant>
- **BR-2**: <aturan berikutnya dengan ID berurutan>

Pensiun: <BR-lama → BR-baru (apa yang berubah)>, atau "tidak ada"

## Edge cases
- **EC-1** [<kategori>]: <penanganan konkret satu kasus batas: pemicu -> perilaku yang diharapkan>
- **EC-2** [<kategori>]: <kasus berikutnya dengan ID berurutan>

Kategori nihil: <kategori tanpa kasus beserta alasannya>, atau "tidak ada"

## Business metrics
- **BM-1**: <metrik bisnis yang bergerak> — baseline: <nilai saat ini>; target: <nilai yang diharapkan>; diobservasi: <pihak dan sumber datanya>; digerakkan: SC-<n>
- **BM-2**: <metrik berikutnya dengan ID berurutan>
- **BM-LUAR-RANTAI: BM-<n>** — alasan: <mengapa target ini tidak dikejar satu pun kriteria akar taskdir ini>  <baris ini ditulis hanya untuk metrik yang memang tak berpaut `SC-{n}`; metrik biasa cukup baris `BM-{n}` di atasnya>

<Nihil metrik yang dapat diukur -> tulis satu baris `- **BM-0**: Tidak ada metrik bisnis yang bergerak` beserta alasannya. Seksi ini dinamai `Business metrics`, bukan `Success criteria`: `## Success Criteria` adalah milik `TASK.md` dan diangkut sumbu `SC-{n}` yang digrep hilir, sehingga dua heading senama di satu taskdir membuat penyandingan mekanis salah sasaran.>

## Out of scope
<fitur atau skenario terkait yang secara sadar DITUNDA atau DIKECUALIKAN dari ruang lingkup pekerjaan ini>

## Open questions
<kosong adalah keadaan normal: tulis eksplisit "Tidak ada pertanyaan terbuka", jangan dibiarkan kosong. Ada yang tersisa -> maksimum tiga entri, satu baris per entri dengan tiga bagian:
- **<pertanyaan konkret>** — terdampak: <seksi/BR yang berubah kalau jawabannya lain>; sementara dipakai: <asumsi aktif>>
```

## Authoring rules

- **Status** selalu mulai `DRAFT`. Hanya `backenddev:analyst` yang mengubahnya jadi `APPROVED`, di gerbang dokumen Fase 4-nya dan sesudah persetujuan eksplisit user. Rumah kanonik kepemilikan itu `analyst/references/chain-rules.md` bagian 4; `business-analysis` dilarang menulis nilai itu maupun meminta persetujuan user atas dokumennya sendiri.
- **Observasi vs aturan dibedakan eksplisit.** Kalimat hasil membaca kode berlabel "Observasi kode" disertai `file:line`; kalimat hasil konfirmasi user, khusus di `## Business rules`, berlabel `BR-{n}`. Pembaca harus bisa membedakan keduanya tanpa bertanya balik.
- **Tiap business rule diberi ID `BR-{n}` berurutan** (`BR-1`, `BR-2`, …), tidak diberi ulang meski urutan penyajian berubah saat revisi — ID ini yang dirujuk PRD dari `system-analysis`, jadi sekali diberikan tidak dipakai ulang untuk aturan lain di dokumen yang sama.
- **Aturan yang berubah makna dipensiunkan, bukan ditimpa.** `preserve_history` mempertahankan nomor, dan itu sah hanya selama maknanya tetap. Revisi yang mengubah kondisi, syarat, atau invariant sebuah `BR-{n}` wajib **mempensiunkan nomor lama dan menerbitkan aturannya sebagai nomor baru** di ujung daftar, lalu mencatat jejaknya di baris `Pensiun:` (`Pensiun: BR-3 → BR-9 (syarat approval berubah)`). Alasannya ada di hilir: `PRD.md` yang sudah terbit merujuk `BR-{n}` di kolom `Dasar`, dan menimpa makna di nomor yang sama membuat rujukan itu basi tanpa jejak apa pun. Dengan pensiun, PRD basi otomatis memegang **rujukan hantu** — kegagalan yang sudah ditangkap `## Self-test pra-reviewer` PRD butir 1 dan `prd-reviewer` fokus #5. Penghalusan redaksi tanpa perubahan makna tetap memakai nomor lama.
- **Tiap kasus batas diberi ID `EC-{n}` berurutan**, satu kasus satu baris, dengan aturan permanensi yang sama seperti `BR-{n}`. Ini **rumah kanonik** penomoran kasus batas: `system-analysis` menyandingkan tiap `EC-{n}` dengan Acceptance Criteria PRD-nya secara mekanis, jadi kasus batas yang ditulis sebagai prosa mengalir tanpa ID membuat penyandingan itu mustahil. Nihil kasus batas → tulis satu baris `- **EC-0**: Tidak ada kasus batas yang teridentifikasi` beserta alasannya, bukan seksi kosong.
- **Tiap `EC-{n}` memikul label kategori taksonomi.** Lima kategori `references/elicitation-guide.md` §5 ditulis sebagai slug di dalam kurung siku tepat sesudah ID: `data-hilang` (field opsional tidak dikirim), `duplikasi` (submit dobel atau event diterima ulang — idempotensi), `in-flight` (gagal di tengah rangkaian: rollback penuh, tersimpan sebagian, atau kompensasi manual), `timeout` (batas waktu terlampaui, termasuk kapan alokasi stok atau kuota dilepaskan kembali), `status-eksternal` (kondisi di luar alur berubah saat transaksi menggantung — akun dibekukan, hak akses dicabut). Slug di luar kelimanya dilarang; guide itu **rumah kanonik** taksonominya. Kelima kategori wajib tersapu: kategori tanpa kasus disebut namanya di baris `Kategori nihil:` beserta alasannya, bukan didiamkan.
- **Tiap aktor memikul daftar aksi diizinkan dan aksi tegas dilarang.** Satu peran satu baris berjenis `primer`, `approver`, `sistem`, atau `terlarang`, masing-masing membawa `boleh:` dan `dilarang:`. Istilah generik "user" tanpa kualifikasi peran ditolak — `system-analysis` menurunkan matriks `## Permission & scope` PRD dari seksi ini, dan matriks tidak bisa dibangun di atas aktor yang tidak bernama. Minimal satu baris berjenis `terlarang` wajib ada: pihak yang eksplisit dilarang mengakses alur ini adalah bagian dari kontrak, bukan sisa.
- **Biaya pembiaran dikuantifikasi pada tiga sumbu.** `## Problem` wajib memuat baris `Finansial:`, `Operasional:`, dan `Integritas data:`, masing-masing berangka, bersatuan, atau bernilai "nihil" beserta alasannya. Keluhan sifat ("lambat", "membingungkan") tanpa indikator konkret bukan temuan dan tidak sah mengisi ketiganya. Frekuensi kejadian ditulis sebagai salah satu dari `tiap transaksi`, `beban puncak`, atau `insidental`.
- **Tidak ada seksi berisi "TBD".** Seksi yang belum bisa diisi substantif → pindahkan pertanyaannya ke `## Open questions` sebagai pertanyaan konkret, dan seksi asalnya tetap ditulis dengan apa yang sudah diketahui (boleh singkat, tidak boleh placeholder).
- **Anggaran `## Open questions`: nol adalah target, tiga adalah batas.** Yang bisa dijawab kode dijawab dengan membaca kode; yang butuh keputusan user ditanyakan di Fase 2, bukan disimpan ke sini. Entri yang tersisa wajib **tidak memblokir** — BRD tetap bisa di-`APPROVED` dan PRD tetap bisa disusun tanpa jawabannya. Yang memblokir boleh ditulis, tapi BRD-nya berhenti di `DRAFT` sampai terjawab; itu keadaan yang dilaporkan, bukan yang di-approve.
- **Tiap metrik bisnis diberi ID `BM-{n}` berurutan** dengan aturan permanensi yang sama seperti `BR-{n}`, dan tiap baris memikul baseline, target, serta pihak pengobservasinya. Konsumennya adalah ringkasan eksekutif `backenddev:analyst` di gerbang dokumen: `BM-{n}` disajikan ke user sebagai hasil bisnis yang diklaim rantai ini, sehingga metrik tanpa baseline tidak bisa dinilai bergerak atau tidak. Metrik teknis (latensi, coverage) bukan isi seksi ini.
- **Tiap `BM-{n}` menyebut kriteria akar yang menggerakkannya.** Baris `digerakkan: SC-{n}` menunjuk minimal satu `SC-{n}` `## Success Criteria` `TASK.md`, atau metriknya ditulis sebagai entri bertoken `BM-LUAR-RANTAI: BM-{n}` beserta alasannya. Tanpa penyandingan ini BRD boleh menjanjikan target bisnis yang tak satu pun kriteria akar kejar, dan tak ada gerbang yang pernah menyandingkan keduanya — datanya sudah ada di kedua sisi, yang absen hanya barisnya. Token itu bukan formalitas: ia bentuk yang sama dengan `BR-DISANGGAH:`, dan gunanya sama — membuat yang sengaja dilepas tetap terlihat, bukan lenyap. `TASK.md` absen: baris `digerakkan:` berisi `—`.
- **`## Out of scope` tidak boleh kosong diam-diam** — tidak ada yang dikecualikan → tulis eksplisit "Tidak ada pengecualian yang disepakati sejauh ini".

## Self-test struktural

Dijalankan `business-analysis` atas `BRD.md` yang baru ditulis, sebelum `brd-reviewer` didispatch, lewat `skills/_common/validate_doc.py --kind brd --taskdir <taskdir>`. Validator menagih butir mekanis (ID check di kurung siku); `WARN` adalah heuristik yang diperiksa penulis; butir `MANUAL` dinilai penulis memakai prosa di bawah. Satu `FAIL` berarti BRD diperbaiki seketika lalu validator dijalankan ulang.

1. **Struktur** [B1]: frontmatter `title`, `requester`, `status: DRAFT`; tepat satu H1 `# BRD: …`; sembilan seksi baku dengan nama dan urutan persis template.
2. **Penomoran** [B2]: `BR-{n}`, `EC-{n}`, `BM-{n}` masing-masing urut tanpa lompatan dan tanpa ganda — `EC-0`/`BM-0` hanya sebagai satu-satunya baris. Nomor pensiun (baris `Pensiun:`) mengisi celah penomoran dan dilarang muncul lagi sebagai aturan aktif. `BM-LUAR-RANTAI: BM-{n}` menunjuk `BM-{n}` yang ada dan tidak menambah nomor.
3. **Observasi vs aturan** [B3]: tiap `file:baris` di `## Current state` berlabel `Observasi kode:` pada baris yang sama (FAIL); berkas yang tidak ada di repo adalah `WARN`.
4. **Nol placeholder** [B4]: nol `TBD`, `TODO`, `diisi nanti` di luar blok kode.
5. **Seksi nihil tetap bersuara** [B5]: `## Edge cases`, `## Business metrics`, `## Out of scope`, `## Open questions` berisi item atau penegasan eksplisitnya (`EC-0`, `BM-0`, "Tidak ada pengecualian yang disepakati sejauh ini", "Tidak ada pertanyaan terbuka").
6. **Anggaran Open questions** [B6]: maksimal tiga entri, tiap entri memuat `terdampak:` dan `sementara dipakai:`. Entri yang `terdampak:`-nya menyebut `## Business rules` atau `## Target state` memblokir — BRD tetap `DRAFT` dan approval tidak diajukan.
7. **Batas akar** [B7a: `digerakkan:` BM → SC nyata, rujukan `SC-{n}` hantu; B7b MANUAL: BR → SC dan sentuhan `## Out of Scope`]: bila `{taskdir}/TASK.md` ada, tiap `BR-{n}` terpetakan ke minimal satu `SC-{n}` `## Success Criteria`-nya dan tidak ada aturan yang menyentuh `## Out of Scope`-nya. Tiap `BM-{n}` selain `BM-0` memikul baris `digerakkan:` yang menyebut minimal satu `SC-{n}` nyata, atau ditulis sebagai entri `BM-LUAR-RANTAI: BM-{n}` beralasan; nomor `SC-{n}` yang tidak ada di `TASK.md` adalah rujukan hantu dan sama-sama gagal. Aturan yang menyentuh `## Out of Scope` dikembalikan ke `backenddev:analyst` sebagai permintaan amandemen akar, bukan dibuang sendiri. `TASK.md` absen: butir ini dilewati.
8. **Taksonomi kasus batas** [B8]: tiap `EC-{n}` membawa tepat satu slug dari lima yang sah (`data-hilang`, `duplikasi`, `in-flight`, `timeout`, `status-eksternal`), dan kelimanya tersapu — dipakai `EC-{n}` atau disebut beserta alasannya di baris `Kategori nihil:`.
9. **Aktor & aksi terlarang** [B9]: tiap baris `## Actors` berbentuk `- **<peran>** (<primer|approver|sistem|terlarang>) — boleh: …; dilarang: …`, minimal satu `terlarang`; kata "user" berdiri sendiri adalah `WARN`.
10. **Biaya pembiaran terkuantifikasi** [B10]: `## Problem` memuat baris `Finansial:`, `Operasional:`, `Integritas data:` yang terisi, dan frekuensi `tiap transaksi`, `beban puncak`, atau `insidental`. Isi tiap sumbu berangka, bersatuan, atau "nihil" beralasan — kata sifat tanpa indikator adalah kegagalan yang dinilai penulis.
11. **Nol heading tabrakan** [B11]: tidak ada `## Success criteria`/`## Success Criteria` — heading itu milik `TASK.md`.

12. **Kecukupan aturan** [B12 MANUAL] — arah balik butir 7, dan tidak pernah dilewati: butir 7 memvonis aturan yang menembus batas akar, butir ini memvonis aturan yang tidak punya akar sama sekali. Sandingkan tiap `BR-{n}` dengan akarnya — `SC-{n}` `## Success Criteria` bila `TASK.md` ada, jawaban elisitasi Fase 2 bila absen — lalu periksa masing-masing menutup bagian akar yang belum ditutup `BR-{n}` lain. Aturan kedua di atas akar yang sudah tertutup penuh wajib menyebut bagian yang belum tertutup itu di prosanya. `Grep` `## Business rules` atas aturan yang tak berpasangan dengan satu pun akar — pengetatan yang tidak diminta, kewajiban audit/log/notifikasi yang tak disinggung, dan aturan bersyarat masa depan ("bila nanti", "untuk berjaga-jaga") — satu kecocokan adalah kegagalan: hapus aturannya, dilarang dicarikan akar susulan. Aturan yang benar-benar dibutuhkan tetapi akarnya belum ada bukan pengecualian butir ini: ia permintaan amandemen akar, dan rutenya butir 7.

Hasilnya: keluaran validator ditambah satu baris per butir `MANUAL` (`butir <n>: lolos` atau `butir <n>: gagal — <rincian>`), dan dispatch `brd-reviewer` dilarang berangkat sebelum seluruhnya lolos.

## Contoh terisi — `orders-api` (dipangkas, tidak tersalin ke artefak)

```markdown
---
title: Pembatalan order berstatus PAID
requester: Pemilik toko (via CS)
status: DRAFT
---

# BRD: Pembatalan order berstatus PAID — 2026-09-05

## Problem
Pemilik toko tidak dapat membatalkan order yang sudah dibayar tetapi belum dikirim; CS membatalkannya manual lewat SQL. Terjadi insidental, ±20 order per minggu.

Biaya pembiaran:
- Finansial: nihil — pembayaran tetap tercatat, refund diproses terpisah
- Operasional: ±2 jam kerja CS per minggu untuk pembatalan manual
- Integritas data: order `PAID` yang dibatalkan manual tidak memicu pengembalian stok (`Observasi kode: internal/order/service.go:142` — `Cancel` hanya menerima `PENDING`)

## Actors
- **Pemilik toko** (primer) — boleh: membatalkan order `PAID` miliknya yang stoknya belum dikurangi; dilarang: membatalkan order toko lain
- **Sistem payment** (sistem) — boleh: menerima sinyal pembatalan; dilarang: mengubah status order
- **Pembeli** (terlarang) — boleh: melihat status order miliknya; dilarang: membatalkan order `PAID`

## Current state
Order `PAID` hanya berubah ke `FULFILLED` lewat job pengiriman. Observasi kode: `internal/order/state.go:27` — transisi keluar dari `PAID` hanya `FULFILLED`.

## Target state
Pemilik toko membatalkan order `PAID` dari dashboard; sistem menolak bila stok sudah dikurangi, dan pembatalan yang sah mengembalikan stok.

## Business rules
- **BR-1**: Order `PAID` dapat dibatalkan hanya bila belum `FULFILLED` dan stoknya belum dikurangi
- **BR-2**: Pembatalan order `PAID` mengembalikan stok tiap item ke gudang asal

Pensiun: tidak ada

## Edge cases
- **EC-1** [status-eksternal]: job pengiriman mengubah order ke `FULFILLED` di tengah permintaan pembatalan → pembatalan ditolak, status tetap `FULFILLED`

Kategori nihil: `data-hilang` — pembatalan tidak menerima payload; `duplikasi` — permintaan kedua atas order `CANCELLED` jatuh ke EC-1 yang sama; `in-flight` — pengembalian stok dan perubahan status satu transaksi DB; `timeout` — tidak ada alokasi berbatas waktu

## Business metrics
- **BM-1**: order `PAID` dibatalkan manual oleh CS — baseline: ±20/minggu; target: 0; diobservasi: CS lead dari log SQL manual; digerakkan: SC-1

## Out of scope
Refund otomatis ke payment gateway; pembatalan oleh pembeli.

## Open questions
Tidak ada pertanyaan terbuka
```
