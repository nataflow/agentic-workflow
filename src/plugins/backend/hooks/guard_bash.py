#!/usr/bin/env python3
"""Pagar mekanis `backend:code-implementor`, `code-explorer`, dan `code-reviewer` (hook PreToolUse, matcher `Bash|Edit|Write`).

  guard_bash.py hook                   # input hook JSON dari stdin
  guard_bash.py lease --brief <path>   # ditulis architect sebelum dispatch implementor
  guard_bash.py lease --clear          # dihapus architect sesudah triase unit

Hanya berlaku bila input hook membawa `agent_type` salah satu dari ketiga agent itu — identitas
subagen plugin di input hook (docs hooks, "Common input fields"). Panggilan lain (main loop,
agent lain, plugin lain) lolos tanpa keputusan (exit 0).

`code-explorer` (tanpa Bash): Edit/Write hanya pada laporan laci `.explore/*.md` di dalam repo
(`backenddev/docs/.explore/<slug>.md` atau `<taskdir>/.explore/<slug>.md`); selain itu ditolak.

`code-reviewer` (09 E19): read-only atas repo kecuali laporannya sendiri. Bash: git baca (+ `merge-base`,
`symbolic-ref`), `ls`, dan `git add`/`git commit -m` hanya atas `<taskdir>/REVIEW.md` dan
`backenddev/issues/README.md`; Write/Edit hanya kedua path itu. Tanpa lease: path-nya berpola tetap.

Untuk implementor: fail-closed — galat internal pun menolak (exit 2), karena exit selain 2 tidak
memblokir (docs hooks: "Any other exit code doesn't block on its own").

Allowlist Bash implementor: git read-only (`status`, `diff`, `log`, `show`, `rev-parse`,
`ls-files`), `git add <path lease>…` tanpa flag, `git commit -m "<pesan>"`. Edit/Write hanya pada
path lease. Lease = scope brief (parser `skills/_common/verify_scope.py`) + berkas brief +
`report-NN.md` + `finding_source`; disimpan di `<git-dir>/nataflow/lease-backend.json`,
di luar working tree sehingga tidak pernah muncul di `git status --porcelain`.
"""
import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "_common"))
try:
    from verify_scope import rel, scope_of  # noqa: E402
    IMPORT_ERROR = None
except Exception as e:  # berkas plugin rusak: implementor tetap ditolak di hook(), bukan diloloskan
    IMPORT_ERROR = e

AGENT = "backend:code-implementor"
EXPLORER = "backend:code-explorer"
REVIEWER = "backend:code-reviewer"
REVIEWER_FILES = re.compile(r"^(backenddev/docs/[^/]+/REVIEW\.md|backenddev/issues/README\.md)$")
REVIEWER_READ_GIT = {"merge-base", "symbolic-ref"}
EXPLORE_REPORT = re.compile(r"^backenddev/docs/(?:[^/]+/)?\.explore/[^/]+\.md$")
META = re.compile(r"[;&|<>`\n\r]|\$\(|\$\{")          # rantai/pengalihan/substitusi → tolak
READ_ONLY_GIT = {"status", "diff", "log", "show", "rev-parse", "ls-files"}
READ_ONLY_BAD_FLAGS = {"--output", "--ext-diff"}      # satu-satunya jalan tulis/eksekusi di subperintah baca


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def repo_root(cwd: str) -> Path:
    out = git(Path(cwd), "rev-parse", "--show-toplevel")
    if out.returncode != 0:
        raise RuntimeError("bukan repo git")
    return Path(out.stdout.strip()).resolve()


def lease_path(root: Path) -> Path:
    gd = Path(git(root, "rev-parse", "--git-dir").stdout.strip())
    return (gd if gd.is_absolute() else root / gd) / "nataflow" / "lease-backend.json"


