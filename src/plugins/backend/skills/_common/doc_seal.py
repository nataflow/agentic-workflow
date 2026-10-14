#!/usr/bin/env python3
"""Materai dokumen taskdir backend di disk (Langkah 24) — pengganti commit dokumen.

Dokumen taskdir (`backenddev/docs/<taskdir>/`) diabaikan git dan tidak pernah di-commit (`docs_git.py`).
Titik yang dulu dikunci lewat commit kini dikunci lewat materai yang ditulis skrip ini, satu-satunya
penulisnya:

- `root`        — kunci akar: `base_commit` = sha `HEAD` di frontmatter `TASK.md` (24 K6). Rentang kode
                  rantai (`landed_sha`, `done_sha`) dihitung sejak titik ini. Idempoten; `base_commit` yang
                  tidak sah → FAIL.
- `approve`     — `BRD.md`/`PRD.md` → `status: APPROVED`, `approved_seal` (sidik isi yang disetujui),
                  `approved_at`, `approval` (jawaban user), lalu centang hop ledger `## Chain`
                  `@ APPROVED <sidik12>` (24 K8). Satu-satunya jalur tulis `APPROVED`.
- `lock-briefs` — kunci batch brief sesudah self-review lolos: `sidik_kontrak` (sidik `verify_scope.brief_contract`)
                  ke tiap brief `READY` (24 K10). Brief `DONE`/`BLOCKED`/`SUPERSEDED` tidak disentuh.
- `tick`        — centang hop `BRIEF` `@ READY <sidik12 batch>` sesudah tiap brief hidup terkunci utuh.
- `cabut-halt`  — `HALT.md` → `status: DICABUT` beserta alasannya (24 K11); berkasnya tetap sebagai jejak.
- `status`      — vonis seluruh materai taskdir (read-only).

Batas yang dinyatakan apa adanya: materai menangkap suntingan dokumen yang tidak lewat skrip ini, bukan
pemalsuan materai itu sendiri oleh runtime yang sama. Jawaban user wajib satu baris (`--answer -` dari stdin).

Exit: 0 = PASS, 1 = FAIL. `--json` selalu JSON. Zero external dependencies (Python Standard Library only).
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs_git  # noqa: E402
from brief_status import HALT_FILE, HALT_REVOKED, read_frontmatter, scan_briefs, set_frontmatter  # noqa: E402
from precondition_lib import (  # noqa: E402
    check_taskdir,
    cli,
    doc_seal,
    find_repo_root,
    task_base_commit,
)
from verify_scope import SIDIK_FIELD, contract_sidik  # noqa: E402

PREFIX = "backenddev"
DOC_HOPS = {"BRD": "BRD.md", "PRD": "PRD.md"}
LIVE_BRIEFS = ("READY", "DONE", "BLOCKED")   # SUPERSEDED tidak dieksekusi lagi dan tidak menahan rantai
_LEDGER = re.compile(r"^- \[(?P<mark>[ xX~])\] (?P<hop>BRD|PRD|BRIEF)\b(?P<mid>.*?)(?P<tail>[ \t]+@[ \t].*)?$")
_WAS = re.compile(r"\(was (?P<old>[^)]+)\)")


class SealError(Exception):
    pass


def flat(value: str, limit: int = 200) -> str:
    """Teks bebas → satu baris berkutip ganda, aman ditulis ke frontmatter (pola analyst `clean_value`)."""
    return '"' + " ".join(value.replace('"', "'").split())[:limit] + '"'


def read_answer(value: str) -> str:
    answer = (sys.stdin.read() if value == "-" else value).strip()
    if not answer:
        raise SealError("`--answer` kosong — approval wajib memateraikan jawaban eksplisit user dari AskUserQuestion")
    if "\n" in answer or "\r" in answer:
        raise SealError("`--answer` memuat baris baru — tulis satu baris jawaban user apa adanya")
    return answer


class Taskdir:
    def __init__(self, arg: str):
        self.root = find_repo_root()
        verdict = check_taskdir(self.root, arg)
        if not verdict.ok:
            raise SealError(verdict.summary)
        self.rel, self.path = verdict.rel, verdict.path
        self.task = self.path / "TASK.md"
        if not self.task.is_file():
            raise SealError(f"{self.rel}/TASK.md belum ada — akar ditulis `backend:task` lebih dulu")

    def require_root(self) -> str:
        value, problem = task_base_commit(self.root, self.path)
        if problem:
            raise SealError(f"{self.rel}/TASK.md: {problem} — jalankan `doc_seal.py root` lewat `backend:task`")
        return value

    # -- ledger --------------------------------------------------------------------------------

    def ledger_row(self, hop: str) -> Tuple[List[str], str, int, "re.Match"]:
        """`(baris, newline, indeks, match)` baris hop `hop` yang belum tercentang di `## Chain`."""
        text = self.task.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in text else "\n"
        lines = text.split(nl)
        in_chain = False
        for i, line in enumerate(lines):
            if line.startswith("## "):
                in_chain = line.strip() == "## Chain"
                continue
            m = _LEDGER.match(line) if in_chain else None
            if not m or m.group("hop") != hop:
                continue
            if m.group("mark") in "xX":
                raise SealError(f"hop `{hop}` sudah tercentang — buka re-entry (`[~]`) lebih dulu bila hop "
                                "dikerjakan ulang")
            return lines, nl, i, m
        raise SealError(f"ledger `## Chain` {self.rel}/TASK.md tanpa baris hop `{hop}`")

    def tick(self, hop: str, state: str, sidik: str) -> str:
        """Centang baris ledger `hop` → `[x] … @ <state> <sidik12>`; jejak `(was …)` re-entry dipertahankan."""
        lines, nl, i, m = self.ledger_row(hop)
        was = _WAS.search(m.group("tail") or "")
        tail = f" @ {state} {sidik[:12]}" + (f" (was {was.group('old')})" if was else "")
        lines[i] = f"- [x] {hop}{m.group('mid').rstrip()}{tail}"
        self.task.write_bytes(nl.join(lines).encode("utf-8"))
        return lines[i]

    # -- brief ---------------------------------------------------------------------------------

    def briefs(self) -> List[Dict[str, Any]]:
        out = []
        for b in scan_briefs(self.path):
            text = b["path"].read_bytes().decode("utf-8")
            sidik = str(read_frontmatter(b["path"]).get(SIDIK_FIELD, "")).strip()
            b.update(sidik=sidik, intact=bool(sidik) and contract_sidik(text) == sidik)
            out.append(b)
        return out


def batch_sidik(briefs: List[Dict[str, Any]]) -> str:
    rows = sorted(f"{b['name']}:{b['sidik']}" for b in briefs if b["status"] in LIVE_BRIEFS)
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


# -- subperintah ---------------------------------------------------------------------------------


def cmd_root(td: Taskdir, args) -> Dict[str, Any]:
    tracked = docs_git.tracked_docs(td.root, PREFIX)
    if tracked:
        raise SealError(f"{len(tracked)} berkas `backenddev/docs/` masih ter-track git — migrasi lewat "
                        "`docs_git.py migrate` (gerbang `backend:tech-lead`) sebelum akar dikunci")
    _, problem = docs_git.ensure_ignored(td.root, PREFIX)
    if problem:
        raise SealError(problem)
    current = str(read_frontmatter(td.task).get("base_commit", "")).strip()
    if current:
        problem = docs_git.base_commit_problem(td.root, current)
        if problem:
            raise SealError(f"{td.rel}/TASK.md: {problem}")
        return {"status": "PASS", "base_commit": current, "written": False,
                "summary": f"akar {td.rel} sudah terkunci @ {current[:7]}"}
    head = docs_git.head_sha(td.root)
    if not head:
        raise SealError("repo tanpa commit — `base_commit` butuh `HEAD`; buat commit awal lebih dulu")
    set_frontmatter(td.task, base_commit=head)
    return {"status": "PASS", "base_commit": head, "written": True, "summary": f"akar {td.rel} dikunci @ {head[:7]}"}


def cmd_approve(td: Taskdir, args) -> Dict[str, Any]:
    answer = read_answer(args.answer)
    td.require_root()
    doc = td.path / DOC_HOPS[args.doc]
    if not doc.is_file():
        raise SealError(f"{td.rel}/{doc.name} tidak ada")
    status = str(read_frontmatter(doc).get("status", "")).strip()
    if status not in ("DRAFT", "APPROVED"):
        raise SealError(f"{doc.name} berstatus `{status or '(kosong)'}`, bukan DRAFT")
    td.ledger_row(args.doc)                            # ledger ditolak → dokumen tidak disentuh
    set_frontmatter(doc, status="APPROVED", approved_at=dt.date.today().isoformat(), approval=flat(answer))
    seal = doc_seal(doc.read_bytes().decode("utf-8"))
    set_frontmatter(doc, approved_seal=seal)
    line = td.tick(args.doc, "APPROVED", seal)
    return {"status": "PASS", "doc": f"{td.rel}/{doc.name}", "approved_seal": seal, "ledger": line,
            "summary": f"{doc.name} APPROVED @ {seal[:12]} · ledger: {line.strip()}"}


def cmd_lock_briefs(td: Taskdir, args) -> Dict[str, Any]:
    td.require_root()
    briefs = td.briefs()
    ready = [b for b in briefs if b["status"] == "READY"]
    if not ready:
        raise SealError(f"tidak ada brief READY di {td.rel} — tidak ada yang dikunci")
    for b in ready:
        set_frontmatter(b["path"], **{SIDIK_FIELD: contract_sidik(b["path"].read_bytes().decode("utf-8"))})
    briefs = td.briefs()
    unsealed = [b["name"] for b in briefs if b["status"] in ("DONE", "BLOCKED") and not b["sidik"]]
    batch = batch_sidik(briefs)
    out = {"status": "PASS", "locked": [b["name"] for b in ready], "batch_sidik": batch,
           "summary": f"{len(ready)} brief READY terkunci · batch @ {batch[:12]}"}
    if unsealed:
        out["warnings"] = [f"brief tanpa `{SIDIK_FIELD}`: {', '.join(unsealed)}"]
    return out


def cmd_tick(td: Taskdir, args) -> Dict[str, Any]:
    td.require_root()
    briefs = td.briefs()
    live = [b for b in briefs if b["status"] in LIVE_BRIEFS]
    if not any(b["status"] == "READY" for b in live) and not any(b["status"] == "DONE" for b in live):
        raise SealError(f"tidak ada brief READY/DONE di {td.rel}")
    bad = [b["name"] for b in live if not b["intact"]]
    if bad:
        raise SealError(f"brief belum terkunci atau disunting sesudah dikunci: {', '.join(bad)} — jalankan "
                        "`doc_seal.py lock-briefs` sesudah self-review `brief-reviewer` lolos")
    batch = batch_sidik(briefs)
    line = td.tick("BRIEF", "READY", batch)
    return {"status": "PASS", "batch_sidik": batch, "ledger": line, "summary": f"ledger: {line.strip()}"}


def cmd_cabut_halt(td: Taskdir, args) -> Dict[str, Any]:
    if not args.alasan.strip() or "\n" in args.alasan:
        raise SealError("`--alasan` wajib satu baris berisi")
    halt = td.path / HALT_FILE
    if not halt.is_file():
        raise SealError(f"{td.rel}/{HALT_FILE} tidak ada")
    fm = read_frontmatter(halt)
    if str(fm.get("status", "")).strip().upper() == HALT_REVOKED:
        raise SealError(f"{HALT_FILE} sudah dicabut ({fm.get('dicabut', '-')})")
    set_frontmatter(halt, status=HALT_REVOKED, dicabut=flat(args.alasan))
    return {"status": "PASS", "summary": f"{HALT_FILE} {fm.get('brief', '?')} ({fm.get('verdict', '?')}) dicabut"}


def cmd_status(td: Taskdir, args) -> Dict[str, Any]:
    problems: List[str] = []
    base, problem = task_base_commit(td.root, td.path)
    if problem:
        problems.append(f"TASK.md: {problem}")
    docs: Dict[str, str] = {}
    for hop, name in DOC_HOPS.items():
        path = td.path / name
        if not path.is_file():
            continue
        fm = read_frontmatter(path)
        status, seal = str(fm.get("status", "")).strip(), str(fm.get("approved_seal", "")).strip()
        if status == "APPROVED":
            ok = bool(seal) and seal == doc_seal(path.read_bytes().decode("utf-8"))
            docs[name] = f"APPROVED @ {seal[:12]}" if ok else "APPROVED tanpa materai utuh"
            if not ok:
                problems.append(f"{name} APPROVED tetapi isi ≠ `approved_seal` (atau tanpa materai)")
        else:
            docs[name] = status or "(kosong)"
    briefs = td.briefs()
    drift = [b["name"] for b in briefs if b["status"] in LIVE_BRIEFS and b["sidik"] and not b["intact"]]
    problems += [f"{n} disunting sesudah dikunci (kontrak ≠ `{SIDIK_FIELD}`)" for n in drift]
    halt = td.path / HALT_FILE
    halt_state = "-"
    if halt.is_file():
        halt_state = str(read_frontmatter(halt).get("status", "")).strip().upper() or "AKTIF"
        halt_state = "DICABUT" if halt_state == HALT_REVOKED else "AKTIF"
    return {"status": "FAIL" if problems else "PASS", "base_commit": base, "documents": docs,
            "briefs": {b["name"]: ("terkunci" if b["intact"] else "disunting" if b["sidik"] else "belum dikunci")
                       for b in briefs},
            "halt": halt_state, "problems": problems,
            "summary": f"akar {'@ ' + base[:7] if not problem else 'belum terkunci'} · {len(briefs)} brief · "
                       f"HALT {halt_state}"}


COMMANDS = {"root": cmd_root, "approve": cmd_approve, "lock-briefs": cmd_lock_briefs, "tick": cmd_tick,
            "cabut-halt": cmd_cabut_halt, "status": cmd_status}


def main() -> int:
    ap = argparse.ArgumentParser(description="Materai dokumen taskdir backend di disk (Langkah 24)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        p.add_argument("--taskdir", required=True)
        p.add_argument("--json", action="store_true")
        if name == "approve":
            p.add_argument("--doc", required=True, choices=sorted(DOC_HOPS))
            p.add_argument("--answer", required=True, help="jawaban user apa adanya; `-` = baca dari stdin")
        if name == "tick":
            p.add_argument("--hop", required=True, choices=["BRIEF"])
        if name == "cabut-halt":
            p.add_argument("--alasan", required=True)
    args = ap.parse_args()
    try:
        data = COMMANDS[args.cmd](Taskdir(args.taskdir), args)
    except (SealError, OSError, UnicodeDecodeError, ValueError) as exc:
        data = {"status": "FAIL", "summary": str(exc)}
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"DOC_SEAL {args.cmd.upper()}: [{data['status']}] {data['summary']}")
        for item in data.get("problems") or []:
            print(f"    - {item}")
        for item in data.get("warnings") or []:
            print(f"    - WARN: {item}")
    return 0 if data["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(cli(main))
