#!/usr/bin/env python3
"""Pindahkan profil lama `.claude/profile/` ke `.claude/profile/<plugin>/` (mode MIGRATE).

Hanya berkas profil milik plugin ini yang dipindah (`git mv` bila ter-track,
rename biasa bila belum). Berkas lain di `.claude/profile/` dilaporkan sebagai
sisa dan tidak disentuh — bisa jadi milik plugin lain. Skrip ini tidak
meng-commit; commit milik fase kerja skill `profile`.

Isi berkas ini sama di `backenddev` dan `frontenddev`: nama plugin dan daftar
berkas profil dibaca dari `skills/_common/precondition_lib.py` dan
`hooks/detect.py` plugin yang memuatnya.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import PLUGIN, _detect  # noqa: E402


def _git_mv(root: Path, src: Path, dst: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "mv", "--",
             src.relative_to(root).as_posix(), dst.relative_to(root).as_posix()],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def migrate(root: Path, plugin: str = PLUGIN) -> Tuple[List[str], List[str]]:
    """Pindahkan profil lama milik `plugin`. Mengembalikan (dipindah, sisa)."""
    legacy = root / _detect.PROFILE_ROOT
    target = legacy / plugin
    data, state = _detect.read_index(legacy / "index.json")
    if state != "OK" or _detect.owner_of(data) != plugin:
        raise SystemExit(f"MIGRATE FAIL: .claude/profile/index.json bukan milik {plugin}")
    if (target / "index.json").exists():
        raise SystemExit(f"MIGRATE FAIL: .claude/profile/{plugin}/index.json sudah ada; "
                         "lokasi baru tidak ditimpa")
    target.mkdir(parents=True, exist_ok=True)
    moved: List[str] = []
    for name in _detect.PROFILE_FILES[plugin]:
        src = legacy / name
        if not src.is_file():
            continue
        if not _git_mv(root, src, target / name):  # berkas belum ter-track
            src.rename(target / name)
        moved.append(name)
    data["plugin"] = plugin
    (target / "index.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    leftovers = sorted(p.name for p in legacy.iterdir() if p.is_file())
    return moved, leftovers


def _find_root() -> Path:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      stderr=subprocess.DEVNULL, universal_newlines=True).strip()
        if out:
            return Path(out)
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd()


def main() -> None:
    parser = argparse.ArgumentParser(description=f"Migrasi profil {PLUGIN} ke .claude/profile/{PLUGIN}/")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()
    root = (Path(args.root) if args.root else _find_root()).resolve()
    moved, leftovers = migrate(root)
    history = "git log --oneline -- .claude/profile/index.json"
    if args.json:
        print(json.dumps({"plugin": PLUGIN, "target": f".claude/profile/{PLUGIN}",
                          "moved": moved, "leftovers": leftovers, "history": history}, indent=2))
        return
    print(f"MIGRATE OK: {len(moved)} berkas dipindah ke .claude/profile/{PLUGIN}/: {', '.join(moved)}")
    if leftovers:
        print(f"Sisa di .claude/profile/ (bukan milik {PLUGIN} — tidak disentuh): {', '.join(leftovers)}")
    print(f"Profil plugin lain yang pernah tertimpa dapat dipulihkan dari riwayat: `{history}`")


if __name__ == "__main__":
    main()
