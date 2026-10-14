# CONTRACT Template — `contract`

Rumah kanonik bentuk `frontenddev/docs/<YYMMDDhhmm>-<slug>/CONTRACT.md`. Bagian 1 adalah kerangka yang disalin ke artefak, bagian 2 aturan yang ditagih `skills/_common/validate_doc.py --kind contract`, `contract-reviewer`, dan self-test penulis, bagian 3 contoh terisi yang **tidak** tersalin ke artefak. `SKILL.md` dan `agents/contract-reviewer.md` merujuk ke sini dan dilarang menulis ulang kerangkanya.

---

## 1. Template Kanonik CONTRACT.md

````markdown
---
status: DRAFT
slug: <slug>
order: 30
stack: <stack-id>
based_on: <sha 7 digit HEAD saat artefak ditulis> (<YYYY-MM-DD>)
sections: [<salinan persis sections TASK.md>]
---

# Contract — <Nama Fitur / Modul>

Spesifikasi kontrak data, batas layer 5-tier, dan rencana eksekusi. Path berkas mengikuti `## Layer taxonomy` adapter `stack`.

# Architecture

## 1. Intent & Scope Statement
- **Intent**: <satu kalimat kapabilitas + batas teknis>
- **Target Feature**: `<feature root profil>/<feature>/`
- **Upstream References**: `TASK.md` (akar)<, `FLOW.md`, `UI.md` sesuai sections>
- **Asal Temuan**: `<finding_source TASK.md>` — `<ID temuan>` | `—`

## 2. Data Contract & Endpoints

### Endpoint: `<METHOD> <path>`
- **Deskripsi Operasi**: <...>
- **Request Payload Interface**: blok `typescript` tanpa `any`
- **Response Payload Interface (DTO)**: blok `typescript` tanpa `any`
- **Error Model Contract**: blok `typescript`
- **Error Status Mapping**: <status → pesan UI manusiawi>

## 3. Cache Management & Mutation Strategy
- **Query Key Factory Object**: blok `typescript` factory array
- **Mutation Lifecycle & Invalidation**: <onMutate / onError / onSettled atau `invalidate` sesuai adapter>

## 4. Layer Shape Specification (The 5-Tier Architecture)

| Layer | Path File Target (sesuai adapter) | Ekspor Utama | Tanggung Jawab Tunggal |
|---|---|---|---|

## 5. Decisions Not Taken

| Alternatif | Alasan Ditolak | Konsekuensi yang Diterima |
|---|---|---|

# Execution

## 1. Files Touched
- `CREATE` `<path>`
- `MODIFY` `<path>`

## 2. Execution Steps
1. <urutan penerapan lintas layer: DTO → service → API layer → view-model → controller → presentasi>

## 3. Verification Commands & Baseline
- `<perintah dari commands.md profil>` (<ambang relatif baseline>)

## 4. Proposed Units Breakdown
- **Unit 01**: <nama> (`<unit-slug>`: <layer>)

## 5. Acceptance Criteria

| ID | Skenario | Cara verifikasi | Sumber |
|---|---|---|---|
| `AC-1` | <skenario teramati> | test otomatis \| QA manual: <langkah> | `SC-{n}` · `DD-{n}` · `ST-{n}` \| `—` |
````

---

## 2. Aturan Validasi

**Mekanis** — ditagih `validate_doc.py --kind contract`; `FAIL` menahan ronde `contract-reviewer`, `chain.py draft`, dan `chain.py approve`:

