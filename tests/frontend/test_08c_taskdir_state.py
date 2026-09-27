"""08c C4 — taskdir_state.py: vonis tidak menyesatkan, tanpa kode mati."""
import json

from conftest import FE_SKILLS, commit, git, run_script, write_files

SCRIPT = FE_SKILLS / "lead" / "scripts" / "taskdir_state.py"
TD = "frontenddev/docs/2609240900-label"

TASK = """---
status: ACTIVE
lane: HOTFIX_MINOR
sections: []
created: 2026-09-24
---

# Label

## Description

Contoh.

## Success Criteria

- [ ] **SC-1**: label benar — verifikasi: test `A.test.ts` hijau

## Out of Scope

- Lainnya — di luar lingkup

## Chain

{row}
"""
OPEN_ROW = "- [ ] BRIEF    — frontend:plan          → brief-*.md"
BRIEF = "---\nstatus: {}\nfiles_touched: [src/a.ts]\n---\n\n# Brief\n"


def state(root, *args):
    return run_script(SCRIPT, "--root", str(root), *args)


def test_c4_taskdir_yang_tidak_ada_bukan_akar(make_repo):
    proc = state(make_repo(), "--taskdir", "frontenddev/docs/2609240900-tidak-ada")
    assert "RUSAK" in proc.stdout and "direktori tidak ada" in proc.stdout
    assert "AKAR" not in proc.stdout


def test_c4_nama_di_luar_pola_dilaporkan_saat_pindai(make_repo):
    root = make_repo({"frontenddev/docs/2609240900-Order-Checkout/TASK.md": TASK.format(row=OPEN_ROW)})
    commit(root, "docs(Order-Checkout): kunci TASK sebagai akar rantai")
    proc = state(root)
    assert "nol taskdir terbuka" not in proc.stdout
    assert "2609240900-Order-Checkout" in proc.stdout and "RUSAK" in proc.stdout


def test_c4_direktori_non_pola_kosong_tetap_diabaikan(make_repo):
    root = make_repo()
    (root / "frontenddev/docs/catatan").mkdir(parents=True)
    assert "nol taskdir terbuka" in state(root).stdout


def test_c4_repo_non_git_gagal_eksplisit(make_repo):
    root = make_repo({f"{TD}/TASK.md": TASK.format(row=OPEN_ROW)}, git_init=False)
    proc = state(root)
    assert proc.returncode == 1 and "bukan repo git" in proc.stdout
    proc = state(root, "--json")
    assert proc.returncode == 1 and json.loads(proc.stdout)["status"] == "FAIL"


def test_c4_blocked_tanpa_remedi_menang_atas_ready(make_repo):
    root = make_repo({f"{TD}/TASK.md": TASK.format(row=OPEN_ROW),
                      f"{TD}/brief-01-a.md": BRIEF.format("READY"),
                      f"{TD}/brief-02-b.md": BRIEF.format("READY")})
    sha = commit(root, "docs(label): draft breakdown")
    write_files(root, {f"{TD}/TASK.md": TASK.format(
        row=f"- [x] BRIEF    — frontend:plan          → brief-*.md @ READY {sha}")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(label): approve breakdown (2 briefs)", "-m", f"Konten disetujui: {sha}",
        "-m", "Hop: BRIEF")
    write_files(root, {f"{TD}/brief-02-b.md": BRIEF.format("BLOCKED")})
    commit(root, "docs(label): brief 02 BLOCKED")
    proc = state(root, "--taskdir", TD)
    assert "TERHENTI" in proc.stdout, proc.stdout


def test_c4_kode_mati_dibuang():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "def followups" not in src and "DILANJUTKAN" not in src and "successors" not in src
