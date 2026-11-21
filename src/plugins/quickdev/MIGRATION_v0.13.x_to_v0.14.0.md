# Migrasi `quickdev` v0.13.x → v0.14.0

quickdev 0.14.0 mengikat rencana ke nataflow lebih erat: task nataflow yang sudah ada bisa menjadi acuan, rencana
sudah terbaca di nataflow saat approval diajukan, dan hasil eksekusi terbit sebagai dokumen report.

## Yang berubah

| Sebelum (0.13) | Sesudah (0.14) |
|---|---|
| task nataflow selalu task baru milik quickdev | user boleh menyebut task acuan (`#12` atau UUID): `plan_lock.py task --ref` membacanya, deskripsinya menjadi spesifikasi, rencana menaut lewat `Nataflow-Task`, dan quickdev tidak membuat task baru maupun mengubah isinya |
| rencana DRAFT tidak didorong; cermin pertama sesudah `lock` | `plan` Fase 4 mencerminkan draf sebelum approval diajukan (dan di tiap revisi); task baru tetap `todo` sampai `lock` |
| sinkron `GAGAL` tidak pernah menahan apa pun | di Fase 4 `plan`, `GAGAL` menahan approval: *Coba lagi* · *Lanjut tanpa cermin nataflow* |
| hanya dokumen `quickdev.plan` | ditambah `quickdev.report` (`<task>.report.md`) sesudah eksekusi ditutup |
| — | `plan_lock.py summary` menulis ringkasan naratif 1–3 kalimat ke blok (`Summary`) sesudah `close` |
| segmen `NATAFLOW: workdir <nama> · …` | `NATAFLOW: task #<kode> · workdir <nama> · …` |

## Langkah migrasi per repo

1. **Daftarkan tipe dokumen `quickdev.report` di server nataflow** (sekali per server). Tanpanya rencana tetap
   tercermin, tetapi segmen berakhir `· report GAGAL: …`.
2. **Tidak ada yang lain yang wajib.** Rencana tanpa `Nataflow-Task` memakai task milik quickdev seperti sebelumnya;
   rencana yang sedang berjalan tetap lolos `verify`.
3. **Task acuan untuk rencana lama** tidak bisa ditautkan menyusul: rencana yang sudah tersinkron punya workdir di
   task milik quickdev, dan skrip menolak memindahkannya. Buat rencana baru bila ingin bekerja di bawah task acuan.

## Kebiasaan baru

- Sebut task nataflow di permintaan (`/quickdev:plan kerjakan task #12`) supaya rencana memakai kartu task itu
  sebagai spesifikasi dan workdir-nya menempel di task yang sama dengan taskdir backend/frontend.
- Baca draf di nataflow sebelum memilih *Setujui & eksekusi*; ringkasan gerbang menyebut `task #<kode>`.
