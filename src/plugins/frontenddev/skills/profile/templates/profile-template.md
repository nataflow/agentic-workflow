# `.claude/profile/frontenddev/` Template

Profil kode acuan arsitektur untuk seluruh skill dan subagent plugin `frontenddev`. Nilai contoh di bawah bercampur antar stack sebagai ilustrasi; profil nyata hanya memuat idiom satu `<stack-id>`.

Profil ditulis **modular**: satu `index.json` dan sembilan berkas `.md`. Konsumen membaca hanya berkas yang rutenya butuhkan — `ui-design` membuka `visual.md` saja, `code-implementor` membuka `invariants.md` dan `surface-map.md` saja. Monolit satu berkas memaksa tiap konsumen menelan seluruh profil untuk mengambil satu tabel.

---

## Tata Cara Anchor Bukti

Berlaku untuk seluruh kolom `Bukti` dan seluruh baris berbukti di seluruh berkas profil.

- Bentuk sah: `` `<path>#<simbol>` `` atau `` `<path>` `` telanjang bila buktinya adalah keberadaan berkas itu sendiri.
- **Nomor baris dilarang.** Baris bergeser tanpa suara pada tiap commit, dan profil yang menunjuk `file:42` tetap terbaca sah lama sesudah barisnya berpindah. Anchor bersimbol gagal berisik: saat simbolnya hilang, pencariannya nol hit dan cacatnya langsung terlihat.
- Satu anchor menunjuk satu tempat. Bukti yang menuntut dua lokasi ditulis dua anchor, bukan satu rentang.
- Anchor `<script>` dipakai untuk blok skrip berkas `.svelte` yang tidak punya ekspor bernama.

---

## Peta berkas

| Berkas | Isi | Konsumen utama |
|---|---|---|
| `index.json` | `project`, `stack`, `platform`, `framework`, `source_root`, `workspace`, `commit_convention` | `hooks/detect.py`, seluruh skill (resolusi adapter) |
| `stack.md` | framework & versi, bahasa & compiler flags, package manager, router, state, query, styling, UI library | `contract`, `ui-design`, `ux-design`, `code-reviewer`, `review` |
| `structure.md` | source root, path fitur, anatomi layer per direktori, shared components, definisi rute | `contract`, `plan`, `code-explorer` |
| `surface-map.md` | permukaan runtime: path kanonik · penanda pengenal kode · bukti | `code-explorer`, `plan`, `contract`, `code-implementor` |
| `invariants.md` | 6 invariant mutlak; pelanggaran = blocker, bukan gaya | `code-implementor`, `code-reviewer`, `contract-reviewer`, `plan`, `review` |
| `commands.md` | 4 perintah verifikasi + status baseline + cakupan yang TIDAK diperiksa, standar test | `plan`, `architect`, `review` |
| `layer-adoption.md` | tingkat adopsi 5 layer, aturan arsitektur, persisted state, shared HTTP client | `contract`, `contract-reviewer`, `code-reviewer`, `plan`, `review` |
| `visual.md` | token warna, tipografi, spacing & radius, batas platform | `ui-design` |
| `drift.md` | pola warisan → pola modern, tiap baris ber-resep `deteksi` | `plan` (Check P), `code-implementor`, `code-reviewer`, `review` |
| `manual-notes.md` | catatan manual user; **satu-satunya** berkas yang selamat dari tulis ulang REFRESH | semua |

Berkas yang datanya nihil tetap ditulis, berisi satu baris `tidak terdeteksi`. Berkas yang absen tidak dapat dibedakan dari instalasi profil yang gagal di tengah, dan gerbang menolak keduanya dengan pesan yang sama.

---

## 1. `.claude/profile/frontenddev/index.json`

Satu-satunya berkas mesin di profil. `hooks/detect.py` dan skrip prasyarat tiap skill (`skills/*/scripts/check_preconditions.py`) membaca field `stack` dari sini untuk memuat adapter; field yang hilang atau kosong mengunci gate.

