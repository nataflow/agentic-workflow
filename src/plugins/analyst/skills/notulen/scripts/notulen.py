#!/usr/bin/env python3
"""CLI siklus hidup notulen rapat plugin `analyst` (18 N1–N4, N6).

Tiap notulendir `analyst/notulen/<YYMMDDhhmm>-<slug>/` memuat satu `NOTULEN.md`: notulen terstruktur di atas,
`## Catatan Asli` (catatan kasar pencatat apa adanya) sebagai H2 terakhir. Notulen bisa memuat info sensitif, jadi
`analyst/notulen/.gitignore` (`*`) ditulis tanpa syarat dan skrip ini **tidak pernah meng-commit**: notulen hanya
ada di disk ini dan, bila sinkron aktif, di nataflow.

- `state`  — pindai `analyst/notulen/*/`, vonis keadaan tiap notulendir (`DRAFT`, `FINAL`, `DRIFT`, `RUSAK`,
             `NAMA_TIDAK_SAH`).
- `new`    — alokasikan notulendir beserta `NOTULEN.md` awal: kerangka, catatan asli verbatim, `source_hash`.
- `check`  — validator struktur dan isi notulen; `--final` ikut menagih nol `Asumsi:`.
- `final`  — `status: FINAL` + segel `final_hash` sesudah validator `PASS` dan jawaban eksplisit user.

`DRIFT` = notulen `FINAL` yang disunting sesudah disegel: `final` dijalankan ulang sesudah user mengonfirmasi isinya.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from analyst_lib import (  # noqa: E402
    BOM,
    PLACEHOLDER,
    SLUG_RE,
    Checker,
    clean_value,
    duplicate_headings,
    find_root,
    format_report,
    git_mode,
    h1_lines,
    meaningful,
    normalize_ticketdir,
    report_json,
    sections,
    set_frontmatter_field,
    split_frontmatter,
)

NOTULEN_DIR = "analyst/notulen"
NOTULEN_FILE = "NOTULEN.md"
NOTULENDIR_RE = re.compile(r"^analyst/notulen/\d{10}-[a-z0-9]+(?:-[a-z0-9]+)*$")
IGNORE = f"{NOTULEN_DIR}/.gitignore"
IGNORE_TEXT = (
    "# Ditulis analyst `notulen.py new`: notulen rapat bisa memuat info sensitif, jadi notulendir tetap di disk\n"
    "# dan tidak pernah di-commit. Isi berkas ini milik user sesudah ditulis.\n"
    "*\n"
)
H2 = ("Ringkasan", "Peserta", "Agenda", "Pembahasan", "Keputusan", "Action Item", "Pertanyaan Terbuka",
      "Catatan Asli")
PROSE_H2 = ("Ringkasan", "Peserta", "Agenda", "Pembahasan")
SOURCE_H2 = "Catatan Asli"
UNWRITTEN = "_(belum ditulis)_"
UNDECIDED = "belum ditentukan"
NONE_LINE = "- Tidak ada."
STATUSES = ("DRAFT", "FINAL")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HASH12 = re.compile(r"^[0-9a-f]{12}$")
D_LINE = re.compile(r"^- \*\*D-(\d+)\*\*: \S.*$")
Q_LINE = re.compile(r"^- \*\*Q-(\d+)\*\*: \S.* — menunggu: \S.*$")
ACTION_HEAD = re.compile(r"^\|\s*ID\s*\|\s*Tindakan\s*\|\s*PIC\s*\|\s*Tenggat\s*\|$")
ACTION_SEP = re.compile(r"^\|(\s*:?-{3,}:?\s*\|){4}$")
ACTION_ROW = re.compile(r"^\|\s*A-(\d+)\s*\|(.*)\|(.*)\|(.*)\|$")
# Selaras validator elisitasi: `Asumsi:` di mana pun dalam baris, juga bentuk tebal.
ASSUMPTION = re.compile(r"(?:^|[\s(\[>*_])\**Asumsi\**\s*:", re.IGNORECASE)
CONTENT_FIELDS = ("meeting_date",)  # field isi yang ikut sidik `final_hash`; sisanya pembukuan


# ── Bentuk berkas ────────────────────────────────────────────────────────────

def text_of(path: Path) -> str:
    """Isi berkas; non-UTF-8 → FAIL rapi (exit 1) yang menyebut berkasnya, bukan traceback."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"FAIL: {path} bukan UTF-8 ({exc.reason} @ byte {exc.start}) — simpan ulang sebagai "
                         f"UTF-8; jangan menebak isinya")


