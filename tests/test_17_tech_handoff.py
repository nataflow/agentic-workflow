"""17 T9 — serah-terima tiket `TECH` ke backend/frontend lewat `ticket_source` tanpa perubahan skrip hilir.

Tiket dibawa sampai `READY` oleh `ticket.py` sungguhan (`close` → `review` → `approve`), lalu dinilai prasyarat
`task` dan validator `TASK.md` kedua plugin persis seperti tiket `FEATURE` di `test_a1_ticket_source.py`.
"""
import json
from pathlib import Path

import pytest

from conftest import (BE_SKILLS, PLUGINS, be_checks, be_profile, commit, fe_profile, fe_run, run_script, ticket_review,
                      write_files)

TICKET_PY = PLUGINS / "analyst/skills/_common/ticket.py"
FIXTURE = Path(__file__).resolve().parent / "analyst" / "fixtures" / "ticket_tech.md"
TDIR = "analyst/tickets/2610011000-relasi-project-workspace"
TICKET = f"{TDIR}/TICKET.md"
BE_TD = "backenddev/docs/2610021000-project-workspace-relation"
FE_TD = "frontenddev/docs/2610021000-project-workspace-relation"
CODE = {
    "internal/project/model.go": "package project\n" * 30,
    "internal/project/repository.go": "package project\n" * 60,
    "src/features/project/ProjectList.tsx": "export {}\n" * 20,
}


def tk(root, *args):
    proc = run_script(TICKET_PY, *args, cwd=root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc


@pytest.fixture
def ready(make_repo):
    root = make_repo({TICKET: FIXTURE.read_text(encoding="utf-8"), f"{BE_TD}/.keep": "", f"{FE_TD}/.keep": "",
                      **CODE})
    be_profile(root, "go")
    fe_profile(root, "react-vite")
    commit(root, "init")
    tk(root, "close", "--ticketdir", TDIR)
    assert ticket_review(root, TDIR, "PASS").returncode == 0
    tk(root, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    return root


@pytest.mark.regression("17 T9")
def test_t9_tiket_tech_ready_lolos_prasyarat_task_kedua_plugin(ready):
    be = be_checks(ready, "task/scripts/check_preconditions.py", "--root", str(ready), "--taskdir", BE_TD,
                   "--lane", "DIRECT_BRIEF", "--chain", "BRIEF", "--ticket-source", TICKET)[7]
    assert be["status"] == "PASS", be
    r = fe_run(ready, "task/scripts/check_preconditions.py", "--root", str(ready), "--taskdir", FE_TD,
               "--lane", "REFACTOR_ARCH", "--sections", "architecture", "--ticket-source", TICKET, "--json")
    fe = {c["id"]: c for c in json.loads(r.stdout)["checks"]}[8]
    assert fe["status"] == "PASS", fe


BE_TASK = """---
status: ACTIVE
chain: BRIEF
lane: DIRECT_BRIEF
risk: MAJOR
created: 2026-10-02
ticket_source: {ticket}
---

# Project — relasi many-to-many ke workspace

## Chain

- [ ] BRIEF — backend:plan             → brief-*.md

## Description

Project hanya dapat berada di satu workspace karena kolom `workspace_id` menempel di model (`internal/project/model.go:12`).

## Success Criteria

- [ ] **SC-1**: project tertaut ke dua workspace muncul di daftar keduanya (TAC-1) — verifikasi: `TestProjectRepo_ListByWorkspace` hijau
- [ ] **SC-2**: respons daftar project tidak berubah bentuk (TAC-2, TC-1) — verifikasi: snapshot test handler hijau
{sc}
## Out of Scope

- Izin per workspace atas project — tiket terpisah
{oos}"""


def be_task_checks(root):
    proc = run_script(BE_SKILLS / "_common/validate_doc.py", "--kind", "task", "--taskdir", BE_TD,
                      "--root", str(root), "--json")
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


@pytest.mark.regression("17 T9")
def test_t9_tac_tiket_tech_ditagih_validator_task(ready):
    write_files(ready, {f"{BE_TD}/TASK.md": BE_TASK.format(ticket=TICKET, sc="", oos="")})
    c = be_task_checks(ready)["T10"]
    assert c["status"] == "FAIL" and "TAC-3" in c["summary"], c
    sc3 = ("- [ ] **SC-3**: migrasi naik lalu turun mengembalikan `workspace_id` tiap project (TAC-3, TC-2) — "
           "verifikasi: `make migrate-up` lalu `migrate down 1` atas data seed\n")
    write_files(ready, {f"{BE_TD}/TASK.md": BE_TASK.format(ticket=TICKET, sc=sc3, oos="")})
    c = be_task_checks(ready)["T10"]
    assert c["status"] == "PASS", c
