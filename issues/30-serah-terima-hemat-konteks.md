# Langkah 30 — `backend`: serah terima hemat konteks sebelum `architect`, `JOURNEY.md` per taskdir, alat ukur token (U1, J1–J3, H1–H2, D1)

Sumber: keluhan user 2026-11-10 bahwa plugin `backend` sangat boros token, lalu analisis log sesi Claude Code di
tiga workspace (`nataflow/backend`, `hkm/wms`, `hkm/orderhub`; 301 sesi, ±25.700 pemanggilan main loop). Seluruh
keputusan di bawah diambil di sesi analisis yang sama. Basis kode: commit `53ea3f2` (backend 0.19.1).

**Status (2026-11-10):** SELESAI di branch `feat/hemat-konteks-30-31` (belum di-commit). U1, J1–J3, H1–H2, dan D1
terpasang; versi backend 0.20.0 (dirilis bersama Langkah 31). Test baru: `tests/test_token_usage.py` (7),
`tests/backend/test_journey_30.py` (J1 + kontrak prosa J2/J3/H1/H2), dua entri `CASES` `tests/test_smoke.py`.

Baseline U1 (Tahap 1, `token_usage.py ringkas` atas `hkm/wms`, `hkm/orderhub`, `nataflow/backend` beserta turunannya):
302 sesi, 25.740 pemanggilan main loop, konteks rata-rata 303.274, puncak sesi p90 690.358, porsi main loop 68,2%.
Fase: `plan` 23,1% (konteks 408k), `architect` 18,6% (490k), `system-analysis` 11,9% (304k), `report` 11,7% (512k),
`tech-lead` 7,9% (129k). Pembanding sesudah rilis diukur dengan perintah yang sama memakai `--since <tanggal rilis>`.

Selisih pelaksanaan terhadap Kontrak:

- **Anggaran `tech-lead/SKILL.md` ≤ 14.000 byte** (`test_l28_tech_lead.py::test_skill_size_budget`) memaksa rincian
  serah terima dan journey pindah ke `references/gate-lifecycle.md` bagian 6a baru; SKILL hanya menunjuk ke sana
  (IRON LAW, Fase 0 butir 4, Fase 4 butir 3, Fase 5 butir 3–4). Pemangkasan pengimbang: daftar presedensi lane di
  Keputusan 1 (tetap utuh di `decisions.md` bagian 6), daftar slot di Fase 1 butir 2 (tetap di Protokol Dispatch),
  dan beberapa frasa. Contoh `COMPLETED (WARNING)` dipertahankan (`test_l212_output_lint.py`).
- **H2 dipertajam**: jalur lanjutan hanya berlaku bila entri journey terakhir ber-hop `READY`; ia melewati Fase 1–4,
  tidak mencabangkan ulang, dan tidak menjalankan baseline build gerbang (baseline milik `architect` Fase 0 butir 3a).
  Taskdir lama tanpa journey menempuh gerbang biasa.
- **Balasan "lanjut"** di sesi yang sama ditambahkan sebagai jalur ketiga, supaya serah terima tidak memaksa user
  membersihkan konteks.
- **`analyst/references/chain-rules.md` tidak diubah**: entri journey cukup di `analyst/SKILL.md` Fase 4 butir 6 dan
  Fase 6 butir 3.
- **U1 sekaligus memuat subperintah `explorer`** (Langkah 31 X4), dan pemasangan dispatch ↔ agent memakai `toolUseId`
  di `*.meta.json`, bukan urutan kemunculan. Slug diawali `-`, jadi argumennya ditulis `--slug=<slug>`.

## Temuan dasar (data log)

| Metrik | nataflow | WMS | OrderHub |
|---|---|---|---|
| Rata-rata konteks per pemanggilan main loop | 273k | 302k | 307k |
| Puncak konteks per sesi (p90 / maks) | – / 693k | 692k / 963k | 696k / 960k |
| Porsi biaya main loop dari total | 59% | 69% | 68% |
| Konteks rata-rata fase `architect` | 368k | 473k | 538k |
| Porsi biaya main loop fase `plan` + `architect` + `report` | 77% | 52% | 52% |

