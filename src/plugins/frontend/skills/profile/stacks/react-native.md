# Stack adapter — `react-native`

React Native — Expo (Expo Router atau React Navigation) maupun Bare CLI. Ditulis mengikuti `_CONTRACT.md`; tujuh seksi, urutan tetap.

## Detection

Manifest: `package.json` di root atau satu tingkat workspace (`apps/mobile`, `apps/app`).

- **Penanda wajib**: `react-native` di `dependencies`. `expo` hadir → varian Expo; `ios/` dan `android/` hadir tanpa `expo` → Bare CLI.
- **Pengecualian**: `next` hadir di manifest yang sama → bukan stack plugin ini; hentikan.
- **Pemutus terhadap `react-vite`**: `react-native` menang atas `react`+`vite` dalam satu manifest (Expo web memakai Metro, bukan Vite).
- **Pembuktian**: `grep -E '"(react-native|expo)"\s*:' package.json; ls app.json app.config.* metro.config.* babel.config.*`.
- **Entry point**: Expo Router — `app/_layout.tsx` dan `app/index.tsx`; React Navigation — `App.tsx` + `src/navigation/`; Bare — `index.js` mendaftarkan `AppRegistry`.
- **Versi runtime**: `expo` SDK dari `dependencies.expo`, RN dari `dependencies.react-native`; Node dari `.nvmrc`.
- **Package manager aktif**: lockfile — `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `bun.lockb`.

Dependensi penanda per kelompok:

| Kelompok | Paket |
|---|---|
| Router | `expo-router`, `@react-navigation/native`, `@react-navigation/native-stack`, `@react-navigation/bottom-tabs` |
| Query / cache | `@tanstack/react-query`, `swr` |
| State global | `zustand`, `@reduxjs/toolkit`, `jotai`, `legend-state` |
| Styling | `nativewind`, `tamagui`, `react-native-paper`, `@gluestack-ui/*`, `StyleSheet` bawaan, `styled-components/native` |
| Form & validasi | `react-hook-form`, `zod`, `yup` |
| HTTP client | `axios`, `ky`, `fetch` bawaan |
| Storage | `react-native-mmkv`, `@react-native-async-storage/async-storage`, `expo-secure-store` |
| Platform | `react-native-safe-area-context`, `react-native-gesture-handler`, `react-native-reanimated`, `react-native-keyboard-controller` |
| Test runner | `jest` + `jest-expo`/`react-native` preset, `@testing-library/react-native`, `detox`, `maestro` |
| Config | `app.json`/`app.config.*`, `metro.config.*`, `babel.config.*`, `tsconfig.json`, `eas.json` |

Batas framework: Metro men-transpile TypeScript lewat Babel **tanpa typecheck**; batas native ada di modul yang butuh dev build (bukan Expo Go).

## Commands

| Perintah | Nilai |
|---|---|
| typecheck | `<pm> run typecheck`, atau `npx tsc --noEmit` |
| lint | `<pm> run lint`, atau `npx eslint .` (`eslint-config-expo` bila Expo) |
| test | `<pm> test`, lazim `jest` dengan preset `jest-expo` atau `react-native` |
| test-single | `npx jest <pola> -t "<nama>"` |
| build | `npx expo export` (Expo) / `npx react-native bundle --platform android --dev false --entry-file index.js --bundle-output /tmp/rn.bundle` (Bare); build native EAS/Gradle/Xcode **tidak** dijalankan plugin |
| typecheck-per-brief | `ya` — `tsc --noEmit` tidak menyentuh Metro maupun build native, jadi biayanya sama dengan SPA |

`<pm>` diambil dari lockfile. Skrip di `package.json` menang atas perintah generik di atas.

**Cakupan yang TIDAK diperiksa**:

- `typecheck`: tidak memeriksa modul native yang ketiadaannya baru ketahuan saat runtime (Expo Go vs dev build).
- `lint`: tidak memeriksa tipe; `react-hooks/exhaustive-deps` hanya bila plugin terpasang.
- `test`: **Metro/Babel membuang anotasi tipe sebelum Jest jalan** — test hijau tidak membuktikan typecheck hijau. Test juga tidak merender native view sesungguhnya.
- `build`: `expo export` membuktikan bundle JS terbentuk, bukan bahwa binary native terpasang; konfigurasi `app.json` yang salah baru ketahuan di EAS.

## Layer taxonomy

| Layer | Penamaan | Letak lazim | Ekspor utama |
|---|---|---|---|
| DTO | `<entitas>.dto.ts` | `src/features/<feat>/dto/` | `interface *RequestDTO`, `*ResponseDTO` |
| Service | `<entitas>.service.ts` | `src/features/<feat>/services/` | objek `<entitas>Service` |
| API layer | `use<Entitas>Query.ts`, `use<Aksi>Mutation.ts` | `src/features/<feat>/hooks/api/` | hook TanStack Query + `<ENTITAS>_KEYS` |
| View-Model | `use<Entitas>ViewModel.ts` | `src/features/<feat>/hooks/view-model/` | hook + `interface *UI` |
| Controller | `use<Layar>Screen.ts` | `src/features/<feat>/hooks/` | hook `use*Screen` |
| Presentation | `<Layar>Screen.tsx`, `<Bagian>.tsx` | `src/features/<feat>/screens/`, `components/`; rute tipis di `app/**` (Expo Router) | komponen fungsi |
| Test | `*.test.ts(x)` | `__tests__/` atau bersebelahan | — |

Potongan per layer:

```typescript
// Controller — hooks/useOrderListScreen.ts
export const useOrderListScreen = () => {
  const { data, isLoading, isError, refetch, isRefetching } = useOrdersQuery();
  const rows = useOrderRowsViewModel(data);
  const router = useRouter(); // expo-router; atau useNavigation() dari @react-navigation/native
  useFocusEffect(useCallback(() => { void refetch(); }, [refetch]));
  const handleOpen = useCallback((id: string) => router.push(`/orders/${id}`), [router]);
  return { rows, isLoading, isError, isRefetching, refetch, handleOpen };
};

// Presentation — screens/OrderListScreen.tsx
export function OrderListScreen() {
  const vm = useOrderListScreen();
  const insets = useSafeAreaInsets();
  return (
    <View style={{ paddingTop: insets.top, flex: 1 }}>
      <FlatList data={vm.rows ?? []} keyExtractor={(r) => r.id}
        refreshControl={<RefreshControl refreshing={vm.isRefetching} onRefresh={vm.refetch} />}
        renderItem={({ item }) => <OrderRow row={item} onPress={vm.handleOpen} />} />
    </View>
  );
}
```

Jebakan stack saat menulis kode di layer ini:

1. **Berkas di `app/**` (Expo Router) adalah rute, bukan layar.** Isinya satu baris merender `*Screen`; logika di sana lolos dari struktur feature dan tidak bisa diuji tanpa router.
2. **`useFocusEffect` bukan `useEffect`.** Refetch saat layar aktif kembali hanya jalan lewat focus effect; `useEffect` tidak menyala ketika stack kembali ke layar yang sudah mounted.
3. **Hardware back Android diintersep di Controller.** `BackHandler.addEventListener` wajib dilepas di cleanup; modal terbuka ditutup lebih dulu sebelum navigasi mundur.
4. **`useEffect` bersubscription (`AppState`, `Keyboard`, `BackHandler`) wajib cleanup.** Tanpanya listener menumpuk tiap layar dibuka ulang dari stack.
5. **Touch target ≥44×44 dp.** `Pressable` kecil butuh `hitSlop`; ikon 20 px tanpa `hitSlop` gagal ditekan.
6. **Safe area di root layar.** `useSafeAreaInsets()` di container layar, bukan di tiap komponen anak.
7. **`KeyboardAvoidingView` untuk form.** `behavior="padding"` iOS, `"height"` Android; tanpa itu input tertutup keyboard.
8. **Modul native butuh dev build.** Menambah paket native tanpa instruksi brief membuat Expo Go gagal load; dilarang.

Hygiene penutup unit (`agents/code-implementor.md` Fase 1): nol `any`, return type hook eksplisit, nol `console.log`, import lewat alias `tsconfig`, nol side-effect di dalam hook TanStack Query, cleanup pada listener native, komponen mengonsumsi `*UI` alih-alih DTO. `package.json`, lockfile, `app.json`, `metro.config.*`, `babel.config.*`, dan `tsconfig.json` tidak boleh dimutasi oleh brief implementasi.

## Navigation recipes

| Target | Resep lokalisasi |
|---|---|
| Route / Presentation | `Glob` `app/**/*.tsx` (Expo Router), `src/features/**/screens/*.tsx`; `Grep -n "createNativeStackNavigator\|Stack\.Screen\|<Stack "` |
| Controller | `Grep -n "export (const\|function) use\w+(Screen\|Page\|Controller)\b"` |
| View-Model | `Grep -n "export (const\|function) use\w+(ViewModel\|Rows)\b"` |
| API layer | `Grep -n "useQuery\(\{\|useMutation\(\{\|useInfiniteQuery\(\{"` |
| Cache & mutasi | `Grep -n "export const \w+_KEYS = \{\|onMutate:\|onSettled:\|invalidateQueries"` |
| Service transport | `Grep -n "axios\.create\|apiClient\.(get\|post\|put\|patch\|delete)\|fetch\("` |
| DTO | `Grep -n "export (interface\|type) \w+(DTO\|Response\|Request)\b"` |
| Kebocoran DTO ke presentasi | `Grep -n "from ['\"].*dto" src/features/**/screens/ src/features/**/components/ app/` |
| State global | `Grep -n "create<\|createSlice\(\{\|atom\("` |
| Form & skema | `Grep -n "useForm<\|zodResolver(\|= z\.object\(\{"` |
| Batas framework / platform | `Grep -n "useSafeAreaInsets\(\)\|BackHandler\.addEventListener\|useFocusEffect\(\|KeyboardAvoidingView\|Platform\.OS"` |
| Storage | `Grep -n "MMKV\|AsyncStorage\.\|SecureStore\."` |

Offset baca di sekitar baris temuan `L`: `max(1, L-15)` sampai `L+35`.

## Review checklist

#### `layer-boundaries`

- **`import ... from '../dto/...'` di `*Screen.tsx`, `components/`, atau `app/**`.** P1. Grep: `Grep -n "from.*dto" src/features/**/{screens,components}/ app/`.
- **Logika query/state di berkas `app/**`.** P2. Rute Expo Router tidak dapat diuji tanpa router.

#### `api-layer`

- **`router.push`, `navigation.navigate`, atau `Toast.show` di `hooks/api/`.** P1. Grep: `Grep -n "router\.\|navigation\.\|Toast\." src/features/**/hooks/api/`.

#### `state-scope`

- **`useQuery(` di dalam `renderItem`/komponen baris `FlatList`.** P2. Fetch per baris saat scroll.

#### `ui-states`

- **`FlatList` tanpa `ListEmptyComponent`.** P2. Daftar kosong tampil sebagai layar putih.
- **Error state tanpa tombol retry yang memanggil `refetch`.** P2.
- **Refetch latar tanpa `RefreshControl`/indikator.** P3.

#### `platform`

- **`Pressable`/`TouchableOpacity` dengan dimensi <44 dp tanpa `hitSlop`.** P2.
- **Layar tanpa `useSafeAreaInsets()`/`SafeAreaView` di root.** P2. Konten tertutup notch.
- **`BackHandler.addEventListener` tanpa `remove()` di cleanup.** P2. Grep: `Grep -n "BackHandler\.addEventListener"`, cek `return`.
- **Form tanpa `KeyboardAvoidingView`.** P3.

#### `performance`

- **`FlatList` tanpa `keyExtractor` atau dengan `renderItem` inline yang membuat closure baru per render tanpa memo.** P3.
- **Listener `AppState`/`Keyboard` tanpa cleanup.** P2.

#### `tests`

- **Typecheck diklaim hijau dari test hijau.** P1 pada laporan review — Metro membuang tipe.

## UI & navigation surface

- **Routing**: Expo Router — berkas `app/orders/[id].tsx`, parameter via `useLocalSearchParams()`, layout `app/_layout.tsx`, grup `(tabs)`; React Navigation — `Stack.Navigator` di `src/navigation/`, param bertipe lewat `RootStackParamList`. Rute ditulis ke `FLOW.md` persis seperti deklarasinya.
- **Deep-link**: skema `scheme` di `app.json` (`myapp://orders/123`); Expo Router memetakan otomatis, React Navigation lewat `linking.config`.
- **Sinkronisasi state URL**: tidak ada URL bar; state filter/page hidup di Controller atau param rute, dan wajib dinyatakan eksplisit di `FLOW.md` sebagai payload antar layar.
- **Kembali & batal**: hardware back Android (`BackHandler`), swipe-back iOS (`gestureEnabled: false` pada form dirty), header back; dirty guard lewat `navigation.addListener('beforeRemove', ...)` atau `usePreventRemove`.
- **Platform**: safe area di root, touch target ≥44×44 dp, keyboard avoidance, bottom sheet menggantikan dropdown, maksimal 2 ikon aksi di header kanan, `RefreshControl` untuk pull-to-refresh, tap di luar input menutup keyboard.
- **Design token**: `tailwind.config.*` (NativeWind), `tamagui.config.ts`, atau `src/theme/` (`StyleSheet`); token semantik dipakai lewat `useTheme()`/class.
- **Aksesibilitas**: `accessibilityLabel` dan `accessibilityRole` pada tombol ikon; `accessibilityLiveRegion="polite"` untuk pesan asinkron.

## Failure signatures

| Kategori error | Penyebab umum | Strategi resolusi yang sah |
|---|---|---|
| **TS2322 / TS2345 type mismatch** | Interface DTO berbeda tipe dari hook | Sesuaikan tipe lokal ke `CONTRACT.md`; jangan ubah tipe backend |
| **TS2307 Cannot find module** | Alias `@/*` belum di `tsconfig.paths` dan `babel-plugin-module-resolver` | Periksa keduanya |
| **Jest `Cannot use import statement outside a module`** | Paket native belum masuk `transformIgnorePatterns` | Tambahkan paket ke pola transform di `jest.config` **hanya** bila brief mengizinkan config; selain itu laporkan blocker |
| **`Invariant Violation: requireNativeComponent`** | Modul native dipakai di Expo Go / test tanpa mock | Mock modul di `jest.setup`; jangan tambah paket native tanpa brief |
| **`react-hooks/exhaustive-deps`** | Dependensi efek hilang | Lengkapi array atau `useCallback` |
| **`act()` warning** | State berubah di luar siklus test | `await act(async () => ...)` / `waitFor` dari Testing Library RN |
| **Maximum update depth exceeded** | `setState` di badan komponen | Pindahkan ke handler/efek |
| **`The action 'NAVIGATE' ... was not handled`** | Nama rute tidak terdaftar di navigator | Cocokkan dengan `RootStackParamList` / berkas `app/**` |
| **Metro `Unable to resolve module`** | Path alias atau ekstensi platform (`.ios.tsx`) salah | Perbaiki path; jangan ubah `metro.config` untuk menyembunyikannya |
| **Typecheck merah padahal test hijau** | Metro membuang tipe | Perlakukan sebagai error baru; test bukan bukti tipe |
