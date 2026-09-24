# Brief Template & Authoring Rules — The Single Execution Contract

Brief adalah **satu-satunya** artefak kontrak eksekusi yang dibaca oleh subagent `code-implementor`. Dokumen ini disusun oleh skill `backenddev:plan` melalui ketiga jalur masuk (`PRD`, `RCA`, `LANGSUNG`).

Path: `backenddev/docs/<YYMMDDhhmm>-<slug>/brief-<NN>-<unit>.md` Format Penamaan: `NN` dua digit urutan eksekusi (`01`, `02`, ...), `<unit>` nama unit pekerjaan kebab-case (`entity-stock`, `order-service`, `lock-endpoint`).

> **THE IRON LAW.** Apa pun yang tidak tertulis di brief tidak akan pernah diketahui eksekutornya. Eksekutor tidak membaca PRD, tidak membaca laporan audit, dan tidak mengimprovisasi kode di luar brief.

______________________________________________________________________

> **Kerangka ditulis skrip, bukan disalin tangan.** Blok bagian 1 di bawah adalah **contoh terisi domain nyata** — ia memperlihatkan bentuk tiap seksi, bukan teks yang disalin ke brief. Kerangka sesungguhnya dituliskan `../scripts/scaffold_brief.py --nn <NN>` dari matriks alokasi Fase 3 langkah 1: sepuluh seksi berurutan, frontmatter terisi, dan baris `Covers:` — plus `Fulfills:` pada rantai tanpa PRD — yang disalin dari matriks. Tiap seksi kosongnya membawa penanda `<!-- scaffold: ... -->` berisi predikat yang akan ditagih Fase 4; hapus penanda itu saat seksinya diisi. Penanda yang masih tersisa saat validasi berarti seksi itu belum digarap, dan `../scripts/validate_briefs.py` menolaknya lewat Check S.

## 1. Template Kanonik Brief

````markdown
---
title: <ringkas tujuan pekerjaan>
source: <path artefak asal + tanggal, atau kutipan permintaan user>
risk: BREAKING | MAJOR | MINOR
status: READY
commit_message: "feat(order): implement order lock service"
---

# Brief: <title> — <yyyy-mm-dd>

## Objective
<2-3 kalimat: apa yang dikerjakan dan alasan bisnis/teknisnya, dengan bukti file:line kondisi saat ini. Jika bergantung pada brief pendahulu, sebutkan secara eksplisit: "Mengandaikan brief-01 sudah DONE". Asumsi aktif hulu yang membentuk langkah brief ini ditulis di sini sebagai kalimat berawalan "Berlaku asumsi:" — bukan di `## Analysis trace`, yang eksekutornya diberitahu bukan pekerjaannya.>

Covers: AC-1, AC-3
<!-- baris `Fulfills: SC-2` hanya pada rantai TANPA PRD; lihat bagian 2 butir 7 -->

## Interfaces

- Consumes: `VoucherCreateRequest.SelectAllStores` dari `brief-02` — `bool`, default `false`
- Consumes: `StockReadySummary` dari `brief-01` — `struct{Ready int; CheckedAt time.Time}`
- Produces: `VoucherArea{Voucher, StoreGroup}`; `VoucherAreaRepo.FindAllByVoucherID(ctx, string) -> []VoucherArea`; `DeleteAllByVoucherID(ctx, string) -> error`

## File scope

**Folder**

| Path folder | Kenapa tersentuh |
|---|---|
| `internal/order/` | service dan handler utama |
| `db/migrations/` | satu migrasi baru |

**File**

| Aksi | Path | Anchor | Apa yang berubah |
|---|---|---|---|
| modify | `internal/order/service.go` | `Submit(ctx, OrderRequest)` | pasang lock sebelum baca stok (~`:84`) |
| create | `internal/order/dto_stock.go` | — | tipe respons baru |
| create | `db/migrations/0037_add_stock_idx.up.sql` | — | index penunjang |
| modify | `internal/order/service_test.go` | `TestSubmitGagalSaatStokHabis` | AC-3: assert submit ditolak saat stok habis |

