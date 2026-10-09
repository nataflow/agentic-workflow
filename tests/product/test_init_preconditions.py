"""Prasyarat `product:init`: folder kosong tanpa git PASS, codebase memberi mode codebase, home ditolak."""
import json
import os
import subprocess
import sys

from conftest import GIT_ENV, PLUGINS, run_script
from product_helpers import empty_ws, ws  # noqa: F401  (fixture)

PRE = PLUGINS / "product" / "skills" / "init" / "scripts" / "check_preconditions.py"


def _run(root):
    proc = run_script(PRE, "--json", cwd=root)
    return proc, json.loads(proc.stdout)


def test_folder_kosong_tanpa_git_pass(empty_ws):
    proc, data = _run(empty_ws.root)
    assert proc.returncode == 0, proc.stdout
    assert data["workspace"] == "EMPTY" and data["mode_diizinkan"] == "NEW_PRODUCT" and data["git"] == "tidak"
    assert data["charter_terbuka"] == "-"


def test_codebase_memberi_mode_codebase(ws):
    proc, data = _run(ws.root)
    assert proc.returncode == 0
    if ws.mode == "NEW_PRODUCT":
        assert data["workspace"] == "EMPTY"
    else:
        assert data["workspace"] == "CODEBASE" and data["bukti"] == "src/kasir.go"
        assert data["mode_diizinkan"] == "NEW_FEATURE,IMPROVEMENT"


def test_manifest_di_root_cukup_jadi_bukti(empty_ws):
    (empty_ws.root / "package.json").write_text("{}\n", encoding="utf-8")
    _, data = _run(empty_ws.root)
    assert data["workspace"] == "CODEBASE" and data["bukti"] == "package.json"


def test_charter_terbuka_terdaftar(empty_ws):
    assert empty_ws.new().returncode == 0
    _, data = _run(empty_ws.root)
    assert data["charter_terbuka"] == "product/keuangan-umkm(ELICITATION)"


def test_home_ditolak(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = {**os.environ, **GIT_ENV, "HOME": str(home)}
    proc = subprocess.run([sys.executable, str(PRE), "--root", str(home)], capture_output=True, text=True, env=env)
    assert proc.returncode == 1 and "direktori home" in proc.stdout
