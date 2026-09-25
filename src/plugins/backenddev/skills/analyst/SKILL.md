---
name: analyst
description: Dipanggil gerbang backenddev:tech-lead sesudah lane PLANNING ditetapkan dan taskdir terprovisi - orkestrasi rantai TASK/BRD/PRD/brief beserta gerbang approval dokumen, sebelum brief READY diserahkan ke fase eksekusi
metadata:
  mode: standard
---

## THE IRON LAW

- Tetapkan `chain` sekali di Fase 1 dan materaikan ke `TASK.md`; seluruh hilir membaca nilai itu, bukan menebaknya dari keberadaan berkas.
- Jalankan hop rantai berurutan sampai brief `READY` terbit; dilarang melompati hop yang tercantum di ledger `## Chain`.
- Tulis nol baris isi `BRD.md`, `PRD.md`, dan `brief-*.md` — skill ini mengorkestrasi, penulisnya skill hop.
- Naikkan `chain` saat pemicu eskalasi aktif dan jangan pernah menurunkannya.
- Dilarang menyentuh `src/`; mutasi git sah hanya commit approval `BRD.md`/`PRD.md` dan pembaruan `TASK.md`.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyst/scripts/check_preconditions.py --taskdir <taskdir> --risk <risk> [--chain <chain>]`.
2. `PASS` (6/6 checks) → lanjut ke Workflow. `FAIL` → hentikan dan remediasi butir gagal: taskdir belum sah atau belum diprovisi → minta alokasi ke `backenddev:tech-lead`; profil belum lengkap → `backenddev:profile`; `risk` di luar enum → minta gerbang menetapkannya; artefak taskdir bertentangan dengan `chain` → laporkan salah rute ke gerbang; working tree kotor di luar taskdir → bersihkan dulu.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — path taskdir hasil provisi gerbang; wajib cocok pola `backenddev/docs/<YYMMDDhhmm>-<slug>/`.
- `risk` — enum — `[REQUIRED]` — `BREAKING` | `MAJOR` | `MINOR` hasil Keputusan 2 gerbang; penentu utama derivasi `chain`.
- `request` — string — `[REQUIRED]` — permintaan user sebagai bahan mentah; diteruskan apa adanya ke `task`.
- `evidence` — list — `[REQUIRED]` — minimal satu `file:line` hasil eksplorasi Fase 1 gerbang; daftar kosong menghentikan skill.
- `clarification` — list — default `[]` — pasangan tanya-jawab gerbang; diteruskan ke `task` sebagai sumber `## Out of Scope`.
- `file_scope` — string — `[REQUIRED]` — slot `File Scope` laporan rute gerbang; diteruskan apa adanya ke `plan` sebagai pembanding Check E.
- `chain` — enum — default `auto` — `BRD_PRD_BRIEF` | `PRD_BRIEF` | `BRIEF`; `auto` menurunkannya dari dua sumbu Fase 1.
- `finding_source` — string — default `""` — Path berkas temuan asal (`backenddev/issues/<file>.md` atau `{taskdir}/REVIEW.md`) saat akar berangkat dari temuan terpilih; kosong pada permintaan kerja biasa. Diteruskan apa adanya ke `task` dan `plan` menurut bagian 2.1 `references/chain-rules.md`; dilarang disimpulkan dari isi `request`.
- `reentry_reason` — string — default `""` — Alasan gerbang mengembalikan taskdir yang ledger-nya sudah tercentang penuh: predikat gerbang yang gagal, perintah verifikasi penutup yang merah, atau daftar berkas yatim. Terisi → Fase 3 butir 0 berangkat lebih dulu. Kosong pada taskdir berledger penuh → rantai berhenti tanpa hop yang dapat dijalankan; minta gerbang menyebutkan alasannya, dilarang menebak hop pemiliknya.

## Workflow

### Fase 1 — Derivasi & Penguncian Chain

