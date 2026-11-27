"""Review lapangan hkm 2611 — quickdev Q1, Q2, Q4.

- Q1: direktori rencana diabaikan git lewat penanda `<plan_dir>/.gitignore` (`*`) yang ditulis `lock`/`start`.
- Q2: `plan_lock.py commit` meng-commit hasil eksekusi COMPLETED tersegel atas pilihan user di akhir review; `start`
  menandai tree kotor yang seluruhnya hasil rencana lain COMPLETED (`MILIK:`).
- Q4: tipe dokumen yang belum terdaftar dilaporkan dengan instruksi pendaftaran; review mengutip segmen sinkron.
"""
import json

import pytest

from conftest import PLUGINS, commit, git, run_script, write_files
from nataflow_fake import FakeMCP, Nataflow, enable_sync

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
SK = PLUGINS / "quickdev" / "skills"
PLAN = """# Implementation Plan — {name}
Status: DRAFT
Author: quickdev:plan

## 1. Overview & Objectives
Tambah validasi kuota.

## 3. Atomic Implementation Steps
- [ ] 1. Ubah `app.js`: tambah `checkQuota()`

## 4. Verification & Testing Strategy
- `npm test`
"""


def plan_text(name="t"):
    return PLAN.format(name=name)


@pytest.fixture
def repo(make_repo):
    root = make_repo({"app.js": "a\n", "old.js": "lama\n"})
    commit(root, "init")
    write_files(root, {"plan/t.md": plan_text()})
    return root


def pl(repo, *args, stdin=""):
    r = run_script(PL, *args, cwd=repo, stdin=stdin)
    assert "Traceback" not in r.stderr, r.stderr
    return r


def lock(repo, plan="plan/t.md"):
    r = pl(repo, "lock", "--plan", plan, "--answer", "setuju")
    assert r.returncode == 0, r.stdout
    return r


def execute(repo, plan="plan/t.md", files=None):
    """start → kode berubah → checklist → close COMPLETED."""
    r = pl(repo, "start", "--plan", plan)
    assert r.returncode == 0, r.stdout
    if files is None:
        write_files(repo, {"app.js": "a\nfunction checkQuota() {}\n", "src/new.js": "baru\n"})
        (repo / "old.js").unlink()
    else:
        write_files(repo, files)
    p = repo / plan
    p.write_text(p.read_text(encoding="utf-8").replace("- [ ] 1.", "- [x] 1."), encoding="utf-8")
    r = pl(repo, "close", "--plan", plan, "--status", "COMPLETED", "--verification", "test=PASSED")
    assert r.returncode == 0, r.stdout


def commit_code(repo, *extra, plan="plan/t.md", message="feat: validasi kuota (#12)"):
    return pl(repo, "commit", "--plan", plan, "--message", "-", *extra, stdin=message)


def head_files(repo):
    return git(repo, "show", "--name-status", "--format=", "HEAD").split()


# ── Q1 rencana di luar git ────────────────────────────────────────────────────

@pytest.mark.regression("Q1")
def test_lock_menulis_penanda_ignore(repo):
    out = lock(repo).stdout
    assert "INFO: `plan/.gitignore` ditulis" in out and "PERINGATAN: `.claude/nataflow.json` tidak ada" in out
    marker = (repo / "plan" / ".gitignore").read_text(encoding="utf-8")
    assert marker.endswith("\n*\n") and marker.startswith("# ")
    assert git(repo, "status", "--porcelain", "-uall") == "", "rencana dan penandanya tidak muncul di git"
    assert "INFO:" not in lock_again(repo), "idempoten: penanda tidak ditulis ulang"


def lock_again(repo):
    pl(repo, "unlock", "--plan", "plan/t.md", "--reason", "revisi")
    return lock(repo).stdout


@pytest.mark.regression("Q1")
def test_penanda_tidak_ditulis_bila_sudah_diabaikan(repo):
    (repo / ".gitignore").write_text("plan/\n", encoding="utf-8")
    commit(repo, "abaikan plan", ".gitignore")
    out = lock(repo).stdout
    assert "INFO:" not in out and "PERINGATAN" not in out and not (repo / "plan" / ".gitignore").exists()


