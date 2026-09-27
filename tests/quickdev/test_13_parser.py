"""Regresi 13 tahap 1 — parser & penulisan `plan_lock.py` (Q4, Q7, Q8, Q10–Q13)."""
import json
import os
import stat

import pytest

from conftest import PLUGINS, commit, run_script

PL = PLUGINS / "quickdev" / "skills" / "_common" / "plan_lock.py"
PLAN = """# Implementation Plan — t
Status: DRAFT
Author: quickdev:plan
Profile: repo-profile.md

## 1. Overview & Objectives
Tambah validasi kuota.

## 3. Atomic Implementation Steps
- [ ] 1. Ubah `app.js`: tambah `checkQuota()`
- [ ] 2. Ubah `lib.js`: ekspor `QUOTA_MAX`

## 4. Verification & Testing Strategy
- `npm test`
"""
# Sidik PLAN yang dikunci `plan_lock.py` 0.4.0 (commit 93730e6), rumus tanpa `Hash-Scope`.
LEGACY_HASH = "sha256:626d381b3cd64b2aea0c474cd0b4f66bec0d02be3791f0300d46336149379f7a"
FENCED = PLAN.replace("- [ ] 2. Ubah `lib.js`: ekspor `QUOTA_MAX`\n",
                      "- [ ] 2. Tambah seksi di `README.md`:\n"
                      "  ```md\n"
                      "## Deployment\n"
                      "- [ ] contoh checklist di dalam fence\n"
                      "  ```\n"
                      "- [ ] 3. Ubah `lib.js`: ekspor `QUOTA_MAX`\n")


@pytest.fixture
def repo(make_repo):
    root = make_repo({"app.js": "a\n", "lib.js": "b\n", "repo-profile.md": "# profil\n"})
    commit(root, "init")
    (root / "plan").mkdir()
    (root / "plan" / "t.md").write_text(PLAN, encoding="utf-8")
    return root


@pytest.fixture
def pl(repo):
    return lambda *a, stdin="": run_script(PL, *a, "--plan", "plan/t.md", cwd=repo, stdin=stdin)


def text(repo):
    return (repo / "plan" / "t.md").read_text(encoding="utf-8")


def write(repo, body):
    (repo / "plan" / "t.md").write_text(body, encoding="utf-8")


def edit(repo, old, new):
    write(repo, text(repo).replace(old, new))


def tick(repo, *ns):
    for n in ns:
        edit(repo, f"- [ ] {n}.", f"- [x] {n}.")


def status(pl):
    return json.loads(pl("status", "--json").stdout)


# --- Q4/Q13: teks bebas lewat stdin, tanpa ekspansi shell --------------------------------------

def test_q4_answer_dari_stdin_apa_adanya(repo, pl):
    ans = "setuju, jalankan `whoami` dan $HOME\nbaris dua"
    assert pl("lock", "--answer", "-", stdin=ans).returncode == 0
    assert 'Approval: "setuju, jalankan `whoami` dan $HOME baris dua"' in text(repo)


