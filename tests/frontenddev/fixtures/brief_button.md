---
status: {status}
slug: orders-lacak
stack: react-vite
based_on: {sha} (2026-09-24)
order: 40
unit: "{nn}"
total_units: "{total}"
depends_on: []
fulfills: ["SC-1"]
covers: ["AC-1"]
files_touched:
  - src/features/orders/OrderDetail.tsx
  - src/features/orders/OrderDetail.test.tsx
verification:
  - pnpm test
remedies: "{remedies}"
---

# Implementation Brief — Unit {nn}: Orders Lacak Button

Brief implementasi atomik untuk subagent `code-implementor`; satu-satunya acuan kerjanya.

## 1. Intent & Scope Boundaries
- **Intent**: menambah tombol Lacak.
- **Akar**: `SC-1` (frontmatter `fulfills`)
- **Strict Scope Boundaries**: hanya berkas `files_touched`.
- **Out of Scope (Dikerjakan pada Unit Lain)**: tidak ada

## 2. Interfaces & Contracts

```typescript
export interface OrderDetailUI { trackLabel: string }
```

## 3. Current Repo State & Reference Symbols

| Aksi | Berkas | Anchor |
|---|---|---|
| MODIFY | `src/features/orders/OrderDetail.tsx` | `OrderDetail` |
| CREATE | `src/features/orders/OrderDetail.test.tsx` | — |

- **Pola Acuan**: `src/features/orders/OrderDetail.tsx:1` komponen fungsi
- **Import Alias**: `@/`

## 4. Implementation Steps
1. {step}
2. Tulis test render label.

## 5. Done Criteria & Verification Baseline
- [ ] tombol berlabel Lacak
- [ ] (verifikasi penutup) pnpm test — nol galat baru
