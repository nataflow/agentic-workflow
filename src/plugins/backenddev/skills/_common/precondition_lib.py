#!/usr/bin/env python3
"""Helper bersama skrip prasyarat lintas skill `backenddev`.

Berisi **hanya** primitif yang byte-identik di seluruh skrip pemakainya. Check
itu sendiri tetap tinggal di skripnya masing-masing: tiap skill menagih hal yang
berbeda, memberi pesan remediasi yang berbeda, dan menomori check-nya sendiri —
menyatukannya akan menyeragamkan hal yang memang seharusnya berbeda.

Yang diekstrak ke sini sengaja sempit: uji izin tulis beserta pencarian
direktori induknya, dua fungsi yang tersalin apa adanya di sembilan skrip.

Zero external dependencies (Python Standard Library only).
"""

import os
from pathlib import Path
from typing import Tuple


def nearest_existing_ancestor(path: Path) -> Path:
    """Naik ke atas sampai menemukan direktori yang benar-benar sudah ada."""
    probe = path
    while not probe.exists():
        parent = probe.parent
        if parent == probe:
            break
        probe = parent
    return probe


def probe_writable(path: Path) -> Tuple[bool, str]:
    """Uji izin tulis tanpa membuat direktori dan tanpa menulis berkas uji.

    Skrip prasyarat hanya memeriksa; pembuatan direktori adalah wewenang fase
    kerja skill yang memilikinya. Yang diuji adalah direktori induk terdekat
    yang sudah ada, karena di situlah direktori target nanti akan dibuat.

    Mengembalikan (ok, keterangan).
    """
    anchor = nearest_existing_ancestor(path)
    if not anchor.is_dir():
        return False, f"{anchor} ada tetapi bukan direktori"
    if not os.access(anchor, os.W_OK | os.X_OK):
        return False, f"{anchor} tidak memiliki izin tulis"
    return True, str(anchor)


def profile_staleness(root: Path, source_root: str) -> Tuple[str, str]:
    """Nilai kesegaran `.claude/profile/` terhadap kode yang dipetakannya.

    Profil yang tertinggal di belakang kode tidak pernah gagal dengan suara:
    `domain-map.md` yang basi melebarkan `Batas cakupan` explorer ke seluruh
    `source_root`, dan `surface-map.md` yang basi membuat permukaan baru tidak
    terdaftar. Keduanya menurunkan daya jangkau eksplorasi tanpa satu pun
    kegagalan tercatat, dan itulah yang dibuat terbaca di sini.

    Vonisnya **tidak pernah menggagalkan** skrip prasyarat — profil basi adalah
    keadaan wajar pada repo yang bergerak, bukan alasan menghentikan kerja.
    Pemanggil menempelkannya sebagai catatan degradasi, sejalan dengan banner
    `TERDEGRADASI` Check E `plan`.

    Mengembalikan (vonis, keterangan) dengan vonis salah satu dari
    `SEGAR`, `BASI`, atau `TAK_TERNILAI`.
    """
    import subprocess

    profile_dir = root / ".claude" / "profile"
    if not profile_dir.is_dir():
        return "TAK_TERNILAI", ".claude/profile/ tidak ada"

    sr = (source_root or "").strip().strip("/")
    if not sr:
        return "TAK_TERNILAI", "source_root kosong di index.json"
    if not (root / sr).exists():
        return "TAK_TERNILAI", f"source_root '{sr}' tidak ada di disk"

    def _git(*args: str) -> str:
        try:
            out = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        return out.stdout.strip() if out.returncode == 0 else ""

    if _git("rev-parse", "--is-inside-work-tree") != "true":
        return "TAK_TERNILAI", "bukan repositori git"

    profile_sha = _git("log", "-1", "--format=%H", "--", ".claude/profile")
    if not profile_sha:
        return "TAK_TERNILAI", "profil belum pernah masuk riwayat git"

    # Rentang commit, bukan rentang waktu: `--since` berbasis approxidate dan
    # tidak menerima epoch mentah, sehingga penyaringnya diam-diam tidak
    # berlaku dan tiap commit ikut terhitung.
    lag = _git("rev-list", "--count", f"{profile_sha}..HEAD", "--", sr)
    if not lag.isdigit():
        return "TAK_TERNILAI", f"riwayat '{sr}' tidak terbaca"

    n = int(lag)
    if n == 0:
        return "SEGAR", f"nol commit menyentuh '{sr}' sesudah profil terakhir diperbarui"
    return "BASI", (
        f"{n} commit menyentuh '{sr}' sesudah profil terakhir diperbarui — "
        "batas cakupan explorer dan daftar permukaan berpotensi tertinggal"
    )
