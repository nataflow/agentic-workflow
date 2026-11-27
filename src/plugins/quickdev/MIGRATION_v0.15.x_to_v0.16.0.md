# Migrasi `quickdev` v0.15.x → v0.16.0

quickdev 0.16.0 menindaklanjuti review lapangan (Q5): "perbaiki temuan minor" diketik di sekitar 40% sesi, jadi
remediasi temuan review kini berantai dari pilihan di laporan review, tidak lagi diketik user.

## Yang berubah

| Sebelum (0.15) | Sesudah (0.16) |
|---|---|
| `CHANGES_REQUIRED` menawarkan *Remediasi otomatis*, ditutup perintah `/quickdev:execute <plan_path>` untuk diketik user | opsi pertama *Perbaiki semua temuan — remediasi putaran n+1/2 (Recommended)* langsung memanggil `quickdev:execute` (remediasi), lalu review ulang |
| `REVIEWED` dengan temuan MINOR langsung ke tawaran commit | satu pertanyaan gabungan: *Perbaiki semua temuan minor (Recommended)* · *Commit di branch aktif* · *Commit di branch baru* · *Jangan dulu* |
| `review_findings` hanya dari laporan `CHANGES_REQUIRED` | juga dari laporan `REVIEWED` bertemuan MINOR yang dijawab *Perbaiki semua temuan minor* |

Plafon tetap 2 putaran remediasi per rencana (`plan_lock.py start --findings`): sesudah putaran ke-2, opsi perbaiki
tidak ditawarkan lagi. Temuan yang menuntut berkas di luar rencana tetap berakhir `BLOCKED` dan diarahkan ke revisi
rencana.

## Langkah migrasi per repo

Tidak ada. Format rencana, blok `## Execution Status`, dan subperintah `plan_lock.py` tidak berubah; rencana yang
sedang berjalan dilanjutkan apa adanya.

## Kebiasaan baru

- Berhenti mengetik "perbaiki temuan minor": pilih opsi perbaiki di laporan review.
- Ingin menerima temuan MINOR apa adanya: pilih salah satu opsi commit (atau *Jangan dulu*) di pertanyaan yang sama.
