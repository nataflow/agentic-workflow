#!/usr/bin/env python3
"""Frontend Brief Validator.

Menegakkan predikat brief yang **dapat divonis atas token** — struktur
frontmatter, kelengkapan seri unit, keasikliskan DAG, kuota berkas, co-location
test, larangan verifikasi per unit, placeholder, aksi berkas terhadap disk,
perintah verifikasi terhadap profil, penamaan lintas stack, tumpang tindih
berkas, cakupan terhadap `CONTRACT.md`, cakupan Acceptance Criteria, dan
keterpikulan tiap `SC-{n}` akar `TASK.md` lewat `fulfills` (Check G).

Plafon ronde audit Gate Plan Review **tidak** di sini lagi: ia dijaga
`skills/_common/review_round.py`, yang juga dibaca `chain.py approve`.

Predikat yang menuntut penilaian (apakah brief benar-benar mengerjakan yang
kontrak janjikan, apakah pemecahan unitnya masuk akal) **tidak** ada di sini;
itu wewenang `frontenddev:doc-reviewer`. Pemisahan itulah alasan skrip ini ada:
subagent berbayar tidak boleh membakar satu dispatch untuk menghitung ulang hal
yang deterministik.

Dipakai `frontenddev:plan` (per brief dan per batch), `chain.py approve --row
BRIEF` (syarat approval breakdown), dan `frontenddev:architect` (prasyarat).

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py` — parser frontmatter yang
sama dengan seluruh gerbang lain, supaya status brief tidak pernah divonis
berbeda oleh dua skrip.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    profile_dir_for,
    TASKDIR_PATTERN,
    FrontmatterError,
    split_frontmatter,
    sc_ids,
    success_criteria,
)
BRIEF_PATTERN = re.compile(r"^brief-(\d{2})-[a-z0-9-]+\.md$")

REQUIRED_FM_FIELDS = [
    "status", "slug", "stack", "based_on", "order", "unit",
    "total_units", "depends_on", "fulfills", "covers", "files_touched", "verification",
]
VALID_STATUS = {"READY", "DONE", "BLOCKED"}
LIST_FIELDS = ("depends_on", "fulfills", "covers", "files_touched", "verification")
LOCKED_STATUS = {"DONE", "BLOCKED"}

REQUIRED_SECTIONS = [
    "## 1. Intent & Scope Boundaries",
    "## 2. Interfaces & Contracts",
    "## 3. Current Repo State & Reference Symbols",
    "## 4. Implementation Steps",
    "## 5. Done Criteria & Verification Baseline",
]

# Check F — larangan verifikasi per unit di seksi 4.
#
# Tiga pola sempit, bukan satu pola lebar. Pola lebar "kata kerja + nama
# perintah dalam 40 karakter" menandai kalimat sah seperti "pastikan berkas
# test pendamping terdaftar": `test` di situ kata benda, bukan perintah.
_CMD = (r"typecheck|type-check|tsc|svelte-check|lint|eslint|vitest|jest|build"
        r"|dev server|npm run|pnpm|yarn|npx")
# Kata pengisi yang boleh berdiri antara kata kerja dan nama perintah.
_FILLER = r"(?:(?:perintah|skrip|ulang|kembali|seluruh|semua|lagi|dulu|juga)\s+){0,2}"

FORBIDDEN_RUN = [
    # 1. Kata kerja eksekusi langsung pada nama perintah: "jalankan typecheck".
    #    `test` ikut di sini karena "jalankan test" tidak punya bacaan lain.
    re.compile(rf"\b(?:jalankan|jalankanlah|eksekusi|eksekusikan|run)\b\s+{_FILLER}"
               rf"[`'\"]?\b(?:{_CMD}|tests?)\b", re.IGNORECASE),
    # 2. Kata kerja penjaminan pada nama perintah: "pastikan build lolos".
    #    `test` sengaja TIDAK ikut — "pastikan berkas test terdaftar" sah.
    re.compile(rf"\b(?:pastikan|memastikan)\b[^.\n]{{0,30}}?\b(?:{_CMD})\b",
               re.IGNORECASE),
    # 3. Penjaminan atas hasil test: "pastikan seluruh test lulus".
    re.compile(r"\b(?:pastikan|memastikan)\b[^.\n]{0,30}?\btests?\b[^.\n]{0,20}?"
               r"\b(?:lolos|lulus|hijau|passing|pass|berhasil|bersih)\b", re.IGNORECASE),
]


def forbidden_run(line: str) -> bool:
    """True bila baris menyuruh menjalankan verifikasi terminal."""
    return any(p.search(line) for p in FORBIDDEN_RUN)
TERMINAL_HINT = re.compile(
    r"\b(typecheck|type-check|tsc|svelte-check|lint|eslint|vitest|jest|npm run|pnpm|yarn|npx|build)\b",
    re.IGNORECASE,
)
CLOSING_MARK = "(verifikasi penutup)"

# Check B — placeholder yang tidak boleh lolos ke implementor.
PLACEHOLDER = re.compile(r"\b(TBD|TODO|FIXME|diisi nanti|isi nanti)\b", re.IGNORECASE)

# Slot `<...>` yang tersisa dari template dibedakan dari generik TypeScript dan
# tag JSX, yang sah muncul di prosa brief frontend. Dua penanda placeholder:
# memuat spasi (`<Nama Unit Fungsional>`), atau satu kata dari kosakata slot
# template (`<slug>`, `<NN>`). `<void>`, `<string>`, `<OrderRow>`, dan
# `<script>` tidak memenuhi keduanya.
ANGLE_SPAN = re.compile(r"<([^<>\n]{1,80})>")
ANGLE_SLOT = re.compile(
    r"^(?:slug|stack|stack-id|stack_id|feat|feature|taskdir|unit|nn|mm|n"
    r"|entitas|layar|nama|perintah|path|berkas|file|sha|commit|tanggal|versi"
    r"|command|deskripsi|judul|angka|nilai|id)$",
    re.IGNORECASE,
)
# Sintaks tipe TypeScript yang tidak pernah muncul di slot template berbahasa
# Indonesia: literal objek, anotasi, union, dan panah fungsi.
TS_TYPE_SYNTAX = re.compile(r"[{}:;=]")


def angle_placeholder(line: str) -> bool:
    """True bila baris menyisakan slot template `<...>` yang belum diisi.

    Dibedakan dari generik TypeScript dan tag JSX yang sah muncul di prosa brief
    frontend. Sebuah span `<...>` dinilai placeholder bila namanya ada di
    kosakata slot template, atau isinya berupa frasa multi-kata. Daftar argumen
    generik (`Record<string, string>`) bukan frasa multi-kata: spasi sesudah
    koma dinormalkan lebih dulu, dan span bersintaks tipe dilewati.
    """
    for m in ANGLE_SPAN.finditer(line):
        content = m.group(1).strip()
        if ANGLE_SLOT.match(content):
            return True
        if TS_TYPE_SYNTAX.search(content):
            continue
        probe = re.sub(r",\s+", ",", content)
        if " " in probe and re.search(r"[a-z]", probe, re.IGNORECASE):
            return True
    return False

# Check T — layer yang wajib punya test pendamping.
TEST_REQUIRED_DIRS = ("services/", "view-model/", "hooks/api/", "controllers/")
TEST_FILE = re.compile(r"\.(test|spec)\.[a-z]+$", re.IGNORECASE)

# Check K — penamaan lintas stack.
REACT_STACKS = {"react-vite", "react-native"}
SVELTE_STACKS = {"sveltekit", "svelte-vite"}
REACT_HOOK_FILE = re.compile(r"/use[A-Z][A-Za-z0-9]*\.ts$")

# Check P — resep deteksi pada baris Drift profil.
DRIFT_ROW = re.compile(
    r"^\s*-\s+(?P<warisan>.+?)\s+\u2192\s+(?P<modern>.+?)\s+\u00b7\s+deteksi\s+"
    r"`(?P<pola>[^`]+?)\s*@\s*(?P<glob>[^`]+?)`"          # satu span: `pola @ glob`
    r"|^\s*-\s+(?P<warisan2>.+?)\s+\u2192\s+(?P<modern2>.+?)\s+\u00b7\s+deteksi\s+"
    r"`(?P<pola2>[^`]+?)`\s*@\s*`(?P<glob2>[^`]+?)`"      # dua span: `pola` @ `glob`
)

ACTION_ROW = re.compile(
    r"^\|\s*(CREATE|MODIFY)\s*\|\s*`?([^`|]+?)`?\s*\|\s*(?:`?([^`|]*?)`?\s*\|)?"
)


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Pembungkus ketat parser bersama: frontmatter rusak adalah `FrontmatterError`."""
    return split_frontmatter(text, strict=True)


