"""Regresi teks 08d — SKILL dan template quickdev menagih kunci rencana, base, dan batas yang disepakati."""
import re
import subprocess

import pytest

from conftest import GIT_ENV, PLUGINS, commit, git

QD = PLUGINS / "quickdev"
SK = QD / "skills"


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


@pytest.mark.regression("34 P2")
def test_d4_section4_tabel_perintah_verifikasi():
    plan = skill("plan")
    assert "| Jenis | Perintah | Cwd | Risiko |" in plan and "`TIDAK_ADA`, bukan dikarang" in plan
    assert "`target_dir`" in plan


def test_d5_perbaikan_verifikasi_terbatas_section3():
    execute = skill("execute")
    assert "PERBAIKAN GALAT VERIFIKASI TUNDUK PADA BATAS YANG SAMA" in execute
    assert "(di luar rencana)" in execute and "di luar rencana: <daftar berkas>" in execute


@pytest.mark.regression("34 D1")
def test_d6_tanpa_profil_dan_skill_terhapus():
    for name in ("plan", "execute", "review"):
        text = skill(name)
        assert "repo-profile.md" not in text and "profile_path" not in text, name
        assert not re.search(r"quickdev:(profile|explore|clarify)", text), name
    assert not re.search(r"quickdev:(profile|explore|clarify)|repo-profile",
                         (SK / "plan" / "references" / "nataflow-sync.md").read_text(encoding="utf-8"))


@pytest.mark.regression("34 P1")
def test_d7_plan_menyerap_telusur_dan_klarifikasi():
    plan = skill("plan")
    assert "### Fase 1 — Telusur Kode" in plan and "### Fase 2 — Klarifikasi" in plan
    assert "Gates:" not in plan
    assert "plan_lock.py confirm" in skill("execute")


def test_d9_failure_path_review_menunjuk_base_ref():
    fp = skill("review").split("## Failure path", 1)[1]
    assert "base_ref=<Base-Commit>" in fp


def test_d10_klarifikasi_berbatas():
    fase2 = skill("plan").split("### Fase 2", 1)[1].split("### Fase 3", 1)[0]
    assert "**Fast-path**" in fase2 and "**2 batch**" in fase2 and "(Recommended)" in fase2
    assert "*Lanjut dengan asumsi tertulis di Section 1*" in fase2
    assert "PLAN — TERTAHAN" in skill("plan")


def test_d11_fullstack_punya_sumber():
    plan = skill("plan")
    assert "`fullstack` (dependensi frontend **dan** minimal satu berkas route server nyata" in plan
    assert "**fullstack**: gabungan keduanya" in plan


def test_d12_repo_tanpa_runner_test():
    plan = skill("plan")
    assert "baris Test Section 4 bernilai `TIDAK_ADA`" in plan
    assert "Tests: repo tanpa test runner" in plan
    assert "MUST NOT memasang framework/dependensi test" in skill("execute")


def test_d13_telusur_fallback_bash_dan_skala():
    plan = skill("plan")
    assert "git ls-files | grep -i" in plan and "Jalankan `Glob`" not in plan
    assert "**kecil**: ≤2 berkas" in plan and "**standar**" in plan


def _sh(repo, script):
    env = {"PATH": "/usr/bin:/bin", **GIT_ENV}
    return subprocess.run(["bash", "-c", script], cwd=repo, capture_output=True, text=True, env=env)


def test_d8_predikat_git_baru(make_repo):
    """Tiga kasus Reproduksi D8 dengan perintah persis dari SKILL baru."""
    root = make_repo({"app.js": "x\n"})
    commit(root, "init")
    (root / "plan").mkdir()
    (root / "plan" / "t.md").write_text("Status: APPROVED\n", encoding="utf-8")
    (root / "plan" / "lama.md").write_text("Status: APPROVED\n", encoding="utf-8")
    exclude = "grep -v -e '^plan/'"
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


def _section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


@pytest.mark.regression("34 P3")
def test_p3_telusur_menagih_kemampuan_existing_dan_akar_masalah():
    fase1 = _section(skill("plan"), "### Fase 1", "### Fase 2")
    assert "cari kemampuan serupa yang sudah ada" in fase1
    assert "**akar masalah**" in fase1 and "akar belum terbukti → catat sebagai celah Fase 2" in fase1


@pytest.mark.regression("34 P4")
def test_p4_section1_ac_dan_alternatif():
    fase3 = _section(skill("plan"), "### Fase 3", "### Fase 4")
    assert "acceptance criteria bernomor `AC-<n>`" in fase3
    assert "`Alternatif ditolak: <pendekatan> — <alasan>`" in fase3


@pytest.mark.regression("34 P5")
def test_p5_section2_risiko_non_fungsional():
    fase3 = _section(skill("plan"), "### Fase 3", "### Fase 4")
    for risiko in ("Kompatibilitas mundur", "Data existing", "Konkurensi", "Keamanan", "Performa"):
        assert f"`{risiko}`" in fase3, risiko


@pytest.mark.regression("34 P6")
def test_p6_section4_skenario_dipetakan_ke_ac():
    fase3 = _section(skill("plan"), "### Fase 3", "### Fase 4")
    assert "happy path, error/validasi, batas nilai, dan edge case" in fase3
    assert "setiap `AC-<n>` punya minimal satu skenario atau langkah QA manual" in fase3


@pytest.mark.regression("34 P7")
def test_p7_ringkasan_gerbang_menunjuk_rencana():
    plan = skill("plan")
    fase4 = _section(plan, "### Fase 4", "### Fase 5")
    assert "Baca rencana lengkap sebelum menyetujui:" in fase4 and "alternatif yang ditolak" in fase4
    assert "LANGKAH: <n> langkah atomik, <n> berkas target, <n> AC" in plan


@pytest.mark.regression("34 E2")
def test_e2_execute_skenario_selaras_section4():
    assert "(happy path, error/validasi, batas nilai, edge case)" in skill("execute")


@pytest.mark.regression("34 R2")
def test_r2_review_menagih_ac():
    review = skill("review")
    fase2 = _section(review, "### Fase 2", "### Fase 3")
    assert "acceptance criteria `AC-<n>` Section 1 bila rencana memuatnya" in fase2
    assert "`AC-<n>` rencana tanpa skenario test atau langkah QA" in review
