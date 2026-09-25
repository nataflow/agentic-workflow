"""L2.7 — matriks dan hitungan ronde plan bertahan saat laci `.explore/` hilang."""
import json
import shutil

from conftest import TD, be_run, brief, commit, git

SCAFFOLD = "plan/scripts/scaffold_brief.py"
VALIDATE = "plan/scripts/validate_briefs.py"


def _spec(repo, rows):
    path = repo.parent / "spec.json"
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
