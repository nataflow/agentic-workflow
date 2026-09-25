# Taskdir Provisioning, Branch Isolation & Batas Dokumen — `tech-lead`

Panduan pendamping gerbang: prosedur penamaan direktori kerja, resolusi branch dari base branch, baseline build sebelum delegasi, serta batas wewenang gerbang atas dokumen spesifikasi pada plugin `backenddev`.

______________________________________________________________________

## 1. Penamaan & Pemakaian Ulang Taskdir

Format wajib `backenddev/docs/<YYMMDDhhmm>-<slug>/` — timestamp dari `date +%y%m%d%H%M`, slug dari `feature_slug` (kebab-case, 2–4 kata, pola `<domain>-<jenis-kerja>`). Evaluasi direktori eksisting selalu lewat `ls backenddev/docs/` sebelum satu direktori baru dibuat; state machine pemulihan sesi selengkapnya di `decisions.md` bagian 4.

| Kondisi terdeteksi | Tindakan |
| --- | --- |
| Parameter `taskdir` diisi dan direktorinya ada di disk | Pakai ulang. Dilarang membuat timestamp baru untuk pekerjaan yang sama |
| Taskdir memuat brief `BLOCKED` atau `HALT.md` | Lane `PLANNING` taskdir sama, `reentry_reason` = brief-NN + sebab `report-NN.md`/`HALT.md`; `plan` menerbitkan pengganti ber-`supersedes` atau perbaikan ber-`repairs`. `HALT.md` `verdict: SCOPE` ditanyakan ke user lebih dulu (`SKILL.md` Fase 5). Jangan menutupinya dengan taskdir baru |
| Taskdir memuat brief `READY` | Rutekan ke `backenddev:architect` |
| Taskdir memuat `BRD.md`/`PRD.md` berstatus `DRAFT` | Rutekan ke `backenddev:analyst`; gerbang dokumennya milik skill itu (bagian 4) |
| Seluruh brief `DONE`/`SUPERSEDED` **dan** `REPORT.md` terbit, atau permintaannya memang baru | Buat taskdir bertimestamp baru. `REVIEW.md` ber-`P1` bukan rantai selesai: perbaikannya berjalan di taskdir yang sama |

- Tambah suffix `-v2` dan konfirmasikan ke user sebelum dipakai jika slug hasil turunan bentrok dengan taskdir lain yang masih aktif.
- Salin laporan `code-explorer` gerbang ke laci taskdir sesudah direktorinya siap: `mkdir -p <taskdir>/.explore && cp backenddev/docs/.explore/<slug>.md <taskdir>/.explore/gate-<slug>.md`, satu berkas per slug yang dispatch gerbang ini hasilkan. Salin, bukan pindah: lane tanpa taskdir tetap memerlukan laci gerbang sebagai satu-satunya rumah laporannya. Dilarang menyalin seluruh isi laci gerbang — laci itu menumpuk lintas task, dan laporan task lain yang ikut terbawa akan dipanen Tahap 0 skill hilir sebagai konteks yang salah. Prefiks `gate-` menjaga salinan itu dari ditimpa slug dispatch hilir; `slug:` di frontmatter tidak diubah, dan itulah yang dikutip skill hilir saat menyebut asal fakta warisan. Berkas salinan tetap berstatus laci kerja: tidak di-stage, tidak di-commit, tidak dihitung working tree kotor.
- Lewati seluruh bagian 1–3 jika lane bernilai `EXPLORE_FACT` atau `PROFILE`; keduanya tidak pernah mengalokasikan taskdir maupun branch.

### 1a. TASK.md — Amandemen & Backfill

`TASK.md` adalah akar rantai: `BRD.md`, `PRD.md`, dan tiap `brief-<NN>` adalah turunannya. Penulisan awalnya milik `backenddev:task`, dan frontmatter `chain:` beserta ledger `## Chain`-nya milik `backenddev:analyst`. Setiap taskdir yang berujung di `backenddev:architect` wajib berakar: lane `PLANNING` lewat `analyst` — taskdir perbaikan temuan `backenddev/issues/` dan `{taskdir}/REVIEW.md` berdiri di dalamnya, lane `DEFECT_RCA` lewat panggilan gerbang ke `task` saat provisioning (`SKILL.md` Fase 3 butir 1, lane `DEFECT_RCA`, `chain` kosong), lane `EXEC_BRIEF` lewat backfill di bawah. Taskdir yang dibuat sebelum aturan ini dan tidak berakar berada di luar cakupan: `report` menolaknya di prasyarat, dan penutupannya dilakukan manual. Dua operasi di bawah ini milik gerbang dan dilarang didelegasikan ke hilir.

