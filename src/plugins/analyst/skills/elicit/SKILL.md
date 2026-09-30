---
name: elicit
description: Dipanggil analyst:intake sesudah tipe dan slug ditetapkan, atau untuk ticketdir berkeadaan ELISITASI, atau analyst:spec saat fakta tiket perlu digali ulang - tanya-jawab terarah dengan peminta non-engineer, direkam per pilar ke seksi Catatan Elisitasi TICKET.md tiap giliran, sampai tertutup tanpa pertanyaan memblokir, sebelum analyst:spec menulis kartu tiket di atasnya
user-invocable: false
---

## THE IRON LAW

- Tiap fakta di `## Catatan Elisitasi` berasal dari permintaan asli atau jawaban yang terekam di log. Yang disimpulkan analis ditulis `Asumsi:` dan wajib dikonfirmasi di Phase 4.
- `TICKET.md` ditulis ulang **sesudah tiap giliran tanya-jawab**, bukan di akhir — jawaban yang hanya hidup di percakapan hilang saat sesi berganti.
- Maksimal 3 pertanyaan per giliran lewat `AskUserQuestion`; dilarang menanyakan solusi teknis.
- `elicitation: CLOSED` hanya ditulis `ticket.py close` sesudah konfirmasi fakta Phase 4 — skrip memvonis `validate_doc.py --kind elicit`, menyegel catatan, dan meng-commit. Skill ini hanya menulis frontmatter miliknya dan `## Catatan Elisitasi` di bawah `### Permintaan Asli`; kutipan permintaan asli (dimateraikan `ticket.py new`), kartu di atasnya, `status`, dan `priority` bukan miliknya.

## Precondition [REQUIRED]

1. Skrip: `ticket.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py`; `validate_doc.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`.
2. **Tiket baru** (dari intake dengan `slug`, `type`, `request`, `requester`; juga ticketdir `KOSONG`): `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py new --slug <slug> --type <type> --requester "<requester>" --request - <<'EOF'`, lalu `request` apa adanya, lalu `EOF` → `NEW PASS: <ticketdir> · root=<root> · git=<ya|tidak> · type=<type>`. Skrip menulis `TICKET.md` persis bagian 1 `templates/elicit-template.md` — permintaan asli sebagai blockquote beserta `request_hash`, seluruh pilar `_(belum terjawab)_` — dan memakai ulang ticketdir `KOSONG` ber-slug sama. `FAIL` slug kembar → kembali ke `analyst:intake` Phase 1.
3. **Ticketdir ada** (`ELISITASI` atau buka ulang): `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py check --gate elicit --ticketdir <ticketdir>` (tambah `--reopen` bila `reopen_reason` terisi). `PASS` → catat `root=` dan `git=` dari baris `Terselesaikan:` lalu lanjut. `FAIL` → remediasi per baris `Tindakan`; tiket `READY` dibuka ulang hanya lewat `analyst:spec`.

## Parameter [REQUIRED]

- `ticketdir` — string — default `""` — ticketdir yang dilanjutkan; kosong berarti tiket baru.
- `slug`, `type` — string — `[REQUIRED]` bila `ticketdir` kosong atau berkeadaan `KOSONG` — hasil `analyst:intake` (`slug` ticketdir `KOSONG` dibaca dari namanya).
- `request` — string — `[REQUIRED]` bila `ticketdir` kosong atau berkeadaan `KOSONG` — permintaan asli apa adanya.
- `requester` — string — `[REQUIRED]` bila `ticketdir` kosong atau berkeadaan `KOSONG` — nama/peran peminta; `ticket.py new` menolak nilai kosong.
- `reopen_reason` — string — default `""` — alasan `analyst:spec` mengembalikan elisitasi yang sudah `CLOSED`.

## Workflow

### Phase 0 — Alokasi atau Lanjutan

