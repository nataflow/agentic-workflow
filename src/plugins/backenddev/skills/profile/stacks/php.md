# Stack adapter — `php`

PHP dengan framework web. Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `composer.json` di root atau satu tingkat submodule.

- **Penanda wajib**: minimal satu framework di `require` — `laravel/framework`,
  `symfony/framework-bundle`, `slim/slim`, `laminas/laminas-mvc`, `yiisoft/yii2`. Paket tanpa penanda
  ini adalah pustaka, bukan stack backend ini.
- **Pemutus terhadap `php-codeigniter`**: `codeigniter4/framework` di `require` bersama berkas `spark`
  memindahkan repo ke adapter `php-codeigniter`; taksonomi dan jebakan di bawah tidak berlaku padanya.
- **Nama project**: field `name` pada `composer.json`.
- **Versi bahasa**: `require.php`, atau `config.platform.php` yang mengunci versi target Composer.
- **Entrypoint**: `public/index.php`. Direktori kode = `source_root` — `app/` (Laravel) atau
  `src/` (Symfony/Slim), dikonfirmasi dari peta `autoload.psr-4` di `composer.json`.
- **Pemutus Laravel vs Symfony**: keberadaan `artisan` menandai Laravel; `bin/console` menandai
  Symfony. Keduanya menentukan bentuk perintah di `## Commands`.
- **Model eksekusi**: PHP-FPM menjalankan satu proses per permintaan sehingga state mati di akhir
  permintaan; runtime persisten (Swoole, RoadRunner, Laravel Octane) tidak. Periksa `laravel/octane`,
  `spiral/roadrunner`, atau ekstensi Swoole — perbedaannya mengubah arti seluruh dimensi
  `concurrency` di bawah, dan wajib dicatat di `## Invariants` profil.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| DB & ORM | `laravel/framework` (Eloquent), `doctrine/orm`, `doctrine/dbal`, `illuminate/database` |
| Migration | migrasi bawaan Laravel, `doctrine/migrations` |
| Messaging | `laravel/horizon`, `symfony/messenger`, `php-amqplib/php-amqplib`, `enqueue` |
| Cache | `predis/predis`, `symfony/cache`, cache bawaan framework |
| Validasi | validator bawaan Laravel, `symfony/validator`, `respect/validation` |
| Auth | `laravel/sanctum`, `laravel/passport`, `lexik/jwt-authentication-bundle` |
| Kualitas | `phpstan/phpstan`, `vimeo/psalm`, `laravel/pint`, `friendsofphp/php-cs-fixer`, `phpunit/phpunit` |

Konfigurasi per environment: `.env`, `.env.example`, `config/*.php` (Laravel), `config/packages/*.yaml`
(Symfony). Setelan yang mengubah semantik runtime: driver antrean (`sync` menjalankan job secara
sinkron sehingga seluruh perilaku asinkron berubah), driver cache dan session, serta `APP_DEBUG` yang
menentukan apakah stack trace ikut keluar ke respons.

Penanda zona waktu runtime: `date.timezone` di `php.ini`, `config/app.php` kunci `timezone`,
`date_default_timezone_set`, dan `TZ` di `Dockerfile`.

## Commands

| Perintah | Laravel | Symfony |
|---|---|---|
| build | `composer install --no-dev --optimize-autoloader` | sama |
| typecheck | `vendor/bin/phpstan analyse` atau `vendor/bin/psalm` | sama |
| typecheck-scoped | `vendor/bin/phpstan analyse <path>` | sama |
| typecheck-per-brief | `tidak` — phpstan bukan compiler; vonisnya baseline-relatif dan konfigurasinya tidak selalu ada | sama |
| lint | `vendor/bin/pint --test`, atau `vendor/bin/php-cs-fixer fix --dry-run` | sama |
| test | `php artisan test`, atau `vendor/bin/phpunit` | `vendor/bin/phpunit` |
| test-single | `php artisan test --filter=<NamaTest>` | `vendor/bin/phpunit --filter=<NamaTest>` |
| migration | `php artisan migrate` | `php bin/console doctrine:migrations:migrate` |

