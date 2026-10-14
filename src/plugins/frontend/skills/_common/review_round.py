#!/usr/bin/env python3
"""Plafon ronde reviewer dokumen — `contract-reviewer` (gate `contract`) dan `doc-reviewer` (gate `plan`).

Plafon yang hanya ditulis di prosa dilanggar persis saat ia paling dibutuhkan:
ketika ronde kedua masih menyisakan temuan dan "satu ronde lagi" terasa murah.
Skrip ini menyimpan state ronde di laci `<taskdir>/.explore/<gate>-review-state.json`
(zona kerja, tidak dicerminkan) dan menolak ronde yang melampaui plafon.

Subperintah:

- `open`   — dipanggil **sebelum** dispatch reviewer. Mencatat ronde baru beserta
             sidik konten berkas yang akan direview, epoch reopen, dan jumlah kejadian
             `## Riwayat Rantai` saat itu, lalu mencetak `sidik <12 hex>` untuk slot
             `{sidik}` prompt reviewer. `FAIL` (exit 1) bila plafon putaran (2) atau
             plafon taskdir (8) habis — dispatch dilarang berangkat.
- `record` — dipanggil sesudah balikan reviewer. Mencatat verdict ronde terakhir
             beserta hitungan `BLOCKER [MEKANIS]`/`[SEMANTIK]`. Gate contract menuntut
             `--evidence` (balikan `contract-reviewer` apa adanya); gate plan menuntut
             `REVIEW-PLAN.md` ber-`verdict` sama. Laporan wajib menggemakan sidik ronde
             yang terbuka (`- Sidik:` / frontmatter `sidik:`, 12 J45) — laporan ronde
             lama atas konten lain ditolak.
- `status` — cetak ronde, sisa plafon, dan `siap diajukan`. `--ready`: exit 1 bila belum siap
             (ronde terakhir bukan `PASS` atas konten disk dan epoch sekarang).
- `rebuild` — state hilang padahal Riwayat mencatat ronde: tulis ulang hitungan taskdir
             dari field `review` kejadian `draft`/`approve` (ronde sesudah draft terakhir tidak
             terpulihkan).

Draft `CONTRACT.md` dan batch brief lane non-MINOR dicatat `chain.py draft` (Langkah 24, pengganti
`review_round.py commit`): skrip itu menolak kecuali `ready()` di sini kosong, lalu mencatat field
`review <gate> r<n> t<total> PASS <sidik>` di kejadian `draft` — jejak ronde yang ikut tercermin ke
nataflow bersama `TASK.md`.

**Putaran** adalah ronde ber-epoch sama yang dibuka sesudah ronde `PASS` terakhir
yang **sudah diajukan** — ada kejadian `draft` hop gate ini sesudah ronde itu dibuka
dengan sidik yang sama. Tiap putaran berhak dua ronde. Draft yang belum pernah `PASS`
tidak membuka putaran baru.

**Epoch** adalah jumlah kejadian `reopen` yang membuka hop gate ini **atau hop di
atasnya** (`FLOW`/`UI`/`CONTRACT` untuk gate contract, semua hop untuk gate plan),
ditambah kejadian `eskalasi` (12 J42). Dokumen hulu yang berubah membuka putaran
baru dan membatalkan vonis ronde sebelumnya, walau hop gate ini masih `[ ]`.

`chain.py approve` membaca state ini lewat `Rounds.ready()`: approval `CONTRACT`
dan `BRIEF` hanya sah bila ronde terakhir ber-verdict `PASS`, sidik kontennya
sama dengan konten yang disetujui, dan epoch-nya sama dengan epoch sekarang —
suntingan atau `reopen` sesudah reviewer lolos membatalkan vonisnya. Kejadian
`draft` sesudah ronde tidak berpengaruh.

**Batas yang dinyatakan apa adanya**: state di `.explore/` tidak dicerminkan.
Berkas rusak atau berbentuk salah → `FAIL` (pulihkan dari `.bak`, salinan sebelum
tulis terakhir; tulis pertama menyalin state barunya, 12 J52). Berkas hilang → hitungan dari nol, **kecuali**
Riwayat mencatat ronde: maka `FAIL` sampai `rebuild`. Ronde yang belum pernah ikut kejadian `draft`
tidak dapat dibuktikan sesudah lacinya dihapus.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from precondition_lib import (  # noqa: E402
    GATE_ROW, TASKDIR_PATTERN,
    BRIEF_GLOB, content_snapshot, find_repo_root, normalize_taskdir, read_status, reopen_epoch, task_history,
)
from precondition_lib import cli  # noqa: E402

MAX_PER_CYCLE = 2
MAX_PER_TASKDIR = 8
MAX_DISPATCH_FAILED = 2
GATES = ("contract", "plan")
REVIEW_LINE = re.compile(r"^-\s*Verdict:\s*(PASS|BLOCKED)\s*$", re.MULTILINE)
SIDIK_LINE = re.compile(r"^-\s*Sidik:\s*`?([0-9a-f]{12,40})`?\s*$", re.MULTILINE)
SIDIK_LEN = 12
CAP_ROUTE = ("hentikan gate; `frontend:lead` bertanya lewat `AskUserQuestion`: rumuskan ulang di taskdir baru "
             "(`chain.py abandon` taskdir ini) atau hentikan")
BLOCKER_LINE = re.compile(r"^-\s*BLOCKER:\s*(\d+)\s*\[MEKANIS\]\s*·\s*(\d+)\s*\[SEMANTIK\]\s*$", re.MULTILINE)


class Rounds:
    def __init__(self, taskdir: str, gate: str, root: Optional[Path] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        if not TASKDIR_PATTERN.match(self.taskdir_rel):   # state ditulis di <taskdir>/.explore/
            raise SystemExit(f"REVIEW ROUND: [FAIL] `{self.taskdir_rel}` tidak berpola "
                             f"frontenddev/docs/<YYMMDDhhmm>-<slug>")
        self.taskdir = self.root / self.taskdir_rel
        self.gate = gate
        self.path = self.taskdir / ".explore" / f"{gate}-review-state.json"

    def targets(self) -> List[str]:
        if self.gate == "contract":
            return [f"{self.taskdir_rel}/CONTRACT.md"]
        return sorted(f"{self.taskdir_rel}/{p.name}" for p in self.taskdir.glob(BRIEF_GLOB))

    def history(self) -> List[Dict[str, Any]]:
        """Kejadian `## Riwayat Rantai` `TASK.md`; Riwayat rusak → `FAIL` (fail-closed)."""
        events, problem = task_history(self.root, self.taskdir_rel)
        if problem:
            raise SystemExit(f"REVIEW ROUND: [FAIL] `## Riwayat Rantai` rusak: {problem} — laporkan ke user lewat "
                             "`frontend:lead`; dilarang menambal Riwayat dengan tangan.")
        return events

    def committed_rounds(self) -> int:
        """Total ronde taskdir terbesar yang dicatat field `review` gate ini di kejadian Riwayat."""
        rx = re.compile(rf"^{self.gate} r\d+ t(\d+)\b")
        found = [rx.match(e["fields"].get("review", "")) for e in self.history()]
        return max([int(m.group(1)) for m in found if m] or [0])

    def load(self) -> Dict[str, Any]:
        name = self.path.name
        if not self.path.exists():
            committed = self.committed_rounds()
            if committed:
                raise SystemExit(f"REVIEW ROUND: [FAIL] `{name}` hilang padahal `## Riwayat Rantai` mencatat "
                                 f"{committed} ronde — pulihkan dari `{name}.bak`, atau jalankan "
                                 "`review_round.py rebuild`; dilarang memulai hitungan dari nol.")
            return {"gate": self.gate, "rounds": []}
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SystemExit(f"REVIEW ROUND: [FAIL] `{name}` rusak ({exc.__class__.__name__}) — pulihkan "
                             f"dari `{name}.bak`; dilarang menghapus atau menulis ulang dari nol.")
        rounds = state.get("rounds") if isinstance(state, dict) else None
        if not isinstance(rounds, list) or not all(isinstance(r, dict) for r in rounds):
            raise SystemExit(f"REVIEW ROUND: [FAIL] `{name}` tidak berbentuk {{gate, rounds: [...]}} — "
                             f"pulihkan dari `{name}.bak`.")
        if len(rounds) < self.committed_rounds():
            raise SystemExit(f"REVIEW ROUND: [FAIL] `{name}` memuat {len(rounds)} ronde, lebih pendek dari "
                             f"jejak ronde di Riwayat ({self.committed_rounds()}) — pulihkan dari `{name}.bak`.")
        return state

    def save(self, state: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        bak = self.path.with_name(self.path.name + ".bak")
        first = not self.path.exists()
        if not first:
            shutil.copy2(self.path, bak)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)
        if first:                  # 12 J52: pesan "pulihkan dari .bak" wajib benar sejak tulis pertama
            shutil.copy2(self.path, bak)

    def epoch(self) -> int:
        return reopen_epoch(self.root, self.taskdir_rel, self.gate)

    def presented(self, r: Dict[str, Any], events: List[Dict[str, Any]]) -> bool:
        """Ronde PASS yang kontennya tercatat `chain.py draft` sesudah ronde itu dibuka — sudah diajukan ke user.

        Ronde format lama (tanpa `riwayat`, dulu ber-`head` commit) dianggap belum diajukan (konservatif).
        """
        if r.get("verdict") != "PASS" or not isinstance(r.get("riwayat"), int):
            return False
        row, sidik = GATE_ROW[self.gate], str(r.get("snapshot", ""))[:12]
        return any(e["n"] > r["riwayat"] and e["kind"] == "draft" and e["rows"] == [row]
                   and e["fields"].get("sidik") == sidik for e in events)

    def cycle(self, rounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ronde putaran berjalan: epoch sama, sesudah ronde PASS terakhir yang sudah diajukan."""
        epoch = self.epoch()
        events = self.history()
        cur = [r for r in rounds if r.get("epoch", epoch) == epoch]   # ronde format lama ikut dihitung
        for i in range(len(cur) - 1, -1, -1):
            if self.presented(cur[i], events):
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
                             "(putaran sejak draft terakhir yang lolos `PASS` dan dicatat `chain.py draft`, "
                             f"epoch reopen {self.epoch()}). Dilarang mendispatch ronde ketiga: sajikan BLOCKER "
                             f"yang tersisa ke user, lalu {CAP_ROUTE}. Putaran baru hanya dibuka reopen hop "
                             "ini atau hop di atasnya, atau eskalasi lane.")
        if c["taskdir"] >= MAX_PER_TASKDIR:
            raise SystemExit(f"REVIEW ROUND OPEN: [FAIL] plafon {MAX_PER_TASKDIR} ronde per taskdir habis — "
                             f"{CAP_ROUTE}.")
        entry = {"round": c["cycle"] + 1, "epoch": self.epoch(), "riwayat": len(self.history()),
                 "snapshot": content_snapshot(self.root, targets), "opened": _now(),
                 "verdict": None}
        rounds.append(entry)
        state["rounds"] = rounds
        self.save(state)
        return (f"REVIEW ROUND OPEN: [PASS] {self.gate} ronde {entry['round']}/{MAX_PER_CYCLE} "
                f"(taskdir {c['taskdir'] + 1}/{MAX_PER_TASKDIR}) atas {len(targets)} berkas — "
                f"sidik {entry['snapshot'][:SIDIK_LEN]} (slot `{{sidik}}` prompt reviewer)")

    def record(self, verdict: str, mechanical: int, semantic: int, evidence: str = "") -> str:
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
        if mechanical < 0 or semantic < 0:
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] hitungan BLOCKER tidak boleh negatif.")
        if verdict == "PASS" and mechanical + semantic > 0:
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] verdict PASS dengan BLOCKER > 0 adalah kontradiksi.")
        if verdict == "BLOCKED" and mechanical + semantic == 0:
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] verdict BLOCKED tanpa satu pun BLOCKER.")
        report = self.report_rel()
        if report:
            if not (self.root / report).is_file():
                raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] `{report}` tidak ada — reviewer belum menulis laporannya.")
            written = read_status(self.root / report, "verdict")
            if written != verdict:
                raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] `{report}` ber-`verdict: {written or '(kosong)'}`, "
                                 f"bukan `{verdict}` — catat vonis laporan apa adanya.")
            self.check_sidik(read_status(self.root / report, "sidik").strip("`"), rounds[-1], report,
                             "frontmatter `sidik:`")
        else:
            report = self.check_evidence(evidence, verdict, mechanical, semantic, rounds[-1]["round"])
            m = SIDIK_LINE.search((self.root / report).read_text(encoding="utf-8"))
            self.check_sidik(m.group(1) if m else "", rounds[-1], report, "baris `- Sidik:`")
        rounds[-1].update({"verdict": verdict, "mechanical": mechanical, "semantic": semantic,
                           "recorded": _now(),
                           "report": content_snapshot(self.root, [report]) if report else ""})
        if not self.report_rel():
            rounds[-1]["evidence"] = report
        state["rounds"] = rounds
        self.save(state)
        c = self.counts(state)
        nxt = ("gerbang terbuka" if verdict == "PASS" else
               "perbaiki, jalankan validator, lalu buka ronde menyempit atas konten final (approval menuntut ronde PASS)"
               if not semantic else
               ("perbaiki lalu buka ronde menyempit" if c["cycle"] < MAX_PER_CYCLE
                else "plafon habis — sajikan BLOCKER ke user"))
        return f"REVIEW ROUND RECORD: {self.gate} ronde {rounds[-1]['round']} {verdict} — {nxt}"

    def check_sidik(self, written: str, opened: Dict[str, Any], report: str, where: str) -> None:
        """Laporan reviewer wajib menggemakan sidik ronde yang terbuka (12 J45, padanan analyst E9).

        Tanpa ini laporan ronde lama — atas konten yang sudah berubah — dapat dicatat sebagai vonis ronde
        baru tanpa satu dispatch pun.
        """
        want = str(opened.get("snapshot", ""))[:SIDIK_LEN]
        if not written:
            raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] `{report}` tanpa {where} — reviewer wajib menggemakan "
                             f"sidik ronde ini (`{want}`, keluaran `open`); laporan tanpa sidik tidak dapat "
                             "dibuktikan milik ronde ini. Catat `DISPATCH_FAILED` lalu dispatch ulang.")
        if written[:SIDIK_LEN] != want:
            raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] `{report}` ber-Sidik `{written[:SIDIK_LEN]}` ≠ sidik "
                             f"ronde terbuka `{want}` — laporan basi dari ronde lain, atau reviewer menilai konten "
                             "lain. Catat `DISPATCH_FAILED` lalu dispatch ulang atas konten ini.")

    def check_evidence(self, evidence: str, verdict: str, mechanical: int, semantic: int, n: int) -> str:
        """Gate contract: balikan `contract-reviewer` tersimpan dan cocok dengan flag `record`."""
        hint = f"{self.taskdir_rel}/.explore/contract-review-r{n}.md"
        if not evidence:
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] gate contract menuntut `--evidence <berkas>` — "
                             f"simpan balikan `contract-reviewer` apa adanya ke `{hint}` lebih dulu.")
        rel = normalize_taskdir(os.path.relpath(Path(evidence).resolve(), self.root)) \
            if Path(evidence).is_absolute() else normalize_taskdir(evidence)
        if not rel.startswith(f"{self.taskdir_rel}/.explore/"):
            raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] `--evidence` wajib di laci `{self.taskdir_rel}/.explore/`.")
        path = self.root / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if "## Contract Review" not in text:
            raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] `{rel}` tidak ada atau tidak memuat blok `## Contract Review`.")
        v, b = REVIEW_LINE.search(text), BLOCKER_LINE.search(text)
        if not v or not b:
            raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] `{rel}` tanpa baris `- Verdict:` atau "
                             "`- BLOCKER: <n> [MEKANIS] · <n> [SEMANTIK]`.")
        if (v.group(1), int(b.group(1)), int(b.group(2))) != (verdict, mechanical, semantic):
            raise SystemExit(f"REVIEW ROUND RECORD: [FAIL] flag ({verdict}, mekanis {mechanical}, semantik "
                             f"{semantic}) ≠ balikan di `{rel}` ({v.group(1)}, mekanis {b.group(1)}, "
                             f"semantik {b.group(2)}) — catat vonis reviewer apa adanya.")
        return rel

    def rebuild(self) -> str:
        if self.path.exists():
            raise SystemExit(f"REVIEW ROUND REBUILD: [FAIL] `{self.path.name}` masih ada — `rebuild` hanya "
                             "untuk state yang hilang; berkas rusak dipulihkan dari `.bak`.")
        committed = self.committed_rounds()
        if not committed:
            raise SystemExit("REVIEW ROUND REBUILD: [FAIL] `## Riwayat Rantai` tidak mencatat ronde gate ini — tidak "
                             "ada yang dipulihkan.")
        # Ronde rekonstruksi mengisi plafon taskdir tetapi tidak pernah sah untuk approve
        # (tanpa epoch/sidik) dan tidak dihitung di putaran berjalan (epoch -1).
        rounds = [{"round": 0, "epoch": -1, "riwayat": -1, "snapshot": "", "verdict": "REKONSTRUKSI",
                   "mechanical": 0, "semantic": 0, "opened": _now()} for _ in range(committed)]
        self.save({"gate": self.gate, "rounds": rounds, "rebuilt": _now()})
        return (f"REVIEW ROUND REBUILD: {self.gate} — {committed} ronde dipulihkan dari Riwayat "
                f"(taskdir {committed}/{MAX_PER_TASKDIR}); approval menuntut satu ronde baru atas konten sekarang.")

    def status(self) -> str:
        state = self.load()
        problem = self.ready(state)
        c = self.counts(state)
        lines = [f"REVIEW ROUND STATUS: {self.gate} — putaran {c['cycle']}/{MAX_PER_CYCLE}, "
                 f"taskdir {c['taskdir']}/{MAX_PER_TASKDIR}"]
        for r in state.get("rounds", []):
            where = (f"epoch {r['epoch']}, riwayat #{r['riwayat']}" if isinstance(r.get("riwayat"), int)
                     else f"epoch {r['epoch']}, format lama" if "epoch" in r
                     else f"format lama {r.get('generation', '-')}")
            lines.append(f"- ronde {r.get('round')} [{where}] → {r.get('verdict') or 'terbuka'}"
                         + (f" (mekanis {r.get('mechanical')}, semantik {r.get('semantic')})" if r.get("verdict") else ""))
        lines.append("siap diajukan: ya" if not problem else f"siap diajukan: tidak — {problem}")
        return "\n".join(lines)


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def nonneg(value: str) -> int:
    n = int(value)
    if n < 0:
        raise argparse.ArgumentTypeError("hitungan BLOCKER tidak boleh negatif")
    return n


