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
commit_scope: order
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

1. **Pesan Commit (`commit_message`, `commit_scope`)**: diturunkan dari `commit_template` profil lewat `scripts/scaffold_brief.py` (`skills/_common/commit_lib.py`; template absen → `<type>(<scope>): implement <unit>`), dan dicocokkan Check S dengan regex dari template yang sama. `type` default `fix` pada lane `DEFECT_RCA` atau akar ber-`finding_source`, selain itu `feat`. `commit_scope` menyimpan `<scope>` apa adanya, juga saat template tanpa `{scope}`. Eksekutor memakai `commit_message` apa adanya; varian gagal menjadi `wip(<commit_scope>): brief-<NN>-<unit> [BLOCKED]`.

2. **Status Siklus Hidup Brief (Frontmatter)** — empat nilai, tiap transisi punya satu penulis:

   - `READY`: Ditulis `backenddev:plan` lewat `scaffold_brief.py --nn`. Seluruh brief lahir siap eksekusi tanpa fase draft.
   - `DONE`: Ditulis `code-implementor` sesudah seluruh `## Steps` tuntas, tepat sebelum ia meng-commit brief bersama perubahan `src/**`-nya. Koreksi `READY → DONE` oleh `architect` sah hanya pada baris "commit ada, status tertinggal" matriks bukti disk (`architect/references/lifecycle-recovery.md` bagian 3), dengan commit `chore(<slug>): koreksi status brief-NN ke DONE (<sha7>)`.
   - `BLOCKED`: Ditulis `code-implementor` saat terhenti oleh *stop condition*. Brief `BLOCKED` menahan rantai sampai digantikan.
   - `SUPERSEDED`: Ditulis **hanya** oleh `scaffold_brief.py --nn <NN-pengganti>` atas brief yang disebut kolom `supersedes` baris pengganti. Asal sah: `BLOCKED`, atau `READY` hilir yang diterbitkan ulang sesudah perbaikan supaya urutan `NN` tetap urutan eksekusi. Brief lama menerima `superseded_by: brief-<NN>`, brief pengganti membawa `supersedes: brief-<NN>[, brief-<NN>]`. `SUPERSEDED` tertutup: dilewati traversal `architect`, tidak dihitung predikat cakupan `Covers:`/`Fulfills:`, dan tidak pernah kembali ke status lain.
   - Field `repairs: brief-<NN>` (bukan status): brief perbaikan atas brief `DONE` yang ditahan `{taskdir}/HALT.md` (gerbang kompilasi, scope, simbol, atau berkas liar `architect`). Ditulis `scaffold_brief.py --nn` dari kolom spec `repairs`, yang sekaligus mencabut `HALT.md`.

   *(Dilarang memakai `DRAFT` atau `APPROVED` pada brief — approval berhenti di BRD dan PRD — dan dilarang menulis `SUPERSEDED` dengan tangan: Check C `validate_briefs.py` menolak tautan yang tidak dua arah.)*

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
   - **Nol verifikasi di dalam brief** *(Check F)*: dilarang baris `— verifikasi:`, perintah build/test, maupun seksi `## Verification` di seksi mana pun — build dan test dijalankan sekali di penutup taskdir. Ini **rumah kanonik** aturan tersebut.

6. **Baris `Covers:` — Pendaratan Acceptance Criteria** *(Check H, Check I)*: rumah kanonik aturan ini; rasional dan remediasinya di `../references/check-catalog.md`.

   - Berdiri tepat di bawah paragraf `## Objective`, berformat `Covers: AC-1, AC-3` — nomor disalin apa adanya dari `## Acceptance criteria` PRD, dipisah koma, dan **hanya** `AC-{n}` (sumbu akar punya barisnya sendiri di butir 7). Bukan seksi baru.
   - Gabungan `Covers:` seluruh brief taskdir menutup **setiap** `AC-{n}` PRD; `AC-{n}` yang tidak ada di PRD dan baris yang hilang dilarang. Brief sah tanpa AC (jalur `LANGSUNG`/`RCA` tanpa PRD) menulis `Covers: — (<alasan>)`.
   - AC `test otomatis`: minimal satu baris berkas test di `## File scope` brief pengklaim menyebut `AC-{n}` itu di kolom `Anchor` atau "Apa yang berubah" — penamaan, bukan sekadar ada berkas test.
   - AC `QA manual:`: diklaim di `Covers:` seperti AC lain, dan langkah manualnya turun ke `## Risk & rollback` brief pengklaim sebagai kalimat operasional bernomor AC — dilarang di `## Analysis trace`.

