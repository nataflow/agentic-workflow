#!/usr/bin/env python3
"""Tech-Lead Precondition Validator.

Automates verification of repository preconditions before tech-lead gateway execution.
Runs checks 1 through 6 in a single pass and produces a compact, actionable report.

Mode `--read-only` (jalur baca-kode, Fase 0 tiap permintaan): tree kotor, HEAD
detached, izin tulis, `commands.md`, dan profil yang belum ada tidak dinilai —
ketiganya tidak relevan untuk "di mana X dipanggil?". Prasyarat penuh (tanpa
flag) dijalankan Fase 3 butir 0 sebelum taskdir/branch diprovisi.
Zero external dependencies (Python Standard Library only). Satu impor intra-plugin:
`skills/_common/precondition_lib.py` (parser frontmatter, taskdir, chain, profil,
berkas plugin, keluaran), di-bootstrap relatif terhadap berkas ini.
"""

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional


# Zona artefak yang kepemilikan commit-nya ada di gerbang tech-lead
# (references/gate-scope.md bagian 3). Pada mode re-entry berkas kotor di
# bawah prefix ini menunggu commit Fase 5, jadi tidak menggagalkan check 3.
# `backenddev/docs/` tidak di sini: dokumen taskdir diabaikan git (Langkah 24)
# dan tidak pernah tampak kotor.
RE_ENTRY_ALLOWED_PREFIXES = (
    ".claude/profile/backenddev/",
    "backenddev/issues/",
    "docs/api/",
)


# Helper izin tulis dipakai bersama lintas skrip prasyarat; rumah kanoniknya
# `skills/_common/precondition_lib.py`. Bootstrap path relatif terhadap berkas
# ini, bukan terhadap cwd — skrip dipanggil dengan path absolut dari mana saja.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
from precondition_lib import (  # noqa: E402
    GitError,
    dirty_paths,
    find_repo_root,
    format_text,
    freshness_banner,
    is_under,
    legacy_suffix,
    load_profile_index,
    NOT_APPLICABLE,
    parse_commands,
    probe_writable as _probe_writable,
    profile_staleness as _profile_staleness,
    resolve_profile_dir,
    to_json,
    LEGACY_PROFILE_DIR_REL,
    PROFILE_FILES,
)
from precondition_lib import cli  # noqa: E402
import docs_git  # noqa: E402

# Selama masa transisi MIGRATE: `git mv` meninggalkan penghapusan berkas profil
# backend di lokasi lama `.claude/profile/<berkas>`. Cabut di rilis berikutnya.
RE_ENTRY_ALLOWED_PREFIXES += tuple(f"{LEGACY_PROFILE_DIR_REL}/{f}" for f in PROFILE_FILES)


