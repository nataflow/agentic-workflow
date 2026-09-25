#!/usr/bin/env python3
"""Profile Precondition Validator.

Automates verification of repository preconditions before repository profiling execution.
Runs checks 1 through 6 in a single pass and produces a compact, actionable report.
Check 6 menyelesaikan mode operasi (GENERATE / REFRESH / MIGRATE) dan kepemilikan
profil, sehingga profil milik plugin lain tidak pernah dibaca sebagai REFRESH.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` (uji izin tulis, resolver profil, dan deteksi
`hooks/detect.py`), di-bootstrap relatif terhadap berkas ini.
"""

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Helper izin tulis dipakai bersama lintas skrip prasyarat; rumah kanoniknya
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd — skrip dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    LEGACY_PROFILE_DIR_REL,
    PLUGIN,
    PROFILE_DIR_REL,
    _detect,
    find_repo_root,
    foreign_owner,
    format_text,
    probe_writable as _probe_writable,
    to_json,
)


class PreconditionChecker:
    def __init__(
        self,
        mode: Optional[str] = None,
        stack: Optional[str] = None,
        profile_dir: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.mode_arg = mode
        self.stack_arg = stack
        self.profile_dir_arg = profile_dir or PROFILE_DIR_REL
        self.results: List[Dict[str, Any]] = []
        self.mode: str = ""


    def run_all(self) -> bool:
        """Run checks 1 through 6."""
        self._check_1_backend_manifest()
        self._check_2_stack_adapter()
        self._check_3_profile_dir_writable()
        self._check_4_git_worktree()
        self._check_5_references()
        self._check_6_mode_ownership()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_backend_manifest(self):
        # Deteksi yang sama dengan hook SessionStart (`hooks/detect.py`): penanda
        # framework server, bukan sekadar keberadaan manifest. Repo React murni
        # yang hanya punya `package.json` tidak lolos.
        check_id = 1
        name = "Backend Manifest Detection"
        hits = _detect.detect_backend(self.root)
        if not hits:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Nol penanda framework server backend di root, workspace, apps/*, packages/*, services/*, maupun anak langsung root",
                "action": "Repo bukan target backenddev; jangan buat profil.",
            })
            return

        stacks = sorted({h.stack for h in hits})
        summary = ", ".join(f"{h.path} → {h.stack}" for h in hits[:4])
        if len(stacks) > 1:
            summary += " (monorepo multi-stack: pilih `stack`)"
        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": summary,
            "action": "",
        })

    def _check_2_stack_adapter(self):
        check_id = 2
        name = "Stack Adapter Availability"
        skill_dir = Path(__file__).resolve().parent.parent

        contract_file = skill_dir / "stacks" / "_CONTRACT.md"
        if not contract_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas stacks/_CONTRACT.md tidak ditemukan",
                "action": "Pastikan direktori stacks pada skill profile terpasang lengkap.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Koleksi adapter stack dan kontrak stacks/_CONTRACT.md tersedia",
            "action": "",
        })

    def _check_3_profile_dir_writable(self):
        check_id = 3
        name = "Profile Directory Write Access"
        if self.profile_dir_arg.strip("/") != PROFILE_DIR_REL:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"`--profile-dir {self.profile_dir_arg}` ditolak; profil {PLUGIN} hanya sah di `{PROFILE_DIR_REL}/`",
                "action": "Jalankan ulang tanpa `--profile-dir`.",
            })
            return
        target_dir = Path(self.profile_dir_arg)
        if not target_dir.is_absolute():
            target_dir = self.root / target_dir

        # Direktori profil dibuat saat profil ditulis, bukan oleh skrip check.
        ok, detail = _probe_writable(target_dir)
        if not ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori profil {target_dir} tidak memiliki izin tulis: {detail}",
                "action": f"Periksa hak akses penulisan ke direktori {PROFILE_DIR_REL}/.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Direktori {self.profile_dir_arg} siap ditulis",
            "action": "",
        })

    def _check_4_git_worktree(self):
        check_id = 4
        name = "Git Inspection Access"
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
                    "action": "Inisialisasi repositori git agar riwayat commit dan branch convention dapat dipindai.",
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Repositori git valid untuk pemindaian commit & branch conventions",
                "action": "",
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca status git: {e}",
                "action": "Pastikan git CLI tersedia.",
            })

    def _check_5_references(self):
        check_id = 5
        name = "Scan Guides & Templates"
        skill_dir = Path(__file__).resolve().parent.parent

        scan_guide = skill_dir / "references" / "scan-guide.md"
        conv_scan = skill_dir / "references" / "convention-scan.md"
        tpl_file = skill_dir / "templates" / "profile-template.md"

        missing = []
        if not scan_guide.exists():
            missing.append("references/scan-guide.md")
        if not conv_scan.exists():
            missing.append("references/convention-scan.md")
        if not tpl_file.exists():
            missing.append("templates/profile-template.md")

        if missing:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Berkas pendukung profile hilang: {', '.join(missing)}",
                "action": "Pastikan plugin backenddev:profile terpasang utuh.",
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Panduan pemindaian scan-guide.md, convention-scan.md, dan profile-template.md tersedia",
            "action": "",
        })

    def _check_6_mode_ownership(self):
        """GENERATE / REFRESH / MIGRATE dan kepemilikan profil.

        REFRESH hanya bila `.claude/profile/backenddev/index.json` ada dan milik
        plugin ini. Profil backenddev di lokasi lama → MIGRATE. Profil milik plugin
        lain tidak pernah menjadi REFRESH: di direktori sendiri FAIL, di lokasi
        lama diabaikan (GENERATE ke direktori sendiri).
        """
        check_id = 6
        name = "Mode & kepemilikan profil"
        own = self.root / PROFILE_DIR_REL
        if (own / "index.json").is_file():
            owner = foreign_owner(own)
            if owner:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"`{PROFILE_DIR_REL}/index.json` milik `{owner}`; bukan profil {PLUGIN}",
                    "action": "Jangan menimpa profil plugin lain, juga dengan `force: true`. Laporkan ke user; profil itu salah tempat.",
                })
                return
            actual, note = "REFRESH", "index.json ada"
        else:
            legacy = _detect.read_profile(self.root, PLUGIN)
            if legacy.location == "legacy" and legacy.state not in ("ABSENT", "OTHER_OWNER", "INVALID_JSON"):
                actual = "MIGRATE"
                note = (f"profil {PLUGIN} masih di lokasi lama `{LEGACY_PROFILE_DIR_REL}/`; "
                        f"pindahkan ke `{PROFILE_DIR_REL}/` lewat `migrate_profile.py`")
            elif legacy.state == "OTHER_OWNER":
                actual = "GENERATE"
                note = (f"profil lama milik `{legacy.owner}` di `{LEGACY_PROFILE_DIR_REL}/` diabaikan; "
                        f"profil {PLUGIN} ditulis ke `{PROFILE_DIR_REL}/`")
            elif legacy.location == "legacy" and legacy.state == "INVALID_JSON":
                actual = "GENERATE"
                note = (f"`{LEGACY_PROFILE_DIR_REL}/index.json` bukan JSON valid dan tidak disentuh; "
                        f"profil {PLUGIN} ditulis ke `{PROFILE_DIR_REL}/`")
            else:
                actual, note = "GENERATE", "index.json belum ada"
        asked = (self.mode_arg or "auto").lower()
        self.mode = actual
        if asked in ("generate", "refresh", "migrate") and asked.upper() != actual:
            note += f"; parameter `mode` = `{asked.upper()}` diabaikan, keadaan disk menang"
        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"`{self.mode}` — {note}",
            "action": "",
        })

    def format_text(self) -> str:
        return format_text("profile", self.results,
                           footer=[f"Terselesaikan: mode `{self.mode or 'tidak terselesaikan'}`"])

    def to_json(self) -> str:
        return to_json(self.root, self.results, profile_dir=self.profile_dir_arg, mode=self.mode)


def main():
    parser = argparse.ArgumentParser(description="Profile Preconditions Checker")
    parser.add_argument("--mode", type=str, default=None, help="Execution mode (auto, generate, refresh, migrate)")
    parser.add_argument("--stack", type=str, default=None, help="Stack identifier override")
    parser.add_argument("--profile-dir", type=str, default=None, help=f"Target profile directory; hanya {PROFILE_DIR_REL} yang diterima")
    parser.add_argument("--root", type=str, default=None, help="Target repo root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        mode=args.mode,
        stack=args.stack,
        profile_dir=args.profile_dir,
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
