# Stack adapter — `rust`

Rust dengan framework HTTP asinkron. Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `Cargo.toml` di root, atau anggota `[workspace] members` satu tingkat.

- **Penanda wajib**: minimal satu framework server di `[dependencies]` —
  `axum`, `actix-web`, `rocket`, `warp`, `poem`, `salvo`. Crate tanpa penanda ini adalah pustaka atau
  CLI, bukan stack backend ini.
- **Nama project**: `[package] name`; pada workspace, nama crate yang memuat entrypoint server.
- **Versi bahasa**: `[package] rust-version`, `rust-toolchain.toml`, atau `edition`.
- **Entrypoint**: `grep -rn "async fn main" --include=*.rs .` — lazimnya `src/main.rs` atau
  `src/bin/<nama>.rs`. Nama crate = `root_namespace`; `src/` = `source_root`.
- **Pemutus workspace**: bila `[workspace] members` memuat lebih dari satu crate biner, yang
  mendaftarkan `Router`/`App` adalah entrypoint API; sisanya dicatat di `## Surface map` profil.
- **Runtime asinkron**: `tokio` hampir selalu hadir; catat fitur yang diaktifkan (`full`,
  `rt-multi-thread`) karena menentukan apakah kerja blocking punya thread pool tersendiri.

**Penanda gaya arsitektur** (mengisi `architecture:` profil):

1. Batas crate: `[workspace] members` yang memisahkan `domain`/`core`, `application`/`use-case`, dan
   `infrastructure`/`adapters` adalah penanda `hexagonal` terkuat — batasnya ditegakkan compiler.
   Tanpa workspace, periksa modul: `find src -maxdepth 2 -type d` mencari `domain/`, `application/`,
   `ports/`, `adapters/`, `infrastructure/`, atau pasangan `inbound`/`outbound`.
2. Letak trait: `grep -rn "pub trait" <core-dir>` — pada `hexagonal`, kontrak penyimpanan dan klien
   eksternal berupa `trait` di inti; pada `layered`, `repository.rs` langsung memegang `PgPool`.
3. Kebersihan inti — pemutus terkuat. Pada workspace: baca `[dependencies]` crate inti; kehadiran
   `sqlx`, `diesel`, `axum`, `actix-web`, atau `reqwest` di sana berarti `layered`. Tanpa workspace:
   `grep -rn "use sqlx\|use axum\|use diesel\|use reqwest" <core-dir>` — nol hit → `hexagonal`.

Butir 3 mengalahkan butir 1: modul bernama `domain/` yang meng-`use sqlx` adalah `layered` berkostum
hexagonal. Jika sebagian modul bersih dan sebagian tidak → `hybrid`, sebutkan modul mana yang mana
di `## Module structure` profil.

Dependensi penanda per kelompok:

| Kelompok | Crate |
|---|---|
| DB & pool | `sqlx`, `diesel`, `sea-orm`, `tokio-postgres`, `deadpool`, `bb8` |
| Migration | `sqlx-cli`, `diesel_migrations`, `refinery`, `sea-orm-migration` |
| Messaging | `lapin`, `rdkafka`, `async-nats` |
| Cache | `redis`, `moka`, `cached` |
| Serialisasi & validasi | `serde`, `serde_json`, `validator`, `garde` |
| Auth | `jsonwebtoken`, `argon2`, `tower-http` (middleware), `axum-extra` |
| Observability | `tracing`, `tracing-subscriber`, `metrics`, `opentelemetry` |

Konfigurasi per environment: `config/*.toml`, `.env` (`dotenvy`), atau struct `serde` yang dibaca
dari variabel lingkungan. Setelan yang mengubah semantik runtime: `max_connections` pada pool,
`acquire_timeout`, jumlah worker Tokio, dan profil `[profile.release]` yang memengaruhi overflow check.

Penanda zona waktu runtime: `TZ` di `Dockerfile`, dan pilihan tipe waktu — `chrono::DateTime<Utc>`
atau `time::OffsetDateTime` versus tipe naif tanpa zona.

