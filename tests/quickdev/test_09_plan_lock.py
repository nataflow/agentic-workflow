"""Regresi 09 E2–E5 — `plan_lock.py`: revisi sesudah selesai, sidik kosong, blok rusak/palsu."""
import json

import pytest

from conftest import PLUGINS, commit, run_script

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
PLAN = """# Implementation Plan — t
Status: DRAFT
Author: quickdev:plan

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
    (repo / "plan" / "t.md").write_text(text(repo).replace(old, new), encoding="utf-8")


def tick(repo, *ns):
    for n in ns:
        edit(repo, f"- [ ] {n}.", f"- [x] {n}.")


NEW_STEP = "- [ ] 3. Ubah `report.js`: sesuaikan pemanggil\n\n## 4."


def completed(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    assert pl("close", "--status", "COMPLETED", "--verification", "npm test hijau").returncode == 0


def test_e2_revisi_sesudah_completed_menjadi_resume(repo, pl):
    completed(repo, pl)
    base = json.loads(pl("status", "--json").stdout)["execution"]["Base-Commit"]
    assert pl("unlock", "--reason", "review: tambah langkah konsumen").returncode == 0
    edit(repo, "\n## 4.", "\n" + NEW_STEP)
    assert pl("lock", "--answer", "ok revisi").returncode == 0
    r = pl("start")
    assert "mode=resume (rencana direvisi sesudah selesai)" in r.stdout and "berikutnya: 3." in r.stdout
    tick(repo, 3)
    assert pl("close", "--status", "COMPLETED", "--verification", "hijau").returncode == 0
    st = json.loads(pl("status", "--json").stdout)
    assert st["execution"]["Base-Commit"] == base and st["consistent"] is True


def test_e2_remediasi_ditolak_selama_langkah_revisi_terbuka(repo, pl):
    completed(repo, pl)
    pl("unlock", "--reason", "x")
    edit(repo, "\n## 4.", "\n" + NEW_STEP)
    pl("lock", "--answer", "ok")
    r = pl("start", "--findings", "--findings-text", "R1")
    assert r.returncode == 1 and "mode resume" in r.stdout


def test_e2_revisi_sesudah_manual_menjadi_resume(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    pl("close", "--status", "VERIFICATION_MANUAL_REQUIRED", "--verification", "manual")
    pl("unlock", "--reason", "x")
    edit(repo, "\n## 4.", "\n" + NEW_STEP)
    pl("lock", "--answer", "ok")
    assert pl("confirm", "--answer", "hijau").returncode == 1        # langkah 3 belum dikerjakan
    assert "mode=resume" in pl("start").stdout


def test_e3_rencana_tanpa_section_1_ditolak(repo, pl):
    edit(repo, "## 1. Overview & Objectives\n", "")
    r = pl("lock", "--answer", "ok")
    assert r.returncode == 1 and "`## 1.` tidak ada" in r.stdout


def test_e3_verify_menolak_rencana_lama_bersidik_kosong(repo, pl):
    # Kunci lama (sebelum E3) yang sempat terbit tanpa `## 1.` tidak boleh lolos verify.
    edit(repo, "## 1. Overview & Objectives\n", "")
    edit(repo, "Status: DRAFT", "Status: APPROVED\nPlan-Hash: sha256:" + "e3b0c442" * 8)
    r = pl("verify")
    assert r.returncode == 1 and "`## 1.` tidak ada" in r.stdout


def test_e4_remediation_round_rusak_fail_rapi(repo, pl):
    completed(repo, pl)
    edit(repo, "- Remediation-Round: 0", "- Remediation-Round: dua")
    for args in (("status", "--json"), ("start", "--findings", "--findings-text", "R1")):
        r = pl(*args)
        out = r.stdout + r.stderr
        assert r.returncode == 1 and "Traceback" not in out and "bukan bilangan" in out
    assert "bukan bilangan" in json.loads(pl("status", "--json").stdout)["error"]


def test_e4_save_atomik_tanpa_sisa_berkas_sementara(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    assert [p.name for p in (repo / "plan").iterdir()] == ["t.md"]


def test_e5_blok_completed_tulisan_tangan_tidak_konsisten(repo, pl):
    pl("lock", "--answer", "ok")
    (repo / "plan/t.md").write_text(text(repo) + "\n## Execution Status\n- Status: COMPLETED\n", encoding="utf-8")
    st = json.loads(pl("status", "--json").stdout)
    assert st["consistent"] is False and "langkah `- [ ]`" in st["inconsistency"]
    tick(repo, 1, 2)
    st = json.loads(pl("status", "--json").stdout)
    assert st["consistent"] is False and "tanpa `Verification`" in st["inconsistency"]


def test_e5_confirm_memanggil_verify(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    pl("close", "--status", "VERIFICATION_MANUAL_REQUIRED", "--verification", "manual")
    edit(repo, "Tambah validasi kuota.", "Tambah validasi kuota dan audit.")
    r = pl("confirm", "--answer", "hijau")
    assert r.returncode == 1 and "VERIFY FAIL" in r.stdout


def test_e5_lock_tanpa_profile_mempertahankan_metadata(repo, pl):
    edit(repo, "Author: quickdev:plan", "Author: quickdev:plan\nProfile: apps/web/repo-profile.md")
    pl("lock", "--answer", "ok")
    assert json.loads(pl("status", "--json").stdout)["profile"] == "apps/web/repo-profile.md"


def test_e5_lock_tanpa_profile_dan_metadata_memakai_default(make_repo):
    root = make_repo({"plan/t.md": PLAN})
    run_script(PL, "lock", "--answer", "ok", "--plan", "plan/t.md", cwd=root)
    st = json.loads(run_script(PL, "status", "--json", "--plan", "plan/t.md", cwd=root).stdout)
    assert st["profile"] == "repo-profile.md"
