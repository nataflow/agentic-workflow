#!/usr/bin/env python3
"""Klien MCP nataflow (langkah 29) — salinan identik di `analyst`, `backend`, `frontend`, `quickdev` (`skills/_common/`)
dan `nataflow` (`skills/create-artifact/scripts/`): plugin dipasang terpisah sehingga tidak bisa saling mengimpor.
Ubah kelimanya bersamaan.

Bicara MCP Streamable HTTP langsung ke server nataflow, sehingga skrip sinkron memanggil tool sendiri dan isi dokumen
tidak pernah lewat konteks model. Server bersesi (`initialize` → header `Mcp-Session-Id`), autentikasi
`Authorization: Bearer <MCP key>`. Balikan `application/json` maupun `text/event-stream` diterima.

Kegagalan selalu `NataflowError` berpesan pendek tanpa nilai key:
- `transport` — server tidak terjangkau, HTTP bukan 2xx, atau balikan bukan JSON-RPC sah;
- `tool` — tool menjawab `isError` atau galat JSON-RPC (pesan server apa adanya).

Panggilan tulis tidak pernah diulang otomatis: tulisan yang ternyata sampai di server membuat task/dokumen kembar.
Hanya panggilan baca (`read=True`) yang dicoba sekali lagi sesudah sesi kedaluwarsa (HTTP 404 bersesi).

Zero external dependencies (Python Standard Library only).
"""

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

PROTOCOL_VERSION = "2025-03-26"
CLIENT_NAME = "nataflow-sync"
CLIENT_VERSION = "1"
TIMEOUT = 60          # detik per permintaan HTTP
BODY_MAX = 200        # karakter isi balikan galat HTTP yang dikutip


