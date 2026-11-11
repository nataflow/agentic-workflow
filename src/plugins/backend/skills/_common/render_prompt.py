#!/usr/bin/env python3
"""Render Prompt — hidrasi template dispatcher ke laci `.explore/prompt/` (32 T1).

Main loop tidak lagi memuat badan template dispatcher ke konteksnya. Skrip ini:

1. mengambil blok template prompt dispatcher — blok berpagar pertama yang dibuka
   ```` ````markdown ```` atau ```` ```markdown ```` — tanpa mengubah satu karakter pun;
2. membaca daftar slot dari tabel `### Slot Hidrasi` berkas yang sama (baris berawalan
   `` | `{nama}` ``). Slot bertanda `[OPTIONAL]` atau "Diisi hanya ..." opsional; sisanya wajib;
3. mengisi slot dari `--slot nama=nilai` (berulang) dan/atau `--slots-json <berkas>`
   (untuk nilai multi-baris). Kurung kurawal yang bukan slot tabel (`AC-{n}`, `BR-{n}`)
   dibiarkan apa adanya;
4. menghapus utuh tiap baris yang memuat slot opsional bernilai kosong — aturan
   "hapus barisnya utuh" Slot Hidrasi;
5. menulis prompt jadi ke `--out`, yang wajib berada di laci prompt:
   `backenddev/docs/.explore/prompt/<nama>.md` (dispatch gerbang) atau
   `backenddev/docs/<taskdir>/.explore/prompt/<nama>.md` (skill hilir). Subdirektori
   `prompt/` menjaga prompt jadi dari panen laci (`validate_briefs.py` hanya memindai
   `.explore/*.md`).

Prompt subagent lalu cukup satu kalimat, dicetak skrip ini apa adanya:
"Baca dan jalankan instruksi di `<out>`; jangan menyuntingnya."

Exit: 0 = prompt ditulis; 1 = slot wajib kosong, slot tak dikenal, atau slot tabel
tersisa mentah (prompt tidak ditulis); 2 = template tak terbaca, tanpa blok template,
atau `--out` di luar laci prompt.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

OUT_RE = re.compile(r"^backenddev/docs/(?:[^/]+/)?\.explore/prompt/[A-Za-z0-9._-]+\.md$")
SLOT_ROW = re.compile(r"^\|\s*`\{([a-z_]+)\}`\s*\|(.*)$")


class RenderError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def template_block(text: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(`{3,})markdown\s*$", line)
        if not m:
            continue
        fence = m.group(1)
        for j in range(i + 1, len(lines)):
            if lines[j].rstrip() == fence:
                return "\n".join(lines[i + 1:j]) + "\n"
        raise RenderError(2, f"blok template dibuka di baris {i + 1} tanpa pagar penutup `{fence}`")
    raise RenderError(2, "tidak ada blok template (```` ```markdown ```` / ```` ````markdown ````)")


def slot_table(text: str) -> Dict[str, bool]:
    """nama slot → wajib?"""
    m = re.search(r"^### Slot Hidrasi[ \t]*$", text, re.M)
    if not m:
        raise RenderError(2, "tidak ada seksi `### Slot Hidrasi`")
    sec = text[m.end():]
    nxt = re.search(r"^#{2,3} ", sec, re.M)
    sec = sec[:nxt.start()] if nxt else sec
    slots: Dict[str, bool] = {}
    for line in sec.splitlines():
        row = SLOT_ROW.match(line.strip())
        if row:
            rest = row.group(2)
            slots[row.group(1)] = not ("[OPTIONAL]" in rest or "Diisi hanya" in rest)
    if not slots:
        raise RenderError(2, "tabel `### Slot Hidrasi` tidak memuat satu baris slot pun")
    return slots


def render(template_text: str, values: Dict[str, str]) -> Tuple[str, List[str], List[str]]:
    body = template_block(template_text)
    slots = slot_table(template_text)
    unknown = sorted(set(values) - set(slots))
    if unknown:
        raise RenderError(1, f"slot tak dikenal template ini: {', '.join(unknown)} (sah: {', '.join(sorted(slots))})")
    used = [s for s in slots if "{" + s + "}" in body]
    missing = [s for s in used if slots[s] and not values.get(s, "").strip()]
    if missing:
        raise RenderError(1, f"slot wajib kosong: {', '.join(missing)}")
    empty_optional = [s for s in used if not slots[s] and not values.get(s, "").strip()]
    kept = []
    for line in body.splitlines():
        if any("{" + s + "}" in line for s in empty_optional):
            continue
        kept.append(line)
    body = "\n".join(kept) + "\n"
    body = re.sub(r"\n{3,}", "\n\n", body)
    pattern = re.compile(r"\{(" + "|".join(map(re.escape, slots)) + r")\}")
    body = pattern.sub(lambda m: values.get(m.group(1), m.group(0)), body)
    # Nilai slot tidak pernah dipindai ulang: sisa mentah hanya mungkin dari teks template.
    filled = [s for s in used if values.get(s, "").strip()]
    return body, filled, empty_optional


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--template", required=True, help="Berkas dispatcher, mis. <plugin>/skills/plan/dispatcher/explorer.md")
    ap.add_argument("--slot", action="append", default=[], help="nama=nilai (berulang)")
    ap.add_argument("--slots-json", help="Berkas JSON {nama: nilai} untuk nilai multi-baris")
    ap.add_argument("--out", required=True, help="Laci prompt: backenddev/docs/[<taskdir>/].explore/prompt/<nama>.md")
    ap.add_argument("--root", default=".", help="Root repositori (path --out relatif terhadapnya)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    def emit(status: str, code: int, **extra) -> int:
        if a.json:
            print(json.dumps({"status": status, **extra}, ensure_ascii=False))
        elif status == "PASS":
            print(f"PASS prompt {extra['out']} ({extra['karakter']} karakter) — prompt subagent: "
                  f"\"Baca dan jalankan instruksi di `{extra['out']}`; jangan menyuntingnya.\"")
        else:
            print(f"{status}: {extra.get('reason', '')}", file=sys.stderr)
        return code

    try:
        out_rel = a.out.replace("\\", "/").lstrip("./") if not Path(a.out).is_absolute() else None
        if out_rel is None or not OUT_RE.match(out_rel) or ".." in out_rel.split("/"):
            raise RenderError(2, f"`--out` {a.out} di luar laci prompt "
                                 "(backenddev/docs/[<taskdir>/].explore/prompt/<nama>.md, path relatif root repo)")
        values: Dict[str, str] = {}
        if a.slots_json:
            data = json.loads(Path(a.slots_json).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise RenderError(2, "--slots-json wajib objek JSON {nama: nilai}")
            values.update({str(k): "" if v is None else str(v) for k, v in data.items()})
        for item in a.slot:
            if "=" not in item:
                raise RenderError(1, f"--slot `{item}` bukan bentuk nama=nilai")
            k, v = item.split("=", 1)
            values[k.strip()] = v
        text = Path(a.template).read_text(encoding="utf-8")
        body, filled, dropped = render(text, values)
        out = Path(a.root) / out_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
    except RenderError as e:
        return emit("FAIL" if e.code == 1 else "ERROR", e.code, reason=str(e))
    except (OSError, ValueError) as e:   # UnicodeDecodeError dan JSON rusak termasuk ValueError
        return emit("ERROR", 2, reason=str(e))
    return emit("PASS", 0, out=out_rel, karakter=len(body), slot_terisi=filled, baris_opsional_dihapus=dropped,
                prompt=f"Baca dan jalankan instruksi di `{out_rel}`; jangan menyuntingnya.")


if __name__ == "__main__":
    sys.exit(main())
