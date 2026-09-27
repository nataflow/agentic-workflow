#!/usr/bin/env python3
"""System-Analysis Precondition Validator.

Automates verification of repository preconditions before system-analysis execution.
Runs checks 1 through 8 in a single pass and produces a compact, actionable report.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` (parser frontmatter, taskdir, chain, profil,
berkas plugin, keluaran), di-bootstrap relatif terhadap berkas ini.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional


# Helper izin tulis dipakai bersama lintas skrip prasyarat; rumah kanoniknya
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd — skrip dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    TASKDIR_ACTION,
    check_taskdir,
    declared_chain,
    doc_status,
    find_agent,
    find_repo_root,
    format_text,
    freshness_banner,
    legacy_suffix,
    load_profile_index,
    parse_chain,
    plugin_file,
    probe_writable as _probe_writable,
    profile_staleness as _profile_staleness,
    to_json,
)
from precondition_lib import cli  # noqa: E402


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        risk_level: Optional[str] = None,
        chain: Optional[str] = None,
        target_root: Optional[Path] = None
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.risk_level_arg = (risk_level or "").strip().upper()
        self.chain_arg, self.chain_err = parse_chain(chain)
        self.td = check_taskdir(self.root, taskdir)
        self.results: List[Dict[str, Any]] = []

    def _effective_chain(self) -> Optional[str]:
        """Chain dari parameter, atau frontmatter `chain:` TASK.md sebagai fallback.

        Kebutuhan BRD dibaca dari ledger rantai, bukan dari risk_level maupun
        keberadaan berkas (analyst/references/chain-rules.md bagian 1.3).
        """
        if self.chain_arg:
            return self.chain_arg
        return declared_chain(self.td.path)[0] if self.td.ok else None

    def _chain_error(self) -> str:
        """Galat chain dari parameter, lalu dari frontmatter TASK.md."""
        if self.chain_err or self.chain_arg:
            return self.chain_err
        return declared_chain(self.td.path)[1] if self.td.ok else ""

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
                "Minta `backend:analyst` meneruskan risk_level (BREAKING | MAJOR) dari akar; dilarang menebak sendiri.",
            )
            return

        if not self.td.ok:
            fail(self.td.summary, TASKDIR_ACTION)
            return

        chain_err = self._chain_error()
        if chain_err:
            fail(chain_err,
                 "Sertakan --chain <BRD_PRD_BRIEF | PRD_BRIEF> dari `backend:analyst`, atau perbaiki frontmatter "
                 "chain: TASK.md lewat `backend:analyst`; nilai asing berarti salah rute.")
            return

        chain = self._effective_chain()
        if chain not in ("BRD_PRD_BRIEF", "PRD_BRIEF"):
            fail(
                f"Chain '{chain or 'tidak terbaca'}' bukan chain ber-PRD",
                "Sertakan --chain <BRD_PRD_BRIEF | PRD_BRIEF> dari `backend:analyst`, atau pastikan TASK.md memuat frontmatter chain:. Kebutuhan BRD dibaca dari ledger rantai, bukan dari risk_level maupun keberadaan berkas.",
            )
            return

        brd_file = self.td.path / "BRD.md"
        brd_exists = brd_file.exists()

        if chain == "PRD_BRIEF":
            if brd_exists:
                fail(
                    "Chain PRD_BRIEF tetapi taskdir memuat BRD.md",
                    "Artefak di luar chain berarti salah rute; laporkan ke `backend:analyst`. Dilarang menghapus artefak atau memakainya sebagai acuan.",
                )
                return
            ok("Chain PRD_BRIEF tanpa BRD.md (sah pada risk level mana pun; source_brd bertanda tidak ada)")
            return

        # chain == BRD_PRD_BRIEF
        if not brd_exists:
            fail(
                "Chain BRD_PRD_BRIEF tetapi BRD.md tidak ada — rantai putus",
                "Kembalikan rute ke `backend:analyst` untuk menyelesaikan hop BRD sebelum hop PRD berangkat.",
            )
            return

        # Status hanya dari frontmatter blok `---` pertama: kalimat aturan bisnis
        # seperti "Order dengan status: DRAFT ditolak" di badan tidak ikut dibaca.
        status, why = doc_status(brd_file, ("DRAFT", "APPROVED"))
        if status is None:
            fail(
                f"Status BRD.md tidak terbaca dari frontmatter ({why})",
                "Frontmatter BRD.md wajib memuat `status: DRAFT` atau `status: APPROVED` di blok `---` pertama; kembalikan ke `backend:analyst` bila rusak.",
            )
            return
        if status == "DRAFT":
            fail(
                "BRD.md masih berstatus DRAFT",
                "Kembalikan ke `backend:analyst`: hanya skill itu yang menulis status APPROVED, di gerbang dokumen Fase 4-nya sesudah persetujuan user.",
            )
            return

        ok("Chain BRD_PRD_BRIEF terikat BRD.md berstatus APPROVED")

    def _check_2_profile(self):
        check_id = 2
        name = "Profile Index & Architecture"
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

    def _check_3_taskdir(self):
        check_id = 3
        name = "Taskdir Allocation & Format"

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS" if self.td.ok else "FAIL",
            "summary": self.td.summary,
            "action": "" if self.td.ok else TASKDIR_ACTION,
        })

    def _check_4_read_write_access(self):
        check_id = 4
        name = "Workspace Read & Taskdir Write"
        # Check source_root read access
        source_root_path = self.root
        data = load_profile_index(self.root, required=("source_root",)).data
        if data:
            candidate = self.root / data["source_root"]
            if candidate.is_dir():
                source_root_path = candidate

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
        taskdir_path = self.td.path if self.td.ok else self.root / "backenddev" / "docs"

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
        template_found = plugin_file("skills", "system-analysis", "templates", "prd-template.md")
        checklist_found = plugin_file("skills", "system-analysis", "references", "analysis-protocol.md")

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

        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/reviewer.md tidak ditemukan di skill system-analysis",
                "action": "Pastikan template dispatcher/reviewer.md tersedia untuk dispatch prd-reviewer."
            })
            return

        if not find_agent("prd-reviewer"):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/prd-reviewer.md tidak ditemukan",
                "action": "Pastikan berkas agents/prd-reviewer.md tersedia di plugin backend."
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

        `system-analysis` mendispatch `code-explorer` langsung, tanpa skill pembungkus,
        lewat dua template: `dispatcher/explorer-surface.md` (Profil S, empat permukaan
        wajib Fase 1) dan `dispatcher/explorer-blast.md` (Profil B, lima dimensi rawan
        bocor sebelum Fase 4). Tanpa keduanya, predikat dispatch bagian A protokol tidak
        punya jalur sah.
        """
        check_id = 8
        name = "Explorer Dispatcher & Agent"
        skill_dir = Path(__file__).resolve().parent.parent
        templates = (("explorer-surface.md", "## Profil S"), ("explorer-blast.md", "## Profil B"))

        missing = [f"dispatcher/{f}" for f, _ in templates if not (skill_dir / "dispatcher" / f).exists()]
        if missing:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Template dispatch tidak ditemukan di skill system-analysis: {', '.join(missing)}",
                "action": "Pastikan kedua template dispatcher explorer tersedia untuk dispatch langsung code-explorer."
            })
            return

        if not find_agent("code-explorer"):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/code-explorer.md tidak ditemukan",
                "action": "Pastikan berkas agents/code-explorer.md tersedia di plugin backend."
            })
            return

        missing_profiles = []
        for fname, heading in templates:
            try:
                body = (skill_dir / "dispatcher" / fname).read_text(encoding="utf-8")
            except Exception as e:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"dispatcher/{fname} tidak terbaca: {e}",
                    "action": "Periksa izin baca berkas template dispatcher."
                })
                return
            if heading not in body:
                missing_profiles.append(f"{heading[3:]} ({fname})")
        if missing_profiles:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Profil dispatch hilang: {', '.join(missing_profiles)}",
                "action": "Pulihkan kedua profil; Profil S menutup permukaan Fase 1, Profil B menutup blast-sweep pra-Fase 4."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Template explorer-surface.md (Profil S), explorer-blast.md (Profil B), dan agent code-explorer.md terverifikasi",
            "action": ""
        })

    def format_text(self) -> str:
        return format_text("system-analysis", self.results,
                           banner=freshness_banner(getattr(self, "profile_freshness", None)))

    def to_json(self) -> str:
        return to_json(self.root, self.results, taskdir=self.taskdir_arg,
                       risk_level=self.risk_level_arg, chain=self._effective_chain() or "",
                       profile_freshness=getattr(self, "profile_freshness", ("TAK_TERNILAI", "belum dinilai"))[0])


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
    sys.exit(cli(main))
