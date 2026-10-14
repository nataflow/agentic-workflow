---
name: analyst
description: Dipanggil gerbang backend:tech-lead sesudah lane PLANNING ditetapkan dan taskdir terprovisi - orkestrasi rantai TASK/BRD/PRD/brief beserta gerbang approval dokumen, sebelum brief READY diserahkan ke fase eksekusi
user-invocable: false
---

## THE IRON LAW

- Tetapkan `chain` sekali di Fase 1 dan materaikan ke `TASK.md`; seluruh hilir membaca nilai itu, bukan menebaknya dari keberadaan berkas.
- Jalankan hop rantai berurutan sampai brief `READY` terbit; dilarang melompati hop yang tercantum di ledger `## Chain`.
- Tulis nol baris isi `BRD.md`, `PRD.md`, dan `brief-*.md` — skill ini mengorkestrasi, penulisnya skill hop.
- Naikkan `chain` saat pemicu eskalasi aktif dan jangan pernah menurunkannya.
- Dilarang menyentuh `src/` dan menjalankan mutasi git: dokumen taskdir tidak di-commit (Langkah 24), dan approval, ledger, re-entry, serta eskalasi dikunci di disk lewat `doc_seal.py`/`chain_counters.py`.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyst/scripts/check_preconditions.py --taskdir <taskdir> --risk <risk> [--chain <chain>]`.
2. `PASS` (7/7 checks) → lanjut ke Workflow; baris check 7 (`Resume Point`) menentukan titik masuk Fase 0. `FAIL` → hentikan dan remediasi butir gagal: taskdir belum sah atau belum diprovisi → minta alokasi ke `backend:tech-lead`; profil belum lengkap → `backend:profile`; `risk` di luar enum → minta gerbang menetapkannya; artefak taskdir bertentangan dengan `chain` → laporkan salah rute ke gerbang; working tree kotor di luar taskdir → bersihkan dulu; check 7 `TASK.md tanpa ledger` → kembalikan ke gerbang, taskdir lane non-planning dirutekan ke `plan` jalur `RCA` atau `debug` (`tech-lead/references/gate-lifecycle.md` bagian 1); check 7 `## Counters` disunting tangan → pulihkan nilainya dari entri terakhir `{taskdir}/.explore/counters-log.json` (log `chain_counters.py`; `TASK.md` tidak punya riwayat git sejak Langkah 24), dilarang melanjutkan di atas plafon yang dikosongkan.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — path taskdir hasil provisi gerbang; wajib cocok pola `backenddev/docs/<YYMMDDhhmm>-<slug>/`.
- `risk` — enum — `[REQUIRED]` — `BREAKING` | `MAJOR` | `MINOR` hasil Keputusan 2 gerbang; penentu utama derivasi `chain`.
- `request` — string — `[REQUIRED]` — permintaan user sebagai bahan mentah; diteruskan apa adanya ke `task`.
- `evidence` — list — `[REQUIRED]` — minimal satu `file:line` hasil eksplorasi Fase 1 gerbang; daftar kosong menghentikan skill.
- `clarification` — list — default `[]` — pasangan tanya-jawab gerbang; diteruskan ke `task` sebagai sumber `## Out of Scope`.
- `file_scope` — string — `[REQUIRED]` — slot `File Scope` laporan rute gerbang; diteruskan apa adanya ke `plan` sebagai pembanding Check E.
- `chain` — enum — default `auto` — `BRD_PRD_BRIEF` | `PRD_BRIEF` | `BRIEF`; `auto` menurunkannya dari dua sumbu Fase 1.
- `finding_source` — string — default `""` — Path berkas temuan asal (`backenddev/issues/<file>.md` atau `{taskdir}/REVIEW.md`) saat akar berangkat dari temuan terpilih; kosong pada permintaan kerja biasa. Diteruskan apa adanya ke `task` dan `plan` menurut bagian 2.1 `references/chain-rules.md`; dilarang disimpulkan dari isi `request`.
- `ticket_source` — string — default `""` — Path `TICKET.md` `READY` analyst dari slot `Ticket Source` gerbang; kosong bila akar tidak berangkat dari tiket. Menyalakan pengakuan `TBR-{n}` di bagian 1.1 `references/chain-rules.md`, lalu diteruskan apa adanya ke `task` dan, bila sumbu bisnis tetap aktif, ke `business-analysis` (bagian 2.1). Dilarang disimpulkan dari isi `request`.
- `reentry_reason` — string — default `""` — Alasan gerbang mengembalikan taskdir yang ledger-nya sudah tercentang penuh: predikat gerbang yang gagal, perintah verifikasi penutup yang merah, atau daftar berkas yatim. Terisi → Fase 3 butir 0 berangkat lebih dulu. Kosong pada taskdir berledger penuh → rantai berhenti tanpa hop yang dapat dijalankan; minta gerbang menyebutkan alasannya, dilarang menebak hop pemiliknya.

