"""`plan/scripts/validate_briefs.py`: predikat per token/segmen, bukan substring (L5.3)."""
import json

import pytest

from conftest import be_run, write_files

TD = "backenddev/docs/2601011200-refund"
VB = "plan/scripts/validate_briefs.py"

TASK = """---
status: ACTIVE
chain: PRD_BRIEF
risk: MAJOR
---
# Refund
## Success Criteria
- [ ] **SC-1**: refund tercatat
## Out of Scope
- `src/payment/` — modul pembayaran tidak disentuh
"""

PRD = """---
status: APPROVED
---
# PRD
## Acceptance criteria
| ID | Kriteria | Verifikasi |
|---|---|---|
| AC-1 | tombol refund tampil | QA manual |
| AC-10 | refund tersimpan | test otomatis |
## Migration requirements
{migration}
"""


def brief_text(nn, covers, rows, migration="tidak perlu", rr="Rollback: revert commit.", extra=""):
    return f"""---
title: brief {nn}
source: PRD.md
risk: MAJOR
status: READY
commit_message: "feat(refund): brief {nn}"
---
# Brief: brief {nn} — 2026-01-01
## Objective
Kerjakan refund.

Covers: {covers}
## Interfaces
- Produces: `Refund{nn}`
## File scope
**File**

| Aksi | Path | Anchor | Apa yang berubah |
|---|---|---|---|
{rows}
## Out of scope
lain
## Steps
1. Ubah `Refund{nn}`. {extra}
## Migration
{migration}
## Mirrored paths
tidak ada
## Risk & rollback
{rr}
## Work status
| Item | Status | Catatan |
|---|---|---|
| P1-1 | PLANNED | — |
## Analysis trace
Tidak ada.
"""


ROW_02 = "| create | `src/refund/store_test.go` | — | AC-10: assert tersimpan |"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TD}/TASK.md": TASK, f"{TD}/PRD.md": PRD.format(migration="tidak perlu")})
    write_files(root, {f"{TD}/brief-01-x.md": brief_text(
        "01", "AC-1", "| create | `src/refund/ui.go` | — | tombol |",
        rr="AC-1: klik tombol refund, pastikan tampil. Rollback: revert.")})
    return root


def b02(repo, **kw):
    kw.setdefault("rows", ROW_02)
    write_files(repo, {f"{TD}/brief-02-x.md": brief_text("02", "AC-10", **kw)})


def check(repo, cid, *args):
    proc = be_run(repo, VB, "--root", str(repo), "--taskdir", TD, "--json", *args)
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}[cid]


def path_violations(c):
    return [d for d in c.get("details") or [] if "TERDEGRADASI" not in d]


def test_ac1_tidak_diklaim_brief_ac10(repo):
    b02(repo)
    assert check(repo, "I")["status"] == "PASS"


def test_manual_ac_butuh_id_persis(repo):
    write_files(repo, {f"{TD}/brief-01-x.md": brief_text(
        "01", "AC-1", "| create | `src/refund/ui.go` | — | tombol |", rr="AC-10: cek. Rollback: revert.")})
    b02(repo)
    c = check(repo, "I")
    assert c["status"] == "FAIL" and any("`AC-1`" in d for d in c["details"])


def test_file_scope_per_segmen(repo):
    b02(repo, rows="| create | `src/refundhistory/store_test.go` | — | AC-10: assert tersimpan |")
    c = check(repo, "E", "--file-scope", "src/refund")
    assert c["status"] == "FAIL" and any("src/refundhistory" in d for d in c["details"])


def test_out_of_scope_per_segmen(repo):
    b02(repo, rows="| create | `src/payments_report.go` | — | AC-10: assert tersimpan |")
    assert path_violations(check(repo, "E")) == []


def test_scope_nama_lepas_cocok_segmen(repo):
    write_files(repo, {f"{TD}/TASK.md": TASK.replace("`src/payment/`", "`config.yaml`")})
    b02(repo, rows="| modify | `deploy/config.yaml` | `port` | AC-10: assert tersimpan |")
    c = check(repo, "E")
    assert c["status"] == "FAIL" and any("deploy/config.yaml" in d for d in path_violations(c))


def test_mongo_testcontainer_bukan_perintah(repo):
    b02(repo, extra="Pakai Mongo TestContainer yang sudah ada.")
    assert check(repo, "F")["status"] == "PASS"


def test_go_test_berbacktick_tetap_ditolak(repo):
    b02(repo, extra="Lalu jalankan `go test ./...`.")
    c = check(repo, "F")
    assert c["status"] == "FAIL" and any("`go test`" in d for d in c["details"])


def test_migration_tidak_diperlukan_bukan_pemilik(repo):
    b02(repo, migration="Tidak diperlukan — tidak ada perubahan skema.")
    assert check(repo, "J")["status"] == "SKIP"


def test_prd_migration_tidak_perlu_di_tengah_kalimat(repo):
    write_files(repo, {f"{TD}/PRD.md": PRD.format(
        migration="Kolom lama tidak perlu dihapus; tambah kolom `refund_reason` (ALTER TABLE).")})
    b02(repo)
    c = check(repo, "J")
    assert c["status"] == "FAIL" and any("tidak satu pun brief" in d for d in c["details"]), c


def test_brief_status_huruf_kecil_bukan_ready(repo):
    write_files(repo, {f"{TD}/brief-02-x.md": brief_text("02", "AC-10", ROW_02).replace(
        "status: READY", "status: ready")})
    c = check(repo, "S")
    assert c["status"] == "FAIL" and any("brief-02-x.md" in d for d in c["details"])
