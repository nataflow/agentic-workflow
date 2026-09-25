# Langkah 5 — Parsing & Pustaka Bersama (detail)

> Rincian L5.1–L5.9 dari `ISSUES.md`. Semua klaim diperiksa ulang terhadap commit `34684ee` (2026-09-24). Reproduksi dijalankan di `mktemp -d` dengan Python 3.13.5 dan git 2.47.3; repo tidak disentuh. Nomor baris mengacu `34684ee`. Path relatif root repo kecuali disebut lain.

**Tujuan.** Tiap plugin punya satu parser untuk tiap jenis data: frontmatter, taskdir, chain, status git, placeholder, dan alat ukur. Semua skrip memakai parser yang sama. Dengan begitu vonis gerbang tidak lagi bergantung pada substring di badan dokumen, path berkutip dari git, atau salinan kode yang sudah divergen.

## Urutan pengerjaan

| # | Pekerjaan | Item | Alasan |
|---|---|---|---|
| 0 | Fondasi test `tests/conftest.py` dan test karakterisasi (golden) 14 skrip backenddev | L6.1 (sub-tugas 3 dan 8) | Belum ada test sama sekali, dan refactor di bawah menyentuh 14 skrip |
| 1 | Tambah API baru ke `backenddev/skills/_common/precondition_lib.py` beserta unit test-nya, tanpa mengganti satu call site pun | L5.5 bagian A | Fondasi untuk L5.1, L5.2, L5.4, dan L5.9-BE |
| 2 | Status dari frontmatter (system-analysis, plan) | **L5.1** | Satu-satunya item Tinggi |
| 3 | Status brief dan H1 (architect, report) | L5.9 (bagian backenddev) | Memakai `doc_status`/`count_h1` yang sama dengan L5.1 |
| 4 | Parser chain | L5.4 | Crash traceback |
| 5 | `check_taskdir` | L5.2 | |
| 6 | Sisa call site: `dirty_paths`, kunci index, path plugin, `find_repo_root`, keluaran | L5.5 | Mekanis; dikerjakan satu skrip per commit |
| 7 | `validate_briefs.py` backenddev | L5.3 | Tidak bergantung `_common`; boleh paralel sejak butir 0 |
| 8 | Jalur frontenddev: L5.8 → L5.7 → L5.6 → L5.9 (bagian frontenddev) | L5.6–L5.9 | Tidak bergantung jalur backenddev |
| 9 | analyst: buang BOM di `split_frontmatter` | L5.9 (bagian analyst) | Satu baris |

## Dependensi dengan langkah lain

- **Langkah 6 (L6.1), wajib lebih dulu.** Butuh `pytest.ini`, `tests/conftest.py` (fixture `git_repo`, `plain_dir`, `run_script`, `skill_script`, `Repo.write(..., crlf=, bom=)`), `tests/builders.py` (`be_profile`, `be_taskdir`), dan golden `assert_golden` sesuai `issues/06-test-ci.md`. Semua nama test di berkas ini memakai tata letak `tests/<plugin>/...` dari sana. Bila L6.1 memutuskan `src/plugins/<plugin>/tests/`, cukup pindahkan direktorinya. Test L5.1 dan L5.2 yang sudah ditulis di 06 (`test_brd_approved_dengan_kalimat_status_draft_di_body`, `test_brd_review_dengan_kalimat_refund_status_approved`, `test_taskdir_bukan_kanonik_ditolak`, `tests/analyst/test_ticket.py::test_state_ticket_ber_bom`) dipakai ulang; marker `xfail`-nya dicabut di commit perbaikan.
- **L6.2/L6.3.** CI menjalankan test dari langkah ini. Aturan lint "tidak ada path `.gemini`/repo-dev di skrip" baru bisa hijau setelah L5.5.
- **L1.1 (profil per plugin).** `load_profile_index` di bagian A sudah memakai konstanta `PROFILE_DIR`. Dengan begitu Opsi A L1.1 cukup mengganti satu baris. Kerjakan L5.5 sebelum L1.1 atau dalam PR yang sama.
- **L2.2/L2.3** mengubah `architect/_check_3_brief_readiness`, fungsi yang juga diubah L5.9-BE. Kerjakan L5.9-BE lebih dulu atau satukan dalam satu PR.
- **L4.2** menilai substansi `validate_review.py`/`validate_report.py`. Kerjakan L5.7, L5.8, dan L5.9-FE lebih dulu supaya L4.2 memakai `is_manual()` dan `outside_fences()` dari pustaka bersama.
- **Langkah 8:** separuh B6 (filter `.explore` terlalu luas) tertutup oleh `is_scratch()` di L5.5. B14 (path `~/.gemini` di tech-lead) tertutup oleh L5.5. B16 (`--brief 1`, `validate_briefs.py:431`) sengaja **tidak** dikerjakan di sini.

## Estimasi

| Item | Estimasi |
|---|---|
| L5.1 | 0,5 hari |
| L5.2 | 0,5 hari |
| L5.3 | 1 hari |
| L5.4 | 0,5 hari |
| L5.5 | 2 hari (termasuk bagian A) |
| L5.6 | 1 hari |
| L5.7 | 0,25 hari |
| L5.8 | 0,5 hari |
| L5.9 | 1 hari |
| **Total** | **7,25 hari**. Tambah ±1 hari bila fondasi L6.1 (butir 0) belum ada. |

## Berkas yang disentuh

| Berkas | Item |
|---|---|
| `src/plugins/backenddev/skills/_common/precondition_lib.py` | A, L5.1, L5.2, L5.4, L5.5, L5.9 |
| `src/plugins/backenddev/skills/{analyst,architect,audit,business-analysis,debug,document-api,plan,profile,report,system-analysis,task,tech-lead}/scripts/check_preconditions.py` (12) | L5.1, L5.2, L5.4, L5.5, L5.9 |
| `src/plugins/backenddev/skills/plan/scripts/validate_briefs.py` | L5.3, L5.4, L5.5 |
| `src/plugins/backenddev/skills/plan/scripts/scaffold_brief.py` | L5.4, L5.5 |
| `src/plugins/frontenddev/skills/_common/precondition_lib.py` | L5.6, L5.7, L5.8, L5.9 |
| `src/plugins/frontenddev/skills/_common/validate_doc.py` | L5.6, L5.7 |
| `src/plugins/frontenddev/skills/plan/scripts/validate_briefs.py` | L5.6 |
| `src/plugins/frontenddev/skills/task/scripts/validate_task.py` | L5.6, L5.7, L5.9 |
| `src/plugins/frontenddev/skills/architect/scripts/validate_review.py` | L5.7, L5.9 |
| `src/plugins/frontenddev/skills/report/scripts/validate_report.py` | L5.7, L5.8, L5.9 |
| `src/plugins/analyst/skills/_common/analyst_lib.py` | L5.9 |
| `tests/backenddev/`, `tests/frontenddev/`, `tests/analyst/` (baru) | semua |

`frontenddev/skills/lead/scripts/taskdir_state.py` tidak perlu diubah. Ia ikut benar begitu `split_frontmatter` frontenddev membuang BOM.

## Ringkasan koreksi terhadap ISSUES.md

1. **L5.5 `_find_repo_root`:** "4 varian" hanya berlaku pada teks (docstring dan koma). Perilakunya satu: semua memanggil `git rev-parse --show-toplevel` dari cwd dan jatuh ke `Path.cwd()`.
2. **L5.5 kunci wajib `index.json`:** bukan "7, 4, atau 1", melainkan 8 himpunan berbeda di 11 skrip (tabel B.1).
3. **L5.5 path `.gemini`:** di mesin ini path itu tidak mati. `~/.gemini/config/plugins/backenddev/agents/*.md` ada, sehingga fallback menutupi agent yang hilang dari plugin terpasang (FAIL berubah jadi PASS, direproduksi). Yang memang tidak pernah ada adalah `~/.claude/plugins/backenddev/...`, muncul 21 kali. Claude Code memasang plugin di `~/.claude/plugins/cache/<marketplace>/<plugin>/<versi>/`.
4. **L5.5 porcelain:** bukan hanya nama non-ASCII yang terkena. Nama berspasi (`catatan rapat.md`) juga dikutip git dan juga dilaporkan kotor oleh analyst/task.
5. **L5.9 status brief:** `status: DONE` di blok kode hanya terhitung bila baris status frontmatter tidak cocok `[A-Z_]+` (berkutip `"READY"`, huruf kecil, atau hilang) dan blok kodenya tidak terindentasi. Frontmatter `status: READY` yang benar tetap menang karena muncul lebih dulu.
6. **L5.9 BOM pada H1 TASK.md:** "ditemukan: 0" hanya terjadi bila H1 ada di baris pertama (TASK.md tanpa frontmatter). TASK.md berfrontmatter yang ber-BOM tetap PASS.
7. **L5.9 analyst:** `ticket.py state` memvonis RUSAK dengan pesan "status tidak sah (elicitation -, status -)". Pesan "requester kosong" datang dari `validate_doc.py`, bersama lima galat lain.
8. **L5.7:** ada pembaca keempat, `_common/validate_doc.py:302`, yang tidak peka huruf. Selain itu `validate_review.py:137` mencocokkan `QA manual:` di mana saja pada baris SC, bukan hanya di posisi alat ukur.
9. **L5.6:** `validate_task.py` **tidak** gagal untuk `` `<Spinner />` `` maupun "todo list". Ia gagal untuk SC `< 300 ms` dan juga untuk `<OrderRow>`. Ia juga meloloskan slot `` `src/features/<slug>/api.ts` `` (false negative).
10. **Temuan tambahan L5.3:** bila `## Migration requirements` PRD memuat "tidak perlu" di tengah kalimat, Check J mati (SKIP) padahal migrasi diminta.

## Definisi selesai langkah ini

- Kesembilan checkbox L5.1–L5.9 dicentang dan kriteria "Selesai bila" tiap item terpenuhi.
- `python -m pytest tests/backenddev tests/frontenddev tests/analyst` hijau. Setiap skenario "Reproduksi" di berkas ini sudah menjadi test tanpa `xfail`.
- Golden `--json` 12 skrip prasyarat backenddev (L6.1 sub-tugas 8) hanya berubah pada check yang memang diperbaiki.
- Gerbang grep di `src/plugins/backenddev/skills` bernilai nol:
  - `grep -rnE '"\.gemini"|"src" / "plugins"|"\.claude" / "plugins"'`
  - `grep -rnE 'def _find_repo_root|def _resolve_taskdir|def _get_rel_taskdir_str|def _declared_chain|def _porcelain_paths|def _strip_explore_scratch'`
  - `grep -rn 'in content.lower()'`
- `grep -l 'from precondition_lib import' src/plugins/backenddev/skills/*/scripts/*.py | wc -l` = 14.
- Setiap skrip reproduksi di berkas ini menghasilkan vonis kolom "harap".

---

## A. Rancangan API `_common` backenddev

**Keputusan letak:** tambahkan ke `src/plugins/backenddev/skills/_common/precondition_lib.py`, bukan modul baru. Alasannya, 8 skrip sudah mem-bootstrap `sys.path` ke direktori itu, sehingga cukup menambah nama di `from precondition_lib import (...)`. Tiga fungsi lama (`nearest_existing_ancestor`, `probe_writable`, `profile_staleness`) tetap ada. Docstring modul baris 4–10 ("hanya primitif yang byte-identik… dua fungsi… sembilan skrip") sudah basi dan ditulis ulang menjadi: *"Primitif parsing dan I/O bersama skrip prasyarat backenddev: frontmatter, taskdir, chain, status git, profil, berkas plugin, dan format keluaran. Check itu sendiri tetap tinggal di skripnya."*

| Fungsi / konstanta | Signature | Pengganti untuk | Item |
|---|---|---|---|
| `PLUGIN_ROOT`, `PROFILE_DIR`, `TASKDIR_RE`, `VALID_CHAINS`, `VALID_RISKS`, `REQUIRED_INDEX_KEYS` | konstanta | salinan konstanta di tiap skrip | L5.2, L5.4, L5.5 |
| `find_repo_root` | `(start: Optional[Path] = None) -> Path` | 14 × `_find_repo_root` | L5.5 |
| `is_scratch` | `(path: str) -> bool` | filter `.explore` di 5 skrip | L5.5 (B6) |
| `dirty_paths` | `(root: Path, exclude_scratch: bool = True) -> List[str]`; raise `GitError` | `_porcelain_paths`, `_strip_explore_scratch`, 2 loop manual | L5.5 |
| `is_under` | `(path: str, prefix: str) -> bool` | `startswith(rel + "/")`, `startswith(PREFIXES)` | L5.5 |
| `normalize_text` / `read_text` | `(text: str) -> str` / `(path: Path) -> str` | `read_text(encoding="utf-8")` tanpa normalisasi | L5.9 |
| `split_frontmatter` / `read_frontmatter` | `(text) -> (fields, body)` / `(path) -> (fields, body)`; raise `FrontmatterError` | regex `status:`/`chain:`/`risk:` di seluruh isi, parser mini `validate_briefs.py:508-515` | L5.1, L5.4 |
| `frontmatter_field` | `(path: Path, key: str) -> Optional[str]` | `plan._frontmatter`, `scaffold_brief.py:176,229`, `validate_briefs._risk_ceiling` | L5.4 |
| `doc_status` | `(path: Path, allowed: Sequence[str]) -> Tuple[Optional[str], str]` | status BRD/PRD/RCA/brief | L5.1, L5.9 |
| `iter_outside_fences` / `count_h1` | `(text) -> Iterable[(no, line)]` / `(text) -> int` | regex H1 `report:161` | L5.9 |
| `parse_enum` / `parse_chain` / `declared_chain` | `(value, allowed, label) -> (val, err)` / `(value) -> (val, err)` / `(taskdir) -> (val, err)` | `_declared_chain`, `_effective_chain`, `chain_arg = ...upper()` | L5.4 |
| `resolve_taskdir` / `check_taskdir` | `(root, arg) -> Path` / `(root, arg, must_exist=True) -> TaskdirVerdict` | `_resolve_taskdir`, `_get_rel_taskdir_str`, 8 check taskdir | L5.2 |
| `load_profile_index` | `(root, required=REQUIRED_INDEX_KEYS) -> (data, err)` | 11 blok baca `index.json` | L5.5 |
| `plugin_file` / `find_agent` | `(*parts) -> Optional[Path]` / `(name) -> Optional[Path]` | 29 daftar kandidat path | L5.5 |
| `format_text` / `to_json` / `freshness_banner` | lihat kode | 13 × `format_text`, 13 × `to_json` | L5.5 |

Implementasi. Kode di bawah sudah dijalankan: semua assert di `selftest_bd.py` scratchpad lolos, termasuk matriks taskdir L5.2, kasus L5.1, `-z` porcelain, dan urutan kunci JSON.

```python
# --- tambahan precondition_lib.py (impor baru: json, re, dataclasses, typing) ---
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PLUGIN_ROOT = Path(__file__).resolve().parents[2]          # src/plugins/backenddev
PROFILE_DIR = Path(".claude") / "profile"                  # L1.1 Opsi A cukup mengganti baris ini
TASKDIR_RE = re.compile(r"^backenddev/docs/\d{10}-[a-z0-9-]+$")
VALID_CHAINS = ("BRD_PRD_BRIEF", "PRD_BRIEF", "BRIEF")
VALID_RISKS = ("BREAKING", "MAJOR", "MINOR")
# Tujuh kunci yang ditulis profile/templates/profile-template.md bagian 1 dan dibaca skrip
# (`project` ditulis template tetapi tidak dibaca satu skrip pun).
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


# ------------------------------------------------------------ repo & git

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

    Tanpa kutip, tanpa escape oktal, rename/copy diwakili path tujuannya.
    Laci kerja (`is_scratch`) dibuang bila `exclude_scratch`. Raise `GitError` bila git gagal.
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
        if "R" in xy or "C" in xy:
            i += 1                      # entri berikutnya = path asal rename/copy
        if exclude_scratch and is_scratch(path):
            continue
        out.append(path)
    return out


def is_under(path: str, prefix: str) -> bool:
    """`path` sama dengan `prefix` atau berada di bawahnya, per segmen (bukan substring)."""
    a = [p for p in path.strip("/").split("/") if p not in ("", ".")]
    b = [p for p in prefix.strip("/").split("/") if p not in ("", ".")]
    return bool(b) and a[:len(b)] == b


# ------------------------------------------------------------ teks & frontmatter

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
    """`split_frontmatter` atas isi berkas. OSError dan FrontmatterError diteruskan ke pemanggil."""
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

    Nilai dibandingkan persis (huruf besar) dengan `allowed`.
    """
    try:
        fields, _ = read_frontmatter(path)
    except OSError as exc:
        return None, f"{Path(path).name} tidak terbaca: {exc}"
    except UnicodeDecodeError:
        return None, f"{Path(path).name} bukan UTF-8"
    except FrontmatterError as exc:
        return None, f"{Path(path).name}: {exc}"
    value = fields.get("status")
    if value is None:
        return None, f"{Path(path).name}: frontmatter tanpa kunci `status`"
    if value not in allowed:
        return None, f"{Path(path).name}: status `{value}` bukan salah satu dari {' | '.join(allowed)}"
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


# ------------------------------------------------------------ enum

def parse_enum(value: Optional[str], allowed: Sequence[str], label: str) -> Tuple[Optional[str], str]:
    """Normalkan nilai enum (trim, buka kutip, huruf besar) → `(NILAI, "")`, `(None, "")` bila
    kosong/-/—, atau `(None, galat)` bila asing."""
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


# ------------------------------------------------------------ taskdir

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
    """Vonis parameter taskdir: di dalam root, pola kanonik berjangkar, direktori (dan ada bila wajib)."""
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


# ------------------------------------------------------------ profil & berkas plugin

def load_profile_index(root: Path, required: Sequence[str] = REQUIRED_INDEX_KEYS
                       ) -> Tuple[Optional[Dict[str, Any]], str]:
    """`(data, "")` bila index.json profil sah dan memuat `required` non-kosong."""
    index = Path(root) / PROFILE_DIR / "index.json"
    if not index.is_file():
        return None, f"Berkas {PROFILE_DIR.as_posix()}/index.json tidak ditemukan"
    try:
        data = json.loads(read_text(index))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return None, f"Format JSON rusak pada index.json: {exc}"
    if not isinstance(data, dict):
        return None, "index.json bukan objek JSON"
    missing = [k for k in required if not str(data.get(k) or "").strip()]
    if missing:
        return None, f"Field kritis hilang/kosong di index.json: {', '.join(missing)}"
    return data, ""


def plugin_file(*parts: str) -> Optional[Path]:
    """Berkas milik plugin ini (relatif `src/plugins/backenddev/`), atau None bila tidak ada.
    Tidak ada fallback ke ~/.gemini, ~/.claude/plugins, atau salinan repo pengembang."""
    p = PLUGIN_ROOT.joinpath(*parts)
    return p if p.is_file() else None


def find_agent(name: str) -> Optional[Path]:
    return plugin_file("agents", f"{name}.md")


# ------------------------------------------------------------ keluaran

def format_text(skill: str, results: List[Dict[str, Any]], width: int = 32,
                header_suffix: str = "", banner: Optional[str] = None) -> str:
    passed = sum(1 for r in results if r["status"] == "PASS")
    label = "PASS" if passed == len(results) else "FAIL"
    lines = [f"PRECONDITION CHECK: {skill} [{label}] ({passed}/{len(results)} passed){header_suffix}"]
    for r in results:
        lines.append(f"[{r['id']}] {r['name']:<{width}} : {r['status']} ({r['summary']})")
        if r["status"] == "FAIL" and r.get("action"):
            lines.append(f"    * Tindakan: {r['action']}")
    if banner:
        lines.insert(0, banner)
    return "\n".join(lines)


def to_json(root: Path, results: List[Dict[str, Any]], **extra: Any) -> str:
    """Urutan kunci sama dengan 13 salinan lama: status, passed_count, total_count, root, extra…, checks."""
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
```