## Workflow

### Fase 0 — Resume Taskdir Berakar

Jalankan sebelum Fase 1 tiap kali skill ini berangkat.

1. `{taskdir}/TASK.md` tidak ada (check 7: `rantai baru`) → lanjut ke Fase 1.
2. `TASK.md` ada → **dilarang memanggil `backend:task`** dan dilarang menurunkan `chain` ulang: Fase 1 dan 2 dilewati. Pakai `chain:` dan `risk:` frontmatter; parameter gerbang yang berbeda sudah ditolak prasyarat check 4. Baca baris `Resume:` check 7 prasyarat.
3. Titik masuk dari ledger `## Chain`: ada hop `[ ]`/`[~]` (`Resume: hop <HOP>`) → Fase 3 pada hop teratas itu, dan artefak hop yang sudah ada (`BRD.md`/`PRD.md` `DRAFT` yang self-review-nya `Approved`) langsung masuk Fase 4 atasnya alih-alih ditulis ulang; ledger tercentang penuh (`butuh reentry_reason`) → Fase 3 butir 0 dengan `reentry_reason` (kosong → `## Failure path` butir 9).
4. Plafon yang berjalan dibaca dari baris `Counters:` check 7 (tabel `## Counters` `TASK.md`), bukan dari ingatan sesi. Seluruh plafon Fase 3–5 dimateraikan lewat `scripts/chain_counters.py`, satu-satunya penulis tabel itu; riwayat tulisannya di `{taskdir}/.explore/counters-log.json` menangkap nilai yang diturunkan tangan.

Tiga keadaan normal masuk lewat jalur ini: taskdir ber-`BRD.md`/`PRD.md` `DRAFT` yang dirutekan gerbang, keberangkatan ulang sesudah amandemen akar, dan keberangkatan ulang sesudah rantai tertahan atau kegagalan hilir.

### Fase 1 — Derivasi & Penguncian Chain

1. Vonis **sumbu bisnis** bagian 1.1 `references/chain-rules.md` atas lima butirnya, lalu **sumbu kontrak** bagian 1.2 atas tiga butirnya. Kedua sumbu dievaluasi terpisah dan masing-masing berpredikat bukti `file:line` atau jawaban user, bukan keyakinan.
2. Turunkan `chain` dari matriks bagian 1.3 atas kedua vonis itu; nilai `chain` eksplisit dari gerbang mengesampingkan derivasi dan tetap diverifikasi terhadap matriks yang sama.
3. Verifikasi pasangan `(risk, chain)` terhadap tabel bagian 1.4. `risk: MINOR` bersumbu kontrak aktif → naikkan `risk` ke `MAJOR` di sini juga dan laporkan butir pemicunya. Pasangan lain yang tidak sah → `## Failure path` butir 1.
4. Panggil `AskUserQuestion` tepat sekali bila salah satu sumbu masih abu-abu sesudah `evidence` dibaca. Tiap opsi memuat konsekuensi rantai: hop yang bertambah dan artefak yang wajib disetujui.
5. Kunci nilai hasilnya beserta vonis kedua sumbunya; vonis itu masuk slot `Justifikasi Chain` laporan penutup.

### Fase 2 — Perumusan Akar Rantai

1. Panggil `backend:task` dengan `taskdir`, `lane` terminal chain (matriks bagian 1.3 `references/chain-rules.md`, kolom keempat), `risk`, `request`, `evidence`, `clarification`, `chain`, `finding_source`, dan `ticket_source` apa adanya.
2. Tangkap laporan `### TASK ROOT LOCKED`; `Uji Akar` bukan `9/9 lolos` atau `Kunci` bernilai `GAGAL` → `## Failure path` butir 2.
3. Verifikasi `TASK.md` **yang baru diterbitkan `task` di giliran ini** memuat frontmatter `chain:` sesuai Fase 1 dan seksi `## Chain` berisi tepat hop chain itu, seluruhnya belum tercentang. Butir ini tidak berlaku pada jalur resume Fase 0.
4. **Sinkron nataflow**: `backend:task` sudah mencerminkan akar yang dikuncinya (Fase 5 butir 5 skill itu). Bawa segmen `Nataflow` laporan `### TASK ROOT LOCKED` ke baris `Nataflow` laporan penutup, tanpa menjalankan prosedurnya lagi; `GAGAL` tidak menahan Fase 3.