1. Vonis **sumbu bisnis** bagian 1.1 `references/chain-rules.md` atas lima butirnya, lalu **sumbu kontrak** bagian 1.2 atas tiga butirnya. Kedua sumbu dievaluasi terpisah dan masing-masing berpredikat bukti `file:line` atau jawaban user, bukan keyakinan.
2. Turunkan `chain` dari matriks bagian 1.3 atas kedua vonis itu; nilai `chain` eksplisit dari gerbang mengesampingkan derivasi dan tetap diverifikasi terhadap matriks yang sama.
3. Verifikasi pasangan `(risk, chain)` terhadap tabel bagian 1.4. `risk: MINOR` bersumbu kontrak aktif → naikkan `risk` ke `MAJOR` di sini juga dan laporkan butir pemicunya. Pasangan lain yang tidak sah → `## Failure path` butir 1.
4. Panggil `AskUserQuestion` tepat sekali bila salah satu sumbu masih abu-abu sesudah `evidence` dibaca. Tiap opsi memuat konsekuensi rantai: hop yang bertambah dan artefak yang wajib disetujui.
5. Kunci nilai hasilnya beserta vonis kedua sumbunya; vonis itu masuk slot `Justifikasi Chain` laporan penutup.

### Fase 2 — Perumusan Akar Rantai

1. Panggil `backenddev:task` dengan `taskdir`, `lane` terminal chain (matriks bagian 1.3 `references/chain-rules.md`, kolom keempat), `risk`, `request`, `evidence`, `clarification`, `chain`, dan `finding_source` apa adanya.
2. Tangkap laporan `### TASK ROOT LOCKED`; `Uji Akar` bukan `9/9 lolos` atau `Commit` bernilai `GAGAL` → `## Failure path` butir 2.
3. Verifikasi `TASK.md` memuat frontmatter `chain:` sesuai Fase 1 dan seksi `## Chain` berisi tepat hop chain itu, seluruhnya belum tercentang.

### Fase 3 — Eksekusi Hop Rantai

Jalankan hop belum tercentang paling atas pada ledger `## Chain`, satu hop per giliran:

| Hop | Skill | Artefak | Sesudahnya |
|---|---|---|---|
| `BRD` | `backenddev:business-analysis` | `BRD.md` `DRAFT` | Fase 4 |
| `PRD` | `backenddev:system-analysis` | `PRD.md` `DRAFT` | Fase 4 |
| `BRIEF` | `backenddev:plan` | `brief-*.md` `READY` | Fase 6 |

0. **Re-entry — ledger sudah tercentang penuh.** Taskdir yang kembali dari gerbang membawa kegagalan hilir tidak punya hop belum tercentang, sehingga predikat butir 1 tidak pernah terpenuhi dan rantai berhenti tanpa jalan masuk. Bukalah hop-nya lebih dulu, jangan berimprovisasi masuk ke tengah fase. Lima pemicunya: vonis `NOT_READY_FOR_IMPLEMENTATION` yang dikembalikan gerbang, verifikasi penutup `architect` merah karena cacat perencanaan (`architect` Failure path 4b), berkas terdampak yang tak dimiliki `## File scope` brief mana pun, brief `BLOCKED` di taskdir (`reentry_reason` menyebut brief-NN beserta sebab dari `report-NN.md`; hop pemilik `BRIEF`), dan temuan `P1` `REVIEW.md` yang dikembalikan gerbang (hop pemilik: `BRIEF`, atau `PRD` bila temuan menunjuk kontrak).

   1. Tetapkan **satu** hop pemilik kegagalannya dari laporan masuk: predikat atau berkas yang gagal menunjuk `brief-*.md` → hop `BRIEF`; menunjuk kontrak, `AC-{n}`, atau permukaan PRD → hop `PRD`; menunjuk aturan bisnis `BR-{n}` → hop `BRD`. Kegagalan yang menunjuk dua hop sekaligus dibuka pada hop **paling hulu**.
   2. Ubah centang hop itu menjadi `- [~] <HOP> — <skill> → <artefak> @ re-entry <n> (was <sha lama>)`. Hop di bawahnya yang sudah tercentang ikut dibuka menjadi `- [ ]` tanpa penanda: artefaknya tidak dibatalkan, tetapi ia wajib berangkat ulang di atas hasil hop hulu yang baru.
   3. Commit pembaruan dengan staging path eksplisit `{taskdir}/TASK.md` dan subjek `docs(<slug>): re-entry hop <HOP> ke-<n>`.
   4. Lanjutkan ke butir 1; hop `[~]` diperlakukan persis seperti hop belum tercentang, dan kembali `[x]` bersha baru saat ia tuntas.

   **Artefak hop yang dibuka tidak dihapus dan tidak diturunkan statusnya.** `BRD.md`/`PRD.md` `APPROVED` bertahan `APPROVED` sampai hop itu menerbitkan revisinya, lalu gerbang dokumen Fase 4 berjalan ulang atasnya. Brief `DONE` **tidak pernah** dibuka: ia sudah dieksekusi, dan sisa pekerjaannya adalah brief tambahan pada taskdir yang sama — bukan penulisan ulang riwayat. Brief `BLOCKED` juga tidak dibuka: `plan` menutupnya jadi `SUPERSEDED` lewat brief pengganti.

   **Plafon dua re-entry per taskdir**, dihitung terpisah dari eskalasi chain Fase 5 dan amandemen akar Fase 4a. Permintaan ketiga → `## Failure path` butir 9.

