# Aturan Rantai Planning — `analyst`

Derivasi `chain` (bagian 1), pemetaan hop ke parameter skill (bagian 2), pemicu dan transisi eskalasi (bagian 3), protokol gerbang dokumen (bagian 4), serta kanal amandemen akar (bagian 5). Ini **rumah kanonik** enum `chain`, ledger `## Chain`, kepemilikan `status: APPROVED`, dan rute amandemen `TASK.md` di tengah rantai; `task`, `business-analysis`, `system-analysis`, `plan`, dan ketiga reviewer dokumen merujuk ke sini, dan dilarang menulis ulang aturannya dengan kata lain.

## 1. Derivasi `chain` (Fase 1)

`chain` menjawab satu pertanyaan: artefak rancangan apa yang wajib terbit sebelum brief boleh ditulis. Jawabannya diturunkan dari **dua sumbu yang dievaluasi terpisah** — sumbu bisnis menentukan BRD, sumbu kontrak menentukan PRD. Keduanya berpredikat bukti dari `evidence` dan kode, bukan keyakinan.

### 1.1 Sumbu bisnis — butuh `BRD.md`?

BRD wajib terbit bila **minimal satu** butir berikut benar:

1. Aturan bisnis yang disentuh belum disepakati user, dan tidak terbukti sebagai konstanta, guard, `BR-{n}` di taskdir mana pun, atau `TBR-{n}` tiket `ticket_source` (`BR-{n}` kartu `TICKET.md` `READY` — sudah disetujui user lewat `analyst:spec`).
2. Alur yang berubah melibatkan lebih dari satu aktor manusia, atau memperkenalkan aktor sistem baru (scheduler, webhook consumer, queue listener).
3. Urutan langkah kerja manusia berubah, bukan hanya perilaku teknis yang menopangnya.
4. Kebijakan operasional berubah: kuota, batas waktu, hak persetujuan, aturan pembatalan, atau aturan pembagian biaya.
5. Ada pertanyaan yang jawabannya menentukan nilai sebuah konstanta atau cabang alur, dan jawabannya tidak ditemukan di kode maupun di taskdir mana pun — permintaan tidak dapat dirumuskan sebagai perubahan perilaku teknis tanpa memutuskan aturan bisnisnya lebih dulu. Ini satu-satunya butir berpredikat penilaian: vonis aktifnya wajib membawa pertanyaan konkret itu ke `AskUserQuestion` Fase 1 butir 4, dilarang disimpulkan sendiri.

**Tiket analyst sebagai bukti kesepakatan.** `ticket_source` terisi → butir 2–4 dinilai hanya atas aktor, urutan kerja, dan kebijakan yang **tidak** tertulis di kartu tiket (H1 sampai akhir `## Lampiran`) atau di pilar `Aktor`/`Aturan Bisnis`/`Kondisi Diinginkan` catatan elisitasinya; yang tertulis dihitung disepakati. Butir 5 aktif hanya untuk pertanyaan yang tidak dijawab tiket. Tiket yang tidak lagi `READY`, atau disunting sesudah approve, bukan bukti — hentikan dan kembalikan ke `analyst:spec`. Bila sumbu tetap aktif karena fakta di luar tiket, BRD terbit dalam mode serap tiket (bagian 2.1).

Nol butir aktif berarti BRD **tidak** terbit — termasuk pada `risk: BREAKING`. Pecahnya kontrak teknis bukan predikat bisnis: menghapus kolom yang nol konsumennya adalah `BREAKING` yang tidak punya satu pun aktor, aturan, atau biaya pembiaran untuk digali, dan BRD yang dipaksakan di atasnya terisi seremonial.

### 1.2 Sumbu kontrak — butuh `PRD.md`?

PRD wajib terbit bila **minimal satu** butir berikut benar:

1. `risk` bernilai `BREAKING`.
2. Ada DTO, endpoint, transisi status, aturan validasi lintas-field, atau aturan permission yang baru atau berubah.
3. Satu saja permukaan yang disentuh belum punya `file:line` di `evidence`.

