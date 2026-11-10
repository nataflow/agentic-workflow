"""Server MCP nataflow palsu untuk tes sinkron `--push` (langkah 29).

`FakeMCP` adalah server HTTP Streamable MCP bersesi di `127.0.0.1` (thread latar): `initialize` menerbitkan
`Mcp-Session-Id`, setiap permintaan sesudahnya wajib membawanya beserta `Authorization: Bearer <key>`. Tool
didaftarkan sebagai fungsi `args -> objek JSON`; `ToolError` menjadi hasil `isError`. `Nataflow` memasang model
keadaan server (task, workdir, dokumen, artifact) dengan semantik yang dipakai sinkron: saringan metadata
containment, upsert dokumen `created`/`updated`/`unchanged`, dan status task.

Semua panggilan tool tercatat di `calls` (`(nama, argumen)`), supaya tes bisa membuktikan bahwa jalur gagal tidak
memanggil tool tulis apa pun.
"""
import hashlib
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple

KEY = "nfk_tes_rahasia_0123456789"
WRITE_TOOLS = {"create_task", "update_task", "update_task_status", "upsert_workdir", "upsert_document",
               "create_document", "upsert_artifact"}


class ToolError(Exception):
    """Galat tool: dikirim sebagai hasil `isError` dengan pesan ini."""


class FakeMCP:
    def __init__(self, key: str = KEY, sse: bool = False):
        self.key = key
        self.sse = sse
        self.tools: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.calls: List[Tuple[str, Dict[str, Any]]] = []
        self.requests: List[Dict[str, Any]] = []
        self.sessions: set = set()
        self.expire_next = False          # permintaan bersesi berikutnya dijawab 404 (sesi kedaluwarsa)
        self.status_override: Optional[int] = None
        self._server: Optional[ThreadingHTTPServer] = None

    # ── siklus ───────────────────────────────────────────────────────────────

    def __enter__(self) -> "FakeMCP":
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_a: Any) -> None:
                pass

            def do_DELETE(self) -> None:
                fake.sessions.discard(self.headers.get("Mcp-Session-Id"))
                self.send_response(200)
                self.end_headers()

            def do_POST(self) -> None:
                fake._handle(self)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *_exc: Any) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/mcp"

    def tool_names(self) -> List[str]:
        return [name for name, _ in self.calls]

    def writes(self) -> List[str]:
        return [name for name, _ in self.calls if name in WRITE_TOOLS]

    # ── HTTP ─────────────────────────────────────────────────────────────────

    def _reply(self, h: BaseHTTPRequestHandler, code: int, body: Any = None, headers: Optional[Dict[str, str]] = None):
        h.send_response(code)
        for k, v in (headers or {}).items():
            h.send_header(k, v)
        if body is None:
            h.send_header("Content-Length", "0")
            h.end_headers()
            return
        if self.sse:
            payload = ("event: message\ndata: " + json.dumps(body) + "\n\n").encode()
            h.send_header("Content-Type", "text/event-stream")
        else:
            payload = json.dumps(body).encode()
            h.send_header("Content-Type", "application/json")
        h.send_header("Content-Length", str(len(payload)))
        h.end_headers()
        h.wfile.write(payload)

    def _handle(self, h: BaseHTTPRequestHandler) -> None:
        raw = h.rfile.read(int(h.headers.get("Content-Length") or 0))
        body = json.loads(raw)
        self.requests.append({"headers": dict(h.headers), "body": body})
        if self.status_override:
            return self._reply(h, self.status_override, {"error": "dipaksa tes"})
        if h.headers.get("Authorization") != "Bearer " + self.key:
            return self._reply(h, 401, {"error": "unauthorized"})
        method = body.get("method")
        if method == "initialize":
            sid = uuid.uuid4().hex
            self.sessions.add(sid)
            result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}},
                      "serverInfo": {"name": "fake-nataflow", "version": "0"}}
            return self._reply(h, 200, {"jsonrpc": "2.0", "id": body["id"], "result": result},
                               {"Mcp-Session-Id": sid})
        sid = h.headers.get("Mcp-Session-Id")
        if self.expire_next and sid:
            self.expire_next = False
            self.sessions.discard(sid)
        if sid not in self.sessions:
            return self._reply(h, 404, {"error": "session not found"})
        if "id" not in body:
            return self._reply(h, 202)
        if method != "tools/call":
            return self._reply(h, 200, {"jsonrpc": "2.0", "id": body["id"],
                                        "error": {"code": -32601, "message": f"method {method} not found"}})
        name, args = body["params"]["name"], body["params"].get("arguments") or {}
        self.calls.append((name, args))
        fn = self.tools.get(name)
        if fn is None:
            return self._reply(h, 200, {"jsonrpc": "2.0", "id": body["id"],
                                        "error": {"code": -32602, "message": f"tool '{name}' not found"}})
        try:
            out = fn(args)
            result = {"content": [{"type": "text", "text": out if isinstance(out, str) else json.dumps(out)}]}
        except ToolError as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        return self._reply(h, 200, {"jsonrpc": "2.0", "id": body["id"], "result": result})


