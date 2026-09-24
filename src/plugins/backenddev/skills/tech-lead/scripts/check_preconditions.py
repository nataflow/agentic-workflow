#!/usr/bin/env python3
"""Tech-Lead Precondition Validator.

Automates verification of repository preconditions before tech-lead gateway execution.
Runs checks 1 through 6 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` untuk uji izin tulis, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional


# Zona artefak yang kepemilikan commit-nya ada di gerbang tech-lead
# (references/gate-scope.md bagian 3). Pada mode re-entry berkas kotor di
# bawah prefix ini menunggu commit Fase 5, jadi tidak menggagalkan check 3.
RE_ENTRY_ALLOWED_PREFIXES = (
    ".claude/profile/",
    "backenddev/docs/",
    "backenddev/issues/",
    "docs/api/",
)


# Helper izin tulis dipakai bersama lintas skrip prasyarat; rumah kanoniknya
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd — skrip dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    nearest_existing_ancestor as _nearest_existing_ancestor,
    probe_writable as _probe_writable,
    profile_staleness as _profile_staleness,
)


class PreconditionChecker:
    def __init__(self, target_root: Optional[Path] = None, re_entry: bool = False):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.re_entry = re_entry
        self.results: List[Dict[str, Any]] = []

    def _find_repo_root(self) -> Path:
        """Find the git repository root or fallback to cwd."""
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
            if out and os.path.isdir(out):
                return Path(out)
        except Exception:
            pass
        return Path.cwd()

    def run_all(self) -> bool:
        """Run checks 1 through 6."""
        self._check_1_profile()
        self._check_2_git_worktree_and_head()
        self._check_3_git_status()
        self._check_4_write_access()
        self._check_5_commands()
        self._check_6_explorer_dispatcher()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_profile(self):
        check_id = 1
        name = "Profile Index & Invariants"
        profile_dir = self.root / ".claude" / "profile"
        index_file = profile_dir / "index.json"
        module_file = profile_dir / "module-structure.md"
        invariants_file = profile_dir / "invariants.md"

        if not index_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Missing .claude/profile/index.json",
                "action": "Arahkan user ke `backenddev:profile` untuk inisialisasi profil repo."
            })
            return

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            required_keys = [
                "root_namespace", "source_root", "base_branch",
                "branch_convention", "commit_convention", "stack", "architecture"
            ]
            missing_keys = [k for k in required_keys if not data.get(k)]
            if missing_keys:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Field kritis hilang/kosong di index.json: {', '.join(missing_keys)}",
                    "action": "Jalankan `backenddev:profile` untuk memperbarui field profil."
                })
                return
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Corrupt index.json: {e}",
                "action": "Perbaiki format JSON atau inisialisasi ulang via `backenddev:profile`."
            })
            return

        missing_docs = []
        if not module_file.exists():
            missing_docs.append("module-structure.md")
        if not invariants_file.exists():
            missing_docs.append("invariants.md")

        if missing_docs:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Dokumen profil belum lengkap: {', '.join(missing_docs)}",
                "action": "Lengkapi berkas profil di .claude/profile/ atau jalankan profile refresh."
            })
            return

        # Kesegaran profil: non-blocking, dilaporkan sebagai degradasi.
        # Profil yang tertinggal di belakang kode melebarkan batas cakupan
        # `code-explorer` dan membuat permukaan baru tak terdaftar, tanpa
        # satu pun kegagalan tercatat.
        self.profile_freshness = _profile_staleness(
            self.root, data.get("source_root", "")
        )
        freshness_suffix = (
            f" · profil TERDEGRADASI: {self.profile_freshness[1]}"
            if self.profile_freshness[0] == "BASI" else ""
        )
        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Profil valid (stack: {data.get('stack', 'unknown')}, base: {data.get('base_branch', 'unknown')}){freshness_suffix}",
            "action": ""
        })

    def _check_2_git_worktree_and_head(self):
        check_id = 2
        name = "Git Worktree & HEAD State"
        try:
            inside = subprocess.check_output(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
            if inside != "true":
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Bukan repositori git yang valid",
                    "action": "Inisialisasi repositori git atau buka direktori kerja yang valid."
                })
                return

            branch_out = subprocess.check_output(
                ["git", "symbolic-ref", "-q", "--short", "HEAD"],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()

            if not branch_out:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "HEAD detached",
                    "action": "Checkout ke branch aktif (misal base_branch) sebelum melanjutkan."
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": f"Git repo valid (HEAD di branch '{branch_out}')",
                "action": ""
            })
        except subprocess.CalledProcessError:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Gagal membaca status git (HEAD detached atau repositori rusak)",
                "action": "Pastikan HEAD terhubung ke branch aktif dan direktori memiliki .git sah."
            })

    @staticmethod
    def _porcelain_paths(status_out: str) -> List[str]:
        """Ambil path relatif dari tiap baris `git status --porcelain` v1.

        Tiap baris berbentuk `XY <path>`; rename/copy berbentuk
        `XY <lama> -> <baru>`; path ber-spasi atau non-ASCII dibungkus kutip.
        """
        paths = []
        for line in status_out.splitlines():
            if not line.strip():
                continue
            path = line[3:] if len(line) > 3 else line.strip()
            if " -> " in path:
                path = path.split(" -> ")[-1]
            path = path.strip()
            if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
                path = path[1:-1]
            if path:
                paths.append(path)
        return paths

    def _check_3_git_status(self):
        check_id = 3
        name = "Git Clean Working Tree"
        try:
            # `-uall` mencegah git meringkas direktori untracked jadi satu baris
            # (`docs/`), yang membuat perbandingan prefix zona artefak meleset.
            status_out = subprocess.check_output(
                ["git", "status", "--porcelain", "-uall"],
                cwd=self.root,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            )

            # Laci kerja `.explore/` milik `code-explorer` bukan artefak rantai:
            # tidak pernah di-stage maupun di-commit, jadi tidak dihitung kotor.
            dirty_paths = [
                p for p in self._porcelain_paths(status_out)
                if ".explore" not in p.rstrip("/").split("/")
            ]

            if dirty_paths:
                if self.re_entry:
                    outside = [p for p in dirty_paths if not p.startswith(RE_ENTRY_ALLOWED_PREFIXES)]

                    if outside:
                        sample = ", ".join(outside[:3])
                        if len(outside) > 3:
                            sample += f", +{len(outside) - 3} lainnya"
                        self.results.append({
                            "id": check_id,
                            "name": name,
                            "status": "FAIL",
                            "summary": f"Mode re-entry: {len(outside)} berkas kotor di luar zona artefak ({sample})",
                            "action": "Minta user stash atau commit berkas di luar zona artefak sebelum melanjutkan re-entry."
                        })
                        return

                    self.results.append({
                        "id": check_id,
                        "name": name,
                        "status": "PASS",
                        "summary": f"Mode re-entry: {len(dirty_paths)} berkas artefak menunggu commit gerbang, nol berkas di luar zona artefak",
                        "action": ""
                    })
                    return

                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Working tree kotor ({len(dirty_paths)} berkas uncommitted)",
                    "action": "Minta user stash atau commit perubahan sebelum membuat taskdir/branch."
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Working tree bersih (0 perubahan uncommitted)",
                "action": ""
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal menjalankan git status: {e}",
                "action": "Periksa akses dan integritas git."
            })

    def _check_4_write_access(self):
        check_id = 4
        name = "Workspace Write Access"
        test_dirs = [self.root / "backenddev" / "docs", self.root / "backenddev" / "issues"]
        unwritable = []

        # Gerbang berjalan juga pada lane EXPLORE_FACT dan PROFILE yang dilarang
        # mengalokasikan direktori apa pun (SKILL.md Fase 3). Karena itu check ini
        # hanya memeriksa izin tulis induk terdekat, tidak membuat backenddev/.
        for d in test_dirs:
            ok, _ = _probe_writable(d)
            if not ok:
                unwritable.append(str(d.relative_to(self.root) if d.is_relative_to(self.root) else d))

        if unwritable:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Zona artefak tidak dapat ditulis: {', '.join(unwritable)}",
                "action": "Periksa hak akses tulis pada induk direktori backenddev/."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Zona artefak backenddev/docs/ dan backenddev/issues/ dapat ditulis",
            "action": ""
        })

    def _check_5_commands(self):
        check_id = 5
        name = "Profile Commands"
        commands_file = self.root / ".claude" / "profile" / "commands.md"
        if not commands_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas .claude/profile/commands.md tidak ditemukan",
                "action": "Jalankan `backenddev:profile` untuk mencatat perintah build dan test."
            })
            return

        try:
            content = commands_file.read_text(encoding="utf-8").lower()
            has_build = "build" in content or "compile" in content
            has_test = "test" in content

            if not (has_build and has_test):
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Perintah build atau test belum didefinisikan di commands.md",
                    "action": "Lengkapi seksi ## Commands dengan instruksi build dan test yang sah."
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Perintah build dan test terdefinisi di commands.md",
                "action": ""
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca commands.md: {e}",
                "action": "Periksa permissions berkas .claude/profile/commands.md."
            })

    def _check_6_explorer_dispatcher(self):
        """Template dispatch code-explorer milik gerbang beserta definisi agentnya.

        Gerbang mendispatch `code-explorer` langsung lewat `dispatcher/explorer.md`,
        tanpa skill pembungkus. Template itu satu-satunya prompt dispatch yang sah di
        Fase 1 butir 2; tanpanya pemicu dispatch wajib bagian 4E tidak punya jalur
        berangkat dan gerbang diam-diam jatuh ke sapuan manual berkuota.
        """
        check_id = 6
        name = "Explorer Dispatcher & Agent"
        skill_dir = Path(__file__).resolve().parent.parent
        dispatcher_file = skill_dir / "dispatcher" / "explorer.md"

        candidate_agents = [
            skill_dir.parent.parent / "agents" / "code-explorer.md",
            self.root / "src" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
        ]

        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/explorer.md tidak ditemukan di skill tech-lead",
                "action": "Pastikan template dispatcher/explorer.md tersedia untuk dispatch langsung code-explorer."
            })
            return

        if not any(p.exists() for p in candidate_agents):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/code-explorer.md tidak ditemukan",
                "action": "Pastikan berkas agents/code-explorer.md tersedia di plugin backenddev."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Template dispatcher/explorer.md dan agent code-explorer.md terverifikasi",
            "action": ""
        })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        mode_label = " · mode: re-entry" if self.re_entry else ""
        lines = [
            f"PRECONDITION CHECK: tech-lead [{status_label}] ({passed_count}/{total} passed){mode_label}",
        ]
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<28} : {r['status']} ({r['summary']})")
            if r["status"] == "FAIL" and r["action"]:
                lines.append(f"    * Tindakan: {r['action']}")

        freshness = getattr(self, "profile_freshness", None)
        if freshness and freshness[0] == "BASI":
            lines.insert(0, f"[TERDEGRADASI] profil basi — {freshness[1]}")

        return "\n".join(lines)

    def to_json(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        return json.dumps({
            "status": "PASS" if all_passed else "FAIL",
            "passed_count": sum(1 for r in self.results if r["status"] == "PASS"),
            "total_count": len(self.results),
            "root": str(self.root),
            "re_entry": self.re_entry,
            "profile_freshness": getattr(self, "profile_freshness", ("TAK_TERNILAI", "belum dinilai"))[0],
            "checks": self.results
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Tech-Lead Preconditions Checker")
    parser.add_argument("--root", type=str, default=None, help="Root path of target repository")
    parser.add_argument(
        "--re-entry",
        action="store_true",
        help="Re-entry mode: berkas kotor di zona artefak gerbang tidak menggagalkan check 3"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(target_root=target_root, re_entry=args.re_entry)
    passed = checker.run_all()

    if args.json:
        print(checker.to_json())
    else:
        print(checker.format_text())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
