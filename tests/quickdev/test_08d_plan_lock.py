"""Regresi D1/D2/D3/D6/D7/D8 — kunci rencana quickdev (`skills/_common/plan_lock.py`)."""
import json

import pytest

from conftest import PLUGINS, commit, git, run_script

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
PLAN = """# Implementation Plan — t
Status: DRAFT
Author: quickdev:plan
Date: 2026-09-24T10:00:00+07:00

## 1. Overview & Objectives
Tambah validasi kuota.

## 3. Atomic Implementation Steps
- [ ] 1. Ubah `app.js`: tambah `checkQuota()`
- [ ] 2. Ubah `lib.js`: ekspor `QUOTA_MAX`

## 4. Verification & Testing Strategy
- `npm test`
"""


@pytest.fixture
def repo(make_repo):
    root = make_repo({"app.js": "a\n", "lib.js": "b\n", "repo-profile.md": "# profil\n"})
    commit(root, "init")
    (root / "plan").mkdir()
    (root / "plan" / "t.md").write_text(PLAN, encoding="utf-8")
    return root


@pytest.fixture
def pl(repo):
    return lambda *a: run_script(PL, *a, "--plan", "plan/t.md", cwd=repo)


def text(repo):
    return (repo / "plan" / "t.md").read_text(encoding="utf-8")


def edit(repo, old, new):
    p = repo / "plan" / "t.md"
    p.write_text(p.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def tick(repo, *ns):
    for n in ns:
        edit(repo, f"- [ ] {n}.", f"- [x] {n}.")


def test_d1_checkbox_bukan_drift_teks_langkah_drift(repo, pl):
    assert pl("lock", "--answer", "setuju").returncode == 0
    assert 'Approval: "setuju"' in text(repo) and "Plan-Hash: sha256:" in text(repo)
    tick(repo, 1)
    assert pl("verify").returncode == 0
    edit(repo, "tambah `checkQuota()`", "tambah `checkQuota()` dan `logQuota()`")
    r = pl("verify")
    assert r.returncode == 1 and "berubah sesudah APPROVED" in r.stdout


def test_d1_hapus_langkah_terdeteksi(repo, pl):
    pl("lock", "--answer", "ok")
    edit(repo, "- [ ] 2. Ubah `lib.js`: ekspor `QUOTA_MAX`\n", "")
    assert pl("verify").returncode == 1


def test_d1_lock_menolak_jawaban_kosong_dan_non_draft(pl):
    assert pl("lock", "--answer", " ").returncode == 1
    assert pl("lock", "--answer", "ok").returncode == 0
    assert pl("lock", "--answer", "ok").returncode == 1


def test_d1_approved_tangan_tanpa_hash_ditolak(repo, pl):
    edit(repo, "Status: DRAFT", "Status: APPROVED")
    r = pl("verify")
    assert r.returncode == 1 and "tanpa `Plan-Hash`" in r.stdout


def test_d1_unlock_lock_mempertahankan_blok(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1)
    assert pl("unlock", "--reason", "tambah langkah konsumen").returncode == 0
    assert "Unlock-Reason:" in text(repo) and "Status: DRAFT" in text(repo)
    edit(repo, "\n## 4.", "- [ ] 3. Ubah `report.js`: sesuaikan pemanggil\n\n## 4.")
    assert pl("lock", "--answer", "ok revisi").returncode == 0
    assert "- Base-Commit:" in text(repo)
    assert "mode=resume" in pl("start").stdout


def test_d2_resume_sesudah_sesi_putus(repo, pl):
    pl("lock", "--answer", "ok")
    base = git(repo, "rev-parse", "HEAD").strip()
    assert "mode=awal" in pl("start").stdout
    tick(repo, 1)
    r = pl("start")
    assert "mode=resume" in r.stdout and "berikutnya: 2. Ubah `lib.js`" in r.stdout
    assert f"- Base-Commit: {base}" in text(repo)


def test_d2_resume_tanpa_blok_mengisi_base_note(repo, pl):
    pl("lock", "--answer", "ok")
    tick(repo, 1)
    r = pl("start")
    assert "mode=resume" in r.stdout and "- Base-Note:" in text(repo)


def test_d2_blocked_lalu_resume(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1)
    assert pl("close", "--status", "BLOCKED", "--verification", "x").returncode == 1  # tanpa --blocked-step
    assert pl("close", "--status", "BLOCKED", "--verification", "x", "--blocked-step", "2").returncode == 0
    assert "mode=resume" in pl("start").stdout


def test_d2_close_completed_menolak_langkah_terbuka(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1)
    assert pl("close", "--status", "COMPLETED", "--verification", "x").returncode == 1


def test_d2_close_tanpa_start_ditolak(repo, pl):
    pl("lock", "--answer", "ok")
    tick(repo, 1, 2)
    assert pl("close", "--status", "COMPLETED", "--verification", "x").returncode == 1


def test_d3_plafon_remediasi(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    for n in range(2):
        assert pl("close", "--status", "COMPLETED", "--verification", "ok").returncode == 0
        assert pl("start", "--findings", "--findings-text", f"R{n} app.js:1 — x").returncode == 0
    pl("close", "--status", "COMPLETED", "--verification", "ok")
    r = pl("start", "--findings", "--findings-text", "R3")
    assert r.returncode == 1 and "plafon 2 putaran" in r.stdout


def test_d6_profile_tercatat_di_metadata(repo, pl):
    pl("lock", "--answer", "ok", "--profile", "apps/api/repo-profile.md")
    assert json.loads(pl("status", "--json").stdout)["profile"] == "apps/api/repo-profile.md"


def test_d7_konfirmasi_manual_tercatat(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    pl("close", "--status", "VERIFICATION_MANUAL_REQUIRED", "--verification", "test manual")
    assert "mode=manual" in pl("start").stdout
    assert pl("confirm", "--answer", "sudah jalan, hijau").returncode == 0
    assert "- Status: COMPLETED (manual)" in text(repo)
    assert "mode=selesai" in pl("start").stdout


def test_d7_findings_tersimpan(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    pl("close", "--status", "COMPLETED", "--verification", "ok")
    assert pl("start", "--findings").returncode == 1  # temuan wajib dicatat
    assert pl("start", "--findings", "--findings-text", "R1 app.js:3 — cek null").returncode == 0
    assert '- Findings-1: "R1 app.js:3 — cek null"' in text(repo)
    assert json.loads(pl("status", "--json").stdout)["remediation_round"] == 1


def test_d8_repo_tanpa_commit_base_none(make_repo):
    root = make_repo({"plan/t.md": PLAN})
    run = lambda *a: run_script(PL, *a, "--plan", "plan/t.md", cwd=root)
    run("lock", "--answer", "ok")
    assert "base=none" in run("start").stdout
    assert json.loads(run("status", "--json").stdout)["execution"]["Base-Commit"] == "none"


def test_d7_manual_gagal_menjadi_blocked_lalu_resume(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    pl("close", "--status", "VERIFICATION_MANUAL_REQUIRED", "--verification", "test manual")
    assert pl("close", "--status", "COMPLETED", "--verification", "x").returncode == 1
    assert pl("close", "--status", "BLOCKED", "--verification", "gagal", "--blocked-step", "verifikasi").returncode == 0
    assert "mode=resume · langkah 2/2" in pl("start").stdout