1. Serahkan `taskdir`, `chain`, dan `risk` ke tiap skill hop tanpa kecuali; `system-analysis` menerima `risk` bernama `risk_level`, dan `plan` menerima `entry_mode`, `file_scope`, beserta `finding_source` menurut bagian 2.1 `references/chain-rules.md`. Dilarang membiarkan hop menyimpulkan `chain` dari keberadaan berkas.
2. Tangkap laporan penutup skill hop **beserta blok `## <BRD|PRD|Brief> Review` reviewer-nya apa adanya**. Laporan menyatakan artefaknya tidak terbit, commit-nya gagal, verdict reviewer bukan `Approved`, atau blok review-nya tidak dilampirkan → `## Failure path` butir 3.
3. Evaluasi Fase 5 lebih dulu tiap kali laporan hop menyebut pemicu eskalasi; hop dianggap belum tuntas sampai evaluasi itu selesai.
4. Jalankan Fase 4a lebih dulu tiap kali laporan hop meminta amandemen `## Success Criteria` atau `## Out of Scope` `TASK.md`; hop ditahan apa adanya sampai keputusan user turun.
5. Hop `BRIEF` tuntas → langsung ke Fase 6. Hop `BRD` dan `PRD` tuntas → Fase 4.

### Fase 4 — Gerbang Dokumen

Dijalankan atas tiap `BRD.md` dan `PRD.md` sebelum hop berikutnya berangkat, mengikuti bagian 4 `references/chain-rules.md`:

0. Predikat masuk: laporan hop menyatakan self-review lolos dan melampirkan blok review reviewer-nya. Verifikasi klaim itu lewat jejak yang penulis tidak dapat karang — `git log --oneline -1 -- {taskdir}/<artefak>` wajib menunjukkan commit draft berformat pesan penulisnya, karena penulis dilarang meng-commit sebelum verdict `Approved`. Salah satu tidak terpenuhi → fase ini tidak berangkat sama sekali; rutekan ke `## Failure path` butir 3. Artefak yang tertahan karena verdict gagal bukan draft yatim.
1. Kunci draft yatim: periksa `git status --porcelain` atas artefak hop; belum terkunci → commit seketika memakai format pesan penulisnya, tanpa menunggu persetujuan siapa pun.
2. Verifikasi `## Open questions` artefak: maksimal tiga entri dan tidak satu pun memblokir menurut predikat rumah kanoniknya. Ada yang memblokir → kembalikan poin revisinya ke skill hop, pertahankan `DRAFT`, ulangi Fase 3 pada hop yang sama. Plafon dua pengembalian per hop; pengembalian ketiga → `## Failure path` butir 7.
3. Sajikan ringkasan eksekutif artefak — termasuk enumerasi tiap `BR-DISANGGAH: BR-{n}` PRD dan tiap asumsi aktif `sementara dipakai:` — lalu mintakan persetujuan eksplisit user lewat `AskUserQuestion`.
4. User menyetujui → tulis `status: APPROVED` di frontmatter, commit approval seketika dengan staging path eksplisit, lalu centang hop itu di ledger `## Chain` beserta sha commit tersebut dan commit pembaruan `TASK.md`-nya. Urutan itu tidak dapat dipadatkan jadi satu commit: baris centang memuat sha yang belum ada saat berkasnya di-stage (`references/chain-rules.md` bagian 4 butir 5). Lanjut ke hop berikutnya.
5. User menolak → pertahankan `DRAFT`, teruskan poin revisi ke skill hop, ulangi Fase 3 pada hop yang sama. Dilarang mengubah commit draft yang sudah mendarat.

### Fase 4a — Kanal Amandemen Akar

