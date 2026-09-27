"""B12-A — `validate_doc.py` menagih butir mekanis self-test TASK/BRD/PRD.

Fixture positif = contoh terisi ketiga template (diekstrak langsung, jadi contoh dan validator tidak
bisa bergeser diam-diam). Contoh PRD sengaja dipangkas ke 3 dari 16 dimensi Impact map; fixture
melengkapi 13 baris sisanya. Tiap test negatif merusak satu hal dan menagih FAIL tepat di check-nya.
"""
import json
import re

import pytest

from conftest import BE_SKILLS, run_script, write_files

VD = BE_SKILLS / "_common/validate_doc.py"
TD = "backenddev/docs/2609051000-order-cancel-paid"


def _example(rel, marker):
    text = (BE_SKILLS / rel).read_text(encoding="utf-8")
    text = text[text.index(marker):]
    m = re.search(r"(`{3,4})markdown\n(.*?)\n\1\n", text, re.S)
    return m.group(2) + "\n"


TASK = _example("task/templates/task-template.md", "## 3. Contoh Terisi")
BRD = _example("business-analysis/templates/brd-template.md", "## Contoh terisi")
PRD = _example("system-analysis/templates/prd-template.md", "## Contoh terisi")
PRD_FULL = PRD.replace(
    "| 3 | Transisi lifecycle | terdampak | `internal/order/state.go:27` | Task breakdown #1 |\n",
    "| 3 | Transisi lifecycle | terdampak | `internal/order/state.go:27` | Task breakdown #1 |\n"
    + "".join(f"| {n} | Dimensi {n} | tidak relevan | sapuan `internal/order/`: nihil | — |\n" for n in range(4, 17)))


@pytest.fixture
def repo(make_repo):
    return make_repo({"internal/order/service.go": "package order\n" * 150,
                      "internal/order/state.go": "package order\n" * 30,
                      f"{TD}/TASK.md": TASK, f"{TD}/BRD.md": BRD, f"{TD}/PRD.md": PRD_FULL})


def vd(repo, kind, *args):
    proc = run_script(VD, "--kind", kind, "--taskdir", TD, "--root", str(repo), "--json", *args)
    assert proc.returncode in (0, 1), proc.stderr
    out = json.loads(proc.stdout)
    assert (proc.returncode == 1) == (out["status"] == "FAIL")
    return {c["id"]: c for c in out["checks"]}


def fails(checks):
    return sorted(cid for cid, c in checks.items() if c["status"] == "FAIL")


@pytest.mark.parametrize("kind, args", [("task", ("--fresh",)), ("brd", ()), ("prd", ())])
def test_contoh_template_lolos(repo, kind, args):
    checks = vd(repo, kind, *args)
    assert fails(checks) == [], {k: c["summary"] for k, c in checks.items() if c["status"] == "FAIL"}
    assert any(c["status"] == "MANUAL" for c in checks.values())


def test_prd_contoh_dipangkas_gagal_hanya_di_p7(repo):
    write_files(repo, {f"{TD}/PRD.md": PRD})
    assert fails(vd(repo, "prd")) == ["P7"]


def test_dokumen_tidak_ada_exit_2(make_repo):
    root = make_repo({f"{TD}/.keep": ""})
    assert run_script(VD, "--kind", "task", "--taskdir", TD, "--root", str(root)).returncode == 2


# --- TASK ------------------------------------------------------------------------------------

@pytest.mark.parametrize("old, new, cid", [
    ("status: ACTIVE", "status: DRAFT", "T1"),
    ("## Out of Scope", "## Out of scope", "T1"),
    ("**SC-3**", "**SC-4**", "T2"),
    ("- [ ] **SC-2**: ", "- [ ] ", "T2"),
    ("— verifikasi: `TestCancelPaidOrder` hijau", "— verifikasi: AC-1 di PRD.md tertutup", "T3a"),
    ("— verifikasi: diff `internal/order/state.go`", "diff state", "T3a"),
    ("(`internal/order/service.go:142`)", "(`internal/order/gone.go:142`)", "T5"),
    ("state.go:27", "state.go:999", "T5"),
    ("- Pembatalan oleh pembeli — opsi yang ditolak pada klarifikasi gerbang", "- Pembatalan oleh pembeli", "T6"),
    ("Refund otomatis", "TODO refund otomatis", "T7"),
    ("Order berstatus `PAID` dapat", "Order <isi nanti> dapat", "T7"),
    ("- [ ] BRIEF — backend:plan", "- [ ] BRD — x\n- [ ] BRIEF — backend:plan", "T8a"),
    ("risk: MAJOR", "risk: MINOR", "T8a"),
    ("lane: PRD_CONVERSION", "lane: DIRECT_BRIEF", "T8a"),
])
def test_task_rusak(repo, old, new, cid):
    assert old in TASK
    write_files(repo, {f"{TD}/TASK.md": TASK.replace(old, new, 1)})
    assert cid in fails(vd(repo, "task", "--fresh"))


