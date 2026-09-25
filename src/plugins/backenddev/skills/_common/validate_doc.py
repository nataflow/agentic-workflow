#!/usr/bin/env python3
"""Validator mekanis self-test `TASK.md`, `BRD.md`, dan `PRD.md` backenddev.

  validate_doc.py --kind task --taskdir <taskdir> [--fresh] [--finding-source <path>] [--json]
  validate_doc.py --kind brd  --taskdir <taskdir> [--json]
  validate_doc.py --kind prd  --taskdir <taskdir> [--json]

Menagih butir mekanis bagian self-test ketiga template — `task/templates/task-template.md`
bagian 2, `business-analysis/templates/brd-template.md` `## Self-test struktural`, dan
`system-analysis/templates/prd-template.md` `## Self-test pra-reviewer` — atas token, sehingga
puluhan `Grep` tangan per dokumen menjadi satu panggilan. Butir yang menuntut penilaian
dicetak `MANUAL` beserta rujukan predikatnya dan tidak memengaruhi exit code; butir heuristik
yang rawan positif palsu dicetak `WARN`.

Exit 0: nol FAIL. Exit 1: minimal satu FAIL. Exit 2: argumen salah atau dokumen tidak ada.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`precondition_lib.py` (frontmatter, fence, taskdir) di direktori yang sama.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from precondition_lib import (  # noqa: E402
    VALID_CHAINS,
    FrontmatterError,
    find_repo_root,
    iter_outside_fences,
    normalize_text,
    resolve_taskdir,
    split_frontmatter,
)

# --- konstanta kanonik (salinan penegak; rumahnya template masing-masing) ---------------------

TASK_LANES = ("PRD_CONVERSION", "DIRECT_BRIEF", "DEFECT_RCA", "EXEC_BRIEF")
NON_PLANNING_LANES = ("DEFECT_RCA", "EXEC_BRIEF")
TASK_RISKS = ("BREAKING", "MAJOR", "MINOR", "-")
# analyst/references/chain-rules.md bagian 1.3 (lane terminal) dan 1.4 (pasangan risk, chain).
CHAIN_TERMINAL_LANES = {"BRD_PRD_BRIEF": "PRD_CONVERSION", "PRD_BRIEF": "PRD_CONVERSION", "BRIEF": "DIRECT_BRIEF"}
RISK_CHAINS = {"BREAKING": ("BRD_PRD_BRIEF", "PRD_BRIEF"), "MAJOR": ("BRD_PRD_BRIEF", "PRD_BRIEF", "BRIEF"),
               "MINOR": ("BRIEF",)}
CHAIN_HOPS = {"BRD_PRD_BRIEF": ["BRD", "PRD", "BRIEF"], "PRD_BRIEF": ["PRD", "BRIEF"], "BRIEF": ["BRIEF"]}

BRD_SECTIONS = ["Problem", "Actors", "Current state", "Target state", "Business rules", "Edge cases",
                "Business metrics", "Out of scope", "Open questions"]
PRD_SECTIONS = ["API contract", "Status lifecycle", "Validation policy", "Permission & scope", "Impact map",
                "Migration requirements", "Task breakdown", "Acceptance criteria", "Open questions"]
EC_CATEGORIES = ("data-hilang", "duplikasi", "in-flight", "timeout", "status-eksternal")
ACTOR_KINDS = ("primer", "approver", "sistem", "terlarang")
FREQUENCIES = ("tiap transaksi", "beban puncak", "insidental")
LEAK_PRONE_DIMENSIONS = (2, 4, 11, 13, 16)
CONTRACT_PILLARS = ("API contract", "Status lifecycle", "Validation policy", "Permission & scope")
ASSUMPTION_TARGETS = CONTRACT_PILLARS + ("Task breakdown",)

PLACEHOLDER_WORDS = re.compile(r"\bTBD\b|\bTODO\b|diisi nanti", re.IGNORECASE)
TEMPLATE_SLOT = re.compile(r"<[A-Za-z][^<>\n]{0,80}>")
INLINE_CODE = re.compile(r"`[^`\n]*`")
FILE_LINE = re.compile(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]+):(\d+)")
SOURCE_FILE = re.compile(r"\b[\w./-]+\.(?:go|java|kt|kts|scala|ts|tsx|js|jsx|mjs|py|rs|php|rb|cs)\b")
TEST_CLASS = re.compile(r"\bTest[A-Z]\w*|\b[A-Z]\w*(?:Test|Tests|Spec|IT)\b|\b\w+_test\b|\b\w+\.(?:spec|test)\b")
SUBJECTIVE_MEASURES = re.compile(r"review manual|dinilai layak|dicek manual|diuji manual", re.IGNORECASE)


class Doc:
    """Dokumen markdown: frontmatter, H1, dan seksi H2 beserta baris bernomornya (di luar fence)."""

    def __init__(self, path: Path):
        self.path = path
        self.text = normalize_text(path.read_text(encoding="utf-8"))
        try:
            self.fm, _ = split_frontmatter(self.text)
            self.fm_error = ""
        except FrontmatterError as exc:
            self.fm, self.fm_error = {}, str(exc)
        self.lines: List[Tuple[int, str]] = list(iter_outside_fences(self.text))
        raw = self.text.split("\n")
        body_start = 0          # nomor baris (1-based) pagar penutup frontmatter
        if raw and raw[0].strip() == "---":
            body_start = next((i + 1 for i in range(1, len(raw)) if raw[i].strip() == "---"), 0)
        self.body = [(n, l) for n, l in self.lines if n > body_start]
        self.h1 = [l for _, l in self.body if re.match(r"^# +\S", l)]
        self.h2: List[str] = []
        self.sections: Dict[str, List[Tuple[int, str]]] = {}
        current: Optional[str] = None
        for n, line in self.body:
            m = re.match(r"^## +(.+?)\s*$", line)
            if m:
                current = m.group(1)
                self.h2.append(current)
                self.sections.setdefault(current, [])
                continue
            if current is not None:
                self.sections[current].append((n, line))

    def section(self, name: str) -> List[Tuple[int, str]]:
        return self.sections.get(name, [])

    def section_text(self, name: str) -> str:
        return "\n".join(l for _, l in self.section(name))

    def raw_lines(self) -> List[str]:
        """Seluruh baris berkas (termasuk fence) — untuk placeholder yang dilarang di mana pun."""
        return self.text.split("\n")


def table_rows(lines: Sequence[Tuple[int, str]]) -> List[List[Dict[str, str]]]:
    """Tabel markdown di `lines`: list tabel, tiap tabel list baris {header: sel}."""
    tables: List[List[Dict[str, str]]] = []
    header: Optional[List[str]] = None
    rows: List[Dict[str, str]] = []

    def cells(line: str) -> List[str]:
        inner = line.strip()
        inner = inner[1:] if inner.startswith("|") else inner
        inner = inner[:-1] if inner.endswith("|") else inner
        return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", inner)]

    for _, line in list(lines) + [(0, "")]:
        if line.strip().startswith("|"):
            row = cells(line)
            if header is None:
                header = row
            elif all(re.fullmatch(r":?-{3,}:?", c) for c in row if c):
                continue
            else:
                rows.append({h: (row[i] if i < len(row) else "") for i, h in enumerate(header)})
            continue
        if header is not None:
            tables.append(rows)
        header, rows = None, []
    return tables


def ids(text: str, prefix: str) -> List[int]:
    return [int(n) for n in re.findall(rf"\b{prefix}-(\d+)\b", text)]


def sequence_problem(nums: Sequence[int], prefix: str, allow_zero: bool = False) -> str:
    """'' bila `nums` = 1..n tanpa lompatan dan ganda (atau tepat [0] bila `allow_zero`)."""
    if allow_zero and list(nums) == [0]:
        return ""
    if not nums:
        return f"tidak ada baris `{prefix}-{{n}}`" + (f" maupun `{prefix}-0`" if allow_zero else "")
    dup = sorted({n for n in nums if list(nums).count(n) > 1})
    if dup:
        return f"nomor ganda: {', '.join(f'{prefix}-{n}' for n in dup)}"
    if 0 in nums:
        return f"`{prefix}-0` hanya sah sebagai satu-satunya baris"
    expect = list(range(1, len(nums) + 1))
    if sorted(nums) != expect or list(nums) != sorted(nums):
        return f"penomoran wajib urut {prefix}-1..{prefix}-{len(nums)} tanpa lompatan (menemukan: " \
               f"{', '.join(f'{prefix}-{n}' for n in nums)})"
    return ""


def placeholder_hits(doc: Doc, slots: bool) -> List[str]:
    """Kata placeholder di mana pun (di luar fence); slot `<...>` hanya di luar inline code."""
    hits: List[str] = []
    for n, line in doc.lines:
        if PLACEHOLDER_WORDS.search(line):
            hits.append(f"baris {n}: {PLACEHOLDER_WORDS.search(line).group(0)}")
        elif slots:
            m = TEMPLATE_SLOT.search(INLINE_CODE.sub("", line))
            if m and not line.lstrip().startswith("<!--"):
                hits.append(f"baris {n}: {m.group(0)}")
    return hits


def success_criteria_ids(task: Optional[Doc]) -> Set[int]:
    if not task:
        return set()
    return {int(n) for n in re.findall(r"\*\*SC-(\d+)\*\*", task.section_text("Success Criteria"))}


# --- validator ---------------------------------------------------------------------------------

class Validator:
    def __init__(self, kind: str, taskdir: Path, root: Path, fresh: bool = False,
                 finding_source: Optional[str] = None):
        self.kind, self.taskdir, self.root = kind, taskdir, root
        self.fresh, self.finding_source = fresh, (finding_source or "").strip() or None
        self.results: List[Dict[str, Any]] = []
        name = {"task": "TASK.md", "brd": "BRD.md", "prd": "PRD.md"}[kind]
        self.doc = Doc(taskdir / name)
        task_path = taskdir / "TASK.md"
        self.task = Doc(task_path) if kind != "task" and task_path.is_file() else None
        brd_path = taskdir / "BRD.md"
        self.brd = Doc(brd_path) if kind == "prd" and brd_path.is_file() else None

    def add(self, cid: str, name: str, problems: Sequence[str] = (), status: Optional[str] = None,
            note: str = "") -> None:
        status = status or ("FAIL" if problems else "PASS")
        self.results.append({"id": cid, "name": name, "status": status,
                             "summary": "; ".join(problems) if problems else note})

    def manual(self, cid: str, name: str, ref: str) -> None:
        self.add(cid, name, status="MANUAL", note=f"nilai sendiri — {ref}")

    # ------------------------------------------------------------------ TASK

    def run_task(self) -> None:
        d, fm = self.doc, self.doc.fm
        lane = (fm.get("lane") or "").upper()
        planning = lane not in NON_PLANNING_LANES

        p: List[str] = []
        if d.fm_error:
            p.append(d.fm_error)
        if (fm.get("status") or "") != "ACTIVE":
            p.append(f"`status: {fm.get('status') or '(kosong)'}` — wajib `ACTIVE`")
        if lane not in TASK_LANES:
            p.append(f"`lane: {fm.get('lane') or '(kosong)'}` di luar {' | '.join(TASK_LANES)}")
        if (fm.get("risk") or "").upper() not in TASK_RISKS:
            p.append(f"`risk: {fm.get('risk') or '(kosong)'}` di luar {' | '.join(TASK_RISKS)}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fm.get("created") or ""):
            p.append("`created` wajib YYYY-MM-DD")
        if len(d.h1) != 1:
            p.append(f"H1 wajib tepat satu (menemukan {len(d.h1)})")
        heads = [h for h in d.h2 if h != "Counters"]
        if "Counters" in d.h2 and d.h2[-1] != "Counters":
            p.append("`## Counters` wajib heading terakhir")
        want = (["Chain"] if planning else []) + ["Description", "Success Criteria", "Out of Scope"]
        if heads != want:
            p.append(f"heading wajib persis {' → '.join(want)} (menemukan: {' → '.join(heads) or '—'})")
        self.add("T1", "Struktur & frontmatter", p)

        sc_lines = [l for _, l in d.section("Success Criteria") if re.match(r"^\s*- \[[ xX]\]", l)]
        nums, p = [], []
        for line in sc_lines:
            m = re.match(r"^\s*- \[[ xX]\] (?:~~)?\*\*SC-(\d+)\*\*", line)
            if not m:
                p.append(f"butir tanpa ID `**SC-{{n}}**`: {line.strip()[:60]}")
            else:
                nums.append(int(m.group(1)))
        seq = sequence_problem(nums, "SC")
        if seq:
            p.append(seq)
        if not 1 <= len(nums) <= 7:
            p.append(f"jumlah butir wajib 1–7 (menemukan {len(nums)})")
        self.add("T2", "Penomoran SC-{n}", p)

        p = []
        for line in sc_lines:
            if "~~" in line:
                continue
            sc = (re.search(r"SC-\d+", line) or [None])[0] or line.strip()[:30]
            if "— verifikasi:" not in line:
                p.append(f"{sc}: literal `— verifikasi:` tidak ada")
                continue
            measure = line.split("— verifikasi:", 1)[1]
            bad = re.findall(r"\bBRD\.md\b|\bPRD\.md\b|\bAC-\d+\b", measure)
            if bad:
                p.append(f"{sc}: alat ukur menunjuk dokumen/ID hilir yang belum terbit ({', '.join(sorted(set(bad)))})")
            if SUBJECTIVE_MEASURES.search(measure):
                p.append(f"{sc}: alat ukur subjektif ({SUBJECTIVE_MEASURES.search(measure).group(0)})")
            if not measure.strip():
                p.append(f"{sc}: alat ukur kosong")
        if self.finding_source:
            carriers = [l for l in sc_lines if re.search(r"\bP[1-3]-\d+\b", l)]
            if not carriers:
                p.append("`finding_source` terisi tetapi tidak satu pun butir menyebut ID temuan (`P1-1`, …)")
            for line in carriers:
                if "Status: FIXED" not in line and "tidak muncul di REVIEW.md" not in line:
                    sc = (re.search(r"SC-\d+", line) or ["butir"])[0]
                    p.append(f"{sc}: butir pemikul temuan tanpa `> Status: FIXED` / `tidak muncul di REVIEW.md …`")
        self.add("T3a", "Alat ukur: literal & token terlarang", p)
        self.manual("T3b", "Alat ukur cocok kolom lane", "task/SKILL.md tabel Fase 3, task-template bagian 2 butir 3")
        self.manual("T4", "Ambang terukur", "task-template bagian 2 butir 4")

        p = []
        refs = FILE_LINE.findall(d.section_text("Description"))
        if not refs:
            p.append("`## Description` tanpa rujukan `file:baris`")
        for path, line_no in refs:
            f = self.root / path
            if not f.is_file():
                p.append(f"`{path}:{line_no}` — berkas tidak ada")
            elif int(line_no) > len(f.read_text(encoding="utf-8", errors="replace").splitlines()):
                p.append(f"`{path}:{line_no}` — melewati jumlah baris berkas")
        self.add("T5", "Bukti berpaut kode", p)

        items = [l for _, l in d.section("Out of Scope") if re.match(r"^\s*- ", l)]
        p = [] if items else ["`## Out of Scope` tanpa butir"]
        p += [f"butir tanpa ` — <alasan>`: {l.strip()[:60]}" for l in items
              if not re.match(r"^\s*- .+\S\s+—\s+\S", l)]
        self.add("T6", "Batas kerja bersuara", p)

        counters_start = min((n for n, l in d.body if re.match(r"^## +Counters\s*$", l)), default=None)
        hits = [h for h in placeholder_hits(d, slots=True)
                if counters_start is None or int(h.split(":")[0].split()[1]) < counters_start]
        self.add("T7", "Nol placeholder", hits)

        chain = (fm.get("chain") or "").strip().upper()
        ledger = [(m.group(1), m.group(2)) for _, l in d.section("Chain")
                  for m in [re.match(r"^\s*- \[([ xX~])\] +(BRD|PRD|BRIEF)\b", l)] if m]
        p = []
        if not planning:
            if chain or "Chain" in d.h2:
                p.append(f"lane non-planning `{lane}`: `chain:` dan `## Chain` wajib absen")
        elif chain not in VALID_CHAINS:
            p.append(f"`chain: {fm.get('chain') or '(kosong)'}` di luar {' | '.join(VALID_CHAINS)}")
        else:
            hops = [h for _, h in ledger]
            if hops != CHAIN_HOPS[chain]:
                p.append(f"ledger `## Chain` wajib tepat {' → '.join(CHAIN_HOPS[chain])} (menemukan: "
                         f"{' → '.join(hops) or '—'})")
            if CHAIN_TERMINAL_LANES[chain] != lane:
                p.append(f"`lane: {lane}` bukan lane terminal `{chain}` ({CHAIN_TERMINAL_LANES[chain]})")
            risk = (fm.get("risk") or "").upper()
            if risk in RISK_CHAINS and chain not in RISK_CHAINS[risk]:
                p.append(f"pasangan (risk {risk}, chain {chain}) tidak sah — chain-rules bagian 1.4")
        self.add("T8a", "Struktur ledger chain", p)
        if self.fresh:
            done = [h for mark, h in ledger if mark != " "]
            self.add("T8b", "Kondisi awal ledger", [f"hop sudah bertanda: {', '.join(done)}"] if done else [])
        self.manual("T9", "Kecukupan akar", "task-template bagian 2 butir 9")

    # ------------------------------------------------------------------ BRD

    def run_brd(self) -> None:
        d, fm = self.doc, self.doc.fm
        p: List[str] = [d.fm_error] if d.fm_error else []
        for key in ("title", "requester"):
            if not (fm.get(key) or "").strip():
                p.append(f"frontmatter `{key}` kosong")
        if (fm.get("status") or "") != "DRAFT":
            p.append(f"`status: {fm.get('status') or '(kosong)'}` — wajib `DRAFT`")
        if len(d.h1) != 1 or not d.h1[0].startswith("# BRD: "):
            p.append("H1 wajib tepat satu berawalan `# BRD: `")
        if d.h2 != BRD_SECTIONS:
            p.append(f"seksi wajib persis {' → '.join(BRD_SECTIONS)} (menemukan: {' → '.join(d.h2) or '—'})")
        self.add("B1", "Struktur & frontmatter", p)

        rules = d.section_text("Business rules")
        br = [int(n) for n in re.findall(r"^\s*- \*\*BR-(\d+)\*\*", rules, re.M)]
        retired_line = next((l for _, l in d.section("Business rules") if l.strip().startswith("Pensiun:")), "")
        retired = [int(a) for a, _ in re.findall(r"BR-(\d+)\s*(?:→|->)\s*BR-(\d+)", retired_line)]
        p = []
        if set(br) & set(retired):
            p.append(f"nomor pensiun muncul lagi sebagai aturan aktif: "
                     f"{', '.join(f'BR-{n}' for n in sorted(set(br) & set(retired)))}")
        seq = sequence_problem(sorted(br + retired), "BR") if br else "tidak ada baris `- **BR-{n}**:`"
        if seq and not (set(br) & set(retired)):
            p.append(seq)
        if not retired_line:
            p.append("baris `Pensiun:` tidak ada")
        ec = [int(n) for n in re.findall(r"^\s*- \*\*EC-(\d+)\*\*", d.section_text("Edge cases"), re.M)]
        seq = sequence_problem(ec, "EC", allow_zero=True)
        if seq:
            p.append(seq)
        metrics = d.section_text("Business metrics")
        bm = [int(n) for n in re.findall(r"^\s*- \*\*BM-(\d+)\*\*", metrics, re.M)]
        seq = sequence_problem(bm, "BM", allow_zero=True)
        if seq:
            p.append(seq)
        outside = [int(n) for n in re.findall(r"BM-LUAR-RANTAI:\s*BM-(\d+)", metrics)]
        p += [f"`BM-LUAR-RANTAI: BM-{n}` menunjuk nomor yang tidak ada" for n in outside if n not in bm]
        self.add("B2", "Penomoran BR/EC/BM", p)

        p, warn = [], []
        for n, line in d.section("Current state"):
            for path, line_no in FILE_LINE.findall(line):
                if "Observasi kode" not in line:
                    p.append(f"baris {n}: `{path}:{line_no}` tanpa label `Observasi kode:`")
                elif not (self.root / path).is_file():
                    warn.append(f"baris {n}: `{path}` tidak ada di repo")
        self.add("B3", "Observasi vs aturan", p or warn, status="FAIL" if p else ("WARN" if warn else "PASS"))

        self.add("B4", "Nol placeholder", placeholder_hits(d, slots=False))

        p = [f"`## {s}` kosong" for s in ("Edge cases", "Business metrics", "Out of scope", "Open questions")
             if not d.section_text(s).strip()]
        self.add("B5", "Seksi nihil tetap bersuara", p)

        self.add("B6", "Anggaran Open questions",
                 self._open_questions(d, blocking=("Business rules", "Target state"), brd=True))

        p = []
        sc = success_criteria_ids(self.task)
        luar = set(outside)
        for _, line in d.section("Business metrics"):
            m = re.match(r"^\s*- \*\*BM-(\d+)\*\*", line)
            if not m or m.group(1) == "0":
                continue
            moved = re.search(r"digerakkan:\s*(.*)$", line)
            if not self.task:
                if moved and moved.group(1).strip() not in ("—", "-"):
                    p.append(f"BM-{m.group(1)}: `TASK.md` absen — `digerakkan:` wajib `—`")
                continue
            refs = [int(n) for n in re.findall(r"SC-(\d+)", moved.group(1))] if moved else []
            if not refs and int(m.group(1)) not in luar:
                p.append(f"BM-{m.group(1)}: tanpa `digerakkan: SC-{{n}}` maupun entri `BM-LUAR-RANTAI`")
        if self.task:
            ghosts = sorted(set(ids(d.text, "SC")) - sc)
            p += [f"SC-{n} tidak ada di TASK.md (rujukan hantu)" for n in ghosts]
        self.add("B7a", "Batas akar: BM → SC", p)
        self.manual("B7b", "Batas akar: BR → SC & Out of Scope", "brd-template Self-test butir 7")

        p, used = [], set()
        for _, line in d.section("Edge cases"):
            m = re.match(r"^\s*- \*\*EC-(\d+)\*\*\s*(.*)$", line)
            if not m or m.group(1) == "0":
                continue
            slugs = re.findall(r"\[([a-z-]+)\]", m.group(2).split(":", 1)[0])
            if len(slugs) != 1 or slugs[0] not in EC_CATEGORIES:
                p.append(f"EC-{m.group(1)}: wajib tepat satu slug kategori sah (menemukan: {slugs or '—'})")
            used.update(s for s in slugs if s in EC_CATEGORIES)
        nihil = next((l for _, l in d.section("Edge cases") if l.strip().startswith("Kategori nihil:")), None)
        if nihil is None:
            p.append("baris `Kategori nihil:` tidak ada")
        named = {c for c in EC_CATEGORIES if nihil and re.search(rf"(?<![\w-]){re.escape(c)}(?![\w-])", nihil)}
        missing = [c for c in EC_CATEGORIES if c not in used | named]
        if missing:
            p.append(f"kategori tidak tersapu (tidak dipakai EC maupun disebut `Kategori nihil:`): {', '.join(missing)}")
        self.add("B8", "Taksonomi kasus batas", p)

        p, warn, kinds = [], [], []
        for _, line in d.section("Actors"):
            m = re.match(r"^\s*- \*\*(.+?)\*\*\s*\(([^)]*)\)\s*(.*)$", line)
            if not line.strip().startswith("- "):
                continue
            if not m:
                p.append(f"baris aktor tanpa bentuk `- **<peran>** (<jenis>) — boleh: …; dilarang: …`: {line.strip()[:50]}")
                continue
            kind = m.group(2).strip()
            kinds.append(kind)
            if kind not in ACTOR_KINDS:
                p.append(f"{m.group(1)}: jenis `{kind}` di luar {' | '.join(ACTOR_KINDS)}")
            for key in ("boleh:", "dilarang:"):
                if key not in m.group(3):
                    p.append(f"{m.group(1)}: `{key}` tidak ada")
        if "terlarang" not in kinds:
            p.append("tidak ada aktor berjenis `terlarang`")
        for n, line in d.section("Actors"):
            if re.search(r"(?<![\w-])user(?![\w-])", INLINE_CODE.sub("", line), re.IGNORECASE):
                warn.append(f"baris {n}: kata `user` berdiri sendiri")
        self.add("B9", "Aktor & aksi terlarang", p or warn, status="FAIL" if p else ("WARN" if warn else "PASS"))

        problem = d.section_text("Problem")
        p = []
        for axis in ("Finansial:", "Operasional:", "Integritas data:"):
            m = re.search(rf"^\s*-?\s*{re.escape(axis)}\s*(.*)$", problem, re.M)
            if not m or not m.group(1).strip():
                p.append(f"baris `{axis}` hilang atau kosong")
        if not any(f in problem.lower() for f in FREQUENCIES):
            p.append(f"frekuensi ({' | '.join(FREQUENCIES)}) tidak disebut")
        self.add("B10", "Biaya pembiaran terkuantifikasi", p)

        self.add("B11", "Nol heading tabrakan",
                 [f"heading `## {h}` milik TASK.md" for h in d.h2 if h.lower() == "success criteria"])
        self.manual("B12", "Kecukupan aturan", "brd-template Self-test butir 12")

    # ------------------------------------------------------------------ PRD

    def run_prd(self) -> None:
        d, fm = self.doc, self.doc.fm
        no_brd = "tidak ada" in (fm.get("source_brd") or "").lower()
        tables = {s: table_rows(d.section(s)) for s in PRD_SECTIONS}
        ac_rows = [r for t in tables["Acceptance criteria"] for r in t if "AC" in r]
        breakdown = [r for t in tables["Task breakdown"] for r in t if "Urutan" in r]

        def dasar_text() -> str:
            parts = [l for _, l in d.body if re.match(r"^\s*- Dasar:", l)]
            parts += [r.get("Dasar", "") for ts in tables.values() for t in ts for r in t]
            return "\n".join(parts)

        dasar = dasar_text()
        questions = d.section_text("Open questions")

        if no_brd:
            self.add("P1", "Cakupan BR-{n}", status="PASS", note="dilewati — BRD absen (sumbu bisnis nol)")
            self.add("P2", "Cakupan EC-{n}", status="PASS", note="dilewati — BRD absen (sumbu bisnis nol)")
        elif not self.brd:
            self.add("P1", "Cakupan BR-{n}", [f"`source_brd` menunjuk BRD tetapi {self.taskdir.name}/BRD.md tidak ada"])
            self.add("P2", "Cakupan EC-{n}", ["BRD.md tidak ada"])
        else:
            brd_br = {int(n) for n in re.findall(r"^\s*- \*\*BR-(\d+)\*\*", self.brd.section_text("Business rules"), re.M)}
            disputed = {int(n) for n in re.findall(r"BR-DISANGGAH:\s*BR-(\d+)", questions)}
            cited = set(ids(dasar, "BR"))
            p = [f"BR-{n} tidak disebut kolom Dasar mana pun maupun `BR-DISANGGAH:`"
                 for n in sorted(brd_br - cited - disputed)]
            p += [f"BR-{n} di kolom Dasar tidak ada di BRD (rujukan hantu)" for n in sorted((cited | disputed) - brd_br)]
            self.add("P1", "Cakupan BR-{n}", p)
            brd_ec = {int(n) for n in re.findall(r"^\s*- \*\*EC-(\d+)\*\*", self.brd.section_text("Edge cases"), re.M)} - {0}
            ac_ec = {n for r in ac_rows for n in ids(r.get("Dasar", ""), "EC")}
            p = [f"EC-{n} tanpa AC penagih" for n in sorted(brd_ec - ac_ec)]
            p += [f"EC-{n} di AC tidak ada di BRD (rujukan hantu)" for n in sorted(ac_ec - brd_ec)]
            self.add("P2", "Cakupan EC-{n}", p)

        roots = {n for r in ac_rows for n in ids(r.get("Akar", ""), "SC")}
        if self.task:
            sc = success_criteria_ids(self.task)
            p = [f"SC-{n} tanpa AC penagih (kolom Akar)" for n in sorted(sc - roots)]
            p += [f"SC-{n} di kolom Akar tidak ada di TASK.md" for n in sorted(roots - sc)]
        else:
            p = [f"{r.get('AC')}: `TASK.md` absen — kolom Akar wajib `—`" for r in ac_rows
                 if r.get("Akar", "").strip() not in ("—", "-")]
        self.add("P3", "Cakupan SC-{n}", p)
        self.manual("P4", "Batas ruang lingkup hulu", "prd-template Self-test butir 4")

        p = []
        for r in ac_rows:
            how = r.get("Cara verifikasi", "").strip()
            if how != "test otomatis" and not re.match(r"^QA manual:\s*\S.{4,}", how):
                p.append(f"{r.get('AC')}: `Cara verifikasi` \"{how or '(kosong)'}\" bukan `test otomatis` atau `QA manual: <langkah>`")
            elif TEST_CLASS.search(INLINE_CODE.sub(lambda m: m.group(0).strip("`"), how)):
                p.append(f"{r.get('AC')}: `Cara verifikasi` menyebut nama test — penamaan milik `plan`")
        if not ac_rows:
            p.append("tabel `## Acceptance criteria` kosong")
        self.add("P5", "Realitas verifikasi AC", p)

        p = [d.fm_error] if d.fm_error else []
        for key in ("title", "source_brd"):
            if not (fm.get(key) or "").strip():
                p.append(f"frontmatter `{key}` kosong")
        if (fm.get("status") or "") != "DRAFT":
            p.append(f"`status: {fm.get('status') or '(kosong)'}` — wajib `DRAFT`")
        if len(d.h1) != 1 or not d.h1[0].startswith("# PRD: "):
            p.append("H1 wajib tepat satu berawalan `# PRD: `")
        if d.h2 != PRD_SECTIONS:
            p.append(f"seksi wajib persis {' → '.join(PRD_SECTIONS)} (menemukan: {' → '.join(d.h2) or '—'})")
        self.add("P6", "Struktur & frontmatter", p)

        p = []
        impact = [r for t in tables["Impact map"] for r in t if "#" in r]
        nums = [r.get("#", "").strip() for r in impact]
        if nums != [str(i) for i in range(1, 17)]:
            p.append(f"wajib tepat 16 baris bernomor 1–16 (menemukan {len(nums)}: {', '.join(nums[:18])})")
        steps = {r.get("Urutan", "").strip() for r in breakdown}
        for r in impact:
            n, verdict = r.get("#", "").strip(), r.get("Vonis", "").strip()
            proof, landing = r.get("Bukti", "").strip(), r.get("Mendarat di", "").strip()
            if verdict not in ("terdampak", "tidak relevan"):
                p.append(f"dimensi {n}: vonis `{verdict or '(kosong)'}`")
            elif verdict == "terdampak":
                if "`" not in proof and not FILE_LINE.search(proof):
                    p.append(f"dimensi {n}: `terdampak` tanpa bukti simbol")
                target = re.search(r"Task breakdown #(\d+)", landing)
                if not target or target.group(1) not in steps:
                    p.append(f"dimensi {n}: `Mendarat di` wajib `Task breakdown #<n>` yang ada")
            elif n.isdigit() and int(n) in LEAK_PRONE_DIMENSIONS and "`" not in proof:
                p.append(f"dimensi {n} (rawan bocor): `tidak relevan` tanpa jejak sapuan bersimbol")
        self.add("P7", "Impact map penuh", p)

        p = placeholder_hits(d, slots=False)
        for pillar in CONTRACT_PILLARS:
            for t in tables[pillar]:
                for r in t:
                    empty = [h for h, v in r.items() if h and not v.strip()]
                    if empty:
                        p.append(f"`## {pillar}`: sel kosong ({', '.join(empty)})")
            if not d.section_text(pillar).strip():
                p.append(f"`## {pillar}` kosong")
        self.add("P8", "Nol placeholder & sel kosong", p)

        self.add("P9", "Anggaran Open questions",
                 self._open_questions(d, blocking=("Task breakdown", "Business rules"), brd=False))

        p = []
        targets = "\n".join(d.section_text(s) for s in ASSUMPTION_TARGETS)
        for entry in self._question_entries(d):
            assumed = entry.split("sementara dipakai:", 1)[1] if "sementara dipakai:" in entry else ""
            for token in re.findall(r"`([^`\n]+)`", assumed):
                if token.strip() and token in targets:
                    p.append(f"asumsi `{token}` sudah membentuk kontrak — entri memblokir: {entry.strip()[:50]}")
        self.add("P9b", "Silang isi asumsi", p)

        p = []
        for section, rows in (("Task breakdown", breakdown), ("Acceptance criteria", ac_rows)):
            for r in rows:
                for h, v in r.items():
                    plain = v.replace("`", "")
                    for rx, what in ((SOURCE_FILE, "berkas sumber"), (TEST_CLASS, "nama test")):
                        m = rx.search(plain)
                        if m:
                            p.append(f"`## {section}` kolom {h}: {what} `{m.group(0)}` — penamaan milik `plan`")
        self.add("P10", "Nol penetapan berkas", p)
        self.manual("P10b", "Kecukupan kontrak", "prd-template Self-test butir 10b")

    # ------------------------------------------------------------------ bersama

    @staticmethod
    def _question_entries(d: Doc) -> List[str]:
        return [l for _, l in d.section("Open questions") if re.match(r"^\s*- \*\*", l)]

    def _open_questions(self, d: Doc, blocking: Sequence[str], brd: bool) -> List[str]:
        entries = self._question_entries(d)
        text = d.section_text("Open questions").strip()
        p: List[str] = []
        if not entries and not text:
            return ["seksi kosong — tulis penegasan eksplisit"]
        if len(entries) > 3:
            p.append(f"{len(entries)} entri — batas tiga")
        for e in entries:
            label = e.strip()[:50]
            disputed = "BR-DISANGGAH:" in e
            if "sementara dipakai:" not in e:
                p.append(f"entri tanpa `sementara dipakai:`: {label}")
            if not disputed and "terdampak:" not in e:
                p.append(f"entri tanpa `terdampak:`: {label}")
            hit = re.search(r"terdampak:(.*?)(?:;\s*sementara dipakai:|$)", e)
            if hit and any(b.lower() in hit.group(1).lower() for b in blocking):
                p.append(f"entri memblokir (`terdampak:` menyebut {' / '.join(blocking)}): {label}")
        return p

    def run(self) -> None:
        {"task": self.run_task, "brd": self.run_brd, "prd": self.run_prd}[self.kind]()

    @property
    def failed(self) -> bool:
        return any(r["status"] == "FAIL" for r in self.results)

    def format_text(self) -> str:
        mech = [r for r in self.results if r["status"] in ("PASS", "FAIL", "WARN")]
        ok = sum(1 for r in mech if r["status"] != "FAIL")
        manual = sum(1 for r in self.results if r["status"] == "MANUAL")
        head = (f"DOC VALIDATION: {self.kind} [{'FAIL' if self.failed else 'PASS'}] "
                f"({ok}/{len(mech)} mekanis lolos) · {manual} butir manual")
        width = max(len(f"[{r['id']}] {r['name']}") for r in self.results)
        lines = [head]
        for r in self.results:
            label = f"[{r['id']}] {r['name']}".ljust(width)
            lines.append(f"{label} : {r['status']}" + (f" ({r['summary']})" if r["summary"] else ""))
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps({"kind": self.kind, "taskdir": str(self.taskdir.relative_to(self.root))
                           if self.taskdir.is_relative_to(self.root) else str(self.taskdir),
                           "status": "FAIL" if self.failed else "PASS", "checks": self.results},
                          ensure_ascii=False, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kind", required=True, choices=["task", "brd", "prd"])
    ap.add_argument("--taskdir", required=True)
    ap.add_argument("--fresh", action="store_true", help="TASK baru ditulis: seluruh hop ledger belum tercentang (T8b)")
    ap.add_argument("--finding-source", default=None, help="Akar berangkat dari temuan (T3a klausa Status)")
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve() if a.root else find_repo_root()
    taskdir = resolve_taskdir(root, a.taskdir)
    name = {"task": "TASK.md", "brd": "BRD.md", "prd": "PRD.md"}[a.kind]
    if not (taskdir / name).is_file():
        msg = f"{taskdir / name} tidak ada"
        if a.json:
            print(json.dumps({"kind": a.kind, "status": "ERROR", "error": msg, "checks": []}, ensure_ascii=False))
        else:
            print(f"DOC VALIDATION: {a.kind} [ERROR] {msg}", file=sys.stderr)
        return 2
    v = Validator(a.kind, taskdir, root, fresh=a.fresh, finding_source=a.finding_source)
    v.run()
    print(v.to_json() if a.json else v.format_text())
    return 1 if v.failed else 0


if __name__ == "__main__":
    sys.exit(main())
