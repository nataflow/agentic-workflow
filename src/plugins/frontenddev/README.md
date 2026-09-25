# frontenddev

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
| `frontenddev:lead` | gerbang tiap permintaan: lane, sections, taskdir, pemulihan, eskalasi | — | — |
| `frontenddev:profile` | prasyarat sekali per repo | `.claude/profile/frontenddev/` | — |
| `frontenddev:task` | akar tiap taskdir | `TASK.md` + ledger `## Chain` | commit akar |
| `frontenddev:ux-design` | Gate Flow | `FLOW.md` | `chain.py approve --row FLOW` |
| `frontenddev:ui-design` | Gate Design | `UI.md` | `chain.py approve --row UI` |
| `frontenddev:contract` | Gate Contract (+ `contract-reviewer`) | `CONTRACT.md` | `chain.py approve --row CONTRACT` |
| `frontenddev:plan` | Gate Breakdown (+ `doc-reviewer`) | `brief-<NN>-<unit>.md`, `REVIEW-PLAN.md` | `chain.py approve --row BRIEF` |
| `frontenddev:architect` | eksekusi sekuensial, verifikasi penutup, review tunggal | status brief, `REVIEW.md` (ditulis `code-reviewer`) | commit unit; `validate_review.py` |
| `frontenddev:report` | laporan penutup | `REPORT.md` | commit — penanda tuntas |
| `frontenddev:review` | review ad-hoc di luar rantai aktif | chat, atau `frontenddev/reviews/<berkas>.md` | commit bila `--write` |

Hanya `lead`, `profile`, dan `review` yang muncul di menu `/`. Tujuh lainnya ber-`user-invocable: false`:
model tetap memanggilnya lewat tool Skill, tetapi mengetik `/frontenddev:plan` tidak menjalankan apa pun.
Untuk memulai, melanjutkan, atau memulihkan rantai, termasuk yang terputus di tengah eksekusi, panggil
`/frontenddev:lead`, yang merutekan ke gate pemiliknya.

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

## Workflow

```
permintaan ──► lead ──┬─► profile ─────────────► .claude/profile/frontenddev/
                      ├─► explore ─────────────► jawaban, berhenti
                      ├─► review (ad-hoc) ─────► laporan / frontenddev/reviews/, berhenti
                      │
                      └─► task ──► TASK.md + ## Chain ──► commit akar
                            │
                            ├─► ux-design  → FLOW.md DRAFT → commit → AskUserQuestion → chain.py approve FLOW
                            ├─► ui-design  → UI.md DRAFT   → commit → AskUserQuestion → chain.py approve UI
                            ├─► contract   → CONTRACT.md DRAFT → validate_doc → contract-reviewer (≤2 ronde)
                            │                → commit → AskUserQuestion → chain.py approve CONTRACT
                            ├─► plan       → brief READY × N → validate_briefs → doc-reviewer (≤2 ronde)
                            │                → commit → AskUserQuestion → chain.py approve BRIEF
                            └─► architect  → per unit: ingest → code-implementor → report-NN.md
                                             → matriks bukti disk → commit unit (+ gerbang kompilasi)
                                           → verifikasi penutup sekali → code-reviewer → validate_review
                                           → commit REVIEW.md → report → REPORT.md (tuntas)
```

Gate bersifat **kondisional** menurut `sections` `TASK.md`: `flow` menjadwalkan Gate Flow, `ui` Gate
Design, `sections` non-kosong Gate Contract, dan Gate Breakdown selalu. Lane `HOTFIX_MINOR` punya
`sections` kosong — satu gate saja, tanpa kontrak dan tanpa Plan Review.

## The Ledger

`TASK.md` memuat ledger `## Chain`, satu baris per hop yang dijadwalkan `sections`, ditulis
`chain.py init`:

```markdown
## Chain

- [x] FLOW     — frontenddev:ux-design → FLOW.md @ APPROVED 3f9c2ab
- [x] UI       — frontenddev:ui-design → UI.md @ APPROVED 8e01d7a
- [~] CONTRACT — frontenddev:contract  → CONTRACT.md @ re-entry 1 (was 7d1e0c4)
- [ ] BRIEF    — frontenddev:plan      → brief-*.md
```

