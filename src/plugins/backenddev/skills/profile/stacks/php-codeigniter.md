# Stack adapter — `php-codeigniter`

CodeIgniter 4 di atas PHP. Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap. Perintah dan
perilaku di bawah dibuktikan pada appstarter CodeIgniter 4.7.

## Detection

Manifest: `composer.json` di root atau satu tingkat submodule, bersama berkas `spark` di direktori yang sama.

- **Penanda wajib**: `codeigniter4/framework` di `require` (`grep -n '"codeigniter4/framework"' composer.json`)
  dan `test -f spark`. CodeIgniter 3 (tanpa paket ini, kode di `application/`) belum didukung.
- **Pemutus terhadap `php`**: penanda ini menang meski `symfony/*` atau `illuminate/*` hadir sebagai
  pustaka lepas — layer, CLI, dan jebakannya mengikuti CodeIgniter.
- **Nama project**: field `name` pada `composer.json`; bila masih `codeigniter4/appstarter`, nama direktori repo.
- **Versi**: `require.php`; versi framework dari `composer.lock` atau baris pertama keluaran `php spark`.
- **Entrypoint**: `public/index.php` (document root) dan CLI `spark`. `source_root` = `app/` dari
  `autoload.psr-4`; namespace modul tambahan terdaftar di `$psr4` `app/Config/Autoload.php`.
- **Mode routing**: `$autoRoute` (`app/Config/Routing.php`) dan `$autoRoutesImproved`
  (`app/Config/Feature.php`). Auto routing aktif menjadikan method controller permukaan HTTP di luar
  `Routes.php` — wajib dicatat di `## Invariants` profil beserta modenya (legacy/improved).
- **Lingkungan**: `CI_ENVIRONMENT` di `.env`; `development` menyalakan `display_errors`, `CI_DEBUG`, dan
  Debug Toolbar lewat `app/Config/Boot/<env>.php`.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| DB & ORM | `CodeIgniter\Model` + Query Builder bawaan; driver dari `DBDriver` (`MySQLi`, `Postgre`, `SQLite3`, `SQLSRV`, `OCI8`) |
| Auth | `codeigniter4/shield` — alias filter `session`, `tokens`, `hmac`, `jwt`, `chain`, `group`, `permission` |
| Antrean / Penjadwal | `codeigniter4/queue` / `codeigniter4/tasks` |
| Kualitas | `phpunit/phpunit`, `phpstan/phpstan` + `codeigniter/phpstan-codeigniter`, `codeigniter/coding-standard` |

Konfigurasi: properti `app/Config/*.php` ditimpa `.env` lewat kunci bertitik (`database.default.hostname`,
`app.baseURL`); kunci salah eja tidak memicu error dan nilai default kelas yang berlaku. Setelan yang
mengubah semantik runtime: `DBDebug` (`false` membuat query gagal mengembalikan `false`), `numberNative`
MySQLi (default `false`, angka kembali sebagai string), dan `Filters::$globals` (`csrf` dikomentari di
appstarter).

Penanda zona waktu runtime: `$appTimezone` di `app/Config/App.php` (`.env` `app.appTimezone`, default
`UTC`), `date.timezone` di `php.ini`, dan `TZ` di `Dockerfile`.

## Commands

| Perintah | CodeIgniter 4 |
|---|---|
| build | `composer install --no-dev --optimize-autoloader`; tambah `php spark optimize` bila pipeline deploy repo memakainya |
| typecheck | `vendor/bin/phpstan analyse` dengan `vendor/codeigniter/phpstan-codeigniter/extension.neon` di `includes` |
| typecheck-scoped | `vendor/bin/phpstan analyse <path>` |
| typecheck-per-brief | `tidak` — phpstan bukan compiler; appstarter bersih pun melaporkan puluhan error level 5 di `app/Views/errors/`, jadi vonisnya baseline-relatif |
| lint | `vendor/bin/php-cs-fixer fix --dry-run --diff` dengan `.php-cs-fixer.dist.php` berbasis `codeigniter/coding-standard` |
| test | `vendor/bin/phpunit` (appstarter: `composer test`) |
| test-single | `vendor/bin/phpunit --filter=<NamaTest>` |
| migration | `php spark migrate`; status per berkas `php spark migrate:status` |

Skrip `composer.json` bagian `scripts` dan `Makefile` repo menang atas perintah di atas. Tidak ada
`php spark test`; test basis data memakai grup koneksi `tests` di `app/Config/Database.php`.

