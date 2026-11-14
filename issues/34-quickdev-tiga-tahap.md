# Langkah 34 — `quickdev`: tiga tahap plan → execute → review, tanpa profil (P1–P2, L1–L3, E1, R1, D1)

Sumber: permintaan user 2026-11-14 — quickdev untuk repo kecil yang masih awal development, supaya tidak overkill:
skill `profile` dihapus, `explore` dan `clarify` digabung ke fase planning, tersisa `plan → execute → review`.
Basis kode: commit `325fba9` (quickdev 0.11.1).

**Status (2026-11-14):** SELESAI di branch `quickdev-tiga-tahap`. P1–P2, L1–L3, E1, R1, dan D1
terpasang; versi quickdev 0.12.0 (commit rilis terpisah). Test regresi baru bertanda `34 L1`–`L3`, `34 P1`–`P2`, `34 E1`, `34 D1` di
`tests/quickdev/`; entri `--repo-profile` dihapus dari `CASES` `tests/test_smoke.py`. Suite penuh 2946 lulus,
`lint_plugins.py --base origin/main` 0 FAIL/0 WARN, `claude plugin validate .` lulus.

## Temuan dasar

- Enam skill = enam perhentian manual (`disable-model-invocation: true`); user mengetik `/quickdev:*` enam kali
  sebelum satu tugas selesai, dan langkah pertama (`profile`) menuntut profil 6 seksi plus baseline perintah.
- Profil hanya mengikat di tiga tempat: `plan` (Precondition 4 — perintah verifikasi Section 4), `execute`
  (Precondition 4 — perintah dan pembanding baseline), `review` (Precondition 5 — dimensi konvensi). `explore` dan
  `clarify` sudah punya fallback heuristik tanpa profil.
- `plan_lock.py` sudah punya jalur tanpa profil: baseline segar terikat `Base-Commit` (`baseline`, 13 Q6) dan
  `profile_comparator` jatuh ke "baseline segar" di luar kondisi sempit (25 R9). Rumus sidik lama tanpa `Profile:`
  (0.4.0) masih dipertahankan `verify`.
- Repo kecil di awal development belum punya konvensi layer yang mapan; perintah verifikasinya bisa dibaca
  langsung dari manifest saat rencana disusun.

## Tujuan

Tiga skill (`plan`, `execute`, `review`) yang berjalan di repo tanpa artefak tingkat repo apa pun. Rencana yang
dikunci 0.11 tetap lolos `verify` dan dapat diselesaikan oleh `execute`/`review` 0.12.

## Keputusan

1. `profile`, `explore`, `clarify` dihapus. Penelusuran (skala `kecil`/`standar`) dan klarifikasi (fast-path skip,
   batch) menjadi fase di dalam `plan`, tanpa status `EXPLORED`/`CLARIFIED` terpisah dan tanpa metadata `Gates:`.
2. Perintah verifikasi dideteksi `plan` dari manifest dan ditulis sebagai tabel Section 4 (`Jenis | Perintah | Cwd |
   Risiko`). Section 4 ikut disidik, jadi perintahnya terkunci saat approval.
3. Izin: approval rencana mencakup perintah Section 4. Hanya perintah bertanda `menyentuh DB/jaringan` yang
   ditanyakan sekali di `execute` sebelum dijalankan. Migrasi dan perintah pengubah skema/data tetap tidak pernah
   dijalankan.
4. Baseline selalu segar di `Base-Commit` (mode `awal`). Tanpa baseline tercatat (sesi putus sebelum baseline) →
   tanpa pembanding: galat di berkas rencana = regresi, sisanya `UNVERIFIED`.
5. Sinkron nataflow rencana tetap seperti sekarang; sinkron profil (`--repo-profile`) dihapus.
6. Koeksistensi dengan hook backend/frontend tetap; penawaran `.claude/workflow` pindah ke `plan` Fase 0.
7. Perampingan mesin `execute` (remediasi, `manual`, `resume`, segel) dan tujuh dimensi `review` di luar cakupan;
   langkah terpisah.

## Kontrak

### P1 — `plan` menyerap explore dan clarify

