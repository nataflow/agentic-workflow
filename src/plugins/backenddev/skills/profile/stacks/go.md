# Stack adapter — `go`

Go dengan framework HTTP/RPC. Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `go.mod` di root atau satu tingkat submodule.

- **Penanda wajib**: minimal satu framework server di `go.mod` —
  `gin-gonic/gin`, `gofiber/fiber`, `labstack/echo`, `go-chi/chi`, `gorilla/mux`, `grpc-go`.
  Modul Go tanpa satu pun penanda ini adalah pustaka atau CLI, bukan stack backend ini.
- **Nama project**: baris `module <path>` pada `go.mod`; nama pendeknya = segmen terakhir path itu.
- **Versi bahasa**: direktif `go 1.xx` pada `go.mod`; `toolchain` bila ada mengalahkannya.
- **Entrypoint**: `grep -rln "func main()" --include=*.go .` — lazimnya `cmd/<nama>/main.go`.
  Path modul di `go.mod` = `root_namespace`; direktori kode = `source_root` (lazim `internal/`).
- **Pemutus multi-binary**: bila `cmd/` memuat lebih dari satu `main.go`, yang mendaftarkan rute HTTP
  adalah entrypoint API; sisanya (worker, migrator) dicatat di `## Surface map` profil.

**Penanda gaya arsitektur** (mengisi `architecture:` profil):

1. Direktori: `find <source_root> -maxdepth 2 -type d`. Penanda `hexagonal` — `core/`, `domain/`,
   `app/`, `application/`, `usecase/`, `ports/`, `adapters/`, `infrastructure/`, dan pasangan
   `inbound`/`outbound` atau `driving`/`driven`. Penanda `layered` — domain berisi trio
   `handler.go` / `service.go` / `repository.go` berdampingan.
2. Letak interface: `grep -rn "interface {" <core-dir>`. Pada `hexagonal`, kontrak penyimpanan dan
   klien eksternal dideklarasikan di paket inti (konsumen); pada `layered` ia lazim absen atau
   dideklarasikan bersama implementasinya.
3. Kebersihan inti — pemutus terkuat:
   `grep -rn "database/sql\|jackc/pgx\|gorm.io\|gin-gonic\|labstack/echo\|go-chi/chi\|go-redis" <core-dir>`.
   Nol hit = inti bebas infrastruktur → `hexagonal`. Ada hit = `layered`.

Butir 3 mengalahkan butir 1: direktori bernama `domain/` yang mengimpor driver DB adalah `layered`
berkostum hexagonal. Jika sebagian modul bersih dan sebagian tidak → `hybrid`, dan sebutkan modul
mana yang mana di `## Module structure` profil.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| DB & driver | `lib/pq`, `jackc/pgx`, `go-sql-driver/mysql`, `mattn/go-sqlite3`, `mongo-driver` |
| Query & ORM | `sqlc`, `sqlx`, `gorm.io/gorm`, `ent`, `squirrel` |
| Migration | `golang-migrate/migrate`, `pressly/goose`, `atlas` |
| Messaging | `nats-io/nats.go`, `segmentio/kafka-go`, `IBM/sarama`, `rabbitmq/amqp091-go` |
| Cache | `redis/go-redis`, `patrickmn/go-cache`, `hashicorp/golang-lru` |
| Config & auth | `kelseyhightower/envconfig`, `spf13/viper`, `golang-jwt/jwt`, `casbin` |
| Observability | `uber-go/zap`, `rs/zerolog`, `prometheus/client_golang`, `otel` |

Konfigurasi per environment: `.env`, `.env.example`, `config/*.yaml`, atau struct `envconfig`/`viper`
di `internal/platform/config`. Setelan yang mengubah semantik runtime: `SetMaxOpenConns`,
`SetMaxIdleConns`, `SetConnMaxLifetime`, level isolasi pada `sql.TxOptions`, `GOMAXPROCS`.

Penanda zona waktu runtime: `time.Local = ...`, `os.Setenv("TZ", ...)`, `ENV TZ=` di `Dockerfile`,
dan pemakaian `time.Now()` vs `time.Now().UTC()` di lapisan penulisan data.

## Commands

| Perintah | Nilai |
|---|---|
| build | `go build ./...` |
| typecheck | `go vet ./...` |
| typecheck-scoped | `go build ./<paket>/...` |
| typecheck-per-brief | `ya` — inkremental, biayanya mendekati nol |
| lint | `golangci-lint run` bila `.golangci.yml` ada; jika tidak, `gofmt -l .` |
| test | `go test ./...` |
| test-single | `go test ./<paket> -run <NamaTest>` |
| migration | sesuai tool: `migrate -path <dir> -database $DATABASE_URL up`, atau `goose -dir <dir> up` |

