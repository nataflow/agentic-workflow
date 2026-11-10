#!/usr/bin/env python3
"""Argumen tool MCP nataflow untuk satu taskdir frontend atau dokumen tingkat repo (15 F2, F9, F11–F13).

Tidak menulis berkas dan tidak meng-commit (D5), sehingga materai approve (kejadian `approve` di
`## Riwayat Rantai`) tidak tersentuh. Prosedur `lead/references/nataflow-sync.md` memakai `--push` (29 S3): skrip
sendiri memanggil tool server lewat `nataflow_client` dengan MCP key `.claude/nataflow.local.json`, lalu mencetak satu
baris segmen — isi dokumen tidak pernah lewat konteks model. Tanpa `--push` keluarannya argumen tool per fase.
Sengaja bukan subperintah `chain.py`: `chain.py` satu-satunya penulis ledger, sedangkan sinkron hanya membaca.

- `--taskdir <td>`: workdir `frontenddev:<repo>:<td>` tertaut ke task tiket analyst (`ticket_source`) atau ke task
  baru ber-`workdir_key`. Dokumen taskdir tidak di-commit (Langkah 24), jadi isinya diambil dari disk (24 K14).
  `TASK.md` selalu, asal akarnya terkunci (`base_commit`); `FLOW.md`/`UI.md`/`CONTRACT.md` hanya bila baris
  ledger-nya `[x]` dan sah (`verify_chain_row`, definisi "stabil" yang sama dengan gerbang); brief dan
  `REVIEW-PLAN.md` bila hop BRIEF `[x]` sah, atau brief sudah `DONE`/`BLOCKED`; `report-NN.md`, `REVIEW.md`, dan
  `REPORT.md` apa adanya; `.explore/` tidak pernah. Metadata `commit` kosong, `head` = sha `HEAD` saat sinkron.
  Status workdir dari `taskdir_state.py`: `TUNTAS` → `done`, `DITUTUP` → `abandoned`, `TERHENTI`/`TEMUAN` →
  `blocked`, selain itu `active`. Task naik ke `in_progress` sejak workdir terbit (28 T1); task milik taskdir ini
  `done`/`cancelled` mengikuti workdir, task tiket hanya lewat `--workdirs` (28 T2).
- `--repo-docs review|profile`: `frontenddev/reviews/` atau profil sebagai dokumen `adhoc.review`/`profile` di bawah
  workspace, dengan key `<repo>/<path>` (T10).

Workspace (`--workspace <alias>`, dari `workspaces` config): `task.lookup` menjangkau seluruh project key, sehingga task
tiket analyst ditemukan di workspace mana pun user memilihnya; workdir mengikuti workspace task induknya (diisi model
dari balikan tool). Pilihan hanya dibutuhkan untuk task baru dan induk dokumen repo: config berisi lebih dari satu
workspace tanpa `--workspace` → `workspace_choices`, user memilih, lalu skrip dijalankan ulang dengan `--workspace`.

Tanpa `--remote`: argumen task, workdir, dan manifest, tanpa isi dokumen. `--remote -`: dokumen yang berbeda dari
teks balikan `list_document include_content=false` di stdin, ditambah key remote yang tidak lagi terpilih (E7): hop
yang dibuka ulang didorong dari disk dengan status terbarunya (F9); berkas taskdir yang sudah tidak ada dibiarkan
dengan isi terakhirnya di server (24 G5), sedangkan dokumen repo yang dihapus dari git didorong dengan
`removed: true`. Hop yang DRIFT tidak pernah didorong ulang: cermin tetap menampilkan isi yang disetujui.

`--workdirs -`: teks balikan `list_workdir task_id` di stdin, hanya bila payload fase pertama membawa
`task.siblings` (task tiket, workdir `done`/`abandoned`) → `task_status` pengganti `task.status`: `done` bila seluruh
workdir di bawah task itu sudah `done`/`abandoned` dan sedikitnya satu `done`, selain itu tetap `task.status` (28 T2).

Keluaran `--json` selalu JSON: `SKIP` (config absen), `FAIL` (`problems`), atau `PASS`; dengan `--push` juga
`PILIH_WORKSPACE` (`workspace_choices`), selalu beserta `segment`. Exit 1 hanya untuk `FAIL`.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nataflow_sync as ns  # noqa: E402
from docs_git import head_sha  # noqa: E402
from precondition_lib import (  # noqa: E402
    PROFILE_DIR_REL,
    TASKDIR_PATTERN,
    TICKET_PATH_RE,
    cli,
    find_repo_root,
    normalize_taskdir,
    normalize_ticket_path,
    read_chain,
    verify_chain_row,
)

SOURCE = "frontenddev"
PREFIX = "SYNC-PAYLOAD"
TASKDIR_STATE = Path(__file__).resolve().parents[1] / "lead" / "scripts" / "taskdir_state.py"
FIXED_TYPES = {"TASK.md": "task", "FLOW.md": "flow", "UI.md": "ui", "CONTRACT.md": "contract",
               "REVIEW-PLAN.md": "review.plan", "REVIEW.md": "review", "REPORT.md": "report"}
ROW_DOCS = {"FLOW": "FLOW.md", "UI": "UI.md", "CONTRACT": "CONTRACT.md"}
BRIEF_NAME = re.compile(r"^brief-\d{2}-[a-z0-9-]+\.md$")
UNIT_REPORT = re.compile(r"^report-\d{2}\.md$")
WORKDIR_STATUS = {"TUNTAS": "done", "DITUTUP": "abandoned", "TERHENTI": "blocked", "TEMUAN": "blocked"}
REPO_DOCS = {"review": ("frontenddev/reviews", "adhoc.review"), "profile": (PROFILE_DIR_REL, "profile")}
TASK_SECTIONS = ("Description", "Success Criteria", "Out of Scope")


def doc_type(name: str) -> str:
    if name in FIXED_TYPES:
        return FIXED_TYPES[name]
    return "brief" if BRIEF_NAME.match(name) else "unit.report" if UNIT_REPORT.match(name) else ""


def doc_status(text: str) -> str:
    return ns.frontmatter_value(text, "status") or ns.frontmatter_value(text, "verdict")


def build_doc(root: Path, table: str, key: str, rel: str, doc_type_: str, text: str, repo: str,
              removed_commit: str = "") -> Dict[str, Any]:
    """Dokumen tingkat repo (ter-commit): metadata `commit` = commit terakhir berkasnya."""
    commit = removed_commit or ns.last_commit(root, rel)
    meta = ns.doc_meta(SOURCE, repo, rel, doc_status(text), commit, removed=bool(removed_commit))
    return ns.document(table, key, doc_type_, text, meta)


def build_disk_doc(key: str, rel: str, doc_type_: str, text: str, repo: str, head: str) -> Dict[str, Any]:
    """Dokumen taskdir (di disk, tidak di-commit): metadata `commit` kosong, `head` = `HEAD` saat sinkron (24 K14)."""
    meta = ns.doc_meta(SOURCE, repo, rel, doc_status(text), "", head=head)
    return ns.document("workdir", key, doc_type_, text, meta)


def taskdir_files(root: Path, td: str) -> List[str]:
    """Nama berkas langsung di bawah taskdir di disk (tanpa subdirektori), terurut."""
    path = root / td
    return sorted(p.name for p in path.iterdir() if p.is_file()) if path.is_dir() else []


def ledger(root: Path, td: str, task_text: str) -> Tuple[Set[str], Set[str]]:
    """(baris `[x]` yang sah, berkas hop yang DRIFT dan karenanya ditahan dari cermin)."""
    stable, drift = set(), set()
    for entry in read_chain(task_text):
        if entry["mark"] != "x":
            continue
        if verify_chain_row(root, td, entry):
            drift.add(ROW_DOCS.get(entry["row"], entry["row"]))
        else:
            stable.add(entry["row"])
    return stable, drift


def select_taskdir(root: Path, td: str, repo: str, head: str):
    """Dokumen terpilih dari disk, isi per nama berkas, berkas yang ditahan (DRIFT), dan masalah."""
    texts: Dict[str, str] = {}
    problems: List[str] = []
    for name in taskdir_files(root, td):
        if not doc_type(name):
            continue
        text, problem = ns.disk_text(root / td / name)
        if problem:
            problems.append(f"{td}/{problem}")
        elif text is not None:
            texts[name] = text
    if problems or "TASK.md" not in texts:
        return [], texts, set(), problems
    stable, drift = ledger(root, td, texts["TASK.md"])
    docs = []
    for name, text in texts.items():
        kind = doc_type(name)
        row = next((r for r, doc in ROW_DOCS.items() if doc == name), "")
        if row and row not in stable:
            continue
        if kind in ("brief", "review.plan") and "BRIEF" not in stable and doc_status(text) not in ("DONE", "BLOCKED"):
            continue
        docs.append(build_disk_doc(name, f"{td}/{name}", kind, text, repo, head))
    held = drift | ({n for n in texts if doc_type(n) == "brief"} if "BRIEF" in drift else set())
    return docs, texts, held, []


def select_repo_docs(root: Path, kind: str, repo: str) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    rel_dir, doc_type_ = REPO_DOCS[kind]
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


def disk_extras(root: Path, remote: Dict[str, Dict[str, Any]], chosen: List[Dict[str, Any]], td: str, repo: str,
                head: str, held: Set[str]) -> List[Dict[str, Any]]:
    """Key remote taskdir yang tidak lagi terpilih tetap dicerminkan (E7) bila berkasnya masih di disk, dengan isi
    dan status terbarunya (mis. hop yang dibuka ulang), kecuali berkas yang ditahan karena DRIFT. Berkas yang sudah
    tidak ada tidak didorong (24 G5)."""
    chosen_keys = {d["key"] for d in chosen}
    extras = []
    for key in sorted(set(remote) - chosen_keys - held):
        if "/" in key:
            continue
        text, _ = ns.disk_text(root / td / key)
        if text is None:
            continue
        kind = ns.remote_type(remote[key]["type"]) or doc_type(key) or "doc"
        extras.append(build_disk_doc(key, f"{td}/{key}", kind, text, repo, head))
    return extras


def mirrored_extras(root: Path, table: str, remote: Dict[str, Dict[str, Any]], chosen: List[Dict[str, Any]],
                    key_to_rel, repo: str, held: Set[str]) -> List[Dict[str, Any]]:
    """Key remote dokumen repo yang tidak lagi terpilih tetap dicerminkan (E7): isi `HEAD` terbaru, atau versi
    terakhir sebelum dihapus dengan `removed: true`."""
    chosen_keys = {d["key"] for d in chosen}
    extras = []
    for key in sorted(set(remote) - chosen_keys - held):
        rel = key_to_rel(key)
        if not rel:
            continue
        kind = ns.remote_type(remote[key]["type"]) or doc_type(posixpath.basename(rel)) or "doc"
        text, _ = ns.head_text(root, rel)
        if text is not None:
            extras.append(build_doc(root, table, key, rel, kind, text, repo))
            continue
        text, sha = ns.removed_text(root, rel)
        if text is not None:
            extras.append(build_doc(root, table, key, rel, kind, text, repo, removed_commit=sha))
    return extras


def diff_result(docs: List[Dict[str, Any]], extras_fn, text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Teks balikan `list_document` → dokumen yang perlu didorong (fase `--remote`)."""
    remote, problems = ns.parse_remote(text) if text.strip() else (None, [
        "--remote kosong — serahkan teks balikan list_document (larik kosong `[]` bila tidak ada)"])
    if problems:
        return None, problems
    docs = docs + extras_fn(remote)
    problems = ns.check_documents(docs)
    if problems:
        return None, problems
    push, same = ns.split_remote(docs, remote)
    return {"documents": push, "same": same, "documents_total": len(docs)}, []


