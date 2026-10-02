---
name: elicit
description: Dipanggil analyst:intake sesudah tipe dan slug ditetapkan, atau untuk ticketdir berkeadaan ELISITASI, atau analyst:spec saat fakta tiket perlu digali ulang - tanya-jawab terarah dengan peminta non-engineer (tiket TECH: dengan lead engineer, ditambah pembuktian klaimnya lewat subagent code-scout; tipe lain memakai code-scout hanya sebagai konteks pertanyaan), direkam per pilar ke seksi Catatan Elisitasi TICKET.md tiap giliran, sampai tertutup tanpa pertanyaan memblokir, sebelum analyst:spec menulis kartu tiket di atasnya
user-invocable: false
---

## THE IRON LAW

- Tiap fakta di `## Catatan Elisitasi` berasal dari permintaan asli atau jawaban yang terekam di log. Yang disimpulkan analis ditulis `Asumsi:` dan wajib dikonfirmasi di Phase 4.
- `TICKET.md` ditulis ulang **sesudah tiap giliran tanya-jawab**, bukan di akhir — jawaban yang hanya hidup di percakapan hilang saat sesi berganti.
- Konteks utama tidak membaca kode. Seluruh pembacaan kode lewat subagent `analyst:code-scout` (`dispatcher/scout.md`), maksimal 2 dispatch per sesi. Balikannya bahan bertanya, bukan fakta: hanya tiket `TECH` yang mencatat `path:baris`, dan hanya dari butir `Ditemukan`.
- Maksimal 3 pertanyaan per giliran lewat `AskUserQuestion`; dilarang menanyakan solusi teknis. Tiket `TECH` boleh bertanya teknis, tetapi analyst tetap tidak memilihkan solusi (`references/elicitation-tech.md` bagian 1).
- `elicitation: CLOSED` hanya ditulis `ticket.py close` sesudah konfirmasi fakta Phase 4 — skrip memvonis `validate_doc.py --kind elicit`, menyegel catatan, dan meng-commit. Skill ini hanya menulis frontmatter miliknya dan `## Catatan Elisitasi` di bawah `### Permintaan Asli`; kutipan permintaan asli (dimateraikan `ticket.py new`), kartu di atasnya, `status`, dan `priority` bukan miliknya.

## Precondition [REQUIRED]

1. Skrip: `ticket.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py`; `validate_doc.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`. Template dispatch penelusur kode: `dispatcher/scout.md`.
2. **Tiket baru** (dari intake dengan `slug`, `type`, `request`, `requester`; juga ticketdir `KOSONG`): `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py new --slug <slug> --type <type> [--category <category>] --requester "<requester>" --request - <<'EOF'` (`--category` wajib untuk `TECH` dan ditolak untuk tipe lain), lalu `request` apa adanya, lalu `EOF` → `NEW PASS: <ticketdir> · root=<root> · git=<ya|tidak|diabaikan> · type=<type>[ · category=<category>]`. `git=diabaikan`: ticketdir diabaikan `.gitignore` — tetap di disk, tidak pernah di-commit (repo bersinkron nataflow: `new` menulis `analyst/tickets/.gitignore` bila belum ada); segmen tambahan keluaran `new` disampaikan ke user apa adanya. Skrip menulis `TICKET.md` persis bagian 1 `templates/elicit-template.md` — permintaan asli sebagai blockquote beserta `request_hash`, seluruh pilar `_(belum terjawab)_` — dan memakai ulang ticketdir `KOSONG` ber-slug sama. `FAIL` slug kembar → kembali ke `analyst:intake` Phase 1.
3. **Ticketdir ada** (`ELISITASI` atau buka ulang): `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py check --gate elicit --ticketdir <ticketdir>` (tambah `--reopen` bila `reopen_reason` terisi). `PASS` → catat `root=` dan `git=` dari baris `Terselesaikan:` lalu lanjut. `FAIL` → remediasi per baris `Tindakan`; tiket `READY` dibuka ulang hanya lewat `analyst:spec`.

