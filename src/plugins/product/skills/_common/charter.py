#!/usr/bin/env python3
"""CLI siklus hidup charterdir plugin `product`.

Tiap charterdir `product/<slug>/` memuat `CHARTER.md`: kartu enam pilar di atas, `## Catatan Elisitasi` sebagai H2
terakhir. `review.md` (opsional) adalah jejak blok `## Charter Review` terakhir, hanya ditulis `review --report`.
Field `status` (ELICITATION/DRAFT/APPROVED/CANCELLED) dan seluruh field pembukuan hanya ditulis skrip ini.

Keadaan yang divonis `state` (diturunkan dari status, kartu, vonis review, dan sidik):

- `EMPTY`       — direktori kosong sisa alokasi gagal; `new` memakainya ulang.
- `ELICITATION` — catatan elisitasi terbuka (product:discover).
- `DRAFT`       — catatan tertutup; kartu belum ditulis atau belum lolos review atas isinya sekarang (product:spec).
- `REVIEW`      — kartu lolos `charter-reviewer` atas sidik sekarang; menunggu keputusan user.
- `APPROVED`    — disetujui user dan isi sama dengan yang dimateraikan.
- `DRIFT`       — APPROVED tetapi disunting sesudah disetujui.
- `CANCELLED`, `BROKEN`.

Subcommand:

- `guard`   — guard konteks minimum read-only (product:init, sebelum folder dibuat).
- `state`   — pindai `product/*/`, vonis keadaan dan rute tiap charterdir.
- `new`     — guard konteks minimum + kecocokan mode dengan ruang kerja, lalu alokasikan `product/<slug>/`
              beserta `CHARTER.md` awal (Konteks Awal, Permintaan Asli, `context_hash`, `request_hash`).
- `check`   — prasyarat gate `discover` / `spec` atas satu charterdir.
- `close`   — tutup elisitasi: status DRAFT + segel catatan (`elicit_hash`, `elicit_log`).
- `review`  — catat vonis `charter-reviewer` beserta sidik konten yang dinilainya (dan bloknya).
- `revise`  — buka putaran revisi draft atas permintaan user (plafon 3 per basis fakta).
- `approve` — materai APPROVED sesudah jawaban eksplisit user; commit bila repo git.
- `commit`  — commit draft (`--stage draft`) atau elisitasi tertahan (`--stage tertunda`).
- `reopen`  — buka ulang: `--to draft` (APPROVED/DRIFT → DRAFT) atau `--to elicitation` (DRAFT/APPROVED →
              ELICITATION, baris log `Dibuka ulang` ditulis skrip).
- `cancel`  — tutup charterdir atas keputusan user.

Kontrak exit `close`/`approve`/`cancel`/`commit`: 0 = tertulis dan ter-commit (atau tanpa git, `--no-commit`, atau
diabaikan `.gitignore`), 1 = ditolak, 3 = tertulis tetapi commit gagal.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from charter_lib import (  # noqa: E402
    CHARTER_FILE,
    CHARTERDIR_RE,
    CONTEXT_KEYS,
    CONTEXT_LABELS,
    ELICIT_H2,
    MODES,
    PRODUCT_DIR,
    REVIEW_FILE,
    SLUG_MAX,
    SLUG_RE,
    Checker,
    append_log_row,
    charter_skeleton,
    clean_value,
    content_hash,
    context_problems,
    detect_workspace,
    find_root,
    format_report,
    git_commit,
    git_error_line,
    git_mode,
    is_git_repo,
    log_rows,
    mode_problem,
    normalize_dir,
    report_json,
    set_frontmatter_field,
    split_frontmatter,
    split_parts,
    workspace_problem,
)
from validate_doc import DocValidator  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REVISION_CAP = 3
REVIEW_CAP = 2
REVIEW_VALUE = re.compile(r"^(PASS|BLOCKED) @([0-9a-f]{12})/([0-9a-f]{12})$")
REPORT_BLOCKERS = re.compile(r"^- BLOCKER:\s*(\d+)\s*\[MEKANIS\]\s*·\s*(\d+)\s*\[SEMANTIK\]\s*$", re.MULTILINE)
REPORT_ROUND = re.compile(r"^- Ronde:\s*(\d+)\b", re.MULTILINE)
REOPEN_ROW = "dibuka ulang"
# Berkas plugin yang dibaca tiap gate; instalasi yang kehilangannya gagal di `check`, bukan di tengah fase.
GATE_FILES = {
    "discover": ("discover/templates/charter-skeleton.md", "discover/references/elicitation-guide.md",
                 "discover/dispatcher/scout.md"),
    "spec": ("spec/templates/charter-template.md", "spec/dispatcher/reviewer.md"),
}


def text_of(path: Path) -> str:
    """Isi berkas charter; non-UTF-8 → FAIL rapi (exit 1) yang menyebut berkasnya, bukan traceback."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"FAIL: {path} bukan UTF-8 ({exc.reason} @ byte {exc.start}) — pulihkan dari git "
                         f"(`git checkout -- <berkas>`) atau simpan ulang sebagai UTF-8; jangan menebak isinya")


