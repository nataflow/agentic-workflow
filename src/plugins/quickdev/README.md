# quickdev

Alur kerja ringan untuk repo backend, frontend, dan fullstack, terutama repo kecil yang masih awal development:
tiga skill tanpa taskdir, tanpa subagent, tanpa hook, tanpa profil repo, dan dengan satu skrip
(`skills/_common/plan_lock.py`, pengunci rencana, beserta pustaka sinkron `nataflow_sync.py`). Setiap tugas punya
**satu berkas rencana** (`plan/<task>.md`), sedangkan perubahan kodenya boleh menyentuh banyak berkas dan layer.
Semua kerja berlangsung di percakapan utama.

## Kapan Dipakai

- Repo kecil di awal development, yang belum punya konvensi layer mapan dan belum perlu profil repo.
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

Prasyarat: `git` (execute dan review menuntut repo git), `python3` (3.12+, hanya stdlib) untuk
`plan_lock.py`, dan toolchain repo sendiri untuk baseline dan verifikasi. Pindah dari 0.11: lihat
`MIGRATION_v0.11.x_to_v0.12.0.md`; dari 0.12: `MIGRATION_v0.12.x_to_v0.13.0.md`; dari 0.13:
`MIGRATION_v0.13.x_to_v0.14.0.md`; dari 0.14: `MIGRATION_v0.14.x_to_v0.15.0.md`; dari 0.15:
`MIGRATION_v0.15.x_to_v0.16.0.md`.

## Tiga Skill

Alur dimulai user dengan `/quickdev:plan` (satu-satunya skill ber-`disable-model-invocation: true`), lalu
berantai tanpa jeda konfirmasi tambahan:

- Gerbang approval rencana punya tiga opsi: *Setujui & eksekusi* · *Setujui saja* · *Revisi*. Kedua opsi setuju
  mengunci berkas rencana; *Setujui & eksekusi* langsung memanggil `quickdev:execute`.
- `execute` yang ditutup `COMPLETED` langsung memanggil `quickdev:review` dan melaporkan temuannya.
- `review` yang `REVIEWED` (atau `CHANGES_REQUIRED` yang diterima apa adanya) menawarkan commit hasilnya: branch
  aktif · branch baru · jangan dulu.
- `review` yang punya temuan (`CHANGES_REQUIRED`, atau `REVIEWED` dengan temuan MINOR) menawarkan *Perbaiki semua
  temuan* sebagai opsi utama; memilihnya langsung memanggil `quickdev:execute` (remediasi), lalu review ulang (sejak 0.16, Q5).
- Status lain (`VERIFICATION_MANUAL_REQUIRED`, `BLOCKED`) tetap berhenti dan menunggu user. `execute` dan `review` juga tetap bisa diketik langsung (`/quickdev:execute`, `/quickdev:review`).

Rantai ini aman karena gerbangnya ada di skrip, bukan di frontmatter: `execute` ditolak `plan_lock.py
verify`/`start` tanpa rencana `APPROVED` bersidik cocok, dan `review` ditolak tanpa status `COMPLETED` yang konsisten.

```
/quickdev:plan     → PLAN_APPROVED
/quickdev:execute  → COMPLETED | VERIFICATION_MANUAL_REQUIRED | BLOCKED
/quickdev:review   → REVIEWED | CHANGES_REQUIRED | NO_CHANGES
```

| Skill | Yang dilakukan |
|---|---|
| `plan` | Membaca manifest (tipe repo dan perintah verifikasi), menelusuri kode terkait dengan skala `kecil` (≤2 berkas, tanpa kontrak/skema/env) atau `standar`, mengklarifikasi celah (fast-path bila nol celah; maksimal `batch_limit` pertanyaan per batch dan 2 batch), lalu menulis `plan/<task>.md` sebagai `DRAFT` dan menguncinya (`plan_lock.py lock`) menjadi `APPROVED` hanya dengan persetujuan eksplisit user. Tidak menjalankan perintah verifikasi apa pun dan tidak meng-commit apa pun. |
| `execute` | Menjalankan langkah rencana `APPROVED` yang lolos `verify`, mengukur baseline segar di `Base-Commit` sebelum mutasi pertama, memverifikasi dengan perintah Section 4 rencana, dan memperbaiki maksimal `max_fix_iterations` kali di berkas rencana saja. |
| `review` | Menilai diff sejak `Base-Commit` terhadap rencana dan konvensi kode di sekitarnya dengan 7 dimensi dan severity `BLOCKER`/`MAJOR`/`MINOR`, lalu menawarkan commit hasil eksekusi (`plan_lock.py commit`) atas pilihan user. Tidak mengubah isi berkas. |

