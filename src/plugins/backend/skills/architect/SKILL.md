---
name: architect
description: Gunakan ketika direktori taskdir berisi brief READY siap dieksekusi atau rantai terputus - orkestrasi sekuensial brief dan review penutup, sebelum mengeksekusi tanpa verifikasi dan atomic commit.
---

## THE IRON LAW

- Jalankan brief satu per satu secara sekuensial dan jangan pernah menyentuh `src/` secara langsung.
- Dilarang menjalankan implementor secara paralel atau meneruskan brief jika terdapat status `BLOCKED`.
- Commit dikerjakan penulisnya, bukan oleh skill ini.
- Verifikasi tiap commit benar-benar mendarat dan diff-nya tidak melewati file scope sebelum melanjutkan.
- Dispatch `code-reviewer` tepat satu kali di akhir tiap putaran rantai atas merge-base `base_branch` HEAD; putaran baru dimulai saat `REVIEW.md` basi.

## Precondition [REQUIRED]

1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/architect/scripts/check_preconditions.py --taskdir <taskdir> [--base-branch <base_branch>]`.
2. Evaluasi output skrip secara deterministik:
   - `PASS` (7/7 checks): Lanjutkan ke evaluasi parameter dan workflow orkestrasi brief.
   - `FAIL`: Hentikan eksekusi segera dan jalankan tindakan remediasi pada butir yang gagal (taskdir belum sah/tidak ada → minta alokasi dari `backend:tech-lead`; profil/invariants hilang → arahkan ke `backend:profile`; brief READY tidak ditemukan → jalankan `backend:plan`; brief `BLOCKED` → `backend:tech-lead` (lane `PLANNING`, taskdir sama); `HALT.md` ada → `backend:tech-lead` (check 7 menyebut brief dan verdict-nya); working tree kotor atau operasi git (merge/cherry-pick/revert/rebase) menggantung → bersihkan/selesaikan sebelum melanjutkan; HEAD detached/di base branch atau `base_branch` tak resolve → kembali ke gerbang `backend:tech-lead`).

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — Path direktori kerja aktif yang memuat rangkaian brief.
- `base_branch` — string — `[OPTIONAL]` — Branch dasar pembanding (default: dari profile).
- `max_retries_per_brief` — integer — default `1` — Batas retry dispatch per brief, dibaca di Fase 3 hanya pada cabang "dispatch tidak pernah berangkat"; cabang lain dilarang retry.
- `typecheck_per_brief` — boolean — default dari baris `typecheck-per-brief` `## Commands` profil — Jalankan gerbang kompilasi sesudah tiap brief (Fase 3 butir 3b). Nilai `false` menonaktifkannya pada stack mana pun; nilai `true` tidak dapat menghidupkannya bila ketiga perintah kompilasi profil bernilai `tidak berlaku`.

## Workflow

### Fase 0 — Verifikasi Prasyarat & Penyerapan Profil Repositori