- **Baru** (termasuk ticketdir `KOSONG`): `TICKET.md` sudah ditulis `ticket.py new` (Precondition 2) dengan `elicitation: OPEN`; dilarang menulis kerangkanya dengan tangan. Baca berkasnya, lalu Phase 1.
- **Lanjutan** (`ELISITASI`): baca `TICKET.md` utuh. Ada `Q-{n}` `menunggu:` orang lain → tanyakan lewat `AskUserQuestion` apakah jawabannya sudah tersedia; ya → catat, tidak → lompat ke pilar yang belum terjawab tanpa `menunggu`.
- **Buka ulang** (`reopen_reason`): set `elicitation: OPEN` (kartu yang sudah ada dibiarkan untuk `spec`), tambahkan baris log `| n | <tanggal> | Dibuka ulang | <reopen_reason> | analyst:spec |` — `ticket.py close` menolak menutup ulang catatan yang berubah sejak segel terakhir tanpa baris ini — lalu gali hanya pilar yang disebut alasannya.

### Phase 1 — Isi dari Permintaan

Baca `references/elicitation-guide.md` dan `references/literasi-teknis.md`. Isi tiap pilar yang sudah dijawab permintaan asli. Fakta tersurat ditulis langsung; fakta tersirat ditulis `Asumsi: <...>`. `Kondisi Diinginkan` diawali baris `Bentuk hasil:` (panduan bagian 6). Istilah teknis yang diucapkan peminta dirumuskan ulang sebagai perilaku (panduan bagian 3); istilah yang memang kosakata produk dikonfirmasi ke peminta — konfirmasinya dicatat sebagai baris log (`| n | <tanggal> | Apakah "<istilah>" nama produk? | Ya | <peminta> |`, atau untuk bentuk hasil API baris panduan bagian 6) — lalu dicatat di frontmatter `domain_terms`. `CLOSED` menuntut tiap istilah `domain_terms` punya baris konfirmasi berjawaban *Ya* yang mengutip istilahnya; kemunculan di permintaan asli saja tidak cukup. Tulis `TICKET.md`.

### Phase 2 — Giliran Tanya-Jawab

1. Pilih ≤ 3 pilar wajib yang belum terjawab, urut dampak: `FEATURE`/`IMPROVEMENT` — Masalah → Aktor → Kondisi Diinginkan → Aturan Bisnis → Batas Cakupan → Urgensi → Kondisi Saat Ini; `BUG` — Langkah Reproduksi → Yang Terjadi → Yang Diharapkan → Dampak → Urgensi.
2. `AskUserQuestion`: satu pertanyaan per pilar, 2–4 opsi konkret beserta konsekuensi bisnisnya (aturan bertanya: panduan bagian 2). Pertanyaan pilar `Aktor`, `Aturan Bisnis`, `Kondisi Diinginkan`, dan `Kasus Khusus` dipilih dari `references/literasi-teknis.md` — hanya konsep yang disentuh permintaan dan bentuk hasilnya.
3. **Sesudah tiap giliran**: tambahkan baris log per jawaban (sumber = `requester` atau nama yang disebut user), perbarui pilar, tulis `TICKET.md`, jalankan `validate_doc.py --kind elicit --ticketdir <ticketdir>` — `elicitation: OPEN` boleh menyisakan pilar belum terjawab, tetapi struktur wajib `PASS`.
4. Jawaban "tidak tahu" atau "tanya si X" → `- **Q-{n}** [MEMBLOKIR | TIDAK MEMBLOKIR]: <pertanyaan> — menunggu: <siapa>` (butir 12 template menentukan labelnya), lanjut ke pilar lain.
5. Ulangi sampai seluruh pilar wajib terisi atau yang tersisa hanya pertanyaan `menunggu`. **Plafon 5 giliran per sesi**: habis → simpan, commit, dan sajikan blok `TERTAHAN`.
6. Jawaban memunculkan tujuan pengguna kedua yang dapat dirilis terpisah → panduan bagian 5: tanyakan mana yang dikerjakan, catat sisanya di `Batas Cakupan` `— tiket terpisah`.

