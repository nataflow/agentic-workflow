# Langkah 11 — Robustness Plugin backend (H1–H36)

Sumber: review robustness plugin `backend` 2026-09-27 (lima penelusur paralel: hook, `_common`, skrip
plan/architect/analyst, prasyarat skill lain, orkestrasi dokumen). Temuan TINGGI terbukti lewat probe di
ruang kerja sementara atau jejak kode `file:baris` dari kedua sisi. Basis kode: commit `e90cd69`.

**Status (2026-09-27):** direncanakan.

## Tujuan

Menutup celah yang tersisa sesudah 09/10. Tiga pola yang berulang:

1. **Dua pembaca untuk satu fakta.** Validator dan penegak membaca berkas yang sama dengan aturan berbeda
   (`## File scope` di `validate_briefs.py` vs `verify_scope.py`/lease; `plugin` profil di `_grade` vs
   `owner_of`; shell yang dinilai `shlex` vs yang dijalankan bash).
2. **Plafon tanpa jalan keluar.** Counter yang habis tidak pernah dapat di-reset oleh jalur yang sah
   (ronde reviewer sesudah penolakan user, re-entry, taskdir tanpa ledger), dan "klasifikasi ulang" tidak
   didefinisikan di gerbang.
3. **Bukti yang dapat diakali atau keliru.** Approval tanpa segel, brief yang dapat disunting pelaksananya
   sendiri, verifikasi hijau tanpa satu tanda galat pun, koreksi resmi yang ditolak pemeriksanya sendiri.

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perbaikan + test regresi → suite penuh hijau → commit.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | H1–H7 (hook, `verify_scope.py`, `brief_status.py`, Check C/S) | Pagar dan bukti mendarat; tahap lain berdiri di atas parser `File scope` bersama. |
| 2 | H8–H13 (`validate_briefs.py`, `scaffold_brief.py`, `symbol_map.py`, `commit_lib.py`, `chain_counters.py`) | Pengetatan validator plan; memakai parser tahap 1. |
| 3 | H14–H16 (`run_verification.py`) | Salinan identik be/fe; berdiri sendiri. |
| 4 | H17–H25 (prasyarat, `precondition_lib.py`, `validate_doc.py`, `migrate_profile.py`) | Mengubah fixture approval BRD/PRD yang dipakai test tahap 5. |
| 5 | H26–H36 (SKILL, rujukan, agent, `detect.py`, README) | Orkestrasi; bergantung pada perilaku skrip tahap 1–4. Versi plugin dinaikkan di sini. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. **Lintas plugin** = berkas identik atau pola
yang sama di plugin lain. **Test tersentuh** = test yang ada dan harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| H1 | `hooks/guard_bash.py` (be, fe) | subagent implementor/explorer/reviewer be, reviewer fe | **ya** — pola `META` sama di fe | `test_l34_guard_bash.py`, `test_09_robustness.py` (be/fe) | Sedang: `$` apa pun kini ditolak; `<`/`>` di dalam kutip kini lolos. |
| H2 | `_common/verify_scope.py` (be=fe), `plan/scripts/validate_briefs.py` | lease `guard_bash.py`, architect Fase 3, Check S | **ya** — `verify_scope.py` identik fe | `test_l34_implementor_no_bash.py` (fe, identitas) | Rendah: baris beraksi < 4 kolom tak lagi masuk lease dan FAIL di Check S. |
| H3 | `_common/verify_scope.py` | architect Fase 3 (gerbang scope), fe architect `--worktree` | **ya** | `test_09_robustness.py` fe (worktree) | Sedang: brief yang disunting di luar `status:`/`## Work status` kini FAIL. |
| H4 | `_common/verify_scope.py` | sama dengan H3 | **ya** | — | Rendah: `-z --no-renames`; merge → exit 2. |
| H5 | `_common/brief_status.py` (`done_sha`) | architect check 3, report | tidak | `test_09_robustness.py` E18 | Rendah: koreksi resmi kini dikenali lewat `landed_sha`. |
| H6 | `validate_briefs.py` Check C, `scaffold_brief.py validate_spec` | plan Fase 3–4 | tidak | — | Rendah: `commit_message`/`unit` ganda kini FAIL. |
| H7 | `validate_briefs.py` Check C, `scaffold_brief.py scaffold`, architect check 3 | plan, architect | tidak | — | Rendah: NN ganda / brief `READY` di luar matriks kini FAIL. |
| H8 | `validate_briefs.py` Check K/J | plan Fase 4 | tidak | `test_plan_preconditions.py`? (fixture Migration) | Rendah |
| H9 | `validate_briefs.py` state ronde | plan Fase 5 | tidak | `test_l27_plan_state.py` | Rendah: state rusak kini FAIL alih-alih reset. |
| H10 | `validate_briefs.py` Check N/C | plan Fase 4 | tidak | — | Rendah: FAIL palsu hilang; `create` ganda FAIL; anchor tumpang tindih WARN. |
| H11 | `architect/scripts/symbol_map.py` | architect Fase 3 butir 4 | tidak | `test_l29_symbol_map.py` | Rendah: hunk campuran kini memetakan sisi lama juga. |
| H12 | `validate_briefs.py` Check S, `_common/commit_lib.py`, `scaffold_brief.py` | plan, `commit_template` profil | tidak | `test_08b_commit_template.py` | Rendah: pola `ticket` dilonggarkan, template liar ditolak. |
| H13 | `analyst/scripts/chain_counters.py`, `analyst/scripts/check_preconditions.py` | analyst Fase 0/3/4/5 | tidak | `test_l213_counters.py`, `test_analyst_preconditions.py` | Rendah: tabel yang diturunkan tangan kini menahan `--bump` dan check 7. |
| H14 | `_common/run_verification.py` (be=fe) | architect Fase 3/4 be, fe architect | **ya** — identik | `frontend/test_run_verification.py`, `test_validate_review.py` fe | Sedang: MERAH tanpa tanda galat kini dibandingkan lewat ekor log; exit 126/127 selalu baru. |
| H15 | `_common/run_verification.py`, `architect/SKILL.md` | architect Fase 0/4 | **ya** | sama | Rendah |
| H16 | `_common/run_verification.py` | sama | **ya** | sama | Nihil |
| H17 | `_common/precondition_lib.py` (`approval_verdict`), prasyarat `system-analysis`, `plan` | hop PRD, plan jalur `PRD` | tidak | `test_system_analysis_preconditions.py`, `test_plan_preconditions.py`, `test_e2e_langkah2.py` (fixture `status: APPROVED`) | **Sedang**: BRD/PRD `APPROVED` tanpa commit `docs(spec): approve …` kini FAIL. |
| H18 | prasyarat `system-analysis` | hop PRD | tidak | `test_system_analysis_preconditions.py` | Rendah |
| H19 | prasyarat `business-analysis`, `system-analysis` | hop BRD/PRD | tidak | kedua test prasyarat | Rendah: tree kotor di luar taskdir kini FAIL. |
| H20 | prasyarat `task`, `tech-lead/SKILL.md` Fase 3, `gate-lifecycle.md` | lane `DEFECT_RCA`, backfill `EXEC_BRIEF` | tidak | `test_task_preconditions.py` | Sedang: `task` kini menolak HEAD di base/detached. |
| H21 | `_common/precondition_lib.py` (`cli`), prasyarat `tech-lead` | semua skrip ber-`cli()` | tidak | — | Nihil |
| H22 | `_common/precondition_lib.py` (`load_profile_index`) | semua prasyarat | tidak | `test_common_parsing.py` | Rendah |
| H23 | `_common/validate_doc.py` (PRD P1/P2) | `system-analysis` Fase 8 | tidak (validate_doc be ≠ fe/analyst) | `test_08b_validate_doc.py` | Rendah |
| H24 | `profile/scripts/migrate_profile.py` (be=fe) | `profile` mode MIGRATE | **ya** — identik | `backend/`/`frontend/test_migrate_profile.py`, `hooks/test_detect.py` (identitas) | Rendah |
| H25 | `_common/brief_status.py` (`set_frontmatter`), prasyarat `tech-lead` | scaffold (SUPERSEDED) | tidak | `test_brief_status.py` | Nihil |
| H26 | `tech-lead/SKILL.md`, `gate-lifecycle.md`, `decisions.md`, analyst check 7 | gerbang Fase 3/5, analyst Fase 0 | tidak | `test_analyst_preconditions.py` | Sedang: taskdir tanpa ledger kini FAIL di analyst, rutenya `plan` jalur `RCA`. |
| H27 | `chain_counters.py`, `validate_briefs.py` (generasi), `analyst/SKILL.md`, `chain-rules.md` | analyst Fase 4, plan Fase 5 | tidak | `test_l213_counters.py`, `test_l27_plan_state.py` | Rendah |
| H28 | `tech-lead/SKILL.md`, `gate-lifecycle.md`, `analyst/SKILL.md` | gerbang, analyst Failure path | tidak | — | Nihil (prosa) |
| H29 | `hooks/detect.py` (be=fe), `profile-template.md` | hook SessionStart, prasyarat | **ya** — identik | `hooks/test_detect.py` | Rendah: `plugin: backend` kini dibaca sama dengan `backenddev`. |
| H30 | `tech-lead/SKILL.md`, `decisions.md`, `gate-lifecycle.md` | gerbang Fase 3 | tidak | — | Nihil (prosa) |
| H31 | `agents/code-implementor.md`, `agents/code-reviewer.md`, `architect/dispatcher/*.md` | subagent | tidak | `test_lint_plugins.py` | Nihil |
| H32 | `agents/code-explorer.md` | gerbang `EXPLORE_FACT` | tidak | — | Nihil |
| H33 | `agents/code-reviewer.md` (tools) | architect Fase 4 | tidak | `test_l36_reviewer_branch.py`? | Nihil (hook sudah menangani Edit reviewer) |
| H34 | `analyst/SKILL.md` Guardrails | analyst Fase 6 | tidak | — | Nihil |
| H35 | `tech-lead/SKILL.md`, `analyst/SKILL.md`, rujukan | gerbang, analyst | tidak | `test_lint_plugins.py` (R2) | Nihil |
| H36 | `hooks/detect.py` (be=fe), README | hook SessionStart | **ya** | `hooks/test_detect.py` | Nihil |

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| H1 | Satu penilai shell bersama di tiap guard: tolak `$`, backtick, CR/LF, dan brace expansion (`{a,b}`/`{1..3}`) di mana pun; operator (`; & \| < > ( )`) dinilai **sesudah** tokenisasi `shlex` ber-`punctuation_chars`, sehingga `<T>`/`->` di dalam kutip lolos. Diterapkan di be dan fe. | `shlex` bukan bash: ANSI-C `$'…'` dan brace expansion diperluas bash tetapi terbaca literal oleh `shlex`. Menolak kelas karakternya lebih pasti daripada meniru bash. |
| H2 | Aturan baris `File scope` tunggal: baris beraksi (`modify`/`create`) sah hanya dengan ≥ 4 kolom. `verify_scope` (dan lease) memakai aturan yang sama; heading dibaca tak peka huruf; Check S menolak baris beraksi yang kolomnya kurang dan heading seksi wajib yang ejaannya menyimpang dari template. | Yang dieksekusi = yang divalidasi. |
| H3 | `verify_scope --commit` membaca scope dari `<sha>^:<brief>` (brief sebelum commit unit), dan diff brief di commit itu hanya boleh menyentuh baris `status:` frontmatter dan baris tabel `## Work status`. Mode `--worktree` membaca brief dari `HEAD`. | Pelaksana tidak boleh menulis ulang kontrak yang menilai dirinya. `symbol_map --anchor` ikut aman karena Anchor tidak dapat berubah tanpa FAIL di sini. |
| H5 | `done_sha` menerima transisi `DONE` tanpa kode bila commit ber-`commit_message` brief (`landed_sha`) sudah mendarat dan membawa kode. | Koreksi resmi `lifecycle-recovery.md` bagian 3 adalah commit brief saja; bukti kodenya ada di commit unit. |
| H14 | MERAH tanpa satu tanda galat pun memakai ekor log ternormalisasi (10 baris tak kosong terakhir) sebagai tanda; `ERROR_LINE` ditambah pola diagnostik `berkas:baris[:kolom]:`. Exit 126/127 (perintah tidak dapat dijalankan) selalu dihitung minimal 1 galat baru. | "Tidak ada tanda" bukan "tidak ada galat baru". |
| H15 | `TIMEOUT` tetap merah (fail-closed), tetapi baseline `TIMEOUT` → ukur ulang baseline sekali dengan `--timeout` 3× `--force`; penutup `TIMEOUT` dengan baseline `TIMEOUT` → ulangi sekali dengan `--timeout` 3×, lalu eskalasi ke user. | Jalan keluar tertulis, bukan pelonggaran vonis. |
| H17 | `approval_verdict`: `BRD.md`/`PRD.md` `APPROVED` sah hanya bila ter-track, bersih (index dan worktree), dan commit terakhir yang menyentuhnya bersubjek `docs(spec): approve <BRD\|PRD> <slug>`. Ditagih prasyarat `system-analysis` (BRD) dan `plan` jalur `PRD` (PRD). | Pola yang sama dengan `ticket_source_verdict` tiket tanpa segel; `approved_seal` penuh tidak dipakai karena commit approve sudah menjadi satu-satunya jalur tulis `APPROVED` (chain-rules bagian 4 butir 5). |
| H26 | Taskdir tanpa ledger `## Chain` (lane `DEFECT_RCA`, backfill `EXEC_BRIEF`) yang kembali membawa brief `BLOCKED`, `HALT.md`, atau `P1` tidak dirutekan ke lane `PLANNING`: `RCA.md` `ROOT_CAUSE_CONFIRMED` ada → `backend:plan` `entry_mode: RCA` + `reentry_reason` (`--write-matrix --append`); tidak ada → `backend:debug` lebih dulu. Prasyarat analyst check 7 FAIL atas taskdir tanpa ledger. | `analyst` tidak punya hop untuk dibuka; jalur `RCA` sudah satu-satunya rute gerbang → `plan`. |
| H27 | `--bump reject:<HOP>` dan `--bump oq_return:<HOP>` menolkan `review_round:<HOP>` di tulisan yang sama; `tampered()` menerima penurunan itu. Generasi ronde brief `plan` ikut memuat nilai `reentry` `## Counters`, sehingga hop `BRIEF` yang dibuka ulang mendapat jatah ronde baru (plafon keras taskdir 4 tetap). | Revisi yang diminta user/analyst sah mendapat review baru; loopnya tetap dibatasi plafon `reject`/`oq_return`/`reentry`. |
| H28 | "Klasifikasi ulang dari awal" = gerbang menghentikan rantai dan bertanya ke user (`AskUserQuestion`): **rumuskan ulang di taskdir baru** (pengecualian tabel bagian 1; taskdir lama dibiarkan sebagai riwayat dan tidak dirutekan lagi kecuali user memintanya) atau **hentikan**. | Plafon ada untuk menghentikan loop, bukan untuk menciptakan loop baru di gerbang. |
| H29 | `detect.py` menormalkan nilai `plugin` nama tampilan (`backend`/`frontend`) ke kunci kanonik (`backenddev`/`frontenddev`) di `owner_of` dan `_grade`; template menulis `"backenddev"`. | Satu nilai, satu vonis di hook dan skrip. |
| H30 | `AUDIT_SWEEP` berjalan di `base_branch` tanpa branch baru (laporan temuan di-commit di base, sehingga taskdir perbaikan yang bercabang dari base memuat `finding_source`); `API_DOCS` tetap di branch aktif (mode `POST_CHAIN` menilai branch rantai). Keduanya tanpa taskdir. | Artefak keduanya bukan kode; branch baru dari base memutus rujukan hilir. |

