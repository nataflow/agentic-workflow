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

Deklarasi lama dibandingkan dengan nama berkualifikasi tipe induknya (`Foo::default`, B1): `fn
default` di `impl Default for Foo` yang baru tidak lagi dianggap lama hanya karena `impl Default for Bar`
sudah punya `fn default`. Pada Rust, `impl Trait for Type` dinamai `Type`. Fn baru di dalam blok tipe atau
`impl` yang baris deklarasinya ditambah commit yang sama juga masuk `new_declared` tanpa syarat `## Steps`:
seluruh bloknya lahir di commit itu.

Fn yang lazim tersentuh sebagai pendukung masuk `diabaikan`, bukan `outside_anchor` (B1): lifecycle test
(annotation `@Before*`/`@After*`, atau nama `setUp`/`tearDown`/`beforeEach`/`TestMain`/… di berkas test),
`main`, dan `default`.

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
# Pola fn berkata kunci (`fn`/`func`/`fun`/`function`) tidak tertukar dengan pemanggilan, jadi `CONTROL` tidak
# berlaku: `fn new` Rust dulu tidak pernah dikenali dan barisnya jatuh ke blok `impl` (B1).
KEYWORD_FN = {".rs", ".go", ".kt", ".php"}
# Fn pendukung yang tidak dinilai terhadap `Anchor` (B1): `diabaikan`, bukan `outside_anchor`.
ALWAYS_IGNORED = {"main", "default"}
TEST_LIFECYCLE = {"setUp", "tearDown", "setUpClass", "tearDownClass", "setup", "teardown", "setUpTest",
                  "tearDownTest", "beforeEach", "afterEach", "beforeAll", "afterAll", "TestMain"}
LIFECYCLE_ANN = {"Before", "After", "BeforeEach", "AfterEach", "BeforeAll", "AfterAll", "BeforeClass",
                 "AfterClass", "BeforeMethod", "AfterMethod", "BeforeTest", "AfterTest", "BeforeSuite",
                 "AfterSuite"}
TEST_PATH = re.compile(r"(?:^|/)(?:tests?|__tests__|spec)/|_test\.\w+$|Tests?\.\w+$|\.(?:test|spec)\.\w+$"
                       r"|(?:^|/)test_[^/]*$")
_RUST_IMPL = re.compile(r"^\s*(?:unsafe\s+)?impl\b")
_ANN = re.compile(r"@(\w+)")
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


def rust_impl_target(code: str) -> Optional[str]:
    """Nama tipe sasaran `impl`: `impl<T> fmt::Display for Foo<T>` -> `Foo`; `impl Foo` -> `Foo`."""
    if not _RUST_IMPL.match(code):
        return None
    rest = re.sub(r"<[^<>]*>", "", _RUST_IMPL.sub("", code, count=1))
    rest = re.sub(r"<[^<>]*>", "", rest)
    m = re.search(r"\bfor\s+((?:\w+::)*\w+)", rest) or re.match(r"\s*((?:\w+::)*\w+)", rest)
    return m.group(1).split("::")[-1] if m else None


def blocks(text: str, ext: str) -> List[Dict]:
    """Deklarasi beserta rentang [baris deklarasi, baris kurawal penutup].

    Fn membawa `parent` (nama tipe induk terdekat) dan `parent_line` (baris deklarasinya), serta
    `lifecycle` bila diberi annotation lifecycle test (`@BeforeEach` dan sejenisnya).
    """
    fn_re = re.compile(FN[ext])
    out: List[Dict] = []
    stack: List[Optional[Dict]] = []
    pending: Optional[Dict] = None
    in_block = False
    ann: List[str] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        code, in_block_next = _code_only(raw, in_block)
        if not in_block:
            m = fn_re.match(code)
            t = TYPE.match(code)
            # `impl<T> Trait for Foo<T>` tidak cocok `TYPE` (tanpa spasi sebelum `<`) dan `impl Trait for Foo`
            # tertangkap sebagai `Trait`; sasaran impl Rust dibaca terpisah.
            rt = rust_impl_target(code) if ext == ".rs" else None
            if m and (ext in KEYWORD_FN or m.group(1) not in CONTROL):
                anns = ann + _ANN.findall(code[:m.start(1)])
                pending = {"symbol": m.group(1), "kind": "fn", "start": lineno,
                           "lifecycle": any(a in LIFECYCLE_ANN for a in anns)}
                ann = []
            elif t or rt:
                name = rt or t.group(1) or t.group(2)
                pending = {"symbol": name, "kind": "type", "start": lineno}
                ann = []
            elif code.strip().startswith("@"):
                ann += _ANN.findall(code)
            elif code.strip():
                ann = []
        in_block = in_block_next
        for ch in code:
            if ch == "{":
                if pending and lineno - pending["start"] < MAX_SIGNATURE_LINES:
                    if pending["kind"] == "fn":
                        parent = next((b for b in reversed(stack) if b and b["kind"] == "type"), None)
                        pending["parent"] = parent["symbol"] if parent else None
                        pending["parent_line"] = parent["start"] if parent else None
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


