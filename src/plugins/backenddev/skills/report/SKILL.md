---
name: report
description: Dipanggil backenddev:architect sesudah REVIEW.md terbit dan seluruh brief tertutup - perumusan REPORT.md dari diff merge-base yang dipasangkan dengan Success Criteria TASK.md, dikunci satu commit sebelum rantai dinyatakan selesai
user-invocable: false
---

## THE IRON LAW

- Tulis `REPORT.md` hanya sesudah `REVIEW.md` terbit dan seluruh brief tertutup (`DONE`, atau `SUPERSEDED` yang bertaut ke pengganti) — rantai yang belum tuntas tidak punya hasil untuk dilaporkan.
- Setiap butir `## Perubahan` wajib berakar pada berkas yang muncul di diff merge-base; klaim tanpa berkas dibuang, bukan diloloskan.
- Skill ini melaporkan, bukan menilai — dilarang menerbitkan severity, verdict, atau temuan baru.
- Dilarang menyentuh `src/`, mengedit `TASK.md`, `REVIEW.md`, atau brief mana pun.
- Kunci berkas dalam satu commit path-eksplisit sebelum mengembalikan kendali ke gerbang.

## Precondition [REQUIRED]

1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/report/scripts/check_preconditions.py --taskdir <taskdir> [--base-branch <base_branch>]`.
2. Evaluasi output skrip secara deterministik:
   - `PASS` (7/7 checks): Lanjutkan ke perumusan laporan rantai dan commit REPORT.md.
   - `FAIL`: Hentikan eksekusi segera dan jalankan tindakan remediasi pada butir yang gagal (taskdir hilang → verifikasi inisialisasi taskdir; `TASK.md` hilang → kembalikan ke `backenddev:tech-lead` untuk backfill akar (`gate-lifecycle.md` bagian 1a), taskdir lama tanpa akar di luar cakupan; REVIEW.md belum ada → tuntaskan review via `architect`; brief belum tertutup → selesaikan brief lewat `architect`; REPORT.md sudah ada → minta otorisasi user; working tree kotor → bersihkan sebelum melanjutkan).

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — Path taskdir aktif berpola `backenddev/docs/<YYMMDDhhmm>-<slug>/`; path tak ditemukan ditolak.
- `base_branch` — string — default dari `.claude/profile/backenddev/index.json` — Branch pembanding merge-base; nilai yang tidak resolve ke ref git ditolak.

## Workflow

### Fase 0 — Verifikasi Prasyarat & Penolakan Dini

1. Jalankan skrip prasyarat `## Precondition` dan hentikan eksekusi segera bila hasilnya `FAIL`. Laporkan butir yang gagal beserta nilai terbacanya; dilarang menambal prasyarat yang hilang.
2. Baca `base_branch` dan `commit_convention` dari profil; catat keduanya untuk Fase 4.

### Fase 1 — Penyerapan Akar & Hasil Rantai

1. Baca H1 `{taskdir}/TASK.md` dan pakai apa adanya sebagai judul: `<H1 TASK.md> — Report`. Dilarang mengarang judul dari slug direktori.
2. Serap `## Description` sebagai konteks, lalu pasangkan tiap butir `## Success Criteria` dengan bukti pemenuhannya.
3. Baca `{taskdir}/REVIEW.md`; catat severity tertinggi dan daftar temuan yang belum dituntaskan.
4. Hentikan eksekusi segera jika severity tertinggi bernilai `P1` karena rantai bertemuan `P1` belum selesai. Kembalikan kendali ke `backenddev:tech-lead` untuk klasifikasi kerja lanjutan.

### Fase 2 — Derivasi Perubahan dari Diff Mendarat

1. Jalankan `git diff --stat $(git merge-base {base_branch} HEAD)..HEAD`. Daftar berkas hasil perintah ini adalah satu-satunya sumber sah butir `## Perubahan`.
2. Kelompokkan berkas per unit kerja atau modul, bukan per berkas. Tulis 2–7 butir berbentuk `- <perubahan perilaku> (<modul atau berkas>)`.
3. Tambahkan butir baru jika satu berkas di diff tidak terjelaskan oleh butir mana pun; jangan tinggalkan berkas menggantung.
4. Hentikan eksekusi segera jika diff kosong. Laporkan bahwa tidak ada perubahan mendarat di atas `base_branch`. Dilarang menulis report atas rantai tanpa diff.
5. Dilarang menyalin subjek commit sebagai butir; butir menyatakan perubahan perilaku, bukan riwayat git.

### Fase 3 — Perumusan Ringkasan & Catatan

1. Rumuskan `## Ringkasan` sebagai tepat satu kalimat yang menyatakan apa yang dikerjakan dengan alasannya tersirat di kalimat yang sama. Tolak dua kalimat atau lebih di fase ini.
2. Tulis ulang dari hasil Fase 2 bila ringkasan hanya mengulang `## Description` TASK.md; report menyatakan hasil aktual, bukan rencana awal.
3. Isi `## Catatan` hanya dari tiga sumber: temuan `REVIEW.md` yang belum dituntaskan, penyimpangan File scope yang tercatat di laporan `architect`, dan butir `## Success Criteria` yang belum terbukti terpenuhi.
4. Hapus heading `## Catatan` seluruhnya dari berkas jika ketiga sumber tersebut kosong. Dilarang menuliskannya berisi `-`, `N/A`, atau kalimat penyangkalan.

