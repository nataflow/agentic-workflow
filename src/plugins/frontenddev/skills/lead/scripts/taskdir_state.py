#!/usr/bin/env python3
"""Taskdir State Scanner — pemulihan sesi `frontenddev:lead` Phase 2.

Membaca tiap `frontenddev/docs/<YYMMDDhhmm>-<slug>/` dan memvonis **satu**
keadaan beserta **satu** rute berikutnya, dari fakta disk dan ledger — bukan
dari ingatan sesi, dan bukan dari model yang membaca frontmatter satu per satu.
Tabel keadaan yang dulu hidup sebagai prosa di Phase 2 kini hidup di sini.

Urutan vonis (yang pertama cocok menang):

1. `RUSAK`      — artefak rantai tanpa `TASK.md`, atau pasangan lane/sections tidak sah.
2. `AKAR`       — taskdir kosong, atau `TASK.md` belum ter-commit → `frontenddev:task`.
3. `DRIFT`      — hop `[x]` yang kontennya berubah sesudah disetujui → `chain.py reopen`.
4. `GATE`       — hop ledger pertama yang belum `[x]` → skill pemiliknya (beserta mode `plan`).
5. `EKSEKUSI`   — brief `READY` dapat berangkat → `frontenddev:architect`.
6. `TERHENTI`   — brief `BLOCKED` tanpa remedi → `chain.py reopen --row BRIEF` → `plan` APPEND.
7. `PENUTUP`    — seluruh brief tertutup, `REVIEW.md` absen → `frontenddev:architect` Phase 4.
8. `TEMUAN`     — `REVIEW.md` ber-verdict `BLOCKED` → kerja baru lewat lead (`finding_source`).
   Perbaikannya di taskdir yang sama: reopen BRIEF → `plan` APPEND → review ulang.
9. `LAPORAN`    — `REVIEW.md` `PASS`/`WARNING`, `REPORT.md` absen → `frontenddev:report`.
10. `TUNTAS`    — `REPORT.md` ada.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    lane_tamper,
    CHAIN_BY_ROW,
    MINOR_LANE,
    brief_closure,
    expected_rows,
    find_repo_root,
    review_is_fresh,
    is_committed,
    lane_sections_problem,
    read_chain,
    read_status,
    task_lane_sections,
    verify_chain_row,
)

DOCS = "frontenddev/docs"
TASKDIR_NAME = re.compile(r"^\d{10}-[a-z0-9-]+$")
CHAIN_ARTIFACTS = ("FLOW.md", "UI.md", "CONTRACT.md", "REVIEW-PLAN.md", "REVIEW.md", "REPORT.md")


def followups(root: Path) -> Dict[str, str]:
    """`{path finding_source: taskdir penerus}` dari frontmatter seluruh `TASK.md`."""
    out: Dict[str, str] = {}
    base = root / DOCS
    if not base.is_dir():
        return out
    for task in sorted(base.glob("*/TASK.md")):
        source = read_status(task, "finding_source").strip().strip("./")
        if source:
            out[source] = f"{DOCS}/{task.parent.name}"
    return out


def classify(root: Path, rel: str, successors: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    taskdir = root / rel
    task = taskdir / "TASK.md"
    out = {"taskdir": rel, "lane": "-", "state": "", "next": "", "detail": ""}
    artifacts = [a for a in CHAIN_ARTIFACTS if (taskdir / a).is_file()] + \
                [p.name for p in taskdir.glob("brief-*.md")]
    if not task.is_file():
        if artifacts:
            out.update(state="RUSAK", next="laporkan ke user",
                       detail="artefak rantai tanpa TASK.md — taskdir warisan tidak dilayani sejak v0.4.0")
        else:
            out.update(state="AKAR", next="frontenddev:task (lead Phase 7), atau hapus direktori kosong bila user batal",
                       detail="taskdir kosong")
        return out
    if read_status(task) == "ABANDONED":
        out.update(state="DITUTUP", next="-", detail="ditutup atas keputusan user (`chain.py abandon`)")
        return out
    lane, sections = task_lane_sections(task)
    out["lane"] = lane or "-"
    problem = lane_sections_problem(lane, sections) or lane_tamper(root, rel)
    if problem:
        out.update(state="RUSAK", next="laporkan ke user", detail=problem)
        return out
    if not is_committed(root, f"{rel}/TASK.md"):
        out.update(state="AKAR", next="frontenddev:task (commit akar)", detail="TASK.md belum ter-commit")
        return out
    entries = read_chain(task.read_text(encoding="utf-8"))
    if [e["row"] for e in entries] != expected_rows(sections):
        out.update(state="RUSAK", next="laporkan ke user",
                   detail=f"ledger {[e['row'] for e in entries]} ≠ jadwal sections {expected_rows(sections)}")
        return out
    for entry in entries:
        if entry["mark"] == "x":
            drift = verify_chain_row(root, rel, entry)
            if drift:
                out.update(state="DRIFT", next=f"chain.py reopen --row {entry['row']}", detail=drift)
                return out
            continue
        row = entry["row"]
        skill = CHAIN_BY_ROW[row][1]
        if row == "BRIEF":
            briefs = list(taskdir.glob("brief-*.md"))
            if entry["mark"] == "~":
                mode = "APPEND"
            elif briefs:
                mode = "REVISE atau approval breakdown tertunda"
            else:
                mode = "MINOR" if lane == MINOR_LANE else "CONTRACT"
            out.update(state="GATE", next=f"{skill} (mode {mode})",
                       detail=f"hop BRIEF `[{entry['mark']}]`, {len(briefs)} brief")
            return out
        doc = CHAIN_BY_ROW[row][2]
        status = read_status(taskdir / doc) if (taskdir / doc).is_file() else "absen"
        out.update(state="GATE", next=skill,
                   detail=f"hop {row} `[{entry['mark']}]`, {doc} {status}"
                          + (" — minta keputusan user atas draft" if status == "DRAFT" else ""))
        return out
    closure = brief_closure(taskdir)
    open_blocked = [nn for nn, (st, done) in closure.items() if st == "BLOCKED" and not done
                    and not any(read_status(p, "remedies") == nn for p in taskdir.glob("brief-*.md"))]
    if open_blocked:
        out.update(state="TERHENTI", next="chain.py reopen --row BRIEF → frontenddev:plan (mode APPEND)",
                   detail=f"brief-{open_blocked[0]} BLOCKED tanpa remedi")
        return out
    if any(st == "READY" for st, _ in closure.values()):
        out.update(state="EKSEKUSI", next="frontenddev:architect",
                   detail=f"{sum(1 for st, _ in closure.values() if st == 'READY')} brief READY")
        return out
    review = taskdir / "REVIEW.md"
    if not review.is_file() or not review_is_fresh(root, rel):
        out.update(state="PENUTUP", next="frontenddev:architect (Phase 4)", detail="seluruh brief tertutup")
        return out
    verdict = read_status(review, "verdict")
    if verdict == "BLOCKED":
        out.update(state="TEMUAN", next="chain.py reopen --row BRIEF → frontenddev:plan (mode APPEND, brief perbaikan)",
                   detail=f"{rel}/REVIEW.md BLOCKED — diperbaiki di taskdir yang sama, lalu review ulang")
        return out
    if not (taskdir / "REPORT.md").is_file():
        out.update(state="LAPORAN", next="frontenddev:architect (Phase 5)", detail=f"REVIEW.md {verdict}")
        return out
    out.update(state="TUNTAS", next="taskdir baru untuk permintaan baru", detail="REPORT.md ada")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Taskdir state scanner")
    parser.add_argument("--taskdir", default="", help="satu taskdir; kosong = seluruh frontenddev/docs")
    parser.add_argument("--all", action="store_true", help="sertakan taskdir TUNTAS")
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = (Path(args.root) if args.root else find_repo_root()).resolve()
    if args.taskdir:
        rels = [args.taskdir.strip().strip("/").replace("./", "")]
    else:
        base = root / DOCS
        rels = [f"{DOCS}/{p.name}" for p in sorted(base.iterdir())
                if p.is_dir() and TASKDIR_NAME.match(p.name)] if base.is_dir() else []
    successors = followups(root)
    rows = [classify(root, r, successors) for r in rels]
    if not args.all and not args.taskdir:
        rows = [r for r in rows if r["state"] not in ("TUNTAS", "DILANJUTKAN", "DITUTUP")]
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    if not rows:
        print("TASKDIR STATE: nol taskdir terbuka — aman membuat taskdir baru")
        return
    print(f"TASKDIR STATE: {len(rows)} taskdir terbuka")
    for r in rows:
        print(f"- {r['taskdir']} [{r['lane']}] {r['state']} → {r['next']} ({r['detail']})")


if __name__ == "__main__":
    main()
