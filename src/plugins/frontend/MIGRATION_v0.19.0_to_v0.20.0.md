# Migrasi `frontend` v0.19.0 → v0.20.0

Langkah 36: menghapus friksi yang ditemukan di pemakaian lapangan — loop remedi karena format, rantai yang tak
bisa menghapus berkas, taskdir yang diulang dari nol karena plafon ronde reviewer, dan giliran yang terbuang. Tidak
ada format dokumen yang wajib dimigrasi; taskdir yang sedang berjalan dapat dilanjutkan apa adanya.

## Yang berubah

- **Format unit sebelum commit.** Baris opsional ``- `format`: `<perintah>` `` di
  `.claude/profile/frontenddev/commands.md` (mis. `yarn prettier --write --ignore-unknown`). Bila ada, `architect`
  menjalankannya atas berkas `CREATE`/`MODIFY` unit sebelum commit unit, sehingga cacat format tidak lagi baru
  ketahuan di verifikasi penutup dan dibayar dengan brief perbaikan. Tanpa baris itu perilakunya sama dengan
  0.19.0.
- **Aksi `DELETE`.** Tabel seksi 3 brief dan `## 1. Files Touched` kontrak menerima `DELETE` untuk berkas yang
  dihapus utuh. Implementor tidak menyentuhnya; `architect` menjalankan `git rm` di commit unit. Penghapusan berkas
  tidak lagi alasan meninggalkan rantai.
- **Satu ronde reviewer tambahan.** Plafon 2 ronde per putaran (`contract-reviewer`, `doc-reviewer`) kini dapat
  ditambah satu ronde, hanya atas persetujuan user, lewat `review_round.py open --tambahan "<alasan; jawaban
  user>"`. Gate menawarkannya sebelum menyerahkan ke `lead` untuk dirumuskan ulang; plafon 8 per taskdir tetap.
- **Verdict reviewer kontrak.** `- Verdict: PASS — nol temuan` kini diterima `record`; agent menulis
  `- Verdict: PASS` saja.
- **Prasyarat `architect` lebih lengkap.** `Terselesaikan:` membawa `base_commit` dan `format`; mode rantai
  mencetak blok `Rantai:`, mode `--brief` mencetak `Berkas unit <NN>:`. `architect` tidak lagi membaca frontmatter
  brief atau `TASK.md` lewat `sed`/`grep`.
- **Plafon journey disebut di tiap titik panggil** (2 kalimat, 280 karakter) — `journey.py` sendiri tidak berubah.
- **`lead` lebih ramping.** Phase 3–7 (lane, sections, slug, peta gate, kunci akar) pindah ke
  `skills/lead/references/permintaan-baru.md`, dibaca hanya untuk permintaan baru; sesi `lanjutkan <taskdir>`
  tidak memuatnya.

## Langkah migrasi

Tidak ada yang wajib. Opsional: tambahkan baris `format` ke `commands.md` profil repo yang sudah bersih format
(pemeriksaan formatnya `OK` di baseline), lewat `frontend:profile` REFRESH atau suntingan tangan yang di-commit.
Jangan menambahkannya di repo yang belum bersih format — format atas berkas unit akan merombak berkas utuh.
