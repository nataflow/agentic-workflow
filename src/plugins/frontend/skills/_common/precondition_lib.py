#!/usr/bin/env python3
"""Helper bersama skrip prasyarat, validator, dan CLI rantai `frontend`.

Berisi **hanya** primitif yang byte-identik di seluruh pemakainya. Check itu
sendiri tetap tinggal di skripnya masing-masing: tiap skill menagih hal yang
berbeda, memberi pesan remediasi yang berbeda, dan menomori check-nya sendiri —
menyatukannya akan menyeragamkan hal yang memang seharusnya berbeda.

Isinya lima kelompok:

1. **Stack & profil** — pembungkus detektor stack di `hooks/detect.py` (fungsi
   yang sama dengan yang dipakai hook SessionStart), resolver direktori profil
   `.claude/profile/frontenddev/`, pembaca field `stack` profil, dan uji izin
   tulis. Dua detektor yang berselisih menghasilkan repo yang lolos gate tetapi
   ditolak skrip prasyarat tanpa satu pun pesan yang menyebut sebabnya.
2. **Git & frontmatter** — akar repo, pemanggil git, satu parser frontmatter
   (`split_frontmatter`) untuk **semua** skrip termasuk validator, penyaring
   laci `.explore/`, dan bukti `DONE` dari commit kode. Satu parser berarti status
   artefak yang sama tidak pernah divonis berbeda oleh dua gerbang.
3. **Lane & sections** — enum lane berakar, nilai `sections`, dan invarian
   pasangan keduanya. Ketiganya dibaca dari frontmatter `TASK.md`, bukan
   disimpulkan dari berkas yang kebetulan ada.
4. **Ledger `## Chain` dan `## Riwayat Rantai`** — pembaca/penulis baris ledger
   dan kejadian Riwayat (Langkah 24: dokumen taskdir tidak di-commit, jadi materai
   approve, plafon, dan epoch dibaca dari Riwayat di `TASK.md`), uji keutuhan
   konten yang disetujui (drift), dan penghitung plafon (revisi, re-entry,
   eskalasi). CLI-nya `chain.py`; hilir memakai `check_chain_rows`.
5. **Blok check & laporan** — check yang pesannya sama persis di banyak
   gerbang, plus format laporan teks/JSON baku.

Zero external dependencies (Python Standard Library only).
"""

import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs_git as _docs_git  # noqa: E402
from verify_scope import SIDIK_FIELD  # noqa: E402

KNOWN_STACKS = ("react-vite", "react-native", "sveltekit", "svelte-vite")
TASKDIR_PATTERN = re.compile(r"^frontenddev/docs/\d{10}-[a-z0-9-]+$")
PROFILE_FILES = ("index.json", "stack.md", "structure.md", "surface-map.md",
                 "invariants.md", "commands.md", "layer-adoption.md", "visual.md",
                 "drift.md", "manual-notes.md")
STACKS_DIR = Path(__file__).resolve().parents[1] / "profile" / "stacks"
BRIEF_GLOB = "brief-*.md"


# ================================================================ 1. stack & profil


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
    """
    anchor = nearest_existing_ancestor(path)
    if not anchor.is_dir():
        return False, f"{anchor} ada tetapi bukan direktori"
    if not os.access(anchor, os.W_OK | os.X_OK):
        return False, f"{anchor} tidak memiliki izin tulis"
    return True, str(anchor)


# Deteksi stack tinggal di `hooks/detect.py` (identik di kedua plugin) — satu
# implementasi untuk hook dan skrip, sehingga vonis keduanya tidak bisa berselisih.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
import detect as _detect  # noqa: E402

# Tiap plugin engineer punya direktori profilnya sendiri. `.claude/profile/`
# (tanpa subdirektori) adalah lokasi lama yang hanya dibaca selama masa transisi
# dan selalu disertai catatan MIGRATE.
PLUGIN = "frontenddev"
PROFILE_DIR_REL = f".claude/profile/{PLUGIN}"
LEGACY_PROFILE_DIR_REL = ".claude/profile"
DEFAULT_PROFILE_DIR = PROFILE_DIR_REL


def resolve_profile_dir(root: Path) -> Tuple[Path, str]:
    """(direktori profil yang dibaca, catatan untuk laporan prasyarat).

    Lokasi baru selalu menang. Lokasi lama dipakai hanya bila `index.json`-nya
    milik plugin ini (field `plugin`, atau `stack` anggota daftar frontend),
    dan selalu disertai catatan MIGRATE. Profil milik plugin lain tidak pernah
    dikembalikan: skrip melihatnya sebagai profil yang tidak ada.
    """
    own = root / PROFILE_DIR_REL
    if (own / "index.json").exists():
        return own, ""
    prof = _detect.read_profile(root, PLUGIN)
    if prof.location == "legacy" and prof.state not in ("OTHER_OWNER", "ABSENT", "INVALID_JSON"):
        return root / LEGACY_PROFILE_DIR_REL, (
            "profil frontend masih di lokasi lama `.claude/profile/`; "
            "jalankan `frontend:profile` mode MIGRATE")
    return own, ""


def profile_dir_for(root: Path, override: Optional[str] = None) -> Path:
    """Direktori profil skrip: `--profile-dir` bila diberikan, selain itu resolver."""
    return (root / override) if override else resolve_profile_dir(root)[0]


def is_legacy_profile_dir(profile_dir: Path) -> bool:
    """Benar bila `profile_dir` adalah lokasi lama `<root>/.claude/profile`."""
    return profile_dir.parts[-2:] == (".claude", "profile")


def detect_stack(manifest: Path) -> Optional[str]:
    """`<stack-id>` dari satu `package.json`, atau `None` (lihat `detect.frontend_from_package`)."""
    return _detect.frontend_from_package(manifest)[0]


def is_next(manifest: Path) -> bool:
    return _detect.frontend_from_package(manifest)[1] == "next"


def out_of_scope_reason(manifest: Path) -> str:
    """`next` | `cra` | `react-tanpa-vite` | `svelte-tanpa-vite` | `manifest-rusak` | ''."""
    return _detect.frontend_from_package(manifest)[1]


def candidate_manifests(root: Path) -> list:
    """Manifest yang diperiksa hook dan skrip: urutan `detect.candidate_dirs`."""
    return [d / "package.json" for d in _detect.candidate_dirs(root) if (d / "package.json").is_file()]


def read_profile_stack(profile_dir: Path) -> str:
    """Baca field `stack` dari `<profile_dir>/index.json`, atau string kosong."""
    data, _state = _detect.read_index(profile_dir / "index.json")
    if data is None:
        return ""
    stack = data.get("stack")
    return stack.strip() if isinstance(stack, str) else ""


def profile_owner(profile_dir: Path) -> str:
    """Pemilik profil di `<profile_dir>/index.json` (`plugin`, atau keanggotaan `stack`)."""
    data, _state = _detect.read_index(profile_dir / "index.json")
    return _detect.owner_of(data) if data is not None else ""


def load_profile(profile_dir: Path, required: Tuple[str, ...]) -> Tuple[str, List[str]]:
    """Kembalikan `(stack, berkas_wajib_yang_hilang)` untuk satu profil."""
    missing = [f for f in required if not (profile_dir / f).is_file()]
    return read_profile_stack(profile_dir), missing


def adapter_path(stack: str) -> Path:
    """Path adapter `skills/profile/stacks/<stack>.md` milik plugin ini."""
    return STACKS_DIR / f"{stack}.md"


PROFILE_TPB = re.compile(r"^-\s*`typecheck-per-brief`\s*:\s*`?\s*(ya|tidak)\b", re.MULTILINE)
ADAPTER_TPB = re.compile(r"^\|\s*typecheck-per-brief\s*\|\s*`?(ya|tidak)\b", re.MULTILINE)


def typecheck_per_brief(profile_dir: Path, stack: str) -> Tuple[str, str]:
    """`(nilai, sumber)` gerbang kompilasi per-brief — satu resolver untuk seluruh pembaca.

    Profil menang bila `commands.md` menulis barisnya (keputusan berbasis durasi
    terukur di repo itu, `stacks/_CONTRACT.md` §2); selain itu baris `## Commands`
    adapter; selain itu `tidak`.
    """
    try:
        m = PROFILE_TPB.search((profile_dir / "commands.md").read_text(encoding="utf-8"))
        if m:
            return m.group(1), "profil"
    except (OSError, UnicodeDecodeError):
        pass
    try:
        m = ADAPTER_TPB.search(adapter_path(stack).read_text(encoding="utf-8")) if stack else None
        if m:
            return m.group(1), "adapter"
    except (OSError, UnicodeDecodeError):
        pass
    return "tidak", "bawaan"


# ================================================================ 2. git & frontmatter


def find_repo_root() -> Path:
    """Akar worktree git, atau cwd bila bukan repo git."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL, universal_newlines=True,
        ).strip()
        if out:
            return Path(out)
    except Exception:
        pass
    return Path.cwd()


def git(root: Path, *args: str) -> str:
    """Jalankan git di `root`; kegagalan dikembalikan sebagai string kosong."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            stderr=subprocess.DEVNULL, universal_newlines=True,
        )
    except Exception:
        return ""


def git_ok(root: Path, *args: str) -> Tuple[bool, str]:
    """Jalankan git dan kembalikan `(sukses, stdout+stderr)` — untuk operasi tulis."""
    proc = subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, universal_newlines=True)
    return proc.returncode == 0, proc.stdout


def normalize_taskdir(taskdir: str) -> str:
    """Buang segmen kosong dan `.`; segmen `..` **dipertahankan** supaya `TASKDIR_PATTERN` menolaknya.

    Versi lama (`.replace("./", "")`) merusak `../` menjadi `.`-sisa, sehingga path yang keluar repo
    kebetulan gagal alih-alih ditolak dengan sengaja (09 E16).
    """
    return "/".join(p for p in taskdir.strip().split("/") if p not in ("", "."))


def strip_explore_scratch(status_out: str) -> str:
    """Buang baris `git status --porcelain` yang menunjuk laci `.explore/`/`.frontenddev/`.

    Laci itu zona kerja, bukan artefak rantai: tidak pernah di-stage maupun
    di-commit, sehingga kehadirannya tidak boleh dihitung working tree kotor.
    Hanya laci berjangkar (12 J4, sama dengan `verify_scope.is_scratch`):
    `.frontenddev/` di akar repo dan `frontenddev/docs/[<taskdir>/].explore/`;
    `src/.explore/x.ts` adalah kode biasa dan tetap terhitung kotor.
    """
    kept = []
    for line in status_out.splitlines():
        if not line.strip():
            continue
        path = line[3:] if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ")[-1]
        path = path.strip().strip('"')
        seg = path.strip("/").split("/")
        if seg[0] == ".frontenddev" or (seg[:2] == ["frontenddev", "docs"] and ".explore" in seg[2:4]):
            continue
        kept.append(line)
    return "\n".join(kept)


def is_git_repo(root: Path) -> bool:
    """Benar hanya bila git benar-benar dapat membaca repo di `root`."""
    return git(root, "rev-parse", "--is-inside-work-tree").strip() == "true"


class GitError(RuntimeError):
    """git tidak dapat membaca keadaan tree (index rusak, git absen, izin)."""


def git_status(root: Path, *paths: str) -> str:
    """`git status --porcelain` apa adanya; `GitError` bila git gagal (12 J17).

    `git()` menelan kegagalan jadi string kosong — untuk status, kosong berarti "bersih", jadi index
    rusak dulu terbaca "nol perubahan menggantung". Selaras `dirty_paths` backend.
    """
    try:
        proc = subprocess.run(["git", "-C", str(root), "status", "--porcelain", *(["--", *paths] if paths else [])],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitError(str(exc)) from exc
    if proc.returncode != 0:
        raise GitError((proc.stderr.strip().splitlines() or [f"exit {proc.returncode}"])[-1])
    return proc.stdout


def dirty_lines(root: Path) -> List[str]:
    """Baris `git status --porcelain` di luar laci kerja; `GitError` bila tree tak terbaca."""
    out = strip_explore_scratch(git_status(root))
    return [l for l in out.splitlines() if l.strip()]


def as_list(value: Any) -> List[str]:
    """Nilai frontmatter berbentuk list; skalar dibungkus, kosong jadi `[]`."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    value = str(value or "").strip()
    return [value] if value else []


