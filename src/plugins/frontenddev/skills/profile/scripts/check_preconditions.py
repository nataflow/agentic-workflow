#!/usr/bin/env python3
"""Profile Precondition Validator.

Memvonis prasyarat `frontenddev:profile` sebelum Phase 0 dibuka: keberadaan
manifest frontend, keterbacaan adapter stack, izin tulis direktori profil,
ketersediaan worktree git, dan kelengkapan berkas referensi skill.

Skrip ini juga **menyelesaikan dua fakta** yang dipakai Workflow dan
mengembalikannya di footer: `<stack-id>` hasil deteksi dan mode operasi
(`GENERATE` atau `REFRESH`). Keduanya deterministik; menyerahkannya ke
pembacaan model membuat repo yang sama divonis berbeda antar-sesi.

Vonis `WARN` tidak menahan: repo non-git tetap dapat diprofil — hanya kolom
konvensi commit yang lahir `UNINITIALIZED`, persis seperti `## Failure path`
baris repositori non-git menetapkan.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Bootstrap path relatif terhadap berkas ini, bukan terhadap cwd — skrip
# dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    KNOWN_STACKS,
    candidate_manifests,
    detect_stack,
    is_next,
    probe_writable,
)

REFERENCES = ("references/framework-matrix.md", "templates/profile-template.md",
              "references/scan-guide.md")
STACK_CONTRACT = "stacks/_CONTRACT.md"
DEFAULT_PROFILE_DIR = ".claude/profile"
# Sepuluh berkas profil. Berkas berdata nihil tetap ditulis berisi `tidak
# terdeteksi`; yang absen dibaca sebagai profil rusak, bukan sebagai profil
# tanpa data.
PROFILE_FILES = ("index.json", "stack.md", "structure.md", "surface-map.md",
                 "invariants.md", "commands.md", "layer-adoption.md", "visual.md",
                 "drift.md", "manual-notes.md")


class PreconditionChecker:
    def __init__(self, mode: Optional[str] = None, stack: Optional[str] = None,
                 profile_dir: Optional[str] = None, root: Optional[Path] = None):
        self.root = (root or self._find_repo_root()).resolve()
        self.mode_arg = (mode or "auto").lower()
        self.stack_arg = (stack or "auto").lower()
        self.profile_rel = profile_dir or DEFAULT_PROFILE_DIR
        self.profile_dir = self.root / self.profile_rel
        self.index_path = self.profile_dir / "index.json"
        self.skill_dir = Path(__file__).resolve().parents[1]
        self.stacks_dir = self.skill_dir / "stacks"
        self.results: List[Dict[str, Any]] = []
        self.stack: str = ""
        self.detected: str = ""
        self.mode: str = ""
        self.manifest: str = ""

    @staticmethod
    def _find_repo_root() -> Path:
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL, universal_newlines=True,
            ).strip()
            if out:
                return Path(out)
        except Exception:
            pass
        return Path.cwd()

    def _add(self, cid: int, name: str, status: str, summary: str, action: str = "") -> None:
        self.results.append({
            "id": cid, "name": name, "status": status,
            "summary": summary, "action": action,
        })

    def _rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    # ---------------------------------------------------------------- checks

    def run_all(self) -> bool:
        """Jalankan 5 check; hanya `FAIL` yang menahan, `WARN` tidak."""
        self._check_1_manifest()
        self._check_2_adapter()
        self._check_3_profile_writable()
        self._check_4_git_worktree()
        self._check_5_references()
        self._resolve_mode()
        return not any(r["status"] == "FAIL" for r in self.results)

    def _check_1_manifest(self) -> None:
        name = "Manifest frontend terdeteksi"
        manifests = candidate_manifests(self.root)
        if not manifests:
            self._add(1, name, "FAIL", "nol `package.json` di root maupun `apps/*`, `packages/*`",
                      "Target bukan proyek frontend Node.js. Hentikan; jangan buat profil palsu.")
            return

        hits = [(m, detect_stack(m)) for m in manifests]
        supported = [(m, s) for m, s in hits if s]
        if supported:
            manifest, stack = supported[0]
            self.manifest = self._rel(manifest)
            self.detected = stack
            extra = {s for _, s in supported if s != stack}
            if extra:
                self._add(1, name, "WARN",
                          f"{self._rel(manifest)} → `{stack}`, tetapi stack lain juga hadir: "
                          + ", ".join(sorted(extra)),
                          "Monorepo multi-stack. Setel parameter `stack` (dan `target_app`) "
                          "untuk memilih satu stack utama sebelum Phase 0 berjalan.")
                return
            self._add(1, name, "PASS", f"{self._rel(manifest)} → `{stack}`")
            return

        self.detected = ""
        nexts = [m for m in manifests if is_next(m)]
        if nexts:
            self._add(1, name, "FAIL",
                      f"{self._rel(nexts[0])} memuat `next` — Next.js di luar cakupan plugin",
                      "Hentikan rantai dan laporkan ke user; jangan buat profil untuk repo "
                      "yang tidak dilayani adapter mana pun.")
            return
        self._add(1, name, "FAIL",
                  f"{len(manifests)} manifest diperiksa, nol penanda "
                  + "/".join(KNOWN_STACKS),
                  "Sebutkan manifest yang diperiksa ke user dan hentikan; repo di luar "
                  "cakupan plugin.")

    def _check_2_adapter(self) -> None:
        name = "Adapter stack terbaca"
        override = ""
        if self.stack_arg != "auto":
            if self.stack_arg not in KNOWN_STACKS:
                self._add(2, name, "FAIL",
                          f"parameter `stack` = `{self.stack_arg}`, di luar {list(KNOWN_STACKS)}",
                          "Pakai salah satu nilai sah, atau biarkan `auto` untuk deteksi.")
                return
            self.stack = self.stack_arg
            if self.detected and self.detected != self.stack_arg:
                override = (f"parameter `stack` = `{self.stack_arg}` menimpa deteksi "
                            f"`{self.detected}`")
        elif self.detected:
            self.stack = self.detected
        else:
            self._add(2, name, "FAIL", "stack belum terselesaikan",
                      "Perbaiki Check 1 lebih dulu, atau setel parameter `stack` eksplisit.")
            return

        # Keberadaan adapter diuji apa pun asal `<stack-id>`-nya. Menyingkat jalur
        # override berarti stack yang dipaksa user tidak pernah dibuktikan punya
        # adapter, dan kegagalannya baru muncul di tengah Phase 0.
        path = self.stacks_dir / f"{self.stack}.md"
        if not path.is_file():
            self._add(2, name, "FAIL", f"adapter `{path.name}` tidak ditemukan",
                      f"Pulihkan berkas plugin di {self.stacks_dir}.")
            return
        if override:
            self._add(2, name, "WARN", f"{override}; adapter {path.name} tersedia",
                      "Catat penanda pendukung maupun yang bertentangan di laporan Phase 0.")
            return
        self._add(2, name, "PASS", f"adapter {path.name} tersedia")

    def _check_3_profile_writable(self) -> None:
        name = "Direktori profil dapat ditulis"
        if self.profile_dir.exists() and not self.profile_dir.is_dir():
            self._add(3, name, "FAIL", f"`{self.profile_rel}` ada tetapi bukan direktori",
                      "Bereskan path itu; profil hanya sah ditulis sebagai satu direktori.")
            return
        # Yang diprobe adalah direktori profil bila sudah ada, atau induk terdekat
        # bila belum. `probe_writable` mencari leluhur *yang sudah ada*, jadi
        # meneruskan path berkas di dalamnya akan mengembalikan berkas itu sendiri
        # lalu memvonisnya "bukan direktori".
        ok, detail = probe_writable(self.profile_dir)
        if not ok:
            self._add(3, name, "FAIL", detail,
                      f"Periksa izin `{self.profile_rel}/` di root repo sebelum menulis profil.")
            return
        if self.profile_dir.is_dir():
            locked = [f for f in PROFILE_FILES
                      if (self.profile_dir / f).is_file()
                      and not os.access(self.profile_dir / f, os.W_OK)]
            if locked:
                self._add(3, name, "FAIL",
                          f"{len(locked)} berkas profil tidak dapat ditimpa: "
                          + ", ".join(locked[:4]),
                          "REFRESH menulis ulang profil secara penuh; berikan izin tulis "
                          "pada berkas itu atau hapus lebih dulu.")
                return
            present = sum(1 for f in PROFILE_FILES if (self.profile_dir / f).is_file())
            self._add(3, name, "PASS", f"{present}/10 berkas profil ada, seluruhnya dapat ditimpa")
            return
        self._add(3, name, "PASS", f"induk terdekat `{detail}` dapat ditulis")

    def _check_4_git_worktree(self) -> None:
        name = "Worktree git tersedia"
        try:
            proc = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--git-dir"],
                                  capture_output=True, text=True, timeout=10)
            ok = proc.returncode == 0
        except (OSError, subprocess.SubprocessError):
            ok = False
        if not ok:
            self._add(4, name, "WARN", "bukan repositori git",
                      "Profiling boleh lanjut; `Commit Convention` lahir "
                      "`UNINITIALIZED (default conventional commits)` dan baris `.gitignore` "
                      "tidak dapat dipasang. Beri tahu user.")
            return
        self._add(4, name, "PASS", "`git log` dan `git check-ignore` dapat dijalankan")

    def _check_5_references(self) -> None:
        name = "Berkas referensi skill lengkap"
        missing = [r for r in REFERENCES if not (self.skill_dir / r).is_file()]
        if not (self.stacks_dir / "_CONTRACT.md").is_file():
            missing.append(STACK_CONTRACT)
        if missing:
            self._add(5, name, "FAIL", "hilang: " + ", ".join(missing),
                      f"Pulihkan berkas plugin di {self.skill_dir}.")
            return
        self._add(5, name, "PASS", f"{len(REFERENCES) + 1} berkas referensi tersedia")

    # ------------------------------------------------------------------ mode

    def _resolve_mode(self) -> None:
        """Selesaikan GENERATE vs REFRESH; ketidakcocokan jadi WARN, bukan FAIL."""
        exists = self.index_path.is_file()
        actual = "REFRESH" if exists else "GENERATE"
        if self.mode_arg in ("generate", "refresh"):
            asked = self.mode_arg.upper()
            self.mode = asked
            if asked != actual:
                self._add(6, "Mode operasi selaras", "WARN",
                          f"diminta `{asked}`, keadaan disk `{actual}`",
                          "REFRESH tanpa profil lama berjalan sebagai GENERATE; GENERATE di "
                          "atas profil yang ada akan menimpanya. Konfirmasikan ke user.")
                return
        else:
            self.mode = actual
        self._add(6, "Mode operasi selaras", "PASS",
                  f"`{self.mode}` — index.json {'ada' if exists else 'belum ada'}")

    # ---------------------------------------------------------------- output

    def format_text(self) -> str:
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        warned = sum(1 for r in self.results if r["status"] == "WARN")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        total = len(self.results)
        label = "FAIL" if failed else ("PASS (WARN)" if warned else "PASS")
        lines = [f"PRECONDITION CHECK: profile [{label}] ({passed}/{total} passed"
                 + (f", {warned} warn)" if warned else ")")]
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<32} : {r['status']} ({r['summary']})")
            if r["status"] in ("FAIL", "WARN") and r["action"]:
                lines.append(f"    * Tindakan: {r['action']}")
        lines.append(f"Terselesaikan: stack `{self.stack or 'tidak terdeteksi'}` "
                     f"· mode `{self.mode or 'tidak terselesaikan'}`")
        return "\n".join(lines)

    def to_json(self) -> str:
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = any(r["status"] == "FAIL" for r in self.results)
        return json.dumps({
            "status": "FAIL" if failed else "PASS",
            "passed_count": passed,
            "total_count": len(self.results),
            "root": str(self.root),
            "profile_dir": self.profile_rel,
            "manifest": self.manifest,
            "stack": self.stack,
            "mode": self.mode,
            "checks": self.results,
        }, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile Preconditions Checker")
    parser.add_argument("--mode", default=None, help="auto | generate | refresh")
    parser.add_argument("--stack", default=None,
                        help="paksa <stack-id>; default auto (deteksi dari manifest)")
    parser.add_argument("--profile-dir", default=None, dest="profile_dir",
                        help=f"direktori profil, default {DEFAULT_PROFILE_DIR}")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()

    checker = PreconditionChecker(
        mode=args.mode, stack=args.stack, profile_dir=args.profile_dir,
        root=Path(args.root) if args.root else None,
    )
    ok = checker.run_all()
    print(checker.to_json() if args.json else checker.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