def read_section(text: str, heading: str) -> str:
    """Ambil badan satu heading markdown sampai heading setingkat berikutnya."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    out: List[str] = []
    capturing = False
    for line in lines:
        if line.strip() == heading.strip():
            capturing = True
            continue
        if capturing:
            stripped = line.lstrip("#")
            hashes = len(line) - len(stripped)
            if line.startswith("#") and 0 < hashes <= level:
                break
            out.append(line)
    return "\n".join(out)


def strip_code_fences(text: str) -> str:
    """Buang blok kode berpagar; contoh kode bukan instruksi menjalankan sesuatu."""
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


class BriefValidator:
    def __init__(
        self,
        taskdir: str,
        root: Optional[Path] = None,
        brief_filter: Optional[str] = None,
        contract_mode: bool = False,
        max_files_per_unit: int = 5,
        profile_dir: Optional[str] = None,
    ):
        self.root = (root or self._find_repo_root()).resolve()
        self.taskdir_rel = taskdir.strip("/").replace("./", "")
        self.taskdir = (self.root / self.taskdir_rel).resolve()
        self.brief_filter = brief_filter
        self.contract_mode = contract_mode
        self.max_files = max_files_per_unit
        self.profile_dir = profile_dir_for(self.root, profile_dir)
        self.stacks_dir = Path(__file__).resolve().parents[2] / "profile" / "stacks"
        self.briefs: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self.fatal: Optional[str] = None

    @staticmethod
    def _find_repo_root() -> Path:
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL, universal_newlines=True,
            ).strip()
            return Path(out)
        except Exception:
            return Path.cwd()

    def _add(self, cid: str, name: str, status: str, summary: str,
             action: str = "", details: Optional[List[str]] = None) -> None:
        self.results.append({
            "id": cid, "name": name, "status": status,
            "summary": summary, "action": action, "details": details or [],
        })

    # ------------------------------------------------------------------ load

    def load(self) -> bool:
        if not TASKDIR_PATTERN.match(self.taskdir_rel):
            self.fatal = (
                f"taskdir `{self.taskdir_rel}` tidak berpola "
                "`frontenddev/docs/<YYMMDDhhmm>-<slug>`"
            )
            return False
        if not self.taskdir.is_dir():
            self.fatal = f"taskdir `{self.taskdir_rel}` tidak ada di {self.root}"
            return False

        for path in sorted(self.taskdir.glob("brief-*.md")):
            m = BRIEF_PATTERN.match(path.name)
            if not m:
                self.fatal = (
                    f"`{path.name}` tidak berpola `brief-<NN>-<unit>.md`"
                )
                return False
            text = path.read_text(encoding="utf-8")
            try:
                fm, body = parse_frontmatter(text)
            except FrontmatterError as exc:
                self.fatal = f"{path.name}: {exc}"
                return False
            status = str(fm.get("status", "")).strip()
            self.briefs.append({
                "path": path,
                "name": path.name,
                "nn": m.group(1),
                "fm": fm,
                "body": body,
                "text": text,
                "status": status,
                "locked": status in LOCKED_STATUS,
            })

        if not self.briefs:
            self.fatal = f"tidak ada `brief-*.md` di `{self.taskdir_rel}`"
            return False
        return True

    def active(self) -> List[Dict[str, Any]]:
        """Brief yang ditagih predikat rencana: tidak terkunci, dan lolos filter."""
        out = [b for b in self.briefs if not b["locked"]]
        if self.brief_filter:
            out = [b for b in out if b["nn"] == self.brief_filter]
        return out

    # ---------------------------------------------------------------- checks

    def run_all(self) -> bool:
        if not self.load():
            return False
        self._check_s_struct()
        self._check_n_series()
        self._check_d_dag()
        self._check_l_quota()
        self._check_t_test_colocation()
        self._check_f_no_run()
        self._check_b_placeholder()
        self._check_r_repo_state()
        self._check_v_verification()
        self._check_k_naming()
        self._check_o_overlap()
        self._check_e_contract()
        self._check_c_acceptance()
        self._check_p_drift()
        self._check_g_fulfills()
        self._check_m_remedies()
        return not any(r["status"] == "FAIL" for r in self.results)

    def _files(self, brief: Dict[str, Any]) -> List[str]:
        value = brief["fm"].get("files_touched", [])
        return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []

    def _check_s_struct(self) -> None:
        """Berlaku atas **seluruh** brief, termasuk yang terkunci: brief `DONE` tanpa seksi atau
        tanpa field bukanlah unit yang pernah dieksekusi, melainkan status yang diketik."""
        cid, name = "S", "Struktur frontmatter & seksi"
        targets = [b for b in self.briefs if not self.brief_filter or b["nn"] == self.brief_filter]
        problems: List[str] = []
        for b in targets:
            missing = [f for f in REQUIRED_FM_FIELDS if f not in b["fm"]]
            if missing:
                problems.append(f"{b['name']}: field frontmatter hilang → {', '.join(missing)}")
            for f in LIST_FIELDS:
                if f in b["fm"] and not isinstance(b["fm"][f], list):
                    problems.append(f"{b['name']}: `{f}` wajib list (`[...]` atau butir `- `), bukan skalar")
            if b["status"] not in VALID_STATUS:
                problems.append(
                    f"{b['name']}: status `{b['status']}` di luar "
                    f"{sorted(VALID_STATUS)}"
                )
            pos = -1
            for heading in REQUIRED_SECTIONS:
                idx = b["body"].find("\n" + heading)
                if idx == -1:
                    problems.append(f"{b['name']}: seksi `{heading}` tidak ada")
                    continue
                if idx < pos:
                    problems.append(f"{b['name']}: seksi `{heading}` tidak berurutan")
                pos = idx
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} pelanggaran struktur",
                      "Samakan frontmatter dan judul seksi dengan "
                      "`templates/brief-template.md` bagian 1, persis huruf demi huruf.",
                      problems)
        else:
            self._add(cid, name, "PASS", f"{len(targets)} brief berstruktur sah")

    def _check_n_series(self) -> None:
        cid, name = "N", "Kelengkapan seri unit"
        nns = [b["nn"] for b in self.briefs]
        problems: List[str] = []
        expected = [f"{i:02d}" for i in range(1, len(self.briefs) + 1)]
        if sorted(nns) != expected:
            problems.append(
                f"nomor unit {sorted(nns)} bukan seri berurutan dari `01` "
                f"(diharapkan {expected})"
            )
        # Brief terkunci mempertahankan `total_units` saat ia ditulis: APPEND tidak menyunting
        # brief DONE/BLOCKED, jadi hanya brief aktif yang ditagih menyebut jumlah akhir.
        pool = [b for b in self.briefs if not b["locked"]]
        totals = {str(b["fm"].get("total_units", "")).strip().lstrip("0") or "0" for b in pool}
        if len(totals) > 1:
            problems.append(f"`total_units` tidak seragam antar brief aktif: {sorted(totals)}")
        declared = totals.pop() if len(totals) == 1 else None
        # Nilai ber-nol-depan ("03") dan tanpa ("3") setara; template memakai dua digit.
        if declared is not None and declared != str(len(self.briefs)):
            problems.append(
                f"`total_units: {declared}` tidak sama dengan jumlah brief "
                f"({len(self.briefs)})"
            )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} cacat seri",
                      "Perbaiki penomoran `unit`; `total_units` brief aktif = jumlah seluruh brief. "
                      "Brief DONE/BLOCKED tidak disunting.",
                      problems)
        else:
            self._add(cid, name, "PASS", f"seri 01..{len(self.briefs):02d} lengkap")

    def _check_d_dag(self) -> None:
        cid, name = "D", "DAG dependensi"
        known = {b["nn"] for b in self.briefs}
        edges: Dict[str, List[str]] = {}
        problems: List[str] = []
        for b in self.briefs:
            deps = b["fm"].get("depends_on", [])
            deps = [str(d).strip() for d in deps] if isinstance(deps, list) else []
            edges[b["nn"]] = deps
            for d in deps:
                if d not in known:
                    problems.append(f"{b['name']}: `depends_on` menunjuk unit `{d}` yang tidak ada")
                elif d >= b["nn"]:
                    problems.append(
                        f"{b['name']}: `depends_on` menunjuk `{d}` yang tidak lebih kecil "
                        f"dari `{b['nn']}` — urutan eksekusi tidak dapat ditentukan"
                    )
        state: Dict[str, int] = {}

        def visit(node: str, trail: List[str]) -> None:
            if state.get(node) == 2:
                return
            if state.get(node) == 1:
                problems.append(f"siklus dependensi: {' -> '.join(trail + [node])}")
                return
            state[node] = 1
            for nxt in edges.get(node, []):
                if nxt in edges:
                    visit(nxt, trail + [node])
            state[node] = 2

        for nn in edges:
            visit(nn, [])
        roots = [nn for nn, deps in edges.items() if not deps]
        if edges and not roots:
            problems.append("tidak ada unit akar (`depends_on: []`); rantai tidak punya titik mulai")
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} cacat DAG",
                      "Buat `depends_on` linier satu arah ke unit bernomor lebih kecil; "
                      "hapus siklus.", problems)
        else:
            self._add(cid, name, "PASS", f"{len(edges)} unit asiklik dan terjangkau")

    def _check_l_quota(self) -> None:
        cid, name = "L", "Kuota berkas per unit"
        targets = self.active()
        if not targets:
            self._add(cid, name, "SKIP", "seluruh brief terkunci")
            return
        problems: List[str] = []
        for b in targets:
            files = self._files(b)
            non_test = [f for f in files if not TEST_FILE.search(f)]
            if not files:
                problems.append(f"{b['name']}: `files_touched` kosong")
            if len(non_test) > self.max_files:
                problems.append(
                    f"{b['name']}: {len(non_test)} berkas non-test melampaui kuota "
                    f"{self.max_files} → {non_test}"
                )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} unit melampaui kuota",
                      "Pecah unit sampai maksimal "
                      f"{self.max_files} berkas non-test per brief.", problems)
        else:
            self._add(cid, name, "PASS", f"{len(targets)} unit di dalam kuota")

    def _check_t_test_colocation(self) -> None:
        cid, name = "T", "Co-location test"
        targets = self.active()
        if not targets:
            self._add(cid, name, "SKIP", "seluruh brief terkunci")
            return
        problems: List[str] = []
        for b in targets:
            files = self._files(b)
            tests = [f for f in files if TEST_FILE.search(f)]
            for f in files:
                if TEST_FILE.search(f):
                    continue
                if not any(seg in f for seg in TEST_REQUIRED_DIRS):
                    continue
                stem = Path(f).name
                stem = stem[: stem.rfind(".")] if "." in stem else stem
                if not any(Path(t).name.startswith(stem + ".") for t in tests):
                    problems.append(
                        f"{b['name']}: `{f}` berlayer logic tanpa berkas test pendamping "
                        "di `files_touched` yang sama"
                    )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} berkas logic tanpa test",
                      "Tambahkan berkas `*.test.*` pendamping ke `files_touched` brief "
                      "yang sama; implementor dilarang menyentuh berkas di luar daftar.",
                      problems)
        else:
            self._add(cid, name, "PASS", "seluruh berkas logic baru berpasangan test")

    def _check_f_no_run(self) -> None:
        cid, name = "F", "Larangan verifikasi per unit"
        targets = self.active()
        if not targets:
            self._add(cid, name, "SKIP", "seluruh brief terkunci")
            return
        problems: List[str] = []
        for b in targets:
            steps = strip_code_fences(read_section(b["body"], REQUIRED_SECTIONS[3]))
            for line in steps.splitlines():
                if forbidden_run(line):
                    problems.append(
                        f"{b['name']} seksi 4: instruksi menjalankan perintah terminal → "
                        f"{line.strip()[:90]}"
                    )
            done = read_section(b["body"], REQUIRED_SECTIONS[4])
            for line in done.splitlines():
                if not line.strip().startswith("- ["):
                    continue
                if TERMINAL_HINT.search(line) and CLOSING_MARK not in line:
                    problems.append(
                        f"{b['name']} seksi 5: butir terminal tanpa penanda "
                        f"`{CLOSING_MARK}` → {line.strip()[:90]}"
                    )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} pelanggaran",
                      "Hapus langkah menjalankan terminal dari seksi 4, dan beri "
                      f"penanda `{CLOSING_MARK}` pada tiap butir Done Criteria berbasis perintah.",
                      problems)
        else:
            self._add(cid, name, "PASS", "nol instruksi eksekusi terminal per unit")

    def _check_b_placeholder(self) -> None:
        cid, name = "B", "Placeholder tersisa"
        targets = self.active()
        if not targets:
            self._add(cid, name, "SKIP", "seluruh brief terkunci")
            return
        problems: List[str] = []
        for b in targets:
            for heading in REQUIRED_SECTIONS[1:]:
                body = strip_code_fences(read_section(b["body"], heading))
                for line in body.splitlines():
                    if PLACEHOLDER.search(line) or angle_placeholder(line):
                        problems.append(
                            f"{b['name']} `{heading[:6].strip()}`: placeholder tersisa → "
                            f"{line.strip()[:90]}"
                        )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} placeholder",
                      "Ganti seluruh `TBD`/`TODO`/`<...>` di seksi 2–5 dengan nilai nyata; "
                      "implementor membaca brief apa adanya.", problems)
        else:
            self._add(cid, name, "PASS", "seksi 2–5 bebas placeholder")

    def _action_table(self, brief: Dict[str, Any]) -> Dict[str, Tuple[str, str]]:
        """Baca tabel aksi seksi 3 menjadi {path: (aksi, anchor)}."""
        section = read_section(brief["body"], REQUIRED_SECTIONS[2])
        actions: Dict[str, Tuple[str, str]] = {}
        for line in section.splitlines():
            m = ACTION_ROW.match(line.strip())
            if m:
                anchor = (m.group(3) or "").strip()
                actions[m.group(2).strip()] = (m.group(1).strip(), anchor)
        return actions

    def _check_r_repo_state(self) -> None:
        cid, name = "R", "Aksi & anchor berkas vs disk"
        targets = self.active()
        if not targets:
            self._add(cid, name, "SKIP", "seluruh brief terkunci")
            return
        problems: List[str] = []
        for b in targets:
            actions = self._action_table(b)
            files = self._files(b)
            if not actions:
                problems.append(
                    f"{b['name']} seksi 3: tabel aksi berkas "
                    "(`| CREATE \\| MODIFY | <path> |`) tidak ada"
                )
                continue
            upstream_created = {
                p for o in self.briefs if o["nn"] < b["nn"] and o["status"] != "BLOCKED"
                for p, (a, _) in self._action_table(o).items() if a == "CREATE"
            }
            for f in files:
                if f not in actions:
                    problems.append(f"{b['name']}: `{f}` tidak punya baris aksi di seksi 3")
                    continue
                act, anchor = actions[f]
                exists = (self.root / f).exists() or (act == "MODIFY" and f in upstream_created)
                if act == "CREATE" and exists:
                    problems.append(
                        f"{b['name']}: `{f}` ditandai CREATE tetapi sudah ada di disk"
                    )
                if act == "MODIFY":
                    if not exists:
                        problems.append(
                            f"{b['name']}: `{f}` ditandai MODIFY tetapi belum ada di disk"
                        )
                    if not anchor or anchor in {"-", "—", "–"}:
                        problems.append(
                            f"{b['name']}: `{f}` ditandai MODIFY tanpa kolom `Anchor` — "
                            "batas scope berhenti di nama berkas dan simbol lain di "
                            "dalamnya bebas disunting"
                        )
            for path in actions:
                if path not in files:
                    problems.append(
                        f"{b['name']}: baris aksi `{path}` tidak ada di `files_touched`"
                    )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} ketidakcocokan",
                      "Samakan tabel aksi seksi 3 dengan `files_touched` dan keadaan "
                      "disk nyata; jalankan ulang Check 1 Rekonsiliasi.", problems)
        else:
            self._add(cid, name, "PASS", "aksi berkas cocok dengan keadaan disk")

    def _profile_file(self, name: str) -> Optional[str]:
        """Baca satu berkas profil modular, atau `None` bila ia tidak ada.

        Profil modular membuat tiap check membaca hanya berkas yang ia butuhkan;
        yang hilang divonis per berkas, bukan per profil, supaya pesannya menunjuk
        tepat ke yang perlu ditulis ulang.
        """
        path = self.profile_dir / name
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def _adapter_text(self, stack: str) -> Optional[str]:
        path = self.stacks_dir / f"{stack}.md"
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _commands(text: str) -> Set[str]:
        """Perintah utuh: span ber-backtick dan baris polos berawalan runner paket."""
        runner = re.compile(r"^(?:pnpm|npm|yarn|npx|bun|bunx|node|svelte-kit|svelte-check|tsc|vitest|jest|expo|eslint)\b")
        found: Set[str] = set()
        for m in re.finditer(r"`([^`\n]+)`", text):
            cand = " ".join(m.group(1).split())
            if runner.match(cand):
                found.add(cand)
        for line in text.splitlines():
            cand = " ".join(line.strip().lstrip("-* ").split())
            if runner.match(cand) and "`" not in cand and "|" not in cand:
                found.add(cand)
        return found

    @staticmethod
    def _tools(text: str) -> Set[str]:
        return set(
            t.lower() for t in re.findall(
                r"\b(tsc|svelte-check|svelte-kit|eslint|prettier|vitest|jest|"
                r"vite|expo|metro|playwright|check|lint|test|build|typecheck)\b",
                text, re.IGNORECASE,
            )
        )

    def _check_v_verification(self) -> None:
        cid, name = "V", "Perintah verifikasi vs profil"
        targets = self.active()
        if not targets:
            self._add(cid, name, "SKIP", "seluruh brief terkunci")
            return
        baseline = self._profile_file("commands.md")
        if baseline is None:
            self._add(cid, name, "WARN",
                      "berkas profil `commands.md` tidak ditemukan",
                      "Jalankan `frontenddev:profile` lebih dulu; tanpa baseline, "
                      "perintah verifikasi tidak dapat divonis.")
            return
        stack = str(self.briefs[0]["fm"].get("stack", "")).strip()
        adapter = self._adapter_text(stack) or ""
        allowed_cmds = self._commands(baseline) | self._commands(read_section(adapter, "## Commands"))
        problems: List[str] = []
        for b in targets:
            cmds = b["fm"].get("verification", [])
            cmds = [c for c in cmds if isinstance(c, str)] if isinstance(cmds, list) else []
            if not cmds:
                problems.append(f"{b['name']}: `verification` kosong")
            for cmd in cmds:
                norm = " ".join(cmd.split())
                if not any(norm == c or norm.startswith(c + " ") for c in allowed_cmds):
                    problems.append(
                        f"{b['name']}: perintah `{cmd}` bukan perintah `commands.md` profil atau "
                        "`## Commands` adapter (boleh ditambah argumen path/pola di belakangnya)"
                    )
            if stack in SVELTE_STACKS:
                joined = " ".join(cmds)
                if re.search(r"\btsc\b", joined) and "svelte-check" not in joined:
                    problems.append(
                        f"{b['name']}: repo Svelte memakai `tsc` tanpa `svelte-check` — "
                        "`tsc --noEmit` tidak memeriksa berkas `.svelte`, jadi verifikasi "
                        "penutupnya hijau semu"
                    )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} perintah tidak sah",
                      "Salin perintah dari `commands.md` profil atau "
                      "`## Commands` adapter; dilarang mengetik dari ingatan stack lain.",
                      problems)
        else:
            self._add(cid, name, "PASS", "seluruh perintah verifikasi dikenali profil")

    def _check_k_naming(self) -> None:
        cid, name = "K", "Penamaan lintas stack"
        targets = self.active()
        if not targets:
            self._add(cid, name, "SKIP", "seluruh brief terkunci")
            return
        problems: List[str] = []
        for b in targets:
            stack = str(b["fm"].get("stack", "")).strip()
            if stack not in REACT_STACKS | SVELTE_STACKS:
                problems.append(
                    f"{b['name']}: `stack: {stack or '(kosong)'}` di luar adapter yang ada "
                    f"({sorted(REACT_STACKS | SVELTE_STACKS)})"
                )
                continue
            for f in self._files(b):
                if stack in REACT_STACKS:
                    if f.endswith(".svelte"):
                        problems.append(f"{b['name']}: berkas `.svelte` di stack `{stack}` → `{f}`")
                    if "/$lib/" in f or f.startswith("src/lib/features/"):
                        problems.append(
                            f"{b['name']}: letak khas SvelteKit di stack `{stack}` → `{f}`"
                        )
                else:
                    if f.endswith(".tsx"):
                        problems.append(f"{b['name']}: berkas `.tsx` di stack `{stack}` → `{f}`")
                    if REACT_HOOK_FILE.search("/" + f):
                        problems.append(
                            f"{b['name']}: penamaan hook React `use*.ts` di stack `{stack}` → `{f}`"
                        )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} nama berkas silang stack",
                      "Ikuti `## Layer taxonomy` adapter `stack` brief; satu taskdir "
                      "hidup di bawah satu Stack ID.", problems)
        else:
            self._add(cid, name, "PASS", "penamaan berkas konsisten dengan stack")

    def _check_o_overlap(self) -> None:
        cid, name = "O", "Tumpang tindih berkas antar unit"
        owners: Dict[str, List[str]] = {}
        for b in self.briefs:
            if b["status"] == "BLOCKED":
                continue  # suntingannya sudah di-rollback; remedinya pemilik baru berkas itu
            for f in self._files(b):
                owners.setdefault(f, []).append(b["nn"])
        deps = {
            b["nn"]: set(str(d).strip() for d in b["fm"].get("depends_on", []) or [])
            for b in self.briefs
        }

        def connected(a: str, c: str) -> bool:
            seen: Set[str] = set()

            def reach(src: str, dst: str) -> bool:
                if src == dst:
                    return True
                if src in seen:
                    return False
                seen.add(src)
                return any(reach(d, dst) for d in deps.get(src, set()))

            return reach(a, c) or reach(c, a)

        problems: List[str] = []
        for f, nns in owners.items():
            if len(nns) < 2:
                continue
            for i in range(len(nns)):
                for j in range(i + 1, len(nns)):
                    if not connected(nns[i], nns[j]):
                        problems.append(
                            f"`{f}` disentuh unit {nns[i]} dan {nns[j]} yang tidak "
                            "terhubung `depends_on` — urutan suntingannya tidak tertentu"
                        )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} tumpang tindih tak berurut",
                      "Hubungkan kedua unit lewat `depends_on`, atau pindahkan berkas "
                      "itu ke satu unit saja.", problems)
        else:
            self._add(cid, name, "PASS", "tumpang tindih berkas selalu berurut")

    def _check_e_contract(self) -> None:
        cid, name = "E", "Cakupan terhadap CONTRACT.md"
        if not self.contract_mode:
            self._add(cid, name, "SKIP", "mode non-KONTRAK (`--contract` tidak dipakai)")
            return
        contract = self.taskdir / "CONTRACT.md"
        if not contract.is_file():
            self._add(cid, name, "FAIL", "`CONTRACT.md` tidak ada di taskdir",
                      "Jalankan `frontenddev:contract` lebih dulu, atau lepas `--contract` "
                      "untuk lane MINOR.")
            return
        text = contract.read_text(encoding="utf-8")
        section = read_section(text, "## 1. Files Touched")
        declared: Set[str] = set()
        for line in section.splitlines():
            for m in re.finditer(r"`([^`]+\.[a-z]+)`", line):
                declared.add(m.group(1).strip())
            m = re.match(r"^\s*[-*]\s+([^\s`|]+\.[a-z]+)\s*$", line)
            if m:
                declared.add(m.group(1).strip())
        if not declared:
            self._add(cid, name, "FAIL",
                      "`# Execution ## 1. Files Touched` kosong atau tidak terbaca",
                      "Tulis daftar berkas kontrak sebagai butir ber-backtick di seksi itu.")
            return
        union: Set[str] = set()
        for b in self.briefs:
            union.update(self._files(b))
        stray = sorted(f for f in union if f not in declared and not TEST_FILE.search(f))
        unclaimed = sorted(declared - union)
        problems: List[str] = []
        if stray:
            problems.append(
                "berkas di `files_touched` tetapi di luar Files Touched kontrak: "
                + ", ".join(stray)
            )
        if unclaimed:
            problems.append(
                "berkas dijanjikan kontrak tetapi tidak diklaim brief mana pun: "
                + ", ".join(unclaimed)
            )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} ketidakcocokan cakupan",
                      "Lengkapi `CONTRACT.md § Execution ## 1. Files Touched` lewat "
                      "`frontenddev:contract`, lalu tambahkan unit penampung dengan "
                      "`frontenddev:plan` mode APPEND.", problems)
        else:
            self._add(cid, name, "PASS",
                      f"{len(declared)} berkas kontrak tertutup union brief")

    def _drift_rows(self) -> List[Dict[str, str]]:
        """Baca baris Drift berstruktur profil beserta resep `deteksi`-nya."""
        section = self._profile_file("drift.md")
        if section is None:
            return []
        rows: List[Dict[str, str]] = []
        for line in section.splitlines():
            m = DRIFT_ROW.match(line)
            if m:
                g = m.groupdict()
                rows.append({
                    "warisan": (g["warisan"] or g["warisan2"] or "").strip(),
                    "modern": (g["modern"] or g["modern2"] or "").strip(),
                    "pola": (g["pola"] or g["pola2"] or "").strip(),
                    "glob": (g["glob"] or g["glob2"] or "").strip(),
                })
        return rows

    def _check_c_acceptance(self) -> None:
        cid, name = "C", "Cakupan Acceptance Criteria"
        if not self.contract_mode:
            self._add(cid, name, "SKIP", "mode non-KONTRAK (`--contract` tidak dipakai)")
            return
        contract = self.taskdir / "CONTRACT.md"
        if not contract.is_file():
            self._add(cid, name, "FAIL", "`CONTRACT.md` tidak ada di taskdir",
                      "Jalankan `frontenddev:contract` lebih dulu.")
            return
        section = read_section(contract.read_text(encoding="utf-8"),
                               "## 5. Acceptance Criteria")
        declared: List[str] = []
        auto: Set[str] = set()
        for line in section.splitlines():
            m = re.match(r"^\|\s*`?(AC-\d+)`?\s*\|(.*)$", line.strip())
            if not m:
                continue
            declared.append(m.group(1))
            if "test otomatis" in m.group(2).lower():
                auto.add(m.group(1))
        if not declared:
            self._add(cid, name, "FAIL",
                      "`# Execution ## 5. Acceptance Criteria` kosong atau tidak terbaca",
                      "Tulis tabel `AC-{n} | Skenario | Cara verifikasi | Sumber` di seksi itu.")
            return
        expected = [f"AC-{i}" for i in range(1, len(declared) + 1)]
        problems: List[str] = []
        if declared != expected:
            problems.append(
                f"penomoran AC {declared} bukan seri berurutan dari `AC-1` "
                f"(diharapkan {expected})"
            )
        claims: Dict[str, List[str]] = {}
        for b in self.briefs:
            covers = b["fm"].get("covers", [])
            covers = [str(c).strip() for c in covers] if isinstance(covers, list) else []
            for c in covers:
                claims.setdefault(c, []).append(b["nn"])
        for ghost in sorted(set(claims) - set(declared)):
            problems.append(
                f"brief unit {claims[ghost]} mengklaim `{ghost}` yang tidak ada di "
                "`CONTRACT.md`"
            )
        for ac in declared:
            if ac not in claims:
                problems.append(
                    f"`{ac}` tidak diklaim `covers:` brief mana pun — kriteria itu "
                    "tidak akan pernah dikerjakan"
                )
                continue
            if ac in auto:
                landed = False
                for nn in claims[ac]:
                    brief = next(b for b in self.briefs if b["nn"] == nn)
                    tests = [f for f in self._files(brief) if TEST_FILE.search(f)]
                    if not tests:
                        continue
                    for t in tests:
                        path = self.root / t
                        if path.is_file() and re.search(
                            rf"\b{re.escape(ac)}\b", path.read_text(encoding="utf-8", errors="ignore")
                        ):
                            landed = True
                            break
                        if not path.is_file():
                            landed = True  # berkas test masih CREATE; ditagih di penutup
                            break
                    if landed:
                        break
                if not landed:
                    problems.append(
                        f"`{ac}` bertanda `test otomatis` tetapi brief pengklaimnya "
                        f"{claims[ac]} tidak punya berkas test yang menyebut nomor itu"
                    )
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} cacat keterlacakan",
                      "Samakan `covers:` brief dengan tabel Acceptance Criteria kontrak; "
                      "AC tanpa pengklaim ditambahkan lewat `plan` mode APPEND, dan "
                      "rujukan hantu dihapus.", problems)
        else:
            self._add(cid, name, "PASS",
                      f"{len(declared)} AC seluruhnya diklaim brief")

    def _check_p_drift(self) -> None:
        cid, name = "P", "Pola Acuan vs Drift profil"
        targets = self.active()
        if not targets:
            self._add(cid, name, "SKIP", "seluruh brief terkunci")
            return
        rows = self._drift_rows()
        if not rows:
            self._add(cid, name, "SKIP",
                      "profil tidak memuat baris Drift ber-resep `deteksi`")
            return
        problems: List[str] = []
        for b in targets:
            haystack = "\n".join(
                read_section(b["body"], h) for h in REQUIRED_SECTIONS[2:4]
            )
            for row in rows:
                try:
                    pattern = re.compile(row["pola"])
                except re.error:
                    pattern = re.compile(re.escape(row["pola"]))
                for line in haystack.splitlines():
                    if pattern.search(line):
                        problems.append(
                            f"{b['name']}: seksi 3/4 memuat pola warisan "
                            f"`{row['warisan']}` \u2192 ganti dengan `{row['modern']}` "
                            f"(baris: {line.strip()[:70]})"
                        )
                        break
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} rujukan pola warisan",
                      "Ganti Pola Acuan di seksi 3 dan langkah di seksi 4 dengan pola "
                      "pengganti pada baris Drift yang sama; brief yang menunjuk preseden "
                      "menyesatkan membuat implementor menirunya dengan sah.", problems)
        else:
            self._add(cid, name, "PASS",
                      f"nol rujukan ke {len(rows)} pola warisan yang tercatat profil")

    def _check_g_fulfills(self) -> None:
        """Tiap `SC-{n}` akar dipikul minimal satu brief lewat `fulfills`; nol rujukan hantu.

        Dinilai atas **seluruh** brief, termasuk yang terkunci: janji akar yang
        sudah dipikul brief `DONE` tetap terpikul. Tanpa check ini rantai dapat
        tuntas — seluruh brief `DONE`, review hijau — tanpa satu pun unit yang
        pernah ditugasi memenuhi sebuah butir Success Criteria.
        """
        cid, name = "G", "Fulfills vs Success Criteria"
        task = self.taskdir / "TASK.md"
        sc = list(success_criteria(task))
        if not sc:
            self._add(cid, name, "FAIL", "`TASK.md` tanpa butir `SC-{n}` terbaca",
                      "Kunci akar lewat `frontenddev:task`; brief tanpa akar tidak punya ukuran selesai.")
            return
        claims: Dict[str, List[str]] = {}
        problems: List[str] = []
        for b in self.briefs:
            value = b["fm"].get("fulfills", [])
            value = [str(v).strip() for v in value] if isinstance(value, list) else []
            if not value and not b["locked"]:
                problems.append(f"{b['name']}: `fulfills` kosong — unit yang tidak memikul satu pun "
                                "`SC-{n}` adalah perluasan lingkup")
            for v in value:
                claims.setdefault(v, []).append(b["nn"])
        all_ids = set(sc_ids(task.read_text(encoding="utf-8"))) if task.is_file() else set()
        locked = {b["nn"] for b in self.briefs if b["locked"]}
        for ghost in sorted(set(claims) - set(sc)):
            owners = claims[ghost]
            if ghost in all_ids and all(nn in locked for nn in owners):
                continue  # SC digugurkan amandemen sesudah brief terkunci memikulnya — sah
            problems.append(f"brief unit {owners} mengklaim `{ghost}` yang tidak ada (atau sudah gugur) di `TASK.md`")
        for s_id in sc:
            if s_id not in claims:
                problems.append(f"`{s_id}` tidak dipikul brief mana pun — janji akar tidak akan dikerjakan")
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} cacat keterpikulan",
                      "Isi `fulfills:` tiap brief dengan `SC-{n}` yang dipikulnya; SC tanpa pemikul "
                      "ditambahkan unitnya, rujukan hantu dihapus.", problems)
        else:
            self._add(cid, name, "PASS", f"{len(sc)} SC seluruhnya dipikul brief")

    def _check_m_remedies(self) -> None:
        """`remedies: "NN"` menunjuk brief `BLOCKED` bernomor lebih kecil; plafon 2 remedi per unit asal.

        Remedi atas remedi dihitung ke unit asal paling hulu: unit yang gagal
        tiga kali membuktikan cacatnya ada di kontrak, bukan di brief, dan brief
        keempat hanya menambah satu commit `BLOCKED` lagi. Plafon bertambah satu per
        re-entry kontrak: `reopen … CONTRACT`, atau eskalasi dari `HOTFIX_MINOR`
        (satu-satunya eskalasi yang menambah hop CONTRACT).
        """
        cid, name = "M", "Remedi & plafon per unit asal"
        by_nn = {b["nn"]: b for b in self.briefs}
        problems: List[str] = []
        origin_of: Dict[str, str] = {}
        for b in self.briefs:
            target = str(b["fm"].get("remedies", "") or "").strip()
            if not target:
                continue
            src = by_nn.get(target)
            if src is None:
                problems.append(f"{b['name']}: `remedies: {target}` menunjuk unit yang tidak ada")
                continue
            if target >= b["nn"]:
                problems.append(f"{b['name']}: `remedies: {target}` tidak lebih kecil dari `{b['nn']}`")
                continue
            if src["status"] != "BLOCKED":
                problems.append(f"{b['name']}: `remedies: {target}` menunjuk brief berstatus `{src['status']}`, "
                                "bukan `BLOCKED`")
                continue
            origin_of[b["nn"]] = origin_of.get(target, target)
        counts: Dict[str, int] = {}
        for origin in origin_of.values():
            counts[origin] = counts.get(origin, 0) + 1
        slug = self.taskdir_rel.rsplit("/", 1)[-1].split("-", 1)[-1]
        try:
            log = subprocess.check_output(["git", "-C", str(self.root), "log", "--format=%s", "--",
                                           f"{self.taskdir_rel}/TASK.md"], stderr=subprocess.DEVNULL,
                                          universal_newlines=True)
        except Exception:
            log = ""
        # Re-entry kontrak: reopen yang membuka CONTRACT, atau eskalasi dari HOTFIX_MINOR yang
        # menambah hop CONTRACT (rute resmi remedi ketiga lane MINOR).
        contract_reentries = sum(1 for l in log.splitlines()
                                 if re.match(rf"^docs\({re.escape(slug)}\): reopen [A-Z ]*\bCONTRACT\b", l)
                                 or re.match(rf"^docs\({re.escape(slug)}\): eskalasi lane HOTFIX_MINOR → ", l))
        for origin, n in sorted(counts.items()):
            # Remedi ketiga dan seterusnya sah hanya sesudah kontrak dibuka ulang (satu per re-entry).
            if n > 2 + contract_reentries:
                problems.append(f"unit asal `{origin}` punya {n} brief remedi — plafon 2; eskalasi ke "
                                "Gate Contract (`chain.py reopen --row CONTRACT`) alih-alih remedi ketiga")
        if problems:
            self._add(cid, name, "FAIL", f"{len(problems)} cacat remedi",
                      "Perbaiki `remedies`; remedi ketiga atas unit yang sama dilarang.", problems)
        elif counts:
            self._add(cid, name, "PASS", f"{sum(counts.values())} remedi atas {len(counts)} unit asal")
        else:
            self._add(cid, name, "SKIP", "tidak ada brief remedi")

    # ---------------------------------------------------------------- output

    def format_text(self) -> str:
        if self.fatal:
            return f"BRIEF VALIDATION: [FAIL] {self.fatal}"
        failed = [r for r in self.results if r["status"] == "FAIL"]
        passed = [r for r in self.results if r["status"] == "PASS"]
        warned = [r for r in self.results if r["status"] == "WARN"]
        skipped = [r for r in self.results if r["status"] == "SKIP"]
        label = "FAIL" if failed else ("PASS (WARN)" if warned else "PASS")
        mode = f"brief {self.brief_filter}" if self.brief_filter else "batch"
        locked = len([b for b in self.briefs if b["locked"]])
        lines = [
            f"BRIEF VALIDATION: {mode} [{label}] "
            f"({len(passed)} pass / {len(failed)} fail / {len(warned)} warn / "
            f"{len(skipped)} skip)",
            f"Taskdir: {self.taskdir_rel} — {len(self.briefs)} brief "
            f"({locked} terkunci, {len(self.briefs) - locked} aktif)",
        ]
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<34} : {r['status']} ({r['summary']})")
            for d in r["details"][:12]:
                lines.append(f"      - {d}")
            if len(r["details"]) > 12:
                lines.append(f"      - ... {len(r['details']) - 12} lagi")
            if r["status"] in ("FAIL", "WARN") and r["action"]:
                lines.append(f"    * Tindakan: {r['action']}")
        return "\n".join(lines)

    def to_json(self) -> str:
        failed = [r for r in self.results if r["status"] == "FAIL"]
        return json.dumps({
            "status": "FAIL" if (failed or self.fatal) else "PASS",
            "fatal": self.fatal,
            "taskdir": self.taskdir_rel,
            "mode": f"brief {self.brief_filter}" if self.brief_filter else "batch",
            "brief_count": len(self.briefs),
            "locked_count": len([b for b in self.briefs if b["locked"]]),
            "checks": self.results,
        }, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Frontend Brief Validator")
    parser.add_argument("--taskdir", required=True,
                        help="path taskdir relatif root repo, "
                             "misal frontenddev/docs/2509051200-order-export")
    parser.add_argument("--brief", default=None,
                        help="batasi predikat rencana ke satu unit (NN)")
    parser.add_argument("--contract", action="store_true",
                        help="aktifkan Check E & C terhadap CONTRACT.md (lane non-MINOR)")
    parser.add_argument("--max-files", type=int, default=5,
                        help="kuota berkas non-test per unit (default 5)")
    parser.add_argument("--profile-dir", default=None, dest="profile_dir",
                        help="direktori profil, default .claude/profile/frontenddev (lokasi lama .claude/profile hanya dibaca untuk MIGRATE)")
    parser.add_argument("--root", default=None, help="root repo target")
    parser.add_argument("--json", action="store_true", help="keluaran JSON")
    args = parser.parse_args()

    validator = BriefValidator(
        taskdir=args.taskdir,
        root=Path(args.root) if args.root else None,
        brief_filter=args.brief,
        contract_mode=args.contract,
        max_files_per_unit=args.max_files,
        profile_dir=args.profile_dir,
    )
    ok = validator.run_all()
    print(validator.to_json() if args.json else validator.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
