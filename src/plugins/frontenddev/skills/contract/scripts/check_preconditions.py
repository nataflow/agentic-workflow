#!/usr/bin/env python3
"""Contract Precondition Validator.

Memvonis prasyarat `frontenddev:contract` sebelum Phase 0 dibuka lewat blok
bersama `design_gate_checks`: bentuk taskdir, akar `TASK.md` beserta pasangan
lane/sections-nya, `sections` non-kosong (lane non-MINOR), hop hulu ledger `## Chain` tercentang
dan kontennya utuh, profil beserta adapter stack, berkas template/referensi/
dispatcher, `CONTRACT.md` tertunda dari sesi lalu, dan kebersihan working tree.

`sections` dibaca dari frontmatter `TASK.md`, tidak diterima sebagai parameter:
gate tidak dapat dipanggil dengan cakupan yang berbeda dari yang dikunci akar.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Bootstrap path relatif terhadap berkas ini, bukan terhadap cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    design_gate_checks,
    find_repo_root,
    format_report,
    normalize_taskdir,
    report_json,
)

PROFILE_REQUIRED = ("index.json", "stack.md", "surface-map.md", "invariants.md", "layer-adoption.md")
PLUGIN_FILES = ("references/layer-patterns.md", "templates/contract-template.md", "dispatcher/explorer.md", "dispatcher/reviewer.md")


class PreconditionChecker:
    def __init__(self, taskdir: str, root: Optional[Path] = None,
                 profile_dir: Optional[str] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.profile_dir = self.root / (profile_dir or ".claude/profile")
        self.skill_dir = Path(__file__).resolve().parents[1]
        self.results: List[Dict[str, Any]] = []
        self.stack: str = ""
        self.sections: List[str] = []

    def _add(self, cid: int, name: str, status: str, summary: str, action: str = "") -> None:
        self.results.append({
            "id": cid, "name": name, "status": status,
            "summary": summary, "action": action,
        })

    def run_all(self) -> bool:
        """Jalankan 9 check; hanya `FAIL` yang menahan, `WARN` tidak."""
        self.stack, self.sections = design_gate_checks(
            self._add, self.root, self.taskdir_rel, self.profile_dir, self.skill_dir,
            required=None, row="CONTRACT", profile_required=PROFILE_REQUIRED,
            plugin_files=PLUGIN_FILES)
        return not any(r["status"] == "FAIL" for r in self.results)

    def format_text(self) -> str:
        return format_report("contract", self.results,
                             {"sections": ",".join(self.sections) or "-"})

    def to_json(self) -> str:
        return report_json(self.results, root=str(self.root), taskdir=self.taskdir_rel,
                           sections=self.sections, stack=self.stack)


def main() -> None:
    parser = argparse.ArgumentParser(description="Contract Preconditions Checker")
    parser.add_argument("--taskdir", required=True, help="path taskdir relatif root repo")
    parser.add_argument("--profile-dir", default=None, dest="profile_dir",
                        help="direktori profil, default .claude/profile")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()

    checker = PreconditionChecker(
        taskdir=args.taskdir,
        root=Path(args.root) if args.root else None,
        profile_dir=args.profile_dir,
    )
    ok = checker.run_all()
    print(checker.to_json() if args.json else checker.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