---

## Tahap 1 — Pagar & bukti mendarat

## H1 [Tinggi] Pagar hook ditembus ekspansi shell
- [ ] Belum

`META` (`hooks/guard_bash.py:49`, sama di fe) dinilai sebelum `shlex.split`, dan `shlex` tidak mengenal ANSI-C
quoting maupun brace expansion. Probe: `git diff $'--output=<path>'` → hook exit 0 untuk implementor dan
reviewer; bash menulis berkas di luar lease. `git diff --{out,}put=<path>` lolos dengan cara yang sama.
Sebaliknya `git log -S "<T>"` dan `->` ditolak walau berada di dalam kutip. **Perbaikan:** lihat Keputusan H1.

## H2 [Tinggi] Validator dan lease membaca `## File scope` dengan aturan berbeda
- [ ] Belum

`validate_briefs.py:650` melewati baris ber-kolom < 4, `verify_scope.py:69` menerima ≥ 2. Probe: baris
`| modify | internal/payment/gateway.go | Charge |` → validator PASS (Check E/N/L buta), lease memuat path itu,
hook Edit exit 0. Heading `## File Scope` dinormalkan validator tetapi peka huruf di `verify_scope.py:60` →
validator PASS, `lease` FAIL "kosong". **Perbaikan:** lihat Keputusan H2.

