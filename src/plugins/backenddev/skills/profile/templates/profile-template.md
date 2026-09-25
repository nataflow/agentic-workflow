# `.claude/profile/backenddev/` Template

Dokumen ini mendefinisikan struktur artefak modular `.claude/profile/backenddev/` yang ditulis oleh `backenddev:profile` pada Fase 6.
Profil codebase disimpan dalam direktori `.claude/profile/backenddev/` yang terdiri atas `index.json` (metadata terstruktur) dan 8 berkas markdown seksi arsitektur.

**Field `stack` pada `index.json` adalah kunci pemuatan adapter.** Tanpa nilai yang sah, tiap skill hilir tidak tahu berkas `stacks/<stack-id>.md` mana yang harus dibaca dan akan berhenti di Fase 0-nya.

**Prinsip Statis & Blueprint:** Seluruh berkas hanya mencatat konsep, arsitektur, dan blueprint statis yang bertahan lintas fitur. Dilarang mencatat data dinamis/fast-changing seperti *migration high-water mark* atau snapshot error sesaat.

---

## Tata cara anchor bukti

Profil hidup jauh lebih lama daripada nomor baris. Setiap bukti karena itu ditulis sebagai **anchor**, bukan koordinat baris. Dua bentuk sah, tidak ada yang ketiga:

| Bentuk | Kapan dipakai |
|---|---|
| `<path>#<simbol>` | default — `<simbol>` = nama fungsi, method, tipe, kelas, atau konstanta |
| `<path>` | seluruh berkas memang yang dirujuk, atau anchor provisional saat sampel belum cukup |

- Method yang namanya tidak unik dalam satu berkas ditulis `<path>#<Tipe>.<method>`.
- Fakta tingkat-berkas — import, penanda package-level, ketiadaan sebuah paket — memakai `<path>` telanjang; dilarang memaksakan simbol terdekat yang bukan pemikul fakta itu.
- Berkas tanpa simbol (YAML, SQL, Dockerfile, properties) memakai kunci atau direktifnya: `Dockerfile#ENV TZ`, `application.yml#spring.datasource`.
- **Nomor baris dilarang dalam bentuk apa pun**, termasuk `#L12`. Nomor baris bergeser diam-diam lalu tetap resolve ke baris keliru; anchor yang basi gagal berisik.
- Syarat sah: anchor wajib dapat ditemukan kembali lewat satu Grep atas literal `<simbol>` di `<path>`. Yang tidak memenuhi ini diturunkan ke `<path>` telanjang, bukan dipaksakan.

---

## 1. `.claude/profile/backenddev/index.json`

Metadata konfigurasi dan identitas repositori dalam format JSON valid:

```json
{
  "plugin": "backenddev",
  "project": "<nama-repo>",
  "stack": "<java-spring | go | node | bun | rust | php | php-codeigniter>",
  "architecture": "<layered | hexagonal | hybrid | tidak terdeteksi>",
  "root_namespace": "<package/module/namespace dasar aplikasi>",
  "source_root": "<path/relatif/ke/source-root>",
  "commit_convention": "<pola pesan commit repo ini, mis. 'conventional: <type>(<scope>): <subject>'>",
  "base_branch": "<branch titik cabang pekerjaan sekaligus titik banding review, mis. main atau dev>",
  "branch_convention": "<pola nama branch memuat placeholder <slug>, mis. feat/<slug>>"
}
```

`plugin` selalu `"backenddev"`: penanda kepemilikan. Profil ber-`plugin` lain tidak pernah dibaca atau ditimpa skill backenddev, dan skrip prasyarat memvonisnya FAIL.

---

## 2. `.claude/profile/backenddev/stack.md`

Ringkasan blueprint stack, versi runtime, package manager, dan dependensi penanda:

```markdown
# Stack

<framework + versi> / <bahasa + versi> · <package manager aktif + lockfile, sebut bila lebih dari satu> · <database + migration tool> · <messaging bila ada> · <cache bila ada> · <websocket bila ada> · <codegen bila ada>
```

---

## 3. `.claude/profile/backenddev/module-structure.md`

Pola pengelompokan modul, gaya arsitektur, anatomi layer, dan tipe data batas:

```markdown
# Module Structure

<pola module: bergrup domain, flat, atau monorepo — tulis contoh path nyata>
Gaya: <nilai `architecture` + anchor penentunya; bila `hybrid`, sebutkan modul mana hexagonal dan mana layered>
Anatomi: <pola penamaan tiap layer menurut sub-bagian `## Layer taxonomy` adapter yang sesuai gaya, dan di mana definisi persistensi hidup relatif terhadap module>
Tipe batas: <pola folder tipe request/response, dan mekanisme pemetaannya>
Shared: <folder util bersama bila ada>
```

---

## 4. `.claude/profile/backenddev/domain-map.md`

Peta modul bisnis nyata beserta path, permukaan aktif, dan titik entri daftarnya (maksimal 12 baris):

```markdown
# Domain Map

