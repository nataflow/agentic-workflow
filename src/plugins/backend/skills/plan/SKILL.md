---
name: plan
description: Dipanggil backend:analyst (entry_mode PRD sesudah PRD APPROVED, atau LANGSUNG pada chain BRIEF) dan gerbang backend:tech-lead (entry_mode RCA dari RCA.md terkonfirmasi) - perencana brief READY sebelum kode disentuh
user-invocable: false
---

## THE IRON LAW

- Tulis setiap hal yang dibutuhkan eksekutor ke dalam brief; apa pun yang tidak tertulis tidak akan diketahuinya.
- Terbitkan seluruh brief berstatus `READY` dan jangan mengubah file kode di `src/`.
- Penuhi titik hijau mandiri dan sapuan scan 12 dimensi di tiap unit kerja.
- Alirkan ketergantungan antar-brief satu arah tanpa siklus.
- Berhenti di brief terakhir yang menutup kontrak; unit yang tak meng-`Covers` maupun `Fulfills` apa pun tidak ditulis.
- Luluskan self-review lewat subagent `brief-reviewer`, lalu kunci seluruh brief dalam satu commit agregat sebelum handoff ke pemanggilnya — `backend:analyst` pada lane planning, `backend:tech-lead` pada jalur `RCA`.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/check_preconditions.py --taskdir <taskdir> --entry-mode <entry_mode> [--chain <chain>] [--risk <risk>] [--file-scope <file_scope>]`. `PASS` (8/8) → lanjut ke Workflow. `FAIL` → hentikan eksekusi dan remediasi butir yang gagal: taskdir belum sah atau kosong → minta alokasi dari `backend:tech-lead`; `.claude/profile/backenddev/index.json` belum ada → `backend:profile`; dokumen hulu belum siap → kembalikan ke penerbitnya; `chain`, `risk`, atau `entry_mode` tak selaras → kembalikan ke `backend:analyst`; jalur `RCA` tanpa `risk` sah atau tanpa `file_scope` → kembalikan ke `backend:tech-lead`.
2. Serap profil repositori mengikuti `references/entry-rules.md` bagian 0 — adapter stack `../profile/stacks/<stack>.md` beserta seksi `## Layer taxonomy`-nya, berkas profil yang wajib dibaca, dan batas struktur modul untuk slicing ada di sana. Berkas adapter tidak ada → hentikan eksekusi, rutekan ke `backend:profile`.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — Path direktori kerja aktif yang memuat artefak perancangan.
- `entry_mode` — enum — `[REQUIRED]` — Cabang Fase 1: `PRD` | `RCA` | `LANGSUNG`. Tidak ada nilai bawaan dan tidak ada resolusi dari artefak taskdir; pemanggil meneruskannya eksplisit (`backend:analyst` menurunkannya dari `chain`, gerbang menyebut `RCA` di `First Action`). Kosong atau di luar ketiga enum → skrip prasyarat `FAIL` di check 3.
  > Rasional: `references/rationale.md` R1.
- `chain` — enum — `[REQUIRED]` pada lane planning — `BRD_PRD_BRIEF` | `PRD_BRIEF` | `BRIEF` yang dimateraikan `TASK.md`; dipakai apa adanya untuk menghidrasi slot `Chain` `dispatcher/reviewer.md`. Tanpa nilai itu `brief-reviewer` tidak dapat membedakan dokumen hulu yang sah tidak ada dari rantai putus. Kosong → baca frontmatter `chain:` `TASK.md`. Jalur `RCA` mengisinya `—`.
- `risk` — enum — `[REQUIRED]` — `risk:` frontmatter `TASK.md`; plafon Check K. `TASK.md` absen → nilai risk level rute gerbang, diteruskan pemanggil.
- `file_scope` — string — `[REQUIRED]` — slot `File Scope` laporan rute gerbang, diteruskan pemanggil apa adanya; pembanding Check E. Kosong → skrip prasyarat `FAIL` di check 8, bukan diloloskan dengan catatan.
  > Rasional: `references/rationale.md` R2.
