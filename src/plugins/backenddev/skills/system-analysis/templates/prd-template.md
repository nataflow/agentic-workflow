# PRD template — `system-analysis`

Dipakai di Fase 6 (`SKILL.md`) sebagai isi file `backenddev/docs/<YYMMDDhhmm>-<slug>/PRD.md`. Ikuti struktur ini persis — sembilan nama seksi dan urutannya adalah kontrak yang dibaca `plan` saat mengonversi PRD jadi brief. Dilarang mengganti, menambah, atau menghapus seksi.

PRD **tidak pernah** sampai ke `code-implementor`; yang ia baca hanya brief. Pembaca adalah penerjemah yang tidak membuat keputusan desain baru, sehingga setiap celah spesifikasi wajib ditutup konkret di PRD.

Tulis isi fenced block di bawah ini langsung ke berkas PRD, mulai dari `---` di baris pertama:

````markdown
---
title: <nama fitur/topik singkat>
source_brd: <path BRD sumber, atau "tidak ada — sumbu bisnis nol">
status: DRAFT
---

# PRD: <title> — <yyyy-mm-dd>

## API contract

### <METHOD> <path>
<deskripsi satu baris: tujuan endpoint ini>
- Dasar: BR-{n} | keputusan teknis murni — <alasan singkat>

**Request field**

| Field | Tipe | Wajib | Validasi |
|---|---|---|---|
| `nama` | string | wajib | tidak boleh kosong, maks 100 karakter |

**Response sukses** (`200`/`201`)

```json
{ "id": 1, "nama": "contoh" }
```

**Error**

| Kondisi | Kode | Pesan |
|---|---|---|
| `nama` kosong | 400 | "nama wajib diisi" |
| duplikat | 409 | "nama sudah dipakai" |

<ulangi blok `### <METHOD> <path>` untuk tiap endpoint baru/berubah>

## Status lifecycle

| Dari | Ke | Aktor | Syarat | Efek samping | Dasar |
|---|---|---|---|---|---|
| DRAFT | SUBMITTED | pembuat | semua item terisi | notifikasi ke approver | BR-2 |

<sebut transisi status yang baru/dihapus; "tidak ada perubahan lifecycle" bila memang tidak ada>

## Validation policy
<aturan validasi lintas-field dan urutan evaluasi saat terjadi kegagalan bersamaan>

## Permission & scope

| Endpoint | Role/permission | Scoping yang berlaku | Dasar |
|---|---|---|---|
| `POST /...` | `ORDER_CREATE` | store dari konteks user | BR-4 |

## Impact map

<hasil Fase 4. Tabel ini wajib memuat tepat 16 baris berurutan 1–16, satu per dimensi bagian B ../references/analysis-protocol.md. Dimensi yang tidak berlaku tetap ditulis dengan vonis tidak relevan beserta jejak sapuannya; dilarang menghapus baris dimensi.>

| # | Dimensi | Vonis | Bukti | Mendarat di |
|---|---|---|---|---|
| 1 | Definisi persistensi & kolom berubah | terdampak | `Order.status` varchar(16) -> varchar(24) — `internal/order/entity.go:31` | Task breakdown #2 |
| 2 | Konsumen endpoint | tidak relevan | sapuan `POST /orders` di `src/`: nihil pemanggil internal | — |
| 3 | Transisi lifecycle | <terdampak \| tidak relevan> | <simbol / file:line, atau alasan penafian> | <Task breakdown #n \| —> |
| 4 | Mirrored path (queue, scheduler, worker, websocket) | | | |
| 5 | Permission & scope baru | | | |
| 6 | Cache yang di-invalidate | | | |
| 7 | Integrasi eksternal | | | |
| 8 | Backfill data lama | | | |
| 9 | Migration & urutan deploy | | | |
| 10 | Feature flag & fallback | | | |
| 11 | Test existing yang pecah | | | |
| 12 | Konfigurasi & environment properties | | | |
| 13 | Kompatibilitas enum & serialisasi | | | |
| 14 | Dokumentasi API & OpenAPI | | | |
| 15 | Pesan error & i18n | | | |
| 16 | Dampak query & indexing | | | |

