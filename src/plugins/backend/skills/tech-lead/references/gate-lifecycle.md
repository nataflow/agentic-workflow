# Taskdir Provisioning, Branch Isolation & Batas Dokumen — `tech-lead`

Panduan pendamping gerbang: prosedur penamaan direktori kerja, resolusi branch dari base branch, baseline build sebelum delegasi, serta batas wewenang gerbang atas dokumen spesifikasi pada plugin `backend`.

______________________________________________________________________

## 1. Penamaan & Pemakaian Ulang Taskdir

Format wajib `backenddev/docs/<YYMMDDhhmm>-<slug>/` — timestamp dari `date +%y%m%d%H%M`, slug dari `feature_slug` (kebab-case, 2–4 kata, pola `<domain>-<jenis-kerja>`). Evaluasi direktori eksisting selalu lewat `ls backenddev/docs/` sebelum satu direktori baru dibuat; state machine pemulihan sesi selengkapnya di `decisions.md` bagian 4.

| Kondisi terdeteksi | Tindakan |
| --- | --- |
| Parameter `taskdir` diisi dan direktorinya ada di disk | Pakai ulang. Dilarang membuat timestamp baru untuk pekerjaan yang sama |
| Taskdir memuat brief `BLOCKED` atau `HALT.md` | Lane `PLANNING` taskdir sama, `reentry_reason` = brief-NN + sebab `report-NN.md`/`HALT.md`; `plan` menerbitkan pengganti ber-`supersedes` atau perbaikan ber-`repairs`. `HALT.md` `verdict: SCOPE` ditanyakan ke user lebih dulu (`SKILL.md` Fase 5). Jangan menutupinya dengan taskdir baru |
| Taskdir memuat brief `READY` | Rutekan ke `backend:architect` |
| Taskdir memuat `BRD.md`/`PRD.md` berstatus `DRAFT` | Rutekan ke `backend:analyst`; gerbang dokumennya milik skill itu (bagian 4) |
| Seluruh brief `DONE`/`SUPERSEDED` **dan** `REPORT.md` terbit, atau permintaannya memang baru | Buat taskdir bertimestamp baru. `REVIEW.md` ber-`P1` bukan rantai selesai: perbaikannya berjalan di taskdir yang sama |

- Tambah suffix `-v2` dan konfirmasikan ke user sebelum dipakai jika slug hasil turunan bentrok dengan taskdir lain yang masih aktif.
- Salin laporan `code-explorer` gerbang ke laci taskdir sesudah direktorinya siap: `mkdir -p <taskdir>/.explore && cp backenddev/docs/.explore/<slug>.md <taskdir>/.explore/gate-<slug>.md`, satu berkas per slug yang dispatch gerbang ini hasilkan. Salin, bukan pindah: lane tanpa taskdir tetap memerlukan laci gerbang sebagai satu-satunya rumah laporannya. Dilarang menyalin seluruh isi laci gerbang — laci itu menumpuk lintas task, dan laporan task lain yang ikut terbawa akan dipanen Tahap 0 skill hilir sebagai konteks yang salah. Prefiks `gate-` menjaga salinan itu dari ditimpa slug dispatch hilir; `slug:` di frontmatter tidak diubah, dan itulah yang dikutip skill hilir saat menyebut asal fakta warisan. Berkas salinan tetap berstatus laci kerja: tidak di-stage, tidak di-commit, tidak dihitung working tree kotor.
- Lewati seluruh bagian 1–3 jika lane bernilai `EXPLORE_FACT` atau `PROFILE`; keduanya tidak pernah mengalokasikan taskdir maupun branch.

### 1a. TASK.md — Amandemen & Backfill

`TASK.md` adalah akar rantai: `BRD.md`, `PRD.md`, dan tiap `brief-<NN>` adalah turunannya. Penulisan awalnya milik `backend:task`, dan frontmatter `chain:` beserta ledger `## Chain`-nya milik `backend:analyst`. Setiap taskdir yang berujung di `backend:architect` wajib berakar: lane `PLANNING` lewat `analyst` — taskdir perbaikan temuan `backenddev/issues/` dan `{taskdir}/REVIEW.md` berdiri di dalamnya, lane `DEFECT_RCA` lewat panggilan gerbang ke `task` saat provisioning (`SKILL.md` Fase 3 butir 1, lane `DEFECT_RCA`, `chain` kosong), lane `EXEC_BRIEF` lewat backfill di bawah. Taskdir yang dibuat sebelum aturan ini dan tidak berakar berada di luar cakupan: `report` menolaknya di prasyarat, dan penutupannya dilakukan manual. Dua operasi di bawah ini milik gerbang dan dilarang didelegasikan ke hilir.

