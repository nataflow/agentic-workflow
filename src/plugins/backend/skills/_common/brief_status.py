"""Mesin status brief backend dan penanda tingkat taskdir.

Satu rumah untuk pertanyaan yang diajukan `architect`, `report`, dan `plan` atas
disk taskdir: status tiap brief, tautan `supersedes`/`superseded_by`, kesegaran
`REVIEW.md`, penanda henti `HALT.md`, dan commit brief yang sudah mendarat.

Status brief dan penulis tunggalnya:

* `READY`       — `plan` (`scaffold_brief.py --nn`).
* `DONE`        — `code-implementor`; koreksi `READY → DONE` oleh `architect`
                  hanya saat commit brief terbukti mendarat.
* `BLOCKED`     — `code-implementor` saat stop condition.
* `SUPERSEDED`  — hanya `scaffold_brief.py --nn <pengganti>`, atas brief `BLOCKED`
                  atau brief `READY` hilir yang diterbitkan ulang. Terminal.

Zero external dependencies (Python Standard Library only).
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from precondition_lib import FrontmatterError, doc_status, split_frontmatter

BRIEF_STATUSES = ("READY", "DONE", "BLOCKED", "SUPERSEDED")
CLOSED = ("DONE", "SUPERSEDED")               # tidak dieksekusi lagi, tidak menahan rantai
LOCKED = ("DONE", "BLOCKED", "SUPERSEDED")    # alokasi tidak boleh ditulis ulang `plan`
SUPERSEDABLE = ("BLOCKED", "READY")           # asal sah transisi -> SUPERSEDED
HALT_FILE = "HALT.md"
HALT_VERDICTS = ("COMPILE", "SCOPE", "SYMBOL", "STRAY")

# Hanya blok `---` pertama; BOM dan CRLF diterima.
_FM = re.compile(r"^(﻿?---\r?\n)(.*?)(\r?\n---[ \t]*(?:\r?\n|$))", re.S)
_BRIEF_NAME = re.compile(r"^brief-(\d{2})-")


def read_frontmatter(path: Path) -> Dict[str, str]:
    """Field frontmatter blok `---` pertama; baris `key:` di badan atau blok kode tidak terbaca.

    Parser bersama `precondition_lib.split_frontmatter`; frontmatter rusak (tanpa
    pagar, kunci ganda) terbaca kosong sehingga status brief jatuh ke `UNKNOWN`.
    """
    try:
        return split_frontmatter(path.read_bytes().decode("utf-8"))[0]
    except (OSError, UnicodeDecodeError, FrontmatterError):
        return {}


def set_frontmatter(path: Path, **fields: str) -> None:
    """Tulis/timpa field frontmatter; badan dan gaya akhir baris dipertahankan byte-per-byte."""
    text = path.read_bytes().decode("utf-8")
    m = _FM.match(text)
    if not m:
        raise ValueError(f"{path.name}: frontmatter tidak terbaca")
    nl = "\r\n" if "\r\n" in m.group(1) else "\n"
    body = m.group(2)
    for key, val in fields.items():
        pat = re.compile(rf"^{re.escape(key)}:[^\r\n]*", re.M)   # bukan `.*$`: `.` ikut memakan `\r`
        if pat.search(body):
            body = pat.sub(lambda _m: f"{key}: {val}", body, count=1)
        else:
            body = f"{body}{nl}{key}: {val}"
    path.write_bytes((m.group(1) + body + m.group(3) + text[m.end():]).encode("utf-8"))


def brief_refs(value: str) -> List[str]:
    """`brief-02, brief-03` -> ["02", "03"]."""
    return re.findall(r"brief-(\d{2})", value or "")


def scan_briefs(taskdir: Path) -> List[Dict]:
    """Brief taskdir urut NN, dibaca dari frontmatter saja.

    Status dibandingkan persis (huruf besar): `status: ready` atau frontmatter
    rusak menjadi `UNKNOWN` dengan alasannya di `why`, bukan dilipat diam-diam.
    """
    out: List[Dict] = []
    for p in sorted(taskdir.glob("brief-*.md")):
        m = _BRIEF_NAME.match(p.name)
        if not m:
            continue
        fm = read_frontmatter(p)
        status, why = doc_status(p, BRIEF_STATUSES)
        out.append({
            "nn": m.group(1),
            "name": p.name,
            "path": p,
            "status": status or "UNKNOWN",
            "why": why,
            "superseded_by": brief_refs(fm.get("superseded_by", "")),
            "supersedes": brief_refs(fm.get("supersedes", "")),
            "repairs": brief_refs(fm.get("repairs", "")),
            "commit_message": fm.get("commit_message", ""),
        })
    return out


def validate_links(briefs: List[Dict]) -> List[str]:
    """`SUPERSEDED` wajib bertaut dua arah ke satu pengganti ber-NN lebih besar.

    Pengganti sah berstatus `READY`/`DONE`, atau `SUPERSEDED` yang tautannya
    sendiri sah (rantai penggantian). Pengganti `BLOCKED` adalah pelanggaran:
    brief yang digantikan belum benar-benar tertutup.
    """
    by_nn = {b["nn"]: b for b in briefs}
    problems: List[str] = []
    # Satu NN = satu berkas (11 H7); peta `by_nn` di atas dan titik masuk `FASE_3:<NN>` tidak dapat
    # membedakan dua berkas bernomor sama.
    for nn in sorted({b["nn"] for b in briefs}):
        twins = [b["name"] for b in briefs if b["nn"] == nn]
        if len(twins) > 1:
            problems.append(f"brief-{nn} dipakai {len(twins)} berkas: {', '.join(twins)}")
    for b in briefs:
        if b["status"] == "SUPERSEDED":
            tgt = by_nn.get(b["superseded_by"][0]) if len(b["superseded_by"]) == 1 else None
            if not tgt:
                problems.append(f"{b['name']}: SUPERSEDED tanpa `superseded_by: brief-NN` yang ada")
            elif int(tgt["nn"]) <= int(b["nn"]) or b["nn"] not in tgt["supersedes"]:
                problems.append(f"{b['name']}: tautan ke {tgt['name']} tidak dua arah atau NN tidak naik")
            elif tgt["status"] not in ("READY", "DONE", "SUPERSEDED"):
                problems.append(f"{tgt['name']}: pengganti {b['name']} berstatus {tgt['status']}")
        for s in b["supersedes"]:
            if by_nn.get(s, {}).get("status") != "SUPERSEDED":
                problems.append(f"{b['name']}: supersedes brief-{s} yang tidak berstatus SUPERSEDED")
    return problems


# -- git ------------------------------------------------------------------------------------


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def review_freshness(root: Path, taskdir_rel: str) -> Tuple[bool, str]:
    """`REVIEW.md` sah hanya bila tak ada commit brief/kode sesudah commit `REVIEW.md`.

    Yang dikecualikan (`backenddev/`, `.claude/`) sama dengan yang dikecualikan
    `code-reviewer` Fase 0 butir 5, sehingga `REPORT.md`, `HALT.md`, `TASK.md`,
    dan indeks issues tidak membuat REVIEW basi; brief atau kode baru selalu.
    """
    rv = git(root, "log", "-1", "--format=%H", "--", f"{taskdir_rel}/REVIEW.md")
    if not rv:
        return False, "REVIEW.md belum ter-commit"
    later = set(git(root, "rev-list", f"{rv}..HEAD", "--", f"{taskdir_rel}/brief-*.md").split())
    later |= set(git(root, "rev-list", f"{rv}..HEAD", "--", ".",
                     ":(exclude)backenddev", ":(exclude).claude").split())
    if later:
        return False, f"{len(later)} commit brief/kode mendarat sesudah REVIEW.md @ {rv[:7]}"
    return True, f"REVIEW.md @ {rv[:7]} menutup HEAD"


def norm_subject(subject: str) -> str:
    """Spasi dirapatkan dan huruf disamakan: subjek diketik implementor (09 E18)."""
    return " ".join(subject.split()).casefold()


def landed_sha(root: Path, brief_rel: str, commit_message: str) -> str:
    """SHA commit ber-subjek `commit_message` brief, sesudah brief itu lahir.

    Dibandingkan sesudah `norm_subject` (bukan `--grep` regex): satu spasi atau huruf yang meleset
    tidak lagi membuat unit yang sudah mendarat di-dispatch ulang. Rentangnya dimulai dari commit
    yang menambahkan berkas brief, supaya unit bernama sama di taskdir lain tidak ikut cocok.
    """
    if not commit_message:
        return ""
    born = git(root, "log", "--diff-filter=A", "--format=%H", "--", brief_rel).splitlines()
    if not born:
        return ""
    want = norm_subject(commit_message)
    for line in git(root, "log", "--format=%h%x09%s", f"{born[-1]}..HEAD").splitlines():
        sha, _, subj = line.partition("\t")
        if norm_subject(subj) == want:
            return sha
    return ""


def _status_at(root: Path, rev: str, brief_rel: str) -> str:
    r = subprocess.run(["git", "show", f"{rev}:{brief_rel}"], cwd=root, capture_output=True)
    if r.returncode != 0:
        return ""
    try:
        return str(split_frontmatter(r.stdout.decode("utf-8"))[0].get("status", "")).strip()
    except (UnicodeDecodeError, FrontmatterError):
        return ""


def _carries_code(root: Path, sha: str) -> bool:
    """Commit menyentuh berkas di luar dokumen rantai (`backenddev/`, `.claude/`)."""
    return bool(git(root, "show", "--name-only", "--format=", sha, "--", ".", ":(exclude)backenddev",
                    ":(exclude).claude").strip())


def done_sha(root: Path, brief_rel: str, commit_message: str = "") -> str:
    """SHA commit bukti brief `DONE` mendarat; kosong bila tak ada.

    Implementor meng-commit `status: DONE` bersama kode unitnya (satu commit), jadi transisi status
    di riwayat git adalah bukti mendarat yang tidak bergantung pada subjek yang diketik. `DONE` yang
    hanya ada di working tree, atau ditulis tangan lalu di-commit tanpa lewat transisi, tidak punya
    bukti ini (09 E18).

    Transisi yang hanya menyentuh dokumen sah bila commit unit ber-`commit_message` brief sudah
    mendarat lebih dulu dan membawa kode: itulah koreksi `READY → DONE` architect
    (`lifecycle-recovery.md` bagian 3), yang memang commit brief saja (11 H5).
    """
    for sha in git(root, "log", "--format=%H", "--", brief_rel).splitlines():
        if _status_at(root, sha, brief_rel) == "DONE" and _status_at(root, f"{sha}^", brief_rel) != "DONE":
            if _carries_code(root, sha):
                return sha[:7]
            landed = landed_sha(root, brief_rel, commit_message)
            if landed and _carries_code(root, landed) and \
                    subprocess.run(["git", "merge-base", "--is-ancestor", landed, sha], cwd=root,
                                   capture_output=True).returncode == 0:
                return landed[:7]
            return ""
    return ""


FIXED_MARKER = re.compile(r"^> Status: FIXED\b")


def finding_diff_ok(root: Path, sha: str, path: str) -> bool:
    """Diff `path` di commit `sha` hanya menambah baris `> Status: FIXED …`.

    Berkas `finding_source` sah ikut commit implementor hanya dalam bentuk ini;
    perubahan lain atas berkas temuan tetap pelanggaran scope.
    """
    diff = git(root, "show", sha, "-U0", "--format=", "--", path)
    changed = [l for l in diff.splitlines()
               if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    return bool(changed) and all(l.startswith("+") and FIXED_MARKER.match(l[1:]) for l in changed)


# -- penanda henti ----------------------------------------------------------------------------


def read_halt(taskdir: Path) -> Optional[Dict[str, str]]:
    """Frontmatter `{taskdir}/HALT.md`, atau None bila rantai tidak ditahan."""
    halt = taskdir / HALT_FILE
    return read_frontmatter(halt) if halt.exists() else None


def halted_nn(taskdir: Path) -> Optional[str]:
    """NN brief yang ditahan `HALT.md` ("02"), atau None."""
    fm = read_halt(taskdir)
    refs = brief_refs(fm.get("brief", "")) if fm else []
    return refs[0] if refs else None
