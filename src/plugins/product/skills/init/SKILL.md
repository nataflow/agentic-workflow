---
name: init
description: Gunakan ketika ada gagasan produk baru yang perlu diinisiasi dari nol (folder kosong), fitur baru untuk aplikasi yang sudah ada, atau improvement fitur yang sudah berjalan (codebase), dan yang dibutuhkan dokumen inisiasi CHARTER.md enam pilar (Purpose, Actors, Business Process, Business Rules, Success Criteria, Scope) — atau charter yang sudah ada perlu dilanjutkan, diubah, atau dibatalkan; bukan untuk tiket kerja satu tujuan (itu analyst:intake) - deteksi ruang kerja, mode NEW_PRODUCT/NEW_FEATURE/IMPROVEMENT, guard konteks minimum atas permintaan yang terlalu umum, cek duplikat, dan slug, sebelum elisitasi dimulai atau satu folder pun dibuat
---

## THE IRON LAW

- Gate ini tidak menulis berkas apa pun. Charterdir dialokasikan `product:discover` lewat `charter.py new`; kartu
  ditulis `product:spec`.
- Permintaan yang terlalu umum **tidak** diteruskan. Tiga butir konteks minimum per mode wajib lolos
  `charter.py guard` sebelum serah terima, dan butir yang kosong tidak pernah diisi tebakan
  (`references/konteks-minimum.md`).
- Mode ditentukan skrip dan kata-kata peminta, bukan selera: folder tanpa kode selalu `NEW_PRODUCT`; codebase
  memilih `NEW_FEATURE` atau `IMPROVEMENT`, dan pilihan itu diverifikasi `product:code-scout` sebelum folder dibuat.
- Keadaan charterdir dibaca dari `charter.py state`, bukan dari ingatan sesi.
- Konteks utama tidak membaca kode. Satu-satunya pembacaan kode di gate ini adalah satu dispatch
  `product:code-scout` `mode: CEK_FITUR` (Phase 5).

## Precondition [REQUIRED]

1. Skrip: `charter.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py`. Guard: `references/konteks-minimum.md`.
   Template dispatch scout: `${CLAUDE_PLUGIN_ROOT}/skills/discover/dispatcher/scout.md`.
2. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/check_preconditions.py`. `PASS` → catat dari baris
   `Terselesaikan:` nilai `root`, `git`, `workspace` (`EMPTY` | `CODEBASE`), `bukti`, `mode_diizinkan`, dan
   `charter_terbuka`. `FAIL` → remediasi per baris `Tindakan` lalu berhenti; check 3 (home atau root filesystem)
   → minta user membuat atau masuk ke folder proyek lebih dulu. Repo git **tidak** wajib: folder kosong tanpa git
   adalah tempat `NEW_PRODUCT`.

## Parameter [REQUIRED]

- `request` — string — `[REQUIRED]` — gagasan atau permintaan apa adanya, termasuk teks tempelan dari chat/email.
- `requester` — string — default `""` — nama atau peran peminta; kosong → tanyakan di Phase 7.
- `force_mode` — string — default `""` — `NEW_PRODUCT`, `NEW_FEATURE`, atau `IMPROVEMENT`, hanya bila user
  menyebutnya eksplisit.

## Workflow

### Phase 1 — Pemulihan Charterdir

Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py state`:

| Keadaan | Rute |
|---|---|
| `EMPTY` | sisa alokasi gagal → jalankan Phase 3–7 seperti baru; `charter.py new` memakai ulang direktori itu bila slug-nya sama |
| `ELICITATION` | `product:discover` dengan `charterdir` itu |
| `DRAFT` / `REVIEW` | `product:spec` dengan `charterdir` itu |
| `DRIFT` | charter `APPROVED` disunting sesudah disetujui → `AskUserQuestion`: setujui ulang lewat `product:spec` (reopen), atau pulihkan isi yang disetujui |
| `BROKEN` | laporkan baris skrip apa adanya; dilarang menambal frontmatter dengan tangan |

Permintaan yang jelas menyambung charterdir terbuka (topik, peminta, atau jawaban atas pertanyaan terbukanya) →
rute charterdir itu, lompat ke Output. Ada charterdir terbuka tetapi hubungannya tidak jelas → `AskUserQuestion`:
lanjutkan yang itu, atau inisiasi baru (yang lama tetap terbuka).

### Phase 2 — Wilayah

