#!/usr/bin/env python3
"""Pagar mekanis subagen `frontend` (hook PreToolUse, matcher `Bash|Edit|Write`).

  guard_bash.py hook                   # input hook JSON dari stdin

Hanya berlaku bila input hook membawa `agent_type` salah satu agent di bawah — identitas subagen plugin di
input hook (docs hooks, "Common input fields"). Panggilan lain (main loop, agent lain, plugin lain) lolos
tanpa keputusan (exit 0). Fail-closed: galat internal pun menolak (exit 2), karena exit selain 2 tidak
memblokir.

`frontend:code-reviewer` bekerja read-only atas repo (`agents/code-reviewer.md` Kalibrasi, 09 E15):
- Bash: git baca (`status`, `diff`, `log`, `show`, `rev-parse`, `ls-files`, `merge-base`, `blame`, dan
  `symbolic-ref` bentuk baca) tanpa `--output`/`--ext-diff` dan tanpa opsi global selain `--no-pager`;
  `ls`; `python3 <plugin ini>/skills/_common/chain.py files …`.
- Write: `frontenddev/docs/<taskdir>/REVIEW.md`.
- Edit: `REVIEW.md` yang sama, dan berkas temuan `frontenddev/reviews/*.md` (baris `> Status:` saja;
  isinya dinilai architect lewat `validate_audit.py --only-status-changed`, sisanya oleh TREE).

Penulis lain (12 J4) tidak memegang `Bash`, jadi yang dipagar hanya Edit/Write:
- `frontend:code-implementor`: ditolak di luar repo, di `.git/`, atau pada path ter-ignore git — tempat yang
  tidak terlihat `verify_scope.py --worktree`. Scope `files_touched`-nya tetap divonis `verify_scope.py`
  sesudah unit (L3.4 Opsi B; lease ala backend sengaja tidak dibawa).
- `frontend:code-explorer`: hanya laci `frontenddev/docs/<taskdir>/.explore/*.md` atau
  `.frontenddev/explore/*.md`.
- `frontend:doc-reviewer`: hanya `frontenddev/docs/<taskdir>/REVIEW-PLAN.md`.
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
except Exception as e:  # berkas plugin rusak: agent terpagar tetap ditolak di hook(), bukan diloloskan
    IMPORT_ERROR = e

REVIEWER = "frontend:code-reviewer"
IMPLEMENTOR = "frontend:code-implementor"
EXPLORER = "frontend:code-explorer"
DOC_REVIEWER = "frontend:doc-reviewer"
# `shlex` bukan bash (11 H1): ANSI-C `$'…'`, `$VAR`, dan brace expansion diperluas bash tetapi terbaca
# literal oleh `shlex`, sehingga yang dinilai berbeda dari yang dijalankan. Kelas karakternya ditolak utuh.
EXPANSION = re.compile(r"[$`\n\r]")
BRACE = re.compile(r"\{[^{}]*(?:,|\.\.)[^{}]*\}")   # `{a,b}`/`{1..3}`; `HEAD@{1}` tetap lolos
OPERATOR_CHARS = set(";&|<>()")
# `grep` keluar (12 J1): `-O<cmd>`/`--open-files-in-pager` menjalankan pager lewat shell; pakai tool Grep.
READ_ONLY_GIT = {"status", "diff", "log", "show", "rev-parse", "ls-files", "merge-base", "symbolic-ref", "blame"}
GIT_GLOBAL_OK = {"--no-pager"}
BAD_FLAGS = {"--output", "--ext-diff", "--open-files-in-pager", "-O"}   # `-O` tetap ditolak (12 J8)
CHAIN_PY = Path(__file__).resolve().parents[1] / "skills" / "_common" / "chain.py"
TASKDIR = r"frontenddev/docs/\d{10}-[a-z0-9-]+"
WRITE_OK = re.compile(rf"^{TASKDIR}/REVIEW\.md$")
EDIT_OK = re.compile(rf"^({TASKDIR}/REVIEW\.md|frontenddev/reviews/[^/]+\.md)$")
EXPLORE_OK = re.compile(rf"^({TASKDIR}/\.explore/[^/]+\.md|\.frontenddev/explore/[^/]+\.md)$")
PLAN_REVIEW_OK = re.compile(rf"^{TASKDIR}/REVIEW-PLAN\.md$")


def repo_root(cwd: Path) -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("bukan repo git")
    return Path(out.stdout.strip()).resolve()


def unquoted_glob(cmd: str) -> bool:
    """Benar bila `*`/`?`/`[` tanpa kutip atau escape muncul di kata sebelum `--` (12 J8).

    Bash mengekspansinya menjadi nama berkas, dan nama berkas berawalan `-` terbaca sebagai opsi; sesudah
    `--` hasil ekspansi tetap pathspec. `shlex` membuang kutip, jadi yang dinilai teks mentah.
    """
    quote, word, glob, esc = "", "", False, False
    for ch in cmd + " ":
        if esc:
            word, esc = word + ch, False
        elif quote:
            if ch == quote:
                quote = ""
            elif ch == "\\" and quote == '"':
                esc = True
            else:
                word += ch
        elif ch == "\\":
            esc = True
        elif ch in "'\"":
            quote = ch
        elif ch.isspace():
            if word == "--" and not glob:
                return False
            if glob:
                return True
            word, glob = "", False
        else:
            word, glob = word + ch, glob or ch in "*?["
    return False


def symbolic_ref_readonly(args: List[str]) -> bool:
    """`git symbolic-ref` bentuk baca saja (12 J3): ≤ 1 positional, flag hanya dari allowlist.

    Allowlist, bukan blocklist: parse-options git menerima singkatan (`--del` = `--delete`) dan gugus (`-qd`);
    `-m <reason>` dan `--` juga di luar allowlist.
    """
    read_flags = {"-q", "--quiet", "--no-quiet", "--short", "--no-short", "--recurse", "--no-recurse"}
    flags = [a for a in args if a.startswith("-")]
    return all(f in read_flags for f in flags) and len(args) - len(flags) <= 1


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
    if unquoted_glob(cmd):
        return [], ("glob tanpa kutip (`*`, `?`, `[`) sebelum `--` dilarang; kutip argumennya atau taruh "
                    "path sesudah `--`")
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    tok = list(lex)
    if any(t and set(t) <= OPERATOR_CHARS for t in tok):
        return [], "rantai/pipe/pengalihan dilarang; jalankan satu perintah polos per panggilan"
    if not tok:
        return [], "perintah kosong"
    return tok, ""


def decide_bash(cmd: str, cwd: Path) -> str:
    """'' bila boleh, selain itu alasan penolakan."""
    tok, why = shell_tokens(cmd)
    if why:
        return why
    if tok[0] == "git":
        i = 1
        while i < len(tok) and tok[i].startswith("-"):
            if tok[i] not in GIT_GLOBAL_OK:        # seluruh posisi opsi global, bukan `tok[1]` saja (12 J2)
                return "opsi global git (`-c`, `-C`, `--config-env`, …) dilarang; hanya `--no-pager`"
            i += 1
        sub, args = (tok[i], tok[i + 1:]) if i < len(tok) else ("", [])
        if sub not in READ_ONLY_GIT:
            return f"`git {sub}` bukan subperintah baca — reviewer read-only atas repo"
        if sub == "symbolic-ref" and not symbolic_ref_readonly(args):
            return "`git symbolic-ref` hanya bentuk baca (`[-q] [--short] <name>`) — menulis HEAD dilarang"
        bad = BAD_FLAGS.intersection(t.split("=")[0] for t in args)
        return f"flag {sorted(bad)} dilarang" if bad else ""
    if tok[0] == "ls":
        return ""
    if tok[0] in ("python3", "python") and len(tok) > 2 and tok[2] == "files" \
            and (cwd / tok[1]).resolve() == CHAIN_PY:  # path plugin ini, bukan akhiran (12 J7)
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


def ignored(root: Path, p: str) -> bool:
    """Benar bila git mengabaikan `p`; galat git = benar (fail-closed)."""
    out = subprocess.run(["git", "check-ignore", "-q", "--", p], cwd=root, capture_output=True, text=True)
    if out.returncode not in (0, 1):
        raise RuntimeError(out.stderr.strip() or f"git check-ignore {p} gagal")
    return out.returncode == 0


def decide_writer(agent: str, file_path: str, root: Path, cwd: Path) -> str:
    """Edit/Write implementor/explorer/doc-reviewer (12 J4); '' bila boleh."""
    try:
        p = rel(root, str(cwd / file_path))
    except ValueError:
        return f"`{file_path}` di luar repo"
    if agent == EXPLORER:
        return "" if EXPLORE_OK.match(p) else \
            f"{EXPLORER} hanya menulis laci `<taskdir>/.explore/*.md` atau `.frontenddev/explore/*.md`; `{p}` ditolak"
    if agent == DOC_REVIEWER:
        return "" if PLAN_REVIEW_OK.match(p) else f"{DOC_REVIEWER} hanya menulis `<taskdir>/REVIEW-PLAN.md`; `{p}` ditolak"
    if ".git" in p.lower().split("/"):
        return f"`{p}` di dalam `.git/` — di luar pantauan `git status`"
    if ignored(root, p):
        return f"`{p}` diabaikan git — tulisan di sana tidak terlihat `verify_scope.py`; laporkan di report-NN.md"
    return ""


def deny(reason: str) -> int:
    print(f"guard_bash: DITOLAK — {reason}", file=sys.stderr)
    return 2   # exit 2 = blokir; stderr menjadi alasan yang dibaca subagen


def hook() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    agent = data.get("agent_type")
    tool = data.get("tool_name")
    writer = agent in (IMPLEMENTOR, EXPLORER, DOC_REVIEWER)
    if not (agent == REVIEWER and tool in ("Bash", "Edit", "Write") or writer and tool in ("Edit", "Write")):
        return 0
    try:
        if IMPORT_ERROR is not None:
            raise IMPORT_ERROR
        ti = data["tool_input"]
        cwd = Path(data.get("cwd") or ".").resolve()
        if tool == "Bash":
            reason = decide_bash(ti["command"], cwd)
        elif writer:
            reason = decide_writer(agent, ti["file_path"], repo_root(cwd), cwd)
        else:
            reason = decide_file(tool, ti["file_path"], repo_root(cwd), cwd)
        return deny(reason) if reason else 0
    except Exception as e:                         # fail-closed khusus agent terpagar
        return deny(f"galat internal pagar: {e!r}")

if __name__ == "__main__":
    if sys.argv[1:] != ["hook"]:
        print("pemakaian: guard_bash.py hook   (input hook JSON dari stdin)", file=sys.stderr)
        sys.exit(2)
    sys.exit(hook())