**Amandemen.** Gerbang mengubah `TASK.md` hanya pada tiga pemicu di tabel ini, dan tiap perubahan dikunci satu commit tersendiri yang menyebut pemicunya — git adalah changelog dokumen ini, jadi dilarang menambahkan seksi `## Amendments`.

| Pemicu | Yang berubah |
| --- | --- |
| `analyst` melaporkan kriteria akar terbukti salah atau kurang | Butir `## Success Criteria` terkait; butir gugur dicoret **dengan ID tetap** (`- [ ] ~~**SC-2**: …~~`), bukan dihapus — butir tercoret tetap dihitung dalam penomoran |
| User menyisipkan permintaan susulan yang masih di dalam batas | Satu butir `## Success Criteria` baru, bernomor sesudah butir terakhir (termasuk yang tercoret) |
| `plan` jalur `RCA` kembali membawa pemicu eskalasi (`plan/references/entry-rules.md` bagian 1C) dan user memilih naik ke rantai ber-PRD | Frontmatter `lane: PRD_CONVERSION`, `chain: PRD_BRIEF`, `risk:` `MINOR` → `MAJOR` (`MAJOR`/`BREAKING` tetap); seksi `## Chain` baru berisi hop `PRD` dan `BRIEF` belum tercentang; klausa `— verifikasi:` tiap `SC-{n}` ditulis ulang ke kolom alat ukur `PRD_CONVERSION` tanpa mengubah prosa hasilnya |

Pembaruan `chain:`, ledger `## Chain`, dan `risk:` saat eskalasi chain **bukan** amandemen gerbang: ketiganya dieksekusi `analyst` di dalam fase planning menurut `analyst/references/chain-rules.md` bagian 3. Satu-satunya pengecualian adalah pemicu ketiga: taskdir `DEFECT_RCA` belum memikul `chain` yang dapat dinaikkan `analyst`, sehingga gerbang menuliskannya sekali, lalu `analyst` masuk lewat jalur resume Fase 0-nya pada hop `PRD`.

Setiap amandemen: jalankan ulang `skills/_common/validate_doc.py --kind task --taskdir <taskdir>` tanpa `--fresh` (self-test akar `task/templates/task-template.md` bagian 2, termasuk T8a untuk pemicu ketiga), lalu commit dengan staging path eksplisit `{taskdir}/TASK.md` dan subjek `docs(<slug>): amandemen akar TASK (<pemicu>)` (`gate-scope.md` bagian 3).

- Buat taskdir baru jika susulan user melanggar butir `## Out of Scope`; dilarang melebarkan akar dengan menghapus batas yang pernah ditetapkan.
- Hentikan amandemen dan buat taskdir baru jika amandemen menyentuh lebih dari separuh butir `## Success Criteria`.

**Backfill.** Untuk taskdir yang belum memuat `TASK.md`:

- Panggil `backend:task` sebelum `backend:architect` berangkat jika lane `EXEC_BRIEF` masuk ke taskdir tanpa `TASK.md`, dengan `lane` bernilai `EXEC_BRIEF`, `chain` dikosongkan, `evidence` diambil dari tabel `## File scope` brief eksisting, dan `## Success Criteria` disusun dari gabungan Acceptance Criteria brief `READY`. Backfill, seperti penulisan akar `DEFECT_RCA` saat provisioning, dipanggil gerbang langsung tanpa melewati `analyst`.
- Lewati backfill jika seluruh brief di taskdir itu sudah `DONE`; akar untuk kerja yang sudah tuntas tidak menambah kemampuan verifikasi apa pun.
- Dilarang mengarang butir yang tidak terbukti di brief saat backfill. Tulis kriteria yang tidak dapat ditarik dari brief eksisting di `## Out of Scope` beralasan `tidak terekam di brief`.

______________________________________________________________________

## 2. Resolusi Branch dari Base Branch

Branch kerja **wajib bercabang dari `base_branch`**, bukan dari `HEAD` aktif. Mencabangkan branch kerja di atas branch kerja lain membuat diff `merge-base` milik `code-reviewer` memuat pekerjaan pihak lain.

