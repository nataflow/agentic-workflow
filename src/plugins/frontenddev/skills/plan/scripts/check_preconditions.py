#!/usr/bin/env python3
"""Plan Precondition Validator.

Memvonis prasyarat `frontenddev:plan` sebelum Phase 0 dibuka: bentuk dan izin
tulis taskdir, akar `TASK.md` beserta pasangan lane/sections, kesesuaian `mode`
dengan keadaan taskdir dan ledger, hop hulu `## Chain` tercentang dan utuh,
keutuhan seri brief beserta `report-<NN>.md` tiap unit `BLOCKED`, profil
beserta adapter stack, berkas template/referensi/dispatcher, dan kebersihan
working tree.

`mode` wajib eksplisit dan diverifikasi terhadap keadaan, bukan disimpulkan
darinya — menyimpulkan jalur dari berkas yang kebetulan ada adalah cara rantai
ber-kontrak turun diam-diam jadi MINOR:

| mode     | lane          | brief di taskdir | baris BRIEF ledger |
|----------|---------------|------------------|--------------------|
| CONTRACT | non-MINOR     | belum ada        | `[ ]`              |
| MINOR    | HOTFIX_MINOR  | belum ada        | `[ ]`              |
| REVISE   | apa pun       | ada              | `[ ]` (belum disetujui; plafon revisi 2) |
| APPEND   | apa pun       | ada              | `[~]` (dibuka ulang `chain.py reopen`)   |

Skrip ini juga **menyelesaikan satu fakta** di baris `Terselesaikan:`: nomor
`NN` unit berikutnya. Batas lingkup MINOR tetap dinilai model.

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
from precondition_lib import (  # noqa: E402
    profile_dir_for,
    MINOR_LANE,
    check_adapter,
    check_chain_rows,
    check_plugin_files,
    check_profile,
    check_task_root,
    check_taskdir,
    check_worktree,
    expected_rows,
    find_repo_root,
    format_report,
    normalize_taskdir,
    probe_writable,
    read_chain,
    read_status,
    report_json,
    revisions_since_open,
    taskdir_slug,
)

MODES = ("CONTRACT", "MINOR", "REVISE", "APPEND")
PROFILE_REQUIRED = ("index.json", "invariants.md", "surface-map.md", "commands.md", "drift.md")
PLUGIN_FILES = ("references/slicing-patterns.md", "templates/brief-template.md",
                "dispatcher/explorer.md", "dispatcher/reviewer.md", "scripts/validate_briefs.py")
BRIEF_PATTERN = re.compile(r"^brief-(\d{2})-[a-z0-9-]+\.md$")
MAX_REVISIONS = 2


class PreconditionChecker:
    def __init__(self, taskdir: str, mode: str, root: Optional[Path] = None,
                 profile_dir: Optional[str] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.taskdir = self.root / self.taskdir_rel
        self.mode = (mode or "").strip().upper()
        self.profile_dir = profile_dir_for(self.root, profile_dir)
        self.skill_dir = Path(__file__).resolve().parents[1]
        self.results: List[Dict[str, Any]] = []
        self.stack: str = ""
        self.lane: str = ""
        self.sections: List[str] = []
        self.next_unit: str = "01"

    def _add(self, cid: int, name: str, status: str, summary: str, action: str = "") -> None:
        self.results.append({
            "id": cid, "name": name, "status": status,
            "summary": summary, "action": action,
        })

    def _briefs(self) -> Dict[str, Path]:
        found: Dict[str, Path] = {}
        if not self.taskdir.is_dir():
            return found
        for path in sorted(self.taskdir.iterdir()):
            m = BRIEF_PATTERN.match(path.name)
            if m:
                found.setdefault(m.group(1), path)
        return found

    def _brief_row(self) -> Dict[str, Any]:
        try:
            for e in read_chain((self.taskdir / "TASK.md").read_text(encoding="utf-8")):
                if e["row"] == "BRIEF":
                    return e
        except OSError:
            pass
        return {}

    # ---------------------------------------------------------------- checks

    def run_all(self) -> bool:
        """Jalankan 9 check; hanya `FAIL` yang menahan, `WARN` tidak."""
        taskdir_ok = self._check_1_taskdir()
        if taskdir_ok:
            self.lane, self.sections = check_task_root(self._add, 2, self.root, self.taskdir_rel)
        else:
            self._add(2, "TASK.md akar, lane & sections", "FAIL", "taskdir tidak sah",
                      "Perbaiki Check 1 lebih dulu.")
        rooted = bool(self.lane)
        self._check_3_mode(rooted)
        if rooted:
            rows = [r for r in expected_rows(self.sections) if r != "BRIEF"]
            check_chain_rows(self._add, 4, self.root, self.taskdir_rel, rows, self.sections)
        else:
            self._add(4, "Ledger ## Chain tercentang", "FAIL", "akar belum sah",
                      "Perbaiki Check 2 lebih dulu.")
        self._check_5_brief_series(taskdir_ok)
        self.stack = check_profile(self._add, 6, self.profile_dir, PROFILE_REQUIRED)
        check_adapter(self._add, 7, self.stack)
        check_plugin_files(self._add, 8, self.skill_dir, PLUGIN_FILES)
        check_worktree(self._add, 9, self.root, self.taskdir_rel)
        return not any(r["status"] == "FAIL" for r in self.results)

    def _check_1_taskdir(self) -> bool:
        if not check_taskdir(self._add, 1, self.root, self.taskdir_rel):
            return False
        ok, detail = probe_writable(self.taskdir)
        if not ok:
            self.results.pop()
            self._add(1, "Bentuk & keberadaan taskdir", "FAIL", detail,
                      "Periksa izin tulis taskdir; brief ditulis ke sana.")
            return False
        return True

    def _check_3_mode(self, rooted: bool) -> None:
        name = f"Mode {self.mode or '(kosong)'} sesuai keadaan"
        if self.mode not in MODES:
            self._add(3, name, "FAIL", f"mode `{self.mode or '(kosong)'}` di luar {MODES}",
                      "Teruskan `mode` eksplisit dari pemanggil; tidak ada nilai bawaan.")
            return
        if not rooted:
            self._add(3, name, "FAIL", "akar belum sah", "Perbaiki Check 2 lebih dulu.")
            return
        briefs = self._briefs()
        row = self._brief_row()
        mark = row.get("mark", "")
        minor = self.lane == MINOR_LANE
        problem = ""
        if self.mode in ("CONTRACT", "MINOR"):
            if briefs:
                problem = f"taskdir sudah memuat {len(briefs)} brief — pakai REVISE atau APPEND"
            elif mark != " ":
                problem = f"baris BRIEF ledger `[{mark}]`, bukan `[ ]`"
            elif self.mode == "CONTRACT" and minor:
                problem = f"lane `{MINOR_LANE}` tidak punya kontrak — pakai mode MINOR"
            elif self.mode == "MINOR" and not minor:
                problem = f"lane `{self.lane}` bukan MINOR — pakai mode CONTRACT"
            elif self.mode == "MINOR" and (self.taskdir / "CONTRACT.md").is_file():
                problem = "taskdir MINOR memuat `CONTRACT.md` — lane sudah tereskalasi tanpa dicatat"
        elif self.mode == "REVISE":
            if not briefs:
                problem = "belum ada brief untuk direvisi"
            elif mark != " ":
                problem = (f"baris BRIEF ledger `[{mark}]` — breakdown yang sudah disetujui dibuka "
                           "lewat `chain.py reopen --row BRIEF` lalu mode APPEND")
            else:
                slug = taskdir_slug(self.taskdir_rel)
                used = revisions_since_open(self.root, [f"{self.taskdir_rel}/brief-*.md"], slug, "breakdown")
                if used >= MAX_REVISIONS:
                    self._add(3, name, "WARN", f"plafon {MAX_REVISIONS} revisi breakdown habis",
                              "Hanya approval (Phase 5) yang boleh — batch tidak ditulis ulang. Penolakan "
                              "berikutnya dihentikan ke `frontenddev:lead`.")
                    return
        else:  # APPEND
            if not briefs:
                problem = "mode APPEND tetapi taskdir belum memuat brief"
            elif mark != "~":
                problem = (f"baris BRIEF ledger `[{mark}]`, bukan `[~]` — buka ulang lewat "
                           "`chain.py reopen --row BRIEF --reason <pemicu>` lebih dulu")
        if problem:
            self._add(3, name, "FAIL", problem,
                      "Pilih mode yang sesuai keadaan taskdir; dilarang memaksa mode lain agar lolos.")
            return
        self._add(3, name, "PASS", f"lane `{self.lane}`, {len(briefs)} brief, BRIEF `[{mark}]`")

    def _check_5_brief_series(self, taskdir_ok: bool) -> None:
        name = "Seri brief & bukti unit BLOCKED"
        if not taskdir_ok:
            self._add(5, name, "FAIL", "taskdir tidak sah", "Perbaiki Check 1 lebih dulu.")
            return
        briefs = self._briefs()
        if not briefs:
            self._add(5, name, "PASS", "belum ada brief — unit pertama `01`")
            return
        numbers = sorted(int(nn) for nn in briefs)
        self.next_unit = f"{numbers[-1] + 1:02d}"
        missing = [nn for nn, path in sorted(briefs.items())
                   if read_status(path) == "BLOCKED"
                   and not (self.taskdir / f"report-{nn}.md").is_file()]
        if missing:
            self._add(5, name, "FAIL",
                      "unit BLOCKED tanpa `report-<NN>.md`: " + ", ".join(missing),
                      "`report-<NN>.md` adalah sumber brief remedi; laporkan bukti yang hilang ke "
                      "user, jangan ditambal dengan tebakan.")
            return
        self._add(5, name, "PASS", f"{len(briefs)} brief, unit berikutnya `{self.next_unit}`")

    # ---------------------------------------------------------------- output

    def format_text(self) -> str:
        return format_report(f"plan ({self.mode or '-'})", self.results,
                             {"unit_berikutnya": self.next_unit,
                              "lane": self.lane or "-",
                              "sections": ",".join(self.sections) or "-"})

    def to_json(self) -> str:
        return report_json(self.results, root=str(self.root), taskdir=self.taskdir_rel,
                           mode=self.mode, lane=self.lane, sections=self.sections,
                           stack=self.stack, next_unit=self.next_unit)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan Preconditions Checker")
    parser.add_argument("--taskdir", required=True, help="path taskdir relatif root repo")
    parser.add_argument("--mode", required=True, help="CONTRACT, MINOR, REVISE, atau APPEND")
    parser.add_argument("--profile-dir", default=None, dest="profile_dir",
                        help="direktori profil, default .claude/profile/frontenddev (lokasi lama .claude/profile hanya dibaca untuk MIGRATE)")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()

    checker = PreconditionChecker(
        taskdir=args.taskdir, mode=args.mode,
        root=Path(args.root) if args.root else None,
        profile_dir=args.profile_dir,
    )
    ok = checker.run_all()
    print(checker.to_json() if args.json else checker.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
