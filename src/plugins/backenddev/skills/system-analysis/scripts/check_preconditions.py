#!/usr/bin/env python3
"""System-Analysis Precondition Validator.

Automates verification of repository preconditions before system-analysis execution.
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
    nearest_existing_ancestor as _nearest_existing_ancestor,
    probe_writable as _probe_writable,
    profile_staleness as _profile_staleness,
)


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        risk_level: Optional[str] = None,
        chain: Optional[str] = None,
        target_root: Optional[Path] = None
    ):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.risk_level_arg = (risk_level or "").strip().upper()
        self.chain_arg = (chain or "").strip().upper()
        self.results: List[Dict[str, Any]] = []

    def _effective_chain(self) -> str:
        """Chain dari parameter, atau frontmatter `chain:` TASK.md sebagai fallback.

        Kebutuhan BRD dibaca dari ledger rantai, bukan dari risk_level maupun
        keberadaan berkas (analyst/references/chain-rules.md bagian 1.3).
        """
        if self.chain_arg:
            return self.chain_arg
        taskdir_path = self._resolve_taskdir()
        if not taskdir_path:
            return ""
        task_file = taskdir_path / "TASK.md"
        if not task_file.exists():
            return ""
        try:
            content = task_file.read_text(encoding="utf-8")
        except Exception:
            return ""
        match = re.search(r"^chain:\s*([A-Z_]+)\s*$", content, re.MULTILINE)
        return match.group(1).upper() if match else ""

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
        self._check_1_brd_and_risk_level()
        self._check_2_profile()
        self._check_3_taskdir()
        self._check_4_read_write_access()
        self._check_5_templates_and_checklist()
        self._check_6_git_worktree()
        self._check_7_reviewer_dispatcher()
        self._check_8_explorer_dispatcher()
        return all(r["status"] == "PASS" for r in self.results)

    def _resolve_taskdir(self) -> Optional[Path]:
        if not self.taskdir_arg:
            return None
        td = Path(self.taskdir_arg)
        return td if td.is_absolute() else self.root / td

    def _check_1_brd_and_risk_level(self):
        check_id = 1
        name = "BRD & Chain Alignment"

        def fail(summary: str, action: str):
            self.results.append({
                "id": check_id, "name": name, "status": "FAIL",
                "summary": summary, "action": action,
            })

        def ok(summary: str):
            self.results.append({
                "id": check_id, "name": name, "status": "PASS",
                "summary": summary, "action": "",
            })

        if not self.risk_level_arg or self.risk_level_arg not in ("BREAKING", "MAJOR"):
            fail(
                f"Risk level '{self.risk_level_arg}' tidak sah (wajib BREAKING atau MAJOR)",
                "Minta `backenddev:analyst` meneruskan risk_level (BREAKING | MAJOR) dari akar; dilarang menebak sendiri.",
            )
            return

        taskdir_path = self._resolve_taskdir()
        if not taskdir_path:
            fail(
                "Parameter taskdir belum diberikan",
                "Sertakan --taskdir <path> dari `backenddev:analyst`.",
            )
            return

        chain = self._effective_chain()
        if chain not in ("BRD_PRD_BRIEF", "PRD_BRIEF"):
            fail(
                f"Chain '{chain or 'tidak terbaca'}' bukan chain ber-PRD",
                "Sertakan --chain <BRD_PRD_BRIEF | PRD_BRIEF> dari `backenddev:analyst`, atau pastikan TASK.md memuat frontmatter chain:. Kebutuhan BRD dibaca dari ledger rantai, bukan dari risk_level maupun keberadaan berkas.",
            )
            return

        brd_file = taskdir_path / "BRD.md"
        brd_exists = brd_file.exists()

        if chain == "PRD_BRIEF":
            if brd_exists:
                fail(
                    "Chain PRD_BRIEF tetapi taskdir memuat BRD.md",
                    "Artefak di luar chain berarti salah rute; laporkan ke `backenddev:analyst`. Dilarang menghapus artefak atau memakainya sebagai acuan.",
                )
                return
            ok("Chain PRD_BRIEF tanpa BRD.md (sah pada risk level mana pun; source_brd bertanda tidak ada)")
            return

        # chain == BRD_PRD_BRIEF
        if not brd_exists:
            fail(
                "Chain BRD_PRD_BRIEF tetapi BRD.md tidak ada — rantai putus",
                "Kembalikan rute ke `backenddev:analyst` untuk menyelesaikan hop BRD sebelum hop PRD berangkat.",
            )
            return

        try:
            content = brd_file.read_text(encoding="utf-8")
        except Exception as e:
            fail(f"Gagal membaca {brd_file}: {e}", "Periksa izin baca dan integritas berkas BRD.md.")
            return

        status_match = re.search(r"status:\s*([A-Z_]+)", content, re.IGNORECASE)
        status_val = status_match.group(1).upper() if status_match else ""

        if "DRAFT" in status_val or "status: draft" in content.lower():
            fail(
                "BRD.md masih berstatus DRAFT",
                "Kembalikan ke `backenddev:analyst`: hanya skill itu yang menulis status APPROVED, di gerbang dokumen Fase 4-nya sesudah persetujuan user.",
            )
            return

        if "APPROVED" not in status_val and "status: approved" not in content.lower():
            fail(
                "Status BRD.md tidak terdefinisi APPROVED",
                "Pastikan `backenddev:analyst` telah menulis status: APPROVED di frontmatter BRD.md.",
            )
            return

        ok("Chain BRD_PRD_BRIEF terikat BRD.md berstatus APPROVED")

    def _check_2_profile(self):
        check_id = 2
        name = "Profile Index & Architecture"
        profile_dir = self.root / ".claude" / "profile"
        index_file = profile_dir / "index.json"

        if not index_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas .claude/profile/index.json tidak ditemukan",
                "action": "Jalankan skill `backenddev:profile` untuk membuat profil repositori."
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
            "summary": f"Profil valid (stack: {data.get('stack', 'unknown')}, arch: {data.get('architecture', 'unknown')}){freshness_suffix}",
            "action": ""
        })

    def _check_3_taskdir(self):
        check_id = 3
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

        taskdir_path = self._resolve_taskdir()
        if not taskdir_path:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Gagal meresolusi path taskdir",
                "action": "Pastikan path taskdir valid."
            })
            return

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

    def _check_4_read_write_access(self):
        check_id = 4
        name = "Workspace Read & Taskdir Write"
        profile_dir = self.root / ".claude" / "profile"
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

        # Check taskdir write access
        taskdir_path = self._resolve_taskdir()
        if not taskdir_path:
            taskdir_path = self.root / "backenddev" / "docs"

        # Taskdir diprovisi gerbang, bukan skrip check: izin tulis diuji pada induk
        # terdekat yang sudah ada tanpa membuat direktori apa pun.
        ok, detail = _probe_writable(taskdir_path)
        if not ok:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Direktori taskdir tidak dapat ditulis: {taskdir_path} ({detail})",
                "action": "Periksa hak akses tulis pada taskdir untuk menerbitkan PRD.md."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Akses baca source_root dan tulis taskdir terverifikasi",
            "action": ""
        })

    def _check_5_templates_and_checklist(self):
        check_id = 5
        name = "Canonical Templates & Checklist"
        skill_dir = Path(__file__).resolve().parent.parent

        template_candidates = [
            skill_dir / "templates" / "prd-template.md",
            self.root / "src" / "plugins" / "backenddev" / "skills" / "system-analysis" / "templates" / "prd-template.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "system-analysis" / "templates" / "prd-template.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "system-analysis" / "templates" / "prd-template.md",
        ]

        checklist_candidates = [
            skill_dir / "references" / "analysis-protocol.md",
            self.root / "src" / "plugins" / "backenddev" / "skills" / "system-analysis" / "references" / "analysis-protocol.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "system-analysis" / "references" / "analysis-protocol.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "system-analysis" / "references" / "analysis-protocol.md",
        ]

        template_found = any(p.exists() for p in template_candidates)
        checklist_found = any(p.exists() for p in checklist_candidates)

        if not template_found or not checklist_found:
            missing = []
            if not template_found:
                missing.append("templates/prd-template.md")
            if not checklist_found:
                missing.append("references/analysis-protocol.md")
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Berkas referensi hilang: {', '.join(missing)}",
                "action": "Pastikan berkas template prd-template.md dan references/analysis-protocol.md terpasang di direktori skill."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "prd-template.md dan analysis-protocol.md tersedia",
            "action": ""
        })

    def _check_6_git_worktree(self):
        check_id = 6
        name = "Git Worktree Status"
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
                "summary": "Repositori git valid untuk commit draft PRD",
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

    def _check_7_reviewer_dispatcher(self):
        check_id = 7
        name = "PRD Reviewer Dispatcher & Agent"
        skill_dir = Path(__file__).resolve().parent.parent
        dispatcher_file = skill_dir / "dispatcher" / "reviewer.md"

        candidate_agents = [
            skill_dir.parent.parent / "agents" / "prd-reviewer.md",
            self.root / "src" / "plugins" / "backenddev" / "agents" / "prd-reviewer.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "agents" / "prd-reviewer.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "agents" / "prd-reviewer.md",
        ]

        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/reviewer.md tidak ditemukan di skill system-analysis",
                "action": "Pastikan template dispatcher/reviewer.md tersedia untuk dispatch prd-reviewer."
            })
            return

        if not any(p.exists() for p in candidate_agents):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/prd-reviewer.md tidak ditemukan",
                "action": "Pastikan berkas agents/prd-reviewer.md tersedia di plugin backenddev."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Template dispatcher/reviewer.md dan agent prd-reviewer.md terverifikasi",
            "action": ""
        })

    def _check_8_explorer_dispatcher(self):
        """Dispatcher explorer wajib ada sebelum Fase 1 boleh memetakan as-is.

        `system-analysis` mendispatch `code-explorer` langsung lewat
        `dispatcher/explorer.md`, tanpa skill pembungkus.
        Template itu memuat dua profil yang keduanya wajib: Profil S menutup empat
        permukaan wajib Fase 1, Profil B menutup lima dimensi rawan bocor sebelum
        Fase 4. Tanpanya, predikat dispatch bagian A protokol tidak punya jalur sah.
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
                "summary": "Berkas dispatcher/explorer.md tidak ditemukan di skill system-analysis",
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

        try:
            body = dispatcher_file.read_text(encoding="utf-8")
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"dispatcher/explorer.md tidak terbaca: {e}",
                "action": "Periksa izin baca berkas template dispatcher."
            })
            return

        missing_profiles = [p for p in ("Profil S", "Profil B") if p not in body]
        if missing_profiles:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Profil dispatch hilang di dispatcher/explorer.md: {', '.join(missing_profiles)}",
                "action": "Pulihkan kedua profil; Profil S menutup permukaan Fase 1, Profil B menutup blast-sweep pra-Fase 4."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Template dispatcher/explorer.md (Profil S + B) dan agent code-explorer.md terverifikasi",
            "action": ""
        })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: system-analysis [{status_label}] ({passed_count}/{total} passed)",
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
            "risk_level": self.risk_level_arg,
            "chain": self._effective_chain(),
            "profile_freshness": getattr(self, "profile_freshness", ("TAK_TERNILAI", "belum dinilai"))[0],
            "checks": self.results
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="System-Analysis Preconditions Validator")
    parser.add_argument("--taskdir", type=str, default=None, help="Task directory path")
    parser.add_argument("--risk-level", type=str, default=None, help="Risk level (BREAKING | MAJOR)")
    parser.add_argument("--chain", type=str, default=None, help="Chain enum (BRD_PRD_BRIEF | PRD_BRIEF); fallback: frontmatter chain: TASK.md")
    parser.add_argument("--root", type=str, default=None, help="Root path of target repository")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        taskdir=args.taskdir,
        risk_level=args.risk_level,
        chain=args.chain,
        target_root=target_root
    )
    passed = checker.run_all()

    if args.json:
        print(checker.to_json())
    else:
        print(checker.format_text())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
