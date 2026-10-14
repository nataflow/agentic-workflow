# Execution Protocol — `architect`

Rumah kanonik prosedur eksekusi rantai brief: ingest, dispatch implementor, matriks bukti disk, kontrak `report-<NN>.md`, gerbang kompilasi per-brief, verifikasi penutup, klasifikasi kegagalan, dan protokol rollback. `SKILL.md` merujuk bagian bernomor di sini dan dilarang menulis ulang isinya. Penulisan kode hidup di `agents/code-implementor.md`; penilaian penutup di `agents/code-reviewer.md`.

**Satu aturan yang membingkai seluruh dokumen**: tidak ada verifikasi terminal **di dalam subagent**. Lint, test, dan build berjalan tepat sekali di Phase 4, sesudah seluruh brief tertutup. Satu pengecualian sempit hidup di main loop: typecheck per unit (bagian 5), dijalankan `architect` sesudah commit unit, dan hanya bila baris `typecheck-per-brief` adapter bernilai `ya`.

---

## 1. Ingest — Prasyarat per Unit

Sebelum tiap dispatch, predikat unit divonis skrip, bukan dibaca ulang (`«nama.py»` = path absolut dari peta **Skrip:** `architect/SKILL.md`):

```bash
python3 «check_preconditions.py» --taskdir <taskdir> --brief <NN>
```

| # | Predikat |
|---|---|
| 1–9 | Predikat rantai: taskdir, akar & lane/sections, ledger `## Chain` tercentang penuh dan utuh, status brief (batch lolos `validate_briefs.py`; brief `DONE` wajib punya commit `implement unit NN` dan `report-NN.md`), profil lengkap, adapter, berkas plugin, working tree bersih, HEAD pada branch |
| 10 | Brief target `READY`, ber-`files_touched`, dan `stack`-nya = `stack` profil (satu profil melayani satu app pada satu waktu) |
| 11 | Tiap `depends_on` tertutup — `DONE` dengan commit `implement unit NN` di riwayat, atau `BLOCKED` yang remedinya `DONE` |
| 12 | `report-<NN>.md` belum ada — unit ini belum pernah didispatch |
| 13 | `based_on` tidak lebih tua daripada commit asing terakhir yang menyentuh `files_touched` — `WARN`, bukan `FAIL`; sha `based_on` yang tidak ada di repo juga `WARN` |

`FAIL` menahan dispatch; jalankan tindakan yang disebut, jangan menawar. `WARN` wajib disebut ke user sebelum dispatch berangkat.

**Pengecualian `.gitignore`**: `.gitignore` kotor yang satu-satunya perubahannya baris berjangkar `/.frontenddev/` atau `frontenddev/docs/**/.explore/` adalah jejak `frontend:profile` yang belum di-commit. Laporkan ke user dan rutekan ke `frontend:profile` mode REFRESH; dilarang men-stash, dilarang meng-commit atas nama rantai.

---

## 2. Dispatch & Strict Scope Law

`code-implementor` dipanggil langsung lewat tool `Agent` (`subagent_type`: `frontend:code-implementor`) dengan prompt hasil hidrasi `dispatcher/implementor.md` — tepat sekali per brief, sekuensial, tanpa polling.

Enam butir batas ditegakkan di tingkat prompt:

1. Hanya berkas `files_touched`; pada berkas `MODIFY` hanya simbol kolom `Anchor` tabel seksi 3 brief.
2. Satu-satunya berkas di luar `files_touched` yang boleh ditulis adalah `{taskdir}/report-<NN>.md`.
3. Bug di berkas atau simbol lain dicatat di `## Out of Scope / Mismatch` `report-<NN>.md`, tidak diperbaiki.
4. Nol `@ts-ignore`, `eslint-disable`, `svelte-ignore`, dan nol penambahan package tanpa instruksi brief.
5. Komentar dan fungsi eksisting di luar unit dipertahankan.
6. Nama fungsi dan ekspor persis brief.

---

## 3. Matriks Bukti Disk & Triase

`report-<NN>.md` adalah klaim subagent, bukan bukti. Jalankan `python3 «verify_scope.py» --brief <brief_path> --worktree` **sebelum** cabang mana pun dibuka — skrip menyandingkan `git status --porcelain -uall` (laci `.explore/` dibuang) dengan `files_touched` + brief + `report-<NN>.md`. `PASS` (exit 0) = baris "hanya `files_touched` berubah"; `FAIL` (exit 1) = baris "ada berkas berubah di luar `files_touched`", dengan daftar berkas liarnya; exit 2 = brief tak terbaca, perbaiki pemanggilannya. Vonis scope diambil dari exit skrip, bukan dari pembacaan manual:

| `report-<NN>.md` | Disk vs `files_touched` | Tindakan |
|---|---|---|
| `status: DONE` | hanya `files_touched` (+ `report-<NN>.md`) berubah | Pemeriksaan anchor (bawah), lalu **commit unit** |
| `status: DONE` | ada berkas berubah di luar `files_touched` | Pelanggaran scope: pulihkan berkas liar dan `files_touched`, tulis `## Triase` ke `report-<NN>.md`, turunkan brief ke `BLOCKED` — **tandai BLOCKED** |
| `status: DONE` | `## Changes` menyebut berkas yang tidak berubah | Laporan tidak jujur: perlakukan sebagai baris "kosong/rusak" di bawah |
| `status: DONE` | hunk `git diff -U0` berkas `MODIFY` menyebut simbol di luar `Anchor` | Pelanggaran scope tingkat simbol: perlakuan sama dengan berkas liar |
| `status: FAILED` | bersih | **Tandai BLOCKED** |
| `status: FAILED` | kotor di dalam `files_touched` | Rollback milik `architect` (implementor tidak punya terminal): `git restore -- <path>` berkas `MODIFY` dan `rm -- <path>` berkas `CREATE` yang disebut `## Rollback` laporan atau terbaca kotor, catat di `## Triase`, lalu **tandai BLOCKED** |
| absen / rusak | bersih | Kegagalan dispatch: hapus `report-<NN>.md` rusak itu bila ada (Check 12 menuntut ia absen), lalu ulangi maksimal sekali dengan slot yang sama; brief tetap `READY` |
| absen / rusak | kotor | **HENTIKAN.** Tampilkan berkas kotor ke user dan eskalasi; dilarang retry, rollback otomatis, dan commit |

Dokumen taskdir (brief, `report-<NN>.md`) diabaikan git, jadi tidak pernah tampak di `git status`; `verify_scope.py` tetap memvonis kontrak brief terhadap `sidik_kontrak`-nya. Brief `DONE` di disk tanpa commit unit (sesi terputus di antara penulisan status dan commit kode, `DONE` diketik tangan, atau commit unit di-reset user) divonis prasyarat sebagai fase `TERPUTUS` dengan `unit_berikutnya` = unit itu (25 R6) dan dijalankan lewat matriks yang sama **tanpa dispatch**: baris pertama berakhir di **commit unit** (statusnya sudah `DONE`); laporan absen/rusak dengan tree bersih → kembalikan status brief ke `READY` di disk lalu Phase 1 (dispatch ulang, laporan rusak dihapus dulu); baris lain → HENTIKAN dan eskalasi ke user. Asal kotoran pada fase ini tidak diketahui (Check 8 tidak menjaminnya bersih sebelum dispatch), jadi dilarang memulihkan berkas di luar `files_touched` — baris "berkas di luar `files_touched`" pada fase ini berarti HENTIKAN, bukan pemulihan.

Kotoran di **luar** `files_touched` pada baris mana pun bukan wewenang `architect` untuk dipulihkan bila ia sudah ada sebelum dispatch — Check 8 menjamin tree bersih sebelum berangkat, jadi yang muncul sesudahnya adalah kerja subagent.

**Pemeriksaan anchor.** Untuk tiap berkas `MODIFY`: `git diff -U0 -- <path>`; hunk header `@@ … @@ <konteks>` yang tidak menyebut anchor adalah pelanggaran. Funcname bawaan git untuk TypeScript/Svelte hanya menangkap deklarasi top-level tanpa indentasi — repo tanpa diff driver (`*.ts diff=typescript` di `.gitattributes`) menghasilkan hunk header kosong; pada kasus itu vonis turun ke `WARN`, isi hunk diperiksa manual, dan temuan dicatat sebagai rekomendasi profil.

**Commit unit** — kenaikan status di disk lalu commit kode, satu langkah:

```bash
# frontmatter brief: status: READY → DONE (disk; brief dan report-<NN>.md tidak di-stage)
git add <files_touched>
git commit -m "feat(<slug>): implement unit <NN> - <nama unit>"
```

**Tandai BLOCKED** — suntingan disk, tanpa commit:

```bash
# frontmatter brief: status: READY → BLOCKED; report-<NN>.md memuat ## Triase
```

