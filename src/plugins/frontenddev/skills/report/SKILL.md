---
name: report
description: Dipanggil frontenddev:architect Phase 5 sesudah REVIEW.md penutup lolos validate_review.py, ter-commit dengan verdict PASS atau WARNING, dan seluruh brief tertutup - perumusan REPORT.md dari berkas rantai sejak commit akar dan vonis Success Criteria REVIEW.md, dikunci satu commit sebagai penanda tuntas taskdir
user-invocable: false
---

## THE IRON LAW

- Tulis `REPORT.md` hanya sesudah `REVIEW.md` penutup lolos `validate_review.py`, ter-commit dengan verdict `PASS` atau `WARNING`, dan seluruh brief tertutup.
- Setiap butir `## Perubahan` wajib berakar pada berkas rantai; klaim tanpa berkas dibuang, bukan diloloskan.
- Skill ini melaporkan, bukan menilai — dilarang menerbitkan severity, verdict, atau temuan baru.
- Vonis tiap `SC-{n}` disalin dari `## Cakupan Success Criteria` `REVIEW.md`, bukan diklasifikasi ulang; `PERLU VERIFIKASI MANUAL` tetap begitu sampai user sendiri memverifikasinya.
- Dilarang menyentuh `src/`, mengedit `TASK.md`, `REVIEW.md`, atau brief mana pun.
- Kunci berkas dalam satu commit path-eksplisit sebelum mengembalikan kendali ke `frontenddev:architect`.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/report/scripts/check_preconditions.py --taskdir <taskdir>`.
2. `PASS` (8/8 checks) → lanjut ke Workflow; pakai baris `Terselesaikan:` (`akar`, `slug`, `berkas_rantai`) apa adanya di Phase 2. `FAIL` → hentikan dan remediasi butir gagal: taskdir atau akar tidak sah → kembali ke lead; `REVIEW.md` absen, belum ter-commit, basi (ada commit yang menyentuh `brief-*.md` sesudahnya), atau gagal `validate_review.py` → kembali ke `frontenddev:architect` Phase 4; verdict `BLOCKED` → REPORT ditahan, temuan dirutekan lead untuk diperbaiki di taskdir yang sama; brief belum tertutup → `frontenddev:architect`; ledger tidak tercentang penuh atau berubah → lead; `REPORT.md` sudah ada → serahkan keputusan penulisan ulang ke user; nol berkas rantai → laporkan ke user; working tree kotor → laporkan ke user, jangan di-stash sendiri.
3. Skrip: `chain.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py`; `validate_review.py` = `${CLAUDE_PLUGIN_ROOT}/skills/architect/scripts/validate_review.py`.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — path taskdir aktif berpola `frontenddev/docs/<YYMMDDhhmm>-<slug>`.

## Workflow

### Phase 1 — Penyerapan Akar & Hasil Rantai

1. Baca H1 `{taskdir}/TASK.md` dan pakai apa adanya sebagai judul `<H1 TASK.md> — Report`.
2. Serap `## Description` sebagai konteks, lalu salin vonis tiap `SC-{n}` aktif dari `## Cakupan Success Criteria` `REVIEW.md` (SC gugur — `~~…~~ — gugur: <alasan>` — tidak divonis dan tidak masuk `## Catatan`) — `terbukti` atau `PERLU VERIFIKASI MANUAL`. Vonis `belum terbukti` tidak mungkin sampai di sini: `validate_review.py` memaksanya jadi verdict `BLOCKED`.
3. Baca `{taskdir}/REVIEW.md`: catat temuan berstatus `PLANNED` atau `DEFERRED` sebagai sumber `## Catatan`.
4. Baca tiap `{taskdir}/report-<NN>.md`: seksi `## Triase` yang mencatat pemulihan scope, dan brief `BLOCKED` yang ditutup remedi, adalah sumber penyimpangan untuk `## Catatan`.

### Phase 2 — Derivasi Perubahan dari Berkas Rantai

1. Pakai `berkas_rantai` prasyarat, atau jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py files --taskdir <taskdir>`. Daftar ini — berkas yang diubah commit bersubjek `<type>(<slug>):` sesudah akar terkunci — adalah satu-satunya sumber sah butir `## Perubahan`; commit user lain yang menyelinap di rentang yang sama tidak ikut terhitung.
2. Kelompokkan berkas per layar, unit logika, atau direktori modul, bukan per berkas. Tulis 1–7 butir berbentuk `- <perubahan perilaku> (<berkas atau direktori>)`.
3. Tambahkan butir bila satu berkas rantai tidak tercakup butir mana pun; dilarang meninggalkan berkas menggantung.
4. Dilarang menyalin subjek commit atau isi brief sebagai butir; butir menyatakan perubahan perilaku yang mendarat.