## Migration requirements
<migration schema + backfill yang dibutuhkan, atau "tidak perlu" dengan alasan teknis. Bila tidak backward-compatible: urutan deploy eksplisit>

## Task breakdown

| Urutan | Deskripsi | Permukaan (modul / layer) | Bergantung pada | AC terkait | Kriteria selesai |
|---|---|---|---|---|---|
| 1 | <unit perubahan> | `internal/order` · layer service | — | AC-1 | <kondisi yang membuat unit ini dianggap tuntas> |

## Acceptance criteria

| AC | Skenario (Given/When/Then) | Cara verifikasi | Dasar | Akar |
|---|---|---|---|---|
| AC-1 | <kondisi awal → aksi → hasil yang diharapkan> | test otomatis \| QA manual: `<langkah konkret>` | BR-3, EC-2 | SC-1 |

## Open questions
<tulis eksplisit "Tidak ada — semua pertanyaan terjawab", atau cantumkan maksimal 3 pertanyaan non-blocking:
- **<pertanyaan konkret>** — terdampak: <seksi PRD yang berubah kalau jawabannya lain; dilarang `## Task breakdown`, dilarang `## Business rules` BRD>; sementara dipakai: <asumsi aktif>
Aturan bisnis hulu yang sengaja tidak diterjemahkan jadi kontrak ditulis di sini dengan awalan token wajib:
- **BR-DISANGGAH: BR-{n}** — alasan: <mengapa aturan itu tidak turun jadi kontrak sistem>; sementara dipakai: <perilaku yang berlaku sebagai gantinya>
````

## Authoring rules

