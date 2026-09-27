# Fullstack Repository Profile Template

Dokumen ini merupakan template acuan profil arsitektur untuk aplikasi Fullstack satu paket: UI dan route server hidup di paket yang sama (Next.js route handlers/API routes, SvelteKit `+server.ts`/`+page.server.ts`, Remix/React Router loader/action, Nuxt `server/api`). Monorepo dengan workspace backend dan frontend terpisah tetap diprofilkan per workspace memakai template backend atau frontend. Panjang dokumen profil final yang dihasilkan wajib berada di bawah 10.000 karakter dan mencantumkan fakta nyata dari file konfigurasi serta baseline pengujian aktual. Setiap placeholder `<...>` wajib diganti fakta repo; contoh di dalamnya bukan nilai default.

---

## 1. Project Overview & Runtime

- **Repository Name**: `<nama-repo>`
- **Workspace**: `<workspace_dir | . (root)>`
- **Runtime & Language**: `<misal: Node.js 20 LTS + TypeScript 5.x>`
- **Core Framework**: `<misal: Next.js 14 (App Router) / SvelteKit 2 / Remix 2 / Nuxt 3>`
- **Package Manager**: `<misal: pnpm / npm / yarn / bun>`
- **Path Aliases**: `<misal: @/* -> src/* di tsconfig.json>`
- **Environment & Config Management**: `<misal: .env.local + env.mjs (zod), $env/static/private>` — variabel server-only vs publik (`NEXT_PUBLIC_*`, `PUBLIC_*`)

## 2. UI Framework & State Management

- **UI Component Library**: `<misal: Tailwind CSS / shadcn/ui / MUI>`
- **Global State Management**: `<misal: Zustand / Svelte stores / Pinia / React Context | tidak ada>`
- **Server State & Data Fetching**: `<misal: Server Components + fetch / TanStack Query / SWR / load function>`
- **Form Management & Validation**: `<misal: React Hook Form + Zod / Superforms / Server Actions + zod>`

## 3. Component & Layering Hierarchy

Batas antara kode klien dan kode server beserta arah dependensinya:

- **Page / View Layer**: `<lokasi: app/**/page.tsx, src/routes/**/+page.svelte>`
- **Feature & UI Components**: `<lokasi: src/components/ui/, src/features/*/components/>`
- **Client Hooks / Stores**: `<lokasi: src/hooks/, src/lib/stores/>`
- **Server-only Modules**: `<lokasi: src/server/, src/lib/server/, *.server.ts>` — larangan impor dari komponen klien: `<penanda nyata: import 'server-only' / $lib/server | tidak ada>`
- **Shared Types & Schemas**: `<lokasi: src/types/, src/schemas/>` — dipakai klien dan server

## 4. Server Routes, Data Access & Error Handling

- **Server-side Route Pattern**: `<pola path nyata: app/api/**/route.ts | src/routes/**/+server.ts | app/routes/*.tsx (loader/action) | server/api/**>`
- **Server Actions / Form Actions**: `<pola nyata | tidak ada>`
- **Input Validation**: `<misal: zod schema di handler, lokasi src/schemas/>`
- **Response & Error Convention**: `<salin bentuk response/error nyata beserta path sumbernya; status code yang dipakai>`
- **Authentication & Route Protection**: `<misal: middleware.ts + next-auth, hooks.server.ts>`
- **Database & ORM**: `<misal: PostgreSQL + Prisma (prisma/schema.prisma) | tidak ada>`
- **Migration Apply Command**: `<misal: pnpm prisma migrate deploy>` — dicatat, tidak pernah dijalankan skill

## 5. Verification Baseline

Dijalankan dari root repo kecuali kolom Cwd menyebut lain. Status: `PASSED` | `FAILED` | `TIMEOUT` | `SKIPPED` | `UNVERIFIED_ENV_NOT_READY` | `TIDAK_ADA` (tidak ada runner/konfigurasi di manifest). Known issues memakai penanda persis (mis. `src/legacy/a.ts:12 no-explicit-any`, `test_order_refund`), maksimal 10 baris; bila lebih, tulis `<n> issue — contoh: …` beserta perintah untuk mereproduksi daftar lengkap. `UNVERIFIED_ENV_NOT_READY` diberi pesan penyebab satu baris di kolom Known issues; `SKIPPED` diberi alasannya (`ditolak user: menyentuh DB/jaringan`, `ditolak user: lewati semua`, atau `skip_baseline_exec`). `quickdev:execute` mencocokkan galat per berkas + aturan/nama test, tanpa nomor baris.

Baseline-Commit: `<sha HEAD saat baseline dijalankan | none (repo tanpa commit)>` — tree bersih: `<ya | tidak: daftar berkas>`

| Jenis | Perintah | Cwd | Status | Durasi | Known issues (baseline) |
|---|---|---|---|---|---|
| Typecheck | `<perintah: misal pnpm typecheck / npx tsc --noEmit>` | `.` | <status> | <detik> | `<berkas:baris kode/aturan>` per issue, atau `-` |
| Linter | `<perintah: misal pnpm lint / eslint src --ext .ts,.tsx>` | `.` | <status> | <detik> | `<berkas:baris aturan>` per issue, atau `-` |
| Test | `<perintah: misal pnpm test / vitest run / jest>` | `.` | <status> | <detik> | `<nama test gagal/skip>` per issue, atau `-` |
| Build | `<perintah: misal pnpm build>` | `.` | <status> | <detik> | `<pesan galat ringkas>`, atau `-` |

## 6. Styling & Design System Rules

- **Styling Paradigm**: `<misal: Tailwind CSS Utility Classes / CSS Modules>`
- **Color Palette & Design Tokens**: `<lokasi: tailwind.config.ts, src/styles/theme.css>`
- **UI State Branches Convention**: `<cabang state yang benar-benar dipakai repo (misal: loading, empty, error, success) beserta komponen atau pola acuannya; tulis "tidak ada konvensi" bila tiap komponen berbeda>`