1. Jalankan skrip `check_preconditions.py` dengan parameter `taskdir` dan `base_branch`.
2. Hentikan eksekusi segera jika skrip menghasilkan `FAIL`. Laporkan butir gagal beserta tindakan perbaikannya ke gerbang `backend:tech-lead`. Dilarang mengabaikan prasyarat yang gagal.
3. Serap profil: `base_branch`, `commit_convention`, `source_root`, `stack` dari `index.json`, perintah `build`/`typecheck`/`typecheck-scoped`/`typecheck-per-brief`/test dari `commands.md`, dan invariant (setelan skema penyimpanan, tenant scoping, zona waktu) dari `invariants.md`.
3a. **Baseline verifikasi dikunci ke merge-base.** Baseline adalah hasil `build` dan `test` — ditambah `typecheck` (perintah gerbang Fase 3 butir 3b) bila `typecheck-per-brief` `ya` — pada `$(git merge-base <base_branch> HEAD)`, bukan pada HEAD sesi ini: galat yang diperkenalkan brief mana pun di taskdir ini tetap terhitung "baru" sampai diperbaiki. Pengukurnya selalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py baseline --taskdir <taskdir absolut> --cmd build='<build>' --cmd test='<test>' [--cmd typecheck='<typecheck>']`, dipanggil lewat Bash `run_in_background: true` lalu ditunggu notifikasi selesainya; skrip menyimpan exit code, durasi, dan tanda galat tiap perintah ke `{taskdir}/.explore/verification-baseline.json`. Berkas itu ada → dipakai ulang apa adanya (skrip menolak mengukur ulang tanpa `--force`); dilarang mengukur ulang di atas brief yang sudah mendarat. Tidak ada dan HEAD = merge-base → ukur di tempat. Tidak ada dan HEAD ≠ merge-base → ukur di worktree sementara di luar repo: `wt=$(mktemp -d)/wt; git worktree add -q --detach "$wt" <merge-base>; (cd "$wt" && python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py baseline --taskdir <taskdir absolut> --cmd …); git worktree remove --force "$wt"`. Worktree tidak dapat dibangun (dependensi di luar git, mis. `node_modules`) → catat `Baseline: TERDEGRADASI (<alasan>)` dan ukur di HEAD sebelum brief pertama sesi ini berangkat — `HALT.md` tetap menahan brief yang sudah divonis merah. `TIMEOUT` di baseline → ukur ulang **sekali** dengan `--timeout` 3× lipat dan `--force` (skrip mencetak nilainya), tetap di merge-base; masih `TIMEOUT` → catat apa adanya. Merah atau `TIMEOUT` di merge-base bukan alasan menghentikan rantai: ia justru fakta yang membuat gerbang per-brief dan gerbang penutup dapat memvonis galat **baru** alih-alih menuntut hijau absolut atas repo yang memang belum hijau. Catat `Baseline: <sha7 merge-base> · <baris BASELINE skrip, satu per perintah | TERDEGRADASI (<alasan>)>` di laporan penutup, dan `baseline: <sha7> · <hijau | merah (<n> galat)>` untuk perintah gerbang di `HALT.md`.
4. Pastikan `git status --porcelain` kosong, `git branch --show-current` sesuai branch taskdir, dan tidak ada rebase in-progress (`.git/rebase-apply` / `.git/rebase-merge`). Berkas di bawah segmen `.explore/` adalah laci kerja `code-explorer` — bukan artefak rantai, tidak di-stage, dan **tidak dihitung sebagai working tree kotor**. Skrip prasyarat sudah membuangnya lebih dulu; buang barisnya juga saat membaca `git status` sendiri, supaya taskdir yang memakai fan-out explorer di `plan` Fase 2 tidak dihentikan oleh berkas yang memang dirancang tertinggal.

### Fase 1 — Penelusuran Titik Mulai Rantai Brief (Brief Traversal)

Pindai direktori tugas untuk menentukan titik awal eksekusi deterministik:

1. Jalankan `ls {taskdir}/`, baca frontmatter tiap `brief-<NN>-<unit>.md` urut `NN`.
2. Tetapkan titik masuk dari field `entry` check 3 skrip prasyarat (`--json`; keluaran teks mencetaknya sebagai `Titik masuk`), lalu konfirmasi dengan frontmatter:
   - `DONE` atau `SUPERSEDED`: Lewati, lanjut ke `NN` berikutnya. `SUPERSEDED` sah hanya bila bertaut dua arah ke pengganti ber-NN lebih besar — skrip sudah menagihnya.
   - `READY` (`entry` `FASE_3:<NN>`): Tetapkan sebagai titik mulai rantai aktif.
   - `BLOCKED`: Hentikan eksekusi, laporkan ke gerbang. Brief itu ditutup `plan` lewat brief pengganti, bukan oleh skill ini — skrip sudah `FAIL` di check 3 sekalipun ada brief `READY` sesudahnya.
   - Nilai di luar `READY|DONE|BLOCKED|SUPERSEDED`: Hentikan eksekusi, laporkan nilai terbaca beserta path briefnya.
   - Seluruh brief tertutup (`DONE`/`SUPERSEDED`): ikuti `entry` check 3. Rantai dinyatakan tuntas hanya ketika `REVIEW.md` **dan** `REPORT.md` sama-sama ada.
     - `FASE_4` — `REVIEW.md` belum ada **atau basi** (commit kode mendarat sesudah `HEAD` yang dinilainya, ujung `range:` frontmatter-nya): Lompat ke Fase 4 untuk verifikasi penutup lalu satu review baru. Dilarang menilai kesegaran `REVIEW.md` sendiri dari keberadaan berkasnya — skrip membandingkan `range:` dengan riwayat commit kode.
     - `FASE_5` — `REVIEW.md` segar, `REPORT.md` belum ada: Lompat ke Fase 5 untuk memanen laporan rantai yang belum terbit — `report` yang gagal atau tidak pernah berangkat di sesi sebelumnya dijemput persis di sini. Rekonstruksi tabel commit trail dari `git log` dan severity dari `REVIEW.md`; dilarang mendispatch ulang implementor maupun reviewer yang keluarannya sudah mendarat.
     - `KOREKSI:<NN>:<sha7>` — brief `READY` yang commit ber-`commit_message`-nya sudah mendarat: jalankan koreksi status menurut matriks bukti disk `references/lifecycle-recovery.md` bagian 3, dilarang mendispatch ulang implementor, lalu jalankan ulang skrip prasyarat.
     - `TUNTAS` — keduanya ada: Rantai tuntas. Laporkan apa adanya tanpa mendispatch siapa pun dan tanpa menulis ulang artefak yang sudah terbit.

### Fase 2 — Presentasi Rencana Kerja & Penguncian Konfigurasi

Sajikan rencana eksekusi sebelum implementor pertama berangkat:

1. **Presentasi Rantai Brief**: Tampilkan tabel ringkasan nomor urut `NN`, nama unit, tingkat risiko, dan daftar berkas `## File scope`.
2. **Atomic Commit Rantai**: Pastikan tiap implementor meng-commit kode unitnya sendiri dalam satu commit bersubjek `commit_message` brief, ditambah satu commit indeks issues oleh reviewer di akhir. Brief, `HALT.md`, `REVIEW.md`, dan `REPORT.md` tidak di-commit: dokumen taskdir diabaikan git (Langkah 24).
3. **Penanganan Penundaan**: Tuntaskan brief sebelumnya jika user meminta penundaan satu brief. Hentikan rantai pada brief tersebut dan laporkan penghentiannya. Pertahankan status `READY` agar pengerjaan berikutnya melanjutkan dari titik tersebut. Dilarang melompati brief ke `NN+1` karena urutan `NN` adalah DAG linear.
4. Kunci konfigurasi eksekusi sebelum mendispatch implementor pertama.

