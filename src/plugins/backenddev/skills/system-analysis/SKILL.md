---
name: system-analysis
description: Dipanggil backenddev:analyst pada hop PRD chain BRD_PRD_BRIEF (sesudah BRD APPROVED) atau PRD_BRIEF (tanpa BRD, risk MAJOR/BREAKING) - mengunci kontrak API, state lifecycle, validasi, permission, dan impact map ke PRD.md DRAFT sebelum brief ditulis
metadata:
  mode: compact
---

## THE IRON LAW

Kebutuhan BRD dibaca dari `chain`, bukan dari `risk_level`: `chain: BRD_PRD_BRIEF` wajib berdiri di atas `BRD.md` APPROVED, `chain: PRD_BRIEF` sah tanpa BRD pada risk level mana pun termasuk `BREAKING`, dan BRD `DRAFT` memblokir keduanya. Ledger yang menyatakan rantainya, bukan keberadaan berkas maupun tingkat risikonya. Dilarang menyisakan `TBD`, tipe data kosong, atau endpoint tanpa tabel error di seksi PRD mana pun. Evaluasi 16 dimensi impact checklist tanpa melewati satu pun. Tiap baris breakdown wajib menamai unit perubahan beserta permukaannya — modul atau layer, bukan path berkas `src/` maupun nama kelas test, yang keduanya wewenang `plan`. Berhenti di kontrak yang menutup akar: field, endpoint, dan baris breakdown yang tak berakar pada `BR-{n}`, `EC-{n}`, `SC-{n}`, atau permukaan terbukti Fase 1 dihapus, bukan dicarikan dasar. Dilarang mengubah `src/` atau menjalankan migration; commit sah hanya `PRD.md` DRAFT sesudah self-review `prd-reviewer` lolos.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/system-analysis/scripts/check_preconditions.py --taskdir <taskdir> --risk-level <risk_level> --chain <chain>`.
2. `PASS` (8/8): lanjut. `FAIL`: hentikan dan rutekan butir gagal — BRD absen/belum `APPROVED` pada `chain: BRD_PRD_BRIEF` ke `backenddev:analyst`; `chain` tak terbaca ke `backenddev:analyst`; taskdir tidak sah ke `tech-lead`; `.claude/profile/backenddev/index.json` absen ke `backenddev:profile`.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — direktori kerja aktif alokasi gerbang.
- `chain` — enum — `[REQUIRED]` — `BRD_PRD_BRIEF` | `PRD_BRIEF` yang dimateraikan `TASK.md`; penentu tunggal wajib-tidaknya BRD dan sumber hidrasi slot `Chain` `dispatcher/reviewer.md`. Kosong → baca frontmatter `chain:` `TASK.md`; keduanya kosong → Fase 0 berhenti.
- `risk_level` — string — `[REQUIRED]` — `BREAKING` atau `MAJOR`; penentu kedalaman analisis dampak dan plafon `risk:` hilir, bukan penentu kebutuhan BRD.
- `target_module` — string — `[OPTIONAL]` — mempersempit pemetaan as-is Fase 1 ke satu modul.

## Workflow

### Fase 0 — Penguncian Acuan Hulu

1. Rutekan menurut `chain`, bukan menurut `risk_level`:

| Kondisi | Aksi |
|---|---|
| `chain: BRD_PRD_BRIEF` + BRD `APPROVED` | Kunci `BR-{n}`, `EC-{n}`, `BM-{n}`, dan `## Out of scope`-nya sebagai batas atas PRD |
| `chain: BRD_PRD_BRIEF` + BRD `DRAFT` | Hentikan; BRD wajib `APPROVED` dulu. Kembalikan ke `backenddev:analyst` |
| `chain: BRD_PRD_BRIEF` + BRD absen | Hentikan; rantai putus — hop BRD tercantum di ledger tetapi artefaknya tidak ada. Kembalikan ke `backenddev:analyst` |
| `chain: PRD_BRIEF` + BRD absen | Lanjut pada risk level mana pun. Tandai `source_brd: tidak ada — sumbu bisnis nol` dan jalankan sapuan pilar residual `references/analysis-protocol.md` |
| `chain: PRD_BRIEF` + BRD ada di disk | Hentikan; artefak di luar chain berarti salah rute. Kembalikan ke `backenddev:analyst`, dilarang memakainya sebagai acuan |
| `chain` kosong dan `TASK.md` tanpa `chain:` | Hentikan; minta `backenddev:analyst` meneruskannya. Dilarang menyimpulkan rantai dari keberadaan berkas |
| `risk_level` kosong atau di luar `BREAKING`/`MAJOR` | Hentikan; minta pemanggil menetapkannya, dilarang menebak |