def test_task_t8b_hanya_dengan_fresh(repo):
    write_files(repo, {f"{TD}/TASK.md": TASK.replace("- [ ] PRD", "- [x] PRD")})
    assert "T8b" in fails(vd(repo, "task", "--fresh"))
    assert "T8b" not in vd(repo, "task")


def test_task_lane_non_planning_tanpa_chain(repo):
    text = TASK.replace("chain: PRD_BRIEF\n", "").replace("lane: PRD_CONVERSION", "lane: DEFECT_RCA")
    text = re.sub(r"## Chain\n.*?\n## Description", "## Description", text, flags=re.S)
    write_files(repo, {f"{TD}/TASK.md": text})
    assert fails(vd(repo, "task")) == []
    write_files(repo, {f"{TD}/TASK.md": text.replace("lane: DEFECT_RCA", "lane: DEFECT_RCA\nchain: BRIEF")})
    assert "T8a" in fails(vd(repo, "task"))


def test_task_counters_dan_coretan_amandemen(repo):
    text = TASK.replace("- [ ] **SC-2**: order", "- [ ] ~~**SC-2**: order") + \
        "\n## Counters\n\n| Kunci | Nilai | Plafon |\n|---|---|---|\n| <kunci> | 0 | 2 |\n"
    write_files(repo, {f"{TD}/TASK.md": text})
    assert fails(vd(repo, "task")) == []


def test_task_finding_source(repo):
    src = "backenddev/issues/2026-09-05-001-issues.md"
    assert "T3a" in fails(vd(repo, "task", "--finding-source", src))
    fixed = TASK.replace("`TestCancelPaidOrder` hijau", f"`TestCancelPaidOrder` hijau (P1-1) dan `> Status: FIXED` atas P1-1 di {src}")
    write_files(repo, {f"{TD}/TASK.md": fixed})
    assert "T3a" not in fails(vd(repo, "task", "--finding-source", src))


# --- BRD -------------------------------------------------------------------------------------

@pytest.mark.parametrize("old, new, cid", [
    ("requester: Pemilik toko (via CS)\n", "", "B1"),
    ("## Target state", "## Target State", "B1"),
    ("**BR-2**", "**BR-3**", "B2"),
    ("Pensiun: tidak ada", "Pensiun: BR-2 → BR-3 (makna berubah)", "B2"),
    ("Observasi kode: `internal/order/state.go:27`", "`internal/order/state.go:27`", "B3"),
    ("Tidak ada pertanyaan terbuka", "", "B5"),
    ("Tidak ada pertanyaan terbuka", "- **Apakah refund ikut?** — terdampak: `## Business rules`; sementara dipakai: tidak", "B6"),
    ("Tidak ada pertanyaan terbuka", "- **Apakah refund ikut?** — sementara dipakai: tidak", "B6"),
    ("digerakkan: SC-1", "digerakkan: SC-9", "B7a"),
    ("; digerakkan: SC-1", "", "B7a"),
    ("**EC-1** [status-eksternal]", "**EC-1** [race]", "B8"),
    ("`timeout` — tidak ada alokasi berbatas waktu", "", "B8"),
    ("(sistem)", "(integrasi)", "B9"),
    ("- **Pembeli** (terlarang)", "- **Pembeli** (primer)", "B9"),
    ("- Operasional: ±2 jam kerja CS per minggu untuk pembatalan manual\n", "", "B10"),
    ("Terjadi insidental, ±20", "Terjadi ±20", "B10"),
    ("## Business metrics", "## Success criteria", "B11"),
])
def test_brd_rusak(repo, old, new, cid):
    assert old in BRD
    write_files(repo, {f"{TD}/BRD.md": BRD.replace(old, new, 1)})
    assert cid in fails(vd(repo, "brd"))


def test_brd_pensiun_sah(repo):
    text = BRD.replace("- **BR-2**: Pembatalan", "- **BR-3**: Pembatalan").replace(
        "Pensiun: tidak ada", "Pensiun: BR-2 → BR-3 (gudang tujuan berubah)")
    write_files(repo, {f"{TD}/BRD.md": text})
    assert "B2" not in fails(vd(repo, "brd"))


def test_brd_user_generik_hanya_warn(repo):
    write_files(repo, {f"{TD}/BRD.md": BRD.replace("(primer) — boleh:", "(primer) — boleh: seperti user lain,")})
    checks = vd(repo, "brd")
    assert checks["B9"]["status"] == "WARN" and "B9" not in fails(checks)


def test_brd_tanpa_task_digerakkan_strip(repo):
    (repo / TD / "TASK.md").unlink()
    assert "B7a" in fails(vd(repo, "brd"))
    write_files(repo, {f"{TD}/BRD.md": BRD.replace("digerakkan: SC-1", "digerakkan: —")})
    assert "B7a" not in fails(vd(repo, "brd"))