### Fase 3 — Eksekusi Sekuensial Brief & Verifikasi Commit Hilir

Eksekusi tiap brief `READY` bergantian mengacu `references/lifecycle-recovery.md`:

1. **Dispatch Implementor Terisolasi**: Muat template prompt dari `dispatcher/implementor.md`, hidrasi slot `taskdir`, `brief_path`, `unit_name`, dan `adapter_path` — isi `adapter_path` dengan `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md` memakai `stack` hasil Fase 0. Batalkan dispatch dan rutekan ke `backend:profile` bila berkas adapter itu tidak ada di disk. Tulis lease pagar Bash/Edit/Write: `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/guard_bash.py lease --brief <brief_path>` — hook `PreToolUse` plugin menolak perintah implementor di luar allowlist dan path di luar lease; tanpa lease seluruh Bash/Edit/Write implementor ditolak. Lease gagal (exit 2: `## File scope` kosong atau tak terbaca) → batalkan dispatch. Sesudah triase unit selesai (butir 2–4: commit unit mendarat, atau `BLOCKED`/`HALT.md` tertulis), cabut dengan `guard_bash.py lease --clear`. Lalu panggil subagent `code-implementor` secara langsung tepat **satu kali per brief**. Tangkap balikan `## Implementor Report — brief-{NN}-{unit}`. Dispatch gagal: `## Failure path` butir 8.
2. **Triase `DONE`**: Pastikan implementor telah menulis `status: DONE` di disk dan meng-commit kode unitnya sendiri.
   - Catat SHA dari baris `Commit:` laporan implementor untuk pelaporan akhir.
   - Commit sendiri berkas kode yang tertinggal memakai `commit_message` frontmatter brief jika baris `Commit:` berbunyi `SKIPPED`. Catat penyimpangannya di laporan penutup.
3. **Triase `BLOCKED`**: Putuskan tindakan berdasarkan bukti disk aktual — jalankan matriks tujuh baris di `references/lifecycle-recovery.md` bagian 3 dan ambil tindakan persis sesuai barisnya. Dilarang menebak status tanpa verifikasi disk.
   - **Rantai terhenti tidak pernah direview.** Baris mana pun yang berbunyi HENTIKAN membawa rantai langsung ke Fase 5 dengan `Execution Status: BLOCKED (di brief-NN)`, `Verifikasi Penutup: tidak dijalankan (rantai terhenti)`, dan `Review Severity: tidak dinilai (rantai terhenti)`. Fase 4 dilewati utuh: gerbang verifikasinya menuntut brief `NN` tertinggi `DONE`, dan `dispatcher/reviewer.md` menuntut build hijau — mendispatch `code-reviewer` di atas rantai separuh menghasilkan temuan yang tak dapat dipisahkan dari pekerjaan yang memang belum ditulis. Kendali kembali ke `backend:tech-lead`, yang mengklasifikasikan sisa pekerjaan sebagai **brief perbaikan pada taskdir yang sama** lewat lane `PLANNING`. Dilarang memindahkannya ke taskdir baru: itu menyembunyikan brief `BLOCKED` dari tiap gerbang yang memindainya dan memutus `Consumes` brief sisanya dari `Produces` brief yang sudah `DONE` (`references/lifecycle-recovery.md` bagian 3).