Bukti `DONE` dibaca skrip dari dua hal: status `DONE` di disk dan commit `<type>(<slug>): implement unit <NN>` pembawa kode sejak `base_commit`. Brief `DONE` tanpa commit itu ditolak Check 4 dan membuat `depends_on` unit berikutnya tak pernah terpenuhi. Karena itu status `DONE` ditulis tepat sebelum commit kode, tidak pernah tanpa commit itu, dan subjek commit wajib persis bentuk di atas. `BLOCKED` cukup ditulis di disk: `taskdir_state.py` membaca titik berhentinya dari brief, dan Riwayat mencatatnya saat lead membuka ulang hop BRIEF.

---

## 4. Kontrak `report-<NN>.md`

Ditulis `code-implementor` sebagai **satu-satunya** balikan persisten unit — ringkasan di chat mati bersama sesi, berkas ini tidak. `architect` hanya menambahkan `## Triase`.

```markdown
---
artifact: UNIT_REPORT
unit: "<NN>"
brief: brief-<NN>-<unit>.md
status: DONE | FAILED
---

# Unit <NN> — <nama unit>

## Changes
- `<path>` — CREATE | MODIFY — simbol: `<simbol yang disentuh>` — <ringkasan>

## Verification
- `<perintah verification brief>` → DITUNDA (verifikasi penutup)

## Done Criteria
- <butir non-terminal> → Terpenuhi | Belum (<alasan>)
- <butir terminal> → DITUNDA (verifikasi penutup)

## Out of Scope / Mismatch
- `<file:baris>` — <bug existing | drift kontrak | prasyarat kurang | preseden menyesatkan> — <alasan>

## Rollback
- <Tidak perlu | berkas yang perlu dipulihkan/dihapus pendispatch>

## Triase
<ditulis architect: baris matriks bagian 3 yang berlaku, hasil pemeriksaan anchor, tindakan restore>
```

`frontend:plan` mode APPEND membaca `## Triase` dan `## Out of Scope / Mismatch` `report-<NN>.md` — apa pun statusnya, termasuk `DONE` yang diturunkan retroaktif — sebagai sumber brief remedi atau brief perbaikan. `frontend:report` dan kanal umpan balik profil membaca baris `preseden menyesatkan` dari sini — bukan dari percakapan.

---

## 5. Gerbang Kompilasi Per-Brief

Pakai `typecheck_per_brief` dari baris `Terselesaikan:` prasyarat rantai (nilai profil `commands.md`, fallback adapter).

| Nilai | Tindakan sesudah commit unit |
|---|---|
| `tidak` | Lewati; pembuktian menunggu Phase 4 |
| `ya` | `python3 «run_verification.py» closing --taskdir <taskdir> --cmd typecheck='<typecheck commands.md>' --out {taskdir}/.explore/gate-<NN>.md` — dibandingkan dengan baseline Phase 0 (diukur sebelum unit pertama mendarat); exit 1 = galat baru atau `TIMEOUT` |

Vonis **relatif baseline**: nol galat *baru*, bukan hijau absolut. Galat baru → unit `BLOCKED` retroaktif: tambahkan `## Triase` berisi galat mentahnya ke `report-<NN>.md`, dan turunkan brief `DONE` → `BLOCKED` di disk (tanpa commit). Kode unit **tetap** di tree — `git revert` hanya atas persetujuan eksplisit user, karena ia membalik kode yang dinilai `report-<NN>.md`. Brief remedi (`remedies: "<NN>"`) memperbaikinya dengan aksi `MODIFY`. Dilarang melanjutkan ke `NN+1` di atas galat yang unit ini terbitkan. Lint, test, dan build tidak pernah ikut gerbang ini.

---

## 6. Siklus `status` Brief

| Dari | Pemicu | Ke | Penulis | Ikut di-commit (kode saja) |
|---|---|---|---|---|
| — | Batch brief ditulis `plan`, disetujui user lewat `chain.py approve --row BRIEF` | `READY` | `frontend:plan` | — (`chain.py approve` menulis `sidik_kontrak` dan kejadian `approve BRIEF`) |
| `READY` | `report-<NN>.md` `DONE` + matriks bagian 3 bersih | `DONE` | `architect` | `files_touched` |
| `READY` | `report-<NN>.md` `FAILED` atau pelanggaran scope | `BLOCKED` | `architect` | — (suntingan disk) |
| `DONE` | Galat kompilasi baru di gerbang bagian 5 | `BLOCKED` | `architect` | — (suntingan disk; `report-<NN>.md` ber-`## Triase`) |
| `DONE` tanpa commit unit (fase `TERPUTUS`) | Laporan absen/rusak + tree bersih (bagian 3) | `READY` | `architect` | — (suntingan disk; dispatch ulang) |

