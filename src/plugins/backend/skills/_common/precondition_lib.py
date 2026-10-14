#!/usr/bin/env python3
"""Primitif parsing dan I/O bersama skrip prasyarat backend.

Frontmatter, taskdir, chain, status git, profil, berkas plugin, dan format
keluaran — satu parser untuk tiap jenis data, dipakai semua skrip, sehingga
vonis gerbang tidak bergantung pada substring di badan dokumen, path berkutip
dari git, atau salinan kode yang sudah divergen. Check itu sendiri tetap tinggal
di skripnya: tiap skill menagih hal yang berbeda, memberi pesan remediasi yang
berbeda, dan menomori check-nya sendiri.

Deteksi repo dan pembacaan profil memakai `hooks/detect.py` (fungsi yang sama
dengan yang dipakai hook SessionStart, sehingga vonis hook = vonis skrip).

Zero external dependencies (Python Standard Library only).
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

# Deteksi repo dan pembacaan profil tinggal di `hooks/detect.py` (identik di
# backend dan frontend) — satu implementasi untuk hook dan skrip.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
import detect as _detect  # noqa: E402

# Tiap plugin engineer punya direktori profilnya sendiri. `.claude/profile/`
# (tanpa subdirektori) adalah lokasi lama yang hanya dibaca selama masa transisi
# dan selalu disertai catatan MIGRATE.
PLUGIN = "backenddev"
PROFILE_DIR_REL = f".claude/profile/{PLUGIN}"      # satu-satunya lokasi tulis
LEGACY_PROFILE_DIR_REL = ".claude/profile"          # lokasi lama, dibaca hanya untuk MIGRATE
PROFILE_FILES = _detect.PROFILE_FILES[PLUGIN]


def resolve_profile_dir(root: Path) -> Tuple[Path, str]:
    """(direktori profil yang dibaca, catatan untuk laporan prasyarat).

    Lokasi baru selalu menang. Lokasi lama dipakai hanya bila `index.json`-nya
    milik plugin ini (field `plugin`, atau `stack` anggota daftar backend),
    dan selalu disertai catatan MIGRATE. Profil milik plugin lain tidak pernah
    dikembalikan: skrip melihatnya sebagai profil yang tidak ada.
    """
    own = root / PROFILE_DIR_REL
    if (own / "index.json").exists():
        return own, ""
    prof = _detect.read_profile(root, PLUGIN)
    if prof.location == "legacy" and prof.state not in ("OTHER_OWNER", "ABSENT", "INVALID_JSON"):
        return root / LEGACY_PROFILE_DIR_REL, (
            "profil backend masih di lokasi lama `.claude/profile/`; "
            "jalankan `backend:profile` mode MIGRATE")
    return own, ""


def legacy_suffix(note: str) -> str:
    """Sufiks ringkasan check PASS saat profil masih dibaca dari lokasi lama."""
    return f" — {note}" if note else ""


def foreign_owner(profile_dir: Path) -> str:
    """Nama plugin lain pemilik `<profile_dir>/index.json`, atau '' bila milik sendiri/tak terbaca."""
    data, _state = _detect.read_index(profile_dir / "index.json")
    if data is None:
        return ""
    owner = _detect.owner_of(data)
    return owner if owner and owner != PLUGIN else ""


def nearest_existing_ancestor(path: Path) -> Path:
    """Naik ke atas sampai menemukan direktori yang benar-benar sudah ada."""
    probe = path
    while not probe.exists():
        parent = probe.parent
        if parent == probe:
            break
        probe = parent
    return probe


def probe_writable(path: Path) -> Tuple[bool, str]:
    """Uji izin tulis tanpa membuat direktori dan tanpa menulis berkas uji.

    Skrip prasyarat hanya memeriksa; pembuatan direktori adalah wewenang fase
    kerja skill yang memilikinya. Yang diuji adalah direktori induk terdekat
    yang sudah ada, karena di situlah direktori target nanti akan dibuat.

    Mengembalikan (ok, keterangan).
    """
    anchor = nearest_existing_ancestor(path)
    if not anchor.is_dir():
        return False, f"{anchor} ada tetapi bukan direktori"
    if not os.access(anchor, os.W_OK | os.X_OK):
        return False, f"{anchor} tidak memiliki izin tulis"
    return True, str(anchor)


def profile_staleness(root: Path, source_root: str) -> Tuple[str, str]:
    """Nilai kesegaran profil backend terhadap kode yang dipetakannya.

    Profil yang tertinggal di belakang kode tidak pernah gagal dengan suara:
    `domain-map.md` yang basi melebarkan `Batas cakupan` explorer ke seluruh
    `source_root`, dan `surface-map.md` yang basi membuat permukaan baru tidak
    terdaftar. Keduanya menurunkan daya jangkau eksplorasi tanpa satu pun
    kegagalan tercatat, dan itulah yang dibuat terbaca di sini.

    Vonisnya **tidak pernah menggagalkan** skrip prasyarat — profil basi adalah
    keadaan wajar pada repo yang bergerak, bukan alasan menghentikan kerja.
    Pemanggil menempelkannya sebagai catatan degradasi, sejalan dengan banner
    `TERDEGRADASI` Check E `plan`.

    Mengembalikan (vonis, keterangan) dengan vonis salah satu dari
    `SEGAR`, `BASI`, atau `TAK_TERNILAI`.
    """
    profile_dir, _note = resolve_profile_dir(root)
    if not profile_dir.is_dir():
        return "TAK_TERNILAI", f"{PROFILE_DIR_REL}/ tidak ada"

    sr = (source_root or "").strip().strip("/")
    if not sr:
        return "TAK_TERNILAI", "source_root kosong di index.json"
    if not (root / sr).exists():
        return "TAK_TERNILAI", f"source_root '{sr}' tidak ada di disk"

    def _git(*args: str) -> str:
        try:
            out = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        return out.stdout.strip() if out.returncode == 0 else ""

    if _git("rev-parse", "--is-inside-work-tree") != "true":
        return "TAK_TERNILAI", "bukan repositori git"

    # Hanya berkas profil backend: commit profil plugin lain (mis.
    # `.claude/profile/frontenddev/`) tidak boleh me-reset vonis kesegaran.
    rel = profile_dir.relative_to(root).as_posix()
    profile_sha = _git("log", "-1", "--format=%H", "--", *(f"{rel}/{f}" for f in PROFILE_FILES))
    if not profile_sha:
        return "TAK_TERNILAI", "profil belum pernah masuk riwayat git"

    # Rentang commit, bukan rentang waktu: `--since` berbasis approxidate dan
    # tidak menerima epoch mentah, sehingga penyaringnya diam-diam tidak
    # berlaku dan tiap commit ikut terhitung.
    lag = _git("rev-list", "--count", f"{profile_sha}..HEAD", "--", sr)
    if not lag.isdigit():
        return "TAK_TERNILAI", f"riwayat '{sr}' tidak terbaca"

    n = int(lag)
    if n == 0:
        return "SEGAR", f"nol commit menyentuh '{sr}' sesudah profil terakhir diperbarui"
    return "BASI", (
        f"{n} commit menyentuh '{sr}' sesudah profil terakhir diperbarui — "
        "batas cakupan explorer dan daftar permukaan berpotensi tertinggal"
    )



# ============================================================ konstanta

PLUGIN_ROOT = Path(__file__).resolve().parents[2]          # src/plugins/backend
TASKDIR_RE = re.compile(r"^backenddev/docs/\d{10}-[a-z0-9-]+$")
VALID_CHAINS = ("BRD_PRD_BRIEF", "PRD_BRIEF", "BRIEF")
VALID_RISKS = ("BREAKING", "MAJOR", "MINOR")
# Tujuh kunci yang ditulis profile/templates/profile-template.md bagian 1 dan
# dibaca skrip (`project` ditulis template tetapi tidak dibaca satu skrip pun).
# Semua skrip prasyarat menagih ketujuhnya, supaya profil yang kurang gagal di
# hulu rantai, bukan baru di architect/report.
REQUIRED_INDEX_KEYS = (
    "stack", "architecture", "root_namespace", "source_root",
    "commit_convention", "base_branch", "branch_convention",
)
_NA = ("", "-", "—")
_BOM = chr(0xFEFF)


class FrontmatterError(ValueError):
    """Frontmatter tidak ada, tidak tertutup, atau memuat kunci ganda."""


class GitError(RuntimeError):
    """Perintah git gagal (bukan repo, git tidak terpasang, repo rusak)."""


# ============================================================ repo & git

def find_repo_root(start: Optional[Path] = None) -> Path:
    """Akar worktree git dari `start` (bawaan cwd); `start` itu sendiri bila bukan repo git."""
    base = Path(start) if start else Path.cwd()
    try:
        proc = subprocess.run(["git", "-C", str(base), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return base.resolve()
    top = proc.stdout.strip()
    if proc.returncode == 0 and top and os.path.isdir(top):
        return Path(top).resolve()
    return base.resolve()


def is_scratch(path: str) -> bool:
    """Laci code-explorer: `backenddev/docs/.explore/**` atau `backenddev/docs/<taskdir>/.explore/**`."""
    seg = path.strip("/").split("/")
    return seg[:2] == ["backenddev", "docs"] and ".explore" in seg[2:4]


def dirty_paths(root: Path, exclude_scratch: bool = True) -> List[str]:
    """Path kotor relatif root dari `git status --porcelain -z -uall`.

    Tanpa kutip, tanpa escape oktal. Rename/copy menyumbang **kedua** path-nya (tujuan lalu
    asal): memindahkan berkas ter-track ke laci `.explore/` tetap terhitung kotor lewat path
    asalnya. Laci kerja (`is_scratch`) dibuang bila `exclude_scratch`. Raise `GitError` bila git gagal.
    """
    try:
        proc = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "-z", "-uall"],
                              capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitError(str(exc)) from exc
    if proc.returncode != 0:
        raise GitError(proc.stderr.decode("utf-8", "replace").strip() or "git status gagal")
    entries = proc.stdout.decode("utf-8", "surrogateescape").split("\0")
    out: List[str] = []
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        xy, path = entry[:2], entry[3:]
        paths = [path]
        if "R" in xy or "C" in xy:      # format -z: "XY <tujuan>\0<asal>\0"
            if i < len(entries) and entries[i]:
                paths.append(entries[i])
            i += 1
        out.extend(p for p in paths if not (exclude_scratch and is_scratch(p)))
    return out


# Penanda operasi git yang belum selesai. Dicari lewat `git rev-parse --git-path`
# supaya benar juga di worktree tambahan, tempat `.git` berupa berkas.
GIT_OPERATION_MARKERS = (
    ("MERGE_HEAD", "merge"),
    ("CHERRY_PICK_HEAD", "cherry-pick"),
    ("REVERT_HEAD", "revert"),
    ("rebase-merge", "rebase"),
    ("rebase-apply", "rebase/am"),
    ("sequencer", "sequencer (cherry-pick/revert beruntun)"),
    ("BISECT_LOG", "bisect"),
)


def _git_out(root: Path, *args: str) -> Tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        return 255, str(exc)
    return r.returncode, r.stdout.strip()


def git_operation_in_progress(root: Path) -> List[str]:
    """Label operasi git yang masih menggantung (kosong = tidak ada)."""
    found: List[str] = []
    for marker, label in GIT_OPERATION_MARKERS:
        rc, out = _git_out(root, "rev-parse", "--git-path", marker)
        if rc != 0 or not out:
            continue
        p = Path(out)
        if not p.is_absolute():
            p = root / p
        if p.exists() and label not in found:
            found.append(label)
    return found


def check_base_branch(root: Path, base: Optional[str], require_diff: bool = False) -> Tuple[bool, str]:
    """Validasi `base_branch` dan posisi HEAD untuk skill yang menilai diff merge-base.

    Mengembalikan (ok, keterangan). Urutan: base resolve → HEAD ter-attach →
    HEAD bukan base → merge-base ada → (opsional) ada commit di atas base.
    """
    base = (base or "").strip()
    if not base or base == "tidak terdeteksi":
        return False, "base_branch kosong di parameter maupun index.json"
    rc, _ = _git_out(root, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
    if rc != 0:
        return False, f"base_branch '{base}' tidak resolve ke commit"
    rc, head = _git_out(root, "symbolic-ref", "-q", "--short", "HEAD")
    if rc != 0 or not head:
        return False, "Detached HEAD — rantai wajib berjalan di branch kerja"
    if head == base:
        return False, f"HEAD berada di base branch `{base}` — rantai wajib berjalan di branch kerja"
    rc, mb = _git_out(root, "merge-base", base, "HEAD")
    if rc != 0 or not mb:
        return False, f"tidak ada merge-base antara '{base}' dan HEAD"
    if require_diff:
        _, head_sha = _git_out(root, "rev-parse", "HEAD")
        if mb == head_sha:
            return False, f"nol commit di atas '{base}' (merge-base = HEAD)"
    return True, f"branch '{head}' · merge-base {mb[:7]} terhadap '{base}'"


# ============================================================ materai dokumen (Langkah 24)

# Dokumen taskdir tidak di-commit (24 K1): `APPROVED` dan akar rantai dijangkarkan pada materai di disk,
# bukan pada riwayat git. `docs_git.py` (salinan identik backend/frontend) memegang `base_commit_problem`.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs_git as _docs_git  # noqa: E402

SEAL_FIELDS = ("status", "approved_seal", "approved_at", "approval")
_SEAL_LINE = re.compile(rf"^(?:{'|'.join(SEAL_FIELDS)})[ \t]*:.*$")


def doc_seal(text: str) -> str:
    """Sidik sha256 isi dokumen tanpa baris frontmatter `status`/`approved_*`/`approval` (24 K8).

    BOM dan CRLF dinormalkan; badan dokumen ikut utuh. Menyunting isi sesudah approve mengubah sidik,
    sedangkan penulisan materai itu sendiri tidak.
    """
    lines = normalize_text(text).split("\n")
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is not None:
            lines = [lines[0]] + [l for l in lines[1:end] if not _SEAL_LINE.match(l)] + lines[end:]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def task_base_commit(root: Path, taskdir: Path) -> Tuple[str, str]:
    """`(base_commit, masalah)` frontmatter `TASK.md` taskdir; masalah kosong bila sah (24 K6)."""
    value = frontmatter_field(Path(taskdir) / "TASK.md", "base_commit") or ""
    return value, _docs_git.base_commit_problem(root, value)


def approval_verdict(root: Path, doc: Path, kind: str) -> Tuple[bool, str]:
    """`status: APPROVED` BRD/PRD sah hanya bila materai approve `analyst` utuh (11 H17, 24 K8).

    `doc_seal.py approve` satu-satunya jalur tulis `APPROVED`: ia menulis `approved_seal` = sidik isi
    yang disetujui user (`analyst/references/chain-rules.md` bagian 4 butir 5). APPROVED tulisan tangan
    (tanpa materai), atau isi yang disunting sesudah approval, tidak lolos hanya karena frontmatter-nya
    berbunyi benar.
    """
    name = Path(doc).name
    try:
        text = Path(doc).read_bytes().decode("utf-8")
        fields, _ = split_frontmatter(text)
    except OSError as exc:
        return False, f"{name} tidak terbaca: {exc}"
    except UnicodeDecodeError:
        return False, f"{name} bukan UTF-8"
    except FrontmatterError as exc:
        return False, f"{name}: {exc}"
    seal = (fields.get("approved_seal") or "").strip()
    if not seal:
        return False, f"{name} berstatus APPROVED tanpa `approved_seal` — APPROVED tidak lewat `doc_seal.py approve`"
    if seal != doc_seal(text):
        return False, f"{name} disunting sesudah approve (isi ≠ `approved_seal` {seal[:12]})"
    return True, f"{kind} APPROVED @ {seal[:12]}"


def is_under(path: str, prefix: str) -> bool:
    """`path` sama dengan `prefix` atau berada di bawahnya, per segmen (bukan substring)."""
    a = [p for p in path.strip("/").split("/") if p not in ("", ".")]
    b = [p for p in prefix.strip("/").split("/") if p not in ("", ".")]
    return bool(b) and a[:len(b)] == b


# ============================================================ teks & frontmatter

def normalize_text(text: str) -> str:
    """Buang BOM di awal, samakan CRLF/CR menjadi LF."""
    return text.lstrip(_BOM).replace("\r\n", "\n").replace("\r", "\n")


def read_text(path: Path) -> str:
    return normalize_text(Path(path).read_text(encoding="utf-8"))


_FM_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:(.*)$")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Pisahkan blok frontmatter PERTAMA → `(fields, body)`.

    Hanya kunci tingkat atas; nilai berkutip dibuka, komentar ` # ...` di ujung
    nilai tak berkutip dibuang. Raise `FrontmatterError` bila pagar pembuka tidak
    di baris pertama, pagar penutup tidak ada, atau satu kunci muncul dua kali.
    """
    lines = normalize_text(text).split("\n")
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("baris pertama bukan pagar frontmatter `---`")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise FrontmatterError("pagar penutup frontmatter `---` tidak ditemukan")
    fields: Dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw[:1].isspace() or raw.lstrip().startswith("#"):
            continue
        m = _FM_KEY.match(raw)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value[:1] not in ("'", '"'):
            value = re.sub(r"\s+#.*$", "", value)
        if key in fields:
            raise FrontmatterError(f"kunci frontmatter `{key}` muncul lebih dari sekali")
        fields[key] = _unquote(value.strip())
    return fields, "\n".join(lines[end + 1:])


