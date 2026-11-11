"""32 L1 — langit-langit `## Steps` tidak menghitung langkah yang hanya menyentuh berkas test."""
import json

import pytest

from conftest import be_run, write_files

TD = "backenddev/docs/2601011200-refund"
VB = "plan/scripts/validate_briefs.py"
TASK = "---\nstatus: ACTIVE\nchain: BRIEF\nrisk: MAJOR\n---\n# Refund\n## Success Criteria\n- [ ] **SC-1**: refund\n"
TESTS = [f"src/test/java/acme/Refund{i}Test.java" for i in range(1, 6)]


def brief(rows, steps):
    return f"""---
title: brief 01
source: TASK.md
risk: MAJOR
status: READY
commit_message: "feat(refund): brief 01"
---
# Brief: brief 01 — 2026-01-01
## Objective
Kerjakan refund.

Covers: — (jalur LANGSUNG)
## Interfaces
- Produces: —
## File scope
**File**

| Aksi | Path | Anchor | Apa yang berubah |
|---|---|---|---|
{rows}
## Out of scope
lain
## Steps
{steps}
## Migration
tidak perlu
## Mirrored paths
tidak ada
## Risk & rollback
Rollback: revert commit.
## Work status
| Item | Status | Catatan |
|---|---|---|
| P1-1 | PLANNED | — |
## Analysis trace
Tidak ada.
"""


def _check_l(make_repo, rows, steps):
    root = make_repo({f"{TD}/TASK.md": TASK})
    write_files(root, {f"{TD}/brief-01-refund.md": brief(rows, steps)})
    proc = be_run(root, VB, "--root", str(root), "--taskdir", TD, "--json")
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}["L"]


ROWS = "\n".join(["| modify | `src/main/java/acme/RefundService.java` | `refund` | validasi |"]
                 + [f"| modify | `{p}` | `body` | fixture |" for p in TESTS])


@pytest.mark.regression("32 L1")
def test_langkah_test_tidak_dihitung(make_repo):
    steps = "\n".join(["1. Ubah `refund` di `src/main/java/acme/RefundService.java`.",
                       "2. Tambah helper `hasPhoto` di `RefundService`."]
                      + [f"{i + 3}. Lengkapi body di `Refund{i + 1}Test` dengan foto." for i in range(5)])
    c = _check_l(make_repo, ROWS, steps)
    assert c["status"] == "PASS", c


@pytest.mark.regression("32 L1")
def test_langkah_produksi_tetap_dibatasi(make_repo):
    steps = "\n".join(f"{i + 1}. Ubah `refund` di `RefundService` bagian {i + 1}." for i in range(6))
    c = _check_l(make_repo, ROWS, steps)
    assert c["status"] == "FAIL" and "6 produksi, 0 test" in " ".join(c.get("details") or [c.get("summary", "")])


@pytest.mark.regression("32 L1")
def test_langkah_tanpa_sebutan_berkas_dihitung_produksi(make_repo):
    steps = "\n".join(f"{i + 1}. Lengkapi body dengan foto." for i in range(6))
    c = _check_l(make_repo, ROWS, steps)
    assert c["status"] == "FAIL"


@pytest.mark.regression("32 L1")
def test_langkah_campuran_test_dan_produksi_dihitung_produksi(make_repo):
    steps = "\n".join(f"{i + 1}. Ubah `RefundService` dan `Refund1Test`." for i in range(6))
    c = _check_l(make_repo, ROWS, steps)
    assert c["status"] == "FAIL"
