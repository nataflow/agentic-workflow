# Backend Repository Profile Template

Dokumen ini merupakan template acuan profil arsitektur untuk repositori Backend. Panjang dokumen profil final yang dihasilkan wajib berada di bawah 10.000 karakter dan mencantumkan fakta nyata dari file konfigurasi serta baseline pengujian aktual. Setiap placeholder `<...>` wajib diganti fakta repo; contoh di dalamnya bukan nilai default.

---

## 1. Project Overview & Runtime

- **Repository Name**: `<nama-repo>`
- **Runtime & Language**: `<misal: Node.js 20 LTS / Python 3.11 / Go 1.22 / Java 21>`
- **Framework**: `<misal: NestJS / Express / FastAPI / Gin / Spring Boot>`
- **Package Manager**: `<misal: pnpm / npm / yarn / poetry / go modules / maven>`
- **Environment & Config Management**: `<misal: dotenv (.env.example), config service, pydantic-settings>`
- **Entry Point**: `<misal: src/main.ts, app/main.py, cmd/server/main.go>`

## 2. Architecture & Layering Pattern

Hierarki layer backend dan pemisahan tanggung jawab kode:

- **Presentation / Controller Layer**: `<lokasi: src/controllers/ atau src/api/routes/>`
  - Tanggung jawab: Menerima HTTP request, validasi input DTO/Schema, memetakan status response HTTP.
- **Business Logic / Service Layer**: `<lokasi: src/services/ atau src/usecases/>`
  - Tanggung jawab: Mengelola aturan bisnis inti, orkestrasi domain, transaksi database.
- **Data Access / Repository Layer**: `<lokasi: src/repositories/ atau src/models/>`
  - Tanggung jawab: Abstraksi query database, komunikasi ORM/Query Builder.
- **Data Transfer Objects (DTO) & Entities**: `<lokasi: src/dtos/ atau src/schemas/>`
  - Tanggung jawab: Definisi tipe data request/response payload, validasi deklaratif.
- **Middlewares & Interceptors**: `<lokasi: src/middlewares/ atau src/interceptors/>`
  - Tanggung jawab: Autentikasi JWT, logging, rate limiting, exception filter global.

## 3. Database, ORM & Migrations

- **Database Engine**: `<misal: PostgreSQL 16 / MySQL 8 / MongoDB 7 / Redis 7>`
- **ORM / Query Builder**: `<misal: Prisma / TypeORM / Drizzle / SQLAlchemy / GORM>`
- **Migration Path & Tool**: `<misal: prisma/migrations, alembic/versions, migrations/>`
- **Migration Status Command**: `<misal: pnpm prisma migrate status / alembic current>` — read-only
- **Migration Apply Command**: `<misal: pnpm prisma migrate deploy / alembic upgrade head>` — dicatat, tidak pernah dijalankan skill
- **Seeding Command**: `<misal: pnpm prisma db seed / python scripts/seed.py>`

## 4. API Contracts & Routing Conventions

- **API Architecture**: `<misal: RESTful JSON API / GraphQL / gRPC>`
- **Base URL & Versioning**: `<misal: /api/v1>`
- **Authentication Strategy**: `<misal: Bearer JWT Authorization Header / Cookie Session>`
- **Naming Conventions**:
  - Endpoint URLs: `<konvensi nyata dari route eksisting, misal: kebab-case plural /api/v1/user-profiles>`
  - Payload keys: `<konvensi nyata dari DTO eksisting, misal: camelCase / snake_case>`
- **Standard Response Envelope**: `<salin bentuk envelope nyata beserta path sumbernya; tulis "tidak ada envelope" bila handler mengembalikan payload mentah>`

## 5. Verification Baseline

Perintah pengujian dan audit kualitas kode yang wajib dijalankan sebelum dan sesudah perubahan:

- **Typecheck**: `<perintah: misal pnpm tsc --noEmit / mypy src>`
- **Linter**: `<perintah: misal pnpm lint / ruff check . / golangci-lint run>`
- **Unit & Integration Tests**: `<perintah: misal pnpm test / pytest / go test ./...>`
- **Build / Bundle Check**: `<perintah: misal pnpm build / go build ./...>`

## 6. Error Handling & Logging Standards

- **Custom Exception Classes**: `<lokasi: src/common/exceptions/>`
- **Global Error Filter**: `<lokasi: src/common/filters/http-exception.filter.ts>`
- **Standard Error Payload**: `<salin bentuk payload error nyata dari exception filter/handler beserta path sumbernya>`
- **Logging Utility**: `<misal: Pino / Winston / structlog / logrus>`