def read_frontmatter(path: Path) -> Tuple[Dict[str, str], str]:
    """`split_frontmatter` atas isi berkas. OSError, UnicodeDecodeError, dan FrontmatterError diteruskan."""
    return split_frontmatter(Path(path).read_text(encoding="utf-8"))


def frontmatter_field(path: Path, key: str) -> Optional[str]:
    """Nilai satu kunci, atau None bila berkas/frontmatter/kunci tidak ada atau rusak."""
    try:
        fields, _ = read_frontmatter(path)
    except (OSError, UnicodeDecodeError, FrontmatterError):
        return None
    return fields.get(key)


def doc_status(path: Path, allowed: Sequence[str]) -> Tuple[Optional[str], str]:
    """Status dokumen dari frontmatter saja → `(STATUS, "")` atau `(None, alasan)`.

    Nilai dibandingkan persis (huruf besar) dengan `allowed`: `status: approved`
    ditolak dengan pesan yang menyebut nilai aktualnya (fail-closed).
    """
    name = Path(path).name
    try:
        fields, _ = read_frontmatter(path)
    except OSError as exc:
        return None, f"{name} tidak terbaca: {exc}"
    except UnicodeDecodeError:
        return None, f"{name} bukan UTF-8"
    except FrontmatterError as exc:
        return None, f"{name}: {exc}"
    value = fields.get("status")
    if value is None:
        return None, f"{name}: frontmatter tanpa kunci `status`"
    if value not in allowed:
        return None, f"{name}: status `{value}` bukan salah satu dari {' | '.join(allowed)}"
    return value, ""