1. **Frontmatter**: `status` hanya `DRAFT` atau `APPROVED` (yang kedua hanya lewat `chain.py approve`); `slug`, `stack` terisi; `order: 30`; `based_on` berpola `<sha 7 digit> (YYYY-MM-DD)`; `sections` identik dengan `sections` `TASK.md`.
2. **Struktur**: tepat satu H1 berawalan `# Contract — `, lalu `# Architecture` dengan lima `##` dan `# Execution` dengan lima `##`, persis urutan bagian 1.
3. **Files Touched**: minimal satu butir `` - `CREATE|MODIFY` `<path>` ``. Daftar ini batas union `files_touched` brief — `validate_briefs.py` Check E menagih keduanya sama.
4. **Acceptance Criteria**: `AC-{n}` berurutan dari `AC-1`; kolom *Cara verifikasi* `test otomatis` atau `QA manual: <langkah>`; kolom *Sumber* memuat token `SC-{n}`/`DD-{n}`/`ST-{n}` yang benar-benar ada di `TASK.md`/`FLOW.md`/`UI.md`, atau `—` untuk kriteria yang lahir dari kontrak sendiri.
5. **Keterlacakan dua arah**: tiap `SC-{n}` `TASK.md`, tiap `DD-{n}` `FLOW.md` (bila `sections` memuat `flow`), dan tiap `ST-{n}` `UI.md` (bila memuat `ui`) muncul di kolom *Sumber* minimal satu AC. Satu AC boleh memikul beberapa token sekaligus (`SC-2` · `ST-4`). Token hulu tanpa AC berarti janji akar atau kebutuhan layar yang tidak akan pernah dikerjakan brief mana pun.
6. **Placeholder**: nol `TBD`/`TODO`/`diisi nanti` dan nol slot `<...>` berspasi di luar blok kode.

**Semantik** — dinilai `contract-reviewer` (maks 2 ronde) lalu self-test penulis:

7. **Isolasi DTO**: tidak ada komponen presentasi di Layer Shape yang mengonsumsi DTO response; presentasi mengonsumsi `*UI` dari View-Model.
8. **API layer bebas side-effect**: navigasi, toast, dan dialog hanya di Controller.
9. **Query key factory**: tiap query berkey array factory; tiap mutasi menyebut invalidasi eksplisit.
10. **Penamaan adapter**: tiap path Layer Shape dan Files Touched mengikuti `## Layer taxonomy` adapter `stack` — `use*Page.ts` di repo Svelte atau `*.svelte` di repo React adalah cacat.
11. **Sapuan maju**: tiap field response DTO punya jalur ke props `*UI` atau dinyatakan tidak dipakai di *Decisions Not Taken*.
12. **Batas akar**: tidak ada endpoint, DTO, atau layer yang disebut `## Out of Scope` `TASK.md`.
13. Butir `test otomatis` akan punya berkas test di `files_touched` brief pengklaimnya, dan berkas itu wajib menyebut nomor AC-nya; butir `QA manual:` menyertakan langkah yang dapat diulang orang lain.

---

## 3. Contoh Terisi — `order-checkout` (tidak tersalin ke artefak)

````markdown
---
status: DRAFT
slug: order-checkout
order: 30
stack: react-vite
based_on: 7d1e0c4 (2026-09-24)
sections: [flow, ui]
---

# Contract — Order Checkout

Spesifikasi kontrak data, batas layer 5-tier, dan rencana eksekusi. Path berkas mengikuti `## Layer taxonomy` adapter `stack`.

# Architecture

## 1. Intent & Scope Statement
- **Intent**: Membuat pesanan dari keranjang aktif dan menampilkan buktinya tanpa mengubah kontrak backend.
- **Target Feature**: `src/features/checkout/`
- **Upstream References**: `TASK.md` (akar), `FLOW.md`, `UI.md`
- **Asal Temuan**: `—`

## 2. Data Contract & Endpoints

### Endpoint: `POST /api/v1/orders`
- **Deskripsi Operasi**: Membuat pesanan dari `cartId`.
- **Request Payload Interface**:
```typescript
export interface CreateOrderRequestDTO {
  cartId: string;
  note?: string;
}
```
- **Response Payload Interface (DTO)**:
```typescript
export interface OrderResponseDTO {
  id: string;
  receipt_number: string;
  paid_at: string; // ISO-8601
}
```
- **Error Model Contract**:
```typescript
export interface ApiErrorResponseDTO {
  code: string;
  message: string;
}
```
- **Error Status Mapping**: `409` → "Keranjang berubah, muat ulang"; `5xx` → banner *Coba Lagi*.

