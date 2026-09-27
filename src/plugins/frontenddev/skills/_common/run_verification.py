#!/usr/bin/env python3
"""Jalankan perintah verifikasi dengan exit code, durasi, timeout, dan ekor log yang tercatat mesin.

Mode:
  baseline  jalankan tiap perintah, simpan {taskdir}/.explore/verification-baseline.json
  closing   jalankan tiap perintah, bandingkan dengan baseline, tulis
            {taskdir}/.explore/closing-verification.md (format tabel yang dibaca validate_review.py)
            dan log mesin closing-verification.json di sebelahnya (`validate_review.py --log`)

Exit: 0 = tidak ada merah baru; 1 = ada TIMEOUT atau galat baru; 2 = argumen/IO salah.
Hanya pustaka standar.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
ERROR_LINE = re.compile(r"\b(error|errors|failed|failure|fatal|exception)\b|✗|✖|\bFAIL\b", re.I)
VOLATILE = [
    (re.compile(r":\d+:\d+\b"), ":L:C"),                        # posisi baris:kolom bergeser antar-commit
    (re.compile(r"\(\d+(\.\d+)?\s?(ms|s)\)|\b\d+(\.\d+)?\s?(ms|s)\b"), "<dur>"),
    (re.compile(r"0x[0-9a-f]+", re.I), "<addr>"),
]


def signatures(text: str) -> set:
    """Baris galat yang dinormalisasi; selisih himpunan = galat baru."""
    sigs = set()
    for raw in text.splitlines():
        line = ANSI.sub("", raw).strip()
        if not line or not ERROR_LINE.search(line):
            continue
        for pat, rep in VOLATILE:
            line = pat.sub(rep, line)
        sigs.add(line[:300])
    return sigs


def run_one(name: str, cmd: str, timeout: int, log_dir: Path, cwd: Path) -> dict:
    log_path = log_dir / f"{name}.log"
    start = time.monotonic()
    status, exit_code = None, None
    with open(log_path, "wb") as log:
        # start_new_session: seluruh pohon proses (worker jest, daemon gradle) bisa dibunuh saat timeout
        proc = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            exit_code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            status = "TIMEOUT"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return {
        "name": name, "cmd": cmd, "exit": exit_code,
        "status": status or ("HIJAU" if exit_code == 0 else "MERAH"),
        "duration_s": round(time.monotonic() - start, 1),
        "signatures": sorted(signatures(text)),
        "tail": text.splitlines()[-40:],
        "log": str(log_path),
    }


def new_errors(res: dict, base: dict) -> int:
    if res["status"] == "HIJAU":
        return 0
    cur = set(res["signatures"])
    if base is None or base.get("status") == "HIJAU":
        # tidak ada baseline merah yang bisa memaafkan: merah minimal 1 galat baru
        return max(1, len(cur - set((base or {}).get("signatures", []))))
    return len(cur - set(base.get("signatures", [])))


def render_md(results: list, baseline: dict) -> str:
    # Tiga kolom pertama = kontrak validate_review.py (_verification_red membaca cells[0..2]).
    # Perintah penuh di kolom terakhir: '|' di dalam perintah tidak menggeser tiga kolom itu.
    out = ["| Perintah | Hasil | Galat baru vs baseline | Exit | Durasi | Perintah penuh |",
           "|---|---|---|---|---|---|"]
    for r in results:
        out.append(f"| `{r['name']}` | {r['status']} | {r['new']} | "
                   f"{'—' if r['exit'] is None else r['exit']} | {r['duration_s']}s | `{r['cmd']}` |")
    if not baseline:
        out += ["", "> Baseline absen: tiap MERAH dihitung minimal 1 galat baru."]
    for r in results:
        if r["status"] != "HIJAU":
            out += ["", f"### {r['name']} — {r['status']}", "```", *r["tail"], "```",
                    f"Log penuh: `{r['log']}`"]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["baseline", "closing"])
    ap.add_argument("--taskdir", required=True)
    ap.add_argument("--cmd", action="append", required=True, metavar="NAMA=PERINTAH")
    ap.add_argument("--timeout", type=int, default=300, help="detik per perintah (default 300)")
    ap.add_argument("--out", help="closing: berkas hasil (default .explore/closing-verification.md)")
    ap.add_argument("--force", action="store_true", help="baseline: timpa baseline yang sudah ada")
    args = ap.parse_args()

    root = Path.cwd()
    explore = Path(args.taskdir) / ".explore"
    base_path = explore / "verification-baseline.json"
    if args.mode == "baseline" and base_path.exists() and not args.force:
        # Re-entry lintas sesi: baseline lama dipakai ulang, bukan diukur ulang di atas brief yang
        # sudah mendarat (galat brief itu akan tertelan jadi "warisan" — lihat L2.4).
        print(f"BASELINE ada, dipakai ulang: {base_path}")
        return 0
    log_dir = explore / "verification-logs" / args.mode
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        pairs = [c.split("=", 1) for c in args.cmd]
        if any(len(p) != 2 or not p[0] or not p[1].strip() for p in pairs):
            raise ValueError("--cmd wajib berbentuk NAMA=PERINTAH")
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    results = [run_one(n, c, args.timeout, log_dir, root) for n, c in pairs]

    if args.mode == "baseline":
        base_path.write_text(json.dumps({r["name"]: r for r in results}, indent=1), encoding="utf-8")
        for r in results:
            print(f"BASELINE {r['name']}: {r['status']} exit={r['exit']} {r['duration_s']}s "
                  f"galat={len(r['signatures'])}")
        return 0

    baseline = {}
    if base_path.exists():
        try:
            baseline = json.loads(base_path.read_text(encoding="utf-8"))
        except ValueError as exc:   # termasuk UnicodeDecodeError: baseline rusak = tanpa pembanding (merah)
            print(f"PERINGATAN: baseline {base_path} rusak ({exc}) — semua galat dihitung baru")
    red = False
    for r in results:
        r["new"] = new_errors(r, baseline.get(r["name"]))
        red |= r["status"] == "TIMEOUT" or r["new"] > 0
        print(f"CLOSING {r['name']}: {r['status']} exit={r['exit']} baru={r['new']} {r['duration_s']}s")
    out = Path(args.out) if args.out else explore / "closing-verification.md"
    out.write_text(render_md(results, baseline), encoding="utf-8")
    log = [{"cmd": r["name"], "full": r["cmd"], "status": r["status"], "exit": r["exit"], "new_errors": r["new"],
            "baseline_status": (baseline.get(r["name"]) or {}).get("status"),
            "baseline_errors": len((baseline.get(r["name"]) or {}).get("signatures", []))} for r in results]
    out.with_suffix(".json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"VERDICT: {'MERAH' if red else 'HIJAU'} -> {out}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