7. **Baris `Fulfills:` — Pendaratan Success Criteria Akar, hanya pada rantai tanpa PRD** *(Check G, Check S)*: rumah kanonik aturan ini; rasional di `../references/check-catalog.md` Check G.

   - **Rantai ber-PRD tidak menulis baris ini sama sekali** — keterlacakan `SC-{n}` diangkut kolom `Akar` PRD (predikat G2 `analyst`, lalu Check H). `scaffold_brief.py` tidak menuliskannya, dan Check S menolak brief yang memuatnya.
   - **Rantai tanpa PRD** (`chain: BRIEF`, jalur `RCA`): baris `Fulfills: SC-2, SC-4` tepat di bawah `Covers:`, nomor disalin apa adanya dari `## Success Criteria` `TASK.md`. Gabungannya menutup **setiap** `SC-{n}`; nomor hantu dan baris hilang dilarang; taskdir tanpa `TASK.md` menulis `Fulfills: — (akar absen)`. Bukan seksi baru.
   - **Nomor, bukan prosa**: prosa butir SC dilarang disalin ke seksi mana pun — ia memuat `— verifikasi:` yang ditolak Check F.

8. **Satu baris `Consumes` = satu brief sumber (`## Interfaces`)**: brief yang mengonsumsi dari dua pendahulu menulis **dua baris `Consumes`**, masing-masing menyebut satu `brief-NN`, seperti contoh bagian 1. Ini **rumah kanonik** aturan tersebut; `plan` menagihnya lewat Check C.

   Baris `Produces` tidak memikul aturan ini: banyak signature sah berdiri di satu baris dipisah titik koma. Rasionalnya di `../references/check-catalog.md` Check C.

9. **Integritas Batas Cakupan (`## File scope` & `## Out of scope`)**:

   - Baris `modify` wajib menyertakan simbol `Anchor` (nama method, field, class), dan simbol itu wajib **disebut minimal satu langkah `## Steps`**. Anchor yang tak pernah dipakai langkah mana pun berarti brief menamai satu titik sisip lalu mengerjakan titik lain; `plan` menagihnya lewat Check N.
   - Seluruh file yang disentuh wajib terdaftar. Implementor dilarang menyentuh file di luar tabel ini, **maupun simbol di luar kolom `Anchor` baris berkas itu**. Simbol tambahan yang ternyata harus ikut berubah dilaporkan implementor, bukan disunting diam-diam; `architect` membandingkan peta simbol commit (`architect/scripts/symbol_map.py`) terhadap kolom ini.
   - Tidak ada seksi yang dibiarkan kosong tanpa penjelasan; jika nihil, tulis "tidak ada" beserta alasannya.

10. **Pendaratan Migrasi (`## Migration` & `## Risk & rollback`)** *(Check J)*: rumah kanonik aturan ini. Berlaku pada `## Migration requirements` PRD yang bukan "tidak perlu", **dan** pada berkas migrasi baru yang ditetapkan scan Fase 2 butir 5 di jalur tanpa PRD; rasional dan kasus ORM lengkapnya di `../references/check-catalog.md` Check J.

   - `## Migration` memuat DDL utuh (nama berkas + `CREATE`/`ALTER`), bukan "sesuai PRD", dan urutan deploy sebagai langkah bernomor — satu fase satu langkah (mis. Expand-Contract), dengan penanda fase milik brief ini vs brief berikutnya. Jalur tanpa PRD menurunkan urutannya sendiri: migrasi tidak backward-compatible mengikuti Expand-Contract menurut `## Failure signatures` adapter.
   - `## Risk & rollback` memuat rollback plan operasional: cara mengembalikan skema beserta tanda kegagalannya. Satu sisi terisi tanpa pasangannya adalah cacat.
   - **Skema dibentuk ORM**: baris `Berkas migrasi: tidak ada — skema dibentuk ORM (<setelan>)` membebaskan kewajiban berkas migrasi di `## File scope` hanya bila `invariants.md`/`commands.md` profil menyatakannya (`ddl-auto`, `hbm2ddl`, `synchronize: true`, `AutoMigrate`); DDL setara, urutan deploy, dan rollback plan tetap wajib.
   - Tanpa pemicu → tiap brief menulis "tidak perlu" beserta alasannya di `## Migration`, dan Check J dilewati.