### Phase 3 — Ringkasan & Catatan

1. Rumuskan `## Ringkasan` sebagai tepat satu kalimat hasil aktual — bukan pengulangan `## Description` TASK.md.
2. Isi `## Catatan` hanya dari tiga sumber: butir `SC-{n}` `PERLU VERIFIKASI MANUAL` (disertai langkahnya), temuan `REVIEW.md` yang belum dituntaskan, dan penyimpangan yang tercatat di `## Triase` `report-<NN>.md` — termasuk unit `BLOCKED` beserta remedinya.
3. Hapus heading `## Catatan` seluruhnya bila ketiga sumber kosong.

### Phase 4 — Penulisan, Validasi & Penguncian

1. Tulis `{taskdir}/REPORT.md` mengikuti `templates/report-template.md` bagian 1.
2. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/report/scripts/validate_report.py --taskdir <taskdir>`; `FAIL` → perbaiki berkasnya lalu ulangi, maksimal 2 putaran perbaikan; masih `FAIL` → hentikan tanpa commit, sajikan butir gagal di Output, dan serahkan ke user.
3. Stage path eksplisit `{taskdir}/REPORT.md`, lalu commit `docs(<slug>): laporkan hasil rantai <slug>`. Dilarang `git add .` maupun `git add -A`.
4. Catat SHA commit dan kembalikan kendali ke `frontenddev:architect`.

## Guardrails

- **NOL SENTUHAN KODE**: dilarang menulis di luar `{taskdir}/REPORT.md`, menjalankan build atau test, dan mendispatch subagent.
- **MELAPORKAN, BUKAN MENILAI**: dilarang menerbitkan severity, verdict, atau temuan yang tidak ada di `REVIEW.md`; penilaian diff milik `code-reviewer` lewat `frontenddev:architect`.
- **ARTEFAK HULU TAK TERSENTUH**: dilarang mengedit `TASK.md` (termasuk mencentang `SC-{n}`), `REVIEW.md`, brief, dan `REPORT.md` yang sudah ada.
- **GIT TERBATAS**: dilarang `git push`, `git merge`, `git rebase`, `gh pr create`, dan staging wildcard.
- **KEPUTUSAN MILIK USER**: penetapan bahwa rantai layak di-push, di-PR, atau di-merge, serta hasil QA manual, tetap milik user; skill ini berhenti pada laporan terkunci.
- **RATIONALIZATION PREVENTION**: dilarang menulis report sebelum `REVIEW.md` ter-commit ("kodenya sudah jelas selesai"), menyatakan butir `QA manual:` terpenuhi karena test lain hijau, mengisi `## Catatan` dengan basa-basi, atau mengarang butir `## Perubahan` dari brief alih-alih dari berkas rantai.

## Output [REQUIRED]

Validasi `PASS` dan commit mendarat → tutup satu baris: `### REPORT LOCKED — <taskdir>/REPORT.md @ <sha> · <n> butir dari <n> berkas · SC <n> terbukti / <n> manual / <n> belum`. Commit gagal → sajikan:

```markdown
### REPORT LOCKED — GAGAL
- **Path**  : frontenddev/docs/<YYMMDDhhmm>-<slug>/REPORT.md · tertulis, belum terkunci
- **Commit**: GAGAL — <pesan git>
```

Tutup satu baris: `kembali ke frontenddev:architect | Taskdir: <path> | Laporan: REPORT.md @ <sha | belum terkunci>`.

## Failure path

1. **REPORT.md sudah ada**: hentikan tanpa menimpa. Ter-commit → laporkan path-nya dan serahkan keputusan penulisan ulang ke user; belum ter-commit → tertunda, penguncian milik `architect` Phase 5 butir 4.
2. **Taskdir tanpa TASK.md**: hentikan; tidak ada kriteria untuk dipasangkan — sejak v0.4.0 tidak ada taskdir sah tanpa akar.
3. **Verdict BLOCKED**: hentikan sebelum menulis berkas; lead merutekan temuannya ke brief perbaikan di taskdir yang sama (`chain.py reopen --row BRIEF` → `plan` APPEND).
4. **Nol berkas rantai**: hentikan dan laporkan `akar` serta slug terbaca. Dilarang mengarang butir dari isi brief.
5. **Commit gagal**: pertahankan berkas di working tree, laporkan `Commit: GAGAL` beserta pesan git, serahkan penguncian ke `architect` (fase `LAPORAN TERTUNDA`, Phase 5 butir 4).

## STYLE

- Gunakan fase bernomor dan kalimat imperatif aktif.
- Gunakan Bahasa Indonesia baku dan istilah teknis asli stack.
- Sebut berkas atau direktori di tiap butir `## Perubahan` agar reviewer dapat menelusurinya.
