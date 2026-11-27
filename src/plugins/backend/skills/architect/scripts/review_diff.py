#!/usr/bin/env python3
"""Review Diff — diff utuh rentang merge-base untuk `code-reviewer` (B13).

`code-reviewer` (opus) dulu menelusuri diff lewat `git show`/`git diff` per berkas: ratusan panggilan Bash
dan puluhan giliran, tiap giliran membaca ulang seluruh konteksnya. Skrip ini dijalankan `architect` Fase 4
butir 2 tepat sebelum dispatch reviewer dan menulis satu berkas:

    {taskdir}/.explore/review/diff.patch

berisi header (`range`, `head`, `base_branch`, berkas yang dikecualikan), `git diff --stat`, lalu diff `-U3`
rentang `<merge-base>..HEAD` tanpa `backenddev/` dan `.claude/` (artefak, bukan kode — sama dengan Fase 0
butir 5 reviewer). Reviewer membacanya dengan `Read` per potongan dan mencocokkan `head:` dengan
`git rev-parse HEAD`; beda berarti berkas basi dan reviewer kembali ke git.

Subdirektori `review/` menjaga berkas ini dari panen laci (`validate_briefs.py` hanya memindai `.explore/*.md`).
Taskdir diabaikan git (Langkah 24), jadi berkas ini tidak pernah ter-commit dan tidak mengotori tree.

Keluaran satu baris: `REVIEW-DIFF PASS: <path> · <mb7>..<head7> · <n> berkas · +<a>/-<d> baris`.
Exit: 0 = berkas ditulis; 1 = merge-base gagal, HEAD detached, atau HEAD = base_branch; 2 = argumen salah,
taskdir tidak ada, atau bukan repo git.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

EXCLUDE = ("backenddev", ".claude")
OUT_REL = ".explore/review/diff.patch"


class Fail(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise Fail(1, f"`git {' '.join(args[:2])}` gagal: {(r.stderr or r.stdout).strip()[:200]}")
    return r.stdout


def pathspec() -> list:
    return ["--", "."] + [f":(exclude){d}" for d in EXCLUDE]


def build(root: Path, taskdir: str, base: str) -> dict:
    try:
        top = Path(git(root, "rev-parse", "--show-toplevel").strip())
    except Fail as e:
        raise Fail(2, f"bukan repo git — {e}")
    td = top / taskdir
    if not td.is_dir():
        raise Fail(2, f"taskdir `{taskdir}` tidak ada")
    try:
        branch = git(top, "symbolic-ref", "-q", "--short", "HEAD").strip()
    except Fail:
        raise Fail(1, "HEAD detached — review menuntut branch kerja taskdir")
    if branch == base:
        raise Fail(1, f"HEAD = `{base}` — review menuntut branch kerja taskdir, bukan base_branch")
    mb = git(top, "merge-base", base, "HEAD").strip()
    head = git(top, "rev-parse", "HEAD").strip()
    rng = f"{mb}..{head}"
    numstat = git(top, "diff", "--numstat", rng, *pathspec())
    files, add, dele = 0, 0, 0
    for row in numstat.splitlines():
        parts = row.split("\t")
        if len(parts) < 3:
            continue
        files += 1
        add += int(parts[0]) if parts[0].isdigit() else 0
        dele += int(parts[1]) if parts[1].isdigit() else 0
    stat = git(top, "diff", "--stat=120", rng, *pathspec())
    diff = git(top, "diff", "-U3", "--no-color", rng, *pathspec())
    header = [
        "# review-diff (B13) — dibuat architect untuk code-reviewer; jangan disunting",
        f"range: {rng}",
        f"head: {head}",
        f"base_branch: {base}",
        f"branch: {branch}",
        "dikecualikan: " + ", ".join(f"{d}/" for d in EXCLUDE),
        f"berkas: {files} · +{add}/-{dele} baris",
        "",
        "## stat",
        stat.rstrip("\n") or "(kosong)",
        "",
        "## diff",
    ]
    out = td / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(header) + "\n" + diff, encoding="utf-8")
    return {"status": "PASS", "file": f"{taskdir.rstrip('/')}/{OUT_REL}", "range": rng, "head": head,
            "merge_base": mb, "files": files, "added": add, "deleted": dele}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--taskdir", required=True, help="backenddev/docs/<YYMMDDhhmm>-<slug>")
    ap.add_argument("--base-branch", required=True, help="Field `base_branch` profil backend")
    ap.add_argument("--root", default=".", help="Root repositori")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        r = build(Path(a.root), a.taskdir.rstrip("/"), a.base_branch)
    except Fail as e:
        if a.json:
            print(json.dumps({"status": "FAIL", "code": e.code, "reason": str(e)}, ensure_ascii=False))
        else:
            print(f"REVIEW-DIFF FAIL: {e}")
        return e.code
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(f"REVIEW-DIFF PASS: {r['file']} · {r['merge_base'][:7]}..{r['head'][:7]} · {r['files']} berkas · "
              f"+{r['added']}/-{r['deleted']} baris")
    return 0


if __name__ == "__main__":
    sys.exit(main())
