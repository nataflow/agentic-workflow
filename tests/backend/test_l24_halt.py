"""L2.4 — vonis henti architect ter-commit sebagai `HALT.md`; `plan` mencabutnya lewat baris `repairs`."""
import json

from conftest import TD, be_checks, be_run, brief, commit, land, write_files

def _spec_path(repo):
    """Spec batch di laci `.explore/` taskdir — satu-satunya lokasi yang diterima scaffold (B11)."""
    path = repo / TD / ".explore" / "brief-spec.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


ARCH = "architect/scripts/check_preconditions.py"
SCAFFOLD = "plan/scripts/scaffold_brief.py"
HALT = ("---\nbrief: brief-02-endpoint.md\nverdict: COMPILE\nsha: abc1234\nbaseline: 1111111 · hijau\n---\n"
        "# HALT — brief-02-endpoint\n\n## Galat\nSyntaxError: invalid syntax\n")


def _row(nn, unit, fulfills, **extra):
    return {"nn": nn, "unit": unit, "title": unit, "risk": "MINOR", "fulfills": fulfills, **extra}


def _halted(repo):
    brief(repo, "01", "lock", "DONE")
    brief(repo, "02", "endpoint", "DONE")
    brief(repo, "03", "recap", "READY")
    write_files(repo, {f"{TD}/.explore/brief-matrix.json": json.dumps({"briefs": [
        _row("01", "lock", ["SC-1"]), _row("02", "endpoint", ["SC-2"]), _row("03", "recap", ["SC-2"])]}),
        f"{TD}/HALT.md": HALT})
    commit(repo, "chore(order-fix): tahan rantai di brief-02 (COMPILE)")


def _append(repo, *rows):
    spec = _spec_path(repo)
    spec.write_text(json.dumps({"briefs": list(rows)}), encoding="utf-8")
    return be_run(repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--append", "--spec", str(spec))


FIX = _row("04", "endpoint-compile-fix", ["— (perbaikan brief-02, HALT COMPILE)"], repairs="02")
REISSUE = _row("05", "recap", ["SC-2"], supersedes=["03"])


def test_halt_blocks_architect(chain_repo):
    _halted(chain_repo)
    c7 = be_checks(chain_repo, ARCH, "--taskdir", TD)[7]
    assert c7["status"] == "FAIL"
    assert "brief-02-endpoint.md" in c7["summary"] and "COMPILE" in c7["summary"]


def test_append_requires_repairs_row_when_halted(chain_repo):
    _halted(chain_repo)
    out = _append(chain_repo, _row("04", "endpoint-compile-fix", ["— (perbaikan)"]), REISSUE)
    assert out.returncode == 1
    assert "HALT.md menahan brief-02" in out.stdout


def test_append_requires_reissue_of_ready_after_halt(chain_repo):
    _halted(chain_repo)
    out = _append(chain_repo, FIX)
    assert out.returncode == 1
    assert "brief READY hilir brief-03" in out.stdout
    assert _append(chain_repo, FIX, REISSUE).returncode == 0


def test_scaffold_repairs_removes_halt(chain_repo):
    _halted(chain_repo)
    assert _append(chain_repo, FIX, REISSUE).returncode == 0
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--nn", "04")
    assert out.returncode == 0, out.stdout + out.stderr
    assert not (chain_repo / TD / "HALT.md").exists()
    assert "git rm -q HALT.md" in out.stdout
    fm = (chain_repo / TD / "brief-04-endpoint-compile-fix.md").read_text().split("---")[1]
    assert "repairs: brief-02" in fm


def test_halt_under_taskdir_keeps_review_fresh(chain_repo):
    land(chain_repo, brief(chain_repo, "01", "lock", "READY"))
    write_files(chain_repo, {f"{TD}/REVIEW.md": "---\nhighest: CLEAN\n---\n"})
    commit(chain_repo, "docs(order-fix): add final review report")
    write_files(chain_repo, {f"{TD}/HALT.md": HALT})
    commit(chain_repo, "chore(order-fix): tahan rantai di brief-01 (STRAY)")
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["entry"] == "FASE_5"
