# Stack adapter — `react-vite`

React SPA di atas Vite (termasuk CRA yang sudah bermigrasi). Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `package.json` di root atau satu tingkat workspace (`apps/*`, `packages/*`).

- **Penanda wajib**: `react` dan `react-dom` di `dependencies`, plus `vite` di `devDependencies` atau berkas `vite.config.{ts,js,mjs}`.
- **Pengecualian**: `next` hadir → bukan stack ini dan bukan stack plugin ini; hentikan. `react-native` atau `expo` hadir → `react-native`.
- **Pembuktian**: `grep -E '"(react|react-dom)"\s*:' package.json && ls vite.config.*`.
- **Entry point**: `src/main.tsx` (atau `src/index.tsx`) yang memanggil `createRoot`; `index.html` di root.
- **Versi runtime**: `engines.node`, `.nvmrc`, `volta.node`; React dari `dependencies.react`.
- **Package manager aktif**: lockfile — `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `bun.lockb`.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| Router | `react-router-dom`, `@tanstack/react-router`, `wouter` |
| Query / cache | `@tanstack/react-query`, `swr`, `@apollo/client` |
| State global | `zustand`, `@reduxjs/toolkit`, `jotai`, `valtio`, `mobx` |
| Styling | `tailwindcss`, `@emotion/react`, `styled-components`, CSS Modules (`*.module.css`), `@vanilla-extract/css` |
| UI primitives | `@radix-ui/*`, `shadcn` (`components/ui/`), `@mui/material`, `@chakra-ui/react` |
| Form & validasi | `react-hook-form`, `zod`, `yup`, `valibot` |
| HTTP client | `axios`, `ky`, `ofetch` |
| Storage | `localStorage`/`sessionStorage` (bawaan), `idb`, `dexie` |
| Test runner | `vitest`, `jest`, `@testing-library/react`, `@playwright/test`, `cypress`, `msw` |
| Config | `vite.config.*`, `tsconfig.json` (`paths`), `tailwind.config.*`, `eslint.config.*` |

Batas framework: tidak ada server/client boundary; batasnya adalah `import.meta.env` (hanya `VITE_*` yang terekspos) dan loader router bila memakai TanStack Router / React Router data APIs.

## Commands

| Perintah | Nilai |
|---|---|
| typecheck | `<pm> run typecheck`, atau `npx tsc --noEmit -p tsconfig.json` (atau `tsconfig.app.json` pada template Vite terbaru) |
| lint | `<pm> run lint`, atau `npx eslint .` |
| test | `<pm> test`, lazim `vitest run` |
| test-single | `npx vitest run <berkas> -t "<nama>"` / `npx jest <pola>` |
| build | `<pm> run build` (`vite build`, sering didahului `tsc -b`) |
| typecheck-per-brief | `ya` — `tsc --noEmit` inkremental di SPA Vite hitungan detik; galat import tak terselesaikan unit hulu terlihat sebelum unit hilir mendarat |

`<pm>` diambil dari lockfile. Skrip di `package.json` menang atas perintah generik di atas.

**Cakupan yang TIDAK diperiksa**:

- `typecheck`: tidak memeriksa runtime invariant, payload jaringan, maupun berkas yang di-`exclude` `tsconfig` (sering `*.test.tsx` di `tsconfig.app.json`).
- `lint`: tidak memeriksa tipe kecuali rule type-aware aktif; `react-hooks/exhaustive-deps` hanya berjalan bila plugin `eslint-plugin-react-hooks` terpasang.
- `test`: Vitest men-transpile lewat esbuild tanpa typecheck — test hijau bukan bukti tipe hijau.
- `build`: `vite build` tidak menjalankan `tsc` kecuali skrip `build` menyertakannya.

## Layer taxonomy

| Layer | Penamaan | Letak lazim | Ekspor utama |
|---|---|---|---|
| DTO | `<entitas>.dto.ts` | `src/features/<feat>/dto/` | `interface *RequestDTO`, `*ResponseDTO` |
| Service | `<entitas>.service.ts` | `src/features/<feat>/services/` | objek `<entitas>Service` |
| API layer | `use<Entitas>Query.ts`, `use<Aksi>Mutation.ts` | `src/features/<feat>/hooks/api/` | hook TanStack Query + `<ENTITAS>_KEYS` |
| View-Model | `use<Entitas>ViewModel.ts` | `src/features/<feat>/hooks/view-model/` | hook + `interface *UI` |
| Controller | `use<Layar>Page.ts` | `src/features/<feat>/hooks/` | hook `use*Page` |
| Presentation | `<Layar>Page.tsx`, `<Bagian>.tsx` | `src/features/<feat>/pages/`, `components/` | komponen fungsi |
| Test | `*.test.ts(x)` | `__tests__/` atau bersebelahan | — |

Potongan per layer:

```typescript
// API layer — hooks/api/useUserQuery.ts
export const USER_KEYS = {
  all: ['users'] as const,
  detail: (id: string) => [...USER_KEYS.all, 'detail', id] as const,
};
export const useUserQuery = (id: string) =>
  useQuery({ queryKey: USER_KEYS.detail(id), queryFn: () => userService.getProfile(id), staleTime: 5 * 60_000 });

// View-Model — hooks/view-model/useUserViewModel.ts
export interface UserItemUI { id: string; fullName: string; formattedBalance: string }
export const useUserViewModel = (dto?: UserResponseDTO): UserItemUI | null =>
  useMemo(() => (dto ? { id: dto.id, fullName: `${dto.first_name} ${dto.last_name}`.trim(),
    formattedBalance: formatIDR(dto.balance_cents) } : null), [dto]);

// Controller — hooks/useUserProfilePage.ts
export const useUserProfilePage = (userId: string) => {
  const { data, isLoading, isError, refetch } = useUserQuery(userId);
  const user = useUserViewModel(data);
  const [isEditOpen, setEditOpen] = useState(false);
  const handleOpenEdit = useCallback(() => setEditOpen(true), []);
  return { user, isLoading, isError, refetch, isEditOpen, handleOpenEdit };
};
```

Jebakan stack saat menulis kode di layer ini:

1. **`useEffect` bersubscription wajib mengembalikan cleanup.** Listener `window`, `setInterval`, dan subscribe store yang tidak dilepas menumpuk tiap mount ulang route.
2. **Dependency array lengkap.** Variabel yang dipakai di dalam `useEffect`/`useCallback`/`useMemo` tetapi absen dari array memberi closure basi; `exhaustive-deps` menangkapnya hanya bila plugin terpasang.
3. **Mutasi state di badan komponen memicu render tak berhingga.** `setState` dan `mutate()` hanya di handler atau efek.
4. **Side-effect UI dilarang di `onSuccess` hook query.** `navigate()` dan `toast()` hidup di Controller; hook API yang membawanya tidak bisa dipakai ulang di dialog lain.
5. **Env hanya lewat `import.meta.env.VITE_*`.** `process.env` tidak ada di bundle browser Vite.
6. **Alias `@/*` wajib sinkron di `tsconfig.paths` dan `vite.config.resolve.alias`.** Salah satu absen → typecheck hijau tetapi build merah, atau sebaliknya.

Hygiene penutup unit (`agents/code-implementor.md` Fase 1): nol `any`, return type hook eksplisit, nol `console.log`, import lewat alias `tsconfig`, nol side-effect di dalam hook TanStack Query, cleanup pada `useEffect` bersubscription, komponen mengonsumsi `*UI` alih-alih DTO. `package.json`, lockfile, `vite.config.*`, dan `tsconfig*.json` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Route / Presentation | `Glob` `src/features/**/pages/*.tsx`; `Grep -n "createBrowserRouter\|<Route \|createRoute("` |
| Controller | `Grep -n "export (const\|function) use\w+(Page\|Controller)\b"` |
| View-Model | `Grep -n "export (const\|function) use\w+(ViewModel\|Rows)\b"` |
| API layer | `Grep -n "useQuery\(\{\|useMutation\(\{\|useInfiniteQuery\(\{"` |
| Cache & mutasi | `Grep -n "export const \w+_KEYS = \{\|onMutate:\|onSuccess:\|onSettled:\|invalidateQueries"` |
| Service transport | `Grep -n "axios\.create\|apiClient\.(get\|post\|put\|patch\|delete)\|ky\.create"` |
| DTO | `Grep -n "export (interface\|type) \w+(DTO\|Response\|Request)\b"` |
| Kebocoran DTO ke presentasi | `Grep -n "from ['\"].*dto" src/features/**/pages/ src/features/**/components/` |
| State global | `Grep -n "create<\|createSlice\(\{\|atom\(\|createContext<"` |
| Form & skema | `Grep -n "useForm<\|zodResolver(\|= z\.object\(\{"` |
| Batas framework | `Grep -n "import\.meta\.env\.\|loader:\|useLoaderData\("` |
| Hook kustom bertipe balikan | `grep -rnE "^export (const\|function) use[A-Za-z0-9]+\s*=\s*\(.*\)\s*:\s*[A-Za-z0-9]+"` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35`.