## H3 [Tinggi] Implementor dapat memperluas scope dan Anchor brief-nya sendiri
- [ ] Belum

Brief ada di lease (`guard_bash.py:239`) dan `verify_scope.allowed_paths` membaca scope dari brief versi
sesudah commit (`verify_scope.py:115`). Probe: sunting simbol di luar Anchor, lalu ubah kolom Anchor brief →
`verify_scope` PASS, `symbol_map` exit 0. Tambah baris `| modify | src/important.go |` di brief yang sama →
`PASS scope HEAD: 2 berkas`. **Perbaikan:** lihat Keputusan H3.

## H4 [Sedang] Rename, merge, dan path non-ASCII di `verify_scope`
- [ ] Belum

`git show --name-only` tanpa `--no-renames` hanya menampilkan path tujuan: `git mv src/important.go src/new.go`
(tujuan di scope) → PASS walau sumbernya di luar scope. Commit merge → `0 berkas` PASS. Tanpa `-z`, `src/café.go`
tampil sebagai `"src/caf\303\251.go"` → FAIL palsu → HALT SCOPE. **Perbaikan:** `--no-renames -z`, merge → exit 2.

## H5 [Tinggi] Koreksi status resmi berujung jalan buntu
- [ ] Belum

`done_sha` (`brief_status.py:184`) menolak transisi `DONE` yang hanya menyentuh `backenddev/`, padahal koreksi
`READY → DONE` (`lifecycle-recovery.md:172`) memang commit brief saja. Probe: sesi 1 `KOREKSI:01:<sha>` → sesi 2
FAIL "Brief DONE tanpa commit transisi". Mengembalikan status ke `READY` memicu `KOREKSI` lagi. **Perbaikan:**
lihat Keputusan H5.

