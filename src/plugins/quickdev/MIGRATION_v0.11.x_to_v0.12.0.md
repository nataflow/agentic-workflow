# Migrasi `quickdev` v0.11.x → v0.12.0

quickdev 0.12.0 menyederhanakan alur untuk repo kecil yang masih awal development: dari enam skill menjadi tiga
(`plan → execute → review`), tanpa profil repo.

## Yang berubah

| Sebelum (0.11) | Sesudah (0.12) |
|---|---|
| `/quickdev:profile` menulis `repo-profile.md` + baseline | dihapus; tidak ada artefak tingkat repo |
| `/quickdev:explore` lalu `/quickdev:clarify` | dihapus; telusur kode dan klarifikasi menjadi Fase 1–2 `/quickdev:plan` |
| perintah verifikasi dari Section 5 profil | tabel Jenis/Perintah/Cwd/Risiko di Section 4 rencana, ditulis `plan` dari manifest dan ikut disidik |
| izin menjalankan baseline ditanya di `profile` | approval rencana mencakup perintah Section 4; perintah bertanda `menyentuh DB/jaringan` ditanya sekali di `execute` |
| pembanding regresi: baseline segar atau profil (`PEMBANDING:`) | selalu baseline segar di `Base-Commit` (`plan_lock.py baseline`) |
| metadata rencana `Profile:`, `Gates:`, `Hash-Scope: profile+body` | tidak ditulis lagi; `lock` menulis `Hash-Scope: body` (sidik Section 1–5) |
| `plan_lock.py lock --profile`, `sync-payload --repo-profile` | dihapus (argparse menolaknya) |
| dimensi review "Konvensi Profil & Layer" | "Konvensi Repo & Layer": acuan Section 2 rencana dan berkas sejenis, berbukti `path:baris` |
| penawaran `.claude/workflow` di `profile` Fase 4 | di `plan` Fase 0 |

## Langkah migrasi per repo

1. **Tidak ada yang wajib.** Repo tanpa `repo-profile.md` langsung memakai `/quickdev:plan`.
2. **`repo-profile.md` yang sudah ada** tidak lagi dibaca. Hapus berkasnya bila tidak dipakai alat lain, atau
   biarkan; quickdev 0.12 mengabaikannya. Ia bukan lagi artefak gate untuk rencana baru, jadi perubahan
   uncommitted padanya membuat `execute` mode `awal` menolak tree kotor — commit atau hapus dulu.
3. **Rencana yang sedang berjalan** (terkunci 0.11 dengan `Hash-Scope: profile+body`) tetap lolos `verify` dan
   dapat diselesaikan `execute`/`review` 0.12; profil yang tercatat di `Profile:`-nya tetap dikecualikan dari
   tree kotor dan `Tree-Hash`. Satu perbedaan: baseline tidak lagi diambil dari profil. Rencana lama yang
   Section 4-nya belum berupa tabel tetap dijalankan dengan perintah yang tertulis di sana (`Cwd` root).
4. **Rencana yang dibuka ulang** (`unlock` → revisi → `lock`) dikunci dengan `Hash-Scope: body`. Pertimbangkan
   mengubah Section 4 menjadi tabel saat revisi.
5. **Dokumen `profile` di nataflow** yang pernah disinkron tidak dihapus dan tidak diperbarui lagi; hapus dari
   server bila tidak dibutuhkan.

## Kebiasaan baru

- Satu perintah untuk mulai: `/quickdev:plan <permintaan>`. Telusur, klarifikasi, draf, dan approval terjadi di
  pemanggilan itu; `plan` tidak menjalankan perintah apa pun.
- Repo besar dengan konvensi yang sudah mapan lebih cocok memakai `backend:tech-lead` atau `frontend:lead`.
