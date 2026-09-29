#!/usr/bin/env python3
"""CLI siklus hidup ticketdir plugin `analyst`.

Tiap ticketdir memuat `TICKET.md`: kartu tiket di atas, `## Catatan Elisitasi` sebagai H2
terakhir. `review.md` (opsional) adalah jejak blok `## Ticket Review` terakhir, hanya ditulis
`review --report`. Frontmatter `elicitation` (OPEN/CLOSED) milik `analyst:elicit`; `status`
(DRAFT/READY/CANCELLED) milik skrip ini kecuali DRAFT awal.

Satu-satunya jalan mutasi status yang punya konsekuensi di luar penulisnya:

- `state`   — pindai `analyst/tickets/*/`, vonis keadaan dan rute tiap ticketdir.
- `new`     — alokasikan `analyst/tickets/<YYMMDDhhmm>-<slug>/` beserta `TICKET.md` awal (kerangka,
              permintaan asli, `request_hash`); menolak slug kembar terbuka, memakai ulang yang `KOSONG`.
- `check`   — prasyarat gate `elicit` / `spec` atas satu ticketdir.
- `close`   — tutup elisitasi: `elicitation: CLOSED` + segel catatan (`elicit_hash`, `elicit_log`).
- `review`  — catat vonis `ticket-reviewer` beserta sidik konten yang dinilainya (dan bloknya).
- `revise`  — buka putaran revisi draft atas permintaan user (plafon 3 per siklus persetujuan).
- `approve` — materai `TICKET.md` `READY` sesudah jawaban eksplisit user; commit bila repo git.
- `reopen`  — buka ulang tiket `READY` menjadi `DRAFT` untuk perubahan permintaan.
- `cancel`  — tutup ticketdir atas keputusan user.
- `ref`     — isi `external_ref` (kunci kartu Jira/Trello) pada DRAFT maupun READY.
- `sync-payload` — isi argumen tool MCP nataflow untuk tiket READY (`list_task`/`create_task`/`update_task`
              beserta `upsert_document` `review.md`) atau tiket pernah-READY yang dibatalkan
              (`update_task_status cancelled`); read-only, tanpa commit, dan tidak pernah menulis `TICKET.md`.

`approve` menuntut kedua validator (`ticket`, `elicit`) `PASS`, `elicitation: CLOSED`, catatan elisitasi
sama dengan segel `close`, **dan** vonis review `PASS` atas sidik `<kartu>/<catatan elisitasi>` yang sama
persis dengan sekarang: draft yang disunting sesudah direview, atau elisitasi yang dibuka dan berubah
sesudahnya, tidak dapat disetujui.

Kontrak exit `close`/`approve`/`ref`/`cancel`: 0 = tertulis dan ter-commit (atau tanpa git/`--no-commit`;
`ref` pada DRAFT tidak meng-commit), 1 = ditolak, 3 = tertulis tetapi commit gagal.

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
from analyst_lib import (  # noqa: E402
    ELICIT_H2,
    SLUG_RE,
    SYNC_CONFIG,
    TICKET_FILE,
    TICKETDIR_RE,
    TICKETS_DIR,
    TYPES,
    Checker,
    clean_value,
    content_hash,
    find_root,
    format_report,
    git_commit,
    git_error_line,
    is_git_repo,
    load_sync_config,
    log_rows,
    normalize_ticketdir,
    report_json,
    set_frontmatter_field,
    split_frontmatter,
    split_parts,
    ticket_seal,
    ticket_skeleton,
)
from validate_doc import DocValidator  # noqa: E402
import nataflow_sync as ns  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REVISION_CAP = 3
REVIEW_CAP = 2
REVIEW_FILE = "review.md"  # blok `## Ticket Review` terakhir, ditulis hanya oleh `ticket.py review --report`
REVIEW_VALUE = re.compile(r"^(PASS|BLOCKED) @([0-9a-f]{12})/([0-9a-f]{12})$")
REPORT_BLOCKERS = re.compile(r"^- BLOCKER:\s*(\d+)\s*\[MEKANIS\]\s*·\s*(\d+)\s*\[SEMANTIK\]\s*$", re.MULTILINE)
REPORT_ROUND = re.compile(r"^- Ronde:\s*(\d+)\b", re.MULTILINE)
REOPEN_ROW = "dibuka ulang"  # kolom pertanyaan baris log pembukaan ulang elisitasi (elicit Phase 0)


def text_of(path: Path) -> str:
    """Isi berkas tiket; non-UTF-8 → FAIL rapi (exit 1) yang menyebut berkasnya, bukan traceback."""
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
    """Field pembukuan bilangan; nilai rusak → FAIL rapi, bukan traceback. Field absen dibaca 0."""
    raw = str(fm.get(key, "0")).strip()
    if not raw.isdigit():
        raise SystemExit(f"FAIL: field `{key}: {raw}` bukan bilangan — field ini hanya ditulis ticket.py; "
                         f"pulihkan nilainya dari riwayat git, dilarang menebak")
    return int(raw)


def parse_review(value: Any) -> Any:
    """`PASS @<kartu>/<elisitasi>` → (verdict, sidik kartu, sidik elisitasi); selain itu None."""
    m = REVIEW_VALUE.match(str(value).strip())
    return m.groups() if m else None


def review_report(ticketdir: Path, fm: Dict[str, Any]) -> Any:
    """`review.md` bila kepalanya mencatat ronde dan vonis yang sama dengan frontmatter; blok lama → None."""
    f = ticketdir / REVIEW_FILE
    review = str(fm.get("review", "")).strip()
    if not f.is_file() or not parse_review(review):
        return None
    head = text_of(f).split("\n", 1)[0]
    return f if f"ronde {fm.get('review_round', '-')}/{REVIEW_CAP} · {review} ·" in head else None


def review_digest(ticketdir: Path) -> str:
    """Sidik gabungan yang dinilai reviewer: `<sidik kartu>/<sidik catatan elisitasi>`."""
    f = ticketdir / TICKET_FILE
    if not f.is_file():
        return "-/-"
    text = text_of(f)
    return f"{content_hash(text, 'card')}/{content_hash(text, 'elicit')}"


def seal_problem(text: str) -> str:
    """Catatan elisitasi dibanding segel `close`; string kosong = cocok.

    Hanya `analyst:elicit` yang mengubah fakta, dan tiap perubahan melewati `close` lagi. Tanpa segel ini,
    `spec` dapat menyesuaikan catatan dengan kartunya, dan satu baris kosong di catatan me-reset plafon ronde.
    """
    fm, _ = split_frontmatter(text)
    sealed = str(fm.get("elicit_hash", "-")).strip() or "-"
    current = content_hash(text, "elicit")
    if sealed == "-":
        return "elisitasi tanpa segel — tutup lewat `ticket.py close` (tiket lama: sekali, untuk adopsi segel)"
    if sealed != current:
        return (f"catatan elisitasi ({current}) berubah sesudah ditutup (segel {sealed}) — hanya analyst:elicit "
                "yang mengubah fakta: pulihkan catatannya, atau buka ulang elisitasi (baris log `Dibuka ulang`) "
                "lalu `ticket.py close`")
    return ""


def next_round(fm: Dict[str, Any], text: str) -> int:
    """Ronde review yang akan dicatat berikutnya (1-based); basis fakta baru membuka siklus ronde baru."""
    rnd = int_field(fm, "review_round")
    prev = parse_review(fm.get("review", ""))
    if prev and prev[2] != content_hash(text, "elicit"):
        rnd = 0  # basis fakta berubah sesudah ronde terakhir → siklus ronde baru (pola revision_base)
    return rnd + 1


def report_problems(report: str, verdict: str, rnd: int) -> List[str]:
    """Blok `## Ticket Review` yang isinya bertentangan dengan dirinya sendiri atau dengan ronde yang dicatat."""
    problems = []
    counts = REPORT_BLOCKERS.search(report)
    if not counts:
        return ["blok tanpa baris `- BLOCKER: <n> [MEKANIS] · <n> [SEMANTIK]`"]
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
    if not path.is_file():
        return "-"
    _, body = split_frontmatter(text_of(path))
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "-"


def classify(root: Path, rel: str) -> Dict[str, str]:
    """Keadaan satu ticketdir → rute berikutnya."""
    d = root / rel
    ticket = d / TICKET_FILE
    if ticket.is_file() and not decodes(ticket):   # satu tiket rusak tidak menghentikan pemindaian `state`
        return {"ticketdir": rel, "type": "-", "title": "-", "state": "RUSAK",
                "route": f"{TICKET_FILE} bukan UTF-8 — pulihkan dari git atau simpan ulang sebagai UTF-8"}
    t = read(ticket)
    es, ts = t.get("elicitation", ""), t.get("status", "")
    row = {"ticketdir": rel, "type": t.get("type", "-"), "title": title_of(ticket)}
    if not TICKETDIR_RE.match(rel):
        row.update(state="NAMA_TIDAK_SAH", route=f"bukan ticketdir analyst — ganti nama ke {TICKETS_DIR}/"
                                                 "<YYMMDDhhmm>-<slug> (git mv) atau pindahkan keluar analyst/tickets/")
    elif ts == "CANCELLED":
        row.update(state="DIBATALKAN", route="-")
    elif not ticket.is_file():
        row.update(state="KOSONG", route="analyst:intake → analyst:elicit menulis TICKET.md ke ticketdir ini")
    elif es not in ("OPEN", "CLOSED") or ts not in ("DRAFT", "READY"):
        row.update(state="RUSAK", route=f"status tidak sah (elicitation {es or '-'}, status {ts or '-'})")
    elif not split_parts(split_frontmatter(text_of(ticket))[1])[1]:
        row.update(state="RUSAK", route=f"TICKET.md tanpa `## {ELICIT_H2}` — laporkan ke user")
    elif ts == "READY" and (es == "OPEN" or not has_card(ticket)):
        row.update(state="RUSAK", route="tiket READY dengan elisitasi OPEN atau tanpa kartu — `reopen` "
                                        "dulu lewat spec, atau pulihkan isinya")
    elif es == "OPEN":
        row.update(state="ELISITASI", route="analyst:elicit (lanjutkan pertanyaan terbuka)")
    elif not has_card(ticket):
        row.update(state="SPEC", route="analyst:spec (tulis kartu tiket)")
    elif ts == "DRAFT":
        row.update(state="DRAFT", route="analyst:spec (ajukan keputusan atau revisi)")
    elif str(t.get("approved_hash", "")) != content_hash(text_of(ticket)) or \
            str(t.get("approved_seal", "-")) not in ("-", "", ticket_seal(text_of(ticket))):
        row.update(state="DRIFT", route="TICKET READY disunting sesudah disetujui — analyst:spec REVISE "
                                        "(reopen) atau pulihkan isinya")
    else:
        row.update(state="READY", route="selesai — serahkan path TICKET.md sebagai ticket_source ke "
                                        "backend:tech-lead / frontend:lead")
    return row


def ticketdirs(root: Path) -> List[str]:
    base = root / TICKETS_DIR
    if not base.is_dir():
        return []
    return sorted(f"{TICKETS_DIR}/{p.name}" for p in base.iterdir() if p.is_dir())


# ── subcommand ────────────────────────────────────────────────────────────────

def cmd_state(root: Path, args: argparse.Namespace) -> int:
    rows = [classify(root, rel) for rel in ticketdirs(root)]
    if not args.all:
        rows = [r for r in rows if r["state"] not in ("DIBATALKAN",) and (args.ready or r["state"] != "READY")]
    if args.json:
        import json
        print(json.dumps({"root": str(root), "ticketdirs": rows}, indent=2, ensure_ascii=False))
        return 0
    if not rows:
        print("TICKET STATE: nihil ticketdir terbuka")
        return 0
    print(f"TICKET STATE: {len(rows)} ticketdir")
    for r in rows:
        print(f"- {r['ticketdir']} · {r['state']} · {r['type']} · {r['title']}\n    → {r['route']}")
    return 0


def cmd_new(root: Path, args: argparse.Namespace) -> int:
    """Alokasikan ticketdir dan tulis `TICKET.md` awal sekaligus — tanpa jendela ticketdir `KOSONG`."""
    if not SLUG_RE.match(args.slug) or len(args.slug) > 40:
        print(f"NEW FAIL: slug `{args.slug}` bukan kebab-case ≤40 karakter")
        return 1
    request = sys.stdin.read() if args.request == "-" else args.request
    if not request.strip():
        print("NEW FAIL: --request kosong — minta user menempelkan permintaan atau keluhan aslinya")
        return 1
    if not args.requester.strip():
        print("NEW FAIL: --requester kosong — tanyakan nama atau peran peminta (analyst:intake Phase 6)")
        return 1
    reuse = None
    for rel in ticketdirs(root):
        r = classify(root, rel)
        if r["state"] == "NAMA_TIDAK_SAH" or rel.split("-", 1)[-1] != args.slug:
            continue
        if r["state"] == "KOSONG":
            reuse = rel            # sisa `new` lama yang gagal sebelum menulis: pakai ulang, jangan menumpuk
        elif r["state"] not in ("DIBATALKAN", "READY"):
            print(f"NEW FAIL: slug `{args.slug}` masih terbuka di {rel} ({r['state']}) — lanjutkan itu, "
                  f"atau pilih slug lain")
            return 1
    rel = reuse or f"{TICKETS_DIR}/{dt.datetime.now().strftime('%y%m%d%H%M')}-{args.slug}"
    if not reuse and (root / rel).exists():
        print(f"NEW FAIL: {rel} sudah ada (slug sama dalam menit yang sama) — tunggu satu menit atau pilih slug lain")
        return 1
    title = " ".join(args.title.split()) or args.slug.replace("-", " ").capitalize()
    text = ticket_skeleton(args.type, args.slug, args.requester, dt.date.today().isoformat(), title, request)
    (root / rel).mkdir(parents=True, exist_ok=True)
    (root / rel / TICKET_FILE).write_text(text, encoding="utf-8")
    print(f"NEW PASS: {rel} · root={root} · git={'ya' if is_git_repo(root) else 'tidak'} · type={args.type}"
          + (" · ticketdir KOSONG dipakai ulang" if reuse else ""))
    return 0


def cmd_check(root: Path, args: argparse.Namespace) -> int:
    rel = normalize_ticketdir(args.ticketdir, root)
    c = Checker()
    d = root / rel
    ok = bool(TICKETDIR_RE.match(rel)) and d.is_dir()
    c.add(1, "Ticketdir sah", ok, rel if ok else f"`{rel}` bukan direktori analyst/tickets/<YYMMDDhhmm>-<slug>",
          "Alokasikan lewat `ticket.py new` dari analyst:intake.")
    gate = args.gate
    needed = {"elicit": ("elicit/templates/elicit-template.md", "elicit/references/elicitation-guide.md"),
              "spec": ("spec/templates/ticket-template.md", "spec/dispatcher/reviewer.md")}[gate]
    missing = [f for f in needed if not (PLUGIN_ROOT / "skills" / f).is_file()]
    c.add(2, "Berkas plugin", not missing, "lengkap" if not missing else ", ".join(missing),
          "Instalasi plugin rusak — pasang ulang plugin analyst.")
    resolved: Dict[str, str] = {"root": str(root), "git": "ya" if is_git_repo(root) else "tidak"}
    if ok:
        state = classify(root, rel)
        resolved["keadaan"] = state["state"]
        t = read(d / TICKET_FILE) if decodes(d / TICKET_FILE) or not (d / TICKET_FILE).is_file() else {}
        if gate == "elicit":
            allowed = ("KOSONG", "ELISITASI") + (("SPEC", "DRAFT") if args.reopen else ())
            c.add(3, "Keadaan menerima elisitasi", state["state"] in allowed, state["state"],
                  "Elisitasi CLOSED dibuka ulang hanya dengan `--reopen` atas permintaan user; tiket READY "
                  "wajib `ticket.py reopen` lebih dulu." if state["state"] in ("SPEC", "DRAFT", "READY", "DRIFT")
                  else state["route"])
        else:
            c.add(3, "Keadaan menerima spec", state["state"] in ("SPEC", "DRAFT"), state["state"],
                  "READY/DRIFT → `ticket.py reopen` atas keputusan user; ELISITASI → selesaikan analyst:elicit."
                  if state["state"] in ("READY", "DRIFT", "ELISITASI") else state["route"])
            v = DocValidator("elicit", rel, root)
            vok = v.run_all()
            c.add(4, "Catatan elisitasi CLOSED & sah", vok and t.get("elicitation") == "CLOSED",
                  f"elicitation {t.get('elicitation', '-')}, validator {'PASS' if vok else 'FAIL'}",
                  "Jalankan `validate_doc.py --kind elicit` dan tutup elisitasi lewat analyst:elicit.")
            if t.get("elicitation") == "CLOSED":
                problem = seal_problem(text_of(d / TICKET_FILE))
                c.add(5, "Catatan elisitasi tersegel", not problem,
                      problem.split(" — ")[0] if problem else f"segel {t.get('elicit_hash')} cocok",
                      problem.split(" — ", 1)[-1])
            resolved["type"] = str(t.get("type", "-"))
            if state["state"] == "DRAFT":
                text = text_of(d / TICKET_FILE)
                resolved["revision"] = str(t.get("revision", "0"))
                resolved["review_round"] = str(t.get("review_round", "0"))
                raw = str(t.get("review_round", "0")).strip()
                nxt = next_round(t, text) if raw.isdigit() else 0
                resolved["ronde"] = str(nxt) if 0 < nxt <= REVIEW_CAP else "habis" if nxt else "-"  # slot `{round}`
                digest = review_digest(d)
                resolved["sidik"] = digest          # slot `{sidik}` prompt dispatch reviewer
                fresh = str(t.get("review", "")) == f"PASS @{digest}"
                resolved["review_segar"] = "ya" if fresh else "tidak"
                prev, cur = parse_review(t.get("review", "")), digest.split("/")
                stale = [n for n, i in (("kartu", 1), ("elisitasi", 2)) if prev and prev[i] != cur[i - 1]]
                resolved["review_basi"] = "belum" if not prev else (",".join(stale) or "-")
                report = review_report(d, t)
                resolved["review_report"] = f"{rel}/{REVIEW_FILE}" if report else "-"
    print(report_json(c.results, ticketdir=rel, **resolved) if args.json
          else format_report(f"prasyarat {gate}", c.results, resolved))
    return 0 if c.ok else 1


def _ticket_path(root: Path, args: argparse.Namespace) -> Path:
    rel = normalize_ticketdir(args.ticketdir, root)
    if not TICKETDIR_RE.match(rel):
        raise SystemExit(f"FAIL: `{rel}` bukan ticketdir sah")
    return root / rel / TICKET_FILE


def cmd_review(root: Path, args: argparse.Namespace) -> int:
    path = _ticket_path(root, args)
    fm = read(path)
    if fm.get("status") != "DRAFT":
        print(f"REVIEW FAIL: TICKET.md berstatus `{fm.get('status', '-')}`, bukan DRAFT")
        return 1
    if args.verdict == "DISPATCH_FAILED":
        print("REVIEW PASS: dispatch gagal dicatat, tidak dihitung ronde")
        return 0
    rel = str(path.parent.relative_to(root))
    bad = [k for k in ("ticket", "elicit") if not DocValidator(k, rel, root).run_all()]
    if bad:
        print("REVIEW FAIL: " + ", ".join(f"validate_doc.py --kind {k} FAIL" for k in bad)
              + " — dispatch tidak sah; perbaiki draft (atau kembali ke analyst:elicit) lalu dispatch ulang")
        return 1
    rnd = next_round(fm, text_of(path)) - 1
    if rnd >= REVIEW_CAP:
        print(f"REVIEW FAIL: plafon {REVIEW_CAP} ronde per revisi habis — sajikan temuan tersisa ke user")
        return 1
    # Vonis tanpa blok reviewer tidak sah: `--report` wajib, dan blok itu membawa sidik yang disalin
    # reviewer dari prompt dispatch. Sidik itu harus sama dengan konten disk sekarang, sehingga vonis
    # terikat pada konten yang benar-benar dibaca reviewer, bukan pada konten saat `review` dijalankan.
    if not args.report:
        print(f"REVIEW FAIL: --verdict {args.verdict} tanpa `--report` — teruskan blok `## Ticket Review` "
              f"reviewer apa adanya (`--report -` lewat stdin)")
        return 1
    try:
        report = sys.stdin.read() if args.report == "-" else Path(args.report).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"REVIEW FAIL: --report `{args.report}` tak terbaca ({exc.__class__.__name__}: {exc})")
        return 1
    if not re.search(r"^## Ticket Review\s*$", report, re.MULTILINE):
        print("REVIEW FAIL: --report bukan blok `## Ticket Review` reviewer")
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
    if report:
        (path.parent / REVIEW_FILE).write_text(
            f"<!-- ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest} · ditulis ticket.py review; "
            f"jangan disunting -->\n{report.strip()}\n", encoding="utf-8")
    print(f"REVIEW PASS: ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest}"
          + (f" · blok tersimpan {rel}/{REVIEW_FILE}" if report else ""))
    return 0


def cmd_revise(root: Path, args: argparse.Namespace) -> int:
    path = _ticket_path(root, args)
    fm = read(path)
    if fm.get("status") != "DRAFT":
        print(f"REVISE FAIL: TICKET.md berstatus `{fm.get('status', '-')}`; READY dibuka lewat `reopen`")
        return 1
    # Plafon berlaku per basis fakta: elisitasi yang dibuka ulang dan berubah memulai siklus baru,
    # karena draft sesudahnya disusun dari fakta yang berbeda, bukan diredaksi ulang.
    base = content_hash(text_of(path), "elicit")
    rev = int_field(fm, "revision") if str(fm.get("revision_base", base)) == base else 0
    if rev >= REVISION_CAP:
        print(f"REVISE FAIL: plafon {REVISION_CAP} revisi habis — lingkup belum jelas; kembali ke analyst:elicit "
              f"(`check --gate elicit --reopen`) atau `cancel` atas keputusan user")
        return 1
    write_fields(path, revision=str(rev + 1), revision_base=base, review="-", review_round="0")
    print(f"REVISE PASS: revisi {rev + 1}/{REVISION_CAP}")
    return 0


def cmd_close(root: Path, args: argparse.Namespace) -> int:
    """Tutup elisitasi dan segel catatannya; satu-satunya penulis `elicitation: CLOSED`."""
    path = _ticket_path(root, args)
    rel = str(path.parent.relative_to(root))
    if not path.is_file():
        print(f"CLOSE FAIL: {rel}/{TICKET_FILE} tidak ada — alokasikan lewat `ticket.py new`")
        return 1
    text = text_of(path)
    fm, _ = split_frontmatter(text)
    if fm.get("status") != "DRAFT":
        print(f"CLOSE FAIL: TICKET.md berstatus `{fm.get('status', '-')}`, bukan DRAFT — tiket READY dibuka lewat "
              f"`reopen` (analyst:spec) lebih dulu")
        return 1
    sealed = str(fm.get("elicit_hash", "-")).strip() or "-"
    notes = content_hash(text, "elicit")
    rows = log_rows(text)
    adopted = False
    if fm.get("elicitation") == "CLOSED":
        if sealed == notes:
            print(f"CLOSE PASS: {rel}/{TICKET_FILE} sudah tertutup, segel {sealed} cocok — tidak ada yang ditulis")
            return 0
        if sealed != "-":
            print(f"CLOSE FAIL: {seal_problem(text)}")
            return 1
        prev = parse_review(fm.get("review", ""))
        if prev and prev[2] != notes:   # tiket lama: adopsi hanya bila catatan sama dengan yang terakhir direview
            print("CLOSE FAIL: tiket lama tanpa segel, dan catatan elisitasi berubah sesudah review terakhir — "
                  "buka ulang elisitasi (`elicitation: OPEN` + baris log `Dibuka ulang`) lalu `ticket.py close`")
            return 1
        adopted = True
    elif fm.get("elicitation") == "OPEN":
        if sealed not in ("-", notes):
            since = rows[int_field(fm, "elicit_log"):]
            if not any(r[2].lower().startswith(REOPEN_ROW) for r in since):
                print(f"CLOSE FAIL: catatan berubah sejak segel {sealed} tanpa baris log baru `Dibuka ulang` — "
                      "tiap pembukaan ulang elisitasi dicatat di log (elicit Phase 0) sebelum ditutup lagi")
                return 1
    else:
        print(f"CLOSE FAIL: elicitation `{fm.get('elicitation', '-')}` bukan OPEN|CLOSED")
        return 1
    closed = set_frontmatter_field(text, "elicitation", "CLOSED")
    path.write_text(closed, encoding="utf-8")
    v = DocValidator("elicit", rel, root)
    if not v.run_all():
        path.write_text(text, encoding="utf-8")         # kembalikan apa adanya; elisitasi tetap terbuka
        print("CLOSE FAIL: validate_doc.py --kind elicit FAIL pada CLOSED — elisitasi tetap "
              f"{fm.get('elicitation')}\n" + format_report(f"validate {TICKET_FILE} (elicit)", v.results))
        return 1
    seal = content_hash(closed, "elicit")
    write_fields(path, elicit_hash=seal, elicit_log=str(len(rows)))
    msg = f"CLOSE PASS: {rel}/{TICKET_FILE} elicitation CLOSED · segel {seal} · {len(rows)} log" \
          + (" · segel diadopsi (tiket lama)" if adopted else "")
    if is_git_repo(root) and not args.no_commit:
        paths = [f"{rel}/{TICKET_FILE}"]
        subject = f"docs(ticket): elisitasi {rel.split('-', 1)[-1]}"
        ok, out = git_commit(root, paths, subject)
        if not ok:
            return _commit_failed(msg, root, paths, out, subject)
        msg += f" · commit {out}"
    print(msg)
    return 0


def cmd_approve(root: Path, args: argparse.Namespace) -> int:
    path = _ticket_path(root, args)
    fm = read(path)
    rel = str(path.parent.relative_to(root))
    errors = []
    if fm.get("status") != "DRAFT":
        errors.append(f"status `{fm.get('status', '-')}` bukan DRAFT")
    for kind in ("ticket", "elicit"):
        if not DocValidator(kind, rel, root).run_all():
            errors.append(f"validate_doc.py --kind {kind} FAIL"
                          + (" — catatan elisitasi rusak; kembali ke analyst:elicit" if kind == "elicit" else ""))
    if fm.get("elicitation") != "CLOSED":
        errors.append("elicitation bukan CLOSED — elisitasi dibuka ulang; tuntaskan analyst:elicit dulu")
    elif seal_problem(text_of(path)):
        errors.append(seal_problem(text_of(path)))
    digest = review_digest(path.parent)
    if str(fm.get("review", "")) != f"PASS @{digest}":
        errors.append(f"vonis review terakhir `{fm.get('review', '-')}` bukan `PASS @{digest}` (belum "
                      f"direview, BLOCKED, atau tiket/elisitasi berubah sesudah review → review ulang)")
    if not args.answer.strip():
        errors.append("jawaban user kosong")
    if errors:
        print("APPROVE FAIL: " + "; ".join(errors))
        return 1
    report = review_report(path.parent, fm)
    sealed = content_hash(text_of(path))
    # `approved_seal` (tanpa parser YAML) dibaca penerima backend/frontend; `approved_hash`
    # tetap dipakai analyst sendiri untuk DRIFT dan tiket lama.
    write_fields(path, status="READY", approved=dt.date.today().isoformat(),
                 approved_hash=sealed, approved_seal=ticket_seal(text_of(path)), approval=clean_value(args.answer))
    msg = f"APPROVE PASS: {rel}/{TICKET_FILE} READY @{sealed}"
    if is_git_repo(root) and not args.no_commit:
        # Subjek ini (dan `ref TICKET`) menandai tiket terkunci. Pembacanya: `ticket_source_verdict`
        # di `_common/precondition_lib.py` backend dan frontend — ubah ketiganya bersamaan.
        paths = [f"{rel}/{TICKET_FILE}"] + ([f"{rel}/{REVIEW_FILE}"] if report else [])
        subject = f"docs(ticket): kunci TICKET {rel.split('-', 1)[-1]} READY"
        ok, out = git_commit(root, paths, subject)
        if not ok:
            return _commit_failed(msg, root, paths, out, subject)
        msg += f" · commit {out}"
    print(msg)
    return 0


def _commit_failed(msg: str, root: Path, paths: List[str], out: str, subject: str) -> int:
    """Isi sudah tertulis tetapi commit gagal (hook, gpg, `.gitignore`) → exit 3 beserta sebab git.

    Perintah pemulihan memuat subjek yang sama persis: tiket tanpa `approved_seal` (format lama)
    dinilai penerima dari subjek commit terakhirnya, jadi commit manual bersubjek lain = DRIFT.
    """
    quoted = subject.replace('"', '\\"')
    print(f"{msg} · COMMIT GAGAL: {git_error_line(out)} — isi sudah tertulis; commit manual "
          f"`git -C {root} add -- {' '.join(paths)} && git -C {root} commit -m \"{quoted}\" -- {' '.join(paths)}` "
          f"sesudah sebabnya dibereskan (subjek wajib persis)")
    return 3


def cmd_reopen(root: Path, args: argparse.Namespace) -> int:
    path = _ticket_path(root, args)
    fm = read(path)
    if fm.get("status") != "READY":
        print(f"REOPEN FAIL: TICKET.md berstatus `{fm.get('status', '-')}`, bukan READY")
        return 1
    if not args.reason.strip():
        print("REOPEN FAIL: alasan kosong")
        return 1
    n = int_field(fm, "reopened") + 1
    write_fields(path, status="DRAFT", revision="0", review="-", review_round="0", approved="-",
                 approved_hash="-", approved_seal="-", approval="-", reopened=str(n),
                 reopen_reason=clean_value(args.reason))
    print(f"REOPEN PASS: TICKET.md DRAFT (buka ulang ke-{n})")
    return 0


def cmd_cancel(root: Path, args: argparse.Namespace) -> int:
    rel = normalize_ticketdir(args.ticketdir, root)
    d = root / rel
    if not TICKETDIR_RE.match(rel) or not d.is_dir():
        print(f"CANCEL FAIL: `{rel}` bukan ticketdir sah")
        return 1
    f = d / TICKET_FILE
    if not f.is_file():
        if any(d.iterdir()):
            print(f"CANCEL FAIL: {rel} tanpa {TICKET_FILE} tetapi berisi berkas lain — periksa dan hapus manual")
            return 1
        d.rmdir()
        print(f"CANCEL PASS: {rel} (direktori kosong dihapus)")
        return 0
    try:
        status = read(f).get("status", "")
    except SystemExit:
        status = ""
    if status == "READY" and not args.force:
        print(f"CANCEL FAIL: {rel} READY — tiket mungkin sudah diserahkan ke engineer (`ticket_source`); "
              f"batalkan hanya atas keputusan eksplisit user dengan `--force`")
        return 1
    try:
        write_fields(f, status="CANCELLED", cancel_reason=clean_value(args.reason))
        msg = f"CANCEL PASS: {rel} ({TICKET_FILE})"
    except ValueError as exc:
        text = text_of(f)
        f.write_text(f"---\nstatus: CANCELLED\ncancel_reason: {clean_value(args.reason)}\n---\n\n{text}",
                     encoding="utf-8")
        msg = f"CANCEL PASS: {rel} ({TICKET_FILE}: {exc} — frontmatter baru disisipkan di atas isi lama)"
    if is_git_repo(root) and not args.no_commit:
        # Pembatalan ikut riwayat: tiket READY yang sudah diserahkan tidak berubah status diam-diam.
        paths, subject = [f"{rel}/{TICKET_FILE}"], f"docs(ticket): batalkan TICKET {rel.split('-', 1)[-1]}"
        ok, out = git_commit(root, paths, subject)
        if not ok:
            return _commit_failed(msg, root, paths, out, subject)
        msg += f" · commit {out}"
    print(msg)
    return 0


def cmd_ref(root: Path, args: argparse.Namespace) -> int:
    """`external_ref` di luar sidik konten: boleh diisi pada DRAFT maupun READY tanpa DRIFT.

    Subjek `ref TICKET` dibaca penerima tiket lama (tanpa `approved_seal`) sebagai tanda terkunci, jadi
    `ref` tidak pernah meng-commit isi yang belum disetujui: DRIFT ditolak, DRAFT tidak di-commit.
    """
    path = _ticket_path(root, args)
    fm = read(path)
    rel = str(path.parent.relative_to(root))
    if fm.get("status") not in ("DRAFT", "READY"):
        print(f"REF FAIL: TICKET.md berstatus `{fm.get('status', '-')}`, bukan DRAFT|READY")
        return 1
    state = classify(root, rel)
    if state["state"] in ("DRIFT", "RUSAK"):
        print(f"REF FAIL: {rel} {state['state']} — {state['route']}; `ref` tidak meng-commit isi yang belum disetujui")
        return 1
    if not args.ref.strip():
        print("REF FAIL: --ref kosong")
        return 1
    value = clean_value(args.ref, 120)
    write_fields(path, external_ref=value)
    msg = f"REF PASS: {rel}/{TICKET_FILE} external_ref = {value}"
    if fm.get("status") == "DRAFT":
        print(msg + " · DRAFT: tanpa commit — ikut commit draft berikutnya (analyst:spec Phase 4)")
        return 0
    if is_git_repo(root) and not args.no_commit:
        paths = [f"{rel}/{TICKET_FILE}"]
        subject = f"docs(ticket): ref TICKET {rel.split('-', 1)[-1]}"
        ok, out = git_commit(root, paths, subject)
        if not ok:
            return _commit_failed(msg, root, paths, out, subject)
        msg += f" · commit {out}"
    print(msg)
    return 0


def _compact(obj: Dict[str, Any]) -> str:
    """Teks JSON byte-stabil: ketiga tool MCP menerima `metadata` sebagai string, bukan objek."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def _sync_fail(args: argparse.Namespace, problems: List[str]) -> int:
    if args.json:
        print(json.dumps({"status": "FAIL", "enabled": True, "problems": problems}, indent=2, ensure_ascii=False))
    else:
        print("SYNC-PAYLOAD FAIL: " + "; ".join(problems))
    return 1