`skills/_common/chain.py` adalah **satu-satunya penulis** ledger, status `APPROVED`, `lane`, dan
`sections`:

| Subperintah | Dipakai | Yang ditegakkan |
|---|---|---|
| `init` | `task` | baris ledger persis jadwal `sections` |
| `approve --row R --answer "<jawaban>"` | gate pemilik hop | hop hulu sah; dokumen `DRAFT` ter-commit; validator `PASS`; untuk CONTRACT/BRIEF ronde reviewer terakhir `PASS` atas konten final **tanpa `reopen` sesudah ronde itu** (BRIEF di hop `[~]` tanpa brief `READY` baru sah tanpa ronde baru). Menulis `APPROVED` + centang dalam satu commit yang memateraikan jawaban user, sha konten, dan `Hop: <R>` |
| `reopen --row R --reason` | `lead` | kaskade: R dan seluruh hop tercentang di bawahnya jadi `[~]`, dokumen FLOW/UI/CONTRACT-nya kembali `DRAFT`; seluruh kaskade divalidasi sebelum ada yang ditulis; plafon 3 per hop (dihitung saat hop itu target), 6 per taskdir |
| `escalate --lane L --sections S` | `lead` | lane hanya naik, sections hanya bertambah, hop tercentang di bawah hop baru wajib di-`reopen` dulu; plafon 2 |
| `abandon --reason` | `lead` | `TASK.md` `status: ABANDONED` atas keputusan user; taskdir keluar dari pemindaian (`DITUTUP`) |
| `files` | `code-reviewer`, `report` | berkas rantai: commit bersubjek `<type>(<slug>):` sejak akar |
| `revisions --row R` | gate pemilik hop | plafon 2 revisi berturut sejak draft/reopen |
| `verify` / `status` | siapa pun | tiap `[x]`: sha ada, dimateraikan commit `approve` yang memuat sha itu **dan** `Hop: <R>` hop itu serta lebih baru daripada reopen terakhirnya, dokumen `APPROVED`, **konten identik dengan saat disetujui kecuali baris `status:`**, `SC-{n}` akar tidak berubah sejak approval |

Sha yang dicentang adalah commit **konten** yang disetujui user. Karena itu setiap skrip prasyarat hilir
dapat membuktikan bahwa yang dikerjakan adalah yang disetujui: suntingan `CONTRACT.md` sesudah approval
tanpa `reopen` gagal di `plan`, `architect`, dan `report` sebagai drift. Batasnya dinyatakan apa adanya:
skrip tidak dapat membuktikan `AskUserQuestion` benar-benar terjadi — yang dijaminnya jejak, karena
approval tanpa jawaban ditolak dan jawabannya dimateraikan di badan commit.

## Mechanical Enforcement

Tiap skill kecuali `lead` punya `skills/<skill>/scripts/check_preconditions.py` yang dijalankan sebelum Phase 0 (`lead` memakai `skills/lead/scripts/taskdir_state.py`); primitif bersamanya
di `skills/_common/precondition_lib.py`, supaya satu artefak tidak pernah divonis berbeda oleh dua gate.
Di atasnya lima validator:

| Validator | Menagih |
|---|---|
| `_common/validate_doc.py --kind flow\|ui\|contract` | frontmatter, heading persis template, ID `DD`/`ST`/`AC` berurutan, nol placeholder; untuk CONTRACT **keterlacakan dua arah** — tiap token `Sumber` AC nyata, dan tiap `SC` akar, `DD` FLOW, `ST` UI dipikul minimal satu AC |
| `plan/scripts/validate_briefs.py` | 16 check S N D L T F B R V K O E C P G M — termasuk **G** (tiap `SC` dipikul brief lewat `fulfills`) dan **M** (remedi menunjuk brief `BLOCKED`, plafon 2 per unit asal, +1 per re-entry kontrak: `reopen … CONTRACT`, atau eskalasi dari `HOTFIX_MINOR`) |
| `task/scripts/validate_task.py` | struktur akar, pasangan lane/sections, `SC` ber-alat-ukur, bukti `file:baris` nyata, ledger `[ ]` (`--amend`: amandemen akar oleh `lead`, ledger boleh bercentang) |
| `architect/scripts/validate_review.py` | `taskdir`/`stack`/`reviewed_at` sah, H1 ber-slug; tiap `SC` dan `AC` divonis dengan bukti (`path:baris` berkas rantai atau perintah HIJAU); status 9 dimensi = severity terburuk temuan; `## Summary` dan Done Criteria DITUNDA ikut menurunkan verdict; `--log` mencocokkan verifikasi penutup dengan log mesin; hitungan temuan; `base` = commit akar `TASK.md`; **verdict diturunkan**: `BLOCKED` ⇔ P1 / SC belum terbukti / verifikasi merah (`TIMEOUT` atau galat baru > 0; `MERAH` bergalat baru 0 adalah warisan baseline) |
| `report/scripts/validate_report.py` | Ringkasan ≥ 5 kata, butir ≥ 3 kata; perubahan berakar berkas rantai; temuan REVIEW `PLANNED`/`DEFERRED` disebut di Catatan; tiap SC `PERLU VERIFIKASI MANUAL` tercatat |
| `review/scripts/validate_audit.py` | berkas audit `frontenddev/reviews/`: ID `P{n}-{m}` berurutan, hitungan `p1/p2/p3`, `verdict` turunan, `> Status:` ber-enum, jangkar `file:baris`; `--only-status-changed` menolak diff `finding_source` yang menyentuh baris selain `> Status:` |

Dan dua penjaga keadaan:

- `_common/review_round.py` — plafon ronde reviewer dokumen (2 per putaran, 8 per taskdir; putaran baru
  dimulai sesudah dokumen yang lolos ronde `PASS` di-commit, atau sesudah `reopen` hop gate itu) disimpan di
  `.explore/<gate>-review-state.json` beserta sidik konten, epoch reopen, dan `HEAD` tiap ronde. State rusak →
  FAIL (pulihkan dari `.bak`); `commit` meng-commit draft/batch hanya sesudah ronde `PASS` dengan trailer
  `Review-Round`, sehingga state yang hilang terdeteksi (`rebuild` memulihkan hitungannya).
- `lead/scripts/taskdir_state.py` — memvonis keadaan tiap taskdir (`AKAR`, `GATE`, `DRIFT`,
  `EKSEKUSI`, `TERHENTI`, `PENUTUP`, `TEMUAN`, `LAPORAN`, `LAPORAN TERTUNDA`, `TUNTAS`, `DITUTUP`, `RUSAK`) beserta satu
  rute berikutnya, dari disk dan ledger — bukan dari ingatan sesi.

Pasangan `(lane, sections)` ditegakkan di setiap gate: `HOTFIX_MINOR` ⇔ sections kosong;
`FAST_FORWARD`/`REFACTOR_ARCH` ⇔ tepat `architecture`; `FULL_PIPELINE` memuat `flow` atau `ui`.
`lane`/`sections` yang berubah di luar commit akar (`kunci TASK`) atau `chain.py escalate` divonis `RUSAK`
oleh `taskdir_state.py` dan `FAIL` di check akar setiap gate.

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

1. **Ingest** — `check_preconditions.py --brief NN`: brief `READY`, `depends_on` tertutup lewat commit
   `implement unit`, `report-NN.md` belum ada, kesegaran `based_on`.
2. **Dispatch** — `code-implementor` menerapkan brief tanpa satu perintah terminal pun (Bash hanya untuk
   `git restore` ber-scope dan `rm --` atas berkas `CREATE` buatannya sendiri) dan menulis `report-<NN>.md` — laporan yang bertahan melewati sesi.
3. **Matriks bukti disk** — `git status` dan hunk anchor disandingkan dengan `files_touched`; laporan
   adalah klaim, disk adalah bukti. Hasilnya commit unit (brief `DONE` + kode + laporan, satu commit)
   atau commit `BLOCKED`.
4. **Gerbang kompilasi per-brief** — typecheck sesudah commit, hanya bila adapter `typecheck-per-brief: ya`,
   divonis relatif baseline.

