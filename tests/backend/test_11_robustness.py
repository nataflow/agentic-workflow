"""Regresi 11 — robustness plugin backend (H1–H36)."""
import json

import pytest

from conftest import PLUGINS, TD, be_checks, be_run, brief, commit, git, land, run_script, write_files

ARCH = "architect/scripts/check_preconditions.py"
VALIDATE = "plan/scripts/validate_briefs.py"
SCAFFOLD = "plan/scripts/scaffold_brief.py"
SCOPE = "_common/verify_scope.py"
GUARD = PLUGINS / "backend/hooks/guard_bash.py"
IMPL = "backend:code-implementor"
REVIEWER = "backend:code-reviewer"

SCOPE_BODY = ("# Brief\n## File scope\n\n**File**\n\n| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n"
              "| modify | `src/order.go` | `Submit` | pasang lock |\n{extra}\n"
              "## Work status\n\n| Item | Status | Catatan |\n|---|---|---|\n| P1-1 | PLANNED | — |\n")


def hook(repo, cmd, agent=IMPL):
    data = {"cwd": str(repo), "tool_name": "Bash", "tool_input": {"command": cmd},
            "hook_event_name": "PreToolUse", "agent_type": agent, "agent_id": "a1"}
    return run_script(GUARD, "hook", stdin=json.dumps(data))


def scoped_brief(repo, extra=""):
    b = brief(repo, "01", "lock", "READY", body=SCOPE_BODY.format(extra=extra))
    commit(repo, "docs(plan): add 1 briefs for order-fix")
    return b


def checks(repo, script, *args):
    proc = be_run(repo, script, "--json", *args)
    assert proc.stdout.strip(), proc.stderr
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


def verify(repo, sha):
    return be_run(repo, SCOPE, "--brief", f"{TD}/brief-01-lock.md", "--commit", sha)


# --- H1: pagar shell ---------------------------------------------------------------------------

@pytest.mark.regression("H1")
@pytest.mark.parametrize("cmd", [
    "git diff $'--output=/tmp/h1'", "git diff --{out,}put=/tmp/h1", "git log --format=$HOME",
    "git diff \"$(echo x)\"", "git status 2>&1", "git log | head", "git commit -m \"a\" -m \"b <c@d>\"",
])
@pytest.mark.parametrize("agent", [IMPL, REVIEWER])
def test_h1_ekspansi_shell_ditolak(chain_repo, agent, cmd):
    scoped_brief(chain_repo)
    assert run_script(GUARD, "lease", "--brief", f"{TD}/brief-01-lock.md", cwd=chain_repo).returncode == 0
    r = hook(chain_repo, cmd, agent)
    assert r.returncode == 2 and "DITOLAK" in r.stderr, (cmd, r.stderr)


@pytest.mark.regression("H1")
@pytest.mark.parametrize("cmd", ['git log -S "<T>" --oneline', "git log -S 'a->b' --oneline",
                                 "git show HEAD@{1} --stat", 'git commit -m "feat: #482 implement lock"'])
def test_h1_kutip_berisi_operator_tetap_lolos(chain_repo, cmd):
    scoped_brief(chain_repo)
    run_script(GUARD, "lease", "--brief", f"{TD}/brief-01-lock.md", cwd=chain_repo)
    assert hook(chain_repo, cmd).returncode == 0, cmd


# --- H2: satu aturan baris File scope ----------------------------------------------------------

@pytest.mark.regression("H2")
def test_h2_baris_berkolom_kurang_tidak_masuk_lease_dan_gagal_check_s(chain_repo):
    scoped_brief(chain_repo, extra="| modify | `src/pay.go` | `Charge` |")
    assert run_script(GUARD, "lease", "--brief", f"{TD}/brief-01-lock.md", cwd=chain_repo).returncode == 0
    allowed = json.loads((chain_repo / ".git/nataflow/lease-backend.json").read_text())["allowed"]
    assert "src/order.go" in allowed and "src/pay.go" not in allowed
    s = checks(chain_repo, VALIDATE, "--taskdir", TD, "--brief", "01")["S"]
    assert s["status"] == "FAIL" and any("berkolom kurang" in d for d in s["details"]), s


