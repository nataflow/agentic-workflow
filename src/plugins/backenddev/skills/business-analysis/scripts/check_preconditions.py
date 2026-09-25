#!/usr/bin/env python3
"""Business-Analysis Precondition Validator.

Automates verification of repository preconditions before business-analysis execution.
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
    find_agent,
    find_repo_root,
    format_text,
    freshness_banner,
    legacy_suffix,
    load_profile_index,
    parse_chain,
    probe_writable as _probe_writable,
    profile_staleness as _profile_staleness,
    to_json,
)


# Chain yang sah dijadwalkan menerbitkan BRD.md (chain-rules.md bagian 1.3).
# `business-analysis` hanya berangkat pada chain ber-BRD; nilai lain berarti salah rute.
BRD_CHAINS = {"BRD_PRD_BRIEF"}


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        chain: Optional[str] = None,
        target_root: Optional[Path] = None,
    ):
        self.root = (target_root or find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.chain_arg, self.chain_err = parse_chain(chain)
        self.td = check_taskdir(self.root, taskdir)
        self.results: List[Dict[str, Any]] = []

    def _task_chain(self):
        """(chain, galat) dari frontmatter TASK.md bila berkasnya sudah ada."""
        return declared_chain(self.td.path) if self.td.ok else (None, "")

    def _effective_chain(self) -> Optional[str]:
        """Parameter menang atas frontmatter; keduanya kosong berarti rantai tak terbaca."""
        return self.chain_arg or self._task_chain()[0]

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

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS" if self.td.ok else "FAIL",
            "summary": self.td.summary,
            "action": "" if self.td.ok else TASKDIR_ACTION,
        })

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

    def _check_3_read_write_access(self):
        check_id = 3
        name = "Workspace Read & Write Access"
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

        # Check taskdir / docs write access
        target_write_dir = self.td.path if self.td.ok else self.root / "backenddev" / "docs"

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
        

        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/reviewer.md tidak ditemukan di skill business-analysis",
                "action": "Pastikan template dispatcher/reviewer.md tersedia untuk dispatch brd-reviewer."
            })
            return

        if not find_agent("brd-reviewer"):
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

        declared, declared_err = self._task_chain()
        chain_err = self.chain_err or (declared_err if not self.chain_arg else "")
        if chain_err:
            fail(chain_err, 'Gunakan enum kanonik `analyst/references/chain-rules.md` bagian 1.3 (huruf besar-kecil dan kutip dinormalkan; tanda hubung tidak). Nilai asing di TASK.md berarti salah rute: laporkan ke `backenddev:analyst`.')
            return

        effective = self.chain_arg or declared

        if not effective:
            fail(
                "Chain tidak terbaca dari parameter maupun frontmatter chain: TASK.md",
                "Minta `backenddev:analyst` meneruskan parameter `chain`; dilarang menyimpulkannya dari artefak di disk.",
            )
            return

        if effective not in BRD_CHAINS:
            fail(
                f"Chain {effective} tidak menjadwalkan BRD.md; skill ini salah rute",
                "Kembalikan ke `backenddev:analyst`: hop BRD tidak ada di ledger `## Chain` chain ini.",
            )
            return

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


        if not dispatcher_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/explorer.md tidak ditemukan di skill business-analysis",
                "action": "Pastikan template dispatcher/explorer.md tersedia untuk dispatch langsung code-explorer."
            })
            return

        if not find_agent("code-explorer"):
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
        return format_text("business-analysis", self.results,
                           banner=freshness_banner(getattr(self, "profile_freshness", None)))

    def to_json(self) -> str:
        return to_json(self.root, self.results, taskdir=self.taskdir_arg, chain=self._effective_chain(),
                       profile_freshness=getattr(self, "profile_freshness", ("TAK_TERNILAI", "belum dinilai"))[0])


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