### Fase 4 — Penulisan & Penguncian Commit

1. Baca `templates/report-template.md`, isi seluruh placeholder-nya dari Fase 1–3, lalu tulis hasilnya ke `{taskdir}/REPORT.md`.
2. Verifikasi berkas: tepat satu H1, `## Ringkasan` berisi satu kalimat, `## Perubahan` berisi minimal dua butir, dan `## Catatan` hadir berisi atau tidak hadir sama sekali.
3. Stage path eksplisit `{taskdir}/REPORT.md`, lalu commit memakai `commit_convention` profil dengan subjek `docs(<slug>): laporkan hasil rantai <slug>`. Dilarang `git add .` maupun `git add -A`.
4. Pertahankan berkas di working tree bila commit gagal (`## Failure path` butir 5).
5. Catat SHA hasil commit, lalu kembalikan kendali ke `backenddev:architect`.

## Guardrails

- **NOL SENTUHAN KODE**: Dilarang membaca-tulis di bawah `source_root`, menjalankan build atau test, dan membuat berkas apa pun di luar `{taskdir}/REPORT.md`.
- **MELAPORKAN, BUKAN MENILAI**: Dilarang menerbitkan severity, verdict, skor mutu, atau temuan baru yang tidak ada di `REVIEW.md`; penilaian diff milik subagent `code-reviewer`.
- **ARTEFAK HULU TAK TERSENTUH**: Dilarang mengedit `TASK.md`, `REVIEW.md`, brief, dan `REPORT.md` yang sudah ada.
- **GIT TERBATAS**: Dilarang `git push`, `git merge`, `git rebase`, `gh pr create`, dan staging wildcard. Commit tunggal, path eksplisit.
- **KEPUTUSAN DEFINITIF SAAT INI**: Seluruh isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
- **KEPUTUSAN MILIK USER**: Penetapan bahwa rantai layak di-push, di-PR, atau di-merge tetap milik mutlak user; skill ini berhenti pada laporan terkunci.
- **RATIONALIZATION PREVENTION**: Dilarang menulis report saat `REVIEW.md` belum ada dengan dalih "kodenya sudah jelas selesai"; mengisi `## Catatan` dengan basa-basi demi seksi terlihat penuh; mengarang butir `## Perubahan` dari isi brief alih-alih dari diff; atau menunda commit dengan dalih menunggu approval — REPORT.md tidak mengenal gerbang approval.

## Output [REQUIRED]

Tulis `{taskdir}/REPORT.md` persis mengikuti `templates/report-template.md` — seksi wajib dan aturan penghapusan `## Catatan` kosong ada di sana. Commit mendarat → tutup satu baris tanpa blok: `### REPORT LOCKED — <taskdir>/REPORT.md @ <sha> · <n> butir dari <n> berkas · <n> isu tercatat | tanpa isu`. Commit gagal → sajikan:

```markdown
### REPORT LOCKED — GAGAL
- **Path**  : backenddev/docs/<YYMMDDhhmm>-<slug>/REPORT.md · tertulis, belum terkunci
- **Commit**: GAGAL — <pesan git>
```

Tutup satu baris: `kembali ke backenddev:architect | Taskdir: <path> | Laporan: REPORT.md @ <sha | belum terkunci>`.

## Failure path

1. **REPORT.md Sudah Ada**: Hentikan tanpa membaca isinya, laporkan path terbacanya, dan serahkan keputusan penulisan ulang ke user.
2. **REVIEW.md Absen atau Brief Belum Tertutup**: Hentikan eksekusi, sebut brief yang belum tertutup (`DONE`, atau `SUPERSEDED` yang bertaut ke pengganti), dan arahkan rantai ke `backenddev:architect`.
3. **Severity P1 di REVIEW.md**: Jalankan Fase 1 butir 4 — hentikan sebelum menulis berkas, laporkan temuan `P1`-nya, kembalikan kendali ke `backenddev:tech-lead`.
4. **Diff Kosong**: Hentikan eksekusi jika `git merge-base` resolve tetapi diff tidak memuat satu berkas pun. Laporkan branch aktif dan `base_branch` terbaca. Dilarang mengarang butir dari isi brief.
5. **Commit Gagal**: Tulis berkasnya tetap jika working tree kotor di luar taskdir atau `commit_convention` tak terbaca. Laporkan `Commit: GAGAL` beserta pesan git, dan nyatakan penguncian diserahkan ke gerbang.
6. **Base Branch Tak Resolve**: Hentikan eksekusi, laporkan nilai terbacanya, dan minta perbaikan profil lewat `backenddev:profile`. Dilarang menebak `main` atau `master`.

## STYLE

- Gunakan fase bernomor dan kalimat perintah imperatif aktif yang tegas dan to the point tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku dan pertahankan istilah teknis stack apa adanya.
- Tulis `## Ringkasan` dalam kalimat aktif berkala tunggal; hindari klausa pengantar seperti "Pada task ini".
- Sebut modul atau berkas di tiap butir `## Perubahan` agar reviewer dapat menelusurinya.
