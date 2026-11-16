# Langkah 37 — `frontend` + `backend`: laporan unit lewat balikan — implementor berhenti menulis `report-NN.md`, main loop menulisnya hanya bila perlu, laci explorer tanpa awalan `report` (U1–U5, B1–B2, E1, R1)

Sumber: transkrip subagent di `~/.claude/projects` (2026-11-16) — 7 repo (esim-dashboard, wms-svelte, oms-app,
wms-3d, wms-dashboard, nocan/frontend, nataflow-frontend untuk frontend; wms-rust, oms-api, wms-api,
nataflow-backend untuk backend), Claude Code 2.1.323 dan 2.1.325. Keputusan diambil 2026-11-16. Basis kode: commit
`238f09f` (frontend 0.20.0, backend 0.22.0).

**Status (2026-11-16):** RENCANA — belum ada kode yang diubah.

## Temuan dasar (data log)

Harness Claude Code — bukan hook plugin — menolak `Write` subagent ke berkas berawalan `report`:

```
<tool_use_error>Subagents should return findings as text, not write report files.
Include this content in your final response instead.</tool_use_error>
```

Subagent lalu menyerahkan isi laporannya sebagai teks lewat `SubagentHandback`. `guard_bash.py` frontend justru
mengizinkan path itu (`UNIT_REPORT_OK`, 24 K13), jadi penolakan datang sebelum hook berperan.

| # | Friksi | Bukti |
|---|---|---|
| 1 | Setiap unit frontend berhenti di matriks bukti disk | 133 `Write` `report-NN.md` ditolak, nol lolos — 116 dari `frontend:code-implementor`. Laporan absen + tree kotor = baris **HENTIKAN** (`execution-protocol.md` bagian 3), jadi `architect` bertanya ke user tiap unit; user menyetujui main loop menulis laporan dari balikan, berulang per unit (mis. sesi `8ad6dc71…` di wms-svelte: unit 01–04 tiap kali `AskUserQuestion` lalu `Write report-0N.md` oleh main loop) |
| 2 | Jalur gagal backend kehilangan laporan | 7 penolakan `report-NN.md` dari `backend:code-implementor` — tepat di jalur `BLOCKED`, satu-satunya jalur yang menulisnya. Matriks amplop `BLOCKED` (`lifecycle-recovery.md`) berporos pada ada-tidaknya laporan |
| 3 | Laci explorer bernama `report-*` ditolak | `frontend:code-explorer` gagal menulis `.explore/report-dcc-hasil-selisih-tabel-badge.md` (wms-dashboard) — slug laci diturunkan dari topik yang berawalan `report` |

Pola penolakan: nama berkas, bukan lokasi. `REVIEW.md` (174×), `REVIEW-PLAN.md` (60×), `brief-*.md`, dan berkas
`.explore/` lain selalu lolos walau sama-sama di taskdir yang diabaikan git. Penolakan yang tampak di reviewer
adalah `Read` atas laporan yang mengutip pesan di atas, bukan blokir. Aturan harness tidak terdokumentasi; issue ini
tidak bergantung pada bentuk persisnya selain "subagent tidak menulis berkas laporan".

## Tujuan

Rantai frontend kembali berjalan tanpa pertanyaan user per unit, dan jalur gagal backend kembali meninggalkan
laporan di disk — tanpa melonggarkan vonis: status unit tetap klaim subagent yang divonis dari disk
(`verify_scope.py`, `git status`, hunk anchor, commit unit).

## Keputusan

- **K1 (U1, B1)** — Implementor (frontend dan backend) tidak pernah menulis berkas laporan. Isi laporan menjadi
  balikan chat. Ini menyamakan frontend dengan backend, yang sejak awal hanya membalas amplop di jalur sukses.
- **K2 (U2, B2)** — Main loop (`architect`) yang menulis `report-NN.md`, **salin persis** dari balikan; satu-satunya
  tambahan miliknya tetap `## Triase`. Lokasi, nama, dan kontrak isi laporan tidak berubah — pembaca hilir (`plan`,
  `report`, `contract`, kanal profil, `sync_payload.py`) dan taskdir lama tetap sah.
- **K3 (U2)** — Frontend menulis laporan **hanya untuk unit yang tidak bersih**: `FAILED`, turun ke `BLOCKED`
  (pelanggaran scope atau gerbang kompilasi retroaktif), ber-`## Triase` (termasuk catatan Format unit 36 F1), atau
  `## Out of Scope / Mismatch` tidak kosong. Unit bersih tanpa berkas laporan — sama dengan backend, yang menulisnya
  hanya di jalur gagal.
