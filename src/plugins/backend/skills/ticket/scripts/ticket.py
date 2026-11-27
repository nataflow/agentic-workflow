#!/usr/bin/env python3
"""CLI siklus hidup tiket cepat `backend:ticket` (Langkah 40).

Tiap ticketdir `backenddev/tickets/<YYMMDDhhmm>-<slug>/` memuat satu `TICKET.md`: kartu teknis pendek berisi kondisi
sekarang berbukti `path:baris`, perubahan, `AC-{n}`, dan dampak kontrak. Tiket hidup di disk dan tidak pernah
di-commit (40 T2): `new` menulis penanda `backenddev/tickets/.gitignore` (`*`), dan tidak ada subperintah yang
menjalankan git commit. Cermin nataflow lewat `sync` (40 T3).

- `state`   — pindai ticketdir: DRAFT/READY/DRIFT/DIBATALKAN/RUSAK beserta taskdir pemakainya (`ticket_source`);
              DIBATALKAN hanya dengan `--all`.
- `new`     — alokasikan ticketdir beserta `TICKET.md` dari templat (DRAFT); menolak slug kembar yang masih terbuka.
- `check`   — vonis mekanis kartu: frontmatter, H1 tunggal, lima H2 wajib berurutan dan terisi, tanpa placeholder,
              `AC-{n}` kanonik 1..n (n ≤ 5) hanya di seksinya, bukti `path:baris` yang ada di repo, jenis dampak kontrak.
- `approve` — DRAFT yang lolos `check` → READY bermaterai `approved_seal`/`approved_seal_norm`, segel yang dibaca
              penerima `ticket_source` (`precondition_lib.be_ticket_verdict`). Dipanggil sesudah jawaban eksplisit user.
- `reopen`  — READY/DRIFT → DRAFT; segel dikosongkan, `reopened` naik.
- `cancel`  — DRAFT/READY/DRIFT → CANCELLED atas keputusan user.
- `sync`    — argumen tool MCP nataflow untuk tiket READY (task `create`/`update`) atau tiket pernah-READY yang
              dibatalkan (`update_task_status cancelled`). Identitas task `{"source":"backenddev","ticket_key":<ticketdir>}`
              sama dengan turunan `sync_payload.ticket_key` dari `ticket_source` taskdir. `--push` memanggil server
              langsung (MCP key `.claude/nataflow.local.json`) dan mencetak satu baris segmen; isi tiket tidak lewat
              konteks model. Tanpa `.claude/nataflow.json` → SKIP.

Keluaran `--json` selalu JSON. Exit 0 = PASS/SKIP/PILIH_WORKSPACE, 1 = ditolak atau FAIL.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    BE_TICKETS_DIR,
    TICKET_AC_RE,
    FrontmatterError,
    cli,
    find_repo_root,
    iter_outside_fences,
    normalize_text,
    normalize_ticket_path,
    plugin_file,
    resolve_evidence_path,
    split_frontmatter,
    ticket_seal,
    ticket_seal_norm,
    tracked_files,
)
import nataflow_sync as ns  # noqa: E402

PREFIX = "TICKET"
SOURCE = "backenddev"
KIND = "backend-ticket"
TICKET_FILE = "TICKET.md"
TEMPLATE = ("skills", "ticket", "templates", "ticket-template.md")
IGNORE_FILE = f"{BE_TICKETS_DIR}/.gitignore"
IGNORE_TEXT = (
    "# Ditulis `backend:ticket` (`ticket.py new`, Langkah 40): tiket hidup di disk dan dicerminkan ke nataflow,\n"
    "# tidak pernah di-commit. Pola `*` ikut mengabaikan berkas ini sendiri; jangan di-commit.\n"
    "*\n"
)
NAME_RE = re.compile(r"^\d{10}-([a-z0-9]+(?:-[a-z0-9]+)*)$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_MAX = 48
STATUSES = ("DRAFT", "READY", "CANCELLED")
OPEN_STATES = ("DRAFT", "READY", "DRIFT")
SECTIONS = ("Permintaan", "Kondisi Sekarang", "Perubahan", "Acceptance Criteria", "Dampak Kontrak")
AC_MAX = 5
IMPACTS = ("aditif", "mengubah", "menghapus", "tidak ada")
IMPACT_RE = re.compile(r"^[\W_]*(aditif|mengubah|menghapus|tidak ada)\b", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"<isi\b|\{\{")
EVIDENCE_RE = re.compile(r"`([^`\s:]+):(\d+)(?:-(\d+))?`")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_NA = ("", "-")


# ── Dasar ─────────────────────────────────────────────────────────────────────

def _git(root: Path, *args: str) -> Tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        return 255, str(exc)
    return r.returncode, r.stdout.strip()


def is_git(root: Path) -> bool:
    return _git(root, "rev-parse", "--is-inside-work-tree") == (0, "true")


def read_ticket(path: Path) -> Tuple[Optional[str], str]:
    """Isi `TICKET.md` → `(teks, masalah)`; non-UTF-8 atau tak terbaca menjadi masalah, bukan traceback."""
    try:
        return normalize_text(path.read_bytes().decode("utf-8")), ""
    except UnicodeDecodeError as exc:
        return None, f"{path.name} bukan UTF-8 ({exc.reason} @ byte {exc.start})"
    except OSError as exc:
        return None, f"{path.name} tidak terbaca ({exc.strerror or exc})"


def rel_ticketdir(root: Path, value: str) -> str:
    """Nilai `--ticketdir` (relatif, absolut di bawah root, atau path `TICKET.md`) → path ticketdir relatif root."""
    rel = normalize_ticket_path(value).rstrip("/")
    path = Path(rel)
    if path.is_absolute():
        try:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return rel
    if rel.endswith("/" + TICKET_FILE):
        rel = rel[: -len(TICKET_FILE) - 1]
    return rel


def ticketdir_problem(root: Path, rel: str) -> str:
    head, _, name = rel.rpartition("/")
    if head != BE_TICKETS_DIR or not NAME_RE.match(name):
        return f"`{rel}` bukan direktori {BE_TICKETS_DIR}/<YYMMDDhhmm>-<slug>"
    if not (root / rel / TICKET_FILE).is_file():
        return f"`{rel}/{TICKET_FILE}` tidak ada"
    return ""


def frontmatter_bounds(text: str) -> Tuple[int, int]:
    """Indeks baris pagar pembuka dan penutup frontmatter; `(-1, -1)` bila tidak ada."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return -1, -1
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), -1)
    return (0, end) if end > 0 else (-1, -1)


