"""Hook SessionStart `backenddev`/`frontenddev` (`hooks/detect.py`) — tabel kasus L1.1–L1.3.

ID kasus mengikuti `issues/01-profil-hook-koeksistensi.md` (B*, F* dari L1.2;
A* tata letak profil per plugin L1.1; Q* opt-out `.claude/workflow` L1.3).
"""
import filecmp
import json

import pytest

from conftest import PLUGINS, be_profile, fe_profile, git, run_hook, run_script, write_files

VITE = {"devDependencies": {"vite": "^6"}}
REACT_VITE = json.dumps({"dependencies": {"react": "^19", "react-dom": "^19"}, **VITE})
EXPRESS = json.dumps({"dependencies": {"express": "^4"}})
GIN_GOMOD = "module x\n\ngo 1.22\n\nrequire github.com/gin-gonic/gin v1.10.0\n"
FULLSTACK = {
    "package.json": json.dumps({"private": True, "workspaces": ["apps/*"]}),
    "apps/web/package.json": REACT_VITE,
    "apps/api/package.json": EXPRESS,
}


def _files(root, files):
    write_files(root, files)


# Tiap kasus: (nama direktori, pembangun fixture, subdirektori cwd, stdin khusus, vonis BE, vonis FE).
# Vonis: None = hook diam; dict = subset field `--explain` (emit=True tersirat).
def _b7(root):
    _files(root, {"package.json": EXPRESS, ".claude/profile/index.json": '{"stack":"no\tde"}\n'})


def _f4(root):
    _files(root, {"package.json": REACT_VITE})
    fe_profile(root, "react-vite")
    (root / ".claude/profile/frontenddev/index.json").write_text('{\n  "stack": "react-vite",\n}\n')


def _f5(root):
    _files(root, {"package.json": REACT_VITE})
    fe_profile(root, "react-vite")
    (root / ".claude/profile/frontenddev/index.json").write_text(
        '{\n  "meta": {\n    "stack": "react-native"\n  },\n  "stack": "react-vite"\n}\n')


def _a3(root):
    _files(root, FULLSTACK)
    be_profile(root, "node", source_root="apps/api")
    fe_profile(root, "react-vite")


def _a4(root):
    _files(root, FULLSTACK)
    be_profile(root, "node", legacy=True, source_root="apps/api")


def _a6(root):
    _files(root, {"package.json": REACT_VITE})
    be_profile(root, "node", extra={"plugin": "frontenddev"})