```json
{
  "plugin": "frontenddev",
  "project": "<nama repo>",
  "stack": "<react-vite | react-native | sveltekit | svelte-vite>",
  "platform": "<React SPA (Vite) | React Native (Expo / Bare) | SvelteKit | Svelte SPA (Vite)>",
  "framework": "<React 19.0 + Vite 6.0 | Expo SDK 52 | SvelteKit 2.8 + Svelte 5.2>",
  "source_root": "src",
  "workspace": "<single | monorepo>",
  "target_app": "<kosong bila single; mis. apps/web pada monorepo>",
  "commit_convention": "<type>(<slug>): <deskripsi imperative>"
}
```

`plugin` selalu `"frontenddev"`: penanda kepemilikan — profil ber-`plugin` lain tidak pernah dibaca atau ditimpa skill frontenddev, juga dengan `force: true`. `stack` wajib salah satu dari empat nilai sah — ia yang menentukan `stacks/<stack-id>.md` mana yang dimuat seluruh skill hilir. `commit_convention` diturunkan dari `git log -n 20 --oneline` nyata, bukan dari asumsi Conventional Commits; repo non-git menulis `UNINITIALIZED (default conventional commits)`.

---

## 2. `.claude/profile/frontenddev/stack.md`

- **Platform**: `<React SPA (Vite) | React Native (Expo / Bare) | SvelteKit | Svelte SPA (Vite)>`
- **Framework Version**: React `<18.x | 19.x>` / Svelte `<4.x | 5.x>`, Vite `<5 | 6>`, Expo SDK `<51 | 52>`, SvelteKit `<2.x>`
- **Language**: TypeScript `<versi>` (Compiler: `strict: true`, `noImplicitAny: true`, `jsx: react-jsx` | `extends: ./.svelte-kit/tsconfig.json`)
- **Path Aliases**: `<@/* → src/* | $lib → src/lib | ~/* → src/*>`
- **Package Manager**: `<pnpm | yarn | npm | bun>` (Lockfile: `pnpm-lock.yaml | yarn.lock | package-lock.json | bun.lockb`)
- **Router**: `<React Router | TanStack Router | Expo Router | React Navigation | SvelteKit file-system | svelte-spa-router>`
- **State Management**: `<Zustand | Redux Toolkit | Jotai | rune $state module | svelte/store | Context>`
- **Query Layer**: `<TanStack Query v5 | TanStack Svelte Query | SvelteKit load + invalidate>`
- **Styling Engine**: `<Tailwind CSS v3/v4 | NativeWind v4 | StyleSheet | Tamagui | CSS Modules | scoped <style>>`
- **UI Component Library**: `<Radix UI / shadcn/ui | shadcn-svelte / bits-ui | React Native Paper | Gluestack | Custom UI>`

---

## 3. `.claude/profile/frontenddev/structure.md`

- **Source Root**: `src/` (atau `apps/web/src/`, `apps/mobile/src/`, `src/lib/` di SvelteKit)
- **Workspace**: `<Single App | Monorepo — daftar package aktif dan aplikasi utama>`
- **Features Path**: `src/features/<feature-name>/` (SvelteKit: `src/lib/features/<feature-name>/`)
  - `dto/`: Antarmuka payload backend (`*.dto.ts`)
  - `services/`: Modul transport HTTP murni (`*.service.ts`)
  - `<api layer>/`: `hooks/api/use*Query.ts` (React) | `api/*.query.ts` (Svelte) | `+page.ts` `load` (SvelteKit)
  - `<view-model>/`: `hooks/view-model/use*ViewModel.ts` (React) | `view-model/*.vm.ts` (Svelte)
  - `<controller>/`: `hooks/use*Page.ts` / `use*Screen.ts` (React) | `controllers/*.controller.svelte.ts` (Svelte)
  - `pages/` | `screens/` | `components/`: Komponen presentasi (`*Page.tsx`, `*Screen.tsx`, `*.svelte`)
- **Shared Components**: `src/components/ui/` (atau `packages/ui/src/components/`, `$lib/components/ui/`)
- **Route Definitions**: `src/routes/` | `app/**` | `src/navigation/` | `src/routes/**/+page.svelte`
- **Shared Utilities & Libs**: `src/lib/`, `src/utils/`, `src/constants/`

---

## 4. `.claude/profile/frontenddev/surface-map.md`

Kolom **Penanda Pengenal Kode** diisi dari `## Navigation recipes` adapter yang benar-benar berhit di repo; `code-explorer` menyisir dari kolom ini, bukan dari adapter.