- **Status** selalu mulai `DRAFT`. Hanya `backenddev:analyst` yang mengubahnya jadi `APPROVED`, di gerbang dokumen Fase 4-nya dan sesudah persetujuan eksplisit user. Rumah kanonik kepemilikan itu `analyst/references/chain-rules.md` bagian 4; `system-analysis` dan gerbang `tech-lead` sama-sama dilarang menulis nilai itu.
- **`## API contract` tidak boleh setengah jadi.** Tiap endpoint wajib punya method + path, request field lengkap dengan tipe dan validasi per field, contoh response sukses, dan tabel error (`kondisi -> kode -> pesan`). Pindahkan field yang belum pasti ke `## Open questions`, dilarang membiarkan kolom kosong.
- **Kolom `Pesan` disalin, bukan dirumuskan.** Literal tiap cabang error diambil apa adanya dari seksi `### Error Surface` laporan `code-explorer` Profil S — huruf besar-kecil dan tanda bacanya ikut. `system-analysis` terikat guardrail **NOL SENTUHAN KODE** dan tidak membaca berkas sumber, sehingga pesan yang tidak sampai lewat laporan itu tidak punya jalur perolehan lain selain dikarang. Literal yang belum terbukti ditulis `<belum terbukti>` dan dinaikkan ke `## Open questions`; parafrase, terjemahan, dan "perapian" redaksional adalah cacat, karena string ini mengikat konsumen yang mencocokkannya.
- **Tipe kolom dan index berbukti, atau jadi asumsi bertoken.** Tipe, nullability, constraint, dan daftar index diambil dari berkas migrasi atau definisi entity lebih dulu; yang tidak terbukti dari kode boleh diambil lewat pembacaan skema read-only berkuota (`references/analysis-protocol.md` bagian A) dan **memikul penanda sumbernya** di kolom bukti. Yang tidak tertutup keduanya turun ke `## Open questions` berlabel `sementara dipakai:` beserta nilai yang diasumsikan — tidak pernah ditulis sebagai fakta.
- **Tiap keputusan teknis dirujuk lewat dua kolom terpisah.** Kolom `Dasar` di endpoint, lifecycle, permission, dan acceptance criteria wajib menyebut `BR-{n}` — dan pada acceptance criteria juga `EC-{n}` — asalnya di BRD, atau ditandai "keputusan teknis murni" disertai alasan singkat. Kolom `Akar`, khusus tabel `## Acceptance criteria`, wajib menyebut `SC-{n}` `## Success Criteria` `TASK.md` yang ditagih AC itu, atau `—` bila `TASK.md` absen. Dilarang menggabungkan kedua sumbu ke satu kolom: `Dasar` menjawab "aturan bisnis mana", `Akar` menjawab "kriteria akar mana", dan keduanya digrep terpisah oleh self-test di bawah.
- **Nol toleransi untuk "TBD".** Pindahkan pertanyaan yang belum terjawab ke `## Open questions` sebagai pertanyaan konkret, dan tulis seksi asalnya dengan data konkret yang sudah terverifikasi.
- **Anggaran `## Open questions`: target nol, batas maksimum tiga, dan "non-blocking" berpredikat operasional.** Fakta kode diselesaikan di Fase 1; keputusan user diklarifikasi di Fase 2. Sebuah entri disebut non-blocking hanya bila kolom `terdampak:`-nya **tidak menyebut `## Task breakdown`** — jawaban yang mengubah dekomposisi teknis membatalkan brief yang akan disusun `plan` di atasnya. Entri semacam itu memblokir: PRD berhenti di `DRAFT` dan approval tidak diajukan. Predikat kedua berlaku sejajar: entri yang `terdampak:`-nya menyebut `## Business rules` BRD juga memblokir — jawabannya mengubah aturan bisnis yang sudah `APPROVED`, dan itu amandemen hulu, bukan asumsi sementara. **Predikat ketiga tidak membaca `terdampak:` sama sekali, dan itu alasannya ada.** Dua predikat di atas menilai entri lewat kolom yang ditulis penulis entri itu sendiri — nol verifikasi silang, sehingga apa pun dapat dinyatakan non-blocking dengan menuliskan seksi lain di `terdampak:`. Predikat ketiga menutupnya dengan membaca **isi asumsinya** terhadap dokumen: entri yang `sementara dipakai:`-nya menyebut nilai, tipe, nama field, nilai enum, nama role, atau ambang yang **muncul di** `## API contract`, `## Status lifecycle`, `## Validation policy`, `## Permission & scope`, atau `## Task breakdown` otomatis bervonis **memblokir**, apa pun isi `terdampak:`-nya. Asumsi yang sudah membentuk salah satu dari lima seksi itu bukan lagi asumsi sementara — ia kontrak yang belum diputuskan.

