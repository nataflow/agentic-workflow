---
name: business-analysis
description: Dipanggil backenddev:analyst sebagai hop BRD pada chain BRD_PRD_BRIEF - elisitasi terarah masalah domain, aktor, dan business rules ke BRD.md DRAFT di taskdir, sebelum system-analysis menyusun kontrak teknis
metadata:
  mode: compact
---

## THE IRON LAW

- Kode bukan aturan bisnis: labeli tiap fakta kode `Observasi kode: <file:baris>`, dilarang menganggapnya aturan target.
- Dilarang mengubah `src/`; commit sah hanya `BRD.md` DRAFT sesudah self-review `brd-reviewer` bervonis `Approved`.
- Ajukan maks 3 pertanyaan elisitasi non-blocking per giliran via `AskUserQuestion`.
- Dilarang menyisakan TBD atau placeholder di seksi substantif, dan dilarang menutup pilar wajib dengan asumsi.
- Berhenti di akar terakhir: aturan yang tidak menggerakkan satu `SC-{n}` pun dihapus, bukan dicarikan akar.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/business-analysis/scripts/check_preconditions.py --taskdir <taskdir> --chain <chain>`.
2. `PASS` (8/8): lanjut. `FAIL`: hentikan, remediasi butir gagal per `## Failure path` butir 1, ulangi skrip.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — direktori kerja aktif, diteruskan `backenddev:analyst`.
- `chain` — enum — `[REQUIRED]` — `BRD_PRD_BRIEF` | `PRD_BRIEF` | `BRIEF` yang dimateraikan `TASK.md`; dipakai apa adanya untuk menghidrasi slot `Chain` `dispatcher/reviewer.md`. Kosong → baca frontmatter `chain:` `TASK.md`; keduanya kosong → `## Failure path` butir 1.
- `risk` — enum — `[REQUIRED]` — `BREAKING` | `MAJOR` dari akar; menandai seberapa jauh aturan yang digali mengikat kontrak keluar.
- `feature_slug` — string — `[OPTIONAL]` — slug fitur; dipakai Fase 0 saat cek konflik domain.
- `target_domain` — string — `[OPTIONAL]` — mempersempit pemindaian Fase 1 ke satu domain.
- `preserve_history` — boolean — default `true` — pertahankan nomor `BR-{n}` lama saat tulis ulang.

## Workflow

### Fase 0 — Prasyarat & Status Artefak

1. `{taskdir}/BRD.md` `APPROVED`: laporkan dan minta konfirmasi user (revisi atau lanjut PRD). `DRAFT`: jadikan baseline dan sempurnakan seluruh seksi.
2. Pastikan slug tidak bentrok dengan modul domain eksisting; serap eksplorasi pendahulu dari konteks dispatch.
3. `{taskdir}/TASK.md` ada: kunci `## Success Criteria` dan `## Out of Scope` sebagai batas atas BRD, petakan tiap `BR-{n}` ke minimal 1 `SC-{n}`, lalu buang aturan yang menyentuh Out of Scope **atau** ajukan amandemen akar ke `backenddev:analyst` lewat laporan penutup (kanalnya bagian 5 `analyst/references/chain-rules.md`). Dilarang menembus langsung ke gerbang: gerbang tidak punya slot untuk menerimanya, dan pemegang ledger jadi tidak tahu hop ini tertahan. Absen: catat `akar absen` di laporan penutup.

### Fase 1 — Observasi Kode Baseline