## Commands

| Perintah | Nilai |
|---|---|
| build | `cargo build` |
| typecheck | `cargo check --all-targets` |
| typecheck-scoped | `cargo check -p <crate>` |
| typecheck-per-brief | `ya` — inkremental, biayanya mendekati nol |
| lint | `cargo clippy --all-targets -- -D warnings` |
| test | `cargo test` |
| test-single | `cargo test <nama_test> -- --exact` |
| migration-status | `sqlx migrate info`, `diesel migration list`, atau `sea-orm-cli migrate status`; `refinery`: `tidak berlaku` (tanpa subperintah status) — `profile` menjalankannya hanya sesudah izin user |
| migration-apply | `sqlx migrate run`, `diesel migration run`, `sea-orm-cli migrate up`, atau `refinery migrate` — **dicatat untuk manusia, tidak pernah dijalankan plugin** |

Skrip di `Makefile`, `Justfile`, atau alias `cargo` di `.cargo/config.toml` menang atas perintah di atas.

Migrasi: `sqlx` di `migrations/{timestamp}_{nama}.sql`; `diesel` di
`migrations/{timestamp}_{nama}/{up,down}.sql`. High-water mark = timestamp tertinggi.

> `sqlx` dengan makro `query!` memvalidasi SQL saat kompilasi terhadap skema nyata. Karena itu di
> repo semacam ini `cargo check` **ikut gagal** bila migrasi belum dijalankan atau `SQLX_OFFLINE`
> tidak disiapkan — kegagalan build bisa berarti masalah skema, bukan masalah kode.
>
> Pakai `SQLX_OFFLINE=true` bila `.sqlx/` ada; dilarang menjalankan migrasi agar `cargo check` hijau.

## Layer taxonomy

Pilih sub-bagian sesuai `architecture:` profil. Lima jebakan di bawah tiap gaya berlaku hanya untuk
gaya itu; jebakan yang tidak bergantung gaya ada di keduanya.

### Gaya `layered`

Urutan eksekusi kode dalam satu brief:
**Migration & Model → Repository → Service → DTO & Handler → Wiring Router → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Model | `model.rs` — struct ber-`derive(FromRow)` atau skema Diesel | `src/<domain>/`, `src/schema.rs` |
| Repository | `repository.rs` | `src/<domain>/` |
| Service | `service.rs` | `src/<domain>/` |
| Handler | `handler.rs` | `src/<domain>/` |
| DTO | `dto.rs` — struct ber-`derive(Serialize, Deserialize)` | `src/<domain>/` |
| Error | `error.rs` — enum error domain + implementasi `IntoResponse` | `src/<domain>/`, `src/error.rs` |
| Wiring | pendaftaran rute dan `AppState` | `src/main.rs`, `src/routes.rs` |
| Test | `#[cfg(test)] mod tests` in-file, dan `tests/` untuk integrasi | sama dengan kode, `tests/` |

Lima jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **`.unwrap()` dan `.expect()` dilarang di jalur permintaan.** Keduanya memanggil `panic!`; di
   handler ini berarti koneksi diputus tanpa respons yang berarti. Pakai `?` dengan tipe error yang
   mengimplementasikan `IntoResponse`.
2. **Tipe error domain punya satu rumah.** Setiap varian dipetakan eksplisit ke status HTTP di satu
   implementasi `IntoResponse`; pemetaan ad-hoc di tiap handler akan menyimpang.
3. **Kerja blocking tidak dijalankan di dalam task async.** Operasi CPU berat, I/O berkas sinkron,
   dan panggilan pustaka blocking dibungkus `tokio::task::spawn_blocking`; tanpa itu ia menahan
   worker thread dan menghentikan seluruh permintaan lain di thread yang sama.