## H6 [Tinggi] `commit_message` ganda membuat brief dilompati
- [ ] Belum

Dua brief `implement stock-index` lolos (`scaffold_brief.py:309` tidak menagih `unit` unik; Check S hanya regex).
Sesudah brief-01 mendarat, `landed_sha` brief-02 menemukan commit yang sama → `KOREKSI:02` → brief-02 `DONE` tanpa
pernah dikerjakan. **Perbaikan:** Check C menagih `commit_message` unik (sesudah `norm_subject`) antar-brief hidup;
`validate_spec` menagih `unit` unik.

## H7 [Tinggi] NN ganda dan brief basi di luar matriks lolos lalu dieksekusi
- [ ] Belum

`by_nn` (`validate_briefs.py:1333`) menelan duplikat; `scaffold` hanya menolak path yang sama. Matriks ditulis
ulang dengan unit 02 berganti nama → `brief-02-order-guard.md` + `brief-02-order-lock.md`, validator PASS,
architect memberi `FASE_3:02` dua kali. **Perbaikan:** Check C dan architect check 3 FAIL untuk NN ganda; Check C
menolak brief `READY` yang tidak ada di matriks laci (bila matriks ada); `scaffold` menolak NN yang sudah
dipakai berkas ber-unit lain.

## Tahap 2 — Validator plan & skrip rantai

