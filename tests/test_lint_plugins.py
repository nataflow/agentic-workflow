"""`scripts/lint_plugins.py` (L6.3): marketplace mini sah lolos, tiap check ditangkap satu kasus."""
import json
import os
import subprocess
import sys

import pytest

from conftest import REPO, git, load_module, write_files

LINT = REPO / "scripts" / "lint_plugins.py"
lint_mod = load_module(LINT, "lint_plugins_under_test")

SKILL = "---\nname: plan\ndescription: Gunakan ketika brief perlu ditulis.\nmetadata:\n  mode: standard\n---\n\n# Plan\n"
AGENT = "---\nname: code-explorer\ndescription: Penelusur kode read-only.\ntools: Read, Grep\n---\n\n# Explorer\n"
HOOKS = {"hooks": {"SessionStart": [{"hooks": [
    {"type": "command", "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/detect.py" --plugin demo'}]}]}}


def mini(root, **over):
    """Marketplace satu plugin `demo` yang lolos semua check; `over` menimpa/menambah berkas."""
    mp = {"name": "demo-market", "owner": {"name": "t"},
          "plugins": [{"name": "demo", "source": "./src/plugins/demo", "description": "Demo"}]}
    pj = {"name": "demo", "version": "0.1.0", "description": "Demo", "author": {"name": "t", "email": "t@t"}}
    files = {
        ".claude-plugin/marketplace.json": json.dumps(mp),
        "src/plugins/demo/.claude-plugin/plugin.json": json.dumps(pj),
        "src/plugins/demo/skills/plan/SKILL.md":
            SKILL + "\nJalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/check.py`. "
                    "Baca `references/rules.md`.\n",
        "src/plugins/demo/skills/plan/scripts/check.py": 'print("ok")\n',
        "src/plugins/demo/skills/plan/references/rules.md": "# Rules\n",
        "src/plugins/demo/agents/code-explorer.md": AGENT,
        "src/plugins/demo/hooks/hooks.json": json.dumps(HOOKS),
        "src/plugins/demo/hooks/detect.py": "import sys\n",
    }
    files.update(over)
    write_files(root, {k: v for k, v in files.items() if v is not None})
    for k, v in files.items():
        if v is None and (root / k).exists():
            (root / k).unlink()
    return root


def found(root, base=None):
    return {(i["level"], i["check"]) for i in lint_mod.lint(root, base).items}


def test_marketplace_sah_bersih(tmp_path):
    assert found(mini(tmp_path)) == set()


def test_m1_json_rusak(tmp_path):
    assert ("FAIL", "M1") in found(mini(tmp_path, **{"src/plugins/demo/hooks/hooks.json": "{"}))


def test_m2_source_hilang_dan_nama_beda(tmp_path):
    mp = {"name": "demo-market", "plugins": [{"name": "demo", "source": "./src/plugins/tidak-ada"}]}
    assert ("FAIL", "M2") in found(mini(tmp_path, **{".claude-plugin/marketplace.json": json.dumps(mp)}))
    mp = {"name": "demo-market", "plugins": [{"name": "lain", "source": "./src/plugins/demo"}]}
    assert ("FAIL", "M2") in found(mini(tmp_path, **{".claude-plugin/marketplace.json": json.dumps(mp)}))


def test_m3_versi_di_dua_tempat(tmp_path):
    mp = {"name": "demo-market", "plugins": [{"name": "demo", "source": "./src/plugins/demo", "version": "0.1.0"}]}
    assert ("FAIL", "M3") in found(mini(tmp_path, **{".claude-plugin/marketplace.json": json.dumps(mp)}))


def test_m4_author_beda(tmp_path):
    mp = {"name": "demo-market", "plugins": [{"name": "demo", "source": "./src/plugins/demo",
                                              "author": {"email": "lain@t"}}]}
    assert ("FAIL", "M4") in found(mini(tmp_path, **{".claude-plugin/marketplace.json": json.dumps(mp)}))


def test_m5_plugin_json_liar(tmp_path):
    assert ("FAIL", "M5") in found(mini(tmp_path, **{"src/plugins/demo/plugin.json": "{}"}))


@pytest.mark.parametrize("name", ["Demo_Market", "claude-plugins-official"])
def test_m6_nama_marketplace(tmp_path, name):
    mp = {"name": name, "plugins": [{"name": "demo", "source": "./src/plugins/demo"}]}
    assert ("FAIL", "M6") in found(mini(tmp_path, **{".claude-plugin/marketplace.json": json.dumps(mp)}))


def _committed(tmp_path):
    root = mini(tmp_path)
    git(root, "init", "-q", "-b", "main")
    git(root, "add", ".")
    git(root, "commit", "-qm", "init")
    return root


def test_m7_berubah_tanpa_bump(tmp_path):
    root = _committed(tmp_path)
    base = git(root, "rev-parse", "HEAD").strip()
    write_files(root, {"src/plugins/demo/skills/plan/references/rules.md": "# Rules v2\n"})
    assert ("FAIL", "M7") in found(root, base)
    pj = json.loads((root / "src/plugins/demo/.claude-plugin/plugin.json").read_text())
    pj["version"] = "0.1.1"
    write_files(root, {"src/plugins/demo/.claude-plugin/plugin.json": json.dumps(pj)})
    assert ("FAIL", "M7") not in found(root, base)


def test_m7_tanpa_perubahan_dan_ref_asing(tmp_path):
    root = _committed(tmp_path)
    assert ("FAIL", "M7") not in found(root, "HEAD")
    assert ("FAIL", "M7") in found(root, "tidak-ada")


def test_f1_frontmatter(tmp_path):
    p = "src/plugins/demo/skills/plan/SKILL.md"
    assert ("FAIL", "F1") in found(mini(tmp_path, **{p: "# tanpa frontmatter\n"}))
    assert ("FAIL", "F1") in found(mini(tmp_path, **{p: f"---\nname: plan\ndescription: {'x' * 1537}\n---\n"}))
    assert ("WARN", "F1") in found(mini(tmp_path, **{p: "---\nname: lain\ndescription: d\n---\n"}))
    assert ("WARN", "F1") in found(mini(tmp_path, **{p: "---\nname: plan\ndescription: d\nlevel: 3\n---\n"}))
    assert ("WARN", "F1") in found(mini(tmp_path, **{p: "---\nname: plan\ndescription: d\nmetadata: x\n---\n"}))


def test_f2_agent(tmp_path):
    p = "src/plugins/demo/agents/code-explorer.md"
    assert ("FAIL", "F2") in found(mini(tmp_path, **{p: "---\nname: x\n---\n"}))
    assert ("WARN", "F2") in found(mini(tmp_path, **{p: AGENT.replace("tools:", "permissionMode: plan\ntools:")}))


def test_f3_dipanggil_tanpa_user_invocable_false(tmp_path):
    p = "src/plugins/demo/skills/plan/SKILL.md"
    body = "---\nname: plan\ndescription: Dipanggil lead sesudah kontrak.\n{extra}---\n"
    assert ("WARN", "F3") in found(mini(tmp_path, **{p: body.format(extra="")}))
    assert ("WARN", "F3") not in found(mini(tmp_path, **{p: body.format(extra="user-invocable: false\n")}))


def test_r1_rujukan_hilang_dan_singkat(tmp_path):
    p = "src/plugins/demo/skills/plan/references/rules.md"
    assert ("FAIL", "R1") in found(mini(tmp_path, **{p: "Lihat `templates/brief.md`.\n"}))
    other = {"src/plugins/demo/skills/review/templates/brief.md": "# b\n",
             "src/plugins/demo/skills/review/SKILL.md": SKILL.replace("name: plan", "name: review")}
    assert ("WARN", "R1") in found(mini(tmp_path, **{p: "Lihat `templates/brief.md`.\n", **other}))


def test_r2_r3_plugin_root_literal(tmp_path):
    ref = "src/plugins/demo/skills/plan/references/rules.md"
    assert ("FAIL", "R2") in found(mini(tmp_path, **{ref: "Baca ${CLAUDE_PLUGIN_ROOT}/skills/x.md\n"}))
    assert ("FAIL", "R2") not in found(mini(tmp_path, **{ref: "| slot | hasil substitusi ${CLAUDE_PLUGIN_ROOT} |\n"}))
    agent = "src/plugins/demo/agents/code-explorer.md"
    assert ("WARN", "R3") in found(mini(tmp_path, **{agent: AGENT + "Baca ${CLAUDE_PLUGIN_ROOT}/x.md\n"}))


def test_s0_syntax_error(tmp_path):
    assert ("FAIL", "S0") in found(mini(tmp_path, **{"src/plugins/demo/skills/plan/scripts/check.py": "def (\n"}))


@pytest.mark.parametrize("code,hit", [
    ('p = Path.home() / ".gemini" / "x"\n', True),
    ('p = root / "src" / "plugins" / "demo"\n', True),
    ('p = "src/plugins/demo/x.md"\n', True),
    ('"""Tanpa fallback ke `~/.gemini` atau src/plugins/demo."""\n# src/plugins/demo\nx = 1\n', False),
])
def test_s1_path_dev_hanya_di_literal_kode(tmp_path, code, hit):
    got = ("FAIL", "S1") in found(mini(tmp_path, **{"src/plugins/demo/skills/plan/scripts/check.py": code}))
    assert got is hit


def test_s2_skrip_dirujuk_skill_hilang(tmp_path):
    assert ("FAIL", "S2") in found(mini(tmp_path, **{"src/plugins/demo/skills/plan/scripts/check.py": None}))


def test_h1_target_hook_hilang(tmp_path):
    assert ("FAIL", "H1") in found(mini(tmp_path, **{"src/plugins/demo/hooks/detect.py": None}))


def test_h1_eksekusi_langsung_wajib_100755(tmp_path):
    hooks = {"hooks": {"SessionStart": [{"hooks": [
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/gate.sh"}]}]}}
    root = mini(tmp_path, **{"src/plugins/demo/hooks/hooks.json": json.dumps(hooks),
                             "src/plugins/demo/hooks/gate.sh": "#!/bin/sh\n"})
    git(root, "init", "-q", "-b", "main")
    git(root, "add", ".")
    assert ("FAIL", "H1") in found(root)
    git(root, "update-index", "--chmod=+x", "src/plugins/demo/hooks/gate.sh")
    assert ("FAIL", "H1") not in found(root)


@pytest.mark.parametrize("path", ["src/plugins/demo/tests/test_x.py", "src/plugins/demo/conftest.py",
                                  "src/plugins/demo/skills/plan/scripts/test_check.py"])
def test_t1_test_di_dalam_plugin(tmp_path, path):
    assert ("FAIL", "T1") in found(mini(tmp_path, **{path: "x = 1\n"}))


def test_g1_bytecode(tmp_path):
    pyc = "src/plugins/demo/skills/plan/scripts/__pycache__/hilang.cpython-313.pyc"
    root = mini(tmp_path, **{pyc: ""})
    assert ("WARN", "G1") in found(root)
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-f", ".")
    assert ("FAIL", "G1") in found(root)


def _cli(root, *args):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run([sys.executable, str(LINT), "--root", str(root), *args],
                          capture_output=True, text=True, env=env)


def test_cli_ignore_strict_json(tmp_path):
    root = mini(tmp_path, **{"src/plugins/demo/plugin.json": "{}",
                             "src/plugins/demo/agents/code-explorer.md": AGENT + "${CLAUDE_PLUGIN_ROOT}\n"})
    assert _cli(root).returncode == 1                      # M5 FAIL
    assert _cli(root, "--ignore", "M5").returncode == 0     # sisa WARN R3
    assert _cli(root, "--ignore", "M5", "--strict").returncode == 1
    out = json.loads(_cli(root, "--json").stdout)
    assert out["fail"] == 1 and {i["check"] for i in out["items"]} == {"M5", "R3"}


def test_repo_ini_hanya_gagal_di_check_yang_dijadwalkan():
    """Repo sendiri: FAIL hanya boleh dari check yang ditunda (M3/M4 ← L7.1, M5 ← L7.2, R2 ← X1).

    Hapus ID dari DEFERRED di PR yang memperbaikinya, bersamaan dengan LINT_IGNORE di CI.
    """
    deferred = {"M3", "M4", "M5", "R2"}
    fails = {i["check"] for i in lint_mod.lint(REPO).items if i["level"] == "FAIL"}
    assert fails <= deferred, fails - deferred