Nol butir aktif berarti PRD tidak terbit dan brief ditulis langsung di atas akar.

Temuan `backenddev/issues/` dan `{taskdir}/REVIEW.md` dinilai ketiga butir yang sama persis — laporan temuan tidak punya sumbu sendiri, dan severity `P1` bukan predikat kontrak. Temuan yang menyentuh kontrak API, transisi status, validasi lintas-field, atau permission mengaktifkan butir 2 dan karena itu menerbitkan PRD; temuan duplikasi kode atau penamaan tidak mengaktifkan satu butir pun dan turun langsung jadi brief.

### 1.3 Matriks chain

| Sumbu bisnis | Sumbu kontrak | `chain` | Lane terminal |
|---|---|---|---|
| aktif | aktif | `BRD_PRD_BRIEF` | `PRD_CONVERSION` |
| nol | aktif | `PRD_BRIEF` | `PRD_CONVERSION` |
| nol | nol | `BRIEF` | `DIRECT_BRIEF` |
| aktif | nol | **tidak sah** — naikkan ke `BRD_PRD_BRIEF` | `PRD_CONVERSION` |

Baris terakhir adalah satu-satunya kombinasi terlarang, dan alasannya bukan administratif: `BRD.md` berhenti pada aturan bisnis dan tidak pernah menyebut endpoint, DTO, maupun skema. Brief yang lahir langsung darinya memaksa eksekutor menerjemahkan aturan bisnis jadi kontrak sistem sendiri — persis keputusan yang fase planning ada untuk menyelesaikannya. Aturan bisnis yang baru disepakati selalu melewati `system-analysis` lebih dulu.

### 1.4 Batas `risk` & invarian pasangan

| `risk` | `chain` yang sah |
|---|---|
| `BREAKING` | `BRD_PRD_BRIEF`, `PRD_BRIEF` |
| `MAJOR` | `BRD_PRD_BRIEF`, `PRD_BRIEF`, `BRIEF` |
| `MINOR` | `BRIEF` |

- **Invarian pasangan**: tiap penetapan Fase 1 dan tiap transisi bagian 3 wajib menghasilkan pasangan `(risk, chain)` yang sah menurut tabel ini. Pasangan di luar tabel dihentikan dan dilaporkan, bukan ditambal.
- `risk: MINOR` yang sumbu kontraknya aktif dinaikkan ke `MAJOR` di Fase 1 juga — `system-analysis` menolak `risk_level` di luar `BREAKING`/`MAJOR`. Kenaikan ini terjadi **sebelum** akar terkunci sehingga bukan eskalasi bagian 3; laporkan kenaikannya beserta butir sumbu kontrak yang memicunya di slot `Justifikasi Chain`.
- **Lane terminal** adalah nilai yang diteruskan ke `task` sebagai `lane`, dan darinya `task` Fase 3 memilih kolom alat ukur `SC-{n}`. Hanya dua lane planning yang pernah ditulis ke `TASK.md`: `PRD_CONVERSION` dan `DIRECT_BRIEF`. Kriteria akar mengukur hasil akhir rantai, bukan keberadaan dokumen antara.

## 2. Hop, Ledger, dan Parameter Skill

Ledger `## Chain` `TASK.md` memuat **tepat** hop chain-nya, berurutan, satu baris per hop. Hop di luar chain dihapus barisnya — dokumen sendiri yang menyatakan rantainya, sehingga hilir berhenti menyimpulkannya dari keberadaan berkas.

```markdown
## Chain

- [ ] BRD   — backenddev:business-analysis → BRD.md
- [ ] PRD   — backenddev:system-analysis  → PRD.md
- [ ] BRIEF — backenddev:plan             → brief-*.md
```

Hop tuntas dicentang `backenddev:analyst`, seluruhnya tanpa kecuali, beserta jejaknya:

- Hop `BRD` dan `PRD` dicentang di gerbang dokumen bagian 4 butir 5, bersha commit approval-nya: `- [x] PRD — backenddev:system-analysis → PRD.md @ APPROVED a1b2c3d`.
- Hop `BRIEF` dicentang di Fase 6 langkah 0, bersha commit agregat `plan`: `- [x] BRIEF — backenddev:plan → brief-*.md @ READY e4f5g6h`. Brief tidak melewati gerbang dokumen, tetapi ia tetap hop ledger — pengecualian bagian 4 menyangkut **approval**, bukan pencentangan. Hop terminal yang tak berpencentang membuat predikat B gerbang akhir mustahil dipenuhi siapa pun, sehingga rantai yang isinya benar pun selalu bervonis `NOT_READY_FOR_IMPLEMENTATION`.

### 2a. Penanda re-entry `[~]`

Ledger mengenal **tiga** keadaan hop, bukan dua:

| Penanda | Arti | Ditulis di |
|---|---|---|
| `- [ ]` | belum berangkat | `task` saat akar terkunci |
| `- [x] … @ <sha>` | tuntas, jejaknya mendarat | bagian 4 butir 5 (`BRD`/`PRD`) · Fase 6 langkah 0 (`BRIEF`) |
| `- [~] … @ re-entry <n> (was <sha lama>)` | dibuka ulang, sedang dikerjakan lagi | `analyst` Fase 3 butir 0 |

Keadaan ketiga ada karena taskdir yang kembali dari gerbang membawa kegagalan hilir — vonis `NOT_READY_FOR_IMPLEMENTATION`, verifikasi penutup `architect` merah karena cacat perencanaan, atau berkas terdampak yang tak dimiliki brief mana pun — punya ledger tercentang penuh dan karena itu **nol hop yang memenuhi predikat "belum tercentang paling atas"**. Tanpa `[~]`, satu-satunya jalan melanjutkan adalah masuk ke tengah fase secara improvisasi, tepat pada saat rantai paling butuh determinisme.

`[~]` diperlakukan persis seperti `[ ]` oleh Fase 3, dan kembali `[x]` bersha **baru** saat hop-nya tuntas; sha lama bertahan di dalam kurung sebagai jejak. Predikat B gerbang akhir menuntut ledger tercentang penuh, sehingga satu `[~]` yang tersisa memang menahan vonis `READY_FOR_IMPLEMENTATION` — itu perilaku yang benar, bukan kebocoran.

Taskdir yang sudah berakar masuk lewat `analyst` Fase 0 Resume; `task` hanya dipanggil pada taskdir tanpa `TASK.md`, dan titik masuknya dibaca dari baris `Resume:` check 7 prasyarat `analyst`.

Membuka hop **tidak menurunkan status artefaknya**: `BRD.md`/`PRD.md` `APPROVED` bertahan `APPROVED` sampai revisinya terbit, lalu gerbang dokumen bagian 4 berjalan ulang atasnya. Brief `DONE` tidak pernah dibuka — sisa pekerjaan atasnya adalah brief tambahan pada taskdir yang sama. Plafon dua re-entry per taskdir, dihitung terpisah dari eskalasi bagian 3 dan amandemen akar bagian 5.

### 2.1 Parameter yang diteruskan ke tiap hop

| `chain` | Ledger | Hop `BRD` | Hop `PRD` | Hop `BRIEF` |
|---|---|---|---|---|
| `BRD_PRD_BRIEF` | BRD, PRD, BRIEF | `business-analysis` | `system-analysis`, `risk_level` = `risk` akar | `plan`, `entry_mode: PRD` |
| `PRD_BRIEF` | PRD, BRIEF | — | `system-analysis`, `risk_level` = `risk` akar | `plan`, `entry_mode: PRD` |
| `BRIEF` | BRIEF | — | — | `plan`, `entry_mode: LANGSUNG` |

**Parameter yang dipikul setiap hop tanpa kecuali:**

