#!/usr/bin/env python3
"""Ledger `## Chain` `TASK.md` — satu-satunya penulis approval, re-entry, dan eskalasi.

Transisi status dokumen planning dan pencentangan ledger **tidak** ditulis model
dengan tangan. Model mengumpulkan jawaban eksplisit user lewat `AskUserQuestion`,
lalu memanggil subperintah di bawah; skrip ini memeriksa prasyaratnya, menulis
frontmatter dan baris ledger, dan meng-commit keduanya sebagai satu langkah.

Subperintah:

- `init`       — tulis `## Chain` dari `sections` frontmatter `TASK.md` (dipakai `task`, tanpa commit).
- `status`     — cetak ledger beserta vonis keutuhan tiap baris.
- `verify`     — `FAIL` bila baris yang diminta (default: semua) belum `[x]` sah dan utuh.
- `approve`    — `FLOW`/`UI`/`CONTRACT`: `DRAFT` → `APPROVED` + centang, satu commit.
                 `BRIEF`: centang batch brief `READY` + `REVIEW-PLAN.md` `PASS`, satu commit.
- `reopen`     — buka ulang hop tercentang (`[~]`) beserta **seluruh hop tercentang di bawahnya**
                 (kaskade: yang disetujui atas hulu lama tidak lagi sah); dokumen hop turun ke
                 `DRAFT`. Plafon 3 per hop dan 6 per taskdir.
- `abandon`    — tutup taskdir yang tidak dilanjutkan (`status: ABANDONED`) atas keputusan user.
- `files`      — cetak berkas rantai (commit berscope `(<slug>)` sejak akar) — rentang review penutup.
- `escalate`   — geser `lane`/`sections` ke atas dan tambah baris ledger. Plafon 2/taskdir.
- `revisions`  — hitung revisi berturut sebuah hop; exit 1 bila plafon 2 sudah habis.

Sha yang dicentang adalah commit **konten** yang disetujui user (commit terakhir
yang menyentuh dokumennya sebelum approval), bukan commit approval itu sendiri.
Karena itu approval dan centang muat dalam satu commit. Badan commit approve
memateraikan `Konten disetujui: <sha>`, `Sidik: <hash konten tanpa status:>`,
`Review-Round:` (hop yang direview), dan `Hop: <ROW>`; hilir menjangkarkan
keutuhan pada commit approve itu (12 J44) — tahan rebase dan clone — dan isi
dokumen sekarang wajib identik dengan isinya di sana, kecuali baris `status:`.
Suntingan sesudah approval tanpa `reopen` tertangkap sebagai drift.

Batas yang dinyatakan apa adanya: skrip tidak dapat membuktikan `AskUserQuestion`
benar-benar terjadi. Yang dijaminnya adalah jejak — jawaban user dimateraikan di
badan commit approval, dan approval tanpa jawaban, atau dengan jawaban bernewline
yang dapat menyisipkan baris materai, ditolak.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from precondition_lib import (  # noqa: E402
    TASKDIR_PATTERN,
    BRIEF_GLOB,
    CHAIN_BY_ROW,
    DOC_ROWS,
    FrontmatterError,
    ROOTED_LANES,
    MINOR_LANE,
    approval_targets,
    chain_files,
    chain_line,
    count_subjects,
    expected_rows,
    find_repo_root,
    git,
    git_ok,
    is_committed,
    lane_sections_problem,
    last_commit,
    locked_brief_problems,
    normalize_taskdir,
    parse_sections,
    read_chain,
    read_status,
    replace_chain_row,
    revisions_since_open,
    set_frontmatter_field,
    snapshot_at,
    split_frontmatter,
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


class ChainError(Exception):
    """Prasyarat subperintah tidak terpenuhi; pesannya adalah tindakan remediasi."""


def one_line(value: str, flag: str) -> str:
    """Teks bebas yang masuk subjek/badan commit wajib satu baris (12 J46).

    Baris baru di `--answer` dapat menyisipkan `Konten disetujui:`/`Hop:` palsu ke materai; di
    `--reason` ia memecah subjek commit.
    """
    if "\n" in value or "\r" in value:
        raise ChainError(f"`{flag}` memuat baris baru — tulis satu baris; jawaban/alasan bernewline dapat "
                         "menyisipkan baris materai palsu ke badan commit.")
    return value.strip()


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
            raise ChainError(f"`{self.task_rel}` tidak ada — kunci akar lewat `frontend:task`.")
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

    def require_ledger_shape(self) -> None:
        present = [e["row"] for e in self.entries()]
        expected = expected_rows(self.sections)
        if present != expected:
            raise ChainError(f"ledger {present} ≠ jadwal sections {expected}; ledger rusak — "
                             "tulis ulang lewat `chain.py init` hanya bila belum ada centang.")

    def require_above(self, row: str) -> None:
        for e in self.entries():
            if e["row"] == row:
                return
            problem = verify_chain_row(self.root, self.taskdir_rel, e)
            if problem:
                raise ChainError(f"hop hulu belum sah: {problem}.")

    def require_clean(self, *rels: str) -> None:
        for rel in rels:
            if not is_committed(self.root, rel):
                raise ChainError(f"`{rel}` belum ter-commit atau punya perubahan menggantung — "
                                 "commit draft/revisinya lebih dulu.")

    def require_active(self) -> None:
        """`approve`/`reopen`/`escalate` hanya atas akar `ACTIVE` (12 J51)."""
        status = read_status(self.task)
        if status != "ACTIVE":
            raise ChainError(f"`{self.task_rel}` berstatus `{status or '(kosong)'}`, bukan `ACTIVE` — "
                             + ("taskdir sudah ditutup (`chain.py abandon`); permintaan lanjutan dibuka di "
                                "taskdir baru." if status == "ABANDONED" else
                                "akar rusak; laporkan ke user lewat `frontend:lead` (dilarang menambal akar "
                                "dengan tangan)."))

    def stamp_body(self, answer: str, sha: str, row: str, targets_row: str, review: str = "") -> str:
        """Badan materai approve (12 J44/J46): sidik dihitung dari tree `HEAD` — commit approve hanya
        menambah baris `status:`/ledger, jadi isinya sama dengan tree commit approve itu sendiri."""
        sidik = snapshot_at(self.root, "HEAD", approval_targets(self.root, self.taskdir_rel, targets_row, "HEAD"))
        return "\n".join([f"Persetujuan user: {answer}", f"Konten disetujui: {sha}", f"Sidik: {sidik}"]
                         + ([f"Review-Round: {review}"] if review else []) + [f"Hop: {row}"])

    def commit(self, paths: List[str], subject: str, body: str = "",
               originals: Optional[Dict[str, bytes]] = None) -> str:
        """Commit **hanya** `paths` — index user yang lain tidak ikut; gagal → isi dipulihkan."""
        ok, out = git_ok(self.root, "add", "--", *paths)
        if ok:
            args = ["commit", "-q", "-m", subject] + (["-m", body] if body else []) + ["--", *paths]
            ok, out = git_ok(self.root, *args)
        if not ok:
            git_ok(self.root, "reset", "-q", "--", *paths)
            for rel, data in (originals or {}).items():
                (self.root / rel).write_bytes(data)
            raise ChainError(f"`git commit` gagal (hook/lock?) — berkas dipulihkan ke keadaan "
                             f"semula: {out.strip()[-400:]}")
        return git(self.root, "rev-parse", "--short", "HEAD").strip()

    def snapshot(self, *rels: str) -> Dict[str, bytes]:
        """Isi byte persis — pemulihan sesudah commit gagal tidak boleh mengubah line ending."""
        return {r: (self.root / r).read_bytes() for r in rels if (self.root / r).is_file()}

    def write_task(self, text: str) -> None:
        write_keep_newline(self.task, text)

    def briefs(self) -> List[Path]:
        return sorted(self.taskdir.glob(BRIEF_GLOB))

    # ------------------------------------------------------------ init / status / verify

    def init(self) -> str:
        problem = lane_sections_problem(self.lane, self.sections)
        if problem:
            raise ChainError(f"frontmatter `TASK.md` tidak sah: {problem}.")
        text = self.text()
        if any(e["mark"] != " " for e in read_chain(text)):
            raise ChainError("ledger sudah punya centang; `init` hanya untuk akar yang baru ditulis.")
        block = "## Chain\n\n" + "\n".join(chain_line(r) for r in expected_rows(self.sections)) + "\n"
        if re.search(r"^## Chain\s*$", text, flags=re.MULTILINE):
            text = re.sub(r"^## Chain\s*\n(?:.*\n?)*?(?=^## |\Z)", block, text,
                          count=1, flags=re.MULTILINE)
        else:
            text = text.rstrip("\n") + "\n\n" + block
        self.write_task(text)
        return f"CHAIN INIT: {', '.join(expected_rows(self.sections))} ditulis ke {self.task_rel} (belum di-commit)"

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

    # ------------------------------------------------------------ approve

    def approve(self, row: str, answer: str) -> str:
        if not answer.strip():
            raise ChainError("`--answer` kosong — approval wajib memateraikan jawaban eksplisit "
                             "user dari `AskUserQuestion`. Diam atau jawaban ambigu bukan persetujuan.")
        answer = one_line(answer, "--answer")
        self.require_active()
        self.require_ledger_shape()
        entry = self.entry(row)
        if entry["mark"] == "x":
            raise ChainError(f"hop `{row}` sudah tercentang @ {entry['sha']}; revisi hanya lewat `reopen`.")
        self.require_above(row)
        if row in DOC_ROWS:
            return self._approve_doc(row, entry, answer)
        return self._approve_brief(entry, answer)

    def _approve_doc(self, row: str, entry: Dict, answer: str) -> str:
        doc = CHAIN_BY_ROW[row][2]
        rel = f"{self.taskdir_rel}/{doc}"
        path = self.root / rel
        if not path.is_file():
            raise ChainError(f"`{rel}` tidak ada — tulis dan commit draft-nya lebih dulu.")
        self.require_clean(rel, self.task_rel)
        status = read_status(path)
        if status != "DRAFT":
            raise ChainError(f"`{doc}` berstatus `{status or '(kosong)'}`; hanya `DRAFT` yang dapat disetujui.")
        kind = {"FLOW": "flow", "UI": "ui", "CONTRACT": "contract"}[row]
        validator = PLUGIN_SKILLS / "_common" / "validate_doc.py"
        proc = subprocess.run([sys.executable, str(validator), "--kind", kind,
                               "--taskdir", self.taskdir_rel, "--root", str(self.root)],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        if proc.returncode != 0:
            raise ChainError(f"`validate_doc.py --kind {kind}` FAIL — perbaiki draft dulu:\n{proc.stdout}")
        review = self._require_review_pass("contract") if row == "CONTRACT" else ""
        sha = last_commit(self.root, rel)
        body = self.stamp_body(answer, sha, row, row, review)
        originals = self.snapshot(rel, self.task_rel)
        write_keep_newline(path, set_frontmatter_field(path.read_text(encoding="utf-8"), "status", "APPROVED"))
        tail = f"APPROVED {sha}" + (f" (re-entry {entry['n']}, was {entry['sha']})" if entry["mark"] == "~" else "")
        self.write_task(replace_chain_row(self.text(), row, chain_line(row, "x", tail)))
        new = self.commit([rel, self.task_rel], f"docs({self.slug}): approve {doc}", body, originals)
        return f"CHAIN APPROVE: {row} @ APPROVED {sha} — commit {new}"

    def _approve_brief(self, entry: Dict, answer: str) -> str:
        briefs = self.briefs()
        if not briefs:
            raise ChainError("nol `brief-*.md` di taskdir — jalankan `frontend:plan` lebih dulu.")
        rels = [f"{self.taskdir_rel}/{b.name}" for b in briefs]
        self.require_clean(*rels, self.task_rel)
        bad = [f"{b.name} ({read_status(b) or 'kosong'})" for b in briefs
               if read_status(b) not in ("READY", "DONE", "BLOCKED")]
        if bad:
            raise ChainError("status brief di luar READY/DONE/BLOCKED: " + ", ".join(bad))
        if not any(read_status(b) == "READY" for b in briefs) and entry["mark"] != "~":
            raise ChainError("nol brief `READY` — tidak ada breakdown baru untuk disetujui.")
        if entry["mark"] == "~":
            locked = locked_brief_problems(self.root, self.taskdir_rel)
            if locked:
                raise ChainError("brief terkunci saat hop BRIEF dibuka ulang berubah: " + ", ".join(locked)
                                 + " — brief `DONE`/`BLOCKED` tidak pernah disunting atau dinaikkan lagi; "
                                   "pulihkan isinya (`git checkout <reopen> -- <brief>`) dan tulis brief remedi "
                                   "(`remedies: \"NN\"`) untuk sisa pekerjaan unit `BLOCKED`.")
        validator = PLUGIN_SKILLS / "plan" / "scripts" / "validate_briefs.py"
        args = [sys.executable, str(validator), "--taskdir", self.taskdir_rel, "--root", str(self.root)]
        if self.sections:
            args.append("--contract")
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        if proc.returncode != 0:
            raise ChainError(f"`validate_briefs.py` FAIL — perbaiki brief dulu:\n{proc.stdout}")
        paths = list(rels)
        new_work = any(read_status(b) == "READY" for b in briefs)
        review_line = ""
        if self.lane != MINOR_LANE and new_work:
            review_rel = f"{self.taskdir_rel}/REVIEW-PLAN.md"
            review = self.root / review_rel
            if not review.is_file():
                raise ChainError("`REVIEW-PLAN.md` tidak ada — Gate Plan Review belum jalan.")
            self.require_clean(review_rel)
            verdict = read_status(review, "verdict")
            if verdict != "PASS":
                raise ChainError(f"`REVIEW-PLAN.md` ber-verdict `{verdict or '(kosong)'}`, bukan `PASS`.")
            review_line = self._require_review_pass("plan")
            paths.append(review_rel)
        sha = last_commit(self.root, *paths)
        body = self.stamp_body(answer, sha, "BRIEF", "BRIEF", review_line)
        originals = self.snapshot(self.task_rel)
        tail = f"READY {sha}" + (f" (re-entry {entry['n']}, was {entry['sha']})" if entry["mark"] == "~" else "")
        self.write_task(replace_chain_row(self.text(), "BRIEF", chain_line("BRIEF", "x", tail)))
        n = sum(1 for b in briefs if read_status(b) == "READY")
        new = self.commit([self.task_rel], f"docs({self.slug}): approve breakdown ({n} briefs)", body, originals)
        return f"CHAIN APPROVE: BRIEF @ READY {sha} — commit {new}"

    def _require_review_pass(self, gate: str) -> str:
        """Ronde reviewer terakhir wajib `PASS` atas konten yang persis sama dan epoch reopen sekarang.

        Mengembalikan nilai baris `Review-Round:` materai approve (12 J46): `<gate> r<n> t<total> PASS <sidik12>`.
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
        self.require_ledger_shape()
        entry = self.entry(row)
        if entry["mark"] != "x":
            raise ChainError(f"hop `{row}` tidak tercentang; tidak ada yang dibuka ulang.")
        pattern = rf"^docs\({re.escape(self.slug)}\): reopen "
        used = count_subjects(self.root, pattern, self.task_rel)
        if used >= MAX_REOPEN:
            raise ChainError(f"plafon re-entry taskdir ({MAX_REOPEN}) habis — cacatnya satu lapis di atas "
                             f"hop ini; {CAP_ROUTE}.")
        # kuota per hop: hanya reopen yang menargetkan hop ini (token pertama subjek);
        # kaskade tidak memakan kuota hop di bawahnya — plafon taskdir tetap membatasi total
        n = count_subjects(self.root, rf"{pattern}{row}\b", self.task_rel) + 1
        if n > MAX_REOPEN_ROW:
            raise ChainError(f"plafon re-entry hop `{row}` ({MAX_REOPEN_ROW}) habis — {CAP_ROUTE}.")
        entries = self.entries()
        idx = [e["row"] for e in entries].index(row)
        cascade = [e for e in entries[idx:] if e["mark"] == "x"]
        docs = {f"{self.taskdir_rel}/{CHAIN_BY_ROW[e['row']][2]}": e["sha"] for e in cascade if e["row"] in DOC_ROWS}
        # 12 J47: commit reopen hanya membawa ledger + baris `status:`; suntingan menggantung tidak ikut tersapu
        dirty = [rel for rel in (self.task_rel, *docs) if (self.root / rel).is_file()
                 and not is_committed(self.root, rel)]
        if dirty:
            raise ChainError(f"{', '.join(f'`{d}`' for d in dirty)} punya perubahan menggantung — reopen hanya "
                             "meng-commit ledger dan baris `status:`. Suntingan akar → amandemen akar lebih dulu "
                             "(`validate_task.py --amend`, commit `amandemen akar TASK`); suntingan dokumen → "
                             f"`git stash push -- {' '.join(dirty)}`, ulangi reopen, lalu `git stash pop` dan "
                             "lanjutkan di gate pemiliknya. Tidak ada berkas yang diubah.")
        originals = self.snapshot(self.task_rel, *docs)
        staged: Dict[str, str] = {}
        for rel, sha in docs.items():                 # 1) validasi seluruh kaskade — belum ada yang ditulis
            if rel not in originals:
                raise ChainError(f"`{rel}` hilang dari disk padahal hop-nya tercentang @ {sha} — "
                                 f"pulihkan dengan `git checkout {sha} -- {rel}`, lalu ulangi reopen. "
                                 "Tidak ada berkas yang diubah.")
            try:
                staged[rel] = set_frontmatter_field((self.root / rel).read_text(encoding="utf-8"),
                                                    "status", "DRAFT")
            except FrontmatterError as exc:
                raise ChainError(f"`{rel}`: {exc} — pulihkan frontmatter dari commit tercentang "
                                 f"(`git show {sha}:{rel}`), lalu ulangi reopen. Tidak ada berkas yang diubah.")
        text = self.text()
        for e in cascade:
            r = e["row"]
            # label informasional: target = hitungan target, kaskade = total pembukaan hop itu
            k = n if r == row else count_subjects(self.root, rf"{pattern}[A-Z ]*\b{r}\b", self.task_rel) + 1
            text = replace_chain_row(text, r, chain_line(r, "~", f"re-entry {k} (was {e['sha']})"))
        try:                                          # 2) tulis semuanya; gagal di tengah → pulihkan
            for rel, new_text in staged.items():
                write_keep_newline(self.root / rel, new_text)
            self.write_task(text)
        except OSError as exc:
            stuck = []
            for rel, old in originals.items():
                try:
                    if (self.root / rel).read_bytes() != old:
                        (self.root / rel).write_bytes(old)
                except OSError:
                    stuck.append(rel)
            if stuck:
                raise ChainError(f"gagal menulis kaskade ({exc}); {', '.join(stuck)} tidak dapat dipulihkan — "
                                 f"`git checkout -- {' '.join(stuck)}` lalu ulangi reopen.")
            raise ChainError(f"gagal menulis kaskade ({exc}) — berkas dipulihkan ke keadaan semula.")
        paths = [self.task_rel, *staged]
        rows = " ".join(e["row"] for e in cascade)
        new = self.commit(paths, f"docs({self.slug}): reopen {rows} — {reason[:72]}",
                          "", originals)
        return f"CHAIN REOPEN: {rows} (kaskade dari {row}, re-entry {n}) — commit {new}"

    def abandon(self, reason: str) -> str:
        if not reason.strip():
            raise ChainError("`--reason` kosong — sebut keputusan user yang menutup taskdir.")
        reason = one_line(reason, "--reason")
        if read_status(self.task) == "ABANDONED":
            raise ChainError(f"`{self.task_rel}` sudah `ABANDONED` — taskdir sudah ditutup; tidak ada yang diubah.")
        self.require_clean(self.task_rel)
        originals = self.snapshot(self.task_rel)
        self.write_task(set_frontmatter_field(self.text(), "status", "ABANDONED"))
        new = self.commit([self.task_rel], f"docs({self.slug}): tutup taskdir — {reason[:72]}",
                          "", originals)
        return f"CHAIN ABANDON: {self.taskdir_rel} ABANDONED — commit {new}"

    def escalate(self, lane: str, sections_raw: str, reason: str) -> str:
        reason = one_line(reason, "--reason")
        self.require_active()
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
        used = count_subjects(self.root, rf"^docs\({re.escape(self.slug)}\): eskalasi lane", self.task_rel)
        if used >= MAX_ESCALATE:
            raise ChainError(f"plafon eskalasi taskdir ({MAX_ESCALATE}) habis — {CAP_ROUTE}.")
        self.require_clean(self.task_rel)
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
        originals = self.snapshot(self.task_rel)
        self.write_task(text)
        new = self.commit([self.task_rel], f"docs({self.slug}): eskalasi lane {self.lane} → {lane}",
                          f"Alasan: {reason}\nSections: {','.join(self.sections) or '-'} → {','.join(sections)}",
                          originals)
        return f"CHAIN ESCALATE: {self.lane} → {lane}, hop baru {added or '-'} — commit {new}"

    def revisions(self, row: str) -> int:
        if row in DOC_ROWS:
            doc = CHAIN_BY_ROW[row][2]
            return revisions_since_open(self.root, [f"{self.taskdir_rel}/{doc}"], self.slug, doc)
        return revisions_since_open(self.root, [f"{self.taskdir_rel}/{BRIEF_GLOB}"], self.slug, "breakdown")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ledger ## Chain frontend")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("init", "status", "verify", "approve", "reopen", "escalate", "revisions",
                 "abandon", "files"):
        p = sub.add_parser(name)
        p.add_argument("--taskdir", required=True)
        p.add_argument("--root", default=None)
        if name in ("approve", "reopen", "revisions"):
            p.add_argument("--row", required=True, choices=list(CHAIN_BY_ROW))
        if name == "verify":
            p.add_argument("--rows", default="", help="dipisah koma; kosong = semua")
        if name == "approve":
            p.add_argument("--answer", required=True, help="jawaban user apa adanya dari AskUserQuestion")
        if name in ("reopen", "escalate", "abandon"):
            p.add_argument("--reason", required=True)
        if name == "escalate":
            p.add_argument("--lane", required=True, choices=list(ROOTED_LANES))
            p.add_argument("--sections", required=True)
    args = parser.parse_args()
    try:
        chain = Chain(args.taskdir, Path(args.root) if args.root else None)
        if args.cmd == "init":
            print(chain.init())
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