def is_committed(root: Path, rel: str) -> bool:
    """Benar bila `rel` pernah di-commit **dan** tidak punya perubahan menggantung.

    Hanya untuk dokumen tingkat repo (mis. `finding_source` di `frontenddev/reviews/`): dokumen taskdir tidak
    pernah di-commit (Langkah 24). Status yang tak terbaca bukan "tanpa perubahan" (12 J17): hasilnya False.
    """
    if not git(root, "log", "-1", "--format=%h", "--", rel).strip():
        return False
    try:
        return not git_status(root, rel).strip()
    except GitError:
        return False


def carries_code(root: Path, sha: str) -> bool:
    """Commit menyentuh berkas di luar dokumen rantai (`frontenddev/`, `.claude/`)."""
    return bool(git(root, "show", "--name-only", "--format=", sha, "--", ".", ":(exclude)frontenddev",
                    ":(exclude).claude").strip())


def done_landed(root: Path, brief_rel: str) -> str:
    """Sha pendek commit unit brief `DONE` yang membawa kode, atau kosong (24 K7, padanan 09 E18 dan 12 J15).

    Dokumen taskdir tidak di-commit (Langkah 24), jadi transisi `→ DONE` tidak lagi ada di riwayat git. Buktinya
    kini dua: status `DONE` di disk, dan commit `<type>(<slug>): implement unit <NN>` di `base_commit..HEAD` yang
    membawa kode. `DONE` yang diketik tangan tanpa commit kode tetap tertangkap. Subjek yang diketik di commit
    tanpa kode juga tidak dihitung.
    """
    path = root / brief_rel
    m = re.match(r"^brief-(\d{2})-", path.name)
    if not m or read_status(path) != "DONE":
        return ""
    taskdir_rel = Path(brief_rel).parent.as_posix()
    base = task_root_sha(root, taskdir_rel)
    if not base:
        return ""
    rx = re.compile(rf"^[a-z]+!?\({re.escape(taskdir_slug(taskdir_rel))}\)!?: implement unit {m.group(1)}\b")
    for line in git(root, "log", "--format=%H %s", f"{base}..HEAD").splitlines():
        sha, _, subject = line.partition(" ")
        if rx.match(subject) and carries_code(root, sha):
            return sha[:7]
    return ""


class FrontmatterError(ValueError):
    pass


BOM = chr(0xFEFF)
_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def fenced_mask(lines: List[str]) -> List[bool]:
    """Per baris: True bila baris itu pagar atau isi blok kode berpagar ``` / ~~~.

    Panjang pagar dihormati: blok ```` ```` ```` yang memuat ```` ``` ```` baru ditutup
    oleh pagar sejenis yang sama panjang atau lebih panjang tanpa info string.
    """
    mask: List[bool] = []
    fence = ""
    for line in lines:
        m = _FENCE.match(line)
        if m and not fence:
            fence = m.group(1)
            mask.append(True)
            continue
        if m and fence:
            tok = m.group(1)
            if tok[0] == fence[0] and len(tok) >= len(fence) and not line.strip()[len(tok):].strip():
                fence = ""
                mask.append(True)
                continue
        mask.append(bool(fence))
    return mask


def outside_fences(lines: List[str]) -> List[str]:
    """Baris di luar blok kode berpagar (baris pagar ikut dibuang).

    Log build atau perintah reproduksi ber-`# komentar` di dalam blok kode bukan heading.
    """
    return [l for l, fenced in zip(lines, fenced_mask(lines)) if not fenced]


def split_frontmatter(text: str, strict: bool = False) -> Tuple[Dict[str, Any], str]:
    """Parse subset YAML frontmatter → `(data, body)`.

    Mendukung skalar, list inline `[a, b]`, `[]`/`{}` kosong, list blok `- x`,
    dan komentar `#`. `strict=True` melempar `FrontmatterError` bila pagar `---`
    tidak lengkap atau kunci muncul lebih dari sekali — dipakai validator, yang
    harus memvonis berkas rusak sebagai rusak, bukan sebagai berkas tanpa field.
    BOM (U+FEFF) di awal berkas dibuang lebih dulu: pagar `---` sesudah BOM tetap pagar.

    Kunci ganda (12 J31, keputusan 05-3): mode toleran tidak memilih salah satu nilai, melainkan
    mengisi kunci itu dengan `DUPLICATE_KEY` — nilai yang tidak pernah sah di field mana pun, sehingga
    pembaca status/lane/list gagal tertutup tanpa crash.
    """
    text = text.lstrip(BOM)
    if not text.startswith("---"):
        if strict:
            raise FrontmatterError("frontmatter tidak dibuka dengan `---`")
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        if strict:
            raise FrontmatterError("frontmatter tidak ditutup dengan `---`")
        return {}, text
    head, body = text[3:end], text[end + 4:]
    data: Dict[str, Any] = {}
    duplicated: Set[str] = set()
    current: Optional[str] = None
    for raw in head.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith(("  - ", "- ")) and current:
            data.setdefault(current, [])
            if isinstance(data[current], list):
                data[current].append(line.split("- ", 1)[1].strip().strip('"').strip("'"))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key in data or key in duplicated:
            if strict:
                raise FrontmatterError(f"kunci frontmatter `{key}` muncul lebih dari sekali")
            duplicated.add(key)
            data[key] = DUPLICATE_KEY
            current = None
            continue
        if value == "":
            data[key] = []
            current = key
        elif value in ("[]", "{}"):
            data[key] = []
            current = None
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
            current = None
        else:
            data[key] = value.strip('"').strip("'")
            current = None
    return data, body


DUPLICATE_KEY = "(kunci frontmatter ganda)"


def parse_frontmatter(text: str) -> Dict[str, Any]:
    """Frontmatter saja, versi toleran (berkas tanpa pagar → dict kosong)."""
    return split_frontmatter(text)[0]


NOT_UTF8 = "(bukan UTF-8)"


def undecodable(directory: Path, exc: UnicodeDecodeError) -> str:
    """Ringkasan untuk validator yang terhenti `UnicodeDecodeError`: berkas mana di `directory` yang rusak.

    Pengecualian dekode tidak membawa nama berkas; nama itu dicari ulang dengan membaca tiap
    `*.md` di taskdir, supaya vonis menunjuk berkas yang harus dipulihkan.
    """
    bad = []
    for p in sorted(directory.glob("*.md")) if directory.is_dir() else []:
        try:
            p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bad.append(f"`{p.name}`")
        except OSError:
            pass
    where = ", ".join(bad) if bad else "berkas yang dibaca (profil atau dokumen lain)"
    return f"{where} {NOT_UTF8} ({exc.reason} @ byte {exc.start})"


UNDECODABLE_ACTION = "Simpan ulang berkasnya sebagai UTF-8 (pulihkan dari git bila rusak); jangan menebak isinya."


def read_status(path: Path, field: str = "status") -> str:
    """Nilai satu field frontmatter sebagai string, atau kosong.

    Berkas non-UTF-8 → `NOT_UTF8`, bukan kosong: nilai itu tidak pernah sama dengan status sah
    mana pun, sehingga pemanggil gagal tertutup dengan pesan yang menyebut sebabnya, alih-alih
    memperlakukan berkas rusak sebagai berkas absen. Kunci ganda → `DUPLICATE_KEY` (12 J31), dengan
    alasan yang sama.
    """
    try:
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return NOT_UTF8
    except OSError:
        return ""
    value = fm.get(field, "")
    return value.strip() if isinstance(value, str) else ""


def newline_of(path: Path) -> str:
    r"""Gaya line ending mayoritas berkas: `\r\n` atau `\n` (default untuk berkas baru)."""
    try:
        data = path.read_bytes()
    except OSError:
        return "\n"
    crlf = data.count(b"\r\n")
    return "\r\n" if crlf > data.count(b"\n") - crlf else "\n"


def write_keep_newline(path: Path, text: str) -> None:
    r"""Tulis `text` (ber-`\n`, hasil `read_text`) dengan gaya line ending berkas yang ditimpa."""
    newline = newline_of(path)
    with open(path, "w", encoding="utf-8", newline=newline) as fh:   # `Path.write_text(newline=)` baru ada di 3.10
        fh.write(text)


def set_frontmatter_field(text: str, key: str, value: str) -> str:
    """Ganti (atau sisipkan di akhir frontmatter) satu field skalar.

    BOM di awal berkas dipertahankan, supaya diff suntingan tidak menyentuh baris pertama.
    """
    bom = BOM if text.startswith(BOM) else ""
    text = text[len(bom):]
    if not text.startswith("---"):
        raise FrontmatterError("frontmatter tidak dibuka dengan `---`")
    end = text.find("\n---", 3)
    if end == -1:
        raise FrontmatterError("frontmatter tidak ditutup dengan `---`")
    head = text[3:end]
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    if pattern.search(head):
        head = pattern.sub(f"{key}: {value}", head, count=1)
    else:
        head = head.rstrip("\n") + f"\n{key}: {value}"
    return bom + "---" + head + text[end:]


# Pagar untuk pemotong seksi: berindentasi bebas (blok kode di dalam butir list tetap blok kode), ``` dan
# ~~~, panjang dihormati seperti `fenced_mask` (12 J40).
_SECTION_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def section_lines(body: str, heading: str) -> List[str]:
    """Badan satu heading (`## X`) sampai heading setingkat atau lebih tinggi berikutnya.

    Heading di dalam blok kode berpagar ``` atau ~~~ bukan heading (12 J40).
    """
    level = len(heading) - len(heading.lstrip("#"))
    out: List[str] = []
    capturing = False
    fence = ""
    for line in body.splitlines():
        m = _SECTION_FENCE.match(line)
        if m and not fence:
            fence = m.group(1)
            in_fence = True
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                and not line.strip()[len(m.group(1)):].strip():
            fence, in_fence = "", True               # baris pagar penutup masih bagian blok
        else:
            in_fence = bool(fence)
        if not in_fence and line.strip() == heading.strip():
            capturing = True
            continue
        if capturing:
            if not in_fence and line.startswith("#"):
                hashes = len(line) - len(line.lstrip("#"))
                if 0 < hashes <= level:
                    break
            out.append(line)
    return out


_ESCAPED_PIPE = "\x00"


def table_cells(line: str) -> List[str]:
    r"""Sel satu baris tabel markdown; `\|` adalah pipa di dalam sel, bukan pemisah (12 J26).

    Pipa pembuka dan penutup opsional (GFM). Kosong bila baris bukan baris tabel.
    """
    s = line.strip()
    if "|" not in s.replace("\\|", ""):
        return []
    s = s.replace("\\|", _ESCAPED_PIPE)
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip().replace(_ESCAPED_PIPE, "|") for c in s.split("|")]


def is_table_rule(cells: List[str]) -> bool:
    """Baris pemisah header `|---|:--:|`."""
    return bool(cells) and all(c and set(c) <= set("-: ") for c in cells)


AC_ID = re.compile(r"^`?(AC-\d+)`?$")
AC_TOKEN = re.compile(r"\bAC-\d+\b")
AC_SECTION = "## 5. Acceptance Criteria"


