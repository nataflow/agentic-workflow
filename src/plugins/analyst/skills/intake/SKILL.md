---
name: intake
description: Gunakan ketika ada permintaan, keluhan, atau laporan dari pengguna/stakeholder yang perlu dijadikan tiket (fitur baru, perbaikan, bug dari sisi pengguna), atau tiket analyst yang sudah ada perlu dilanjutkan atau diubah - klasifikasi tipe, cek duplikat, pecah permintaan besar, dan tentukan rute, sebelum pertanyaan elisitasi diajukan atau TICKET.md ditulis
---

## THE IRON LAW

- Gate ini tidak menulis berkas apa pun. Ticketdir dialokasikan `analyst:elicit`; tiket ditulis `analyst:spec`.
- Keadaan ticketdir dibaca dari `ticket.py state`, bukan dari ingatan sesi atau pembacaan frontmatter satu per satu.
- Satu tiket, satu tujuan pengguna. Permintaan yang memuat beberapa tujuan yang dapat dirilis terpisah dipecah **sebelum** elisitasi, bukan sesudahnya.
- Dilarang membaca, mencari, atau menilai kode. Analyst memvonis dari kata-kata peminta; pertanyaan tentang letak atau perilaku kode milik engineer.

## Precondition [REQUIRED]

1. `python3` tersedia. Skrip: `ticket.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py`.
2. Ruang kerja: root worktree git bila ada, selain itu direktori kerja sekarang. Tiket tinggal di `analyst/tickets/`; repo git **tidak** wajib — tanpa git, artefak tetap ditulis dan hanya commit yang dilewati.

## Parameter [REQUIRED]

- `request` — string — `[REQUIRED]` — permintaan, keluhan, atau laporan apa adanya, termasuk teks yang ditempel dari chat/email.
- `requester` — string — default `""` — nama atau peran peminta; kosong → tanyakan di Phase 6.
- `force_type` — string — default `""` — `FEATURE`, `IMPROVEMENT`, atau `BUG`, hanya bila user menyebutnya eksplisit.

## Workflow