2. Serap `{taskdir}/TASK.md` bila ada: `## Success Criteria` dan `## Out of Scope` jadi batas atas PRD, tiap `AC-{n}` menyebut `SC-{n}` sumbernya di kolom `Akar`, dan kontrak yang menyentuh `## Out of Scope` mana pun dikembalikan ke `backenddev:analyst` sebagai permintaan amandemen akar (kanalnya bagian 5 `analyst/references/chain-rules.md`). Dilarang menembus langsung ke gerbang maupun membuang kontraknya sendiri. Absen: catat `akar absen` di laporan.

### Fase 1 — Pemetaan Kode Aktual (As-Is)

Jalankan bagian A `references/analysis-protocol.md` utuh: **Tahap 0 panen laci `{taskdir}/.explore/gate-*.md`**, kuota sapuan, predikat dispatch `code-explorer`, empat permukaan wajib, dan blast-sweep lima dimensi rawan bocor. Dispatch Profil S hanya untuk permukaan yang belum tertutup laporan gerbang; membuktikan ulang fakta yang sudah dibuktikan gerbang membayar dua dispatch berkedalaman `menyeluruh` untuk satu hasil. `code-explorer` didispatch langsung lewat `dispatcher/explorer.md` — Profil S di fase ini, Profil B sebelum Fase 4 — tanpa skill pembungkus; petakan tiap balikan lewat `### Penanganan Balikan` template itu. Laporkan tiap temuan berbukti `file:line` beserta jalur perolehannya (`code-explorer <slug>` atau fast-path `<n>/3`), dan tandai permukaan yang tak ditemukan.

### Fase 2 — Klarifikasi & Penguncian Kontrak

Lompati ke Fase 3 bila keempat pilar sudah konkret dari kode tanpa satu pun `TBD`. Pilar belum konkret: panggil `AskUserQuestion` 1–3 pertanyaan dalam satu giliran, sertakan konsekuensi teknis dan blast radius tiap opsi. Dilarang menanyakan hal yang sudah terbukti di Fase 1.

### Fase 3 — Penguncian 4 Pilar Kontrak Mutlak

Kunci empat pilar sampai nol kolom kosong, kolomnya persis `templates/prd-template.md`: **API contract** (method + path, field beserta tipe dan validasi per field menurut `## API surface` adapter, response sukses, tabel error), **status lifecycle**, **validation policy** termasuk urutan evaluasi saat kegagalan input bersamaan, dan **permission & scope** dengan boundary scoping terbukti dari filter security.

Dua kolom punya jalur perolehan yang ditetapkan dan dilarang ditempuh dengan cara lain. Kolom `Pesan` tabel `## Error` disalin apa adanya dari `### Error Surface` laporan Profil S — skill ini tidak membaca berkas sumber. Tipe kolom, nullability, constraint, dan index yang tidak terbukti dari berkas migrasi maupun definisi entity diambil lewat pembacaan skema read-only berkuota di bagian A `references/analysis-protocol.md`. Keduanya yang tidak tertutup mendarat di `## Open questions` sebagai asumsi berlabel `sementara dipakai:`, bukan diisi tebakan.

**Uji kecukupan kontrak.** Tiap field, nilai enum, aturan validasi, baris permission, dan baris tabel error berakar pada `BR-{n}`, `EC-{n}`, `SC-{n}`, atau permukaan terbukti Fase 1. Yang tak berakar pada satu pun dihapus dari tabelnya, bukan dicarikan dasar susulan.

### Fase 4 — Sapuan Analisis Dampak (16 Dimensi)

Vonis 16 dimensi bagian B `references/analysis-protocol.md` ke tabel `## Impact map` menurut aturan pengisian di bagian itu, lalu rinci migrasi dan backfill di `## Migration requirements` lengkap dengan rollback plan bila migrasi gagal di tengah deployment.

### Fase 5 — Dekomposisi Tugas & Acceptance Criteria

