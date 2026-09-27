#!/usr/bin/env python3
"""Brief Matrix & Scaffold Writer.

Dua mode yang menegakkan urutan kerja Fase 3: **alokasi lebih dulu, penulisan
menyusul**.

* `--write-matrix --spec <json>` — kunci matriks alokasi batch sebelum satu baris
  brief ditulis. Skrip memvonis kelengkapannya terhadap `## Success Criteria`
  `TASK.md` dan `## Acceptance criteria` `PRD.md`: tiap `SC-{n}` dan `AC-{n}`
  wajib punya brief pengklaim, tidak boleh ada rujukan hantu, penomoran `NN`
  wajib urut tanpa lompatan, `Consumes` wajib menunjuk `NN` lebih kecil, dan
  `risk` tiap brief wajib di bawah plafon akar. Matriks yang lolos ditulis ke
  laci kerja taskdir dalam dua bentuk: tabel markdown untuk dibaca, dan JSON
  untuk dibaca skrip.

* `--write-matrix --append --spec <json>` — tambahkan unit kerja yang baru ketahuan
  **sesudah** sebagian brief dieksekusi. Baris matriks lama dipertahankan apa
  adanya, nomor barunya melanjutkan `NN` tertinggi, dan alokasi brief
  `DONE`/`BLOCKED`/`SUPERSEDED` dilarang didefinisikan ulang; brief `BLOCKED` dan
  brief `READY` hilirnya ditutup lewat baris pengganti ber-`supersedes`. Tanpa `--append`, penulisan
  matriks penuh di atas taskdir yang sudah punya brief tereksekusi ditolak —
  itu memalsukan alokasi `Covers:`/`Fulfills:` pekerjaan yang kodenya sudah
  mendarat di `src/`.

* `--nn <NN>` — tuliskan kerangka satu brief dari baris matriksnya. Sepuluh
  seksi baku, frontmatter terisi, dan baris `Covers:`/`Fulfills:` **disalin dari
  matriks**, bukan diketik ulang. Tiap seksi membawa satu penanda
  `<!-- scaffold: ... -->` yang wajib dihapus penulis saat mengisinya;
  `validate_briefs.py` menolak brief yang masih menyisakan penanda itu. Baris
  ber-`supersedes` sekaligus menandai brief lama `SUPERSEDED` + `superseded_by` —
  satu-satunya penulis transisi itu. Baris ber-`repairs` memperbaiki brief `DONE`
  yang ditahan `{taskdir}/HALT.md` dan mencabut penanda itu saat kerangkanya ditulis.

Alasan urutannya: alokasi `AC`/`SC` adalah keputusan slicing. Menentukannya
sesudah delapan brief ditulis berarti coverage yang bolong menuntut pembongkaran
slicing — biaya yang tidak pernah perlu dibayar bila matriksnya dikunci lebih
dulu.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from brief_status import (  # noqa: E402
    HALT_FILE, LOCKED, SUPERSEDABLE, halted_nn, read_frontmatter, scan_briefs, set_frontmatter,
)
from precondition_lib import (  # noqa: E402
    VALID_RISKS, find_repo_root, frontmatter_field, load_profile_index, parse_enum, read_text, resolve_taskdir,
)
from precondition_lib import cli  # noqa: E402
from commit_lib import COMMIT_TYPES, commit_template, default_commit_type, render  # noqa: E402

RISK_ORDER = {"MINOR": 1, "MAJOR": 2, "BREAKING": 3}

# Laci kerja taskdir. Direktori ini sudah dikecualikan tiap gerbang git di
# rantai — tidak di-stage, tidak di-commit, tidak dihitung working tree kotor —
# sehingga matriks yang mendarat di sini tidak pernah menghentikan `architect`
# Fase 0 maupun gerbang penutup. Ia berbagi laci dengan laporan `code-explorer`.
# Karena tidak ter-commit, laci bisa hilang (clone baru, mesin lain); matriks
# lalu direkonstruksi dari brief ter-commit (`reconstruct_matrix`).
LACI = ".explore"
MATRIX_MD = "brief-matrix.md"
MATRIX_JSON = "brief-matrix.json"

SECTIONS = [
    ("Objective", "2-3 kalimat: apa yang dikerjakan dan alasannya, dengan bukti file:line "
                  "kondisi saat ini. Asumsi hulu yang membentuk langkah brief ini ditulis di "
                  "sini sebagai kalimat berawalan \"Berlaku asumsi:\""),
    ("Interfaces", "salin baris Consumes/Produces dari matriks; signature lengkap, bukan nama saja"),
    ("File scope", "tabel Folder lalu tabel File. Tiap baris `modify` wajib membawa Anchor "
                   "yang disalin dari kolom `Simbol anchor` laporan .explore unit ini, dan "
                   "anchor itu wajib disebut minimal satu langkah `## Steps`. Baris berkas "
                   "test pemikul AC bertanda `test otomatis` wajib menyebut `AC-{n}`-nya"),
    ("Out of scope", "modul/file/alur yang sengaja TIDAK disentuh beserta alasan teknisnya"),
    ("Steps", "maksimal 5 langkah bernomor, snippet lengkap dan valid, tiap langkah bertitik "
              "sisip konkret. Nol perintah build/test"),
    ("Migration", "nama berkas migrasi beserta DDL-nya dan urutan deploy bernomor, atau "
                  "\"tidak perlu\" beserta alasannya"),
    ("Mirrored paths", "consumer queue, scheduler, websocket, changelog dengan bukti file:line, "
                       "atau \"tidak ada\""),
    ("Risk & rollback", "dampak regresi, cara deteksi, strategi rollback. Langkah verifikasi tiap "
                        "AC bertanda `QA manual:` yang diklaim brief ini mendarat di sini, "
                        "bernomor AC-nya"),
    ("Work status", "tabel item kerja berstatus PLANNED"),
    ("Analysis trace", "BUKAN pekerjaan eksekutor: temuan gugur, pola modul tetangga, atau "
                       "asumsi. Tulis \"Tidak ada.\" bila kosong"),
]


def _read(path: Path) -> Optional[str]:
    """Isi berkas ternormalisasi (BOM dibuang, CRLF → LF), atau None bila tak terbaca."""
    try:
        return read_text(path)
    except (OSError, UnicodeDecodeError):
        return None


def _supersedes(row: Dict[str, Any]) -> List[str]:
    """Kolom spec `supersedes` (`["02"]`, `"02"`, atau `["brief-02"]`) -> ["02"]."""
    raw = row.get("supersedes") or []
    if isinstance(raw, (str, int)):
        raw = [raw]
    return [m for t in raw for m in re.findall(r"(?<!\d)(\d{2})(?!\d)", str(t))]


def _repairs(row: Dict[str, Any]) -> str:
    """Kolom spec `repairs` (`"02"` atau `"brief-02"`) -> "02", atau ""."""
    m = re.search(r"(?<!\d)(\d{2})(?!\d)", str(row.get("repairs") or ""))
    return m.group(1) if m else ""


def _doc_section(text: Optional[str], title: str) -> Optional[str]:
    if not text:
        return None
    want = re.sub(r"\s+", " ", title).strip().lower()
    capture: List[str] = []
    active = False
    for line in text.splitlines():
        if line.startswith("## "):
            if active:
                break
            active = re.sub(r"\s+", " ", line[3:]).strip().lower() == want
            continue
        if active:
            capture.append(line)
    return "\n".join(capture) if capture else None


class MatrixTool:
    def __init__(self, taskdir: str, target_root: Optional[Path] = None):
        self.root = (target_root or find_repo_root()).resolve()
        self.taskdir = resolve_taskdir(self.root, taskdir)
        self.task_text = _read(self.taskdir / "TASK.md")
        self.prd_text = _read(self.taskdir / "PRD.md")
        self.commit_template = commit_template(load_profile_index(self.root, required=()).data)

    def default_commit_type(self, finding_source: Optional[str]) -> str:
        lane = frontmatter_field(self.taskdir / "TASK.md", "lane") if self.task_text else None
        return default_commit_type(lane, finding_source)

    # -- sumbu hulu --------------------------------------------------------

    def sc_ids(self) -> Set[str]:
        body = _doc_section(self.task_text, "Success Criteria")
        return set(re.findall(r"\bSC-(\d+)\b", body)) if body else set()

    def ac_ids(self) -> Set[str]:
        body = _doc_section(self.prd_text, "Acceptance criteria")
        return set(re.findall(r"\bAC-(\d+)\b", body)) if body else set()

    def next_nn(self) -> int:
        """Nomor brief pertama batch ini: lanjutan `NN` tertinggi taskdir, atau 1.

        Batch yang ditambahkan ke taskdir eksisting (`preserve_history`) melanjutkan
        penomoran; nomor yang sudah terpakai tidak pernah dipakai ulang.
        """
        # Brief yang sudah dikerangkakan batch ini sendiri tidak menggeser titik
        # mulainya: tanpa pengecualian ini, menjalankan ulang `--write-matrix`
        # sesudah sebagian kerangka terbit — yang persis terjadi saat `plan`
        # dipanggil ulang — menolak matriksnya sendiri.
        own: Set[str] = set()
        existing = self.load_matrix()
        if existing:
            own = {str(b.get("nn")) for b in existing.get("briefs", [])}

        used = [
            int(m.group(1))
            for p in self.taskdir.glob("brief-*.md")
            for m in [re.match(r"^brief-(\d{2})-", p.name)]
            if m and m.group(1) not in own
        ]
        return max(used) + 1 if used else 1

    def locked_briefs(self) -> Dict[str, str]:
        """Brief taskdir yang sudah dieksekusi atau digantikan, dipetakan `NN` -> status.

        `DONE` dan `BLOCKED` ditulis `code-implementor` saat brief dieksekusi;
        `SUPERSEDED` ditulis skrip ini saat penggantinya terbit. Alokasinya karena
        itu **fakta sejarah**, bukan rencana yang boleh ditulis ulang: menimpanya
        berarti memalsukan riwayat brief yang kodenya sudah mendarat di `src/`,
        dan membuat `Covers:`/`Fulfills:` matriks berbeda dari yang benar-benar
        dikerjakan.
        """
        return {b["nn"]: b["status"] for b in scan_briefs(self.taskdir) if b["status"] in LOCKED}

    def merge_spec(self, spec: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Gabungkan baris matriks eksisting dengan baris baru `--append`.

        Mengembalikan (spec gabungan, nn yang dipertahankan, pelanggaran).
        Baris brief yang sudah `DONE`/`BLOCKED`/`SUPERSEDED` dipertahankan apa
        adanya dan dilarang didefinisikan ulang oleh spec baru.
        """
        existing = self.load_matrix()
        problems: List[str] = []
        if not existing or not existing.get("briefs"):
            return spec, [], [
                "`--append` menuntut matriks eksisting di "
                f"{self.taskdir / LACI / MATRIX_JSON}; tidak ada yang dapat ditambahi. "
                "Kunci batch pertamanya dengan `--write-matrix` tanpa `--append`."
            ]

        locked = self.locked_briefs()
        kept: List[Dict[str, Any]] = []
        kept_nn: List[str] = []
        for b in existing.get("briefs", []):
            nn = str(b.get("nn") or "")
            kept.append(b)
            kept_nn.append(nn)

        incoming = spec.get("briefs") or []
        for b in incoming:
            nn = str(b.get("nn") or "")
            if nn in locked:
                problems.append(
                    f"brief {nn}: berstatus `{locked[nn]}` di disk — alokasinya tidak dapat "
                    f"didefinisikan ulang. Beri nomor baru pada unit kerja tambahan"
                )
            elif nn in kept_nn:
                problems.append(
                    f"brief {nn}: sudah ada di matriks. `--append` menambah baris baru, "
                    f"bukan menimpa baris lama"
                )

        problems += self._check_supersedes(incoming)

        merged = dict(existing)
        merged.update({k: v for k, v in spec.items() if k != "briefs"})   # finding_source, date, …
        merged["briefs"] = kept + [b for b in incoming if str(b.get("nn") or "") not in kept_nn]
        return merged, kept_nn, problems

    def _check_supersedes(self, incoming: List[Dict[str, Any]]) -> List[str]:
        """Batch `--append` wajib menutup brief `BLOCKED`/`HALT.md` dan menerbitkan ulang `READY` hilirnya.

        Urutan `NN` adalah urutan eksekusi (D2-A): brief `READY` yang bernomor
        sesudah brief terblokir — atau sesudah brief `DONE` yang ditahan
        `HALT.md` — akan berjalan **sebelum** pengganti/perbaikan bernomor
        tertinggi, di atas kode yang belum diperbaiki. Karena itu ia ikut
        digantikan dan diterbitkan ulang sesudahnya.
        """
        problems: List[str] = []
        disk = {b["nn"]: b for b in scan_briefs(self.taskdir)}
        claimed = {t for b in incoming for t in _supersedes(b)}
        for b in incoming:
            for t in _supersedes(b):
                st = disk.get(t, {}).get("status", "tidak ada")
                if st not in SUPERSEDABLE:
                    problems.append(f"brief {b.get('nn')}: `supersedes` brief-{t} berstatus `{st}` — "
                                    f"hanya BLOCKED atau READY yang dapat digantikan")
        held = halted_nn(self.taskdir)
        for b in incoming:
            r = _repairs(b)
            if r and disk.get(r, {}).get("status") != "DONE":
                problems.append(f"brief {b.get('nn')}: `repairs` brief-{r} berstatus "
                                f"`{disk.get(r, {}).get('status', 'tidak ada')}` — hanya brief DONE yang diperbaiki")
        if held is not None and not any(_repairs(b) == held for b in incoming):
            problems.append(f"HALT.md menahan brief-{held} — batch --append wajib memuat baris "
                            f"`\"repairs\": \"{held}\"`")
        pivot = min((int(n) for n, b in disk.items() if b["status"] == "BLOCKED"), default=None)
        if pivot is None and held is not None:
            pivot = int(held)
        for n, b in sorted(disk.items()):
            if b["status"] == "BLOCKED" and n not in claimed:
                problems.append(f"brief-{n} BLOCKED belum digantikan — tambah baris ber-`supersedes: [\"{n}\"]`")
            if pivot is not None and b["status"] == "READY" and int(n) > pivot and n not in claimed:
                problems.append(f"brief READY hilir brief-{n} akan berjalan sebelum pengganti/perbaikan — "
                                f"terbitkan ulang sesudahnya (baris `supersedes: [\"{n}\"]`)")
        return problems

    def risk_ceiling(self, override: Optional[str]) -> Optional[str]:
        if override and override.strip().upper() not in ("", "-", "—"):
            return override.strip().upper()
        # Hanya frontmatter TASK.md: baris `risk:` di badan atau blok kode tidak terbaca.
        raw = frontmatter_field(self.taskdir / "TASK.md", "risk")
        if raw is None:
            return None
        if raw.strip() in ("-", "—"):
            return "MINOR"
        val, _err = parse_enum(raw, VALID_RISKS, "risk")
        return val or raw.strip().upper()

    # -- penulisan matriks -------------------------------------------------

    def validate_spec(self, spec: Dict[str, Any], ceiling: Optional[str]) -> List[str]:
        problems: List[str] = []
        briefs = spec.get("briefs") or []
        if not briefs:
            return ["spec tidak memuat satu pun entri `briefs`"]

        seen_nn: List[int] = []
        for i, b in enumerate(briefs, start=1):
            label = b.get("nn") or f"entri ke-{i}"

            for field in ("nn", "unit", "title", "risk"):
                if not str(b.get(field) or "").strip():
                    problems.append(f"brief {label}: field `{field}` kosong")

            nn = str(b.get("nn") or "")
            if not re.fullmatch(r"\d{2}", nn):
                problems.append(f"brief {label}: `nn` wajib dua digit (mis. `01`)")
            else:
                seen_nn.append(int(nn))

            unit = str(b.get("unit") or "")
            if unit and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", unit):
                problems.append(f"brief {label}: `unit` \"{unit}\" bukan kebab-case")

            ctype = str(b.get("commit_type") or "").strip()
            if ctype and ctype not in COMMIT_TYPES:
                problems.append(f"brief {label}: `commit_type` \"{ctype}\" di luar {', '.join(COMMIT_TYPES)}")
            if "{ticket}" in self.commit_template and not str(b.get("ticket") or spec.get("ticket") or "").strip():
                problems.append(f"brief {label}: `commit_template` profil memuat {{ticket}} — isi `ticket` "
                                f"(mis. `OMS-412`) di baris ini atau di tingkat atas spec")

            risk = str(b.get("risk") or "").upper()
            if risk and risk not in VALID_RISKS:
                problems.append(f"brief {label}: `risk` \"{risk}\" di luar enum")
            elif risk and ceiling and RISK_ORDER.get(risk, 0) > RISK_ORDER.get(ceiling, 3):
                problems.append(
                    f"brief {label}: `risk: {risk}` melampaui plafon akar `{ceiling}` — "
                    f"hentikan batch dan kembalikan klasifikasinya ke pemanggil"
                )

        # Penomoran melanjutkan brief yang sudah ada di taskdir (`preserve_history`),
        # bukan selalu mulai dari 01. Yang ditegakkan: kontinuitas tanpa lompatan
        # dan tanpa pemakaian ulang nomor — nomor brief tidak pernah dipakai dua kali
        # dalam satu taskdir.
        start = self.next_nn()
        if seen_nn:
            expected = list(range(start, start + len(seen_nn)))
            if sorted(seen_nn) != expected:
                problems.append(
                    f"penomoran `nn` wajib urut {start:02d}..{start + len(seen_nn) - 1:02d} "
                    f"tanpa lompatan (menemukan: "
                    f"{', '.join(f'{n:02d}' for n in sorted(seen_nn))})"
                )

        # DAG: `consumes` hanya boleh menunjuk brief bernomor lebih kecil.
        for b in briefs:
            nn = int(b["nn"]) if re.fullmatch(r"\d{2}", str(b.get("nn") or "")) else None
            for c in b.get("consumes") or []:
                for ref in re.findall(r"brief-(\d{2})", str(c)):
                    if nn is not None and int(ref) >= nn:
                        problems.append(
                            f"brief {b.get('nn')}: `consumes` menunjuk brief-{ref} yang "
                            f"nomornya tidak lebih kecil — DAG wajib satu arah"
                        )

        # Klaim brief yang digantikan (atau sedang digantikan batch ini) tidak
        # menutup AC/SC: penggantinya yang wajib memikulnya.
        gone = {t for b in briefs for t in _supersedes(b)}
        gone |= {n for n, st in self.locked_briefs().items() if st == "SUPERSEDED"}
        live = [b for b in briefs if str(b.get("nn") or "") not in gone]
        problems += self._validate_axis(live, "covers", "AC", self.ac_ids(), self.prd_text)
        # Sumbu `fulfills` hanya berlaku pada rantai tanpa PRD. Pada rantai
        # ber-PRD keterlacakan `SC-{n}` diangkut kolom `Akar` PRD, dan baris
        # `Fulfills:` tidak ditulis ke brief sama sekali.
        if not self.prd_text:
            problems += self._validate_axis(live, "fulfills", "SC", self.sc_ids(), self.task_text)
        return problems

    @staticmethod
    def _validate_axis(briefs: List[Dict[str, Any]], key: str, prefix: str,
                       upstream: Set[str], upstream_text: Optional[str]) -> List[str]:
        problems: List[str] = []
        claimed: Set[str] = set()

        for b in briefs:
            tokens = [str(t) for t in (b.get(key) or [])]
            if not upstream_text:
                # Dokumen hulu sah tidak ada: barisnya tetap wajib berupa penegasan.
                if tokens:
                    problems.append(
                        f"brief {b.get('nn')}: `{key}` memuat {prefix} padahal dokumen "
                        f"hulunya tidak ada di taskdir"
                    )
                continue
            if not tokens:
                problems.append(f"brief {b.get('nn')}: `{key}` kosong")
                continue

            # Penegasan bernalar `— (<alasan>)`: brief yang sah tidak memikul
            # sumbu ini. Bentuk normalnya brief tambahan untuk berkas yatim —
            # ia melandaskan pekerjaan yang baru ketahuan sesudah eksekusi, dan
            # tidak memperkenalkan AC/SC baru. Cakupan tetap ditegakkan atas
            # gabungan matriks di bawah, jadi penegasan ini tidak membuka celah:
            # AC/SC yang tidak diklaim siapa pun tetap gagal.
            if len(tokens) == 1 and re.fullmatch(r"[—-]\s*\(\s*\S.*\)", tokens[0].strip()):
                continue

            for t in tokens:
                m = re.fullmatch(rf"{prefix}-(\d+)", t.strip())
                if not m:
                    problems.append(
                        f"brief {b.get('nn')}: token `{t}` bukan `{prefix}-{{n}}` yang sah"
                    )
                    continue
                num = m.group(1)
                if num not in upstream:
                    problems.append(
                        f"brief {b.get('nn')}: `{prefix}-{num}` tidak ada di dokumen hulu "
                        f"(rujukan hantu)"
                    )
                claimed.add(num)

        if upstream_text:
            for num in sorted(upstream, key=int):
                if num not in claimed:
                    problems.append(
                        f"`{prefix}-{num}` tidak dialokasikan ke satu pun brief — petakan ke "
                        f"brief yang mengerjakannya atau tambah brief"
                    )
        return problems

    def render_matrix(self, spec: Dict[str, Any]) -> str:
        rows = []
        for b in spec.get("briefs", []):
            rows.append(
                "| `brief-{nn}` | `{unit}`{sup} | {covers} | {fulfills} | {risk} | {explore} | "
                "{consumes} | {produces} |".format(
                    nn=b.get("nn", ""),
                    unit=b.get("unit", ""),
                    sup="".join(f" · menggantikan `brief-{s}`" for s in _supersedes(b))
                        + (f" · memperbaiki `brief-{_repairs(b)}`" if _repairs(b) else ""),
                    covers=", ".join(b.get("covers") or []) or "—",
                    fulfills=", ".join(b.get("fulfills") or []) or "—",
                    risk=str(b.get("risk", "")).upper(),
                    explore=f"`.explore/{b['explore']}.md`" if b.get("explore") else "—",
                    consumes="; ".join(f"`{c}`" for c in (b.get("consumes") or [])) or "—",
                    produces="; ".join(f"`{p}`" for p in (b.get("produces") or [])) or "—",
                )
            )
        return "\n".join([
            "# Matriks Alokasi Batch Brief",
            "",
            "Dikunci di Fase 3 langkah 0 **sebelum** satu baris brief ditulis. Baris",
            "`Covers:`/`Fulfills:` tiap brief disalin dari tabel ini, bukan sebaliknya —",
            "dengan begitu cakupan dua sumbu benar sejak konstruksi, dan Check G/H turun",
            "jadi konfirmasi, bukan penemuan.",
            "",
            "Berkas ini laci kerja taskdir: tidak di-stage, tidak di-commit, dan tidak",
            "dihitung sebagai working tree kotor oleh gerbang git mana pun.",
            "",
            "| Brief | Unit | Covers | Fulfills | risk | Laporan `.explore` | Consumes | Produces |",
            "|---|---|---|---|---|---|---|---|",
            *rows,
            "",
        ])

    def write_matrix(self, spec: Dict[str, Any]) -> Path:
        laci = self.taskdir / LACI
        laci.mkdir(parents=True, exist_ok=True)
        (laci / MATRIX_MD).write_text(self.render_matrix(spec), encoding="utf-8")
        (laci / MATRIX_JSON).write_text(
            json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return laci / MATRIX_MD

    def load_matrix(self) -> Optional[Dict[str, Any]]:
        text = _read(self.taskdir / LACI / MATRIX_JSON)
        if text:
            try:
                return json.loads(text)
            except Exception:
                pass
        return self.reconstruct_matrix()

    def reconstruct_matrix(self) -> Optional[Dict[str, Any]]:
        """Baris matriks dari brief di disk: frontmatter, baris `Covers:`/`Fulfills:`, `## Interfaces`.

        Penegasan bernalar `— (<alasan>)` disalin apa adanya bila dokumen hulunya
        ada, supaya brief lama yang sah tidak memicu "sumbu kosong".
        """
        rows: List[Dict[str, Any]] = []
        for b in scan_briefs(self.taskdir):
            text = _read(b["path"]) or ""
            fm = read_frontmatter(b["path"])
            iface = _doc_section(text, "Interfaces") or ""
            row: Dict[str, Any] = {
                "nn": b["nn"],
                "unit": re.sub(r"^brief-\d{2}-|\.md$", "", b["name"]),
                "title": fm.get("title", ""),
                "risk": fm.get("risk", "MINOR"),
                "consumes": [c.strip() for c in re.findall(r"^\s*[-*]\s*Consumes:\s*(.+)$", iface, re.M)],
                "produces": [p.strip() for p in re.findall(r"^\s*[-*]\s*Produces:\s*(.+)$", iface, re.M)],
                "reconstructed": True,
            }
            for key, label, prefix, upstream in (("covers", "Covers", "AC", self.prd_text),
                                                 ("fulfills", "Fulfills", "SC", self.task_text)):
                m = re.search(rf"^\s*{label}:\s*(.+)$", text, re.M)
                val = m.group(1).strip() if m else ""
                ids = re.findall(rf"\b{prefix}-\d+\b", val)
                if ids:
                    row[key] = ids
                elif val and upstream:
                    row[key] = [val]
                else:
                    row[key] = []
                    if val:
                        row[f"{key}_note"] = val
            if b["supersedes"]:
                row["supersedes"] = b["supersedes"]
            if b["repairs"]:
                row["repairs"] = b["repairs"][0]
            rows.append(row)
        return {"briefs": rows, "reconstructed_from": "brief di disk"} if rows else None

    # -- scaffold ----------------------------------------------------------

    def scaffold(self, nn: str, force: bool) -> str:
        matrix = self.load_matrix()
        if not matrix:
            raise SystemExit(
                f"Matriks alokasi belum ada di {self.taskdir / LACI / MATRIX_JSON}. "
                f"Jalankan `--write-matrix` lebih dulu: kerangka brief diturunkan darinya, "
                f"bukan diketik ulang."
            )

        row = next((b for b in matrix.get("briefs", []) if str(b.get("nn")) == nn), None)
        if not row:
            raise SystemExit(f"Matriks tidak memuat baris untuk brief-{nn}.")

        locked = self.locked_briefs()
        sup = _supersedes(row)
        for s in sup:
            if locked.get(s, "READY") not in SUPERSEDABLE or not list(self.taskdir.glob(f"brief-{s}-*.md")):
                raise SystemExit(f"brief-{s} berstatus `{locked.get(s, 'tidak ada')}` — transisi ke "
                                 f"SUPERSEDED ditolak; hanya BLOCKED atau READY yang dapat digantikan.")
        if nn in locked:
            raise SystemExit(
                f"brief-{nn} berstatus `{locked[nn]}` — kerangkanya tidak ditulis ulang, "
                f"`--force` sekalipun. Brief yang sudah dieksekusi adalah riwayat; "
                f"pekerjaan susulan atasnya ditampung brief bernomor baru lewat "
                f"`--write-matrix --append`."
            )

        unit = row["unit"]
        path = self.taskdir / f"brief-{nn}-{unit}.md"
        if path.exists() and not force:
            raise SystemExit(
                f"{path} sudah ada. Gunakan `--force` hanya bila kerangkanya memang "
                f"ditulis ulang dari nol."
            )

        covers = ", ".join(row.get("covers") or []) or row.get("covers_note") or "— (tidak memikul AC)"
        fulfills = ", ".join(row.get("fulfills") or []) or row.get("fulfills_note") or "— (akar absen)"
        ctype = row.get("commit_type") or self.default_commit_type(matrix.get("finding_source"))
        scope = row.get("domain") or unit.split("-")[0]
        try:
            commit_message = render(self.commit_template, ctype=ctype, scope=scope, unit=unit,
                                    ticket=row.get("ticket") or matrix.get("ticket"))
        except ValueError as exc:
            raise SystemExit(f"commit_message brief-{nn} tidak dapat dirender: {exc}")

        lines = [
            "---",
            f"title: {row['title']}",
            f"source: {row.get('source') or matrix.get('source') or 'TASK.md'}",
            f"risk: {str(row['risk']).upper()}",
            "status: READY",
            f'commit_message: "{commit_message}"',
            f"commit_scope: {scope}",
            *([f"supersedes: {', '.join(f'brief-{s}' for s in sup)}"] if sup else []),
            *([f"repairs: brief-{_repairs(row)}"] if _repairs(row) else []),
            *([f"finding_source: {matrix['finding_source']}"] if matrix.get("finding_source") else []),
            "---",
            "",
            f"# Brief: {row['title']} — {matrix.get('date', '<yyyy-mm-dd>')}",
            "",
        ]

        for title, hint in SECTIONS:
            lines.append(f"## {title}")
            lines.append(f"<!-- scaffold: {hint} -->")
            if title == "Objective":
                lines.append("")
                lines.append(f"Covers: {covers}")
                # Rantai ber-PRD memakai satu sumbu: `SC-{n}` diangkut kolom
                # `Akar` PRD, bukan baris ini.
                if not self.prd_text:
                    lines.append(f"Fulfills: {fulfills}")
            elif title == "Interfaces":
                lines.append("")
                for c in row.get("consumes") or []:
                    lines.append(f"- Consumes: {c}")
                for p in row.get("produces") or []:
                    lines.append(f"- Produces: {p}")
            elif title == "Work status":
                lines.extend([
                    "",
                    "| Item | Status | Catatan |",
                    "|---|---|---|",
                    "| P1-1 | PLANNED | — |",
                ])
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        staged = [path.name]
        disk = {b["nn"]: b for b in scan_briefs(self.taskdir)}
        for s in sup:
            old = disk[s]
            set_frontmatter(old["path"], status="SUPERSEDED", superseded_by=f"brief-{nn}")
            staged.append(old["name"])
        if _repairs(row) and halted_nn(self.taskdir) == _repairs(row):
            (self.taskdir / HALT_FILE).unlink()
            staged.append(f"{HALT_FILE} (dihapus — stage dengan `git rm -q {HALT_FILE}`)")
        explore = row.get("explore")
        note = (
            f"Panen `{LACI}/{explore}.md` lebih dulu sebelum mengisi `## File scope` "
            f"dan `## Steps`." if explore else
            f"Unit ini tidak punya laporan `{LACI}/`; anchor diturunkan dari sapuan mandiri."
        )
        if len(staged) > 1:
            note += f"\n    Stage bersama di commit agregat: {', '.join(staged)}"
        return f"{path}\n{note}"


SPEC_LIST_FIELDS = ("covers", "fulfills", "consumes", "produces")
SPEC_STR_FIELDS = ("nn", "unit", "title", "risk", "explore", "commit_type", "domain", "ticket", "repairs")


def spec_shape_problems(spec: Any) -> List[str]:
    """Tolak bentuk spec yang akan membuat skrip crash, sebelum validasi isi."""
    if not isinstance(spec, dict):
        return [f"akar spec wajib objek JSON `{{\"briefs\": [...]}}`, bukan {type(spec).__name__}"]
    briefs = spec.get("briefs")
    if not isinstance(briefs, list):
        return ["`briefs` wajib berupa list objek"]
    problems: List[str] = []
    for i, b in enumerate(briefs, start=1):
        if not isinstance(b, dict):
            problems.append(f"entri ke-{i} wajib objek, bukan {type(b).__name__}")
            continue
        for f in SPEC_LIST_FIELDS:
            if f in b and not (isinstance(b[f], list) and all(isinstance(x, str) for x in b[f])):
                problems.append(f"entri ke-{i}: `{f}` wajib list string")
        for f in SPEC_STR_FIELDS:
            if f in b and not isinstance(b[f], (str, int)):
                problems.append(f"entri ke-{i}: `{f}` wajib string")
        if "supersedes" in b and not isinstance(b["supersedes"], (str, list)):
            problems.append(f"entri ke-{i}: `supersedes` wajib string atau list string")
    return problems


def main():
    parser = argparse.ArgumentParser(
        description="Brief Matrix & Scaffold Writer — alokasi dikunci sebelum penulisan"
    )
    parser.add_argument("--taskdir", required=True, help="Path taskdir aktif")
    parser.add_argument("--write-matrix", action="store_true",
                        help="Kunci matriks alokasi batch dari --spec")
    parser.add_argument("--spec", help="Path JSON spesifikasi batch; `-` berarti stdin")
    parser.add_argument("--nn", help="Nomor brief yang kerangkanya ditulis dari matriks")
    parser.add_argument("--risk", help="Plafon risk; fallback frontmatter risk: TASK.md")
    parser.add_argument("--append", action="store_true",
                        help="Tambahkan baris ke matriks eksisting; alokasi brief yang sudah "
                             "dieksekusi dipertahankan apa adanya")
    parser.add_argument("--force", action="store_true", help="Timpa kerangka yang sudah ada")
    parser.add_argument("--root", help="Root repositori target")
    args = parser.parse_args()

    tool = MatrixTool(args.taskdir, Path(args.root) if args.root else None)
    if not tool.taskdir.is_dir():
        print(f"SCAFFOLD: [FAIL] Taskdir tidak ditemukan: {tool.taskdir}")
        sys.exit(1)

    if args.write_matrix:
        if not args.spec:
            print("SCAFFOLD: [FAIL] `--write-matrix` menuntut `--spec <json|->`")
            sys.exit(1)
        if args.spec != "-":
            # Spec hanya boleh tinggal di laci `.explore/` taskdir (di-gitignore): berkas liar di
            # taskdir membuat working tree kotor dan prasyarat `architect` check 4 FAIL.
            spec_path = Path(args.spec)
            spec_path = (spec_path if spec_path.is_absolute() else tool.root / spec_path).resolve()
            laci = (tool.taskdir / LACI).resolve()
            if laci not in spec_path.parents:
                print(f"SCAFFOLD: [FAIL] spec wajib di {tool.taskdir / LACI}/ (mis. brief-spec.json) "
                      f"atau stdin (`-`): {args.spec}")
                sys.exit(1)
        raw = sys.stdin.read() if args.spec == "-" else (_read(spec_path) or "")
        try:
            spec = json.loads(raw)
        except Exception as exc:
            print(f"SCAFFOLD: [FAIL] spec bukan JSON sah: {exc}")
            sys.exit(1)
        shape = spec_shape_problems(spec)
        if shape:
            print(f"SCAFFOLD: [FAIL] bentuk spec tidak sah ({len(shape)} pelanggaran)")
            for problem in shape:
                print(f"    - {problem}")
            sys.exit(1)

        locked = tool.locked_briefs()
        kept_nn: List[str] = []
        merge_problems: List[str] = []
        n_new = len(spec.get("briefs") or [])

        if args.append:
            spec, kept_nn, merge_problems = tool.merge_spec(spec)
        elif locked:
            # Menulis ulang matriks penuh di atas brief yang sudah dieksekusi
            # membuang alokasi `Covers:`/`Fulfills:` yang benar-benar dikerjakan,
            # tanpa satu pun peringatan. Berkas terdampak yang baru ketahuan
            # sesudah eksekusi ditampung brief tambahan, bukan penulisan ulang.
            print(f"BRIEF MATRIX: [FAIL] {len(locked)} brief sudah dieksekusi di taskdir ini")
            for nn, status in sorted(locked.items()):
                print(f"    - brief-{nn}: `{status}`")
            print("\nMatriks penuh tidak boleh ditulis ulang di atas brief yang sudah "
                  "dieksekusi — alokasi AC/SC-nya adalah fakta sejarah, bukan rencana. "
                  "Tambahkan unit kerja baru dengan `--write-matrix --append --spec <json>`; "
                  "brief lama dipertahankan apa adanya dan nomor barunya melanjutkan `NN` "
                  "tertinggi.")
            sys.exit(1)

        ceiling = tool.risk_ceiling(args.risk)
        problems = merge_problems + tool.validate_spec(spec, ceiling)
        if problems:
            print(f"BRIEF MATRIX: [FAIL] {len(problems)} pelanggaran alokasi")
            for p in problems:
                print(f"    - {p}")
            print("\nPerbaiki alokasinya lebih dulu. Matriks yang bolong di sini menjadi "
                  "coverage yang bolong sesudah seluruh brief ditulis — dan pada titik itu "
                  "perbaikannya menuntut pembongkaran slicing.")
            sys.exit(1)

        out = tool.write_matrix(spec)
        n = len(spec.get("briefs", []))
        if args.append:
            print(f"BRIEF MATRIX: [PASS] {n} brief di matriks ({n_new} baru); "
                  f"plafon risk {ceiling or '—'}")
        else:
            print(f"BRIEF MATRIX: [PASS] {n} brief teralokasi; plafon risk {ceiling or '—'}")
        if args.append:
            origin = " (direkonstruksi dari brief di disk)" if spec.get("reconstructed_from") else ""
            print(f"    dipertahankan : {len(kept_nn)} baris lama "
                  f"({', '.join(f'brief-{n}' for n in kept_nn) or '—'}){origin}")
            print(f"    baris baru    : {n_new}")
            if locked:
                print(f"    terkunci      : "
                      f"{', '.join(f'brief-{k}={v}' for k, v in sorted(locked.items()))}")
        print(f"    matriks : {out}")
        print(f"    sumbu   : AC {len(tool.ac_ids())} · SC {len(tool.sc_ids())} tertutup penuh")
        sys.exit(0)

    if args.nn:
        print(f"SCAFFOLD: [PASS]\n    {tool.scaffold(args.nn, args.force)}")
        sys.exit(0)

    parser.error("pilih salah satu mode: `--write-matrix --spec <json>` atau `--nn <NN>`")


if __name__ == "__main__":
    sys.exit(cli(main))