@pytest.mark.regression("Q1")
def test_penanda_tanpa_peringatan_config_bila_sinkron_aktif(repo):
    write_files(repo, {".claude/nataflow.json": "{}"})
    out = lock(repo).stdout
    assert "INFO: `plan/.gitignore` ditulis" in out and "PERINGATAN" not in out


@pytest.mark.regression("Q1")
def test_rencana_di_root_repo_tidak_mengabaikan_repo(repo):
    write_files(repo, {"t.md": plan_text()})
    out = lock(repo, plan="t.md").stdout
    assert "PERINGATAN: rencana di root repo" in out and not (repo / ".gitignore").exists()


@pytest.mark.regression("Q1")
def test_direktori_berbagi_berkas_lain_tidak_diberi_penanda(repo):
    write_files(repo, {"docs/panduan.md": "# Panduan\n", "docs/t.md": plan_text()})
    commit(repo, "panduan", "docs/panduan.md")
    out = lock(repo, plan="docs/t.md").stdout
    assert "PERINGATAN: `docs/` memuat berkas ter-track selain rencana quickdev (docs/panduan.md)" in out
    assert not (repo / "docs" / ".gitignore").exists()


@pytest.mark.regression("Q1")
def test_rencana_lama_ter_track_tetap_ter_track(repo):
    commit(repo, "rencana lama", "plan/t.md")
    out = lock(repo).stdout
    assert "INFO: `plan/.gitignore` ditulis" in out
    assert git(repo, "ls-files", "plan").split() == ["plan/t.md"]
    assert git(repo, "status", "--porcelain") == " M plan/t.md\n"


@pytest.mark.regression("Q1")
def test_start_menulis_penanda_untuk_rencana_versi_lama(repo):
    lock(repo)
    (repo / "plan" / ".gitignore").unlink()
    r = pl(repo, "start", "--plan", "plan/t.md")
    assert r.returncode == 0 and "START PASS: mode=awal" in r.stdout
    assert "INFO: `plan/.gitignore` ditulis" in r.stdout and (repo / "plan" / ".gitignore").is_file()


@pytest.mark.regression("Q1")
def test_bukan_git_tanpa_penanda(make_repo):
    root = make_repo(git_init=False)
    write_files(root, {"plan/t.md": plan_text()})
    r = lock(root)
    assert r.stdout.count("\n") == 1 and not (root / "plan" / ".gitignore").exists()


# ── Q2 commit hasil eksekusi ──────────────────────────────────────────────────

@pytest.mark.regression("Q2")
def test_commit_hanya_hasil_tersegel(repo):
    lock(repo)
    execute(repo)
    r = commit_code(repo)
    assert r.returncode == 0 and "COMMIT PASS: 3 berkas @" in r.stdout, r.stdout
    assert '· "feat: validasi kuota (#12)"' in r.stdout
    assert head_files(repo) == ["M", "app.js", "D", "old.js", "A", "src/new.js"]
    assert git(repo, "log", "-1", "--format=%s") == "feat: validasi kuota (#12)\n"
    assert git(repo, "status", "--porcelain", "-uall") == ""
    status = json.loads(pl(repo, "status", "--plan", "plan/t.md", "--json").stdout)
    assert status["consistent"] and status["commits_since_base"] == 1, "segel close tetap cocok sesudah commit"
    assert "COMMIT SKIP: hasil eksekusi sudah ter-commit" in commit_code(repo).stdout


@pytest.mark.regression("Q2")
def test_commit_pesan_multibaris_lewat_stdin(repo):
    lock(repo)
    execute(repo)
    assert commit_code(repo, message="fix: kuota `$HOME`\n\nNataflow-Task: #12\n").returncode == 0
    assert git(repo, "log", "-1", "--format=%B").strip() == "fix: kuota `$HOME`\n\nNataflow-Task: #12"


@pytest.mark.regression("Q2")
def test_commit_ditolak_sebelum_completed_atau_segel_basi(repo):
    assert "VERIFY FAIL" in commit_code(repo).stdout, "DRAFT"
    lock(repo)
    r = commit_code(repo)
    assert r.returncode == 1 and "COMMIT FAIL: eksekusi `-` bukan COMPLETED" in r.stdout
    execute(repo)
    assert "COMMIT FAIL: pesan commit kosong" in commit_code(repo, message="  \n").stdout
    write_files(repo, {"lain.txt": "milik user\n"})
    r = commit_code(repo)
    assert r.returncode == 1 and "COMMIT FAIL: blok `COMPLETED` basi" in r.stdout, r.stdout
    assert git(repo, "log", "--format=%s").splitlines() == ["init"]


