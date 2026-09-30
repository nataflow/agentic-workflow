#!/usr/bin/env python3
"""Pustaka sinkron nataflow bersama (langkah 15) — salinan identik di keempat plugin.

`skills/_common/nataflow_sync.py` ada di `analyst`, `backend`, `frontend`, dan `quickdev` dengan isi byte-identik:
plugin dipasang terpisah sehingga tidak bisa saling mengimpor. Ubah keempatnya bersamaan.

Isinya hanya primitif yang tidak bergantung pada artefak plugin mana pun:

- config `.claude/nataflow.json` (plus berkas lama per plugin) → `load_config`;
- identitas repo: `repo` config, `git remote origin` ternormalisasi, atau nama direktori root → `repo_identity`;
- isi berkas di `HEAD`, commit terakhir, dan versi terakhir berkas yang sudah dihapus dari git;
- workspace tujuan dari `workspaces` config (`choose_workspace`): nol entri → workspace key, satu → otomatis,
  lebih dari satu → user memilih alias saat sinkron;
- argumen tool MCP: task (`lookup`/`create`/`status`), workdir, dokumen (`upsert_document` tanpa `reference_id`);
- diff dokumen terhadap manifest remote (balikan `list_document include_content=false`).

Sinkron tidak menulis berkas apa pun (D5) dan tidak membuka koneksi jaringan (D4): skrip hanya menyusun argumen
yang dikirim model apa adanya. Semua `metadata` berupa teks JSON ringkas, karena tool MCP menerimanya sebagai string.

Zero external dependencies (Python Standard Library only).
"""

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONFIG_FILE = ".claude/nataflow.json"
DEFAULT_SERVER = "nataflow-api"
CONFIG_KEYS = ("mcp_server", "workspaces", "pic_id", "repo")
ALIAS_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
BOM = "\ufeff"
KEY_MAX = 255     # `key` workdir dan dokumen di server
TYPE_MAX = 50     # `type` dokumen di server
# Format `type` yang diterima server: huruf kecil a-z, titik di antara segmen tak kosong (mis. `prd`, `unit.report`).
TYPE_RE = re.compile(r"^[a-z]+(\.[a-z]+)*$")
MIMETYPE = "text/markdown"
WORKDIR_STATUSES = ("active", "blocked", "done", "abandoned")
# Status task yang boleh ditimpa per status tujuan (E8): status tidak pernah diturunkan dari `done`/`cancelled`.
TASK_STATUS_FROM = {"in_progress": ["todo"], "done": ["todo", "in_progress"], "cancelled": ["todo", "in_progress"]}