Method `format_text`/`to_json` di kelas tetap ada supaya `main()` tidak berubah, tetapi isinya tinggal satu baris. Contoh system-analysis:

```python
    def format_text(self) -> str:
        return format_text("system-analysis", self.results,
                           banner=freshness_banner(getattr(self, "profile_freshness", None)))

    def to_json(self) -> str:
        return to_json(self.root, self.results, taskdir=self.taskdir_arg,
                       risk_level=self.risk_level_arg, chain=self._effective_chain(),
                       profile_freshness=getattr(self, "profile_freshness", ("TAK_TERNILAI", ""))[0])
```

Bootstrap untuk 6 skrip yang belum mengimpor `_common` (analyst, architect, report, task, `scaffold_brief.py`, `validate_briefs.py`), disalin dari 8 skrip lain:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    check_taskdir, dirty_paths, doc_status, find_repo_root, format_text, to_json, ...
)
```

---

## B. Peta call site dan statistik duplikasi (backenddev)

Dihitung dengan AST (`ast.get_source_segment`, docstring dibuang untuk varian perilaku) dan grep atas `src/plugins/backenddev/skills/*/scripts/*.py` (14 berkas, 8.011 baris; `_common` 107 baris).

### B.1 Statistik

| Pola | Salinan | Varian | Catatan |
|---|---|---|---|
| `_find_repo_root` | 14 (12 `check_preconditions.py` + `scaffold_brief.py` + `validate_briefs.py`) | 4 teks, 2 AST (method vs fungsi modul), **1 perilaku** | Semua `git rev-parse --show-toplevel` dari cwd, fallback `Path.cwd()` |
| `format_text` | 13 | 13 AST. Bila nama skill diparameterkan tersisa **5**: lebar 32 polos (architect, audit, debug, document-api, profile, report), lebar 35 (analyst, task), lebar 32 + banner TERDEGRADASI (business-analysis, plan, system-analysis), tech-lead (lebar 28 + label mode + banner), `validate_briefs` (format sendiri) | |
| `to_json` | 13 | **11** AST. architect = debug = report identik. Kunci dasar sama; yang berbeda kunci tambahan | |
| `_resolve_taskdir` | 8 | 2 | `validate_briefs.py:244` tanpa guard `None` |
| `_get_rel_taskdir_str` | 4 | 1 | analyst, architect, report, task |
| Baca `chain:` TASK.md | 4 (`analyst:94`, `business-analysis:56`, `system-analysis:46`, `plan:99`) | 2 regex: `[A-Z_]+` vs `[A-Za-z_-]+` + `upper()` | Semua memindai seluruh isi, tidak hanya frontmatter |
| Baca `status:` | 7 lokasi (system-analysis 1, plan 2, architect 1, report 1, `scaffold_brief` 1, `validate_briefs` 1) | 4 | Hanya `validate_briefs` yang membatasi diri ke frontmatter |
| Baca `risk:` TASK.md | 3 (`plan:118`, `scaffold_brief:229`, `validate_briefs:667`) | 1 regex, seluruh isi | |
| Cek taskdir | 8 | **3**: OR + `re.search` (business-analysis, system-analysis, plan); AND + `re.match` + `exists()` (analyst, architect, report, task); hanya `exists()` (debug) | |
| Parsing `git status --porcelain` | 5 lokasi | **3**: buang kutip (architect/report `strip('"')`, tech-lead berpasangan); tanpa buang kutip (analyst, task); tanpa `-uall` (architect, report) | |
| Kunci wajib `index.json` | 11 skrip | **8 himpunan**: 7 kunci (tech-lead); 4A `root_namespace, source_root, stack, architecture` (business-analysis, system-analysis, plan); 4B `base_branch, commit_convention, source_root, stack` (architect); 3 `root_namespace, source_root, stack` (debug); 2 `base_branch, commit_convention` (report); 1 `commit_convention` (analyst, task); 1 `stack` (audit); `stack` opsional bila ada `--stack` (document-api) | Template profil menulis 8 kunci (7 + `project`) |
| `_strip_explore_scratch` | 2 (architect, report) | 1 | |
| `_read` | 2 (`scaffold_brief`, `validate_briefs`) | 1 | |
| `_doc_section` | 2 | 2 (beda kondisi `return`) | Di luar cakupan wajib langkah ini |
| Path `~/.gemini/config/plugins/backenddev/…` | **21** di 8 skrip | | Tabel B.3 |
| Path `self.root / "src" / "plugins" / "backenddev" / …` | **22** di 8 skrip | | Tabel B.3 |
| Path `~/.claude/plugins/backenddev/…` | **21** di 8 skrip | | Tidak ada di tata letak cache Claude Code |
| Impor `_common` | 8 dari 12 `check_preconditions.py`; 0 dari 2 skrip plan lain | | Tidak mengimpor: analyst, architect, report, task |

### B.2 Call site per skrip (lama → baru)

`check_preconditions.py` kecuali disebut lain. Semua baris mengacu `34684ee`.

**analyst** (belum mengimpor `_common`)

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 9–17 | tanpa bootstrap | bootstrap + `from precondition_lib import …` | L5.5 |
| 18–20 | `VALID_RISKS`, `VALID_CHAINS` lokal | impor dari lib | L5.4 |
| 47, 53–65 | `self._find_repo_root()` + def | `find_repo_root()`; def dihapus | L5.5 |
| 50 | `(chain or "auto").strip().upper()` | `"AUTO"` bila kosong/`auto`, selain itu `parse_chain(chain)` (galat → check 4 FAIL) | L5.4 |
| 77–92 | `_resolve_taskdir`, `_get_rel_taskdir_str` | `self.td = check_taskdir(self.root, taskdir)`, pakai `.path`/`.rel` | L5.2 |
| 94–107 | `_declared_chain` (regex seluruh isi) | `declared_chain(self.td.path)` | L5.4 |
| 121–144 | cek exists + `re.match` | `check_taskdir` (menolak berkas; symlink absolut lolos) | L5.2 |
| 169–190 | baca `commit_convention` | `load_profile_index(self.root)` | L5.5 |
| 268 | `declared = self._declared_chain()` | `declared, err = declared_chain(...)`; `err` → FAIL | L5.4 |
| 302, 315 | `... else self._declared_chain()`; `CHAIN_ARTIFACTS[effective_chain]` | chain tervalidasi dulu; galat → FAIL rapi | L5.4 |
| 364–386 | porcelain manual tanpa buang kutip | `dirty_paths(self.root)` + `is_under(p, rel)` | L5.5 |
| 417–444 | `format_text`, `to_json` | isi satu baris ke lib (lebar 32) | L5.5 |

**architect** (belum mengimpor `_common`)

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 19–38, 314–319 | `_strip_explore_scratch(git status --porcelain)` | `dirty_paths(self.root)` | L5.5 |
| 48, 53–65 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 77–92, 94–137 | resolve/rel + cek AND | `check_taskdir` | L5.2 |
| 156–167 | `required_keys` 4B | `load_profile_index(self.root)` | L5.5 |
| 228–243 | `re.search(r"^status:\s*([A-Z_]+)", content, re.M)` | `doc_status(bf, ("READY", "DONE", "BLOCKED"))` | L5.9 |
| 286–292 | ringkasan PASS tanpa BLOCKED/OTHER | ringkasan menyebut keempat hitungan | L5.9 |
| 378–392 | 2 daftar kandidat agent (4 path) | `find_agent("code-implementor")`, `find_agent("code-reviewer")` | L5.5 |
| 445–448 | `self.root/src/plugins/…/lifecycle-recovery.md` + `__file__` | `plugin_file("skills", "architect", "references", "lifecycle-recovery.md")` | L5.5 |
| 468–493 | `format_text`, `to_json` | lib | L5.5 |

**audit**

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 38, 43–55 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 128–147 | cek `data.get("stack")` | `load_profile_index(self.root)` | L5.5 |
| 186–191 | 4 kandidat adapter; `__file__` di urutan **terakhir** | `plugin_file("skills", "profile", "stacks", f"{stack}.md")` | L5.5 |
| 317–342 | `format_text`, `to_json` | lib | L5.5 |

**business-analysis**

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 45, 77–89 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 47 | `(chain or "").strip().upper() or None` | `parse_chain(chain)` | L5.4 |
| 50–75 | `_resolve_taskdir`, `_declared_chain`, `_effective_chain` | `check_taskdir(...).path`, `declared_chain` | L5.2, L5.4 |
| 117–137 | OR + `re.search` | `check_taskdir` | L5.2 |
| 159–172 | `required_keys` 4A | `load_profile_index(self.root)` | L5.5 |
| 328–332, 432–436 | kandidat `brd-reviewer`, `code-explorer` | `find_agent(...)` | L5.5 |
| 378–407 | validasi chain dari string mentah | pakai `(value, err)` parser | L5.4 |
| 466–497 | `format_text`, `to_json` | lib + banner | L5.5 |

**debug**

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 39, 45–57 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 84–97 | `required_keys` 3 | `load_profile_index(self.root)` | L5.5 |
| 179–184 | 4 kandidat adapter (`__file__` terakhir) | `plugin_file("skills", "profile", "stacks", ...)` | L5.5 |
| 231–235 | kandidat `code-explorer` | `find_agent("code-explorer")` | L5.5 |
| 283–295 | `td.exists()` saja | `check_taskdir(...)` sebelum `_probe_writable(v.path)` | L5.2 |
| 353–378 | `format_text`, `to_json` | lib | L5.5 |

**document-api**

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 39, 45–57 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 112–118 | `stack` dari index tanpa validasi | `load_profile_index(self.root, required=("stack",))` bila `--stack` kosong | L5.5 |
| 130–135 | 4 kandidat adapter | `plugin_file(...)` | L5.5 |
| 240–265 | `format_text`, `to_json` | lib | L5.5 |

**plan** (`check_preconditions.py`)

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 32–33 | `VALID_CHAINS`, `VALID_RISKS` lokal | impor | L5.4 |
| 62, 73–85 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 64–69 | `upper()` + penanda `—`/`-` | `parse_chain`, `parse_enum(risk, VALID_RISKS, "risk")` | L5.4 |
| 99–118 | `_frontmatter(field)` regex seluruh isi | `frontmatter_field(task, "chain"/"risk")` + parser enum | L5.4 |
| 120–124, 138–171 | resolve + OR/`re.search` | `check_taskdir` | L5.2 |
| 188–201 | `required_keys` 4A | `load_profile_index(self.root)` | L5.5 |
| 289–313 | status PRD (search + substring) | `doc_status(prd, ("DRAFT", "APPROVED"))` | **L5.1** |
| 343–367 | status RCA (search + substring) | `doc_status(rca, ("ROOT_CAUSE_CONFIRMED", "INCONCLUSIVE"))` | **L5.1** |
| 457–495 | 6 daftar kandidat (24 path) | `plugin_file("skills", "plan", ...)` | L5.5 |
| 571–584 | kandidat `brief-reviewer`, `code-explorer` | `find_agent(...)` | L5.5 |
| 734–768 | `format_text`, `to_json` | lib + banner | L5.5 |

**plan/`scaffold_brief.py`** (belum mengimpor `_common`)

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 83–93, 122 | `_find_repo_root()` modul | `find_repo_root()` | L5.5 |
| 96–100 | `_read` tanpa normalisasi | `read_text` (dibungkus try → None) | L5.9 |
| 176 | `re.search(r"^status:\s*([A-Za-z_-]+)\s*$", text, re.M)` | `frontmatter_field(p, "status")` | L5.4 |
| 229 | `re.search(r"^risk:…", self.task_text, re.M)` | `frontmatter_field(task, "risk")` + `parse_enum` | L5.4 |

**plan/`validate_briefs.py`** (belum mengimpor `_common`)

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 216, 231–242 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 244–246 | `_resolve_taskdir` | `resolve_taskdir(self.root, taskdir)` | L5.2 |
| 249–253 | `_read` | `read_text` | L5.9 |
| 508–515 | parser frontmatter mini (tanpa BOM) | `split_frontmatter` (FrontmatterError → frontmatter kosong, Check S FAIL) | L5.9 |
| 664–676 | `_risk_ceiling` regex seluruh isi | `frontmatter_field` + `parse_enum` (`-` → MINOR tetap) | L5.4 |
| 888–889 | `if cmd in low` | `BUILD_TEST_RE` | L5.3 |
| 1241–1247 | `_path_matches` substring | per segmen + glob | L5.3 |
| 1432, 1470 | `f"AC-{num}" in …` | `covers_ac` / `\bAC-{num}\b` | L5.3 |
| 1499, 1508 | `"tidak perlu" not in …` | `migration_declined()` | L5.3 |
| 1583–1646 | `format_text`/`to_json` sendiri | **tetap**: formatnya memang beda (bukan skrip prasyarat) | — |

**profile**

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 47, 53–65 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 236–261 | `format_text`, `to_json` | lib | L5.5 |

**report** (belum mengimpor `_common`)

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 19–38, 350–355 | `_strip_explore_scratch` | `dirty_paths(self.root)` | L5.5 |
| 48, 53–65 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 78–93, 95–138 | resolve/rel + cek AND | `check_taskdir` | L5.2 |
| 161 | `len(re.findall(r"^#\s+[^\n]+", content, re.M))` | `count_h1(content)` | L5.9 |
| 171 | `"## Success Criteria" not in content` | cari baris `## Success Criteria` lewat `iter_outside_fences` | L5.9 |
| 246–249 | regex status brief | `doc_status(bf, ("READY", "DONE", "BLOCKED"))` | L5.9 |
| 288–298 | `base_branch`, `commit_convention` | `load_profile_index(self.root)` | L5.5 |
| 383–408 | `format_text`, `to_json` | lib | L5.5 |

**system-analysis**

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 40, 67–79 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 43 | `(chain or "").strip().upper()` | `parse_chain(chain)` | L5.4 |
| 46–65 | `_effective_chain` regex `[A-Z_]+` | `declared_chain` | L5.4 |
| 93–97, 255–288 | resolve + OR/`re.search` | `check_taskdir` | L5.2 |
| 163–180 | status BRD (search + substring) | `doc_status(brd, ("DRAFT", "APPROVED"))` | **L5.1** |
| 199–212 | `required_keys` 4A | `load_profile_index(self.root)` | L5.5 |
| 351–362 | kandidat template/checklist | `plugin_file("skills", "system-analysis", ...)` | L5.5 |
| 434–438, 483–487 | kandidat `prd-reviewer`, `code-explorer` | `find_agent(...)` | L5.5 |
| 540–572 | `format_text`, `to_json` | lib + banner | L5.5 |

**task** (belum mengimpor `_common`)

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 55, 61–73 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 58 | `(chain or "").strip().upper() if chain else None` | `parse_chain(chain)` | L5.4 |
| 147–162, 176–200 | resolve/rel + cek AND | `check_taskdir` | L5.2 |
| 223–245 | baca `commit_convention` | `load_profile_index(self.root)` | L5.5 |
| 362–386 | porcelain manual | `dirty_paths` + `is_under` | L5.5 |
| 418–445 | `format_text`, `to_json` | lib (lebar 32) | L5.5 |

**tech-lead**

| Baris | Lama | Baru | Item |
|---|---|---|---|
| 44, 48–60 | `_find_repo_root` | `find_repo_root()` | L5.5 |
| 89–105 | `required_keys` 7 | `load_profile_index(self.root)` (sama isinya) | L5.5 |
| 205–224, 231–243 | `_porcelain_paths` + filter `.explore` | `dirty_paths(self.root)` | L5.5 |
| 246 | `p.startswith(RE_ENTRY_ALLOWED_PREFIXES)` | `any(is_under(p, x) for x in RE_ENTRY_ALLOWED_PREFIXES)` | L5.5 |
| 388–392 | kandidat `code-explorer` | `find_agent("code-explorer")` | L5.5 |
| 422–453 | `format_text` (lebar 28 + label mode), `to_json` | lib dengan `header_suffix` | L5.5 |

### B.3 Semua kemunculan path `.gemini` dan path repo-dev

Format sel: baris `.gemini` / baris `self.root/src/plugins/backenddev` / baris `~/.claude/plugins/backenddev`.

| Skrip | Target | Baris |
|---|---|---|
| audit | `skills/profile/stacks/<stack>.md` | 188 / 187 / 189 (kandidat `__file__` di 190, **terakhir**) |
| business-analysis | `agents/brd-reviewer.md` | 330 / 329 / 331 |
| business-analysis | `agents/code-explorer.md` | 434 / 433 / 435 |
| architect | `agents/code-implementor.md` | 381 / 380 / 382 |
| architect | `agents/code-reviewer.md` | 390 / 389 / 391 |
| architect | `references/lifecycle-recovery.md` | — / 446 / — |
| tech-lead | `agents/code-explorer.md` | 390 / 389 / 391 |
| debug | `skills/profile/stacks/<stack>.md` | 181 / 180 / 182 (`__file__` di 183, terakhir) |
| debug | `agents/code-explorer.md` | 233 / 232 / 234 |
| document-api | `skills/profile/stacks/<stack>.md` | 132 / 131 / 133 (`__file__` di 134, terakhir) |
| system-analysis | `templates/prd-template.md` | 354 / 353 / 355 |
| system-analysis | `references/analysis-protocol.md` | 361 / 360 / 362 |
| system-analysis | `agents/prd-reviewer.md` | 436 / 435 / 437 |
| system-analysis | `agents/code-explorer.md` | 485 / 484 / 486 |
| plan | `templates/brief-template.md` | 460 / 459 / 461 |
| plan | `references/entry-rules.md` | 466 / 465 / 467 |
| plan | `references/slicing-and-scan.md` | 472 / 471 / 473 |
| plan | `references/review-and-commit.md` | 478 / 477 / 479 |
| plan | `scripts/scaffold_brief.py` | 487 / 486 / 488 |
| plan | `scripts/validate_briefs.py` | 493 / 492 / 494 |
| plan | `agents/brief-reviewer.md` | 573 / 572 / 574 |
| plan | `agents/code-explorer.md` | 582 / 581 / 583 |
| **Total** | | **21 / 22 / 21** |

---

## C. Urutan refactor yang aman

Hari ini belum ada test sama sekali. Karena itu setiap langkah harus dimulai dengan membekukan perilaku lama.

1. **C.0 Fondasi** (bagian L6.1, butir 0 tabel urutan): `pytest.ini` (`xfail_strict = true`), `tests/conftest.py`, `tests/builders.py` sesuai `issues/06-test-ci.md`. Tambah helper `load_module(path, name)` yang memakai `importlib.util.spec_from_file_location`. Helper ini wajib karena backenddev dan frontenddev sama-sama punya modul bernama `precondition_lib`. Impor lewat `sys.path` di satu sesi pytest akan bertabrakan di `sys.modules`.
2. **C.1 Karakterisasi.** Rekam golden `--json` 12 skrip prasyarat × 4 fixture (kosong, profil lengkap, taskdir DRAFT, taskdir siap eksekusi), kunci `root` dibuang. Tambahkan setiap skenario "Reproduksi" di berkas ini sebagai test `@pytest.mark.xfail(reason="L5.x: …")`. Test ini harus gagal karena alasan yang benar; periksa dengan `--runxfail --tb=line`.
3. **C.2 API tanpa call site.** Tambahkan bagian A ke `precondition_lib.py` beserta `tests/backenddev/test_common_*.py`. Golden tidak boleh berubah karena belum ada skrip yang memakainya.
4. **C.3 Satu skrip per commit**, dengan urutan: system-analysis → plan → business-analysis → analyst → task → architect → report → tech-lead → debug → audit → document-api → profile → `scaffold_brief.py` → `validate_briefs.py`. Tiap commit terdiri dari dua langkah:
   1. **Pergantian mekanis** (`find_repo_root`, `format_text`/`to_json`, `find_agent`/`plugin_file`, `load_profile_index`). Golden harus identik, kecuali lebar kolom teks dan check profil pada fixture yang kuncinya sengaja kurang (keputusan 1).
   2. **Perbaikan semantik** (status, chain, taskdir, dirty) untuk ID item yang dikerjakan. Cabut `xfail` yang relevan. Golden hanya boleh berubah pada check itu. Perbarui golden-nya dalam commit yang sama dan sebut ID-nya di pesan commit.
5. **C.4 Pembersihan.** Hapus fungsi yang tidak dipakai lagi dan tulis ulang docstring `_common`, lalu jalankan gerbang grep di "Definisi selesai". Sebelum mengubah teks `summary`/`action`, cek `grep -rn '<pesan lama>' src/plugins/backenddev/skills/*/SKILL.md src/plugins/backenddev/skills/*/references/`. Beberapa SKILL mungkin mengutip pesan skrip.

Jalur frontenddev (L5.6–L5.9-FE) dan analyst ikut pola yang sama. Bedanya, fungsinya sudah terpusat di `precondition_lib.py` frontenddev, jadi pekerjaannya lebih kecil.

---

## L5.1 [Tinggi] Status dokumen backenddev dicari sebagai substring di seluruh isi

- [ ] Selesai

**Plugin:** backenddev · **Estimasi:** 0,5 hari · **Bergantung pada:** C.0–C.2 (`split_frontmatter`, `doc_status`) · **Memblokir:** L5.9-BE (memakai `doc_status` yang sama)

### Konteks

Gerbang hop PRD (system-analysis) dan hop brief (plan) membaca status BRD/PRD/RCA dengan dua cara yang sama-sama salah:

- `re.search(r"status:\s*([A-Z_]+)", content, re.IGNORECASE)` mengambil kemunculan `status:` **pertama di mana saja**;
- lalu OR dengan substring `"status: draft" in content.lower()` di **seluruh isi**.

Frontmatter tidak pernah dipisahkan dari badan. Padahal kepemilikan `status: APPROVED` adalah invarian rantai (`analyst/references/chain-rules.md` bagian 4), dan kata "status" lazim di domain (order, invoice, refund).

### Lokasi & kode saat ini

`src/plugins/backenddev/skills/system-analysis/scripts/check_preconditions.py:165-178`

```python
165:        status_match = re.search(r"status:\s*([A-Z_]+)", content, re.IGNORECASE)
166:        status_val = status_match.group(1).upper() if status_match else ""
168:        if "DRAFT" in status_val or "status: draft" in content.lower():
169:            fail(
170:                "BRD.md masih berstatus DRAFT",
175:        if "APPROVED" not in status_val and "status: approved" not in content.lower():
176:            fail(
177:                "Status BRD.md tidak terdefinisi APPROVED",
```

`src/plugins/backenddev/skills/plan/scripts/check_preconditions.py:290-304` (PRD) dan `:344-358` (RCA, pola identik dengan `INCONCLUSIVE`/`ROOT_CAUSE_CONFIRMED`)

```python
290:                content = prd_file.read_text(encoding="utf-8")
291:                status_match = re.search(r"status:\s*([A-Z_]+)", content, re.IGNORECASE)
292:                status_val = status_match.group(1).upper() if status_match else ""
294:                if "DRAFT" in status_val or "status: draft" in content.lower():
304:                if "APPROVED" not in status_val and "status: approved" not in content.lower():
```

### Reproduksi

```bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
S=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); cd "$tmp" && git init -q && git config user.email t@t && git config user.name t
mkdir -p .claude/profile backenddev/docs/2601011200-refund src
cat > .claude/profile/index.json <<'J'
{"stack":"go","architecture":"layered","root_namespace":"x","source_root":"src","commit_convention":"c","base_branch":"main","branch_convention":"feat/<slug>"}
J
for f in commands code-conventions anti-patterns invariants; do echo "# $f" > .claude/profile/$f.md; done
TD=backenddev/docs/2601011200-refund
printf -- '---\nchain: BRD_PRD_BRIEF\n---\n# T\n' > $TD/TASK.md
git add -A && git commit -qm init
sa() { python3 $S/system-analysis/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --risk-level MAJOR --chain BRD_PRD_BRIEF | grep '^\[1\]'; }
pl() { python3 $S/plan/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --entry-mode "$1" --chain "$2" --risk MAJOR | grep '^\[3\]'; }

echo "== Kasus 1: PRD APPROVED, badan menyebut 'status: DRAFT'"
printf -- '---\ntitle: Refund\nsource_brd: x\nstatus: APPROVED\n---\n# PRD\n\n## Business rules\n- Order dengan status: DRAFT ditolak.\n' > $TD/PRD.md
pl PRD BRD_PRD_BRIEF
echo "== Kasus 2: BRD APPROVED, badan menyebut 'status: DRAFT'"
printf -- '---\ntitle: Refund\nrequester: ops\nstatus: APPROVED\n---\n# BRD\n\n## Business rules\n- **BR-1**: Order dengan status: DRAFT ditolak.\n' > $TD/BRD.md
sa
echo "== Kasus 3: RCA ROOT_CAUSE_CONFIRMED, hipotesis gugur 'status: INCONCLUSIVE'"
printf -- '---\nstatus: ROOT_CAUSE_CONFIRMED\ntaskdir: %s/\n---\n# RCA\n\n## Hipotesis\n- H1 (gugur) — status: INCONCLUSIVE\n' $TD > $TD/RCA.md
pl RCA -
echo "== Kasus 4: BRD status REVIEW, badan menyebut 'Refund status: APPROVED'"
printf -- '---\ntitle: Refund\nrequester: ops\nstatus: REVIEW\n---\n# BRD\n\n## Business rules\n- **BR-1**: Refund status: APPROVED hanya oleh supervisor.\n' > $TD/BRD.md
sa
echo "== Kasus 5: BRD tanpa field status di frontmatter, badan memuat 'status: APPROVED'"
printf -- '---\ntitle: Refund\nrequester: ops\n---\n# BRD\n\nRefund status: APPROVED\n' > $TD/BRD.md
sa
echo "== Kasus 6: BRD ber-BOM + CRLF, frontmatter APPROVED (kontrol)"
printf '\xef\xbb\xbf---\r\ntitle: R\r\nrequester: ops\r\nstatus: APPROVED\r\n---\r\n# BRD\r\n' > $TD/BRD.md
sa
rm -rf "$tmp"
```

Output aktual:

```
== Kasus 1: PRD APPROVED, badan menyebut 'status: DRAFT'
[3] Upstream Document Status         : FAIL (PRD.md masih berstatus DRAFT)
== Kasus 2: BRD APPROVED, badan menyebut 'status: DRAFT'
[1] BRD & Chain Alignment            : FAIL (BRD.md masih berstatus DRAFT)
== Kasus 3: RCA ROOT_CAUSE_CONFIRMED, hipotesis gugur 'status: INCONCLUSIVE'
[3] Upstream Document Status         : FAIL (RCA.md berstatus INCONCLUSIVE)
== Kasus 4: BRD status REVIEW, badan menyebut 'Refund status: APPROVED'
[1] BRD & Chain Alignment            : PASS (Chain BRD_PRD_BRIEF terikat BRD.md berstatus APPROVED)
== Kasus 5: BRD tanpa field status di frontmatter, badan memuat 'status: APPROVED'
[1] BRD & Chain Alignment            : PASS (Chain BRD_PRD_BRIEF terikat BRD.md berstatus APPROVED)
== Kasus 6: BRD ber-BOM + CRLF, frontmatter APPROVED (kontrol)
[1] BRD & Chain Alignment            : PASS (Chain BRD_PRD_BRIEF terikat BRD.md berstatus APPROVED)
```

Keempat bukti ISSUES terkonfirmasi. Kasus 5 adalah bukti tambahan.

### Dampak

- **Kasus 1–3, jalan buntu.** Dokumen sudah disetujui, tetapi gerbang menolak. Satu-satunya jalan keluar adalah mengubah kalimat aturan bisnis yang sah, padahal penulis dokumen dilarang menyentuh dokumen APPROVED.
- **Kasus 4–5, lolos palsu.** PRD disusun di atas BRD yang belum disetujui user. Ini melanggar "PEMILIK TUNGGAL APPROVAL" (`analyst/SKILL.md:147`) tanpa jejak.

### Rencana perbaikan

1. **`_common/precondition_lib.py`:** tambah `normalize_text`, `split_frontmatter`, `read_frontmatter`, dan `doc_status` (bagian A).
2. **`system-analysis/scripts/check_preconditions.py:159-180`:** baris `import re` tetap dibutuhkan skrip lain; di blok ini ganti menjadi:

   ```python
   status, why = doc_status(brd_file, ("DRAFT", "APPROVED"))
   if status is None:
       fail(f"Status BRD.md tidak terbaca dari frontmatter ({why})",
            "Frontmatter BRD.md wajib memuat `status: DRAFT` atau `status: APPROVED` di blok `---` "
            "pertama; kembalikan ke `backenddev:analyst` bila rusak.")
       return
   if status == "DRAFT":
       fail("BRD.md masih berstatus DRAFT",
            "Kembalikan ke `backenddev:analyst`: hanya skill itu yang menulis status APPROVED, "
            "di gerbang dokumen Fase 4-nya sesudah persetujuan user.")
       return
   ok("Chain BRD_PRD_BRIEF terikat BRD.md berstatus APPROVED")
   ```

   Blok `try: content = brd_file.read_text(...)` di 157–163 dihapus karena `doc_status` sudah menangani OSError.
3. **`plan/scripts/check_preconditions.py:288-313` (PRD):** pola yang sama dengan `("DRAFT", "APPROVED")`. Blok `try/except` luar tetap ada untuk galat tak terduga.
4. **`plan/scripts/check_preconditions.py:342-367` (RCA):** `doc_status(rca_file, ("ROOT_CAUSE_CONFIRMED", "INCONCLUSIVE"))`. `INCONCLUSIVE` memakai pesan lama; `None` memakai pesan "tidak terbaca" baru.
5. Pesan remediasi untuk status `None` selalu menyebut nilai aktual dan penyebabnya (dari `why`), bukan "tidak terdefinisi".

### Test yang ditambahkan

| Test | Input | Assert |
|---|---|---|
| `tests/backenddev/test_common_frontmatter.py::test_split_frontmatter_bom_crlf` | `b"\xef\xbb\xbf---\r\nstatus: APPROVED\r\n---\r\n# x"` | `fields == {"status": "APPROVED"}` |
| `…::test_only_first_block` | `---\nstatus: DRAFT\n---\n# x\n---\nstatus: APPROVED\n---` | `DRAFT` |
| `…::test_quoted_value_and_trailing_comment` | `status: "READY"  ` dan `chain: prd_brief # dari analyst` | `READY`, `prd_brief` |
| `…::test_duplicate_key_rejected` | dua baris `status:` | `FrontmatterError` memuat "lebih dari sekali" |
| `…::test_missing_open_or_close_fence` | tanpa `---` / tanpa penutup | `FrontmatterError`, pesan berbeda |
| `…::test_doc_status_body_sentence_ignored` | kasus 1–5 di atas | `("APPROVED", "")`, `(None, "…REVIEW…")`, `(None, "…tanpa kunci `status`")` |
| `tests/backenddev/test_system_analysis_preconditions.py::test_brd_approved_dengan_kalimat_status_draft_di_body` (sudah ada di 06, cabut `xfail`) | kasus 2 | check 1 PASS |
| `…::test_brd_review_dengan_kalimat_refund_status_approved` (sudah ada di 06, cabut `xfail`) | kasus 4 | check 1 FAIL, `summary` memuat `REVIEW` |
| `…::test_brd_tanpa_status_frontmatter` | kasus 5 | check 1 FAIL |
| `…::test_brd_bom_crlf_approved` | kasus 6 | check 1 PASS |
| `tests/backenddev/test_plan_preconditions.py::test_prd_approved_kalimat_status_draft` | kasus 1, `--entry-mode PRD` | check 3 PASS |
| `…::test_rca_confirmed_hipotesis_inconclusive` | kasus 3, `--entry-mode RCA --chain -` | check 3 PASS |
| `…::test_rca_inconclusive_frontmatter` | frontmatter `status: INCONCLUSIVE` | check 3 FAIL "berstatus INCONCLUSIVE" |

### Selesai bila

- Kasus 1, 2, 3, dan 6 → PASS.
- Kasus 4 dan 5 → FAIL dengan `summary` yang menyebut status aktual (`REVIEW`) atau ketiadaan kunci `status`.
- `grep -n 'in content.lower()' src/plugins/backenddev/skills/{system-analysis,plan}/scripts/check_preconditions.py` kosong.

### Risiko & catatan

- **Fail-closed disengaja.** Dokumen dengan `status: approved` (huruf kecil) atau frontmatter rusak kini FAIL dengan pesan jelas. Sebelumnya dokumen seperti itu lolos lewat substring. Lihat keputusan 2 (perbandingan persis vs tak peka huruf).
- **Kunci ganda** (`status: DRAFT` lalu `status: APPROVED`) kini FAIL (keputusan 3). YAML sendiri akan mengambil yang terakhir.
- `doc_status` tidak memvalidasi seluruh YAML. Nilai list/objek bertingkat diabaikan karena skrip hanya butuh skalar tingkat atas.

---

## L5.2 [Sedang] Cek taskdir terbalik (logika OR) dan pola taskdir tidak ditegakkan

- [ ] Selesai

**Plugin:** backenddev · **Estimasi:** 0,5 hari · **Bergantung pada:** C.2 (`check_taskdir`) · **Memblokir:** L5.5 (penghapusan `_resolve_taskdir`/`_get_rel_taskdir_str`)

### Konteks

Delapan skrip menerima `--taskdir` dengan tiga logika berbeda:

- **OR + `re.search`** (business-analysis, system-analysis, plan): FAIL hanya bila pola **tidak** cocok **dan** path **tidak** ada. Polanya tidak berjangkar, sehingga direktori apa pun yang sudah ada lolos.
- **AND + `re.match` + `exists()`** (analyst, architect, report, task): benar untuk teks, tetapi `exists()` menerima berkas, dan `relative_to` tanpa `resolve()` menolak path absolut lewat symlink.
- **Hanya `exists()`** (debug), padahal `debug/SKILL.md:26` menyatakan "Wajib cocok pola … pola lain ditolak tanpa negosiasi".

### Lokasi & kode saat ini

`src/plugins/backenddev/skills/business-analysis/scripts/check_preconditions.py:117-127` (identik di `system-analysis:257-272` dan `plan:140-155`)

```python
117:        taskdir_path = Path(self.taskdir_arg)
118:        if not taskdir_path.is_absolute():
119:            taskdir_path = self.root / taskdir_path
122:        rel_path = str(taskdir_path.relative_to(self.root) if taskdir_path.is_relative_to(self.root) else taskdir_path)
123:        pattern = r"backenddev/docs/\d{10}-[a-z0-9-]+/?"
125:        is_canonical = bool(re.search(pattern, rel_path))
126:        if not is_canonical and not taskdir_path.exists():
```

`src/plugins/backenddev/skills/analyst/scripts/check_preconditions.py:123-136` (identik di architect, report, task)

```python
123:        taskdir_path = self._resolve_taskdir()
124:        if not taskdir_path or not taskdir_path.exists():
134:        rel_str = self._get_rel_taskdir_str()
135:        pattern = r"^backenddev/docs/\d{10}-[a-z0-9-]+$"
136:        if not re.match(pattern, rel_str):
```

`src/plugins/backenddev/skills/debug/scripts/check_preconditions.py:283-287`

```python
283:        td = Path(self.taskdir_arg)
284:        if not td.is_absolute():
285:            td = self.root / td
287:        if not td.exists():
```

### Reproduksi

```bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
S=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); cd "$tmp" && git init -q && git config user.email t@t && git config user.name t
mkdir -p .claude/profile backenddev/docs/2601011200-ok src
echo '{"stack":"go","architecture":"layered","root_namespace":"x","source_root":"src","commit_convention":"c","base_branch":"main","branch_convention":"feat/<slug>"}' > .claude/profile/index.json
touch backenddev/docs/2601011200-berkas
ln -s "$tmp" "$tmp.link"
git add -A && git commit -qm init
v() { # $1=skill $2=check-id $3=taskdir ; sisanya argumen tambahan → PASS/FAIL
  local sk=$1 id=$2 td=$3; shift 3
  python3 $S/$sk/scripts/check_preconditions.py --root "$tmp" --taskdir "$td" "$@" 2>&1 \
    | grep "^\[$id\]" | grep -oE ': (PASS|FAIL)' | tr -d ': '
}
printf '%-44s %-4s %-4s %-4s %-5s %-4s %-4s %-4s %-4s\n' "--taskdir" BA SA plan debug anl arch rep task
for td in src /tmp . backenddev/docs/2601011200-belum-ada backenddev/docs/2601011200-berkas \
          "$tmp.link/backenddev/docs/2601011200-ok" backenddev/docs/2601011200-ok; do
  printf '%-44s %-4s %-4s %-4s %-5s %-4s %-4s %-4s %-4s\n' "${td/$tmp/\$tmp}" \
    "$(v business-analysis 1 "$td" --chain BRD_PRD_BRIEF)" \
    "$(v system-analysis 3 "$td" --risk-level MAJOR --chain BRD_PRD_BRIEF)" \
    "$(v plan 1 "$td" --entry-mode LANGSUNG --chain BRIEF --risk MINOR)" \
    "$(v debug 5 "$td" --symptom x)" \
    "$(v analyst 1 "$td" --risk MAJOR)" "$(v architect 1 "$td")" "$(v report 1 "$td")" \
    "$(v task 1 "$td" --lane DIRECT_BRIEF --chain BRIEF)"
done
rm -rf "$tmp" "$tmp.link"
```

Output aktual (BA = business-analysis check 1, SA = system-analysis check 3, plan check 1, debug check 5, lainnya check 1):

```
--taskdir                                    BA   SA   plan debug anl  arch rep  task
src                                          PASS PASS PASS PASS  FAIL FAIL FAIL FAIL
/tmp                                         PASS PASS PASS PASS  FAIL FAIL FAIL FAIL
.                                            PASS PASS PASS PASS  FAIL FAIL FAIL FAIL
backenddev/docs/2601011200-belum-ada         PASS PASS PASS FAIL  FAIL FAIL FAIL FAIL
backenddev/docs/2601011200-berkas            PASS PASS PASS FAIL  PASS PASS PASS PASS
$tmp.link/backenddev/docs/2601011200-ok      PASS PASS PASS PASS  FAIL FAIL FAIL FAIL
backenddev/docs/2601011200-ok                PASS PASS PASS PASS  PASS PASS PASS PASS
```

Semua bukti ISSUES terkonfirmasi. Rinciannya: taskdir berupa berkas lolos di **7 dari 8** skrip (hanya debug yang menolak, dan itu pun lewat `probe_writable`), dan symlink gagal di 4 skrip AND.

### Dampak

- business-analysis/system-analysis/plan bisa menulis `BRD.md`/`PRD.md`/brief ke `src/`, `.`, atau `/tmp`. Commit draft kemudian menyentuh berkas di luar zona artefak.
- Taskdir kanonik yang belum diprovisi lolos, padahal taskdir wajib diprovisi tech-lead.
- Taskdir berupa berkas lolos check 1, lalu check berikutnya gagal dengan pesan yang tidak menunjuk akar masalah.
- Path absolut lewat symlink (umum di macOS: `/var` → `/private/var`, dan di home ter-symlink) ditolak oleh 4 skrip dengan pesan "Format taskdir tidak sesuai".

### Rencana perbaikan

1. **`_common`:** `TASKDIR_RE`, `resolve_taskdir`, `check_taskdir`, `TaskdirVerdict` (bagian A). Karena `resolve()` dilakukan sebelum `relative_to`, symlink dan `./…/` ternormalisasi.
2. **Pola pemakaian di tiap skrip** (business-analysis 103–142, system-analysis 243–288, plan 126–171, analyst 109–152, architect 94–137, report 95–138, task 164–207):

   ```python
   def _check_1_taskdir(self):
       v = self.td = check_taskdir(self.root, self.taskdir_arg)
       self.results.append({
           "id": 1, "name": "Taskdir Format & Existence",
           "status": "PASS" if v.ok else "FAIL", "summary": v.summary,
           "action": "" if v.ok else "Minta direktori kerja sah dari gerbang `backenddev:tech-lead` "
                                     "(format: backenddev/docs/<YYMMDDhhmm>-<slug>/).",
       })
   ```

   Check lain memakai `self.td.path if self.td.ok else None` sebagai pengganti `_resolve_taskdir()`. Di `__init__`, isi `self.td = check_taskdir(...)` sekali supaya check yang jalan lebih dulu (system-analysis check 1) juga bisa memakainya.
3. **debug check 5 (283–314):** panggil `check_taskdir` lebih dulu; bila lolos, jalankan `_probe_writable(v.path)`. Pesan FAIL untuk pola mengutip `debug/SKILL.md:26`.
4. `must_exist=True` di kedelapan skrip. Tidak satu pun dari mereka pembuat taskdir; taskdir diprovisi tech-lead di Fase 3.
5. Hapus `_resolve_taskdir` (8 salinan) dan `_get_rel_taskdir_str` (4 salinan). `validate_briefs.py:244` memakai `resolve_taskdir`.

### Test yang ditambahkan

| Test | Input | Assert |
|---|---|---|
| `tests/backenddev/test_common_taskdir.py::test_check_taskdir_matrix` (parametrik) | `src`, `/tmp`, `.`, `…-belum-ada`, `…-berkas`, `x/backenddev/docs/2601011200-ok`, symlink absolut, `./backenddev/docs/2601011200-ok/` | `ok` = F,F,F,F,F,F,T,T; `rel` symlink = `backenddev/docs/2601011200-ok` |
| `…::test_must_exist_false` | `…-belum-ada`, `must_exist=False` | `ok is True` |
| `…::test_outside_root` | `/tmp` | `summary` memuat "di luar root repo" |
| `tests/backenddev/test_business_analysis_preconditions.py::test_taskdir_non_kanonik_ditolak` (parametrik `src`, `.`) | | check 1 FAIL |
| `tests/backenddev/test_system_analysis_preconditions.py::test_taskdir_bukan_kanonik_ditolak` (sudah ada di 06, cabut `xfail`) | `src` | check 3 FAIL |
| `tests/backenddev/test_plan_preconditions.py::test_taskdir_belum_diprovisi` | `…-belum-ada` | check 1 FAIL "tidak ditemukan" |
| `tests/backenddev/test_debug_preconditions.py::test_taskdir_pola_ditegakkan` | `src` (ada, bisa ditulis) | check 5 FAIL "pola kanonik" |
| `tests/backenddev/test_analyst_preconditions.py::test_taskdir_berupa_berkas` | `…-berkas` | check 1 FAIL "bukan direktori" |
| `…::test_taskdir_absolut_lewat_symlink` | `$tmp.link/…-ok` | check 1 PASS |

### Selesai bila

Matriks reproduksi dijalankan ulang menghasilkan: lima baris pertama FAIL di kedelapan kolom, dan dua baris terakhir PASS di kedelapan kolom.

### Risiko & catatan

- `resolve()` mengikuti symlink. Repo yang `backenddev/docs` di dalamnya berupa symlink ke luar repo akan ditolak ("di luar root repo"). Perilaku ini dapat diterima karena artefak rantai harus ter-commit di repo.
- `TASKDIR_RE` mempertahankan kelas `[a-z0-9-]+` apa adanya (termasuk slug berawalan atau berakhiran `-`) supaya taskdir lama tidak tiba-tiba ditolak.

---

## L5.3 [Sedang] Pencocokan substring di `validate_briefs.py`

- [ ] Selesai

**Plugin:** backenddev · **Estimasi:** 1 hari · **Bergantung pada:** C.0 (fixture brief di `tests/builders.py`) · **Memblokir:** —

### Konteks

Validator batch brief memakai operator `in` pada string di empat predikat: cakupan AC, batas path, perintah build/test, dan pemilik migrasi. Brief yang sah jadi gagal, dan brief yang melanggar batas jadi lolos.

### Lokasi & kode saat ini

`src/plugins/backenddev/skills/plan/scripts/validate_briefs.py`

```python
1431:            claimers = [b for b in self.briefs
1432:                        if b["covers"] and f"AC-{num}" in b["covers"]]      # string: "AC-1" ⊂ "AC-10"
1469:                    rr = self._section_text(b, "Risk & rollback")
1470:                    if f"AC-{num}" not in rr:                             # "AC-10" meloloskan AC-1
```

```python
1241:    def _path_matches(path: str, pattern: str) -> bool:
1242:        pattern = pattern.rstrip("/")
1243:        if not pattern:
1244:            return False
1245:        if pattern in path:
1246:            return True
1247:        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern + "/*")
```

```python
886:                low = line.lower()
887:                for cmd in BUILD_TEST_COMMANDS:
888:                    if cmd in low:                                        # "mongo testcontainer" ⊃ "go test"
```

```python
1499:        prd_trigger = bool(prd_req.strip()) and "tidak perlu" not in prd_req.lower()
1506:        owners = [b for b in self.briefs
1507:                  if self._section_text(b, "Migration").strip()
1508:                  and "tidak perlu" not in self._section_text(b, "Migration").lower()]
```

### Reproduksi

```bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
V=$REPO/src/plugins/backenddev/skills/plan/scripts/validate_briefs.py
tmp=$(mktemp -d); cd "$tmp" && git init -q
TD=backenddev/docs/2601011200-refund; mkdir -p $TD .claude/profile
cat > $TD/TASK.md <<'T'
---
status: ACTIVE
chain: PRD_BRIEF
risk: MAJOR
---
# Refund
## Success Criteria
- [ ] **SC-1**: refund tercatat
## Out of Scope
- `src/payment/` — modul pembayaran tidak disentuh
T
cat > $TD/PRD.md <<'P'
---
status: APPROVED
---
# PRD
## Acceptance criteria
| ID | Kriteria | Verifikasi |
|---|---|---|
| AC-1 | tombol refund tampil | QA manual |
| AC-10 | refund tersimpan | test otomatis |
## Migration requirements
tidak perlu
P
brief() { # $1=NN $2=covers $3=file-rows $4=migration $5=risk&rollback $6=steps-extra
cat > $TD/brief-$1-x.md <<B
---
title: brief $1
source: PRD.md
risk: MAJOR
status: READY
commit_message: "feat(refund): brief $1"
---
# Brief: brief $1 — 2026-01-01
## Objective
Kerjakan refund.

Covers: $2
## Interfaces
- Produces: \`Refund$1\`
## File scope
**File**

| Aksi | Path | Anchor | Apa yang berubah |
|---|---|---|---|
$3
## Out of scope
lain
## Steps
1. Ubah \`Refund$1\`. $6
## Migration
$4
## Mirrored paths
tidak ada
## Risk & rollback
$5
## Work status
| Item | Status | Catatan |
|---|---|---|
| P1-1 | PLANNED | — |
## Analysis trace
Tidak ada.
B
}
brief 01 "AC-1" "| create | \`src/refund/ui.go\` | — | tombol |" "tidak perlu" "AC-1: klik tombol refund, pastikan tampil. Rollback: revert." ""
brief 02 "AC-10" "| create | \`src/refund/store_test.go\` | — | AC-10: assert tersimpan |" "tidak perlu" "Rollback: revert commit." ""
show() { python3 $V --root "$tmp" --taskdir $TD "$@" | awk -v id="$ID" '$0 ~ "^\\["id"\\]" {p=1; print; next} /^\[/ {p=0} p && /^    - /'; }
echo "== (a) AC-1 vs AC-10 — Check I"; ID=I show
echo "== (b1) --file-scope src/refund meloloskan src/refundhistory — Check E"
brief 02 "AC-10" "| create | \`src/refundhistory/store_test.go\` | — | AC-10: assert tersimpan |" "tidak perlu" "Rollback: revert commit." ""
ID=E show --file-scope src/refund
echo "== (b2) Out of Scope src/payment/ menolak src/payments_report.go — Check E"
brief 02 "AC-10" "| create | \`src/payments_report.go\` | — | AC-10: assert tersimpan |" "tidak perlu" "Rollback: revert commit." ""
ID=E show
echo "== (c) 'Mongo TestContainer' dibaca sebagai 'go test' — Check F"
brief 02 "AC-10" "| create | \`src/refund/store_test.go\` | — | AC-10: assert tersimpan |" "tidak perlu" "Rollback: revert commit." "Pakai Mongo TestContainer yang sudah ada."
ID=F show
echo "== (d) '## Migration' berbunyi 'Tidak diperlukan' — Check J"
brief 02 "AC-10" "| create | \`src/refund/store_test.go\` | — | AC-10: assert tersimpan |" "Tidak diperlukan — tidak ada perubahan skema." "Rollback: revert commit." ""
ID=J show
echo "== (e) PRD 'Migration requirements' menyebut 'tidak perlu' di tengah kalimat — Check J"
brief 02 "AC-10" "| create | \`src/refund/store_test.go\` | — | AC-10: assert tersimpan |" "tidak perlu" "Rollback: revert commit." ""
sed -i 's/^tidak perlu$/Kolom lama tidak perlu dihapus; tambah kolom `refund_reason` (ALTER TABLE)./' $TD/PRD.md
ID=J show
rm -rf "$tmp"
```

Output aktual:

```
== (a) AC-1 vs AC-10 — Check I
[I] AC Test Landing                : FAIL (1 pelanggaran)
    - brief-02-x.md: langkah manual `AC-1` tidak mendarat di `## Risk & rollback` — `## Analysis trace` bukan tempatnya
== (b1) --file-scope src/refund meloloskan src/refundhistory — Check E
[E] Scope Containment              : PASS (seluruh path di dalam batas)
== (b2) Out of Scope src/payment/ menolak src/payments_report.go — Check E
[E] Scope Containment              : FAIL (1 pelanggaran)
    - brief-02-x.md:20: `src/payments_report.go` menyentuh butir `## Out of Scope` akar (`src/payment/`)
    - TERDEGRADASI: file_scope kosong — batas diturunkan dari `## Out of Scope` TASK.md. Pembandingnya menyebut yang dilarang, bukan yang diizinkan — berkas di luar batas yang tidak tersebut di sana lolos tanpa terdeteksi.
== (c) 'Mongo TestContainer' dibaca sebagai 'go test' — Check F
[F] Verification Sweep             : FAIL (1 pelanggaran)
    - brief-02-x.md:24: perintah build/test `go test`
== (d) '## Migration' berbunyi 'Tidak diperlukan' — Check J
[J] Migration Landing              : FAIL (3 pelanggaran)
    - brief-02-x.md: `## Migration` memuat DDL tetapi tidak satu pun berkas migrasi terdaftar di `## File scope`
    - brief-02-x.md: `## Migration` tidak memuat urutan deploy sebagai langkah bernomor
    - brief-02-x.md: `## Migration` tidak memuat DDL konkret
== (e) PRD 'Migration requirements' menyebut 'tidak perlu' di tengah kalimat — Check J
[J] Migration Landing              : SKIP (nol berkas migrasi dan `## Migration requirements` tidak menuntut apa pun)
```

Keempat bukti ISSUES (a–d) terkonfirmasi. Kasus (e) adalah temuan tambahan: arah kebalikannya, yaitu lolos palsu.

### Dampak

- **(a)** FAIL palsu di setiap batch yang memiliki ≥10 AC. Arah sebaliknya di baris 1470: brief yang `Risk & rollback`-nya hanya menyebut `AC-10` dianggap sudah mendaratkan `AC-1`.
- **(b1)** Brief menyentuh modul tetangga (`src/orderhistory` saat batasnya `src/order`) tanpa terdeteksi, sehingga batas `file_scope` gerbang jebol. **(b2)** FAIL palsu yang memaksa model memelintir path.
- **(c)** Kata biasa ("Mongo TestContainer", "cargo builder", "gotest") memicu FAIL. Model akan mengganti istilah teknis yang benar.
- **(d)** Pola template ("tulis \"tidak perlu\" beserta alasan") gagal bila penulis memilih kata lain yang sama artinya. Hasilnya tiga pelanggaran palsu.
- **(e)** Kebutuhan migrasi PRD hilang tanpa jejak bila kalimatnya kebetulan memuat "tidak perlu".

### Rencana perbaikan

Semua di `plan/scripts/validate_briefs.py`. Kode di bawah sudah diuji di scratchpad (`be_brief_fix.py`) pada kasus a–e.

1. **Cakupan AC (1432, 1470):**

   ```python
   def _covers_ac(covers: Optional[str], num: str) -> bool:
       return bool(covers) and re.search(rf"\bAC-{re.escape(num)}\b", covers) is not None
   # 1432: if _covers_ac(b["covers"], num)
   # 1470: if not re.search(rf"\bAC-{re.escape(num)}\b", rr):
   ```

2. **`_path_matches` (1241–1247):** glob → `fnmatchcase`; nama lepas tanpa `/` → cocok per segmen; selain itu → prefix per segmen (`is_under` dari `_common`).

   ```python
   @staticmethod
   def _path_matches(path: str, pattern: str) -> bool:
       pattern = pattern.strip().strip("`").rstrip("/")
       if not pattern:
           return False
       if any(ch in pattern for ch in "*?["):
           return fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(path, pattern + "/*")
       if "/" not in pattern:
           return pattern in path.strip("/").split("/")
       return is_under(path, pattern)
   ```

3. **Perintah build/test (886–892):** satu regex dengan batas kata. Di kiri tidak boleh ada `[\w./-]`, di kanan tidak boleh ada `[\w-]`.

   ```python
   BUILD_TEST_RE = re.compile(
       r"(?<![\w./-])(" + "|".join(re.escape(c) for c in BUILD_TEST_COMMANDS) + r")(?![\w-])",
       re.IGNORECASE)
   # di loop: m = BUILD_TEST_RE.search(line); if m: problems.append(... m.group(1).lower() ...)
   ```

4. **Penolakan migrasi (1499, 1508):** hanya **baris isi pertama** seksi yang dinilai.

   ```python
   NO_MIGRATION_RE = re.compile(
       r"^(?:tidak\s+(?:perlu|diperlukan|dibutuhkan|ada)|nihil|n/?a|none)\b|^[—-]$", re.IGNORECASE)

   def _migration_declined(body: str) -> bool:
       for line in body.splitlines():
           s = line.strip()
           if not s or s.startswith("<!--"):
               continue
           return bool(NO_MIGRATION_RE.match(s.lstrip("-* ").strip()))
       return True
   # 1499: prd_trigger = bool(prd_req.strip()) and not _migration_declined(prd_req)
   # 1508: owners = [b for b in self.briefs if not _migration_declined(self._section_text(b, "Migration"))]
   ```

   `ORM_SCHEMA_TOKEN` ("Berkas migrasi: tidak ada — skema dibentuk ORM") tidak cocok dengan `NO_MIGRATION_RE` karena diawali "Berkas migrasi:". Pemilik ORM tetap diperlakukan seperti sebelumnya.

Hasil helper usulan pada input yang sama (keluaran aktual scratchpad):

```
covers_ac('AC-10', 1)                                    -> False
path_matches('src/orderhistory/x.go','src/order')        -> False
path_matches('src/payments_report.go','src/payment/')    -> False
path_matches('deploy/config.yaml','config.yaml')         -> True
path_matches('internal/order/handler.go','internal/*/handler.go') -> True
build_command('Pakai Mongo TestContainer')               -> None
build_command('jalankan `go test ./...`')                -> go test
migration_declined('Tidak diperlukan — ...')             -> True
migration_declined('Kolom lama tidak perlu dihapus; tambah kolom x') -> False
migration_declined('Berkas migrasi: tidak ada — skema dibentuk ORM') -> False
```

### Test yang ditambahkan

`tests/backenddev/test_validate_briefs.py`, dengan fixture batch dari `be_briefs` atau builder setara isi skrip di atas:

| Test | Input | Assert |
|---|---|---|
| `test_ac1_tidak_diklaim_brief_ac10` | kasus (a) | Check I PASS |
| `test_manual_ac_butuh_id_persis` | brief-01 `Covers: AC-1`, `Risk & rollback` hanya "AC-10: …" | Check I FAIL untuk `AC-1` |
| `test_file_scope_per_segmen` | kasus (b1) | Check E FAIL memuat `src/refundhistory` |
| `test_out_of_scope_per_segmen` | kasus (b2) | Check E tanpa pelanggaran path (status WARN/TERDEGRADASI tetap boleh) |
| `test_scope_nama_lepas_cocok_segmen` | Out of Scope `` `config.yaml` ``, path `deploy/config.yaml` | Check E FAIL |
| `test_anti_pattern_glob_tetap_berlaku` | `anti-patterns.md` dengan `deteksi \`panic\( @ internal/*/service.go\`` | Check P tetap FAIL pada brief yang menyentuh `internal/order/service.go` |
| `test_mongo_testcontainer_bukan_perintah` | kasus (c) | Check F PASS |
| `test_go_test_berbacktick_tetap_ditolak` | langkah "jalankan `go test ./...`" | Check F FAIL `go test` |
| `test_migration_tidak_diperlukan_bukan_pemilik` | kasus (d) | Check J SKIP |
| `test_prd_migration_tidak_perlu_di_tengah_kalimat` | kasus (e) | Check J FAIL "aktif tetapi tidak satu pun brief" |

