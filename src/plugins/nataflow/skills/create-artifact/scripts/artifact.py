#!/usr/bin/env python3
"""Gerbang artifact HTML nataflow (`nataflow:create-artifact`).

Pemakaian:
  python3 artifact.py config [--json]
  python3 artifact.py check --file <draft.html> [--key <key>] [--json]

`config` menentukan server MCP (`mcp_server` di `.claude/nataflow.json` root repo, default `nataflow-api`)
dan direktori draft cadangan. `check` menilai satu berkas HTML terhadap kontrak halaman artifact, lalu
menyusun argumen `upsert_artifact` yang dikirim model apa adanya: `key`, `content_sha256`, dan `metadata`.

Skrip tidak membuka koneksi jaringan dan tidak menulis berkas: isi artifact hanya hidup di server nataflow,
draft lokal cuma bahan kerja sementara.

Exit 0 = PASS, 1 = FAIL. Zero external dependencies (Python Standard Library only).
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONFIG_FILE = ".claude/nataflow.json"
DEFAULT_SERVER = "nataflow-api"
SOURCE = "nataflow:create-artifact"
DRAFT_DIR = "nataflow-artifacts"
MAX_BYTES = 1024 * 1024          # isi dikirim utuh sebagai argumen tool MCP
KEY_MAX = 80                     # server menerima 255; kunci artifact dibuat pendek dan terbaca
TITLE_MAX = 120
KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SERVER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
# Asal skrip dan stylesheet eksternal yang boleh dimuat halaman; selain itu wajib inline.
SCRIPT_HOSTS = ("https://cdnjs.cloudflare.com/", "https://cdn.jsdelivr.net/npm/", "https://unpkg.com/",
                "https://cdn.tailwindcss.com", "https://code.jquery.com/")
STYLE_HOSTS = ("https://fonts.googleapis.com/",)
INLINE_SCHEMES = ("data:", "blob:", "#", "about:", "javascript:", "mailto:", "tel:")
SLOW_RELS = {"stylesheet", "modulepreload", "preload"}
LOADING_TAGS = ("img", "script", "iframe", "source", "video", "audio")
# Endpoint render mengirim `Content-Security-Policy: sandbox allow-scripts`: origin halaman opaque, jadi API
# penyimpanan melempar SecurityError, sedangkan dialog, popup, dan submit form diam-diam diblokir.
STORAGE_RE = re.compile(r"\b(?:localStorage|sessionStorage|indexedDB)\b|\bdocument\s*\.\s*cookie\b")
DIALOG_RE = re.compile(r"(?<![\w.])(?:window\s*\.\s*)?(?:alert|confirm|prompt)\s*\(")


def compact(obj: Any) -> str:
    """Teks JSON byte-stabil untuk argumen `metadata`."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def emit(payload: Dict[str, Any], as_json: bool) -> int:
    code = 0 if payload["status"] == "PASS" else 1
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return code
    print(payload["status"])
    for key in ("mcp_server", "draft_dir", "key", "title", "bytes", "content_sha256", "metadata"):
        if payload.get(key) not in (None, ""):
            print(f"{key}: {payload[key]}")
    for line in payload.get("problems", []):
        print(f"FAIL: {line}")
    for line in payload.get("warnings", []):
        print(f"WARN: {line}")
    return code


# ── config ────────────────────────────────────────────────────────────────────

def repo_root(cwd: Path) -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(cwd), capture_output=True,
                             text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return cwd
    top = out.stdout.strip()
    return Path(top) if out.returncode == 0 and top else cwd


def load_server(root: Path) -> Tuple[str, str, List[str]]:
    """`(mcp_server, sumber, masalah)` dari `.claude/nataflow.json`; berkas absen → default."""
    path = root / CONFIG_FILE
    if not path.is_file():
        return DEFAULT_SERVER, "default", []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return "", CONFIG_FILE, [f"{CONFIG_FILE} tidak bisa dibaca sebagai JSON: {exc}"]
    if not isinstance(data, dict):
        return "", CONFIG_FILE, [f"{CONFIG_FILE} harus objek JSON"]
    server = data.get("mcp_server", DEFAULT_SERVER)
    if not isinstance(server, str) or not SERVER_RE.match(server):
        return "", CONFIG_FILE, [f"`mcp_server` di {CONFIG_FILE} harus nama server MCP tanpa spasi"]
    return server, CONFIG_FILE, []