## Parameter [REQUIRED]

- `ticketdir` — string — default `""` — ticketdir yang dilanjutkan; kosong berarti tiket baru.
- `slug`, `type` — string — `[REQUIRED]` bila `ticketdir` kosong atau berkeadaan `KOSONG` — hasil `analyst:intake` (`slug` ticketdir `KOSONG` dibaca dari namanya).
- `category` — string — `[REQUIRED]` bila `type` = `TECH` dan ticketdir baru — hasil `analyst:intake` Phase 3.
- `request` — string — `[REQUIRED]` bila `ticketdir` kosong atau berkeadaan `KOSONG` — permintaan asli apa adanya.
- `requester` — string — `[REQUIRED]` bila `ticketdir` kosong atau berkeadaan `KOSONG` — nama/peran peminta; `ticket.py new` menolak nilai kosong.
- `reopen_reason` — string — default `""` — alasan `analyst:spec` mengembalikan elisitasi yang sudah `CLOSED`.

## Workflow

### Phase 0 — Alokasi atau Lanjutan

- **Baru** (termasuk ticketdir `KOSONG`): `TICKET.md` sudah ditulis `ticket.py new` (Precondition 2) dengan `elicitation: OPEN`; dilarang menulis kerangkanya dengan tangan. Baca berkasnya, lalu Phase 1.
- **Lanjutan** (`ELISITASI`): baca `TICKET.md` utuh. Ada `Q-{n}` `menunggu:` orang lain → tanyakan lewat `AskUserQuestion` apakah jawabannya sudah tersedia; ya → catat, tidak → lompat ke pilar yang belum terjawab tanpa `menunggu`.
- **Buka ulang** (`reopen_reason`): set `elicitation: OPEN` (kartu yang sudah ada dibiarkan untuk `spec`), tambahkan baris log `| n | <tanggal> | Dibuka ulang | <reopen_reason> | analyst:spec |` — `ticket.py close` menolak menutup ulang catatan yang berubah sejak segel terakhir tanpa baris ini — lalu gali hanya pilar yang disebut alasannya.

### Phase 1 — Isi dari Permintaan

**Tiket `TECH`**: baca `references/elicitation-tech.md` saja (rubrik urgensi tetap bagian 4 `references/elicitation-guide.md`) dan jalankan mode ringkasnya (bagian 2): petakan brief peminta ke pilar, dispatch `analyst:code-scout` `mode: BUKTI` (`dispatcher/scout.md`) dengan klaim kondisi sekarang, catat `` `path:baris` `` butir `Ditemukan` di `Kondisi Saat Ini`, tulis `TICKET.md`, lalu Phase 2 hanya untuk celahnya: butir `Tidak ditemukan`, `Belum disisir`, dan klaim yang dibantah kode. Kalimat sesudah ini berlaku untuk tipe lain.

Baca `references/elicitation-guide.md` dan `references/literasi-teknis.md`. Isi tiap pilar yang sudah dijawab permintaan asli. Fakta tersurat ditulis langsung; fakta tersirat ditulis `Asumsi: <...>`. `Kondisi Diinginkan` diawali baris `Bentuk hasil:` (panduan bagian 6). Istilah teknis yang diucapkan peminta dirumuskan ulang sebagai perilaku (panduan bagian 3); istilah yang memang kosakata produk dikonfirmasi ke peminta — konfirmasinya dicatat sebagai baris log (`| n | <tanggal> | Apakah "<istilah>" nama produk? | Ya | <peminta> |`, atau untuk bentuk hasil API baris panduan bagian 6) — lalu dicatat di frontmatter `domain_terms`. `CLOSED` menuntut tiap istilah `domain_terms` punya baris konfirmasi berjawaban *Ya* yang mengutip istilahnya; kemunculan di permintaan asli saja tidak cukup. Tulis `TICKET.md`.

