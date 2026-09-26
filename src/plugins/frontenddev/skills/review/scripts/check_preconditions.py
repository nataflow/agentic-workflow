#!/usr/bin/env python3
"""Review (ad-hoc) Precondition Validator.

`frontenddev:review` hanya melayani lane `REVIEW_AUDIT` — penilaian kode di luar
rantai taskdir. Review penutup taskdir adalah milik `frontenddev:architect` +
`code-reviewer`, dan skill ini tidak pernah menulis `<taskdir>/REVIEW.md`.

Tiga target:

- `diff`    — rentang commit (`--range A..B`, default `HEAD~1..HEAD`).
- `path`    — satu direktori fitur atau berkas (`--path`).
- `taskdir` — taskdir yang **sudah tuntas** (`REPORT.md` ada), dinilai ulang
              atas rentang sejak akarnya; read-only terhadap taskdir itu.

`--write` menerbitkan temuan ke `frontenddev/reviews/<YYMMDDhhmm>-<slug>.md`
(ter-commit) supaya dapat menjadi `finding_source` taskdir perbaikan; tanpanya
laporan berhenti di chat. Hanya `--write` yang menuntut working tree bersih.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    profile_dir_for,
    TASKDIR_PATTERN,
    chain_files,
    check_adapter,
    check_plugin_files,
    check_profile,
    check_worktree,
    find_repo_root,
    format_report,
    git,
    normalize_taskdir,
    probe_writable,
    report_json,
    task_root_sha,
)

TARGETS = ("diff", "path", "taskdir")
PROFILE_REQUIRED = ("index.json", "stack.md", "invariants.md", "surface-map.md",
                    "commands.md", "layer-adoption.md", "drift.md")
PLUGIN_FILES = ("references/nine-dimensions-catalog.md", "references/review-checklist.md",
                "templates/audit-template.md")


class PreconditionChecker:
    def __init__(self, target: str, rng: str = "", path: str = "", taskdir: str = "",
                 write: bool = False, root: Optional[Path] = None,
                 profile_dir: Optional[str] = None):
        self.root = (root or find_repo_root()).resolve()
        self.target = (target or "").lower()
        self.range = rng.strip()
        self.path_raw = path.strip()
        self.path = ""
        self.taskdir_rel = normalize_taskdir(taskdir or "")
        self.write = write
        self.profile_dir = profile_dir_for(self.root, profile_dir)
        self.skill_dir = Path(__file__).resolve().parents[1]
        self.results: List[Dict[str, Any]] = []
        self.stack = ""
        self.resolved_range = ""
        self.chain_files: List[str] = []

    def _add(self, cid: int, name: str, status: str, summary: str, action: str = "") -> None:
        self.results.append({"id": cid, "name": name, "status": status,
                             "summary": summary, "action": action})

    def run_all(self) -> bool:
        self._check_1_scope()
        self.stack = check_profile(self._add, 2, self.profile_dir, PROFILE_REQUIRED)
        check_adapter(self._add, 3, self.stack)
        check_plugin_files(self._add, 4, self.skill_dir, PLUGIN_FILES)
        if self.write:
            ok, detail = probe_writable(self.root / "frontenddev" / "reviews")
            self._add(5, "frontenddev/reviews dapat ditulis", "PASS" if ok else "FAIL", detail,
                      "" if ok else "Periksa izin tulis direktori kerja.")
            check_worktree(self._add, 6, self.root)
        return not any(r["status"] == "FAIL" for r in self.results)

    def _check_1_scope(self) -> None:
        name = f"Objek review `{self.target or '-'}` tersedia"
        if self.target not in TARGETS:
            self._add(1, name, "FAIL", f"target `{self.target or '(kosong)'}` di luar {TARGETS}",
                      "Review penutup taskdir aktif bukan milik skill ini — itu `frontenddev:architect`.")
            return
        if self.target == "diff":
            rng = self.range or "HEAD~1..HEAD"
            start, _, end = rng.partition("...") if "..." in rng else rng.partition("..")
            if not (git(self.root, "rev-parse", "--verify", "-q", start).strip()
                    and git(self.root, "rev-parse", "--verify", "-q", end or "HEAD").strip()):
                self._add(1, name, "FAIL", f"rentang `{rng}` tidak resolve",
                          "Sebut rentang commit yang ada, mis. `main..HEAD`.")
                return
            self.resolved_range = rng
            self._add(1, name, "PASS", f"diff `{rng}`")
            return
        if self.target == "path":
            raw = self.path_raw
            full = (Path(raw) if Path(raw).is_absolute() else self.root / raw).resolve() if raw else None
            try:
                rel = full.relative_to(self.root) if full else None
            except ValueError:
                self._add(1, name, "FAIL", f"path `{raw}` berada di luar repo `{self.root}`",
                          "Review ad-hoc hanya menilai berkas di dalam toplevel git repo ini.")
                return
            if rel is None or not full.exists():
                self._add(1, name, "FAIL", f"path `{raw or '(kosong)'}` tidak ada",
                          "Sebut direktori fitur atau berkas yang ada di repo.")
                return
            self.path = rel.as_posix()
            self._add(1, name, "PASS", f"path `{self.path}`")
            return
        taskdir = self.root / self.taskdir_rel
        if not TASKDIR_PATTERN.match(self.taskdir_rel) or not taskdir.is_dir():
            self._add(1, name, "FAIL", f"taskdir `{self.taskdir_rel}` tidak sah atau tidak ada",
                      "Isi `taskdir` dengan path frontenddev/docs/<YYMMDDhhmm>-<slug> yang ada.")
            return
        if not (taskdir / "REPORT.md").is_file():
            self._add(1, name, "FAIL", "taskdir belum tuntas (`REPORT.md` absen)",
                      "Taskdir yang masih berjalan dinilai `frontenddev:architect` Fase 4, bukan di sini.")
            return
        sha = task_root_sha(self.root, self.taskdir_rel)
        self.resolved_range = f"{sha[:7]}..HEAD" if sha else ""
        # Objek = berkas rantai (commit bersubjek `<type>(<slug>):`), sama dengan review penutup
        # architect — bukan seluruh diff akar..HEAD yang ikut memuat kerja user dan taskdir lain.
        self.chain_files = chain_files(self.root, self.taskdir_rel)
        if not self.chain_files:
            self._add(1, name, "WARN", f"taskdir tuntas, rentang `{self.resolved_range}`, nol berkas rantai",
                      "Tidak ada kode yang dinilai; sebut ke user sebelum melanjutkan.")
            return
        self._add(1, name, "PASS", f"taskdir tuntas, rentang `{self.resolved_range}`, "
                                   f"{len(self.chain_files)} berkas rantai")

    def format_text(self) -> str:
        resolved = {"rentang": self.resolved_range or "-", "tulis": "ya" if self.write else "tidak"}
        if self.target == "taskdir":
            resolved["berkas"] = "chain.py files --taskdir " + self.taskdir_rel
        return format_report(f"review ({self.target or '-'})", self.results, resolved)

    def to_json(self) -> str:
        return report_json(self.results, root=str(self.root), target=self.target,
                           range=self.resolved_range, path=self.path, write=self.write,
                           chain_files=self.chain_files, stack=self.stack)


def main() -> None:
    parser = argparse.ArgumentParser(description="Review (ad-hoc) Preconditions Checker")
    parser.add_argument("--target", required=True, help="diff | path | taskdir")
    parser.add_argument("--range", default="", dest="rng", help="rentang commit target diff")
    parser.add_argument("--path", default="", help="direktori/berkas target path")
    parser.add_argument("--taskdir", default="", help="taskdir tuntas untuk target taskdir")
    parser.add_argument("--write", action="store_true", help="terbitkan ke frontenddev/reviews/")
    parser.add_argument("--profile-dir", default=None, dest="profile_dir")
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    checker = PreconditionChecker(args.target, args.rng, args.path, args.taskdir, args.write,
                                  Path(args.root) if args.root else None, args.profile_dir)
    ok = checker.run_all()
    print(checker.to_json() if args.json else checker.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
