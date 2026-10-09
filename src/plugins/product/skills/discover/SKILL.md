---
name: discover
description: Dipanggil product:init sesudah mode, slug, dan konteks minimum lolos guard, atau untuk charterdir berkeadaan ELICITATION, atau product:spec saat fakta charter perlu digali ulang - alokasi CHARTER.md lewat charter.py new, lalu tanya-jawab terarah per pilar (Purpose, Actors, Business Process, Business Rules, Scope, Success Criteria) dengan bank pertanyaan per mode; mode NEW_FEATURE dan IMPROVEMENT memetakan kondisi sekarang lewat subagent code-scout berbukti path:baris; direkam ke Catatan Elisitasi tiap giliran sampai tertutup tanpa pertanyaan memblokir, sebelum product:spec menulis kartu enam pilar
user-invocable: false
---

## THE IRON LAW

- Tiap fakta di `## Catatan Elisitasi` berasal dari permintaan asli, Konteks Awal, atau jawaban yang terekam di log.
  Yang disimpulkan analis — termasuk temuan `code-scout` — ditulis `Asumsi:` dan wajib dikonfirmasi di Phase 4.
- `CHARTER.md` ditulis ulang **sesudah tiap giliran tanya-jawab**, bukan di akhir.
- Konteks utama tidak membaca kode. Pembacaan kode hanya lewat `product:code-scout` (`dispatcher/scout.md`), dan
  `NEW_PRODUCT` tidak pernah mendispatch scout.
- Maksimal 3 pertanyaan per giliran lewat `AskUserQuestion`; dilarang menanyakan solusi teknis.
- Status `DRAFT` (elisitasi tertutup) hanya ditulis `charter.py close` sesudah konfirmasi fakta Phase 4. Skill ini
  hanya menulis H1 kerja dan isi `### Fakta`, `### Log Tanya-Jawab`, `### Pertanyaan Terbuka`; Konteks Awal dan
  Permintaan Asli dimateraikan `charter.py new`, frontmatter milik skrip.

## Precondition [REQUIRED]

1. Skrip: `charter.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py`; `validate_doc.py` =
   `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`. Kerangka dan aturan catatan: `templates/charter-skeleton.md`.
   Panduan: `references/elicitation-guide.md`. Dispatch scout: `dispatcher/scout.md`.
2. **Charter baru** (dari init): jalankan
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py new --slug <slug> --mode <mode> --untuk "<untuk>" --masalah "<masalah>" --lingkup "<lingkup>" --requester "<requester>" --title "<title>" [--confirm-workspace] --request - <<'EOF'`,
   lalu `request` apa adanya, lalu `EOF` → `NEW PASS: <charterdir> · root=<root> · git=<ya|tidak|diabaikan> ·
   mode=<mode> · workspace=<EMPTY|CODEBASE>`. Skrip menjalankan ulang guard konteks minimum dan kecocokan mode
   dengan ruang kerja, lalu menulis `CHARTER.md` persis bagian 1 template. `NEW FAIL` konteks atau mode → kembali ke
   `product:init` Phase 4–5; slug kembar → `product:init` Phase 1.
3. **Charterdir ada** (`ELICITATION`): `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py check --gate discover --charterdir <charterdir>`.
   `PASS` → catat `root`, `git`, dan `mode` dari baris `Terselesaikan:`. `FAIL` → remediasi per `Tindakan`; charter
   tertutup dibuka ulang hanya lewat `product:spec` (`charter.py reopen --to elicitation`).

## Parameter [REQUIRED]

- `charterdir` — string — default `""` — charterdir yang dilanjutkan; kosong berarti charter baru.
- `mode`, `slug`, `title`, `untuk`, `masalah`, `lingkup`, `request`, `requester` — string — `[REQUIRED]` bila
  `charterdir` kosong — hasil `product:init`.
- `confirm_workspace` — bool — default `false` — `NEW_PRODUCT` di ruang kerja ber-kode yang dikonfirmasi user.
- `scout_awal` — string — default `""` — balikan `CEK_FITUR` dari `product:init`, bila ada.
- `reopen_reason` — string — default `""` — alasan `product:spec` membuka ulang elisitasi (baris log `Dibuka ulang`
  sudah ditulis `charter.py reopen`).

## Workflow

### Phase 0 — Alokasi atau Lanjutan

- **Baru**: Precondition 2; baca berkas hasil `new`, lalu Phase 1.
- **Lanjutan**: baca `CHARTER.md` utuh. Ada `Q-n` `menunggu:` orang lain → tanyakan lewat `AskUserQuestion` apakah
  jawabannya sudah tersedia; ya → catat, tidak → lompat ke pilar yang belum terjawab.
- **Buka ulang** (`reopen_reason`): gali hanya pilar yang disebut alasannya; kartu yang sudah ada dibiarkan untuk
  `spec`.

### Phase 1 — Isi dari Permintaan & Peta Kode

1. Baca `references/elicitation-guide.md` dan bagian 2 template. Isi tiap pilar yang sudah dijawab permintaan asli
   atau Konteks Awal; fakta tersirat ditulis `Asumsi: <...>`.
2. **Mode codebase**: dispatch `product:code-scout` `mode: PETA` per `dispatcher/scout.md` — `IMPROVEMENT` tiga
   fokus (`Actors`, `Business Process`, `Business Rules`) dalam satu pesan; `NEW_FEATURE` fokus `Actors`, ditambah
   `Business Process` bila `--lingkup` menyebut area yang sudah ada. Pakai `scout_awal` sebagai titik masuk. Temuan
   `Ditemukan` yang relevan ditulis ke pilarnya sebagai `Asumsi: <kalimat dalam bahasa pengguna> `` `path:baris` ``.