1. Tetapkan `base_branch` dari parameter; ambil dari frontmatter profil jika kosong.
   - Hentikan eksekusi segera jika keduanya kosong atau bernilai `tidak terdeteksi`. Dilarang menebak branch acuan.
2. Pastikan `git status --porcelain` kosong di luar laci kerja `.explore/`.
   - Tampilkan daftar berkas uncommitted dan minta user stash atau commit lebih dulu jika working tree kotor. Dilarang merapikannya sendiri.
   - Berkas di bawah segmen `.explore/` adalah laporan `code-explorer`, bukan artefak rantai: abaikan, jangan ditampilkan sebagai berkas kotor, dan jangan minta user membereskannya.
3. Turunkan `<branch_name>` dari `branch_convention` profil, dengan `<slug>` diisi slug taskdir (misal `feat/order-split`).
4. Eksekusi checkout menurut kondisi:

| Kondisi | Perintah |
| --- | --- |
| `HEAD` detached atau bukan repositori git | **BERHENTI SEGERA** — dilarang membuat branch maupun taskdir |
| `<branch_name>` sudah ada | `git checkout <branch_name>` — sesi re-entry, taskdir lama dipakai ulang |
| Selain itu | `git checkout <base_branch>` (no-op bila sudah di sana), lalu `git checkout -b <branch_name>` |

______________________________________________________________________

## 3. Baseline Build Sebelum Delegasi

Berlaku untuk lane yang menyentuh `src/` — `PLANNING` dan `EXEC_BRIEF`. Tujuannya memverifikasi stabilitas branch acuan sebelum mutasi kode dilakukan.

1. Setelah branch kerja aktif, jalankan perintah `build` sesuai `## Commands` profil.
2. Catat `Baseline Build: hijau` di laporan gerbang dan lanjut ke framing delegasi jika baseline hijau.
3. Laporkan kegagalan apa adanya dan minta keputusan user sebelum delegasi jika baseline merah sebelum perubahan apa pun. Dilarang membebankan kegagalan pra-perubahan ke implementor.
4. Catat `Baseline Build: tidak dijalankan` beserta alasannya jika skrip build tidak ada atau tidak dapat dieksekusi, dependensi tak terunduh, atau toolchain hilang; jangan menggagalkan rute karenanya.

Baseline dinyatakan **merah** hanya jika kompilasi atau test gagal di atas `base_branch` bersih sebelum satu berkas pun diubah. Kegagalan lingkungan pada butir 4 **bukan** merah.

______________________________________________________________________

## 4. Gerbang Dokumen — Dipindahkan ke `analyst`

Penguncian draft yatim, verifikasi anggaran `## Open questions`, penyajian ringkasan eksekutif, persetujuan user, penulisan `status: APPROVED`, dan commit approval `BRD.md`/`PRD.md` seluruhnya milik `backend:analyst`. Rumah kanoniknya di `analyst/references/chain-rules.md` bagian 4, dan dilarang ditulis ulang di sini.

Gerbang menyentuh dokumen rancangan hanya pada satu titik: taskdir eksisting yang memuat `BRD.md`/`PRD.md` berstatus `DRAFT` dirutekan kembali ke lane `PLANNING`, dan `analyst` melanjutkan rantainya dari hop yang belum tercentang di ledger `## Chain`. Dilarang membaca ulang, menyunting, menyetujui, atau meng-commit dokumen itu di gerbang.

______________________________________________________________________

## 5. Aturan Tepi Gerbang Masuk

Dua kondisi yang dievaluasi di `SKILL.md` seksi `### Gerbang Masuk` butir 4:

1. **Permintaan Baru di Tengah Rantai Hilir**: Tahan permintaan baru yang disisipkan user saat skill hilir sedang berjalan sampai rantai aktif menutup, lalu masukkan sebagai pemicu gerbang tersendiri. Subagent yang sedang berjalan dilarang memproses permintaan di luar briefnya.
2. **Berkas Non-`src/` Berefek Runtime**: Berkas konfigurasi runtime per environment, skrip migrasi database, berkas manifest, serta konfigurasi pipeline build tetap memerlukan aktivasi gerbang — perlakukan sebagai perubahan kode dan klasifikasikan lewat Keputusan 2.
   - Klasifikasikan migrasi destruktif (`DROP`, `ALTER` penyempitan tipe, `NOT NULL` atas kolom terisi) dan perubahan setelan skema penyimpanan sebagai `BREAKING`.
   - Klasifikasikan bump versi dependensi dan penambahan properti opsional berdefault sebagai `MINOR`, kecuali menyentuh dependensi keamanan atau driver database.