- **`execute`**: `COMPLETED` membuka `review`. `VERIFICATION_MANUAL_REQUIRED` menahan `review` sampai user
  menjalankan perintah manual dan `/quickdev:execute` (mode `manual`) mencatat konfirmasinya. `BLOCKED` tidak
  membuka `review`; user memilih melanjutkan (`/quickdev:execute` lagi → mode `resume`), merevisi lewat
  `/quickdev:plan`, atau rollback.
- **`review`**: `CHANGES_REQUIRED` bila ada minimal satu temuan BLOCKER/MAJOR, atau MINOR dengan
  `strict=true`. Review lalu bertanya: perbaiki semua temuan (maksimal 2 putaran remediasi), revisi rencana, atau
  terima apa adanya (lanjut ke tawaran commit). `REVIEWED` dengan temuan MINOR mengajukan satu pertanyaan gabungan:
  perbaiki semua temuan minor · commit di branch aktif · commit di branch baru · jangan dulu. Pilihan perbaiki
  langsung memanggil `quickdev:execute`, yang mengambil temuan dari laporan itu sebagai `review_findings` lalu
  memanggil review ulang sesudah `COMPLETED`.

`execute` menurunkan mode dari berkas rencana (`plan_lock.py start`), tanpa parameter tambahan:

| Keadaan rencana | Mode |
|---|---|
| belum ada blok `## Execution Status`, nol `[x]` | `awal` — `start` sendiri menolak tree kotor di luar direktori rencana (atau direktori bukan git) **sebelum** menulis apa pun; bila seluruh kotoran adalah hasil rencana lain yang sudah `COMPLETED`, baris `MILIK:` membuat `execute` menawarkan commit hasil itu dulu. Lalu baseline segar sebelum mutasi pertama |
| blok `IN_PROGRESS`/`BLOCKED`, ada `[x]` tanpa blok, blok terminal dengan langkah `[ ]` baru (rencana direvisi), atau segel penutup basi (kode/rencana berubah sesudah `close`) | `resume` — kerja parsial uncommitted diizinkan; semua `[x]` → langsung verifikasi |
| blok `IN_PROGRESS`/`BLOCKED` dengan `Remediation-State: OPEN` | `remediasi` lanjutan — ronde yang terputus, temuan dicetak ulang, ronde tidak bertambah |
| blok `COMPLETED` + `review_findings` | `remediasi` — plafon 2 putaran |
| blok `VERIFICATION_MANUAL_REQUIRED`, semua langkah `[x]`, segel cocok | `manual` — mencatat konfirmasi user |
| blok `COMPLETED`, semua langkah `[x]`, segel cocok, tanpa temuan | `selesai` — tawarkan `review` |

`start` juga mencetak `PERINGATAN:` bila `Base-Commit` bukan lagi leluhur HEAD (rebase, amend, pindah branch);
review lalu meminta `base_ref` sebelum membaca diff.

## Artefak

**Rencana** — `plan/<task>.md` (`plan_dir`, `task_name` kebab-case), satu-satunya artefak quickdev, diabaikan git
(lihat Git):

