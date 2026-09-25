#!/usr/bin/env python3
"""Plafon ronde reviewer dokumen — `contract-reviewer` (gate `contract`) dan `doc-reviewer` (gate `plan`).

Plafon yang hanya ditulis di prosa dilanggar persis saat ia paling dibutuhkan:
ketika ronde kedua masih menyisakan temuan dan "satu ronde lagi" terasa murah.
Skrip ini menyimpan state ronde di laci `<taskdir>/.explore/<gate>-review-state.json`
(zona kerja, tidak di-commit) dan menolak ronde yang melampaui plafon.

Subperintah:

- `open`   — dipanggil **sebelum** dispatch reviewer. Mencatat ronde baru beserta
             sidik konten berkas yang akan direview, epoch reopen, dan `HEAD`. `FAIL`
             (exit 1) bila plafon putaran (2) atau plafon taskdir (8) habis —
             dispatch dilarang berangkat.
- `record` — dipanggil sesudah balikan reviewer. Mencatat verdict ronde terakhir
             beserta hitungan `BLOCKER [MEKANIS]`/`[SEMANTIK]`.
- `status` — cetak ronde dan sisa plafon.

**Putaran** adalah ronde ber-epoch sama yang dibuka sesudah ronde `PASS` terakhir
yang **sudah diajukan** — kontennya pernah di-commit sesudah ronde itu dibuka
(`git log <head>..HEAD` + sidik isi berkas di tiap commit). Tiap putaran berhak
dua ronde. Commit draft yang belum pernah `PASS` tidak membuka putaran baru,
apa pun subjeknya.

**Epoch** adalah jumlah commit `reopen` yang membuka hop gate ini (`CONTRACT` untuk
gate contract, `BRIEF` untuk gate plan), sebagai target atau kaskade. Reopen
membuka putaran baru dan membatalkan vonis ronde sebelumnya.

`chain.py approve` membaca state ini lewat `Rounds.ready()`: approval `CONTRACT`
dan `BRIEF` hanya sah bila ronde terakhir ber-verdict `PASS`, sidik kontennya
sama dengan konten yang disetujui, dan epoch-nya sama dengan epoch sekarang —
suntingan atau `reopen` sesudah reviewer lolos membatalkan vonisnya. Commit
`draft`/`revise`/`append` sesudah ronde tidak berpengaruh.

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
    BRIEF_GLOB, content_snapshot, find_repo_root, gate_targets_at, git, normalize_taskdir,
    reopen_epoch, snapshot_at,
)

MAX_PER_CYCLE = 2
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

    def epoch(self) -> int:
        return reopen_epoch(self.root, self.taskdir_rel, self.gate)

    def presented(self, r: Dict[str, Any]) -> bool:
        """Ronde PASS yang kontennya sudah di-commit sesudah ronde itu dibuka — sudah diajukan ke user."""
        if r.get("verdict") != "PASS" or not r.get("head"):
            return False
        pathspec = (f"{self.taskdir_rel}/CONTRACT.md" if self.gate == "contract"
                    else f"{self.taskdir_rel}/{BRIEF_GLOB}")
        # head yang hilang (rebase/amend) → git log gagal → dianggap belum diajukan (konservatif)
        for sha in git(self.root, "log", "--format=%H", f"{r['head']}..HEAD", "--", pathspec).split():
            targets = gate_targets_at(self.root, self.taskdir_rel, self.gate, sha)
            if snapshot_at(self.root, sha, targets) == r.get("snapshot"):
                return True
        return False

    def cycle(self, rounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ronde putaran berjalan: epoch sama, sesudah ronde PASS terakhir yang sudah diajukan."""
        epoch = self.epoch()
        cur = [r for r in rounds if r.get("epoch", epoch) == epoch]   # ronde format lama ikut dihitung
        for i in range(len(cur) - 1, -1, -1):
            if self.presented(cur[i]):
                return cur[i + 1:]
        return cur

    def ready(self, state: Optional[Dict[str, Any]] = None) -> str:
        """Kosong bila ronde terakhir `PASS` atas konten disk sekarang dan epoch sekarang; selain itu alasannya."""
        state = self.load() if state is None else state
        rounds = state.get("rounds") or []
        if not rounds:
            return (f"state review `{self.gate}` kosong — reviewer belum pernah berangkat "
                    f"(`review_round.py open --gate {self.gate}`)")
        last = rounds[-1]
        if last.get("verdict") != "PASS":
            return f"ronde review `{self.gate}` terakhir ber-verdict `{last.get('verdict') or 'belum dicatat'}`, bukan PASS"
        if "epoch" not in last:
            return (f"ronde review `{self.gate}` terakhir tercatat format lama (tanpa `epoch`) — "
                    "buka satu ronde baru atas konten sekarang")
        if last["epoch"] != self.epoch():
            return (f"hop dibuka ulang (`reopen`) sesudah ronde review `{self.gate}` terakhir — "
                    "vonisnya atas hulu lama; jalankan ronde baru atas konten sekarang")
        if last.get("snapshot") != content_snapshot(self.root, self.targets()):
            return (f"konten berubah sesudah ronde review `{self.gate}` terakhir — "
                    "jalankan ronde baru atas konten final (bila plafon masih ada)")
        report = self.report_rel()
        if report and last.get("report") != content_snapshot(self.root, [report]):
            return (f"`{report}` bukan laporan ronde terakhir — laporan basi dari ronde "
                    "sebelumnya, atau reviewer gagal menulisnya")
        return ""

    def report_rel(self) -> str:
        return f"{self.taskdir_rel}/REVIEW-PLAN.md" if self.gate == "plan" else ""

    def counts(self, state: Dict[str, Any]) -> Dict[str, int]:
        rounds = state.get("rounds", [])
        return {"cycle": len(self.cycle(rounds)), "taskdir": len(rounds)}

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
        if c["cycle"] >= MAX_PER_CYCLE:
            raise SystemExit(f"REVIEW ROUND OPEN: [FAIL] plafon {MAX_PER_CYCLE} ronde per putaran habis "
                             "(putaran sejak draft terakhir yang lolos `PASS` dan di-commit, epoch "
                             f"reopen {self.epoch()}). Dilarang mendispatch ronde ketiga: sajikan BLOCKER "
                             "yang tersisa ke user dan rutekan ke gate pemilik untuk rancang ulang. "
                             "(Commit ronde `PASS` yang hilang karena rebase/amend tidak lagi dihitung "
                             "sebagai sudah diajukan.)")
        if c["taskdir"] >= MAX_PER_TASKDIR:
            raise SystemExit(f"REVIEW ROUND OPEN: [FAIL] plafon {MAX_PER_TASKDIR} ronde per taskdir habis.")
        entry = {"round": c["cycle"] + 1, "epoch": self.epoch(),
                 "head": git(self.root, "rev-parse", "HEAD").strip(),
                 "snapshot": content_snapshot(self.root, targets), "opened": _now(),
                 "verdict": None}
        rounds.append(entry)
        state["rounds"] = rounds
        self.save(state)
        return (f"REVIEW ROUND OPEN: [PASS] {self.gate} ronde {entry['round']}/{MAX_PER_CYCLE} "
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
               ("perbaiki lalu buka ronde menyempit" if c["cycle"] < MAX_PER_CYCLE
                else "plafon habis — sajikan BLOCKER ke user"))
        return f"REVIEW ROUND RECORD: {self.gate} ronde {rounds[-1]['round']} {verdict} — {nxt}"

    def status(self) -> str:
        state = self.load()
        c = self.counts(state)
        lines = [f"REVIEW ROUND STATUS: {self.gate} — putaran {c['cycle']}/{MAX_PER_CYCLE}, "
                 f"taskdir {c['taskdir']}/{MAX_PER_TASKDIR}"]
        for r in state.get("rounds", []):
            where = (f"epoch {r['epoch']}, head {str(r.get('head', ''))[:7] or '-'}" if "epoch" in r
                     else f"format lama {r.get('generation', '-')}")
            lines.append(f"- ronde {r.get('round')} [{where}] → {r.get('verdict') or 'terbuka'}"
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