Akar masalahnya: rantai `tech-lead → analyst → task → system-analysis → plan → architect → report` berjalan dalam
**satu sesi** (48 sesi di WMS + OrderHub, ditambah 11 sesi yang diawali tiket `analyst`). Tiap pemanggilan tool di
fase eksekusi membaca ulang seluruh sisa elisitasi, PRD, laporan explorer, dan brief. Padahal `architect` bekerja
mekanis dan state rantai dapat dipulihkan dari disk (`check_preconditions.py` → `entry`, ledger, materai, status
brief, commit).

Compaction yang tercatat (66 kali) menunjukkan konteks sesudah `/compact` ±108k (manual, median) dan ±112k (auto),
dengan lampiran ulang body skill yang pernah dipanggil sebesar 74–90 ribu karakter.

## Tujuan

1. Rantai berhenti di **satu** titik serah terima wajib — `READY_FOR_IMPLEMENTATION` → `architect` — dan menawarkan
   user memulai fase eksekusi dengan konteks bersih (`/clear`) atau ringkas (`/compact`), plus saran `/model sonnet`.
2. Nuansa percakapan yang tidak tercatat di dokumen rantai (keputusan lisan user, opsi yang ditolak, alasannya)
   tidak hilang saat konteks dibersihkan: dicatat ringkas di `{taskdir}/JOURNEY.md`.
3. Penghematan dapat dibuktikan dengan angka: alat ukur pemakaian token dari log sesi tersimpan di repo.

## Keputusan

- **K1 — Backend saja.** Frontend, analyst, dan plugin lain di luar cakupan; diperluas setelah terbukti.
- **K2 — Satu titik wajib.** Hanya `READY_FOR_IMPLEMENTATION` → `architect`. Titik lain (PRD `APPROVED` → `plan`,
  sesudah `REPORT.md`) tidak dijadikan titik henti.
- **K3 — Pilihan milik user.** Plugin tidak dapat menjalankan `/clear`, `/compact`, atau `/model`; skill hanya berhenti
  dan mencetak opsi. Kedua jalur sah:
  ```
  Rantai siap dieksekusi. Journey dicatat di <taskdir>/JOURNEY.md.
  Hemat konteks sebelum architect (pilih salah satu):
    a. /clear  → /model sonnet (opsional) → /backend:tech-lead lanjutkan <taskdir>
    b. /compact fokus taskdir <taskdir>; state dari disk, keputusan di JOURNEY.md
  ```
- **K4 — Re-entry lewat `tech-lead`, bukan `/backend:architect` langsung.** Konsisten dengan teks gerbang SessionStart
  ("eksekusi artefak" lewat gerbang). Biayanya satu body `tech-lead` (±14 ribu karakter) dan satu prasyarat; rute
  `brief READY → architect` di Fase 3 butir 1 sudah ada.
- **K5 — `JOURNEY.md` bukan sumber kebenaran.** Tidak ada skrip gerbang yang membacanya. Bila bertentangan dengan
  disk (ledger, materai, status brief, commit), disk menang. Isinya keputusan dan alasan, bukan status.
- **K6 — Fakta mekanis dari skrip, kalimat dari model.** `journey.py` menulis waktu dan hop; model hanya menulis
  1–2 kalimat "apa dan kenapa". Plafon dipaksa skrip.
- **K7 — Lokasi dan git.** `{taskdir}/JOURNEY.md`, ikut diabaikan git lewat penanda Langkah 24. Tidak disinkron ke
  nataflow (`sync_payload.py` `FIXED_TYPES` tidak mengenalnya — tidak berubah).
