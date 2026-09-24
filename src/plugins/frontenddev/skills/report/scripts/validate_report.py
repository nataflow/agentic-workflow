#!/usr/bin/env python3
"""REPORT.md Validator.

Memvonis bentuk `REPORT.md` terhadap `templates/report-template.md`: judul
diturunkan dari H1 `TASK.md`, urutan heading, Ringkasan satu kalimat, butir
Perubahan berakar pada berkas rantai dan mencakup seluruhnya, Catatan tidak
basa-basi, tiap `SC-{n}` yang `REVIEW.md` vonis `PERLU VERIFIKASI MANUAL`
tercatat di Catatan (sumbernya tabel `## Cakupan Success Criteria` `REVIEW.md`,
bukan tebakan dari berkas rantai), dan nol placeholder.

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
    chain_files,
    find_repo_root,
    format_report,
    normalize_taskdir,
    report_json,
    section_lines,
    split_frontmatter,
)

REVIEW_SC_ROW = re.compile(r"^\|\s*`?(SC-\d+)`?\s*\|\s*([^|]+?)\s*\|")

SC_LINE = re.compile(r"^- \[[ xX]\] \*\*(SC-\d+)\*\*:(.*)$")
INLINE_CODE = re.compile(r"`[^`\n]*`")
SENTENCE_END = re.compile(r"[.!?](?=\s|$)")
BULLET = re.compile(r"^- (.+) \(([^()]+)\)\s*$")
PLACEHOLDER = re.compile(r"\{\{|<!--|<[^<>\n]+>")
EMPTY_NOTE = re.compile(r"^(-|n/?a|tidak ada|nihil)\.?$", re.IGNORECASE)


class ReportValidator:
    def __init__(self, taskdir: str, root: Optional[Path] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.taskdir = self.root / self.taskdir_rel
        self.results: List[Dict[str, Any]] = []

    def _add(self, cid: int, name: str, ok: bool, summary: str, action: str = "") -> None:
        self.results.append({"id": cid, "name": name, "status": "PASS" if ok else "FAIL",
                             "summary": summary, "action": "" if ok else action})

    @staticmethod
    def _sections(text: str) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        current = None
        for line in text.splitlines():
            if line.startswith("## "):
                current = line.strip()
                out[current] = []
            elif current:
                out[current].append(line)
        return out

    def run_all(self) -> bool:
        report, task = self.taskdir / "REPORT.md", self.taskdir / "TASK.md"
        if not report.is_file() or not task.is_file():
            self._add(1, "REPORT.md & TASK.md terbaca", False, "salah satu berkas tidak ada",
                      "Tulis REPORT.md di taskdir yang berakar TASK.md.")
            return False
        self.text = report.read_text(encoding="utf-8")
        self.task = task.read_text(encoding="utf-8")
        self.sec = self._sections(self.text)
        self._check_1_title()
        self._check_2_headings()
        self._check_3_summary()
        self._check_4_changes()
        self._check_5_notes()
        self._check_6_placeholder()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_title(self) -> None:
        h1 = [l[2:].strip() for l in self.text.splitlines() if l.startswith("# ")]
        task_h1 = [l[2:].strip() for l in self.task.splitlines() if l.startswith("# ")]
        want = f"{task_h1[0]} — Report" if task_h1 else ""
        ok = len(h1) == 1 and bool(want) and h1[0] == want
        self._add(1, "Judul dari H1 TASK.md", ok, f"H1 {h1}" if not ok else "lolos",
                  f"Tulis tepat satu H1: `# {want}`.")

    def _check_2_headings(self) -> None:
        heads = list(self.sec)
        ok = heads in (["## Ringkasan", "## Perubahan"], ["## Ringkasan", "## Perubahan", "## Catatan"])
        self._add(2, "Urutan heading", ok, f"{heads}" if not ok else "lolos",
                  "Heading sah: Ringkasan, Perubahan, lalu Catatan opsional.")

    def _check_3_summary(self) -> None:
        body = " ".join(l.strip() for l in self.sec.get("## Ringkasan", []) if l.strip())
        ends = len(SENTENCE_END.findall(INLINE_CODE.sub("``", body)))
        ok = bool(body) and ends == 1 and SENTENCE_END.search(body.rstrip()[-1:] or "x") is not None
        self._add(3, "Ringkasan satu kalimat", ok, f"{ends} akhir kalimat" if not ok else "lolos",
                  "Tulis tepat satu kalimat yang diakhiri titik.")

    def _check_4_changes(self) -> None:
        lines = [l.strip() for l in self.sec.get("## Perubahan", []) if l.strip()]
        bullets = [BULLET.match(l) for l in lines]
        errors = []
        if not 1 <= len(lines) <= 7:
            errors.append(f"{len(lines)} butir, sah 1–7")
        if any(b is None for b in bullets):
            errors.append("butir tanpa `(<berkas atau direktori>)` di ujungnya")
        refs = [r.strip().strip("`").rstrip("/") for b in bullets if b for r in b.group(2).split(",")]
        files = chain_files(self.root, self.taskdir_rel)

        def covers(ref: str, f: str) -> bool:
            return f == ref or f.startswith(ref + "/")

        stray = [r for r in refs if not any(covers(r, f) for f in files)]
        orphan = [f for f in files if not any(covers(r, f) for r in refs)]
        if stray:
            errors.append("bukan berkas rantai: " + ", ".join(stray[:5]))
        if orphan:
            errors.append("berkas rantai tak tercakup: " + ", ".join(orphan[:5]))
        self._add(4, "Perubahan berakar berkas rantai", not errors,
                  "; ".join(errors) or f"{len(lines)} butir mencakup {len(files)} berkas",
                  "Tiap butir ditutup kurung berisi berkas/direktori rantai, dan tiap berkas rantai tercakup.")

    def _check_5_notes(self) -> None:
        errors = []
        notes = [l.strip() for l in self.sec.get("## Catatan", []) if l.strip()]
        if "## Catatan" in self.sec and (not notes or all(EMPTY_NOTE.match(n.lstrip("- ")) for n in notes)):
            errors.append("Catatan kosong atau basa-basi — hapus heading-nya")
        manual = [m.group(1) for m in map(SC_LINE.match, (l.strip() for l in self.task.splitlines()))
                  if m and "— verifikasi:" in m.group(2) and not re.search(r"—\s*gugur:", m.group(2))
                  and m.group(2).split("— verifikasi:", 1)[1].strip().lower().startswith("qa manual:")]
        review = self.taskdir / "REVIEW.md"
        if review.is_file():
            _, rbody = split_frontmatter(review.read_text(encoding="utf-8"))
            for line in section_lines(rbody, "## Cakupan Success Criteria"):
                m = REVIEW_SC_ROW.match(line.strip())
                if m and m.group(2).strip() == "PERLU VERIFIKASI MANUAL" and m.group(1) not in manual:
                    manual.append(m.group(1))
                if m and m.group(2).strip() == "belum terbukti":
                    errors.append(f"{m.group(1)} belum terbukti di REVIEW.md — rantai ini tidak boleh dilaporkan")
        joined = "\n".join(notes)
        missing = [sc for sc in manual
                   if not re.search(rf"\b{sc}\b.*PERLU VERIFIKASI MANUAL", joined)]
        if missing:
            errors.append("SC QA manual tanpa `PERLU VERIFIKASI MANUAL`: " + ", ".join(missing))
        self._add(5, "Catatan jujur", not errors, "; ".join(errors) or "lolos",
                  "Catat tiap SC ber-`QA manual:` sebagai `SC-{n} — PERLU VERIFIKASI MANUAL: <langkah>`.")

    def _check_6_placeholder(self) -> None:
        hits = sorted(set(PLACEHOLDER.findall(INLINE_CODE.sub("", self.text))))
        self._add(6, "Nol placeholder", not hits, "sisa: " + ", ".join(hits[:5]) if hits else "lolos",
                  "Isi seluruh slot template dan hapus komentar.")

    def format_text(self) -> str:
        return format_report("report validate", self.results)

    def to_json(self) -> str:
        return report_json(self.results, root=str(self.root), taskdir=self.taskdir_rel)


def main() -> None:
    parser = argparse.ArgumentParser(description="REPORT.md validator")
    parser.add_argument("--taskdir", required=True, help="path taskdir relatif root repo")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()

    v = ReportValidator(args.taskdir, Path(args.root) if args.root else None)
    ok = v.run_all()
    print(v.to_json() if args.json else v.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
