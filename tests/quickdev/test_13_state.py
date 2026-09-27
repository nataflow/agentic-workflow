"""Regresi 13 tahap 2 — mesin state `plan_lock.py` (Q1, Q3, Q6, Q9, Q14)."""
import json

import pytest

from conftest import PLUGINS, commit, git, run_script

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


@pytest.fixture
def repo(make_repo):
    root = make_repo({"app.js": "a\n", "lib.js": "b\n", "repo-profile.md": "# profil\n",
                      ".gitignore": "dist/\n"})
    commit(root, "init")
    (root / "plan").mkdir()
    (root / "plan" / "t.md").write_text(PLAN, encoding="utf-8")
    return root


@pytest.fixture
def pl(repo):
    return lambda *a, stdin="": run_script(PL, *a, "--plan", "plan/t.md", cwd=repo, stdin=stdin)


def text(repo):
    return (repo / "plan" / "t.md").read_text(encoding="utf-8")


def edit(repo, old, new):
    (repo / "plan" / "t.md").write_text(text(repo).replace(old, new), encoding="utf-8")


def tick(repo, *ns):
    for n in ns:
        edit(repo, f"- [ ] {n}.", f"- [x] {n}.")


def status(pl):
    return json.loads(pl("status", "--json").stdout)


def execute(repo, pl, verification="npm test hijau"):
    """Satu putaran execute penuh: start → ubah kode → centang → close COMPLETED."""
    pl("lock", "--answer", "ok")
    assert "mode=awal" in pl("start").stdout
    (repo / "app.js").write_text("a\ncheckQuota()\n", encoding="utf-8")
    tick(repo, 1, 2)
    assert pl("close", "--status", "COMPLETED", "--verification", verification).returncode == 0


# --- Q1: tree bersih dinilai skrip sebelum state ditulis ---------------------------------------

def test_q1_awal_menolak_tree_kotor_tanpa_menulis_blok(repo, pl):
    pl("lock", "--answer", "ok")
    (repo / "src").mkdir()
    (repo / "src" / "unrelated.ts").write_text("x\n", encoding="utf-8")
    r = pl("start")
    assert r.returncode == 1 and "src/unrelated.ts" in r.stdout
    assert "## Execution Status" not in text(repo)
    commit(repo, "user commit perubahan lain", "src/unrelated.ts")
    r = pl("start")
    assert "mode=awal" in r.stdout
    assert status(pl)["execution"]["Base-Commit"] == git(repo, "rev-parse", "HEAD").strip()


def test_q1_awal_mengizinkan_rencana_dan_profil(repo, pl):
    pl("lock", "--answer", "ok")
    (repo / "repo-profile.md").write_text("# profil REFRESH\n", encoding="utf-8")
    (repo / "plan" / "lain.md").write_text("# rencana lain\n", encoding="utf-8")
    assert "mode=awal" in pl("start").stdout


def test_q1_awal_di_luar_repo_git_ditolak(make_repo):
    root = make_repo({"plan/t.md": PLAN}, git_init=False)
    run = lambda *a: run_script(PL, *a, "--plan", "plan/t.md", cwd=root)
    run("lock", "--answer", "ok")
    r = run("start")
    assert r.returncode == 1 and "bukan repo git" in r.stdout


