# Stack adapter — `svelte-vite`

Svelte SPA murni di atas Vite tanpa SvelteKit (Svelte 5 runes, dengan catatan untuk Svelte 4 store). Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `package.json` di root atau satu tingkat workspace.

- **Penanda wajib**: `svelte` di `devDependencies`/`dependencies` bersama `@sveltejs/vite-plugin-svelte` dan `vite`, **tanpa** `@sveltejs/kit`.
- **Pengecualian**: `next` hadir → bukan stack plugin ini; hentikan. `@sveltejs/kit` hadir → `sveltekit`.
- **Pembuktian**: `grep -E '"svelte"\s*:' package.json && ! grep -q '"@sveltejs/kit"' package.json && ls vite.config.*`.
- **Entry point**: `src/main.ts` yang memanggil `mount(App, { target })` (Svelte 5) atau `new App({ target })` (Svelte 4); `index.html` di root.
- **Versi runtime**: Svelte dari `devDependencies.svelte` (`^5` → runes; `^4` → store `$:`), Node dari `.nvmrc`/`engines`.
- **Package manager aktif**: lockfile — `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `bun.lockb`.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| Router | `svelte-routing`, `svelte-spa-router`, `@mateothegreat/svelte5-router`, `svelte-navigator`; atau router manual berbasis `history` |
| Query / cache | `@tanstack/svelte-query`, `swr`-like manual di store |
| State global | rune `$state` di modul `.svelte.ts`, `svelte/store` (`writable`, `derived`) |
| Styling | `tailwindcss`, `<style>` scoped bawaan, `unocss`, `sass` |
| UI primitives | `bits-ui`, `shadcn-svelte`, `flowbite-svelte`, `@skeletonlabs/skeleton` |
| Form & validasi | `zod`, `valibot`, `felte`, `svelte-forms-lib` |
| HTTP client | `fetch` bawaan, `axios`, `ky`, `ofetch` |
| Storage | `localStorage`/`sessionStorage`, `idb` |
| Test runner | `vitest`, `@testing-library/svelte`, `@playwright/test`, `msw` |
| Config | `vite.config.*` (`svelte()` plugin), `svelte.config.js` (opsional, `vitePreprocess`), `tsconfig.json` (extends `@tsconfig/svelte`), `eslint.config.*` |

Batas framework: tidak ada server/client boundary — semuanya client; batasnya adalah `import.meta.env.VITE_*` dan guard rute milik router pilihan repo.

## Commands

| Perintah | Nilai |
|---|---|
| typecheck | `<pm> run check`, yaitu `svelte-check --tsconfig ./tsconfig.json` |
| lint | `<pm> run lint`, atau `npx eslint .` dengan `eslint-plugin-svelte` |
| test | `<pm> test`, lazim `vitest run` |
| test-single | `npx vitest run <berkas> -t "<nama>"` |
| build | `<pm> run build` (`vite build`) |
| typecheck-per-brief | `tidak` — `svelte-check` menyisir seluruh berkas `.svelte` tiap jalan; `profile` boleh menaikkannya ke `ya` bila durasi terukur di repo itu di bawah ~15 detik |

`<pm>` diambil dari lockfile. Skrip di `package.json` menang atas perintah generik di atas.

**Cakupan yang TIDAK diperiksa**:

- `typecheck`: `svelte-check` menilai `.svelte` dan `.ts`; `tsc --noEmit` **saja tidak memeriksa `.svelte`** — dilarang menggantinya.
- `lint`: tidak memeriksa tipe; warning reaktivitas dan a11y datang dari compiler Svelte saat `check`/`build`, bukan dari ESLint.
- `test`: Vitest men-transpile tanpa typecheck; komponen diuji di jsdom — perilaku router nyata dan `history` tidak tertangkap.
- `build`: `vite build` tidak menjalankan `svelte-check` kecuali skrip `build` menyertakannya.

## Layer taxonomy

| Layer | Penamaan | Letak lazim | Ekspor utama |
|---|---|---|---|
| DTO | `<entitas>.dto.ts` | `src/features/<feat>/dto/` | `interface *RequestDTO`, `*ResponseDTO` |
| Service | `<entitas>.service.ts` | `src/features/<feat>/services/` | objek `<entitas>Service` |
| API layer | `<entitas>.query.ts` (TanStack Svelte Query) | `src/features/<feat>/api/` | `create<Entitas>Query`, `<ENTITAS>_KEYS` |
| View-Model | `<entitas>.vm.ts` (fungsi murni) atau `<entitas>.vm.svelte.ts` (rune) | `src/features/<feat>/view-model/` | `to<Entitas>UI()` + `interface *UI` |
| Controller | `<layar>.controller.svelte.ts` | `src/features/<feat>/controllers/` | `create<Layar>Controller()` |
| Presentation | `<Layar>Page.svelte`, `<Bagian>.svelte` | `src/features/<feat>/pages/`, `components/` | komponen |
| Test | `*.test.ts` | bersebelahan atau `__tests__/` | — |

Potongan per layer:

```typescript
// Service — services/order.service.ts
export const orderService = {
  list: async (filters: OrderFiltersDTO): Promise<OrderResponseDTO[]> =>
    (await apiClient.get<OrderResponseDTO[]>('/api/v1/orders', { searchParams: filters })).data,
};

