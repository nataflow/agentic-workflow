---
name: spec
description: Dipanggil product:discover sesudah elisitasi tertutup, atau product:init untuk charterdir berkeadaan DRAFT/REVIEW/DRIFT, perubahan charter APPROVED, dan pembatalan charter - menyusun kartu CHARTER.md enam pilar (Purpose, Actors, Business Process, Business Rules, Success Criteria, Scope berID S<n> untuk serah-terima) dari catatan elisitasi dengan bentuk per mode NEW_PRODUCT/NEW_FEATURE/IMPROVEMENT, lolos charter-reviewer dan persetujuan user, sebelum charter dijadikan acuan pemecahan tiket
user-invocable: false
---

## THE IRON LAW

- Kartu disusun **hanya** dari `## Catatan Elisitasi` di berkas yang sama. Yang tidak ada di sana kembali ke
  `product:discover`, tidak dikarang di sini.
- `APPROVED` hanya ditulis `charter.py approve` sesudah jawaban eksplisit user di `AskUserQuestion`; skrip menolak bila
  validator gagal, catatan berbeda dari segel `charter.py close`, atau vonis `charter-reviewer` terakhir bukan `PASS`
  atas sidik kartu **dan** catatan yang sama persis dengan sekarang.
- Bahasa bisnis: kartu menyebut **apa** yang dilakukan dan dilihat pelaku, tidak pernah **bagaimana** sistem dibangun.
- Field frontmatter dan `<charterdir>/review.md` hanya ditulis `charter.py`; saat menulis ulang body, frontmatter
  disalin apa adanya.

## Precondition [REQUIRED]

1. Skrip: `charter.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py`; `validate_doc.py` =
   `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`. Bentuk kartu: `templates/charter-template.md`. Dispatch
   reviewer: `dispatcher/reviewer.md`.
2. **Perubahan charter `APPROVED`/`DRIFT`** (`change_request` terisi atau keadaan `DRIFT`): konfirmasi ke user lewat
   `AskUserQuestion` bahwa charter dibuka ulang. Perubahan yang menambah fakta (aktor, aturan, angka, butir Scope baru)
   → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py reopen --charterdir <charterdir> --to elicitation --reason "<change_request>"`
   lalu `product:discover` dengan `reopen_reason`; perubahan redaksional atau pemindahan butir ke Tidak Termasuk →
   `charter.py reopen ... --to draft --reason "<...>"` lalu lanjut di sini.
3. **Pembatalan** (`cancel_request` terisi): konfirmasi lewat `AskUserQuestion` — charter `APPROVED` mungkin sudah
   menjadi acuan tim — lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py cancel --charterdir <charterdir> --reason "<cancel_request>"`,
   ditambah `--force` hanya untuk charter `APPROVED` yang pembatalannya dikonfirmasi eksplisit. Tutup dengan baris
   `SPEC — BATAL`; Workflow tidak dijalankan.
4. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py check --gate spec --charterdir <charterdir>`. `PASS` →
   baca baris `Terselesaikan:` (`root`, `git`, `mode`, `kartu`, `revision`, `review_round`, `ronde`, `sidik`,
   `review_segar`, `review_basi`, `review_report`). `FAIL` → remediasi per `Tindakan`: keadaan `ELICITATION` →
   `product:discover`; check 5 *catatan berubah sesudah ditutup* → dilarang menyegel ulang dari sini: pulihkan
   catatannya, atau `charter.py reopen --to elicitation` lalu `product:discover`.

## Parameter [REQUIRED]

- `charterdir` — string — `[REQUIRED]` — charterdir aktif.
- `change_request` — string — default `""` — perubahan yang diminta atas charter `APPROVED`, apa adanya.
- `cancel_request` — string — default `""` — alasan pembatalan atas keputusan user, apa adanya.

## Workflow

### Phase 0 — Orientasi

- Baca `CHARTER.md` utuh. `review_segar=ya` (keadaan `REVIEW`, draft yang belum diputuskan) → langsung Phase 5 tanpa
  menulis ulang.
- `review_basi` memuat `elisitasi` (catatan berubah sesudah ronde terakhir, mis. kembali dari elisitasi yang dibuka
  ulang) → `charter.py revise --charterdir <charterdir>` lebih dulu, lalu Phase 1. `review_basi=kartu` → Phase 2 atas
  draft yang ada.

### Phase 1 — Rumusan

Petakan catatan ke kartu persis bagian 1 `templates/charter-template.md` untuk mode itu:

1. **Judul** ≤ 12 kata: `NEW_PRODUCT` — nama atau "<kemampuan inti> untuk <segmen>"; `NEW_FEATURE` — kata kerja +
   kemampuan + area; `IMPROVEMENT` — kata kerja perubahan (Persingkat, Ubah, Perluas, Sederhanakan) + fitur.
2. **Purpose** dari pilar Purpose dan Konteks Awal.
3. **Actors** dari pilar Actors; mode codebase menandai `[ADA]`/`[BARU]` sesuai catatan.
4. **Business Process** dari pilar Business Process; tiap langkah satu aktor, cabang sebagai sub-butir.
   `IMPROVEMENT`: `### Kondisi Sekarang` (bukti `path:baris` disalin persis dari catatan, dilarang menambah bukti
   baru) lalu `### Kondisi Target`.