def set_fields(text: str, **fields: Any) -> str:
    """Tulis ulang kunci frontmatter tingkat atas (yang belum ada ditambahkan sebelum pagar penutup)."""
    lines = text.split("\n")
    _, end = frontmatter_bounds(text)
    if end < 0:
        raise FrontmatterError("frontmatter tidak ada atau tidak tertutup")
    pending = dict(fields)
    for i in range(1, end):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:", lines[i])
        if m and m.group(1) in pending:
            lines[i] = f"{m.group(1)}: {pending.pop(m.group(1))}"
    lines[end:end] = [f"{k}: {v}" for k, v in pending.items()]
    return "\n".join(lines)


def int_field(fm: Dict[str, str], key: str) -> int:
    value = str(fm.get(key, "0")).strip() or "0"
    return int(value) if value.isdigit() else 0


def h1_of(body: str) -> str:
    for _, line in iter_outside_fences(body):
        m = re.match(r"^# +(\S.*)$", line)
        if m:
            return m.group(1).strip()
    return ""


def sections_of(body: str) -> List[Tuple[str, List[Tuple[int, str]]]]:
    """`[(judul H2, [(nomor baris badan, baris), …]), …]` di luar fence, berurutan."""
    out: List[Tuple[str, List[Tuple[int, str]]]] = []
    for no, line in iter_outside_fences(body):
        if line.startswith("## "):
            out.append((line[3:].strip(), []))
        elif re.match(r"^# +\S", line):
            continue
        elif out:
            out[-1][1].append((no, line))
    return out


