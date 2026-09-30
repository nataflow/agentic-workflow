#!/usr/bin/env python3
"""Helper bersama skrip plugin `analyst`.

Berisi **hanya** primitif yang dipakai lebih dari satu skrip: letak ticketdir,
parser frontmatter, pemecah seksi, sidik konten, pemindai kebocoran teknis, dan
format laporan baku. Check itu sendiri tetap tinggal di skripnya masing-masing.

Plugin ini tidak menuntut repo git: ticketdir berakar di root worktree git bila
ada, selain itu di cwd. Git hanya dipakai untuk commit opsional; berkas yang
diabaikan `.gitignore` tetap di disk tanpa commit.

Zero external dependencies (Python Standard Library only).
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))   # pustaka bersama sebelah, apa pun pemuatnya
import nataflow_sync as ns  # noqa: E402

TICKETS_DIR = "analyst/tickets"
SYNC_CONFIG = "analyst/nataflow.json"  # config sinkron lama (14 N1); yang bersama `.claude/nataflow.json` (15 A1)
# Repo bersinkron nataflow: `new` menulis berkas ini (`*` ikut mengabaikan dirinya), jadi ticketdir tetap di disk
# tanpa pernah di-commit dan tanpa mengotori working tree yang ditagih gerbang engineer.
TICKETS_IGNORE = f"{TICKETS_DIR}/.gitignore"
TICKETS_IGNORE_TEXT = (
    "# Ditulis analyst `ticket.py new` karena repo ini menyinkronkan tiket ke nataflow: ticketdir tetap di disk,\n"
    "# tetapi tidak di-commit. Tiket mau di-commit lagi → ganti isi berkas ini, lalu commit berkasnya.\n"
    "*\n"
)
IGNORED = "diabaikan git"   # hasil `git_commit` bila seluruh path diabaikan `.gitignore`
TICKETDIR_RE = re.compile(r"^analyst/tickets/\d{10}-[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TYPES = ("FEATURE", "IMPROVEMENT", "BUG")
PRIORITIES = ("HIGH", "MEDIUM", "LOW")
PLACEHOLDER = re.compile(r"\bTBD\b|\bTODO\b|diisi nanti|<[A-Za-z][^<>\n]*>")
UNANSWERED = "_(belum terjawab)_"
LIST_FIELDS = ("domain_terms",)  # satu-satunya field frontmatter bertipe list

# Satu-satunya artefak: kartu tiket di atas, catatan elisitasi sebagai H2 terakhir.
TICKET_FILE = "TICKET.md"
ELICIT_H2 = "Catatan Elisitasi"

# Pilar `### Fakta` di `## Catatan Elisitasi` per tipe — rumah kanoniknya
# `skills/elicit/templates/elicit-template.md`.
PILLARS_REQUIRED = {
    "FEATURE": ("Masalah", "Aktor", "Kondisi Saat Ini", "Kondisi Diinginkan",
                "Aturan Bisnis", "Batas Cakupan", "Urgensi"),
    "IMPROVEMENT": ("Masalah", "Aktor", "Kondisi Saat Ini", "Kondisi Diinginkan",
                    "Aturan Bisnis", "Batas Cakupan", "Urgensi"),
    "BUG": ("Langkah Reproduksi", "Yang Diharapkan", "Yang Terjadi", "Dampak", "Urgensi"),
}
PILLARS_OPTIONAL = {
    "FEATURE": ("Kasus Khusus", "Ukuran Keberhasilan"),
    "IMPROVEMENT": ("Kasus Khusus", "Ukuran Keberhasilan"),
    "BUG": ("Lingkungan", "Batas Cakupan"),
}


# ── Root & git ────────────────────────────────────────────────────────────────

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


def is_git_repo(root: Path) -> bool:
    try:
        subprocess.check_output(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                                stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def ignored_paths(root: Path, paths: List[str]) -> List[str]:
    """Anggota `paths` (relatif root) yang diabaikan `.gitignore`; berkas ter-track tidak pernah terhitung.

    Git gagal atau bukan repo git → `[]`: commit tetap dicoba dan kegagalannya dilaporkan apa adanya.
    """
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
    """Nilai `git=` keluaran `new`/`check` untuk berkas `rel`: `ya` (di-commit), `tidak` (bukan repo git), atau
    `diabaikan` (diabaikan `.gitignore`: tetap di disk, tidak pernah di-commit)."""
    if not is_git_repo(root):
        return "tidak"
    return "diabaikan" if ignored_paths(root, [rel]) else "ya"


def sync_configured(root: Path) -> bool:
    """Repo memilih sinkron nataflow: berkas config ada, sah maupun rusak (selaras `nataflow_sync.load_config`)."""
    return any((root / rel).is_file() for rel in (ns.CONFIG_FILE, SYNC_CONFIG))


def git_commit(root: Path, paths: List[str], message: str) -> Tuple[bool, str]:
    """Commit hanya `paths` (staging eksplisit, `--only`), tanpa menyentuh index lain.

    Isi yang sudah sama dengan HEAD (mis. `close` ulang tanpa perubahan, `ref` dengan kunci yang sama)
    bukan kegagalan: `(True, "tanpa perubahan")`, tanpa commit kosong. Path yang diabaikan `.gitignore`
    tidak di-stage; bila seluruhnya diabaikan → `(True, IGNORED)`, juga tanpa commit.
    """
    ignored = ignored_paths(root, paths)
    paths = [p for p in paths if p not in ignored]
    if not paths:
        return True, IGNORED
    tracked = set(tracked_files(root, *paths))
    # Berkas ter-track di direktori yang diabaikan (tiket lama sesudah `TICKETS_IGNORE` ditulis) ditolak
    # `git add` biasa walau tetap ter-stage; `add -u` memperbaruinya tanpa keluhan.
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


def normalize_ticketdir(ticketdir: str, root: Path) -> str:
    """Path ticketdir relatif root, tanpa garis miring penutup."""
    p = Path(ticketdir)
    if p.is_absolute():
        try:
            p = p.resolve().relative_to(root.resolve())
        except ValueError:
            return str(p)
    return str(p).strip("/").removeprefix("./")


# ── Frontmatter & seksi ───────────────────────────────────────────────────────

BOM = chr(0xFEFF)


def split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Parse subset YAML frontmatter → `(data, body)`.

    Mendukung skalar, skalar berkutip, list inline `[a, "b, c"]`, dan `[]` kosong. Nilai kosong
    menjadi `[]` hanya untuk `LIST_FIELDS`; field lain tetap string kosong.
    Tidak ada komentar di akhir baris: `#` adalah bagian nilai (`Tim #2 Sales`).
    Berkas tanpa pagar `---` lengkap → `({}, text)`. BOM (U+FEFF) di awal berkas,
    tulisan sebagian editor Windows, dibuang lebih dulu: pagar sesudah BOM tetap pagar.
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
        key, value = key.strip(), value.strip()
        if value == "[]" or (value == "" and key in LIST_FIELDS):
            data[key] = []
        elif value.startswith("[") and value.endswith("]"):
            items = _LIST_ITEM.findall(value[1:-1])
            data[key] = [_unquote(v.strip()) for v in items if v.strip()]
        else:
            data[key] = _unquote(value)
    return data, body.lstrip("\n")


_LIST_ITEM = re.compile(r'\s*("[^"]*"|\'[^\']*\'|[^,]+)')


def _unquote(value: str) -> str:
    """Kutip luar yang berpasangan saja; kutip di dalam nilai dipertahankan."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def clean_value(value: str, limit: int = 200) -> str:
    """Nilai bebas (jawaban, alasan) → satu baris berkutip ganda, aman ditulis ke frontmatter."""
    flat = " ".join(value.replace('"', "'").split())[:limit]
    return f'"{flat}"'