```markdown
# Implementation Plan — user-auth-jwt
Status: APPROVED                       ← hanya ditulis plan_lock.py lock
Author: quickdev:plan
Date: <ISO>
Approved-At: <ISO>                     ← ditulis lock
Approval: "setuju, lanjut"              ← jawaban user apa adanya
Hash-Scope: body                       ← ditulis lock
Plan-Hash: sha256:<64 hex>             ← sidik Section 1–5
Nataflow-Task: <uuid>                  ← task acuan; hanya ditulis plan_lock.py task --plan

## 1. Overview & Objectives            ← tujuan, keputusan klarifikasi, asumsi, out of scope
## 2. Architecture & Layer Impact      ← modul disentuh berbukti path:baris, berkas acuan konvensi
## 3. Atomic Implementation Steps      ← checklist - [ ], dicentang execute
## 4. Verification & Testing Strategy  ← tabel | Jenis | Perintah | Cwd | Risiko | + skenario test
## 5. Rollback & Contingency Strategy  ← bila include_rollback

## Execution Status                    ← ditulis plan_lock.py start/baseline/close/summary/confirm
- Status: COMPLETED
- Base-Commit: <sha | none>            ← pembanding diff review, tidak pernah ditimpa
- Remediation-Round: 1
- Remediation-State: CLOSED            ← OPEN selama ronde remediasi belum ditutup close
- Findings-1: "<temuan ringkas>"
- Baseline: "<ringkasan per perintah>" ← baseline segar, sah hanya di Base-Commit
- Baseline-Commit: <sha>
- Verification: "<ringkasan>"
- Summary: "<1–3 kalimat hasil>"       ← ditulis summary sesudah close; pembuka report nataflow
- Blocked-Step: -
- Verified-Hash: sha256:<64 hex>       ← Plan-Hash saat close
- Tree-Hash: sha256:<64 hex>           ← isi berkas yang berbeda dari Base-Commit saat close
- Timestamp: <ISO>
```

**Perintah verifikasi** — `plan` membaca `scripts`/konfigurasi runner di manifest dan menulis tabel Section 4
(typecheck, lint, test, build). Jenis tanpa runner dicatat `TIDAK_ADA`, bukan dikarang. Kolom Risiko menandai
`menyentuh DB/jaringan` (test integrasi yang membaca `.env`, docker-compose, Testcontainers, `DATABASE_URL`) dan
`menulis artefak` (build). Karena Section 4 ikut disidik, perintahnya terkunci saat approval. Persetujuan rencana
mencakup izin menjalankan perintah itu, kecuali yang bertanda `menyentuh DB/jaringan`: `execute` menanyakannya
sekali sebelum dijalankan. Migrasi dan perintah yang mengubah skema/data tidak pernah dijalankan.

**Baseline** — `execute` mode `awal` selalu menjalankan perintah Section 4 di `Base-Commit` sebelum mutasi
pertama, lalu menguncinya lewat `plan_lock.py baseline` (`Baseline`, `Baseline-Commit`). Setiap perintah dibatasi
timeout 5 menit. Hasil verifikasi dibandingkan dengan baseline itu, per berkas + aturan/nama test tanpa nomor
baris. Tanpa baseline tercatat (mis. sesi putus sebelum baseline terkunci), galat di berkas rencana dihitung
regresi dan sisanya dicatat `UNVERIFIED`.

**Sidik** — mencakup `## 1.` sampai sebelum `## Execution Status`, dengan checkbox dinormalkan; heading dan
checklist di dalam code fence diabaikan. Centang langkah dan blok eksekusi boleh berubah; teks Section 1–5 tidak.
`execute` dan `review` menolak rencana yang sidiknya berbeda (`plan_lock.py verify`). Rencana lama tetap
diverifikasi dengan rumusnya: tanpa `Hash-Scope` (0.4.0) = Section 1–5, `Hash-Scope: profile+body` (0.5–0.11) =
Section 1–5 ditambah baris `Profile:`. Revisi sesudah approval: `plan_lock.py unlock` → revisi → approval ulang
(`lock`); blok eksekusi dipertahankan, dan langkah yang teksnya berubah dikembalikan ke `[ ]`. Rencana format
lama (tanpa `Plan-Hash`) perlu disetujui ulang. Nama yang sudah dipakai ditawarkan sebagai `<task>-v2`.

`close` (`COMPLETED`/`VERIFICATION_MANUAL_REQUIRED`) menyegel `Verified-Hash` dan `Tree-Hash`. Kode atau
rencana yang berubah sesudahnya membuat `status` tidak konsisten (review menolak), `confirm` gagal, dan
`start` berikutnya masuk `resume` untuk verifikasi ulang. Commit sesudah `close` tidak membatalkan segel
karena sidiknya berbasis isi berkas, bukan riwayat.