### Fase 3 — Eksekusi Hop Rantai

Jalankan hop belum tercentang paling atas pada ledger `## Chain`, satu hop per giliran:

| Hop | Skill | Artefak | Sesudahnya |
|---|---|---|---|
| `BRD` | `backend:business-analysis` | `BRD.md` `DRAFT` | Fase 4 |
| `PRD` | `backend:system-analysis` | `PRD.md` `DRAFT` | Fase 4 |
| `BRIEF` | `backend:plan` | `brief-*.md` `READY` | Fase 6 |

0. **Re-entry — ledger sudah tercentang penuh.** Taskdir yang kembali dari gerbang membawa kegagalan hilir tidak punya hop belum tercentang, sehingga predikat butir 1 tidak pernah terpenuhi dan rantai berhenti tanpa jalan masuk. Bukalah hop-nya lebih dulu, jangan berimprovisasi masuk ke tengah fase. Lima pemicunya: vonis `NOT_READY_FOR_IMPLEMENTATION` yang dikembalikan gerbang, verifikasi penutup `architect` merah karena cacat perencanaan (`architect` Failure path 4b), berkas terdampak yang tak dimiliki `## File scope` brief mana pun, brief `BLOCKED` atau `HALT.md` di taskdir (`reentry_reason` menyebut brief-NN beserta sebab dari `report-NN.md`/`HALT.md`; hop pemilik `BRIEF`), dan temuan `P1` `REVIEW.md` yang dikembalikan gerbang (hop pemilik: `BRIEF`, atau `PRD` bila temuan menunjuk kontrak).

   1. Tetapkan **satu** hop pemilik kegagalannya dari laporan masuk: predikat atau berkas yang gagal menunjuk `brief-*.md` → hop `BRIEF`; menunjuk kontrak, `AC-{n}`, atau permukaan PRD → hop `PRD`; menunjuk aturan bisnis `BR-{n}` → hop `BRD`. Kegagalan yang menunjuk dua hop sekaligus dibuka pada hop **paling hulu**.
   2. Ubah centang hop itu menjadi `- [~] <HOP> — <skill> → <artefak> @ re-entry <n> (was <sidik lama>)`. Hop di bawahnya yang sudah tercentang ikut dibuka menjadi `- [ ]` tanpa penanda: artefaknya tidak dibatalkan, tetapi ia wajib berangkat ulang di atas hasil hop hulu yang baru.
   3. Materaikan hitungan sebelum membuka hop: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyst/scripts/chain_counters.py --taskdir <taskdir> --bump reentry`; `FAIL` → `## Failure path` butir 9. Lolos → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyst/scripts/chain_counters.py --taskdir <taskdir> --reset-hop <HOP>` supaya revisi hop yang dibuka mendapat jatah ronde reviewer, penolakan, dan pengembalian baru.
   4. Pembaruan ledger tinggal di disk, tanpa commit; `<n>` penanda `[~]` dari keluaran `--bump`.
   5. Lanjutkan ke butir 1; hop `[~]` diperlakukan persis seperti hop belum tercentang, dan kembali `[x]` bersidik baru saat ia tuntas (jejak `(was …)` dipertahankan `doc_seal.py`).

   **Artefak hop yang dibuka tidak dihapus dan tidak diturunkan statusnya.** `BRD.md`/`PRD.md` `APPROVED` bertahan `APPROVED` sampai hop itu menerbitkan revisinya, lalu gerbang dokumen Fase 4 berjalan ulang atasnya. Brief `DONE` **tidak pernah** dibuka: ia sudah dieksekusi, dan sisa pekerjaannya adalah brief tambahan pada taskdir yang sama — bukan penulisan ulang riwayat. Brief `BLOCKED` juga tidak dibuka: `plan` menutupnya jadi `SUPERSEDED` lewat brief pengganti.

   **Plafon dua re-entry per taskdir**, dihitung terpisah dari eskalasi chain Fase 5 dan amandemen akar Fase 4a, dan dimateraikan `chain_counters.py` di `## Counters` `TASK.md` — bukan di ingatan sesi. Permintaan ketiga → `## Failure path` butir 9.

