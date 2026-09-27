# backend

Plugin Claude Code untuk kerja backend lintas-stack: Java Spring, Go, Node, Bun, Rust, PHP, dan
CodeIgniter 4. Dua belas skill dan enam subagent, dengan satu gerbang masuk, `backend:tech-lead`, yang
memutuskan lane, risk level, dan taskdir dari kode sebelum satu brief ditulis atau satu berkas `src/`
disentuh.

Plugin ini sengaja generic. Pengetahuan spesifik-repo hidup di `.claude/profile/backenddev/`, disiapkan
sekali lewat skill `profile`. Pengetahuan spesifik-stack hidup di satu adapter
`skills/profile/stacks/<stack>.md`, dipilih dari field `stack` `index.json`. Kontrak adapternya ada di
`skills/profile/stacks/_CONTRACT.md`.

| `stack` | Penanda deteksi (manifest) |
|---|---|
| `java-spring` | `pom.xml` groupId `org.springframework.boot`, atau Gradle/`libs.versions.toml` memuat `org.springframework.boot` |
| `go` | `go.mod` require langsung (bukan `// indirect`): gin, fiber, echo, chi, gorilla/mux, grpc-go |
| `node` | `package.json` `dependencies`: `@nestjs/core`, express, fastify, koa, `@hapi/hapi`, hono (tanpa penanda Bun) |
| `bun` | `elysia`, atau `hono` + `bun.lockb`/`bun.lock`/`bunfig.toml` tanpa nest/express |
| `rust` | `Cargo.toml`: axum, actix-web, rocket, warp, poem, salvo |
| `php-codeigniter` | `composer.json` require `codeigniter4/framework` |
| `php` | `composer.json` require laravel, symfony/framework-bundle, slim, laminas-mvc, yii2 |

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install backend@nataflow
```

Marketplace `nataflow` memuat keempat plugin repo ini. Lihat `README.md` di root repo untuk memilih
plugin dan cara keempatnya hidup berdampingan.

**Prasyarat**: `python3` ≥ 3.9 di `PATH` (3.11+ disarankan: anggota workspace Cargo hanya dibaca lewat
`tomllib`), `git`, dan repo git dengan `base_branch` yang jelas. Semua skrip hanya memakai stdlib. Toolchain
stack repo sendiri (build, test) dibutuhkan untuk baseline profil.

Lalu di tiap repo backend, sekali: `/backend:profile`, atau cukup ajukan permintaan kerja pertama.
`tech-lead` merutekan lane `PROFILE` lebih dulu bila profil belum ada.

## Dua Belas Skill

| Skill | Titik masuk user | Peran |
|---|---|---|
| `backend:tech-lead` | ya | gerbang tiap permintaan: lane, risk, taskdir, re-entry |
| `backend:profile` | ya | deteksi stack dan pemindaian arsitektur ke `.claude/profile/backenddev/` |
| `backend:debug` | ya | pembuktian rantai kausal `file:line` ke `RCA.md` |
| `backend:audit` | ya | sapuan 6 konvensi arsitektur ke `backenddev/issues/` |
| `backend:document-api` | ya | endpoint nyata dipetakan ke `docs/api/` |
| `backend:architect` | ya | orkestrasi sekuensial brief READY dan review penutup |
| `backend:analyst` | — | orkestrasi rantai TASK/BRD/PRD/brief dan gerbang approval |
| `backend:task` | — | akar rantai `TASK.md` |
| `backend:business-analysis` | — | hop BRD |
| `backend:system-analysis` | — | hop PRD |
| `backend:plan` | — | brief READY |
| `backend:report` | — | `REPORT.md` penutup |

Enam skill tanpa tanda "titik masuk user" ber-`user-invocable: false`. Model tetap memanggilnya lewat tool
Skill, tetapi skill itu tidak muncul di menu `/`, dan mengetik `/backend:plan` tidak menjalankan apa
pun. Untuk memulai, melanjutkan, atau memulihkan rantai, panggil `/backend:tech-lead`.

## Enam Subagent

| Agent | Tools | Peran |
|---|---|---|
| `code-explorer` | Read, Grep, Glob, Write | penelusur bukti `file:line`; menulis hanya ke laci `.explore/`, dipagari hook `guard_bash.py` |
| `code-implementor` | Read, Grep, Glob, Edit, Write, Bash | menerapkan satu brief READY, dipagari hook `guard_bash.py` |
| `code-reviewer` | Read, Grep, Glob, Bash, Write | menilai diff merge-base terhadap kontrak gabungan brief; menulis `REVIEW.md`, dipagari hook `guard_bash.py` |
| `brd-reviewer` | Read, Grep, Glob | vonis BRD `Approved`/`Issues Found` |
| `prd-reviewer` | Read, Grep, Glob | vonis PRD |
| `brief-reviewer` | Read, Grep, Glob | audit helikopter seluruh brief terhadap PRD, BRD, dan TASK |

## Lane

`tech-lead` memilih tepat satu dari tujuh lane (Keputusan 1, `skills/tech-lead/SKILL.md`). Bila lebih dari
satu cocok, presedensinya:

```
PROFILE → EXEC_BRIEF → AUDIT_SWEEP → DEFECT_RCA → PLANNING → API_DOCS → EXPLORE_FACT
```

| Lane | Rute |
|---|---|
| `PROFILE` | `profile` (GENERATE, REFRESH, atau MIGRATE) |
| `EXEC_BRIEF` | `architect` |
| `AUDIT_SWEEP` | `audit` |
| `DEFECT_RCA` | `debug` → `RCA.md`; bila `ROOT_CAUSE_CONFIRMED` → `plan` dengan `entry_mode: RCA` |
| `PLANNING` | `analyst`, termasuk perbaikan temuan `backenddev/issues/` dan `REVIEW.md` (`finding_source`) serta tiket analyst `READY` (`ticket_source`) |
| `API_DOCS` | `document-api` |
| `EXPLORE_FACT` | dijawab di Fase 1 `tech-lead`, berhenti |

Risk level: `BREAKING`, `MAJOR`, `MINOR`. Bila ragu, pilih yang lebih tinggi. `strict_mode` menaikkan satu
tingkat.

## Rantai Planning

`backend:analyst` memilih panjang rantai dari dua sumbu (`skills/analyst/references/chain-rules.md`
§1.3–1.4):

| Sumbu bisnis (BRD) | Sumbu kontrak (PRD) | Chain | Lane di `TASK.md` |
|---|---|---|---|
| aktif | aktif | `BRD_PRD_BRIEF` | `PRD_CONVERSION` |
| nol | aktif | `PRD_BRIEF` | `PRD_CONVERSION` |
| nol | nol | `BRIEF` | `DIRECT_BRIEF` |
| aktif | nol | tidak sah, naik ke `BRD_PRD_BRIEF` | `PRD_CONVERSION` |

- `BREAKING` → `PRD_BRIEF` atau `BRD_PRD_BRIEF`; `MAJOR` → ketiganya; `MINOR` → hanya `BRIEF` (MINOR
  dengan sumbu kontrak aktif dinaikkan ke MAJOR).
- Chain hanya naik, maksimal 2 transisi per taskdir, dan maksimal 2 re-entry. Hitungannya ada di
  `## Counters` `TASK.md`, dijaga `chain_counters.py`.
