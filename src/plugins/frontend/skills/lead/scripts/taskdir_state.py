#!/usr/bin/env python3
"""Taskdir State Scanner — pemulihan sesi `frontend:lead` Phase 2.

Membaca tiap `frontenddev/docs/<YYMMDDhhmm>-<slug>/` dan memvonis **satu**
keadaan beserta **satu** rute berikutnya, dari fakta disk dan ledger — bukan
dari ingatan sesi, dan bukan dari model yang membaca frontmatter satu per satu.
Tabel keadaan yang dulu hidup sebagai prosa di Phase 2 kini hidup di sini.

Urutan vonis (yang pertama cocok menang) — sama persis dengan `classify()`:

1. `RUSAK`      — path di luar `frontenddev/docs/<YYMMDDhhmm>-<slug>`, direktori tidak ada,
                  nama di luar pola, atau artefak rantai tanpa `TASK.md`.
2. `AKAR`       — taskdir kosong → `frontend:task`.
3. `DITUTUP`    — `TASK.md` `status: ABANDONED` (`chain.py abandon`).
4. `RUSAK`      — `status` selain `ACTIVE`/`ABANDONED` (12 J50), atau `## Riwayat Rantai` rusak.
5. Akar belum terkunci (`base_commit` atau kejadian `akar` absen, Langkah 24):
   - `TUNTAS`   — ber-`REPORT.md`: taskdir warisan era git yang sudah selesai;
   - `RUSAK`    — ber-centang ledger atau ber-artefak rantai: taskdir era git yang belum tuntas,
                  hanya dapat ditutup (`chain.py abandon`);
   - `AKAR`     — selain itu: `TASK.md` tertulis tetapi `chain.py root` belum jalan → `frontend:task`.
6. `RUSAK`      — `base_commit` tidak sah (rebase/reset sesudah akar dikunci), atau pasangan lane/sections
                  tidak sah atau diubah di luar akar/eskalasi.
7. `DRIFT`      — sidik akar ≠ kejadian akar/eskalasi/amandemen terakhir: `TASK.md` disunting di luar
                  `chain.py amend` → amandemen akar lewat lead, atau kembalikan suntingan.
7a. `TUNTAS`    — `REVIEW.md` `PASS`/`WARNING`, ledger tercentang penuh, nol brief `READY`, `REPORT.md` ada,
                  dan review segar (laporan lolos validator) atau `head`-nya tidak lagi di riwayat `HEAD`. Dinilai
                  **sebelum** ledger dan penutupan brief (12 J44): rantai tuntas yang di-squash-merge
                  kehilangan commit unitnya, bukan keabsahannya.
8. `RUSAK`      — ledger `## Chain` ≠ jadwal sections.
9. `DRIFT`      — hop `[x]` yang kontennya berubah sesudah disetujui, atau materainya tidak sah
                  → `chain.py reopen`.
10. `GATE`      — hop ledger pertama yang belum `[x]` → skill pemiliknya (beserta mode `plan`).
10a. `TERPUTUS` — brief `DONE` tanpa commit unit pembawa kode (25 R6) → `frontend:architect` fase `TERPUTUS`
                  (matriks bukti disk, tanpa dispatch). Dinilai sebelum `TERHENTI`: unit itu bukan prasyarat yang
                  macet (`DAG`) dan bukan tanda seluruh brief tertutup (`PENUTUP`).
11. `TERHENTI`  — brief `BLOCKED` tanpa remedi, atau brief `READY` yang tak satu pun dapat berangkat
                  (`DAG`, 12 J58) → `chain.py reopen --row BRIEF` → `plan` APPEND.
12. `EKSEKUSI`  — brief `READY` dapat berangkat (`runnable_briefs`) → `frontend:architect`.
13. `PENUTUP`   — seluruh brief tertutup, `REVIEW.md` absen, basi, atau ber-verdict di luar
                  `PASS`/`WARNING`/`BLOCKED` (12 J53) → `architect` Phase 4.
14. `TEMUAN`    — `REVIEW.md` `BLOCKED` → reopen BRIEF → `plan` APPEND brief perbaikan di
                  taskdir yang sama → review ulang.
15. `LAPORAN`   — `REVIEW.md` `PASS`/`WARNING`, `REPORT.md` absen → `architect` Phase 5.
16. `LAPORAN TERTUNDA` — `REPORT.md` tertulis tetapi tidak lolos `validate_report.py` (penulisan
                  terputus) → `architect` Phase 5 butir 4.
17. `TUNTAS`    — `REPORT.md` ada dan lolos `validate_report.py`.

`RUSAK` membawa jalan keluar per jenis di `next` (12 J58): akar ber-`TASK.md` → `chain.py abandon`
lalu taskdir baru (atau user memulihkan `TASK.md`); nama di luar pola atau tanpa `TASK.md` — `chain.py`
menolak keduanya — → user memindahkan direktori keluar `frontenddev/docs/` atau menghapusnya.

Repo non-git tidak divonis per taskdir: skrip keluar `FAIL` karena `base_commit` dan commit kode
rantai hanya dapat dibuktikan lewat git. Repo yang masih men-track `frontenddev/docs/` juga keluar
`FAIL` dengan rute `MIGRASI` (24 G2): dokumen taskdir kini diabaikan git dan dicerminkan ke nataflow.
Skrip ini read-only; penanda ignore ditulis prasyarat `frontend:task`.

Zero external dependencies (Python Standard Library only). Satu impor
intra-plugin: `skills/_common/precondition_lib.py`.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
import docs_git  # noqa: E402
from precondition_lib import (  # noqa: E402
    lane_tamper,
    CHAIN_BY_ROW,
    MINOR_LANE,
    TASKDIR_PATTERN,
    brief_closure,
    expected_rows,
    find_repo_root,
    git,
    git_ok,
    is_git_repo,
    last_root_seal,
    normalize_taskdir,
    review_is_fresh,
    root_sidik,
    runnable_briefs,
    lane_sections_problem,
    read_chain,
    read_status,
    task_base_commit,
    task_history,
    task_lane_sections,
    verify_chain_row,
)
from precondition_lib import cli  # noqa: E402

DOCS = "frontenddev/docs"
TASKDIR_NAME = re.compile(r"^\d{10}-[a-z0-9-]+$")
CHAIN_ARTIFACTS = ("FLOW.md", "UI.md", "CONTRACT.md", "REVIEW-PLAN.md", "REVIEW.md", "REPORT.md")
REVIEW_VERDICTS = ("PASS", "WARNING", "BLOCKED")
VALIDATE_REPORT = Path(__file__).resolve().parents[2] / "report" / "scripts" / "validate_report.py"
# Jalan keluar RUSAK (12 J58) — keputusan user lewat `AskUserQuestion`, tidak pernah tambalan tangan.
ROOTED_EXIT = ("laporkan ke user; `AskUserQuestion`: `chain.py abandon` lalu rumuskan ulang di taskdir baru, "
               "atau user sendiri memulihkan `TASK.md`")
UNROOTED_EXIT = ("laporkan ke user; bukan artefak rantai yang dapat dilanjutkan (`chain.py` menolaknya) — "
                 "user memindahkan direktori itu keluar `frontenddev/docs/` atau menghapusnya")
AMEND_EXIT = ("`frontend:lead`: amandemen akar atas persetujuan user (`validate_task.py --amend` lalu "
              "`chain.py amend`), atau kembalikan suntingannya")


def finished(root: Path, rel: str, entries) -> bool:
    """Rantai tuntas dinilai dari disk, bukan dari penutupan brief (12 J44, 24 K9).

    `REVIEW.md` `PASS`/`WARNING`, seluruh hop `[x]`, nol brief `READY`, dan `REPORT.md` ada; lalu salah satu: review
    segar dan `REPORT.md` lolos validator, atau `head` review tidak lagi leluhur `HEAD` karena riwayat ditulis ulang
    (squash-merge). Unit baru sesudah review normal membuat review basi tanpa menulis ulang riwayat, jadi rantai
    yang dilanjutkan tetap divonis lewat ledger.
    """
    taskdir = root / rel
    if not (taskdir / "REPORT.md").is_file() or read_status(taskdir / "REVIEW.md", "verdict") not in ("PASS", "WARNING"):
        return False
    if any(e["mark"] != "x" for e in entries) or any(read_status(b) == "READY" for b in taskdir.glob("brief-*.md")):
        return False
    if review_is_fresh(root, rel):
        return report_valid(root, rel)
    # Riwayat ditulis ulang: commit rantai tidak lagi ada, jadi `validate_report.py` (berkas rantai) tidak dapat
    # dinilai ulang — laporan itu sudah lolos sebelum squash.
    return review_head_rewritten(root, rel)


def review_head_rewritten(root: Path, rel: str) -> bool:
    """`head:` `REVIEW.md` berbentuk sha tetapi tidak lagi leluhur `HEAD` (riwayat ditulis ulang)."""
    head = read_status(root / rel / "REVIEW.md", "head")
    if not re.fullmatch(r"[0-9a-f]{7,40}", head):
        return False
    full = git(root, "rev-parse", "--verify", "-q", f"{head}^{{commit}}").strip()
    return not full or not git_ok(root, "merge-base", "--is-ancestor", full, "HEAD")[0]


def report_valid(root: Path, rel: str) -> bool:
    """`REPORT.md` lolos `validate_report.py` — pengganti "ter-commit" sejak dokumen taskdir tidak di-commit."""
    proc = subprocess.run([sys.executable, str(VALIDATE_REPORT), "--taskdir", rel, "--root", str(root)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc.returncode == 0


def classify(root: Path, rel: str) -> Dict[str, str]:
    taskdir = root / rel
    task = taskdir / "TASK.md"
    out = {"taskdir": rel, "lane": "-", "state": "", "next": "", "detail": ""}
    if not TASKDIR_PATTERN.match(rel):
        out.update(state="RUSAK", next=UNROOTED_EXIT,
                   detail=f"path `{rel}` di luar {DOCS}/<YYMMDDhhmm>-<slug> (huruf kecil, angka, `-`)")
        return out
    if not taskdir.is_dir():
        out.update(state="RUSAK", next="periksa path taskdir; taskdir dibuat lead Phase 5",
                   detail="direktori tidak ada")
        return out
    if not TASKDIR_NAME.match(taskdir.name):
        out.update(state="RUSAK", next=UNROOTED_EXIT,
                   detail=f"nama `{taskdir.name}` di luar pola <YYMMDDhhmm>-<slug> (huruf kecil, angka, `-`)")
        return out
    artifacts = [a for a in CHAIN_ARTIFACTS if (taskdir / a).is_file()] + \
                [p.name for p in taskdir.glob("brief-*.md")]
    if not task.is_file():
        if artifacts:
            out.update(state="RUSAK", next=UNROOTED_EXIT,
                       detail="artefak rantai tanpa TASK.md — taskdir warisan tidak dilayani sejak v0.4.0")
        else:
            out.update(state="AKAR", next="frontend:task (lead Phase 7), atau hapus direktori kosong bila user batal",
                       detail="taskdir kosong")
        return out
    status = read_status(task)
    if status == "ABANDONED":
        out.update(state="DITUTUP", next="-", detail="ditutup atas keputusan user (`chain.py abandon`)")
        return out
    if status != "ACTIVE":
        out.update(state="RUSAK", next=ROOTED_EXIT,
                   detail=f"`TASK.md` berstatus `{status or '(kosong)'}` — hanya `ACTIVE` (berjalan) atau "
                          "`ABANDONED` (ditutup) yang sah")
        return out
    events, problem = task_history(root, rel)
    if problem:
        out.update(state="RUSAK", next=ROOTED_EXIT, detail=f"`## Riwayat Rantai` rusak: {problem}")
        return out
    lane, sections = task_lane_sections(task)
    out["lane"] = lane or "-"
    text = task.read_text(encoding="utf-8")
    entries = read_chain(text)
    base, problem = task_base_commit(root, rel)
    if not base or not events or events[0]["kind"] != "akar":
        if (taskdir / "REPORT.md").is_file():
            out.update(state="TUNTAS", next="taskdir baru untuk permintaan baru",
                       detail="REPORT.md ada — taskdir warisan era git (sebelum Langkah 24)")
        elif any(e["mark"] != " " for e in entries) or [a for a in artifacts if a != "REPORT.md"]:
            out.update(state="RUSAK", next=ROOTED_EXIT,
                       detail="taskdir era git yang belum tuntas (tanpa `base_commit`/Riwayat) — tidak dapat "
                              "dilanjutkan sesudah dokumen taskdir lepas dari git")
        else:
            out.update(state="AKAR", next="frontend:task (kunci akar: `chain.py root`)",
                       detail="TASK.md tertulis, akar belum terkunci")
        return out
    if problem:
        out.update(state="RUSAK", next=ROOTED_EXIT, detail=f"`base_commit`: {problem}")
        return out
    problem = lane_sections_problem(lane, sections) or lane_tamper(root, rel)
    if problem:
        out.update(state="RUSAK", next=ROOTED_EXIT, detail=problem)
        return out
    if root_sidik(text)[:12] != last_root_seal(events):
        out.update(state="DRIFT", next=AMEND_EXIT,
                   detail="`TASK.md` disunting di luar `chain.py amend`/`escalate`")
        return out
    if finished(root, rel, entries):
        out.update(state="TUNTAS", next="taskdir baru untuk permintaan baru", detail="REPORT.md terbit")
        return out
    if [e["row"] for e in entries] != expected_rows(sections):
        out.update(state="RUSAK", next=ROOTED_EXIT,
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
    closure = brief_closure(taskdir, root)
    unlanded = sorted(nn for nn, (st, done) in closure.items() if st == "DONE" and not done)
    if unlanded:
        out.update(state="TERPUTUS", next=f"frontend:architect (fase TERPUTUS: matriks bukti disk atas brief-{unlanded[0]})",
                   detail=f"brief-{', '.join(unlanded)} DONE di disk tanpa commit unit pembawa kode — sesi terputus di "
                          "antara status dan commit, `DONE` diketik tangan, atau commit unit di-reset")
        return out
    open_blocked = [nn for nn, (st, done) in closure.items() if st == "BLOCKED" and not done
                    and not any(read_status(p, "remedies") == nn for p in taskdir.glob("brief-*.md"))]
    if open_blocked:
        out.update(state="TERHENTI", next="chain.py reopen --row BRIEF → frontend:plan (mode APPEND)",
                   detail=f"brief-{open_blocked[0]} BLOCKED tanpa remedi")
        return out
    ready = sum(1 for st, _ in closure.values() if st == "READY")
    if ready:
        if not runnable_briefs(taskdir, root):
            out.update(state="TERHENTI", next="chain.py reopen --row BRIEF → frontend:plan (mode APPEND, perbaiki depends_on)",
                       detail=f"DAG: {ready} brief READY, tak satu pun dapat berangkat — prasyaratnya tidak pernah "
                              "tertutup (mis. remedi ber-`depends_on` unit asalnya)")
            return out
        out.update(state="EKSEKUSI", next="frontend:architect", detail=f"{ready} brief READY")
        return out
    review = taskdir / "REVIEW.md"
    if not review.is_file() or not review_is_fresh(root, rel):
        out.update(state="PENUTUP", next="frontend:architect (Phase 4)", detail="seluruh brief tertutup")
        return out
    verdict = read_status(review, "verdict")
    if verdict not in REVIEW_VERDICTS:
        out.update(state="PENUTUP", next="frontend:architect (Phase 4, review ulang)",
                   detail=f"REVIEW.md ber-verdict `{verdict or '(kosong)'}` di luar {'/'.join(REVIEW_VERDICTS)} "
                          "— tidak lolos `validate_review.py`; review ulang menimpanya")
        return out
    if verdict == "BLOCKED":
        out.update(state="TEMUAN", next="chain.py reopen --row BRIEF → frontend:plan (mode APPEND, brief perbaikan)",
                   detail=f"{rel}/REVIEW.md BLOCKED — diperbaiki di taskdir yang sama, lalu review ulang")
        return out
    if not (taskdir / "REPORT.md").is_file():
        out.update(state="LAPORAN", next="frontend:architect (Phase 5)", detail=f"REVIEW.md {verdict}")
        return out
    if not report_valid(root, rel):
        out.update(state="LAPORAN TERTUNDA", next="frontend:architect (Phase 5 butir 4)",
                   detail="REPORT.md tertulis tetapi tidak lolos `validate_report.py`")
        return out
    out.update(state="TUNTAS", next="taskdir baru untuk permintaan baru", detail="REPORT.md terbit")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Taskdir state scanner")
    parser.add_argument("--taskdir", default="", help="satu taskdir; kosong = seluruh frontenddev/docs")
    parser.add_argument("--all", action="store_true", help="sertakan taskdir TUNTAS")
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = (Path(args.root) if args.root else find_repo_root()).resolve()
    error = ""
    if not is_git_repo(root):
        error = f"`{root}` bukan repo git — akar dan commit kode rantai tidak dapat dibuktikan"
    else:
        tracked = docs_git.tracked_docs(root, docs_git.PREFIXES["frontend"])
        if tracked:
            error = (f"MIGRASI: {len(tracked)} berkas `{DOCS}/` masih ter-track git — dokumen taskdir kini hanya di "
                     "disk dan dicerminkan ke nataflow; jalankan prosedur migrasi `frontend:lead` (`AskUserQuestion`, "
                     "lalu `docs_git.py migrate --answer -`)")
    if error:
        print(json.dumps({"status": "FAIL", "error": error}, indent=2) if args.json
              else f"TASKDIR STATE: [FAIL] {error}")
        sys.exit(1)
    if args.taskdir:
        rels = [normalize_taskdir(args.taskdir)]        # segmen `..` dipertahankan → RUSAK (12 J53)
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
