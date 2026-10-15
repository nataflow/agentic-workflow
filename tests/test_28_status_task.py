"""Langkah 28 — status task nataflow mengikuti workdir.

Task naik ke `in_progress` sejak workdir terbit (T1). Task milik taskdir tetap ditutup oleh taskdir-nya sendiri,
sedangkan task tiket analyst — yang bisa menaungi taskdir backend dan frontend sekaligus (15 E8) — baru `done` bila
seluruh workdir di bawahnya tuntas: payload membawa `task.siblings`, model menyerahkan balikan `list_workdir task_id`
ke `sync_payload.py --workdirs -`, dan skrip yang memutuskan (T2). Prosedur langkah 7 kedua plugin dikunci teks (T3).
"""
import json

import pytest

from conftest import BE_SKILLS, FE_SKILLS, FE_TD, TD, fe_run, load_module, run_script, write_files

NS = load_module(BE_SKILLS / "_common" / "nataflow_sync.py", "nataflow_sync_28")
BE_SP = BE_SKILLS / "_common" / "sync_payload.py"
FE_SP = FE_SKILLS / "_common" / "sync_payload.py"
BE_REF = BE_SKILLS / "tech-lead" / "references" / "nataflow-sync.md"
FE_REF = FE_SKILLS / "lead" / "references" / "nataflow-sync.md"
TICKET = "analyst/tickets/2609231400-cicilan-pembayaran"
BE_KEY = f"backenddev:tim/api:{TD}"
FE_KEY = f"frontenddev:tim/web:{FE_TD}"
IN_PROGRESS = {"status": "in_progress", "from": ["todo"]}
DONE = {"status": "done", "from": ["todo", "in_progress"]}


def wd(key, status, n=1):
    """Satu `workdirView` balikan `list_workdir`."""
    return {"id": f"00000000-0000-0000-0000-00000000000{n}", "key": key, "name": key.rsplit("/", 1)[-1],
            "status": status, "task_id": "99999999-0000-0000-0000-000000000000"}


def sp(script, repo, *args, stdin=""):
    r = run_script(script, *args, "--json", cwd=repo, stdin=stdin)
    assert r.stdout.strip(), r.stderr
    return r.returncode, json.loads(r.stdout)


def bertiket(repo, td):
    path = repo / td / "TASK.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "status: ACTIVE\n", f"status: ACTIVE\nticket_source: {TICKET}/TICKET.md\n", 1), encoding="utf-8")


# ── Pustaka bersama ─────────────────────────────────────────────────────────

@pytest.mark.regression("28 T2")
def test_parse_workdirs_larik_dan_bungkus():
    rows = [wd("a", "done", 1), {"id": "tanpa-key", "status": "BLOCKED"}, wd("c", "aneh", 3), wd("d", None, 4)]
    want = {"a": "done", "tanpa-key": "blocked", "c": "active", "d": "active"}
    for text in (json.dumps(rows), json.dumps({"workdirs": rows}), json.dumps({"data": rows, "total": 4})):
        assert NS.parse_workdirs(text) == (want, []), "status tak dikenal/kosong dibaca active"


@pytest.mark.regression("28 T2")
@pytest.mark.parametrize("text,needle", [
    ("{", "bukan JSON sah"),
    ("{}", "harus larik workdir"),
    ("[1]", "bukan objek workdir"),
    ('[{"status":"done"}]', "tanpa `key` maupun `id`"),
])
def test_parse_workdirs_rusak(text, needle):
    workdirs, problems = NS.parse_workdirs(text)
    assert workdirs is None and needle in problems[0]


def test_read_workdirs_kosong_dan_berkas(tmp_path):
    assert "kosong" in NS.read_workdirs("-", " \n")[1][0]
    assert "tidak terbaca" in NS.read_workdirs(str(tmp_path / "tidak-ada.json"), "")[1][0]
    (tmp_path / "w.json").write_text(json.dumps([wd("a", "done")]), encoding="utf-8")
    assert NS.read_workdirs(str(tmp_path / "w.json"), "") == ({"a": "done"}, [])
    assert NS.read_remote("-", "")[1] == [
        "--remote kosong — serahkan teks balikan list_document (larik kosong `[]` bila tidak ada)"]


@pytest.mark.regression("28 T2")
@pytest.mark.parametrize("own,siblings,want", [
    ("done", {}, DONE),
    ("done", {"fe": "done"}, DONE),
    ("done", {"fe": "abandoned"}, DONE),
    ("abandoned", {"be": "done"}, DONE),
    ("done", {"fe": "active"}, IN_PROGRESS),
    ("done", {"fe": "blocked"}, IN_PROGRESS),
    ("done", {"fe": "done", "lain": "active"}, IN_PROGRESS),
    ("abandoned", {"be": "abandoned"}, IN_PROGRESS),
    ("abandoned", {}, IN_PROGRESS),
])
def test_task_tiket_done_hanya_bila_seluruh_workdir_tuntas(own, siblings, want):
    workdirs = dict(siblings, own="active")          # status remote workdir ini diganti status disk
    assert NS.sibling_task_status(workdirs, "own", own, IN_PROGRESS) == (want, [])


def test_workdir_sendiri_wajib_ada_di_balikan():
    status, problems = NS.sibling_task_status({"lain": "done"}, "own", "done", IN_PROGRESS)
    assert status is None and "workdir `own` tidak ada di balikan list_workdir" in problems[0]


# ── backend ─────────────────────────────────────────────────────────────────

@pytest.fixture
def be(chain_repo):
    write_files(chain_repo, {".claude/nataflow.json": json.dumps({"repo": "tim/api"})})
    return chain_repo


