"""Tiket di repo bersinkron nataflow: ticketdir diabaikan git, tetap di disk, dan tidak pernah di-commit.

`ticket.py new` menulis `analyst/tickets/.gitignore` (`*`) bila `.claude/nataflow.json` ada. `git_commit` tidak
men-stage path yang diabaikan, jadi `close`/`approve`/`ref`/`cancel` tetap exit 0 tanpa commit, sementara serah
terima (`approved_seal`) dan working tree yang ditagih gerbang engineer tetap sah.
"""
import json
from pathlib import Path

from conftest import PLUGINS, git, load_module, run_script, ticket_review, write_files

TICKET = PLUGINS / "analyst" / "skills" / "_common" / "ticket.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
IGNORE = "analyst/tickets/.gitignore"
WS = "a3e1d6c4-1f2b-4c3d-9e8f-7a6b5c4d3e2f"


def tk(root, *args):
    return run_script(TICKET, *args, cwd=root)


def new(root, slug="lain"):
    return tk(root, "new", "--slug", slug, "--type", "FEATURE", "--requester", "Rina",
              "--request", "Tolong bikin fitur cicilan.")


def status(root):
    return git(root, "status", "--porcelain", "-uall")


def commits(root):
    return int(git(root, "rev-list", "--count", "HEAD"))


def committed(root, *files):
    git(root, "add", "--", *files)
    git(root, "commit", "-qm", "fixture")


def synced(make_repo):
    """Repo git bersinkron nataflow, config ter-commit, belum ada ticketdir."""
    root = make_repo({".claude/nataflow.json": json.dumps({"workspaces": {"utama": WS}})})
    committed(root, ".claude/nataflow.json")
    return root