def decide_bash(cmd: str, root: Path, allowed: set, cwd: Path) -> str:
    """'' bila boleh, selain itu alasan penolakan."""
    if META.search(cmd):
        return "rantai/pipe/pengalihan/substitusi dilarang; jalankan satu perintah polos per panggilan"
    tok = shlex.split(cmd)
    if not tok:
        return "perintah kosong"
    if tok[0] == "git" and len(tok) > 1 and tok[1] in READ_ONLY_GIT:
        bad = READ_ONLY_BAD_FLAGS.intersection(t.split("=")[0] for t in tok)
        return f"flag {sorted(bad)} dilarang" if bad else ""
    if tok[:2] == ["git", "add"]:
        rest = tok[2:]
        ps = rest[rest.index("--") + 1:] if "--" in rest else rest
        flags = [t for t in rest if t.startswith("-") and t != "--"]
        if flags or not ps or any(ch in p for p in ps for ch in "*?[]"):
            return "`git add` hanya menerima path eksplisit tanpa flag dan tanpa glob"
        out = []
        for p in ps:
            try:
                if rel(root, str(cwd / p)) not in allowed:
                    out.append(p)
            except ValueError:
                out.append(p)
        return f"path di luar File scope/lease: {out}" if out else ""
    if tok[:2] == ["git", "commit"]:
        rest = tok[2:]
        if len(rest) == 2 and rest[0] in ("-m", "--message") and rest[1].strip():
            return ""
        return "hanya `git commit -m '<commit_message brief>'` (tanpa -a/--amend/--no-verify/-n/heredoc)"
    return f"perintah di luar allowlist {AGENT}: `{cmd[:80]}`"


def decide_file(file_path: str, root: Path, allowed: set) -> str:
    try:
        p = rel(root, file_path)
    except ValueError:
        return f"`{file_path}` di luar repo"
    return "" if p in allowed else f"`{p}` di luar File scope/lease"


def deny(reason: str) -> int:
    print(f"guard_bash: DITOLAK — {reason}", file=sys.stderr)
    return 2   # exit 2 = blokir; stderr menjadi alasan yang dibaca subagen


def hook() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0                                   # agen tak dapat dikenali: bukan urusan pagar ini
    if not isinstance(data, dict):
        return 0
    if data.get("agent_type") == EXPLORER:
        return explorer_hook(data)
    if data.get("agent_type") == REVIEWER:
        return reviewer_hook(data)
    if data.get("agent_type") != AGENT:
        return 0
    tool = data.get("tool_name")
    if tool not in ("Bash", "Edit", "Write"):
        return 0
    try:
        if IMPORT_ERROR is not None:
            raise IMPORT_ERROR
        cwd = Path(data.get("cwd") or ".").resolve()
        root = repo_root(str(cwd))
        lp = lease_path(root)
        if not lp.exists():
            return deny(f"lease absen ({lp}); architect wajib menjalankan `guard_bash.py lease` sebelum dispatch")
        allowed = set(json.loads(lp.read_text(encoding="utf-8"))["allowed"])
        ti = data["tool_input"]
        reason = decide_bash(ti["command"], root, allowed, cwd) if tool == "Bash" else \
            decide_file(ti["file_path"], root, allowed)
        return deny(reason) if reason else 0
    except Exception as e:                         # fail-closed khusus implementor
        return deny(f"galat internal pagar: {e!r}")


def explorer_hook(data: dict) -> int:
    """`code-explorer` hanya menulis laporan `.explore/*.md`; fail-closed seperti implementor."""
    if data.get("tool_name") not in ("Edit", "Write"):
        return 0
    try:
        cwd = Path(data.get("cwd") or ".").resolve()
        root = repo_root(str(cwd))
        target = str(cwd / data["tool_input"]["file_path"])
        try:
            p = rel(root, target)
        except ValueError:
            return deny(f"`{data['tool_input']['file_path']}` di luar repo")
        if EXPLORE_REPORT.match(p):
            return 0
        return deny(f"{EXPLORER} hanya boleh menulis laporan `.explore/*.md`; `{p}` ditolak")
    except Exception as e:
        return deny(f"galat internal pagar: {e!r}")


