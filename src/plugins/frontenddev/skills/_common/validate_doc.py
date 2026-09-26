#!/usr/bin/env python3
"""Validator mekanis dokumen planning `FLOW.md`, `UI.md`, dan `CONTRACT.md`.

Menegakkan bagian 2 (Aturan Validasi) template masing-masing — `ux-design`,
`ui-design`, dan `contract` `templates/*-template.md` — atas token, sehingga
predikat struktur tidak bergantung pada ingatan penulis maupun reviewer:

- frontmatter wajib (`status` DRAFT|APPROVED, `slug`, `order`, `stack`, `based_on`),
- tepat satu H1 berawalan tetap dan heading seksi bernomor persis urutan template,
- ID berurutan tanpa lompatan (`DD-{n}` FLOW, `ST-{n}` UI, `AC-{n}` CONTRACT),
- nol placeholder di luar blok kode,
- **CONTRACT saja** — keterlacakan dua arah: tiap token `Sumber` Acceptance
  Criteria menunjuk `SC`/`DD`/`ST` yang benar-benar ada, dan tiap `SC-{n}`
  `TASK.md`, tiap `DD-{n}` `FLOW.md`, serta tiap `ST-{n}` `UI.md` dipikul minimal
  satu AC. Inilah "sapuan dua arah" Gate Contract dalam bentuk yang dapat ditagih.

Yang menuntut penilaian (apakah alurnya masuk akal, apakah DTO memenuhi data
demand secara semantik) tetap milik model dan `contract-reviewer`.

Dipanggil penulis dokumen sebelum commit draft, dan oleh `chain.py approve`
sebagai syarat approval.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from precondition_lib import (  # noqa: E402
    FrontmatterError,
    find_repo_root,
    is_manual_cell,
    normalize_taskdir,
    outside_fences,
    parse_sections,
    section_lines,
    split_frontmatter,
    success_criteria,
    task_lane_sections,
    find_placeholders,
    PLACEHOLDER_ACTION,
)

SHA_DATE = re.compile(r"^[0-9a-f]{7,40} \(\d{4}-\d{2}-\d{2}\)$")

SPECS: Dict[str, Dict[str, Any]] = {
    "flow": {
        "file": "FLOW.md", "order": "10", "h1": "# User Flow — ",
        "headings": [
            "## 1. Intent Statement & Scope",
            "## 2. Diagram Alur (Mermaid Flowchart)",
            "## 3. Perjalanan Layar Rinci",
            "## 4. Penanganan Batal & Kembali (Back / Cancel Matrix)",
            "## 5. Kebutuhan Data per Langkah (Data Demands Table)",
            "## 6. Catatan Keputusan Desain & Trade-offs",
        ],
    },
    "ui": {
        "file": "UI.md", "order": "20", "h1": "# UI Design — ",
        "headings": [
            "## 1. Mockup Antarmuka (Layout Mockup ASCII)",
            "## 2. Hierarki Prioritas Informasi (Information Priority)",
            "## 3. Cabang State Tampilan (The 6-State Branches Matrix)",
            "## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)",
            "## 5. Batasan State Scope & Isolasi Komponen",
        ],
    },
    "contract": {
        "file": "CONTRACT.md", "order": "30", "h1": "# Contract — ",
        "headings": [
            "# Architecture",
            "## 1. Intent & Scope Statement",
            "## 2. Data Contract & Endpoints",
            "## 3. Cache Management & Mutation Strategy",
            "## 4. Layer Shape Specification (The 5-Tier Architecture)",
            "## 5. Decisions Not Taken",
            "# Execution",
            "## 1. Files Touched",
            "## 2. Execution Steps",
            "## 3. Verification Commands & Baseline",
            "## 4. Proposed Units Breakdown",
            "## 5. Acceptance Criteria",
        ],
    },
}

DD_ROW = re.compile(r"^\|\s*`?(DD-\d+)`?\s*\|")
ST_HEAD = re.compile(r"^###\s+(ST-\d+)\.\s")
ST_TITLE = re.compile(r"^###\s+(ST-\d+)\.\s+(.*)$")
AC_ROW = re.compile(r"^\|\s*`?(AC-\d+)`?\s*\|(.*)\|\s*$")
TOKEN = re.compile(r"\b(SC|DD|ST)-\d+\b")
FILES_ROW = re.compile(r"^\s*[-*]\s+`(CREATE|MODIFY)`\s+`[^`<>]+`")
# Enam cabang wajib per layar (ui-design Phase 4). Jenis sebuah ST = kata kunci
# yang muncul PALING AWAL di judulnya ("State Error saat Loading" = error).
STATE_KINDS = (
    ("normal", re.compile(r"\b(normal|ready)\b", re.IGNORECASE)),
    ("loading", re.compile(r"\b(loading|skeleton)\b", re.IGNORECASE)),
    ("kosong", re.compile(r"\b(kosong|empty)\b", re.IGNORECASE)),
    ("error", re.compile(r"\b(error|failure|gagal)\b", re.IGNORECASE)),
    ("initial", re.compile(r"\b(initial|idle)\b", re.IGNORECASE)),
    ("stale/mutating", re.compile(r"\b(stale|mutating|optimistic)\b", re.IGNORECASE)),
)
KIND_NAMES = [k for k, _ in STATE_KINDS]


def state_kind(title: str) -> str:
    hits = [(m.start(), kind) for kind, rx in STATE_KINDS for m in [rx.search(title)] if m]
    return min(hits)[1] if hits else ""


def per_screen_problems(heads: List[Tuple[str, str]]) -> List[str]:
    """Blok enam ST berurutan = satu layar (ST-1..6, ST-7..12, ...); tiap blok
    wajib memuat keenam jenis cabang tepat sekali. Urutan di dalam blok bebas."""
    problems: List[str] = []
    for start in range(0, len(heads), 6):
        block = heads[start:start + 6]
        label = f"layar {start // 6 + 1} ({block[0][0]}..{block[-1][0]})"
        seen: Dict[str, List[str]] = {}
        for sid, title in block:
            kind = state_kind(title)
            if not kind:
                problems.append(f"{label}: judul `{sid}` tidak menyebut jenis cabang ({', '.join(KIND_NAMES)})")
                continue
            seen.setdefault(kind, []).append(sid)
        problems += [f"{label}: cabang `{k}` ganda ({', '.join(v)})" for k, v in seen.items() if len(v) > 1]
        missing = [k for k in KIND_NAMES if k not in seen]
        if missing:
            problems.append(f"{label}: cabang hilang — {', '.join(missing)}")
    return problems


def body_after(heading: str, body: str) -> List[str]:
    return section_lines(body, heading)


def sequential(ids: List[str], prefix: str) -> str:
    expected = [f"{prefix}-{i}" for i in range(1, len(ids) + 1)]
    return "" if ids == expected else f"penomoran {prefix} {ids} bukan seri berurutan dari `{prefix}-1`"


class DocValidator:
    def __init__(self, kind: str, taskdir: str, root: Optional[Path] = None):
        self.kind = kind
        self.spec = SPECS[kind]
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.taskdir = self.root / self.taskdir_rel
        self.path = self.taskdir / self.spec["file"]
        self.results: List[Dict[str, Any]] = []

    def _add(self, cid: str, name: str, problems: List[str], ok_summary: str, action: str) -> None:
        self.results.append({"id": cid, "name": name,
                             "status": "FAIL" if problems else "PASS",
                             "summary": f"{len(problems)} pelanggaran" if problems else ok_summary,
                             "details": problems, "action": action if problems else ""})

    def run(self) -> bool:
        if not self.path.is_file():
            self._add("S", "Berkas ada", [f"`{self.path.relative_to(self.root)}` tidak ada"], "",
                      "Tulis dokumen dari templat skill pemiliknya lebih dulu.")
            return False
        text = self.path.read_text(encoding="utf-8")
        try:
            self.fm, self.body = split_frontmatter(text, strict=True)
        except FrontmatterError as exc:
            self._add("S", "Frontmatter", [str(exc)], "", "Buka dan tutup frontmatter dengan `---`.")
            return False
        self._check_frontmatter()
        self._check_structure()
        self._check_placeholders()
        if self.kind == "flow":
            self._check_ids("DD", self.dd_ids())
        elif self.kind == "ui":
            ids = self.st_ids()
            self._check_ids("ST", ids)
        else:
            self._check_contract()
        return not any(r["status"] == "FAIL" for r in self.results)

    # ------------------------------------------------------------------ id readers

    def dd_ids(self, body: Optional[str] = None) -> List[str]:
        lines = section_lines(body if body is not None else self.body, self.spec["headings"][4]
                              if self.kind == "flow" else SPECS["flow"]["headings"][4])
        return [m.group(1) for m in (DD_ROW.match(l.strip()) for l in lines) if m]

    def st_ids(self, body: Optional[str] = None) -> List[str]:
        heading = SPECS["ui"]["headings"][2]
        lines = section_lines(body if body is not None else self.body, heading)
        return [m.group(1) for m in (ST_HEAD.match(l.strip()) for l in lines) if m]

    def st_heads(self) -> List[Tuple[str, str]]:
        lines = section_lines(self.body, SPECS["ui"]["headings"][2])
        return [(m.group(1), m.group(2)) for m in (ST_TITLE.match(l.strip()) for l in lines) if m]

    # ------------------------------------------------------------------ checks

    def _check_frontmatter(self) -> None:
        problems = []
        status = str(self.fm.get("status", "")).strip()
        if status not in ("DRAFT", "APPROVED"):
            problems.append(f"`status: {status or '(kosong)'}` — sah hanya DRAFT (ditulis penulis) "
                            "atau APPROVED (ditulis `chain.py approve`)")
        for key in ("slug", "stack"):
            if not str(self.fm.get(key, "")).strip():
                problems.append(f"field `{key}` kosong")
        if str(self.fm.get("order", "")).strip() != self.spec["order"]:
            problems.append(f"`order` wajib `{self.spec['order']}`")
        based = str(self.fm.get("based_on", "")).strip()
        if not SHA_DATE.match(based):
            problems.append(f"`based_on: {based or '(kosong)'}` tidak berpola `<sha 7 digit> (YYYY-MM-DD)`")
        if self.kind == "contract":
            task = self.taskdir / "TASK.md"
            _, task_sections = task_lane_sections(task)
            mine = parse_sections(self.fm.get("sections", ""))
            if sorted(mine) != sorted(task_sections):
                problems.append(f"`sections` {mine} ≠ `sections` TASK.md {task_sections}")
        self._add("F", "Frontmatter", problems, "field wajib lengkap",
                  "Samakan frontmatter dengan bagian 1 template; `based_on` dari `git rev-parse --short HEAD`.")

    def _check_structure(self) -> None:
        problems = []
        lines = self.body.splitlines()
        code = outside_fences(lines)
        h1 = [l for l in code if l.startswith("# ") and l.strip() not in ("# Architecture", "# Execution")]
        if len(h1) != 1 or not h1[0].startswith(self.spec["h1"]):
            problems.append(f"wajib tepat satu H1 berawalan `{self.spec['h1'].strip()}` (ditemukan {len(h1)})")
        headings = [l.strip() for l in code if re.match(r"^#{1,2} ", l)
                    and l.strip() not in [x.strip() for x in h1]]
        expected = self.spec["headings"]
        if headings != expected:
            missing = [h for h in expected if h not in headings]
            extra = [h for h in headings if h not in expected]
            if missing:
                problems.append("heading hilang: " + "; ".join(missing))
            if extra:
                problems.append("heading di luar template: " + "; ".join(extra))
            if not missing and not extra:
                problems.append("urutan heading tidak sama dengan template")
        if self.kind == "flow":
            diagram = "\n".join(section_lines(self.body, expected[1]))
            if "```mermaid" not in diagram:
                problems.append("seksi 2 tanpa blok ```mermaid")
            screens = [l for l in section_lines(self.body, expected[2]) if l.startswith("### Screen")]
            if not screens:
                problems.append("seksi 3 tanpa satu pun `### Screen <n>: <nama>`")
        if self.kind == "ui":
            mock = "\n".join(section_lines(self.body, expected[0]))
            if "```" not in mock:
                problems.append("seksi 1 tanpa blok mockup berpagar ```")
        self._add("S", "Struktur heading", problems, f"{len(expected)} heading sesuai template",
                  "Salin heading persis dari bagian 1 template; dilarang menambah, membuang, atau menomori ulang.")

    def _check_placeholders(self) -> None:
        problems = []
        for line in outside_fences(self.body.splitlines()):
            if find_placeholders(line):
                problems.append(line.strip()[:90])
        self._add("B", "Placeholder", problems, "nol placeholder",
                  PLACEHOLDER_ACTION + " Isi dari bukti repo atau keputusan user.")

    def _check_ids(self, prefix: str, ids: List[str]) -> None:
        problems = []
        if not ids:
            problems.append(f"nol `{prefix}-{{n}}` — seksi ID wajib memuat minimal satu baris")
        else:
            seq = sequential(ids, prefix)
            if seq:
                problems.append(seq)
        if prefix == "ST" and ids:
            problems += per_screen_problems(self.st_heads())
        self._add("I", f"Penomoran {prefix}", problems, f"{len(ids)} {prefix} berurutan",
                  f"Nomori `{prefix}-{{n}}` berurutan dari `{prefix}-1` tanpa lompatan"
                  + ("; tiap layar tepat enam ST (ST-1..6, ST-7..12, ...), satu per cabang "
                     "normal, loading, kosong, error, initial, stale/mutating." if prefix == "ST" else "."))

    def _check_contract(self) -> None:
        # Files Touched
        files = [l for l in section_lines(self.body, "## 1. Files Touched") if FILES_ROW.match(l)]
        self._add("E", "Files Touched", [] if files else ["`# Execution ## 1. Files Touched` kosong atau "
                                                          "tidak berpola `- \\`CREATE|MODIFY\\` \\`<path>\\``"],
                  f"{len(files)} berkas", "Tulis satu butir per berkas: `- `CREATE` `path``.")
        # Acceptance Criteria
        rows = []
        for line in section_lines(self.body, "## 5. Acceptance Criteria"):
            m = AC_ROW.match(line.strip())
            if m:
                cells = [c.strip() for c in m.group(2).split("|")]
                rows.append((m.group(1), cells))
        problems: List[str] = []
        ids = [r[0] for r in rows]
        if not ids:
            problems.append("tabel `AC-{n} | Skenario | Cara verifikasi | Sumber` kosong")
        else:
            seq = sequential(ids, "AC")
            if seq:
                problems.append(seq)
        sc = set(success_criteria(self.taskdir / "TASK.md"))
        _, sections = task_lane_sections(self.taskdir / "TASK.md")
        dd: Set[str] = set()
        st: Set[str] = set()
        if "flow" in sections:
            flow = self.taskdir / "FLOW.md"
            dd = set(self.dd_ids(split_frontmatter(flow.read_text(encoding="utf-8"))[1])) if flow.is_file() else set()
        if "ui" in sections:
            ui = self.taskdir / "UI.md"
            st = set(self.st_ids(split_frontmatter(ui.read_text(encoding="utf-8"))[1])) if ui.is_file() else set()
        known = {"SC": sc, "DD": dd, "ST": st}
        borne: Set[str] = set()
        for ac, cells in rows:
            if len(cells) < 3:
                problems.append(f"`{ac}`: baris kurang kolom (wajib Skenario | Cara verifikasi | Sumber)")
                continue
            how, source = cells[1].lower(), cells[-1]
            if "test otomatis" not in how and not is_manual_cell(cells[1]):
                problems.append(f"`{ac}`: Cara verifikasi bukan `test otomatis` atau `QA manual: <langkah>`")
            tokens = [m.group(0) for m in TOKEN.finditer(source)]
            if not tokens and source.strip("` ") not in ("—", "-"):
                problems.append(f"`{ac}`: Sumber `{source}` tanpa token SC/DD/ST dan bukan `—`")
            for t in tokens:
                if t not in known[t.split("-")[0]]:
                    problems.append(f"`{ac}`: Sumber menunjuk `{t}` yang tidak ada di dokumen hulunya")
                borne.add(t)
        for label, pool in (("SC", sc), ("DD", dd), ("ST", st)):
            for t in sorted(pool - borne, key=lambda x: int(x.split("-")[1])):
                problems.append(f"`{t}` tidak dipikul satu pun AC — "
                                + ("janji akar tidak direncanakan" if label == "SC"
                                   else "sapuan mundur bolong: kebutuhan hulu tanpa kriteria penerimaan"))
        if not sc:
            problems.append("`TASK.md` tanpa butir `SC-{n}` terbaca — keterlacakan akar tidak dapat dinilai")
        self._add("C", "Acceptance Criteria & keterlacakan", problems,
                  f"{len(ids)} AC; {len(sc)} SC, {len(dd)} DD, {len(st)} ST terpikul",
                  "Tambahkan AC yang memikul token yang yatim, atau perbaiki token Sumber yang salah; "
                  "SC/DD/ST tidak dihapus dari hulu demi meloloskan kontrak.")

    # ------------------------------------------------------------------ output

    def format_text(self) -> str:
        failed = [r for r in self.results if r["status"] == "FAIL"]
        lines = [f"DOC VALIDATION: {self.spec['file']} [{'FAIL' if failed else 'PASS'}] "
                 f"({len(self.results) - len(failed)}/{len(self.results)} passed)"]
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<36} : {r['status']} ({r['summary']})")
            for d in r["details"][:12]:
                lines.append(f"      - {d}")
            if r["action"]:
                lines.append(f"    * Tindakan: {r['action']}")
        return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validator FLOW.md / UI.md / CONTRACT.md")
    parser.add_argument("--kind", required=True, choices=list(SPECS))
    parser.add_argument("--taskdir", required=True)
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    v = DocValidator(args.kind, args.taskdir, Path(args.root) if args.root else None)
    ok = v.run()
    if args.json:
        print(json.dumps({"status": "PASS" if ok else "FAIL", "checks": v.results}, indent=2))
    else:
        print(v.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