def iter_outside_fences(text: str) -> Iterable[Tuple[int, str]]:
    """`(nomor_baris, baris)` di luar blok kode berpagar ``` atau ~~~ (panjang pagar dihormati)."""
    fence = ""
    for no, line in enumerate(normalize_text(text).split("\n"), start=1):
        m = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if m:
            tok = m.group(1)
            if not fence:
                fence = tok
                continue
            if tok[0] == fence[0] and len(tok) >= len(fence) and not line.strip()[len(tok):].strip():
                fence = ""
                continue
        if not fence:
            yield no, line


def count_h1(text: str) -> int:
    """Jumlah heading H1 ATX di badan (sesudah frontmatter), di luar code fence."""
    try:
        _, body = split_frontmatter(text)
    except FrontmatterError:
        body = normalize_text(text)
    return sum(1 for _, l in iter_outside_fences(body) if re.match(r"^# +\S", l))


def has_heading(text: str, heading: str) -> bool:
    """Baris heading persis `heading` ada di luar code fence."""
    return any(l.strip() == heading for _, l in iter_outside_fences(text))


# ============================================================ enum

def parse_enum(value: Optional[str], allowed: Sequence[str], label: str) -> Tuple[Optional[str], str]:
    """Normalkan nilai enum (trim, buka kutip, huruf besar) → `(NILAI, "")`, `(None, "")` bila
    kosong/-/—, atau `(None, galat)` bila asing. Tanda hubung tidak dilipat ke garis bawah."""
    if value is None:
        return None, ""
    v = _unquote(value.strip()).strip()
    if v in _NA:
        return None, ""
    v = v.upper()
    if v in allowed:
        return v, ""
    return None, f"{label} '{value.strip()}' tidak sah (wajib {' | '.join(allowed)})"


