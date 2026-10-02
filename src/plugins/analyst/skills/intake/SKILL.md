---
name: intake
description: Gunakan ketika ada permintaan, keluhan, atau laporan dari pengguna/stakeholder yang perlu dijadikan tiket (fitur baru, perbaikan, bug dari sisi pengguna) — termasuk beberapa permintaan sekaligus, hingga 5 tiket diproses berurutan — perubahan teknis dari lead engineer yang perlu dikunci jadi tiket TECH sebelum dikerjakan (refaktor, relasi data, arsitektur, kinerja, upgrade dependensi), tiket analyst yang sudah ada perlu dilanjutkan atau diubah, tiket perlu dibatalkan, atau tiket READY perlu disinkron ulang ke nataflow - klasifikasi tipe, cek duplikat, pecah permintaan besar atau susun batch berurutan, dan tentukan rute, sebelum pertanyaan elisitasi diajukan atau TICKET.md ditulis
---

## THE IRON LAW

- Gate ini tidak menulis berkas apa pun. Ticketdir dialokasikan `analyst:elicit`; tiket ditulis `analyst:spec`. Satu-satunya tulisan keluar dari gate adalah sinkron ulang tiket `READY` (atau pembatalannya) ke nataflow (Phase 2), dan isinya ditentukan `ticket.py sync-payload`, bukan gate. Pembatalan tiket sendiri dijalankan `analyst:spec`.
- Keadaan ticketdir dibaca dari `ticket.py state`, bukan dari ingatan sesi atau pembacaan frontmatter satu per satu.
- Satu tiket, satu tujuan pengguna. Permintaan yang memuat beberapa tujuan yang dapat dirilis terpisah dipecah **sebelum** elisitasi, bukan sesudahnya. 2–5 tujuan diproses sebagai **batch** berurutan, satu tiket penuh sebelum tiket berikutnya (`references/batch.md`).
- Dilarang membaca, mencari, atau menilai kode — juga untuk tiket `TECH`. Gate memvonis dari kata-kata peminta; bukti kode tiket `TECH` dikumpulkan `analyst:elicit`, dan pertanyaan tentang letak atau perilaku kode milik engineer.

## Precondition [REQUIRED]

1. `python3` tersedia. Skrip: `ticket.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py`. Aturan batch: `references/batch.md`.
2. Ruang kerja: root worktree git bila ada, selain itu direktori kerja sekarang. Tiket tinggal di `analyst/tickets/`; repo git **tidak** wajib — tanpa git, artefak tetap ditulis dan hanya commit yang dilewati. Repo bersinkron nataflow (`.claude/nataflow.json` ada): `ticket.py new` menulis `analyst/tickets/.gitignore` bila belum ada, sehingga ticketdir tetap di disk tetapi tidak di-commit.

## Parameter [REQUIRED]

- `request` — string — `[REQUIRED]` — permintaan, keluhan, atau laporan apa adanya, termasuk teks yang ditempel dari chat/email.
- `requester` — string — default `""` — nama atau peran peminta; kosong → tanyakan di Phase 6.
- `force_type` — string — default `""` — `FEATURE`, `IMPROVEMENT`, `BUG`, atau `TECH`, hanya bila user menyebutnya eksplisit.
- `force_category` — string — default `""` — `REFACTOR`, `DATA_MODEL`, `ARCHITECTURE`, `PERFORMANCE`, atau `DEPENDENCY` untuk tiket `TECH`, hanya bila user menyebutnya eksplisit.

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

Permintaan yang jelas menyambung ticketdir terbuka (topik, peminta, atau jawaban atas pertanyaan terbukanya) → rute ticketdir itu, lompat ke Output. Ada ticketdir terbuka tetapi hubungannya tidak jelas → `AskUserQuestion`: lanjutkan ticketdir itu, atau buka tiket baru (yang lama tetap terbuka dan muncul lagi di pemindaian berikutnya). Ticketdir yang dilanjutkan bersegmen `batch <id> <k>/<N>` → lanjutkan batch itu dari tiket **terbuka berurutan terkecil**-nya per `references/batch.md` bagian 9, bukan dari tiket yang kebetulan disebut.

### Phase 2 — Wilayah