CASES = {
    "B1": ("b1", lambda r: _files(r, {"package.json": json.dumps(
        {"dependencies": {"react": "^19", "react-dom": "^19"}, "devDependencies": {"vite": "^6", "express": "^4"}})}),
        None, None, None, {"stack": "react-vite", "source": "package.json"}),
    "B2": ("b2", lambda r: _files(r, {"Cargo.toml": '[package]\nname = "poems-cli"\nversion = "0.1.0"\n\n[dependencies]\nclap = "4"\n'}),
        None, None, None, None),
    "B3": ("b3", lambda r: _files(r, {"go.mod": "module example.com/rpc\n\ngo 1.22\n\nrequire google.golang.org/grpc v1.66.0\n"}),
        None, None, {"stack": "go", "source": "go.mod"}, None),
    "B4": ("b4", lambda r: _files(r, {"package.json": json.dumps({"dependencies": {"hono": "^4", "@hono/node-server": "^1"}})}),
        None, None, {"stack": "node"}, None),
    "B5": ("b5", lambda r: _files(r, {"package.json": json.dumps({"private": True, "workspaces": ["apps/*"]}),
                                      "apps/api/package.json": EXPRESS}),
        None, None, {"stack": "node", "source": "apps/api/package.json"}, None),
    "B6": ('b6"q', lambda r: _files(r, {"package.json": EXPRESS}), None, None, {"stack": "node"}, None),
    "B6u": ("b6é", lambda r: _files(r, {"package.json": EXPRESS}), None, "ascii", {"stack": "node"}, None),
    "B7": ("b7", _b7, None, None,
           {"stack": "node", "source": "package.json", "state": "INVALID_JSON", "location": "legacy"}, None),
    "B8": ("b8", lambda r: _files(r, {"package.json": json.dumps({"dependencies": {"elysia": "^1"}}), "bun.lockb": ""}),
        None, None, {"stack": "bun"}, None),
    "B9": ("b9", lambda r: _files(r, {"package.json": json.dumps({"dependencies": {"hono": "^4"}}), "bun.lock": ""}),
        None, None, {"stack": "bun"}, None),
    "B10": ("b10", lambda r: _files(r, {"package.json": json.dumps(
        {"name": "ui-kit", "keywords": ["express", "koa"], "dependencies": {"lodash": "^4"}})}),
        None, None, None, None),
    "B11": ("b11", lambda r: _files(r, {"services/api/package.json": json.dumps({"dependencies": {"fastify": "^5"}})}),
        None, None, {"stack": "node", "source": "services/api/package.json"}, None),
    "B12": ("b12", lambda r: _files(r, {"Cargo.toml": '[package]\nname = "api"\n\n[dependencies]\nsalvo = "0.7"\n'}),
        None, None, {"stack": "rust", "source": "Cargo.toml"}, None),
    "F1": ("f1", lambda r: _files(r, {"package.json": json.dumps(
        {"dependencies": {"express": "^4", "react": "^19", "@react-email/components": "^0.0.25"}})}),
        None, None, {"stack": "node"}, None),
    "F2": ("f2", lambda r: _files(r, {"package.json": json.dumps({"dependencies": {"lodash": "^4"}, "overrides": {"react": "^19"}})}),
        None, None, None, None),
    "F3": ("f3", lambda r: _files(r, {"package.json": json.dumps({"name": "lib", "peerDependenciesMeta": {"react": {"optional": True}}})}),
        None, None, None, None),
    "F4": ("f4", _f4, None, None, None, {"state": "INVALID_JSON", "location": "own", "source": "profile"}),
    "F5": ("f5", _f5, None, None, None, {"stack": "react-vite", "source": "profile", "state": "OK", "location": "own"}),
    "F6": ("f6", lambda r: (_files(r, {"package.json": REACT_VITE}), (r / "src/features").mkdir(parents=True)),
        "src/features", None, None, {"stack": "react-vite", "source": "package.json"}),
    "F7": ("f7\\w", lambda r: _files(r, {"package.json": REACT_VITE}), None, None, None, {"stack": "react-vite"}),
    "F8": ("f8", lambda r: _files(r, {"package.json": json.dumps(
        {"dependencies": {"react": "^18", "react-dom": "^18", "react-scripts": "5.0.1"}})}),
        None, None, None, None),
    "F9": ("f9", lambda r: _files(r, {"package.json": json.dumps(
        {"devDependencies": {"svelte": "^4", "rollup": "^4", "rollup-plugin-svelte": "^7"}})}),
        None, None, None, None),
    "F10": ("f10", lambda r: _files(r, {"frontend/package.json": REACT_VITE, "backend/package.json": EXPRESS}),
        None, None, {"stack": "node", "source": "backend/package.json"},
        {"stack": "react-vite", "source": "frontend/package.json"}),
    "A1": ("a1", lambda r: (_files(r, {"go.mod": GIN_GOMOD}), be_profile(r, "go")),
        None, None, {"stack": "go", "source": "profile", "state": "OK", "location": "own"}, None),
    "A2": ("a2", lambda r: (_files(r, {"package.json": REACT_VITE}), fe_profile(r, "react-vite")),
        None, None, None, {"stack": "react-vite", "source": "profile", "state": "OK", "location": "own"}),
    "A3": ("a3", _a3, None, None,
           {"stack": "node", "source": "profile", "state": "OK", "location": "own"},
           {"stack": "react-vite", "source": "profile", "state": "OK", "location": "own"}),
    "A4": ("a4", _a4, None, None,
           {"stack": "node", "source": "profile", "state": "OK", "location": "legacy"},
           {"stack": "react-vite", "source": "apps/web/package.json", "state": "OTHER_OWNER", "location": "legacy"}),
    "A5": ("a5", lambda r: (_files(r, {"go.mod": GIN_GOMOD}), be_profile(r, "go", legacy=True)),
        None, None, {"stack": "go", "source": "profile", "state": "OK", "location": "legacy"}, None),
    "A6": ("a6", _a6, None, None, None, {"stack": "react-vite", "source": "package.json"}),
    "Q1": ("q1", lambda r: _files(r, {"package.json": EXPRESS, "repo-profile.md": "# p\n", ".claude/workflow": "quickdev\n"}),
        None, None, None, None),
    "Q2": ("q2", lambda r: _files(r, {"package.json": REACT_VITE, ".claude/workflow": "frontenddev\nquickdev\n"}),
        None, None, None, {"stack": "react-vite"}),
}