def parse_chain(value: Optional[str]) -> Tuple[Optional[str], str]:
    return parse_enum(value, VALID_CHAINS, "chain")


def declared_chain(taskdir: Optional[Path]) -> Tuple[Optional[str], str]:
    """Chain dari frontmatter `TASK.md` → `(CHAIN, "")`, `(None, "")` bila berkas/kunci belum ada,
    atau `(None, galat)` bila frontmatter rusak atau nilainya asing."""
    task = Path(taskdir) / "TASK.md" if taskdir else None
    if task is None or not task.is_file():
        return None, ""
    try:
        fields, _ = read_frontmatter(task)
    except (OSError, UnicodeDecodeError, FrontmatterError) as exc:
        return None, f"TASK.md: {exc}"
    return parse_chain(fields.get("chain"))


# ============================================================ taskdir

@dataclass
class TaskdirVerdict:
    ok: bool
    rel: str               # path relatif root berpemisah '/', '' bila tak ter-resolve
    path: Optional[Path]   # path absolut ter-resolve
    summary: str


def resolve_taskdir(root: Path, arg: str) -> Path:
    p = Path(arg.strip()).expanduser()
    return (p if p.is_absolute() else Path(root) / p).resolve()


def check_taskdir(root: Path, arg: Optional[str], must_exist: bool = True) -> TaskdirVerdict:
    """Vonis parameter taskdir: di dalam root, pola kanonik berjangkar, direktori (dan ada bila wajib).

    `resolve()` dilakukan sebelum `relative_to`, sehingga path absolut lewat
    symlink dan bentuk `./…/` ternormalisasi.
    """
    if not arg or not arg.strip():
        return TaskdirVerdict(False, "", None, "Parameter taskdir belum diberikan")
    root = Path(root).resolve()
    path = resolve_taskdir(root, arg)
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return TaskdirVerdict(False, "", path, f"Taskdir '{arg}' berada di luar root repo {root}")
    if not TASKDIR_RE.match(rel):
        return TaskdirVerdict(False, rel, path,
                              f"Format taskdir '{rel}' tidak mengikuti pola kanonik "
                              "backenddev/docs/<YYMMDDhhmm>-<slug>/")
    if path.exists() and not path.is_dir():
        return TaskdirVerdict(False, rel, path, f"Taskdir '{rel}' ada tetapi bukan direktori")
    if must_exist and not path.is_dir():
        return TaskdirVerdict(False, rel, path, f"Direktori taskdir tidak ditemukan di disk: {rel}")
    return TaskdirVerdict(True, rel, path, f"Taskdir terverifikasi: {rel}")


