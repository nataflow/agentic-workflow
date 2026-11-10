#!/usr/bin/env python3
"""Gerbang artifact HTML nataflow (`nataflow:create-artifact`).

Pemakaian:
  python3 artifact.py config [--json]
  python3 artifact.py check --file <draft.html> [--key <key>] [--json]
  python3 artifact.py list [--json]
  python3 artifact.py pull --key <key> --file <draft.html> [--json]
  python3 artifact.py publish --file <draft.html> [--key <key>] [--overwrite] [--json]

`config` membaca `url` di `.claude/nataflow.json` (root repo, atau cwd di luar git) dan MCP key di
`.claude/nataflow.local.json` (wajib diabaikan git di dalam repo), lalu memastikan key menjangkau tepat satu
project lewat `get_project_info`. `check` menilai satu berkas HTML terhadap kontrak halaman artifact tanpa jaringan.

Langkah server dijalankan skrip sendiri lewat `nataflow_client` (29 S6), sehingga isi HTML tidak pernah lewat
konteks model: `list` mendaftar artifact project, `pull` menulis isi artifact yang ada ke berkas draft (satu-satunya
berkas yang ditulis skrip), dan `publish` menjalankan `check`, cek tabrakan key lewat `get_document`, lalu
`upsert_artifact` dengan isi berkas apa adanya. Artifact ber-key sama hanya ditimpa dengan `--overwrite`
(persetujuan user); dokumen non-artifact ber-key sama tidak pernah ditimpa.

Exit 1 hanya untuk FAIL; status lain (`PASS`, `CREATED`, `UPDATED`, `UNCHANGED`, `NOT_FOUND`, `TABRAKAN`,
`TABRAKAN_DOKUMEN`) exit 0. Zero external dependencies (Python Standard Library only).
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nataflow_client as nc  # noqa: E402
import nataflow_sync as ns  # noqa: E402

SOURCE = "nataflow:create-artifact"
DRAFT_DIR = "nataflow-artifacts"
MAX_BYTES = 1024 * 1024          # isi dikirim utuh sebagai argumen tool MCP
KEY_MAX = 80                     # server menerima 255; kunci artifact dibuat pendek dan terbaca
TITLE_MAX = 120
KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
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
    code = 1 if payload["status"] == "FAIL" else 0
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return code
    print(payload["status"])
    for key in ("url", "project_id", "project_name", "draft_dir", "file", "key", "title", "bytes", "content_sha256",
                "metadata", "id", "existing_type", "existing_title"):
        if payload.get(key) not in (None, ""):
            print(f"{key}: {payload[key]}")
    for row in payload.get("artifacts", []):
        print(f"- {row['key']} · {row['title']}")
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


def server_context(root: Path) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
    """`(config, key, masalah)`: `url` wajib di `.claude/nataflow.json`, key fail-closed di `.local.json`."""
    config, problems = ns.load_config(root)
    if problems:
        return None, "", problems
    if config is None:
        return None, "", [f"{ns.CONFIG_FILE} tidak ada — buat berisi `{{\"url\": \"{ns.URL_EXAMPLE}\"}}`, lalu "
                          + ns.LOCAL_SETUP]
    key, problems = ns.load_key(root)
    return (None, "", problems) if problems else (config, key, [])


def project_of(session: Any) -> Dict[str, Any]:
    """Project tunggal milik MCP key (`get_project_info`); id-nya tidak pernah ditebak."""
    info = session.call_json("get_project_info", {}, read=True)
    rows = info if isinstance(info, list) else [info]
    if len(rows) != 1 or not isinstance(rows[0], dict) or not rows[0].get("id"):
        raise nc.NataflowError("tool", f"key menjangkau {len(rows)} project — artifact butuh MCP key yang terikat ke "
                                       f"satu project")
    return rows[0]


def with_project(args: argparse.Namespace, fn) -> int:
    """Sesi + project → `fn(session, project, payload)`; galat konfigurasi/sesi/tool menjadi FAIL terbaca."""
    root = repo_root(Path.cwd())
    payload: Dict[str, Any] = {"status": "FAIL", "problems": []}
    config, key, problems = server_context(root)
    if problems:
        payload["problems"] = problems
        return emit(payload, args.json)
    payload["url"] = config["url"]
    try:
        with nc.Session(config["url"], key) as session:
            project = project_of(session)
            payload.update(project_id=project["id"], project_name=project.get("name", ""))
            fn(session, project, payload)
    except nc.NataflowError as exc:
        payload.update(status="FAIL", problems=[exc.message])
    return emit(payload, args.json)


def cmd_config(args: argparse.Namespace) -> int:
    def done(_s: Any, _p: Dict[str, Any], payload: Dict[str, Any]) -> None:
        payload.update(status="PASS", draft_dir=str(Path(tempfile.gettempdir()) / DRAFT_DIR))
    return with_project(args, done)


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
    return emit(check_payload(Path(args.file), args.key), args.json)


def check_payload(path: Path, key_arg: Optional[str]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"status": "FAIL", "file": str(path), "key": "", "title": "", "bytes": 0,
                               "content_sha256": "", "metadata": "", "problems": [], "warnings": []}
    problems: List[str] = payload["problems"]
    try:
        raw = path.read_bytes()
    except OSError as exc:
        problems.append(f"draft `{path}` tidak bisa dibaca: {exc.strerror or exc}")
        return payload
    payload["bytes"] = len(raw)
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("draft diawali BOM UTF-8; simpan tanpa BOM supaya sha256 cocok dengan isi yang dikirim")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        problems.append(f"draft bukan UTF-8 valid (byte {exc.start})")
        return payload
    if not text.strip():
        problems.append("draft kosong")
        return payload
    if len(raw) > MAX_BYTES:
        problems.append(f"draft {len(raw)} byte > {MAX_BYTES} byte (data: URI ikut dihitung); "
                        "perkecil gambar atau data yang disematkan")

    scan, page_problems, warnings = audit(text)
    problems.extend(page_problems)
    payload["warnings"] = warnings
    payload["title"] = scan.title[:TITLE_MAX]

    if key_arg is not None:
        key = key_arg.strip()
        if not KEY_RE.match(key) or len(key) > KEY_MAX:
            problems.append(f"`--key {key_arg}` harus kebab-case huruf kecil/angka, maksimal {KEY_MAX} karakter")
    else:
        key = slugify(scan.title)
        if scan.title and not key:
            problems.append("judul tidak menghasilkan key kebab-case (mis. huruf non-Latin); berikan `--key`")
    payload["key"] = key

    payload["content_sha256"] = hashlib.sha256(raw).hexdigest()
    payload["metadata"] = compact({"title": payload["title"], "source": SOURCE})
    payload["status"] = "FAIL" if problems else "PASS"
    return payload


def ref(project: Dict[str, Any], key: str) -> Dict[str, Any]:
    return {"reference_table": "project", "reference_id": project["id"], "key": key}


def cmd_list(args: argparse.Namespace) -> int:
    def run(session: Any, project: Dict[str, Any], payload: Dict[str, Any]) -> None:
        rows = nc.as_list(session.call_json("list_artifacts", {"reference_table": "project", "reference_id":
                                                               project["id"], "include_content": False}, read=True),
                          "artifacts", "documents", "data")
        payload.update(status="PASS", artifacts=[{"key": r.get("key") or "", "title": artifact_title(r)}
                                                 for r in rows if isinstance(r, dict)])
    return with_project(args, run)


def artifact_title(row: Dict[str, Any]) -> str:
    meta = row.get("metadata")
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except ValueError:
            meta = {}
    return str((meta or {}).get("title") or row.get("title") or "")


def cmd_pull(args: argparse.Namespace) -> int:
    path = Path(args.file)

    def run(session: Any, project: Dict[str, Any], payload: Dict[str, Any]) -> None:
        payload.update(key=args.key, file=str(path))
        try:
            doc = session.call_json("get_artifact", ref(project, args.key), read=True)
        except nc.NataflowError as exc:
            if exc.kind == "tool" and "not found" in exc.message:
                payload["status"] = "NOT_FOUND"
                return
            raise
        content = doc.get("content") if isinstance(doc, dict) else None
        if not isinstance(content, str):
            raise nc.NataflowError("transport", "balikan get_artifact tanpa `content`")
        data = content.encode("utf-8")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        except OSError as exc:
            raise nc.NataflowError("transport", f"draft `{path}` tidak bisa ditulis: {exc.strerror or exc}")
        payload.update(status="PASS", title=artifact_title(doc), bytes=len(data),
                       content_sha256=hashlib.sha256(data).hexdigest())
    return with_project(args, run)


def cmd_publish(args: argparse.Namespace) -> int:
    """`check` → cek tabrakan key → `upsert_artifact` berisi berkas draft apa adanya (sha mismatch: kirim ulang
    sekali sesudah membaca ulang berkas)."""
    gate = check_payload(Path(args.file), args.key)
    if gate["status"] != "PASS":
        return emit(gate, args.json)

    def run(session: Any, project: Dict[str, Any], payload: Dict[str, Any]) -> None:
        payload.update({k: gate[k] for k in ("file", "key", "title", "bytes", "content_sha256", "metadata",
                                             "warnings")})
        try:
            found = session.call_json("get_document", ref(project, gate["key"]), read=True)
        except nc.NataflowError as exc:
            if not (exc.kind == "tool" and "not found" in exc.message):
                raise
            found = None
        if isinstance(found, dict):
            payload.update(existing_type=found.get("type", ""), existing_title=artifact_title(found))
            if found.get("type") != "artifact" or found.get("mimetype") != "text/html":
                payload["status"] = "TABRAKAN_DOKUMEN"
                return
            if not args.overwrite:
                payload["status"] = "TABRAKAN"
                return
        for attempt in (1, 2):
            raw = Path(args.file).read_bytes()
            body = dict(ref(project, gate["key"]), content=raw.decode("utf-8"),
                        content_sha256=hashlib.sha256(raw).hexdigest(), metadata=gate["metadata"])
            try:
                out = session.call_json("upsert_artifact", body)
                break
            except nc.NataflowError as exc:
                if attempt == 2 or "content_sha256 does not match" not in exc.message:
                    raise
        action = str(out.get("action") or "") if isinstance(out, dict) else ""
        payload.update(status={"created": "CREATED", "updated": "UPDATED", "unchanged": "UNCHANGED"}.get(
            action, "UPDATED"), id=out.get("id", "") if isinstance(out, dict) else "")
    return with_project(args, run)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_config = sub.add_parser("config", help="url, MCP key, dan project milik key")
    p_config.add_argument("--json", action="store_true")
    p_check = sub.add_parser("check", help="nilai draft HTML terhadap kontrak halaman (tanpa jaringan)")
    p_check.add_argument("--file", required=True)
    p_check.add_argument("--key")
    p_check.add_argument("--json", action="store_true")
    p_list = sub.add_parser("list", help="artifact di project milik key (tanpa isi)")
    p_list.add_argument("--json", action="store_true")
    p_pull = sub.add_parser("pull", help="tulis isi artifact yang ada ke berkas draft")
    p_pull.add_argument("--key", required=True)
    p_pull.add_argument("--file", required=True)
    p_pull.add_argument("--json", action="store_true")
    p_pub = sub.add_parser("publish", help="check, cek tabrakan key, lalu upsert_artifact")
    p_pub.add_argument("--file", required=True)
    p_pub.add_argument("--key")
    p_pub.add_argument("--overwrite", action="store_true", help="timpa artifact ber-key sama (persetujuan user)")
    p_pub.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return {"config": cmd_config, "check": cmd_check, "list": cmd_list, "pull": cmd_pull,
            "publish": cmd_publish}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
