#!/usr/bin/env python3
"""Helper bersama skrip plugin `product`.

Berisi **hanya** primitif yang dipakai lebih dari satu skrip: letak charterdir, deteksi ruang kerja, guard
konteks minimum, parser frontmatter, pemecah seksi, sidik konten, commit git, dan format laporan baku.
Check itu sendiri tetap tinggal di skripnya masing-masing.

Plugin ini tidak menuntut repo git: charterdir berakar di root worktree git bila ada, selain itu di cwd. Git
hanya dipakai untuk commit opsional; berkas yang diabaikan `.gitignore` tetap di disk tanpa commit.

Zero external dependencies (Python Standard Library only).
"""

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PRODUCT_DIR = "product"
CHARTER_FILE = "CHARTER.md"
REVIEW_FILE = "review.md"  # blok `## Charter Review` terakhir, ditulis hanya oleh `charter.py review --report`
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CHARTERDIR_RE = re.compile(r"^product/[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_MAX = 40

# Mode inisiasi. `NEW_PRODUCT` berjalan di folder kosong; dua lainnya di codebase.
MODES = ("NEW_PRODUCT", "NEW_FEATURE", "IMPROVEMENT")
CODE_MODES = ("NEW_FEATURE", "IMPROVEMENT")
# Status tersimpan di frontmatter; keadaan `REVIEW` dan `DRIFT` diturunkan `charter.py state`.
STATUSES = ("ELICITATION", "DRAFT", "APPROVED", "CANCELLED")

PLACEHOLDER = re.compile(r"\bTBD\b|\bTODO\b|diisi nanti|<[A-Za-z][^<>\n]*>")
UNANSWERED = "_(belum terjawab)_"
ELICIT_H2 = "Catatan Elisitasi"
ELICIT_H3 = ("Konteks Awal", "Permintaan Asli", "Fakta", "Log Tanya-Jawab", "Pertanyaan Terbuka")
# Enam pilar: heading kartu dan pilar `####` catatan elisitasi memakai nama yang sama.
PILLARS = ("Purpose", "Actors", "Business Process", "Business Rules", "Success Criteria", "Scope")

# ── Guard konteks minimum ─────────────────────────────────────────────────────

# Tiga butir wajib per mode, urut sesuai flag `--untuk`, `--masalah`, `--lingkup`. Labelnya ditulis apa adanya
# ke `### Konteks Awal`; rumah kanonik penjelasannya `skills/init/references/konteks-minimum.md`.
CONTEXT_KEYS = ("untuk", "masalah", "lingkup")
CONTEXT_LABELS = {
    "NEW_PRODUCT": ("Untuk siapa", "Masalah utama", "Domain"),
    "NEW_FEATURE": ("Pengguna", "Yang belum bisa dilakukan", "Area"),
    "IMPROVEMENT": ("Yang terdampak", "Yang salah atau kurang", "Fitur"),
}
CONTEXT_MIN = 3
# Jawaban yang tidak mempersempit apa pun. Dicocokkan utuh (huruf kecil, tanpa tanda baca ujung), bukan sebagai
# potongan kata: "semua cabang toko" tetap sah, "semua" saja tidak.
VAGUE = {
    "-", "--", "?", "tbd", "todo", "n/a", "na", "nanti", "belum tahu", "belum tau", "tidak tahu", "tidak tau",
    "gak tahu", "ga tau", "entah", "terserah", "bebas", "apa saja", "apa aja", "siapa saja", "siapa aja",
    "semua", "semua orang", "semuanya", "umum", "masyarakat umum", "orang", "orang-orang", "pokoknya",
    "macam-macam", "banyak", "lainnya", "lain-lain", "dll", "everyone", "anyone", "anything", "general",
    "aplikasi", "sistem", "fitur", "masalah",
}
# Sebutan orang tanpa segmen hanya terlalu umum untuk produk baru: di codebase, "pelanggan" bisa jadi peran
# yang memang sudah ada di aplikasi, dan scout yang memastikannya.
VAGUE_PERSON = {"pengguna", "user", "users", "customer", "customers", "pelanggan", "konsumen", "klien",
                "client", "masyarakat"}


def context_problems(mode: str, values: Dict[str, str]) -> List[str]:
    """Butir konteks minimum yang kosong, terlalu pendek, atau terlalu umum; `[]` = lolos.

    Skrip hanya menjamin ketiga butir terisi sesuatu yang mempersempit; mutunya dinilai `charter-reviewer`
    terhadap Purpose dan Actors.
    """
    labels = CONTEXT_LABELS.get(mode)
    if not labels:
        return [f"mode `{mode}` bukan {'|'.join(MODES)}"]
    problems = []
    for key, label in zip(CONTEXT_KEYS, labels):
        raw = " ".join(str(values.get(key, "")).split())
        norm = raw.lower().strip(" .,!?;:")
        if not raw:
            problems.append(f"{label} (--{key}) kosong")
        elif len(norm) < CONTEXT_MIN:
            problems.append(f"{label} (--{key}) `{raw}` terlalu pendek")
        elif norm in VAGUE or (mode == "NEW_PRODUCT" and key == "untuk" and norm in VAGUE_PERSON):
            problems.append(f"{label} (--{key}) `{raw}` terlalu umum")
        elif PLACEHOLDER.search(raw):
            problems.append(f"{label} (--{key}) `{raw}` masih placeholder")
    return problems


# ── Root, ruang kerja & git ───────────────────────────────────────────────────

def find_root() -> Path:
    """Akar worktree git, atau cwd bila bukan repo git."""
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      stderr=subprocess.DEVNULL, universal_newlines=True).strip()
        if out:
            return Path(out)
    except Exception:
        pass
    return Path.cwd()


