"""L2.2 — brief BLOCKED ditutup `plan` lewat pengganti ber-`supersedes`; konsumen mengenal SUPERSEDED."""
import json

from conftest import TD, be_checks, be_run, brief, commit, write_files

ARCH = "architect/scripts/check_preconditions.py"
REPORT = "report/scripts/check_preconditions.py"
SCAFFOLD = "plan/scripts/scaffold_brief.py"
VALIDATE = "plan/scripts/validate_briefs.py"


def _row(nn, unit, fulfills, **extra):
    return {"nn": nn, "unit": unit, "title": unit, "risk": "MINOR", "fulfills": fulfills, **extra}


def _blocked_taskdir(repo):
    """Keadaan [A] reproduksi: 01 DONE, 02 BLOCKED, 03 READY, matriks laci 3 baris."""
    brief(repo, "01", "lock", "DONE")
    brief(repo, "02", "endpoint", "BLOCKED")
    brief(repo, "03", "recap", "READY")
    write_files(repo, {f"{TD}/.explore/brief-matrix.json": json.dumps({"briefs": [
        _row("01", "lock", ["SC-1"]), _row("02", "endpoint", ["SC-2"]), _row("03", "recap", ["SC-2"])]})})
    commit(repo, "wip(order): brief-02-endpoint [BLOCKED]")


def _spec(repo, *rows):
    path = repo.parent / "spec.json"
    path.write_text(json.dumps({"briefs": list(rows)}), encoding="utf-8")
    return str(path)


