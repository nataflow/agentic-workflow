# REVIEW Template — review penutup `architect`

Rumah kanonik bentuk `frontenddev/docs/<YYMMDDhhmm>-<slug>/REVIEW.md`, ditulis `agents/code-reviewer.md` sekali per rantai atas diff sejak akar. Bagian 1 adalah kerangka yang disalin ke artefak, bagian 2 aturan yang ditagih `scripts/validate_review.py`, bagian 3 contoh terisi yang **tidak** tersalin ke artefak. `dispatcher/reviewer.md` dan agent reviewer merujuk ke sini dan dilarang menulis ulang kerangkanya.

---

## 1. Template Kanonik REVIEW.md

````markdown
---
artifact: REVIEW
taskdir: frontenddev/docs/<YYMMDDhhmm>-<slug>
stack: <stack-id>
verdict: <PASS | WARNING | BLOCKED>
p1: <n>
p2: <n>
p3: <n>
base: <sha 7 digit commit akar TASK.md>
reviewed_at: <YYYY-MM-DD>
---

# Review Findings — <slug>

## Summary
- Stack: <stack-id>
- Diff: <base>..HEAD, <n> berkas di luar frontenddev/docs
- Total Findings: <n> (<x> P1, <y> P2, <z> P3)
- Overall Status: <PASS | WARNING | BLOCKED>

## Verifikasi Penutup
| Perintah | Hasil | Galat baru vs baseline |
|---|---|---|
| `<perintah dari commands.md profil>` | HIJAU \| MERAH \| TIMEOUT | 0 \| <n> |

## Cakupan Success Criteria
| SC | Vonis | Bukti |
|---|---|---|
| `SC-1` | terbukti \| belum terbukti \| PERLU VERIFIKASI MANUAL | `<file:baris>` / `<perintah hijau>` / langkah QA |

## Cakupan Acceptance Criteria
| AC | Vonis | Bukti |
|---|---|---|
| `AC-1` | terbukti \| belum terbukti \| QA manual | `<file:baris>` |

## Temuan

### [P1-1] <judul>

> Status: PLANNED

- **Location**: `<file:baris>`
- **Violation**: <dimensi + penjelasan>
- **Evidence**: <cuplikan>
- **Recommendation**: <perbaikan konkret>

## Done Criteria DITUNDA
| Brief | Butir | Vonis | Bukti |
|---|---|---|---|
| brief-<NN> | <butir> | terpenuhi \| tidak terpenuhi | <perintah + hasil> |

## Umpan balik profil
| Berkas | Pola warisan | Pola pengganti | Sumber |
|---|---|---|---|
| — | — | — | — |

## 9 Dimensi
| # | Dimensi | Status |
|---|---|---|
| 1 | Layer Boundaries | PASS \| P1 \| P2 \| P3 |
| 2 | Data Flow & DTO | PASS |
| 3 | API Layer | PASS |
| 4 | State Scope & Ownership | PASS |
| 5 | UI & 6-State Branches | PASS |
| 6 | Platform Semantics | PASS |
| 7 | Error Handling | PASS |
| 8 | Performance & Leaks | PASS |
| 9 | Test Quality & Coverage | PASS |
````

---

## 2. Aturan Validasi

Ditagih `validate_review.py`; `FAIL` menahan commit `REVIEW.md` dan membuat dispatch reviewer dianggap gagal (maks satu ulang):

