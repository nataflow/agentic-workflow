# Batch Intake — Beberapa Tiket Berurutan

Dimuat `analyst:intake` (Phase 1 dan 4–6), `analyst:elicit` (alokasi dan penelusuran kode awal batch, tiket tertahan), dan `analyst:spec` (lanjut ke tiket berikutnya). Ini satu-satunya rumah aturan batch: skill lain merujuk ke sini dan dilarang menulis ulang isinya. `<ticket.py>` di bawah adalah path skrip dari Precondition skill pemuatnya.

## 1. Kapan Batch

- Satu pesan memuat **2–5 tujuan pengguna** yang masing-masing menjadi tiket baru → batch. Satu tujuan → tiket tunggal, tanpa field batch.
- Lebih dari 5 tujuan → lima teratas menurut urutan (bagian 3) masuk batch; sisanya **antrian tiket** di blok intake.
- User eksplisit meminta satu tujuan dulu ("catat yang cicilan saja") → tiket tunggal; sisanya antrian tiket.
- Batch hanya untuk **tiket baru**. Butir lain di pesan yang sama — ubah tiket `READY`, batalkan, sinkron ulang, tanya status, kerja di luar wilayah, atau tujuan yang sama dengan tiket `READY`/ticketdir terbuka (intake Phase 5) — tidak ikut batch: sebut beserta rutenya di baris `Di luar batch`, dan jalankan hanya bila user memintanya sesudah batch.
- Dua butir dengan tujuan sama → satu tiket, disebut di baris `Digabung`.
- Tipe boleh campur, termasuk `TECH`; tiap tiket memakai panduan tipenya sendiri. Bagian `TECH` untuk repo lain tetap masuk antrian tiket (intake Phase 4).

## 2. Permintaan Asli per Tiket

- Butir yang tertulis terpisah (nomor, poin, paragraf sendiri) → potongan butir itu **apa adanya**, tanpa nomor atau penanda daftarnya.
- Tujuan yang bercampur dalam satu paragraf → teks **utuh** di tiap tiket. `analyst:elicit` mencatat tujuan lain di pilar `Batas Cakupan` tiket itu sebagai `<tujuan> — tiket <slug>`, tanpa menanyakannya.

## 3. Urutan

Ditentukan tanpa pertanyaan, dari kata-kata peminta saja (intake tetap tanpa kode). Kriteria berurutan:

1. **Prasyarat** — tujuan yang menurut peminta harus ada lebih dulu ("sesudah cicilan jalan, baru laporan piutangnya") mendahului tujuan yang bergantung padanya.
2. **Urgensi yang disebut** — tenggat, pengguna yang sedang terhambat, atau bug yang sedang berdampak mendahului yang tidak menyebut urgensi.
3. **Seri** → urutan kemunculan di pesan user.

Urutan disajikan sekali di blok `INTAKE — BATCH` (bagian 10) sebelum tiket pertama dimulai. Koreksi urutan dari user sebelum tiket pertama dialokasikan → susun ulang; sesudah dialokasikan, urutan tetap.

## 4. Peminta

`requester` wajib untuk tiap `ticket.py new`, dan semua tiket dialokasikan di awal (bagian 5). Peminta yang belum disebut ditanyakan **sekali untuk seluruh batch** lewat `AskUserQuestion`: *Saya sendiri*, peran yang disebut permintaan, atau *Berbeda per tiket* — user menyebut nama per nomor tiket lewat *Other*.

## 5. Alokasi — `analyst:elicit`, Awal Batch

Semua ticketdir dialokasikan sebelum tiket pertama dielisitasi, supaya permintaan asli tiap tiket langsung tersegel di disk.

1. Tiket urutan 1: `python3 <ticket.py> new --slug <slug> --type <type> [--category <category>] --requester "<requester>" --urutan 1/<N> --request - <<'EOF'`, lalu `request` tiket itu apa adanya, lalu `EOF`. Keluaran `NEW PASS: … · batch=<id> urutan=1/<N>` — `<id>` adalah id batch.
2. Tiket urutan k = 2…N, berurutan: perintah yang sama dengan `--urutan <k>/<N> --batch <id>`.
3. `NEW FAIL` di tengah → perbaiki sebabnya dan ulangi **hanya** urutan itu; tiket yang sudah `PASS` tidak dialokasikan ulang. Slug kembar dengan ticketdir terbuka berarti tujuan itu duplikat yang lolos intake Phase 5: jangan alokasikan, sebut di ringkasan sebagai `Belum disentuh` beserta ticketdir lamanya.