| Permintaan | Rute |
|---|---|
| Gagasan produk, fitur baru, atau improvement yang belum punya arah tertulis | lanjut Phase 3 |
| Mengubah charter `APPROVED` ("tambah aktor kurir di charter kasir") | `product:spec` pada charterdir itu dengan `change_request` = permintaan |
| Membatalkan charter | cari charterdir-nya di `charter.py state --all` (lebih dari satu kandidat → `AskUserQuestion`), lalu `product:spec` dengan `cancel_request` = alasan user |
| Menanyakan status atau daftar charter | jawab dari `charter.py state --all`, selesai |
| Satu perubahan kecil berbatas jelas yang langsung bisa dijadikan tiket (satu layar, satu aturan, satu laporan) | di luar wilayah: sebut `analyst:intake`, selesai |
| Bug, stacktrace, atau kerja teknis | di luar wilayah: sebut `analyst:intake` (bug dari pengguna) atau `backend:tech-lead` / `frontend:lead`, selesai |

Ragu antara charter dan tiket → satu `AskUserQuestion`: "Ini inisiatif yang perlu arah lengkap (tujuan, aktor,
alur, aturan, ukuran sukses, batas versi pertama), atau satu perubahan yang langsung bisa dijadikan tiket?"

### Phase 3 — Mode Sementara

- `workspace=EMPTY` → `NEW_PRODUCT`, tanpa pertanyaan. `force_mode` codebase di folder kosong → jelaskan bahwa tidak
  ada kode yang dikembangkan; tawarkan `NEW_PRODUCT`, atau minta user menjalankan dari repo yang dikembangkan.
- `workspace=CODEBASE`:
  - Permintaan menyebut kemampuan yang **belum ada** ("tambah fitur cicilan") → `NEW_FEATURE`.
  - Permintaan mengubah atau memperbaiki kemampuan yang **sudah berjalan** ("alur retur terlalu panjang") →
    `IMPROVEMENT`.
  - Ragu → satu `AskUserQuestion`: "Kemampuan ini sudah ada di aplikasi dan mau diubah, atau belum ada sama
    sekali?"
  - User eksplisit menginisiasi **produk baru** di folder ber-kode (mis. repo dokumen yang memuat skrip) →
    `AskUserQuestion` konfirmasi; ya → `NEW_PRODUCT` dengan `confirm_workspace: true`.
- `force_mode` terisi dan cocok dengan `mode_diizinkan` → pakai.

### Phase 4 — Guard Konteks Minimum

Baca `references/konteks-minimum.md`. Petakan permintaan ke tiga butir mode itu (`--untuk`, `--masalah`,
`--lingkup`); butir yang tersurat diisi kata-kata peminta. Butir kosong → satu `AskUserQuestion` berisi opsi
konkret (bagian 4 rujukan). Lalu:

`python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/charter.py guard --mode <mode> --untuk "<...>" --masalah "<...>" --lingkup "<...>"`

`GUARD PASS` → Phase 5. `GUARD FAIL` → tanyakan hanya butir yang disebut keluarannya; maksimal dua putaran, lalu
blok `INIT — TERTAHAN` (bagian 5 rujukan).

### Phase 5 — Verifikasi Mode (codebase saja)

`NEW_PRODUCT` → lompat ke Phase 6. Mode codebase → muat
`${CLAUDE_PLUGIN_ROOT}/skills/discover/dispatcher/scout.md`, hidrasi `mode: CEK_FITUR`, `root`, dan satu
pertanyaan `P1` dari `--lingkup` (fitur atau area dalam kata-kata peminta), lalu dispatch `product:code-scout`
langsung. Balikan dipakai di sini dan diteruskan ke `product:discover` sebagai `scout_awal`:

| Mode sementara | Balikan `P1` | Tindakan |
|---|---|---|
| `IMPROVEMENT` | `Ditemukan` | mode tetap |
| `IMPROVEMENT` | `Tidak ditemukan` | `AskUserQuestion`: fitur yang dimaksud bernama lain (sebut namanya → satu dispatch ulang), atau ini sebenarnya `NEW_FEATURE` |
| `NEW_FEATURE` | `Tidak ditemukan` | mode tetap |
| `NEW_FEATURE` | `Ditemukan` (kemampuan serupa sudah ada) | `AskUserQuestion`: kembangkan yang ada (`IMPROVEMENT`), atau tetap fitur terpisah (`NEW_FEATURE`) beserta alasan pembedanya |
| apa pun | `Belum disisir`, `Repo: tanpa kode`, atau scout gagal dua kali | mode tetap; sebut di Output bahwa verifikasi tidak berjalan |

Mode berubah → jalankan ulang `charter.py guard` dengan mode baru (label butirnya berbeda); butir yang tidak lagi
pas ditanyakan sekali.

### Phase 6 — Duplikat

Jalankan `charter.py state --all` dan bandingkan judul serta Konteks Awal tiap charterdir dengan inisiatif ini.
Sama dengan charter `APPROVED` → `AskUserQuestion`: ubah charter itu (rute Phase 2 baris kedua), atau charter baru
beserta alasan pembeda. Sama dengan charterdir terbuka → rute Phase 1.

### Phase 7 — Slug & Serah Terima