def impact_of(body: str) -> str:
    for title, lines in sections_of(body):
        if title == "Dampak Kontrak":
            first = next((l.strip() for _, l in lines if l.strip()), "")
            m = IMPACT_RE.match(first)
            return m.group(1).lower() if m else ""
    return ""


def now_stamp() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def emit(as_json: bool, payload: Dict[str, Any], line: str) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False) if as_json else line)


def fail(as_json: bool, problems: List[str], **extra: Any) -> int:
    emit(as_json, {"status": "FAIL", "problems": problems, **extra}, f"{PREFIX} FAIL: " + "; ".join(problems))
    return 1


# ── Keadaan ───────────────────────────────────────────────────────────────────

def classify(root: Path, rel: str) -> Dict[str, Any]:
    """Keadaan satu ticketdir dari isi `TICKET.md` di disk."""
    info: Dict[str, Any] = {"ticketdir": rel, "ticket": f"{rel}/{TICKET_FILE}", "state": "RUSAK", "title": "",
                            "note": "", "approvals": 0}
    text, problem = read_ticket(root / rel / TICKET_FILE)
    if text is None:
        info["note"] = problem
        return info
    try:
        fm, body = split_frontmatter(text)
    except FrontmatterError as exc:
        info["note"] = str(exc)
        return info
    info.update(title=h1_of(body), approvals=int_field(fm, "approvals"))
    if fm.get("kind") != KIND:
        info["note"] = f"`kind: {fm.get('kind', '-')}` bukan `{KIND}`"
        return info
    status = fm.get("status", "")
    if status == "DRAFT":
        info["state"] = "DRAFT"
    elif status == "CANCELLED":
        info["state"] = "DIBATALKAN"
    elif status == "READY":
        seal = str(fm.get("approved_seal") or "-").strip()
        norm = str(fm.get("approved_seal_norm") or "-").strip()
        if seal not in _NA and (ticket_seal(text) == seal or (norm not in _NA and ticket_seal_norm(text) == norm)):
            info["state"] = "READY"
        else:
            info["state"] = "DRIFT"
            info["note"] = ("isi berubah sesudah disetujui" if seal not in _NA else "READY tanpa `approved_seal`")
    else:
        info["note"] = f"status `{status or '-'}` bukan {' | '.join(STATUSES)}"
    return info


def ticketdirs(root: Path) -> List[str]:
    base = root / BE_TICKETS_DIR
    if not base.is_dir():
        return []
    return sorted(f"{BE_TICKETS_DIR}/{p.name}" for p in base.iterdir() if p.is_dir() and NAME_RE.match(p.name))


def users_of(root: Path) -> Dict[str, List[str]]:
    """`ticketdir → [taskdir]` dari `ticket_source` di `backenddev/docs/*/TASK.md`."""
    out: Dict[str, List[str]] = {}
    docs = root / "backenddev" / "docs"
    if not docs.is_dir():
        return out
    for task in sorted(docs.glob("*/TASK.md")):
        text, _ = read_ticket(task)
        if text is None:
            continue
        src = normalize_ticket_path(ns.frontmatter_value(text, "ticket_source"))
        if src.endswith("/" + TICKET_FILE):
            out.setdefault(src[: -len(TICKET_FILE) - 1], []).append(task.parent.relative_to(root).as_posix())
    return out


def cmd_state(root: Path, args: argparse.Namespace) -> int:
    users = users_of(root)
    rows = []
    for rel in ticketdirs(root):
        info = classify(root, rel)
        if info["state"] == "DIBATALKAN" and not args.all:
            continue
        info["used_by"] = users.get(rel, [])
        rows.append(info)
    lines = [f"{PREFIX} STATE: {len(rows)} tiket di {BE_TICKETS_DIR}/"]
    for r in rows:
        extra = f" · {r['note']}" if r["note"] else ""
        used = f" · dipakai {', '.join(r['used_by'])}" if r["used_by"] else ""
        lines.append(f"- {r['ticketdir']} · {r['state']} · {r['title'] or '-'}{extra}{used}")
    emit(args.json, {"status": "PASS", "tickets": rows}, "\n".join(lines))
    return 0


