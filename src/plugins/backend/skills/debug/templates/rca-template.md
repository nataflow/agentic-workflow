---
doc_type: RCA
status: ROOT_CAUSE_CONFIRMED | INCONCLUSIVE
taskdir: backenddev/docs/<YYMMDDhhmm>-<slug>/
reproduksi: terverifikasi | tidak tersedia
siklus_hipotesis: <n>/3
---

# RCA — <ringkas gejala dalam satu frasa>

## Symptom

- **Exception / status**: `<ExceptionClass>` atau `<HTTP status>`
- **Frame terdalam `root_namespace`**: `<file>:<line>` — `<method>`
- **Kondisi kemunculan**: <kapan, request/job apa, sejak kapan>
- **Cakupan dampak**: <satu user | satu endpoint | seluruh instans>
- **Sumber gejala**: <stacktrace ditempel user | test merah `<NamaTest>` | log>

## Reproduksi

**Status**: terverifikasi user | tidak tersedia

1. <langkah arrange — kondisi data atau konfigurasi awal>
2. <aksi — perintah test, request HTTP + payload, atau trigger job>
3. <observasi — gejala yang muncul, verbatim>

Jika status `tidak tersedia`: tulis alasannya di sini (data produksi, kondisi balapan, lingkungan tidak tersedia) dan sebutkan bukti pengganti yang dipakai Fase 3.

## Rantai kausal

Urutan sebab-akibat dari pemicu sampai gejala. Tiap mata rantai wajib menyebut `file:line`.

1. `<file>:<line>` — <apa yang terjadi di sini>
2. `<file>:<line>` — <konsekuensi langsung dari langkah 1>
3. `<file>:<line>` — <konsekuensi berikutnya>
4. `<file>:<line>` — <titik gejala muncul>

**Root cause**: <satu proposisi yang dapat salah, menyebut `file:line`>

**Bukti pendukung**:

- `<file>:<line>` — <kutipan atau kondisi kode yang menegaskan>
- <keluaran test yang benar-benar dijalankan, atau log yang ditempel user>

**Inferensi (bukan fakta terverifikasi)**: <daftar langkah yang disimpulkan tanpa bukti langsung, atau `-`>

## Hipotesis terfalsifikasi

Minimal satu entri wajib terisi sebelum status `ROOT_CAUSE_CONFIRMED` ditulis.

| # | Hipotesis | Bukti pembalik | Sumber bukti |
| --- | --- | --- | --- |
| H1 | <proposisi yang diuji> | <fakta yang membatalkannya> | `<file>:<line>` \| test \| log |
| H2 | <proposisi yang diuji> | <fakta yang membatalkannya> | `<file>:<line>` \| test \| log |

Jika status `INCONCLUSIVE`: tabel memuat ketiga siklus, dan seksi `## Bukti tambahan dibutuhkan` di bawah wajib terisi.

## Blast radius

- **Pemanggil lain pada lokasi penyebab**: `<file>:<line>` — <dampaknya>
- **Endpoint / job terdampak**: `<METHOD> <path>` atau `<NamaScheduler>`
- **Data yang mungkin sudah rusak**: <tabel/kolom + kriteria baris terdampak, atau `tidak ada`>
- **Defect serupa di lokasi lain**: `<file>:<line>` atau `tidak ditemukan`

## Arah perbaikan

Masukan untuk `## File scope` brief `plan`. Daftar berkas kandidat, bukan patch.

| Berkas | Aksi | Sifat perubahan |
| --- | --- | --- |
| `<path>` | modify | <apa yang perlu berubah, tanpa kode pengganti> |
| `<path>` | create | <peran berkas baru> |

**Batasan yang wajib dipatuhi pelaksana**: <invariant profil, kontrak API, atau pattern eksisting yang tidak boleh dilanggar>

## Regression guard

Spesifikasi test, bukan berkas test. Assertion wajib gagal pada kode saat ini.

- **Kelas test**: `<NamaTest>`
- **Tier & command**: <tier sesuai `## Commands` backend:profile + command-nya>
- **Arrange**: <kondisi data/mock awal>
- **Act**: <aksi yang dipanggil>
- **Assert**: <assertion spesifik yang gagal sebelum fix dan lulus sesudahnya>

Jika tidak dapat digerbangi test: tulis `tidak dapat digerbangi test` beserta alasannya dan mekanisme pencegahan pengganti (validasi startup, konfigurasi terkunci, atau alarm).

## Bukti tambahan dibutuhkan

Ditulis hanya bila status `INCONCLUSIVE`; hapus seksi ini bila root cause terkonfirmasi.

- <log, dump, atau konfigurasi yang perlu ditempel user>
- <akses atau lingkungan yang perlu disediakan>

<!-- Contoh terisi (dipangkas) — hapus seluruh blok komentar ini sebelum RCA.md ditulis ke taskdir.

# RCA — order PAID dibatalkan tanpa mengembalikan stok

## Symptom
- Exception / status: `TestCancelPaidOrder_StockRestored` merah — expected stock 10, got 9
- Frame terdalam root_namespace: `internal/order/service.go:158` — `Cancel`
- Kondisi kemunculan: setiap pembatalan order PAID sejak commit a1b2c3d
- Cakupan dampak: seluruh instans
- Sumber gejala: test merah

## Reproduksi
Status: terverifikasi user
1. Order PAID dengan 1 item qty 1, stok gudang 9
2. `go test ./internal/order -run TestCancelPaidOrder_StockRestored`
3. assertion stok gagal: expected 10, got 9

## Rantai kausal
1. `internal/order/service.go:150` — `Cancel` memanggil `state.Transition(PAID, CANCELLED)`
2. `internal/order/service.go:158` — cabang pengembalian stok hanya dijalankan bila status awal `PENDING`
3. `internal/order/service.go:171` — order tersimpan `CANCELLED` tanpa `stock.Restore`

Root cause: kondisi `if prev == PENDING` di `internal/order/service.go:158` tidak mencakup `PAID`, sehingga `stock.Restore` tidak dipanggil.

## Hipotesis terfalsifikasi
| # | Hipotesis | Bukti pembalik | Sumber bukti |
| H1 | `stock.Restore` gagal diam-diam | `Restore` tidak pernah dipanggil menurut mock | test |

## Arah perbaikan
| `internal/order/service.go` | modify | perluas kondisi pengembalian stok ke status `PAID` |

## Regression guard
- Kelas test: `TestCancelPaidOrder_StockRestored`
- Assert: stok gudang kembali ke nilai sebelum order, gagal pada kode saat ini
-->