@pytest.mark.regression("Q2")
def test_commit_branch_baru(repo):
    lock(repo)
    execute(repo)
    base = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    git(repo, "branch", "sudah-ada")
    for name, why in (("sudah-ada", "sudah ada"), ("a..b", "bukan nama branch sah")):
        r = commit_code(repo, "--branch", name)
        assert r.returncode == 1 and why in r.stdout, r.stdout
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() == base
    r = commit_code(repo, "--branch", "feat/kuota")
    assert r.returncode == 0 and "· branch feat/kuota ·" in r.stdout, r.stdout
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() == "feat/kuota"
    assert git(repo, "log", "--format=%s", base).splitlines() == ["init"], "branch asal tidak berubah"


@pytest.mark.regression("Q2")
def test_commit_rencana_ter_track_ikut_commit_kode(repo):
    commit(repo, "rencana lama", "plan/t.md")
    lock(repo)
    execute(repo)
    assert "COMMIT PASS: 4 berkas" in commit_code(repo).stdout
    assert "plan/t.md" in head_files(repo) and "plan/.gitignore" not in head_files(repo)


@pytest.mark.regression("Q2")
def test_commit_gagal_hook_exit_3(repo):
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'error: ditolak hook' >&2\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    lock(repo)
    execute(repo)
    r = commit_code(repo)
    assert r.returncode == 3 and "COMMIT GAGAL: error: ditolak hook" in r.stdout, r.stdout
    assert "git commit -m \"feat: validasi kuota (#12)\" -- app.js old.js src/new.js" in r.stdout
    assert json.loads(pl(repo, "status", "--plan", "plan/t.md", "--json").stdout)["consistent"]


@pytest.mark.regression("Q2")
def test_start_menandai_tree_milik_rencana_lain(repo):
    write_files(repo, {"plan/b.md": plan_text("b")})
    lock(repo)
    lock(repo, plan="plan/b.md")
    execute(repo)
    r = pl(repo, "start", "--plan", "plan/b.md")
    assert r.returncode == 1 and "START FAIL: mode awal menuntut tree bersih" in r.stdout
    assert "MILIK: plan/t.md (COMPLETED) — tawarkan `plan_lock.py commit --plan plan/t.md` lebih dulu" in r.stdout
    assert "## Execution Status" not in (repo / "plan" / "b.md").read_text(encoding="utf-8")
    assert commit_code(repo).returncode == 0
    assert "START PASS: mode=awal" in pl(repo, "start", "--plan", "plan/b.md").stdout


@pytest.mark.regression("Q2")
def test_start_tanpa_milik_bila_ada_kotoran_lain(repo):
    write_files(repo, {"plan/b.md": plan_text("b")})
    lock(repo)
    lock(repo, plan="plan/b.md")
    execute(repo)
    write_files(repo, {"lain.txt": "milik user\n"})            # rencana t basi, lain.txt bukan milik siapa pun
    r = pl(repo, "start", "--plan", "plan/b.md")
    assert r.returncode == 1 and "MILIK:" not in r.stdout


# ── Q4 tipe dokumen dan segmen sinkron ────────────────────────────────────────

@pytest.fixture
def fake():
    with FakeMCP() as f:
        yield f, Nataflow(f)


@pytest.fixture
def sync_repo(make_repo, fake):
    root = make_repo({"app.js": "a\n", "old.js": "lama\n"})
    enable_sync(root, fake[0].url, extra={"repo": "tim/app"})
    commit(root, "init")
    write_files(root, {"plan/t.md": plan_text()})
    return root


def types(f, *codes):
    f.tools["list_document_types"] = lambda _a: [{"id": str(i), "code": c, "name": c, "description": None}
                                                for i, c in enumerate(codes)]


def push(repo):
    r = pl(repo, "sync-payload", "--plan", "plan/t.md", "--push", "--json")
    return r.returncode, json.loads(r.stdout)


