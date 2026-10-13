# frontend

Plugin Claude Code untuk kerja frontend lintas-stack — React + Vite SPA, React Native/Expo, SvelteKit,
dan Svelte + Vite. Sepuluh skill dan lima subagent, dengan tiga aturan yang menyetir seluruh bentuknya:
**keputusan ditulis ke file**, **repo dibaca sekali, di tempat yang hasilnya masih terpakai**, dan
**yang dapat divonis mesin divonis skrip, bukan diingat model.**

Plugin ini sengaja generic — ia tidak tahu apa-apa tentang brand token, komponen, atau konvensi repo
tempat dijalankan, dan tidak tahu stack mana yang dipakai sampai profil menyebutnya. Pengetahuan
spesifik-repo hidup di `.claude/profile/frontenddev/`, disiapkan sekali lewat skill `profile`; pengetahuan
spesifik-stack hidup di satu adapter `skills/profile/stacks/<stack-id>.md` yang dipilih dari field
`stack` `index.json` profil itu. Next.js sengaja di luar cakupan.

## Ten Skills

| Skill | Peran | Menulis | Dikunci oleh |
|---|---|---|---|
| `frontend:lead` | gerbang tiap permintaan: lane, sections, taskdir, pemulihan, eskalasi | — | — |
| `frontend:profile` | prasyarat sekali per repo | `.claude/profile/frontenddev/` | — |
| `frontend:task` | akar tiap taskdir | `TASK.md` + ledger `## Chain` | `chain.py root` |
| `frontend:ux-design` | Gate Flow | `FLOW.md` | `chain.py approve --row FLOW` |
| `frontend:ui-design` | Gate Design | `UI.md` | `chain.py approve --row UI` |
| `frontend:contract` | Gate Contract (+ `contract-reviewer`) | `CONTRACT.md` | `chain.py approve --row CONTRACT` |
| `frontend:plan` | Gate Breakdown (+ `doc-reviewer`) | `brief-<NN>-<unit>.md`, `REVIEW-PLAN.md` | `chain.py approve --row BRIEF` |
| `frontend:architect` | eksekusi sekuensial, verifikasi penutup, review tunggal | status brief, `REVIEW.md` (ditulis `code-reviewer`) | commit kode unit; `validate_review.py` |
| `frontend:report` | laporan penutup | `REPORT.md` | `validate_report.py` — penanda tuntas |
| `frontend:review` | review ad-hoc di luar rantai aktif | chat, atau `frontenddev/reviews/<berkas>.md` | commit bila `--write` |

Hanya `lead`, `profile`, dan `review` yang muncul di menu `/`. Tujuh lainnya ber-`user-invocable: false`:
model tetap memanggilnya lewat tool Skill, tetapi mengetik `/frontend:plan` tidak menjalankan apa pun.
Untuk memulai, melanjutkan, atau memulihkan rantai, termasuk yang terputus di tengah eksekusi, panggil
`/frontend:lead`, yang merutekan ke gate pemiliknya.

Kesepuluhnya jalan **di main loop**. Penelusuran, penilaian dokumen, penulisan kode, dan penilaian diff
duduk di `agents/*.md` — tiap subagent mandiri, didispatch langsung lewat template prompt di
`skills/<skill>/dispatcher/`, tanpa skill pembungkus.

`ux-design`, `ui-design`, dan `contract` dipisah karena tiap domain butuh budget pertanyaan dan budget
bacanya sendiri. `plan` dan `architect` dipisah karena aturannya berbeda jenis: yang pertama
menerjemahkan dan boleh berhenti bertanya, yang kedua menjalankan dan tidak memutuskan apa pun.

## Five Subagents

| Agent | Boleh menulis | Didispatch |
|---|---|---|
| `code-explorer` | laci `.explore/` / `.frontenddev/explore/` (scratch, gitignored) | `lead`, `ux-design`, `ui-design`, `contract`, `plan` |
| `contract-reviewer` | — (read-only) | `contract` lewat `contract/dispatcher/reviewer.md` |
| `doc-reviewer` | `<taskdir>/REVIEW-PLAN.md` | `plan` lewat `plan/dispatcher/reviewer.md` |
| `code-implementor` | `src/**` dalam `files_touched` + `<taskdir>/report-<NN>.md` | `architect` lewat `architect/dispatcher/implementor.md` |
| `code-reviewer` | `<taskdir>/REVIEW.md` (+ baris `> Status:` berkas temuan asal) | `architect` lewat `architect/dispatcher/reviewer.md` |

Subagent menghemat **context window**, bukan token, dan tiap dispatch membayar penuh. Lima yang ada
menanggung ongkos itu demi alasan yang dapat disebut:

- `code-explorer` — **menahan token**: jejak grep dan kandidat yang salah mati di context-nya; yang
  kembali hanya ringkasan plus path laporan.
- `contract-reviewer`, `doc-reviewer`, `code-reviewer` — **independensi**: penilai yang duduk di
  context penulisnya menilai ingatannya sendiri, bukan dokumennya. Context terpisah memaksanya membuka
  tiap jangkar dari disk.
- `code-implementor` — **batas izin yang dapat ditegakkan**: brief menyebut `files_touched` dan
  `Anchor`, dan pelanggarannya ketahuan di perbatasan agent lewat matriks bukti disk, bukan sesudah
  kerjanya bercampur dengan kerja user.

