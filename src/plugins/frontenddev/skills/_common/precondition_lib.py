#!/usr/bin/env python3
"""Helper bersama skrip prasyarat, validator, dan CLI rantai `frontenddev`.

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
   laci `.explore/`, dan uji ter-commit. Satu parser berarti status artefak yang
   sama tidak pernah divonis berbeda oleh dua gerbang.
3. **Lane & sections** — enum lane berakar, nilai `sections`, dan invarian
   pasangan keduanya. Ketiganya dibaca dari frontmatter `TASK.md`, bukan
   disimpulkan dari berkas yang kebetulan ada.
4. **Ledger `## Chain`** — pembaca/penulis baris ledger, uji keutuhan konten
   yang disetujui (drift), dan penghitung plafon (revisi, re-entry, eskalasi).
   CLI-nya `chain.py`; hilir memakai `check_chain_rows`.
5. **Blok check & laporan** — check yang pesannya sama persis di banyak
   gerbang, plus format laporan teks/JSON baku.

Zero external dependencies (Python Standard Library only).
"""

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

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
    milik plugin ini (field `plugin`, atau `stack` anggota daftar frontenddev),
    dan selalu disertai catatan MIGRATE. Profil milik plugin lain tidak pernah
    dikembalikan: skrip melihatnya sebagai profil yang tidak ada.
    """
    own = root / PROFILE_DIR_REL
    if (own / "index.json").exists():
        return own, ""
    prof = _detect.read_profile(root, PLUGIN)
    if prof.location == "legacy" and prof.state not in ("OTHER_OWNER", "ABSENT", "INVALID_JSON"):
        return root / LEGACY_PROFILE_DIR_REL, (
            "profil frontenddev masih di lokasi lama `.claude/profile/`; "
            "jalankan `frontenddev:profile` mode MIGRATE")
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
    return taskdir.strip().strip("/").replace("./", "")


def strip_explore_scratch(status_out: str) -> str:
    """Buang baris `git status --porcelain` yang menunjuk laci `.explore/`/`.frontenddev/`.

    Laci itu zona kerja, bukan artefak rantai: tidak pernah di-stage maupun
    di-commit, sehingga kehadirannya tidak boleh dihitung working tree kotor.
    """
    kept = []
    for line in status_out.splitlines():
        if not line.strip():
            continue
        path = line[3:] if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ")[-1]
        path = path.strip().strip('"')
        segments = path.rstrip("/").split("/")
        if ".explore" in segments or ".frontenddev" in segments:
            continue
        kept.append(line)
    return "\n".join(kept)


def is_git_repo(root: Path) -> bool:
    """Benar hanya bila git benar-benar dapat membaca repo di `root`."""
    return git(root, "rev-parse", "--is-inside-work-tree").strip() == "true"


def dirty_lines(root: Path) -> List[str]:
    """Baris `git status --porcelain` di luar laci kerja."""
    out = strip_explore_scratch(git(root, "status", "--porcelain"))
    return [l for l in out.splitlines() if l.strip()]


def as_list(value: Any) -> List[str]:
    """Nilai frontmatter berbentuk list; skalar dibungkus, kosong jadi `[]`."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    value = str(value or "").strip()
    return [value] if value else []


def is_committed(root: Path, rel: str) -> bool:
    """Benar bila `rel` pernah di-commit **dan** tidak punya perubahan menggantung."""
    if not git(root, "log", "-1", "--format=%h", "--", rel).strip():
        return False
    return not git(root, "status", "--porcelain", "--", rel).strip()


def last_commit(root: Path, *paths: str) -> str:
    """Sha pendek commit terakhir yang menyentuh salah satu `paths`, atau kosong."""
    return git(root, "log", "-1", "--format=%h", "--", *paths).strip()


class FrontmatterError(ValueError):
    pass


