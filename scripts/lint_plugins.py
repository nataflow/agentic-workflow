#!/usr/bin/env python3
"""Lint statis marketplace `agentic-workflow` (read-only, stdlib saja).

Pemakaian:
  python3 scripts/lint_plugins.py [--root DIR] [--strict] [--json] [--ignore M3,R2] [--base REF]

Exit 1 bila ada FAIL (atau WARN dengan --strict). `--base REF` mengaktifkan M7
(bump versi plugin yang berubah terhadap REF, dipakai di PR).
"""
import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

SKILL_FIELDS = {"name", "description", "when_to_use", "argument-hint", "arguments",
                "disable-model-invocation", "user-invocable", "allowed-tools", "disallowed-tools",
                "model", "effort", "context", "agent", "background", "hooks", "paths", "shell",
                "metadata", "license", "compatibility"}
AGENT_FIELDS = {"name", "description", "tools", "disallowedTools", "model", "permissionMode",
                "maxTurns", "skills", "mcpServers", "hooks", "memory", "background", "omitClaudeMd",
                "effort", "isolation", "color", "initialPrompt", "experimental"}
AGENT_IGNORED_IN_PLUGIN = {"hooks", "mcpServers", "permissionMode"}
DESC_CAP = 1536
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED_MARKETPLACES = {"claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
                         "claude-plugins-community", "claude-community", "anthropic-marketplace",
                         "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
                         "npm", "pip", "uv", "cargo", "github", "gh"}
REF_DIRS = {"references", "templates", "dispatcher", "stacks", "agents", "scripts"}
TOKEN = re.compile(r"`([^`\s]+)`")
PLACEHOLDER = re.compile(r"[<>{}*…]|\bNN\b|\bXX\b")
DEV_PATHS = re.compile(r"\.gemini|(^|/)src/plugins(/|$)")
PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
ROOT_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w@/-]+(?:\.[\w-]+)*)")
TEST_NAMES = re.compile(r"^(conftest\.py|test_.*\.py|.*_test\.py|pytest\.ini)$")
INVOKED = re.compile(r"^\s*(?:Dipanggil|Invoked)\b")


class Report:
    def __init__(self) -> None:
        self.items: List[dict] = []

    def add(self, level: str, check: str, where: str, msg: str) -> None:
        self.items.append({"level": level, "check": check, "where": where, "msg": msg})

    def count(self, level: str) -> int:
        return sum(1 for i in self.items if i["level"] == level)