Fase 0 konteks repo (manifest, tipe repo, perintah verifikasi, tanpa menjalankan apa pun) → Fase 1 telusur (skala
`kecil`: ≤2 berkas tanpa kontrak/skema/env, trace 1; `standar`: trace 2, pemanggil simbol yang berubah, test
terkait) → Fase 2 klarifikasi (fast-path bila nol celah; maksimal 3 pertanyaan per batch, 2 batch; sisa celah →
*asumsi di Section 1* · *perkecil lingkup* · *batal*) → Fase 3 draft → Fase 4 approval + `lock` → Fase 5 sinkron
dan handoff.

### P2 — Section 4 rencana

Tabel perintah verifikasi dari manifest; jenis tanpa runner `TIDAK_ADA` (bukan dikarang). `require_test_plan`
default `false` bila baris Test `TIDAK_ADA`.

### L1 — `plan_lock.py lock`/`verify`

`lock` menulis `Hash-Scope: body` tanpa `Profile:`; `--profile` dihapus. `verify` menerima `Hash-Scope` absen
(0.4.0), `profile+body` (0.5–0.11), dan `body`.

### L2 — `plan_lock.py start`/segel

`profile_comparator` dan baris `PEMBANDING:` dihapus. `gate_paths` hanya mengecualikan profil bila rencana memuat
`Profile:` (rencana lama yang masih berjalan); default `repo-profile.md` dihapus.

### L3 — `plan_lock.py sync-payload`

`--repo-profile` dan cabang dokumen `profile` dihapus. Sinkron rencana tidak berubah.

### E1 — `execute`

Tanpa `profile_path`/`fresh_baseline`. Perintah dari Section 4 rencana; baseline segar selalu di mode `awal`;
aturan izin keputusan 3; aturan pembanding hanya `BASELINE:` atau tanpa pembanding.

### R1 — `review`

Tanpa precondition profil. Dimensi 3 menjadi "Konvensi Repo & Layer": acuan Section 2 rencana dan pola berkas
sekitar yang diubah, dengan bukti `file:baris` pembanding.

### D1 — Dokumen dan rilis

README, `flow/quickdev.md`, `CLAUDE.md`, description `plugin.json`/`marketplace.json` (sama, M4),
`MIGRATION_v0.11.x_to_v0.12.0.md`. Versi quickdev 0.12.0.

## Peta blast radius

| Berkas | Perubahan |
|---|---|
| `src/plugins/quickdev/skills/profile/`, `skills/explore/`, `skills/clarify/` | dihapus |
| `src/plugins/quickdev/skills/plan/SKILL.md` | ditulis ulang (P1, P2) |
| `src/plugins/quickdev/skills/plan/references/nataflow-sync.md` | varian profil dihapus |
| `src/plugins/quickdev/skills/execute/SKILL.md` | E1 |
| `src/plugins/quickdev/skills/review/SKILL.md` | R1 |
| `src/plugins/quickdev/skills/_common/plan_lock.py` | L1–L3 |
| `src/plugins/quickdev/README.md`, `MIGRATION_v0.11.x_to_v0.12.0.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | D1 |
| `flow/quickdev.md`, `CLAUDE.md` | D1 |
| `tests/quickdev/*`, `tests/test_smoke.py`, `tests/test_nataflow_workspaces.py` | test |

`nataflow_sync.py`/`nataflow_client.py` (byte-identical lintas plugin) dan hook backend/frontend tidak disentuh.

## Verifikasi ujung ke ujung

`uvx pytest`, `uvx --python 3.12 pytest -q`, `python3 scripts/lint_plugins.py --base origin/main`,
`claude plugin validate .`. Uji lapangan sesudah rilis di satu repo kecil.

## Trade-off yang diterima

- Konteks repo dideteksi ulang di setiap rencana; murah di repo kecil, berulang di repo besar.
- Baseline selalu diukur segar: satu putaran perintah verifikasi tambahan di awal setiap `execute`.
- `plan/SKILL.md` lebih panjang karena memuat telusur dan klarifikasi.

## Di luar cakupan

- Perampingan `execute` dan `review` (keputusan 7).
- Penghapusan dokumen `profile` yang sudah tersinkron di nataflow.
