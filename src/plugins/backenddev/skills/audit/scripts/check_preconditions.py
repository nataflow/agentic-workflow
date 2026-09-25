#!/usr/bin/env python3
"""Audit Precondition Validator.

Automates verification of repository preconditions before audit sweep execution.
Runs checks 1 through 6 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` (parser frontmatter, taskdir, chain, profil,
berkas plugin, keluaran), di-bootstrap relatif terhadap berkas ini.
"""

import argparse
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional


# Helper izin tulis dipakai bersama lintas skrip prasyarat; rumah kanoniknya
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd — skrip dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    find_repo_root,
    format_text,
    legacy_suffix,
    load_profile_index,
    plugin_file,
    probe_writable as _probe_writable,
    to_json,
)


VALID_DIMENSIONS = ("security", "transaction", "data", "persistence", "concurrency", "architecture")

# Bentuk target yang menunjuk diff/PR, dicocokkan terhadap SELURUH string dan hanya
# bila string itu bukan path yang ada. `a..b`/`a...b` wajib punya ruas kiri bukan
# titik/garis miring, sehingga `../x` dan `internal/expr/` tidak ikut tertangkap.
DIFF_TARGET = re.compile(
    r"^(?:[^\s./][^\s]*?\.\.\.?[^\s/][^\s]*"      # main..HEAD, a...b
    r"|origin/\S+|refs/pull/\d+(?:/\w+)?|pr/\d+|#\d+|diff:.*)$",
    re.IGNORECASE,
)


class PreconditionChecker:
    def __init__(
        self,
        target_scope: Optional[str] = None,
        dimensions: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.target_scope_arg = target_scope
        self.dimensions_arg = dimensions
        self.results: List[Dict[str, Any]] = []


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
        data = load_profile_index(self.root, required=("source_root",)).data
        src_rel = data["source_root"] if data else "src"

        src_dir = (self.root / src_rel).resolve()
        if not src_dir.is_relative_to(self.root):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"source_root '{src_rel}' berada di luar root repositori {self.root}",
                "action": "Perbaiki `source_root` di index.json menjadi path relatif di dalam repo lewat `backenddev:profile`.",
            })
            return

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
        prof = load_profile_index(self.root)
        if not prof.ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": prof.error,
                "action": prof.action,
            })
            return
        data, legacy_note, profile_dir = prof.data, prof.note, prof.dir

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
            "summary": f"Profil valid (stack: {data.get('stack')})" + legacy_suffix(legacy_note),
            "action": "",
        })

    def _check_3_stack_adapter(self):
        check_id = 3
        name = "Stack Adapter Resolution"
        data = load_profile_index(self.root, required=("stack",)).data
        stack_id = data["stack"] if data else "unknown"

        found = plugin_file("skills", "profile", "stacks", f"{stack_id}.md")
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
        contract = skill_dir / "references" / "findings-contract.md"

        missing = []
        if not dim_ref.exists():
            missing.append("references/dimensions.md")
        if not tpl_file.exists():
            missing.append("templates/issues-template.md")
        if not contract.exists():
            missing.append("references/findings-contract.md")

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
            "summary": "Referensi dimensions.md, findings-contract.md, dan issues-template.md tersedia",
            "action": "",
        })

    def _check_6_target_scope(self):
        check_id = 6
        name = "Target Scope Validation"

        def fail(summary: str, action: str):
            self.results.append({"id": check_id, "name": name, "status": "FAIL",
                                 "summary": summary, "action": action})

        scope_str = (self.target_scope_arg or "").strip()
        if not scope_str:
            fail("Parameter target_scope kosong (REQUIRED)",
                 "Minta path modul/package/folder yang disapu; audit tidak menebak cakupan.")
            return

        dims = [d.strip().lower() for d in (self.dimensions_arg or "all").split(",") if d.strip()]
        unknown = [d for d in dims if d != "all" and d not in VALID_DIMENSIONS]
        if unknown:
            fail(f"Dimensi tidak dikenal: {', '.join(unknown)}",
                 f"Gunakan `all` atau subset dari: {', '.join(VALID_DIMENSIONS)}.")
            return

        scope_path = Path(scope_str)
        if not scope_path.is_absolute():
            scope_path = self.root / scope_path
        scope_path = scope_path.resolve()

        if not scope_path.exists() and DIFF_TARGET.match(scope_str):
            fail(f"target_scope '{scope_str}' menunjuk diff branch/PR, bukan kode mendarat",
                 "Gunakan subagent `code-reviewer` untuk penilaian diff, audit hanya menyapu path direktori/modul nyata.")
            return

        if not scope_path.is_relative_to(self.root):
            fail(f"target_scope '{scope_str}' berada di luar root repositori",
                 "Tentukan path modul/package di dalam repositori target.")
            return

        if not scope_path.exists():
            fail(f"Path target_scope '{scope_str}' tidak ditemukan di disk",
                 "Tentukan path modul/package yang valid di repositori.")
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Target scope terverifikasi: {scope_path.relative_to(self.root).as_posix() or '.'} · dimensi {', '.join(dims)}",
            "action": "",
        })

    def format_text(self) -> str:
        return format_text("audit", self.results)

    def to_json(self) -> str:
        return to_json(self.root, self.results, target_scope=self.target_scope_arg)


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
