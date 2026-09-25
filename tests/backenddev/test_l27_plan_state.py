"""L2.7 — matriks dan hitungan ronde plan bertahan saat laci `.explore/` hilang."""
import json
import shutil

from conftest import TD, be_run, brief, commit, git

def _spec_path(repo):
    """Spec batch di laci `.explore/` taskdir — satu-satunya lokasi yang diterima scaffold (B11)."""
    path = repo / TD / ".explore" / "brief-spec.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


SCAFFOLD = "plan/scripts/scaffold_brief.py"
VALIDATE = "plan/scripts/validate_briefs.py"


def _spec(repo, rows):
    path = _spec_path(repo)
    path.write_text(json.dumps({"briefs": rows}), encoding="utf-8")
    return str(path)


def _row(nn, unit, fulfills):
    return {"nn": nn, "unit": unit, "title": unit, "risk": "MINOR", "fulfills": fulfills}


def test_append_reconstructs_matrix_without_explore(chain_repo):
    brief(chain_repo, "01", "lock", "DONE", body="# B\n## Objective\nCovers: — (PRD absen)\nFulfills: SC-1\n")
    commit(chain_repo, "fix(order): implement lock")
    assert not (chain_repo / TD / ".explore").exists()
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--append",
                 "--spec", _spec(chain_repo, [_row("02", "recap", ["SC-2"])]))
    assert out.returncode == 0, out.stdout
    assert "direkonstruksi dari brief di disk" in out.stdout


def test_reconstruct_keeps_assertion_tokens(chain_repo):
    brief(chain_repo, "01", "lock", "DONE", body="# B\n## Objective\nCovers: — (PRD absen)\nFulfills: SC-1, SC-2\n")
    brief(chain_repo, "02", "audit-log", "DONE", body="# B\n## Objective\nCovers: — (PRD absen)\nFulfills: — (berkas yatim)\n")
    commit(chain_repo, "x")
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--append",
                 "--spec", _spec(chain_repo, [_row("03", "recap", ["SC-2"])]))
    assert out.returncode == 0, out.stdout


def _round(repo, verdict):
    assert be_run(repo, VALIDATE, "--taskdir", TD, "--open-round").returncode == 0
    return be_run(repo, VALIDATE, "--taskdir", TD, "--record-round", verdict)


def test_review_state_survives_explore_loss(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    _round(chain_repo, "Issues Found")
    out = _round(chain_repo, "Approved")
    trailer = next(l.split(": ", 1)[1] for l in out.stdout.splitlines() if "trailer commit agregat" in l)
    assert trailer.startswith("Brief-Review-Rounds: ") and "rounds=2 total=2" in trailer
    git(chain_repo, "add", f"{TD}/brief-01-lock.md")
    git(chain_repo, "commit", "-qm", "docs(plan): add 1 briefs for order-fix", "-m", trailer)
    shutil.rmtree(chain_repo / TD / ".explore")
    state = be_run(chain_repo, VALIDATE, "--taskdir", TD, "--review-state").stdout
    assert "ronde terpakai 2/2" in state and "taskdir 2/4" in state


def test_trailer_parse_ignores_other_trailers(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    git(chain_repo, "add", "-A")
    git(chain_repo, "commit", "-qm", "docs(plan): add 1 briefs", "-m",
        "Co-Authored-By: x <x@x>\nBrief-Review-Rounds: gen=abc123 rounds=1 total=3\nReviewed-by: y")
    state = be_run(chain_repo, VALIDATE, "--taskdir", TD, "--review-state").stdout
    assert "taskdir 3/4" in state


def test_b11_spec_di_luar_laci_ditolak(chain_repo):
    loose = chain_repo / TD / "spec.json"
    loose.write_text(json.dumps({"briefs": [_row("01", "lock", ["SC-1"])]}), encoding="utf-8")
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", str(loose))
    assert out.returncode == 1 and "spec wajib di" in out.stdout
    rel = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", f"{TD}/spec.json")
    assert rel.returncode == 1 and "spec wajib di" in rel.stdout
    sneaky = f"{TD}/.explore/../spec.json"
    assert "spec wajib di" in be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", sneaky).stdout


def test_b11_spec_di_laci_tidak_mengotori_worktree(chain_repo):
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix",
                 "--spec", _spec(chain_repo, [_row("01", "lock", ["SC-1"]), _row("02", "endpoint", ["SC-2"])]))
    assert out.returncode == 0, out.stdout
    assert git(chain_repo, "status", "--porcelain") == ""