## Out of scope
<Daftar modul, file, atau alur yang sengaja TIDAK disentuh beserta alasan teknisnya>

## Steps
<Langkah murni perubahan kode. DILARANG menyisipkan perintah build/test di seksi mana pun — brief tidak memuat gerbang verifikasi; kompilasi dan test ditunda ke penutup taskdir.>

1. Buat tipe respons `StockView` di `internal/order/dto_stock.go`:

   ```go
   type StockView struct {
       SKU       string    `json:"sku"`
       Available int       `json:"available"`
       CheckedAt time.Time `json:"checked_at"`
   }
   ```
2. Pasang lock sebelum baca stok — sisipkan tepat sesudah baris
   `order, err := repo.FindByID(ctx, id)` di dalam `Submit(ctx, OrderRequest)`
   pada `internal/order/service.go` (~`:84`):

   ```go
   if err := s.stockRepo.LockBySKU(ctx, req.SKU); err != nil {
       return err
   }
   ```
3. <Langkah perubahan nilai terhitung jika ada>:
   — sebelum: `2026-08-20T07:00`, sesudah: `2026-08-20T14:00`

## Migration
<`V{n}__nama.sql` yang ditulis dan isi DDL-nya, atau tulis "tidak perlu" beserta alasan jika tidak mengubah schema/entity>

## Mirrored paths
<Consumer queue, scheduler, websocket, changelog yang harus ikut konsisten dengan bukti file:line, atau tulis "tidak ada">

## Risk & rollback
<Potensi dampak regresi, cara deteksi kegagalan, strategi rollback, dan stop condition khusus brief ini. Langkah verifikasi tiap `AC-{n}` bertanda `QA manual:` yang diklaim brief ini mendarat di sini sebagai kalimat operasional bernomor AC — bukan di `## Analysis trace`.>

## Work status

| Item | Status | Catatan |
|---|---|---|
| P1-1 | PLANNED | — |

## Analysis trace
<BUKAN pekerjaan eksekutor. Jejak temuan yang gugur (OBSOLETE/DROPPED), pola modul tetangga untuk audit berikutnya, atau asumsi. Tulis "Tidak ada." bila kosong>
````

______________________________________________________________________

## 2. Authoring & Validation Rules

1. **Pesan Commit (`commit_message`)**: Ditulis `backenddev:plan` dari `commit_convention` profil, berbentuk `<type>(<domain>): implement <unit>`. Eksekutor memakainya apa adanya; varian gagal diturunkan darinya menjadi `wip(<domain>): brief-<NN>-<unit> [BLOCKED]`.

2. **Status Siklus Hidup Brief (Frontmatter)**:

   - `READY`: Ditulis oleh `backenddev:plan`. Seluruh brief lahir siap eksekusi tanpa fase draft (`status: READY`).
   - `DONE`: Ditulis `code-implementor` sesudah seluruh langkah `## Steps` tuntas, tepat sebelum ia meng-commit brief itu bersama perubahan `src/**`-nya.
   - `BLOCKED`: Ditulis `code-implementor` jika ia terhenti oleh *stop condition*. *(Dilarang memakai status `DRAFT` atau `APPROVED` pada brief; approval berhenti di BRD dan PRD).*

3. **4 Nilai Status Item Kerja (`## Work status`)**:

   - `PLANNED`: Masuk rencana aktif eksekusi.
   - `FIXED`: Selesai dikerjakan oleh implementor.
   - `DROPPED`: Dibatalkan karena dependensi/asumsi tidak terpenuhi (tercatat di `## Analysis trace`).
   - `OBSOLETE`: Tidak relevan akibat perubahan kode sebelumnya (tercatat di `## Analysis trace`).

   *(`DEFERRED` bukan nilai item brief — ia status **temuan** di `backenddev/issues/`. Penundaan brief menghentikan rantai, bukan melompatinya.)*