Isi `## Task breakdown` dan `## Acceptance criteria` menurut `## Authoring rules` template. Breakdown berhenti pada **unit perubahan dan permukaannya** — modul, layer, atau berkas migrasi menurut `## Layer taxonomy` adapter — satu baris per unit terisolasi (migrasi skema, mirrored path async, dan konfigurasi masing-masing satu baris), dengan dependensi membentuk DAG satu arah. Dilarang menetapkan path berkas `src/` konkret, urutan berkas, maupun nama kelas test: pemilihan berkas beserta penamaannya adalah wewenang tunggal `plan`, dan menetapkannya di sini menjadikan dua dokumen berwenang atas hal yang sama. Tiap endpoint, baris tabel error, dan `EC-{n}` BRD punya AC Given/When/Then dengan kolom `Cara verifikasi` bernilai `test otomatis` atau `QA manual: <langkah konkret>`, berkolom `Dasar` dan `Akar` terpisah. Baris breakdown berhenti di unit yang menutup kontrak Fase 3 dan dimensi `## Impact map` bervonis `terdampak`; pemecahan unit sah hanya bila permukaannya memang berbeda.

### Fase 6 — Penulisan Artefak PRD.md

Tulis tepat satu `{taskdir}/PRD.md` menurut `templates/prd-template.md` beserta `## Authoring rules`-nya; tulis ulang utuh bila sudah ada. Frontmatter wajib: `title`, `source_brd` (path relatif BRD sumber, atau `tidak ada — sumbu bisnis nol`), dan `status: DRAFT`.

### Fase 7 — Koreksi Fakta Pra-Commit

Ini **konfirmasi fakta, bukan gerbang keputusan**. Keputusan lingkup atas PRD diambil sekali saja, di gerbang dokumen `backenddev:analyst` Fase 4.

Fase ini berdiri **sesudah** PRD ditulis, bukan sebelumnya. Ditempatkan sebelum penulisan, ia tidak punya apa pun untuk ditahan: PRD belum ada, koreksi user tidak punya sasaran, dan satu-satunya cara melanjutkan adalah menulis PRD lebih dulu lalu menyajikan faktanya sebagai formalitas. Ditempatkan di sini, ia menahan sesuatu yang nyata — commit.

1. Sajikan fakta yang sudah dibekukan di PRD: nama dan tipe tiap field kontrak, nilai enum status, ambang tiap aturan validasi, nama role/permission, literal tiap pesan error, dan `file:baris` tiap permukaan hasil Fase 1. Tandai mana yang bersumber kode, mana dari pembacaan skema, dan mana yang masih asumsi `## Open questions`.
2. Minta koreksi atas fakta yang salah. Dilarang menyajikan ringkasan eksekutif, menawarkan opsi lingkup, atau menanyakan setuju-tidaknya user atas dokumen — ketiganya milik gerbang dokumen `analyst`.
3. **Penahanan.** Koreksi yang turun → perbaiki PRD atas fakta terkoreksi (ulangi Fase 6 pada seksi terdampak), lalu sajikan ulang fakta yang berubah saja. Fase 8 tidak berangkat dan commit tidak dieksekusi sampai tiap koreksi mendarat di berkas. Nol koreksi → lanjut ke Fase 8.

### Fase 8 — Self-Review, Commit Draft & Serah Terima

1. **Self-test mekanis**: loloskan tiga belas butir `## Self-test pra-reviewer` `templates/prd-template.md` sebelum butir 2 berangkat; satu gagal → perbaiki PRD, ulangi dari butir 1.
2. **Self-review**: muat `dispatcher/reviewer.md`, hidrasi slot `taskdir`, `chain`, dan `ronde`, panggil `prd-reviewer`. Perbaiki isu `## PRD Review`; pertahankan `DRAFT` tanpa commit selama isu kritis terbuka. Gagal: `## Failure path` butir 2.
3. **Commit draft**, bukan approval. `Approved`: `git add {taskdir}/PRD.md` lalu `git commit -m "docs(spec): draft PRD <slug>"`. Selain itu lewati commit dan laporkan PRD belum terkunci di git. Exit code bukan nol: butir 3.
4. Sajikan `## Output [REQUIRED]` **beserta blok `## PRD Review` reviewer apa adanya**, lalu kembalikan rute ke `backenddev:analyst`. Dilarang meminta persetujuan user: approval dan penulisan `status: APPROVED` adalah wewenang tunggal `analyst` di gerbang dokumennya.

