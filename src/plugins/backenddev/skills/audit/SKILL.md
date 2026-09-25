---
name: audit
description: Gunakan ketika kode backend perlu disapu terhadap 6 konvensi arsitektur - evaluasi bukti konkret file:line dan pencatatan issues, sebelum perbaikan kode dimulai tanpa laporan audit
---

## THE IRON LAW

- Kandidat bukan temuan: tiap kandidat wajib melewati gate dengan bukti `file:line` konkret.
- Dilarang menurunkan kandidat tanpa bukti menjadi P3 karena kandidat tanpa bukti wajib dibuang.
- Perlakukan `src/` sebagai read-only dan jangan menjalankan perintah build atau test.
- Setiap penyisiran wajib menghasilkan berkas laporan di `backenddev/issues/` meskipun nol temuan.
- Dilarang menjalankan direct git commit karena commit adalah wewenang mutlak gerbang `tech-lead`.

## Precondition [REQUIRED]

1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/audit/scripts/check_preconditions.py --target-scope <target_scope> [--dimensions <dimensions>]` (`dimensions` dipisah koma, mis. `security,data`).
2. Evaluasi output skrip secara deterministik:
   - `PASS` (6/6 checks): Lanjutkan ke evaluasi parameter dan alur audit kode.
   - `FAIL`: Hentikan eksekusi segera dan jalankan tindakan remediasi pada butir yang gagal (source root hilang/tidak terbaca → periksa izin direktori; profil/adapter hilang → arahkan ke `backenddev:profile`; direktori issues tidak dapat ditulis → periksa izin tulis `backenddev/issues/`; target scope menunjuk diff/PR → gunakan subagent `code-reviewer` lewat `backenddev:architect`; target scope kosong, di luar repo, atau tidak ada → minta path modul di dalam repo; dimensi asing → pakai `all` atau token dimensi yang sah; `source_root` profil di luar repo → perbaiki lewat `backenddev:profile`).

## Parameter [REQUIRED]

- `target_scope` — string — `[REQUIRED]` — Path modul, package, atau folder yang disapu. Cakupan diff bukan milik skill ini.
- `dimensions` — array — default `["all"]` — Membatasi dimensi yang disisir di Fase 2; nilai di luar 6 token dimensi ditolak.
- `max_findings` — integer — default `50` — Batas temuan per laporan di Fase 4; kelebihannya dipotong pada prioritas terberat dan sisanya dicatat di `## Summary`.

## Workflow

Penyisiran dan audit kualitas arsitektur dieksekusi sekuensial melalui 6 fase terstruktur:

### Fase 0 — Penentuan Cakupan & Enumerasi Berkas Target (Scoping)

1. Jalankan skrip `check_preconditions.py` dengan parameter `target_scope` dan `dimensions`. Hentikan eksekusi segera jika skrip menghasilkan `FAIL`.
2. Baca `.claude/profile/backenddev/index.json` dan `.claude/profile/backenddev/{module-structure,anti-patterns,invariants}.md`. Catat `stack`, `source_root`, batasan modul pada `module-structure.md`, aturan `invariants.md` (pelanggarannya `P1`, `references/findings-contract.md` bagian 1), dan tiap baris `anti-patterns.md` sebagai pola terlarang khas repo ini.
3. Baca `../profile/stacks/<stack>.md` dari field `stack` di `index.json`. Seksi `## Audit checklist` di sana adalah sumber tunggal butir pemeriksaan. Dilarang memakai butir stack lain atau mengarangnya sendiri. Hentikan audit jika berkas adapter tidak ditemukan, lalu rutekan ke `backenddev:profile`.
4. Jalankan `Glob` seluruh berkas sumber stack ini di bawah path direktori target, memakai ekstensi dan konvensi penamaan dari `## Layer taxonomy` adapter. Hentikan sweep jika `target_scope` menunjuk diff branch atau PR; arahkan penilaian diff ke subagent `code-reviewer` lewat `backenddev:architect` Fase 4.
5. Identifikasi berkas konfigurasi runtime yang relevan dengan modul target menurut `## Detection` adapter. Dilarang mempersempit daftar berkas secara spekulatif di luar cakupan yang ditentukan.
6. Baca indeks `backenddev/issues/README.md`. Cari baris yang kolom `Target`-nya beririsan prefix path dengan cakupan saat ini. Buka laporan terkait dan catat temuan berstatus `DEFERRED` atau `FIXED`. Dilarang melaporkan ganda temuan lama yang masih aktif. Laporkan temuan `FIXED` yang kambuh sebagai temuan baru sambil merujuk ID lamanya.

### Fase 1 — Penyusunan Peta Cakupan Sebelum Penyisiran (Scope Map)

Susun peta arsitektur cakupan mengikuti urutan layer di sub-bagian `## Layer taxonomy` adapter yang sesuai field `architecture:` profil, dari titik masuk sampai lapisan penyimpanan. Pola pencarian tiap butir diambil dari `## Navigation recipes` adapter:

1. **Entry Points**: Endpoint HTTP, consumer message broker, dan tugas terjadwal.
2. **Transaction Boundaries**: Batas pembuka dan penutup transaksi, beserta lapisan tempat batas itu dideklarasikan.
3. **Data Mutation Points**: Lokasi penulisan dan penghapusan data.
4. **Egress Side-Effects**: Panggilan keluar, publish event, dan I/O di luar proses.
5. Dilarang melompati Fase 1; penyisiran tanpa peta alur menghasilkan evaluasi yang dangkal.

### Fase 2 — Penyisiran Kode Berbasis 6 Dimensi & Invariant (Sweep)

Definisi dan cakupan tiap dimensi ada di `references/dimensions.md`; butir pemeriksaan konkretnya ada di `## Audit checklist` adapter, dikelompokkan dengan sub-heading dimensi yang sama. Baris `## Anti-patterns` profil disisir bersamaan sebagai butir tambahan dimensi `architecture`.

1. Sisir seluruh berkas target terhadap keenam dimensi: `security`, `transaction`, `data`, `persistence`, `concurrency`, `architecture`.
   - Baca hanya sub-heading yang diminta jika `dimensions` dipersempit oleh user, dan catat dimensi yang dilewati di laporan.
   - Perlakukan tiap butir adapter sebagai kandidat, bukan temuan; putuskan kelayakannya di Fase 3.
2. **Invariants Compliance**: Cocokkan seluruh kode terhadap `## Invariants` profil, konvensi penamaan tiap layer, dan batas pemanggilan antar-modul di `## Module structure`.
3. Laporkan cacat nyata yang tidak tercakup butir adapter mana pun dengan penanda `di luar checklist adapter`, dan sebutkan di penutup sebagai kandidat butir baru untuk adapter itu.
4. Gabungkan kandidat yang melanggar beberapa dimensi menjadi 1 temuan dengan prioritas terberat: `security` > `transaction` > `data` > `persistence` > `concurrency` > `architecture`.

### Fase 3 — Gerbang Verifikasi Temuan Konkret (Verification Gate)

Jalankan evaluasi ketat untuk setiap kandidat temuan sebelum dicatat ke laporan:

1. **CONFIRMED**: Memiliki bukti `file:line` konkret untuk input, alur eksekusi, dan dampaknya.
2. **PLAUSIBLE**: Ada `file:line` pemicunya, tapi dampaknya bergantung nilai runtime yang tidak terbaca dari kode; sebutkan fakta yang belum terbukti secara eksplisit di temuan.
3. **DIBUANG (DROPPED)**: Tidak terbukti secara konkret dari kode aktual repositori.
   - **THE IRON LAW**: Dilarang menurunkan kandidat tanpa bukti menjadi `P3`; buang kandidat tanpa bukti sepenuhnya dan catat di ringkasan pembuangan.
4. Tetapkan severity menurut `references/findings-contract.md` bagian 1 — satu-satunya definisi; dilarang memakai tangga lain. Temuan anti-pattern wajib mengutip **dua** bukti: `file:line` kode pelanggar dan baris profil yang dilanggar; plafonnya `P2`.

### Fase 4 — Penerbitan Artefak Laporan & Pembaruan Indeks

Tulis dokumen laporan hasil audit mengacu pada struktur template `templates/issues-template.md`:

1. Cari indeks file tertinggi hari ini menggunakan `Glob backenddev/issues/{yyyy-mm-dd}-*-issues.md`.
2. Tulis berkas laporan ke `backenddev/issues/{yyyy-mm-dd}-{NNN}-issues.md` (`NNN` urut 3-digit).
3. Tulis berkas laporan dengan status bersih jika tidak ditemukan temuan. Berkas laporan tetap wajib diterbitkan.
4. Tambahkan satu baris di `backenddev/issues/README.md` persis skema `references/findings-contract.md` bagian 4 (kolom `File` = path relatif root berkas laporan, `Target` = path konkret modul/package tanpa label).
5. Verifikasi bahwa format tabel indeks tetap rapi dan tidak merusak struktur markdown.

### Fase 5 — Laporan Penutupan & Serah Terima Gerbang

Sajikan laporan deterministik kepada main loop:

1. Konfirmasikan path berkas laporan: `backenddev/issues/{yyyy-mm-dd}-{NNN}-issues.md`.
2. Rangkum jumlah temuan per severity: P1 (Blocker), P2 (Should fix), P3 (Nice to have).
3. Sajikan daftar temuan ringkas memuat: ID Temuan, Severity, Lokasi (`file:line`), dan Judul.
4. Tegaskan bahwa berkas laporan belum di-commit dan menunggu commit dari gerbang `tech-lead`. Dilarang mengusulkan temuan mana yang dikerjakan lebih dulu: seleksinya milik user di gerbang, berplafon tujuh temuan per taskdir.
5. Serahkan kembali kendali eksekusi tanpa menjalankan perbaikan kode mandiri.

