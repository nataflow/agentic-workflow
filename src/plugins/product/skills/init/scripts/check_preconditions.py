#!/usr/bin/env python3
"""Prasyarat gate `product:init` (read-only).

Memvonis ruang kerja sebelum guard konteks minimum dan sebelum satu folder pun dibuat: root bukan home atau root
filesystem, berkas plugin lengkap, jenis ruang kerja (`EMPTY` tanpa kode / `CODEBASE`) beserta mode yang
diizinkan, dan charterdir yang masih terbuka. Folder kosong tanpa git **PASS** — itu tempat `NEW_PRODUCT`.

Exit 0 = PASS, 1 = FAIL. `--json` untuk keluaran mesin.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parents[2] / "_common"
sys.path.insert(0, str(COMMON))
from charter_lib import (  # noqa: E402
    CHARTER_FILE,
    PRODUCT_DIR,
    Checker,
    detect_workspace,
    find_root,
    format_report,
    is_git_repo,
    report_json,
    workspace_problem,
)
from charter import charterdirs, classify  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
NEEDED = ("init/references/konteks-minimum.md", "discover/dispatcher/scout.md", "_common/charter.py")
OPEN_STATES = ("EMPTY", "ELICITATION", "DRAFT", "REVIEW", "DRIFT", "BROKEN")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=None, help="root ruang kerja; default root git atau cwd")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = (Path(args.root) if args.root else find_root()).resolve()
    c = Checker()

    c.add(1, "Python", sys.version_info >= (3, 9), sys.version.split()[0], "Pasang python3 ≥ 3.9.")
    missing = [f for f in NEEDED if not (PLUGIN_ROOT / "skills" / f).is_file()]
    c.add(2, "Berkas plugin", not missing, "lengkap" if not missing else ", ".join(missing),
          "Instalasi plugin rusak — pasang ulang plugin product.")
    problem = workspace_problem(root)
    c.add(3, "Ruang kerja", not problem, problem or str(root),
          "Buat folder proyek (mis. `mkdir <nama-produk> && cd <nama-produk>`) lalu jalankan ulang dari sana.")

    ws = detect_workspace(root) if not problem else {"workspace": "-", "evidence": "-"}
    modes = {"EMPTY": "NEW_PRODUCT", "CODEBASE": "NEW_FEATURE,IMPROVEMENT"}.get(ws["workspace"], "-")
    c.add(4, "Jenis ruang kerja", ws["workspace"] != "-", f"{ws['workspace']} (bukti: {ws['evidence']})",
          "Perbaiki ruang kerja (check 3) lebih dulu.")

    rows = []
    try:
        rows = [classify(root, rel) for rel in charterdirs(root)]
    except SystemExit:   # berkas rusak tidak menghentikan gerbang; `charter.py state` merinci
        pass
    open_rows = [r for r in rows if r["state"] in OPEN_STATES]
    resolved = {
        "root": str(root),
        "git": "ya" if is_git_repo(root) else "tidak",
        "workspace": ws["workspace"],
        "bukti": ws["evidence"],
        "mode_diizinkan": modes,
        "charter_terbuka": ",".join(f"{r['charterdir']}({r['state']})" for r in open_rows) or "-",
        "charter_file": f"{PRODUCT_DIR}/<slug>/{CHARTER_FILE}",
    }
    print(report_json(c.results, **resolved) if args.json
          else format_report("prasyarat product:init", c.results, resolved))
    sys.exit(0 if c.ok else 1)


if __name__ == "__main__":
    main()