3b. **Gerbang Kompilasi Per-Brief** (sesudah tiap brief sukses commit, sebelum `NN+1` berangkat):

   Baris `typecheck-per-brief` `## Commands` profil menentukan apakah gerbang ini berjalan. Bernilai `tidak` — java-spring, php, dan php-codeigniter, yang kompilasinya build penuh atau analisis statis berbaseline — lewati seluruhnya dan catat `Gerbang kompilasi: penutup saja (<stack>)`; verifikasinya tetap berdiri di Fase 4. Parameter `typecheck_per_brief` bernilai `false` menonaktifkannya pada stack mana pun.

   Bernilai `ya`:

   - **Perintah**: `typecheck-scoped` bila ada dan modul targetnya terbaca dari `## File scope` brief; selain itu `typecheck`. Keduanya `tidak berlaku` → turun ke `build`. Ketiganya `tidak berlaku` → gerbang ini `SKIP` dan dicatat, bukan dianggap lolos.
   - **Vonis relatif baseline, bukan hijau absolut.** Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py closing --taskdir {taskdir} --cmd typecheck='<perintah>' --out {taskdir}/.explore/gate-NN.md` — nama `typecheck` membuatnya dibandingkan dengan baseline Fase 0 butir 3a. Exit 0 = tidak ada galat baru; exit 1 = galat **baru** atau `TIMEOUT` — hanya itu yang menahan rantai. Dilarang memipe keluaran ke `tail`/`head` atau menebak vonis dari teks log.
   - **Merah baru → `BLOCKED (di brief-NN)`**: brief itu melanggar lantai "titik hijau mandiri" (`plan/references/slicing-and-scan.md` bagian 3A butir 1) — ia menerbitkan kondisi kode yang tidak kompilabel dan mewariskannya ke brief berikutnya. Tulis `{taskdir}/HALT.md` menurut `references/lifecycle-recovery.md` bagian 3a (`verdict: COMPILE`, galat ≤40 baris), di disk tanpa commit (dokumen taskdir diabaikan git), lalu hentikan rantai dan serahkan ke `backend:tech-lead`. Status brief tetap `DONE` — kodenya memang mendarat; `HALT.md` yang menahan sesi berikutnya. Dilarang menambal sendiri dan dilarang melanjutkan ke `NN+1`.

   > Rasional: `references/rationale.md` R1.

4. **Verifikasi Diff Mendarat** (sesudah tiap brief sukses):
   - Jalankan `git status --porcelain`. Berkas di bawah segmen `.explore/` dikecualikan sesuai Fase 0 butir 4 dan tidak pernah dihitung sebagai sisa. Sisa berkas lain → hentikan rantai di brief ini: tulis `HALT.md` `verdict: STRAY` berisi daftar path (bagian 3a `references/lifecycle-recovery.md`) di disk, lalu kembalikan ke `backend:tech-lead`. Dilarang `git restore`, `git clean`, atau `git stash` sendiri.
   - Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/verify_scope.py --brief <brief_path> --commit <sha>`. Himpunan sahnya: path `## File scope` brief, berkas brief itu sendiri, `{taskdir}/report-NN.md` (jalur gagal), dan berkas `finding_source` frontmatter brief **asalkan** diff-nya hanya menambah baris `> Status: FIXED`; laci `.explore/` diabaikan. Kontrak brief di disk wajib sama dengan `sidik_kontrak` yang ditulis `plan` saat batch dikunci (11 H3). Vonis = exit skrip, bukan pembacaan `git show --stat`. Exit 2 (brief tak terbaca, sha salah) → perbaiki pemanggilannya. `FAIL` (exit 1) — berkas di luar himpunan → **hentikan rantai di brief ini**: catat sebagai temuan `P1 — berkas di luar scope` (`../audit/references/findings-contract.md` bagian 1), tulis `HALT.md` (`verdict: SCOPE`, bagian 3a `references/lifecycle-recovery.md`), lewati Fase 4, bawa ke Fase 5 dengan `Status: TERTAHAN (scope brief-NN)`, dan kembalikan kendali ke `backend:tech-lead` yang menanyakan reset ke user. Dilarang melanjutkan ke `NN+1` di atas commit yang mungkin di-reset, dan dilarang menjalankan `git reset` atau `git revert` sendiri.
   - **Bandingkan simbolnya, bukan hanya berkasnya.** Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/architect/scripts/symbol_map.py --sha <sha> --path <path> --anchor "<isi kolom Anchor>"` atas tiap berkas beraksi `modify`. Simbol `kind: fn` di `outside_anchor` (exit 1) adalah temuan `P1 — simbol di luar anchor`; baris `kind: type` (field, import, anotasi di tingkat kelas) di `type_level_unanchored` sah hanya bila nama kelas atau field-nya ada di `Anchor`. Sebut simbol dan `file:baris`-nya, tulis `HALT.md` `verdict: SYMBOL`, lalu hentikan rantai dengan perlakuan yang sama seperti berkas di luar scope. Berkas beraksi `create` dikecualikan: seluruh isinya memang ditulis brief itu. Skrip exit 2 (`DEGRADED`: ekstensi tak dikenal, kurawal tak seimbang) → baca hunk header ber-driver lewat atribut sementara di luar repo: `attr=$(mktemp); printf '*.java diff=java\n*.php diff=php\n*.go diff=golang\n*.rs diff=rust\n*.kt diff=kotlin\n' > "$attr"; git -c core.attributesFile="$attr" show -U0 --format= <sha> -- <path> | grep '^@@'; rm -f "$attr"`, periksa baris `+` yang cocok pola deklarasi secara terpisah (header melekatkan baris signature dan method baru ke simbol sebelumnya), dan catat `Cek simbol: TERDEGRADASI (hunk header)` di laporan.
     > Rasional: `references/rationale.md` R2 dan R3.
   - Sandingkan hasilnya dengan baris `Simbol tersentuh` `## Implementor Report`. Selisih antara yang dilaporkan implementor dan yang terbaca dari peta simbol `symbol_map.py` dicatat apa adanya di laporan penutup.