Dijalankan saat laporan hop mana pun melaporkan aturan atau kontrak yang menyentuh `## Success Criteria` atau `## Out of Scope` `TASK.md`, mengikuti bagian 5 `references/chain-rules.md`:

1. Tahan hop apa adanya: ledger tidak dicentang, artefak tetap `DRAFT`, hop berikutnya tidak berangkat.
2. Sajikan butir akar yang tersentuh beserta aturan atau kontrak penyentuhnya lewat `AskUserQuestion`, dengan dua konsekuensi eksplisit: akar diamandemen, atau butir hilir dibuang.
3. User membuang butir hilir → teruskan keputusannya apa adanya ke skill hop, ulangi Fase 3 pada hop yang sama, catat butirnya di slot `Keputusan Lingkup`.
4. User memilih amandemen → hentikan rantai, serahkan rumusan amandemennya ke gerbang. Dilarang menulis ulang `## Success Criteria` maupun `## Out of Scope` sendiri; mutasi `TASK.md` milik skill ini terbatas pada pencentangan ledger dan transisi eskalasi.
5. Plafon dua amandemen per taskdir; permintaan ketiga → `## Failure path` butir 8.

### Fase 5 — Evaluasi Eskalasi Chain

1. Sandingkan laporan hop dengan empat pemicu bagian 3 `references/chain-rules.md`. Nol pemicu aktif → kembali ke Fase 3.
2. Pemicu aktif → jalankan prosedur transisi enam langkah bagian itu apa adanya: verifikasi pasangan `(risk, chain)` hasil transisi terhadap tabel bagian 1.4 lebih dulu, tulis ulang frontmatter dan ledger `## Chain`, tulis ulang klausa `— verifikasi:` tiap `SC-{n}` agar cocok lane baru tanpa mengubah prosa hasilnya, jalankan ulang butir 2–4 **dan butir 8a** self-test akar, lalu commit dengan staging path eksplisit.
3. Kembali ke Fase 3 pada hop baru yang belum tercentang; hop yang sudah tercentang beserta artefaknya dipertahankan apa adanya.
4. Plafon dua transisi `chain` per taskdir; kenaikan `risk` tanpa transisi chain (pemicu 4) tidak dihitung. Transisi ketiga → `## Failure path` butir 5.

### Fase 6 — Gerbang `READY_FOR_IMPLEMENTATION` & Serah Terima

Ini satu-satunya titik yang memeriksa rantai sebagai satu kesatuan. Tiap skill hulu memeriksa dokumennya sendiri; tidak ada yang memeriksa sambungannya sekali lagi sesudah brief terbit.

