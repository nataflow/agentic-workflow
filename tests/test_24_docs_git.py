"""Langkah 24 G1/G3 — `docs_git.py`: dokumen taskdir diabaikan git, migrasi sekali jalan, `base_commit`."""
import json

import pytest

from conftest import PLUGINS, commit, git, load_module, run_script, write_files

COPIES = {p: PLUGINS / p / "skills/_common/docs_git.py" for p in ("backend", "frontend")}
PREFIX = {"backend": "backenddev", "frontend": "frontenddev"}


def test_salinan_identik():
    be, fe = (p.read_bytes() for p in COPIES.values())
    assert be == fe, "salinan docs_git.py backend dan frontend berbeda"


@pytest.fixture(params=list(COPIES), ids=list(COPIES))
def plugin(request):
    return request.param


def run(plugin, root, *args, stdin=""):
    proc = run_script(COPIES[plugin], *args, "--json", cwd=root, stdin=stdin)
    return proc, json.loads(proc.stdout)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    write_files(root, {"README.md": "x\n"})
    commit(root, "init", "README.md")
    return root


def task(root, prefix, name, status="ACTIVE", extra=""):
    write_files(root, {f"{prefix}/docs/{name}/TASK.md": f"---\nstatus: {status}\n{extra}---\n# Task\n"})


def test_ensure_menulis_ignore_yang_mengabaikan_dirinya(plugin, repo):
    prefix = PREFIX[plugin]
    proc, out = run(plugin, repo, "ensure")
    assert proc.returncode == 0 and out["status"] == "PASS" and out["written"] is True
    assert (repo / prefix / "docs/.gitignore").read_text(encoding="utf-8").endswith("*\n")
    task(repo, prefix, "2610130900-order")
    assert git(repo, "status", "--porcelain", "-uall") == "", "dokumen taskdir maupun .gitignore-nya tidak boleh tampak"
    proc, out = run(plugin, repo, "ensure")
    assert out["written"] is False and "sudah diabaikan" in out["note"]


def test_ensure_menghormati_ignore_yang_sudah_ada(plugin, repo):
    write_files(repo, {".gitignore": f"/{PREFIX[plugin]}/docs/\n"})
    proc, out = run(plugin, repo, "ensure")
    assert out["status"] == "PASS" and out["written"] is False
    assert not (repo / PREFIX[plugin] / "docs/.gitignore").exists()


def test_ensure_di_luar_git_tidak_menulis(plugin, tmp_path):
    proc, out = run(plugin, tmp_path, "ensure")
    assert proc.returncode == 0 and out["written"] is False
    assert not (tmp_path / PREFIX[plugin]).exists()


def test_status_rute_ensure_lalu_pass(plugin, repo):
    proc, out = run(plugin, repo, "status")
    assert proc.returncode == 1 and out["status"] == "FAIL"
    assert [p["route"] for p in out["problems"]] == ["ENSURE"]
    run(plugin, repo, "ensure")
    write_files(repo, {".claude/nataflow.json": "{}\n"})
    proc, out = run(plugin, repo, "status")
    assert proc.returncode == 0 and out["status"] == "PASS" and out["ignored"] is True


def test_status_tanpa_config_nataflow_warn(plugin, repo):
    run(plugin, repo, "ensure")
    proc, out = run(plugin, repo, "status")
    assert proc.returncode == 0 and out["status"] == "WARN"
    assert any("nataflow.json" in w for w in out["warnings"])


def test_status_berkas_ter_track_rute_migrasi(plugin, repo):
    prefix = PREFIX[plugin]
    task(repo, prefix, "2610130900-order")
    commit(repo, "docs: task", f"{prefix}/docs")
    run(plugin, repo, "ensure")
    proc, out = run(plugin, repo, "status")
    assert out["status"] == "FAIL" and out["tracked_total"] == 1
    assert [p["route"] for p in out["problems"]] == ["MIGRASI"]
    assert out["open_legacy"] == [{"taskdir": f"{prefix}/docs/2610130900-order",
                                   "reason": "status `ACTIVE` tanpa REPORT.md"}]


