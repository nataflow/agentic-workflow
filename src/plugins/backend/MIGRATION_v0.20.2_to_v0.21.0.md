# Migrasi `backend` v0.20.2 → v0.21.0

Langkah 32: memangkas ongkos tetap rantai pada perubahan kecil. Tidak ada perubahan config atau format dokumen
yang wajib dimigrasi; taskdir yang sedang berjalan dapat dilanjutkan apa adanya.

## Yang berubah

- **Serah terima PRD.** Pada chain ber-PRD (`PRD_BRIEF`, `BRD_PRD_BRIEF`), PRD yang baru disetujui tidak lagi
  langsung memberangkatkan `plan`. `analyst` mengembalikan vonis `PRD_APPROVED_SERAH_TERIMA`, lalu `tech-lead`
  berhenti dengan `Status Rantai: TERTAHAN (serah terima PRD)` dan menawarkan `/clear` atau `/compact` lalu
  `/backend:tech-lead lanjutkan <taskdir>`. Balasan "lanjut" di sesi yang sama tetap menulis brief seperti dulu.
- **Rute hop terbuka.** Taskdir yang dokumen hulunya sudah `APPROVED` tetapi hop berikutnya belum berangkat
  (mis. PRD `APPROVED`, hop `BRIEF` `[ ]`) kini dirutekan gerbang ke `analyst` tanpa `reentry_reason`; `analyst`
  masuk hop itu lewat resume Fase 0.
- **Cek simbol mengenali deklarasi baru.** `symbol_map.py --brief <brief>` membaca kolom `Anchor` dan
  `## Steps` sendiri. Method, test, atau tipe baru yang deklarasinya ditulis `## Steps` dilaporkan
  `new_declared` dan sah; suntingan simbol eksisting di luar `Anchor` tetap `HALT.md SYMBOL`. Mode anchor
  mencetak keluaran ringkas tanpa daftar `lines` (`--verbose` mengembalikannya).
- **Satu perintah penutup per brief.** `architect/scripts/close_brief.py --brief --sha` menjalankan
  `git status`, `verify_scope.py`, `symbol_map.py --brief`, dan mencabut lease, lalu mencetak satu baris vonis
  `PASS`/`STRAY`/`SCOPE`/`SYMBOL`.
- **Langkah test tidak dihitung langit-langit.** Batas 5 langkah per brief kini 5 langkah **produksi**: langkah
  yang seluruh berkas `## File scope` yang disebutnya berkas test tidak dihitung. Plafon 120 baris `## Steps`
  tetap berlaku.
- **Explorer delta.** Profil S `system-analysis` berangkat mode delta (slot `{laporan_gerbang}`) untuk simbol yang
  letaknya sudah dibuktikan laporan gerbang. `plan` memanen laporan Profil S/B lebih dulu: unit yang tertutup laci
  tidak didispatch, celah tercatat didispatch sempit.
- **Dispatch lewat berkas.** Prompt subagent dirender `skills/_common/render_prompt.py` ke
  `.explore/prompt/<nama>.md` dan dikirim sebagai satu kalimat rujukan berkas; tiap agent membaca berkas itu
  sebagai prompt utuhnya. Main loop tidak lagi memuat badan template dispatcher.

## Langkah migrasi

Tidak ada. Perbarui plugin, lalu pakai seperti biasa.

- Taskdir lama yang PRD-nya sudah `APPROVED` dan hop `BRIEF`-nya belum berangkat dapat dilanjutkan dengan
  `/backend:tech-lead lanjutkan <taskdir>`; ia tidak memicu serah terima PRD (persetujuannya bukan di pemanggilan
  itu), dan langsung masuk `plan`.
- Brief lama yang anchor-nya hanya menyebut simbol eksisting tidak perlu disunting: deklarasi barunya kini dinilai
  terhadap `## Steps`.
- Berkas `.explore/prompt/` ikut diabaikan git bersama dokumen taskdir lain dan tidak dipanen `validate_briefs.py`.
