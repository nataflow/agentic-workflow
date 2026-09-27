#!/usr/bin/env python3
"""Deteksi repo untuk hook SessionStart `backend` dan `frontend`.

Berkas ini IDENTIK byte-per-byte di `backend/hooks/detect.py` dan
`frontend/hooks/detect.py` (ditegakkan `test_detect_py_identik`). Teks
gerbang milik tiap plugin ada di `hooks/gate_text.py` masing-masing. Skrip
prasyarat mengimpor fungsi deteksi dari sini lewat
`skills/_common/precondition_lib.py`, sehingga vonis hook = vonis skrip.

Standard library saja. `tomllib` dipakai bila ada (Python >= 3.11).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Tuple

try:
    import tomllib  # Python >= 3.11
except ImportError:  # pragma: no cover
    tomllib = None

# Slug artefak di repo pengguna (`.claude/profile/<slug>/`, `<slug>/docs/`, `index.json` `plugin`),
# sengaja tetap nama lama walau plugin kini bernama `backend`/`frontend`.
PLUGINS = ("backenddev", "frontenddev")
PLUGIN_NAMES = {"backenddev": "backend", "frontenddev": "frontend"}
STACKS = {
    "backenddev": ("java-spring", "go", "node", "bun", "rust", "php", "php-codeigniter"),
    "frontenddev": ("react-vite", "react-native", "sveltekit", "svelte-vite"),
}
PROFILE_ROOT = Path(".claude") / "profile"          # Opsi A: <root>/.claude/profile/<plugin>/
PROFILE_FILES = {
    "backenddev": ("index.json", "stack.md", "module-structure.md", "domain-map.md",
                   "surface-map.md", "code-conventions.md", "anti-patterns.md",
                   "invariants.md", "commands.md"),
    "frontenddev": ("index.json", "stack.md", "structure.md", "surface-map.md",
                    "invariants.md", "commands.md", "layer-adoption.md", "visual.md",
                    "drift.md", "manual-notes.md"),
}
OPT_FILE = Path(".claude") / "workflow"              # L1.3: daftar plugin yang boleh menggerbangi repo
SKIP_DIRS = {"node_modules", "vendor", "target", "build", "dist", "out", ".git", "docs",
             "example", "examples", "fixtures", "test", "tests", "e2e", "playground", "demo"}
CONVENTIONAL = ("apps/*", "packages/*", "services/*")
MAX_CANDIDATES = 200

NODE_SERVER = {"@nestjs/core", "express", "fastify", "koa", "@hapi/hapi", "hono"}
BUN_MARKERS = ("bun.lockb", "bun.lock", "bunfig.toml")
GO_SERVER = ("github.com/gin-gonic/gin", "github.com/gofiber/fiber", "github.com/labstack/echo",
             "github.com/go-chi/chi", "github.com/gorilla/mux", "google.golang.org/grpc")
RUST_SERVER = {"axum", "actix-web", "rocket", "warp", "poem", "salvo"}
PHP_FRAMEWORK = {"laravel/framework", "symfony/framework-bundle", "slim/slim",
                 "laminas/laminas-mvc", "yiisoft/yii2"}
GRADLE_FILES = ("build.gradle", "build.gradle.kts", "gradle/libs.versions.toml")


@dataclass
class Hit:
    path: str   # manifest relatif root, mis. "apps/api/package.json"
    stack: str


@dataclass
class Profile:
    state: str                  # ABSENT | OK | INVALID_JSON | NO_STACK | UNKNOWN_STACK | INCOMPLETE | OTHER_OWNER
    location: str = ""          # own | legacy | ""
    stack: str = ""
    owner: str = ""
    missing: List[str] = field(default_factory=list)


@dataclass
class Verdict:
    plugin: str
    root: str
    emit: bool = False
    stack: str = ""
    source: str = ""            # "profile" atau path manifest
    profile: Profile = field(default_factory=lambda: Profile("ABSENT"))
    hits: List[Hit] = field(default_factory=list)
    out_of_scope: List[Hit] = field(default_factory=list)   # frontend: next/cra/tanpa-vite
    opted_out: bool = False


# ------------------------------------------------------------------ manifest

def _json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _keys(data: dict, *fields: str) -> Set[str]:
    out: Set[str] = set()
    for name in fields:
        block = data.get(name)
        if isinstance(block, dict):
            out.update(k for k in block if isinstance(k, str))
    return out


def backend_from_package(pkg: Path, root: Path) -> Optional[str]:
    """Backend hanya dari `dependencies`; devDependencies/overrides/peer tidak dihitung."""
    data = _json(pkg)
    if data is None:
        return None
    deps = _keys(data, "dependencies")
    bun = any((d / m).is_file() for d in {pkg.parent, root} for m in BUN_MARKERS)
    if not deps & {"@nestjs/core", "express"} and ("elysia" in deps or (bun and "hono" in deps)):
        return "bun"
    return "node" if deps & NODE_SERVER else None


def go_requires(gomod: Path) -> Set[str]:
    """Path modul di `require` (tunggal maupun blok), tanpa `// indirect`."""
    try:
        lines = gomod.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return set()
    mods: Set[str] = set()
    block = False
    for raw in lines:
        indirect = "// indirect" in raw
        line = raw.split("//", 1)[0].strip()
        if block:
            if line == ")":
                block = False
                continue
            body = line
        elif line.startswith("require"):
            body = line[len("require"):].strip()
            if body == "(":
                block = True
                continue
        else:
            continue
        parts = body.split()
        if len(parts) >= 2 and not indirect:
            mods.add(parts[0])
    return mods


def _go_match(mod: str, marker: str) -> bool:
    return mod == marker or (mod.startswith(marker + "/v") and mod[len(marker) + 2:].isdigit())


def cargo_deps(cargo: Path) -> Set[str]:
    """Nama crate di [dependencies], [workspace.dependencies], [target.*.dependencies]."""
    try:
        text = cargo.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()
    if tomllib is None:
        return _cargo_deps_fallback(text)
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return set()
    tables = [data.get("dependencies"), (data.get("workspace") or {}).get("dependencies")]
    tables += [t.get("dependencies") for t in (data.get("target") or {}).values() if isinstance(t, dict)]
    names: Set[str] = set()
    for table in tables:
        if isinstance(table, dict):
            for key, val in table.items():
                names.add(val.get("package", key) if isinstance(val, dict) else key)
    return names


def _cargo_deps_fallback(text: str) -> Set[str]:  # Python < 3.11
    names: Set[str] = set()
    in_deps = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("["):
            hdr = s.strip("[]").split("#", 1)[0].strip()
            in_deps = hdr in ("dependencies", "workspace.dependencies") or (
                hdr.startswith("target.") and hdr.endswith(".dependencies"))
            if hdr.startswith("dependencies."):
                names.add(hdr.split(".", 1)[1].strip('"'))
            continue
        m = re.match(r"([A-Za-z0-9_-]+)\s*=", s)
        if in_deps and m:
            names.add(m.group(1))
    return names


def backend_from_composer(path: Path) -> Optional[str]:
    data = _json(path)
    if data is None:
        return None
    req = {k.lower() for k in _keys(data, "require")}
    if "codeigniter4/framework" in req:
        return "php-codeigniter"
    return "php" if req & PHP_FRAMEWORK else None


def _pom_is_spring(pom: Path) -> bool:
    try:
        tree = ET.parse(pom)
    except (ET.ParseError, OSError):
        return False
    return any(el.tag.rsplit("}", 1)[-1] == "groupId"
               and (el.text or "").strip() == "org.springframework.boot" for el in tree.iter())


def _gradle_is_spring(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    lines = [ln.split("//", 1)[0].split("#", 1)[0] if path.suffix == ".toml" else ln.split("//", 1)[0]
             for ln in text.splitlines()]
    return re.search(r"org\.springframework\.boot", "\n".join(lines)) is not None


def frontend_from_package(pkg: Path) -> Tuple[Optional[str], str]:
    """(stack, alasan_di_luar_cakupan). Penanda Vite wajib untuk react-vite/svelte-vite."""
    data = _json(pkg)
    if data is None:
        return None, "manifest-rusak" if pkg.is_file() else ""
    deps = _keys(data, "dependencies", "devDependencies")
    if "next" in deps:
        return None, "next"
    if deps & {"react-native", "expo"}:
        return "react-native", ""
    if "@sveltejs/kit" in deps:
        return "sveltekit", ""
    vite = "vite" in deps or any(pkg.parent.glob("vite.config.*"))
    if "svelte" in deps:
        return ("svelte-vite", "") if vite else (None, "svelte-tanpa-vite")
    if "react" in deps:
        if vite:
            return "react-vite", ""
        return None, "cra" if "react-scripts" in deps else "react-tanpa-vite"
    return None, ""


# ------------------------------------------------------------------ monorepo

def _workspace_globs(root: Path) -> List[str]:
    globs: List[str] = []
    ws = (_json(root / "package.json") or {}).get("workspaces")
    if isinstance(ws, dict):
        ws = ws.get("packages")
    if isinstance(ws, list):
        globs += [w for w in ws if isinstance(w, str)]
    pnpm = root / "pnpm-workspace.yaml"
    if pnpm.is_file():
        inside = False
        for line in pnpm.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.match(r"^packages\s*:", line):
                inside = True
                continue
            m = re.match(r"""^\s*-\s*['"]?([^'"#]+?)['"]?\s*(#.*)?$""", line)
            if inside and m:
                globs.append(m.group(1))
            elif inside and line.strip() and not line[0].isspace():
                inside = False
    gowork = root / "go.work"
    if gowork.is_file():
        text = gowork.read_text(encoding="utf-8", errors="replace")
        for blk in re.findall(r"^use\s*\(([^)]*)\)", text, flags=re.M):
            globs += [ln.split("//", 1)[0].strip() for ln in blk.splitlines() if ln.strip()]
        globs += re.findall(r"^use\s+([^\s(]+)", text, flags=re.M)
    cargo = root / "Cargo.toml"
    if tomllib is not None and cargo.is_file():
        try:
            members = tomllib.loads(cargo.read_text(encoding="utf-8")).get("workspace", {}).get("members", [])
            globs += [m for m in members if isinstance(m, str)]
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            pass
    return globs


def candidate_dirs(root: Path) -> List[Path]:
    """Root, workspace terdeklarasi, apps/packages/services, lalu anak langsung root."""
    seen: Set[Path] = set()
    out: List[Path] = []

    def add(d: Path) -> None:
        if len(out) >= MAX_CANDIDATES or d in seen or not d.is_dir():
            return
        parts = d.relative_to(root).parts
        if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
            return
        seen.add(d)
        out.append(d)

    add(root)
    for pat in _workspace_globs(root) + list(CONVENTIONAL):
        pat = pat.strip().replace("**", "*")
        while pat.startswith("./"):
            pat = pat[2:]
        pat = pat.rstrip("/")
        if pat and not pat.startswith(("!", "/", "..")):
            for d in sorted(root.glob(pat)):
                add(d)
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        add(d)
    return out


def detect_backend(root: Path) -> List[Hit]:
    hits: List[Hit] = []
    for d in candidate_dirs(root):
        rel = lambda name: (d / name).relative_to(root).as_posix()  # noqa: E731
        if (d / "pom.xml").is_file() and _pom_is_spring(d / "pom.xml"):
            hits.append(Hit(rel("pom.xml"), "java-spring"))
        else:
            for g in GRADLE_FILES:
                if (d / g).is_file() and _gradle_is_spring(d / g):
                    hits.append(Hit(rel(g), "java-spring"))
                    break
        if (d / "go.mod").is_file() and any(_go_match(m, k) for m in go_requires(d / "go.mod") for k in GO_SERVER):
            hits.append(Hit(rel("go.mod"), "go"))
        stack = backend_from_package(d / "package.json", root) if (d / "package.json").is_file() else None
        if stack:
            hits.append(Hit(rel("package.json"), stack))
        if (d / "Cargo.toml").is_file() and cargo_deps(d / "Cargo.toml") & RUST_SERVER:
            hits.append(Hit(rel("Cargo.toml"), "rust"))
        stack = backend_from_composer(d / "composer.json") if (d / "composer.json").is_file() else None
        if stack:
            hits.append(Hit(rel("composer.json"), stack))
    return hits


def detect_frontend(root: Path) -> Tuple[List[Hit], List[Hit]]:
    hits: List[Hit] = []
    skipped: List[Hit] = []
    for d in candidate_dirs(root):
        pkg = d / "package.json"
        if not pkg.is_file():
            continue
        stack, why = frontend_from_package(pkg)
        rel = pkg.relative_to(root).as_posix()
        if stack:
            hits.append(Hit(rel, stack))
        elif why:
            skipped.append(Hit(rel, why))
    return hits, skipped


# ------------------------------------------------------------------ profil

def read_index(path: Path) -> Tuple[Optional[dict], str]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return None, "ABSENT"
    except (OSError, UnicodeDecodeError):         # berkas rusak/non-UTF-8 = profil tak sah, bukan crash
        return None, "INVALID_JSON"
    try:
        data = json.loads(raw)
    except ValueError:
        return None, "INVALID_JSON"
    return (data, "OK") if isinstance(data, dict) else (None, "INVALID_JSON")


def canonical_plugin(value: object) -> object:
    """Nama tampilan (`backend`/`frontend`) → kunci profil (`backenddev`/`frontenddev`); selain itu apa adanya.

    Sesudah rename fd08fc8 nilai `plugin` di `index.json` dapat berbunyi nama tampilan; `_grade` dulu
    memvonisnya milik plugin lain sementara `owner_of` menganggapnya milik sendiri (11 H29).
    """
    return {v: k for k, v in PLUGIN_NAMES.items()}.get(value, value) if isinstance(value, str) else value


def owner_of(data: dict) -> str:
    """Field `plugin` bila ada; profil lama tanpa field → dari keanggotaan `stack`."""
    plugin = canonical_plugin(data.get("plugin"))
    if plugin in PLUGINS:
        return plugin
    for plugin, stacks in STACKS.items():
        if data.get("stack") in stacks:
            return plugin
    return ""


def _grade(d: Path, plugin: str, data: dict, location: str) -> Profile:
    stack = data.get("stack")
    stack = stack.strip() if isinstance(stack, str) else ""
    owner = canonical_plugin(data.get("plugin")) or plugin
    if owner != plugin:
        return Profile("OTHER_OWNER", location, stack, owner)
    if not stack:
        return Profile("NO_STACK", location)
    if stack not in STACKS[plugin]:
        return Profile("UNKNOWN_STACK", location, stack, plugin)
    missing = [f for f in PROFILE_FILES[plugin] if not (d / f).is_file()]
    return Profile("INCOMPLETE" if missing else "OK", location, stack, plugin, missing)


def read_profile(root: Path, plugin: str) -> Profile:
    own = root / PROFILE_ROOT / plugin
    data, st = read_index(own / "index.json")
    if st == "INVALID_JSON":
        return Profile("INVALID_JSON", "own")
    if data is not None:
        return _grade(own, plugin, data, "own")
    legacy = root / PROFILE_ROOT
    data, st = read_index(legacy / "index.json")
    if st != "OK":
        return Profile(st, "legacy" if st == "INVALID_JSON" else "")
    owner = owner_of(data)
    if owner != plugin:
        return Profile("OTHER_OWNER", "legacy", str(data.get("stack", "")), owner)
    return _grade(legacy, plugin, data, "legacy")


# ------------------------------------------------------------------ vonis

def opted_out(root: Path, plugin: str) -> bool:
    try:
        words = (root / OPT_FILE).read_text(encoding="utf-8").split()
    except (OSError, UnicodeDecodeError):
        return False
    return plugin not in words and PLUGIN_NAMES[plugin] not in words


def evaluate(root: Path, plugin: str) -> Verdict:
    v = Verdict(plugin=plugin, root=str(root))
    if opted_out(root, plugin):
        v.opted_out = True
        return v
    v.profile = read_profile(root, plugin)
    if plugin == "backenddev":
        v.hits = detect_backend(root)
    else:
        v.hits, v.out_of_scope = detect_frontend(root)
    legacy_broken = v.profile.location == "legacy" and v.profile.state == "INVALID_JSON"
    if v.profile.state not in ("ABSENT", "OTHER_OWNER") and not legacy_broken:
        v.emit, v.stack, v.source = True, v.profile.stack, "profile"
    elif v.hits:
        v.emit, v.stack, v.source = True, v.hits[0].stack, v.hits[0].path
    return v


def resolve_root(cwd: str) -> Optional[Path]:
    p = Path(cwd).expanduser() if cwd else Path.cwd()
    if not p.is_dir():
        return None
    try:
        out = subprocess.run(["git", "-C", str(p), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=2)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return p.resolve()


def emit(text: str) -> None:
    payload = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Deteksi repo untuk hook SessionStart")
    ap.add_argument("--plugin", required=True, choices=PLUGINS + tuple(PLUGIN_NAMES.values()))
    ap.add_argument("--explain", action="store_true", help="cetak Verdict mentah (debug/test)")
    args = ap.parse_args(argv)
    args.plugin = {v: k for k, v in PLUGIN_NAMES.items()}.get(args.plugin, args.plugin)
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        data = {}
    cwd = data.get("cwd") if isinstance(data, dict) else None
    root = resolve_root(cwd if isinstance(cwd, str) else "")
    if root is None:
        return 0
    try:
        verdict = evaluate(root, args.plugin)
    except Exception as exc:  # noqa: BLE001 — gerbang yang diam paling mahal
        print(f"detect.py: {exc!r}", file=sys.stderr)
        if (root / PROFILE_ROOT / args.plugin).is_dir():
            emit(f"<{args.plugin}-gate>\nDeteksi hook gagal ({exc!r}). Jalankan skrip "
                 f"prasyarat skill secara manual sebelum merutekan kerja.\n</{args.plugin}-gate>")
        return 0
    if args.explain:
        print(json.dumps(asdict(verdict), ensure_ascii=False, indent=2))
        return 0
    if verdict.emit:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from gate_text import render  # teks milik plugin ini
            text = render(verdict)
        except Exception as exc:  # noqa: BLE001 — gerbang yang diam paling mahal (11 H36)
            print(f"detect.py: gate_text: {exc!r}", file=sys.stderr)
            text = (f"<{args.plugin}-gate>\nTeks gerbang gagal dirender ({exc!r}). Jalankan skrip prasyarat "
                    f"skill secara manual sebelum merutekan kerja.\n</{args.plugin}-gate>")
        emit(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
