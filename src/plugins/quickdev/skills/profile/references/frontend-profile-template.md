# Frontend Repository Profile Template

Dokumen ini merupakan template acuan profil arsitektur untuk repositori Frontend. Panjang dokumen profil final yang dihasilkan wajib berada di bawah 10.000 karakter dan mencantumkan fakta nyata dari file konfigurasi serta baseline pengujian aktual. Setiap placeholder `<...>` wajib diganti fakta repo; contoh di dalamnya bukan nilai default.

---

## 1. Project Overview & Runtime

- **Repository Name**: `<nama-repo>`
- **Workspace**: `<workspace_dir | . (root)>`
- **Runtime & Language**: `<misal: TypeScript 5.x / JavaScript ES2024 / Node.js 20 LTS>`
- **Core Framework**: `<misal: Next.js 14 (App Router) / React 18 / Vue 3 / Nuxt 3 / SvelteKit>`
- **Build Tool & Bundler**: `<misal: Vite / Turbopack / Webpack>`
- **Package Manager**: `<misal: pnpm / npm / yarn / bun>`
- **Path Aliases**: `<misal: @/* -> src/* di tsconfig.json>`
- **Entry Points**: `<misal: src/main.tsx, app/layout.tsx, pages/_app.tsx>`

## 2. UI Framework & State Management

- **UI Component Library**: `<misal: Tailwind CSS / shadcn/ui / MUI / Ant Design / Mantine>`
- **Global State Management**: `<misal: Zustand / Redux Toolkit / Jotai / Pinia / React Context>`
- **Server State & Data Fetching**: `<misal: TanStack Query (React Query) / SWR / RTK Query>`
- **Form Management & Validation**: `<misal: React Hook Form + Zod / Formik + Yup>`
- **Icon Set**: `<misal: Lucide Icons / Heroicons / Tabler Icons>`

## 3. Component & Layering Hierarchy

Struktur arsitektur folder frontend dan batasan layer:

- **Page / View Layer**: `<lokasi: src/pages/ atau src/app/>`
  - Tanggung jawab: Mengelola routing, breadcrumbs, komposisi kontainer tampilan.
- **Component Layer (Smart vs Dumb)**:
  - **Shared / UI Primitive Components**: `<lokasi: src/components/ui/>` (Tombol, Input, Modal, Badge — 100% presentasional murni).
  - **Feature / Domain Components**: `<lokasi: src/features/*/components/>` (Widget bisnis, form khusus domain).
- **View-Model / Custom Hooks Layer**: `<lokasi: src/hooks/ atau src/features/*/hooks/>`
  - Tanggung jawab: Menampung state lokal UI, logika transisi interaksi, binding ke data fetching.
- **API Client & Services**: `<lokasi: src/services/ atau src/api/>`
  - Tanggung jawab: Abstraksi HTTP client (Axios/Fetch), type definitions untuk API request/response.

## 4. Routing & Navigation Architecture

- **Router Type**: `<misal: Next.js App Router / React Router v6 / TanStack Router>`
- **Navigation Conventions**:
  - URL slugs: `<konvensi nyata dari definisi route, misal: kebab-case /dashboard/user-settings>`
  - Query Params: `<state yang benar-benar disinkronkan ke URL, misal: ?page=1&status=active>`
- **Route Protection & Guards**: `<misal: Middleware middleware.ts / ProtectedRoute wrapper>`

## 5. Verification Baseline

Dijalankan dari root repo kecuali kolom Cwd menyebut lain. Status: `PASSED` | `FAILED` | `TIMEOUT` | `SKIPPED` | `UNVERIFIED_ENV_NOT_READY` | `TIDAK_ADA` (tidak ada runner/konfigurasi di manifest). Known issues memakai penanda persis (mis. `src/legacy/a.ts:12 no-explicit-any`, `test_order_refund`), maksimal 10 baris; bila lebih, tulis `<n> issue — contoh: …` beserta perintah untuk mereproduksi daftar lengkap. `UNVERIFIED_ENV_NOT_READY` diberi pesan penyebab satu baris di kolom Known issues.

| Jenis | Perintah | Cwd | Status | Durasi | Known issues (baseline) |
|---|---|---|---|---|---|
| Typecheck | `<perintah: misal pnpm typecheck / npx tsc --noEmit>` | `.` | <status> | <detik> | `<berkas:baris kode/aturan>` per issue, atau `-` |
| Linter | `<perintah: misal pnpm lint / eslint src --ext .ts,.tsx>` | `.` | <status> | <detik> | `<berkas:baris aturan>` per issue, atau `-` |
| Test | `<perintah: misal pnpm test / vitest run / jest>` | `.` | <status> | <detik> | `<nama test gagal/skip>` per issue, atau `-` |
| Build | `<perintah: misal pnpm build>` | `.` | <status> | <detik> | `<pesan galat ringkas>`, atau `-` |

## 6. Styling & Design System Rules

- **Styling Paradigm**: `<misal: Tailwind CSS Utility Classes / CSS Modules / Styled-Components>`
- **Color Palette & Design Tokens**: `<lokasi: tailwind.config.js, src/styles/theme.css>`
- **Responsive Breakpoints**: `<misal: sm (640px), md (768px), lg (1024px), xl (1280px)>`
- **UI State Branches Convention**: `<cabang state yang benar-benar dipakai repo (misal: loading, empty, error, success) beserta komponen atau pola acuannya; tulis "tidak ada konvensi" bila tiap komponen berbeda>`
