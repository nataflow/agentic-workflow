# quickdev

Alur kerja ringan untuk repo backend, frontend, dan fullstack: enam skill tanpa taskdir, tanpa subagent, tanpa
hook, dan dengan satu skrip (`skills/_common/plan_lock.py`, pengunci rencana). Setiap tugas punya **satu berkas rencana** (`plan/<task>.md`), sedangkan perubahan kodenya
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

Prasyarat: `git`, `python3` (3.9+, hanya stdlib) untuk `plan_lock.py`, dan toolchain repo sendiri untuk
baseline dan verifikasi.

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
| `profile` | Mendeteksi tipe repo (backend/frontend/fullstack satu paket), menulis profil 6 seksi dari template, dan menjalankan baseline perintah. Mode `GENERATE`/`REFRESH`. |
| `explore` | Menelusuri kode untuk satu `query` sampai `trace_depth` (1–4), dengan skala `kecil` (≤2 berkas, tanpa kontrak/skema/env) atau `standar`. Tanpa tool `Glob`/`Grep`, memakai `git ls-files`/`grep`. Menawarkan `clarify`, atau `plan` bila tidak ada celah. |
| `clarify` | Maksimal `batch_limit` pertanyaan per batch (default 3, maksimal 4) dan 3 batch per pemanggilan. Melewati dirinya (`SKIPPED`) bila spesifikasi sudah jelas. |
| `plan` | Menulis `plan/<task>.md` sebagai `DRAFT`, lalu menguncinya (`plan_lock.py lock`) menjadi `APPROVED` hanya dengan persetujuan eksplisit user. |
| `execute` | Menjalankan langkah rencana `APPROVED` yang lolos `verify`, memverifikasi terhadap baseline profil, dan memperbaiki maksimal `max_fix_iterations` kali di berkas rencana saja. |
| `review` | Menilai diff sejak `Base-Commit` terhadap rencana dengan 7 dimensi dan severity `BLOCKER`/`MAJOR`/`MINOR`. Hanya laporan di terminal. |

- **`execute`**: `COMPLETED` membuka `review`. `VERIFICATION_MANUAL_REQUIRED` menahan `review` sampai user
  menjalankan perintah manual dan `/quickdev:execute` (mode `manual`) mencatat konfirmasinya. `BLOCKED` tidak
  membuka `review`; user memilih melanjutkan (`/quickdev:execute` lagi → mode `resume`), merevisi lewat
  `/quickdev:plan`, atau rollback.
- **`review`**: `CHANGES_REQUIRED` bila ada minimal satu temuan BLOCKER/MAJOR, atau MINOR dengan
  `strict=true`. Review lalu bertanya: remediasi otomatis (maksimal 2 putaran), revisi rencana, atau terima
  apa adanya. Hanya opsi pertama yang menjalankan `execute` dengan `review_findings`.

`execute` menurunkan mode dari berkas rencana (`plan_lock.py start`), tanpa parameter tambahan:

| Keadaan rencana | Mode |
|---|---|
| belum ada blok `## Execution Status`, nol `[x]` | `awal` — tree harus bersih selain `plan/` dan profil |
| blok `IN_PROGRESS`/`BLOCKED`, atau ada `[x]` tanpa blok, atau blok terminal dengan langkah `[ ]` baru (rencana direvisi sesudah selesai) | `resume` — kerja parsial uncommitted diizinkan |
| blok `COMPLETED` + `review_findings` | `remediasi` — plafon 2 putaran |
| blok `VERIFICATION_MANUAL_REQUIRED`, semua langkah `[x]` | `manual` — mencatat konfirmasi user |
| blok `COMPLETED`, semua langkah `[x]`, tanpa temuan | `selesai` — tawarkan `review` |

## Artefak

**Profil** — `repo-profile.md` di root repo, atau `<workspace_dir>/repo-profile.md` per workspace monorepo
(`target_path`; alternatif yang dikenali skill hilir: `.dev/profile.md`). Berisi 6 seksi dari template
backend, frontend, atau fullstack, di bawah 10.000 karakter (`wc -m`). Section 1 mencatat `Workspace`;
Section 5 berupa tabel baseline (Perintah, Cwd, Status, Durasi, Known issues).
Profil ini terpisah dari `.claude/profile/<plugin>/` milik backend/frontend dan tidak bertabrakan
dengannya.

Baseline (`profile` Fase 2) meminta izin lewat satu pertanyaan sebelum menjalankan apa pun, dengan opsi
jalankan semua, lewati yang menyentuh DB/jaringan, atau lewati semua. Setiap perintah dibatasi timeout 5
menit, dan statusnya dicatat sebagai `PASSED`, `FAILED`, `TIMEOUT`, `SKIPPED`, atau
`UNVERIFIED_ENV_NOT_READY`; jenis tanpa runner di manifest dicatat `TIDAK_ADA`. `execute` membedakan galat
bawaan dari regresi lewat kolom Known issues. Migrasi dan perintah yang mengubah skema/data tidak pernah dijalankan. Berkas
baru yang muncul sesudah baseline dilaporkan sebagai "artefak build perlu di-ignore", tidak dihapus.