- `status: APPROVED` pada BRD/PRD hanya ditulis `backend:analyst`, sesudah reviewer `Approved` dan
  persetujuan user.

## Artefak di Repo Pengguna

```
.claude/profile/backenddev/
  index.json           project, stack, architecture, root_namespace, source_root,
                       commit_convention, base_branch, branch_convention, plugin
  stack.md · module-structure.md · domain-map.md · surface-map.md
  code-conventions.md · anti-patterns.md · invariants.md · commands.md
backenddev/
  docs/
    .explore/<slug>.md               laci dispatch gerbang (tidak di-commit)
    2609231200-order-refund/         <YYMMDDhhmm>-<slug>
      TASK.md  BRD.md  PRD.md  RCA.md
      brief-01-<unit>.md             READY → DONE | BLOCKED | SUPERSEDED
      report-01.md                   laporan brief yang gagal
      HALT.md  REVIEW.md  REPORT.md
      .explore/                      scratch skill hilir (tidak di-commit)
  issues/
    README.md                        indeks temuan audit
    2026-09-23-001-issues.md
docs/api/<slug>.md
```

Skill `profile` Fase 5 menambahkan `.explore/` dan `.backenddev/` ke `.gitignore` bila belum ter-ignore,
lalu melaporkannya sebagai "Menunggu commit".

