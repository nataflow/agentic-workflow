# agentic-workflow

Marketplace plugin Claude Code `fakhrulnugroho`: empat plugin untuk alur kerja rekayasa perangkat lunak,
mulai dari tiket stakeholder sampai kode yang direview.

| Plugin | Versi | Fungsi | Titik masuk |
|---|---|---|---|
| [`analyst`](src/plugins/analyst/README.md) | 0.3.0 | Permintaan pengguna/stakeholder menjadi `TICKET.md` non-teknis (user story, acceptance criteria, aturan bisnis) lewat elisitasi, review independen, dan persetujuan | `/analyst:intake` |
| [`backenddev`](src/plugins/backenddev/README.md) | 0.6.0 | Kerja backend 7 stack (Java Spring, Go, Node, Bun, Rust, PHP, CodeIgniter 4): profil, TASK/BRD/PRD/brief, eksekusi, review, dan laporan | `/backenddev:tech-lead` |
| [`frontenddev`](src/plugins/frontenddev/README.md) | 0.5.0 | Kerja frontend (React + Vite, React Native/Expo, SvelteKit, Svelte + Vite): alur layar, bentuk layar, kontrak, brief, eksekusi, review, dan laporan dengan ledger approval | `/frontenddev:lead` |
| [`quickdev`](src/plugins/quickdev/README.md) | 0.2.0 | Alur ringan untuk stack apa pun: profil, explore, clarify, satu berkas rencana, execute, dan review, tanpa taskdir dan tanpa subagent | `/quickdev:profile`, `/quickdev:plan` |

Skill internal (mis. `backenddev:plan`, `frontenddev:contract`, `analyst:spec`) tidak muncul di menu `/`.
Model memanggilnya dari gerbang masing-masing.

## Instalasi

```
/plugin marketplace add <owner>/<repo>
/plugin install analyst@fakhrulnugroho
/plugin install backenddev@fakhrulnugroho
/plugin install frontenddev@fakhrulnugroho
/plugin install quickdev@fakhrulnugroho
```

Untuk salinan lokal: `/plugin marketplace add ./path/ke/agentic-workflow`. Marketplace direktori lokal
memuat plugin langsung dari tempatnya dan tidak dikunci versi, jadi perubahan berkas langsung terpakai.
Marketplace git memakai `version` di `plugin.json`: pengguna hanya mendapat perubahan bila versinya naik.

## Prasyarat

- `python3` ≥ 3.9 di `PATH` untuk hook dan skrip `analyst`, `backenddev`, dan `frontenddev`. Semua skrip
  hanya memakai stdlib. Python 3.11+ disarankan untuk repo Rust ber-workspace (`tomllib`).
- `git`. `backenddev` dan `frontenddev` mewajibkan repo git, sedangkan `analyst` bisa berjalan di folder
  dokumen biasa.
- Di Windows yang hanya punya `py`/`python` tanpa `python3`, hook SessionStart tidak jalan.

## Memilih Plugin

| Situasi | Plugin |
|---|---|
| Peminta non-engineer atau stakeholder; kebutuhan belum jelas | `analyst` |
| Repo backend salah satu dari 7 stack; kerja berisiko atau butuh kontrak dan jejak keputusan | `backenddev` |
| Repo React + Vite, React Native/Expo, SvelteKit, atau Svelte + Vite | `frontenddev` |
| Perubahan kecil–menengah, stack lain (Next.js, FastAPI, …), tanpa taskdir | `quickdev` |

Rantai `analyst` → engineer: tiket `READY` diserahkan dengan menempelkan isi `TICKET.md` sebagai permintaan
ke `/backenddev:tech-lead` dan/atau `/frontenddev:lead`. Engineer lalu menerbitkan `TASK.md` teknisnya
sendiri.

## Hidup Berdampingan

Keempat plugin biasanya dipasang user-wide. Yang menentukan perilaku di satu repo:

- **Hook SessionStart.** Hanya `backenddev` dan `frontenddev` yang punya hook. Keduanya berbagi
  `hooks/detect.py` yang identik byte-per-byte, dan masing-masing menyala bila profilnya ada atau
  manifest repo memuat penanda stack-nya. Di repo fullstack keduanya menyala dan menyuntik blok gerbang
  masing-masing. Di repo lain keduanya diam.
- **Profil per plugin.** `.claude/profile/backenddev/` dan `.claude/profile/frontenddev/` terpisah. Profil
  lama di `.claude/profile/` dimigrasikan oleh pemiliknya (mode MIGRATE) dan tidak disentuh plugin lain.
  `quickdev` memakai `repo-profile.md` sendiri.
- **Pemanggilan eksplisit.** Teks gerbang engineer mengecualikan permintaan yang memanggil atau melanjutkan
  `/analyst:*` dan `/quickdev:*`. Skill quickdev hanya jalan bila user mengetik `/quickdev:<skill>`.
- **Penanda `.claude/workflow`.** Berkas teks di repo pengguna berisi nama plugin yang boleh menggerbangi
  repo itu, dipisah spasi atau baris. Hook yang namanya tidak tercantum akan diam. Isi `quickdev` membuat
  kedua hook engineer diam; isi `frontenddev quickdev` hanya menyalakan frontenddev. Bila berkas tidak ada,
  semua hook berjalan normal.

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

CI saat ini menjalankan lint dengan `--ignore R2`, yang harus sinkron dengan `deferred` di
`tests/test_lint_plugins.py`. Salinan berkas yang sengaja identik antar-plugin (`hooks/detect.py`,
`profile/scripts/migrate_profile.py`, `_common/verify_scope.py`, `_common/run_verification.py`) dijaga oleh
test. Ubah keduanya bersama-sama.

**Kebijakan versi.** `version` hanya ditulis di `src/plugins/<plugin>/.claude-plugin/plugin.json`, tidak
di `marketplace.json`, karena Claude Code selalu memakai nilai `plugin.json`. Setiap PR yang mengubah
`src/plugins/<plugin>/` wajib menaikkan `version` plugin itu. Lint M7 (`--base`) menagihnya. `description`
dan `author` di entri marketplace harus sama dengan `plugin.json`, karena listing `/plugin` menampilkan nilai
entri (lint M4).

**Skill internal.** Skill yang deskripsinya diawali "Dipanggil …" wajib ber-`user-invocable: false` (lint
F3). Skill quickdev memakai `disable-model-invocation: true` supaya hanya user yang bisa memanggilnya.

## Lisensi

[MIT](LICENSE)