// View-Model — view-model/order.vm.ts (fungsi murni, diuji tanpa render)
export interface OrderRowUI { id: string; title: string; amountLabel: string; badge: { label: string; tone: 'success' | 'muted' } }
export const toOrderRowsUI = (dtos: OrderResponseDTO[] | undefined): OrderRowUI[] =>
  (dtos ?? []).map((d) => ({ id: d.id, title: d.title, amountLabel: formatIDR(d.amount_cents),
    badge: d.status === 'ACTIVE' ? { label: 'Aktif', tone: 'success' } : { label: d.status, tone: 'muted' } }));

// Controller — controllers/order-list.controller.svelte.ts
export function createOrderListController() {
  let filters = $state<OrderFiltersDTO>({ status: 'all' });
  const query = createOrderListQuery(() => filters);
  const rows = $derived(toOrderRowsUI(query.data));
  return { get rows() { return rows; }, get isLoading() { return query.isLoading; }, get isError() { return query.isError; },
    refetch: () => query.refetch(), setStatus: (s: string) => { filters = { ...filters, status: s }; } };
}
```

Jebakan stack saat menulis kode di layer ini:

1. **Rune `$state`/`$derived` hanya di `.svelte` dan `.svelte.ts`.** Di `.ts` biasa compiler menolak; state yang diekspor dari modul wajib lewat getter/objek, bukan destrukturisasi (nilai primitif kehilangan reaktivitas).
2. **`$effect` bersubscription wajib mengembalikan cleanup** (Svelte 4: `onDestroy`). Listener `window` menumpuk tiap komponen dimount ulang oleh router.
3. **Parameter reaktif ke query diberikan sebagai getter/fungsi**, bukan nilai; nilai langsung membekukan query pada filter pertama.
4. **Side-effect UI (`navigate`, toast) dilarang di `createMutation`.** Hidup di Controller.
5. **Router pilihan repo menentukan cara baca param.** Jangan campur `svelte-routing` (`<Route path="/orders/:id" let:params>`) dengan `svelte-spa-router` (`#/orders/:id`, `params` prop); cek profil.
6. **Env hanya lewat `import.meta.env.VITE_*`.** `process.env` tidak ada di bundle.
7. **Alias `@/*` atau `$lib` wajib sinkron di `tsconfig.paths` dan `vite.config.resolve.alias`**; tanpa SvelteKit tidak ada yang mengisinya otomatis.

