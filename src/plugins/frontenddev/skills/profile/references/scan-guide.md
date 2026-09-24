# Scan Guide — `profile`

Resep 18 titik pemindaian Phase 2. Tiap titik menyebut **apa yang dicari**, **dari mana resepnya**,
dan **muaranya** — berkas profil tempat hasilnya mendarat. Muara itu mengikat: titik yang hasilnya
tidak pernah ditulis ke berkas mana pun adalah pemindaian yang tidak dibaca siapa pun.

Resep spesifik stack **selalu** diambil dari `stacks/<stack-id>.md` yang Phase 0 tetapkan, bukan dari
ingatan stack lain. Berkas ini hanya menyebut *seksi adapter mana* yang menjawab tiap titik.

Aturan yang berlaku di seluruh titik:

- Catat fakta bersama anchor `<path>#<simbol>` atau `<path>` telanjang. Nomor baris dilarang.
- Fakta nihil ditulis `tidak terdeteksi`, bukan dikosongkan dan bukan ditebak dari kelaziman stack.
- Resep adapter yang nol hit di repo ini **bukan** temuan; ia berarti pola itu tidak dipakai.
- Inkonsistensi antar-fitur dan gaya terbelah tanpa mayoritas dikumpulkan sebagai bahan Phase 3,
  tidak diputuskan di sini.

---

## 1. Manifest & framework → `index.json`, `stack.md`

`package.json` root dan `target_app`. Versi framework dan variannya: Expo versus Bare, Svelte 5 runes
versus Svelte 4 store, router yang dipakai. Cocokkan tabel kelompok penanda di `## Detection` adapter
untuk **State Management**, **Query / cache**, **Styling Engine**, **Form & validasi**, **Storage**,
dan **Test Runner**. Catat hanya yang benar-benar hadir di manifest.

## 2. Perintah verifikasi repo → `commands.md`

Scripts `typecheck`/`check`, `lint`, `test`, `test-single`, `build` beserta argumennya. **Skrip repo
menang atas perintah generik adapter**: repo yang punya `pnpm check:types` dijalankan dengan perintah
itu, bukan dengan `tsc --noEmit` yang adapter sebut sebagai default. Perintah hasil titik ini yang
dieksekusi Phase 4; jangan menuliskannya ke profil sebelum dijalankan.

## 3. TypeScript config & alias → `stack.md`, `structure.md`

`tsconfig.json` beserta rantai `extends`-nya. **Path aliases** (`@/*`, `~/*`, `$lib`, `@features/*`)
dan **compiler flags** `strict`, `noImplicitAny`, `jsx`, `target`, `moduleResolution`, `paths`.
Alias yang salah dicatat membuat tiap `import` di brief hilir ditulis dengan prefix yang tidak
di-resolve bundler, dan galatnya baru muncul di verifikasi penutup.

## 4. Framework & bundler config → `stack.md`

Berkas yang disebut baris **Config** di `## Detection` adapter: `vite.config.*`, `svelte.config.js`,
`app.json`, `metro.config.*`, `babel.config.*`, `tailwind.config.*`. Catat plugin yang terpasang dan
opsi yang menyimpang dari default — keduanya membatasi bentuk kode yang sah di repo ini.

## 5. Arsitektur workspace → `structure.md`, `index.json`

- **Single App**: root memuat `src/` dan satu `package.json`, tanpa sub-workspace.
- **Monorepo**: root memuat `pnpm-workspace.yaml`, `turbo.json`, atau `lerna.json` dengan `apps/*`
  dan `packages/*`. Petakan seluruh package aktif dan tetapkan aplikasi utama.

Pemetaan package wajib pada monorepo: tanpa itu, routing modul di gerbang `lead` menebak letak fitur.

## 6. Controller layer → `layer-adoption.md`

Unit orkestrasi layar yang membungkus seluruh state satu layar — React `use*Page`/`use*Screen`,
Svelte `*.controller.svelte.ts`. Resep pencariannya di `## Navigation recipes` adapter. Catat
**sebarannya**, bukan sekadar ada atau tidak: layer yang dipakai tiga fitur dari sepuluh adalah
adopsi parsial, dan menuliskannya sebagai "dipakai" membuat hilir menagih pola yang belum berlaku.

## 7. View-Model layer → `layer-adoption.md`

Unit transformasi DTO → props UI — React `use*ViewModel`, Svelte `to*UI()` / `*.vm.ts`. Periksa
apakah ia benar-benar mengekspor tipe `*UI` atau hanya meneruskan DTO apa adanya; yang kedua bukan
View-Model, melainkan lapisan kosong yang menyamarkan kebocoran DTO.

## 8. API layer → `layer-adoption.md`

Pemakaian query library (TanStack Query React/Svelte, atau `load` SvelteKit) dan konvensi query key.
Catat apakah key disusun lewat **array factory terpusat** atau string mentah tersebar — perbedaan itu
yang menentukan apakah invalidasi cache di brief hilir dapat ditulis sama sekali.

## 9. HTTP Service layer → `layer-adoption.md`

Modul transport API murni di `src/services/` atau `src/features/<feat>/services/*.service.ts`.
Periksa kemurniannya: service yang memanggil navigasi atau toast bukan transport, dan mencatatnya
sebagai transport membuat brief hilir menaruh side-effect di tempat yang salah.

## 10. DTO layer → `layer-adoption.md`

