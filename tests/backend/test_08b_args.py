"""B16 — parsing argumen: `--brief` dinormalisasi dua digit, spec berbentuk salah tanpa traceback, `--chain` tanpa nilai."""
import json

import pytest

from conftest import TD, be_run, brief, commit

VB = "plan/scripts/validate_briefs.py"
SCAFFOLD = "plan/scripts/scaffold_brief.py"
TASK = "task/scripts/check_preconditions.py"


@pytest.fixture
def batch(chain_repo):
    for nn in ("01", "02", "10"):
        brief(chain_repo, nn, f"u{nn}", "READY")
    commit(chain_repo, "briefs")
    return chain_repo


def _vb(repo, arg):
    proc = be_run(repo, VB, "--taskdir", TD, "--brief", arg, "--json")
    assert "Traceback" not in proc.stderr, proc.stderr
    return json.loads(proc.stdout)


@pytest.mark.parametrize("arg", ["1", "01", "#1", "brief-01", "brief-01-u01"])
def test_b16_brief_dinormalisasi(batch, arg):
    d = _vb(batch, arg)
    assert d["mode"] == "single" and "brief-01-u01.md" in json.dumps(d) and "brief-10" not in json.dumps(d)


@pytest.mark.parametrize("arg", ["0", "00", "x", "100"])
def test_b16_brief_nol_atau_asing_ditolak(batch, arg):
    d = _vb(batch, arg)
    assert d["status"] == "FAIL" and "1..99" in json.dumps(d)


def test_b16_brief_10_tetap_bisa_dipilih(batch):
    d = _vb(batch, "10")
    assert "brief-10-u10.md" in json.dumps(d) and "brief-01-u01" not in json.dumps(d)


@pytest.mark.parametrize("spec", ['[{"nn": "01"}]', '{"briefs": ["01-order-fix"]}',
                                  '{"briefs": [{"nn": "01", "covers": "AC-1"}]}', '{"briefs": {"nn": "01"}}'])
def test_b16_spec_bentuk_salah_tanpa_traceback(chain_repo, spec):
    path = chain_repo / TD / ".explore" / "brief-spec.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(spec)
    p = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", str(path))
    assert p.returncode == 1 and "Traceback" not in p.stderr and "bentuk spec tidak sah" in p.stdout


@pytest.mark.parametrize("lane", ["DEFECT_RCA", "EXEC_BRIEF"])
def test_b16_task_chain_tanpa_nilai(chain_repo, lane):
    p = be_run(chain_repo, TASK, "--taskdir", TD, "--lane", lane, "--chain", "--json")
    assert p.returncode != 2 and "expected one argument" not in p.stderr
    checks = {c["id"]: c for c in json.loads(p.stdout)["checks"]}
    assert any("non-planning" in c["summary"] for c in checks.values())