def split_frontmatter(text: str, strict: bool = False) -> Tuple[Dict[str, Any], str]:
    """Parse subset YAML frontmatter → `(data, body)`.

    Mendukung skalar, list inline `[a, b]`, `[]`/`{}` kosong, list blok `- x`,
    dan komentar `#`. `strict=True` melempar `FrontmatterError` bila pagar `---`
    tidak lengkap — dipakai validator, yang harus memvonis berkas rusak sebagai
    rusak, bukan sebagai berkas tanpa field.
    """
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


def parse_frontmatter(text: str) -> Dict[str, Any]:
    """Frontmatter saja, versi toleran (berkas tanpa pagar → dict kosong)."""
    return split_frontmatter(text)[0]


def read_status(path: Path, field: str = "status") -> str:
    """Nilai satu field frontmatter sebagai string, atau kosong."""
    try:
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return ""
    value = fm.get(field, "")
    return value.strip() if isinstance(value, str) else ""


def set_frontmatter_field(text: str, key: str, value: str) -> str:
    """Ganti (atau sisipkan di akhir frontmatter) satu field skalar."""
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
    return "---" + head + text[end:]


def section_lines(body: str, heading: str) -> List[str]:
    """Badan satu heading (`## X`) sampai heading setingkat atau lebih tinggi berikutnya."""
    level = len(heading) - len(heading.lstrip("#"))
    out: List[str] = []
    capturing = False
    in_fence = False
    for line in body.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
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
    except OSError:
        return {}
    out: Dict[str, str] = {}
    for line in section_lines(body, "## Success Criteria"):
        m = SC_LINE.match(line.strip())
        if m and not re.search(r"—\s*gugur:", m.group(2)):
            out[m.group(1)] = m.group(2).strip()
    return out


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
    except OSError:
        return "", []
    lane = fm.get("lane", "")
    return (lane.strip() if isinstance(lane, str) else ""), parse_sections(fm.get("sections", ""))


# ================================================================ 4. ledger `## Chain`

