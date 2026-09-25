#!/usr/bin/env python3
"""Helper bersama skrip prasyarat lintas skill `backenddev`.

Berisi **hanya** primitif yang byte-identik di seluruh skrip pemakainya. Check
itu sendiri tetap tinggal di skripnya masing-masing: tiap skill menagih hal yang
berbeda, memberi pesan remediasi yang berbeda, dan menomori check-nya sendiri —
menyatukannya akan menyeragamkan hal yang memang seharusnya berbeda.

Yang diekstrak ke sini sengaja sempit: uji izin tulis beserta pencarian
direktori induknya, dua fungsi yang tersalin apa adanya di sembilan skrip; lalu
resolver direktori profil `.claude/profile/backenddev/` beserta pemeriksa
kepemilikannya, dan pembungkus deteksi `hooks/detect.py` (fungsi yang sama
dengan yang dipakai hook SessionStart, sehingga vonis hook = vonis skrip).

Zero external dependencies (Python Standard Library only).
"""

import os
import sys
from pathlib import Path
from typing import Tuple

# Deteksi repo dan pembacaan profil tinggal di `hooks/detect.py` (identik di
# backenddev dan frontenddev) — satu implementasi untuk hook dan skrip.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
import detect as _detect  # noqa: E402

# Tiap plugin engineer punya direktori profilnya sendiri. `.claude/profile/`
# (tanpa subdirektori) adalah lokasi lama yang hanya dibaca selama masa transisi
# dan selalu disertai catatan MIGRATE.
PLUGIN = "backenddev"
PROFILE_DIR_REL = f".claude/profile/{PLUGIN}"      # satu-satunya lokasi tulis
LEGACY_PROFILE_DIR_REL = ".claude/profile"          # lokasi lama, dibaca hanya untuk MIGRATE
PROFILE_FILES = _detect.PROFILE_FILES[PLUGIN]


def resolve_profile_dir(root: Path) -> Tuple[Path, str]:
    """(direktori profil yang dibaca, catatan untuk laporan prasyarat).

    Lokasi baru selalu menang. Lokasi lama dipakai hanya bila `index.json`-nya
    milik plugin ini (field `plugin`, atau `stack` anggota daftar backenddev),
    dan selalu disertai catatan MIGRATE. Profil milik plugin lain tidak pernah
    dikembalikan: skrip melihatnya sebagai profil yang tidak ada.
    """
    own = root / PROFILE_DIR_REL
    if (own / "index.json").exists():
        return own, ""
    prof = _detect.read_profile(root, PLUGIN)
    if prof.location == "legacy" and prof.state not in ("OTHER_OWNER", "ABSENT", "INVALID_JSON"):
        return root / LEGACY_PROFILE_DIR_REL, (
            "profil backenddev masih di lokasi lama `.claude/profile/`; "
            "jalankan `backenddev:profile` mode MIGRATE")
    return own, ""


def legacy_suffix(note: str) -> str:
    """Sufiks ringkasan check PASS saat profil masih dibaca dari lokasi lama."""
    return f" — {note}" if note else ""


def foreign_owner(profile_dir: Path) -> str:
    """Nama plugin lain pemilik `<profile_dir>/index.json`, atau '' bila milik sendiri/tak terbaca."""
    data, _state = _detect.read_index(profile_dir / "index.json")
    if data is None:
        return ""
    owner = _detect.owner_of(data)
    return owner if owner and owner != PLUGIN else ""


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
    """Nilai kesegaran profil backenddev terhadap kode yang dipetakannya.

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

    profile_dir, _note = resolve_profile_dir(root)
    if not profile_dir.is_dir():
        return "TAK_TERNILAI", f"{PROFILE_DIR_REL}/ tidak ada"

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

    # Hanya berkas profil backenddev: commit profil plugin lain (mis.
    # `.claude/profile/frontenddev/`) tidak boleh me-reset vonis kesegaran.
    rel = profile_dir.relative_to(root).as_posix()
    profile_sha = _git("log", "-1", "--format=%H", "--", *(f"{rel}/{f}" for f in PROFILE_FILES))
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