Kolom "Boleh menulis" di atas ditegakkan hook `hooks/guard_bash.py`, bukan hanya prosa (lihat Mechanical
Enforcement): `code-reviewer`, `code-explorer`, dan `doc-reviewer` dipagar ke berkas tulisnya, dan
`code-implementor` ditolak menulis di luar repo, di `.git/`, atau pada path ter-ignore — tempat yang tidak
terlihat matriks bukti disk.

## Workflow

```
permintaan ──► lead ──┬─► profile ─────────────► .claude/profile/frontenddev/
                      ├─► explore ─────────────► jawaban, berhenti
                      ├─► review (ad-hoc) ─────► laporan / frontenddev/reviews/, berhenti
                      │
                      └─► task ──► TASK.md + ## Chain ──► chain.py root
                            │
                            ├─► ux-design  → FLOW.md DRAFT → chain.py draft → AskUserQuestion → chain.py approve FLOW
                            ├─► ui-design  → UI.md DRAFT   → chain.py draft → AskUserQuestion → chain.py approve UI
                            ├─► contract   → CONTRACT.md DRAFT → validate_doc → contract-reviewer (≤2 ronde)
                            │                → chain.py draft → AskUserQuestion → chain.py approve CONTRACT
                            ├─► plan       → brief READY × N → validate_briefs → doc-reviewer (≤2 ronde)
                            │                → chain.py draft → AskUserQuestion → chain.py approve BRIEF
                            └─► architect  → per unit: ingest → code-implementor → report-NN.md
                                             → matriks bukti disk → commit unit (+ gerbang kompilasi)
                                           → verifikasi penutup sekali → code-reviewer → validate_review
                                           → REVIEW.md (validate_review) → report → REPORT.md (tuntas)
```

Gate bersifat **kondisional** menurut `sections` `TASK.md`: `flow` menjadwalkan Gate Flow, `ui` Gate
Design, `sections` non-kosong Gate Contract, dan Gate Breakdown selalu. Lane `HOTFIX_MINOR` punya
`sections` kosong — satu gate saja, tanpa kontrak dan tanpa Plan Review.

Tiap loop berplafon (ronde reviewer, revisi user, re-entry, eskalasi; lihat
`skills/lead/references/lane-routing-matrix.md` bagian 5). Bila plafon habis, rantai berhenti dan `lead`
menanyakan user lewat `AskUserQuestion`: **rumuskan ulang di taskdir baru** (`chain.py abandon` taskdir
lama) atau **hentikan**. Tidak ada jalan pintas yang me-reset plafon — amandemen akar dan `draft` ulang
pun tidak.

## The Ledger

`TASK.md` memuat ledger `## Chain`, satu baris per hop yang dijadwalkan `sections`, ditulis
`chain.py init`:

```markdown
## Chain

- [x] FLOW     — frontend:ux-design → FLOW.md @ APPROVED 3f9c2ab1d0e4
- [x] UI       — frontend:ui-design → UI.md @ APPROVED 8e01d7a5c3f9
- [~] CONTRACT — frontend:contract  → CONTRACT.md @ re-entry 1 (was 7d1e0c4a92b1)
- [ ] BRIEF    — frontend:plan      → brief-*.md
```

`skills/_common/chain.py` adalah **satu-satunya penulis** ledger, `## Riwayat Rantai`, `base_commit`, status
`APPROVED`, `lane`, dan `sections`. Riwayat adalah seksi terakhir `TASK.md`: satu baris bernomor per kejadian
(`akar`, `draft`, `approve`, `reopen`, `eskalasi`, `amandemen`, `abandon`), pengganti subjek dan badan commit
dokumen sejak dokumen taskdir lepas dari git (Langkah 24). Plafon, epoch ronde, dan materai approve dibaca
darinya; Riwayat yang tak terurai atau bernomor loncat membuat semua gerbang `FAIL`.