# ── new ───────────────────────────────────────────────────────────────────────

def ensure_ignored(root: Path) -> Tuple[str, List[str]]:
    """Penanda `backenddev/tickets/.gitignore` → `(catatan, peringatan)`. Berkas yang sudah ada tidak ditimpa."""
    warnings: List[str] = []
    target = root / IGNORE_FILE
    note = f"`{IGNORE_FILE}` sudah ada"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(IGNORE_TEXT.encode("utf-8"))
        note = f"`{IGNORE_FILE}` ditulis"
    if is_git(root):
        probe = f"{BE_TICKETS_DIR}/0000000000-probe/{TICKET_FILE}"
        if _git(root, "check-ignore", "-q", "--no-index", probe)[0] != 0:
            warnings.append(f"`{BE_TICKETS_DIR}/` tidak diabaikan git — periksa `{IGNORE_FILE}`; tiket jangan di-commit")
        code, tracked = _git(root, "ls-files", "--", BE_TICKETS_DIR)
        if code == 0 and tracked:
            n = len(tracked.splitlines())
            warnings.append(f"{n} berkas di bawah `{BE_TICKETS_DIR}/` ter-track — `.gitignore` tidak berlaku atasnya")
    return note, warnings


def quote(request: str) -> str:
    lines = normalize_text(request).strip("\n").split("\n")
    return "\n".join(f"> {l}".rstrip() for l in lines)


def cmd_new(root: Path, args: argparse.Namespace) -> int:
    slug = args.slug.strip()
    if not SLUG_RE.match(slug) or len(slug) > SLUG_MAX:
        return fail(args.json, [f"slug `{slug}` wajib kebab-case huruf kecil, paling panjang {SLUG_MAX} karakter"])
    title = " ".join(args.title.split())
    if not title or PLACEHOLDER_RE.search(title):
        return fail(args.json, ["`--title` kosong atau berisi placeholder"])
    request = sys.stdin.read() if args.request == "-" else args.request
    if not request.strip():
        return fail(args.json, ["`--request` kosong — salin permintaan asli user apa adanya"])
    for rel in ticketdirs(root):
        m = NAME_RE.match(rel.rpartition("/")[2])
        info = classify(root, rel)
        if m and m.group(1) == slug and info["state"] in OPEN_STATES:
            return fail(args.json, [f"tiket ber-slug `{slug}` masih terbuka: {rel} ({info['state']}) — lanjutkan "
                                    f"tiket itu, atau batalkan dulu lewat `ticket.py cancel`"])
    template = plugin_file(*TEMPLATE)
    if template is None:
        return fail(args.json, [f"templat `{'/'.join(TEMPLATE)}` hilang dari plugin — pasang ulang plugin backend"])
    created = dt.datetime.now().strftime("%y%m%d%H%M")
    rel = f"{BE_TICKETS_DIR}/{created}-{slug}"
    if (root / rel).exists():
        return fail(args.json, [f"`{rel}` sudah ada — tunggu satu menit atau pilih slug lain"])
    text = (normalize_text(template.read_text(encoding="utf-8"))
            .replace("{{slug}}", slug).replace("{{created}}", created).replace("{{title}}", title)
            .replace("{{request}}", quote(request)))
    note, warnings = ensure_ignored(root)
    (root / rel).mkdir(parents=True)
    (root / rel / TICKET_FILE).write_bytes(text.encode("utf-8"))
    line = f"{PREFIX} NEW: {rel}/{TICKET_FILE} (DRAFT) · {note}"
    line += "".join(f"\n  PERINGATAN: {w}" for w in warnings)
    emit(args.json, {"status": "PASS", "ticketdir": rel, "ticket": f"{rel}/{TICKET_FILE}", "note": note,
                     "warnings": warnings}, line)
    return 0


# ── check ─────────────────────────────────────────────────────────────────────