<domain bisnis>: <path/glob modul> · <permukaan aktif, dipisah tanda +> · entry <file#simbol>
```

---

## 5. `.claude/profile/backenddev/surface-map.md`

Peta permukaan runtime aktif yang benar-benar ada di kode (maksimal 15 baris). Permukaan yang tidak ada dihapus:

```markdown
# Surface Map

<permukaan>: <path/glob tempatnya hidup> · <penanda pengenal> · <catatan satu frasa>
```

---

## 6. `.claude/profile/backenddev/code-conventions.md`

Keputusan gaya nyata yang dianut repo per aspek kanonik (maksimal 10 baris). Setiap baris wajib bercontoh anchor:

```markdown
# Code Conventions

<aspek>: <aturan satu frasa> · contoh <file#simbol>
```

---

## 7. `.claude/profile/backenddev/anti-patterns.md`

Pola minoritas atau warisan yang dilarang ditiru beserta pola pengganti mayoritas, resep pengenalnya, dan buktinya (maksimal 8 baris). Baris bersumber repo wajib ber-`deteksi`; baris bersumber konfirmasi user dilarang punya `deteksi` karena polanya memang tak berjejak di kode:

```markdown
# Anti-patterns

- <pola terlarang> (<sebaran>) → <pola pengganti> · deteksi `<pola> @ <cakupan>` · bukti <file#simbol>
- <pola terlarang> → <pola pengganti> · bukti user
```

`deteksi` adalah resep `Grep` yang mengembalikan pelanggarnya — pola pencarian, tanda `@`, lalu glob cakupannya — bukan perintah shell literal. Ia wajib menghasilkan minimal satu hit saat profil ditulis — nol hit berarti polanya tidak ada dan barisnya batal — dan pada REFRESH ia dijalankan ulang untuk memvonis apakah pola itu masih hidup.

---

## 8. `.claude/profile/backenddev/invariants.md`

Aturan keras runtime yang bila dilanggar membuat sistem rusak (blocker, bukan sekadar gaya kode):

```markdown
# Invariants (violation = blocker, not style)

- <invariant 1 — aturan runtime/arsitektur keras>
- <invariant 2>
- <zona waktu runtime — format terbukti atau format nihil standar>
- <boundary scoping, gerbang env consumer/scheduler, mirrored runtime paths>
```

---

## 9. `.claude/profile/backenddev/commands.md`

Blueprint perintah build, verifikasi, dan manajemen migrasi:

```markdown
# Commands

build: <command> [OK|FAIL|tidak berlaku] · typecheck: <command> [status] · lint: <command> [status]
typecheck-scoped: <command berplaceholder target> [status|tidak berlaku] · typecheck-per-brief: <ya|tidak — alasan>
test: <command> [status] · test-single: <command dengan placeholder target> [status]
migration: <command> · folder <path> · pola <format nama berkas>
```

---

## Filled Example — `orders-api` (Go Stack)

### `.claude/profile/backenddev/index.json`
```json
{
  "project": "orders-api",
  "stack": "go",
  "architecture": "layered",
  "root_namespace": "github.com/acme/orders-api",
  "source_root": "internal",
  "commit_convention": "conventional: <type>(<scope>): <subject> — subject bahasa Inggris huruf kecil",
  "base_branch": "main",
  "branch_convention": "feat/<slug>"
}
```

### `.claude/profile/backenddev/stack.md`
```markdown
# Stack

Echo v4.11 / Go 1.22 · go modules (go.sum) · PostgreSQL + golang-migrate · NATS JetStream · Redis · sqlc untuk codegen query
```

### `.claude/profile/backenddev/module-structure.md`
```markdown
# Module Structure

internal/<domain>/… — bergrup domain: internal/order, internal/catalog, internal/billing
Gaya: layered — internal/order/service.go#orderService menyimpan *sql.DB langsung; tidak ada paket ports/adapters
Anatomi: handler.go / service.go / repository.go per domain; definisi tabel di db/schema.sql (sqlc)
Tipe batas: internal/<domain>/dto.go — struct request/response terpisah dari struct domain
Shared: internal/platform/ (config, logger, httpx, txmanager)
```

### `.claude/profile/backenddev/domain-map.md`
```markdown
# Domain Map