1. `Glob backenddev/docs/*/BRD.md`: serap konvensi domain serupa dan pertanyaan yang sudah terjawab.
2. Baca kode hanya untuk memetakan alur as-is; labeli tiap fakta `Observasi kode: <file:baris>`. Kuota sapuan: maks 3 panggilan `Glob`+`Grep`, potongan maks 40 baris, nol berkas penuh, nol query DB.
3. Alur >1 modul, target luput pada `Grep` pertama, atau kuota habis: muat `dispatcher/explorer.md`, hidrasi slot `objective`, `taskdir`, dan `slug` — plus `konteks_diketahui` dan `batas_cakupan` bila tersedia — lalu dispatch `code-explorer` langsung tanpa skill pembungkus, dengan blok `Format laporan` template ikut berangkat utuh. Laporannya mendarat di `{taskdir}/.explore/{slug}.md` sekaligus kembali ke context. Kuota dispatch maks 1, naik ke 2 hanya bila alur terbukti menyentuh >1 modul; `Kedalaman` terkunci `ringkas`. Petakan balikannya lewat `### Penanganan Balikan` template itu. Balikan tidak konklusif atau dispatch gagal: `## Failure path` butir 8.
4. Sajikan ringkasan observasi: temuan kode aktual dan komponen bisnis yang belum terakomodasi.
5. Identifikasi entitas domain, enum status, dan service facade terkait; petakan invariant runtime dari `.claude/profile/invariants.md`.

### Fase 2 — Elisitasi Kebutuhan Domain

Baca `references/elicitation-guide.md` sebelum menyusun pertanyaan.

1. Ajukan 1-3 pertanyaan per giliran; tiap opsi memuat trade-off bisnis dan mitigasi risiko. Dilarang bertanya menetes lintas giliran atau kuesioner panjang sekaligus.
2. Gali 6 pilar wajib (Problem, Actors, Current State, Target State, Business Rules, Out of Scope) tanpa asumsi sepihak, plus 2 opsional (Edge Cases, Business Metrics).
3. Pilar opsional yang tertunda: tulis alasannya sebagai penegasan eksplisit di seksi BRD pemiliknya.

### Fase 3 — Konfirmasi Fakta Pra-Penyusunan

Ini **konfirmasi fakta, bukan gerbang keputusan**. Keputusan lingkup atas BRD diambil sekali saja, di gerbang dokumen `backenddev:analyst` Fase 4. Fase ini hanya memastikan bahan mentahnya benar sebelum ditulis.

1. Sajikan daftar fakta yang akan dibekukan ke dokumen: nama aktor beserta jenisnya, angka dan satuan tiap sumbu biaya pembiaran, istilah domain yang dipakai, nilai ambang tiap `BR-{n}`, dan `file:baris` tiap observasi kode.
2. Minta koreksi atas fakta yang salah. Dilarang menawarkan opsi lingkup, menanyakan setuju atau tidak atas dokumennya, dan menyajikan ringkasan eksekutif — ketiganya milik gerbang dokumen `analyst`, dan mengulangnya di sini membuat user memutuskan hal yang sama dua kali lalu mengecap gerbang yang sebenarnya secara otomatis.
3. Catat tiap koreksi, sesuaikan rumusan aturan, kunci istilah bisnis untuk PRD.

### Fase 4 — Penulisan BRD.md

Tulis tepat satu `{taskdir}/BRD.md` mengikuti `templates/brd-template.md`; tulis ulang utuh bila sudah ada. Sembilan seksi baku, urutannya, dan frontmatter (`title`, `requester`, `status: DRAFT`) mengikat.

1. `## Business rules`, `## Edge cases`, dan `## Business metrics` bernomor permanen: `- **BR-{n}**: <aturan mutlak>`, `- **EC-{n}**: <penanganan>`, `- **BM-{n}**: <metrik beserta baseline, target, dan baris `digerakkan: SC-{n}`>`; pertahankan penomoran lama bila `preserve_history` `true`. Aturan yang berubah makna dipensiunkan dan terbit ulang bernomor baru, jejaknya di baris `Pensiun:`; nomor pensiun tak dipakai ulang.
2. Tulis observasi kode terpisah: `Observasi kode: <file:baris> · <penjelasan fakta>`.
3. Isi seksi tanpa item dengan penegasan eksplisit, dan tahan `## Open questions` di maksimum tiga entri non-blocking.
4. **Uji kecukupan.** Tiap `BR-{n}` menutup bagian akar yang belum ditutup aturan lain; yang tidak menutup apa pun dihapus, bukan dicarikan akar. Pengetatan yang tidak diminta, kewajiban audit/log/notifikasi yang tak disinggung user maupun akar, dan aturan bersyarat masa depan ("bila nanti") adalah rancangan analis, dan rancangan bukan isi BRD.

### Fase 5 — Self-Review, Commit & Serah Terima