### Phase 3 — Pilar Opsional

Satu giliran untuk pilar opsional tipe itu. User menolak atau tidak relevan → `Tidak dibahas — <alasan>`. Pilar opsional tidak pernah menahan penutupan.

### Phase 4 — Konfirmasi Fakta

Ini **konfirmasi fakta, bukan persetujuan tiket** — persetujuan hanya di `analyst:spec`.

1. Sajikan ringkas per pilar: bentuk hasil, aktor beserta larangannya, angka dan ambang tiap aturan, batas cakupan, urgensi, tiap baris `Asumsi:`, dan pertanyaan terbuka yang tersisa.
2. `AskUserQuestion`: *Fakta sudah benar* · *Ada koreksi (sebut)* · *Tunda — tunggu jawaban pihak lain*.
3. Koreksi → catat di log, perbarui pilar, ulangi Phase 4. Asumsi yang dikonfirmasi → hapus label `Asumsi:` (validator menolak `CLOSED` selama `Asumsi:` masih muncul di mana pun dalam `### Fakta`, termasuk di tengah kalimat); yang ditolak → kembali ke Phase 2 untuk pilar itu. Tunda → blok `TERTAHAN`.

### Phase 5 — Tutup & Serah Terima

1. Pertanyaan `MEMBLOKIR` masih ada → dilarang menutup; blok `TERTAHAN` beserta daftar pertanyaan siap diteruskan.
2. Self-test semantik butir 10–15 template, lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py close --ticketdir <ticketdir>`. Skrip menulis `elicitation: CLOSED` hanya bila `validate_doc.py --kind elicit` `PASS` (bila tidak, berkas dikembalikan apa adanya dan laporan validator dicetak), menyegel catatan (`elicit_hash`, `elicit_log`), dan di repo git meng-commit `docs(ticket): elisitasi <slug>`. Dilarang menulis `elicitation: CLOSED` dengan tangan: `analyst:spec` menolak catatan tanpa segel.
3. Exit 3 (`COMMIT GAGAL`) → `CLOSED` sudah tertulis; sajikan barisnya apa adanya (Failure path 5). Draft yang **tertahan** di-commit dengan tangan: `git -C <root> add <ticketdir>/TICKET.md` lalu `git -C <root> commit -m "docs(ticket): elisitasi <slug> (tertunda)" -- <ticketdir>/TICKET.md` — `<root>` dari keluaran `new` atau `check`; path ticketdir relatif root, bukan relatif cwd. Bukan repo git → lewati, sebut di Output.
4. Panggil `analyst:spec` dengan `{ ticketdir }`.

## Guardrails

- **FAKTA BUKAN TEBAKAN**: pilar dilarang diisi "yang biasanya berlaku", praktik terbaik, atau perilaku sistem sejenis. Yang tidak dikatakan peminta adalah pertanyaan, bukan fakta.
- **NOL PERTANYAAN TEKNIS**: dilarang menanyakan penyimpanan data, integrasi sistem, teknologi, atau struktur layar internal. Pilihan yang **terlihat** pengguna (email atau notifikasi aplikasi, satu layar atau dua langkah) boleh ditanyakan.
- **BAHASA PEMINTA**: istilah bisnis peminta dipakai apa adanya dan konsisten; dilarang diganti sinonim di pilar lain. Istilah domain dan nama entitas, menu, layar, atau kolom berbahasa Inggris (*Report Order*, *Created At*) tidak diterjemahkan ke Bahasa Indonesia (panduan bagian 3).
- **SIMPAN TIAP GILIRAN**: tulis `TICKET.md` sesudah tiap giliran, sebelum pertanyaan berikutnya.
- **NOL KODE**: dilarang membaca atau mencari kode repo untuk mengisi `Kondisi Saat Ini`; itu diceritakan peminta.
- **KUTIPAN PERMINTAAN TETAP**: `### Permintaan Asli` dimateraikan `request_hash` oleh `ticket.py new`; saat menulis ulang berkas tiap giliran, salin kutipan itu byte demi byte. Keterangan baru dari peminta masuk log, bukan ke kutipan.
- **SATU TIKET SATU ELISITASI**: dilarang menulis atau menyunting kartu di atas `## Catatan Elisitasi`, menyusun acceptance criteria, atau menanyakan "setuju dengan tiketnya?".
- **RATIONALIZATION PREVENTION**:
  - "Aturannya pasti begini, tidak perlu ditanya" — aturan yang ditebak lolos ke tiket sebagai kebutuhan palsu dan dibangun engineer.
  - "Sisa pertanyaannya sedikit, tutup saja dengan asumsi" — pertanyaan memblokir mengubah aturan tiket; menutupnya dengan asumsi memindahkan tebakan ke engineer.
  - "Saya tanya 6 hal sekaligus biar cepat" — kuesioner panjang menghasilkan jawaban dangkal; 3 per giliran.
  - "Nanti saja ditulis ke berkas" — sesi terputus menghapus semua jawaban yang belum tertulis.
  - "Validator sudah PASS, `elicitation: CLOSED` saya tulis sendiri" — tanpa segel `close`, suntingan catatan sesudahnya tidak terdeteksi dan `analyst:spec` menolak masuk.