**Memanggil `plan_lock.py`** — teks bebas (`--answer`, `--reason`, `--verification`, `--findings-text`,
`--summary`, `--message`) bernilai `-` dibaca dari stdin, satu per panggilan. SKILL mengirimnya lewat heredoc berkutip
supaya shell tidak mengekspansi backtick atau `$`:

```
python3 <plugin>/skills/_common/plan_lock.py lock --plan plan/user-auth-jwt.md --answer - <<'QD_EOF'
setuju, pakai `jose` dan $JWT_SECRET dari env
QD_EOF
```

## Git

**`plan/` tidak di-commit.** `plan_lock.py lock` (dan `start` untuk rencana yang dikunci versi lama) menulis
penanda `plan/.gitignore` berisi `*`, yang ikut mengabaikan dirinya sendiri, sehingga rencana tidak pernah muncul
di `git status` maupun di commit; `.gitignore` akar repo tidak disentuh. Jejak keputusan (rencana, report, status
task) dicerminkan ke nataflow; tanpa `.claude/nataflow.json` rencana hanya ada di disk itu, dan `lock` mengingatkannya.
Penanda tidak ditulis bila direktori rencana sudah diabaikan, bila rencana ada di root repo, atau bila direktorinya
memuat berkas ter-track selain rencana quickdev (mis. `plan_dir=docs`). Rencana yang sudah ter-track di repo lama
tetap ter-track dan ikut commit kode; melepasnya dari git dijelaskan di `MIGRATION_v0.14.x_to_v0.15.0.md`.

Satu-satunya commit quickdev adalah hasil eksekusi, dan hanya atas pilihan eksplisit user:

- **`plan`** tidak meng-commit, men-stage, atau men-stash apa pun.
- **`execute`** tidak meng-commit hasilnya sendiri. Perubahan sengaja dibiarkan uncommitted untuk `review`.
  Pada putaran awal, `plan_lock.py start` menolak working tree (`git status --porcelain -uall`) yang memuat
  berkas selain direktori rencana, sebelum mencatat `Base-Commit`. Bila seluruh berkas itu hasil rencana lain di
  direktori yang sama yang sudah `COMPLETED` dengan segel cocok (task sebelumnya belum di-commit), `start` menambah
  baris `MILIK: <rencana>` dan `execute` menawarkan commit hasil rencana itu dulu; selain itu commit atau stash
  perubahan lain dulu, lalu panggil `/quickdev:execute` lagi. Kerja parsial sesudah `BLOCKED` atau sesi putus tidak
  perlu di-commit: `resume` melanjutkannya dan `review` membandingkan terhadap `Base-Commit`. Rollback (`git
  checkout`, `reset`, `stash`, hapus berkas) hanya dengan persetujuan user.
- **`review`** menilai tanpa mengubah berkas: hanya `git diff`, `git status`, `git log`, `git ls-files`, `git
  rev-parse`, dan `plan_lock.py verify`/`status`. Berkas untracked ikut dinilai. Diff dihitung sejak `Base-Commit`
  (tree kosong di repo tanpa commit), jadi hasil `execute` yang sudah di-commit tetap ter-review; `base_ref`
  mengganti pembandingnya. Sesudah `REVIEWED` (atau *Terima apa adanya*), review menawarkan *Commit di branch aktif*
  · *Commit di branch baru* · *Jangan dulu*, dengan subjek usulan `<feat|fix>: <tujuan Section 1> (#<kode task>)`.
- **`plan_lock.py commit --plan <p> --message - [--branch <nama>]`** hanya sah untuk eksekusi `COMPLETED` yang
  segelnya cocok, dan hanya men-stage berkas yang disegel `close` (berbeda dari `Base-Commit`, tanpa direktori
  rencana) yang masih uncommitted, ditambah berkas rencana bila masih ter-track. Index lain milik user tidak ikut
  (`--only`), hook git tidak dilewati, dan `--branch` membuat branch baru dari HEAD lebih dulu (nama yang sudah ada
  ditolak). `COMMIT SKIP` bila semua sudah ter-commit; `COMMIT GAGAL` (hook, gpg, identitas) mencetak perintah
  manualnya. Segel `close` tetap cocok sesudah commit karena sidiknya berbasis isi berkas.