4. **5 Bentuk Placeholder Terlarang (Zero-Tolerance Red Flags)**:

   - `TODO`
   - `TBD`
   - `diisi nanti`
   - `tambahkan error handling seperlunya`
   - `tulis test untuk yang di atas`

   Ini **rumah kanonik** daftar tersebut. Skill `plan` serta subagent `code-implementor` dan `brief-reviewer` merujuk ke sini berikut berkas pendukungnya; dilarang menulis ulang daftarnya dengan kata lain.

5. **Kaidah Penulisan Langkah (`## Steps`)**:

   - Setiap langkah kode wajib berupa snippet lengkap dan valid (bukan potongan elipsis `...`).
   - Setiap langkah wajib membawa **titik sisip/anchor konkret** (nama class, method, atau field beserta posisi relatifnya).
   - Langkah yang mengubah nilai wajib mendokumentasikan nilai `sebelum:` dan `sesudah:`.
   - **Nol verifikasi di dalam brief**: dilarang menempel baris `— verifikasi:` atau perintah perintah build/test di seksi mana pun, dan dilarang menghidupkan kembali seksi `## Verification`. Eksekutor brief menulis kode tanpa menjalankan build/test; kompilasi dan test suite dijalankan sekali di penutup taskdir sesudah brief terakhir mendarat. Ini **rumah kanonik** aturan tersebut.

6. **Baris `Covers:` — Pendaratan Acceptance Criteria**:

   - Baris `Covers:` berdiri tepat di bawah paragraf `## Objective`, berformat `Covers: AC-1, AC-3` — nomor `AC-{n}` disalin apa adanya dari `## Acceptance criteria` PRD, dipisah koma. Ini **rumah kanonik** aturan tersebut; `plan` dan `brief-reviewer` membacanya mekanis, bukan menafsirkan isi `## Steps`.
   - Gabungan baris `Covers:` seluruh brief satu taskdir wajib menutup **setiap** `AC-{n}` PRD. AC yang tak terpetakan berarti fiturnya ter-implement separuh tanpa terdeteksi gerbang.
   - Dilarang menyebut `AC-{n}` yang tidak ada di PRD, dan dilarang menghilangkan barisnya. Brief yang sah tidak memikul AC (mis. jalur `LANGSUNG` atau `RCA` tanpa PRD) menulis `Covers: — (<alasan>)`.
   - **AC bertanda `test otomatis` wajib punya pemikul test yang tertulis.** Minimal satu baris berkas test di `## File scope` brief pengklaim menyebut `AC-{n}` itu — di kolom `Anchor` atau di kolom "Apa yang berubah", seperti contoh bagian 1. Menuntut sekadar "ada berkas test di brief pengklaim" tidak cukup: beberapa brief dapat menyentuh berkas test yang sama karena alasan yang berbeda-beda, dan bertiga lolos mengklaim satu AC yang tidak satu pun di antaranya benar-benar menguji. Penamaan membuat pemikul assertion-nya tertulis, bukan tersirat. `plan` menagihnya lewat Check I di `../references/review-and-commit.md` bagian 4.
   - AC yang kolom "Cara verifikasi"-nya bernilai `QA manual:` diklaim di `Covers:` persis seperti AC lain, dan **langkah manualnya turun ke `## Risk & rollback`** brief pengklaim sebagai kalimat operasional yang menyebut nomor AC-nya. Ia dilarang mendarat di `## Analysis trace`: seksi itu dinyatakan bukan pekerjaan eksekutor, sehingga satu-satunya bentuk verifikasi AC tersebut jadi tak terlihat justru di titik ia harus dijalankan. `plan` menagihnya lewat Check I di `../references/review-and-commit.md` bagian 4.
   - Baris ini bukan seksi baru: sepuluh seksi wajib brief tidak bertambah karenanya.
   - `Covers:` mengangkut **hanya** `AC-{n}`. Token sumbu lain dilarang menumpang di baris ini; keterlacakan ke akar `TASK.md` punya barisnya sendiri di butir 7.