- `taskdir` — path taskdir aktif.
- `chain` — nilai enum yang dimateraikan di `TASK.md`. Diteruskan **eksplisit**, tidak disimpulkan hilir. Ia menyatakan dokumen hulu mana yang memang dijadwalkan terbit, dan tanpanya ketiga reviewer dokumen tidak dapat membedakan "dokumen sah tidak ada" dari "rantai putus" — slot `Chain` di ketiga template reviewer (`business-analysis/dispatcher/reviewer.md`, `system-analysis/dispatcher/reviewer.md`, `plan/dispatcher/reviewer.md`) dihidrasi dari nilai ini.
- `risk` — `risk:` frontmatter `TASK.md`. `plan` memakainya sebagai plafon Check K; `system-analysis` menerimanya bernama `risk_level`.

**Parameter tambahan hop `BRIEF`:** `file_scope` — `File Scope` laporan rute gerbang, diteruskan `analyst` apa adanya. Tanpanya Check E `plan` tidak punya pembanding, karena `plan` pada lane planning dipanggil `analyst` dan tidak pernah membaca laporan gerbang sendiri.

**`finding_source` — penanda akar yang berangkat dari temuan.** Gerbang mengisinya dengan path berkas temuan (`backenddev/issues/<file>.md` atau `{taskdir}/REVIEW.md`) dan mengosongkannya pada permintaan kerja biasa. `analyst` meneruskannya apa adanya ke **dua** titik: ke `task`, yang menambahkan penandaan baris `> Status:` ke alat ukur tiap `SC-{n}` pemikul temuan; dan ke `plan`, yang menyalakan re-verification temuan beserta pembuangan `PLAUSIBLE` tak terjawab di Fase 2-nya. Hop `BRD` dan `PRD` tidak memikulnya — keduanya bekerja atas aturan dan kontrak, bukan atas berkas laporan.

Nilai ini menempel pada **asal-usul akar**, bukan pada panjang rantai, sehingga ketiga aturan di atas ikut berjalan pada rantai ber-PRD juga. Nilai yang putus di tengah rantai tidak menghasilkan kegagalan yang terlihat: ia mematikan ketiganya diam-diam, dan temuan yang sudah diperbaiki orang lain tetap masuk batch lalu dikerjakan ulang.

**`ticket_source` — penanda akar yang berangkat dari tiket analyst.** Gerbang mengisinya dengan path `TICKET.md` `READY` (`tech-lead/references/gate-scope.md` bagian 4 B-2) dan mengosongkannya pada permintaan lain. `analyst` meneruskannya apa adanya ke `task`, yang menagih keterpikulan tiap `TAC-{n}` (Fase 3 butir 7), dan — bila sumbu bisnis bagian 1.1 tetap aktif — ke `business-analysis`, yang menyerap tiap `TBR-{n}` ke `## Business rules` sebagai `BR-{n}` berakhiran `— Asal: TBR-{m}` tanpa menanyakannya ulang. Hop `PRD` dan `BRIEF` tidak memikulnya; keterlacakan tiket mengalir lewat `SC-{n}`. Kartu menulis `AC-{n}`/`BR-{n}`; di artefak backenddev keduanya selalu dirujuk `TAC-{n}`/`TBR-{n}` agar tidak bertabrakan dengan `AC-{n}` PRD dan `BR-{n}` BRD.

`entry_mode` diteruskan eksplisit ke `plan` sebagai salah satu dari `PRD` | `RCA` | `LANGSUNG`. Nilai bawaan dan resolusi dari artefak di disk sudah dihapus dari kontrak `plan`: keduanya menyimpulkan jalur dari apa yang kebetulan ada, sehingga chain ber-PRD yang PRD-nya gagal terbit turun diam-diam jadi jalur `LANGSUNG` dan seluruh pemeriksaan ber-gate PRD dilewati tanpa satu pun kegagalan tercatat. `plan` yang dipanggil tanpa nilai ini berhenti di check 3 prasyaratnya.