## H8 [Sedang] DDL destruktif lolos Check K/J
- [ ] Belum

Check K hanya membaca `## Migration` (`validate_briefs.py:1240`); Check J menerima kata prosa "update" sebagai
DDL (`:1645`, IGNORECASE). Probe: `ALTER TABLE stock DROP COLUMN` di `## Steps`, `risk: MINOR` → K dan J PASS.
**Perbaikan:** K menyapu `## Migration` + `## Steps`; J menagih DDL berbentuk pernyataan
(`CREATE|ALTER|DROP <objek>`, `INSERT INTO`, `UPDATE <t> SET`).

## H9 [Sedang] State ronde review brief rusak
- [ ] Belum

JSON terpotong dibaca `{}` → plafon reset diam-diam; JSON sah berbentuk salah (`[]`, `null`, `"total_rounds":"dua"`)
→ traceback; `--record-round` tanpa ronde terbuka mencatat 3/2 dengan exit 0 (`validate_briefs.py:334–440`).
**Perbaikan:** state rusak → FAIL terbaca (hapus berkas laci hanya lewat keputusan user); tulis atomik;
`--record-round` menagih ronde terbuka dan plafon.

## H10 [Sedang] `File scope` lintas brief tidak dimodelkan
- [ ] Belum

Brief-02 `modify` berkas yang di-`create` brief-01 → FAIL palsu "tidak ada di disk" (`:1071`), padahal slicing
bagian 3B membolehkannya. Dua brief `create` path yang sama → PASS. **Perbaikan:** berkas `create` brief hidup
ber-NN lebih kecil dihitung ada (anchor dicari di `## Steps`/`## Interfaces` brief pembuatnya); `create` ganda
FAIL; anchor sama pada berkas sama di dua brief `READY` → WARN (aturan 3B ambigu untuk simbol kelas).

## H11 [Sedang] `symbol_map`: hunk campuran dan crash berkode 1
- [ ] Belum

Hunk yang menghapus sekaligus menambah hanya dipetakan di sisi baru (`symbol_map.py:158`): hapus `Bar` + ubah `Baz`
(anchor `Baz`) → PASS. Berkas Latin-1 → `UnicodeDecodeError`, exit 1 — sama dengan kode "outside_anchor".
**Perbaikan:** petakan kedua sisi; decode `errors="replace"`; galat tak terduga → `DEGRADED` exit 2.