def evidence_problems(root: Path, path: str, start: int, end: Optional[int],
                      tracked: Optional[List[str]] = None) -> str:
    """Masalah satu bukti `path:baris`; kosong = sah. Nama berkas lepas di-resolve ke satu-satunya
    berkas terlacak berakhiran itu (B11); `amazoncorretto:21` dan sejenisnya disaring pemanggil (vonis `bukan`)."""
    if path.startswith("/") or ".." in path.split("/"):
        return f"bukti `{path}:{start}` wajib relatif root repo"
    verdict, full = resolve_evidence_path(root, path, tracked)
    if verdict == "ambigu":
        return f"bukti `{path}:{start}`: nama berkas ambigu ({full}) — tulis path penuh"
    if verdict in ("hilang", "bukan"):
        return f"bukti `{path}:{start}`: berkas tidak ada di repo"
    target = root / full
    try:
        total = len(target.read_bytes().decode("utf-8", "replace").splitlines())
    except OSError as exc:
        return f"bukti `{path}:{start}`: berkas tak terbaca ({exc.strerror or exc})"
    last = end if end is not None else start
    if start < 1 or last < start:
        return f"bukti `{path}:{start}{'-' + str(end) if end else ''}`: rentang baris tidak sah"
    if last > total:
        return f"bukti `{path}:{last}` melewati panjang berkas ({total} baris)"
    return ""


def card_problems(root: Path, rel: str, text: str) -> List[str]:
    """Seluruh masalah mekanis kartu; kosong = PASS."""
    try:
        fm, body = split_frontmatter(text)
    except FrontmatterError as exc:
        return [f"frontmatter: {exc}"]
    problems: List[str] = []
    name = rel.rpartition("/")[2]
    m = NAME_RE.match(name)
    if fm.get("kind") != KIND:
        problems.append(f"frontmatter `kind` wajib `{KIND}`")
    if fm.get("status") not in STATUSES:
        problems.append(f"frontmatter `status` wajib {' | '.join(STATUSES)}")
    if m and fm.get("slug") != m.group(1):
        problems.append(f"frontmatter `slug` (`{fm.get('slug', '-')}`) tidak sama dengan nama ticketdir (`{m.group(1)}`)")
    h1 = [l for _, l in iter_outside_fences(body) if re.match(r"^# +\S", l)]
    if len(h1) != 1:
        problems.append(f"kartu wajib tepat satu H1 judul (ada {len(h1)})")
    holders = [no for no, l in enumerate(body.split("\n"), start=1) if PLACEHOLDER_RE.search(l)]
    if holders:
        problems.append("placeholder templat (`<isi: …>`) belum diganti di baris badan " + ", ".join(map(str, holders)))
    secs = sections_of(body)
    titles = [t for t, _ in secs]
    if titles != list(SECTIONS):
        problems.append("seksi H2 wajib persis dan berurutan: " + " → ".join(SECTIONS)
                        + f" (ada: {' → '.join(titles) or '-'})")
    content = {t: [(no, l) for no, l in lines if l.strip()] for t, lines in secs}
    for title in SECTIONS:
        if title in content and not content[title]:
            problems.append(f"`## {title}` kosong")
    # AC: baris kanonik `- **AC-{n}**: …` hanya di seksinya (dibaca penerima sebagai `TAC-{n}`).
    ac_lines = content.get("Acceptance Criteria", [])
    numbers = []
    for _, line in ac_lines:
        mac = TICKET_AC_RE.match(line)
        if mac:
            numbers.append(int(mac.group(1)))
            if not line[mac.end():].strip():
                problems.append(f"`AC-{mac.group(1)}` tanpa isi")
        elif LIST_ITEM_RE.match(line):
            problems.append(f"butir AC tidak kanonik (`- **AC-{{n}}**: …`): `{line.strip()[:60]}`")
    if "Acceptance Criteria" in content:
        if not numbers:
            problems.append("`## Acceptance Criteria` tanpa baris `- **AC-{n}**: …`")
        elif numbers != list(range(1, len(numbers) + 1)):
            problems.append(f"penomoran AC wajib 1..n berurutan (ada: {', '.join(map(str, numbers))})")
        if len(numbers) > AC_MAX:
            problems.append(f"{len(numbers)} AC melewati batas {AC_MAX} — bukan tiket cepat; arahkan ke "
                            f"`backend:tech-lead`")
    ac_section = {no for no, _ in ac_lines}
    strays = [no for no, l in iter_outside_fences(body) if TICKET_AC_RE.match(l) and no not in ac_section]
    if strays:
        problems.append("baris `- **AC-{n}**:` di luar `## Acceptance Criteria` (baris badan "
                        + ", ".join(map(str, strays)) + ")")
    # Bukti `path:baris` di Kondisi Sekarang: berkas ada, baris dalam jangkauan.
    if "Kondisi Sekarang" in content:
        tracked = tracked_files(root)
        found = [(p, int(a), int(b) if b else None) for _, l in content["Kondisi Sekarang"]
                 for p, a, b in EVIDENCE_RE.findall(l)
                 if resolve_evidence_path(root, p, tracked)[0] != "bukan"]   # tag image, host:port (B11)
        if not found:
            problems.append("`## Kondisi Sekarang` tanpa bukti `path:baris` berbacktick")
        problems.extend(p for p in (evidence_problems(root, *f, tracked=tracked) for f in found) if p)
    if "Dampak Kontrak" in content and content["Dampak Kontrak"] and not impact_of(body):
        problems.append("baris pertama `## Dampak Kontrak` wajib diawali jenis: " + " | ".join(IMPACTS))
    return problems


