"""Pustaka bersama plugin `fullstack`: pemindaian root multi-repo, profil repo anak, dan `layanan.json`.

Root multi-repo = folder non-git yang menampung repo git, satu tingkat (`wms/api`) atau dua tingkat
(`company/wms/api`). Anak langsung ber-`.git` adalah repo berproyek `.`; anak tanpa `.git` adalah proyek,
dan anak langsungnya yang ber-`.git` adalah repo milik proyek itu. Scan tidak pernah turun ke dalam repo.

Profil dibaca dari `.claude/profile/backenddev/` dan `.claude/profile/frontenddev/` milik tiap repo, yang
ditulis `backend:profile` dan `frontend:profile`. `SKIP_DIRS` dan `STACKS` disalin dari `hooks/detect.py`
plugin backend/frontend (cache plugin terpisah, tidak bisa diimpor); test menjaga salinannya tetap sama.

Standard library saja.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PLUGINS = ("backenddev", "frontenddev")
PERAN = {"backenddev": "BE", "frontenddev": "FE"}
NAMA_PLUGIN = {"backenddev": "backend", "frontenddev": "frontend"}
STACKS = {
    "backenddev": ("java-spring", "go", "node", "bun", "rust", "php", "php-codeigniter"),
    "frontenddev": ("react-vite", "react-native", "sveltekit", "svelte-vite"),
}
SKIP_DIRS = {"node_modules", "vendor", "target", "build", "dist", "out", ".git", "docs",
             "example", "examples", "fixtures", "test", "tests", "e2e", "playground", "demo"}
PROFILE_ROOT = Path(".claude") / "profile"
PROFILE_MD = {
    "backenddev": ("stack.md", "module-structure.md", "domain-map.md", "surface-map.md",
                   "code-conventions.md", "anti-patterns.md", "invariants.md", "commands.md"),
    "frontenddev": ("stack.md", "structure.md", "surface-map.md", "invariants.md", "commands.md",
                    "layer-adoption.md", "visual.md", "drift.md", "manual-notes.md"),
}

MAX_REPO = 60               # K10
BATAS_TERTINGGAL = 50       # K14
FULLSTACK_DIR = ".fullstack"
EXPLORE_DIR = f"{FULLSTACK_DIR}/explore"
PETA_FILE = f"{FULLSTACK_DIR}/PETA.md"
LAYANAN_FILE = f"{FULLSTACK_DIR}/layanan.json"
STAMP = re.compile(r"^\d{10}$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ------------------------------------------------------------------ git & berkas

def git(cwd: Path, *args: str) -> Optional[str]:
    """stdout git tanpa spasi tepi, atau `None` bila gagal."""
    try:
        out = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def inside_git(path: Path) -> bool:
    return git(path, "rev-parse", "--is-inside-work-tree") == "true"


def head(repo: Path) -> Optional[str]:
    return git(repo, "rev-parse", "--short=7", "HEAD")


def read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def read_json_obj(path: Path) -> Tuple[Optional[dict], str]:
    """(data, `OK` | `ABSENT` | `INVALID_JSON`)."""
    if not path.is_file():
        return None, "ABSENT"
    raw = read_text(path)
    if raw is None:
        return None, "INVALID_JSON"
    try:
        data = json.loads(raw)
    except ValueError:
        return None, "INVALID_JSON"
    return (data, "OK") if isinstance(data, dict) else (None, "INVALID_JSON")


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def stamp() -> str:
    return datetime.now().strftime("%y%m%d%H%M")


# ------------------------------------------------------------------ profil

def canonical_plugin(value: Any) -> Any:
    """Nama tampilan (`backend`/`frontend`) → kunci profil; selain itu apa adanya."""
    return {v: k for k, v in NAMA_PLUGIN.items()}.get(value, value) if isinstance(value, str) else value


def _owner(data: dict) -> str:
    plugin = canonical_plugin(data.get("plugin"))
    if plugin in PLUGINS:
        return plugin
    for plugin, stacks in STACKS.items():
        if data.get("stack") in stacks:
            return plugin
    return ""


def _text_field(data: dict, key: str) -> str:
    value = data.get(key)
    return value.strip() if isinstance(value, str) else ""


def tertinggal(repo: Path, lokasi: str, source_root: str) -> Optional[int]:
    """Jumlah commit yang menyentuh `source_root` sesudah commit terakhir yang menyentuh profil (K14)."""
    last = git(repo, "log", "-1", "--format=%H", "--", lokasi)
    if not last:
        return None
    count = git(repo, "rev-list", "--count", f"{last}..HEAD", "--", source_root or ".")
    return int(count) if count and count.isdigit() else None


def read_profiles(repo: Path) -> List[Dict[str, Any]]:
    """Profil milik repo: satu butir per plugin, atau satu butir `LEGACY`; kosong bila tanpa profil."""
    out: List[Dict[str, Any]] = []
    for plugin in PLUGINS:
        lokasi = (PROFILE_ROOT / plugin).as_posix()
        data, state = read_json_obj(repo / lokasi / "index.json")
        if state == "ABSENT":
            continue
        entry: Dict[str, Any] = {"peran": PERAN[plugin], "plugin": plugin, "lokasi": lokasi, "status": state,
                                 "stack": "", "source_root": "", "tertinggal": None, "hilang": [], "info": {}}
        if data is not None:
            owner = canonical_plugin(data.get("plugin")) or plugin
            entry["stack"] = _text_field(data, "stack")
            entry["source_root"] = _text_field(data, "source_root")
            entry["info"] = {k: _text_field(data, k) for k in ("project", "architecture", "framework", "platform")
                             if _text_field(data, k)}
            if owner != plugin or not entry["stack"]:
                entry["status"] = "TIDAK_SAH"
            else:
                entry["status"] = "VALID"
                entry["hilang"] = [f for f in PROFILE_MD[plugin] if not (repo / lokasi / f).is_file()]
                entry["tertinggal"] = tertinggal(repo, lokasi, entry["source_root"])
        out.append(entry)
    if out:
        return out
    data, state = read_json_obj(repo / PROFILE_ROOT / "index.json")
    if state == "ABSENT":
        return []
    owner = _owner(data) if data is not None else ""
    return [{"peran": PERAN.get(owner, ""), "plugin": owner, "lokasi": PROFILE_ROOT.as_posix(), "status": "LEGACY",
             "stack": _text_field(data, "stack") if data else "", "source_root": "", "tertinggal": None,
             "hilang": [], "info": {}}]


def arahan_profil(dir_: str, prof: Optional[Dict[str, Any]]) -> str:
    """Kalimat arahan untuk profil yang tidak `VALID` atau tertinggal."""
    if prof is None:
        return f"bila repo ini backend atau frontend, `cd {dir_}` lalu jalankan `backend:profile` atau `frontend:profile`"
    skill = f"{NAMA_PLUGIN.get(prof['plugin'], 'backend/frontend')}:profile"
    mode = {"LEGACY": "MIGRATE", "INVALID_JSON": "REFRESH", "TIDAK_SAH": "REFRESH"}.get(prof["status"], "REFRESH")
    return f"`cd {dir_}` lalu jalankan `{skill}` mode {mode}"


# ------------------------------------------------------------------ scan

def _skip(d: Path) -> bool:
    try:
        return d.name.startswith(".") or d.name in SKIP_DIRS or not d.is_dir()
    except OSError:
        return True


def _is_repo(d: Path) -> bool:
    try:
        return (d / ".git").exists()
    except OSError:
        return False


def _children(d: Path) -> List[Path]:
    try:
        return [c for c in sorted(d.iterdir()) if not _skip(c)]
    except OSError:
        return []


def find_repos(root: Path) -> Tuple[List[Tuple[str, str, Path]], List[str]]:
    """([(dir relatif, proyek, path)], proyek/repo yang terpotong plafon)."""
    found: List[Tuple[str, str, Path]] = []
    for child in _children(root):
        if _is_repo(child):
            found.append((child.name, ".", child))
            continue
        for sub in _children(child):
            if _is_repo(sub):
                found.append((f"{child.name}/{sub.name}", child.name, sub))
    kept, cut = found[:MAX_REPO], found[MAX_REPO:]
    return kept, sorted({proyek if proyek != "." else dir_ for dir_, proyek, _ in cut})


def scan(root: Path) -> Dict[str, Any]:
    root = root.resolve()
    result: Dict[str, Any] = {"root": str(root), "mode": "WORKSPACE", "repo": [], "proyek": [], "terpotong": [],
                              "valid": 0}
    if inside_git(root):
        result["mode"] = "DALAM_REPO"
        return result
    repos, cut = find_repos(root)
    result["terpotong"] = cut
    per_proyek: Dict[str, Dict[str, Any]] = {}
    for dir_, proyek, path in repos:
        profil = read_profiles(path)
        result["repo"].append({"dir": dir_, "proyek": proyek, "head": head(path), "profil": profil})
        p = per_proyek.setdefault(proyek, {"nama": proyek, "repo": 0, "be": 0, "fe": 0, "tanpa_profil": 0,
                                           "tertinggal": 0})
        p["repo"] += 1
        valid = [x for x in profil if x["status"] == "VALID"]
        if not valid:
            p["tanpa_profil"] += 1
        for x in valid:
            result["valid"] += 1
            p["be" if x["peran"] == "BE" else "fe"] += 1
            if (x["tertinggal"] or 0) > BATAS_TERTINGGAL:
                p["tertinggal"] += 1
    result["proyek"] = [per_proyek[k] for k in sorted(per_proyek)]
    if not repos:
        result["mode"] = "KOSONG"
    return result


def repo_index(scan_result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {r["dir"]: r for r in scan_result["repo"]}


def peran_valid(repo: Dict[str, Any]) -> List[str]:
    return [p["peran"] for p in repo["profil"] if p["status"] == "VALID"]


# ------------------------------------------------------------------ layanan.json

def load_layanan(root: Path) -> Tuple[List[Dict[str, str]], str]:
    """(butir peta, galat). Berkas tidak ada = peta kosong tanpa galat."""
    data, state = read_json_obj(root / LAYANAN_FILE)
    if state == "ABSENT":
        return [], ""
    if state != "OK":
        return [], f"`{LAYANAN_FILE}` bukan JSON objek yang valid"
    peta = data.get("peta")
    if data.get("versi") != 1 or not isinstance(peta, list):
        return [], f"`{LAYANAN_FILE}` wajib berisi `versi: 1` dan daftar `peta`"
    out: List[Dict[str, str]] = []
    for i, item in enumerate(peta, 1):
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item.get(k)
                                                 for k in ("pemanggil", "target", "repo")):
            return [], f"`{LAYANAN_FILE}` butir {i} wajib punya `pemanggil`, `target`, dan `repo` berupa teks"
        prefix = item.get("prefix", "")
        if not isinstance(prefix, str):
            return [], f"`{LAYANAN_FILE}` butir {i}: `prefix` wajib teks"
        out.append({"pemanggil": item["pemanggil"], "target": item["target"], "repo": item["repo"],
                    "prefix": prefix})
    return out, ""


def save_layanan(root: Path, peta: List[Dict[str, str]]) -> None:
    items = []
    for item in sorted(peta, key=lambda x: (x["pemanggil"], x["target"])):
        row = {"pemanggil": item["pemanggil"], "target": item["target"], "repo": item["repo"]}
        if item.get("prefix"):
            row["prefix"] = item["prefix"]
        items.append(row)
    write_atomic(root / LAYANAN_FILE, json.dumps({"versi": 1, "peta": items}, indent=2, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------ keluaran

def cell(text: Any) -> str:
    """Isi sel tabel markdown satu baris."""
    return str(text).replace("\n", " ").replace("|", "\\|").strip()


def dump_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)
