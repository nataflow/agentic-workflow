# quickdev

Alur kerja ringan untuk repo backend, frontend, dan fullstack: enam skill tanpa taskdir, tanpa subagent, tanpa
hook, dan dengan satu skrip (`skills/_common/plan_lock.py`, pengunci rencana, beserta pustaka sinkron
`nataflow_sync.py`). Setiap tugas punya **satu berkas rencana** (`plan/<task>.md`), sedangkan perubahan kodenya
boleh menyentuh banyak berkas dan layer. Semua kerja berlangsung di percakapan utama.

## Kapan Dipakai

- Perubahan kecil sampai menengah yang tidak butuh BRD/PRD, ledger approval, atau review subagent.
- Stack yang tidak dilayani `backend`/`frontend`, mis. Next.js, FastAPI, Django, atau Rails.
- Repo yang sudah memakai `backend`/`frontend`, untuk kerja yang sengaja dibuat ringan. Panggil
  `/quickdev:*` secara eksplisit (lihat Hidup Berdampingan).

Untuk kerja berisiko (kontrak API, migrasi skema, perubahan lintas modul yang butuh jejak keputusan), pakai
gerbang `backend:tech-lead` atau `frontend:lead`.

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install quickdev@nataflow
```

Prasyarat: `git` (execute dan review menuntut repo git), `python3` (3.9+, hanya stdlib) untuk
`plan_lock.py`, dan toolchain repo sendiri untuk baseline dan verifikasi.

## Enam Skill

Keenam skill ber-`disable-model-invocation: true`: skill hanya jalan bila **user** mengetik
`/quickdev:<skill>`. Model tidak memanggilnya sendiri, termasuk dari skill quickdev lain. Setiap skill
menutup dengan status dan **menawarkan** langkah berikutnya, lalu menunggu user.

```
/quickdev:profile  → PROFILED
/quickdev:explore  → EXPLORED
/quickdev:clarify  → CLARIFIED | SKIPPED
/quickdev:plan     → PLAN_APPROVED
/quickdev:execute  → COMPLETED | VERIFICATION_MANUAL_REQUIRED | BLOCKED
/quickdev:review   → REVIEWED | CHANGES_REQUIRED | NO_CHANGES
```

| Skill | Yang dilakukan |
|---|---|
| `profile` | Mendeteksi tipe repo (backend/frontend/fullstack satu paket), menulis profil 6 seksi dari template, dan menjalankan baseline perintah di commit yang dicatat (`Baseline-Commit`). Mode `GENERATE`/`REFRESH`. |
| `explore` | Menelusuri kode untuk satu `query` sampai `trace_depth` (1–4), dengan skala `kecil` (≤2 berkas, tanpa kontrak/skema/env) atau `standar`. Tanpa tool `Glob`/`Grep`, memakai `git ls-files`/`grep`. Menawarkan `clarify`, atau `plan` bila tidak ada celah. |
| `clarify` | Maksimal `batch_limit` pertanyaan per batch (default 3, maksimal 4) dan 3 batch per pemanggilan. Melewati dirinya (`SKIPPED`) bila spesifikasi sudah jelas. |
| `plan` | Menulis `plan/<task>.md` sebagai `DRAFT`, lalu menguncinya (`plan_lock.py lock`) menjadi `APPROVED` hanya dengan persetujuan eksplisit user. |
| `execute` | Menjalankan langkah rencana `APPROVED` yang lolos `verify`, memverifikasi terhadap baseline yang terikat `Base-Commit`, dan memperbaiki maksimal `max_fix_iterations` kali di berkas rencana saja. |
| `review` | Menilai diff sejak `Base-Commit` terhadap rencana dengan 7 dimensi dan severity `BLOCKER`/`MAJOR`/`MINOR`. Hanya laporan di terminal. |

- **`execute`**: `COMPLETED` membuka `review`. `VERIFICATION_MANUAL_REQUIRED` menahan `review` sampai user
  menjalankan perintah manual dan `/quickdev:execute` (mode `manual`) mencatat konfirmasinya. `BLOCKED` tidak
  membuka `review`; user memilih melanjutkan (`/quickdev:execute` lagi → mode `resume`), merevisi lewat
  `/quickdev:plan`, atau rollback.
- **`review`**: `CHANGES_REQUIRED` bila ada minimal satu temuan BLOCKER/MAJOR, atau MINOR dengan
  `strict=true`. Review lalu bertanya: remediasi otomatis (maksimal 2 putaran), revisi rencana, atau terima
  apa adanya. Review tidak memanggil `execute`: opsi pertama menutup review dengan perintah
  `/quickdev:execute <plan_path>` untuk diketik user di sesi yang sama, dan `execute` mengambil temuan dari
  laporan itu sebagai `review_findings`.

`execute` menurunkan mode dari berkas rencana (`plan_lock.py start`), tanpa parameter tambahan:

| Keadaan rencana | Mode |
|---|---|
| belum ada blok `## Execution Status`, nol `[x]` | `awal` — `start` sendiri menolak tree kotor di luar direktori rencana dan profil (atau direktori bukan git) **sebelum** menulis apa pun; lalu baseline segar bila profil diukur di commit lain |
| blok `IN_PROGRESS`/`BLOCKED`, ada `[x]` tanpa blok, blok terminal dengan langkah `[ ]` baru (rencana direvisi), atau segel penutup basi (kode/rencana berubah sesudah `close`) | `resume` — kerja parsial uncommitted diizinkan; semua `[x]` → langsung verifikasi |
| blok `IN_PROGRESS`/`BLOCKED` dengan `Remediation-State: OPEN` | `remediasi` lanjutan — ronde yang terputus, temuan dicetak ulang, ronde tidak bertambah |
| blok `COMPLETED` + `review_findings` | `remediasi` — plafon 2 putaran |
| blok `VERIFICATION_MANUAL_REQUIRED`, semua langkah `[x]`, segel cocok | `manual` — mencatat konfirmasi user |
| blok `COMPLETED`, semua langkah `[x]`, segel cocok, tanpa temuan | `selesai` — tawarkan `review` |