Jalur `RCA` `plan` tidak diorkestrasi skill ini: ia berangkat dari `RCA.md` milik `debug`, dan gerbang merutekannya langsung ke `plan`. Perbaikan temuan `audit` dan `{taskdir}/REVIEW.md` **bukan** jalur semacam itu — ia masuk lewat lane `PLANNING` seperti permintaan kerja lain, chain-nya diturunkan bagian 1, dan `plan`-nya dimasuki lewat `entry_mode` kolom terakhir tabel di atas. Satu-satunya yang membedakannya dari permintaan biasa adalah `finding_source`.

## 3. Pemicu & Transisi Eskalasi (Fase 5)

Eskalasi menaikkan chain satu tingkat. Arahnya satu jalan: artefak yang sudah terbit dan disetujui dipertahankan, hop yang bertambah disisipkan sebelum hop yang tersisa.

| # | Pemicu | Sumber laporan | Transisi `chain` | `risk` |
|---|---|---|---|---|
| 1 | Satu dari 5 pemicu eskalasi `plan` aktif (kontrak API, transisi status, validation policy, permission/scope, side-effect lintas modul) | `plan` menutup dengan eskalasi `entry-rules.md` bagian 1A | `BRIEF` → `PRD_BRIEF` | `MINOR` → `MAJOR`; `MAJOR` dan `BREAKING` tetap |
| 2 | `risk:` brief yang dituntut predikat derivasi melampaui plafon akar | `plan` Failure path butir 6 (Check K) | `BRIEF` → `PRD_BRIEF` | naikkan ke nilai yang dituntut predikat |
| 3 | Sumbu bisnis bagian 1.1 yang semula nol ternyata aktif — aturan bisnis belum disepakati muncul saat perancangan kontrak | `system-analysis` Fase 2 menutup dengan pilar bisnis yang tak terjawab kode maupun user | `PRD_BRIEF` → `BRD_PRD_BRIEF` | tetap |
| 4 | Kontrak eksternal ternyata pecah: field wajib berubah, atau transisi status terekspos berubah | `system-analysis` Failure path butir 5 | tetap | `MAJOR` → `BREAKING` |

Pemicu 4 menaikkan `risk` tanpa menggeser `chain`: PRD yang sedang disusun sudah menjadi tempat yang benar untuk mengunci perubahan itu, dan sumbu bisnis tidak ikut aktif hanya karena kontraknya pecah. Ia berlaku **maksimal sekali per taskdir**: `BREAKING` adalah puncak enum `risk` dan tidak dapat dinaikkan lagi, sehingga pemicu 4 kedua atas taskdir yang sama adalah `## Failure path` butir 5 — bukan kenaikan diam-diam dan bukan pula loop tanpa plafon.

Prosedur transisi:

1. Verifikasi pasangan `(risk, chain)` hasil transisi terhadap tabel bagian 1.4. Pasangan tidak sah → hentikan lewat `## Failure path` butir 5; dilarang menerbitkan hop di atas pasangan ilegal.
2. Tulis ulang frontmatter `TASK.md`: `chain:` bernilai hasil transisi, `risk:` bernilai hasil kolom terakhir, `lane:` bernilai lane terminal chain baru.
3. Sisipkan baris hop baru ke ledger `## Chain` **sebelum** hop yang belum tercentang, pertahankan centang hop yang sudah tuntas.
4. Tulis ulang klausa `— verifikasi:` tiap `SC-{n}` agar cocok dengan kolom alat ukur lane baru pada tabel Fase 3 `task/SKILL.md`, **tanpa mengubah prosa hasil yang diukur**. Lalu jalankan ulang `skills/_common/validate_doc.py --kind task --taskdir <taskdir>` (tanpa `--fresh`) atas berkas hasilnya; check T8a ikut karena transisi inilah satu-satunya mutasi yang menulis ulang ledger, `lane:`, dan pasangan `(risk, chain)` sekaligus; T8b dilewati karena ledger pasca-transisi memang sudah membawa centang hop yang tuntas.
5. Commit pembaruan dengan staging path eksplisit `{taskdir}/TASK.md` dan subjek `docs(<slug>): eskalasi chain <asal> ke <hasil>`.
6. Berangkatkan hop baru dari Fase 3.

