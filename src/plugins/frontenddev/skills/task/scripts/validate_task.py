#!/usr/bin/env python3
"""TASK.md Self-test Validator.

Memvonis butir mekanis Self-test Akar (`templates/task-template.md` bagian 2):
1 struktur & frontmatter (termasuk pasangan `lane`/`sections`), 2 penomoran
`SC-{n}`, 3 alat ukur sah, 4 bukti `file:baris`, 6 Out of Scope bersuara,
7 nol placeholder & temuan terpikul, 9 ledger `## Chain` sesuai jadwal sections.
Butir 5 (ambang terukur) dan 8 (kecukupan akar) menuntut penilaian dan tetap
milik model.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    expected_rows,
    find_repo_root,
    fenced_mask,
    format_report,
    lane_sections_problem,
    normalize_taskdir,
    outside_fences,
    parse_sections,
    read_chain,
    report_json,
    find_placeholders,
    split_frontmatter,
)

HEADINGS = ("## Description", "## Success Criteria", "## Out of Scope", "## Chain")
SC_LINE = re.compile(r"^- \[[ xX]\] \*\*SC-(\d+)\*\*:(.*)$")
MEASURE = re.compile(r"— verifikasi:\s*(test|diff|typecheck|lint|build|qa\s+manual\s*:)", re.IGNORECASE)
FORBIDDEN_MEASURE = re.compile(r"review manual|dinilai layak|terlihat bagus", re.IGNORECASE)
DOWNSTREAM_DOCS = re.compile(r"\b(FLOW|UI|CONTRACT)\.md\b")
FILE_REF = re.compile(r"`([\w@./+-]+\.[A-Za-z0-9]+):(\d+)(?:-\d+)?`")
OOS_LINE = re.compile(r"^- .+ — .+$")


class TaskValidator:
    def __init__(self, taskdir: str, root: Optional[Path] = None, amend: bool = False):
        self.amend = amend
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.path = self.root / self.taskdir_rel / "TASK.md"
        self.results: List[Dict[str, Any]] = []

    def _add(self, cid: int, name: str, ok: bool, summary: str, action: str = "") -> None:
        self.results.append({"id": cid, "name": name, "status": "PASS" if ok else "FAIL",
                             "summary": summary, "action": "" if ok else action})

    def run_all(self) -> bool:
        if not self.path.is_file():
            self._add(1, "TASK.md terbaca", False, f"`{self.path}` tidak ada",
                      "Tulis TASK.md lebih dulu (Phase 4 butir 2).")
            return False
        text = self.path.read_text(encoding="utf-8")
        self.fm, self.body = split_frontmatter(text)
        self.sections = self._split_sections()
        self._check_1_structure()
        self._check_2_numbering()
        self._check_3_measure()
        self._check_4_evidence()
        self._check_6_out_of_scope()
        self._check_7_placeholder_findings(text)
        self._check_9_chain(text)
        return all(r["status"] == "PASS" for r in self.results)

    def _split_sections(self) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {}
        current = None
        lines = self.body.splitlines()
        for line, fenced in zip(lines, fenced_mask(lines)):
            if line.startswith("## ") and not fenced:
                current = line.strip()
                sections[current] = []
            elif current:
                sections[current].append(line)
        return sections

    def _sc_lines(self) -> List[re.Match]:
        lines = self.sections.get("## Success Criteria", [])
        return [m for m in (SC_LINE.match(l.strip()) for l in lines) if m]

    def _check_1_structure(self) -> None:
        errors = []
        if self.fm.get("status") != "ACTIVE":
            errors.append(f"status `{self.fm.get('status', '')}` bukan ACTIVE")
        problem = lane_sections_problem(str(self.fm.get("lane", "")),
                                        parse_sections(self.fm.get("sections", "")))
        if problem:
            errors.append(problem)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(self.fm.get("created", ""))):
            errors.append("created bukan YYYY-MM-DD")
        code = outside_fences(self.body.splitlines())
        h1 = [l for l in code if l.startswith("# ")]
        if len(h1) != 1:
            errors.append(f"{len(h1)} H1, wajib tepat satu")
        h2 = [l.strip() for l in code if l.startswith("## ")]
        if tuple(h2) != HEADINGS:
            errors.append(f"heading {h2} bukan {list(HEADINGS)}")
        self._add(1, "Struktur & frontmatter", not errors, "; ".join(errors) or "lolos",
                  "Ikuti bagian 1 template persis.")

    def _check_2_numbering(self) -> None:
        nums = [int(m.group(1)) for m in self._sc_lines()]
        ok = 1 <= len(nums) <= 7 and nums == list(range(1, len(nums) + 1))
        self._add(2, "Penomoran SC-{n}", ok, f"SC {nums}" if nums else "nol butir SC",
                  "Nomori 1–7 butir berurutan dari SC-1 tanpa lompatan atau ganda.")

    def _check_3_measure(self) -> None:
        bad = []
        for m in self._sc_lines():
            rest = m.group(2)
            _, _, measure = rest.partition("— verifikasi:")
            if (not MEASURE.search(rest) or FORBIDDEN_MEASURE.search(rest)
                    or DOWNSTREAM_DOCS.search(measure)):
                bad.append(f"SC-{m.group(1)}")
        self._add(3, "Alat ukur sah", not bad and bool(self._sc_lines()),
                  f"gagal: {', '.join(bad)}" if bad else "lolos",
                  "Pakai `— verifikasi:` + test | diff | typecheck | lint | build | QA manual:, "
                  "tanpa menunjuk FLOW/UI/CONTRACT.")

    def _check_4_evidence(self) -> None:
        desc = "\n".join(self.sections.get("## Description", []))
        refs = FILE_REF.findall(desc)
        dangling = []
        for path, line in refs:
            f = self.root / path
            if not f.is_file():
                dangling.append(f"{path}:{line} (berkas tidak ada)")
                continue
            try:
                count = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                count = 0
            if not 1 <= int(line) <= count:
                dangling.append(f"{path}:{line} (di luar {count} baris)")
        ok = bool(refs) and not dangling
        summary = ("nol rujukan `file:baris`" if not refs
                   else f"menggantung: {', '.join(dangling)}" if dangling
                   else f"{len(refs)} rujukan valid")
        self._add(4, "Bukti berpaut kode", ok, summary,
                  "Sebut minimal satu `path:baris` relatif root repo yang benar-benar ada.")

    def _check_6_out_of_scope(self) -> None:
        items = [l.strip() for l in self.sections.get("## Out of Scope", []) if l.strip().startswith("- ")]
        bad = [i for i in items if not OOS_LINE.match(i)]
        ok = bool(items) and not bad
        self._add(6, "Out of Scope bersuara", ok,
                  "kosong" if not items else (f"{len(bad)} butir tanpa alasan" if bad else f"{len(items)} butir"),
                  "Tulis minimal satu `- <yang tidak dikerjakan> — <alasan>`.")

    def _check_7_placeholder_findings(self, text: str) -> None:
        errors = []
        head = text.split("\n## Chain", 1)[0]
        hits = sorted({h for line in head.splitlines() for h in find_placeholders(line)})
        if hits:
            errors.append("placeholder: " + ", ".join(hits[:5]))
        source = self.fm.get("finding_source")
        findings = self.fm.get("findings")
        if isinstance(findings, str):
            findings = [findings] if findings else []
        if source or findings:
            if not source or not findings:
                errors.append("finding_source dan findings wajib hadir berpasangan")
            for fid in findings or []:
                owners = [m for m in self._sc_lines() if re.search(rf"\b{re.escape(fid)}\b", m.group(2))]
                if len(owners) != 1:
                    errors.append(f"{fid} dipikul {len(owners)} butir, wajib tepat satu")
                elif "Status: FIXED" not in owners[0].group(2):
                    errors.append(f"SC pemikul {fid} tanpa `> Status: FIXED`")
        self._add(7, "Nol placeholder & temuan terpikul", not errors,
                  "; ".join(errors) or "lolos",
                  "Hapus sisa placeholder; tiap ID temuan dipikul tepat satu SC ber-`> Status: FIXED`.")

    def _check_9_chain(self, text: str) -> None:
        entries = read_chain(text)
        expected = expected_rows(parse_sections(self.fm.get("sections", "")))
        present = [e["row"] for e in entries]
        errors = []
        if present != expected:
            errors.append(f"baris ledger {present} ≠ jadwal sections {expected}")
        ticked = [e["row"] for e in entries if e["mark"] != " "]
        if ticked and not self.amend:
            errors.append(f"akar baru tidak boleh bercentang: {ticked}")
        self._add(9, "Ledger ## Chain", not errors, "; ".join(errors) or f"{len(present)} hop `[ ]`",
                  "Tulis ledger lewat `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py init "
                  "--taskdir <taskdir>`; dilarang mengetik baris ledger dengan tangan.")

    def format_text(self) -> str:
        return format_report("task self-test", self.results)

    def to_json(self) -> str:
        return report_json(self.results, root=str(self.root), taskdir=self.taskdir_rel)


def main() -> None:
    parser = argparse.ArgumentParser(description="TASK.md self-test validator")
    parser.add_argument("--taskdir", required=True, help="path taskdir relatif root repo")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--amend", action="store_true",
                        help="amandemen akar oleh lead: ledger boleh bercentang")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()

    v = TaskValidator(args.taskdir, Path(args.root) if args.root else None, args.amend)
    ok = v.run_all()
    print(v.to_json() if args.json else v.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