| Subperintah | Dipakai | Yang ditegakkan |
|---|---|---|
| `init` | `task` | baris ledger persis jadwal `sections` |
| `root` | `task` | akar sah (`validate_task.py`), `frontenddev/docs/` tidak ter-track; menulis `base_commit` = `HEAD` dan kejadian `akar` beserta sidik akar |
| `amend --reason` | `lead` | amandemen akar sah (`validate_task.py --amend`); kejadian `amandemen` bersidik akar baru. Suntingan akar di luar `amend`/`escalate` → `FAIL` di check akar tiap gate |
| `draft --row R` | gate pemilik hop | validator `PASS`; CONTRACT dan BRIEF non-MINOR: ronde reviewer terakhir `PASS` atas konten itu; konten berbeda dari draft terakhir; plafon 2 revisi. Kejadian `draft` membawa sidik konten dan field `review` |
| `approve --row R --answer "<jawaban>"` | gate pemilik hop | akar `ACTIVE` dan utuh; `--answer` satu baris; hop hulu sah; dokumen `DRAFT` yang kontennya sama dengan draft terakhir yang dicatat; validator `PASS`; untuk CONTRACT/BRIEF ronde reviewer terakhir `PASS` atas konten final **tanpa `reopen` hop itu atau hop di atasnya, maupun `escalate`, sesudah ronde itu** (BRIEF di hop `[~]` tanpa brief `READY` baru sah tanpa ronde baru; brief `DONE`/`BLOCKED` tidak boleh berubah sejak reopen). Menulis `APPROVED` + centang `@ <sidik12>` dan kejadian `approve <R>` yang memateraikan sidik konten (tanpa `status:`), ronde reviewer, sidik `SC-{n}`, dan jawaban user; BRIEF juga menulis `sidik_kontrak` ke tiap brief `READY` |
| `reopen --row R --reason` | `lead` | akar `ACTIVE` dan utuh; kaskade: R dan seluruh hop tercentang di bawahnya jadi `[~]`, dokumen FLOW/UI/CONTRACT-nya kembali `DRAFT`; seluruh kaskade divalidasi sebelum ada yang ditulis; kejadian `reopen` mencatat status dan sidik tiap brief saat itu; plafon 3 per hop (dihitung saat hop itu target), 6 per taskdir |
| `escalate --lane L --sections S` | `lead` | akar `ACTIVE`; lane hanya naik, sections hanya bertambah, hop tercentang di bawah hop baru wajib di-`reopen` dulu; plafon 2 |
| `abandon --reason` | `lead` | `TASK.md` `status: ABANDONED` atas keputusan user; taskdir keluar dari pemindaian (`DITUTUP`) |
| `files` | `code-reviewer`, `report` | berkas rantai: commit kode bersubjek `<type>(<slug>):` sejak `base_commit` |
| `revisions --row R` | gate pemilik hop | plafon 2 revisi berturut sejak kejadian `draft` **pertama** sesudah reopen/approve — `draft` berikutnya dihitung revisi, amandemen akar tidak me-reset |
| `verify` / `status` | siapa pun | tiap `[x]` berjangkar pada **kejadian `approve`** hop itu di Riwayat (terbaru sesudah reopen terakhirnya): sidik ledger = `sidik` kejadian; `review` PASS atas konten yang sama untuk hop yang direview; dokumen `APPROVED`; **konten identik dengan sidik itu kecuali baris `status:`**; brief per berkas dengan transisi status yang sah; `SC-{n}` akar tidak berubah sejak approval. Centang tanpa kejadian `approve` → FAIL dengan remedi reopen + approve ulang; validator tidak dijalankan ulang atas approval lama |

Sidik yang dicentang adalah sidik **konten** yang disetujui user. Karena itu setiap skrip prasyarat hilir
dapat membuktikan bahwa yang dikerjakan adalah yang disetujui: suntingan `CONTRACT.md` sesudah approval
tanpa `reopen` gagal di `plan`, `architect`, dan `report` sebagai drift. Batasnya dinyatakan apa adanya:
skrip tidak dapat membuktikan `AskUserQuestion` benar-benar terjadi — yang dijaminnya jejak, karena
approval tanpa jawaban (atau dengan jawaban bernewline yang dapat menyisipkan kejadian palsu) ditolak dan
jawabannya dimateraikan di kejadian `approve`. Batas kedua: model di runtime yang sama dapat menulis ulang
Riwayat itu sendiri — yang dijamin, suntingan dokumen yang tidak lewat skrip terdeteksi sebagai drift.
Rantai yang sudah `TUNTAS` dinilai sebelum ledger, jadi squash-merge sesudah laporan tidak mengubahnya
menjadi `PENUTUP`.

## Mechanical Enforcement

Tiap skill kecuali `lead` punya `skills/<skill>/scripts/check_preconditions.py` yang dijalankan sebelum Phase 0 (`lead` memakai `skills/lead/scripts/taskdir_state.py`); primitif bersamanya
di `skills/_common/precondition_lib.py`, supaya satu artefak tidak pernah divonis berbeda oleh dua gate.
Di atasnya tujuh penjaga — enam validator dan satu hook:

| Penjaga | Menagih |
|---|---|
| `_common/validate_doc.py --kind flow\|ui\|contract` | frontmatter, heading persis template, ID `DD`/`ST`/`AC` berurutan, nol placeholder; untuk CONTRACT **keterlacakan dua arah** — tiap token `Sumber` AC nyata, dan tiap `SC` akar, `DD` FLOW, `ST` UI dipikul minimal satu AC |
| `plan/scripts/validate_briefs.py` | 16 check S N D L T F B R V K O E C P G M — termasuk **G** (tiap `SC` dipikul brief `READY`/`DONE` lewat `fulfills`; brief `BLOCKED` tidak memikul apa pun, begitu pula di C dan E), **D** (DAG satu arah; remedi yang bergantung pada unit asalnya — rantai buntu — ditolak), **V** (operator shell hanya bila perintah sama persis dengan perintah profil), dan **M** (remedi menunjuk brief `BLOCKED`; brief `READY` yang beririsan dengan brief `BLOCKED` belum ter-remedi wajib `remedies`; plafon 2 per unit asal, +1 per re-entry kontrak sesudah `BLOCKED` pertama: `reopen … CONTRACT`, atau eskalasi dari `HOTFIX_MINOR`); `CREATE` ganda antar brief, `unit` ≠ NN nama berkas, dan path `../`/absolut FAIL |
| `task/scripts/validate_task.py` | struktur akar, pasangan lane/sections, `SC` ber-alat-ukur, bukti `file:baris` nyata, ledger `[ ]` (`--amend`: amandemen akar oleh `lead`, ledger boleh bercentang) |
| `architect/scripts/validate_review.py` | `taskdir`/`stack`/`reviewed_at` sah, H1 ber-slug; tiap `SC` dan `AC` `terbukti` wajib berbukti (`path:baris` berkas rantai atau perintah HIJAU; AC `test otomatis` hanya `path:baris` berkas test rantai, sehingga test yang tak pernah dibuat tidak dapat divonis `terbukti`); status 9 dimensi = severity terburuk temuan; `## Summary` dan Done Criteria DITUNDA ikut menurunkan verdict; `--log` mencocokkan verifikasi penutup dengan log mesin dan menagih `baseline_head` leluhur commit `implement unit` pertama (baseline diukur sebelum unit mana pun mendarat); hitungan temuan; `base` = `base_commit` akar `TASK.md`, `head` = `HEAD` yang dinilai (leluhur `HEAD`); **verdict diturunkan**: `BLOCKED` ⇔ P1 / SC belum terbukti / verifikasi merah (`TIMEOUT` atau galat baru > 0; `MERAH` bergalat baru 0 adalah warisan baseline) |
| `hooks/guard_bash.py` (PreToolUse) | `code-reviewer` read-only atas repo: Bash hanya git baca (`status`, `diff`, `log`, `show`, `rev-parse`, `ls-files`, `merge-base`, `blame`, `symbolic-ref` bentuk baca — pencarian lewat tool Grep), opsi global hanya `--no-pager`, tanpa ekspansi shell, glob sebelum `--`, pipe, atau pengalihan; `ls`; dan `chain.py files` plugin ini; Write hanya `REVIEW.md`; Edit hanya `REVIEW.md` dan berkas temuan `frontenddev/reviews/`. Penulis lain hanya Edit/Write: `code-explorer` hanya laci `.explore/`/`.frontenddev/explore/`, `doc-reviewer` hanya `REVIEW-PLAN.md`, `code-implementor` ditolak di luar repo, di `.git/`, atau pada path ter-ignore kecuali `report-NN.md` taskdir-nya (scope `files_touched`-nya divonis `verify_scope.py` sesudah unit). Fail-closed; main loop tidak dipagar. `validate_review.py --log` menagih tree bersih sesudah reviewer — hanya `REVIEW.md` dan `finding_source` taskdir itu (check `TREE`) |
| `report/scripts/validate_report.py` | Ringkasan ≥ 5 kata, butir ≥ 3 kata; perubahan berakar berkas rantai; temuan REVIEW `PLANNED`/`DEFERRED` disebut di Catatan; tiap SC `PERLU VERIFIKASI MANUAL` tercatat |
| `review/scripts/validate_audit.py` | berkas audit `frontenddev/reviews/`: ID `P{n}-{m}` berurutan, hitungan `p1/p2/p3`, `verdict` turunan, `> Status:` ber-enum, jangkar `file:baris`; `--only-status-changed` menolak diff `finding_source` yang menyentuh baris selain `> Status:` |

Dan dua penjaga keadaan:

- `_common/review_round.py` — plafon ronde reviewer dokumen (2 per putaran, 8 per taskdir; putaran baru
  dimulai sesudah dokumen yang lolos ronde `PASS` dicatat `chain.py draft`, atau sesudah `reopen` hop gate itu
  atau hop di atasnya, atau sesudah `escalate`) disimpan di `.explore/<gate>-review-state.json` beserta sidik
  konten, epoch, dan jumlah kejadian Riwayat tiap ronde. `open` mencetak sidik konten; reviewer menggemakannya (`- Sidik:` di balikan
  `contract-reviewer`, `sidik:` di `REVIEW-PLAN.md`) dan `record` menolak laporan ronde lain. State rusak →
  FAIL (pulihkan dari `.bak`, yang ditulis sejak `save` pertama); kejadian `draft` di Riwayat membawa field
  `review <gate> r<n> t<total> PASS`, sehingga state yang hilang terdeteksi (`rebuild` memulihkan hitungannya).
- `lead/scripts/taskdir_state.py` — memvonis keadaan tiap taskdir (`AKAR`, `GATE`, `DRIFT`,
  `EKSEKUSI`, `TERHENTI`, `PENUTUP`, `TEMUAN`, `LAPORAN`, `LAPORAN TERTUNDA`, `TUNTAS`, `DITUTUP`, `RUSAK`) beserta satu
  rute berikutnya, dari disk, ledger, dan Riwayat — bukan dari ingatan sesi. `TUNTAS` dinilai sebelum ledger dan
  berarti `REPORT.md` lolos `validate_report.py` (`LAPORAN TERTUNDA`: tertulis tetapi gagal validator);
  taskdir era git tanpa `base_commit` divonis `TUNTAS` bila ber-`REPORT.md`, selain itu `RUSAK`; repo yang
  masih men-track `frontenddev/docs/` keluar `FAIL` dengan rute `MIGRASI`;
  `TERHENTI` juga mencakup rantai buntu (`DAG`: brief `READY` ada, tak satu pun dapat berangkat); `RUSAK`
  membawa jalan keluarnya (`abandon` lalu taskdir baru, atau direktori dipindah bila tak berakar); status akar
  selain `ACTIVE`/`ABANDONED` juga `RUSAK`.