Deklarasi antarmuka payload backend di `dto/*.dto.ts` atau `types/*.ts`. Jalankan juga resep
**kebocoran DTO ke presentasi** dari `## Navigation recipes`: hit di sini adalah bukti pelanggaran
Invariant 1 yang sudah hidup di repo, dan muaranya `drift.md`, bukan sini.

## 11. Surface map → `surface-map.md`

Lokasi kanonik dan penanda kode untuk Routing, Global State, Cache, Styling, Forms, Auth/Storage,
dan batas framework. Kolom **Penanda Pengenal Kode** diisi dari resep adapter yang **benar-benar
berhit** di repo ini — resep yang disalin tanpa dijalankan menghasilkan peta yang menunjuk ke
direktori kosong, dan explorer hilir menyisir tempat yang salah tanpa satu pun kegagalan tercatat.

## 12. Persisted state & storage → `layer-adoption.md`

Library storage dari kelompok **Storage** adapter: `MMKV`, `AsyncStorage`, `SecureStore`,
`localStorage`, `IndexedDB`, cookies server-side. Catat **daftar key yang sudah terdaftar**
(`@auth_token`, `@user_session`, `@app_theme`, `@draft_order`) — daftar itu yang mencegah brief baru
menabrak key yang sudah dipakai, dan tabrakannya tidak pernah gagal saat compile.

## 13. Shared HTTP client → `layer-adoption.md`

Instance Axios / Ky / Fetch wrapper (`src/services/api.ts`, `$lib/api/client.ts`) beserta auth
interceptor, base URL, dan response error handler. Catat dari mana base URL dibaca; env var yang
salah prefix (`VITE_*` versus `PUBLIC_*`) menghasilkan `undefined` saat runtime, bukan galat build.

## 14. Design token & visual → `visual.md`

Letak token warna, tipografi, radius, dan spacing — `tailwind.config.*`, berkas tema, atau konstanta
token. **Salin nilainya persis dari konfigurasi**, jangan dari ingatan atau dari tampilan aplikasi.

## 15. Standar test → `commands.md`

Test runner, letak berkas test, konvensi penamaan, dan apa yang benar-benar diuji repo ini
(View-Model, Service, komponen). Catat juga yang **tidak** diuji: cakupan yang absen adalah batas
klaim yang boleh dibuat verifikasi penutup.

## 16. Konvensi commit → `index.json`

`git log -n 20 --oneline`. Turunkan pola prefix nyata dari riwayat, bukan dari asumsi Conventional
Commits. Repo non-git: tulis `UNINITIALIZED (default conventional commits)`.

## 17. Enam invariant mutlak → `invariants.md`

Pelanggaran = blocker, bukan gaya. Nilai tiap invariant terhadap kode nyata dan catat buktinya:

1. *Zero DTO Leak to Presentation* — komponen presentasi mengimpor DTO langsung, atau wajib via
   View-Model.
2. *No Direct Fetch in Presentation* — fetch API terisolasi di Controller/API layer, bukan di efek
   komponen presentasi.
3. *Query Key Factory Arrays* — query key memakai array factory terpusat atau string mentah.
4. *Mandatory 6-State Branches* — layar asinkron menangani initial, skeleton loading, empty, error,
   ready, mutating.
5. *Strict Design Token Theme* — kepatuhan pemakaian token warna, font, radius, spacing.
6. *Framework Boundary Scoping* — batas yang dinyatakan adapter: SafeAreaInsets dan touch target
   React Native, server/client boundary SvelteKit, env `VITE_*`/`PUBLIC_*` di SPA.

Invariant yang repo-nya belum patuhi tetap ditulis sebagai invariant, dan ketidakpatuhannya masuk
titik 18. Menurunkannya jadi "tidak berlaku" karena repo melanggarnya membuat profil melegalkan
pelanggaran yang sedang berjalan.

## 18. Drift & competing patterns → `drift.md`

Pola lama warisan versus pola modern rekomendasi (Svelte 4 `$:` versus rune, `useEffect` fetch versus
query hook). Tiap baris berstruktur, bukan prosa:

```
- <pola warisan> (<sebaran>) → <pola modern> · deteksi `<pola grep> @ <glob>` · bukti <file#simbol>
```

Resep `deteksi` diturunkan dari `## Navigation recipes` adapter dan **wajib berhit minimal sekali**
saat ditulis; nol hit berarti polanya sudah punah dan barisnya batal. Tanpa resep itu, baris Drift
tidak dapat diverifikasi masih hidup pada REFRESH berikutnya, dan implementor terus dilarang meniru
pola yang sudah tidak ada.

Format baris ini dibaca mesin: `skills/plan/scripts/validate_briefs.py` mem-parse-nya untuk Check
Drift. Mengubah urutan atau pemisah `·`-nya mematikan check itu tanpa satu pun galat.

---

## Aturan penutup

- Titik 1–16 adalah pemindaian; titik 17 penilaian terhadap kode nyata; titik 18 memuat konsekuensi
  dari keduanya.
- Sebaran pola dihitung dari sampel **minimal 3 fitur** per aspek. Di bawah itu, angka sebarannya
  tidak menyatakan apa pun dan wajib ditulis sebagai `sampel tidak memadai`.
- Parameter `strict_scan: false` mempersempit sampel ke fitur yang disebut `target_app` saja; catat
  penyempitan itu di `manual-notes.md` supaya REFRESH berikutnya tahu angkanya tidak menyeluruh.