def cmd_config(args: argparse.Namespace) -> int:
    server, source, problems = load_server(repo_root(Path.cwd()))
    return emit({
        "status": "FAIL" if problems else "PASS",
        "mcp_server": server,
        "config_source": source,
        "draft_dir": str(Path(tempfile.gettempdir()) / DRAFT_DIR),
        "problems": problems,
    }, args.json)


# ── check ─────────────────────────────────────────────────────────────────────

class PageScan(HTMLParser):
    """Kumpulkan fakta halaman yang dinilai `check`; parser stdlib toleran terhadap HTML rusak."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: List[str] = []
        self.in_title = False
        self.title_seen = False
        self.charset = False
        self.viewport = False
        self.password = False
        self.scripts: List[str] = []
        self.styles: List[str] = []
        self.relative: List[str] = []
        self.in_script = False
        self.code: List[str] = []          # isi <script> inline dan atribut on* — tempat API browser dipanggil
        self.blank_links = 0
        self.form_actions = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        a = {k.lower(): (v or "").strip() for k, v in attrs}
        if tag == "title":
            self.in_title = True
            self.title_seen = True
        elif tag == "meta":
            if "charset" in a or a.get("http-equiv", "").lower() == "content-type":
                self.charset = True
            if a.get("name", "").lower() == "viewport":
                self.viewport = True
        elif tag == "input" and a.get("type", "").lower() == "password":
            self.password = True
        elif tag == "script":
            self.in_script = True
            if a.get("src"):
                self.scripts.append(a["src"])
        elif tag == "a" and a.get("target", "").lower() == "_blank":
            self.blank_links += 1
        elif tag == "form" and a.get("action"):
            self.form_actions += 1
        self.code.extend(v for k, v in a.items() if k.startswith("on") and v)
        rels = set(a.get("rel", "").lower().split())
        if tag == "link" and a.get("href") and rels & SLOW_RELS:
            self.styles.append(a["href"])
        # Rujukan yang dimuat browser; <link> lain (canonical, preconnect) tidak memuat berkas.
        loads = tag in LOADING_TAGS or (tag == "link" and bool(rels & (SLOW_RELS | {"icon"})))
        for attr in ("src", "href"):
            ref = a.get(attr, "")
            if loads and ref and is_relative(ref):
                self.relative.append(f"<{tag} {attr}=\"{ref}\">")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "script":
            self.in_script = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        elif self.in_script:
            self.code.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def is_relative(ref: str) -> bool:
    low = ref.lower()
    return not (low.startswith(("http://", "https://", "//")) or low.startswith(INLINE_SCHEMES))


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug[:KEY_MAX].rstrip("-")


def audit(text: str) -> Tuple[PageScan, List[str], List[str]]:
    problems: List[str] = []
    warnings: List[str] = []
    scan = PageScan()
    try:
        scan.feed(text)
        scan.close()
    except Exception as exc:  # HTMLParser hampir tak pernah melempar; tetap jangan sampai traceback
        problems.append(f"HTML tidak bisa diurai: {exc}")
        return scan, problems, warnings

    if not re.match(r"\s*<!doctype html>", text, re.IGNORECASE):
        problems.append("baris pertama wajib `<!doctype html>` (tanpanya browser memakai quirks mode)")
    if not scan.charset:
        problems.append("`<meta charset=\"utf-8\">` tidak ada; endpoint render bisa salah menebak encoding")
    if not scan.viewport:
        problems.append("`<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">` tidak ada")
    if not scan.title:
        problems.append("`<title>` kosong atau tidak ada; judul artifact diambil dari situ")
    elif len(scan.title) > TITLE_MAX:
        problems.append(f"`<title>` {len(scan.title)} karakter > {TITLE_MAX}; pakai nama pendek 2–4 kata")
    if scan.password:
        problems.append("`<input type=\"password\">` dilarang: artifact tidak boleh mengumpulkan kredensial")
    for src in scan.scripts:
        if not is_relative(src) and not src.startswith(SCRIPT_HOSTS):
            problems.append(f"skrip `{src}` di luar CDN yang diizinkan ({', '.join(SCRIPT_HOSTS)}); "
                            "sematkan inline")
    for href in scan.styles:
        if not is_relative(href) and not href.startswith(STYLE_HOSTS):
            problems.append(f"stylesheet `{href}` di luar Google Fonts; sematkan CSS inline")
    for ref in scan.relative:
        problems.append(f"rujukan relatif {ref}: artifact satu berkas tanpa berkas pendukung; "
                        "sematkan inline atau pakai data: URI")
    code = "\n".join(scan.code)
    used = sorted({" ".join(m.group(0).split()) for m in STORAGE_RE.finditer(code)})
    if used:
        problems.append(f"{', '.join(used)} tidak tersedia di sandbox render (origin opaque, melempar "
                        "SecurityError); simpan state di memori")

    if "prefers-color-scheme" not in text:
        warnings.append("tidak ada `@media (prefers-color-scheme: dark)`; halaman hanya bertema terang")
    if not re.search(r":root\s*(?:\[[^\]]*\]\s*)?\{[^}]*--", text):
        warnings.append("warna tidak didefinisikan sebagai token `--*` di `:root`")
    if DIALOG_RE.search(code):
        warnings.append("`alert`/`confirm`/`prompt` diblokir sandbox render; tampilkan pesan di halaman")
    if scan.blank_links:
        warnings.append(f"{scan.blank_links} tautan `target=\"_blank\"` tidak terbuka di sandbox render "
                        "(tanpa allow-popups)")
    if scan.form_actions:
        warnings.append("`<form action>` tidak bisa dikirim di sandbox render (tanpa allow-forms); "
                        "tangani di JS dengan preventDefault")
    if len(scan.title.split()) > 6:
        warnings.append("`<title>` lebih dari 6 kata; judul artifact sebaiknya 2–4 kata")
    return scan, problems, warnings


def cmd_check(args: argparse.Namespace) -> int:
    path = Path(args.file)
    payload: Dict[str, Any] = {"status": "FAIL", "file": str(path), "key": "", "title": "", "bytes": 0,
                               "content_sha256": "", "metadata": "", "problems": [], "warnings": []}
    problems: List[str] = payload["problems"]
    try:
        raw = path.read_bytes()
    except OSError as exc:
        problems.append(f"draft `{path}` tidak bisa dibaca: {exc.strerror or exc}")
        return emit(payload, args.json)
    payload["bytes"] = len(raw)
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("draft diawali BOM UTF-8; simpan tanpa BOM supaya sha256 cocok dengan isi yang dikirim")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        problems.append(f"draft bukan UTF-8 valid (byte {exc.start})")
        return emit(payload, args.json)
    if not text.strip():
        problems.append("draft kosong")
        return emit(payload, args.json)
    if len(raw) > MAX_BYTES:
        problems.append(f"draft {len(raw)} byte > {MAX_BYTES} byte (data: URI ikut dihitung); "
                        "perkecil gambar atau data yang disematkan")

    scan, page_problems, warnings = audit(text)
    problems.extend(page_problems)
    payload["warnings"] = warnings
    payload["title"] = scan.title[:TITLE_MAX]

    if args.key is not None:
        key = args.key.strip()
        if not KEY_RE.match(key) or len(key) > KEY_MAX:
            problems.append(f"`--key {args.key}` harus kebab-case huruf kecil/angka, maksimal {KEY_MAX} karakter")
    else:
        key = slugify(scan.title)
        if scan.title and not key:
            problems.append("judul tidak menghasilkan key kebab-case (mis. huruf non-Latin); berikan `--key`")
    payload["key"] = key

    payload["content_sha256"] = hashlib.sha256(raw).hexdigest()
    payload["metadata"] = compact({"title": payload["title"], "source": SOURCE})
    payload["status"] = "FAIL" if problems else "PASS"
    return emit(payload, args.json)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_config = sub.add_parser("config", help="server MCP dan direktori draft cadangan")
    p_config.add_argument("--json", action="store_true")
    p_check = sub.add_parser("check", help="nilai draft HTML dan susun argumen upsert_artifact")
    p_check.add_argument("--file", required=True)
    p_check.add_argument("--key")
    p_check.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return cmd_config(args) if args.cmd == "config" else cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
