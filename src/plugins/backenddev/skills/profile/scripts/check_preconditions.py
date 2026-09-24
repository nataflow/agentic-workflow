#!/usr/bin/env python3
"""Profile Precondition Validator.

Automates verification of repository preconditions before repository profiling execution.
Runs checks 1 through 5 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` untuk uji izin tulis, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional

MANIFEST_MAP = [
    (["pom.xml", "build.gradle", "build.gradle.kts"], "java-spring"),
    (["go.mod"], "go"),
    (["package.json"], "node"),  # or bun, resolved by stack adapter
    (["Cargo.toml"], "rust"),
    (["composer.json"], "php"),  # or php-codeigniter, resolved by stack adapter
]


# Helper izin tulis dipakai bersama lintas skrip prasyarat; rumah kanoniknya
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd — skrip dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    nearest_existing_ancestor as _nearest_existing_ancestor,
    probe_writable as _probe_writable,
)


class PreconditionChecker:
    def __init__(
        self,
        mode: Optional[str] = None,
        stack: Optional[str] = None,
        profile_dir: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.mode_arg = mode
        self.stack_arg = stack
        self.profile_dir_arg = profile_dir or ".claude/profile"
        self.results: List[Dict[str, Any]] = []

    def _find_repo_root(self) -> Path:
        """Find the git repository root or fallback to cwd."""
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            ).strip()
            if out and os.path.isdir(out):
                return Path(out)
        except Exception:
            pass
        return Path.cwd()

    def run_all(self) -> bool:
        """Run checks 1 through 5."""
        self._check_1_backend_manifest()
        self._check_2_stack_adapter()
        self._check_3_profile_dir_writable()
        self._check_4_git_worktree()
        self._check_5_references()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_backend_manifest(self):
        check_id = 1
        name = "Backend Manifest Detection"
        found_manifests = []

        # Scan root and 1-level submodules
        scan_dirs = [self.root]
        for child in self.root.iterdir():
            if child.is_dir() and not child.name.startswith(".") and child.name not in {"node_modules", "vendor", "target", "build"}:
                scan_dirs.append(child)

        detected_stacks = set()
        for d in scan_dirs:
            for manifests, stack_name in MANIFEST_MAP:
                for m in manifests:
                    if (d / m).exists():
                        rel = (d / m).relative_to(self.root)
                        found_manifests.append(str(rel))
                        detected_stacks.add(stack_name)

        if not found_manifests:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Tidak ditemukan berkas manifest backend (pom.xml, build.gradle, go.mod, package.json, Cargo.toml, composer.json)",
                "action": "Pastikan repositori target merupakan proyek backend yang memuat manifest sah.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Manifest backend terdeteksi: {', '.join(found_manifests[:4])}",
            "action": "",
        })

    def _check_2_stack_adapter(self):
        check_id = 2
        name = "Stack Adapter Availability"
        skill_dir = Path(__file__).resolve().parent.parent

        contract_file = skill_dir / "stacks" / "_CONTRACT.md"
        if not contract_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas stacks/_CONTRACT.md tidak ditemukan",
                "action": "Pastikan direktori stacks pada skill profile terpasang lengkap.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Koleksi adapter stack dan kontrak stacks/_CONTRACT.md tersedia",
            "action": "",
        })

    def _check_3_profile_dir_writable(self):
        check_id = 3
        name = "Profile Directory Write Access"
        target_dir = Path(self.profile_dir_arg)
        if not target_dir.is_absolute():
            target_dir = self.root / target_dir

        # Direktori profil dibuat saat profil ditulis, bukan oleh skrip check.
        ok, detail = _probe_writable(target_dir)
        if not ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori profil {target_dir} tidak memiliki izin tulis: {detail}",
                "action": "Periksa hak akses penulisan ke direktori .claude/profile/.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Direktori {self.profile_dir_arg} siap ditulis",
            "action": "",
        })

    def _check_4_git_worktree(self):
        check_id = 4
        name = "Git Inspection Access"
        try:
            inside = subprocess.check_output(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            ).strip()
            if inside != "true":
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Bukan repositori git yang valid",
                    "action": "Inisialisasi repositori git agar riwayat commit dan branch convention dapat dipindai.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Repositori git valid untuk pemindaian commit & branch conventions",
                "action": "",
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca status git: {e}",
                "action": "Pastikan git CLI tersedia.",
            })

    def _check_5_references(self):
        check_id = 5
        name = "Scan Guides & Templates"
        skill_dir = Path(__file__).resolve().parent.parent

        scan_guide = skill_dir / "references" / "scan-guide.md"
        conv_scan = skill_dir / "references" / "convention-scan.md"
        tpl_file = skill_dir / "templates" / "profile-template.md"

        missing = []
        if not scan_guide.exists():
            missing.append("references/scan-guide.md")
        if not conv_scan.exists():
            missing.append("references/convention-scan.md")
        if not tpl_file.exists():
            missing.append("templates/profile-template.md")

        if missing:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Berkas pendukung profile hilang: {', '.join(missing)}",
                "action": "Pastikan plugin backenddev:profile terpasang utuh.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Panduan pemindaian scan-guide.md, convention-scan.md, dan profile-template.md tersedia",
            "action": "",
        })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: profile [{status_label}] ({passed_count}/{total} passed)",
        ]
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<32} : {r['status']} ({r['summary']})")
            if r["status"] == "FAIL" and r["action"]:
                lines.append(f"    * Tindakan: {r['action']}")

        return "\n".join(lines)

    def to_json(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        return json.dumps({
            "status": "PASS" if all_passed else "FAIL",
            "passed_count": sum(1 for r in self.results if r["status"] == "PASS"),
            "total_count": len(self.results),
            "root": str(self.root),
            "profile_dir": self.profile_dir_arg,
            "checks": self.results,
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Profile Preconditions Checker")
    parser.add_argument("--mode", type=str, default=None, help="Execution mode (auto, generate, refresh)")
    parser.add_argument("--stack", type=str, default=None, help="Stack identifier override")
    parser.add_argument("--profile-dir", type=str, default=None, help="Target profile directory")
    parser.add_argument("--root", type=str, default=None, help="Target repo root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        mode=args.mode,
        stack=args.stack,
        profile_dir=args.profile_dir,
        target_root=target_root,
    )
    passed = checker.run_all()

    if args.json:
        print(checker.to_json())
    else:
        print(checker.format_text())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