Brief `BLOCKED` tidak pernah naik lagi: sisa pekerjaannya diambil brief remedi (`remedies: "NN"`) pada
taskdir yang sama lewat `reopen BRIEF` → `plan` APPEND. Remedi ketiga atas unit yang sama dilarang —
cacatnya di kontrak (`reopen CONTRACT`; di `HOTFIX_MINOR`: `reopen BRIEF` → `escalate FAST_FORWARD`).
Berkas yang tersentuh di luar union `files_touched` adalah **berkas yatim** — cacat perencanaan,
dirutekan ke kontrak, tidak pernah ditambal di brief `DONE`. `REVIEW.md` `BLOCKED` juga diperbaiki di
taskdir yang sama: `reopen BRIEF` → `plan` APPEND brief perbaikan → eksekusi → review ulang yang
menimpa `REVIEW.md`. Rantai yang ditinggalkan user ditutup `chain.py abandon`.

Sesudah seluruh unit tertutup: lint, test, build, dan typecheck **sekali**, ditulis ke
`.explore/closing-verification.md`; hijau → `code-reviewer` menilai berkas rantai (`chain.py files`) terhadap union
`files_touched`, sembilan dimensi, CONTRACT, dan SC; `REVIEW.md` di-commit hanya sesudah
`validate_review.py` `PASS`.

## Artifacts

```
./frontenddev/
  docs/
    2609231200-order-checkout/
      TASK.md            akar + ledger     → task; chain.py
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
- **`DRAFT`** — FLOW/UI/CONTRACT yang ditulis penulisnya dan di-commit, menunggu keputusan user; juga keadaan dokumen yang dibuka ulang.
- **`APPROVED`** — ditulis hanya oleh `chain.py approve`.
- **`READY`** → **`DONE`** | **`BLOCKED`** — khusus brief; transisi ditulis `architect` bersama commit-nya.

Tiap dokumen membawa `based_on: <sha> (<tanggal>)` dan `stack: <stack-id>` — brief yang lahir untuk
`react-vite` tidak dieksekusi di profil `sveltekit`, dan brief yang berkasnya bergerak sesudah ditulis
diberi `WARN` di ingest.

## Commits

Plugin meng-commit apa yang ia tulis **di titik ia selesai ditulis**, selalu dengan path eksplisit —
tidak pernah `git add .`/`-A`, tidak pernah `commit -a`, tidak pernah `--no-verify`, tidak pernah push
atau pindah branch. Subjek tiap commit rantai memuat `(<slug>)`; `report` dan ingest mengenali commit
rantai dari situ.

| Titik | Subjek | Pemilik |
|---|---|---|
| Akar | `docs(<slug>): kunci TASK sebagai akar rantai` | `task` |
| Draft / revisi dokumen gate | `docs(<slug>): draft FLOW.md` · `revise FLOW.md` | gate pemilik |
| Approval | `docs(<slug>): approve FLOW.md` · `approve breakdown (<N> briefs)` | `chain.py` |
| Re-entry / eskalasi / penutupan | `docs(<slug>): reopen <ROW ROW ...> — <alasan>` · `eskalasi lane <A> → <B>` · `tutup taskdir — <alasan>` | `chain.py` |
| Amandemen akar | `docs(<slug>): amandemen akar TASK` | `lead` |
| Batch brief | `docs(<slug>): draft breakdown (<N> briefs)` · `revise breakdown` · `draft breakdown append (...)` | `plan` |
| Unit | `feat(<slug>): implement unit <NN> - <nama>` · `docs(<slug>): unit <NN> BLOCKED - <sebab>` | `architect` |
| Review penutup | `docs(<slug>): closing review <verdict>` | `architect` |
| Laporan | `docs(<slug>): laporkan hasil rantai <slug>` | `report` |

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

Rencana eksekusi hidup di `brief-*.md` sebagai file — dibaca ulang, di-diff, di-commit, bertahan lintas
sesi, dan disetujui satu kali lewat ledger. Plan mode di atas brief berarti menyetujui isi yang sama dua
kali.

## Per-Repo Setup

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install frontenddev@fakhrulnugroho
```