def _was_ready(fm: Dict[str, Any]) -> bool:
    """Tiket pernah `READY`: segel approve masih tertulis, atau pernah dibuka ulang (`reopen` mengosongkan segel)."""
    approved = str(fm.get("approved_hash", "-")).strip()
    reopened = str(fm.get("reopened", "0")).strip()
    return approved not in ("", "-") or (reopened.isdigit() and int(reopened) > 0)


def _review_document(root: Path, rel: str, fm: Dict[str, Any], repo: str) -> List[Dict[str, Any]]:
    """`review.md` (blok `## Ticket Review` terakhir) sebagai dokumen `ticket.review` di bawah task (15 A4).

    Hanya bila kepalanya sah terhadap frontmatter (`review_report`): blok basi tidak pernah dicerminkan. Isi diambil
    dari disk, karena analyst boleh berjalan tanpa git.
    """
    path = review_report(root / rel, fm)
    if path is None:
        return []
    content, problem = ns.disk_text(path)
    if content is None:
        return []
    verdict = re.search(r"^- Verdict:\s*(\w+)", content, re.M)
    meta = ns.doc_meta("analyst", repo, f"{rel}/{REVIEW_FILE}", verdict.group(1) if verdict else "",
                       ns.last_commit(root, f"{rel}/{REVIEW_FILE}"))
    return [ns.document("task", REVIEW_FILE, "ticket.review", content, meta)]


