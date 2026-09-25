---
name: debug
description: Gunakan ketika ada stacktrace, exception, HTTP 5xx, atau test merah yang penyebabnya belum diketahui - pembuktian rantai kausal file:line di RCA.md, sebelum menulis brief perbaikan atau menyentuh src/
---

## THE IRON LAW

- Perlakukan `src/` sebagai read-only mutlak: skill ini membuktikan penyebab, bukan memperbaikinya.
- Dilarang menyatakan root cause tanpa minimal satu bukti `file:line` konkret dan satu hipotesis alternatif yang terfalsifikasi eksplisit.
- Hipotesis yang belum diuji adalah dugaan dan dilarang naik menjadi temuan.
- Terbitkan `RCA.md` meskipun hasilnya `INCONCLUSIVE`, dan dilarang menebak sesudah tiga siklus hipotesis gagal.
- Dilarang menulis brief, memanggil `architect`, atau menjalankan git commit karena keduanya wewenang gerbang lain.

## Precondition [REQUIRED]

1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/debug/scripts/check_preconditions.py --taskdir <taskdir> [--scope-hint <scope_hint>]`. **Jangan pernah menempelkan `symptom` ke baris perintah shell**: stacktrace memuat `$`, backtick, dan kurung yang diekspansi atau dieksekusi shell. Bila gejala perlu disimpan, tulis ke `{taskdir}/.explore/symptom.txt` lewat tool `Write`, bukan `echo`/heredoc.
2. Evaluasi output skrip secara deterministik:
   - `PASS` (7/7 checks): Lanjutkan ke evaluasi parameter dan workflow investigasi RCA.
   - `FAIL`: Hentikan eksekusi segera dan jalankan tindakan remediasi pada butir yang gagal (profil/commands hilang → arahkan ke `backenddev:profile`; repo non-git → jalankan pada repo git aktif; adapter/seksi `## Failure signatures`/template hilang → pulihkan berkas plugin; taskdir tidak dapat diakses → periksa izin direktori; `scope_hint` tidak ada di repo → perbaiki atau kosongkan).

## Parameter [REQUIRED]

- `symptom` — string — `[REQUIRED]` — Stacktrace mentah, pesan exception, status HTTP, nama test merah, atau deskripsi perilaku menyimpang. Hentikan eksekusi dan minta gejala konkret jika parameter kosong atau hanya berisi kalimat umum tanpa gejala terukur ("aplikasi error", "tidak jalan").
- `taskdir` — path — `[REQUIRED]` — Dialokasikan gerbang `backenddev:tech-lead` Fase 3; skill ini tidak memprovisi taskdir sendiri. Wajib cocok pola `backenddev/docs/<YYMMDDhhmm>-<slug>/`; pola lain ditolak tanpa negosiasi.
- `scope_hint` — path — default: `-` — Package atau berkas yang dicurigai; mempersempit permukaan penelusuran Fase 2 tanpa mengunci kesimpulan Fase 3.

## Workflow

### Fase 0 — Verifikasi Prasyarat & Penerimaan Taskdir

1. Jalankan skrip `check_preconditions.py` dengan parameter `taskdir` dan `scope_hint`. Hentikan eksekusi segera jika skrip menghasilkan `FAIL`. Kelayakan `symptom` (tidak kosong, memuat gejala terukur) dinilai di butir ini secara langsung, bukan oleh skrip.
2. Gunakan ulang direktori yang ditunjuk `taskdir`. Hentikan eksekusi jika `taskdir` kosong dan minta alokasinya dari gerbang `backenddev:tech-lead` Fase 3; hentikan juga jika `taskdir` diisi tetapi tidak ada di disk. Dilarang mengarang atau mengalokasikan direktori pengganti — akar rantai `TASK.md` lahir di gerbang, bukan di sini.
3. Evaluasi berkas `{taskdir}/RCA.md` jika sudah ada di disk:
   - Status `ROOT_CAUSE_CONFIRMED`: Laporkan artefak eksisting dan hentikan eksekusi.
   - Status `INCONCLUSIVE`: Lanjutkan dari `## Hipotesis terfalsifikasi` yang sudah tercatat; dilarang mengulang siklus yang sudah gugur.