Skrip di `composer.json` bagian `scripts` dan `Makefile` repo menang atas perintah generik di atas.

Migrasi: Laravel di `database/migrations/{Y_m_d_His}_{nama}.php`; Doctrine di
`migrations/Version{timestamp}.php`. High-water mark = timestamp tertinggi.

## Layer taxonomy

Urutan eksekusi kode dalam satu brief:
**Migration & Model → Repository → Service → Request & Controller → Wiring rute → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Migration | `{timestamp}_{nama}.php` | `database/migrations/`, `migrations/` |
| Model/Entity | `<Nama>.php` | `app/Models/`, `src/Entity/` |
| Repository | `<Nama>Repository.php` | `app/Repositories/`, `src/Repository/` |
| Service | `<Nama>Service.php` | `app/Services/`, `src/Service/` |
| Controller | `<Nama>Controller.php` | `app/Http/Controllers/`, `src/Controller/` |
| Request/DTO | `<Nama>Request.php`, `<Nama>Resource.php` | `app/Http/Requests/`, `app/Http/Resources/` |
| Wiring rute | `routes/api.php` (Laravel), `config/routes.yaml` atau atribut (Symfony) | `routes/`, `config/` |
| Test | `<Nama>Test.php` | `tests/` |

Lima jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **Perubahan skema selalu lewat berkas migrasi baru.** Mengedit migrasi yang sudah dijalankan
   membuat basis data lingkungan lain menyimpang tanpa jejak.
2. **`Model::create($request->all())` dilarang.** Mass assignment lolos ke kolom mana pun yang tidak
   dilindungi `$fillable`; masukkan field secara eksplisit dari objek request tervalidasi.
3. **Relasi dimuat lewat `with()` bila akan dipakai.** Pemuatan lazy di dalam perulangan menerbitkan
   satu query per elemen, dan bentuknya tidak terlihat di kode karena akses relasinya menyerupai
   akses properti biasa.
4. **Sumber tipe adalah kelas request tervalidasi, bukan array asosiatif.** Array yang mengalir dari
   controller ke service menghilangkan seluruh jaminan bentuk data.
5. **Model tidak dikembalikan langsung sebagai respons.** Serialisasi model membocorkan kolom
   internal dan memicu pemuatan relasi tak terduga; pakai lapisan resource/transformer.