5. **Business Rules**: tiap aturan pilar menjadi satu `BR-n` beserta pengecualiannya; `IMPROVEMENT` bertanda
   `[TETAP]/[UBAH]/[BARU]` sesuai catatan.
6. **Success Criteria**: tiap ukuran pilar menjadi satu `SC-n` dengan angka dan cara atau waktu ukurnya.
7. **Scope**: tiap butir versi pertama menjadi `S<n>` (satu butir kerja yang dapat dirilis sendiri); yang tidak
   masuk beserta alasannya ke `### Tidak Termasuk`. Charter yang dibuka ulang dari `APPROVED` mempertahankan ID
   `S<n>` lama (bagian 1 template).

### Phase 2 — Tulis Draft

1. Sunting `<charterdir>/CHARTER.md`: ganti H1 kerja dengan judul final dan tulis kartu di antara H1 dan
   `## Catatan Elisitasi`. Seksi catatan dan frontmatter dibiarkan byte demi byte.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind charter --charterdir <charterdir>` sampai
   `PASS`. Bukti kode basi atau hilang → `charter.py reopen --to elicitation --reason "bukti basi: <path:baris>"`.
3. Self-test semantik butir 12–18 template.

### Phase 3 — Review Independen

1. `ronde=habis` → dilarang dispatch; lompat ke Phase 5 dengan BLOCKER tersisa.
2. Muat `dispatcher/reviewer.md`, hidrasi slot (`sidik` diambil dari `check --gate spec` tepat sebelum dispatch), lalu
   dispatch `product:charter-reviewer` langsung.
3. Catat balikan **seketika**, sebelum satu suntingan pun:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py review --charterdir <charterdir> --verdict <PASS|BLOCKED> --report - <<'EOF'`,
   lalu blok `## Charter Review` apa adanya, lalu `EOF`. Skrip menolak vonis yang `- Verdict:`, `- Sidik:`, atau
   `- Ronde:`-nya tidak cocok, blok yang hitungan BLOCKER-nya tidak konsisten, dan dispatch atas draft yang tidak lolos
   validator. Tangani per tabel *Penanganan Balikan* template dispatch.

### Phase 4 — Commit Draft

`python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py commit --charterdir <charterdir> --stage draft` — subjek
`docs(product): draft CHARTER <slug>` (sesudah `revise`: `revise CHARTER <slug>`); dilarang `git add`/`git commit`
dengan tangan. Tanpa git → skrip melewati commit.

### Phase 5 — Persetujuan User

1. Sajikan **ringkasan gerbang**, bukan isi kartu: baris `CHARTER — DRAFT · <charterdir>/CHARTER.md · review
   <review_report>`, lalu 3–5 kalimat — judul dan mode; inti Purpose (segmen dan masalah); jumlah aktor, langkah alur,
   `BR-n`, `SC-n`, dan `S<n>` beserta aturan dan ukuran yang paling menentukan; vonis reviewer dalam satu frasa.
   Ada `ADVISORY [ELISITASI]` → satu kalimat: itu pertanyaan yang belum pernah diajukan ke peminta, dijawab lewat
   *Kembali ke elisitasi*. User meminta rincian → sajikan seksi yang diminta saja.
2. `AskUserQuestion`: *Setujui (APPROVED)* — **hanya bila `review_segar=ya`** · *Revisi (sebut poinnya)* ·
   *Kembali ke elisitasi* · *Tahan*.