7. **Baris `Fulfills:` — Pendaratan Success Criteria Akar, hanya pada rantai tanpa PRD**:

   - **Rantai ber-PRD tidak menulis baris ini sama sekali.** Keterlacakan `SC-{n}` sudah diangkut kolom `Akar` tabel `## Acceptance criteria` PRD, dan rantainya tergerbangi di tiap sambungan: `SC-{n}` → `Akar` (predikat G2 `analyst`), lalu `AC-{n}` → `Covers:` (Check H dan predikat G). Baris `Fulfills:` di atasnya memvonis ulang kesimpulan yang sama dari ujung yang berbeda, dan `SC-{n}` pada rantai itu memang parafrase `AC-{n}`-nya. `scaffold_brief.py` tidak menuliskannya, dan Check S menolak brief yang memuatnya.
   - **Rantai tanpa PRD** — `chain: BRIEF` dan jalur `RCA` — memakainya sebagai satu-satunya rute ke akar, dan gerbangnya berlaku penuh: baris `Fulfills:` berdiri tepat di bawah baris `Covers:`, berformat `Fulfills: SC-2, SC-4`, nomor `SC-{n}` disalin apa adanya dari `## Success Criteria` `TASK.md`, dipisah koma. Ini **rumah kanonik** aturan tersebut; `plan` (Check G) dan `brief-reviewer` membacanya mekanis.
   - Gabungan baris `Fulfills:` seluruh brief satu taskdir wajib menutup **setiap** `SC-{n}` `TASK.md`. `SC-{n}` tanpa brief pengklaim berarti kriteria akar dikerjakan separuh tanpa terdeteksi gerbang.
   - Dilarang menyebut `SC-{n}` yang tidak ada di `TASK.md`, dan dilarang menghilangkan barisnya. Brief pada taskdir tanpa `TASK.md` menulis `Fulfills: — (akar absen)`.
   - **Nomor, bukan prosa.** Prosa butir Success Criteria dilarang disalin ke brief seksi mana pun — butir itu memuat literal `— verifikasi:` yang ditolak Check F dan butir 5 di atas. Baris `Fulfills:` ada justru supaya penyalinan itu tidak pernah diperlukan.
   - Baris ini bukan seksi baru: sepuluh seksi wajib brief tidak bertambah karenanya.

8. **Satu baris `Consumes` = satu brief sumber (`## Interfaces`)**: brief yang mengonsumsi dari dua pendahulu menulis **dua baris `Consumes`**, masing-masing menyebut satu `brief-NN`, seperti contoh bagian 1. Ini **rumah kanonik** aturan tersebut; `plan` menagihnya lewat Check C.

   Alasannya bukan kerapian. Satu baris yang menyebut dua sumber membuat pasangan simbol-ke-sumbernya tidak dapat dipetakan, dan pemeriksaan mana pun terpaksa menyandingkan simbol pertama baris itu dengan **tiap** brief yang disebut — lalu melaporkan kegagalan hantu atas simbol yang memang milik brief yang lain. Baris `Produces` tidak memikul aturan ini: ia tidak menunjuk sumber, sehingga banyak signature sah berdiri di satu baris dipisah titik koma.