- **K4 (U4)** — Butir `DITUNDA` untuk `## Done Criteria DITUNDA` `REVIEW.md` dibaca reviewer dari seksi 5 brief
  (sumber aslinya), bukan dari laporan yang kini tidak selalu ada.
- **K5 (E1)** — Nama berkas laci `.explore/` tidak pernah berawalan `report`; slug yang berawalan itu diberi awalan
  `telusur-`.
- **K6** — Ganti nama berkas (mis. `unit-NN.md`) **ditolak**: tetap bergantung pada aturan nama harness yang tidak
  terdokumentasi, menyentuh lebih banyak skrip dan test, dan mengubah nama cermin di nataflow.
- **K7** — `verify_scope.py` (byte-identik frontend/backend) **tidak diubah**: himpunan sahnya tetap memuat
  `report-NN.md`, tetapi path itu diabaikan git sehingga tidak pernah tampak di `git status`.

## Kontrak

### U1 — Implementor frontend tanpa berkas laporan

- `agents/code-implementor.md`: Iron Law berbunyi "TIDAK ADA BERKAS LAIN YANG BOLEH DITULIS"; input `report_path` dan
  gerbang masuk no. 2 dihapus; Fase 2 butir 4 dan `## Output`: balikan = blok `Format laporan` persis, tanpa teks lain
  (frontmatter `artifact: UNIT_REPORT` … `## Rollback`). `description` frontmatter tidak lagi menyebut menulis
  `report-NN.md`.
- Baris alibi "Laporannya cukup di chat saja" diganti "Saya tulis laporannya ke berkas biar aman" → harness menolak
  tulisan laporan subagent; `architect` yang menyimpannya.
- `[FORBIDDEN]` menulis berkas di taskdir — tanpa pengecualian.
- `architect/dispatcher/implementor.md`: slot `{report_path}` dihapus; butir **Balikan** = blok `Format laporan`;
  **Penanganan Balikan** memakai status balikan sebagai klaim (DONE/FAILED/rusak), lalu matriks bagian 3.

### U2 — `architect` frontend menyimpan laporan unit tak bersih

- `execution-protocol.md` bagian 3: kolom pertama matriks = status **balikan** (`DONE` / `FAILED` / absen-rusak),
  bukan `report-<NN>.md`. Baris dan tindakannya tetap; baris yang menulis `## Triase` kini juga menyimpan laporan.
- Bagian 4 (kontrak laporan): penulis = `architect`, dari balikan, salin persis + `## Triase`; ditulis di disk
  **sebelum** commit unit (atau sebelum status `BLOCKED`), tidak pernah di-stage. Daftar pemicu K3 ditulis di sini
  sebagai satu-satunya rumah.
- Bagian 5 (gerbang kompilasi): `BLOCKED` retroaktif atas unit bersih → tulis laporan dari balikan bila masih di
  konteks; sudah tidak ada (sesi terputus) → frontmatter (`status: FAILED`) + `## Triase` berisi galat mentahnya.
- Bagian 6 (siklus status): pemicu `READY → DONE`/`BLOCKED` membaca status balikan.
- `architect/SKILL.md` Iron Law dan Phase 2 butir 2: "status unit divonis dari disk — `git status`, `verify_scope.py`,
  hunk anchor; balikan implementor adalah klaim"; Failure path butir 2–3 berbunyi "balikan absen atau rusak".

### U3 — Prasyarat `architect` frontend

- `check_preconditions.py` Check 4: `missing_reports` dan `_warn_missing_reports` (25 R6) dihapus — `DONE` ber-commit
  tanpa laporan adalah keadaan normal, bukan `WARN`.
- Fase `TERPUTUS` (brief `DONE` di disk tanpa commit unit) divonis dari tree saja: perubahan di dalam
  `files_touched` (`verify_scope.py` `PASS`) → pemeriksaan anchor → commit unit; tree bersih → brief kembali ke
  `READY` dan `report-<NN>.md` sisa dihapus (Check 12 menuntut ia absen), lalu dispatch ulang; kotor di luar scope →
  HENTIKAN. `TERPUTUS_ACTION` dan paragraf `TERPUTUS` bagian 3 diselaraskan.
- Check 12 tetap: laporan untuk brief `READY` berarti unit itu sudah pernah ditriase.
- `plan/scripts/check_preconditions.py` Check 5 (unit `BLOCKED` wajib punya laporan) tetap — K3 menjamin laporannya
  ditulis.