**Konteks kode** (tipe selain `TECH`): bila permintaan menyebut layar, menu, laporan, status, atau data yang mungkin sudah ada, dispatch `analyst:code-scout` `mode: KONTEKS` (`dispatcher/scout.md`) dengan 1–5 konsep itu dalam kata-kata peminta. Temuannya dipakai sebagai bahan opsi pertanyaan Phase 2 dalam bahasa yang terlihat pengguna, atau sebagai baris `Asumsi:` tanpa rujukan berkas yang dikonfirmasi di Phase 4. Temuan scout dilarang ditulis sebagai fakta pilar, dan `path:baris` dilarang disalin ke catatan (`validate_doc.py --kind elicit` menolaknya). Ruang kerja tanpa kode atau scout gagal → lanjut tanpa konteks kode.

### Phase 2 — Giliran Tanya-Jawab

1. Pilih ≤ 3 pilar wajib yang belum terjawab, urut dampak: `FEATURE`/`IMPROVEMENT` — Masalah → Aktor → Kondisi Diinginkan → Aturan Bisnis → Batas Cakupan → Urgensi → Kondisi Saat Ini; `BUG` — Langkah Reproduksi → Yang Terjadi → Yang Diharapkan → Dampak → Urgensi; `TECH` — Masalah Teknis → Kondisi Saat Ini → Kondisi Target → Batasan → Batas Cakupan → Urgensi, ditambah yang wajib tergali untuk `category`-nya (`references/elicitation-tech.md` bagian 4).
2. `AskUserQuestion`: satu pertanyaan per pilar, 2–4 opsi konkret beserta konsekuensi bisnisnya (aturan bertanya: panduan bagian 2). Pertanyaan pilar `Aktor`, `Aturan Bisnis`, `Kondisi Diinginkan`, dan `Kasus Khusus` dipilih dari `references/literasi-teknis.md` — hanya konsep yang disentuh permintaan dan bentuk hasilnya. Opsi boleh bertumpu pada temuan scout `KONTEKS` ("Layar daftar invoice sudah punya saringan status. Tambah saringan tanggal di sana, atau layar baru?"), tetap tanpa nama berkas atau istilah sistem. Tiket `TECH` tidak memakai `literasi-teknis.md`: opsinya alternatif teknis beserta konsekuensinya, dan klaim yang tidak cocok dengan kode diajukan berdampingan dengan buktinya.
3. **Sesudah tiap giliran**: tambahkan baris log per jawaban (sumber = `requester` atau nama yang disebut user), perbarui pilar, tulis `TICKET.md`, jalankan `validate_doc.py --kind elicit --ticketdir <ticketdir>` — `elicitation: OPEN` boleh menyisakan pilar belum terjawab, tetapi struktur wajib `PASS`.
4. Jawaban "tidak tahu" atau "tanya si X" → `- **Q-{n}** [MEMBLOKIR | TIDAK MEMBLOKIR]: <pertanyaan> — menunggu: <siapa>` (butir 12 template menentukan labelnya), lanjut ke pilar lain.
5. Ulangi sampai seluruh pilar wajib terisi atau yang tersisa hanya pertanyaan `menunggu`. **Plafon 5 giliran per sesi**: habis → simpan, commit tertunda (Phase 5 butir 3), dan sajikan blok `TERTAHAN`.
6. Jawaban memunculkan klaim kode baru (`TECH`) atau konsep baru yang mungkin sudah ada (tipe lain), atau balikan scout menyisakan `Belum disisir` → satu dispatch susulan bila plafon 2 per sesi masih tersisa; selain itu tanyakan ke peminta.
7. Jawaban memunculkan tujuan pengguna kedua yang dapat dirilis terpisah → panduan bagian 5: tanyakan mana yang dikerjakan, catat sisanya di `Batas Cakupan` `— tiket terpisah`.

### Phase 3 — Pilar Opsional

Satu giliran untuk pilar opsional tipe itu. User menolak atau tidak relevan → `Tidak dibahas — <alasan>`. Pilar opsional tidak pernah menahan penutupan.