9. **Integritas Batas Cakupan (`## File scope` & `## Out of scope`)**:

   - Baris `modify` wajib menyertakan simbol `Anchor` (nama method, field, class), dan simbol itu wajib **disebut minimal satu langkah `## Steps`**. Anchor yang tak pernah dipakai langkah mana pun berarti brief menamai satu titik sisip lalu mengerjakan titik lain; `plan` menagihnya lewat Check N.
   - Seluruh file yang disentuh wajib terdaftar. Implementor dilarang menyentuh file di luar tabel ini, **maupun simbol di luar kolom `Anchor` baris berkas itu**. Simbol tambahan yang ternyata harus ikut berubah dilaporkan implementor, bukan disunting diam-diam; `architect` membandingkan hunk header commit terhadap kolom ini.
   - Tidak ada seksi yang dibiarkan kosong tanpa penjelasan; jika nihil, tulis "tidak ada" beserta alasannya.

10. **Pendaratan Migrasi (`## Migration` & `## Risk & rollback`)**: berlaku pada dua pemicu — `## Migration requirements` PRD yang bukan "tidak perlu" (jalur `PRD`), **dan** berkas migrasi baru yang ditetapkan scan Fase 2 butir 5 pada jalur tanpa PRD. Pemicu kedua ada karena urutan deploy dan rollback plan tidak pernah divonis hulu di jalur itu; tanpa aturan ini keduanya jatuh ke orang yang menjalankan deploy.

   - Isi DDL — nama berkas migrasi beserta pernyataan `CREATE`/`ALTER`-nya — ditulis utuh di `## Migration`, bukan dirujuk sebagai "sesuai PRD".
   - **Skema dibentuk ORM tanpa berkas migrasi**: repo yang profilnya (`.claude/profile/invariants.md` atau `commands.md`) menyatakan skema dibentuk ORM saat startup — mis. Hibernate `ddl-auto`, `hbm2ddl`, TypeORM `synchronize: true`, GORM `AutoMigrate` — dan yang PRD-nya memutuskan tanpa berkas migrasi, menulis baris `Berkas migrasi: tidak ada — skema dibentuk ORM (<setelan>)` di `## Migration`. Baris itu hanya membebaskan kewajiban berkas migrasi di `## File scope`; DDL setara yang dibangkitkan ORM, urutan deploy bernomor, dan rollback plan tetap wajib. Token yang tidak ditopang pernyataan profil adalah cacat.
   - **Urutan deploy** yang dikunci PRD (mis. pola Expand-Contract: kolom baru nullable → backfill → pembacaan pindah → kolom lama dibuang) turun jadi langkah bernomor di `## Migration`, satu fase satu langkah, dengan penanda tegas fase mana yang dieksekusi brief ini dan fase mana yang milik brief berikutnya.
   - **Rollback plan** migrasi — cara mengembalikan skema bila migrasi gagal di tengah deployment beserta tanda kegagalannya — turun ke `## Risk & rollback` sebagai kalimat operasional, bukan frasa kosong "rollback migrasi bila gagal".
   - Brief ber-`## Migration` terisi yang `## Risk & rollback`-nya tidak menyebut pengembalian skema adalah cacat, begitu pula sebaliknya. Ini **rumah kanonik** aturan tersebut; `plan` menagihnya lewat Check J di `../references/review-and-commit.md` bagian 4.
   - **Urutan deploy pada jalur tanpa PRD** diturunkan `plan` sendiri dari sifat migrasinya: migrasi tidak backward-compatible mengikuti pola Expand-Contract menurut `## Failure signatures` adapter stack, satu fase satu langkah bernomor. Rollback plan-nya tetap wajib.
   - PRD menulis "tidak perlu" pada `## Migration requirements`, atau batch tanpa PRD nol berkas migrasi → tiap brief tetap menulis "tidak perlu" beserta alasannya di `## Migration`, dan Check J dilewati.

