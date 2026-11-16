# Migrasi `frontend` v0.20.0 → v0.21.0

Langkah 37: laporan unit lewat balikan. Claude Code menolak subagent menulis berkas laporan ("Subagents should
return findings as text, not write report files"), sehingga di 0.20.0 setiap unit berhenti di baris "laporan absen +
tree kotor" matriks bukti disk dan `architect` bertanya ke user per unit. Tidak ada format dokumen yang wajib
dimigrasi; taskdir yang sedang berjalan dapat dilanjutkan apa adanya.

## Yang berubah

- **Implementor tidak menulis berkas laporan.** `code-implementor` mengembalikan laporan unit (bentuk `Format
  laporan` yang sama) sebagai balikan. Slot `report_path` dicabut dari dispatcher, dan hook menolak tulisan
  implementor ke `report-NN.md`.
- **`architect` menyimpan laporan unit tak bersih.** Balikan disalin persis ke `report-<NN>.md` (+ `## Triase`) hanya
  bila unit `FAILED`, turun ke `BLOCKED`, ber-`## Triase`, atau `## Out of Scope / Mismatch` tidak kosong. Unit bersih
  tidak meninggalkan berkas laporan; buktinya commit unit.
- **Prasyarat `architect`.** Check 4 tidak lagi memperingatkan brief `DONE` tanpa `report-NN.md`. Fase `TERPUTUS`
  divonis dari tree saja: tree bersih → brief kembali `READY`, laporan sisa dihapus, lalu dispatch ulang.
- **Reviewer penutup** membaca butir `DITUNDA` dari seksi 5 brief `DONE`, bukan dari laporan unit.
- **Laci explorer** tidak pernah bernama `report*`; slug yang berawalan itu diberi awalan `telusur-`.

## Langkah migrasi

Tidak ada yang wajib. Taskdir lama yang punya `report-NN.md` untuk setiap unit tetap terbaca oleh semua gerbang.
Taskdir yang berhenti di tengah eksekusi karena laporan absen: jalankan `/frontend:lead lanjutkan <taskdir>` —
unit yang kodenya sudah di tree dan statusnya `DONE` divonis fase `TERPUTUS` dari tree; unit yang masih `READY`
dengan tree kotor tetap dieskalasi ke user seperti sebelumnya.