SOURCE_EXT = {".go", ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".svelte", ".vue", ".java", ".kt",
              ".kts", ".rb", ".php", ".rs", ".cs", ".swift", ".dart", ".scala", ".c", ".cc", ".cpp", ".h", ".m",
              ".ex", ".exs", ".erl", ".clj", ".fs", ".sql"}
MANIFESTS = ("package.json", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
             "composer.json", "pyproject.toml", "requirements.txt", "Gemfile", "pubspec.yaml", "mix.exs",
             "setup.py", "deno.json")
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "target", ".venv", "venv", "__pycache__",
             ".next", ".svelte-kit", ".nuxt", ".idea", ".vscode", ".claude", ".cache", "coverage"}
WALK_DEPTH = 6
WALK_LIMIT = 20000


def detect_workspace(root: Path) -> Dict[str, Any]:
    """Ruang kerja `EMPTY` (tanpa kode) atau `CODEBASE`, beserta buktinya.

    Kode = berkas manifest di root, atau minimal satu berkas sumber dalam kedalaman `WALK_DEPTH`. Pemindaian
    berhenti di bukti pertama dan dibatasi `WALK_LIMIT` entri, supaya folder besar tidak menahan gerbang.
    """
    for name in MANIFESTS:
        if (root / name).is_file():
            return {"workspace": "CODEBASE", "evidence": name}
    seen = 0
    base_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(str(root)):
        depth = len(Path(dirpath).parts) - base_depth
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        if depth >= WALK_DEPTH:
            dirnames[:] = []
        for f in sorted(filenames):
            seen += 1
            if Path(f).suffix.lower() in SOURCE_EXT:
                rel = Path(dirpath, f).relative_to(root).as_posix()
                return {"workspace": "CODEBASE", "evidence": rel}
        if seen > WALK_LIMIT:
            break
    return {"workspace": "EMPTY", "evidence": "-"}


