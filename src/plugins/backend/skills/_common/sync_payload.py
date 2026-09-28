#!/usr/bin/env python3
"""Argumen tool MCP nataflow untuk satu taskdir backend atau dokumen tingkat repo (15 B2, B8–B10).

Read-only: tidak menulis berkas dan tidak meng-commit (D5). Model mengirim nilai keluarannya apa adanya lewat
prosedur `tech-lead/references/nataflow-sync.md` (D4); skrip ini satu-satunya penyusun isi dan pemilih berkas.

- `--taskdir <td>`: workdir `backenddev:<repo>:<td>` tertaut ke task tiket analyst (`ticket_source`) atau ke task
  baru ber-`workdir_key`. Isi dokumen diambil dari blob `HEAD` (E6): `TASK.md` selalu; `BRD.md`/`PRD.md` hanya
  `APPROVED`; brief semua status; `RCA.md`, `report-NN.md`, `HALT.md`, `REVIEW.md`, `REPORT.md` bila ter-commit;
  `.explore/` tidak pernah. Status workdir dari disk: `REPORT.md` → `done`, `HALT.md` atau brief `BLOCKED` →
  `blocked`, selain itu `active`.
- `--repo-docs audit|api|profile`: laporan `backenddev/issues/`, `docs/api/`, atau profil sebagai dokumen
  `AUDIT`/`API_DOC`/`PROFILE` di bawah workspace, dengan key `<repo>/<path>` (T10).

Tanpa `--remote`: argumen task, workdir, dan manifest, tanpa isi dokumen. `--remote -`: dokumen yang berbeda dari
teks balikan `list_document include_content=false` di stdin, ditambah key remote yang tidak lagi terpilih: berkasnya
masih di `HEAD` → didorong dengan status terbaru; sudah dihapus → versi terakhirnya dengan `removed: true` (E7).

Keluaran `--json` selalu JSON: `SKIP` (config absen), `FAIL` (`problems`), atau `PASS`.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import posixpath
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nataflow_sync as ns  # noqa: E402
from precondition_lib import (  # noqa: E402
    PROFILE_DIR_REL,
    TICKET_PATH_RE,
    check_taskdir,
    cli,
    find_repo_root,
    normalize_ticket_path,
    resolve_profile_dir,
)

SOURCE = "backenddev"
PREFIX = "SYNC-PAYLOAD"
FIXED_TYPES = {"TASK.md": "TASK", "BRD.md": "BRD", "PRD.md": "PRD", "RCA.md": "RCA", "HALT.md": "HALT",
               "REVIEW.md": "REVIEW", "REPORT.md": "REPORT"}
BRIEF_NAME = re.compile(r"^brief-\d{2}-[^/]+\.md$")
UNIT_REPORT = re.compile(r"^report-\d{2}\.md$")
APPROVAL_DOCS = ("BRD", "PRD")                         # hanya APPROVED yang didorong (D2)
STARTED = ("DONE", "BLOCKED", "SUPERSEDED")            # brief yang sudah disentuh eksekusi
REPO_DOCS = {"audit": ("backenddev/issues", "AUDIT"), "api": ("docs/api", "API_DOC"),
             "profile": (PROFILE_DIR_REL, "PROFILE")}
TASK_SECTIONS = ("Description", "Success Criteria", "Out of Scope")


def doc_type(name: str) -> str:
    if name in FIXED_TYPES:
        return FIXED_TYPES[name]
    return "BRIEF" if BRIEF_NAME.match(name) else "UNIT_REPORT" if UNIT_REPORT.match(name) else ""


def doc_status(text: str) -> str:
    return ns.frontmatter_value(text, "status") or ns.frontmatter_value(text, "verdict")


def build_doc(root: Path, table: str, key: str, rel: str, doc_type_: str, text: str, repo: str,
              removed_commit: str = "") -> Dict[str, Any]:
    commit = removed_commit or ns.last_commit(root, rel)
    meta = ns.doc_meta(SOURCE, repo, rel, doc_status(text), commit, removed=bool(removed_commit))
    return ns.document(table, key, doc_type_, text, meta)


def select_taskdir(root: Path, td: str, repo: str) -> Tuple[List[Dict[str, Any]], Dict[str, str], List[str]]:
    """Dokumen terpilih dari `HEAD`, isi `TASK.md`, dan masalah (berkas non-UTF-8)."""
    docs: List[Dict[str, Any]] = []
    texts: Dict[str, str] = {}
    problems: List[str] = []
    for name in ns.head_files(root, td):
        kind = doc_type(name)
        if not kind:
            continue
        text, problem = ns.head_text(root, f"{td}/{name}")
        if problem:
            problems.append(problem)
            continue
        if text is None:
            continue
        texts[name] = text
        if kind in APPROVAL_DOCS and doc_status(text) != "APPROVED":
            continue
        docs.append(build_doc(root, "workdir", name, f"{td}/{name}", kind, text, repo))
    return docs, texts, problems


def select_repo_docs(root: Path, kind: str, repo: str) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    rel_dir, doc_type_ = REPO_DOCS[kind]
    if kind == "profile":
        rel_dir = resolve_profile_dir(root)[0].relative_to(root).as_posix()
    docs, problems = [], []
    for name in ns.head_files(root, rel_dir):
        if not name.endswith(".md"):
            continue
        rel = f"{rel_dir}/{name}"
        text, problem = ns.head_text(root, rel)
        if problem:
            problems.append(problem)
        elif text is not None:
            docs.append(build_doc(root, "workspace", f"{repo}/{rel}", rel, doc_type_, text, repo))
    return rel_dir, docs, problems


def mirrored_extras(root: Path, table: str, remote: Dict[str, Dict[str, Any]], chosen: List[Dict[str, Any]],
                    key_to_rel, repo: str) -> List[Dict[str, Any]]:
    """Key remote yang tidak lagi terpilih tetap dicerminkan (E7): isi `HEAD` terbaru, atau versi terakhir sebelum
    dihapus dengan `removed: true`. Key yang tidak bisa dipetakan ke berkas di jangkarnya diabaikan."""
    chosen_keys = {d["key"] for d in chosen}
    extras = []
    for key in sorted(set(remote) - chosen_keys):
        rel = key_to_rel(key)
        if not rel:
            continue
        kind = remote[key]["type"] or doc_type(posixpath.basename(rel)) or "DOC"
        text, _ = ns.head_text(root, rel)
        if text is not None:
            extras.append(build_doc(root, table, key, rel, kind, text, repo))
            continue
        text, sha = ns.removed_text(root, rel)
        if text is not None:
            extras.append(build_doc(root, table, key, rel, kind, text, repo, removed_commit=sha))
    return extras


def diff_phase(args, config: Dict[str, str], docs: List[Dict[str, Any]], extras_fn) -> int:
    remote, problems = ns.read_remote(args.remote, sys.stdin.read() if args.remote == "-" else "")
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    docs = docs + extras_fn(remote)
    problems = ns.check_documents(docs)
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    push, same = ns.split_remote(docs, remote)
    payload = {"status": "PASS", "enabled": True, "mcp_server": config["mcp_server"], "documents": push,
               "same": same, "documents_total": len(docs)}
    ns.emit(payload, args.json, f"{PREFIX} PASS: {len(push)} dokumen perlu didorong, {same} sama — argumen lewat `--json`")
    return 0


def ticket_key(task_text: str) -> Tuple[Optional[str], str]:
    """`ticket_source` frontmatter → `ticket_key` analyst (dirname path `TICKET.md`), `None` tanpa tiket."""
    raw = ns.frontmatter_value(task_text, "ticket_source")
    if not raw:
        return None, ""
    path = normalize_ticket_path(raw)
    if not TICKET_PATH_RE.fullmatch(path):
        return None, f"`ticket_source: {raw}` bukan path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md`"
    return posixpath.dirname(path), ""


def run_taskdir(args, root: Path, config: Dict[str, str]) -> int:
    verdict = check_taskdir(root, args.taskdir)
    if not verdict.ok:
        return ns.emit_fail(args.json, PREFIX, [verdict.summary])
    td, repo = verdict.rel, ns.repo_identity(root, config)
    docs, texts, problems = select_taskdir(root, td, repo)
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    task_text = texts.get("TASK.md")
    if task_text is None:
        return ns.emit_fail(args.json, PREFIX, [f"{td}/TASK.md belum ter-commit — akar belum terkunci"])
    if args.remote is not None:
        return diff_phase(args, config, docs, lambda remote: mirrored_extras(
            root, "workdir", remote, docs, lambda key: f"{td}/{key}" if "/" not in key else "", repo))
    tkey, problem = ticket_key(task_text)
    if problem:
        return ns.emit_fail(args.json, PREFIX, [problem])
    key, name = f"{SOURCE}:{repo}:{td}", posixpath.basename(td)
    kinds = {d["key"]: d["type"] for d in docs}
    briefs = [ns.frontmatter_value(texts[k], "status") for k, t in kinds.items() if t == "BRIEF"]
    done = "REPORT.md" in kinds
    blocked = "HALT.md" in kinds or "BLOCKED" in briefs
    started = done or any(s in STARTED for s in briefs) or any(
        t in ("UNIT_REPORT", "HALT", "REVIEW") for t in kinds.values())
    status = "done" if done else "blocked" if blocked else "active"
    problems = ns.workdir_problems(key, name, status)
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    ident = {"source": "analyst", "ticket_key": tkey} if tkey else {"source": SOURCE, "workdir_key": key}
    title = ns.h1_title(task_text) or name
    task = ns.task_args(config, ident, repo, title, ns.pick_sections(task_text, TASK_SECTIONS) or title)
    # Task tiket bisa menaungi taskdir frontend juga: plugin ini hanya menaikkannya ke `in_progress` (E8).
    task["status"] = ns.task_status("done" if done and not tkey else "in_progress" if started else "")
    meta = {"source": SOURCE, "repo": repo, "path": td, "lane": ns.frontmatter_value(task_text, "lane"),
            "chain": ns.frontmatter_value(task_text, "chain"), "risk": ns.frontmatter_value(task_text, "risk"),
            "ticket_key": tkey or ""}
    payload = {"status": "PASS", "enabled": True, "mcp_server": config["mcp_server"], "repo": repo, "task": task,
               "workdir": ns.workdir_args(config, key, name, status, {k: v for k, v in meta.items() if v}),
               "list_document": {"reference_table": "workdir", "include_content": False},
               "documents_total": len(docs)}
    ns.emit(payload, args.json, f"{PREFIX} PASS: {td} · workdir {name} ({status}) · {len(docs)} dokumen · server "
                                f"{config['mcp_server']} — argumen tool lewat `--json`")
    return 0


def run_repo_docs(args, root: Path, config: Dict[str, str]) -> int:
    repo = ns.repo_identity(root, config)
    rel_dir, docs, problems = select_repo_docs(root, args.repo_docs, repo)
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    prefix = f"{repo}/{rel_dir}/"
    if args.remote is not None:
        return diff_phase(args, config, docs, lambda remote: mirrored_extras(
            root, "workspace", remote, docs, lambda key: key[len(repo) + 1:] if key.startswith(prefix) else "", repo))
    payload = {"status": "PASS", "enabled": True, "mcp_server": config["mcp_server"], "repo": repo,
               "workspace_id": config["workspace_id"],
               "list_document": {"reference_table": "workspace", "include_content": False,
                                 "metadata": ns.compact({"source": SOURCE, "repo": repo})},
               "documents_total": len(docs)}
    ns.emit(payload, args.json, f"{PREFIX} PASS: {rel_dir}/ · {len(docs)} dokumen → workspace "
                                f"{config['workspace_id'] or '-'} — argumen tool lewat `--json`")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Argumen tool MCP nataflow untuk artefak backend (read-only)")
    target = ap.add_mutually_exclusive_group(required=True)
    target.add_argument("--taskdir", help="backenddev/docs/<YYMMDDhhmm>-<slug>")
    target.add_argument("--repo-docs", dest="repo_docs", choices=sorted(REPO_DOCS),
                        help="dokumen tingkat repo: audit, api, atau profile")
    ap.add_argument("--remote", default=None, help="teks balikan list_document include_content=false (`-` = stdin)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = find_repo_root()
    config, problems = ns.load_config(root)
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    if config is None:
        return ns.emit_skip(args.json, PREFIX)
    return run_taskdir(args, root, config) if args.taskdir else run_repo_docs(args, root, config)


if __name__ == "__main__":
    sys.exit(cli(main))
