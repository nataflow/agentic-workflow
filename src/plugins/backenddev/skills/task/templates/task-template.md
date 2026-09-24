# TASK Template & Self-test Akar — `task`

Dipakai di Fase 5 (`SKILL.md`) sebagai isi berkas `backenddev/docs/<YYMMDDhhmm>-<slug>/TASK.md`. Ikuti bagian 1 persis — satu H1 dan empat heading, tidak lebih: begitu dokumen menuntut sub-heading di luar keempatnya, isinya milik `business-analysis`, `system-analysis`, atau `plan`. Bagian 2 tidak ikut tersalin ke artefak.

______________________________________________________________________

## 1. Template Kanonik TASK.md

````markdown
---
status: ACTIVE
chain: <BRD_PRD_BRIEF | PRD_BRIEF | BRIEF>
lane: <PRD_CONVERSION | DIRECT_BRIEF | DEFECT_RCA | EXEC_BRIEF>
risk: <BREAKING | MAJOR | MINOR | ->
created: <YYYY-MM-DD>
---

# <Domain — jenis kerja, maksimal 8 kata>

## Chain

- [ ] BRD   — backenddev:business-analysis → BRD.md
- [ ] PRD   — backenddev:system-analysis  → PRD.md
- [ ] BRIEF — backenddev:plan             → brief-*.md

<Ledger rantai planning. Muat **tepat** hop milik `chain:` frontmatter, berurutan — hop di luar chain dihapus barisnya, bukan dibiarkan tak tercentang. Hop tuntas dicentang `backenddev:analyst` beserta jejaknya (`- [x] PRD — backenddev:system-analysis → PRD.md @ APPROVED a1b2c3d`). Rumah kanonik enum dan aturan pencentangannya di `analyst/references/chain-rules.md` bagian 2. Lane non-planning (`DEFECT_RCA`, `EXEC_BRIEF`): hilangkan seksi ini beserta baris `chain:` frontmatter.>

## Description

<Kalimat 1: Keputusan target perubahan perilaku sistem atau pembuatan artefak saat ini secara definitif.>
<Kalimat 2–4: Kondisi kode teknis terverifikasi dengan minimal satu rujukan `file:baris` (dilarang menulis narasi riwayat/komparasi masa lalu).>

## Success Criteria

- [ ] **SC-1**: <hasil terukur> — verifikasi: <diff, test, atau artefak bernama>
- [ ] **SC-2**: <hasil terukur> — verifikasi: <diff, test, atau artefak bernama>
- [ ] **SC-3**: <hasil terukur> — verifikasi: <diff, test, atau artefak bernama>

<ID `SC-{n}` berurutan mulai `SC-1`, permanen sepanjang umur taskdir. Hilir merujuk nomor ini — `system-analysis` di kolom `Akar` tabel Acceptance Criteria, `plan` di baris `Fulfills:` brief — sehingga prosa butir tidak pernah perlu disalin ke dokumen hilir.>

## Out of Scope

- <yang tidak dikerjakan> — <alasan: batas modul | opsi yang ditolak | eskalasi ditunda>
````

______________________________________________________________________

## 2. Self-test Akar

Dijalankan `task` atas `TASK.md` yang baru ditulis, sebelum commit Fase 5 berangkat. Butir 2–4 dan 8a dipanggil ulang `backenddev:analyst` sesudah transisi eskalasi chain (`analyst/references/chain-rules.md` bagian 3 langkah 4); sisanya milik `task` sendiri. Ini penyaring mekanis, bukan penilaian: tiap butir dijawab dengan `Grep` atau `Read` bertarget, dan satu butir gagal berarti `TASK.md` diperbaiki seketika lalu rangkaian diulang dari butir 1. `TASK.md` adalah akar rantai — cacat di sini menular ke BRD, PRD, dan tiap brief tanpa satu pun gerbang hilir yang memeriksanya kembali.

1. **Struktur & frontmatter**: frontmatter memuat `status: ACTIVE`, `lane` bernilai salah satu dari 4 enum, `risk` bernilai salah satu dari 4 enum, dan `created` berformat `YYYY-MM-DD`. Body memuat tepat satu H1 dan tepat empat heading `## Chain`, `## Description`, `## Success Criteria`, `## Out of Scope` dengan nama dan urutan persis bagian 1 — tiga heading tanpa `## Chain` pada lane non-planning. Heading yang hilang, tertukar, atau bertambah adalah kegagalan.
2. **Penomoran `SC-{n}`**: baris `- [ ] **SC-{n}**:` berurut mulai `SC-1` tanpa lompatan dan tanpa nomor ganda, berjumlah 1–7 butir. Butir tanpa ID atau bernomor ganda adalah kegagalan: seluruh hilir merujuk nomor ini.

   > Lantai satu butir, bukan tiga. Cakupanlah yang menentukan jumlahnya, dan butir 9 di bawah yang menggerbanginya — lantai yang lebih tinggi daripada permukaan yang benar-benar diminta memaksa penambalan yang justru gugur di butir itu. Perbaikan satu temuan, satu bugfix lokal, dan satu rename bermuara di satu butir; itu bentuk normalnya, bukan akar yang kurang lengkap.
