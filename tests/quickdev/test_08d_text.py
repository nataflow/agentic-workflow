"""Regresi teks 08d — SKILL dan template quickdev menagih kunci rencana, base, dan batas yang disepakati."""
import re
import subprocess

import pytest

from conftest import GIT_ENV, PLUGINS, commit, git

QD = PLUGINS / "quickdev"
SK = QD / "skills"
TPL = SK / "profile" / "references"
TEMPLATES = ["backend", "frontend", "fullstack"]
BASELINE_HEAD = "| Jenis | Perintah | Cwd | Status | Durasi | Known issues (baseline) |"


def skill(name):
    return (SK / name / "SKILL.md").read_text(encoding="utf-8")


def test_d1_approved_hanya_lewat_plan_lock():
    plan = skill("plan")
    assert "plan_lock.py lock --plan" in plan and "dilarang menulis `Status: APPROVED` dengan tangan" in plan
    assert "plan_lock.py unlock" in plan
    for name in ("execute", "review"):
        assert "plan_lock.py verify --plan" in skill(name)
    assert "plan_lock.py close --plan" in skill("execute")


def test_d2_review_membandingkan_base_bukan_head():
    review = skill("review")
    assert "git diff HEAD" not in review.split("## STYLE")[0]
    assert "git diff <BASE>" in review and "`base_ref`" in review
    execute = skill("execute")
    assert "mode `resume`" in execute and "Dilarang meminta user meng-commit atau men-stash kerja parsial" in execute


def test_d3_remediasi_berplafon_dan_ditanyakan():
    review = skill("review")
    fase5 = review.split("### Fase 5", 1)[1].split("## Guardrails", 1)[0]
    assert "AskUserQuestion" in fase5 and "/2" in fase5 and "sudah 2" in fase5
    assert "--findings --findings-text" in skill("execute")


@pytest.mark.parametrize("kind", TEMPLATES)
def test_d4_d6_template_baseline_tabel_dan_workspace(kind):
    text = (TPL / f"{kind}-profile-template.md").read_text(encoding="utf-8")
    assert BASELINE_HEAD in text
    assert "- **Workspace**:" in text
    assert "`TIDAK_ADA`" in text
    assert len(re.findall(r"^## \d\. ", text, re.M)) == 6


def test_d5_perbaikan_verifikasi_terbatas_section3():
    execute = skill("execute")
    assert "PERBAIKAN GALAT VERIFIKASI TUNDUK PADA BATAS YANG SAMA" in execute
    assert "(di luar rencana)" in execute and "di luar rencana: <daftar berkas>" in execute


def test_d6_profil_dari_metadata_rencana():
    for name in ("execute", "review"):
        assert "default: nilai `Profile:` di metadata `plan_path`" in skill(name)
    for name in ("explore", "clarify", "plan"):
        assert "lebih dari satu profil" in skill(name)


def test_d7_gates_dan_failure_path_plan():
    plan = skill("plan")
    assert "`Gates: explore=" in plan and "5. **Explore/clarify tidak ada di percakapan**" in plan
    assert "plan_lock.py confirm" in skill("execute")


def test_d9_failure_path_review_menunjuk_base_ref():
    fp = skill("review").split("## Failure path", 1)[1]
    assert "base_ref=<Base-Commit>" in fp


def test_d10_clarify_tanpa_kontradiksi():
    clarify = skill("clarify")
    assert "KECUALI `skip_if_clear: false`" in clarify
    assert "simpan status draf" not in clarify and "CLARIFY — TERTAHAN" in clarify
    assert "maksimal 3 batch per pemanggilan" in clarify
    assert "maksimal satu kali per tugas" in clarify and "maksimal satu kali per tugas" in skill("plan")


def test_d11_fullstack_punya_sumber():
    profile = skill("profile")
    assert "references/fullstack-profile-template.md" in profile
    assert "<backend | frontend | fullstack>" in profile
    assert "- **Server-side Route Pattern**:" in (TPL / "fullstack-profile-template.md").read_text(encoding="utf-8")
    assert "Cabang Dinamis C — Fullstack**: dipakai bila" in skill("clarify")


def test_d12_repo_tanpa_runner_test():
    assert "`TIDAK_ADA`" in skill("profile")
    assert "baris Test Section 5 profil berstatus `TIDAK_ADA`" in skill("plan")
    assert "MUST NOT memasang framework/dependensi test" in skill("execute")


def test_d13_explore_fallback_bash_dan_skala():
    explore = skill("explore")
    assert "git ls-files | grep -i" in explore and "Jalankan `Glob`" not in explore
    assert "SKALA: kecil | standar" in explore


def _sh(repo, script):
    env = {"PATH": "/usr/bin:/bin", **GIT_ENV}
    return subprocess.run(["bash", "-c", script], cwd=repo, capture_output=True, text=True, env=env)


def test_d8_predikat_git_baru(make_repo):
    """Tiga kasus Reproduksi D8 dengan perintah persis dari SKILL baru."""
    root = make_repo({"app.js": "x\n", "repo-profile.md": "# profil\n"})
    commit(root, "init")
    (root / "plan").mkdir()
    (root / "plan" / "t.md").write_text("Status: APPROVED\n", encoding="utf-8")
    (root / "plan" / "lama.md").write_text("Status: APPROVED\n", encoding="utf-8")
    exclude = "grep -v -e '^plan/' -e '^repo-profile.md$'"
    awal = _sh(root, f"git status --porcelain -uall | cut -c4- | {exclude}")
    assert awal.stdout == ""                                   # kasus 1 & 2: tree bersih
    (root / "app.js").write_text("x\ny\n", encoding="utf-8")
    base = git(root, "rev-parse", "HEAD").strip()
    review = _sh(root, f"{{ git diff {base} --name-only; git ls-files --others --exclude-standard; }} | {exclude}")
    assert review.stdout.split() == ["app.js"]

    empty = make_repo({"a.js": "a\n"}, name="kosong")
    git(empty, "add", "a.js")
    r = _sh(empty, 'git diff "$(git hash-object -t tree /dev/null)" --name-only')
    assert r.returncode == 0 and r.stdout.split() == ["a.js"]  # kasus 3: tanpa fatal