def ac_rows(body: str) -> Tuple[List[Tuple[str, List[str]]], List[str]]:
    """Satu pengurai tabel Acceptance Criteria `CONTRACT.md` untuk `validate_doc`, `validate_briefs`, dan
    `validate_review` (12 J28) → `([(AC-n, [Skenario, Cara verifikasi, Sumber, ...])], masalah)`.

    Baris ber-`AC-n` di kolom pertama dengan kurang dari empat sel tetap dikembalikan (penomoran tetap
    dinilai) dan dicatat sebagai masalah; baris tabel yang menyebut `AC-n` di luar kolom pertama tidak
    terurai — keduanya masalah, bukan baris yang dilewati diam-diam.
    """
    rows: List[Tuple[str, List[str]]] = []
    problems: List[str] = []
    for line in section_lines(body, AC_SECTION):
        cells = table_cells(line)
        if not cells or is_table_rule(cells):
            continue
        m = AC_ID.match(cells[0])
        if not m:
            if AC_TOKEN.search(line):
                problems.append(f"baris AC tak terurai (kolom pertama bukan `AC-{{n}}`): {line.strip()[:80]}")
            continue
        rows.append((m.group(1), cells[1:]))
        if len(cells) < 4:
            problems.append(f"`{m.group(1)}`: baris {len(cells)} sel, wajib 4 (`AC-{{n}} | Skenario | "
                            "Cara verifikasi | Sumber`)")
    return rows, problems


def inside_root(root: Path, rel: str) -> bool:
    """`rel` path relatif yang tetap di dalam `root` sesudah di-resolve (12 J29).

    Path absolut, segmen `..`, atau tautan simbolik yang keluar root ditolak: rantai hanya menyentuh
    dan hanya membuktikan dengan berkas repo ini.
    """
    rel = rel.strip()
    if not rel or rel.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", rel):
        return False
    if ".." in re.split(r"[\\/]", rel):
        return False
    try:
        (Path(root) / rel).resolve().relative_to(Path(root).resolve())
    except (ValueError, OSError, RuntimeError):
        return False
    return True


# ---------------------------------------------------------------- tiket analyst (`ticket_source`)
# Kontrak serah-terima: `lead/SKILL.md` `## Parameter` dan `task/SKILL.md` Phase 3 butir 6. Kartu
# menulis `AC-{n}`/`BR-{n}`; artefak frontend merujuknya `TAC-{n}`/`TBR-{n}`. Subjek commit di
# `ticket_source_verdict` ditulis `analyst/skills/_common/ticket.py` (`approve`, `ref`) — ubah
# keduanya bersamaan bila formatnya berubah.

TICKET_PATH_RE = re.compile(r"analyst/tickets/\d{10}-([a-z0-9]+(?:-[a-z0-9]+)*)/TICKET\.md")
TICKET_AC_RE = re.compile(r"^- \*\*AC-(\d+)\*\*:")
TICKET_ELICIT_H2 = re.compile(r"^## +Catatan Elisitasi\s*$")
TICKET_ACTION = "Kembalikan ke `analyst:spec` (reopen → approve ulang); rantai engineer dilarang menyunting tiket."


def normalize_ticket_path(value: Any) -> str:
    rel = str(value or "").strip().replace("\\", "/")
    return rel[2:] if rel.startswith("./") else rel


def ticket_card(text: str) -> List[str]:
    """Baris kartu tiket di luar fence: sesudah frontmatter sampai sebelum `## Catatan Elisitasi`."""
    _, body = split_frontmatter(text)
    lines = body.splitlines()
    card: List[str] = []
    for line, fenced in zip(lines, fenced_mask(lines)):
        if not fenced and TICKET_ELICIT_H2.match(line):
            break
        if not fenced:
            card.append(line)
    return card


def ticket_acs(text: str) -> List[int]:
    """Nomor `AC-{n}` kartu tiket, baris kanonik `- **AC-{n}**: …`."""
    return sorted({int(m.group(1)) for line in ticket_card(text) for m in [TICKET_AC_RE.match(line)] if m})


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


def ticket_source_verdict(root: Path, value: Any) -> Tuple[str, str, str]:
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
        fm, _ = split_frontmatter(path.read_text(encoding="utf-8"), strict=True)
    except (OSError, UnicodeDecodeError, FrontmatterError) as exc:
        return "FAIL", f"`{rel}`: frontmatter tak terbaca ({exc})", TICKET_ACTION
    status, elicit = str(fm.get("status") or "-"), str(fm.get("elicitation") or "-")
    if status != "READY" or elicit != "CLOSED":
        return ("FAIL", f"tiket berstatus `{status}`, elisitasi `{elicit}` — wajib `READY` dan `CLOSED`",
                "Selesaikan tiket di `analyst:spec` sampai READY.")
    sealed = sealed_verdict(root, rel, fm)
    if sealed:
        return sealed
    if not is_git_repo(root):
        return "PASS", f"{rel} READY (bukan repo git, tiket tanpa segel — DRIFT tidak dinilai)", ""
    slug = m.group(1)
    locks = (f"docs(ticket): kunci TICKET {slug} READY", f"docs(ticket): ref TICKET {slug}")
    subject = git(root, "log", "-1", "--format=%s", "--", rel).strip()
    if git(root, "status", "--porcelain", "--", rel).strip():
        return "FAIL", f"`{rel}` disunting sesudah dikunci (belum di-commit) — DRIFT", TICKET_ACTION
    if subject not in locks:
        return ("FAIL", f"commit terakhir `{rel}` bersubjek `{subject or '(tidak ada)'}`, bukan kunci READY — DRIFT",
                TICKET_ACTION)
    return "PASS", f"{rel} READY terkunci ({subject})", ""


