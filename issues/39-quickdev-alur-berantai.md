# Langkah 39 — `quickdev`: alur berantai — commit rencana sesudah approve, plan → execute → review tanpa jeda (C1, A1–A3)

Sumber: feedback pemakaian quickdev (2026-11-16): terlalu banyak berhenti untuk konfirmasi user. Basis kode: commit
`3c43b0a` (quickdev 0.12.1).

**Status (2026-11-16):** SELESAI di branch `feat/quickdev-alur-berantai`; quickdev 0.13.0
(`src/plugins/quickdev/MIGRATION_v0.12.x_to_v0.13.0.md`). Test baru: `tests/quickdev/test_39_alur_berantai.py`.
Belum: PR dan uji lapangan.

## Tujuan

Sesudah user menyetujui rencana, rantai `plan → execute → review` berjalan sampai laporan temuan tanpa jeda
konfirmasi, kecuali di titik keputusan nyata.

## Keputusan

- **C1 — commit rencana.** `plan` Fase 5 menjalankan subperintah baru `plan_lock.py commit` sesudah `LOCK PASS` dan
  **sebelum** sinkron nataflow (cermin mencatat sha commit rencana lewat `nataflow_sync.last_commit`). Hanya berkas
  rencana (`add` + `commit --only`), di branch aktif termasuk `main` (keputusan user: skala repo masih kecil), subjek
  `docs(plan): setujui rencana <task>`, hook tidak dilewati. `COMMIT SKIP` (exit 0): bukan repo git, di-ignore, sama
  dengan HEAD, atau blok `## Execution Status` sudah ada (revisi sesudah eksekusi; commit rencana-saja di tengah
  eksekusi hanya menambah `commits_since_base`). `COMMIT GAGAL` (exit 3) tidak membatalkan `PLAN_APPROVED`.
- **A1 — approval tiga opsi.** *Setujui & eksekusi (Recommended)* · *Setujui saja* · *Revisi*. Pertanyaan "lanjut
  eksekusi?" digabung ke gerbang approval supaya tidak menambah satu jeda. *Setujui & eksekusi* memanggil
  `quickdev:execute` lewat tool `Skill`.
- **A2 — execute → review.** `close`/`confirm` yang menghasilkan `COMPLETED`/`COMPLETED (manual)` (termasuk putaran
  remediasi) memanggil `quickdev:review` langsung. `VERIFICATION_MANUAL_REQUIRED` dan `BLOCKED` tetap berhenti.
- **A3 — remediasi tidak berantai** (keputusan user). Review `CHANGES_REQUIRED` tetap menutup dengan perintah
  `/quickdev:execute <plan_path>` untuk diketik user.
- `disable-model-invocation: true` kini hanya di `plan`. Gerbang `execute`/`review` tetap skrip (`verify`, `start`,
  `status --json`), dan description keduanya menolak permintaan tanpa rencana quickdev.

## Trade-off yang diterima

- Review yang dipanggil `execute` selalu `sesi-sama=ya` (menilai kerja sendiri). Tidak dipindah ke subagent supaya
  prinsip quickdev "tanpa subagent" utuh; saran putaran terakhir di sesi baru dipertahankan.
- Commit rencana di `main` tanpa branch.

## Blast radius

`skills/_common/plan_lock.py` (`commit`, `git_error_line`), SKILL `plan`/`execute`/`review`, `README.md`, migrasi
0.13.0, `flow/quickdev.md`, `CLAUDE.md`, `tests/quickdev/test_skill_text.py` (K7 dibalik untuk execute/review),
`tests/quickdev/test_13_text.py` (Q2), `tests/test_smoke.py` (kasus `commit`).
