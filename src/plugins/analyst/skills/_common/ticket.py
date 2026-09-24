#!/usr/bin/env python3
"""CLI siklus hidup ticketdir plugin `analyst`.

Tiap ticketdir memuat **satu** berkas, `TICKET.md`: kartu tiket di atas, `## Catatan Elisitasi`
sebagai H2 terakhir. Frontmatter `elicitation` (OPEN/CLOSED) milik `analyst:elicit`; `status`
(DRAFT/READY/CANCELLED) milik skrip ini kecuali DRAFT awal.

Satu-satunya jalan mutasi status yang punya konsekuensi di luar penulisnya:

- `state`   — pindai `analyst/tickets/*/`, vonis keadaan dan rute tiap ticketdir.
- `new`     — alokasikan `analyst/tickets/<YYMMDDhhmm>-<slug>/` (menolak slug kembar terbuka).
- `check`   — prasyarat gate `elicit` / `spec` atas satu ticketdir.
- `review`  — catat vonis `ticket-reviewer` beserta sidik konten yang dinilainya.
- `revise`  — buka putaran revisi draft atas permintaan user (plafon 3 per siklus persetujuan).
- `approve` — materai `TICKET.md` `READY` sesudah jawaban eksplisit user; commit bila repo git.
- `reopen`  — buka ulang tiket `READY` menjadi `DRAFT` untuk perubahan permintaan.
- `cancel`  — tutup ticketdir atas keputusan user.

`approve` menuntut validator `PASS`, `elicitation: CLOSED`, **dan** vonis review `PASS` atas sidik
`<kartu>/<catatan elisitasi>` yang sama persis dengan sekarang: draft yang disunting sesudah direview,
atau elisitasi yang dibuka dan berubah sesudahnya, tidak dapat disetujui.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyst_lib import (  # noqa: E402
    ELICIT_H2,
    SLUG_RE,
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
    is_git_repo,
    normalize_ticketdir,
    report_json,
    set_frontmatter_field,
    split_frontmatter,
    split_parts,
)
from validate_doc import DocValidator  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REVISION_CAP = 3
REVIEW_CAP = 2


def read(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    fm, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    return fm


def write_fields(path: Path, **fields: str) -> None:
    text = path.read_text(encoding="utf-8")
    for key, value in fields.items():
        text = set_frontmatter_field(text, key, value)
    path.write_text(text, encoding="utf-8")


def review_digest(ticketdir: Path) -> str:
    """Sidik gabungan yang dinilai reviewer: `<sidik kartu>/<sidik catatan elisitasi>`."""
    f = ticketdir / TICKET_FILE
    if not f.is_file():
        return "-/-"
    text = f.read_text(encoding="utf-8")
    return f"{content_hash(text, 'card')}/{content_hash(text, 'elicit')}"


def has_card(path: Path) -> bool:
    """Kartu sudah ditulis `spec`: ada H2 lain di atas `## Catatan Elisitasi`."""
    _, body = split_frontmatter(path.read_text(encoding="utf-8"))
    card, _ = split_parts(body)
    return any(l.startswith("## ") for l in card.splitlines())


def title_of(path: Path) -> str:
    if not path.is_file():
        return "-"
    _, body = split_frontmatter(path.read_text(encoding="utf-8"))
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "-"


def classify(root: Path, rel: str) -> Dict[str, str]:
    """Keadaan satu ticketdir → rute berikutnya."""
    d = root / rel
    ticket = d / TICKET_FILE
    t = read(ticket)
    es, ts = t.get("elicitation", ""), t.get("status", "")
    row = {"ticketdir": rel, "type": t.get("type", "-"), "title": title_of(ticket)}
    if ts == "CANCELLED":
        row.update(state="DIBATALKAN", route="-")
    elif not ticket.is_file():
        row.update(state="KOSONG", route="analyst:intake → analyst:elicit menulis TICKET.md ke ticketdir ini")
    elif es not in ("OPEN", "CLOSED") or ts not in ("DRAFT", "READY"):
        row.update(state="RUSAK", route=f"status tidak sah (elicitation {es or '-'}, status {ts or '-'})")
    elif not split_parts(split_frontmatter(ticket.read_text(encoding="utf-8"))[1])[1]:
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
    elif str(t.get("approved_hash", "")) != content_hash(ticket.read_text(encoding="utf-8")):
        row.update(state="DRIFT", route="TICKET READY disunting sesudah disetujui — analyst:spec REVISE "
                                        "(reopen) atau pulihkan isinya")
    else:
        row.update(state="READY", route="selesai — serahkan ke backenddev:tech-lead / frontenddev:lead")
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
    if not SLUG_RE.match(args.slug) or len(args.slug) > 40:
        print(f"NEW FAIL: slug `{args.slug}` bukan kebab-case ≤40 karakter")
        return 1
    if args.type not in TYPES:
        print(f"NEW FAIL: type `{args.type}` bukan {'|'.join(TYPES)}")
        return 1
    for rel in ticketdirs(root):
        r = classify(root, rel)
        if rel.split("-", 1)[-1] == args.slug and r["state"] not in ("DIBATALKAN", "READY"):
            print(f"NEW FAIL: slug `{args.slug}` masih terbuka di {rel} ({r['state']}) — lanjutkan itu, "
                  f"atau pilih slug lain")
            return 1
    stamp = dt.datetime.now().strftime("%y%m%d%H%M")
    rel = f"{TICKETS_DIR}/{stamp}-{args.slug}"
    if (root / rel).exists():
        print(f"NEW FAIL: {rel} sudah ada (slug sama dalam menit yang sama) — tunggu satu menit atau pilih slug lain")
        return 1
    (root / rel).mkdir(parents=True)
    print(f"NEW PASS: {rel} · git={'ya' if is_git_repo(root) else 'tidak'}")
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
    resolved: Dict[str, str] = {"git": "ya" if is_git_repo(root) else "tidak"}
    if ok:
        state = classify(root, rel)
        resolved["keadaan"] = state["state"]
        t = read(d / TICKET_FILE)
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
            resolved["type"] = str(t.get("type", "-"))
            if state["state"] == "DRAFT":
                resolved["revision"] = str(t.get("revision", "0"))
                resolved["review_round"] = str(t.get("review_round", "0"))
                fresh = str(t.get("review", "")) == f"PASS @{review_digest(d)}"
                resolved["review_segar"] = "ya" if fresh else "tidak"
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
    rnd = int(str(fm.get("review_round", "0")) or 0)
    if args.verdict != "DISPATCH_FAILED" and rnd >= REVIEW_CAP:
        print(f"REVIEW FAIL: plafon {REVIEW_CAP} ronde per revisi habis — sajikan temuan tersisa ke user")
        return 1
    if args.verdict == "DISPATCH_FAILED":
        print("REVIEW PASS: dispatch gagal dicatat, tidak dihitung ronde")
        return 0
    digest = review_digest(path.parent)
    write_fields(path, review=f"{args.verdict} @{digest}", review_round=str(rnd + 1))
    print(f"REVIEW PASS: ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest}")
    return 0


def cmd_revise(root: Path, args: argparse.Namespace) -> int:
    path = _ticket_path(root, args)
    fm = read(path)
    if fm.get("status") != "DRAFT":
        print(f"REVISE FAIL: TICKET.md berstatus `{fm.get('status', '-')}`; READY dibuka lewat `reopen`")
        return 1
    # Plafon berlaku per basis fakta: elisitasi yang dibuka ulang dan berubah memulai siklus baru,
    # karena draft sesudahnya disusun dari fakta yang berbeda, bukan diredaksi ulang.
    base = content_hash(path.read_text(encoding="utf-8"), "elicit")
    rev = int(str(fm.get("revision", "0")) or 0) if str(fm.get("revision_base", base)) == base else 0
    if rev >= REVISION_CAP:
        print(f"REVISE FAIL: plafon {REVISION_CAP} revisi habis — lingkup belum jelas; kembali ke analyst:elicit "
              f"(`check --gate elicit --reopen`) atau `cancel` atas keputusan user")
        return 1
    write_fields(path, revision=str(rev + 1), revision_base=base, review="-", review_round="0")
    print(f"REVISE PASS: revisi {rev + 1}/{REVISION_CAP}")
    return 0


def cmd_approve(root: Path, args: argparse.Namespace) -> int:
    path = _ticket_path(root, args)
    fm = read(path)
    rel = str(path.parent.relative_to(root))
    errors = []
    if fm.get("status") != "DRAFT":
        errors.append(f"status `{fm.get('status', '-')}` bukan DRAFT")
    v = DocValidator("ticket", rel, root)
    if not v.run_all():
        errors.append("validate_doc.py --kind ticket FAIL")
    if fm.get("elicitation") != "CLOSED":
        errors.append("elicitation bukan CLOSED — elisitasi dibuka ulang; tuntaskan analyst:elicit dulu")
    digest = review_digest(path.parent)
    if str(fm.get("review", "")) != f"PASS @{digest}":
        errors.append(f"vonis review terakhir `{fm.get('review', '-')}` bukan `PASS @{digest}` (belum "
                      f"direview, BLOCKED, atau tiket/elisitasi berubah sesudah review → review ulang)")
    if not args.answer.strip():
        errors.append("jawaban user kosong")
    if errors:
        print("APPROVE FAIL: " + "; ".join(errors))
        return 1
    sealed = content_hash(path.read_text(encoding="utf-8"))
    write_fields(path, status="READY", approved=dt.date.today().isoformat(),
                 approved_hash=sealed, approval=clean_value(args.answer))
    msg = f"APPROVE PASS: {rel}/{TICKET_FILE} READY @{sealed}"
    if is_git_repo(root) and not args.no_commit:
        ok, out = git_commit(root, [f"{rel}/{TICKET_FILE}"],
                             f"docs(ticket): kunci TICKET {rel.split('-', 1)[-1]} READY")
        msg += f" · commit {out}" if ok else f" · COMMIT GAGAL: {out.splitlines()[-1] if out else '-'}"
    print(msg)
    return 0


def cmd_reopen(root: Path, args: argparse.Namespace) -> int:
    path = _ticket_path(root, args)
    fm = read(path)
    if fm.get("status") != "READY":
        print(f"REOPEN FAIL: TICKET.md berstatus `{fm.get('status', '-')}`, bukan READY")
        return 1
    if not args.reason.strip():
        print("REOPEN FAIL: alasan kosong")
        return 1
    n = int(str(fm.get("reopened", "0")) or 0) + 1
    write_fields(path, status="DRAFT", revision="0", review="-", review_round="0", approved="-",
                 approved_hash="-", approval="-", reopened=str(n), reopen_reason=clean_value(args.reason))
    print(f"REOPEN PASS: TICKET.md DRAFT (buka ulang ke-{n})")
    return 0


def cmd_cancel(root: Path, args: argparse.Namespace) -> int:
    rel = normalize_ticketdir(args.ticketdir, root)
    d = root / rel
    if not TICKETDIR_RE.match(rel) or not d.is_dir():
        print(f"CANCEL FAIL: `{rel}` bukan ticketdir sah")
        return 1
    if not (d / TICKET_FILE).is_file():
        print(f"CANCEL PASS: {rel} (direktori kosong — hapus saja)")
        return 0
    write_fields(d / TICKET_FILE, status="CANCELLED", cancel_reason=clean_value(args.reason))
    print(f"CANCEL PASS: {rel} ({TICKET_FILE})")
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
    s.add_argument("--type", required=True, choices=TYPES)
    s = sub.add_parser("check")
    s.add_argument("--gate", required=True, choices=("elicit", "spec"))
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--reopen", action="store_true", help="elicit: buka ulang elisitasi CLOSED")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("review")
    s.add_argument("--ticketdir", required=True)
    s.add_argument("--verdict", required=True, choices=("PASS", "BLOCKED", "DISPATCH_FAILED"))
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
    args = p.parse_args()
    root = (Path(args.root) if args.root else find_root()).resolve()
    handler = {"state": cmd_state, "new": cmd_new, "check": cmd_check, "review": cmd_review,
               "revise": cmd_revise, "approve": cmd_approve, "reopen": cmd_reopen,
               "cancel": cmd_cancel}[args.cmd]
    sys.exit(handler(root, args))


if __name__ == "__main__":
    main()
