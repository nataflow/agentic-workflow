#!/usr/bin/env python3
"""Kunci rencana quickdev: sidik Section 1–5, blok `## Execution Status`, dan commit dasar.

- `lock`    DRAFT → APPROVED: tulis `Approved-At`, `Approval`, `Plan-Hash`, `Profile`.
- `verify`  APPROVED dan sidik Section 1–5 sekarang = `Plan-Hash` (checkbox dinormalkan).
- `start`   vonis mode eksekusi (awal | resume | remediasi | manual | selesai); tulis blok
            `## Execution Status` (IN_PROGRESS + Base-Commit) bila belum ada.
- `close`   tulis status terminal execute ke blok (COMPLETED | BLOCKED | VERIFICATION_MANUAL_REQUIRED);
            dari IN_PROGRESS, atau BLOCKED dari VERIFICATION_MANUAL_REQUIRED (verifikasi manual gagal).
- `confirm` VERIFICATION_MANUAL_REQUIRED → COMPLETED (manual) dengan jawaban user apa adanya.
- `status`  ringkasan untuk execute/review (`--json`).
- `unlock`  APPROVED → DRAFT untuk revisi atas permintaan user; blok eksekusi dipertahankan.

Metadata rencana adalah baris polos `Kunci: nilai` di antara H1 dan `## 1.`. Sidik mencakup
`## 1.` sampai sebelum `## Execution Status`: CRLF → LF, spasi ujung baris dibuang, `- [x]` dihitung
sebagai `- [ ]`. Checkbox dan blok penutup boleh berubah; teks Section 1–5 tidak.

Zero external dependencies (Python Standard Library only).
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

EXEC_H2 = "## Execution Status"
STEP = re.compile(r"^\s*- \[([ xX])\]\s*(.*)$")
META = re.compile(r"^([A-Z][A-Za-z-]+): ?(.*)$")
ITEM = re.compile(r"^- ([A-Z][A-Za-z0-9-]+): ?(.*)$")
REMEDIATION_CAP = 2


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def quote(v: str) -> str:
    return '"' + " ".join(v.replace('"', "'").split())[:300] + '"'


def head_commit(cwd: Path) -> str:
    """SHA HEAD, atau `none` di repo tanpa commit (review lalu memakai tree kosong, D8)."""
    try:
        r = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--verify", "-q", "HEAD"],
                           capture_output=True, text=True)
    except OSError:
        return "none"
    return r.stdout.strip() or "none"


class Plan:
    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")

    def _first(self, pred) -> int:
        return next((i for i, l in enumerate(self.lines) if pred(l)), len(self.lines))

    @property
    def body_start(self) -> int:          # heading `## 1.` pertama
        return self._first(lambda l: l.startswith("## 1."))

    @property
    def exec_start(self) -> int:
        return self._first(lambda l: l.strip() == EXEC_H2)

    def meta(self) -> dict:
        return {m.group(1): m.group(2) for m in (META.match(l) for l in self.lines[:self.body_start]) if m}

    def block(self) -> dict:
        return {m.group(1): m.group(2) for m in (ITEM.match(l) for l in self.lines[self.exec_start + 1:]) if m}

    def steps(self) -> list:
        s3 = self._first(lambda l: l.startswith("## 3."))
        end = next((i for i in range(s3 + 1, len(self.lines)) if self.lines[i].startswith("## ")), len(self.lines))
        return [(m.group(1) != " ", m.group(2)) for m in (STEP.match(l) for l in self.lines[s3 + 1:end]) if m]

    def digest(self) -> str:
        region = self.lines[self.body_start:self.exec_start]
        norm = [STEP.sub(lambda m: m.group(0).replace(f"[{m.group(1)}]", "[ ]", 1), l).rstrip() for l in region]
        return "sha256:" + hashlib.sha256("\n".join(norm).strip().encode("utf-8")).hexdigest()

    def set_meta(self, **kv: str) -> None:
        for key, val in kv.items():
            key = key.replace("_", "-")
            idx = next((i for i in range(self.body_start) if self.lines[i].startswith(f"{key}:")), None)
            if idx is None:
                last = max((i for i in range(self.body_start) if META.match(self.lines[i])), default=0)
                self.lines.insert(last + 1, f"{key}: {val}")
            else:
                self.lines[idx] = f"{key}: {val}"

    def set_block(self, **kv: str) -> None:
        while self.lines and not self.lines[-1].strip():
            self.lines.pop()
        if self.exec_start == len(self.lines):
            self.lines += ["", EXEC_H2]
        for key, val in kv.items():
            key = key.replace("_", "-")
            idx = next((i for i in range(self.exec_start + 1, len(self.lines))
                        if self.lines[i].startswith(f"- {key}:")), None)
            if idx is None:
                self.lines.append(f"- {key}: {val}")
            else:
                self.lines[idx] = f"- {key}: {val}"

    def save(self) -> None:
        self.path.write_text("\n".join(self.lines).rstrip("\n") + "\n", encoding="utf-8")


def fail(msg: str) -> int:
    print(msg)
    return 1


def cmd_lock(p: Plan, a) -> int:
    if p.meta().get("Status") != "DRAFT":
        return fail(f"LOCK FAIL: Status `{p.meta().get('Status', '-')}` bukan DRAFT")
    if not a.answer.strip():
        return fail("LOCK FAIL: jawaban user kosong")
    if not p.steps():
        return fail("LOCK FAIL: Section 3 tanpa langkah checkbox `- [ ]`")
    p.set_meta(Status="APPROVED", Approved_At=now(), Approval=quote(a.answer), Plan_Hash=p.digest(),
               Profile=a.profile)
    p.save()
    print(f"LOCK PASS: {p.path} APPROVED @{p.digest()[7:19]}")
    return 0


def cmd_verify(p: Plan, a) -> int:
    m = p.meta()
    if m.get("Status") != "APPROVED":
        return fail(f"VERIFY FAIL: Status `{m.get('Status', '-')}` bukan APPROVED — selesaikan approval di quickdev:plan")
    if not m.get("Plan-Hash", "").startswith("sha256:"):
        return fail("VERIFY FAIL: rencana APPROVED tanpa `Plan-Hash` (format lama atau ditulis tangan) — "
                    "`unlock` lalu minta user menyetujui ulang di quickdev:plan (`lock`)")
    if m["Plan-Hash"] != p.digest():
        return fail(f"VERIFY FAIL: Section 1–5 berubah sesudah APPROVED (tercatat {m['Plan-Hash'][7:19]}, "
                    f"sekarang {p.digest()[7:19]}) — pulihkan teksnya, atau `unlock` lalu approval ulang di quickdev:plan")
    print(f"VERIFY PASS: {p.path} @{p.digest()[7:19]}")
    return 0


def cmd_start(p: Plan, a) -> int:
    if cmd_verify(p, a):
        return 1
    b, steps = p.block(), p.steps()
    done = sum(1 for ok, _ in steps if ok)
    st = b.get("Status", "")
    rnd = int(b.get("Remediation-Round", "0") or 0)
    if a.findings:
        if not st.startswith("COMPLETED"):
            return fail(f"START FAIL: remediasi menuntut Status COMPLETED, tercatat `{st or '-'}`")
        if rnd >= REMEDIATION_CAP:
            return fail(f"START FAIL: plafon {REMEDIATION_CAP} putaran remediasi habis — serahkan temuan ke user")
        if not (a.findings_text or "").strip():
            return fail("START FAIL: remediasi tanpa `--findings-text` — temuan wajib tercatat sebelum kode diubah")
        mode = "remediasi"
        p.set_block(Status="IN_PROGRESS", Remediation_Round=str(rnd + 1), Timestamp=now(),
                    **{f"Findings_{rnd + 1}": quote(a.findings_text)})
    elif st == "VERIFICATION_MANUAL_REQUIRED":
        mode = "manual"
    elif st.startswith("COMPLETED"):
        mode = "selesai"
    elif st in ("IN_PROGRESS", "BLOCKED") or done:
        mode = "resume"
        if not b.get("Base-Commit"):
            p.set_block(Base_Commit=head_commit(p.path.parent), Base_Note="tidak tercatat sebelum sesi putus")
        p.set_block(Status="IN_PROGRESS", Timestamp=now())
    else:
        mode = "awal"
        p.set_block(Status="IN_PROGRESS", Base_Commit=head_commit(p.path.parent), Remediation_Round="0",
                    Timestamp=now())
    p.save()
    nxt = next((t for ok, t in steps if not ok), "-")
    print(f"START PASS: mode={mode} · langkah {done}/{len(steps)} · berikutnya: {nxt} · "
          f"base={p.block().get('Base-Commit', '-')[:12]}")
    return 0


def cmd_close(p: Plan, a) -> int:
    if cmd_verify(p, a):
        return 1
    st = p.block().get("Status")
    manual_gagal = st == "VERIFICATION_MANUAL_REQUIRED" and a.status == "BLOCKED"
    if st != "IN_PROGRESS" and not manual_gagal:
        return fail(f"CLOSE FAIL: blok `{EXEC_H2}` bukan IN_PROGRESS — jalankan `start` dulu")
    if a.status == "COMPLETED" and any(not ok for ok, _ in p.steps()):
        return fail("CLOSE FAIL: COMPLETED dengan langkah `- [ ]` tersisa")
    if a.status == "BLOCKED" and not a.blocked_step.strip():
        return fail("CLOSE FAIL: BLOCKED tanpa `--blocked-step`")
    p.set_block(Status=a.status, Verification=quote(a.verification), Blocked_Step=a.blocked_step or "-",
                Timestamp=now())
    p.save()
    print(f"CLOSE PASS: {a.status}")
    return 0


def cmd_confirm(p: Plan, a) -> int:
    if p.block().get("Status") != "VERIFICATION_MANUAL_REQUIRED":
        return fail("CONFIRM FAIL: blok bukan VERIFICATION_MANUAL_REQUIRED")
    if not a.answer.strip():
        return fail("CONFIRM FAIL: jawaban user kosong")
    p.set_block(Status="COMPLETED (manual)", Manual_Confirmation=quote(a.answer), Timestamp=now())
    p.save()
    print("CONFIRM PASS: COMPLETED (manual)")
    return 0


def cmd_unlock(p: Plan, a) -> int:
    if p.meta().get("Status") != "APPROVED":
        return fail("UNLOCK FAIL: bukan APPROVED")
    if not a.reason.strip():
        return fail("UNLOCK FAIL: alasan kosong")
    p.set_meta(Status="DRAFT", Plan_Hash="-", Unlock_Reason=quote(a.reason))
    p.save()
    print("UNLOCK PASS: DRAFT — blok Execution Status dipertahankan")
    return 0


def cmd_status(p: Plan, a) -> int:
    m, b, steps = p.meta(), p.block(), p.steps()
    out = {"status": m.get("Status", "-"), "hash_ok": m.get("Plan-Hash") == p.digest(),
           "profile": m.get("Profile", "-"), "gates": m.get("Gates", "-"),
           "steps_done": sum(ok for ok, _ in steps), "steps_total": len(steps),
           "next_step": next((t for ok, t in steps if not ok), "-"),
           "remediation_round": int(b.get("Remediation-Round", "0") or 0),
           "remediation_cap": REMEDIATION_CAP, "execution": b}
    print(json.dumps(out, ensure_ascii=False, indent=2) if a.json else
          f"STATUS: {out['status']} · hash {'ok' if out['hash_ok'] else 'DRIFT'} · langkah "
          f"{out['steps_done']}/{out['steps_total']} · eksekusi {b.get('Status', '-')} · base {b.get('Base-Commit', '-')}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Kunci rencana quickdev")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("lock", "verify", "start", "close", "confirm", "status", "unlock"):
        s = sub.add_parser(name)
        s.add_argument("--plan", required=True)
        if name in ("lock", "confirm"):
            s.add_argument("--answer", required=True)
        if name == "lock":
            s.add_argument("--profile", default="repo-profile.md")
        if name == "start":
            s.add_argument("--findings", action="store_true", help="putaran remediasi dari review CHANGES_REQUIRED")
            s.add_argument("--findings-text", default="", help="temuan ringkas yang dicatat ke blok (Findings-<n>)")
        if name == "close":
            s.add_argument("--status", required=True, choices=("COMPLETED", "BLOCKED", "VERIFICATION_MANUAL_REQUIRED"))
            s.add_argument("--verification", required=True)
            s.add_argument("--blocked-step", default="")
        if name == "unlock":
            s.add_argument("--reason", required=True)
        if name == "status":
            s.add_argument("--json", action="store_true")
    a = ap.parse_args()
    path = Path(a.plan)
    if not path.is_file():
        if getattr(a, "json", False):
            print(json.dumps({"status": "FAIL", "error": f"{path} tidak ada"}))
            sys.exit(1)
        sys.exit(f"FAIL: {path} tidak ada")
    sys.exit(globals()[f"cmd_{a.cmd}"](Plan(path), a))


if __name__ == "__main__":
    main()
