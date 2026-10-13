#!/usr/bin/env python3
"""Task Precondition Validator.

Automates verification of repository preconditions before task skill execution.
Runs checks 1 through 7 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` (parser taskdir, chain, status git, profil,
keluaran), di-bootstrap relatif terhadap berkas ini.
"""

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Parser bersama tinggal di `skills/_common/precondition_lib.py`. Bootstrap path
# relatif terhadap berkas ini, bukan terhadap cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    check_base_branch,
    TASKDIR_ACTION,
    GitError,
    check_taskdir,
    dirty_paths,
    find_repo_root,
    format_text,
    is_under,
    legacy_suffix,
    load_profile_index,
    parse_chain,
    ticket_source_verdict,
    to_json,
)
from precondition_lib import cli  # noqa: E402
import docs_git  # noqa: E402

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
        ticket_source: Optional[str] = None,
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.lane_arg = (lane or "").strip().upper() if lane else None
        # Kosong/`-` berarti tanpa chain (lane non-planning); nilai asing dilaporkan check 6.
        self.chain_arg, self.chain_err = parse_chain(chain)
        self.td = check_taskdir(self.root, taskdir)
        self.ticket_source = (ticket_source or "").strip()
        self.results: List[Dict[str, Any]] = []


    def run_all(self) -> bool:
        """Run checks 1 through 7."""
        self._check_1_taskdir()
        self._check_2_profile()
        self._check_3_task_absence()
        self._check_4_lane()
        self._check_5_git_worktree_and_status()
        self._check_6_chain()
        self._check_7_ticket_source()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_6_chain(self):
        check_id = 6
        name = "Chain & Terminal Lane Alignment"

        if self.chain_err:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": self.chain_err,
                "action": "Gunakan enum chain kanonik dari `analyst/references/chain-rules.md` bagian 1.3.",
            })
            return

        if not self.chain_arg:
            if self.lane_arg and self.lane_arg not in NON_PLANNING_LANES and self.lane_arg in VALID_LANES:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Lane planning '{self.lane_arg}' berangkat tanpa parameter chain",
                    "action": "Sertakan --chain <BRD_PRD_BRIEF | PRD_BRIEF | BRIEF> dari `backend:analyst`.",
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

    def _check_7_ticket_source(self):
        # Ditambahkan di akhir supaya nomor check 1–6 yang sudah dirujuk tetap.
        status, summary, action = ticket_source_verdict(self.root, self.ticket_source)
        self.results.append({
            "id": 7,
            "name": "Ticket Source READY & Terkunci",
            "status": status,
            "summary": summary,
            "action": action,
        })

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

    def _check_2_profile(self):
        check_id = 2
        name = "Profile & Commit Convention"
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

        commit_conv = data["commit_convention"]

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Profil valid (commit_convention: {commit_conv})" + legacy_suffix(legacy_note),
            "action": "",
        })

    def _check_3_task_absence(self):
        check_id = 3
        name = "TASK.md Absence"

        if not self.td.ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Taskdir tidak tersedia untuk memeriksa keberadaan TASK.md",
                "action": "Sertakan parameter --taskdir yang valid.",
            })
            return

        task_file = self.td.path / "TASK.md"
        if task_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"{self.td.rel}/TASK.md sudah ada di disk",
                "action": "Hentikan eksekusi segera. Amandemen dan backfill TASK.md adalah wewenang gerbang `backend:tech-lead`.",
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
            # Akar ditulis ke `backenddev/docs/` yang wajib sudah di luar git (24 G2): penanda ignore ditulis
            # prasyarat penuh `tech-lead` (check 3), dan berkas yang masih ter-track menunggu migrasi.
            tracked = docs_git.tracked_docs(self.root, docs_git.PREFIXES["backend"])
            if tracked or not docs_git.docs_ignored(self.root, docs_git.PREFIXES["backend"]):
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": (f"{len(tracked)} berkas `backenddev/docs/` masih ter-track git" if tracked else
                                "`backenddev/docs/` belum diabaikan git"),
                    "action": "Kembalikan ke `backend:tech-lead`: prasyarat penuhnya (check 3) menulis penanda ignore "
                              "atau merutekan migrasi; dokumen taskdir tidak di-commit.",
                })
                return
            # Laci kerja `.explore/` milik `code-explorer` bukan artefak rantai:
            # tidak pernah di-stage maupun di-commit, jadi dibuang dirty_paths.
            dirty_outside = [p for p in dirty_paths(self.root)
                             if not (self.td.rel and is_under(p, self.td.rel))]
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

            # Akar rantai dikunci di branch kerja taskdir ini (11 H20): `base_commit` diambil dari HEAD, dan
            # commit kode unit mendarat di branch yang sama. HEAD di base atau detached mendaratkan kode di
            # base/entah di mana, dan HEAD di branch rantai lain mengikat akar ke rantai yang salah.
            base = (load_profile_index(self.root, required=()).data or {}).get("base_branch")
            ok, detail = check_base_branch(self.root, base if isinstance(base, str) else None)
            slug = self.td.rel.rsplit("/", 1)[-1].split("-", 1)[-1] if self.td.rel else ""
            head = subprocess.run(["git", "symbolic-ref", "-q", "--short", "HEAD"], cwd=self.root,
                                  capture_output=True, text=True).stdout.strip()
            if ok and slug and slug not in head:
                ok, detail = False, f"HEAD di branch '{head}', bukan branch kerja taskdir ini (memuat `{slug}`)"
            if not ok:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": detail,
                    "action": "Kembalikan ke `backend:tech-lead`: isolasi branch kerja taskdir (Fase 3 butir 2) "
                              "berangkat sebelum akar ditulis; dilarang mengunci TASK.md di base atau branch lain.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": f"Working tree bersih di luar taskdir · {detail}",
                "action": "",
            })
        except GitError as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal memeriksa git status: {e}",
                "action": "Periksa kondisi repositori git.",
            })

    def format_text(self) -> str:
        return format_text("task", self.results)

    def to_json(self) -> str:
        return to_json(self.root, self.results, taskdir=self.taskdir_arg, lane=self.lane_arg, chain=self.chain_arg,
                       ticket_source=self.ticket_source)


def main():
    parser = argparse.ArgumentParser(description="Task Preconditions Checker")
    parser.add_argument("--taskdir", type=str, required=False, help="Task directory path")
    parser.add_argument("--lane", type=str, required=False, help="Terminal lane enum")
    parser.add_argument("--chain", type=str, nargs="?", const="", default=None,
                        help="Chain enum (BRD_PRD_BRIEF | PRD_BRIEF | BRIEF); kosong/tanpa nilai pada lane non-planning")
    parser.add_argument("--ticket-source", type=str, default="", dest="ticket_source",
                        help="path TICKET.md analyst (analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md), bila akar dari tiket")
    parser.add_argument("--root", type=str, default=None, help="Root path of target repository")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(taskdir=args.taskdir, lane=args.lane, chain=args.chain, target_root=target_root,
                                  ticket_source=args.ticket_source)
    passed = checker.run_all()

    if args.json:
        print(checker.to_json())
    else:
        print(checker.format_text())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    sys.exit(cli(main))