## Guardrails

- **ATURAN BISNIS**: pada risk `MAJOR` tanpa BRD, dilarang merumuskan aturan bisnis baru sendiri.
- **COMMIT TERBATAS DRAFT**: commit hanya `{taskdir}/PRD.md` DRAFT, staging path eksplisit. Dilarang `status: APPROVED`, commit approval, `git add .`/`-A`, `push`, `merge`, `rebase`, pindah branch (wewenang gerbang). Commit berangkat tanpa menunggu persetujuan user.
- **NOL PERMINTAAN APPROVAL**: persetujuan user atas PRD dan penulisan `status: APPROVED` adalah wewenang tunggal `backenddev:analyst` (`analyst/references/chain-rules.md` bagian 4). Dilarang menanyakannya dalam bentuk apa pun.
- **NOL PENETAPAN BERKAS**: dilarang menulis path berkas `src/` konkret, urutan berkas, atau nama kelas test di `## Task breakdown` maupun `## Acceptance criteria`. PRD mengunci kontrak dan permukaan; pemilihan berkas beserta penamaannya milik `plan`.
- **SKEMA DIBACA READ-ONLY & BERKUOTA**: pembacaan skema database sah hanya di bawah batas bagian A `references/analysis-protocol.md` — introspeksi dan agregat saja, nol DML dan nol DDL, terbatas pada permukaan Fase 1, maksimal 5 panggilan per taskdir, dan tiap fakta hasilnya memikul penanda sumbernya. Dilarang menjalankan migrasi, menyentuh tabel di luar permukaan, atau memakai jalur ini untuk fakta yang sebenarnya terbaca dari berkas migrasi maupun definisi entity.
- **CUKUP ITU BERHENTI**: PRD mengunci kontrak yang dituntut akar, bukan kontrak yang ideal. Dilarang menambah field, endpoint, nilai enum, tabel, index, atau migrasi yang tak satu pun `BR-{n}`, `EC-{n}`, `SC-{n}`, maupun permukaan Fase 1 tuntut lalu mengisi kolom `Dasar`-nya dengan rujukan terdekat yang kebetulan bersinggungan; memakai vonis `terdampak` sebagai izin merancang ulang modul yang disentuhnya — ia menuntut dampaknya mendarat di satu baris breakdown, bukan modulnya ikut digarap; dan memecah `## Task breakdown` lebih halus daripada permukaan yang benar-benar berbeda.
- **VERDICT DITERUSKAN UTUH**: blok `## PRD Review` dari `prd-reviewer` diteruskan apa adanya ke laporan penutup, tanpa parafrase maupun penyaringan. `analyst` memakainya sebagai predikat masuk gerbang dokumen.
- **DISPATCH RESMI**: `prd-reviewer` via `dispatcher/reviewer.md`, `code-explorer` via `dispatcher/explorer.md`; keduanya didispatch langsung, tanpa skill pembungkus. Dilarang prompt di luar kedua template itu, mengubah `Kedalaman` explorer dari `menyeluruh`, mencampur Profil S dan Profil B dalam satu prompt, menyapu sendiri permukaan yang harus didispatch, masuk ronde self-review ke-3, atau dispatch ulang atas `ADVISORY`/tanpa `previous_report`.
- **RATIONALIZATION PREVENTION**: dilarang mengisi kolom `Pesan` tabel `## Error` dengan parafrase atau terjemahan alih-alih literal `### Error Surface`, menuliskan tipe kolom atau daftar index yang tidak pernah dibaca dari kode maupun skema, mengasumsikan scoping tenant aman tanpa bukti filter security, memvonis dimensi `Tidak terdampak` di atas baris `### Blast Map` berstatus `belum disisir`, di atas baris yang kolom `Disisir`-nya nol atau kosong, di atas dimensi yang tidak muncul di tabel itu, atau di atas `### Gaps` explorer yang berbunyi "belum disisir", memvonis dimensi 11 `tidak relevan` tanpa menyebut jumlah berkas test yang disisir, mengunci tabel kontrak Fase 3 di atas balikan `confidence: medium` tanpa konfirmasi Fase 2, mengubah urutan sembilan seksi PRD, melewati penahanan koreksi Fase 7 atau meng-commit PRD yang koreksinya belum mendarat, menganggap keheningan sebagai persetujuan, mengarang verdict `Approved`, atau menyatakan PRD ter-commit saat `git commit` gagal.