def decodes(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except UnicodeDecodeError:
        return False


def read(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    fm, _ = split_frontmatter(text_of(path))
    return fm


def write_fields(path: Path, **fields: str) -> None:
    text = text_of(path)
    for key, value in fields.items():
        text = set_frontmatter_field(text, key, value)
    path.write_text(text, encoding="utf-8")


def int_field(fm: Dict[str, Any], key: str) -> int:
    """Field pembukuan bilangan; nilai rusak → FAIL rapi. Field absen dibaca 0."""
    raw = str(fm.get(key, "0")).strip()
    if not raw.isdigit():
        raise SystemExit(f"FAIL: field `{key}: {raw}` bukan bilangan — field ini hanya ditulis charter.py; "
                         f"pulihkan nilainya dari riwayat git, dilarang menebak")
    return int(raw)


def parse_review(value: Any) -> Any:
    """`PASS @<kartu>/<elisitasi>` → (verdict, sidik kartu, sidik elisitasi); selain itu None."""
    m = REVIEW_VALUE.match(str(value).strip())
    return m.groups() if m else None


def review_digest(charterdir: Path) -> str:
    """Sidik gabungan yang dinilai reviewer: `<sidik kartu>/<sidik catatan elisitasi>`."""
    f = charterdir / CHARTER_FILE
    if not f.is_file():
        return "-/-"
    text = text_of(f)
    return f"{content_hash(text, 'card')}/{content_hash(text, 'elicit')}"


def review_report(charterdir: Path, fm: Dict[str, Any]) -> Any:
    """`review.md` bila kepalanya mencatat ronde dan vonis yang sama dengan frontmatter; blok lama → None."""
    f = charterdir / REVIEW_FILE
    review = str(fm.get("review", "")).strip()
    if not f.is_file() or not parse_review(review) or not decodes(f):
        return None
    head = text_of(f).split("\n", 1)[0]
    return f if f"ronde {fm.get('review_round', '-')}/{REVIEW_CAP} · {review} ·" in head else None


def seal_problem(text: str) -> str:
    """Catatan elisitasi dibanding segel `close`; string kosong = cocok."""
    fm, _ = split_frontmatter(text)
    sealed = str(fm.get("elicit_hash", "-")).strip() or "-"
    if sealed == "-":
        return "catatan elisitasi tanpa segel — tutup lewat `charter.py close`"
    current = content_hash(text, "elicit")
    if sealed != current:
        return (f"catatan elisitasi ({current}) berubah sesudah ditutup (segel {sealed}) — hanya product:discover "
                "yang mengubah fakta: pulihkan catatannya, atau `charter.py reopen --to elicitation` lalu "
                "`charter.py close`")
    return ""


def next_round(fm: Dict[str, Any], text: str) -> int:
    """Ronde review berikutnya (1-based); basis fakta baru membuka siklus ronde baru."""
    rnd = int_field(fm, "review_round")
    prev = parse_review(fm.get("review", ""))
    if prev and prev[2] != content_hash(text, "elicit"):
        rnd = 0
    return rnd + 1


def report_problems(report: str, verdict: str, rnd: int) -> List[str]:
    """Blok `## Charter Review` yang bertentangan dengan dirinya sendiri atau dengan ronde yang dicatat."""
    counts = REPORT_BLOCKERS.search(report)
    if not counts:
        return ["blok tanpa baris `- BLOCKER: <n> [MEKANIS] · <n> [SEMANTIK]`"]
    problems = []
    total = int(counts.group(1)) + int(counts.group(2))
    items: List[str] = []
    head = re.search(r"^\*\*BLOCKER:\*\*\s*$", report, re.MULTILINE)
    for line in (report[head.end():].splitlines() if head else []):
        s = line.strip()
        if s.startswith("**"):
            break
        if s.startswith("- ") and s not in ("- —", "- -"):
            items.append(s)
    if len(items) != total:
        problems.append(f"hitungan BLOCKER {total} ≠ {len(items)} butir di bawah `**BLOCKER:**`")
    if verdict == "PASS" and total:
        problems.append(f"Verdict PASS dengan {total} BLOCKER — `BLOCKED` ⇔ minimal satu BLOCKER")
    if verdict == "BLOCKED" and not total:
        problems.append("Verdict BLOCKED tanpa satu BLOCKER pun")
    said = REPORT_ROUND.search(report)
    if not said or int(said.group(1)) != rnd:
        problems.append(f"`- Ronde: {said.group(1) if said else 'tidak ada'}` ≠ ronde yang dicatat {rnd} — slot "
                        "`{round}` dihidrasi dari `ronde` keluaran `check --gate spec`")
    return problems


def has_card(path: Path) -> bool:
    """Kartu sudah ditulis `spec`: ada H2 lain di atas `## Catatan Elisitasi`."""
    _, body = split_frontmatter(text_of(path))
    card, _ = split_parts(body)
    return any(l.startswith("## ") for l in card.splitlines())


def title_of(path: Path) -> str:
    _, body = split_frontmatter(text_of(path))
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "-"


def classify(root: Path, rel: str) -> Dict[str, str]:
    """Keadaan satu charterdir → rute berikutnya."""
    f = root / rel / CHARTER_FILE
    row = {"charterdir": rel, "mode": "-", "title": "-"}
    if not f.is_file():
        return dict(row, state="EMPTY", route="product:init → product:discover memakai ulang direktori ini")
    if not decodes(f):
        return dict(row, state="BROKEN", route=f"{CHARTER_FILE} bukan UTF-8 — pulihkan dari git atau simpan ulang "
                                                "sebagai UTF-8")
    fm = read(f)
    status = fm.get("status", "")
    row.update(mode=str(fm.get("mode", "-")), title=title_of(f))
    if status == "CANCELLED":
        return dict(row, state="CANCELLED", route="-")
    if status not in ("ELICITATION", "DRAFT", "APPROVED") or fm.get("mode") not in MODES:
        return dict(row, state="BROKEN", route=f"status/mode tidak sah (status {status or '-'}, mode "
                                               f"{fm.get('mode', '-')}) — laporkan ke user")
    if not split_parts(split_frontmatter(text_of(f))[1])[1]:
        return dict(row, state="BROKEN", route=f"CHARTER.md tanpa `## {ELICIT_H2}` — laporkan ke user")
    if status == "ELICITATION":
        return dict(row, state="ELICITATION", route="product:discover (lanjutkan pertanyaan terbuka)")
    if status == "APPROVED":
        if not has_card(f):
            return dict(row, state="BROKEN", route="APPROVED tanpa kartu — pulihkan isinya dari git")
        if str(fm.get("approved_hash", "")) != content_hash(text_of(f)):
            return dict(row, state="DRIFT", route="CHARTER APPROVED disunting sesudah disetujui — product:spec "
                                                  "(reopen) atau pulihkan isinya")
        return dict(row, state="APPROVED", route="selesai — Scope `S<n>` siap dipecah jadi tiket")
    if not has_card(f):
        return dict(row, state="DRAFT", route="product:spec (tulis kartu enam pilar)")
    if str(fm.get("review", "")) == f"PASS @{review_digest(f.parent)}":
        return dict(row, state="REVIEW", route="product:spec (ajukan keputusan ke user)")
    return dict(row, state="DRAFT", route="product:spec (review atau revisi draft)")


def charterdirs(root: Path) -> List[str]:
    """Subdirektori `product/` yang memuat `CHARTER.md` atau kosong; direktori lain (mis. kode) diabaikan."""
    base = root / PRODUCT_DIR
    if not base.is_dir():
        return []
    out = []
    for p in sorted(base.iterdir()):
        if p.is_dir() and ((p / CHARTER_FILE).is_file() or not any(p.iterdir())):
            out.append(f"{PRODUCT_DIR}/{p.name}")
    return out


# ── subcommand ────────────────────────────────────────────────────────────────

def _context(args: argparse.Namespace) -> Dict[str, str]:
    return {k: getattr(args, k) for k in CONTEXT_KEYS}


def cmd_guard(root: Path, args: argparse.Namespace) -> int:
    problems = context_problems(args.mode, _context(args))
    labels = CONTEXT_LABELS.get(args.mode, ())
    if args.json:
        print(json.dumps({"status": "FAIL" if problems else "PASS", "mode": args.mode,
                          "labels": dict(zip(CONTEXT_KEYS, labels)), "problems": problems},
                         indent=2, ensure_ascii=False))
    else:
        print(("GUARD FAIL: " + "; ".join(problems)) if problems
              else f"GUARD PASS: {args.mode} · " + " · ".join(labels))
    return 1 if problems else 0


def cmd_state(root: Path, args: argparse.Namespace) -> int:
    rows = [classify(root, rel) for rel in charterdirs(root)]
    if not args.all:
        rows = [r for r in rows if r["state"] not in ("CANCELLED", "APPROVED")]
    if args.json:
        print(json.dumps({"root": str(root), "charterdirs": rows}, indent=2, ensure_ascii=False))
        return 0
    if not rows:
        print("CHARTER STATE: nihil charterdir" + ("" if args.all else " terbuka"))
        return 0
    print(f"CHARTER STATE: {len(rows)} charterdir")
    for r in rows:
        print(f"- {r['charterdir']} · {r['state']} · {r['mode']} · {r['title']}\n    → {r['route']}")
    return 0


def cmd_new(root: Path, args: argparse.Namespace) -> int:
    """Guard, lalu alokasikan charterdir dan tulis `CHARTER.md` awal sekaligus."""
    if not SLUG_RE.match(args.slug) or len(args.slug) > SLUG_MAX:
        print(f"NEW FAIL: slug `{args.slug}` bukan kebab-case ≤{SLUG_MAX} karakter")
        return 1
    problem = workspace_problem(root)
    if problem:
        print(f"NEW FAIL: {problem} — buat atau masuk ke folder proyek lebih dulu")
        return 1
    problems = context_problems(args.mode, _context(args))
    if problems:
        print("NEW FAIL: konteks minimum belum terpenuhi — " + "; ".join(problems)
              + " (product:init, skills/init/references/konteks-minimum.md)")
        return 1
    ws = detect_workspace(root)
    problem = mode_problem(args.mode, ws["workspace"], args.confirm_workspace)
    if problem:
        print(f"NEW FAIL: {problem} (bukti ruang kerja: {ws['evidence']})")
        return 1
    request = sys.stdin.read() if args.request == "-" else args.request
    if not request.strip():
        print("NEW FAIL: --request kosong — minta user menempelkan permintaan aslinya")
        return 1
    if not args.requester.strip():
        print("NEW FAIL: --requester kosong — tanyakan nama atau peran peminta")
        return 1
    rel = f"{PRODUCT_DIR}/{args.slug}"
    d = root / rel
    reused = False
    if d.exists():
        if not d.is_dir():
            print(f"NEW FAIL: {rel} sudah ada dan bukan direktori — pilih slug lain")
            return 1
        if (d / CHARTER_FILE).is_file():
            r = classify(root, rel)
            print(f"NEW FAIL: slug `{args.slug}` sudah dipakai {rel} ({r['state']}) — lanjutkan itu, atau pilih "
                  f"slug lain (mis. `{args.slug}-v2`)")
            return 1
        if any(d.iterdir()):
            print(f"NEW FAIL: {rel} sudah ada berisi berkas lain — pilih slug lain")
            return 1
        reused = True
    title = " ".join(args.title.split()) or args.slug.replace("-", " ").capitalize()
    text = charter_skeleton(args.mode, args.slug, args.requester, dt.date.today().isoformat(), title, request,
                            _context(args))
    d.mkdir(parents=True, exist_ok=True)
    (d / CHARTER_FILE).write_text(text, encoding="utf-8")
    print(f"NEW PASS: {rel} · root={root} · git={git_mode(root, f'{rel}/{CHARTER_FILE}')} · mode={args.mode} · "
          f"workspace={ws['workspace']}" + (" · direktori EMPTY dipakai ulang" if reused else ""))
    return 0


def cmd_check(root: Path, args: argparse.Namespace) -> int:
    rel = normalize_dir(args.charterdir, root)
    c = Checker()
    d = root / rel
    ok = bool(CHARTERDIR_RE.match(rel)) and (d / CHARTER_FILE).is_file()
    c.add(1, "Charterdir sah", ok, rel if ok else f"`{rel}` bukan product/<slug> ber-{CHARTER_FILE}",
          "Alokasikan lewat `charter.py new` dari product:discover.")
    missing = [f for f in GATE_FILES[args.gate] if not (PLUGIN_ROOT / "skills" / f).is_file()]
    c.add(2, "Berkas plugin", not missing, "lengkap" if not missing else ", ".join(missing),
          "Instalasi plugin rusak — pasang ulang plugin product.")
    resolved: Dict[str, str] = {"root": str(root), "git": git_mode(root, f"{rel}/{CHARTER_FILE}")}
    if ok:
        state = classify(root, rel)
        resolved["keadaan"] = state["state"]
        resolved["mode"] = state["mode"]
        if args.gate == "discover":
            c.add(3, "Keadaan menerima elisitasi", state["state"] == "ELICITATION", state["state"],
                  "DRAFT/REVIEW/APPROVED/DRIFT dibuka ulang hanya lewat `charter.py reopen --to elicitation` "
                  "dari product:spec." if state["state"] in ("DRAFT", "REVIEW", "APPROVED", "DRIFT")
                  else state["route"])
        else:
            c.add(3, "Keadaan menerima spec", state["state"] in ("DRAFT", "REVIEW"), state["state"],
                  "APPROVED/DRIFT → `charter.py reopen` atas keputusan user; ELICITATION → selesaikan "
                  "product:discover." if state["state"] in ("APPROVED", "DRIFT", "ELICITATION") else state["route"])
            if state["state"] in ("DRAFT", "REVIEW"):
                v = DocValidator("notes", rel, root)
                c.add(4, "Catatan elisitasi sah", v.run_all(), "validator PASS" if v.ok else "validator FAIL",
                      "Jalankan `validate_doc.py --kind notes`; perbaikan fakta lewat product:discover (reopen).")
                text = text_of(d / CHARTER_FILE)
                problem = seal_problem(text)
                c.add(5, "Catatan elisitasi tersegel", not problem,
                      problem.split(" — ")[0] if problem else "segel cocok", problem.split(" — ", 1)[-1])
                fm = read(d / CHARTER_FILE)
                resolved["kartu"] = "ada" if has_card(d / CHARTER_FILE) else "belum"
                resolved["revision"] = str(fm.get("revision", "0"))
                resolved["review_round"] = str(fm.get("review_round", "0"))
                raw = str(fm.get("review_round", "0")).strip()
                nxt = next_round(fm, text) if raw.isdigit() else 0
                resolved["ronde"] = str(nxt) if 0 < nxt <= REVIEW_CAP else "habis" if nxt else "-"
                digest = review_digest(d)
                resolved["sidik"] = digest
                resolved["review_segar"] = "ya" if str(fm.get("review", "")) == f"PASS @{digest}" else "tidak"
                prev, cur = parse_review(fm.get("review", "")), digest.split("/")
                stale = [n for n, i in (("kartu", 1), ("elisitasi", 2)) if prev and prev[i] != cur[i - 1]]
                resolved["review_basi"] = "belum" if not prev else (",".join(stale) or "-")
                report = review_report(d, fm)
                resolved["review_report"] = f"{rel}/{REVIEW_FILE}" if report else "-"
    print(report_json(c.results, charterdir=rel, **resolved) if args.json
          else format_report(f"prasyarat {args.gate}", c.results, resolved))
    return 0 if c.ok else 1


def _charter_path(root: Path, args: argparse.Namespace) -> Path:
    rel = normalize_dir(args.charterdir, root)
    if not CHARTERDIR_RE.match(rel):
        raise SystemExit(f"FAIL: `{rel}` bukan charterdir product/<slug>")
    path = root / rel / CHARTER_FILE
    if not path.is_file():
        raise SystemExit(f"FAIL: {rel}/{CHARTER_FILE} tidak ada — alokasikan lewat `charter.py new`")
    return path


def _slug(path: Path) -> str:
    return path.parent.name


def _commit(root: Path, args: argparse.Namespace, msg: str, paths: List[str], subject: str) -> int:
    """Commit opsional sesudah isi tertulis; exit 3 bila commit gagal."""
    if not is_git_repo(root) or getattr(args, "no_commit", False):
        print(msg + (" · tanpa git" if not is_git_repo(root) else ""))
        return 0
    ok, out = git_commit(root, paths, subject)
    if not ok:
        quoted = subject.replace('"', '\\"')
        print(f"{msg} · COMMIT GAGAL: {git_error_line(out)} — isi sudah tertulis; commit manual "
              f"`git -C {root} add -- {' '.join(paths)} && git -C {root} commit -m \"{quoted}\" -- {' '.join(paths)}` "
              f"sesudah sebabnya dibereskan")
        return 3
    print(msg + f" · commit {out}")
    return 0


def cmd_close(root: Path, args: argparse.Namespace) -> int:
    """Tutup elisitasi dan segel catatannya; satu-satunya penulis status DRAFT dari ELICITATION."""
    path = _charter_path(root, args)
    rel = str(path.parent.relative_to(root).as_posix())
    text = text_of(path)
    fm, _ = split_frontmatter(text)
    if fm.get("status") != "ELICITATION":
        print(f"CLOSE FAIL: status `{fm.get('status', '-')}`, bukan ELICITATION — catatan sudah tertutup; perubahan "
              f"fakta lewat `charter.py reopen --to elicitation`")
        return 1
    sealed = str(fm.get("elicit_hash", "-")).strip() or "-"
    rows = log_rows(text)
    if sealed not in ("-", content_hash(text, "elicit")):
        since = rows[int_field(fm, "elicit_log"):]
        if not any(r[2].lower().startswith(REOPEN_ROW) for r in since):
            print(f"CLOSE FAIL: catatan berubah sejak segel {sealed} tanpa baris log `Dibuka ulang` — buka ulang "
                  f"hanya lewat `charter.py reopen --to elicitation`")
            return 1
    closed = set_frontmatter_field(text, "status", "DRAFT")
    path.write_text(closed, encoding="utf-8")
    v = DocValidator("notes", rel, root)
    if not v.run_all():
        path.write_text(text, encoding="utf-8")         # kembalikan apa adanya; elisitasi tetap terbuka
        print("CLOSE FAIL: validate_doc.py --kind notes FAIL pada catatan tertutup — status tetap ELICITATION\n"
              + format_report(f"validate {CHARTER_FILE} (notes)", v.results))
        return 1
    seal = content_hash(closed, "elicit")
    write_fields(path, elicit_hash=seal, elicit_log=str(len(rows)))
    msg = f"CLOSE PASS: {rel}/{CHARTER_FILE} DRAFT · segel {seal} · {len(rows)} log"
    return _commit(root, args, msg, [f"{rel}/{CHARTER_FILE}"], f"docs(product): elisitasi {_slug(path)}")


def cmd_review(root: Path, args: argparse.Namespace) -> int:
    path = _charter_path(root, args)
    rel = str(path.parent.relative_to(root).as_posix())
    fm = read(path)
    if fm.get("status") != "DRAFT":
        print(f"REVIEW FAIL: status `{fm.get('status', '-')}`, bukan DRAFT")
        return 1
    if args.verdict == "DISPATCH_FAILED":
        print("REVIEW PASS: dispatch gagal dicatat, tidak dihitung ronde")
        return 0
    bad = [k for k in ("charter", "notes") if not DocValidator(k, rel, root).run_all()]
    if bad:
        print("REVIEW FAIL: " + ", ".join(f"validate_doc.py --kind {k} FAIL" for k in bad)
              + " — dispatch tidak sah; perbaiki draft lalu dispatch ulang")
        return 1
    rnd = next_round(fm, text_of(path)) - 1
    if rnd >= REVIEW_CAP:
        print(f"REVIEW FAIL: plafon {REVIEW_CAP} ronde per revisi habis — sajikan temuan tersisa ke user")
        return 1
    if not args.report:
        print(f"REVIEW FAIL: --verdict {args.verdict} tanpa `--report` — teruskan blok `## Charter Review` "
              f"reviewer apa adanya (`--report -` lewat stdin)")
        return 1
    try:
        report = sys.stdin.read() if args.report == "-" else Path(args.report).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"REVIEW FAIL: --report `{args.report}` tak terbaca ({exc.__class__.__name__}: {exc})")
        return 1
    if not re.search(r"^## Charter Review\s*$", report, re.MULTILINE):
        print("REVIEW FAIL: --report bukan blok `## Charter Review` reviewer")
        return 1
    said = re.search(r"^- Verdict:\s*(PASS|BLOCKED)\b", report, re.MULTILINE)
    if not said or said.group(1) != args.verdict:
        print(f"REVIEW FAIL: --verdict {args.verdict} tidak sama dengan `- Verdict:` di blok "
              f"({said.group(1) if said else 'tidak ada'}) — catat vonis reviewer apa adanya")
        return 1
    digest = review_digest(path.parent)
    seen = re.search(r"^- Sidik:\s*(\S+)", report, re.MULTILINE)
    if not seen or seen.group(1).strip("`") != digest:
        print(f"REVIEW FAIL: sidik yang dinilai reviewer `{seen.group(1) if seen else 'tidak ada'}` ≠ sidik disk "
              f"`{digest}` — draft berubah sesudah dispatch, atau prompt tanpa `{{sidik}}`; dispatch ulang "
              f"(`check --gate spec` memberi `sidik`)")
        return 1
    sealed = seal_problem(text_of(path))
    if sealed:
        print(f"REVIEW FAIL: {sealed}")
        return 1
    problems = report_problems(report, args.verdict, rnd + 1)
    if problems:
        print("REVIEW FAIL: blok reviewer tidak konsisten — " + "; ".join(problems)
              + " — dispatch ulang; dilarang menyunting blok balikan")
        return 1
    write_fields(path, review=f"{args.verdict} @{digest}", review_round=str(rnd + 1))
    (path.parent / REVIEW_FILE).write_text(
        f"<!-- ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest} · ditulis charter.py review; "
        f"jangan disunting -->\n{report.strip()}\n", encoding="utf-8")
    print(f"REVIEW PASS: ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest} · blok tersimpan {rel}/{REVIEW_FILE}")
    return 0


def cmd_revise(root: Path, args: argparse.Namespace) -> int:
    path = _charter_path(root, args)
    fm = read(path)
    if fm.get("status") != "DRAFT":
        print(f"REVISE FAIL: status `{fm.get('status', '-')}`, bukan DRAFT; APPROVED dibuka lewat `reopen`")
        return 1
    base = content_hash(text_of(path), "elicit")
    rev = int_field(fm, "revision") if str(fm.get("revision_base", base)) == base else 0
    if rev >= REVISION_CAP:
        print(f"REVISE FAIL: plafon {REVISION_CAP} revisi habis — lingkup belum jelas; `charter.py reopen --to "
              f"elicitation` atau `cancel` atas keputusan user")
        return 1
    write_fields(path, revision=str(rev + 1), revision_base=base, review="-", review_round="0")
    print(f"REVISE PASS: revisi {rev + 1}/{REVISION_CAP}")
    return 0


def cmd_approve(root: Path, args: argparse.Namespace) -> int:
    path = _charter_path(root, args)
    rel = str(path.parent.relative_to(root).as_posix())
    fm = read(path)
    errors = []
    if fm.get("status") != "DRAFT":
        errors.append(f"status `{fm.get('status', '-')}` bukan DRAFT")
    for kind in ("charter", "notes"):
        if not DocValidator(kind, rel, root).run_all():
            errors.append(f"validate_doc.py --kind {kind} FAIL")
    problem = seal_problem(text_of(path))
    if problem:
        errors.append(problem)
    digest = review_digest(path.parent)
    if str(fm.get("review", "")) != f"PASS @{digest}":
        errors.append(f"vonis review terakhir `{fm.get('review', '-')}` bukan `PASS @{digest}` (belum direview, "
                      f"BLOCKED, atau charter berubah sesudah review → review ulang)")
    if not args.answer.strip():
        errors.append("jawaban user kosong")
    if errors:
        print("APPROVE FAIL: " + "; ".join(errors))
        return 1
    report = review_report(path.parent, fm)
    write_fields(path, status="APPROVED", approved=dt.date.today().isoformat(),
                 approved_hash=content_hash(text_of(path)), approval=clean_value(args.answer))
    sealed = content_hash(text_of(path))
    msg = f"APPROVE PASS: {rel}/{CHARTER_FILE} APPROVED @{sealed}"
    paths = [f"{rel}/{CHARTER_FILE}"] + ([f"{rel}/{REVIEW_FILE}"] if report else [])
    return _commit(root, args, msg, paths, f"docs(product): kunci CHARTER {_slug(path)} APPROVED")


def cmd_commit(root: Path, args: argparse.Namespace) -> int:
    path = _charter_path(root, args)
    rel = str(path.parent.relative_to(root).as_posix())
    fm = read(path)
    want = "DRAFT" if args.stage == "draft" else "ELICITATION"
    if fm.get("status") != want:
        print(f"COMMIT FAIL: status `{fm.get('status', '-')}`, bukan {want} untuk --stage {args.stage}")
        return 1
    paths = [f"{rel}/{CHARTER_FILE}"]
    if args.stage == "draft":
        paths += [f"{rel}/{REVIEW_FILE}"] if (path.parent / REVIEW_FILE).is_file() else []
        subject = f"docs(product): {'revise' if int_field(fm, 'revision') else 'draft'} CHARTER {_slug(path)}"
    else:
        subject = f"docs(product): elisitasi {_slug(path)} (tertunda)"
    return _commit(root, args, f"COMMIT PASS: {' '.join(paths)}", paths, subject)


def cmd_reopen(root: Path, args: argparse.Namespace) -> int:
    path = _charter_path(root, args)
    fm = read(path)
    status = fm.get("status", "")
    if not args.reason.strip():
        print("REOPEN FAIL: alasan kosong")
        return 1
    allowed = {"draft": ("APPROVED",), "elicitation": ("DRAFT", "APPROVED")}[args.to]
    if status not in allowed:
        print(f"REOPEN FAIL: status `{status or '-'}` tidak dapat dibuka ke {args.to} (sah: {'|'.join(allowed)})")
        return 1
    n = int_field(fm, "reopened") + 1
    reset = dict(review="-", review_round="0", approved="-", approved_hash="-", approval="-", reopened=str(n),
                 reopen_reason=clean_value(args.reason))
    if args.to == "draft":
        write_fields(path, status="DRAFT", revision="0", **reset)
        print(f"REOPEN PASS: CHARTER.md DRAFT (buka ulang ke-{n})")
        return 0
    try:
        text = append_log_row(text_of(path), dt.date.today().isoformat(), "Dibuka ulang", args.reason,
                              "product:spec")
    except ValueError as exc:
        print(f"REOPEN FAIL: {exc} — catatan elisitasi rusak; pulihkan dari git")
        return 1
    path.write_text(text, encoding="utf-8")
    write_fields(path, status="ELICITATION", **reset)
    print(f"REOPEN PASS: CHARTER.md ELICITATION (buka ulang ke-{n}) · baris log `Dibuka ulang` ditulis")
    return 0


def cmd_cancel(root: Path, args: argparse.Namespace) -> int:
    rel = normalize_dir(args.charterdir, root)
    d = root / rel
    if not CHARTERDIR_RE.match(rel) or not d.is_dir():
        print(f"CANCEL FAIL: `{rel}` bukan charterdir sah")
        return 1
    f = d / CHARTER_FILE
    if not f.is_file():
        if any(d.iterdir()):
            print(f"CANCEL FAIL: {rel} tanpa {CHARTER_FILE} tetapi berisi berkas lain — periksa dan hapus manual")
            return 1
        d.rmdir()
        print(f"CANCEL PASS: {rel} (direktori kosong dihapus)")
        return 0
    if not args.reason.strip():
        print("CANCEL FAIL: alasan kosong")
        return 1
    try:
        status = read(f).get("status", "")
    except SystemExit:
        status = ""
    if status == "APPROVED" and not args.force:
        print(f"CANCEL FAIL: {rel} APPROVED — mungkin sudah menjadi acuan tim; batalkan hanya atas keputusan "
              f"eksplisit user dengan `--force`")
        return 1
    try:
        write_fields(f, status="CANCELLED", cancel_reason=clean_value(args.reason))
    except (ValueError, SystemExit) as exc:
        print(f"CANCEL FAIL: {exc} — perbaiki atau hapus {rel} manual atas keputusan user")
        return 1
    return _commit(root, args, f"CANCEL PASS: {rel} ({CHARTER_FILE})", [f"{rel}/{CHARTER_FILE}"],
                   f"docs(product): batalkan CHARTER {d.name}")


def _add_context(s: argparse.ArgumentParser) -> None:
    s.add_argument("--mode", required=True, type=str.upper, choices=MODES)
    s.add_argument("--untuk", default="", help="NEW_PRODUCT: segmen pengguna · NEW_FEATURE: pengguna · "
                                               "IMPROVEMENT: yang terdampak")
    s.add_argument("--masalah", default="", help="NEW_PRODUCT: masalah utama · NEW_FEATURE: yang belum bisa "
                                                 "dilakukan · IMPROVEMENT: yang salah atau kurang")
    s.add_argument("--lingkup", default="", help="NEW_PRODUCT: domain · NEW_FEATURE: area/modul · "
                                                 "IMPROVEMENT: fitur yang mana")


def main() -> None:
    p = argparse.ArgumentParser(description="Siklus hidup charterdir product")
    p.add_argument("--root", default=None, help="root ruang kerja; default root git atau cwd")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("guard")
    _add_context(s)
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("state")
    s.add_argument("--all", action="store_true", help="ikut tampilkan APPROVED dan CANCELLED")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("new")
    s.add_argument("--slug", required=True)
    _add_context(s)
    s.add_argument("--requester", required=True, help="nama atau peran peminta")
    s.add_argument("--request", required=True, help="permintaan asli apa adanya, atau `-` untuk stdin")
    s.add_argument("--title", default="", help="judul kerja H1; default dari slug")
    s.add_argument("--confirm-workspace", action="store_true", dest="confirm_workspace",
                   help="user mengonfirmasi NEW_PRODUCT di ruang kerja yang memuat kode")
    s = sub.add_parser("check")
    s.add_argument("--gate", required=True, choices=("discover", "spec"))
    s.add_argument("--charterdir", required=True)
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("close")
    s.add_argument("--charterdir", required=True)
    s.add_argument("--no-commit", action="store_true", dest="no_commit")
    s = sub.add_parser("review")
    s.add_argument("--charterdir", required=True)
    s.add_argument("--verdict", required=True, choices=("PASS", "BLOCKED", "DISPATCH_FAILED"))
    s.add_argument("--report", default="", help="blok `## Charter Review` reviewer: path berkas atau `-` (stdin)")
    s = sub.add_parser("revise")
    s.add_argument("--charterdir", required=True)
    s = sub.add_parser("approve")
    s.add_argument("--charterdir", required=True)
    s.add_argument("--answer", required=True, help="jawaban user apa adanya")
    s.add_argument("--no-commit", action="store_true", dest="no_commit")
    s = sub.add_parser("commit")
    s.add_argument("--charterdir", required=True)
    s.add_argument("--stage", required=True, choices=("draft", "tertunda"))
    s = sub.add_parser("reopen")
    s.add_argument("--charterdir", required=True)
    s.add_argument("--to", required=True, choices=("draft", "elicitation"))
    s.add_argument("--reason", required=True)
    s = sub.add_parser("cancel")
    s.add_argument("--charterdir", required=True)
    s.add_argument("--reason", required=True)
    s.add_argument("--force", action="store_true", help="wajib untuk charter APPROVED (keputusan eksplisit user)")
    s.add_argument("--no-commit", action="store_true", dest="no_commit")
    args = p.parse_args()
    root = (Path(args.root) if args.root else find_root()).resolve()
    handler = {"guard": cmd_guard, "state": cmd_state, "new": cmd_new, "check": cmd_check, "close": cmd_close,
               "review": cmd_review, "revise": cmd_revise, "approve": cmd_approve, "commit": cmd_commit,
               "reopen": cmd_reopen, "cancel": cmd_cancel}[args.cmd]
    sys.exit(handler(root, args))


if __name__ == "__main__":
    main()
