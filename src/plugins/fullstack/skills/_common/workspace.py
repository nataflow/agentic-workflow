#!/usr/bin/env python3
"""Peta root multi-repo plugin `fullstack`: `scan` (proyek, repo, profil) dan `peta` (`.fullstack/PETA.md`).

    python3 workspace.py scan [--root <dir>] [--json]
    python3 workspace.py peta [--root <dir>] [--write] [--json]
    python3 workspace.py abaikan list|tambah <pola>|hapus <pola> [--root <dir>] [--json]

`scan` exit 0 bila minimal satu profil `VALID`, 1 bila tidak atau root berada di dalam repo git.
`peta` membangun peta aplikasi dari profil repo dan `layanan.json` saja, tanpa membaca kode (K12–K15).
Isi BE di-parse dari `domain-map.md`/`surface-map.md`; isi FE dikutip dari `structure.md` dan tabel
`surface-map.md`. Baris di luar format masuk `## Belum terpetakan`, bukan ditebak. `peta` exit 1 hanya bila
root berada di dalam repo git. `abaikan` mengelola `.fullstack/abaikan`: pola proyek/repo yang dikecualikan dari
semua skrip fullstack (Langkah 22).

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
    ABAIKAN_FILE,
    BATAS_TERTINGGAL,
    NAMA_PLUGIN,
    PETA_FILE,
    arahan_profil,
    cell,
    clean_pola,
    dump_json,
    find_repos,
    inside_git,
    load_layanan,
    read_text,
    scan,
    stamp,
    write_atomic,
)

KUTIPAN_MAX = 400
# `<kunci>: <isi>`, boleh berawalan butir `- `; kunci tanpa titik dua, pipa, atau backtick.
LINE = re.compile(r"^\s*(?:[-*]\s+)?([^\s:|#<>`][^:|<>`]*?)\s*:\s+(.+?)\s*$")
KEY = re.compile(r"^[a-z][a-z0-9_-]*$")


# ------------------------------------------------------------------ parser profil

def _content_lines(text: str):
    fence = False
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("```"):
            fence = not fence
            continue
        if fence or not line or line.startswith(("#", "<!--", ">")) or line.lower() == "tidak terdeteksi":
            continue
        yield no, raw


def parse_domain_map(text: str) -> Tuple[List[Dict[str, str]], List[str]]:
    """Baris `<domain>: <path> · <permukaan> · entry <file>#<simbol>` → (baris, nomor baris di luar format)."""
    rows: List[Dict[str, str]] = []
    bad: List[str] = []
    for no, raw in _content_lines(text):
        m = LINE.match(raw)
        parts = [p.strip() for p in m.group(2).split(" · ")] if m else []
        if len(parts) != 3 or not parts[2].startswith("entry "):
            bad.append(str(no))
            continue
        rows.append({"domain": m.group(1), "path": parts[0], "permukaan": parts[1], "entry": parts[2][6:].strip()})
    return rows, bad


def parse_be_surface(text: str) -> Tuple[List[str], Optional[str]]:
    """(kunci permukaan, isi baris `external:` atau None)."""
    keys: List[str] = []
    external = None
    for _no, raw in _content_lines(text):
        m = LINE.match(raw)
        if not m or not KEY.match(m.group(1)):
            continue
        keys.append(m.group(1))
        if m.group(1) == "external":
            external = m.group(2)
    return keys, external


def parse_fe_surface(text: str) -> List[str]:
    """Nama permukaan dari kolom pertama tabel `surface-map.md` frontend."""
    names: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = line.strip("|").split("|")
        first = cells[0].strip().replace("**", "").replace("`", "").strip()
        if not first or set(first) <= set("-: ") or first.lower() == "surface domain":
            continue
        names.append(first)
    return names


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def quote_bullet(text: str, label: str) -> Optional[str]:
    """Isi butir `**<label>**`: teks sesudah label, atau anak butirnya bila kosong. Dipotong `KUTIPAN_MAX`."""
    lines = text.splitlines()
    marker = f"**{label}**"
    for i, raw in enumerate(lines):
        if marker not in raw:
            continue
        after = raw.split(marker, 1)[1].strip().lstrip(":").strip()
        if not after:
            base = _indent(raw)
            parts = []
            for nxt in lines[i + 1:]:
                if not nxt.strip() or _indent(nxt) <= base:
                    break
                parts.append(re.sub(r"^\s*[-*]\s+", "", nxt).strip())
            after = "; ".join(parts)
        if not after:
            return None
        if len(after) <= KUTIPAN_MAX:
            return after
        cut = after[:KUTIPAN_MAX - 1].rstrip()
        return cut + ("`" if cut.count("`") % 2 else "") + "…"     # backtick terpotong ditutup
    return None


# ------------------------------------------------------------------ model peta

def _profile_file(root: Path, repo_dir: str, prof: Dict[str, Any], name: str) -> Optional[str]:
    return read_text(root / repo_dir / prof["lokasi"] / name)


def _be_card(root: Path, repo: Dict[str, Any], prof: Dict[str, Any], gaps: List[str]) -> Dict[str, Any]:
    card: Dict[str, Any] = {"peran": "BE", "domain": [], "permukaan": [], "external": None}
    text = _profile_file(root, repo["dir"], prof, "domain-map.md")
    if text is None:
        gaps.append(f"`{repo['dir']}`: `domain-map.md` tidak ada atau tidak terbaca")
    else:
        card["domain"], bad = parse_domain_map(text)
        if bad:
            gaps.append(f"`{repo['dir']}`: `domain-map.md` baris {', '.join(bad)} di luar format "
                        "`<domain>: <path> · <permukaan> · entry <file>#<simbol>`")
    text = _profile_file(root, repo["dir"], prof, "surface-map.md")
    if text is None:
        gaps.append(f"`{repo['dir']}`: `surface-map.md` (BE) tidak ada atau tidak terbaca")
    else:
        card["permukaan"], card["external"] = parse_be_surface(text)
    return card


def _fe_card(root: Path, repo: Dict[str, Any], prof: Dict[str, Any], gaps: List[str]) -> Dict[str, Any]:
    card: Dict[str, Any] = {"peran": "FE", "permukaan": [], "fitur": None, "rute": None}
    text = _profile_file(root, repo["dir"], prof, "structure.md")
    if text is None:
        gaps.append(f"`{repo['dir']}`: `structure.md` tidak ada atau tidak terbaca")
    else:
        card["fitur"] = quote_bullet(text, "Features Path")
        card["rute"] = quote_bullet(text, "Route Definitions")
        for label, key in (("Features Path", "fitur"), ("Route Definitions", "rute")):
            if card[key] is None:
                gaps.append(f"`{repo['dir']}`: butir `**{label}**` tidak ada di `structure.md`")
    text = _profile_file(root, repo["dir"], prof, "surface-map.md")
    if text is None:
        gaps.append(f"`{repo['dir']}`: `surface-map.md` (FE) tidak ada atau tidak terbaca")
    else:
        card["permukaan"] = parse_fe_surface(text)
    return card


def build_peta(root: Path) -> Dict[str, Any]:
    sc = scan(root)
    model: Dict[str, Any] = {"root": sc["root"], "mode": sc["mode"], "ringkasan": sc["proyek"],
                             "terpotong": sc["terpotong"], "proyek": [], "hubungan": [], "belum_terpetakan": [],
                             "dikecualikan": sc["dikecualikan"]}
    if sc["mode"] == "DALAM_REPO":
        return model
    gaps: List[str] = model["belum_terpetakan"]
    gaps.extend(sc["abaikan"]["galat"])
    by_proyek: Dict[str, List[Dict[str, Any]]] = {}
    for repo in sc["repo"]:
        cards = []
        for prof in repo["profil"]:
            if prof["status"] != "VALID":
                gaps.append(f"`{repo['dir']}`: profil {prof['peran'] or '?'} berstatus {prof['status']} — "
                            + arahan_profil(repo["dir"], prof))
                continue
            card = (_be_card if prof["peran"] == "BE" else _fe_card)(root, repo, prof, gaps)
            card.update({"stack": prof["stack"], "info": prof["info"], "tertinggal": prof["tertinggal"],
                         "hilang": prof["hilang"], "plugin": prof["plugin"]})
            if prof["hilang"]:
                gaps.append(f"`{repo['dir']}`: profil {prof['peran']} kehilangan {', '.join(prof['hilang'])} — "
                            + arahan_profil(repo["dir"], prof))
            cards.append(card)
        if not repo["profil"]:
            gaps.append(f"`{repo['dir']}`: tanpa profil — " + arahan_profil(repo["dir"], None))
        by_proyek.setdefault(repo["proyek"], []).append({"dir": repo["dir"], "head": repo["head"], "kartu": cards,
                                                         "profil": repo["profil"]})
    for proyek in sorted(by_proyek):
        model["proyek"].append({"nama": proyek, "repo": by_proyek[proyek]})
    for name in sc["terpotong"]:
        gaps.append(f"`{name}`: melewati plafon 60 repo, tidak dipindai")
    model["hubungan"] = _hubungan(root, model, gaps)
    return model


def _hubungan(root: Path, model: Dict[str, Any], gaps: List[str]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for proyek in model["proyek"]:
        be = [r["dir"] for r in proyek["repo"] if any(c["peran"] == "BE" for c in r["kartu"])]
        fe = [r["dir"] for r in proyek["repo"] if any(c["peran"] == "FE" for c in r["kartu"])]
        if len(be) == 1:
            rows.extend({"pemanggil": d, "target": "—", "penerima": be[0], "sumber": "satu BE di proyek"} for d in fe)
    peta, err = load_layanan(root)
    if err:
        gaps.append(err + "; hubungan dari `layanan.json` dilewati")
    mapped = set()
    for item in peta:
        rows.append({"pemanggil": item["pemanggil"], "target": item["target"], "penerima": item["repo"],
                     "sumber": "layanan.json"})
        mapped.add(item["pemanggil"])
    for proyek in model["proyek"]:
        for repo in proyek["repo"]:
            for card in repo["kartu"]:
                if card["peran"] == "BE" and card.get("external") and repo["dir"] not in mapped:
                    rows.append({"pemanggil": repo["dir"], "target": "baris `external:` profil", "penerima": "—",
                                 "sumber": "belum dipetakan"})
    return sorted(rows, key=lambda r: (r["pemanggil"], r["target"], r["penerima"]))


# ------------------------------------------------------------------ render

def _nama_proyek(nama: str) -> str:
    return "(root)" if nama == "." else nama


def _profil_line(card: Dict[str, Any], dir_: str) -> str:
    n = card["tertinggal"]
    if n is None:
        return "- Profil: VALID · belum pernah di-commit, kesegaran tidak terukur"
    line = f"- Profil: VALID · tertinggal {n} commit"
    if n > BATAS_TERTINGGAL:
        line += f" — **profil tertinggal**, `cd {dir_}` lalu jalankan `{NAMA_PLUGIN[card['plugin']]}:profile` mode REFRESH"
    return line


def render(model: Dict[str, Any], when: str) -> str:
    n_repo = sum(len(p["repo"]) for p in model["proyek"])
    excluded = model.get("dikecualikan", [])
    n_skip = sum(e.get("repo", 1) for e in excluded)
    out = [f"# Peta Aplikasi — {Path(model['root']).name}", "",
           f"Dibangun: {when} · {len(model['proyek'])} proyek · {n_repo} repo"
           + (f" · {n_skip} repo dikecualikan" if n_skip else "")
           + " · sumber: profil repo dan `layanan.json`, tanpa membaca kode.", "",
           "## Ringkasan", "",
           "| Proyek | Repo BE | Repo FE | Tanpa profil | Profil tertinggal |",
           "|---|---|---|---|---|"]
    out += [f"| `{_nama_proyek(p['nama'])}` | {p['be']} | {p['fe']} | {p['tanpa_profil']} | {p['tertinggal']} |"
            for p in model["ringkasan"]] or ["| — | 0 | 0 | 0 | 0 |"]
    for proyek in model["proyek"]:
        out += ["", f"## Proyek `{_nama_proyek(proyek['nama'])}`"]
        for repo in proyek["repo"]:
            sha = repo["head"] or "tanpa commit"
            if not repo["kartu"]:
                status = ", ".join(p["status"] for p in repo["profil"]) or "ABSENT"
                out += ["", f"### `{repo['dir']}` — tanpa profil valid · HEAD {sha}", "",
                        f"- Profil: {status} · lihat `## Belum terpetakan`"]
                continue
            for card in repo["kartu"]:
                info = card["info"]
                if card["peran"] == "BE":
                    extra = info.get("architecture", "")
                    out += ["", f"### `{repo['dir']}` — BE · {card['stack']}" + (f" · {extra}" if extra else "")
                            + f" · HEAD {sha}", "", _profil_line(card, repo["dir"]),
                            "- Permukaan: " + (", ".join(card["permukaan"]) or "tidak terbaca"),
                            "- Panggilan keluar: " + (card["external"] or "tidak ada baris `external:` di profil"),
                            "", "| Domain | Path | Permukaan | Entry |", "|---|---|---|---|"]
                    out += [f"| {cell(d['domain'])} | `{cell(d['path'])}` | {cell(d['permukaan'])} | "
                            f"`{cell(d['entry'])}` |" for d in card["domain"]] or ["| — | — | — | — |"]
                else:
                    extra = info.get("framework") or info.get("platform", "")
                    out += ["", f"### `{repo['dir']}` — FE · {card['stack']}" + (f" · {extra}" if extra else "")
                            + f" · HEAD {sha}", "", _profil_line(card, repo["dir"]),
                            "- Permukaan: " + (", ".join(card["permukaan"]) or "tidak terbaca"),
                            "- Fitur: " + (card["fitur"] or "tidak terbaca"),
                            "- Rute: " + (card["rute"] or "tidak terbaca")]
    out += ["", "## Hubungan antar aplikasi", ""]
    if model["hubungan"]:
        out += ["| Pemanggil | Target | Penerima | Sumber |", "|---|---|---|---|"]
        out += [f"| `{cell(h['pemanggil'])}` | {cell(h['target'])} | "
                + (f"`{cell(h['penerima'])}`" if h["penerima"] != "—" else "—") + f" | {cell(h['sumber'])} |"
                for h in model["hubungan"]]
    else:
        out.append("- Tidak ada.")
    out += ["", "## Dikecualikan", ""]
    if excluded:
        out += [f"Dari `{ABAIKAN_FILE}`.", "", "| Proyek/Repo | Pola |", "|---|---|"]
        out += [f"| `{cell(e['dir'])}`" + (f" (proyek, {e['repo']} repo)" if e["jenis"] == "proyek" else "")
                + f" | `{cell(e['pola'])}` |" for e in excluded]
    else:
        out.append("- Tidak ada.")
    out += ["", "## Belum terpetakan", ""]
    out += [f"- {g}" for g in model["belum_terpetakan"]] or ["- Tidak ada."]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ abaikan (22)

def _abaikan_lines(root: Path) -> Tuple[List[str], str]:
    path = root / ABAIKAN_FILE
    if not path.exists():
        return [], ""
    text = read_text(path) if path.is_file() else None
    if text is None:
        return [], f"`{ABAIKAN_FILE}` tidak terbaca; perbaiki atau hapus berkasnya"
    return text.splitlines(), ""


def _pola_baris(line: str) -> str:
    """Pola bersih dari satu baris berkas, atau '' untuk komentar, baris kosong, dan baris tidak sah."""
    text = line.strip()
    return "" if not text or text.startswith("#") else clean_pola(text)[0]


def _terkena(root: Path, pola: str) -> List[str]:
    """Proyek/repo di root yang dikenai `pola`."""
    _kept, _cut, excluded = find_repos(root, [pola])
    return [e["dir"] + (" (proyek)" if e["jenis"] == "proyek" else "") for e in excluded]


def abaikan(root: Path, aksi: str, raw: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"berkas": ABAIKAN_FILE, "aksi": aksi, "pola": "", "terkena": [], "galat": "",
                           "peringatan": ""}
    if inside_git(root):
        out["galat"] = "root berada di dalam repo git"
        return out
    lines, err = _abaikan_lines(root)
    if err:
        out["galat"] = err
        return out
    current = [p for p in (_pola_baris(ln) for ln in lines) if p]
    if aksi == "list":
        out["daftar"] = [{"pola": p, "terkena": _terkena(root, p)} for p in current]
        out["tidak_sah"] = [ln.strip() for ln in lines
                            if ln.strip() and not ln.strip().startswith("#") and not _pola_baris(ln)]
        return out
    pola, err = clean_pola(raw)
    out["pola"] = pola or raw.strip()
    if err:
        out["galat"] = f"pola `{raw.strip()}` {err}"
        return out
    if aksi == "tambah":
        if pola in current:
            out["galat"] = f"pola `{pola}` sudah ada"
            return out
        new_lines = lines + [pola]
    else:
        if pola not in current:
            out["galat"] = f"pola `{pola}` tidak ada di `{ABAIKAN_FILE}`"
            return out
        new_lines = [ln for ln in lines if _pola_baris(ln) != pola]
    write_atomic(root / ABAIKAN_FILE, "\n".join(new_lines) + ("\n" if new_lines else ""))
    out["terkena"] = _terkena(root, pola)
    if aksi == "tambah" and not out["terkena"]:
        out["peringatan"] = "pola belum mengenai proyek atau repo mana pun; tetap disimpan"
    return out


# ------------------------------------------------------------------ CLI

def _scan_text(sc: Dict[str, Any]) -> str:
    if sc["mode"] == "DALAM_REPO":
        return (f"SCAN: {sc['root']} [FAIL]\nRoot berada di dalam repo git. `fullstack` berjalan dari root yang "
                "menampung repo (mis. folder induk `api/` dan `frontend/`). Di dalam repo, pakai "
                "`backend:tech-lead` atau `frontend:lead`.")
    lines = [f"SCAN: {sc['root']} [{'PASS' if sc['valid'] else 'FAIL'}] ({len(sc['repo'])} repo, "
             f"{sc['valid']} profil VALID)"]
    for r in sc["repo"]:
        prof = "; ".join(f"{p['peran'] or '?'} {p['stack'] or '-'} {p['status']}"
                         + (f" tertinggal {p['tertinggal']}" if p["tertinggal"] is not None else "")
                         for p in r["profil"]) or "tanpa profil"
        lines.append(f"- {r['dir']} (proyek {_nama_proyek(r['proyek'])}, HEAD {r['head'] or '-'}): {prof}")
    if sc["terpotong"]:
        lines.append("Terpotong plafon 60 repo: " + ", ".join(sc["terpotong"]))
    if sc.get("dikecualikan"):
        lines.append("Dikecualikan: " + ", ".join(f"{e['dir']} (pola {e['pola']})" for e in sc["dikecualikan"]))
    lines += [f"Peringatan: {g}" for g in sc.get("abaikan", {}).get("galat", [])]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "peta", "abaikan"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=None, help="root multi-repo; default cwd")
        p.add_argument("--json", action="store_true")
        if name == "peta":
            p.add_argument("--write", action="store_true", help=f"tulis ke <root>/{PETA_FILE}")
        if name == "abaikan":
            p.add_argument("aksi", choices=("list", "tambah", "hapus"))
            p.add_argument("pola", nargs="?", default="")
    args = ap.parse_args(argv)
    root = Path(args.root or ".").resolve()

    if args.cmd == "abaikan":
        out = abaikan(root, args.aksi, args.pola)
        if args.json:
            print(dump_json(out))
        elif out["galat"]:
            print(f"ABAIKAN FAIL: {out['galat']}")
        elif args.aksi == "list":
            rows = [f"- {d['pola']}: " + (", ".join(d["terkena"]) or "belum mengenai apa pun") for d in out["daftar"]]
            rows += [f"- tidak sah: {t}" for t in out["tidak_sah"]]
            print("\n".join(rows) or f"`{ABAIKAN_FILE}` kosong atau belum ada.")
        else:
            print(f"ABAIKAN {args.aksi.upper()}: `{out['pola']}` → " + (", ".join(out["terkena"]) or "-")
                  + (f"\nPeringatan: {out['peringatan']}" if out["peringatan"] else ""))
        return 1 if out["galat"] else 0

    if args.cmd == "scan":
        sc = scan(root)
        print(dump_json(sc) if args.json else _scan_text(sc))
        return 0 if sc["valid"] and sc["mode"] == "WORKSPACE" else 1

    model = build_peta(root)
    if model["mode"] == "DALAM_REPO":
        print(dump_json(model) if args.json else _scan_text({"mode": "DALAM_REPO", "root": model["root"]}))
        return 1
    text = render(model, stamp())
    if args.write:
        try:
            write_atomic(root / PETA_FILE, text)
        except OSError as exc:
            msg = f"Gagal menulis `{PETA_FILE}`: {exc}"
            print(dump_json({**model, "galat": msg}) if args.json else msg)
            return 1
        model["berkas"] = PETA_FILE
    print(dump_json(model) if args.json else (f"Tertulis: {PETA_FILE}" if args.write else text.rstrip()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
