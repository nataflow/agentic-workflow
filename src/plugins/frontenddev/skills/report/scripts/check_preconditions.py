#!/usr/bin/env python3
"""Report Precondition Validator.

Memvonis prasyarat `frontenddev:report` sebelum Phase 1 dibuka: bentuk
taskdir, akar `TASK.md` beserta ledger `## Chain` tercentang penuh dan utuh,
`REVIEW.md` penutup ter-commit, lolos `validate_review.py`, dan ber-verdict
`PASS`/`WARNING`, seluruh brief tertutup (`DONE`, atau `BLOCKED` ber-remedi
`DONE`), ketiadaan `REPORT.md`, berkas rantai tidak kosong, dan kebersihan
working tree.

Skrip ini juga **menyelesaikan tiga fakta** di baris `Terselesaikan:`: SHA
commit akar, slug, dan jumlah berkas rantai — rentang yang dipakai Phase 2.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    brief_closure,
    chain_files,
    check_chain_rows,
    check_task_root,
    check_taskdir,
    check_worktree,
    expected_rows,
    find_repo_root,
    format_report,
    is_committed,
    normalize_taskdir,
    read_status,
    report_json,
    review_is_fresh,
    task_root_sha,
    taskdir_slug,
)

VALIDATE_REVIEW = Path(__file__).resolve().parents[2] / "architect" / "scripts" / "validate_review.py"


class PreconditionChecker:
    def __init__(self, taskdir: str, root: Optional[Path] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.taskdir = self.root / self.taskdir_rel
        self.results: List[Dict[str, Any]] = []
        self.root_sha = ""
        self.sections: Optional[List[str]] = None
        self.files: List[str] = []

    def _add(self, cid: int, name: str, status: str, summary: str, action: str = "") -> None:
        self.results.append({
            "id": cid, "name": name, "status": status,
            "summary": summary, "action": action,
        })

    def run_all(self) -> bool:
        """Jalankan 8 check; hanya `FAIL` yang menahan."""
        ok = check_taskdir(self._add, 1, self.root, self.taskdir_rel)
        for cid, fn in ((2, self._check_2_task), (3, self._check_3_review),
                        (4, self._check_4_briefs), (5, self._check_5_absent),
                        (6, self._check_6_chain)):
            if ok:
                fn(cid)
            else:
                self._add(cid, fn.__doc__ or "", "FAIL", "taskdir tidak sah",
                          "Perbaiki Check 1 lebih dulu.")
        check_worktree(self._add, 7, self.root)
        if ok and self.sections is not None:
            check_chain_rows(self._add, 8, self.root, self.taskdir_rel,
                             expected_rows(self.sections), self.sections)
        else:
            self._add(8, "Ledger ## Chain tercentang", "FAIL", "akar belum sah",
                      "Perbaiki Check 2 lebih dulu.")
        return not any(r["status"] == "FAIL" for r in self.results)

    def _check_2_task(self, cid: int) -> None:
        """TASK.md akar ter-commit"""
        lane, sections = check_task_root(self._add, cid, self.root, self.taskdir_rel)
        if lane:
            self.sections = sections
            self.root_sha = task_root_sha(self.root, self.taskdir_rel)

    def _check_3_review(self, cid: int) -> None:
        """REVIEW.md penutup layak"""
        name = self._check_3_review.__doc__
        rel = f"{self.taskdir_rel}/REVIEW.md"
        if not (self.root / rel).is_file():
            self._add(cid, name, "FAIL", "`REVIEW.md` belum ada",
                      "Review penutup belum jalan; kembali ke `frontenddev:architect` Fase 4.")
            return
        if not is_committed(self.root, rel):
            self._add(cid, name, "FAIL", "`REVIEW.md` belum ter-commit",
                      "Commit `REVIEW.md` lewat `frontenddev:architect` Fase 4 lebih dulu.")
            return
        proc = subprocess.run([sys.executable, str(VALIDATE_REVIEW), "--taskdir", self.taskdir_rel,
                               "--root", str(self.root)], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, universal_newlines=True)
        if proc.returncode != 0:
            self._add(cid, name, "FAIL", "`validate_review.py` FAIL — " + proc.stdout.splitlines()[0][:120],
                      "REVIEW.md yang ter-commit tidak sah; kembali ke `frontenddev:architect` Fase 4.")
            return
        if not review_is_fresh(self.root, self.taskdir_rel):
            self._add(cid, name, "FAIL", "`REVIEW.md` lebih tua daripada commit `implement unit` terakhir",
                      "Unit yang mendarat sesudah review belum pernah dinilai; kembali ke `frontenddev:architect` Phase 4.")
            return
        verdict = read_status(self.root / rel, "verdict")
        if verdict not in ("PASS", "WARNING"):
            self._add(cid, name, "FAIL", f"verdict `{verdict or '(kosong)'}`",
                      "REPORT ditahan; temuan diperbaiki di taskdir yang sama (reopen BRIEF → plan APPEND → review ulang).")
            return
        self._add(cid, name, "PASS", f"verdict `{verdict}`")

    def _check_4_briefs(self, cid: int) -> None:
        """Seluruh brief tertutup"""
        name = self._check_4_briefs.__doc__
        closure = brief_closure(self.taskdir)
        if not closure:
            self._add(cid, name, "FAIL", "nol brief di taskdir", "Rantai belum pernah dieksekusi.")
            return
        pending = [f"brief-{nn} ({st})" for nn, (st, done) in closure.items() if not done]
        if pending:
            self._add(cid, name, "FAIL", "belum tertutup: " + ", ".join(pending),
                      "Selesaikan eksekusi lewat `frontenddev:architect`.")
            return
        remedied = sum(1 for st, _ in closure.values() if st == "BLOCKED")
        self._add(cid, name, "PASS", f"{len(closure)} brief tertutup"
                  + (f" ({remedied} BLOCKED ber-remedi)" if remedied else ""))

    def _check_5_absent(self, cid: int) -> None:
        """REPORT.md belum ada"""
        name = self._check_5_absent.__doc__
        if (self.taskdir / "REPORT.md").is_file():
            if is_committed(self.root, f"{self.taskdir_rel}/REPORT.md"):
                self._add(cid, name, "FAIL", "`REPORT.md` sudah terbit (ter-commit)",
                          "Dilarang ditimpa; serahkan keputusan penulisan ulang ke user.")
            else:
                self._add(cid, name, "FAIL", "`REPORT.md` tertunda — tertulis tetapi belum ter-commit",
                          "Jangan tulis ulang: kunci lewat `frontenddev:architect` Phase 5 butir 4 "
                          "(validasi lalu commit).")
            return
        self._add(cid, name, "PASS", "siap ditulis baru")

    def _check_6_chain(self, cid: int) -> None:
        """Berkas rantai tidak kosong"""
        name = self._check_6_chain.__doc__
        if not self.root_sha:
            self._add(cid, name, "FAIL", "akar belum resolve", "Perbaiki Check 2 lebih dulu.")
            return
        self.files = chain_files(self.root, self.taskdir_rel)
        if not self.files:
            self._add(cid, name, "FAIL",
                      f"nol berkas diubah commit `({taskdir_slug(self.taskdir_rel)})` sesudah akar",
                      "Laporkan ke user; dilarang mengarang butir dari isi brief.")
            return
        self._add(cid, name, "PASS", f"{len(self.files)} berkas rantai")

    def format_text(self) -> str:
        return format_report("report", self.results, {
            "akar": self.root_sha[:12] or "-",
            "slug": taskdir_slug(self.taskdir_rel),
            "berkas_rantai": str(len(self.files)),
        })

    def to_json(self) -> str:
        return report_json(self.results, root=str(self.root), taskdir=self.taskdir_rel,
                           root_sha=self.root_sha, chain_files=self.files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Report Preconditions Checker")
    parser.add_argument("--taskdir", required=True, help="path taskdir relatif root repo")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()

    checker = PreconditionChecker(args.taskdir, Path(args.root) if args.root else None)
    ok = checker.run_all()
    print(checker.to_json() if args.json else checker.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