- **K8 — Alat ukur di repo, tidak dikirim.** `scripts/token_usage.py` (dev-only, stdlib, baca-saja atas
  `~/.claude/projects/`), di luar `src/plugins/` sehingga tidak masuk cache plugin. Dipakai juga oleh Langkah 31.

## Kontrak

### U1 — `scripts/token_usage.py`

- Masukan: satu atau lebih direktori proyek `~/.claude/projects/<slug>` (atau `--repo <path>` yang diterjemahkan ke
  slug), opsional `--since <tanggal>`.
- Keluaran teks dan `--json`: jumlah sesi; pemanggilan, cache read/write, output main loop; rata-rata dan p50/p90
  konteks; biaya per **fase** (skill nataflow terakhir dimuat); biaya per tipe subagent beserta model; ukuran balikan
  subagent ke main loop; compaction (sebelum/sesudah); rangkaian skill per sesi.
- Bobot biaya relatif dinyatakan eksplisit di keluaran (cache read 0,1×, cache write 2×, output 5× input) dan dapat
  diganti lewat argumen.
- Tidak pernah mencetak isi prompt, isi dokumen, atau path di luar slug proyek.

### J1 — `skills/_common/journey.py` (backend)

- `add --taskdir <t> --hop <HOP> --teks "<kalimat>"` — menambah satu baris
  `- <YYMMDD hh:mm> · <hop> · <kalimat>` ke `{taskdir}/JOURNEY.md`, membuat berkas dengan judul
  `# Journey — <nama taskdir>` bila belum ada.
- `show --taskdir <t>` — mencetak isinya (untuk Fase 0).
- Validasi (exit 1 + pesan): taskdir tidak sah (`TASKDIR_RE`), `HOP` di luar enum (`TECH_LEAD`, `TASK`, `BRD`, `PRD`,
  `BRIEF`, `READY`, `ARCHITECT`, `REVIEW`), teks kosong, > 280 karakter, lebih dari 2 kalimat, memuat blok kode atau
  baris baru, atau berkas sudah mencapai 40 entri (minta entri lama dirangkum manual — keputusan user).
- `--json` selalu JSON valid; masuk `CASES` `tests/test_smoke.py`.

### J2 — Penulis entri journey

| Skill | Titik | Isi kalimat |
|---|---|---|
| `tech-lead` | Fase 4 (serah terima pertama) | Lane, risk, dan alasan rute yang tidak tertulis di `TASK.md` |
| `analyst` | Fase 4 (approve/tolak BRD/PRD) | Keputusan user dan alasannya, termasuk opsi yang ditolak |
| `analyst` | Fase 6 (`READY_FOR_IMPLEMENTATION`) | Ringkasan batch brief dan permintaan khusus user |
| `architect` | Fase 5 (laporan penutup) | Hasil akhir dan penyimpangan yang perlu diingat |

Aturan prosa bersama: sebut keputusan atau alasan, bukan aktivitas ("melanjutkan pekerjaan" ditolak reviewer manusia,
tidak oleh skrip).

### J3 — Pembacaan journey

`tech-lead` Fase 0 (bila `taskdir` diberikan) dan `architect` Fase 0 menjalankan `journey.py show` dan
memperlakukannya sebagai konteks, tunduk pada K5.

### H1 — Titik henti `tech-lead` Fase 5

Pengirim `analyst` bervonis `READY_FOR_IMPLEMENTATION` (`references/gate-lifecycle.md` bagian 6 butir 3): alih-alih
merutekan ke `architect` di giliran yang sama, gerbang memastikan entri journey `READY` ada, mencetak opsi K3 di
slot **Langkah Lanjut** `### TECH-LEAD RE-ENTRY DECISION` dengan `Status Rantai: TERTAHAN (serah terima)`, lalu
berhenti. Pengecualian "jalankan langkah pertama di giliran yang sama" (Fase 4 butir 3, IRON LAW butir 2) dinyatakan
eksplisit untuk titik ini.

