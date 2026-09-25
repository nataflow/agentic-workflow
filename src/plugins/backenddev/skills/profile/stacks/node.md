# Stack adapter — `node`

Node.js/TypeScript dengan framework HTTP. Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `package.json` di root, workspace terdeklarasi, `apps/*`, `packages/*`, `services/*`, atau
anak langsung root (sama dengan `hooks/detect.py`).

- **Penanda wajib**: minimal satu framework server di `dependencies` (bukan `devDependencies`,
  `overrides`, atau `keywords`) — `@nestjs/core`, `express`, `fastify`, `koa`, `@hapi/hapi`, `hono`.
  Paket dengan `react`/`vue`/`next` tanpa satu pun penanda ini adalah frontend, bukan stack backend ini.
- **Pemutus terhadap `bun`**: `elysia` di `dependencies`, atau `hono` bersama lockfile Bun
  (`bun.lockb`/`bun.lock`) atau `bunfig.toml`, dan tanpa `@nestjs/core`/`express` → stack-nya `bun`,
  bukan `node`. `hono` di atas Node (tanpa penanda Bun) tetap `node`.
- **Nama project**: field `name` pada `package.json`; pada workspace, `name` paket yang memuat entrypoint server.
- **Versi runtime**: `engines.node`, `.nvmrc`, atau `volta.node`.
- **Package manager aktif**: ditentukan lockfile yang ada — `pnpm-lock.yaml`, `yarn.lock`,
  `package-lock.json`. Bila lebih dari satu, yang paling baru diubah adalah yang aktif.
- **Entrypoint**: `main`/`exports` pada `package.json`, atau `src/main.ts` (Nest) / `src/index.ts` /
  `src/server.ts`. Direktori kode = `source_root` (lazim `src/`).
- **Workspace**: `pnpm-workspace.yaml`, `workspaces` pada `package.json`, `turbo.json`, `nx.json` →
  `source_root` menunjuk paket API, submodul lain dicatat di `## Module structure` profil.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| DB & ORM | `prisma`, `@prisma/client`, `typeorm`, `drizzle-orm`, `sequelize`, `mongoose`, `kysely` |
| Driver | `pg`, `mysql2`, `better-sqlite3`, `mongodb` |
| Migration | `prisma migrate`, `typeorm migration`, `drizzle-kit`, `knex` |
| Messaging | `amqplib`, `kafkajs`, `bullmq`, `@nestjs/microservices`, `nats` |
| Cache | `ioredis`, `redis`, `cache-manager`, `lru-cache` |
| Validasi | `zod`, `class-validator`, `joi`, `yup`, `@sinclair/typebox` |
| Auth | `passport`, `@nestjs/jwt`, `jsonwebtoken`, `lucia` |

Konfigurasi per environment: `.env`, `.env.example`, `config/*.ts`, `@nestjs/config`. Setelan yang
mengubah semantik runtime: ukuran pool koneksi, `synchronize` pada TypeORM, level isolasi transaksi,
dan `strict` pada `tsconfig.json` — `strict: false` mematikan sebagian besar jaminan tipe.

Penanda zona waktu runtime: `process.env.TZ`, `ENV TZ=` di `Dockerfile`, opsi `timezone` pada
konfigurasi driver DB, dan pemakaian `new Date()` vs penyimpanan `timestamptz`.

## Commands

| Perintah | Nilai |
|---|---|
| build | `<pm> run build` (lazim `tsc -p tsconfig.build.json` atau bundler) |
| typecheck | `<pm> run typecheck`, atau `npx tsc --noEmit` |
| typecheck-scoped | tidak berlaku (`tsc` menilai seluruh program) |
| typecheck-per-brief | `ya` — `tsc --noEmit` cukup murah untuk dijalankan per brief |
| lint | `<pm> run lint`, atau `npx eslint .` |
| test | `<pm> test` (`jest`, `vitest run`, atau `node --test`) |
| test-single | `npx jest <pola>` / `npx vitest run <berkas> -t "<nama>"` |
| migration | `npx prisma migrate deploy`, `npx typeorm migration:run`, atau `npx drizzle-kit migrate` |

`<pm>` diambil dari lockfile. Skrip di `package.json` menang atas perintah generik di atas.