### Selesai bila

Skrip reproduksi menghasilkan: (a) Check I PASS; (b1) Check E FAIL; (b2) Check E tanpa pelanggaran path; (c) Check F PASS; (d) Check J SKIP; (e) Check J FAIL.

### Risiko & catatan

- `_path_matches` juga dipakai Check P (baris 1102, cakupan anti-pattern). Cakupan di profil berbentuk glob berjangkar root (`internal/*/handler.go`, contoh di `profile/templates/profile-template.md:234-236`), jadi tidak terpengaruh. Cakupan berbentuk direktori tanpa root (`handler/`) yang sebelumnya cocok lewat substring kini hanya cocok sebagai segmen utuh.
- `fnmatch` → `fnmatchcase` membuat pencocokan peka huruf di semua OS (sebelumnya tidak peka huruf di Windows).
- `--brief 1` yang memilih brief-10 (baris 431) sudah tercatat sebagai **B16**, dan tidak dikerjakan di sini.

---

## L5.4 [Sedang] Crash dan regex chain yang divergen di skrip analyst backenddev

- [ ] Selesai

**Plugin:** backenddev · **Estimasi:** 0,5 hari · **Bergantung pada:** C.2 (`parse_chain`, `declared_chain`), L5.1 (`read_frontmatter`) · **Memblokir:** —