def decide_reviewer_bash(cmd: str, root: Path, cwd: Path) -> str:
    """Allowlist Bash reviewer; '' bila boleh."""
    if META.search(cmd):
        return "rantai/pipe/pengalihan/substitusi dilarang; jalankan satu perintah polos per panggilan"
    tok = shlex.split(cmd)
    if not tok:
        return "perintah kosong"
    if tok[0] == "ls":
        return ""
    if tok[0] != "git" or len(tok) < 2:
        return f"perintah di luar allowlist {REVIEWER}: `{cmd[:80]}` — dilarang build/test"
    if tok[1] in READ_ONLY_GIT | REVIEWER_READ_GIT:
        bad = READ_ONLY_BAD_FLAGS.intersection(t.split("=")[0] for t in tok)
        return f"flag {sorted(bad)} dilarang" if bad else ""
    if tok[1] == "add":
        rest = tok[2:]
        ps = rest[rest.index("--") + 1:] if "--" in rest else rest
        if any(t.startswith("-") and t != "--" for t in rest) or not ps:
            return "`git add` hanya menerima path eksplisit tanpa flag"
        bad = []
        for p in ps:
            try:
                if not REVIEWER_FILES.match(rel(root, str(cwd / p))):
                    bad.append(p)
            except ValueError:
                bad.append(p)
        return f"reviewer hanya men-stage REVIEW.md dan backenddev/issues/README.md, bukan {bad}" if bad else ""
    if tok[1] == "commit":
        rest = tok[2:]
        if len(rest) == 2 and rest[0] in ("-m", "--message") and rest[1].strip():
            return ""
        return "hanya `git commit -m '<pesan>'` (tanpa -a/--amend/--no-verify)"
    return f"`git {tok[1]}` dilarang untuk {REVIEWER} (read-only atas repo; dilarang reset/checkout/push/rebase)"


def reviewer_hook(data: dict) -> int:
    """`code-reviewer` read-only kecuali REVIEW.md + indeks issues; fail-closed seperti implementor."""
    tool = data.get("tool_name")
    if tool not in ("Bash", "Edit", "Write"):
        return 0
    try:
        if IMPORT_ERROR is not None:
            raise IMPORT_ERROR
        cwd = Path(data.get("cwd") or ".").resolve()
        root = repo_root(str(cwd))
        ti = data["tool_input"]
        if tool == "Bash":
            reason = decide_reviewer_bash(ti["command"], root, cwd)
        else:
            try:
                p = rel(root, str(cwd / ti["file_path"]))
                reason = "" if REVIEWER_FILES.match(p) else \
                    f"{REVIEWER} hanya menulis REVIEW.md dan backenddev/issues/README.md; `{p}` ditolak"
            except ValueError:
                reason = f"`{ti['file_path']}` di luar repo"
        return deny(reason) if reason else 0
    except Exception as e:
        return deny(f"galat internal pagar: {e!r}")


def lease(brief: str, clear: bool) -> int:
    try:
        root = repo_root(".")
        lp = lease_path(root)
        if clear:
            lp.unlink(missing_ok=True)
            print(f"LEASE CLEARED {lp}")
            return 0
        b = Path(brief).resolve()
        paths, fs = scope_of(b.read_text(encoding="utf-8"))
        if not paths:
            raise ValueError("`## File scope` kosong atau tak terbaca")
        allowed = [rel(root, p) for p in paths] + [rel(root, str(b))]
        nn = re.match(r"brief-(\d+)-", b.name)
        if nn:                                     # jalur gagal: commit wip menstage report-NN.md
            allowed.append(rel(root, str(b.parent / f"report-{nn.group(1)}.md")))
        if fs:                                     # penanda FIXED di-stage implementor (L2.6)
            allowed.append(rel(root, fs))
        lp.parent.mkdir(parents=True, exist_ok=True)
        lp.write_text(json.dumps({"brief": allowed[len(paths)], "allowed": sorted(set(allowed))}, indent=1),
                      encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"LEASE {lp}: {len(paths)} path scope")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=["hook", "lease"])
    ap.add_argument("--brief")
    ap.add_argument("--clear", action="store_true")
    a = ap.parse_args()
    if a.mode == "lease" and not (a.clear or a.brief):
        ap.error("lease butuh --brief atau --clear")
    sys.exit(hook() if a.mode == "hook" else lease(a.brief or "", a.clear))