**Profil lokasi lama.** Versi sebelumnya menulis profil langsung di `.claude/profile/`. Profil lama milik
backend memicu lane `PROFILE` mode MIGRATE, yang menjalankan
`skills/profile/scripts/migrate_profile.py`. Skrip ini memindah berkas lewat `git mv`, menulis
`"plugin": "backenddev"` ke `index.json`, dan tidak meng-commit. Commit `docs: migrate backend profile`
dilakukan `tech-lead` di Fase 5. Profil lama milik plugin lain tidak dibaca dan tidak ditimpa.

## Branch dan Commit

- Branch kerja selalu bercabang dari `base_branch` profil, bukan dari HEAD aktif, dengan nama
  `branch_convention` + slug (mis. `feat/<slug>`). Gerbang berhenti bila `base_branch` kosong, HEAD detached,
  bukan repo git, atau working tree kotor di luar `.explore/`.
- Staging selalu dengan path eksplisit. `git add .`/`-A` dilarang. Push, merge, rebase, `gh pr create`,
  `branch -d`, dan pindah branch hanya dengan izin user.

| Pemilik | Yang di-commit |
|---|---|
| `tech-lead` | profil, laporan audit, `RCA.md`, penghapusan `HALT.md` |
| `task` | `TASK.md` |
| `analyst` | eskalasi chain, tutup ledger, approval BRD/PRD |
| `business-analysis` / `system-analysis` | draft BRD / PRD sesudah reviewer `Approved` |
| `plan` | batch brief |
| `code-implementor` | `src/**` + brief, dengan pesan `commit_message` brief (`wip(...) [BLOCKED]` bila terblokir) |
| `code-reviewer` | `REVIEW.md` + baris indeks `issues/README.md` |
| `architect` | `HALT.md`, koreksi status `READY → DONE` |
| `report` | `REPORT.md` |

`audit` dan `debug` tidak meng-commit sendiri.

## Hook

`hooks/hooks.json` memasang dua hook.

**SessionStart** (`python3 hooks/detect.py --plugin backend`, matcher `startup|resume|clear|compact`,
timeout 5 detik) menyuntik blok `<backend-tech-lead-gate>` sekali per sesi. Blok itu berisi stack
terdeteksi, status profil, dan aturan bahwa `backend:tech-lead` jalan lebih dulu untuk tiap permintaan
kerja, termasuk susulan. `hooks/detect.py` identik byte-per-byte dengan milik `frontend` dan dipakai juga
oleh skrip prasyarat, sehingga vonis hook sama dengan vonis skrip.

- **Kapan menyuntik**: profil `.claude/profile/backenddev/` ada, atau salah satu manifest memuat penanda di
  tabel stack. Manifest dicari di root git, workspace terdeklarasi (npm/pnpm workspaces, `go.work`, anggota
  Cargo), `apps/*`, `packages/*`, `services/*`, dan anak langsung root, maksimal 200 kandidat. Direktori
  seperti `node_modules`, `vendor`, `docs`, `test(s)`, `examples`, dan direktori berawalan titik dilewati.
  Di tempat lain hook diam.
