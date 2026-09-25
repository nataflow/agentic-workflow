#!/usr/bin/env python3
"""Report Precondition Validator.

Automates verification of repository preconditions before REPORT.md generation.
Runs checks 1 through 7 in a single pass and produces a compact, actionable report.
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

# Resolver profil `.claude/profile/backenddev/` tinggal di
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    resolve_profile_dir,
    foreign_owner,
    legacy_suffix,
)
from brief_status import CLOSED, review_freshness, scan_briefs, validate_links  # noqa: E402


def _strip_explore_scratch(status_out: str) -> str:
    """Buang baris `git status --porcelain` yang menunjuk laci kerja `.explore/`.

    `code-explorer` menulis laporannya ke `<taskdir>/.explore/<slug>.md` (dan
    `backenddev/docs/.explore/` untuk dispatch gerbang). Laci itu zona kerja,
    bukan artefak rantai: tidak pernah di-stage maupun di-commit, sehingga
    kehadirannya tidak boleh dihitung sebagai working tree kotor.
    """
    kept = []
    for line in status_out.splitlines():
        if not line.strip():
            continue
        path = line[3:] if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ")[-1]
        path = path.strip().strip('"')
        if ".explore" in path.rstrip("/").split("/"):
            continue
        kept.append(line)
    return "\n".join(kept)


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        base_branch: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.base_branch_arg = base_branch
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
        """Run checks 1 through 7."""
        self._check_1_taskdir()
        self._check_2_root_task()
        self._check_3_review_report()
        self._check_4_all_briefs_done()
        self._check_5_profile_config()
        self._check_6_report_absence()
        self._check_7_git_clean()
        return all(r["status"] == "PASS" for r in self.results)

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
                "action": "Tentukan path taskdir aktif (format: backenddev/docs/<YYMMDDhhmm>-<slug>/).",
            })
            return

        taskdir_path = self._resolve_taskdir()
        if not taskdir_path or not taskdir_path.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori taskdir tidak ditemukan di disk: {self.taskdir_arg}",
                "action": "Pastikan path taskdir valid dan menunjuk direktori nyata.",
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

    def _check_2_root_task(self):
        check_id = 2
        name = "Root TASK.md Contract"
        taskdir_path = self._resolve_taskdir()

        if not taskdir_path or not taskdir_path.exists():
            return

        task_file = taskdir_path / "TASK.md"
        if not task_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas TASK.md tidak ditemukan di taskdir",
                "action": "Pastikan TASK.md sebagai akar rantai telah dirumuskan.",
            })
            return

        try:
            content = task_file.read_text(encoding="utf-8")
            h1_count = len(re.findall(r"^#\s+[^\n]+", content, re.MULTILINE))
            if h1_count != 1:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"TASK.md harus memuat tepat satu judul H1 (ditemukan: {h1_count})",
                    "action": "Perbaiki format judul H1 pada TASK.md.",
                })
                return

            if "## Success Criteria" not in content:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "TASK.md tidak memuat seksi ## Success Criteria",
                    "action": "Lengkapi seksi ## Success Criteria pada TASK.md.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "TASK.md valid (memuat 1 H1 dan Success Criteria)",
                "action": "",
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca TASK.md: {e}",
                "action": "Periksa integritas berkas TASK.md.",
            })

    def _check_3_review_report(self):
        check_id = 3
        name = "REVIEW.md Closure Report"
        taskdir_path = self._resolve_taskdir()

        if not taskdir_path or not taskdir_path.exists():
            return

        review_file = taskdir_path / "REVIEW.md"
        if not review_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas REVIEW.md belum ada — gerbang penutup architect belum tuntas",
                "action": "Tuntaskan eksekusi code-reviewer dan penerbitan REVIEW.md via `backenddev:architect`.",
            })
            return

        fresh, why = review_freshness(self.root, self._get_rel_taskdir_str())
        if not fresh:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"REVIEW.md basi — {why}",
                "action": "Kembalikan ke `backenddev:architect` Fase 4 (review ulang); REPORT.md atas review basi dilarang.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"REVIEW.md terverifikasi di taskdir ({why})",
            "action": "",
        })

    def _check_4_all_briefs_done(self):
        """Seluruh brief tertutup: `DONE`, atau `SUPERSEDED` yang bertaut ke penggantinya."""
        check_id = 4
        name = "All Briefs Closed"
        taskdir_path = self._resolve_taskdir()

        if not taskdir_path or not taskdir_path.exists():
            return

        briefs = scan_briefs(taskdir_path)
        if not briefs:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Tidak ditemukan berkas brief-* di taskdir",
                "action": "Pastikan rangkaian brief ada di taskdir.",
            })
            return

        problems = [f"{b['name']} ({b['status']})" for b in briefs if b["status"] not in CLOSED]
        problems += validate_links(briefs)
        n_done = sum(b["status"] == "DONE" for b in briefs)
        if not n_done:
            problems.append("nol brief DONE")
        if problems:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Brief belum tertutup: {'; '.join(problems)}",
                "action": "Selesaikan lewat `backenddev:architect`; SUPERSEDED sah hanya bila bertaut ke pengganti.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"{n_done} DONE · {len(briefs) - n_done} SUPERSEDED",
            "action": "",
        })

    def _check_5_profile_config(self):
        check_id = 5
        name = "Profile Commit Convention"
        profile_dir, legacy_note = resolve_profile_dir(self.root)
        index_file = profile_dir / "index.json"

        if not index_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas .claude/profile/backenddev/index.json tidak ditemukan",
                "action": "Jalankan `backenddev:profile` untuk membuat profil repositori.",
            })
            return

        owner = foreign_owner(profile_dir)
        if owner:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Profil di {profile_dir.relative_to(self.root).as_posix()}/ milik `{owner}`; bukan profil backenddev",
                "action": "Jangan membaca atau menimpa profil plugin lain; jalankan `backenddev:profile` (ditulis ke `.claude/profile/backenddev/`).",
            })
            return

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data.get("base_branch") or not data.get("commit_convention"):
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Field 'base_branch' atau 'commit_convention' hilang di index.json",
                    "action": "Lengkapi field profil via `backenddev:profile`.",
                })
                return
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Format JSON corrupt pada index.json: {e}",
                "action": "Perbaiki format index.json.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Profil valid (base_branch: {data.get('base_branch')})" + legacy_suffix(legacy_note),
            "action": "",
        })

    def _check_6_report_absence(self):
        check_id = 6
        name = "REPORT.md Target Absence"
        taskdir_path = self._resolve_taskdir()

        if not taskdir_path or not taskdir_path.exists():
            return

        report_file = taskdir_path / "REPORT.md"
        if report_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Berkas {report_file.name} sudah ada di taskdir",
                "action": "Dilarang menimpa REPORT.md yang sudah terkunci tanpa instruksi eksplisit user.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Berkas REPORT.md belum ada (siap ditulis baru)",
            "action": "",
        })

    def _check_7_git_clean(self):
        check_id = 7
        name = "Git Working Tree Cleanliness"
        try:
            status = _strip_explore_scratch(subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            )).strip()

            if status:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Working tree git kotor sebelum penulisan REPORT.md",
                    "action": "Bersihkan atau commit perubahan git sebelum merumuskan REPORT.md.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Working tree git bersih",
                "action": "",
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca status git: {e}",
                "action": "Pastikan git repo valid.",
            })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: report [{status_label}] ({passed_count}/{total} passed)",
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
    parser = argparse.ArgumentParser(description="Report Preconditions Checker")
    parser.add_argument("--taskdir", type=str, default=None, help="Task directory path")
    parser.add_argument("--base-branch", type=str, default=None, help="Base branch comparison")
    parser.add_argument("--root", type=str, default=None, help="Target repo root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        taskdir=args.taskdir,
        base_branch=args.base_branch,
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