## 6. Re-entry Fase 5 — Commit Artefak & Tabel Pengirim Balik

Dijalankan tiap kali skill hilir menutup dengan instruksi `kembali ke backend:tech-lead`. Butir 4–5 (`P1` dan `BLOCKED`) tinggal di `SKILL.md` Fase 5.

1. Jalankan skrip prasyarat dengan `--re-entry`; berkas kotor di zona artefak (`.claude/profile/backenddev/`, `backenddev/docs/`, `backenddev/issues/`, `docs/api/`, dan — hanya selama masa transisi MIGRATE — penghapusan berkas profil backend di lokasi lama `.claude/profile/<berkas>`) memang menunggu commit butir 2. Berkas di `.claude/profile/frontenddev/` atau sisa milik plugin lain di `.claude/profile/` bukan artefak gerbang ini dan tidak ikut di-stage. Identifikasi pengirim balik, baca laporan penutupnya, dan periksa status artefaknya.
2. Commit artefak yang masih menunggu: profil dari `backend:profile`, laporan dan indeks `backenddev/issues/` dari `audit`, serta `RCA.md` dari `debug`. Gunakan staging path eksplisit; dilarang `git add .` atau `-A` (`gate-scope.md` bagian 3). Stage **tiap path** yang disebut slot `Menunggu commit` laporan pengirim — pada `profile` itu termasuk `.gitignore`, yang memikul baris ignore laci `.explore/` dan `.backenddev/`. Berkas itu tertinggal di luar commit berarti ia tiba di `architect` sebagai working tree kotor, lalu berakhir jadi commit susulan tanpa brief pengklaim yang dihukum `code-reviewer` di penutup taskdir.
3. Tentukan langkah lanjut berdasarkan pengirim balik:
   - Pengirim `backend:profile`: Ulangi Fase 0 dan lanjutkan rute tertunda.
   - Pengirim `analyst` bervonis `READY_FOR_IMPLEMENTATION`: Rutekan ke `backend:architect`. Bervonis `NOT_READY_FOR_IMPLEMENTATION`: baca predikat yang gagal, selesaikan akar masalahnya lewat `SKILL.md` `## Failure path` butir 7, lalu berangkatkan ulang lane `PLANNING` pada taskdir yang sama **dengan `reentry_reason` terisi predikat yang gagal beserta ID-nya**; taskdir berledger tercentang penuh yang berangkat tanpa parameter itu tidak punya hop yang dapat dijalankan `analyst` dan berhenti seketika. Dilarang merutekan ke `architect` atas rantai bervonis itu, dan dilarang menyentuh artefak rancangannya sendiri. Menyerahkan rantai tertahan: perlakuan yang sama.
   - Pengirim `analyst` membawa **amandemen akar** yang sudah disetujui user di Fase 4a-nya (`analyst/references/chain-rules.md` bagian 5): tulis ulang butir `## Success Criteria` / `## Out of Scope` `TASK.md` sesuai rumusan yang diserahkan, jalankan ulang `skills/_common/validate_doc.py --kind task` tanpa `--fresh`, commit dengan staging path eksplisit dan subjek `docs(<slug>): amandemen akar TASK (analyst)`, lalu berangkatkan ulang lane `PLANNING` pada taskdir yang sama. Ini satu dari tiga pemicu amandemen gerbang (bagian 1a); dilarang menambah, menghapus, atau menafsirkan ulang butir di luar rumusan yang diserahkan `analyst`.
   - Pengirim `debug` menyerahkan `RCA.md` `ROOT_CAUSE_CONFIRMED`: Rutekan ke `plan` lewat Keputusan 2 (`decisions.md` bagian 7). Jika `INCONCLUSIVE`: kembalikan ke user dengan daftar bukti tambahan; dilarang merutekan ke `plan`.
   - Pengirim `plan` jalur `RCA` menyerahkan brief `READY` ter-commit: Rutekan ke `backend:architect` pada taskdir yang sama. Brief belum terkunci di git atau self-review tidak tuntas: selesaikan akar masalahnya lewat `SKILL.md` `## Failure path` butir 5 lebih dulu; dilarang memberangkatkan `architect` di atas batch yang belum ter-commit. Ini satu-satunya pengirim balik `plan` yang sampai ke gerbang — lane planning pulang ke `backend:analyst`.
   - Pengirim `plan` jalur `RCA` berhenti membawa **pemicu eskalasi** (`plan/references/entry-rules.md` bagian 1C — perbaikan menuntut DTO, endpoint, kolom baru, transisi status, atau permission): sajikan pemicunya beserta buktinya, lalu tanyakan via `AskUserQuestion` apakah perbaikan naik ke rantai ber-PRD. Naik → amandemen pemicu ketiga bagian 1a pada taskdir yang sama, lalu berangkatkan lane `PLANNING` dengan `evidence` menyertakan `{taskdir}/RCA.md` beserta `file:line` rantai kausalnya; `analyst` melanjutkan dari hop `PRD`. Ditolak → kembalikan ke user dengan pemicu yang menahan; dilarang merutekan ulang ke `plan` jalur `RCA` atas perbaikan yang sama. Taskdir baru tidak dibuat: `RCA.md` dan riwayatnya tetap di taskdir ini.
   - Pengirim `audit` menyerahkan laporan temuan: Sajikan ringkasan per severity, lalu tanyakan via `AskUserQuestion` temuan yang ditindaklanjuti — seleksi batch beserta filter statusnya mengikuti `gate-scope.md` bagian 6, berplafon 7 temuan per taskdir. Temuan terpilih diproses lewat Keputusan 2 (`decisions.md` bagian 7), lalu `SKILL.md` Fase 3 memprovisi taskdir baru dan rutekan ke lane `PLANNING` dengan `request` menyebut berkas laporan beserta ID tiap temuan terpilih, `evidence` berisi `file:line` tiap temuan itu, dan `finding_source` berisi path berkas laporannya. Dilarang menetapkan chain di sini.
   - Pengirim `architect` menutup `TERTAHAN (scope brief-NN)`: sajikan berkas atau simbol di luar scope beserta SHA-nya dari `{taskdir}/HALT.md`, tanyakan via `AskUserQuestion` apakah commit itu di-reset user atau diterima. Diterima → `git rm -q {taskdir}/HALT.md` lalu `git commit -m "docs(<slug>): cabut HALT brief-NN (scope diterima user)"`, kemudian berangkatkan ulang `backend:architect`. Di-reset → user me-reset (commit `HALT.md` ikut hilang bila reset melewatinya), lalu klasifikasikan ulang brief itu lewat lane `PLANNING`. Dilarang menjalankan reset dari gerbang.
   - Pengirim `architect` menutup dengan `HALT.md` ber-`verdict` `COMPILE` atau `STRAY` (`SYMBOL` diperlakukan seperti `SCOPE`: butir `TERTAHAN (scope brief-NN)` di atas): berangkatkan lane `PLANNING` pada taskdir yang sama dengan `reentry_reason` menyebut `{taskdir}/HALT.md`; `plan` menambah baris `repairs` yang mencabut penanda itu.
   - Pengirim `architect` menutup `COMPLETED` atau `COMPLETED (WARNING)` (severity `CLEAN`, `P3`, atau `P2`): Nyatakan rantai selesai, sebut branch aktif dan taskdir final. Pada `WARNING`, sebut ID `P2` beserta tawaran taskdir perbaikan baru (tidak otomatis). Rutekan ke `backend:document-api` hanya jika user memintanya eksplisit.
   - Pengirim `architect` mengisi slot **`Umpan balik profil`**: tanyakan lewat `AskUserQuestion` apakah preseden itu ditandai permanen di profil. Ya → jalankan `backend:profile` dengan `reported_anti_patterns` berisi entri itu apa adanya, lalu commit profilnya lewat butir 2. Tidak → buang, jangan simpan sebagai catatan. Pertanyaan ini berdiri sendiri dan tidak menahan penutupan rantai. Preseden yang terbukti menyesatkan saat eksekusi tidak pernah tertangkap sapuan statis `profile`; tanpa kanal ini pengetahuannya mati bersama taskdir dan rantai berikutnya menyalin preseden yang sama.
   - Pengirim `document-api` menyerahkan `docs/api/` belum ter-commit: Commit lewat butir 2, lalu nyatakan rantai selesai.
