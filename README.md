# nataflow

Marketplace plugin Claude Code `nataflow`: tujuh plugin untuk alur kerja rekayasa perangkat lunak,
mulai dari inisiasi produk dan tiket stakeholder sampai kode yang direview, ditambah peta lintas repo untuk
memahami seluruh aplikasi satu perusahaan dan kerja langsung dengan server nataflow.

| Plugin | Versi | Fungsi | Titik masuk |
|---|---|---|---|
| [`analyst`](src/plugins/analyst/README.md) | 0.16.0 | Permintaan pengguna/stakeholder (satu, atau hingga lima sekaligus secara berurutan) menjadi `TICKET.md` non-teknis (user story, acceptance criteria, aturan bisnis), atau perubahan struktur dari lead engineer menjadi tiket `TECH` berbukti `file:baris`, lewat elisitasi, review independen, dan persetujuan; catatan kasar rapat menjadi `NOTULEN.md` | `/analyst:intake`, `/analyst:notulen` |
| [`backend`](src/plugins/backend/README.md) | 0.15.0 | Kerja backend 7 stack (Java Spring, Go, Node, Bun, Rust, PHP, CodeIgniter 4): profil, TASK/BRD/PRD/brief, eksekusi, review, dan laporan | `/backend:tech-lead` |
| [`frontend`](src/plugins/frontend/README.md) | 0.14.0 | Kerja frontend (React + Vite, React Native/Expo, SvelteKit, Svelte + Vite): alur layar, bentuk layar, kontrak, brief, eksekusi, review, dan laporan dengan ledger approval | `/frontend:lead` |
| [`quickdev`](src/plugins/quickdev/README.md) | 0.8.0 | Alur ringan untuk stack apa pun: profil, explore, clarify, satu berkas rencana, execute, dan review, tanpa taskdir dan tanpa subagent | `/quickdev:profile`, `/quickdev:plan` |
| [`nataflow`](src/plugins/nataflow/README.md) | 0.1.0 | Artifact nataflow: halaman HTML mandiri yang dinilai gerbang kontrak halaman lalu di-upsert ke project milik MCP key, tanpa berkas di repo | `/nataflow:create-artifact` |
| [`product`](src/plugins/product/README.md) | 0.1.0 | Inisiasi produk baru (folder kosong), fitur baru, atau improvement fitur (codebase) menjadi `CHARTER.md` enam pilar — Purpose, Actors, Business Process, Business Rules, Success Criteria, Scope — dengan guard permintaan yang terlalu umum, elisitasi, review independen, dan persetujuan | `/product:init` |
| [`fullstack`](src/plugins/fullstack/README.md) | 0.3.0 | Memahami seluruh aplikasi dari root multi-repo (satu proyek atau banyak proyek satu perusahaan): peta aplikasi `PETA.md` dari profil backend/frontend tiap repo tanpa membaca kode, explore permukaan satu pertanyaan konkret dengan jahitan frontend → backend dan API → API yang dicocokkan skrip, dan penelusuran alur di dalam repo lewat subagent explorer backend/frontend; read-only terhadap repo | `/fullstack:explore` |

Skill internal (mis. `backend:plan`, `frontend:contract`, `analyst:spec`) tidak muncul di menu `/`.
Model memanggilnya dari gerbang masing-masing.

## Instalasi

```
/plugin marketplace add <owner>/<repo>
/plugin install analyst@nataflow
/plugin install backend@nataflow
/plugin install frontend@nataflow
/plugin install quickdev@nataflow
/plugin install nataflow@nataflow
/plugin install product@nataflow
/plugin install fullstack@nataflow
```

Untuk salinan lokal: `/plugin marketplace add ./path/ke/agentic-workflow`. Marketplace direktori lokal
memuat plugin langsung dari tempatnya dan tidak dikunci versi, jadi perubahan berkas langsung terpakai.
Marketplace git memakai `version` di `plugin.json`: pengguna hanya mendapat perubahan bila versinya naik.

## Prasyarat