1. Serahkan `taskdir`, `chain`, dan `risk` ke tiap skill hop tanpa kecuali; `system-analysis` menerima `risk` bernama `risk_level`, `plan` menerima `entry_mode`, `file_scope`, beserta `finding_source`, dan `business-analysis` menerima `ticket_source` bila terisi, menurut bagian 2.1 `references/chain-rules.md`. Dilarang membiarkan hop menyimpulkan `chain` dari keberadaan berkas.
2. Tangkap laporan penutup skill hop, lalu baca blok `## <BRD|PRD|Brief> Review` reviewer-nya dari `{taskdir}/.explore/review/<brd|prd|brief>.md` — hop menulisnya di sana apa adanya, bukan mencetaknya di chat. Laporan menyatakan artefaknya tidak terbit, penguncian batch brief-nya gagal, verdict reviewer bukan `Approved`, atau berkas review-nya absen → `## Failure path` butir 3.
3. Evaluasi Fase 5 lebih dulu tiap kali laporan hop menyebut pemicu eskalasi; hop dianggap belum tuntas sampai evaluasi itu selesai.
4. Jalankan Fase 4a lebih dulu tiap kali laporan hop meminta amandemen `## Success Criteria` atau `## Out of Scope` `TASK.md`; hop ditahan apa adanya sampai keputusan user turun.
5. Hop `BRIEF` tuntas → langsung ke Fase 6. Hop `BRD` dan `PRD` tuntas → Fase 4.

### Fase 4 — Gerbang Dokumen

Dijalankan atas tiap `BRD.md` dan `PRD.md` sebelum hop berikutnya berangkat, mengikuti bagian 4 `references/chain-rules.md`:

0. Predikat masuk: laporan hop menyatakan self-review lolos, dan `{taskdir}/.explore/review/<brd|prd>.md` memuat blok review reviewer-nya berverdict `Approved` dengan jejak konkret (`references/chain-rules.md` bagian 4 butir 0). Salah satu tidak terpenuhi → fase ini tidak berangkat sama sekali; rutekan ke `## Failure path` butir 3.
1. Draft tidak dikunci terpisah: dokumen taskdir tidak di-commit (Langkah 24), dan isi yang disetujui user dimateraikan di butir 4.
2. Verifikasi `## Open questions` artefak: maksimal tiga entri dan tidak satu pun memblokir menurut predikat rumah kanoniknya. Ada yang memblokir → jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyst/scripts/chain_counters.py --taskdir <taskdir> --bump oq_return:<HOP>` lebih dulu (`FAIL` → `## Failure path` butir 7), lalu kembalikan poin revisinya ke skill hop, pertahankan `DRAFT`, ulangi Fase 3 pada hop yang sama. Plafon dua pengembalian per hop. Bump itu sekaligus menolkan `review_round:<HOP>`: revisi yang dikembalikan mendapat ronde reviewer baru, dan loopnya dibatasi plafon `oq_return`.
3. Sajikan ringkasan eksekutif artefak — ringkasan gerbang 3–4 kalimat beserta path-nya, bukan salinan isi artefak — lalu satu `AskUserQuestion`: tiap `BR-DISANGGAH: BR-{n}` PRD dan tiap asumsi aktif `sementara dipakai:` sebagai pertanyaan tersendiri, ditambah pertanyaan persetujuan eksplisit (`references/chain-rules.md` bagian 4 butir 3–4).
4. User menyetujui → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/doc_seal.py approve --taskdir <taskdir> --doc <BRD|PRD> --answer -` dengan jawaban user apa adanya lewat stdin. Skrip menulis `status: APPROVED`, `approved_seal` (sidik isi yang disetujui), dan jawaban user ke frontmatter, lalu mencentang hop itu di ledger `## Chain` `@ APPROVED <sidik12>` dalam satu langkah (`references/chain-rules.md` bagian 4 butir 5); dilarang menulis keduanya dengan tangan. Sesudahnya, jalankan prosedur `tech-lead/references/nataflow-sync.md` (`--taskdir <taskdir>`) supaya dokumen `APPROVED` tercermin seketika; `GAGAL` tidak menahan hop. Lanjut ke hop berikutnya.
5. User menolak → jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyst/scripts/chain_counters.py --taskdir <taskdir> --bump reject:<HOP>` lebih dulu (`FAIL` → `## Failure path` butir 4), lalu pertahankan `DRAFT`, teruskan poin revisi ke skill hop, ulangi Fase 3 pada hop yang sama. Bump itu sekaligus menolkan `review_round:<HOP>`, sehingga revisi yang diminta user mendapat ronde reviewer baru di bawah plafon `reject`.

