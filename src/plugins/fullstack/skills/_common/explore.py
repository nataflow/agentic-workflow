#!/usr/bin/env python3
"""Laporan explore `TELUSUR` plugin `fullstack`: panen, jahitan, pagar, dan pemetaan layanan.

    python3 explore.py new   --slug <slug> --objective <teks> --lingkup <proyek,...> --repo <dir,...>
                             [--root <dir>] [--json]
    python3 explore.py list  [--root <dir>] [--json]
    python3 explore.py seam  --report <path> [--root <dir>] [--write] [--json]
    python3 explore.py check --report <path> [--root <dir>] [--json]
    python3 explore.py layanan list  [--root <dir>] [--json]
    python3 explore.py layanan set   --pemanggil <dir> --target <nama-config> --repo <dir> [--prefix <path>]
    python3 explore.py layanan hapus --pemanggil <dir> --target <nama-config>

`new` menulis kerangka laporan dari `templates/explore-template.md` skill `explore`, dengan frontmatter dan tabel
`## Repo` yang sudah terisi dari `scan`. `list` membaca frontmatter laporan di `.fullstack/explore/` dan menandai laporan `basi` bila HEAD salah satu
repo sudah bergeser (K18–K19). `seam` mencocokkan tabel `## Panggilan` dengan `## Endpoint` (K20–K26); dengan
`--write` tabel `## Jahitan` laporan ditulis ulang dari hasilnya. `check` adalah pagar laporan (exit 0 PASS,
1 FAIL). `layanan` mengelola `.fullstack/layanan.json`, satu-satunya sumber target pasti BE → BE (K21).

Standard library saja.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fullstack_lib import (  # noqa: E402
    EXPLORE_DIR,
    LAYANAN_FILE,
    SLUG,
    STAMP,
    bukan_di_root,
    cell,
    dump_json,
    load_layanan,
    peran_valid,
    read_text,
    repo_index,
    save_layanan,
    scan,
    stamp,
    write_atomic,
)

SECTIONS = ("Jawaban", "Repo", "Temuan", "Endpoint", "Panggilan", "Jahitan", "Celah", "Arahan Lanjut")
FM_FIELDS = ("slug", "objective", "dibuat", "lingkup", "repo", "confidence")
CONFIDENCE = ("high", "medium", "low")
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
STATUS = ("COCOK", "TIDAK_ADA_DI_TARGET", "DUGAAN", "AMBIGU", "TAK_DIKENAL", "TAK_TERPANGGIL")
TABLE_COLS = {"Endpoint": 4, "Panggilan": 5, "Jahitan": 6}
POINTER = re.compile(r"`([\w.\-()\[\]+@~]+(?:/[\w.\-()\[\]+@~]+)+):(\d+)(?:-(\d+))?`")
PLACEHOLDER = re.compile(r"\b(TBD|TODO)\b")
NONE_CELLS = ("", "-", "—")
COMMENT = re.compile(r"<!--.*?-->", re.S)
TEMPLATE = Path(__file__).resolve().parents[1] / "explore" / "templates" / "explore-template.md"


# ------------------------------------------------------------------ parsing laporan

def parse_report(text: str) -> Dict[str, Any]:
    """{fm, sections (urutan judul `##`), body {judul: isi}, galat}."""
    out: Dict[str, Any] = {"fm": {}, "sections": [], "body": {}, "galat": []}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        out["galat"].append("frontmatter `---` tidak ada di baris pertama")
        rest = lines
    else:
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
        except StopIteration:
            out["galat"].append("frontmatter tidak ditutup `---`")
            return out
        for raw in lines[1:end]:
            if ":" in raw:
                key, value = raw.split(":", 1)
                out["fm"][key.strip()] = value.strip()
        rest = lines[end + 1:]
    current = None
    fence = False
    for raw in rest:
        if raw.strip().startswith("```"):
            fence = not fence
        if not fence and raw.startswith("## "):
            current = raw[3:].strip()
            out["sections"].append(current)
            out["body"].setdefault(current, [])
            continue
        if current is not None:
            out["body"][current].append(raw)
    # Komentar penjelas template bukan isi: contoh tabel di dalamnya tidak boleh terbaca sebagai tabel.
    out["body"] = {k: COMMENT.sub("", "\n".join(v)).strip("\n") for k, v in out["body"].items()}
    return out


def split_list(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def fm_repos(value: str) -> List[Tuple[str, str]]:
    out = []
    for item in split_list(value):
        dir_, _, sha = item.partition("@")
        out.append((dir_.strip().strip("`"), sha.strip()))
    return out


def table_rows(body: str) -> List[List[str]]:
    """Baris data tabel markdown pertama di `body` (tanpa header dan pemisah)."""
    rows: List[List[str]] = []
    seen_header = False
    for raw in body.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            if rows or seen_header:
                break
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if not seen_header:
            seen_header = True
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows


def plain(value: str) -> str:
    return value.replace("\\|", "|").strip().strip("`").strip()


def subsections(body: str) -> Dict[str, str]:
    out: Dict[str, List[str]] = {}
    current = None
    for raw in body.splitlines():
        if raw.startswith("### "):
            current = raw[4:].strip()
            out[current] = []
        elif current is not None:
            out[current].append(raw)
    return {k: "\n".join(v) for k, v in out.items()}


def base_api(report: Dict[str, Any]) -> Dict[str, str]:
    """`{dir FE: prefix}` dari baris `- Base API:` di `### <dir> (FE)` seksi Temuan."""
    out: Dict[str, str] = {}
    for title, body in subsections(report["body"].get("Temuan", "")).items():
        m = re.match(r"^`?([^`(]+?)`?\s*\(FE\)\s*$", title)
        if not m:
            continue
        for raw in body.splitlines():
            line = raw.strip()
            if not line.startswith("- Base API:"):
                continue
            value = re.split(r"\s+\(|\s+—", line[len("- Base API:"):].strip(), 1)[0].strip().strip("`")
            value = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^/]*", "", value)
            if value.startswith("/"):
                out[m.group(1).strip()] = value
    return out


# ------------------------------------------------------------------ jahitan

def norm_path(path: str) -> str:
    p = plain(path)
    p = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^/]*", "", p)
    p = re.sub(r"\$\{[^}]*\}", "{}", p.split("?", 1)[0].split("#", 1)[0])
    segs = []
    for s in p.split("/"):
        if not s:
            continue
        segs.append("{}" if re.fullmatch(r"\{[^}]*\}|:[A-Za-z_]\w*|\[[^\]]+\]|<[^>]+>", s) else s)
    return "/" + "/".join(segs)


def _match(call: str, endpoint: str, exact: bool) -> bool:
    if call == endpoint:
        return True
    if exact or call == "/":
        return False
    c, e = call.strip("/").split("/"), endpoint.strip("/").split("/")
    return len(c) < len(e) and e[-len(c):] == c


def seam_rows(report: Dict[str, Any], sc: Dict[str, Any], layanan: List[Dict[str, str]]) -> List[Dict[str, str]]:
    repos = repo_index(sc)
    lingkup = set(split_list(report["fm"].get("lingkup", "")))
    be_repos = sorted(d for d, r in repos.items() if "BE" in peran_valid(r) and (not lingkup or r["proyek"] in lingkup))
    endpoints = [{"repo": plain(r[0]), "metode": plain(r[1]).upper(), "path": norm_path(r[2])}
                 for r in table_rows(report["body"].get("Endpoint", "")) if len(r) >= 4]
    calls = [{"pemanggil": plain(r[0]), "target": plain(r[1]), "metode": plain(r[2]).upper(), "path": r[3]}
             for r in table_rows(report["body"].get("Panggilan", "")) if len(r) >= 5]
    bases = base_api(report)
    mapped = {(m["pemanggil"], m["target"]): m for m in layanan}
    used = set()
    rows: List[Dict[str, str]] = []
    for call in calls:
        caller = repos.get(call["pemanggil"])
        roles = peran_valid(caller) if caller else []
        is_fe = "FE" in roles and "BE" not in roles
        if is_fe:
            cands = [d for d in be_repos if repos[d]["proyek"] == caller["proyek"]]
        else:
            cands = [d for d in be_repos if d != call["pemanggil"]]
        target, prefix = None, None
        m = mapped.get((call["pemanggil"], call["target"]))
        if m:
            target, prefix = m["repo"], m.get("prefix") or None
        elif is_fe and len(cands) == 1:
            target = cands[0]
        if is_fe and prefix is None:
            prefix = bases.get(call["pemanggil"])
        path = norm_path((prefix or "") + "/" + plain(call["path"])) if prefix else norm_path(call["path"])
        hits = [i for i, e in enumerate(endpoints) if e["metode"] == call["metode"]
                and _match(path, e["path"], exact=prefix is not None)]
        row = {"pemanggil": call["pemanggil"], "target": call["target"] or "—", "metode": call["metode"], "path": path}
        if target:
            hit = [i for i in hits if endpoints[i]["repo"] == target]
            used.update(hit)
            row.update(penerima=target, status="COCOK" if hit else "TIDAK_ADA_DI_TARGET")
        else:
            hit = [i for i in hits if endpoints[i]["repo"] in cands]
            used.update(hit)
            recv = sorted({endpoints[i]["repo"] for i in hit})
            status = "TAK_DIKENAL" if not recv else ("DUGAAN" if len(recv) == 1 else "AMBIGU")
            row.update(penerima=", ".join(recv) or "—", status=status)
        rows.append(row)
    for i, e in enumerate(endpoints):
        if i not in used:
            rows.append({"pemanggil": "—", "target": "—", "metode": e["metode"], "path": e["path"],
                         "penerima": e["repo"], "status": "TAK_TERPANGGIL"})
    return rows


def _code(value: str) -> str:
    return "—" if value in NONE_CELLS else ", ".join(f"`{cell(v)}`" for v in split_list(value))


def render_seam(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return "- Tidak ada."
    out = ["| Pemanggil | Target | Metode | Path | Penerima | Status |", "|---|---|---|---|---|---|"]
    out += [f"| {_code(r['pemanggil'])} | {_code(r['target'])} | {r['metode']} | `{cell(r['path'])}` | "
            f"{_code(r['penerima'])} | {r['status']} |" for r in rows]
    return "\n".join(out)


def _row_key(cells: List[str]) -> Tuple[str, ...]:
    return tuple(", ".join(plain(x) for x in c.split(",")) if c.strip() not in NONE_CELLS else "—" for c in cells)


def replace_section(text: str, title: str, body: str) -> str:
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == f"## {title}")
    except StopIteration:
        raise ValueError(f"seksi `## {title}` tidak ada")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    new = lines[:start + 1] + [""] + body.splitlines() + ([""] if end < len(lines) else []) + lines[end:]
    return "\n".join(new) + "\n"


# ------------------------------------------------------------------ check

class Checks:
    def __init__(self) -> None:
        self.results: List[Dict[str, Any]] = []

    def add(self, cid: int, name: str, problems: List[str], ok_summary: str = "lolos") -> None:
        self.results.append({"id": cid, "name": name, "status": "FAIL" if problems else "PASS",
                             "summary": "; ".join(problems[:6]) + (f" (+{len(problems) - 6} lagi)"
                                                                   if len(problems) > 6 else "")
                             if problems else ok_summary})

    @property
    def ok(self) -> bool:
        return all(r["status"] == "PASS" for r in self.results)


def _line_count(path: Path) -> Optional[int]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)


def run_check(root: Path, report_path: Path) -> Tuple[Checks, Dict[str, Any]]:
    c = Checks()
    text = read_text(report_path)
    if text is None:
        c.add(1, "Frontmatter", [f"laporan `{report_path}` tidak ada atau tidak terbaca"])
        return c, {}
    rep = parse_report(text)
    sc = scan(root)
    repos = repo_index(sc)
    proyek = {r["proyek"] for r in sc["repo"]}

    fm = rep["fm"]
    probs = list(rep["galat"])
    probs += [f"field `{k}` kosong atau tidak ada" for k in FM_FIELDS if not fm.get(k)]
    if fm.get("slug") and not SLUG.match(fm["slug"]):
        probs.append(f"`slug` `{fm['slug']}` bukan kebab-case")
    if fm.get("dibuat") and not STAMP.match(fm["dibuat"]):
        probs.append("`dibuat` wajib YYMMDDhhmm")
    if fm.get("confidence") and fm["confidence"] not in CONFIDENCE:
        probs.append(f"`confidence` `{fm['confidence']}` di luar high/medium/low")
    probs += [f"`lingkup`: {bukan_di_root(sc, 'proyek', p)}" for p in split_list(fm.get("lingkup", ""))
              if p not in proyek]
    fm_dirs = [d for d, _sha in fm_repos(fm.get("repo", ""))]
    probs += [f"`repo`: {bukan_di_root(sc, 'repo', d)}" for d in fm_dirs if d not in repos]
    probs += [f"`repo` `{d}@{sha}` tanpa SHA" for d, sha in fm_repos(fm.get("repo", "")) if not sha]
    c.add(1, "Frontmatter", probs)

    probs = []
    if tuple(rep["sections"]) != SECTIONS:
        probs.append("seksi wajib berurutan: " + ", ".join(f"`## {s}`" for s in SECTIONS)
                     + "; ditemukan: " + (", ".join(f"`## {s}`" for s in rep["sections"]) or "tidak ada"))
    probs += [f"`## {s}` kosong" for s in SECTIONS if s in rep["body"] and not rep["body"][s].strip()]
    for title, n in TABLE_COLS.items():
        body = rep["body"].get(title, "")
        rows = table_rows(body)
        if body.strip() and not rows and body.strip() != "- Tidak ada.":
            probs.append(f"`## {title}` wajib tabel {n} kolom atau `- Tidak ada.`")
        probs += [f"`## {title}` baris {i} punya {len(r)} kolom, wajib {n}" for i, r in enumerate(rows, 1)
                  if len(r) != n]
        if title != "Jahitan":
            col = 1 if title == "Endpoint" else 2
            probs += [f"`## {title}` baris {i}: metode `{plain(r[col])}` tidak dikenal" for i, r in enumerate(rows, 1)
                      if len(r) == n and plain(r[col]).upper() not in METHODS]
    c.add(2, "Seksi", probs)

    probs = []
    body_text = "\n".join(rep["body"].values())
    dirs = sorted(fm_dirs, key=len, reverse=True)
    for m in POINTER.finditer(body_text):
        ref, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
        owner = next((d for d in dirs if ref.startswith(d + "/")), None)
        if owner is None:
            probs.append(f"`{ref}:{m.group(2)}` menunjuk repo di luar frontmatter `repo`")
            continue
        count = _line_count(root / ref)
        if count is None:
            probs.append(f"`{ref}` tidak ada")
        elif not (1 <= a <= b <= count):
            probs.append(f"`{ref}:{m.group(2)}{'-' + m.group(3) if m.group(3) else ''}` melewati {count} baris berkas")
    c.add(3, "Rujukan path:baris", probs)

    probs = []
    layanan, err = load_layanan(root)
    if err:
        probs.append(err)
    else:
        want = [_row_key([r["pemanggil"], r["target"], r["metode"], r["path"], r["penerima"], r["status"]])
                for r in seam_rows(rep, sc, layanan)]
        got = [_row_key(r) for r in table_rows(rep["body"].get("Jahitan", ""))]
        if want != got:
            probs.append(f"tabel `## Jahitan` ({len(got)} baris) berbeda dari keluaran `seam` ({len(want)} baris); "
                         "jalankan `explore.py seam --write`")
    c.add(4, "Jahitan = seam", probs)

    probs = []
    arahan = rep["body"].get("Arahan Lanjut", "")
    for r in table_rows(rep["body"].get("Repo", "")):
        if len(r) >= 5 and re.search(r"ABSENT|LEGACY|INVALID_JSON|TIDAK_SAH", r[4]) and plain(r[0]) not in arahan:
            probs.append(f"repo `{plain(r[0])}` berprofil {plain(r[4])} tanpa butir di `## Arahan Lanjut`")
    c.add(5, "Arahan profil", probs)

    probs = []
    celah = rep["body"].get("Celah", "")
    for r in table_rows(rep["body"].get("Jahitan", "")):
        if len(r) == 6 and plain(r[5]) in ("DUGAAN", "AMBIGU") and plain(r[1]) not in celah:
            probs.append(f"jahitan {plain(r[5])} `{plain(r[0])}` → `{plain(r[1])}` tanpa butir di `## Celah`")
    c.add(6, "Celah pemetaan", probs)

    hits = sorted({m.group(1) for m in PLACEHOLDER.finditer(text)})
    c.add(7, "Tanpa placeholder", [f"`{h}` masih ada" for h in hits])
    return c, rep


def format_check(report: str, c: Checks) -> str:
    passed = sum(1 for r in c.results if r["status"] == "PASS")
    lines = [f"CHECK: {report} [{'PASS' if c.ok else 'FAIL'}] ({passed}/{len(c.results)} passed)"]
    lines += [f"[{r['id']}] {r['name']:<22} : {r['status']} ({r['summary']})" for r in c.results]
    return "\n".join(lines)


# ------------------------------------------------------------------ new

def repo_table(sc: Dict[str, Any], lingkup: List[str], dirs: List[str]) -> str:
    """Tabel `## Repo`: repo yang disisir, ditambah repo lain di proyek lingkup yang profilnya ada tetapi tidak `VALID`.

    Repo tanpa profil sama sekali (pustaka, infra) cukup tercatat di `PETA.md`; mencantumkannya di sini memaksa
    tiap laporan menulis arahan untuk repo yang mungkin memang bukan aplikasi.
    """
    rows = [r for r in sc["repo"] if r["dir"] in dirs
            or (r["proyek"] in lingkup and r["profil"] and not peran_valid(r))]
    out = ["| Dir | Proyek | Peran | Stack | Profil | HEAD |", "|---|---|---|---|---|---|"]
    for r in rows:
        prof = r["profil"]
        out.append(f"| `{cell(r['dir'])}` | {cell(r['proyek'])} | {', '.join(p['peran'] or '?' for p in prof) or '—'} | "
                   f"{', '.join(p['stack'] or '-' for p in prof) or '—'} | "
                   f"{', '.join(p['status'] for p in prof) or 'ABSENT'} | {r['head'] or 'tanpa commit'} |")
    return "\n".join(out)


def new_report(root: Path, slug: str, objective: str, lingkup: List[str], dirs: List[str]) -> Tuple[str, str]:
    """(path relatif laporan, galat)."""
    if not SLUG.match(slug):
        return "", f"`--slug {slug}` bukan kebab-case"
    objective = " ".join(objective.split())
    if not objective:
        return "", "`--objective` kosong"
    sc = scan(root)
    if sc["mode"] == "DALAM_REPO":
        return "", "root berada di dalam repo git"
    repos = repo_index(sc)
    proyek = {r["proyek"] for r in sc["repo"]}
    bad = [bukan_di_root(sc, "proyek", p) for p in lingkup if p not in proyek]
    bad += [bukan_di_root(sc, "repo", d) for d in dirs if d not in repos]
    bad += [f"repo `{d}` tanpa commit" for d in dirs if d in repos and not repos[d]["head"]]
    if not lingkup or not dirs:
        bad.append("`--lingkup` dan `--repo` wajib diisi")
    if bad:
        return "", "; ".join(bad)
    template = read_text(TEMPLATE)
    if template is None:
        return "", f"template `{TEMPLATE.name}` tidak ada; pasang ulang plugin fullstack"
    rel = f"{EXPLORE_DIR}/{stamp()}-{slug}.md"
    if (root / rel).exists():
        return "", f"`{rel}` sudah ada"
    shas = ", ".join(f"{d}@{repos[d]['head']}" for d in dirs)
    fm = (f"---\nslug: {slug}\nobjective: {objective}\ndibuat: {rel.rsplit('/', 1)[1][:10]}\n"
          f"lingkup: {', '.join(lingkup)}\nrepo: {shas}\nconfidence:\n---\n")
    body = template.split("\n## ", 1)
    text = fm + "\n## " + body[1] if len(body) == 2 else fm + template
    text = replace_section(text, "Repo", repo_table(sc, lingkup, dirs))
    write_atomic(root / rel, text)
    return rel, ""


# ------------------------------------------------------------------ list

def list_reports(root: Path) -> Dict[str, Any]:
    sc = scan(root)
    out: Dict[str, Any] = {"root": str(root), "mode": sc["mode"], "laporan": [], "rusak": []}
    if sc["mode"] == "DALAM_REPO":
        return out
    repos = repo_index(sc)
    d = root / EXPLORE_DIR
    files = sorted(d.glob("*.md"), reverse=True) if d.is_dir() else []
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = read_text(path)
        rep = parse_report(text) if text is not None else {"fm": {}, "galat": ["tidak terbaca"]}
        missing = [k for k in FM_FIELDS if not rep["fm"].get(k)]
        if rep["galat"] or missing:
            out["rusak"].append({"berkas": rel, "alasan": "; ".join(rep["galat"] + [f"tanpa `{k}`" for k in missing])})
            continue
        items = []
        for dir_, sha in fm_repos(rep["fm"]["repo"]):
            now = (repos.get(dir_) or {}).get("head")
            stale = not (now and sha and (now.startswith(sha) or sha.startswith(now)))
            items.append({"dir": dir_, "sha": sha, "sekarang": now, "basi": stale})
        fm = rep["fm"]
        out["laporan"].append({"berkas": rel, "slug": fm["slug"], "objective": fm["objective"], "dibuat": fm["dibuat"],
                               "lingkup": split_list(fm["lingkup"]), "confidence": fm["confidence"], "repo": items,
                               "basi": any(i["basi"] for i in items)})
    return out


# ------------------------------------------------------------------ layanan

def layanan_set(root: Path, pemanggil: str, target: str, repo: str, prefix: str) -> str:
    """'' bila tersimpan, selain itu alasan penolakan."""
    peta, err = load_layanan(root)
    if err:
        return err
    sc = scan(root)
    repos = repo_index(sc)
    if pemanggil not in repos:
        return f"`--pemanggil`: {bukan_di_root(sc, 'repo', pemanggil)}"
    if repo not in repos:
        return f"`--repo`: {bukan_di_root(sc, 'repo', repo)}"
    if "BE" not in peran_valid(repos[repo]):
        return f"`--repo {repo}` bukan repo BE berprofil VALID"
    if pemanggil == repo:
        return "`--pemanggil` sama dengan `--repo`"
    if not target.strip():
        return "`--target` kosong"
    if prefix and not prefix.startswith("/"):
        return "`--prefix` wajib diawali `/`"
    peta = [m for m in peta if (m["pemanggil"], m["target"]) != (pemanggil, target)]
    peta.append({"pemanggil": pemanggil, "target": target, "repo": repo, "prefix": prefix})
    save_layanan(root, peta)
    return ""


def layanan_hapus(root: Path, pemanggil: str, target: str) -> str:
    peta, err = load_layanan(root)
    if err:
        return err
    keep = [m for m in peta if (m["pemanggil"], m["target"]) != (pemanggil, target)]
    if len(keep) == len(peta):
        return f"pemetaan `{pemanggil}` → `{target}` tidak ada"
    save_layanan(root, keep)
    return ""


# ------------------------------------------------------------------ CLI

def _report_path(root: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else root / p


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new")
    p_new.add_argument("--slug", required=True)
    p_new.add_argument("--objective", required=True)
    p_new.add_argument("--lingkup", required=True, help="proyek dipisah koma; `.` untuk repo langsung di root")
    p_new.add_argument("--repo", required=True, help="dir repo yang disisir, dipisah koma")
    p_list = sub.add_parser("list")
    p_seam = sub.add_parser("seam")
    p_check = sub.add_parser("check")
    for p in (p_seam, p_check):
        p.add_argument("--report", required=True)
    p_seam.add_argument("--write", action="store_true", help="tulis ulang tabel `## Jahitan` laporan")
    p_lay = sub.add_parser("layanan")
    p_lay.add_argument("aksi", choices=("list", "set", "hapus"))
    p_lay.add_argument("--pemanggil", default="")
    p_lay.add_argument("--target", default="")
    p_lay.add_argument("--repo", default="")
    p_lay.add_argument("--prefix", default="")
    for p in (p_new, p_list, p_seam, p_check, p_lay):
        p.add_argument("--root", default=None, help="root multi-repo; default cwd")
        p.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root or ".").resolve()

    if args.cmd == "new":
        rel, err = new_report(root, args.slug, args.objective, split_list(args.lingkup), split_list(args.repo))
        print(dump_json({"status": "FAIL" if err else "OK", "berkas": rel, "galat": err}) if args.json
              else (err or f"Tertulis: {rel}"))
        return 1 if err else 0

    if args.cmd == "list":
        out = list_reports(root)
        if args.json:
            print(dump_json(out))
        else:
            lines = [f"LAPORAN: {len(out['laporan'])} di {EXPLORE_DIR}"]
            lines += [f"- {r['berkas']}{' [BASI]' if r['basi'] else ''} · {r['confidence']} · {r['objective']}"
                      for r in out["laporan"]]
            lines += [f"- {r['berkas']} [RUSAK] {r['alasan']}" for r in out["rusak"]]
            print("\n".join(lines))
        return 1 if out["mode"] == "DALAM_REPO" else 0

    if args.cmd == "layanan":
        if args.aksi == "list":
            peta, err = load_layanan(root)
            print(dump_json({"peta": peta, "galat": err}) if args.json
                  else (err or "\n".join(f"- {m['pemanggil']} → {m['target']} = {m['repo']}"
                                         + (f" (prefix {m['prefix']})" if m["prefix"] else "") for m in peta)
                        or "Peta layanan kosong."))
            return 1 if err else 0
        missing = [f"--{k}" for k in (("pemanggil", "target", "repo") if args.aksi == "set" else ("pemanggil", "target"))
                   if not getattr(args, k)]
        err = (f"{', '.join(missing)} wajib untuk `layanan {args.aksi}`" if missing else
               layanan_set(root, args.pemanggil, args.target, args.repo, args.prefix) if args.aksi == "set" else
               layanan_hapus(root, args.pemanggil, args.target))
        print(dump_json({"status": "FAIL" if err else "OK", "galat": err, "berkas": LAYANAN_FILE}) if args.json
              else (err or f"Tersimpan: {LAYANAN_FILE}"))
        return 1 if err else 0

    report_path = _report_path(root, args.report)
    if args.cmd == "check":
        c, _rep = run_check(root, report_path)
        print(dump_json({"status": "PASS" if c.ok else "FAIL", "report": args.report, "checks": c.results})
              if args.json else format_check(args.report, c))
        return 0 if c.ok else 1

    text = read_text(report_path)
    layanan, err = load_layanan(root)
    if text is None or err:
        msg = err or f"laporan `{args.report}` tidak ada atau tidak terbaca"
        print(dump_json({"status": "FAIL", "galat": msg}) if args.json else msg)
        return 1
    rep = parse_report(text)
    rows = seam_rows(rep, scan(root), layanan)
    table = render_seam(rows)
    if args.write:
        try:
            write_atomic(report_path, replace_section(text, "Jahitan", table))
        except (ValueError, OSError) as exc:
            print(dump_json({"status": "FAIL", "galat": str(exc)}) if args.json else str(exc))
            return 1
    print(dump_json({"status": "OK", "baris": rows, "ditulis": bool(args.write)}) if args.json else table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