## H12 [Rendah] Check S dan `commit_template` tidak sepakat dengan scaffold
- [ ] Belum

Check S memakai `.upper()` (`:841`), menyimpang dari 05-2: `status: ready` PASS padahal architect FAIL. Pola
`ticket` `[A-Z][A-Z0-9]+-\d+` menolak `#482`, `482`, `oms-412` yang dirender scaffold; `domain` `Order` dirender
lalu ditolak. Template `"{subject} }"` → `ValueError` di `render`; template multi-baris merusak frontmatter.
**Perbaikan:** status dibanding persis; `scaffold` memvalidasi `domain`/`ticket` dengan pola slot yang sama;
pola `ticket` menerima satu token tanpa spasi (`#482`, `OMS-412`, `oms-412`); `commit_template()` menolak kurawal
liar dan baris baru.

## H13 [Sedang] `--bump` tidak menilai riwayat (regresi 09 E20)
- [ ] Belum

`--check` menangkap tabel yang diturunkan tangan, tetapi tidak ada SKILL yang memanggilnya; `--bump`
(`chain_counters.py:172`) dan analyst check 7 (`check_preconditions.py:386`) tidak. Probe: bump ke-3 FAIL → nilai
diubah 2→0 → `--bump` PASS 1/2. **Perbaikan:** `--bump`/`--reset-hop` menjalankan `tampered()` lebih dulu;
analyst check 7 FAIL atas tabel yang diturunkan tangan.

## Tahap 3 — Verifikasi penutup

## H14 [Tinggi] Verifikasi hijau palsu
- [ ] Belum

`ERROR_LINE` (`run_verification.py:25`) tidak mengenal diagnostik Go (`a.go:2:23: undefined: x`), sehingga
MERAH→MERAH bertanda kosong memberi `baru=0` (`:82`). Probe Go nyata: baseline MERAH `galat=0`, brief menambah
`undefined: brokenY` → `VERDICT: HIJAU`. `./mvnw: not found` (exit 127) di kedua sisi → PASS walau test tak pernah
jalan. **Perbaikan:** lihat Keputusan H14.

## H15 [Sedang] `TIMEOUT` di baseline membuat penutup tak pernah bisa tutup
- [ ] Belum

`TIMEOUT` → `TIMEOUT` = MERAH (`:149`), sementara architect 3a menyatakan TIMEOUT di merge-base bukan alasan
berhenti dan SKILL tidak pernah meneruskan `--timeout`. **Perbaikan:** lihat Keputusan H15; ringkasan penutup
menandai `TIMEOUT (baseline juga TIMEOUT)`.

## H16 [Rendah] Masukan rusak ke `run_verification` berakhir traceback
- [ ] Belum

`--cmd 'a/b=…'` → `FileNotFoundError` (nama log memuat `/`); baseline JSON berupa list → `AttributeError`.
**Perbaikan:** nama perintah `[A-Za-z0-9_-]+`; baseline bukan objek = baseline rusak.

## Tahap 4 — Prasyarat & gerbang dokumen

## H17 [Tinggi] Approval BRD/PRD tidak terikat isi
- [ ] Belum

Check 1 `system-analysis` (`check_preconditions.py:151`) dan check 3 `plan` (`:221–246`) hanya membaca
`status: APPROVED`. Probe: BRD APPROVED ditulis tangan tanpa commit (`?? BRD.md`), atau BR disunting sesudah commit
approve → PASS. **Perbaikan:** lihat Keputusan H17.

## H18 [Sedang] `--chain` system-analysis menimpa chain `TASK.md` tanpa dibandingkan
- [ ] Belum

`TASK.md` `chain: BRD_PRD_BRIEF`, BRD belum ada, `--chain PRD_BRIEF` → PASS 8/8, hop BRD terlewati
(`check_preconditions.py:58–72`). Kunci `chain` ganda diabaikan selama `--chain` diisi. business-analysis sudah
menolak ketidakcocokan ini di check 7. **Perbaikan:** tagih kesamaan parameter dengan frontmatter; galat
frontmatter tetap dilaporkan.

## H19 [Sedang] business-analysis dan system-analysis tidak menjaga tree kotor
- [ ] Belum