# --- PRD -------------------------------------------------------------------------------------

@pytest.mark.parametrize("old, new, cid", [
    ("| test otomatis | BR-1, EC-1 | SC-2 |", "| test otomatis | BR-1 | SC-2 |", "P2"),
    ("| test otomatis | BR-1, EC-1 | SC-2 |", "| test otomatis | BR-1, EC-1, BR-7 | SC-2 |", "P1"),
    ("| SC-1, SC-3 |", "| SC-1 |", "P3"),
    ("| test otomatis | BR-1, EC-1 | SC-2 |", "| diuji manual | BR-1, EC-1 | SC-2 |", "P5"),
    ("| test otomatis | BR-1, EC-1 | SC-2 |", "| QA manual: jalankan `TestCancelFulfilled` | BR-1, EC-1 | SC-2 |", "P5"),
    ("source_brd: backenddev", "source: backenddev", "P6"),
    ("## Migration requirements", "## Migration", "P6"),
    ("| 3 | Transisi lifecycle | terdampak | `internal/order/state.go:27` | Task breakdown #1 |",
     "| 3 | Transisi lifecycle | terdampak | `internal/order/state.go:27` | Task breakdown #9 |", "P7"),
    ("| 4 | Dimensi 4 | tidak relevan | sapuan `internal/order/`: nihil | — |",
     "| 4 | Dimensi 4 | tidak relevan | tidak ada | — |", "P7"),
    ("| `POST /orders/{id}/cancel` | `ORDER_CANCEL` |", "| `POST /orders/{id}/cancel` |  |", "P8"),
    ("Tidak perlu — kolom", "TBD — kolom", "P8"),
    ("Tidak ada — semua pertanyaan terjawab",
     "- **Batas refund?** — terdampak: `## Task breakdown`; sementara dipakai: tanpa refund", "P9"),
    ("Tidak ada — semua pertanyaan terjawab",
     "- **Kode izin?** — terdampak: `## Validation policy`; sementara dipakai: `ORDER_CANCEL`", "P9b"),
    ("`internal/order` · state", "`internal/order/state.go`", "P10"),
    ("| test AC hijau |", "| `TestCancelPaidOrder` hijau |", "P10"),
])
def test_prd_rusak(repo, old, new, cid):
    assert old in PRD_FULL
    write_files(repo, {f"{TD}/PRD.md": PRD_FULL.replace(old, new, 1)})
    assert cid in fails(vd(repo, "prd"))


def test_prd_br_disanggah_menutup_p1(repo):
    text = PRD_FULL.replace("| test otomatis | BR-1, BR-2 | SC-1, SC-3 |", "| test otomatis | BR-1 | SC-1, SC-3 |")
    text = text.replace("| PAID | CANCELLED | pemilik toko | `stock_deducted_at` kosong | stok tiap item dikembalikan | BR-1, BR-2 |",
                        "| PAID | CANCELLED | pemilik toko | `stock_deducted_at` kosong | stok tiap item dikembalikan | BR-1 |")
    text = text.replace("Tidak ada — semua pertanyaan terjawab",
                        "- **BR-DISANGGAH: BR-2** — alasan: stok dikembalikan job terpisah; sementara dipakai: stok tetap")
    write_files(repo, {f"{TD}/PRD.md": text})
    assert "P1" not in fails(vd(repo, "prd"))


def test_prd_tanpa_brd_melewati_p1_p2(repo):
    text = PRD_FULL.replace("source_brd: backenddev/docs/2609051000-order-cancel-paid/BRD.md",
                            "source_brd: tidak ada — sumbu bisnis nol")
    write_files(repo, {f"{TD}/PRD.md": text})
    (repo / TD / "BRD.md").unlink()
    checks = vd(repo, "prd")
    assert checks["P1"]["status"] == "PASS" and "dilewati" in checks["P1"]["summary"]
    assert fails(checks) == []


def test_crlf_dan_bom(repo):
    write_files(repo, {f"{TD}/TASK.md": "﻿" + TASK.replace("\n", "\r\n")})
    assert fails(vd(repo, "task", "--fresh")) == []


def test_placeholder_di_code_fence_diabaikan(repo):
    write_files(repo, {f"{TD}/TASK.md": TASK.replace("## Out of Scope", "```\nTODO <slot>\n```\n\n## Out of Scope")})
    assert "T7" not in fails(vd(repo, "task"))


def test_prd_br_brd_tak_tercakup(repo):
    write_files(repo, {f"{TD}/BRD.md": BRD.replace("\n\nPensiun: tidak ada",
                                                    "\n- **BR-3**: Pembatalan dicatat di audit log\n\nPensiun: tidak ada")})
    checks = vd(repo, "prd")
    assert "P1" in fails(checks) and "BR-3" in checks["P1"]["summary"]