Skrip di `Makefile` atau `Justfile` repo menang atas perintah generik di atas.

Migrasi: lazim di `db/migrations/` atau `migrations/`. `golang-migrate` memakai pasangan
`{n}_{deskripsi}.up.sql` / `.down.sql`; `goose` memakai `{timestamp}_{deskripsi}.sql` dengan penanda
`-- +goose Up`. High-water mark = penanda versi tertinggi yang benar-benar ada.

## Layer taxonomy

Pilih sub-bagian sesuai `architecture:` profil. Lima jebakan di bawah tiap gaya berlaku hanya untuk
gaya itu; jebakan yang tidak bergantung gaya ada di keduanya.

### Gaya `layered`

Urutan eksekusi kode dalam satu brief:
**Schema & Migration → Repository → Service → DTO & Handler → Wiring rute → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Schema | `schema.sql`, definisi tabel, atau struct model | `db/`, `internal/<domain>/model.go` |
| Repository | `repository.go`, atau berkas hasil generate | `internal/<domain>/` |
| Service | `service.go` | `internal/<domain>/` |
| Handler | `handler.go` | `internal/<domain>/` |
| DTO | `dto.go` — struct request/response ber-tag `json` | `internal/<domain>/` |
| Wiring rute | pendaftaran rute terpusat | `cmd/api/routes.go`, `internal/platform/http` |
| Test | `<berkas>_test.go` bersebelahan dengan kode yang diuji | sama dengan kode |

Lima jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **`context.Context` diteruskan sampai lapisan query.** Fungsi repository tanpa `ctx` membuat query
   tak bisa dibatalkan saat request putus, dan koneksi tetap tertahan sampai timeout DB.
2. **Setiap `error` dibungkus dengan `%w`, bukan `%v`.** `%v` memutus rantai `errors.Is`/`errors.As`
   sehingga penanganan error di lapisan atas diam-diam berhenti bekerja.
3. **`defer rows.Close()` dan `defer tx.Rollback()` dipasang tepat setelah objeknya lahir.**
   `Rollback` setelah `Commit` sukses adalah no-op yang aman; ketiadaannya membocorkan transaksi.
4. **Struct DTO dan struct domain tidak digabung.** Tag `json` pada struct domain membocorkan field
   internal ke response dan membuat perubahan skema langsung mengubah kontrak API.
5. **Goroutine punya jalur berhenti.** Setiap `go func()` menerima `ctx` atau channel penutup;
   goroutine yang menulis ke channel tanpa pembaca menggantung selama proses hidup.

### Gaya `hexagonal`

Urutan eksekusi kode dalam satu brief:
**Entitas domain → Port (interface di inti) → Use case → Adapter driven → Adapter driving → Wiring `cmd/` → Test**.

| Layer | Penamaan | Letak lazim |
|---|---|---|
| Entitas & aturan domain | `<entitas>.go`, tanpa tag `json` maupun tag ORM | `internal/core/domain/`, `internal/domain/` |
| Port | `ports.go`, `repository.go` berisi `interface` saja | `internal/core/port/`, `internal/ports/`, atau bersama use case-nya |
| Use case | `<verba>_<entitas>.go` atau `service.go` | `internal/core/service/`, `internal/app/`, `internal/usecase/` |
| Adapter driven | `postgres/<entitas>_repository.go`, `kafka/publisher.go` | `internal/adapters/<teknologi>/` |
| Adapter driving | `http/<entitas>_handler.go`, `grpc/`, `consumer/` | `internal/adapters/http/`, `internal/handler/` |
| DTO | struct ber-tag `json` milik adapter driving, bukan milik domain | sama dengan adapter yang memakainya |
| Wiring | konstruksi adapter dan injeksi port ke use case | `cmd/<nama>/main.go`, `internal/wire/` |
| Test | `<berkas>_test.go`; use case diuji dengan fake port, bukan DB | sama dengan kode |

Lima jebakan yang wajib dijaga saat menulis kode di layer ini:

1. **Port dideklarasikan di sisi konsumen.** Interface hidup di paket inti yang memakainya, bukan di
   paket adapter; menaruhnya di adapter membalik arah dependensi dan memaksa inti mengimpor infrastruktur.
2. **Tipe infrastruktur dilarang muncul di signature port.** `*sql.Tx`, `*gorm.DB`, `*gin.Context`,
   `pgx.Rows`, atau tipe DTO transport pada interface inti mengikat domain ke driver dan membuat
   fake port di test mustahil ditulis tanpa menarik driver itu.
