# Migrasi `quickdev` v0.12.x → v0.13.0

quickdev 0.13.0 mengurangi jeda konfirmasi: `plan → execute → review` berantai sesudah user menyetujui rencana,
dan berkas rencana di-commit otomatis.

## Yang berubah

| Sebelum (0.12) | Sesudah (0.13) |
|---|---|
| ketiga skill ber-`disable-model-invocation: true` | hanya `plan`; `execute` dan `review` boleh dipanggil skill quickdev lain |
| approval: *Setujui rencana* · *Revisi* | *Setujui & eksekusi* · *Setujui saja* · *Revisi* |
| user disarankan meng-commit rencana `APPROVED` sendiri | `plan` Fase 5 menjalankan `plan_lock.py commit` (berkas rencana saja, di branch aktif) sebelum sinkron nataflow |
| `plan` menawarkan `/quickdev:execute` lalu menunggu | *Setujui & eksekusi* → `quickdev:execute` dipanggil langsung; *Setujui saja* → tetap ditawarkan |
| `execute` `COMPLETED` menawarkan `/quickdev:review` | `quickdev:review` dipanggil langsung dan temuannya dilaporkan |
| remediasi: user mengetik `/quickdev:execute` | tidak berubah — remediasi tetap keputusan user |

## Langkah migrasi per repo

1. **Tidak ada yang wajib.** Rencana yang sedang berjalan tetap lolos `verify` dan dilanjutkan seperti biasa.
2. **Rencana di `.gitignore`**: `plan_lock.py commit` melewatinya (`COMMIT SKIP`). Lepaskan `plan/` dari
   `.gitignore` bila ingin riwayat rencana tercatat.
3. **Repo dengan hook commit** (commitlint, pre-commit): subjek commit rencana adalah
   `docs(plan): setujui rencana <task>`. Hook yang menolaknya menghasilkan `COMMIT GAGAL`; rencana tetap
   `APPROVED` dan skrip mencetak perintah manualnya.

## Kebiasaan baru

- Pilih *Setujui & eksekusi* untuk menjalankan seluruh rantai dalam satu giliran. Rantai tetap berhenti di izin
  perintah `menyentuh DB/jaringan`, tree kotor saat `execute` mulai, `BLOCKED`, `VERIFICATION_MANUAL_REQUIRED`,
  dan keputusan remediasi.
- Review yang dipanggil langsung oleh `execute` selalu `sesi-sama=ya`. Untuk putaran terakhir, jalankan ulang
  `/quickdev:review` di sesi baru.