def cmd_sync_payload(root: Path, args: argparse.Namespace) -> int:
    """Argumen tool MCP nataflow untuk satu tiket (14 N2, 15 A1–A4, A6) — read-only, tanpa commit.

    Model mengirim `lookup`, `create`, `update`, dan `documents` apa adanya; skrip ini satu-satunya penyusun isinya,
    supaya yang tercermin di nataflow selalu kartu yang disetujui (K1, K5). Identitas task adalah `ticket_key` = path
    ticketdir, bukan slug: `new` membuat ticketdir baru ber-slug sama begitu tiket lama READY/batal (K2). `lookup`
    tidak memuat `repo`, supaya task langkah 14 tetap ditemukan; plugin engineer menurunkan `ticket_key` yang sama
    dari `ticket_source` untuk menautkan workdir-nya ke task ini. Status task hanya dikirim untuk tiket pernah-READY
    yang dibatalkan (`task_status` `cancelled`, A6).
    """
    config, problems = load_sync_config(root)
    if problems:
        return _sync_fail(args, problems)
    if config is None:
        if args.json:
            print(json.dumps({"status": "SKIP", "enabled": False}, indent=2))
        else:
            print(f"SYNC-PAYLOAD SKIP: {ns.CONFIG_FILE} (atau {SYNC_CONFIG} lama) tidak ada — sinkron nataflow "
                  f"tidak aktif di repo ini")
        return 0
    rel = normalize_ticketdir(args.ticketdir, root)
    if not TICKETDIR_RE.match(rel) or not (root / rel).is_dir():
        return _sync_fail(args, [f"`{rel}` bukan direktori {TICKETS_DIR}/<YYMMDDhhmm>-<slug>"])
    state = classify(root, rel)          # non-UTF-8 → RUSAK, bukan traceback
    key = {"source": "analyst", "ticket_key": rel}
    scope = {"workspace_id": config["workspace_id"]} if config["workspace_id"] else {}
    if state["state"] == "DIBATALKAN" and _was_ready(read(root / rel / TICKET_FILE)):
        payload = {"status": "PASS", "enabled": True, "mcp_server": config["mcp_server"], "ticket_key": rel,
                   "lookup": dict(scope, metadata=_compact(key)), "task_status": ns.task_status("cancelled")}
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"SYNC-PAYLOAD PASS: {rel} DIBATALKAN · task cermin menjadi cancelled — argumen tool lewat `--json`")
        return 0
    if state["state"] != "READY":
        return _sync_fail(args, [f"{rel} {state['state']} — hanya tiket READY (atau pernah READY lalu dibatalkan) "
                                 f"yang disinkronkan ({state['route']})"])
    path = root / rel / TICKET_FILE
    text = text_of(path)
    fm, body = split_frontmatter(text)
    title = title_of(path)
    if title == "-":
        return _sync_fail(args, [f"{rel}/{TICKET_FILE} tanpa H1 — judul task diambil dari H1 kartu"])
    reopened = str(fm.get("reopened", "0")).strip() or "0"
    if not reopened.isdigit():
        return _sync_fail(args, [f"field `reopened: {reopened}` bukan bilangan — field ini hanya ditulis "
                                 f"ticket.py; pulihkan nilainya dari riwayat git"])
    repo = ns.repo_identity(root, config)
    meta = dict(key, repo=repo, slug=str(fm.get("slug", "")).strip() or rel.split("-", 1)[-1],
                type=str(fm.get("type", "-")), priority=str(fm.get("priority", "-")),
                approved=str(fm.get("approved", "-")),
                # READY menjamin `approved_seal` tertulis = segel isi sekarang; tiket lama tanpa field itu
                # mendapat nilai yang sama dari isinya.
                approved_seal=ticket_seal(text), reopened=int(reopened))
    ref = str(fm.get("external_ref", "-")).strip()
    if ref and ref != "-":
        meta["external_ref"] = ref
    card = split_parts(body)[0].strip()   # kartu saja: `## Catatan Elisitasi` tetap di disk (K5, 15 A5 tidak diambil)
    create: Dict[str, Any] = {"title": title, "description": card}
    create.update(scope)
    if config["pic_id"]:
        create["pic_id"] = config["pic_id"]
    create["metadata"] = _compact(meta)
    payload = {
        "status": "PASS", "enabled": True, "mcp_server": config["mcp_server"], "ticket_key": rel,
        "lookup": dict(scope, metadata=_compact(key)),
        "create": create,
        "update": {"title": title, "description": card, "metadata": create["metadata"]},
        "documents": _review_document(root, rel, fm, repo),
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"SYNC-PAYLOAD PASS: {rel} · server {config['mcp_server']} · workspace "
              f"{config['workspace_id'] or '-'} · pic {config['pic_id'] or '-'} · {len(payload['documents'])} dokumen "
              f"— argumen tool lewat `--json`")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Siklus hidup ticketdir analyst")
    p.add_argument("--root", default=None, help="root ruang kerja; default root git atau cwd")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("state")
    s.add_argument("--all", action="store_true", help="ikut tampilkan DIBATALKAN dan READY")
    s.add_argument("--ready", action="store_true", help="ikut tampilkan READY")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("new")
    s.add_argument("--slug", required=True)
    s.add_argument("--type", required=True, type=str.upper, choices=TYPES)
    s.add_argument("--requester", required=True, help="nama atau peran peminta")
    s.add_argument("--request", required=True, help="permintaan asli apa adanya, atau `-` untuk stdin")
    s.add_argument("--title", default="", help="judul kerja H1; default dari slug")
    s = sub.add_parser("check")
    s.add_argument("--gate", required=True, choices=("elicit", "spec"))
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--reopen", action="store_true", help="elicit: buka ulang elisitasi CLOSED")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("close")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--no-commit", action="store_true", dest="no_commit")
    s = sub.add_parser("review")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--verdict", required=True, choices=("PASS", "BLOCKED", "DISPATCH_FAILED"))
    s.add_argument("--report", default="", help="blok `## Ticket Review` reviewer: path berkas atau `-` (stdin)")
    s = sub.add_parser("revise")
    s.add_argument("--ticketdir", required=True)
    s = sub.add_parser("approve")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--answer", required=True, help="jawaban user apa adanya")
    s.add_argument("--no-commit", action="store_true", dest="no_commit")
    s = sub.add_parser("reopen")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--reason", required=True)
    s = sub.add_parser("cancel")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--reason", required=True)
    s.add_argument("--force", action="store_true", help="wajib untuk tiket READY (keputusan eksplisit user)")
    s.add_argument("--no-commit", action="store_true", dest="no_commit")
    s = sub.add_parser("ref")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--ref", required=True, help="kunci atau tautan kartu Jira/Trello")
    s.add_argument("--no-commit", action="store_true", dest="no_commit")
    s = sub.add_parser("sync-payload")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--json", action="store_true")
    args = p.parse_args()
    root = (Path(args.root) if args.root else find_root()).resolve()
    handler = {"state": cmd_state, "new": cmd_new, "check": cmd_check, "close": cmd_close, "review": cmd_review,
               "revise": cmd_revise, "approve": cmd_approve, "reopen": cmd_reopen,
               "cancel": cmd_cancel, "ref": cmd_ref, "sync-payload": cmd_sync_payload}[args.cmd]
    sys.exit(handler(root, args))


if __name__ == "__main__":
    main()