## Review checklist

#### `layer-boundaries`

- **`import ... from '../dto/...'` di dalam `*.tsx` presentasi.** P1. Perubahan skema backend merambat ke markup. Grep: `Grep -n "from.*dto" src/features/**/{pages,components}/`.
- **`axios`/`fetch` dipanggil di `useEffect` komponen.** P1. Fetch lepas dari cache dan invalidasi. Grep: `Grep -n "fetch(\|axios\." src/features/**/{pages,components}/`.

#### `data-flow`

- **Field DTO snake_case dipakai langsung di markup.** P2. Tanda View-Model dilewati.

#### `api-layer`

- **`navigate(`, `router.`, atau `toast` di `hooks/api/`.** P1. Grep: `Grep -n "navigate(\|toast\.\|useNavigate(" src/features/**/hooks/api/`.
- **Mutasi tanpa `invalidateQueries` di `onSettled`.** P2. Daftar tetap basi sesudah tulis.

#### `state-scope`

- **`useQuery(` di dalam `components/` kartu/baris.** P2. Cascade fetch per item. Grep: `Grep -n "useQuery(" src/features/**/components/`.
- **`useState` untuk data yang sudah ada di cache query.** P3. Dua sumber kebenaran.

#### `ui-states`

- **`isError` dirender tanpa `onRetry`/`refetch`.** P2.
- **`isLoading` merender `null` alih-alih skeleton berdimensi.** P2. Layout shift saat data tiba.