0. **Tutup ledger.** Centang hop `BRIEF` di `## Chain` `TASK.md` beserta sha commit agregat dari laporan `plan` (`- [x] BRIEF — backenddev:plan → brief-*.md @ READY <sha>`), lalu commit pembaruannya dengan staging path eksplisit `{taskdir}/TASK.md` dan subjek `docs(<slug>): tutup ledger chain <enum>`. Brief tidak melewati gerbang dokumen Fase 4, tetapi ia tetap hop ledger — tanpa langkah ini predikat B di bawah mustahil dipenuhi dan tiap rantai bervonis `NOT_READY_FOR_IMPLEMENTATION` betapapun benar isinya. Laporan `plan` menyatakan commit agregatnya gagal → lewati pencentangan, jangan mengarang sha, dan biarkan predikat B gagal apa adanya.
1. **Vonis lima belas predikat** berikut, satu baris hasil per predikat. Satu predikat gagal → status `NOT_READY_FOR_IMPLEMENTATION`; laporkan predikat yang gagal beserta ID yang membuatnya gagal, dan dilarang menurunkannya jadi catatan serah terima.

   | # | Predikat |
   |---|---|
   | A | `TASK.md` `status: ACTIVE`, self-test akar 9/9 lolos, ter-commit |
   | B | Ledger `## Chain` tercentang penuh, tiap centang membawa sha |
   | C | `BRD.md` `APPROVED` bila `chain: BRD_PRD_BRIEF`, verdict `brd-reviewer` `Approved` terlampir apa adanya |
   | D | `PRD.md` `APPROVED` bila `chain` ber-PRD, verdict `prd-reviewer` `Approved` terlampir apa adanya |
   | E | Tiap `brief-*.md` berstatus `READY`, `DONE`, atau `SUPERSEDED` bertaut (Check C `validate_briefs.py` tanpa pelanggaran tautan); yang `READY` ter-commit satu batch; verdict `brief-reviewer` `Approved` terlampir apa adanya. `BLOCKED` tetap gagal — ia wajib sudah digantikan brief ber-`supersedes` |
   | F | Tiap `SC-{n}` `TASK.md` disebut minimal satu baris `Fulfills:` — **hanya `chain: BRIEF`**; rantai ber-PRD melewatinya (jalurnya `Akar` PRD → `Covers:`, predikat G2 dan G) |
   | G | Tiap `AC-{n}` `PRD.md` disebut minimal satu baris `Covers:` (chain ber-PRD) |
   | G2 | Tiap `SC-{n}` `TASK.md` disebut minimal satu kolom `Akar` PRD (chain ber-PRD) |
   | H | Tiap `BR-{n}` `BRD.md` disebut minimal satu kolom `Dasar` PRD (chain ber-BRD) |
   | H2 | Tiap `EC-{n}` `BRD.md` disebut minimal satu kolom `Dasar` tabel `## Acceptance criteria`; `EC-0` lolos tanpa AC (chain ber-BRD) |
   | I | Nol rujukan hantu pada kelima sumbu di atas |
   | J | Tiap `BR-DISANGGAH: BR-{n}` PRD punya keputusan user tercatat di Fase 4 |
   | K | Nol entri `## Open questions` memblokir di `BRD.md`/`PRD.md`; nol seksi `## Open questions` di brief mana pun |
   | L | Nol brief melanggar `## Out of Scope` `TASK.md`; `risk:` tiap brief ≤ `risk:` `TASK.md` |
   | M | Tiap asumsi aktif `sementara dipakai:` yang membentuk `## Steps` mendarat di `## Objective` brief pelaksananya, bukan di `## Analysis trace` |

   > Mengapa E menerima `DONE`: predikat ini dijalankan ulang pada tiap re-entry Fase 3 butir 0, dan brief yang sudah dieksekusi tidak pernah kembali ke `READY`; menuntut `READY` mutlak gagal permanen di taskdir yang pernah dieksekusi. Mengapa F hanya `chain: BRIEF`: brief pada rantai ber-PRD tidak menulis `Fulfills:` sama sekali.

   Predikat F–M diperiksa ulang di sini sekalipun sudah ditagih hulu: penagihan hulu berlaku per dokumen dan per batch, sedangkan rantai bisa putus di sambungannya — misalnya brief yang menutup seluruh AC PRD sementara satu `SC-{n}` akar tak pernah dipetakan ke AC mana pun. G2 dan H2 hadir karena alasan yang sama persis dengan H: `SC-{n}` dan `EC-{n}` diangkut kolom PRD yang sama dengan `BR-{n}`, dan sumbu yang diperiksa hanya di hulu putus tanpa suara di sini.

2. Sajikan `## Output [REQUIRED]` beserta vonis gerbang ini.
3. Kelima belas predikat lolos → kembalikan kendali ke `backenddev:tech-lead` untuk merutekan fase eksekusi ke `backenddev:architect`, beserta slot `Verifikasi Manual` yang mengenumerasi tiap `AC-{n}` bertanda `QA manual:` — itu satu-satunya bentuk verifikasi AC tersebut, dan tanpa enumerasi ini ia tidak sampai ke gerbang penutup. Dilarang memanggil `architect` maupun `code-implementor` sendiri.
4. Status `NOT_READY_FOR_IMPLEMENTATION` → serahkan ke gerbang beserta daftar predikat yang gagal; dilarang menyerahkan rantai sebagai selesai.

## Guardrails

- **ORKESTRASI, BUKAN PENULISAN — dan predikatnya terbaca dari git**: dilarang menulis, menyunting, atau menambal isi `BRD.md`, `PRD.md`, dan `brief-*.md`. Revisi dikembalikan ke skill hop penulisnya beserta poin perbaikannya.

  Batas ini tidak dapat ditegakkan oleh isolasi runtime — giliran yang sama memuat skill ini dan skill hop yang menulis, dan tidak ada yang memisahkan keduanya selain niat. Yang menggantikan isolasi adalah **jejak yang dapat diperiksa**: tiap mutasi ketiga berkas itu wajib mendarat di commit berformat pesan skill hop penulisnya — `docs(spec): draft <BRD|PRD> <slug>` dan `docs(plan): add <N> briefs for <slug>`. Fase 6 memverifikasinya lewat `git log --format=%s -1 -- <berkas>` pada predikat C, D, dan E. Mutasi yang mendarat di commit di luar format itu — atau tidak mendarat di commit mana pun — adalah pelanggaran batas yang **terbaca**, dan dilaporkan apa adanya di slot `Catatan Rantai`, bukan didiamkan karena "toh isinya benar".
