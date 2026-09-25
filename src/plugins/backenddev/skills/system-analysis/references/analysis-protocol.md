# Protokol analisis sistem — `system-analysis`

Bagian A dipakai Fase 1, bagian B Fase 4. Jalankan utuh.

## Bagian A — Pemetaan kode aktual (as-is)

Delegasikan pemetaan lebih dulu; sapuan main loop hanya sisa kuota ringan: maks 3 panggilan `Glob`+`Grep`, potongan baca ≤40 baris, nol berkas dibaca penuh.

**Pembacaan skema database — berjenjang, bukan nol mutlak.** Default tetap nol query. Fase 3 dan dimensi 1, 8, 9, dan 16 bagian B menuntut tipe kolom, nullability, constraint, dan daftar index; ketiganya wajib diambil dari **kode** lebih dulu — berkas migrasi, definisi entity/model, dan skema yang dicek toolchain. Larangan mutlak membuat sisanya hanya punya dua jalan keluar, dan keduanya lebih buruk daripada satu pembacaan read-only: tipe `integer NOT NULL` dan daftar index dikarang, atau kontrak dikunci di atas permukaan yang belum tertutup.

Naik ke pembacaan skema hanya bila fakta itu **tidak terbukti dari kode**, dan di bawah batas berikut:

- **Read-only mutlak.** Nol `INSERT`/`UPDATE`/`DELETE`, nol DDL, nol migrasi dijalankan. Yang sah hanya introspeksi skema dan pembacaan agregat (`describe`, daftar index, `COUNT`/distribusi nilai untuk dimensi 8).
- **Terbatas pada permukaan Fase 1.** Tabel di luar permukaan yang sudah terpetakan tidak disentuh.
- **Kuota 5 panggilan per taskdir**, dihitung bersama, bukan per dimensi.
- **Jalur perolehan dicatat.** Tiap fakta hasil pembacaan skema memikul penanda sumbernya di kolom `Bukti` `## Impact map` atau di kolom tipe `## API contract` — mis. `skema: stock_cache.qty integer NOT NULL`. Fakta tanpa penanda dianggap bersumber kode dan harus punya `file:baris`.
- **Tanpa akses skema**, fakta itu turun jadi entri `## Open questions` berlabel `sementara dipakai:` beserta nilai yang diasumsikan. Ia **tidak** dikarang sebagai fakta, dan **tidak** pula membuat Fase 3 dikunci seolah tertutup.

**Tahap 0 — panen laci lebih dulu.** Sebelum satu dispatch pun berangkat, baca `{taskdir}/.explore/gate-*.md`: gerbang `backenddev:tech-lead` sudah mendispatch `code-explorer` di Fase 1-nya dan menyalin laporannya ke laci taskdir (`tech-lead/SKILL.md` Fase 3 butir 1). Petakan tiap permukaan wajib (a)–(d) di bawah terhadap isi laporan itu, lalu **dispatch Profil S hanya untuk permukaan yang belum tertutup**.

Tanpa tahap ini Profil S rutin membuktikan ulang seluruh fakta yang sudah dibuktikan gerbang — dua dispatch berkedalaman `menyeluruh` atas permukaan yang sama, dan laporan keduanya berakhir menyatakan sendiri bahwa tidak ada selisih. Laporan gerbang berkedalaman `ringkas` dan tidak memuat `### Error Surface`, sehingga ia jarang menutup keempat permukaan sendirian — yang dipangkas adalah pengulangannya, bukan Profil S-nya. Catat di laporan penutup permukaan mana yang tertutup laci gerbang dan mana yang menuntut dispatch baru.

**Predikat dispatch wajib** (tanpa sapuan pendahulu, sesudah Tahap 0): permukaan melintasi lebih dari satu layer atau modul; menyentuh mirrored path menurut `## Navigation recipes` adapter; atau kuota sapuan habis sebelum permukaan terpetakan.

