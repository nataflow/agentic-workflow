"""B13 — `commit_message` brief diturunkan dari `commit_template` profil lewat satu modul (`commit_lib`)."""
import json

import pytest

from conftest import PLUGINS, TD, be_run, commit, git, load_module, write_files

LIB = load_module(PLUGINS / "backend/skills/_common/commit_lib.py", "commit_lib_b13")
SCAFFOLD = "plan/scripts/scaffold_brief.py"
VB = "plan/scripts/validate_briefs.py"
INDEX = ".claude/profile/backenddev/index.json"


def test_b13_render_dan_pattern_sepasang():
    conv = LIB.commit_template({})
    assert conv == LIB.DEFAULT_TEMPLATE
    msg = LIB.render(conv, ctype="fix", scope="order", unit="order-total-null")
    assert msg == "fix(order): implement order-total-null" and LIB.pattern(conv).match(msg)
    assert not LIB.pattern(conv).match("OMS-412: fix x")
    tk = LIB.commit_template({"commit_template": "{ticket}: {subject}"})
    msg = LIB.render(tk, ctype="feat", scope="order", unit="order-total-null", ticket="OMS-412")
    assert msg == "OMS-412: implement order-total-null" and LIB.pattern(tk).match(msg)


@pytest.mark.parametrize("tpl", ["{type}: tanpa subjek", "{type}({scope}): {subject} {asing}", ""])
def test_b13_template_tidak_sah_jatuh_ke_default(tpl):
    assert LIB.commit_template({"commit_template": tpl}) == LIB.DEFAULT_TEMPLATE


def test_b13_default_type():
    assert LIB.default_commit_type("DEFECT_RCA", None) == "fix"
    assert LIB.default_commit_type("PRD_CONVERSION", "backenddev/issues/x.md") == "fix"
    assert LIB.default_commit_type("DIRECT_BRIEF", "") == "feat"
    with pytest.raises(ValueError):
        LIB.render(LIB.DEFAULT_TEMPLATE, ctype="wip", scope="x", unit="y")


def _spec(repo, rows, **top):
    path = repo / TD / ".explore" / "brief-spec.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"briefs": rows, **top}))
    return str(path)


def _row(**kw):
    return {"nn": "01", "unit": "order-total-null", "title": "t", "risk": "MINOR", "fulfills": ["SC-1", "SC-2"], **kw}


def _scaffold(repo, rows, **top):
    out = be_run(repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", _spec(repo, rows, **top))
    assert out.returncode == 0, out.stdout
    out = be_run(repo, SCAFFOLD, "--taskdir", TD, "--nn", "01")
    assert out.returncode == 0, out.stdout + out.stderr
    return (repo / TD / "brief-01-order-total-null.md").read_text()


def _lane(repo, lane):
    task = repo / TD / "TASK.md"
    task.write_text(task.read_text().replace("---\n", f"---\nlane: {lane}\n", 1))
    commit(repo, "lane")


def test_b13_defect_rca_default_fix(chain_repo):
    _lane(chain_repo, "DEFECT_RCA")
    text = _scaffold(chain_repo, [_row()])
    assert 'commit_message: "fix(order): implement order-total-null"' in text and "commit_scope: order" in text


def test_b13_planning_default_feat(chain_repo):
    _lane(chain_repo, "DIRECT_BRIEF")
    assert 'commit_message: "feat(order): implement order-total-null"' in _scaffold(chain_repo, [_row()])


def test_b13_template_tiket_lolos_check_s(chain_repo):
    idx = chain_repo / INDEX
    idx.write_text(json.dumps({**json.loads(idx.read_text()), "commit_template": "{ticket}: {subject}"}))
    commit(chain_repo, "tpl")
    text = _scaffold(chain_repo, [_row(ticket="OMS-412")])
    assert 'commit_message: "OMS-412: implement order-total-null"' in text
    out = be_run(chain_repo, VB, "--taskdir", TD, "--brief", "01", "--json")
    assert "commit_message" not in out.stdout, out.stdout


def test_b13_template_tiket_tanpa_ticket_fail(chain_repo):
    idx = chain_repo / INDEX
    idx.write_text(json.dumps({**json.loads(idx.read_text()), "commit_template": "{ticket}: {subject}"}))
    commit(chain_repo, "tpl")
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", _spec(chain_repo, [_row()]))
    assert out.returncode == 1 and "{ticket}" in out.stdout


def test_b13_commit_type_asing_fail(chain_repo):
    out = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix",
                 "--spec", _spec(chain_repo, [_row(commit_type="wip")]))
    assert out.returncode == 1 and "commit_type" in out.stdout


def test_b13_validator_menolak_pesan_di_luar_template(chain_repo):
    text = _scaffold(chain_repo, [_row()])
    path = chain_repo / TD / "brief-01-order-total-null.md"
    path.write_text(text.replace("implement order-total-null\"", "tambah null guard\""))
    out = be_run(chain_repo, VB, "--taskdir", TD, "--brief", "01", "--json")
    assert "tidak cocok `commit_template`" in out.stdout
