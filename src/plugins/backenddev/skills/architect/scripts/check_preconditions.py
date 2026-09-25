#!/usr/bin/env python3
"""Architect Precondition Validator.

Automates verification of repository preconditions before architect skill execution.
Runs checks 1 through 7 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Impor intra-plugin:
`skills/_common/precondition_lib.py` (parser taskdir, status git, profil, berkas
plugin, keluaran) dan `skills/_common/brief_status.py`, di-bootstrap relatif
terhadap berkas ini.
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
    TASKDIR_ACTION,
    check_taskdir,
    dirty_paths,
    find_agent,
    find_repo_root,
    format_text,
    legacy_suffix,
    load_profile_index,
    plugin_file,
    to_json,
)
from brief_status import (  # noqa: E402
    BRIEF_STATUSES, CLOSED, landed_sha, read_halt, review_freshness, scan_briefs, validate_links,
)


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
        self._check_2_profile()
        self._check_3_brief_readiness()
        self._check_4_git_worktree()
        self._check_5_dispatchers()
        self._check_6_lifecycle_recovery()
        self._check_7_halt_marker()
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

    def _check_2_profile(self):
        check_id = 2
        name = "Profile Invariants & Commands"
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
        data, legacy_note, profile_dir = prof.data, prof.note, prof.dir

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
            "summary": f"Profil valid (stack: {data.get('stack')}, base_branch: {data.get('base_branch')})" + legacy_suffix(legacy_note),
            "action": "",
        })

    def _profile_base_branch(self) -> Optional[str]:
        """Field `base_branch` index.json profil; `None` bila tak terbaca (check 2 yang memvonisnya)."""
        data = load_profile_index(self.root, required=("base_branch",)).data
        return data["base_branch"].strip() if data and isinstance(data["base_branch"], str) else None

    def _add(self, cid: int, name: str, status: str, summary: str, action: str = "", entry: str = ""):
        self.results.append({
            "id": cid,
            "name": name,
            "status": status,
            "summary": summary,
            "action": action,
            "entry": entry,
        })

    def _check_3_brief_readiness(self):
        """Titik masuk sesi dari status brief di disk.

        `entry` adalah titik masuk yang dibaca Fase 1: `FASE_3:<NN>`, `FASE_4`,
        `FASE_5`, `TUNTAS`, atau `KOREKSI:<NN>:<sha7>` — brief `READY` yang commit
        ber-`commit_message`-nya sudah mendarat (matriks bukti disk, status tertinggal). Brief `BLOCKED` menahan rantai walau ada brief
        `READY` sesudahnya — Fase 1 berhenti di brief pertama yang terblokir.
        """
        cid, name = 3, "Brief Set & Readiness"
        td = self.td.path if self.td.ok else None
        if not td:
            return self._add(cid, name, "FAIL", "Taskdir tidak ditemukan untuk pemindaian brief",
                             "Selesaikan provisi taskdir terlebih dahulu.")
        briefs = scan_briefs(td)
        if not briefs:
            return self._add(cid, name, "FAIL", "Tidak ditemukan berkas brief-* di taskdir",
                             "Jalankan skill `backenddev:plan` untuk merumuskan brief sebelum orkestrasi.")
        # Status dibaca dari frontmatter saja (blok kode `status: DONE` di badan tidak
        # terhitung) dan dibandingkan persis; yang tak terbaca disebut beserta alasannya.
        bad = [f"{b['name']} tak terbaca ({b['why']})" for b in briefs if b["status"] not in BRIEF_STATUSES]
        bad += validate_links(briefs)
        if bad:
            return self._add(cid, name, "FAIL", "; ".join(bad),
                             "Kembalikan ke `backenddev:plan`; architect dilarang menyunting frontmatter brief.")
        blocked = [b["name"] for b in briefs if b["status"] == "BLOCKED"]
        if blocked:
            return self._add(cid, name, "FAIL", f"Brief BLOCKED menahan rantai: {', '.join(blocked)}",
                             "Kembalikan ke `backenddev:tech-lead` → lane PLANNING taskdir yang sama "
                             "(`reentry_reason` = brief + sebab `report-NN.md`); `plan` menerbitkan "
                             "pengganti ber-`supersedes`.")
        start = next((b for b in briefs if b["status"] not in CLOSED), None)
        if start:
            rel = f"{self.td.rel}/{start['name']}"
            sha = landed_sha(self.root, rel, start["commit_message"])
            if sha:
                return self._add(cid, name, "PASS", f"brief-{start['nn']} READY tetapi commit {sha} sudah mendarat",
                                 "Jalankan koreksi status (matriks bukti disk `lifecycle-recovery.md` bagian 3); "
                                 "dilarang dispatch ulang.", entry=f"KOREKSI:{start['nn']}:{sha}")
            return self._add(cid, name, "PASS", f"Titik mulai brief-{start['nn']} ({start['name']})",
                             entry=f"FASE_3:{start['nn']}")
        self._all_closed(cid, name, td, briefs)

    def _all_closed(self, cid: int, name: str, td: Path, briefs: List[Dict[str, Any]]):
        done = sum(b["status"] == "DONE" for b in briefs)
        closed = f"{done} DONE · {len(briefs) - done} SUPERSEDED"
        if not (td / "REVIEW.md").exists():
            return self._add(cid, name, "PASS", f"Seluruh brief tertutup ({closed}), REVIEW.md belum ada",
                             "Jalankan Fase 4 (verifikasi penutup lalu review).", entry="FASE_4")
        # REVIEW.md yang ada belum tentu menutup HEAD: brief perbaikan (P1, BLOCKED,
        # HALT) yang mendarat sesudahnya membuka putaran baru yang wajib diverifikasi
        # dan direview ulang, bukan dilompati ke Fase 5.
        fresh, why = review_freshness(self.root, self.td.rel)
        if not fresh:
            return self._add(cid, name, "PASS", f"Seluruh brief tertutup ({closed}); REVIEW.md basi — {why}",
                             "Jalankan Fase 4 ulang: verifikasi penutup lalu SATU review baru; dilarang lompat ke Fase 5.",
                             entry="FASE_4")
        if (td / "REPORT.md").exists():
            return self._add(cid, name, "PASS",
                             f"Seluruh brief tertutup ({closed}); {why}; REPORT.md sudah terbit (rantai tuntas)",
                             entry="TUNTAS")
        # Rantai tuntas menuntut DUA artefak penutup. REVIEW.md yang berdiri sendiri
        # berarti `report` gagal commit atau tak pernah berangkat di sesi sebelumnya;
        # Fase 1 menjemputnya di Fase 5, bukan memvonis rantai selesai.
        self._add(cid, name, "PASS", f"Seluruh brief tertutup ({closed}); {why}, REPORT.md belum ada",
                  "Lompat ke Fase 5 untuk memanen laporan rantai lewat `backenddev:report`; "
                  "dilarang mendispatch ulang implementor atau reviewer.", entry="FASE_5")

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

            # Laci kerja `.explore/` milik `code-explorer` bukan artefak rantai: tidak
            # pernah di-stage maupun di-commit, jadi dibuang dirty_paths.
            if dirty_paths(self.root):
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

            # Commit brief dan REVIEW.md wajib mendarat di branch kerja: detached HEAD
            # membuatnya hilang saat user kembali ke branch, dan HEAD = base branch
            # membuat rentang merge-base..HEAD kosong sementara commit langsung ke base.
            branch = subprocess.run(["git", "symbolic-ref", "-q", "--short", "HEAD"], cwd=self.root,
                                    capture_output=True, text=True).stdout.strip()
            if not branch:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Detached HEAD",
                    "action": "Checkout branch kerja taskdir sebelum orkestrasi.",
                })
                return
            base = self.base_branch_arg or self._profile_base_branch()
            if base and branch == base:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"HEAD berada di base branch `{base}`",
                    "action": "Buat/checkout branch kerja taskdir; rentang review kosong di base branch.",
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


        reviewer_dispatcher = skill_dir / "dispatcher" / "reviewer.md"


        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/implementor.md tidak ditemukan di skill architect",
                "action": "Pastikan template dispatcher/implementor.md tersedia untuk dispatch code-implementor.",
            })
            return

        if not find_agent("code-implementor"):
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

        if not find_agent("code-reviewer"):
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
        if not plugin_file("skills", "architect", "references", "lifecycle-recovery.md"):
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

    def _check_7_halt_marker(self):
        """`{taskdir}/HALT.md` ter-commit menahan rantai lintas sesi.

        Vonis gerbang kompilasi, scope, simbol, dan berkas liar jatuh sesudah
        brief ter-commit `DONE`; tanpa penanda di disk sesi berikutnya memilih
        `NN+1` dan melanjutkan di atas kode yang diketahui rusak.
        """
        cid, name = 7, "Halt Marker"
        fm = read_halt(self.td.path) if self.td.ok else None
        if fm is not None:
            return self._add(
                cid, name, "FAIL",
                f"HALT.md menahan rantai di {fm.get('brief', '?')} "
                f"(verdict {fm.get('verdict', '?')} @ {fm.get('sha', '?')})",
                "Kembalikan ke `backenddev:tech-lead`: SCOPE → tanya user terima/reset; COMPILE/SYMBOL/STRAY → "
                "lane PLANNING taskdir sama, `plan` menambah baris `repairs`. Architect dilarang menghapus HALT.md.")
        self._add(cid, name, "PASS", "Tidak ada HALT.md")

    def format_text(self) -> str:
        return format_text("architect", self.results, entry_label="Titik masuk")

    def to_json(self) -> str:
        return to_json(self.root, self.results, taskdir=self.taskdir_arg)


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