3. Tulis `CHARTER.md`, lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind notes --charterdir <charterdir>`
   — selama `ELICITATION`, pilar belum terjawab sah, tetapi struktur wajib `PASS`.

### Phase 2 — Giliran Tanya-Jawab

1. Pilih ≤ 3 pilar yang belum terjawab, urut bagian 1 panduan.
2. `AskUserQuestion` per bagian 2 panduan, memakai bank pertanyaan mode ini (bagian 4–6). Asumsi dari scout diajukan
   sebagai opsi konfirmasi ("Saat ini ... — tetap, atau berubah?").
3. **Sesudah tiap giliran**: tambahkan baris log per jawaban (sumber = `requester` atau nama yang disebut user),
   perbarui pilar, tulis `CHARTER.md`, jalankan `validate_doc.py --kind notes` sampai struktur `PASS`.
4. Ulangi sampai keenam pilar terjawab (bagian 3 panduan) atau yang tersisa hanya pertanyaan `menunggu`.
   **Plafon 6 giliran per sesi**: habis → simpan, commit tertunda (Phase 5 butir 3), sajikan blok `TERTAHAN`.
5. Jawaban memunculkan konsep yang mungkin sudah ada di kode, atau balikan scout menyisakan `Belum disisir` → satu
   dispatch susulan per `dispatcher/scout.md`; selain itu tanyakan ke peminta.
6. Jawaban memunculkan inisiatif kedua → bagian 7 panduan.

### Phase 3 — Bentuk Akhir Pilar

Sebelum konfirmasi, rapikan tiap pilar menjadi kalimat fakta masa kini yang siap dipetakan `spec`:

- **Actors** (mode codebase): tiap peran ditandai sudah ada atau baru, sesuai temuan scout yang dikonfirmasi.
- **Business Process** (`IMPROVEMENT`): dua paragraf berlabel `Kondisi sekarang:` (berbukti `path:baris` dari scout)
  dan `Kondisi target:`.
- **Business Rules** (`IMPROVEMENT`): tiap aturan diberi keterangan tetap, ubah, atau baru.

### Phase 4 — Konfirmasi Fakta

Ini **konfirmasi fakta, bukan persetujuan charter** — persetujuan hanya di `product:spec`.

1. Sajikan ringkas per pilar: masalah dan untuk siapa, aktor beserta larangannya, alur utama, angka dan ambang tiap
   aturan, batas versi pertama, ukuran sukses, tiap baris `Asumsi:`, dan pertanyaan terbuka yang tersisa.
2. `AskUserQuestion`: *Fakta sudah benar* · *Ada koreksi (sebut)* · *Tunda — tunggu jawaban pihak lain*.
3. Koreksi → catat di log, perbarui pilar, ulangi Phase 4. Asumsi yang dikonfirmasi → hapus label `Asumsi:`
   (rujukan `path:baris`-nya tetap); yang ditolak → kembali ke Phase 2 untuk pilar itu. Tunda → blok `TERTAHAN`.

### Phase 5 — Tutup & Serah Terima

1. Pertanyaan `MEMBLOKIR` masih ada → dilarang menutup; blok `TERTAHAN` beserta daftar pertanyaan siap diteruskan.
2. Self-test semantik butir 11–17 template, lalu
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py close --charterdir <charterdir>`. Skrip menulis
   `status: DRAFT` hanya bila `validate_doc.py --kind notes` `PASS` (bila tidak, berkas dikembalikan dan laporan
   validator dicetak), menyegel catatan, dan di repo git meng-commit `docs(product): elisitasi <slug>`.