### Konteks

Nilai `chain:` TASK.md dibaca di empat tempat dengan dua regex. Keduanya memindai seluruh isi, bukan hanya frontmatter. analyst lalu memakai hasil regex tanpa validasi sebagai kunci dict `CHAIN_ARTIFACTS`. Nilai asing yang lolos `[A-Z_]+` (misalnya nilai lane `PRD_CONVERSION`) langsung memicu `KeyError`.

### Lokasi & kode saat ini

`src/plugins/backenddev/skills/analyst/scripts/check_preconditions.py`

```python
 50:        self.chain_arg = (chain or "auto").strip().upper()
106:        match = re.search(r"^chain:\s*([A-Z_]+)\s*$", content, re.MULTILINE)
302:        effective_chain = self.chain_arg if self.chain_arg in VALID_CHAINS else self._declared_chain()
315:        stray = sorted(present - CHAIN_ARTIFACTS[effective_chain])
```

Regex lain: `business-analysis:68` dan `system-analysis:64` memakai `r"^chain:\s*([A-Z_]+)\s*$"`, sedangkan `plan:111` memakai `rf"^{field}:\s*([A-Za-z_-]+)\s*$"` + `.upper()`.

### Reproduksi

```bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
S=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); cd "$tmp" && git init -q && git config user.email t@t && git config user.name t
TD=backenddev/docs/2601011200-refund; mkdir -p $TD .claude/profile src
echo '{"stack":"go","architecture":"layered","root_namespace":"x","source_root":"src","commit_convention":"c","base_branch":"main","branch_convention":"feat/<slug>"}' > .claude/profile/index.json
for f in commands code-conventions anti-patterns invariants; do echo "# $f" > .claude/profile/$f.md; done
git add -A && git commit -qm init
task() { printf -- '---\nstatus: ACTIVE\nchain: %s\nlane: PRD_CONVERSION\nrisk: MAJOR\n---\n# T\n' "$1" > $TD/TASK.md; }

echo "== (1) TASK.md chain: PRD_CONVERSION, analyst tanpa --chain (auto)"
task PRD_CONVERSION
python3 $S/analyst/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --risk MAJOR 2>&1 | tail -3
echo "-- mode --json: stdout =" ; python3 $S/analyst/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --risk MAJOR --json 2>/dev/null | wc -c; echo "exit=${PIPESTATUS[0]}"

echo "== (2) TASK.md chain: prd_brief + BRD.md nyasar, analyst auto"
task prd_brief; echo "# BRD" > $TD/BRD.md
python3 $S/analyst/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --risk MAJOR | grep '^\[5\]'
rm $TD/BRD.md

echo "== (3) Nilai chain yang sama dibaca berbeda oleh tiga skrip (tanpa --chain)"
for v in PRD_BRIEF prd_brief '"PRD_BRIEF"' 'PRD_BRIEF  # dari analyst' PRD-BRIEF; do
  task "$v"
  ba=$(python3 $S/business-analysis/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --json | python3 -c 'import json,sys;print(json.load(sys.stdin)["chain"])')
  sa=$(python3 $S/system-analysis/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --risk-level MAJOR --json | python3 -c 'import json,sys;print(json.load(sys.stdin)["chain"] or "")')
  pl=$(python3 $S/plan/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --entry-mode PRD --json | python3 -c 'import json,sys;print(json.load(sys.stdin)["chain"])')
  printf '%-28s BA=%-10s SA=%-10s plan=%s\n' "chain: $v" "$ba" "${sa:-''}" "$pl"
done
rm -rf "$tmp"
```

