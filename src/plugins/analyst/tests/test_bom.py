"""L5.9 (analyst) — TICKET.md ber-BOM tetap terbaca frontmatter-nya."""
import importlib.util
import sys

from conftest import PLUGINS, run_script, write_files

COMMON = PLUGINS / "analyst" / "skills" / "_common"
AT = "analyst/tickets/2601011200-promo"
BOM = "﻿"
TICKET = (BOM + "---\nstatus: DRAFT\nelicitation: OPEN\ntype: FEATURE\npriority: -\nslug: promo\n"
          "requester: Rina\ncreated: 2026-01-01\n---\n# Promo\n\n## Catatan Elisitasi\n")

_spec = importlib.util.spec_from_file_location("analyst_lib_l59", COMMON / "analyst_lib.py")
lib = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = lib
_spec.loader.exec_module(lib)


def test_state_ticket_ber_bom(make_repo):
    root = make_repo({f"{AT}/TICKET.md": TICKET})
    r = run_script(COMMON / "ticket.py", "--root", str(root), "state", "--all")
    assert "ELISITASI" in r.stdout and "RUSAK" not in r.stdout, r.stdout + r.stderr


def test_elicit_bom_frontmatter_terbaca(make_repo):
    root = make_repo({f"{AT}/TICKET.md": TICKET})
    r = run_script(COMMON / "validate_doc.py", "--root", str(root), "--kind", "elicit", "--ticketdir", AT)
    line = next(l for l in r.stdout.splitlines() if l.startswith("[1]"))
    assert ": PASS" in line, r.stdout


def test_split_frontmatter_bom():
    fm, body = lib.split_frontmatter(TICKET)
    assert fm["status"] == "DRAFT" and body.startswith("# Promo")


def test_set_frontmatter_field_mempertahankan_bom():
    out = lib.set_frontmatter_field(TICKET, "status", "READY")
    assert out.startswith(BOM + "---\nstatus: READY\n")
