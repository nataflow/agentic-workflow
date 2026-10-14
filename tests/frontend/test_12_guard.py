"""Regresi 12 Tahap 1 — pagar hook `frontend` dan deteksi SessionStart (J1–J9).

Pagar reviewer ditembus lewat pager `git grep` (J1), opsi global sesudah `--no-pager` (J2), dan
`symbolic-ref` yang menulis HEAD (J3); penulis lain (implementor/explorer/doc-reviewer) dapat menulis
ke tempat yang tak terlihat `git status` (J4); TREE meloloskan semua berkas temuan (J6); `chain.py`
dicocokkan akhiran (J7); glob tanpa kutip sebelum `--` (J8). `detect.py` crash pada workspace `.`
(J5) dan salah membaca opt-out berkoma serta `plugin` asing (J9).
"""
import json
import os
import re

import pytest

from conftest import FE_MINOR_TD as TD, FE_SKILLS, PLUGINS, commit, fe_review_md, fe_run, load_module, \
    run_hook, run_script, write_files

GUARD = PLUGINS / "frontend/hooks/guard_bash.py"
CHAIN = PLUGINS / "frontend/skills/_common/chain.py"
REVIEWER = "frontend:code-reviewer"
IMPL = "frontend:code-implementor"
EXPLORER = "frontend:code-explorer"
DOC_REVIEWER = "frontend:doc-reviewer"
TDIR = "frontenddev/docs/2609260000-akar"
# Baris ignore lama (tanpa jangkar) seperti repo yang diprofil sebelum J4.
LEGACY_IGNORE = ".env*\n.explore/\n.frontenddev/\n"
REACT_VITE = json.dumps({"dependencies": {"react": "^19"}, "devDependencies": {"vite": "^6"}})
EXPRESS = json.dumps({"dependencies": {"express": "^4"}})


def hook(repo, *, cmd=None, tool="Bash", file_path=None, agent=REVIEWER):
    ti = {"command": cmd} if tool == "Bash" else {"file_path": file_path, "content": "x"}
    data = {"cwd": str(repo), "tool_name": tool, "tool_input": ti, "hook_event_name": "PreToolUse",
            "agent_type": agent, "agent_id": "a1"}
    return run_script(GUARD, "hook", stdin=json.dumps(data))


def denied(r):
    return r.returncode == 2 and "DITOLAK" in r.stderr


@pytest.fixture
def repo(make_repo):
    root = make_repo({"src/a.ts": "x\n", f"{TDIR}/TASK.md": "# t\n", ".gitignore": LEGACY_IGNORE})
    commit(root, "init")
    return root


# --- J1: `git grep` keluar dari allowlist reviewer ------------------------------------------------

@pytest.mark.regression("J1")
@pytest.mark.parametrize("cmd", ["git grep -Otouch -e x", 'git grep "-Otouch /tmp/j1;true" -e x',
                                 "git grep --open-files=touch -e x", "git grep -e x"])
def test_j1_git_grep_ditolak(repo, cmd):
    assert denied(hook(repo, cmd=cmd)), cmd


# --- J2: seluruh posisi opsi global dinilai ------------------------------------------------------

@pytest.mark.regression("J2")
@pytest.mark.parametrize("cmd", ["git --no-pager --config-env=diff.external=SHELL diff",
                                 "git --no-pager --exec-path=/tmp log -1", "git --no-pager --git-dir=/tmp/x log",
                                 "git --no-pager --work-tree=/ status", "git --no-pager -c core.pager=sh log"])
def test_j2_opsi_global_sesudah_no_pager_ditolak(repo, cmd):
    assert denied(hook(repo, cmd=cmd)), cmd


@pytest.mark.regression("J2")
def test_j2_no_pager_polos_tetap_lolos(repo):
    assert hook(repo, cmd="git --no-pager show HEAD --stat").returncode == 0


# --- J3: `symbolic-ref` bentuk baca saja --------------------------------------------------------

SYMREF_WRITE = ["git symbolic-ref HEAD refs/heads/evil", "git symbolic-ref --delete refs/remotes/origin/HEAD",
                "git symbolic-ref --del HEAD", "git symbolic-ref -d HEAD", "git symbolic-ref -qd HEAD",
                "git symbolic-ref -m x HEAD refs/heads/y", "git symbolic-ref -- HEAD refs/heads/y"]
SYMREF_READ = ["git symbolic-ref HEAD", "git symbolic-ref -q --short HEAD",
               "git symbolic-ref --short refs/remotes/origin/HEAD"]


