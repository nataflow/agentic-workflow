# Gate Decisions & Lifecycle State Machine — `tech-lead`

Panduan pendamping gerbang: eskalasi lintas-lane, klasifikasi risiko backend, tata kelola pertanyaan klarifikasi, siklus hidup taskdir, dan resolusi branch pada plugin `backenddev`.

______________________________________________________________________

## 1. Dynamic Escalation & Lane Switching

Fakta baru yang memperluas cakupan kerja ditangani di dua tingkat berbeda, dan gerbang hanya memiliki tingkat kedua:

```
[ chain: BRIEF ]     ──► Endpoint / DTO / status baru      ──► analyst menaikkan chain ke PRD_BRIEF
[ chain: PRD_BRIEF ] ──► Aturan bisnis belum disepakati    ──► analyst menaikkan chain ke BRD_PRD_BRIEF
[ EXEC_BRIEF ]       ──► Implementor menemukan isu BREAKING ──► Kembalikan ke gerbang (tech-lead)
```

- **Eskalasi chain (milik `backenddev:analyst`)**: Kedua transisi teratas dijalankan di dalam fase planning tanpa keluar ke gerbang — pemicu, tabel transisi, dan prosedur penulisan ulang `TASK.md`-nya ada di `analyst/references/chain-rules.md` bagian 3. Gerbang tidak menetapkan chain, tidak menaikkannya, dan tidak mengamandemen `risk:` karenanya.
- **Eskalasi lintas fase (milik gerbang)**: Isu `BREAKING` yang ditemukan `architect` atau `code-implementor` saat brief dieksekusi kembali ke gerbang sebagai permintaan kerja baru pada taskdir yang sama, diklasifikasi ulang lewat Keputusan 2, lalu dirutekan ke lane `PLANNING`.

______________________________________________________________________

## 2. Interactive Alignment & Questioning Rules (Fase 2)

Protokol klarifikasi interaktif untuk mencegah salah rute dan salah asumsi kontrak:

- **Format Wajib**: Satu panggilan `AskUserQuestion`, **1–3 pertanyaan dalam satu giliran**. Jika butuh >3 pertanyaan, pilih 3 yang paling menentukan rute/kontrak, sisanya menyusul sesudah dijawab.
- **Ukuran Kelayakan Pertanyaan**: Jawaban wajib mengubah rute, batasan file scope, atau isi artefak berikutnya.

| Pertanyaan Sah                                                              | Nilai Keputusan yang Diubah                                         |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| "`OrderService.cancel` di modul `order`, atau `cancel` di modul `payment`?" | Menentukan objek kerja, batas package, dan file scope brief         |
| "Endpoint sudah ada dan mau diubah method/path-nya, atau buat baru?"        | Membedakan risk `MINOR` dari `MAJOR` / `BREAKING` pada Keputusan 2   |
| "Status `RETURNED` adalah transisi lifecycle baru, atau reuse `CANCELLED`?" | Menentukan risk level dan migration kolom enum database             |
| "Perbaiki seluruh pemanggil di modul lain, atau batasi di modul ini saja?"  | Menentukan cakupan blast radius dan pembagian unit brief            |

### Empat Larangan Keras Pertanyaan:

1. Menanyakan fakta yang sudah dapat dibuktikan dari membaca kode di Fase 1.
2. Menanyakan izin klise untuk melanjutkan ("Boleh saya mulai?"). Approval hanya ada di BRD dan PRD.
3. Menanyakan hal yang jawabannya tidak mengubah rute atau kontrak (preferensi formatting/gaya).
4. Melakukan pertanyaan lanjutan berkali-kali (Fase 2 berjalan tepat satu kali di gerbang).

### Penanganan User Menghindar / Ambigu:

- Setiap opsi dalam `AskUserQuestion` wajib menyertakan trade-off dan konsekuensi teknis (blast radius).
- Jika user menjawab tidak pasti ("terserah", "pilih yang terbaik", atau melewati pertanyaan): naikkan 1 level risiko, pilih opsi dengan blast radius terkecil / paling terisolasi, dan nyatakan secara eksplisit sebagai keputusan gerbang sebelum melangkah.

______________________________________________________________________

## 3. Concrete Backend Risk Catalog (Decision 2)

Klasifikasi risiko berbasis kriteria teknis deterministik (satu terpenuhi cukup; jika ragu → naik 1 level):

### `BREAKING` — Mengubah Kontrak Eksternal

- **REST API**: Mengubah HTTP method, URL path, response status code; menghapus/mengubah tipe field DTO request/response; menambah field request wajib (penanda wajib pada validasi request).
- **Domain & Status**: Menambah, menghapus, atau mengubah urutan transisi status enum entity yang terekspos.
- **Database Schema**: Migration destruktif (drop table/column, rename column/table, alter data type, constraint `NOT NULL` tanpa default value).
- **Security & Authorization**: Mengubah role, authority, atau ekspresi otorisasi pada deklarasi keamanan endpoint maupun konfigurasi keamanan terpusat.
- **Asynchronous & Messaging**: Mengubah routing key, exchange, destination topic, atau format payload JSON Kafka/RabbitMQ yang sudah memiliki consumer aktif.

### `MAJOR` — Perilaku Berubah, Kontrak Eksternal Tetap

