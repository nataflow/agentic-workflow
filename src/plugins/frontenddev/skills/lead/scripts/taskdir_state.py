#!/usr/bin/env python3
"""Taskdir State Scanner — pemulihan sesi `frontenddev:lead` Phase 2.

Membaca tiap `frontenddev/docs/<YYMMDDhhmm>-<slug>/` dan memvonis **satu**
keadaan beserta **satu** rute berikutnya, dari fakta disk dan ledger — bukan
dari ingatan sesi, dan bukan dari model yang membaca frontmatter satu per satu.
Tabel keadaan yang dulu hidup sebagai prosa di Phase 2 kini hidup di sini.

Urutan vonis (yang pertama cocok menang) — sama persis dengan `classify()`:

1. `RUSAK`      — direktori tidak ada, nama di luar pola `<YYMMDDhhmm>-<slug>`, atau
                  artefak rantai tanpa `TASK.md`.
2. `AKAR`       — taskdir kosong → `frontenddev:task`.
3. `DITUTUP`    — `TASK.md` `status: ABANDONED` (`chain.py abandon`).
4. `RUSAK`      — pasangan lane/sections tidak sah atau diubah di luar akar/eskalasi.
5. `AKAR`       — `TASK.md` belum ter-commit → `frontenddev:task` (commit akar).
6. `RUSAK`      — ledger `## Chain` ≠ jadwal sections.
7. `DRIFT`      — hop `[x]` yang kontennya berubah sesudah disetujui → `chain.py reopen`.
8. `GATE`       — hop ledger pertama yang belum `[x]` → skill pemiliknya (beserta mode `plan`).
9. `TERHENTI`   — brief `BLOCKED` tanpa remedi → `chain.py reopen --row BRIEF` → `plan` APPEND.
10. `EKSEKUSI`  — brief `READY` dapat berangkat → `frontenddev:architect`.
11. `PENUTUP`   — seluruh brief tertutup, `REVIEW.md` absen atau basi → `architect` Phase 4.
12. `TEMUAN`    — `REVIEW.md` `BLOCKED` → reopen BRIEF → `plan` APPEND brief perbaikan di
                  taskdir yang sama → review ulang.
13. `LAPORAN`   — `REVIEW.md` `PASS`/`WARNING`, `REPORT.md` absen → `architect` Phase 5.
14. `LAPORAN TERTUNDA` — `REPORT.md` tertulis tetapi belum ter-commit (commit report gagal)
                  → `architect` Phase 5 butir 4.
15. `TUNTAS`    — `REPORT.md` ada dan ter-commit.

Repo non-git tidak divonis per taskdir: skrip keluar `FAIL` karena akar dan
ledger hanya dapat dibuktikan lewat riwayat commit.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    lane_tamper,
    CHAIN_BY_ROW,
    MINOR_LANE,
    brief_closure,
    expected_rows,
    find_repo_root,
    is_git_repo,
    review_is_fresh,
    is_committed,
    lane_sections_problem,
    read_chain,
    read_status,
    task_lane_sections,
    verify_chain_row,
)
from precondition_lib import cli  # noqa: E402

DOCS = "frontenddev/docs"
TASKDIR_NAME = re.compile(r"^\d{10}-[a-z0-9-]+$")
CHAIN_ARTIFACTS = ("FLOW.md", "UI.md", "CONTRACT.md", "REVIEW-PLAN.md", "REVIEW.md", "REPORT.md")


def classify(root: Path, rel: str) -> Dict[str, str]:
    taskdir = root / rel
    task = taskdir / "TASK.md"
    out = {"taskdir": rel, "lane": "-", "state": "", "next": "", "detail": ""}
    if not taskdir.is_dir():
        out.update(state="RUSAK", next="periksa path taskdir; taskdir dibuat lead Phase 5",
                   detail="direktori tidak ada")
        return out
    if not TASKDIR_NAME.match(taskdir.name):
        out.update(state="RUSAK", next="laporkan ke user",
                   detail=f"nama `{taskdir.name}` di luar pola <YYMMDDhhmm>-<slug> (huruf kecil, angka, `-`)")
        return out
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
    if not is_committed(root, f"{rel}/REPORT.md"):
        out.update(state="LAPORAN TERTUNDA", next="frontenddev:architect (Phase 5 butir 4)",
                   detail="REPORT.md tertulis tetapi belum ter-commit")
        return out
    out.update(state="TUNTAS", next="taskdir baru untuk permintaan baru", detail="REPORT.md ter-commit")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Taskdir state scanner")
    parser.add_argument("--taskdir", default="", help="satu taskdir; kosong = seluruh frontenddev/docs")
    parser.add_argument("--all", action="store_true", help="sertakan taskdir TUNTAS")
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = (Path(args.root) if args.root else find_repo_root()).resolve()
    if not is_git_repo(root):
        error = f"`{root}` bukan repo git — akar dan ledger tidak dapat dibuktikan"
        print(json.dumps({"status": "FAIL", "error": error}, indent=2) if args.json
              else f"TASKDIR STATE: [FAIL] {error}")
        sys.exit(1)
    if args.taskdir:
        rels = [args.taskdir.strip().strip("/").replace("./", "")]
    else:
        base = root / DOCS
        # Nama di luar pola tetap dilaporkan (RUSAK) bila berisi berkas, bukan diabaikan diam-diam.
        rels = [f"{DOCS}/{p.name}" for p in sorted(base.iterdir())
                if p.is_dir() and (TASKDIR_NAME.match(p.name) or any(p.glob("*.md")))] if base.is_dir() else []
    rows = [classify(root, r) for r in rels]
    if not args.all and not args.taskdir:
        rows = [r for r in rows if r["state"] not in ("TUNTAS", "DITUTUP")]
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
    sys.exit(cli(main))