def decodes(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except UnicodeDecodeError:
        return False


def source_digest(text: str) -> str:
    """Sidik 12 hex `## Catatan Asli` — dimateraikan `new` sebagai `source_hash`."""
    _, body = split_frontmatter(text)
    quote = meaningful(sections(body, 2).get(SOURCE_H2, []))
    return hashlib.sha256("\n".join(l.rstrip() for l in quote).encode("utf-8")).hexdigest()[:12]


def final_digest(text: str) -> str:
    """Sidik 12 hex badan notulen + `CONTENT_FIELDS`; field pembukuan (`status`, `final_*`) di luar sidik."""
    fm, body = split_frontmatter(text)
    norm = "\n".join(l.rstrip() for l in body.strip().splitlines())
    fields = "\n".join(f"{k}={fm.get(k, '')}" for k in CONTENT_FIELDS)
    return hashlib.sha256(f"{fields}\n{norm}".encode("utf-8")).hexdigest()[:12]


def skeleton(slug: str, title: str, meeting_date: str, created: str, notes: str) -> str:
    """`NOTULEN.md` awal persis bagian 1 `templates/notulen-template.md`, beserta `source_hash`."""
    quote = "\n".join(f"> {l.rstrip()}" if l.strip() else ">" for l in notes.strip("\n").splitlines())
    prose = "\n\n".join(f"## {h}\n\n{UNWRITTEN}" for h in PROSE_H2)
    text = (f"---\ntype: meeting\nslug: {slug}\nmeeting_date: {meeting_date}\ncreated: {created}\nstatus: DRAFT\n"
            f"source_hash: -\nfinal_hash: -\nfinalized: -\nfinal_answer: -\n---\n\n# {title}\n\n{prose}\n\n"
            f"## Keputusan\n\n{NONE_LINE}\n\n## Action Item\n\n| ID | Tindakan | PIC | Tenggat |\n|---|---|---|---|\n\n"
            f"## Pertanyaan Terbuka\n\n{NONE_LINE}\n\n## {SOURCE_H2}\n\n{quote}\n")
    return set_frontmatter_field(text, "source_hash", source_digest(text))


def title_of(text: str) -> str:
    _, body = split_frontmatter(text)
    h1 = h1_lines(body)
    return h1[0][2:].strip() if h1 else "-"


def counts(text: str) -> Tuple[int, int, int]:
    """(keputusan, action item, pertanyaan terbuka) menurut baris yang sah."""
    _, body = split_frontmatter(text)
    h2 = sections(body, 2)
    d = sum(1 for l in h2.get("Keputusan", []) if D_LINE.match(l.strip()))
    a = sum(1 for l in h2.get("Action Item", []) if ACTION_ROW.match(l.strip()))
    q = sum(1 for l in h2.get("Pertanyaan Terbuka", []) if Q_LINE.match(l.strip()))
    return d, a, q


# ── Validator ────────────────────────────────────────────────────────────────

class NotulenValidator(Checker):
    def __init__(self, root: Path, rel: str, final: bool = False):
        super().__init__()
        self.root, self.rel, self.final = root, rel, final
        self.path = root / rel / NOTULEN_FILE

    def run_all(self) -> bool:
        if not NOTULENDIR_RE.match(self.rel):
            self.add(0, "Letak notulendir", False, f"`{self.rel}` bukan {NOTULEN_DIR}/<YYMMDDhhmm>-<slug>",
                     "Pakai notulendir hasil `notulen.py new`.")
            return False
        if not self.path.is_file():
            self.add(0, f"{NOTULEN_FILE} terbaca", False, f"`{self.rel}/{NOTULEN_FILE}` tidak ada",
                     "Alokasikan lewat `notulen.py new`.")
            return False
        if not decodes(self.path):
            self.add(0, f"{NOTULEN_FILE} terbaca", False, f"`{self.rel}/{NOTULEN_FILE}` bukan UTF-8",
                     "Simpan ulang berkasnya sebagai UTF-8; jangan menebak isinya.")
            return False
        self.text = self.path.read_text(encoding="utf-8")
        self.fm, self.body = split_frontmatter(self.text)
        self.h2 = sections(self.body, 2)
        self._frontmatter()
        self._structure()
        self._source()
        self._prose()
        self._decisions()
        self._actions()
        self._questions()
        self._placeholder()
        self._assumptions()
        return self.ok

    def _frontmatter(self) -> None:
        fm, errors = self.fm, []
        if fm.get("type") != "meeting":
            errors.append(f"type `{fm.get('type', '')}` bukan meeting")
        slug = self.rel.rsplit("/", 1)[-1].split("-", 1)[-1]
        if fm.get("slug") != slug:
            errors.append(f"slug `{fm.get('slug', '')}` ≠ slug notulendir `{slug}`")
        for key in ("meeting_date", "created"):
            if not DATE.match(str(fm.get(key, ""))):
                errors.append(f"{key} bukan YYYY-MM-DD")
        if fm.get("status") not in STATUSES:
            errors.append(f"status `{fm.get('status', '')}` bukan {'|'.join(STATUSES)}")
        if not HASH12.match(str(fm.get("source_hash", ""))):
            errors.append("source_hash bukan 12 hex (ditulis `notulen.py new`)")
        self.add(1, "Frontmatter", not errors, "; ".join(errors) or "lolos",
                 "Field frontmatter ditulis `notulen.py new`/`final`; jangan menyuntingnya dengan tangan.")

    def _structure(self) -> None:
        errors = []
        h1 = h1_lines(self.body)
        if len(h1) != 1 or not h1[0][2:].strip():
            errors.append(f"{len(h1)} H1 berisi, wajib tepat satu")
        if tuple(self.h2) != H2:
            errors.append(f"heading {list(self.h2)} bukan {list(H2)}")
        dup = duplicate_headings(self.body, 2)
        if dup:
            errors.append("heading ganda (isi yang pertama tertimpa): " + ", ".join(dup))
        self.add(2, "Struktur", not errors, "; ".join(errors) or "lolos",
                 f"Satu H1 judul rapat, lalu {len(H2)} H2 persis urutan template, tiap heading sekali, "
                 f"`## {SOURCE_H2}` terakhir.")

    def _source(self) -> None:
        quote = meaningful(self.h2.get(SOURCE_H2, []))
        sealed = str(self.fm.get("source_hash", "-")).strip()
        drifted = HASH12.match(sealed) is not None and sealed != source_digest(self.text)
        ok = bool(quote) and all(l.startswith(">") for l in quote) and not drifted
        self.add(3, "Catatan asli utuh", ok,
                 f"Catatan Asli berubah sejak `notulen.py new` (source_hash {sealed})" if drifted
                 else f"{len(quote)} baris kutipan" if quote else "kosong",
                 "Salin ulang `## Catatan Asli` byte demi byte seperti ditulis `notulen.py new`; keterangan baru "
                 "dari pencatat masuk seksi notulen, bukan ke kutipan.")

    def _prose(self) -> None:
        errors = []
        for h in PROSE_H2:
            lines = meaningful(self.h2.get(h, []))
            if not lines or UNWRITTEN in "\n".join(lines):
                errors.append(f"{h} belum ditulis")
        if not any(l.strip().startswith("- ") for l in self.h2.get("Peserta", [])):
            errors.append("Peserta tanpa butir `- `")
        self.add(4, "Seksi isi", not errors, "; ".join(errors) or "lolos",
                 f"Isi {', '.join(PROSE_H2)} dari catatan asli atau jawaban pencatat; peserta sebagai butir `- `.")

    def _numbered(self, cid: int, name: str, heading: str, pattern: "re.Pattern[str]", fmt: str) -> None:
        lines = [l.strip() for l in meaningful(self.h2.get(heading, []))]
        errors, ids = [], []
        if lines != [NONE_LINE]:
            if not lines:
                errors.append(f"seksi kosong — tulis `{NONE_LINE}`")
            for line in lines:
                m = pattern.match(line)
                if m:
                    ids.append(int(m.group(1)))
                else:
                    errors.append(f"format rusak: {line[:50]}")
        if ids != list(range(1, len(ids) + 1)):
            errors.append(f"nomor {ids} tidak berurutan dari 1")
        self.add(cid, name, not errors, "; ".join(errors) or (f"{len(ids)} butir" if ids else "nihil"),
                 f"`{fmt}` bernomor urut dari 1, atau `{NONE_LINE}`.")

    def _decisions(self) -> None:
        self._numbered(5, "Keputusan", "Keputusan", D_LINE, "- **D-n**: <keputusan>")

    def _actions(self) -> None:
        rows = [l.strip() for l in self.h2.get("Action Item", []) if l.strip().startswith("|")]
        errors, ids = [], []
        if len(rows) < 2 or not ACTION_HEAD.match(rows[0]) or not ACTION_SEP.match(rows[1].replace(" ", "")):
            errors.append("tabel tanpa header `| ID | Tindakan | PIC | Tenggat |` beserta baris pemisah")
        for row in rows[2:]:
            m = ACTION_ROW.match(row)
            if not m:
                errors.append(f"baris rusak: {row[:50]}")
                continue
            ids.append(int(m.group(1)))
            what, pic, due = (g.strip() for g in m.groups()[1:])
            if not what:
                errors.append(f"A-{m.group(1)}: Tindakan kosong")
            if not pic:
                errors.append(f"A-{m.group(1)}: PIC kosong — tulis `{UNDECIDED}` bila memang belum ada")
            if due != UNDECIDED and not _real_date(due):
                errors.append(f"A-{m.group(1)}: Tenggat `{due}` bukan YYYY-MM-DD atau `{UNDECIDED}`")
        if ids != list(range(1, len(ids) + 1)):
            errors.append(f"nomor {ids} tidak berurutan dari A-1")
        self.add(6, "Action item", not errors, "; ".join(errors) or f"{len(ids)} butir",
                 f"Baris `| A-n | <tindakan> | <PIC> | <YYYY-MM-DD> |`; PIC atau tenggat yang tidak disebut "
                 f"ditulis `{UNDECIDED}`, bukan ditebak.")

    def _questions(self) -> None:
        self._numbered(7, "Pertanyaan terbuka", "Pertanyaan Terbuka", Q_LINE,
                       "- **Q-n**: <pertanyaan> — menunggu: <siapa>")

    def _placeholder(self) -> None:
        text = "\n".join(l for h, body in self.h2.items() if h != SOURCE_H2 for l in body)
        hits = sorted({h for h in PLACEHOLDER.findall(text) if "@" not in h and not h.startswith("<http")})
        self.add(8, "Nol placeholder", not hits, "lolos" if not hits else ", ".join(hits[:5]),
                 "Ganti tiap `<...>`, TBD, TODO dengan isi final; yang belum diketahui jadi `Q-n`.")

    def _assumptions(self) -> None:
        final = self.final or self.fm.get("status") == "FINAL"
        lines = [l.strip()[:50] for h, body in self.h2.items() if h != SOURCE_H2 for l in body
                 if ASSUMPTION.search(l)]
        self.add(9, "Asumsi terkonfirmasi", not (final and lines),
                 f"{len(lines)} baris `Asumsi:`" + (" pada FINAL" if final and lines else ""),
                 "Konfirmasi tiap `Asumsi:` ke pencatat (hapus labelnya) atau pindahkan jadi `Q-n` sebelum final.")


def _real_date(value: str) -> bool:
    if not DATE.match(value):
        return False
    try:
        dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


# ── Keadaan ──────────────────────────────────────────────────────────────────

def notulendirs(root: Path) -> List[str]:
    base = root / NOTULEN_DIR
    if not base.is_dir():
        return []
    return sorted(f"{NOTULEN_DIR}/{p.name}" for p in base.iterdir() if p.is_dir())


def classify(root: Path, rel: str) -> Dict[str, str]:
    """Keadaan satu notulendir → rute berikutnya."""
    f = root / rel / NOTULEN_FILE
    row = {"notulendir": rel, "title": "-", "meeting_date": "-"}
    if not NOTULENDIR_RE.match(rel):
        return {**row, "state": "NAMA_TIDAK_SAH",
                "route": f"bukan notulendir analyst — ganti nama ke {NOTULEN_DIR}/<YYMMDDhhmm>-<slug>"}
    if not f.is_file():
        return {**row, "state": "RUSAK", "route": f"{NOTULEN_FILE} tidak ada — hapus direktorinya atau `new` ulang"}
    if not decodes(f):
        return {**row, "state": "RUSAK", "route": f"{NOTULEN_FILE} bukan UTF-8 — simpan ulang sebagai UTF-8"}
    text = f.read_text(encoding="utf-8")
    fm, _ = split_frontmatter(text)
    row.update(title=title_of(text), meeting_date=str(fm.get("meeting_date", "-")))
    status = fm.get("status")
    if status == "DRAFT":
        return {**row, "state": "DRAFT", "route": "analyst:notulen → lengkapi, `check`, konfirmasi user, `final`"}
    if status == "FINAL":
        if str(fm.get("final_hash", "-")).strip() == final_digest(text):
            return {**row, "state": "FINAL", "route": "selesai — sinkron ulang ke nataflow bila perlu"}
        return {**row, "state": "DRIFT",
                "route": "disunting sesudah final — konfirmasi isinya ke user lalu `final` ulang"}
    return {**row, "state": "RUSAK", "route": f"status `{status or '-'}` bukan {'|'.join(STATUSES)}"}


def resolve(root: Path, raw: str) -> str:
    return normalize_ticketdir(raw, root)


# ── subcommand ───────────────────────────────────────────────────────────────

def cmd_state(root: Path, args: argparse.Namespace) -> int:
    rows = [classify(root, rel) for rel in notulendirs(root)]
    if args.json:
        print(json.dumps({"root": str(root), "notulendirs": rows}, indent=2, ensure_ascii=False))
        return 0
    if not rows:
        print("NOTULEN STATE: nihil notulendir")
        return 0
    print(f"NOTULEN STATE: {len(rows)} notulendir")
    for r in rows:
        print(f"- {r['notulendir']} · {r['state']} · {r['meeting_date']} · {r['title']}\n    → {r['route']}")
    return 0


def cmd_new(root: Path, args: argparse.Namespace) -> int:
    """Alokasikan notulendir dan tulis `NOTULEN.md` awal; `.gitignore` notulen ditulis tanpa syarat (K8)."""
    if not SLUG_RE.match(args.slug) or len(args.slug) > 40:
        print(f"NEW FAIL: slug `{args.slug}` bukan kebab-case ≤40 karakter")
        return 1
    title = " ".join(args.title.split())
    if not title:
        print("NEW FAIL: --title kosong — tanyakan judul atau topik rapat ke pencatat")
        return 1
    if not _real_date(args.date):
        print(f"NEW FAIL: --date `{args.date}` bukan tanggal YYYY-MM-DD — tanyakan tanggal rapat ke pencatat")
        return 1
    notes = sys.stdin.read() if args.notes == "-" else args.notes
    notes = notes.lstrip(BOM)
    if not notes.replace(BOM, "").strip():   # U+FEFF bukan spasi bagi `str.strip`
        print("NEW FAIL: --notes kosong — minta pencatat menempelkan catatan kasar rapatnya")
        return 1
    for rel in notulendirs(root):
        r = classify(root, rel)
        if rel.split("-", 1)[-1] == args.slug and r["state"] in ("DRAFT", "DRIFT"):
            print(f"NEW FAIL: slug `{args.slug}` masih terbuka di {rel} ({r['state']}) — lanjutkan itu, "
                  f"atau pilih slug lain")
            return 1
    rel = f"{NOTULEN_DIR}/{dt.datetime.now().strftime('%y%m%d%H%M')}-{args.slug}"
    if (root / rel).exists():
        print(f"NEW FAIL: {rel} sudah ada (slug sama dalam menit yang sama) — tunggu satu menit atau pilih slug lain")
        return 1
    (root / rel).mkdir(parents=True)
    (root / rel / NOTULEN_FILE).write_text(skeleton(args.slug, title, args.date, dt.date.today().isoformat(), notes),
                                           encoding="utf-8")
    note = ""
    if not (root / IGNORE).exists():
        (root / IGNORE).write_text(IGNORE_TEXT, encoding="utf-8")
        note = f" · {IGNORE} ditulis"
    mode = git_mode(root, f"{rel}/{NOTULEN_FILE}")
    if mode == "ya":
        note += f" · PERINGATAN: notulen tidak diabaikan git — isi {IGNORE} sudah diubah user; notulen tetap tidak " \
                f"di-commit skrip ini"
    print(f"NEW PASS: {rel} · root={root} · git={mode}{note}")
    return 0


def cmd_check(root: Path, args: argparse.Namespace) -> int:
    rel = resolve(root, args.notulendir)
    v = NotulenValidator(root, rel, final=args.final)
    v.run_all()
    if args.json:
        print(report_json(v.results, notulendir=rel))
    else:
        print(format_report(f"notulen {rel}", v.results))
    return 0 if v.ok else 1


def cmd_final(root: Path, args: argparse.Namespace) -> int:
    rel = resolve(root, args.notulendir)
    answer = " ".join(args.answer.split())
    if not answer:
        print("FINAL FAIL: --answer kosong — `final` hanya atas jawaban eksplisit user")
        return 1
    v = NotulenValidator(root, rel, final=True)
    if not v.run_all():
        print(format_report(f"notulen {rel}", v.results))
        print("FINAL FAIL: validator FAIL — perbaiki per baris `Tindakan`, lalu konfirmasi ulang ke user")
        return 1
    path = root / rel / NOTULEN_FILE
    text = text_of(path)
    digest = final_digest(text)
    for key, value in (("status", "FINAL"), ("final_hash", digest), ("finalized", dt.date.today().isoformat()),
                       ("final_answer", clean_value(answer))):
        text = set_frontmatter_field(text, key, value)
    path.write_text(text, encoding="utf-8")
    d, a, q = counts(text)
    print(f"FINAL PASS: {rel} · sidik {digest} · {d} keputusan · {a} action item · {q} Q · tanpa commit "
          f"(notulen diabaikan git)")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Siklus hidup notulen rapat analyst")
    p.add_argument("--root", default=None, help="root ruang kerja; default root git atau cwd")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("state")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("new")
    s.add_argument("--slug", required=True)
    s.add_argument("--title", required=True, help="judul atau topik rapat (H1)")
    s.add_argument("--date", required=True, help="tanggal rapat YYYY-MM-DD")
    s.add_argument("--notes", required=True, help="catatan kasar apa adanya, atau `-` untuk stdin")
    s = sub.add_parser("check")
    s.add_argument("--notulendir", required=True)
    s.add_argument("--final", action="store_true", help="ikut menagih nol `Asumsi:` (aturan `final`)")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("final")
    s.add_argument("--notulendir", required=True)
    s.add_argument("--answer", required=True, help="jawaban user apa adanya")
    args = p.parse_args()
    root = (Path(args.root) if args.root else find_root()).resolve()
    handler: Dict[str, Any] = {"state": cmd_state, "new": cmd_new, "check": cmd_check, "final": cmd_final}
    sys.exit(handler[args.cmd](root, args))


if __name__ == "__main__":
    main()