## Output [REQUIRED]

Artefak `{taskdir}/PRD.md` (DRAFT) mengikuti `templates/prd-template.md`. Self-review PASS, Open Qs 0, dan draft ter-commit → tutup satu baris tanpa blok: `### SYSTEM ANALYSIS SUMMARY — PRD.md DRAFT @ <sha> · <n> endpoint terkunci · <n> langkah breakdown · Open Qs 0 · Self-review PASS`, ditambah baris `BR Disanggah` bila ada. Selain itu, sajikan:

```markdown
### SYSTEM ANALYSIS SUMMARY — TERTAHAN
- **Artefak** : backenddev/docs/<taskdir>/PRD.md (DRAFT) · belum di-commit (<alasan>)
- **Self-review**: tidak tuntas (<alasan>)
- **Open Qs** : <n> tersisa — <pertanyaan yang menahan>
- **BR Disanggah**: <BR-{n} yang ditulis sebagai entri `BR-DISANGGAH:` di `## Open questions`> | —
```

Kedua bentuk melampirkan blok `## PRD Review` `prd-reviewer` apa adanya tepat di bawahnya — predikat D `analyst` menuntutnya utuh, dilarang diparafrase. `BR Disanggah` bertahan sekalipun PRD bersih: sanggahan atas `BR-{n}` yang sudah `APPROVED` diputuskan user di gerbang dokumen, bukan di sini. Kontrak endpoint, lifecycle status, permission boundary, migrasi, dan impact map hidup di `PRD.md`.

**Serah-terima.** `Kembali ke backenddev:analyst`; `plan` menunggu `analyst` menulis `status: APPROVED`.

## Failure path

| # | Pemicu | Penanganan |
|---|---|---|
| 1 | BRD absen atau `DRAFT` pada `chain: BRD_PRD_BRIEF` | Hentikan; kembalikan ke `backenddev:analyst` untuk melanjutkan hop BRD. Pada `chain: PRD_BRIEF`, ketiadaan BRD sah pada risk level mana pun: lanjut dengan `source_brd` bertanda tidak ada |
| 2 | `prd-reviewer` gagal atau balikan rusak | Ulangi maks sekali; tetap gagal: serahkan PRD tanpa commit, tandai self-review tak tuntas |
| 3 | `git commit` gagal (gpg, bukan repo git, indeks terkunci) | Pertahankan `DRAFT`, sertakan galat mentah, serahkan penguncian ke gerbang. Dilarang `--no-gpg-sign` atau staging wildcard |
| 4 | Simbol hasil Fase 1 berubah saat Fase 6 | Ulangi Fase 1 untuk simbol terdampak; dilarang menambal kontrak di atas bukti basi |
| 5 | Risk `MAJOR` tapi Fase 3 menemukan perubahan field wajib atau transisi status terekspos | Hentikan, kembalikan ke `backenddev:analyst` menyebut **pemicu eskalasi nomor 4** (kenaikan `risk` ke `BREAKING` tanpa transisi chain); dilarang menaikkan risk atau chain sendiri |
| 6 | Fase 2 menemukan pilar bisnis yang tak terjawab kode maupun user pada `chain: PRD_BRIEF` | Hentikan, kembalikan ke `backenddev:analyst` menyebut **pemicu eskalasi nomor 3** (sumbu bisnis ternyata aktif); dilarang merumuskan aturan bisnisnya sendiri di PRD |
| 7 | Balikan `code-explorer` tetap `confidence: low` sesudah satu kali pertajaman, atau payload kosong/rusak dua kali | Turun ke sapuan manual di sisa kuota Fase 1, tandai permukaan yang tak tertutup, dan laporkan penyimpangannya pada baris `Explorasi` `## Output`. Dilarang mengunci pilar kontrak Fase 3 di atas permukaan yang belum tertutup |

## STYLE

- Fase bernomor dan kalimat imperatif aktif, tanpa konstruksi WHEN/THEN.
- Berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal; istilah domain teknis tetap bahasa aslinya.