- `finding_source` — string — default `""` — Path berkas temuan asal (`backenddev/issues/<file>.md` atau `{taskdir}/REVIEW.md`) saat `## Success Criteria` akar berdiri di atas temuan terpilih; diteruskan `backend:analyst` apa adanya. Terisi → menyalakan re-verification temuan dan pembuangan `PLAUSIBLE` tak terjawab di Fase 2 (`references/entry-rules.md` bagian 1B). Kosong pada permintaan kerja biasa; dilarang disimpulkan dari isi taskdir.
- `preserve_history` — boolean — default `true` — Lanjutkan penomoran `NN` eksisting saat menambahkan brief ke taskdir.

## Workflow

### Fase 1 — Identifikasi Jalur Masuk & Validasi Dokumen Hulu

Tetapkan jalur masuk memakai matriks `entry_mode` di `references/entry-rules.md` bagian 1, memakai nilai yang diteruskan pemanggil apa adanya. Dilarang menurunkan jalur masuk sendiri dari artefak yang ada di taskdir; nilai yang kosong atau tak dikenal sudah dihentikan skrip prasyarat sebelum fase ini. Tolak dan kembalikan ke penerbit artefaknya begitu kondisi berhentinya terpenuhi; 5 pemicu eskalasi jalur `LANGSUNG` ada di bagian 1A, kewajiban batch ber-`finding_source` di 1B, kontrak panen `RCA.md` di 1C, dan kontrak panen `PRD.md` di 1D. Dilarang menulis ulang aturannya di sini.

Kunci daftar item masukan hasil fase ini menjadi rangkaian unit kerja yang dipetakan ke brief atomik.

### Fase 2 — Pemetaan Kode Aktual 12 Dimensi

Jalankan seluruh 12 dimensi checklist di `references/slicing-and-scan.md` bagian 2 tiap unit kerja, di bawah kuota sapuan main loop yang ditetapkan di sana. Dilarang melewati satu dimensi pun atau menulis ulang daftarnya di sini.

1. **Stop Condition**: berhenti hanya sesudah tiap berkas yang disentuh punya bukti `file:line`, simbol anchor, dan kelas test terdampak.
2. **Fan-Out Explorer Paralel**: unit yang melewati kuota atau belum terpetakan di profil diberangkatkan lewat template `dispatcher/explorer.md` mengikuti protokol bagian 2A — penandaan unit, batas 4 dispatch serentak, slot hidrasi, dan penanganan balikan gagal ada di sana.
3. **Siklus Dependensi**: petakan dependensi antar komponen, cegah siklus konstruksi memakai tanda di `## Failure signatures` adapter.
4. **Sapuan Dimensi Residual**: `entry_mode` selain `PRD` → jalankan tujuh dimensi bagian 2B sekali per batch; ketujuhnya selisih terhadap 16 dimensi `## Impact map` yang di jalur `PRD` sudah divonis hulu. Dimensi 3 atau 4 bervonis `terdampak` → berhenti dan terapkan 5 pemicu eskalasi bagian 1A (jalur `RCA`: muara bagian 1C).

### Fase 3 — Pemecahan Unit Atomik & Penulisan Brief

Kunci alokasi lebih dulu, tulis brief menyusul; urutan itu dilarang dibalik. Alokasi `AC-{n}` dan `SC-{n}` adalah keputusan slicing, dan menetapkannya sesudah seluruh brief ditulis membuat cakupan yang bolong hanya dapat ditambal dengan membongkar slicing. Sepuluh seksi wajib brief dienumerasi di blok template `templates/brief-template.md` **bagian 1**; kaidah `## Steps`, format `commit_message`, baris `Covers:` dan `Fulfills:`, nilai status item kerja, pendaratan `## Migration requirements`, derivasi `risk:`, dan integritas `## File scope` ditegakkan dari **bagian 2** berkas yang sama — itu rumah kanoniknya, dilarang ditulis ulang. Slicing 3-lapis dan DAG linear ada di `references/slicing-and-scan.md` bagian 3.

