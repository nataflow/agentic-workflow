#!/usr/bin/env python3
"""Debug Precondition Validator.

Automates verification of repository preconditions before debug RCA execution.
Runs checks 1 through 6 in a single pass and produces a compact, actionable report.
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
    check_taskdir,
    find_agent,
    find_repo_root,
    format_text,
    legacy_suffix,
    load_profile_index,
    plugin_file,
    probe_writable as _probe_writable,
    to_json,
)


class PreconditionChecker:
    def __init__(
        self,
        symptom: Optional[str] = None,
        taskdir: Optional[str] = None,
        scope_hint: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.symptom_arg = symptom
        self.taskdir_arg = taskdir
        self.td = check_taskdir(self.root, taskdir)
        self.scope_hint_arg = scope_hint
        self.results: List[Dict[str, Any]] = []


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
            "summary": f"Profil valid (stack: {data.get('stack')}, root_ns: {data.get('root_namespace')})" + legacy_suffix(legacy_note),
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


        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/explorer.md tidak ditemukan di skill debug",
                "action": "Pastikan template dispatcher/explorer.md tersedia untuk dispatch langsung code-explorer.",
            })
            return

        if not find_agent("code-explorer"):
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

        # Pola kanonik ditegakkan (SKILL.md Fase 0: "pola lain ditolak tanpa
        # negosiasi") sebelum izin tulis diuji.
        if not self.td.ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": self.td.summary,
                "action": "Pastikan taskdir sudah dialokasikan gerbang `backenddev:tech-lead` "
                          "(backenddev/docs/<YYMMDDhhmm>-<slug>/); pola lain ditolak dan dilarang mengarang direktori pengganti.",
            })
            return
        td = self.td.path

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
            "summary": f"Taskdir terverifikasi dan siap ditulis: {self.td.rel}",
            "action": "",
        })

    def _check_6_source_read_access(self):
        check_id = 6
        name = "Source & Test Read Access"
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
        return format_text("debug", self.results)

    def to_json(self) -> str:
        return to_json(self.root, self.results, taskdir=self.taskdir_arg)


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