#### `platform`

- **`process.env.*` di kode browser.** P1. `undefined` di bundle Vite. Grep: `Grep -n "process\.env\." src/`.
- **Alias hanya di salah satu `tsconfig`/`vite.config`.** P2. Build dan typecheck saling bertentangan.

#### `performance`

- **`useEffect` dengan `addEventListener`/`setInterval` tanpa `return`.** P2. Grep: `Grep -n "addEventListener\|setInterval" src/features/`, cek ada `return () =>`.
- **Kalkulasi list berat di badan komponen tanpa `useMemo`.** P3.

## UI & navigation surface

- **Routing**: React Router — deklarasi di `src/routes/` atau `createBrowserRouter([...])`, segmen dinamis `/:id`, search params via `useSearchParams()`; TanStack Router — `createRoute({ path: '/orders/$id' })` dengan `validateSearch` bertipe. Rute ditulis ke `FLOW.md` persis seperti deklarasinya, bukan diasumsikan.
- **Deep-link**: URL browser adalah deep-link; setiap state yang harus bertahan refresh (filter, page, modal terbuka) dinyatakan di query string: `?q=`, `?page=`, `?modal=detail&item_id=`.
- **Sinkronisasi state URL**: `setSearchParams(next, { replace: true })` untuk search/sort (tanpa menambah history), `push` untuk filter/page.
- **Kembali & batal**: tombol back browser; dirty guard lewat `useBlocker` (React Router 6.4+) atau `beforeunload` untuk tutup tab. Modal ditutup `Esc` dan klik backdrop.
- **Platform**: breakpoint mobile <640px, tablet 768–1023px, desktop ≥1024px; fokus keyboard wajib terlihat (`focus-visible:ring-2`); dialog di tengah untuk konfirmasi destruktif, drawer samping untuk form panjang.
- **Design token**: `tailwind.config.*` (`theme.extend.colors`) atau CSS variables di `src/styles/`; token semantik `primary`, `muted-foreground`, `destructive`.
- **Aksesibilitas**: `aria-label` pada tombol ikon, `aria-live="polite"` untuk pesan asinkron, kontras teks ≥4.5:1.

## Failure signatures

| Kategori error | Penyebab umum | Strategi resolusi yang sah |
|---|---|---|
| **TS2322 / TS2345 type mismatch** | Interface DTO berbeda tipe dari variabel di hook | Sesuaikan tipe lokal ke kontrak DTO di `CONTRACT.md`; jangan ubah tipe backend |
| **TS2307 Cannot find module** | Path alias `@/*` belum di `tsconfig.paths` atau `vite.config.resolve.alias`; barrel export hilang | Periksa keduanya, pastikan simbol diekspor |
| **`react-hooks/exhaustive-deps`** | Variabel di efek hilang dari dependency array | Tambahkan dependensi atau bungkus helper dengan `useCallback` |
| **Vitest async timeout** | Pemanggilan API asinkron tidak ditunggu | `await waitFor(() => ...)` atau `findByRole` dari Testing Library |
| **`act()` warning** | Mutasi state di luar siklus pengujian | Bungkus handler dengan `await act(async () => ...)` |
| **Maximum update depth exceeded** | `setState`/`mutate()` di badan komponen | Pindahkan ke `useEffect` atau handler Controller |
| **Zod parse error di test form** | `defaultValues` form tidak cocok skema | Sinkronkan `defaultValues` dengan tipe inferensi Zod |
| **MSW unhandled request** | Endpoint service belum ada di handler mock | Tambahkan handler di berkas test lokal terkait |
| **`vite build` gagal `Rollup failed to resolve import`** | Import path atau alias tidak dikenal bundler | Perbaiki alias di `vite.config.*`; jangan tambahkan `external` untuk menyembunyikannya |
| **Tailwind class tidak berefek** | Class di luar `content` glob atau typo utility | Periksa `content` di `tailwind.config.*` dan token di profil |