3. **Setujui** → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py approve --charterdir <charterdir> --answer "<jawaban user apa adanya>"`.
   Skrip memateraikan `APPROVED` dan meng-commit `CHARTER.md` beserta `review.md` bila repo git.
4. **Revisi** → `charter.py revise --charterdir <charterdir>` (plafon 3) → perbarui draft → Phase 2–4 → ajukan ulang.
   Poin revisi yang menambah fakta → *Kembali ke elisitasi*.
5. **Kembali ke elisitasi** → `charter.py reopen --charterdir <charterdir> --to elicitation --reason "<alasan user>"`,
   lalu `product:discover` dengan `charterdir` dan `reopen_reason`.
6. **Tahan** → biarkan; charterdir muncul lagi di `charter.py state`.

## Guardrails

- **ELISITASI SATU-SATUNYA SUMBER**: dilarang menambah aktor, langkah, aturan, ukuran, atau butir Scope yang tidak ada
  di catatan, sekalipun "biasanya perlu".
- **CATATAN MILIK DISCOVER**: dilarang menyunting `## Catatan Elisitasi`; tiap perubahan fakta lewat
  `charter.py reopen --to elicitation` dan `product:discover`.
- **APPROVAL LEWAT SKRIP**: dilarang menulis `status: APPROVED`, `approved_hash`, atau `review:` dengan tangan.
- **ID SCOPE STABIL**: `S<n>` yang pernah disetujui tidak dinomori ulang; butir yang dibatalkan pindah ke Tidak
  Termasuk beserta ID-nya (`- **S<n>**: <butir> — <alasan>`), dan butir baru memakai ID berikutnya.
- **REVIEWER LEWAT TEMPLATE**: `charter-reviewer` hanya lewat prompt terhidrasi `dispatcher/reviewer.md`; blok
  vonisnya diteruskan tanpa parafrase.
- **ATOMIC COMMIT**: commit hanya lewat `charter.py`; dilarang `git add .`/`-A`/`-f`, `--no-verify`, push.
- **SERAH-TERIMA BELUM AKTIF**: charter `APPROVED` belum dipecah otomatis menjadi tiket; `S<n>` disiapkan untuk itu.
  Sebut di Output bahwa butir Scope dapat dibawa satu per satu ke `analyst:intake`.
- **RATIONALIZATION PREVENTION**:
  - "Reviewer cuma ADVISORY, langsung setujui saja" — menyerap advisory mengubah sidik; `approve` menolak vonis atas
    konten lama.
  - "User bilang oke di chat, saya set APPROVED sendiri" — tanpa `approve`, sidik tidak dimateraikan dan suntingan
    sesudahnya tidak terdeteksi sebagai `DRIFT`.
  - "Tim pasti butuh rancangan tabelnya, saya tambahkan" — rancangan teknis milik engineer; charter yang memutuskan
    cara membangun mengikat tim pada tebakan analis.
  - "Scope-nya 15 butir, tidak apa-apa" — versi pertama sebesar itu jarang selesai; tanyakan ke user butir mana yang
    pindah ke Tidak Termasuk.

## Output [REQUIRED]

Charter disetujui — satu baris: `SPEC — APPROVED · <charterdir>/CHARTER.md @<sidik> · <mode> · <n> aktor ·
<n> langkah · <n> BR · <n> SC · S1–S<n> · <commit <sha> | tanpa git | diabaikan git> — butir Scope siap dibawa ke
analyst:intake satu per satu.` Charter dibatalkan — `SPEC — BATAL · <charterdir> · <commit <sha> | tanpa git>`. Selain
itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### SPEC — <MENUNGGU KEPUTUSAN | TERTAHAN>
- **Draft**: <charterdir>/CHARTER.md · validator <PASS | FAIL> · review <PASS | BLOCKED> ronde <n>/2
- **Revisi**: <n>/3
- **BLOCKER tersisa**: <ringkas per butir> | —
- **Rute**: <menunggu jawaban user | product:discover (reopen) | ditahan user>
```

## Failure path

1. **Catatan belum tertutup**: hentikan; `product:discover` menuntaskannya lebih dulu.
2. **Fakta catatan saling bertentangan** saat merumuskan kartu: jangan memilih sendiri —
   `charter.py reopen --to elicitation` dengan alasan yang menyebut kedua fakta.
3. **Dispatch reviewer gagal dua kali**: charter tidak dapat di-`approve`; sajikan blok `TERTAHAN` dan minta user
   mengulang sesi.
4. **`approve` atau `commit` gagal commit** (exit 3): isinya sudah tertulis; sajikan baris `COMMIT GAGAL` apa adanya
   dan minta user meng-commit sendiri dengan perintah yang dicetak. Dilarang `--no-verify`.

## STYLE

- Imperatif aktif; kalimat aktif, satu aksi per langkah alur.
- Istilah tetap: Charterdir, Pilar, Sidik, Scope `S<n>`.