`start` juga mencetak `PERINGATAN:` bila `Base-Commit` bukan lagi leluhur HEAD (rebase, amend, pindah branch);
review lalu meminta `base_ref` sebelum membaca diff.

## Artefak

**Profil** — `repo-profile.md` di root repo, atau `<workspace_dir>/repo-profile.md` per workspace monorepo
(`target_path`; alternatif yang dikenali skill hilir: `.dev/profile.md`). Berisi 6 seksi dari template
backend, frontend, atau fullstack, di bawah 10.000 karakter (`wc -m`). Section 1 mencatat `Workspace`;
Section 5 berupa baris `Baseline-Commit` dan tabel baseline (Perintah, Cwd, Status, Durasi, Known issues).
Profil ini terpisah dari `.claude/profile/<plugin>/` milik backend/frontend dan tidak bertabrakan
dengannya.

Baseline (`profile` Fase 2) meminta izin lewat satu pertanyaan sebelum menjalankan apa pun, dengan opsi
jalankan semua, lewati yang menyentuh DB/jaringan, atau lewati semua. Setiap perintah dibatasi timeout 5
menit, dan statusnya dicatat sebagai `PASSED`, `FAILED`, `TIMEOUT`, `SKIPPED` (beserta alasannya), atau
`UNVERIFIED_ENV_NOT_READY`; jenis tanpa runner di manifest dicatat `TIDAK_ADA`. Migrasi dan perintah yang
mengubah skema/data tidak pernah dijalankan, di `profile` maupun `execute`. Berkas baru yang muncul sesudah
baseline dilaporkan sebagai "artefak build perlu di-ignore", tidak dihapus.

`execute` membandingkan hasil verifikasinya dengan pembanding yang terikat commit: baseline segar yang
dikunci `plan_lock.py baseline` di `Base-Commit` (mode `awal`, sebelum mutasi), atau profil bila
`Baseline-Commit`-nya sama dengan `Base-Commit` dan diukur di tree bersih (`start` mencetak `PEMBANDING:`).
Profil yang diukur di commit lain atau di tree kotor hanya memvonis berkas yang
disentuh rencana; galat lain dicatat `UNVERIFIED`. Galat dicocokkan per berkas + aturan/nama test tanpa nomor
baris. Perintah yang ditolak user di `profile` hanya dijalankan `execute` sesudah izin baru.

