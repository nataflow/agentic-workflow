#!/usr/bin/env python3
"""Ledger `## Chain` dan `## Riwayat Rantai` `TASK.md` — satu-satunya penulis akar, draft, approval, re-entry,
dan eskalasi.

Dokumen taskdir diabaikan git dan dicerminkan ke nataflow (Langkah 24): skrip ini tidak pernah men-stage atau
meng-commit. Jejak yang dulu hidup di subjek dan badan commit dokumen kini ditulis sebagai kejadian bernomor di
seksi `## Riwayat Rantai` (ujung `TASK.md`). Transisi status dokumen planning, pencentangan ledger, dan kejadian
Riwayat **tidak** ditulis model dengan tangan. Model mengumpulkan jawaban eksplisit user lewat `AskUserQuestion`,
lalu memanggil subperintah di bawah; skrip memeriksa prasyaratnya dan menulis frontmatter, ledger, dan Riwayat.

Subperintah:

- `init`       — tulis `## Chain` dari `sections` frontmatter `TASK.md` (dipakai `task` sebelum self-test akar).
- `root`       — kunci akar: `validate_task.py` `PASS`, `base_commit` = `HEAD`, dan kejadian `akar` (lane, sections,
                 sidik akar). Pengganti commit `kunci TASK sebagai akar rantai`.
- `amend`      — amandemen akar sesudah `validate_task.py --amend` `PASS`: kejadian `amandemen` bersidik akar baru.
- `draft`      — catat draft atau revisi hop sesudah validator gate-nya `PASS` (CONTRACT, dan BRIEF lane non-MINOR
                 ber-brief `READY`: ronde reviewer terakhir juga `PASS` atas konten itu). Plafon 2 revisi.
- `status`     — cetak ledger beserta vonis keutuhan tiap baris.
- `verify`     — `FAIL` bila baris yang diminta (default: semua) belum `[x]` sah dan utuh.
- `approve`    — `FLOW`/`UI`/`CONTRACT`: `DRAFT` → `APPROVED` + centang + kejadian `approve`.
                 `BRIEF`: centang batch brief `READY` + `REVIEW-PLAN.md` `PASS`, `sidik_kontrak` tiap brief `READY`.
- `reopen`     — buka ulang hop tercentang (`[~]`) beserta **seluruh hop tercentang di bawahnya**
                 (kaskade: yang disetujui atas hulu lama tidak lagi sah); dokumen hop turun ke
                 `DRAFT`. Plafon 3 per hop dan 6 per taskdir.
- `abandon`    — tutup taskdir yang tidak dilanjutkan (`status: ABANDONED`) atas keputusan user.
- `files`      — cetak berkas rantai (commit kode berscope `(<slug>)` sejak `base_commit`) — rentang review penutup.
- `escalate`   — geser `lane`/`sections` ke atas dan tambah baris ledger. Plafon 2/taskdir.
- `revisions`  — hitung revisi berturut sebuah hop; exit 1 bila plafon 2 sudah habis.

Ledger mencentang **sidik** konten yang disetujui (`@ APPROVED <sidik12>`), bukan sha commit. Kejadian `approve`
memateraikan `sidik` (sha1 isi tanpa baris `status:`), `review` (ronde reviewer hop yang direview), `sc` (sidik
butir `SC-{n}`), dan jawaban user (12 J44/J46, 24 K8). Isi dokumen sekarang wajib identik dengan sidik itu, kecuali
baris `status:`; suntingan sesudah approval tanpa `reopen` tertangkap sebagai drift.

Batas yang dinyatakan apa adanya: skrip tidak dapat membuktikan `AskUserQuestion` benar-benar terjadi, dan tidak
dapat membuktikan Riwayat itu sendiri tidak ditulis ulang — model di runtime yang sama dapat menulisnya. Yang
dijamin adalah jejak: suntingan dokumen yang tidak lewat skrip terdeteksi sebagai drift, approval tanpa jawaban
ditolak, dan jawaban/alasan bernewline (yang dapat menyisipkan kejadian palsu) ditolak.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs_git  # noqa: E402
from verify_scope import SIDIK_FIELD, contract_sidik  # noqa: E402
from precondition_lib import (  # noqa: E402
    TASKDIR_PATTERN,
    BRIEF_GLOB,
    CHAIN_BY_ROW,
    DOC_ROWS,
    FrontmatterError,
    ROOTED_LANES,
    MINOR_LANE,
    append_history,
    approval_targets,
    berkas_value,
    chain_files,
    chain_line,
    content_snapshot,
    drafts_since_open,
    expected_rows,
    find_repo_root,
    history_line,
    lane_sections_problem,
    lane_tamper,
    last_draft,
    last_root_seal,
    locked_brief_problems,
    normalize_taskdir,
    parse_sections,
    read_chain,
    read_history,
    read_status,
    replace_chain_row,
    revisions_since_open,
    root_sidik,
    sc_sidik,
    sections_value,
    set_frontmatter_field,
    task_lane_sections,
    taskdir_slug,
    verify_chain_row,
    write_keep_newline,
)
from precondition_lib import cli  # noqa: E402
from review_round import Rounds  # noqa: E402

PLUGIN_SKILLS = Path(__file__).resolve().parents[1]
MAX_REOPEN_ROW = 3
MAX_REOPEN = 6
MAX_ESCALATE = 2
MAX_REVISIONS = 2
LANE_RANK = {"HOTFIX_MINOR": 0, "FAST_FORWARD": 1, "REFACTOR_ARCH": 1, "FULL_PIPELINE": 2}
# Rute plafon habis (12 J43, padanan 11 H28): tidak ada jalan pintas yang me-reset plafon.
CAP_ROUTE = ("hentikan gate; `frontend:lead` bertanya lewat `AskUserQuestion`: rumuskan ulang di taskdir baru "
             "(`chain.py abandon` taskdir ini) atau hentikan")
RIWAYAT_BROKEN = ("laporkan ke user lewat `frontend:lead`; Riwayat hanya ditulis `chain.py`, dilarang menambalnya "
                  "dengan tangan")


class ChainError(Exception):
    """Prasyarat subperintah tidak terpenuhi; pesannya adalah tindakan remediasi."""


def one_line(value: str, flag: str) -> str:
    """Teks bebas yang masuk kejadian Riwayat wajib satu baris (12 J46).

    Baris baru di `--answer`/`--reason` dapat menyisipkan kejadian palsu ke `## Riwayat Rantai`.
    """
    if "\n" in value or "\r" in value:
        raise ChainError(f"`{flag}` memuat baris baru — tulis satu baris; jawaban/alasan bernewline dapat "
                         "menyisipkan kejadian palsu ke `## Riwayat Rantai`.")
    return value.strip()


def run_script(*args: str) -> Tuple[bool, str]:
    proc = subprocess.run([sys.executable, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          universal_newlines=True)
    return proc.returncode == 0, proc.stdout


class Chain:
    def __init__(self, taskdir: str, root: Optional[Path] = None):
        self.root = (root or find_repo_root()).resolve()
        self.taskdir_rel = normalize_taskdir(taskdir)
        if not TASKDIR_PATTERN.match(self.taskdir_rel):
            raise ChainError(f"`{self.taskdir_rel}` tidak berpola frontenddev/docs/<YYMMDDhhmm>-<slug>")
        self.taskdir = self.root / self.taskdir_rel
        self.task_rel = f"{self.taskdir_rel}/TASK.md"
        self.task = self.root / self.task_rel
        self.slug = taskdir_slug(self.taskdir_rel)
        if not self.task.is_file():
            raise ChainError(f"`{self.task_rel}` tidak ada — tulis akar lewat `frontend:task`.")
        self.lane, self.sections = task_lane_sections(self.task)

    # ------------------------------------------------------------ helpers

    def text(self) -> str:
        return self.task.read_text(encoding="utf-8")

    def entries(self) -> List[Dict]:
        return read_chain(self.text())

    def entry(self, row: str) -> Dict:
        for e in self.entries():
            if e["row"] == row:
                return e
        raise ChainError(f"baris `{row}` tidak ada di ledger — hop ini tidak dijadwalkan "
                         f"sections `{','.join(self.sections) or '-'}`.")

    def history(self, text: Optional[str] = None) -> List[Dict]:
        events, problem = read_history(self.text() if text is None else text)
        if problem:
            raise ChainError(f"`## Riwayat Rantai` rusak: {problem} — {RIWAYAT_BROKEN}.")
        return events

    def record(self, text: str, kind: str, rows: List[str], fields: List[Tuple[str, str]],
               free: Optional[Tuple[str, str]] = None) -> Tuple[str, int]:
        """`text` ditambah satu kejadian Riwayat bernomor berikutnya.

        Teks bebas kosong ditolak di sini untuk semua kejadian: baris `· alasan: ` tanpa isi tidak terbaca
        `read_history`, dan taskdir jatuh `RUSAK` dengan `abandon` sebagai satu-satunya jalan keluar (25 R3).
        """
        if free is not None and not free[1].strip():
            raise ChainError(f"`{free[0]}` kosong — kejadian Riwayat menuntut teks bebas berisi.")
        n = len(self.history(text)) + 1
        return append_history(text, history_line(n, kind, rows, fields, free)), n

    def require_rooted(self, intact: bool = True) -> List[Dict]:
        """Akar terkunci (`chain.py root`): kejadian pertama `akar`. Mengembalikan kejadian Riwayat.

        `intact`: sidik akar wajib sama dengan kejadian akar/eskalasi/amandemen terakhir (12 J47, 24) — suntingan
        akar yang menggantung diselesaikan lewat amandemen lebih dulu, tidak dibawa diam-diam ke kejadian lain.
        """
        events = self.history()
        if not events or events[0]["kind"] != "akar":
            raise ChainError("akar belum terkunci — jalankan `chain.py root` (`frontend:task` Phase 4) lebih dulu.")
        if intact and root_sidik(self.text())[:12] != last_root_seal(events):
            raise ChainError(f"`{self.task_rel}` disunting di luar `chain.py amend`/`escalate` — selesaikan dulu "
                             "lewat `frontend:lead`: amandemen akar (`validate_task.py --amend` lalu `chain.py "
                             "amend`) atau kembalikan suntingannya. Tidak ada berkas yang diubah.")
        return events

    def require_ledger_shape(self) -> None:
        present = [e["row"] for e in self.entries()]
        expected = expected_rows(self.sections)
        if present != expected:
            raise ChainError(f"ledger {present} ≠ jadwal sections {expected}; ledger rusak — "
                             "tulis ulang lewat `chain.py init` hanya bila akar belum dikunci.")

    def require_above(self, row: str) -> None:
        for e in self.entries():
            if e["row"] == row:
                return
            problem = verify_chain_row(self.root, self.taskdir_rel, e)
            if problem:
                raise ChainError(f"hop hulu belum sah: {problem}.")

    def require_active(self) -> None:
        """`approve`/`reopen`/`escalate`/`draft`/`amend` hanya atas akar `ACTIVE` (12 J51)."""
        status = read_status(self.task)
        if status != "ACTIVE":
            raise ChainError(f"`{self.task_rel}` berstatus `{status or '(kosong)'}`, bukan `ACTIVE` — "
                             + ("taskdir sudah ditutup (`chain.py abandon`); permintaan lanjutan dibuka di "
                                "taskdir baru." if status == "ABANDONED" else
                                "akar rusak; laporkan ke user lewat `frontend:lead` (dilarang menambal akar "
                                "dengan tangan)."))

    def snapshot(self, *rels: str) -> Dict[str, bytes]:
        """Isi byte persis — pemulihan sesudah tulis gagal tidak boleh mengubah line ending."""
        return {r: (self.root / r).read_bytes() for r in rels if (self.root / r).is_file()}

    def write_all(self, writes: Dict[str, str]) -> None:
        """Tulis seluruh berkas; gagal di tengah → pulihkan isi semula semuanya."""
        originals = self.snapshot(*writes)
        try:
            for rel, text in writes.items():
                write_keep_newline(self.root / rel, text)
        except OSError as exc:
            stuck = []
            for rel, old in originals.items():
                try:
                    if (self.root / rel).read_bytes() != old:
                        (self.root / rel).write_bytes(old)
                except OSError:
                    stuck.append(rel)
            if stuck:
                raise ChainError(f"gagal menulis ({exc}); {', '.join(stuck)} tidak dapat dipulihkan — laporkan ke "
                                 "user, lalu ulangi.")
            raise ChainError(f"gagal menulis ({exc}) — berkas dipulihkan ke keadaan semula.")

    def briefs(self) -> List[Path]:
        return sorted(self.taskdir.glob(BRIEF_GLOB))

    def brief_rels(self) -> List[str]:
        return [f"{self.taskdir_rel}/{b.name}" for b in self.briefs()]

    def validate_doc(self, row: str) -> None:
        kind = {"FLOW": "flow", "UI": "ui", "CONTRACT": "contract"}[row]
        ok, out = run_script(str(PLUGIN_SKILLS / "_common" / "validate_doc.py"), "--kind", kind,
                             "--taskdir", self.taskdir_rel, "--root", str(self.root))
        if not ok:
            raise ChainError(f"`validate_doc.py --kind {kind}` FAIL — perbaiki draft dulu:\n{out}")

    def validate_briefs(self) -> None:
        args = [str(PLUGIN_SKILLS / "plan" / "scripts" / "validate_briefs.py"), "--taskdir", self.taskdir_rel,
                "--root", str(self.root)] + (["--contract"] if self.sections else [])
        ok, out = run_script(*args)
        if not ok:
            raise ChainError(f"`validate_briefs.py` FAIL — perbaiki brief dulu:\n{out}")

    def doc_rel(self, row: str) -> str:
        return f"{self.taskdir_rel}/{CHAIN_BY_ROW[row][2]}"

    # ------------------------------------------------------------ init / root / amend / status / verify

    def init(self) -> str:
        problem = lane_sections_problem(self.lane, self.sections)
        if problem:
            raise ChainError(f"frontmatter `TASK.md` tidak sah: {problem}.")
        text = self.text()
        if self.history(text):
            raise ChainError("akar sudah terkunci (`## Riwayat Rantai` berisi); ledger hanya diubah "
                             "`approve`/`reopen`/`escalate`.")
        if any(e["mark"] != " " for e in read_chain(text)):
            raise ChainError("ledger sudah punya centang; `init` hanya untuk akar yang baru ditulis.")
        block = "## Chain\n\n" + "\n".join(chain_line(r) for r in expected_rows(self.sections)) + "\n"
        if re.search(r"^## Chain\s*$", text, flags=re.MULTILINE):
            text = re.sub(r"^## Chain\s*\n(?:.*\n?)*?(?=^## |\Z)", block, text,
                          count=1, flags=re.MULTILINE)
        else:
            text = text.rstrip("\n") + "\n\n" + block
        write_keep_newline(self.task, text)
        return (f"CHAIN INIT: {', '.join(expected_rows(self.sections))} ditulis ke {self.task_rel} "
                "(akar belum terkunci — `chain.py root` sesudah self-test)")

    def lock_root(self) -> str:
        """Kunci akar (24 K6): `base_commit` = `HEAD` dan kejadian `akar` — pengganti commit akar."""
        self.require_active()
        problem = lane_sections_problem(self.lane, self.sections)
        if problem:
            raise ChainError(f"frontmatter `TASK.md` tidak sah: {problem}.")
        if self.history():
            raise ChainError("akar sudah terkunci (`## Riwayat Rantai` berisi); suntingan akar hanya lewat "
                             "`chain.py amend`.")
        prefix = docs_git.PREFIXES["frontend"]
        tracked = docs_git.tracked_docs(self.root, prefix)
        if tracked:
            raise ChainError(f"MIGRASI: {len(tracked)} berkas `{prefix}/docs/` masih ter-track git — jalankan "
                             "prosedur migrasi `frontend:lead` (`docs_git.py migrate`) lebih dulu.")
        _, problem = docs_git.ensure_ignored(self.root, prefix)
        if problem:
            raise ChainError(f"{problem} — perbaiki `.gitignore` di bawah `{prefix}/docs/`, lalu ulangi.")
        head = docs_git.head_sha(self.root)
        if not head:
            raise ChainError("repo belum punya commit — akar dikunci atas `HEAD`; commit awal repo lebih dulu.")
        ok, out = run_script(str(PLUGIN_SKILLS / "task" / "scripts" / "validate_task.py"),
                             "--taskdir", self.taskdir_rel, "--root", str(self.root))
        if not ok:
            raise ChainError(f"`validate_task.py` FAIL — akar belum sah, perbaiki dulu:\n{out}")
        text = set_frontmatter_field(self.text(), "base_commit", head)
        text, n = self.record(text, "akar", [], [("base", head[:7]), ("lane", self.lane),
                                                  ("sections", sections_value(self.sections)),
                                                  ("akar", root_sidik(text)[:12])])
        self.write_all({self.task_rel: text})
        return f"CHAIN ROOT: {self.task_rel} terkunci @ base {head[:7]} (Riwayat #{n})"

    def amend(self, reason: str) -> str:
        """Amandemen akar: `validate_task.py --amend` `PASS`, lalu sidik akar baru dicatat."""
        if not reason.strip():
            raise ChainError("`--reason` kosong — sebut keputusan user yang mengamandemen akar.")
        reason = one_line(reason, "--reason")
        self.require_active()
        events = self.require_rooted(intact=False)
        problem = lane_tamper(self.root, self.taskdir_rel)
        if problem:
            raise ChainError(f"{problem} — pergeseran lane/sections hanya lewat `chain.py escalate`.")
        ok, out = run_script(str(PLUGIN_SKILLS / "task" / "scripts" / "validate_task.py"), "--amend",
                             "--taskdir", self.taskdir_rel, "--root", str(self.root))
        if not ok:
            raise ChainError(f"`validate_task.py --amend` FAIL — amandemen belum sah:\n{out}")
        text = self.text()
        sidik = root_sidik(text)[:12]
        if sidik == last_root_seal(events):
            raise ChainError("akar tidak berubah sejak kejadian akar terakhir — tidak ada amandemen untuk dicatat.")
        text, n = self.record(text, "amandemen", [], [("akar", sidik)], ("alasan", reason))
        self.write_all({self.task_rel: text})
        return f"CHAIN AMEND: akar {self.task_rel} @ {sidik} (Riwayat #{n})"

    def status_lines(self, rows: Optional[List[str]] = None) -> List[str]:
        out = []
        for e in self.entries():
            if rows and e["row"] not in rows:
                continue
            problem = verify_chain_row(self.root, self.taskdir_rel, e)
            out.append(f"{e['raw'].strip()}  ::  {'SAH' if not problem else problem}")
        return out

    def verify(self, rows: Optional[List[str]]) -> List[str]:
        self.require_ledger_shape()
        unknown = [r for r in (rows or []) if r not in [e["row"] for e in self.entries()]]
        if unknown:
            raise ChainError(f"baris {unknown} tidak ada di ledger {[e['row'] for e in self.entries()]}.")
        problems = []
        for e in self.entries():
            if rows and e["row"] not in rows:
                continue
            problem = verify_chain_row(self.root, self.taskdir_rel, e)
            if problem:
                problems.append(problem)
        return problems

    # ------------------------------------------------------------ draft

    def draft(self, row: str) -> str:
        """Catat draft/revisi hop (pengganti commit `draft`/`revise` dan `review_round.py commit`)."""
        self.require_active()
        events = self.require_rooted()
        self.require_ledger_shape()
        entry = self.entry(row)
        if entry["mark"] == "x":
            raise ChainError(f"hop `{row}` sudah tercentang @ {entry['sha']}; revisi hanya lewat `reopen`.")
        self.require_above(row)
        review = ""
        if row in DOC_ROWS:
            rel = self.doc_rel(row)
            if not (self.root / rel).is_file():
                raise ChainError(f"`{rel}` tidak ada — tulis draft-nya lebih dulu.")
            status = read_status(self.root / rel)
            if status != "DRAFT":
                raise ChainError(f"`{rel}` berstatus `{status or '(kosong)'}`; hanya `DRAFT` yang dicatat sebagai draft.")
            self.validate_doc(row)
            if row == "CONTRACT":
                review = self._require_review_pass("contract")
            sidik = content_snapshot(self.root, [rel])
        else:
            briefs = self.briefs()
            if not any(read_status(b) == "READY" for b in briefs):
                raise ChainError("nol brief `READY` — tidak ada breakdown baru untuk dicatat.")
            bad = [f"{b.name} ({read_status(b) or 'kosong'})" for b in briefs
                   if read_status(b) not in ("READY", "DONE", "BLOCKED")]
            if bad:
                raise ChainError("status brief di luar READY/DONE/BLOCKED: " + ", ".join(bad))
            self.validate_briefs()
            if self.lane != MINOR_LANE:
                review = self._require_review_pass("plan")
            sidik = content_snapshot(self.root, self.brief_rels())
        prev = last_draft(events, row)
        if prev and prev["fields"].get("sidik") == sidik[:12]:
            raise ChainError(f"konten ini sudah tercatat sebagai draft (Riwayat #{prev['n']}) — tidak ada perubahan "
                             "untuk dicatat.")
        revisions = drafts_since_open(events, row)        # draft ini menjadi revisi ke-n putaran berjalan
        if revisions > MAX_REVISIONS:
            raise ChainError(f"plafon revisi hop `{row}` ({MAX_REVISIONS}) habis — {CAP_ROUTE} (`frontend:lead` "
                             "Phase 8).")
        text, n = self.record(self.text(), "draft", [row], [("sidik", sidik[:12])]
                              + ([("review", review)] if review else []))
        self.write_all({self.task_rel: text})
        label = f"revisi {revisions}/{MAX_REVISIONS}" if revisions else "draft pertama putaran ini"
        return f"CHAIN DRAFT: {row} @ {sidik[:12]} — {label} (Riwayat #{n})"

    # ------------------------------------------------------------ approve

    def approve(self, row: str, answer: str) -> str:
        if not answer.strip():
            raise ChainError("`--answer` kosong — approval wajib memateraikan jawaban eksplisit "
                             "user dari `AskUserQuestion`. Diam atau jawaban ambigu bukan persetujuan.")
        answer = one_line(answer, "--answer")
        self.require_active()
        events = self.require_rooted()
        self.require_ledger_shape()
        entry = self.entry(row)
        if entry["mark"] == "x":
            raise ChainError(f"hop `{row}` sudah tercentang @ {entry['sha']}; revisi hanya lewat `reopen`.")
        self.require_above(row)
        if row in DOC_ROWS:
            return self._approve_doc(row, entry, answer, events)
        return self._approve_brief(entry, answer, events)

    @staticmethod
    def _tail(state: str, sidik: str, entry: Dict) -> str:
        return f"{state} {sidik[:12]}" + (f" (re-entry {entry['n']}, was {entry['sha']})" if entry["mark"] == "~" else "")

    def _require_presented(self, events: List[Dict], row: str, sidik: str) -> None:
        """Konten yang disetujui wajib konten yang tercatat diajukan (pengganti `require_clean`)."""
        draft = last_draft(events, row)
        if not draft or draft["fields"].get("sidik") != sidik[:12]:
            raise ChainError(f"konten hop `{row}` di disk belum tercatat sebagai draft yang diajukan "
                             f"(`chain.py draft --row {row}`"
                             + (f"; draft terakhir #{draft['n']} @ {draft['fields'].get('sidik')}" if draft else "")
                             + ") — yang disetujui wajib persis konten yang diajukan ke user.")

    def _approve_doc(self, row: str, entry: Dict, answer: str, events: List[Dict]) -> str:
        rel = self.doc_rel(row)
        path = self.root / rel
        if not path.is_file():
            raise ChainError(f"`{rel}` tidak ada — tulis dan catat draft-nya lebih dulu.")
        status = read_status(path)
        if status != "DRAFT":
            raise ChainError(f"`{CHAIN_BY_ROW[row][2]}` berstatus `{status or '(kosong)'}`; hanya `DRAFT` yang dapat "
                             "disetujui.")
        self.validate_doc(row)
        review = self._require_review_pass("contract") if row == "CONTRACT" else ""
        sidik = content_snapshot(self.root, [rel])
        self._require_presented(events, row, sidik)
        doc_text = set_frontmatter_field(path.read_text(encoding="utf-8"), "status", "APPROVED")
        text = replace_chain_row(self.text(), row, chain_line(row, "x", self._tail("APPROVED", sidik, entry)))
        text, n = self.record(text, "approve", [row], [("sidik", sidik)] + ([("review", review)] if review else [])
                              + [("sc", sc_sidik(text))], ("persetujuan", answer))
        self.write_all({rel: doc_text, self.task_rel: text})
        return f"CHAIN APPROVE: {row} @ APPROVED {sidik[:12]} (Riwayat #{n})"

    def _approve_brief(self, entry: Dict, answer: str, events: List[Dict]) -> str:
        briefs = self.briefs()
        if not briefs:
            raise ChainError("nol `brief-*.md` di taskdir — jalankan `frontend:plan` lebih dulu.")
        bad = [f"{b.name} ({read_status(b) or 'kosong'})" for b in briefs
               if read_status(b) not in ("READY", "DONE", "BLOCKED")]
        if bad:
            raise ChainError("status brief di luar READY/DONE/BLOCKED: " + ", ".join(bad))
        ready = [b for b in briefs if read_status(b) == "READY"]
        if not ready and entry["mark"] != "~":
            raise ChainError("nol brief `READY` — tidak ada breakdown baru untuk disetujui.")
        if entry["mark"] == "~":
            locked = locked_brief_problems(self.root, self.taskdir_rel)
            if locked:
                raise ChainError("brief terkunci saat hop BRIEF dibuka ulang berubah: " + ", ".join(locked)
                                 + " — brief `DONE`/`BLOCKED` tidak pernah disunting atau dinaikkan lagi; "
                                   "pulihkan isinya dan tulis brief remedi (`remedies: \"NN\"`) untuk sisa "
                                   "pekerjaan unit `BLOCKED`.")
        self.validate_briefs()
        review = ""
        if self.lane != MINOR_LANE and ready:
            plan_review = self.taskdir / "REVIEW-PLAN.md"
            if not plan_review.is_file():
                raise ChainError("`REVIEW-PLAN.md` tidak ada — Gate Plan Review belum jalan.")
            verdict = read_status(plan_review, "verdict")
            if verdict != "PASS":
                raise ChainError(f"`REVIEW-PLAN.md` ber-verdict `{verdict or '(kosong)'}`, bukan `PASS`.")
            review = self._require_review_pass("plan")
        brief_sidik = content_snapshot(self.root, self.brief_rels())
        if ready:
            self._require_presented(events, "BRIEF", brief_sidik)
        # 24 K10: kontrak tiap brief READY dikunci di frontmatternya sendiri (`verify_scope.py`). Baris
        # `sidik_kontrak:` di luar sidik konten, jadi sidik ronde dan draft tidak bergeser.
        writes = {}
        for b in ready:
            text = b.read_text(encoding="utf-8")
            writes[f"{self.taskdir_rel}/{b.name}"] = set_frontmatter_field(text, SIDIK_FIELD, contract_sidik(text))
        self.write_all(writes)
        targets = approval_targets(self.root, self.taskdir_rel, "BRIEF")
        sidik = content_snapshot(self.root, targets)
        names = [Path(t).name for t in targets]
        text = replace_chain_row(self.text(), "BRIEF", chain_line("BRIEF", "x", self._tail("READY", sidik, entry)))
        text, n = self.record(text, "approve", ["BRIEF"],
                              [("sidik", sidik), ("brief", brief_sidik[:12]),
                               ("berkas", berkas_value(self.root, self.taskdir_rel, names))]
                              + ([("review", review)] if review else []) + [("sc", sc_sidik(text))],
                              ("persetujuan", answer))
        self.write_all({self.task_rel: text})
        return f"CHAIN APPROVE: BRIEF @ READY {sidik[:12]} — {len(ready)} brief READY (Riwayat #{n})"

    def _require_review_pass(self, gate: str) -> str:
        """Ronde reviewer terakhir wajib `PASS` atas konten yang persis sama dan epoch reopen sekarang.

        Mengembalikan nilai field `review` kejadian (12 J46): `<gate> r<n> t<total> PASS <sidik12>`.
        """
        try:
            rounds = Rounds(self.taskdir_rel, gate, self.root)
            state = rounds.load()
            problem = rounds.ready(state)
        except SystemExit as exc:          # state ronde rusak/hilang: fail-closed, pesan apa adanya
            raise ChainError(str(exc))
        if problem:
            raise ChainError(problem + ".")
        last = state["rounds"][-1]
        return f"{gate} r{last['round']} t{len(state['rounds'])} PASS {last['snapshot'][:12]}"

    # ------------------------------------------------------------ reopen / escalate / revisions

    def reopen(self, row: str, reason: str) -> str:
        if not reason.strip():
            raise ChainError("`--reason` kosong — sebut pemicu re-entry (mis. berkas yatim, BLOCKED berulang).")
        reason = one_line(reason, "--reason")
        self.require_active()
        events = self.require_rooted()
        self.require_ledger_shape()
        entry = self.entry(row)
        if entry["mark"] != "x":
            raise ChainError(f"hop `{row}` tidak tercentang; tidak ada yang dibuka ulang.")
        reopens = [e for e in events if e["kind"] == "reopen"]
        if len(reopens) >= MAX_REOPEN:
            raise ChainError(f"plafon re-entry taskdir ({MAX_REOPEN}) habis — cacatnya satu lapis di atas "
                             f"hop ini; {CAP_ROUTE}.")
        # kuota per hop: hanya reopen yang menargetkan hop ini; kaskade tidak memakan kuota hop di bawahnya —
        # plafon taskdir tetap membatasi total
        n = sum(1 for e in reopens if e["fields"].get("target") == row) + 1
        if n > MAX_REOPEN_ROW:
            raise ChainError(f"plafon re-entry hop `{row}` ({MAX_REOPEN_ROW}) habis — {CAP_ROUTE}.")
        entries = self.entries()
        idx = [e["row"] for e in entries].index(row)
        cascade = [e for e in entries[idx:] if e["mark"] == "x"]
        writes: Dict[str, str] = {}
        for e in cascade:                             # 1) validasi seluruh kaskade — belum ada yang ditulis
            if e["row"] not in DOC_ROWS:
                continue
            rel = self.doc_rel(e["row"])
            if not (self.root / rel).is_file():
                raise ChainError(f"`{rel}` hilang dari disk padahal hop-nya tercentang @ {e['sha']} — pulihkan "
                                 "berkasnya (cermin nataflow, atau salinan user), lalu ulangi reopen. Tidak ada "
                                 "berkas yang diubah.")
            try:
                writes[rel] = set_frontmatter_field((self.root / rel).read_text(encoding="utf-8"), "status", "DRAFT")
            except FrontmatterError as exc:
                raise ChainError(f"`{rel}`: {exc} — pulihkan frontmatter-nya, lalu ulangi reopen. Tidak ada berkas "
                                 "yang diubah.")
        text = self.text()
        for e in cascade:
            r = e["row"]
            # label informasional: target = hitungan target, kaskade = total pembukaan hop itu
            k = n if r == row else sum(1 for x in reopens if r in x["rows"]) + 1
            text = replace_chain_row(text, r, chain_line(r, "~", f"re-entry {k} (was {e['sha']})"))
        rows = [e["row"] for e in cascade]
        # 12 J48: keadaan brief saat hop dibuka dicatat — brief DONE/BLOCKED tidak boleh berubah sesudahnya
        names = [b.name for b in self.briefs()]
        text, num = self.record(text, "reopen", rows, [("target", row)]
                                + ([("berkas", berkas_value(self.root, self.taskdir_rel, names))] if names else []),
                                ("alasan", reason))
        writes[self.task_rel] = text
        self.write_all(writes)
        return f"CHAIN REOPEN: {' '.join(rows)} (kaskade dari {row}, re-entry {n}) — Riwayat #{num}"

    def abandon(self, reason: str) -> str:
        if not reason.strip():
            raise ChainError("`--reason` kosong — sebut keputusan user yang menutup taskdir.")
        reason = one_line(reason, "--reason")
        if read_status(self.task) == "ABANDONED":
            raise ChainError(f"`{self.task_rel}` sudah `ABANDONED` — taskdir sudah ditutup; tidak ada yang diubah.")
        text = set_frontmatter_field(self.text(), "status", "ABANDONED")
        _, problem = read_history(text)
        if problem:                                  # jalan keluar RUSAK: Riwayat rusak tidak menahan penutupan
            note = f" (Riwayat rusak, kejadian tidak dicatat: {problem})"
        else:
            text, n = self.record(text, "abandon", [], [], ("alasan", reason))
            note = f" (Riwayat #{n})"
        self.write_all({self.task_rel: text})
        return f"CHAIN ABANDON: {self.taskdir_rel} ABANDONED{note}"

    def escalate(self, lane: str, sections_raw: str, reason: str) -> str:
        if not reason.strip():
            raise ChainError("`--reason` kosong — sebut pemicu eskalasi (mis. temuan yang menuntut hop baru).")
        reason = one_line(reason, "--reason")
        self.require_active()
        events = self.require_rooted()
        sections = parse_sections(sections_raw)
        problem = lane_sections_problem(lane, sections)
        if problem:
            raise ChainError(f"pasangan tujuan tidak sah: {problem}.")
        if LANE_RANK.get(lane, -1) < LANE_RANK.get(self.lane, -1):
            raise ChainError(f"lane hanya naik: `{self.lane}` → `{lane}` adalah penurunan.")
        old_rows = expected_rows(self.sections)
        new_rows = expected_rows(sections)
        if not set(old_rows) <= set(new_rows) or not set(self.sections) <= set(sections):
            raise ChainError(f"sections hanya bertambah: `{','.join(self.sections)}` → `{','.join(sections)}`.")
        if new_rows == old_rows and lane == self.lane:
            raise ChainError("tidak ada yang berubah.")
        if sum(1 for e in events if e["kind"] == "eskalasi") >= MAX_ESCALATE:
            raise ChainError(f"plafon eskalasi taskdir ({MAX_ESCALATE}) habis — {CAP_ROUTE}.")
        problem = lane_tamper(self.root, self.taskdir_rel)
        if problem:
            raise ChainError(f"{problem} — kembalikan frontmatter ke pasangan terakhir di Riwayat, lalu ulangi.")
        entries = {e["row"]: e for e in self.entries()}
        added = [r for r in new_rows if r not in entries]
        first_added = min(new_rows.index(r) for r in added) if added else len(new_rows)
        blocked = [r for r in new_rows[first_added:] if r in entries and entries[r]["mark"] == "x"]
        if blocked:
            raise ChainError(f"hop tercentang {blocked} berada di bawah hop baru {added}; "
                             f"`reopen` hop itu lebih dulu, lalu ulangi eskalasi.")
        lines = [entries[r]["raw"].strip() if r in entries else chain_line(r) for r in new_rows]
        text = self.text()
        text = set_frontmatter_field(text, "lane", lane)
        text = set_frontmatter_field(text, "sections", ", ".join(sections) if sections else "[]")
        block = "## Chain\n\n" + "\n".join(lines) + "\n"
        text = re.sub(r"^## Chain\s*\n(?:.*\n?)*?(?=^## |\Z)", block, text, count=1, flags=re.MULTILINE)
        text, n = self.record(text, "eskalasi", [], [("lane", f"{self.lane} → {lane}"),
                                                     ("sections", f"{sections_value(self.sections)} → "
                                                                  f"{sections_value(sections)}"),
                                                     ("akar", root_sidik(text)[:12])], ("alasan", reason))
        self.write_all({self.task_rel: text})
        return f"CHAIN ESCALATE: {self.lane} → {lane}, hop baru {added or '-'} (Riwayat #{n})"

    def revisions(self, row: str) -> int:
        return revisions_since_open(self.root, self.taskdir_rel, row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ledger ## Chain dan ## Riwayat Rantai frontend")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("init", "root", "amend", "draft", "status", "verify", "approve", "reopen", "escalate",
                 "revisions", "abandon", "files"):
        p = sub.add_parser(name)
        p.add_argument("--taskdir", required=True)
        p.add_argument("--root", default=None)
        if name in ("approve", "reopen", "revisions", "draft"):
            p.add_argument("--row", required=True, choices=list(CHAIN_BY_ROW))
        if name == "verify":
            p.add_argument("--rows", default="", help="dipisah koma; kosong = semua")
        if name == "approve":
            p.add_argument("--answer", required=True, help="jawaban user apa adanya dari AskUserQuestion")
        if name in ("reopen", "escalate", "abandon", "amend"):
            p.add_argument("--reason", required=True)
        if name == "escalate":
            p.add_argument("--lane", required=True, choices=list(ROOTED_LANES))
            p.add_argument("--sections", required=True)
    args = parser.parse_args()
    try:
        chain = Chain(args.taskdir, Path(args.root) if args.root else None)
        if args.cmd == "init":
            print(chain.init())
        elif args.cmd == "root":
            print(chain.lock_root())
        elif args.cmd == "amend":
            print(chain.amend(args.reason))
        elif args.cmd == "draft":
            print(chain.draft(args.row))
        elif args.cmd == "status":
            print("\n".join(chain.status_lines()) or "(ledger kosong)")
        elif args.cmd == "verify":
            rows = [r.strip() for r in args.rows.split(",") if r.strip()] or None
            problems = chain.verify(rows)
            if problems:
                print("CHAIN VERIFY: [FAIL]\n" + "\n".join(f"- {p}" for p in problems))
                sys.exit(1)
            print("CHAIN VERIFY: [PASS] " + ", ".join(rows or [e["row"] for e in chain.entries()]))
        elif args.cmd == "approve":
            print(chain.approve(args.row, args.answer))
        elif args.cmd == "reopen":
            print(chain.reopen(args.row, args.reason))
        elif args.cmd == "escalate":
            print(chain.escalate(args.lane, args.sections, args.reason))
        elif args.cmd == "abandon":
            print(chain.abandon(args.reason))
        elif args.cmd == "files":
            print("\n".join(chain_files(chain.root, chain.taskdir_rel)) or "(nol berkas rantai)")
        elif args.cmd == "revisions":
            n = chain.revisions(args.row)
            left = MAX_REVISIONS - n
            print(f"CHAIN REVISIONS: {args.row} {n}/{MAX_REVISIONS}"
                  + (f" — plafon habis; penolakan berikutnya tidak direvisi lagi: {CAP_ROUTE} (`frontend:lead` Phase 8)"
                     if left <= 0 else f" — sisa {left}"))
            sys.exit(1 if left <= 0 else 0)
    except (ChainError, FrontmatterError, ValueError, KeyError) as exc:
        print(f"CHAIN {args.cmd.upper()}: [FAIL] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(cli(main))