def taskdir_state(root: Path, td: str) -> Tuple[str, str]:
    """Keadaan `taskdir_state.py` (subproses, pola pemanggilan lintas skill yang sudah ada) → `(state, masalah)`."""
    try:
        proc = subprocess.run([sys.executable, str(TASKDIR_STATE), "--taskdir", td, "--root", str(root), "--json"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=120)
        rows = json.loads(proc.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return "", f"taskdir_state.py tidak terbaca ({exc})"
    if not isinstance(rows, list) or not rows:
        return "", f"taskdir_state.py: {rows.get('error', 'tanpa hasil') if isinstance(rows, dict) else 'tanpa hasil'}"
    return str(rows[0].get("state", "")), ""


def siblings_result(key: str, status: str, task: Dict[str, Any], text: str
                    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Teks balikan `list_workdir` → status task tiket dari seluruh workdir di bawahnya (28 T2). Tanpa
    `task.siblings` → `task.status`."""
    workdirs, problems = ns.parse_workdirs(text) if text.strip() else (None, [
        "--workdirs kosong — serahkan teks balikan list_workdir apa adanya"])
    if problems:
        return None, problems
    target, problems = (ns.sibling_task_status(workdirs, key, status, task["status"]) if task.get("siblings")
                        else (task["status"], []))
    if problems:
        return None, problems
    open_ = sum(1 for k, s in workdirs.items() if (status if k == key else s) not in ns.WORKDIR_FINAL)
    return {"task_status": target, "workdirs_total": len(workdirs), "workdirs_open": open_}, []


def emit_phase(args, config: Dict[str, Any], fn, flag: str, source: str, line) -> int:
    """Jalur `--remote`/`--workdirs`: teks balikan tool dari stdin/berkas → payload fase."""
    text, problems = ns.read_tool_text(flag, source, sys.stdin.read() if source == "-" else "")
    result, problems = (None, problems) if problems else fn(text)
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    ns.emit(dict({"status": "PASS", "enabled": True, "url": config["url"]}, **result), args.json, line(result))
    return 0


def diff_line(result: Dict[str, Any]) -> str:
    return (f"{PREFIX} PASS: {len(result['documents'])} dokumen perlu didorong, {result['same']} sama — argumen "
            f"lewat `--json`")


def siblings_line(result: Dict[str, Any]) -> str:
    target = result["task_status"]
    return (f"{PREFIX} PASS: {result['workdirs_total']} workdir di bawah task, {result['workdirs_open']} belum tuntas "
            f"→ task {target['status'] if target else 'tidak diubah'} — argumen lewat `--json`")


def ticket_key(task_text: str) -> Tuple[Optional[str], str]:
    """`ticket_source` frontmatter → `ticket_key` analyst (dirname path `TICKET.md`), `None` tanpa tiket."""
    raw = ns.frontmatter_value(task_text, "ticket_source")
    if not raw:
        return None, ""
    path = normalize_ticket_path(raw)
    if not TICKET_PATH_RE.fullmatch(path):
        return None, f"`ticket_source: {raw}` bukan path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md`"
    return posixpath.dirname(path), ""


def taskdir_plan(args, root: Path, config: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Seluruh fase taskdir: `diff` (dokumen, tersedia lebih dulu) dan `phase1()` → `(payload, siblings, masalah)`."""
    td = normalize_taskdir(args.taskdir)
    if not TASKDIR_PATTERN.match(td) or not (root / td).is_dir():
        return None, [f"`{td}` bukan taskdir frontenddev/docs/<YYMMDDhhmm>-<slug> yang ada"]
    repo, head = ns.repo_identity(root, config), head_sha(root)
    docs, texts, held, problems = select_taskdir(root, td, repo, head)
    if problems:
        return None, problems
    task_text = texts.get("TASK.md")
    if task_text is None or not ns.frontmatter_value(task_text, "base_commit"):
        return None, [f"{td}/TASK.md tanpa `base_commit` — akar belum terkunci"]

    def diff(text: str):
        return diff_result(docs, lambda remote: disk_extras(root, remote, docs, td, repo, head, held), text)

    def phase1():
        tkey, problem = ticket_key(task_text)
        if problem:
            return None, None, [problem]
        state, problem = taskdir_state(root, td)
        if problem:
            return None, None, [problem]
        key, name = f"{SOURCE}:{repo}:{td}", posixpath.basename(td)
        status = WORKDIR_STATUS.get(state, "active")
        problems = ns.workdir_problems(key, name, status)
        if problems:
            return None, None, problems
        ident = {"source": "analyst", "ticket_key": tkey} if tkey else {"source": SOURCE, "workdir_key": key}
        title = ns.h1_title(task_text) or name
        task = ns.task_args(config, args.workspace_id, ident, repo, title,
                            ns.pick_sections(task_text, TASK_SECTIONS) or title)
        # Workdir terbit → `in_progress` (28 T1). Task tiket bisa menaungi taskdir backend juga (15 E8): ia baru
        # `done` bila seluruh workdir di bawahnya tuntas, diputuskan dari balikan `list_workdir` (28 T2).
        target = "in_progress"
        if not tkey and status == "done":
            target = "done"
        elif not tkey and status == "abandoned":
            target = "cancelled"
        task["status"] = ns.task_status(target)
        if tkey and status in ns.WORKDIR_FINAL:
            task["siblings"] = True
        meta = {"source": SOURCE, "repo": repo, "path": td, "lane": ns.frontmatter_value(task_text, "lane"),
                "sections": ns.frontmatter_value(task_text, "sections"), "state": state, "ticket_key": tkey or ""}
        payload = {"status": "PASS", "enabled": True, "url": config["url"], "repo": repo,
                   **ns.workspace_fields(args.workspace_id, args.workspace_choices), "task": task,
                   "workdir": ns.workdir_args(key, name, status, {k: v for k, v in meta.items() if v}),
                   "list_document": {"reference_table": "workdir", "include_content": False},
                   "documents_total": len(docs)}
        return payload, (lambda text: siblings_result(key, status, task, text)), []

    return {"td": td, "diff": diff, "phase1": phase1}, []


def run_taskdir(args, root: Path, config: Dict[str, Any]) -> int:
    plan, problems = taskdir_plan(args, root, config)
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    if args.remote is not None:
        return emit_phase(args, config, plan["diff"], "--remote", args.remote, diff_line)
    payload, siblings, problems = plan["phase1"]()
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    if args.workdirs is not None:
        return emit_phase(args, config, siblings, "--workdirs", args.workdirs, siblings_line)
    wd = payload["workdir"]
    state = json.loads(wd["metadata"]).get("state", "")
    ns.emit(payload, args.json, f"{PREFIX} PASS: {plan['td']} · workdir {wd['name']} ({wd['status']}, {state}) · "
                                f"{payload['documents_total']} dokumen · server {config['url']} — argumen tool lewat "
                                f"`--json`")
    return 0


def workspace_label(args) -> str:
    if args.workspace_choices:
        return "pilih: " + ", ".join(c["alias"] for c in args.workspace_choices)
    return args.workspace_id or "-"


def repo_docs_plan(args, root: Path, config: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    repo = ns.repo_identity(root, config)
    rel_dir, docs, problems = select_repo_docs(root, args.repo_docs, repo)
    if problems:
        return None, problems
    prefix = f"{repo}/{rel_dir}/"

    def diff(text: str):
        return diff_result(docs, lambda remote: mirrored_extras(
            root, "workspace", remote, docs, lambda key: key[len(repo) + 1:] if key.startswith(prefix) else "",
            repo, set()), text)

    payload = {"status": "PASS", "enabled": True, "url": config["url"], "repo": repo,
               **ns.workspace_fields(args.workspace_id, args.workspace_choices),
               "list_document": {"reference_table": "workspace", "include_content": False,
                                 "metadata": ns.compact({"source": SOURCE, "repo": repo})},
               "documents_total": len(docs)}
    return {"rel_dir": rel_dir, "diff": diff, "payload": payload}, []


def run_repo_docs(args, root: Path, config: Dict[str, Any]) -> int:
    if args.workdirs is not None:
        return ns.emit_fail(args.json, PREFIX, ["--workdirs hanya untuk --taskdir"])
    plan, problems = repo_docs_plan(args, root, config)
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    if args.remote is not None:
        return emit_phase(args, config, plan["diff"], "--remote", args.remote, diff_line)
    ns.emit(plan["payload"], args.json, f"{PREFIX} PASS: {plan['rel_dir']}/ · {plan['payload']['documents_total']} "
                                        f"dokumen → workspace {workspace_label(args)} — argumen tool lewat `--json`")
    return 0


def push(args, root: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """`--push`: seluruh fase dijalankan skrip ini sendiri terhadap server (29 S3)."""
    if args.taskdir:
        plan, problems = taskdir_plan(args, root, config)
        if problems:
            return ns.push_fail(problems)
        payload, siblings, problems = plan["phase1"]()
        if problems:
            return ns.push_fail(problems)
        return ns.run_push(root, config, lambda s: ns.push_workdir(s, payload, plan["diff"], siblings))
    plan, problems = repo_docs_plan(args, root, config)
    if problems:
        return ns.push_fail(problems)
    return ns.run_push(root, config, lambda s: ns.push_repo_docs(s, plan["payload"], plan["diff"]))


def main() -> int:
    ap = argparse.ArgumentParser(description="Sinkron nataflow untuk artefak frontend (tanpa menulis berkas)")
    target = ap.add_mutually_exclusive_group(required=True)
    target.add_argument("--taskdir", help="frontenddev/docs/<YYMMDDhhmm>-<slug>")
    target.add_argument("--repo-docs", dest="repo_docs", choices=sorted(REPO_DOCS),
                        help="dokumen tingkat repo: review atau profile")
    ap.add_argument("--workspace", default="", help="alias `workspaces` tujuan task baru atau induk dokumen repo; "
                                                    "wajib dipilih user bila config berisi lebih dari satu workspace")
    phase = ap.add_mutually_exclusive_group()
    phase.add_argument("--push", action="store_true", help="kirim langsung ke server lewat MCP key lokal; keluaran "
                                                           "satu baris segmen")
    phase.add_argument("--remote", default=None, help="teks balikan list_document include_content=false (`-` = stdin)")
    phase.add_argument("--workdirs", default=None, help="teks balikan list_workdir task_id (`-` = stdin), bila payload "
                                                        "membawa task.siblings")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = find_repo_root().resolve()
    config, problems = ns.load_config(root)
    if not problems and config is not None:
        args.workspace_id, args.workspace_choices, problems = ns.choose_workspace(config, args.workspace)
    if args.push:
        result = (ns.push_fail(problems) if problems else {"status": "SKIP"} if config is None
                  else push(args, root, config))
        what = "repo" if args.repo_docs else f"workdir {result.get('workdir', '')}"
        return ns.emit_push(result, args.json, "nataflow " + ns.push_segment(result, what))
    if problems:
        return ns.emit_fail(args.json, PREFIX, problems)
    if config is None:
        return ns.emit_skip(args.json, PREFIX)
    return run_taskdir(args, root, config) if args.taskdir else run_repo_docs(args, root, config)


if __name__ == "__main__":
    sys.exit(cli(main))