`business-analysis/SKILL.md:112` menjanjikan "Tree kotor: bersihkan", tetapi check 5 hanya `rev-parse`. Probe:
`M  src/order.go` ter-stage → PASS 8/8, commit `docs(spec): draft BRD` ikut membawa `src/order.go`.
**Perbaikan:** `dirty_paths()` di luar taskdir → FAIL, seperti check 5 `task`.

## H20 [Sedang] Akar `DEFECT_RCA` di-commit sebelum branch diisolasi
- [ ] Belum

`tech-lead/SKILL.md` Fase 3 memanggil `task` (commit `TASK.md`) di butir 1, baru mencabangkan branch di butir 2.
Probe: HEAD di `feat/other-chain` → akar mendarat di branch lain; HEAD di base → akar mendarat di base.
**Perbaikan:** tukar urutan (isolasi branch sebelum `task`); prasyarat `task` menagih HEAD attached dan ≠ base
(`check_base_branch`).

## H21 [Sedang] Crash tanpa JSON saat `--root` tidak ada atau git tidak ada di PATH
- [ ] Belum

tech-lead hanya menangkap `CalledProcessError` (`:152–158`); `cli()` hanya `UnicodeDecodeError`. Probe:
`--root /nonexistent --json` → rc=1, stdout kosong, `FileNotFoundError`. **Perbaikan:** `cli()` menangkap
`OSError` sebagai FAIL terbaca; tech-lead menangkap `OSError` di check 2.

## H22 [Sedang] `index.json` bertipe salah → traceback
- [ ] Belum

`load_profile_index` (`precondition_lib.py:687`) hanya menagih `str(v)` tidak kosong: `"source_root": ["src"]`
lolos lalu `TypeError`/`AttributeError` di lima skrip. **Perbaikan:** kunci wajib bertipe string.

## H23 [Sedang] `validate_doc` PRD melewati cakupan BR/EC dari teks bebas
- [ ] Belum

`no_brd` diturunkan dari "tidak ada" di `source_brd` (`validate_doc.py:470`), termasuk slot template yang belum
diisi. Probe: `BRD.md` ada, BR-3 tak tercakup → PASS 10/10. **Perbaikan:** keberadaan `BRD.md` yang memutuskan;
`source_brd` "tidak ada" padahal `BRD.md` ada → FAIL.

## H24 [Rendah] `migrate_profile.py` tidak dapat dilanjutkan bila terputus
- [ ] Belum

`index.json` dipindah paling awal (`PROFILE_FILES[0]`); terputus sesudahnya → ulang = "tidak ada profil lama",
prasyarat memilih REFRESH, `anti-patterns.md` lama terabaikan. JSON sukses tanpa kunci `status`.
**Perbaikan:** `index.json` dipindah terakhir; JSON sukses `"status": "PASS"`.

## H25 [Rendah] `set_frontmatter` tidak sepakat dengan `split_frontmatter`
- [ ] Belum

`status : BLOCKED` (spasi sebelum titik dua) terbaca `split_frontmatter` tetapi tidak ditimpa `set_frontmatter`
→ kunci ganda → brief `UNKNOWN`; pagar `--- ` (spasi di ujung) → `ValueError`. Dubious ownership git dilaporkan
tech-lead sebagai "HEAD detached". **Perbaikan:** pola kunci `^key\s*:`, pagar boleh berspasi ujung; pesan
`safe.directory` terpisah.

## Tahap 5 — Orkestrasi

## H26 [Tinggi] Taskdir tanpa ledger bolak-balik antara analyst dan gerbang
- [ ] Belum

`tech-lead/SKILL.md:76,91` merutekan `BLOCKED`/`HALT.md`/`P1` ke lane `PLANNING` → analyst; taskdir `DEFECT_RCA`
dan backfill `EXEC_BRIEF` tidak punya `## Chain` (`task/SKILL.md:25`), dan analyst check 7 hanya berkata "laporkan
ke gerbang" (PASS 7/7). **Perbaikan:** lihat Keputusan H26.

## H27 [Tinggi] Plafon ronde reviewer tidak di-reset saat hop dikembalikan
- [ ] Belum

`analyst/SKILL.md` Fase 4 butir 2 dan 5 mengulang Fase 3 pada hop yang sama; `review_round:<HOP>` hanya dinolkan
`--reset-hop` pada re-entry. Probe: ronde 1 Issues Found, ronde 2 Approved, user menolak → revisi →
`review_round:BRD 3/2 FAIL`. Hop `BRIEF` yang dibuka re-entry tetap satu generasi ronde (himpunan nama brief sama).
**Perbaikan:** lihat Keputusan H27.

## H28 [Tinggi] Plafon habis = jalan buntu
- [ ] Belum

