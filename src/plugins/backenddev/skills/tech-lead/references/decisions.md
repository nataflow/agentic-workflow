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
| 1. Brief BLOCKED / HALT.md ──► analyst re-entry (reentry_reason) → pengganti plan |
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

## 6. Keputusan 1 — Tabel Lane, Presedensi, dan Batas Lane `PLANNING`

Pilih satu dari tujuh jalur kanonik berdasar fakta kode terverifikasi:

| Jalur (Lane) | Kondisi Masuk | Rute Awal | Artefak |
|---|---|---|---|
| **PROFILE** | Profil tidak ada, 1 field/dokumen wajibnya hilang, `index.json` tidak sah, atau profil masih di lokasi lama `.claude/profile/` (MIGRATE) | `profile` | `.claude/profile/backenddev/` |
| **EXPLORE_FACT** | Pertanyaan faktual letak simbol/alur, tanpa mutasi | Selesai di Fase 1 | Jawaban di chat |
| **PLANNING** | Permintaan mengubah perilaku sistem dan brief `READY`-nya belum terbit | `analyst` | `TASK.md` → `BRD.md`/`PRD.md` → `brief-<NN>-<unit>.md` |
| **DEFECT_RCA** | Ada error/stacktrace/test merah, penyebab belum terbukti | `debug` | `RCA.md` |
| **EXEC_BRIEF** | Eksekusi brief `READY` di taskdir eksisting | `architect` | `REVIEW.md` |
| **AUDIT_SWEEP** | Audit kode terhadap 6 dimensi tanpa brief | `audit` | `backenddev/issues/<file>.md` |
| **API_DOCS** | Dokumentasi API diminta, endpoint sudah ada di kode | `document-api` | `docs/api/<slug>.md` |

**Presedensi Lane**: Pilih prioritas menurun jika lebih dari satu kondisi masuk terpenuhi: `PROFILE` → `EXEC_BRIEF` → `AUDIT_SWEEP` → `DEFECT_RCA` → `PLANNING` → `API_DOCS` → `EXPLORE_FACT`. Sebutkan lane yang dikalahkan beserta alasannya di slot `Justifikasi Rute`.

Lane `PLANNING` menampung seluruh kerja perancangan tanpa memilah artefaknya di sini: panjang rantai (`TASK` saja, plus `PRD`, atau plus `BRD`) adalah keputusan `backenddev:analyst` di Fase 1-nya, diturunkan dari `risk` Keputusan 2 dan kepastian kontrak yang terbukti di bukti Fase 1 gerbang. Dilarang menetapkan chain di gerbang atau memanggil `business-analysis`, `system-analysis`, `task`, maupun `plan` secara langsung pada lane ini. Gerbang memanggil `task` sendiri hanya pada lane `DEFECT_RCA` dan backfill `EXEC_BRIEF` (`SKILL.md` Fase 3 butir 1).

Perbaikan temuan terpilih dari `backenddev/issues/` dan `{taskdir}/REVIEW.md` masuk lewat lane ini juga, bukan lewat rute tersendiri: gerbang menyerahkan temuannya sebagai `request` beserta `evidence`, dan `finding_source` menandai berkas asalnya.

Dilarang mengarang lane baru; turun ke `EXPLORE_FACT` untuk kumpulkan bukti lalu evaluasi ulang tabel.

## 7. Keputusan 2 — Level Risiko, `strict_mode`, dan Batas Wewenang

Klasifikasikan permintaan yang mengubah kode (lane `PROFILE` dan `EXPLORE_FACT` tanpa risk level; katalog di bagian 3):

| Level | Pemicu ringkas |
|---|---|
| **`BREAKING`** | Kontrak eksternal berubah: endpoint/DTO eksisting, field wajib baru, transisi status terekspos, event ber-consumer, migrasi destruktif, auth |
| **`MAJOR`** | Validasi bisnis, batas transaksi, query kompleks, field opsional baru |
| **`MINOR`** | Rename lokal, refactor private, tambah test, log tracing, bugfix lokal |

1. **Prinsip Eskalasi**: Pilih level lebih tinggi jika ragu di antara dua klasifikasi.
2. **`strict_mode`**: Naikkan klasifikasi dasar 1 tingkat (`MINOR`→`MAJOR`, `MAJOR`→`BREAKING`, `BREAKING` tetap) jika bernilai `true`, jalankan rute Keputusan 1 dengan level hasilnya, dan laporkan kenaikan secara eksplisit.
3. **Batas Wewenang**: Serahkan `risk` hasil klasifikasi ini ke `backenddev:analyst` sebagai parameter. Panjang rantai perancangan dan eskalasi dinamisnya (DTO atau kolom DB baru yang muncul di tengah pengerjaan) adalah wewenang `analyst`; gerbang tidak memutuskannya dan tidak mengamandemen `TASK.md` karenanya.
4. **Satu rute langsung ke `plan`**: `plan` dipanggil gerbang hanya pada satu jalur di luar lane `PLANNING` — `RCA.md` bervonis `ROOT_CAUSE_CONFIRMED` dari `debug`. Slot `First Action` blok Output `SKILL.md` **wajib menyebut `entry_mode: RCA` eksplisit**; parameter itu tidak punya nilai bawaan dan tidak pernah disimpulkan `plan` dari artefak yang ada di taskdir, sehingga gerbang yang lupa menyebutnya membuat `plan` berhenti di check 3 prasyaratnya. Taskdir wajib sudah berakar `TASK.md` sebelum `plan` berangkat, dan jalur ini memakainya sejak provisioning `DEFECT_RCA`.
5. **Temuan bukan rute langsung**: temuan terpilih dari `backenddev/issues/` maupun `{taskdir}/REVIEW.md` dirutekan ke lane `PLANNING`, dan panjang rantainya diputuskan `backenddev:analyst` dari dua sumbu — bukan ditetapkan gerbang. Temuan yang menyentuh kontrak API, transisi status, aturan validasi, atau permission menerbitkan `PRD.md` lewat sumbu kontrak (`analyst/references/chain-rules.md` bagian 1.2 butir 1 dan 2; `risk: BREAKING` menuntutnya tanpa syarat lain), dan temuan yang membuka aturan bisnis belum disepakati menambah `BRD.md` lewat sumbu bisnis. Gerbang meneruskan `risk` hasil Keputusan 2 ini apa adanya dan berhenti di situ.