| Permintaan | Rute |
|---|---|
| Kebutuhan, masalah, atau keluhan dari sisi pengguna/bisnis | lanjut Phase 3 |
| Mengubah tiket yang sudah `READY` ("tambah aturan di tiket cicilan") | `analyst:spec` pada ticketdir itu dengan `change_request` = permintaan; spec yang membuka ulang |
| Membatalkan tiket ("batalkan tiket cicilan", tidak jadi dikerjakan) | cari ticketdir-nya di `ticket.py state --all` (lebih dari satu kandidat → `AskUserQuestion`), lalu `analyst:spec` pada ticketdir itu dengan `cancel_request` = alasan user; spec yang membatalkan dan menyinkronkan pembatalannya |
| Menanyakan status atau daftar tiket | jawab dari `ticket.py state --ready`, selesai |
| Sinkron ulang tiket ke nataflow ("sinkron ulang tiket cicilan", sesudah segmen `nataflow GAGAL`) | cari ticketdir-nya di `ticket.py state --all` (lebih dari satu kandidat → `AskUserQuestion`). `READY`, atau `DIBATALKAN` sesudah pernah `READY` (pembatalan task cermin, 15 A6) → jalankan prosedur `${CLAUDE_PLUGIN_ROOT}/skills/spec/references/nataflow-sync.md` apa adanya atas ticketdir itu tanpa `reopen`, lalu tutup dengan baris `SINKRON`; `DRIFT` → rute Phase 1 baris `DRIFT`; keadaan lain → belum ada yang disetujui untuk disinkronkan, rute Phase 1 keadaannya |
| Perubahan teknis yang perlu **dikunci sebelum dikerjakan** — biasanya dari lead engineer: refaktor lintas modul, relasi data, batas modul atau arah dependensi, kinerja, upgrade pustaka yang berdampak | lanjut Phase 3 sebagai `TECH` |
| Kerja teknis kecil atau diagnosis — perbaikan satu berkas, stacktrace/log dari developer, pertanyaan letak kode | di luar wilayah analyst: sebut `backend:tech-lead` atau `frontend:lead`, selesai |

Laporan bug dari **pengguna** ("tombol bayar tidak bisa diklik") tetap wilayah analyst; stacktrace yang ditempel **developer** tidak. Ragu antara tiket `TECH` dan kerja langsung → satu pertanyaan `AskUserQuestion`: "Perlu dikunci jadi tiket yang disetujui dulu, atau langsung dikerjakan engineer?"

### Phase 3 — Tipe

| Tipe | Pemicu |
|---|---|
| `FEATURE` | kemampuan yang belum ada sama sekali |
| `IMPROVEMENT` | mengubah atau memperluas kemampuan yang sudah ada dan bekerja sesuai rancangannya |
| `BUG` | perilaku yang menyimpang dari yang seharusnya — pernah benar, atau melanggar aturan yang disepakati |
| `TECH` | perubahan teknis dari baris kedua tabel Phase 2 — yang diminta struktur, bukan perilaku baru bagi pengguna |

`force_type` terisi → pakai. Ragu antara `IMPROVEMENT` dan `BUG` → satu pertanyaan `AskUserQuestion`: "Apakah ini dulu pernah berjalan benar, atau memang belum pernah dibuat begitu?"

Tiket `TECH` juga mendapat `category` (`force_category` terisi → pakai), dari pemicu tabel bagian 4 `${CLAUDE_PLUGIN_ROOT}/skills/elicit/references/elicitation-tech.md`: `REFACTOR` (struktur berubah, perilaku tetap), `DATA_MODEL` (relasi, tabel, kolom, constraint), `ARCHITECTURE` (batas modul, arah dependensi, pola lintas fitur), `PERFORMANCE` (latensi, kueri, beban), `DEPENDENCY` (pustaka atau runtime naik versi atau diganti). Lebih dari satu cocok → pilih yang menentukan cara membuktikan selesainya; masih ragu → satu pertanyaan `AskUserQuestion` dengan kandidatnya.

### Phase 4 — Ukuran