def set_frontmatter_field(text: str, key: str, value: str) -> str:
    """Ganti nilai `key` di frontmatter, atau sisipkan sebelum pagar penutup.

    BOM di awal berkas ikut `head` dan tertulis kembali apa adanya. `ValueError` bila berkas
    tidak diawali pagar `---` atau pagar penutupnya tidak ada — menyisipkan di posisi lain
    merusak body tanpa membuat frontmatter terbaca.
    """
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


def headings(body: str, level: int = 2) -> List[str]:
    return list(sections(body, level).keys())


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


def duplicate_headings(body: str, level: int) -> List[str]:
    """Heading level `level` yang muncul lebih dari sekali di luar pagar kode.

    `sections()` memetakan heading ke dict, jadi heading ganda menimpa isi yang pertama tanpa mengubah
    urutan kunci — cek struktur yang hanya membandingkan urutan kunci tidak melihatnya.
    """
    prefix = "#" * level + " "
    seen: List[str] = []
    in_fence = False
    for line in body.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.startswith(prefix):
            seen.append(line[len(prefix):].strip())
    return sorted({h for h in seen if seen.count(h) > 1})


LOG_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|(.+)\|(.+)\|(.+)\|\s*$")


def log_rows(text: str) -> List[Tuple[str, ...]]:
    """Baris data `### Log Tanya-Jawab` → `(nomor, tanggal, pertanyaan, jawaban, sumber)`, sudah di-strip."""
    _, body = split_frontmatter(text)
    notes = sections(split_parts(body)[1], 2).get(ELICIT_H2, [])
    log = sections("\n".join(notes), 3).get("Log Tanya-Jawab", [])
    return [tuple(g.strip() for g in m.groups()) for m in (LOG_ROW.match(l.strip()) for l in log) if m]


