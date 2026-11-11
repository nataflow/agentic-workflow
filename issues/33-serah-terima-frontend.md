# Langkah 33 — `frontend`: serah terima konteks sebelum `plan` dan `architect`, `JOURNEY.md` per taskdir, explorer effort medium (H1–H2, J1–J3, E1, D1)

Sumber: permintaan user 2026-11-11 untuk mengadaptasi penghematan token backend (Langkah 30–32) ke `frontend`
supaya tim frontend bisa segera memakainya, didahului pengukuran `scripts/token_usage.py` atas log sesi frontend.
Basis kode: commit `59f8d15` (frontend 0.18.1, backend 0.21.0).

**Status (2026-11-11):** SELESAI di branch `feat/33-serah-terima-frontend`. H1–H2, J1–J3, E1, dan D1 terpasang;
versi frontend 0.19.0. Test baru: `tests/frontend/test_journey_33.py` (J1),
`tests/frontend/test_serah_terima_33.py` (kontrak prosa H1/H2/J2/J3/E1), dua entri `CASES` `tests/test_smoke.py`.

## Temuan dasar (data log)

`token_usage.py ringkas` atas dua workspace frontend (16 sesi):

| Metrik | `hkm/nocan-frontend` | `nataflow/frontend` |
|---|---|---|
| Sesi / pemanggilan main loop | 5 / 518 | 11 / 790 |
| Porsi biaya main loop dari total | 77,6% | 64,5% |
| Konteks rata-rata / puncak sesi maks | 311k / 766k | 212k / 407k |
| Porsi `plan` + `architect` dari main loop | 54,5% | 58,8% |
| Konteks rata-rata fase `plan` | 387k | 257k |
| Konteks rata-rata fase `report` | 391k | 342k |
| `code-explorer` dari biaya subagent | 6,4% | 15,3% |
| Compaction | 0 | 1 manual (263k → 108k) |