def load(root: Path, args: argparse.Namespace) -> Tuple[Optional[str], Optional[str], List[str]]:
    rel = rel_ticketdir(root, args.ticketdir)
    problem = ticketdir_problem(root, rel)
    if problem:
        return rel, None, [problem]
    text, problem = read_ticket(root / rel / TICKET_FILE)
    return rel, text, [problem] if problem else []


def cmd_check(root: Path, args: argparse.Namespace) -> int:
    rel, text, problems = load(root, args)
    if problems:
        return fail(args.json, problems, ticketdir=rel)
    problems = card_problems(root, rel, text)
    if problems:
        return fail(args.json, problems, ticketdir=rel)
    emit(args.json, {"status": "PASS", "ticketdir": rel}, f"{PREFIX} CHECK PASS: {rel}/{TICKET_FILE}")
    return 0


# ── approve / reopen / cancel ─────────────────────────────────────────────────

def write(root: Path, rel: str, text: str) -> None:
    (root / rel / TICKET_FILE).write_bytes(text.encode("utf-8"))


def cmd_approve(root: Path, args: argparse.Namespace) -> int:
    rel, text, problems = load(root, args)
    if problems:
        return fail(args.json, problems, ticketdir=rel)
    info = classify(root, rel)
    if info["state"] != "DRAFT":
        return fail(args.json, [f"{rel} {info['state']} — hanya DRAFT yang dapat disetujui"
                                + (" (buka ulang dulu lewat `ticket.py reopen`)" if info["state"] == "DRIFT" else "")],
                    ticketdir=rel)
    problems = card_problems(root, rel, text)
    if problems:
        return fail(args.json, ["`check` belum PASS"] + problems, ticketdir=rel)
    seal, norm = ticket_seal(text), ticket_seal_norm(text)
    fm, _ = split_frontmatter(text)
    new = set_fields(text, status="READY", approved_seal=seal, approved_seal_norm=norm, approved_at=now_stamp(),
                     approvals=int_field(fm, "approvals") + 1)
    if ticket_seal(new) != seal:     # status/segel di luar sidik; penjaga bila field segel berubah kelak
        return fail(args.json, ["segel berubah karena penulisan frontmatter — laporkan sebagai bug plugin"])
    write(root, rel, new)
    emit(args.json, {"status": "PASS", "ticketdir": rel, "ticket": f"{rel}/{TICKET_FILE}", "approved_seal": seal},
         f"{PREFIX} — READY · {rel}/{TICKET_FILE} · segel {seal}")
    return 0