1. **Self-test mekanis**: loloskan seluruh butir `## Self-test struktural` `templates/brd-template.md`; satu gagal → perbaiki BRD, ulangi dari butir 1.
2. Muat `dispatcher/reviewer.md`, hidrasi slot `taskdir`, `chain`, dan `ronde`, panggil `brd-reviewer`. Tangkap `## BRD Review`, perbaiki isu, tahan `DRAFT` tanpa commit selama isu kritis terbuka. Gagal: `## Failure path` butir 6.
3. Verdict `Approved`: `git add {taskdir}/BRD.md` lalu `git commit -m "docs(spec): draft BRD <slug>"`. Verdict lain: lewati commit, laporkan `BRD.md` belum terkunci di git.
4. Sajikan `## Output [REQUIRED]` **beserta blok `## BRD Review` reviewer apa adanya**, lalu kembalikan rute ke `backenddev:analyst`. Approval user diminta di gerbang dokumennya, bukan di sini.

## Guardrails

- **KODE BUKAN ATURAN BISNIS**: dilarang menganggap logika kode eksisting benar sebagai aturan target tanpa konfirmasi user, atau menanyakan ulang fakta terbukti.
- **LARANGAN MUTASI**: dilarang membuat, mengubah, atau menghapus berkas `src/` maupun migration database, atau membuat taskdir spekulatif.
- **LARANGAN DESAIN TEKNIS**: endpoint HTTP, DTO, dan skema tabel dilarang muncul di `BRD.md` (wewenang `system-analysis`).
- **COMMIT TERBATAS DRAFT**: commit hanya `{taskdir}/BRD.md` DRAFT, staging path eksplisit. Dilarang `status: APPROVED`, commit approval, `git add .`/`-A`, `push`, `merge`, `rebase`, pindah branch (wewenang gerbang). Commit berangkat tanpa menunggu persetujuan user.
- **NOL PERMINTAAN APPROVAL**: `status: APPROVED` dan persetujuan user atas BRD adalah wewenang tunggal `backenddev:analyst` (`analyst/references/chain-rules.md` bagian 4). Dilarang menanyakan "setuju dokumen ini?" dalam bentuk apa pun, termasuk sebagai opsi `AskUserQuestion` Fase 2 atau kalimat penutup laporan.
- **VERDICT DITERUSKAN UTUH**: blok `## BRD Review` dari `brd-reviewer` diteruskan apa adanya ke laporan penutup. Dilarang memparafrase, meringkas, menyaring `Issues Found` jadi "sudah diperbaiki", atau menutup tanpa melampirkannya — `analyst` memakai blok itu sebagai predikat masuk gerbang dokumennya.
- **DISPATCH RESMI**: `brd-reviewer` via `dispatcher/reviewer.md`, `code-explorer` via `dispatcher/explorer.md`; keduanya didispatch langsung, tanpa skill pembungkus. Dilarang prompt di luar kedua template itu, mengubah `Kedalaman` explorer dari `ringkas`, memberangkatkan dispatch explorer ke-3 dalam satu taskdir, meneruskan sapuan sesudah kuota Fase 1 habis, membaca ulang berkas yang diringkas, masuk ronde self-review ke-3, atau dispatch ulang atas temuan `ADVISORY`/tanpa `previous_report`.
- **CUKUP ITU BERHENTI**: BRD merekam aturan yang berlaku, bukan aturan yang sebaiknya berlaku. Dilarang merumuskan `BR-{n}` yang tak satu pun `SC-{n}` gerakkan maupun user sebutkan — termasuk yang lahir dari "praktik terbaiknya begitu" atau "sekalian" — memperluas elisitasi ke domain tetangga yang tidak diminta, dan menaikkan pilar opsional (`Edge Cases`, `Business Metrics`) jadi sumbu kerja baru; keduanya melengkapi aturan yang ada, bukan menambah aturan.
- **RATIONALIZATION PREVENTION**: dilarang menganggap kode lama benar karena lama di produksi; menyerap laporan explorer `confidence: low` sebagai `Observasi kode`; menambal celah observasi dengan asumsi alur; meloloskan pertanyaan memblokir ke draft; melewati konfirmasi Fase 3; mengubah urutan 9 seksi; membuat >1 BRD per taskdir; menafsirkan keheningan sebagai persetujuan; atau menyatakan BRD ter-commit saat `git commit` gagal.