**Amandemen.** Gerbang mengubah `TASK.md` hanya pada dua pemicu, dan tiap perubahan dikunci satu commit tersendiri yang menyebut pemicunya — git adalah changelog dokumen ini, jadi dilarang menambahkan seksi `## Amendments`.

| Pemicu | Yang berubah |
| --- | --- |
| `analyst` melaporkan kriteria akar terbukti salah atau kurang | Butir `## Success Criteria` terkait; butir gugur dicoret `~~...~~`, bukan dihapus |
| User menyisipkan permintaan susulan yang masih di dalam batas | Satu butir `## Success Criteria` baru |

Pembaruan `chain:`, ledger `## Chain`, dan `risk:` saat eskalasi chain **bukan** amandemen gerbang: ketiganya dieksekusi `analyst` di dalam fase planning menurut `analyst/references/chain-rules.md` bagian 3.

- Buat taskdir baru jika susulan user melanggar butir `## Out of Scope`; dilarang melebarkan akar dengan menghapus batas yang pernah ditetapkan.
- Hentikan amandemen dan buat taskdir baru jika amandemen menyentuh lebih dari separuh butir `## Success Criteria`.

**Backfill.** Untuk taskdir yang belum memuat `TASK.md`:

- Panggil `backenddev:task` sebelum `backenddev:architect` berangkat jika lane `EXEC_BRIEF` masuk ke taskdir tanpa `TASK.md`, dengan `lane` bernilai `EXEC_BRIEF`, `chain` dikosongkan, `evidence` diambil dari tabel `## File scope` brief eksisting, dan `## Success Criteria` disusun dari gabungan Acceptance Criteria brief `READY`. Backfill, seperti penulisan akar `DEFECT_RCA` saat provisioning, dipanggil gerbang langsung tanpa melewati `analyst`.
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

Penguncian draft yatim, verifikasi anggaran `## Open questions`, penyajian ringkasan eksekutif, persetujuan user, penulisan `status: APPROVED`, dan commit approval `BRD.md`/`PRD.md` seluruhnya milik `backenddev:analyst`. Rumah kanoniknya di `analyst/references/chain-rules.md` bagian 4, dan dilarang ditulis ulang di sini.

Gerbang menyentuh dokumen rancangan hanya pada satu titik: taskdir eksisting yang memuat `BRD.md`/`PRD.md` berstatus `DRAFT` dirutekan kembali ke lane `PLANNING`, dan `analyst` melanjutkan rantainya dari hop yang belum tercentang di ledger `## Chain`. Dilarang membaca ulang, menyunting, menyetujui, atau meng-commit dokumen itu di gerbang.

______________________________________________________________________

## 5. Aturan Tepi Gerbang Masuk

Dua kondisi yang dievaluasi di `SKILL.md` seksi `### Gerbang Masuk` butir 4:

1. **Permintaan Baru di Tengah Rantai Hilir**: Tahan permintaan baru yang disisipkan user saat skill hilir sedang berjalan sampai rantai aktif menutup, lalu masukkan sebagai pemicu gerbang tersendiri. Subagent yang sedang berjalan dilarang memproses permintaan di luar briefnya.
2. **Berkas Non-`src/` Berefek Runtime**: Berkas konfigurasi runtime per environment, skrip migrasi database, berkas manifest, serta konfigurasi pipeline build tetap memerlukan aktivasi gerbang — perlakukan sebagai perubahan kode dan klasifikasikan lewat Keputusan 2.
   - Klasifikasikan migrasi destruktif (`DROP`, `ALTER` penyempitan tipe, `NOT NULL` atas kolom terisi) dan perubahan setelan skema penyimpanan sebagai `BREAKING`.
   - Klasifikasikan bump versi dependensi dan penambahan properti opsional berdefault sebagai `MINOR`, kecuali menyentuh dependensi keamanan atau driver database.