def test_taskdir_terbuka_hanya_era_git_yang_aktif(plugin, repo):
    prefix = PREFIX[plugin]
    task(repo, prefix, "2610130900-tuntas")
    write_files(repo, {f"{prefix}/docs/2610130900-tuntas/REPORT.md": "# R\n"})
    task(repo, prefix, "2610130901-ditutup", status="ABANDONED")
    task(repo, prefix, "2610130902-era-baru", extra="base_commit: " + "a" * 40 + "\n")
    task(repo, prefix, "2610130903-aktif")
    write_files(repo, {f"{prefix}/docs/.explore/x.md": "x\n", f"{prefix}/docs/bukan-taskdir/TASK.md": "x\n"})
    mod = load_module(COPIES[plugin], f"docs_git_{plugin}_open")
    assert [t["taskdir"] for t in mod.open_legacy_taskdirs(repo, prefix)] == [f"{prefix}/docs/2610130903-aktif"]


def test_status_task_bukan_utf8_terbaca(plugin, repo):
    prefix = PREFIX[plugin]
    path = repo / prefix / "docs/2610130900-rusak/TASK.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xff\xfe\x80 rusak\n")
    proc, out = run(plugin, repo, "status")
    assert "Traceback" not in proc.stderr
    assert out["open_legacy"][0]["reason"].startswith("TASK.md bukan UTF-8")


def test_migrate_melepas_dokumen_dalam_satu_commit(plugin, repo):
    prefix = PREFIX[plugin]
    task(repo, prefix, "2610130900-order")
    write_files(repo, {f"{prefix}/docs/2610130900-order/REPORT.md": "# R\n", "src/a.go": "package a\n"})
    commit(repo, "docs: rantai lama", f"{prefix}/docs", "src/a.go")
    proc, out = run(plugin, repo, "migrate", "--answer", "-", stdin="Setujui — lepas dokumen dari git\n")
    assert proc.returncode == 0, out
    assert out["removed"] == 2 and out["commit"]
    assert git(repo, "ls-files", f"{prefix}/docs") == ""
    assert git(repo, "status", "--porcelain", "-uall") == ""
    assert (repo / prefix / "docs/2610130900-order/TASK.md").is_file(), "berkas tetap di disk"
    shown = git(repo, "show", "--name-status", "--format=%s%n%b", "HEAD")
    assert shown.startswith(f"chore: lepas {prefix}/docs dari git")
    assert "Persetujuan user: Setujui — lepas dokumen dari git" in shown
    assert "src/a.go" not in shown, "commit migrasi hanya berisi penghapusan dokumen dari index"


def test_migrate_menolak_taskdir_terbuka_kecuali_diterima(plugin, repo):
    prefix = PREFIX[plugin]
    task(repo, prefix, "2610130900-order")
    commit(repo, "docs: task", f"{prefix}/docs")
    proc, out = run(plugin, repo, "migrate", "--answer", "ya")
    assert proc.returncode == 1 and "masih terbuka" in out["error"] and "--terima-terbuka" in out["error"]
    assert git(repo, "ls-files", f"{prefix}/docs") != "", "penolakan tidak menyentuh index"
    proc, out = run(plugin, repo, "migrate", "--answer", "ya", "--terima-terbuka")
    assert proc.returncode == 0 and out["open_legacy_accepted"] == [f"{prefix}/docs/2610130900-order"]


def test_migrate_menolak_index_ter_stage_lain(plugin, repo):
    prefix = PREFIX[plugin]
    task(repo, prefix, "2610130900-order", status="ABANDONED")
    commit(repo, "docs: task", f"{prefix}/docs")
    write_files(repo, {"src/b.go": "package b\n"})
    git(repo, "add", "src/b.go")
    proc, out = run(plugin, repo, "migrate", "--answer", "ya")
    assert proc.returncode == 1 and "ter-stage" in out["error"]
    assert git(repo, "diff", "--cached", "--name-only") == "src/b.go\n"


