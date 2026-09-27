# REPORT Template — `report`

Rumah kanonik bentuk `frontenddev/docs/<YYMMDDhhmm>-<slug>/REPORT.md`, dipakai `SKILL.md` Phase 4. Bagian 1 kerangka, bagian 2 aturan yang ditagih `scripts/validate_report.py`, bagian 3 contoh terisi yang tidak tersalin ke artefak. Bentuknya sengaja sejajar dengan `REPORT.md` milik `backend` — satu H1, `## Ringkasan`, `## Perubahan`, dan `## Catatan` opsional — supaya satu fitur full-stack punya dua laporan penutup yang dapat disandingkan. Yang berbeda hanya sumber diff (rentang commit rantai sejak akar, bukan merge-base) dan status `PERLU VERIFIKASI MANUAL` untuk butir `SC-{n}` ber-alat-ukur `QA manual:`.

______________________________________________________________________

## 1. Template Kanonik REPORT.md

````markdown
# <H1 TASK.md apa adanya> — Report

## Ringkasan
<Tepat satu kalimat: apa yang dikerjakan, alasannya tersirat di kalimat yang sama.>

## Perubahan
- <perubahan perilaku> (<berkas atau direktori modul>)
- <perubahan perilaku> (<berkas atau direktori modul>)

## Catatan
- <SC-{n} — PERLU VERIFIKASI MANUAL: langkah QA dari REVIEW.md/TASK.md>
- <temuan REVIEW.md yang belum dituntaskan beserta ID-nya>
- <unit NN BLOCKED → remedi brief-MM, dari ## Triase report-NN.md>
````

______________________________________________________________________

## 2. Aturan Validasi

Ditagih `validate_report.py`; `FAIL` menahan commit:

- **H1** — salin H1 `TASK.md` apa adanya, lalu tambahkan ` — Report`. Dilarang diturunkan dari slug.
- **Ringkasan** — tepat satu kalimat hasil aktual, minimal 5 kata (kode inline dihitung satu kata); `Selesai.`/`Done.`/`Beres.` ditolak.
- **Perubahan** — 1–7 butir, masing-masing menyebut perubahan perilaku (minimal 3 kata) dan ditutup kurung berisi berkas atau direktori modul yang muncul di berkas rantai (`SKILL.md` Phase 2); direktori tingkat atas tanpa `/` (mis. `src`) terlalu lebar dan ditolak. Tiap berkas rantai wajib tercakup satu butir, langsung atau lewat direktori induknya. Rujukan di dalam kurung dipisah koma; kurung penutup yang dibaca adalah kurung seimbang terakhir di ujung baris, sehingga route group (`app/(tabs)/index.tsx`, `src/routes/(app)/+page.svelte`) dan nama berkas non-ASCII ditulis apa adanya.
- **Catatan** — hanya dari tiga sumber: tiap `SC-{n}` yang `REVIEW.md` vonis `PERLU VERIFIKASI MANUAL` (wajib hadir, ditagih skrip), temuan `REVIEW.md` yang belum dituntaskan (tiap `### [Px-n]` ber-`> Status: PLANNED|DEFERRED` wajib disebut ID-nya, ditagih skrip), dan penyimpangan di `## Triase` `report-<NN>.md`. Ketiganya kosong → hapus heading beserta isinya; dilarang diisi `-`, `N/A`, atau kalimat penyangkalan.
- **Nol placeholder** — tidak ada slot `<...>`, `TBD`/`TODO`, `{{`, atau komentar HTML tersisa. Pendeteksinya sama dengan validator gate lain: JSX (`<Skeleton />`), generik TS, dan operator perbandingan (`< 300 ms`) bukan slot.

______________________________________________________________________

## 3. Contoh Terisi — `order-tracking` (tidak tersalin ke artefak)

````markdown
# Order tracking — layar lacak pengiriman — Report

## Ringkasan
Pembeli kini dapat membuka layar lacak pengiriman dari detail pesanan dan melihat status kurir terakhir beserta penanganan gagal-muatnya.

## Perubahan
- Rute `/orders/:id/tracking` terdaftar dan tombol *Lacak* menavigasi ke sana (src/app/router.tsx, src/features/orders/OrderDetail.tsx)
- Layar tracking beserta Controller dan query status kurir ditambahkan (src/features/tracking/)
- Test navigasi dan kasus error layar tracking ditambahkan (src/features/orders/OrderDetail.test.tsx, src/features/tracking/TrackingScreen.test.tsx)

## Catatan
- SC-2 — PERLU VERIFIKASI MANUAL: buka `/orders/:id/tracking` untuk pesanan terkirim, amati baris status teratas dan jamnya
- REVIEW.md P3-1: skeleton tracking memakai spacing literal `12px` di src/features/tracking/TrackingScreen.tsx:40; tidak diperbaiki di rantai ini
````
