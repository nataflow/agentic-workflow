#!/usr/bin/env python3
"""Architect Precondition Validator.

Dua tingkat vonis, satu skrip:

**Rantai** (tanpa `--brief`) — dijalankan sekali di Fase 0 `frontend:architect`:
bentuk taskdir, akar `TASK.md` beserta lane/sections, ledger `## Chain`
tercentang penuh dan kontennya utuh (termasuk batch brief dan `REVIEW-PLAN.md`
yang disetujui), status seluruh brief, profil lengkap beserta adapter, berkas
dispatcher/template/agent, working tree bersih, dan HEAD tidak detached. Skrip
juga **menyelesaikan** keadaan rantai di baris `Terselesaikan:` — `fase`
(EKSEKUSI | TERPUTUS | PENUTUP | LAPORAN | TUNTAS | TERHENTI | TEMUAN) dan `unit_berikutnya` — sehingga
titik mulai tidak ditebak dari membaca frontmatter satu per satu.

**Ingest** (`--brief NN`) — dijalankan sebelum tiap dispatch implementor:
ditambah brief target `READY` ber-`files_touched`, seluruh `depends_on` `DONE`
dengan commit `implement unit` berkode sejak `base_commit`, `report-<NN>.md` belum ada, dan
kesegaran `based_on` (`WARN`, bukan `FAIL`).

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    profile_dir_for,
    PROFILE_FILES,
    as_list,
    brief_closure,
    check_adapter,
    check_chain_rows,
    check_plugin_files,
    check_profile,
    check_task_root,
    check_taskdir,
    check_worktree,
    done_landed,
    expected_rows,
    find_repo_root,
    format_report,
    git,
    normalize_taskdir,
    parse_frontmatter,
    read_status,
    report_json,
    review_is_fresh,
    runnable_briefs,
    taskdir_slug,
    typecheck_per_brief,
)
from precondition_lib import cli  # noqa: E402

VALIDATE_BRIEFS = Path(__file__).resolve().parents[2] / "plan" / "scripts" / "validate_briefs.py"
VALIDATE_REPORT = Path(__file__).resolve().parents[2] / "report" / "scripts" / "validate_report.py"

BRIEF_PATTERN = re.compile(r"^brief-(\d{2})-[a-z0-9-]+\.md$")
PLUGIN_FILES = ("dispatcher/implementor.md", "dispatcher/reviewer.md",
                "templates/review-template.md", "references/execution-protocol.md",
                "scripts/validate_review.py", "../../agents/code-implementor.md",
                "../../agents/code-reviewer.md")
BRIEF_STATUS = ("READY", "DONE", "BLOCKED")
# Kotoran di luar taskdir pada fase PENUTUP (12 J55): prasyarat dijalankan ulang sesudah verifikasi penutup,
# sebelum reviewer — jejak perintah verifikasi akan divonis check TREE `validate_review.py` sebagai mutasi reviewer.
CLOSING_DIRT_ACTION = ("Fase PENUTUP: kotoran di luar taskdir sesudah verifikasi penutup adalah jejak perintah "
                       "verifikasi (snapshot test baru, coverage, `*.tsbuildinfo`, `lint --fix` atas berkas ter-track) "
                       "atau kerja user. Hentikan sebelum reviewer berangkat dan sajikan path-nya ke user lewat "
                       "`AskUserQuestion`: buang/pulihkan (keputusan user), tambah pola ignore lewat `frontend:profile` "
                       "REFRESH, atau brief perbaikan (`chain.py reopen --row BRIEF`) bila berkas itu bagian rantai; "
                       "lalu ulangi Phase 4 dari butir 1. Dilarang membersihkan otomatis.")


# Brief DONE tanpa commit unit (25 R6): sesi terputus di antara status DONE dan commit kode, `DONE` diketik
# tangan, atau commit unit di-reset. Tidak didispatch ulang; disk-nya divonis matriks bukti disk.
TERPUTUS_ACTION = ("Fase TERPUTUS: jalankan matriks bukti disk (`references/execution-protocol.md` bagian 3) atas "
                   "brief-{nn} tanpa dispatch, mulai dari `verify_scope.py --brief <brief-{nn}> --worktree`: "
                   "`report-{nn}.md` DONE + hanya `files_touched` berubah → commit unit; laporan absen/rusak + tree "
                   "bersih → kembalikan status brief ke `READY` di disk lalu Phase 1 (dispatch ulang); berkas di luar "
                   "`files_touched` atau laporan FAILED → HENTIKAN, sajikan ke user — dilarang memulihkan kotoran yang "
                   "asalnya tak diketahui.")
TERPUTUS_DIRT_ACTION = ("Fase TERPUTUS: kotoran ini divonis matriks bukti disk atas brief-{nn} "
                        "(`verify_scope.py --worktree`), bukan oleh check ini. Dilarang stash atau bersihkan sendiri.")


class PreconditionChecker:
    def __init__(self, taskdir: str, brief: Optional[str] = None, root: Optional[Path] = None,
                 profile_dir: Optional[str] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.taskdir = self.root / self.taskdir_rel
        self.brief_nn = brief
        self.profile_dir = profile_dir_for(self.root, profile_dir)
        self.skill_dir = Path(__file__).resolve().parents[1]
        self.results: List[Dict[str, Any]] = []
        self.stack = ""
        self.lane = ""
        self.sections: List[str] = []
        self.phase = "-"
        self.next_unit = "-"
        self._closure: Optional[Dict[str, Any]] = None

    def _add(self, cid: int, name: str, status: str, summary: str, action: str = "") -> None:
        self.results.append({"id": cid, "name": name, "status": status,
                             "summary": summary, "action": action})

    def remedies(self) -> Dict[str, List[str]]:
        """`{NN asal: [NN remedi, ...]}` dari field `remedies` brief."""
        out: Dict[str, List[str]] = {}
        for nn, p in self.briefs().items():
            origin = str(parse_frontmatter(p.read_text(encoding="utf-8")).get("remedies", "")).strip()
            if origin:
                out.setdefault(origin, []).append(nn)
        return out

    def closed(self, nn: str) -> bool:
        """Unit tertutup: `DONE` yang mendarat bersama kode, atau `BLOCKED` yang punya remedi tertutup.

        Satu implementasi dengan `report`/`taskdir_state` (`brief_closure`, penjaga siklus remedi — 12 J20).
        """
        if self._closure is None:
            self._closure = brief_closure(self.taskdir, self.root)
        return self._closure.get(nn, ("", False))[1]

    def implemented(self, nn: str) -> bool:
        """Brief `DONE` sah hanya bila laporannya ada dan commit `implement unit <NN>` pembawa kode mendarat sejak
        `base_commit` (12 J15, padanan 09 E18; 24 K7 — status brief tidak lagi ada di riwayat git)."""
        path = self.briefs().get(nn)
        if path is None or not (self.taskdir / f"report-{nn}.md").is_file():
            return False
        return bool(done_landed(self.root, f"{self.taskdir_rel}/{path.name}"))

    def squashed_finished(self) -> bool:
        """`REPORT.md` ada, `REVIEW.md` `PASS`/`WARNING`, dan `head:` review tidak lagi leluhur `HEAD` (riwayat
        ditulis ulang). Padanan `taskdir_state.review_head_rewritten` untuk penjaga fase `TERPUTUS` (25 R6)."""
        review = self.taskdir / "REVIEW.md"
        if not (self.taskdir / "REPORT.md").is_file() or read_status(review, "verdict") not in ("PASS", "WARNING"):
            return False
        head = read_status(review, "head")
        if not re.fullmatch(r"[0-9a-f]{7,40}", head):
            return False
        full = git(self.root, "rev-parse", "--verify", "-q", f"{head}^{{commit}}").strip()
        if not full:
            return True
        return subprocess.run(["git", "-C", str(self.root), "merge-base", "--is-ancestor", full, "HEAD"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0

    def briefs(self) -> Dict[str, Path]:
        out: Dict[str, Path] = {}
        if self.taskdir.is_dir():
            for p in sorted(self.taskdir.iterdir()):
                m = BRIEF_PATTERN.match(p.name)
                if m:
                    out.setdefault(m.group(1), p)
        return out

    # ---------------------------------------------------------------- rantai

    def run_all(self) -> bool:
        taskdir_ok = check_taskdir(self._add, 1, self.root, self.taskdir_rel)
        if taskdir_ok:
            self.lane, self.sections = check_task_root(self._add, 2, self.root, self.taskdir_rel)
        else:
            self._add(2, "TASK.md akar, lane & sections", "FAIL", "taskdir tidak sah",
                      "Perbaiki Check 1 lebih dulu.")
        if self.lane:
            check_chain_rows(self._add, 3, self.root, self.taskdir_rel,
                             expected_rows(self.sections), self.sections)
        else:
            self._add(3, "Ledger ## Chain tercentang", "FAIL", "akar belum sah",
                      "Perbaiki Check 2 lebih dulu.")
        self._check_4_briefs(taskdir_ok)
        self.stack = check_profile(self._add, 5, self.profile_dir, PROFILE_FILES)
        check_adapter(self._add, 6, self.stack)
        check_plugin_files(self._add, 7, self.skill_dir, PLUGIN_FILES)
        # Dokumen taskdir diabaikan git (Langkah 24): yang dinilai kotor hanya kode dan dokumen tingkat repo.
        if self.phase == "TERPUTUS":
            check_worktree(self._add, 8, self.root, self.taskdir_rel,
                           foreign_action=TERPUTUS_DIRT_ACTION.format(nn=self.next_unit), dirty_status="WARN")
        else:
            check_worktree(self._add, 8, self.root, self.taskdir_rel,
                           foreign_action=CLOSING_DIRT_ACTION if self.phase == "PENUTUP" else "")
        self._check_9_head()
        if self.brief_nn:
            self._check_10_target()
            self._check_11_dependencies()
            self._check_12_report_absent()
            self._check_13_freshness()
        return not any(r["status"] == "FAIL" for r in self.results)

    def _check_4_briefs(self, taskdir_ok: bool) -> None:
        name = "Status brief & fase rantai"
        if not taskdir_ok:
            self._add(4, name, "FAIL", "taskdir tidak sah", "Perbaiki Check 1 lebih dulu.")
            return
        briefs = self.briefs()
        if not briefs:
            self._add(4, name, "FAIL", "nol brief", "Jalankan `frontend:plan` lebih dulu.")
            return
        states = {nn: read_status(p) for nn, p in briefs.items()}
        bad = [f"brief-{nn} `{s or 'kosong'}`" for nn, s in states.items() if s not in BRIEF_STATUS]
        if bad:
            self._add(4, name, "FAIL", "status di luar READY/DONE/BLOCKED: " + ", ".join(bad),
                      "Hentikan dan laporkan nilai terbaca beserta path-nya; dilarang menebak.")
            return
        unlanded = [nn for nn, st in states.items()
                    if st == "DONE" and not done_landed(self.root, f"{self.taskdir_rel}/{briefs[nn].name}")]
        if unlanded and self.squashed_finished():
            # Rantai tuntas yang di-squash-merge kehilangan commit unitnya, bukan keabsahannya (12 J44) — sama
            # dengan vonis `TUNTAS` `taskdir_state.py`; jangan dibaca sebagai unit yang terputus.
            self.phase = "TUNTAS"
            self._add(4, name, "PASS", "rantai tuntas; commit unit hilang karena riwayat ditulis ulang (squash-merge)")
            return
        if unlanded:
            # Fase TERPUTUS (25 R6): dulu FAIL, sehingga architect kembali ke lead dan lead (`taskdir_state`)
            # merutekannya sebagai TERHENTI (DAG) atau PENUTUP — tak ada pihak yang menjalankan matriksnya.
            self.phase = "TERPUTUS"
            self.next_unit = unlanded[0]
            self._add(4, name, "WARN", "brief DONE tanpa commit `implement unit NN` berkode: " + ", ".join(unlanded),
                      TERPUTUS_ACTION.format(nn=unlanded[0]))
            return
        fake = [nn for nn, st in states.items() if st == "DONE" and not self.implemented(nn)]
        if fake:
            self._add(4, name, "FAIL", "brief DONE ber-commit unit tetapi tanpa `report-NN.md`: " + ", ".join(fake),
                      "Laporan unit hilang dari disk sesudah commit mendarat; pulihkan dari cermin nataflow atau "
                      "laporkan ke user — dilarang mendispatch ulang unit yang sudah mendarat.")
            return
        # Brief BLOCKED tanpa remedi divonis **sebelum** validate_briefs: janji yang dipikulnya kini tak
        # dipikul brief READY/DONE mana pun (Check G), jadi validator pasti FAIL dan menutupi fase TERHENTI
        # beserta rutenya (12 J20).
        remedies = self.remedies()
        open_blocked = [nn for nn, s in sorted(states.items())
                        if s == "BLOCKED" and not remedies.get(nn)]
        if open_blocked:
            self.phase = f"TERHENTI (brief-{open_blocked[0]} BLOCKED)"
            self._add(4, name, "FAIL", f"brief BLOCKED tanpa remedi: {', '.join(open_blocked)}",
                      "Rantai berhenti. Brief remedi lewat `chain.py reopen --row BRIEF` lalu "
                      "`frontend:plan` mode APPEND (`remedies: \"NN\"`) pada taskdir yang sama.")
            return
        args = [sys.executable, str(VALIDATE_BRIEFS), "--taskdir", self.taskdir_rel, "--root", str(self.root)]
        if self.sections:
            args.append("--contract")
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        if proc.returncode != 0:
            self._add(4, name, "FAIL", "`validate_briefs.py` FAIL: " + proc.stdout.splitlines()[0][:100],
                      "Batch brief tidak lagi sah terhadap akar/kontrak; kembali ke `frontend:lead`.")
            return
        ready = [nn for nn, s in sorted(states.items()) if s == "READY"]
        if ready:
            runnable = runnable_briefs(self.taskdir, self.root)
            if not runnable:
                self.phase = "TERHENTI (DAG)"
                self._add(4, name, "FAIL", f"{len(ready)} brief READY tetapi prasyaratnya tak satu pun tertutup",
                          "Rantai buntu (mis. remedi ber-`depends_on` unit asalnya). Kembali ke `frontend:lead`: "
                          "`chain.py reopen --row BRIEF` → `frontend:plan` mode APPEND memperbaiki `depends_on`.")
                return
            self.phase = "EKSEKUSI"
            self.next_unit = runnable[0]
            self._add(4, name, "PASS", f"{len(ready)} READY; mulai brief-{runnable[0]}")
            return
        review = self.taskdir / "REVIEW.md"
        report = self.taskdir / "REPORT.md"
        valid = review.is_file() and subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "validate_review.py"),
             "--taskdir", self.taskdir_rel, "--root", str(self.root)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if not review.is_file() or not review_is_fresh(self.root, self.taskdir_rel) or not valid:
            self.phase = "PENUTUP"
        elif not report.is_file():
            self.phase = "LAPORAN" if read_status(review, "verdict") in ("PASS", "WARNING") else "TEMUAN (REVIEW BLOCKED)"
        elif subprocess.run([sys.executable, str(VALIDATE_REPORT), "--taskdir", self.taskdir_rel,
                             "--root", str(self.root)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL).returncode != 0:
            self.phase = "LAPORAN TERTUNDA"
        else:
            self.phase = "TUNTAS"
        self._add(4, name, "PASS", f"seluruh {len(states)} brief tertutup — fase {self.phase}")

    def _check_9_head(self) -> None:
        name = "HEAD pada branch"
        # `--git-path` menunjuk git dir yang benar juga di worktree/submodule, tempat `.git` berupa berkas.
        paths = {d: git(self.root, "rev-parse", "--git-path", d).strip() for d in ("rebase-apply", "rebase-merge")}
        ongoing = [d for d, p in paths.items() if p and (self.root / p).exists()]
        if ongoing:
            self._add(9, name, "FAIL", f"rebase/`git am` sedang berjalan (`{ongoing[0]}`)",
                      "Selesaikan atau batalkan (`git rebase --abort` / `git am --abort`) dulu.")
            return
        branch = git(self.root, "symbolic-ref", "--short", "-q", "HEAD").strip()
        if not branch:
            self._add(9, name, "FAIL", "detached HEAD",
                      "Checkout branch sah sebelum commit unit mana pun.")
            return
        self._add(9, name, "PASS", f"branch `{branch}`")

    # ---------------------------------------------------------------- ingest

    def _target(self) -> Optional[Path]:
        return self.briefs().get(self.brief_nn or "")

    def _check_10_target(self) -> None:
        name = f"brief-{self.brief_nn} READY"
        path = self._target()
        if path is None:
            self._add(10, name, "FAIL", f"`brief-{self.brief_nn}-*.md` tidak ada",
                      "Periksa nomor unit dari `unit_berikutnya` rantai.")
            return
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        status = str(fm.get("status", "")).strip()
        if status != "READY":
            self._add(10, name, "FAIL", f"{path.name} berstatus `{status or '(kosong)'}`",
                      "Hanya brief `READY` yang didispatch; `DONE` sudah selesai, `BLOCKED` menahan rantai.")
            return
        if not fm.get("files_touched"):
            self._add(10, name, "FAIL", f"{path.name} tanpa `files_touched`",
                      "Batas scope unit tidak ada; kembalikan ke `frontend:plan`.")
            return
        stack = str(fm.get("stack", "")).strip()
        if self.stack and stack != self.stack:
            self._add(10, name, "FAIL", f"{path.name} `stack: {stack or '(kosong)'}` ≠ stack profil `{self.stack}`",
                      "Brief lahir untuk stack lain (12 J16); kembalikan ke `frontend:lead` — dilarang menyunting "
                      "`stack` brief agar lolos.")
            return
        self._add(10, name, "PASS", f"{path.name}, {len(fm['files_touched'])} berkas")

    def _check_11_dependencies(self) -> None:
        name = "depends_on DONE & ter-commit"
        path = self._target()
        if path is None:
            self._add(11, name, "FAIL", "brief target tidak ada", "Perbaiki Check 10 lebih dulu.")
            return
        deps = as_list(parse_frontmatter(path.read_text(encoding="utf-8")).get("depends_on"))
        problems = []
        for dep in deps:
            dep_path = self.briefs().get(dep)
            if dep_path is None:
                problems.append(f"unit `{dep}` tanpa berkas brief")
                continue
            if not self.closed(dep):
                problems.append(f"unit `{dep}` belum tertutup (`DONE`, atau `BLOCKED` ber-remedi `DONE`)")
                continue
            if read_status(dep_path) != "DONE":
                continue
            if not self.implemented(dep):
                problems.append(f"unit `{dep}` DONE tanpa commit `implement unit {dep}` berkode sejak `base_commit`")
        if problems:
            self._add(11, name, "FAIL", "; ".join(problems),
                      "Selesaikan dan commit unit prasyarat lebih dulu, berurutan.")
            return
        self._add(11, name, "PASS", f"{len(deps)} prasyarat DONE" if deps else "unit akar")

    def _check_12_report_absent(self) -> None:
        name = f"report-{self.brief_nn}.md belum ada"
        path = self.taskdir / f"report-{self.brief_nn}.md"
        if path.is_file():
            self._add(12, name, "FAIL", f"`{path.name}` sudah ada berstatus `{read_status(path) or 'kosong'}`",
                      "Laporan unit ini sudah pernah ditulis — jalankan matriks bukti disk "
                      "(`references/execution-protocol.md` bagian 3) sebelum dispatch ulang.")
            return
        self._add(12, name, "PASS", "belum pernah didispatch")

    def _check_13_freshness(self) -> None:
        name = "Kesegaran brief (based_on)"
        path = self._target()
        if path is None:
            self._add(13, name, "FAIL", "brief target tidak ada", "Perbaiki Check 10 lebih dulu.")
            return
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        m = re.match(r"^([0-9a-f]{7,40})\b", str(fm.get("based_on", "")).strip())
        if not m:
            self._add(13, name, "WARN", "`based_on` bukan sha — kesegaran tak dapat divonis",
                      "Sebut ke user sebelum dispatch.")
            return
        if not git(self.root, "cat-file", "-t", m.group(1)).strip():
            self._add(13, name, "WARN", f"`based_on` {m.group(1)} tidak ada di repo — kesegaran tak dapat divonis",
                      "Sebut ke user sebelum dispatch; brief mungkin ditulis di cabang lain.")
            return
        # Hanya commit unit taskdir INI yang dikecualikan; `implement unit` milik taskdir lain tetap asing.
        own_unit = re.compile(rf"^[a-z]+!?\({re.escape(taskdir_slug(self.taskdir_rel))}\)!?: implement unit \d+")
        stale = []
        for f in as_list(fm.get("files_touched")):
            subjects = git(self.root, "log", "--format=%s", f"{m.group(1)}..HEAD", "--", f).splitlines()
            foreign = [s for s in subjects if s.strip() and not own_unit.match(s)]
            if foreign:
                stale.append(f"{f} ({len(foreign)} commit)")
        if stale:
            self._add(13, name, "WARN", "berkas berubah sesudah brief ditulis: " + "; ".join(stale[:4]),
                      "Sebut ke user; brief yang tak lagi cocok dikembalikan ke `frontend:plan`.")
            return
        self._add(13, name, "PASS", f"nol commit asing menyentuh `files_touched` sesudah {m.group(1)}")

    # ---------------------------------------------------------------- output

    def tpb(self) -> str:
        value, source = typecheck_per_brief(self.profile_dir, self.stack or "")
        return f"{value} ({source})"

    def format_text(self) -> str:
        return format_report("architect" + (f" ingest brief-{self.brief_nn}" if self.brief_nn else ""),
                             self.results, {"fase": self.phase, "unit_berikutnya": self.next_unit,
                                            "lane": self.lane or "-", "typecheck_per_brief": self.tpb()})

    def to_json(self) -> str:
        return report_json(self.results, root=str(self.root), taskdir=self.taskdir_rel,
                           brief=self.brief_nn, phase=self.phase, next_unit=self.next_unit,
                           lane=self.lane, stack=self.stack, typecheck_per_brief=self.tpb())


def main() -> None:
    parser = argparse.ArgumentParser(description="Architect Preconditions Checker")
    parser.add_argument("--taskdir", required=True)
    parser.add_argument("--brief", default=None, help="NN unit untuk vonis ingest")
    parser.add_argument("--profile-dir", default=None, dest="profile_dir")
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    checker = PreconditionChecker(args.taskdir, args.brief,
                                  Path(args.root) if args.root else None, args.profile_dir)
    ok = checker.run_all()
    print(checker.to_json() if args.json else checker.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    sys.exit(cli(main))