Output aktual:

```
== (1) TASK.md chain: PRD_CONVERSION, analyst tanpa --chain (auto)
    stray = sorted(present - CHAIN_ARTIFACTS[effective_chain])
                             ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
KeyError: 'PRD_CONVERSION'
-- mode --json: stdout =
0
exit=1
== (2) TASK.md chain: prd_brief + BRD.md nyasar, analyst auto
[5] Artifact vs Chain Consistency       : PASS (Chain belum ditetapkan; artefak rancangan terbaca: BRD.md)
== (3) Nilai chain yang sama dibaca berbeda oleh tiga skrip (tanpa --chain)
chain: PRD_BRIEF             BA=PRD_BRIEF  SA=PRD_BRIEF  plan=PRD_BRIEF
chain: prd_brief             BA=None       SA=''         plan=PRD_BRIEF
chain: "PRD_BRIEF"           BA=None       SA=''         plan=None
chain: PRD_BRIEF  # dari analyst BA=None       SA=''         plan=None
chain: PRD-BRIEF             BA=None       SA=''         plan=PRD-BRIEF
```

### Dampak

- **(1)** Mode `--json`, yang dipakai model untuk membaca vonis, tidak mengeluarkan apa pun di stdout. Model hanya melihat traceback di stderr dan tidak mendapat check mana pun.
- **(2)** Artefak di luar chain (BRD.md pada chain PRD_BRIEF) lolos sebagai "Chain belum ditetapkan". Pengaman salah rute di check 5 mati.
- **(3)** Hop yang berurutan membaca TASK.md yang sama dengan hasil berbeda. business-analysis/system-analysis gagal "chain tidak terbaca" sementara plan lolos, sehingga rantai macet di tengah dengan pesan yang tidak menunjuk penyebabnya.

### Rencana perbaikan

1. **`_common`:** `parse_enum`, `parse_chain`, `declared_chain`, `frontmatter_field`, `VALID_CHAINS`, `VALID_RISKS` (bagian A). Normalisasinya: trim, buka kutip, buang komentar ` # …`, huruf besar. `-`/`—`/kosong → `None` tanpa galat. Nilai lain di luar enum → `(None, galat)`. Tanda hubung **tidak** dilipat: `PRD-BRIEF` tetap galat.
2. **analyst:**

   ```python
   raw = (chain or "").strip()
   if raw.lower() in ("", "auto"):
       self.chain_arg, self.chain_err = "AUTO", ""
   else:
       self.chain_arg, self.chain_err = parse_chain(raw)
   ```

   - Check 4: bila `self.chain_err` → FAIL (`summary` = `chain_err`). `declared, derr = declared_chain(self.td.path)`; bila `derr` → FAIL "TASK.md memuat chain asing: …".
   - Check 5 baris 302–315: `effective = self.chain_arg if self.chain_arg in VALID_CHAINS else declared`. Bila `derr` → FAIL dengan tindakan "laporkan salah rute ke `backenddev:tech-lead`". `CHAIN_ARTIFACTS[...]` hanya diakses sesudah nilainya tervalidasi.
3. **business-analysis / system-analysis:** `self.chain_arg, self.chain_err = parse_chain(chain)`. `_effective_chain()` → `self.chain_arg or declared_chain(td)[0]`. Galat dari parameter atau dari TASK.md dilaporkan di check chain (BA check 7, SA check 1).
4. **plan:** `_frontmatter("chain")` → `parse_chain(frontmatter_field(task, "chain"))`; `_frontmatter("risk")` → `parse_enum(frontmatter_field(task, "risk"), VALID_RISKS, "risk")`. Galat masuk check 8.
5. **task:** `self.chain_arg, self.chain_err = parse_chain(chain)`. Check 6 memakai `chain_err` untuk nilai asing. Kosong tetap berarti "tanpa chain" (lane non-planning).
6. **`scaffold_brief.py:229`, `validate_briefs.py:664-676`:** baca `risk` lewat `frontmatter_field`. Nilai `-`/`—` tetap berarti plafon MINOR, sesuai komentar di `validate_briefs.py:674`.

### Test yang ditambahkan

| Test | Input | Assert |
|---|---|---|
| `tests/backenddev/test_common_chain.py::test_parse_chain_normalisasi` (parametrik) | `PRD_BRIEF`, `prd_brief`, `"PRD_BRIEF"`, `PRD_BRIEF # x` (lewat `split_frontmatter`), `—` | `PRD_BRIEF` ×4, `None` tanpa galat |
| `…::test_parse_chain_menolak_nilai_lane` | `PRD_CONVERSION`, `PRD-BRIEF` | `(None, "chain '…' tidak sah …")` |
| `…::test_declared_chain_frontmatter_rusak` | TASK.md dengan dua `chain:` | galat memuat "lebih dari sekali" |
| `tests/backenddev/test_analyst_preconditions.py::test_chain_asing_di_task_json_tetap_valid` | kasus (1), `--json` | `r.traceback is False`, `r.json()` valid, check 5 FAIL memuat `PRD_CONVERSION`, exit 1 |
| `…::test_chain_huruf_kecil_mendeteksi_brd_nyasar` | kasus (2) | check 5 FAIL memuat `BRD.md` |
| `…::test_parameter_chain_asing` | `--chain PRD_CONVERSION` | check 4 FAIL, tanpa traceback |
| `tests/backenddev/test_chain_consistency.py::test_tiga_skrip_membaca_chain_sama` (parametrik 5 nilai) | kasus (3) | kolom BA = SA = plan; `PRD-BRIEF` → ketiganya melaporkan galat |

### Selesai bila

- Kasus (1): tanpa traceback; `--json` mengeluarkan JSON valid; check 5 FAIL dengan pesan chain tidak sah.
- Kasus (2): check 5 FAIL karena `BRD.md` berada di luar chain PRD_BRIEF.
- Kasus (3): empat baris pertama bernilai `PRD_BRIEF` di ketiga kolom. Baris `PRD-BRIEF` melaporkan galat yang sama di ketiga skrip.

### Risiko & catatan

- TASK.md lama yang memakai huruf kecil atau kutip kini terbaca, padahal sebelumnya dianggap "tidak terbaca" oleh business-analysis/system-analysis. Perubahan ini melonggarkan. Tidak ada kasus di mana TASK.md yang tadinya lolos kini gagal, kecuali TASK.md dengan kunci `chain` ganda.
- Nilai `AUTO` hanya sah sebagai parameter analyst, tidak pernah sebagai isi TASK.md. `declared_chain` tidak mengenalnya.

---

## L5.5 [Sedang] Duplikasi kode yang sudah divergen dan path mati

- [ ] Selesai

**Plugin:** backenddev · **Estimasi:** 2 hari (bagian A + call site bagian B) · **Bergantung pada:** C.0, C.1 · **Memblokir:** L6.3 (aturan lint path), L1.1 (`PROFILE_DIR`)

### Konteks

Statistik lengkap ada di tabel B.1, dan call site per skrip di tabel B.2. Ringkasnya, ada empat masalah:

1. **Salinan yang divergen.** 14 × `_find_repo_root`, 13 × `format_text`, 13 × `to_json` (11 varian AST), 8 × `_resolve_taskdir`. `_common` hanya diimpor 8 dari 12 skrip prasyarat.
2. **Path fallback di luar plugin.** 21 path `~/.gemini/config/plugins/backenddev/…`, 22 path `self.root/src/plugins/backenddev/…`, dan 21 path `~/.claude/plugins/backenddev/…`. Di audit/debug/document-api, kandidat relatif `__file__` (satu-satunya yang benar) ada di urutan **terakhir**.
3. **Tiga parser `git status --porcelain`.** analyst/task tidak membuang kutip. Filter `.explore` berlaku di segmen mana pun (B6).
4. **Kunci wajib `index.json` berbeda di tiap skrip:** 8 himpunan di 11 skrip.

**Koreksi terhadap ISSUES.md:**

- (a) `_find_repo_root` punya 4 varian teks tetapi 1 perilaku.
- (b) Kunci index bukan "7, 4, atau 1" melainkan 8 himpunan (B.1).
- (c) Path `.gemini` tidak mati di mesin pengguna: `~/.gemini/config/plugins/backenddev/agents/` berisi 6 agent. Fallback ini **menutupi** berkas yang hilang (reproduksi 2). Yang benar-benar tidak pernah ada adalah `~/.claude/plugins/backenddev/…`; tata letak nyata `~/.claude/plugins/cache/fakhrulnugroho/backenddev/<versi>/`.
- (d) Nama berspasi juga dikutip git, jadi `café.md` bukan satu-satunya pemicu.

### Lokasi & kode saat ini

`_find_repo_root`, contoh `analyst/scripts/check_preconditions.py:53-65`. 13 salinan lain berbeda hanya di docstring, koma, atau bentuk method vs fungsi:

```python
53:    def _find_repo_root(self) -> Path:
54:        """Find the git repository root or fallback to cwd."""
55:        try:
56:            out = subprocess.check_output(
57:                ["git", "rev-parse", "--show-toplevel"],
58:                stderr=subprocess.DEVNULL,
59:                universal_newlines=True,
60:            ).strip()
61:            if out and os.path.isdir(out):
62:                return Path(out)
63:        except Exception:
64:            pass
65:        return Path.cwd()
```

Porcelain tanpa buang kutip, `analyst/scripts/check_preconditions.py:374-382` (task `:372-384` identik):

```python
374:            for line in status_output:
375:                if not line.strip():
376:                    continue
377:                file_part = line[3:].strip().rstrip("/")
378:                if " -> " in file_part:
379:                    file_part = file_part.split(" -> ")[-1].strip().rstrip("/")
381:                if rel_taskdir and (file_part == rel_taskdir or file_part.startswith(rel_taskdir + "/")):
382:                    continue
```

Porcelain dengan buang kutip tetapi escape oktal dibiarkan, `tech-lead/scripts/check_preconditions.py:213-221`:

```python
213:        for line in status_out.splitlines():
216:            path = line[3:] if len(line) > 3 else line.strip()
217:            if " -> " in path:
218:                path = path.split(" -> ")[-1]
219:            path = path.strip()
220:            if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
221:                path = path[1:-1]
```

Daftar kandidat, `audit/scripts/check_preconditions.py:186-191`:

```python
186:        candidate_paths = [
187:            self.root / "src" / "plugins" / "backenddev" / "skills" / "profile" / "stacks" / f"{stack_id}.md",
188:            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "skills" / "profile" / "stacks" / f"{stack_id}.md",
189:            Path.home() / ".claude" / "plugins" / "backenddev" / "skills" / "profile" / "stacks" / f"{stack_id}.md",
190:            Path(__file__).resolve().parent.parent.parent / "profile" / "stacks" / f"{stack_id}.md",
191:        ]
```

Kunci index (7 vs 4A vs 4B vs 3 vs 2 vs 1): `tech-lead:93-96`, `business-analysis:163`, `system-analysis:203`, `plan:192`, `architect:158`, `debug:88`, `report:292`, `analyst:173`, `task:228`, `audit:132`, `document-api:116`.

Docstring basi, `_common/precondition_lib.py:9-10`: *"Yang diekstrak ke sini sengaja sempit: uji izin tulis beserta pencarian direktori induknya, dua fungsi yang tersalin apa adanya di sembilan skrip."*

### Reproduksi

**1. Berkas unicode/berspasi di dalam taskdir dilaporkan kotor di luar taskdir**

```bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
S=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); cd "$tmp" && git init -q && git config user.email t@t && git config user.name t
TD=backenddev/docs/2601011200-refund; mkdir -p $TD .claude/profile src
echo '{"stack":"go","architecture":"layered","root_namespace":"x","source_root":"src","commit_convention":"c","base_branch":"main","branch_convention":"feat/<slug>"}' > .claude/profile/index.json
printf -- '---\nstatus: ACTIVE\nchain: BRIEF\n---\n# T\n' > $TD/TASK.md
git add -A && git commit -qm init
echo "catatan" > "$TD/café.md"; echo "catatan" > "$TD/catatan rapat.md"
echo "== git status --porcelain (v1, tanpa -z)"; git status --porcelain -uall
echo "== analyst check 6";  python3 $S/analyst/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --risk MINOR --chain BRIEF | grep '^\[6\]'
echo "== task check 5";     python3 $S/task/scripts/check_preconditions.py --root "$tmp" --taskdir $TD --lane DIRECT_BRIEF --chain BRIEF | grep '^\[5\]'
echo "== tech-lead --re-entry check 3"; python3 $S/tech-lead/scripts/check_preconditions.py --root "$tmp" --re-entry | grep '^\[3\]'
echo "== git status --porcelain -z (usulan)"; git status --porcelain -z -uall | tr '\0' '\n'
rm -rf "$tmp"
```

```
== git status --porcelain (v1, tanpa -z)
?? "backenddev/docs/2601011200-refund/caf\303\251.md"
?? "backenddev/docs/2601011200-refund/catatan rapat.md"
== analyst check 6
[6] Git Worktree & Working Tree Status  : FAIL (Working tree kotor di luar taskdir (2 file: "backenddev/docs/2601011200-refund/caf\303\251.md", "backenddev/docs/2601011200-refund/catatan rapat.md"))
== task check 5
[5] Git Worktree & Working Tree Status  : FAIL (Working tree kotor di luar taskdir (2 file: "backenddev/docs/2601011200-refund/caf\303\251.md", "backenddev/docs/2601011200-refund/catatan rapat.md"))
== tech-lead --re-entry check 3
[3] Git Clean Working Tree       : PASS (Mode re-entry: 2 berkas artefak menunggu commit gerbang, nol berkas di luar zona artefak)
== git status --porcelain -z (usulan)
?? backenddev/docs/2601011200-refund/café.md
?? backenddev/docs/2601011200-refund/catatan rapat.md
```

**2. Fallback `~/.gemini` menutupi agent yang hilang dari plugin terpasang** (plugin disalin ke tmp; repo tidak disentuh)

```bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
tmp=$(mktemp -d); cp -r $REPO/src/plugins/backenddev $tmp/plug
rm $tmp/plug/agents/code-explorer.md                       # plugin terpasang kehilangan agent
mkdir -p $tmp/home/.gemini/config/plugins/backenddev/agents
echo "# salinan lama" > $tmp/home/.gemini/config/plugins/backenddev/agents/code-explorer.md
mkdir $tmp/repo && cd $tmp/repo && git init -q
echo "== HOME tanpa .gemini"
HOME=$tmp/emptyhome python3 $tmp/plug/skills/tech-lead/scripts/check_preconditions.py --root "$tmp/repo" | grep '^\[6\]'
echo "== HOME dengan ~/.gemini/config/plugins/backenddev/agents/code-explorer.md"
HOME=$tmp/home python3 $tmp/plug/skills/tech-lead/scripts/check_preconditions.py --root "$tmp/repo" | grep '^\[6\]'
rm -rf "$tmp"
```

