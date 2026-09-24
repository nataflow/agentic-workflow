# {{JUDUL_H1_TASK}} — Report

## Ringkasan
{{SATU_KALIMAT_APA_YANG_DIKERJAKAN_ALASAN_TERSIRAT}}

## Perubahan
- {{PERUBAHAN_PERILAKU_1}} ({{MODUL_ATAU_BERKAS_1}})
- {{PERUBAHAN_PERILAKU_2}} ({{MODUL_ATAU_BERKAS_2}})

## Catatan
{{ISU_TERSISA_REVIEW_ATAU_PENYIMPANGAN_SCOPE}}

<!--
Aturan pengisian:
- JUDUL_H1_TASK  : salin apa adanya dari H1 {taskdir}/TASK.md, jangan diturunkan dari slug.
- Ringkasan      : tepat satu kalimat; dua kalimat atau lebih ditolak.
- Perubahan      : 2-7 butir, tiap butir berakar pada berkas di diff merge-base..HEAD.
- Catatan        : hapus heading ini seluruhnya bila tidak ada isu; dilarang diisi "-" atau "N/A".
- Hapus seluruh blok komentar ini sebelum berkas ditulis ke taskdir.

Contoh terisi (orders-api):

# Order — pembatalan order berstatus PAID — Report

## Ringkasan
Order PAID kini dapat dibatalkan pemilik toko selama stoknya belum dikurangi.

## Perubahan
- Transisi PAID → CANCELLED terdaftar di state machine (internal/order/state.go)
- POST /orders/{id}/cancel menerima order PAID dan menolak 409 bila stok sudah dikurangi (internal/order/handler.go, internal/order/service.go)
- Test TestCancelPaidOrder dan TestCancelPaidOrder_Fulfilled ditambahkan (internal/order/service_test.go)

## Catatan
REVIEW.md P3: nama variabel `st` di internal/order/service.go:150 menyimpang dari konvensi; tidak diperbaiki di rantai ini.
-->