Dengan predikat ketiga, `terdampak:` turun jadi dokumentasi niat penulis, bukan gerbang. Ini **rumah kanonik** ketiga predikat tersebut; `plan/references/entry-rules.md` bagian 1 menegakkannya sebagai jaring pengaman di gerbang masuk, bukan definisi tandingan.
- **Aturan bisnis yang gugur wajib bertoken, bukan berprosa.** `BR-{n}` yang sengaja tidak diterjemahkan jadi kontrak ditulis sebagai entri `BR-DISANGGAH: BR-{n}` di `## Open questions`, satu entri per nomor, dan ikut dihitung terhadap anggaran tiga entri. Token itu bukan formalitas: `backenddev:analyst` menggrepnya untuk mengenumerasi tiap aturan yang gugur ke user di gerbang dokumen (`analyst/references/chain-rules.md` bagian 4 butir 3), dan tanpa token itu aturan bisnis dapat hilang dari implementasi tanpa satu pun pihak memutuskannya. Penyanggahan berprosa tanpa token adalah cacat.
- **`## Impact map` bervonis penuh.** Enam belas baris wajib hadir dengan vonis eksplisit. Tiap baris `terdampak` memikul bukti simbol konkret (`file:line`, nama entity/kolom, nama cache, berkas test) dan kolom `Mendarat di` yang menunjuk nomor baris `## Task breakdown`. Lima dimensi rawan bocor (2, 4, 11, 13, 16) wajib menyertakan jejak sapuan konkret pada vonis `tidak relevan` — dilarang menulis prosa tanpa simbol.
- **`## Task breakdown` berhenti pada unit dan permukaan, bukan berkas.** Tiap baris menamai satu unit perubahan terisolasi beserta permukaannya — modul, layer menurut `## Layer taxonomy` adapter, atau berkas migrasi — dan setiap item migrasi, mirrored path, serta konfigurasi memiliki barisnya sendiri. **Dilarang menetapkan path berkas `src/` konkret, urutan berkas, atau nama kelas test**: pemilihan berkas beserta penamaannya adalah wewenang tunggal `plan`, yang membacanya dari profil repositori dan adapter stack. Menetapkannya di sini membuat PRD dan brief sama-sama berwenang atas hal yang sama, dan setiap perbedaan penamaan yang wajar berubah jadi tuntutan amandemen PRD. Kolom "Kriteria selesai" merujuk `AC-{n}`; kolom `Bergantung pada` menjadi arah DAG antar-unit yang diturunkan `plan` jadi urutan brief.
- **Cakupan `## Acceptance criteria`.** Tiap endpoint memiliki minimal satu AC jalur sukses; tiap baris tabel error memiliki AC sendiri; tiap `EC-{n}` BRD memiliki AC teruji. Kolom "Cara verifikasi" menetapkan **jenis** alat ukurnya, bukan namanya: `test otomatis` bila AC itu wajib digerbangi test, atau `QA manual: <langkah konkret>` bila tidak dapat digerbangi test. Nama kelas test tidak ditulis di sini — `plan` menamainya dari konvensi repo, dan Check I menagih tiap AC bertanda `test otomatis` punya berkas test di `## File scope` brief pengklaimnya. Frasa generik ("diuji manual", "dicek QA") tetap cacat.

## Self-test pra-reviewer

Dijalankan `system-analysis` atas `PRD.md` yang baru ditulis, sebelum `prd-reviewer` didispatch, lewat `skills/_common/validate_doc.py --kind prd --taskdir <taskdir>`. Validator menagih butir mekanis (ID check di kurung siku) dan menerapkan pengecualian butir 11 sendiri; butir `MANUAL` dinilai penulis memakai prosa di bawah. Satu `FAIL` berarti PRD diperbaiki seketika lalu validator dijalankan ulang. Butir 1–4 menyandingkan PRD dengan dokumen hulunya, butir 5–10 memeriksa integritas PRD sendiri, dan butir 10b menutup arah balik keduanya — kontrak yang tak punya akar di mana pun.