Migrasi: Prisma di `prisma/migrations/<timestamp>_<nama>/migration.sql`; TypeORM di
`src/migrations/<timestamp>-<Nama>.ts`; Drizzle di `drizzle/`. High-water mark = timestamp tertinggi.

## Layer taxonomy

Urutan eksekusi kode dalam satu brief:
**Schema & Migration → Repository/Model → Service → DTO & Controller → Wiring modul → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Schema | `schema.prisma`, entity, atau tabel Drizzle | `prisma/`, `src/<domain>/entities/` |
| Repository | `<nama>.repository.ts` | `src/<domain>/` |
| Service | `<nama>.service.ts` | `src/<domain>/` |
| Controller | `<nama>.controller.ts` (Nest) atau `<nama>.routes.ts` (Express/Fastify) | `src/<domain>/` |
| DTO | `dto/create-<nama>.dto.ts`, atau skema `zod` | `src/<domain>/dto/` |
| Wiring | `<nama>.module.ts` (Nest) atau pendaftaran rute terpusat | `src/<domain>/`, `src/app.ts` |
| Test | `<nama>.spec.ts` / `<nama>.test.ts` | bersebelahan atau `test/` |

Lima jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **Setiap `Promise` di-`await` atau dirantai.** Promise yang dilepas tanpa `await` membuat error-nya
   jadi unhandled rejection yang mematikan proses di Node modern, dan urutan operasinya tak terjamin.
2. **Transaksi diteruskan sebagai parameter.** Klien transaksional (`tx` pada `prisma.$transaction`,
   `queryRunner.manager`) wajib dipakai di seluruh operasi dalam blok itu; memakai klien global di
   dalamnya menjalankan query di luar transaksi.
3. **Validasi di batas, bukan di dalam.** Body dan query divalidasi tepat setelah masuk handler
   dengan skema yang sama yang menurunkan tipenya; `as` casting tanpa validasi adalah lubang tipe.
4. **Entity dan DTO tidak digabung.** Mengembalikan entity langsung membocorkan kolom internal dan
   memicu pemuatan relasi tak terduga saat serialisasi.
5. **Kerja berat tidak di event loop.** Perulangan besar atau kriptografi sinkron memblokir seluruh
   proses; pindahkan ke worker thread atau antrean.