TASKDIR_ACTION = ("Minta direktori kerja sah dari gerbang `backend:tech-lead` "
                  "(format: backenddev/docs/<YYMMDDhhmm>-<slug>/, sudah diprovisi).")


# ============================================================ tiket analyst (`ticket_source`)
# Kontrak serah-terima: `tech-lead/references/gate-scope.md` bagian 4 B-2. Kartu menulis
# `AC-{n}`/`BR-{n}`; artefak backend merujuknya `TAC-{n}`/`TBR-{n}`. Subjek commit di
# `ticket_source_verdict` ditulis `analyst/skills/_common/ticket.py` (`approve`, `ref`) —
# ubah keduanya bersamaan bila formatnya berubah.

TICKET_PATH_RE = re.compile(r"analyst/tickets/\d{10}-([a-z0-9]+(?:-[a-z0-9]+)*)/TICKET\.md")
TICKET_AC_RE = re.compile(r"^- \*\*AC-(\d+)\*\*:")
TICKET_ELICIT_H2 = re.compile(r"^## +Catatan Elisitasi\s*$")
TICKET_ACTION = "Kembalikan ke `analyst:spec` (reopen → approve ulang); rantai engineer dilarang menyunting tiket."


def normalize_ticket_path(value: Optional[str]) -> str:
    rel = (value or "").strip().replace("\\", "/")
    return rel[2:] if rel.startswith("./") else rel


