# Stack adapter — `sveltekit`

SvelteKit (Svelte 5 runes, dengan catatan untuk Svelte 4 store). Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `package.json` di root atau satu tingkat workspace.

- **Penanda wajib**: `@sveltejs/kit` di `devDependencies` (atau `dependencies`) bersama `svelte`, plus `svelte.config.js` dan `vite.config.*`.
- **Pengecualian**: `next` hadir → bukan stack plugin ini; hentikan.
- **Pemutus terhadap `svelte-vite`**: `@sveltejs/kit` hadir → `sveltekit`, apa pun plugin Vite lainnya.
- **Pembuktian**: `grep -E '"@sveltejs/kit"\s*:' package.json && ls svelte.config.js`.
- **Entry point**: `src/routes/+layout.svelte` dan `src/routes/+page.svelte`; `src/app.html` sebagai shell; `src/hooks.server.ts` untuk middleware server.
- **Versi runtime**: Svelte dari `devDependencies.svelte` (`^5` → runes; `^4` → store `$:`), Node dari `.nvmrc`/`engines`.
- **Package manager aktif**: lockfile — `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `bun.lockb`.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| Router | bawaan file-system `src/routes/**` (`+page`, `+layout`, `+server`) |
| Query / cache | `@tanstack/svelte-query`; atau `load` function + `invalidate()` bawaan |
| State global | rune `$state` di modul `.svelte.ts`, `svelte/store` (`writable`), `page` store dari `$app/stores` / `$app/state` |
| Styling | `tailwindcss`, `<style>` scoped bawaan, `unocss`, `sass` |
| UI primitives | `bits-ui`, `shadcn-svelte` (`$lib/components/ui/`), `skeleton`, `flowbite-svelte` |
| Form & validasi | `sveltekit-superforms`, `zod`, `valibot`, form actions bawaan (`+page.server.ts` `actions`) |
| HTTP client | `fetch` bawaan (`event.fetch` di `load`), `ky`, `ofetch` |
| Storage | `localStorage` (client-only), cookies via `event.cookies` (server) |
| Test runner | `vitest`, `@testing-library/svelte`, `@playwright/test`, `msw` |
| Config | `svelte.config.js` (`kit.alias`, adapter), `vite.config.*`, `tsconfig.json` (extends `.svelte-kit/tsconfig.json`), `eslint.config.*` |

Batas framework: **server/client boundary** — `+page.server.ts`, `+layout.server.ts`, `+server.ts`, dan `$lib/server/**` hanya berjalan di server; `+page.ts` universal; `.svelte` di-render di server lalu di-hydrate. Env: `$env/static/private` dilarang di kode client; hanya `$env/static/public` (`PUBLIC_*`) yang boleh.

## Commands

| Perintah | Nilai |
|---|---|
| typecheck | `<pm> run check`, yaitu `svelte-kit sync && svelte-check --tsconfig ./tsconfig.json` |
| lint | `<pm> run lint`, atau `npx eslint .` dengan `eslint-plugin-svelte` |
| test | `<pm> test`, lazim `vitest run` |
| test-single | `npx vitest run <berkas> -t "<nama>"` |
| build | `<pm> run build` (`vite build` lewat `@sveltejs/kit/vite`) |
| typecheck-per-brief | `tidak` — `svelte-kit sync && svelte-check` memuat seluruh graf rute tiap jalan; `profile` boleh menaikkannya ke `ya` bila durasi terukur di repo itu di bawah ~15 detik |

`<pm>` diambil dari lockfile. Skrip di `package.json` menang atas perintah generik di atas.

**Cakupan yang TIDAK diperiksa**:

- `typecheck`: `svelte-check` menilai `.svelte` dan `.ts`; `tsc --noEmit` **saja tidak memeriksa `.svelte`** — dilarang menggantinya. Tidak memeriksa tipe `load` lintas rute bila `./$types` belum di-sync (`svelte-kit sync`).
- `lint`: tidak memeriksa tipe; aturan reaktivitas Svelte 5 (`state_referenced_locally`) datang dari compiler, bukan ESLint.
- `test`: Vitest men-transpile tanpa typecheck; komponen diuji di jsdom tanpa SSR nyata — hydration mismatch tidak tertangkap.
- `build`: tidak memverifikasi env server tersedia di target deploy; kesalahan adapter baru ketahuan saat runtime.

## Layer taxonomy

| Layer | Penamaan | Letak lazim | Ekspor utama |
|---|---|---|---|
| DTO | `<entitas>.dto.ts` | `src/lib/features/<feat>/dto/` | `interface *RequestDTO`, `*ResponseDTO` |
| Service | `<entitas>.service.ts` | `src/lib/features/<feat>/services/` | objek `<entitas>Service` (menerima `fetch` sebagai parameter agar bisa dipakai di `load`) |
| API layer | `<entitas>.query.ts` (TanStack) **atau** `+page.ts`/`+page.server.ts` `load` + `invalidate('app:<key>')` | `src/lib/features/<feat>/api/`, `src/routes/**` | `create<Entitas>Query`, `<ENTITAS>_KEYS`, atau fungsi `load` |
| View-Model | `<entitas>.vm.ts` (fungsi murni) atau `<entitas>.vm.svelte.ts` (rune) | `src/lib/features/<feat>/view-model/` | `to<Entitas>UI()` + `interface *UI` |
| Controller | `<layar>.controller.svelte.ts` (kelas/fungsi rune `$state`/`$derived`) | `src/lib/features/<feat>/controllers/` | `create<Layar>Controller()` |
| Presentation | `<Layar>Page.svelte`, `<Bagian>.svelte`; rute tipis `+page.svelte` | `src/lib/features/<feat>/components/`, `src/routes/**` | komponen |
| Test | `*.test.ts` | bersebelahan atau `__tests__/` | — |

Potongan per layer:

```typescript
// API layer — api/order.query.ts (TanStack Svelte Query)
export const ORDER_KEYS = { all: ['orders'] as const, detail: (id: string) => [...ORDER_KEYS.all, 'detail', id] as const };
export const createOrderQuery = (id: () => string) =>
  createQuery(() => ({ queryKey: ORDER_KEYS.detail(id()), queryFn: () => orderService.get(fetch, id()) }));

// Controller — controllers/order-detail.controller.svelte.ts
export function createOrderDetailController(id: () => string) {
  const query = createOrderQuery(id);
  let isEditOpen = $state(false);
  const ui = $derived(toOrderUI(query.data));
  return {
    get ui() { return ui; }, get isLoading() { return query.isLoading; }, get isError() { return query.isError; },
    get isEditOpen() { return isEditOpen; },
    refetch: () => query.refetch(), openEdit: () => { isEditOpen = true; },
  };
}
```

```svelte
<!-- Presentation — components/OrderDetailPage.svelte -->
<script lang="ts">
  import { createOrderDetailController } from '../controllers/order-detail.controller.svelte';
  let { id }: { id: string } = $props();
  const vm = createOrderDetailController(() => id);
</script>
{#if vm.isLoading}<OrderSkeleton />{:else if vm.isError}<ErrorBanner onRetry={vm.refetch} />{:else if vm.ui}<OrderCard order={vm.ui} />{/if}
```

Jebakan stack saat menulis kode di layer ini:

1. **`$lib/server/**` dan `$env/static/private` dilarang diimpor dari `.svelte` atau `+page.ts`.** Build gagal dengan error boundary server; kredensial bisa bocor ke bundle bila dipaksakan.
2. **`load` memakai `event.fetch`, bukan `fetch` global.** Fetch global di SSR kehilangan cookie dan relative URL.
3. **Rune `$state`/`$derived` hanya di `.svelte` dan `.svelte.ts`.** Di `.ts` biasa compiler menolak; state bersama di modul `.svelte.ts` wajib diekspor lewat getter atau objek, bukan destrukturisasi.
4. **`$effect` bersubscription wajib mengembalikan cleanup** (Svelte 4: `onDestroy`). Listener `window` menumpuk tiap navigasi client-side.
5. **`localStorage`/`window` hanya di dalam `onMount`/`$effect` atau guard `browser` dari `$app/environment`.** Di SSR keduanya `undefined`.
6. **Invalidasi sesudah mutasi**: TanStack → `invalidateQueries`; `load` bawaan → `invalidate('app:<key>')` atau `invalidateAll()`; form action → otomatis re-run `load`. Tanpa itu daftar basi.
7. **Side-effect UI (`goto`, toast) dilarang di `createMutation`/`load`.** Hidup di Controller.
8. **`./$types` wajib dipakai untuk `PageLoad`/`PageServerLoad`/`Actions`.** Tipe manual meleset dari param rute nyata.

Hygiene penutup unit (`agents/code-implementor.md` Fase 1): nol `any`, tipe balikan controller/vm eksplisit, nol `console.log`, import lewat `$lib`/`kit.alias`, nol side-effect di API layer, cleanup pada `$effect`/`onDestroy`, `.svelte` mengonsumsi `*UI` alih-alih DTO, nol import server-only di client. `package.json`, lockfile, `svelte.config.js`, `vite.config.*`, dan `tsconfig.json` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Route / Presentation | `Glob` `src/routes/**/+page.svelte`, `src/routes/**/+layout.svelte`; `Glob` `src/lib/features/**/components/*.svelte` |
| Controller | `Grep -n "export (function\|const) create\w+Controller\b"`; `Glob` `**/*.controller.svelte.ts` |
| View-Model | `Grep -n "export (function\|const) to\w+UI\b\|export interface \w+UI\b"`; `Glob` `**/*.vm*.ts` |
| API layer | `Grep -n "createQuery\(\|createMutation\(\|export const load\b\|export const actions\b"` |
| Cache & mutasi | `Grep -n "export const \w+_KEYS = \{\|invalidateQueries\|invalidate('\|invalidateAll("` |
| Service transport | `Grep -n "apiClient\.(get\|post\|put\|patch\|delete)\|ky\.create\|fetch: typeof fetch"` |
| DTO | `Grep -n "export (interface\|type) \w+(DTO\|Response\|Request)\b"` |
| Kebocoran DTO ke presentasi | `Grep -n "from ['\"].*dto" --glob "*.svelte"` |
| State global | `Grep -n "\$state(\|writable(\|readable("` di `src/lib/**/*.svelte.ts` dan `stores/` |
| Form & skema | `Grep -n "superForm(\|superValidate(\|= z\.object\(\{\|export const actions"` |
| Batas framework | `Grep -n "\$lib/server\|\$env/static/private\|\$env/dynamic/private\|from '\$app/environment'"`; `Glob` `src/routes/**/+*.server.ts` |
| Rute dinamis | `Glob` `src/routes/**/\[*\]/**`; `Grep -n "params\.\w+\|url\.searchParams"` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35`; untuk `.svelte` mulai dari `<script>` sampai tag penutupnya bila ≤50 baris.

## Review checklist

#### `layer-boundaries`

- **`import ... from '.../dto/...'` di `.svelte`.** P1. Grep: `Grep -n "from.*dto" --glob "*.svelte"`.
- **`fetch(` langsung di `<script>` komponen presentasi.** P1. Lepas dari cache/invalidasi dan gagal di SSR.

#### `data-flow`

- **`load` mengembalikan DTO mentah ke `data` prop tanpa View-Model.** P2.

#### `api-layer`

- **`goto(` atau toast di `createMutation`/`load`.** P1. Grep: `Grep -n "goto(\|toast" src/lib/**/api/ src/routes/**/+page*.ts`.

#### `state-scope`

- **`$state` global di `.svelte.ts` menyimpan state form satu halaman.** P2. God store.

#### `ui-states`

- **`{:else if isError}` tanpa `onRetry`.** P2.
- **`{#await}` tanpa `{:catch}`.** P2. Error tak tertangani di template.

#### `platform`

- **`$lib/server` atau `$env/static/private` diimpor dari `.svelte`/`+page.ts`.** P1. Grep: `Grep -n "\$lib/server\|\$env/static/private" --glob "*.svelte" --glob "+page.ts" --glob "+layout.ts"`.
- **`window`/`localStorage` di top-level `<script>` tanpa `browser` guard.** P1. Crash di SSR.
- **`fetch` global di `load`.** P2. Cookie hilang di SSR.

#### `error-handling`

- **`+error.svelte` absen di segmen yang memuat `load` berpotensi gagal.** P3.

#### `performance`

- **`$effect` dengan `addEventListener`/`setInterval` tanpa `return`.** P2.

## UI & navigation surface

- **Routing**: file-system di `src/routes/` — segmen dinamis `[id]`, opsional `[[slug]]`, rest `[...path]`, grup `(app)`; `params` dari `load`, search params dari `url.searchParams` (`load`) atau `page.url.searchParams` (`$app/state`). Rute ditulis ke `FLOW.md` persis seperti struktur foldernya.
- **Deep-link**: URL adalah deep-link; state yang harus bertahan refresh dinyatakan di query string dan dibaca di `load`.
- **Sinkronisasi state URL**: `goto(url, { replaceState: true, keepFocus: true, noScroll: true })` untuk search/sort; `goto` biasa untuk filter/page; `pushState`/`replaceState` dari `$app/navigation` untuk shallow routing (modal `?modal=detail`).
- **Kembali & batal**: `beforeNavigate((nav) => { if (dirty) nav.cancel(); })` untuk dirty guard client-side; `beforeunload` untuk tutup tab; form action `use:enhance` menangani submit tanpa reload.
- **Platform**: breakpoint mobile <640px, tablet 768–1023px, desktop ≥1024px; fokus keyboard terlihat; dialog untuk konfirmasi destruktif, drawer untuk form panjang; `+layout.svelte` memegang header/footer sticky.
- **Design token**: `tailwind.config.*` atau CSS variables di `src/app.css`; komponen bersama di `$lib/components/ui/`.
- **Aksesibilitas**: `aria-label` pada tombol ikon, `aria-live="polite"` untuk pesan asinkron; compiler Svelte memberi warning a11y — dilarang dibungkam dengan `<!-- svelte-ignore a11y_* -->`.

## Failure signatures

| Kategori error | Penyebab umum | Strategi resolusi yang sah |
|---|---|---|
| **`svelte-check` TS2322 / TS2345** | Tipe DTO berbeda dari yang dipakai controller/vm | Sesuaikan tipe lokal ke `CONTRACT.md` |
| **`Cannot find module './$types'`** | `svelte-kit sync` belum jalan | Jalankan `svelte-kit sync` lewat skrip `check`; jangan tulis tipe manual |
| **`Cannot import $lib/server/... into client-side code`** | Modul server diimpor dari `.svelte`/`+page.ts` | Pindahkan pemanggilan ke `+page.server.ts` / `+server.ts` |
| **`state_referenced_locally` / `$state` di `.ts`** | Rune dipakai di berkas non-`.svelte.ts`, atau state didestrukturisasi | Ganti ekstensi ke `.svelte.ts`; ekspor getter |
| **`ReferenceError: window is not defined`** | Akses browser API di SSR | Bungkus `onMount`/`$effect` atau guard `browser` |
| **`Error: Not found: /...` di test Playwright** | Struktur `src/routes` tidak cocok rute di `FLOW.md` | Cocokkan folder; jangan ubah `FLOW.md` diam-diam |
| **Vitest `Failed to resolve import "$lib/..."`** | Alias `$lib` tidak dikenal Vitest tanpa plugin `sveltekit()` | Pastikan `vite.config` memuat `sveltekit()`; jangan hardcode path relatif |
| **a11y warning compiler (`a11y_click_events_have_key_events`)** | Elemen non-interaktif diberi `onclick` | Pakai `<button>`; dilarang `svelte-ignore` |
| **`superValidate` schema mismatch** | `defaultValues` form tidak cocok skema | Sinkronkan dengan tipe inferensi skema |
| **Hydration mismatch** | Markup SSR berbeda dari client (tanggal lokal, random) | Pindahkan nilai non-deterministik ke `onMount`/`$effect` |
