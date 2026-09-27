"""Regresi 09 E9–E11 — `ticket.py`: vonis reviewer bersidik, `--report` rusak, `new`/`cancel`."""
import json
from pathlib import Path

import pytest

from conftest import PLUGINS, git, run_script, ticket_block, ticket_review

TICKET = PLUGINS / "analyst" / "skills" / "_common" / "ticket.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    return root


def tk(root, *args, stdin=""):
    proc = run_script(TICKET, *args, cwd=root, stdin=stdin)
    proc.out = proc.stdout + proc.stderr
    return proc


@pytest.mark.regression("E9")
@pytest.mark.parametrize("verdict", ["PASS", "BLOCKED"])
def test_e9_vonis_tanpa_blok_reviewer_ditolak(repo, verdict):
    r = tk(repo, "review", "--ticketdir", TDIR, "--verdict", verdict)
    assert r.returncode == 1 and "tanpa `--report`" in r.out
    assert "review: -" in (repo / TDIR / "TICKET.md").read_text(encoding="utf-8") or \
        "review:" not in (repo / TDIR / "TICKET.md").read_text(encoding="utf-8")


@pytest.mark.regression("E9")
def test_e9_dispatch_failed_tanpa_blok_tetap_sah(repo):
    assert tk(repo, "review", "--ticketdir", TDIR, "--verdict", "DISPATCH_FAILED").returncode == 0


@pytest.mark.regression("E9")
def test_e9_sidik_berubah_sesudah_dispatch_ditolak(repo):
    block = ticket_block(repo, TDIR, "PASS")            # sidik saat dispatch
    p = repo / TDIR / "TICKET.md"
    p.write_text(p.read_text(encoding="utf-8").replace("minimal Rp 50.000.000", "minimal Rp 10.000.000"),
                 encoding="utf-8")
    r = tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS", "--report", "-", stdin=block)
    assert r.returncode == 1 and "draft berubah sesudah dispatch" in r.out


@pytest.mark.regression("E9")
def test_e9_blok_tanpa_sidik_ditolak(repo):
    block = ticket_block(repo, TDIR, "PASS").replace("- Sidik:", "- Catatan:")
    r = tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS", "--report", "-", stdin=block)
    assert r.returncode == 1 and "`tidak ada`" in r.out


@pytest.mark.regression("E9")
def test_e9_check_spec_memberi_sidik(repo):
    out = json.loads(tk(repo, "check", "--gate", "spec", "--ticketdir", TDIR, "--json").stdout)
    assert "/" in out["sidik"]
    assert ticket_review(repo, TDIR, "PASS").returncode == 0


@pytest.mark.regression("E10")
def test_e10_report_path_hilang_fail_rapi(repo):
    r = tk(repo, "review", "--ticketdir", TDIR, "--verdict", "PASS", "--report", "/tidak/ada.md")
    assert r.returncode == 1 and "tak terbaca" in r.out and "Traceback" not in r.out


@pytest.mark.regression("E11")
def test_e11_new_tanpa_type_diterima(make_repo):
    root = make_repo()
    r = tk(root, "new", "--slug", "tanpa-tipe")
    assert r.returncode == 0 and "type=" not in r.stdout
    r = tk(root, "new", "--slug", "bertipe", "--type", "bug")
    assert r.returncode == 0 and "type=BUG" in r.stdout


@pytest.mark.regression("E11")
def test_e11_cancel_ready_menuntut_force_dan_ter_commit(repo):
    assert ticket_review(repo, TDIR, "PASS").returncode == 0
    assert tk(repo, "approve", "--ticketdir", TDIR, "--answer", "ok").returncode == 0
    r = tk(repo, "cancel", "--ticketdir", TDIR, "--reason", "batal")
    assert r.returncode == 1 and "--force" in r.out
    assert "status: READY" in (repo / TDIR / "TICKET.md").read_text(encoding="utf-8")
    assert tk(repo, "cancel", "--ticketdir", TDIR, "--reason", "batal", "--force").returncode == 0
    assert git(repo, "log", "-1", "--format=%s").strip() == "docs(ticket): batalkan TICKET cicilan"
    assert not git(repo, "status", "--porcelain").strip()
