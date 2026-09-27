# Template Prompt Reviewer Dokumen PRD

Gunakan template ini saat mendispatch subagent reviewer dokumen PRD (`prd-reviewer`).

**Tujuan:** Memverifikasi dokumen PRD lengkap, konsisten, deterministik, menutup 4 pilar kontrak dan 16 dimensi impact map, serta siap untuk dekomposisi brief (`plan`).

**Dispatch setelah:** Dokumen PRD selesai ditulis ke `backenddev/docs/<taskdir>/PRD.md`.

```markdown
Review dokumen PRD berikut: `{taskdir}/PRD.md`

Konteks tugas:
- Taskdir: `{taskdir}`
- Target: `{taskdir}/PRD.md`
- Chain: `{chain}` — dokumen hulu di luar chain ini memang tidak ada dan ketiadaannya sah
- BRD acuan: `{taskdir}/BRD.md` (baca jika tersedia)
- TASK acuan: `{taskdir}/TASK.md` (baca jika tersedia)
- Ronde: `{ronde}` dari maks 2
- Previous report: `{previous_report}` (baca jika ronde > 1)

Ronde > 1 — `{previous_report}` adalah daftar temuan yang wajib dipastikan tertutup, **bukan** batas lingkup pemeriksaan. Baca ulang `{taskdir}/PRD.md` dari disk (isinya sudah berubah sejak ronde lalu), lalu jalankan kembali **seluruh** butir `## Fokus Pemeriksaan` atas versi baru itu. Kalimat yang lahir dari perbaikan belum pernah dinilai siapa pun: baris tabel `Error` baru bisa belum bertagih AC, entri `BR-DISANGGAH:` baru bisa melampaui plafon tiga entri `## Open questions`, pendarat `## Task breakdown` baru bisa membocorkan path `src/` atau menyentuh `## Out of scope`, dan AC yang dihapus bisa membolongi penyandingan `EC-{n}`/`SC-{n}`. Temuan baru atas butir yang ronde sebelumnya loloskan adalah `Issues Found` yang sah — yang berubah dokumennya, bukan penilaiannya.
```

### Slot Hidrasi

| Slot | Sumber Pengisian | Batasan |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` skill pemanggil | Path taskdir aktif |
| `{chain}` | Parameter `chain` skill pemanggil, yang diteruskan `backend:analyst` dari `TASK.md` | **Wajib terisi.** Kosong → batalkan dispatch dan minta nilainya ke `backend:analyst`. Dilarang menyimpulkannya dari artefak yang ada di disk: kesimpulan itu membuat rantai putus terbaca sebagai chain pendek yang sah |
| `{ronde}` | Nomor ronde self-review skill pemanggil | `1` pada dispatch pertama, `2` pada dispatch ulang. Ronde 3 dilarang berangkat |
| `{previous_report}` | Laporan reviewer ronde sebelumnya | Diisi hanya pada ronde > 1; ronde 2 tanpa slot ini dilarang berangkat |

**Reviewer mengembalikan:** Laporan `## PRD Review` dengan status `Approved` atau `Issues Found`. Balikan itu diteruskan pemanggil **apa adanya** ke laporan penutupnya; memparafrase atau menyaringnya menghapus predikat masuk gerbang hilir.
