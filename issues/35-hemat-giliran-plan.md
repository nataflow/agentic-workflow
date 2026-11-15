# Langkah 35 — `backend`: hemat giliran fase `plan` — kerangka sekaligus, `--open-round` membawa state, gerbang brief pertama, contoh spec (G1–G4, D1)

Sumber: compare `token_usage.py` sesudah backend 0.21.0 (2026-11-15) dan pembedahan log 35 sesi fase `plan`
(wms + orderhub `--turunan`, `--since "2026-11-11T10:26+07:00"`). Keputusan diambil 2026-11-15. Basis kode: commit
`d2fab2c` (backend 0.21.0). Alat ukur: `scripts/token_usage.py` (Langkah 30 U1, perbaikan prompt rujukan 32 T1).

**Status (2026-11-15):** SELESAI di branch `feat/35-hemat-giliran-plan`; backend 0.22.0
(`MIGRATION_v0.21.0_to_v0.22.0.md`). Test baru: `tests/backend/test_hemat_giliran_35.py` (G1–G4). Belum: compare
`token_usage.py` sesudah 0.22.0 terpasang (bagian Verifikasi).

## Temuan dasar (data log)

Fase `plan` ±25% biaya main loop: 35 sesi, 1.786 giliran, 128 brief (±14 giliran per brief), konteks rata-rata
250 rb (masuk ±139 rb, keluar ±264 rb). Biaya 63% cache read, jadi yang menentukan adalah **jumlah giliran ×
konteks** (±39 rb unit per giliran), bukan ukuran isi.

| Pola giliran mekanis | Jumlah | Catatan |
|---|---|---|
| `scaffold_brief.py --nn` berdiri sendiri | 41 | 32 lainnya sudah dirangkai `&&` sesudah `--write-matrix` |
| Membaca sumber/`--help` `scaffold_brief.py` | 63 | Menebak bentuk JSON `brief-spec.json`; SKILL hanya menyebut nama field |
| `validate_briefs.py --review-state` | 43 | Selalu disusul `--open-round` (46) |
| `validate_briefs.py --brief` | 104 | 42% FAIL di run pertama → Edit + run ulang |

Check yang paling sering FAIL di run `--brief`/batch: N (resolusi anchor), L (langit-langit slicing), E (batas
cakupan), lalu V, C, P.

## Tujuan

Mengurangi giliran mekanis main loop di fase `plan` tanpa melonggarkan predikat apa pun: seluruh check tetap
ditagih, hanya titik dan jumlah pemanggilannya yang berubah.

## Keputusan

- **K1** — Kerangka seluruh batch ditulis satu panggilan, semua-atau-tidak sama sekali; `--nn` tetap ada untuk satu
  brief dan `--force`.
- **K2** — `--open-round` jadi satu-satunya panggilan sebelum dispatch reviewer; `--review-state` tetap ada untuk
  membaca tanpa membuka.
- **K3** — Gerbang per-brief hanya brief pertama batch (cacat sistemik); sisanya ditagih gerbang batch Fase 4. Risiko
  Check L (brief kebesaran baru ketahuan di Fase 4) diterima user.
- **K4** — Contoh bentuk `brief-spec.json` ditulis di SKILL. Ini **penambahan** teks, bukan pemangkasan
  (pemangkasan SKILL/references tetap ditunda).
- Di luar langkah ini (diusulkan, belum diputuskan): pengarahan bacaan references (U3, menyentuh keputusan tunda),
  jalur cepat masuk `plan` tanpa body `analyst` (U4), delegasi penulisan brief ke subagent (U5).

## Kontrak

### G1 — `scaffold_brief.py --all` (K1)

- Menulis kerangka tiap baris matriks yang berkasnya belum ada dan NN-nya tidak terkunci, urut NN.
- Seluruh baris direncanakan dulu (`_plan`: legalitas `supersedes`, NN terkunci, kembar NN, render `commit_message`)
  tanpa menyentuh disk; satu baris gagal → `SCAFFOLD: [FAIL] … tidak satu kerangka pun ditulis` (exit 1) dan tidak
  ada kerangka, transisi `SUPERSEDED`, maupun pencabutan `HALT.md` yang mendarat.
- Berkas yang sudah ada dan NN terkunci dilewati dan dilaporkan (`dilewati: …`), tidak ditimpa.
- Isi kerangka byte-identik dengan `--nn` per brief (`_apply` dipakai bersama).
- `--all` bersama `--nn` atau `--force` ditolak argparse (exit 2).

