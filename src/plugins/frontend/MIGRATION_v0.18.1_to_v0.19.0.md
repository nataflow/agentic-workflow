# Migrasi `frontend` v0.18.1 → v0.19.0

Langkah 33: menghemat token di sesi rantai panjang, mengadaptasi Langkah 30–31 plugin `backend`. Tidak ada
perubahan config atau format dokumen yang wajib dimigrasi; taskdir yang sedang berjalan dapat dilanjutkan apa
adanya.

## Yang berubah

- **Serah terima konteks di dua titik.** Sesudah `CONTRACT` disetujui (lane ber-CONTRACT) dan sesudah `BRIEF`
  disetujui (semua lane, termasuk `HOTFIX_MINOR`), gate tidak lagi langsung memanggil `plan`/`architect`. Ia
  berhenti dan menawarkan: `/clear` (opsional `/model sonnet`) lalu `/frontend:lead lanjutkan <taskdir>`,
  `/compact`, atau balasan "lanjut" untuk meneruskan di sesi yang sama seperti dulu.
- **Jalur cepat `lead`.** "lanjutkan `<taskdir>`" melewati sapuan lokasi dan pemilihan lane, lalu merutekan
  menurut `taskdir_state.py --taskdir` (mis. `plan` mode `CONTRACT`, atau `architect`).
- **`{taskdir}/JOURNEY.md`.** Catatan keputusan antar sesi yang ditulis `skills/_common/journey.py`: satu baris
  per titik (`LEAD`, `FLOW`/`UI`/`CONTRACT`/`BRIEF`, `ARCHITECT`, `REVIEW`). Berkas ini ikut diabaikan git
  seperti dokumen taskdir lain dan tidak disinkron ke nataflow. Ia bukan sumber status: bila bertentangan dengan
  disk, disk menang. Taskdir lama tanpa berkas ini tetap berjalan (`journey.py show` melapor "belum ada").
- **`code-explorer` berjalan dengan effort `medium`.** Kedalaman, kuota baca, dan kewajiban bukti `file:baris`
  tidak berubah.

## Langkah migrasi

Tidak ada. Perbarui plugin, lalu pakai seperti biasa. Taskdir lama di tengah rantai dilanjutkan dengan
`/frontend:lead lanjutkan <taskdir>`; jalur cepat tidak bergantung pada isi journey.
