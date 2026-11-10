# Migrasi `backend` v0.19.1 → v0.20.0

Langkah 30 dan 31: menghemat token di sesi rantai panjang. Tidak ada perubahan config atau format dokumen yang
wajib dimigrasi; taskdir yang sedang berjalan dapat dilanjutkan apa adanya.

## Yang berubah

- **Serah terima eksekusi.** Sesudah `analyst` memvonis `READY_FOR_IMPLEMENTATION`, `tech-lead` tidak lagi
  langsung memberangkatkan `architect`. Ia berhenti dengan `Status Rantai: TERTAHAN (serah terima)` dan
  menawarkan dua jalur: `/clear` (opsional `/model sonnet`) atau `/compact`, lalu
  `/backend:tech-lead lanjutkan <taskdir>`. Balasan "lanjut" di sesi yang sama tetap mengeksekusi seperti dulu.
  Jalur lanjutan membaca state dari disk dan langsung ke `architect` tanpa eksplorasi ulang.
- **`{taskdir}/JOURNEY.md`.** Catatan keputusan antar sesi yang ditulis `skills/_common/journey.py`: satu baris
  per titik rantai (`TECH_LEAD`, `BRD`/`PRD`, `READY`, `REVIEW`, `ARCHITECT`). Berkas ini ikut diabaikan git
  seperti dokumen taskdir lain dan tidak disinkron ke nataflow. Ia bukan sumber status: bila bertentangan dengan
  disk, disk menang. Taskdir lama tanpa berkas ini tetap berjalan (`journey.py show` melapor "belum ada").
- **Balikan `code-explorer` ringkas.** Laporan utuh hanya ditulis ke `.explore/<slug>.md`; balasan ke context
  menjadi amplop ≤15 baris (`confidence`, angka cakupan, `### Summary`, daftar seksi, path). Skill pendispatch
  membaca seksi yang dibutuhkan langsung dari berkas. Kedalaman, kuota baca, dan kewajiban bukti `file:line`
  tidak berubah.

## Langkah migrasi

Tidak ada. Perbarui plugin, lalu pakai seperti biasa. Taskdir lama yang sedang di tengah eksekusi
(`brief READY`) tidak punya entri journey `READY`, sehingga `/backend:tech-lead lanjutkan <taskdir>` menempuh
gerbang biasa (Fase 3: `brief READY` → `architect`), bukan jalur lanjutan serah terima.