order: internal/order · http+consumer · entry cmd/api/routes.go#registerOrderRoutes
catalog: internal/catalog · http · entry cmd/api/routes.go#registerCatalogRoutes
billing: internal/billing · http+scheduler · entry cmd/api/routes.go#registerBillingRoutes
```

### `.claude/profile/backenddev/surface-map.md`
```markdown
# Surface Map

http: internal/*/handler.go · echo.Group registrasi di cmd/api/routes.go · prefix /api/v1
transaksi: internal/platform/txmanager · pgx.Tx diteruskan lewat context, tidak pernah global
persistence: internal/*/repository.go · sqlc generated di internal/*/db/ · query di *.sql
migration: db/migrations · {n}_{deskripsi}.up.sql · golang-migrate
messaging: internal/*/subscriber.go · nats.Subscribe · digerbang ENABLE_CONSUMER
scheduler: cmd/worker/ · robfig/cron · digerbang ENABLE_SCHEDULER
cache: internal/platform/cache · redis.Client langsung
security: internal/platform/auth · echo middleware JWT · role dari klaim `roles`
error: internal/platform/httpx/error.go · HTTPErrorHandler terpusat · bentuk APIResponse
config: internal/platform/config · envconfig struct · .env.example sebagai daftar wajib
```

### `.claude/profile/backenddev/code-conventions.md`
```markdown
# Code Conventions

penamaan: satu domain = satu paket; berkas per peran (handler/service/repository) · contoh internal/order/service.go
error: dibungkus fmt.Errorf("...: %w", err), sentinel errors di internal/platform/errs · contoh internal/order/service.go#orderService.Create
tipe batas: struct request/response di dto.go, pemetaan manual ke struct domain · contoh internal/order/dto.go#CreateOrderRequest
validasi: di handler sebelum service dipanggil, lewat go-playground/validator tag · contoh internal/order/handler.go#handler.Create
logging: slog terstruktur dengan field request_id; dilarang fmt.Println · contoh internal/platform/logger/log.go#New
wiring: konstruktor New<Peran>(deps) dirakit manual di cmd/api/main.go, tanpa DI container · contoh cmd/api/main.go#main
envelope: seluruh response dibungkus httpx.APIResponse{data,error} · contoh internal/platform/httpx/response.go#APIResponse
test: <nama>_test.go bersebelahan dengan berkas ujinya, table-driven · contoh internal/order/service_test.go#TestOrderService_Create
```

### `.claude/profile/backenddev/anti-patterns.md`
```markdown
# Anti-patterns

- Akses *sql.DB langsung dari handler, melompati repository (warisan, 3 tempat) → panggil repository domainnya · deteksi `sql\.DB @ internal/*/handler.go` · bukti internal/catalog/handler.go#handler.List
- panic() sebagai kontrol alur di jalur request (2 tempat) → kembalikan error dan biarkan HTTPErrorHandler memetakannya · deteksi `panic\( @ internal/*/{handler,service}.go` · bukti internal/billing/service.go#billingService.Charge
- time.Now() dipanggil langsung di service, membuat test bergantung jam dinding → injeksi clock lewat deps konstruktor · deteksi `time\.Now\(\) @ internal/*/service.go` · bukti internal/order/service.go#orderService.Create
- Menambah kolom lewat sqlc tanpa migrasi baru → satu migrasi baru per perubahan skema · bukti user
```

### `.claude/profile/backenddev/invariants.md`
```markdown
# Invariants (violation = blocker, not style)

- Setiap perubahan db/schema.sql WAJIB disertai migrasi baru + `sqlc generate`; lupa = build merah
- Transaksi hanya lewat internal/platform/txmanager; membuka pgx.Tx manual di repository dilarang
- context.Context WAJIB diteruskan sampai lapisan query; repository tanpa ctx = query tak bisa dibatalkan
- Tenant scoping lewat internal/platform/auth.TenantFromContext — jangan di-bypass
- Mirrored runtime paths: handler.go · subscriber.go · cmd/worker harus konsisten untuk state order
- TZ=UTC diset di Dockerfile#ENV TZ → seluruh time.Time lahir dalam UTC; konversi lokal wajib eksplisit
```

### `.claude/profile/backenddev/commands.md`
```markdown
# Commands

build: go build ./... [OK] · typecheck: go vet ./... [OK] · lint: golangci-lint run [FAIL]
typecheck-scoped: go build ./<paket>/... [OK] · typecheck-per-brief: ya — inkremental, biayanya mendekati nol
test: go test ./... [OK] · test-single: go test ./internal/order -run <TestName> [OK]
migration: migrate -path db/migrations -database $DATABASE_URL up · folder db/migrations · pola {n}_{deskripsi}.up.sql
```