**Rencana** — `plan/<task>.md` (`plan_dir`, `task_name` kebab-case):

```markdown
# Implementation Plan — user-auth-jwt
Status: APPROVED                       ← hanya ditulis plan_lock.py lock
Author: quickdev:plan
Date: <ISO>
Profile: repo-profile.md               ← dibaca execute/review lintas sesi; ikut disidik
Gates: explore=EXPLORED clarify=SKIPPED
Hash-Scope: profile+body               ← ditulis lock
Approved-At: <ISO>                     ← ditulis lock
Approval: "setuju, lanjut"              ← jawaban user apa adanya
Plan-Hash: sha256:<64 hex>             ← sidik Profile: + Section 1–5

## 1. Overview & Objectives
## 2. Architecture & Layer Impact
## 3. Atomic Implementation Steps      ← checklist - [ ], dicentang execute
## 4. Verification & Testing Strategy
## 5. Rollback & Contingency Strategy  ← bila include_rollback

## Execution Status                    ← ditulis plan_lock.py start/baseline/close/confirm
- Status: COMPLETED
- Base-Commit: <sha | none>            ← pembanding diff review, tidak pernah ditimpa
- Remediation-Round: 1
- Remediation-State: CLOSED            ← OPEN selama ronde remediasi belum ditutup close
- Findings-1: "<temuan ringkas>"
- Baseline: "<ringkasan per perintah>" ← baseline segar, sah hanya di Base-Commit
- Baseline-Commit: <sha>
- Verification: "<ringkasan>"
- Blocked-Step: -
- Verified-Hash: sha256:<64 hex>       ← Plan-Hash saat close
- Tree-Hash: sha256:<64 hex>           ← isi berkas yang berbeda dari Base-Commit saat close
- Timestamp: <ISO>
```

Sidik mencakup baris `Profile:` dan `## 1.` sampai sebelum `## Execution Status`, dengan checkbox
dinormalkan; heading dan checklist di dalam code fence diabaikan. Centang langkah dan blok eksekusi boleh
berubah; teks Section 1–5 dan `Profile:` tidak. `execute` dan `review` menolak rencana yang sidiknya berbeda
(`plan_lock.py verify`). Rencana yang dikunci 0.4.0 (tanpa `Hash-Scope`) tetap diverifikasi dengan rumus
lamanya (Section 1–5 saja). Revisi sesudah approval: `plan_lock.py unlock` → revisi → approval ulang
(`lock`); blok eksekusi dipertahankan, dan langkah yang teksnya berubah dikembalikan ke `[ ]`. Rencana format
lama (tanpa `Plan-Hash`) perlu disetujui ulang. Nama yang sudah dipakai ditawarkan sebagai `<task>-v2`.

`close` (`COMPLETED`/`VERIFICATION_MANUAL_REQUIRED`) menyegel `Verified-Hash` dan `Tree-Hash`. Kode atau
rencana yang berubah sesudahnya membuat `status` tidak konsisten (review menolak), `confirm` gagal, dan
`start` berikutnya masuk `resume` untuk verifikasi ulang. Commit sesudah `close` tidak membatalkan segel
karena sidiknya berbasis isi berkas, bukan riwayat.

**Memanggil `plan_lock.py`** — teks bebas (`--answer`, `--reason`, `--verification`, `--findings-text`,
`--summary`) bernilai `-` dibaca dari stdin, satu per panggilan. SKILL mengirimnya lewat heredoc berkutip
supaya shell tidak mengekspansi backtick atau `$`:

```
python3 <plugin>/skills/_common/plan_lock.py lock --plan plan/user-auth-jwt.md --answer - <<'QD_EOF'
setuju, pakai `jose` dan $JWT_SECRET dari env
QD_EOF
```

## Git

**`repo-profile.md` dan `plan/` di-commit ke repo.** Profil adalah pengetahuan repo yang dipakai ulang
lintas sesi, dan rencana adalah jejak keputusan: apa yang disetujui, apa yang dieksekusi, dan hasil
verifikasinya. Jangan masukkan keduanya ke `.gitignore`.

