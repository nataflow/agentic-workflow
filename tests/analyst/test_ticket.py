"""analyst `_common/ticket.py` + `_common/validate_doc.py` — siklus tiket dan validator (L6.1).

Contoh terisi diambil dari bagian 3 kedua template saat test berjalan, supaya fixture tidak
basi ketika template berubah.
"""
import json
import re

import pytest

from conftest import PLUGINS, git, run_script, ticket_review, write_files

SKILLS = PLUGINS / "analyst" / "skills"
TICKET = SKILLS / "_common" / "ticket.py"
VALIDATE = SKILLS / "_common" / "validate_doc.py"
TD = "analyst/tickets/2609250000-cicilan-pembayaran"


def _example(template) -> str:
    section = template.read_text(encoding="utf-8").split("\n## 3. ", 1)[1]
    return re.search(r"````markdown\n(.*?)\n````", section, re.S).group(1) + "\n"


def elicit_md() -> str:
    """TICKET.md sesudah elisitasi ditutup (contoh `elicit-template.md`)."""
    return _example(SKILLS / "elicit" / "templates" / "elicit-template.md")


def ticket_md() -> str:
    """Kartu lengkap: kartu contoh `ticket-template.md` di atas catatan elisitasi, priority terisi."""
    fm, body = elicit_md().split("\n---\n", 1)
    card = _example(SKILLS / "spec" / "templates" / "ticket-template.md").split("## Catatan Elisitasi")[0]
    notes = body[body.index("## Catatan Elisitasi"):]
    return fm.replace("priority: -", "priority: HIGH") + "\n---\n" + card + notes


def repo_with(make_repo, text: str, *, commit: bool = True):
    root = make_repo({f"{TD}/TICKET.md": text})
    if commit:
        git(root, "commit", "-q", "--allow-empty", "-m", "init")
    return root


def ticket(root, *args, cwd=None):
    return run_script(TICKET, *args, cwd=cwd or root)


def validate(root, kind, ticketdir=TD):
    return run_script(VALIDATE, "--kind", kind, "--ticketdir", ticketdir, "--json", cwd=root)


def state_of(root, *, all_=True) -> str:
    rows = json.loads(ticket(root, "state", "--json", *(["--all"] if all_ else [])).stdout)["ticketdirs"]
    return {r["ticketdir"]: r["state"] for r in rows}.get(TD, "-")


# --- validate_doc --------------------------------------------------------------------------------

def test_contoh_template_lolos_kedua_kind(make_repo):
    root = repo_with(make_repo, ticket_md())
    assert validate(root, "ticket").returncode == 0
    root2 = repo_with(make_repo, elicit_md(), commit=False)
    out = json.loads(validate(root2, "elicit").stdout)
    assert out["status"] == "PASS" and out["passed_count"] == out["total_count"], out


def test_contoh_crlf_tetap_lolos(make_repo):
    """E6."""
    root = repo_with(make_repo, ticket_md().replace("\n", "\r\n"))
    assert json.loads(validate(root, "ticket").stdout)["status"] == "PASS"


@pytest.mark.parametrize("kind,cut,check", [
    ("elicit", "#### Aturan Bisnis", 4),         # pilar hilang
    ("ticket", "## Acceptance Criteria", 2),     # heading wajib hilang → struktur
])
def test_bagian_wajib_hilang_gagal(make_repo, kind, cut, check):
    text = elicit_md() if kind == "elicit" else ticket_md()
    head, tail = text.split(cut, 1)
    nxt = re.search(r"\n#{2,4} ", tail)
    root = repo_with(make_repo, head + (tail[nxt.start() + 1:] if nxt else ""), commit=False)
    out = json.loads(validate(root, kind).stdout)
    assert out["status"] == "FAIL"
    assert {c["id"]: c["status"] for c in out["checks"]}[check] == "FAIL", out["checks"]


def test_ticketdir_hilang_fail_json(make_repo):
    """E8."""
    root = make_repo()
    out = validate(root, "ticket")
    assert out.returncode == 1 and json.loads(out.stdout)["status"] == "FAIL"


def test_frontmatter_rusak_fail(make_repo):
    """E9: pagar penutup hilang."""
    root = repo_with(make_repo, ticket_md().replace("\n---\n", "\n", 1).replace("---\n", "--\n", 1), commit=False)
    assert json.loads(validate(root, "ticket").stdout)["status"] == "FAIL"


# --- ticket.py -----------------------------------------------------------------------------------

