#!/usr/bin/env python3
"""Plan Precondition Validator.

Automates verification of repository preconditions before plan execution.
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


VALID_CHAINS = {"BRD_PRD_BRIEF", "PRD_BRIEF", "BRIEF"}
VALID_RISKS = {"BREAKING", "MAJOR", "MINOR"}

# Tiga jalur masuk yang sah. Tidak ada nilai keempat: resolusi dari artefak di disk
# ("auto") dihapus karena ia menyimpulkan jalur dari apa yang kebetulan ada, sehingga
# chain ber-PRD yang PRD-nya gagal terbit turun senyap jadi LANGSUNG tanpa satu pun
# kegagalan tercatat. Pemanggil wajib meneruskan jalurnya eksplisit. "TEMUAN" dihapus
# karena perbaikan temuan tidak lagi punya jalur sendiri: ia berakar lewat lane planning
# seperti permintaan kerja lain, dan `finding_source` yang menandai asal-usulnya.
VALID_ENTRY_MODES = {"PRD", "RCA", "LANGSUNG"}

# entry_mode yang sah dipikul tiap chain (chain-rules.md bagian 2.1).
# Chain ber-PRD wajib masuk lewat jalur PRD; chain BRIEF lewat jalur LANGSUNG.
CHAIN_ENTRY_MODES = {
    "BRD_PRD_BRIEF": "PRD",
    "PRD_BRIEF": "PRD",
    "BRIEF": "LANGSUNG",
}


class PreconditionChecker:
    def __init__(
        self,
        taskdir: Optional[str] = None,
        entry_mode: Optional[str] = None,
        chain: Optional[str] = None,
        risk: Optional[str] = None,
        file_scope: Optional[str] = None,
        target_root: Optional[Path] = None
    ):
        self.root = (target_root or self._find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.entry_mode_arg = (entry_mode or "").strip().upper()
        # "—" dan "-" adalah penanda "tidak berlaku" pada jalur RCA, bukan nilai enum.
        _chain = (chain or "").strip().upper()
        _risk = (risk or "").strip().upper()
        self.chain_arg = None if _chain in ("", "—", "-") else _chain
        self.risk_arg = None if _risk in ("", "—", "-") else _risk
        self.file_scope_arg = (file_scope or "").strip() or None
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
        """Run checks 1 through 8."""
        self._check_1_taskdir()
        self._check_2_profile()
        self._check_3_upstream_artifact()
        self._check_4_read_write_access()
        self._check_5_templates_and_references()
        self._check_6_git_worktree()
        self._check_7_dispatchers()
        self._check_8_planning_parameters()
        return all(r["status"] == "PASS" for r in self.results)

    def _frontmatter(self, field: str) -> Optional[str]:
        """Baca satu field frontmatter TASK.md bila berkasnya sudah ada."""
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
        match = re.search(rf"^{field}:\s*([A-Za-z_-]+)\s*$", content, re.MULTILINE)
        return match.group(1).upper() if match else None

    def _effective_chain(self) -> Optional[str]:
        return self.chain_arg or self._frontmatter("chain")

    def _effective_risk(self) -> Optional[str]:
        return self.risk_arg or self._frontmatter("risk")

    def _resolve_taskdir(self) -> Optional[Path]:
        if not self.taskdir_arg:
            return None
        td = Path(self.taskdir_arg)
        return td if td.is_absolute() else self.root / td

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

    def _check_2_profile(self):
        check_id = 2
        name = "Profile Index & Documents"
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

        required_docs = ["commands.md", "code-conventions.md", "anti-patterns.md", "invariants.md"]
        missing_docs = [doc for doc in required_docs if not (profile_dir / doc).exists()]
        if missing_docs:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Dokumen profil belum lengkap: {', '.join(missing_docs)}",
                "action": "Lengkapi berkas profil di .claude/profile/ atau jalankan `backenddev:profile`."
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
            "summary": f"Profil valid (stack: {data.get('stack', 'unknown')}, arch: {data.get('architecture', 'unknown')}, 4 dokumen profil lengkap){freshness_suffix}",
            "action": ""
        })

    def _check_3_upstream_artifact(self):
        check_id = 3
        name = "Upstream Document Status"
        taskdir_path = self._resolve_taskdir()

        mode = self.entry_mode_arg
        prd_file = taskdir_path / "PRD.md" if taskdir_path else None
        rca_file = taskdir_path / "RCA.md" if taskdir_path else None
        review_file = taskdir_path / "REVIEW.md" if taskdir_path else None
        issues_dir = self.root / "backenddev" / "issues"

        # Jalur masuk tidak pernah disimpulkan dari artefak di disk. Kesimpulan itu membuat
        # chain ber-PRD yang PRD-nya gagal terbit terbaca sebagai LANGSUNG yang sah, dan
        # seluruh pemeriksaan ber-gate PRD ikut dilewati tanpa satu pun kegagalan tercatat.
        if not mode:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Parameter entry_mode kosong; jalur masuk tidak punya nilai bawaan",
                "action": "Minta pemanggil meneruskan `--entry-mode` eksplisit (PRD | RCA | LANGSUNG); dilarang menyimpulkannya dari artefak di taskdir."
            })
            return

        if mode not in VALID_ENTRY_MODES:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"entry_mode '{mode}' bukan jalur masuk yang sah",
                "action": "Gunakan salah satu dari PRD | RCA | LANGSUNG; nilai `auto` dan `TEMUAN` sudah dihapus dari kontrak skill ini."
            })
            return

        if mode == "PRD":
            if not prd_file or not prd_file.exists():
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "PRD.md tidak ditemukan di taskdir",
                    "action": "Pastikan PRD.md telah disusun oleh `backenddev:system-analysis`."
                })
                return

            try:
                content = prd_file.read_text(encoding="utf-8")
                status_match = re.search(r"status:\s*([A-Z_]+)", content, re.IGNORECASE)
                status_val = status_match.group(1).upper() if status_match else ""

                if "DRAFT" in status_val or "status: draft" in content.lower():
                    self.results.append({
                        "id": check_id,
                        "name": name,
                        "status": "FAIL",
                        "summary": "PRD.md masih berstatus DRAFT",
                        "action": "Kembalikan rute ke `backenddev:analyst`: hanya skill itu yang menulis status APPROVED, di gerbang dokumen Fase 4-nya sesudah persetujuan user."
                    })
                    return

                if "APPROVED" not in status_val and "status: approved" not in content.lower():
                    self.results.append({
                        "id": check_id,
                        "name": name,
                        "status": "FAIL",
                        "summary": "Status PRD.md tidak terdefinisi APPROVED",
                        "action": "Pastikan PRD.md memiliki status: APPROVED di frontmatter."
                    })
                    return

                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "PASS",
                    "summary": "Dokumen hulu PRD.md berstatus APPROVED terverifikasi",
                    "action": ""
                })
                return
            except Exception as e:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Gagal membaca PRD.md: {e}",
                    "action": "Periksa integritas berkas PRD.md."
                })
                return

        elif mode == "RCA":
            if not rca_file or not rca_file.exists():
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "RCA.md tidak ditemukan di taskdir",
                    "action": "Pastikan RCA.md telah disusun oleh `backenddev:debug`."
                })
                return

            try:
                content = rca_file.read_text(encoding="utf-8")
                status_match = re.search(r"status:\s*([A-Z_]+)", content, re.IGNORECASE)
                status_val = status_match.group(1).upper() if status_match else ""

                if "INCONCLUSIVE" in status_val or "status: inconclusive" in content.lower():
                    self.results.append({
                        "id": check_id,
                        "name": name,
                        "status": "FAIL",
                        "summary": "RCA.md berstatus INCONCLUSIVE",
                        "action": "Kembalikan rute ke `backenddev:debug` untuk memastikan akar masalah terbukti."
                    })
                    return

                if "ROOT_CAUSE_CONFIRMED" not in status_val and "status: root_cause_confirmed" not in content.lower():
                    self.results.append({
                        "id": check_id,
                        "name": name,
                        "status": "FAIL",
                        "summary": "Status RCA.md tidak terdefinisi ROOT_CAUSE_CONFIRMED",
                        "action": "Pastikan RCA.md memiliki status: ROOT_CAUSE_CONFIRMED di frontmatter."
                    })
                    return

                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "PASS",
                    "summary": "Dokumen hulu RCA.md berstatus ROOT_CAUSE_CONFIRMED terverifikasi",
                    "action": ""
                })
                return
            except Exception as e:
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Gagal membaca RCA.md: {e}",
                    "action": "Periksa integritas berkas RCA.md."
                })
                return

        else:  # LANGSUNG
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Jalur LANGSUNG terverifikasi untuk permintaan terisolasi",
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
                "action": "Periksa hak akses tulis pada taskdir untuk menerbitkan brief."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Akses baca source_root dan tulis taskdir terverifikasi",
            "action": ""
        })

    def _check_5_templates_and_references(self):
        check_id = 5
        name = "Templates & Reference Files"
        skill_dir = Path(__file__).resolve().parent.parent

        required_files = [
            ("templates/brief-template.md", [
                skill_dir / "templates" / "brief-template.md",
                self.root / "src" / "plugins" / "backenddev" / "skills" / "plan" / "templates" / "brief-template.md",
                Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "plan" / "templates" / "brief-template.md",
                Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "plan" / "templates" / "brief-template.md",
            ]),
            ("references/entry-rules.md", [
                skill_dir / "references" / "entry-rules.md",
                self.root / "src" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "entry-rules.md",
                Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "entry-rules.md",
                Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "entry-rules.md",
            ]),
            ("references/slicing-and-scan.md", [
                skill_dir / "references" / "slicing-and-scan.md",
                self.root / "src" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "slicing-and-scan.md",
                Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "slicing-and-scan.md",
                Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "slicing-and-scan.md",
            ]),
            ("references/review-and-commit.md", [
                skill_dir / "references" / "review-and-commit.md",
                self.root / "src" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "review-and-commit.md",
                Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "review-and-commit.md",
                Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "plan" / "references" / "review-and-commit.md",
            ]),
            # Kedua skrip di bawah menegakkan Fase 3 dan Fase 4. Ketiadaannya
            # diperiksa di sini supaya rantai berhenti sebelum brief ditulis,
            # bukan di tengah batch saat gerbang per-brief hendak dipanggil.
            ("scripts/scaffold_brief.py", [
                skill_dir / "scripts" / "scaffold_brief.py",
                self.root / "src" / "plugins" / "backenddev" / "skills" / "plan" / "scripts" / "scaffold_brief.py",
                Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "plan" / "scripts" / "scaffold_brief.py",
                Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "plan" / "scripts" / "scaffold_brief.py",
            ]),
            ("scripts/validate_briefs.py", [
                skill_dir / "scripts" / "validate_briefs.py",
                self.root / "src" / "plugins" / "backenddev" / "skills" / "plan" / "scripts" / "validate_briefs.py",
                Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "plan" / "scripts" / "validate_briefs.py",
                Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "plan" / "scripts" / "validate_briefs.py",
            ]),
        ]

        missing = []
        for rel_name, candidates in required_files:
            if not any(p.exists() for p in candidates):
                missing.append(rel_name)

        if missing:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Berkas template/referensi hilang: {', '.join(missing)}",
                "action": "Pastikan brief-template.md, referensi entry-rules.md, slicing-and-scan.md, review-and-commit.md, beserta skrip scaffold_brief.py dan validate_briefs.py terpasang di direktori skill plan."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "template, 3 referensi, dan 2 skrip penegak Fase 3-4 tersedia",
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
                "summary": "Repositori git valid untuk commit agregat brief",
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

    def _check_7_dispatchers(self):
        """Dua template dispatch plan beserta definisi agentnya.

        `plan` mendispatch `code-explorer` lewat `dispatcher/explorer.md` di Fase 2 dan
        `brief-reviewer` lewat `dispatcher/reviewer.md` di Fase 5, keduanya langsung
        tanpa skill pembungkus. Tanpa yang pertama fan-out 12 dimensi tidak punya jalur
        berangkat; tanpa yang kedua batch brief terkunci di git tanpa self-review.
        """
        check_id = 7
        name = "Explorer & Brief Reviewer Dispatcher"
        skill_dir = Path(__file__).resolve().parent.parent
        dispatcher_file = skill_dir / "dispatcher" / "reviewer.md"

        candidate_agents = [
            skill_dir.parent.parent / "agents" / "brief-reviewer.md",
            self.root / "src" / "plugins" / "backenddev" / "agents" / "brief-reviewer.md",
            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "agents" / "brief-reviewer.md",
            Path.home() / ".claude" / "plugins" / "backenddev" / "agents" / "brief-reviewer.md",
        ]

        explorer_dispatcher = skill_dir / "dispatcher" / "explorer.md"

        candidate_explorer_agents = [
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
                "summary": "Berkas dispatcher/reviewer.md tidak ditemukan di skill plan",
                "action": "Pastikan template dispatcher/reviewer.md tersedia untuk dispatch brief-reviewer."
            })
            return

        if not any(p.exists() for p in candidate_agents):
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Definisi subagent agents/brief-reviewer.md tidak ditemukan",
                "action": "Pastikan berkas agents/brief-reviewer.md tersedia di plugin backenddev."
            })
            return

        if not explorer_dispatcher.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas dispatcher/explorer.md tidak ditemukan di skill plan",
                "action": "Pastikan template dispatcher/explorer.md tersedia untuk dispatch langsung code-explorer."
            })
            return

        if not any(p.exists() for p in candidate_explorer_agents):
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
            "summary": "Template dispatcher/reviewer.md + explorer.md dan agent brief-reviewer.md + code-explorer.md terverifikasi",
            "action": ""
        })

    def _check_8_planning_parameters(self):
        """Parameter lane planning: chain, risk, file_scope, dan keselarasan entry_mode.

        Check E berdiri di atas `file_scope`, Check K di atas `risk`, dan hidrasi slot
        `Chain` dispatcher/reviewer.md di atas `chain`. Ketiganya diverifikasi di sini
        supaya parameter yang lupa diteruskan gagal keras, bukan melemahkan check
        hilir tanpa satu pun kegagalan tercatat.
        """
        check_id = 8
        name = "Planning Parameters & Entry Mode Alignment"

        def fail(summary: str, action: str):
            self.results.append({
                "id": check_id, "name": name, "status": "FAIL",
                "summary": summary, "action": action,
            })

        chain = self._effective_chain()

        # Jalur RCA dirutekan gerbang langsung, bukan lane planning:
        # ia tidak memikul chain dan tidak diperiksa di sini.
        if self.entry_mode_arg == "RCA" and not chain:
            self.results.append({
                "id": check_id, "name": name, "status": "PASS",
                "summary": f"Jalur {self.entry_mode_arg} dirutekan gerbang; parameter chain tidak berlaku",
                "action": "",
            })
            return

        if not chain:
            fail(
                "Chain tidak terbaca dari parameter maupun frontmatter chain: TASK.md",
                "Minta `backenddev:analyst` meneruskan parameter `chain`; tanpanya `brief-reviewer` tidak dapat membedakan dokumen hulu yang sah tidak ada dari rantai putus.",
            )
            return

        if chain not in VALID_CHAINS:
            fail(
                f"Chain '{chain}' tidak sah (wajib BRD_PRD_BRIEF | PRD_BRIEF | BRIEF)",
                "Gunakan enum kanonik `analyst/references/chain-rules.md` bagian 1.3.",
            )
            return

        if self.entry_mode_arg not in VALID_ENTRY_MODES:
            fail(
                f"entry_mode '{self.entry_mode_arg or '(kosong)'}' tidak sah pada lane planning (chain {chain})",
                f"Minta `backenddev:analyst` meneruskan entry_mode '{CHAIN_ENTRY_MODES[chain]}' eksplisit; jalur masuk tidak punya nilai bawaan dan dilarang disimpulkan dari artefak di taskdir.",
            )
            return

        expected = CHAIN_ENTRY_MODES[chain]
        if self.entry_mode_arg != expected:
            fail(
                f"entry_mode {self.entry_mode_arg} tidak selaras chain {chain} (yang sah: {expected})",
                "Selaraskan lewat `backenddev:analyst`; dilarang menurunkan jalur masuk sendiri dari artefak di disk.",
            )
            return

        risk = self._effective_risk()
        if not risk:
            fail(
                "Risk tidak terbaca dari parameter maupun frontmatter risk: TASK.md",
                "Minta pemanggil meneruskan parameter `risk`: ia plafon Check K, dan tanpanya nilai `risk:` brief tak punya batas atas.",
            )
            return

        if risk not in VALID_RISKS:
            fail(
                f"Risk '{risk}' tidak sah pada lane planning (wajib BREAKING | MAJOR | MINOR)",
                "Nilai `-` hanya berlaku pada lane non-mutasi kode; minta gerbang mengklasifikasi ulang.",
            )
            return

        if not self.file_scope_arg:
            # `file_scope` adalah satu-satunya pembanding yang menyebut apa yang
            # **diizinkan**; `## Out of Scope` menyebut apa yang dilarang. Keduanya
            # tidak setara, dan parameter yang lupa diteruskan pernah membuat
            # Check E berjalan terdegradasi sepanjang satu rantai penuh sambil
            # tetap mencetak PASS enam kali. Kegagalan di sini keras dan berisik;
            # remediasinya satu baris di pemanggil, bukan satu rantai yang
            # gerbang cakupannya mati diam-diam.
            fail(
                f"file_scope kosong pada lane planning (chain {chain}) — Check E akan berjalan "
                f"terdegradasi dengan `## Out of Scope` TASK.md sebagai satu-satunya pembanding",
                "Minta pemanggil meneruskan `file_scope` apa adanya: `backenddev:analyst` pada lane "
                "planning (parameter `file_scope`-nya sendiri), gerbang `backenddev:tech-lead` pada "
                "jalur RCA (slot `File Scope` laporan rutenya). Batas yang "
                "menyebut apa yang diizinkan tidak dapat diturunkan dari batas yang menyebut apa "
                "yang dilarang.",
            )
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Chain {chain} · entry_mode {self.entry_mode_arg} · risk {risk} · file_scope terisi",
            "action": "",
        })

    def format_text(self) -> str:
        all_passed = all(r["status"] == "PASS" for r in self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        status_label = "PASS" if all_passed else "FAIL"

        lines = [
            f"PRECONDITION CHECK: plan [{status_label}] ({passed_count}/{total} passed)",
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
            "entry_mode": self.entry_mode_arg,
            "chain": self._effective_chain(),
            "risk": self._effective_risk(),
            "file_scope": self.file_scope_arg,
            "profile_freshness": getattr(self, "profile_freshness", ("TAK_TERNILAI", "belum dinilai"))[0],
            "checks": self.results
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Plan Preconditions Validator")
    parser.add_argument("--taskdir", type=str, default=None, help="Task directory path")
    parser.add_argument("--entry-mode", type=str, default=None, help="Entry mode WAJIB eksplisit (PRD | RCA | LANGSUNG); tidak ada nilai bawaan")
    parser.add_argument("--chain", type=str, default=None, help="Chain enum (BRD_PRD_BRIEF | PRD_BRIEF | BRIEF); fallback: frontmatter chain: TASK.md")
    parser.add_argument("--risk", type=str, default=None, help="Plafon risk Check K (BREAKING | MAJOR | MINOR); fallback: frontmatter risk: TASK.md")
    parser.add_argument("--file-scope", type=str, default=None, help="Slot File Scope laporan rute gerbang; pembanding Check E")
    parser.add_argument("--root", type=str, default=None, help="Root path of target repository")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(
        taskdir=args.taskdir,
        entry_mode=args.entry_mode,
        chain=args.chain,
        risk=args.risk,
        file_scope=args.file_scope,
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
