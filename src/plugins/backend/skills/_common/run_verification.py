#!/usr/bin/env python3
"""Jalankan perintah verifikasi dengan exit code, durasi, timeout, dan ekor log yang tercatat mesin.

Mode:
  baseline  jalankan tiap perintah, simpan {taskdir}/.explore/verification-baseline.json
  closing   jalankan tiap perintah, bandingkan dengan baseline, tulis
            {taskdir}/.explore/closing-verification.md (tabel yang dibaca pemeriksa penutup: frontend
            `validate_review.py`, backend architect Fase 4)
            dan log mesin closing-verification.json di sebelahnya (frontend `validate_review.py --log`)

Perintah dijalankan `bash -o pipefail -c` (exit sisi kiri pipa tidak hilang, 12 J11); tanpa `bash`, lewat
`sh -c` dan `--cmd` ber-`|` ditolak. Tiap hasil baseline mencatat `head` (commit tempat ia diukur) dan log
closing membawanya sebagai `baseline_head` (12 J13).

Exit: 0 = tidak ada merah baru; 1 = ada TIMEOUT atau galat baru; 2 = argumen/IO salah.
Hanya pustaka standar.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from collections import Counter, deque
from pathlib import Path
from typing import Iterable, Optional

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
# Kata kunci galat, atau diagnostik kompilator `berkas:baris[:kolom]: pesan` (Go, gcc, …) yang tidak memuat
# satu pun kata kunci — `a.go:2:23: undefined: x` dulu tidak menghasilkan tanda sama sekali (11 H14).
ERROR_LINE = re.compile(r"\b(error|errors|failed|failure|fatal|exception)\b|✗|✖|\bFAIL\b"
                        r"|(?:^|\s)[\w./\\-]+\.\w+:\d+(?::\d+)?:\s", re.I)
TAIL_LINES = 10                      # ekor log pengganti tanda galat saat MERAH tanpa satu tanda pun
LOG_TAIL = 40                        # ekor log di laporan
NOT_RUNNABLE = (126, 127)            # perintah tidak dapat dieksekusi / tidak ditemukan
NAME = re.compile(r"^[A-Za-z0-9_-]+$")
VOLATILE = [
    (re.compile(r":\d+:\d+\b"), ":L:C"),                        # posisi baris:kolom bergeser antar-commit
    (re.compile(r"\(\d+(\.\d+)?\s?(ms|s)\)|\b\d+(\.\d+)?\s?(ms|s)\b"), "<dur>"),
    (re.compile(r"0x[0-9a-f]+", re.I), "<addr>"),
]


def _normalize(raw: str) -> str:
    line = ANSI.sub("", raw).strip()
    for pat, rep in VOLATILE:
        line = pat.sub(rep, line)
    return line[:300]


def signatures(lines: Iterable[str], red: bool = False) -> list:
    """Baris galat yang dinormalisasi, **berulang bila berulang** (multiset); selisih multiset = galat baru.

    Galat kedua yang identik sesudah normalisasi (baris/kolom berbeda di berkas yang sama) adalah galat
    baru, bukan warisan (12 J12). Perintah MERAH tanpa satu baris bertanda galat memakai ekor log
    ternormalisasi sebagai tandanya — tetap himpunan: "tidak ada tanda" dulu terbaca "tidak ada galat
    baru" (11 H14). `lines` dibaca bertahap; log raksasa tidak dimuat utuh (12 J23).
    """
    sigs, tail = [], deque(maxlen=TAIL_LINES)
    for raw in lines:
        raw = raw.rstrip("\r\n")
        if not raw.strip():
            continue
        if ERROR_LINE.search(ANSI.sub("", raw)):
            sigs.append(_normalize(raw))
        elif red and not sigs:
            norm = _normalize(raw)
            if norm:
                tail.append(norm)
    if red and not sigs:
        return sorted({f"ekor: {ln}" for ln in tail}) or ["ekor: (log kosong)"]
    return sorted(sigs)


def head_of(cwd: Path) -> Optional[str]:
    """Commit tempat perintah diukur (`git rev-parse HEAD`), atau None di luar git (12 J13)."""
    try:
        proc = subprocess.run(["git", "-C", str(cwd), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _killpg(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:       # proses sudah keluar di antara timeout dan kill (12 J23)
        pass


def run_one(name: str, cmd: str, timeout: int, log_dir: Path, cwd: Path) -> dict:
    log_path = log_dir / f"{name}.log"
    start = time.monotonic()
    status, exit_code = None, None
    bash = shutil.which("bash")
    argv = [bash, "-o", "pipefail", "-c", cmd] if bash else ["/bin/sh", "-c", cmd]
    with open(log_path, "wb") as log:
        # start_new_session: seluruh pohon proses (worker jest, daemon gradle) bisa dibunuh saat timeout
        proc = subprocess.Popen(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            exit_code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            status = "TIMEOUT"
    status = status or ("HIJAU" if exit_code == 0 else "MERAH")
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        sigs = signatures(fh, red=status == "MERAH")
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        tail = [ln.rstrip("\r\n") for ln in deque(fh, maxlen=LOG_TAIL)]
    return {
        "name": name, "cmd": cmd, "exit": exit_code,
        "status": status,
        "duration_s": round(time.monotonic() - start, 1),
        "signatures": sigs,
        "tail": tail,
        "log": str(log_path),
        "head": head_of(cwd),
    }


def new_errors(res: dict, base: Optional[dict]) -> int:
    if res["status"] == "HIJAU":
        return 0
    base = base if isinstance(base, dict) else None
    fresh = sum((Counter(res["signatures"]) - Counter((base or {}).get("signatures", []))).values())
    # Tidak ada baseline merah yang bisa memaafkan, atau perintahnya tidak dapat dijalankan sama sekali
    # (exit 126/127 = verifikasi tidak pernah terjadi, bukan merah warisan — 11 H14): minimal 1 galat baru.
    if base is None or base.get("status") == "HIJAU" or res.get("exit") in NOT_RUNNABLE:
        return max(1, fresh)
    return fresh


def render_md(results: list, baseline: dict) -> str:
    # Tiga kolom pertama = kontrak pembaca tabel (frontend validate_review.py `_verification_red`
    # membaca cells[0..2]; backend architect Fase 4 membacanya apa adanya).
    # Perintah penuh di kolom terakhir: '|' di dalam perintah tidak menggeser tiga kolom itu.
    out = ["| Perintah | Hasil | Galat baru vs baseline | Exit | Durasi | Perintah penuh |",
           "|---|---|---|---|---|---|"]
    for r in results:
        out.append(f"| `{r['name']}` | {r['status']} | {r['new']} | "
                   f"{'—' if r['exit'] is None else r['exit']} | {r['duration_s']}s | `{r['cmd']}` |")
    if not baseline:
        out += ["", "> Baseline absen: tiap MERAH dihitung minimal 1 galat baru."]
    inherited = [r["name"] for r in results if r["status"] == "TIMEOUT"
                 and isinstance(baseline.get(r["name"]), dict) and baseline[r["name"]].get("status") == "TIMEOUT"]
    if inherited:
        out += ["", f"> TIMEOUT warisan (baseline juga TIMEOUT): {', '.join(inherited)} — ulangi sekali dengan "
                    f"`--timeout` 3× lipat; masih TIMEOUT → eskalasi ke user, bukan dianggap hijau."]
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
        bad = [p[0] for p in pairs if not NAME.match(p[0])]
        if bad:   # nama menjadi nama berkas log (11 H16)
            raise ValueError(f"NAMA --cmd hanya huruf, angka, `_`, `-`: {', '.join(bad)}")
        names = [p[0] for p in pairs]
        dup = sorted({n for n in names if names.count(n) > 1})
        if dup:   # log dan entri baseline saling menimpa (12 J23)
            raise ValueError(f"NAMA --cmd ganda: {', '.join(dup)}")
        if not shutil.which("bash") and any("|" in p[1] for p in pairs):
            raise ValueError("`bash` tidak ada di PATH: `--cmd` berpipa tidak dapat divonis tanpa `pipefail` "
                             "(12 J11) — pasang bash atau jalankan tanpa pipa")
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    results = [run_one(n, c, args.timeout, log_dir, root) for n, c in pairs]

    if args.mode == "baseline":
        base_path.write_text(json.dumps({r["name"]: r for r in results}, indent=1), encoding="utf-8")
        for r in results:
            print(f"BASELINE {r['name']}: {r['status']} exit={r['exit']} {r['duration_s']}s "
                  f"galat={len(r['signatures'])}")
            if r["status"] == "TIMEOUT":
                print(f"    ukur ulang sekali: --timeout {args.timeout * 3} --force (11 H15)")
        return 0

    baseline = {}
    if base_path.exists():
        try:
            baseline = json.loads(base_path.read_text(encoding="utf-8"))
            if not isinstance(baseline, dict):
                raise ValueError("bukan objek JSON")
        except ValueError as exc:   # termasuk UnicodeDecodeError: baseline rusak = tanpa pembanding (merah)
            print(f"PERINGATAN: baseline {base_path} rusak ({exc}) — semua galat dihitung baru")
            baseline = {}
    red = False
    for r in results:
        r["new"] = new_errors(r, baseline.get(r["name"]))
        red |= r["status"] == "TIMEOUT" or r["new"] > 0
        print(f"CLOSING {r['name']}: {r['status']} exit={r['exit']} baru={r['new']} {r['duration_s']}s")
    out = Path(args.out) if args.out else explore / "closing-verification.md"
    out.write_text(render_md(results, baseline), encoding="utf-8")
    def _base(name: str) -> dict:
        b = baseline.get(name)
        return b if isinstance(b, dict) else {}
    log = [{"cmd": r["name"], "full": r["cmd"], "status": r["status"], "exit": r["exit"], "new_errors": r["new"],
            "baseline_status": _base(r["name"]).get("status"),
            "baseline_errors": len(_base(r["name"]).get("signatures", [])),
            "baseline_head": _base(r["name"]).get("head")} for r in results]
    out.with_suffix(".json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"VERDICT: {'MERAH' if red else 'HIJAU'} -> {out}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