Hitung tujuan pengguna di permintaan. Tanda lebih dari satu: daftar bernomor atau berpoin, beberapa peran dengan tujuan berbeda, kata "dan juga"/"sekalian", atau bagian yang masing-masing berguna bila dirilis sendiri. Satu tujuan → tiket tunggal. 2–5 tujuan → **batch**: tiap tujuan menjadi tiket sendiri, diurutkan **tanpa pertanyaan** menurut `references/batch.md` bagian 3, dan Phase 2–3 serta 5–6 berlaku per tujuan. Lebih dari 5 → lima teratas masuk batch, sisanya **antrian tiket** di Output — tiap butir kelak masuk lewat `analyst:intake` sendiri. User eksplisit meminta satu tujuan dulu → tiket tunggal, sisanya antrian tiket. Butir yang bukan tiket baru tidak ikut batch (`references/batch.md` bagian 1). Dilarang menggabungkan beberapa tujuan diam-diam ke satu tiket.

Tiket `TECH` dihitung **per repo**: bukti `path:baris`-nya diperiksa terhadap root repo tempat tiket tinggal, dan `ticket_source` hilir hanya membaca tiket di repo engineer itu sendiri. Perubahan yang menyentuh dua repo (mis. backend dan frontend) → tiket ini untuk repo ruang kerja sekarang, bagian repo lain masuk antrian tiket dengan catatan *buka dari repo `<nama>`*. Ruang kerja sekarang bukan repo yang diubah (mis. folder induk beberapa repo) → tahan dengan blok `TERTAHAN`, sebab `ruang kerja bukan repo yang diubah`.

### Phase 5 — Duplikat

Jalankan `ticket.py state --ready` dan bandingkan judul tiap baris dengan tujuan yang dipilih. Tujuan yang sama dengan tiket `READY` → `AskUserQuestion`: ubah tiket itu (rute Phase 2 baris kedua), atau tiket baru dengan alasan pembeda. Sama dengan ticketdir terbuka → rute Phase 1.

Batch: bandingkan tiap tujuan, juga antar-tujuan dalam batch. Butir kembar dalam batch menjadi satu tiket (`Digabung`). Tujuan yang sama dengan tiket `READY` atau ticketdir terbuka keluar dari batch tanpa pertanyaan dan disebut di `Di luar batch` beserta rutenya di atas; batch tidak menunggu keputusannya.

### Phase 6 — Slug & Serah Terima

- Slug kebab-case ≤ 40 karakter, unik dalam batch, dari **kata benda bisnis** tujuan (`cicilan-pembayaran`, `bug-tombol-bayar-mati`), bukan istilah teknis. Tiket `TECH` memakai kata benda teknis objeknya (`relasi-project-workspace`, `upgrade-gorm-v2`). Istilah domain berbahasa Inggris dari permintaan tidak diterjemahkan (`report-order-created-at-detik`, bukan `laporan-pesanan-waktu-dibuat`).
- `requester` kosong → tanyakan sekali lewat `AskUserQuestion` (opsi: "Saya sendiri", peran yang disebut di permintaan); batch: sekali untuk seluruh batch per `references/batch.md` bagian 4.
- Panggil `analyst:elicit` dengan `{ slug, type, category, request, requester }` (`category` hanya untuk `TECH`). `request` diteruskan **apa adanya** — hanya bagian tujuan terpilih bila Phase 4 memecahnya, tanpa disunting atau diringkas.
- Batch: sajikan blok `INTAKE — BATCH` (`references/batch.md` bagian 10), lalu panggil `analyst:elicit` sekali dengan `{ batch: [{ slug, type, category, request, requester }, …] }` berurutan. `request` tiap tiket per `references/batch.md` bagian 2.

## Guardrails

