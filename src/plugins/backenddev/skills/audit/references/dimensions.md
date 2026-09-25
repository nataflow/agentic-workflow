# Six audit dimensions + the verification gate — `audit`

Rumah tunggal **definisi** dimensi untuk `backenddev:audit`. Butir checklist
konkretnya tidak tinggal di sini: ia milik `## Audit checklist` pada `../../profile/stacks/<stack-id>.md`,
dibaca dari field `stack` di `.claude/profile/backenddev/index.json`. Jangan menyalin butir adapter ke skill
mana pun — dua salinan melahirkan dua definisi `P1`.

Subagent `code-reviewer` memegang kembaran **diff-scoped** dari definisi keenam dimensi ini di
`agents/code-reviewer.md` Fase 1 butir 5, karena ia menilai baris yang berubah alih-alih menyapu
direktori. Perubahan definisi dimensi di sini wajib menyentuh berkas itu juga.

Default sweep memeriksa keenam dimensi (dibaca di awal Fase 2). Jika user mempersempit, baca hanya
sub-heading dimensi yang diminta dari adapter. Tiap butir adalah kandidat yang wajib melewati
**Verification gate**.

Enam nilai sah field `Dimension`: `security`, `transaction`, `data`, `persistence`, `concurrency`,
`architecture`. Kandidat yang cocok di lebih dari satu checklist dicatat sebagai **satu** temuan
dengan dampak terburuk, menurut prioritas menurun:

`security` → `transaction` → `data` → `persistence` → `concurrency` → `architecture`

## `security` — Security & scoping

Celah otorisasi, kebocoran data, dan manipulasi input. Yang dinilai: siapa boleh menyentuh data
siapa, dan apakah input dari luar bisa memutarbalikkan jawaban itu.

## `transaction` — Transactional correctness

Kerusakan pada **atomicity** perubahan data. Yang dinilai: apakah satu perubahan yang secara logika
utuh benar-benar utuh saat gagal di tengah — termasuk efek samping ke luar proses (pesan, event,
panggilan HTTP) yang tidak ikut ter-rollback.

## `data` — Data correctness

Cacat komputasi yang menghasilkan nilai salah **tanpa memicu error**. Yang dinilai: tipe numerik
untuk nilai uang dan kuantitas, pembulatan, perbandingan, penanganan nilai kosong, semantik waktu,
dan penegakan validasi di semua jalur tulis — bukan hanya jalur HTTP.

## `persistence` — Storage access & performance

Pola akses penyimpanan yang tidak efisien atau berefek query keliru. Yang dinilai: jumlah query yang
benar-benar terbit, batas hasil, kebocoran koneksi/cursor, pemetaan tipe, dan kebenaran hasil saat
relasi ikut dimuat.

## `concurrency` — Concurrency, async & messaging

Jalur eksekusi di luar satu request sinkron: consumer antrean, scheduler, worker latar, tugas
asinkron. Yang dinilai: idempotensi terhadap pengulangan, penanganan kegagalan pengiriman, batas
waktu dan retry, pewarisan konteks, serta keselarasan mirrored path terhadap `## Invariants` profil.

## `architecture` — Architecture

Penyimpangan struktural dan pelanggaran boundary layer. Yang dinilai: penempatan logika, arah
dependensi, kebocoran tipe antar-layer, state bersama yang bisa berubah, dan penyimpangan dari
anatomi module yang tercatat di `.claude/profile/backenddev/module-structure.md`.

Tolok ukurnya bergantung pada field `architecture` di `index.json`. Pada `layered`, yang dinilai adalah
penempatan logika dan lompatan layer (handler memanggil repository). Pada `hexagonal`, yang dinilai
adalah **arah dependensi**: inti tidak boleh mengimpor adapter atau driver, port dideklarasikan di
sisi konsumen, dan tipe infrastruktur tidak boleh muncul di signature port. Butir bertanda
`hexagonal` di adapter stack **hanya** dipakai bila profil bernilai `hexagonal` atau `hybrid`;
memakainya pada repo `layered` menghasilkan temuan palsu. Pada `hybrid`, gaya ditentukan per modul
yang sedang disapu, dengan bukti `file:line` yang menunjukkan gaya modul itu.

## Butir universal lintas stack

Empat butir berikut terbukti berlaku identik di seluruh adapter, sehingga rumahnya di sini — bukan
diulang di tiap `stacks/<stack-id>.md`. Sapuan wajib memeriksa keempatnya di samping butir adapter.

- **IDOR** — `security`. Baris data diambil hanya berdasarkan identitas yang dikirim klien, tanpa
  klausa kepemilikan di dalam query yang sama. Pemeriksaan kepemilikan setelah data terambil tetap
  membocorkan keberadaan data lewat perbedaan waktu respons dan pesan error.
- **Panggilan jaringan di dalam batas transaksi** — `transaction`. HTTP keluar atau publish pesan
  sambil memegang transaksi menahan koneksi basis data selama I/O eksternal, dan menautkan umur
  transaksi ke ketersediaan sistem lain.
- **Kolom yang dipakai di `WHERE` atau `ORDER BY` tanpa index** — `persistence`. Biayanya tidak
  terlihat pada data kecil dan baru muncul sebagai timeout setelah tabel tumbuh.
- **Modul menyimpang dari anatomi standar di `.claude/profile/backenddev/module-structure.md`** — `architecture`.
  Profil adalah rekaman kode nyata repo; penyimpangan darinya membuat seluruh skill hilir menebak.

## Verification gate — mandatory, per candidate

Tiap kandidat wajib diverifikasi dengan bukti nyata (`file:line`, konfigurasi, schema) sebelum
dilaporkan:

- **CONFIRMED** — Ada bukti `file:line` konkret untuk sumber data, jalur eksekusi, dan dampak.
- **PLAUSIBLE** — Bukti kuat namun belum lengkap; sebutkan fakta yang belum terverifikasi.
- **Dibuang** — Tidak terbukti; catat alasan di Catatan verifikasi agar tidak diperiksa ulang.

**Tanpa bukti = dibuang, bukan diturunkan jadi P3.**
