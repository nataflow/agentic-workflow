#!/usr/bin/env python3
"""Prasyarat skill `fullstack:explore` (read-only).

Memvonis root sebelum peta dibangun atau scout didispatch: berkas plugin lengkap, root bukan bagian repo git, ada
repo di bawahnya, minimal satu profil `VALID`, `.fullstack/` bisa ditulis, dan `layanan.json` terbaca. Kurang dari
dua profil `VALID` → WARN (penelusuran lintas repo terbatas); `layanan.json` rusak → WARN (jalur `PETA` tetap jalan,
`seam` berhenti sampai berkas diperbaiki); `.fullstack/abaikan` tak terbaca atau berbaris tidak sah → WARN.

Exit 0 = PASS, 1 = FAIL. `--json` untuk keluaran mesin.

Standard library saja.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

COMMON = Path(__file__).resolve().parents[2] / "_common"
sys.path.insert(0, str(COMMON))
from fullstack_lib import (  # noqa: E402
    ABAIKAN_FILE,
    EXPLORE_DIR,
    FULLSTACK_DIR,
    LAYANAN_FILE,
    PETA_FILE,
    load_layanan,
    scan,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
NEEDED = ("skills/_common/fullstack_lib.py", "skills/_common/workspace.py", "skills/_common/explore.py",
          "skills/explore/dispatcher/scout.md", "skills/explore/dispatcher/explorer.md",
          "skills/explore/templates/explore-template.md", "skills/explore/templates/alur-template.md",
          "agents/repo-scout.md", "agents/backend-explorer.md", "agents/frontend-explorer.md")


def _add(results: List[Dict[str, Any]], cid: int, name: str, status: str, summary: str, action: str = "") -> None:
    results.append({"id": cid, "name": name, "status": status, "summary": summary,
                    "action": action if status != "PASS" else ""})


def _writable(root: Path) -> bool:
    d = root / FULLSTACK_DIR
    while not d.exists() and d != root:
        d = d.parent
    return d.is_dir() and os.access(str(d), os.W_OK | os.X_OK)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=None, help="root multi-repo; default cwd")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.root or ".").resolve()
    res: List[Dict[str, Any]] = []

    _add(res, 1, "Python", "PASS" if sys.version_info >= (3, 9) else "FAIL", sys.version.split()[0],
         "Pasang python3 ≥ 3.9.")
    missing = [f for f in NEEDED if not (PLUGIN_ROOT / f).is_file()]
    _add(res, 2, "Berkas plugin", "FAIL" if missing else "PASS", ", ".join(missing) or "lengkap",
         "Instalasi plugin rusak — pasang ulang plugin fullstack.")

    sc = scan(root)
    if sc["mode"] == "DALAM_REPO":
        _add(res, 3, "Root multi-repo", "FAIL", f"{root} berada di dalam repo git",
             "`fullstack` berjalan dari folder yang menampung repo (mis. induk `api/` dan `frontend/`). Di dalam "
             "repo, pakai `backend:tech-lead` atau `frontend:lead`.")
    elif sc["mode"] == "KOSONG":
        _add(res, 3, "Root multi-repo", "FAIL", "tidak ada repo git di anak atau cucu langsung root",
             "Jalankan dari folder yang berisi repo (`<root>/<repo>` atau `<root>/<proyek>/<repo>`).")
    else:
        cut = f"; terpotong plafon: {', '.join(sc['terpotong'])}" if sc["terpotong"] else ""
        _add(res, 3, "Root multi-repo", "WARN" if cut else "PASS",
             f"{len(sc['repo'])} repo di {len(sc['proyek'])} proyek{cut}",
             "Proyek yang terpotong tidak dipetakan; jalankan dari folder yang lebih sempit untuk proyek itu.")

    valid = sc["valid"]
    if sc["mode"] == "WORKSPACE":
        if valid == 0:
            _add(res, 4, "Profil repo", "FAIL", "tidak ada profil VALID",
                 "Jalankan `backend:profile` atau `frontend:profile` dari dalam tiap repo aplikasi lebih dulu.")
        else:
            _add(res, 4, "Profil repo", "WARN" if valid < 2 else "PASS", f"{valid} profil VALID",
                 "Hanya satu profil VALID: penelusuran lintas repo terbatas. Profilkan repo lain bila perlu.")
        _add(res, 5, "Folder .fullstack", "PASS" if _writable(root) else "FAIL",
             f"{FULLSTACK_DIR}/ bisa ditulis" if _writable(root) else f"{FULLSTACK_DIR}/ tidak bisa ditulis",
             f"Beri izin tulis di `{root}`.")
        _peta, err = load_layanan(root)
        _add(res, 6, "layanan.json", "WARN" if err else "PASS", err or "terbaca atau belum ada",
             f"Perbaiki atau hapus `{LAYANAN_FILE}` sebelum jalur TELUSUR menjalankan `seam`.")
        ab = sc["abaikan"]
        _add(res, 7, "abaikan", "WARN" if ab["galat"] else "PASS",
             "; ".join(ab["galat"]) or (f"{len(ab['pola'])} pola, {len(sc['dikecualikan'])} dikecualikan"
                                        if ab["ada"] else "belum ada"),
             f"Perbaiki baris yang disebut di `{ABAIKAN_FILE}` lewat `workspace.py abaikan`; baris tidak sah "
             "diabaikan sehingga proyek/repo-nya tetap dipetakan.")

    failed = any(r["status"] == "FAIL" for r in res)
    resolved = {"root": str(root), "mode": sc["mode"], "repo": str(len(sc["repo"])),
                "dikecualikan": str(len(sc["dikecualikan"])), "profil_valid": str(valid),
                "proyek": ",".join(p["nama"] for p in sc["proyek"]) or "-",
                "peta": PETA_FILE if (root / PETA_FILE).is_file() else "belum ada",
                "laporan": str(len(list((root / EXPLORE_DIR).glob("*.md")))) if (root / EXPLORE_DIR).is_dir() else "0"}
    if args.json:
        print(json.dumps({"status": "FAIL" if failed else "PASS", "resolved": resolved, "checks": res},
                         indent=2, ensure_ascii=False))
    else:
        warned = sum(1 for r in res if r["status"] == "WARN")
        label = "FAIL" if failed else ("PASS (WARN)" if warned else "PASS")
        lines = [f"CHECK: fullstack:explore [{label}] ({sum(1 for r in res if r['status'] == 'PASS')}/{len(res)} passed)"]
        for r in res:
            lines.append(f"[{r['id']}] {r['name']:<18} : {r['status']} ({r['summary']})")
            if r["action"]:
                lines.append(f"    * Tindakan: {r['action']}")
        lines.append("Terselesaikan: " + "; ".join(f"{k}={v}" for k, v in resolved.items()))
        print("\n".join(lines))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