- Urutan git: `plan` (tanpa commit) → `execute` → `review` → commit hasil atas pilihan user. Merge dan push milik
  user.

## Parameter Penting

| Skill | Parameter | Default |
|---|---|---|
| `plan` | `task_name` · `task_spec` · `plan_dir` · `target_dir` (monorepo) · `trace_depth` · `batch_limit` · `require_test_plan` · `include_rollback` | diturunkan lalu dikonfirmasi · permintaan user · `plan` · ditanyakan · `2` (skala kecil: `1`) · `3` · `true` (`false` bila Test `TIDAK_ADA`) · `true` |
| `execute` | `plan_path` · `auto_verify` · `strict_baseline` · `stop_on_error` · `update_plan_checklist` · `max_fix_iterations` · `review_findings` | dari percakapan atau `plan/*.md` · `true` · `true` · `true` · `true` · `3` · laporan review terakhir |
| `review` | `plan_path` · `scope_paths` · `strict` · `include_staged` · `base_ref` | dari percakapan atau `plan/*.md` · semua · `false` · `true` · `Base-Commit` |

## Hidup Berdampingan

Hook SessionStart `backend` dan `frontend` menyuntik gerbangnya di repo yang manifestnya cocok. Teks
gerbang keduanya mengecualikan permintaan yang memanggil atau melanjutkan `/quickdev:*`, termasuk susulan di
tengah skill quickdev. Setiap skill quickdev juga:

- dilarang memakai `backend:*`/`frontend:*` sebagai pengganti langkahnya;
- lanjut bila user memanggil `/quickdev:*` secara eksplisit walaupun blok gerbang engineer ada;
- bertanya sekali (quickdev atau gerbang engineer) untuk permintaan baru yang belum memilih alur.

Untuk repo yang sepenuhnya memakai quickdev, tulis penanda `.claude/workflow`. `/quickdev:plan` Fase 0
menawarkannya bila blok gerbang engineer ada di konteks sesi dan berkas itu belum ada, dan hanya menulisnya
dengan persetujuan user. Isinya nama plugin yang boleh menggerbangi repo, dipisah spasi, koma, atau baris:

| Isi `.claude/workflow` | Efek |
|---|---|
| `quickdev` | hook backend dan frontend diam |
| `frontend quickdev` | hanya hook frontend yang menyala |
| (berkas tidak ada) | perilaku normal |

Bila berkas ada tetapi tidak memuat `quickdev`, skill quickdev melapor dan bertanya dulu sebelum lanjut.

## Sinkron nataflow (opsional)

Rencana dapat dicerminkan ke nataflow. Berkas di disk tetap satu-satunya sumber kebenaran: sinkron tidak menulis
berkas apa pun, sehingga `Plan-Hash`, `Verified-Hash`, dan `Tree-Hash` tidak basi.

- **Aktif per repo** lewat `.claude/nataflow.json` (ter-commit, dibaca juga oleh `analyst`, `backend`, dan
  `frontend`): `url` endpoint MCP (wajib), `workspaces` (objek alias → UUID workspace;
  kosong → workspace milik key, satu entri → otomatis, lebih dari satu → user memilih saat task baru dibuat),
  `pic_id` (UUID), dan `repo` (default: remote `origin` ternormalisasi). Berkas absen → dilewati; ada
  tetapi rusak (termasuk `mcp_server` lama) → `GAGAL`. MCP key di `.claude/nataflow.local.json` (`{"mcp_key": "…"}`, tidak pernah di-commit; di repo git wajib diabaikan git, bila tidak sinkron menolak berjalan). Skrip memanggil server sendiri lewat `url`; server tidak perlu didaftarkan di Claude Code.