### U4 — Reviewer frontend

- `agents/code-reviewer.md` Fase 0 butir 4 dan Fase 3 butir 3: butir `DITUNDA` = butir terminal seksi
  `## 5. Done Criteria & Verification Baseline` tiap brief `DONE`; baris `preseden menyesatkan` dari
  `report-<NN>.md` yang ada (absen = nihil).
- `architect/SKILL.md` Phase 5 butir 2: kumpulan `preseden menyesatkan` dari laporan yang ada.

### U5 — Guard frontend

- `hooks/guard_bash.py`: `UNIT_REPORT_OK` dan pengecualiannya di `decide_writer` dicabut; docstring 24 K13
  diperbarui. `Write`/`Edit` implementor ke `report-NN.md` kini ditolak hook (path diabaikan git) dengan alasan yang
  terbaca, selaras dengan harness.

### B1 — Implementor backend: badan laporan di amplop `BLOCKED`

- `agents/code-implementor.md` Kalibrasi (**Batas tulis**, **Jalur gagal**, **Penutupan kegagalan**) dan gerbang 9
  stop condition: "tulis alasannya ke `report-{NN}.md`" → "bawa alasannya di badan laporan amplop". Brief tetap
  ditandai `BLOCKED` dan commit penanda `wip(<domain>)` tetap dibuat implementor.
- `## Format Output`: amplop jalur gagal = baris `Status/Cause/Commit` lalu badan laporan utuh (frontmatter `brief`,
  `status: BLOCKED`, `reason`, empat seksi, baris `Umpan balik profil:` bila ada). Plafon 10 baris hanya untuk
  jalur sukses. Baris `Report File:` dihapus.
- `architect/dispatcher/implementor.md` diselaraskan.

### B2 — `architect` backend menyimpan laporan `BLOCKED`

- `lifecycle-recovery.md` bagian 3: amplop `BLOCKED` → `architect` menulis `{taskdir}/report-<NN>.md` salin persis dari
  badan amplop **sebelum** matriks amplop `BLOCKED` dijalankan; amplop tanpa badan → laporan dari baris
  `Status`/`Cause` dengan `## Evidence` "badan laporan tidak dikirim implementor". `### Struktur Laporan Kegagalan`
  menyebut penulisnya.
- `hooks/guard_bash.py` `lease()`: `report-NN.md` dicabut dari `allowed`; docstring lease diperbarui.
- `architect/SKILL.md` slot **Umpan balik profil** tetap membaca `report-NN.md` (kini tulisan `architect`).

### E1 — Laci explorer tanpa awalan `report`

- `frontend/agents/code-explorer.md` Fase 4 dan `## Batas`: slug laci yang berawalan `report` diberi awalan
  `telusur-` (`<taskdir>/.explore/telusur-report-….md`).
- Backend: slug laci dipilih skill pendispatch. `_common/render_prompt.py` menolak (exit 1) nilai slot `slug` yang
  berawalan `report` dengan pesan "beri awalan `telusur-`"; dispatch yang tidak lewat `render_prompt.py` (mis. gerbang
  `tech-lead` `dispatcher/explorer.md`) diberi kalimat yang sama di Slot Hidrasi-nya.

### R1 — Dokumen dan rilis

`flow/frontend.md`, `flow/backend.md`, `src/plugins/frontend/README.md`, `src/plugins/backend/README.md`,
`MIGRATION_v0.20.0_to_v0.21.0.md` (frontend), `plugin.json` frontend 0.21.0 dan backend 0.23.0.

## Peta blast radius

| Berkas | ID |
|---|---|
| frontend `agents/code-implementor.md`, `architect/dispatcher/implementor.md` | U1 |
| frontend `architect/references/execution-protocol.md` bagian 1, 3, 4, 5, 6; `architect/SKILL.md` | U2, U3, U4 |
| frontend `architect/scripts/check_preconditions.py` (Check 4, `TERPUTUS_ACTION`) | U3 |
| frontend `agents/code-reviewer.md` | U4 |
| frontend `hooks/guard_bash.py` | U5 |
| frontend `agents/code-explorer.md` | E1 |
| backend `agents/code-implementor.md`, `architect/dispatcher/implementor.md` | B1 |
| backend `architect/references/lifecycle-recovery.md`, `architect/SKILL.md` | B2 |
| backend `hooks/guard_bash.py` (`lease`) | B2 |
| backend `_common/render_prompt.py`, `tech-lead/dispatcher/explorer.md` | E1 |
| `flow/frontend.md`, `flow/backend.md`, kedua `README.md`, `MIGRATION_*`, kedua `plugin.json` | R1 |
| `tests/frontend/test_12_guard.py` (baris `report-01.md`/`report-12.md` → 2), `test_24_riwayat.py:180` (WARN → PASS), `test_12_orchestration.py` (R6 `TERPUTUS`), `test_l34_implementor_no_bash.py` | U3, U5 |
| `tests/backend/test_l34_guard_bash.py` (lease tanpa `report-01.md`; `Edit` → 2), `test_25_report_contract.py` (penulis = amplop + `architect`) | B1, B2 |
| `tests/frontend/test_laporan_balikan_37.py`, `tests/backend/test_laporan_balikan_37.py` (baru) | semua |