@pytest.mark.regression("J3")
@pytest.mark.parametrize("cmd", SYMREF_WRITE)
def test_j3_symbolic_ref_tulis_ditolak(repo, cmd):
    assert denied(hook(repo, cmd=cmd)), cmd


@pytest.mark.regression("J3")
@pytest.mark.parametrize("cmd", SYMREF_READ)
def test_j3_symbolic_ref_baca_lolos(repo, cmd):
    assert hook(repo, cmd=cmd).returncode == 0, cmd


# --- J4: penulis fe tidak menulis ke tempat yang tak terlihat git --------------------------------

@pytest.mark.regression("J4")
@pytest.mark.parametrize("tool, path, code", [
    ("Write", ".git/hooks/pre-commit", 2),
    ("Edit", ".git/config", 2),
    ("Write", ".env.local", 2),                          # ter-ignore
    ("Write", "src/.explore/inject.ts", 2),              # ter-ignore oleh pola `.explore/` lama
    ("Write", "/tmp/j4-luar-repo.ts", 2),
    ("Write", "src/../../luar.ts", 2),
    ("Edit", "src/a.ts", 0),
    ("Write", "src/b.ts", 0),
    ("Write", f"{TDIR}/report-01.md", 0),
    ("Edit", f"{TDIR}/brief-01-x.md", 0),
])
def test_j4_implementor_git_dir_dan_ignored_ditolak(repo, tool, path, code):
    assert hook(repo, tool=tool, file_path=path, agent=IMPL).returncode == code, (tool, path)


@pytest.mark.regression("24 K13")
@pytest.mark.parametrize("tool, path, code", [
    ("Write", f"{TDIR}/report-01.md", 0),                # laporan unit: satu-satunya keluaran implementor di taskdir
    ("Edit", f"{TDIR}/report-12.md", 0),
    ("Edit", f"{TDIR}/brief-01-x.md", 2),                # status brief milik architect
    ("Write", f"{TDIR}/FLOW.md", 2),
    ("Write", f"{TDIR}/report-01.md.bak", 2),
    ("Write", f"{TDIR}/sub/report-01.md", 2),
    ("Write", ".env.local", 2),
])
def test_24_k13_implementor_di_taskdir_ter_ignore(repo, tool, path, code):
    write_files(repo, {"frontenddev/docs/.gitignore": "*\n"})
    assert hook(repo, tool=tool, file_path=path, agent=IMPL).returncode == code, (tool, path)


@pytest.mark.regression("J4")
@pytest.mark.parametrize("path, code", [
    (f"{TDIR}/.explore/gate-cart.md", 0),
    (".frontenddev/explore/2609260000-cart.md", 0),
    ("src/a.ts", 2),
    (f"{TDIR}/TASK.md", 2),
    (f"{TDIR}/.explore/../TASK.md", 2),
    ("src/.explore/q.md", 2),
    (".git/hooks/post-checkout", 2),
])
def test_j4_explorer_hanya_laci(repo, path, code):
    assert hook(repo, tool="Write", file_path=path, agent=EXPLORER).returncode == code, path


@pytest.mark.regression("J4")
def test_j4_explorer_symlink_laci_ke_src_ditolak(repo):
    (repo / TDIR / ".explore").mkdir()
    os.symlink("../../../../src/a.ts", repo / TDIR / ".explore" / "lnk.md")
    assert denied(hook(repo, tool="Write", file_path=f"{TDIR}/.explore/lnk.md", agent=EXPLORER))


@pytest.mark.regression("J4")
@pytest.mark.parametrize("path, code", [(f"{TDIR}/REVIEW-PLAN.md", 0), (f"{TDIR}/REVIEW.md", 2),
                                        (f"{TDIR}/brief-01-x.md", 2), ("src/a.ts", 2)])
def test_j4_doc_reviewer_hanya_review_plan(repo, path, code):
    assert hook(repo, tool="Write", file_path=path, agent=DOC_REVIEWER).returncode == code, path


@pytest.mark.regression("J4")
def test_j4_penulis_tanpa_repo_git_fail_closed(tmp_path):
    assert denied(hook(tmp_path, tool="Write", file_path="x.md", agent=EXPLORER))