4. Dilarang membuat atau berpindah branch — isolasi branch adalah wewenang mutlak gerbang `backenddev:tech-lead`.

### Fase 1 — Normalisasi Gejala & Konfirmasi Reproduksi

0. Baca `stack` dari `.claude/profile/backenddev/index.json`, lalu seksi `## Failure signatures` adapter `../profile/stacks/<stack>.md`: format stacktrace, frame paling informatif, dan pola akar masalah lazim di stack ini. Pakai ketiganya saat memecah gejala (butir 1) dan sebagai kandidat hipotesis Fase 3; pola yang dipakai disebut sumbernya.
1. Pecah `symptom` menjadi empat fakta terpisah: exception class atau kode status, frame terdalam milik `root_namespace`, waktu/kondisi kemunculan, dan cakupan dampak (satu user, satu endpoint, atau seluruh instans).
2. Tandai gejala sebagai kegagalan lapisan framework atau dependensi jika stacktrace tidak memuat satu pun frame di bawah `root_namespace`, dan jadikan itu hipotesis H1 alih-alih menelusuri kode aplikasi lebih dulu.
3. Susun langkah reproduksi kandidat: perintah test, request HTTP dengan payload, atau kondisi data yang memicu. Sajikan ke user dan minta konfirmasi eksplisit bahwa langkah tersebut memunculkan gejala.
4. Tangani hasil konfirmasi reproduksi:
   - Konfirmasi user positif: Catat sebagai reproduksi terverifikasi.
   - Konfirmasi user negatif (tidak dapat direproduksi): Lanjutkan berlabel `reproduksi: tidak tersedia`. Bukti Fase 3 kemudian bersandar penuh pada pembacaan kode dan log, dan status terminal dibatasi maksimal `ROOT_CAUSE_CONFIRMED` hanya bila rantai kausalnya utuh tanpa celah.
5. Dilarang melanjutkan ke Fase 2 sebelum langkah reproduksi dijawab oleh user.

### Fase 2 — Lokalisasi Permukaan Kegagalan

1. Tetapkan permukaan awal dari frame terdalam milik `root_namespace`, dipersempit `scope_hint` jika terisi.
2. Muat template `dispatcher/explorer.md`, hidrasi slot `{objective}`, `{permukaan_awal}`, `{taskdir}`, `{konteks_diketahui}`, `{batas_cakupan}`, dan `{slug}` — `{slug}` juga menamai berkas laporan `{taskdir}/.explore/{slug}.md` — lalu berangkatkan prompt itu beserta blok `Format laporan`-nya utuh dan panggil subagent `code-explorer` secara langsung jika permukaan menyentuh lebih dari satu package, rantai pemanggil belum jelas, atau batas transaksi perlu ditelusuri. Petakan balikannya lewat `### Penanganan Balikan` template itu. Dilarang memanggil subagent lewat jalur lain.
3. Baca berkasnya langsung tanpa dispatch jika permukaan terlokalisasi dalam satu berkas dan alurnya terbaca jelas.
4. Kumpulkan konteks pendukung yang dapat diperiksa: anotasi transaksi, konfigurasi wiring komponen, urutan validasi, mapping ORM, atau properti profil aktif yang menyentuh permukaan itu.
5. Susun daftar kandidat lokasi bertanda `file:line`. Buang kandidat tanpa `file:line` konkret; dilarang menurunkan derajatnya.

### Fase 3 — Siklus Hipotesis & Falsifikasi

Jalankan maksimal tiga siklus. Tuntaskan tiap siklus secara penuh sebelum memulai siklus berikutnya.