### Fase 4a — Kanal Amandemen Akar

Dijalankan saat laporan hop mana pun melaporkan aturan atau kontrak yang menyentuh `## Success Criteria` atau `## Out of Scope` `TASK.md`, mengikuti bagian 5 `references/chain-rules.md`:

1. Tahan hop apa adanya: ledger tidak dicentang, artefak tetap `DRAFT`, hop berikutnya tidak berangkat.
2. Sajikan butir akar yang tersentuh beserta aturan atau kontrak penyentuhnya lewat `AskUserQuestion`, dengan dua konsekuensi eksplisit: akar diamandemen, atau butir hilir dibuang.
3. User membuang butir hilir → teruskan keputusannya apa adanya ke skill hop, ulangi Fase 3 pada hop yang sama, catat butirnya di slot `Keputusan Lingkup`.
4. User memilih amandemen → hentikan rantai, serahkan rumusan amandemennya ke gerbang. Dilarang menulis ulang `## Success Criteria` maupun `## Out of Scope` sendiri; mutasi `TASK.md` milik skill ini terbatas pada pencentangan ledger dan transisi eskalasi.
5. Plafon dua amandemen per taskdir: sebelum butir 2, jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyst/scripts/chain_counters.py --taskdir <taskdir> --bump root_amendment`; `FAIL` → `## Failure path` butir 8.

### Fase 5 — Evaluasi Eskalasi Chain

1. Sandingkan laporan hop dengan empat pemicu bagian 3 `references/chain-rules.md`. Nol pemicu aktif → kembali ke Fase 3.
2. Pemicu aktif → jalankan prosedur transisi lima langkah bagian itu apa adanya: verifikasi pasangan `(risk, chain)` hasil transisi terhadap tabel bagian 1.4 lebih dulu, tulis ulang frontmatter dan ledger `## Chain`, tulis ulang klausa `— verifikasi:` tiap `SC-{n}` agar cocok lane baru tanpa mengubah prosa hasilnya, jalankan ulang `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind task --taskdir <taskdir>` tanpa `--fresh` (self-test akar, termasuk T8a; `«validate_doc.py»` di `references/chain-rules.md` berarti path ini), tanpa commit.
3. Kembali ke Fase 3 pada hop baru yang belum tercentang; hop yang sudah tercentang beserta artefaknya dipertahankan apa adanya.
4. Plafon dua transisi `chain` per taskdir: sebelum butir 2 menulis ulang ledger, jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyst/scripts/chain_counters.py --taskdir <taskdir> --bump chain_transition`; `FAIL` → `## Failure path` butir 5. Kenaikan `risk` tanpa transisi chain (pemicu 4) tidak dihitung.

### Fase 6 — Gerbang `READY_FOR_IMPLEMENTATION` & Serah Terima

Ini satu-satunya titik yang memeriksa rantai sebagai satu kesatuan. Tiap skill hulu memeriksa dokumennya sendiri; tidak ada yang memeriksa sambungannya sekali lagi sesudah brief terbit.

0. **Tutup ledger.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/doc_seal.py tick --taskdir <taskdir> --hop BRIEF` mencentang hop `BRIEF` di `## Chain` `TASK.md` beserta sidik batch brief terkunci (`- [x] BRIEF — backend:plan → brief-*.md @ READY <sidik12>`). Brief tidak melewati gerbang dokumen Fase 4, tetapi ia tetap hop ledger — tanpa langkah ini predikat B di bawah mustahil dipenuhi dan tiap rantai bervonis `NOT_READY_FOR_IMPLEMENTATION` betapapun benar isinya. Skrip menolak brief yang belum dikunci `plan` atau disunting sesudahnya → lewati pencentangan, jangan menulisnya dengan tangan, dan biarkan predikat B gagal apa adanya.
   **Sinkron nataflow** sesudah langkah ini, apa pun hasil `tick`-nya: jalankan prosedur `tech-lead/references/nataflow-sync.md` (`--taskdir <taskdir>`) di main loop supaya batch brief terkunci dan centang ledger `BRIEF` tercermin seketika — kunci batch adalah titik approval brief, karena brief tidak melewati gerbang dokumen Fase 4. Payload hanya membawa brief yang sudah dikunci. Butir 1–4 hanya membaca, jadi segmen ini segmen terakhir rantai; `GAGAL` tidak menahan vonis.
