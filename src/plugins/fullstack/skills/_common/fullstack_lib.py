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

import fnmatch
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
ABAIKAN_FILE = f"{FULLSTACK_DIR}/abaikan"
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


# ------------------------------------------------------------------ abaikan (22)

def clean_pola(raw: str) -> Tuple[str, str]:
    """(pola bersih, galat). `/` di awal dan akhir dibuang; pola tanpa `/` mencocokkan nama di tingkat mana pun."""
    text = raw.strip()
    if text.startswith("~") or re.match(r"^[A-Za-z]:[\\/]", text) or "\\" in text:
        return "", "bukan path relatif root"
    pola = text.strip("/")
    if not pola:
        return "", "pola kosong"
    segs = pola.split("/")
    if any(seg in ("", ".", "..") for seg in segs):
        return "", "memuat segmen kosong, `.`, atau `..`"
    if len(segs) > 2:
        return "", "lebih dari dua tingkat (root hanya `<proyek>/<repo>`)"
    return pola, ""


def load_abaikan(root: Path) -> Dict[str, Any]:
    """{berkas, ada, pola, galat}. Berkas tak terbaca atau baris tidak sah tidak menghentikan scan (22 K4)."""
    out: Dict[str, Any] = {"berkas": ABAIKAN_FILE, "ada": False, "pola": [], "galat": []}
    path = root / ABAIKAN_FILE
    if not path.exists():
        return out
    out["ada"] = True
    text = read_text(path) if path.is_file() else None
    if text is None:
        out["galat"].append(f"`{ABAIKAN_FILE}` tidak terbaca; tanpa pengecualian")
        return out
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pola, err = clean_pola(line)
        if err:
            out["galat"].append(f"`{ABAIKAN_FILE}` baris {no} `{line}`: {err}")
        elif pola not in out["pola"]:
            out["pola"].append(pola)
    return out


def cocok_abaikan(rel: str, pola: List[str]) -> Optional[str]:
    """Pola pertama yang mengena `rel` (path relatif root), atau None."""
    name = rel.rsplit("/", 1)[-1]
    for p in pola:
        if fnmatch.fnmatchcase(rel if "/" in p else name, p):
            return p
    return None


def find_repos(root: Path, pola: Optional[List[str]] = None
               ) -> Tuple[List[Tuple[str, str, Path]], List[str], List[Dict[str, Any]]]:
    """([(dir relatif, proyek, path)], proyek/repo terpotong plafon, dikecualikan `.fullstack/abaikan`)."""
    pola = pola or []
    found: List[Tuple[str, str, Path]] = []
    excluded: List[Dict[str, Any]] = []
    for child in _children(root):
        hit = cocok_abaikan(child.name, pola)
        if _is_repo(child):
            if hit:
                excluded.append({"dir": child.name, "jenis": "repo", "pola": hit})
            else:
                found.append((child.name, ".", child))
            continue
        if hit:                                     # proyek dilewati utuh, tanpa membaca repo di dalamnya (22 K3)
            n = sum(1 for sub in _children(child) if _is_repo(sub))
            if n:
                excluded.append({"dir": child.name, "jenis": "proyek", "pola": hit, "repo": n})
            continue
        for sub in _children(child):
            if not _is_repo(sub):
                continue
            rel = f"{child.name}/{sub.name}"
            hit = cocok_abaikan(rel, pola)
            if hit:
                excluded.append({"dir": rel, "jenis": "repo", "pola": hit})
            else:
                found.append((rel, child.name, sub))
    kept, cut = found[:MAX_REPO], found[MAX_REPO:]
    return kept, sorted({proyek if proyek != "." else dir_ for dir_, proyek, _ in cut}), excluded


def alasan_dikecualikan(scan_result: Dict[str, Any], name: str) -> Optional[str]:
    """Pola yang mengecualikan repo atau proyek `name`, atau None."""
    for e in scan_result.get("dikecualikan", []):
        if e["dir"] == name or (e["jenis"] == "proyek" and name.startswith(e["dir"] + "/")):
            return e["pola"]
    return None


def bukan_di_root(scan_result: Dict[str, Any], kind: str, name: str) -> str:
    """Pesan untuk repo/proyek yang tidak ada di scan: dikecualikan, atau memang tidak ada."""
    pola = alasan_dikecualikan(scan_result, name)
    if pola:
        return f"{kind} `{name}` dikecualikan `{ABAIKAN_FILE}` (pola `{pola}`)"
    return f"{kind} `{name}` tidak ada di root"


def scan(root: Path) -> Dict[str, Any]:
    root = root.resolve()
    result: Dict[str, Any] = {"root": str(root), "mode": "WORKSPACE", "repo": [], "proyek": [], "terpotong": [],
                              "valid": 0, "dikecualikan": [], "abaikan": {"berkas": ABAIKAN_FILE, "ada": False,
                                                                          "pola": [], "galat": []}}
    if inside_git(root):
        result["mode"] = "DALAM_REPO"
        return result
    result["abaikan"] = load_abaikan(root)
    repos, cut, excluded = find_repos(root, result["abaikan"]["pola"])
    result["terpotong"] = cut
    result["dikecualikan"] = excluded
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