- **Status profil**: ADA; di lokasi lama → MIGRATE; belum ada atau milik plugin lain → tetap lewat
  `tech-lead`, yang menawarkan GENERATE; JSON rusak, tanpa stack, stack tidak dikenal, atau tidak lengkap →
  REFRESH.
- **Pengecualian**: jawaban atas klarifikasi rute yang sudah diputuskan, pengetahuan umum, operasi VCS atas
  kerja selesai, dan alur `/analyst:*` atau `/quickdev:*` yang dipanggil atau dilanjutkan secara eksplisit.
- **Opt-out `.claude/workflow`**: lihat Hidup Berdampingan.

**PreToolUse** (`python3 hooks/guard_bash.py hook`, matcher `Bash|Edit|Write`, timeout 10 detik) berlaku
untuk subagent `backend:code-implementor`, `backend:code-explorer`, dan `backend:code-reviewer`, dan menolak bila ragu (fail-closed). Implementor hanya
boleh menjalankan git read-only (`status`, `diff`, `log`, `show`, `rev-parse`, `ls-files`),
`git add <path>` eksplisit di dalam lease, dan `git commit -m` satu baris. Rantai perintah, pipe, pengalihan,
substitusi, dan ekspansi shell (`$`, backtick, brace `{a,b}`) ditolak; operator dinilai sesudah tokenisasi,
jadi `<T>` atau `->` di dalam kutip tetap satu argumen. Edit/Write hanya boleh ke path lease. Lease ditulis `architect` sebelum dispatch
(`guard_bash.py lease --brief <path>`) ke `<git-dir>/nataflow/lease-backend.json`, di luar
working tree. Isinya `## File scope` brief, berkas brief, `report-NN.md`, dan `finding_source`. Tanpa lease,
semua Bash/Edit/Write implementor ditolak. Untuk `backend:code-explorer`, hook yang sama hanya
mengizinkan Edit/Write ke laporan `backenddev/docs/[<taskdir>/].explore/*.md`. `backend:code-reviewer` hanya
boleh git read-only (ditambah `merge-base`, `symbolic-ref`), `ls`, serta `git add`/`git commit -m` dan
Edit/Write atas `<taskdir>/REVIEW.md` dan `backenddev/issues/README.md`; `reset`, `checkout`, `push`, build,
dan test ditolak.

## Penegakan Mekanis

Tiap skill punya `skills/<skill>/scripts/check_preconditions.py` yang dijalankan sebelum fase pertamanya
(`--json` dan `--root` tersedia; exit 0 = PASS, 1 = FAIL). `tech-lead` memakai `--read-only` di Fase 0 dan
`--re-entry` di Fase 5. Primitif bersamanya ada di `skills/_common/`:

| Skrip | Peran |
|---|---|
| `_common/precondition_lib.py` | parser frontmatter, taskdir, chain, status git, profil, dan ikatan approval BRD/PRD ke commit `docs(spec): approve …`; mengimpor `hooks/detect.py` |
| `_common/brief_status.py` | status brief dan penulis tunggalnya |
| `_common/run_verification.py baseline\|closing` | verifikasi baseline dan penutup, log mesin di `.explore/` |
| `_common/verify_scope.py` | diff commit/worktree terhadap `File scope` brief versi sebelum unit dikerjakan |
| `plan/scripts/scaffold_brief.py` | kunci matriks alokasi, lalu kerangka brief |
| `plan/scripts/validate_briefs.py` | validasi batch dan per-brief, ronde review brief |
| `analyst/scripts/chain_counters.py` | plafon eskalasi, re-entry, amandemen akar, dan ronde reviewer; menolak tabel yang diturunkan tangan |
| `architect/scripts/symbol_map.py` | peta simbol pada sha tertentu untuk ingest brief |

## Pemulihan