@pytest.mark.regression("Q4")
def test_tipe_rencana_belum_terdaftar_gagal_sebelum_tulisan(sync_repo, fake):
    f, nf = fake
    types(f, "quickdev.report")
    lock(sync_repo)
    code, out = push(sync_repo)
    assert code == 1 and out["segment"] == (
        "GAGAL: tipe dokumen `quickdev.plan` belum terdaftar di server nataflow — admin mendaftarkannya di halaman "
        "Document Types (kode `quickdev.plan`), lalu sinkron ulang"), out
    assert f.writes() == [] and nf.tasks == []


@pytest.mark.regression("Q4")
def test_tipe_report_belum_terdaftar_rencana_tetap_tercermin(sync_repo, fake):
    f, nf = fake
    types(f, "quickdev.plan")
    lock(sync_repo)
    execute(sync_repo)
    code, out = push(sync_repo)
    assert code == 0 and out["segment"].endswith(
        "· 1 dokumen (1 baru, 0 diperbarui, 0 sama) · report GAGAL: tipe dokumen `quickdev.report` belum terdaftar "
        "di server nataflow — admin mendaftarkannya di halaman Document Types (kode `quickdev.report`), lalu sinkron "
        "ulang"), out
    assert [d["type"] for d in nf.docs] == ["quickdev.plan"] and nf.tasks[0]["status"] == "done"


@pytest.mark.regression("Q4")
def test_tipe_terdaftar_dan_server_lama(sync_repo, fake):
    f, nf = fake
    lock(sync_repo)
    execute(sync_repo)
    code, out = push(sync_repo)                     # server lama tanpa `list_document_types` → cek dilewati
    assert code == 0 and out["segment"].endswith("· 2 dokumen (2 baru, 0 diperbarui, 0 sama)"), out
    types(f, "quickdev.plan", "quickdev.report")
    code, out = push(sync_repo)
    assert code == 0 and out["segment"].endswith("(0 baru, 0 diperbarui, 2 sama)"), out
    assert [n for n, _ in f.calls].count("list_document_types") == 2


# ── prosa selaras skrip ───────────────────────────────────────────────────────

def skill(name):
    return (SK / name / "SKILL.md").read_text(encoding="utf-8")


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


@pytest.mark.regression("Q1")
def test_plan_tidak_lagi_meng_commit_rencana():
    plan = skill("plan")
    assert "plan_lock.py commit" not in plan and "COMMIT:" not in section(plan, "## Output", "## Failure path")
    assert "`<plan_dir>/.gitignore`" in section(plan, "### Fase 3", "### Fase 4")
    readme = (PLUGINS / "quickdev" / "README.md").read_text(encoding="utf-8")
    assert "Jangan masukkan ke `.gitignore`" not in readme and "plan/.gitignore" in readme
    assert (PLUGINS / "quickdev" / "MIGRATION_v0.14.x_to_v0.15.0.md").is_file()


@pytest.mark.regression("Q2")
def test_review_menawarkan_commit_atas_pilihan_user():
    review = skill("review")
    fase5 = section(review, "### Fase 5", "## Guardrails")
    for opt in ("*Commit di branch aktif (Recommended)*", "*Commit di branch baru*", "*Jangan dulu*"):
        assert opt in fase5, opt
    assert "plan_lock.py commit --plan <plan_path> --message -" in fase5 and "--branch <nama>" in fase5
    assert "*Terima apa adanya*" in fase5
    guard = section(review, "## Guardrails", "## Output")
    assert "`commit`" in guard and "jawaban eksplisit user" in guard
    assert "COMMIT:" in section(review, "## Output", "## Failure path")


@pytest.mark.regression("Q2")
def test_execute_menawarkan_commit_rencana_lain():
    execute_ = skill("execute")
    assert "`MILIK:`" in section(execute_, "### Fase 0", "### Fase 1")
    assert "`MILIK:`" in section(execute_, "## Failure path", "## STYLE")


@pytest.mark.regression("Q4")
def test_segmen_sinkron_dikutip_apa_adanya():
    assert "apa adanya" in section(skill("execute"), "## Output", "## Failure path")
    out = section(skill("review"), "## Output", "## Failure path")
    assert "NATAFLOW: <segmen" in out and "sinkron ulang <plan_path>" in out
    sync = (SK / "plan" / "references" / "nataflow-sync.md").read_text(encoding="utf-8")
    assert "list_document_types" in sync and "Document Types" in sync
