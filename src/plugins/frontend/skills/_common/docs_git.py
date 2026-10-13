#!/usr/bin/env python3
"""Dokumen taskdir di luar git (Langkah 24): `<prefix>/docs/` diabaikan git dan tidak pernah di-commit.

Dokumen taskdir (`backenddev/docs/<taskdir>/`, `frontenddev/docs/<taskdir>/`) hidup di disk dan dicerminkan ke
nataflow; riwayat git repo hanya memuat kode, profil, dan dokumen tingkat repo. Skrip ini pemilik tunggal
penanda ignore-nya dan migrasi repo yang sudah meng-commit dokumen taskdir.

Subperintah:

- `status`  — `<prefix>/docs/` diabaikan git atau belum, berkas yang masih ter-track, taskdir era git yang masih
              terbuka, dan ada tidaknya config sinkron nataflow. Read-only.
- `ensure`  — tulis `<prefix>/docs/.gitignore` berisi `*` bila `<prefix>/docs/` belum diabaikan (24 K3). Berkas itu
              ikut mengabaikan dirinya sendiri, sehingga tidak pernah muncul di `git status` maupun di commit;
              `.gitignore` akar repo tidak disentuh. Idempoten; di luar repo git tidak menulis apa pun.
- `migrate` — sekali jalan untuk repo yang sudah meng-commit dokumen taskdir (24 K4): `git rm -r --cached` atas
              `<prefix>/docs`, lalu satu commit yang hanya berisi penghapusan dari index, sesudah jawaban eksplisit
              user (`--answer -`, dibaca dari stdin). Berkasnya tetap di disk.

Taskdir era git yang terbuka: ber-`TASK.md`, tanpa `REPORT.md`, `status` `ACTIVE` atau kosong, dan tanpa
`base_commit`. Taskdir seperti itu tidak dapat dilanjutkan sesudah migrasi (gerbang menuntut `base_commit`),
sehingga `migrate` menolaknya kecuali user menerimanya lewat `--terima-terbuka`.

`--plugin backend|frontend` memilih prefix; default-nya plugin tempat salinan ini berada. Exit: 0 = PASS atau WARN,
1 = FAIL, 2 = argumen salah. `--json` selalu JSON, termasuk di jalur gagal.

Pustaka untuk gerbang: `docs_prefix`, `docs_ignored`, `ensure_ignored`, `tracked_docs`, `open_legacy_taskdirs`,
`head_sha`, `base_commit_problem` (24 G3). Fungsinya menerima `prefix` secara eksplisit: modul ini bernama sama di
dua plugin, jadi salinan yang termuat lebih dulu tidak boleh menentukan prefix plugin lain.

Salinan identik di skills/_common/ backend dan frontend. Hanya pustaka standar.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PREFIXES = {"backend": "backenddev", "frontend": "frontenddev"}
IGNORE_TEXT = (
    "# Ditulis `docs_git.py ensure` (Langkah 24): dokumen taskdir hidup di disk dan dicerminkan ke nataflow,\n"
    "# tidak pernah di-commit. Pola `*` ikut mengabaikan berkas ini sendiri; jangan di-commit.\n"
    "*\n"
)
NATAFLOW_CONFIG = ".claude/nataflow.json"
TASKDIR_NAME = re.compile(r"^\d{10}-[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_FULL = re.compile(r"^[0-9a-f]{40}$")
OPEN_STATUSES = ("", "ACTIVE")
GIT_OPERATIONS = (("MERGE_HEAD", "merge"), ("rebase-merge", "rebase"), ("rebase-apply", "rebase/am"),
                  ("CHERRY_PICK_HEAD", "cherry-pick"), ("REVERT_HEAD", "revert"))


class DocsGitError(Exception):
    pass


def docs_prefix(plugin: str) -> str:
    """`backend` → `backenddev`, `frontend` → `frontenddev`."""
    if plugin not in PREFIXES:
        raise DocsGitError(f"plugin `{plugin}` tidak dikenal (backend | frontend)")
    return PREFIXES[plugin]


def docs_rel(prefix: str) -> str:
    return f"{prefix}/docs"


def _git(root: Path, *args: str, stdin: str = "") -> Tuple[int, str]:
    try:
        proc = subprocess.run(["git", *args], cwd=root, input=stdin, capture_output=True, text=True)
    except OSError as exc:
        return 127, f"git tidak dapat dijalankan: {exc.strerror or exc}"
    return proc.returncode, (proc.stdout if proc.returncode == 0 else (proc.stderr or proc.stdout)).strip()


def repo_root(start: Path) -> Tuple[Path, bool]:
    """(root worktree git, True), atau (`start`, False) di luar repo git."""
    code, out = _git(start, "rev-parse", "--show-toplevel")
    return (Path(out).resolve(), True) if code == 0 and out else (start.resolve(), False)


def head_sha(root: Path) -> str:
    """Sha penuh `HEAD`, atau kosong di repo tanpa commit."""
    code, out = _git(root, "rev-parse", "--verify", "-q", "HEAD")
    return out if code == 0 and SHA_FULL.match(out) else ""


def docs_ignored(root: Path, prefix: str) -> bool:
    """Path baru di bawah `<prefix>/docs/` diabaikan git (path probe untracked, jadi berkas ter-track tak menyesatkan)."""
    probe = f"{docs_rel(prefix)}/0000000000-probe/TASK.md"
    return _git(root, "check-ignore", "-q", "--", probe)[0] == 0


def ensure_ignored(root: Path, prefix: str) -> Tuple[bool, str]:
    """(berkas ignore ditulis, masalah). Sudah diabaikan → (False, ""). Masalah = tetap tidak diabaikan sesudah ditulis."""
    if docs_ignored(root, prefix):
        return False, ""
    target = root / docs_rel(prefix) / ".gitignore"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_bytes().decode("utf-8", "replace") if target.is_file() else ""
    if existing != IGNORE_TEXT:
        target.write_bytes(IGNORE_TEXT.encode("utf-8"))
    if not docs_ignored(root, prefix):
        return True, (f"`{docs_rel(prefix)}/` tetap tidak diabaikan sesudah `{docs_rel(prefix)}/.gitignore` ditulis — "
                      "periksa berkas itu dan `.gitignore` di bawahnya")
    return True, ""


def tracked_docs(root: Path, prefix: str) -> List[str]:
    """Berkas di bawah `<prefix>/docs/` yang masih ter-track git."""
    code, out = _git(root, "ls-files", "-z", "--", docs_rel(prefix))
    return [p for p in out.split("\0") if p] if code == 0 else []


def _frontmatter(text: str) -> Dict[str, str]:
    """Skalar blok `---` pertama; cukup untuk `status` dan `base_commit`."""
    text = text.lstrip("﻿").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 3)
    fields: Dict[str, str] = {}
    for line in text[4:end if end != -1 else len(text)].splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() and not line[:1].isspace():
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def open_legacy_taskdirs(root: Path, prefix: str) -> List[Dict[str, str]]:
    """Taskdir era git yang masih terbuka: `[{taskdir, reason}]`, terurut."""
    base = root / docs_rel(prefix)
    found: List[Dict[str, str]] = []
    if not base.is_dir():
        return found
    for d in sorted(p for p in base.iterdir() if p.is_dir() and TASKDIR_NAME.match(p.name)):
        task = d / "TASK.md"
        if not task.is_file() or (d / "REPORT.md").is_file():
            continue
        rel = f"{docs_rel(prefix)}/{d.name}"
        try:
            fm = _frontmatter(task.read_bytes().decode("utf-8"))
        except UnicodeDecodeError:
            found.append({"taskdir": rel, "reason": "TASK.md bukan UTF-8 — keadaannya tidak terbaca"})
            continue
        if fm.get("base_commit") or fm.get("status", "").upper() not in OPEN_STATUSES:
            continue
        found.append({"taskdir": rel, "reason": f"status `{fm.get('status') or '(kosong)'}` tanpa REPORT.md"})
    return found


def base_commit_problem(root: Path, value: Optional[str]) -> str:
    """Kosong bila `base_commit` sah: sha penuh, ada di repo ini, dan leluhur `HEAD` (24 G3)."""
    value = (value or "").strip()
    if not value:
        return "`base_commit` kosong — akar rantai belum dikunci"
    if not SHA_FULL.match(value):
        return f"`base_commit: {value}` bukan sha penuh 40 hex"
    if _git(root, "cat-file", "-e", f"{value}^{{commit}}")[0] != 0:
        return (f"`base_commit` {value[:7]} tidak ada di repo ini — taskdir dibawa dari clone lain atau riwayat "
                "ditulis ulang")
    if _git(root, "merge-base", "--is-ancestor", value, "HEAD")[0] != 0:
        return (f"`base_commit` {value[:7]} bukan leluhur `HEAD` — branch kerja tidak lagi memuat titik awal rantai; "
                "checkout branch taskdir ini")
    return ""


def git_operation(root: Path) -> str:
    """Nama operasi git yang sedang berjalan (merge/rebase/…), atau kosong."""
    for marker, name in GIT_OPERATIONS:
        code, out = _git(root, "rev-parse", "--git-path", marker)
        if code == 0 and out and (root / out).exists():
            return name
    return ""


# -- CLI ------------------------------------------------------------------------------------


def _status(root: Path, is_git: bool, prefix: str) -> Dict[str, object]:
    rel = docs_rel(prefix)
    data: Dict[str, object] = {"prefix": prefix, "docs": rel, "git": is_git,
                               "nataflow_config": (root / NATAFLOW_CONFIG).is_file()}
    problems: List[Dict[str, str]] = []
    warnings: List[str] = []
    if not data["nataflow_config"]:
        warnings.append(f"`{NATAFLOW_CONFIG}` tidak ada — dokumen taskdir hanya tersimpan di disk ini, tanpa cermin "
                        "nataflow")
    legacy = open_legacy_taskdirs(root, prefix)
    data["open_legacy"] = legacy
    if not is_git:
        data.update(ignored=False, ignore_file=(root / rel / ".gitignore").is_file(), tracked=[], tracked_total=0)
        warnings.append("bukan repo git — tidak ada yang perlu diabaikan; dokumen tetap di disk")
    else:
        tracked = tracked_docs(root, prefix)
        data.update(ignored=docs_ignored(root, prefix), ignore_file=(root / rel / ".gitignore").is_file(),
                    tracked=tracked[:50], tracked_total=len(tracked))
        if tracked:
            problems.append({"route": "MIGRASI",
                             "summary": f"{len(tracked)} berkas di bawah `{rel}/` masih ter-track git — jalankan "
                                        f"`docs_git.py migrate` sesudah persetujuan user"})
        elif not data["ignored"]:
            problems.append({"route": "ENSURE", "summary": f"`{rel}/` belum diabaikan git — jalankan `docs_git.py ensure`"})
    data["problems"], data["warnings"] = problems, warnings
    data["status"] = "FAIL" if problems else ("WARN" if warnings else "PASS")
    return data


def _ensure(root: Path, is_git: bool, prefix: str) -> Dict[str, object]:
    rel = docs_rel(prefix)
    if not is_git:
        return {"status": "PASS", "prefix": prefix, "written": False, "note": "bukan repo git — tidak ada yang ditulis"}
    written, problem = ensure_ignored(root, prefix)
    if problem:
        return {"status": "FAIL", "prefix": prefix, "written": written, "error": problem}
    note = f"`{rel}/.gitignore` ditulis" if written else f"`{rel}/` sudah diabaikan git"
    tracked = tracked_docs(root, prefix)
    data: Dict[str, object] = {"status": "PASS", "prefix": prefix, "written": written, "note": note,
                               "tracked_total": len(tracked)}
    if tracked:
        data["status"] = "WARN"
        data["warning"] = (f"{len(tracked)} berkas di bawah `{rel}/` masih ter-track — `.gitignore` tidak berlaku atas "
                           "berkas ter-track; jalankan `docs_git.py migrate`")
    return data


def _read_answer(value: str) -> str:
    answer = sys.stdin.read() if value == "-" else value
    answer = answer.strip()
    if not answer:
        raise DocsGitError("`--answer` kosong — migrasi menuntut jawaban eksplisit user dari AskUserQuestion")
    if "\n" in answer or "\r" in answer:
        raise DocsGitError("`--answer` memuat baris baru — tulis satu baris jawaban user apa adanya")
    return answer


def _migrate(root: Path, is_git: bool, prefix: str, answer: str, accept_open: bool) -> Dict[str, object]:
    rel = docs_rel(prefix)
    if not is_git:
        raise DocsGitError("bukan repo git — tidak ada yang dimigrasi")
    operation = git_operation(root)
    if operation:
        raise DocsGitError(f"operasi git `{operation}` sedang berjalan — selesaikan atau batalkan dulu")
    tracked = tracked_docs(root, prefix)
    if not tracked:
        written, problem = ensure_ignored(root, prefix)
        if problem:
            raise DocsGitError(problem)
        return {"status": "PASS", "prefix": prefix, "removed": 0, "commit": "",
                "note": f"tidak ada berkas ter-track di bawah `{rel}/`" + (f"; `{rel}/.gitignore` ditulis" if written else "")}
    legacy = open_legacy_taskdirs(root, prefix)
    if legacy and not accept_open:
        listed = "; ".join(f"{t['taskdir']} ({t['reason']})" for t in legacy)
        raise DocsGitError(f"{len(legacy)} taskdir era git masih terbuka: {listed} — selesaikan rantainya dengan versi "
                           "plugin sebelumnya, atau ulangi dengan `--terima-terbuka` bila user menerima taskdir itu tidak "
                           "dapat dilanjutkan")
    if _git(root, "diff", "--cached", "--quiet")[0] != 0:
        raise DocsGitError("index sudah memuat perubahan ter-stage lain — commit atau `git restore --staged` dulu, supaya "
                           "commit migrasi hanya berisi penghapusan dokumen taskdir dari index")
    code, out = _git(root, "rm", "-r", "--cached", "-q", "--", rel)
    if code != 0:
        raise DocsGitError(f"`git rm --cached {rel}` gagal: {out.splitlines()[0] if out else code}")
    written, problem = ensure_ignored(root, prefix)
    if problem:
        _git(root, "reset", "-q", "--", rel)
        raise DocsGitError(problem)
    body = (f"Dokumen taskdir hidup di disk dan dicerminkan ke nataflow (Langkah 24); berkasnya tetap di disk.\n\n"
            f"Persetujuan user: {answer}")
    code, out = _git(root, "commit", "-q", "-m", f"chore: lepas {rel} dari git", "-m", body)
    if code != 0:
        _git(root, "reset", "-q", "--", rel)
        raise DocsGitError(f"commit migrasi gagal, index dipulihkan: {out.splitlines()[0] if out else code}")
    left = tracked_docs(root, prefix)
    if left:
        raise DocsGitError(f"{len(left)} berkas masih ter-track sesudah commit migrasi: {', '.join(left[:5])}")
    return {"status": "PASS", "prefix": prefix, "removed": len(tracked), "commit": head_sha(root)[:7],
            "ignore_written": written, "open_legacy_accepted": [t["taskdir"] for t in legacy]}


def _print(cmd: str, data: Dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    head = f"DOCS_GIT {cmd.upper()} — {data['status']}"
    if data.get("error"):
        print(f"{head} · {data['error']}")
    elif cmd == "status":
        state = "diabaikan git" if data.get("ignored") else "belum diabaikan git"
        print(f"{head} · `{data['docs']}/` {state} · {data.get('tracked_total', 0)} berkas ter-track · "
              f"{len(data.get('open_legacy') or [])} taskdir era git terbuka")
        for p in data.get("problems") or []:
            print(f"- FAIL [{p['route']}]: {p['summary']}")
        for t in data.get("open_legacy") or []:
            print(f"- terbuka: {t['taskdir']} — {t['reason']}")
        for w in data.get("warnings") or []:
            print(f"- WARN: {w}")
    elif cmd == "ensure":
        print(f"{head} · {data.get('note')}")
        if data.get("warning"):
            print(f"- WARN: {data['warning']}")
    else:
        if data.get("commit"):
            print(f"{head} · {data['removed']} berkas dilepas dari index @ {data['commit']}")
        else:
            print(f"{head} · {data.get('note')}")
        for t in data.get("open_legacy_accepted") or []:
            print(f"- diterima terbuka: {t}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dokumen taskdir di luar git (Langkah 24)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("status", "ensure", "migrate"):
        p = sub.add_parser(name)
        p.add_argument("--plugin", choices=sorted(PREFIXES), default=None)
        p.add_argument("--root", default=None)
        p.add_argument("--json", action="store_true")
        if name == "migrate":
            p.add_argument("--answer", required=True, help="jawaban user apa adanya; `-` = baca dari stdin")
            p.add_argument("--terima-terbuka", action="store_true", dest="accept_open",
                           help="user menerima taskdir era git yang masih terbuka tidak dapat dilanjutkan")
    args = parser.parse_args()
    try:
        prefix = docs_prefix(args.plugin or Path(__file__).resolve().parents[2].name)
        start = Path(args.root) if args.root else Path.cwd()
        if not start.is_dir():
            raise DocsGitError(f"`--root {start}` bukan direktori")
        root, is_git = repo_root(start)
        if args.cmd == "status":
            data = _status(root, is_git, prefix)
        elif args.cmd == "ensure":
            data = _ensure(root, is_git, prefix)
        else:
            data = _migrate(root, is_git, prefix, _read_answer(args.answer), args.accept_open)
    except (DocsGitError, OSError) as exc:
        data = {"status": "FAIL", "error": str(exc)}
    _print(args.cmd, data, args.json)
    return 1 if data["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