def ticket_card(text: str) -> str:
    """Kartu tiket: badan sesudah frontmatter sampai sebelum `## Catatan Elisitasi` (di luar fence)."""
    try:
        _, body = split_frontmatter(text)
    except FrontmatterError:
        body = normalize_text(text)
    lines = body.split("\n")
    stop = next((no - 1 for no, line in iter_outside_fences(body) if TICKET_ELICIT_H2.match(line)), len(lines))
    return "\n".join(lines[:stop])


def ticket_acs(text: str) -> List[int]:
    """Nomor `AC-{n}` kartu tiket, baris kanonik `- **AC-{n}**: …` di luar fence."""
    card = ticket_card(text)
    return sorted({int(m.group(1)) for _, line in iter_outside_fences(card) for m in [TICKET_AC_RE.match(line)] if m})


# Segel serah-terima tiket (09 E8) — salinan persis `analyst_lib.ticket_seal`; ketiganya ditagih sama
# oleh `tests/test_a1_ticket_source.py`. Ubah bersamaan.
TICKET_SEAL_FIELDS = ("type", "priority", "domain_terms")


def ticket_seal(text: str) -> str:
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    head: List[str] = []
    body = lines
    if lines and lines[0].rstrip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].rstrip() == "---"), None)
        if end is not None:
            head = [l.rstrip() for l in lines[1:end]
                    if re.match(r"^(%s)\s*:" % "|".join(TICKET_SEAL_FIELDS), l)]
            body = lines[end + 1:]
    norm = "\n".join(l.rstrip() for l in body).strip("\n")
    return hashlib.sha256(("\n".join(head) + "\n\x00\n" + norm).encode("utf-8")).hexdigest()[:16]


