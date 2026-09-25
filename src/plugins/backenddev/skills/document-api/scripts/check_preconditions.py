#!/usr/bin/env python3
"""Document-API Precondition Validator.

Automates verification of repository preconditions before API documentation extraction.
Runs checks 1 through 5 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` (parser frontmatter, taskdir, chain, profil,
berkas plugin, keluaran), di-bootstrap relatif terhadap berkas ini.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional


# Helper izin tulis dipakai bersama lintas skrip prasyarat; rumah kanoniknya
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd — skrip dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    find_repo_root,
    format_text,
    load_profile_index,
    plugin_file,
    probe_writable as _probe_writable,
    to_json,
)


class PreconditionChecker:
    def __init__(
        self,
        domain: Optional[str] = None,
        base_branch: Optional[str] = None,
        stack: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.domain_arg = domain
        self.base_branch_arg = base_branch
        self.stack_arg = stack
        self.results: List[Dict[str, Any]] = []


    def run_all(self) -> bool:
        """Run checks 1 through 5."""
        self._check_1_source_root()
        self._check_2_profile_and_stack()
        self._check_3_docs_api_directory()
        self._check_4_template_reference()
        self._check_5_git_cli()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_source_root(self):
        check_id = 1
        name = "Source Root & Code Access"
        data = load_profile_index(self.root, required=("source_root",)).data
        src_rel = data["source_root"] if data else "src"

        src_dir = self.root / src_rel
        target_check = src_dir if src_dir.exists() else (self.root / "src")

        if not target_check.exists() or not os.access(target_check, os.R_OK):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori kode sumber {target_check} tidak ditemukan atau tidak dapat dibaca",
                "action": "Pastikan izin baca pada kode sumber aktif untuk pemindaian endpoint.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Akses kode sumber terverifikasi di {target_check.relative_to(self.root) if target_check.is_relative_to(self.root) else target_check}",
            "action": "",
        })

    def _check_2_profile_and_stack(self):
        check_id = 2
        name = "Profile & Stack Adapter"
        # `--stack` eksplisit membebaskan skill ini dari profil; tanpanya profil
        # ditagih utuh (tujuh kunci) seperti skrip prasyarat lain.
        stack_id = (self.stack_arg or "").strip()
        if not stack_id:
            prof = load_profile_index(self.root)
            if not prof.ok:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Stack tidak terbaca dari profil ({prof.error}) dan --stack kosong",
                    "action": "Jalankan `backenddev:profile` atau tentukan parameter --stack secara eksplisit.",
                })
                return
            stack_id = prof.data["stack"]

        if not plugin_file("skills", "profile", "stacks", f"{stack_id}.md"):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Adapter stacks/{stack_id}.md tidak ditemukan",
                "action": f"Pastikan plugin backenddev mendukung stack '{stack_id}' dengan seksi ## API surface.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Stack '{stack_id}' terverifikasi dengan adapter API surface sah",
            "action": "",
        })

    def _check_3_docs_api_directory(self):
        check_id = 3
        name = "Output Directory Access"
        api_dir = self.root / "docs" / "api"

        # Direktori dibuat saat dokumen ditulis, bukan oleh skrip check.
        ok, detail = _probe_writable(api_dir)
        if not ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori docs/api/ tidak dapat ditulis: {detail}",
                "action": "Periksa hak akses penulisan ke direktori docs/api/.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Direktori docs/api/ siap ditulis",
            "action": "",
        })

    def _check_4_template_reference(self):
        check_id = 4
        name = "API Doc Template Reference"
        skill_dir = Path(__file__).resolve().parent.parent
        template_file = skill_dir / "references" / "api-doc-template.md"

        if not template_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas references/api-doc-template.md tidak ditemukan",
                "action": "Pastikan plugin backenddev:document-api terpasang lengkap.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Template references/api-doc-template.md tersedia",
            "action": "",
        })

    def _check_5_git_cli(self):
        check_id = 5
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
                    "action": "Jalankan pada repositori git aktif.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Git CLI siap untuk resolusi branch dan diff pada mode POST_CHAIN",
                "action": "",
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal menjalankan perintah git: {e}",
                "action": "Pastikan git CLI tersedia di environment kerja.",
            })

    def format_text(self) -> str:
        return format_text("document-api", self.results)

    def to_json(self) -> str:
        return to_json(self.root, self.results, domain=self.domain_arg)


def main():
    parser = argparse.ArgumentParser(description="Document-API Preconditions Checker")
    parser.add_argument("--domain", type=str, default=None, help="Domain API scope name")
    parser.add_argument("--base-branch", type=str, default=None, help="Base branch comparison")
    parser.add_argument("--stack", type=str, default=None, help="Stack identifier override")
    parser.add_argument("--root", type=str, default=None, help="Target repo root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        domain=args.domain,
        base_branch=args.base_branch,
        stack=args.stack,
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
