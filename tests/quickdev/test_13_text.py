"""Regresi teks 13 tahap 3 — SKILL, template, dan README quickdev selaras perilaku `plan_lock.py` baru."""
import re

import pytest

from conftest import PLUGINS

QD = PLUGINS / "quickdev"
SK = QD / "skills"
TPL = SK / "profile" / "references"
SKILLS = ["clarify", "execute", "explore", "plan", "profile", "review"]


def skill(name):
    return (SK / name / "SKILL.md").read_text(encoding="utf-8")


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def test_q2_review_tidak_memanggil_execute():
    fase5 = section(skill("review"), "### Fase 5", "## Guardrails")
    assert "memanggil `quickdev:execute`" not in fase5
    assert "/quickdev:execute" in fase5 and "disable-model-invocation" in fase5
    param = section(skill("execute"), "- `review_findings`", "\n## ")
    assert "laporan `quickdev:review` `CHANGES_REQUIRED` terakhir di percakapan" in param


@pytest.mark.parametrize("name", ["plan", "execute", "review"])
def test_q4_teks_bebas_lewat_heredoc_berkutip(name):
    text = skill(name)
    assert not re.search(r"--(answer|verification|findings-text|reason|summary) \"", text), name
    if name != "review":
        assert "<<'QD_EOF'" in text


def test_q5_execute_meminta_izin_dan_bertimeout():
    execute = skill("execute")
    iron = section(execute, "## THE IRON LAW", "## Precondition")
    assert "MIGRASI" in iron
    fase3 = section(execute, "### Fase 3", "### Fase 4")
    assert "300000" in fase3 and "AskUserQuestion" in fase3
    assert "`SKIPPED` / `TIMEOUT`" not in fase3                   # tidak lagi "jalankan sekarang" tanpa izin


@pytest.mark.parametrize("kind", ["backend", "frontend", "fullstack"])
def test_q6_template_mencatat_baseline_commit(kind):
    text = (TPL / f"{kind}-profile-template.md").read_text(encoding="utf-8")
    assert "Baseline-Commit:" in section(text, "## 5.", "## 6.")


def test_q6_execute_baseline_segar_tanpa_nomor_baris():
    execute = skill("execute")
    assert "plan_lock.py baseline --plan" in execute and "`fresh_baseline`" in execute
    assert "tanpa nomor baris" in section(execute, "### Fase 3", "### Fase 4")
    assert "Baseline-Commit" in skill("profile")


def test_q1_q3_q9_q14_tabel_mode_execute():
    fase0 = section(skill("execute"), "### Fase 0", "### Fase 1")
    for phrase in ("START FAIL", "verifikasi basi", "lanjutan", "Remediation-State", "PERINGATAN"):
        assert phrase in fase0, phrase
    pre = section(skill("review"), "## Precondition", "## Koeksistensi")
    assert "base_drift" in skill("review") and "basi" in pre


def test_q15_stop_on_error_false_terdefinisi():
    param = section(skill("execute"), "- `stop_on_error`", "\n- `")
    assert "`false`" in param and "langkah gagal pertama" in param


@pytest.mark.parametrize("name", ["execute", "review"])
def test_q16_plan_path_punya_fallback(name):
    param = section(skill(name), "- `plan_path`", "\n- `")
    assert "kosong" in param.lower() and "status --json" in param


def test_q17_profile_tanpa_path_detect_plugin_lain():
    assert "hooks/detect.py" not in skill("profile")


@pytest.mark.parametrize("name", SKILLS)
def test_q18_pemisah_workflow_selaras_detect(name):
    assert "dipisah spasi, koma, atau baris" in skill(name)


def test_rilis_readme_dan_versi():
    readme = (QD / "README.md").read_text(encoding="utf-8")
    for phrase in ("Hash-Scope", "Verified-Hash", "Tree-Hash", "Remediation-State", "Baseline-Commit",
                   "plan_lock.py baseline", "<<'QD_EOF'"):
        assert phrase in readme, phrase
    assert '"version": "0.5.0"' in (QD / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
