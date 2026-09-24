#!/usr/bin/env python3
"""Task Precondition Validator.

Automates verification of repository preconditions before task skill execution.
Runs checks 1 through 5 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional

VALID_LANES = {
    "PRD_CONVERSION",
    "DIRECT_BRIEF",
    "DEFECT_RCA",
    "EXEC_BRIEF",
}

DISALLOWED_LANES = {
    "EXPLORE_FACT",
    "PROFILE",
}

VALID_CHAINS = {"BRD_PRD_BRIEF", "PRD_BRIEF", "BRIEF"}

# Lane terminal yang sah dipikul tiap chain (analyst/references/chain-rules.md bagian 1.3).
CHAIN_TERMINAL_LANES = {
    "BRD_PRD_BRIEF": {"PRD_CONVERSION"},
    "PRD_BRIEF": {"PRD_CONVERSION"},
    "BRIEF": {"DIRECT_BRIEF"},
}

# Lane di luar fase planning: chain wajib kosong. Perbaikan temuan tidak ada di sini —
# ia berakar lewat lane planning, dan `finding_source` yang menandainya.
NON_PLANNING_LANES = {
    "DEFECT_RCA",
    "EXEC_BRIEF",
}


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        lane: Optional[str] = None,
        chain: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.lane_arg = (lane or "").strip().upper() if lane else None
        self.chain_arg = (chain or "").strip().upper() if chain else None
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
        self._check_1_taskdir()
        self._check_2_profile()
        self._check_3_task_absence()
        self._check_4_lane()
        self._check_5_git_worktree_and_status()
        self._check_6_chain()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_6_chain(self):
        check_id = 6
        name = "Chain & Terminal Lane Alignment"

        if not self.chain_arg:
            if self.lane_arg and self.lane_arg not in NON_PLANNING_LANES and self.lane_arg in VALID_LANES:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Lane planning '{self.lane_arg}' berangkat tanpa parameter chain",
                    "action": "Sertakan --chain <BRD_PRD_BRIEF | PRD_BRIEF | BRIEF> dari `backenddev:analyst`.",
                })
                return
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Lane non-planning; ledger ## Chain tidak ditulis",
                "action": "",
            })
            return

        if self.chain_arg not in VALID_CHAINS:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Chain '{self.chain_arg}' tidak sah (wajib BRD_PRD_BRIEF | PRD_BRIEF | BRIEF)",
                "action": "Gunakan enum chain kanonik dari `analyst/references/chain-rules.md` bagian 1.3.",
            })
            return

        if self.lane_arg in NON_PLANNING_LANES:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Lane non-planning '{self.lane_arg}' dipasangkan chain {self.chain_arg}",
                "action": "Kosongkan --chain pada lane DEFECT_RCA dan EXEC_BRIEF.",
            })
            return

        allowed = CHAIN_TERMINAL_LANES[self.chain_arg]
        if self.lane_arg not in allowed:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Lane '{self.lane_arg}' bukan lane terminal chain {self.chain_arg} (yang sah: {' | '.join(sorted(allowed))})",
                "action": "Teruskan lane terminal kolom keempat matriks `analyst/references/chain-rules.md` bagian 1.3.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Chain {self.chain_arg} selaras dengan lane terminal {self.lane_arg}",
            "action": "",
        })

    def _resolve_taskdir(self) -> Optional[Path]:
        if not self.taskdir_arg:
            return None
        td = Path(self.taskdir_arg)
        return td if td.is_absolute() else self.root / td

    def _get_rel_taskdir_str(self) -> str:
        if not self.taskdir_arg:
            return ""
        td_path = self._resolve_taskdir()
        if not td_path:
            return self.taskdir_arg
        try:
            return str(td_path.relative_to(self.root)).rstrip("/")
        except ValueError:
            return str(td_path).rstrip("/")

    def _check_1_taskdir(self):
        check_id = 1
        name = "Taskdir Format & Existence"

        if not self.taskdir_arg:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Parameter taskdir belum diberikan",
                "action": "Minta direktori kerja sah dari gerbang `backenddev:tech-lead` (format: backenddev/docs/<YYMMDDhhmm>-<slug>/).",
            })
            return

        taskdir_path = self._resolve_taskdir()
        if not taskdir_path or not taskdir_path.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori taskdir tidak ditemukan di disk: {self.taskdir_arg}",
                "action": "Pastikan gerbang `backenddev:tech-lead` telah memprovisi direktori taskdir sebelum memanggil skill task.",
            })
            return

        rel_str = self._get_rel_taskdir_str()
        pattern = r"^backenddev/docs/\d{10}-[a-z0-9-]+$"
        if not re.match(pattern, rel_str):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Format taskdir '{rel_str}' tidak sesuai pola kanonik backenddev/docs/<YYMMDDhhmm>-<slug>/",
                "action": "Gunakan format taskdir kanonik backenddev/docs/<YYMMDDhhmm>-<slug>/.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Taskdir terverifikasi: {rel_str}",
            "action": "",
        })

    def _check_2_profile(self):
        check_id = 2
        name = "Profile & Commit Convention"
        index_file = self.root / ".claude" / "profile" / "index.json"

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

            commit_conv = data.get("commit_convention")
            if not commit_conv or not str(commit_conv).strip():
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Field commit_convention kosong atau hilang di index.json",
                    "action": "Lengkapi field commit_convention via skill `backenddev:profile`.",
                })
                return
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Format JSON rusak pada index.json: {e}",
                "action": "Perbaiki format JSON atau inisialisasi ulang via `backenddev:profile`.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Profil valid (commit_convention: {commit_conv})",
            "action": "",
        })

    def _check_3_task_absence(self):
        check_id = 3
        name = "TASK.md Absence"

        taskdir_path = self._resolve_taskdir()
        if not taskdir_path:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Taskdir tidak tersedia untuk memeriksa keberadaan TASK.md",
                "action": "Sertakan parameter --taskdir yang valid.",
            })
            return

        task_file = taskdir_path / "TASK.md"
        if task_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"{self._get_rel_taskdir_str()}/TASK.md sudah ada di disk",
                "action": "Hentikan eksekusi segera. Amandemen dan backfill TASK.md adalah wewenang gerbang `backenddev:tech-lead`.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "TASK.md belum ada di taskdir (siap dirumuskan)",
            "action": "",
        })

    def _check_4_lane(self):
        check_id = 4
        name = "Lane Validity"

        if not self.lane_arg:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Parameter lane belum diberikan",
                "action": "Sertakan parameter --lane dari pemanggilnya (salah satu dari 4 lane berartefak).",
            })
            return

        if self.lane_arg in DISALLOWED_LANES:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Lane '{self.lane_arg}' tidak mengalokasikan taskdir atau TASK.md",
                "action": f"Lane {self.lane_arg} dieksekusi tanpa taskdir; jangan memanggil skill task untuk lane ini.",
            })
            return

        if self.lane_arg not in VALID_LANES:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Lane '{self.lane_arg}' tidak dikenal (wajib salah satu dari 4 lane kanonik)",
                "action": f"Gunakan salah satu lane sah: {', '.join(sorted(VALID_LANES))}.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Lane valid: {self.lane_arg}",
            "action": "",
        })

    def _check_5_git_worktree_and_status(self):
        check_id = 5
        name = "Git Worktree & Working Tree Status"

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
                    "summary": "Workspace bukan repositori git yang valid",
                    "action": "Inisialisasi repositori git atau buka direktori kerja yang valid.",
                })
                return
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca status git: {e}",
                "action": "Pastikan git terpasang dan repositori memiliki .git sah.",
            })
            return

        try:
            status_output = subprocess.check_output(
                ["git", "status", "--porcelain", "-uall"],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            ).splitlines()

            rel_taskdir = self._get_rel_taskdir_str().rstrip("/")
            # Check for dirty entries outside taskdir
            dirty_outside: List[str] = []
            for line in status_output:
                if not line.strip():
                    continue
                # Line format is XY path or XY orig -> path
                file_part = line[3:].strip().rstrip("/")
                if " -> " in file_part:
                    file_part = file_part.split(" -> ")[-1].strip().rstrip("/")

                # Normalize path
                if rel_taskdir and (file_part == rel_taskdir or file_part.startswith(rel_taskdir + "/")):
                    continue
                # Laci kerja `.explore/` milik `code-explorer` bukan artefak rantai:
                # tidak pernah di-stage maupun di-commit, jadi tidak dihitung kotor.
                if ".explore" in file_part.rstrip("/").split("/"):
                    continue
                dirty_outside.append(file_part)

            if dirty_outside:
                samples = dirty_outside[:3]
                suffix = f" (+{len(dirty_outside)-3} lainnya)" if len(dirty_outside) > 3 else ""
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Working tree kotor di luar taskdir ({len(dirty_outside)} file: {', '.join(samples)}{suffix})",
                    "action": "Commit, stash, atau bersihkan perubahan di luar taskdir sebelum merumuskan dan mengunci TASK.md.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Working tree bersih di luar taskdir (siap untuk commit isolasi)",
                "action": "",
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal memeriksa git status: {e}",
                "action": "Periksa kondisi repositori git.",
            })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: task [{status_label}] ({passed_count}/{total} passed)",
        ]
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<35} : {r['status']} ({r['summary']})")
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
            "lane": self.lane_arg,
            "chain": self.chain_arg,
            "checks": self.results,
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Task Preconditions Checker")
    parser.add_argument("--taskdir", type=str, required=False, help="Task directory path")
    parser.add_argument("--lane", type=str, required=False, help="Terminal lane enum")
    parser.add_argument("--chain", type=str, required=False, help="Chain enum (BRD_PRD_BRIEF | PRD_BRIEF | BRIEF)")
    parser.add_argument("--root", type=str, default=None, help="Root path of target repository")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(taskdir=args.taskdir, lane=args.lane, chain=args.chain, target_root=target_root)
    passed = checker.run_all()

    if args.json:
        print(checker.to_json())
    else:
        print(checker.format_text())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