4. **`MutexGuard` tidak melewati titik `.await`.** Menahan lock lintas await bisa menyebabkan
   deadlock; untuk state bersama di jalur async gunakan lock async atau perpendek cakupan lock
   sebelum `.await`.
5. **`AppState` dibagi lewat `Arc`, bukan diklon per permintaan.** Pool koneksi dan klien HTTP dibuat
   sekali saat startup; membuatnya di dalam handler membuka pool baru tiap permintaan.

### Gaya `hexagonal`

Urutan eksekusi kode dalam satu brief:
**Entitas domain → Port (`trait` di inti) → Use case → Adapter driven → Adapter driving → Wiring biner → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Entitas & aturan domain | `<entitas>.rs`, tanpa `derive(Serialize)` maupun `derive(FromRow)` | crate `domain/`, `src/domain/` |
| Port | `ports.rs`, `repository.rs` — hanya `trait` | crate `domain/` atau `application/` |
| Use case | `<verba>_<entitas>.rs`, struct generik atau ber-`Arc<dyn Port>` | crate `application/`, `src/application/` |
| Adapter driven | `persistence/<entitas>_repository.rs`, `http_client.rs` | crate `infrastructure/`, `src/adapters/` |
| Adapter driving | `routes.rs`, `handler.rs`, `consumer.rs` | crate `api/`, `src/adapters/http/` |
| DTO | struct ber-`derive(Serialize, Deserialize)` milik adapter driving | sama dengan adapter |
| Error | enum error domain di inti; `IntoResponse` **hanya** di adapter driving | inti + `src/adapters/http/error.rs` |
| Wiring | `Arc<dyn Port>` dirakit sekali ke `AppState` | crate biner, `src/main.rs` |
| Test | use case diuji dengan fake port in-memory, tanpa DB | `#[cfg(test)]` in-file, `tests/` |

Lima jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **Trait port hidup di crate inti.** Menaruhnya di crate infrastruktur memaksa `domain` bergantung
   pada `infrastructure`; pada workspace ini bukan sekadar bau desain — cargo menolak siklus dependensi.
2. **Tipe infrastruktur dilarang muncul di signature trait.** `PgPool`, `sqlx::Error`,
   `&mut Transaction<'_, Postgres>`, atau `axum::Json` pada port menarik crate infrastruktur ke
   `[dependencies]` inti dan membatalkan alasan memakai gaya ini.
3. **Port yang dipakai sebagai `Arc<dyn Port>` wajib object-safe.** `async fn` dalam trait perlu
   `#[async_trait]`; trait dengan method generik atau `impl Future` tidak bisa di-`dyn`, dan wiring
   gagal kompilasi setelah seluruh adapter selesai ditulis.
4. **Adapter menerjemahkan error driver ke error domain.** `sqlx::Error::RowNotFound` yang
   diteruskan mentah memaksa use case menangani error milik teknologi yang seharusnya tak dikenalnya.
5. **`IntoResponse` dan `StatusCode` milik adapter driving.** Mengimplementasikannya pada error
   domain menaruh `axum` di `[dependencies]` crate inti — kebocoran paling sering di stack ini.

Transaksi lintas port memakai port tersendiri (`UnitOfWork`), karena `&mut Transaction` beserta
lifetime-nya tidak bisa melewati batas port tanpa membocorkan tipe `sqlx`.