# Urutan kanonik baris ledger. Satu baris per hop yang dijadwalkan lane-nya.
CHAIN_SPEC = (
    ("FLOW", "frontenddev:ux-design", "FLOW.md", "APPROVED"),
    ("UI", "frontenddev:ui-design", "UI.md", "APPROVED"),
    ("CONTRACT", "frontenddev:contract", "CONTRACT.md", "APPROVED"),
    ("BRIEF", "frontenddev:plan", BRIEF_GLOB, "READY"),
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
    """Isi dokumen tanpa baris `status:` frontmatter — basis uji keutuhan konten."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    head = re.sub(r"^status:.*\n?", "", text[3:end], flags=re.MULTILINE)
    return "---" + head + text[end:]


def show_at(root: Path, sha: str, rel: str) -> Optional[str]:
    """Isi berkas `rel` pada commit `sha`, atau `None` bila tidak ada di sana."""
    try:
        return subprocess.check_output(["git", "-C", str(root), "show", f"{sha}:{rel}"],
                                       stderr=subprocess.DEVNULL, universal_newlines=True)
    except Exception:
        return None


def doc_drift(root: Path, rel: str, sha: str) -> str:
    """Kosong bila isi `rel` di disk sama dengan isinya di `sha` kecuali baris `status:`."""
    then = show_at(root, sha, rel)
    if then is None:
        return f"`{rel}` tidak ada pada commit {sha}"
    path = root / rel
    if not path.is_file():
        return f"`{rel}` hilang dari disk"
    now = path.read_text(encoding="utf-8")
    if strip_status_line(now) != strip_status_line(then):
        return f"`{rel}` berubah sesudah disetujui @ {sha}"
    return ""


def brief_set_drift(root: Path, taskdir_rel: str, sha: str) -> str:
    """Kosong bila himpunan brief + `REVIEW-PLAN.md` sama dengan saat `sha`, kecuali baris status."""
    listed = git(root, "ls-tree", "--name-only", sha, f"{taskdir_rel}/").splitlines()
    then = sorted(Path(p).name for p in listed if re.match(r"brief-\d{2}-.*\.md$", Path(p).name))
    now = sorted(p.name for p in (root / taskdir_rel).glob(BRIEF_GLOB))
    if then != now:
        added = sorted(set(now) - set(then))
        gone = sorted(set(then) - set(now))
        parts = ([f"ditambah {', '.join(added)}"] if added else []) + \
                ([f"hilang {', '.join(gone)}"] if gone else [])
        return "himpunan brief berubah sesudah breakdown disetujui: " + "; ".join(parts)
    for name in now + (["REVIEW-PLAN.md"] if "REVIEW-PLAN.md" in
                       [Path(p).name for p in listed] else []):
        drift = doc_drift(root, f"{taskdir_rel}/{name}", sha)
        if drift:
            return drift
    allowed = {("READY", "READY"), ("READY", "DONE"), ("READY", "BLOCKED"), ("DONE", "DONE"),
               ("DONE", "BLOCKED"), ("BLOCKED", "BLOCKED")}
    for name in now:
        rel = f"{taskdir_rel}/{name}"
        before = parse_frontmatter(show_at(root, sha, rel) or "").get("status", "")
        after = read_status(root / rel)
        if (str(before).strip(), after) not in allowed:
            return f"`{name}` berpindah status `{before}` → `{after}` — transisi di luar siklus brief"
    return ""


def count_subjects(root: Path, pattern: str, *paths: str) -> int:
    """Jumlah commit yang subjeknya cocok `pattern` (regex), opsional terbatas `paths`."""
    out = git(root, "log", "--format=%s", "--", *paths) if paths else git(root, "log", "--format=%s")
    rx = re.compile(pattern)
    return sum(1 for s in out.splitlines() if rx.search(s))


def revisions_since_open(root: Path, rel_paths: List[str], slug: str, label: str) -> int:
    """Revisi berturut sejak draft/reopen terakhir: subjek `docs(<slug>): revise <label>`."""
    out = git(root, "log", "--format=%s", "--", *rel_paths)
    count = 0
    for subject in out.splitlines():
        if subject.startswith(f"docs({slug}): revise {label}"):
            count += 1
        elif (subject.startswith(f"docs({slug}): draft {label}")
              or subject.startswith(f"docs({slug}): reopen")
              or subject.startswith(f"docs({slug}): approve {label}")):
            break
    return count


# ================================================================ 5. blok check & laporan

AddFn = Callable[..., None]


def format_report(title: str, results: List[Dict[str, Any]],
                  resolved: Optional[Dict[str, str]] = None) -> str:
    """Keluaran teks baku skrip prasyarat; `resolved` menjadi baris `Terselesaikan:`."""
    results = sorted(results, key=lambda r: (str(r["id"]).zfill(3)))
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    label = "FAIL" if failed else ("PASS (WARN)" if warned else "PASS")
    lines = [f"PRECONDITION CHECK: {title} [{label}] ({passed}/{len(results)} passed"
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
                f"Gate `{skill}` tidak dicakup lane MINOR; kembali ke `frontenddev:lead`.")
            return False
        add(cid, name, "PASS", f"sections `{','.join(sections)}`")
        return True
    if required not in sections:
        add(cid, name, "FAIL", f"sections `{','.join(sections) or '-'}` tidak memuat `{required}`",
            f"Gate `{skill}` tidak dicakup taskdir ini; kembali ke `frontenddev:lead` "
            "untuk rute yang benar.")
        return False
    add(cid, name, "PASS", f"sections `{','.join(sections)}`")
    return True


def check_taskdir(add: AddFn, cid: int, root: Path, taskdir_rel: str) -> bool:
    name = "Bentuk & keberadaan taskdir"
    if not TASKDIR_PATTERN.match(taskdir_rel):
        add(cid, name, "FAIL",
            f"`{taskdir_rel}` tidak berpola frontenddev/docs/<YYMMDDhhmm>-<slug>",
            "Tetapkan taskdir lewat `frontenddev:lead` Phase 5.")
        return False
    if not (root / taskdir_rel).is_dir():
        add(cid, name, "FAIL", f"`{taskdir_rel}` tidak ada",
            "Buat taskdir lewat gate `frontenddev:lead` lebih dulu; dilarang mengarang direktori pengganti.")
        return False
    add(cid, name, "PASS", f"{taskdir_rel} sah")
    return True


def check_profile(add: AddFn, cid: int, profile_dir: Path, required: Tuple[str, ...]) -> str:
    """Check profil; mengembalikan stack terbaca atau string kosong."""
    name = "Profil repo memuat berkas wajib"
    if not profile_dir.is_dir():
        add(cid, name, "FAIL", f"`{DEFAULT_PROFILE_DIR}/` tidak ada",
            "Jalankan `frontenddev:profile` lebih dulu.")
        return ""
    owner = profile_owner(profile_dir)
    if owner and owner != PLUGIN:
        add(cid, name, "FAIL", f"profil milik `{owner}`; bukan profil {PLUGIN}",
            f"Jangan membaca atau menimpa profil plugin lain; jalankan `frontenddev:profile` "
            f"(ditulis ke `{DEFAULT_PROFILE_DIR}/`).")
        return ""
    stack, missing = load_profile(profile_dir, required)
    if missing:
        add(cid, name, "FAIL", f"{len(missing)} berkas profil hilang: " + ", ".join(missing),
            "Jalankan `frontenddev:profile` mode REFRESH untuk menulis ulang profil.")
        return ""
    if not stack:
        add(cid, name, "FAIL", "field `stack` tidak terbaca dari `index.json`",
            "`index.json` rusak atau tanpa field `stack`; jalankan `frontenddev:profile` mode REFRESH.")
        return ""
    note = ""
    if is_legacy_profile_dir(profile_dir):
        note = "; profil masih di lokasi lama `.claude/profile/` — jalankan `frontenddev:profile` mode MIGRATE"
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


def check_worktree(add: AddFn, cid: int, root: Path, taskdir_rel: str = "") -> bool:
    name = "Working tree bersih"
    if not is_git_repo(root):
        add(cid, name, "FAIL", "git tidak dapat membaca repo (bukan repo git, atau ditolak git)",
            "Jalankan di root repo git yang sah; tree yang tak terbaca tidak pernah dianggap bersih.")
        return False
    dirty = dirty_lines(root)
    if dirty:
        paths = [l[3:].strip().strip('"') for l in dirty]
        preview = ", ".join(paths[:5])
        own = bool(taskdir_rel) and all(p.startswith(taskdir_rel + "/") for p in paths)
        add(cid, name, "FAIL", f"{len(dirty)} berkas belum bersih: {preview}",
            "Seluruhnya artefak taskdir ini dari sesi lalu. `CONTRACT.md` atau batch brief lane "
            "non-MINOR: commit hanya lewat `review_round.py commit --gate <contract|plan> --subject "
            "\"<subjek gate pemiliknya>\"` — skrip menolak bila ronde reviewer terakhir belum `PASS` "
            "atas konten itu (cek dulu: `review_round.py status --ready`); ditolak → **jangan commit**, "
            "lanjutkan dari validator + ronde reviewer gate itu. Brief lane MINOR dan `FLOW.md`/`UI.md` "
            "(tanpa ronde): commit hanya bila validator gate itu `PASS`. Lalu ulangi prasyarat."
            if own else
            "Commit atomik gate ini menuntut tree bersih. Kotoran yang bukan milik rantai "
            "adalah kerja user — laporkan, jangan di-stash sendiri.")
        return False
    add(cid, name, "PASS", "nol perubahan menggantung")
    return True


def check_task_root(add: AddFn, cid: int, root: Path, taskdir_rel: str) -> Tuple[str, List[str]]:
    """`TASK.md` akar wajib ada, ter-commit, `ACTIVE`, dan pasangan lane/sections-nya sah.

    Mengembalikan `(lane, sections)` bila lolos, atau `("", [])`. Taskdir tanpa
    `TASK.md` selalu `FAIL`: sejak v0.4.0 tidak ada lagi taskdir warisan yang
    dilayani tanpa akar.
    """
    name = "TASK.md akar, lane & sections"
    rel = f"{taskdir_rel}/TASK.md"
    path = root / rel
    if not path.is_file():
        add(cid, name, "FAIL", "`TASK.md` tidak ada di taskdir",
            "Kunci akar lewat `frontenddev:task` (dipanggil `frontenddev:lead` Phase 7) lebih dulu.")
        return "", []
    if not is_committed(root, rel):
        add(cid, name, "FAIL", "`TASK.md` belum ter-commit atau punya perubahan menggantung",
            "Akar wajib terkunci commit sebelum gate hilir berangkat.")
        return "", []
    status = read_status(path)
    if status != "ACTIVE":
        add(cid, name, "FAIL", f"`TASK.md` berstatus `{status or '(kosong)'}`",
            "Hanya `status: ACTIVE` yang sah; kembali ke `frontenddev:lead`.")
        return "", []
    lane, sections = task_lane_sections(path)
    problem = lane_sections_problem(lane, sections) or lane_tamper(root, taskdir_rel)
    if problem:
        add(cid, name, "FAIL", problem,
            "Perbaiki lewat `chain.py escalate` di `frontenddev:lead`; dilarang menyunting "
            "frontmatter `TASK.md` dengan tangan.")
        return "", []
    add(cid, name, "PASS", f"TASK.md `ACTIVE`, lane `{lane}`, sections `{','.join(sections) or '-'}`")
    return lane, sections


def lane_tamper(root: Path, taskdir_rel: str) -> str:
    """Kosong bila `lane`/`sections` sekarang sama dengan yang ditulis commit akar atau eskalasi terakhir."""
    rel = f"{taskdir_rel}/TASK.md"
    slug = taskdir_slug(taskdir_rel)
    for line in git(root, "log", "--format=%H %s", "--", rel).splitlines():
        sha, _, subject = line.partition(" ")
        if subject.startswith(f"docs({slug}): eskalasi lane") or subject.startswith(f"docs({slug}): kunci TASK"):
            then = parse_frontmatter(show_at(root, sha, rel) or "")
            now = parse_frontmatter((root / rel).read_text(encoding="utf-8"))
            if (str(then.get("lane", "")).strip(), sorted(parse_sections(then.get("sections", "")))) != \
               (str(now.get("lane", "")).strip(), sorted(parse_sections(now.get("sections", "")))):
                return "`lane`/`sections` berubah di luar commit akar atau `chain.py escalate`"
            return ""
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
    """Sidik sha1 isi berkas di disk tanpa baris `status:` — basis vonis ronde reviewer."""
    return _snapshot(rels, lambda r: (root / r).read_text(encoding="utf-8") if (root / r).is_file() else None)


def snapshot_at(root: Path, sha: str, rels: List[str]) -> str:
    """Sidik yang sama dengan `content_snapshot`, atas isi berkas di commit `sha`."""
    def read(rel: str) -> Optional[str]:
        proc = subprocess.run(["git", "-C", str(root), "show", f"{sha}:{rel}"],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if proc.returncode != 0:
            return None
        # samakan dengan Path.read_text(): newline universal
        return proc.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return _snapshot(rels, read)


def gate_targets_at(root: Path, taskdir_rel: str, gate: str, sha: str) -> List[str]:
    """Berkas yang direview gate pada commit `sha` — padanan `Rounds.targets()` di disk."""
    if gate == "contract":
        return [f"{taskdir_rel}/CONTRACT.md"]
    names = git(root, "ls-tree", "--name-only", sha, f"{taskdir_rel}/").splitlines()
    return sorted(n for n in names if fnmatch.fnmatch(Path(n).name, BRIEF_GLOB))


def reopen_epoch(root: Path, taskdir_rel: str, gate: str) -> int:
    """Jumlah commit `reopen` yang membuka hop gate ini (sebagai target atau lewat kaskade).

    Regexnya sama dengan `verify_chain_row`: kaskade memang membuka hop gate ini.
    Angka, bukan sha, supaya tahan rebase.
    """
    slug = re.escape(taskdir_slug(taskdir_rel))
    return count_subjects(root, rf"^docs\({slug}\): reopen [A-Z ]*\b{GATE_ROW[gate]}\b",
                          f"{taskdir_rel}/TASK.md")


def verify_chain_row(root: Path, taskdir_rel: str, entry: Dict[str, Any]) -> str:
    """Kosong bila satu baris ledger `[x]` sah: sha ada, dok APPROVED/READY, konten utuh."""
    row = entry["row"]
    if entry["mark"] != "x":
        state = "belum berangkat" if entry["mark"] == " " else f"dibuka ulang (re-entry {entry['n']})"
        return f"hop `{row}` {state}"
    sha = entry["sha"]
    if not sha or not git(root, "cat-file", "-t", sha).strip():
        return f"hop `{row}` bersha `{sha or '(kosong)'}` yang tidak ada di repo"
    task_rel = f"{taskdir_rel}/TASK.md"
    stamp = git(root, "log", "--format=%H", "--fixed-strings", "--all-match",
                f"--grep=Konten disetujui: {sha}", f"--grep=Hop: {row}", "--", task_rel).strip()
    if not stamp:
        return (f"hop `{row}` tercentang tanpa commit `chain.py approve` yang memateraikan {sha} — "
                "centang tulisan tangan")
    slug = taskdir_slug(taskdir_rel)
    reopens = [l.split(" ", 1)[0] for l in git(root, "log", "--format=%H %s", "--", task_rel).splitlines()
               if re.match(rf"^\S+ docs\({re.escape(slug)}\): reopen [A-Z ]*\b{row}\b", l)]
    if reopens and stamp.splitlines()[0] not in git(root, "log", "--format=%H", f"{reopens[0]}..HEAD",
                                                     "--", task_rel).split():
        return (f"hop `{row}` dicentang dengan approval lama {sha} padahal sudah dibuka ulang — "
                "centang tulisan tangan; setujui ulang lewat `chain.py approve`")
    then_task = show_at(root, stamp.splitlines()[0], task_rel) or ""
    if sc_ids(then_task) != sc_ids((root / task_rel).read_text(encoding="utf-8")):
        return f"`SC-{{n}}` TASK.md berubah sesudah hop `{row}` disetujui — hop wajib dibuka ulang"
    if row in DOC_ROWS:
        doc = CHAIN_BY_ROW[row][2]
        rel = f"{taskdir_rel}/{doc}"
        status = read_status(root / rel)
        if status != "APPROVED":
            return f"`{doc}` berstatus `{status or '(kosong)'}` padahal hop `{row}` tercentang"
        return doc_drift(root, rel, sha)
    return brief_set_drift(root, taskdir_rel, sha)


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
    except OSError:
        add(cid, name, "FAIL", "`TASK.md` tidak terbaca", "Perbaiki check akar lebih dulu.")
        return False
    expected = expected_rows(sections)
    present = [e["row"] for e in entries]
    if present != expected:
        add(cid, name, "FAIL", f"baris ledger {present} ≠ jadwal sections {expected}",
            "Ledger ditulis `frontenddev:task` dan diubah hanya lewat `chain.py escalate`.")
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
    """WARN bila artefak milik gate ini sudah ada dari sesi sebelumnya."""
    name = f"{doc} tertunda dari sesi lalu"
    path = root / taskdir_rel / doc
    if not path.is_file():
        add(cid, name, "PASS", f"`{doc}` belum ada — sesi baru")
        return
    status = read_status(path) or "(kosong)"
    if status == "APPROVED":
        add(cid, name, "FAIL", f"`{doc}` sudah `APPROVED`",
            "Gate ini sudah tuntas. Revisi atas dokumen yang disetujui hanya lewat "
            "`chain.py reopen` di `frontenddev:lead`.")
        return
    if doc == "CONTRACT.md":
        ready = contract_review_ready(root, taskdir_rel)
        if ready:
            add(cid, name, "WARN", f"`{doc}` tertunda berstatus `{status}`; belum layak diajukan: {ready}",
                "Jangan commit dan jangan ajukan ke user: lanjutkan perbaikan draft, `validate_doc.py` "
                "sampai `PASS`, lalu ronde reviewer (Phase 5 butir 2–3) sebelum diajukan.")
            return
        add(cid, name, "WARN", f"`{doc}` tertunda berstatus `{status}`; ronde terakhir `PASS` atas konten ini",
            "Belum ter-commit → `review_round.py commit` (Phase 6 butir 1). Lalu tanyakan ke user "
            "apakah draft diputuskan (setuju/revisi) atau ditulis ulang, sebelum Phase 0 berjalan.")
        return
    add(cid, name, "WARN", f"`{doc}` sudah ada berstatus `{status}`",
        "Lanjutkan dari draft itu: tanyakan ke user apakah draft diputuskan (setuju/revisi) "
        "atau ditulis ulang, sebelum Phase 0 berjalan.")


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


def task_root_sha(root: Path, taskdir_rel: str) -> str:
    """SHA commit yang melahirkan `TASK.md` — titik awal rentang rantai, atau kosong."""
    out = git(root, "log", "--diff-filter=A", "--format=%H", "--", f"{taskdir_rel}/TASK.md")
    lines = [l for l in out.splitlines() if l.strip()]
    return lines[-1].strip() if lines else ""


def taskdir_slug(taskdir_rel: str) -> str:
    """Slug dari nama taskdir `<YYMMDDhhmm>-<slug>`."""
    return taskdir_rel.rstrip("/").rsplit("/", 1)[-1].split("-", 1)[-1]


def chain_files(root: Path, taskdir_rel: str) -> List[str]:
    """Berkas di luar `frontenddev/docs` yang diubah commit rantai sesudah akar.

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
    files: List[str] = []
    for sha in chain_commits(root, taskdir_rel, since):
        out = git(root, "show", "--name-only", "--format=", sha, "--", ".",
                  ":(exclude)frontenddev/docs", ":(exclude).claude")
        files += [l.strip() for l in out.splitlines() if l.strip()]
    return files


def review_is_fresh(root: Path, taskdir_rel: str) -> bool:
    """`REVIEW.md` lebih baru daripada commit `implement unit` terakhir taskdir ini.

    Unit yang mendarat sesudah review penutup belum pernah dinilai; review
    lama tidak boleh dipakai sebagai penutup rantai yang sudah bertambah.
    """
    rel = f"{taskdir_rel}/REVIEW.md"
    review_sha = last_commit(root, rel)
    if not review_sha:
        return False
    later = git(root, "log", f"{review_sha}..HEAD", "--format=%s", "--", f"{taskdir_rel}/{BRIEF_GLOB}")
    return not any("implement unit" in s for s in later.splitlines())


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


def brief_closure(taskdir: Path) -> Dict[str, Tuple[str, bool]]:
    """`{NN: (status, tertutup)}` — tertutup = `DONE`, atau `BLOCKED` yang remedinya tertutup.

    Remedi dikenali dari field `remedies: "NN"` brief. Dipakai `architect`
    (fase rantai, prasyarat `depends_on`) dan `report` (seluruh unit tertutup).
    """
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

    def closed(nn: str, seen: Tuple[str, ...] = ()) -> bool:
        if nn in seen or nn not in status:
            return False
        if status[nn] == "DONE":
            return True
        return status[nn] == "BLOCKED" and any(closed(r, seen + (nn,)) for r in remedies.get(nn, []))

    return {nn: (status[nn], closed(nn)) for nn in briefs}