def sealed_verdict(root: Path, rel: str, fm: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
    """Vonis dari `approved_seal` bila tiket bersegel; None = tiket lama (vonis dari subjek commit).

    Segel menilai isi, bukan riwayat: suntingan sesudah READY → DRIFT di dalam maupun di luar git,
    dan commit suntingan yang meniru subjek kunci tidak lagi lolos.
    """
    seal = str(fm.get("approved_seal") or "-").strip()
    if seal in ("", "-"):
        return None
    try:
        now = ticket_seal((root / rel).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        return "FAIL", f"`{rel}` tak terbaca ({exc})", TICKET_ACTION
    if now != seal:
        return ("FAIL", f"isi `{rel}` berubah sesudah disetujui (segel {seal}, sekarang {now}) — DRIFT",
                TICKET_ACTION)
    return "PASS", f"{rel} READY bersegel {seal}", ""


def ticket_source_verdict(root: Path, value: Optional[str]) -> Tuple[str, str, str]:
    """`(status, ringkasan, tindakan)` untuk `ticket_source`: kosong → PASS; tiket wajib READY dan terkunci."""
    rel = normalize_ticket_path(value)
    if not rel:
        return "PASS", "bukan dari tiket analyst", ""
    m = TICKET_PATH_RE.fullmatch(rel)
    if not m:
        return ("FAIL", f"`{rel}` bukan path TICKET.md analyst (analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md)",
                "Minta path dari keluaran `analyst:spec` (`SPEC — READY · <ticketdir>/TICKET.md`).")
    path = root / rel
    if not path.is_file():
        return "FAIL", f"`{rel}` tidak ada di disk", "Minta path dari keluaran `analyst:spec`."
    try:
        fm, _ = read_frontmatter(path)
    except (OSError, UnicodeDecodeError, FrontmatterError) as exc:
        return "FAIL", f"`{rel}`: frontmatter tak terbaca ({exc})", TICKET_ACTION
    status, elicit = fm.get("status") or "-", fm.get("elicitation") or "-"
    if status != "READY" or elicit != "CLOSED":
        return ("FAIL", f"tiket berstatus `{status}`, elisitasi `{elicit}` — wajib `READY` dan `CLOSED`",
                "Selesaikan tiket di `analyst:spec` sampai READY.")
    sealed = sealed_verdict(root, rel, fm)
    if sealed:
        return sealed
    rc, inside = _git_out(root, "rev-parse", "--is-inside-work-tree")
    if rc != 0 or inside != "true":
        return "PASS", f"{rel} READY (bukan repo git, tiket tanpa segel — DRIFT tidak dinilai)", ""
    slug = m.group(1)
    locks = (f"docs(ticket): kunci TICKET {slug} READY", f"docs(ticket): ref TICKET {slug}")
    _, subject = _git_out(root, "log", "-1", "--format=%s", "--", rel)
    _, dirty = _git_out(root, "status", "--porcelain", "--", rel)
    if dirty:
        return "FAIL", f"`{rel}` disunting sesudah dikunci (belum di-commit) — DRIFT", TICKET_ACTION
    if subject not in locks:
        return ("FAIL", f"commit terakhir `{rel}` bersubjek `{subject or '(tidak ada)'}`, bukan kunci READY — DRIFT",
                TICKET_ACTION)
    return "PASS", f"{rel} READY terkunci ({subject})", ""


def ticket_carry_problems(root: Path, value: Optional[str], carried: str, out_of_scope: str) -> List[str]:
    """Tiap `AC-{n}` kartu wajib muncul sebagai `TAC-{n}` di `carried` (SC aktif) atau `out_of_scope`."""
    rel = normalize_ticket_path(value)
    if not rel:
        return []
    try:
        acs = ticket_acs(read_text(root / rel))
    except (OSError, UnicodeDecodeError):
        return [f"`ticket_source: {rel}` tidak terbaca"]
    if not acs:
        return [f"`ticket_source: {rel}` tanpa baris `- **AC-{{n}}**:` di kartunya"]
    both = carried + "\n" + out_of_scope
    cited = {int(n) for n in re.findall(r"\bTAC-(\d+)\b", both)}
    lost = [f"TAC-{n}" for n in acs if n not in cited]
    ghost = [f"TAC-{n}" for n in sorted(cited - set(acs))]
    p = [f"TAC tanpa SC pemikul maupun `## Out of Scope`: {', '.join(lost)}"] if lost else []
    if ghost:
        p.append(f"TAC tanpa `AC-{{n}}` di kartu tiket (rujukan hantu): {', '.join(ghost)}")
    return p


# ============================================================ profil & berkas plugin

@dataclass
class ProfileIndex:
    """Hasil `load_profile_index`: `data` terisi hanya bila `error` kosong."""
    data: Optional[Dict[str, Any]]
    error: str
    action: str
    dir: Path
    note: str = ""          # catatan MIGRATE bila profil dibaca dari lokasi lama
    kind: str = ""          # "", "missing", "foreign", "corrupt", "incomplete"

    @property
    def ok(self) -> bool:
        return not self.error


def load_profile_index(root: Path, required: Sequence[str] = REQUIRED_INDEX_KEYS) -> ProfileIndex:
    """`index.json` profil backend yang sah dan memuat `required` non-kosong.

    Lokasi dibaca lewat `resolve_profile_dir` (baru menang; lama hanya bila milik
    backend, disertai `note` MIGRATE). Profil milik plugin lain ditolak.
    """
    profile_dir, note = resolve_profile_dir(Path(root))
    index = profile_dir / "index.json"
    if not index.is_file():
        return ProfileIndex(None, f"Berkas {PROFILE_DIR_REL}/index.json tidak ditemukan",
                            "Jalankan skill `backend:profile` untuk membuat profil repositori.",
                            profile_dir, note, "missing")
    owner = foreign_owner(profile_dir)
    if owner:
        rel = profile_dir.relative_to(root).as_posix() if profile_dir.is_relative_to(root) else profile_dir
        return ProfileIndex(None, f"Profil di {rel}/ milik `{owner}`; bukan profil backend",
                            "Jangan membaca atau menimpa profil plugin lain; jalankan `backend:profile` "
                            f"(ditulis ke `{PROFILE_DIR_REL}/`).", profile_dir, note, "foreign")
    try:
        data = json.loads(read_text(index))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return ProfileIndex(None, f"Format JSON rusak pada index.json: {exc}",
                            "Perbaiki format JSON atau inisialisasi ulang via `backend:profile`.",
                            profile_dir, note, "corrupt")
    if not isinstance(data, dict):
        return ProfileIndex(None, "index.json bukan objek JSON",
                            "Perbaiki format JSON atau inisialisasi ulang via `backend:profile`.",
                            profile_dir, note, "corrupt")
    # Kunci wajib bertipe string (11 H22): `"source_root": ["src"]` dulu lolos `str(v)` lalu crash hilir.
    wrong = [k for k in required if k in data and data[k] is not None and not isinstance(data[k], str)]
    if wrong:
        return ProfileIndex(None, f"Field index.json wajib string: {', '.join(f'{k} ({type(data[k]).__name__})' for k in wrong)}",
                            "Perbaiki tipe field lewat `backend:profile` (REFRESH); dilarang menyuntingnya tangan.",
                            profile_dir, note, "incomplete")
    missing = [k for k in required if not str(data.get(k) or "").strip()]
    if missing:
        return ProfileIndex(None, f"Field kritis hilang/kosong di index.json: {', '.join(missing)}",
                            "Jalankan `backend:profile` untuk melengkapi field profil.",
                            profile_dir, note, "incomplete")
    return ProfileIndex(data, "", "", profile_dir, note)


# commands.md ditulis `backend:profile` sebagai baris `kunci: nilai [status]` yang dipisah
# ` · ` (profile/templates/profile-template.md bagian 9), bukan tabel. Butir list `- kunci: nilai`
# juga diterima.
_CMD_SEGMENT = re.compile(r"^\s*(?:[-*]\s+)?([a-z][a-z-]*)\s*:\s*(.*?)\s*$")
NOT_APPLICABLE = re.compile(r"^`?tidak berlaku\b", re.IGNORECASE)


def parse_commands(text: str) -> Dict[str, str]:
    """Peta `kunci -> nilai` dari commands.md (di luar code fence, tanpa heading); kunci pertama menang."""
    cmds: Dict[str, str] = {}
    for _, line in iter_outside_fences(normalize_text(text)):
        if line.lstrip().startswith("#"):
            continue
        for seg in line.split("·"):
            m = _CMD_SEGMENT.match(seg)
            if m and m.group(2):
                cmds.setdefault(m.group(1), m.group(2))
    return cmds


def plugin_file(*parts: str) -> Optional[Path]:
    """Berkas milik plugin ini (relatif `src/plugins/backend/`), atau None bila tidak ada.

    Tidak ada fallback ke `~/.gemini`, `~/.claude/plugins`, atau salinan repo
    pengembang: berkas yang hilang dari plugin terpasang harus terlihat hilang.
    """
    p = PLUGIN_ROOT.joinpath(*parts)
    return p if p.is_file() else None


def find_agent(name: str) -> Optional[Path]:
    return plugin_file("agents", f"{name}.md")


def stack_adapter_section(stack_id: str, heading: str, base: Optional[Path] = None) -> Tuple[Optional[Path], str]:
    """Adapter `skills/profile/stacks/<stack_id>.md` yang memuat seksi `heading` (mis. `## Failure signatures`).

    Kembalikan (path, "") bila berkas ada dan heading-nya hadir persis (di luar blok kode),
    selain itu (None, alasan). `base` hanya untuk test (menggantikan `PLUGIN_ROOT`).
    """
    rel = f"stacks/{stack_id}.md"
    path = (base or PLUGIN_ROOT) / "skills" / "profile" / "stacks" / f"{stack_id}.md"
    if not stack_id or not path.is_file():
        return None, f"Berkas adapter {rel} tidak ditemukan"
    if not has_heading(read_text(path), heading):
        return None, f"Adapter {rel} tanpa seksi `{heading}`"
    return path, ""


# ============================================================ keluaran

def format_text(skill: str, results: List[Dict[str, Any]], width: int = 32,
                header_suffix: str = "", banner: Optional[str] = None,
                entry_label: str = "", footer: Sequence[str] = ()) -> str:
    """Keluaran teks baku skrip prasyarat.

    `entry_label` (mis. "Titik masuk") mencetak `action` check non-FAIL juga;
    tanpanya hanya `Tindakan` check FAIL yang dicetak.
    """
    passed = sum(1 for r in results if r["status"] == "PASS")
    label = "PASS" if passed == len(results) else "FAIL"
    lines = [f"PRECONDITION CHECK: {skill} [{label}] ({passed}/{len(results)} passed){header_suffix}"]
    for r in results:
        lines.append(f"[{r['id']}] {r['name']:<{width}} : {r['status']} ({r['summary']})")
        if r.get("action") and (r["status"] == "FAIL" or entry_label):
            lines.append(f"    * {'Tindakan' if r['status'] == 'FAIL' else entry_label}: {r['action']}")
    lines.extend(footer)
    if banner:
        lines.insert(0, banner)
    return "\n".join(lines)


def to_json(root: Path, results: List[Dict[str, Any]], **extra: Any) -> str:
    """Urutan kunci: status, passed_count, total_count, root, extra…, checks."""
    passed = sum(1 for r in results if r["status"] == "PASS")
    payload: Dict[str, Any] = {
        "status": "PASS" if passed == len(results) else "FAIL",
        "passed_count": passed,
        "total_count": len(results),
        "root": str(root),
    }
    payload.update(extra)
    payload["checks"] = results
    return json.dumps(payload, indent=2)


def freshness_banner(freshness: Optional[Tuple[str, str]]) -> Optional[str]:
    if freshness and freshness[0] == "BASI":
        return f"[TERDEGRADASI] profil basi — {freshness[1]}"
    return None


def cli(main: Callable[[], Any]) -> Any:
    """Jaring terakhir skrip ber-CLI: berkas non-UTF-8 (09 E1), `--root` yang tidak ada, atau git yang tidak
    terpasang (11 H21) menjadi vonis FAIL terbaca (JSON bila `--json`), bukan traceback berstdout kosong."""
    try:
        return main()
    except UnicodeDecodeError as exc:
        name, msg = "Berkas terbaca", (f"berkas yang dibaca skrip ini bukan UTF-8 ({exc.reason} @ byte {exc.start}) "
                                       f"— pulihkan dari git atau simpan ulang sebagai UTF-8; jangan menebak isinya")
    except OSError as exc:
        name, msg = "Lingkungan terbaca", (f"{exc.strerror or exc} ({exc.filename or '—'}) — periksa `--root` dan "
                                           f"pastikan `git` terpasang di PATH")
    if "--json" in sys.argv:
        print(json.dumps({"status": "FAIL", "error": msg, "checks": [
            {"id": 0, "name": name, "status": "FAIL", "summary": msg, "action": ""}]},
            ensure_ascii=False, indent=2))
    else:
        print(f"FAIL: {msg}")
    return 1