- **NOL SENTUHAN KODE**: dilarang membaca-tulis di bawah `source_root`, menjalankan build atau test, dan membuat berkas di luar `{taskdir}`.
- **CHAIN SATU ARAH**: dilarang menurunkan `chain`, membatalkan artefak hop yang sudah `APPROVED`, atau melompati hop yang tercantum di ledger dengan alasan artefaknya "tidak diperlukan". Membuka hop jadi `[~]` di Fase 3 butir 0 bukan penurunan chain: enum `chain` tidak berubah, tidak ada baris hop yang hilang dari ledger, dan artefak yang sudah `APPROVED` bertahan sampai revisinya terbit.
- **GIT TERBATAS**: mutasi sah hanya commit approval `{taskdir}/BRD.md`/`{taskdir}/PRD.md`, commit draft yatim atas nama penulisnya, dan commit pembaruan `{taskdir}/TASK.md` — pencentangan ledger (termasuk penutupannya di Fase 6 langkah 0), pembukaan hop re-entry Fase 3 butir 0, dan transisi eskalasi. Penulisan ulang `## Success Criteria` maupun `## Out of Scope` bukan salah satunya: itu amandemen akar milik gerbang, dirutekan lewat Fase 4a. Dilarang `git add .`/`-A`, `push`, `merge`, `rebase`, `branch`, dan `checkout`.
- **PINTU MASUK TUNGGAL**: skill ini berangkat hanya dari gerbang `backenddev:tech-lead` bersama `taskdir` terprovisi dan `risk` tertetapkan. Permintaan user langsung dikembalikan ke gerbang; dilarang memprovisi taskdir atau branch sendiri.
- **APPROVAL HANYA BRD & PRD**: brief lahir `READY` tanpa gerbang approval terpisah. Dilarang menahan brief menunggu persetujuan user atau menulis `status: APPROVED` pada brief.
- **PEMILIK TUNGGAL APPROVAL**: `status: APPROVED` `BRD.md` dan `PRD.md` ditulis skill ini dan tidak ada pihak lain — bukan penulis dokumennya, bukan gerbang, bukan user langsung. Laporan hop yang menyatakan approval sudah diminta atau sudah ditulis di hulu adalah pelanggaran batas; kembalikan hop itu lewat `## Failure path` butir 3.
- **RATIONALIZATION PREVENTION**: dilarang menetapkan `chain: BRIEF` demi memangkas hop ("kontraknya kelihatan jelas") tanpa bukti `file:line`; menafsirkan keheningan user sebagai persetujuan Fase 4; mengarang laporan penutup skill hop yang gagal; melewati Fase 5 karena pemicunya "kecil"; atau menyatakan artefak ter-commit saat `git commit` mengembalikan kode keluar bukan nol.

## Output [REQUIRED]

Vonis `READY_FOR_IMPLEMENTATION` (15/15) → tutup satu baris tanpa blok: `### PLANNING CHAIN REPORT — READY_FOR_IMPLEMENTATION (15/15) · <taskdir> · Chain <enum> · Risk <level> · Brief <n> READY @ <sha>`, ditambah baris `Verifikasi Manual` bila ada. Selain itu, sajikan blok berikut dan hapus tiap baris bernilai `—`:

```markdown
### PLANNING CHAIN REPORT — NOT_READY_FOR_IMPLEMENTATION
- **Rantai** : <taskdir> · Chain <enum> · Risk <BREAKING | MAJOR | MINOR>
- **Gerbang**: <predikat gagal beserta ID> — <bukti tiap kegagalan>
- **Hop**    : tertahan di <HOP> · TASK <sha> · BRD <sha | —> · PRD <sha | —> · BRIEF <n READY @ sha | —>
- **Re-entry**: <n>/2 · hop <HOP> dibuka karena <reentry_reason> @ <sha> | — (putaran `REVIEW P1` ikut memakan plafon ini; putaran P1 ketiga kembali ke gerbang)
- **Verifikasi Manual**: <tiap `AC-{n}` bertanda `QA manual:` + brief pengklaim + langkah konkretnya> | —
- **Catatan**: <eskalasi · amandemen akar · `BR-DISANGGAH` disetujui user · asumsi `sementara dipakai:` pembentuk kontrak> | —
```

