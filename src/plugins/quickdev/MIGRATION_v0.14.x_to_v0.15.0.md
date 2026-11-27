# Migrasi `quickdev` v0.14.x → v0.15.0

quickdev 0.15.0 menindaklanjuti review lapangan: rencana tidak lagi masuk git, commit hasil ditawarkan di akhir
rantai, dan status sinkron nataflow selalu terlihat.

## Yang berubah

| Sebelum (0.14) | Sesudah (0.15) |
|---|---|
| `plan` Fase 5 meng-commit `plan/<task>.md` di branch aktif (`docs(plan): setujui rencana <task>`) | rencana tidak di-commit: `plan_lock.py lock` (dan `start` untuk rencana yang dikunci versi lama) menulis penanda `plan/.gitignore` berisi `*`; jejaknya ada di cermin nataflow |
| `plan_lock.py commit --plan <p>` meng-commit berkas rencana | `plan_lock.py commit --plan <p> --message - [--branch <nama>]` meng-commit hasil eksekusi `COMPLETED` yang segelnya cocok: hanya berkas yang disegel `close`, ditambah berkas rencana bila masih ter-track |
| `review` read-only penuh; commit kode diketik user | `REVIEWED` (atau *Terima apa adanya*) menawarkan *Commit di branch aktif* · *Commit di branch baru* · *Jangan dulu* |
| `START FAIL` tree kotor selalu buntu | bila seluruh berkas kotor hasil rencana lain yang sudah `COMPLETED`, `start` mencetak `MILIK: <rencana>` dan `execute` menawarkan commit hasil itu dulu |
| tipe dokumen belum terdaftar → `upsert_document: invalid input data` | skrip memeriksa `list_document_types` lebih dulu: `quickdev.plan` absen → `GAGAL` sebelum tulisan apa pun, `quickdev.report` absen → `· report GAGAL: …`, keduanya dengan instruksi pendaftaran |
| ringkasan `review` tanpa status sinkron | ringkasan `review` memuat `NATAFLOW:` (segmen `execute` terakhir apa adanya) dan `COMMIT:` |

## Langkah migrasi per repo

1. **Tidak ada yang wajib untuk rencana baru.** `lock` pertama di 0.15 menulis `plan/.gitignore` sendiri; berkas
   itu mengabaikan dirinya sendiri dan tidak perlu di-commit. `.gitignore` akar repo tidak disentuh.
2. **Repo yang sudah meng-commit `plan/*.md`** (0.13–0.14): rencana lama tetap ter-track dan ikut commit kode bila
   berubah. Untuk melepasnya dari git tanpa menghapus berkasnya dari disk, jalankan sekali di root repo, di branch
   tempat Anda biasa meng-commit:

   ```
   git rm -r --cached plan/
   git commit -m "chore: lepas plan/ dari git (rencana quickdev dicerminkan ke nataflow)"
   ```

   Jalankan sesudah tidak ada rencana yang sedang dieksekusi (blok `IN_PROGRESS`/`BLOCKED`), supaya diff review
   berikutnya tidak memuat penghapusan rencana. `plan_dir` lain → ganti `plan/` dengan direktori itu.
3. **Commit "setujui rencana" lama** di riwayat tidak perlu dihapus. Bila ingin membuangnya dari branch yang belum
   di-push, itu keputusan Anda (`git rebase`); quickdev tidak melakukannya.
4. **Tanpa `.claude/nataflow.json`** rencana kini hanya ada di disk; `lock` mencetak `PERINGATAN` sekali saat
   penanda ditulis. Aktifkan sinkron (prosedur `skills/plan/references/nataflow-sync.md`) bila rencana perlu dibaca
   orang lain.
5. **Tipe dokumen** `quickdev.plan` dan `quickdev.report` tetap wajib terdaftar di server (admin, halaman Document
   Types). Server tanpa tool `list_document_types` tetap dilayani; pengecekannya dilewati.

## Kebiasaan baru

- Berhenti mengetik "commit" di akhir sesi: pilih opsi commit di laporan review.
- Mengerjakan beberapa task berurutan: bila task sebelumnya belum di-commit, `/quickdev:execute` task berikutnya
  menawarkan commit hasil itu, bukan berhenti dengan `START FAIL`.
- Ingin tahu apakah dokumen sudah tercermin: lihat baris `NATAFLOW:` di ringkasan `execute` atau `review`.
