#!/usr/bin/env python3
"""Analyst Precondition Validator.

Automates verification of repository preconditions before analyst skill execution.
Runs checks 1 through 7 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` (parser frontmatter, taskdir, chain, status git,
profil, keluaran), di-bootstrap relatif terhadap berkas ini.
"""

import argparse
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Parser bersama tinggal di `skills/_common/precondition_lib.py`. Bootstrap path
# relatif terhadap berkas ini, bukan terhadap cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    TASKDIR_ACTION,
    VALID_CHAINS,
    VALID_RISKS,
    GitError,
    check_taskdir,
    declared_chain,
    dirty_paths,
    find_repo_root,
    format_text,
    is_under,
    legacy_suffix,
    load_profile_index,
    parse_chain,
    read_text,
    to_json,
)
from precondition_lib import cli  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain_counters as _counters  # noqa: E402

# Artefak rancangan yang wajib ada pada tiap chain.
CHAIN_ARTIFACTS = {
    "BRD_PRD_BRIEF": {"BRD.md", "PRD.md"},
    "PRD_BRIEF": {"PRD.md"},
    "BRIEF": set(),
}

# Chain yang sah dipikul tiap risk level (chain-rules.md bagian 1.4 — invarian pasangan).
# BREAKING menuntut PRD lewat sumbu kontrak butir 1, tetapi TIDAK menuntut BRD:
# kebutuhan BRD diputuskan sumbu bisnis bagian 1.1, bukan oleh pecahnya kontrak teknis.
RISK_CHAINS = {
    "BREAKING": {"BRD_PRD_BRIEF", "PRD_BRIEF"},
    "MAJOR": {"BRD_PRD_BRIEF", "PRD_BRIEF", "BRIEF"},
    "MINOR": {"BRIEF"},
}


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        risk: Optional[str] = None,
        chain: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.risk_arg = (risk or "").strip().upper() if risk else None
        # `auto` (atau kosong) hanya sah sebagai parameter: chain diturunkan di Fase 1.
        # Nilai lain dinormalkan parse_chain; nilai asing dilaporkan check 4, bukan KeyError.
        raw = (chain or "").strip()
        if raw.lower() in ("", "auto"):
            self.chain_arg, self.chain_err = "AUTO", ""
        else:
            parsed, self.chain_err = parse_chain(raw)
            self.chain_arg = parsed or raw.upper()
        self.td = check_taskdir(self.root, taskdir)
        self.results: List[Dict[str, Any]] = []


    def run_all(self) -> bool:
        """Run checks 1 through 6."""
        self._check_1_taskdir()
        self._check_2_profile()
        self._check_3_risk()
        self._check_4_chain()
        self._check_5_artifact_consistency()
        self._check_6_git_worktree_and_status()
        self._check_7_resume_point()
        return all(r["status"] == "PASS" for r in self.results)

    def _task_chain(self):
        """(chain, galat) dari frontmatter TASK.md bila berkasnya sudah ada."""
        return declared_chain(self.td.path) if self.td.ok else (None, "")

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

    def _check_3_risk(self):
        check_id = 3
        name = "Risk Level Enum"

        if not self.risk_arg:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Parameter risk belum diberikan",
                "action": "Sertakan --risk <BREAKING | MAJOR | MINOR> hasil Keputusan 2 gerbang `backend:tech-lead`.",
            })
            return

        if self.risk_arg not in VALID_RISKS:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Risk level '{self.risk_arg}' tidak sah (wajib BREAKING | MAJOR | MINOR)",
                "action": "Minta gerbang `backend:tech-lead` menetapkan risk level; dilarang menebak sendiri.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Risk level {self.risk_arg} terverifikasi",
            "action": "",
        })

    def _check_4_chain(self):
        check_id = 4
        name = "Chain Enum & Risk Alignment"

        if self.chain_arg == "AUTO":
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Chain diturunkan di Fase 1 dari dua sumbu references/chain-rules.md bagian 1.1-1.3",
                "action": "",
            })
            return

        if self.chain_err:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"{self.chain_err[:-1]} | auto)",
                "action": "Gunakan salah satu enum chain kanonik atau kosongkan agar diturunkan di Fase 1.",
            })
            return

        if self.risk_arg in RISK_CHAINS and self.chain_arg not in RISK_CHAINS[self.risk_arg]:
            allowed = " | ".join(sorted(RISK_CHAINS[self.risk_arg]))
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Chain {self.chain_arg} tidak sah pada risk {self.risk_arg} (yang sah: {allowed})",
                "action": "Selaraskan chain dengan matriks references/chain-rules.md bagian 1.3 dan invarian pasangan bagian 1.4, atau minta gerbang mengklasifikasi ulang risk.",
            })
            return

        declared, declared_err = self._task_chain()
        if declared_err:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"TASK.md memuat chain asing: {declared_err}",
                "action": "Laporkan salah rute ke gerbang `backend:tech-lead`; chain TASK.md hanya boleh BRD_PRD_BRIEF | PRD_BRIEF | BRIEF.",
            })
            return
        if declared and declared != self.chain_arg:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"TASK.md sudah memateraikan chain {declared}, berbeda dari parameter {self.chain_arg}",
                "action": "Perubahan chain hanya sah lewat eskalasi Fase 5; kembalikan penyimpangan ini ke gerbang `backend:tech-lead`.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Chain {self.chain_arg} selaras dengan risk {self.risk_arg}",
            "action": "",
        })

    def _check_5_artifact_consistency(self):
        check_id = 5
        name = "Artifact vs Chain Consistency"

        if not self.td.ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Taskdir tidak tersedia untuk memeriksa konsistensi artefak",
                "action": "Selesaikan check 1 terlebih dahulu.",
            })
            return
        taskdir_path = self.td.path

        declared, declared_err = self._task_chain()
        if self.chain_arg in VALID_CHAINS:
            effective_chain = self.chain_arg
        elif self.chain_err or declared_err:
            # CHAIN_ARTIFACTS hanya diakses sesudah nilainya tervalidasi.
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Chain tidak sah; konsistensi artefak tak dapat dinilai ({self.chain_err or declared_err})",
                "action": "Laporkan salah rute ke gerbang `backend:tech-lead`; dilarang menghapus artefak atau menyesuaikan chain agar cocok.",
            })
            return
        else:
            effective_chain = declared
        present = {n for n in ("BRD.md", "PRD.md") if (taskdir_path / n).exists()}

        if not effective_chain:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": f"Chain belum ditetapkan; artefak rancangan terbaca: {', '.join(sorted(present)) or 'nihil'}",
                "action": "",
            })
            return

        stray = sorted(present - CHAIN_ARTIFACTS[effective_chain])
        if stray:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Taskdir memuat artefak di luar chain {effective_chain}: {', '.join(stray)}",
                "action": "Laporkan salah rute ke gerbang `backend:tech-lead`; dilarang menghapus artefak atau menyesuaikan chain agar cocok.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Artefak taskdir konsisten dengan chain {effective_chain}",
            "action": "",
        })

    def _check_6_git_worktree_and_status(self):
        check_id = 6
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
                    "action": "Commit, stash, atau bersihkan perubahan di luar taskdir sebelum rantai planning berangkat.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Working tree bersih di luar taskdir (siap untuk commit isolasi)",
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

    def _check_7_resume_point(self):
        """Titik resume taskdir berakar — informatif, selalu PASS.

        Taskdir yang sudah memuat `TASK.md` tidak memanggil `backend:task` lagi
        (prasyarat `task` check 3 menolaknya); titik masuknya dihitung di sini dari
        ledger `## Chain`, bukan ditebak model.
        """
        check_id, name = 7, "Resume Point"
        task = self.td.path / "TASK.md" if self.td.ok else None
        text = None
        if task and task.exists():
            try:
                text = read_text(task)
            except UnicodeDecodeError as exc:
                self.results.append({
                    "id": check_id, "name": name, "status": "FAIL",
                    "summary": f"TASK.md bukan UTF-8 ({exc.reason} @ byte {exc.start})",
                    "action": "Simpan ulang TASK.md sebagai UTF-8 (pulihkan dari git bila rusak); jangan menebak isinya.",
                })
                return
        if text is None:
            summary = "TASK.md belum ada — rantai baru (Fase 1)"
        else:
            ledger = re.search(r"^## Chain\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
            hops = re.findall(r"^- \[( |x|~)\] (BRD|PRD|BRIEF)\b", ledger.group(1) if ledger else "", re.M)
            top = next((h for mark, h in hops if mark in (" ", "~")), None)
            if top:
                summary = f"Resume: hop {top} (TASK.md ada; `task` tidak dipanggil)"
            elif hops:
                summary = "Resume: ledger tercentang penuh — butuh reentry_reason (Fase 3 butir 0)"
            else:
                summary = "Resume: TASK.md tanpa ledger `## Chain` — laporkan ke gerbang (lane non-planning)"
        if text is not None:
            counters = _counters.parse(text)
            summary += f" · Counters: {_counters.summary(counters)}"
        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": summary,
            "action": "",
        })

    def format_text(self) -> str:
        return format_text("analyst", self.results)

    def to_json(self) -> str:
        return to_json(self.root, self.results, taskdir=self.taskdir_arg, risk=self.risk_arg, chain=self.chain_arg)


def main():
    parser = argparse.ArgumentParser(description="Analyst Preconditions Checker")
    parser.add_argument("--taskdir", type=str, required=False, help="Task directory path")
    parser.add_argument("--risk", type=str, required=False, help="Risk level (BREAKING | MAJOR | MINOR)")
    parser.add_argument("--chain", type=str, default="auto", help="Chain enum (BRD_PRD_BRIEF | PRD_BRIEF | BRIEF | auto)")
    parser.add_argument("--root", type=str, default=None, help="Root path of target repository")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        taskdir=args.taskdir,
        risk=args.risk,
        chain=args.chain,
        target_root=target_root,
    )
    passed = checker.run_all()

    print(checker.to_json() if args.json else checker.format_text())
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    sys.exit(cli(main))