`Cargo.toml` dan `Cargo.lock` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Deklarasi tipe | `Grep -n "(pub )?(struct\|enum\|trait) <Nama>\b"` di `source_root` |
| Pemakai simbol | `Grep -n "<Simbol>"`, saring baris `use ` di kepala berkas |
| Pemanggil fungsi/method | `Grep -n "\.<method>\(\|<fungsi>\("`, telusuri tipe receiver via deklarasi `let` |
| Implementasi trait | `Grep -n "impl (\w+ )?<Trait> for\|impl <Tipe>"` |
| Titik masuk HTTP | `Glob` `**/{routes,main}.rs` → `Grep -n "\.route(\|get(\|post(\|#\[get\|#\[post"` |
| Rantai Handler→Service→Repository | `Read` handler, catat field `State`/`Extension` → `Grep -n "impl <Service>"` → `Read` method → `Grep -n "impl <Repo>"` |
| Akses penyimpanan | `Grep -n "sqlx::query\|query!\|query_as\|\.fetch_(one\|all\|optional)\|diesel::"` |
| Batas transaksi | `Grep -n "\.begin()\|&mut \*tx\|transaction("` |
| Pemetaan error → status | `Grep -n "impl IntoResponse\|StatusCode::"` |
| Messaging / Scheduler | `"basic_consume\|StreamConsumer\|subscribe("` / `"tokio::spawn\|interval(\|cron"` |
| Middleware / Auth | `Grep -n "layer(\|ServiceBuilder\|FromRequestParts\|middleware::from_fn"` |
| Config & schema | `Glob` `**/{config*.toml,.env.example}`; kode: `Grep -n "env::var\|Config::"`; migrasi `**/migrations/**` |
| Deklarasi port (hexagonal) | `Grep -n "pub trait \w+(Repository\|Port\|Gateway\|Publisher)"` di crate/modul inti |
| Adapter pengimplementasi port (hexagonal) | `Grep -n "impl (\w+ )?<Trait> for"` — hasilnya adalah seluruh adapter yang terikat kontrak itu |
| Arah dependensi inti (hexagonal) | `Read` `[dependencies]` `Cargo.toml` crate inti; tanpa workspace: `Grep -rn "use (sqlx\|axum\|diesel\|reqwest\|actix)" <core-dir>` |
| Wiring port → adapter (hexagonal) | `Grep -n "Arc::new(\|Arc<dyn "` di `src/main.rs` dan berkas `AppState` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35` — cukup menangkap atribut,
signature generik, dan bound `where` di kepala fungsi.

## Audit checklist

#### `security`

- **Rute didaftarkan di luar `Router` yang memasang layer autentikasi.** Layer di Axum berlaku pada router tempat ia dipasang; rute yang digabung setelahnya tidak mewarisinya.
- **Identitas dibaca dari body atau query, bukan dari extractor hasil verifikasi token.**
- **SQL dirakit lewat `format!`.** Melewati parameterisasi `sqlx`; `query!` yang benar memakai binding `$1`.
- **Struct model di-`Deserialize` langsung dari body.** Field seperti `role` ikut ter-set dari input; pakai DTO terpisah.
- **Password di-hash dengan fungsi hash cepat.** Gunakan `argon2` atau `bcrypt`, bukan SHA keluarga.
- **Error internal ikut terserialisasi ke respons.** Pesan `sqlx::Error` membocorkan nama tabel dan struktur query.
- **Secret ter-log lewat `derive(Debug)`.** Struct konfigurasi yang di-`tracing::info!` membawa kredensial; tandai field-nya dengan tipe pembungkus yang menyembunyikan isi.

#### `transaction`

- **Pool dipakai di dalam blok transaksi.** Query yang mengambil koneksi dari pool alih-alih memakai `&mut *tx` berjalan di koneksi lain dan tidak ikut ter-rollback.
- **Transaksi di-drop tanpa `commit()`.** `sqlx` melakukan rollback saat drop — perilaku ini benar, tapi jalur sukses yang lupa `commit()` gagal diam-diam tanpa error.
- **Transaksi tidak diteruskan ke lapisan repository.** Setiap repository membuka transaksinya sendiri, sehingga dua operasi yang seharusnya atomik jadi dua transaksi terpisah.
- **Publish pesan sebelum `commit()`.** Consumer memproses data yang belum commit.
- **Baca lalu tulis tanpa `SELECT ... FOR UPDATE` atau kolom versi.** Dua permintaan paralel saling menimpa.

#### `data`

- **`f64` untuk nominal uang.** Wajib integer unit terkecil atau tipe desimal (`rust_decimal`).
- **Aritmetika integer memakai operator polos.** Overflow panik di build debug tapi **membungkus diam-diam** di build release, sehingga bug hanya muncul di produksi; pakai `checked_*` atau `saturating_*` pada nilai yang berasal dari input.
- **Tipe waktu naif dipakai untuk momen lintas zona.** `NaiveDateTime` tidak membawa offset; simpan `DateTime<Utc>`.
- **Validasi hanya di handler.** Consumer, scheduler, dan importir yang menulis tabel sama melewati aturan yang sama.
- **`#[serde(default)]` menyembunyikan field wajib yang absen.** Nilai default lolos sebagai data valid.
- **`match` atas enum memakai `_ =>` sebagai penutup.** Menghapus jaminan exhaustiveness: varian baru lolos diam-diam alih-alih memicu error kompilasi.