Pasangan `(lane, sections)` ditegakkan di setiap gate: `HOTFIX_MINOR` ⇔ sections kosong;
`FAST_FORWARD`/`REFACTOR_ARCH` ⇔ tepat `architecture`; `FULL_PIPELINE` memuat `flow` atau `ui`.
`lane`/`sections` yang berubah di luar akar terkunci atau `chain.py escalate` divonis `RUSAK` oleh
`taskdir_state.py` dan `FAIL` di check akar setiap gate — Riwayat di-replay sejak kejadian `akar`, dan sidik
akar menangkap suntingan `TASK.md` lain di luar `chain.py amend`. Slug unik per repo: prasyarat `task` menolak
slug yang sudah dipakai taskdir lain (`lead` menambah sufiks `-2`), karena commit rantai dikenali dari `(<slug>)`.

## Success Criteria, End to End

`SC-{n}` di `TASK.md` adalah satu-satunya ukuran selesai, dan tiap lapis hilir memikulnya secara
mekanis:

```
TASK.md SC-n ──► CONTRACT.md AC (kolom Sumber)      validate_doc.py  — tiap SC dipikul AC
             ──► brief fulfills: [SC-n]             validate_briefs  — tiap SC dipikul brief (Check G)
             ──► REVIEW.md ## Cakupan Success Criteria  validate_review — tiap SC divonis berbukti;
                                                        satu "belum terbukti" ⇒ verdict BLOCKED
             ──► REPORT.md ## Catatan               validate_report  — tiap SC manual tercatat
```

Rantai yang janji akarnya tidak mendarat tidak pernah sampai ke `report`, sebersih apa pun kodenya.

## Execution

`architect` menjalankan brief satu per satu. Tiap unit:

1. **Ingest** — `check_preconditions.py --brief NN`: brief `READY` ber-`stack` sama dengan profil,
   `depends_on` tertutup lewat commit `implement unit` yang membawa kode sejak `base_commit` (status `DONE`
   yang diketik tanpa commit itu tidak sah), `report-NN.md` belum ada, kesegaran `based_on`.
2. **Dispatch** — `code-implementor` menerapkan brief tanpa satu perintah terminal pun (tool `Bash` tidak
   tersedia) dan menulis `report-<NN>.md` — laporan yang bertahan melewati sesi. Berkas yang perlu
   dipulihkan dicatatnya di `## Rollback`; rollback-nya (`git restore --` berkas `MODIFY`, `rm --` berkas
   `CREATE`) milik `architect` di matriks bukti disk.
3. **Matriks bukti disk** — `git status` dan hunk anchor disandingkan dengan `files_touched`; laporan
   adalah klaim, disk adalah bukti. Hasilnya commit unit (status `DONE` di disk lalu commit kode saja)
   atau brief `BLOCKED` di disk.
4. **Gerbang kompilasi per-brief** — typecheck sesudah commit, hanya bila adapter `typecheck-per-brief: ya`,
   divonis relatif baseline.

Brief `BLOCKED` tidak pernah naik lagi: sisa pekerjaannya diambil brief remedi (`remedies: "NN"`) pada
taskdir yang sama lewat `reopen BRIEF` → `plan` APPEND. Remedi ketiga atas unit yang sama dilarang —
cacatnya di kontrak (`reopen CONTRACT`; di `HOTFIX_MINOR`: `reopen BRIEF` → `escalate FAST_FORWARD`).
Berkas yang tersentuh di luar union `files_touched` adalah **berkas yatim** — cacat perencanaan,
dirutekan ke kontrak, tidak pernah ditambal di brief `DONE`. `REVIEW.md` `BLOCKED` juga diperbaiki di
taskdir yang sama: `reopen BRIEF` → `plan` APPEND brief perbaikan → eksekusi → review ulang yang
menimpa `REVIEW.md`. Rantai yang ditinggalkan user ditutup `chain.py abandon`.

Baseline seluruh perintah diukur sekali sebelum unit pertama mendarat (`run_verification.py baseline`, mencatat
`head`; bila hilang sesudah unit mendarat, diukur di worktree pada `base_commit` akar). Sesudah seluruh unit tertutup:
lint, test, build, dan typecheck **sekali** lewat `bash -o pipefail`, ditulis ke `.explore/closing-verification.md`.
Galat baru = tanda galat yang tidak ada di baseline, dihitung per kemunculan. Merah tidak pernah dibiarkan
tanpa rute:

- galat baru yang menyebut berkas → brief perbaikan, atau rute kontrak bila berkasnya yatim;
- exit 126/127 → perintah profil salah: REFRESH, lalu baseline diukur ulang;
- `TIMEOUT` → ulang sekali dengan `--timeout` 3× lipat, lalu `AskUserQuestion`. Tidak ada opsi "terima
  tidak terverifikasi";
- `MERAH` tanpa berkas → ekor log disajikan ke user.

Hijau → prasyarat dijalankan ulang, sehingga jejak perintah verifikasi di tree (snapshot, coverage,
`lint --fix`) disajikan ke user sebelum reviewer berangkat. Tree bersih → `code-reviewer` menilai berkas
rantai (`chain.py files`) terhadap union `files_touched`, sembilan dimensi, CONTRACT, dan SC; `REVIEW.md`
sah hanya sesudah `validate_review.py` `PASS`, dan basi begitu commit kode mendarat sesudah `head`-nya.

## Artifacts

