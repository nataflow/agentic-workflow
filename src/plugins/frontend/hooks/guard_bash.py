#!/usr/bin/env python3
"""Pagar mekanis `frontend:code-reviewer` (hook PreToolUse, matcher `Bash|Edit|Write`).

  guard_bash.py hook                   # input hook JSON dari stdin

Hanya berlaku bila input hook membawa `agent_type` = `frontend:code-reviewer`, identitas subagen
plugin di input hook (docs hooks, "Common input fields"). Panggilan lain (main loop, agent lain,
plugin lain) lolos tanpa keputusan (exit 0). `code-implementor` tidak butuh pagar ini: ia tanpa
`Bash`, dan scope Edit/Write-nya divonis `verify_scope.py` sesudah unit mendarat (L3.4).

Reviewer bekerja read-only atas repo (`agents/code-reviewer.md` Kalibrasi) — prosa itu kini ditegakkan
(09 E15). Fail-closed: galat internal pun menolak (exit 2), karena exit selain 2 tidak memblokir.

Allowlist:
- Bash: git baca (`status`, `diff`, `log`, `show`, `rev-parse`, `ls-files`, `merge-base`,
  `symbolic-ref`, `blame`, `grep`) tanpa `--output`/`--ext-diff`; `ls`; `python3 <…>/chain.py files …`.
- Write: `frontenddev/docs/<taskdir>/REVIEW.md`.
- Edit: `REVIEW.md` yang sama, dan berkas temuan `frontenddev/reviews/*.md` (baris `> Status:` saja;
  isinya dinilai architect lewat `validate_audit.py --only-status-changed`).
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "_common"))
try:
    from verify_scope import rel  # noqa: E402
    IMPORT_ERROR = None
except Exception as e:  # berkas plugin rusak: reviewer tetap ditolak di hook(), bukan diloloskan
    IMPORT_ERROR = e

REVIEWER = "frontend:code-reviewer"
# `shlex` bukan bash (11 H1): ANSI-C `$'…'`, `$VAR`, dan brace expansion diperluas bash tetapi terbaca
# literal oleh `shlex`, sehingga yang dinilai berbeda dari yang dijalankan. Kelas karakternya ditolak utuh.
EXPANSION = re.compile(r"[$`\n\r]")
BRACE = re.compile(r"\{[^{}]*(?:,|\.\.)[^{}]*\}")   # `{a,b}`/`{1..3}`; `HEAD@{1}` tetap lolos
OPERATOR_CHARS = set(";&|<>()")
READ_ONLY_GIT = {"status", "diff", "log", "show", "rev-parse", "ls-files", "merge-base", "symbolic-ref",
                 "blame", "grep"}
BAD_FLAGS = {"--output", "--ext-diff", "--open-files-in-pager", "-O"}
WRITE_OK = re.compile(r"^frontenddev/docs/\d{10}-[a-z0-9-]+/REVIEW\.md$")
EDIT_OK = re.compile(r"^(frontenddev/docs/\d{10}-[a-z0-9-]+/REVIEW\.md|frontenddev/reviews/[^/]+\.md)$")


def repo_root(cwd: Path) -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("bukan repo git")
    return Path(out.stdout.strip()).resolve()


def shell_tokens(cmd: str) -> Tuple[List[str], str]:
    """(token, '') bila `cmd` satu perintah polos; ([], alasan) bila tidak.

    Operator dinilai sesudah tokenisasi, sehingga `<T>` atau `->` di dalam kutip (mis. `git log -S`) tetap
    satu argumen, sedangkan `>`/`|`/`;` di luar kutip menjadi token operator dan ditolak.
    """
    if EXPANSION.search(cmd):
        return [], ("substitusi/ekspansi shell (`$`, backtick) dan baris baru dilarang; "
                    "jalankan satu perintah polos per panggilan")
    if BRACE.search(cmd):
        return [], "brace expansion (`{a,b}`, `{1..3}`) dilarang; tulis tiap argumen utuh"
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    tok = list(lex)
    if any(t and set(t) <= OPERATOR_CHARS for t in tok):
        return [], "rantai/pipe/pengalihan dilarang; jalankan satu perintah polos per panggilan"
    if not tok:
        return [], "perintah kosong"
    return tok, ""


def decide_bash(cmd: str) -> str:
    """'' bila boleh, selain itu alasan penolakan."""
    tok, why = shell_tokens(cmd)
    if why:
        return why
    if tok[0] == "git":
        sub = next((t for t in tok[1:] if not t.startswith("-")), "")
        if len(tok) > 1 and tok[1].startswith("-") and tok[1] != "--no-pager":
            return "opsi global git (`-c`, `-C`, …) dilarang; jalankan dari root repo"
        if sub not in READ_ONLY_GIT:
            return f"`git {sub}` bukan subperintah baca — reviewer read-only atas repo"
        bad = BAD_FLAGS.intersection(t.split("=")[0] for t in tok)
        return f"flag {sorted(bad)} dilarang" if bad else ""
    if tok[0] == "ls":
        return ""
    if tok[0] in ("python3", "python") and len(tok) > 2 and tok[1].endswith("skills/_common/chain.py") \
            and tok[2] == "files":
        return ""
    return f"perintah di luar allowlist {REVIEWER}: `{cmd[:80]}`"


def decide_file(tool: str, file_path: str, root: Path, cwd: Path) -> str:
    try:
        p = rel(root, str(cwd / file_path))
    except ValueError:
        return f"`{file_path}` di luar repo"
    ok = WRITE_OK if tool == "Write" else EDIT_OK
    return "" if ok.match(p) else f"{tool} `{p}` ditolak — reviewer hanya menulis REVIEW.md " \
                                  f"(dan menyunting baris `> Status:` berkas temuan frontenddev/reviews/)"


def deny(reason: str) -> int:
    print(f"guard_bash: DITOLAK — {reason}", file=sys.stderr)
    return 2   # exit 2 = blokir; stderr menjadi alasan yang dibaca subagen


def hook() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict) or data.get("agent_type") != REVIEWER:
        return 0
    tool = data.get("tool_name")
    if tool not in ("Bash", "Edit", "Write"):
        return 0
    try:
        if IMPORT_ERROR is not None:
            raise IMPORT_ERROR
        ti = data["tool_input"]
        if tool == "Bash":
            reason = decide_bash(ti["command"])
        else:
            cwd = Path(data.get("cwd") or ".").resolve()
            reason = decide_file(tool, ti["file_path"], repo_root(cwd), cwd)
        return deny(reason) if reason else 0
    except Exception as e:                         # fail-closed khusus reviewer
        return deny(f"galat internal pagar: {e!r}")


if __name__ == "__main__":
    if sys.argv[1:] != ["hook"]:
        print("pemakaian: guard_bash.py hook   (input hook JSON dari stdin)", file=sys.stderr)
        sys.exit(2)
    sys.exit(hook())