| Surface Domain | Pola & Engine Runtime | Lokasi / Path Kanonik | Penanda Pengenal Kode | Bukti |
|---|---|---|---|---|
| **Routing & Navigation** | `<router dari stack.md>` | `src/navigation/`, `app/`, `src/routes/` | `Stack.Navigator`, `router.push`, `createBrowserRouter`, `+page.svelte`, `goto(` | `src/routes/+layout.svelte` |
| **Global State** | `<Zustand / RTK / rune module / store>` | `src/stores/` atau `src/features/*/store/` | `create<`, `createSlice`, `$state(`, `writable(` | `src/stores/useAuthStore.ts#useAuthStore` |
| **Data Fetching & Cache** | `<TanStack Query / load>` | `src/features/*/hooks/api/`, `src/lib/features/*/api/` | `useQuery`, `createQuery`, `export const load` | `src/features/order/hooks/api/useOrderQuery.ts#useOrderQuery` |
| **Query Key Factories** | `Centralized Array Keys` | `src/features/*/constants/queryKeys.ts` | `const ORDER_KEYS = { all: [...] }` | `src/features/order/constants/queryKeys.ts#ORDER_KEYS` |
| **UI & Theme Primitives** | `<Tailwind / NativeWind / bits-ui / Paper>` | `src/components/ui/`, `$lib/components/ui/` | `cn(...)`, `styled(...)`, `cva(...)` | `src/components/ui/button.tsx#Button` |
| **Form & Validation** | `<react-hook-form + Zod / superforms>` | `src/features/*/components/*Form.*` | `useForm`, `zodResolver(`, `superForm(` | `src/features/order/components/OrderForm.tsx#OrderForm` |
| **Storage & Session** | `<MMKV / AsyncStorage / LocalStorage / cookies>` | `src/services/storage.ts` | `storage.getItem`, `storage.set`, `event.cookies` | `src/services/storage.ts#storage` |
| **Shared HTTP Client** | `<Axios / Ky / fetch wrapper>` | `src/services/api.ts`, `$lib/api/client.ts` | `apiClient.interceptors.request`, `event.fetch` | `src/services/api.ts#apiClient` |
| **Framework Boundary** | `<env VITE_* / native module / $lib/server>` | `src/lib/server/`, `+page.server.ts`, `app.json` | `$env/static/private`, `useSafeAreaInsets(`, `import.meta.env` | `src/lib/server/db.ts` |

---

## 5. `.claude/profile/frontenddev/invariants.md`

Pelanggaran = blocker, bukan gaya.

1. **Zero DTO Leak to Presentation**: Komponen presentasi dilarang mengimpor interface `*DTO` langsung. Data wajib dipetakan melalui View-Model (React: `use*ViewModel`; Svelte: `to*UI()`) ke `*UI`.
2. **No Direct Data-Fetching in Presentation Components**: Dilarang memanggil `fetch`/`axios` di dalam efek komponen presentasi. Data fetching wajib via Controller dan API layer.
3. **Query Key Factory Array Discipline**: Query key wajib memakai array factory terpusat (`ORDER_KEYS.all`, `ORDER_KEYS.detail(id)`), dilarang raw string concatenation.
4. **Mandatory 6-State Branches for Async Screens**: Setiap layar asinkron wajib menyediakan state: Initial, Loading (Skeleton CLS-safe), Empty, Error + Retry Action, Ready, Mutating.
5. **Strict Design Token Theme Usage**: Styling wajib menggunakan token tema, dilarang arbitrary hardcoded styling.
6. **Framework Boundary Scoping**: `<sesuai adapter — React Native: SafeAreaInsets dan touch target ≥44dp; SvelteKit: nol import `$lib/server`/`$env/static/private` di client; SPA Vite: env hanya `VITE_*`>`.

Invariant yang repo-nya belum patuhi tetap ditulis sebagai invariant; ketidakpatuhannya dicatat di `drift.md`. Menurunkannya jadi "tidak berlaku" karena repo melanggarnya membuat profil melegalkan pelanggaran yang sedang berjalan.

---

## 6. `.claude/profile/frontenddev/commands.md`

