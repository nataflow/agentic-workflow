#!/usr/bin/env python3
"""Kunci rencana quickdev: sidik Section 1–5, blok `## Execution Status`, dan commit dasar.

- `lock`    DRAFT → APPROVED: tulis `Approved-At`, `Approval`, `Plan-Hash`, `Profile`.
- `verify`  APPROVED dan sidik Section 1–5 sekarang = `Plan-Hash` (checkbox dinormalkan).
- `start`   vonis mode eksekusi (awal | resume | remediasi | manual | selesai); tulis blok
            `## Execution Status` (IN_PROGRESS + Base-Commit) bila belum ada. Mode `awal` menolak tree
            kotor di luar direktori rencana dan profil **sebelum** menulis (13 Q1). Blok terminal dengan
            langkah `[ ]` tersisa (rencana direvisi) atau segel basi (13 Q9/Q14) → `resume`; ronde
            remediasi yang masih `OPEN` → `remediasi` lanjutan (13 Q3).
- `baseline` kunci ringkasan baseline segar (`Baseline`, `Baseline-Commit`); sah hanya di HEAD = Base-Commit
            dengan tree bersih, yaitu sebelum mutasi pertama (13 Q6).
- `close`   tulis status terminal execute ke blok (COMPLETED | BLOCKED | VERIFICATION_MANUAL_REQUIRED);
            dari IN_PROGRESS, atau BLOCKED dari VERIFICATION_MANUAL_REQUIRED (verifikasi manual gagal).
            COMPLETED/VERIFICATION_MANUAL_REQUIRED menyegel `Verified-Hash` (= Plan-Hash) dan `Tree-Hash`.
- `confirm` VERIFICATION_MANUAL_REQUIRED → COMPLETED (manual) dengan jawaban user apa adanya; segel basi → FAIL.
- `status`  ringkasan untuk execute/review (`--json`); `consistent` menilai blok terhadap checklist dan segel.
- `unlock`  APPROVED → DRAFT untuk revisi atas permintaan user; blok eksekusi dipertahankan.
- `sync-payload` argumen tool MCP nataflow untuk rencana yang pernah dikunci (`--plan`) atau profil
            (`--repo-profile`); read-only. Config `.claude/nataflow.json` absen → SKIP sebelum rencana dibaca (15 Q2).

Metadata rencana adalah baris polos `Kunci: nilai` di antara H1 dan `## 1.`. Sidik mencakup
`## 1.` sampai sebelum `## Execution Status`: CRLF → LF, spasi ujung baris dibuang, `- [x]` dihitung
sebagai `- [ ]`. Checkbox dan blok penutup boleh berubah; teks Section 1–5 tidak. Rencana yang dikunci
dengan `Hash-Scope: profile+body` juga menyidik baris `Profile:` (13 Q11); tanpa penanda = rumus lama.
Heading, langkah, dan blok di dalam code fence diabaikan (13 Q7).

Teks bebas (`--answer`, `--reason`, `--verification`, `--findings-text`, `--summary`) bernilai `-` dibaca dari stdin,
satu per panggilan (13 Q4): SKILL mengirimnya lewat heredoc berkutip supaya shell tidak mengekspansi apa pun.

Zero external dependencies (Python Standard Library only).
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import posixpath
import re
import stat
import tempfile
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nataflow_sync as ns  # noqa: E402

EXEC_H2 = "## Execution Status"
STEP = re.compile(r"^\s*- \[([ xX])\]\s*(.*)$")
META = re.compile(r"^([A-Z][A-Za-z-]+): ?(.*)$")
ITEM = re.compile(r"^- ([A-Z][A-Za-z0-9-]+): ?(.*)$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
META_KEYS = ("Status", "Author", "Date", "Profile", "Gates", "Approved-At", "Approval", "Plan-Hash",
             "Hash-Scope", "Unlock-Reason")
SCOPE_V2 = "profile+body"
TEXT_ARGS = ("answer", "reason", "verification", "findings_text", "summary")
DONE_STATES = ("COMPLETED", "VERIFICATION_MANUAL_REQUIRED")      # close yang menyegel verifikasi
MANUAL = "VERIFICATION_MANUAL_REQUIRED"
REMEDIATION_CAP = 2


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def one_line(v: str) -> str:
    return " ".join(v.split())


def quote(v: str, limit: int = 300) -> str:
    return '"' + one_line(v.replace('"', "'"))[:limit] + '"'


def fence_mask(lines: list) -> tuple:
    """(masker per baris: True = di dalam code fence termasuk pagarnya, fence terbuka di akhir berkas)."""
    mask, fence = [], ""
    for line in lines:
        m = FENCE.match(line)
        if not fence:
            if m:
                fence = m.group(1)
            mask.append(bool(m))
            continue
        mask.append(True)
        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
            fence = ""
    return mask, bool(fence)


def git(cwd: Path, *args: str, stdin: str = ""):
    """`CompletedProcess`, atau None bila binari git tidak ada."""
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", input=stdin)
    except OSError:
        return None


def head_commit(cwd: Path) -> str:
    """SHA HEAD, atau `none` di repo tanpa commit (review lalu memakai tree kosong, D8)."""
    r = git(cwd, "rev-parse", "--verify", "-q", "HEAD")
    return (r.stdout.strip() if r else "") or "none"


class Plan:
    def __init__(self, path: Path):
        self.path = path
        self.raw = path.read_text(encoding="utf-8")
        self.lines = self.raw.replace("\r\n", "\n").split("\n")

    def _mask(self) -> list:
        return fence_mask(self.lines)[0]

    def _first(self, pred, start: int = 0) -> int:
        mask = self._mask()
        return next((i for i in range(start, len(self.lines)) if not mask[i] and pred(self.lines[i])),
                    len(self.lines))

    @property
    def unclosed_fence(self) -> bool:
        return fence_mask(self.lines)[1]

    @property
    def body_start(self) -> int:          # heading `## 1.` pertama di luar fence
        return self._first(lambda l: l.startswith("## 1."))

    @property
    def exec_start(self) -> int:
        return self._first(lambda l: l.strip() == EXEC_H2)

    @property
    def exec_end(self) -> int:            # heading `## ` berikutnya sesudah blok, atau akhir berkas
        return self._first(lambda l: l.startswith("## "), self.exec_start + 1)

    def _pairs(self, pattern, lo: int, hi: int) -> list:
        mask = self._mask()
        return [(m.group(1), m.group(2).strip()) for i in range(lo, hi) if not mask[i]
                for m in [pattern.match(self.lines[i])] if m]

    def meta(self) -> dict:
        """Kemunculan pertama, sama dengan `set_meta`; kunci dikenal yang ganda → FAIL (13 Q10)."""
        out = {}
        for key, val in self._pairs(META, 0, self.body_start):
            if key in out and key in META_KEYS:
                raise SystemExit(f"FAIL: kunci metadata `{key}` ganda — disunting tangan; pulihkan dari "
                                 f"riwayat git, dilarang menebak")
            out.setdefault(key, val)
        return out

    def block(self) -> dict:
        out = {}
        for key, val in self._pairs(ITEM, self.exec_start + 1, self.exec_end):
            if key in out:
                raise SystemExit(f"FAIL: kunci `{key}` ganda di blok `{EXEC_H2}` — disunting tangan; "
                                 f"pulihkan dari riwayat git, dilarang menebak")
            out[key] = val
        return out

    def steps(self) -> list:
        s3 = self._first(lambda l: l.startswith("## 3."))
        end = self._first(lambda l: l.startswith("## "), s3 + 1)
        return [(ok != " ", t) for ok, t in self._pairs(STEP, s3 + 1, end)]

    def digest(self, scope: str = "") -> str:
        """Normalisasi tidak berubah sejak 0.4.0 supaya rencana lama tetap lolos `verify` (13 Q7)."""
        region = self.lines[self.body_start:self.exec_start]
        norm = [STEP.sub(lambda m: m.group(0).replace(f"[{m.group(1)}]", "[ ]", 1), l).rstrip() for l in region]
        body = "\n".join(norm).strip()
        if scope == SCOPE_V2:
            body = f"Profile: {self.meta().get('Profile', '')}\n{body}"
        return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()

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
        if self.exec_start == len(self.lines):
            while self.lines and not self.lines[-1].strip():
                self.lines.pop()
            self.lines += ["", EXEC_H2]
        for key, val in kv.items():
            key = key.replace("_", "-")
            lo, hi = self.exec_start + 1, self.exec_end
            idx = next((i for i in range(lo, hi) if self.lines[i].startswith(f"- {key}:")), None)
            if idx is None:
                idx = hi                  # sisip di akhir seksi blok, sebelum baris kosong penutupnya
                while idx > lo and not self.lines[idx - 1].strip():
                    idx -= 1
                self.lines.insert(idx, f"- {key}: {val}")
            else:
                self.lines[idx] = f"- {key}: {val}"

    def save(self) -> None:
        """Tulis atomik (berkas sementara + `os.replace`): sesi yang putus di tengah tulis tidak
        meninggalkan rencana setengah tertulis. Mode berkas asli dipertahankan; isi yang tidak berubah
        tidak ditulis ulang (13 Q8)."""
        content = "\n".join(self.lines).rstrip("\n") + "\n"
        if content == self.raw:
            return
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), prefix=f".{self.path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            os.chmod(tmp, stat.S_IMODE(os.stat(str(self.path)).st_mode))
            os.replace(tmp, str(self.path))
            self.raw = content
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise


def fail(msg: str) -> int:
    print(msg)
    return 1


def remediation_round(b: dict) -> int:
    """`Remediation-Round` blok; nilai rusak → SystemExit rapi (field ini hanya ditulis skrip)."""
    raw = (b.get("Remediation-Round") or "0").strip()
    if not raw.isdigit():
        raise SystemExit(f"FAIL: `Remediation-Round: {raw}` bukan bilangan — blok `{EXEC_H2}` disunting tangan; "
                         f"pulihkan dari riwayat git, dilarang menebak")
    return int(raw)


# ------------------------------------------------------------------ state repo (13 Q1, Q6, Q9)

def repo_top(p: "Plan") -> Optional[Path]:
    r = git(p.path.parent, "rev-parse", "--show-toplevel")
    top = r.stdout.strip() if r is not None and r.returncode == 0 else ""
    return Path(top) if top else None


def gate_paths(p: "Plan", top: Path) -> list:
    """Artefak gate relatif root repo: direktori rencana (berkas rencana bila di root) dan `Profile:`."""
    out = []
    try:
        rel = p.path.resolve().relative_to(top.resolve()).as_posix()
    except ValueError:
        rel = ""
    if rel:
        out.append(posixpath.dirname(rel) or rel)
    prof = posixpath.normpath(p.meta().get("Profile") or "repo-profile.md")
    if not prof.startswith("..") and not posixpath.isabs(prof):
        out.append(prof)
    return out


def dirty_outside(p: "Plan", top: Path) -> tuple:
    """(berkas berubah atau untracked di luar artefak gate, galat git). Tree tak terbaca ≠ bersih."""
    r = git(top, "status", "--porcelain", "-z", "-uall")
    if r is None or r.returncode != 0:
        return [], "`git status` gagal: " + one_line(r.stderr if r is not None else "git tidak ada")[:160]
    gates = gate_paths(p, top)
    items, out, i = r.stdout.split("\0"), set(), 0
    while i < len(items):
        entry, i = items[i], i + 1
        if len(entry) < 4:
            continue
        paths = [entry[3:]]
        if "R" in entry[:2] or "C" in entry[:2]:        # `XY baru\0lama\0`
            paths.append(items[i] if i < len(items) else "")
            i += 1
        out.update(x for x in paths if x and not any(x == g or x.startswith(g + "/") for g in gates))
    return sorted(out), ""


def base_state(top: Optional[Path], base: str) -> tuple:
    """(drift, commit sejak base). Drift = base bukan leluhur HEAD atau tak terbaca; "" bila aman/tak dinilai."""
    if top is None or base in ("", "none"):
        return "", None
    r = git(top, "merge-base", "--is-ancestor", base, "HEAD")
    if r is None:
        return "", None
    if r.returncode == 1:
        return (f"`Base-Commit` {base[:12]} bukan leluhur HEAD (rebase, amend, atau pindah branch) — diff sejak "
                f"base memuat perubahan di luar tugas; tanyakan `base_ref` ke user"), None
    if r.returncode != 0:
        return f"`Base-Commit` {base[:12]} tidak terbaca ({one_line(r.stderr)[:120]})", None
    n = git(top, "rev-list", "--count", f"{base}..HEAD")
    count = n.stdout.strip() if n is not None and n.returncode == 0 else ""
    return "", int(count) if count.isdigit() else None


def tree_hash(p: "Plan", top: Optional[Path], base: str) -> str:
    """Sidik isi berkas yang berbeda dari base + untracked, tanpa artefak gate; `none` bila tak terhitung.

    Berbasis isi, bukan teks diff: tahan konfigurasi diff git dan commit yang dibuat sesudah `close`."""
    if top is None:
        return "none"
    if base in ("", "none"):
        e = git(top, "hash-object", "-t", "tree", "--stdin")
        base = e.stdout.strip() if e is not None and e.returncode == 0 else ""
    if not base:
        return "none"
    spec = ["--", "."] + [f":(exclude){g}" for g in gate_paths(p, top)]
    d = git(top, "diff", "--name-only", "-z", "--no-renames", base, *spec)
    u = git(top, "ls-files", "--others", "--exclude-standard", "-z", *spec)
    if d is None or u is None or d.returncode or u.returncode:
        return "none"
    h = hashlib.sha256()
    for rel in sorted({x for x in d.stdout.split("\0") + u.stdout.split("\0") if x}):
        f = top / rel
        if f.is_symlink():
            data = b"L" + os.readlink(str(f)).encode("utf-8", "surrogateescape")
        elif f.is_file():
            data = (b"X" if os.access(str(f), os.X_OK) else b"F") + f.read_bytes()
        else:
            data = b"-"                                   # terhapus
        h.update(rel.encode("utf-8", "surrogateescape") + b"\0" + hashlib.sha256(data).digest())
    return "sha256:" + h.hexdigest()


def stale(p: "Plan") -> str:
    """Segel `close` yang tidak lagi cocok (13 Q9/Q14); kosong bila cocok atau blok lama tanpa segel."""
    b = p.block()
    vh, th = b.get("Verified-Hash", ""), b.get("Tree-Hash", "")
    if vh and vh != p.meta().get("Plan-Hash", ""):
        return "rencana berubah sesudah verifikasi terakhir (`Verified-Hash` ≠ `Plan-Hash`)"
    if th.startswith("sha256:"):
        cur = tree_hash(p, repo_top(p), b.get("Base-Commit", ""))
        if cur.startswith("sha256:") and cur != th:
            return "kode berubah sesudah verifikasi terakhir (`Tree-Hash` ≠ isi sekarang)"
    return ""


def body_problem(p: "Plan") -> str:
    """Wilayah sidik wajib ada: tanpa `## 1.` sidik = sha256 string kosong dan Section 1–5 bebas diubah."""
    if p.unclosed_fence:
        return "code fence (```/~~~) tidak ditutup — heading sesudahnya tidak terbaca"
    if p.body_start == len(p.lines):
        return "heading `## 1.` tidak ada — sidik Section 1–5 kosong"
    if not "\n".join(p.lines[p.body_start:p.exec_start]).strip():
        return "Section 1–5 kosong"
    return ""


def inconsistency(p: "Plan") -> str:
    """Blok eksekusi terminal wajib cocok dengan checklist; kosong bila konsisten."""
    st, steps = p.block().get("Status", ""), p.steps()
    if st.startswith("COMPLETED") and any(not ok for ok, _ in steps):
        return f"blok `{st}` padahal masih ada langkah `- [ ]` — blok ditulis tangan, atau rencana direvisi " \
               f"sesudah selesai (jalankan quickdev:execute → mode resume)"
    if st.startswith("COMPLETED") and not p.block().get("Verification", "").strip('" '):
        return f"blok `{st}` tanpa `Verification` — blok tidak ditulis `plan_lock.py close`"
    why = stale(p) if st.startswith("COMPLETED") else ""
    if why:
        return f"blok `{st}` basi: {why} — jalankan quickdev:execute (mode resume) untuk verifikasi ulang"
    return ""


def plan_digest(p: "Plan") -> str:
    """Sidik sesuai `Hash-Scope` rencana: tanpa penanda = rumus 0.4.0 (Section 1–5 saja)."""
    return p.digest(p.meta().get("Hash-Scope", ""))


def cmd_lock(p: Plan, a) -> int:
    if p.meta().get("Status") != "DRAFT":
        return fail(f"LOCK FAIL: Status `{p.meta().get('Status', '-')}` bukan DRAFT")
    if not a.answer.strip():
        return fail("LOCK FAIL: jawaban user kosong")
    problem = body_problem(p)
    if problem:
        return fail(f"LOCK FAIL: {problem}")
    if not p.steps():
        return fail("LOCK FAIL: Section 3 tanpa langkah checkbox `- [ ]`")
    # `--profile` absen → pertahankan `Profile:` yang ditulis plan Fase 2, bukan menimpanya dengan default.
    profile = (a.profile or p.meta().get("Profile") or "repo-profile.md").strip()
    if re.search(r"[\x00-\x1f\x7f]", profile):
        return fail("LOCK FAIL: `--profile` memuat baris baru atau karakter kontrol")
    # Profil dan penanda scope ditulis lebih dulu karena ikut disidik (13 Q11).
    p.set_meta(Profile=profile, Hash_Scope=SCOPE_V2)
    p.set_meta(Status="APPROVED", Approved_At=now(), Approval=quote(a.answer), Plan_Hash=p.digest(SCOPE_V2))
    p.save()
    print(f"LOCK PASS: {p.path} APPROVED @{p.digest(SCOPE_V2)[7:19]}")
    return 0


def cmd_verify(p: Plan, a) -> int:
    m = p.meta()
    if m.get("Status") != "APPROVED":
        return fail(f"VERIFY FAIL: Status `{m.get('Status', '-')}` bukan APPROVED — selesaikan approval di quickdev:plan")
    problem = body_problem(p)
    if problem:
        return fail(f"VERIFY FAIL: {problem} — `unlock`, lengkapi rencana, lalu approval ulang di quickdev:plan")
    if not m.get("Plan-Hash", "").startswith("sha256:"):
        return fail("VERIFY FAIL: rencana APPROVED tanpa `Plan-Hash` (format lama atau ditulis tangan) — "
                    "`unlock` lalu minta user menyetujui ulang di quickdev:plan (`lock`)")
    if m.get("Hash-Scope", SCOPE_V2) != SCOPE_V2:
        return fail(f"VERIFY FAIL: `Hash-Scope: {m['Hash-Scope']}` tidak dikenal — disunting tangan; `unlock` "
                    f"lalu approval ulang di quickdev:plan")
    now_hash = plan_digest(p)
    if m["Plan-Hash"] != now_hash:
        what = "Section 1–5 atau `Profile:`" if m.get("Hash-Scope") else "Section 1–5"
        return fail(f"VERIFY FAIL: {what} berubah sesudah APPROVED (tercatat {m['Plan-Hash'][7:19]}, "
                    f"sekarang {now_hash[7:19]}) — pulihkan teksnya, atau `unlock` lalu approval ulang di quickdev:plan")
    print(f"VERIFY PASS: {p.path} @{now_hash[7:19]}")
    return 0


def cmd_start(p: Plan, a) -> int:
    if cmd_verify(p, a):
        return 1
    b, steps = p.block(), p.steps()
    done = sum(1 for ok, _ in steps if ok)
    st = b.get("Status", "")
    rnd = remediation_round(b)
    top = repo_top(p)
    terminal = st.startswith("COMPLETED") or st == MANUAL
    revised = terminal and done < len(steps)
    basi = stale(p) if terminal and not revised else ""
    note = " (rencana direvisi sesudah selesai)" if revised else f" (verifikasi basi: {basi})" if basi else ""
    if b.get("Remediation-State") == "OPEN" and st in ("IN_PROGRESS", "BLOCKED"):
        # Ronde yang terputus (sesi putus / BLOCKED) dilanjutkan dengan temuan tercatat, bukan ronde baru (13 Q3).
        mode, note = "remediasi", f" (lanjutan putaran {rnd}/{REMEDIATION_CAP}; temuan tercatat dipakai)"
        p.set_block(Status="IN_PROGRESS", Timestamp=now())
    elif a.findings:
        if not st.startswith("COMPLETED"):
            return fail(f"START FAIL: remediasi menuntut Status COMPLETED, tercatat `{st or '-'}`")
        if revised:
            return fail("START FAIL: rencana punya langkah `- [ ]` baru sesudah selesai — jalankan tanpa "
                        "`--findings` (mode resume) lebih dulu")
        if rnd >= REMEDIATION_CAP:
            return fail(f"START FAIL: plafon {REMEDIATION_CAP} putaran remediasi habis — serahkan temuan ke user")
        if not (a.findings_text or "").strip():
            return fail("START FAIL: remediasi tanpa `--findings-text` — temuan wajib tercatat sebelum kode diubah")
        rnd += 1
        mode, note = "remediasi", f" (putaran {rnd}/{REMEDIATION_CAP})"
        p.set_block(Status="IN_PROGRESS", Remediation_Round=str(rnd), Remediation_State="OPEN", Timestamp=now(),
                    **{f"Findings_{rnd}": quote(a.findings_text)})
    elif st == MANUAL and not (revised or basi):
        mode = "manual"
    elif st.startswith("COMPLETED") and not (revised or basi):
        mode = "selesai"
    elif st in ("IN_PROGRESS", "BLOCKED") or done or revised or basi:
        # `revised`: review → "Revisi rencana" → unlock → langkah baru → lock. `basi`: kode atau rencana
        # berubah sesudah close. Kerja lama tetap di Base-Commit yang sama, jadi review berikutnya menilai
        # seluruh hasil sejak base itu.
        mode = "resume"
        if not b.get("Base-Commit"):
            p.set_block(Base_Commit=head_commit(p.path.parent), Base_Note="tidak tercatat sebelum sesi putus")
        p.set_block(Status="IN_PROGRESS", Timestamp=now())
    else:
        # Predikat tree bersih dinilai di sini, sebelum blok ditulis: base yang tercatat saat tree kotor
        # lalu di-commit user membuat review menilai commit itu (13 Q1).
        if top is None:
            return fail("START FAIL: bukan repo git — quickdev:execute menuntut git untuk `Base-Commit` dan review")
        dirty, err = dirty_outside(p, top)
        if err:
            return fail(f"START FAIL: {err} — tree yang tak terbaca tidak pernah bersih")
        if dirty:
            more = f" … (+{len(dirty) - 10})" if len(dirty) > 10 else ""
            return fail(f"START FAIL: mode awal menuntut tree bersih di luar direktori rencana dan profil — "
                        f"minta user meng-commit atau men-stash dulu: {', '.join(dirty[:10])}{more}")
        mode = "awal"
        p.set_block(Status="IN_PROGRESS", Base_Commit=head_commit(top), Remediation_Round="0", Timestamp=now())
    p.save()
    b = p.block()
    nxt = next((t for ok, t in steps if not ok), "-")
    print(f"START PASS: mode={mode}{note} · langkah {done}/{len(steps)} · berikutnya: {nxt} · "
          f"base={b.get('Base-Commit', '-')[:12]}")
    if mode == "remediasi":
        print(f"TEMUAN: Findings-{rnd}: {b.get(f'Findings-{rnd}', '-')}")
    drift, ahead = base_state(top, b.get("Base-Commit", ""))
    if drift:
        print(f"PERINGATAN: {drift}")
    elif ahead:
        print(f"INFO: HEAD maju {ahead} commit sejak Base-Commit — review menilainya sebagai bagian tugas")
    if b.get("Baseline"):
        print(f"BASELINE: {b['Baseline']} @{b.get('Baseline-Commit', '-')[:12]}")
    return 0


def cmd_baseline(p: Plan, a) -> int:
    """Kunci baseline segar: sah hanya di HEAD = Base-Commit dengan tree bersih, sebelum mutasi (13 Q6)."""
    if cmd_verify(p, a):
        return 1
    b = p.block()
    if b.get("Status") != "IN_PROGRESS":
        return fail("BASELINE FAIL: blok bukan IN_PROGRESS — jalankan `start` dulu")
    top = repo_top(p)
    if top is None:
        return fail("BASELINE FAIL: bukan repo git")
    base, head = b.get("Base-Commit", ""), head_commit(top)
    if head != base:
        return fail(f"BASELINE FAIL: HEAD {head[:12]} ≠ Base-Commit {base[:12]} — baseline segar hanya sah di "
                    f"Base-Commit; pakai baseline profil")
    dirty, err = dirty_outside(p, top)
    if err or dirty:
        return fail(f"BASELINE FAIL: tree tidak bersih ({err or ', '.join(dirty[:10])}) — baseline segar diukur "
                    f"sebelum mutasi pertama; pakai baseline profil")
    if not a.summary.strip():
        return fail("BASELINE FAIL: ringkasan kosong")
    p.set_block(Baseline=quote(a.summary, 600), Baseline_Commit=head)
    p.save()
    print(f"BASELINE PASS: @{head[:12]}")
    return 0


def cmd_close(p: Plan, a) -> int:
    if cmd_verify(p, a):
        return 1
    b = p.block()
    st = b.get("Status")
    manual_gagal = st == MANUAL and a.status == "BLOCKED"
    if st != "IN_PROGRESS" and not manual_gagal:
        return fail(f"CLOSE FAIL: blok `{EXEC_H2}` bukan IN_PROGRESS — jalankan `start` dulu")
    if a.status == "COMPLETED" and any(not ok for ok, _ in p.steps()):
        return fail("CLOSE FAIL: COMPLETED dengan langkah `- [ ]` tersisa")
    if a.status == "BLOCKED" and not a.blocked_step.strip():
        return fail("CLOSE FAIL: BLOCKED tanpa `--blocked-step`")
    kv = {"Status": a.status, "Verification": quote(a.verification),
          "Blocked_Step": one_line(a.blocked_step)[:80] or "-", "Timestamp": now()}
    if a.status in DONE_STATES:
        # Segel: klaim verifikasi terikat pada rencana dan isi kode yang diverifikasi (13 Q9/Q14).
        kv.update(Verified_Hash=p.meta().get("Plan-Hash", "-"),
                  Tree_Hash=tree_hash(p, repo_top(p), b.get("Base-Commit", "")))
        if b.get("Remediation-State") == "OPEN":
            kv["Remediation_State"] = "CLOSED"
    p.set_block(**kv)
    p.save()
    print(f"CLOSE PASS: {a.status}")
    return 0


def cmd_confirm(p: Plan, a) -> int:
    if cmd_verify(p, a):
        return 1
    if any(not ok for ok, _ in p.steps()):
        return fail("CONFIRM FAIL: masih ada langkah `- [ ]` — jalankan quickdev:execute (mode resume) dulu")
    if p.block().get("Status") != MANUAL:
        return fail("CONFIRM FAIL: blok bukan VERIFICATION_MANUAL_REQUIRED")
    if not a.answer.strip():
        return fail("CONFIRM FAIL: jawaban user kosong")
    why = stale(p)
    if why:
        return fail(f"CONFIRM FAIL: {why} — konfirmasi manual tidak berlaku untuk isi yang berubah; jalankan "
                    f"quickdev:execute (mode resume) untuk verifikasi ulang")
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
    rnd, why = remediation_round(b), inconsistency(p)
    rem_open = b.get("Remediation-State") == "OPEN"
    drift, ahead = base_state(repo_top(p), b.get("Base-Commit", ""))
    out = {"status": m.get("Status", "-"), "hash_ok": m.get("Plan-Hash") == plan_digest(p),
           "hash_scope": m.get("Hash-Scope") or "body",
           "profile": m.get("Profile", "-"), "gates": m.get("Gates", "-"),
           "steps_done": sum(ok for ok, _ in steps), "steps_total": len(steps),
           "next_step": next((t for ok, t in steps if not ok), "-"),
           "remediation_round": rnd, "remediation_cap": REMEDIATION_CAP,
           "remediation_open": rem_open, "open_findings": b.get(f"Findings-{rnd}", "-") if rem_open else "-",
           "base_drift": drift or "-", "commits_since_base": ahead, "baseline": b.get("Baseline", "-"),
           "consistent": not why, "inconsistency": why or "-", "execution": b}
    print(json.dumps(out, ensure_ascii=False, indent=2) if a.json else
          f"STATUS: {out['status']} · hash {'ok' if out['hash_ok'] else 'DRIFT'} · langkah "
          f"{out['steps_done']}/{out['steps_total']} · eksekusi {b.get('Status', '-')} · base {b.get('Base-Commit', '-')}"
          + ("" if out["consistent"] else f" · TIDAK KONSISTEN: {out['inconsistency']}"))
    return 0


# ------------------------------------------------------------------ sinkron nataflow (15 Q2, Q10, Q11)

SYNC = "SYNC-PAYLOAD"


def sync_root() -> Path:
    """Root git cwd (letak `.claude/nataflow.json`), atau cwd di luar repo git."""
    r = git(Path.cwd(), "rev-parse", "--show-toplevel")
    top = r.stdout.strip() if r is not None and r.returncode == 0 else ""
    return Path(top).resolve() if top else Path.cwd().resolve()


def root_relative(root: Path, raw: str):
    """(path absolut, path relatif root) atau (None, pesan) bila di luar root."""
    path = (Path.cwd() / raw).resolve()
    try:
        return path, path.relative_to(root).as_posix()
    except ValueError:
        return None, f"`{raw}` di luar root repo {root}"


def section_one(p: Plan) -> str:
    """Isi `## 1.` sampai heading `## ` berikutnya: deskripsi task (tujuan dan keputusan terkunci)."""
    end = p._first(lambda l: l.startswith("## "), p.body_start + 1)
    return "\n".join(p.lines[p.body_start:end]).strip()


def plan_title(p: Plan) -> str:
    return next((l[2:].strip() for l in p.lines[:p.body_start] if l.startswith("# ")), "")


def _sync_emit(a, payload: dict, line: str) -> int:
    ns.emit(payload, a.json, f"{SYNC} PASS: {line}")
    return 0


def _sync_documents(a, config: dict, docs: list, head: dict, line: str) -> int:
    """Fase 1 (tanpa `--remote`): argumen task/workdir/manifest tanpa isi. Fase 2: dokumen yang berbeda saja."""
    problems = ns.check_documents(docs)
    if problems:
        return ns.emit_fail(a.json, SYNC, problems)
    base = {"status": "PASS", "enabled": True, "mcp_server": config["mcp_server"]}
    if a.remote is None:
        base.update(head, documents_total=len(docs))
        return _sync_emit(a, base, line + " — argumen tool lewat `--json`")
    remote, problems = ns.read_remote(a.remote, a.remote_text)
    if problems:
        return ns.emit_fail(a.json, SYNC, problems)
    push, same = ns.split_remote(docs, remote)
    base.update(documents=push, same=same, documents_total=len(docs))
    return _sync_emit(a, base, f"{len(push)} dokumen perlu didorong, {same} sama — argumen lewat `--json`")


def cmd_sync_payload(a) -> int:
    """Argumen tool MCP nataflow; read-only, tanpa commit (D4, D5). Model mengirim nilainya apa adanya.

    Rencana: satu workdir `quickdev:<repo>:<path rencana>` bernama `<task_name>`, task baru ber-`workdir_key`
    (quickdev tidak mengenal tiket analyst), dan satu dokumen `QUICKDEV_PLAN` berisi berkas di disk (skill tidak
    meng-commit). Rencana yang belum pernah `lock` (tanpa `Approved-At`) → FAIL: DRAFT tidak didorong (D2).
    Profil: dokumen `PROFILE` di bawah workspace, `key` = `<repo>/<path>` (T10).
    """
    root = sync_root()
    config, problems = ns.load_config(root)
    if problems:
        return ns.emit_fail(a.json, SYNC, problems)
    if config is None:
        return ns.emit_skip(a.json, SYNC)
    path, rel = root_relative(root, a.repo_profile or a.plan)
    if path is None:
        return ns.emit_fail(a.json, SYNC, [rel])
    if not path.is_file():
        return ns.emit_fail(a.json, SYNC, [f"{rel} tidak ada"])
    content, problem = ns.disk_text(path)
    if problem:
        return ns.emit_fail(a.json, SYNC, [f"{rel}: {problem} — pulihkan dari git; jangan menebak isinya"])
    repo = ns.repo_identity(root, config)
    commit = ns.last_commit(root, rel)
    if a.repo_profile:
        doc = ns.document("workspace", f"{repo}/{rel}", "PROFILE", content, ns.doc_meta("quickdev", repo, rel, "", commit))
        head = {"repo": repo, "workspace_id": config["workspace_id"],
                "list_document": {"reference_table": "workspace", "include_content": False,
                                  "metadata": ns.compact({"source": "quickdev", "repo": repo})}}
        return _sync_documents(a, config, [doc], head, f"{rel} → workspace {config['workspace_id'] or '-'}")
    try:
        p = Plan(path)
        m, b = p.meta(), p.block()
    except SystemExit as exc:           # kunci ganda: FAIL rapi dari pembaca
        return ns.emit_fail(a.json, SYNC, [str(exc.code)[len("FAIL: "):] if str(exc.code).startswith("FAIL: ")
                                           else str(exc.code)])
    if (m.get("Approved-At") or "-") == "-":
        return ns.emit_fail(a.json, SYNC, [f"{rel} belum pernah dikunci (`lock`) — rencana DRAFT tidak didorong"])
    body, title = section_one(p), plan_title(p) or path.stem
    if p.body_start == len(p.lines) or not body:
        return ns.emit_fail(a.json, SYNC, [f"{rel} tanpa `## 1.` — deskripsi task diambil dari Section 1"])
    execution = b.get("Status", "")
    done = execution.startswith("COMPLETED")
    status = "done" if done else "blocked" if execution == "BLOCKED" else "active"
    key = f"quickdev:{repo}:{rel}"
    problems = ns.workdir_problems(key, path.stem, status)
    if problems:
        return ns.emit_fail(a.json, SYNC, problems)
    task = ns.task_args(config, {"source": "quickdev", "workdir_key": key}, repo, title, body)
    task["status"] = ns.task_status("done" if done else "in_progress" if execution else "")
    meta = {"source": "quickdev", "repo": repo, "path": rel, "plan_status": m.get("Status", ""),
            "plan_hash": m.get("Plan-Hash", ""), "base_commit": b.get("Base-Commit", ""), "execution": execution}
    workdir = ns.workdir_args(config, key, path.stem, status, {k: v for k, v in meta.items() if v})
    doc = ns.document("workdir", path.name, "QUICKDEV_PLAN", content,
                      ns.doc_meta("quickdev", repo, rel, m.get("Status", ""), commit, execution=execution))
    head = {"repo": repo, "task": task, "workdir": workdir,
            "list_document": {"reference_table": "workdir", "include_content": False}}
    return _sync_documents(a, config, [doc], head,
                           f"{rel} · workdir {path.stem} ({status}) · server {config['mcp_server']}")


def main_sync(a) -> None:
    """`sync-payload` berjalan di luar jalur subperintah lain: config absen harus SKIP walau rencana tidak ada."""
    a.remote_text = ""
    if a.remote == "-":
        try:
            a.remote_text = sys.stdin.read()
        except UnicodeDecodeError:
            sys.exit(ns.emit_fail(a.json, SYNC, ["stdin bukan UTF-8"]))
    sys.exit(cmd_sync_payload(a))


def main() -> None:
    ap = argparse.ArgumentParser(description="Kunci rencana quickdev")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("lock", "verify", "start", "baseline", "close", "confirm", "status", "unlock"):
        s = sub.add_parser(name)
        s.add_argument("--plan", required=True)
        if name == "baseline":
            s.add_argument("--summary", required=True, help="ringkasan baseline segar per perintah (`-` = stdin)")
        if name in ("lock", "confirm"):
            s.add_argument("--answer", required=True)
        if name == "lock":
            s.add_argument("--profile", default=None, help="default: `Profile:` yang sudah ada, lalu repo-profile.md")
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
    s = sub.add_parser("sync-payload")
    target = s.add_mutually_exclusive_group(required=True)
    target.add_argument("--plan", help="rencana yang pernah dikunci")
    target.add_argument("--repo-profile", dest="repo_profile", help="profil repo (dokumen tingkat workspace)")
    s.add_argument("--remote", default=None, help="balikan list_document include_content=false (`-` = stdin)")
    s.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "sync-payload":
        main_sync(a)
    path = Path(a.plan)

    def die(msg: str) -> None:
        if getattr(a, "json", False):
            print(json.dumps({"status": "FAIL", "error": msg}, ensure_ascii=False))
            sys.exit(1)
        sys.exit(f"FAIL: {msg}")

    # Nilai `-` = teks dari stdin (heredoc berkutip di SKILL); stdin hanya dapat dibaca sekali (13 Q4).
    from_stdin = [k for k in TEXT_ARGS + ("blocked_step", "profile") if getattr(a, k, None) == "-"]
    if len(from_stdin) > 1:
        die(f"hanya satu argumen boleh bernilai `-` (stdin) per panggilan: {', '.join(from_stdin)}")
    if from_stdin:
        if from_stdin[0] not in TEXT_ARGS:
            die(f"`--{from_stdin[0].replace('_', '-')}` tidak menerima stdin")
        try:
            setattr(a, from_stdin[0], sys.stdin.read())
        except UnicodeDecodeError:
            die("stdin bukan UTF-8")

    if not path.is_file():
        die(f"{path} tidak ada")
    try:
        plan = Plan(path)
    except UnicodeDecodeError as exc:
        die(f"{path} bukan UTF-8 ({exc.reason} @ byte {exc.start}) — pulihkan dari git; jangan menebak isinya")
    try:
        code = globals()[f"cmd_{a.cmd}"](plan, a)
    except SystemExit as exc:          # FAIL rapi dari pembaca field (`remediation_round`)
        if isinstance(exc.code, str):
            die(exc.code[len("FAIL: "):] if exc.code.startswith("FAIL: ") else exc.code)
        raise
    sys.exit(code)


if __name__ == "__main__":
    main()
