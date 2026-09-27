# Stack adapter — `bun`

Bun sebagai runtime, dengan Hono atau Elysia sebagai framework HTTP. Ditulis mengikuti `_CONTRACT.md`;
tujuh seksi, urutan tetap.

## Detection

Manifest: `package.json` bersama `bun.lockb`, `bun.lock`, atau `bunfig.toml` (di direktori paket itu
atau di root).

- **Penanda wajib**: `elysia` di `dependencies`, atau lockfile Bun (`bun.lockb` biner / `bun.lock`
  teks) atau `bunfig.toml` **dan** `hono` di `dependencies`. Salah satu saja tidak cukup: `hono` di atas Node adalah
  stack `node`; `bun.lockb` tanpa framework server adalah CLI atau pustaka.
- **Pemutus terhadap `node`**: bila `bun.lockb` hadir bersama `@nestjs/core` atau `express`, repo
  memakai Bun hanya sebagai package manager — stack-nya `node`, karena taksonomi layer dan jebakannya
  mengikuti framework, bukan runtime.
- **Nama project**: field `name` pada `package.json`.
- **Versi runtime**: `engines.bun`, atau keluaran `bun --version` di lingkungan kerja.
- **Entrypoint**: `main` pada `package.json`, atau `src/index.ts` yang mengekspor `default { fetch }`
  (Hono) / memanggil `.listen()` (Elysia). Direktori kode = `source_root` (lazim `src/`).
- **Workspace**: `workspaces` pada `package.json` — `source_root` menunjuk paket API.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| DB & ORM | `drizzle-orm`, `@prisma/client`, `kysely`, `bun:sqlite` (bawaan, tanpa entri manifest) |
| Driver | `postgres`, `pg`, `mysql2`, `@planetscale/database` |
| Migration | `drizzle-kit`, `prisma migrate`, skrip SQL manual |
| Messaging | `nats`, `kafkajs`, `bullmq`, `amqplib` |
| Cache | `ioredis`, `bun:sqlite` sebagai cache lokal, `lru-cache` |
| Validasi | `zod`, `@sinclair/typebox`, `valibot`, `elysia` (skema bawaan) |
| Auth | `hono/jwt`, `@elysiajs/jwt`, `jose`, `lucia` |

Konfigurasi per environment: Bun memuat `.env` otomatis tanpa `dotenv` — ketiadaan `dotenv` di
manifest **bukan** tanda konfigurasi tidak dipakai. Periksa `.env.example`, `bunfig.toml`, dan
`Bun.env`/`process.env` di kode. Setelan yang mengubah semantik runtime: ukuran pool driver DB,
mode WAL pada `bun:sqlite`, dan `strict` pada `tsconfig.json`.

Penanda zona waktu runtime: `TZ` di `.env` atau `Dockerfile`, dan opsi zona pada konfigurasi driver.

## Commands

| Perintah | Nilai |
|---|---|
| build | `bun build <entry> --target bun --outdir dist`; tidak berlaku bila repo dijalankan langsung dari sumber |
| typecheck | `bunx tsc --noEmit` — Bun menjalankan TypeScript tanpa memeriksa tipe, jadi langkah ini tidak boleh dilewati |
| typecheck-scoped | tidak berlaku (`tsc` menilai seluruh program) |
| typecheck-per-brief | `ya` — `tsc --noEmit` cukup murah untuk dijalankan per brief |
| lint | `bunx eslint .`, atau `bunx biome check .` bila `biome.json` ada |
| test | `bun test` |
| test-single | `bun test <pola-berkas> -t "<nama test>"` |
| migration-status | `bunx prisma migrate status`; Drizzle: `bunx drizzle-kit check` (konsistensi berkas migrasi, tanpa DB) — `profile` menjalankannya hanya sesudah izin user |
| migration-apply | `bunx drizzle-kit migrate`, `bunx prisma migrate deploy`, atau skrip `bun run` repo yang memanggil salah satunya — **dicatat untuk manusia, tidak pernah dijalankan plugin** |