1. **Rumuskan**: Tulis hipotesis sebagai proposisi yang dapat dinyatakan salah (misal: "`internal/order/service.go:88` membuka koneksi di luar batas transaksi sehingga rollback tidak menjangkau penulisan kedua di `:104`").
2. **Uji**: Cari bukti pembalik lebih dulu, bukan bukti pendukung. Gunakan hanya tiga sumber sah: pembacaan kode pada `file:line`, keluaran test yang benar-benar dijalankan, dan log dari user. Dilarang mengarang keluaran perintah yang tidak dieksekusi.
3. **Putuskan**:
   - Bukti pembalik ditemukan: Catat hipotesis sebagai terfalsifikasi beserta buktinya, lalu masuk ke siklus berikutnya.
   - Tidak ada bukti pembalik dan rantai kausal tersambung utuh tanpa langkah tak terverifikasi: Naikkan menjadi root cause.
4. Sertakan minimal satu hipotesis alternatif yang sudah terfalsifikasi eksplisit pada root cause. Selesaikan pengujian alternatif sebelum menaikkan kesimpulan.
5. Tetapkan status `INCONCLUSIVE` jika tiga siklus habis tanpa root cause terbukti. Catat ketiga hipotesis beserta alasan gugurnya, dan tulis daftar bukti tambahan yang dibutuhkan. Dilarang menebak kesimpulan.

### Fase 4 — Blast Radius & Spesifikasi Regression Guard

1. Petakan blast radius: pemanggil lain pada `file:line` penyebab, endpoint terdampak, dan data yang berpotensi rusak akibat defect.
2. Susun `## Arah perbaikan` sebagai daftar berkas kandidat beserta sifat perubahannya untuk masukan `File scope` brief. Dilarang menuliskan diff atau kode pengganti utuh.
3. Susun `## Regression guard` sebagai spesifikasi test: nama kelas test, tier test sesuai `## Commands` profil, kondisi arrange, aksi, dan assertion yang akan gagal pada kode saat ini. Dilarang membuat berkas test.
4. Tulis regression guard pada lapisan yang dapat diuji otomatis jika gejala berasal dari konfigurasi atau data, atau tandai `tidak dapat digerbangi test` beserta alasannya.

### Fase 5 — Approval Root Cause & Penerbitan Artefak

1. Sajikan ringkasan ke user: rantai kausal, bukti `file:line`, hipotesis yang gugur, dan arah perbaikan kandidat.
2. Tangani respons user:
   - User menyetujui root cause: Tulis `{taskdir}/RCA.md` mengikuti `templates/rca-template.md` sebagai satu aksi tuntas.
   - User menolak atau menunjuk arah lain: Kembali ke Fase 3 butir 1 dengan hipotesis baru tanpa menambah sisa siklus.
3. Serahkan hasil ke pemanggil tanpa mengeksekusi langkah berikutnya sendiri.

## Guardrails

- Dilarang mengedit, membuat, atau menghapus berkas apa pun di `src/` — termasuk berkas test regression yang dispesifikasikan sendiri.
- Dilarang menulis brief, memanggil `backenddev:plan`, `backenddev:architect`, atau subagent selain `code-explorer`.
- Dilarang menjalankan `git commit`, `git checkout`, `git stash`, atau membuat branch; commit artefak adalah wewenang gerbang `backenddev:tech-lead`.
- Dilarang menjalankan perintah yang memutasi state di luar repo: migrasi database, restart service, atau pemanggilan endpoint non-idempoten ke lingkungan nyata.
- Dilarang menulis ke `backenddev/issues/` — direktori tersebut milik `backenddev:audit`.
- Dilarang menaikkan dugaan menjadi root cause demi menutup sesi; status `INCONCLUSIVE` adalah hasil sah.
- **KEPUTUSAN DEFINITIF SAAT INI**: Seluruh isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
- Keputusan mutlak milik user: kebenaran langkah reproduksi, approval root cause, dan pemilihan arah perbaikan.

## Output [REQUIRED]