class NataflowError(Exception):
    """Galat sinkron terbaca: `kind` = `transport` | `tool`."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind
        self.message = message


class Session:
    """Satu sesi MCP ke `url` dengan MCP key `key`; buka lewat `with Session(...) as s:`."""

    def __init__(self, url: str, key: str, timeout: float = TIMEOUT):
        self.url = url
        self._key = key
        self.timeout = timeout
        self.session_id = ""
        self.protocol = PROTOCOL_VERSION
        self._next_id = 0
        self._opener = urllib.request.build_opener(urllib.request.HTTPHandler, urllib.request.HTTPSHandler)

    # ── siklus sesi ──────────────────────────────────────────────────────────

    def __enter__(self) -> "Session":
        self.open()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def open(self) -> None:
        """`initialize` lalu `notifications/initialized`."""
        self.session_id = ""
        result = self._request("initialize", {
            "protocolVersion": PROTOCOL_VERSION, "capabilities": {},
            "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION}})
        if isinstance(result, dict) and isinstance(result.get("protocolVersion"), str):
            self.protocol = result["protocolVersion"]
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect=False)

    def close(self) -> None:
        """Akhiri sesi di server (best effort; galat diabaikan)."""
        if not self.session_id:
            return
        req = urllib.request.Request(self.url, method="DELETE", headers=self._headers())
        try:
            self._opener.open(req, timeout=self.timeout).close()
        except (OSError, ValueError):
            pass
        self.session_id = ""

    # ── tool ─────────────────────────────────────────────────────────────────

    def call(self, tool: str, arguments: Dict[str, Any], read: bool = False) -> str:
        """Panggil satu tool → teks hasilnya (gabungan `content[].text`)."""
        params = {"name": tool, "arguments": arguments}
        try:
            result = self._request("tools/call", params)
        except _SessionExpired:
            if not read:
                raise NataflowError("transport", f"sesi MCP kedaluwarsa saat {tool} — sinkron ulang; tulisan tidak "
                                                 f"diulang otomatis")
            self.open()
            result = self._request("tools/call", params)
        if not isinstance(result, dict):
            raise NataflowError("transport", f"balikan {tool} bukan objek hasil tool")
        text = "".join(c.get("text", "") for c in result.get("content") or []
                       if isinstance(c, dict) and c.get("type") == "text")
        if result.get("isError"):
            raise NataflowError("tool", f"{tool}: {text.strip() or 'galat tanpa pesan'}")
        return text

    def call_json(self, tool: str, arguments: Dict[str, Any], read: bool = False) -> Any:
        """`call` lalu dekode teksnya sebagai JSON."""
        text = self.call(tool, arguments, read=read)
        try:
            return json.loads(text)
        except ValueError:
            raise NataflowError("transport", f"balikan {tool} bukan JSON: {self._clip(text)}")

    # ── HTTP & JSON-RPC ──────────────────────────────────────────────────────

    def _request(self, method: str, params: Dict[str, Any]) -> Any:
        self._next_id += 1
        ident = self._next_id
        message = self._post({"jsonrpc": "2.0", "id": ident, "method": method, "params": params}, expect=True,
                             want_id=ident)
        error = message.get("error")
        if error is not None:
            text = error.get("message") if isinstance(error, dict) else error
            raise NataflowError("tool", f"{params.get('name') or method}: {text}")
        return message.get("result")

    def _headers(self) -> Dict[str, str]:
        headers = {"Authorization": "Bearer " + self._key, "Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
            headers["Mcp-Protocol-Version"] = self.protocol
        return headers

    def _post(self, body: Dict[str, Any], expect: bool, want_id: Optional[int] = None) -> Dict[str, Any]:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, method="POST", headers=self._headers())
        try:
            resp = self._opener.open(req, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            detail = self._clip(exc.read().decode("utf-8", "replace") if exc.fp else "")
            exc.close()
            if exc.code == 404 and self.session_id:
                raise _SessionExpired()
            if exc.code in (401, 403):
                raise NataflowError("transport", f"MCP key ditolak server (HTTP {exc.code}) — periksa `mcp_key` di "
                                                 f".claude/nataflow.local.json")
            raise NataflowError("transport", f"HTTP {exc.code} dari {self.url}" + (f": {detail}" if detail else ""))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            reason = getattr(exc, "reason", exc)
            raise NataflowError("transport", f"tidak dapat menghubungi {self.url} ({self._clip(str(reason))})")
        with resp:
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self.session_id = sid
            if not expect:
                return {}
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            try:
                raw = resp.read().decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise NataflowError("transport", f"balikan {self.url} tidak terbaca ({exc})")
        messages = list(_sse_messages(raw)) if ctype == "text/event-stream" else _json_messages(raw)
        for message in messages:
            if isinstance(message, dict) and message.get("id") == want_id and (
                    "result" in message or "error" in message):
                return message
        raise NataflowError("transport", f"balikan {self.url} tanpa jawaban JSON-RPC: {self._clip(raw)}")

    def _clip(self, text: str) -> str:
        """Potong dan sensor: nilai key tidak pernah ikut dalam pesan."""
        text = " ".join(text.split())
        if self._key:
            text = text.replace(self._key, "***")
        return text[:BODY_MAX] + ("…" if len(text) > BODY_MAX else "")


class _SessionExpired(Exception):
    """HTTP 404 atas permintaan bersesi: server sudah tidak mengenal `Mcp-Session-Id`."""


def _json_messages(raw: str) -> List[Any]:
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    return data if isinstance(data, list) else [data]


def _sse_messages(raw: str) -> Iterator[Any]:
    """Pesan JSON di tiap event SSE (baris `data:` digabung per event)."""
    data: List[str] = []
    for line in raw.splitlines() + [""]:
        if line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
        elif not line.strip() and data:
            try:
                yield json.loads("\n".join(data))
            except ValueError:
                pass
            data = []


def as_list(value: Any, *fields: str) -> List[Any]:
    """Balikan tool daftar → larik: larik apa adanya, atau objek yang membungkusnya di salah satu `fields`."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for field in fields:
            if isinstance(value.get(field), list):
                return value[field]
    raise NataflowError("transport", "balikan daftar tool bukan larik")