@pytest.mark.regression("J4")
def test_j4_strip_scratch_berjangkar():
    lib = load_module(FE_SKILLS / "_common/precondition_lib.py", "fe_precondition_lib_j4")
    status = "\n".join(["?? src/.explore/inject.ts", " M src/.frontenddev/x.ts",
                        f"?? {TDIR}/.explore/", "?? frontenddev/docs/.explore/a.md", "?? .frontenddev/",
                        " M src/a.ts"])
    kept = lib.strip_explore_scratch(status).splitlines()
    assert kept == ["?? src/.explore/inject.ts", " M src/.frontenddev/x.ts", " M src/a.ts"]


EXPLORER_DISPATCHERS = sorted((PLUGINS / "frontend/skills").glob("*/dispatcher/explorer.md"))
ANCHORED = ("/.frontenddev/", "frontenddev/docs/**/.explore/")


@pytest.mark.regression("J4")
@pytest.mark.parametrize("path", [PLUGINS / "frontend/skills/profile/SKILL.md", *EXPLORER_DISPATCHERS],
                         ids=lambda p: p.parent.parent.name if p.name == "explorer.md" else "profile")
def test_j4_pola_ignore_berjangkar_di_prosa(path):
    text = path.read_text(encoding="utf-8")
    assert all(f"`{pat}`" in text for pat in ANCHORED), path
    assert "baris `.frontenddev/` dan `.explore/`" not in text, path


def test_j4_lima_dispatcher_explorer():
    assert len(EXPLORER_DISPATCHERS) == 5


# --- J5: `detect.py` tidak crash pada workspace `.`/kosong atau manifest tak terbaca --------------

@pytest.mark.regression("J5")
@pytest.mark.parametrize("plugin, sub, manifest", [("frontenddev", "apps/web", REACT_VITE),
                                                   ("backenddev", "apps/api", EXPRESS)])
@pytest.mark.parametrize("workspaces", [[".", "apps/*"], ["", "apps/*"], ["./"]])
def test_j5_workspace_titik_tidak_crash(make_repo, plugin, sub, manifest, workspaces):
    root = make_repo({"package.json": json.dumps({"private": True, "workspaces": workspaces}),
                      f"{sub}/package.json": manifest})
    proc, payload = run_hook(plugin, root)
    assert proc.returncode == 0 and "detect.py:" not in proc.stderr, proc.stderr
    assert payload is not None and payload["hookSpecificOutput"]["additionalContext"]


@pytest.mark.regression("J5")
@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root membaca berkas mode 000")
@pytest.mark.parametrize("name", ["pnpm-workspace.yaml", "go.work"])
def test_j5_manifest_workspace_tak_terbaca(make_repo, name):
    root = make_repo({"apps/web/package.json": REACT_VITE, name: "packages:\n  - 'apps/*'\n"})
    (root / name).chmod(0)
    try:
        proc, payload = run_hook("frontenddev", root)
    finally:
        (root / name).chmod(0o644)
    assert "detect.py:" not in proc.stderr and payload is not None, proc.stderr


@pytest.mark.regression("J5")
def test_j5_prasyarat_profile_workspace_titik(make_repo):
    root = make_repo({"package.json": json.dumps({"workspaces": ["."]}), "apps/web/package.json": REACT_VITE})
    commit(root, "init")
    r = fe_run(root, "profile/scripts/check_preconditions.py", "--json")
    assert "Traceback" not in r.out, r.out
    assert json.loads(r.stdout)


# --- J6: TREE hanya meloloskan `finding_source` taskdir ini --------------------------------------

REVIEW = f"{TD}/REVIEW.md"
AUDIT = "frontenddev/reviews/2609250000-audit.md"


def _validate_tree(repo):
    rel = f"{TD}/.explore/closing-verification.json"
    write_files(repo, {rel: json.dumps([{"cmd": "test", "status": "HIJAU", "new_errors": 0,
                                         "baseline_status": "HIJAU"}])})
    r = fe_run(repo, "architect/scripts/validate_review.py", "--taskdir", TD, "--json", "--log", rel)
    return next(c for c in json.loads(r.stdout)["checks"] if c["id"] == "TREE")


@pytest.mark.regression("J6")
def test_j6_tree_berkas_temuan_lain_fail(fe_minor_chain):
    (fe_minor_chain / TD / "REPORT.md").unlink()
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain),
                                 "frontenddev/reviews/2609260000-lain.md": "> Status: FIXED\n"})
    c = _validate_tree(fe_minor_chain)
    assert c["status"] == "FAIL" and any("2609260000-lain.md" in d for d in c["details"]), c