`composer.json` dan `composer.lock` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Deklarasi kelas/interface/enum | `Glob` `**/<Nama>.php`; bila >1, `Grep -n "(class\|interface\|enum) <Nama>\b"` |
| Pemakai simbol | `Grep -n "<Simbol>"` di `source_root`, saring baris `use App\\...;` |
| Pemanggil method | `Grep -n "->{0,1}<method>\("`, telusuri tipe receiver via type hint constructor |
| Implementasi / turunan | `Grep -n "implements <Interface>\|extends <Base>"` |
| Titik masuk HTTP | Laravel: `Glob` `routes/*.php` → `Grep -n "Route::(get\|post\|put\|patch\|delete)"`; Symfony: `Grep -n "#\[Route\("` |
| Rantai Controller→Service→Repository | `Read` controller, catat type hint constructor → `Glob` `**/<Nama>Service.php` → `Read` method → `Glob` `**/<Nama>Repository.php` |
| Akses penyimpanan | `Grep -n "DB::\|::query()\|->where(\|createQueryBuilder\|getRepository("` |
| Batas transaksi | `Grep -n "DB::transaction\|beginTransaction\|->flush()"` |
| Antrean / Scheduler | `"implements ShouldQueue\|dispatch(\|MessageHandler"` / `"->schedule(\|#\[AsCron\|Kernel::schedule"` |
| Middleware / Auth | Laravel: `"->middleware(\|Gate::\|->can("`; Symfony: `"#\[IsGranted\|security.yaml"` |
| Validasi | Laravel: `"extends FormRequest\|->validate(\|rules()"`; Symfony: `"#\[Assert\\\\"` |
| Config & schema | `Glob` `**/{.env.example,config/*.php,config/packages/*.yaml}`; kode: `Grep -n "config(\|env(\|getParameter("` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35` — cukup menangkap atribut,
signature, dan properti hasil injeksi constructor.

## Audit checklist

#### `security`

- **Rute terdaftar di luar grup yang memasang middleware autentikasi.** Rute yang ditambahkan setelah blok grup ditutup tidak mewarisinya.
- **Identitas dibaca dari input permintaan, bukan dari pengguna terautentikasi.** `user_id` kiriman klien membuat impersonasi trivial.
- **Mass assignment.** `create($request->all())` atau `$fillable` yang memuat kolom sensitif seperti `role` dan `is_admin`.
- **SQL mentah dirakit lewat interpolasi string.** `DB::raw("... $input")` dan `whereRaw` tanpa binding melewati parameterisasi.
- **`APP_DEBUG=true` di lingkungan produksi.** Stack trace, isi variabel lingkungan, dan struktur query ikut keluar ke respons.
- **Model dikembalikan langsung sebagai respons**, membawa kolom seperti `password` dan `remember_token`.
- **Berkas unggahan disimpan tanpa validasi tipe dan ukuran**, atau disimpan di direktori yang dapat dieksekusi web server.

#### `transaction`

- **Operasi lintas-tabel tanpa `DB::transaction`.** Kegagalan di operasi kedua meninggalkan data separuh.
- **Exception ditangkap di dalam blok transaksi tanpa rethrow.** Blok dianggap sukses dan tetap commit meski operasinya gagal.
- **Job dikirim ke antrean sebelum transaksi commit.** Worker mengambil job lebih cepat daripada commit dan gagal menemukan datanya — gejalanya intermiten dan sulit direproduksi lokal.
- **Baca lalu tulis tanpa `lockForUpdate` atau kolom versi.** Dua permintaan paralel saling menimpa pada mutasi saldo atau stok.
- **Transaksi bersarang tanpa memperhatikan savepoint.** Rollback terdalam tidak membatalkan operasi di lapisan luar seperti yang diasumsikan.

#### `data`

- **`float` untuk nominal uang.** Wajib integer unit terkecil atau tipe desimal berpresisi.
- **Perbandingan longgar (`==`) pada nilai yang berasal dari input.** Aturan koersi PHP membuat perbandingan menghasilkan benar untuk nilai yang berbeda.
- **Validasi hanya di controller.** Job antrean, perintah konsol, dan importir yang menulis tabel sama melewati aturan yang sama.
- **Cast tipe kolom tidak dideklarasikan pada model.** Nilai boolean dan tanggal kembali sebagai string sehingga percabangan di lapisan atas salah.
- **Zona waktu campur antara `config` aplikasi, koneksi DB, dan kolom.** Perbandingan rentang salah di batas hari.
- **`enum` diperluas tanpa memperbarui percabangan yang memetakannya.** Nilai baru jatuh ke cabang default tanpa peringatan.

#### `persistence`

- **N+1 query.** Relasi diakses di dalam perulangan tanpa `with()` — bentuknya tidak terlihat karena menyerupai akses properti biasa.
- **`all()` atau `get()` tanpa paginasi** pada tabel yang tumbuh; seluruh tabel masuk memori proses.
- **`select *` di jalur yang hanya butuh sebagian kolom**, termasuk kolom besar.
- **`first()` yang mengembalikan `null` tidak dibedakan dari kegagalan query**, sehingga status HTTP-nya salah.
- **Chunking tidak dipakai pada perintah pemrosesan massal.** Batas memori PHP tercapai di tengah jalan dan pekerjaan berhenti separuh.

#### `concurrency`

- **Job antrean tanpa idempotensi.** Percobaan ulang memproses pesan yang sama dua kali.
- **Job tanpa batas percobaan atau antrean gagal.** Pekerjaan gagal berputar tanpa henti.
- **Scheduler multi-instance tanpa penguncian.** Setiap replika menjalankan tugas terjadwal yang sama bersamaan.
- **Driver antrean `sync` di lingkungan yang mengasumsikan pemrosesan asinkron.** Job berjalan di dalam siklus permintaan sehingga kegagalannya ikut menggagalkan permintaan.
- **Panggilan keluar tanpa timeout.** Klien HTTP menahan worker FPM sampai batas waktu server.
- **Properti statis dipakai sebagai cache lintas permintaan.** Aman di PHP-FPM karena proses mati tiap permintaan, tetapi bocor antar-permintaan pada runtime persisten seperti Octane, Swoole, atau RoadRunner.
- **State bergantung pada urutan job.** Dua job yang saling mendahului menghasilkan hasil akhir berbeda.

#### `architecture`

- **Logika bisnis di controller.** Percabangan aturan ditulis bersama pengambilan input dan penentuan respons.
- **Query dibangun langsung di controller**, melewati repository maupun service.
- **Facade dipanggil dari lapisan domain**, menyulitkan pengujian dan menyembunyikan dependensi nyata.
- **Array asosiatif dipakai sebagai kontrak antar-layer**, tanpa tipe maupun jaminan bentuk.
- **Model dipakai sebagai tipe respons di batas layer.**
- **Kelas service tanpa deklarasi tipe pada parameter dan nilai kembalian**, membuang pemeriksaan statis yang tersedia.

## API surface

Dua bentuk deklarasi; tentukan lebih dulu mana yang dipakai repo.

- **Laravel**: sumber kebenarannya `routes/api.php`. Method dan path dari
  `Route::post('/products', [ProductController::class, 'store'])`; prefix dari
  `Route::prefix('v1')->group(...)`, digabung dari luar ke dalam. Parameter path memakai `{id}`.
  Otorisasi dari `->middleware('auth:sanctum')` dan `->can(...)` pada rute atau grupnya, ditambah
  otorisasi di `FormRequest::authorize()`. Validasi dan bentuk request dari `rules()` pada
  `FormRequest`; bentuk respons dari kelas `Resource`, bukan dari model. Verifikasi cepat seluruh
  permukaan: `php artisan route:list`.
- **Symfony**: atribut `#[Route('/products/{id}', methods: ['GET'])]` pada method controller,
  ditambah prefix dari `#[Route]` di level kelas dan konfigurasi impor rute. Otorisasi dari
  `#[IsGranted]` dan aturan `access_control` di `security.yaml`. Validasi dari atribut `#[Assert\...]`
  pada DTO. Verifikasi cepat: `php bin/console debug:router`.

