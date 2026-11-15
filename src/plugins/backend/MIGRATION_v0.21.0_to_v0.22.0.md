# Migrasi `backend` v0.21.0 → v0.22.0

Langkah 35: memangkas giliran mekanis main loop di fase `plan`. Tidak ada perubahan config atau format dokumen
yang wajib dimigrasi; taskdir yang sedang berjalan dapat dilanjutkan apa adanya.

## Yang berubah

- **Kerangka brief sekaligus.** `plan/scripts/scaffold_brief.py --all` menulis kerangka tiap baris matriks yang
  berkasnya belum ada dalam satu panggilan. Seluruh baris diperiksa lebih dulu: satu baris gagal berarti tidak satu
  kerangka, transisi `SUPERSEDED`, maupun pencabutan `HALT.md` yang mendarat. Berkas yang sudah ada dan brief
  terkunci dilewati. `--nn <NN>` tetap ada untuk satu brief dan `--force`.
- **`--open-round` membawa state ronde.** `validate_briefs.py --open-round` kini mencetak ronde terpakai, sisa
  plafon, brief berubah, dan isi slot `{ronde}`/`{brief_berubah}` dispatcher reviewer, sehingga `--review-state`
  tidak lagi wajib sebelum dispatch. Ronde lanjutan tanpa satu pun brief berubah tidak dibuka (exit 0, state tidak
  disentuh): self-review ditutup tanpa dispatch. Ronde yang masih terbuka tanpa vonis dibuka ulang dengan
  peringatan.
- **Gerbang brief pertama.** `validate_briefs.py --brief <NN>` dijalankan hanya atas brief pertama batch untuk
  menangkap cacat sistemik; brief sisanya ditagih gerbang batch Fase 4 seperti sebelumnya.
- **Contoh bentuk `brief-spec.json`** kini ada di SKILL `plan` Fase 3 butir 1.

## Langkah migrasi

Tidak ada. Perbarui plugin, lalu pakai seperti biasa.

- Taskdir yang kerangkanya sebagian sudah ditulis `--nn` dapat dilanjutkan dengan `--all`: berkas yang sudah ada
  dilewati, bukan ditimpa.
- State ronde self-review lama (`.explore/brief-review-state.json`) dibaca apa adanya.
