"""08c C10 (profile_dir kanonik) dan C13 (mode PATCH `drift.md`)."""
import json

import pytest

from conftest import PLUGINS, commit, fe_profile, run_script, write_files

SCRIPT = PLUGINS / "frontend/skills/profile/scripts/check_preconditions.py"
REACT_VITE = json.dumps({"dependencies": {"react": "^19", "react-dom": "^19"}, "devDependencies": {"vite": "^6"}})


def run(root, *args):
    proc = run_script(SCRIPT, "--json", "--root", str(root), *args)
    out = json.loads(proc.stdout)
    return proc, out, next(c for c in out["checks"] if c["id"] == 6)


@pytest.fixture
def react(make_repo):
    return make_repo({"package.json": REACT_VITE})


# --- C10 --------------------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["docs/elsewhere", "/tmp/luar-repo", ".claude/profile"])
def test_c10_profile_dir_lain_ditolak(react, value):
    proc = run_script(SCRIPT, "--root", str(react), "--profile-dir", value)
    assert proc.returncode == 1 and "ditolak" in proc.stdout


@pytest.mark.parametrize("value", [None, ".claude/profile/frontenddev", "./.claude/profile/frontenddev/"])
def test_c10_profile_dir_kanonik_diterima(react, value):
    args = ["--root", str(react)] + (["--profile-dir", value] if value else [])
    assert run_script(SCRIPT, *args).returncode == 0


def test_c10_template_peta_berkas_memuat_target_app():
    tmpl = (PLUGINS / "frontend/skills/profile/templates/profile-template.md").read_text(encoding="utf-8")
    row = next(l for l in tmpl.splitlines() if l.startswith("| `index.json` |"))
    assert "`target_app`" in row


# --- C13 --------------------------------------------------------------------------------------

def test_c13_patch_tanpa_profil_gagal(react):
    proc, out, check = run(react, "--mode", "patch")
    assert proc.returncode == 1 and check["status"] == "FAIL"
    assert "absen atau bukan JSON valid" in check["summary"] and out["mode"] == "GENERATE"


def test_c13_patch_di_atas_profil_utuh_lolos(react):
    fe_profile(react, "react-vite")
    commit(react, "docs: init frontend profile")
    proc, out, check = run(react, "--mode", "patch")
    assert proc.returncode == 0, check
    assert out["mode"] == "PATCH" and "drift.md" in check["summary"]


def test_c13_patch_stack_berubah_gagal(react):
    fe_profile(react, "sveltekit")
    commit(react, "docs: init frontend profile")
    proc, out, check = run(react, "--mode", "patch")
    assert proc.returncode == 1
    assert "stack profil `sveltekit` ≠ stack terdeteksi `react-vite`" in check["summary"]
    assert out["mode"] == "REFRESH"


def test_c13_patch_berkas_profil_hilang_gagal(react):
    d = fe_profile(react, "react-vite")
    commit(react, "docs: init frontend profile")
    (d / "visual.md").unlink()
    proc, _out, check = run(react, "--mode", "patch")
    assert proc.returncode == 1 and "berkas profil hilang: visual.md" in check["summary"]


def test_c13_patch_direktori_profil_kotor_gagal(react):
    fe_profile(react, "react-vite")
    commit(react, "docs: init frontend profile")
    write_files(react, {".claude/profile/frontenddev/invariants.md": "# invariants\n- diubah\n"})
    proc, _out, check = run(react, "--mode", "patch")
    assert proc.returncode == 1 and "perubahan menggantung" in check["summary"]


def test_c13_auto_tidak_pernah_patch(react):
    fe_profile(react, "react-vite")
    commit(react, "docs: init frontend profile")
    _proc, out, _check = run(react)
    assert out["mode"] == "REFRESH"