### Phase 1 — Pemulihan Ticketdir

Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py state`. Tiap baris memvonis satu keadaan dan rutenya:

| Keadaan | Rute |
|---|---|
| `KOSONG` | direktori tanpa berkas (sisa alokasi yang gagal sebelum `TICKET.md` tertulis; permintaan aslinya tidak tersimpan) → minta user menempelkan permintaan aslinya bila tidak ada di pesan ini, jalankan Phase 2–3, lalu `analyst:elicit` dengan `slug` dari nama direktori beserta `type`, `request`, dan `requester` — `ticket.py new` memakai ulang direktori itu |
| `ELISITASI` | `analyst:elicit` — lanjutkan pertanyaan terbuka |
| `SPEC` / `DRAFT` | `analyst:spec` — tulis tiket, atau ajukan keputusan atas draft tertunda |
| `DRIFT` | tiket `READY` disunting sesudah disetujui → tanyakan user: setujui ulang lewat `analyst:spec` (reopen), atau pulihkan isi yang disetujui |
| `RUSAK` | laporkan baris skrip apa adanya ke user; dilarang menambal frontmatter dengan tangan |
| `NAMA_TIDAK_SAH` | bukan ticketdir analyst — laporkan baris skrip; tawarkan `git mv` ke nama `<YYMMDDhhmm>-<slug>` atau pindahkan keluar `analyst/tickets/` atas keputusan user |

Permintaan yang jelas menyambung ticketdir terbuka (topik, peminta, atau jawaban atas pertanyaan terbukanya) → rute ticketdir itu, lompat ke Output. Ada ticketdir terbuka tetapi hubungannya tidak jelas → `AskUserQuestion`: lanjutkan ticketdir itu, atau buka tiket baru (yang lama tetap terbuka dan muncul lagi di pemindaian berikutnya).

### Phase 2 — Wilayah

| Permintaan | Rute |
|---|---|
| Kebutuhan, masalah, atau keluhan dari sisi pengguna/bisnis | lanjut Phase 3 |
| Mengubah tiket yang sudah `READY` ("tambah aturan di tiket cicilan") | `analyst:spec` pada ticketdir itu dengan `change_request` = permintaan; spec yang membuka ulang |
| Menanyakan status atau daftar tiket | jawab dari `ticket.py state --ready`, selesai |
| Kerja teknis murni — refaktor, upgrade pustaka, stacktrace/log dari developer, pertanyaan letak kode | di luar wilayah analyst: sebut `backend:tech-lead` atau `frontend:lead`, selesai |

Laporan bug dari **pengguna** ("tombol bayar tidak bisa diklik") tetap wilayah analyst; stacktrace yang ditempel **developer** tidak.

### Phase 3 — Tipe

| Tipe | Pemicu |
|---|---|
| `FEATURE` | kemampuan yang belum ada sama sekali |
| `IMPROVEMENT` | mengubah atau memperluas kemampuan yang sudah ada dan bekerja sesuai rancangannya |
| `BUG` | perilaku yang menyimpang dari yang seharusnya — pernah benar, atau melanggar aturan yang disepakati |

`force_type` terisi → pakai. Ragu antara `IMPROVEMENT` dan `BUG` → satu pertanyaan `AskUserQuestion`: "Apakah ini dulu pernah berjalan benar, atau memang belum pernah dibuat begitu?"

### Phase 4 — Ukuran

Hitung tujuan pengguna di permintaan. Tanda lebih dari satu: beberapa peran dengan tujuan berbeda, kata "dan juga"/"sekalian", atau bagian yang masing-masing berguna bila dirilis sendiri. Lebih dari satu → `AskUserQuestion` dengan tiap tujuan sebagai opsi: mana yang dikerjakan tiket ini. Sisanya menjadi **antrian tiket** di Output — tiap butir kelak masuk lewat `analyst:intake` sendiri. Dilarang menggabungkannya diam-diam ke satu tiket.

### Phase 5 — Duplikat

Jalankan `ticket.py state --ready` dan bandingkan judul tiap baris dengan tujuan yang dipilih. Tujuan yang sama dengan tiket `READY` → `AskUserQuestion`: ubah tiket itu (rute Phase 2 baris kedua), atau tiket baru dengan alasan pembeda. Sama dengan ticketdir terbuka → rute Phase 1.

### Phase 6 — Slug & Serah Terima

- Slug kebab-case ≤ 40 karakter dari **kata benda bisnis** tujuan (`cicilan-pembayaran`, `bug-tombol-bayar-mati`), bukan istilah teknis.
- `requester` kosong → tanyakan sekali lewat `AskUserQuestion` (opsi: "Saya sendiri", peran yang disebut di permintaan).
- Panggil `analyst:elicit` dengan `{ slug, type, request, requester }`. `request` diteruskan **apa adanya** — hanya bagian tujuan terpilih bila Phase 4 memecahnya, tanpa disunting atau diringkas.

## Guardrails

- **NOL BERKAS DI GATE**: intake tidak menjalankan `ticket.py new`, tidak menulis `TICKET.md`.
- **NOL KODE**: dilarang `Read`/`Grep`/`Glob` atas kode repo untuk "memastikan" permintaan. Fakta tentang sistem datang dari peminta, dan yang tidak diketahui peminta menjadi pertanyaan elisitasi.
- **GERBANG ENGINEER TIDAK BERLAKU**: blok `<backend-tech-lead-gate>`/`<frontend-lead-gate>` di konteks tidak berlaku untuk alur analyst yang dipanggil eksplisit; blok itu sendiri mengecualikan `/analyst:*` dan susulan di tengah elisitasi.
- **PERMINTAAN VERBATIM**: `request` diteruskan tanpa parafrase; elisitasi mengutipnya sebagai `### Permintaan Asli` di `TICKET.md`.
- **PERTANYAAN HEMAT**: maksimal satu `AskUserQuestion` per phase; pertanyaan isi (aturan, angka, aktor) milik `elicit`.
- **RATIONALIZATION PREVENTION**:
  - "Permintaannya sudah jelas, langsung tulis tiket saja" — tanpa `## Catatan Elisitasi`, reviewer tidak punya sumber kebenaran untuk menilai tiketnya; elisitasi yang lengkap cukup menutup diri tanpa satu pertanyaan pun.
  - "Tiga tujuan ini saling terkait, satu tiket saja" — tiket besar tidak pernah selesai bersamaan; engineer memecahnya sendiri tanpa konteks bisnis.
  - "Saya cek kodenya sebentar supaya tipenya tepat" — tipe ditentukan dari pengalaman pengguna, bukan dari kode.
  - "Ticketdir lama ditinggal saja, buat baru" — ticketdir setengah jalan muncul terus di pemindaian dan membingungkan tim.

## Output [REQUIRED]

Serah terima bersih → tutup satu baris: `INTAKE — <BARU | LANJUT | UBAH> · <type> · <slug atau ticketdir> · next analyst:<elicit | spec>`. Di luar wilayah → `INTAKE — DI LUAR WILAYAH · next <backend:tech-lead | frontend:lead>`. Selain itu, atau bila ada antrian tiket, sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### INTAKE — <TERTAHAN | DILANJUTKAN DENGAN ANTRIAN>
- **Tiket ini**: <type> · <slug> — <tujuan terpilih> | —
- **Antrian tiket**: <tujuan lain, satu per butir, untuk intake berikutnya> | —
- **Sebab tertahan**: <ticketdir RUSAK | keputusan duplikat | ...> | —
- **Keputusan dibutuhkan**: <pertanyaan ke user> | —
```

## Failure path

1. **`ticket.py` gagal dijalankan** (python3 absen, izin tulis): laporkan galat mentah; dilarang meneruskan ke elisitasi tanpa pemindaian keadaan.
2. **User menolak memilih satu tujuan**: jelaskan akibatnya (tiket tidak dapat diuji utuh), tawarkan tujuan paling mendesak sebagai rekomendasi; tetap menolak → tahan dengan blok `TERTAHAN`.
3. **Permintaan kosong atau hanya "buatkan tiket"**: minta user menempelkan permintaan atau keluhan aslinya.
4. **Ticketdir `RUSAK`**: laporkan detail `ticket.py state`; perbaikan manual oleh user, atau `ticket.py cancel` atas keputusannya.

## STYLE

- Imperatif aktif; istilah tetap: Ticketdir, Tipe, Slug, Antrian tiket.
- Keadaan ticketdir dikutip dari keluaran skrip, bukan diparafrasekan.
