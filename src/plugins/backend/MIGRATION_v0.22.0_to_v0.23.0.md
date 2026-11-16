# Migrasi `backend` v0.22.0 → v0.23.0

Langkah 37: laporan unit lewat balikan. Claude Code menolak subagent menulis berkas laporan ("Subagents should
return findings as text, not write report files"), sehingga brief `BLOCKED` kehilangan `report-NN.md` — satu-satunya
jalur yang menulisnya. Tidak ada format dokumen yang wajib dimigrasi.

## Yang berubah

- **Badan laporan jalur gagal dibawa amplop.** `code-implementor` tidak menulis `report-NN.md`; amplop
  `## Implementor Report` jalur gagal memuat badan laporan utuh (frontmatter dan empat seksi yang sama) sesudah
  baris `Commit:`. Brief tetap ditandai `BLOCKED` dan commit penanda `wip(<domain>)` tetap dibuat implementor.
- **`architect` menyimpan laporan sebelum triase `BLOCKED`**, salinan persis badan amplop; amplop tanpa badan →
  laporan dari baris `Status`/`Cause`.
- **Lease implementor tanpa `report-NN.md`.** Hook kini menolak tulisan implementor ke berkas itu.
- **`render_prompt.py` menolak slot `slug` berawalan `report`** — nama itu menjadi nama berkas laporan explorer yang
  ditolak harness. Beri awalan `telusur-`.

## Langkah migrasi

Tidak ada. Isi dan letak `report-NN.md` tidak berubah, sehingga `tech-lead`, `analyst`, `plan`, dan sinkron nataflow
membacanya seperti sebelumnya.