def build(make_repo, case_id):
    name, builder, sub, stdin_mode, _be, _fe = CASES[case_id]
    root = make_repo(name=name)
    builder(root)
    cwd = root / sub if sub else root
    stdin = None
    if stdin_mode == "ascii":
        stdin = json.dumps({"cwd": str(cwd)}, ensure_ascii=True)
    return root, cwd, stdin


def explain(plugin, cwd, stdin):
    proc, _ = run_hook(plugin, cwd, stdin=stdin, explain=True)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def assert_verdict(v, expected):
    if expected is None:
        assert v["emit"] is False, v
        return
    assert v["emit"] is True, v
    for key, want in expected.items():
        got = v["profile"][key] if key in ("state", "location") else v[key]
        assert got == want, (key, v)


@pytest.mark.parametrize("case_id", list(CASES))
def test_case(make_repo, case_id):
    _root, cwd, stdin = build(make_repo, case_id)
    for plugin, expected in (("backenddev", CASES[case_id][4]), ("frontenddev", CASES[case_id][5])):
        assert_verdict(explain(plugin, cwd, stdin), expected)
        proc, payload = run_hook(plugin, cwd, stdin=stdin)
        assert proc.returncode == 0, proc.stderr
        if expected is None:
            assert payload is None, payload
        else:
            assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
            assert payload["hookSpecificOutput"]["additionalContext"]


def test_detect_py_identik():
    assert filecmp.cmp(PLUGINS / "backenddev/hooks/detect.py", PLUGINS / "frontenddev/hooks/detect.py",
                       shallow=False)


def test_migrate_profile_identik():
    assert filecmp.cmp(PLUGINS / "backenddev/skills/profile/scripts/migrate_profile.py",
                       PLUGINS / "frontenddev/skills/profile/scripts/migrate_profile.py", shallow=False)


FE_PROFILE_SCRIPT = PLUGINS / "frontenddev/skills/profile/scripts/check_preconditions.py"
BE_PROFILE_SCRIPT = PLUGINS / "backenddev/skills/profile/scripts/check_preconditions.py"


@pytest.mark.parametrize("case_id", [c for c in CASES if c[0] in "BF"])
def test_hook_equals_script_verdict(make_repo, case_id):
    root, cwd, stdin = build(make_repo, case_id)
    fe = explain("frontenddev", cwd, stdin)
    if fe["source"] != "profile":
        out = json.loads(run_script(FE_PROFILE_SCRIPT, "--json", "--root", str(root)).stdout)
        check1 = next(c for c in out["checks"] if c["id"] == 1)
        script_stack = out["stack"] if check1["status"] != "FAIL" else ""
        assert script_stack == (fe["stack"] if fe["emit"] else ""), (out, fe)
    be = explain("backenddev", cwd, stdin)
    if be["source"] != "profile":
        out = json.loads(run_script(BE_PROFILE_SCRIPT, "--json", "--root", str(root)).stdout)
        check1 = next(c for c in out["checks"] if c["id"] == 1)
        assert (check1["status"] == "PASS") == be["emit"], (out, be)


@pytest.mark.parametrize("plugin", ["backenddev", "frontenddev"])
def test_output_valid_json_with_control_chars(make_repo, plugin):
    root = make_repo({"package.json": EXPRESS if plugin == "backenddev" else REACT_VITE})
    prof = (be_profile if plugin == "backenddev" else fe_profile)(root, "node" if plugin == "backenddev" else "react-vite")
    (prof / "index.json").write_text('{"plugin": "%s", "stack": "a\tb\x01c"}\n' % plugin)
    proc, payload = run_hook(plugin, root)
    assert proc.returncode == 0
    assert payload is not None  # json.loads berhasil di run_hook