Muat `dispatcher/explorer-surface.md` (**Profil S**), hidrasi slot `objective`, `permukaan`, `taskdir`, dan `slug` — plus `konteks_diketahui` dan `batas_cakupan` bila tersedia — lalu dispatch `code-explorer` langsung, tanpa skill pembungkus, dengan blok `Format laporan` Profil S ikut berangkat utuh. Laporannya mendarat di `{taskdir}/.explore/{slug}.md` sekaligus kembali ke context. Pointer `file:line` laporannya adalah bukti as-is; dilarang membaca ulang berkas yang sudah diringkas explorer. Balikan `confidence: low` atau format rusak: pertajam `objective` ke simbol konkret, ulangi maks sekali dengan slug baru, lalu turun ke sapuan manual dan laporkan penyimpangannya. Pemetaan balikan selengkapnya ada di `### Penanganan Balikan` template itu.

**Empat permukaan wajib.** (a) Modul dan batas namespace target sesuai `## Module structure` profil. (b) Model persistensi (`## Layer taxonomy` adapter), endpoint, enum status, dan repositori — field dan tipenya apa adanya sebagai baseline aditif vs breaking. (c) Deklarasi otorisasi dan handler error terpusat (`## API surface` adapter), **beserta literal pesan tiap cabang error apa adanya** — laporan Profil S menyetorkannya di `### Error Surface`. Kolom `Pesan` tabel `## Error` PRD mengikat string itu sebagai kontrak yang dibaca konsumen, sementara guardrail **NOL SENTUHAN KODE** melarang skill ini membacanya sendiri dari berkas sumber; seksi itulah satu-satunya jalur perolehannya. Literal yang tidak sampai: dispatch ulang sekali dengan `objective` menyebut handler-nya; tetap absen → kolom `Pesan` berbunyi `<belum terbukti>` dan naik ke `## Open questions`, tidak pernah ditebak dari nama kondisinya. (d) Mirrored path: konsumer async atas simbol sama.

**Blast-sweep sebelum Fase 4.** Begitu simbol berubah teridentifikasi, sapukan lima jalur rawan bocor (dimensi 2, 4, 11, 13, 16) lewat tepat satu dispatch `dispatcher/explorer-blast.md` (**Profil B**, dimuat baru di titik ini): hidrasi `simbol_berubah`, `daftar_dimensi`, dan `taskdir`, dan salin nama kelima dimensi apa adanya dari bagian B karena subagent tidak membaca berkas ini. Blok `Format laporan` Profil B ikut berangkat utuh — kerangkanya berbeda dari Profil S dan hanya ia yang memuat `### Blast Map`. Baris `### Blast Map` berstatus `disisir bersih` **beserta kolom `Disisir` berangka bukan nol** adalah vonis sah `Tidak terdampak`. Berstatus `belum disisir`, berangka nol, tanpa angka, atau dimensi yang tidak muncul di tabel — ketiganya bukan, dan dilarang divonis aman. Angka itu yang membedakan "sudah dibuka dan bersih" dari "tidak ketemu di pencarian pertama"; tanpanya laporan dapat berbunyi `confidence: high` dan `Gaps: Nihil` sambil melewatkan berkas test yang endpoint-nya hanya muncul sebagai string literal di dalam array. Gagal dua kali: turun ke sapuan manual di sisa kuota dan laporkan penyimpangannya.

## Bagian B — 16 dimensi analisis dampak

**Aturan pengisian.** `## Impact map` memuat tepat 16 baris berurutan bervonis `terdampak` atau `tidak relevan`; dilarang menghapus baris. Baris `terdampak` memikul bukti simbol di kolom `Bukti` dan nomor baris `## Task breakdown` pendaratnya di `Mendarat di`. Baris 2, 4, 11, 13, dan 16 diisi payload blast-sweep; vonis `tidak relevan` di kelimanya wajib berjejak sapuan konkret, dilarang prosa tanpa simbol. Dimensi 3 juga mendarat di `## Status lifecycle`, 5 di `## Permission & scope`, 8–9 di `## Migration requirements`.