Butir 4 ada karena lane ikut berubah saat chain naik, dan kolom alat ukur `SC-{n}` terikat pada lane. Yang ditulis ulang hanyalah alat ukurnya — hasil yang diukur tidak berubah karena jalannya bertambah panjang. Kriteria yang benar-benar gugur adalah amandemen akar milik gerbang, bukan eskalasi.

**Plafon dua transisi `chain` per taskdir.** Kenaikan `risk` tanpa transisi chain (pemicu 4) tidak dihitung terhadap plafon, tetapi tetap dilaporkan di slot `Eskalasi`. Transisi chain ketiga → `## Failure path` butir 5. Hitungan dimateraikan `scripts/chain_counters.py` di `## Counters` `TASK.md`, bukan di ingatan sesi.

Chain dilarang turun. Hop yang ternyata berlebihan diselesaikan apa adanya; artefaknya tetap terbit dan tetap mengikat hilir.

## 4. Protokol Gerbang Dokumen (Fase 4)

Berlaku atas `BRD.md` dan `PRD.md`. Brief dikecualikan **dari approval**, bukan dari ledger: ia lahir `READY`, dikunci `plan` sendiri, dan hop-nya tetap dicentang `analyst` di Fase 6 langkah 0 menurut bagian 2.

**Kepemilikan approval.** `status: APPROVED` ditulis `backenddev:analyst`, dan hanya di sini. Penulis dokumen (`business-analysis`, `system-analysis`) dilarang menulisnya maupun meminta persetujuan user atas dokumennya; gerbang `backenddev:tech-lead` tidak pernah menulisnya dan tidak aktif pada approval dokumen. Ini **rumah kanonik** kepemilikan tersebut — template BRD, template PRD, skrip prasyarat hilir, dan `tech-lead/references/gate-scope.md` bagian 2 merujuk ke sini dan dilarang menyebut pemilik lain.

0. **Predikat masuk.** Fase 4 berangkat hanya bila laporan penutup hop menyatakan self-review reviewernya lolos **dan** melampirkan blok `## BRD Review` / `## PRD Review` reviewer apa adanya. Laporan tanpa blok itu, atau berverdict selain `Approved`, tidak pernah masuk gerbang ini: rutekan ke `## Failure path` butir 3 sebagai hop tertahan. Artefak yang belum ter-commit karena verdict-nya gagal **bukan** draft yatim, dan butir 1 tidak berlaku atasnya.

   **Jangkar verdict — apa yang benar-benar ditegakkannya.** Jangkar ini menegakkan **urutan**, bukan keaslian. Jalankan `git log --oneline -1 -- {taskdir}/<artefak>` dan pastikan commit draft berformat pesan penulisnya (`docs(spec): draft <BRD|PRD> <slug>`) benar-benar mendarat.

   Batasnya wajib dinyatakan apa adanya: penulis dokumen dan pemeriksa jangkar berjalan di runtime yang sama, sehingga commit draft yang dijadikan bukti dibuat oleh pihak yang sedang diperiksa. Yang tertangkap jangkar ini adalah hop yang **melompati** self-review — verdict `Approved` yang muncul tanpa commit draft di belakangnya adalah kontradiksi yang langsung terbaca. Yang **tidak** tertangkapnya adalah verdict yang dikarang lengkap dengan commit draftnya; itu tidak dapat digerbangi dalam satu runtime, dan berpura-pura sebaliknya lebih berbahaya daripada mengakuinya.

   Yang benar-benar menggerbangi keaslian adalah reviewer sebagai subagent terisolasi. Karena itu tambahkan predikat kedua yang dapat diperiksa di sini: **blok review wajib menyebut jejak konkret** — minimal satu ID temuan, nama seksi, atau `file:baris` — atau baris statusnya berbunyi persis `**Status:** Approved — nol temuan` (format output `agents/brd-reviewer.md`/`agents/prd-reviewer.md`). Blok berisi prosa pujian tanpa satu pun jejak ditolak sebagai balikan rusak lewat `## Failure path` butir 3, bukan diterima sebagai `Approved`. Penulis dilarang meng-commit draft-nya sebelum verdict `Approved`, sehingga blok `Approved` tanpa commit draft adalah kontradiksi yang langsung terbaca — rutekan ke `## Failure path` butir 3, jangan menambalnya dengan commit draft yatim butir 1. Draft yatim yang sah adalah artefak berverdict `Approved` yang commit-nya gagal dan **dilaporkan gagal**, bukan yang senyap.