## 6. Penelusuran Kode Awal Batch — `analyst:elicit`

1. Sesudah semua `new` `PASS`, tentukan tiket yang membutuhkan `analyst:code-explorer`: `TECH` selalu (`mode: BUKTI` kedalaman `menyeluruh`, klaim kondisi sekarang dari permintaannya); tipe lain hanya bila permintaannya menyebut layar, menu, laporan, status, atau data yang mungkin sudah ada (`mode: KONTEKS` kedalaman `ringkas`).
2. Hidrasi template dispatch explorer (Precondition 1 `analyst:elicit`) per tiket, lalu dispatch **semuanya dalam satu pesan** supaya berjalan paralel. Dispatch ini dihitung sebagai dispatch pertama tiket itu.
3. Balikan disimpan di percakapan berlabel slug tiketnya, dan dilarang ditulis ke disk.
4. Tiket ke-k boleh menjalankan elicit Phase 1 sebelum balikan explorer-nya tiba, tetapi Phase 2 menunggu balikan explorer tiket ke-k saja.
5. Balikan hilang dari percakapan (diringkas otomatis, atau sesi baru) → dispatch ulang satu kali, tidak dihitung plafon.

## 7. Satu Tiket dalam Batch

- Tiket berjalan penuh lewat `analyst:elicit` → `analyst:spec` seperti tiket tunggal. Plafon berlaku **per tiket**: 5 giliran tanya-jawab, 2 dispatch explorer, dan 3 pertanyaan per giliran.
- Satu `AskUserQuestion` hanya untuk satu tiket. Header tiap pertanyaannya `Tiket <k>/<N>`.
- Tanpa fakta lintas tiket: jawaban yang diberikan untuk tiket lain hanya boleh masuk tiket ini sebagai `Asumsi:`, yang wajib dikonfirmasi di elicit Phase 4 tiket ini.
- Tiket **selesai** bila salah satu sudah tersaji: baris penutup `analyst:spec` (`READY` beserta segmen nataflow-nya, *Tahan*, atau dibatalkan), atau blok `TERTAHAN` `analyst:elicit`/`analyst:spec`.

## 8. Lanjut ke Tiket Berikutnya

Sesudah tiket ke-k selesai: `python3 <ticket.py> state --batch <id>`, lalu tiket urutan k+1 → `analyst:elicit` dengan `{ ticketdir }` (Precondition 3, lanjutan). Tiket berikutnya yang sudah tidak terbuka (`READY`, `DIBATALKAN`) dilewati. Sesudah tiket urutan N, atau saat user meminta berhenti, sajikan ringkasan (bagian 10).

## 9. Lanjutan Lintas Sesi

`ticket.py state` menampilkan tiket satu batch berurutan dengan segmen `batch <id> <k>/<N>`. Intake Phase 1 merutekan tiket **terbuka berurutan terkecil** di batch itu, lalu batch berlanjut per bagian 8. Tiket yang tertahan di sesi sebelumnya ikut didahulukan: elicit Phase 0 (lanjutan) menanyakan apakah jawaban yang ditunggu sudah tersedia. Bila belum, tiket itu kembali `TERTAHAN` dan batch lanjut ke tiket berikutnya. Balikan explorer sesi lama tidak terbawa: dispatch ulang per bagian 6 butir 5 saat giliran tiket itu tiba.

## 10. Blok

Blok intake, sebelum alokasi. Baris bernilai `—` dihapus:

```markdown
### INTAKE — BATCH <N> tiket
1. <type>[/<category>] · <slug> — <tujuan>
2. <type>[/<category>] · <slug> — <tujuan>
- **Peminta**: <requester | per tiket: 1 <nama>, 2 <nama>, …>
- **Digabung**: <butir kembar yang dijadikan satu tiket> | —
- **Antrian tiket**: <tujuan ke-6 dst., bagian repo lain> | —
- **Di luar batch**: <butir bukan tiket baru beserta rutenya> | —
```

Ringkasan, sesudah tiket urutan N atau saat user berhenti. Kolom `Keadaan` dari `ticket.py state --batch <id>`; kolom `nataflow` dari baris penutup tiap tiket di sesi ini (`—` bila tidak ada):

```markdown
### BATCH <id> — <r> READY dari <N>
| # | Ticketdir | Keadaan | nataflow |
|---|---|---|---|
| 1 | <ticketdir> | READY | dibuat #<code> |
| 2 | <ticketdir> | ELISITASI — tertahan: menunggu <siapa> | — |
- **Belum disentuh**: <urutan yang tidak sempat diproses di sesi ini> | —
```
