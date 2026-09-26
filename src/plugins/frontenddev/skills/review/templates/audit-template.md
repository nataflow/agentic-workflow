# AUDIT Template — review ad-hoc `review`

Rumah kanonik bentuk `frontenddev/reviews/<YYMMDDhhmm>-<slug>.md` — temuan review ad-hoc (`--write`) yang dapat dijadikan `finding_source` taskdir perbaikan. Bagian 1 kerangka, bagian 2 aturan, bagian 3 contoh yang tidak tersalin. Review **penutup** taskdir memakai `architect/templates/review-template.md`, bukan berkas ini.

---

## 1. Template Kanonik

````markdown
---
artifact: AUDIT_REVIEW
target: <diff | path | taskdir>
scope: <rentang commit | path | taskdir>
stack: <stack-id>
verdict: <PASS | WARNING | BLOCKED>
p1: <n>
p2: <n>
p3: <n>
reviewed_at: <YYYY-MM-DD>
---

# Review Findings — <slug>

## Summary
- Stack: <stack-id>
- Objek: <rentang | path | taskdir>
- Total Findings: <n> (<x> P1, <y> P2, <z> P3)
- Overall Status: <PASS | WARNING | BLOCKED>

## Temuan

### [P1-1] <judul>

> Status: PLANNED

- **Location**: `<file:baris>`
- **Violation**: <dimensi + penjelasan>
- **Evidence**: <cuplikan minimal>
- **Recommendation**: <perbaikan konkret>

## 9 Dimensi
| # | Dimensi | Status |
|---|---|---|
| 1 | Layer Boundaries | PASS \| P1 \| P2 \| P3 |
````

---

## 2. Aturan

1. Tiap temuan ber-ID `P{severity}-{n}` berurutan per severity dan membawa `> Status:` — `PLANNED` saat lahir; `FIXED <tanggal> — lihat <taskdir>` ditulis `code-reviewer` penutup taskdir perbaikan; `DEFERRED <tanggal> — <alasan>`/`DROPPED <tanggal> — <alasan>` ditulis `frontenddev:lead` atas keputusan user; `OBSOLETE <tanggal>` ditulis `task` saat re-verifikasi sebelum akar dikunci menemukan kodenya sudah berubah, dan ikut commit akar.
2. `verdict` diturunkan: `BLOCKED` ⇔ `p1 > 0`; `WARNING` ⇔ `p2 > 0`; selain itu `PASS`.
3. Tiap temuan berjangkar `file:baris` yang dibuka reviewer; tanpa jangkar → dibuang.
4. Berkas di-commit `docs(review): audit <slug>` — tanpa commit, ia tidak sah sebagai `finding_source` (`task` memeriksanya).

---

## 3. Contoh Terisi (tidak tersalin ke artefak)

````markdown
---
artifact: AUDIT_REVIEW
target: path
scope: src/features/cart
stack: react-vite
verdict: BLOCKED
p1: 1
p2: 0
p3: 0
reviewed_at: 2026-09-26
---

# Review Findings — cart-audit

## Summary
- Stack: react-vite
- Objek: src/features/cart
- Total Findings: 1 (1 P1, 0 P2, 0 P3)
- Overall Status: BLOCKED

## Temuan

### [P1-1] DTO bocor ke komponen presentasi

> Status: PLANNED

- **Location**: `src/features/cart/components/CartRow.tsx:3`
- **Violation**: Dimensi 1 — presentasi mengimpor `CartItemResponseDTO`.
- **Evidence**: `import { CartItemResponseDTO } from '../dto/cart.dto'`
- **Recommendation**: konsumsi `CartRowUI` dari View-Model.

## 9 Dimensi
| # | Dimensi | Status |
|---|---|---|
| 1 | Layer Boundaries | P1 |
| 2 | Data Flow & DTO | PASS |
| 3 | API Layer | PASS |
| 4 | State Scope & Ownership | PASS |
| 5 | UI & 6-State Branches | PASS |
| 6 | Platform & Framework Boundary | PASS |
| 7 | Error Handling | PASS |
| 8 | Performance & Leaks | PASS |
| 9 | Test Quality | PASS |
````
