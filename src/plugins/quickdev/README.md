# quickdev

Alur kerja ringan untuk repo backend dan frontend: enam skill tanpa taskdir, tanpa subagent, tanpa hook, dan
tanpa skrip. Setiap tugas punya **satu berkas rencana** (`plan/<task>.md`), sedangkan perubahan kodenya
boleh menyentuh banyak berkas dan layer. Semua kerja berlangsung di percakapan utama.

## Kapan Dipakai

- Perubahan kecil sampai menengah yang tidak butuh BRD/PRD, ledger approval, atau review subagent.
- Stack yang tidak dilayani `backenddev`/`frontenddev`, mis. Next.js, FastAPI, Django, atau Rails.
- Repo yang sudah memakai `backenddev`/`frontenddev`, untuk kerja yang sengaja dibuat ringan. Panggil
  `/quickdev:*` secara eksplisit (lihat Hidup Berdampingan).

Untuk kerja berisiko (kontrak API, migrasi skema, perubahan lintas modul yang butuh jejak keputusan), pakai
gerbang `backenddev:tech-lead` atau `frontenddev:lead`.

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install quickdev@fakhrulnugroho
```

Prasyarat: `git`, dan toolchain repo sendiri untuk baseline dan verifikasi. quickdev tidak menjalankan skrip
Python sendiri.

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
| `profile` | Mendeteksi tipe repo (backend/frontend), menulis profil 6 seksi dari template, dan menjalankan baseline perintah. Mode `GENERATE`/`REFRESH`. |
| `explore` | Menelusuri kode untuk satu `query` sampai `trace_depth` (1–4). Menawarkan `clarify`, atau `plan` bila tidak ada celah. |
| `clarify` | Maksimal `batch_limit` pertanyaan per putaran (default 3, maksimal 4). Melewati dirinya (`SKIPPED`) bila spesifikasi sudah jelas. |
| `plan` | Menulis `plan/<task>.md` sebagai `DRAFT`, lalu mengubahnya menjadi `APPROVED` hanya dengan persetujuan eksplisit user. |
| `execute` | Menjalankan langkah rencana `APPROVED`, memverifikasi, dan memperbaiki maksimal `max_fix_iterations` kali. |
| `review` | Menilai diff terhadap rencana dengan 7 dimensi dan severity `BLOCKER`/`MAJOR`/`MINOR`. Hanya laporan di terminal. |

- **`execute`**: `COMPLETED` membuka `review`. `VERIFICATION_MANUAL_REQUIRED` menahan `review` sampai user
  mengonfirmasi hasil perintah manual. `BLOCKED` tidak membuka `review`; user memilih melanjutkan perbaikan,
  merevisi lewat `/quickdev:plan`, atau rollback.
- **`review`**: `CHANGES_REQUIRED` bila ada minimal satu temuan BLOCKER/MAJOR, atau MINOR dengan
  `strict=true`. User lalu dapat menjalankan `/quickdev:execute` dengan `review_findings` untuk putaran
  remediasi.

## Artefak

**Profil** — `repo-profile.md` di root repo (`target_path`; alternatif yang dikenali skill hilir:
`.dev/profile.md`). Berisi 6 seksi dari template backend atau frontend, di bawah 10.000 karakter (`wc -m`).
Profil ini terpisah dari `.claude/profile/<plugin>/` milik backenddev/frontenddev dan tidak bertabrakan
dengannya.

Baseline (`profile` Fase 2) meminta izin lewat satu pertanyaan sebelum menjalankan apa pun, dengan opsi
jalankan semua, lewati yang menyentuh DB/jaringan, atau lewati semua. Setiap perintah dibatasi timeout 5
menit, dan statusnya dicatat sebagai `PASSED`, `FAILED`, `TIMEOUT`, `SKIPPED`, atau
`UNVERIFIED_ENV_NOT_READY`. Migrasi dan perintah yang mengubah skema/data tidak pernah dijalankan. Berkas
baru yang muncul sesudah baseline dilaporkan sebagai "artefak build perlu di-ignore", tidak dihapus.

**Rencana** — `plan/<task>.md` (`plan_dir`, `task_name` kebab-case):

```markdown
# Implementation Plan — user-auth-jwt
Status: DRAFT            ← APPROVED hanya sesudah persetujuan eksplisit user
Author: quickdev:plan
Date: <timestamp>

## 1. Overview & Objectives
## 2. Architecture & Layer Impact
## 3. Atomic Implementation Steps      ← checklist - [ ], dicentang execute
## 4. Verification & Testing Strategy
## 5. Rollback & Contingency Strategy  ← bila include_rollback