Hygiene penutup unit (`agents/code-implementor.md` Fase 1): nol `any`, tipe balikan controller/vm eksplisit, nol `console.log`, import lewat alias `tsconfig`, nol side-effect di API layer, cleanup pada `$effect`/`onDestroy`, `.svelte` mengonsumsi `*UI` alih-alih DTO. `package.json`, lockfile, `vite.config.*`, `svelte.config.js`, dan `tsconfig.json` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Route / Presentation | `Grep -n "<Route \|<Router\|Router(\|routes = \{"`; `Glob` `src/features/**/pages/*.svelte` |
| Controller | `Grep -n "export (function\|const) create\w+Controller\b"`; `Glob` `**/*.controller.svelte.ts` |
| View-Model | `Grep -n "export (function\|const) to\w+UI\b\|export interface \w+UI\b"`; `Glob` `**/*.vm*.ts` |
| API layer | `Grep -n "createQuery\(\|createMutation\(\|createInfiniteQuery\("` |
| Cache & mutasi | `Grep -n "export const \w+_KEYS = \{\|onMutate:\|onSettled:\|invalidateQueries"` |
| Service transport | `Grep -n "axios\.create\|apiClient\.(get\|post\|put\|patch\|delete)\|ky\.create"` |
| DTO | `Grep -n "export (interface\|type) \w+(DTO\|Response\|Request)\b"` |
| Kebocoran DTO ke presentasi | `Grep -n "from ['\"].*dto" --glob "*.svelte"` |
| State global | `Grep -n "\$state(\|writable(\|readable(\|derived("` di `**/*.svelte.ts` dan `stores/` |
| Form & skema | `Grep -n "= z\.object\(\{\|createForm(\|safeParse("` |
| Batas framework | `Grep -n "import\.meta\.env\.\|navigate(\|push(\|location\.hash"` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35`; untuk `.svelte` mulai dari `<script>` sampai tag penutupnya bila ≤50 baris.

## Review checklist

#### `layer-boundaries`

- **`import ... from '.../dto/...'` di `.svelte`.** P1. Grep: `Grep -n "from.*dto" --glob "*.svelte"`.
- **`fetch(`/`axios.` langsung di `<script>` komponen.** P1. Lepas dari cache/invalidasi.
- **Logika query di komponen `Route`/`pages/*.svelte` alih-alih Controller.** P2.

#### `data-flow`

- **Field DTO snake_case dipakai di template.** P2. View-Model dilewati.

#### `api-layer`

- **`navigate(`/`push(` atau toast di `api/`.** P1. Grep: `Grep -n "navigate(\|push(\|toast" src/features/**/api/`.
- **Parameter query diberikan sebagai nilai, bukan getter.** P2. Query membeku pada nilai awal.

#### `state-scope`

- **`createQuery(` di komponen baris/kartu.** P2.
- **`writable()`/`$state` global memegang state form satu halaman.** P2.

#### `ui-states`

- **Error state tanpa `onRetry`.** P2.
- **`{#await}` tanpa `{:catch}`.** P2.
- **Loading merender kosong alih-alih skeleton berdimensi.** P2.

#### `platform`

- **`process.env.*` di kode.** P1. Grep: `Grep -n "process\.env\." src/`.
- **Dua library router dipakai bersamaan.** P2. Param dibaca dari sumber berbeda.
- **Alias hanya di salah satu `tsconfig`/`vite.config`.** P2.

#### `performance`

- **`$effect` dengan listener/timer tanpa `return`.** P2.
- **Kalkulasi berat di template alih-alih `$derived`.** P3.

## UI & navigation surface

- **Routing**: bergantung library — `svelte-routing`: `<Route path="/orders/:id" let:params>` dengan `navigate()`; `svelte-spa-router`: hash `#/orders/:id`, `push()`, `params` prop, `wrap()` untuk guard; router manual: tabel `routes` + `history.pushState`. Rute ditulis ke `FLOW.md` persis seperti deklarasinya; library yang dipakai dibaca dari profil.
- **Deep-link**: URL (atau hash) adalah deep-link; state yang bertahan refresh dinyatakan di query string (`?q=`, `?page=`) dan dibaca lewat `URLSearchParams(location.search)` atau helper router (`querystring` store di `svelte-spa-router`).
- **Sinkronisasi state URL**: `navigate(url, { replace: true })` / `replace()` untuk search/sort; `push` untuk filter/page; parsing dan default nilai ditulis eksplisit di `FLOW.md`.
- **Kembali & batal**: tombol back browser; dirty guard lewat `beforeunload` untuk tutup tab dan guard router (`wrap({ conditions })` di `svelte-spa-router`, atau cek `dirty` sebelum `navigate`). Modal ditutup `Esc` dan klik backdrop.
- **Platform**: breakpoint mobile <640px, tablet 768–1023px, desktop ≥1024px; fokus keyboard terlihat; dialog untuk konfirmasi destruktif, drawer untuk form panjang; `App.svelte` memegang shell header/footer.
- **Design token**: `tailwind.config.*` atau CSS variables di `src/app.css`; komponen bersama di `src/lib/components/ui/` atau `src/components/ui/`.
- **Aksesibilitas**: `aria-label` pada tombol ikon, `aria-live="polite"` untuk pesan asinkron; warning a11y compiler dilarang dibungkam dengan `<!-- svelte-ignore a11y_* -->`.

## Failure signatures

| Kategori error | Penyebab umum | Strategi resolusi yang sah |
|---|---|---|
| **`svelte-check` TS2322 / TS2345** | Tipe DTO berbeda dari controller/vm | Sesuaikan tipe lokal ke `CONTRACT.md` |
| **`$state` di `.ts` / `state_referenced_locally`** | Rune di berkas non-`.svelte.ts`, atau state didestrukturisasi | Ganti ekstensi; ekspor getter |
| **`Cannot find module '@/...'`** | Alias belum di `tsconfig.paths` dan `vite.config.resolve.alias` | Periksa keduanya |
| **Query membeku pada filter awal** | Parameter query diberikan sebagai nilai | Berikan getter `() => filters` |
| **a11y warning compiler** | Elemen non-interaktif diberi `onclick` | Pakai `<button>`; dilarang `svelte-ignore` |
| **Vitest `render` gagal `mount is not a function`** | Versi `@testing-library/svelte` tidak cocok Svelte 5 | Laporkan blocker; dilarang mengubah `package.json` tanpa brief |
| **Router param `undefined` di test** | Komponen dirender tanpa `Router` pembungkus | Bungkus dengan `Router` di test, atau uji Controller langsung |
| **`vite build` `Rollup failed to resolve import`** | Alias atau path salah | Perbaiki alias di `vite.config.*`; jangan tambahkan `external` |
| **Tailwind class tidak berefek** | Class di luar `content` glob | Periksa `content` di `tailwind.config.*` |
| **`window is not defined` di test** | Test env bukan jsdom | Pastikan `environment: 'jsdom'` di `vite.config` test; jangan guard kode produksi untuk test |
