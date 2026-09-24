#!/usr/bin/env python3
"""Debug Precondition Validator.

Automates verification of repository preconditions before debug RCA execution.
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
        symptom: Optional[str] = None,
        taskdir: Optional[str] = None,
        scope_hint: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.symptom_arg = symptom
        self.taskdir_arg = taskdir
        self.scope_hint_arg = scope_hint
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
        self._check_1_profile()
        self._check_2_git_worktree()
        self._check_3_stack_adapter()
        self._check_4_templates_and_dispatcher()
        self._check_5_taskdir_or_docs_root()
        self._check_6_source_read_access()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_profile(self):
        check_id = 1
        name = "Profile Index & Commands"
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
            required_keys = ["root_namespace", "source_root", "stack"]
            missing = [k for k in required_keys if not data.get(k)]
            if missing:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Field kritis hilang di index.json: {', '.join(missing)}",
                    "action": "Jalankan `backenddev:profile` untuk melengkapi field profil.",
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

        commands_file = profile_dir / "commands.md"
        if not commands_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas commands.md tidak ditemukan di direktori profil",
                "action": "Jalankan `backenddev:profile` untuk mencatat perintah build dan test.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Profil valid (stack: {data.get('stack')}, root_ns: {data.get('root_namespace')})",
            "action": "",
        })

    def _check_2_git_worktree(self):
        check_id = 2
        name = "Git Repository Worktree"
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
                    "action": "Jalankan pada direktori repositori git aktif.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Repositori git aktif terverifikasi",
                "action": "",
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca status git: {e}",
                "action": "Pastikan git terpasang dan repositori valid.",
            })

    def _check_3_stack_adapter(self):
        check_id = 3
        name = "Stack Adapter Signatures"
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
            "summary": f"Adapter stack '{stack_id}' memuat seksi failure signatures",
            "action": "",
        })

    def _check_4_templates_and_dispatcher(self):
        """Template RCA dan template dispatch explorer beserta definisi agentnya.

        `debug` mendispatch `code-explorer` langsung lewat `dispatcher/explorer.md`,
        tanpa skill pembungkus. Template itu memikul patokan `Kedalaman: menyeluruh`
        dan pemisahan `### Not Found` dari `### Gaps`; tanpanya jalur yang belum
        disisir dapat menggugurkan hipotesis yang sebenarnya benar.
        """
        check_id = 4
        name = "RCA Template & Explorer Dispatcher"
        skill_dir = Path(__file__).resolve().parent.parent
        rca_template = skill_dir / "templates" / "rca-template.md"

        if not rca_template.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas templates/rca-template.md tidak ditemukan",
                "action": "Pastikan berkas plugin backenddev:debug terpasang lengkap.",
            })
            return

        dispatcher_file = skill_dir / "dispatcher" / "explorer.md"

        candidate_agents = [
            skill_dir.parent.parent / "agents" / "code-explorer.md",
            self.root / "src" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
        ]

        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/explorer.md tidak ditemukan di skill debug",
                "action": "Pastikan template dispatcher/explorer.md tersedia untuk dispatch langsung code-explorer.",
            })
            return

        if not any(p.exists() for p in candidate_agents):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/code-explorer.md tidak ditemukan",
                "action": "Pastikan berkas agents/code-explorer.md tersedia di plugin backenddev.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Template rca-template.md, dispatcher/explorer.md, dan agent code-explorer.md terverifikasi",
            "action": "",
        })

    def _check_5_taskdir_or_docs_root(self):
        check_id = 5
        name = "Taskdir Write Access"

        # Taskdir hanya diprovisi gerbang `backenddev:tech-lead` Fase 3, dan
        # `backenddev:task` menulis TASK.md sebelum lane hilir mana pun berangkat.
        # Lane DEFECT_RCA selalu masuk lewat gerbang, jadi taskdir kosong adalah
        # cacat pemanggilan, bukan pemicu alokasi mandiri.
        if not self.taskdir_arg:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Parameter taskdir kosong; debug tidak memprovisi taskdir sendiri",
                "action": "Minta alokasi taskdir dari gerbang `backenddev:tech-lead` Fase 3 lalu jalankan ulang.",
            })
            return

        td = Path(self.taskdir_arg)
        if not td.is_absolute():
            td = self.root / td

        if not td.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori taskdir yang diberikan tidak ditemukan: {self.taskdir_arg}",
                "action": "Pastikan taskdir sudah dialokasikan gerbang `backenddev:tech-lead`; dilarang mengarang direktori pengganti.",
            })
            return

        ok, detail = _probe_writable(td)
        if not ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori taskdir tidak dapat ditulis: {detail}",
                "action": "Periksa hak akses direktori taskdir.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Taskdir terverifikasi dan siap ditulis: {td.relative_to(self.root) if td.is_relative_to(self.root) else td}",
            "action": "",
        })

    def _check_6_source_read_access(self):
        check_id = 6
        name = "Source & Test Read Access"
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
        target_check = src_dir if src_dir.exists() else (self.root / "src")

        if not target_check.exists() or not os.access(target_check, os.R_OK):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori kode sumber {target_check} tidak ditemukan atau tidak dapat dibaca",
                "action": "Pastikan izin baca pada kode sumber aktif.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Izin baca kode sumber aktif untuk lokalisasi kegagalan",
            "action": "",
        })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: debug [{status_label}] ({passed_count}/{total} passed)",
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
            "taskdir": self.taskdir_arg,
            "checks": self.results,
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Debug RCA Preconditions Checker")
    parser.add_argument("--symptom", type=str, default=None, help="Raw symptom or error message")
    parser.add_argument("--taskdir", type=str, default=None, help="Task directory path")
    parser.add_argument("--scope-hint", type=str, default=None, help="Suspected scope path")
    parser.add_argument("--root", type=str, default=None, help="Target repo root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        symptom=args.symptom,
        taskdir=args.taskdir,
        scope_hint=args.scope_hint,
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