def compact(obj: Any) -> str:
    """Teks JSON byte-stabil untuk argumen `metadata`."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


# ── Config ────────────────────────────────────────────────────────────────────

def parse_workspaces(value: Any) -> Tuple[Dict[str, str], List[str]]:
    """Nilai `workspaces` → `({alias: UUID}, masalah)`, urutan entri berkas dipertahankan."""
    if not isinstance(value, dict):
        return {}, [f"`workspaces` harus objek alias → UUID, bukan {type(value).__name__}"]
    workspaces: Dict[str, str] = {}
    problems: List[str] = []
    for alias, uuid in value.items():
        if not ALIAS_RE.match(alias):
            problems.append(f"alias workspace `{alias}` harus huruf/angka/`.`/`_`/`-`, diawali huruf/angka, "
                            f"paling panjang 63")
        elif not isinstance(uuid, str):
            problems.append(f"`workspaces.{alias}` harus string, bukan {type(uuid).__name__}")
        elif not UUID_RE.match(uuid.strip()):
            problems.append(f"`workspaces.{alias}` `{uuid.strip()}` bukan UUID")
        elif uuid.strip().lower() in (u.lower() for u in workspaces.values()):
            problems.append(f"`workspaces.{alias}` mengulang UUID alias lain")
        else:
            workspaces[alias] = uuid.strip()
    return workspaces, problems


def parse_config(path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Satu berkas config → `(config, masalah)`. Config sah selalu memuat keempat `CONFIG_KEYS`.

    `mcp_server` default `nataflow-api`; `pic_id` dan `repo` string kosong, `workspaces` objek kosong bila tidak
    diisi. `workspace_id` tunggal lama ditolak dengan petunjuk penggantinya. Pesan masalah tanpa nama berkas;
    pemanggil yang menyebutnya.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8").lstrip(BOM))
    except UnicodeDecodeError as exc:
        return None, [f"bukan UTF-8 ({exc.reason} @ byte {exc.start})"]
    except ValueError as exc:
        return None, [f"bukan JSON sah ({exc})"]
    except OSError as exc:
        return None, [f"tidak terbaca ({exc.strerror or exc})"]
    if not isinstance(data, dict):
        return None, [f"harus objek JSON, bukan {type(data).__name__}"]
    problems = [f"kunci `workspace_id` sudah diganti `workspaces` — tulis "
                f"`\"workspaces\": {{\"<alias>\": \"<uuid>\"}}`" if k == "workspace_id"
                else f"kunci `{k}` tidak dikenal (sah: {', '.join(CONFIG_KEYS)})" for k in data if k not in CONFIG_KEYS]
    config: Dict[str, Any] = {"mcp_server": DEFAULT_SERVER, "workspaces": {}, "pic_id": "", "repo": ""}
    for key in CONFIG_KEYS:
        if key not in data:
            continue
        value = data[key]
        if key == "workspaces":
            config[key], found = parse_workspaces(value)
            problems.extend(found)
            continue
        if not isinstance(value, str):
            problems.append(f"`{key}` harus string, bukan {type(value).__name__}")
            continue
        value = value.strip()
        if key == "pic_id" and value and not UUID_RE.match(value):
            problems.append(f"`{key}` `{value}` bukan UUID")
        elif key == "repo" and re.search(r"\s", value):
            problems.append(f"`repo` `{value}` memuat spasi")
        elif value:
            config[key] = value
    return (None, problems) if problems else (config, [])


def load_config(root: Path, legacy: str = "") -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """`.claude/nataflow.json` (dan `legacy`, berkas lama relatif root) → `(config, masalah)`.

    Tanpa berkas → `(None, [])`: sinkron tidak aktif. Berkas yang ada tetapi rusak tidak pernah dianggap absen,
    karena repo yang sudah memilih sinkron tidak boleh berhenti sinkron diam-diam akibat salah ketik. Kedua berkas
    ada dengan isi efektif berbeda → masalah, supaya tidak ada config yang diam-diam kalah.
    """
    found: List[Tuple[str, Dict[str, Any]]] = []
    for rel in (CONFIG_FILE, legacy):
        if not rel or not (root / rel).is_file():
            continue
        config, problems = parse_config(root / rel)
        if problems:
            return None, [f"{rel} rusak — " + "; ".join(problems)]
        found.append((rel, config))
    if not found:
        return None, []
    if len(found) == 2 and found[0][1] != found[1][1]:
        return None, [f"{CONFIG_FILE} dan {legacy} berbeda isi — pertahankan satu saja ({CONFIG_FILE})"]
    return found[0][1], []


# ── Git & identitas repo ──────────────────────────────────────────────────────

def _git(root: Path, *args: str) -> Tuple[int, bytes]:
    try:
        proc = subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return 1, b""
    return proc.returncode, proc.stdout


def normalize_remote(url: str) -> str:
    """URL remote → `host/owner/repo`: tanpa skema, kredensial, port, dan akhiran `.git`."""
    value = url.strip()
    scheme = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://(.*)$", value)
    if scheme:
        host, _, path = scheme.group(1).partition("/")
        host = host.rsplit("@", 1)[-1].split(":", 1)[0].lower()
        value = f"{host}/{path}" if host else "/" + path
    else:
        scp = re.match(r"^(?:[^@/\s]+@)?([^:/\s]+):(?![\\/])(.+)$", value)
        if scp and len(scp.group(1)) > 1:           # `C:\…` bukan host
            value = f"{scp.group(1).lower()}/{scp.group(2).lstrip('/')}"
    value = value.rstrip("/")
    if value.endswith(".git"):
        value = value[:-4]
    return value.rstrip("/")


def repo_identity(root: Path, config: Dict[str, Any]) -> str:
    """`repo` config bila diisi; selain itu remote `origin` ternormalisasi; tanpa remote → nama direktori root."""
    if config.get("repo"):
        return config["repo"]
    code, out = _git(root, "remote", "get-url", "origin")
    url = out.decode("utf-8", "replace").strip() if code == 0 else ""
    return (normalize_remote(url) if url else "") or root.resolve().name


def head_text(root: Path, rel: str) -> Tuple[Optional[str], str]:
    """Isi berkas di `HEAD` → `(teks, masalah)`. Tidak ter-commit atau bukan repo git → `(None, "")`."""
    code, out = _git(root, "show", f"HEAD:{rel}")
    if code != 0:
        return None, ""
    try:
        return out.decode("utf-8"), ""
    except UnicodeDecodeError as exc:
        return None, f"{rel} di HEAD bukan UTF-8 ({exc.reason} @ byte {exc.start})"


def head_files(root: Path, rel_dir: str) -> List[str]:
    """Nama berkas yang ter-commit langsung di bawah `rel_dir` pada `HEAD` (tanpa subdirektori), terurut."""
    prefix = rel_dir.rstrip("/") + "/"
    code, out = _git(root, "ls-tree", "HEAD", prefix)
    if code != 0:
        return []
    names = []
    for line in out.decode("utf-8", "replace").splitlines():
        info, _, path = line.partition("\t")           # `<mode> <type> <object>\t<path>`
        if info.split(" ")[1:2] == ["blob"] and path.startswith(prefix) and "/" not in path[len(prefix):]:
            names.append(path[len(prefix):])
    return sorted(names)


def last_commit(root: Path, rel: str) -> str:
    """Sha commit terakhir yang menyentuh `rel` (termasuk yang menghapusnya), atau kosong."""
    code, out = _git(root, "log", "-1", "--format=%H", "--", rel)
    return out.decode("utf-8", "replace").strip() if code == 0 else ""


def removed_text(root: Path, rel: str) -> Tuple[Optional[str], str]:
    """Berkas yang sudah tidak ada di `HEAD` → isi versi terakhirnya (induk commit penghapus), atau `None`."""
    sha = last_commit(root, rel)
    if not sha:
        return None, ""
    code, out = _git(root, "show", f"{sha}^:{rel}")
    if code != 0:
        return None, ""
    try:
        return out.decode("utf-8"), sha
    except UnicodeDecodeError:
        return None, ""


def disk_text(path: Path) -> Tuple[Optional[str], str]:
    """Isi berkas di disk apa adanya (tanpa penerjemahan akhir baris) → `(teks, masalah)`."""
    try:
        return path.read_bytes().decode("utf-8"), ""
    except UnicodeDecodeError as exc:
        return None, f"{path.name} bukan UTF-8 ({exc.reason} @ byte {exc.start})"
    except OSError as exc:
        return None, f"{path.name} tidak terbaca ({exc.strerror or exc})"


def frontmatter_value(text: str, field: str) -> str:
    """Nilai `field: nilai` di blok frontmatter `---` teratas, tanpa kutip; kosong bila tidak ada."""
    lines = text.lstrip(BOM).splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^" + re.escape(field) + r"\s*:\s*(.*)$", line)
        if m:
            return m.group(1).strip().strip("\"'")
    return ""


def h1_title(text: str) -> str:
    """Teks H1 pertama di luar frontmatter, atau kosong."""
    body = text.lstrip(BOM)
    if body.startswith("---"):
        end = re.search(r"^---\s*$", body[3:], re.M)
        body = body[3 + end.end():] if end else body
    m = re.search(r"^# (.+)$", body, re.M)
    return m.group(1).strip() if m else ""


def pick_sections(text: str, names: Tuple[str, ...]) -> str:
    """Seksi H2 bernama `names` (urutan kemunculan di berkas) beserta heading-nya; kosong bila tak satu pun ada."""
    parts, keep = [], False
    for line in text.lstrip(BOM).splitlines():
        if line.startswith("## "):
            keep = line[3:].strip() in names
        elif line.startswith("# "):
            keep = False
        if keep:
            parts.append(line)
    return "\n".join(parts).strip()


# ── Argumen tool ──────────────────────────────────────────────────────────────

def sha256_text(text: str) -> str:
    """Sha256 heksadesimal atas byte UTF-8 isi, sama dengan yang dihitung server."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def doc_meta(source: str, repo: str, path: str, status: str = "", commit: str = "",
             removed: bool = False, **extra: str) -> Dict[str, Any]:
    """Metadata dokumen (01 § Kontrak identitas) dengan urutan kunci tetap; `removed` hanya bila benar."""
    meta: Dict[str, Any] = {"source": source, "repo": repo, "path": path}
    if status:
        meta["status"] = status
    meta["commit"] = commit
    meta.update((k, v) for k, v in extra.items() if v)
    if removed:
        meta["removed"] = True
    return meta


