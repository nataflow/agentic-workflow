"""Langkah 18 — subagent `code-scout` untuk `analyst:elicit` (X1–X3).

Scout read-only dan dangkal: tanpa `Write`, sehingga analyst tetap tanpa hook. Gerbang `check --gate elicit` menagih
template dispatch-nya, dan `validate_doc.py --kind elicit` menolak rujukan `path:baris` di catatan tiket non-`TECH`,
karena konteks kode di sana bukan fakta dari peminta.
"""
import json
import shutil
from pathlib import Path

import pytest

from conftest import PLUGINS, load_module, run_script

ANALYST = PLUGINS / "analyst"
COMMON = ANALYST / "skills" / "_common"
TICKET = COMMON / "ticket.py"
VALIDATE = COMMON / "validate_doc.py"
AGENT = ANALYST / "agents" / "code-scout.md"
DISPATCHER = ANALYST / "skills" / "elicit" / "dispatcher" / "explorer.md"  # 27 E2: scout.md elicit diganti
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TDIR = "analyst/tickets/2609231400-cicilan"
TECH_TDIR = "analyst/tickets/2610011000-relasi-project-workspace"
lib = load_module(COMMON / "analyst_lib.py", "analyst_lib_18x")


def elicit_checks(root, tdir=TDIR):
    r = run_script(VALIDATE, "--kind", "elicit", "--ticketdir", tdir, "--json", cwd=root)
    return r.returncode, {c["id"]: c for c in json.loads(r.stdout)["checks"]}


def feature(make_repo, old="", new=""):
    text = (FIXTURES / "ticket_valid.md").read_text(encoding="utf-8")
    if old:
        assert old in text, old
        text = text.replace(old, new, 1)
    return make_repo({f"{TDIR}/TICKET.md": text}, git_init=False)


# --- X1: agent ----------------------------------------------------------------------------------

@pytest.mark.regression("18 X1")
def test_x1_scout_read_only_dangkal_dan_berplafon():
    fm, body = lib.split_frontmatter(AGENT.read_text(encoding="utf-8"))
    assert fm["name"] == "code-scout"
    assert [t.strip() for t in fm["tools"].split(",")] == ["Read", "Grep", "Glob"]
    assert fm["model"] == "sonnet" and str(fm["maxTurns"]).isdigit()  # 27 E5: haiku → sonnet
    assert "## Code Scout" in body and "Pemanggilan: <n> dari 8" in body
    for section in ("### Ditemukan", "### Tidak ditemukan", "### Belum disisir"):
        assert section in body


@pytest.mark.regression("18 X2")
@pytest.mark.regression("27 E2")
def test_x2_dispatcher_merujuk_agent_dan_slotnya():
    text = DISPATCHER.read_text(encoding="utf-8")
    assert "agents/code-explorer.md" in text
    assert not (ANALYST / "skills" / "elicit" / "dispatcher" / "scout.md").exists()
    for slot in ("{mode}", "{root}", "{batas}", "{pertanyaan}"):
        assert slot in text


# --- X2: gerbang elicit -------------------------------------------------------------------------

@pytest.mark.regression("18 X2")
@pytest.mark.regression("27 E2")
def test_x2_check_elicit_menagih_dispatcher_explorer(tmp_path, make_repo):
    plugin = tmp_path / "plugin"
    shutil.copytree(ANALYST, plugin, ignore=shutil.ignore_patterns("__pycache__"))
    script = plugin / "skills" / "_common" / "ticket.py"
    root = make_repo(name="ws", git_init=False)
    r = run_script(script, "new", "--slug", "cicilan", "--type", "FEATURE", "--requester", "Rina",
                   "--request", "Tolong bikin fitur cicilan.", cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr
    tdir = next((root / "analyst" / "tickets").iterdir()).relative_to(root).as_posix()

    ok = run_script(script, "check", "--gate", "elicit", "--ticketdir", tdir, "--json", cwd=root)
    assert ok.returncode == 0, ok.stdout
    (plugin / "skills" / "elicit" / "dispatcher" / "explorer.md").unlink()
    bad = run_script(script, "check", "--gate", "elicit", "--ticketdir", tdir, "--json", cwd=root)
    by_id = {c["id"]: c for c in json.loads(bad.stdout)["checks"]}
    assert bad.returncode == 1 and by_id[2]["status"] == "FAIL"
    assert "elicit/dispatcher/explorer.md" in by_id[2]["summary"]


# --- X3: validator elicit -----------------------------------------------------------------------

@pytest.mark.regression("18 X3")
def test_x3_fixture_non_tech_tetap_lolos(make_repo):
    code, by_id = elicit_checks(feature(make_repo))
    assert code == 0 and by_id[11]["status"] == "PASS"


@pytest.mark.regression("18 X3")
@pytest.mark.parametrize("old,new", [
    ("Invoice hanya berstatus Belum Bayar atau Lunas.",
     "Invoice hanya berstatus Belum Bayar atau Lunas (`internal/invoice/model.go:42`)."),
    ("| Di atas 50 juta | Rina |", "| Di atas 50 juta, lihat `src/invoice/rules.ts:12-20` | Rina |"),
])
def test_x3_path_baris_di_catatan_non_tech_gagal(make_repo, old, new):
    code, by_id = elicit_checks(feature(make_repo, old, new))
    assert code == 1 and by_id[11]["status"] == "FAIL"
    assert "path:baris" in by_id[11]["summary"]
    assert {i for i, c in by_id.items() if c["status"] == "FAIL"} == {11}


@pytest.mark.regression("18 X3")
def test_x3_jam_dalam_backtick_bukan_rujukan_berkas(make_repo):
    code, by_id = elicit_checks(feature(make_repo, "Hanya pelanggan korporat.",
                                        "Hanya pelanggan korporat, ditutup tiap `17:00`."))
    assert code == 0 and by_id[11]["status"] == "PASS"


@pytest.mark.regression("18 X3")
def test_x3_permintaan_asli_dikecualikan(make_repo):
    root = make_repo(name="ws", git_init=False)
    r = run_script(TICKET, "new", "--slug", "cicilan", "--type", "FEATURE", "--requester", "Rina",
                   "--request", "Status invoice di `src/invoice/model.go:42` kurang satu: Dicicil.", cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr
    tdir = next((root / "analyst" / "tickets").iterdir()).relative_to(root).as_posix()
    _, by_id = elicit_checks(root, tdir)
    assert by_id[11]["status"] == "PASS" and by_id[3]["status"] == "PASS"


@pytest.mark.regression("18 X3")
def test_x3_tech_tidak_ditagih(make_repo):
    root = make_repo({f"{TECH_TDIR}/TICKET.md": (FIXTURES / "ticket_tech.md").read_text(encoding="utf-8")},
                     git_init=False)
    _, by_id = elicit_checks(root, TECH_TDIR)
    assert 11 not in by_id
