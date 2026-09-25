#!/usr/bin/env python3
"""REPORT.md Validator.

Memvonis bentuk `REPORT.md` terhadap `templates/report-template.md`: judul
diturunkan dari H1 `TASK.md`, urutan heading, Ringkasan satu kalimat bermakna
(≥ 5 kata, bukan "Selesai."), butir Perubahan bermakna (≥ 3 kata) yang berakar
pada berkas rantai dan mencakup seluruhnya tanpa rujukan direktori tingkat atas,
Catatan tidak basa-basi, tiap `SC-{n}` yang `REVIEW.md` vonis `PERLU VERIFIKASI
MANUAL` dan tiap temuan `REVIEW.md` ber-`> Status: PLANNED|DEFERRED` tercatat di
Catatan (sumbernya `REVIEW.md`, bukan tebakan dari berkas rantai), dan nol
placeholder.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`, di-bootstrap relatif
terhadap berkas ini.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    BOM,
    chain_files,
    find_repo_root,
    fenced_mask,
    format_report,
    is_manual,
    normalize_taskdir,
    outside_fences,
    report_json,
    section_lines,
    split_frontmatter,
)

REVIEW_SC_ROW = re.compile(r"^\|\s*`?(SC-\d+)`?\s*\|\s*([^|]+?)\s*\|")

SC_LINE = re.compile(r"^- \[[ xX]\] \*\*(SC-\d+)\*\*:(.*)$")
INLINE_CODE = re.compile(r"`[^`\n]*`")
SENTENCE_END = re.compile(r"[.!?](?=\s|$)")
PLACEHOLDER = re.compile(r"\{\{|<!--|<[^<>\n]+>")
EMPTY_NOTE = re.compile(r"^(-|n/?a|tidak ada|nihil)\.?$", re.IGNORECASE)
TRIVIAL = re.compile(r"^(selesai|done|beres|ok|oke|sudah|tuntas)\.?$", re.IGNORECASE)
OPEN_FINDING = re.compile(r"^### \[(P[123]-\d+)\]")
MIN_SUMMARY_WORDS = 5
MIN_BULLET_WORDS = 3


def parse_bullet(line: str) -> Optional[Tuple[str, str]]:
    """`- <teks> (<anotasi>)` → (teks, anotasi); anotasi = kurung seimbang TERAKHIR di ujung baris.

    Kurung di dalam anotasi sah, sehingga route group (`app/(tabs)/…` Expo Router,
    `src/routes/(app)/…` SvelteKit) dapat disebut apa adanya.
    """
    s = line.rstrip()
    if not s.startswith("- ") or not s.endswith(")"):
        return None
    depth = 0
    for i in range(len(s) - 1, 1, -1):
        if s[i] == ")":
            depth += 1
        elif s[i] == "(":
            depth -= 1
            if depth == 0:
                text, inner = s[2:i].rstrip(), s[i + 1:-1].strip()
                return (text, inner) if text and inner else None
    return None


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
        lines = text.splitlines()
        for line, fenced in zip(lines, fenced_mask(lines)):
            if line.startswith("## ") and not fenced:
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
        self.text = report.read_text(encoding="utf-8").lstrip(BOM)
        self.task = task.read_text(encoding="utf-8").lstrip(BOM)
        self.sec = self._sections(self.text)
        self._check_1_title()
        self._check_2_headings()
        self._check_3_summary()
        self._check_4_changes()
        self._check_5_notes()
        self._check_6_placeholder()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_title(self) -> None:
        h1 = [l[2:].strip() for l in outside_fences(self.text.splitlines()) if l.startswith("# ")]
        task_h1 = [l[2:].strip() for l in outside_fences(split_frontmatter(self.task)[1].splitlines())
                   if l.startswith("# ")]
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
        words = len(INLINE_CODE.sub("kode", body).split())
        errors = []
        if not (bool(body) and ends == 1 and SENTENCE_END.search(body.rstrip()[-1:] or "x") is not None):
            errors.append(f"{ends} akhir kalimat")
        if body and (words < MIN_SUMMARY_WORDS or TRIVIAL.match(body.strip())):
            errors.append(f"Ringkasan `{body}` terlalu umum (< {MIN_SUMMARY_WORDS} kata)")
        self._add(3, "Ringkasan satu kalimat", not errors, "; ".join(errors) or "lolos",
                  f"Tulis tepat satu kalimat hasil aktual (≥ {MIN_SUMMARY_WORDS} kata) yang diakhiri titik.")

    def _check_4_changes(self) -> None:
        lines = [l.strip() for l in self.sec.get("## Perubahan", []) if l.strip()]
        bullets = [parse_bullet(l) for l in lines]
        errors = []
        if not 1 <= len(lines) <= 7:
            errors.append(f"{len(lines)} butir, sah 1–7")
        if any(b is None for b in bullets):
            errors.append("butir tanpa `(<berkas atau direktori>)` di ujungnya")
        refs = [r.strip().strip("`").rstrip("/") for b in bullets if b for r in b[1].split(",")]
        files = chain_files(self.root, self.taskdir_rel)

        def covers(ref: str, f: str) -> bool:
            return f == ref or f.startswith(ref + "/")

        vague = [b[0] for b in bullets if b and len(b[0].split()) < MIN_BULLET_WORDS]
        if vague:
            errors.append(f"butir tanpa perubahan perilaku (< {MIN_BULLET_WORDS} kata): " + ", ".join(vague[:3]))
        broad = [r for r in refs if "/" not in r and r not in files]
        if broad:
            errors.append("rujukan terlalu lebar (direktori tingkat atas): " + ", ".join(broad[:3]))
        stray = [r for r in refs if not any(covers(r, f) for f in files)]
        orphan = [f for f in files if not any(covers(r, f) for r in refs)]
        if stray:
            errors.append("bukan berkas rantai: " + ", ".join(stray[:5]))
        if orphan:
            errors.append("berkas rantai tak tercakup: " + ", ".join(orphan[:5]))
        self._add(4, "Perubahan berakar berkas rantai", not errors,
                  "; ".join(errors) or f"{len(lines)} butir mencakup {len(files)} berkas",
                  f"Tiap butir menyebut perubahan perilaku (≥ {MIN_BULLET_WORDS} kata) dan ditutup kurung berisi "
                  "berkas/direktori rantai (bukan direktori tingkat atas); tiap berkas rantai tercakup.")

    def _check_5_notes(self) -> None:
        errors = []
        notes = [l.strip() for l in self.sec.get("## Catatan", []) if l.strip()]
        if "## Catatan" in self.sec and (not notes or all(EMPTY_NOTE.match(n.lstrip("- ")) for n in notes)):
            errors.append("Catatan kosong atau basa-basi — hapus heading-nya")
        manual = [m.group(1) for m in map(SC_LINE.match, (l.strip() for l in self.task.splitlines()))
                  if m and not re.search(r"—\s*gugur:", m.group(2)) and is_manual(m.group(2))]
        review = self.taskdir / "REVIEW.md"
        joined = "\n".join(notes)
        if review.is_file():
            _, rbody = split_frontmatter(review.read_text(encoding="utf-8"))
            rlines = section_lines(rbody, "## Temuan")
            for i, line in enumerate(rlines):
                m = OPEN_FINDING.match(line.strip())
                if not m:
                    continue
                block = []
                for nxt in rlines[i + 1:]:
                    if OPEN_FINDING.match(nxt.strip()):
                        break
                    block.append(nxt)
                if re.search(r"^> Status:\s*(PLANNED|DEFERRED)\b", "\n".join(block), re.MULTILINE) \
                        and not re.search(rf"\b{m.group(1)}\b", joined):
                    errors.append(f"temuan {m.group(1)} belum dituntaskan di REVIEW.md tetapi absen dari Catatan")
            for line in section_lines(rbody, "## Cakupan Success Criteria"):
                m = REVIEW_SC_ROW.match(line.strip())
                if m and m.group(2).strip() == "PERLU VERIFIKASI MANUAL" and m.group(1) not in manual:
                    manual.append(m.group(1))
                if m and m.group(2).strip() == "belum terbukti":
                    errors.append(f"{m.group(1)} belum terbukti di REVIEW.md — rantai ini tidak boleh dilaporkan")
        missing = [sc for sc in manual
                   if not re.search(rf"\b{sc}\b.*PERLU VERIFIKASI MANUAL", joined)]
        if missing:
            errors.append("SC QA manual tanpa `PERLU VERIFIKASI MANUAL`: " + ", ".join(missing))
        self._add(5, "Catatan jujur", not errors, "; ".join(errors) or "lolos",
                  "Catat tiap SC ber-`QA manual:` sebagai `SC-{n} — PERLU VERIFIKASI MANUAL: <langkah>`, dan "
                  "tiap temuan REVIEW.md ber-`> Status: PLANNED|DEFERRED` dengan ID-nya (`P2-1 — …`).")

    def _check_6_placeholder(self) -> None:
        hits = sorted(set(PLACEHOLDER.findall(INLINE_CODE.sub("", self.text))))
        self._add(6, "Nol placeholder", not hits, "sisa: " + ", ".join(hits[:5]) if hits else "lolos",
                  "Isi seluruh slot template dan hapus komentar.")

    def format_text(self) -> str:
        return format_report("report validate", self.results).replace(
            "PRECONDITION CHECK: report validate", "REPORT VALIDATION:", 1)

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