5. **Berkas Yatim — berkas terdampak yang tak dimiliki brief mana pun**: berkas yang muncul di butir 4, di gerbang verifikasi penutup Fase 4, atau di `REVIEW.md` sementara ia berada di luar **union `## File scope` seluruh brief taskdir**. Catat sebagai `P1 — berkas yatim` (`../audit/references/findings-contract.md` bagian 1) beserta `file:line` dan brief yang menyentuhnya terakhir menurut `git log --oneline -- <berkas>`, lalu kembalikan kendali ke `backend:tech-lead`.

   Dilarang mengarang brief penampungnya sendiri, dilarang memperluas `## File scope` brief yang sudah `DONE`, dan dilarang menjalankan `scaffold_brief.py` dari sini. Rutenya satu: `tech-lead` → lane `PLANNING` → `analyst` re-entry (Fase 3 butir 0) dengan `reentry_reason` menyebut berkas yatimnya → `plan` menambahkan brief di `NN` berikutnya lewat `scaffold_brief.py --append`, yang mempertahankan alokasi brief yang sudah dieksekusi. Berkas yatim adalah cacat perencanaan, dan perencanaan diperbaiki di skill perencananya.

### Fase 4 — Gerbang Verifikasi Penutup & Review Diff Tunggal

Verifikasi berkumpul di sini, tepat satu kali sesudah brief `NN` tertinggi berstatus `DONE`.

1. **Gerbang Verifikasi Taskdir**: Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py closing --taskdir {taskdir} --cmd build='<build>' --cmd test='<test>'` (perintah dari `## Commands` profil, nama sama dengan baseline Fase 0 butir 3a; `build` `tidak berlaku` → `--cmd typecheck='<typecheck>'`) lewat Bash `run_in_background: true`, tunggu notifikasi selesai, lalu baca `{taskdir}/.explore/closing-verification.md`. Vonis = exit skrip dan tabel berkas itu. Dilarang memipe keluaran ke `tail`/`head` atau menebak hijau dari teks log.
   - Exit 0 → catat `Verifikasi Penutup: PASS (<n> perintah, merah warisan <m>)` dan lanjut ke butir 2. `MERAH` bergalat baru 0 adalah warisan baseline, bukan kegagalan rantai ini.
   - Exit 1 (`TIMEOUT` atau galat baru > 0) → hentikan eksekusi, lalu jalankan klasifikasi `## Failure path` butir 4 — cacat eksekusi (4a) atau cacat perencanaan (4b) — atas berkas yang disebut ekor log di berkas hasil, sebelum menyerahkan kendali. Dilarang menambal kode sendiri.
   - Exit 2 → argumen salah; perbaiki pemanggilannya, bukan vonisnya.
2. **Dispatch Code Reviewer**: Muat template prompt dari `dispatcher/reviewer.md`, hidrasi slot `taskdir`, `base_branch`, `adapter_path` (path yang sama dengan Fase 3 butir 1), dan `findings_contract` — isi dengan `${CLAUDE_PLUGIN_ROOT}/skills/audit/references/findings-contract.md`; batalkan dispatch bila berkasnya tidak ada — lalu panggil subagent `code-reviewer` secara langsung tepat **satu kali**.
   - Subagent mengevaluasi diff `git merge-base {base_branch} HEAD`..`HEAD`, menerbitkan `{taskdir}/REVIEW.md` di disk, lalu meng-commit baris indeks issues-nya sendiri.
   - Tangkap balikan berupa path `REVIEW.md` dan satu tingkat severity tertinggi, lalu petakan lewat `### Penanganan Balikan` template itu. Ambil SHA commit indeks dari `git log`, bukan dari balikan.
   - Sesudah balikan, pastikan `git status --porcelain` kosong di luar `.explore/`. Sisa `backenddev/issues/README.md` → baris commit gagal `### Penanganan Balikan`.
   - **Sinkron nataflow**: `REVIEW.md` terbit → jalankan prosedur `tech-lead/references/nataflow-sync.md` (`--taskdir <taskdir>`) di main loop sebelum butir 3, apa pun severity-nya, sehingga hasil review dan status brief terbaru tercermin seketika. Segmennya dibawa ke laporan penutup; `GAGAL` tidak mengubah triase.
3. **Triase Temuan Review**:
   - Dilarang memperbaiki temuan langsung jika severity tertinggi `P1`. Laporkan temuannya dan kembalikan kendali ke gerbang `tech-lead`.
   - Rangkum hasilnya di laporan penutupan jika severity `P2`/`P3`/`CLEAN`.

### Fase 5 — Laporan Penutupan & Serah Terima Terminal

Sajikan laporan deterministik kepada main loop:

1. Tampilkan tabel eksekusi: nomor brief, nama unit, status akhir, SHA commit beserta pemiliknya, dan hasil pemeriksaan scope.
2. **Gerbang Success Criteria**: Baca `## Success Criteria` di `{taskdir}/TASK.md` dan pasangkan tiap butir dengan bukti dari commit unit, `REVIEW.md`, atau hasil gerbang verifikasi penutup.
   - Tandai rantai `TERTAHAN`, sebut butir yang belum terpenuhi, dan kembalikan kendali ke `backend:tech-lead` untuk klasifikasi kerja lanjutan jika ada butir tanpa bukti. Dilarang menyatakan rantai selesai walau severity `REVIEW.md` bernilai `CLEAN`.
   - Tandai rantai `TERTAHAN (akar absen)` dan kembalikan kendali ke `backend:tech-lead` jika `{taskdir}/TASK.md` tidak ada: setiap taskdir yang berujung di skill ini wajib berakar (`tech-lead/references/gate-lifecycle.md` bagian 1a). Dilarang menutup rantai tanpa akar.
