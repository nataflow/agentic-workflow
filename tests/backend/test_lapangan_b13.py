"""B13 — diff utuh untuk `code-reviewer` (`architect/scripts/review_diff.py`), review lapangan hkm 2611.

`code-reviewer` dulu membaca diff lewat `git show` per berkas (1.756 panggilan Bash di 62 dispatch). Architect kini
menulis satu berkas diff rentang merge-base yang dibaca reviewer dengan `Read`."""
import json

import pytest

from conftest import BE_SKILLS, PLUGINS, TD, commit, git, run_script, write_files

SCRIPT = BE_SKILLS / "architect/scripts/review_diff.py"
OUT = f"{TD}/.explore/review/diff.patch"


def _run(repo, *extra, base="main"):
    proc = run_script(SCRIPT, "--taskdir", TD, "--base-branch", base, "--json", *extra, cwd=repo)
    return proc.returncode, json.loads(proc.stdout)


@pytest.fixture
def landed(chain_repo):
    write_files(chain_repo, {"src/order.go": "package order\n\nfunc Refund() {}\n",
                             "src/order_test.go": "package order\n",
                             "backenddev/issues/README.md": "# Issues\n",
                             ".claude/profile/backenddev/anti-patterns.md": "# AP\n- x\n"})
    commit(chain_repo, "feat(order): implement refund", "src/order.go", "src/order_test.go",
           "backenddev/issues/README.md", ".claude/profile/backenddev/anti-patterns.md")
    return chain_repo


@pytest.mark.regression("B13")
def test_diff_utuh_ditulis_dengan_header_rentang(landed):
    code, out = _run(landed)
    assert code == 0, out
    mb = git(landed, "merge-base", "main", "HEAD").strip()
    head = git(landed, "rev-parse", "HEAD").strip()
    assert out["file"] == OUT and out["range"] == f"{mb}..{head}" and out["files"] == 2
    teks = (landed / OUT).read_text(encoding="utf-8")
    assert f"range: {mb}..{head}\n" in teks and f"head: {head}\n" in teks
    assert "## stat" in teks and "## diff" in teks and "+func Refund() {}" in teks
    assert "src/order_test.go" in teks


@pytest.mark.regression("B13")
def test_artefak_backenddev_dan_claude_dikecualikan(landed):
    code, _ = _run(landed)
    assert code == 0
    teks = (landed / OUT).read_text(encoding="utf-8")
    diff = teks.split("## diff", 1)[1]
    assert "backenddev/issues/README.md" not in diff and "anti-patterns.md" not in diff
    assert "dikecualikan: backenddev/, .claude/" in teks


@pytest.mark.regression("B13")
def test_berkas_tidak_mengotori_tree_dan_lolos_panen_laci(landed):
    assert _run(landed)[0] == 0
    assert git(landed, "status", "--porcelain").strip() == ""
    assert not list((landed / TD / ".explore").glob("*.md"))   # validate_briefs memanen .explore/*.md saja


@pytest.mark.regression("B13")
def test_ditulis_ulang_sesudah_commit_baru(landed):
    _run(landed)
    write_files(landed, {"src/order.go": "package order\n\nfunc Refund() { _ = 1 }\n"})
    commit(landed, "fix(order): refund", "src/order.go")
    code, out = _run(landed)
    assert code == 0 and out["head"] == git(landed, "rev-parse", "HEAD").strip()
    assert f"head: {out['head']}" in (landed / OUT).read_text(encoding="utf-8")


@pytest.mark.regression("B13")
@pytest.mark.parametrize("kasus", ["base", "detached", "merge-base"])
def test_fail_cabang_tidak_sah(landed, kasus):
    base = "main"
    if kasus == "base":
        git(landed, "checkout", "-q", "main")
    elif kasus == "detached":
        git(landed, "checkout", "-q", "--detach")
    else:
        base = "tidak-ada"
    code, out = _run(landed, base=base)
    assert code == 1 and out["status"] == "FAIL", out
    assert not (landed / OUT).exists()


@pytest.mark.regression("B13")
def test_fail_taskdir_tidak_ada(landed):
    proc = run_script(SCRIPT, "--taskdir", "backenddev/docs/2601010000-x", "--base-branch", "main", cwd=landed)
    assert proc.returncode == 2 and proc.stdout.startswith("REVIEW-DIFF FAIL: taskdir")


@pytest.mark.regression("B13")
def test_keluaran_satu_baris_pass(landed):
    proc = run_script(SCRIPT, "--taskdir", TD, "--base-branch", "main", cwd=landed)
    assert proc.returncode == 0
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 1 and lines[0].startswith(f"REVIEW-DIFF PASS: {OUT} · ") and "2 berkas" in lines[0]


@pytest.mark.regression("B13")
def test_prosa_architect_dispatcher_dan_reviewer_selaras():
    arch = (BE_SKILLS / "architect/SKILL.md").read_text(encoding="utf-8")
    fase4 = arch.split("### Fase 4", 1)[1].split("### Fase 5", 1)[0]
    assert "skills/architect/scripts/review_diff.py --taskdir <taskdir> --base-branch <base_branch>" in fase4
    assert "--slot diff_file=" in fase4
    disp = (BE_SKILLS / "architect/dispatcher/reviewer.md").read_text(encoding="utf-8")
    baris = [b for b in disp.splitlines() if "{diff_file}" in b]
    assert len(baris) == 2 and any(b.startswith("- Diff Utuh:") for b in baris)   # satu baris template, satu baris slot
    assert "**[OPTIONAL]**" in next(b for b in baris if b.startswith("|"))
    agent = (PLUGINS / "backend/agents/code-reviewer.md").read_text(encoding="utf-8")
    assert "Diff utuh (B13)" in agent and "`git rev-parse HEAD`" in agent and "`head:`" in agent


@pytest.mark.regression("B13")
def test_slot_diff_file_kosong_menghapus_barisnya(tmp_path):
    rp = BE_SKILLS / "_common/render_prompt.py"
    args = ["--template", str(BE_SKILLS / "architect/dispatcher/reviewer.md"), "--root", str(tmp_path),
            "--out", f"{TD}/.explore/prompt/code-review.md", "--slot", f"taskdir={TD}", "--slot", "base_branch=main",
            "--slot", "adapter_path=/a.md", "--slot", "findings_contract=/f.md", "--json"]
    kosong = run_script(rp, *args, "--slot", "diff_file=", cwd=tmp_path)
    assert kosong.returncode == 0, kosong.stdout
    body = (tmp_path / TD / ".explore/prompt/code-review.md").read_text(encoding="utf-8")
    assert "Diff Utuh" not in body
    isi = run_script(rp, *args, "--slot", f"diff_file={OUT}", cwd=tmp_path)
    assert isi.returncode == 0, isi.stdout
    body = (tmp_path / TD / ".explore/prompt/code-review.md").read_text(encoding="utf-8")
    assert f"- Diff Utuh: `{OUT}`" in body