@pytest.mark.regression("J6")
def test_j6_tree_finding_source_taskdir_ini_lolos(fe_minor_chain):
    (fe_minor_chain / TD / "REPORT.md").unlink()
    task = fe_minor_chain / TD / "TASK.md"
    task.write_text(task.read_text(encoding="utf-8").replace(
        "status: ACTIVE\n", f"status: ACTIVE\nfinding_source: {AUDIT}\n", 1), encoding="utf-8")
    write_files(fe_minor_chain, {AUDIT: "### [P2-1] x\n\n> Status: PLANNED\n"})
    commit(fe_minor_chain, "docs(order-checkout): finding_source", AUDIT)
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain),
                                 AUDIT: "### [P2-1] x\n\n> Status: FIXED\n"})
    c = _validate_tree(fe_minor_chain)
    assert c["status"] == "PASS", c


# --- J7: `chain.py files` hanya milik plugin ini -------------------------------------------------

@pytest.mark.regression("J7")
@pytest.mark.parametrize("cmd, code", [
    ("python3 /tmp/evil/skills/_common/chain.py files", 2),
    (f"python3 {CHAIN.parent}/../_common/chain.py files --taskdir {TDIR}", 0),
    (f"python3 {CHAIN} files --taskdir {TDIR}", 0),
    (f"python3 {CHAIN} approve --taskdir {TDIR}", 2),
])
def test_j7_chain_py_asing_ditolak(repo, cmd, code):
    assert hook(repo, cmd=cmd).returncode == code, cmd


# --- J8: glob tanpa kutip sebelum `--` ------------------------------------------------------------

@pytest.mark.regression("J8")
@pytest.mark.parametrize("cmd, code", [
    ("git diff HEAD *", 2),
    ("git show HEAD:src/routes/[id]/x.svelte", 2),
    ("git log -S a?b", 2),
    ("git diff HEAD -- *.ts", 0),
    ("git show 'HEAD:src/routes/[id]/x.svelte'", 0),
    ('git log -S "a*b" --oneline', 0),
    (r"git log -S a\*b", 0),
])
def test_j8_glob_sebelum_dashdash_ditolak(repo, cmd, code):
    assert hook(repo, cmd=cmd).returncode == code, cmd


@pytest.mark.regression("J8")
@pytest.mark.parametrize("func", ["unquoted_glob", "shell_tokens", "symbolic_ref_readonly"])
def test_j8_helper_pagar_identik_be_fe(func):
    def src(plugin):
        text = (PLUGINS / plugin / "hooks/guard_bash.py").read_text(encoding="utf-8")
        m = re.search(rf"^def {func}\(.*?(?=^\S)", text, re.M | re.S)
        assert m, (plugin, func)
        return m.group(0)
    assert src("backend") == src("frontend")


# --- J9: opt-out berkoma dan `plugin` asing di profil sendiri ------------------------------------

@pytest.mark.regression("J9")
@pytest.mark.parametrize("content", ["frontend,quickdev", "frontend, quickdev", "quickdev,frontend\n"])
def test_j9_opt_out_koma(make_repo, content):
    root = make_repo({"package.json": REACT_VITE, "apps/api/package.json": EXPRESS, ".claude/workflow": content})
    assert run_hook("frontenddev", root)[1] is not None
    assert run_hook("backenddev", root)[1] is None


@pytest.mark.regression("J9")
@pytest.mark.parametrize("plugin, gate", [("frontenddev", "lane PROFILE"), ("backenddev", "backend:profile")])
@pytest.mark.parametrize("value", [["x"], "zzz"])
def test_j9_plugin_asing_di_profil_sendiri_refresh(make_repo, plugin, gate, value):
    stack = "react-vite" if plugin == "frontenddev" else "node"
    root = make_repo({f".claude/profile/{plugin}/index.json": json.dumps({"plugin": value, "stack": stack})})
    proc, payload = run_hook(plugin, root)
    assert payload is not None, proc.stderr
    text = payload["hookSpecificOutput"]["additionalContext"]
    assert "REFRESH" in text and gate in text
    assert "GENERATE" not in text and "berisi profil milik" not in text, text


@pytest.mark.regression("J9")
def test_j9_profil_salah_tempat_plugin_dikenal_tetap_diabaikan(make_repo):
    """A6 (issue 01) tetap: `.claude/profile/backenddev/` ber-`plugin: frontenddev` diabaikan hook backend."""
    root = make_repo({".claude/profile/backenddev/index.json": json.dumps({"plugin": "frontenddev", "stack": "node"})})
    assert run_hook("backenddev", root)[1] is None
