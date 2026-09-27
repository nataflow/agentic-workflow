---
status: DRAFT
slug: orders-lacak
order: 30
stack: react-vite
based_on: {sha} (2026-09-24)
sections: [architecture]
---

# Contract — Orders Lacak

# Architecture

## 1. Intent & Scope Statement
- **Intent**: Tombol lacak.

## 2. Data Contract & Endpoints

### Endpoint: `GET /api/v1/orders/:id/tracking`
- **Deskripsi Operasi**: ambil status.

## 3. Cache Management & Mutation Strategy
- **Query Key Factory Object**: ORDER_KEYS.

## 4. Layer Shape Specification (The 5-Tier Architecture)

| Layer | Path | Ekspor | Tanggung Jawab |
|---|---|---|---|
| **Presentation** | `src/features/orders/OrderDetail.tsx` | `OrderDetail` | render |

## 5. Decisions Not Taken

| Alternatif | Alasan | Konsekuensi |
|---|---|---|
| modal | tidak perlu | - |

# Execution

## 1. Files Touched
- `MODIFY` `src/features/orders/OrderDetail.tsx`
- `CREATE` `src/features/orders/OrderDetail.test.tsx`

## 2. Execution Steps
1. Tambah tombol.

## 3. Verification Commands & Baseline
- `pnpm typecheck` (nol galat baru)

## 4. Proposed Units Breakdown
- **Unit 01**: Presentasi (`orders-lacak-button`: presentasi)

## 5. Acceptance Criteria

| ID | Skenario | Cara verifikasi | Sumber |
|---|---|---|---|
| `AC-1` | Tombol Lacak tampil | test otomatis | `SC-1` |