1. **Kunci draft yatim.** Berlaku hanya sesudah butir 0 lolos. `git status --porcelain` atas artefak hop; belum terkunci → commit seketika memakai format pesan penulisnya (`docs(spec): draft BRD <slug>` atau `docs(spec): draft PRD <slug>`), tanpa menunggu persetujuan siapa pun. Draft yang hilang bersama sesi lebih mahal daripada satu commit tambahan.
2. **Verifikasi anggaran `## Open questions`.** Maksimal tiga entri, tiap entri memuat `terdampak:` dan `sementara dipakai:`. Predikat memblokirnya dibaca dari rumah kanonik masing-masing — `business-analysis/templates/brd-template.md` untuk BRD, `system-analysis/templates/prd-template.md` untuk PRD — dan dilarang ditafsirkan ulang di sini. Ada yang memblokir → approval tidak diajukan, artefak tetap `DRAFT`, poin revisinya dikembalikan ke skill hop. **Plafon dua pengembalian per hop** (dimateraikan `chain_counters.py --bump oq_return:<HOP>` di `## Counters` `TASK.md`): pengembalian ketiga atas hop yang sama menghentikan rantai lewat `## Failure path` butir 7 beserta daftar pertanyaan yang belum terjawab. Loop ini dihitung terpisah dari penolakan user butir 6.
3. **Ringkasan eksekutif.** Sajikan isi keputusan artefak, bukan daftar seksinya: untuk BRD, masalah inti beserta biaya pembiaran, aktor dan batas kewenangannya, tiap `BR-{n}`, serta tiap `BM-{n}` `## Business metrics`; untuk PRD, endpoint beserta request/response, transisi status yang berubah, matriks permission, dan dampak arsitektur terberisiko. Dua hal berikut **wajib** dienumerasi terpisah dan diminta keputusannya, bukan disajikan sebagai catatan:
   - tiap entri `BR-DISANGGAH: BR-{n}` di `## Open questions` PRD beserta alasan penyanggahannya — aturan bisnis yang gugur di sini tidak akan diperiksa gerbang mana pun lagi;
   - tiap asumsi aktif (`sementara dipakai:`) yang membentuk kontrak atau dekomposisi hilir.
4. **Persetujuan eksplisit.** `AskUserQuestion` dengan opsi yang membawa konsekuensi rantai. Keheningan, jawaban ambigu, dan jawaban di luar opsi bukan persetujuan.
5. **Penguncian approval.** Tulis `status: APPROVED` di frontmatter, `git add {taskdir}/<artefak>` lalu commit dengan subjek `docs(spec): approve <BRD|PRD> <slug>`, **baru** centang hop di ledger beserta sha commit itu dan commit pembaruan `TASK.md`-nya. Commit approval dan commit draft adalah dua commit terpisah; dilarang mengubah commit draft yang sudah mendarat.

   > **Kenapa pencentangan ledger tidak dapat menumpang di commit approval.** Baris centang memuat sha commit approval, dan sha itu belum ada saat berkasnya di-stage. Menyatukan keduanya menuntut baris centang ditulis sebelum sha-nya lahir, atau commit yang sudah mendarat diubah — keduanya terlarang. Satu commit tambahan per hop adalah harga dari ledger yang membawa jejak yang dapat ditelusuri, dan harga itu dibayar sadar.