Brief `BLOCKED` tidak pernah dinaikkan lagi, dan brief `DONE`/`BLOCKED` tidak pernah disunting lagi — kecuali `DONE` yang tak pernah mendarat (fase `TERPUTUS`), yang belum pernah menjadi unit sah. Pekerjaan unit `BLOCKED` diambil alih brief remedi (`remedies: "<NN>"`) pada taskdir yang sama — `chain.py reopen --row BRIEF` (kaskade: hop tercentang di bawahnya ikut terbuka) lalu `frontend:plan` mode APPEND. Cacat pada unit `DONE` (temuan `REVIEW.md` `BLOCKED`, verifikasi penutup merah) diambil brief perbaikan tanpa `remedies` lewat jalur yang sama. Plafon 2 remedi per unit asal (`validate_briefs.py` Check M); remedi ketiga dilarang, cacatnya ada di kontrak: `chain.py reopen --row CONTRACT` — pada `HOTFIX_MINOR` yang tak punya hop CONTRACT: `chain.py reopen --row BRIEF` lalu `chain.py escalate --lane FAST_FORWARD --sections architecture`.

---

## 7. Verifikasi Penutup & Log

Dijalankan sekali di Phase 4, sesudah seluruh brief tertutup. Perintah: seluruh baris `commands.md` profil (typecheck, lint, test, build), ditambah tiap perintah `verification` brief yang belum tercakup. Baca kolom **Cakupan yang TIDAK Diperiksa** profil sebelum menyimpulkan — test hijau bukan bukti typecheck hijau bila adapter menyatakan demikian.

`run_verification.py closing` menulis `{taskdir}/.explore/closing-verification.md` (laci kerja, tidak di-commit) — sumber tunggal `## Verifikasi Penutup` `REVIEW.md`. Tabel dan ekor log diketik mesin, bukan LLM; galat baru = tanda galat ternormalisasi yang tidak ada di `verification-baseline.json` Phase 0, dihitung per kemunculan — galat kedua yang identik dengan galat warisan tetap baru. Log mesin `closing-verification.json` membawa `baseline_head` tiap perintah; `validate_review.py --log` menolak baseline yang diukur sesudah commit `implement unit` pertama rantai (baseline absen → Phase 0 butir 2):

```markdown
| Perintah | Hasil | Galat baru vs baseline | Exit | Durasi | Perintah penuh |
|---|---|---|---|---|---|
| `typecheck` | HIJAU | 0 | 0 | 12.4s | `pnpm typecheck` |
| `test` | MERAH | 0 | 1 | 40.2s | `pnpm test` |

### <perintah yang tidak HIJAU> — <MERAH | TIMEOUT>
<40 baris terakhir keluaran mentah>
Log penuh: `<taskdir>/.explore/verification-logs/closing/<nama>.log`
```

**Merah** (exit 1) → klasifikasikan tiap perintah yang tidak `HIJAU`, lalu hentikan rantai sebelum reviewer berangkat. Merah tanpa kelas tidak pernah terjadi: tiap baris tabel jatuh ke tepat satu cabang di bawah.

| Tanda di `closing-verification.md` | Kelas | Rute |
|---|---|---|
| galat baru menyebut berkas | cacat eksekusi / berkas yatim | dua butir di bawah tabel ini |
| `Exit` 126/127 | perintah tidak dapat dijalankan — selalu galat baru, tidak pernah warisan | perintah `commands.md` profil salah, bukan cacat rantai: `frontend:profile` REFRESH atas persetujuan user → baseline diukur ulang `--force` di worktree akar (Phase 0 butir 2) → Phase 4 ulang |
| `TIMEOUT` (juga `TIMEOUT warisan`) | tak terverifikasi — merah | ulang sekali dengan `--timeout` 3× lipat; masih `TIMEOUT` → `AskUserQuestion`: perbaiki perintah/lingkungan (REFRESH + baseline ulang) atau hentikan. Tidak ada opsi "terima": `validate_review.py` memvonis `TIMEOUT` = `BLOCKED` |
| `MERAH` yang ekor lognya tidak menyebut satu pun berkas (mis. tanpa baris bertanda galat — tanda galatnya ekor log itu sendiri) | tak terklasifikasi mesin | sajikan ekor log ke user lewat `AskUserQuestion`: cacat eksekusi (brief perbaikan membaca log ini) atau hentikan |