- **Business Logic & Validation**: Aturan validasi lintas-field berubah, urutan validasi berubah, batas atau propagasi transaksi bergeser.
- **API Extension**: Menambah endpoint baru yang aditif, menambah field response/request baru yang bersifat opsional (`required = false`).
- **Database Schema**: Migration aditif (tambah tabel baru, tambah kolom nullable baru, tambah index non-unique).
- **Error Response**: Format error payload internal berubah yang diparsing oleh consumer.

### `MINOR` — Perubahan Internal Terisolasi

- **Refactoring**: Rename variable/method internal, ekstraksi tipe/helper privat, optimasi query internal tanpa ubah output.
- **Maintenance**: Penambahan unit/integration test, dependency patch bump, perbaikan log message internal, bugfix lokal yang mengembalikan perilaku sesuai kontrak spek eksisting.

______________________________________________________________________

## 4. Work Directory & Session Recovery State Machine (Fase 3)

Struktur penyimpanan artefak di bawah `backenddev/`:

```
backenddev/
  docs/
    2608201430-order-split/       satu pekerjaan satu direktori
      TASK.md                     task — akar rantai, memuat ledger ## Chain
      BRD.md                      business-analysis — maksimum satu
      PRD.md                      system-analysis   — maksimum satu
      brief-01-entity.md          plan
      brief-02-endpoint.md
      REVIEW.md                   code-reviewer, sekali sesudah rantai selesai
    2608211015-stock-lock-bugfix/
      TASK.md                     chain: BRIEF
      brief-01-lock.md            direktori tanpa BRD/PRD — bentuk sah chain BRIEF
  issues/
    2026-08-20-001-issues.md      datar, tidak ikut per pekerjaan
    README.md                     indeks audit repo
```

```
+-----------------------------------------------------------------------------------+
|                            Taskdir Recovery State Machine                         |
+-----------------------------------------------------------------------------------+
| 1. Brief BLOCKED Ditemukan ──► analyst re-entry (reentry_reason) → pengganti plan |
| 2. Brief READY Belum Jalan ──► Rutekan langsung ke backenddev:architect            |
| 3. Artefak DRAFT Ditemukan ──► Rutekan ke backenddev:analyst (gerbang dokumennya)  |
| 4. Semua Brief DONE + REPORT.md / Baru ──► Buat taskdir baru untuk request baru   |
| 5. REVIEW.md P1 ──► Taskdir sama, lane PLANNING + reentry_reason (bukan baru)     |
+-----------------------------------------------------------------------------------+
```

### Aturan Penetapan Identitas Taskdir:

- **Format Slug**: `<domain>-<jenis-kerja>` (kebab-case, misal: `order-split`, `stock-lock- bugfix`).
- **Format Taskdir**: `backenddev/docs/<YYMMDDhhmm>-<slug>/` dengan timestamp dari `date +%y%m%d%H%M`.
- **Evaluasi `ls backenddev/docs/`**:
  - Pekerjaan yang sama & belum selesai → gunakan kembali taskdir tersebut.
  - Pekerjaan lanjutan sesudah seluruh brief `DONE`/`SUPERSEDED` **dan** `REPORT.md` terbit → buat taskdir baru dengan timestamp baru. `REVIEW.md` ber-`P1` bukan rantai selesai: perbaikannya tetap di taskdir itu.
  - Domain sama tetapi pekerjaan berbeda → buat taskdir baru (`order-split` vs `order-split- export`).
- **Penomoran Brief**: `brief-<NN>-<unit>.md` (`NN` dua digit urutan eksekusi 01, 02, dst.). Nomor brief tidak pernah dipakai ulang dalam satu taskdir.

______________________________________________________________________

## 5. Git Branch Lifecycle & Re-entry Protocol

Setiap direktori pekerjaan memuat tepat satu branch kerja:

- **Format Nama Branch**: Diturunkan dari slug yang dipasang ke `branch_convention` profile (misal: `feat/<slug>` atau `fix/<slug>`).
- **Validasi Prasyarat Branch**:
  - `git status --porcelain` ada output di luar segmen `.explore/` → **BERHENTI SEGERA** dan laporkan uncommitted changes ke user. Berkas di bawah `.explore/` adalah laporan `code-explorer` dan tidak dihitung.
  - `base_branch` atau `branch_convention` tidak ada di profile → **BERHENTI SEGERA** dan minta user jalankan refresh profile.

Branch kerja **selalu** bercabang dari `base_branch` profile; dilarang mencabangkannya dari branch kerja lain.

| Kondisi Posisi `HEAD`                       | Tindakan Gerbang                                                                     |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `HEAD` berada di `base_branch`              | Buat branch baru: `git checkout -b <branch_name>`                                    |
| Branch dengan nama tersebut sudah ada       | `git checkout <branch_name>` — re-entry session, taskdir lama dipakai ulang          |
| `HEAD` di branch kerja lain                 | `git checkout <base_branch>` lebih dulu, baru `git checkout -b <branch_name>`        |
| `HEAD` detached / non-git workspace         | **BERHENTI SEGERA**                                                                  |

**Larangan Operasi Remote/Destruktif**: Plugin dilarang menjalankan `git push`, `git merge`, `git rebase`, `gh pr create`, `git branch -d`, atau checkout ke branch lain di luar persetujuan eksplisit user.

______________________________________________________________________