6. **Penolakan.** Pertahankan `DRAFT`, teruskan poin penolakan user apa adanya ke skill hop, ulangi hop itu. Penolakan kedua pada hop yang sama menghentikan rantai (`## Failure path` butir 4).

## 5. Kanal Amandemen Akar (Fase 4a)

`## Success Criteria` dan `## Out of Scope` `TASK.md` adalah plafon ruang lingkup yang ditegakkan `business-analysis`, `system-analysis`, dan `plan`. Ketiganya karena itu rutin menemukan aturan atau kontrak yang **menyentuh** plafon itu, dan menghadapi dua pilihan: membuang butirnya, atau mengamandemen akar. Rumah kanonik rutenya ada di sini.

**Rutenya selalu ke `backenddev:analyst`, tidak pernah langsung ke gerbang.** Skill hop mengembalikan permintaan amandemen ke pemanggilnya beserta butir yang terdampak; `analyst` yang memegang ledger dan karena itu satu-satunya pihak yang tahu hop mana sedang tertahan. Hop yang menembus langsung ke `backenddev:tech-lead` menghilang dari pandangan pemegang ledger, dan gerbang tidak punya slot untuk menerimanya — Fase 5-nya hanya mengenal `READY_FOR_IMPLEMENTATION`, `NOT_READY_FOR_IMPLEMENTATION`, dan rantai tertahan. Rute buntu itulah yang membuat opsi "buang butirnya" menang secara diam-diam, dan aturan bisnis hilang lewat pintu yang tampak resmi.

Prosedur `analyst` saat laporan hop membawa permintaan amandemen:

1. **Tahan hop apa adanya.** Ledger tidak dicentang, artefak tetap `DRAFT`, dan hop berikutnya tidak berangkat.
2. **Sajikan butirnya ke user** lewat `AskUserQuestion`: butir `## Success Criteria` atau `## Out of Scope` yang tersentuh, aturan atau kontrak yang menyentuhnya, dan dua konsekuensi eksplisit — akar diamandemen (ruang lingkup bertambah, hop berjalan diulang di atas akar baru) atau butir hilir dibuang (aturan atau kontrak itu tidak turun ke implementasi, dan itu keputusan user, bukan kelalaian).
3. **User memilih membuang** → teruskan keputusannya apa adanya ke skill hop, ulangi Fase 3 pada hop yang sama, dan catat butir yang gugur di slot `Keputusan Lingkup` laporan penutup. Selesai di sini; gerbang tidak dilibatkan.
4. **User memilih amandemen** → hentikan rantai dan serahkan ke gerbang beserta rumusan amandemennya. Penulisan ulang `## Success Criteria` / `## Out of Scope` `TASK.md` adalah wewenang gerbang (`task/SKILL.md` guardrail **TASK.md EKSISTING TAK TERSENTUH**), dan `analyst` dilarang menuliskannya sendiri — mutasi `TASK.md` miliknya terbatas pada pencentangan ledger dan transisi eskalasi bagian 3.
5. **Plafon dua amandemen per taskdir**, dimateraikan `chain_counters.py --bump root_amendment` di `## Counters` `TASK.md`. Permintaan ketiga → `## Failure path` butir 8: rantai berhenti dan gerbang mengklasifikasi ulang permintaan dari awal. Akar yang diamandemen tiga kali bukan akar yang perlu ditambal, melainkan akar yang salah dirumuskan.

Amandemen akar berbeda dari eskalasi chain bagian 3 dan dihitung terpisah: eskalasi mengubah **panjang rantai** tanpa menyentuh ruang lingkup, amandemen mengubah **ruang lingkup** tanpa menyentuh panjang rantai. Satu taskdir dapat mengalami keduanya.