```
== HOME tanpa .gemini
[6] Explorer Dispatcher & Agent  : FAIL (Definisi subagent agents/code-explorer.md tidak ditemukan)
== HOME dengan ~/.gemini/config/plugins/backenddev/agents/code-explorer.md
[6] Explorer Dispatcher & Agent  : PASS (Template dispatcher/explorer.md dan agent code-explorer.md terverifikasi)
```

### Dampak

- **Rantai planning (analyst/task) berhenti** begitu ada berkas bernama non-ASCII atau berspasi di taskdir. Pesannya menyuruh user membersihkan berkas "di luar taskdir" yang sebenarnya di dalam.
- **Check keberadaan agent/template/adapter lolos palsu** di mesin yang juga memasang salinan Gemini, atau saat skill dijalankan di repo pengembang plugin ini. Kegagalan baru muncul saat dispatch.
- **Kunci profil yang berbeda-beda:** profil tanpa `base_branch` lolos di 8 skrip dan baru gagal di architect/report, jauh di hilir rantai.
- **Setiap perbaikan skrip harus diulang di 14 salinan**, dan salinan yang tertinggal akan divergen lagi. L5.2 dan L5.4 adalah contoh divergensi yang sudah terjadi.

### Rencana perbaikan

1. **Bagian A** ditambahkan ke `_common/precondition_lib.py` bersama unit test-nya (C.2). Docstring modul ditulis ulang.
2. **Bootstrap impor** di analyst, architect, report, task, `scaffold_brief.py`, `validate_briefs.py` (bagian A, blok terakhir).
3. **Ganti call site per tabel B.2**, satu skrip per commit (C.3):
   - `self._find_repo_root()` → `find_repo_root()`, lalu hapus def-nya (14×).
   - Daftar kandidat path (29 daftar, 64 path) → `find_agent(name)` / `plugin_file(*parts)`. Hanya relatif `PLUGIN_ROOT`; tidak ada `Path.home()` maupun `self.root / "src" / "plugins"`.
   - Porcelain → `dirty_paths(self.root)`. analyst/task: `[p for p in dirty if not is_under(p, self.td.rel)]`. tech-lead mode re-entry: `any(is_under(p, x) for x in RE_ENTRY_ALLOWED_PREFIXES)`. architect/report: cukup `bool(dirty_paths(...))`. `GitError` → FAIL dengan pesan git.
   - Blok `index.json` → `data, err = load_profile_index(self.root)`, lalu `err` → FAIL, dengan pesan remediasi lama per skrip. document-api: `required=("stack",)` hanya bila `--stack` kosong.
   - `format_text`/`to_json` → isi satu baris ke lib. tech-lead: `header_suffix=" · mode: re-entry"`. Skrip berbanner: `banner=freshness_banner(...)`.
4. **Hapus** `_strip_explore_scratch` (2), `_porcelain_paths` (1), `_resolve_taskdir` (8), `_get_rel_taskdir_str` (4), `_declared_chain` (2), dan `_read` di `scaffold_brief.py`/`validate_briefs.py` (diganti `read_text` yang dibungkus try).
5. **Gerbang grep** di "Definisi selesai" dijalankan di akhir PR.

### Test yang ditambahkan

| Test | Input | Assert |
|---|---|---|
| `tests/backenddev/test_common_git.py::test_dirty_paths_unicode_dan_spasi` | berkas `café.md`, `catatan rapat.md` | path apa adanya, tanpa kutip/escape |
| `…::test_dirty_paths_rename_mengambil_tujuan` | `git mv a b` | `["b"]` |
| `…::test_dirty_paths_nama_berpanah` | berkas `src/a -> b.go` | `["src/a -> b.go"]` |
| `…::test_scratch_hanya_laci_taskdir` | `backenddev/docs/<td>/.explore/a.md`, `internal/.explore/q.go` | yang pertama dibuang, yang kedua dilaporkan (B6) |
| `…::test_dirty_paths_bukan_repo` | direktori non-git | `GitError` |
| `…::test_find_repo_root_dari_subdir` | `start=<repo>/backenddev/docs` | `== repo.resolve()` |
| `tests/backenddev/test_common_profile.py::test_load_profile_index_tujuh_kunci` | index tanpa `branch_convention` | `(None, "...branch_convention")` |
| `…::test_load_profile_index_subset` | sama, `required=("stack",)` | `data["stack"] == "go"` |
| `…::test_find_agent_mengabaikan_salinan_home` | salin plugin ke tmp, hapus agent, `HOME` berisi `.gemini` (fixture `env` dari 06) | tech-lead check 6 FAIL (reproduksi 2) |
| `tests/backenddev/test_common_output.py::test_format_text_banner_dan_header` | 2 hasil, banner BASI | baris 1 `[TERDEGRADASI]…`, header `(1/2 passed)` |
| `…::test_to_json_urutan_kunci` | `taskdir="x"` | kunci `status, passed_count, total_count, root, taskdir, checks` |
| `tests/backenddev/test_analyst_preconditions.py::test_berkas_unicode_di_taskdir_tidak_kotor` | reproduksi 1 | check 6 PASS |
| `tests/backenddev/test_task_preconditions.py::test_berkas_unicode_di_taskdir_tidak_kotor` | reproduksi 1 | check 5 PASS |
| `tests/backenddev/test_golden.py` (C.1) | 12 skrip × 4 fixture | identik dengan golden kecuali check yang diperbaiki |
| `tests/test_lint_paths.py::test_tidak_ada_path_home_atau_repo_dev` (atau aturan L6.3) | grep skrip backenddev | nol kemunculan |

### Selesai bila

- Reproduksi 1: analyst check 6 dan task check 5 PASS.
- Reproduksi 2: check 6 FAIL pada kedua HOME.
- Gerbang grep di "Definisi selesai" nol; 14 skrip mengimpor `precondition_lib`.
- Golden hanya berubah pada check yang disebut di pesan commit.

### Risiko & catatan

- **Kunci profil 7 di semua skrip (keputusan 1).** Profil lama yang tidak lengkap akan gagal lebih awal (di tech-lead, business-analysis, dan lainnya), bukan di architect. Ini disengaja karena template profil selalu menulis ketujuhnya.
- **`-uall` di architect/report** melaporkan setiap berkas di direktori untracked. Di repo dengan direktori untracked besar yang tidak di-gitignore, output-nya panjang, tetapi check-nya hanya butuh "kosong atau tidak".
- **Lebar kolom teks disatukan menjadi 32.** Keluaran analyst (35) dan tech-lead (28) bergeser secara kosmetik. Hanya golden teks yang terpengaruh; golden JSON tidak.
- **Modul bernama sama:** `precondition_lib` backenddev dan frontenddev bertabrakan bila diimpor lewat `sys.path` di satu sesi pytest. Unit test wajib memakai `load_module(path, "bd_precondition_lib")` (C.0).

---

## L5.6 [Sedang] False positive placeholder di tiga validator frontenddev

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 1 hari · **Bergantung pada:** C.0 (fondasi test) · **Memblokir:** —

### Konteks

Tiga validator menyapu placeholder dengan tiga aturan berbeda:

- `validate_doc` (FLOW/UI/CONTRACT) dan `plan/validate_briefs` memakai `TODO|TBD|FIXME|diisi nanti` **IGNORECASE**, ditambah `<…>` bila berisi spasi, tanpa melewati inline code.
- `validate_task` membuang inline code, lalu menganggap `<…>` apa pun sebagai placeholder.

Padahal JSX (`<Skeleton />`, `<EmptyState />`), perbandingan (`< 300 ms`), dan kata "todo" sah di dokumen UI frontend.

**Koreksi terhadap ISSUES.md:** `validate_task` tidak FAIL pada `` `<Spinner />` `` maupun "todo list". Ia FAIL pada SC `< 300 ms`, pada `<Skeleton />` tanpa backtick, dan pada `<OrderRow>`. Ia juga meloloskan slot `<slug>` di dalam inline code (false negative).

### Lokasi & kode saat ini

`src/plugins/frontenddev/skills/_common/validate_doc.py:46-52`, `:233-246`

```python
 46: PLACEHOLDER = re.compile(r"\b(TBD|TODO|FIXME|diisi nanti|isi nanti)\b", re.IGNORECASE)
 47: ANGLE = re.compile(r"<([^<>\n]{1,80})>")
233:         for line in outside_fences(self.body.splitlines()):
234:             if PLACEHOLDER.search(line):
237:             for m in ANGLE.finditer(line):
238:                 content = m.group(1).strip()
239:                 if SLOT_WORD.match(content):
242:                 if TS_SYNTAX.search(content):
244:                 if " " in re.sub(r",\s+", ",", content):
```

`src/plugins/frontenddev/skills/plan/scripts/validate_briefs.py:98`, `:126-134`, `:511`

```python
 98: PLACEHOLDER = re.compile(r"\b(TBD|TODO|FIXME|diisi nanti|isi nanti)\b", re.IGNORECASE)
126:     for m in ANGLE_SPAN.finditer(line):
127:         content = m.group(1).strip()
128:         if ANGLE_SLOT.match(content):
130:         if TS_TYPE_SYNTAX.search(content):
132:         probe = re.sub(r",\s+", ",", content)
133:         if " " in probe and re.search(r"[a-z]", probe, re.IGNORECASE):
134:             return True
511:                     if PLACEHOLDER.search(line) or angle_placeholder(line):
```

`src/plugins/frontenddev/skills/task/scripts/validate_task.py:41-42`, `:162-163`