| # | Dimensi | Yang disapu dan dicatat |
|---|---|---|
| 1 | Persistensi | Field yang ditambah, diubah tipe, atau dihapus: entity, kolom, tipe lama -> baru. Input dimensi 8 dan 9 |
| 2 | Konsumen endpoint | Pemanggil endpoint yang disentuh (mobile, SPA, service internal, integrasi eksternal) dan pemiliknya; tak teridentifikasi: tanyakan di Fase 2, sisanya jadi asumsi `## Open questions`. Dilarang mengasumsikan nihil konsumen |
| 3 | Lifecycle | Transisi ditambah, dihapus, atau berubah prasyarat, plus efeknya ke query filter, dashboard, dan laporan berbasis enum status |
| 4 | Mirrored path | Tiap perubahan alur sinkron: queue listener, job terjadwal, broadcast WebSocket, audit changelog (`## Invariants` profil / `## Navigation recipes` adapter). Yang tertinggal = cacat arsitektur |
| 5 | Permission & scope | Role/permission tiap endpoint atau logic baru, dan apakah scoping store/tenant otomatis melindunginya; wajib berbukti filter/interceptor |
| 6 | Cache | Cache repo termasuk in-memory yang membaca entitas berubah: nama, key pattern, titik evict |
| 7 | Integrasi eksternal | Payload atau event ke webhook, payment gateway, API partner, atau ekspor batch: kontrak eksternal dan breaking notice |
| 8 | Backfill | Dari migration dan constraint kolom wajib-isi: usulan default bisnis. Volume data tak terverifikasi dari kode — naikkan ke `## Open questions` |
| 9 | Migration & deploy | Berkas migrasi menurut tool di profil (dari dimensi 1 dan 8). Tidak backward-compatible: Expand-Contract (kode toleran -> migrasi -> kode baru -> hapus kolom lama) |
| 10 | Feature flag | Perubahan berisiko tinggi: flag baru, titik pengecekan, default saat flag mati (wajib perilaku lama yang aman), plus baris pemasangan |
| 11 | Test yang pecah | **Glob dulu, Grep menyusul.** Kumpulkan seluruh berkas test di letak baris `test:` `.claude/profile/backenddev/code-conventions.md` (atau baris `Test` `## Layer taxonomy` adapter) dengan `Glob`, baru `Grep` di dalamnya atas (a) nama simbol berubah, **dan** (b) **literal path endpoint sebagai string** — termasuk kemunculannya di dalam array, tabel kasus, atau test terparametrisasi. Vonis `tidak relevan` wajib menyebut **jumlah berkas test yang disisir**; vonis tanpa angka itu ditolak. `Grep` simbol saja meleset pada endpoint yang hanya muncul sebagai string literal di dalam `for uri in [...]`, dan berkas semacam itu baru ketahuan sebagai test merah sesudah seluruh brief mendarat |
| 12 | Konfigurasi | Properti baru di semua berkas konfigurasi runtime `## Detection` adapter termasuk varian per environment: nama, default aman, secret manual |
| 13 | Enum & serialisasi | Enum baru, perubahan tipe, atau rename field JSON memecah deserialization konsumen lama dan pesan di broker: catat periode transisi memakai alias field stack |
| 14 | Dokumentasi API | Anotasi atau spesifikasi OpenAPI pendeskripsi endpoint wajib selaras kontrak baru; letak dari `## API surface` adapter |
| 15 | Pesan error | Pemetaan pesan tiap kondisi error `## API contract` dan lokasi definisinya (konstanta, berkas messages, enum exception) |
| 16 | Query & indexing | Kolom baru pada `WHERE`, `JOIN`, `ORDER BY` yang mungkin butuh indeks, dan relasi baru per baris berisiko N+1 — mitigasi strategi fetch `## Failure signatures` adapter |