# ── Model keadaan server ─────────────────────────────────────────────────────

def _meta(text: Any) -> Dict[str, Any]:
    if not text:
        return {}
    return json.loads(text) if isinstance(text, str) else dict(text)


def _contains(stored: Dict[str, Any], want: Dict[str, Any]) -> bool:
    return all(stored.get(k) == v for k, v in want.items())


class Nataflow:
    """Model server: `ws` = workspace milik key (default), `project` = project milik key."""

    def __init__(self, fake: FakeMCP, workspaces: Optional[List[str]] = None):
        self.fake = fake
        self.project = {"id": str(uuid.uuid4()), "name": "Proyek Tes", "description": ""}
        self.workspaces = workspaces or [str(uuid.uuid4())]
        self.tasks: List[Dict[str, Any]] = []
        self.workdirs: List[Dict[str, Any]] = []
        self.docs: List[Dict[str, Any]] = []
        for name in ("list_task", "create_task", "update_task", "update_task_status", "upsert_workdir",
                     "list_workdir", "list_document", "upsert_document", "create_document", "get_document",
                     "get_project_info", "list_workspace", "list_artifacts", "get_artifact", "upsert_artifact"):
            fake.tools[name] = getattr(self, name)

    # task
    def _task_view(self, t: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": t["id"], "code": t["code"], "title": t["title"], "status": t["status"],
                "workspace": {"id": t["workspace_id"], "name": "ws"}}

    def add_task(self, metadata: Dict[str, Any], status: str = "todo", workspace_id: str = "") -> Dict[str, Any]:
        t = {"id": str(uuid.uuid4()), "code": len(self.tasks) + 1, "title": "lama", "description": "",
             "status": status, "workspace_id": workspace_id or self.workspaces[0], "metadata": metadata}
        self.tasks.append(t)
        return t

    def list_task(self, args: Dict[str, Any]) -> Any:
        want = _meta(args.get("metadata"))
        return [self._task_view(t) for t in self.tasks if _contains(t["metadata"], want)
                and (not args.get("status") or t["status"] == args["status"])]

    def create_task(self, args: Dict[str, Any]) -> Any:
        ws = args.get("workspace_id") or ""
        if not ws:
            if len(self.workspaces) != 1:
                raise ToolError("workspace_id is required for a project-scoped key")
            ws = self.workspaces[0]
        t = self.add_task(_meta(args.get("metadata")), workspace_id=ws)
        t.update(title=args["title"], description=args["description"], pic_id=args.get("pic_id", ""))
        return self._task_view(t)

    def _task(self, task_id: str) -> Dict[str, Any]:
        for t in self.tasks:
            if t["id"] == task_id:
                return t
        raise ToolError("task not found")

    def update_task(self, args: Dict[str, Any]) -> Any:
        t = self._task(args["task_id"])
        for k in ("title", "description"):
            if args.get(k):
                t[k] = args[k]
        if args.get("metadata"):
            t["metadata"] = _meta(args["metadata"])
        return self._task_view(t)

    def update_task_status(self, args: Dict[str, Any]) -> Any:
        t = self._task(args["task_id"])
        t["status"] = args["status"]
        return self._task_view(t)

    # workdir
    def upsert_workdir(self, args: Dict[str, Any]) -> Any:
        ws = args.get("workspace_id") or self.workspaces[0]
        for w in self.workdirs:
            if w["workspace_id"] == ws and w["key"] == args["key"]:
                action = "updated"
                break
        else:
            w = {"id": str(uuid.uuid4()), "workspace_id": ws, "key": args["key"]}
            self.workdirs.append(w)
            action = "created"
        w.update(name=args["name"], status=args.get("status") or w.get("status") or "active",
                 task_id=args.get("task_id") or w.get("task_id"), metadata=_meta(args.get("metadata")))
        return {"action": action, "id": w["id"], "name": w["name"], "key": w["key"], "slug": w["name"], "task": None}

    def list_workdir(self, args: Dict[str, Any]) -> Any:
        return [{"id": w["id"], "workspace_id": w["workspace_id"], "key": w["key"], "name": w["name"],
                 "status": w["status"], "task_id": w["task_id"]} for w in self.workdirs
                if (not args.get("task_id") or w["task_id"] == args["task_id"])
                and (not args.get("workspace_id") or w["workspace_id"] == args["workspace_id"])]

    # dokumen
    def _doc_view(self, d: Dict[str, Any], content: bool = False) -> Dict[str, Any]:
        view = {"id": d["id"], "reference_table": d["reference_table"], "reference_id": d["reference_id"],
                "key": d["key"], "title": d.get("title"), "type": d["type"], "mimetype": d["mimetype"],
                "content_sha256": d["content_sha256"], "metadata": d["metadata"]}
        if content:
            view["content"] = d["content"]
        return view

    def _find(self, table: str, ref: str, key: str) -> Optional[Dict[str, Any]]:
        for d in self.docs:
            if (d["reference_table"], d["reference_id"], d["key"]) == (table, ref, key):
                return d
        return None

    def add_doc(self, table: str, ref: str, key: str, doc_type: str, content: str, metadata: Dict[str, Any],
                mimetype: str = "text/markdown", title: str = "") -> Dict[str, Any]:
        d = {"id": str(uuid.uuid4()), "reference_table": table, "reference_id": ref, "key": key, "type": doc_type,
             "content": content, "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
             "metadata": metadata, "mimetype": mimetype, "title": title or key}
        self.docs.append(d)
        return d

    def list_document(self, args: Dict[str, Any]) -> Any:
        want = _meta(args.get("metadata"))
        return [self._doc_view(d, bool(args.get("include_content"))) for d in self.docs
                if d["reference_table"] == args["reference_table"] and d["reference_id"] == args["reference_id"]
                and (not args.get("type") or d["type"] == args["type"]) and _contains(d["metadata"], want)]

    def _write(self, args: Dict[str, Any], doc_type: str, mimetype: str) -> Any:
        content = args["content"]
        sha = hashlib.sha256(content.encode()).hexdigest()
        if args.get("content_sha256") and args["content_sha256"] != sha:
            raise ToolError("content_sha256 does not match content")
        meta = _meta(args.get("metadata"))
        d = self._find(args["reference_table"], args["reference_id"], args["key"])
        if d is None:
            d = self.add_doc(args["reference_table"], args["reference_id"], args["key"], doc_type, content, meta,
                             mimetype, args.get("title", ""))
            action = "created"
        elif (d["content_sha256"], d["type"], d["metadata"], d["mimetype"]) == (sha, doc_type, meta, mimetype):
            action = "unchanged"
        else:
            d.update(content=content, content_sha256=sha, type=doc_type, metadata=meta, mimetype=mimetype)
            action = "updated"
        return {"action": action, "id": d["id"], "reference_id": d["reference_id"],
                "reference_table": d["reference_table"], "title": d["title"]}

    def upsert_document(self, args: Dict[str, Any]) -> Any:
        return self._write(args, args["type"], "text/markdown")

    def create_document(self, args: Dict[str, Any]) -> Any:
        key = "-".join(args["title"].lower().split())
        if self._find(args["reference_table"], args["reference_id"], key):
            raise ToolError("document title already exists")
        d = self.add_doc(args["reference_table"], args["reference_id"], key, args["type"], args["content"],
                         _meta(args.get("metadata")), title=args["title"])
        return {"id": d["id"], "reference_id": d["reference_id"], "reference_table": d["reference_table"],
                "title": d["title"]}

    def get_document(self, args: Dict[str, Any]) -> Any:
        d = self._find(args["reference_table"], args["reference_id"], args["key"])
        if d is None:
            raise ToolError("document not found")
        return self._doc_view(d, True)

    # project & workspace
    def get_project_info(self, _args: Dict[str, Any]) -> Any:
        return [self.project]

    def list_workspace(self, _args: Dict[str, Any]) -> Any:
        return [{"id": w, "name": f"ws{i}", "project": {"id": self.project["id"], "name": self.project["name"]}}
                for i, w in enumerate(self.workspaces)]

    # artifact
    def upsert_artifact(self, args: Dict[str, Any]) -> Any:
        return self._write(args, "artifact", "text/html")

    def list_artifacts(self, args: Dict[str, Any]) -> Any:
        return [{"id": d["id"], "key": d["key"], "title": d["title"], "content_sha256": d["content_sha256"],
                 "metadata": d["metadata"]} for d in self.docs
                if d["type"] == "artifact" and d["reference_id"] == args.get("reference_id")]

    def get_artifact(self, args: Dict[str, Any]) -> Any:
        d = self._find(args["reference_table"], args["reference_id"], args["key"])
        if d is None or d["type"] != "artifact":
            raise ToolError("document not found")
        return self._doc_view(d, True)


def enable_sync(root, url: str, key: str = KEY, extra: Optional[Dict[str, Any]] = None, ignore: bool = True) -> None:
    """Config sinkron di `root`: `url` server palsu + MCP key lokal yang diabaikan git."""
    cfg = {"url": url, **(extra or {})}
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude/nataflow.json").write_text(json.dumps(cfg), encoding="utf-8")
    (root / ".claude/nataflow.local.json").write_text(json.dumps({"mcp_key": key}), encoding="utf-8")
    if ignore:
        gi = root / ".gitignore"
        old = gi.read_text(encoding="utf-8") if gi.exists() else ""
        if ".claude/nataflow.local.json" not in old:
            gi.write_text(old + ("" if not old or old.endswith("\n") else "\n") + ".claude/nataflow.local.json\n",
                          encoding="utf-8")