def test_siklus_review_approve_reopen_cancel(make_repo):
    root = repo_with(make_repo, ticket_md())
    assert ticket(root, "check", "--gate", "spec", "--ticketdir", TD).returncode == 0
    r = ticket_review(root, TD, "PASS")
    assert r.returncode == 0 and "REVIEW PASS" in r.stdout, r.stdout + r.stderr
    r = ticket(root, "approve", "--ticketdir", TD, "--answer", "ya")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "READY" in git(root, "log", "-1", "--format=%s")
    assert state_of(root, all_=False) == "-"               # READY tidak lagi di daftar aktif
    assert state_of(root) == "READY"
    assert ticket(root, "reopen", "--ticketdir", TD, "--reason", "ubah BR-2").returncode == 0
    assert state_of(root, all_=False) == "DRAFT"
    assert ticket(root, "cancel", "--ticketdir", TD, "--reason", "batal").returncode == 0
    assert state_of(root, all_=False) == "-"


def test_approve_tanpa_review_ditolak(make_repo):
    root = repo_with(make_repo, ticket_md())
    r = ticket(root, "approve", "--ticketdir", TD, "--answer", "ya")
    assert r.returncode != 0
    assert state_of(root) == "DRAFT"


def test_commit_draft_revise_dan_tertunda(make_repo):
    root = repo_with(make_repo, ticket_md())
    assert ticket_review(root, TD, "PASS").returncode == 0
    r = ticket(root, "commit", "--ticketdir", TD, "--stage", "draft")
    assert r.returncode == 0, r.stdout + r.stderr
    assert git(root, "log", "-1", "--format=%s").strip() == "docs(ticket): draft TICKET cicilan-pembayaran"
    assert sorted(git(root, "show", "--name-only", "--format=", "HEAD").split()) == [f"{TD}/TICKET.md", f"{TD}/review.md"]
    assert ticket(root, "revise", "--ticketdir", TD).returncode == 0
    assert ticket(root, "commit", "--ticketdir", TD, "--stage", "draft").returncode == 0
    assert git(root, "log", "-1", "--format=%s").strip() == "docs(ticket): revise TICKET cicilan-pembayaran"
    (root / TD / "TICKET.md").write_text(ticket_md().replace("elicitation: CLOSED", "elicitation: OPEN"), encoding="utf-8")
    assert ticket(root, "commit", "--ticketdir", TD, "--stage", "tertunda").returncode == 0
    assert git(root, "log", "-1", "--format=%s").strip() == "docs(ticket): elisitasi cicilan-pembayaran (tertunda)"
    assert git(root, "status", "--porcelain") == ""


def test_commit_menolak_tiket_ready(make_repo):
    root = repo_with(make_repo, ticket_md())
    assert ticket_review(root, TD, "PASS").returncode == 0
    assert ticket(root, "approve", "--ticketdir", TD, "--answer", "ya").returncode == 0
    r = ticket(root, "commit", "--ticketdir", TD, "--stage", "draft")
    assert r.returncode == 1 and "bukan DRAFT" in r.stdout, r.stdout


def test_new_di_luar_repo_git(make_repo):
    """E1: tanpa git, `new` tetap jalan dan melaporkan git=tidak."""
    root = make_repo(git_init=False)
    r = ticket(root, "new", "--slug", "cicilan", "--type", "FEATURE", "--requester", "Rina", "--request", "Tolong bikin fitur cicilan.")
    assert r.returncode == 0 and "git=tidak" in r.stdout, r.stdout + r.stderr
    assert [p.name for p in (root / "analyst" / "tickets").iterdir()][0].endswith("-cicilan")


@pytest.mark.parametrize("name", ["repo dengan spasi", "répo-ünïcode"])
def test_new_path_berspasi_dan_unicode(make_repo, name):
    """E5."""
    root = make_repo(name=name)
    r = ticket(root, "new", "--slug", "cicilan", "--type", "BUG", "--requester", "Rina", "--request", "Tolong bikin fitur cicilan.")
    assert r.returncode == 0 and "git=ya" in r.stdout, r.stdout + r.stderr


def test_new_dari_subdirektori_menulis_di_root_git(make_repo):
    """E4."""
    root = make_repo({"src/features/.keep": ""})
    r = ticket(root, "new", "--slug", "cicilan", "--type", "FEATURE", "--requester", "Rina", "--request", "Tolong bikin fitur cicilan.", cwd=root / "src" / "features")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (root / "analyst" / "tickets").is_dir()
    assert not (root / "src" / "features" / "analyst").exists()


# Regresi A5/A6 (sebelumnya xfail di sini) pindah ke test_ticket_8a.py.
