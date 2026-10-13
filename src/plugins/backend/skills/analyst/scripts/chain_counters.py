#!/usr/bin/env python3
"""Chain Counters — plafon loop rantai planning, dimateraikan di `## Counters` `TASK.md`.

`analyst` memegang lima plafon (re-entry, transisi chain, amandemen akar,
penolakan user per hop, pengembalian `## Open questions` per hop), dan
`business-analysis`/`system-analysis` masing-masing plafon ronde reviewer.
Hitungan yang hanya hidup di ingatan sesi hilang saat compaction atau
pemanggilan ulang, sehingga loop analyst ↔ gerbang dapat melewati plafonnya
tanpa terdeteksi. Skrip ini satu-satunya penulis tabel `## Counters`.

`TASK.md` tidak di-commit (Langkah 24), jadi riwayat tabel tidak lagi dibaca dari
git: tiap tulisan skrip ini menambah satu entri ke `<taskdir>/.explore/counters-log.json`
(tabel sesudah tulis + operasinya). Penurunan di tabel disk yang tidak dijelaskan
entri log tertangkap sebagai suntingan tangan (09 E20, 11 H13).

    --bump <kunci>   naikkan satu; melewati plafon → FAIL exit 1, tabel tidak berubah;
                     `reject:<HOP>`/`oq_return:<HOP>` sekaligus menolkan `review_round:<HOP>`
    --check          cetak seluruh kunci; exit 1 bila ada yang melebihi plafon, kunci tak dikenal,
                     atau nilai yang turun di luar `--reset-hop` menurut log tulisan skrip
    --reset-hop HOP  nolkan kunci ber-hop milik HOP dan hop hilirnya — dipanggil
                     re-entry (Fase 3 butir 0) sesudah `--bump reentry` lolos, supaya
                     revisi hop yang dibuka ulang mendapat ronde reviewer baru;
                     loopnya tetap dibatasi plafon `reentry`

Kunci: `reentry`, `chain_transition`, `root_amendment`, dan kunci ber-hop
`reject:<HOP>`, `oq_return:<HOP>`, `review_round:<HOP>` (`HOP` = BRD | PRD | BRIEF).

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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


def unknown_keys(counters: Dict[str, int]) -> List[str]:
    """Kunci yang tidak sah menurut `validate_key` — baris tulisan tangan atau salah ketik."""
    bad = []
    for k in counters:
        try:
            validate_key(k)
        except ValueError:
            bad.append(k)
    return bad


LOG = ".explore/counters-log.json"


def history(taskdir: Path) -> List[Tuple[Dict[str, int], str]]:
    """Entri log tulisan skrip `[(tabel sesudah tulis, operasi)]`, tertua dulu; log absen atau rusak → `[]`.

    Operasi: `bump:<kunci>` atau `reset:<HOP>`. Log tinggal di laci `.explore/` taskdir yang, seperti
    `TASK.md`, hanya ada di disk.
    """
    try:
        raw = json.loads((taskdir / LOG).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for item in raw if isinstance(raw, list) else []:
        table, op = (item.get("counters"), item.get("op")) if isinstance(item, dict) else (None, None)
        if isinstance(table, dict) and isinstance(op, str):
            out.append(({str(k): int(v) for k, v in table.items() if str(v).isdigit()}, op))
    return out


def record(taskdir: Path, counters: Dict[str, int], op: str) -> None:
    """Tambah satu entri log sesudah tabel ditulis."""
    entries = [{"counters": c, "op": o} for c, o in history(taskdir)] + [{"counters": dict(counters), "op": op}]
    path = taskdir / LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def tampered(entries: List[Tuple[Dict[str, int], str]], current: Dict[str, int]) -> List[str]:
    """Penurunan yang tidak dijelaskan operasi skrip, antar-entri log berurutan dan dari entri terakhir ke
    tabel disk sekarang (09 E20).

    Kunci global (`reentry`, `chain_transition`, `root_amendment`) tidak pernah turun. Kunci ber-hop hanya
    boleh turun (atau hilang) di entri `reset:<HOP>` untuk hop itu dan hilirnya, dan hanya bila entri tepat
    sebelumnya `bump:reentry` — urutan re-entry Fase 3 butir 0. `review_round:<HOP>` juga boleh turun di entri
    `bump:reject:<HOP>` atau `bump:oq_return:<HOP>` (11 H27). Tabel disk tidak membawa operasi: penurunan apa
    pun dari entri terakhir adalah suntingan tangan.
    """
    versions = [({}, "")] + entries + [(current, "disk")]
    problems = []
    for (before, prev_op), (after, op) in zip(versions, versions[1:]):
        kind, _, arg = op.partition(":")
        reentered = kind == "reset" and arg in HOPS and prev_op == "bump:reentry"
        reopened = HOPS[HOPS.index(arg):] if reentered else ()
        for k, v in before.items():
            now = after.get(k, 0)
            if now >= v:
                continue
            base, _, hop = k.partition(":")
            if hop and hop in reopened:
                continue
            if base == "review_round" and op in (f"bump:reject:{hop}", f"bump:oq_return:{hop}"):
                continue
            problems.append(f"{k} turun {v} → {now} tanpa `--reset-hop` sesudah `--bump reentry`")
    return problems


def render(text: str, counters: Dict[str, int]) -> str:
    """Tulis ulang seksi `## Counters` saja; seksi lain dibiarkan byte-identik."""
    rows = "".join(f"| {k} | {v} | {PLAFON.get(k.split(':')[0], '?')} |\n" for k, v in counters.items())
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
    return " · ".join(f"{k} {v}/{PLAFON.get(k.split(':')[0], '?')}" for k, v in counters.items()) or "—"


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
    bad = unknown_keys(counters)

    if args.check:
        over = [k for k, v in counters.items() if k.split(":")[0] in PLAFON and v > PLAFON[k.split(":")[0]]]
        # Tabel disk dinilai terhadap entri log terakhir: penurunan tangan apa pun tertangkap.
        drops = tampered(history(Path(args.taskdir)), counters)
        status = "FAIL" if over or bad or drops else "PASS"
        print(f"COUNTER: [{status}] {summary(counters)}")
        for k in over:
            print(f"    - {k} melebihi plafon — jalankan Failure path analyst yang sesuai")
        for k in bad:
            print(f"    - kunci `{k}` tak dikenal — tabel `## Counters` hanya ditulis skrip ini; pulihkan dari "
                  f"entri terakhir `{LOG}`")
        for d in drops:
            print(f"    - {d} — tabel disunting tangan; pulihkan nilainya dari entri terakhir `{LOG}`")
        sys.exit(1 if status == "FAIL" else 0)

    if bad:
        print(f"COUNTER: [FAIL] kunci tak dikenal di `## Counters`: {', '.join(bad)} — tabel disunting tangan; "
              f"pulihkan dari entri terakhir `{LOG}` sebelum menulis")
        sys.exit(1)
    # Menulis di atas nilai yang diturunkan tangan menghapus jejak penurunannya dari versi berikutnya;
    # `--check` saja tidak cukup karena tidak ada fase yang memanggilnya (11 H13, regresi 09 E20).
    drops = tampered(history(Path(args.taskdir)), counters)
    if drops:
        print(f"COUNTER: [FAIL] tabel `## Counters` disunting tangan — pulihkan nilainya dari entri terakhir "
              f"`{LOG}` sebelum menulis:")
        for d in drops:
            print(f"    - {d}")
        sys.exit(1)

    if args.reset_hop:
        reopened = HOPS[HOPS.index(args.reset_hop):]
        dropped = [k for k in counters if k.partition(":")[2] in reopened]
        for k in dropped:
            del counters[k]
        task.write_text(render(text, counters), encoding="utf-8")
        record(Path(args.taskdir), counters, f"reset:{args.reset_hop}")
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
    reset = ""
    if base in ("reject", "oq_return"):
        # Revisi yang dikembalikan user (reject) atau analyst (oq_return) sah mendapat review baru; loopnya
        # tetap dibatasi plafon kunci pemicu ini (11 H27).
        hop = args.bump.partition(":")[2]
        if counters.pop(f"review_round:{hop}", 0):
            reset = f" · review_round:{hop} dinolkan"
    task.write_text(render(text, counters), encoding="utf-8")
    record(Path(args.taskdir), counters, f"bump:{args.bump}")
    print(f"COUNTER: [PASS] {args.bump} {n}/{PLAFON[base]}{reset}")
    sys.exit(0)


if __name__ == "__main__":
    main()