1. **Kunci Matriks Alokasi Batch**: susun spesifikasi batch — `nn`, `unit`, `title`, `risk`, `covers`, `fulfills`, `consumes`, `produces`, dan `explore` tiap brief — serta opsional `commit_type` (default `fix` pada lane `DEFECT_RCA` atau akar ber-`finding_source`, selain itu `feat`), `domain` (default segmen pertama `unit`), dan `ticket` (wajib bila `commit_template` profil memuat `{ticket}`) — ditambah field tingkat atas `finding_source` yang disalin dari parameter skill ini (kosong pada kerja biasa; `scaffold_brief.py` menuliskannya ke frontmatter tiap brief) — dan tulis ke `{taskdir}/.explore/brief-spec.json` lewat tool `Write`. Lalu jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/scaffold_brief.py --taskdir <taskdir> --write-matrix --spec <taskdir>/.explore/brief-spec.json [--risk <risk>]`. Spec di luar laci `.explore/` ditolak skrip: berkas liar di taskdir membuat prasyarat `architect` check 4 FAIL. `PASS` → matriks terkunci di laci `{taskdir}/.explore/brief-matrix.md`. `FAIL` → perbaiki alokasinya di titik ini juga; dilarang menulis satu baris brief pun di atas matriks yang belum lolos. Skrip menegakkan penomoran `NN` berkelanjutan sendiri, sehingga `preserve_history` tidak lagi dihitung tangan.

   **Taskdir yang sudah punya brief `DONE`/`BLOCKED`/`SUPERSEDED`** — re-entry `analyst` Fase 3 butir 0, berkas yatim `architect` Fase 3 butir 5, brief `BLOCKED` — memakai `--write-matrix --append --spec <taskdir>/.explore/brief-spec.json`. Baris lama dipertahankan apa adanya dan hanya unit baru yang ditambahkan di `NN` berikutnya. Brief `BLOCKED` beserta brief `READY` hilirnya ditutup lewat baris pengganti ber-`supersedes` (`"supersedes": ["02"]`); brief `DONE` yang ditahan `{taskdir}/HALT.md` diperbaiki lewat baris ber-`repairs` (`"repairs": "02"`), yang mencabut `HALT.md` saat kerangkanya ditulis. Skrip menolak batch yang meninggalkan brief `BLOCKED` tanpa pengganti, `HALT.md` tanpa baris `repairs`, atau brief `READY` hilir yang akan berjalan sebelum pengganti/perbaikannya. Skrip menolak penulisan matriks penuh di atas brief tereksekusi tanpa flag itu: alokasi `Covers:`/`Fulfills:` brief yang kodenya sudah mendarat di `src/` adalah riwayat, bukan rencana yang boleh ditulis ulang. Kerangkanya pun tidak dapat ditimpa — `--nn` menolak brief `DONE`/`BLOCKED`/`SUPERSEDED` sekalipun diberi `--force`.

   **Uji kecukupan alokasi.** Matriks lolos hanya bila tiap barisnya memikul minimal satu `covers` atau `fulfills` nyata; baris yang keduanya kosong sah hanya di taskdir tanpa `PRD.md` maupun `TASK.md`. Di luar itu ia unit tanpa akar — hapus barisnya di titik ini, dilarang dicarikan `AC-{n}` susulan sesudah briefnya terlanjur ditulis.
2. **Tulis Kerangka dari Matriks**: `scaffold_brief.py --taskdir <taskdir> --nn <NN>` menuliskan `{taskdir}/brief-<NN>-<unit>.md` berisi sepuluh seksi baku berurutan, frontmatter terisi, dan baris `Covers:`/`Fulfills:` yang **disalin dari matriks**. Isi tiap seksi lalu hapus penanda `<!-- scaffold: ... -->`-nya; penanda itu memuat predikat yang akan ditagih Fase 4 tepat di seksi yang mengikatnya. Dilarang mengarang struktur brief dari contoh `templates/brief-template.md` bagian 1 — contoh itu berisi domain nyata, dan menyalinnya membocorkan isi contoh ke brief.
3. **Panen Laporan Unit Sebelum Mengisi**: baca `{taskdir}/.explore/<slug>-<NN>.md` milik unit itu (kolom `Laporan .explore` matriks) tepat sebelum mengisi `## File scope` dan `## Steps`, salin kolom `Simbol anchor`-nya apa adanya, dan terapkan ulang vonis `### Penanganan Balikan` `dispatcher/explorer.md` saat memanennya — `confidence: low` bukan alas brief, `belum disisir` bukan `tidak ada test`. Unit tanpa laporan diisi dari sapuan mandiri Fase 2. Kuota penulisan `## Steps`: maksimal 2 potongan per berkas, plafon 120 baris per brief, hanya atas berkas yang terdaftar di `## File scope` brief itu (`references/slicing-and-scan.md` bagian 2).
   > Rasional: `references/rationale.md` R3.
