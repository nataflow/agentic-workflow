#!/usr/bin/env python3
"""Architect Precondition Validator.

Automates verification of repository preconditions before architect skill execution.
Runs checks 1 through 6 in a single pass and produces a compact, actionable report.
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
        """Run checks 1 through 6."""
        self._check_1_taskdir()
        self._check_2_profile()
        self._check_3_brief_readiness()
        self._check_4_git_worktree()
        self._check_5_dispatchers()
        self._check_6_lifecycle_recovery()
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
                "action": "Pastikan direktori taskdir telah diprovisi oleh gerbang `backenddev:tech-lead`.",
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
        name = "Profile Invariants & Commands"
        profile_dir = self.root / ".claude" / "profile"
        index_file = profile_dir / "index.json"

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
            required_keys = ["base_branch", "commit_convention", "source_root", "stack"]
            missing = [k for k in required_keys if not data.get(k)]
            if missing:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Field kritis hilang di index.json: {', '.join(missing)}",
                    "action": "Jalankan `backenddev:profile` untuk melengkapi field profil.",
                })
                return
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Format JSON corrupt pada index.json: {e}",
                "action": "Perbaiki format JSON atau inisialisasi ulang via `backenddev:profile`.",
            })
            return

        required_docs = ["commands.md", "invariants.md"]
        missing_docs = [doc for doc in required_docs if not (profile_dir / doc).exists()]
        if missing_docs:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Dokumen profil wajib hilang: {', '.join(missing_docs)}",
                "action": "Jalankan `backenddev:profile` untuk melengkapi dokumen profil.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Profil valid (stack: {data.get('stack')}, base_branch: {data.get('base_branch')})",
            "action": "",
        })

    def _check_3_brief_readiness(self):
        check_id = 3
        name = "Brief Set & Readiness"
        taskdir_path = self._resolve_taskdir()
        if not taskdir_path or not taskdir_path.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Taskdir tidak ditemukan untuk pemindaian brief",
                "action": "Selesaikan provisi taskdir terlebih dahulu.",
            })
            return

        brief_files = sorted(taskdir_path.glob("brief-*.md"))
        if not brief_files:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Tidak ditemukan berkas brief-* di taskdir",
                "action": "Jalankan skill `backenddev:plan` untuk merumuskan brief sebelum orkestrasi.",
            })
            return

        ready_count = 0
        done_count = 0
        blocked_count = 0
        other_count = 0

        for bf in brief_files:
            try:
                content = bf.read_text(encoding="utf-8")
                match = re.search(r"^status:\s*([A-Z_]+)", content, re.MULTILINE)
                st = match.group(1) if match else "UNKNOWN"
                if st == "READY":
                    ready_count += 1
                elif st == "DONE":
                    done_count += 1
                elif st == "BLOCKED":
                    blocked_count += 1
                else:
                    other_count += 1
            except Exception:
                other_count += 1

        review_file = taskdir_path / "REVIEW.md"
        report_file = taskdir_path / "REPORT.md"
        if ready_count == 0 and done_count == len(brief_files) and review_file.exists():
            # Rantai tuntas menuntut DUA artefak penutup. REVIEW.md yang berdiri sendiri
            # berarti `report` gagal commit atau tak pernah berangkat di sesi sebelumnya;
            # Fase 1 menjemputnya di Fase 5, bukan memvonis rantai selesai.
            if report_file.exists():
                summary = f"Seluruh {done_count} brief DONE; REVIEW.md dan REPORT.md sudah terbit (rantai tuntas)"
                action = ""
            else:
                summary = f"Seluruh {done_count} brief DONE dan REVIEW.md terbit, REPORT.md belum ada"
                action = "Lompat ke Fase 5 untuk memanen laporan rantai lewat `backenddev:report`; dilarang mendispatch ulang implementor atau reviewer."
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": summary,
                "action": action,
            })
            return

        if ready_count == 0 and done_count == len(brief_files):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": f"Seluruh {done_count} brief DONE, siap masuk gerbang penutup REVIEW.md",
                "action": "",
            })
            return

        if ready_count == 0:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Nol brief berstatus READY (DONE: {done_count}, BLOCKED: {blocked_count}, OTHER: {other_count})",
                "action": "Pastikan minimal satu brief berstatus READY atau selesaikan status BLOCKED.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"{len(brief_files)} brief terdeteksi ({ready_count} READY, {done_count} DONE)",
            "action": "",
        })

    def _check_4_git_worktree(self):
        check_id = 4
        name = "Git Worktree & Status"
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
                    "summary": "Bukan repositori git yang valid",
                    "action": "Jalankan pada repositori git aktif.",
                })
                return

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
                    "summary": "Working tree git kotor sebelum rantai orkestrasi dimulai",
                    "action": "Bersihkan atau simpan perubahan uncommitted sebelum memulai orkestrasi architect.",
                })
                return

            # Check rebase in progress
            git_dir = Path(subprocess.check_output(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            ).strip())
            if not git_dir.is_absolute():
                git_dir = self.root / git_dir
            if (git_dir / "rebase-apply").exists() or (git_dir / "rebase-merge").exists():
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Operasi git rebase sedang berlangsung",
                    "action": "Selesaikan atau batalkan git rebase sebelum melanjutkan.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Working tree bersih dan siap dieksekusi",
                "action": "",
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca status git: {e}",
                "action": "Periksa koneksi dan integritas repositori git.",
            })

    def _check_5_dispatchers(self):
        """Dua template dispatch architect beserta definisi agentnya.

        `architect` mendispatch `code-implementor` lewat `dispatcher/implementor.md`
        dan `code-reviewer` lewat `dispatcher/reviewer.md`, keduanya langsung tanpa
        skill pembungkus. Rantai eksekusi tidak dapat dimulai tanpa yang pertama, dan
        Fase 4 tidak dapat ditutup tanpa yang kedua.
        """
        check_id = 5
        name = "Implementor & Reviewer Dispatcher"
        skill_dir = Path(__file__).resolve().parent.parent
        dispatcher_file = skill_dir / "dispatcher" / "implementor.md"

        candidate_agents = [
            skill_dir.parent.parent / "agents" / "code-implementor.md",
            self.root / "src" / "plugins" / "backenddev" / "agents" / "code-implementor.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "agents" / "code-implementor.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "agents" / "code-implementor.md",
        ]

        reviewer_dispatcher = skill_dir / "dispatcher" / "reviewer.md"

        candidate_reviewer_agents = [
            skill_dir.parent.parent / "agents" / "code-reviewer.md",
            self.root / "src" / "plugins" / "backenddev" / "agents" / "code-reviewer.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "agents" / "code-reviewer.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "agents" / "code-reviewer.md",
        ]

        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/implementor.md tidak ditemukan di skill architect",
                "action": "Pastikan template dispatcher/implementor.md tersedia untuk dispatch code-implementor.",
            })
            return

        if not any(p.exists() for p in candidate_agents):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/code-implementor.md tidak ditemukan",
                "action": "Pastikan berkas agents/code-implementor.md tersedia di plugin backenddev.",
            })
            return

        if not reviewer_dispatcher.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/reviewer.md tidak ditemukan di skill architect",
                "action": "Pastikan template dispatcher/reviewer.md tersedia untuk dispatch code-reviewer.",
            })
            return

        if not any(p.exists() for p in candidate_reviewer_agents):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/code-reviewer.md tidak ditemukan",
                "action": "Pastikan berkas agents/code-reviewer.md tersedia di plugin backenddev.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Template dispatcher/implementor.md + reviewer.md dan agent code-implementor.md + code-reviewer.md terverifikasi",
            "action": "",
        })

    def _check_6_lifecycle_recovery(self):
        check_id = 6
        name = "Lifecycle Recovery Reference"
        ref_paths = [
            self.root / "src" / "plugins" / "backenddev" / "skills" / "architect" / "references" / "lifecycle-recovery.md",
            Path(__file__).resolve().parent.parent / "references" / "lifecycle-recovery.md",
        ]
        found = any(p.exists() for p in ref_paths)
        if not found:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas references/lifecycle-recovery.md tidak ditemukan",
                "action": "Pastikan referensi recovery architect tersedia di direktori skill.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Referensi pemulihan state lifecycle-recovery.md tersedia",
            "action": "",
        })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: architect [{status_label}] ({passed_count}/{total} passed)",
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
    parser = argparse.ArgumentParser(description="Architect Preconditions Checker")
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