| Perintah Terminal | Status Baseline Aktual | Error Pre-existing / Catatan | Cakupan yang TIDAK Diperiksa |
|---|---|---|---|
| `<typecheck dari ## Commands adapter>` | `OK (0 errors)` | - | `<salin dari adapter — mis. tidak memeriksa .svelte bila tsc saja>` |
| `<lint dari adapter>` | `OK (0 errors)` | - | Tidak memeriksa tipe / kebocoran memori efek |
| `<test dari adapter>` | `OK (14 passing)` | 0 failed | `<salin dari adapter — mis. Metro membuang tipe TS di React Native>` |
| `<build dari adapter>` | `OK` | - | `<salin dari adapter>` |

Status sah: `OK (...)`, `FAIL (<n> errors)`, `UNVERIFIED_ENV_NOT_READY`, `TIMEOUT / UNVERIFIED`, `tidak berlaku`.

- `typecheck-per-brief`: `<ya | tidak — alasan>` — nilai adapter, atau dinaikkan/diturunkan profil sesuai `stacks/_CONTRACT.md` §2 dengan durasi `typecheck` baseline sebagai alasan (`ya — svelte-check 8 dtk`); ia menjawab cara pemakaian, bukan status jalan, dan menang atas adapter.

> [!NOTE]
> Jika baseline awal memuat error pre-existing, kriteria verifikasi implementasi berbunyi "nol error baru dibanding baseline", bukan "bersih total". `UNVERIFIED_ENV_NOT_READY` bukan utang kode: ia menandai dependensi belum terpasang, dan menagihnya sebagai utang menghentikan rantai yang sebenarnya sehat.

**Standar test.** Framework & libraries: `<Vitest v2.x (Web) / Jest + jest-expo (Mobile)>`, `<@testing-library/react | @testing-library/react-native | @testing-library/svelte>`, MSW mock client di `src/mocks/`. Penamaan: `*.test.ts`, `*.test.tsx`, `*.spec.ts` di folder `__tests__/` atau bersebelahan. Catat juga apa yang **tidak** diuji: cakupan yang absen adalah batas klaim yang boleh dibuat verifikasi penutup.

---

## 7. `.claude/profile/frontenddev/layer-adoption.md`

```
[ Presentation ] ──► [ Controller ]
                          ├───► [ View-Model ] (DTO -> UI Props)
                          └───► [ API layer ] (query / mutation / load)
                                     └───► [ HTTP Service & DTO ]
```

| Layer | Penamaan | Tingkat adopsi | Bukti |
|---|---|---|---|
| **Controller** | `<use*Page / use*Screen \| create*Controller>` | Tinggi pada fitur modular baru (5 dari 7 fitur) | `src/features/order/hooks/useOrdersPage.ts#useOrdersPage` |
| **View-Model** | `<use*ViewModel / use*Rows \| to*UI()>` | Wajib untuk seluruh fitur baru | `src/features/order/hooks/view-model/useOrderViewModel.ts#useOrderViewModel` |
| **API layer** | `<useQuery / useMutation \| createQuery / createMutation \| load>` | 100% pada pemanggilan endpoint | `src/features/order/hooks/api/useOrderQuery.ts#useOrderQuery` |
| **HTTP Service Layer** | Modul transport murni di `services/` | 100% | `src/services/api.ts#apiClient` |
| **DTO Isolation** | DTO diisolasi dari presentasi via View-Model | invariant, nol pengecualian | `src/features/order/dto/order.dto.ts#OrderResponseDTO` |

Aspek yang terbelah tanpa mayoritas dicatat di sini hanya sesudah user memilih gayanya di Phase 3; gaya yang kalah pindah ke `drift.md` dengan `bukti user`.

**Persisted state & storage.** Storage engine: `<MMKV (Mobile) / LocalStorage (Web) / cookies (SvelteKit server) / SecureStore (auth token)>`. Registered keys: `@auth_token`, `@refresh_token`, `@user_preferences`, `@draft_form_state` — daftar ini yang mencegah brief baru menabrak key yang sudah dipakai, dan tabrakannya tidak pernah gagal saat compile.

**Shared HTTP client.** `<Axios instance | ky | fetch wrapper>` di `src/services/api.ts` dengan request interceptor (Bearer token) dan response interceptor (auto-refresh token pada 401). Base URL via env variable (`VITE_*` / `PUBLIC_*` / `EXPO_PUBLIC_*`).

---