4. **Gerbang Per-Brief**: jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/validate_briefs.py --taskdir <taskdir> --brief <NN>` tepat sesudah tiap brief selesai diisi, sebelum brief berikutnya dimulai. `FAIL` → perbaiki seketika. Cacat yang lolos di sini tereplikasi ke seluruh sisa batch, dan menambalnya di Fase 4 berbiaya N kali lipat.
5. Kutip baris `## Code conventions` apa adanya di dalam butir `## Steps` yang bersangkutan bila unit menyentuh aspek terkait, supaya implementor terikat pada langkah — bukan acuan umum yang boleh dilewati. Dilarang menambah seksi baru ke brief demi menampungnya.
6. Batalkan langkah yang menuntut pola terdaftar di `## Anti-patterns`, lalu rancang ulang memakai pola pengganti yang tertulis di baris yang sama. Check P menegakkan butir ini secara mekanis atas tiap baris profil ber-resep `deteksi`; baris bersumber konfirmasi user tidak punya resep dan tetap dinilai penilaian sendiri.
7. Tulis penegasan eksplisit ("tidak perlu", "tidak ada") pada seksi tanpa isi, bukan dikosongkan.

### Fase 4 — Protokol Uji Mandiri Rantai Brief

Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/validate_briefs.py --taskdir <taskdir> [--risk <risk>] [--file-scope <file_scope>]` atas seluruh brief batch aktif. Skrip memvonis seluruh predikat mekanis sekaligus — struktur dan frontmatter, sapuan placeholder dan verifikasi, langit-langit slicing, resolusi anchor beserta pemakaiannya di `## Steps`, sapuan anti-pattern profil, realitas berkas test, enum `risk:` beserta plafon akarnya, batas cakupan, DAG lintas-brief, cakupan dua sumbu `Covers:`/`Fulfills:`, pendaratan AC bertanda `test otomatis` dan `QA manual:`, serta pendaratan migrasi beserta rollback plan-nya. Predikat lengkap tiap check beserta remediasinya ada di `references/check-catalog.md` — buka hanya untuk ID check yang gagal; dilarang menulis ulang daftarnya di sini.

Teruskan `--file-scope` apa adanya dari parameter skill. Tanpa itu Check E turun ke pembanding yang lebih lemah dan divonis `WARN` — bukan `PASS` — beserta banner `TERDEGRADASI` di puncak keluaran. Banner itu dilaporkan apa adanya di laporan penutup, dilarang disaring.