#### `persistence`

- **N+1 query.** Relasi diambil di dalam loop alih-alih satu query dengan `WHERE id = ANY($1)`.
- **`fetch_all` tanpa `LIMIT` pada tabel yang tumbuh.** Seluruh tabel masuk memori proses.
- **`fetch_one` dipakai saat baris mungkin tidak ada.** Menghasilkan `RowNotFound` sebagai error, bukan `None`; gunakan `fetch_optional` agar "tidak ditemukan" bisa dibedakan dari kegagalan query.
- **Pool memakai `max_connections` default.** Tidak selaras dengan batas koneksi DB dan jumlah replika.
- **`query!` diganti `query` string dinamis tanpa alasan.** Membuang verifikasi SQL saat kompilasi yang jadi keunggulan utama `sqlx`.

#### `concurrency`

- **Kerja blocking di dalam task async.** Menahan worker thread Tokio dan menghentikan permintaan lain di thread yang sama.
- **`MutexGuard` ditahan melewati `.await`.** Berisiko deadlock; lock sinkron tidak boleh hidup lintas titik suspensi.
- **`tokio::spawn` tanpa penanganan `JoinHandle`.** Panic di dalam task hilang tanpa jejak dan pekerjaannya diam-diam tidak selesai.
- **Task latar tanpa jalur pembatalan.** Tidak menerima token pembatalan, sehingga shutdown menggantung.
- **Consumer tanpa idempotensi.** Pesan yang di-`ack` setelah pemrosesan akan dikirim ulang bila task-nya panik di tengah jalan.
- **Klien HTTP keluar tanpa timeout.** `reqwest::Client` default tidak membatasi durasi permintaan.
- **Task terjadwal dijalankan lewat `tokio::spawn` di setiap instance.** Tanpa penguncian terdistribusi, seluruh replika menjalankannya bersamaan.

#### `architecture`

- **Logika bisnis di handler.** Percabangan aturan ditulis bersama ekstraksi dan pemetaan status.
- **Repository dipanggil langsung dari handler**, melewati service.
- **Tipe error tunggal raksasa untuk seluruh aplikasi.** Setiap modul memaksa varian ke dalamnya sehingga pemetaan status jadi kabur.
- **`Box<dyn Error>` di batas layer publik.** Menghapus kemampuan pemanggil membedakan jenis kegagalan.
- **Struct model dipakai sebagai tipe respons**, sehingga perubahan skema langsung mengubah kontrak API.
- **`pub` dipakai berlebihan pada item internal modul**, membocorkan detail implementasi lintas modul.

Empat butir berikut **hanya berlaku bila `architecture: hexagonal`**; pada repo `layered` keempatnya bukan temuan:

- **Crate atau modul inti bergantung pada infrastruktur.** `sqlx`, `axum`, atau `reqwest` di `[dependencies]` crate inti — atau `use crate::adapters::` di dalamnya — membalik arah dependensi; pada workspace ini berujung siklus yang ditolak cargo begitu adapter ikut memakai inti.
- **Trait port dideklarasikan bersama implementornya.** Inti harus mengimpor crate adapter untuk memakai kontraknya sendiri, dan port terkunci pada satu implementasi.
- **Tipe `sqlx`/`axum` muncul di signature port.** `PgPool`, `sqlx::Error`, `Transaction`, atau `Json<T>` pada trait inti membuat fake port di test menarik driver aslinya.
- **`impl IntoResponse` pada error domain.** Menempatkan pemetaan status HTTP di inti menyeret `axum` ke crate domain; pemetaan itu milik adapter driving.

