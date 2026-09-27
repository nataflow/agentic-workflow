"""Regresi 12 Tahap 2 sisi backend — salinan kembar `run_verification.py` (J11, J12, J13, J23) dan
`migrate_profile.py` (J21). Isi berkasnya identik byte dengan frontend (`test_run_verification.py`
`test_copies_identical`, `tests/frontend/test_12_verification.py`)."""
import json
import subprocess
import sys

import pytest

from conftest import PLUGINS, be_profile, commit, git, run_script, write_files

RUNV = PLUGINS / "backend/skills/_common/run_verification.py"
MIGRATE = PLUGINS / "backend/skills/profile/scripts/migrate_profile.py"


def runv(tmp, mode, *cmds, timeout=5):
    args = [sys.executable, str(RUNV), mode, "--taskdir", "td", "--timeout", str(timeout)]
    for c in cmds:
        args += ["--cmd", c]
    return subprocess.run(args, cwd=tmp, capture_output=True, text=True)


@pytest.mark.regression("J11")
def test_j11_pipa_tidak_menelan_exit(tmp_path):
    r = runv(tmp_path, "closing", "build=false | cat")
    assert r.returncode == 1 and "MERAH" in r.stdout, r.stdout


@pytest.mark.regression("J12")
def test_j12_galat_kembar_baseline_terhitung_baru(tmp_path):
    runv(tmp_path, "baseline", "build=printf 'a/a.go:2:23: undefined: x\\n'; exit 1")
    r = runv(tmp_path, "closing", "build=printf 'a/a.go:2:23: undefined: x\\na/a.go:9:4: undefined: x\\n'; exit 1")
    assert r.returncode == 1 and "baru=1" in r.stdout, r.stdout


@pytest.mark.regression("J13")
def test_j13_baseline_mencatat_head(make_repo):
    repo = make_repo({"a.txt": "a\n"})
    commit(repo, "init")
    runv(repo, "baseline", "build=true")
    base = json.loads((repo / "td/.explore/verification-baseline.json").read_text(encoding="utf-8"))
    assert base["build"]["head"] == git(repo, "rev-parse", "HEAD").strip()


@pytest.mark.regression("J23")
def test_j23_nama_ganda_ditolak(tmp_path):
    r = runv(tmp_path, "baseline", "build=true", "build=false")
    assert r.returncode == 2 and "ganda" in r.stderr and "Traceback" not in r.stderr, r.stderr


@pytest.mark.regression("J21")
def test_j21_tujuan_berisi_tidak_ditimpa(make_repo):
    root = make_repo()
    be_profile(root, "go", legacy=True)
    commit(root, "profil lama")
    write_files(root, {".claude/profile/backenddev/commands.md": "# suntingan user\n"})
    r = run_script(MIGRATE, "--root", str(root), "--json")
    assert r.returncode == 1 and "commands.md" in json.loads(r.stdout)["error"], r.stdout
    assert (root / ".claude/profile/backenddev/commands.md").read_text(encoding="utf-8") == "# suntingan user\n"
    assert (root / ".claude/profile/index.json").is_file()