Execution Status: COMPLETED            ← blok penutup, ditimpa tiap putaran execute
Verification: <ringkasan>
Remediation Round: 0
Timestamp: <ISO-Date>
```

Rencana `APPROVED` tidak ditimpa tanpa instruksi revisi. Nama yang sudah dipakai ditawarkan sebagai
`<task>-v2`.

## Git

**`repo-profile.md` dan `plan/` di-commit ke repo.** Profil adalah pengetahuan repo yang dipakai ulang
lintas sesi, dan rencana adalah jejak keputusan: apa yang disetujui, apa yang dieksekusi, dan hasil
verifikasinya. Jangan masukkan keduanya ke `.gitignore`.

quickdev sendiri tidak pernah meng-commit. Commit dan merge adalah keputusan user:

- **`execute`** tidak meng-commit dan tidak merge. Perubahan sengaja dibiarkan uncommitted untuk `review`.
  Pada putaran awal, working tree harus bersih kecuali `plan_path` dan `profile_path`; commit atau stash
  perubahan lain dulu. Rollback (`git checkout`, `reset`, `stash`, hapus berkas) hanya dengan persetujuan
  user.
- **`review`** read-only: hanya `git diff`, `git status`, `git log`, `git ls-files`, dan `git rev-parse`.
  Berkas untracked ikut dinilai.
- Urutan yang disarankan: `plan` → commit rencana `APPROVED` → `execute` → `review` → commit kode bersama
  blok penutup rencana.

## Parameter Penting

| Skill | Parameter | Default |
|---|---|---|
| `profile` | `target_path` · `mode` · `skip_baseline_exec` · `workspace_dir` (monorepo: satu profil per workspace) | `repo-profile.md` · `GENERATE` · `false` · ditanyakan |
| `explore` | `query` (wajib) · `scope_dir` · `trace_depth` · `include_tests` | — · repo · `2` · `true` |
| `clarify` | `skip_if_clear` · `batch_limit` · `allow_assumptions` | `true` · `3` · `false` |
| `plan` | `task_name` · `plan_dir` · `require_test_plan` · `include_rollback` | diturunkan lalu dikonfirmasi · `plan` · `true` · `true` |
| `execute` | `plan_path` (wajib) · `auto_verify` · `strict_baseline` · `stop_on_error` · `update_plan_checklist` · `max_fix_iterations` · `review_findings` | — · `true` · `true` · `true` · `true` · `3` · kosong |
| `review` | `plan_path` (wajib) · `scope_paths` · `strict` · `include_staged` | — · semua · `false` · `true` |

`plan`, `execute`, dan `review` berhenti dan mengarahkan ke `/quickdev:profile` bila profil tidak ada.
`explore` dan `clarify` tetap jalan dengan heuristik.

## Hidup Berdampingan

Hook SessionStart `backenddev` dan `frontenddev` menyuntik gerbangnya di repo yang manifestnya cocok. Teks
gerbang keduanya mengecualikan permintaan yang memanggil atau melanjutkan `/quickdev:*`, termasuk susulan di
tengah skill quickdev. Setiap skill quickdev juga:

- dilarang memakai `backenddev:*`/`frontenddev:*` sebagai pengganti langkahnya;
- lanjut bila user memanggil `/quickdev:*` secara eksplisit walaupun blok gerbang engineer ada;
- bertanya sekali (quickdev atau gerbang engineer) untuk permintaan baru yang belum memilih alur.

Untuk repo yang sepenuhnya memakai quickdev, tulis penanda `.claude/workflow`. `/quickdev:profile` Fase 4
menawarkannya bila mendeteksi hook engineer aktif, dan hanya menulisnya dengan persetujuan user. Isinya nama
plugin yang boleh menggerbangi repo, dipisah spasi atau baris:

| Isi `.claude/workflow` | Efek |
|---|---|
| `quickdev` | hook backenddev dan frontenddev diam |
| `frontenddev quickdev` | hanya hook frontenddev yang menyala |
| (berkas tidak ada) | perilaku normal |

Bila berkas ada tetapi tidak memuat `quickdev`, skill quickdev melapor dan bertanya dulu sebelum lanjut.

## Keterbatasan yang Diketahui

- **Kunci rencana hanya baris `Status: APPROVED`.** Baris itu ditulis model, dan `review` membandingkan diff
  dengan isi rencana saat review. Suntingan langkah sesudah approval tidak terdeteksi. Commit rencana
  `APPROVED` sebelum `execute` supaya perubahannya terlihat di `git diff`.
- **Tidak ada jalur resume `execute`** sesudah `BLOCKED` atau sesi terputus di tengah eksekusi. `execute`
  hanya menerima tree bersih (putaran awal) atau `review_findings` (remediasi). Pilihannya: rollback lalu
  ulangi, atau revisi lewat `/quickdev:plan`.
- **State antargate hidup di percakapan.** Hasil `explore`/`clarify`, `task_spec`, konfirmasi
  `VERIFICATION_MANUAL_REQUIRED`, dan `review_findings` tidak ditulis ke berkas. Sesi baru harus mengulang
  dari `plan` atau menyebut ulang konteksnya.
- Putaran `review` ↔ `execute` belum berplafon. Perbaikan saat verifikasi belum dibatasi ke berkas rencana.
- Pilihan `workspace_dir` monorepo tidak tersimpan lintas sesi.