3. **Penerbitan Laporan Rantai**: Panggil `backend:report` dengan `taskdir` dan `base_branch` aktif jika rantai tidak `TERTAHAN`. Skill tersebut menulis `{taskdir}/REPORT.md` sendiri di disk lalu mencerminkannya ke nataflow. Catat path dan segmen `Nataflow`-nya dari laporannya. Catat `dilewati (laporan sudah terbit)` jika `REPORT.md` sudah ada. Lewati penerbitan dan catat alasannya jika rantai `TERTAHAN`, rantai berhenti `BLOCKED`, atau severity `REVIEW.md` bernilai `P1` — pada ketiganya `report` akan menolaknya sendiri di prasyarat atau Fase 1-nya, jadi dispatch itu hanya membuang giliran. Dilarang menulis `REPORT.md` sendiri.
4. Tampilkan path `{taskdir}/REVIEW.md`, severity tertinggi, branch aktif, dan total commit yang mendarat. Rantai yang berhenti `BLOCKED` menulis `tidak dinilai (rantai terhenti)` pada kedua kolom review, bukan path berkas yang tidak pernah terbit.
5. Tegaskan larangan `git push`/PR tanpa instruksi user, lalu kembalikan kendali ke main loop.

## Guardrails

- **STRICT NON-AUTHORING**: Dilarang keras membuat, mengedit, atau menghapus berkas kode di `src/` langsung dari main loop architect.
- **SEKUENSIAL MUTLAK**: Dilarang mendispatch implementor paralel; subagent berikutnya berangkat hanya setelah subagent sebelumnya tuntas dan commit mendarat.
- **SATU REVIEW PER PUTARAN**: Reviewer didispatch tepat sekali di akhir tiap putaran rantai. `REVIEW.md` yang dinyatakan basi oleh check 3 menandai putaran baru (brief/kode mendarat sesudahnya), dan tepat satu review baru wajib berangkat sesudah verifikasi penutup hijau.
- **TEST DI PENUTUP, KOMPILASI PER BRIEF**: Test suite dijalankan tepat sekali di Fase 4 butir 1, di luar pengukuran baseline Fase 0 butir 3a. Kompilasi berjalan sesudah tiap brief pada stack yang `typecheck-per-brief`-nya `ya` (Fase 3 butir 3b) — lantai "titik hijau mandiri" menuntutnya, dan pada stack inkremental biayanya mendekati nol. Stack yang kompilasinya build penuh menundanya ke penutup, dan konsekuensinya diterima apa adanya: brief yang memecahkan kompilasi di sana baru ketahuan di Fase 4, dengan diagnosis lewat `git log` Failure path butir 4.
- **COMMIT MILIK PENULISNYA**: Skill ini tidak meng-commit `src/**`, `backenddev/issues/README.md`, maupun dokumen taskdir. Penanda henti `{taskdir}/HALT.md` (bagian 3a `references/lifecycle-recovery.md`) dan koreksi status `READY → DONE` (bagian 3, baris "commit ada, status tertinggal") milik skill ini ditulis di disk tanpa commit. Commit susulan atas kode penulis lain hanya saat commit hilir terbukti gagal, dengan staging path eksplisit tanpa wildcard (`git add .`/`-A` dilarang keras). Dilarang mencabut `HALT.md` — pencabutannya milik `plan` (baris `repairs`) atau gerbang (`doc_seal.py cabut-halt`, scope diterima user).
- **LARANGAN GIT MUTASI REMOTE**: Dilarang `git push`, `git merge`, `git rebase`, atau `gh pr create` tanpa instruksi eksplisit user.
- **DISPATCH LEWAT TEMPLATE RESMI**: Panggil `code-implementor` langsung via template `dispatcher/implementor.md` dan `code-reviewer` langsung via template `dispatcher/reviewer.md`. Dilarang menyusun prompt dispatch di luar template resminya maupun menyalin isi brief ke dalam prompt.
- **FAIL-FAST ON BLOCKED**: Hentikan rantai seketika jika terjadi status `BLOCKED` pada satu brief. Dilarang melompati brief yang gagal.
- **KEPUTUSAN DEFINITIF SAAT INI**: Seluruh isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.
- **RATIONALIZATION PREVENTION**:
  - Dilarang memperbaiki temuan review P1 di dalam siklus architect.
  - Dilarang menahan rantai untuk meminta otorisasi commit, di awal maupun di tiap brief.
  - Dilarang mengabaikan working tree kotor saat inisialisasi.
  - Dilarang mengedit berkas brief, kecuali koreksi `status: READY → DONE` pada baris "commit ada, status tertinggal" matriks bukti disk — suntingan status di disk saja, tanpa commit. Arah balik `DONE → READY` (brief `DONE` tanpa commit unit) bukan wewenang skill ini: kembalikan ke `backend:tech-lead`, yang menjalankan `doc_seal.py buka-done`.
  - Dilarang melakukan git reset destruktif tanpa persetujuan eksplisit user.
  - Dilarang menyimpulkan status akhir brief dari kata balikan tanpa bukti disk.

