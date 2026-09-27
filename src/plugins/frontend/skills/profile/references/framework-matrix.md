# Framework Matrix & Profiling Heuristics

Panduan komparasi arsitektur empat stack yang didukung `frontend` (`react-vite`, `react-native`, `sveltekit`, `svelte-vite`) dan heuristik deteksi otomatis untuk skill `frontend:profile`. Detail per stack hidup di `../stacks/<stack-id>.md`; matriks ini hanya peta perbandingannya.

---

## 1. Multi-Stack Feature & Pattern Matrix

| Fitur / Dimensi | `react-vite` | `react-native` (Expo / Bare) | `sveltekit` | `svelte-vite` |
|---|---|---|---|---|
| **Entry Point File** | `src/main.tsx` + `index.html` | `app/_layout.tsx` (Expo Router) / `App.tsx` + `index.js` | `src/routes/+layout.svelte` + `src/app.html` | `src/main.ts` + `index.html` |
| **Routing System** | React Router / TanStack Router | Expo Router (`app/**`) / React Navigation (`src/navigation/`) | File-system `src/routes/**` (`+page`, `+layout`) | `svelte-routing` / `svelte-spa-router` / manual |
| **Data Fetching** | TanStack Query di Controller | TanStack Query di Controller | TanStack Svelte Query atau `load` + `invalidate` | TanStack Svelte Query |
| **Unit logika** | hook (`use*`) | hook (`use*`) | rune di `.svelte.ts` / store | rune di `.svelte.ts` / store |
| **Styling Solution** | Tailwind / CSS Modules / Emotion | NativeWind / StyleSheet / Tamagui | Tailwind / `<style>` scoped | Tailwind / `<style>` scoped |
| **State Persistence** | LocalStorage / IndexedDB | MMKV / AsyncStorage / SecureStore | LocalStorage (client) / cookies (server) | LocalStorage / IndexedDB |
| **Batas framework** | `import.meta.env.VITE_*` | Metro tanpa typecheck; modul native | server/client boundary, `$lib/server`, `$env/static/private` | `import.meta.env.VITE_*` |
| **Safe Area** | CSS viewport units | `react-native-safe-area-context` | CSS `env(safe-area-inset-*)` | CSS viewport units |
| **Gestures / Back** | Browser back, `useBlocker` | `BackHandler`, swipe-back iOS, `beforeRemove` | Browser back, `beforeNavigate` | Browser back, guard router |
| **Keyboard Avoidance** | Browser default | `KeyboardAvoidingView` | Browser default | Browser default |
| **Typecheck** | `tsc --noEmit` | `tsc --noEmit` | `svelte-check` (bukan `tsc` saja) | `svelte-check` (bukan `tsc` saja) |

---

## 2. Profiling Heuristics & Terminal Detection Recipes

Urutan pemutus wajib dari yang paling spesifik; satu manifest hanya menghasilkan satu `<stack-id>`:

```bash
# 0. Pengecualian — Next.js tidak dilayani plugin ini
grep -qE '"next"\s*:' package.json && echo "UNSUPPORTED: next" && exit 1

# 1. React Native (Expo atau Bare)
grep -qE '"(react-native|expo)"\s*:' package.json && echo "react-native"

# 2. SvelteKit
grep -qE '"@sveltejs/kit"\s*:' package.json && echo "sveltekit"

# 3. Svelte + Vite (tanpa kit)
grep -qE '"svelte"\s*:' package.json && ! grep -qE '"@sveltejs/kit"' package.json \
  && { grep -qE '"vite"\s*:' package.json || ls vite.config.* >/dev/null 2>&1; } && echo "svelte-vite"

# 4. React + Vite
grep -qE '"react"\s*:' package.json \
  && { grep -qE '"vite"\s*:' package.json || ls vite.config.* >/dev/null 2>&1; } && echo "react-vite"

# 5. React/Svelte tanpa Vite (CRA `react-scripts`, Rollup) → di luar cakupan plugin
# Resep grep di atas hanya bantuan baca manual; vonis yang mengikat adalah `hooks/detect.py`
# (`frontend_from_package`), yang dipakai hook dan skrip prasyarat.
```

### A. Varian di dalam satu stack:
```bash
# React Native: Expo vs Bare
grep -qE '"expo"\s*:' package.json && echo "Expo" || { test -d ios && test -d android && echo "Bare CLI"; }

# Svelte: runes (5) vs store (4)
grep -E '"svelte"\s*:\s*"[\^~]?5' package.json && echo "Svelte 5 runes" || echo "Svelte 4 store"
```

### B. Deteksi router:
```bash
grep -E '"(react-router-dom|@tanstack/react-router|expo-router|@react-navigation/native|svelte-routing|svelte-spa-router)"' package.json
test -d src/routes && echo "SvelteKit file-system routes"
```

### C. Deteksi query & state:
```bash
grep -E '"(@tanstack/react-query|@tanstack/svelte-query|zustand|@reduxjs/toolkit|jotai)"' package.json
grep -rln '\$state(' src --include='*.svelte.ts' | head -n 3   # rune module
```

Daftar lengkap kelompok penanda per stack ada di `## Detection` adapter masing-masing.

---

## 3. Monorepo Package Mapping Heuristics

Pada struktur monorepo terpadu (Turborepo, Nx, pnpm workspaces):

1. **Aplikasi Konsumen (`apps/*`)**:
   - `apps/web`: Aplikasi web (`react-vite`, `sveltekit`, atau `svelte-vite`).
   - `apps/mobile`: Aplikasi seluler (`react-native`).
   - `apps/admin` / `apps/dashboard`: Panel administrasi internal.
2. **Paket Bersama (`packages/*`)**:
   - `packages/ui`: Komponen presentasi visual bersama yang murni domain-agnostic (`Button`, `Card`, `Modal`).
   - `packages/shared`: Utilitas tanggal, fungsi sanitasi, formatting mata uang, dan tipe dasar.
   - `packages/api-client`: Wrapper HTTP client terpusat dan penanganan token auth.
3. **Aturan Isolasi Monorepo**:
   - Paket di `packages/ui` dilarang keras mengimpor modul bisnis dari `apps/*` atau `src/features/*`.
   - Kode fitur baru wajib ditempatkan di dalam folder fitur spesifik aplikasi (`apps/<app>/src/features/<feat>/` atau `apps/<app>/src/lib/features/<feat>/` di SvelteKit).
   - Satu profil melayani **satu** `<stack-id>`; monorepo dengan `apps/web` dan `apps/mobile` diprofil per app lewat `target_app`.