def ticket_carry_problems(root: Path, value: Any, carried: str, out_of_scope: str) -> List[str]:
    """Tiap `AC-{n}` kartu wajib muncul sebagai `TAC-{n}` di `carried` (SC aktif) atau `out_of_scope`."""
    rel = normalize_ticket_path(value)
    if not rel:
        return []
    try:
        acs = ticket_acs((root / rel).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return [f"`ticket_source: {rel}` tidak terbaca"]
    if not acs:
        return [f"`ticket_source: {rel}` tanpa baris `- **AC-{{n}}**:` di kartunya"]
    cited = {int(n) for n in re.findall(r"\bTAC-(\d+)\b", carried + "\n" + out_of_scope)}
    lost = [f"TAC-{n}" for n in acs if n not in cited]
    ghost = [f"TAC-{n}" for n in sorted(cited - set(acs))]
    p = [f"TAC tanpa SC pemikul maupun `## Out of Scope`: {', '.join(lost)}"] if lost else []
    if ghost:
        p.append(f"TAC tanpa `AC-{{n}}` di kartu tiket (rujukan hantu): {', '.join(ghost)}")
    return p


SC_LINE = re.compile(r"^- \[[ xX]\] \*\*(SC-\d+)\*\*:(.*)$")


def sc_ids(task_text: str) -> Dict[str, str]:
    """`{SC-n: baris}` dari teks `TASK.md` apa adanya."""
    _, body = split_frontmatter(task_text)
    out: Dict[str, str] = {}
    for line in section_lines(body, "## Success Criteria"):
        m = SC_LINE.match(line.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def success_criteria(task_path: Path) -> Dict[str, str]:
    """`{SC-n: baris}` **aktif** dari `## Success Criteria` `TASK.md`, urut; kosong bila tidak terbaca.

    Butir yang digugurkan amandemen akar (`~~teks~~ — gugur: <alasan>`) mempertahankan
    nomornya tetapi tidak lagi ditagih pemikul hilir (AC, `fulfills`, vonis review).
    """
    try:
        _, body = split_frontmatter(task_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}
    out: Dict[str, str] = {}
    for line in section_lines(body, "## Success Criteria"):
        m = SC_LINE.match(line.strip())
        if m and not re.search(r"—\s*gugur:", m.group(2)):
            out[m.group(1)] = m.group(2).strip()
    return out


VERIFY_MARK = "— verifikasi:"
_MANUAL = re.compile(r"`?\s*qa\s+manual\s*:", re.IGNORECASE)


def measure_of(sc_text: str) -> str:
    """Teks alat ukur sesudah penanda `— verifikasi:` pertama; kosong bila tidak ada."""
    _, sep, tail = sc_text.partition(VERIFY_MARK)
    return tail.strip() if sep else ""


def is_manual(sc_text: str) -> bool:
    """SC beralat ukur `QA manual:` — huruf besar-kecil dan spasi bebas, hanya di posisi alat ukur.

    Satu aturan untuk `validate_task`, `validate_review`, dan `validate_report`:
    `qa manual:` yang lolos akar tidak boleh ditolak reviewer atau dilupakan laporan.
    """
    return bool(_MANUAL.match(measure_of(sc_text)))


def is_manual_cell(how: str) -> bool:
    """Sel *Cara verifikasi* AC `CONTRACT.md` diawali `QA manual:` (aturan huruf yang sama dengan `is_manual`)."""
    return bool(_MANUAL.match(how.strip()))


INLINE_CODE = re.compile(r"`[^`\n]*`")
# TODO/TBD/FIXME hanya huruf besar (penanda penulis di template); frasa Indonesia tak peka huruf.
# Fitur bernama "todo list" bukan placeholder.
WORD_PLACEHOLDER = re.compile(r"\b(?:TBD|TODO|FIXME)\b|(?i:\b(?:diisi nanti|isi nanti)\b)")
# Slot `<...>`: dibuka huruf/underscore tepat sesudah `<`, ditutup non-spasi non-`/` tepat
# sebelum `>`. Operator perbandingan (`< 300 ms dan item > 0`) dan JSX swa-tutup
# (`<Spinner />`) gugur di sini.
PLACEHOLDER_ANGLE = re.compile(r"<(?=[A-Za-z_])([^<>\n]{1,80}?)(?<=[^\s/])>")
# Sintaks tipe/atribut (literal objek, anotasi, union, atribut JSX) tidak pernah muncul
# di slot template berbahasa Indonesia.
_TS_SYNTAX = re.compile(r"[{}:;=|]")
SLOT_WORDS = frozenset("""
slug stack stack-id stack_id feat feature taskdir unit unit-slug nn mm n nama path berkas file
layer layar perintah command sha commit tanggal versi judul deskripsi angka nilai id elemen field
skenario langkah alasan keputusan platform rute entitas
""".split())


def _is_slot(content: str) -> bool:
    """Isi `<...>` di prosa: kosakata slot template, atau frasa multi-kata tanpa sintaks tipe."""
    content = content.strip()
    if content.lower() in SLOT_WORDS:
        return True
    if _TS_SYNTAX.search(content):
        return False
    return " " in re.sub(r",\s+", ",", content)


def find_placeholders(line: str) -> List[str]:
    """Token placeholder yang tersisa di satu baris (kosong bila bersih) — satu aturan tiga validator.

    Di dalam inline code hanya slot berkosakata (`` `src/features/<slug>/api.ts` ``) yang
    ditolak; backtick lazim membungkus JSX dan generik (`` `<Nama Komponen>` `` lolos).
    Di prosa: `TBD`/`TODO`/`FIXME`/`diisi nanti`, dan `<...>` yang `_is_slot`. Tag JSX
    (`<OrderRow>`, `<Skeleton />`), generik TS (`Record<string, string>`), dan operator
    perbandingan bukan placeholder.
    """
    hits: List[str] = []
    for m in INLINE_CODE.finditer(line):
        for a in PLACEHOLDER_ANGLE.finditer(m.group(0)):
            if a.group(1).strip().lower() in SLOT_WORDS:
                hits.append(a.group(0))
    prose = INLINE_CODE.sub(" ", line)
    hits += [m.group(0) for m in WORD_PLACEHOLDER.finditer(prose)]
    hits += [m.group(0) for m in PLACEHOLDER_ANGLE.finditer(prose) if _is_slot(m.group(1))]
    return hits


PLACEHOLDER_ACTION = ("Ganti `TBD`/`TODO`/`FIXME`/`diisi nanti`/slot `<…>` dengan isi nyata. JSX (`<X />`), "
                      "generik TS, dan operator perbandingan bukan placeholder.")


# ================================================================ 3. lane & sections

ROOTED_LANES = ("FULL_PIPELINE", "FAST_FORWARD", "REFACTOR_ARCH", "HOTFIX_MINOR")
MINOR_LANE = "HOTFIX_MINOR"
SECTION_VALUES = ("architecture", "flow", "ui")


def parse_sections(raw: Any) -> List[str]:
    """Pecah nilai `sections` (`flow,ui`, `flow ui`, `flow|ui`, `-`, atau list)."""
    if isinstance(raw, list):
        raw = ",".join(str(r) for r in raw)
    parts = re.split(r"[\s,|]+", (raw or "").strip())
    return [p for p in parts if p and p != "-"]


def lane_sections_problem(lane: str, sections: List[str]) -> str:
    """Pesan pelanggaran invarian pasangan `(lane, sections)`, atau kosong bila sah.

    - `HOTFIX_MINOR` ⇔ `sections` kosong (tanpa dokumen hulu, tanpa kontrak).
    - `FAST_FORWARD`/`REFACTOR_ARCH` ⇒ tepat `architecture` (kontrak tanpa FLOW/UI).
    - `FULL_PIPELINE` ⇒ memuat `flow` atau `ui` — tanpa keduanya lane-nya
      sebenarnya `FAST_FORWARD`/`REFACTOR_ARCH`.
    """
    unknown = [s for s in sections if s not in SECTION_VALUES]
    if unknown:
        return f"nilai sections tak dikenal: {', '.join(unknown)} (sah {SECTION_VALUES})"
    if lane not in ROOTED_LANES:
        return f"lane `{lane or '(kosong)'}` di luar {ROOTED_LANES}"
    if lane == MINOR_LANE:
        return "" if not sections else f"lane {MINOR_LANE} wajib bersections kosong"
    if not sections:
        return f"lane `{lane}` wajib bersections non-kosong"
    if lane in ("FAST_FORWARD", "REFACTOR_ARCH") and sections != ["architecture"]:
        return f"lane `{lane}` wajib bersections tepat `architecture`"
    if lane == "FULL_PIPELINE" and not ({"flow", "ui"} & set(sections)):
        return "lane FULL_PIPELINE wajib memuat `flow` atau `ui`"
    return ""


def task_lane_sections(task_path: Path) -> Tuple[str, List[str]]:
    """`(lane, sections)` dari frontmatter `TASK.md`."""
    try:
        fm = parse_frontmatter(task_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return NOT_UTF8, []                       # lane tak sah → check akar FAIL, bukan crash
    except OSError:
        return "", []
    lane = fm.get("lane", "")
    return (lane.strip() if isinstance(lane, str) else ""), parse_sections(fm.get("sections", ""))


# ================================================================ 4. ledger `## Chain`

# Urutan kanonik baris ledger. Satu baris per hop yang dijadwalkan lane-nya.
CHAIN_SPEC = (
    ("FLOW", "frontend:ux-design", "FLOW.md", "APPROVED"),
    ("UI", "frontend:ui-design", "UI.md", "APPROVED"),
    ("CONTRACT", "frontend:contract", "CONTRACT.md", "APPROVED"),
    ("BRIEF", "frontend:plan", BRIEF_GLOB, "READY"),
)
CHAIN_BY_ROW = {r[0]: r for r in CHAIN_SPEC}
DOC_ROWS = ("FLOW", "UI", "CONTRACT")
CHAIN_LINE = re.compile(
    r"^- \[(?P<mark>[ x~])\] (?P<row>FLOW|UI|CONTRACT|BRIEF)\s+—\s+(?P<skill>\S+)\s+→\s+"
    r"(?P<doc>\S+)(?:\s+@\s+(?P<tail>.+))?$"
)
TAIL_DONE = re.compile(r"^(?P<state>APPROVED|READY) (?P<sha>[0-9a-f]{7,40})\b")
TAIL_REENTRY = re.compile(r"^re-entry (?P<n>\d+) \(was (?P<sha>[0-9a-f]{7,40})\)")


def expected_rows(sections: List[str]) -> List[str]:
    """Baris ledger yang dijadwalkan `sections`: FLOW/UI sesuai isi, CONTRACT bila non-kosong."""
    rows = []
    if "flow" in sections:
        rows.append("FLOW")
    if "ui" in sections:
        rows.append("UI")
    if sections:
        rows.append("CONTRACT")
    rows.append("BRIEF")
    return rows


def chain_line(row: str, mark: str = " ", tail: str = "") -> str:
    _, skill, doc, _ = CHAIN_BY_ROW[row]
    line = f"- [{mark}] {row:<8} — {skill:<21} → {doc}"
    return line + (f" @ {tail}" if tail else "")


def read_chain(task_text: str) -> List[Dict[str, Any]]:
    """Baris ledger `## Chain` sebagai list dict berurutan (`row`, `mark`, `sha`, `n`, `line_no`)."""
    _, body = split_frontmatter(task_text)
    offset = task_text.count("\n", 0, len(task_text) - len(body))
    rows: List[Dict[str, Any]] = []
    in_chain = False
    for i, line in enumerate(body.splitlines()):
        if line.startswith("## "):
            in_chain = line.strip() == "## Chain"
            continue
        if not in_chain:
            continue
        m = CHAIN_LINE.match(line.strip())
        if not m:
            continue
        tail = (m.group("tail") or "").strip()
        sha, n, state = "", 0, ""
        td = TAIL_DONE.match(tail)
        tr = TAIL_REENTRY.match(tail)
        if td:
            sha, state = td.group("sha"), td.group("state")
        elif tr:
            sha, n = tr.group("sha"), int(tr.group("n"))
        rows.append({"row": m.group("row"), "mark": m.group("mark"), "sha": sha,
                     "state": state, "n": n, "tail": tail, "line_no": offset + i + 1,
                     "raw": line})
    return rows


def replace_chain_row(task_text: str, row: str, new_line: str) -> str:
    """Ganti satu baris ledger; baris lain dan seksi lain tidak disentuh."""
    for entry in read_chain(task_text):
        if entry["row"] == row:
            lines = task_text.split("\n")
            lines[entry["line_no"] - 1] = new_line
            return "\n".join(lines)
    raise KeyError(row)


def strip_status_line(text: str) -> str:
    """Isi dokumen tanpa baris `status:` dan `sidik_kontrak:` frontmatter **pertama** — basis uji keutuhan konten.

    Hanya yang pertama (12 J31): baris `status:` kedua yang disisipkan sesudah approval adalah perubahan konten,
    bukan transisi status. `sidik_kontrak:` ditulis `chain.py approve --row BRIEF` sesudah ronde reviewer (24 K10),
    jadi ia tidak boleh mengubah sidik konten yang sudah direview.
    """
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    head = re.sub(r"^status:.*\n?", "", text[3:end], count=1, flags=re.MULTILINE)
    # Baris beserta newline di depannya: `set_frontmatter_field` menambahkan field baru di ujung frontmatter, dan
    # isi tanpa baris itu wajib persis isi sebelum ia ditulis.
    head = re.sub(rf"\n{SIDIK_FIELD}:[^\n]*", "", head, count=1)
    return "---" + head + text[end:]


# ---------------------------------------------------------------- Riwayat Rantai (24 K5)
#
# Dokumen taskdir tidak di-commit (Langkah 24), jadi subjek dan badan commit `TASK.md` tidak lagi menjadi jejak
# rantai. Penggantinya seksi `## Riwayat Rantai` di ujung `TASK.md`: satu baris per kejadian, bernomor urut, dan
# hanya ditulis `chain.py`. Materai approve adalah kejadian `approve`; plafon, epoch, dan putaran dihitung dari
# kejadian `reopen`/`eskalasi`/`draft`. Batasnya sama dengan materai analyst: suntingan yang tidak lewat skrip
# terdeteksi, tetapi skrip tidak dapat membuktikan keaslian Riwayat itu sendiri.

HISTORY_HEADING = "## Riwayat Rantai"
HISTORY_KINDS = ("akar", "draft", "approve", "reopen", "eskalasi", "amandemen", "abandon")
HISTORY_FREE = ("persetujuan", "alasan")
HISTORY_SEP = " · "
_HISTORY_LINE = re.compile(r"^- (?P<n>\d+) · (?P<kind>[a-z]+)(?P<rows>(?: (?:FLOW|UI|CONTRACT|BRIEF))*) · "
                           r"(?P<rest>.+)$")
_HISTORY_FIELD = re.compile(r"^(?P<key>[a-z]+) (?P<value>\S.*)$")
_CHAIN_CUT = re.compile(r"^## (?:Chain|Riwayat Rantai)[ \t]*$", re.MULTILINE)
ROOT_KINDS = ("akar", "eskalasi", "amandemen")       # kejadian yang mencatat sidik akar baru


def history_section(task_text: str) -> Optional[List[str]]:
    """Baris seksi `## Riwayat Rantai` tanpa heading-nya, atau `None` bila seksinya absen."""
    _, body = split_frontmatter(task_text)
    lines = body.splitlines()
    out: Optional[List[str]] = None
    for line, fenced in zip(lines, fenced_mask(lines)):
        if line.startswith("## ") and not fenced:
            if out is not None:
                break
            if line.strip() == HISTORY_HEADING:
                out = []
            continue
        if out is not None:
            out.append(line)
    return out


def read_history(task_text: str) -> Tuple[List[Dict[str, Any]], str]:
    """Kejadian `## Riwayat Rantai` berurutan, dan masalahnya (kosong bila utuh).

    Tiap kejadian: `n`, `kind`, `rows` (hop), `fields` (dict), dan `free` (`(kunci, teks)` atau `None`). Seksi
    absen berarti nol kejadian (akar belum dikunci). Baris tak terurai, nomor yang tidak berurut dari 1, jenis
    tak dikenal, atau field ganda adalah masalah: Riwayat yang disunting tangan tidak pernah dibaca setengah.
    """
    events: List[Dict[str, Any]] = []
    for raw in history_section(task_text) or []:
        line = raw.strip()
        if not line:
            continue
        m = _HISTORY_LINE.match(line)
        if not m or m.group("kind") not in HISTORY_KINDS:
            return [], f"baris tak terurai `{line[:80]}`"
        n = int(m.group("n"))
        if n != len(events) + 1:
            return [], f"nomor kejadian {n} ≠ urutan {len(events) + 1}"
        parts = m.group("rest").split(HISTORY_SEP)
        fields: Dict[str, str] = {}
        free: Optional[Tuple[str, str]] = None
        for i, part in enumerate(parts):
            key = next((k for k in HISTORY_FREE if part.startswith(f"{k}: ")), "")
            if key:
                free = (key, HISTORY_SEP.join(parts[i:])[len(key) + 2:])
                break
            f = _HISTORY_FIELD.match(part)
            if not f or f.group("key") in fields:
                return [], f"kejadian #{n}: field `{part[:40]}` tak terurai atau ganda"
            fields[f.group("key")] = f.group("value")
        events.append({"n": n, "kind": m.group("kind"), "rows": m.group("rows").split(), "fields": fields,
                       "free": free})
    return events, ""


def task_history(root: Path, taskdir_rel: str) -> Tuple[List[Dict[str, Any]], str]:
    """`read_history` atas `TASK.md` taskdir; berkas absen = nol kejadian."""
    path = root / taskdir_rel / "TASK.md"
    if not path.is_file():
        return [], ""
    try:
        return read_history(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return [], f"`{taskdir_rel}/TASK.md` tak terbaca atau {NOT_UTF8}"


def history_line(n: int, kind: str, rows: Iterable[str], fields: Iterable[Tuple[str, str]],
                 free: Optional[Tuple[str, str]] = None) -> str:
    """Satu baris kejadian. Teks bebas (`persetujuan:`/`alasan:`) selalu di ujung, satu baris (12 J46)."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [f"- {n} · {kind}" + "".join(f" {r}" for r in rows)]
    parts += [f"{k} {v}" for k, v in fields] + [f"waktu {now}"]
    if free:
        parts.append(f"{free[0]}: {free[1]}")
    return HISTORY_SEP.join(parts)


def append_history(task_text: str, line: str) -> str:
    """Tambah satu kejadian di ujung `## Riwayat Rantai`; seksinya dibuat di ujung berkas bila belum ada."""
    if history_section(task_text) is None:
        return task_text.rstrip("\n") + f"\n\n{HISTORY_HEADING}\n\n{line}\n"
    lines = task_text.split("\n")
    mask = fenced_mask(lines)
    idx = next(i for i, (l, f) in enumerate(zip(lines, mask)) if not f and l.strip() == HISTORY_HEADING)
    end = next((i for i in range(idx + 1, len(lines)) if not mask[i] and lines[i].startswith("## ")), len(lines))
    last = max([i for i in range(idx + 1, end) if lines[i].strip()] or [idx])
    lines[last + 1:last + 1] = ["", line] if last == idx else [line]
    return "\n".join(lines)


def root_sidik(task_text: str) -> str:
    """Sidik akar `TASK.md`: isi sebelum `## Chain` tanpa baris `status:` (24, pengganti `is_committed`).

    Ledger dan Riwayat ditulis `chain.py` sesudah akar dikunci, dan `status:` berubah lewat `abandon`; ketiganya di
    luar sidik. Suntingan akar lainnya hanya sah lewat `chain.py amend`/`escalate`, yang mencatat sidik baru.
    """
    text = strip_status_line(task_text.lstrip(BOM).replace("\r\n", "\n").replace("\r", "\n"))
    m = _CHAIN_CUT.search(text)
    return hashlib.sha1((text[:m.start()] if m else text).rstrip().encode("utf-8")).hexdigest()


def sc_sidik(task_text: str) -> str:
    """Sidik 12 hex butir `SC-{n}` `TASK.md` — materai approve mengikat hop pada SC saat disetujui."""
    data = json.dumps(sc_ids(task_text), sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(data.encode("utf-8")).hexdigest()[:12]


def file_sidik(root: Path, rel: str) -> str:
    """Sidik 12 hex isi satu berkas tanpa baris `status:`/`sidik_kontrak:`, atau `absen`."""
    path = root / rel
    if not path.is_file():
        return "absen"
    text = path.read_text(encoding="utf-8", errors="replace")
    return hashlib.sha1(strip_status_line(text).encode("utf-8")).hexdigest()[:12]


def berkas_value(root: Path, taskdir_rel: str, names: Iterable[str]) -> str:
    """Field `berkas` kejadian: `<nama>=<status>:<sidik12>` dipisah `;` (status `REVIEW-PLAN.md` = verdict-nya)."""
    items = []
    for name in names:
        status = read_status(root / taskdir_rel / name, "verdict" if name == "REVIEW-PLAN.md" else "status")
        items.append(f"{name}={status or '-'}:{file_sidik(root, f'{taskdir_rel}/{name}')}")
    return ";".join(items) or "-"


def parse_berkas(value: str) -> Dict[str, Tuple[str, str]]:
    """Kebalikan `berkas_value`: `{nama: (status, sidik12)}`."""
    out: Dict[str, Tuple[str, str]] = {}
    for item in (value or "").split(";"):
        name, _, rest = item.partition("=")
        if name and name != "-":
            status, _, sidik = rest.partition(":")
            out[name] = (status, sidik)
    return out


def last_root_seal(events: List[Dict[str, Any]]) -> str:
    """Sidik akar (12 hex) yang dicatat kejadian `akar`/`eskalasi`/`amandemen` terakhir, atau kosong."""
    for e in reversed(events):
        if e["kind"] in ROOT_KINDS:
            return e["fields"].get("akar", "")
    return ""


def last_draft(events: List[Dict[str, Any]], row: str) -> Optional[Dict[str, Any]]:
    """Kejadian `draft <row>` terbaru sesudah `reopen` terakhir yang membuka hop itu, atau `None`."""
    for e in reversed(events):
        if e["kind"] == "reopen" and row in e["rows"]:
            return None
        if e["kind"] == "draft" and e["rows"] == [row]:
            return e
    return None


def revisions_since_open(root: Path, taskdir_rel: str, row: str) -> int:
    """Revisi berturut hop `row` sejak `reopen` apa pun atau `approve` hop itu (12 J43, Riwayat 24 K5).

    Hanya kejadian `draft` **pertama** putaran itu yang merupakan draft; tiap `draft` sesudahnya adalah revisi.
    Dulu subjek `draft` ulang me-reset plafon; kini satu jenis kejadian dan hitungannya sama. Amandemen akar dan
    eskalasi bukan batas putaran.
    """
    return max(0, drafts_since_open(task_history(root, taskdir_rel)[0], row) - 1)


def drafts_since_open(events: List[Dict[str, Any]], row: str) -> int:
    """Kejadian `draft <row>` sejak `reopen` apa pun atau `approve` hop itu — basis hitungan revisi."""
    drafts = 0
    for e in reversed(events):
        if e["kind"] == "reopen" or (e["kind"] == "approve" and e["rows"] == [row]):
            break
        if e["kind"] == "draft" and e["rows"] == [row]:
            drafts += 1
    return drafts


# ================================================================ 5. blok check & laporan

AddFn = Callable[..., None]


def format_report(title: str, results: List[Dict[str, Any]],
                  resolved: Optional[Dict[str, str]] = None,
                  kind: str = "PRECONDITION CHECK") -> str:
    """Keluaran teks baku skrip prasyarat/validator; `kind` = label baris pertama
    (`PRECONDITION CHECK`, `REPORT VALIDATION`, ...); `resolved` menjadi baris `Terselesaikan:`."""
    results = sorted(results, key=lambda r: (str(r["id"]).zfill(3)))
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    label = "FAIL" if failed else ("PASS (WARN)" if warned else "PASS")
    lines = [f"{kind}: {title} [{label}] ({passed}/{len(results)} passed"
             + (f", {warned} warn)" if warned else ")")]
    for r in results:
        lines.append(f"[{r['id']}] {r['name']:<32} : {r['status']} ({r['summary']})")
        if r["status"] in ("FAIL", "WARN") and r["action"]:
            lines.append(f"    * Tindakan: {r['action']}")
    if resolved:
        lines.append("Terselesaikan: " + "; ".join(f"{k}={v}" for k, v in resolved.items()))
    return "\n".join(lines)


def report_json(results: List[Dict[str, Any]], **extra: Any) -> str:
    """Keluaran JSON baku; `extra` disisipkan sesudah hitungan, sebelum `checks`."""
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = any(r["status"] == "FAIL" for r in results)
    payload: Dict[str, Any] = {
        "status": "FAIL" if failed else "PASS",
        "passed_count": passed,
        "total_count": len(results),
    }
    payload.update(extra)
    payload["checks"] = sorted(results, key=lambda r: str(r["id"]).zfill(3))
    return json.dumps(payload, indent=2)


def check_sections(add: AddFn, cid: int, sections: List[str], required: Optional[str],
                   skill: str) -> bool:
    """`required=None` berarti gate ini jalan pada cakupan non-kosong apa pun (Gate Contract)."""
    name = f"sections memuat {required}" if required else "sections non-kosong"
    unknown = [s for s in sections if s not in SECTION_VALUES]
    if unknown:
        add(cid, name, "FAIL", f"nilai tak dikenal: {', '.join(unknown)}",
            f"`sections` dibaca dari `TASK.md`; nilai sah {SECTION_VALUES}.")
        return False
    if required is None:
        if not sections:
            add(cid, name, "FAIL", "sections kosong — lane MINOR tanpa berkas kontrak",
                f"Gate `{skill}` tidak dicakup lane MINOR; kembali ke `frontend:lead`.")
            return False
        add(cid, name, "PASS", f"sections `{','.join(sections)}`")
        return True
    if required not in sections:
        add(cid, name, "FAIL", f"sections `{','.join(sections) or '-'}` tidak memuat `{required}`",
            f"Gate `{skill}` tidak dicakup taskdir ini; kembali ke `frontend:lead` "
            "untuk rute yang benar.")
        return False
    add(cid, name, "PASS", f"sections `{','.join(sections)}`")
    return True


def check_taskdir(add: AddFn, cid: int, root: Path, taskdir_rel: str) -> bool:
    name = "Bentuk & keberadaan taskdir"
    if not TASKDIR_PATTERN.match(taskdir_rel):
        add(cid, name, "FAIL",
            f"`{taskdir_rel}` tidak berpola frontenddev/docs/<YYMMDDhhmm>-<slug>",
            "Tetapkan taskdir lewat `frontend:lead` Phase 5.")
        return False
    if not (root / taskdir_rel).is_dir():
        add(cid, name, "FAIL", f"`{taskdir_rel}` tidak ada",
            "Buat taskdir lewat gate `frontend:lead` lebih dulu; dilarang mengarang direktori pengganti.")
        return False
    add(cid, name, "PASS", f"{taskdir_rel} sah")
    return True


def check_profile(add: AddFn, cid: int, profile_dir: Path, required: Tuple[str, ...]) -> str:
    """Check profil; mengembalikan stack terbaca atau string kosong."""
    name = "Profil repo memuat berkas wajib"
    if not profile_dir.is_dir():
        add(cid, name, "FAIL", f"`{DEFAULT_PROFILE_DIR}/` tidak ada",
            "Jalankan `frontend:profile` lebih dulu.")
        return ""
    owner = profile_owner(profile_dir)
    if owner and owner != PLUGIN:
        add(cid, name, "FAIL", f"profil milik `{owner}`; bukan profil {PLUGIN}",
            f"Jangan membaca atau menimpa profil plugin lain; jalankan `frontend:profile` "
            f"(ditulis ke `{DEFAULT_PROFILE_DIR}/`).")
        return ""
    stack, missing = load_profile(profile_dir, required)
    if missing:
        moved = [f for f in missing if is_legacy_profile_dir(profile_dir) and (profile_dir / PLUGIN / f).is_file()]
        add(cid, name, "FAIL", f"{len(missing)} berkas profil hilang: " + ", ".join(missing),
            (f"Migrasi profil terputus ({', '.join(moved)} sudah di `{DEFAULT_PROFILE_DIR}/`): lanjutkan "
             "`frontend:profile` mode MIGRATE (`migrate_profile.py`), bukan REFRESH (12 J21).") if moved else
            "Jalankan `frontend:profile` mode REFRESH untuk menulis ulang profil.")
        return ""
    if not stack:
        add(cid, name, "FAIL", "field `stack` tidak terbaca dari `index.json`",
            "`index.json` rusak atau tanpa field `stack`; jalankan `frontend:profile` mode REFRESH.")
        return ""
    note = ""
    if is_legacy_profile_dir(profile_dir):
        note = "; profil masih di lokasi lama `.claude/profile/` — jalankan `frontend:profile` mode MIGRATE"
    add(cid, name, "PASS", f"{len(required)} berkas wajib ada, stack `{stack}`{note}")
    return stack


def check_adapter(add: AddFn, cid: int, stack: str) -> bool:
    name = "Adapter stack terbaca"
    if not stack:
        add(cid, name, "FAIL", "field `stack` belum terbaca dari profil",
            "Perbaiki check profil lebih dulu.")
        return False
    if stack not in KNOWN_STACKS:
        add(cid, name, "FAIL", f"`{stack}` di luar {sorted(KNOWN_STACKS)}",
            "Repo di luar cakupan plugin; hentikan rantai dan laporkan ke user.")
        return False
    path = adapter_path(stack)
    if not path.is_file():
        add(cid, name, "FAIL", f"adapter `{path.name}` tidak ditemukan",
            f"Periksa instalasi plugin di {STACKS_DIR}.")
        return False
    add(cid, name, "PASS", f"adapter {path.name} tersedia")
    return True


def check_plugin_files(add: AddFn, cid: int, skill_dir: Path, files: Iterable[str]) -> bool:
    name = "Berkas template, referensi & dispatcher"
    files = list(files)
    missing = [f for f in files if not (skill_dir / f).is_file()]
    if missing:
        add(cid, name, "FAIL", "hilang: " + ", ".join(missing),
            f"Pulihkan berkas plugin di {skill_dir}.")
        return False
    add(cid, name, "PASS", f"{len(files)} berkas tersedia")
    return True


def check_worktree(add: AddFn, cid: int, root: Path, taskdir_rel: str = "", foreign_action: str = "",
                   dirty_status: str = "FAIL") -> bool:
    """Tree bersih di luar laci kerja.

    Dokumen taskdir diabaikan git (Langkah 24), jadi draft atau laporan yang tertunda tidak pernah tampak kotor dan
    cabang "kotoran milik taskdir sendiri" (12 J22) tidak lagi ada. `foreign_action` menggantikan tindakan baku,
    mis. jejak perintah verifikasi penutup (12 J55); tanpanya kotoran itu kerja user. `dirty_status` `WARN`
    menyerahkan kotoran ke vonis lain (fase `TERPUTUS` architect: matriks bukti disk, 25 R6); repo yang tak terbaca
    tetap `FAIL`. `taskdir_rel` dipertahankan demi pemanggil lama dan tidak dipakai.
    """
    name = "Working tree bersih"
    if not is_git_repo(root):
        add(cid, name, "FAIL", "git tidak dapat membaca repo (bukan repo git, atau ditolak git)",
            "Jalankan di root repo git yang sah; tree yang tak terbaca tidak pernah dianggap bersih.")
        return False
    try:
        lines = dirty_lines(root)
    except GitError as exc:
        add(cid, name, "FAIL", f"`git status` gagal: {exc}",
            "Pulihkan repo (mis. index rusak: `git reset` atas persetujuan user) lalu ulangi prasyarat; "
            "tree yang tak terbaca tidak pernah dianggap bersih.")
        return False
    if lines:
        paths = [l[3:].strip().strip('"') for l in lines]
        add(cid, name, dirty_status, f"{len(lines)} berkas belum bersih: {', '.join(paths[:5])}",
            foreign_action or "Commit kode gate ini menuntut tree bersih. Kotoran yang bukan milik rantai adalah "
                              "kerja user — laporkan, jangan di-stash sendiri.")
        return dirty_status != "FAIL"
    add(cid, name, "PASS", "nol perubahan menggantung")
    return True


def check_task_root(add: AddFn, cid: int, root: Path, taskdir_rel: str) -> Tuple[str, List[str]]:
    """`TASK.md` akar wajib ada, terkunci, `ACTIVE`, utuh, dan pasangan lane/sections-nya sah.

    Terkunci (24 K6): `base_commit` sah dan kejadian `akar` di `## Riwayat Rantai` (`chain.py root`). Utuh: sidik
    akar sama dengan sidik yang dicatat kejadian `akar`/`eskalasi`/`amandemen` terakhir — pengganti "ter-commit
    tanpa perubahan menggantung" sejak dokumen taskdir tidak di-commit. Mengembalikan `(lane, sections)` bila
    lolos, atau `("", [])`. Taskdir tanpa `TASK.md` selalu `FAIL`.
    """
    name = "TASK.md akar, lane & sections"
    rel = f"{taskdir_rel}/TASK.md"
    path = root / rel
    if not path.is_file():
        add(cid, name, "FAIL", "`TASK.md` tidak ada di taskdir",
            "Kunci akar lewat `frontend:task` (dipanggil `frontend:lead` Phase 7) lebih dulu.")
        return "", []
    events, problem = task_history(root, taskdir_rel)
    if problem:
        add(cid, name, "FAIL", f"`## Riwayat Rantai` rusak: {problem}",
            "Laporkan ke user lewat `frontend:lead`; Riwayat hanya ditulis `chain.py`, dilarang menambalnya "
            "dengan tangan.")
        return "", []
    base, problem = task_base_commit(root, taskdir_rel)
    if not events or events[0]["kind"] != "akar" or not base:
        add(cid, name, "FAIL", "akar belum terkunci — `base_commit` atau kejadian `akar` di `## Riwayat Rantai` "
                               "tidak ada",
            "Akar wajib terkunci `chain.py root` (`frontend:task` Phase 4) sebelum gate hilir berangkat.")
        return "", []
    if problem:
        add(cid, name, "FAIL", f"`base_commit`: {problem}",
            "Branch kerja ditulis ulang (rebase/reset) sesudah akar dikunci; laporkan ke user lewat "
            "`frontend:lead` — dilarang menyunting `base_commit` dengan tangan.")
        return "", []
    status = read_status(path)
    if status != "ACTIVE":
        add(cid, name, "FAIL", f"`TASK.md` berstatus `{status or '(kosong)'}`",
            "Hanya `status: ACTIVE` yang sah; kembali ke `frontend:lead`.")
        return "", []
    lane, sections = task_lane_sections(path)
    problem = lane_sections_problem(lane, sections) or lane_tamper(root, taskdir_rel)
    if problem:
        add(cid, name, "FAIL", problem,
            "Perbaiki lewat `chain.py escalate` di `frontend:lead`; dilarang menyunting "
            "frontmatter `TASK.md` dengan tangan.")
        return "", []
    seal = last_root_seal(events)
    if root_sidik(path.read_text(encoding="utf-8", errors="replace"))[:12] != seal:
        add(cid, name, "FAIL", f"`TASK.md` disunting di luar `chain.py amend`/`escalate` (sidik akar ≠ `{seal}`)",
            "Amandemen akar lewat `frontend:lead` (`validate_task.py --amend` lalu `chain.py amend`), atau "
            "kembalikan suntingannya.")
        return "", []
    add(cid, name, "PASS", f"TASK.md `ACTIVE` @ base {base[:7]}, lane `{lane}`, sections `{','.join(sections) or '-'}`")
    return lane, sections


# Urutan lane untuk replay eskalasi — sama dengan `chain.LANE_RANK` (lane hanya naik).
LANE_RANK = {"HOTFIX_MINOR": 0, "FAST_FORWARD": 1, "REFACTOR_ARCH": 1, "FULL_PIPELINE": 2}


def _lane_key(fm: Dict[str, Any]) -> Tuple[str, List[str]]:
    return str(fm.get("lane", "")).strip(), sorted(parse_sections(fm.get("sections", "")))


def _sections_field(value: str) -> List[str]:
    """Nilai field `sections` kejadian Riwayat (`architecture,flow` atau `-`) sebagai list terurut."""
    value = value.strip()
    return [] if value in ("", "-") else sorted(parse_sections(value))


def sections_value(sections: List[str]) -> str:
    """Kebalikan `_sections_field`: list sections → nilai field kejadian."""
    return ",".join(sections) or "-"


def lane_tamper(root: Path, taskdir_rel: str) -> str:
    """Kosong bila `lane`/`sections` hanya pernah bergeser lewat `chain.py escalate` sejak akar dikunci.

    Riwayat di-replay dari kejadian `akar` (12 J18, 24 K5): tiap kejadian `eskalasi` wajib berangkat dari pasangan
    terakhir dan monoton (lane naik, sections bertambah), dan hasil akhirnya wajib sama dengan frontmatter di disk.
    Akar yang belum terkunci tidak divonis di sini.
    """
    rel = f"{taskdir_rel}/TASK.md"
    events, problem = task_history(root, taskdir_rel)
    if problem:
        return f"`## Riwayat Rantai` rusak: {problem}"
    if not events or events[0]["kind"] != "akar":
        return ""
    first = events[0]["fields"]
    state = (first.get("lane", ""), _sections_field(first.get("sections", "")))
    for e in events[1:]:
        if e["kind"] != "eskalasi":
            continue
        lanes = [s.strip() for s in e["fields"].get("lane", "").split("→")]
        secs = [_sections_field(s) for s in e["fields"].get("sections", "").split("→")]
        if len(lanes) != 2 or len(secs) != 2 or (lanes[0], secs[0]) != state:
            return f"kejadian eskalasi #{e['n']} tidak berangkat dari lane/sections terakhir `{state[0]}`"
        after = (lanes[1], secs[1])
        if LANE_RANK.get(after[0], -1) < LANE_RANK.get(state[0], -1) or not set(state[1]) <= set(after[1]):
            return f"kejadian eskalasi #{e['n']} tidak monoton (`{state[0]}` → `{after[0]}`)"
        state = after
    try:
        disk = _lane_key(parse_frontmatter((root / rel).read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError):
        return f"`{rel}` tak terbaca atau {NOT_UTF8}"
    if disk != state:
        return "`lane`/`sections` berubah di luar akar atau `chain.py escalate`"
    return ""


GATE_ROW = {"contract": "CONTRACT", "plan": "BRIEF"}


def _snapshot(rels: List[str], read: Callable[[str], Optional[str]]) -> str:
    h = hashlib.sha1()
    for rel in sorted(rels):
        text = read(rel)
        h.update(rel.encode())
        h.update(strip_status_line(text).encode() if text is not None else b"<absen>")
    return h.hexdigest()


def content_snapshot(root: Path, rels: List[str]) -> str:
    """Sidik sha1 isi berkas di disk tanpa baris `status:`/`sidik_kontrak:` — basis vonis ronde dan materai."""
    # errors="replace" di kedua sisi: berkas non-UTF-8 tetap bersidik deterministik, bukan crash.
    return _snapshot(rels, lambda r: (root / r).read_text(encoding="utf-8", errors="replace")
                     if (root / r).is_file() else None)


def reopen_epoch(root: Path, taskdir_rel: str, gate: str) -> int:
    """Epoch ronde gate: kejadian `reopen` yang membuka hop gate ini **atau hop di atasnya**, ditambah kejadian
    `eskalasi` (12 J42, padanan 11 H27; dibaca dari Riwayat, 24 K5).

    Dokumen hulu yang berubah membatalkan vonis reviewer hilir walau hop hilir masih `[ ]` dan karena itu tidak
    ikut kaskade — dulu `reopen CONTRACT` atas BRIEF `[ ]` meninggalkan plafon ronde plan habis selamanya.
    """
    rows = [spec[0] for spec in CHAIN_SPEC]
    upto = set(rows[:rows.index(GATE_ROW[gate]) + 1])
    events, _ = task_history(root, taskdir_rel)
    return sum(1 for e in events if e["kind"] == "eskalasi" or (e["kind"] == "reopen" and upto & set(e["rows"])))


# ---------------------------------------------------------------- materai approve (12 J44, J46, 24 K8)

_REVIEW_ROUND = re.compile(r"^(?P<gate>contract|plan) r\d+ t\d+ PASS (?P<sidik>[0-9a-f]{12})$")
REAPPROVE = "`chain.py reopen --row {row}` lalu setujui ulang lewat gate pemiliknya"


def approval_stamp(events: List[Dict[str, Any]], row: str) -> Optional[Dict[str, Any]]:
    """Kejadian `approve <row>` terbaru yang lebih baru daripada `reopen` terakhir yang membuka hop itu, atau `None`.

    Padanan pembacaan `git log` lama atas commit approve (12 J44): pindai mundur, `reopen` yang membuka hop itu
    berarti hop belum bermaterai lagi.
    """
    for e in reversed(events):
        if e["kind"] == "reopen" and row in e["rows"]:
            return None
        if e["kind"] == "approve" and e["rows"] == [row]:
            return e
    return None


def approval_targets(root: Path, taskdir_rel: str, row: str) -> List[str]:
    """Berkas yang disidik materai hop `row` di disk: dokumennya, atau seluruh brief + `REVIEW-PLAN.md`."""
    if row in DOC_ROWS:
        return [f"{taskdir_rel}/{CHAIN_BY_ROW[row][2]}"]
    taskdir = root / taskdir_rel
    names = sorted(p.name for p in taskdir.glob(BRIEF_GLOB))
    if (taskdir / "REVIEW-PLAN.md").is_file():
        names.append("REVIEW-PLAN.md")
    return [f"{taskdir_rel}/{n}" for n in names]


def _lane_at(events: List[Dict[str, Any]], n: int) -> str:
    """Lane yang berlaku tepat sebelum kejadian ke-`n` (replay `akar` + `eskalasi`)."""
    lane = ""
    for e in events:
        if e["n"] >= n:
            break
        if e["kind"] == "akar":
            lane = e["fields"].get("lane", "")
        elif e["kind"] == "eskalasi":
            lane = e["fields"].get("lane", "").split("→")[-1].strip()
    return lane


def brief_set_drift(root: Path, taskdir_rel: str, stamp: Dict[str, Any]) -> str:
    """Kosong bila himpunan brief + `REVIEW-PLAN.md` sama dengan saat disetujui, kecuali baris status.

    Pembandingnya field `berkas` kejadian approve: nama, status, dan sidik isi tiap berkas (24 K8).
    """
    recorded = parse_berkas(stamp["fields"].get("berkas", ""))
    then = sorted(n for n in recorded if n != "REVIEW-PLAN.md")
    now = sorted(p.name for p in (root / taskdir_rel).glob(BRIEF_GLOB))
    if then != now:
        added = sorted(set(now) - set(then))
        gone = sorted(set(then) - set(now))
        parts = ([f"ditambah {', '.join(added)}"] if added else []) + \
                ([f"hilang {', '.join(gone)}"] if gone else [])
        return "himpunan brief berubah sesudah breakdown disetujui: " + "; ".join(parts)
    for name, (_, sidik) in recorded.items():
        if file_sidik(root, f"{taskdir_rel}/{name}") != sidik:
            return f"`{taskdir_rel}/{name}` berubah sesudah disetujui (Riwayat #{stamp['n']})"
    allowed = {("READY", "READY"), ("READY", "DONE"), ("READY", "BLOCKED"), ("DONE", "DONE"),
               ("DONE", "BLOCKED"), ("BLOCKED", "BLOCKED")}
    for name in now:
        before, after = recorded[name][0], read_status(root / taskdir_rel / name)
        if (before, after) not in allowed:
            return f"`{name}` berpindah status `{before}` → `{after}` — transisi di luar siklus brief"
    return ""


def verify_chain_row(root: Path, taskdir_rel: str, entry: Dict[str, Any]) -> str:
    """Kosong bila satu baris ledger `[x]` sah: materai approve utuh, dok APPROVED/READY, konten utuh.

    Jangkarnya kejadian `approve` di `## Riwayat Rantai` (24 K8), bukan sha ledger: kejadian terbaru hop itu yang
    lebih baru daripada `reopen` terakhirnya. Sidik ledger wajib sama dengan `sidik` kejadian itu, isi berkas di disk
    sama dengan sidiknya, `SC-{n}` tidak berubah sejak disetujui, dan hop yang direview membawa `review … PASS`
    atas konten yang sama (12 J46). Validator tidak dijalankan ulang: versi validator baru tidak boleh menggugurkan
    approval lama.
    """
    row = entry["row"]
    if entry["mark"] != "x":
        state = "belum berangkat" if entry["mark"] == " " else f"dibuka ulang (re-entry {entry['n']})"
        return f"hop `{row}` {state}"
    sha = entry["sha"]
    remedy = REAPPROVE.format(row=row)
    events, problem = task_history(root, taskdir_rel)
    if problem:
        return f"`## Riwayat Rantai` rusak: {problem} — laporkan ke user lewat `frontend:lead`"
    stamp = approval_stamp(events, row)
    if stamp is None:
        return (f"hop `{row}` @ {sha or '(kosong)'} tercentang tanpa kejadian `approve` di Riwayat sesudah reopen "
                f"terakhirnya — centang tulisan tangan; {remedy}")
    fields = stamp["fields"]
    sidik = fields.get("sidik", "")
    if not sha or not re.fullmatch(r"[0-9a-f]{40}", sidik) or not sidik.startswith(sha):
        return (f"hop `{row}` @ {sha or '(kosong)'} tidak dimateraikan kejadian approve terakhirnya "
                f"(#{stamp['n']} memateraikan `{sidik[:12] or '-'}`) — centang tulisan tangan; {remedy}")
    gate = {"CONTRACT": "contract", "BRIEF": "plan"}.get(row, "")
    if row == "BRIEF":
        recorded = parse_berkas(fields.get("berkas", ""))
        if _lane_at(events, stamp["n"]) == MINOR_LANE or not any(s == "READY" for s, _ in recorded.values()):
            gate = ""
    if gate:
        m = _REVIEW_ROUND.match(fields.get("review", ""))
        reviewed = sidik[:12] if row == "CONTRACT" else fields.get("brief", "")
        if not m or m.group("gate") != gate or m.group("sidik") != reviewed:
            return (f"materai approve hop `{row}` (Riwayat #{stamp['n']}) tanpa `review {gate} … PASS` atas konten "
                    f"yang sama — approval tanpa ronde reviewer; {remedy}")
    task_text = (root / taskdir_rel / "TASK.md").read_text(encoding="utf-8", errors="replace")
    if fields.get("sc", "") != sc_sidik(task_text):
        return f"`SC-{{n}}` TASK.md berubah sesudah hop `{row}` disetujui — hop wajib dibuka ulang"
    if row in DOC_ROWS:
        doc = CHAIN_BY_ROW[row][2]
        rel = f"{taskdir_rel}/{doc}"
        if not (root / rel).is_file():
            return f"`{rel}` hilang dari disk"
        status = read_status(root / rel)
        if status != "APPROVED":
            return f"`{doc}` berstatus `{status or '(kosong)'}` padahal hop `{row}` tercentang"
        if content_snapshot(root, [rel]) != sidik:
            return f"`{rel}` berubah sesudah disetujui @ {sidik[:12]}"
        return ""
    return brief_set_drift(root, taskdir_rel, stamp)


def locked_brief_problems(root: Path, taskdir_rel: str) -> List[str]:
    """Brief `DONE`/`BLOCKED` saat hop BRIEF terakhir dibuka ulang wajib tetap sama status dan isinya (12 J48).

    Jangkarnya kejadian `reopen` terakhir yang membuka BRIEF (target atau kaskade) beserta field `berkas`-nya:
    keadaan brief saat hop dibuka. Brief `BLOCKED` tidak pernah naik lagi — sisa pekerjaannya milik brief remedi.
    """
    events, _ = task_history(root, taskdir_rel)
    anchor = next((e for e in reversed(events) if e["kind"] == "reopen" and "BRIEF" in e["rows"]), None)
    if anchor is None:
        return []
    problems = []
    for name, (before, sidik) in parse_berkas(anchor["fields"].get("berkas", "")).items():
        if name == "REVIEW-PLAN.md" or before not in ("DONE", "BLOCKED"):
            continue
        path = root / taskdir_rel / name
        if not path.is_file():
            problems.append(f"`{name}` ({before}) hilang")
            continue
        after = read_status(path)
        if after != before:
            problems.append(f"`{name}` {before} → {after or '(kosong)'}")
        elif file_sidik(root, f"{taskdir_rel}/{name}") != sidik:
            problems.append(f"`{name}` ({before}) disunting")
    return problems


def check_chain_rows(add: AddFn, cid: int, root: Path, taskdir_rel: str,
                     rows: Iterable[str], sections: List[str]) -> bool:
    """Tiap baris `rows` yang dijadwalkan `sections` wajib `[x]` sah dan kontennya utuh.

    Baris yang tidak dijadwalkan `sections` dilewati. Ledger yang tidak memuat
    baris terjadwal — atau memuat baris di luar jadwal — adalah akar rusak.
    """
    name = "Ledger ## Chain tercentang"
    path = root / taskdir_rel / "TASK.md"
    try:
        entries = read_chain(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        add(cid, name, "FAIL", f"`TASK.md` tidak terbaca atau {NOT_UTF8}", "Perbaiki check akar lebih dulu.")
        return False
    expected = expected_rows(sections)
    present = [e["row"] for e in entries]
    if present != expected:
        add(cid, name, "FAIL", f"baris ledger {present} ≠ jadwal sections {expected}",
            "Ledger ditulis `frontend:task` dan diubah hanya lewat `chain.py escalate`.")
        return False
    wanted = [r for r in rows if r in expected]
    if not wanted:
        add(cid, name, "PASS", "tidak ada hop hulu yang dituntut")
        return True
    problems = []
    for entry in entries:
        if entry["row"] in wanted:
            problem = verify_chain_row(root, taskdir_rel, entry)
            if problem:
                problems.append(problem)
    if problems:
        add(cid, name, "FAIL", "; ".join(problems),
            "Hop belum tercentang → selesaikan gate pemiliknya sampai `chain.py approve`. "
            "Konten berubah sesudah disetujui → `chain.py reopen` lalu setujui ulang; "
            "dilarang mengembalikan isi dengan tangan agar lolos.")
        return False
    add(cid, name, "PASS", f"{', '.join(wanted)} tercentang dan utuh")
    return True


def check_pending(add: AddFn, cid: int, root: Path, taskdir_rel: str, doc: str) -> None:
    """WARN bila artefak milik gate ini sudah ada dari sesi sebelumnya, beserta apakah draft-nya sudah tercatat."""
    name = f"{doc} tertunda dari sesi lalu"
    path = root / taskdir_rel / doc
    if not path.is_file():
        add(cid, name, "PASS", f"`{doc}` belum ada — sesi baru")
        return
    status = read_status(path) or "(kosong)"
    if status == "APPROVED":
        add(cid, name, "FAIL", f"`{doc}` sudah `APPROVED`",
            "Gate ini sudah tuntas. Revisi atas dokumen yang disetujui hanya lewat "
            "`chain.py reopen` di `frontend:lead`.")
        return
    row = next(r for r in DOC_ROWS if CHAIN_BY_ROW[r][2] == doc)
    if doc == "CONTRACT.md":
        ready = contract_review_ready(root, taskdir_rel)
        if ready:
            add(cid, name, "WARN", f"`{doc}` tertunda berstatus `{status}`; belum layak diajukan: {ready}",
                "Jangan catat draft dan jangan ajukan ke user: lanjutkan perbaikan draft, `validate_doc.py` "
                "sampai `PASS`, lalu ronde reviewer (Phase 5 butir 2–3) sebelum diajukan.")
            return
    events, _ = task_history(root, taskdir_rel)
    draft = last_draft(events, row)
    if draft and draft["fields"].get("sidik") == content_snapshot(root, [f"{taskdir_rel}/{doc}"])[:12]:
        add(cid, name, "WARN", f"`{doc}` tertunda berstatus `{status}`; draft tercatat (Riwayat #{draft['n']})",
            "Tanyakan ke user apakah draft diputuskan (setuju/revisi) atau ditulis ulang, sebelum Phase 0 berjalan.")
        return
    add(cid, name, "WARN", f"`{doc}` tertunda berstatus `{status}`; konten di disk belum tercatat sebagai draft",
        f"Lanjutkan dari draft itu: catat lewat `chain.py draft --row {row}` (skrip menjalankan validator"
        + ("; CONTRACT menuntut ronde reviewer terakhir `PASS` atas konten ini" if row == "CONTRACT" else "")
        + "), lalu tanyakan ke user apakah draft diputuskan (setuju/revisi) atau ditulis ulang, sebelum Phase 0 "
          "berjalan.")


def contract_review_ready(root: Path, taskdir_rel: str) -> str:
    """Alasan `CONTRACT.md` di disk belum lolos ronde reviewer, atau kosong bila siap diajukan."""
    common = str(Path(__file__).resolve().parent)
    if common not in sys.path:
        sys.path.insert(0, common)
    from review_round import Rounds   # impor lambat: review_round mengimpor modul ini
    try:
        return Rounds(taskdir_rel, "contract", root).ready()
    except SystemExit as exc:
        return str(exc)


def task_base_commit(root: Path, taskdir_rel: str) -> Tuple[str, str]:
    """`(base_commit, masalah)` dari frontmatter `TASK.md` (24 K6, G3). Absen → `("", "")`."""
    path = root / taskdir_rel / "TASK.md"
    try:
        value = str(parse_frontmatter(path.read_text(encoding="utf-8")).get("base_commit", "") or "").strip()
    except (OSError, UnicodeDecodeError):
        return "", ""
    if not value:
        return "", ""
    return value, _docs_git.base_commit_problem(root, value)


def task_root_sha(root: Path, taskdir_rel: str) -> str:
    """`base_commit` akar yang sah — titik awal rentang rantai — atau kosong (24 K6).

    Dulu sha commit yang melahirkan `TASK.md`; dokumen taskdir tidak lagi di-commit, jadi rentang kode rantai
    dihitung dari `HEAD` saat akar dikunci (`chain.py root`). Taskdir era git tanpa `base_commit` tetap dibaca dari
    commit yang dulu menambahkan `TASK.md`-nya (riwayatnya masih ada sesudah `docs_git.py migrate`), supaya review
    ad-hoc dan laporan atas taskdir lama tetap punya rentang.
    """
    value, problem = task_base_commit(root, taskdir_rel)
    if value:
        return "" if problem else value
    added = git(root, "log", "--diff-filter=A", "--format=%H", "--", f"{taskdir_rel}/TASK.md").split()
    return added[-1] if added else ""


def taskdir_slug(taskdir_rel: str) -> str:
    """Slug dari nama taskdir `<YYMMDDhhmm>-<slug>`."""
    return taskdir_rel.rstrip("/").rsplit("/", 1)[-1].split("-", 1)[-1]


def chain_files(root: Path, taskdir_rel: str) -> List[str]:
    """Berkas di luar `frontenddev/docs`, `frontenddev/reviews`, dan `.claude` yang diubah commit rantai sesudah akar.

    Laci audit dikecualikan: `finding_source` ikut commit `closing review` hanya
    untuk menutup baris `> Status:`-nya, bukan sebagai kerja rantai.

    Commit rantai dikenali dari `(<slug>)` di subjeknya — konvensi commit
    plugin ini — sehingga commit user lain di rentang yang sama tidak terhitung.
    """
    sha = task_root_sha(root, taskdir_rel)
    if not sha:
        return []
    return sorted(set(chain_files_since(root, taskdir_rel, sha)))


def chain_commits(root: Path, taskdir_rel: str, since: str) -> List[str]:
    """Sha commit rantai sesudah `since`: subjek berscope persis `<type>(<slug>)`.

    Hanya **subjek** yang dicocokkan — badan commit yang kebetulan menyebut
    slug, atau scope user lain, tidak ikut terhitung.
    """
    rx = re.compile(rf"^[a-z]+(?:!)?\({re.escape(taskdir_slug(taskdir_rel))}\)!?: ")
    out = git(root, "log", f"{since}..HEAD", "--format=%H %s")
    return [l.split(" ", 1)[0] for l in out.splitlines()
            if " " in l and rx.match(l.split(" ", 1)[1])]


def chain_files_since(root: Path, taskdir_rel: str, since: str) -> List[str]:
    """Path apa adanya (`core.quotePath=false`, `-z`): nama non-ASCII atau berspasi tidak dikutip git."""
    files: List[str] = []
    for sha in chain_commits(root, taskdir_rel, since):
        out = git(root, "-c", "core.quotePath=false", "show", "-z", "--name-only", "--format=", sha,
                  "--", ".", ":(exclude)frontenddev/docs", ":(exclude)frontenddev/reviews",
                  ":(exclude).claude")
        files += [f.strip("\n") for f in out.split("\0") if f.strip()]
    return files


def review_is_fresh(root: Path, taskdir_rel: str) -> bool:
    """`REVIEW.md` menilai keadaan kode rantai sekarang (24 K9, pengganti urutan commit `REVIEW.md`).

    Frontmatter `head:` adalah sha `HEAD` yang dinilai reviewer. Review segar bila `head` leluhur `HEAD` dan tidak ada
    commit pembawa kode sesudahnya, apa pun subjeknya: unit yang mendarat sesudah review penutup belum pernah dinilai,
    dan yang dinilai berkas yang disentuh, bukan subjek yang diketik model (09 E13). Commit yang hanya menyentuh
    `frontenddev/` atau `.claude/` (mis. `finding_source`, profil) tidak membasikannya.
    """
    path = root / taskdir_rel / "REVIEW.md"
    try:
        head = str(parse_frontmatter(path.read_text(encoding="utf-8")).get("head", "") or "").strip()
    except (OSError, UnicodeDecodeError):
        return False
    if not re.fullmatch(r"[0-9a-f]{7,40}", head):
        return False
    full = git(root, "rev-parse", "--verify", "-q", f"{head}^{{commit}}").strip()
    if not full or not git_ok(root, "merge-base", "--is-ancestor", full, "HEAD")[0]:
        return False
    return not any(carries_code(root, sha) for sha in git(root, "rev-list", f"{full}..HEAD").split())


def design_gate_checks(add: AddFn, root: Path, taskdir_rel: str, profile_dir: Path,
                       skill_dir: Path, *, required: Optional[str], row: str,
                       profile_required: Tuple[str, ...], plugin_files: Iterable[str]
                       ) -> Tuple[str, List[str]]:
    """Blok prasyarat bersama tiga gerbang dokumen (`ux-design`, `ui-design`, `contract`).

    Urutan check-nya tetap supaya nomor check sama di ketiga skrip:
    1 taskdir · 2 akar `TASK.md` + lane/sections · 3 sections mencakup gate ·
    4 hop hulu ledger tercentang & utuh · 5 profil · 6 adapter · 7 berkas plugin ·
    8 dokumen gate ini tertunda · 9 working tree. `sections` dibaca dari
    `TASK.md` — bukan parameter handoff — sehingga gate tidak dapat dipanggil
    dengan cakupan yang berbeda dari yang dikunci akar.
    """
    taskdir_ok = check_taskdir(add, 1, root, taskdir_rel)
    lane, sections = ("", [])
    if taskdir_ok:
        lane, sections = check_task_root(add, 2, root, taskdir_rel)
    else:
        add(2, "TASK.md akar, lane & sections", "FAIL", "taskdir tidak sah", "Perbaiki Check 1 lebih dulu.")
    rooted = bool(lane)
    if rooted:
        check_sections(add, 3, sections, required, CHAIN_BY_ROW[row][1])
        above = [r for r in expected_rows(sections) if r != row]
        above = above[:expected_rows(sections).index(row)] if row in expected_rows(sections) else above
        check_chain_rows(add, 4, root, taskdir_rel, above, sections)
    else:
        for cid, name in ((3, "sections mencakup gate"), (4, "Ledger ## Chain tercentang")):
            add(cid, name, "FAIL", "akar belum sah", "Perbaiki Check 2 lebih dulu.")
    stack = check_profile(add, 5, profile_dir, profile_required)
    check_adapter(add, 6, stack)
    check_plugin_files(add, 7, skill_dir, plugin_files)
    if taskdir_ok:
        check_pending(add, 8, root, taskdir_rel, CHAIN_BY_ROW[row][2])
    else:
        add(8, f"{CHAIN_BY_ROW[row][2]} tertunda dari sesi lalu", "FAIL", "taskdir tidak sah",
            "Perbaiki Check 1 lebih dulu.")
    check_worktree(add, 9, root, taskdir_rel)
    return stack, sections


def brief_closure(taskdir: Path, root: Optional[Path] = None) -> Dict[str, Tuple[str, bool]]:
    """`{NN: (status, tertutup)}` — tertutup = `DONE` yang mendarat bersama kode (`done_landed`, 12 J15),
    atau `BLOCKED` yang remedinya tertutup.

    Remedi dikenali dari field `remedies: "NN"` brief; remedi siklik tidak pernah tertutup. Dipakai
    `architect` (fase rantai, prasyarat `depends_on`), `report` (seluruh unit tertutup), dan
    `taskdir_state`. `root` default: toplevel git `taskdir`.
    """
    if root is None:
        top = git(taskdir, "rev-parse", "--show-toplevel").strip() if taskdir.is_dir() else ""
        root = Path(top) if top else taskdir
    try:
        taskdir_rel = taskdir.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        taskdir_rel = ""
    briefs: Dict[str, Path] = {}
    for p in sorted(taskdir.glob(BRIEF_GLOB)):
        m = re.match(r"^brief-(\d{2})-[a-z0-9-]+\.md$", p.name)
        if m:
            briefs.setdefault(m.group(1), p)
    status = {nn: read_status(p) for nn, p in briefs.items()}
    remedies: Dict[str, List[str]] = {}
    for nn, p in briefs.items():
        origin = read_status(p, "remedies")
        if origin:
            remedies.setdefault(origin, []).append(nn)

    landed = {nn: bool(taskdir_rel) and bool(done_landed(root, f"{taskdir_rel}/{p.name}"))
              for nn, p in briefs.items() if status[nn] == "DONE"}

    def closed(nn: str, seen: Tuple[str, ...] = ()) -> bool:
        if nn in seen or nn not in status:
            return False
        if status[nn] == "DONE":
            return landed[nn]
        return status[nn] == "BLOCKED" and any(closed(r, seen + (nn,)) for r in remedies.get(nn, []))

    return {nn: (status[nn], closed(nn)) for nn in briefs}


def runnable_briefs(taskdir: Path, root: Optional[Path] = None) -> List[str]:
    """NN brief `READY` yang seluruh `depends_on`-nya tertutup (`brief_closure`), terurut.

    Kosong padahal ada brief `READY` = rantai buntu (`TERHENTI (DAG)`, 12 J58): mis. remedi yang
    bergantung pada unit asalnya — unit asal hanya tertutup lewat remedi itu. Satu implementasi untuk
    `taskdir_state` dan prasyarat `architect`, supaya lead tidak merutekan `EKSEKUSI` ke architect
    yang lalu menolaknya.
    """
    closure = brief_closure(taskdir, root)
    out: List[str] = []
    for p in sorted(taskdir.glob(BRIEF_GLOB)):
        m = re.match(r"^brief-(\d{2})-[a-z0-9-]+\.md$", p.name)
        if not m or closure.get(m.group(1), ("", False))[0] != "READY" or m.group(1) in out:
            continue
        deps = as_list(parse_frontmatter(p.read_text(encoding="utf-8")).get("depends_on"))
        if all(closure.get(str(d).strip(), ("", False))[1] for d in deps):
            out.append(m.group(1))
    return out


def cli(main: Callable[[], Any]) -> Any:
    """Jaring terakhir skrip ber-CLI: berkas non-UTF-8 (09 E1), `--root` yang tidak ada, atau git yang tidak
    terpasang (11 H21, 12 J19) menjadi vonis FAIL terbaca (JSON bila `--json`), bukan traceback."""
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
