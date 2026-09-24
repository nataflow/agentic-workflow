# Layer Patterns & Architecture Rules Reference

Panduan arsitektur layer frontend 5-tier (Presentation, Controller, View-Model, API layer, Service/DTO), tanggung jawab dan ekspor tiap layer, spesifikasi platform, dan katalog anti-pattern untuk skill `frontenddev:contract`. Penamaan berkas, letak direktori, dan potongan kode idiomatik per stack **tidak** ditulis di sini — rumahnya `## Layer taxonomy` pada adapter `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack-id>.md`.

---

## 1. Core Layer Responsibilities

```
[ Presentation ]
      │ (hanya memanggil Controller)
[ Controller ] (React: use*Page / use*Screen · Svelte: create*Controller di .svelte.ts)
      │ (menggabungkan view-model, mutasi, navigasi, form)
      ├───► [ View-Model ] (transformasi DTO -> UI Props murni; React: use*ViewModel · Svelte: to*UI())
      └───► [ API layer ] (React: useQuery/useMutation · Svelte: createQuery/createMutation atau load)
                 │ (transport HTTP murni lewat client bersama)
            [ HTTP Service & DTO ]
```

| Layer | Ekspor utama | Boleh mengimpor | Dilarang mengimpor |
|---|---|---|---|
| **DTO** | `interface *RequestDTO`, `*ResponseDTO`, `ApiErrorResponseDTO` | — | apa pun dari layer lain |
| **Service** | objek `<entitas>Service` dengan fungsi async bertipe DTO | DTO, client HTTP bersama | query library, store, komponen |
| **API layer** | query/mutation + `<ENTITAS>_KEYS` factory | Service, DTO | router, toast, store UI |
| **View-Model** | `interface *UI` + fungsi/unit transformasi murni | DTO, util format | Service, query, router |
| **Controller** | satu unit orkestrasi per layar: state, handler, side-effect | API layer, View-Model, router, form, store | DTO ke luar (hanya lewat `*UI`) |
| **Presentation** | komponen | Controller, komponen bersama, tipe `*UI` | DTO, Service, query library |

### Kontrak per layer (netral stack)

- **DTO** memuat nama field persis seperti backend (snake_case bila backend snake_case); tidak ada transformasi.
- **Service** menerima parameter primitif/DTO dan mengembalikan `Promise<DTO>`; tidak menyimpan state; memakai client bersama repo (`layer-adoption.md` profil).
- **API layer** memegang query key factory, `staleTime`/`gcTime`, dan invalidasi di `onSettled`; **nol** side-effect UI. Di SvelteKit dengan `load` bawaan, layer ini adalah `+page.ts`/`+page.server.ts` dan invalidasinya `invalidate('app:<key>')`.
- **View-Model** adalah fungsi murni dari DTO ke `*UI` — teruji tanpa render, tanpa akses jaringan. Format uang, tanggal, badge, dan label hidup di sini.
- **Controller** mengikat query + View-Model + state lokal (modal, filter, form) dan mengeksekusi navigasi/toast **di handler**, bukan di API layer.
- **Presentation** menerima `*UI` dan handler; tidak memicu fetch mandiri; merender 6 cabang state dari flag Controller.

Contoh kode per layer untuk stack repo dibaca dari `## Layer taxonomy` adapter (React: hook; Svelte: rune/store) — dilarang menyalin idiom stack lain ke `CONTRACT.md`.

---

## 2. Platform Specifics

Dibaca dari `## Layer taxonomy` dan `## UI & navigation surface` adapter; ringkasan batas yang wajib disebut di `# Architecture` bila relevan:

### Web SPA (`react-vite`, `svelte-vite`):
- **Env boundary**: hanya `import.meta.env.VITE_*` yang ada di bundle.
- **URL Query Sync**: state filter/page disinkronkan ke search params dengan `replace` untuk search/sort.
- **Error boundary**: error boundary di tingkat rute; `+error`/`ErrorBoundary` sesuai router.

### SvelteKit (`sveltekit`):
- **Server vs Client Boundary**: `+page.server.ts` / `$lib/server/**` memuat data awal dan rahasia; `.svelte` dan `+page.ts` universal. Kontrak wajib menyebut di sisi mana Service dipanggil.
- **`load` sebagai API layer**: bila repo memakai `load` alih-alih TanStack, `# Architecture` menyebut key `invalidate('app:<key>')` per entitas.
- **Global Error Boundary**: `+error.svelte` pada segmen rute yang memuat `load` berpotensi gagal.

### React Native & Mobile (`react-native`):
- **App Lifecycle & Focus**: refetch saat layar aktif kembali lewat `useFocusEffect`.
- **Hardware Back Handling**: intersep hardware back Android di Controller bila terdapat modal terbuka.
- **Offline Query Cache**: persistence query dengan MMKV storage untuk retensi data offline.

---

## 3. Architectural Anti-Patterns & Hard Violations

| Pelanggaran (Anti-Pattern) | Risiko & Biaya Perubahan | Solusi Arsitektural yang Benar |
|---|---|---|
| **DTO Leaking to Presentation** | Perubahan skema backend merusak puluhan komponen | Petakan melalui View-Model dengan interface `*UI` |
| **Side Effects in API layer** | API layer tidak dapat dipakai ulang di dialog/layar lain | Pindahkan navigasi/toast ke handler Controller |
| **God Store** | Store global mengelola state form milik 1 halaman | Batasi store global untuk auth/sesi; state lokal tetap di Controller |
| **Raw String Query Keys** | Tabrakan cache dan kegagalan invalidasi data | Gunakan query key factory array terpusat |
| **Component Self-Fetching** | Anak komponen memicu cascade network waterfall | Angkat query ke Controller layar |
| **Cross-Stack Idiom** | Berkas bernama pola stack lain tidak dikenali router/compiler repo | Ikuti `## Layer taxonomy` adapter `stack` profil |
