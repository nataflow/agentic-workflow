#!/usr/bin/env python3
"""Brief Batch Validator.

Menegakkan seluruh predikat **mekanis** rantai brief (`brief-*.md`) satu taskdir
dalam satu lintasan: kelengkapan struktur, sapuan placeholder & verifikasi,
konsistensi lintas-brief, cakupan dua sumbu (`Covers:`/`Fulfills:`), pendaratan
migrasi, derivasi `risk:`, langit-langit slicing, realitas berkas test, dan
resolusi anchor terhadap laci `.explore/` maupun disk.

Dua mode:

* **batch** (bawaan) — seluruh `brief-*.md` taskdir dinilai kolektif. Dipakai
  di Fase 4 sebagai pengganti pemeriksaan A-K yang dikerjakan main loop.
* **per-brief** (`--brief NN`) — hanya berkas itu, memakai predikat yang dapat
  divonis tanpa melihat batch. Dipakai di Fase 3 sebagai gerbang tepat sesudah
  satu brief ditulis, supaya cacat sistematis tidak tereplikasi ke brief
  berikutnya.

Seluruh kegagalan dilaporkan **sekaligus**; tidak ada penghentian di kegagalan
pertama, sehingga satu putaran perbaikan cukup untuk menutup seluruh temuan.

Brief `DONE`/`BLOCKED`/`SUPERSEDED` dilewati predikat **rencana**; `DONE`/`BLOCKED`
tetap ditagih predikat **cakupan**: remediasi predikat rencana atasnya berarti
memalsukan riwayat brief yang kodenya sudah mendarat, sementara
`Covers:`/`Fulfills:`/`Produces`-nya masih menopang rantai keterlacakan. Klaim
brief `SUPERSEDED` tidak dihitung — penggantinya yang memikul. `--include-locked` menagih keduanya; ia alat audit,
bukan gerbang.

State ronde self-review dimateraikan ke laci taskdir: `--open-round` sebelum
dispatch (snapshot brief), `--record-round` sesudah balikan, `--review-state`
untuk membacanya. Plafonnya per **generasi batch** — himpunan berkas brief yang
ada — sehingga brief yang ditambahkan sesudah plafon habis tetap dapat direview.

Predikat semantik sengaja tidak ditangani di sini — keselarasan aturan bisnis
`BR-{n}`, pendaratan 4 pilar kontrak PRD, dan kualitas snippet `## Steps` milik
subagent `brief-reviewer`.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Resolver profil `.claude/profile/backenddev/` tinggal di
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    resolve_profile_dir,
)
from brief_status import LOCKED as LOCKED_STATUSES  # noqa: E402

# ---------------------------------------------------------------------------
# Konstanta kanonik
#
# Sepuluh seksi wajib dan lima placeholder terlarang bersumber dari
# `../templates/brief-template.md` bagian 1 dan bagian 2 butir 4. Berkas itu
# rumah kanoniknya; daftar di sini salinan penegak, bukan definisi tandingan.
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = [
    "Objective",
    "Interfaces",
    "File scope",
    "Out of scope",
    "Steps",
    "Migration",
    "Mirrored paths",
    "Risk & rollback",
    "Work status",
    "Analysis trace",
]

# Brief tidak pernah memikul kedua seksi ini: ketidakpastian tuntas sebelum brief
# ditulis, dan verifikasi ditunda ke penutup taskdir.
FORBIDDEN_SECTIONS = ["Open questions", "Verification"]

REQUIRED_FRONTMATTER = ["title", "source", "risk", "status", "commit_message"]

VALID_RISKS = ["BREAKING", "MAJOR", "MINOR"]
RISK_ORDER = {"MINOR": 1, "MAJOR": 2, "BREAKING": 3}

PLACEHOLDERS = [
    "TODO",
    "TBD",
    "diisi nanti",
    "tambahkan error handling seperlunya",
    "tulis test untuk yang di atas",
]

# Penanda verifikasi yang dilarang mendarat di brief mana pun.
VERIFICATION_MARKERS = ["— verifikasi:", "-- verifikasi:", "— verifikasi :"]

BUILD_TEST_COMMANDS = [
    "mvn test", "mvn verify", "mvn clean", "./mvnw", "gradle test", "./gradlew",
    "npm test", "npm run test", "npm run build", "yarn test", "bun test",
    "go test", "go build", "pytest", "cargo test", "cargo build",
    "php artisan test", "phpunit", "dotnet test", "make test", "make build",
]

# Langit-langit slicing (`../references/slicing-and-scan.md` bagian 3A butir 3).
MAX_STEPS = 5
MAX_CODE_FILES = 4

# Pola DDL destruktif yang memaksa `risk: BREAKING`.
DESTRUCTIVE_DDL = [
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bDROP\s+COLUMN\b", "DROP COLUMN"),
    (r"\bTRUNCATE\b", "TRUNCATE"),
    (r"\bRENAME\s+COLUMN\b", "RENAME COLUMN"),
    (r"\bALTER\s+COLUMN\b[^;\n]*\bTYPE\b", "ALTER COLUMN ... TYPE"),
]

# Kata yang tak pernah menjadi simbol anchor; dibuang sebelum resolusi.
ANCHOR_STOPWORDS = {
    "dan", "atau", "pada", "baris", "sesudah", "sebelum", "method", "class",
    "field", "tepat", "dalam", "untuk", "yang", "dari", "ke", "di", "itu",
    "the", "and", "after", "before", "line", "new", "add", "set",
}


# Baris berbentuk **deklarasi** lintas stack yang didukung plugin ini (Rust, Go,
# Java/Spring, Node, Bun, PHP). Dipakai Check N untuk membedakan anchor yang
# menunjuk titik sisip dari anchor yang sekadar menunjuk penyebutan simbol di
# tengah berkas. Heuristik ini sengaja longgar — vonis kegagalannya `WARN`,
# bukan `FAIL`, karena bentuk deklarasi tiap stack tidak pernah tertangkap penuh
# satu regex.
DECLARATION_RE = re.compile(
    r"(?:^|\s)(?:"
    r"fn|func|def|class|struct|enum|impl|trait|interface|type|record|"
    r"function|const|let|var|val|object|module|namespace|"
    r"public|private|protected|internal|static|final|abstract|override|"
    r"export|declare|async|pub"
    r")\b"
)

# Laci kerja taskdir; sudah dikecualikan tiap gerbang git di rantai.
LACI = ".explore"
REVIEW_STATE = "brief-review-state.json"

# Plafon ronde **per generasi batch**, bukan per taskdir. Satu generasi adalah
# himpunan berkas brief yang ada di taskdir; ia berganti hanya saat brief
# **ditambahkan** — re-entry `analyst`, berkas yatim `architect`, atau brief
# perbaikan. Menyunting isi brief tidak pernah membuka generasi baru, sehingga
# plafon tidak dapat diakali dengan mengedit.
#
# Plafon per-taskdir yang lama membuat brief yang lahir sesudah ronde kedua
# mustahil direview: `--review-state` membalas "plafon habis" atas berkas yang
# belum pernah dilihat reviewer mana pun. Plafon keras taskdir tetap ada supaya
# penambahan brief berulang tidak jadi loop tanpa batas.
MAX_ROUNDS = 2
MAX_ROUNDS_TASKDIR = 4

# Brief terkunci (`LOCKED_STATUSES`, dari `_common/brief_status.py`): sudah
# dieksekusi `code-implementor` (`DONE`/`BLOCKED`) atau digantikan
# (`SUPERSEDED`). Predikat yang menilai *rencana* tidak berlaku atasnya:
# statusnya memang bukan READY, berkas `create`-nya memang sudah ada, dan
# anchornya menunjuk kode yang sudah berpindah. Yang tetap berlaku predikat
# *cakupan* — `Covers:`, `Fulfills:`, `Produces` — karena rantai
# keterlacakannya tidak gugur oleh eksekusi; kecuali brief `SUPERSEDED`, yang
# klaimnya dipikul penggantinya.


def _norm_heading(text: str) -> str:
    """Samakan bentuk heading supaya perbandingan tidak tergelincir spasi/kapital."""
    return re.sub(r"\s+", " ", text).strip().lower()


def _is_test_path(path: str, test_hint: Optional[str] = None) -> bool:
    """Vonis apakah sebuah path berkas test.

    Resep penamaan dibaca dari baris `test:` `.claude/profile/backenddev/code-conventions.md`
    bila tersedia (`test_hint`); bila absen, turun ke heuristik nama yang berlaku
    lintas stack. Heuristik ini hanya memisahkan berkas test dari berkas kode
    untuk langit-langit slicing dan Check I — ia tidak pernah menuntut nama
    tertentu, karena penamaan berkas test milik brief, bukan PRD.
    """
    low = path.lower()
    if test_hint:
        stem = re.sub(r"[^a-z0-9]+", "", test_hint.lower())
        if stem and stem in re.sub(r"[^a-z0-9]+", "", low):
            return True
    base = os.path.basename(low)
    return (
        "test" in base
        or "spec" in base
        or "/tests/" in low
        or "/test/" in low
        or "__tests__" in low
    )


def _is_migration_path(path: str) -> bool:
    low = path.lower()
    return (
        "migration" in low
        or "migrations" in low
        or bool(re.search(r"\bv\d+__", low))
        or (low.endswith(".sql") and "seed" not in low)
    )


ORM_SCHEMA_TOKEN = re.compile(
    r"^\s*Berkas migrasi:\s*tidak ada\s*[—-]+\s*skema dibentuk ORM\b", re.IGNORECASE | re.MULTILINE
)
ORM_SCHEMA_PROFILE_MARKERS = ("ddl-auto", "hbm2ddl", "synchronize: true", "automigrate", "auto_migrate")


class BriefValidator:
    def __init__(
        self,
        taskdir: str,
        brief: Optional[str] = None,
        risk_ceiling: Optional[str] = None,
        file_scope: Optional[str] = None,
        target_root: Optional[Path] = None,
        include_locked: bool = False,
    ):
        self.include_locked = include_locked
        self.root = (target_root or self._find_repo_root()).resolve()
        self.taskdir_arg = taskdir
        self.taskdir = self._resolve_taskdir()
        self.brief_filter = (brief or "").strip().lstrip("#") or None
        _risk = (risk_ceiling or "").strip().upper()
        self.risk_ceiling_arg = None if _risk in ("", "—", "-") else _risk
        self.file_scope_arg = (file_scope or "").strip() or None

        self.results: List[Dict[str, Any]] = []
        self.briefs: List[Dict[str, Any]] = []
        self.explore_map: Dict[str, Set[str]] = {}
        self.test_hint: Optional[str] = None

    # -- infrastruktur -----------------------------------------------------

    def _find_repo_root(self) -> Path:
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            ).strip()
            if out and os.path.isdir(out):
                return Path(out)
        except Exception:
            pass
        return Path.cwd()

    def _resolve_taskdir(self) -> Path:
        td = Path(self.taskdir_arg)
        return td if td.is_absolute() else self.root / td

    @staticmethod
    def _read(path: Path) -> Optional[str]:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return None

    def _add(self, cid: str, name: str, status: str, summary: str,
             action: str = "", details: Optional[List[str]] = None):
        self.results.append({
            "id": cid,
            "name": name,
            "status": status,
            "summary": summary,
            "action": action,
            "details": details or [],
        })

    # -- state ronde self-review ------------------------------------------
    #
    # Plafon ronde dimateraikan ke disk, bukan disimpan di memori main loop.
    # `plan` yang dipanggil ulang — vonis `NOT_READY_FOR_IMPLEMENTATION` dari
    # analyst, eskalasi chain, atau konteks yang ter-compact — membaca hitungan
    # yang sama, sehingga plafonnya berlaku **per taskdir**, bukan per invokasi.
    # Tanpa materai ini plafon 2 ronde tidak pernah benar-benar mengikat: tiga
    # kali masuk `plan` menghasilkan enam ronde tanpa satu pun aturan dilanggar.

    def _state_path(self) -> Path:
        return self.taskdir / LACI / REVIEW_STATE

    def _brief_digests(self) -> Dict[str, str]:
        """Peta nama brief -> sha1 isinya, diambil dari disk saat ini."""
        out: Dict[str, str] = {}
        for p in sorted(self.taskdir.glob("brief-*.md")):
            try:
                out[p.name] = hashlib.sha1(p.read_bytes()).hexdigest()
            except Exception:
                continue
        return out

    def _generation_key(self) -> str:
        """Identitas generasi batch: himpunan **nama** berkas brief.

        Isi brief sengaja tidak ikut: menyunting brief adalah justru yang
        diperbaiki di antara dua ronde, dan generasi yang berganti tiap suntingan
        membuat plafon tidak pernah mengikat.
        """
        names = sorted(self._brief_digests())
        return hashlib.sha1("\n".join(names).encode("utf-8")).hexdigest()[:12]

    def _load_state(self) -> Dict[str, Any]:
        text = self._read(self._state_path())
        data: Dict[str, Any] = {}
        if text:
            try:
                data = json.loads(text)
            except Exception:
                data = {}
        # Migrasi bentuk lama (`{"rounds": n, "history": [...]}`) ke bentuk
        # bergenerasi, supaya taskdir yang sudah berjalan tidak kehilangan
        # hitungannya dan tidak pula mendapat jatah gratis.
        if "generations" not in data:
            legacy_rounds = int(data.get("rounds") or 0)
            legacy_hist = data.get("history") or []
            data = {
                "total_rounds": legacy_rounds,
                "generations": (
                    {self._generation_key(): {"rounds": legacy_rounds, "history": legacy_hist}}
                    if legacy_rounds else {}
                ),
                "open": None,
            }
        data.setdefault("total_rounds", 0)
        data.setdefault("generations", {})
        data.setdefault("open", None)
        return data

    def _write_state(self, data: Dict[str, Any]):
        path = self._state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def read_round_state(self) -> Dict[str, Any]:
        """Ringkas state ronde untuk generasi batch yang aktif sekarang."""
        data = self._load_state()
        gen = self._generation_key()
        bucket = data["generations"].get(gen) or {"rounds": 0, "history": []}
        return {
            "generation": gen,
            "rounds": int(bucket.get("rounds") or 0),
            "history": bucket.get("history") or [],
            "total_rounds": int(data.get("total_rounds") or 0),
            "open": data.get("open"),
            "generations_seen": len(data["generations"]),
        }

    def open_round(self) -> Dict[str, Any]:
        """Buka ronde: materaikan snapshot brief **pada saat dispatch**.

        Snapshot diambil di sini, bukan saat ronde ditutup. Perbaikan `BLOCKER`
        dikerjakan **sesudah** balikan reviewer datang; snapshot yang diambil saat
        penutupan sudah memuat perbaikan itu, sehingga daftar "brief berubah"
        ronde berikutnya selalu kosong dan slot `{brief_berubah}` terpaksa diisi
        dari ingatan. Diambil di sini, ia selalu benar tanpa bergantung pada
        urutan pemanggilan.
        """
        data = self._load_state()
        gen = self._generation_key()
        bucket = data["generations"].setdefault(gen, {"rounds": 0, "history": []})
        data["open"] = {
            "generation": gen,
            "round": int(bucket["rounds"]) + 1,
            "snapshot": self._brief_digests(),
        }
        self._write_state(data)
        return data["open"]

    def record_round(self, verdict: str, changed: List[str]) -> Dict[str, Any]:
        data = self._load_state()
        gen = self._generation_key()
        bucket = data["generations"].setdefault(gen, {"rounds": 0, "history": []})
        opened = data.get("open") or {}
        # Ronde yang tidak pernah dibuka tetap dimateraikan — snapshot-nya
        # diambil sekarang sebagai jalan terakhir, dan penyimpangannya dicatat.
        snapshot = opened.get("snapshot") if opened.get("generation") == gen else None
        bucket["rounds"] = int(bucket["rounds"]) + 1
        bucket["history"].append({
            "round": bucket["rounds"],
            "verdict": verdict,
            "changed_briefs": changed,
            "snapshot": snapshot if snapshot is not None else self._brief_digests(),
            "snapshot_at_dispatch": snapshot is not None,
        })
        data["total_rounds"] = int(data.get("total_rounds") or 0) + 1
        data["open"] = None
        self._write_state(data)
        return self.read_round_state()

    def changed_since_last_round(self) -> List[str]:
        """Brief yang berubah sejak ronde terakhir **diberangkatkan**.

        Dipakai menghidrasi slot `{brief_berubah}` dispatch ronde 2. Pembandingnya
        snapshot saat dispatch ronde sebelumnya, bukan waktu tulis berkas state:
        brief yang tidak tersentuh sejak itu byte-identik dengan yang sudah
        dinilai, dan menilainya ulang tidak menambah satu pun informasi — tetapi
        brief yang diperbaiki karena `BLOCKER` wajib muncul di sini.
        """
        state = self.read_round_state()
        current = self._brief_digests()
        history = state["history"]
        if not history:
            return sorted(current)
        prev = history[-1].get("snapshot") or {}
        return sorted(n for n, d in current.items() if prev.get(n) != d)

    def rounds_left(self) -> Tuple[int, str]:
        """Sisa jatah ronde generasi aktif beserta alasan bila nol."""
        state = self.read_round_state()
        if state["total_rounds"] >= MAX_ROUNDS_TASKDIR:
            return 0, (
                f"plafon keras taskdir habis ({state['total_rounds']}/{MAX_ROUNDS_TASKDIR} ronde "
                f"lintas {state['generations_seen']} generasi batch)"
            )
        left = MAX_ROUNDS - state["rounds"]
        if left <= 0:
            return 0, (
                f"plafon generasi batch ini habis ({state['rounds']}/{MAX_ROUNDS}); "
                f"menambahkan brief baru membuka generasi berikutnya"
            )
        return left, ""

    # -- pemuatan ----------------------------------------------------------

    def load(self) -> Optional[str]:
        """Muat brief, dokumen hulu, laci `.explore`, dan resep penamaan test.

        Mengembalikan pesan galat bila taskdir tidak layak dinilai sama sekali.
        """
        if not self.taskdir.is_dir():
            return f"Taskdir tidak ditemukan: {self.taskdir}"

        paths = sorted(self.taskdir.glob("brief-*.md"))
        if self.brief_filter:
            paths = [p for p in paths if p.name.startswith(f"brief-{self.brief_filter}")]
            if not paths:
                return f"Brief dengan nomor '{self.brief_filter}' tidak ditemukan di {self.taskdir}"
        if not paths:
            return f"Tidak ada berkas brief-*.md di {self.taskdir}"

        for p in paths:
            text = self._read(p)
            if text is None:
                return f"Berkas brief tidak terbaca: {p}"
            self.briefs.append(self._parse_brief(p, text))

        self.task_text = self._read(self.taskdir / "TASK.md")
        self.prd_text = self._read(self.taskdir / "PRD.md")
        self._load_explore()
        self._load_test_hint()
        return None

    def _load_test_hint(self):
        conv = resolve_profile_dir(self.root)[0] / "code-conventions.md"
        text = self._read(conv)
        if not text:
            return
        m = re.search(r"^\s*[-*]?\s*test:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
        if m:
            self.test_hint = m.group(1).strip().strip("`")

    def _load_explore(self):
        """Panen laci `.explore/` jadi peta path -> himpunan simbol anchor.

        Laci itu zona kerja `code-explorer`: tidak di-stage dan tidak di-commit,
        sehingga ia bisa saja kosong (unit disapu main loop, atau taskdir sudah
        dibersihkan). Ketiadaannya bukan kegagalan — resolusi anchor turun ke
        disk. Baris yang dipanen hanya tabel `### File Map`.
        """
        laci = self.taskdir / ".explore"
        if not laci.is_dir():
            return
        for report in sorted(laci.glob("*.md")):
            text = self._read(report)
            if not text:
                continue
            in_map = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("### "):
                    in_map = _norm_heading(stripped[4:]).startswith("file map")
                    continue
                if not in_map or not stripped.startswith("|"):
                    continue
                cols = [c.strip() for c in stripped.strip("|").split("|")]
                if len(cols) < 2 or set(cols[0]) <= set("-: "):
                    continue
                path = cols[0].strip("`").strip()
                if not path or path.lower().startswith("berkas"):
                    continue
                anchors = self.explore_map.setdefault(path, set())
                anchors.add(cols[1])
                # Kolom `Test` ikut dipanen sebagai bukti berkas test yang nyata.
                if len(cols) >= 3:
                    anchors.add(cols[2])

    # -- parsing brief -----------------------------------------------------

    def _parse_brief(self, path: Path, text: str) -> Dict[str, Any]:
        lines = text.splitlines()
        brief: Dict[str, Any] = {
            "path": path,
            "name": path.name,
            "text": text,
            "lines": lines,
            "nn": self._brief_number(path.name),
            "frontmatter": {},
            "sections": {},
            "section_order": [],
        }

        # Frontmatter YAML sederhana di antara sepasang `---`.
        if lines and lines[0].strip() == "---":
            for idx in range(1, len(lines)):
                if lines[idx].strip() == "---":
                    break
                m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", lines[idx])
                if m:
                    brief["frontmatter"][m.group(1)] = m.group(2).strip().strip('"').strip("'")

        # Seksi level-2. Baris di dalam pagar kode diabaikan supaya `## ` yang
        # kebetulan muncul di snippet tidak terbaca sebagai heading.
        current = None
        fenced = False
        for idx, line in enumerate(lines):
            if line.lstrip().startswith("```"):
                fenced = not fenced
            if not fenced and line.startswith("## "):
                current = line[3:].strip()
                brief["section_order"].append(current)
                brief["sections"][_norm_heading(current)] = {
                    "title": current,
                    "start": idx + 1,
                    "body": [],
                }
                continue
            if current is not None:
                brief["sections"][_norm_heading(current)]["body"].append((idx + 1, line))

        brief["covers"], brief["covers_line"] = self._axis_line(brief, "Covers")
        brief["fulfills"], brief["fulfills_line"] = self._axis_line(brief, "Fulfills")
        brief["file_rows"] = self._parse_file_scope(brief)
        brief["steps"] = self._count_steps(brief)
        brief["interfaces"] = self._parse_interfaces(brief)
        brief["status"] = (brief["frontmatter"].get("status") or "").strip().upper()
        brief["locked"] = brief["status"] in LOCKED_STATUSES
        return brief

    @staticmethod
    def _brief_number(name: str) -> Optional[int]:
        m = re.match(r"^brief-(\d{2})-", name)
        return int(m.group(1)) if m else None

    def _section_body(self, brief: Dict[str, Any], title: str) -> List[Tuple[int, str]]:
        sec = brief["sections"].get(_norm_heading(title))
        return sec["body"] if sec else []

    def _section_text(self, brief: Dict[str, Any], title: str) -> str:
        return "\n".join(l for _, l in self._section_body(brief, title))

    def _axis_line(self, brief: Dict[str, Any], axis: str) -> Tuple[Optional[str], Optional[int]]:
        """Ambil baris `Covers:`/`Fulfills:` beserta nomor barisnya.

        Keduanya berdiri di dalam `## Objective`; baris yang mendarat di seksi
        lain tetap ditemukan di sini supaya pesannya bisa menyebut letak
        salahnya, bukan sekadar "tidak ada".
        """
        for lineno, line in enumerate(brief["lines"], start=1):
            m = re.match(rf"^\s*{axis}:\s*(.*)$", line)
            if m:
                return m.group(1).strip(), lineno
        return None, None

    def _parse_file_scope(self, brief: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Baca tabel **File** di `## File scope` jadi baris terstruktur."""
        rows: List[Dict[str, Any]] = []
        in_file_table = False
        for lineno, line in self._section_body(brief, "File scope"):
            stripped = line.strip()
            if stripped.startswith("**"):
                in_file_table = "file" in stripped.lower() and "folder" not in stripped.lower()
                continue
            if not stripped.startswith("|"):
                continue
            cols = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cols) < 4 or set(cols[0]) <= set("-: "):
                continue
            aksi = cols[0].strip("`").lower()
            if aksi not in ("modify", "create"):
                continue
            if not in_file_table:
                # Tabel folder tidak memuat kolom aksi; baris beraksi yang muncul
                # sebelum penanda **File** tetap diperlakukan sebagai baris file.
                in_file_table = True
            rows.append({
                "lineno": lineno,
                "aksi": aksi,
                "path": cols[1].strip("`").strip(),
                "anchor": cols[2].strip().strip("`").strip(),
                "desc": cols[3].strip(),
            })
        return rows

    def _count_steps(self, brief: Dict[str, Any]) -> int:
        """Hitung langkah bernomor tingkat atas di `## Steps`.

        Baris bernomor di dalam pagar kode tidak dihitung: ia isi snippet, bukan
        langkah.
        """
        count = 0
        fenced = False
        for _, line in self._section_body(brief, "Steps"):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            if re.match(r"^\d+\.\s+\S", line):
                count += 1
        return count

    def _parse_interfaces(self, brief: Dict[str, Any]) -> Dict[str, List[str]]:
        out = {"consumes": [], "produces": []}
        for _, line in self._section_body(brief, "Interfaces"):
            m = re.match(r"^\s*[-*]\s*(Consumes|Produces):\s*(.+)$", line, re.IGNORECASE)
            if m:
                out[m.group(1).lower()].append(m.group(2).strip())
        return out

    # -- parsing dokumen hulu ---------------------------------------------

    def _doc_section(self, text: Optional[str], title: str) -> Optional[str]:
        if not text:
            return None
        want = _norm_heading(title)
        capture: List[str] = []
        active = False
        for line in text.splitlines():
            if line.startswith("## "):
                if active:
                    break
                active = _norm_heading(line[3:]) == want
                continue
            if active:
                capture.append(line)
        return "\n".join(capture) if active or capture else None

    def _sc_ids(self) -> Set[str]:
        body = self._doc_section(self.task_text, "Success Criteria")
        return set(re.findall(r"\bSC-(\d+)\b", body)) if body else set()

    def _ac_entries(self) -> Dict[str, str]:
        """Kumpulkan `AC-{n}` PRD beserta cara verifikasinya.

        Nilai yang dikembalikan: `test otomatis`, `qa manual`, atau `lain`.
        """
        body = self._doc_section(self.prd_text, "Acceptance criteria")
        entries: Dict[str, str] = {}
        if not body:
            return entries
        for line in body.splitlines():
            for num in re.findall(r"\bAC-(\d+)\b", line):
                low = line.lower()
                if "test otomatis" in low:
                    kind = "test otomatis"
                elif "qa manual" in low:
                    kind = "qa manual"
                else:
                    kind = entries.get(num, "lain")
                # Baris tabel mengalahkan penyebutan prosa di tempat lain.
                if num not in entries or kind != "lain":
                    entries[num] = kind
        return entries

    def _risk_ceiling(self) -> Optional[str]:
        if self.risk_ceiling_arg:
            return self.risk_ceiling_arg
        if not self.task_text:
            return None
        m = re.search(r"^risk:\s*([A-Za-z_-]+)\s*$", self.task_text, re.MULTILINE)
        if not m:
            return None
        val = m.group(1).strip().upper()
        # `risk: -` menandai lane non-mutasi kode; plafon briefnya MINOR.
        return "MINOR" if val in ("-", "—") else val

    # -- eksekusi ----------------------------------------------------------

    @property
    def plan_briefs(self) -> List[Dict[str, Any]]:
        """Brief yang masih dinilai predikat **rencana**.

        Brief `DONE`/`BLOCKED`/`SUPERSEDED` dikeluarkan: `status:`-nya memang bukan `READY`,
        berkas beraksi `create` miliknya memang sudah ada di disk, dan anchornya
        menunjuk kode yang sudah bergeser oleh brief sesudahnya. Menagihnya
        dengan predikat rencana menuntut remediasi yang berarti **memalsukan
        riwayat brief yang sudah dieksekusi** — satu-satunya jalan keluar yang
        tersisa jadi mengabaikan keluaran skrip, dan gerbang yang rutin
        diabaikan berhenti menggerbangi apa pun.

        Predikat **cakupan** (C, G, H, I, J) tetap menilai seluruh brief yang
        tidak digantikan (`live_briefs`): rantai `Covers:`/`Fulfills:`/`Produces`
        tidak gugur oleh eksekusi.
        """
        if self.include_locked:
            return self.briefs
        return [b for b in self.briefs if not b["locked"]]

    @property
    def live_briefs(self) -> List[Dict[str, Any]]:
        """Brief yang klaim cakupannya dihitung: semua kecuali `SUPERSEDED`."""
        return [b for b in self.briefs if b["status"] != "SUPERSEDED"]

    def run_all(self) -> bool:
        single = self.brief_filter is not None

        locked = [b for b in self.briefs if b["locked"]]
        if locked and not self.include_locked:
            self._add(
                "—", "Brief Terkunci", "LOCKED",
                f"{len(locked)} brief sudah dieksekusi; predikat rencana dilewati atasnya",
                "Jalankan ulang dengan `--include-locked` hanya untuk audit. "
                "Pekerjaan susulan atas brief ini ditampung brief bernomor baru "
                "(`scaffold_brief.py --write-matrix --append`), bukan penulisan ulang.",
                [f"{b['name']}: `{b['status']}`" for b in locked],
            )

        if not self.plan_briefs:
            self._add("—", "Batch Aktif", "LOCKED",
                      "nol brief berstatus READY; seluruh brief taskdir sudah dieksekusi",
                      "Predikat rencana tidak punya sasaran. Tambahkan brief baru bila "
                      "masih ada pekerjaan, atau tutup taskdir lewat `architect`.")

        self._check_struct()
        self._check_placeholder()
        self._check_verification()
        self._check_slicing()
        self._check_anchor()
        self._check_anti_patterns()
        self._check_test_reality()
        self._check_risk()
        self._check_scope_containment()

        if single:
            for cid, name in (
                ("C", "Cross-Brief Consistency"),
                ("G", "Criteria Coverage (Fulfills)"),
                ("H", "AC Coverage (Covers)"),
                ("I", "AC Test Landing"),
                ("J", "Migration Landing"),
            ):
                self._add(cid, name, "SKIP",
                          "menuntut batch penuh; dijalankan di gerbang Fase 4",
                          "")
        else:
            self._check_cross_brief()
            self._check_criteria_coverage()
            self._check_ac_coverage()
            self._check_ac_test_landing()
            self._check_migration_landing()

        return not any(r["status"] == "FAIL" for r in self.results)

    # -- STRUKTUR ----------------------------------------------------------

    def _check_struct(self):
        cid, name = "S", "Struktur & Frontmatter"
        problems: List[str] = []

        for b in self.plan_briefs:
            fm = b["frontmatter"]
            for field in REQUIRED_FRONTMATTER:
                if not fm.get(field):
                    problems.append(f"{b['name']}: frontmatter `{field}:` kosong atau tidak ada")

            status = (fm.get("status") or "").upper()
            if status and status != "READY":
                problems.append(
                    f"{b['name']}: `status: {status}` — brief terbit `READY`; "
                    f"`DONE`/`BLOCKED` milik code-implementor, `SUPERSEDED` milik `scaffold_brief.py`, "
                    f"`DRAFT`/`APPROVED` bukan status brief"
                )

            commit = fm.get("commit_message") or ""
            if commit and not re.match(r"^[a-z]+\([a-z0-9_.-]+\):\s*implement\s+\S", commit):
                problems.append(
                    f"{b['name']}: `commit_message` \"{commit}\" tidak berbentuk "
                    f"`<type>(<domain>): implement <unit>`"
                )

            if b["nn"] is None:
                problems.append(
                    f"{b['name']}: nama berkas tidak berpola `brief-<NN>-<unit>.md` dengan NN dua digit"
                )

            present = [_norm_heading(s) for s in b["section_order"]]
            for want in REQUIRED_SECTIONS:
                if _norm_heading(want) not in present:
                    problems.append(f"{b['name']}: seksi wajib `## {want}` tidak ada")

            for banned in FORBIDDEN_SECTIONS:
                if _norm_heading(banned) in present:
                    problems.append(
                        f"{b['name']}: seksi `## {banned}` dilarang hadir di brief"
                    )

            # Urutan seksi mengikuti template kanonik; seksi yang hadir tapi
            # tertukar urutannya menyulitkan eksekutor membacanya berurutan.
            canonical = [_norm_heading(s) for s in REQUIRED_SECTIONS]
            seen = [s for s in present if s in canonical]
            if seen != sorted(seen, key=canonical.index):
                problems.append(
                    f"{b['name']}: urutan seksi menyimpang dari template kanonik "
                    f"({' → '.join(seen)})"
                )

            # Baris sumbu wajib berdiri di dalam `## Objective`.
            #
            # `Fulfills:` hanya dipakai pada rantai tanpa PRD. Pada rantai
            # ber-PRD, keterlacakan `SC-{n}` sudah diangkut kolom `Akar` tabel
            # `## Acceptance criteria` PRD dan ditagih predikat G2 `analyst`,
            # sehingga baris ini memvonis ulang kesimpulan yang sama dari ujung
            # yang berbeda — dan `SC-{n}`-nya di sana memang parafrase `AC-{n}`.
            obj = b["sections"].get(_norm_heading("Objective"))
            axes = [("Covers", "covers_line")]
            if self.prd_text:
                if b["fulfills_line"] is not None:
                    problems.append(
                        f"{b['name']}:{b['fulfills_line']}: baris `Fulfills:` tidak dipakai pada "
                        f"chain ber-PRD — keterlacakan `SC-{{n}}` diangkut kolom `Akar` PRD. "
                        f"Hapus barisnya"
                    )
            else:
                axes.append(("Fulfills", "fulfills_line"))

            for axis, key in axes:
                lineno = b[key]
                if lineno is None:
                    problems.append(f"{b['name']}: baris `{axis}:` tidak ada")
                    continue
                if obj:
                    body_lines = [ln for ln, _ in obj["body"]]
                    if body_lines and not (min(body_lines) <= lineno <= max(body_lines)):
                        problems.append(
                            f"{b['name']}:{lineno}: baris `{axis}:` berdiri di luar `## Objective`"
                        )

            # Penanda kerangka `scaffold_brief.py` wajib hilang begitu seksinya
            # diisi. Yang tersisa berarti seksi itu belum digarap sama sekali —
            # cacat yang selama ini hanya tertangkap kalau reviewer kebetulan jeli.
            for lineno, line in enumerate(b["lines"], start=1):
                if "<!-- scaffold:" in line:
                    problems.append(
                        f"{b['name']}:{lineno}: penanda kerangka `<!-- scaffold: ... -->` "
                        f"belum dihapus — seksi itu belum diisi"
                    )

            if b["covers"] and re.search(r"\bSC-\d+", b["covers"]):
                problems.append(f"{b['name']}: token `SC-{{n}}` menumpang di baris `Covers:`")
            if b["fulfills"] and re.search(r"\bAC-\d+", b["fulfills"]):
                problems.append(f"{b['name']}: token `AC-{{n}}` menumpang di baris `Fulfills:`")

        self._verdict(cid, name, problems,
                      f"{len(self.plan_briefs)} brief berstruktur lengkap",
                      "Lengkapi seksi/frontmatter yang disebut; struktur dituliskan "
                      "`scaffold_brief.py`, bukan disalin tangan dari contoh template.")

    # -- Check B -----------------------------------------------------------

    def _check_placeholder(self):
        cid, name = "B", "Placeholder Sweep"
        problems: List[str] = []
        for b in self.plan_briefs:
            for lineno, line in enumerate(b["lines"], start=1):
                for ph in PLACEHOLDERS:
                    # `TODO`/`TBD` diperiksa sebagai kata utuh supaya kata lain
                    # yang memuatnya tidak ikut tertuduh.
                    pattern = rf"\b{re.escape(ph)}\b" if ph.isupper() else re.escape(ph)
                    if re.search(pattern, line, re.IGNORECASE if not ph.isupper() else 0):
                        problems.append(f"{b['name']}:{lineno}: placeholder terlarang `{ph}`")
        self._verdict(cid, name, problems,
                      "nol placeholder terlarang",
                      "Ganti placeholder dengan keputusan konkret; brief tidak "
                      "mewariskan ketidakpastian ke eksekutor.")

    # -- Check F -----------------------------------------------------------

    def _check_verification(self):
        cid, name = "F", "Verification Sweep"
        problems: List[str] = []
        for b in self.plan_briefs:
            for lineno, line in enumerate(b["lines"], start=1):
                for marker in VERIFICATION_MARKERS:
                    if marker in line:
                        problems.append(
                            f"{b['name']}:{lineno}: penanda verifikasi `{marker.strip()}`"
                        )
                low = line.lower()
                for cmd in BUILD_TEST_COMMANDS:
                    if cmd in low:
                        problems.append(
                            f"{b['name']}:{lineno}: perintah build/test `{cmd}`"
                        )
                        break
        self._verdict(cid, name, problems,
                      "nol verifikasi di seluruh brief",
                      "Hapus perintahnya — jangan dipindah ke seksi lain. "
                      "Verifikasi milik penutup taskdir.")

    # -- Langit-langit slicing --------------------------------------------

    def _check_slicing(self):
        cid, name = "L", "Langit-langit Slicing"
        problems: List[str] = []
        for b in self.plan_briefs:
            code_files = [
                r for r in b["file_rows"]
                if not _is_test_path(r["path"], self.test_hint)
            ]
            if b["steps"] > MAX_STEPS:
                problems.append(
                    f"{b['name']}: {b['steps']} langkah `## Steps` (langit-langit {MAX_STEPS})"
                )
            if len(code_files) > MAX_CODE_FILES:
                problems.append(
                    f"{b['name']}: {len(code_files)} file kode di `## File scope` "
                    f"(langit-langit {MAX_CODE_FILES}; berkas test tidak dihitung)"
                )
            if b["steps"] == 0:
                problems.append(f"{b['name']}: `## Steps` tidak memuat satu pun langkah bernomor")
            if not b["file_rows"]:
                problems.append(f"{b['name']}: tabel **File** `## File scope` kosong")
        self._verdict(cid, name, problems,
                      "seluruh brief di bawah langit-langit slicing",
                      "Pecah brief yang melewati langit-langit jadi dua brief berurutan; "
                      "gabungkan kembali hanya bila pemecahannya merusak kompilasi, "
                      "dan catat alasannya di `## Analysis trace`.")

    # -- Resolusi anchor ---------------------------------------------------

    def _anchor_tokens(self, anchor: str) -> List[str]:
        cleaned = re.sub(r"~?:\s*\d+", " ", anchor)
        cleaned = cleaned.replace("`", " ")
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", cleaned)
        return [t for t in tokens if t.lower() not in ANCHOR_STOPWORDS]

    def _resolve_anchor(self, path: str, anchor: str) -> Tuple[str, str]:
        """Resolve satu anchor ke laci `.explore` atau ke disk.

        Mengembalikan (`ok` | `weak` | `fail`, keterangan sumber). `weak` berarti
        tokennya memang ada di berkas itu tetapi **tidak pada baris berbentuk
        deklarasi** — anchor yang menunjuk penyebutan, bukan titik sisip. Ia tidak
        menahan batch karena bentuk deklarasi berbeda antar stack dan heuristik
        lintas-stack pasti meleset sesekali; tetapi ia wajib terbaca, karena
        anchor semacam itu mengirim eksekutor mencari titik sisip yang tidak ada.
        """
        tokens = self._anchor_tokens(anchor)
        if not tokens:
            return "fail", "anchor tidak memuat satu pun simbol"

        # 1) Laci `.explore`: bukti yang sudah dipanen explorer.
        for laci_path, anchors in self.explore_map.items():
            if laci_path.endswith(path) or path.endswith(laci_path):
                blob = " ".join(anchors)
                if any(t in blob for t in tokens):
                    return "ok", "laci .explore"

        # 2) Disk: simbolnya benar-benar ada di berkas yang disebut, dan ada
        #    sebagai **deklarasi**, bukan sekadar disebut di suatu tempat.
        candidate = self.root / path
        if candidate.is_file():
            text = self._read(candidate) or ""
            hit = [t for t in tokens if t in text]
            if not hit:
                return "fail", f"simbol {tokens[0]} tidak ditemukan di berkas"
            for line in text.splitlines():
                if DECLARATION_RE.search(line) and any(
                    re.search(rf"\b{re.escape(t)}\b", line) for t in hit
                ):
                    return "ok", "disk (deklarasi)"
            return "weak", (
                f"simbol {hit[0]} muncul di berkas tetapi tidak pada baris berbentuk "
                f"deklarasi — anchor menunjuk penyebutan, bukan titik sisip"
            )

        return "fail", "berkas target tidak ada di disk maupun laci .explore"

    def _check_anchor(self):
        cid, name = "N", "Resolusi Anchor"
        problems: List[str] = []
        warnings: List[str] = []
        for b in self.plan_briefs:
            steps_text = self._section_text(b, "Steps")
            for row in b["file_rows"]:
                if row["aksi"] == "create":
                    # Berkas yang diciptakan brief ini tidak boleh sudah ada.
                    if (self.root / row["path"]).exists():
                        problems.append(
                            f"{b['name']}:{row['lineno']}: aksi `create` pada `{row['path']}` "
                            f"yang sudah ada di disk — seharusnya `modify`"
                        )
                    continue

                if not row["anchor"] or row["anchor"] in ("—", "-", ""):
                    problems.append(
                        f"{b['name']}:{row['lineno']}: baris `modify` `{row['path']}` "
                        f"tanpa kolom Anchor"
                    )
                    continue

                verdict, why = self._resolve_anchor(row["path"], row["anchor"])
                if verdict == "fail":
                    problems.append(
                        f"{b['name']}:{row['lineno']}: anchor `{row['anchor']}` "
                        f"pada `{row['path']}` tidak resolve — {why}"
                    )
                    continue
                if verdict == "weak":
                    warnings.append(
                        f"{b['name']}:{row['lineno']}: anchor `{row['anchor']}` "
                        f"pada `{row['path']}` — {why}"
                    )

                # Anchor yang resolve tetapi tidak disebut satu langkah pun berarti
                # brief menamai titik sisip yang tidak pernah dipakai langkahnya.
                # `../templates/brief-template.md` bagian 2 butir 5 menuntut tiap
                # langkah bertitik sisip konkret; ini separuh mekanis dari tuntutan
                # itu — yang tidak dapat digerbangi di sini adalah apakah klaim
                # isinya benar, dan itu milik `brief-reviewer`.
                tokens = self._anchor_tokens(row["anchor"])
                if tokens and not any(
                    re.search(rf"\b{re.escape(t)}\b", steps_text) for t in tokens
                ):
                    problems.append(
                        f"{b['name']}:{row['lineno']}: anchor `{row['anchor']}` tidak disebut "
                        f"satu langkah pun di `## Steps` — titik sisipnya tidak pernah dipakai"
                    )

        self._verdict(cid, name, problems,
                      "seluruh anchor `modify` resolve ke deklarasi dan dipakai `## Steps`",
                      "Panen ulang `.explore/<slug>-<NN>.md` unit itu lalu salin kolom "
                      "`Simbol anchor` apa adanya; dilarang mengarang anchor. Berkas yang "
                      "memang belum ada berarti unit ini pekerjaan `create`. Anchor yang "
                      "resolve tetapi tak disebut `## Steps` menandakan langkahnya menyentuh "
                      "simbol lain — samakan keduanya.",
                      warnings)

    # -- Check P -----------------------------------------------------------

    @staticmethod
    def _expand_braces(pattern: str) -> List[str]:
        """Perluas `{a,b}` jadi beberapa glob; `fnmatch` tidak mengenalnya."""
        m = re.search(r"\{([^{}]*)\}", pattern)
        if not m:
            return [pattern]
        out: List[str] = []
        for alt in m.group(1).split(","):
            out += BriefValidator._expand_braces(
                pattern[: m.start()] + alt.strip() + pattern[m.end():]
            )
        return out

    def _load_anti_patterns(self) -> List[Dict[str, str]]:
        """Panen resep `deteksi` dari `.claude/profile/backenddev/anti-patterns.md`.

        Formatnya sudah machine-readable sejak profil ditulis:
        `- <pola terlarang> (<sebaran>) → <pengganti> · deteksi `<pola> @ <cakupan>` · bukti …`

        Baris bersumber konfirmasi user tidak punya `deteksi` — polanya memang tak
        berjejak di kode — dan karena itu tidak dapat digerbangi di sini; ia tetap
        milik `brief-reviewer`.
        """
        text = self._read(resolve_profile_dir(self.root)[0] / "anti-patterns.md")
        if not text:
            return []
        out: List[Dict[str, str]] = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not line.lstrip().startswith("-"):
                continue
            m = re.search(r"deteksi\s+`([^`]+?)\s+@\s+([^`]+?)`", line)
            if not m:
                continue
            head = line.split("·")[0].lstrip("- ").strip()
            forbidden, _, replacement = head.partition("→")
            out.append({
                "lineno": str(lineno),
                "pattern": m.group(1).strip(),
                "scope": m.group(2).strip(),
                "forbidden": forbidden.strip() or head,
                "replacement": replacement.strip() or "(pengganti tidak tertulis di profil)",
            })
        return out

    def _check_anti_patterns(self):
        cid, name = "P", "Sapuan Anti-pattern"
        rules = self._load_anti_patterns()
        if not rules:
            self._add(cid, name, "SKIP",
                      "`.claude/profile/backenddev/anti-patterns.md` tidak ada atau nol baris ber-`deteksi`")
            return

        problems: List[str] = []
        for b in self.plan_briefs:
            steps = self._section_text(b, "Steps")
            if not steps:
                continue
            paths = [r["path"] for r in b["file_rows"]]
            for rule in rules:
                globs = self._expand_braces(rule["scope"])
                # Pola hanya berlaku pada brief yang benar-benar menyentuh
                # cakupannya; tanpa penyempitan ini satu resep bercakupan
                # handler menuduh brief yang hanya menyentuh domain.
                if not any(self._path_matches(p, g) for p in paths for g in globs):
                    continue
                try:
                    hit = re.search(rule["pattern"], steps)
                except re.error:
                    continue
                if hit:
                    problems.append(
                        f"{b['name']}: `## Steps` memuat pola terlarang "
                        f"`{hit.group(0)}` — anti-patterns.md:{rule['lineno']} "
                        f"\"{rule['forbidden']}\". Pengganti: {rule['replacement']}"
                    )

        self._verdict(cid, name, problems,
                      f"nol pola terlarang di `## Steps`; {len(rules)} resep `deteksi` disapu",
                      "Batalkan langkah itu dan rancang ulang memakai pola pengganti yang "
                      "tertulis di baris `anti-patterns.md` yang sama (`SKILL.md` Fase 3 "
                      "butir 6). Dilarang meloloskannya dengan alasan modul tetangga "
                      "melakukan hal yang sama — baris itu ada justru karena preseden "
                      "warisannya menyesatkan.")

    # -- Check D -----------------------------------------------------------

    def _check_test_reality(self):
        cid, name = "D", "Test Reality"
        problems: List[str] = []
        for b in self.plan_briefs:
            for row in b["file_rows"]:
                if not _is_test_path(row["path"], self.test_hint):
                    continue
                if row["aksi"] == "modify" and not (self.root / row["path"]).is_file():
                    problems.append(
                        f"{b['name']}:{row['lineno']}: berkas test `{row['path']}` beraksi "
                        f"`modify` tetapi tidak ada di disk"
                    )
        self._verdict(cid, name, problems,
                      "seluruh berkas test menunjuk berkas nyata atau path yang ditulis brief ini",
                      "Sapu direktori test unit itu lalu perbaiki path-nya, atau ubah "
                      "aksinya jadi `create` bila berkasnya memang belum ada.")

    # -- Check K -----------------------------------------------------------

    def _check_risk(self):
        cid, name = "K", "Risk Derivation"
        problems: List[str] = []
        ceiling = self._risk_ceiling()

        for b in self.plan_briefs:
            value = (b["frontmatter"].get("risk") or "").strip().upper()
            if value in ("", "-", "—"):
                problems.append(f"{b['name']}: `risk:` kosong atau `-` — bukan nilai sah bagi brief")
                continue
            if value not in VALID_RISKS:
                problems.append(f"{b['name']}: `risk: {value}` di luar enum BREAKING|MAJOR|MINOR")
                continue
            if ceiling and ceiling in RISK_ORDER and RISK_ORDER[value] > RISK_ORDER[ceiling]:
                problems.append(
                    f"{b['name']}: `risk: {value}` melampaui plafon akar `{ceiling}` — "
                    f"ini pemicu eskalasi, bukan nilai yang diturunkan"
                )

            # Satu predikat derivasi yang dapat divonis mekanis: DDL destruktif
            # menuntut BREAKING. Sisa tabel predikat tetap milik reviewer.
            migration = self._section_text(b, "Migration")
            for pattern, label in DESTRUCTIVE_DDL:
                if re.search(pattern, migration, re.IGNORECASE) and value != "BREAKING":
                    problems.append(
                        f"{b['name']}: `## Migration` memuat {label} (migrasi destruktif) "
                        f"tetapi `risk: {value}` — predikat menuntut BREAKING"
                    )
                    break

        summary = f"{len(self.plan_briefs)} brief bernilai risk sah"
        if ceiling:
            summary += f" di bawah plafon {ceiling}"
        self._verdict(cid, name, problems, summary,
                      "Perbaiki nilainya menurut tabel predikat "
                      "`../templates/brief-template.md` bagian 2 butir 10. Nilai yang "
                      "melampaui plafon dikembalikan ke pemanggil sebagai pemicu eskalasi — "
                      "dilarang dilunakkan agar muat.")

    # -- Check E -----------------------------------------------------------

    def _check_scope_containment(self):
        cid, name = "E", "Scope Containment"
        problems: List[str] = []
        note = ""

        allowed: List[str] = []
        if self.file_scope_arg:
            allowed = [p.strip().strip("`") for p in re.split(r"[,\s]+", self.file_scope_arg) if p.strip()]

        banned: List[str] = []
        if not allowed:
            body = self._doc_section(self.task_text, "Out of Scope")
            if body:
                banned = [t for t in re.findall(r"`([^`]+)`", body) if "/" in t or "." in t]
                note = "file_scope kosong — batas diturunkan dari `## Out of Scope` TASK.md"
            else:
                note = "file_scope kosong dan `## Out of Scope` TASK.md tidak terbaca"

        for b in self.plan_briefs:
            for row in b["file_rows"]:
                path = row["path"]
                if allowed:
                    if not any(self._path_matches(path, pat) for pat in allowed):
                        problems.append(
                            f"{b['name']}:{row['lineno']}: `{path}` di luar batas file_scope"
                        )
                for pat in banned:
                    if self._path_matches(path, pat):
                        problems.append(
                            f"{b['name']}:{row['lineno']}: `{path}` menyentuh butir "
                            f"`## Out of Scope` akar (`{pat}`)"
                        )

        # `file_scope` kosong berarti check ini menilai dengan pembanding yang
        # lebih lemah daripada yang dirancang: `## Out of Scope` menyebut apa yang
        # dilarang, bukan apa yang diizinkan, sehingga berkas di luar batas yang
        # kebetulan tidak disebut di sana lolos tanpa terdeteksi. Itu degradasi,
        # bukan kelulusan — dan ia wajib terbaca di keluaran, bukan tersembunyi
        # sebagai catatan di belakang kata PASS.
        warnings: List[str] = []
        if not allowed:
            warnings.append(
                f"TERDEGRADASI: {note}. Pembandingnya menyebut yang dilarang, bukan yang "
                f"diizinkan — berkas di luar batas yang tidak tersebut di sana lolos "
                f"tanpa terdeteksi."
            )

        self._verdict(cid, name, problems, "seluruh path di dalam batas",
                      "Teruskan parameter `file_scope` dari pemanggil (`analyst` pada lane "
                      "planning, gerbang pada jalur RCA) supaya check ini punya "
                      "pembanding yang dirancang; buang berkas di luar batas, atau ajukan "
                      "amandemen akar dan tunggu keputusannya sebelum batch ditutup. "
                      "Catat penyimpangan batas satu baris di `## Analysis trace`.",
                      warnings)

    @staticmethod
    def _path_matches(path: str, pattern: str) -> bool:
        pattern = pattern.rstrip("/")
        if not pattern:
            return False
        if pattern in path:
            return True
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern + "/*")

    # -- Check C -----------------------------------------------------------

    def _check_cross_brief(self):
        cid, name = "C", "Cross-Brief Consistency"
        problems: List[str] = []
        by_nn = {b["nn"]: b for b in self.briefs if b["nn"] is not None}

        numbers = sorted(by_nn)
        for expected, actual in enumerate(numbers, start=1):
            if expected != actual:
                problems.append(
                    f"penomoran brief bolong atau tidak urut: menemukan brief-{actual:02d} "
                    f"di posisi ke-{expected}"
                )
                break

        for b in self.briefs:
            own = b["nn"]
            for line in b["interfaces"]["consumes"]:
                refs = re.findall(r"brief-(\d{2})", line)
                if not refs:
                    continue

                # Satu baris `Consumes` = satu brief sumber. Baris yang menyebut
                # dua sumber membuat pasangan simbol-ke-sumbernya tidak dapat
                # dipetakan: pemeriksaan mana pun terpaksa menyandingkan simbol
                # pertama dengan tiap brief yang disebut, lalu melaporkan
                # kegagalan hantu atas simbol yang memang milik brief yang lain.
                # Brief yang sah mengonsumsi dari dua pendahulu memecahnya jadi
                # dua baris.
                if len(set(refs)) > 1:
                    problems.append(
                        f"{b['name']}: satu baris `Consumes` menyebut "
                        f"{len(set(refs))} brief sumber ({', '.join('brief-' + r for r in sorted(set(refs)))}) "
                        f"— pecah jadi satu baris per sumber"
                    )
                    continue

                ref = refs[0]
                target = int(ref)
                if own is not None and target >= own:
                    problems.append(
                        f"{b['name']}: `Consumes` menunjuk `brief-{ref}` yang "
                        f"nomornya tidak lebih kecil — DAG wajib mengalir satu arah"
                    )
                    continue
                if target not in by_nn:
                    problems.append(
                        f"{b['name']}: `Consumes` menunjuk `brief-{ref}` yang tidak ada di batch"
                    )
                    continue

                produced = " ".join(by_nn[target]["interfaces"]["produces"])
                symbols = [s for s in re.findall(r"`([^`]+)`", line)
                           if not re.fullmatch(r"brief-\d{2}", s)]
                if not symbols or not produced:
                    continue
                # Cocokkan tiap penggal identifier simbol yang dikonsumsi, bukan
                # hanya penggal terakhirnya: `VoucherCreateRequest.SelectAllStores`
                # sah dipenuhi `Produces` yang menyebut tipe induknya saja.
                tokens = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", symbols[0])
                          if t.lower() not in ("dari", "brief")]
                if tokens and not any(t in produced for t in tokens):
                    problems.append(
                        f"{b['name']}: signature `{symbols[0]}` tidak ditemukan di "
                        f"`Produces` brief-{ref}"
                    )

        # Tautan penggantian dua arah, dan brief READY tidak mengonsumsi brief
        # yang sudah digantikan — kontraknya pindah ke pengganti.
        for b in self.briefs:
            fm = b["frontmatter"]
            if b["status"] == "SUPERSEDED":
                refs = re.findall(r"brief-(\d{2})", fm.get("superseded_by", ""))
                tgt = by_nn.get(int(refs[0])) if len(refs) == 1 else None
                if (not tgt or b["nn"] is None or tgt["nn"] <= b["nn"]
                        or f"brief-{b['nn']:02d}" not in tgt["frontmatter"].get("supersedes", "")):
                    problems.append(f"{b['name']}: SUPERSEDED tanpa tautan dua arah ke pengganti ber-NN lebih besar")
            for ref in re.findall(r"brief-(\d{2})", fm.get("supersedes", "")):
                src = by_nn.get(int(ref))
                if not src or src["status"] != "SUPERSEDED":
                    problems.append(f"{b['name']}: `supersedes` brief-{ref} yang tidak berstatus SUPERSEDED")
            if b["status"] == "READY":
                for line in b["interfaces"]["consumes"]:
                    for ref in re.findall(r"brief-(\d{2})", line):
                        src = by_nn.get(int(ref))
                        if src and src["status"] == "SUPERSEDED":
                            problems.append(f"{b['name']}: `Consumes` menunjuk brief-{ref} yang SUPERSEDED "
                                            f"— rujuk penggantinya")

        self._verdict(cid, name, problems,
                      "DAG linear satu arah, signature Consumes/Produces selaras",
                      "Pecah baris `Consumes` multi-sumber jadi satu baris per brief sumber; samakan "
                      "signature `Produces` pendahulu dengan `Consumes` penerusnya, "
                      "atau ubah nomor urut brief agar alurnya kembali linear.")

    # -- Check G -----------------------------------------------------------

    def _check_criteria_coverage(self):
        cid, name = "G", "Criteria Coverage (Fulfills)"
        problems: List[str] = []

        if self.prd_text:
            # Rantai ber-PRD memakai satu sumbu, bukan dua. `SC-{n}` -> `Akar`
            # PRD -> `AC-{n}` -> `Covers:` sudah tergerbangi di tiap
            # sambungannya (predikat G2 `analyst`, lalu Check H di sini), dan
            # rute langsung `SC-{n}` -> `Fulfills:` memvonis ulang kesimpulan
            # yang sama tanpa menambah informasi.
            self._add(cid, name, "SKIP",
                      "chain ber-PRD; keterlacakan SC diangkut kolom `Akar` PRD "
                      "(predikat G2 `analyst`) lalu Check H")
            return

        if not self.task_text:
            for b in self.live_briefs:
                val = b["fulfills"] or ""
                if not re.match(r"^[—-]\s*\(", val):
                    problems.append(
                        f"{b['name']}: TASK.md absen — baris wajib berbunyi `Fulfills: — (akar absen)`"
                    )
            self._verdict(cid, name, problems, "TASK.md absen; penegasan akar tertulis di tiap brief",
                          "Tulis penegasan `Fulfills: — (akar absen)`, jangan kosongkan barisnya.")
            return

        sc_ids = self._sc_ids()
        claimed: Set[str] = set()
        for b in self.live_briefs:
            val = b["fulfills"]
            if val is None:
                problems.append(f"{b['name']}: baris `Fulfills:` tidak ada")
                continue
            nums = set(re.findall(r"\bSC-(\d+)\b", val))
            if not nums and not re.match(r"^[—-]\s*\(", val):
                problems.append(
                    f"{b['name']}: baris `Fulfills:` tidak memuat satu pun `SC-{{n}}` maupun penegasan"
                )
            for n in nums:
                if n not in sc_ids:
                    problems.append(f"{b['name']}: `SC-{n}` tidak ada di `## Success Criteria` TASK.md")
            claimed |= nums

        for n in sorted(sc_ids, key=int):
            if n not in claimed:
                problems.append(f"`SC-{n}` tidak disebut satu pun baris `Fulfills:` batch ini")

        self._verdict(cid, name, problems,
                      f"SC {len(claimed & sc_ids)}/{len(sc_ids)} tertutup",
                      "Petakan SC yang tertinggal ke brief yang mengerjakannya atau tambah "
                      "brief; hapus rujukan hantu. Dilarang menurunkannya jadi catatan.")

    # -- Check H -----------------------------------------------------------

    def _check_ac_coverage(self):
        cid, name = "H", "AC Coverage (Covers)"
        problems: List[str] = []

        if not self.prd_text:
            for b in self.live_briefs:
                val = b["covers"] or ""
                if not re.match(r"^[—-]\s*\(", val):
                    problems.append(
                        f"{b['name']}: PRD.md absen — baris wajib berbunyi `Covers: — (<alasan>)`"
                    )
            self._verdict(cid, name, problems, "PRD.md absen; penegasan tertulis di tiap brief",
                          "Tulis penegasan `Covers: — (<alasan>)`, jangan kosongkan barisnya.")
            return

        ac = self._ac_entries()
        claimed: Set[str] = set()
        for b in self.live_briefs:
            val = b["covers"]
            if val is None:
                problems.append(f"{b['name']}: baris `Covers:` tidak ada")
                continue
            nums = set(re.findall(r"\bAC-(\d+)\b", val))
            if not nums and not re.match(r"^[—-]\s*\(", val):
                problems.append(
                    f"{b['name']}: baris `Covers:` tidak memuat satu pun `AC-{{n}}` maupun penegasan"
                )
            for n in nums:
                if n not in ac:
                    problems.append(f"{b['name']}: `AC-{n}` tidak ada di `## Acceptance criteria` PRD")
            claimed |= nums

        for n in sorted(ac, key=int):
            if n not in claimed:
                problems.append(f"`AC-{n}` tidak disebut satu pun baris `Covers:` batch ini")

        self._verdict(cid, name, problems,
                      f"AC {len(claimed & set(ac))}/{len(ac)} tertutup",
                      "Petakan AC yang tertinggal ke brief yang mengerjakannya atau tambah "
                      "brief; hapus rujukan hantu. Dilarang menurunkannya jadi catatan.")

    # -- Check I -----------------------------------------------------------

    def _check_ac_test_landing(self):
        cid, name = "I", "AC Test Landing"
        if not self.prd_text:
            self._add(cid, name, "SKIP", "PRD.md absen; check ini tidak berlaku")
            return

        problems: List[str] = []
        ac = self._ac_entries()
        for num, kind in sorted(ac.items(), key=lambda kv: int(kv[0])):
            claimers = [b for b in self.live_briefs
                        if b["covers"] and f"AC-{num}" in b["covers"]]
            if not claimers:
                continue  # sudah dilaporkan Check H

            if kind == "test otomatis":
                # Predikat lama hanya menuntut "ada berkas test di brief pengklaim".
                # Tiga brief yang masing-masing kebetulan menyentuh berkas test
                # karena alasan lain karena itu bertiga lolos mengklaim satu AC
                # yang tidak satu pun di antaranya benar-benar menguji. Yang
                # ditagih sekarang: **satu baris test yang menamai AC-nya**, jadi
                # pemikul assertion-nya tertulis, bukan tersirat.
                carriers = [
                    f"{b['name']}:{r['lineno']}"
                    for b in claimers
                    for r in b["file_rows"]
                    if _is_test_path(r["path"], self.test_hint)
                    and re.search(rf"\bAC-{num}\b", f"{r['anchor']} {r['desc']}")
                ]
                if not carriers:
                    with_tests = [
                        b["name"] for b in claimers
                        if any(_is_test_path(r["path"], self.test_hint) for r in b["file_rows"])
                    ]
                    detail = (
                        f"berkas test ada di {', '.join(with_tests)} tetapi tidak satu pun "
                        f"barisnya menamai `AC-{num}`"
                        if with_tests else
                        f"nol berkas test di seluruh brief pengklaim "
                        f"({', '.join(b['name'] for b in claimers)})"
                    )
                    problems.append(
                        f"`AC-{num}` bertanda `test otomatis` tidak punya pemikul test yang "
                        f"tertulis — {detail}"
                    )

            for b in claimers:
                if kind == "qa manual":
                    rr = self._section_text(b, "Risk & rollback")
                    if f"AC-{num}" not in rr:
                        problems.append(
                            f"{b['name']}: langkah manual `AC-{num}` tidak mendarat di "
                            f"`## Risk & rollback` — `## Analysis trace` bukan tempatnya"
                        )

        self._verdict(cid, name, problems,
                      "tiap AC `test otomatis` punya baris test yang menamainya; "
                      "tiap AC `QA manual` mendarat",
                      "Tandai baris berkas test pemikul assertion-nya dengan `AC-{n}` di kolom "
                      "`Anchor` atau kolom \"Apa yang berubah\" — satu baris yang menamainya "
                      "cukup, dan berkas testnya dinamai menurut konvensi repo (perbedaan nama "
                      "tidak pernah menuntut amandemen PRD). Untuk AC `QA manual:`, turunkan "
                      "langkahnya ke `## Risk & rollback` brief pengklaim.")

    # -- Check J -----------------------------------------------------------

    def _orm_schema_declared(self) -> bool:
        profile = resolve_profile_dir(self.root)[0]
        text = "\n".join(
            t for t in (self._read(profile / "invariants.md"), self._read(profile / "commands.md")) if t
        ).lower()
        return any(marker in text for marker in ORM_SCHEMA_PROFILE_MARKERS)

    def _check_migration_landing(self):
        cid, name = "J", "Migration Landing"
        problems: List[str] = []

        prd_req = self._doc_section(self.prd_text, "Migration requirements") or ""
        prd_trigger = bool(prd_req.strip()) and "tidak perlu" not in prd_req.lower()

        migration_files = [
            (b, r) for b in self.live_briefs for r in b["file_rows"]
            if _is_migration_path(r["path"])
        ]

        owners = [b for b in self.live_briefs
                  if self._section_text(b, "Migration").strip()
                  and "tidak perlu" not in self._section_text(b, "Migration").lower()]

        # Tiga pemicu, bukan dua: brief yang menuliskan DDL tanpa mendaftarkan
        # berkas migrasinya di `## File scope` adalah cacat yang sama seriusnya —
        # eksekutor menulis DDL ke berkas yang tidak pernah disebut scope-nya.
        if not prd_trigger and not migration_files and not owners:
            self._add(cid, name, "SKIP",
                      "nol berkas migrasi dan `## Migration requirements` tidak menuntut apa pun")
            return

        orm_schema = self._orm_schema_declared()
        for b in owners:
            if any(_is_migration_path(r["path"]) for r in b["file_rows"]):
                continue
            if ORM_SCHEMA_TOKEN.search(self._section_text(b, "Migration")):
                if not orm_schema:
                    problems.append(
                        f"{b['name']}: `## Migration` menyatakan skema dibentuk ORM tanpa berkas migrasi, "
                        f"tetapi profil tidak menyatakan pembentukan skema oleh ORM"
                    )
                continue
            problems.append(
                f"{b['name']}: `## Migration` memuat DDL tetapi tidak satu pun berkas "
                f"migrasi terdaftar di `## File scope`"
            )

        if not owners:
            trigger = "PRD `## Migration requirements`" if prd_trigger else "berkas migrasi baru di batch"
            problems.append(
                f"{trigger} aktif tetapi tidak satu pun brief memuat `## Migration` berisi"
            )
        for b in owners:
            body = self._section_text(b, "Migration")
            if not re.search(r"^\s*\d+\.\s+\S", body, re.MULTILINE):
                problems.append(
                    f"{b['name']}: `## Migration` tidak memuat urutan deploy sebagai langkah bernomor"
                )
            if not re.search(r"\b(CREATE|ALTER|DROP|INSERT|UPDATE)\b", body, re.IGNORECASE):
                problems.append(f"{b['name']}: `## Migration` tidak memuat DDL konkret")

            rr = self._section_text(b, "Risk & rollback").lower()
            if not any(k in rr for k in ("rollback", "kembalikan skema", "revert", "turunkan skema")):
                problems.append(
                    f"{b['name']}: `## Risk & rollback` tidak menyebut cara mengembalikan skema"
                )

        self._verdict(cid, name, problems,
                      "migrasi mendarat beserta urutan deploy dan rollback plan",
                      "Lengkapi brief pemilik migrasinya; dilarang menyerahkan urutan deploy "
                      "ke gerbang sebagai catatan lisan.")

    # -- pelaporan ---------------------------------------------------------

    def _verdict(self, cid: str, name: str, problems: List[str],
                 pass_summary: str, action: str,
                 warnings: Optional[List[str]] = None):
        """Vonis satu check.

        `warnings` adalah temuan yang **tidak** menahan batch tetapi wajib
        terbaca. Ia bukan PASS yang diberi catatan: check yang berjalan
        terdegradasi lalu tetap mencetak PASS membuat kegagalan sistemiknya —
        pembanding yang tak pernah sampai, heuristik lintas-stack yang meleset —
        lolos tanpa satu pun jejak, dan itu persis yang membuat gerbang terkuat
        dapat mati diam-diam sepanjang satu rantai penuh.
        """
        warnings = warnings or []
        if problems:
            self._add(cid, name, "FAIL",
                      f"{len(problems)} pelanggaran", action, problems + warnings)
        elif warnings:
            self._add(cid, name, "WARN",
                      f"{len(warnings)} catatan; batch tidak ditahan", action, warnings)
        else:
            self._add(cid, name, "PASS", pass_summary, "")

    def format_text(self) -> str:
        failed = [r for r in self.results if r["status"] == "FAIL"]
        passed = [r for r in self.results if r["status"] == "PASS"]
        skipped = [r for r in self.results if r["status"] == "SKIP"]
        warned = [r for r in self.results if r["status"] == "WARN"]
        label = "FAIL" if failed else ("PASS (WARN)" if warned else "PASS")
        n_locked = len([b for b in self.briefs if b["locked"]])
        if self.brief_filter:
            mode = f"brief-{self.brief_filter}"
        else:
            mode = f"batch {len(self.plan_briefs)} brief aktif"
            if n_locked and not self.include_locked:
                mode += f" (+{n_locked} terkunci)"

        lines = [
            f"BRIEF VALIDATION: {mode} [{label}] "
            f"({len(passed)} pass / {len(failed)} fail / {len(warned)} warn / "
            f"{len(skipped)} skip)"
        ]
        if warned:
            lines.append(
                f"TERDEGRADASI: {len(warned)} check berjalan dengan pembanding atau "
                f"heuristik yang lebih lemah daripada rancangannya — "
                f"{', '.join(r['id'] for r in warned)}. Batch tidak ditahan, tetapi "
                f"vonis check itu tidak sekuat namanya."
            )
        for r in self.results:
            lines.append(f"[{r['id']}] {r['name']:<30} : {r['status']} ({r['summary']})")
            for d in r["details"]:
                lines.append(f"    - {d}")
            if r["status"] in ("FAIL", "WARN", "LOCKED") and r["action"]:
                lines.append(f"    * Tindakan: {r['action']}")

        if failed:
            total = sum(len(r["details"]) for r in failed)
            lines.append("")
            lines.append(
                f"{total} pelanggaran di {len(failed)} check. Perbaiki seluruhnya lebih dulu, "
                f"lalu jalankan ulang skrip ini sekali sebagai konfirmasi."
            )
        return "\n".join(lines)

    def to_json(self) -> str:
        failed = [r for r in self.results if r["status"] == "FAIL"]
        warned = [r for r in self.results if r["status"] == "WARN"]
        return json.dumps({
            "status": "FAIL" if failed else "PASS",
            "degraded_checks": [r["id"] for r in warned],
            "mode": "single" if self.brief_filter else "batch",
            "root": str(self.root),
            "taskdir": str(self.taskdir),
            "briefs": [b["name"] for b in self.briefs],
            "briefs_active": [b["name"] for b in self.plan_briefs],
            "briefs_locked": [
                {"name": b["name"], "status": b["status"]}
                for b in self.briefs if b["locked"]
            ],
            "explore_reports": len(self.explore_map),
            "risk_ceiling": self._risk_ceiling(),
            "violation_count": sum(len(r["details"]) for r in failed),
            "checks": [
                {k: v for k, v in r.items()} for r in self.results
            ],
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Brief Batch Validator — predikat mekanis rantai brief"
    )
    parser.add_argument("--taskdir", type=str, required=True, help="Path taskdir aktif")
    parser.add_argument("--brief", type=str, default=None,
                        help="Nomor NN satu brief untuk gerbang per-brief Fase 3; "
                             "kosong berarti seluruh batch")
    parser.add_argument("--risk", type=str, default=None,
                        help="Plafon risk Check K; fallback frontmatter risk: TASK.md")
    parser.add_argument("--file-scope", type=str, default=None,
                        help="File Scope rute gerbang; pembanding Check E")
    parser.add_argument("--review-state", action="store_true",
                        help="Laporkan ronde self-review yang sudah terpakai taskdir ini "
                             "beserta brief yang berubah sejak ronde terakhir")
    parser.add_argument("--open-round", action="store_true",
                        help="Buka ronde self-review tepat sebelum dispatch berangkat; "
                             "snapshot brief diambil di sini supaya perbaikan BLOCKER "
                             "sesudahnya terbaca sebagai brief berubah")
    parser.add_argument("--record-round", type=str, default=None,
                        metavar="VERDICT",
                        help="Materaikan satu ronde self-review yang baru selesai "
                             "(Approved | Issues Found)")
    parser.add_argument("--include-locked", action="store_true",
                        help="Nilai brief DONE/BLOCKED/SUPERSEDED dengan predikat rencana juga; "
                             "untuk audit, bukan untuk gerbang Fase 4")
    parser.add_argument("--root", type=str, default=None, help="Root repositori target")
    parser.add_argument("--json", action="store_true", help="Keluaran JSON")
    args = parser.parse_args()

    validator = BriefValidator(
        taskdir=args.taskdir,
        brief=args.brief,
        risk_ceiling=args.risk,
        file_scope=args.file_scope,
        target_root=Path(args.root) if args.root else None,
        include_locked=args.include_locked,
    )

    err = validator.load()
    if err:
        if args.json:
            print(json.dumps({"status": "FAIL", "error": err}, indent=2))
        else:
            print(f"BRIEF VALIDATION: [FAIL] {err}")
        sys.exit(1)

    if args.review_state or args.record_round or args.open_round:
        # `changed` dihitung **sebelum** ronde dibuka atau dimateraikan: keduanya
        # menulis state, dan menghitung sesudahnya membandingkan snapshot dengan
        # dirinya sendiri.
        changed = validator.changed_since_last_round()

        if args.open_round:
            left, why = validator.rounds_left()
            if left <= 0:
                print(f"REVIEW STATE: [FAIL] ronde tidak dapat dibuka — {why}")
                sys.exit(1)
            opened = validator.open_round()
            print(f"REVIEW STATE: ronde {opened['round']} dibuka "
                  f"(generasi {opened['generation']}, {len(opened['snapshot'])} brief tersnapshot)")
            print(f"    brief berubah sejak ronde terakhir: "
                  f"{', '.join(changed) if changed else '(tidak ada)'}")
            print("    Berangkatkan dispatch sekarang, lalu tutup dengan `--record-round`.")
            sys.exit(0)

        if args.record_round:
            state = validator.record_round(args.record_round, changed)
        else:
            state = validator.read_round_state()

        used = int(state["rounds"])
        left, why = validator.rounds_left()
        changed = validator.changed_since_last_round()
        payload = {
            "generation": state["generation"],
            "rounds_used": used,
            "rounds_remaining": left,
            "max_rounds": MAX_ROUNDS,
            "total_rounds": state["total_rounds"],
            "max_rounds_taskdir": MAX_ROUNDS_TASKDIR,
            "open_round": state["open"],
            "changed_briefs": changed,
            "history": [{k: v for k, v in h.items() if k != "snapshot"}
                        for h in state["history"]],
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"REVIEW STATE: generasi batch {state['generation']} — "
                  f"ronde terpakai {used}/{MAX_ROUNDS} (sisa {left}) · "
                  f"taskdir {state['total_rounds']}/{MAX_ROUNDS_TASKDIR}")
            for h in state["history"]:
                tail = "" if h.get("snapshot_at_dispatch", True) else "  [snapshot menyusul]"
                print(f"    ronde {h['round']}: {h['verdict']}{tail}")
            if state["open"]:
                print(f"    * ronde {state['open']['round']} masih terbuka — "
                      f"tutup dengan `--record-round \"<verdict>\"`.")
            print(f"    brief berubah sejak ronde terakhir: "
                  f"{', '.join(changed) if changed else '(tidak ada)'}")
            if left == 0:
                print(f"    * {why}. Serahkan brief apa adanya dengan status self-review "
                      f"tidak tuntas; dilarang membuka ronde baru sekalipun `plan` "
                      f"dipanggil ulang atas generasi batch yang sama.")
        sys.exit(0)

    ok = validator.run_all()
    print(validator.to_json() if args.json else validator.format_text())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
