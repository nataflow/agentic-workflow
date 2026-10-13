#!/usr/bin/env python3
"""REVIEW.md Validator — review penutup `frontend:architect`.

Menegakkan bagian 2 `templates/review-template.md` atas **isi**, bukan hanya
bentuk: frontmatter menunjuk taskdir, stack profil, dan tanggal kalender yang
sah; H1 memuat slug; satu baris vonis per `SC-{n}` `TASK.md` dan per `AC-{n}`
`CONTRACT.md`; bukti `terbukti` menunjuk baris berkas rantai yang ada atau
perintah yang HIJAU; hitungan temuan sama dengan frontmatter; status 9 dimensi
sama dengan severity terburuk temuan yang menyebutnya; `## Summary` menyalin
verdict dan hitungan; dan **verdict yang diturunkan mekanis** dari isinya —
bukan dipilih reviewer:

- `BLOCKED` ⇔ P1 > 0, satu SC `belum terbukti`, satu Done Criteria `tidak terpenuhi`,
  atau galat baru/TIMEOUT di verifikasi penutup;
- selain itu `WARNING` ⇔ P2 > 0 atau satu AC `belum terbukti`;
- selain itu `PASS`.

`--log <taskdir>/.explore/closing-verification.json` (dipakai `architect` Phase 4,
sesi yang sama dengan `run_verification.py closing`) mencocokkan tabel
`## Verifikasi Penutup` dengan log mesin: himpunan perintah, hasil, dan galat
baru wajib identik, `MERAH` bergalat baru 0 sah hanya di atas baseline yang
juga merah, dan tiap baseline wajib diukur (`baseline_head`) di leluhur commit
`implement unit` pertama rantai — baseline di atas unit yang sudah mendarat
menelan galatnya sebagai warisan (12 J13). Tanpa `--log` (laci `.explore/` tidak dicerminkan, jadi `report` dan
sesi lain tidak dapat menuntutnya) check `LOG` dicatat `SKIP`.

Dipakai `architect` sesudah reviewer menulis `REVIEW.md` (tanpa commit, Langkah 24), dan `frontend:report` sebagai
prasyarat — janji akar yang belum terbukti tidak pernah sampai ke laporan.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    strip_explore_scratch,
    UNDECODABLE_ACTION,
    undecodable,
    FrontmatterError,
    GitError,
    ac_rows,
    chain_files,
    find_repo_root,
    git,
    is_manual,
    is_table_rule,
    normalize_taskdir,
    outside_fences,
    profile_dir_for,
    read_profile_stack,
    section_lines,
    split_frontmatter,
    success_criteria,
    table_cells,
    task_root_sha,
    taskdir_slug,
)
from precondition_lib import cli  # noqa: E402

HEADINGS = ["## Summary", "## Verifikasi Penutup", "## Cakupan Success Criteria",
            "## Cakupan Acceptance Criteria", "## Temuan", "## Done Criteria DITUNDA",
            "## Umpan balik profil", "## 9 Dimensi"]
ROW_ID = re.compile(r"^`?((?:SC|AC)-\d+)`?$")
ID_TOKEN = re.compile(r"\b(?:SC|AC)-\d+\b")
FINDING = re.compile(r"^### \[(P[123])-(\d+)\]")
# Heading yang tampak temuan tetapi tak terurai `FINDING` (`###[P1-1]`, `### [p1-1]`) — 12 J26.
LOOSE_FINDING = re.compile(r"^#{1,6}\s*\[?\s*[pP]\s*\d+\s*-\s*\d+")
TEST_FILE = re.compile(r"\.(test|spec)\.[A-Za-z0-9]+$")
EMPTY_CELLS = {"", "-", "—", "–"}
SC_VERDICTS = ("terbukti", "belum terbukti", "PERLU VERIFIKASI MANUAL")
AC_VERDICTS = ("terbukti", "belum terbukti", "QA manual")
DIMENSIONS = ["Layer Boundaries", "Data Flow & DTO", "API Layer", "State Scope & Ownership",
              "UI & 6-State Branches", "Platform & Framework Boundary", "Error Handling", "Performance & Leaks",
              "Test Quality"]
DIM_STATUS = ("PASS", "P1", "P2", "P3")
PATH_LINE = re.compile(r"`([^`\s]+):(\d+)(?:-\d+)?`")
VIOLATION = re.compile(r"^- \*\*Violation\*\*:\s*Dimensi\s+([1-9](?:\s*(?:&|,)\s*[1-9])*)\s*—")
DONE_VERDICTS = ("terpenuhi", "tidak terpenuhi")
BACKTICKED = re.compile(r"^`([^`]+)`$")


class ReviewValidator:
    def __init__(self, taskdir: str, root: Optional[Path] = None, log: str = ""):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.taskdir = self.root / self.taskdir_rel
        self.path = self.taskdir / "REVIEW.md"
        self.log = log
        self.results: List[Dict[str, Any]] = []
        self.derived = ""
        self.green: Set[str] = set()
        self.table: Dict[str, Tuple[str, str]] = {}
        self.dims: Dict[int, str] = {}
        self.finding_dims: List[Tuple[str, List[int]]] = []
        self.dups: List[str] = []
        self.unparsed: List[str] = []

    def _add(self, cid: str, name: str, problems: List[str], ok: str, action: str,
             status: str = "") -> None:
        self.results.append({"id": cid, "name": name, "status": status or ("FAIL" if problems else "PASS"),
                             "summary": f"{len(problems)} pelanggaran" if problems else ok,
                             "details": problems, "action": action if problems else ""})

    def rows(self, heading: str) -> Dict[str, List[str]]:
        """`{SC-n|AC-n: [vonis, bukti]}`; sel dipecah dengan menghormati `\\|` (12 J26).

        Baris yang menyebut `SC-n`/`AC-n` tetapi tak terurai (kolom pertama bukan ID, kurang dari tiga
        sel) dicatat di `self.unparsed`, bukan dilewati — vonis yang hilang tidak boleh menurunkan verdict.
        """
        out: Dict[str, List[str]] = {}
        for line in section_lines(self.body, heading):
            cells = table_cells(line)
            if not cells or is_table_rule(cells):
                continue
            m = ROW_ID.match(cells[0])
            if not m or len(cells) < 3:
                if ID_TOKEN.search(line):
                    self.unparsed.append(f"baris tak terurai di `{heading}`: {line.strip()[:80]}")
                continue
            if m.group(1) in out:
                self.dups.append(m.group(1))
                continue
            out[m.group(1)] = [cells[1], " | ".join(cells[2:])]
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
        red = self._verification_red()          # dibaca lebih dulu: perintah HIJAU dipakai bukti SC
        self._check_log()
        self._check_tree()
        sc_blocked = self._check_sc()
        ac_open = self._check_ac()
        counts = self._check_findings()
        self._check_dimensions()
        done_blocked = self._check_done()
        self._check_verdict(counts, sc_blocked or done_blocked, ac_open, red)
        self._check_summary(counts)
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
            p.append(f"`base: {base or '(kosong)'}` bukan `base_commit` akar TASK.md ({root_sha[:7] or 'tak terbaca'})")
        # 24 K9: `head` = HEAD yang dinilai reviewer; kesegaran review diukur dari sha ini, bukan dari commit REVIEW.md
        head = str(self.fm.get("head", "")).strip()
        full = git(self.root, "rev-parse", "--verify", "-q", f"{head}^{{commit}}").strip() \
            if re.fullmatch(r"[0-9a-f]{7,40}", head) else ""
        if not full or not self._is_ancestor(full, "HEAD"):
            p.append(f"`head: {head or '(kosong)'}` bukan commit leluhur `HEAD` — isi dengan `HEAD` saat review")
        raw = str(self.fm.get("reviewed_at", "")).strip()
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
                raise ValueError
            reviewed = datetime.datetime.strptime(raw, "%Y-%m-%d").date()
            born = git(self.root, "log", "-1", "--format=%cs", root_sha).strip() if root_sha else ""
            # sengaja tanpa pembanding "tanggal masa depan": zona waktu mesin menggesernya
            if born and reviewed < datetime.date.fromisoformat(born):
                p.append(f"`reviewed_at: {raw}` lebih awal dari `base_commit` akar ({born})")
        except ValueError:
            p.append(f"`reviewed_at: {raw or '(kosong)'}` bukan tanggal kalender YYYY-MM-DD")
        if str(self.fm.get("taskdir", "")).strip() != self.taskdir_rel:
            p.append(f"`taskdir: {self.fm.get('taskdir', '') or '(kosong)'}` ≠ `{self.taskdir_rel}`")
        stack = read_profile_stack(profile_dir_for(self.root))
        if stack and str(self.fm.get("stack", "")).strip() != stack:
            p.append(f"`stack: {self.fm.get('stack', '') or '(kosong)'}` ≠ stack profil `{stack}`")
        self._add("F", "Frontmatter", p, "lengkap", "Samakan dengan bagian 1 template.")

    def _check_structure(self) -> None:
        p = []
        lines = outside_fences(self.body.splitlines())
        h1 = [l for l in lines if l.startswith("# ")]
        want = f"# Review Findings — {taskdir_slug(self.taskdir_rel)}"
        if len(h1) != 1 or h1[0].strip() != want:
            p.append(f"H1 {h1} ≠ `{want}`")
        h2 = [l.strip() for l in lines if l.startswith("## ")]
        if h2 != HEADINGS:
            p.append(f"heading {h2} ≠ {HEADINGS}")
        for line in section_lines(self.body, "## 9 Dimensi"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 3 or not cells[0].isdigit():
                continue
            n = int(cells[0])
            if not 1 <= n <= 9 or n in self.dims:
                p.append(f"baris dimensi `{cells[0]}` di luar 1–9 atau ganda")
                continue
            if cells[1] != DIMENSIONS[n - 1]:
                p.append(f"dimensi {n} bernama `{cells[1] or '(kosong)'}`, wajib `{DIMENSIONS[n - 1]}`")
            if cells[2] not in DIM_STATUS:
                p.append(f"status dimensi {n} `{cells[2] or '(kosong)'}` di luar {'|'.join(DIM_STATUS)}")
            self.dims[n] = cells[2]
        if sorted(self.dims) != list(range(1, 10)):
            p.append(f"`## 9 Dimensi` memuat dimensi {sorted(self.dims)}, wajib 1–9")
        self._add("S", "Struktur", p, "8 heading + 9 dimensi", "Salin heading dan nama dimensi persis template.")

    def _evidence_problem(self, evidence: str, test_only: bool = False) -> str:
        """Kosong bila bukti memuat `path:baris` berkas rantai yang ada, atau perintah HIJAU di Verifikasi Penutup.

        `test_only` (AC `test otomatis`, 12 J41): hanya `path:baris` berkas test rantai yang sah. Berkas biner
        bukan bukti baris (12 J36) — ditolak dengan pesan yang menyebutnya, bukan dengan vonis "bukan UTF-8".
        """
        files = set(chain_files(self.root, self.taskdir_rel))
        binary = []
        for path, line in PATH_LINE.findall(evidence):
            f = self.root / path
            if path not in files or not f.is_file() or (test_only and not TEST_FILE.search(path)):
                continue
            try:
                count = len(f.read_bytes().decode("utf-8").splitlines())
            except UnicodeDecodeError:
                binary.append(path)
                continue
            if 1 <= int(line) <= count:
                return ""
        if not test_only and any(f"`{cmd}`" in evidence for cmd in self.green):
            return ""
        why = ("butuh `path:baris` berkas test rantai (`*.test.*`/`*.spec.*`) yang ada — AC `test otomatis`"
               if test_only else
               "butuh `path:baris` berkas rantai yang ada, atau perintah yang HIJAU di `## Verifikasi Penutup`")
        return why + (f"; `{'`, `'.join(binary)}` bukan berkas teks" if binary else "")

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
            if verdict == "terbukti":
                why = self._evidence_problem(evidence)
                if why:
                    p.append(f"`{s_id}` terbukti tanpa bukti sah: {why}")
            if verdict == "PERLU VERIFIKASI MANUAL" and not is_manual(line):
                p.append(f"`{s_id}` bukan SC ber-alat-ukur `QA manual:` — wajib divonis terbukti/belum")
            if verdict == "belum terbukti":
                blocked = True
        ghosts = sorted(set(k for k in rows if k.startswith("SC-")) - set(sc))
        p += [f"`{g}` tidak ada di TASK.md" for g in ghosts]
        p += [f"`{d}` divonis lebih dari sekali — satu baris per SC" for d in self.dups if d.startswith("SC-")]
        p += [u for u in self.unparsed if "Success Criteria" in u]
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
        contract_rows, parse_problems = ac_rows(cbody)
        acs = [ac for ac, _ in contract_rows]
        auto = {ac for ac, cells in contract_rows if len(cells) > 1 and "test otomatis" in cells[1].lower()}
        p, open_ = [f"CONTRACT.md: {x}" for x in parse_problems], False
        for ac in acs:
            if ac not in rows:
                p.append(f"`{ac}` tanpa baris vonis")
                continue
            verdict, evidence = rows[ac]
            if verdict not in AC_VERDICTS:
                p.append(f"`{ac}` vonis `{verdict}` di luar {AC_VERDICTS}")
            if verdict == "terbukti":                   # 12 J41: AC terbukti menuntut bukti seperti SC
                why = self._evidence_problem(evidence, test_only=ac in auto)
                if why:
                    p.append(f"`{ac}` terbukti tanpa bukti sah: {why}")
            if verdict == "belum terbukti":
                open_ = True
        p += [f"`{g}` tidak ada di CONTRACT.md" for g in sorted(set(k for k in rows if k.startswith("AC-")) - set(acs))]
        p += [f"`{d}` divonis lebih dari sekali — satu baris per AC" for d in self.dups if d.startswith("AC-")]
        p += [u for u in self.unparsed if "Acceptance Criteria" in u]
        self._add("AC", "Cakupan Acceptance Criteria", p, f"{len(acs)} AC divonis",
                  "Satu baris per AC-{n} CONTRACT.md; `terbukti` menunjuk `path:baris` berkas rantai atau perintah "
                  "HIJAU — AC `test otomatis` hanya berkas test rantai.")
        return open_

    def _check_findings(self) -> Dict[str, int]:
        lines = section_lines(self.body, "## Temuan")
        found: Dict[str, List[int]] = {"P1": [], "P2": [], "P3": []}
        p = []
        for i, line in enumerate(lines):
            m = FINDING.match(line.strip())
            if not m:
                if LOOSE_FINDING.match(line.strip()):
                    p.append(f"heading temuan tak terurai (wajib `### [P<1-3>-<n>] <judul>`): {line.strip()[:80]}")
                continue
            fid = f"{m.group(1)}-{m.group(2)}"
            found[m.group(1)].append(int(m.group(2)))
            block = []
            for nxt in lines[i + 1:]:
                if FINDING.match(nxt.strip()):
                    break
                block.append(nxt.strip())
            if not any(b.startswith("> Status:") for b in block):
                p.append(f"`{fid}` tanpa baris `> Status:`")
            viol = [VIOLATION.match(b) for b in block if b.startswith("- **Violation**")]
            if not viol or not viol[0]:
                p.append(f"`{fid}` *Violation* tidak diawali `Dimensi <n>[ & <m>] —`")
            else:
                self.finding_dims.append((m.group(1), [int(d) for d in re.findall(r"[1-9]", viol[0].group(1))]))
        counts = {k: len(v) for k, v in found.items()}
        for k, nums in found.items():
            if nums != list(range(1, len(nums) + 1)):
                p.append(f"nomor {k} {nums} tidak berurutan")
            declared = str(self.fm.get(k.lower(), "")).strip()
            if declared.isdigit() and int(declared) != len(nums):
                p.append(f"`{k.lower()}: {declared}` ≠ {len(nums)} temuan `{k}` di badan")
        self._add("T", "Temuan & hitungan", p, f"P1 {counts['P1']}, P2 {counts['P2']}, P3 {counts['P3']}",
                  "Samakan hitungan frontmatter dengan temuan ber-ID di badan; *Violation* diawali "
                  "`Dimensi <n>[ & <m>] —`.")
        return counts

    def _check_dimensions(self) -> None:
        p, worst = [], {}
        for sev, dims in self.finding_dims:
            for d in dims:
                worst[d] = min(worst.get(d, "P9"), sev)          # "P1" < "P2" < "P3"
        for n, status in sorted(self.dims.items()):
            want = worst.get(n, "PASS")
            if status in DIM_STATUS and status != want:           # status tak sah sudah FAIL di [S]
                p.append(f"dimensi {n} berstatus `{status}`, temuan menurunkan `{want}`")
        self._add("D", "Status 9 dimensi", p, "selaras dengan temuan",
                  "Status dimensi = severity terburuk temuan yang menyebut `Dimensi <n>` di *Violation*; "
                  "tanpa temuan → PASS.")

    def _check_done(self) -> bool:
        p, blocked = [], False
        for line in section_lines(self.body, "## Done Criteria DITUNDA"):
            cells = table_cells(line)                  # `\|` di sel bukan pemisah (12 J26)
            if not cells or is_table_rule(cells) or cells[0].lower() == "brief" or set(cells) <= EMPTY_CELLS:
                continue
            cells[0] = cells[0].strip("`")
            if len(cells) != 4 or not re.match(r"^brief-\d{2}\b", cells[0]):
                p.append(f"baris Done Criteria tak terurai (wajib `brief-<NN> | butir | vonis | bukti`): "
                         f"{line.strip()[:80]}")
                continue
            if cells[2] not in DONE_VERDICTS:
                p.append(f"{cells[0]} `{cells[1]}` vonis `{cells[2]}` di luar {DONE_VERDICTS}")
            blocked |= cells[2] == "tidak terpenuhi"
        self._add("DC", "Done Criteria DITUNDA", p, "vonis sah" + (" — ada yang tidak terpenuhi" if blocked else ""),
                  "Vonis `terpenuhi | tidak terpenuhi`; satu saja `tidak terpenuhi` memaksa BLOCKED.")
        return blocked

    def _verification_red(self) -> bool:
        """Merah bila satu baris MERAH/TIMEOUT bergalat baru; tabel tak sah juga FAIL.

        Tabel kosong, hasil di luar enum, perintah tanpa backtick, atau kolom galat
        non-angka tidak pernah dibaca sebagai hijau — vonis penutup tanpa bukti
        verifikasi adalah vonis palsu.
        """
        rows, p, red = 0, [], False
        for line in section_lines(self.body, "## Verifikasi Penutup"):
            cells = table_cells(line)                  # `\|` di sel bukan pemisah (12 J26)
            if not cells or is_table_rule(cells) or cells[0].lower() == "perintah":
                continue
            if len(cells) < 3:                         # 12 J39: baris pendek bukan baris yang dilewati
                p.append(f"baris tak terurai (wajib `perintah | hasil | galat baru`): {line.strip()[:80]}")
                red = True
                continue
            rows += 1
            result, new = cells[1].upper(), cells[2]
            cmd = BACKTICKED.match(cells[0])
            if not cmd:
                p.append(f"perintah `{cells[0] or '(kosong)'}` bukan perintah ber-backtick")
            if result not in ("HIJAU", "MERAH", "TIMEOUT"):
                p.append(f"hasil `{cells[1]}` di luar HIJAU|MERAH|TIMEOUT ({cells[0]})")
            if not new.isdigit():
                p.append(f"galat baru `{new}` bukan bilangan ({cells[0]})")
            if cmd:
                self.table[cmd.group(1)] = (result, new)
                if result == "HIJAU":
                    self.green.add(cmd.group(1))
                    full = BACKTICKED.match(cells[-1]) if len(cells) >= 6 else None
                    if full:
                        self.green.add(full.group(1))
            # Merah warisan baseline (galat baru 0) bukan kegagalan rantai ini; TIMEOUT tetap merah.
            if result == "TIMEOUT" or (new.isdigit() and int(new) > 0) or not new.isdigit():
                red = True
        if not rows:
            p.append("tabel `## Verifikasi Penutup` kosong — penutup tanpa bukti verifikasi")
            red = True
        self._add("VP", "Verifikasi penutup", p, f"{rows} perintah",
                  "Salin hasil `.explore/closing-verification.md` apa adanya: perintah ber-backtick, "
                  "HIJAU|MERAH|TIMEOUT, dan jumlah galat baru.")
        return red

    def _check_tree(self) -> None:
        """Reviewer read-only atas repo: sesudah ia bekerja, yang berubah hanya `REVIEW.md` dan baris
        status `finding_source` taskdir ini (09 E15, 12 J6). Hanya dengan `--log` (architect Phase 4,
        sesi reviewer); pemanggil lain (`report`) dapat sah memegang draft lain → `SKIP`."""
        name = "Tree sesudah reviewer"
        if not self.log:
            self.results.append({"id": "TREE", "name": name, "status": "SKIP", "summary": "tanpa --log",
                                 "details": [], "action": ""})
            return
        # Hanya `finding_source` taskdir ini, bukan seluruh `frontenddev/reviews/` (12 J6): berkas temuan
        # lain tidak dinilai `validate_audit.py` dan tidak ikut commit `closing review`.
        allowed = {f"{self.taskdir_rel}/REVIEW.md"}
        try:
            task_fm, _ = split_frontmatter((self.taskdir / "TASK.md").read_text(encoding="utf-8"))
        except (OSError, ValueError):                 # FrontmatterError & UnicodeDecodeError termasuk
            task_fm = {}
        source = task_fm.get("finding_source")
        if isinstance(source, str) and source.strip() not in ("", "-"):
            allowed.add(PurePosixPath(source.strip().strip("\"'")).as_posix())
        try:
            status = self._status_all()
        except GitError as exc:                   # 12 J17: tree tak terbaca tidak pernah bersih
            self._add("TREE", name, [f"`git status` gagal: {exc}"], "",
                      "Pulihkan repo (mis. index rusak) lalu jalankan ulang validator; tree yang tak terbaca "
                      "tidak pernah dianggap bersih.")
            return
        stray = []
        for line in strip_explore_scratch(status).splitlines():
            path = line[3:].split(" -> ")[-1].strip().strip('"')
            if path not in allowed:
                stray.append(path)
        self._add("TREE", name, [f"berubah selama review: `{p}`" for p in stray],
                  "hanya REVIEW.md / finding_source",
                  "Reviewer memutasi repo di luar batasnya: pulihkan berkas itu (`git restore -- <path>`), "
                  "buang REVIEW.md ini, dan dispatch ulang reviewer.")

    def _status_all(self) -> str:
        """`git status --porcelain -uall`; `GitError` bila git gagal (pola `precondition_lib.git_status`, 12 J17)."""
        try:
            proc = subprocess.run(["git", "-C", str(self.root), "status", "--porcelain", "-uall"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            raise GitError(str(exc)) from exc
        if proc.returncode != 0:
            raise GitError((proc.stderr.strip().splitlines() or [f"exit {proc.returncode}"])[-1])
        return proc.stdout

    def _check_log(self) -> None:
        name = "Verifikasi vs log mesin"
        if not self.log:
            self._add("LOG", name, [], "dilewati — tanpa `--log` (laci `.explore/` tidak dicerminkan)", "",
                      status="SKIP")
            return
        path = Path(self.log) if Path(self.log).is_absolute() else self.root / self.log
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
            log = {str(e["cmd"]): e for e in entries}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self._add("LOG", name, [f"log `{self.log}` tidak terbaca ({exc.__class__.__name__})"], "",
                      "Jalankan `run_verification.py closing` di sesi ini; log-nya ditulis di sebelah "
                      "`closing-verification.md`.")
            return
        p = []
        for cmd in sorted(set(self.table) - set(log)):
            p.append(f"perintah `{cmd}` di tabel tidak ada di log mesin")
        for cmd in sorted(set(log) - set(self.table)):
            p.append(f"perintah `{cmd}` di log mesin absen dari tabel")
        for cmd in sorted(set(self.table) & set(log)):
            result, new = self.table[cmd]
            e = log[cmd]
            if result != str(e.get("status")) or new != str(e.get("new_errors")):
                p.append(f"`{cmd}` {result}/{new} ≠ log mesin {e.get('status')}/{e.get('new_errors')}")
            elif result == "MERAH" and new == "0" and e.get("baseline_status") != "MERAH":
                p.append(f"`{cmd}` MERAH/0 tanpa baseline merah di log mesin")
        p += self._baseline_heads(log)
        self._add("LOG", name, p, f"{len(log)} perintah identik dengan log",
                  "Salin tabel `closing-verification.md` apa adanya; dilarang mengetik hasil sendiri.")

    def _first_unit(self) -> str:
        """Sha penuh commit `implement unit` pertama taskdir ini sejak akar, atau kosong."""
        since = task_root_sha(self.root, self.taskdir_rel)
        if not since:
            return ""
        rx = re.compile(rf"^[a-z]+!?\({re.escape(taskdir_slug(self.taskdir_rel))}\)!?: implement unit \d+")
        units = [l.split(" ", 1)[0] for l in git(self.root, "log", "--format=%H %s", f"{since}..HEAD").splitlines()
                 if " " in l and rx.match(l.split(" ", 1)[1])]
        return units[-1] if units else ""

    def _baseline_heads(self, log: Dict[str, Any]) -> List[str]:
        """Baseline yang ada wajib diukur sebelum unit pertama mendarat (12 J13, padanan merge-base be 3a)."""
        first = self._first_unit()
        p, verdicts = [], {}
        for cmd, e in sorted(log.items()):
            if e.get("baseline_status") is None:          # baseline absen: tiap MERAH sudah galat baru
                continue
            head = str(e.get("baseline_head") or "").strip()
            if not head:
                p.append(f"`{cmd}` baseline tanpa `baseline_head` — tidak terikat commit; ukur ulang baseline "
                         "di akar rantai")
                continue
            if head not in verdicts:
                full = git(self.root, "rev-parse", "--verify", "-q", f"{head}^{{commit}}").strip()
                if not full:
                    verdicts[head] = f"di {head[:7]} yang tidak ada di repo"
                elif first and (full == first or not self._is_ancestor(full, first)):
                    verdicts[head] = f"di {head[:7]}, sesudah unit pertama rantai ({first[:7]}) mendarat"
                else:
                    verdicts[head] = ""
            if verdicts[head]:
                p.append(f"`{cmd}` baseline diukur {verdicts[head]} — galat unit tertelan jadi warisan")
        return p

    def _is_ancestor(self, a: str, b: str) -> bool:
        return subprocess.run(["git", "-C", str(self.root), "merge-base", "--is-ancestor", a, b],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

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
                  "Verdict tidak dipilih: BLOCKED ⇔ P1/SC belum terbukti/Done Criteria tidak terpenuhi/"
                  "verifikasi merah; WARNING ⇔ P2/AC belum terbukti; selain itu PASS.")

    def _check_summary(self, counts: Dict[str, int]) -> None:
        p, lines = [], section_lines(self.body, "## Summary")
        status = [l.split(":", 1)[1].strip() for l in lines if l.strip().startswith("- Overall Status:")]
        if status != [self.derived]:
            p.append(f"`Overall Status: {', '.join(status) or '(absen)'}` ≠ verdict turunan `{self.derived}`")
        want = (f"- Total Findings: {sum(counts.values())} ({counts['P1']} P1, {counts['P2']} P2, "
                f"{counts['P3']} P3)")
        if [l.strip() for l in lines if l.strip().startswith("- Total Findings:")] != [want]:
            p.append(f"baris Total Findings wajib `{want}`")
        self._add("SUM", "Summary selaras", p, "Overall Status & Total Findings cocok",
                  "Salin verdict turunan dan hitungan temuan ke `## Summary`.")

    def format_text(self) -> str:
        failed = [r for r in self.results if r["status"] == "FAIL"]
        counted = [r for r in self.results if r["status"] != "SKIP"]
        lines = [f"REVIEW VALIDATION: [{'FAIL' if failed else 'PASS'}] "
                 f"({len(counted) - len(failed)}/{len(counted)} passed) — verdict turunan "
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
    parser.add_argument("--log", default="", help="log mesin closing-verification.json (architect Phase 4)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    v = ReviewValidator(args.taskdir, Path(args.root) if args.root else None, args.log)
    try:
        ok = v.run()
    except UnicodeDecodeError as exc:
        ok = False
        v._add("S", "Berkas terbaca", [undecodable(v.taskdir, exc)], "", UNDECODABLE_ACTION)
    print(json.dumps({"status": "PASS" if ok else "FAIL", "derived_verdict": v.derived,
                      "checks": v.results}, indent=2) if args.json else v.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    sys.exit(cli(main))
