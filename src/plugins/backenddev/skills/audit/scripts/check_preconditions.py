#!/usr/bin/env python3
"""Audit Precondition Validator.

Automates verification of repository preconditions before audit sweep execution.
Runs checks 1 through 6 in a single pass and produces a compact, actionable report.
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
        target_scope: Optional[str] = None,
        dimensions: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.target_scope_arg = target_scope
        self.dimensions_arg = dimensions
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
        """Run checks 1 through 6."""
        self._check_1_source_root()
        self._check_2_profile_config()
        self._check_3_stack_adapter()
        self._check_4_issues_directory()
        self._check_5_references_and_template()
        self._check_6_target_scope()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_source_root(self):
        check_id = 1
        name = "Source Root Read Access"
        profile_dir = self.root / ".claude" / "profile"
        index_file = profile_dir / "index.json"

        src_rel = "src"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("source_root"):
                        src_rel = data["source_root"]
            except Exception:
                pass

        src_dir = self.root / src_rel
        if not src_dir.exists() and not (self.root / "src").exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori kode sumber tidak ditemukan di {src_rel} maupun src/",
                "action": "Pastikan repositori target memuat kode sumber backend di root atau konfigurasi profil.",
            })
            return

        target_check = src_dir if src_dir.exists() else (self.root / "src")
        if not os.access(target_check, os.R_OK):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Izin baca ke direktori kode sumber {target_check} ditolak",
                "action": "Periksa hak akses direktori kode sumber.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Akses baca kode sumber terverifikasi di {target_check.relative_to(self.root)}",
            "action": "",
        })

    def _check_2_profile_config(self):
        check_id = 2
        name = "Profile Configuration"
        profile_dir = self.root / ".claude" / "profile"
        index_file = profile_dir / "index.json"

        if not index_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas .claude/profile/index.json tidak ditemukan",
                "action": "Jalankan skill `backenddev:profile` untuk membuat profil repositori.",
            })
            return

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data.get("stack"):
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Field 'stack' tidak ditemukan pada index.json",
                    "action": "Jalankan `backenddev:profile` untuk memperbarui field stack.",
                })
                return
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Format JSON corrupt pada index.json: {e}",
                "action": "Perbaiki berkas index.json.",
            })
            return

        required_docs = ["module-structure.md", "anti-patterns.md", "invariants.md"]
        missing_docs = [doc for doc in required_docs if not (profile_dir / doc).exists()]
        if missing_docs:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Dokumen profil wajib hilang: {', '.join(missing_docs)}",
                "action": "Jalankan `backenddev:profile` untuk melengkapi dokumen profil.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Profil valid (stack: {data.get('stack')})",
            "action": "",
        })

    def _check_3_stack_adapter(self):
        check_id = 3
        name = "Stack Adapter Resolution"
        profile_dir = self.root / ".claude" / "profile"
        index_file = profile_dir / "index.json"
        stack_id = "unknown"

        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    stack_id = data.get("stack", "unknown")
            except Exception:
                pass

        candidate_paths = [
            self.root / "src" / "plugins" / "backenddev" / "skills" / "profile" / "stacks" / f"{stack_id}.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "profile" / "stacks" / f"{stack_id}.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "profile" / "stacks" / f"{stack_id}.md",
            Path(__file__).resolve().parent.parent.parent / "profile" / "stacks" / f"{stack_id}.md",
        ]

        found = any(p.exists() for p in candidate_paths)
        if not found:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Berkas adapter stacks/{stack_id}.md tidak ditemukan",
                "action": f"Pastikan plugin backenddev memuat adapter untuk stack '{stack_id}'.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Adapter stack '{stack_id}' tersedia",
            "action": "",
        })

    def _check_4_issues_directory(self):
        check_id = 4
        name = "Issues Directory Write Access"
        issues_dir = self.root / "backenddev" / "issues"

        # Direktori dibuat saat laporan diterbitkan, bukan oleh skrip check.
        ok, detail = _probe_writable(issues_dir)
        if not ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori backenddev/issues/ tidak dapat ditulis: {detail}",
                "action": "Pastikan direktori backenddev/issues/ memiliki izin tulis untuk penerbitan laporan.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Direktori backenddev/issues/ siap ditulis",
            "action": "",
        })

    def _check_5_references_and_template(self):
        check_id = 5
        name = "Dimensions Ref & Issues Template"
        skill_dir = Path(__file__).resolve().parent.parent

        dim_ref = skill_dir / "references" / "dimensions.md"
        tpl_file = skill_dir / "templates" / "issues-template.md"

        missing = []
        if not dim_ref.exists():
            missing.append("references/dimensions.md")
        if not tpl_file.exists():
            missing.append("templates/issues-template.md")

        if missing:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Berkas pendukung audit hilang: {', '.join(missing)}",
                "action": "Pastikan berkas plugin backenddev:audit terpasang utuh.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Referensi dimensions.md dan issues-template.md tersedia",
            "action": "",
        })

    def _check_6_target_scope(self):
        check_id = 6
        name = "Target Scope Validation"

        if not self.target_scope_arg:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Parameter target_scope kosong, evaluasi cakupan default di Fase 0",
                "action": "",
            })
            return

        # Check if target scope looks like a diff or PR
        scope_str = self.target_scope_arg.strip()
        if re.search(r"(\.\.|origin/|refs/pull|pr/)", scope_str):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"target_scope '{scope_str}' menunjuk diff branch/PR, bukan kode mendarat",
                "action": "Gunakan subagent `code-reviewer` untuk penilaian diff, audit hanya menyapu path direktori/modul nyata.",
            })
            return

        scope_path = Path(scope_str)
        if not scope_path.is_absolute():
            scope_path = self.root / scope_path

        if not scope_path.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Path target_scope '{scope_str}' tidak ditemukan di disk",
                "action": "Tentukan path modul/package yang valid di repositori.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Target scope terverifikasi: {scope_str}",
            "action": "",
        })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: audit [{status_label}] ({passed_count}/{total} passed)",
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
            "target_scope": self.target_scope_arg,
            "checks": self.results,
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Audit Preconditions Checker")
    parser.add_argument("--target-scope", type=str, default=None, help="Target package or module scope path")
    parser.add_argument("--dimensions", type=str, default=None, help="Comma-separated dimensions list")
    parser.add_argument("--root", type=str, default=None, help="Target repo root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        target_scope=args.target_scope,
        dimensions=args.dimensions,
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