Migrasi: `app/Database/Migrations/{Y-m-d-His}_{Nama}.php` dari `php spark make:migration <Nama>`.
High-water mark = prefix timestamp tertinggi. Seeder di `app/Database/Seeds/` (`php spark db:seed <Nama>`).

## Layer taxonomy

Urutan eksekusi kode dalam satu brief:
**Migration → Entity & Model → Library → Validation & Filter → Controller → Wiring rute → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Migration & Seeder | `{Y-m-d-His}_{Nama}.php`, `<Nama>Seeder.php` | `app/Database/Migrations/`, `app/Database/Seeds/` |
| Entity | `<Nama>.php` extends `CodeIgniter\Entity\Entity` | `app/Entities/` |
| Model | `<Nama>Model.php` extends `CodeIgniter\Model` | `app/Models/` |
| Library (logika bisnis) | `<Nama>.php`, `<Nama>Service.php` | `app/Libraries/`, `app/Services/` |
| Validation | rule group, atau `$validationRules` model | `app/Config/Validation.php`, `app/Models/` |
| Filter | `<Nama>.php` implements `FilterInterface` | `app/Filters/`; alias di `app/Config/Filters.php` |
| Controller | `<Nama>.php` extends `BaseController` atau `ResourceController` | `app/Controllers/`, `app/Controllers/Api/` |
| Wiring rute | `$routes->...` | `app/Config/Routes.php` |
| Test | `<Nama>Test.php` extends `CIUnitTestCase` | `tests/unit/`, `tests/database/`, `tests/feature/` |

Penamaan mengikuti pola repo: `make:model Product` menghasilkan `Product.php`, dengan `--suffix`
`ProductModel.php`. `Services` di CodeIgniter adalah service locator (`app/Config/Services.php`,
`service('nama')`), bukan lapisan logika bisnis. `Model` sudah berperan table gateway; lapisan
Repository hanya ditulis bila repo terbukti (`file:line`) memakainya.

Enam jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **Kolom baru wajib masuk `$allowedFields`.** Dengan `$protectFields = true` (default), field di luar
   daftar dibuang diam-diam; bila semuanya terbuang lahir `DataException: There is no data to insert.`
2. **Nilai kembali `insert()`, `update()`, dan `save()` wajib diperiksa.** Validasi model yang gagal
   mengembalikan `false`, bukan exception; pesannya ada di `$model->errors()`.
3. **Mutasi lewat `$model->builder()` atau `$db->table()` melewati model.** `$allowedFields`,
   `$validationRules`, timestamp, callback `$beforeInsert`, dan kondisi soft delete tidak berlaku.
4. **`transStart()` selalu dipasangkan dengan pemeriksaan `transComplete()`.** Query gagal di dalamnya
   tidak melempar exception kecuali `transException(true)`.
5. **Method controller yang bukan endpoint dideklarasikan `protected` atau `private`.** Pada auto
   routing, method `public` langsung dapat dipanggil dari URI.
6. **`countAllResults()` mereset builder secara default.** Memanggilnya sebelum `get()`/`findAll()` pada
   builder yang sama membuang seluruh kondisi; pakai `countAllResults(false)`.