- **NOL BERKAS DI GATE**: intake tidak menjalankan `ticket.py new`, tidak menulis `TICKET.md`.
- **NOL KODE**: dilarang `Read`/`Grep`/`Glob` atas kode repo untuk "memastikan" permintaan. Fakta tentang sistem datang dari peminta, dan yang tidak diketahui peminta menjadi pertanyaan elisitasi; konteks kode dikumpulkan `analyst:elicit` lewat subagent `code-scout`.
- **GERBANG ENGINEER TIDAK BERLAKU**: blok `<backend-tech-lead-gate>`/`<frontend-lead-gate>` di konteks tidak berlaku untuk alur analyst yang dipanggil eksplisit; blok itu sendiri mengecualikan `/analyst:*` dan susulan di tengah elisitasi.
- **PERMINTAAN VERBATIM**: `request` diteruskan tanpa parafrase; elisitasi mengutipnya sebagai `### Permintaan Asli` di `TICKET.md`.
- **PERTANYAAN HEMAT**: maksimal satu `AskUserQuestion` per phase; pertanyaan isi (aturan, angka, aktor) milik `elicit`. Batch: maksimal satu per tiket per phase, dan tiap `AskUserQuestion` hanya tentang satu tiket; urutan batch tidak pernah ditanyakan.
- **RATIONALIZATION PREVENTION**:
  - "Permintaannya sudah jelas, langsung tulis tiket saja" — tanpa `## Catatan Elisitasi`, reviewer tidak punya sumber kebenaran untuk menilai tiketnya; elisitasi yang lengkap cukup menutup diri tanpa satu pertanyaan pun.
  - "Tiga tujuan ini saling terkait, satu tiket saja" — tiket besar tidak pernah selesai bersamaan; engineer memecahnya sendiri tanpa konteks bisnis.
  - "Saya cek kodenya sebentar supaya tipenya tepat" — tipe ditentukan dari pengalaman pengguna, bukan dari kode; untuk `TECH`, dari kata-kata peminta. Pembuktian kode milik `analyst:elicit`.
  - "Refaktor backend dan frontend ini satu tujuan, satu tiket saja" — tiket `TECH` dibuktikan dan diserahkan per repo; tiket gabungan tidak lolos validator di repo mana pun.
  - "Ticketdir lama ditinggal saja, buat baru" — ticketdir setengah jalan muncul terus di pemindaian dan membingungkan tim.
  - "Lima tiket ini mirip, satu `AskUserQuestion` untuk semuanya supaya cepat" — satu panggilan satu tiket; jawaban yang tercampur konteks berakhir di tiket yang salah, dan log tiap tiket harus berdiri sendiri di depan reviewer.
  - "Tiket ketiga paling gampang, kerjakan duluan" — urutan batch dari prasyarat dan urgensi peminta (`references/batch.md` bagian 3), bukan dari kemudahan analis.

## Output [REQUIRED]

Serah terima bersih → tutup satu baris: `INTAKE — <BARU | LANJUT | UBAH> · <type>[/<category>] · <slug atau ticketdir> · next analyst:<elicit | spec>`. Batch → blok `INTAKE — BATCH` (`references/batch.md` bagian 10), lalu baris `INTAKE — BATCH · <N> tiket · next analyst:elicit`; antrian tiket dan butir di luar batch masuk blok itu. Di luar wilayah → `INTAKE — DI LUAR WILAYAH · next <backend:tech-lead | frontend:lead>`. Sinkron ulang → `SINKRON — <ticketdir> · nataflow <dibuat #<code> | diperbarui #<code> | dibatalkan #<code> | dilewati | GAGAL: <sebab>>`; `GAGAL` tidak mengubah `READY`. Selain itu, atau bila tiket tunggal punya antrian tiket, sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### INTAKE — <TERTAHAN | DILANJUTKAN DENGAN ANTRIAN>
- **Tiket ini**: <type> · <slug> — <tujuan terpilih> | —
- **Antrian tiket**: <tujuan lain, satu per butir, untuk intake berikutnya> | —
- **Sebab tertahan**: <ticketdir RUSAK | keputusan duplikat | ruang kerja bukan repo yang diubah | ...> | —
- **Keputusan dibutuhkan**: <pertanyaan ke user> | —
```

## Failure path

1. **`ticket.py` gagal dijalankan** (python3 absen, izin tulis): laporkan galat mentah; dilarang meneruskan ke elisitasi tanpa pemindaian keadaan.
2. **User bersikeras beberapa tujuan dijadikan satu tiket**: jelaskan akibatnya (tiket tidak dapat diuji utuh), tawarkan batch berurutan; tetap menolak → tahan dengan blok `TERTAHAN`.
3. **Permintaan kosong atau hanya "buatkan tiket"**: minta user menempelkan permintaan atau keluhan aslinya.
4. **Ticketdir `RUSAK`**: laporkan detail `ticket.py state`; perbaikan manual oleh user, atau `ticket.py cancel` atas keputusannya.

## STYLE

- Imperatif aktif; istilah tetap: Ticketdir, Tipe, Slug, Antrian tiket, Batch, Urutan.
- Keadaan ticketdir dikutip dari keluaran skrip, bukan diparafrasekan.