1. **Vonis lima belas predikat** berikut, satu baris hasil per predikat. Satu predikat gagal → status `NOT_READY_FOR_IMPLEMENTATION`; laporkan predikat yang gagal beserta ID yang membuatnya gagal, dan dilarang menurunkannya jadi catatan serah terima.

   | # | Predikat |
   |---|---|
   | A | `TASK.md` `status: ACTIVE`, self-test akar 9/9 lolos, akar terkunci (`base_commit` sah) |
   | B | Ledger `## Chain` tercentang penuh, tiap centang membawa sidik |
   | C | `BRD.md` `APPROVED` bila `chain: BRD_PRD_BRIEF`, verdict `brd-reviewer` `Approved` apa adanya di `{taskdir}/.explore/review/brd.md` |
   | D | `PRD.md` `APPROVED` bila `chain` ber-PRD, verdict `prd-reviewer` `Approved` apa adanya di `{taskdir}/.explore/review/prd.md` |
   | E | Tiap `brief-*.md` berstatus `READY`, `DONE`, atau `SUPERSEDED` bertaut (Check C `validate_briefs.py` tanpa pelanggaran tautan); yang `READY` terkunci satu batch (`sidik_kontrak` utuh); verdict `brief-reviewer` `Approved` apa adanya di `{taskdir}/.explore/review/brief.md`. `BLOCKED` tetap gagal — ia wajib sudah digantikan brief ber-`supersedes` |
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

   > Rasional: `references/rationale.md` R1.

   Predikat F–M diperiksa ulang di sini sekalipun sudah ditagih hulu: penagihan hulu berlaku per dokumen dan per batch, sedangkan rantai bisa putus di sambungannya — misalnya brief yang menutup seluruh AC PRD sementara satu `SC-{n}` akar tak pernah dipetakan ke AC mana pun. G2 dan H2 hadir karena alasan yang sama persis dengan H: `SC-{n}` dan `EC-{n}` diangkut kolom PRD yang sama dengan `BR-{n}`, dan sumbu yang diperiksa hanya di hulu putus tanpa suara di sini.

2. Sajikan `## Output [REQUIRED]` beserta vonis gerbang ini.
3. Kelima belas predikat lolos → kembalikan kendali ke `backend:tech-lead` untuk merutekan fase eksekusi ke `backend:architect`, beserta slot `Verifikasi Manual` yang mengenumerasi tiap `AC-{n}` bertanda `QA manual:` — itu satu-satunya bentuk verifikasi AC tersebut, dan tanpa enumerasi ini ia tidak sampai ke gerbang penutup. Dilarang memanggil `architect` maupun `code-implementor` sendiri.
4. Status `NOT_READY_FOR_IMPLEMENTATION` → serahkan ke gerbang beserta daftar predikat yang gagal; dilarang menyerahkan rantai sebagai selesai.

## Guardrails

- **ORKESTRASI, BUKAN PENULISAN — dan predikatnya terbaca dari materai**: dilarang menulis, menyunting, atau menambal isi `BRD.md`, `PRD.md`, dan `brief-*.md`. Revisi dikembalikan ke skill hop penulisnya beserta poin perbaikannya.

  Batas ini tidak dapat ditegakkan oleh isolasi runtime — giliran yang sama memuat skill ini dan skill hop yang menulis, dan tidak ada yang memisahkan keduanya selain niat. Dokumen taskdir tidak di-commit (Langkah 24), jadi yang menggantikan isolasi adalah **materai di disk** yang ditulis skrip: `approved_seal` `BRD.md`/`PRD.md` (sidik isi yang disetujui user, Fase 4 butir 4 — prasyarat hilir menagihnya) dan `sidik_kontrak` tiap brief (dikunci `plan` lewat `doc_seal.py lock-briefs`, ditagih `verify_scope.py` dan `tick`). Fase 6 memverifikasinya lewat `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/doc_seal.py status --taskdir <taskdir>` pada predikat A–E. Suntingan sesudah dokumen dimateraikan adalah pelanggaran batas yang **terbaca**, dan dilaporkan apa adanya di slot `Catatan`, bukan didiamkan karena "toh isinya benar". Batasnya dinyatakan apa adanya: suntingan `DRAFT` sebelum approval tidak meninggalkan jejak.