`package.json` dan lockfile tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Deklarasi tipe/kelas/interface | `Grep -n "(export )?(class\|interface\|type) <Nama>\b"` di `source_root` |
| Pemakai simbol | `Grep -n "<Simbol>"`, saring baris `import` dan `export ... from` |
| Pemanggil method | `Grep -n "\.<method>\("`, telusuri tipe receiver via deklarasi field |
| Implementasi interface | `Grep -n "implements <Interface>\|extends <Base>"` |
| Titik masuk HTTP | Nest: `Grep -n "@(Get\|Post\|Put\|Patch\|Delete)\("`; Express/Fastify: `Grep -n "(router\|app)\.(get\|post\|put\|patch\|delete)\("` |
| Rantai Controller→Service→Repository | `Read` controller, catat parameter constructor → `Glob` `**/<nama>.service.ts` → `Read` method → `Glob` `**/<nama>.repository.ts` |
| Akses penyimpanan | `Grep -n "prisma\.\w+\.(find\|create\|update\|delete)\|repository\.(find\|save)\|db\.select\|\.query\("` |
| Batas transaksi | `Grep -n "\$transaction\|transaction(\|queryRunner\|startTransaction"` |
| Messaging / Scheduler | `"@EventPattern\|@MessagePattern\|new Queue(\|consume("` / `"@Cron\|node-cron\|setInterval"` |
| Middleware / Guard | Nest: `"@UseGuards\|CanActivate\|@Injectable"` ; lainnya: `"app.use(\|preHandler"` |
| Error handling terpusat | `"@Catch\|ExceptionFilter\|app.setErrorHandler\|err, req, res, next"` |
| Config & schema | `Glob` `**/{.env.example,*.config.ts}`; kode: `Grep -n "process.env\.\|ConfigService"`; migrasi `**/migrations/**` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35` — cukup menangkap dekorator,
signature, dan constructor injection di kepala kelas.

## Audit checklist

#### `security`

- **Rute tanpa guard atau middleware autentikasi.** Terutama rute yang ditambahkan setelah grup terlindungi ditutup.
- **Identitas dibaca dari body atau query, bukan dari token terverifikasi.** `userId` kiriman klien membuat impersonasi trivial.
- **Query mentah dirakit lewat template literal.** `$queryRawUnsafe`, `query(\`... ${input}\`)` melewati parameterisasi.
- **Body di-spread langsung ke operasi tulis.** `data: { ...req.body }` membiarkan klien mengubah kolom seperti `role` atau `isAdmin`.
- **Objek permintaan atau token ter-log utuh.** Header `authorization` ikut masuk log.
- **Response mengembalikan entity dengan kolom sensitif.** `passwordHash` ikut terserialisasi karena entity dikembalikan apa adanya.
- **Batas ukuran body tidak diset.** Parser JSON default menerima payload besar dan membuka celah kelelahan memori.

#### `transaction`

- **Klien global dipakai di dalam blok transaksi.** Query yang memakai `prisma` alih-alih `tx` berjalan di koneksi lain dan tidak ikut ter-rollback.
- **`await` hilang di dalam blok transaksi.** Blok selesai sebelum operasinya jalan, dan transaksi commit tanpa memuat perubahan itu.
- **Publish pesan atau event sebelum transaksi commit.** Consumer memproses data yang belum commit.
- **Operasi lintas-agregat tanpa transaksi.** Dua `update` berurutan tanpa pembungkus meninggalkan data separuh saat yang kedua gagal.
- **Baca lalu tulis tanpa penguncian atau kolom versi.** Dua request paralel saling menimpa pada mutasi saldo atau stok.

#### `data`

- **`number` untuk nominal uang.** Presisi ganda IEEE-754 menggeser hasil penjumlahan; wajib integer unit terkecil atau tipe desimal.
- **`Date` disimpan tanpa zona eksplisit.** Kolom `timestamp` tanpa zona plus `new Date()` lokal membuat perbandingan rentang salah di batas hari.
- **`as` casting menggantikan validasi.** Data eksternal diberi tipe tanpa diperiksa; kesalahan baru muncul jauh dari sumbernya.
- **Validasi hanya di controller.** Consumer antrean, scheduler, dan skrip impor menulis tabel sama tanpa aturan yang sama.
- **`parseInt`/`Number` tanpa memeriksa `NaN`.** Nilai gagal parse merambat sebagai `NaN` dan lolos perbandingan.
- **Pembedaan `null`, `undefined`, dan field absen tidak konsisten** antara DTO, ORM, dan JSON; "hapus nilai" jadi tak terbedakan dari "tidak diubah".

#### `persistence`

- **N+1 query.** Relasi diambil di dalam `for`/`map` alih-alih lewat `include`/`relations`/`join` sekali jalan.
- **`await` di dalam loop untuk operasi independen.** Bisa dijalankan sekaligus lewat satu query batch.
- **Query tanpa `take`/`limit` pada tabel yang tumbuh.** Seluruh tabel masuk memori proses.
- **`select` tidak dibatasi.** Mengambil seluruh kolom termasuk blob dan kolom sensitif yang tidak dipakai.
- **Klien ORM dibuat per request.** Setiap instance membuka pool sendiri sampai batas koneksi DB tercapai.
- **`findFirst`/`findUnique` yang mengembalikan `null` tidak dibedakan dari kegagalan query.** "Tidak ditemukan" jadi 500, atau kegagalan nyata jadi 404.

#### `concurrency`

- **Unhandled promise rejection.** Promise dilepas tanpa `await` maupun `.catch`; di Node modern prosesnya mati.
- **Consumer tanpa idempotensi.** Redelivery broker atau retry BullMQ memproses pesan yang sama dua kali.
- **Job tanpa batas retry atau dead-letter.** Pesan gagal berputar tanpa henti.
- **Scheduler multi-instance tanpa lock terdistribusi.** Setiap replika menjalankan cron yang sama bersamaan.
- **Panggilan keluar tanpa timeout.** `fetch` dan klien HTTP Node tidak punya batas waktu default.
- **Kerja sinkron berat di handler.** Memblokir event loop sehingga seluruh permintaan lain tertahan.
- **State modul yang bisa berubah dipakai lintas request.** Variabel level modul dibagi seluruh permintaan dalam satu proses.

#### `architecture`

- **Logika bisnis di controller.** Percabangan aturan ditulis bersama decode dan penentuan status HTTP.
- **Repository atau klien ORM dipanggil langsung dari controller**, melewati service.
- **Impor silang antar-domain.** Modul saling mengimpor langsung alih-alih lewat antarmuka yang dideklarasikan konsumen.
- **Dependensi sirkular antar-modul.** Nest melaporkannya saat startup; di Express bentuknya `undefined` yang muncul acak saat runtime.
- **Entity ORM dipakai sebagai tipe response di batas layer.**
- **`any` dipakai untuk melewati tipe di batas layer.** Menghapus jaminan yang jadi alasan memakai TypeScript.

## API surface

Dua bentuk deklarasi yang berbeda; tentukan lebih dulu mana yang dipakai repo.

- **Nest (deklaratif)**: prefix dari `@Controller('products')` digabung `setGlobalPrefix`; method dari
  `@Get(':id')`, `@Post()`, dan seterusnya. Parameter dari `@Param`, `@Query`, `@Body`. Status dari
  `@HttpCode`, default `201` untuk `@Post` dan `200` untuk sisanya. Otorisasi dari `@UseGuards` dan
  `@Roles` di level method atau kelas. Validasi dari `class-validator` pada DTO, aktif hanya bila
  `ValidationPipe` terpasang.
- **Express/Fastify (imperatif)**: sumber kebenarannya berkas pendaftaran rute, bukan handler.
  Prefix dari `app.use('/api/v1', router)` atau `fastify.register(routes, { prefix })`; method dan
  path dari `router.get('/:id', handler)`. Status dari `res.status(...)`, default `200`. Otorisasi
  dari middleware yang dipasang di router, diwarisi seluruh rute di bawahnya. Validasi dari skema
  (`zod`, `typebox`) yang dipanggil di awal handler atau lewat `schema` pada Fastify.

Bentuk request/response diturunkan dari tipe DTO atau skema validasi, bukan dari contoh payload.
Pembungkus generik repo dicatat sekali di kepala dokumen. Bentuk error dari `ExceptionFilter` (Nest)
atau error handler terpusat.

## Failure signatures

- **Stack trace V8.** Frame paling informatif adalah frame pertama yang path-nya di bawah
  `source_root` dan bukan `node_modules`. Bila sumbernya TypeScript hasil kompilasi, nomor barisnya
  merujuk `.js` kecuali source map aktif — periksa `sourceMap` di `tsconfig.json` sebelum memercayainya.
- **`UnhandledPromiseRejection`** — promise tanpa penangan. Pesannya menunjuk lokasi rejection, bukan
  lokasi promise itu dilepas; cari `await` yang hilang di jalur pemanggilnya.
- **`TypeError: Cannot read properties of undefined`** — lazimnya hasil query yang mengembalikan
  `null`/`undefined` satu langkah sebelumnya tanpa diperiksa.
- **`ECONNREFUSED` / `ETIMEDOUT`** — dependensi eksternal, bukan kode aplikasi. Periksa konfigurasi
  host dan apakah panggilan itu punya timeout.
- **`Timed out fetching a new connection from the connection pool`** (Prisma) — pool habis; cari
  transaksi panjang, klien yang dibuat per request, atau `await` yang hilang di jalur pelepasan.
- **`Nest can't resolve dependencies of ...`** saat startup — provider tidak terdaftar di modul, atau
  dependensi sirkular. Pesannya menyebut argumen ke berapa yang gagal diselesaikan.
- **Proses mati tanpa stack trace** — `process.exit` di jalur error, atau OOM. Periksa exit code:
  `137` menandakan kehabisan memori di container.
- **Test hijau sendiri tapi merah dalam satu run** — state bersama antar-test: mock yang tidak
  di-reset, koneksi DB yang dipakai ulang, atau timer palsu yang bocor antar-berkas.
