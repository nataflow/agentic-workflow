"""32 S1–S2 — `symbol_map.py --brief`: deklarasi baru yang disebut `## Steps` sah; keluaran mode anchor ringkas."""
import json

import pytest

from conftest import BE_SKILLS, commit, run_script, write_files

SCRIPT = BE_SKILLS / "architect/scripts/symbol_map.py"
PATH = "src/OrderService.java"
JAVA = """package com.acme.order;

public class OrderService {
    public void submit(Order o) {
        validate(o);
    }

    public void cancel(Order o) {
        o.setStatus("CANCELLED");
    }
}
"""
NEW_METHOD = JAVA[:-2] + "\n    public void refund(Order o) {\n        repo.refund(o);\n    }\n}\n"


def _brief(repo, anchor="`submit`", steps="1. Tambah method `refund` sesudah `cancel`."):
    path = repo / "brief-01-refund.md"
    path.write_text(
        "---\nstatus: READY\n---\n\n## File scope\n\n"
        "| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n"
        f"| modify | `{PATH}` | {anchor} | tambah refund |\n\n"
        f"## Steps\n\n{steps}\n\n## Interfaces\n\n- Produces: —\n",
        encoding="utf-8")
    return path


def _run(repo, *extra):
    sha = commit(repo, "edit")
    proc = run_script(SCRIPT, "--root", str(repo), "--sha", sha, "--path", PATH, *extra)
    return proc.returncode, json.loads(proc.stdout)


@pytest.fixture
def repo(make_repo):
    r = make_repo({PATH: JAVA})
    commit(r, "base")
    return r


@pytest.mark.regression("32 S1")
def test_new_method_named_in_steps_is_new_declared(repo):
    brief = _brief(repo)
    write_files(repo, {PATH: NEW_METHOD})
    code, out = _run(repo, "--brief", str(brief))
    assert code == 0 and out["status"] == "PASS"
    assert out["new_declared"] == ["refund"] and out["outside_anchor"] == []


@pytest.mark.regression("32 S1")
def test_new_method_not_in_steps_still_fails(repo):
    brief = _brief(repo, steps="1. Ubah `submit`.")
    write_files(repo, {PATH: NEW_METHOD})
    code, out = _run(repo, "--brief", str(brief))
    assert code == 1 and [o["symbol"] for o in out["outside_anchor"]] == ["refund"]


@pytest.mark.regression("32 S1")
def test_existing_method_named_in_steps_still_needs_anchor(repo):
    """Suntingan simbol lama di luar Anchor tetap FAIL walau namanya disebut `## Steps`."""
    brief = _brief(repo, steps="1. Ubah `cancel` juga.")
    write_files(repo, {PATH: JAVA.replace('o.setStatus("CANCELLED");', 'o.setStatus("CANCELLED");\n        audit(o);')})
    code, out = _run(repo, "--brief", str(brief))
    assert code == 1 and [o["symbol"] for o in out["outside_anchor"]] == ["cancel"]
    assert out["new_declared"] == []


@pytest.mark.regression("32 S1")
def test_brief_without_row_for_path_degrades(repo):
    brief = _brief(repo)
    brief.write_text(brief.read_text().replace(PATH, "src/Other.java"))
    write_files(repo, {PATH: NEW_METHOD})
    code, out = _run(repo, "--brief", str(brief))
    assert code == 2 and out["status"] == "DEGRADED"


@pytest.mark.regression("32 S2")
def test_anchor_mode_omits_lines_unless_verbose(repo):
    write_files(repo, {PATH: JAVA.replace("validate(o);", "validate(o);\n        audit(o);")})
    sha = commit(repo, "edit")
    base = ["--root", str(repo), "--sha", sha, "--path", PATH, "--anchor", "submit"]
    out = json.loads(run_script(SCRIPT, *base).stdout)
    assert "lines" not in out and out["status"] == "PASS"
    out = json.loads(run_script(SCRIPT, *base, "--verbose").stdout)
    assert out["lines"] and out["lines"][0]["symbol"] == "submit"
    out = json.loads(run_script(SCRIPT, "--root", str(repo), "--sha", sha, "--path", PATH).stdout)
    assert "lines" in out