- **NOL SENTUHAN KODE**: dilarang membaca-tulis di bawah `source_root`, menjalankan build atau test, dan membuat berkas di luar `{taskdir}`.
- **CHAIN SATU ARAH**: dilarang menurunkan `chain`, membatalkan artefak hop yang sudah `APPROVED`, atau melompati hop yang tercantum di ledger dengan alasan artefaknya "tidak diperlukan". Membuka hop jadi `[~]` di Fase 3 butir 0 bukan penurunan chain: enum `chain` tidak berubah, tidak ada baris hop yang hilang dari ledger, dan artefak yang sudah `APPROVED` bertahan sampai revisinya terbit.
- **NOL MUTASI GIT**: skill ini tidak men-stage dan tidak meng-commit apa pun. Mutasi sahnya di disk: materai approval `doc_seal.py approve`, pencentangan ledger (termasuk penutupannya di Fase 6 langkah 0, `doc_seal.py tick`), pembukaan hop re-entry Fase 3 butir 0, dan transisi eskalasi `TASK.md`. Penulisan ulang `## Success Criteria` maupun `## Out of Scope` bukan salah satunya: itu amandemen akar milik gerbang, dirutekan lewat Fase 4a. Dilarang `git add`, `commit`, `push`, `merge`, `rebase`, `branch`, dan `checkout`.
- **PINTU MASUK TUNGGAL**: skill ini berangkat hanya dari gerbang `backend:tech-lead` bersama `taskdir` terprovisi dan `risk` tertetapkan. Permintaan user langsung dikembalikan ke gerbang; dilarang memprovisi taskdir atau branch sendiri.
- **APPROVAL HANYA BRD & PRD**: brief lahir `READY` tanpa gerbang approval terpisah. Dilarang menahan brief menunggu persetujuan user atau menulis `status: APPROVED` pada brief.
- **PEMILIK TUNGGAL APPROVAL**: `status: APPROVED` `BRD.md` dan `PRD.md` ditulis skill ini dan tidak ada pihak lain — bukan penulis dokumennya, bukan gerbang, bukan user langsung. Laporan hop yang menyatakan approval sudah diminta atau sudah ditulis di hulu adalah pelanggaran batas; kembalikan hop itu lewat `## Failure path` butir 3.
- **RATIONALIZATION PREVENTION**: dilarang menetapkan `chain: BRIEF` demi memangkas hop ("kontraknya kelihatan jelas") tanpa bukti `file:line`; menafsirkan keheningan user sebagai persetujuan Fase 4; mengarang laporan penutup skill hop yang gagal; melewati Fase 5 karena pemicunya "kecil"; atau menyatakan artefak terkunci saat `doc_seal.py` mengembalikan kode keluar bukan nol.

## Output [REQUIRED]

Vonis `READY_FOR_IMPLEMENTATION` (15/15) → tutup satu baris tanpa blok: `### PLANNING CHAIN REPORT — READY_FOR_IMPLEMENTATION (15/15) · <taskdir> · Chain <enum> · Risk <level> · Brief <n> READY @ <sidik12>`, ditambah baris `Nataflow: <segmen sinkron Fase 6>` dan baris `Verifikasi Manual` bila ada. Selain itu, sajikan blok berikut dan hapus tiap baris bernilai `—`:

```markdown
### PLANNING CHAIN REPORT — NOT_READY_FOR_IMPLEMENTATION
- **Rantai** : <taskdir> · Chain <enum> · Risk <BREAKING | MAJOR | MINOR>
- **Gerbang**: <predikat gagal beserta ID> — <bukti tiap kegagalan>
- **Hop**    : tertahan di <HOP> · TASK <base_commit 7 digit> · BRD <sidik12 | —> · PRD <sidik12 | —> · BRIEF <n READY @ sidik12 | —>
- **Re-entry**: <n>/2 · hop <HOP> dibuka karena <reentry_reason> | — (putaran `REVIEW P1` ikut memakan plafon ini; putaran P1 ketiga kembali ke gerbang)
- **Verifikasi Manual**: <tiap `AC-{n}` bertanda `QA manual:` + brief pengklaim + langkah konkretnya> | —
- **Nataflow**: <segmen sinkron terakhir (`tech-lead/references/nataflow-sync.md`)> | —
- **Catatan**: <eskalasi · amandemen akar · `BR-DISANGGAH` disetujui user · asumsi `sementara dipakai:` pembentuk kontrak> | —
```

