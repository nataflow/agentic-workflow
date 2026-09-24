#!/usr/bin/env python3
"""Plafon ronde reviewer dokumen — `contract-reviewer` (gate `contract`) dan `doc-reviewer` (gate `plan`).

Plafon yang hanya ditulis di prosa dilanggar persis saat ia paling dibutuhkan:
ketika ronde kedua masih menyisakan temuan dan "satu ronde lagi" terasa murah.
Skrip ini menyimpan state ronde di laci `<taskdir>/.explore/<gate>-review-state.json`
(zona kerja, tidak di-commit) dan menolak ronde yang melampaui plafon.

Subperintah:

- `open`   — dipanggil **sebelum** dispatch reviewer. Mencatat ronde baru beserta
             sidik konten berkas yang akan direview. `FAIL` (exit 1) bila plafon
             generasi (2) atau plafon taskdir (8) habis — dispatch dilarang berangkat.
- `record` — dipanggil sesudah balikan reviewer. Mencatat verdict ronde terakhir
             beserta hitungan `BLOCKER [MEKANIS]`/`[SEMANTIK]`.
- `status` — cetak ronde dan sisa plafon.

**Generasi** adalah siklus kerja yang tercatat di git, bukan nama berkas: tiap
commit `revise`, `reopen`, atau `draft breakdown append` atas berkas yang direview
membuka generasi baru — revisi user dan re-entry yang sah masing-masing berhak atas
dua ronde. Mengganti nama atau menghapus berkas tidak mereset apa pun. Plafon
taskdir (8) tidak pernah reset, dan kegagalan dispatch yang dibatalkan dibatasi 2.

`chain.py approve` membaca state ini: approval `CONTRACT` dan `BRIEF` hanya sah
bila ronde terakhir ber-verdict `PASS` **dan** sidik kontennya sama dengan konten
yang disetujui — suntingan sesudah reviewer lolos membatalkan vonisnya.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from precondition_lib import (  # noqa: E402
    BRIEF_GLOB, find_repo_root, normalize_taskdir, review_generation,
)
from chain import content_snapshot  # noqa: E402

MAX_PER_GENERATION = 2
MAX_PER_TASKDIR = 8
MAX_DISPATCH_FAILED = 2
GATES = ("contract", "plan")


class Rounds:
    def __init__(self, taskdir: str, gate: str, root: Optional[Path] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        self.taskdir = self.root / self.taskdir_rel
        self.gate = gate
        self.path = self.taskdir / ".explore" / f"{gate}-review-state.json"

    def targets(self) -> List[str]:
        if self.gate == "contract":
            return [f"{self.taskdir_rel}/CONTRACT.md"]
        return sorted(f"{self.taskdir_rel}/{p.name}" for p in self.taskdir.glob(BRIEF_GLOB))

    def load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"gate": self.gate, "rounds": []}

    def save(self, state: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    def generation(self) -> str:
        return review_generation(self.root, self.taskdir_rel, self.gate)

    def report_rel(self) -> str:
        return f"{self.taskdir_rel}/REVIEW-PLAN.md" if self.gate == "plan" else ""

    def counts(self, state: Dict[str, Any]) -> Dict[str, int]:
        gen = self.generation()
        rounds = state.get("rounds", [])
        return {"generation": sum(1 for r in rounds if r.get("generation") == gen),
                "taskdir": len(rounds)}

    def open(self) -> str:
        targets = self.targets()
        missing = [t for t in targets if not (self.root / t).is_file()]
        if not targets or missing:
            raise SystemExit(f"REVIEW ROUND OPEN: [FAIL] berkas yang direview tidak ada: {missing or 'nol brief'}")
        state = self.load()
        c = self.counts(state)
        rounds = state.get("rounds", [])
        if rounds and rounds[-1].get("verdict") is None:
            raise SystemExit("REVIEW ROUND OPEN: [FAIL] ronde sebelumnya belum dicatat — jalankan "
                             "`record` dengan verdict balikannya, atau `record --verdict DISPATCH_FAILED` "
                             "bila dispatch gagal (tidak dihitung plafon).")
        if c["generation"] >= MAX_PER_GENERATION:
            raise SystemExit(f"REVIEW ROUND OPEN: [FAIL] plafon {MAX_PER_GENERATION} ronde per generasi habis "
                             f"(generasi `{self.generation()}`). Dilarang mendispatch ronde ketiga: sajikan "
                             "BLOCKER yang tersisa ke user dan rutekan ke gate pemilik untuk rancang ulang.")
        if c["taskdir"] >= MAX_PER_TASKDIR:
            raise SystemExit(f"REVIEW ROUND OPEN: [FAIL] plafon {MAX_PER_TASKDIR} ronde per taskdir habis.")
        entry = {"round": c["generation"] + 1, "generation": self.generation(),
                 "snapshot": content_snapshot(self.root, targets), "opened": _now(),
                 "verdict": None}
        rounds.append(entry)
        state["rounds"] = rounds
        self.save(state)
        return (f"REVIEW ROUND OPEN: [PASS] {self.gate} ronde {entry['round']}/{MAX_PER_GENERATION} "
                f"(taskdir {c['taskdir'] + 1}/{MAX_PER_TASKDIR}) atas {len(targets)} berkas")

    def record(self, verdict: str, mechanical: int, semantic: int) -> str:
        state = self.load()
        rounds = state.get("rounds", [])
        if not rounds or rounds[-1].get("verdict") is not None:
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] tidak ada ronde terbuka — `open` dulu.")
        if verdict == "DISPATCH_FAILED":
            failed = state.get("dispatch_failed", 0)
            if failed >= MAX_DISPATCH_FAILED:
                raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] sudah {failed} dispatch gagal dibatalkan — "
                                 "catat vonis sebenarnya, atau laporkan gate tidak tuntas ke user.")
            rounds.pop()
            state["rounds"] = rounds
            state["dispatch_failed"] = failed + 1
            self.save(state)
            return "REVIEW ROUND RECORD: dispatch gagal — ronde dibatalkan, tidak dihitung plafon"
        if verdict == "PASS" and (mechanical or semantic):
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] verdict PASS dengan BLOCKER > 0 adalah kontradiksi.")
        if verdict == "BLOCKED" and not (mechanical or semantic):
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] verdict BLOCKED tanpa satu pun BLOCKER.")
        report = self.report_rel()
        if report and not (self.root / report).is_file():
            raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] `{report}` tidak ada — reviewer belum menulis laporannya.")
        rounds[-1].update({"verdict": verdict, "mechanical": mechanical, "semantic": semantic,
                           "recorded": _now(),
                           "report": content_snapshot(self.root, [report]) if report else ""})
        state["rounds"] = rounds
        self.save(state)
        c = self.counts(state)
        nxt = ("gerbang terbuka" if verdict == "PASS" else
               "perbaiki, jalankan validator, lalu buka ronde menyempit atas konten final (approval menuntut ronde PASS)"
               if not semantic else
               ("perbaiki lalu buka ronde menyempit" if c["generation"] < MAX_PER_GENERATION
                else "plafon habis — sajikan BLOCKER ke user"))
        return f"REVIEW ROUND RECORD: {self.gate} ronde {rounds[-1]['round']} {verdict} — {nxt}"

    def status(self) -> str:
        state = self.load()
        c = self.counts(state)
        lines = [f"REVIEW ROUND STATUS: {self.gate} — generasi {c['generation']}/{MAX_PER_GENERATION}, "
                 f"taskdir {c['taskdir']}/{MAX_PER_TASKDIR}"]
        for r in state.get("rounds", []):
            lines.append(f"- ronde {r.get('round')} [{r.get('generation')}] → {r.get('verdict') or 'terbuka'}"
                         + (f" (mekanis {r.get('mechanical')}, semantik {r.get('semantic')})" if r.get("verdict") else ""))
        return "\n".join(lines)


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plafon ronde reviewer dokumen frontenddev")
    parser.add_argument("cmd", choices=("open", "record", "status"))
    parser.add_argument("--taskdir", required=True)
    parser.add_argument("--gate", required=True, choices=GATES)
    parser.add_argument("--root", default=None)
    parser.add_argument("--verdict", choices=("PASS", "BLOCKED", "DISPATCH_FAILED"))
    parser.add_argument("--mechanical", type=int, default=0)
    parser.add_argument("--semantic", type=int, default=0)
    args = parser.parse_args()
    rounds = Rounds(args.taskdir, args.gate, Path(args.root) if args.root else None)
    if args.cmd == "open":
        print(rounds.open())
    elif args.cmd == "record":
        if not args.verdict:
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] `--verdict` wajib.")
        print(rounds.record(args.verdict, args.mechanical, args.semantic))
    else:
        print(rounds.status())


if __name__ == "__main__":
    main()