Polanya sama dengan Langkah 30: seluruh rantai `lead → task → [ux/ui] → contract → plan → architect → report`
berjalan dalam satu sesi, sehingga `plan` dan `architect` membawa prosa dan draft gate hulu di tiap giliran.
Bedanya, rantai frontend **mengalir sendiri dari gate ke gate** (Output `contract`: "lanjut ke frontend:plan …
di main loop"; Output `plan`: "lanjut ke frontend:architect di main loop") — tidak ada `tech-lead` yang menerima
kendali kembali seperti backend. Explorer bukan biaya besar di frontend (satu dispatch per fase, balikan 4–9 ribu
karakter), berbeda dengan backend (44–48%).

Re-entry sudah tersedia hampir utuh: `taskdir_state.py --taskdir` memvonis keadaan dari disk (`GATE` → pemilik
hop beserta mode `plan`, `EKSEKUSI` → `architect`, dan 15 keadaan lain). Yang kurang hanya jalur cepat: lead
menjalankan sapuan Phase 1 (≤3 Glob/Grep, bisa dispatch explorer) sebelum Phase 2.

`## Riwayat Rantai` sudah merekam jawaban approve (`persetujuan`) dan alasan reopen/eskalasi (`alasan`) secara
mekanis, tetapi tidak nuansa di luarnya (opsi yang ditolak, permintaan khusus). Teks bebas tidak boleh masuk ke
sana: log itu dibaca setiap gerbang, dan satu baris cacat menggagalkan semuanya.

## Tujuan

Memisahkan sesi persetujuan dari sesi `plan` dan `architect` atas pilihan user, tanpa melonggarkan satu gerbang
pun, dan membawa keputusan lisan antar sesi lewat berkas yang tidak pernah menjadi sumber status.

## Keputusan

- **K1 — Tahap 1 saja.** Serah terima, journey, dan effort explorer. T1 (`render_prompt`) dan C1 (`close_brief`)
  Langkah 32 ditunda sampai backend 0.21.0 lolos uji lapangan; amplop explorer Langkah 31 tidak dikerjakan
  (porsinya kecil di frontend).
- **K2 — Dua titik serah terima.** `CONTRACT` disetujui → `plan` (lane ber-CONTRACT) dan `BRIEF` disetujui →
  `architect` (semua lane, **termasuk `HOTFIX_MINOR`**, atas keputusan user). Sesudah `REPORT.md` bukan titik.
- **K3 — Gate pemilik mencetak blok dan berhenti.** Karena rantai frontend mengalir dari gate ke gate, padanan
  32 K9 ("`tech-lead` mencetak blok") tidak berlaku. Teks blok tetap satu rumah:
  `lead/references/lane-routing-matrix.md` bagian 4a.
- **K4 — Pilihan milik user, tiga jalur.** `/clear` (+ `/model sonnet` opsional) lalu `/frontend:lead lanjutkan
  <taskdir>`, `/compact`, atau balasan "lanjut" di sesi yang sama (gate berikutnya dipanggil langsung; prasyaratnya
  menagih keabsahan hop hulu).
- **K5 — Re-entry lewat `lead`, tujuan dari disk.** Jalur cepat melewati Phase 1 dan Phase 3–7 lalu merutekan
  menurut tabel Phase 2 atas vonis `taskdir_state.py --taskdir`. Tidak bergantung pada hop journey terakhir
  (berbeda dengan backend 30 H2), karena skrip keadaan sudah mencakup semua keadaan.
- **K6 — `JOURNEY.md` bukan sumber kebenaran.** Tidak ada skrip gerbang yang membacanya, tidak disinkron
  (`sync_payload.doc_type` kosong), diabaikan git lewat penanda Langkah 24. Disk menang.
- **K7 — `journey.py` diadaptasi, bukan disalin.** `check_taskdir` frontend bersignatur lain
  (`add, cid, root, rel`), dan hop berbeda. Aturan teks dan plafon dipatok identik dengan backend lewat test
  (`entries`, `teks_problem`, `emit`, konstanta). Taskdir wajib berakar: journey sebelum `TASK.md` membuat taskdir
  tampak kosong (`AKAR`) di `taskdir_state.py`.

## Kontrak

### J1 — `skills/_common/journey.py` (frontend)

`add --taskdir <t> --hop <HOP> --teks "<…>"` dan `show --taskdir <t>` (`--json`). Hop: `LEAD`, `FLOW`, `UI`,
`CONTRACT`, `BRIEF`, `ARCHITECT`, `REVIEW`. Plafon: 1–280 karakter, satu baris, tanpa blok kode, ≤ 2 kalimat,
≤ 40 entri. FAIL untuk taskdir di luar pola, tidak ada, atau tanpa `TASK.md`.

### J2 — Penulis

`lead` Phase 7 sesudah `TASK ROOT LOCKED` (`LEAD`); `ux-design`/`ui-design` sesudah approve bila ada opsi ditolak
atau asumsi dipilih (`FLOW`/`UI`); `contract` dan `plan` sesudah approve (`CONTRACT`/`BRIEF`); `architect` Phase 5
butir 5, apa pun hasilnya (`ARCHITECT`); `lead` Phase 8 baris `TEMUAN` (`REVIEW`).

### J3 — Pembaca

Jalur cepat lead (`journey.py show`) dan `architect` Phase 0 butir 4. Disk menang bila bertentangan.

### H1 — Titik henti `contract` dan `plan`

Sesudah approve, sinkron nataflow, dan entri journey: Output gate + blok bagian 4a butir 3, lalu berhenti. Baris
Output berubah dari "lanjut ke … di main loop" menjadi "serah terima sebelum frontend:…". Opsi approve `plan`
menjadi *Setujui breakdown* (tanpa "lanjut eksekusi").

### H2 — Jalur cepat `lead`

`prompt` hanya melanjutkan satu taskdir → lewati Phase 1 dan Phase 3–7, jalankan `taskdir_state.py --taskdir` +
`journey.py show`, rute Phase 2. `prompt` dengan permintaan baru → lead biasa.

### E1 — `agents/code-explorer.md`

`effort: medium` (padanan backend Langkah 31).

### D1 — Dokumen dan rilis

`flow/frontend.md` (versi, diagram, Alur Utama butir 9, lead/ux/ui/contract/plan/architect, artefak),
`README.md` frontend (bagian Serah Terima Konteks, artefak), `CLAUDE.md` repo; frontend 0.18.1 → 0.19.0.

## Peta blast radius

| Berkas | Perubahan |
|---|---|
| `skills/_common/journey.py` | baru |
| `skills/lead/references/lane-routing-matrix.md` | bagian 4a baru |
| `skills/lead/SKILL.md` | Precondition 4 (peta skrip), Phase 1 jalur cepat, Phase 5 nama berkas, Phase 7 journey, Phase 8 `TEMUAN` |
| `skills/contract/SKILL.md`, `skills/plan/SKILL.md` | Phase approve + Output |
| `skills/ux-design/SKILL.md`, `skills/ui-design/SKILL.md` | journey sesudah approve |
| `skills/architect/SKILL.md` | Phase 0 butir 4, Phase 5 butir 5 |
| `agents/code-explorer.md` | `effort: medium` |
| `flow/frontend.md`, `src/plugins/frontend/README.md`, `CLAUDE.md` | dokumentasi |
| `tests/frontend/test_journey_33.py`, `tests/frontend/test_serah_terima_33.py`, `tests/test_smoke.py` | test |

Tidak ada skrip gerbang yang berubah; `chain.py`, `taskdir_state.py`, validator, dan sinkron tidak disentuh.

## Verifikasi ujung ke ujung

`uvx pytest`, `python3 scripts/lint_plugins.py`, `claude plugin validate .`. Penghematan diukur sesudah rilis di
sesi frontend nyata dengan perintah baseline di atas ditambah `--since <tanggal rilis>`.

## Trade-off yang diterima

- Rantai yang dulu mengalir kini berhenti dua kali; "lanjut" meneruskannya di sesi yang sama.
- Lane `HOTFIX_MINOR` ikut berhenti sebelum `architect` walau rantainya pendek — konsisten dengan backend.
- `journey.py` frontend dan backend dua salinan; kesamaan aturan teks dijaga test, bukan byte-identik.

## Di luar cakupan

- T1 (`render_prompt.py`) dan C1 (`close_brief.py`) — menunggu uji lapangan backend 0.21.0.
- Amplop explorer ringkas (31 X1–X3) dan pola delta (32 E1/E2).
- Pemangkasan body SKILL dan template dokumen.