Berlaku untuk keduanya: status sukses default `200` kecuali ditulis eksplisit pada objek respons.
Bentuk error berasal dari exception handler terpusat — pada Laravel `bootstrap/app.php` atau
`Handler::render`, pada Symfony event listener `kernel.exception`.

## Failure signatures

- **Stack trace PHP.** Dibaca dari **atas**: frame pertama adalah titik lempar. Frame paling
  informatif adalah frame pertama di bawah `source_root` dan bukan `vendor/`. Rantai
  `Next ...Exception` menunjukkan pembungkusan; akar sebenarnya ada di entri terakhir.
- **`Allowed memory size exhausted`** — lazimnya query tanpa paginasi atau pemrosesan massal tanpa
  chunking. Nomor barisnya menunjuk tempat memori habis, bukan tempat data berlebih itu diambil.
- **`Maximum execution time exceeded`** — batas waktu FPM; cari panggilan keluar tanpa timeout atau
  query lambat, bukan sekadar menaikkan batasnya.
- **`SQLSTATE[23000]` (integrity constraint)** — pelanggaran unique atau foreign key. Pesannya
  menyebut nama constraint; itu penunjuk kolom yang paling cepat.
- **`SQLSTATE[42S22]` / kolom tidak dikenal** — migrasi belum dijalankan di lingkungan itu, atau
  migrasi lama diedit sehingga skema menyimpang.
- **`Target class [...] does not exist`** — binding container tidak terdaftar atau autoload belum
  diperbarui; jalankan `composer dump-autoload` sebelum menduga kesalahan lain.
- **Job gagal menemukan data yang baru dibuat** — job dikirim sebelum transaksi commit; gejalanya
  intermiten dan hampir tidak pernah muncul dengan driver antrean `sync`.
- **Test hijau sendiri tapi merah dalam satu run** — state bersama antar-test: basis data tidak
  di-refresh, cache konfigurasi basi, atau properti statis yang bertahan antar-test.