## 8. `.claude/profile/frontenddev/visual.md`

- **Color Palette Tokens**: Primary `primary-500` (`#2563EB`), Secondary `secondary-500` (`#4F46E5`), Background `bg-background` (`#FFFFFF`), Surface `bg-card` (`#F8FAFC`), Semantic (`success`, `danger`, `warning`, `info`), Text `text-foreground` (`#0F172A`), `text-muted` (`#64748B`).
- **Typography**: Heading `Inter`, Body `Inter`, Monospace `JetBrains Mono`.
- **Spacing & Radius**: Spacing `4px (1)`, `8px (2)`, `12px (3)`, `16px (4)`, `24px (6)`, `32px (8)`; Radius `rounded-sm (4px)`, `rounded-md (8px)`, `rounded-lg (12px)`, `rounded-full (9999px)`.
- **Platform**: `<React Native: SafeAreaInsets pada root layout; minimum touch target 44x44 dp | Web: breakpoint 640/768/1024, focus-visible ring>`.

Nilai disalin **persis** dari konfigurasi tema, bukan dari ingatan atau dari tampilan aplikasi.

---

## 9. `.claude/profile/frontenddev/drift.md`

Format baris wajib: `- <pola warisan> (<sebaran>) → <pola modern> · deteksi \`<pola grep> @ <glob>\` · bukti <file#simbol>`. Resep `deteksi` ditulis dalam **satu** span backtick yang memuat pola dan glob dipisah ` @ `; memecahnya jadi dua span membuat `validate_briefs.py` Check P tidak mengenalinya dan baris itu diam-diam tidak pernah ditegakkan. Resep `deteksi` wajib berhit minimal sekali saat baris ditulis; nol hit berarti pola sudah punah dan barisnya batal. Pada REFRESH tiap resep dijalankan ulang dan vonisnya `[MASIH HIDUP — n hit]` atau `[PUNAH — 0 hit]`; baris `PUNAH` dicabut hanya atas persetujuan user, bukan diam-diam oleh pemindaian.

Gaya yang kalah dalam wawancara pola terbelah (Phase 3) masuk ke sini dengan `bukti user` menggantikan `<file#simbol>`, karena yang menjadikannya warisan adalah keputusan tim, bukan temuan pemindaian.

- Query key string concat (3 fitur) → array factory `ORDER_KEYS.detail(id)` · deteksi `queryKey: ' @ src/features/**/hooks/api/*.ts` · bukti `src/features/auth/hooks/api/useLogin.ts#useLogin`
- Fetch di efek komponen presentasi (2 fitur) → API layer via query library di Controller · deteksi `axios.get @ src/features/**/pages/*.tsx` · bukti `src/features/report/pages/ReportPage.tsx#ReportPage`
- State lokal ganda tanpa skema validasi (2 fitur) → `<react-hook-form + zodResolver | superforms>` · deteksi `useState<.*Form @ src/features/**/*.tsx` · bukti `src/features/order/components/OrderForm.tsx#OrderForm`
- `$:` dan `export let` pada berkas baru (4 berkas) → rune `$state`/`$derived` · deteksi `^\s*\$: @ src/lib/**/*.svelte` · bukti `src/lib/features/order/OrderList.svelte#<script>`

---

## 10. `.claude/profile/frontenddev/manual-notes.md`

Catatan manual user. Berkas ini **satu-satunya** bagian profil yang dipertahankan apa adanya saat mode `REFRESH` menulis ulang profil; sembilan berkas lain lahir kembali dari pemindaian segar. Isi dengan satu baris `—` bila belum ada catatan.

Dua tanda yang ditulis `frontenddev:profile` sendiri juga mendarat di sini, dan **bukan** catatan user — jangan hapus keduanya saat menambahkan catatan:

- `[BELUM TERVALIDASI USER — <tanggal>]` bila Phase 3 dilewati (`interview: false` atau user tidak menjawab). Tanpa tanda ini, profil yang gaya terbelahnya diputuskan sepihak terbaca sama persis dengan profil yang gayanya benar-benar disepakati tim.
- `[SAMPEL DIPERSEMPIT — <target_app>]` bila `strict_scan: false` membatasi pemindaian ke satu sub-aplikasi, supaya REFRESH berikutnya tahu angka sebarannya tidak menyeluruh.

—