Skrip di `package.json` menang atas perintah generik di atas.

Migrasi: Drizzle di `drizzle/`, Prisma di `prisma/migrations/`. High-water mark = timestamp tertinggi.

## Layer taxonomy

Urutan eksekusi kode dalam satu brief:
**Schema & Migration → Repository → Service → Skema validasi & Route → Wiring app → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Schema | `schema.ts` (Drizzle) atau `schema.prisma` | `src/db/`, `prisma/` |
| Repository | `<domain>.repository.ts` | `src/<domain>/` |
| Service | `<domain>.service.ts` | `src/<domain>/` |
| Route | `<domain>.routes.ts` — instance `Hono()`/`Elysia()` per domain | `src/<domain>/` |
| Skema validasi | `<domain>.schema.ts` — `zod`/`typebox` yang sekaligus menurunkan tipe | `src/<domain>/` |
| Wiring app | penggabungan sub-router | `src/index.ts`, `src/app.ts` |
| Test | `<nama>.test.ts` | bersebelahan atau `test/` |

Lima jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **Tipe tidak diperiksa saat runtime Bun.** `bun run` menghapus tipe tanpa memvalidasinya, sehingga
   kesalahan tipe hanya tertangkap oleh `tsc --noEmit`. Berkas yang lolos jalan bukan berarti benar.
2. **Handler mengembalikan `Response`, bukan menulis ke objek respons.** Lupa `return` pada
   `c.json(...)` menghasilkan respons kosong, bukan error — kegagalannya diam.
3. **Setiap `Promise` di-`await` atau dirantai.** Promise yang dilepas menghasilkan unhandled
   rejection dan urutan operasi yang tak terjamin.
4. **Skema validasi adalah sumber tipe.** Tipe request diturunkan dari skema (`z.infer`), bukan
   ditulis terpisah; dua deklarasi akan menyimpang diam-diam.
5. **API khusus Bun tidak dipakai di jalur yang harus portabel.** `Bun.file`, `bun:sqlite`, dan
   `Bun.password` tidak tersedia di runtime lain; batasi ke lapisan platform bila repo juga
   menargetkan Node atau edge runtime.

