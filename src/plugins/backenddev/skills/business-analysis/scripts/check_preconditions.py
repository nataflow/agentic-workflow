#!/usr/bin/env python3
"""Business-Analysis Precondition Validator.

Automates verification of repository preconditions before business-analysis execution.
Runs checks 1 through 8 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` untuk uji izin tulis, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional


# Helper izin tulis dipakai bersama lintas skrip prasyarat; rumah kanoniknya
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd — skrip dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    resolve_profile_dir,
    foreign_owner,
    legacy_suffix,
    nearest_existing_ancestor as _nearest_existing_ancestor,
    probe_writable as _probe_writable,
    profile_staleness as _profile_staleness,
)


# Chain yang sah dijadwalkan menerbitkan BRD.md (chain-rules.md bagian 1.3).
# `business-analysis` hanya berangkat pada chain ber-BRD; nilai lain berarti salah rute.
VALID_CHAINS = {"BRD_PRD_BRIEF", "PRD_BRIEF", "BRIEF"}
BRD_CHAINS = {"BRD_PRD_BRIEF"}


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        chain: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.chain_arg = (chain or "").strip().upper() or None
        self.results: List[Dict[str, Any]] = []

    def _resolve_taskdir(self) -> Optional[Path]:
        if not self.taskdir_arg:
            return None
        td = Path(self.taskdir_arg)
        return td if td.is_absolute() else self.root / td

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

    def _effective_chain(self) -> Optional[str]:
        """Parameter menang atas frontmatter; keduanya kosong berarti rantai tak terbaca."""
        if self.chain_arg:
            return self.chain_arg
        return self._declared_chain()

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
        """Run checks 1 through 8."""
        self._check_1_taskdir()
        self._check_2_profile()
        self._check_3_read_write_access()
        self._check_4_domain_and_brd_reference()
        self._check_5_git_worktree()
        self._check_6_dispatch_agent()
        self._check_7_chain()
        self._check_8_explorer_dispatcher()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_taskdir(self):
        check_id = 1
        name = "Taskdir Allocation & Format"
        
        if not self.taskdir_arg:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Parameter taskdir belum diberikan",
                "action": "Minta direktori kerja sah dari gerbang `backenddev:tech-lead` (format: backenddev/docs/<YYMMDDhhmm>-<slug>/)."
            })
            return

        taskdir_path = Path(self.taskdir_arg)
        if not taskdir_path.is_absolute():
            taskdir_path = self.root / taskdir_path

        # Canonical format pattern: backenddev/docs/<digits>-<slug>
        rel_path = str(taskdir_path.relative_to(self.root) if taskdir_path.is_relative_to(self.root) else taskdir_path)
        pattern = r"backenddev/docs/\d{10}-[a-z0-9-]+/?"
        
        is_canonical = bool(re.search(pattern, rel_path))
        if not is_canonical and not taskdir_path.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Format taskdir '{rel_path}' tidak mengikuti format kanonik backenddev/docs/<YYMMDDhhmm>-<slug>/",
                "action": "Pastikan taskdir dialokasikan oleh gerbang `backenddev:tech-lead` sesuai standar kanonik."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Taskdir terverifikasi: {rel_path}",
            "action": ""
        })

    def _check_2_profile(self):
        check_id = 2
        name = "Profile Index & Architecture"
        profile_dir, legacy_note = resolve_profile_dir(self.root)
        index_file = profile_dir / "index.json"

        if not index_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas .claude/profile/backenddev/index.json tidak ditemukan",
                "action": "Jalankan skill `backenddev:profile` untuk membuat profil repositori."
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
            required_keys = ["root_namespace", "source_root", "stack", "architecture"]
            missing_keys = [k for k in required_keys if not data.get(k)]
            if missing_keys:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Field kritis hilang di index.json: {', '.join(missing_keys)}",
                    "action": "Jalankan `backenddev:profile` untuk melengkapi field profil."
                })
                return
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Format JSON corrupt pada index.json: {e}",
                "action": "Perbaiki format JSON atau inisialisasi ulang via `backenddev:profile`."
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
            "summary": f"Profil valid (stack: {data.get('stack', 'unknown')}, arch: {data.get('architecture', 'unknown')}){freshness_suffix}" + legacy_suffix(legacy_note),
            "action": ""
        })

    def _check_3_read_write_access(self):
        check_id = 3
        name = "Workspace Read & Write Access"
        profile_dir = resolve_profile_dir(self.root)[0]
        index_file = profile_dir / "index.json"

        # Check source_root read access
        source_root_path = self.root
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sr = data.get("source_root")
                if sr:
                    candidate = self.root / sr
                    if candidate.exists() and candidate.is_dir():
                        source_root_path = candidate
            except Exception:
                pass

        if not os.access(source_root_path, os.R_OK):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori sumber tidak dapat dibaca: {source_root_path}",
                "action": "Periksa izin baca pada direktori sumber repositori."
            })
            return

        # Check taskdir / docs write access
        target_write_dir = self.root / "backenddev" / "docs"
        if self.taskdir_arg:
            td = Path(self.taskdir_arg)
            target_write_dir = td if td.is_absolute() else self.root / td

        # Skill ini dilarang membuat direktori spekulatif (SKILL.md Fase 0 butir 2),
        # jadi izin tulis diuji pada induk terdekat yang sudah ada.
        ok, detail = _probe_writable(target_write_dir)
        if not ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori kerja tidak dapat ditulis: {target_write_dir} ({detail})",
                "action": "Periksa hak akses tulis pada taskdir."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Izin baca sumber dan tulis taskdir terverifikasi",
            "action": ""
        })

    def _check_4_domain_and_brd_reference(self):
        check_id = 4
        name = "Historical BRD & Reference Access"
        docs_dir = self.root / "backenddev" / "docs"

        # Direktori boleh belum ada — check ini hanya memastikan ia terbaca bila ada,
        # bukan membuatnya. Nol artefak historis bukan kegagalan prasyarat.
        if docs_dir.exists() and not os.access(docs_dir, os.R_OK):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori {docs_dir} tidak memiliki izin baca",
                "action": "Periksa hak akses direktori backenddev/docs/."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Direktori backenddev/docs/ siap dibaca untuk referensi domain",
            "action": ""
        })

    def _check_5_git_worktree(self):
        check_id = 5
        name = "Git Worktree & Commit Status"
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

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Repositori git valid untuk commit draft BRD",
                "action": ""
            })
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca status repositori git: {e}",
                "action": "Pastikan git terpasang dan repositori memiliki .git sah."
            })

    def _check_6_dispatch_agent(self):
        check_id = 6
        name = "BRD Reviewer Dispatcher & Agent"
        skill_dir = Path(__file__).resolve().parent.parent
        dispatcher_file = skill_dir / "dispatcher" / "reviewer.md"
        
        candidate_agents = [
            skill_dir.parent.parent / "agents" / "brd-reviewer.md",
            self.root / "src" / "plugins" / "backenddev" / "agents" / "brd-reviewer.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "agents" / "brd-reviewer.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "agents" / "brd-reviewer.md",
        ]

        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/reviewer.md tidak ditemukan di skill business-analysis",
                "action": "Pastikan template dispatcher/reviewer.md tersedia untuk dispatch brd-reviewer."
            })
            return

        if not any(p.exists() for p in candidate_agents):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/brd-reviewer.md tidak ditemukan",
                "action": "Pastikan berkas agents/brd-reviewer.md tersedia di plugin backenddev."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Template dispatcher/reviewer.md dan agent brd-reviewer.md terverifikasi",
            "action": ""
        })

    def _check_7_chain(self):
        """Chain wajib terbaca dan wajib menjadwalkan BRD.

        Tanpa nilai ini slot `Chain` dispatcher/reviewer.md tidak dapat dihidrasi, dan
        `brd-reviewer` kehilangan satu-satunya cara membedakan dokumen hulu yang sah
        tidak ada dari rantai yang putus.
        """
        check_id = 7
        name = "Chain Enum & BRD Scheduling"

        def fail(summary: str, action: str):
            self.results.append({
                "id": check_id, "name": name, "status": "FAIL",
                "summary": summary, "action": action,
            })

        effective = self._effective_chain()

        if not effective:
            fail(
                "Chain tidak terbaca dari parameter maupun frontmatter chain: TASK.md",
                "Minta `backenddev:analyst` meneruskan parameter `chain`; dilarang menyimpulkannya dari artefak di disk.",
            )
            return

        if effective not in VALID_CHAINS:
            fail(
                f"Chain '{effective}' tidak sah (wajib BRD_PRD_BRIEF | PRD_BRIEF | BRIEF)",
                "Gunakan enum kanonik `analyst/references/chain-rules.md` bagian 1.3.",
            )
            return

        if effective not in BRD_CHAINS:
            fail(
                f"Chain {effective} tidak menjadwalkan BRD.md; skill ini salah rute",
                "Kembalikan ke `backenddev:analyst`: hop BRD tidak ada di ledger `## Chain` chain ini.",
            )
            return

        declared = self._declared_chain()
        if self.chain_arg and declared and declared != self.chain_arg:
            fail(
                f"TASK.md memateraikan chain {declared}, berbeda dari parameter {self.chain_arg}",
                "Perubahan chain hanya sah lewat eskalasi Fase 5 `analyst`; laporkan penyimpangan ini ke skill itu.",
            )
            return

        source = "parameter" if self.chain_arg else "frontmatter TASK.md"
        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Chain {effective} terbaca dari {source}; hop BRD terjadwal",
            "action": "",
        })

    def _check_8_explorer_dispatcher(self):
        """Dispatcher explorer wajib ada sebelum Fase 1 boleh mendelegasikan.

        `business-analysis` mendispatch `code-explorer` langsung lewat
        `dispatcher/explorer.md`, tanpa skill pembungkus.
        Template itu satu-satunya jalur sah keluar dari kuota sapuan main loop
        Fase 1; ketiadaannya memaksa skill menyapu kode melewati kuotanya sendiri.
        """
        check_id = 8
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
                "summary": "Berkas dispatcher/explorer.md tidak ditemukan di skill business-analysis",
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

        lines = [
            f"PRECONDITION CHECK: business-analysis [{status_label}] ({passed_count}/{total} passed)",
        ]
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<32} : {r['status']} ({r['summary']})")
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
            "taskdir": self.taskdir_arg,
            "chain": self._effective_chain(),
            "profile_freshness": getattr(self, "profile_freshness", ("TAK_TERNILAI", "belum dinilai"))[0],
            "checks": self.results
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Business-Analysis Preconditions Checker")
    parser.add_argument("--taskdir", type=str, default=None, help="Task directory path")
    parser.add_argument("--chain", type=str, default=None, help="Chain enum (BRD_PRD_BRIEF | PRD_BRIEF | BRIEF); fallback: frontmatter chain: TASK.md")
    parser.add_argument("--root", type=str, default=None, help="Root path of target repository")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(taskdir=args.taskdir, chain=args.chain, target_root=target_root)
    passed = checker.run_all()

    if args.json:
        print(checker.to_json())
    else:
        print(checker.format_text())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