def workspace_problem(root: Path) -> str:
    """Ruang kerja yang tidak boleh menampung charter (home atau root filesystem); string kosong = sah."""
    resolved = root.resolve()
    if resolved == Path(resolved.anchor):
        return f"ruang kerja `{resolved}` adalah root filesystem"
    try:
        if resolved == Path.home().resolve():
            return f"ruang kerja `{resolved}` adalah direktori home"
    except (RuntimeError, OSError):
        pass
    return ""


def mode_problem(mode: str, workspace: str, confirmed: bool) -> str:
    """Kecocokan mode dengan ruang kerja; string kosong = sah.

    Mode codebase di folder tanpa kode tidak punya apa pun untuk dikembangkan. `NEW_PRODUCT` di codebase sah
    hanya atas konfirmasi user (mis. repo dokumen yang kebetulan memuat skrip).
    """
    if mode in CODE_MODES and workspace == "EMPTY":
        return f"mode {mode} butuh codebase, tetapi ruang kerja tanpa kode — pakai NEW_PRODUCT, atau jalankan dari repo yang dikembangkan"
    if mode == "NEW_PRODUCT" and workspace == "CODEBASE" and not confirmed:
        return ("mode NEW_PRODUCT di codebase butuh konfirmasi user (`--confirm-workspace`) — atau pakai "
                "NEW_FEATURE/IMPROVEMENT")
    return ""


