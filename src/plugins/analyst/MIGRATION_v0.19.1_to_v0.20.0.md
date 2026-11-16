# Migrasi `analyst` v0.19.1 → v0.20.0

Langkah 38: friksi lapangan analyst. Di lapangan, enam tiket `READY` di repo frontend menjadi `DRIFT` hanya karena
`yarn run format` (prettier) dijalankan atas seluruh repo: prettier menambah baris kosong di bawah heading,
meratakan padding tabel, dan mengubah `*x*` menjadi `_x_`, sehingga sidik persetujuan tidak lagi sama walau isinya
tidak berubah. Tiket yang sedang berjalan tetap dapat dilanjutkan apa adanya.

## Yang berubah

- **Sidik tahan format.** `approved_hash`, `elicit_hash`, `request_hash`, dan sidik review dihitung atas teks yang
  dinormalkan dari perbedaan format (baris kosong, padding sel tabel, baris pemisah tabel, `>` kosong, bullet
  `*`/`+`, `*` tunggal ↔ `_`, spasi beruntun). Suntingan kata, angka, baris, atau sel tetap `DRIFT`. Pemeriksa
  menerima sidik lama atau baru.
- **`approved_seal_norm`.** `approve` menulis field baru ini di samping `approved_seal`. `approved_seal` tetap
  algoritma lama, jadi backend/frontend yang belum diperbarui memvonis seperti sebelumnya; backend 0.23.1 dan
  frontend 0.21.1 menerima tiket yang cocok dengan salah satunya.
- **`ticket.py reseal --all | --ticketdir <td>`.** Menaikkan sidik yang masih cocok dengan isi ke algoritma baru tanpa
  mengubah isi tiket. Tiket `DRIFT` dilaporkan, tidak disentuh.
- **`--ticketdir` relatif dibaca terhadap cwd.** `--ticketdir .` dari dalam ticketdir tidak lagi gagal "Letak
  ticketdir"; di luar git, root naik keluar dari `analyst/tickets/<td>`.
- **Ekor batch.** `ticket.py state` menandai tiket `ELISITASI` tanpa log dengan rute `belum disentuh sejak <tanggal>`.
  Batch yang dihentikan sebelum tiket terakhir menawarkan sekali: biarkan terbuka, atau batalkan yang belum disentuh.
- **Temuan sesi.** `elicit` memakai temuan penelusuran yang sudah ada di percakapan (mis. dari `backend:tech-lead`
  sebelum "buatkan tiketnya") seperti balikan `KONTEKS`, dan mendispatch `analyst:code-explorer` hanya untuk konsep
  yang belum tercakup. Tiket `TECH` tetap wajib explorer `BUKTI`.

## Langkah migrasi

1. Perbarui `analyst`, `backend`, dan `frontend` bersamaan (0.20.0, 0.23.1, 0.21.1).
2. Di tiap repo yang punya `analyst/tickets/`, jalankan sekali dari root repo:

   ```sh
   python3 ~/.claude/plugins/cache/<marketplace>/analyst/0.20.0/skills/_common/ticket.py reseal --all
   ```

   Repo git dengan ticketdir ter-track mendapat satu commit `docs(ticket): segel ulang <n> tiket`; ticketdir yang
   diabaikan git ditulis tanpa commit.
3. Tiket yang dilaporkan `DRIFT` oleh `reseal` (mis. yang sudah diformat sebelum migrasi) tidak dapat dibuktikan hanya
   berubah format, karena teks yang disetujui tidak tersimpan. Setujui ulang lewat `/analyst:intake` → `analyst:spec`
   (`reopen` → review → approve).