### G2 — `--open-round` membawa state (K2)

- Mencetak `ronde terpakai <n>/2 (sisa <m>, termasuk ronde ini) · taskdir <t>/4`, brief berubah, dan baris
  `Slot dispatcher: {ronde} = <n>[, {brief_berubah} = baris di atas]`.
- Ronde lanjutan (riwayat generasi ini tidak kosong) tanpa brief berubah → **tidak dibuka**, exit 0, state tidak
  disentuh, pesan "tutup self-review tanpa dispatch" — aturan slot `{brief_berubah}` kini mekanis.
- Ronde sebelumnya yang masih terbuka tanpa vonis → dibuka ulang dengan nomor sama, snapshot diganti, dan
  diperingatkan.
- Plafon habis tetap FAIL (exit 1), tidak berubah.

### G3 — Gerbang brief pertama (K3)

SKILL Fase 3 butir 4 "Gerbang Brief Pertama": `validate_briefs.py --brief <NN>` hanya atas brief pertama batch;
koreksinya diterapkan ke cara mengisi brief berikutnya. Prosa saja — gerbang per-brief memang tidak pernah ditegakkan
skrip.

### G4 — Contoh `brief-spec.json` (K4)

Blok JSON dua baris di SKILL Fase 3 butir 1 beserta aturan bentuk (`nn` dua digit, `unit` kebab-case, field list
selalu list string, `consumes` → `brief-NN` lebih kecil, `explore` tanpa `.md`). Test memvalidasi blok itu dengan
`spec_shape_problems` dan whitelist field skrip, supaya contoh tidak membusuk saat skrip berubah.

### D1 — Dokumen dan rilis

`plan/SKILL.md`, `plan/references/review-and-commit.md` §5–6, `plan/dispatcher/reviewer.md` (sumber slot),
`plan/templates/brief-template.md`, `architect/references/lifecycle-recovery.md`, `flow/backend.md` (§plan +
diagram), `MIGRATION_v0.21.0_to_v0.22.0.md`, `plugin.json` backend 0.22.0.

## Perkiraan dampak (belum diukur)

| ID | Giliran yang hilang (35 sesi) | Porsi biaya fase `plan` |
|---|---|---|
| G1 | ±41 | ±2% |
| G2 | ±43 | ±2,4% |
| G3 | ±70 + sebagian run ulang | ±4% |
| G4 | hingga ±63 | ±3% |

Total ±9–11% biaya fase `plan` (±2% biaya total). SKILL plan bertambah ±1,9 rb karakter (G4 + G3), dibaca sekali
per sesi.

## Peta blast radius

| Berkas | ID |
|---|---|
| `plan/scripts/scaffold_brief.py` (`_require_matrix`, `_plan`/`_apply`, `scaffold_all`, `--all`) | G1 |
| `plan/scripts/validate_briefs.py` (`review_state_cli` cabang `--open-round`, docstring) | G2 |
| `plan/SKILL.md` Fase 3 butir 1/2/4, Fase 5 butir 1, Guardrails | G1–G4 |
| `plan/references/review-and-commit.md`, `plan/dispatcher/reviewer.md` | G2, G3 |
| `plan/templates/brief-template.md`, `architect/references/lifecycle-recovery.md` | G1 |
| `flow/backend.md` | D1 |
| `tests/backend/test_hemat_giliran_35.py` (baru) | G1–G4 |

Tidak terdampak: frontend (`_common/review_round.py` sendiri), test lama `--open-round`/`--record-round`
(`test_11_robustness.py`, `test_l27_plan_state.py` — tetap lulus), `test_smoke` (tidak ada skrip baru).

## Verifikasi ujung ke ujung

- `uvx pytest` penuh dan `python3 scripts/lint_plugins.py --base origin/main` 0 FAIL.
- Sesudah 0.22.0 terpasang: `token_usage.py ringkas` fase `plan` — giliran per brief turun di bawah ±14, giliran
  baca sumber `scaffold_brief.py` mendekati nol, run `--brief` ±1 per sesi, `--review-state` di fase `plan`
  mendekati nol.

## Trade-off yang diterima

- G3: brief kedua dan seterusnya yang melewati langit-langit slicing (Check L) baru ketahuan di Fase 4, dan
  pemecahannya bisa merombak brief hilir yang sudah ditulis.
- G4: SKILL plan sedikit lebih panjang; dibayar sekali per sesi, jauh di bawah giliran baca sumber yang dihilangkan.