1. **Frontmatter**: `artifact: REVIEW`; `verdict` enum; `p1`/`p2`/`p3` bilangan; `base` = sha commit akar `TASK.md` (commit yang melahirkannya) — sha lain `FAIL`; `reviewed_at` `YYYY-MM-DD`.
2. **Struktur**: tepat satu H1 `# Review Findings — `, lalu delapan heading `##` persis urutan bagian 1.
3. **Cakupan Success Criteria**: tepat satu baris per `SC-{n}` aktif `TASK.md` (SC gugur — `~~…~~ — gugur: <alasan>` — tidak divonis), vonis `terbukti` | `belum terbukti` | `PERLU VERIFIKASI MANUAL`. `terbukti` menuntut bukti ber-`file:baris` atau perintah ber-backtick; `PERLU VERIFIKASI MANUAL` hanya sah untuk SC ber-alat-ukur `QA manual:`.
4. **Cakupan Acceptance Criteria**: tepat satu baris per `AC-{n}` `CONTRACT.md` (lane non-MINOR), vonis `terbukti` | `belum terbukti` | `QA manual`.
5. **Temuan**: jumlah `### [P1-n]`/`[P2-n]`/`[P3-n]` sama dengan `p1`/`p2`/`p3`, nomor berurutan per severity, tiap temuan membawa baris `> Status:`.
6. **Konsistensi verdict** — diturunkan mekanis, bukan dipilih:
   - `BLOCKED` ⇔ `p1 > 0` **atau** satu saja SC `belum terbukti` **atau** verifikasi penutup merah: baris `TIMEOUT`, atau galat baru > 0. Baris `MERAH` bergalat baru 0 adalah merah warisan baseline — bukan `BLOCKED`.
   - selain itu `WARNING` ⇔ `p2 > 0` atau satu saja AC `belum terbukti`.
   - selain itu `PASS`.
7. **9 Dimensi**: sembilan baris bernomor 1–9.

Konsekuensi butir 6: rantai dengan janji akar yang belum terbukti **tidak pernah** sampai `frontenddev:report`, apa pun kebersihan kodenya.

---

## 3. Contoh Terisi — `order-checkout` (tidak tersalin ke artefak)

````markdown
---
artifact: REVIEW
taskdir: frontenddev/docs/2609231200-order-checkout
stack: react-vite
verdict: WARNING
p1: 0
p2: 1
p3: 0
base: 540364c
reviewed_at: 2026-09-25
---

# Review Findings — order-checkout

## Summary
- Stack: react-vite
- Diff: 540364c..HEAD, 7 berkas di luar frontenddev/docs
- Total Findings: 1 (0 P1, 1 P2, 0 P3)
- Overall Status: WARNING

## Verifikasi Penutup
| Perintah | Hasil | Galat baru vs baseline |
|---|---|---|
| `pnpm typecheck` | HIJAU | 0 |
| `pnpm test` | HIJAU | 0 |

## Cakupan Success Criteria
| SC | Vonis | Bukti |
|---|---|---|
| `SC-1` | terbukti | `src/features/checkout/pages/CheckoutPage.test.tsx:12` · `pnpm test` hijau |
| `SC-2` | terbukti | `src/features/checkout/hooks/useCheckoutPage.test.ts:30` |

## Cakupan Acceptance Criteria
| AC | Vonis | Bukti |
|---|---|---|
| `AC-1` | terbukti | `src/features/checkout/pages/CheckoutPage.test.tsx:12` |
| `AC-2` | terbukti | `src/features/checkout/pages/CheckoutPage.test.tsx:31` |
| `AC-3` | belum terbukti | banner error tanpa *Coba Lagi* — P2-1 |
| `AC-4` | terbukti | `src/features/checkout/hooks/useCheckoutPage.test.ts:30` |
| `AC-5` | QA manual | klik Konfirmasi, amati tombol selama request |

## Temuan

### [P2-1] Error state tanpa tombol Coba Lagi

> Status: PLANNED

- **Location**: `src/features/checkout/pages/CheckoutPage.tsx:42`
- **Violation**: Dimensi 5 & 7 — banner error tanpa aksi pemulihan.
- **Evidence**: `if (isError) return <p>Gagal</p>`
- **Recommendation**: panggil `refetch` dari `useCheckoutPage` lewat tombol *Coba Lagi*.

## Done Criteria DITUNDA
| Brief | Butir | Vonis | Bukti |
|---|---|---|---|
| brief-01 | Nol galat baru `pnpm typecheck` | terpenuhi | HIJAU |

## Umpan balik profil
| Berkas | Pola warisan | Pola pengganti | Sumber |
|---|---|---|---|
| — | — | — | — |

## 9 Dimensi
| # | Dimensi | Status |
|---|---|---|
| 1 | Layer Boundaries | PASS |
| 2 | Data Flow & DTO | PASS |
| 3 | API Layer | PASS |
| 4 | State Scope & Ownership | PASS |
| 5 | UI & 6-State Branches | P2 |
| 6 | Platform Semantics | PASS |
| 7 | Error Handling | P2 |
| 8 | Performance & Leaks | PASS |
| 9 | Test Quality & Coverage | PASS |
````