Enum vonis dibaca `backend:tech-lead` `## Failure path` butir 7 — tulis utuh, dilarang diparafrase. `Verifikasi Manual` bertahan sekalipun rantai bersih: konsumennya user, dan langkah uji yang tidak digerbangi test tidak punya tempat lain untuk muncul. Ledger `## Chain`, justifikasi dua sumbu Fase 1, dan keputusan lingkup Fase 4a sudah tertulis di taskdir — dilarang menyalinnya.

Tutup satu baris: `kembali ke backend:tech-lead | Taskdir: <path> | Gerbang: <vonis>`.

## Failure path

1. **Chain bertentangan dengan artefak**: taskdir sudah memuat artefak hop yang tidak ada di `chain` hasil derivasi → hentikan, laporkan salah rute ke gerbang. Dilarang menghapus artefak atau menyesuaikan chain agar cocok.
2. **Akar gagal terkunci**: `task` menutup dengan uji akar gagal atau kunci gagal → hentikan rantai sebelum hop pertama, teruskan rincian kegagalannya ke gerbang. Dilarang menulis `TASK.md` sendiri.
3. **Hop gagal menerbitkan artefak**: skill hop menutup tanpa artefak, atau artefaknya tidak lolos self-review internalnya → pertahankan ledger apa adanya, laporkan hop yang tertahan beserta alasan mentahnya, serahkan ke gerbang. Dilarang melanjutkan ke hop berikutnya.
4. **Approval tertahan berulang**: hop yang sama ditolak user dua kali → hentikan rantai, sajikan poin penolakan terakhir, serahkan keputusan lingkup ke gerbang.
5. **Eskalasi melampaui plafon atau pasangan ilegal**: transisi `chain` ketiga pada satu taskdir, atau transisi yang menghasilkan pasangan `(risk, chain)` di luar tabel bagian 1.4 → hentikan, laporkan pemicunya berurutan beserta pasangan yang ditolak, serahkan ke gerbang: ia bertanya ke user rumuskan ulang di taskdir baru atau hentikan (`tech-lead` `## Failure path` butir 7). Dilarang menambal pasangan ilegal dengan menurunkan salah satu nilainya.
6. **Materai gagal**: `doc_seal.py approve` atau `tick` mengembalikan kode keluar bukan nol → pertahankan berkas di disk beserta status jujurnya, sertakan keluaran skrip apa adanya, serahkan ke gerbang. Dilarang menulis `status: APPROVED`, `approved_seal`, atau centang ledger dengan tangan.
7. **Pertanyaan terbuka tak kunjung tuntas**: hop yang sama dikembalikan tiga kali karena `## Open questions`-nya memblokir → hentikan rantai, sajikan daftar pertanyaan yang belum terjawab beserta seksi terdampaknya, serahkan keputusan lingkup ke gerbang. Dilarang meloloskan entri memblokir ke gerbang approval demi memutus loop.
8. **Amandemen akar melampaui plafon**: permintaan amandemen `## Success Criteria`/`## Out of Scope` ketiga pada satu taskdir → hentikan rantai, sajikan ketiga permintaan berurutan beserta keputusan user atas dua yang pertama, serahkan ke gerbang untuk keputusan user rumuskan ulang atau hentikan (`tech-lead` `## Failure path` butir 7). Akar yang diamandemen tiga kali salah dirumuskan sejak awal, bukan kurang tambalan.
9. **Re-entry melampaui plafon atau tanpa alasan**: re-entry ketiga pada satu taskdir, atau `reentry_reason` kosong pada taskdir yang ledger-nya sudah tercentang penuh → hentikan rantai, sajikan riwayat re-entry beserta hop yang dibuka tiap kali, serahkan ke gerbang untuk keputusan user rumuskan ulang atau hentikan (`tech-lead` `## Failure path` butir 7). Rantai yang dibuka tiga kali pada taskdir yang sama salah dipecah sejak perencanaan, bukan kurang satu putaran lagi. Dilarang membuka hop tanpa alasan tertulis, membuka lebih dari satu hop hulu sekaligus, atau menurunkan status artefak hop yang dibuka.

## STYLE

- Gunakan fase bernomor dan kalimat imperatif aktif tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku dan istilah teknis asli stack.
- Sebut nama chain, hop, risk level, dan status artefak persis sesuai enum.
- Berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