@pytest.mark.regression("28 T1")
def test_be_task_tiket_in_progress_sejak_akar(be):
    bertiket(be, TD)
    task = sp(BE_SP, be, "--taskdir", TD)[1]["task"]
    assert task["status"] == IN_PROGRESS and "siblings" not in task, "workdir terbit, belum tuntas"


@pytest.mark.regression("28 T2")
def test_be_task_tiket_ditutup_dari_seluruh_workdir(be):
    bertiket(be, TD)
    write_files(be, {f"{TD}/REPORT.md": "# laporan\n"})
    out = sp(BE_SP, be, "--taskdir", TD)[1]
    assert out["workdir"]["status"] == "done"
    assert out["task"]["status"] == IN_PROGRESS and out["task"]["siblings"] is True

    def phase(rows):
        return sp(BE_SP, be, "--taskdir", TD, "--workdirs", "-", stdin=json.dumps(rows))

    code, out = phase([wd(BE_KEY, "done", 1), wd(FE_KEY, "active", 2)])
    assert code == 0 and out["task_status"] == IN_PROGRESS, "taskdir frontend masih jalan"
    assert (out["workdirs_total"], out["workdirs_open"]) == (2, 1)
    code, out = phase({"workdirs": [wd(BE_KEY, "active", 1), wd(FE_KEY, "done", 2)]})
    assert code == 0 and out["task_status"] == DONE, "status workdir ini dari disk, bukan balikan lama"
    assert out["workdirs_open"] == 0 and "documents" not in out
    code, out = phase([wd(FE_KEY, "done", 2)])
    assert code == 1 and "tidak ada di balikan list_workdir" in out["problems"][0]


def test_be_tanpa_tiket_workdirs_mengembalikan_status_fase_satu(be):
    write_files(be, {f"{TD}/REPORT.md": "# laporan\n"})
    task = sp(BE_SP, be, "--taskdir", TD)[1]["task"]
    assert task["status"] == DONE and "siblings" not in task, "task milik taskdir ditutup taskdir-nya sendiri"
    for rows in ([], [wd("lain", "active")]):
        code, out = sp(BE_SP, be, "--taskdir", TD, "--workdirs", "-", stdin=json.dumps(rows))
        assert code == 0 and out["task_status"] == DONE, "tanpa task.siblings, balikan tidak memengaruhi status"


def test_be_workdirs_hanya_untuk_taskdir(be):
    code, out = sp(BE_SP, be, "--repo-docs", "audit", "--workdirs", "-", stdin="[]")
    assert code == 1 and out["problems"] == ["--workdirs hanya untuk --taskdir"]


# ── frontend ────────────────────────────────────────────────────────────────

@pytest.fixture
def fe(fe_chain_repo):
    write_files(fe_chain_repo, {".claude/nataflow.json": json.dumps({"repo": "tim/web"})})
    return fe_chain_repo


@pytest.mark.regression("28 T2")
def test_fe_task_tiket_ditutup_dari_seluruh_workdir(fe):
    bertiket(fe, FE_TD)
    assert "siblings" not in sp(FE_SP, fe, "--taskdir", FE_TD)[1]["task"]
    r = fe_run(fe, "_common/chain.py", "abandon", "--reason", "user berhenti", "--taskdir", FE_TD)
    assert r.returncode == 0, r.out
    out = sp(FE_SP, fe, "--taskdir", FE_TD)[1]
    assert out["workdir"]["status"] == "abandoned"
    assert out["task"]["status"] == IN_PROGRESS and out["task"]["siblings"] is True, "task tiket tidak di-cancel"

    def phase(rows):
        code, out = sp(FE_SP, fe, "--taskdir", FE_TD, "--workdirs", "-", stdin=json.dumps(rows))
        assert code == 0, out
        return out["task_status"]

    assert phase([wd(FE_KEY, "abandoned", 1), wd(BE_KEY, "done", 2)]) == DONE, "tidak ada lagi kerja di bawah tiket"
    assert phase([wd(FE_KEY, "abandoned", 1), wd(BE_KEY, "blocked", 2)]) == IN_PROGRESS
    assert phase([wd(FE_KEY, "abandoned", 1)]) == IN_PROGRESS, "tanpa satu pun workdir done → tidak ditutup"


def test_fe_workdirs_hanya_untuk_taskdir(fe):
    code, out = sp(FE_SP, fe, "--repo-docs", "review", "--workdirs", "-", stdin="[]")
    assert code == 1 and out["problems"] == ["--workdirs hanya untuk --taskdir"]


# ── Prosedur ────────────────────────────────────────────────────────────────

@pytest.mark.regression("28 T3")
@pytest.mark.parametrize("ref", [BE_REF, FE_REF], ids=["backend", "frontend"])
def test_prosedur_langkah_tujuh_memakai_list_workdir(ref):
    text = ref.read_text(encoding="utf-8")
    tool = text[text.index("2. **Tool.**"): text.index("3. **Task.**")]
    assert "`…__list_workdir`" in tool and "Ketujuh tool" in tool
    step = text[text.index("7. **Status task.**"): text.index("8. **Segmen.**")]
    for needle in ("`task.siblings`", "`list_workdir` dengan `task_id` = `id` dan `workspace_id` = `workspace_id` task",
                   "--taskdir <taskdir> --workdirs - --json", "`task_status` keluarannya", "`update_task_status`"):
        assert needle in step, needle
    rules = text[text.index("## Larangan"):]
    assert "teksnya diserahkan ke `--workdirs` apa adanya" in rules
