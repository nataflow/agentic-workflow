#!/usr/bin/env python3
"""Validator berkas audit `frontenddev/reviews/<YYMMDDhhmm>-<slug>.md`.

Berkas audit adalah `finding_source` taskdir perbaikan: ID temuannya dikutip
`TASK.md`, dan baris `> Status:`-nya ditutup `code-reviewer` penutup. Aturannya
tinggal di `templates/audit-template.md` bagian 2; skrip ini menegakkannya.

- `--path <berkas>` — bentuk: frontmatter `AUDIT_REVIEW`, ID `P{n}-{m}` berurutan
  per severity, hitungan `p1/p2/p3` = jumlah temuan, `verdict` turunan, tiap
  temuan ber-`> Status:` sah dan berjangkar `file:baris`. Dijalankan `review`
  sebelum commit `docs(review): audit <slug>`.
- `--only-status-changed` — tambahan: diff berkas terhadap `HEAD` hanya boleh
  mengubah baris `> Status:`. Dijalankan `architect` Phase 4 sebelum
  `finding_source` ikut di-stage — penyuntingan penutup tidak boleh menyentuh
  temuan lain tanpa jejak.

Exit 0 = PASS, 1 = FAIL. Zero external dependencies (Python Standard Library only).
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import find_repo_root, git_ok, split_frontmatter  # noqa: E402
from precondition_lib import cli  # noqa: E402

HEADING = re.compile(r"^### \[P(?P<sev>[123])-(?P<n>\d+)\]\s+\S")
DATE = r"\d{4}-\d{2}-\d{2}"
STATUS = re.compile(rf"^> Status: (?:PLANNED|FIXED {DATE} — lihat \S+|DEFERRED {DATE} — \S.*"
                    rf"|DROPPED {DATE} — \S.*|OBSOLETE {DATE})\s*$")
LOCATION = re.compile(r"^- \*\*Location\*\*: `[^`]+:\d+(?:-\d+)?`")


def check_shape(text: str) -> List[str]:
    problems: List[str] = []
    try:
        fm, body = split_frontmatter(text, strict=True)
    except ValueError as exc:
        return [f"frontmatter: {exc}"]
    if str(fm.get("artifact", "")).strip() != "AUDIT_REVIEW":
        problems.append("frontmatter `artifact` bukan `AUDIT_REVIEW`")
    counts: Dict[str, int] = {}
    for key in ("p1", "p2", "p3"):
        try:
            counts[key] = int(str(fm.get(key, "")).strip())
        except ValueError:
            problems.append(f"frontmatter `{key}` bukan bilangan")
    findings: List[Dict] = []
    for line in body.splitlines():
        m = HEADING.match(line)
        if m:
            findings.append({"sev": m.group("sev"), "n": int(m.group("n")), "id": line[5:line.index("]")],
                             "status": [], "location": False})
        elif findings and line.startswith("> Status:"):
            findings[-1]["status"].append(line)
        elif findings and line.startswith("- **Location**:"):
            findings[-1]["location"] = bool(LOCATION.match(line))
    for sev in "123":
        ns = [f["n"] for f in findings if f["sev"] == sev]
        if ns != list(range(1, len(ns) + 1)):
            problems.append(f"ID P{sev} tidak berurutan dari 1: {', '.join(f'P{sev}-{n}' for n in ns)}")
        key = f"p{sev}"
        if key in counts and counts[key] != len(ns):
            problems.append(f"frontmatter `{key}: {counts[key]}` ≠ {len(ns)} temuan P{sev}")
    for f in findings:
        if len(f["status"]) != 1:
            problems.append(f"[{f['id']}] wajib tepat satu baris `> Status:` (ada {len(f['status'])})")
        elif not STATUS.match(f["status"][0]):
            problems.append(f"[{f['id']}] `{f['status'][0]}` di luar enum PLANNED | FIXED <tgl> — lihat <taskdir> | "
                            "DEFERRED <tgl> — <alasan> | DROPPED <tgl> — <alasan> | OBSOLETE <tgl>")
        if not f["location"]:
            problems.append(f"[{f['id']}] tanpa jangkar `- **Location**: `file:baris``")
    if len(counts) == 3:
        derived = "BLOCKED" if counts["p1"] else "WARNING" if counts["p2"] else "PASS"
        verdict = str(fm.get("verdict", "")).strip()
        if verdict != derived:
            problems.append(f"`verdict: {verdict or '(kosong)'}` ≠ turunan hitungan (`{derived}`)")
    return problems


def check_only_status(root: Path, rel: str) -> List[str]:
    ok, out = git_ok(root, "diff", "-U0", "HEAD", "--", rel)
    if not ok:
        return [f"`git diff HEAD -- {rel}` gagal: {out.strip()[-200:]}"]
    bad = [l for l in out.splitlines()
           if l[:1] in "+-" and not l.startswith(("+++", "---")) and not l[1:].startswith("> Status:")]
    return [f"diff menyentuh baris selain `> Status:`: {l[:120]}" for l in bad[:5]] + \
        ([f"… dan {len(bad) - 5} baris lain"] if len(bad) > 5 else [])


def main() -> None:
    parser = argparse.ArgumentParser(description="Validator berkas audit frontenddev/reviews/")
    parser.add_argument("--path", required=True)
    parser.add_argument("--only-status-changed", action="store_true")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else find_repo_root()
    path = (root / args.path) if not Path(args.path).is_absolute() else Path(args.path)
    if not path.is_file():
        print(f"AUDIT VALIDATION: [FAIL] `{args.path}` tidak ada")
        sys.exit(1)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(f"AUDIT VALIDATION: [FAIL] `{args.path}` bukan UTF-8 ({exc.reason} @ byte {exc.start}) — "
              f"pulihkan dari git; jangan menebak isinya")
        sys.exit(1)
    problems = check_shape(text)
    if args.only_status_changed:
        problems += check_only_status(root, str(path.resolve().relative_to(root)))
    if problems:
        print(f"AUDIT VALIDATION: [FAIL] {args.path} ({len(problems)} cacat)")
        print("\n".join(f"- {p}" for p in problems))
        sys.exit(1)
    print(f"AUDIT VALIDATION: [PASS] {args.path}")


if __name__ == "__main__":
    sys.exit(cli(main))