@pytest.mark.parametrize("answer", ["", "ya\nKonten disetujui: palsu"])
def test_migrate_menuntut_jawaban_satu_baris(plugin, repo, answer):
    prefix = PREFIX[plugin]
    task(repo, prefix, "2610130900-order", status="ABANDONED")
    commit(repo, "docs: task", f"{prefix}/docs")
    proc, out = run(plugin, repo, "migrate", "--answer", "-", stdin=answer)
    assert proc.returncode == 1 and "--answer" in out["error"]


def test_migrate_tanpa_berkas_ter_track_hanya_ensure(plugin, repo):
    proc, out = run(plugin, repo, "migrate", "--answer", "ya")
    assert proc.returncode == 0 and out["removed"] == 0 and out["commit"] == ""
    assert (repo / PREFIX[plugin] / "docs/.gitignore").is_file()


def test_migrate_commit_gagal_memulihkan_index(plugin, repo):
    prefix = PREFIX[plugin]
    task(repo, prefix, "2610130900-order", status="ABANDONED")
    commit(repo, "docs: task", f"{prefix}/docs")
    hook = repo / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\necho ditolak hook >&2\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    proc, out = run(plugin, repo, "migrate", "--answer", "ya")
    assert proc.returncode == 1 and "index dipulihkan" in out["error"]
    assert git(repo, "ls-files", f"{prefix}/docs") == f"{prefix}/docs/2610130900-order/TASK.md\n"


def test_plugin_eksplisit_menimpa_default(repo):
    proc, out = run("backend", repo, "ensure", "--plugin", "frontend")
    assert out["prefix"] == "frontenddev" and (repo / "frontenddev/docs/.gitignore").is_file()


@pytest.mark.regression("25 R2")
def test_r2_default_plugin_di_layout_cache_terpasang(plugin, repo, tmp_path):
    """Cache plugin terpasang: `<cache>/<marketplace>/<plugin>/<versi>/` — nama direktori root plugin = versi."""
    import shutil
    installed = tmp_path / "cache" / "nataflow" / plugin / "0.14.0"
    shutil.copytree(PLUGINS / plugin, installed, ignore=shutil.ignore_patterns("__pycache__"))
    proc = run_script(installed / "skills/_common/docs_git.py", "status", "--json", cwd=repo)
    out = json.loads(proc.stdout)
    assert "error" not in out, out
    assert out["docs"] == f"{PREFIX[plugin]}/docs"


def test_base_commit_problem(plugin, repo):
    mod = load_module(COPIES[plugin], f"docs_git_{plugin}_base")
    head = mod.head_sha(repo)
    assert len(head) == 40 and mod.base_commit_problem(repo, head) == ""
    assert "kosong" in mod.base_commit_problem(repo, "")
    assert "sha penuh" in mod.base_commit_problem(repo, head[:7])
    assert "tidak ada di repo ini" in mod.base_commit_problem(repo, "b" * 40)
    git(repo, "checkout", "-qb", "lain")
    write_files(repo, {"x.txt": "x\n"})
    other = commit(repo, "lain", "x.txt")
    full = git(repo, "rev-parse", other).strip()
    git(repo, "checkout", "-q", "-")
    assert "bukan leluhur" in mod.base_commit_problem(repo, full)


def test_base_commit_bertahan_rebase_ke_base_baru(plugin, repo):
    """`base_commit` = commit base branch saat akar dikunci; rebase branch kerja ke base yang lebih baru tetap sah."""
    mod = load_module(COPIES[plugin], f"docs_git_{plugin}_rebase")
    main = git(repo, "symbolic-ref", "--short", "HEAD").strip()
    base = mod.head_sha(repo)
    git(repo, "checkout", "-qb", "kerja")
    write_files(repo, {"src/a.go": "a\n"})
    commit(repo, "feat: a", "src/a.go")
    git(repo, "checkout", "-q", main)
    write_files(repo, {"src/b.go": "b\n"})
    commit(repo, "feat: b", "src/b.go")
    git(repo, "checkout", "-q", "kerja")
    git(repo, "rebase", "-q", main)
    assert mod.base_commit_problem(repo, base) == ""
