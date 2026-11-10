# Langkah 31 — `backend`: balikan `code-explorer` ringkas, berkas laporan jadi sumber kebenaran, diagnosis dispatch ganda (X1–X4, D1)

Sumber: analisis pemakaian token 2026-11-10 (lihat Langkah 30, bagian Temuan dasar). Keputusan diambil di sesi yang
sama. Basis kode: commit `53ea3f2` (backend 0.19.1). Bergantung pada alat ukur `scripts/token_usage.py` (Langkah 30
U1).

**Status (2026-11-10):** SELESAI di branch `feat/hemat-konteks-30-31` (belum di-commit). X1–X3 dan D1 terpasang;
X4 terdiagnosis, usulan kebijakannya menunggu keputusan user (K5, bagian Hasil X4). Test baru:
`tests/backend/test_explorer_balikan_31.py`. Versi backend 0.20.0 bersama Langkah 30.

Selisih pelaksanaan terhadap Kontrak:

- **Istilah "amplop pembungkus"** di `tech-lead`/`plan`/`debug` dispatcher (maksudnya Universal Dispatch Envelope)
  diganti nama itu, supaya tidak bertabrakan dengan "amplop ringkas" explorer. `architect/dispatcher/reviewer.md`
  tidak disentuh (bukan explorer).
- **`tech-lead/references/gate-scope.md`** (bagian 3 "Di luar matriks" dan bagian 4E) ikut diubah: keduanya
  menyebut laporan "dikembalikan ke context".
- **X3 tidak menyentuh SKILL hilir**: prosa `plan` (Fase 3 langkah 3), `system-analysis` (Tahap 0 panen), dan
  `business-analysis`/`debug` sudah merujuk berkas laporan atau `### Penanganan Balikan`; cukup dispatcher yang
  menyebut seksi wajib baca.

## Hasil X4 (diagnosis dispatch Profil S)

Dari log (`token_usage.py explorer`, tiga workspace) dan laci `.explore/` di disk:

| Fase · profil · kedalaman | Dispatch | Biaya per agent | Balikan rata-rata |
|---|---|---|---|
| `tech-lead` · gerbang · `ringkas` | 262 | 249k | 12.095 karakter |
| `system-analysis` · S · `menyeluruh` | 148 | 634k | **31.563 karakter** |
| `system-analysis` · B · `menyeluruh` | 90 | 739k | 14.265 karakter |
| `plan` · `ringkas` | 56 | 307k | 16.011 karakter |

145 taskdir ber-PRD memuat 409 laporan gerbang; permukaan tertutup 796/808 (98,5%), 276/409 laporan tertutup penuh
tanpa gap. Jadi dispatch S **bukan** pelanggaran kepatuhan atas "dispatch hanya untuk permukaan yang belum
tertutup": gerbang menutup permukaan dengan satu bukti (`ringkas`), sedangkan PRD menuntut kedalaman `menyeluruh`
(rantai pemanggil, literal `### Error Surface`, invariant, batas transaksi) yang memang tidak ada di laporan gerbang.

Usulan (belum diterapkan, menunggu keputusan user):

1. **Profil S berobjektif sempit**: pointer laporan gerbang menjadi `konteks_diketahui`, dan objective S hanya
   menagih seksi yang tidak dimiliki laporan gerbang (`### Flow & Trace`, `### Rules, Invariants & Config`,
   `### Error Surface`). Hemat sebagian penelusuran ulang; risiko rendah.
2. **Gerbang `menyeluruh` untuk lane `PLANNING` yang hampir pasti ber-PRD**, sehingga S dapat dilewati. Hemat satu
   dispatch per taskdir, tetapi menaikkan biaya gerbang pada rantai yang ternyata `BRIEF` dan memindah keputusan
   chain ke gerbang (bertentangan dengan "panjang rantai milik `analyst`").
3. **Biarkan**: X1 sudah memangkas balikan S terbesar (31,5 ribu karakter) dari context main loop.

Rekomendasi: ukur dulu efek X1 dengan `token_usage.py explorer --since <tanggal rilis>`, lalu putuskan usulan 1.

## Temuan dasar (data log)

| Metrik | nataflow | WMS | OrderHub |
|---|---|---|---|
| Porsi `backend:code-explorer` dari biaya subagent | 44% | 48% | 45% |
| Jumlah dispatch | 56 | 277 | 228 |
| Pemanggilan per agent / output per agent | 19 / 24k | 21 / 23k | 22 / 25k |
| Balikan ke main loop (rata-rata) | 17,5 ribu karakter | ±17 ribu | ±17,5 ribu |