- Slug kebab-case ≤ 40 karakter dari **kata benda bisnis** inisiatif (`kasir-umkm`, `cicilan-pembayaran`,
  `retur-barang`), bukan istilah teknis. Istilah domain berbahasa Inggris tidak diterjemahkan.
- Judul kerja ≤ 12 kata: `NEW_PRODUCT` — nama produk atau "<kemampuan inti> untuk <segmen>"; `NEW_FEATURE` —
  "<kemampuan> di <area>"; `IMPROVEMENT` — "<perubahan> <fitur>".
- `requester` kosong → tanyakan sekali lewat `AskUserQuestion` (opsi: "Saya sendiri", peran yang disebut permintaan).
- Panggil `product:discover` dengan `{ mode, slug, title, untuk, masalah, lingkup, request, requester,
  confirm_workspace, scout_awal }`. `request` diteruskan **apa adanya**, tanpa disunting atau diringkas.

## Guardrails

- **NOL BERKAS DI GATE**: init tidak menjalankan `charter.py new` dan tidak menulis `CHARTER.md`.
- **GUARD LEWAT SKRIP**: dilarang menyatakan konteks "sudah cukup" tanpa `GUARD PASS`.
- **NOL KODE DI KONTEKS UTAMA**: dilarang `Read`/`Grep`/`Glob` atas kode repo; verifikasi mode hanya lewat satu
  dispatch `product:code-scout` (ditambah satu ulang bila user menyebut nama fitur lain).
- **PERMINTAAN VERBATIM**: `request` diteruskan tanpa parafrase; discover mengutipnya sebagai `### Permintaan Asli`.
- **PERTANYAAN HEMAT**: maksimal satu `AskUserQuestion` per phase, kecuali putaran kedua guard. Pertanyaan isi
  (aktor, alur, aturan, angka) milik `product:discover`.
- **GERBANG ENGINEER TIDAK BERLAKU**: blok `<backend-tech-lead-gate>`/`<frontend-lead-gate>` di konteks tidak berlaku
  untuk alur `product` yang dipanggil eksplisit.
- **RATIONALIZATION PREVENTION**:
  - "Aplikasi keuangan pasti untuk UMKM, isi saja" — segmen yang ditebak menjadi Purpose yang salah, dan seluruh
    pilar sesudahnya dibangun di atasnya.
  - "Guard ini merepotkan user, langsung elisitasi saja" — tiga butir itu pertanyaan pertama elisitasi juga; guard
    hanya memastikan pertanyaan itu dijawab sebelum folder dibuat.
  - "Saya intip kodenya sebentar supaya modenya tepat" — pembacaan kode milik `product:code-scout`; konteks utama
    yang membaca kode menghabiskan konteks untuk bukti yang tidak tercatat.
  - "Fiturnya tidak ditemukan scout, saya anggap NEW_FEATURE saja" — bisa jadi namanya berbeda di aplikasi; tanyakan
    dulu, karena IMPROVEMENT dan NEW_FEATURE menghasilkan charter berbentuk berbeda.

## Output [REQUIRED]

Serah terima bersih → satu baris: `INIT — <BARU | LANJUT | UBAH | BATAL> · <mode> · <slug atau charterdir> ·
verifikasi mode <scout cocok | diubah ke <mode> | tidak berjalan | -> · next product:<discover | spec>`. Di luar
wilayah → `INIT — DI LUAR WILAYAH · next <analyst:intake | backend:tech-lead | frontend:lead>`. Selain itu sajikan
blok berikut dan hapus baris bernilai `—`:

```markdown
### INIT — TERTAHAN
- **Mode**: <mode> · ruang kerja <EMPTY | CODEBASE>
- **Konteks minimum**: <butir yang sudah terisi> · belum: <butir yang kosong atau terlalu umum>
- **Sebab tertahan**: <konteks minimum tidak terjawab | keputusan duplikat | charterdir BROKEN | ruang kerja tidak sah | ...>
- **Pertanyaan siap diteruskan**: <pertanyaan untuk pengambil keputusan> | —
```

## Failure path

1. **`check_preconditions.py` atau `charter.py` gagal dijalankan** (python3 absen, izin tulis): laporkan galat
   mentah; dilarang meneruskan ke elisitasi tanpa pemindaian keadaan.
2. **User menolak menjawab konteks minimum** sesudah dua putaran: blok `INIT — TERTAHAN`; dilarang mengisi butir
   dengan tebakan.
3. **Permintaan kosong atau hanya "buatkan charter"**: minta user menceritakan gagasan atau masalahnya lebih dulu.
4. **Charterdir `BROKEN`**: laporkan detail `charter.py state`; perbaikan manual oleh user, atau `charter.py cancel`
   atas keputusannya.

## STYLE

- Imperatif aktif; istilah tetap: Charterdir, Mode, Konteks Minimum, Slug.
- Keadaan charterdir dan keluaran guard dikutip dari skrip, bukan diparafrasekan.