def cmd_reopen(root: Path, args: argparse.Namespace) -> int:
    rel, text, problems = load(root, args)
    if problems:
        return fail(args.json, problems, ticketdir=rel)
    info = classify(root, rel)
    if info["state"] not in ("READY", "DRIFT"):
        return fail(args.json, [f"{rel} {info['state']} — hanya READY/DRIFT yang dapat dibuka ulang"], ticketdir=rel)
    fm, _ = split_frontmatter(text)
    write(root, rel, set_fields(text, status="DRAFT", approved_seal="-", approved_seal_norm="-", approved_at="-",
                                reopened=int_field(fm, "reopened") + 1))
    users = users_of(root).get(rel, [])
    warnings = ([f"dipakai {', '.join(users)} — taskdir itu gagal prasyarat `task` check 7 sampai tiket disetujui "
                 f"ulang"] if users else [])
    line = f"{PREFIX} REOPEN: {rel} → DRAFT" + "".join(f"\n  PERINGATAN: {w}" for w in warnings)
    emit(args.json, {"status": "PASS", "ticketdir": rel, "warnings": warnings}, line)
    return 0


def cmd_cancel(root: Path, args: argparse.Namespace) -> int:
    rel, text, problems = load(root, args)
    if problems:
        return fail(args.json, problems, ticketdir=rel)
    info = classify(root, rel)
    if info["state"] not in OPEN_STATES:
        return fail(args.json, [f"{rel} {info['state']} — hanya DRAFT/READY/DRIFT yang dapat dibatalkan"],
                    ticketdir=rel)
    write(root, rel, set_fields(text, status="CANCELLED", cancelled_at=now_stamp()))
    mirrored = info["approvals"] > 0
    line = f"{PREFIX} CANCEL: {rel} → CANCELLED" + (" · jalankan `sync --push` agar task cermin ikut dibatalkan"
                                                     if mirrored else "")
    emit(args.json, {"status": "PASS", "ticketdir": rel, "sync": mirrored}, line)
    return 0


# ── sync ──────────────────────────────────────────────────────────────────────

def sync_build(root: Path, args: argparse.Namespace, config: Dict[str, Any]
               ) -> Tuple[Optional[Dict[str, Any]], List[str], str]:
    """Argumen tool MCP untuk satu tiket — read-only. `lookup` tanpa `repo` dan tanpa `workspace_id` (pola tiket
    analyst), sehingga task ditemukan di workspace mana pun ia dibuat."""
    rel, text, problems = load(root, args)
    if problems:
        return None, problems, ""
    workspace_id, choices, problems = ns.choose_workspace(config, args.workspace)
    if problems:
        return None, problems, ""
    info = classify(root, rel)
    ident = {"source": SOURCE, "ticket_key": rel}
    lookup = {"metadata": ns.compact(ident)}
    if info["state"] == "DIBATALKAN" and info["approvals"] > 0:
        payload = {"status": "PASS", "enabled": True, "url": config["url"], "ticket_key": rel, "lookup": lookup,
                   "task_status": ns.task_status("cancelled")}
        return payload, [], f"SYNC PASS: {rel} DIBATALKAN · task cermin menjadi cancelled — argumen tool lewat `--json`"
    if info["state"] != "READY":
        return None, [f"{rel} {info['state']} — hanya tiket READY (atau pernah READY lalu dibatalkan) yang "
                      f"disinkronkan"], ""
    fm, body = split_frontmatter(text)
    repo = ns.repo_identity(root, config)
    card = body.strip()
    task = ns.task_args(config, workspace_id, ident, repo, info["title"], card)
    meta = dict(ident, repo=repo, slug=fm.get("slug", ""), kind=KIND, approved_seal=fm.get("approved_seal", "-"),
                dampak_kontrak=impact_of(body), reopened=int_field(fm, "reopened"))
    task["create"]["metadata"] = ns.compact(meta)
    payload = {"status": "PASS", "enabled": True, "url": config["url"], "ticket_key": rel,
               **ns.workspace_fields(workspace_id, choices), "lookup": task["lookup"], "create": task["create"],
               "update": {"title": info["title"], "description": card, "metadata": task["create"]["metadata"]}}
    where = ("pilih: " + ", ".join(c["alias"] for c in choices)) if choices else workspace_id or "-"
    return payload, [], (f"SYNC PASS: {rel} · server {config['url']} · workspace {where} · pic "
                         f"{config['pic_id'] or '-'} — argumen tool lewat `--json`")


