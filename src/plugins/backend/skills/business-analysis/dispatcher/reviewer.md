# Template Prompt Reviewer Dokumen BRD

Gunakan template ini saat mendispatch subagent reviewer dokumen BRD (`brd-reviewer`).

**Tujuan:** Memverifikasi dokumen BRD lengkap, konsisten, deterministik, dan siap untuk perancangan analisis sistem (PRD).

**Dispatch setelah:** Dokumen BRD selesai ditulis ke `backenddev/docs/<taskdir>/BRD.md`.

```markdown
Review dokumen BRD berikut: `{taskdir}/BRD.md`

Konteks tugas:
- Taskdir: `{taskdir}`
- Target: `{taskdir}/BRD.md`
- Chain: `{chain}` — dokumen hulu di luar chain ini memang tidak ada dan ketiadaannya sah
- TASK acuan: `{taskdir}/TASK.md` (baca jika tersedia)
- Ronde: `{ronde}` dari maks 2
- Previous report: `{previous_report}` (baca jika ronde > 1)

Ronde > 1 — `{previous_report}` adalah daftar temuan yang wajib dipastikan tertutup, **bukan** batas lingkup pemeriksaan. Baca ulang `{taskdir}/BRD.md` dari disk (isinya sudah berubah sejak ronde lalu), lalu jalankan kembali **seluruh** butir `## Fokus Pemeriksaan` atas versi baru itu. Kalimat yang lahir dari perbaikan belum pernah dinilai siapa pun: `EC-{n}` baru bisa tak berkategori atau membatalkan baris `Kategori nihil:`, penomoran bisa bolong karena entri dihapus alih-alih diperbaiki, aktor hasil pemecahan bisa membuat `BR-{n}` lama ambigu, dan jawaban `## Open questions` bisa menyeret desain teknis masuk. Temuan baru atas butir yang ronde sebelumnya loloskan adalah `Issues Found` yang sah — yang berubah dokumennya, bukan penilaiannya.
```

### Slot Hidrasi

| Slot | Sumber Pengisian | Batasan |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` skill pemanggil | Path taskdir aktif |
| `{chain}` | Parameter `chain` skill pemanggil, yang diteruskan `backend:analyst` dari `TASK.md` | **Wajib terisi.** Kosong → batalkan dispatch dan minta nilainya ke `backend:analyst`. Dilarang menyimpulkannya dari artefak yang ada di disk: kesimpulan itu membuat rantai putus terbaca sebagai chain pendek yang sah |
| `{ronde}` | Nomor ronde self-review skill pemanggil | `1` pada dispatch pertama, `2` pada dispatch ulang. Ronde 3 dilarang berangkat |
| `{previous_report}` | Laporan reviewer ronde sebelumnya | Diisi hanya pada ronde > 1; ronde 2 tanpa slot ini dilarang berangkat |

**Reviewer mengembalikan:** Laporan `## BRD Review` dengan status `Approved` atau `Issues Found`. Balikan itu diteruskan pemanggil **apa adanya** ke laporan penutupnya; memparafrase atau menyaringnya menghapus predikat masuk gerbang hilir.