`package.json` dan `bun.lockb` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Deklarasi tipe/skema | `Grep -n "(export )?(const\|type\|interface) <Nama>\b"`; skema zod: `Grep -n "<Nama>Schema"` |
| Pemakai simbol | `Grep -n "<Simbol>"`, saring baris `import` dan `export ... from` |
| Pemanggil fungsi/method | `Grep -n "\.<method>\(\|<fungsi>\("`, telusuri sumbernya via baris import |
| Titik masuk HTTP | `Grep -n "\.(get\|post\|put\|patch\|delete)\("` pada berkas `*routes*.ts`, `src/index.ts` |
| Rantai Route→Service→Repository | `Read` handler rute, catat service yang diimpor → `Glob` `**/<domain>.service.ts` → `Read` method → `Glob` `**/<domain>.repository.ts` |
| Akses penyimpanan | `Grep -n "db\.(select\|insert\|update\|delete)\|prisma\.\w+\.\|\.query\(\|sql\`"` |
| Batas transaksi | `Grep -n "db.transaction(\|\$transaction\|BEGIN"` |
| Middleware / Auth | `Grep -n "\.use(\|createMiddleware\|derive(\|jwt("` |
| Skema & validasi terpasang | `Grep -n "zValidator\|@hono/zod-validator\|t\.Object\|body:\s*t\."` |
| Messaging / Scheduler | `"consume(\|subscribe(\|new Worker("` / `"cron\|setInterval\|Bun.sleep"` |
| Error handling terpusat | `Grep -n "onError\|app.onError\|error(\|HTTPException"` |
| Config & schema | `Glob` `**/{.env.example,bunfig.toml,drizzle.config.ts}`; kode: `Grep -n "Bun.env\|process.env\."` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35` — cukup menangkap rantai
`.use()`, signature handler, dan skema validasi yang menempel pada rute.

## Audit checklist

#### `security`

- **Rute terdaftar di luar sub-router yang memasang middleware auth.** Rantai `.use()` pada Hono dan Elysia berlaku menurut urutan dan cakupan instance; rute yang didaftarkan sebelum `.use()` tidak terlindungi.
- **Identitas dibaca dari body atau query, bukan dari konteks hasil verifikasi token.**
- **Query dirakit lewat template literal biasa.** Tag `sql` pada driver melakukan parameterisasi; backtick polos tidak.
- **Body diteruskan utuh ke operasi tulis** tanpa memilih field, sehingga kolom seperti `role` bisa diubah klien.
- **`Bun.password.verify` diganti perbandingan string biasa.** Membuka celah timing attack sekaligus melewati verifikasi hash yang benar.
- **CORS dipasang permisif** (`origin: '*'`) pada rute yang memakai kredensial.
- **Error dikembalikan apa adanya lewat `onError`.** Pesan driver membocorkan struktur query dan nama tabel.

#### `transaction`

- **Klien global dipakai di dalam blok transaksi.** Query yang memakai `db` alih-alih `tx` berjalan di koneksi lain dan tidak ikut ter-rollback.
- **`await` hilang di dalam blok transaksi.** Blok selesai sebelum operasinya jalan; transaksi commit tanpa perubahan itu.
- **`bun:sqlite` tanpa mode WAL untuk beban tulis bersamaan.** Penulis kedua gagal dengan `SQLITE_BUSY` alih-alih menunggu.
- **Publish pesan sebelum transaksi commit.** Consumer memproses data yang belum commit.
- **Operasi lintas-tabel tanpa pembungkus transaksi.** Kegagalan di operasi kedua meninggalkan data separuh.

#### `data`

- **`number` untuk nominal uang.** Presisi ganda menggeser hasil penjumlahan.
- **`bun:sqlite` mengembalikan `INTEGER` besar sebagai `number`.** Nilai di atas `Number.MAX_SAFE_INTEGER` kehilangan presisi diam-diam; gunakan mode bigint driver.
- **Tipe request ditulis manual, terpisah dari skema validasi.** Keduanya menyimpang tanpa error kompilasi.
- **`as` casting menggantikan validasi** pada data yang berasal dari luar proses.
- **Validasi hanya di rute.** Consumer dan skrip yang menulis tabel sama melewati aturan yang sama.
- **`Date` disimpan tanpa zona eksplisit**, sehingga perbandingan rentang salah di batas hari.

#### `persistence`

- **N+1 query.** Relasi diambil di dalam loop alih-alih lewat `join`/`with` sekali jalan.
- **`await` di dalam loop untuk operasi independen** yang bisa dijadikan satu query batch.
- **Query tanpa `limit` pada tabel yang tumbuh.**
- **`select *` di jalur yang hanya butuh sebagian kolom**, termasuk kolom besar dan sensitif.
- **Koneksi DB dibuat per permintaan** alih-alih satu instance modul yang dipakai ulang.
- **"Tidak ditemukan" tidak dibedakan dari kegagalan query**, sehingga status HTTP-nya salah.

#### `concurrency`

- **Unhandled promise rejection.** Promise dilepas tanpa `await` maupun `.catch`.
- **Consumer tanpa idempotensi.** BullMQ mengulang job yang worker-nya mati sebelum menandai selesai, sehingga efek sampingnya terjadi dua kali.
- **State modul yang bisa berubah dipakai lintas request.** Satu proses Bun melayani seluruh permintaan; variabel level modul dibagi semuanya.
- **Panggilan keluar tanpa timeout.** `fetch` bawaan tidak punya batas waktu default; pakai `AbortSignal.timeout`.
- **Kerja sinkron berat di handler**, memblokir jalur permintaan lain.
- **Scheduler dijalankan di dalam proses server.** Setiap replika `Bun.serve` menjalankan `setInterval` yang sama, tanpa penguncian antar-proses.
- **`Bun.serve` dijalankan lebih dari sekali** dalam satu proses karena wiring ganda, sehingga port bentrok atau rute terdaftar dobel.

#### `architecture`

- **Logika bisnis di handler rute.** Percabangan aturan ditulis bersama parsing dan penentuan status.
- **Repository dipanggil langsung dari rute**, melewati service.
- **Impor silang antar-domain** alih-alih lewat antarmuka yang dideklarasikan konsumen.
- **API khusus Bun bocor ke lapisan domain**, membuat logika bisnis terikat runtime.
- **`any` dipakai untuk melewati tipe di batas layer.**
- **Sub-router tidak dipisah per domain**, sehingga satu berkas rute menumpuk seluruh permukaan HTTP.

## API surface

Endpoint didaftarkan secara imperatif pada instance framework; sumber kebenarannya berkas rute dan
wiring app, bukan handler.

- **Prefix**: `app.route('/api/v1', subRouter)` (Hono) atau `.group('/api/v1', app => ...)` (Elysia).
  Prefix bertingkat digabung dari luar ke dalam mengikuti urutan penggabungan di wiring.
- **Method + path**: `app.get('/products/:id', handler)`. Parameter path memakai `:name`.
- **Parameter**: `c.req.param('id')` dan `c.req.query('q')` (Hono); `({ params, query })` (Elysia).
- **Request body**: `await c.req.json()` atau hasil validator yang menempel di rute
  (`zValidator('json', Schema)` pada Hono; opsi `body: t.Object({...})` pada Elysia). Bila validator
  terpasang, skema itulah kontrak resminya — bukan pembacaan manual di dalam handler.
- **Response & status**: `c.json(data, 201)`; tanpa argumen kedua, statusnya `200`.
- **Otorisasi per endpoint**: middleware yang dipasang pada instance sebelum rute didaftarkan.
  Cakupannya adalah instance itu dan sub-router yang digabung sesudahnya — periksa urutannya, bukan
  hanya keberadaannya.
- **Bentuk error**: `app.onError(...)`, atau `HTTPException` yang dilempar dari handler.

## Failure signatures

- **Stack trace Bun.** Menunjuk langsung ke berkas TypeScript sumber tanpa perlu source map. Frame
  paling informatif adalah frame pertama di bawah `source_root` dan bukan `node_modules`.
- **Respons kosong berstatus 200** — handler tidak me-`return` hasil `c.json(...)`. Tidak ada error
  yang tercatat; gejalanya hanya body kosong.
- **`error: Cannot find module`** saat runtime padahal editor bersih — impor yang hanya ada sebagai
  tipe, atau ekstensi berkas yang tidak terselesaikan. Bun tidak menghapus impor tipe yang ditulis
  tanpa `import type`.
- **Kesalahan tipe yang tidak pernah muncul saat dijalankan** — Bun tidak memeriksa tipe; jalankan
  `bunx tsc --noEmit` sebelum menyimpulkan kodenya benar.
- **`SQLITE_BUSY`** (`bun:sqlite`) — penulis bersamaan tanpa mode WAL, atau transaksi yang dibiarkan terbuka.
- **`ECONNREFUSED` / `ETIMEDOUT`** — dependensi eksternal; periksa konfigurasi host dan ketiadaan timeout.
- **Proses mati tanpa jejak** — unhandled rejection, atau OOM di container (exit code `137`).
- **Test hijau sendiri tapi merah dalam satu run** — `bun test` berbagi satu proses antar-berkas;
  state modul, mock, dan koneksi DB bocor antar-test kecuali direset eksplisit.