1. `FAIL` → perbaiki **seluruh** pelanggaran yang dilaporkan satu keluaran itu lebih dulu, lalu jalankan skrip sekali lagi sebagai konfirmasi. Dilarang memperbaiki satu pelanggaran lalu menjalankan ulang skrip berkali-kali, dan dilarang menilai ulang predikat yang sudah divonis skrip lewat pembacaan mandiri. Baris berstatus `LOCKED` bukan pelanggaran: ia menyebut brief `DONE`/`BLOCKED` yang predikat rencananya memang tidak berlaku lagi (`references/check-catalog.md`, "Batch aktif vs brief terkunci"). Dilarang "memperbaikinya" dengan menulis ulang brief yang sudah dieksekusi.
2. **Check A — Source Coverage** tetap dinilai main loop: ia semantik, bukan token. Sandingkan tiap butir PRD, tiap temuan yang dipikul `SC-{n}` saat `finding_source` terisi, atau permintaan `LANGSUNG` terhadap brief yang mengerjakannya; seluruhnya wajib terpetakan ke `## Steps` atau `## Analysis trace`.
2b. **Arah balik Check A — kecukupan unit**, sama-sama dinilai main loop. Brief yang tak satu pun butir PRD, temuan berakar, atau permintaan `LANGSUNG` tuntut adalah unit tanpa akar dan dihapus dari batch, bukan diloloskan karena strukturnya sah dan skripnya hijau. Check A memvonis butir hulu yang tak punya brief; butir ini memvonis brief yang tak punya butir hulu.
3. `PASS`, Check A tertutup, dan butir 2b nol temuan → lanjut ke Fase 5; dispatch self-review dilarang berangkat sebelum titik ini.

### Fase 5 — Laporan Penutupan & Serah Terima Determinik

Jalankan self-review kolektif lebih dulu, commit menyusul, dan tutup dengan laporan:

1. **Self-Review Kolektif Dokumen**: baca state ronde lewat `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/validate_briefs.py --taskdir <taskdir> --review-state`, buka ronde dengan `--open-round` tepat sebelum dispatch berangkat, lalu panggil subagent `brief-reviewer` lewat template `dispatcher/reviewer.md` mengikuti protokol dispatch di `references/review-and-commit.md` bagian 5 — hidrasi slot `taskdir`, `chain`, `ronde`, dan `target`; materaikan tiap ronde yang selesai dengan `--record-round`; plafon **2 ronde per generasi batch dan 4 per taskdir**; ronde 2 menyempit ke brief yang berubah; dan penanganan dispatch gagal ada di sana. Hanya temuan `BLOCKER` yang menahan commit — `ADVISORY` ikut ke laporan tanpa memicu ronde baru.
2. **Commit Agregat**: eksekusi commit satu batch mengikuti `references/review-and-commit.md` bagian 6 — urutan wajib, staging path eksplisit, format `docs(plan): add <N> briefs for <slug>`, batas kewenangan git, dan mitigasi tiap mode kegagalan ada di sana. Status self-review bukan `Approved` → lewati commit dan laporkan brief `READY` belum terkunci di git.
3. Tampilkan tabel ringkasan per brief, lalu tegaskan: *"Tidak ada kode di `src/` yang dimodifikasi."*

## Guardrails