11. **Derivasi `risk:` (Frontmatter)**: Nilainya **dinilai per unit kerja** atas isi `## File scope` dan `## Steps` brief itu sendiri, bukan disalin dari dokumen hulu. Ini **rumah kanonik** aturan tersebut; `plan` menagihnya lewat Check K di `../references/check-catalog.md`.

    > **Salinan tersinkron.** Tabel predikat di bawah disalin verbatim ke `agents/brief-reviewer.md` fokus #3, karena subagent itu tidak dapat membaca berkas plugin ini. Menyunting salah satu tanpa yang lain membuat `plan` dan reviewernya memvonis `risk:` dengan aturan berbeda. Sunting keduanya dalam satu perubahan.

    | Nilai | Predikat — brief menyentuh salah satu |
    |---|---|
    | `BREAKING` | mengubah tipe, nama, atau kewajiban field yang sudah dipakai consumer; menghapus atau mengubah path/method endpoint terbit; mengubah atau membuang transisi status yang terekspos keluar; migrasi destruktif (`DROP`, `NOT NULL` tanpa default, penyempitan tipe) |
    | `MAJOR` | penambahan aditif yang mengubah kontrak keluar tanpa membatalkan yang lama: endpoint baru, field opsional baru, nilai enum baru, tabel atau kolom nullable baru |
    | `MINOR` | perubahan internal tanpa kontrak keluar: refactor, perbaikan logika, penyesuaian test, konfigurasi, index penunjang |

    - **Plafon akar**: nilai brief dilarang melampaui `risk:` frontmatter `{taskdir}/TASK.md`. Brief yang predikatnya menuntut nilai lebih tinggi adalah **pemicu eskalasi** — hentikan penulisan batch dan kembalikan ke pemanggil — `backenddev:analyst` sebagai pemicu eskalasi chain nomor 2 pada lane planning; `backenddev:tech-lead` pada jalur `RCA` (`../references/entry-rules.md` bagian 1C). Dilarang melunakkan predikat agar muat di bawah plafon, dan dilarang menaikkan risk sendiri.
    - `TASK.md` absen → plafonnya diambil dari parameter `risk` yang diteruskan pemanggil. `risk:` `TASK.md` bernilai `-` (lane non-mutasi kode) → plafon brief adalah `MINOR`.
    - Nilai `-` bukan nilai sah bagi brief: brief selalu memikul salah satu dari tiga enum. Satu batch boleh memuat brief bernilai campur — itu justru bentuk normalnya, karena tiap brief menyentuh permukaan yang berbeda.

12. **Kecukupan Unit (`## Steps` & `## File scope`)**: tiap langkah dan tiap berkas brief berakar pada `AC-{n}` baris `Covers:` atau `SC-{n}` baris `Fulfills:` brief itu sendiri. Langkah yang tak menggerakkan satu pun di antaranya dihapus, bukan dibenarkan belakangan dengan menambah nomor ke baris `Covers:` — arah itu terbalik, dan matriks Fase 3 sudah mengunci alokasinya lebih dulu. Butir 6 dan 7 menagih arah maju (tiap `AC-{n}` punya brief); butir ini arah baliknya (tiap langkah punya `AC-{n}`), dan keduanya dibutuhkan karena batch yang menutup seluruh AC tetap boleh memuat kerja yang tak satu pun AC minta.

    - **Abstraksi berkonsumen tunggal dilarang**: interface, factory, strategy, atau lapisan adapter berimplementasi tunggal dan berpemanggil tunggal di seluruh batch ditulis sebagai pemanggilan langsung, kecuali `## Anti-patterns` atau `## Code conventions` profil menuntut sebaliknya. "Nanti ada implementasi kedua" bukan akar.
    - **Flag konfigurasi, kolom, dan index antisipatif dilarang**: yang tidak dibaca satu pun langkah batch ini tidak ditulis. Kolom dan index yang memang dituntut `## Migration requirements` PRD dikecualikan — akarnya ada, dan letaknya di sana.
    - **Temuan bukan langkah**: perbaikan yang ditemukan saat memetakan kode dan tidak dituntut akar mana pun dicatat sebagai temuan di `backenddev/issues/`, bukan diselipkan ke `## Steps` brief terdekat — selipan itu melewati satu-satunya gerbang yang pernah menilai perlu-tidaknya ia dikerjakan.
