#!/usr/bin/env python3
"""Validator mekanis CHARTER.md plugin `product` — satu berkas, dua bagian.

`--kind notes` memvonis frontmatter dan `## Catatan Elisitasi` (H2 terakhir): Konteks Awal tetap seperti yang
dimateraikan `charter.py new` dan lolos guard konteks minimum, Permintaan Asli tetap, enam pilar fakta, log,
dan pertanyaan terbuka. Catatan tertutup (status selain `ELICITATION`) juga menuntut seluruh pilar terjawab,
nol pertanyaan memblokir, dan nol baris `Asumsi:`.

`--kind charter` memvonis enam pilar kartu di atasnya: Purpose, Actors (bertanda `[ADA]`/`[BARU]` di mode
codebase), Business Process (langkah bernomor beraktor terdaftar; `IMPROVEMENT` dibagi Kondisi Sekarang dan
Kondisi Target), Business Rules (`BR-n` dengan pengecualian; `IMPROVEMENT` bertanda `[TETAP]/[UBAH]/[BARU]`),
Success Criteria (`SC-n` berukuran angka), dan Scope (`S<n>` unik berurutan untuk handoff, plus daftar tidak
termasuk) — serta bukti `path:baris` yang benar-benar ada di repo.

Rumah kanonik aturannya bagian 2 `skills/discover/templates/charter-skeleton.md` dan
`skills/spec/templates/charter-template.md`; penilaian semantik milik penulis dan `charter-reviewer`.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from charter_lib import (  # noqa: E402
    CHARTER_FILE,
    CHARTERDIR_RE,
    CODE_MODES,
    CONTEXT_KEYS,
    CONTEXT_LABELS,
    ELICIT_H2,
    ELICIT_H3,
    LOG_ROW,
    MODES,
    PILLARS,
    PLACEHOLDER,
    UNANSWERED,
    Checker,
    content_hash,
    context_digest,
    context_problems,
    duplicate_headings,
    find_root,
    format_report,
    h1_lines,
    meaningful,
    normalize_dir,
    report_json,
    request_digest,
    sections,
    split_frontmatter,
)

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HASH = re.compile(r"^[0-9a-f]{12}$")
NONE_LINE = "- Tidak ada."
ELICIT_Q = re.compile(r"^- \*\*Q-(\d+)\*\* \[(MEMBLOKIR|TIDAK MEMBLOKIR)\]: .+ — menunggu: .+$")
ASSUMPTION = re.compile(r"(?:^|[\s(\[>*_])\**Asumsi\**\s*:", re.IGNORECASE)
CONTEXT_LINE = re.compile(r"^- \*\*(.+?)\*\*: (.*)$")
EVIDENCE = re.compile(r"`([^`\s:]+):(\d+)(?:-(\d+))?`")

ACTOR = re.compile(r"^- \*\*(.+?)\*\*(?: \[(ADA|BARU)\])? — (.+)$")
STEP = re.compile(r"^(\d+)\. \*\*(.+?)\*\* (.+)$")
SYSTEM_ACTOR = "Sistem"
BR_LINE = re.compile(r"^- \*\*BR-(\d+)\*\*(?: \[(TETAP|UBAH|BARU)\])?: (.+) — pengecualian: (.+)$")
BR_NONE = re.compile(r"^- Tidak ada aturan khusus — .+")
SC_LINE = re.compile(r"^- \*\*SC-(\d+)\*\*: (.+) — ukuran: (.+)$")
SC_MAX = 8
SCOPE_H3 = ("Termasuk", "Tidak Termasuk")
SCOPE_IN = re.compile(r"^- \*\*S(\d+)\*\*: .+$")
SCOPE_OUT = re.compile(r"^- .+ — .+$")
PROCESS_H3 = ("Kondisi Sekarang", "Kondisi Target")
TITLE_MAX = 12


class DocValidator(Checker):
    def __init__(self, kind: str, charterdir: str, root: Path):
        super().__init__()
        self.kind = kind
        self.root = root.resolve()
        self.rel = normalize_dir(charterdir, self.root)
        self.path = self.root / self.rel / CHARTER_FILE

    def run_all(self) -> bool:
        if not CHARTERDIR_RE.match(self.rel):
            self.add(0, "Letak charterdir", False, f"`{self.rel}` bukan product/<slug>",
                     "Pakai charterdir hasil `charter.py new`.")
            return False
        if not self.path.is_file():
            self.add(0, f"{CHARTER_FILE} terbaca", False, f"`{self.rel}/{CHARTER_FILE}` tidak ada",
                     "Alokasikan lewat `charter.py new` lebih dulu.")
            return False
        try:
            self.text = self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            self.add(0, f"{CHARTER_FILE} terbaca", False,
                     f"`{self.rel}/{CHARTER_FILE}` bukan UTF-8 ({exc.reason} @ byte {exc.start})",
                     "Simpan ulang berkasnya sebagai UTF-8; jangan menebak isinya.")
            return False
        self.fm, self.body = split_frontmatter(self.text)
        self.h2 = sections(self.body, 2)
        self.mode = self.fm.get("mode") if self.fm.get("mode") in MODES else "NEW_PRODUCT"
        (self._notes if self.kind == "notes" else self._charter)()
        return self.ok

    # ── umum ──
    def _frontmatter_common(self) -> List[str]:
        errors = []
        if self.fm.get("status") not in ("ELICITATION", "DRAFT", "APPROVED"):
            errors.append(f"status `{self.fm.get('status', '')}` bukan ELICITATION|DRAFT|APPROVED")
        if self.fm.get("mode") not in MODES:
            errors.append(f"mode `{self.fm.get('mode', '')}` bukan {'|'.join(MODES)}")
        slug = self.rel.rsplit("/", 1)[-1]
        if self.fm.get("slug") != slug:
            errors.append(f"slug `{self.fm.get('slug', '')}` ≠ nama charterdir `{slug}`")
        if not DATE.match(str(self.fm.get("created", ""))):
            errors.append("created bukan YYYY-MM-DD")
        if not str(self.fm.get("requester", "")).strip():
            errors.append("requester kosong")
        for key in ("context_hash", "request_hash"):
            if not HASH.match(str(self.fm.get(key, ""))):
                errors.append(f"{key} bukan sidik 12 hex (ditulis `charter.py new`)")
        return errors

    def _placeholder(self, cid: int, parts: Dict[str, List[str]], skip: Tuple[str, ...]) -> None:
        """Placeholder di luar seksi kutipan mentah; span kode dilewati, autolink `<https://…>` bukan slot."""
        text = "\n".join(re.sub(r"`[^`\n]*`", " ", l) for h, body in parts.items() if h not in skip for l in body)
        hits = sorted({h for h in PLACEHOLDER.findall(text) if "@" not in h and not h.startswith("<http")})
        self.add(cid, "Nol placeholder", not hits, "lolos" if not hits else ", ".join(hits[:5]),
                 "Ganti tiap `<...>`, TBD, TODO dengan isi final.")

    @property
    def closed(self) -> bool:
        return self.fm.get("status") in ("DRAFT", "APPROVED")

    # ── ## Catatan Elisitasi ──
    def _notes(self) -> None:
        errors = self._frontmatter_common()
        self.add(1, "Frontmatter", not errors, "; ".join(errors) or "lolos",
                 "Ikuti bagian 1 charter-skeleton.md; field pembukuan hanya ditulis charter.py.")

        h1 = h1_lines(self.body)
        notes = "\n".join(self.h2.get(ELICIT_H2, []))
        self.h3 = sections(notes, 3)
        errors = []
        if len(h1) != 1:
            errors.append(f"{len(h1)} H1, wajib tepat satu")
        if not self.h2 or list(self.h2)[-1] != ELICIT_H2:
            errors.append(f"`## {ELICIT_H2}` bukan H2 terakhir")
        elif tuple(self.h3) != ELICIT_H3:
            errors.append(f"sub-heading {list(self.h3)} bukan {list(ELICIT_H3)}")
        dup = duplicate_headings(self.body, 2) + duplicate_headings(notes, 3)
        if dup:
            errors.append("heading ganda (isi yang pertama tertimpa): " + ", ".join(dup))
        self.add(2, "Struktur", not errors, "; ".join(errors) or "lolos",
                 f"Satu H1; `## {ELICIT_H2}` sebagai H2 terakhir dengan lima H3 persis urutan template.")

        # 3 — Konteks Awal: label per mode, lolos guard, dan sama dengan yang dimateraikan `new`.
        lines = [l.strip() for l in meaningful(self.h3.get("Konteks Awal", []))]
        found = {m.group(1): m.group(2) for m in (CONTEXT_LINE.match(l) for l in lines) if m}
        labels = CONTEXT_LABELS[self.mode]
        errors = []
        if list(found) != list(labels) or len(lines) != len(labels):
            errors.append(f"butir {list(found)} bukan {list(labels)} (mode {self.mode})")
        else:
            errors += context_problems(self.mode, {k: found[label] for k, label in zip(CONTEXT_KEYS, labels)})
        sealed = str(self.fm.get("context_hash", "-"))
        if HASH.match(sealed) and sealed != context_digest(self.text):
            errors.append(f"Konteks Awal berubah sejak `charter.py new` (context_hash {sealed})")
        self.add(3, "Konteks awal", not errors, "; ".join(errors) or f"{len(labels)} butir",
                 "Konteks Awal dimateraikan `charter.py new`; pulihkan persis aslinya (git). Konteks yang memang "
                 "berubah berarti inisiatif baru: `charter.py cancel` lalu alokasi ulang lewat product:init.")

        request = meaningful(self.h3.get("Permintaan Asli", []))
        sealed = str(self.fm.get("request_hash", "-"))
        drifted = HASH.match(sealed) is not None and sealed != request_digest(self.text)
        ok = bool(request) and all(l.startswith(">") for l in request) and not drifted
        self.add(4, "Permintaan asli terekam", ok,
                 f"Permintaan Asli berubah sejak `charter.py new` (request_hash {sealed})" if drifted
                 else f"{len(request)} baris kutipan" if request else "kosong",
                 "Kutipan permintaan dimateraikan `charter.py new`; pulihkan persis aslinya (git). Keterangan baru "
                 "dari peminta masuk log, bukan ke kutipan.")

        facts = sections("\n".join(self.h3.get("Fakta", [])), 4)
        errors, unanswered, empty = [], [], []
        if tuple(facts) != PILLARS:
            errors.append(f"pilar {list(facts)} bukan {list(PILLARS)}")
        dup = duplicate_headings("\n".join(self.h3.get("Fakta", [])), 4)
        if dup:
            errors.append("pilar ganda: " + ", ".join(dup))
        for pillar in PILLARS:
            body = meaningful(facts.get(pillar, []))
            if not body:
                empty.append(pillar)
            elif UNANSWERED in "\n".join(body):
                unanswered.append(pillar)
        if empty:
            errors.append("pilar kosong (tulis `" + UNANSWERED + "`): " + ", ".join(empty))
        if self.closed and unanswered:
            errors.append("catatan tertutup dengan pilar belum terjawab: " + ", ".join(unanswered))
        self.add(5, "Enam pilar", not errors,
                 "; ".join(errors) or f"{len(PILLARS)} pilar" + (f", {len(unanswered)} belum terjawab"
                                                                 if unanswered else ""),
                 "Pilar `####` persis urutan template; penutupan menuntut keenamnya terisi.")

        rows = [l.strip() for l in self.h3.get("Log Tanya-Jawab", []) if l.strip().startswith("|")]
        header_ok = (len(rows) >= 2 and rows[0].count("|") == 6
                     and re.fullmatch(r"\|(\s*:?-{3,}:?\s*\|){5}", rows[1].replace(" ", "")) is not None)
        nums, bad = [], []
        for r in rows[2:] if header_ok else []:
            m = LOG_ROW.match(r)
            if m:
                nums.append(int(m.group(1)))
            else:
                bad.append(r[:40])
        errors = []
        if not header_ok:
            errors.append("tabel log tanpa header lima kolom beserta baris pemisah")
        if bad:
            errors.append(f"{len(bad)} baris log rusak")
        if nums != list(range(1, len(nums) + 1)):
            errors.append(f"nomor log {nums} tidak berurutan dari 1")
        self.add(6, "Log tanya-jawab", not errors, "; ".join(errors) or f"{len(nums)} entri",
                 "Baris `| n | YYYY-MM-DD | pertanyaan | jawaban | sumber |` bernomor urut.")

        qs = meaningful(self.h3.get("Pertanyaan Terbuka", []))
        errors, ids, blocking = [], [], 0
        if not qs:
            errors.append("seksi kosong — tulis `- Tidak ada.`")
        elif qs != [NONE_LINE]:
            for q in qs:
                m = ELICIT_Q.match(q.strip())
                if not m:
                    errors.append(f"format rusak: {q.strip()[:50]}")
                    continue
                ids.append(int(m.group(1)))
                blocking += m.group(2) == "MEMBLOKIR"
        if len(set(ids)) != len(ids):
            errors.append("ID Q ganda")
        if self.closed and blocking:
            errors.append(f"catatan tertutup dengan {blocking} pertanyaan MEMBLOKIR")
        self.add(7, "Pertanyaan terbuka", not errors,
                 "; ".join(errors) or (f"{len(ids)} terbuka, {blocking} memblokir" if ids else "nihil"),
                 "`- **Q-n** [MEMBLOKIR|TIDAK MEMBLOKIR]: <tanya> — menunggu: <siapa>`, atau `- Tidak ada.`")

        self._placeholder(8, self.h3, ("Permintaan Asli", "Log Tanya-Jawab"))

        assumed = [l.strip()[:50] for l in self.h3.get("Fakta", []) if ASSUMPTION.search(l)]
        self.add(9, "Asumsi terkonfirmasi", not (self.closed and assumed),
                 f"{len(assumed)} baris `Asumsi:`" + (" pada catatan tertutup" if self.closed and assumed else ""),
                 "Konfirmasi tiap `Asumsi:` ke peminta (hapus labelnya) atau kembalikan pilarnya ke giliran tanya-"
                 "jawab sebelum `charter.py close`.")

        # 10 — NEW_PRODUCT tidak punya kode: rujukan `path:baris` di catatan pasti karangan. Mode codebase boleh
        # mencatatnya dari balikan `code-scout`, dan tiap rujukan wajib ada di disk.
        refs = [(h, m) for h, body in self.h3.items() if h != "Permintaan Asli"
                for line in body for m in EVIDENCE.finditer(line) if re.search(r"[/.]", m.group(1))]
        self._evidence_refs(10, refs, forbid=self.mode == "NEW_PRODUCT")

    # ── kartu enam pilar ──
    def _charter(self) -> None:
        errors = self._frontmatter_common()
        if self.fm.get("status") == "ELICITATION":
            errors.append("status ELICITATION — kartu ditulis sesudah `charter.py close`")
        if not str(self.fm.get("revision", "")).isdigit():
            errors.append("revision bukan bilangan")
        self.add(1, "Frontmatter", not errors, "; ".join(errors) or "lolos",
                 "Kartu hanya ditulis product:spec atas catatan yang sudah ditutup `charter.py close`.")

        h1 = h1_lines(self.body)
        expected = PILLARS + (ELICIT_H2,)
        errors = []
        if len(h1) != 1:
            errors.append(f"{len(h1)} H1, wajib tepat satu")
        elif len(h1[0][2:].split()) > TITLE_MAX:
            errors.append(f"judul lebih dari {TITLE_MAX} kata")
        if tuple(self.h2) != expected:
            errors.append(f"heading {list(self.h2)} bukan {list(expected)}")
        dup = duplicate_headings(self.body, 2)
        if dup:
            errors.append("heading ganda: " + ", ".join(dup))
        self.add(2, "Struktur", not errors, "; ".join(errors) or "lolos",
                 f"Satu H1 ≤ {TITLE_MAX} kata, enam H2 pilar persis urutan template, lalu `## {ELICIT_H2}` tanpa "
                 "disentuh.")

        purpose = meaningful(self.h2.get("Purpose", []))
        self.add(3, "Purpose", bool(purpose), f"{len(purpose)} baris" if purpose else "kosong",
                 "Tulis masalah yang diselesaikan, untuk siapa, dan kenapa sekarang.")

        actors = self._actors(4)
        self._process(5, actors)
        self._rules(6)
        self._success(7)
        self._scope(8)
        self._placeholder(9, self.h2, (ELICIT_H2,))

        card = "\n".join(l for h in PILLARS for l in self.h2.get(h, []))
        refs = [("kartu", m) for m in EVIDENCE.finditer(card) if re.search(r"[/.]", m.group(1))]
        self._evidence_refs(10, refs, forbid=self.mode == "NEW_PRODUCT")

        if self.fm.get("status") == "APPROVED":
            current = content_hash(self.text)
            sealed = str(self.fm.get("approved_hash", ""))
            self.add(11, "Konten = yang disetujui", sealed == current,
                     f"approved_hash {sealed or '-'} · konten {current}",
                     "Charter APPROVED disunting sesudah disetujui: `charter.py reopen`, atau pulihkan isinya.")

    def _actors(self, cid: int) -> List[str]:
        lines = [l.strip() for l in meaningful(self.h2.get("Actors", []))]
        coded = self.mode in CODE_MODES
        names, errors = [], []
        for line in lines:
            m = ACTOR.match(line)
            if not m:
                errors.append(f"format rusak: {line[:50]}")
                continue
            names.append(m.group(1).strip())
            if coded and not m.group(2):
                errors.append(f"`{m.group(1)}` tanpa tanda [ADA]/[BARU] (mode {self.mode})")
            if not coded and m.group(2):
                errors.append(f"`{m.group(1)}` bertanda [{m.group(2)}] — NEW_PRODUCT belum punya aktor yang ada")
        if not lines:
            errors.append("seksi kosong")
        dup = sorted({n for n in names if names.count(n) > 1})
        if dup:
            errors.append("aktor ganda: " + ", ".join(dup))
        if SYSTEM_ACTOR in names:
            errors.append(f"`{SYSTEM_ACTOR}` bukan aktor — ia sudah sah di langkah proses tanpa didaftarkan")
        tag = " [ADA|BARU]" if coded else ""
        self.add(cid, "Actors", not errors, "; ".join(errors) or f"{len(names)} aktor",
                 f"Satu baris per aktor: `- **<Nama>**{tag} — <peran dan tanggung jawabnya>`.")
        return names

    def _process(self, cid: int, actors: List[str]) -> None:
        body = self.h2.get("Business Process", [])
        sub = sections("\n".join(body), 3)
        errors = []
        if self.mode == "IMPROVEMENT":
            if tuple(sub) != PROCESS_H3:
                errors.append(f"sub-heading {list(sub)} bukan {list(PROCESS_H3)} (mode IMPROVEMENT)")
            blocks = [(h, sub.get(h, [])) for h in PROCESS_H3]
        else:
            if sub:
                errors.append(f"sub-heading {list(sub)} hanya untuk mode IMPROVEMENT")
            blocks = [("Business Process", body)]
        allowed = set(actors) | {SYSTEM_ACTOR}
        total = 0
        for name, lines in blocks:
            steps = [l for l in meaningful(lines) if not l.startswith((" ", "\t", "###"))]
            nums = []
            for line in steps:
                m = STEP.match(line.strip())
                if not m:
                    errors.append(f"{name}: baris bukan langkah `n. **<Aktor>** <aksi>`: {line.strip()[:50]}")
                    continue
                nums.append(int(m.group(1)))
                if m.group(2).strip() not in allowed:
                    errors.append(f"{name}: aktor `{m.group(2)}` di langkah {m.group(1)} tidak ada di Actors")
            if len(nums) < 2:
                errors.append(f"{name}: {len(nums)} langkah — alur awal sampai selesai minimal 2 langkah")
            if nums != list(range(1, len(nums) + 1)):
                errors.append(f"{name}: nomor langkah {nums} tidak urut dari 1")
            total += len(nums)
        self.add(cid, "Business Process", not errors, "; ".join(errors[:6]) or f"{total} langkah",
                 "Langkah bernomor `n. **<Aktor>** <aksi>` dari pemicu sampai hasil akhir; aktornya terdaftar di "
                 f"Actors atau `{SYSTEM_ACTOR}`; cabang ditulis sebagai sub-butir berindentasi. Mode IMPROVEMENT: "
                 "`### Kondisi Sekarang` lalu `### Kondisi Target`.")

    def _rules(self, cid: int) -> None:
        lines = [l.strip() for l in meaningful(self.h2.get("Business Rules", []))]
        errors = []
        if len(lines) == 1 and BR_NONE.match(lines[0]):
            self.add(cid, "Business Rules", True, "nihil beralasan")
            return
        nums = []
        for line in lines:
            m = BR_LINE.match(line)
            if not m:
                errors.append(f"format rusak: {line[:50]}")
                continue
            nums.append(int(m.group(1)))
            if self.mode == "IMPROVEMENT" and not m.group(2):
                errors.append(f"BR-{m.group(1)} tanpa tanda [TETAP]/[UBAH]/[BARU]")
            if self.mode != "IMPROVEMENT" and m.group(2):
                errors.append(f"BR-{m.group(1)} bertanda [{m.group(2)}] — tanda hanya untuk mode IMPROVEMENT")
        if not lines:
            errors.append("seksi kosong")
        if nums != list(range(1, len(nums) + 1)):
            errors.append(f"nomor BR {nums} tidak urut dari 1")
        tag = " [TETAP|UBAH|BARU]" if self.mode == "IMPROVEMENT" else ""
        self.add(cid, "Business Rules", not errors, "; ".join(errors[:6]) or f"{len(nums)} aturan",
                 f"`- **BR-n**{tag}: <aturan> — pengecualian: <pengecualian, atau `tidak ada`>`, atau "
                 "`- Tidak ada aturan khusus — <alasan>`.")

    def _success(self, cid: int) -> None:
        lines = [l.strip() for l in meaningful(self.h2.get("Success Criteria", []))]
        errors, nums = [], []
        for line in lines:
            m = SC_LINE.match(line)
            if not m:
                errors.append(f"format rusak: {line[:50]}")
                continue
            nums.append(int(m.group(1)))
            if not re.search(r"\d", m.group(3)):
                errors.append(f"SC-{m.group(1)} ukurannya tanpa angka: {m.group(3)[:40]}")
        if not 1 <= len(nums) <= SC_MAX:
            errors.append(f"{len(nums)} kriteria — wajib 1–{SC_MAX}")
        if nums != list(range(1, len(nums) + 1)):
            errors.append(f"nomor SC {nums} tidak urut dari 1")
        self.add(cid, "Success Criteria", not errors, "; ".join(errors[:6]) or f"{len(nums)} kriteria",
                 "`- **SC-n**: <indikator> — ukuran: <angka, persen, durasi, atau ambang beserta cara/waktu ukur>`.")

    def _scope(self, cid: int) -> None:
        sub = sections("\n".join(self.h2.get("Scope", [])), 3)
        errors = []
        if tuple(sub) != SCOPE_H3:
            errors.append(f"sub-heading {list(sub)} bukan {list(SCOPE_H3)}")
        inc = [l.strip() for l in meaningful(sub.get("Termasuk", []))]
        ids = []
        for line in inc:
            m = SCOPE_IN.match(line)
            if m:
                ids.append(int(m.group(1)))
            else:
                errors.append(f"Termasuk: format rusak: {line[:50]}")
        if not ids:
            errors.append("Termasuk tanpa butir `S<n>`")
        if ids != list(range(1, len(ids) + 1)):
            errors.append(f"ID scope {ids} tidak unik dan urut dari S1")
        out = [l.strip() for l in meaningful(sub.get("Tidak Termasuk", []))]
        if not out:
            errors.append("Tidak Termasuk kosong")
        bad = [l[:50] for l in out if not SCOPE_OUT.match(l)]
        if bad:
            errors.append(f"Tidak Termasuk tanpa `— <alasan>`: {bad[0]}")
        self.add(cid, "Scope", not errors, "; ".join(errors[:6]) or f"{len(ids)} termasuk, {len(out)} tidak termasuk",
                 "`### Termasuk` berisi `- **S<n>**: <butir kerja>` berurutan dari S1 (ID tetap untuk serah-terima), "
                 "`### Tidak Termasuk` berisi `- <yang tidak dikerjakan> — <alasan>`.")

    # ── bukti kode ──
    def _evidence_refs(self, cid: int, refs: List[Tuple[str, "re.Match[str]"]], forbid: bool) -> None:
        errors = []
        if forbid and refs:
            errors.append(f"{len(refs)} rujukan `path:baris` di mode NEW_PRODUCT: "
                          + ", ".join(f"`{m.group(0).strip('`')}`" for _, m in refs[:3]))
        else:
            for where, m in refs:
                problem = self._resolve(m.group(1), int(m.group(2)), int(m.group(3) or m.group(2)))
                if problem:
                    errors.append(f"`{m.group(0).strip('`')}` ({where}) {problem}")
            if self.kind == "charter" and self.mode == "IMPROVEMENT":
                now = "\n".join(sections("\n".join(self.h2.get("Business Process", [])), 3)
                                .get("Kondisi Sekarang", []))
                if not EVIDENCE.search(now):
                    errors.append("Kondisi Sekarang tanpa satu pun bukti `path:baris`")
        self.add(cid, "Bukti kode", not errors,
                 "; ".join(errors[:6]) + (f" (+{len(errors) - 6})" if len(errors) > 6 else "") if errors
                 else f"{len(refs)} rujukan, seluruhnya ada",
                 "NEW_PRODUCT tanpa rujukan kode. Mode codebase: tiap `` `path/relatif/root:baris` `` (atau "
                 "`:awal-akhir`) ada di repo ini dan berasal dari balikan code-scout; IMPROVEMENT menuntut minimal "
                 "satu di Kondisi Sekarang.")

    def _resolve(self, rel: str, start: int, end: int) -> str:
        path = (self.root / rel).resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            return "di luar root repo"
        if not path.is_file():
            return "tidak ada"
        data = path.read_bytes()
        total = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
        if not 1 <= start <= end <= total:
            return f"melampaui {total} baris berkas"
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Validator CHARTER.md product (catatan elisitasi / kartu)")
    parser.add_argument("--kind", required=True, choices=("notes", "charter"))
    parser.add_argument("--charterdir", required=True, help="product/<slug>")
    parser.add_argument("--root", default=None, help="root ruang kerja; default root git atau cwd")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    v = DocValidator(args.kind, args.charterdir, Path(args.root) if args.root else find_root())
    ok = v.run_all()
    print(report_json(v.results, kind=args.kind, charterdir=v.rel) if args.json
          else format_report(f"validate {CHARTER_FILE} ({args.kind})", v.results))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
