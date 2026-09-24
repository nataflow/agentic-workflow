#!/usr/bin/env python3
"""REVIEW.md Validator — review penutup `frontenddev:architect`.

Menegakkan bagian 2 `templates/review-template.md` atas token: frontmatter,
urutan heading, satu baris vonis per `SC-{n}` `TASK.md` dan per `AC-{n}`
`CONTRACT.md`, hitungan temuan sama dengan frontmatter, dan **verdict yang
diturunkan mekanis** dari isinya — bukan dipilih reviewer:

- `BLOCKED` ⇔ P1 > 0, atau satu SC `belum terbukti`, atau galat baru di verifikasi penutup;
- selain itu `WARNING` ⇔ P2 > 0 atau satu AC `belum terbukti`;
- selain itu `PASS`.

Dipakai `architect` sebelum commit `REVIEW.md`, dan `frontenddev:report` sebagai
prasyarat — janji akar yang belum terbukti tidak pernah sampai ke laporan.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    FrontmatterError,
    find_repo_root,
    normalize_taskdir,
    section_lines,
    split_frontmatter,
    success_criteria,
    task_root_sha,
)

HEADINGS = ["## Summary", "## Verifikasi Penutup", "## Cakupan Success Criteria",
            "## Cakupan Acceptance Criteria", "## Temuan", "## Done Criteria DITUNDA",
            "## Umpan balik profil", "## 9 Dimensi"]
ROW = re.compile(r"^\|\s*`?((?:SC|AC)-\d+)`?\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$")
FINDING = re.compile(r"^### \[(P[123])-(\d+)\]")
EVIDENCE = re.compile(r"`[^`]+:\d+`|`[^`]+`")
SC_VERDICTS = ("terbukti", "belum terbukti", "PERLU VERIFIKASI MANUAL")
AC_VERDICTS = ("terbukti", "belum terbukti", "QA manual")
AC_ROW = re.compile(r"^\|\s*`?(AC-\d+)`?\s*\|")


class ReviewValidator:
    def __init__(self, taskdir: str, root: Optional[Path] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.taskdir = self.root / self.taskdir_rel
        self.path = self.taskdir / "REVIEW.md"
        self.results: List[Dict[str, Any]] = []
        self.derived = ""

    def _add(self, cid: str, name: str, problems: List[str], ok: str, action: str) -> None:
        self.results.append({"id": cid, "name": name, "status": "FAIL" if problems else "PASS",
                             "summary": f"{len(problems)} pelanggaran" if problems else ok,
                             "details": problems, "action": action if problems else ""})

    def rows(self, heading: str) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        self.dups = getattr(self, "dups", [])
        for line in section_lines(self.body, heading):
            m = ROW.match(line.strip())
            if m:
                if m.group(1) in out:
                    self.dups.append(m.group(1))
                    continue
                out[m.group(1)] = [m.group(2).strip(), m.group(3).strip()]
        return out

    def run(self) -> bool:
        if not self.path.is_file():
            self._add("S", "REVIEW.md ada", ["`REVIEW.md` tidak ada di taskdir"], "",
                      "Dispatch `code-reviewer` lewat `dispatcher/reviewer.md`.")
            return False
        try:
            self.fm, self.body = split_frontmatter(self.path.read_text(encoding="utf-8"), strict=True)
        except FrontmatterError as exc:
            self._add("S", "Frontmatter", [str(exc)], "", "Tulis ulang frontmatter persis template.")
            return False
        self._check_frontmatter()
        self._check_structure()
        sc_blocked = self._check_sc()
        ac_open = self._check_ac()
        counts = self._check_findings()
        red = self._verification_red()
        self._check_verdict(counts, sc_blocked, ac_open, red)
        return not any(r["status"] == "FAIL" for r in self.results)

    def _check_frontmatter(self) -> None:
        p = []
        if self.fm.get("artifact") != "REVIEW":
            p.append("`artifact` wajib `REVIEW`")
        if self.fm.get("verdict") not in ("PASS", "WARNING", "BLOCKED"):
            p.append(f"`verdict: {self.fm.get('verdict', '')}` di luar PASS|WARNING|BLOCKED")
        for k in ("p1", "p2", "p3"):
            if not str(self.fm.get(k, "")).strip().isdigit():
                p.append(f"`{k}` bukan bilangan")
        base = str(self.fm.get("base", "")).strip()
        root_sha = task_root_sha(self.root, self.taskdir_rel)
        if not re.fullmatch(r"[0-9a-f]{7,40}", base) or not root_sha.startswith(base):
            p.append(f"`base: {base or '(kosong)'}` bukan commit akar TASK.md ({root_sha[:7] or 'tak terbaca'})")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(self.fm.get("reviewed_at", "")).strip()):
            p.append("`reviewed_at` bukan YYYY-MM-DD")
        self._add("F", "Frontmatter", p, "lengkap", "Samakan dengan bagian 1 template.")

    def _check_structure(self) -> None:
        p = []
        lines = self.body.splitlines()
        h1 = [l for l in lines if l.startswith("# ")]
        if len(h1) != 1 or not h1[0].startswith("# Review Findings — "):
            p.append("wajib tepat satu H1 `# Review Findings — <slug>`")
        h2 = [l.strip() for l in lines if l.startswith("## ")]
        if h2 != HEADINGS:
            p.append(f"heading {h2} ≠ {HEADINGS}")
        dims = [l for l in section_lines(self.body, "## 9 Dimensi") if re.match(r"^\|\s*\d\s*\|", l.strip())]
        if len(dims) != 9:
            p.append(f"`## 9 Dimensi` memuat {len(dims)} baris, wajib 9")
        self._add("S", "Struktur", p, "8 heading + 9 dimensi", "Salin heading persis template.")

    def _check_sc(self) -> bool:
        sc = success_criteria(self.taskdir / "TASK.md")
        rows = self.rows("## Cakupan Success Criteria")
        p, blocked = [], False
        for s_id, line in sc.items():
            if s_id not in rows:
                p.append(f"`{s_id}` tanpa baris vonis")
                continue
            verdict, evidence = rows[s_id][0], rows[s_id][1]
            if verdict not in SC_VERDICTS:
                p.append(f"`{s_id}` vonis `{verdict}` di luar {SC_VERDICTS}")
            if verdict == "terbukti" and not EVIDENCE.search(evidence):
                p.append(f"`{s_id}` terbukti tanpa bukti ber-backtick (`file:baris` atau perintah)")
            if verdict == "PERLU VERIFIKASI MANUAL" and "QA manual:" not in line:
                p.append(f"`{s_id}` bukan SC ber-alat-ukur `QA manual:` — wajib divonis terbukti/belum")
            if verdict == "belum terbukti":
                blocked = True
        ghosts = sorted(set(k for k in rows if k.startswith("SC-")) - set(sc))
        p += [f"`{g}` tidak ada di TASK.md" for g in ghosts]
        p += [f"`{d}` divonis lebih dari sekali — satu baris per SC" for d in self.dups if d.startswith("SC-")]
        if not sc:
            p.append("`TASK.md` tanpa butir SC terbaca")
        self._add("SC", "Cakupan Success Criteria", p, f"{len(sc)} SC divonis",
                  "Satu baris per SC-{n} TASK.md; vonis dari bukti, bukan dari perkiraan.")
        return blocked

    def _check_ac(self) -> bool:
        contract = self.taskdir / "CONTRACT.md"
        rows = self.rows("## Cakupan Acceptance Criteria")
        if not contract.is_file():
            p = [] if not rows else ["lane tanpa kontrak tetapi tabel AC terisi"]
            self._add("AC", "Cakupan Acceptance Criteria", p, "lane MINOR — tanpa AC",
                      "Kosongkan tabel AC pada lane MINOR.")
            return False
        _, cbody = split_frontmatter(contract.read_text(encoding="utf-8"))
        acs = [m.group(1) for m in (AC_ROW.match(l.strip()) for l in
                                    section_lines(cbody, "## 5. Acceptance Criteria")) if m]
        p, open_ = [], False
        for ac in acs:
            if ac not in rows:
                p.append(f"`{ac}` tanpa baris vonis")
                continue
            verdict = rows[ac][0]
            if verdict not in AC_VERDICTS:
                p.append(f"`{ac}` vonis `{verdict}` di luar {AC_VERDICTS}")
            if verdict == "belum terbukti":
                open_ = True
        p += [f"`{g}` tidak ada di CONTRACT.md" for g in sorted(set(k for k in rows if k.startswith("AC-")) - set(acs))]
        p += [f"`{d}` divonis lebih dari sekali — satu baris per AC" for d in self.dups if d.startswith("AC-")]
        self._add("AC", "Cakupan Acceptance Criteria", p, f"{len(acs)} AC divonis",
                  "Satu baris per AC-{n} CONTRACT.md.")
        return open_

    def _check_findings(self) -> Dict[str, int]:
        lines = section_lines(self.body, "## Temuan")
        found: Dict[str, List[int]] = {"P1": [], "P2": [], "P3": []}
        p = []
        for i, line in enumerate(lines):
            m = FINDING.match(line.strip())
            if not m:
                continue
            found[m.group(1)].append(int(m.group(2)))
            window = "\n".join(lines[i + 1:i + 4])
            if "> Status:" not in window:
                p.append(f"`{m.group(1)}-{m.group(2)}` tanpa baris `> Status:`")
        counts = {k: len(v) for k, v in found.items()}
        for k, nums in found.items():
            if nums != list(range(1, len(nums) + 1)):
                p.append(f"nomor {k} {nums} tidak berurutan")
            declared = str(self.fm.get(k.lower(), "")).strip()
            if declared.isdigit() and int(declared) != len(nums):
                p.append(f"`{k.lower()}: {declared}` ≠ {len(nums)} temuan `{k}` di badan")
        self._add("T", "Temuan & hitungan", p, f"P1 {counts['P1']}, P2 {counts['P2']}, P3 {counts['P3']}",
                  "Samakan hitungan frontmatter dengan temuan ber-ID di badan.")
        return counts

    def _verification_red(self) -> bool:
        """Merah bila satu baris MERAH/TIMEOUT atau bergalat baru; tabel tak sah juga FAIL.

        Tabel kosong, hasil di luar enum, atau kolom galat non-angka tidak pernah
        dibaca sebagai hijau — vonis penutup tanpa bukti verifikasi adalah vonis palsu.
        """
        rows, p, red = 0, [], False
        for line in section_lines(self.body, "## Verifikasi Penutup"):
            raw = line.strip()
            if not raw.startswith("|") or set(raw.replace("|", "").strip()) <= set("-: "):
                continue
            cells = [c.strip() for c in raw.strip("|").split("|")]
            if len(cells) < 3 or cells[0].lower() == "perintah":
                continue
            rows += 1
            result, new = cells[1].upper(), cells[2]
            if result not in ("HIJAU", "MERAH", "TIMEOUT"):
                p.append(f"hasil `{cells[1]}` di luar HIJAU|MERAH|TIMEOUT ({cells[0]})")
            if not new.isdigit():
                p.append(f"galat baru `{new}` bukan bilangan ({cells[0]})")
            # Merah warisan baseline (galat baru 0) bukan kegagalan rantai ini; TIMEOUT tetap merah.
            if result == "TIMEOUT" or (new.isdigit() and int(new) > 0) or not new.isdigit():
                red = True
        if not rows:
            p.append("tabel `## Verifikasi Penutup` kosong — penutup tanpa bukti verifikasi")
            red = True
        self._add("VP", "Verifikasi penutup", p, f"{rows} perintah",
                  "Salin hasil `.explore/closing-verification.md` apa adanya: HIJAU|MERAH|TIMEOUT dan jumlah galat baru.")
        return red

    def _check_verdict(self, counts: Dict[str, int], sc_blocked: bool, ac_open: bool, red: bool) -> None:
        if counts["P1"] or sc_blocked or red:
            self.derived = "BLOCKED"
        elif counts["P2"] or ac_open:
            self.derived = "WARNING"
        else:
            self.derived = "PASS"
        actual = self.fm.get("verdict")
        p = [] if actual == self.derived else [f"`verdict: {actual}` ≠ turunan mekanis `{self.derived}`"]
        self._add("V", "Verdict turunan", p, self.derived,
                  "Verdict tidak dipilih: BLOCKED ⇔ P1/SC belum terbukti/verifikasi merah; "
                  "WARNING ⇔ P2/AC belum terbukti; selain itu PASS.")

    def format_text(self) -> str:
        failed = [r for r in self.results if r["status"] == "FAIL"]
        lines = [f"REVIEW VALIDATION: [{'FAIL' if failed else 'PASS'}] "
                 f"({len(self.results) - len(failed)}/{len(self.results)} passed) — verdict turunan "
                 f"{self.derived or '-'}"]
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<30} : {r['status']} ({r['summary']})")
            for d in r["details"][:10]:
                lines.append(f"      - {d}")
            if r["action"]:
                lines.append(f"    * Tindakan: {r['action']}")
        return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="REVIEW.md validator")
    parser.add_argument("--taskdir", required=True)
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    v = ReviewValidator(args.taskdir, Path(args.root) if args.root else None)
    ok = v.run()
    print(json.dumps({"status": "PASS" if ok else "FAIL", "derived_verdict": v.derived,
                      "checks": v.results}, indent=2) if args.json else v.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