def main() -> None:
    parser = argparse.ArgumentParser(description="Plafon ronde reviewer dokumen frontend")
    parser.add_argument("cmd", choices=("open", "record", "status", "rebuild"))
    parser.add_argument("--taskdir", required=True)
    parser.add_argument("--gate", required=True, choices=GATES)
    parser.add_argument("--root", default=None)
    parser.add_argument("--verdict", choices=("PASS", "BLOCKED", "DISPATCH_FAILED"))
    parser.add_argument("--mechanical", type=nonneg, default=0)
    parser.add_argument("--semantic", type=nonneg, default=0)
    parser.add_argument("--evidence", default="", help="gate contract: balikan reviewer di .explore/")
    parser.add_argument("--ready", action="store_true", help="status: exit 1 bila belum siap diajukan")
    args = parser.parse_args()
    rounds = Rounds(args.taskdir, args.gate, Path(args.root) if args.root else None)
    if args.cmd == "open":
        print(rounds.open())
    elif args.cmd == "record":
        if not args.verdict:
            raise SystemExit("REVIEW ROUND RECORD: [FAIL] `--verdict` wajib.")
        print(rounds.record(args.verdict, args.mechanical, args.semantic, args.evidence))
    elif args.cmd == "rebuild":
        print(rounds.rebuild())
    else:
        out = rounds.status()
        print(out)
        if args.ready and not out.endswith("siap diajukan: ya"):
            sys.exit(1)


if __name__ == "__main__":
    sys.exit(cli(main))