- `python3` ≥ 3.9 di `PATH` untuk hook dan skrip `analyst`, `backend`, `frontend`, `nataflow`, `product`, dan `fullstack`. Semua skrip
  hanya memakai stdlib. Python 3.11+ disarankan untuk repo Rust ber-workspace (`tomllib`).
- `git`. `backend` dan `frontend` mewajibkan repo git, sedangkan `analyst` dan `product` bisa berjalan di
  folder dokumen biasa atau folder kosong. `nataflow` tidak butuh repo, tetapi butuh server MCP nataflow yang berjalan.
  `fullstack` justru berjalan di folder non-git yang menampung repo git (`<root>/<repo>` atau
  `<root>/<proyek>/<repo>`), dan butuh repo aplikasinya sudah diprofilkan `backend`/`frontend`.
- Di Windows yang hanya punya `py`/`python` tanpa `python3`, hook SessionStart tidak jalan.

## Memilih Plugin

| Situasi | Plugin |
|---|---|
| Gagasan produk baru, fitur baru, atau improvement yang butuh arah lengkap sebelum dipecah jadi tiket | `product` |
| Peminta non-engineer atau stakeholder; kebutuhan belum jelas | `analyst` |
| Catatan kasar rapat yang perlu dirapikan jadi notulen | `analyst` (`/analyst:notulen`) |
| Repo backend salah satu dari 7 stack; kerja berisiko atau butuh kontrak dan jejak keputusan | `backend` |
| Repo React + Vite, React Native/Expo, SvelteKit, atau Svelte + Vite | `frontend` |
| Perubahan kecil–menengah, stack lain (Next.js, FastAPI, …), tanpa taskdir | `quickdev` |
| Laporan, dashboard, atau diagram HTML yang dibuka anggota project di nataflow | `nataflow` |
| Memahami banyak repo sekaligus dari folder induknya: aplikasi apa saja, siapa memanggil siapa, alur satu fitur lintas frontend dan backend, atau cara kerja fitur di dalam satu repo | `fullstack` |

Rantai `product` → `analyst`: butir Scope `S<n>` charter `APPROVED` dibawa satu per satu ke `/analyst:intake`
(serah-terima otomatis belum aktif; ID `S<n>` sudah disiapkan untuk itu).

Rantai `analyst` → engineer: tiket `READY` diserahkan dengan menempelkan isi `TICKET.md` sebagai permintaan
ke `/backend:tech-lead` dan/atau `/frontend:lead`. Engineer lalu menerbitkan `TASK.md` teknisnya
sendiri.

## Hidup Berdampingan

Ketujuh plugin biasanya dipasang user-wide. Yang menentukan perilaku di satu repo:

- **Hook SessionStart.** Hanya `backend` dan `frontend` yang punya hook. Keduanya berbagi
  `hooks/detect.py` yang identik byte-per-byte, dan masing-masing menyala bila profilnya ada atau
  manifest repo memuat penanda stack-nya. Di repo fullstack keduanya menyala dan menyuntik blok gerbang
  masing-masing. Di repo lain keduanya diam. Di root multi-repo (folder non-git dengan ≥ 2 repo anak),
  keduanya tidak menggerbangi: bloknya hanya menunjuk repo miliknya dan `/fullstack:explore`.
- **Profil per plugin.** `.claude/profile/backenddev/` dan `.claude/profile/frontenddev/` terpisah. Profil
  lama di `.claude/profile/` dimigrasikan oleh pemiliknya (mode MIGRATE) dan tidak disentuh plugin lain.
  `quickdev` memakai `repo-profile.md` sendiri.
- **Pemanggilan eksplisit.** Teks gerbang engineer mengecualikan permintaan yang memanggil atau melanjutkan
  `/analyst:*`, `/product:*`, dan `/quickdev:*`. Skill quickdev hanya jalan bila user mengetik `/quickdev:<skill>`.