**Rencana** — `plan/<task>.md` (`plan_dir`, `task_name` kebab-case):

```markdown
# Implementation Plan — user-auth-jwt
Status: APPROVED                       ← hanya ditulis plan_lock.py lock
Author: quickdev:plan
Date: <ISO>
Profile: repo-profile.md               ← dibaca execute/review lintas sesi
Gates: explore=EXPLORED clarify=SKIPPED
Approved-At: <ISO>                     ← ditulis lock
Approval: "setuju, lanjut"              ← jawaban user apa adanya
Plan-Hash: sha256:<64 hex>             ← sidik Section 1–5

## 1. Overview & Objectives
## 2. Architecture & Layer Impact
## 3. Atomic Implementation Steps      ← checklist - [ ], dicentang execute
## 4. Verification & Testing Strategy
## 5. Rollback & Contingency Strategy  ← bila include_rollback

## Execution Status                    ← ditulis plan_lock.py start/close/confirm
- Status: COMPLETED
- Base-Commit: <sha | none>            ← pembanding diff review, tidak pernah ditimpa
- Remediation-Round: 0
- Verification: "<ringkasan>"
- Blocked-Step: -
- Timestamp: <ISO>
```

Sidik mencakup `## 1.` sampai sebelum `## Execution Status`, dengan checkbox dinormalkan. Centang langkah
dan blok eksekusi boleh berubah; teks Section 1–5 tidak. `execute` dan `review` menolak rencana yang
sidiknya berbeda (`plan_lock.py verify`). Revisi sesudah approval: `plan_lock.py unlock --reason` → revisi →
approval ulang (`lock`); blok eksekusi dipertahankan. Rencana format lama (tanpa `Plan-Hash`) perlu
disetujui ulang. Nama yang sudah dipakai ditawarkan sebagai `<task>-v2`.

## Git

**`repo-profile.md` dan `plan/` di-commit ke repo.** Profil adalah pengetahuan repo yang dipakai ulang
lintas sesi, dan rencana adalah jejak keputusan: apa yang disetujui, apa yang dieksekusi, dan hasil
verifikasinya. Jangan masukkan keduanya ke `.gitignore`.

quickdev sendiri tidak pernah meng-commit. Commit dan merge adalah keputusan user:

- **`execute`** tidak meng-commit dan tidak merge. Perubahan sengaja dibiarkan uncommitted untuk `review`.
  Pada putaran awal, working tree (`git status --porcelain -uall`) harus bersih kecuali `plan/` dan profil;
  commit atau stash perubahan lain dulu. Kerja parsial sesudah `BLOCKED` atau sesi putus tidak perlu
  di-commit: `resume` melanjutkannya dan `review` membandingkan terhadap `Base-Commit`. Rollback (`git checkout`, `reset`, `stash`, hapus berkas) hanya dengan persetujuan
  user.
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
| `execute` | `plan_path` (wajib) · `auto_verify` · `strict_baseline` · `stop_on_error` · `update_plan_checklist` · `max_fix_iterations` · `review_findings` | — · `true` · `true` · `true` · `true` · `3` · kosong |
| `review` | `plan_path` (wajib) · `scope_paths` · `strict` · `include_staged` · `base_ref` | — · semua · `false` · `true` · `Base-Commit` |

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
menawarkannya bila mendeteksi hook engineer aktif, dan hanya menulisnya dengan persetujuan user. Isinya nama
plugin yang boleh menggerbangi repo, dipisah spasi atau baris:

| Isi `.claude/workflow` | Efek |
|---|---|
| `quickdev` | hook backend dan frontend diam |
| `frontend quickdev` | hanya hook frontend yang menyala |
| (berkas tidak ada) | perilaku normal |

Bila berkas ada tetapi tidak memuat `quickdev`, skill quickdev melapor dan bertanya dulu sebelum lanjut.

## Keterbatasan yang Diketahui

- **Kunci rencana adalah bukti audit, bukan pencegahan mutlak.** Model tetap bisa memanggil `unlock` lalu
  `lock` sendiri. `lock` menuntut jawaban user dan `unlock` menuntut alasan; keduanya tercatat di metadata
  (`Approval:`, `Unlock-Reason:`). Commit rencana `APPROVED` sebelum `execute` supaya riwayatnya terlihat.
- **Temuan review lintas sesi hanya ringkasan.** `Findings-<n>` dipotong 300 karakter; rincian ada di
  laporan terminal `review`, yang tidak menulis berkas.
- **Independensi review bergantung sesi.** Review di sesi yang sama dengan `execute` ditandai
  `sesi-sama=ya`; jalankan ulang `/quickdev:review` di sesi baru untuk putaran terakhir.