```python
 41: INLINE_CODE = re.compile(r"`[^`\n]*`")
 42: PLACEHOLDER = re.compile(r"\bTBD\b|\bTODO\b|diisi nanti|<[^<>\n]+>")
162:         stripped = INLINE_CODE.sub("", text.split("\n## Chain", 1)[0])
163:         hits = sorted(set(PLACEHOLDER.findall(stripped)))
```

### Reproduksi

Level predikat: fungsi validator dipanggil apa adanya pada satu baris.

```bash
#!/usr/bin/env bash
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
FE=$REPO/src/plugins/frontenddev/skills
python3 - "$FE" <<'PY'
import sys, importlib.util
fe = sys.argv[1]; sys.path.insert(0, fe + "/_common")
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
vdoc = load("vdoc", fe + "/_common/validate_doc.py")
vbr  = load("vbr",  fe + "/plan/scripts/validate_briefs.py")
vtk  = load("vtk",  fe + "/task/scripts/validate_task.py")
def doc(line):      # DocValidator._check_placeholders apa adanya
    v = vdoc.DocValidator.__new__(vdoc.DocValidator); v.body, v.results = line, []
    v._check_placeholders(); return v.results[0]["status"]
def brief(line):    # ekspresi validate_briefs.py:511 apa adanya
    return "FAIL" if (vbr.PLACEHOLDER.search(line) or vbr.angle_placeholder(line)) else "PASS"
def task(line):     # TaskValidator._check_7_placeholder_findings apa adanya
    t = vtk.TaskValidator.__new__(vtk.TaskValidator); t.results, t.fm, t.sections = [], {}, {}
    t._check_7_placeholder_findings(line); return t.results[0]["status"]
cases = [
    ("sah", "Saat memuat tampilkan `<Spinner />` di tengah kartu."),
    ("sah", "Saat memuat tampilkan <Skeleton /> tiga baris."),
    ("sah", "Fitur todo list menampilkan butir yang belum selesai."),
    ("sah", "- [ ] **SC-1**: waktu muat < 300 ms dan jumlah item > 0 — verifikasi: test"),
    ("sah", "Props `Record<string, string>` diteruskan ke <OrderRow>."),
    ("slot", "Nama layar: <Nama Layar Utama>"),
    ("slot", "Berkas `src/features/<slug>/api.ts` dibuat."),
    ("slot", "Keputusan: TBD"),
]
print(f"{'harap':<5} | {'validate_doc':<12} | {'plan':<5} | {'task':<5} | baris")
for want, line in cases:
    print(f"{want:<5} | {doc(line):<12} | {brief(line):<5} | {task(line):<5} | {line}")
PY
```

Output aktual:

```
harap | validate_doc | plan  | task  | baris
sah   | FAIL         | FAIL  | PASS  | Saat memuat tampilkan `<Spinner />` di tengah kartu.
sah   | FAIL         | FAIL  | FAIL  | Saat memuat tampilkan <Skeleton /> tiga baris.
sah   | FAIL         | FAIL  | PASS  | Fitur todo list menampilkan butir yang belum selesai.
sah   | FAIL         | FAIL  | FAIL  | - [ ] **SC-1**: waktu muat < 300 ms dan jumlah item > 0 — verifikasi: test
sah   | PASS         | PASS  | FAIL  | Props `Record<string, string>` diteruskan ke <OrderRow>.
slot  | FAIL         | FAIL  | FAIL  | Nama layar: <Nama Layar Utama>
slot  | FAIL         | FAIL  | PASS  | Berkas `src/features/<slug>/api.ts` dibuat.
slot  | FAIL         | FAIL  | FAIL  | Keputusan: TBD
```

### Dampak

- UI.md dan brief yang menyebut komponen state (`<Skeleton />`, `<EmptyState />`) tidak pernah lolos Gate Design maupun validasi brief. Model akan memelintir teks, misalnya menghapus `/` atau menulis "komponen Skeleton", atau berputar sampai plafon revisi.
- Fitur bernama "Todo" mustahil lolos di validate_doc/plan.
- SC yang terukur (`< 300 ms`) ditolak di akar TASK.md, sehingga penulis terdorong menulis SC yang lebih kabur.
- Slot `<slug>` di path berbacktick lolos di TASK.md.

### Rencana perbaikan

1. **`frontenddev/skills/_common/precondition_lib.py`:** tambah satu pendeteksi bersama. Kode ini sudah diuji (`fe_placeholder.py` di scratchpad):

   ```python
   INLINE_CODE = re.compile(r"`[^`\n]*`")
   # TODO/TBD/FIXME hanya huruf besar (penanda penulis); frasa Indonesia tak peka huruf.
   WORD_PLACEHOLDER = re.compile(r"\b(?:TBD|TODO|FIXME)\b|(?i:\b(?:diisi nanti|isi nanti)\b)")
   # Slot `<...>`: dibuka huruf/underscore tepat sesudah `<`, ditutup non-spasi non-`/` tepat
   # sebelum `>`. `< 300 ms dan item >` (operator) dan `<Spinner />` (JSX) gugur di sini.
   ANGLE = re.compile(r"<(?=[A-Za-z_])([^<>\n]{1,80}?)(?<=[^\s/])>")
   TS_SYNTAX = re.compile(r"[{}:;=|]")
   SLOT_WORDS = frozenset("""
   slug stack stack-id stack_id feat feature taskdir unit unit-slug nn mm n nama path berkas file
   layer layar perintah command sha commit tanggal versi judul deskripsi angka nilai id elemen field
   skenario langkah alasan keputusan platform rute entitas
   """.split())   # gabungan SLOT_WORD validate_doc.py:49-52 dan ANGLE_SLOT validate_briefs.py:106-111


   def _is_slot(content: str) -> bool:
       content = content.strip()
       if content.lower() in SLOT_WORDS:
           return True
       if TS_SYNTAX.search(content):
           return False
       return " " in re.sub(r",\s+", ",", content)


   def find_placeholders(line: str) -> List[str]:
       """Token placeholder yang tersisa di satu baris (kosong bila bersih)."""
       hits: List[str] = []
       for m in INLINE_CODE.finditer(line):          # di dalam inline code: hanya kosakata slot
           for a in ANGLE.finditer(m.group(0)):
               if a.group(1).strip().lower() in SLOT_WORDS:
                   hits.append(a.group(0))
       prose = INLINE_CODE.sub(" ", line)
       hits += [m.group(0) for m in WORD_PLACEHOLDER.finditer(prose)]
       hits += [m.group(0) for m in ANGLE.finditer(prose) if _is_slot(m.group(1))]
       return hits
   ```

2. **`validate_doc.py:231-248`:** loop menjadi `for line in outside_fences(...): if find_placeholders(line): problems.append(...)`. Hapus `PLACEHOLDER`, `ANGLE`, `TS_SYNTAX`, `SLOT_WORD` (baris 46–52).
3. **`plan/scripts/validate_briefs.py:97-135`, `:511`:** hapus `PLACEHOLDER`, `ANGLE_SPAN`, `ANGLE_SLOT`, `TS_TYPE_SYNTAX`, `angle_placeholder`; baris 511 → `if find_placeholders(line):`.
4. **`task/scripts/validate_task.py:41-42`, `:160-165`:** `hits = sorted({h for l in text.split("\n## Chain", 1)[0].splitlines() for h in find_placeholders(l)})`. `INLINE_CODE` lokal dihapus.
5. Teks tindakan ketiga validator diseragamkan: "Ganti `TBD`/`TODO`/`FIXME`/`diisi nanti`/slot `<…>` dengan isi nyata. JSX (`<X />`), generik TS, dan operator perbandingan bukan placeholder."

Tabel sebelum vs sesudah (keluaran aktual scratchpad; kolom "usulan" = `find_placeholders` di atas):

```
harap | validate_doc | plan/validate_briefs | validate_task | usulan     | baris
sah   | FAIL         | FAIL                 | PASS          | PASS       | Saat memuat tampilkan `<Spinner />` di tengah kartu.
sah   | FAIL         | FAIL                 | FAIL          | PASS       | Saat memuat tampilkan <Skeleton /> tiga baris.
sah   | FAIL         | FAIL                 | PASS          | PASS       | Fitur todo list menampilkan butir yang belum selesai.
sah   | FAIL         | FAIL                 | FAIL          | PASS       | - [ ] **SC-1**: waktu muat < 300 ms dan jumlah item > 0 — verifikasi: test
sah   | PASS         | PASS                 | FAIL          | PASS       | Props `Record<string, string>` diteruskan ke <OrderRow>.
slot  | FAIL         | FAIL                 | FAIL          | FAIL       | Nama layar: <Nama Layar Utama>
slot  | FAIL         | FAIL                 | PASS          | FAIL       | Berkas `src/features/<slug>/api.ts` dibuat.
slot  | FAIL         | FAIL                 | FAIL          | FAIL       | Keputusan: TBD
slot  | FAIL         | FAIL                 | FAIL          | FAIL       | Alasan diisi nanti.
```

### Test yang ditambahkan

| Test | Input | Assert |
|---|---|---|
| `tests/frontenddev/test_placeholder.py::test_find_placeholders` (parametrik, 9 baris tabel) | kolom "baris" | kosong untuk "sah", non-kosong untuk "slot" |
| `…::test_jsx_berattribut` | `<Button variant="primary">`, `<Spinner size="sm" />` | kosong |
| `…::test_todo_huruf_besar_tetap_ditolak` | `TODO: pastikan` | `["TODO"]` |
| `…::test_slot_dalam_backtick_hanya_kosakata` | `` `<Nama Komponen>` ``, `` `<NN>` `` | kosong, `["<NN>"]` |
| `tests/frontenddev/test_validate_doc.py::test_ui_skeleton_lolos_check_b` | contoh terisi UI template + baris `<Skeleton />` | check B PASS |
| `tests/frontenddev/test_validate_briefs.py::test_check_b_todo_list` | brief contoh + "fitur todo list" di seksi 2 | check B PASS |
| `tests/frontenddev/test_validate_task.py::test_sc_perbandingan_bukan_placeholder` | TASK contoh dengan SC `< 300 ms` | check 7 PASS |
| `…::test_slug_dalam_backtick_ditolak` | `` `src/features/<slug>/api.ts` `` di Description | check 7 FAIL |

### Selesai bila

Kolom ketiga validator pada tabel reproduksi sama dengan kolom "usulan", dan ketiganya memakai `find_placeholders` dari `precondition_lib`: `grep -n 'PLACEHOLDER = ' src/plugins/frontenddev/skills/{_common/validate_doc.py,plan/scripts/validate_briefs.py,task/scripts/validate_task.py}` kosong.

### Risiko & catatan

- **Keputusan 4:** di dalam inline code hanya slot berkosakata (`<slug>`, `<NN>`) yang ditolak. `` `<Nama Komponen>` `` di dalam backtick lolos. Kompromi ini diambil karena backtick lazim dipakai untuk JSX dan generik.
- `todo`/`tbd` huruf kecil tidak lagi ditangkap. Penanda penulis di template memang huruf besar.
- Operator tanpa spasi (`jumlah<5 dan total>0`) masih bisa terbaca sebagai slot multi-kata `<5 dan total>`. Tidak, karena `<` harus diikuti huruf. Kasus `a<b dan c>d` tetap terbaca slot; kasus ini jarang dan tidak ditangani.

---

## L5.7 [Sedang] Huruf besar-kecil `qa manual:` tidak konsisten

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 0,25 hari · **Bergantung pada:** — · **Memblokir:** L4.2 (validator REVIEW/REPORT substansi memakai `is_manual`)

### Konteks

Empat pembaca menilai "SC/AC ini beralat ukur QA manual" dengan empat aturan:

| Pembaca | Aturan |
|---|---|
| `validate_task.py:37` | regex `— verifikasi:\s*(…|QA manual:)` IGNORECASE, di mana saja |
| `validate_review.py:137` | substring `"QA manual:"` **peka huruf**, di mana saja pada baris SC |
| `validate_report.py:133-135` | teks sesudah `— verifikasi:` pertama, `.lower().startswith("qa manual:")` |
| `validate_doc.py:302` (CONTRACT, pembaca keempat) | `"qa manual:" in how.lower()` |

**Koreksi terhadap ISSUES.md:** ISSUES hanya menyebut tiga pembaca; ada pembaca keempat. Selain itu, `validate_review` juga keliru ke arah lain: ia mencocokkan `QA manual:` yang muncul di deskripsi SC, bukan di posisi alat ukur.

### Lokasi & kode saat ini

```python
# src/plugins/frontenddev/skills/task/scripts/validate_task.py:37
MEASURE = re.compile(r"— verifikasi:\s*(test|diff|typecheck|lint|build|QA manual:)", re.IGNORECASE)
# src/plugins/frontenddev/skills/architect/scripts/validate_review.py:137
            if verdict == "PERLU VERIFIKASI MANUAL" and "QA manual:" not in line:
# src/plugins/frontenddev/skills/report/scripts/validate_report.py:133-135
        manual = [m.group(1) for m in map(SC_LINE.match, (l.strip() for l in self.task.splitlines()))
                  if m and "— verifikasi:" in m.group(2) and not re.search(r"—\s*gugur:", m.group(2))
                  and m.group(2).split("— verifikasi:", 1)[1].strip().lower().startswith("qa manual:")]
# src/plugins/frontenddev/skills/_common/validate_doc.py:302
            if "test otomatis" not in how and "qa manual:" not in how:
```

### Reproduksi

````bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
FE=$REPO/src/plugins/frontenddev/skills
tmp=$(mktemp -d); cd "$tmp" && git init -q && git config user.email t@t && git config user.name t
TD=frontenddev/docs/2601011200-promo; mkdir -p $TD
cat > $TD/TASK.md <<'T'
---
status: ACTIVE
lane: HOTFIX_MINOR
sections: -
created: 2026-01-01
---
# Banner promo

## Description
Perbaiki banner.

## Success Criteria
- [ ] **SC-1**: banner tampil di beranda — verifikasi: qa manual: buka beranda, lihat banner

## Out of Scope
- checkout — di luar permintaan

## Chain
T
git add -A && git commit -qm "docs(promo): root task"
BASE=$(git rev-parse --short HEAD)
cat > $TD/REVIEW.md <<R
---
artifact: REVIEW
verdict: PASS
p1: 0
p2: 0
p3: 0
base: $BASE
reviewed_at: 2026-01-02
---
# Review Findings — promo

## Summary
ok

## Verifikasi Penutup
| Perintah | Hasil | Galat baru |
|---|---|---|
| npm run build | HIJAU | 0 |

## Cakupan Success Criteria
| SC | Vonis | Bukti |
|---|---|---|
| SC-1 | PERLU VERIFIKASI MANUAL | buka beranda |

## Cakupan Acceptance Criteria

## Temuan

## Done Criteria DITUNDA

## Umpan balik profil

## 9 Dimensi
R
echo "== validate_task check 3 (alat ukur)"
python3 $FE/task/scripts/validate_task.py --root "$tmp" --taskdir $TD | grep '^\[3\]'
echo "== validate_review check SC"
python3 $FE/architect/scripts/validate_review.py --root "$tmp" --taskdir $TD | grep -A1 '^\[SC\]'
echo "== ketiga pembaca pada variasi penulisan alat ukur"
python3 - "$FE" <<'PY'
import re, sys
MEASURE = re.compile(r"— verifikasi:\s*(test|diff|typecheck|lint|build|QA manual:)", re.IGNORECASE)  # validate_task.py:37
review  = lambda l: "QA manual:" in l                                                             # validate_review.py:137
report  = lambda l: "— verifikasi:" in l and l.split("— verifikasi:", 1)[1].strip().lower().startswith("qa manual:")  # validate_report.py:133-135
for l in ["x — verifikasi: QA manual: buka", "x — verifikasi: qa manual: buka", "x — verifikasi: Qa Manual: buka",
          "x — verifikasi: QA  manual: buka", "cek QA manual: dulu — verifikasi: test"]:
    print(f"{l:<42} task={'sah' if MEASURE.search(l) else 'tolak':<5} review_manual={str(review(l)):<5} report_manual={report(l)}")
PY
rm -rf "$tmp"
````

Output aktual:

```
== validate_task check 3 (alat ukur)
[3] Alat ukur sah                    : PASS (lolos)
== validate_review check SC
[SC] Cakupan Success Criteria       : FAIL (1 pelanggaran)
      - `SC-1` bukan SC ber-alat-ukur `QA manual:` — wajib divonis terbukti/belum
== ketiga pembaca pada variasi penulisan alat ukur
x — verifikasi: QA manual: buka            task=sah   review_manual=True  report_manual=True
x — verifikasi: qa manual: buka            task=sah   review_manual=False report_manual=True
x — verifikasi: Qa Manual: buka            task=sah   review_manual=False report_manual=True
x — verifikasi: QA  manual: buka           task=tolak review_manual=False report_manual=False
cek QA manual: dulu — verifikasi: test     task=sah   review_manual=True  report_manual=False
```

### Dampak

Akar TASK.md dengan `qa manual:` lolos di awal, tetapi reviewer tidak bisa memvonis `PERLU VERIFIKASI MANUAL`. Reviewer terpaksa memilih antara `terbukti` (tidak jujur) dan `belum terbukti` (verdict BLOCKED yang tidak bisa diperbaiki lewat kode). Sementara itu `validate_report` tetap menuntut catatan manual untuk SC itu. Baris terakhir tabel menunjukkan divergensi ke arah sebaliknya.

### Rencana perbaikan

1. **`_common/precondition_lib.py` frontenddev** (diuji di `fe_fix.py`):

   ```python
   VERIFY_MARK = "— verifikasi:"
   _MANUAL = re.compile(r"qa\s+manual\s*:", re.IGNORECASE)

   def measure_of(sc_text: str) -> str:
       """Teks alat ukur sesudah penanda `— verifikasi:` pertama; kosong bila tidak ada."""
       head, sep, tail = sc_text.partition(VERIFY_MARK)
       return tail.strip() if sep else ""

   def is_manual(sc_text: str) -> bool:
       """SC beralat ukur `QA manual:` (huruf besar-kecil dan spasi bebas), hanya di posisi alat ukur."""
       return bool(_MANUAL.match(measure_of(sc_text)))

   def is_manual_cell(how: str) -> bool:
       """Sel `Cara verifikasi` AC CONTRACT."""
       return bool(re.match(r"\s*qa\s+manual\s*:", how, re.IGNORECASE))
   ```

2. **`validate_task.py:37`:** `MEASURE = re.compile(r"— verifikasi:\s*(test|diff|typecheck|lint|build|qa\s+manual:)", re.IGNORECASE)`. Varian spasi ganda tidak lagi ditolak diam-diam.
3. **`validate_review.py:137`:** `if verdict == "PERLU VERIFIKASI MANUAL" and not is_manual(line):`.
4. **`validate_report.py:133-135`:** `... if m and not re.search(r"—\s*gugur:", m.group(2)) and is_manual(m.group(2))`.
5. **`validate_doc.py:302`:** `if "test otomatis" not in how and not is_manual_cell(cells[1]):`.

Hasil `is_manual` pada lima baris yang sama (keluaran aktual): True, True, True, True, False.

### Test yang ditambahkan

| Test | Input | Assert |
|---|---|---|
| `tests/frontenddev/test_precondition_lib.py::test_is_manual` (parametrik 5 baris) | tabel reproduksi | T, T, T, T, F |
| `tests/frontenddev/test_validate_review.py::test_perlu_verifikasi_manual_qa_huruf_kecil` | fixture reproduksi | check SC PASS |
| `…::test_qa_manual_di_deskripsi_bukan_alat_ukur` | SC `cek QA manual: dulu — verifikasi: test`, vonis PERLU VERIFIKASI MANUAL | check SC FAIL |
| `tests/frontenddev/test_validate_report.py::test_manual_huruf_kecil_wajib_catatan` | TASK `qa manual:`, REPORT tanpa catatan | check 5 FAIL "SC QA manual tanpa" |
| `tests/frontenddev/test_validate_task.py::test_qa_spasi_ganda_diterima` | `— verifikasi: QA  manual: …` | check 3 PASS |

### Selesai bila

Fixture reproduksi: validate_task check 3 PASS dan validate_review check SC PASS. Keempat pembaca memanggil `is_manual`/`is_manual_cell`: `grep -rn '"QA manual:"\|"qa manual:"' src/plugins/frontenddev/skills/*/scripts src/plugins/frontenddev/skills/_common/validate_doc.py` kosong.

### Risiko & catatan

Keputusan 5: aturan tak peka huruf di semua pembaca (disarankan) vs ejaan kanonik `QA manual:` yang ditegakkan ketat sejak `validate_task`. Opsi ketat lebih bersih, tetapi TASK.md lama yang sudah ter-commit dengan `qa manual:` akan gagal di amandemen.

---

## L5.8 [Sedang] Path non-ASCII dan route group berkurung ditolak

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 0,5 hari · **Bergantung pada:** — · **Memblokir:** L4.2 (`validate_report`)

### Konteks

`chain_files()` adalah sumber "berkas rantai" untuk validate_report check 4. Fungsi ini memanggil `git show --name-only` tanpa `core.quotePath=false`, sehingga path non-ASCII keluar berkutip dan ber-escape oktal. Di sisi lain, `BULLET` validate_report melarang kurung di dalam anotasi. Akibatnya route group Expo Router `app/(tabs)/…` dan SvelteKit `src/routes/(app)/…` tidak bisa disebut.

### Lokasi & kode saat ini

`src/plugins/frontenddev/skills/_common/precondition_lib.py:938-944`

```python
938: def chain_files_since(root: Path, taskdir_rel: str, since: str) -> List[str]:
939:     files: List[str] = []
940:     for sha in chain_commits(root, taskdir_rel, since):
941:         out = git(root, "show", "--name-only", "--format=", sha, "--", ".",
942:                   ":(exclude)frontenddev/docs", ":(exclude).claude")
943:         files += [l.strip() for l in out.splitlines() if l.strip()]
944:     return files
```

`src/plugins/frontenddev/skills/report/scripts/validate_report.py:38`, `:106-112`

```python
 38: BULLET = re.compile(r"^- (.+) \(([^()]+)\)\s*$")
106:         bullets = [BULLET.match(l) for l in lines]
110:         if any(b is None for b in bullets):
111:             errors.append("butir tanpa `(<berkas atau direktori>)` di ujungnya")
112:         refs = [r.strip().strip("`").rstrip("/") for b in bullets if b for r in b.group(2).split(",")]
```

### Reproduksi

```bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
FE=$REPO/src/plugins/frontenddev/skills
tmp=$(mktemp -d); cd "$tmp" && git init -q && git config user.email t@t && git config user.name t
TD=frontenddev/docs/2601011200-promo; mkdir -p $TD
printf -- '---\nstatus: ACTIVE\n---\n# Banner promo\n\n## Success Criteria\n- [ ] **SC-1**: x — verifikasi: test\n' > $TD/TASK.md
git add -A && git commit -qm "docs(promo): root task"
mkdir -p src/i18n "app/(tabs)"
echo 'export default {}' > src/i18n/café.tsx
echo 'export default function T(){}' > "app/(tabs)/index.tsx"
git add -A && git commit -qm "feat(promo): implement unit 01"
echo "== chain_files() sekarang"
python3 -c "import sys; sys.path.insert(0,'$FE/_common'); from precondition_lib import chain_files; print(chain_files(__import__('pathlib').Path('$tmp'), '$TD'))"
report() { printf -- '# Banner promo — Report\n\n## Ringkasan\nBanner promo tampil.\n\n## Perubahan\n%s\n' "$1" > $TD/REPORT.md
           python3 $FE/report/scripts/validate_report.py --root "$tmp" --taskdir $TD | grep '^\[4\]'; }
echo "== REPORT: butir menunjuk berkas unicode dan direktori induknya"
report $'- Tambah terjemahan (src/i18n/café.tsx)\n- Tambah tab (app)'
report $'- Tambah terjemahan (src/i18n)\n- Tambah tab (app)'
echo "== REPORT: butir menunjuk route group berkurung"
report $'- Tambah terjemahan (src/i18n)\n- Tambah tab (app/(tabs)/index.tsx)'
echo "== usulan: git -c core.quotePath=false ... -z"
git -c core.quotePath=false show -z --name-only --format= HEAD -- . ':(exclude)frontenddev/docs' ':(exclude).claude' | tr '\0' '\n'
rm -rf "$tmp"
```

Output aktual:

```
== chain_files() sekarang
['"src/i18n/caf\\303\\251.tsx"', 'app/(tabs)/index.tsx']
== REPORT: butir menunjuk berkas unicode dan direktori induknya
[4] Perubahan berakar berkas rantai  : FAIL (bukan berkas rantai: src/i18n/café.tsx; berkas rantai tak tercakup: "src/i18n/caf\303\251.tsx")
[4] Perubahan berakar berkas rantai  : FAIL (bukan berkas rantai: src/i18n; berkas rantai tak tercakup: "src/i18n/caf\303\251.tsx")
== REPORT: butir menunjuk route group berkurung
[4] Perubahan berakar berkas rantai  : FAIL (butir tanpa `(<berkas atau direktori>)` di ujungnya; bukan berkas rantai: src/i18n; berkas rantai tak tercakup: "src/i18n/caf\303\251.tsx", app/(tabs)/index.tsx)
== usulan: git -c core.quotePath=false ... -z
app/(tabs)/index.tsx
src/i18n/café.tsx
```

### Dampak

REPORT.md tidak bisa ditulis dengan jujur untuk rantai yang menyentuh berkas i18n non-ASCII, atau untuk rute di Expo Router/SvelteKit, dua stack yang didukung plugin. Pesan "butir tanpa `(<berkas>)`" menyesatkan. REPORT yang gagal commit adalah jalan buntu yang dibahas di L4.6.

### Rencana perbaikan

1. **`precondition_lib.py:938-944`:**

   ```python
   def chain_files_since(root: Path, taskdir_rel: str, since: str) -> List[str]:
       files: List[str] = []
       for sha in chain_commits(root, taskdir_rel, since):
           out = git(root, "-c", "core.quotePath=false", "show", "-z", "--name-only", "--format=",
                     sha, "--", ".", ":(exclude)frontenddev/docs", ":(exclude).claude")
           files += [f for f in out.split("\0") if f.strip()]
       return files
   ```

   Helper `git()` menyusun `["git", "-C", root, *args]`, sehingga `-c` tetap berada sebelum subperintah. Output `-z --format=` diawali langsung oleh nama berkas tanpa baris kosong (diperiksa dengan `od -c`).
2. **`validate_report.py:38`, `:106-112`:** ganti `BULLET` dengan parser yang mengambil kurung seimbang **terakhir** di ujung baris (diuji di `fe_fix.py`):

   ```python
   def parse_bullet(line: str) -> Optional[Tuple[str, str]]:
       """`- <teks> (<anotasi>)` → (teks, anotasi); anotasi = kurung seimbang TERAKHIR di ujung baris."""
       s = line.rstrip()
       if not s.startswith("- ") or not s.endswith(")"):
           return None
       depth = 0
       for i in range(len(s) - 1, 1, -1):
           if s[i] == ")":
               depth += 1
           elif s[i] == "(":
               depth -= 1
               if depth == 0:
                   text, inner = s[2:i].rstrip(), s[i + 1:-1].strip()
                   return (text, inner) if text and inner else None
       return None
   ```

   Hasil (aktual): `- Tambah tab (app/(tabs)/index.tsx)` → `('Tambah tab', 'app/(tabs)/index.tsx')`; `- Tab (baru) (app/(tabs)/x.tsx)` → `('Tab (baru)', 'app/(tabs)/x.tsx')`; `- Tanpa anotasi` → `None`.
3. Opsional, risiko rendah: `ls-tree --name-only` di `brief_set_drift` (baris 552) dan `status --porcelain` di `dirty_lines` (baris 229) juga diberi `-c core.quotePath=false -z`. Nama brief dan taskdir memang ASCII, jadi dampaknya hari ini nol.

### Test yang ditambahkan

| Test | Input | Assert |
|---|---|---|
| `tests/frontenddev/test_precondition_lib.py::test_chain_files_unicode` | commit `feat(promo): …` menyentuh `src/i18n/café.tsx` | `"src/i18n/café.tsx" in chain_files(...)` |
| `…::test_chain_files_berspasi` | `src/components/Kartu Promo.tsx` | path apa adanya |
| `tests/frontenddev/test_validate_report.py::test_bullet_route_group_expo` | `- Tambah tab (app/(tabs)/index.tsx)` | check 4 tidak memuat "butir tanpa" |
| `…::test_bullet_route_group_sveltekit` | `- Rute (src/routes/(app)/+page.svelte)` | idem |
| `…::test_direktori_induk_mencakup_unicode` | `- Terjemahan (src/i18n)` | check 4 PASS (bersama butir `app`) |
| `…::test_parse_bullet` (parametrik) | 6 baris di atas | sesuai hasil aktual |

### Selesai bila

Pada reproduksi, ketiga panggilan `report` → check 4 PASS, dan `chain_files()` mengembalikan `['app/(tabs)/index.tsx', 'src/i18n/café.tsx']`.

### Risiko & catatan

Path yang mengandung koma masih pecah di `split(",")` (validate_report baris 112). Kasus ini tidak lazim, dan tidak diubah di sini.

---

## L5.9 [Rendah] Parsing tidak sadar code fence dan BOM

- [ ] Selesai

**Plugin:** backenddev, frontenddev, analyst · **Estimasi:** 1 hari · **Bergantung pada:** L5.1 (`doc_status`), bagian A (`count_h1`, `iter_outside_fences`) · **Memblokir:** L2.2/L2.3 (mengubah fungsi architect yang sama)

### Konteks

Tiga plugin punya pembaca heading/field yang tidak mengenal blok kode berpagar maupun BOM (U+FEFF, ditulis sebagian editor Windows). Blok kode lazim di brief (snippet YAML/JSON), di TASK.md (perintah reproduksi), dan di REVIEW.md (log build). Semuanya berisi baris `status: …` atau `# komentar`.

**Koreksi terhadap ISSUES.md:**

- (a) `status: DONE` di blok kode hanya terhitung bila status frontmatter tidak cocok `[A-Z_]+` (berkutip `"READY"`, huruf kecil, atau hilang) dan blok kodenya tidak terindentasi. Frontmatter `status: READY` normal tetap menang.
- (b) BOM → "ditemukan: 0" hanya bila H1 ada di baris pertama TASK.md (tanpa frontmatter).
- (c) analyst: `ticket.py state` → RUSAK "status tidak sah (elicitation -, status -)". "requester kosong" datang dari `validate_doc.py` bersama 5 galat lain.
- Tambahan: `frontenddev/task/scripts/validate_task.py:102` punya masalah H1-di-code-fence yang sama.

### Lokasi & kode saat ini

backenddev, `architect/scripts/check_preconditions.py:229-233` (identik di `report/scripts/check_preconditions.py:246-249`):

```python
229:        for bf in brief_files:
230:            try:
231:                content = bf.read_text(encoding="utf-8")
232:                match = re.search(r"^status:\s*([A-Z_]+)", content, re.MULTILINE)
233:                st = match.group(1) if match else "UNKNOWN"
```

`architect:290` → `"summary": f"{len(brief_files)} brief terdeteksi ({ready_count} READY, {done_count} DONE)"` (BLOCKED/OTHER tidak disebut).

`report/scripts/check_preconditions.py:161`:

```python
161:            h1_count = len(re.findall(r"^#\s+[^\n]+", content, re.MULTILINE))
```

frontenddev, `architect/scripts/validate_review.py:112-115` (juga `task/scripts/validate_task.py:102`):

```python
112:        lines = self.body.splitlines()
113:        h1 = [l for l in lines if l.startswith("# ")]
114:        if len(h1) != 1 or not h1[0].startswith("# Review Findings — "):
115:            p.append("wajib tepat satu H1 `# Review Findings — <slug>`")
```

`_common/precondition_lib.py:265` (dipakai validate_review, validate_doc, taskdir_state, dan lainnya):

```python
265:     if not text.startswith("---"):
```

analyst, `skills/_common/analyst_lib.py:106`:

```python
106:     if not text.startswith("---"):
107:         return {}, text
```

### Reproduksi

````bash
#!/usr/bin/env bash
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
P=$REPO/src/plugins
tmp=$(mktemp -d); cd "$tmp" && git init -q && git config user.email t@t && git config user.name t
BOM=$'\xef\xbb\xbf'
# ---------- backenddev
TD=backenddev/docs/2601011200-refund; mkdir -p $TD .claude/profile src
echo '{"stack":"go","architecture":"layered","root_namespace":"x","source_root":"src","commit_convention":"c","base_branch":"main","branch_convention":"feat/<slug>"}' > .claude/profile/index.json
brief() { printf -- '---\ntitle: b%s\nstatus: %s\n---\n# Brief\n\n## Steps\n1. Contoh isi berkas state:\n\n```yaml\nstatus: DONE\n```\n' "$1" "$2" > $TD/brief-$1-x.md; }
git add -A && git commit -qm init
echo "== BE architect check 3: status frontmatter berkutip/huruf kecil, blok kode memuat 'status: DONE'"
brief 01 '"READY"'; brief 02 ready
python3 $P/backenddev/skills/architect/scripts/check_preconditions.py --root "$tmp" --taskdir $TD | grep '^\[3\]'
echo "== BE report check 4: kondisi yang sama"
printf -- '---\nstatus: ACTIVE\n---\n# T\n\n## Success Criteria\n- SC-1\n' > $TD/TASK.md; touch $TD/REVIEW.md
python3 $P/backenddev/skills/report/scripts/check_preconditions.py --root "$tmp" --taskdir $TD | grep '^\[4\]'
echo "== BE architect check 3: 2 READY + 1 BLOCKED -> PASS tanpa menyebut BLOCKED"
brief 01 READY; brief 02 READY; brief 03 BLOCKED
python3 $P/backenddev/skills/architect/scripts/check_preconditions.py --root "$tmp" --taskdir $TD | grep '^\[3\]'
echo "== BE report check 2: '# jalankan migrasi' di code fence TASK.md"
printf -- '---\nstatus: ACTIVE\n---\n# Refund\n\n## Description\n```bash\n# jalankan migrasi\nmake migrate\n```\n\n## Success Criteria\n- SC-1\n' > $TD/TASK.md
python3 $P/backenddev/skills/report/scripts/check_preconditions.py --root "$tmp" --taskdir $TD | grep '^\[2\]'
echo "== BE report check 2: TASK.md ber-BOM, H1 di baris pertama (tanpa frontmatter)"
printf -- '%s# Refund\n\n## Success Criteria\n- SC-1\n' "$BOM" > $TD/TASK.md
python3 $P/backenddev/skills/report/scripts/check_preconditions.py --root "$tmp" --taskdir $TD | grep '^\[2\]'
echo "== BE report check 2: TASK.md ber-BOM dengan frontmatter (kontrol)"
printf -- '%s---\nstatus: ACTIVE\n---\n# Refund\n\n## Success Criteria\n- SC-1\n' "$BOM" > $TD/TASK.md
python3 $P/backenddev/skills/report/scripts/check_preconditions.py --root "$tmp" --taskdir $TD | grep '^\[2\]'
# ---------- frontenddev
FT=frontenddev/docs/2601011200-promo; mkdir -p $FT
printf -- '---\nstatus: ACTIVE\nlane: HOTFIX_MINOR\nsections: -\ncreated: 2026-01-01\n---\n# Promo\n\n## Success Criteria\n- [ ] **SC-1**: x — verifikasi: test\n\n## Chain\n' > $FT/TASK.md
git add -A && git commit -qm "docs(promo): root task"
review() { printf -- '%s---\nartifact: REVIEW\nverdict: PASS\np1: 0\np2: 0\np3: 0\nbase: %s\nreviewed_at: 2026-01-02\n---\n# Review Findings — promo\n\n## Summary\nok\n%s\n' "$1" "$(git rev-parse --short HEAD)" "$2" > $FT/REVIEW.md; }
echo "== FE validate_review: pelanggaran H1 tanpa vs dengan blok kode ber-'# komentar' (seksi lain sengaja dipangkas)"
review "" ""
echo -n "tanpa blok kode : "; python3 $P/frontenddev/skills/architect/scripts/validate_review.py --root "$tmp" --taskdir $FT | grep -c 'wajib tepat satu H1'
review "" $'\n```bash\n# log build\nnpm run build\n```'
echo -n "dengan blok kode: "; python3 $P/frontenddev/skills/architect/scripts/validate_review.py --root "$tmp" --taskdir $FT | grep 'wajib tepat satu H1' || echo 0
echo "== FE validate_review: REVIEW.md ber-BOM"
review "$BOM" ""
python3 $P/frontenddev/skills/architect/scripts/validate_review.py --root "$tmp" --taskdir $FT | grep -A1 '^\[S\]'
echo "== FE taskdir_state: TASK.md ber-BOM"
printf '%s' "$BOM" | cat - $FT/TASK.md > t && mv t $FT/TASK.md && git commit -qam "docs(promo): bom"
python3 $P/frontenddev/skills/lead/scripts/taskdir_state.py --root "$tmp" --taskdir $FT
echo "== FE validate_task: blok kode ber-'# komentar' di ## Description"
printf -- '---\nstatus: ACTIVE\nlane: HOTFIX_MINOR\nsections: -\ncreated: 2026-01-01\n---\n# Promo\n\n## Description\n```bash\n# reproduksi\nnpm run dev\n```\n\n## Success Criteria\n- [ ] **SC-1**: x — verifikasi: test\n\n## Out of Scope\n- a — b\n\n## Chain\n' > $FT/TASK.md
python3 $P/frontenddev/skills/task/scripts/validate_task.py --root "$tmp" --taskdir $FT | grep '^\[1\]'
# ---------- analyst
AT=analyst/tickets/2601011200-promo; mkdir -p $AT
printf -- '%s---\nstatus: DRAFT\nelicitation: OPEN\ntype: FEATURE\npriority: -\nslug: promo\nrequester: Rina\ncreated: 2026-01-01\n---\n# Promo\n\n## Catatan Elisitasi\n' "$BOM" > $AT/TICKET.md
echo "== analyst ticket.py state: TICKET.md ber-BOM"
python3 $P/analyst/skills/_common/ticket.py --root "$tmp" state --all
echo "== analyst validate_doc --kind elicit: TICKET.md ber-BOM"
python3 $P/analyst/skills/_common/validate_doc.py --root "$tmp" --kind elicit --ticketdir $AT | head -3
rm -rf "$tmp"
````

Output aktual:

```
== BE architect check 3: status frontmatter berkutip/huruf kecil, blok kode memuat 'status: DONE'
[3] Brief Set & Readiness            : PASS (Seluruh 2 brief DONE, siap masuk gerbang penutup REVIEW.md)
== BE report check 4: kondisi yang sama
[4] All Briefs Status DONE           : PASS (Seluruh 2 brief berstatus DONE)
== BE architect check 3: 2 READY + 1 BLOCKED -> PASS tanpa menyebut BLOCKED
[3] Brief Set & Readiness            : PASS (3 brief terdeteksi (2 READY, 0 DONE))
== BE report check 2: '# jalankan migrasi' di code fence TASK.md
[2] Root TASK.md Contract            : FAIL (TASK.md harus memuat tepat satu judul H1 (ditemukan: 2))
== BE report check 2: TASK.md ber-BOM, H1 di baris pertama (tanpa frontmatter)
[2] Root TASK.md Contract            : FAIL (TASK.md harus memuat tepat satu judul H1 (ditemukan: 0))
== BE report check 2: TASK.md ber-BOM dengan frontmatter (kontrol)
[2] Root TASK.md Contract            : PASS (TASK.md valid (memuat 1 H1 dan Success Criteria))
== FE validate_review: pelanggaran H1 tanpa vs dengan blok kode ber-'# komentar' (seksi lain sengaja dipangkas)
tanpa blok kode : 0
dengan blok kode:       - wajib tepat satu H1 `# Review Findings — <slug>`
== FE validate_review: REVIEW.md ber-BOM
[S] Frontmatter                    : FAIL (1 pelanggaran)
      - frontmatter tidak dibuka dengan `---`
== FE taskdir_state: TASK.md ber-BOM
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2601011200-promo [-] RUSAK → laporkan ke user (lane `(kosong)` di luar ('FULL_PIPELINE', 'FAST_FORWARD', 'REFACTOR_ARCH', 'HOTFIX_MINOR'))
== FE validate_task: blok kode ber-'# komentar' di ## Description
[1] Struktur & frontmatter           : FAIL (2 H1, wajib tepat satu)
== analyst ticket.py state: TICKET.md ber-BOM
TICKET STATE: 1 ticketdir
- analyst/tickets/2601011200-promo · RUSAK · - · Promo
    → status tidak sah (elicitation -, status -)
== analyst validate_doc --kind elicit: TICKET.md ber-BOM
CHECK: validate TICKET.md (elicit) [FAIL] (2/8 passed)
[1] Frontmatter                    : FAIL (status `` bukan DRAFT|READY; elicitation `` bukan OPEN|CLOSED; type `` bukan FEATURE|IMPROVEMENT|BUG; slug `` ≠ slug ticketdir `promo`; created bukan YYYY-MM-DD; requester kosong)
    * Tindakan: Ikuti bagian 1 elicit-template.md.
```

### Dampak

- **backenddev:** brief READY dengan status berkutip terbaca DONE. architect melompati eksekusi, dan report menerbitkan REPORT untuk kode yang belum ditulis. Ini lolos palsu yang paling berbahaya di item ini. Dua baris itu juga menunjukkan bahwa `validate_briefs.py` membaca brief yang sama sebagai READY, karena ia membuka kutip. PASS yang tidak menyebut BLOCKED menyembunyikan brief yang macet (bahan L2.2).
- **frontenddev:** REVIEW.md yang menempelkan log build ber-`#` gagal struktur. BOM dari editor Windows membuat taskdir divonis RUSAK dan REVIEW divonis "frontmatter tidak dibuka dengan `---`", padahal pagar itu ada.
- **analyst:** tiket ber-BOM divonis RUSAK dengan pesan yang menunjuk field, bukan encoding.

### Rencana perbaikan

**backenddev**

1. architect `_check_3_brief_readiness` (228–243) dan report `_check_4_all_briefs_done` (244–252):

   ```python
   st, why = doc_status(bf, ("READY", "DONE", "BLOCKED"))
   st = st or "UNKNOWN"          # `why` dikumpulkan untuk detail pesan
   ```

2. Ringkasan architect (baris 290) menjadi `f"{n} brief terdeteksi ({ready} READY, {done} DONE, {blocked} BLOCKED, {other} tak terbaca)"`. Bila `other > 0`, sertakan nama berkas dan `why` pertama. Aturan PASS/FAIL tidak diubah; itu wilayah L2.2.
3. report check 2: baris 161 → `h1_count = count_h1(content)`. Baris 171 → `any(l.strip() == "## Success Criteria" for _, l in iter_outside_fences(content))`.
4. `scaffold_brief.py:96`, `validate_briefs.py:249`: `_read` → `read_text` (BOM/CRLF). `validate_briefs.py:508-515` → `split_frontmatter` (L5.5 B.2).

**frontenddev**

5. `_common/precondition_lib.py:265` (`split_frontmatter`) dan `:329` (`set_frontmatter_field`): tambah `text = text.lstrip(chr(0xFEFF))` di awal. `set_frontmatter_field` mengembalikan BOM di depan bila semula ada, supaya berkas yang disunting tidak berubah encoding. Perbaikan ini menutup kasus validate_review BOM, taskdir_state, validate_doc, dan setiap `read_status`.
6. Pindahkan `outside_fences` dari `validate_doc.py:102-110` ke `precondition_lib.py`, dan buat sadar panjang pagar (``` vs ````) seperti `iter_outside_fences` di bagian A. Pakai di `validate_review.py:112-116` (`lines = outside_fences(self.body.splitlines())`), di `validate_task.py:102,105` (H1/H2), dan di `validate_report.py:55-64,84-85` (`_sections`, H1).

**analyst**

7. `skills/_common/analyst_lib.py:106`: `text = text.lstrip(chr(0xFEFF))` sebelum `startswith("---")`. `set_frontmatter_field` (baris 145) mempertahankan BOM dengan cara yang sama seperti butir 5.

### Test yang ditambahkan

| Test | Input | Assert |
|---|---|---|
| `tests/backenddev/test_architect_preconditions.py::test_status_berkutip_tidak_dibaca_dari_code_fence` | 2 brief `status: "READY"` + blok kode `status: DONE` | check 3 PASS "2 READY" (bukan "DONE") |
| `…::test_ringkasan_menyebut_blocked` | 2 READY + 1 BLOCKED | `summary` memuat `1 BLOCKED` |
| `…::test_status_huruf_kecil_tak_terbaca` | `status: ready` | `summary` memuat "tak terbaca" + nama berkas |
| `tests/backenddev/test_report_preconditions.py::test_brief_berkutip_bukan_done` | sama dengan kasus pertama | check 4 FAIL |
| `…::test_h1_di_code_fence_diabaikan` | TASK dengan `# jalankan migrasi` di blok bash | check 2 PASS |
| `…::test_task_bom_tanpa_frontmatter` | BOM + `# Refund` | check 2 PASS |
| `tests/backenddev/test_common_frontmatter.py::test_count_h1_pagar_bersarang` | ```` ````md ```` berisi ```` ``` ```` + `# x` | `1` |
| `tests/frontenddev/test_validate_review.py::test_log_build_ber_hash_di_code_fence` | fixture reproduksi | tanpa pelanggaran H1 |
| `…::test_review_bom` | REVIEW ber-BOM | tanpa FAIL "frontmatter tidak dibuka" |
| `tests/frontenddev/test_taskdir_state.py::test_task_bom_bukan_rusak` | TASK ber-BOM ter-commit | state bukan RUSAK |
| `tests/frontenddev/test_validate_task.py::test_h1_di_code_fence_diabaikan` | fixture reproduksi | check 1 tanpa "2 H1" |
| `tests/frontenddev/test_precondition_lib.py::test_set_frontmatter_field_mempertahankan_bom` | BOM + set `status` | byte awal tetap `EF BB BF` |
| `tests/analyst/test_ticket.py::test_state_ticket_ber_bom` (sudah ada di 06, cabut `xfail`) | TICKET ber-BOM | state ELISITASI |
| `tests/analyst/test_validate_doc.py::test_elicit_bom_frontmatter_terbaca` | TICKET ber-BOM | check 1 PASS |

### Selesai bila

Reproduksi dijalankan ulang menghasilkan:

- architect check 3 kasus pertama tidak lagi "Seluruh 2 brief DONE";
- report check 4 FAIL;
- ringkasan architect menyebut `1 BLOCKED`;
- report check 2 PASS di ketiga kasus;
- validate_review tanpa pelanggaran H1 dan tanpa FAIL frontmatter;
- taskdir_state tidak RUSAK;
- validate_task tanpa "2 H1";
- ticket state `ELISITASI` dan validate_doc check 1 PASS.

### Risiko & catatan

- **Membuang BOM saat membaca** tidak mengubah berkas di disk. Menyunting frontmatter (butir 5 dan 7) sengaja mempertahankan BOM supaya diff approval tidak menyentuh baris pertama. Ini selaras dengan C3 (menjaga gaya line ending).
- Brief lama dengan `status: ready` (huruf kecil) kini dilaporkan "tak terbaca", padahal sebelumnya jatuh diam-diam ke OTHER atau terbaca dari blok kode. Keputusan 2 berlaku juga di sini.

---

## Keputusan yang dibutuhkan user

1. **Kunci wajib `index.json`:** ketujuh kunci ditagih di semua skrip prasyarat backenddev (disarankan; document-api dikecualikan bila `--stack` diberikan), atau tiap skrip tetap menagih subset yang dipakainya.
2. **Perbandingan status:** persis huruf besar (`APPROVED`, `READY`; disarankan, fail-closed) atau tak peka huruf.
3. **Kunci frontmatter ganda:** FAIL dengan pesan (disarankan) atau ambil nilai terakhir seperti YAML.
4. **Placeholder di dalam inline code (L5.6):** hanya slot berkosakata (`<slug>`, `<NN>`) yang ditolak (disarankan), atau semua `<…>` di dalam backtick diabaikan seperti `validate_task` hari ini.
5. **`qa manual:` (L5.7):** tak peka huruf di keempat pembaca (disarankan), atau ejaan kanonik `QA manual:` ditegakkan ketat sejak `validate_task`.
