"""Regresi 09 E18–E20 — backend: bukti mendarat brief, pagar code-reviewer, keutuhan `## Counters`."""
import json

import pytest

from conftest import PLUGINS, TD, be_checks, be_run, brief, commit, land, run_script, write_files

ARCH = "architect/scripts/check_preconditions.py"
COUNTERS = "analyst/scripts/chain_counters.py"
GUARD = PLUGINS / "backend/hooks/guard_bash.py"
REVIEWER = "backend:code-reviewer"


# --- E18 ---------------------------------------------------------------------------------------

@pytest.mark.regression("E18")
def test_e18_subjek_meleset_satu_spasi_tetap_terdeteksi_mendarat(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    write_files(chain_repo, {"src/order.go": "package order // lock\n"})
    commit(chain_repo, "fix(order):  implement lock", "src/order.go")      # dua spasi
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["entry"].startswith("KOREKSI:01:"), c3


@pytest.mark.regression("E18")
def test_e18_done_tulisan_tangan_tanpa_kode_ditolak(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    b = chain_repo / TD / "brief-01-lock.md"
    b.write_text(b.read_text(encoding="utf-8").replace("status: READY", "status: DONE"), encoding="utf-8")
    commit(chain_repo, "fix(order): implement lock")                        # hanya dokumen
    brief(chain_repo, "02", "endpoint", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "FAIL" and "brief-01-lock.md" in c3["summary"], c3
    assert "FASE_3" not in c3.get("entry", "")


@pytest.mark.regression("E18")
def test_e18_done_mendarat_dengan_subjek_lain_tetap_sah(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    b.write_text(b.read_text(encoding="utf-8").replace('"fix(order): implement lock"', '"feat: kunci pesanan"'),
                 encoding="utf-8")
    land(chain_repo, b)
    brief(chain_repo, "02", "endpoint", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["entry"] == "FASE_3:02"


# --- E19: pagar `backend:code-reviewer` -----------------------------------------------------

def hook(repo, *, cmd=None, tool="Bash", file_path=None, agent=REVIEWER):
    ti = {"command": cmd} if tool == "Bash" else {"file_path": file_path, "content": "x"}
    data = {"cwd": str(repo), "tool_name": tool, "tool_input": ti, "hook_event_name": "PreToolUse",
            "agent_type": agent, "agent_id": "a1"}
    return run_script(GUARD, "hook", stdin=json.dumps(data))


@pytest.mark.regression("E19")
@pytest.mark.parametrize("cmd", [
    "git merge-base main HEAD", "git symbolic-ref -q --short HEAD", "git status --porcelain",
    "git log -S Submit --oneline", "git diff --name-only abc..HEAD", "ls backenddev",
    f"git add {TD}/REVIEW.md backenddev/issues/README.md", "git commit -m 'docs(order-fix): add final review report'",
])
def test_e19_reviewer_boleh(chain_repo, cmd):
    r = hook(chain_repo, cmd=cmd)
    assert r.returncode == 0, (cmd, r.stderr)


@pytest.mark.regression("E19")
@pytest.mark.parametrize("cmd", [
    "git reset --hard HEAD~3", "git checkout main", "git push", "git rebase main", "git add src/order.go",
    "git add -A", "git commit --amend -m x", "git commit -m x --no-verify", "go test ./...",
    "git log; git reset --hard", "git diff --output=/tmp/x",
])
def test_e19_reviewer_dilarang(chain_repo, cmd):
    r = hook(chain_repo, cmd=cmd)
    assert r.returncode == 2 and "DITOLAK" in r.stderr, (cmd, r.stderr)


@pytest.mark.regression("E19")
@pytest.mark.parametrize("path, code", [
    (f"{TD}/REVIEW.md", 0), ("backenddev/issues/README.md", 0), ("src/order.go", 2), (f"{TD}/TASK.md", 2),
])
def test_e19_reviewer_menulis_hanya_laporan(chain_repo, path, code):
    assert hook(chain_repo, tool="Write", file_path=path).returncode == code


@pytest.mark.regression("E19")
def test_e19_agent_lain_tidak_terdampak(chain_repo):
    assert hook(chain_repo, cmd="git reset --hard HEAD", agent="backend:brief-reviewer").returncode == 0


# --- E20: `## Counters` ------------------------------------------------------------------------

def counters(repo, *args):
    return be_run(repo, COUNTERS, "--taskdir", TD, *args)


@pytest.mark.regression("E20")
def test_e20_baris_tak_dikenal_fail_rapi(chain_repo):
    task = chain_repo / TD / "TASK.md"
    task.write_text(task.read_text(encoding="utf-8") + "\n## Counters\n\n| Kunci | Nilai | Plafon |\n|---|---|---|\n"
                    "| Reentry | 9 | 2 |\n", encoding="utf-8")
    for args in (("--check",), ("--bump", "reentry")):
        r = counters(chain_repo, *args)
        assert r.returncode == 1 and "Traceback" not in r.stderr and "tak dikenal" in r.stdout, r.stdout + r.stderr


@pytest.mark.regression("E20")
def test_e20_kunci_global_diturunkan_tangan_terdeteksi(chain_repo):
    """Riwayat tabel dari log tulisan skrip `.explore/counters-log.json`, bukan git (Langkah 24)."""
    assert counters(chain_repo, "--bump", "reentry").returncode == 0
    task = chain_repo / TD / "TASK.md"
    task.write_text(task.read_text(encoding="utf-8").replace("| reentry | 1 |", "| reentry | 0 |"), encoding="utf-8")
    r = counters(chain_repo, "--check")
    assert r.returncode == 1 and "reentry turun 1 → 0" in r.stdout, r.stdout
    r = counters(chain_repo, "--bump", "chain_transition")                # menulis di atasnya pun ditolak
    assert r.returncode == 1 and "disunting tangan" in r.stdout, r.stdout


@pytest.mark.regression("E20")
def test_e20_reset_hop_sesudah_reentry_sah(chain_repo):
    assert counters(chain_repo, "--bump", "review_round:PRD").returncode == 0
    assert counters(chain_repo, "--bump", "reentry").returncode == 0
    assert counters(chain_repo, "--reset-hop", "PRD").returncode == 0
    r = counters(chain_repo, "--check")
    assert r.returncode == 0, r.stdout


@pytest.mark.regression("E20")
def test_e20_kunci_hop_turun_tanpa_reentry_terdeteksi(chain_repo):
    assert counters(chain_repo, "--bump", "review_round:PRD").returncode == 0
    assert counters(chain_repo, "--reset-hop", "PRD").returncode == 0      # tanpa --bump reentry
    r = counters(chain_repo, "--check")
    assert r.returncode == 1 and "review_round:PRD turun" in r.stdout, r.stdout