- **Cacat eksekusi** — berkas di dalam union. Brief pemiliknya dari `git log --oneline -- <berkas>`. Rute, di taskdir yang sama: `chain.py reopen --row BRIEF` → `plan` APPEND brief perbaikan (tanpa `remedies` — unit asalnya `DONE`) yang membaca log ini → `architect` eksekusi → Phase 4 ulang.
- **Cacat perencanaan (berkas yatim)** — berkas di luar union: tidak satu pun brief mengklaimnya, tidak satu pun gate menyetujui blast radius-nya. Rute: `chain.py reopen --row CONTRACT` (kaskade membuka BRIEF) → `contract` melengkapi `## 1. Files Touched` → approve → `plan` APPEND. Pada `HOTFIX_MINOR`: `chain.py reopen --row BRIEF` → `chain.py escalate --lane FAST_FORWARD --sections architecture` → `contract` → `plan` APPEND. Menyuruh `plan` mengarang brief penampung tanpa kontrak dilarang.

**Hijau** (exit 0) → jalankan ulang `«check_preconditions.py» --taskdir <taskdir>` sebelum reviewer berangkat. Check 8 `FAIL` = perintah verifikasi meninggalkan jejak di tree (snapshot baru, coverage, `*.tsbuildinfo`, `lint --fix` atas berkas ter-track). Hentikan, sajikan path-nya ke user, dan ikuti keputusannya: buang/pulihkan, pola ignore lewat `frontend:profile` REFRESH, atau brief perbaikan bila berkas itu memang bagian rantai. Pembersihan otomatis dilarang karena berkas ter-track yang termutasi hanya dapat dinilai user. Tanpa langkah ini, check `TREE` `validate_review.py --log` memvonis jejak itu sebagai mutasi reviewer, dan penutup berulang tanpa akhir.

Rute yang sama berlaku bagi `REVIEW.md` ber-verdict `BLOCKED` (P1, SC belum terbukti → cacat eksekusi; berkas yatim → cacat perencanaan). Review ulang sesudah brief perbaikan `DONE` menimpa `REVIEW.md` utuh; `REVIEW.md` yang `head:`-nya mendahului commit kode terakhir dianggap basi (fase `PENUTUP`).

---

## 8. Kategori Galat Terminal & Resolusi Sah

Kategori generik lintas stack. Tabel per stack — nama galat persis dan resolusi idiomatiknya — di `## Failure signatures` adapter; tabel adapter menang.

| Kategori | Penyebab umum | Resolusi sah |
|---|---|---|
| Type Mismatch | Tipe lokal berbeda dari DTO `CONTRACT.md` | Sesuaikan tipe lokal ke kontrak; jangan ubah tipe backend |
| Missing Module / Export | Alias tidak sinkron `tsconfig` ↔ bundler, barrel hilang | Periksa alias kedua config; ekspor simbolnya |
| Reaktivitas / Efek | Dependensi efek hilang, rune di berkas salah, state didestrukturisasi | Ikuti jebakan `## Layer taxonomy` adapter |
| Test Async Timeout | Panggilan asinkron tidak ditunggu | `waitFor`/`findBy*` Testing Library stack |
| Render Loop | Mutasi state di badan komponen | Pindahkan ke handler Controller atau efek |
| Framework Boundary | Server-only di client, `process.env` di bundle Vite, modul native tanpa dev build | Pindahkan ke sisi yang benar; dilarang menambah config untuk menyembunyikan |
| Mock Handler Miss | Endpoint tidak terdaftar di handler mock | Tambah handler di berkas test lokal terkait |

---

## 9. Anti-Pattern

- Menjalankan lint/test/build per unit "sekadar memastikan" — oleh subagent maupun `architect`.
- Menonaktifkan rule (`eslint-disable`, `@ts-ignore`, `svelte-ignore`) atau mengedit `tsconfig.json`/`package.json`/config bundler untuk meloloskan verifikasi.
- Menghapus, men-skip, atau melemahkan assertion test yang gagal; mengubah mock global demi test lokal.
- Mendispatch ulang unit `BLOCKED` secara buta, atau memindahkan sisa pekerjaan ke taskdir baru — itu menyembunyikan brief `BLOCKED` dari tiap gerbang yang memindainya.
- Menyimpulkan status unit dari kata balikan tanpa matriks bukti disk.