## Guardrails

- **READ-ONLY TERHADAP SRC/**: Dilarang keras membuat, mengedit, atau menghapus file kode di direktori `src/` selama proses audit berlangsung.
- **LARANGAN MUTASI SISTEM**: `Bash` hanya untuk inspeksi non-mutasi (`git log`, `git status`, `ls`). Dilarang menjalankan build, test, maupun `git commit`; seluruh verifikasi berbasis pembacaan kode statis.
- **DILARANG MENDISKRONKAN SEVERITY**: Dilarang menurunkan temuan tanpa bukti menjadi `P3`; buang temuan tanpa bukti seketika. Dilarang menaikkan pelanggaran `## Anti-patterns` melewati `P2`.
- **KEWAJIBAN MENULIS LAPORAN**: Berkas laporan di `backenddev/issues/` wajib dibuat di setiap sesi, termasuk saat hasil penyisiran menunjukkan nol temuan.
- **NOL PENANDAAN STATUS OLEH AUDITOR**: Auditor dilarang menandai baris `> Status: FIXED` pada temuan; penandaan status hanya boleh dilakukan oleh implementor atau arsitek.
- **KEPUTUSAN DEFINITIF SAAT INI**: Seluruh isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
- **RATIONALIZATION PREVENTION**:
  - Dilarang langsung memperbaiki bug kecil yang ditemukan saat audit.
  - Dilarang melewatkan penyusunan peta alur (Fase 1) dengan alasan direktori kecil.
  - Dilarang menebak nomor urut indeks `{NNN}` tanpa melakukan Glob di direktori issues.
  - Dilarang menulis nama target di README.md dengan label abstrak non-path.
  - Dilarang menghapus riwayat temuan lama dari berkas indeks.

## Output [REQUIRED]

Artefak mengikuti `templates/issues-template.md`. Nihil temuan → tutup satu baris tanpa blok: `### BACKEND AUDIT SUMMARY — <path-target> · <n> berkas disapu · 6 dimensi · nihil temuan`. Ada temuan → sajikan:

```markdown
### BACKEND AUDIT SUMMARY
- **Artefak**: backenddev/issues/<yyyy-mm-dd>-<NNN>-issues.md · <path-target> · <n> berkas dievaluasi
- **Temuan** : P1 <n> · P2 <n> · P3 <n> — seluruhnya OPEN
- **P1 & P2**: `P1-1` <judul singkat> · `<path/ke/Berkas>:45` — satu baris per temuan
```

Daftar `P1 & P2` dipakai user memilih temuan di gerbang (plafon tujuh per taskdir) — tulis utuh, dan dilarang mengusulkan mana yang dikerjakan lebih dulu. Bukti tiap temuan hidup di berkas issues; dilarang mengulangnya di laporan.

**Serah-terima.** `Laporan temuan belum di-commit — kembali ke backenddev:tech-lead`. Temuan terpilih berangkat lewat lane `PLANNING` seperti permintaan kerja lain; panjang rantainya diputuskan `backenddev:analyst` dari dua sumbu, bukan oleh severity temuan dan bukan pula oleh skill ini.

## Failure path

1. **Target Cakupan Tidak Ditemukan**: Hentikan proses, laporkan path tidak valid, dan minta verifikasi direktori target kepada user.
2. **Profil Repositori Hilang**: Tunda audit dan sarankan inisialisasi profil terlebih dahulu via skill `backenddev:profile`.
3. **Indeks Issues Rusak atau Berskema Lama**: Jangan menulis ulang header maupun menghapus baris lama; tambahkan tabel baru berheader `references/findings-contract.md` bagian 4 di bawahnya, lalu tulis baris baru ke tabel itu.
4. **Ketiadaan Berkas Sumber pada Target**: Laporkan bahwa direktori target tidak memuat berkas sumber stack ini dan hentikan sweep tanpa membuat laporan palsu.
5. **Konflik ID Temuan**: Lakukan re-numbering sebelum menerbitkan laporan akhir jika ID temuan bertabrakan dengan laporan lain.
6. **Kegagalan Akses File**: Laporkan kendala izin sistem ke main loop bila file target tidak memiliki izin baca.
7. **Timeout Penyisiran Parsial**: Simpan temuan sementara dan lanjutkan dari file terakhir yang dievaluasi jika penyisiran modul besar terputus.

## STYLE

- Gunakan fase bernomor dan kalimat perintah imperatif aktif yang tegas dan to the point tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku untuk narasi penjelasan dan pertahankan istilah teknis asli stack.
- Sajikan seluruh bukti kode dengan format presisi `file:line` yang dapat diverifikasi.
- Prioritaskan rasio sinyal terhadap token yang tinggi dan hilangkan klaim spekulatif tanpa bukti.
- Pertahankan format penamaan laporan baku: `{yyyy-mm-dd}-{NNN}-issues.md`.
- Hindari frasa ambigu seperti 'mungkin' atau 'sepertinya' pada temuan `CONFIRMED`.