```
./frontenddev/
  docs/                  diabaikan git, tidak pernah di-commit (lihat di bawah)
    .gitignore           `*` — ditulis `docs_git.py`, ikut mengabaikan dirinya
    2609231200-order-checkout/
      TASK.md            akar + ledger + Riwayat → task; chain.py
      FLOW.md            perjalanan        → ux-design        (DRAFT → APPROVED)
      UI.md              bentuk layar      → ui-design        (DRAFT → APPROVED)
      CONTRACT.md        kontrak           → contract         (DRAFT → APPROVED)
      brief-01-*.md      scope satu unit   → plan             (READY → DONE | BLOCKED)
      REVIEW-PLAN.md     audit dokumen     → doc-reviewer
      report-01.md       laporan unit      → code-implementor (+ ## Triase architect)
      REVIEW.md          review penutup    → code-reviewer
      REPORT.md          laporan hasil     → report — penanda tuntas
  reviews/
    2609261000-cart-audit.md   temuan review ad-hoc → finding_source taskdir perbaikan
```

Status frontmatter:

- **`ACTIVE`** — khusus `TASK.md`; tidak pernah berubah. `lane`/`sections` hanya bergeser lewat `chain.py escalate`.
- **`DRAFT`** — FLOW/UI/CONTRACT yang ditulis penulisnya dan dicatat `chain.py draft`, menunggu keputusan user; juga keadaan dokumen yang dibuka ulang.
- **`APPROVED`** — ditulis hanya oleh `chain.py approve`.
- **`READY`** → **`DONE`** | **`BLOCKED`** — khusus brief; transisi ditulis `architect` di disk (`DONE` tepat sebelum commit kode unit).

Tiap dokumen membawa `based_on: <sha> (<tanggal>)` dan `stack: <stack-id>` — brief yang lahir untuk
`react-vite` tidak dieksekusi di profil `sveltekit`, dan brief yang berkasnya bergerak sesudah ditulis
diberi `WARN` di ingest.

## Commits

Dokumen taskdir `frontenddev/docs/**` tidak pernah di-commit: diabaikan git (penanda
`frontenddev/docs/.gitignore` tulisan prasyarat `task`) dan dicerminkan ke nataflow. Jejak yang dulu hidup di
subjek dan badan commit dokumen kini kejadian `## Riwayat Rantai` tulisan `chain.py`. Repo yang sudah
meng-commit dokumen taskdir dimigrasikan sekali lewat `skills/_common/docs_git.py migrate` sesudah persetujuan
user (`lead` Failure path 7).

Yang tetap di-commit hanya kode dan dokumen tingkat repo, selalu dengan path eksplisit — tidak pernah
`git add .`/`-A`, tidak pernah `commit -a`, tidak pernah `--no-verify`, tidak pernah push atau pindah branch.
Subjek commit kode rantai memuat `(<slug>)`; `chain.py files`, bukti `DONE`, dan ingest mengenali commit rantai
dari situ.

| Titik | Subjek | Pemilik |
|---|---|---|
| Unit | `feat(<slug>): implement unit <NN> - <nama>` (kode `files_touched` saja) | `architect` |
| Review penutup | `docs(<slug>): closing review <verdict>` (hanya bila `finding_source` berubah) | `architect` |
| Temuan asal `OBSOLETE` | `docs(review): tandai temuan OBSOLETE` | `task` |
| Audit ad-hoc | `docs(review): audit <slug>` | `review` |
| Profil | `docs: init/refresh/migrate frontend profile` · `docs: patch frontend profile (drift +<n>)` | `profile` |
| Migrasi sekali jalan | `chore: lepas frontenddev/docs dari git` | `docs_git.py migrate` |

## Sinkron nataflow (opsional)

Artefak taskdir dan dokumen repo dapat dicerminkan ke nataflow. Disk (dokumen taskdir) dan git (dokumen repo)
tetap sumber kebenaran; untuk dokumen taskdir, nataflow satu-satunya salinan di luar mesin ini. Sinkron
tidak menulis berkas, tidak meng-commit, dan tidak menjalankan `chain.py`, sehingga ledger dan materai approve
tidak tersentuh. Kegagalannya tidak menahan gate maupun eksekusi.

- **Aktif per repo** lewat `.claude/nataflow.json` (ter-commit, dibaca juga oleh `analyst`, `backend`, dan
  `quickdev`): `mcp_server` (default `nataflow-api`), `workspaces` (objek alias → UUID workspace;
  kosong → workspace milik key, satu entri → otomatis, lebih dari satu → user memilih saat task baru atau
  dokumen repo disinkron), `pic_id`, dan `repo` (default: remote `origin` ternormalisasi). Berkas absen → dilewati; ada tetapi
  rusak → `GAGAL`. Server MCP didaftarkan user di Claude Code; plugin tidak menyimpan key.
- **Jangkar**: satu taskdir = satu workdir `frontenddev:<repo>:<path taskdir>`, tertaut ke task tiket analyst
  bila `TASK.md` membawa `ticket_source` (taskdir backend dari tiket yang sama bernaung di task itu juga), atau
  ke task baru dari `TASK.md`.
- **Yang didorong** (isi disk, dipilih `skills/_common/sync_payload.py`; metadata `commit` kosong dan `head` =
  `HEAD` saat sinkron): `TASK.md` berakar terkunci; `FLOW.md`/`UI.md`/
  `CONTRACT.md` hanya bila baris ledger-nya `[x]` dan tidak DRIFT; brief dan `REVIEW-PLAN.md` sesudah hop BRIEF
  disetujui (atau brief `DONE`/`BLOCKED`); `report-NN.md`, `REVIEW.md`, `REPORT.md`. Hop yang dibuka ulang
  tercermin dengan status terbarunya; berkas taskdir yang dihapus dari disk tidak didorong ulang. `frontenddev/reviews/` dan profil didorong ke workspace.