def test_new_menulis_gitignore_dan_tree_tetap_bersih(make_repo):
    root = synced(make_repo)
    r = new(root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "git=diabaikan" in r.stdout and f"{IGNORE} ditulis" in r.stdout
    assert (root / IGNORE).read_text(encoding="utf-8").splitlines()[-1] == "*"
    assert [p.name for p in (root / "analyst/tickets").glob("*/TICKET.md")] == ["TICKET.md"]
    assert status(root) == ""


def test_siklus_tanpa_commit_dan_tiket_tetap_di_disk(make_repo):
    root = synced(make_repo)
    assert new(root).returncode == 0
    write_files(root, {f"{TDIR}/TICKET.md":
                       FIXTURE.read_text(encoding="utf-8").replace("elicitation: CLOSED", "elicitation: OPEN")})
    before = commits(root)
    r = tk(root, "close", "--ticketdir", TDIR)
    assert r.returncode == 0 and "commit diabaikan git" in r.stdout, r.stdout + r.stderr
    r = tk(root, "check", "--gate", "spec", "--ticketdir", TDIR)
    assert r.returncode == 0 and "git=diabaikan" in r.stdout, r.stdout
    assert ticket_review(root, TDIR, "PASS").returncode == 0
    r = tk(root, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    assert r.returncode == 0 and "commit diabaikan git" in r.stdout, r.stdout + r.stderr
    r = tk(root, "ref", "--ticketdir", TDIR, "--ref", "FIN-1")
    assert r.returncode == 0 and "commit diabaikan git" in r.stdout, r.stdout + r.stderr
    assert commits(root) == before and status(root) == ""
    assert "status: READY" in (root / TDIR / "TICKET.md").read_text(encoding="utf-8")
    assert (root / TDIR / "review.md").is_file()
    payload = json.loads(tk(root, "sync-payload", "--ticketdir", TDIR, "--json").stdout)
    assert payload["status"] == "PASS" and len(payload["documents"]) == 1
    r = tk(root, "cancel", "--ticketdir", TDIR, "--reason", "batal", "--force")
    assert r.returncode == 0 and "commit diabaikan git" in r.stdout, r.stdout + r.stderr
    assert commits(root) == before and status(root) == ""


def test_serah_terima_dan_gerbang_engineer_tanpa_commit(make_repo):
    root = synced(make_repo)
    assert new(root).returncode == 0
    write_files(root, {f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    assert ticket_review(root, TDIR, "PASS").returncode == 0
    assert tk(root, "approve", "--ticketdir", TDIR, "--answer", "Setujui").returncode == 0
    be = load_module(PLUGINS / "backend" / "skills" / "_common" / "precondition_lib.py", "pl_be_gitignore")
    fe = load_module(PLUGINS / "frontend" / "skills" / "_common" / "precondition_lib.py", "pl_fe_gitignore")
    for lib in (be, fe):
        verdict = lib.ticket_source_verdict(root, f"{TDIR}/TICKET.md")
        assert verdict[0] == "PASS" and "bersegel" in verdict[1], verdict
    assert be.dirty_paths(root) == [] and fe.dirty_lines(root) == []


def test_tanpa_config_sinkron_tidak_menulis_gitignore(make_repo):
    root = make_repo()
    r = new(root)
    assert r.returncode == 0 and "git=ya" in r.stdout, r.stdout + r.stderr
    assert not (root / IGNORE).exists()


def test_gitignore_milik_user_tidak_ditimpa(make_repo):
    root = synced(make_repo)
    write_files(root, {IGNORE: "# tiket di-commit\n"})
    committed(root, IGNORE)
    r = new(root)
    assert r.returncode == 0 and "git=ya" in r.stdout and "ditulis" not in r.stdout, r.stdout
    assert (root / IGNORE).read_text(encoding="utf-8") == "# tiket di-commit\n"


def test_tiket_lama_ter_track_tetap_di_commit(make_repo):
    root = synced(make_repo)
    write_files(root, {f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    committed(root, f"{TDIR}/TICKET.md")
    r = new(root)
    assert "1 berkas tiket lama tetap ter-track" in r.stdout, r.stdout
    assert ticket_review(root, TDIR, "PASS").returncode == 0      # review.md baru → diabaikan
    r = tk(root, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    assert r.returncode == 0, r.stdout + r.stderr
    assert git(root, "log", "-1", "--format=%s").strip() == "docs(ticket): kunci TICKET cicilan READY"
    assert git(root, "show", "--name-only", "--format=", "HEAD").split() == [f"{TDIR}/TICKET.md"]
    assert status(root) == ""


def test_commit_draft_tiket_lama_ter_track_hanya_ticket_md(make_repo):
    root = synced(make_repo)
    write_files(root, {f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    committed(root, f"{TDIR}/TICKET.md")
    assert new(root).returncode == 0
    assert ticket_review(root, TDIR, "PASS").returncode == 0      # frontmatter berubah, review.md diabaikan
    r = tk(root, "commit", "--ticketdir", TDIR, "--stage", "draft")
    assert r.returncode == 0 and "COMMIT PASS" in r.stdout, r.stdout + r.stderr
    assert git(root, "log", "-1", "--format=%s").strip() == "docs(ticket): draft TICKET cicilan"
    assert git(root, "show", "--name-only", "--format=", "HEAD").split() == [f"{TDIR}/TICKET.md"]
    assert status(root) == ""


def test_commit_tertunda_diabaikan_tanpa_commit(make_repo):
    root = synced(make_repo)
    r = new(root, "cicilan")
    rel = r.stdout.split("NEW PASS: ", 1)[1].split(" ", 1)[0]
    before = commits(root)
    r = tk(root, "commit", "--ticketdir", rel, "--stage", "tertunda")
    assert r.returncode == 0 and "commit diabaikan git" in r.stdout, r.stdout + r.stderr
    assert commits(root) == before and status(root) == ""


def test_diabaikan_tanpa_sinkron_diperingatkan(make_repo):
    root = make_repo({".gitignore": "analyst/tickets/\n"})
    committed(root, ".gitignore")
    r = new(root)
    assert r.returncode == 0 and "git=diabaikan" in r.stdout and "PERINGATAN" in r.stdout, r.stdout
    assert not (root / IGNORE).exists()