## Output [REQUIRED]

Artefak `{taskdir}/BRD.md` (DRAFT) mengikuti `templates/brd-template.md`. Verdict `Approved`, Open Qs 0, dan draft ter-commit → tutup satu baris tanpa blok: `### BUSINESS ANALYSIS SUMMARY — BRD.md DRAFT @ <sha> · <n> BR · Open Qs 0 · Self-review Approved`. Selain itu, sajikan:

```markdown
### BUSINESS ANALYSIS SUMMARY — TERTAHAN
- **Artefak** : backenddev/docs/<taskdir>/BRD.md (DRAFT) · belum di-commit (<alasan>)
- **Self-review**: Issues Found (<n> isu terbuka) | tidak tuntas (<alasan>)
- **Open Qs** : <n> tersisa — <pertanyaan yang menahan>
- **Aturan**  : <n> BR (BR-1..BR-N) · pensiun <BR-lama -> BR-baru> | —
```

Kedua bentuk melampirkan blok `## BRD Review` `brd-reviewer` apa adanya tepat di bawahnya — predikat C `analyst` menuntutnya utuh, dilarang diparafrase maupun diringkas. Aktor, masalah, dan tiap `BM-{n}` hidup di `BRD.md` yang gerbang dokumen baca sendiri; dilarang menyalinnya ke laporan.

**Serah-terima.** `Kembali ke backenddev:analyst`; `system-analysis` dilarang jalan sebelum `analyst` menulis `status: APPROVED`.

## Failure path

1. **Prasyarat gagal**: `chain` kosong dan `TASK.md` tak memuat `chain:`: hentikan, minta `backenddev:analyst` meneruskannya — tanpa nilai itu reviewer tidak dapat membedakan dokumen hulu yang sah tidak ada dari rantai putus. `taskdir` belum dialokasikan: minta inisialisasi `tech-lead`. `.claude/profile/index.json` absen: `backenddev:profile`. Direktori tak terakses: periksa izin. Tree kotor: bersihkan.
2. **Konflik aturan bisnis**: kebutuhan user bertentangan dengan aturan sistem, klarifikasi via `AskUserQuestion` lebih dulu.
3. **Draft ditolak user**: perbarui `BR-{n}` sesuai poin penolakan, tulis ulang sampai sepakat.
4. **Pertanyaan terbuka memblokir**: entri yang mengubah `Business rules`/`Target state`, tahan `DRAFT` dan jangan ajukan approval.
5. **Konteks tidak terbaca**: kode tak terakses, laporkan kendala izin dan minta verifikasi path repo. Sesi elisitasi terputus, lanjutkan dari pilar terakhir yang terjawab.
6. **Self-review gagal**: `brd-reviewer` gagal atau formatnya rusak, ulangi maks sekali; tetap gagal, serahkan `BRD.md` tanpa commit dan tandai tidak tuntas. Dilarang mengarang verdict `Approved`.
7. **Commit draft gagal**: `git commit` gagal (gpg memblokir, bukan repo git, indeks terkunci), tahan `DRAFT`, sertakan galat mentah, serahkan penguncian ke gerbang. Dilarang `--no-gpg-sign` atau staging wildcard.
8. **Eksplorasi kode tidak konklusif**: laporan `code-explorer` berbalik `confidence: low` atau tidak menjawab `objective`, dilarang diserap sebagai `Observasi kode`; angkat pertanyaannya ke elisitasi Fase 2 atau catat sebagai `## Open questions`. Payload kosong, format balikan rusak, atau subagent error adalah kegagalan dispatch, bukan cacat kerja: ulangi maks sekali, lalu lanjutkan Fase 2 tanpa observasi dan catat kendalanya pada slot `Explorasi` laporan penutup.

## STYLE

- Kalimat imperatif aktif, fase bernomor, tanpa konstruksi bersyarat WHEN/THEN.
- Berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal; istilah domain teknis tetap bahasa aslinya.