### Phase 4 — Konfirmasi Fakta

Ini **konfirmasi fakta, bukan persetujuan tiket** — persetujuan hanya di `analyst:spec`.

1. Sajikan ringkas per pilar: bentuk hasil, aktor beserta larangannya, angka dan ambang tiap aturan, batas cakupan, urgensi, tiap baris `Asumsi:`, dan pertanyaan terbuka yang tersisa. Tiket `TECH`: kondisi sekarang beserta jumlah bukti `path:baris`, kondisi target, batasan, keputusan, batas cakupan, urgensi, tiap `Asumsi:`, dan pertanyaan terbuka.
2. `AskUserQuestion`: *Fakta sudah benar* · *Ada koreksi (sebut)* · *Tunda — tunggu jawaban pihak lain*.
3. Koreksi → catat di log, perbarui pilar, ulangi Phase 4. Asumsi yang dikonfirmasi → hapus label `Asumsi:` (validator menolak `CLOSED` selama `Asumsi:` masih muncul di mana pun dalam `### Fakta`, termasuk di tengah kalimat); yang ditolak → kembali ke Phase 2 untuk pilar itu. Tunda → blok `TERTAHAN`.

### Phase 5 — Tutup & Serah Terima

1. Pertanyaan `MEMBLOKIR` masih ada → dilarang menutup; blok `TERTAHAN` beserta daftar pertanyaan siap diteruskan.
2. Self-test semantik butir 10–15 template, lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py close --ticketdir <ticketdir>`. Skrip menulis `elicitation: CLOSED` hanya bila `validate_doc.py --kind elicit` `PASS` (bila tidak, berkas dikembalikan apa adanya dan laporan validator dicetak), menyegel catatan (`elicit_hash`, `elicit_log`), dan di repo git meng-commit `docs(ticket): elisitasi <slug>` (`commit diabaikan git` bila ticketdir diabaikan `.gitignore`). Dilarang menulis `elicitation: CLOSED` dengan tangan: `analyst:spec` menolak catatan tanpa segel.
3. Exit 3 (`COMMIT GAGAL`) → `CLOSED` sudah tertulis; sajikan barisnya apa adanya (Failure path 5). Draft yang **tertahan** di-commit lewat `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py commit --ticketdir <ticketdir> --stage tertunda` (subjek `docs(ticket): elisitasi <slug> (tertunda)`, staging path eksplisit); dilarang `git add`/`git commit` dengan tangan. Bukan repo git (`tanpa git`) atau ticketdir diabaikan `.gitignore` (`commit diabaikan git`) → skrip melewati commit; sebut di Output.
4. Panggil `analyst:spec` dengan `{ ticketdir }`.

## Guardrails

- **FAKTA BUKAN TEBAKAN**: pilar dilarang diisi "yang biasanya berlaku", praktik terbaik, atau perilaku sistem sejenis. Yang tidak dikatakan peminta adalah pertanyaan, bukan fakta.
- **NOL PERTANYAAN TEKNIS** (selain `TECH`): dilarang menanyakan penyimpanan data, integrasi sistem, teknologi, atau struktur layar internal. Pilihan yang **terlihat** pengguna (email atau notifikasi aplikasi, satu layar atau dua langkah) boleh ditanyakan.
- **BAHASA PEMINTA**: istilah bisnis peminta dipakai apa adanya dan konsisten; dilarang diganti sinonim di pilar lain. Istilah domain dan nama entitas, menu, layar, atau kolom berbahasa Inggris (*Report Order*, *Created At*) tidak diterjemahkan ke Bahasa Indonesia (panduan bagian 3).
- **SIMPAN TIAP GILIRAN**: tulis `TICKET.md` sesudah tiap giliran, sebelum pertanyaan berikutnya.
- **KODE SEBAGAI KONTEKS** (selain `TECH`): kode menunjukkan apa yang ada, bukan apa yang diinginkan peminta. Temuan `code-scout` hanya mempertajam pertanyaan atau menjadi `Asumsi:` yang dikonfirmasi; `Kondisi Saat Ini` tetap diceritakan peminta. `path:baris` dilarang di catatan non-`TECH`.
- **KODE LEWAT SCOUT** (semua tipe): konteks utama dilarang memakai `Read`/`Grep`/`Glob` atas kode repo; pembacaan kode hanya lewat `analyst:code-scout`, maksimal 2 dispatch per sesi. Bukti `TECH` hanya dari butir `Ditemukan` balikan scout; dilarang menyunting kode atau menulis bukti yang tidak ada di balikan.
- **KUTIPAN PERMINTAAN TETAP**: `### Permintaan Asli` dimateraikan `request_hash` oleh `ticket.py new`; saat menulis ulang berkas tiap giliran, salin kutipan itu byte demi byte. Keterangan baru dari peminta masuk log, bukan ke kutipan.
- **SATU TIKET SATU ELISITASI**: dilarang menulis atau menyunting kartu di atas `## Catatan Elisitasi`, menyusun acceptance criteria, atau menanyakan "setuju dengan tiketnya?".
- **RATIONALIZATION PREVENTION**:
  - "Aturannya pasti begini, tidak perlu ditanya" — aturan yang ditebak lolos ke tiket sebagai kebutuhan palsu dan dibangun engineer.
  - "Sisa pertanyaannya sedikit, tutup saja dengan asumsi" — pertanyaan memblokir mengubah aturan tiket; menutupnya dengan asumsi memindahkan tebakan ke engineer.
  - "Saya tanya 6 hal sekaligus biar cepat" — kuesioner panjang menghasilkan jawaban dangkal; 3 per giliran.
  - "Nanti saja ditulis ke berkas" — sesi terputus menghapus semua jawaban yang belum tertulis.
  - "Scout sudah menemukannya, tulis saja sebagai fakta" (selain `TECH`) — kode menunjukkan yang ada, bukan yang dibutuhkan peminta; fakta yang tidak pernah dikonfirmasi peminta lolos ke tiket sebagai kebutuhan palsu.
  - "Lead engineer pasti benar, buktinya tidak perlu dicek" (`TECH`) — bukti yang tidak dibaca lolos ke tiket sebagai kondisi palsu; validator kartu menolak `path:baris` yang tidak ada.
  - "Validator sudah PASS, `elicitation: CLOSED` saya tulis sendiri" — tanpa segel `close`, suntingan catatan sesudahnya tidak terdeteksi dan `analyst:spec` menolak masuk.

