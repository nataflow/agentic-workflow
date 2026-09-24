# Template Prompt Reviewer Dokumen Brief

Gunakan template ini saat mendispatch subagent reviewer dokumen brief (`brief-reviewer`).

**Tujuan:** Mengambil sudut pandang helikopter (helicopter view) dengan memverifikasi seluruh dokumen brief (`brief-*.md`) selaras secara utuh terhadap `TASK.md`, `BRD.md`, dan `PRD.md`, lengkap, konsisten, deterministik, mematuhi kaidah slicing & zero-tolerance red flags, serta siap untuk dieksekusi oleh `code-implementor`.

**Dispatch setelah:** Seluruh rangkaian brief selesai ditulis ke `backenddev/docs/<taskdir>/brief-*.md` dan `scripts/validate_briefs.py` memvonis `PASS`.

```markdown
Review dokumen brief berikut: `{target}`

Konteks tugas:
- Taskdir: `{taskdir}`
- Target: `{target}`
- Ronde: `{ronde}` dari maks 2
- Chain: `{chain}` — dokumen hulu di luar chain ini memang tidak ada dan ketiadaannya sah
- Dokumen hulu wajib dibaca (Helicopter View):
  - TASK acuan: `{taskdir}/TASK.md` (wajib baca jika tersedia)
  - BRD acuan: `{taskdir}/BRD.md` (wajib baca jika tersedia)
  - PRD acuan: `{taskdir}/PRD.md` (wajib baca jika tersedia)
  - RCA acuan: `{taskdir}/RCA.md` (baca jika jalur RCA)
- Previous report: `{previous_report}` (baca jika ronde > 1)

Predikat mekanis sudah dijamin `validate_briefs.py` sebelum dispatch ini berangkat:
kelengkapan sepuluh seksi dan frontmatter, sapuan lima placeholder terlarang, nol
verifikasi, langit-langit slicing, resolusi anchor, realitas berkas test, enum `risk:`
beserta plafonnya, DAG lintas-brief, cakupan `Covers:`/`Fulfills:` atas nomor, dan
pendaratan migrasi. Jangan menghitung ulang satu pun di antaranya. Nilai yang menuntut
penilaian: keselarasan invariant `BR-{n}`, pendaratan empat pilar kontrak PRD, kecukupan
`## Steps` sebagai perintah eksekusi, dan asumsi aktif yang membentuk langkah.
```

**Ronde > 1** — `{target}` menyempit ke `{brief_berubah}`, dan `{previous_report}` adalah daftar temuan yang wajib dipastikan tertutup. Brief di luar daftar itu byte-identik dengan yang sudah kau nilai pada ronde sebelumnya; menilainya ulang tidak menambah informasi apa pun, sementara regresi mekanis atas seluruh batch tetap dijaring `validate_briefs.py` yang berjalan penuh. Temuan baru atas seksi yang **tidak berubah** ditulis `ADVISORY`, bukan `BLOCKER` — ronde kedua ada untuk menutup temuan ronde pertama, bukan untuk membuka putaran temuan baru yang lahir dari perbaikannya sendiri.

### Slot Hidrasi

| Slot | Sumber Pengisian | Batasan |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` skill pemanggil | Path taskdir aktif |
| `{target}` | `{taskdir}/brief-*.md` pada ronde 1; `{brief_berubah}` pada ronde 2 | **Wajib terisi.** Ronde 1 menilai seluruh batch sekaligus dan dilarang dipecah per berkas |
| `{ronde}` | Keluaran `scripts/validate_briefs.py --review-state` | `1` pada dispatch pertama, `2` pada dispatch ulang. Ronde 3 dilarang berangkat, dan hitungannya berlaku **per taskdir** — bukan per invokasi `plan`, karena ia dimateraikan ke laci, bukan diingat main loop |
| `{brief_berubah}` | Baris `brief berubah sejak ronde terakhir` keluaran `--review-state` | Diisi hanya pada ronde > 1. Daftar kosong berarti tidak ada yang perlu dinilai ulang: tutup self-review tanpa dispatch |
| `{chain}` | Parameter `chain` skill pemanggil, yang diteruskan `backenddev:analyst` dari `TASK.md` | **Wajib terisi.** Kosong → batalkan dispatch dan minta nilainya ke `backenddev:analyst`. Dilarang menyimpulkannya dari artefak yang ada di disk: kesimpulan itu membuat rantai putus terbaca sebagai chain pendek yang sah |
| `{previous_report}` | Laporan reviewer ronde sebelumnya | Diisi hanya pada ronde > 1; ronde 2 tanpa slot ini dilarang berangkat |

**Reviewer mengembalikan:** Laporan `## Brief Review` dengan status `Approved` atau `Issues Found`. Balikan itu diteruskan pemanggil **apa adanya** ke laporan penutupnya; memparafrase atau menyaringnya menghapus predikat masuk gerbang hilir.