- **Penanda `.claude/workflow`.** Berkas teks di repo pengguna berisi nama plugin yang boleh menggerbangi
  repo itu, dipisah spasi atau baris. Hook yang namanya tidak tercantum akan diam. Isi `quickdev` membuat
  kedua hook engineer diam; isi `frontend quickdev` hanya menyalakan frontend. Bila berkas tidak ada,
  semua hook berjalan normal.
- **Dokumen taskdir di luar git.** `backend` dan `frontend` tidak pernah meng-commit dokumen taskdir
  (`backenddev/docs/**`, `frontenddev/docs/**`). Penanda `<prefix>/docs/.gitignore` (berisi `*`, ikut
  mengabaikan dirinya sendiri) ditulis gerbangnya, dan keutuhan rantai dijaga materai di disk: `doc_seal.py`
  di backend dan `## Riwayat Rantai` tulisan `chain.py` di frontend. Yang tetap di-commit hanya kode, profil,
  dan dokumen tingkat repo (`backenddev/issues/`, `docs/api/`, `frontenddev/reviews/`). Repo yang sudah
  meng-commit dokumen taskdir dimigrasikan sekali lewat `skills/_common/docs_git.py migrate` sesudah
  persetujuan user.
- **Sinkron nataflow (opsional).** `.claude/nataflow.json` di repo pengguna mengaktifkan cermin artefak ke
  server MCP nataflow untuk keempat plugin sekaligus: tiket analyst menjadi task, taskdir backend/frontend dan
  rencana quickdev menjadi workdir beserta dokumennya. Taskdir yang berangkat dari tiket menempel ke task tiket
  itu. Pustaka `skills/_common/nataflow_sync.py` identik byte-per-byte di keempat plugin. Disk tetap sumber
  kebenaran, dan untuk dokumen taskdir nataflow menjadi satu-satunya salinan di luar mesin kerja; tanpa config,
  gerbang `task` memperingatkan bahwa dokumen taskdir hanya ada di disk itu. Kegagalan sinkron tidak pernah
  menahan rantai.

## Pengembangan

```
.claude-plugin/marketplace.json   katalog; tanpa field version
src/plugins/<plugin>/             berkas yang tersalin ke cache plugin pengguna
  .claude-plugin/plugin.json      sumber tunggal version, description, author
  skills/  agents/  hooks/  README.md
tests/                            pytest; di luar src/ supaya tidak ikut terpasang
scripts/lint_plugins.py           lint statis manifest, frontmatter, rujukan, skrip, dan hook
.github/workflows/ci.yml          pytest 3.9–3.13 + macOS, hooks, lint, claude plugin validate
```

Menjalankan test dan lint dari root repo:

```sh
python3 -m pytest                          # atau: uvx --python 3.9 pytest -q
python3 scripts/lint_plugins.py            # --json, --strict, --ignore R2, --base origin/main
claude plugin validate .                   # sebelum rilis
```

CI menjalankan lint dengan `LINT_IGNORE` kosong, yang harus sinkron dengan `deferred` di
`tests/test_lint_plugins.py`. Salinan berkas yang sengaja identik antar-plugin (`hooks/detect.py`,
`profile/scripts/migrate_profile.py`, `_common/verify_scope.py`, `_common/run_verification.py`,
`_common/docs_git.py`) dijaga oleh test. Ubah keduanya bersama-sama.

**Kebijakan versi.** `version` hanya ditulis di `src/plugins/<plugin>/.claude-plugin/plugin.json`, tidak
di `marketplace.json`, karena Claude Code selalu memakai nilai `plugin.json`. Setiap PR yang mengubah
`src/plugins/<plugin>/` wajib menaikkan `version` plugin itu. Lint M7 (`--base`) menagihnya. `description`
dan `author` di entri marketplace harus sama dengan `plugin.json`, karena listing `/plugin` menampilkan nilai
entri (lint M4).

**Skill internal.** Skill yang deskripsinya diawali "Dipanggil …" wajib ber-`user-invocable: false` (lint
F3). Skill quickdev memakai `disable-model-invocation: true` supaya hanya user yang bisa memanggilnya.

## Lisensi

[MIT](LICENSE)