Tidak terdampak: `verify_scope.py` (K7) dan salinan byte-identik lain (`detect.py`, `migrate_profile.py`,
`run_verification.py`, `docs_git.py`); `sync_payload.py` frontend/backend (mencerminkan laporan yang ada, nama
tetap); `plan/scripts/check_preconditions.py` frontend; `validate_review.py` (hanya memvonis bentuk seksi
`## Done Criteria DITUNDA`); `report`/`contract`/`plan` SKILL frontend (membaca `## Triase` dan `## Out of Scope`,
yang hanya ada pada unit tak bersih — dan unit itu selalu punya laporan); analyst, quickdev, nataflow, product,
fullstack (subagent mereka tidak menulis berkas laporan).

## Tahapan

1. U5 + U1 — guard dan implementor frontend (keduanya menutup jalur tulis yang sama).
2. U2 — matriks dan kontrak laporan `architect` frontend.
3. U3 — prasyarat frontend (Check 4, `TERPUTUS`).
4. U4 — reviewer frontend.
5. B1 + B2 — backend.
6. E1 — laci explorer.
7. R1 — dokumen, migrasi, rilis.

Tiap tahap satu commit kode + test; rilis commit terpisah.

## Verifikasi ujung ke ujung

- Test baru frontend:
  - guard menolak `Write`/`Edit` `report-NN.md` oleh `frontend:code-implementor` (exit 2);
  - Check 4 `PASS` untuk brief `DONE` ber-commit tanpa laporan;
  - `TERPUTUS` dengan tree bersih + laporan sisa → aksi "kembali `READY`, hapus laporan";
  - Check 5 `plan` tetap `FAIL` untuk `BLOCKED` tanpa laporan;
  - prosa: implementor tanpa `report_path`; `execution-protocol.md` bagian 4 memuat "salin persis" dan daftar pemicu
    K3; reviewer merujuk seksi 5 brief untuk `DITUNDA`.
- Test baru backend:
  - lease tanpa `report-NN.md`; `Edit` implementor ke sana ditolak;
  - amplop jalur gagal memuat empat seksi laporan dan `Umpan balik profil:`;
  - `lifecycle-recovery.md` menyebut `architect` sebagai penulis;
  - `render_prompt.py` menolak slot `slug` berawalan `report`.
- `uvx pytest` penuh dan `python3 scripts/lint_plugins.py --base origin/main` 0 FAIL.
- Lapangan (hkm, sesudah frontend 0.21.0/backend 0.23.0 terpasang): satu rantai frontend tuntas tanpa
  `AskUserQuestion` soal laporan absen; transkrip `code-implementor` tanpa `Subagents should return findings`; satu
  brief `BLOCKED` frontend/backend meninggalkan `report-NN.md` tulisan main loop yang dipakai `plan` APPEND.

## Trade-off yang diterima

- Isi laporan masuk konteks main loop sebagai balikan. Netto tidak bertambah: sebelumnya `architect` membaca berkas
  yang sama dari disk untuk matriks; tulisan ulang hanya terjadi untuk unit tak bersih.
- Unit bersih tidak lagi meninggalkan jejak `## Changes`/`## Done Criteria` per unit di disk maupun di cermin
  nataflow. Buktinya tetap commit unit (diff, pesan `implement unit NN`) dan seksi 5 brief; `REVIEW.md` menilai
  diff gabungan.
- Laporan ditulis main loop, bukan subagent — risiko "dirapikan" saat disalin. Diredam aturan salin persis +
  `## Triase` saja, dan isinya tetap klaim yang divonis dari disk.
- E1 bergantung pada aturan nama harness yang diamati, bukan didokumentasikan; ruginya bila aturan itu berubah hanya
  awalan `telusur-` yang tak perlu.