- **`tech-lead` Fase 3** memakai ulang taskdir yang belum tuntas. Brief BLOCKED atau `HALT.md` → `PLANNING`
  pada taskdir yang sama dengan `reentry_reason`; brief READY → `architect`; dokumen DRAFT → `analyst`.
  Taskdir tanpa ledger `## Chain` (lane `DEFECT_RCA`, backfill `EXEC_BRIEF`) dirutekan ke `plan` jalur RCA atau
  `debug`, bukan `PLANNING`. Taskdir baru hanya dibuat bila semua brief DONE/SUPERSEDED **dan** `REPORT.md`
  sudah terbit, atau bila plafon `analyst` tertembus dan user memilih merumuskan ulang permintaannya.
- **`tech-lead` Fase 5** (re-entry rantai) meng-commit artefak yang menunggu, lalu mengikuti tabel pengirim
  balik di `skills/tech-lead/references/gate-lifecycle.md` §6. Temuan P1 `REVIEW.md` dikerjakan di taskdir
  yang sama lewat `PLANNING` + `finding_source`.
- **`architect`** mulai dari brief READY pertama. Rantai dianggap tuntas hanya bila `REVIEW.md` dan
  `REPORT.md` sama-sama ada. `REVIEW.md` yang lebih tua dari commit brief/kode terakhir dianggap basi dan
  memicu review ulang. Matriks lengkapnya ada di `skills/architect/references/lifecycle-recovery.md`.

## Hidup Berdampingan

- **frontend**: profil terpisah; plugin lain itu memakai `.claude/profile/frontenddev/`, plugin ini
  `.claude/profile/backenddev/`. Di repo
  fullstack kedua hook menyala dengan deteksinya masing-masing. backend hanya melihat `dependencies`
  server, jadi manifest frontend tidak memicunya.
- **analyst**: tiket `READY` diserahkan ke `/backend:tech-lead` lewat parameter `ticket_source`
  (path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md`). `AC-{n}`/`BR-{n}` kartu dirujuk `TAC-{n}`/`TBR-{n}`;
  tiap `TAC-{n}` dipikul `SC-{n}` atau tercatat di `## Out of Scope` (`validate_doc.py` T10), dan tiket yang
  disunting sesudah approve ditolak prasyarat `task` check 7. Kontrak lengkap:
  `skills/tech-lead/references/gate-scope.md` bagian 4 B-2. Skill `backend:analyst` berbeda dari plugin
  `analyst`.
- **quickdev**: permintaan `/quickdev:*` dilewati gerbang. Untuk repo yang sepenuhnya memakai quickdev,
  tulis `.claude/workflow`.
- **`.claude/workflow`**: berkas teks berisi nama plugin yang boleh menggerbangi repo, dipisah spasi atau
  baris. Bila berkas ada dan tidak memuat `backend`, hook SessionStart backend diam. Contoh: isi
  `quickdev` → hook backend dan frontend diam; isi `frontend quickdev` → hanya frontend yang
  menyala. Bila berkas tidak ada, hook berjalan normal.

## Keterbatasan yang Diketahui

- Filter `.explore` di gerbang git terlalu longgar (direktori ter-track bernama `.explore` ikut lolos), dan
  merge/rebase/cherry-pick yang menggantung belum dideteksi. Pastikan tree bersih sebelum memulai rantai.
- Stacktrace untuk `debug` dioper sebagai argumen shell. Tempel log dari sumber yang dipercaya saja.
- Instruksi yang dimuat sebelum membaca kode besar (sekitar 90 ribu token untuk rantai penuh).
- Hook memagari tulis `code-explorer` hanya sampai pola laci `backenddev/docs/[<taskdir>/].explore/*.md`;
  kewajiban menulis tepat ke path `Berkas laporan` dari pendispatch ditegakkan lewat prompt, bukan hook.
- Hook tidak jalan di Windows yang hanya punya `py`/`python` tanpa `python3`.
