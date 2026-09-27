#!/usr/bin/env python3
"""Chain Counters — plafon loop rantai planning, dimateraikan di `## Counters` `TASK.md`.

`analyst` memegang lima plafon (re-entry, transisi chain, amandemen akar,
penolakan user per hop, pengembalian `## Open questions` per hop), dan
`business-analysis`/`system-analysis` masing-masing plafon ronde reviewer.
Hitungan yang hanya hidup di ingatan sesi hilang saat compaction atau
pemanggilan ulang, sehingga loop analyst ↔ gerbang dapat melewati plafonnya
tanpa terdeteksi. Skrip ini satu-satunya penulis tabel `## Counters`; perubahan
`TASK.md`-nya ikut commit pembaruan `TASK.md` berikutnya milik penulisnya.

    --bump <kunci>   naikkan satu; melewati plafon → FAIL exit 1, tabel tidak berubah
    --check          cetak seluruh kunci; exit 1 bila ada yang melebihi plafon
    --reset-hop HOP  nolkan kunci ber-hop milik HOP dan hop hilirnya — dipanggil
                     re-entry (Fase 3 butir 0) sesudah `--bump reentry` lolos, supaya
                     revisi hop yang dibuka ulang mendapat ronde reviewer baru;
                     loopnya tetap dibatasi plafon `reentry`

Kunci: `reentry`, `chain_transition`, `root_amendment`, dan kunci ber-hop
`reject:<HOP>`, `oq_return:<HOP>`, `review_round:<HOP>` (`HOP` = BRD | PRD | BRIEF).

Zero external dependencies (Python Standard Library only).
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict

PLAFON = {"reentry": 2, "chain_transition": 2, "root_amendment": 2,
          "reject": 2, "oq_return": 2, "review_round": 2}
PER_HOP = {"reject", "oq_return", "review_round"}
HOPS = ("BRD", "PRD", "BRIEF")
_SECTION = re.compile(r"^## Counters[ \t]*\n(.*?)(?=^## |\Z)", re.M | re.S)
_ROW = re.compile(r"^\|\s*([\w:]+)\s*\|\s*(\d+)\s*\|", re.M)


def parse(text: str) -> Dict[str, int]:
    sec = _SECTION.search(text)
    return {m.group(1): int(m.group(2)) for m in _ROW.finditer(sec.group(1) if sec else "")
            if m.group(1) != "Kunci"}


def render(text: str, counters: Dict[str, int]) -> str:
    """Tulis ulang seksi `## Counters` saja; seksi lain dibiarkan byte-identik."""
    rows = "".join(f"| {k} | {v} | {PLAFON[k.split(':')[0]]} |\n" for k, v in counters.items())
    body = f"\n| Kunci | Nilai | Plafon |\n|---|---|---|\n{rows}\n"
    sec = _SECTION.search(text)
    if sec:
        return text[:sec.start(1)] + body + text[sec.end(1):]
    return text.rstrip("\n") + "\n\n## Counters\n" + body


def validate_key(key: str) -> str:
    base, _, hop = key.partition(":")
    if base not in PLAFON:
        raise ValueError(f"kunci tak dikenal: {key}")
    if (base in PER_HOP) != bool(hop) or (hop and hop not in HOPS):
        raise ValueError(f"kunci `{key}` salah bentuk — "
                         f"{'wajib `' + base + ':<BRD|PRD|BRIEF>`' if base in PER_HOP else 'tanpa hop'}")
    return base


def summary(counters: Dict[str, int]) -> str:
    return " · ".join(f"{k} {v}/{PLAFON[k.split(':')[0]]}" for k, v in counters.items()) or "—"


def main():
    parser = argparse.ArgumentParser(description="Plafon loop rantai planning di ## Counters TASK.md")
    parser.add_argument("--taskdir", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bump", help="Kunci yang dinaikkan satu")
    mode.add_argument("--check", action="store_true", help="Cetak seluruh kunci; exit 1 bila melebihi plafon")
    mode.add_argument("--reset-hop", choices=HOPS, help="Nolkan kunci ber-hop milik hop ini dan hilirnya")
    args = parser.parse_args()

    task = Path(args.taskdir) / "TASK.md"
    if not task.is_file():
        print(f"COUNTER: [FAIL] {task} tidak ada")
        sys.exit(1)
    try:
        text = task.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(f"COUNTER: [FAIL] {task} bukan UTF-8 ({exc.reason} @ byte {exc.start}) — pulihkan dari git")
        sys.exit(1)
    counters = parse(text)

    if args.check:
        over = [k for k, v in counters.items() if k.split(":")[0] in PLAFON and v > PLAFON[k.split(":")[0]]]
        status = "FAIL" if over else "PASS"
        print(f"COUNTER: [{status}] {summary(counters)}")
        for k in over:
            print(f"    - {k} melebihi plafon — jalankan Failure path analyst yang sesuai")
        sys.exit(1 if over else 0)

    if args.reset_hop:
        reopened = HOPS[HOPS.index(args.reset_hop):]
        dropped = [k for k in counters if k.partition(":")[2] in reopened]
        for k in dropped:
            del counters[k]
        task.write_text(render(text, counters), encoding="utf-8")
        print(f"COUNTER: [PASS] hop {', '.join(reopened)} dibuka ulang — dinolkan: {', '.join(dropped) or '—'}")
        sys.exit(0)

    try:
        base = validate_key(args.bump)
    except ValueError as exc:
        print(f"COUNTER: [FAIL] {exc}")
        sys.exit(1)
    n = counters.get(args.bump, 0) + 1
    if n > PLAFON[base]:
        print(f"COUNTER: [FAIL] {args.bump} {n}/{PLAFON[base]} — plafon habis, jalankan Failure path analyst")
        sys.exit(1)
    counters[args.bump] = n
    task.write_text(render(text, counters), encoding="utf-8")
    print(f"COUNTER: [PASS] {args.bump} {n}/{PLAFON[base]}")
    print(f"    stage bersama commit pembaruan TASK.md berikutnya: {task}")
    sys.exit(0)


if __name__ == "__main__":
    main()