1. **Cakupan `BR-{n}`** [P1]: tiap `BR-{n}` BRD disebut minimal satu kolom `Dasar` (baris `- Dasar:` endpoint atau kolom tabel), atau ditulis sebagai entri `BR-DISANGGAH: BR-{n}` di `## Open questions` — penyanggahan berprosa tanpa token itu gagal, karena `analyst` menggrep token itu untuk mengenumerasi aturan yang gugur. Nomor `Dasar` yang tidak ada di BRD adalah rujukan hantu.
2. **Cakupan `EC-{n}`** [P2]: tiap `EC-{n}` BRD (selain `EC-0`) disebut kolom `Dasar` tabel `## Acceptance criteria`; `EC-{n}` di AC yang tidak ada di BRD adalah rujukan hantu.
3. **Cakupan `SC-{n}`** [P3]: `TASK.md` ada → tiap `SC-{n}`-nya disebut minimal satu kolom `Akar`, dan tiap `SC-{n}` di kolom `Akar` ada di `TASK.md`. `TASK.md` absen → seluruh kolom `Akar` berisi `—`.
4. **Batas ruang lingkup hulu** [P4 MANUAL]: tidak satu pun endpoint, transisi status, aturan validasi, atau baris `## Task breakdown` menyentuh butir `## Out of scope` BRD maupun `## Out of Scope` `TASK.md`. Kontrak yang menyentuhnya dikembalikan ke `backenddev:analyst` sebagai permintaan amandemen akar (`analyst/references/chain-rules.md` bagian 5) dan menunggu keputusan user di sana — bukan diterbitkan diam-diam, bukan pula dibuang sendiri.
5. **Realitas verifikasi AC** [P5]: kolom "Cara verifikasi" bernilai persis `test otomatis`, atau `QA manual:` diikuti langkah konkret; frasa generik dan nama kelas test gagal — penamaan berkas test milik `plan`.
6. **Struktur & frontmatter** [P6]: frontmatter `title`, `source_brd`, `status: DRAFT`; tepat satu H1 `# PRD: …`; sembilan seksi baku dengan nama dan urutan persis template.
7. **`## Impact map` penuh** [P7]: tepat 16 baris bernomor 1–16, vonis `terdampak` atau `tidak relevan`. Baris `terdampak` memuat bukti simbol dan `Mendarat di` = `Task breakdown #<n>` yang ada; dimensi rawan bocor (2, 4, 11, 13, 16) memuat jejak sapuan bersimbol sekalipun `tidak relevan`.
8. **Nol placeholder** [P8]: nol `TBD`/`TODO`, dan tidak ada sel tabel kosong maupun seksi kosong di empat pilar kontrak (`## API contract`, `## Status lifecycle`, `## Validation policy`, `## Permission & scope`).
9. **Anggaran `## Open questions`** [P9]: maksimal tiga entri termasuk `BR-DISANGGAH:`, tiap entri memuat `sementara dipakai:`, entri berpertanyaan memuat `terdampak:`. `terdampak:` yang menyebut `## Task breakdown` atau `## Business rules` memblokir — PRD tetap `DRAFT` dan approval tidak diajukan.
9b. **Silang isi asumsi** [P9b] — predikat ketiga `## Authoring rules`, satu-satunya yang tidak bersandar pada kolom yang ditulis penulis entri: token ber-backtick di `sementara dipakai:` yang muncul di `## API contract`, `## Status lifecycle`, `## Validation policy`, `## Permission & scope`, atau `## Task breakdown` membuat entri itu **memblokir**, apa pun isi `terdampak:`-nya. Validator hanya melihat token ber-backtick — tulis nilai, tipe, nama field, enum, role, dan ambang asumsi dalam backtick.
10. **Nol penetapan berkas** [P10]: `## Task breakdown` dan `## Acceptance criteria` tidak memuat nama berkas sumber (ekstensi stack) maupun nama kelas test; kolom `Permukaan` menamai modul atau layer. Nama berkas migrasi dikecualikan — ia hidup di `## Migration requirements`.
10b. **Kecukupan kontrak** [P10b MANUAL] — arah balik butir 1–3, dan satu-satunya butir hulu yang tetap berlaku sekalipun BRD dan `TASK.md` sama-sama absen: ambil tiap field `## API contract`, nilai enum `## Status lifecycle`, aturan `## Validation policy`, baris `## Permission & scope`, baris tabel `## Error`, dan baris `## Task breakdown`, lalu periksa masing-masing berakar pada `BR-{n}`, `EC-{n}`, `SC-{n}`, atau permukaan berbukti `file:baris` hasil Fase 1. Yang tak berakar pada satu pun adalah kegagalan: hapus barisnya, dilarang dicarikan dasar susulan. Butir 1–3 memvonis akar yang tak punya kontrak; butir ini memvonis kontrak yang tak punya akar, dan tanpanya PRD boleh membengkak sebanyak apa pun asalkan tiap `BR-{n}` kebetulan tersebut di suatu tempat.
11. **Pengecualian**: BRD absen (`source_brd: tidak ada — sumbu bisnis nol`) melewati butir 1 dan 2 dan mempersempit butir 4 ke `TASK.md`; `TASK.md` absen mempersempit butir 4 ke BRD. Butir 5–10b tidak pernah dilewati; pada PRD tanpa BRD maupun `TASK.md`, butir 10b menyusut ke permukaan Fase 1 sebagai satu-satunya akar yang tersisa.