# Field frontmatter yang ikut menentukan isi: mengubahnya sesudah review atau persetujuan sama
# dengan mengubah body. Field pembukuan (`review`, `revision`, `approved*`, `elicitation`)
# sengaja di luar sidik. `domain_terms` milik elisitasi; `priority` milik kartu.
CONTENT_FIELDS = {
    "card": ("type", "priority"),
    "elicit": ("type", "domain_terms"),
    "all": ("type", "priority", "domain_terms"),
}


def content_hash(text: str, part: str = "all") -> str:
    """Sidik 12 hex atas bagian body (`card`, `elicit`, atau `all`) + field isinya.

    Sidik `card` dan `elicit` dipasangkan sebagai sidik review; `all` dimateraikan `approve`.
    Spasi ujung baris dinormalkan.
    """
    fm, body = split_frontmatter(text)
    if part != "all":
        body = split_parts(body)[0 if part == "card" else 1]
    norm = "\n".join(l.rstrip() for l in body.strip().splitlines())
    fields = "\n".join(f"{k}={','.join(sorted(fm[k])) if isinstance(fm.get(k), list) else fm.get(k, '')}"
                       for k in CONTENT_FIELDS[part])
    return hashlib.sha256(f"{fields}\n{norm}".encode("utf-8")).hexdigest()[:12]


# Segel serah-terima (09 E8). Sengaja tanpa parser YAML: penerima (backend/frontend
# `precondition_lib.ticket_seal`) menyalin fungsi ini apa adanya, dan `tests/test_a1_ticket_source.py`
# menagih ketiga salinan memberi hasil sama. Mencakup body utuh (kartu + catatan elisitasi) dan
# baris frontmatter isi (`SEAL_FIELDS`) persis seperti tertulis; field pembukuan dan `external_ref`
# di luar segel. Ubah ketiganya bersamaan.
SEAL_FIELDS = ("type", "priority", "domain_terms")


def ticket_seal(text: str) -> str:
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    head: List[str] = []
    body = lines
    if lines and lines[0].rstrip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].rstrip() == "---"), None)
        if end is not None:
            head = [l.rstrip() for l in lines[1:end]
                    if re.match(r"^(%s)\s*:" % "|".join(SEAL_FIELDS), l)]
            body = lines[end + 1:]
    norm = "\n".join(l.rstrip() for l in body).strip("\n")
    return hashlib.sha256(("\n".join(head) + "\n\x00\n" + norm).encode("utf-8")).hexdigest()[:16]


def meaningful(lines: List[str]) -> List[str]:
    """Baris berisi, tanpa komentar HTML."""
    return [l for l in lines if l.strip() and not l.strip().startswith("<!--")]


