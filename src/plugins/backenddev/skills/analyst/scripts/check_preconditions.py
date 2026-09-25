#!/usr/bin/env python3
"""Analyst Precondition Validator.

Automates verification of repository preconditions before analyst skill execution.
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

VALID_RISKS = {"BREAKING", "MAJOR", "MINOR"}

VALID_CHAINS = {"BRD_PRD_BRIEF", "PRD_BRIEF", "BRIEF"}

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
        self.root = (target_root or self._find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.risk_arg = (risk or "").strip().upper() if risk else None
        self.chain_arg = (chain or "auto").strip().upper()
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
        self._check_3_risk()
        self._check_4_chain()
        self._check_5_artifact_consistency()
        self._check_6_git_worktree_and_status()
        self._check_7_resume_point()
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

    def _declared_chain(self) -> Optional[str]:
        """Baca nilai `chain:` dari frontmatter TASK.md bila berkasnya sudah ada."""
        taskdir_path = self._resolve_taskdir()
        if not taskdir_path:
            return None
        task_file = taskdir_path / "TASK.md"
        if not task_file.exists():
            return None
        try:
            content = task_file.read_text(encoding="utf-8")
        except Exception:
            return None
        match = re.search(r"^chain:\s*([A-Z_]+)\s*$", content, re.MULTILINE)
        return match.group(1).upper() if match else None

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
                "action": "Pastikan gerbang `backenddev:tech-lead` telah memprovisi direktori taskdir sebelum memanggil skill analyst.",
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
        profile_dir, legacy_note = resolve_profile_dir(self.root)
        index_file = profile_dir / "index.json"

        if not index_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas .claude/profile/backenddev/index.json tidak ditemukan",
                "action": "Jalankan skill `backenddev:profile` untuk membuat profil repositori.",
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
                "action": "Sertakan --risk <BREAKING | MAJOR | MINOR> hasil Keputusan 2 gerbang `backenddev:tech-lead`.",
            })
            return

        if self.risk_arg not in VALID_RISKS:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Risk level '{self.risk_arg}' tidak sah (wajib BREAKING | MAJOR | MINOR)",
                "action": "Minta gerbang `backenddev:tech-lead` menetapkan risk level; dilarang menebak sendiri.",
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

        if self.chain_arg not in VALID_CHAINS:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Chain '{self.chain_arg}' tidak sah (wajib BRD_PRD_BRIEF | PRD_BRIEF | BRIEF | auto)",
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

        declared = self._declared_chain()
        if declared and declared != self.chain_arg:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"TASK.md sudah memateraikan chain {declared}, berbeda dari parameter {self.chain_arg}",
                "action": "Perubahan chain hanya sah lewat eskalasi Fase 5; kembalikan penyimpangan ini ke gerbang `backenddev:tech-lead`.",
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

        taskdir_path = self._resolve_taskdir()
        if not taskdir_path or not taskdir_path.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Taskdir tidak tersedia untuk memeriksa konsistensi artefak",
                "action": "Selesaikan check 1 terlebih dahulu.",
            })
            return

        effective_chain = self.chain_arg if self.chain_arg in VALID_CHAINS else self._declared_chain()
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
                "action": "Laporkan salah rute ke gerbang `backenddev:tech-lead`; dilarang menghapus artefak atau menyesuaikan chain agar cocok.",
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
            status_output = subprocess.check_output(
                ["git", "status", "--porcelain", "-uall"],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            ).splitlines()

            rel_taskdir = self._get_rel_taskdir_str().rstrip("/")
            dirty_outside: List[str] = []
            for line in status_output:
                if not line.strip():
                    continue
                file_part = line[3:].strip().rstrip("/")
                if " -> " in file_part:
                    file_part = file_part.split(" -> ")[-1].strip().rstrip("/")

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
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal memeriksa git status: {e}",
                "action": "Periksa kondisi repositori git.",
            })

    def _check_7_resume_point(self):
        """Titik resume taskdir berakar — informatif, selalu PASS.

        Taskdir yang sudah memuat `TASK.md` tidak memanggil `backenddev:task` lagi
        (prasyarat `task` check 3 menolaknya); titik masuknya dihitung di sini dari
        ledger `## Chain`, bukan ditebak model.
        """
        check_id, name = 7, "Resume Point"
        taskdir_path = self._resolve_taskdir()
        task = taskdir_path / "TASK.md" if taskdir_path else None
        if not task or not task.exists():
            summary = "TASK.md belum ada — rantai baru (Fase 1)"
        else:
            text = task.read_text(encoding="utf-8")
            ledger = re.search(r"^## Chain\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
            hops = re.findall(r"^- \[( |x|~)\] (BRD|PRD|BRIEF)\b", ledger.group(1) if ledger else "", re.M)
            top = next((h for mark, h in hops if mark in (" ", "~")), None)
            if top:
                summary = f"Resume: hop {top} (TASK.md ada; `task` tidak dipanggil)"
            elif hops:
                summary = "Resume: ledger tercentang penuh — butuh reentry_reason (Fase 3 butir 0)"
            else:
                summary = "Resume: TASK.md tanpa ledger `## Chain` — laporkan ke gerbang (lane non-planning)"
        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": summary,
            "action": "",
        })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: analyst [{status_label}] ({passed_count}/{total} passed)",
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
            "risk": self.risk_arg,
            "chain": self.chain_arg,
            "checks": self.results,
        }, indent=2)


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
    main()