## API surface

Dua bentuk deklarasi; tentukan lebih dulu mana yang dipakai repo.

- **Axum/Warp/Poem (imperatif)**: sumber kebenarannya berkas wiring `Router`. Path dan method dari
  `.route("/products/:id", get(handler).post(other))`. Prefix dari `Router::nest("/api/v1", sub)`,
  digabung dari luar ke dalam. Parameter path memakai `:name`.
- **Actix-web/Rocket (atribut)**: `#[get("/products/{id}")]` pada fungsi handler, digabung dengan
  prefix dari `web::scope("/api/v1")` atau `rocket::routes![]` yang di-`mount` pada suatu base path.

Berlaku untuk keduanya:

- **Parameter dan body** dibaca dari tipe extractor pada signature handler: `Path<T>`, `Query<T>`,
  `Json<T>`. Signature handler adalah kontraknya — tidak ada deklarasi terpisah yang perlu dicocokkan.
- **Response & status**: tipe kembalian handler. `Json<T>` menghasilkan `200`; status lain berasal
  dari `(StatusCode::CREATED, Json(t))` atau implementasi `IntoResponse` pada tipe domain.
- **Otorisasi per endpoint**: layer/middleware yang dipasang pada router tempat rute itu terdaftar,
  atau extractor yang memvalidasi klaim di signature handler. Periksa router mana yang memasangnya —
  cakupannya tidak otomatis menurun ke router yang digabung sesudahnya.
- **Bentuk error**: satu implementasi `IntoResponse` memetakan varian error ke status.
- **Pada `architecture: hexagonal`**: `Router` dan DTO hidup di adapter driving, dan `IntoResponse`
  diimplementasikan di sana atas error inti lewat tipe pembungkus. Petakan endpoint ke use case yang
  dipanggil handler — di situlah kontrak perilakunya berada, bukan di signature handler.

## Failure signatures

- **`thread 'tokio-runtime-worker' panicked at ...`** — panic di dalam handler. Frame paling
  informatif ada di bawah nama crate sendiri; jalankan ulang dengan `RUST_BACKTRACE=1` karena secara
  default jejaknya dipangkas. Penyebab terlazim adalah `.unwrap()` pada `Result` atau `Option`.
- **Kompilasi gagal di `query!` dengan pesan soal kolom atau tabel** — bukan kesalahan kode Rust,
  melainkan skema DB tidak selaras: migrasi belum dijalankan, atau `.sqlx/` offline data basi.
- **`error[E0499]` / `E0502` (borrow konflik)** — dua peminjaman aktif bersamaan; lazimnya pertanda
  cakupan lock atau transaksi terlalu lebar, bukan sekadar soal sintaks.
- **`error[E0308]` pada handler Axum** — signature handler tidak memenuhi trait `Handler`, biasanya
  karena urutan extractor salah (extractor yang mengonsumsi body wajib terakhir) atau tipe kembalian
  tidak mengimplementasikan `IntoResponse`.
- **`PoolTimedOut`** — pool habis; cari transaksi panjang, koneksi yang tidak dilepas, atau
  `max_connections` yang lebih kecil dari beban nyata.
- **`RowNotFound`** — `fetch_one` dipakai untuk baris opsional; seharusnya `fetch_optional`.
- **Permintaan menggantung tanpa error** — kerja blocking di task async, atau lock yang ditahan
  melewati `.await`.
- **Perilaku berbeda antara `cargo test` dan build release** — overflow integer yang panik di debug
  namun membungkus diam-diam di release.
