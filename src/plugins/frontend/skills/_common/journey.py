#!/usr/bin/env python3
"""Journey — catatan keputusan antar sesi di `<taskdir>/JOURNEY.md` (Langkah 33 J1).

Rantai frontend dapat dipisah sesi di dua titik serah terima — `CONTRACT` disetujui → `plan`, dan brief `READY` →
`architect` (`/clear` atau `/compact`, lalu `/frontend:lead lanjutkan <taskdir>`). State rantai dipulihkan dari
disk — ledger, `## Riwayat Rantai`, status brief, commit — tetapi nuansa percakapan (opsi yang ditolak, permintaan
khusus user, alasannya) hanya hidup di konteks sesi. Skrip ini menuliskannya sebagai satu baris pendek per titik.

`JOURNEY.md` **bukan sumber kebenaran**: tidak satu skrip gerbang pun membacanya, dan bila isinya bertentangan
dengan disk, disk yang menang. Waktu dan hop ditulis skrip; kalimatnya ditulis model, dibatasi plafon di bawah
supaya berkas tidak ikut menggemukkan konteks. Teks bebas sengaja tidak masuk `## Riwayat Rantai`: log itu dibaca
setiap gerbang, dan satu baris cacat menggagalkan semuanya.

    add  --taskdir <t> --hop <HOP> --teks "<kalimat>"   tambah satu entri
    show --taskdir <t>                                   cetak isi (sesi baru sesudah serah terima)

Plafon sama dengan journey backend (Langkah 30, B2; `entries`/`teks_problem`/`kalimat`/`hasil_add` dipatok identik
oleh test): teks satu baris tanpa blok kode, maksimal 2 kalimat (titik di backtick, singkatan umum, dan `v1.` tidak
memecah); target 280 karakter, 281–360 diterima dengan `WARN`, di atas 360 ditolak; maksimal 40 entri per berkas. Taskdir wajib
berakar (`TASK.md` ada) — journey yang lahir sebelum akar membuat taskdir tampak kosong di `taskdir_state.py`.
Exit 0 = PASS/WARN, 1 = FAIL (taskdir tak sah, teks/hop ditolak, plafon entri), 2 = argumen.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from precondition_lib import TASKDIR_PATTERN, cli, find_repo_root, normalize_taskdir

NAME = "JOURNEY.md"
HOPS = ("LEAD", "FLOW", "UI", "CONTRACT", "BRIEF", "ARCHITECT", "REVIEW")
MAX_TEKS = 280          # target; 281–MAX_TEKS_KERAS diterima dengan WARN (B2)
MAX_TEKS_KERAS = 360
MAX_KALIMAT = 2
MAX_ENTRI = 40
NOTE = ("> Catatan keputusan antar sesi (Langkah 33). Bukan sumber status: bila bertentangan dengan ledger, "
        "Riwayat Rantai, status brief, atau commit, disk yang menang.")
TASKDIR_ACTION = "Tetapkan taskdir lewat `frontend:lead`; journey ditulis sesudah akar `TASK.md` terkunci."
ENTRY_RE = re.compile(r"^- (\d{6} \d{2}:\d{2}) · ([A-Z_]+) · (.+)$")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# Titik yang bukan akhir kalimat (B2): isi backtick, singkatan umum, dan nomor versi (`v1.`).
_BACKTICK = re.compile(r"`[^`]*`")
_SINGKATAN = re.compile(r"(?i)(?<![\w.])(?:mis|dll|dsb|dst|tsb|dkk|yth|spt|hlm|no|vs|cf|etc|e\.g|i\.e)\.|\bv\d+(?:\.\d+)*\.")


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
    if len(teks) > MAX_TEKS_KERAS:
        return f"teks {len(teks)} karakter > {MAX_TEKS_KERAS} (target {MAX_TEKS})"
    jumlah = len(kalimat(teks))
    if jumlah > MAX_KALIMAT:
        return f"{jumlah} kalimat > {MAX_KALIMAT} — sebut keputusan dan alasannya saja"
    return ""


def kalimat(teks: str) -> List[str]:
    """Kalimat teks entri; titik di backtick, singkatan umum, dan nomor versi tidak memecah (B2)."""
    bersih = _SINGKATAN.sub(lambda m: m.group(0).replace(".", ""), _BACKTICK.sub("`x`", teks))
    return [s for s in _SENTENCE_END.split(bersih) if s.strip()]


def teks_warning(teks: str) -> str:
    """Peringatan untuk teks sah yang melewati target `MAX_TEKS` (B2), atau string kosong."""
    if len(teks) > MAX_TEKS:
        return (f"teks {len(teks)} karakter melewati target {MAX_TEKS} — diterima (batas keras {MAX_TEKS_KERAS}); "
                "tulis entri berikutnya lebih ringkas")
    return ""


def hasil_add(teks: str, nomor: int, hop: str) -> Tuple[str, str, Dict[str, Any]]:
    """(status, pesan, tambahan) keluaran `add` yang berhasil; `WARN` tetap exit 0 (B2)."""
    pesan = f"entri {nomor}/{MAX_ENTRI} ditambahkan ({hop})"
    peringatan = teks_warning(teks)
    extra: Dict[str, Any] = {"entri": nomor, "maks": MAX_ENTRI, "karakter": len(teks),
                             "sisa": max(0, MAX_TEKS - len(teks))}
    if peringatan:
        return "WARN", f"{pesan} — {peringatan}", extra
    return "PASS", f"{pesan} · sisa {MAX_TEKS - len(teks)} karakter dari target {MAX_TEKS}", extra


def taskdir_problem(root: Path, rel: str) -> str:
    if not TASKDIR_PATTERN.match(rel):
        return f"`{rel}` tidak berpola frontenddev/docs/<YYMMDDhhmm>-<slug>"
    if not (root / rel).is_dir():
        return f"`{rel}` tidak ada"
    if not (root / rel / "TASK.md").is_file():
        return f"`{rel}` belum berakar (`TASK.md` tidak ada)"
    return ""


def emit(as_json: bool, status: str, message: str, **extra: Any) -> int:
    if as_json:
        print(json.dumps({"status": status, "message": message, **extra}, ensure_ascii=False, indent=2))
    else:
        print(f"JOURNEY: [{status}] {message}")
    return 0 if status in ("PASS", "WARN") else 1


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
    rel = normalize_taskdir(args.taskdir)
    problem = taskdir_problem(root, rel)
    if problem:
        return emit(args.json, "FAIL", f"{problem} — {TASKDIR_ACTION}")
    path = root / rel / NAME
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    current = entries(text)

    if args.cmd == "show":
        if not text:
            return emit(args.json, "PASS", f"{rel}/{NAME} belum ada", ada=False, entri=[])
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
        text = f"# Journey — {Path(rel).name}\n\n{NOTE}\n\n"
    elif not text.endswith("\n"):
        text += "\n"
    path.write_text(text + line + "\n", encoding="utf-8")
    status, pesan, extra = hasil_add(teks, len(current) + 1, hop)
    return emit(args.json, status, pesan, taskdir=rel, **extra)


if __name__ == "__main__":
    sys.exit(cli(main))