def test_q1_base_bukan_leluhur_head_dilaporkan(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    git(repo, "commit", "-q", "--amend", "-m", "init (amend)")    # Base-Commit tidak lagi leluhur HEAD
    st = status(pl)
    assert "bukan leluhur HEAD" in st["base_drift"]
    assert "PERINGATAN" in pl("start").stdout


def test_q1_commit_sesudah_base_dihitung(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    (repo / "app.js").write_text("a\nx\n", encoding="utf-8")
    commit(repo, "kerja parsial", "app.js")
    st = status(pl)
    assert st["base_drift"] == "-" and st["commits_since_base"] == 1


# --- Q3: ronde remediasi yang terputus dilanjutkan ---------------------------------------------

def test_q3_remediasi_terputus_dilanjutkan_tanpa_menambah_ronde(repo, pl):
    execute(repo, pl)
    r = pl("start", "--findings", "--findings-text", "[MAJOR] app.js:2 null")
    assert "mode=remediasi" in r.stdout and status(pl)["remediation_open"] is True
    for args in (("start",), ("start", "--findings", "--findings-text", "teks lain")):
        r = pl(*args)                                              # sesi putus → dipanggil ulang
        assert r.returncode == 0 and "mode=remediasi" in r.stdout and "lanjutan" in r.stdout
        assert "app.js:2 null" in r.stdout
    st = status(pl)
    assert st["remediation_round"] == 1 and st["open_findings"] == '"[MAJOR] app.js:2 null"'


def test_q3_remediasi_blocked_lalu_dilanjutkan(repo, pl):
    execute(repo, pl)
    pl("start", "--findings", "--findings-text", "R1 app.js:2")
    assert pl("close", "--status", "BLOCKED", "--verification", "temuan di luar rencana",
              "--blocked-step", "remediasi").returncode == 0
    assert "mode=remediasi" in pl("start").stdout
    assert pl("close", "--status", "COMPLETED", "--verification", "hijau").returncode == 0
    st = status(pl)
    assert st["remediation_open"] is False and st["execution"]["Remediation-State"] == "CLOSED"
    assert "mode=selesai" in pl("start").stdout
    r = pl("start", "--findings", "--findings-text", "R2")
    assert "mode=remediasi" in r.stdout and status(pl)["remediation_round"] == 2


# --- Q9: segel isi kode saat close --------------------------------------------------------------

def test_q9_kode_berubah_sesudah_close_basi(repo, pl):
    execute(repo, pl)
    assert status(pl)["consistent"] is True
    (repo / "app.js").write_text("a\ncheckQuota()\nsuntingan sesudah close\n", encoding="utf-8")
    st = status(pl)
    assert st["consistent"] is False and "kode berubah" in st["inconsistency"]
    r = pl("start")
    assert "mode=resume" in r.stdout and "verifikasi basi" in r.stdout
    assert pl("close", "--status", "COMPLETED", "--verification", "hijau ulang").returncode == 0
    assert status(pl)["consistent"] is True


def test_q9_berkas_untracked_baru_basi_tetapi_ignored_tidak(repo, pl):
    execute(repo, pl)
    (repo / "dist").mkdir()
    (repo / "dist" / "bundle.js").write_text("x\n", encoding="utf-8")
    assert status(pl)["consistent"] is True
    (repo / "baru.js").write_text("x\n", encoding="utf-8")
    assert status(pl)["consistent"] is False


def test_q9_commit_sesudah_close_tidak_basi(repo, pl):
    execute(repo, pl)
    commit(repo, "feat: kuota", "app.js")
    assert status(pl)["consistent"] is True


def test_q9_confirm_menolak_kode_yang_berubah(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    pl("close", "--status", "VERIFICATION_MANUAL_REQUIRED", "--verification", "cek manual")
    (repo / "app.js").write_text("diperbaiki saat uji manual\n", encoding="utf-8")
    r = pl("confirm", "--answer", "lolos")
    assert r.returncode == 1 and "resume" in r.stdout
    assert "mode=resume" in pl("start").stdout


def test_q9_blok_lama_tanpa_segel_tidak_dinilai(repo, pl):
    execute(repo, pl)
    body = "\n".join(l for l in text(repo).splitlines() if not l.startswith(("- Tree-Hash:", "- Verified-Hash:")))
    (repo / "plan" / "t.md").write_text(body + "\n", encoding="utf-8")
    (repo / "app.js").write_text("berubah\n", encoding="utf-8")
    assert status(pl)["consistent"] is True and "mode=selesai" in pl("start").stdout


# --- Q14: rencana berubah sesudah verifikasi ---------------------------------------------------

def test_q14_revisi_tanpa_langkah_baru_memicu_verifikasi_ulang(repo, pl):
    execute(repo, pl)
    pl("unlock", "--reason", "ganti strategi verifikasi")
    edit(repo, "- `npm test`", "- `npm test`\n- `npm run e2e`")
    pl("lock", "--answer", "ok revisi")
    st = status(pl)
    assert st["consistent"] is False and "rencana berubah" in st["inconsistency"]
    r = pl("start")
    assert "mode=resume" in r.stdout and "verifikasi basi" in r.stdout


# --- Q6: baseline segar terikat Base-Commit ------------------------------------------------------

def test_q6_baseline_dikunci_di_base_commit(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    summary = "typecheck=PASSED lint=FAILED[app.js no-undef x2] test=PASSED build=TIDAK_ADA"
    assert pl("baseline", "--summary", "-", stdin=summary).returncode == 0
    b = status(pl)["execution"]
    assert b["Baseline"] == f'"{summary}"' and b["Baseline-Commit"] == b["Base-Commit"]
    assert "BASELINE:" in pl("start").stdout                        # terbaca ulang di sesi berikutnya


def test_q6_baseline_ditolak_sesudah_mutasi_atau_head_bergeser(repo, pl):
    pl("lock", "--answer", "ok")
    assert pl("baseline", "--summary", "x").returncode == 1          # belum `start`
    pl("start")
    (repo / "app.js").write_text("sudah diubah\n", encoding="utf-8")
    r = pl("baseline", "--summary", "x")
    assert r.returncode == 1 and "app.js" in r.stdout
    commit(repo, "maju", "app.js")
    r = pl("baseline", "--summary", "x")
    assert r.returncode == 1 and "Base-Commit" in r.stdout
