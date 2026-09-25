#!/usr/bin/env python3
"""Report Precondition Validator.

Automates verification of repository preconditions before REPORT.md generation.
Runs checks 1 through 7 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Impor intra-plugin:
`skills/_common/precondition_lib.py` (parser taskdir, heading, status git, profil,
keluaran) dan `skills/_common/brief_status.py`, di-bootstrap relatif terhadap
berkas ini.
"""

import argparse
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Parser bersama tinggal di `skills/_common/precondition_lib.py`. Bootstrap path
# relatif terhadap berkas ini, bukan terhadap cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    TASKDIR_ACTION,
    count_h1,
    check_taskdir,
    dirty_paths,
    find_repo_root,
    format_text,
    has_heading,
    legacy_suffix,
    load_profile_index,
    read_text,
    to_json,
)
from brief_status import CLOSED, review_freshness, scan_briefs, validate_links  # noqa: E402


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        base_branch: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.base_branch_arg = base_branch
        self.td = check_taskdir(self.root, taskdir)
        self.results: List[Dict[str, Any]] = []


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

    def _check_1_taskdir(self):
        check_id = 1
        name = "Taskdir Format & Existence"

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS" if self.td.ok else "FAIL",
            "summary": self.td.summary,
            "action": "" if self.td.ok else TASKDIR_ACTION,
        })

    def _check_2_root_task(self):
        check_id = 2
        name = "Root TASK.md Contract"
        if not self.td.ok:
            return
        taskdir_path = self.td.path

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
            # BOM/CRLF dinormalkan; `# komentar` di blok kode berpagar bukan H1.
            content = read_text(task_file)
            h1_count = count_h1(content)
            if h1_count != 1:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"TASK.md harus memuat tepat satu judul H1 (ditemukan: {h1_count})",
                    "action": "Perbaiki format judul H1 pada TASK.md.",
                })
                return

            if not has_heading(content, "## Success Criteria"):
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
        if not self.td.ok:
            return
        taskdir_path = self.td.path

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

        fresh, why = review_freshness(self.root, self.td.rel)
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
        if not self.td.ok:
            return
        taskdir_path = self.td.path

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

        problems = [f"{b['name']} ({b['status'] if b['status'] != 'UNKNOWN' else 'tak terbaca: ' + b['why']})"
                    for b in briefs if b["status"] not in CLOSED]
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
        data, legacy_note = prof.data, prof.note

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
        if not self.td.ok:
            return
        taskdir_path = self.td.path

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
            # Laci kerja `.explore/` milik `code-explorer` bukan artefak rantai: tidak
            # pernah di-stage maupun di-commit, jadi dibuang dirty_paths.
            if dirty_paths(self.root):
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
        return format_text("report", self.results)

    def to_json(self) -> str:
        return to_json(self.root, self.results, taskdir=self.taskdir_arg)


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