def sync_push(session: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Cari task lewat `lookup`, lalu buat, perbarui, atau batalkan. Task kembar berhenti sebelum tool tulis apa pun."""
    from nataflow_client import as_list
    found = as_list(session.call_json("list_task", payload["lookup"], read=True), "tasks", "data")
    if len(found) > 1:
        return ns.push_fail([f"{len(found)} task ber-ticket_key sama ("
                             + ", ".join(f"#{t.get('code') or t.get('id')}" for t in found) + ")"])
    if "task_status" in payload:
        if not found:
            return {"status": "PASS", "outcome": "dilewati (task belum ada)"}
        row, target = found[0], payload["task_status"]
        code = row.get("code") or row.get("id")
        if row.get("status") not in target["from"]:
            return {"status": "PASS", "outcome": f"dilewati (task {row.get('status')} #{code})"}
        session.call_json("update_task_status", {"task_id": row["id"], "status": target["status"]})
        return {"status": "PASS", "outcome": f"dibatalkan #{code}"}
    if found:
        row, verb = session.call_json("update_task", dict(payload["update"], task_id=found[0]["id"])), "diperbarui"
    elif payload.get("workspace_choices"):
        return ns.push_choose(payload["workspace_choices"])
    else:
        row, verb = session.call_json("create_task", payload["create"]), "dibuat"
    return {"status": "PASS", "outcome": f"{verb} #{row.get('code') or row.get('id')}"}


def sync_segment(result: Dict[str, Any]) -> str:
    return "nataflow " + (result["outcome"] if result["status"] == "PASS" else ns.push_segment(result, ""))


def cmd_sync(root: Path, args: argparse.Namespace) -> int:
    config, problems = ns.load_config(root)
    payload, line = None, ""
    if not problems and config is not None:
        payload, problems, line = sync_build(root, args, config)
    if args.push:
        result = (ns.push_fail(problems) if problems else {"status": "SKIP"} if config is None
                  else ns.run_push(root, config, lambda s: sync_push(s, payload)))
        return ns.emit_push(result, args.json, sync_segment(result))
    if problems:
        return ns.emit_fail(args.json, "SYNC", problems)
    if config is None:
        return ns.emit_skip(args.json, "SYNC")
    ns.emit(payload, args.json, line)
    return 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Siklus hidup tiket cepat backend:ticket")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("state")
    s.add_argument("--all", action="store_true", help="ikut tampilkan tiket DIBATALKAN")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("new")
    s.add_argument("--slug", required=True)
    s.add_argument("--title", required=True, help="judul kartu (H1)")
    s.add_argument("--request", required=True, help="permintaan asli user apa adanya, atau `-` untuk stdin")
    s.add_argument("--json", action="store_true")
    for name in ("check", "approve", "reopen", "cancel"):
        s = sub.add_parser(name)
        s.add_argument("--ticketdir", required=True)
        s.add_argument("--json", action="store_true")
    s = sub.add_parser("sync")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--workspace", default="", help="alias `workspaces` tujuan task baru")
    s.add_argument("--push", action="store_true", help="kirim langsung ke server lewat MCP key lokal")
    s.add_argument("--json", action="store_true")
    args = p.parse_args()
    root = find_repo_root()
    return {"state": cmd_state, "new": cmd_new, "check": cmd_check, "approve": cmd_approve, "reopen": cmd_reopen,
            "cancel": cmd_cancel, "sync": cmd_sync}[args.cmd](root, args)


if __name__ == "__main__":
    sys.exit(cli(main))