Artefak tunggal `{taskdir}/RCA.md` mengikuti `templates/rca-template.md` — seksi wajib, urutannya, dan nilai frontmatter `status` ada di sana. Dilarang menyalinnya ke sini. Sajikan blok berikut dan hapus tiap baris bernilai `—`:

```markdown
### ROOT CAUSE ANALYSIS REPORT — <ROOT_CAUSE_CONFIRMED | INCONCLUSIVE>
- **RCA**       : backenddev/docs/<taskdir>/RCA.md
- **Root cause**: <proposisi satu kalimat + file:line> · blast radius <pemanggil/endpoint/data terdampak> | belum terbukti
- **Bukti dibutuhkan**: <daftar bukti yang menutup celah pembuktian> | —
- **Handoff**   : backenddev:plan entry_mode RCA | kembali ke user
```

`ROOT_CAUSE_CONFIRMED` → rute berikutnya `backenddev:plan` dengan `entry_mode: RCA` lewat gerbang; `## Arah perbaikan` dipanen jadi `## File scope` brief, dan `## Regression guard` jadi kelas test di sana beserta cara deteksi regresi di `## Risk & rollback` — ketiganya dibaca dari `RCA.md`, bukan dari laporan ini, sehingga gejala, reproduksi, dan hipotesis yang gugur tidak disalin ulang. `INCONCLUSIVE` → kembalikan ke user beserta `Bukti dibutuhkan`; dilarang merutekan ke `plan`.

## Failure path

- `symptom` kosong atau tanpa gejala terukur: Hentikan eksekusi di Fase 0, jangan membuat taskdir, minta stacktrace atau langkah pemicu konkret.
- `taskdir` diisi tetapi direktorinya tidak ada: Hentikan eksekusi, laporkan path yang dicari; dilarang mengalokasikan direktori pengganti diam-diam.
- `.claude/profile/backenddev/index.json` hilang atau field wajibnya kosong: Hentikan eksekusi, rutekan ke `backenddev:profile`, dilarang menebak `root_namespace` dari struktur folder.
- `code-explorer` mengembalikan `confidence: low`, payload kosong, atau format rusak: Perbaiki slot `{objective}` menjadi satu pertanyaan bersimbol konkret dan dispatch ulang sekali. Lanjutkan dengan pembacaan kode manual jika balikannya tetap gagal, dan catat keterbatasannya di `## Rantai kausal`.
- Tiga siklus hipotesis habis tanpa rantai kausal utuh: Terbitkan `RCA.md` berstatus `INCONCLUSIVE`.
- Gejala hilang saat reproduksi dicoba (flaky): Catat sebagai defect nondeterministik, jadikan sumber nondeterminisme (concurrency, urutan test, zona waktu, cache) sebagai hipotesis H1, dan jangan menutup sesi berstatus `ROOT_CAUSE_CONFIRMED` tanpa bukti `file:line` konkret.
- Sesi terputus sesudah `RCA.md` ditulis: Baca statusnya di Fase 0 butir 3, lanjutkan dari hipotesis yang sudah gugur, jangan menulis ulang dari awal.

## STYLE

- Gunakan fase bernomor dan kalimat perintah imperatif aktif yang tegas dan to the point tanpa konstruksi bersyarat WHEN/THEN.
- Tulis rantai kausal sebagai urutan sebab-akibat bernomor; tiap mata rantai menyebut `file:line` dan aksi yang terjadi di sana.
- Tulis hipotesis dalam bentuk proposisi yang dapat dinyatakan salah, bukan pertanyaan atau kemungkinan bersyarat.
- Bedakan tegas fakta terverifikasi dari inferensi: fakta menyebut sumbernya, inferensi ditandai eksplisit sebagai inferensi.
- Pertahankan identifier kode, exception class, path, dan istilah domain dalam bahasa Inggris apa adanya; narasi analisis dalam bahasa Indonesia.
- Tulis kalimat imperatif aktif tanpa hedging naratif ("mungkin", "sepertinya") pada seksi yang menyatakan bukti.