- **Jangkar**: satu rencana = satu workdir `quickdev:<repo>:<path rencana>` bernama `<task_name>`. Task induknya
  task nataflow acuan bila user menyebutnya (`#12` atau UUID; dibaca `plan_lock.py task --ref`, ditautkan sebagai
  `Nataflow-Task`, deskripsinya menjadi spesifikasi rencana, dan quickdev tidak membuat task baru maupun mengubah
  isinya), atau task milik quickdev yang dibuat dari H1 dan Section 1 rencana dan diselaraskan bila draf direvisi.
  Rencana didorong sebagai dokumen `quickdev.plan`; sesudah eksekusi ditutup, dokumen `quickdev.report`
  (`<task_name>.report.md`) menyusul: ringkasan naratif (`plan_lock.py summary`), AC, checklist, berkas berubah sejak
  `Base-Commit`, verifikasi, dan temuan review. Kedua tipe dokumen wajib terdaftar di server (oleh admin, halaman
  Document Types); skrip memeriksanya lewat `list_document_types` sebelum tulisan apa pun. `quickdev.plan` belum
  terdaftar → `GAGAL` beserta instruksi pendaftaran, `quickdev.report` belum terdaftar → `· report GAGAL: …`.
- **Kapan**: `plan` Fase 4 sebelum draf diajukan untuk approval (dan di tiap revisi), sesudah `LOCK PASS`,
  dan sesudah `unlock` (cermin menjadi `DRAFT`); `execute` sesudah tiap `close`/`confirm`.
- **Status**: workdir `active`, `blocked` (`BLOCKED`), atau `done` (`COMPLETED`, `COMPLETED (manual)`); task baru tetap
  `todo` selama DRAFT, naik ke `in_progress` begitu rencana terkunci, dan `done` saat eksekusi `COMPLETED`, tanpa
  pernah diturunkan. Task acuan baru `done` bila seluruh workdir di bawahnya (mis. taskdir backend/frontend) tuntas.
- **Hemat token**: `plan_lock.py sync-payload --push` memanggil server sendiri; isi dokumen hanya didorong bila
  sha, tipe, atau metadatanya berbeda dari manifest remote, dan tidak pernah lewat konteks model.
- **Gagal**: ringkasan skill memuat baris `NATAFLOW: <task #<kode> · … | dilewati | GAGAL: <sebab>>`. Di Fase 4 `plan`,
  `GAGAL` menahan approval sampai user memilih *Coba lagi* atau *Lanjut tanpa cermin nataflow*; di titik lain status
  terminal tidak berubah. Report yang gagal didorong hanya menambah `· report GAGAL: <sebab>`. Ulangi lewat
  `/quickdev:plan` ("sinkron ulang `plan/<task>.md`"). Ringkasan `execute` dan `review` menyalin segmen ini apa
  adanya, sehingga status sinkron terlihat di akhir rantai.
- **Tidak didorong**: laporan terminal `review` (temuannya masuk report lewat `Findings-<n>` putaran remediasi).

## Keterbatasan yang Diketahui

- **Kunci rencana adalah bukti audit, bukan pencegahan mutlak.** Model tetap bisa memanggil `unlock` lalu
  `lock` sendiri. `lock` menuntut jawaban user dan `unlock` menuntut alasan; keduanya tercatat di metadata
  (`Approval:`, `Unlock-Reason:`). Rencana tidak di-commit, jadi tidak ada riwayat git atas
  revisinya; yang tersisa hanya berkas di disk dan cermin nataflow terakhir.
- **Konteks repo dideteksi ulang di setiap rencana.** Tanpa profil, `plan` membaca manifest dan menelusuri kode
  untuk tiap tugas; murah di repo kecil, berulang di repo besar (untuk repo besar, pertimbangkan `backend`/`frontend`).
- **Temuan review lintas sesi hanya ringkasan.** `Findings-<n>` dipotong 300 karakter dan `Baseline` 600
  karakter; rincian temuan ada di laporan terminal `review`, yang tidak menulis berkas. Remediasi
  berantai langsung di sesi review; remediasi yang diketik user (`/quickdev:execute`) paling andal di sesi yang sama.
- **`Tree-Hash` hanya menilai berkas ter-track yang berbeda dari `Base-Commit` dan berkas untracked yang
  tidak di-ignore.** Isi submodule dan berkas ter-ignore (mis. `dist/`) tidak ikut disegel.
- **Independensi review bergantung sesi.** Review di sesi yang sama dengan `execute` ditandai
  `sesi-sama=ya`, dan rantai otomatis membuat ini keadaan bawaan. Jalankan ulang `/quickdev:review` di sesi
  baru untuk putaran terakhir.
