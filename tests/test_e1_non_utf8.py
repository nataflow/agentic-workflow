"""09 E1: berkas non-UTF-8 → vonis terbaca yang menyebut berkasnya, bukan traceback.

`test_smoke.py` keadaan `rusak` menjamin tidak ada traceback di 47 CLI. Test ini menjamin
perilakunya: satu berkas rusak tidak menyembunyikan taskdir/tiket lain dari pemindaian, dan
pesan FAIL menunjuk berkas yang harus dipulihkan.
"""
import json

from conftest import PLUGINS, run_script, write_files

BAD = b"\xff\xfe\x80 rusak\n"
FE_STATE = PLUGINS / "frontenddev/skills/lead/scripts/taskdir_state.py"
TICKET = PLUGINS / "analyst/skills/_common/ticket.py"


def test_taskdir_state_satu_task_rusak_tidak_menyembunyikan_yang_lain(make_repo):
    repo = make_repo()
    (repo / "frontenddev/docs/2609260000-rusak").mkdir(parents=True)
    (repo / "frontenddev/docs/2609260000-rusak/TASK.md").write_bytes(BAD)
    (repo / "frontenddev/docs/2609260001-kosong").mkdir(parents=True)
    proc = run_script(FE_STATE, "--all", "--json", cwd=repo)
    assert "Traceback" not in proc.stderr, proc.stderr
    rows = {r["taskdir"].rsplit("/", 1)[-1]: r for r in json.loads(proc.stdout)}
    assert rows["2609260000-rusak"]["state"] == "RUSAK"
    assert "bukan UTF-8" in rows["2609260000-rusak"]["detail"]
    assert rows["2609260001-kosong"]["state"] == "AKAR"


def test_ticket_state_satu_tiket_rusak_tidak_menghentikan_pemindaian(make_repo):
    repo = make_repo()
    (repo / "analyst/tickets/2609260000-rusak").mkdir(parents=True)
    (repo / "analyst/tickets/2609260000-rusak/TICKET.md").write_bytes(BAD)
    (repo / "analyst/tickets/2609260001-kosong").mkdir(parents=True)
    proc = run_script(TICKET, "state", "--all", "--json", cwd=repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    rows = {r["ticketdir"].rsplit("/", 1)[-1]: r for r in json.loads(proc.stdout)["ticketdirs"]}
    assert rows["2609260000-rusak"]["state"] == "RUSAK" and "bukan UTF-8" in rows["2609260000-rusak"]["route"]
    assert rows["2609260001-kosong"]["state"] == "KOSONG"


def test_ticket_perintah_atas_tiket_rusak_fail_rapi(make_repo):
    repo = make_repo()
    (repo / "analyst/tickets/2609260000-rusak").mkdir(parents=True)
    (repo / "analyst/tickets/2609260000-rusak/TICKET.md").write_bytes(BAD)
    proc = run_script(TICKET, "revise", "--ticketdir", "analyst/tickets/2609260000-rusak", cwd=repo)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 1 and "Traceback" not in out
    assert "TICKET.md bukan UTF-8" in out


def test_validator_menyebut_berkas_rusak(make_repo):
    td = "frontenddev/docs/2609260000-x"
    repo = make_repo({f"{td}/TASK.md": "---\nstatus: ACTIVE\n---\n# x\n"})
    (repo / td / "FLOW.md").write_bytes(BAD)
    proc = run_script(PLUGINS / "frontenddev/skills/_common/validate_doc.py",
                      "--kind", "flow", "--taskdir", td, "--json", cwd=repo)
    assert proc.returncode == 1
    detail = json.dumps(json.loads(proc.stdout), ensure_ascii=False)
    assert "FLOW.md" in detail and "bukan UTF-8" in detail


def test_backenddev_validate_doc_json_tetap_json(make_repo):
    td = "backenddev/docs/2609260000-x"
    repo = make_repo()
    write_files(repo, {f"{td}/.keep": ""})
    (repo / td / "TASK.md").write_bytes(BAD)
    proc = run_script(PLUGINS / "backenddev/skills/_common/validate_doc.py",
                      "--kind", "task", "--taskdir", td, "--json", cwd=repo)
    data = json.loads(proc.stdout)
    assert data["status"] == "ERROR" and "bukan UTF-8" in data["error"]


def test_plan_lock_rencana_rusak(make_repo):
    repo = make_repo()
    (repo / "plan").mkdir()
    (repo / "plan/x.md").write_bytes(BAD)
    proc = run_script(PLUGINS / "quickdev/skills/_common/plan_lock.py", "status", "--plan", "plan/x.md", "--json",
                      cwd=repo)
    assert proc.returncode == 1
    assert "bukan UTF-8" in json.loads(proc.stdout)["error"]