def request_digest(text: str) -> str:
    """Sidik 12 hex `### Permintaan Asli` — dimateraikan `ticket.py new` sebagai `request_hash`.

    Elisitasi menulis ulang `TICKET.md` tiap giliran; sidik ini yang menjaga kutipan permintaan tetap
    verbatim lintas penulisan ulang itu.
    """
    _, body = split_frontmatter(text)
    notes = sections(split_parts(body)[1], 2).get(ELICIT_H2, [])
    quote = meaningful(sections("\n".join(notes), 3).get("Permintaan Asli", []))
    return hashlib.sha256("\n".join(l.rstrip() for l in quote).encode("utf-8")).hexdigest()[:12]


def ticket_skeleton(ticket_type: str, slug: str, requester: str, created: str, title: str,
                    request: str) -> str:
    """`TICKET.md` awal persis bagian 1 `elicit-template.md`, beserta `request_hash`.

    Rumah kanonik kerangkanya tetap template itu; `tests/analyst/test_ticket_10.py` menagih keduanya sama.
    """
    quote = "\n".join(f"> {l.rstrip()}" if l.strip() else ">" for l in request.strip("\n").splitlines())
    pillars = "\n\n".join(f"#### {p}\n{UNANSWERED}"
                          for p in PILLARS_REQUIRED[ticket_type] + PILLARS_OPTIONAL[ticket_type])
    text = (f"---\nstatus: DRAFT\nelicitation: OPEN\ntype: {ticket_type}\npriority: -\nslug: {slug}\n"
            f"requester: {clean_value(requester)}\ncreated: {created}\nexternal_ref: -\ndomain_terms: []\n"
            f"revision: 0\nreview: -\nreview_round: 0\nrequest_hash: -\n---\n\n# {title}\n\n"
            f"## {ELICIT_H2}\n\n### Permintaan Asli\n\n{quote}\n\n### Fakta\n\n{pillars}\n\n"
            "### Log Tanya-Jawab\n\n| # | Tanggal | Pertanyaan | Jawaban | Sumber |\n|---|---|---|---|---|\n\n"
            "### Pertanyaan Terbuka\n\n- Tidak ada.\n")
    return set_frontmatter_field(text, "request_hash", request_digest(text))


# ── Kebocoran teknis ──────────────────────────────────────────────────────────

# Istilah yang bentrok dengan kosakata bisnis Indonesia sengaja tidak didaftar: `api` (kereta
# api), `skema` (skema cicilan), `express` (pengiriman express), `expo` (pameran), `migrasi`
# (migrasi pelanggan), `branch` (cabang). Singkatan yang hanya teknis bila berhuruf besar dicocokkan
# peka-huruf lewat `LEAK_TERMS_CASED`.
LEAK_TERMS = (
    "endpoint", "rest api", "graphql", "json", "xml", "dto", "payload", "database",
    "basis data", "tabel database", "query", "sql", "schema", "migration",
    "repository", "controller", "middleware", "microservice", "backend", "back-end", "frontend",
    "front-end", "cache", "redis", "kafka", "rabbitmq", "queue", "cron", "cronjob", "webhook",
    "postgres", "postgresql", "mysql", "mongodb", "sqlite", "elasticsearch", "docker", "kubernetes",
    "react", "vue", "svelte", "sveltekit", "next.js", "angular", "laravel", "codeigniter",
    "node.js", "nodejs", "golang", "typescript", "javascript", "python", "php",
    "kotlin", "flutter", "boolean", "null", "enum", "uuid", "regex", "commit",
    "pull request", "merge request", "stacktrace", "stack trace", "exception",
    "status code", "http", "jwt", "oauth", "sdk", "refactor", "unit test",
    "localstorage", "session storage", "state management",
)
LEAK_TERMS_CASED = ("API", "DB", "Spring Boot", "Rust")
_EXT = (r"(?:tsx?|jsx?|mjs|py|go|java|kts?|rb|php|rs|sql|json|ya?ml|xml|html?|s?css|vue|svelte|"
        r"sh|env|cs|swift|dart|toml|ini|lock|conf)")
