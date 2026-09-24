# Comprehensive Frontend Architecture Review Checklist

Daftar periksa verifikasi cepat (*quick checklist*) per layer dan format laporan temuan untuk review ad-hoc `frontenddev:review`. Kueri grep deteksi otomatis per stack ada di `## Review checklist` dan `## Navigation recipes` adapter `stacks/<stack-id>.md`.

---

## 0. Verification Baseline Checklist (opsional, Phase 1)

- [ ] Perintah `typecheck`, `lint`, `test`, `build` diambil dari `commands.md` profil (bukan diketik dari ingatan stack lain).
- [ ] Kolom **Cakupan yang TIDAK Diperiksa** dibaca sebelum menyimpulkan; test hijau tidak diklaim sebagai bukti typecheck bila adapter menyatakan sebaliknya.
- [ ] Error baru dibedakan dari error pre-existing baseline; error baru diklasifikasi lewat `## Failure signatures` adapter.

---

## 1. Quick Review Checklist by Architecture Layer

### A. DTO & Service Layer:
- [ ] DTO interface dideklarasikan di `dto/*.dto.ts` feature.
- [ ] Tidak ada penggunaan tipe `any` atau `as any` pada payload request/response.
- [ ] Service menggunakan instance HTTP client bersama dari `layer-adoption.md` profil (SvelteKit `load`: `event.fetch`).
- [ ] Unit test service memverifikasi skenario sukses dan gagal (400, 401, 500).

### B. API Layer:
- [ ] Query key dideklarasikan menggunakan object array factory `FEATURE_KEYS`.
- [ ] Tidak ada pemanggilan navigasi, toast, atau alert di opsi `onSuccess`/`onError`.
- [ ] Invalidasi diletakkan pada `onSettled` mutasi (atau `invalidate('app:<key>')` bila memakai `load`).
- [ ] Nilai `staleTime` dan `gcTime` dikonfigurasi sesuai karakteristik data.

### C. View-Model Layer:
- [ ] View-Model mengekspor tipe data UI murni dengan akhiran `*UI`.
- [ ] Seluruh transformasi format mata uang, tanggal, dan badge status dibungkus memo/derived sesuai idiom adapter.
- [ ] View-Model memiliki unit test mandiri tanpa merender komponen.

### D. Controller Layer:
- [ ] Controller mengorkestrasi state form, dialog modal, query, dan handler.
- [ ] Handler aksi mengeksekusi navigasi dan notifikasi toast setelah mutasi berhasil.
- [ ] Referensi handler stabil (React: `useCallback`; Svelte: fungsi di modul rune) sesuai idiom adapter.

### E. Presentation & Sub-Components:
- [ ] Komponen layar hanya memanggil Controller dan membagikan props ke anak komponen.
- [ ] Komponen anak tidak memicu fetch query mandiri secara terisolasi.
- [ ] Seluruh 6 cabang state (Initial, Loading, Empty, Error, Ready, Stale) tertangani.
- [ ] Batas platform adapter dipatuhi: safe area & touch target ≥44 dp (RN), nol import server-only (SvelteKit), env `VITE_*` (SPA).

---

## 2. Sample Findings Report (chat)

```markdown
# Review Findings — checkout-flow

## Summary: 2 Findings (1 P1, 1 P2, 0 P3)
- Stack: react-vite

### [P1] DTO Response Leaking directly into CartItem Component
- **Location**: `src/features/checkout/components/CartItem.tsx:14`
- **Violation**: Dimension 1 (Layer Boundaries) & Dimension 2 (DTO Integrity). Komponen presentasi mengimpor `CartItemResponseDTO` langsung dari folder dto.
- **Evidence**:
  ```typescript
  import { CartItemResponseDTO } from '../dto/cart.dto';
  export const CartItem = ({ item }: { item: CartItemResponseDTO }) => ...
  ```
- **Recommendation**: Buat interface `CartItemUI` pada View-Model dan petakan nilai `amount_cents` ke `formattedPrice` sebelum dikonsumsi oleh komponen `CartItem`.

---

### [P2] Query Error State Missing Retry Action Button
- **Location**: `src/features/checkout/pages/CheckoutPage.tsx:42`
- **Violation**: Dimension 5 (6-State Branches) & Dimension 7 (Error Handling).
- **Evidence**:
  ```typescript
  if (isError) return <div className="text-red-500">Terjadi kesalahan.</div>;
  ```
- **Recommendation**: Tambahkan tombol aksi `[Coba Lagi]` yang memanggil handler `refetch` dari Controller `useCheckoutPage`.
```

---

## 3. Muara Laporan

- **Chat** (tanpa `--write`): format bagian 2, tanpa berkas.
- **`--write`**: `frontenddev/reviews/<YYMMDDhhmm>-<slug>.md` persis `templates/audit-template.md`, di-commit `docs(review): audit <slug>` — dapat dijadikan `finding_source` taskdir perbaikan lewat `frontenddev:lead`.
- **Tidak pernah** `<taskdir>/REVIEW.md`: review penutup rantai milik `frontenddev:architect` + `code-reviewer`, dengan kerangka `architect/templates/review-template.md`.