analyst Failure path 5, 8, 9 meminta gerbang "mengklasifikasi ulang dari awal"; gerbang melarang taskdir baru
(`tech-lead/SKILL.md` Failure path 7, `gate-lifecycle.md` bagian 1) dan counter tidak pernah turun. P1 berikutnya
berputar tanpa akhir. **Perbaikan:** lihat Keputusan H28.

## H29 [Sedang] Nilai `plugin` profil: satu nilai, dua vonis
- [ ] Belum

`profile-template.md:48` berbunyi "`plugin` selalu `\"backend\"`" (sisa rename fd08fc8) sementara contoh `:35`
`"backenddev"`. `detect._grade` membandingkan nilai mentah dengan `backenddev` → `OTHER_OWNER` → hook tiap sesi
menyuntik "Profil BELUM ADA", sedangkan `owner_of` (dipakai prasyarat) jatuh ke keanggotaan `stack` → milik
sendiri. **Perbaikan:** lihat Keputusan H29.

## H30 [Sedang] `AUDIT_SWEEP` dan `API_DOCS` dicabangkan dari base
- [ ] Belum

Laporan audit ter-commit di branch audit; taskdir perbaikan bercabang dari base, sehingga `finding_source` tidak
ada saat `plan` memverifikasi ulang dan penanda `FIXED` tidak punya sasaran. `document-api` mode `POST_CHAIN` di
branch baru menilai diff kosong. **Perbaikan:** lihat Keputusan H30.

## H31 [Sedang] Instruksi agent bertabrakan dengan hook
- [ ] Belum

(a) Pengingat atribusi harness mendorong trailer `Co-Authored-By … <…>` (newline, `<`, `>`), yang ditolak hook;
`code-implementor.md:21` memperlakukan penolakan hook sebagai blocker. (b) `code-reviewer.md:34` menyuruh
`$(git merge-base …)..HEAD` yang ditolak hook. (c) `code-implementor.md:24` "Nomor migrasi bentrok → ambil nomor
berikutnya" menulis di luar lease. **Perbaikan:** pesan commit persis `commit_message`, satu `-m`, tanpa
trailer/heredoc; penolakan hook atas **bentuk** perintah boleh diulang sekali dalam bentuk polos; reviewer memakai
SHA merge-base dari gerbang masuk butir 5; migrasi bentrok → `BLOCKED`.

## H32 [Rendah] `EXPLORE_FACT` tanpa profil membuang dua dispatch
- [ ] Belum

`code-explorer.md:45` berhenti pada profil absen, padahal gerbang menjawab baca-kode tanpa profil lewat jalur
terdegradasi. **Perbaikan:** explorer lanjut dari root repo dengan caveat `tanpa profil` dan plafon `confidence`
`medium`.

## H33 [Rendah] `code-reviewer` tanpa tool `Edit`
- [ ] Belum

Menambah satu baris riwayat `backenddev/issues/README.md` menuntut penulisan ulang penuh lewat `Write`.
Hook sudah mengizinkan `Edit` reviewer atas kedua path. **Perbaikan:** tambah `Edit` ke `tools`.

## H34 [Rendah] Guardrail analyst memvonis commit sahnya sendiri sebagai pelanggaran
- [ ] Belum

`analyst/SKILL.md:153` menuntut commit terakhir BRD/PRD/brief berformat pesan penulis, padahal commit terakhir
BRD/PRD adalah `docs(spec): approve …` milik analyst sendiri, dan brief `DONE` milik implementor. Slot
`Catatan Rantai` tidak ada di Output. **Perbaikan:** daftar subjek sah per berkas; slot `Catatan`.

## H35 [Rendah] Path relatif `skills/_common/validate_doc.py` di rujukan
- [ ] Belum

`gate-lifecycle.md:37,109` dan `chain-rules.md:137` menyuruh menjalankan path relatif; `tech-lead/SKILL.md` tidak
memuat perintah absolutnya. **Perbaikan:** perintah `${CLAUDE_PLUGIN_ROOT}` di SKILL.md; rujukan menunjuk ke sana.

## H36 [Rendah] `detect.py` diam saat `gate_text.render` gagal; README tertinggal
- [ ] Belum

`render()` dipanggil di luar `try` (`detect.py:482`): traceback exit 1 = gerbang hilang tanpa pesan. README
"Keterbatasan" masih menyebut `commit_message` tidak menghormati konvensi profil (sudah `commit_template`, 08b B13).
**Perbaikan:** `render` masuk jaring yang sama; README diselaraskan dengan H1–H35.