## Output [REQUIRED]

Elisitasi tertutup → tutup satu baris: `ELICIT — CLOSED · <ticketdir> · <n> pilar · <n> log · <n> Q tidak memblokir · <commit <sha> | tanpa git> — lanjut ke analyst:spec.` Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### ELICIT — TERTAHAN
- **Ticketdir**: <path> · elicitation OPEN · <commit <sha> | tanpa git>
- **Pilar terjawab**: <n>/<n wajib> — belum: <daftar>
- **Menunggu jawaban**:
  - Q-<n> (<siapa>): <pertanyaan dalam kalimat siap diteruskan lewat chat/email>
- **Lanjutkan dengan**: `analyst:intake` (ticketdir terbaca ELISITASI) atau `analyst:elicit` ticketdir <path>
```

## Failure path

1. **`ticket.py new` gagal** (slug kembar terbuka, `--request`/`--requester` kosong, izin tulis): slug kembar → kembali ke intake Phase 1; masukan kosong → minta permintaan asli atau nama peminta ke user; izin → laporkan galat OS.
2. **Peminta tidak dapat dihubungi / menjawab "terserah"**: "terserah" bukan fakta — tawarkan opsi rekomendasi dengan konsekuensinya dan minta dipilih; tetap tidak memilih → `Q-{n}` `MEMBLOKIR`, tahan.
3. **Jawaban bertentangan** dengan fakta sebelumnya: sajikan keduanya berdampingan lewat `AskUserQuestion`, catat yang dipilih, tandai yang lama di log `(dikoreksi di #n)`.
4. **Validator `FAIL`** (termasuk `CLOSE FAIL` yang mencetak laporan validator): perbaiki sesuai baris `Tindakan`; dilarang menutup sebelum `PASS`. `CLOSE FAIL` karena tanpa baris `Dibuka ulang` → catat pembukaan ulang yang benar-benar terjadi beserta alasannya; `Permintaan Asli berubah` → pulihkan kutipan aslinya dari git.
5. **Commit gagal** (`close` exit 3, atau commit tertunda: hook, gpg, index terkunci): biarkan berkas tertulis, sertakan galat mentah di Output; dilarang `--no-verify`/`--no-gpg-sign` atau `git add .`.

## STYLE

- Imperatif aktif; pertanyaan ke user berbahasa sehari-hari, tanpa jargon sistem.
- Pilar ditulis sebagai kalimat fakta masa kini, bukan kutipan percakapan.