Marketplace `fakhrulnugroho` memuat keempat plugin repo ini; lihat `README.md` di root repo.

Lalu di tiap repo frontend, sekali: `/frontenddev:profile`, atau cukup ajukan permintaan kerja pertama.
`lead` merutekan lane `PROFILE` lebih dulu bila profil belum ada. Skill `profile` mendeteksi stack, memindai repo
dengan resep adapter, dan menulis `.claude/profile/frontenddev/` — `index.json` plus sembilan berkas `.md`, modular
supaya tiap konsumen membuka hanya yang rutenya butuh. `manual-notes.md` satu-satunya yang selamat dari
tulis ulang penuh saat `REFRESH`. Jalankan ulang saat repo bergeser jauh: dependency baru, folder fitur
baru, atau migrasi stack.

`commands.md` merekam status tiap perintah saat dipindai **dan** apa yang tiap perintah tidak periksa —
baris kedua yang membuat `test` hijau berhenti dipakai sebagai bukti typecheck hijau (Metro membuang tipe
di React Native; `tsc` tidak membaca `.svelte`).

## Gate Hook

Hook `SessionStart` (`python3 hooks/detect.py --plugin frontenddev`, matcher
`startup|resume|clear|compact`) menyuntikkan pengingat gate `frontenddev:lead` dan status profil sekali
per sesi lewat `hookSpecificOutput.additionalContext`. `hooks/detect.py` identik byte-per-byte dengan
milik `backenddev` dan dipakai juga oleh skrip prasyarat, sehingga vonis hook = vonis skrip. Teksnya
ada di `hooks/gate_text.py`.

- **Kapan menyuntik**: profil `.claude/profile/frontenddev/` ada, atau manifest (root git, workspace
  terdeklarasi, `apps/*`, `packages/*`, `services/*`, anak langsung root; maksimal 200 kandidat) memuat
  penanda stack yang didukung (tabel Stack Adapters). React dan Svelte non-Kit wajib bersama Vite;
  `react-native`/`expo` dan `@sveltejs/kit` tidak. Next.js, CRA (`react-scripts`), serta React/Svelte
  tanpa Vite di luar cakupan. Di tempat lain hook diam. Di repo fullstack, hook `backenddev` menyala
  juga dengan deteksinya sendiri; keduanya menyuntik bloknya masing-masing.
- **Profil milik plugin lain** (`.claude/profile/index.json` lama milik `backenddev`) tidak pernah
  dibaca atau ditimpa. Profil frontenddev di lokasi lama memicu lane `PROFILE` mode MIGRATE.
- **Profil hilang, tidak sah, atau tidak lengkap**: permintaan kerja tetap lewat `frontenddev:lead`,
  yang merutekan lane `PROFILE` (GENERATE | REFRESH | MIGRATE) lebih dulu lalu melanjutkan rute tertunda.
- **Alur plugin lain**: permintaan yang memanggil atau melanjutkan `/analyst:*` atau `/quickdev:*`
  secara eksplisit dikecualikan dari gate.
- **Opt-out mekanis `.claude/workflow`**: berkas teks berisi nama plugin yang boleh menggerbangi repo,
  dipisah spasi atau baris. Isi `quickdev` → hook `frontenddev` dan `backenddev` diam; isi
  `frontenddev quickdev` → hanya hook `frontenddev` yang menyala. Berkas tidak ada → perilaku normal.
- **Prasyarat**: `python3` ≥ 3.9 di `PATH` (`tomllib` dipakai bila ≥ 3.11). Di Windows yang hanya
  punya `py`/`python`, hook tidak jalan.

## Boundaries With Other Skills

| Kebutuhan | Pakai |
|---|---|
| UI dari nol tanpa codebase acuan | `frontend-design` |
| Bug korektness, keamanan, efisiensi pada diff | `/code-review` |
| Kesesuaian arsitektur & konvensi repo di luar rantai aktif | `frontenddev:review` |
| Backend yang dipanggil kontrak ini | `backenddev` |
| Repo Next.js | di luar cakupan — tidak ada adapter, hook diam |