def _append(repo, *rows):
    return be_run(repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--append", "--spec", _spec(repo, *rows))


def _fm(repo, name):
    return (repo / TD / name).read_text(encoding="utf-8").split("---")[1]


# -- architect ------------------------------------------------------------------------------


def test_blocked_before_ready_fails(chain_repo):
    _blocked_taskdir(chain_repo)
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "FAIL"
    assert c3["summary"] == "Brief BLOCKED menahan rantai: brief-02-endpoint.md"


def test_superseded_is_skipped_and_ready_is_start(chain_repo):
    brief(chain_repo, "01", "lock", "DONE")
    brief(chain_repo, "02", "endpoint", "SUPERSEDED", superseded_by="brief-04")
    brief(chain_repo, "03", "recap", "DONE")
    brief(chain_repo, "04", "endpoint-fix", "READY", supersedes="brief-02")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "PASS" and "brief-04" in c3["summary"]
    assert c3["entry"] == "FASE_3:04"


def test_unlinked_superseded_fails_architect(chain_repo):
    brief(chain_repo, "01", "lock", "SUPERSEDED")
    brief(chain_repo, "02", "lock-fix", "READY")
    commit(chain_repo, "x")
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["status"] == "FAIL"


# -- report ---------------------------------------------------------------------------------


def test_done_plus_superseded_passes(chain_repo):
    brief(chain_repo, "01", "lock", "DONE")
    brief(chain_repo, "02", "endpoint", "SUPERSEDED", superseded_by="brief-04")
    brief(chain_repo, "03", "recap", "SUPERSEDED", superseded_by="brief-05")
    brief(chain_repo, "04", "endpoint-fix", "DONE", supersedes="brief-02")
    brief(chain_repo, "05", "recap", "DONE", supersedes="brief-03")
    commit(chain_repo, "x")
    c4 = be_checks(chain_repo, REPORT, "--taskdir", TD)[4]
    assert c4["status"] == "PASS" and c4["summary"] == "3 DONE · 2 SUPERSEDED"

    brief(chain_repo, "05", "recap", "DONE")          # tautan balik hilang
    commit(chain_repo, "y")
    assert be_checks(chain_repo, REPORT, "--taskdir", TD)[4]["status"] == "FAIL"


# -- scaffold -------------------------------------------------------------------------------


def test_append_requires_supersede_for_blocked(chain_repo):
    _blocked_taskdir(chain_repo)
    out = _append(chain_repo, _row("04", "endpoint-fix", ["SC-2"]))
    assert out.returncode == 1
    assert "brief-02 BLOCKED belum digantikan" in out.stdout


def test_append_requires_reissue_of_downstream_ready(chain_repo):
    _blocked_taskdir(chain_repo)
    out = _append(chain_repo, _row("04", "endpoint-fix", ["SC-2"], supersedes=["02"]))
    assert out.returncode == 1
    assert "brief READY hilir brief-03 akan berjalan sebelum pengganti" in out.stdout
    out = _append(chain_repo, _row("04", "endpoint-fix", ["SC-2"], supersedes=["02"]),
                  _row("05", "recap", ["SC-2"], supersedes=["03"]))
    assert out.returncode == 0, out.stdout


def test_nn_writes_transition_and_links(chain_repo):
    _blocked_taskdir(chain_repo)
    assert _append(chain_repo, _row("04", "endpoint-fix", ["SC-2"], supersedes=["02"]),
                   _row("05", "recap", ["SC-2"], supersedes=["03"])).returncode == 0
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--nn", "04")
    assert out.returncode == 0, out.stdout + out.stderr
    assert "brief-02-endpoint.md" in out.stdout            # catatan staging agregat
    assert "supersedes: brief-02" in _fm(chain_repo, "brief-04-endpoint-fix.md")
    fm02 = _fm(chain_repo, "brief-02-endpoint.md")
    assert "status: SUPERSEDED" in fm02 and "superseded_by: brief-04" in fm02


def test_nn_refuses_superseding_done(chain_repo):
    _blocked_taskdir(chain_repo)
    matrix = chain_repo / TD / ".explore/brief-matrix.json"
    data = json.loads(matrix.read_text())
    data["briefs"].append(_row("04", "lock-again", ["SC-1"], supersedes=["01"]))
    matrix.write_text(json.dumps(data))
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--nn", "04")
    assert out.returncode != 0
    assert "transisi ke SUPERSEDED ditolak" in out.stdout + out.stderr
    assert not (chain_repo / TD / "brief-04-lock-again.md").exists()


# -- validate_briefs ------------------------------------------------------------------------


def _obj(fulfills, consumes=""):
    iface = f"## Interfaces\n- Consumes: {consumes}\n" if consumes else ""
    return f"# Brief\n## Objective\nCovers: — (PRD absen)\nFulfills: {fulfills}\n{iface}"


def _validate(repo):
    out = be_run(repo, VALIDATE, "--taskdir", TD, "--json")
    return {c["id"]: c for c in json.loads(out.stdout)["checks"]}


def test_superseded_not_counted_for_coverage(chain_repo):
    brief(chain_repo, "01", "lock", "DONE", body=_obj("SC-1"))
    brief(chain_repo, "02", "endpoint", "SUPERSEDED", body=_obj("SC-2"), superseded_by="brief-03")
    brief(chain_repo, "03", "endpoint-fix", "DONE", body=_obj("— (perbaikan brief-02)"), supersedes="brief-02")
    g = _validate(chain_repo)["G"]
    assert g["status"] == "FAIL"
    assert any("SC-2" in d for d in g["details"])


def test_consumes_from_superseded_fails(chain_repo):
    brief(chain_repo, "01", "lock", "SUPERSEDED", body=_obj("SC-1"), superseded_by="brief-02")
    brief(chain_repo, "02", "lock-fix", "DONE", body=_obj("SC-1"), supersedes="brief-01")
    brief(chain_repo, "03", "endpoint", "READY", body=_obj("SC-2", "`Lock()` dari brief-01"))
    c = _validate(chain_repo)["C"]
    assert c["status"] == "FAIL"
    assert any("SUPERSEDED — rujuk penggantinya" in d for d in c["details"])


def test_check_s_accepts_superseded_as_locked(chain_repo):
    brief(chain_repo, "01", "lock", "SUPERSEDED", body=_obj("SC-1"), superseded_by="brief-02")
    brief(chain_repo, "02", "lock-fix", "READY", body=_obj("SC-1, SC-2"), supersedes="brief-01")
    checks = _validate(chain_repo)
    assert not any("brief terbit `READY`" in d for d in checks["S"]["details"])
    assert checks["C"]["status"] == "PASS", checks["C"]["details"]
