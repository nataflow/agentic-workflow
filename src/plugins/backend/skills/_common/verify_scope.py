#!/usr/bin/env python3
"""Vonis mekanis berkas yang berubah vs scope brief.

  verify_scope.py --brief <brief> --commit <sha>   # backend: sesudah implementor commit
  verify_scope.py --brief <brief> --worktree       # frontend: sebelum architect commit

Scope sah = path `files_touched` frontmatter (frontend) atau baris `modify|create` tabel
**File** `## File scope` (backend), ditambah berkas brief itu sendiri dan `report-NN.md` di
direktori yang sama. Berkas `finding_source` frontmatter sah hanya bila diff-nya semata menambah
baris `> Status: FIXED`. Laci `.explore/` diabaikan, hanya di `<plugin>/docs/[<taskdir>/].explore/`.

PASS (exit 0): tiap berkas ada di scope. FAIL (exit 1): daftar berkas liar. Exit 2: argumen,
brief, atau git salah. Pemeriksaan simbol (Anchor) tetap milik `symbol_map.py`.
Salinan identik di skills/_common/ backend dan frontend. Hanya pustaka standar.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FIXED_LINE = re.compile(r"^\+> Status: FIXED\b")


def frontmatter(text: str) -> Dict[str, object]:
    """Subset YAML frontmatter: skalar, list inline `[a, b]`, list blok `- x`."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: Dict[str, object] = {}
    current: Optional[str] = None
    for raw in text[3:end].splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.lstrip().startswith("- ") and current:
            data.setdefault(current, [])
            if isinstance(data[current], list):
                data[current].append(line.split("- ", 1)[1].strip().strip("\"'"))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        current = None
        if value == "":
            data[key], current = [], key
        elif value.startswith("[") and value.endswith("]"):
            data[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
        else:
            data[key] = value.strip("\"'")
    return data


def file_scope_rows(text: str) -> List[str]:
    """Path baris `modify|create` di `## File scope` (tabel **Folder** tidak beraksi, jadi terlewati)."""
    m = re.search(r"^## File scope[ \t]*$", text, re.M)
    if not m:
        return []
    sec = text[m.end():]
    nxt = re.search(r"^## ", sec, re.M)
    sec = sec[:nxt.start()] if nxt else sec
    out = []
    for line in sec.splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(cols) >= 2 and cols[0].strip("`").lower() in ("modify", "create"):
            out.append(cols[1].strip("`").strip())
    return out


def scope_of(brief_text: str) -> Tuple[List[str], Optional[str]]:
    """(path scope, finding_source atau None) dari isi brief kedua plugin."""
    fm = frontmatter(brief_text)
    touched = fm.get("files_touched")
    paths = [p for p in touched if p] if isinstance(touched, list) else []
    paths += file_scope_rows(brief_text)
    fs = fm.get("finding_source")
    fs = fs if isinstance(fs, str) and fs.strip() and fs.strip() != "-" else None
    return paths, fs


def is_scratch(path: str) -> bool:
    """Laci code-explorer: `<plugin>/docs/.explore/**` atau `<plugin>/docs/<taskdir>/.explore/**`.

    Segmen `.explore` di tempat lain (mis. `internal/.explore/q.go`) adalah kode biasa.
    """
    seg = path.strip("/").split("/")
    return seg[:1] in (["backenddev"], ["frontenddev"]) and seg[1:2] == ["docs"] and ".explore" in seg[2:4]


def git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git {' '.join(args)} gagal")
    return out.stdout


def repo_root(cwd: Path) -> Path:
    return Path(git(cwd, "rev-parse", "--show-toplevel").strip()).resolve()


def rel(root: Path, p: str) -> str:
    """Path relatif root repo, dinormalisasi (`..` diselesaikan); di luar repo → ValueError."""
    full = (root / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
    if full != root and root not in full.parents:
        raise ValueError(f"path `{p}` di luar repo")
    return full.relative_to(root).as_posix()


def allowed_paths(root: Path, brief: Path) -> Tuple[set, Optional[str]]:
    """Himpunan path sah (relatif root) dan `finding_source` bila ada."""
    paths, fs = scope_of(brief.read_text(encoding="utf-8"))
    if not paths:
        raise ValueError("scope brief kosong atau tak terbaca (`files_touched` / `## File scope`)")
    b = rel(root, str(brief))
    allowed = {rel(root, p) for p in paths} | {b}
    nn = re.match(r"brief-(\d+)-", brief.name)
    if nn:
        allowed.add(rel(root, str(brief.parent / f"report-{nn.group(1)}.md")))
    return allowed, (rel(root, fs) if fs else None)


def only_fixed_marker(root: Path, path: str, commit: Optional[str]) -> bool:
    args = ["show", commit, "-U0", "--format=", "--", path] if commit else ["diff", "-U0", "HEAD", "--", path]
    lines = [l for l in git(root, *args).splitlines()
             if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    return bool(lines) and all(FIXED_LINE.match(l) for l in lines)


def changed(root: Path, commit: Optional[str]) -> List[str]:
    if commit:
        return [p for p in git(root, "show", "--name-only", "--format=", commit).splitlines() if p.strip()]
    out = git(root, "status", "--porcelain", "-uall")
    return [ln[3:].split(" -> ")[-1].strip('"') for ln in out.splitlines() if ln.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--brief", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--commit")
    g.add_argument("--worktree", action="store_true")
    a = ap.parse_args()
    try:
        root = repo_root(Path.cwd())
        brief = Path(a.brief) if Path(a.brief).is_absolute() else Path.cwd() / a.brief
        allowed, fs = allowed_paths(root, brief)
        touched = changed(root, a.commit)
        stray = []
        for p in touched:
            if p in allowed or is_scratch(p):
                continue
            if fs and p == fs and only_fixed_marker(root, p, a.commit):
                continue
            stray.append(p)
    except (OSError, ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    where = "worktree" if a.worktree else a.commit[:7]
    if stray:
        print(f"FAIL scope {where}: {len(stray)} berkas di luar scope: {', '.join(stray)}")
        return 1
    print(f"PASS scope {where}: {len(touched)} berkas, semua di scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
