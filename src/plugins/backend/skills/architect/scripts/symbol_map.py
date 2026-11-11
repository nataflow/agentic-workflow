#!/usr/bin/env python3
"""Symbol Map — simbol yang disunting satu commit, per baris diff.

Pengganti pembacaan hunk header `git show -U0` di `architect` Fase 3 butir 4.
Driver diff bawaan git memilih baris konteks dari berkas **lama** sebelum hunk:
method terindentasi (Java, PHP, Kotlin, TS, `fn` di dalam `impl` Rust) tercatat
sebagai nama kelasnya, perubahan baris signature dilekatkan ke method sebelumnya,
dan method baru dilekatkan ke method di atasnya.

Skrip ini menghitung rentang tiap deklarasi dari pencocokan kurawal di sisi
yang benar: baris tambah/ubah dipetakan di berkas sesudah commit (`sha:path`),
hunk hapus murni di berkas sebelum commit (`sha^:path`). Baris signature karena
itu masuk blok method-nya sendiri, dan method baru menjadi simbol baru.

Keluaran (`--json` bawaan): tiap baris berubah dengan `side`, `line`, `symbol`,
`kind` (`fn` | `type` | `top`), `decl_line`. Dengan `--anchor`, simbol `fn` yang
tidak disebut kolom `Anchor` dilaporkan di `outside_anchor` (exit 1).

Dengan `--brief` (32 S1), kolom `Anchor` baris `--path` dan teks `## Steps` dibaca
dari brief itu. Simbol yang deklarasinya tidak ada di `sha^:path` (deklarasi baru)
dan namanya disebut `## Steps` dilaporkan di `new_declared`, bukan `outside_anchor`:
brief berisi kode lengkap, jadi nama barunya tertulis di sana. Suntingan atas simbol
yang sudah ada tetap dinilai terhadap `Anchor`.

Mode anchor (`--anchor`/`--brief`) mencetak keluaran ringkas tanpa daftar `lines`
(32 S2); `--verbose` mengembalikannya.

Exit 2 = mode terdegradasi (ekstensi tak dikenal, kurawal tak seimbang, git
gagal): pemanggil jatuh ke hunk header ber-driver dan mencatat
`Cek simbol: TERDEGRADASI (hunk header)`.

Batas yang diketahui: komentar blok dan template literal TS multi-baris yang
memuat kurawal; lambda/arrow function TS tidak dikenali sebagai `fn`.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_TS_FN = (r"^\s*(?:export\s+)?(?:default\s+)?(?:(?:public|private|protected|static|async|readonly|override)\s+)*"
          r"(?:function\s+)?(\w+)\s*(?:<[^>]*>)?\s*\([^;]*$")
FN = {
    ".java": r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:public|protected|private|static|final|abstract|synchronized"
             r"|native|default)\s+)*(?:<[^>]+>\s+)?[\w<>\[\],.?]+\s+(\w+)\s*\(",
    ".kt": r"^\s*(?:(?:public|private|protected|internal|override|open|suspend|inline)\s+)*fun\s+"
           r"(?:<[^>]+>\s*)?(?:\w+\.)?(\w+)\s*\(",
    ".php": r"^\s*(?:(?:public|protected|private|static|abstract|final)\s+)*function\s+&?(\w+)\s*\(",
    ".ts": _TS_FN,
    ".js": _TS_FN,
    ".go": r"^func\s+(?:\([^)]*\)\s*)?(\w+)\s*\(",
    ".rs": r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)",
}
TYPE = re.compile(
    r"^\s*(?:export\s+)?(?:(?:public|private|protected|abstract|final|static|pub|data|sealed|open|default)\s+)*"
    r"(?:class|interface|enum|trait|struct|impl|object)\s+(?:<[^>]*>\s*)?(\w+)"
    r"|^type\s+(\w+)\s+(?:struct|interface)\b"
)
CONTROL = {"if", "for", "while", "switch", "catch", "return", "new", "else", "synchronized", "try", "do",
           "foreach", "elseif", "match", "when", "loop", "function"}
# Deklarasi yang kurawalnya tidak muncul dalam jarak ini dianggap tanpa badan
# (method abstract, deklarasi interface, pemanggilan yang mirip deklarasi).
MAX_SIGNATURE_LINES = 6
_STRING = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`')


class Degraded(Exception):
    pass


def _code_only(line: str, in_block: bool) -> Tuple[str, bool]:
    """Buang string, komentar `//`, dan komentar blok `/* */` (boleh multi-baris)."""
    out = []
    i = 0
    if in_block:
        end = line.find("*/")
        if end < 0:
            return "", True
        i = end + 2
    rest = _STRING.sub('""', line[i:])
    while True:
        a, b = rest.find("//"), rest.find("/*")
        if a < 0 and b < 0:
            out.append(rest)
            return "".join(out), False
        if a >= 0 and (b < 0 or a < b):
            out.append(rest[:a])
            return "".join(out), False
        out.append(rest[:b])
        end = rest.find("*/", b + 2)
        if end < 0:
            return "".join(out), True
        rest = rest[end + 2:]


def blocks(text: str, ext: str) -> List[Dict]:
    """Deklarasi beserta rentang [baris deklarasi, baris kurawal penutup]."""
    fn_re = re.compile(FN[ext])
    out: List[Dict] = []
    stack: List[Optional[Dict]] = []
    pending: Optional[Dict] = None
    in_block = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        code, in_block_next = _code_only(raw, in_block)
        if not in_block:
            m = fn_re.match(code)
            t = TYPE.match(code)
            if m and m.group(1) not in CONTROL:
                pending = {"symbol": m.group(1), "kind": "fn", "start": lineno}
            elif t:
                pending = {"symbol": t.group(1) or t.group(2), "kind": "type", "start": lineno}
        in_block = in_block_next
        for ch in code:
            if ch == "{":
                if pending and lineno - pending["start"] < MAX_SIGNATURE_LINES:
                    stack.append(pending)
                else:
                    stack.append(None)
                pending = None
            elif ch == "}":
                if not stack:
                    raise Degraded(f"kurawal penutup tanpa pasangan di baris {lineno}")
                blk = stack.pop()
                if blk:
                    out.append({**blk, "end": lineno})
                pending = None
            elif ch == ";" and pending and not stack_paren_open(code):
                pending = None
    if stack:
        raise Degraded("kurawal tidak seimbang di akhir berkas")
    return out


def stack_paren_open(code: str) -> bool:
    """`;` di dalam kurung (`for (a; b; c)`) tidak menutup deklarasi."""
    return code.count("(") > code.count(")")


def enclosing(blks: List[Dict], line: int) -> Optional[Dict]:
    inside = [b for b in blks if b["start"] <= line <= b["end"]]
    fns = [b for b in inside if b["kind"] == "fn"]
    return max(fns or inside, key=lambda b: b["start"]) if inside else None


def _git(root: Path, *args: str) -> str:
    # Bytes lalu `errors="replace"`: berkas Latin-1 dulu melempar UnicodeDecodeError berkode keluar 1 — kode
    # yang sama dengan vonis `outside_anchor` (11 H11). Kurawal dan identifier ASCII tidak terpengaruh.
    r = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if r.returncode != 0:
        raise Degraded(f"git {' '.join(args[:2])} gagal: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "replace")


def changed(root: Path, sha: str, path: str) -> List[Dict]:
    ext = Path(path).suffix
    if ext not in FN:
        raise Degraded(f"ekstensi `{ext or '(kosong)'}` tidak dikenal")
    diff = _git(root, "show", sha, "-U0", "--format=", "--", path)
    sides: Dict[str, Optional[List[Dict]]] = {"new": None, "old": None}
    result: List[Dict] = []
    for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", diff, re.M):
        a, b = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        c, d = int(m.group(3)), int(m.group(4) if m.group(4) is not None else 1)
        # Hunk campuran (hapus + tambah) dipetakan di kedua sisi: baris yang dihapus dari method lain
        # dulu hilang dari peta karena hanya sisi baru yang dibaca (11 H11). Baris lama yang simbolnya
        # sudah tercatat sisi baru hunk ini (ubah di tempat) tidak diulang.
        seen_new: set = set()
        for side, first, count in (("new", c, d), ("old", a, b)):
            if count <= 0:
                continue
            if sides[side] is None:
                rev = f"{sha}:{path}" if side == "new" else f"{sha}^:{path}"
                sides[side] = blocks(_git(root, "show", rev), ext)
            for line in range(first, first + count):
                blk = enclosing(sides[side], line)
                symbol = blk["symbol"] if blk else None
                if side == "new":
                    seen_new.add(symbol)
                elif symbol in seen_new:
                    continue
                result.append({"side": side, "line": line, "symbol": symbol,
                               "kind": blk["kind"] if blk else "top",
                               "decl_line": blk["start"] if blk else None})
    return result


def brief_row(text: str, path: str) -> Tuple[Optional[str], str]:
    """(isi kolom `Anchor` baris `path` di `## File scope`, teks `## Steps`) dari isi brief."""
    def section(name: str) -> str:
        m = re.search(rf"^## {name}[ \t]*$", text, re.M | re.I)
        if not m:
            return ""
        sec = text[m.end():]
        nxt = re.search(r"^## ", sec, re.M)
        return sec[:nxt.start()] if nxt else sec

    anchor = None
    for line in section("File scope").splitlines():
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) >= 4 and cols[0].strip("`").lower() in ("modify", "create") \
                and cols[1].strip("`").strip() == path:
            anchor = cols[2]
            break
    return anchor, section("Steps")


def old_declarations(root: Path, sha: str, path: str, ext: str) -> set:
    """Nama deklarasi di `sha^:path`; berkas yang belum ada di induk tidak punya deklarasi lama."""
    try:
        text = _git(root, "show", f"{sha}^:{path}")
    except Degraded:
        return set()
    return {b["symbol"] for b in blocks(text, ext)}


def main():
    parser = argparse.ArgumentParser(description="Peta simbol yang disunting satu commit")
    parser.add_argument("--sha", required=True, help="Commit brief")
    parser.add_argument("--path", required=True, help="Berkas beraksi `modify`")
    parser.add_argument("--anchor", help="Isi kolom `Anchor` baris berkas itu di `## File scope`")
    parser.add_argument("--brief", help="Brief pemilik commit: Anchor dan `## Steps` dibaca dari sini (32 S1)")
    parser.add_argument("--verbose", action="store_true", help="Cetak `lines` juga pada mode anchor (32 S2)")
    parser.add_argument("--root", default=".", help="Root repositori")
    args = parser.parse_args()

    def degraded(reason: str):
        print(json.dumps({"status": "DEGRADED", "path": args.path, "reason": reason,
                          "fallback": "git -c core.attributesFile=<tmp> show -U0 (hunk header ber-driver)"},
                         ensure_ascii=False))
        sys.exit(2)

    root = Path(args.root)
    anchor, steps = args.anchor, None
    if args.brief:
        try:
            brief_text = Path(args.brief).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            degraded(f"brief tak terbaca: {exc}")
        row_anchor, steps = brief_row(brief_text, args.path)
        if anchor is None:
            if row_anchor is None:
                degraded(f"baris `## File scope` untuk `{args.path}` tidak ditemukan di brief")
            anchor = row_anchor

    try:
        lines = changed(root, args.sha, args.path)
        old_decl = old_declarations(root, args.sha, args.path, Path(args.path).suffix) if steps is not None else set()
    except Exception as exc:   # noqa: BLE001 — exit 1 berarti `outside_anchor`; galat apa pun wajib exit 2
        degraded(str(exc))

    symbols = sorted({(l["symbol"], l["kind"]) for l in lines if l["symbol"]})
    payload = {"status": "PASS", "path": args.path, "sha": args.sha,
               "symbols": [{"symbol": s, "kind": k} for s, k in symbols]}
    exit_code = 0
    if anchor is None:
        payload["lines"] = lines
    else:
        named = set(re.findall(r"[A-Za-z_]\w*", anchor))

        def declared_new(symbol: str) -> bool:
            return (steps is not None and symbol not in old_decl
                    and re.search(rf"\b{re.escape(symbol)}\b", steps) is not None)

        unanchored_fn = sorted({l["symbol"] for l in lines if l["kind"] == "fn" and l["symbol"] not in named})
        unanchored_type = sorted({l["symbol"] for l in lines if l["kind"] == "type" and l["symbol"] not in named})
        payload["new_declared"] = sorted({s for s in unanchored_fn + unanchored_type if declared_new(s)})
        payload["outside_anchor"] = [
            {"symbol": s, "lines": [l["line"] for l in lines if l["symbol"] == s]}
            for s in unanchored_fn if not declared_new(s)]
        payload["type_level_unanchored"] = [s for s in unanchored_type if not declared_new(s)]
        if args.verbose:
            payload["lines"] = lines
        if payload["outside_anchor"]:
            payload["status"] = "FAIL"
            exit_code = 1
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