- **Kapan** (main loop saja): `task` sesudah `chain.py root`, tiap gate sesudah `chain.py approve`, `architect` sekali
  per putaran, `report` sesudah laporan terbit, `lead` sesudah `reopen`/`escalate`/`abandon`/`amend`, serta
  `review`/`profile` sesudah commit. Prosedurnya di `skills/lead/references/nataflow-sync.md`.
- **Status**: workdir dari `taskdir_state.py` (`TUNTAS` → `done`, `DITUTUP` → `abandoned`, `TERHENTI`/`TEMUAN` →
  `blocked`). Task naik ke `in_progress` sejak eksekusi dimulai; task milik taskdir ini menjadi `done`/`cancelled`,
  sedangkan task tiket tidak ditutup plugin ini.
- **Gagal tidak memblokir**: baris penutup memuat segmen `nataflow <… | dilewati | GAGAL: <sebab>>`. Ulangi lewat
  `/frontend:lead` ("sinkron ulang taskdir <slug>").

## Stack Adapters

| `stack-id` | Cakupan | Penanda deteksi |
|---|---|---|
| `react-vite` | React SPA di atas Vite | `react` + `vite.config.*`, tanpa `next` |
| `react-native` | Expo (Expo Router / React Navigation) dan Bare CLI | `react-native` atau `expo` |
| `sveltekit` | SvelteKit dengan Svelte 5 runes | `@sveltejs/kit` |
| `svelte-vite` | Svelte SPA murni di atas Vite | `svelte` tanpa `@sveltejs/kit` |

Tiap adapter memuat tujuh seksi berjudul tetap dengan konsumen yang jelas: `## Detection` (profile,
hook), `## Commands` (profile, plan, architect), `## Layer taxonomy` (code-implementor, contract,
plan), `## Navigation recipes` (profile, review), `## Review checklist` (code-reviewer, review),
`## UI & navigation surface` (ux-design, ui-design), `## Failure signatures` (architect, code-reviewer,
review). Kontraknya di `skills/profile/stacks/_CONTRACT.md`. Skill memakai nama layer generik — DTO,
Service, API layer, View-Model, Controller, Presentation — dan adapter menerjemahkannya ke idiom stack.

## Questions Deliberately Not Asked

Tiap skill gate dibatasi **maksimal tiga pertanyaan** miliknya sendiri, diajukan lewat
`AskUserQuestion` dengan opsi konkret. Satu pertanyaan layak ditanya kalau ia **bercabang** —
jawabannya mengubah daftar berkas atau melahirkan pertanyaan berikutnya. Yang saling bebas (fallback
field nullable, kalimat empty state, urutan kolom) tidak ditanyakan: default-nya diturunkan dari fitur
sejenis dan disebut sebagai asumsi di ringkasan gate, tempat user mengoreksinya sekaligus saat
menyetujui. Lebih dari tiga pertanyaan yang lolos syarat itu → pekerjaannya terlalu besar untuk satu
taskdir.

## Why There Is No Plan Mode

Rencana eksekusi hidup di `brief-*.md` sebagai file — dibaca ulang, dibandingkan, dicerminkan ke nataflow, bertahan lintas
sesi, dan disetujui satu kali lewat ledger. Plan mode di atas brief berarti menyetujui isi yang sama dua
kali.