## Output [REQUIRED]

Sinkron nataflow berjalan di titik dokumen tuntas, bukan sekali di akhir: Fase 4 butir 2 sesudah `REVIEW.md` terbit, dan `backend:report` sesudah `REPORT.md` tertulis. Putaran yang menutup tanpa melewati satu pun dari keduanya — rantai berhenti sebelum review (brief `BLOCKED`, `HALT.md`, verifikasi merah, berkas yatim) atau `REPORT.md` sudah ada (`dilewati`) — menjalankan prosedur `tech-lead/references/nataflow-sync.md` (`--taskdir <taskdir>`) sekali di main loop sebelum laporan di bawah, sehingga status brief, `report-NN.md`, dan `HALT.md` ikut tercermin. Slot `Nataflow` memuat segmen sinkron terakhir putaran ini; `GAGAL` tidak mengubah vonis.

Verifikasi PASS, seluruh brief tertutup, dan review `CLEAN`/`P3`/`P2` → tutup satu baris tanpa blok: `### ARCHITECT EXECUTION REPORT — <COMPLETED | COMPLETED (WARNING)> · <taskdir> · Branch <nama> · Brief <n> DONE (+<m> SUPERSEDED) · Verifikasi <PASS | tidak terverifikasi (TIMEOUT, diterima user)> · Review <CLEAN | P3 (<n>) | P2 (<n>): <ID, ID>> · REVIEW.md @ <sha> · REPORT.md @ <sha> · Nataflow <segmen>`, ditambah baris `Umpan balik profil` bila ada. `COMPLETED (WARNING)` dipakai tepat bila severity tertinggi `P2`; daftar ID `P2` wajib tertulis, dan `report` membawanya ke `## Catatan`. Hapus `(+<m> SUPERSEDED)` bila `m` nol. Blok di bawah hanya untuk `BLOCKED | TERTAHAN`; hapus tiap baris bernilai `—`:

```markdown
### ARCHITECT EXECUTION REPORT — <BLOCKED | TERTAHAN>
- **Rantai**: <taskdir> · Branch <nama-branch-aktif> · Brief <n>/<n> DONE · terhenti di brief-NN
- **Verifikasi**: FAIL (cacat eksekusi di brief-NN — <perintah yang merah>) | FAIL (cacat perencanaan — <n> berkas yatim) | FAIL (TIMEOUT, dihentikan user) | tidak dijalankan (rantai terhenti)
- **Berkas yatim**: <path · brief penyentuh terakhir @ sha> | —
- **Simbol di luar anchor**: <brief-NN · simbol · file:baris> | —
- **Review**: P1 (wajib eskalasi) | tidak dinilai · REVIEW.md @ <sha> | dilewati (<alasan>)
- **Umpan balik profil**: <`file:baris` + pola preseden menyesatkan, dari baris `Umpan balik profil:` report-NN.md> | —
- **Nataflow**: <segmen sinkron terakhir>
```

`Verifikasi FAIL (cacat perencanaan)` beserta daftar `Berkas yatim` diteruskan gerbang ke `analyst` sebagai `reentry_reason` — tulis keduanya utuh. `Umpan balik profil` bertahan sekalipun rantai bersih: gerbang menanyakannya ke user lalu meneruskannya ke `backend:profile` sebagai `reported_anti_patterns`, dan tanpa baris itu pengetahuannya mati bersama taskdir. Commit trail per brief beserta kesesuaiannya terhadap `## File scope` diverifikasi dari `git log`, bukan dicetak ulang di sini.

**Serah-terima.** `Rantai pekerjaan selesai — kembali ke backend:tech-lead di main loop.` Dilarang membuka rantai baru sendiri; keputusan berikutnya milik gerbang.

## Failure path

1. **Working Tree Kotor**: Hentikan di Fase 0, tampilkan daftar file uncommitted, minta user merapikan git tree.

   **Pengecualian yang bukan pekerjaan user**: bila satu-satunya berkas kotor adalah `.gitignore` dan satu-satunya perubahannya baris `.backenddev/`, itu jejak `backend:profile` yang belum sempat di-commit (`profile/SKILL.md` Fase 5), bukan pekerjaan user yang tertinggal. Laporkan apa adanya dan **serahkan keputusannya ke user** — dilarang meng-commit-nya atas nama rantai. Commit semacam itu tidak punya brief pengklaim dan akan dihukum `code-reviewer` sebagai temuan di penutup taskdir, sehingga menambalnya di sini hanya memindahkan cacatnya ke ujung yang lebih mahal. Rute perbaikannya: `backend:profile` hanya menulis baris itu dan tidak pernah meng-commit-nya (penguncinya re-entry `backend:tech-lead`, `gate-lifecycle.md` bagian 6 butir 2), jadi minta user meng-commit `.gitignore` itu sendiri lalu jalankan ulang `architect`.