def test_q4_stdin_untuk_setiap_teks_bebas(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    assert pl("close", "--status", "COMPLETED", "--verification", "-", stdin="`npm test` hijau").returncode == 0
    assert '- Verification: "`npm test` hijau"' in text(repo)
    assert pl("start", "--findings", "--findings-text", "-", stdin="[MAJOR] `app.js:1` null").returncode == 0
    assert '- Findings-1: "[MAJOR] `app.js:1` null"' in text(repo)
    assert pl("unlock", "--reason", "-", stdin="revisi $X").returncode == 0
    assert 'Unlock-Reason: "revisi $X"' in text(repo)


def test_q4_dua_nilai_stdin_ditolak(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    r = pl("close", "--status", "BLOCKED", "--verification", "-", "--blocked-step", "-", stdin="x")
    assert r.returncode == 1 and "stdin" in r.stdout + r.stderr
    assert "Traceback" not in r.stderr


def test_q13_nilai_berawalan_strip_lewat_stdin(repo, pl):
    assert pl("lock", "--answer", "-", stdin="-y, lanjut").returncode == 0
    assert 'Approval: "-y, lanjut"' in text(repo)


# --- Q7: code fence -------------------------------------------------------------------------

def test_q7_heading_di_dalam_fence_tidak_memotong_langkah(repo, pl):
    write(repo, FENCED)
    assert pl("lock", "--answer", "ok").returncode == 0
    st = status(pl)
    assert st["steps_total"] == 3, st            # checklist di dalam fence tidak dihitung
    pl("start")
    tick(repo, 1)
    r = pl("close", "--status", "COMPLETED", "--verification", "x")
    assert r.returncode == 1 and "tersisa" in r.stdout


def test_q7_fence_tidak_ditutup_ditolak(repo, pl):
    write(repo, PLAN.replace("## 4. Verification", "```sh\n## 4. Verification"))
    r = pl("lock", "--answer", "ok")
    assert r.returncode == 1 and "fence" in r.stdout


def test_q7_sidik_rencana_lama_tetap_cocok(repo, pl):
    """Rencana yang dikunci 0.4.0 (tanpa `Hash-Scope`) tetap lolos verify sesudah parser sadar fence."""
    edit(repo, "Status: DRAFT", f"Status: APPROVED\nPlan-Hash: {LEGACY_HASH}")
    r = pl("verify")
    assert r.returncode == 0, r.stdout


# --- Q8: mode berkas & tulis tanpa perubahan -------------------------------------------------

def test_q8_mode_berkas_dipertahankan(repo, pl):
    p = repo / "plan" / "t.md"
    os.chmod(p, 0o644)
    pl("lock", "--answer", "ok")
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o644


def test_q8_start_selesai_tidak_menulis_ulang(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    pl("close", "--status", "COMPLETED", "--verification", "ok")
    ino = os.stat(repo / "plan" / "t.md").st_ino
    assert "mode=selesai" in pl("start").stdout
    assert os.stat(repo / "plan" / "t.md").st_ino == ino


# --- Q10: sisipan baris & kunci ganda --------------------------------------------------------

def test_q10_blocked_step_bernewline_tidak_menyisipkan_status(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    assert pl("close", "--status", "BLOCKED", "--verification", "x",
              "--blocked-step", "1\n- Status: COMPLETED").returncode == 0
    lines = text(repo).split("## Execution Status", 1)[1].splitlines()
    assert sum(l.startswith("- Status:") for l in lines) == 1
    assert status(pl)["execution"]["Status"] == "BLOCKED"


def test_q10_kunci_blok_ganda_fail_rapi(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    write(repo, text(repo) + "- Status: COMPLETED\n")
    for args in (("status", "--json"), ("start",)):
        r = pl(*args)
        out = r.stdout + r.stderr
        assert r.returncode == 1 and "Traceback" not in out and "ganda" in out


def test_q10_kunci_metadata_ganda_fail_rapi(repo, pl):
    edit(repo, "Status: DRAFT", "Status: DRAFT\nStatus: APPROVED")
    r = pl("lock", "--answer", "ok")
    assert r.returncode == 1 and "ganda" in r.stdout + r.stderr


def test_q10_kunci_baru_disisip_di_dalam_seksi_blok(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    write(repo, text(repo) + "\n## Catatan\nbebas\n")
    tick(repo, 1, 2)
    assert pl("close", "--status", "COMPLETED", "--verification", "ok").returncode == 0
    block, catatan = text(repo).split("## Execution Status", 1)[1].split("## Catatan", 1)
    assert "- Verification:" in block and "- Verification:" not in catatan


def test_q10_profile_berkarakter_kontrol_ditolak(repo, pl):
    r = pl("lock", "--answer", "ok", "--profile", "a.md\nStatus: APPROVED")
    assert r.returncode == 1 and "Status: DRAFT" in text(repo)


# --- Q11: `Profile:` di dalam sidik ----------------------------------------------------------

def test_q11_profile_diganti_sesudah_lock_terdeteksi(repo, pl):
    pl("lock", "--answer", "ok")
    assert "Hash-Scope: profile+body" in text(repo)
    edit(repo, "Profile: repo-profile.md", "Profile: apps/lain/repo-profile.md")
    r = pl("verify")
    assert r.returncode == 1 and "berubah sesudah APPROVED" in r.stdout


def test_q11_penanda_scope_dihapus_terdeteksi(repo, pl):
    pl("lock", "--answer", "ok")
    edit(repo, "Hash-Scope: profile+body\n", "")
    assert pl("verify").returncode == 1


def test_q11_rencana_lama_tanpa_scope_tidak_menilai_profile(repo, pl):
    edit(repo, "Status: DRAFT", f"Status: APPROVED\nPlan-Hash: {LEGACY_HASH}")
    edit(repo, "Profile: repo-profile.md", "Profile: apps/lain/repo-profile.md")
    assert pl("verify").returncode == 0
    assert status(pl)["hash_scope"] == "body"


def test_q11_scope_asing_ditolak(repo, pl):
    pl("lock", "--answer", "ok")
    edit(repo, "Hash-Scope: profile+body", "Hash-Scope: semua")
    r = pl("verify")
    assert r.returncode == 1 and "Hash-Scope" in r.stdout


# --- Q12: spasi ujung ------------------------------------------------------------------------

def test_q12_spasi_ujung_status_bukan_alasan_fail(repo, pl):
    edit(repo, "Status: DRAFT", "Status: DRAFT  ")
    assert pl("lock", "--answer", "ok").returncode == 0