def is_git_repo(root: Path) -> bool:
    try:
        subprocess.check_output(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                                stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def ignored_paths(root: Path, paths: List[str]) -> List[str]:
    """Anggota `paths` (relatif root) yang diabaikan `.gitignore`; git gagal atau bukan repo git → `[]`."""
    if not paths:
        return []
    try:
        proc = subprocess.run(["git", "-C", str(root), "check-ignore", "--", *paths],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:           # 1 = tidak satu pun diabaikan, 128 = git gagal
        return []
    hits = set(proc.stdout.splitlines())
    return [p for p in paths if p in hits]


def tracked_files(root: Path, *paths: str) -> List[str]:
    """Berkas ter-track pada atau di bawah `paths` (relatif root); git gagal atau bukan repo git → `[]`."""
    try:
        out = subprocess.check_output(["git", "-C", str(root), "ls-files", "--", *paths],
                                      stderr=subprocess.DEVNULL, universal_newlines=True)
    except (OSError, subprocess.SubprocessError):
        return []
    return [l for l in out.splitlines() if l]


def git_mode(root: Path, rel: str) -> str:
    """Nilai `git=`: `ya` (di-commit), `tidak` (bukan repo git), atau `diabaikan` (diabaikan `.gitignore`)."""
    if not is_git_repo(root):
        return "tidak"
    return "diabaikan" if ignored_paths(root, [rel]) else "ya"


IGNORED = "diabaikan git"   # hasil `git_commit` bila seluruh path diabaikan `.gitignore`


def git_commit(root: Path, paths: List[str], message: str) -> Tuple[bool, str]:
    """Commit hanya `paths` (staging eksplisit, `--only`), tanpa menyentuh index lain.

    Isi yang sudah sama dengan HEAD bukan kegagalan: `(True, "tanpa perubahan")`, tanpa commit kosong. Path
    yang diabaikan `.gitignore` tidak di-stage; bila seluruhnya diabaikan → `(True, IGNORED)`.
    """
    ignored = ignored_paths(root, paths)
    paths = [p for p in paths if p not in ignored]
    if not paths:
        return True, IGNORED
    tracked = set(tracked_files(root, *paths))
    groups = ((["-u"], [p for p in paths if p in tracked]), ([], [p for p in paths if p not in tracked]))
    try:
        for flags, group in groups:
            if group:
                subprocess.check_output(["git", "-C", str(root), "add", *flags, "--", *group],
                                        stderr=subprocess.STDOUT, universal_newlines=True)
        if subprocess.call(["git", "-C", str(root), "diff", "--cached", "--quiet", "--", *paths],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return True, "tanpa perubahan"
        subprocess.check_output(["git", "-C", str(root), "commit", "-m", message, "--only", "--", *paths],
                                stderr=subprocess.STDOUT, universal_newlines=True)
        sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                                      universal_newlines=True).strip()
        return True, sha
    except subprocess.CalledProcessError as exc:
        step = exc.cmd[3] if len(exc.cmd) > 3 else "git"
        return False, (exc.output or f"error: git {step} gagal tanpa keluaran (exit {exc.returncode})").strip()


def git_error_line(out: str) -> str:
    """Baris galat git yang bermakna: `fatal:`/`error:` lebih dulu, lalu baris non-`hint:` pertama."""
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    for prefix in ("fatal:", "error:"):
        hit = [l for l in lines if l.startswith(prefix)]
        if hit:
            return hit[0]
    plain = [l for l in lines if not l.startswith("hint:")]
    return " ".join(plain[:2]) if plain else (lines[0] if lines else "-")


def normalize_dir(charterdir: str, root: Path) -> str:
    """Path charterdir relatif root, tanpa garis miring penutup."""
    p = Path(charterdir)
    if p.is_absolute():
        try:
            p = p.resolve().relative_to(root.resolve())
        except ValueError:
            return str(p)
    rel = p.as_posix().strip("/")
    return rel[2:] if rel.startswith("./") else rel


# ── Frontmatter & seksi ───────────────────────────────────────────────────────

BOM = chr(0xFEFF)


def split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Parse subset YAML frontmatter (skalar dan skalar berkutip) → `(data, body)`.

    Berkas tanpa pagar `---` lengkap → `({}, text)`. BOM di awal berkas dibuang lebih dulu.
    """
    text = text.lstrip(BOM)
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    head, body = text[3:end], text[end + 4:]
    data: Dict[str, Any] = {}
    for raw in head.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = _unquote(value.strip())
    return data, body.lstrip("\n")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def clean_value(value: str, limit: int = 200) -> str:
    """Nilai bebas (jawaban, alasan) → satu baris berkutip ganda, aman ditulis ke frontmatter."""
    flat = " ".join(value.replace('"', "'").split())[:limit]
    return f'"{flat}"'


def set_frontmatter_field(text: str, key: str, value: str) -> str:
    """Ganti nilai `key` di frontmatter, atau sisipkan sebelum pagar penutup; `ValueError` bila tanpa frontmatter."""
    if not text.lstrip(BOM).startswith("---"):
        raise ValueError("berkas tanpa frontmatter (tidak diawali `---`)")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("frontmatter tanpa pagar penutup `---`")
    head, rest = text[:end], text[end:]
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    if pattern.search(head):
        head = pattern.sub(lambda _: f"{key}: {value}", head, count=1)
    else:
        head = f"{head}\n{key}: {value}"
    return head + rest


def sections(body: str, level: int = 2) -> Dict[str, List[str]]:
    """Heading level `level` → baris isinya (heading level lebih dalam ikut sebagai isi)."""
    prefix = "#" * level + " "
    out: Dict[str, List[str]] = {}
    current: Optional[str] = None
    in_fence = False
    for line in body.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith(prefix):
            current = line[len(prefix):].strip()
            out[current] = []
        elif not in_fence and level > 1 and re.match(rf"^#{{1,{level - 1}}} ", line):
            current = None
        elif current is not None:
            out[current].append(line)
    return out


def h1_lines(body: str) -> List[str]:
    out, in_fence = [], False
    for line in body.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.startswith("# "):
            out.append(line)
    return out


def duplicate_headings(body: str, level: int) -> List[str]:
    """Heading level `level` yang muncul lebih dari sekali di luar pagar kode."""
    prefix = "#" * level + " "
    seen: List[str] = []
    in_fence = False
    for line in body.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.startswith(prefix):
            seen.append(line[len(prefix):].strip())
    return sorted({h for h in seen if seen.count(h) > 1})


def split_parts(body: str) -> Tuple[str, str]:
    """Body → `(kartu, catatan elisitasi)`; batasnya heading `## Catatan Elisitasi` di luar pagar kode."""
    lines = body.splitlines()
    in_fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.rstrip() == f"## {ELICIT_H2}":
            return "\n".join(lines[:i]), "\n".join(lines[i:])
    return body, ""


def meaningful(lines: List[str]) -> List[str]:
    """Baris berisi, tanpa komentar HTML."""
    return [l for l in lines if l.strip() and not l.strip().startswith("<!--")]


def notes_h3(text: str) -> Dict[str, List[str]]:
    """H3 di bawah `## Catatan Elisitasi`."""
    _, body = split_frontmatter(text)
    return sections("\n".join(sections(split_parts(body)[1], 2).get(ELICIT_H2, [])), 3)


LOG_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|(.+)\|(.+)\|(.+)\|\s*$")


def log_rows(text: str) -> List[Tuple[str, ...]]:
    """Baris data `### Log Tanya-Jawab` → `(nomor, tanggal, pertanyaan, jawaban, sumber)`, sudah di-strip."""
    log = notes_h3(text).get("Log Tanya-Jawab", [])
    return [tuple(g.strip() for g in m.groups()) for m in (LOG_ROW.match(l.strip()) for l in log) if m]


def append_log_row(text: str, date: str, question: str, answer: str, source: str) -> str:
    """Tambahkan satu baris di akhir tabel `### Log Tanya-Jawab`; `ValueError` bila tabelnya tidak ditemukan."""
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if l.rstrip() == "### Log Tanya-Jawab"), None)
    if start is None:
        raise ValueError("`### Log Tanya-Jawab` tidak ditemukan")
    last = None
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("#"):
            break
        if lines[i].strip().startswith("|"):
            last = i
    if last is None:
        raise ValueError("tabel `### Log Tanya-Jawab` tanpa header")
    n = len(log_rows(text)) + 1
    cell = lambda v: " ".join(v.replace("|", "/").split())  # noqa: E731
    lines.insert(last + 1, f"| {n} | {date} | {cell(question)} | {cell(answer)} | {cell(source)} |")
    return "\n".join(lines)


# ── Sidik ─────────────────────────────────────────────────────────────────────

# Field frontmatter yang ikut menentukan isi: mengubahnya sesudah review atau persetujuan sama dengan mengubah
# body. Field pembukuan (`status`, `review*`, `revision*`, `approved*`, `*_hash`) sengaja di luar sidik.
CONTENT_FIELDS = ("mode",)


def content_hash(text: str, part: str = "all") -> str:
    """Sidik 12 hex atas bagian body (`card`, `elicit`, atau `all`) + field isinya; spasi ujung baris dinormalkan.

    Sidik `card` dan `elicit` dipasangkan sebagai sidik review; `all` dimateraikan `approve`.
    """
    fm, body = split_frontmatter(text)
    if part != "all":
        body = split_parts(body)[0 if part == "card" else 1]
    norm = "\n".join(l.rstrip() for l in body.strip().splitlines())
    fields = "\n".join(f"{k}={fm.get(k, '')}" for k in CONTENT_FIELDS)
    return hashlib.sha256(f"{fields}\n{norm}".encode("utf-8")).hexdigest()[:12]


def _digest(lines: List[str]) -> str:
    return hashlib.sha256("\n".join(l.rstrip() for l in meaningful(lines)).encode("utf-8")).hexdigest()[:12]


def request_digest(text: str) -> str:
    """Sidik `### Permintaan Asli` — dimateraikan `charter.py new` sebagai `request_hash`."""
    return _digest(notes_h3(text).get("Permintaan Asli", []))


def context_digest(text: str) -> str:
    """Sidik `### Konteks Awal` — dimateraikan `charter.py new` sebagai `context_hash`."""
    return _digest(notes_h3(text).get("Konteks Awal", []))


def context_lines(mode: str, values: Dict[str, str]) -> List[str]:
    return [f"- **{label}**: {' '.join(str(values.get(key, '')).split())}"
            for key, label in zip(CONTEXT_KEYS, CONTEXT_LABELS[mode])]


def charter_skeleton(mode: str, slug: str, requester: str, created: str, title: str, request: str,
                     context: Dict[str, str]) -> str:
    """`CHARTER.md` awal persis bagian 1 `skills/discover/templates/charter-skeleton.md`, beserta kedua sidiknya.

    `tests/product/test_charter.py` menagih keduanya sama.
    """
    quote = "\n".join(f"> {l.rstrip()}" if l.strip() else ">" for l in request.strip("\n").splitlines())
    pillars = "\n\n".join(f"#### {p}\n{UNANSWERED}" for p in PILLARS)
    konteks = "\n".join(context_lines(mode, context))
    text = (f"---\nstatus: ELICITATION\nmode: {mode}\nslug: {slug}\nrequester: {clean_value(requester)}\n"
            f"created: {created}\nrevision: 0\nreview: -\nreview_round: 0\ncontext_hash: -\nrequest_hash: -\n"
            f"elicit_hash: -\nelicit_log: 0\n---\n\n# {title}\n\n"
            f"## {ELICIT_H2}\n\n### Konteks Awal\n\n{konteks}\n\n### Permintaan Asli\n\n{quote}\n\n"
            f"### Fakta\n\n{pillars}\n\n"
            "### Log Tanya-Jawab\n\n| # | Tanggal | Pertanyaan | Jawaban | Sumber |\n|---|---|---|---|---|\n\n"
            "### Pertanyaan Terbuka\n\n- Tidak ada.\n")
    text = set_frontmatter_field(text, "context_hash", context_digest(text))
    return set_frontmatter_field(text, "request_hash", request_digest(text))


# ── Laporan ───────────────────────────────────────────────────────────────────

def format_report(title: str, results: List[Dict[str, Any]],
                  resolved: Optional[Dict[str, str]] = None) -> str:
    """Keluaran teks baku; `resolved` menjadi baris `Terselesaikan:`."""
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    label = "FAIL" if failed else ("PASS (WARN)" if warned else "PASS")
    lines = [f"CHECK: {title} [{label}] ({passed}/{len(results)} passed"
             + (f", {warned} warn)" if warned else ")")]
    for r in results:
        lines.append(f"[{r['id']}] {r['name']:<30} : {r['status']} ({r['summary']})")
        if r["status"] in ("FAIL", "WARN") and r.get("action"):
            lines.append(f"    * Tindakan: {r['action']}")
    if resolved:
        lines.append("Terselesaikan: " + "; ".join(f"{k}={v}" for k, v in resolved.items()))
    return "\n".join(lines)


def report_json(results: List[Dict[str, Any]], **extra: Any) -> str:
    payload: Dict[str, Any] = {
        "status": "FAIL" if any(r["status"] == "FAIL" for r in results) else "PASS",
        "passed_count": sum(1 for r in results if r["status"] == "PASS"),
        "total_count": len(results),
    }
    payload.update(extra)
    payload["checks"] = results
    return json.dumps(payload, indent=2, ensure_ascii=False)


class Checker:
    """Pengumpul hasil check bernomor; subclass mengisi `run_all`."""

    def __init__(self) -> None:
        self.results: List[Dict[str, Any]] = []

    def add(self, cid: int, name: str, ok: Any, summary: str, action: str = "",
            warn: bool = False) -> None:
        status = "PASS" if ok else ("WARN" if warn else "FAIL")
        self.results.append({"id": cid, "name": name, "status": status,
                             "summary": summary, "action": "" if ok else action})

    @property
    def ok(self) -> bool:
        return not any(r["status"] == "FAIL" for r in self.results)