2. **Implementor Melaporkan BLOCKED**: Jalankan tabel bukti disk Fase 3 butir 3 sebelum menyimpulkan apa pun. Baris yang berbunyi HENTIKAN membawa rantai langsung ke Fase 5 sebagai `BLOCKED (di brief-NN)` — Fase 4 dilewati utuh, reviewer tidak berangkat — lalu kendali kembali ke `backend:tech-lead`. Hanya baris `DONE` normal dan baris koreksi status ("commit ada, status tertinggal") yang melanjutkan rantai ke `NN+1`.
3. **Dispatch Tidak Pernah Berangkat**: Pertahankan brief `READY` jika balikan menyebut kegagalan dispatch dan tree bersih. Ulangi sebanyak `max_retries_per_brief`, lalu eskalasi tanpa menurunkan statusnya.
4. **Verifikasi Penutup Merah**: Hentikan rantai dan laporkan perintah gagal beserta galat mentahnya dari `{taskdir}/.explore/closing-verification.md`. `TIMEOUT` diperlakukan merah. `TIMEOUT` warisan (berkas hasil mencatat baseline juga `TIMEOUT`) → ulangi Fase 4 butir 1 **sekali** dengan `--timeout` 3× lipat; masih `TIMEOUT` → eskalasi ke user lewat `AskUserQuestion` (terima `Verifikasi Penutup: tidak terverifikasi (TIMEOUT)` atau hentikan), bukan diklasifikasi 4a/4b. `MERAH` tanpa baris bertanda galat dibandingkan lewat ekor lognya, dan exit 126/127 (perintah tidak dapat dijalankan) selalu galat baru — keduanya bukan warisan. Sebelum menyerahkan kendali, **klasifikasikan sebabnya** — keduanya berhenti di sini, tetapi rutenya berbeda dan gerbang tidak dapat menebaknya dari stacktrace:

   - **4a — cacat eksekusi**: galat menyebut berkas yang terdaftar di `## File scope` sebuah brief `DONE`. Kembalikan ke `backend:tech-lead` sebagai `Verifikasi Penutup: FAIL (cacat eksekusi di brief-NN)`; gerbang mengklasifikasikannya lewat Keputusan 2 sebagai `DEFECT_RCA` atau brief perbaikan pada taskdir yang sama.
   - **4b — cacat perencanaan**: galat menyebut berkas yang **tidak dimiliki `## File scope` brief mana pun**, atau simbol yang tidak pernah direncanakan. Ini berkas yatim Fase 3 butir 5. Kembalikan ke `backend:tech-lead` sebagai `Verifikasi Penutup: FAIL (cacat perencanaan — <n> berkas yatim)` beserta daftarnya; gerbang memberangkatkan ulang lane `PLANNING` pada taskdir yang sama dengan `reentry_reason` terisi daftar itu.

   Pada kedua cabang, jalankan `git log --oneline -- <berkas>` atas tiap berkas yang disebut kompilator dan namai brief yang menyentuhnya terakhir. Ini nol biaya kompilasi tambahan, dan ia satu-satunya yang membuat "brief mana yang memecahkannya" berhenti jadi tebakan pada stack yang gerbang kompilasi per-briefnya tidak berjalan. Dilarang menambal kode sendiri di cabang mana pun.
5. **Temuan Review Severity P1**: Jangan perbaiki di tempat. Catat di laporan akhir dan arahkan user kembali ke gerbang `tech-lead`, yang memberangkatkan perbaikannya pada **taskdir yang sama** (lane `PLANNING`, `reentry_reason` `REVIEW P1: <ID>`).
6. **Commit Hilir Gagal**: Kunci sendiri berkas memakai `commit_message` frontmatter brief jika subagent melapor commit-nya gagal. Catat penyimpangannya. Hentikan rantai dan serahkan riwayat git ke user jika penguncian tersebut ikut gagal.
7. **Taskdir Rusak / Berkas Terhapus**: Hentikan eksekusi, laporkan inkonsistensi disk.
8. **Balikan Implementor Rusak**: Catat sebagai kegagalan dispatch jika balikan bukan `## Implementor Report — brief-{NN}-{unit}`, lalu jalankan tabel bukti disk. Jangan abaikan commit yang sudah mendarat.
9. **Git Detached HEAD State**: Peringatkan user saat terjadi Detached HEAD. Minta checkout branch sah sebelum melanjutkan commit.
10. **Worktree Baseline Tertinggal**: sesi yang putus di tengah pengukuran baseline Fase 0 butir 3a meninggalkan metadata di `.git/worktrees/`. Jalankan `git worktree prune` sebelum mengukur ulang; tree kerja user tidak tersentuh.

## STYLE

- Gunakan fase bernomor dan kalimat perintah imperatif aktif yang tegas dan to the point tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku dan istilah teknis git baku.
- Sajikan commit hash SHA-1 ringkas (7 karakter pertama) pada tabel ringkasan.
- Prioritaskan rasio sinyal-token tinggi dan hindari spekulasi non-faktual.