def read_json(path: Path, rep: Report, where: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        rep.add("FAIL", "M1", where, f"JSON tidak valid: {exc}")
        return None


def frontmatter(text: str) -> Optional[dict]:
    """Subset YAML: `key: value` dan map satu tingkat (`key:` + baris berindentasi). None bila tanpa pagar."""
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    data: dict = {}
    current = None
    for raw in text[3:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1] in (" ", "\t") and current is not None:
            k, _, v = raw.strip().partition(":")
            if not isinstance(data[current], dict):
                data[current] = {}
            data[current][k.strip()] = v.strip()
            continue
        key, _, value = raw.partition(":")
        current = key.strip()
        data[current] = value.strip().strip('"').strip("'")
    return data


def git(root: Path, *args: str) -> Optional[str]:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                              check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def git_modes(root: Path) -> Dict[str, str]:
    """{path: mode} berkas ter-track; kosong bila bukan repo git."""
    out = git(root, "ls-files", "-s", "-z") or ""
    modes = {}
    for entry in filter(None, out.split("\0")):
        meta, _, path = entry.partition("\t")
        modes[path] = meta.split()[0]
    return modes


def lint(root: Path, base: Optional[str] = None) -> Report:
    rep = Report()
    mp = read_json(root / ".claude-plugin" / "marketplace.json", rep, ".claude-plugin/marketplace.json") or {}
    name = mp.get("name", "")
    if name and (not KEBAB.match(name) or name.lower() in RESERVED_MARKETPLACES):
        rep.add("FAIL", "M6", "marketplace.json", f"nama marketplace `{name}` tidak kebab-case atau tercadang")

    modes = git_modes(root)
    plugins = []
    for entry in mp.get("plugins", []):
        pname = entry.get("name", "?")
        src = (root / entry.get("source", "")).resolve()
        where = f"marketplace:{pname}"
        if not entry.get("source") or not src.is_dir():
            rep.add("FAIL", "M2", where, f"source `{entry.get('source')}` tidak ada")
            continue
        pj_path = src / ".claude-plugin" / "plugin.json"
        pj = read_json(pj_path, rep, rel(root, pj_path)) if pj_path.is_file() else None
        if pj is None:
            rep.add("WARN", "M2", where, "tanpa .claude-plugin/plugin.json (nama diturunkan dari direktori)")
            pj = {}
        plugins.append((pname, src, entry, pj))
        if pj.get("name") and pj["name"] != pname:
            rep.add("FAIL", "M2", where, f"nama entri `{pname}` ≠ plugin.json `{pj['name']}`")
        if "version" in entry and "version" in pj:
            same = entry["version"] == pj["version"]
            rep.add("FAIL", "M3", where,
                    f"version di dua tempat (plugin.json {pj['version']}, marketplace {entry['version']})"
                    + ("" if same else " — BERBEDA; Claude Code memakai plugin.json tanpa peringatan"))
        if "description" in entry and "description" in pj and entry["description"] != pj["description"]:
            rep.add("FAIL", "M4", where, "`description` entri ≠ plugin.json (listing menampilkan nilai entri)")
        ea, pa = entry.get("author") or {}, pj.get("author") or {}
        for k in ("name", "email"):
            if k in ea and k in pa and ea[k] != pa[k]:
                rep.add("FAIL", "M4", where, f"author.{k} entri `{ea[k]}` ≠ plugin.json `{pa[k]}`")
        if (src / "plugin.json").is_file():
            rep.add("FAIL", "M5", f"{rel(root, src)}/plugin.json",
                    "plugin.json liar di root plugin (loader hanya membaca .claude-plugin/plugin.json)")

    for _, pdir, _, _ in plugins:
        lint_plugin(root, pdir, rep, modes)
    if base:
        lint_version_bump(root, base, plugins, rep)
    return rep


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def resolve_ref(token: str, md: Path, pdir: Path) -> bool:
    t = token.replace(PLUGIN_ROOT + "/", "")
    t = re.sub(r"(:\d+(-\d+)?)+$|#.*$", "", t)
    skill_dir = next((p for p in md.parents if p.parent.name == "skills"), None)
    cands = [md.parent / t, pdir / t, pdir / "skills" / t]
    if skill_dir:
        cands.append(skill_dir / t)
    return any(c.exists() for c in cands)


def lint_plugin(root: Path, pdir: Path, rep: Report, modes: Dict[str, str]) -> None:
    prel = rel(root, pdir)
    # F1/F3 — frontmatter skill
    for skill_md in sorted(pdir.glob("skills/*/SKILL.md")):
        where = rel(root, skill_md)
        fm = frontmatter(skill_md.read_text(encoding="utf-8"))
        if fm is None:
            rep.add("FAIL", "F1", where, "frontmatter tidak ada/rusak")
            continue
        if not fm.get("description"):
            rep.add("FAIL", "F1", where, "description kosong")
        if fm.get("name") and fm["name"] != skill_md.parent.name:
            rep.add("WARN", "F1", where, f"name `{fm['name']}` ≠ nama direktori")
        total = len(fm.get("description", "")) + len(fm.get("when_to_use", ""))
        if total > DESC_CAP:
            rep.add("FAIL", "F1", where, f"description+when_to_use {total} > {DESC_CAP} karakter")
        for k in fm:
            if k not in SKILL_FIELDS:
                rep.add("WARN", "F1", where, f"field tak dikenal `{k}` (diabaikan diam-diam)")
        if "metadata" in fm and not isinstance(fm["metadata"], dict):
            rep.add("WARN", "F1", where, "metadata bukan map (dibuang Claude Code)")
        if INVOKED.match(fm.get("description", "")) and fm.get("user-invocable") != "false":
            rep.add("FAIL", "F3", where, "skill \"Dipanggil …\" tanpa `user-invocable: false` (L7.4)")
    # F2 — frontmatter agent
    for agent_md in sorted(pdir.glob("agents/*.md")):
        where = rel(root, agent_md)
        fm = frontmatter(agent_md.read_text(encoding="utf-8"))
        if fm is None or not fm.get("name") or not fm.get("description"):
            rep.add("FAIL", "F2", where, "frontmatter/name/description tidak ada")
            continue
        for k in fm:
            if k in AGENT_IGNORED_IN_PLUGIN:
                rep.add("WARN", "F2", where, f"`{k}` diabaikan untuk agent plugin")
            elif k not in AGENT_FIELDS:
                rep.add("WARN", "F2", where, f"field tak dikenal `{k}`")
    # R1/R2/R3 — rujukan dan placeholder di markdown
    for md in sorted(pdir.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        for no, line in enumerate(text.splitlines(), 1):
            where = f"{rel(root, md)}:{no}"
            for tok in TOKEN.findall(line):
                bare = tok.replace(PLUGIN_ROOT + "/", "")
                if not (set(bare.split("/")) & REF_DIRS or tok.endswith("SKILL.md")) or PLACEHOLDER.search(bare):
                    continue
                if not re.search(r"\.(md|py|sh|json)(:\d+.*)?$", tok):
                    continue
                if tok.startswith((".claude/", "~/", "/")):
                    continue
                if not resolve_ref(tok, md, pdir):
                    tail = re.sub(r"(:\d+(-\d+)?)+$", "", bare)
                    elsewhere = [rel(pdir, c) for c in pdir.rglob(Path(tail).name)
                                 if c.as_posix().endswith("/" + tail)]
                    if elsewhere:
                        rep.add("WARN", "R1", where, f"rujukan singkat `{tok}` tidak ada relatif skill ini; "
                                                     f"ada di {', '.join(elsewhere[:3])}")
                    else:
                        rep.add("FAIL", "R1", where, f"rujukan `{tok}` tidak ditemukan di plugin")
            if PLUGIN_ROOT in line and md.name != "SKILL.md" and "substitusi" not in line:
                if md.parent.name == "agents":
                    rep.add("FAIL", "R3", where, f"`{PLUGIN_ROOT}` literal di badan agent (X2)")
                else:
                    rep.add("FAIL", "R2", where, f"`{PLUGIN_ROOT}` literal di berkas non-SKILL.md (X1)")
    # S0/S1 — skrip
    for py in sorted(pdir.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        src = py.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, str(py))
        except SyntaxError as exc:
            rep.add("FAIL", "S0", rel(root, py), f"SyntaxError: {exc}")
            continue
        hits = dev_path_lines(tree)
        if hits:
            rep.add("FAIL", "S1", rel(root, py), f"path .gemini/repo-dev di {len(hits)} baris (mis. :{hits[0]})")
        # R4 — teks yang dicetak skrip disalin model ke Bash, tempat variabel itu tidak ada (X1)
        for no, line in enumerate(src.splitlines(), 1):
            if PLUGIN_ROOT in line:
                rep.add("FAIL", "R4", f"{rel(root, py)}:{no}", f"`{PLUGIN_ROOT}` literal di skrip; cetak path dari `__file__` (X1)")
    # S2 — skrip yang dirujuk SKILL.md ada
    for skill_md in sorted(pdir.glob("skills/*/SKILL.md")):
        for target in sorted(set(ROOT_PATH.findall(skill_md.read_text(encoding="utf-8")))):
            if target.endswith((".py", ".sh")) and not PLACEHOLDER.search(target) and not (pdir / target).is_file():
                rep.add("FAIL", "S2", rel(root, skill_md), f"skrip `{target}` tidak ada")
    # H1 — hooks
    hj = pdir / "hooks" / "hooks.json"
    if hj.is_file():
        data = read_json(hj, rep, rel(root, hj)) or {}
        for event, groups in (data.get("hooks") or {}).items():
            for g in groups:
                for h in g.get("hooks", []):
                    cmd = h.get("command", "")
                    for target in ROOT_PATH.findall(cmd):
                        path = pdir / target
                        if not path.is_file():
                            rep.add("FAIL", "H1", rel(root, hj), f"{event}: `{target}` tidak ada")
                            continue
                        # Dieksekusi langsung (bukan lewat `python3 …`/`sh …`) → wajib executable.
                        direct = re.match(r"^\s*[\"']?\$\{CLAUDE_PLUGIN_ROOT\}/", cmd) is not None
                        mode = modes.get(rel(root, path))
                        if direct and mode not in ("100755", None):
                            rep.add("FAIL", "H1", rel(root, path), "dieksekusi langsung tetapi mode git bukan 100755")
    # T1 — test/fixture tidak ikut terkirim ke pengguna
    for path in sorted(pdir.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if (path.is_dir() and path.name in ("tests", "fixtures")) or (path.is_file() and TEST_NAMES.match(path.name)):
            if path.is_file() and any(p.name in ("tests", "fixtures") for p in path.parents):
                continue  # sudah dilaporkan lewat direktorinya
            rep.add("FAIL", "T1", rel(root, path), "test/fixture di dalam plugin ikut tersalin ke cache pengguna; "
                                                   "taruh di tests/<plugin>/")
    # G1 — sisa cache lokal / bytecode ter-track
    for pyc in sorted(pdir.rglob("__pycache__/*.pyc")):
        source = pyc.parent.parent / (pyc.name.split(".")[0] + ".py")
        if not source.is_file():
            rep.add("WARN", "G1", rel(root, pyc), "bytecode tanpa sumber .py (sisa cache lokal)")
    for path in modes:
        if path.startswith(prel + "/") and ("__pycache__" in path or path.endswith(".pyc")):
            rep.add("FAIL", "G1", path, "bytecode ter-track di git")


def dev_path_lines(tree: ast.AST) -> List[int]:
    """Baris literal string kode (bukan docstring/komentar) yang menunjuk `.gemini` atau repo-dev."""
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    hits = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            if DEV_PATHS.search(node.value):
                hits.add(node.lineno)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            # `Path(...) / "src" / "plugins"`: operan kiri berakhir "src", kanan "plugins".
            left = node.left.right if isinstance(node.left, ast.BinOp) else node.left
            if all(isinstance(n, ast.Constant) for n in (left, node.right)) and \
                    (left.value, node.right.value) == ("src", "plugins"):
                hits.add(node.lineno)
    return sorted(hits)


def lint_version_bump(root: Path, base: str, plugins, rep: Report) -> None:
    """M7 — plugin yang berkasnya berubah terhadap `base` wajib menaikkan `version`."""
    if git(root, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}") is None:
        rep.add("FAIL", "M7", "--base", f"ref `{base}` tidak ditemukan")
        return
    mp_rel = ".claude-plugin/marketplace.json"
    try:
        old_mp = json.loads(git(root, "show", f"{base}:{mp_rel}") or "{}")
    except ValueError:
        old_mp = {}
    old_entries = {e.get("name"): e for e in old_mp.get("plugins", [])}
    for pname, pdir, entry, pj in plugins:
        prel = rel(root, pdir)
        changed = (git(root, "diff", "--name-only", f"{base}...HEAD", "--", prel) or "").split()
        changed += (git(root, "diff", "--name-only", "HEAD", "--", prel) or "").split()
        if not changed:
            continue
        pj_rel = f"{prel}/.claude-plugin/plugin.json"
        try:
            old_pj = json.loads(git(root, "show", f"{base}:{pj_rel}") or "{}")
        except ValueError:
            old_pj = {}
        old_entry = old_entries.get(pname)
        if old_entry is None and not old_pj:
            continue  # plugin baru
        old_v = old_pj.get("version") or (old_entry or {}).get("version")
        new_v = pj.get("version") or entry.get("version")
        if old_v and old_v == new_v:
            rep.add("FAIL", "M7", f"marketplace:{pname}",
                    f"{len(set(changed))} berkas berubah terhadap `{base}` tetapi version tetap {new_v}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--strict", action="store_true", help="WARN dihitung gagal")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ignore", default="", help="ID check dipisah koma, mis. M3,R2 (adopsi bertahap)")
    ap.add_argument("--base", default=None, help="ref pembanding untuk M7 (bump versi), mis. origin/main")
    args = ap.parse_args()
    rep = lint(Path(args.root).resolve(), args.base)
    ignored = {c.strip() for c in args.ignore.split(",") if c.strip()}
    rep.items = [i for i in rep.items if i["check"] not in ignored]
    if args.json:
        print(json.dumps({"fail": rep.count("FAIL"), "warn": rep.count("WARN"), "items": rep.items},
                         indent=2, ensure_ascii=False))
    else:
        for i in sorted(rep.items, key=lambda i: (i["check"], i["where"])):
            print(f"[{i['level']}] {i['check']} {i['where']}: {i['msg']}")
        print(f"LINT: {rep.count('FAIL')} FAIL, {rep.count('WARN')} WARN")
    sys.exit(1 if rep.count("FAIL") or (args.strict and rep.count("WARN")) else 0)


if __name__ == "__main__":
    main()