Dispatch `code-explorer` per fase (gabungan tiga workspace):

| Fase | Profil | Kedalaman | Dispatch | Per sesi |
|---|---|---|---|---|
| `tech-lead` | gerbang | `ringkas` | 265 | 1–6 (umumnya 2–3) |
| `system-analysis` | S (surface) | `menyeluruh` | 149 | 2–6 bersama B |
| `system-analysis` | B (blast) | `menyeluruh` | 91 | |
| `plan` | campuran | `ringkas` | 56 | 1–4 |

Dua sebab borosnya:

1. **Dua muara satu isi** (`agents/code-explorer.md` bagian Pelaporan butir 2): laporan ditulis ke `.explore/` lalu
   isi yang sama dikembalikan utuh ke context pendispatch. Model menghasilkan teks yang sama dua kali, dan balikan
   ±5 ribu token menetap di konteks main loop sampai sesi berakhir. Dengan 2–6 dispatch per fase, beban ini
   menumpuk tepat di sesi yang kemudian menjalankan `plan` dan `architect`.
2. **Profil S `system-analysis` tetap sering didispatch** walaupun Fase 1 sudah memanen
   `{taskdir}/.explore/gate-*.md` dan prosanya membatasi dispatch S ke "permukaan yang belum tertutup laporan gerbang".
   Datanya belum cukup untuk memastikan apakah ini karena laporan gerbang (`ringkas`) memang tidak menutup permukaan
   yang dituntut PRD (`menyeluruh`), karena predikat dispatch terlalu longgar, atau karena kepatuhan model.

## Tujuan

1. Balikan explorer ke main loop menjadi ringkas; berkas `.explore/` menjadi satu-satunya isi lengkap.
2. Main loop membaca seksi laporan yang dibutuhkan saja, kapan dibutuhkan.
3. Sebab dispatch S yang tetap tinggi terdiagnosis dengan angka sebelum kebijakannya diubah.

## Keputusan

- **K1 — Backend saja.** `analyst:code-explorer`, `analyst:code-scout`, dan `fullstack:*-explorer` (adaptasi dari agent
  ini) tidak diubah; test yang mematok angka read-window ke sumber backend tetap hijau karena bagian itu tidak
  disentuh.
- **K2 — Berkas = sumber kebenaran.** Isi laporan lengkap hanya di `Berkas laporan`. Balikan ke context memuat:
  baris `confidence:`, tiga angka cakupan (`permukaan_diminta`/`permukaan_tertutup`/`gaps_terbuka`), `### Summary`
  (≤ 8 baris), daftar judul seksi yang ada di berkas, dan path berkas. Plafon ±15 baris.
- **K3 — Pembacaan tertarget, bukan larangan baca ulang.** Larangan "membuka berkasnya untuk memungutnya" di
  `tech-lead/dispatcher/explorer.md` (Penanganan Balikan) dibalik: pendispatch membaca seksi yang dibutuhkan
  (offset/limit atau per heading), tidak pernah berkas utuh bila hanya satu seksi yang dipakai. Prosa tidak mengikat
  tool tertentu.
- **K4 — Kualitas bukti tidak diturunkan.** Kedalaman, kuota jendela baca, Tahap 0 panen, dan kewajiban `file:line`
  tidak berubah di langkah ini.
- **K5 — Kebijakan dispatch S diubah hanya sesudah diagnosis (X4).** Bila diagnosis menunjukkan perubahan predikat
  diperlukan, usulannya dibawa ke user sebagai keputusan baru, bukan langsung diterapkan.

## Kontrak

### X1 — `agents/code-explorer.md` bagian Pelaporan

"Dua muara dan satu isi" diganti: (1) tulis berkas utuh lebih dulu — tidak berubah; (2) balas dengan amplop ringkas
K2. Aturan Format Laporan butir 1–8 tetap berlaku untuk berkas. Frontmatter tetap identitas berkas dan bahan panen
Tahap 0.

### X2 — Dispatcher dan `### Penanganan Balikan`

Enam template memetakan balikan dari amplop ringkas, dan menyebut seksi mana yang wajib dibaca dari berkas untuk
langkah berikutnya:

| Template | Seksi yang dibaca pendispatch (indikatif — dipastikan di Tahap 1) |
|---|---|
| `skills/tech-lead/dispatcher/explorer.md` | `### Key Pointers & Evidence` untuk slot `Bukti`; `### Not Found`/`### Gaps` untuk angka permukaan |
| `skills/system-analysis/dispatcher/explorer-surface.md` | Seksi yang dikutip literal ke PRD (mis. `### Error Surface`), dibaca saat Fase 3 menulis kontrak |
| `skills/system-analysis/dispatcher/explorer-blast.md` | `### Blast Map` untuk impact map 16 dimensi |
| `skills/plan/dispatcher/explorer.md` | `### File Map`/`### Candidate Locations` untuk `## File scope` dan `Anchor` |
| `skills/business-analysis/dispatcher/explorer.md` | Seksi aturan bisnis yang dikutip BRD |
| `skills/debug/dispatcher/explorer.md` | Rantai kausal untuk `RCA.md` |

### X3 — Prosa skill pemakai

`tech-lead/SKILL.md` Fase 1, `system-analysis/SKILL.md` Fase 1, `system-analysis/references/analysis-protocol.md`
bagian A, `plan` (Fase 2 dan `references/slicing-and-scan.md`), `business-analysis`, dan `debug` diselaraskan dengan
X2. Guardrail yang menuntut literal (mis. kolom `Pesan` tabel `## Error`) kini menunjuk ke seksi berkas, bukan ke
balikan.

### X4 — Diagnosis dispatch Profil S

Perluas `scripts/token_usage.py` (atau subperintah terpisah) agar dapat melaporkan, per sesi `system-analysis`:
jumlah laporan gerbang yang terpanen, permukaan tertutup menurut frontmatter laporan gerbang, jumlah dispatch S/B,
dan biaya per profil. Keluarannya ditulis ke bagian Status issue ini beserta usulan (K5).

## Peta blast radius (awal — diverifikasi ulang di tiap tahap)

| Berkas | Item |
|---|---|
| `src/plugins/backend/agents/code-explorer.md` | X1 |
| Enam dispatcher di tabel X2 | X2 |
| `tech-lead`, `system-analysis` (+ `analysis-protocol.md`), `plan` (+ `slicing-and-scan.md`), `business-analysis`, `debug` | X3 |
| `tests/backend/test_common_parsing.py`, `tests/test_lint_plugins.py` (menyebut `code-explorer.md`), `tests/analyst/test_explorer_27.py`, `tests/fullstack/test_alur_23.py`, `tests/frontend/test_08c_text.py` | Verifikasi: hanya patokan read-window, bukan format balikan (K1) |
| `tests/backend/test_explorer_balikan_31.py` (baru) | Patok K2: amplop ±15 baris, berkas = sumber kebenaran, dispatcher menyebut seksi wajib baca |
| `scripts/token_usage.py`, `tests/test_token_usage.py` | X4 |
| `README.md` backend, `flow/backend.md`, `MIGRATION_*`, `plugin.json` | D1 |

## Urutan pengerjaan

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | X4 | Diagnosis dan baseline biaya explorer sebelum apa pun berubah; memastikan tabel seksi X2. |
| 2 | X1 | Kontrak balikan di agent. |
| 3 | X2, X3 | Pendispatch dan prosa skill mengikuti kontrak baru. |
| 4 | Test baru + penyesuaian test lama | Memaku kontrak X1–X3. |
| 5 | D1 | Dokumen, migrasi, versi backend (minor, digabung dengan Langkah 30 bila dirilis bersamaan). |

## Verifikasi ujung ke ujung

- Suite penuh hijau, lint `--base origin/main` 0 FAIL, `claude plugin validate .`.
- Uji manual satu rantai PLANNING di repo nyata: PRD tetap memuat literal pesan error dan impact map berbukti.
- Ukur ulang dengan `token_usage.py`: ukuran balikan explorer ke main loop, output per agent, dan konteks rata-rata
  fase `system-analysis`/`plan` dibandingkan baseline Tahap 1.

## Trade-off yang diterima

- Fase yang butuh detail (`system-analysis`) tetap membaca sebagian berkas, sehingga penghematan konteks di sana
  parsial; penghematan pasti ada di output explorer (tidak lagi ditulis dua kali) dan di fase yang hanya butuh
  ringkasan (`tech-lead`, `plan`).
- Pendispatch bisa lupa membaca seksi yang dibutuhkan dan menulis dari ringkasan; dimitigasi dengan template yang
  menyebut seksi wajib baca per langkah.

## Di luar cakupan

- Explorer plugin lain (K1).
- Perubahan kedalaman, kuota baca, atau predikat dispatch (K4, K5).
- Penggabungan dispatch `tech-lead` dan `system-analysis` menjadi satu penelusuran.