Hasilnya: keluaran validator ditambah satu baris per butir `MANUAL` (`butir <n>: lolos` atau `butir <n>: <jumlah> gagal — <daftar ID>`), dan dispatch `prd-reviewer` dilarang berangkat sebelum seluruhnya lolos.

## Contoh terisi — `orders-api` (dipangkas, tidak tersalin ke artefak)

Impact map di contoh ini memuat 3 dari 16 baris; artefak nyata wajib memuat 16 baris.

````markdown
---
title: Pembatalan order berstatus PAID
source_brd: backenddev/docs/2609051000-order-cancel-paid/BRD.md
status: DRAFT
---

# PRD: Pembatalan order berstatus PAID — 2026-09-05

## API contract

### POST /orders/{id}/cancel
Membatalkan order `PAID` milik toko pemanggil selama stoknya belum dikurangi.
- Dasar: BR-1

**Request field**

| Field | Tipe | Wajib | Validasi |
|---|---|---|---|
| — | — | — | tanpa body; `id` dari path, wajib UUID |

**Response sukses** (`200`)

```json
{ "id": "6f1c…", "status": "CANCELLED" }
```

**Error**

| Kondisi | Kode | Pesan |
|---|---|---|
| order bukan milik toko pemanggil | 404 | "order tidak ditemukan" |
| status bukan `PAID` atau stok sudah dikurangi | 409 | "ORDER_ALREADY_FULFILLED" |

## Status lifecycle

| Dari | Ke | Aktor | Syarat | Efek samping | Dasar |
|---|---|---|---|---|---|
| PAID | CANCELLED | pemilik toko | `stock_deducted_at` kosong | stok tiap item dikembalikan | BR-1, BR-2 |

## Validation policy
Kepemilikan toko diperiksa sebelum status; kegagalan kepemilikan mengembalikan 404 tanpa membocorkan status.

## Permission & scope

| Endpoint | Role/permission | Scoping yang berlaku | Dasar |
|---|---|---|---|
| `POST /orders/{id}/cancel` | `ORDER_CANCEL` | store dari konteks user | BR-1 |

## Impact map

| # | Dimensi | Vonis | Bukti | Mendarat di |
|---|---|---|---|---|
| 1 | Definisi persistensi & kolom berubah | tidak relevan | `orders.stock_deducted_at` sudah ada — `db/migrations/0031_orders.up.sql:9` | — |
| 2 | Konsumen endpoint | tidak relevan | sapuan `POST /orders/{id}/cancel` di `internal/`: nihil pemanggil (endpoint baru) | — |
| 3 | Transisi lifecycle | terdampak | `internal/order/state.go:27` | Task breakdown #1 |

## Migration requirements
Tidak perlu — kolom dan tabel yang dibutuhkan sudah ada.

## Task breakdown

| Urutan | Deskripsi | Permukaan (modul / layer) | Bergantung pada | AC terkait | Kriteria selesai |
|---|---|---|---|---|---|
| 1 | Daftarkan transisi `PAID → CANCELLED` | `internal/order` · state | — | AC-1 | `state.Can(PAID, CANCELLED)` true |
| 2 | Endpoint cancel + pengembalian stok | `internal/order` · handler, service | 1 | AC-1, AC-2 | test AC hijau |

## Acceptance criteria

| AC | Skenario (Given/When/Then) | Cara verifikasi | Dasar | Akar |
|---|---|---|---|---|
| AC-1 | order `PAID` stok belum dikurangi → `POST /orders/{id}/cancel` → 200, status `CANCELLED`, stok kembali | test otomatis | BR-1, BR-2 | SC-1, SC-3 |
| AC-2 | order `PAID` stok sudah dikurangi → `POST /orders/{id}/cancel` → 409 `ORDER_ALREADY_FULFILLED` | test otomatis | BR-1, EC-1 | SC-2 |

## Open questions
Tidak ada — semua pertanyaan terjawab
````