@pytest.mark.regression("H2")
def test_h2_heading_beda_huruf_dibaca_lease_dan_ditolak_check_s(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY", body=SCOPE_BODY.format(extra="").replace("## File scope", "## File Scope"))
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    assert run_script(GUARD, "lease", "--brief", str(b.relative_to(chain_repo)), cwd=chain_repo).returncode == 0
    s = checks(chain_repo, VALIDATE, "--taskdir", TD, "--brief", "01")["S"]
    assert any("`## File Scope` wajib ditulis persis `## File scope`" in d for d in s["details"]), s


# --- H3/H4: verify_scope membaca brief sebelum unit ---------------------------------------------

@pytest.mark.regression("H3")
def test_h3_brief_diperluas_pelaksana_ditolak(chain_repo):
    b = scoped_brief(chain_repo)
    b.write_text(b.read_text().replace("| pasang lock |\n", "| pasang lock |\n| modify | `src/other.go` | `X` | y |\n"))
    write_files(chain_repo, {"src/other.go": "package order // liar\n"})
    git(chain_repo, "add", "src/other.go")                 # ikut commit unit di bawah
    r = verify(chain_repo, land(chain_repo, b))
    assert r.returncode == 1 and "disunting di luar" in r.stdout, r.stdout


@pytest.mark.regression("H3")
def test_h3_anchor_diubah_pelaksana_ditolak(chain_repo):
    b = scoped_brief(chain_repo)
    b.write_text(b.read_text().replace("`Submit`", "`Submit`, `Keep`"))
    sha = land(chain_repo, b)
    r = verify(chain_repo, sha)
    assert r.returncode == 1 and "disunting di luar" in r.stdout, r.stdout


@pytest.mark.regression("H3")
def test_h3_status_dan_work_status_sah_disunting(chain_repo):
    b = scoped_brief(chain_repo)
    b.write_text(b.read_text().replace("| P1-1 | PLANNED | — |", "| P1-1 | FIXED | lock terpasang |"))
    sha = land(chain_repo, b)
    r = verify(chain_repo, sha)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.regression("H4")
def test_h4_rename_dari_luar_scope_ditolak(chain_repo):
    write_files(chain_repo, {"src/important.go": "package order\n\nfunc Important() {}\n"})
    commit(chain_repo, "chore: berkas lain", "src/important.go")
    b = scoped_brief(chain_repo, extra="| create | `src/new.go` | — | berkas baru |")
    git(chain_repo, "mv", "src/important.go", "src/new.go")      # rename sungguhan: tujuan belum ada
    b.write_text(b.read_text().replace("status: READY", "status: DONE"))
    sha = commit(chain_repo, "fix(order): implement lock", str(b.relative_to(chain_repo)))
    r = verify(chain_repo, sha)
    assert r.returncode == 1 and "src/important.go" in r.stdout, r.stdout


@pytest.mark.regression("H4")
def test_h4_path_non_ascii_di_scope_lolos(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY", body=SCOPE_BODY.format(extra="").replace("src/order.go", "src/café.go"))
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    r = verify(chain_repo, land(chain_repo, b, code="src/café.go"))
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.regression("H4")
def test_h4_commit_merge_ditolak(chain_repo):
    scoped_brief(chain_repo)
    git(chain_repo, "checkout", "-q", "-b", "side")
    write_files(chain_repo, {"src/side.go": "package order\n"})
    commit(chain_repo, "side", "src/side.go")
    git(chain_repo, "checkout", "-q", "fix/order-fix")
    write_files(chain_repo, {"src/order.go": "package order // lock\n"})
    commit(chain_repo, "fix(order): implement lock", "src/order.go")
    git(chain_repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    r = verify(chain_repo, git(chain_repo, "rev-parse", "HEAD").strip())
    assert r.returncode == 2 and "merge" in r.stderr, r.stderr


# --- H5: koreksi status resmi -------------------------------------------------------------------

@pytest.mark.regression("H5")
def test_h5_koreksi_resmi_diterima_sesi_berikutnya(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    write_files(chain_repo, {"src/order.go": "package order // lock\n"})
    sha = commit(chain_repo, "fix(order): implement lock", "src/order.go")      # status tertinggal
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["entry"] == f"KOREKSI:01:{sha}"
    b.write_text(b.read_text().replace("status: READY", "status: DONE"))
    commit(chain_repo, f"chore(order-fix): koreksi status brief-01 ke DONE ({sha})", str(b.relative_to(chain_repo)))
    brief(chain_repo, "02", "endpoint", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "PASS" and c3["entry"] == "FASE_3:02", c3


@pytest.mark.regression("H5")
def test_h5_done_dokumen_tanpa_commit_unit_tetap_ditolak(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    b.write_text(b.read_text().replace("status: READY", "status: DONE"))
    commit(chain_repo, "chore(order-fix): koreksi status brief-01 ke DONE (abc1234)", str(b.relative_to(chain_repo)))
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["status"] == "FAIL"


# --- H6/H7: identitas brief ---------------------------------------------------------------------

@pytest.mark.regression("H6")
def test_h6_commit_message_ganda_gagal_check_c(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    brief(chain_repo, "02", "lock-lagi", "READY", commit_scope="order")
    p = chain_repo / TD / "brief-02-lock-lagi.md"
    p.write_text(p.read_text().replace("implement lock-lagi", "implement lock"))
    c = checks(chain_repo, VALIDATE, "--taskdir", TD)["C"]
    assert c["status"] == "FAIL" and any("`commit_message` sama" in d for d in c["details"]), c


@pytest.mark.regression("H6")
def test_h6_unit_ganda_ditolak_matriks(chain_repo):
    spec = chain_repo / TD / ".explore/brief-spec.json"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps({"briefs": [
        {"nn": "01", "unit": "stock-index", "title": "a", "risk": "MINOR", "fulfills": ["SC-1"]},
        {"nn": "02", "unit": "stock-index", "title": "b", "risk": "MINOR", "fulfills": ["SC-2"]}]}))
    r = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", str(spec))
    assert r.returncode == 1 and "sudah dipakai brief 01" in r.stdout, r.stdout


@pytest.mark.regression("H7")
def test_h7_nn_ganda_gagal_check_c_dan_architect(chain_repo):
    brief(chain_repo, "01", "order-guard", "READY")
    brief(chain_repo, "01", "order-lock", "READY")
    commit(chain_repo, "docs(plan): add 2 briefs for order-fix")
    c = checks(chain_repo, VALIDATE, "--taskdir", TD)["C"]
    assert any("brief-01 dipakai 2 berkas" in d for d in c["details"]), c
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "FAIL" and "dipakai 2 berkas" in c3["summary"], c3


@pytest.mark.regression("H7")
def test_h7_brief_ready_di_luar_matriks_gagal(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    brief(chain_repo, "02", "endpoint", "READY")
    write_files(chain_repo, {f"{TD}/.explore/brief-matrix.json": json.dumps(
        {"briefs": [{"nn": "01", "unit": "lock"}]})})
    c = checks(chain_repo, VALIDATE, "--taskdir", TD)["C"]
    assert any("brief-02-endpoint.md: brief READY tidak ada di matriks" in d for d in c["details"]), c


@pytest.mark.regression("H7")
def test_h7_scaffold_menolak_nn_yang_dipakai_unit_lain(chain_repo):
    brief(chain_repo, "01", "order-guard", "READY")
    write_files(chain_repo, {f"{TD}/.explore/brief-matrix.json": json.dumps({"briefs": [
        {"nn": "01", "unit": "order-lock", "title": "t", "risk": "MINOR"}]})})
    r = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--nn", "01")
    assert r.returncode != 0 and "brief-01 sudah dipakai brief-01-order-guard.md" in r.stdout + r.stderr, r.stdout