- **READ-ONLY MUTLAK TERHADAP SRC/**: dilarang membuat, mengedit, atau menghapus file di `src/` selama perencanaan.
- **STATUS BRIEF MILIK PENULISNYA**: brief terbit `status: READY`; `DONE` dan `BLOCKED` hanya dimutasi `code-implementor`. Satu-satunya mutasi status milik skill ini adalah `BLOCKED|READY → SUPERSEDED` yang ditulis `scaffold_brief.py --nn` atas brief yang disebut `supersedes` baris pengganti. Dilarang menyuntingnya tangan dan dilarang menyentuh brief `DONE`.
- **NOL PERTANYAAN TERBUKA DI BRIEF**: brief dilarang memuat `## Open questions`; ketidakpastian tuntas sebelum brief ditulis, bukan diwariskan ke eksekutor.
- **NOL PERINTAH BUILD/TEST DI BRIEF**: brief dilarang memuat seksi `## Verification` maupun perintah build/test; verifikasi milik penutup taskdir.
- **BATAS FILE SCOPE EKSPLISIT**: tiap file yang disentuh wajib tercantum di `## File scope`, kelas test terdampak termasuk.
- **DAG LINEAR SATU ARAH**: dilarang dependensi melingkar atau `Consumes` yang menunjuk `NN` lebih besar.
- **SUBAGENT DISPATCH**: panggil `brief-reviewer` langsung via template `dispatcher/reviewer.md` di Fase 5, dan `code-explorer` langsung via template `dispatcher/explorer.md` di Fase 2. Dilarang menyusun prompt dispatch di luar template resminya atau melanggar plafon ronde di `references/review-and-commit.md` bagian 5.
- **VERDICT DITERUSKAN UTUH**: blok `## Brief Review` dari `brief-reviewer` diteruskan apa adanya ke laporan penutup, tanpa parafrase maupun penyaringan.
- **COMMIT TERBATAS PADA BRIEF**: commit skill ini hanya memuat `brief-*.md` taskdir aktif — brief baru **dan** brief yang baru ditandai `SUPERSEDED` — ditambah `git rm -q {taskdir}/HALT.md` bila baris `repairs` mencabutnya dan berkas `finding_source` di bawah `backenddev/issues/` bila Fase 2 menandainya `OBSOLETE`/`DROPPED`, dengan staging path eksplisit, satu-satunya mutasi git milik `plan`. Dilarang `git add .`/`-A`, `push`, `merge`, `rebase`, `branch`, maupun `checkout`.
- **CUKUP ITU BERHENTI**: brief mengeksekusi kontrak yang sudah dikunci hulu, bukan kontrak yang seharusnya. Dilarang menambah langkah, berkas, abstraksi, interface, atau flag konfigurasi yang tak satu pun `AC-{n}`/`SC-{n}` tuntut ("nanti ada yang kedua" bukan akar); memecah satu permukaan jadi banyak brief demi terlihat atomik — itu kebalikan *God Brief* dengan ongkos gerbang yang sama; dan membawa perbaikan temuan Fase 2 ke dalam batch ini, karena rumahnya `backenddev/issues/`, bukan brief tambahan.
- **KEPUTUSAN DEFINITIF SAAT INI**: seluruh isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
- **RATIONALIZATION PREVENTION**: dilarang menggabungkan seluruh perubahan ke 1 brief raksasa (*God Brief*); meninggalkan placeholder berharap dilengkapi implementor; menugaskan test suite penuh pada brief awal; mengabaikan file migrasi saat ada mutasi model persistensi; memberi brief status `DRAFT`; memperluas perubahan ke modul tetangga di luar batch aktif; meneruskan sapuan sesudah kuota Fase 2 habis; atau menyatakan brief ter-commit saat `git commit` mengembalikan kode keluar bukan nol.

## Output [REQUIRED]

Brief mengikuti `templates/brief-template.md`. Self-review `Approved` dan batch ter-commit → tutup satu baris tanpa blok: `### BACKEND PLAN GENERATION REPORT — <n> BRIEF READY @ <sha> · <taskdir> · Entry <PRD | RCA | LANGSUNG> · Check 15/15 · ronde <n>/2 · ADVISORY <n>`. Selain itu, sajikan:

```markdown
### BACKEND PLAN GENERATION REPORT — BELUM TERKUNCI
- **Rantai**: <taskdir> · Entry <PRD | RCA | LANGSUNG> · <n> brief ditulis
- **Commit**: tidak dijalankan (<alasan>) — brief `READY` belum terkunci di git
- **Self-Review**: tidak tuntas (<alasan>) · BLOCKER <n> tersisa — <daftar>
- **Check** : <n>/15 PASS · TERDEGRADASI <daftar id | nihil> · LOCKED <n brief DONE/BLOCKED | nihil> · Coverage AC <n>/<n> · SC <n>/<n>
```

Lampirkan verdict `brief-reviewer` apa adanya tepat di bawahnya — predikat E menuntutnya utuh, dilarang diparafrase. Status commit dibaca gerbang di Fase 5-nya: batch yang belum terkunci menahan keberangkatan `architect`. Alokasi `Covers:`/`Fulfills:`, risk per unit, dan `## File scope` tiap brief hidup di berkas brief yang baru saja di-commit — dilarang menyalinnya jadi tabel di laporan.

**Serah-terima.** `Kembali ke backend:analyst` — Fase 6 skill itu satu-satunya titik yang memverifikasi ledger `## Chain` tercentang penuh. Dilarang mendispatch implementor sendiri; orkestrasi eksekusi milik `backend:architect` lewat gerbang. Hanya jalur `RCA` yang pulang ke `backend:tech-lead`.

## Failure path

1. **Dokumen Hulu Tak Layak**: `PRD.md` masih `DRAFT` → kembalikan ke `backend:analyst`, satu-satunya pemilik gerbang approval dokumen; mode `LANGSUNG` menyentuh pemicu eskalasi → batalkan rute MINOR dan kembalikan ke `backend:analyst` sebagai pemicu eskalasi chain nomor 1; jalur `RCA` menyentuh pemicu eskalasi → kembalikan ke `backend:tech-lead` (`references/entry-rules.md` bagian 1C). Dilarang memanggil `system-analysis` sendiri.
2. **Dependensi Melingkar atau Interface Bentrok**: ubah nomor urut brief dan samakan signature DTO `Produces` pendahulu dengan `Consumes` penerusnya agar alur kembali linear.
3. **File Test Hilang dari Scope**: tambahkan kelas test terdampak ke `## File scope` sebelum menutup Fase 4.
4. **Berkas Test AC Tidak Mendarat**: `AC-{n}` bertanda `test otomatis` tak punya satu pun berkas test di `## File scope` brief yang mengklaimnya di `Covers:` → tambahkan berkas testnya ke brief itu, dinamai menurut konvensi repo. Penamaan berkas test tidak pernah menuntut amandemen PRD: PRD menetapkan bahwa AC itu digerbangi test, bukan nama berkasnya.
5. **Migrasi PRD Tidak Mendarat**: urutan deploy atau rollback plan `## Migration requirements` PRD tak ditemukan di `## Migration`/`## Risk & rollback` brief mana pun → lengkapi brief pemilik migrasinya sebelum menutup Fase 4; dilarang menyerahkan urutan deploy ke gerbang sebagai catatan lisan.
6. **Risk Brief Melampaui Plafon Akar**: predikat derivasi menuntut nilai `risk:` lebih tinggi daripada `risk:` `TASK.md` → hentikan penulisan batch dan kembalikan ke `backend:analyst` menyebut pemicu eskalasi chain nomor 2 beserta nilai yang dituntut predikat (jalur `RCA`: ke `backend:tech-lead`, `references/entry-rules.md` bagian 1C). Dilarang melunakkan predikat agar muat di bawah plafon maupun menaikkan risk sendiri.
7. **Taskdir Tidak Terbaca**: minta re-inisialisasi direktori kerja ke `tech-lead`.
8. **Self-Review Gagal atau Plafon Ronde Habis**: dispatch gagal → ulangi maksimal satu kali tanpa memateraikannya sebagai ronde. `--open-round` menolak berangkat, atau temuan `BLOCKER` masih terbuka sesudah ronde kedua generasi ini → serahkan brief tanpa commit dan tandai self-review tidak tuntas beserta daftar `BLOCKER` yang tersisa. Dilarang mengarang verdict `Approved`, membuka ronde ketiga pada generasi batch yang sama, maupun mengulang siklus ronde dari awal dengan memanggil ulang skill ini — hitungan dimateraikan per generasi batch dan per taskdir, bukan per invokasi. Brief yang **ditambahkan** sesudah plafon generasi habis, atau hop `BRIEF` yang dibuka re-entry `analyst`, membuka generasi berikutnya beserta jatah ronde barunya; itu jalur yang sah, dan menambah brief semata demi membuka jatah bukan.
9. **Commit Gagal Dieksekusi**: pertahankan `status: READY`, sertakan galat mentah di laporan, serahkan penguncian ke gerbang. Mitigasi per mode kegagalan ada di `references/review-and-commit.md` bagian 6.

## STYLE

- Gunakan fase bernomor dan kalimat perintah imperatif aktif yang tegas tanpa konstruksi bersyarat WHEN/THEN.
- Seluruh isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
- Pertahankan istilah domain teknis asli stack tanpa transliterasi paksa.