def key_of(blk: Dict) -> str:
    """Nama berkualifikasi tipe induk: `Foo::default`; deklarasi tanpa induk memakai namanya sendiri."""
    return f"{blk['parent']}::{blk['symbol']}" if blk.get("parent") else blk["symbol"]


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
                               "decl_line": blk["start"] if blk else None,
                               # Internal (B1); dibuang sebelum `lines` dicetak supaya bentuk keluaran tetap.
                               "_key": key_of(blk) if blk else None,
                               "_parent_line": blk.get("parent_line") if blk else None,
                               "_lifecycle": bool(blk.get("lifecycle")) if blk else False})
    return result


def public(line: Dict) -> Dict:
    return {k: v for k, v in line.items() if not k.startswith("_")}


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
    """Nama berkualifikasi deklarasi di `sha^:path`; berkas yang belum ada di induk tidak punya deklarasi lama."""
    try:
        text = _git(root, "show", f"{sha}^:{path}")
    except Degraded:
        return set()
    return {key_of(b) for b in blocks(text, ext)}


def ignored(line: Dict, path: str) -> bool:
    """Fn pendukung yang tidak dinilai terhadap `Anchor` (B1)."""
    name = line["symbol"]
    return (name in ALWAYS_IGNORED or line["_lifecycle"]
            or (name in TEST_LIFECYCLE and TEST_PATH.search(path) is not None))


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
        old_decl = old_declarations(root, args.sha, args.path, Path(args.path).suffix) if anchor is not None else set()
    except Exception as exc:   # noqa: BLE001 — exit 1 berarti `outside_anchor`; galat apa pun wajib exit 2
        degraded(str(exc))

    symbols = sorted({(l["symbol"], l["kind"]) for l in lines if l["symbol"]})
    payload = {"status": "PASS", "path": args.path, "sha": args.sha,
               "symbols": [{"symbol": s, "kind": k} for s, k in symbols]}
    exit_code = 0
    if anchor is None:
        payload["lines"] = [public(l) for l in lines]
    else:
        named = set(re.findall(r"[A-Za-z_]\w*", anchor))
        added_new = {l["line"] for l in lines if l["side"] == "new"}

        def declared_new(l: Dict) -> bool:
            if l["_key"] in old_decl:
                return False
            if steps is not None and re.search(rf"\b{re.escape(l['symbol'])}\b", steps):
                return True
            # Blok induk lahir di commit ini: seluruh isinya baru (B1).
            born_line = l["_parent_line"] if l["kind"] == "fn" else l["decl_line"]
            return l["side"] == "new" and born_line is not None and born_line in added_new

        unanchored = [l for l in lines if l["symbol"] and l["kind"] in ("fn", "type") and l["symbol"] not in named]
        new_decl, outside, type_level, skipped = set(), {}, set(), set()
        for l in unanchored:
            if declared_new(l):
                new_decl.add(l["symbol"])
            elif l["kind"] == "fn" and ignored(l, args.path):
                skipped.add(l["symbol"])
            elif l["kind"] == "fn":
                outside.setdefault(l["symbol"], []).append(l["line"])
            else:
                type_level.add(l["symbol"])
        payload["new_declared"] = sorted(new_decl)
        payload["outside_anchor"] = [{"symbol": s, "lines": outside[s]} for s in sorted(outside)]
        payload["type_level_unanchored"] = sorted(type_level - new_decl)
        payload["diabaikan"] = sorted(skipped - set(outside))
        if args.verbose:
            payload["lines"] = [public(l) for l in lines]
        if payload["outside_anchor"]:
            payload["status"] = "FAIL"
            exit_code = 1
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