## 3. Cache Management & Mutation Strategy
- **Query Key Factory Object**:
```typescript
export const CART_KEYS = {
  all: ['cart'] as const,
  detail: () => [...CART_KEYS.all, 'detail'] as const,
};
```
- **Mutation Lifecycle & Invalidation**: `onSettled` → `invalidateQueries(CART_KEYS.all)`; navigasi ke bukti di handler `useCheckoutPage`.

## 4. Layer Shape Specification (The 5-Tier Architecture)

| Layer | Path File Target (sesuai adapter) | Ekspor Utama | Tanggung Jawab Tunggal |
|---|---|---|---|
| **DTO** | `src/features/checkout/dto/order.dto.ts` | `OrderResponseDTO` | Kontrak payload |
| **Service** | `src/features/checkout/services/order.service.ts` | `orderService` | Transport HTTP |
| **API layer** | `src/features/checkout/hooks/api/useCreateOrderMutation.ts` | `useCreateOrderMutation` | Mutasi & invalidasi |
| **View-Model** | `src/features/checkout/hooks/view-model/useReceiptViewModel.ts` | `ReceiptUI` | DTO → UI |
| **Controller** | `src/features/checkout/hooks/useCheckoutPage.ts` | `useCheckoutPage` | Orkestrasi & navigasi |
| **Presentation** | `src/features/checkout/pages/CheckoutPage.tsx` | `CheckoutPage` | Render murni |

## 5. Decisions Not Taken

| Alternatif | Alasan Ditolak | Konsekuensi yang Diterima |
|---|---|---|
| View-Model menyatu di Controller | format Rupiah & tanggal butuh unit test tanpa render | satu berkas tambahan |

# Execution

## 1. Files Touched
- `CREATE` `src/features/checkout/dto/order.dto.ts`
- `CREATE` `src/features/checkout/services/order.service.ts`
- `CREATE` `src/features/checkout/services/order.service.test.ts`
- `CREATE` `src/features/checkout/hooks/api/useCreateOrderMutation.ts`
- `CREATE` `src/features/checkout/hooks/view-model/useReceiptViewModel.ts`
- `CREATE` `src/features/checkout/hooks/useCheckoutPage.ts`
- `CREATE` `src/features/checkout/pages/CheckoutPage.tsx`

## 2. Execution Steps
1. DTO dan service beserta test service.
2. Mutasi dan query key factory.
3. View-Model bukti transaksi beserta test.
4. Controller lalu halaman.

## 3. Verification Commands & Baseline
- `pnpm typecheck` (nol galat baru; baseline 0)
- `pnpm test src/features/checkout` (hijau)

## 4. Proposed Units Breakdown
- **Unit 01**: Data & Transport (`order-api`: DTO, service, mutasi)
- **Unit 02**: Logic (`checkout-logic`: View-Model, Controller)
- **Unit 03**: Presentation (`checkout-page`: halaman)

## 5. Acceptance Criteria

| ID | Skenario | Cara verifikasi | Sumber |
|---|---|---|---|
| `AC-1` | Ringkasan menampilkan item keranjang dengan subtotal | test otomatis | `SC-1` · `DD-1` · `ST-1` |
| `AC-2` | Loading, kosong, dan initial tampil sesuai UI.md | test otomatis | `ST-2` · `ST-3` · `ST-5` |
| `AC-3` | Gagal jaringan menampilkan banner dengan *Coba Lagi* yang memanggil `refetch` | test otomatis | `ST-4` |
| `AC-4` | Konfirmasi membuat pesanan dan menampilkan nomor bukti | test otomatis | `SC-2` · `DD-2` |
| `AC-5` | CTA disabled selama mutasi berjalan | QA manual: klik Konfirmasi, amati tombol selama request | `ST-6` |
````