3. Exit 3 (`COMMIT GAGAL`) → status sudah tertulis; sajikan barisnya apa adanya. Elisitasi **tertahan** di-commit lewat
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py commit --charterdir <charterdir> --stage tertunda`;
   dilarang `git add`/`git commit` dengan tangan. Tanpa git → skrip melewati commit; sebut di Output.
4. Panggil `product:spec` dengan `{ charterdir }`.

## Guardrails

- **FAKTA BUKAN TEBAKAN**: pilar dilarang diisi "yang biasanya berlaku", praktik terbaik, atau perilaku produk
  sejenis. Yang tidak dikatakan peminta adalah pertanyaan, bukan fakta.
- **KODE SEBAGAI KONDISI SEKARANG, BUKAN KEINGINAN**: temuan scout menunjukkan yang ada, bukan yang diinginkan
  peminta. Ia masuk catatan hanya sebagai `Asumsi:` yang kemudian dikonfirmasi; `path:baris` hanya dari butir
  `Ditemukan` balikan scout, dilarang ditulis dari ingatan.
- **NEW_PRODUCT TANPA KODE**: dilarang mendispatch scout atau menulis `path:baris`; validator menolaknya.
- **SIMPAN TIAP GILIRAN**: tulis `CHARTER.md` sesudah tiap giliran, sebelum pertanyaan berikutnya.
- **KUTIPAN DAN KONTEKS TETAP**: `### Konteks Awal` dan `### Permintaan Asli` dimateraikan `charter.py new`; saat
  menulis ulang berkas, salin keduanya byte demi byte. Keterangan baru masuk log.
- **SATU CHARTER SATU ELISITASI**: dilarang menulis kartu enam pilar di atas `## Catatan Elisitasi` atau menanyakan
  "setuju dengan charternya?".
- **RATIONALIZATION PREVENTION**:
  - "Scout sudah menemukan perannya, tulis saja sebagai fakta" — peran yang ada di kode belum tentu peran yang
    dimaksud peminta; tanpa konfirmasi, charter mengunci kondisi yang mungkin justru ingin diubah.
  - "Success Criteria-nya jelas kok, 'pengguna puas'" — tanpa angka, tidak ada yang bisa menyatakan solusi sudah
    benar; tanyakan angkanya, atau `Q-n` `MEMBLOKIR`.
  - "Semua yang disebut masuk versi pertama saja" — versi pertama yang tidak dibatasi tidak pernah selesai; Scope
    wajib punya daftar tidak termasuk.
  - "Sisa pertanyaannya sedikit, tutup saja dengan asumsi" — validator menolak `Asumsi:` pada catatan tertutup, dan
    tebakan itu pindah ke engineer.

## Output [REQUIRED]

Elisitasi tertutup → satu baris: `DISCOVER — CLOSED · <charterdir> · <mode> · <n> log · <n> Q tidak memblokir ·
scout <n dispatch | -> · <commit <sha> | tanpa git | diabaikan git> — lanjut ke product:spec.` Selain itu sajikan
blok berikut dan hapus baris bernilai `—`:

```markdown
### DISCOVER — TERTAHAN
- **Charterdir**: <path> · ELICITATION · <commit <sha> | tanpa git | diabaikan git>
- **Pilar terjawab**: <n>/6 — belum: <daftar>
- **Menunggu jawaban**:
  - Q-<n> (<siapa>): <pertanyaan dalam kalimat siap diteruskan lewat chat/email>
- **Sebab lain**: <plafon giliran | bukti kode tidak dapat dikumpulkan | ...> | —
- **Lanjutkan dengan**: `product:init` (charterdir terbaca ELICITATION)
```

## Failure path

1. **`charter.py new` gagal**: konteks atau mode → `product:init` Phase 4–5; slug kembar → `product:init` Phase 1;
   `--request`/`--requester` kosong → minta ke user; izin → laporkan galat OS.
2. **Jawaban bertentangan** dengan fakta sebelumnya: sajikan keduanya berdampingan lewat `AskUserQuestion`, catat yang
   dipilih, tandai yang lama di log `(dikoreksi di #n)`.
3. **Validator `FAIL`** (termasuk `CLOSE FAIL` yang mencetak laporan validator): perbaiki per baris `Tindakan`;
   `Konteks Awal berubah` atau `Permintaan Asli berubah` → pulihkan teks aslinya dari git.
4. **Scout gagal dua kali**: `NEW_FEATURE` → lanjut tanpa peta kode; `IMPROVEMENT` → blok `TERTAHAN` dengan sebab
   "bukti kode tidak dapat dikumpulkan".
5. **Commit gagal** (exit 3): biarkan berkas tertulis, sertakan galat mentah; dilarang `--no-verify` atau
   `git add -f`.

## STYLE

- Imperatif aktif; pertanyaan ke user berbahasa sehari-hari, tanpa jargon sistem.
- Pilar ditulis sebagai kalimat fakta masa kini, bukan kutipan percakapan.
