#!/usr/bin/env python3
"""Journey — catatan keputusan antar sesi di `<taskdir>/JOURNEY.md` (Langkah 30 J1).

Rantai planning dan eksekusi dapat dipisah sesi (`/clear` atau `/compact` di serah terima
`READY_FOR_IMPLEMENTATION`). State rantai dipulihkan dari disk — ledger, materai, status brief,
commit — tetapi nuansa percakapan (keputusan lisan user, opsi yang ditolak, alasannya) hanya
hidup di konteks sesi. Skrip ini menuliskannya sebagai satu baris pendek per titik rantai.

`JOURNEY.md` **bukan sumber kebenaran**: tidak satu skrip gerbang pun membacanya, dan bila
isinya bertentangan dengan disk, disk yang menang. Waktu dan hop ditulis skrip; kalimatnya
ditulis model, dibatasi plafon di bawah supaya berkas tidak ikut menggemukkan konteks.

    add  --taskdir <t> --hop <HOP> --teks "<kalimat>"   tambah satu entri
    show --taskdir <t>                                   cetak isi (Fase 0 sesi baru)

Plafon: teks 1–280 karakter, satu baris, tanpa blok kode, maksimal 2 kalimat; maksimal 40 entri
per berkas. Exit 0 = PASS, 1 = FAIL (taskdir tak sah, teks/hop ditolak, plafon entri), 2 = argumen.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from precondition_lib import TASKDIR_ACTION, check_taskdir, cli, find_repo_root

NAME = "JOURNEY.md"
HOPS = ("TECH_LEAD", "TASK", "BRD", "PRD", "BRIEF", "READY", "ARCHITECT", "REVIEW")
MAX_TEKS = 280
MAX_KALIMAT = 2
MAX_ENTRI = 40
NOTE = ("> Catatan keputusan antar sesi (Langkah 30). Bukan sumber status: bila bertentangan dengan ledger, "
        "materai, status brief, atau commit, disk yang menang.")
ENTRY_RE = re.compile(r"^- (\d{6} \d{2}:\d{2}) · ([A-Z_]+) · (.+)$")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def entries(text: str) -> List[Dict[str, str]]:
    return [{"waktu": m.group(1), "hop": m.group(2), "teks": m.group(3)}
            for m in (ENTRY_RE.match(line) for line in text.splitlines()) if m]


def teks_problem(teks: str) -> str:
    """Alasan penolakan teks entri, atau string kosong bila sah."""
    if not teks:
        return "teks kosong"
    if "\n" in teks or "\r" in teks:
        return "teks wajib satu baris"
    if "```" in teks:
        return "blok kode dilarang — journey mencatat keputusan, bukan isi kode atau dokumen"
    if len(teks) > MAX_TEKS:
        return f"teks {len(teks)} karakter > {MAX_TEKS}"
    kalimat = [s for s in _SENTENCE_END.split(teks) if s.strip()]
    if len(kalimat) > MAX_KALIMAT:
        return f"{len(kalimat)} kalimat > {MAX_KALIMAT} — sebut keputusan dan alasannya saja"
    return ""


def emit(as_json: bool, status: str, message: str, **extra: Any) -> int:
    if as_json:
        print(json.dumps({"status": status, "message": message, **extra}, ensure_ascii=False, indent=2))
    else:
        print(f"JOURNEY: [{status}] {message}")
    return 0 if status == "PASS" else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Catatan keputusan antar sesi di <taskdir>/JOURNEY.md")
    sub = ap.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add", help="Tambah satu entri")
    add.add_argument("--taskdir", required=True)
    add.add_argument("--hop", required=True)
    add.add_argument("--teks", required=True)
    add.add_argument("--json", action="store_true")
    show = sub.add_parser("show", help="Cetak isi journey")
    show.add_argument("--taskdir", required=True)
    show.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = find_repo_root()
    verdict = check_taskdir(root, args.taskdir)
    if not verdict.ok:
        return emit(args.json, "FAIL", f"{verdict.summary} — {TASKDIR_ACTION}")
    path = verdict.path / NAME
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    current = entries(text)

    if args.cmd == "show":
        if not text:
            return emit(args.json, "PASS", f"{verdict.rel}/{NAME} belum ada", ada=False, entri=[])
        if args.json:
            return emit(True, "PASS", f"{len(current)} entri", ada=True, entri=current)
        print(text.rstrip("\n"))
        return 0

    hop = args.hop.strip().upper()
    if hop not in HOPS:
        return emit(args.json, "FAIL", f"hop `{args.hop}` tidak dikenal — pakai salah satu: {', '.join(HOPS)}")
    teks = args.teks.strip()
    problem = teks_problem(teks)
    if problem:
        return emit(args.json, "FAIL", problem)
    if len(current) >= MAX_ENTRI:
        return emit(args.json, "FAIL", f"{NAME} sudah {len(current)}/{MAX_ENTRI} entri — minta user merangkum entri "
                                       "lama menjadi satu sebelum menambah")
    line = f"- {datetime.now().strftime('%y%m%d %H:%M')} · {hop} · {teks}"
    if not text:
        text = f"# Journey — {verdict.path.name}\n\n{NOTE}\n\n"
    elif not text.endswith("\n"):
        text += "\n"
    path.write_text(text + line + "\n", encoding="utf-8")
    return emit(args.json, "PASS", f"entri {len(current) + 1}/{MAX_ENTRI} ditambahkan ({hop})",
                taskdir=verdict.rel, entri=len(current) + 1, maks=MAX_ENTRI)


if __name__ == "__main__":
    sys.exit(cli(main))
