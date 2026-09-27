"""L3.3 — `run_verification.py`: vonis penutup dari exit code dan baseline yang dicatat mesin."""
import importlib.util
import json
import subprocess
import sys

import pytest

from conftest import PLUGINS

COPIES = {p: PLUGINS / p / "skills/_common/run_verification.py" for p in ("frontend", "backend")}


def run(rv, tmp, mode, *cmds, timeout=5, extra=()):
    args = [sys.executable, str(rv), mode, "--taskdir", "td", "--timeout", str(timeout), *extra]
    for c in cmds:
        args += ["--cmd", c]
    return subprocess.run(args, cwd=tmp, capture_output=True, text=True)


def closing_md(tmp):
    return (tmp / "td/.explore/closing-verification.md").read_text(encoding="utf-8")


def test_copies_identical():
    fe, be = (p.read_bytes() for p in COPIES.values())
    assert fe == be, "salinan run_verification.py frontend dan backend berbeda"


@pytest.fixture(params=list(COPIES), ids=list(COPIES))
def rv(request):
    return COPIES[request.param]


def test_exit_code_captured_and_timeout(rv, tmp_path):
    r = run(rv, tmp_path, "closing", "t=sh -c 'exit 2'", "b=sleep 30", timeout=1)
    assert r.returncode == 1
    md = closing_md(tmp_path)
    assert "| `t` | MERAH | 1 | 2 |" in md and "| `b` | TIMEOUT |" in md
    assert "Baseline absen" in md


def test_inherited_red_is_not_new(rv, tmp_path):
    run(rv, tmp_path, "baseline", "t=sh -c 'echo \"FAIL a.test.ts (12 ms)\"; exit 1'")
    r = run(rv, tmp_path, "closing", "t=sh -c 'echo \"FAIL a.test.ts (15 ms)\"; exit 1'")
    assert r.returncode == 0, r.stdout
    assert "| `t` | MERAH | 0 |" in closing_md(tmp_path)


def test_new_error_on_top_of_inherited_red(rv, tmp_path):
    run(rv, tmp_path, "baseline", "tc=sh -c 'echo \"src/old.ts:10:5 - error TS2304\"; exit 2'")
    r = run(rv, tmp_path, "closing",
            "tc=sh -c 'echo \"src/old.ts:11:5 - error TS2304\"; echo \"src/new.ts:3:1 - error TS2322\"; exit 2'")
    assert r.returncode == 1
    assert "| `tc` | MERAH | 1 | 2 |" in closing_md(tmp_path)


def test_baseline_reused_not_remeasured(rv, tmp_path):
    run(rv, tmp_path, "baseline", "t=true")
    r = run(rv, tmp_path, "baseline", "t=false")
    assert "dipakai ulang" in r.stdout
    base = json.loads((tmp_path / "td/.explore/verification-baseline.json").read_text())
    assert base["t"]["exit"] == 0
    run(rv, tmp_path, "baseline", "t=false", extra=("--force",))
    assert json.loads((tmp_path / "td/.explore/verification-baseline.json").read_text())["t"]["exit"] == 1


def test_bad_cmd_is_usage_error(rv, tmp_path):
    assert run(rv, tmp_path, "closing", "tanpa-sama-dengan").returncode == 2


def test_custom_out_for_per_brief_gate(rv, tmp_path):
    r = run(rv, tmp_path, "closing", "typecheck=true", extra=("--out", "td/.explore/gate-01.md"))
    assert r.returncode == 0
    assert "| `typecheck` | HIJAU | 0 |" in (tmp_path / "td/.explore/gate-01.md").read_text()


def test_output_readable_by_validate_review(tmp_path):
    """Tabel keluaran, disalin apa adanya ke `## Verifikasi Penutup`, terbaca `validate_review.py`."""
    rv = COPIES["frontend"]
    run(rv, tmp_path, "baseline", "test=sh -c 'echo \"FAIL a.test.ts\"; exit 1'", "lint=true")
    run(rv, tmp_path, "closing", "test=sh -c 'echo \"FAIL a.test.ts\"; exit 1'", "lint=true | cat")
    body = "## Verifikasi Penutup\n\n" + closing_md(tmp_path) + "\n## Lain\n"
    sys.path.insert(0, str(PLUGINS / "frontend/skills/_common"))
    spec = importlib.util.spec_from_file_location(
        "validate_review_l33", PLUGINS / "frontend/skills/architect/scripts/validate_review.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = [l for l in mod.section_lines(body, "## Verifikasi Penutup") if l.startswith("| `")]
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
    assert [(c[0], c[1], c[2]) for c in cells] == [("`test`", "MERAH", "0"), ("`lint`", "HIJAU", "0")]


@pytest.mark.parametrize("path", [
    "backend/skills/architect/SKILL.md",
    "frontend/skills/architect/SKILL.md",
    "frontend/skills/architect/references/execution-protocol.md",
])
def test_architects_use_runner_not_tail(path):
    text = (PLUGINS / path).read_text(encoding="utf-8")
    assert "tail -40" not in text
    assert "run_verification.py" in text


def test_closing_writes_machine_log(rv, tmp_path):
    """L4.2 aturan 11 — log mesin di sebelah `closing-verification.md`, dibaca `validate_review.py --log`."""
    run(rv, tmp_path, "baseline", "test=sh -c 'echo \"FAIL a.test.ts\"; exit 1'", "lint=true")
    run(rv, tmp_path, "closing", "test=sh -c 'echo \"FAIL a.test.ts\"; exit 1'", "lint=true")
    log = json.loads((tmp_path / "td/.explore/closing-verification.json").read_text(encoding="utf-8"))
    assert [(e["cmd"], e["status"], e["new_errors"], e["baseline_status"]) for e in log] == \
        [("test", "MERAH", 0, "MERAH"), ("lint", "HIJAU", 0, "HIJAU")]
