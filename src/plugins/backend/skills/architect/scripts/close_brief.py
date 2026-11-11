#!/usr/bin/env python3
"""Close Brief — satu vonis penutup per brief sesudah commit unit mendarat (32 C1).

Menggabungkan pemeriksaan `architect` Fase 3 butir 4 yang selalu berjalan berurutan,
supaya main loop membayar satu giliran per brief, bukan empat:

1. `git status --porcelain` — sisa berkas di luar laci `.explore/` → `STRAY`.
2. `skills/_common/verify_scope.py --brief <b> --commit <sha>` → `SCOPE` (exit 1).
3. `symbol_map.py --sha <sha> --path <p> --brief <b>` atas tiap baris `modify`
   `## File scope` → `SYMBOL` (exit 1); exit 2 dilaporkan `DEGRADED` per berkas dan
   tidak menahan (pemanggil jatuh ke hunk header ber-driver).
4. `hooks/guard_bash.py lease --clear` — lease implementor selalu dicabut di akhir.
5. Status brief dibaca dari frontmatter (`status:`), apa adanya.

Vonis tetap exit skrip yang dipanggil; skrip ini hanya merangkumnya. `HALT.md` tidak
ditulis di sini — itu tetap tugas `architect`.

Exit: 0 = `PASS`; 1 = `STRAY` | `SCOPE` | `SYMBOL` (urutan presedensi itu); 2 = galat
pemanggilan (brief tak terbaca, sha salah, bukan repo git).

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
SYMBOL_MAP = HERE / "symbol_map.py"
VERIFY_SCOPE = HERE.parents[1] / "_common" / "verify_scope.py"
GUARD = HERE.parents[2] / "hooks" / "guard_bash.py"
LACI = "/.explore/"


def _run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")


def modify_rows(text: str) -> List[str]:
    """Path baris beraksi `modify` di tabel **File** `## File scope`."""
    m = re.search(r"^## File scope[ \t]*$", text, re.M | re.I)
    if not m:
        return []
    sec = text[m.end():]
    nxt = re.search(r"^## ", sec, re.M)
    sec = sec[:nxt.start()] if nxt else sec
    out = []
    for line in sec.splitlines():
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) >= 4 and cols[0].strip("`").lower() == "modify":
            out.append(cols[1].strip("`").strip())
    return out


def status_of(text: str) -> str:
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    m = re.search(r"^status:\s*(\S+)", fm.group(1), re.M) if fm else None
    return m.group(1).strip("\"'") if m else "?"


def close(root: Path, brief: Path, sha: str, py: str) -> Dict:
    text = brief.read_text(encoding="utf-8")
    result: Dict = {"brief": brief.name, "sha": sha[:7], "status_brief": status_of(text),
                    "stray": [], "scope": "", "simbol": [], "new_declared": [], "degraded": [], "lease": ""}

    porcelain = _run(["git", "status", "--porcelain"], root)
    if porcelain.returncode != 0:
        raise RuntimeError(f"git status gagal: {porcelain.stderr.strip()}")
    for line in porcelain.stdout.splitlines():
        path = line[3:].strip().strip('"')
        if path and LACI not in f"/{path}":
            result["stray"].append(path)

    scope = _run([py, str(VERIFY_SCOPE), "--brief", str(brief), "--commit", sha], root)
    if scope.returncode == 2:
        raise RuntimeError(f"verify_scope: {(scope.stderr or scope.stdout).strip()}")
    result["scope"] = scope.stdout.strip()
    scope_fail = scope.returncode == 1

    for path in modify_rows(text):
        sm = _run([py, str(SYMBOL_MAP), "--root", str(root), "--sha", sha, "--path", path, "--brief", str(brief)], root)
        try:
            out = json.loads(sm.stdout)
        except ValueError:
            out = {"status": "DEGRADED", "reason": (sm.stderr or sm.stdout).strip()}
        if sm.returncode == 2 or out.get("status") == "DEGRADED":
            result["degraded"].append({"path": path, "reason": out.get("reason", "")})
            continue
        result["new_declared"] += [f"{path}#{s}" for s in out.get("new_declared", [])]
        for o in out.get("outside_anchor", []):
            result["simbol"].append({"path": path, "symbol": o["symbol"], "lines": o["lines"]})

    lease = _run([py, str(GUARD), "lease", "--clear"], root)
    result["lease"] = "dicabut" if lease.returncode == 0 else f"GAGAL: {(lease.stderr or lease.stdout).strip()}"

    if result["stray"]:
        result["verdict"] = "STRAY"
    elif scope_fail:
        result["verdict"] = "SCOPE"
    elif result["simbol"]:
        result["verdict"] = "SYMBOL"
    else:
        result["verdict"] = "PASS"
    return result


def line_of(r: Dict) -> str:
    parts = [f"{r['verdict']} {r['brief']} @ {r['sha']}", f"status {r['status_brief']}"]
    if r["stray"]:
        parts.append(f"sisa berkas: {', '.join(r['stray'])}")
    parts.append(r["scope"] or "scope ?")
    if r["simbol"]:
        parts.append("simbol di luar anchor: " + ", ".join(
            f"{s['path']}:{','.join(map(str, s['lines']))} {s['symbol']}" for s in r["simbol"]))
    if r["new_declared"]:
        parts.append("deklarasi baru: " + ", ".join(r["new_declared"]))
    if r["degraded"]:
        parts.append("cek simbol TERDEGRADASI: " + ", ".join(d["path"] for d in r["degraded"]))
    parts.append(f"lease {r['lease']}")
    return " · ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--brief", required=True, help="Path brief yang commit unitnya baru mendarat")
    ap.add_argument("--sha", required=True, help="SHA commit unit (baris `Commit:` laporan implementor)")
    ap.add_argument("--root", default=".", help="Root repositori")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        top = _run(["git", "rev-parse", "--show-toplevel"], Path(a.root))
        if top.returncode != 0:
            raise RuntimeError("bukan repo git")
        root = Path(top.stdout.strip())
        brief = Path(a.brief) if Path(a.brief).is_absolute() else Path(a.root).resolve() / a.brief
        if _run(["git", "cat-file", "-e", f"{a.sha}^{{commit}}"], root).returncode != 0:
            raise RuntimeError(f"sha `{a.sha}` bukan commit")
        r = close(root, brief, a.sha, sys.executable)
    except (OSError, ValueError, RuntimeError) as e:
        if a.json:
            print(json.dumps({"verdict": "ERROR", "reason": str(e)}, ensure_ascii=False))
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(json.dumps(r, ensure_ascii=False) if a.json else line_of(r))
    return 0 if r["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