Enum vonis dibaca `backenddev:tech-lead` `## Failure path` butir 7 — tulis utuh, dilarang diparafrase. `Verifikasi Manual` bertahan sekalipun rantai bersih: konsumennya user, dan langkah uji yang tidak digerbangi test tidak punya tempat lain untuk muncul. Ledger `## Chain`, justifikasi dua sumbu Fase 1, dan keputusan lingkup Fase 4a sudah ter-commit di taskdir — dilarang menyalinnya.

Tutup satu baris: `kembali ke backenddev:tech-lead | Taskdir: <path> | Gerbang: <vonis>`.

## Failure path

1. **Chain bertentangan dengan artefak**: taskdir sudah memuat artefak hop yang tidak ada di `chain` hasil derivasi → hentikan, laporkan salah rute ke gerbang. Dilarang menghapus artefak atau menyesuaikan chain agar cocok.
2. **Akar gagal terkunci**: `task` menutup dengan uji akar gagal atau commit gagal → hentikan rantai sebelum hop pertama, teruskan rincian kegagalannya ke gerbang. Dilarang menulis `TASK.md` sendiri.
3. **Hop gagal menerbitkan artefak**: skill hop menutup tanpa artefak, atau artefaknya tidak lolos self-review internalnya → pertahankan ledger apa adanya, laporkan hop yang tertahan beserta alasan mentahnya, serahkan ke gerbang. Dilarang melanjutkan ke hop berikutnya.
4. **Approval tertahan berulang**: hop yang sama ditolak user dua kali → hentikan rantai, sajikan poin penolakan terakhir, serahkan keputusan lingkup ke gerbang.
5. **Eskalasi melampaui plafon atau pasangan ilegal**: transisi `chain` ketiga pada satu taskdir, atau transisi yang menghasilkan pasangan `(risk, chain)` di luar tabel bagian 1.4 → hentikan, laporkan pemicunya berurutan beserta pasangan yang ditolak, minta gerbang mengklasifikasi ulang permintaan dari awal. Dilarang menambal pasangan ilegal dengan menurunkan salah satu nilainya.
6. **Commit gagal**: `git commit` approval atau pembaruan `TASK.md` mengembalikan kode keluar bukan nol → pertahankan berkas di working tree beserta status jujurnya, sertakan galat mentah, serahkan penguncian ke gerbang. Dilarang `--no-gpg-sign` atau staging wildcard.
7. **Pertanyaan terbuka tak kunjung tuntas**: hop yang sama dikembalikan tiga kali karena `## Open questions`-nya memblokir → hentikan rantai, sajikan daftar pertanyaan yang belum terjawab beserta seksi terdampaknya, serahkan keputusan lingkup ke gerbang. Dilarang meloloskan entri memblokir ke gerbang approval demi memutus loop.
8. **Amandemen akar melampaui plafon**: permintaan amandemen `## Success Criteria`/`## Out of Scope` ketiga pada satu taskdir → hentikan rantai, sajikan ketiga permintaan berurutan beserta keputusan user atas dua yang pertama, minta gerbang mengklasifikasi ulang permintaan dari awal. Akar yang diamandemen tiga kali salah dirumuskan sejak awal, bukan kurang tambalan.
9. **Re-entry melampaui plafon atau tanpa alasan**: re-entry ketiga pada satu taskdir, atau `reentry_reason` kosong pada taskdir yang ledger-nya sudah tercentang penuh → hentikan rantai, sajikan riwayat re-entry beserta hop yang dibuka tiap kali, minta gerbang mengklasifikasi ulang permintaan dari awal. Rantai yang dibuka tiga kali pada taskdir yang sama salah dipecah sejak perencanaan, bukan kurang satu putaran lagi. Dilarang membuka hop tanpa alasan tertulis, membuka lebih dari satu hop hulu sekaligus, atau menurunkan status artefak hop yang dibuka.

## STYLE

- Gunakan fase bernomor dan kalimat imperatif aktif tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku dan istilah teknis asli stack.
- Sebut nama chain, hop, risk level, dan status artefak persis sesuai enum.
- Berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
