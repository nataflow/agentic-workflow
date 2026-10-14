#!/usr/bin/env python3
"""Task Precondition Validator.

Memvonis prasyarat `frontend:task` sebelum Phase 1 dibuka: bentuk taskdir,
profil, ketiadaan `TASK.md`, keabsahan pasangan `lane`/`sections`, keberadaan
`finding_source`, berkas template, kebersihan working tree, `ticket_source`
analyst yang READY serta terkunci, slug yang belum dipakai taskdir lain, dan
dokumen taskdir di luar git (24 G2): `frontenddev/docs/` yang masih ter-track →
rute MIGRASI; selain itu penanda ignore `frontenddev/docs/.gitignore` ditulis.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Bootstrap path relatif terhadap berkas ini, bukan terhadap cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
import docs_git  # noqa: E402
from precondition_lib import (  # noqa: E402
    profile_dir_for,
    check_plugin_files,
    check_profile,
    check_taskdir,
    check_worktree,
    find_repo_root,
    format_report,
    is_committed,
    lane_sections_problem,
    normalize_taskdir,
    parse_sections,
    read_status,
    report_json,
    taskdir_slug,
    ticket_source_verdict,
)
from precondition_lib import cli  # noqa: E402

PROFILE_REQUIRED = ("index.json", "surface-map.md")
PLUGIN_FILES = ("templates/task-template.md", "scripts/validate_task.py",
                "../_common/chain.py")
DOCS = "frontenddev/docs"
TASKDIR_NAME = re.compile(r"^\d{10}-(?P<slug>.+)$")


class PreconditionChecker:
    def __init__(self, taskdir: str, lane: str, sections: str = "", finding_source: str = "",
                 root: Optional[Path] = None, profile_dir: Optional[str] = None,
                 ticket_source: str = ""):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.lane = (lane or "").strip().upper()
        self.sections = parse_sections(sections)
        self.finding_source = (finding_source or "").strip()
        self.ticket_source = (ticket_source or "").strip()
        self.profile_dir = profile_dir_for(self.root, profile_dir)
        self.skill_dir = Path(__file__).resolve().parents[1]
        self.results: List[Dict[str, Any]] = []
        self.stack: str = ""

    def _add(self, cid: int, name: str, status: str, summary: str, action: str = "") -> None:
        self.results.append({
            "id": cid, "name": name, "status": status,
            "summary": summary, "action": action,
        })

    def run_all(self) -> bool:
        """Jalankan 10 check; hanya `FAIL` yang menahan."""
        taskdir_ok = check_taskdir(self._add, 1, self.root, self.taskdir_rel)
        self.stack = check_profile(self._add, 2, self.profile_dir, PROFILE_REQUIRED)
        self._check_3_absent(taskdir_ok)
        self._check_4_lane()
        self._check_5_finding_source()
        check_plugin_files(self._add, 6, self.skill_dir, PLUGIN_FILES)
        check_worktree(self._add, 7, self.root)
        # Ditambahkan di akhir supaya nomor check 1–7 yang sudah dirujuk tetap.
        self._add(8, "ticket_source READY & terkunci", *ticket_source_verdict(self.root, self.ticket_source))
        self._check_9_slug(taskdir_ok)
        self._check_10_docs_git()
        return not any(r["status"] == "FAIL" for r in self.results)

    def _check_10_docs_git(self) -> None:
        """Dokumen taskdir di luar git (24 G2): ter-track → MIGRASI; selain itu penanda ignore ditulis."""
        name = "Dokumen taskdir di luar git"
        prefix = docs_git.PREFIXES["frontend"]
        tracked = docs_git.tracked_docs(self.root, prefix)
        if tracked:
            self._add(10, name, "FAIL", f"MIGRASI: {len(tracked)} berkas `{prefix}/docs/` masih ter-track git",
                      "Kembali ke `frontend:lead`: prosedur migrasi (`AskUserQuestion`, lalu "
                      "`docs_git.py migrate --answer -`) sebelum akar baru ditulis.")
            return
        written, problem = docs_git.ensure_ignored(self.root, prefix)
        if problem:
            self._add(10, name, "FAIL", problem, f"Perbaiki `.gitignore` di bawah `{prefix}/docs/`, lalu ulangi.")
            return
        if not docs_git.docs_ignored(self.root, prefix):
            self._add(10, name, "FAIL", "repo git tidak terbaca — penanda ignore tidak dapat dipastikan",
                      "Jalankan di root repo git yang sah (lihat check 7).")
            return
        summary = f"`{prefix}/docs/` diabaikan git" + (" (penanda `.gitignore` baru ditulis)" if written else "")
        if not (self.root / docs_git.NATAFLOW_CONFIG).is_file():      # 24 K2: tanpa cermin, disk satu-satunya salinan
            self._add(10, name, "WARN", f"{summary}; `{docs_git.NATAFLOW_CONFIG}` tidak ada — dokumen taskdir hanya "
                                         "tersimpan di disk ini",
                      "Sebut ke user sekali: tanpa sinkron nataflow, dokumen taskdir tidak punya salinan di luar "
                      "mesin ini. Lanjutkan.")
            return
        self._add(10, name, "PASS", summary)

    def _check_3_absent(self, taskdir_ok: bool) -> None:
        name = "TASK.md belum ada"
        if not taskdir_ok:
            self._add(3, name, "FAIL", "taskdir tidak sah", "Perbaiki Check 1 lebih dulu.")
            return
        path = self.root / self.taskdir_rel / "TASK.md"
        if path.is_file():
            status = read_status(path) or "(kosong)"
            self._add(3, name, "FAIL", f"`TASK.md` sudah ada berstatus `{status}`",
                      "Akar tidak ditulis ulang; serahkan ke `frontend:lead`.")
            return
        self._add(3, name, "PASS", "akar belum ditulis")

    def _check_9_slug(self, taskdir_ok: bool) -> None:
        """Slug belum dipakai taskdir lain (12 J49): commit rantai dikenali dari `(<slug>)` di subjeknya,
        jadi dua taskdir bersolug sama saling mencampur berkas rantai, revisi, dan re-entry."""
        name = "Slug belum dipakai taskdir lain"
        if not taskdir_ok:
            self._add(9, name, "FAIL", "taskdir tidak sah", "Perbaiki Check 1 lebih dulu.")
            return
        slug = taskdir_slug(self.taskdir_rel)
        own = Path(self.taskdir_rel).name
        docs = self.root / DOCS
        clash = sorted(p.name for p in docs.iterdir()
                       if p.is_dir() and p.name != own and (m := TASKDIR_NAME.match(p.name))
                       and m.group("slug") == slug) if docs.is_dir() else []
        if clash:
            self._add(9, name, "FAIL", f"slug `{slug}` sudah dipakai {', '.join(f'`{c}`' for c in clash)}",
                      f"Commit rantai dikenali dari `({slug})`; slug kembar mencampur berkas rantai. Kembali ke "
                      f"`frontend:lead` Phase 5: beri sufiks (mis. `{slug}-2`) pada taskdir baru.")
            return
        self._add(9, name, "PASS", f"slug `{slug}` unik")

    def _check_4_lane(self) -> None:
        name = "Pasangan lane & sections sah"
        problem = lane_sections_problem(self.lane, self.sections)
        if problem:
            self._add(4, name, "FAIL", problem,
                      "Teruskan `lane` dan `sections` persis dari handoff `frontend:lead`; "
                      "pasangan yang tidak sah berarti lead salah merutekan, bukan task salah menulis.")
            return
        self._add(4, name, "PASS", f"lane `{self.lane}`, sections `{','.join(self.sections) or '-'}`")

    def _check_5_finding_source(self) -> None:
        name = "finding_source ter-commit"
        if not self.finding_source:
            self._add(5, name, "PASS", "permintaan kerja biasa — tanpa temuan asal")
            return
        rel = normalize_taskdir(self.finding_source)
        if not (self.root / rel).is_file():
            self._add(5, name, "FAIL", f"`{rel}` tidak ada",
                      "Periksa path `finding_source` dari handoff lead.")
            return
        if not is_committed(self.root, rel):
            self._add(5, name, "FAIL", f"`{rel}` belum ter-commit",
                      "Temuan asal wajib ter-commit sebelum dijadikan akar.")
            return
        self._add(5, name, "PASS", rel)

    def format_text(self) -> str:
        return format_report("task", self.results)

    def to_json(self) -> str:
        return report_json(self.results, root=str(self.root), taskdir=self.taskdir_rel,
                           lane=self.lane, sections=self.sections, stack=self.stack,
                           ticket_source=self.ticket_source)


def main() -> None:
    parser = argparse.ArgumentParser(description="Task Preconditions Checker")
    parser.add_argument("--taskdir", required=True, help="path taskdir relatif root repo")
    parser.add_argument("--lane", required=True, help="lane handoff lead")
    parser.add_argument("--sections", required=True,
                        help="sections handoff lead (`flow,ui`, `architecture`, atau `-` untuk MINOR)")
    parser.add_argument("--finding-source", default="", dest="finding_source",
                        help="path REVIEW.md asal, bila ada")
    parser.add_argument("--ticket-source", default="", dest="ticket_source",
                        help="path TICKET.md analyst (analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md), bila akar dari tiket")
    parser.add_argument("--profile-dir", default=None, dest="profile_dir",
                        help="direktori profil, default .claude/profile/frontenddev (lokasi lama .claude/profile hanya dibaca untuk MIGRATE)")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()

    checker = PreconditionChecker(
        taskdir=args.taskdir, lane=args.lane, sections=args.sections,
        finding_source=args.finding_source, ticket_source=args.ticket_source,
        root=Path(args.root) if args.root else None, profile_dir=args.profile_dir,
    )
    ok = checker.run_all()
    print(checker.to_json() if args.json else checker.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    sys.exit(cli(main))