### H2 — Re-entry sesudah serah terima

`/backend:tech-lead lanjutkan <taskdir>` di sesi bersih → Fase 0 + journey → Fase 3 butir 1 (`brief READY` →
`architect`) seperti sekarang. Jalur `/compact` melanjutkan di sesi yang sama dengan rute yang sama. Tidak ada state
baru: "sudah berhenti di serah terima" tidak dicatat di mana pun selain journey.

## Peta blast radius (awal — diverifikasi ulang di tiap tahap)

| Berkas | Item |
|---|---|
| `scripts/token_usage.py` (baru), `tests/test_token_usage.py` (baru, fixture JSONL sintetis) | U1 |
| `src/plugins/backend/skills/_common/journey.py` (baru), `tests/backend/test_journey_30.py` (baru), `tests/test_smoke.py` (`CASES`) | J1 |
| `skills/tech-lead/SKILL.md` (IRON LAW, Fase 0, Fase 4, Fase 5), `skills/tech-lead/references/gate-lifecycle.md` (bagian 6) | J2, J3, H1, H2 |
| `skills/analyst/SKILL.md` (Fase 4, Fase 6), `skills/analyst/references/chain-rules.md` (bagian 4) | J2 |
| `skills/architect/SKILL.md` (Fase 0, Fase 5) | J2, J3 |
| Skrip yang memindai isi taskdir (`validate_briefs.py`, `brief_status.py`, `scaffold_brief.py`, `sync_payload.py`, `docs_git.py`) | Verifikasi tidak terganggu berkas baru — semua memakai pola nama spesifik (`brief-*.md`, `FIXED_TYPES`) |
| `README.md` backend, `flow/backend.md`, `MIGRATION_v0.19.1_to_v0.20.0.md`, `plugin.json` | D1 |

## Urutan pengerjaan

Tiap tahap: blast radius diverifikasi → perubahan + test → suite penuh hijau → lint.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | U1 | Alat ukur lebih dulu; jalankan atas log sekarang dan simpan angkanya sebagai baseline di bagian Status. |
| 2 | J1 | Skrip dan test sebagai kontrak sebelum prosa memakainya. |
| 3 | J2, J3 | Prosa penulis dan pembaca journey. |
| 4 | H1, H2 | Titik henti; bergantung pada journey sudah tertulis. |
| 5 | D1 | Dokumen, migrasi, versi backend 0.20.0. |

## Verifikasi ujung ke ujung

- Suite penuh hijau (`uvx pytest`, minimal Python 3.12), `lint_plugins.py --base origin/main` 0 FAIL, `claude plugin
  validate .`.
- Uji manual di satu repo nyata (pilihan user): rantai MINOR berhenti di serah terima, lanjut lewat jalur a dan b.
- Ukur ulang dengan U1 sesudah beberapa rantai berjalan dengan versi baru; bandingkan konteks rata-rata fase
  `architect` dan `report` terhadap baseline Tahap 1.

## Trade-off yang diterima

- Satu aksi tambahan user per rantai, dan alur tidak lagi otomatis dari tiket sampai report.
- Kalimat journey bisa terlalu umum; plafon skrip hanya menjaga ukuran, bukan mutu.
- Jalur `/compact` membawa ringkasan otomatis yang tidak terkontrol dan lampiran ulang body skill (±20–25 ribu token);
  tetap jauh di bawah konteks sekarang.

## Di luar cakupan

- Titik serah terima lain (K2), plugin selain backend (K1).
- Sinkron `JOURNEY.md` ke nataflow (K7).
- Perubahan model subagent (`code-reviewer` tetap opus), isi brief (tetap berkode lengkap), dan pemangkasan body
  SKILL (didiskusikan sesudah Langkah 30–31 selesai).
- Pembaruan plugin terpasang ke 0.19.x dan penyiapan sinkron `--push` di repo user — tindakan user, bukan kode.