## Per-Repo Setup

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install frontend@nataflow
```

Marketplace `nataflow` memuat keempat plugin repo ini; lihat `README.md` di root repo.

Lalu di tiap repo frontend, sekali: `/frontend:profile`, atau cukup ajukan permintaan kerja pertama.
`lead` merutekan lane `PROFILE` lebih dulu bila profil belum ada — kecuali pertanyaan letak simbol/struktur
(`EXPLORE_FACT`), yang dijawab lewat `code-explorer` tanpa profil. Satu repo punya satu profil untuk satu
`target_app`/`stack` pada satu waktu; profil per-app di monorepo tidak didukung, dan ingest `architect` menolak
brief yang `stack`-nya ≠ profil. Skill `profile` mendeteksi stack, memindai repo
dengan resep adapter, dan menulis `.claude/profile/frontenddev/` — `index.json` plus sembilan berkas `.md`, modular
supaya tiap konsumen membuka hanya yang rutenya butuh. `manual-notes.md` satu-satunya yang selamat dari
tulis ulang penuh saat `REFRESH`. Jalankan ulang saat repo bergeser jauh: dependency baru, folder fitur
baru, atau migrasi stack.

`commands.md` merekam status tiap perintah saat dipindai **dan** apa yang tiap perintah tidak periksa —
baris kedua yang membuat `test` hijau berhenti dipakai sebagai bukti typecheck hijau (Metro membuang tipe
di React Native; `tsc` tidak membaca `.svelte`).

`profile` juga pemilik tunggal dua baris `.gitignore` berjangkar — `/.frontenddev/` dan
`frontenddev/docs/**/.explore/` — yang diputuskan dari exit code `git check-ignore`, bukan dari membaca
berkasnya. Gate lain (termasuk kelima pendispatch explorer) hanya memeriksanya dengan `git check-ignore -q`.
Pola tanpa jangkar di repo lama tidak ditulis ulang.

## Gate Hook

Hook `SessionStart` (`python3 hooks/detect.py --plugin frontend`, matcher
`startup|resume|clear|compact`) menyuntikkan pengingat gate `frontend:lead` dan status profil sekali
per sesi lewat `hookSpecificOutput.additionalContext`. `hooks/detect.py` identik byte-per-byte dengan
milik `backend` dan dipakai juga oleh skrip prasyarat, sehingga vonis hook = vonis skrip. Teksnya
ada di `hooks/gate_text.py`.

- **Kapan menyuntik**: profil `.claude/profile/frontenddev/` ada, atau manifest (root git, workspace
  terdeklarasi, `apps/*`, `packages/*`, `services/*`, anak langsung root; maksimal 200 kandidat) memuat
  penanda stack yang didukung (tabel Stack Adapters). React dan Svelte non-Kit wajib bersama Vite;
  `react-native`/`expo` dan `@sveltejs/kit` tidak. Next.js, CRA (`react-scripts`), serta React/Svelte
  tanpa Vite di luar cakupan. Di tempat lain hook diam. Di repo fullstack, hook `backend` menyala
  juga dengan deteksinya sendiri; keduanya menyuntik bloknya masing-masing.
- **Profil milik plugin lain** (`.claude/profile/index.json` lama milik `backend`) tidak pernah
  dibaca atau ditimpa. Profil frontend di lokasi lama memicu lane `PROFILE` mode MIGRATE.
- **Profil hilang, tidak sah, atau tidak lengkap**: permintaan kerja tetap lewat `frontend:lead`,
  yang merutekan lane `PROFILE` (GENERATE | REFRESH | MIGRATE) lebih dulu lalu melanjutkan rute tertunda.
  `EXPLORE_FACT` berangkat tanpa profil. Profil sendiri yang field `plugin`-nya asing dirutekan REFRESH.
- **Alur plugin lain**: permintaan yang memanggil atau melanjutkan `/analyst:*`, `/product:*`, atau
  `/quickdev:*` secara eksplisit dikecualikan dari gate.
- **Tiket analyst**: tiket `READY` diserahkan ke `/frontend:lead` lewat parameter `ticket_source`
  (path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md`). `AC-{n}`/`BR-{n}` kartu dirujuk `TAC-{n}`/`TBR-{n}`
  agar tidak bertabrakan dengan `AC-{n}` CONTRACT; tiap `TAC-{n}` dipikul `SC-{n}` atau tercatat di
  `## Out of Scope` (`validate_task.py` check 7), dan tiket yang disunting sesudah approve ditolak prasyarat
  `task` check 8.
- **Opt-out mekanis `.claude/workflow`**: berkas teks berisi nama plugin yang boleh menggerbangi repo,
  dipisah spasi, koma, atau baris. Isi `quickdev` → hook `frontend` dan `backend` diam; isi
  `frontend, quickdev` → hanya hook `frontend` yang menyala. Berkas kosong → tidak ada plugin yang boleh;
  berkas tidak ada → perilaku normal.
- **Prasyarat**: `python3` ≥ 3.9 di `PATH` (`tomllib` dipakai bila ≥ 3.11). Di Windows yang hanya
  punya `py`/`python`, hook tidak jalan.

## Upgrade dari 0.8.0

Versi 0.9.0 memperketat materai dan baseline. Akibatnya rantai yang sedang berjalan dari 0.8.0 dapat
berhenti di tiga tempat:

- **Materai lama tanpa `Sidik:`** — tiap hop `[x]` yang di-approve 0.8.0 divonis `DRIFT` (`chain.py verify`:
  "materai … tanpa `Sidik:`"). Remedi sekali per taskdir: `chain.py reopen --row <hop tercentang teratas>`
  lewat `frontend:lead` (kaskade membuka sisanya), lalu setujui ulang tiap hop di gate pemiliknya. Biayanya
  satu kuota reopen, dan satu ronde reviewer untuk CONTRACT/BRIEF yang direview. Rantai yang sudah `TUNTAS`
  tidak terkena.
- **Log baseline/closing tanpa `head`** — `validate_review.py --log` menagih `baseline_head`. Ukur ulang
  baseline dengan `run_verification.py baseline --force` di worktree pada akar `TASK.md`
  (`architect/SKILL.md` Phase 0 butir 2), lalu jalankan ulang verifikasi penutup.
- **Batas baru validator** — brief `BLOCKED` tak lagi memikul SC/AC, remedi yang bergantung pada unit
  asalnya ditolak, dan AC `terbukti` wajib berbukti. Batch yang kini `FAIL` diperbaiki lewat
  `reopen BRIEF` → `plan` APPEND. Approval lama tidak divonis ulang oleh validator baru.

## Boundaries With Other Skills

| Kebutuhan | Pakai |
|---|---|
| UI dari nol tanpa codebase acuan | `frontend-design` |
| Bug korektness, keamanan, efisiensi pada diff | `/code-review` |
| Kesesuaian arsitektur & konvensi repo di luar rantai aktif | `frontend:review` |
| Backend yang dipanggil kontrak ini | `backend` |
| Repo Next.js | di luar cakupan — tidak ada adapter, hook diam |