## Output [REQUIRED]

Elisitasi tertutup → tutup satu baris: `ELICIT — CLOSED · <ticketdir> · <n> pilar · <n> log · <n> Q tidak memblokir · <commit <sha> | tanpa git | diabaikan git> — lanjut ke analyst:spec.` Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### ELICIT — TERTAHAN
- **Ticketdir**: <path> · elicitation OPEN · <commit <sha> | tanpa git | diabaikan git>
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
5. **Commit gagal** (`close` atau `commit --stage tertunda` exit 3: hook, gpg, index terkunci): biarkan berkas tertulis, sertakan galat mentah di Output; dilarang `--no-verify`/`--no-gpg-sign`, `git add .`, atau `git add -f` atas path yang diabaikan `.gitignore`.
6. **Scout gagal** (balikan kosong, tanpa blok `## Code Scout`, atau error): ulangi sekali (tidak dihitung plafon). Gagal lagi, atau `Repo: tanpa kode`: tipe selain `TECH` → lanjut tanpa konteks kode; `TECH` → blok `TERTAHAN` dengan sebab "bukti kode tidak dapat dikumpulkan" (tiket `TECH` wajib tinggal di repo yang diubah).

## STYLE

- Imperatif aktif; pertanyaan ke user berbahasa sehari-hari, tanpa jargon sistem.
- Pilar ditulis sebagai kalimat fakta masa kini, bukan kutipan percakapan.
