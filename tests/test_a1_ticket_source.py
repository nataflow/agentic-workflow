"""A1 (08a) varian penuh — kontrak serah-terima `ticket_source` analyst → backenddev/frontenddev.

Tiket READY di sini dibuat `analyst/skills/_common/ticket.py` sungguhan (`review` → `approve` → `ref`),
jadi subjek commit yang dibaca `ticket_source_verdict` kedua plugin tidak bisa bergeser diam-diam dari
penulisnya.
"""
import json
from pathlib import Path

import pytest

from conftest import BE_SKILLS, FE_SKILLS, PLUGINS, be_checks, be_profile, commit, fe_profile, fe_run, run_script, write_files

TICKET_PY = PLUGINS / "analyst/skills/_common/ticket.py"
FIXTURE = Path(__file__).resolve().parent / "analyst" / "fixtures" / "ticket_valid.md"
TDIR = "analyst/tickets/2609231400-cicilan"
TICKET = f"{TDIR}/TICKET.md"
BE_TD = "backenddev/docs/2609241000-invoice-installment"
FE_TD = "frontenddev/docs/2609241000-invoice-installment"


def tk(root, *args):
    proc = run_script(TICKET_PY, *args, cwd=root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc


@pytest.fixture
def repo(make_repo):
    """Tiket DRAFT sah (AC-1, AC-2, BR-1) ter-commit, profil kedua plugin engineer, dan dua taskdir kosong."""
    root = make_repo({TICKET: FIXTURE.read_text(encoding="utf-8"), f"{BE_TD}/.keep": "", f"{FE_TD}/.keep": "",
                      "internal/invoice/service.go": "package invoice\n" * 40,
                      "src/features/invoice/InvoiceDetail.tsx": "export {}\n" * 40})
    be_profile(root, "go")
    fe_profile(root, "react-vite")
    commit(root, "init")
    return root


@pytest.fixture
def ready(repo):
    tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS")
    tk(repo, "approve", "--ticketdir", TDIR, "--answer", "ok")
    return repo


def be_ticket_check(root, ticket):
    return be_checks(root, "task/scripts/check_preconditions.py", "--root", str(root), "--taskdir", BE_TD,
                     "--lane", "DIRECT_BRIEF", "--chain", "BRIEF", "--ticket-source", ticket)[7]


def fe_ticket_check(root, ticket):
    r = fe_run(root, "task/scripts/check_preconditions.py", "--root", str(root), "--taskdir", FE_TD,
               "--lane", "HOTFIX_MINOR", "--sections", "-", "--ticket-source", ticket, "--json")
    return {c["id"]: c for c in json.loads(r.stdout)["checks"]}[8]


CHECKERS = pytest.mark.parametrize("check", [be_ticket_check, fe_ticket_check], ids=["backenddev", "frontenddev"])


# --- prasyarat `task`: READY & terkunci ------------------------------------------------------

@pytest.mark.regression("A1")
@CHECKERS
def test_tiket_ready_hasil_approve_lolos(ready, check):
    c = check(ready, TICKET)
    assert c["status"] == "PASS" and "docs(ticket): kunci TICKET cicilan READY" in c["summary"], c


@pytest.mark.regression("A1")
@CHECKERS
def test_ref_sesudah_ready_tetap_lolos(ready, check):
    tk(ready, "ref", "--ticketdir", TDIR, "--ref", "FIN-123")
    assert check(ready, TICKET)["status"] == "PASS"


@pytest.mark.regression("A1")
@CHECKERS
def test_tiket_draft_ditolak(repo, check):
    c = check(repo, TICKET)
    assert c["status"] == "FAIL" and "`DRAFT`" in c["summary"], c


@pytest.mark.regression("A1")
@CHECKERS
def test_suntingan_sesudah_approve_drift(ready, check):
    p = ready / TICKET
    p.write_text(p.read_text(encoding="utf-8").replace("minimal Rp 50.000.000", "minimal Rp 10.000.000"),
                 encoding="utf-8")
    c = check(ready, TICKET)
    assert c["status"] == "FAIL" and "DRIFT" in c["summary"] and "analyst:spec" in c["action"], c
    commit(ready, "chore: ubah ambang cicilan", TICKET)
    c = check(ready, TICKET)
    assert c["status"] == "FAIL" and "chore: ubah ambang cicilan" in c["summary"], c


@pytest.mark.regression("A1")
@CHECKERS
@pytest.mark.parametrize("value, needle", [
    (f"{BE_TD}/TASK.md", "bukan path TICKET.md analyst"),
    ("analyst/tickets/2609231400-lain/TICKET.md", "tidak ada di disk"),
])
def test_path_bukan_tiket_ditolak(repo, check, value, needle):
    c = check(repo, value)
    assert c["status"] == "FAIL" and needle in c["summary"], c


@CHECKERS
def test_tanpa_tiket_lolos(repo, check):
    assert check(repo, "")["status"] == "PASS"


# --- keterpikulan `TAC-{n}` di TASK.md --------------------------------------------------------

BE_TASK = """---
status: ACTIVE
chain: BRIEF
lane: DIRECT_BRIEF
risk: MINOR
created: 2026-09-24
ticket_source: {ticket}
---

# Invoice — cicilan invoice korporat

## Chain

- [ ] BRIEF — backenddev:plan             → brief-*.md

## Description

Invoice korporat bernilai besar dapat dicicil. Saat ini invoice hanya punya satu tagihan penuh (`internal/invoice/service.go:12`).

## Success Criteria

- [ ] **SC-1**: jadwal 3 cicilan tersimpan untuk invoice korporat Rp 60.000.000 (TAC-1) — verifikasi: `TestCreateInstallments` hijau
{sc}
## Out of Scope

- Pengingat jatuh tempo — ditunda ke tiket terpisah
{oos}"""

FE_TASK = """---
status: ACTIVE
lane: HOTFIX_MINOR
sections: -
created: 2026-09-24
ticket_source: {ticket}
---
# Invoice — tombol cicilan

## Description
Tombol cicilan tampil di detail invoice (`src/features/invoice/InvoiceDetail.tsx:3`).

## Success Criteria
- [ ] **SC-1**: tombol Buat Cicilan tampil di detail invoice korporat (TAC-1) — verifikasi: test `InvoiceDetail.test.tsx` hijau
{sc}
## Out of Scope
- Pengingat jatuh tempo — ditunda ke tiket terpisah
{oos}
## Chain

- [ ] BRIEF    — frontenddev:plan      → brief-*.md
"""


def be_task_checks(root):
    proc = run_script(BE_SKILLS / "_common/validate_doc.py", "--kind", "task", "--taskdir", BE_TD,
                      "--root", str(root), "--json")
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


def fe_task_checks(root):
    r = fe_run(root, "task/scripts/validate_task.py", "--root", str(root), "--taskdir", FE_TD, "--json")
    return {c["id"]: c for c in json.loads(r.stdout)["checks"]}


VALIDATORS = pytest.mark.parametrize("td, tmpl, run, cid", [
    (BE_TD, BE_TASK, be_task_checks, "T10"),
    (FE_TD, FE_TASK, fe_task_checks, 7),
], ids=["backenddev", "frontenddev"])


def write_task(root, td, tmpl, sc="", oos="", ticket=TICKET):
    write_files(root, {f"{td}/TASK.md": tmpl.format(ticket=ticket, sc=sc, oos=oos)})


@pytest.mark.regression("A1")
@VALIDATORS
def test_tac_tanpa_pemikul_gagal(ready, td, tmpl, run, cid):
    write_task(ready, td, tmpl)
    c = run(ready)[cid]
    assert c["status"] == "FAIL" and "TAC tanpa SC pemikul maupun `## Out of Scope`: TAC-2" in c["summary"], c


@pytest.mark.regression("A1")
@VALIDATORS
@pytest.mark.parametrize("where", ["sc", "oos"])
def test_tac_dipikul_sc_atau_out_of_scope_lolos(ready, td, tmpl, run, cid, where):
    extra = {"sc": ("- [ ] **SC-2**: invoice Rp 40.000.000 tanpa pilihan cicilan (TAC-2) — verifikasi: "
                    "test `InstallmentThreshold.test.ts` hijau", ""),
             "oos": ("", "- TAC-2 tombol cicilan disembunyikan — porsi frontend")}[where]
    write_task(ready, td, tmpl, *extra)
    checks = run(ready)
    assert checks[cid]["status"] == "PASS", checks[cid]
    assert [k for k, c in checks.items() if c["status"] == "FAIL"] == [], checks


@pytest.mark.regression("A1")
@VALIDATORS
def test_tac_hantu_gagal(ready, td, tmpl, run, cid):
    write_task(ready, td, tmpl, oos="- TAC-2 tombol cicilan — porsi frontend\n- TAC-9 ekspor — tiket terpisah")
    c = run(ready)[cid]
    assert c["status"] == "FAIL" and "rujukan hantu): TAC-9" in c["summary"], c


@VALIDATORS
def test_tanpa_ticket_source_tidak_menagih_tac(ready, td, tmpl, run, cid):
    write_files(ready, {f"{td}/TASK.md": tmpl.format(ticket=TICKET, sc="", oos="").replace(f"ticket_source: {TICKET}\n", "")})
    checks = run(ready)
    assert cid not in checks or checks[cid]["status"] == "PASS"


# --- teks kontrak -----------------------------------------------------------------------------

@pytest.mark.parametrize("skill", [
    BE_SKILLS / "tech-lead/SKILL.md", BE_SKILLS / "analyst/SKILL.md", BE_SKILLS / "task/SKILL.md",
    BE_SKILLS / "business-analysis/SKILL.md", FE_SKILLS / "lead/SKILL.md", FE_SKILLS / "task/SKILL.md",
], ids=lambda p: f"{p.parts[-4]}:{p.parts[-2]}")
def test_parameter_ticket_source_dideklarasikan(skill):
    params = skill.read_text(encoding="utf-8").split("## Parameter", 1)[1].split("\n## ", 1)[0]
    assert "- `ticket_source` — string — default `\"\"`" in params


@pytest.mark.regression("A1")
def test_klaim_analyst_bukan_lagi_manual():
    analyst = PLUGINS / "analyst"
    paths = [analyst / ".claude-plugin/plugin.json", analyst / "README.md", analyst / "skills/spec/SKILL.md",
             analyst / "skills/spec/templates/ticket-template.md", analyst / "skills/_common/ticket.py",
             PLUGINS.parent.parent / ".claude-plugin/marketplace.json"]
    for p in paths:
        text = p.read_text(encoding="utf-8")
        assert "masih manual" not in text and "serah-terima manual" not in text and "belum mengenal" not in text, p
    assert "ticket_source" in (analyst / ".claude-plugin/plugin.json").read_text(encoding="utf-8")