quickdev sendiri tidak pernah meng-commit. Commit dan merge adalah keputusan user:

- **`execute`** tidak meng-commit dan tidak merge. Perubahan sengaja dibiarkan uncommitted untuk `review`.
  Pada putaran awal, `plan_lock.py start` menolak working tree (`git status --porcelain -uall`) yang memuat
  berkas selain direktori rencana dan profil, sebelum mencatat `Base-Commit`; commit atau stash perubahan
  lain dulu, lalu panggil `/quickdev:execute` lagi. Kerja parsial sesudah `BLOCKED` atau sesi putus tidak
  perlu di-commit: `resume` melanjutkannya dan `review` membandingkan terhadap `Base-Commit`. Rollback
  (`git checkout`, `reset`, `stash`, hapus berkas) hanya dengan persetujuan user.
- **`review`** read-only: hanya `git diff`, `git status`, `git log`, `git ls-files`, `git rev-parse`, dan
  `plan_lock.py verify`/`status`. Berkas untracked ikut dinilai. Diff dihitung sejak `Base-Commit` (tree
  kosong di repo tanpa commit), jadi hasil `execute` yang sudah di-commit tetap ter-review; `base_ref`
  mengganti pembandingnya.
- Urutan yang disarankan: `plan` → commit rencana `APPROVED` → `execute` → `review` → commit kode bersama
  blok penutup rencana.

## Parameter Penting

| Skill | Parameter | Default |
|---|---|---|
| `profile` | `target_path` · `mode` · `skip_baseline_exec` · `workspace_dir` (monorepo: satu profil per workspace) | `repo-profile.md` · `GENERATE` · `false` · ditanyakan |
| `explore` | `query` (wajib) · `scope_dir` · `trace_depth` · `include_tests` | — · repo · `2` (skala kecil: `1`) · `true` |
| `clarify` | `skip_if_clear` · `batch_limit` · `allow_assumptions` | `true` · `3` · `false` |
| `plan` | `task_name` · `plan_dir` · `require_test_plan` · `include_rollback` | diturunkan lalu dikonfirmasi · `plan` · `true` (`false` bila Test profil `TIDAK_ADA`) · `true` |
| `execute` | `plan_path` · `auto_verify` · `strict_baseline` · `fresh_baseline` · `stop_on_error` · `update_plan_checklist` · `max_fix_iterations` · `review_findings` | dari percakapan atau `plan/*.md` · `true` · `true` · `true` · `true` · `true` · `3` · laporan review terakhir |
| `review` | `plan_path` · `scope_paths` · `strict` · `include_staged` · `base_ref` | dari percakapan atau `plan/*.md` · semua · `false` · `true` · `Base-Commit` |

`plan`, `execute`, dan `review` berhenti dan mengarahkan ke `/quickdev:profile` bila profil tidak ada.
`explore` dan `clarify` tetap jalan dengan heuristik, dan bertanya bila repo punya lebih dari satu
`repo-profile.md`. `execute` dan `review` membaca path profil dari metadata `Profile:` rencana.

## Hidup Berdampingan

Hook SessionStart `backend` dan `frontend` menyuntik gerbangnya di repo yang manifestnya cocok. Teks
gerbang keduanya mengecualikan permintaan yang memanggil atau melanjutkan `/quickdev:*`, termasuk susulan di
tengah skill quickdev. Setiap skill quickdev juga:

- dilarang memakai `backend:*`/`frontend:*` sebagai pengganti langkahnya;
- lanjut bila user memanggil `/quickdev:*` secara eksplisit walaupun blok gerbang engineer ada;
- bertanya sekali (quickdev atau gerbang engineer) untuk permintaan baru yang belum memilih alur.

Untuk repo yang sepenuhnya memakai quickdev, tulis penanda `.claude/workflow`. `/quickdev:profile` Fase 4
menawarkannya bila blok gerbang engineer ada di konteks sesi, dan hanya menulisnya dengan persetujuan user.
Isinya nama plugin yang boleh menggerbangi repo, dipisah spasi, koma, atau baris:

| Isi `.claude/workflow` | Efek |
|---|---|
| `quickdev` | hook backend dan frontend diam |
| `frontend quickdev` | hanya hook frontend yang menyala |
| (berkas tidak ada) | perilaku normal |

Bila berkas ada tetapi tidak memuat `quickdev`, skill quickdev melapor dan bertanya dulu sebelum lanjut.

## Sinkron nataflow (opsional)

Rencana dan profil dapat dicerminkan ke nataflow. Berkas di disk tetap satu-satunya sumber kebenaran: sinkron
tidak menulis berkas apa pun, sehingga `Plan-Hash`, `Verified-Hash`, dan `Tree-Hash` tidak basi.

- **Aktif per repo** lewat `.claude/nataflow.json` (ter-commit, dibaca juga oleh `analyst`, `backend`, dan
  `frontend`): `mcp_server` (default `nataflow-api`), `workspaces` (objek alias → UUID workspace;
  kosong → workspace milik key, satu entri → otomatis, lebih dari satu → user memilih saat task baru atau
  dokumen repo disinkron), `pic_id` (UUID), dan `repo` (default: remote `origin` ternormalisasi). Berkas absen → dilewati; ada
  tetapi rusak → `GAGAL`. Server MCP nataflow didaftarkan user di Claude Code; plugin tidak menyimpan key.
- **Jangkar**: satu rencana = satu workdir `quickdev:<repo>:<path rencana>` bernama `<task_name>`, tertaut ke task
  yang dibuat dari H1 dan Section 1 rencana. Rencana didorong sebagai dokumen `quickdev.plan`; `repo-profile.md`
  sebagai dokumen `profile` di bawah workspace.
- **Kapan**: `plan` sesudah `LOCK PASS` dan sesudah `unlock` (cermin menjadi `DRAFT`); `execute` sesudah tiap
  `close`/`confirm`; `profile` sesudah profil tertulis. Rencana yang belum pernah dikunci tidak didorong.
- **Status**: workdir `active`, `blocked` (`BLOCKED`), atau `done` (`COMPLETED`, `COMPLETED (manual)`); task naik
  ke `in_progress` begitu eksekusi dimulai dan `done` saat selesai, tanpa pernah diturunkan.
- **Hemat token**: `plan_lock.py sync-payload` menyusun seluruh argumen dalam dua fase. Isi dokumen hanya
  diterbitkan bila sha, tipe, atau metadatanya berbeda dari manifest `list_document` remote.
- **Gagal tidak memblokir**: ringkasan skill memuat baris `NATAFLOW: <… | dilewati | GAGAL: <sebab>>`, dan
  status terminal tidak berubah. Ulangi lewat `/quickdev:plan` ("sinkron ulang `plan/<task>.md`").
- **Tidak didorong**: laporan terminal `explore`, `clarify`, dan `review`.

## Keterbatasan yang Diketahui

- **Kunci rencana adalah bukti audit, bukan pencegahan mutlak.** Model tetap bisa memanggil `unlock` lalu
  `lock` sendiri. `lock` menuntut jawaban user dan `unlock` menuntut alasan; keduanya tercatat di metadata
  (`Approval:`, `Unlock-Reason:`). Commit rencana `APPROVED` sebelum `execute` supaya riwayatnya terlihat.
- **Temuan review lintas sesi hanya ringkasan.** `Findings-<n>` dipotong 300 karakter dan `Baseline` 600
  karakter; rincian temuan ada di laporan terminal `review`, yang tidak menulis berkas. Remediasi otomatis
  paling andal bila `/quickdev:execute` diketik di sesi yang sama dengan review.
- **`Tree-Hash` hanya menilai berkas ter-track yang berbeda dari `Base-Commit` dan berkas untracked yang
  tidak di-ignore.** Isi submodule dan berkas ter-ignore (mis. `dist/`) tidak ikut disegel.
- **Independensi review bergantung sesi.** Review di sesi yang sama dengan `execute` ditandai
  `sesi-sama=ya`; jalankan ulang `/quickdev:review` di sesi baru untuk putaran terakhir.