`composer.json`, `composer.lock`, dan `app/Config/Boot/*.php` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Deklarasi kelas/interface/trait | `Glob` `app/**/<Nama>.php`; bila >1, `Grep -n "(class\|interface\|trait\|enum) <Nama>\b"` |
| Pemakai model/library | `Grep -n "<Nama>::class\|model('<Nama>'\|new <Nama>(\|service('<alias>')"` |
| Titik masuk HTTP | `Glob` `**/Config/Routes.php` → `Grep -n "\$routes->(get\|post\|put\|patch\|delete\|match\|add\|resource\|presenter\|group)\("`; bila auto routing aktif, method `public` (legacy) atau berprefiks verb seperti `getIndex` (improved) di `app/Controllers/` ikut jadi titik masuk |
| Rantai Controller→Library→Model | `Read` controller, catat `model(...)`, `service(...)`, `new ...` di method dan `initController()` → `Glob` `app/Libraries/**/<Nama>.php` → `Glob` `app/Models/<Nama>*.php` |
| Filter efektif per rute | `Grep -n "'filter' =>\|\$globals\|\$filters\|\$methods\|#\[Filter\(" app/Config/ app/Controllers/`; rantai final `php spark filter:check <verb> <uri>` |
| Akses penyimpanan | `Grep -n "->builder(\|->table(\|->query(\|->find(\|->findAll(\|->where(\|->insert(\|->update("` |
| Batas transaksi | `Grep -n "transStart\|transBegin\|transComplete\|transRollback\|transException"` |
| Validasi / Auth | `"->validate(\|validateData(\|\$validationRules\|skipValidation"` / `"auth()->\|user_id()\|->can(\|->inGroup("` |
| Antrean / Penjadwal | `"service('queue')->push(\|extends BaseJob"` / `app/Config/Tasks.php` → `"->command(\|->call(\|singleInstance("` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35`. Untuk temuan di Model, baca juga
blok properti di awal kelas (`$allowedFields`, `$returnType`, `$useSoftDeletes`, `$validationRules`) —
perilaku `insert` dan `find` ditentukan di sana.

## Audit checklist

#### `security`

- **Auto routing legacy aktif** (`$autoRoute = true`, `$autoRoutesImproved = false`). Seluruh method `public` controller dapat dipanggil lewat URI dan verb apa pun, tanpa filter yang hanya dipasang pada rute terdefinisi.
- **Field sensitif dibaca dengan `getVar()`.** Tanpa body JSON ia membaca `$_REQUEST`, sehingga query string dapat menggantikan nilai yang diasumsikan datang dari body POST.
- **`$model->insert($this->request->getPost())` pada model yang `$allowedFields`-nya memuat kolom otorisasi** (`role`, `is_admin`, `user_id`) atau `$protectFields = false`. Klien menulis kolom itu langsung.
- **Kondisi Query Builder dirakit dari string input** — `where("id = {$id}")`, argumen `$escape = false`, atau `$db->query()` berinterpolasi tanpa array binding `?`.
- **`CI_ENVIRONMENT = development` di server produksi.** Halaman error berisi stack trace dan Debug Toolbar (query, sesi, header) ikut terkirim ke klien.
- **Filter `csrf` tidak aktif di `$globals` pada aplikasi berautentikasi sesi** (Shield `session`). Appstarter mengomentarinya; form yang mengubah state terbuka untuk CSRF.

#### `transaction`

- **`transComplete()` tanpa pemeriksaan nilai kembali.** Query gagal di dalam `transStart()` hanya membalik blok; controller tetap merespons sukses padahal tidak ada yang tersimpan.
- **Exception tertangkap di antara `transBegin()` dan `transCommit()` tanpa `transRollback()`.** Transaksi manual tidak di-rollback otomatis; query berikutnya dalam permintaan itu ikut masuk transaksi yang tak pernah commit.
- **Baca lalu tulis saldo atau stok lewat `find()` + `update()`.** Query Builder tidak punya penguncian baris; pakai `SELECT ... FOR UPDATE` via `$db->query()` di dalam transaksi, atau update atomik `set('stok', 'stok - 1', false)`.

#### `data`

- **`numberNative` dibiarkan `false` pada MySQLi.** Kolom integer dan desimal kembali sebagai string: perbandingan ketat `=== 0` selalu gagal dan respons JSON membawa `"id":"5"`.
- **`skipValidation(true)` atau `$skipValidation = true` pada jalur tulis.** `$validationRules` model yang menjadi satu-satunya penjaga integritas dilewati tanpa jejak.
- **`is_unique[tabel.kolom]` tanpa pengecualian baris sendiri.** Memperbarui baris tanpa mengubah kolom itu gagal validasi, kecuali aturannya `is_unique[tabel.kolom,id,{id}]` dan `id` ikut di data yang divalidasi.

#### `persistence`

- **Query di dalam `foreach` hasil `findAll()`.** Model CodeIgniter tidak punya relasi eager-load, jadi N+1 muncul sebagai `find()` eksplisit per elemen; ganti dengan `whereIn()` atau join.
- **`findAll()` tanpa argumen `limit`** pada tabel yang tumbuh, alih-alih `paginate()` atau `chunk()`.
- **`DBDebug = false`.** Query gagal mengembalikan `false`; pemanggil yang langsung `->getResult()` jatuh ke fatal error jauh dari query penyebabnya.
- **Query lewat `builder()` pada model `$useSoftDeletes = true`.** Kondisi `deleted_at IS NULL` tidak ditambahkan; baris terhapus muncul lagi di daftar dan hitungan.

#### `concurrency`

- **Session `FileHandler` mengunci berkas sesi sepanjang permintaan.** Permintaan AJAX paralel dari pengguna yang sama berjalan serial sampai `session_write_close()` dipanggil.
- **Task `codeigniter4/tasks` tanpa `singleInstance()`** sementara cron `php spark tasks:run` hidup di lebih dari satu replika. Tugas yang sama berjalan ganda.

#### `architecture`

- **Instance bersama `model('X')` membawa kondisi builder yang belum dieksekusi.** `where()` dari satu pemanggil ikut ke query pemanggil lain dalam permintaan yang sama; pakai `model('X', false)` atau eksekusi di tempat.
- **`initController()` di-override tanpa `parent::initController()`.** `$this->request`, `$this->response`, dan `$this->logger` tidak terisi; endpoint gagal fatal pada akses pertama.

## API surface

- **Rute terdefinisi** di `app/Config/Routes.php` dan `**/Config/Routes.php` modul:
  `$routes->post('orders/(:num)/pay', 'Orders::pay/$1')`. Placeholder `(:num)`, `(:segment)`, `(:any)`,
  `(:alpha)`, `(:alphanum)`, `(:hash)` ditulis sebagai `{nama}` bertipe placeholder. Prefix
  `$routes->group('v1', [...], ...)` digabung dari luar ke dalam; opsi `namespace` grup mengubah kelas handler.
- **`$routes->resource('products')`** menerbitkan `GET products`, `GET products/new`, `GET products/(.*)`,
  `GET products/(.*)/edit`, `POST products`, dan `PUT`/`PATCH`/`DELETE products/(.*)`; opsi
  `only`/`except` memangkasnya, jadi baca opsi sebelum mendokumentasikan.
- **Auto routing** aktif: improved hanya method berprefiks verb (`getIndex` → `GET /<controller>/index`),
  legacy seluruh method publik pada verb apa pun.
- **Otorisasi**: opsi `'filter' => 'tokens'` atau `'permission:users.create'` pada rute atau grup,
  `Filters::$globals`/`$filters`/`$methods`, atribut `#[Filter]` pada controller, dan
  `auth()->user()->can()` di method.
