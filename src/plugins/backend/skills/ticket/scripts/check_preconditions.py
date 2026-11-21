#!/usr/bin/env python3
"""Ticket Precondition Validator (Langkah 40).

Prasyarat `backend:ticket` sebelum Fase 1: repo git, profil backend sah (penelusuran dipandu profil), templat kartu
ada di plugin, `backenddev/tickets/` dapat ditulis, dan tidak ada tiket yang ter-track (tiket tidak pernah di-commit,
40 T2). Tidak menuntut tree bersih, branch kerja, atau taskdir: membuat tiket tidak mengubah kode.

Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py`, di-bootstrap relatif terhadap berkas ini.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    BE_TICKETS_DIR,
    cli,
    find_repo_root,
    format_text,
    load_profile_index,
    plugin_file,
    probe_writable,
    to_json,
)

SKILL = "backend:ticket"
TEMPLATE = ("skills", "ticket", "templates", "ticket-template.md")


def _git(root: Path, *args: str):
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        return 255, str(exc)
    return r.returncode, r.stdout.strip()


class PreconditionChecker:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.results: List[Dict[str, Any]] = []

    def add(self, cid: int, name: str, ok: bool, summary: str, action: str = "") -> None:
        self.results.append({"id": cid, "name": name, "status": "PASS" if ok else "FAIL", "summary": summary,
                             "action": "" if ok else action})

    def run_all(self) -> bool:
        git_ok = _git(self.root, "rev-parse", "--is-inside-work-tree") == (0, "true")
        self.add(1, "Repo git", git_ok, "repo git terdeteksi" if git_ok else f"{self.root} bukan repo git",
                 "Jalankan `backend:ticket` dari dalam repo backend (bukan root multi-repo).")
        prof = load_profile_index(self.root)
        self.add(2, "Profil backend", prof.ok,
                 f"stack `{prof.data['stack']}`" if prof.ok else prof.error,
                 prof.action or "Jalankan `backend:profile`.")
        template = plugin_file(*TEMPLATE)
        self.add(3, "Templat kartu", template is not None,
                 "templat tersedia" if template else f"`{'/'.join(TEMPLATE)}` hilang dari plugin",
                 "Pasang ulang plugin backend.")
        writable, where = probe_writable(self.root / BE_TICKETS_DIR)
        self.add(4, "Folder tiket", writable,
                 f"`{BE_TICKETS_DIR}/` dapat ditulis" if writable else where,
                 f"Pulihkan izin tulis `{BE_TICKETS_DIR}/` atau induknya.")
        tracked: List[str] = []
        if git_ok:
            code, out = _git(self.root, "ls-files", "--", BE_TICKETS_DIR)
            tracked = out.splitlines() if code == 0 and out else []
        self.add(5, "Tiket tidak ter-track", not tracked,
                 "tidak ada tiket ter-track" if not tracked else f"{len(tracked)} berkas di bawah "
                                                                   f"`{BE_TICKETS_DIR}/` ter-track",
                 f"Tiket tidak pernah di-commit (Langkah 40): tanyakan user apakah `git rm -r --cached "
                 f"{BE_TICKETS_DIR}` boleh dijalankan; jangan dijalankan tanpa izin.")
        return all(r["status"] == "PASS" for r in self.results)


def main() -> int:
    ap = argparse.ArgumentParser(description="Prasyarat backend:ticket")
    ap.add_argument("--root", default=None, help="root repo; default root git dari cwd")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    checker = PreconditionChecker(Path(args.root) if args.root else find_repo_root())
    passed = checker.run_all()
    print(to_json(checker.root, checker.results) if args.json else format_text(SKILL, checker.results))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(cli(main))