def remote_type(value: Any) -> str:
    """`type` dari manifest remote dalam format server; baris lama bergaya `UNIT_REPORT` menjadi `unit.report`."""
    return str(value or "").strip().lower().replace("_", ".")


def document(reference_table: str, key: str, doc_type: str, content: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Argumen `upsert_document` tanpa `reference_id` (diisi model dari balikan tool sebelumnya)."""
    return {"reference_table": reference_table, "key": key, "type": doc_type, "content": content,
            "content_sha256": sha256_text(content), "metadata": compact(meta)}


def check_documents(docs: List[Dict[str, Any]]) -> List[str]:
    """Batas server yang bisa diperiksa sebelum dikirim: panjang `key`, format dan panjang `type`, dan key ganda."""
    problems, seen = [], set()
    for d in docs:
        if len(d["key"]) > KEY_MAX:
            problems.append(f"key dokumen `{d['key'][:40]}…` lebih dari {KEY_MAX} karakter")
        if len(d["type"]) > TYPE_MAX:
            problems.append(f"type `{d['type']}` lebih dari {TYPE_MAX} karakter")
        elif not TYPE_RE.match(d["type"]):
            problems.append(f"type `{d['type']}` bukan huruf kecil a-z bersegmen titik")
        if d["key"] in seen:
            problems.append(f"key dokumen `{d['key']}` ganda")
        seen.add(d["key"])
    return problems


def choose_workspace(config: Dict[str, Any], alias: str) -> Tuple[str, List[Dict[str, str]], List[str]]:
    """`--workspace <alias>` terhadap `workspaces` config → `(workspace_id, pilihan, masalah)`.

    Alias terisi → UUID-nya. Tanpa alias: nol entri → `""` (workspace milik key), satu entri → UUID-nya, lebih dari
    satu → `""` beserta `pilihan` `[{alias, workspace_id}]`: user memilih salah satu, lalu skrip dijalankan ulang
    dengan `--workspace`. Pilihan hanya dibutuhkan saat membuat task atau menentukan induk dokumen repo; task yang
    sudah ada ditemukan lewat `lookup` seluruh project dan workdir-nya mengikuti workspace task itu.
    """
    workspaces = config["workspaces"]
    if alias:
        if alias in workspaces:
            return workspaces[alias], [], []
        valid = ", ".join(workspaces) or "tidak ada — `workspaces` kosong"
        return "", [], [f"--workspace `{alias}` tidak ada di `workspaces` {CONFIG_FILE} (sah: {valid})"]
    if len(workspaces) == 1:
        return next(iter(workspaces.values())), [], []
    return "", [{"alias": a, "workspace_id": u} for a, u in workspaces.items()], []


def workspace_fields(workspace_id: str, choices: List[Dict[str, str]]) -> Dict[str, Any]:
    """Field payload penentu workspace: `workspace_id` terpilih, ditambah `workspace_choices` bila user harus memilih."""
    return {"workspace_id": workspace_id, "workspace_choices": choices} if choices else {"workspace_id": workspace_id}


def task_args(config: Dict[str, Any], workspace_id: str, ident: Dict[str, str], repo: str, title: str,
              description: str) -> Dict[str, Any]:
    """`lookup` (saringan containment identitas saja, seluruh jangkauan key) dan `create` untuk task sebuah taskdir
    atau rencana.

    `ident` = `{"source":"analyst","ticket_key":…}` untuk taskdir bertiket (E9), atau
    `{"source":<plugin>,"workdir_key":…}` untuk yang tanpa tiket. `repo` hanya di metadata `create`, supaya task
    lama tanpa `repo` tetap ditemukan. `lookup` tanpa `workspace_id`, supaya task yang dibuat di workspace mana pun
    (termasuk task tiket analyst di workspace pilihan user) tetap ditemukan dan tidak dibuat kembar. `workspace_id`
    kosong → `create` tanpa workspace (workspace milik key, atau user memilih dulu bila ada `workspace_choices`).
    """
    create: Dict[str, Any] = {"title": title, "description": description}
    if workspace_id:
        create["workspace_id"] = workspace_id
    if config["pic_id"]:
        create["pic_id"] = config["pic_id"]
    create["metadata"] = compact(dict(ident, repo=repo))
    return {"lookup": {"metadata": compact(ident)}, "create": create}


def task_status(target: str) -> Optional[Dict[str, Any]]:
    """`{"status": tujuan, "from": [status asal yang boleh ditimpa]}`, atau `None` tanpa tujuan."""
    if target not in TASK_STATUS_FROM:
        return None
    return {"status": target, "from": list(TASK_STATUS_FROM[target])}


def workdir_args(key: str, name: str, status: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Argumen `upsert_workdir` tanpa `task_id` dan `workspace_id`: keduanya diisi model dari task langkah task,
    supaya workdir selalu berada di workspace task induknya."""
    args: Dict[str, Any] = {"key": key, "name": name}
    args["status"] = status
    args["metadata"] = compact(meta)
    return args


def workdir_problems(key: str, name: str, status: str) -> List[str]:
    problems = []
    if len(key) > KEY_MAX:
        problems.append(f"kunci workdir lebih dari {KEY_MAX} karakter ({len(key)}) — isi `repo` di {CONFIG_FILE} "
                        f"dengan nama yang lebih pendek")
    if len(name) > KEY_MAX:
        problems.append(f"nama workdir lebih dari {KEY_MAX} karakter")
    if status not in WORKDIR_STATUSES:
        problems.append(f"status workdir `{status}` tidak sah")
    return problems


# ── Manifest remote ───────────────────────────────────────────────────────────

def parse_remote(text: str) -> Tuple[Optional[Dict[str, Dict[str, Any]]], List[str]]:
    """Teks balikan `list_document` → `{key: {content_sha256, type, mimetype, metadata}}`.

    Diterima larik `documentView` apa adanya, atau objek yang membungkusnya di `documents`/`data`. Dokumen tanpa
    `key` (dibuat di luar sinkron) diabaikan.
    """
    try:
        data = json.loads(text.lstrip(BOM))
    except ValueError as exc:
        return None, [f"--remote bukan JSON sah ({exc}) — serahkan teks balikan list_document apa adanya"]
    if isinstance(data, dict):
        for field in ("documents", "data"):
            if isinstance(data.get(field), list):
                data = data[field]
                break
    if not isinstance(data, list):
        return None, ["--remote harus larik dokumen balikan list_document"]
    remote: Dict[str, Dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            return None, ["--remote memuat entri yang bukan objek dokumen"]
        key = item.get("key")
        if not isinstance(key, str) or not key:
            continue
        meta = item.get("metadata")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except ValueError:
                meta = None
        remote[key] = {"content_sha256": str(item.get("content_sha256") or "").lower(),
                       "type": item.get("type"), "mimetype": item.get("mimetype") or MIMETYPE, "metadata": meta}
    return remote, []


def same_as_remote(doc: Dict[str, Any], entry: Optional[Dict[str, Any]]) -> bool:
    """Sama bila sha, `type`, `mimetype`, dan metadata (semantik JSON) sama — aturan `unchanged` server."""
    return (entry is not None and entry["content_sha256"] == doc["content_sha256"] and entry["type"] == doc["type"]
            and entry["mimetype"] == MIMETYPE and entry["metadata"] == json.loads(doc["metadata"]))


def split_remote(docs: List[Dict[str, Any]], remote: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """→ `(dokumen yang perlu didorong, jumlah yang sudah sama)`."""
    push = [d for d in docs if not same_as_remote(d, remote.get(d["key"]))]
    return push, len(docs) - len(push)


def read_remote(source: str, stdin_text: str) -> Tuple[Optional[Dict[str, Dict[str, Any]]], List[str]]:
    """Nilai `--remote`: `-` = stdin, selain itu path berkas berisi teks balikan `list_document`."""
    if source == "-":
        text = stdin_text
    else:
        try:
            text = Path(source).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return None, [f"--remote `{source}` tidak terbaca ({exc})"]
    if not text.strip():
        return None, ["--remote kosong — serahkan teks balikan list_document (larik kosong `[]` bila tidak ada)"]
    return parse_remote(text)


# ── Keluaran ──────────────────────────────────────────────────────────────────

def emit(payload: Dict[str, Any], as_json: bool, line: str) -> None:
    """`--json` → payload apa adanya (indent 2, urutan kunci tetap); selain itu satu baris ringkas."""
    print(json.dumps(payload, indent=2, ensure_ascii=False) if as_json else line)


def emit_skip(as_json: bool, prefix: str) -> int:
    emit({"status": "SKIP", "enabled": False}, as_json,
         f"{prefix} SKIP: {CONFIG_FILE} tidak ada — sinkron nataflow tidak aktif di repo ini")
    return 0


def emit_fail(as_json: bool, prefix: str, problems: List[str]) -> int:
    emit({"status": "FAIL", "enabled": True, "problems": problems}, as_json, f"{prefix} FAIL: " + "; ".join(problems))
    return 1