3. **Adapter menerjemahkan error driver ke error domain.** `sql.ErrNoRows` atau error framework yang
   diteruskan mentah memaksa use case memeriksa error milik teknologi yang seharusnya tak dikenalnya.
4. **Transaksi lintas port adalah port tersendiri** (`UnitOfWork`/`TxManager` yang dideklarasikan di
   inti). Tanpa itu, atomisitas dua adapter hanya bisa dicapai dengan membocorkan `*sql.Tx` ke inti.
5. **Konstruksi adapter hanya di `cmd/` atau paket wiring.** Use case menerima port lewat konstruktor;
   membangun adapter di dalam use case menghapus seluruh keuntungan isolasi dan menggagalkan test unit.

`go.mod` dan `go.sum` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Deklarasi tipe/interface | `Grep -n "type <Nama> (struct\|interface)"` di `source_root` |
| Pemakai simbol | `Grep -n "<Simbol>"`, saring blok `import (` dan berkas `_test.go` bila tidak relevan |
| Pemanggil fungsi/method | `Grep -n "\.<Method>\("` atau `Grep -n "<Fungsi>\("`, telusuri receiver via `Read` |
| Implementasi interface | `Grep -n "func (\w+ \*\?<Tipe>) <Method>"` — Go tanpa `implements`, kecocokan lewat set method |
| Titik masuk HTTP | `Glob` `**/routes.go`, `**/handler.go` → `Grep -n "\.(GET\|POST\|PUT\|PATCH\|DELETE)\("` |
| Rantai Handler→Service→Repository | `Read` handler, catat field service di struct → `Grep -n "func (s \*<Service>)"` → `Read` method → `Grep -n "func (r \*<Repo>)"` |
| Akses penyimpanan | `Grep -n "QueryContext\|QueryRowContext\|ExecContext\|db.Query\|\.Find(\|\.First("` |
| Batas transaksi | `Grep -n "BeginTx\|\.Begin()\|WithTx\|Transaction("` |
| Messaging / Scheduler | `"nats.Subscribe\|kafka.NewReader\|amqp.*Consume"` / `"cron.New\|time.NewTicker\|time.AfterFunc"` |
| Middleware / Security | `Grep -n "func .*Middleware\|Use(" ` lalu `"jwt.Parse\|ParseWithClaims\|FromContext"` |
| Error handling terpusat | `Grep -n "HTTPErrorHandler\|ErrorHandler\|errors.Is\|errors.As"` |
| Config & schema | `Glob` `**/{.env.example,config*.y?ml}`; kode: `Grep -n "envconfig\|viper.Get"`; migrasi `**/migrations/**` |
| Deklarasi port (hexagonal) | `Grep -n "type \w+(Repository\|Port\|Gateway\|Publisher\|Provider) interface"` di `internal/{core,domain,ports,app,usecase}` |
| Adapter pengimplementasi port (hexagonal) | Ambil nama method port → `Grep -n "func (\w+ \*\?\w+) <MethodPort>\("` di `internal/adapters/**` |
| Arah dependensi inti (hexagonal) | `Grep -rn "database/sql\|jackc/pgx\|gorm.io\|gin-gonic\|labstack/echo\|internal/adapters" <core-dir>` — hit apa pun adalah kebocoran, bukan gaya |
| Wiring port → adapter (hexagonal) | `Glob` `**/cmd/**/*.go`, `**/wire*.go` → `Grep -n "New\w*(Repository\|Handler\|Service\|UseCase)\("` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35` — cukup menangkap signature,
receiver, dan `defer` di kepala fungsi.

## Audit checklist

#### `security`

- **Handler tanpa middleware otorisasi.** Rute terdaftar di grup publik padahal datanya milik user tertentu.
- **Identitas diambil dari body atau query, bukan dari context hasil autentikasi.** `userID`/`tenantID` yang dikirim klien membuat impersonasi trivial.
- **SQL injection lewat `fmt.Sprintf` di query.** Placeholder `$1`/`?` dilewati demi penggabungan string, termasuk pada nama kolom `ORDER BY` dinamis.
- **Struct domain di-`json.Unmarshal` langsung dari body.** Field seperti `Role` atau `Balance` ikut ter-set dari input.
- **Kredensial atau token ter-log.** Struct yang di-log utuh lewat `zap.Any`/`%+v` membawa field sensitif.
- **`http.Server` tanpa `ReadHeaderTimeout`.** Terbuka terhadap koneksi lambat yang menahan resource.
- **Error internal dikembalikan apa adanya ke response.** Pesan driver DB membocorkan nama tabel dan struktur query.

#### `transaction`

- **`tx.Rollback()` tidak di-`defer` sejak transaksi lahir.** Jalur error yang `return` lebih awal meninggalkan transaksi menggantung sampai koneksi ditutup.
- **`sql.DB` dipakai di dalam blok transaksi.** Query yang memakai `db` alih-alih `tx` berjalan di koneksi lain, di luar transaksi, dan tidak ikut ter-rollback.
- **Transaksi tidak diteruskan lewat `context` atau parameter.** Repository yang membuka transaksinya sendiri membuat dua operasi yang seharusnya atomik jadi dua transaksi terpisah.
- **Publish pesan sebelum `Commit`.** Consumer memproses data yang belum commit; bila rollback, pesan merujuk data hantu.
- **Baca lalu tulis tanpa `SELECT ... FOR UPDATE` atau `UPDATE ... WHERE versi = ?`.** Dua request paralel saling menimpa pada mutasi stok atau kuota.

#### `data`

- **`float64` untuk nominal uang.** Akumulasi galat biner; wajib integer unit terkecil atau tipe desimal.
- **`time.Time` ditulis tanpa normalisasi zona.** Campuran `time.Now()` dan `time.Now().UTC()` membuat perbandingan rentang salah di batas hari.
- **Error dari `Scan`, `Unmarshal`, atau `strconv` diabaikan dengan `_`.** Nilai nol lolos sebagai data valid.
- **Validasi hanya di handler.** Consumer, scheduler, dan importer yang menulis tabel sama melewati aturan yang sama.
- **Field opsional dimodelkan sebagai nilai nol, bukan pointer atau `sql.NullX`.** Nol dan "tidak diisi" jadi tak terbedakan.
- **`switch` atas enum tanpa cabang `default` yang melempar error.** Nilai baru lolos diam-diam sebagai perilaku cabang pertama.

#### `persistence`

- **N+1 query di dalam loop.** `FindByID` per elemen alih-alih satu query `WHERE id = ANY(...)`.
- **`rows.Close()` tidak di-`defer`, atau `rows.Err()` tidak diperiksa.** Yang pertama membocorkan koneksi; yang kedua menyembunyikan kegagalan iterasi sebagai hasil kosong.
- **Query tanpa `LIMIT` pada tabel yang tumbuh.** Seluruh tabel masuk memori proses.
- **Pool koneksi memakai default.** `SetMaxOpenConns` yang tidak diset membiarkan jumlah koneksi tumbuh sampai DB menolak.
- **`QueryRow` tanpa membedakan `sql.ErrNoRows` dari error lain.** "Tidak ditemukan" jadi HTTP 500, atau sebaliknya kegagalan nyata jadi 404.

#### `concurrency`

- **Goroutine tanpa jalur berhenti.** Tidak menerima `ctx` dan tidak punya kondisi keluar; bocor selama proses hidup.
- **Goroutine memakai variabel loop tanpa menyalinnya** (pada Go < 1.22) sehingga seluruh goroutine melihat elemen terakhir.
- **Map atau slice bersama ditulis tanpa `sync.Mutex`.** Race pada map memicu panik fatal yang tidak bisa di-`recover`.
- **`panic` di dalam goroutine tanpa `recover`.** Satu goroutine tumbang menjatuhkan seluruh proses, bukan satu request.
- **Consumer tanpa idempotensi.** Redelivery broker memproses pesan yang sama dua kali.
- **`http.Client` atau panggilan keluar tanpa timeout.** Client default Go tidak punya batas waktu.
- **Scheduler multi-instance tanpa lock terdistribusi.** Dua pod menjalankan job yang sama bersamaan.
- **`WaitGroup.Add` dipanggil di dalam goroutine**, bukan sebelum ia dijalankan.

#### `architecture`

- **Logika bisnis di handler.** Percabangan aturan ditulis di fungsi yang juga mengurus decode dan status HTTP.
- **Repository dipanggil langsung dari handler**, melewati lapisan service.
- **Impor `internal/<domain-lain>` langsung antar-domain.** Ketergantungan silang antar-domain seharusnya lewat interface yang dideklarasikan konsumen.
- **Interface dideklarasikan di sisi implementasi, bukan konsumen.** Membalik arah dependensi dan menyulitkan pengujian.
- **Variabel paket yang bisa berubah (`var` global).** State bersama tanpa penjagaan, sekaligus membuat test saling memengaruhi.
- **`init()` melakukan kerja bereferensi lingkungan.** Urutannya tidak terkendali dan gagal diam saat konfigurasi belum siap.

Empat butir berikut **hanya berlaku bila `architecture: hexagonal`**; pada repo `layered` keempatnya bukan temuan:

- **Paket inti mengimpor adapter atau driver.** `internal/core` yang mengimpor `internal/adapters/...`, `database/sql`, atau paket framework membalik arah dependensi: kompilasi tetap hijau, tetapi isolasi yang jadi alasan memilih gaya ini hilang seluruhnya.
- **Port dideklarasikan di paket adapter.** Interface milik implementornya membuat inti mengimpor adapter untuk memakai kontraknya sendiri, dan mengunci inti pada satu implementasi.
- **Tipe infrastruktur muncul di signature port.** `*sql.Tx`, `*gorm.DB`, `*gin.Context`, atau `pgx.Rows` pada interface inti membocorkan detail teknologi ke domain dan membuat fake port di test menarik driver aslinya.
- **Use case membangun adapternya sendiri.** `NewPostgresRepo(db)` dipanggil di dalam use case alih-alih diinjeksikan dari `cmd/`, sehingga port tidak bisa diganti dan test unit memaksa DB nyata hidup.

## API surface

Endpoint didaftarkan secara imperatif, bukan lewat anotasi. Sumber kebenarannya adalah berkas wiring
rute, bukan berkas handler.

- **Kelompok & prefix**: pemanggilan `Group("/api/v1")` (Echo/Gin/Fiber) atau `Route("/api/v1", ...)`
  (chi). Prefix bertingkat digabung dari luar ke dalam.
- **Method + path**: `e.GET("/products/:id", h.Get)`, `r.Post("/products", h.Create)`. Parameter path
  memakai `:name` (Echo/Gin/Fiber) atau `{name}` (chi/gorilla).
- **Parameter**: `c.Param("id")` untuk path, `c.QueryParam`/`r.URL.Query().Get` untuk query. Status
  wajib/opsional dan nilai default hanya terlihat dari kode handler, bukan dari deklarasi rute.
- **Request body**: struct tujuan `c.Bind(&req)` atau `json.NewDecoder(r.Body).Decode(&req)`; aturan
  validasi dari tag `validate:"..."` atau pemeriksaan manual di awal handler.
- **Response & status**: argumen pertama `c.JSON(http.StatusCreated, ...)` atau
  `w.WriteHeader(...)`. Tanpa penulisan eksplisit, statusnya `200`.
- **Otorisasi per endpoint**: middleware yang dipasang di grup rute (`g.Use(auth.Require("admin"))`),
  bukan di handler. Endpoint mewarisi seluruh middleware grup induknya.
- **Bentuk error**: `HTTPErrorHandler` terpusat atau helper `httpx.Error(w, err)`.
- **Pada `architecture: hexagonal`**: wiring rute hidup di adapter driving (`internal/adapters/http/router.go`)
  atau di `cmd/`, dan bentuk request/response adalah DTO milik adapter itu — bukan entitas domain.
  Petakan endpoint ke use case yang dipanggil handler, karena di situlah kontrak perilakunya berada.

## Failure signatures

- **`panic` + goroutine stack trace.** Frame paling informatif adalah frame pertama yang path-nya di
  bawah `root_namespace`; frame di atasnya milik runtime atau framework. Bila jejaknya memuat banyak
  goroutine, yang relevan adalah goroutine yang barisnya bertanda `[running]`.
- **`nil pointer dereference`** — lazimnya hasil error yang diabaikan satu langkah sebelumnya:
  nilai dikembalikan bersama error, error dibuang, nilai nil dipakai.
- **`sql: database is closed` atau `too many connections`** — kebocoran koneksi; cari `rows.Close()`
  dan `tx.Rollback()` yang tidak di-`defer`.
- **`context deadline exceeded`** — timeout dari `ctx`, bukan dari DB. Telusuri asal `ctx`: timeout
  request, timeout klien HTTP, atau `context.WithTimeout` di lapisan tengah.
- **`context canceled` pada query** — klien memutus request; jadi masalah hanya bila muncul di jalur
  latar yang seharusnya tidak terikat siklus request.
- **`fatal error: concurrent map writes`** — race pada map bersama. Tidak bisa di-`recover`;
  prosesnya mati. Jalankan ulang dengan `go test -race` untuk melokalisasi.
- **`all goroutines are asleep - deadlock!`** — channel tanpa pembaca atau `WaitGroup` yang tidak pernah `Done`.
- **Test hijau sendiri tapi merah dalam satu paket** — state bersama antar-test: variabel paket,
  koneksi DB yang dipakai ulang, atau `t.Parallel()` di atas fixture bersama.