@pytest.mark.parametrize("name", ['q"uote', "back\\slash"])
def test_cwd_escaped_quote_and_backslash(make_repo, name):
    root = make_repo({"package.json": EXPRESS}, name=name)
    _proc, payload = run_hook("backenddev", root)
    assert payload is not None


def test_cwd_subdirectory_resolves_toplevel(make_repo):
    root = make_repo({"package.json": REACT_VITE, "src/a/b/.keep": ""})
    v = explain("frontenddev", root / "src/a/b", None)
    assert v["emit"] and v["root"] == str(root.resolve())


def test_non_git_dir_uses_cwd(make_repo):
    root = make_repo({"package.json": EXPRESS}, git_init=False)
    assert explain("backenddev", root, None)["emit"] is True


@pytest.mark.parametrize("plugin", ["backenddev", "frontenddev"])
def test_malformed_stdin_is_silent(plugin, tmp_path):
    proc = run_script(PLUGINS / plugin / "hooks/detect.py", "--plugin", plugin, stdin="not json", cwd=tmp_path)
    assert proc.returncode == 0 and proc.stdout == ""


# --------------------------------------------------------------- L1.1 (teks)

def test_backend_profile_silences_frontend_hook(make_repo):
    root = make_repo({"go.mod": GIN_GOMOD})
    be_profile(root, "go")
    proc, payload = run_hook("frontenddev", root)
    assert proc.returncode == 0 and payload is None


def test_frontend_profile_silences_backend_hook(make_repo):
    root = make_repo({"package.json": REACT_VITE})
    fe_profile(root, "react-vite")
    proc, payload = run_hook("backenddev", root)
    assert proc.returncode == 0 and payload is None


def test_fullstack_two_profiles_both_ok(make_repo):
    root = make_repo(FULLSTACK)
    be_profile(root, "node", source_root="apps/api")
    fe_profile(root, "react-vite")
    for plugin in ("backenddev", "frontenddev"):
        v = explain(plugin, root, None)
        assert v["emit"] and v["profile"]["state"] == "OK" and v["profile"]["location"] == "own"


def test_legacy_own_profile_offers_migrate(make_repo):
    root = make_repo({"go.mod": GIN_GOMOD})
    be_profile(root, "go", legacy=True)
    _proc, payload = run_hook("backenddev", root)
    text = payload["hookSpecificOutput"]["additionalContext"]
    assert "MIGRATE" in text
    assert "mode REFRESH" not in text


def test_legacy_foreign_profile_ignored(make_repo):
    root = make_repo(FULLSTACK)
    be_profile(root, "node", legacy=True, source_root="apps/api")
    _proc, payload = run_hook("frontenddev", root)
    text = payload["hookSpecificOutput"]["additionalContext"]
    assert "apps/web/package.json" in text
    assert "milik `backenddev`" in text


# --------------------------------------------------------------- L1.3 (opt-out)

@pytest.mark.parametrize("content,expect_fe", [("quickdev", False), ("frontenddev quickdev", True)],
                         ids=["quickdev", "frontenddev-quickdev"])
def test_opt_out_workflow_file(make_repo, content, expect_fe):
    root = make_repo({"package.json": REACT_VITE, "apps/api/package.json": EXPRESS,
                      ".claude/workflow": content + "\n"})
    assert explain("backenddev", root, None)["emit"] is False
    assert explain("frontenddev", root, None)["emit"] is expect_fe


def test_opt_out_workflow_dir_is_ignored(make_repo):
    root = make_repo({"package.json": EXPRESS})
    (root / ".claude/workflow").mkdir(parents=True)
    v = explain("backenddev", root, None)
    assert v["emit"] is True and v["opted_out"] is False


def test_git_toplevel_used_for_profile(make_repo):
    """Profil dibaca dari toplevel git walau sesi dimulai di subdirektori."""
    root = make_repo({"go.mod": GIN_GOMOD, "internal/x/.keep": ""})
    be_profile(root, "go")
    git(root, "add", "-A")
    v = explain("backenddev", root / "internal/x", None)
    assert v["source"] == "profile" and v["profile"]["location"] == "own"