11. **Derivasi `risk:` (Frontmatter)**: Nilainya **dinilai per unit kerja** atas isi `## File scope` dan `## Steps` brief itu sendiri, bukan disalin dari dokumen hulu. Ini **rumah kanonik** aturan tersebut; `plan` menagihnya lewat Check K di `../references/review-and-commit.md` bagian 4.

    > **Salinan tersinkron.** Tabel predikat di bawah disalin verbatim ke `agents/brief-reviewer.md` fokus #3, karena subagent itu tidak dapat membaca berkas plugin ini. Menyunting salah satu tanpa yang lain membuat `plan` dan reviewernya memvonis `risk:` dengan aturan berbeda. Sunting keduanya dalam satu perubahan.

    | Nilai | Predikat — brief menyentuh salah satu |
    |---|---|
    | `BREAKING` | mengubah tipe, nama, atau kewajiban field yang sudah dipakai consumer; menghapus atau mengubah path/method endpoint terbit; mengubah atau membuang transisi status yang terekspos keluar; migrasi destruktif (`DROP`, `NOT NULL` tanpa default, penyempitan tipe) |
    | `MAJOR` | penambahan aditif yang mengubah kontrak keluar tanpa membatalkan yang lama: endpoint baru, field opsional baru, nilai enum baru, tabel atau kolom nullable baru |
    | `MINOR` | perubahan internal tanpa kontrak keluar: refactor, perbaikan logika, penyesuaian test, konfigurasi, index penunjang |

    - **Plafon akar**: nilai brief dilarang melampaui `risk:` frontmatter `{taskdir}/TASK.md`. Brief yang predikatnya menuntut nilai lebih tinggi adalah **pemicu eskalasi** — hentikan penulisan batch dan kembalikan klasifikasinya ke gerbang, sama seperti 5 pemicu `../references/entry-rules.md` bagian 1A. Dilarang melunakkan predikat agar muat di bawah plafon, dan dilarang menaikkan risk sendiri.
    - `TASK.md` absen → plafonnya diambil dari parameter `risk` yang diteruskan pemanggil. `risk:` `TASK.md` bernilai `-` (lane non-mutasi kode) → plafon brief adalah `MINOR`.
    - Nilai `-` bukan nilai sah bagi brief: brief selalu memikul salah satu dari tiga enum. Satu batch boleh memuat brief bernilai campur — itu justru bentuk normalnya, karena tiap brief menyentuh permukaan yang berbeda.

12. **Kecukupan Unit (`## Steps` & `## File scope`)**: tiap langkah dan tiap berkas brief berakar pada `AC-{n}` baris `Covers:` atau `SC-{n}` baris `Fulfills:` brief itu sendiri. Langkah yang tak menggerakkan satu pun di antaranya dihapus, bukan dibenarkan belakangan dengan menambah nomor ke baris `Covers:` — arah itu terbalik, dan matriks Fase 3 sudah mengunci alokasinya lebih dulu. Butir 6 dan 7 menagih arah maju (tiap `AC-{n}` punya brief); butir ini arah baliknya (tiap langkah punya `AC-{n}`), dan keduanya dibutuhkan karena batch yang menutup seluruh AC tetap boleh memuat kerja yang tak satu pun AC minta.

    - **Abstraksi berkonsumen tunggal dilarang**: interface, factory, strategy, atau lapisan adapter berimplementasi tunggal dan berpemanggil tunggal di seluruh batch ditulis sebagai pemanggilan langsung, kecuali `## Anti-patterns` atau `## Code conventions` profil menuntut sebaliknya. "Nanti ada implementasi kedua" bukan akar.
    - **Flag konfigurasi, kolom, dan index antisipatif dilarang**: yang tidak dibaca satu pun langkah batch ini tidak ditulis. Kolom dan index yang memang dituntut `## Migration requirements` PRD dikecualikan — akarnya ada, dan letaknya di sana.
    - **Temuan bukan langkah**: perbaikan yang ditemukan saat memetakan kode dan tidak dituntut akar mana pun dicatat sebagai temuan di `backenddev/issues/`, bukan diselipkan ke `## Steps` brief terdekat — selipan itu melewati satu-satunya gerbang yang pernah menilai perlu-tidaknya ia dikerjakan.