# `(jenis, pola, berlaku di dalam kutipan)`. Teks layar yang dikutip sah memuat kode galat atau identifier
# (laporan BUG mengutip "Error: invalid_grant"), tetapi tidak pernah perlu membawa path sistem atau
# metode HTTP — pola itu tetap dipindai di dalam kutipan, supaya kutipan tidak menjadi jalan pintas (G5).
LEAK_PATTERNS = (
    ("path berkas", re.compile(rf"\b[\w-]+/[\w./-]*\.{_EXT}\b"), True),
    ("rujukan file:baris", re.compile(rf"\.{_EXT}:\d+\b"), True),
    ("metode HTTP + path", re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/"), True),
    ("path API", re.compile(r"(?<![\w/])/(api|v\d)/"), True),
    ("kode HTTP", re.compile(r"\bHTTP\s*[1-5]\d\d\b", re.IGNORECASE), False),
    ("kode HTTP", re.compile(r"\b(?:error|galat)\s*[1-5]\d\d\b", re.IGNORECASE), False),
    ("identifier snake_case", re.compile(r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b"), False),
    ("identifier camelCase", re.compile(r"\b[a-z]{2,}[A-Z][A-Za-z0-9]*\b"), False),
    ("blok kode", re.compile(r"^```"), True),
)
_URLISH = re.compile(r'https?://\S+|[\w.+-]+@[\w-]+\.[\w.]+')
_EXEMPT = re.compile(r'"[^"\n]*"|“[^”\n]*”|https?://\S+|[\w.+-]+@[\w-]+\.[\w.]+')


def body_offset(text: str, body: str) -> int:
    """Jumlah baris berkas sebelum `body` (frontmatter + baris kosong yang dibuang `split_frontmatter`)."""
    return text[: len(text) - len(body)].count("\n") if text.endswith(body) else 0


def scan_leaks(body: str, allowed_terms: List[str], skip_sections: Tuple[str, ...] = (),
               line_offset: int = 0) -> List[str]:
    """Temuan kebocoran teknis `baris N: <jenis> «token»` di luar kutipan, URL, dan seksi dikecualikan.

    `line_offset` menggeser N supaya menunjuk baris berkas, bukan baris `body`.

    Istilah, kode HTTP, dan identifier di dalam tanda kutip dikecualikan karena itu tulisan yang benar-benar
    dilihat pengguna (label tombol, pesan galat); path, metode HTTP, dan blok kode tidak. `allowed_terms`
    adalah `domain_terms` frontmatter: istilah yang memang kosakata bisnis produk ini (mis. produk API
    untuk mitra).
    """
    allowed = {t.strip().lower() for t in allowed_terms if t.strip()}
    term_res = []
    for pool, flags in ((LEAK_TERMS, re.IGNORECASE), (LEAK_TERMS_CASED, 0)):
        terms = [t for t in pool if t.lower() not in allowed]
        if terms:
            term_res.append(re.compile(r"(?<![\w-])(" + "|".join(re.escape(t) for t in terms)
                                       + r")(?![\w-])", flags))
    hits: List[str] = []
    skipping = False
    for no, raw in enumerate(body.splitlines(), 1 + line_offset):
        if raw.startswith("## "):
            skipping = raw[3:].strip() in skip_sections
            continue
        if skipping or raw.strip().startswith("<!--"):
            continue
        line, quoted = _EXEMPT.sub(" ", raw), _URLISH.sub(" ", raw)
        for term_re in term_res:
            for m in term_re.finditer(line):
                hits.append(f"baris {no}: istilah teknis «{m.group(1)}»")
        for label, pat, in_quotes in LEAK_PATTERNS:
            for m in pat.finditer(quoted if in_quotes else line):
                token = m.group(0).strip()
                if token.lower() in allowed:
                    continue
                hits.append(f"baris {no}: {label} «{token}»")
    return hits


# ── Sinkron nataflow ──────────────────────────────────────────────────────────

def load_sync_config(root: Path) -> Tuple[Optional[Dict[str, str]], List[str]]:
    """`.claude/nataflow.json` bersama (15 A1) atau `analyst/nataflow.json` lama → `(config, masalah)`.

    Berkas absen → `(None, [])` (sinkron tidak aktif). Aturan kunci, UUID, dan konflik kedua berkas milik pustaka
    bersama `nataflow_sync.load_config`, salinan identik di keempat plugin. Pesan masalah sudah menyebut berkasnya.
    """
    return ns.load_config(root, SYNC_CONFIG)


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