- **Validasi & request**: `$this->validate($rules)`/`validateData()`, rule group
  `app/Config/Validation.php`, atau `$validationRules` model; body dari `getJSON()`, `getPost()`,
  `getVar()`, atau `getRawInput()`.
- **Status & respons**: `ResponseTrait`/`ResourceController` — `respond()` 200, `respondCreated()` 201,
  `respondDeleted()`/`respondUpdated()` 200, `respondNoContent()` 204, `failValidationErrors()` 400,
  `failUnauthorized()` 401, `failForbidden()` 403, `failNotFound()` 404. Tanpa trait:
  `$this->response->setStatusCode()->setJSON()`. Error tak tertangkap dibentuk handler dari
  `Config\Exceptions::handler()`.

Verifikasi cepat: `php spark routes` (kolom *Before Filters* memuat filter per rute), lalu
`php spark filter:check <verb> <uri>` untuk rantai filter efektif satu endpoint.

## Failure signatures

- **Log di `writable/logs/log-YYYY-MM-DD.log`, bukan stdout.** Entri: `CRITICAL - <waktu> --> <Kelas>: <pesan>`,
  `[Method: GET, Route: <uri>]`, `in APPPATH/... on line N.`, lalu frame bernomor dengan path
  `APPPATH/`, `SYSTEMPATH/`, `FCPATH/`. Frame paling informatif adalah frame `APPPATH/` pertama;
  exception terbungkus tercatat sebagai entri lanjutan `[Caused by] ...` — akar ada di sana.
- **HTTP 200 tetapi data tidak tersimpan, tanpa exception** — `transComplete()` bernilai `false` yang
  tidak diperiksa, atau `insert()` gagal validasi model; periksa `$model->errors()` dan `$db->error()`.
- **404 tanpa entri log** — `Config\Exceptions::$ignoreCodes` memuat `404`. `Can't find a route for
  '<verb>: <uri>'.` berarti tidak ada rute cocok (termasuk verb salah); `Controller or its method is not
  found` berarti rute cocok tetapi handler salah namespace atau method-nya tidak ada.
- **`There is no data to insert.`** — seluruh field terbuang oleh `$allowedFields`;
  **`Allowed fields must be specified for model`** — `$allowedFields` kosong.
- **`Duplicate entry '...' for key '...'`** (MySQLi) — pesan server diteruskan tanpa awalan `SQLSTATE`;
  nama key menunjuk unique index. `no such table` (SQLite3) atau `Table '...' doesn't exist` (MySQLi) —
  cek `php spark migrate:status`.
- **`Call to a member function getResult() on bool`** — `DBDebug = false`; akar ada di query sebelumnya.
- **`The action you requested is not allowed.`** (403) — token CSRF tidak cocok, termasuk permintaan
  paralel yang membawa token lama saat `$regenerate = true`.
- **`Cache unable to write to "..."`** atau **`Session: Configured save path "..." is not writable`** —
  izin `writable/` di server, bukan bug kode.