3. **Alat ukur sah per lane**: tiap butir memuat literal `— verifikasi:` diikuti alat ukur yang terdaftar di kolom "Alat ukur yang sah" tabel Fase 3 untuk `lane` berkas ini. Akar ber-`finding_source`: tiap butir pemikul temuan wajib menambahkan penandaan `> Status: FIXED` atas ID temuannya di samping alat ukur lane itu (`SKILL.md` Fase 3 butir 6); butir pemikul temuan yang tidak memuatnya adalah kegagalan. Alat ukur subjektif ("review manual", "dinilai layak"), yang tidak cocok dengan lane-nya, atau yang menunjuk dokumen hop hilir yang belum terbit (`BRD.md`, `PRD.md`) adalah kegagalan. Klausa ini satu-satunya bagian butir SC yang boleh ditulis ulang `backenddev:analyst` saat eskalasi chain menggeser lane; prosa hasil yang diukur tidak pernah ikut berubah.
4. **Ambang terukur**: tiap butir menyebut nama entitas, threshold numerik, atau status spesifik. Kata sifat tanpa ambang ("lebih cepat", "optimal", "rapi") adalah kegagalan.
5. **Bukti berpaut kode**: `## Description` memuat minimal satu `file:baris`, dan tiap rujukan itu diperiksa satu per satu menunjuk berkas yang benar-benar ada di repositori. Rujukan menggantung adalah kegagalan — dilarang mengarangnya kembali dari ingatan.
6. **Batas kerja bersuara**: `## Out of Scope` memuat minimal satu butir berformat `- <yang tidak dikerjakan> — <alasan>`. Seksi kosong atau butir tanpa alasan adalah kegagalan; `business-analysis`, `system-analysis`, dan `plan` menegakkan batas ini sebagai plafon ruang lingkupnya.
7. **Nol placeholder**: `Grep` seluruh berkas atas `TBD`, `TODO`, `diisi nanti`, dan sisa penanda template berbentuk `<...>`. Satu kecocokan adalah kegagalan.
8. **Ledger chain utuh.** Butir ini bercabang dua karena keduanya dipanggil di titik yang berbeda: 8a memeriksa **struktur** ledger dan berlaku kapan pun `TASK.md` bermutasi, 8b memeriksa **kondisi awal** dan hanya berlaku saat berkasnya baru ditulis.

   - **8a — Struktur ledger.** `chain:` frontmatter bernilai salah satu dari `BRD_PRD_BRIEF`, `PRD_BRIEF`, `BRIEF`, dan baris `## Chain` memuat **tepat** hop chain itu — tidak kurang, tidak lebih, urut. `lane` cocok dengan kolom lane terminal matriks bagian 1.3 `analyst/references/chain-rules.md`, dan pasangan `(risk, chain)` sah menurut tabel bagian 1.4 di sana. Lane non-planning: `chain:` dan `## Chain` sama-sama absen; salah satu hadir sendirian adalah kegagalan. Butir ini **tidak menyinggung status centang**, justru supaya `backenddev:analyst` dapat menjalankannya ulang sesudah transisi eskalasi menulis ulang ledger, `lane:`, dan pasangan `(risk, chain)` sekaligus — mutasi paling rawan atas berkas ini, dan satu-satunya yang terjadi saat ledger sudah membawa centang.
   - **8b — Kondisi awal.** Seluruh hop `## Chain` belum tercentang. Berlaku hanya pada penulisan `TASK.md` baru oleh `task`; dilewati pada tiap pemeriksaan ulang sesudah hop mana pun tuntas.

9. **Kecukupan akar**: tiap `SC-{n}` menamai permukaan yang disebut `request` atau terbukti di `evidence` — endpoint, modul, aturan, status, atau artefak. Butir yang memperkenalkan permukaan di luar keduanya adalah kegagalan: hapus butirnya, dilarang dicarikan akar susulan. Jumlah butir dinilai dari cakupan, bukan dari plafon — rangkaian yang sudah menutup seluruh permukaan yang diminta lalu ditambah butir demi mendekati angka 7 gagal di butir ini, sekalipun tiap butirnya lolos butir 2–4.

Hasilnya dilaporkan sebagai satu baris per butir (`butir <n>: lolos` atau `butir <n>: gagal — <rincian>`, butir 8 dua baris untuk 8a dan 8b), dan commit Fase 5 dilarang berangkat sebelum kesembilannya lolos.

______________________________________________________________________

## 3. Contoh Terisi — `orders-api` (tidak tersalin ke artefak)

````markdown
---
status: ACTIVE
chain: PRD_BRIEF
lane: PRD_CONVERSION
risk: MAJOR
created: 2026-09-05
---

# Order — pembatalan order berstatus PAID

## Chain

- [ ] PRD   — backenddev:system-analysis  → PRD.md
- [ ] BRIEF — backenddev:plan             → brief-*.md

## Description

Order berstatus `PAID` dapat dibatalkan pemilik toko lewat endpoint baru selama stoknya belum dikurangi. Saat ini `OrderService.Cancel` hanya menerima status `PENDING` (`internal/order/service.go:142`), dan transisi `PAID → CANCELLED` tidak terdaftar di `internal/order/state.go:27`.

## Success Criteria

- [ ] **SC-1**: `POST /orders/{id}/cancel` atas order `PAID` mengembalikan 200 dan status berubah `CANCELLED` — verifikasi: `TestCancelPaidOrder` hijau
- [ ] **SC-2**: order `PAID` yang stoknya sudah dikurangi ditolak 409 `ORDER_ALREADY_FULFILLED` — verifikasi: `TestCancelPaidOrder_Fulfilled` hijau
- [ ] **SC-3**: transisi `PAID → CANCELLED` terdaftar di state machine — verifikasi: diff `internal/order/state.go`

## Out of Scope

- Refund otomatis ke payment gateway — batas modul: `internal/payment/` tidak disentuh
- Pembatalan oleh pembeli — opsi yang ditolak pada klarifikasi gerbang
````

Pembanding butir yang **gugur** di self-test bagian 2: `- [ ] **SC-1**: order bisa dibatalkan — verifikasi: test` — tidak menamai permukaan (endpoint, status), dan alat ukurnya tidak menyebut test bernama. Butir `SC-1` di contoh lolos karena keduanya disebut.
