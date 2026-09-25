"""Parser manifest di `hooks/detect.py`, diuji langsung lewat impor."""
import importlib.util
import json
import sys
import time

import pytest

from conftest import PLUGINS, write_files

_spec = importlib.util.spec_from_file_location("detect", PLUGINS / "backenddev/hooks/detect.py")
detect = importlib.util.module_from_spec(_spec)
sys.modules["detect"] = detect
_spec.loader.exec_module(detect)


def test_go_requires_block_single_and_indirect(tmp_path):
    gomod = tmp_path / "go.mod"
    gomod.write_text(
        "module x\n\ngo 1.22\n\n"
        "require github.com/labstack/echo/v4 v4.12.0\n\n"
        "require (\n"
        "\tgithub.com/gofiber/fiber/v2 v2.52.0\n"
        "\tgithub.com/go-chi/chi/v5 v5.0.12 // pinned\n"
        "\tgithub.com/gin-gonic/gin v1.10.0 // indirect\n"
        ")\n")
    mods = detect.go_requires(gomod)
    assert "github.com/gin-gonic/gin" not in mods  # K6: // indirect diabaikan
    assert {"github.com/labstack/echo/v4", "github.com/gofiber/fiber/v2", "github.com/go-chi/chi/v5"} <= mods
    assert detect._go_match("github.com/gofiber/fiber/v2", "github.com/gofiber/fiber")
    assert detect._go_match("github.com/go-chi/chi/v5", "github.com/go-chi/chi")
    assert not detect._go_match("github.com/go-chi/chi-extra", "github.com/go-chi/chi")


CARGO = """
[package]
name = "api"

[dependencies]
serde = "1"

[dependencies.axum]
version = "0.7"

[target.'cfg(unix)'.dependencies]
warp = "0.3"

[dev-dependencies]
rocket = "0.5"
"""


def test_cargo_deps_tomllib_and_fallback(tmp_path, monkeypatch):
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(CARGO)
    with_toml = detect.cargo_deps(cargo)
    monkeypatch.setattr(detect, "tomllib", None)
    fallback = detect.cargo_deps(cargo)
    assert with_toml == fallback
    assert {"serde", "axum", "warp"} <= with_toml
    assert "rocket" not in with_toml


def test_pom_comment_ignored(tmp_path):
    pom = tmp_path / "pom.xml"
    pom.write_text('<project xmlns="http://maven.apache.org/POM/4.0.0"><!-- org.springframework.boot -->'
                   "<groupId>com.example</groupId></project>")
    assert not detect._pom_is_spring(pom)
    pom.write_text('<project xmlns="http://maven.apache.org/POM/4.0.0"><parent>'
                   "<groupId>org.springframework.boot</groupId></parent></project>")
    assert detect._pom_is_spring(pom)


def test_gradle_comment_ignored(tmp_path):
    g = tmp_path / "build.gradle.kts"
    g.write_text('// id("org.springframework.boot")\n/* org.springframework.boot */\nplugins { java }\n')
    assert not detect._gradle_is_spring(g)
    g.write_text('plugins { id("org.springframework.boot") version "3.3.0" }\n')
    assert detect._gradle_is_spring(g)


def test_gradle_version_catalog(tmp_path):
    write_files(tmp_path, {"gradle/libs.versions.toml":
                           '[plugins]\nspring-boot = { id = "org.springframework.boot", version = "3.3.0" }\n'})
    hits = detect.detect_backend(tmp_path)
    assert [(h.path, h.stack) for h in hits] == [("gradle/libs.versions.toml", "java-spring")]


def test_workspace_globs_pnpm_negation_skipped(tmp_path):
    write_files(tmp_path, {
        "pnpm-workspace.yaml": "packages:\n  - 'svc/*'\n  - '!svc/legacy'\n",
        "svc/api/package.json": json.dumps({"dependencies": {"koa": "^2"}}),
        "svc/legacy/package.json": json.dumps({"dependencies": {"express": "^4"}}),
    })
    assert "svc/*" in detect._workspace_globs(tmp_path)
    paths = [d.relative_to(tmp_path).as_posix() for d in detect.candidate_dirs(tmp_path)]
    assert "svc/api" in paths


def test_go_work_use_block(tmp_path):
    write_files(tmp_path, {"go.work": "go 1.22\n\nuse (\n\t./cmd/api\n\t./lib // shared\n)\n"})
    globs = detect._workspace_globs(tmp_path)
    assert "./cmd/api" in globs and "./lib" in globs


@pytest.mark.skipif(detect.tomllib is None, reason="members workspace Cargo hanya dibaca lewat tomllib (Python >= 3.11)")
def test_cargo_workspace_members(tmp_path):
    write_files(tmp_path, {
        "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n',
        "crates/server/Cargo.toml": '[package]\nname = "s"\n\n[dependencies]\naxum = "0.7"\n',
    })
    hits = detect.detect_backend(tmp_path)
    assert [(h.path, h.stack) for h in hits] == [("crates/server/Cargo.toml", "rust")]


def test_candidate_dirs_skip_list_and_cap(tmp_path):
    write_files(tmp_path, {"node_modules/x/package.json": json.dumps({"dependencies": {"express": "^4"}})})
    assert detect.detect_backend(tmp_path) == []
    for i in range(250):
        (tmp_path / "packages" / f"p{i:03d}").mkdir(parents=True)
    assert len(detect.candidate_dirs(tmp_path)) <= detect.MAX_CANDIDATES


def test_runtime_budget(tmp_path):
    for i in range(200):
        write_files(tmp_path, {f"packages/p{i:03d}/package.json": json.dumps({"dependencies": {"lodash": "^4"}})})
    start = time.monotonic()
    detect.evaluate(tmp_path, "backenddev")
    detect.evaluate(tmp_path, "frontenddev")
    assert time.monotonic() - start < 1.0


@pytest.mark.parametrize("deps,expected", [
    ({"dependencies": {"react": "^19"}, "devDependencies": {"vite": "^6"}}, ("react-vite", "")),
    ({"dependencies": {"react": "^18", "react-scripts": "5"}}, (None, "cra")),
    ({"dependencies": {"react": "^19"}}, (None, "react-tanpa-vite")),
    ({"devDependencies": {"svelte": "^4", "rollup": "^4"}}, (None, "svelte-tanpa-vite")),
    ({"dependencies": {"next": "^14", "react": "^18"}}, (None, "next")),
    ({"dependencies": {"expo": "^51"}}, ("react-native", "")),
    ({"devDependencies": {"@sveltejs/kit": "^2"}}, ("sveltekit", "")),
])
def test_frontend_from_package(tmp_path, deps, expected):
    pkg = tmp_path / "package.json"
    pkg.write_text(json.dumps(deps))
    assert detect.frontend_from_package(pkg) == expected


def test_frontend_vite_config_counts_as_vite(tmp_path):
    write_files(tmp_path, {"package.json": json.dumps({"dependencies": {"react": "^19"}}), "vite.config.ts": ""})
    assert detect.frontend_from_package(tmp_path / "package.json") == ("react-vite", "")


def test_package_json_with_bom(tmp_path):
    (tmp_path / "package.json").write_bytes(b"\xef\xbb\xbf" + json.dumps({"dependencies": {"express": "^4"}}).encode())
    assert detect.backend_from_package(tmp_path / "package.json", tmp_path) == "node"