class PreconditionChecker:
    def __init__(self, target_root: Optional[Path] = None, re_entry: bool = False, read_only: bool = False):
        self.root = (target_root or find_repo_root()).resolve()
        self.re_entry = re_entry
        self.read_only = read_only
        self.results: List[Dict[str, Any]] = []

    def _soft(self, check_id: int, name: str, summary: str):
        """PASS yang tidak dinilai di mode read-only; kondisinya tetap tertulis."""
        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"{summary} (tidak dinilai: mode read-only)",
            "action": "",
        })


    def run_all(self) -> bool:
        """Run checks 1 through 6."""
        self._check_1_profile()
        self._check_2_git_worktree_and_head()
        self._check_3_git_status()
        self._check_4_write_access()
        self._check_5_commands()
        self._check_6_branch_resolution()
        return all(r["status"] == "PASS" for r in self.results)

    def _check_1_profile(self):
        check_id = 1
        name = "Profile Index & Invariants"
        prof = load_profile_index(self.root)
        if not prof.ok:
            if self.read_only and prof.kind == "missing":
                return self._soft(check_id, name, "Profil absen — jawab dari sapuan manual (TERDEGRADASI), "
                                                  "tawarkan `backend:profile`")
            if self.read_only and prof.kind == "foreign":
                return self._soft(check_id, name, f"Profil backend absen ({prof.error}) — "
                                                  "jawab dari sapuan manual (TERDEGRADASI), tawarkan `backend:profile`")
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": prof.error,
                "action": prof.action,
            })
            return
        data, legacy_note, profile_dir = prof.data, prof.note, prof.dir
        module_file = profile_dir / "module-structure.md"
        invariants_file = profile_dir / "invariants.md"

        missing_docs = []
        if not module_file.exists():
            missing_docs.append("module-structure.md")
        if not invariants_file.exists():
            missing_docs.append("invariants.md")

        if missing_docs:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Dokumen profil belum lengkap: {', '.join(missing_docs)}",
                "action": "Lengkapi berkas profil di .claude/profile/backenddev/ atau jalankan profile refresh."
            })
            return

        # Kesegaran profil: non-blocking, dilaporkan sebagai degradasi.
        # Profil yang tertinggal di belakang kode melebarkan batas cakupan
        # `code-explorer` dan membuat permukaan baru tak terdaftar, tanpa
        # satu pun kegagalan tercatat.
        self.profile_freshness = _profile_staleness(
            self.root, data.get("source_root", "")
        )
        freshness_suffix = (
            f" · profil TERDEGRADASI: {self.profile_freshness[1]}"
            if self.profile_freshness[0] == "BASI" else ""
        )
        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"Profil valid (stack: {data.get('stack', 'unknown')}, base: {data.get('base_branch', 'unknown')}){freshness_suffix}" + legacy_suffix(legacy_note),
            "action": ""
        })

    def _check_2_git_worktree_and_head(self):
        check_id = 2
        name = "Git Worktree & HEAD State"
        try:
            probe = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=self.root,
                                   capture_output=True, text=True)
            if probe.returncode != 0 or probe.stdout.strip() != "true":
                # Dubious ownership menolak semua perintah git; dulu terbaca "HEAD detached" (11 H25).
                dubious = "dubious ownership" in probe.stderr
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": ("git menolak repositori ini (dubious ownership)" if dubious
                                else "Bukan repositori git yang valid"),
                    "action": (f"Tambahkan `git config --global --add safe.directory {self.root}` bila repo ini "
                               f"memang dipercaya." if dubious else
                               "Inisialisasi repositori git atau buka direktori kerja yang valid.")
                })
                return

            # `symbolic-ref -q` keluar 1 pada HEAD detached; `check_output` akan
            # melempar dan pesan "HEAD detached" tidak pernah tercapai.
            ref = subprocess.run(
                ["git", "symbolic-ref", "-q", "--short", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            branch_out = ref.stdout.strip() if ref.returncode == 0 else ""

            if not branch_out:
                if self.read_only:
                    return self._soft(check_id, name, "HEAD detached")
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "HEAD detached",
                    "action": "Checkout ke branch aktif (misal base_branch) sebelum melanjutkan."
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": f"Git repo valid (HEAD di branch '{branch_out}')",
                "action": ""
            })
        except (subprocess.CalledProcessError, OSError):     # OSError: git tak ada di PATH / --root hilang (11 H21)
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Gagal membaca status git (git tidak terpasang, --root tidak ada, atau repositori rusak)",
                "action": "Pastikan HEAD terhubung ke branch aktif dan direktori memiliki .git sah."
            })

    def _docs_outside_git(self, check_id: int, name: str) -> bool:
        """Dokumen taskdir di luar git (24 G2): False bila check 3 sudah divonis FAIL di sini.

        Berkas `backenddev/docs/` yang masih ter-track → rute MIGRASI (`docs_git.py migrate` sesudah
        persetujuan user). Selain itu penanda ignore ditulis sebelum tree dinilai, kecuali mode read-only.
        """
        tracked = docs_git.tracked_docs(self.root, docs_git.PREFIXES["backend"])
        if tracked and not self.read_only:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"MIGRASI: {len(tracked)} berkas `backenddev/docs/` masih ter-track git — dokumen taskdir "
                           "kini hanya di disk dan dicerminkan ke nataflow",
                "action": "Jalankan prosedur migrasi `references/gate-lifecycle.md` bagian 0: AskUserQuestion, lalu "
                          "`skills/_common/docs_git.py migrate --answer -`; taskdir era git yang masih terbuka ikut "
                          "disebut skrip itu."
            })
            return False
        if not self.read_only:
            _, problem = docs_git.ensure_ignored(self.root, docs_git.PREFIXES["backend"])
            if problem:
                self.results.append({"id": check_id, "name": name, "status": "FAIL", "summary": problem,
                                     "action": "Perbaiki `.gitignore` di bawah `backenddev/docs/`, lalu ulangi."})
                return False
        return True

    def _check_3_git_status(self):
        check_id = 3
        name = "Git Clean Working Tree"
        try:
            if not self._docs_outside_git(check_id, name):
                return
            # porcelain -z -uall: path apa adanya (tanpa kutip/escape oktal) dan direktori
            # untracked tidak diringkas jadi satu baris, sehingga perbandingan zona
            # artefak per segmen tidak meleset. Laci kerja `.explore/` milik
            # `code-explorer` bukan artefak rantai, jadi dibuang dirty_paths.
            dirty = dirty_paths(self.root)

            if dirty and self.read_only:
                return self._soft(check_id, name, f"{len(dirty)} berkas uncommitted")

            if dirty:
                if self.re_entry:
                    outside = [p for p in dirty if not any(is_under(p, x) for x in RE_ENTRY_ALLOWED_PREFIXES)]

                    if outside:
                        sample = ", ".join(outside[:3])
                        if len(outside) > 3:
                            sample += f", +{len(outside) - 3} lainnya"
                        self.results.append({
                            "id": check_id,
                            "name": name,
                            "status": "FAIL",
                            "summary": f"Mode re-entry: {len(outside)} berkas kotor di luar zona artefak ({sample})",
                            "action": "Minta user stash atau commit berkas di luar zona artefak sebelum melanjutkan re-entry."
                        })
                        return

                    self.results.append({
                        "id": check_id,
                        "name": name,
                        "status": "PASS",
                        "summary": f"Mode re-entry: {len(dirty)} berkas artefak menunggu commit gerbang, nol berkas di luar zona artefak",
                        "action": ""
                    })
                    return

                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": f"Working tree kotor ({len(dirty)} berkas uncommitted)",
                    "action": "Minta user stash atau commit perubahan sebelum membuat taskdir/branch."
                })
                return

            self.results.append({
                "id": check_id,
                "name": name,
                "status": "PASS",
                "summary": "Working tree bersih (0 perubahan uncommitted)",
                "action": ""
            })
        except GitError as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal menjalankan git status: {e}",
                "action": "Periksa akses dan integritas git."
            })

    def _check_4_write_access(self):
        check_id = 4
        name = "Workspace Write Access"
        if self.read_only:
            return self._soft(check_id, name, "Izin tulis zona artefak")
        test_dirs = [self.root / "backenddev" / "docs", self.root / "backenddev" / "issues"]
        unwritable = []

        # Gerbang berjalan juga pada lane EXPLORE_FACT dan PROFILE yang dilarang
        # mengalokasikan direktori apa pun (SKILL.md Fase 3). Karena itu check ini
        # hanya memeriksa izin tulis induk terdekat, tidak membuat backenddev/.
        for d in test_dirs:
            ok, _ = _probe_writable(d)
            if not ok:
                unwritable.append(str(d.relative_to(self.root) if d.is_relative_to(self.root) else d))

        if unwritable:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Zona artefak tidak dapat ditulis: {', '.join(unwritable)}",
                "action": "Periksa hak akses tulis pada induk direktori backenddev/."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": "Zona artefak backenddev/docs/ dan backenddev/issues/ dapat ditulis",
            "action": ""
        })

    def _check_5_commands(self):
        check_id = 5
        name = "Profile Commands"
        if self.read_only:
            return self._soft(check_id, name, "Perintah build/test commands.md")
        commands_file = resolve_profile_dir(self.root)[0] / "commands.md"
        if not commands_file.exists():
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": "Berkas .claude/profile/backenddev/commands.md tidak ditemukan",
                "action": "Jalankan `backend:profile` untuk mencatat perintah build dan test."
            })
            return

        try:
            cmds = parse_commands(commands_file.read_text(encoding="utf-8"))
        except Exception as e:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"Gagal membaca commands.md: {e}",
                "action": "Periksa permissions berkas .claude/profile/backenddev/commands.md."
            })
            return

        # `build: tidak berlaku` sah (stack yang dijalankan langsung dari sumber); `test: tidak berlaku`
        # tidak: verifikasi penutup architect Fase 4 tidak punya alat ukur tanpanya.
        problems = []
        if "build" not in cmds:
            problems.append("baris `build:` tidak ada")
        test = cmds.get("test")
        if test is None:
            problems.append("baris `test:` tidak ada")
        elif NOT_APPLICABLE.match(test):
            problems.append("`test: tidak berlaku` — verifikasi penutup architect tidak punya alat ukur")
        if problems:
            self.results.append({
                "id": check_id,
                "name": name,
                "status": "FAIL",
                "summary": f"commands.md tidak memenuhi kontrak: {'; '.join(problems)}",
                "action": "Jalankan `backend:profile` (mode refresh) agar baris `build:`/`test:` tertulis dari eksekusi nyata."
            })
            return

        self.results.append({
            "id": check_id,
            "name": name,
            "status": "PASS",
            "summary": f"build: {cmds['build']} · test: {test}",
            "action": ""
        })

    def _check_6_branch_resolution(self):
        """Bahan Fase 3 (isolasi branch): `base_branch` resolve dan `branch_convention` berslot `<slug>`.

        Integritas berkas plugin (dispatcher/agent) bukan keadaan repo user; lint plugin
        (`scripts/lint_plugins.py`) yang menjaganya.
        """
        check_id = 6
        name = "Base Branch & Branch Convention"
        if self.read_only:
            return self._soft(check_id, name, "base_branch dan branch_convention profil")
        prof = load_profile_index(self.root, required=())
        data = prof.data or {}
        base = str(data.get("base_branch") or "").strip()
        conv = str(data.get("branch_convention") or "").strip()
        problems = []
        if base in ("", "tidak terdeteksi"):
            problems.append("base_branch kosong/tidak terdeteksi")
        elif subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"],
                            cwd=self.root, capture_output=True).returncode != 0:
            problems.append(f"base_branch '{base}' tidak resolve ke commit")
        if "<slug>" not in conv:
            problems.append(f"branch_convention '{conv or '(kosong)'}' tanpa placeholder <slug>")
        if problems:
            self.results.append({
                "id": check_id, "name": name, "status": "FAIL",
                "summary": "; ".join(problems),
                "action": "Perbaiki index.json lewat `backend:profile`; gerbang tidak menebak branch acuan (`## Failure path` butir 1)."
            })
            return
        self.results.append({
            "id": check_id, "name": name, "status": "PASS",
            "summary": f"base '{base}' resolve · pola branch '{conv}'", "action": ""
        })

    def _mode_label(self) -> str:
        return (" · mode: re-entry" if self.re_entry else "") + (" · mode: read-only" if self.read_only else "")

    def format_text(self) -> str:
        return format_text("tech-lead", self.results, header_suffix=self._mode_label(),
                           banner=freshness_banner(getattr(self, "profile_freshness", None)))

    def to_json(self) -> str:
        return to_json(self.root, self.results, re_entry=self.re_entry, read_only=self.read_only,
                       profile_freshness=getattr(self, "profile_freshness", ("TAK_TERNILAI", "belum dinilai"))[0])


def main():
    parser = argparse.ArgumentParser(description="Tech-Lead Preconditions Checker")
    parser.add_argument("--root", type=str, default=None, help="Root path of target repository")
    parser.add_argument(
        "--re-entry",
        action="store_true",
        help="Re-entry mode: berkas kotor di zona artefak gerbang tidak menggagalkan check 3"
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Jalur baca-kode: tree kotor, detached HEAD, izin tulis, commands.md, dan profil absen tidak dinilai"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    target_root = Path(args.root) if args.root else None
    checker = PreconditionChecker(target_root=target_root, re_entry=args.re_entry, read_only=args.read_only)
    passed = checker.run_all()

    if args.json:
        print(checker.to_json())
    else:
        print(checker.format_text())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    sys.exit(cli(main))
