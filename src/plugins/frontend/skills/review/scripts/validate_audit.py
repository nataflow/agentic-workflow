#!/usr/bin/env python3
"""Validator berkas audit `frontenddev/reviews/<YYMMDDhhmm>-<slug>.md`.

Berkas audit adalah `finding_source` taskdir perbaikan: ID temuannya dikutip
`TASK.md`, dan baris `> Status:`-nya ditutup `code-reviewer` penutup. Aturannya
tinggal di `templates/audit-template.md` bagian 2; skrip ini menegakkannya.

- `--path <berkas>` — bentuk: frontmatter `AUDIT_REVIEW`, ID `P{n}-{m}` berurutan
  per severity, hitungan `p1/p2/p3` = jumlah temuan, `verdict` turunan, `## Summary`
  menyalin verdict dan hitungan, tiap temuan ber-judul, ber-`> Status:` sah, dan
  berjangkar `file:baris`; heading yang tampak temuan tetapi tak terurai adalah cacat
  (12 J30). Dijalankan `review` sebelum commit `docs(review): audit <slug>`.
- `--only-status-changed` — tambahan: berkas ter-commit di dalam root repo, dan diff
  terhadap `HEAD` hanya boleh mengubah baris `> Status:` (12 J37). Dijalankan
  `architect` Phase 4 sebelum `finding_source` ikut di-stage — penyuntingan penutup
  tidak boleh menyentuh temuan lain tanpa jejak.

Exit 0 = PASS, 1 = FAIL. Zero external dependencies (Python Standard Library only).
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import find_repo_root, git_ok, inside_root, section_lines, split_frontmatter  # noqa: E402
from precondition_lib import cli  # noqa: E402

HEADING = re.compile(r"^### \[P(?P<sev>[123])-(?P<n>\d+)\]\s+\S")
DATE = r"\d{4}-\d{2}-\d{2}"
STATUS = re.compile(rf"^> Status: (?:PLANNED|FIXED {DATE} — lihat \S+|DEFERRED {DATE} — \S.*"
                    rf"|DROPPED {DATE} — \S.*|OBSOLETE {DATE})\s*$")
LOCATION = re.compile(r"^- \*\*Location\*\*: `[^`]+:\d+(?:-\d+)?`")
# Heading yang tampak temuan (`###[P1-1]`, `### [p1-1]`, `### [P1-1]` tanpa judul) — wajib terurai `HEADING`.
LOOSE_HEADING = re.compile(r"^#{1,6}\s*\[?\s*[pP]\s*\d+\s*-\s*\d+")


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
        if not m and LOOSE_HEADING.match(line):
            problems.append(f"heading temuan tak terurai (wajib `### [P<n>-<m>] <judul>`): {line.strip()[:80]}")
            continue
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
        problems += summary_problems(body, derived, [len([f for f in findings if f["sev"] == s]) for s in "123"])
    return problems


def summary_problems(body: str, derived: str, n: List[int]) -> List[str]:
    """`## Summary` menyalin verdict turunan dan hitungan temuan badan (12 J30)."""
    lines = [l.strip() for l in section_lines(body, "## Summary")]
    status = [l.split(":", 1)[1].strip() for l in lines if l.startswith("- Overall Status:")]
    total = [l for l in lines if l.startswith("- Total Findings:")]
    want = f"- Total Findings: {sum(n)} ({n[0]} P1, {n[1]} P2, {n[2]} P3)"
    p = []
    if status != [derived]:
        p.append(f"`## Summary` `Overall Status: {', '.join(status) or '(absen)'}` ≠ verdict turunan `{derived}`")
    if total != [want]:
        p.append(f"`## Summary` baris Total Findings wajib `{want}`")
    return p


def check_only_status(root: Path, rel: str) -> List[str]:
    tracked, _ = git_ok(root, "cat-file", "-e", f"HEAD:{rel}")
    if not tracked:
        return [f"`{rel}` belum ter-commit di HEAD — tanpa pembanding, suntingan apa pun lolos; commit "
                "berkas audit (`docs(review): audit <slug>`) sebelum dipakai `finding_source`"]
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
        try:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = ""
        if not rel or not inside_root(root, rel):
            problems.append(f"`{args.path}` di luar root repo `{root}` — `finding_source` wajib berkas repo ini")
        else:
            problems += check_only_status(root, rel)
    if problems:
        print(f"AUDIT VALIDATION: [FAIL] {args.path} ({len(problems)} cacat)")
        print("\n".join(f"- {p}" for p in problems))
        sys.exit(1)
    print(f"AUDIT VALIDATION: [PASS] {args.path}")


if __name__ == "__main__":
    sys.exit(cli(main))
