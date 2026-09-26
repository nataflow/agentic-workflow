#!/usr/bin/env bash
# Rantai HOTFIX_MINOR frontenddev yang tuntas sampai `closing review PASS` (ter-commit) dan
# `REPORT.md` tertulis tetapi belum di-commit. Pemakaian: minor_chain_reviewed.sh <repo> <skills>.
# Asal: reproduksi L4.6 (`issues/04-frontenddev-revisi-validator.md`).
set -eu
export PYTHONDONTWRITEBYTECODE=1
P=$2
CH="python3 $P/_common/chain.py"
T=frontenddev/docs/2609231200-order-checkout
q() { "$@" >/dev/null || { echo "LANGKAH GAGAL: $*"; "$@"; exit 1; }; }
mkdir -p "$1"; cd "$1"
git init -q -b main .; git config user.email t@t; git config user.name t; git config commit.gpgsign false
printf '.explore/\n' > .gitignore; mkdir -p .claude/profile src $T
echo '{"dependencies":{"react":"19.0.0"},"devDependencies":{"vite":"6.0.0"}}' > package.json
echo '{"stack":"react-vite","source_root":"src"}' > .claude/profile/index.json
printf '| Perintah | Status |\n|---|---|\n| `pnpm test` | OK |\n\n- `typecheck-per-brief`: `ya`\n' > .claude/profile/commands.md
for f in stack structure surface-map invariants layer-adoption visual drift manual-notes; do echo 'tidak terdeteksi' > .claude/profile/$f.md; done
echo 'export const App = () => null;' > src/App.tsx
git add -A; git commit -qm init
cat > $T/TASK.md <<'EOF'
---
status: ACTIVE
lane: HOTFIX_MINOR
sections: []
created: 2026-09-23
---

# Order button — perbaikan label

## Description

Tombol order wajib berlabel Pesan (`src/App.tsx:1`).

## Success Criteria

- [ ] **SC-1**: tombol order menampilkan label Pesan — verifikasi: test `OrderButton.test.tsx` hijau

## Out of Scope

- styling tombol — batas modul

## Chain

EOF
q $CH init --taskdir $T
git add $T/TASK.md; git commit -qm "docs(order-checkout): kunci TASK.md"
BASE=$(git rev-parse --short HEAD)
cat > $T/brief-01-order-button.md <<EOF
---
status: READY
slug: order-checkout
stack: react-vite
based_on: $BASE (2026-09-23)
order: 40
unit: "01"
total_units: "1"
depends_on: []
fulfills: ["SC-1"]
covers: []
files_touched:
  - src/features/order/OrderButton.tsx
  - src/features/order/OrderButton.test.tsx
verification:
  - pnpm test
---

# Implementation Brief — Unit 01: Order Button

Brief implementasi atomik untuk subagent \`code-implementor\`; satu-satunya acuan kerjanya.

## 1. Intent & Scope Boundaries
- **Intent**: menambah tombol order berlabel Pesan.
- **Akar**: \`SC-1\` (frontmatter \`fulfills\`)
- **Strict Scope Boundaries**: hanya berkas \`files_touched\`.
- **Out of Scope (Dikerjakan pada Unit Lain)**: tidak ada

## 2. Interfaces & Contracts

\`\`\`typescript
export interface OrderButtonUI { label: string }
\`\`\`

## 3. Current Repo State & Reference Symbols

| Aksi | Berkas | Anchor |
|---|---|---|
| CREATE | \`src/features/order/OrderButton.tsx\` | — |
| CREATE | \`src/features/order/OrderButton.test.tsx\` | — |

- **Pola Acuan**: \`src/App.tsx:1\` komponen fungsi
- **Import Alias**: \`@/\`

## 4. Implementation Steps
1. Tulis komponen OrderButton yang merender label Pesan.
2. Tulis test render label.

## 5. Done Criteria & Verification Baseline
- [ ] tombol berlabel Pesan
- [ ] (verifikasi penutup) pnpm test — nol galat baru
EOF
git add $T/brief-01-order-button.md; git commit -qm "docs(order-checkout): draft breakdown (1 briefs)"
q $CH approve --taskdir $T --row BRIEF --answer "setuju"
mkdir -p src/features/order
echo 'export const OrderButton = () => <button>Pesan</button>;' > src/features/order/OrderButton.tsx
echo 'test("x", () => { expect(1).toBe(1) })' > src/features/order/OrderButton.test.tsx
printf -- '---\nartifact: UNIT_REPORT\nunit: "01"\nbrief: brief-01-order-button.md\nstatus: DONE\n---\n\n# Unit 01 — order-button\n' > $T/report-01.md
sed -i 's/^status: READY/status: DONE/' $T/brief-01-order-button.md
git add src $T/brief-01-order-button.md $T/report-01.md
git commit -qm "feat(order-checkout): implement unit 01 - order button"
cat > $T/REVIEW.md <<EOF
---
artifact: REVIEW
taskdir: $T
stack: react-vite
verdict: PASS
p1: 0
p2: 0
p3: 0
base: $BASE
reviewed_at: $(git log -1 --format=%cs $BASE)
---

# Review Findings — order-checkout

## Summary
- Stack: react-vite
- Total Findings: 0 (0 P1, 0 P2, 0 P3)
- Overall Status: PASS

## Verifikasi Penutup
| Perintah | Hasil | Galat baru vs baseline |
|---|---|---|
| \`pnpm test\` | HIJAU | 0 |

## Cakupan Success Criteria
| SC | Vonis | Bukti |
|---|---|---|
| \`SC-1\` | terbukti | \`src/features/order/OrderButton.test.tsx:1\` |

## Cakupan Acceptance Criteria
| AC | Vonis | Bukti |
|---|---|---|

## Temuan

## Done Criteria DITUNDA
| Brief | Butir | Vonis | Bukti |
|---|---|---|---|

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
| 5 | UI & 6-State Branches | PASS |
| 6 | Platform & Framework Boundary | PASS |
| 7 | Error Handling | PASS |
| 8 | Performance & Leaks | PASS |
| 9 | Test Quality | PASS |
EOF
git add $T/REVIEW.md; git commit -qm "docs(order-checkout): closing review PASS"
printf '# Order button — perbaikan label — Report\n\n## Ringkasan\n\nTombol order kini berlabel Pesan.\n\n## Perubahan\n\n- tombol order baru beserta test (src/features/order)\n' > $T/REPORT.md
