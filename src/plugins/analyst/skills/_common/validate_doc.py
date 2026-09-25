#!/usr/bin/env python3
"""Validator mekanis TICKET.md plugin `analyst` — satu berkas, dua bagian.

`--kind elicit` memvonis frontmatter dan `## Catatan Elisitasi` (H2 terakhir):
bentuk catatan dan, bila `elicitation: CLOSED`, kelengkapan pilar wajib, nol
pertanyaan memblokir, nol baris `Asumsi:`, dan jejak tiap `domain_terms`. `--kind ticket` memvonis kartu di atasnya: bentuk
tiket, penomoran AC/BR, keterpikulan tiap `BR-{n}` oleh AC, nol placeholder,
dan nol kebocoran teknis. Rumah kanonik aturannya bagian 2
`skills/elicit/templates/elicit-template.md` dan
`skills/spec/templates/ticket-template.md`; penilaian semantik tetap milik
penulis dan `ticket-reviewer`.

Zero external dependencies (Python Standard Library only).
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyst_lib import (  # noqa: E402
    ELICIT_H2,
    PILLARS_OPTIONAL,
    PILLARS_REQUIRED,
    PLACEHOLDER,
    PRIORITIES,
    TICKET_FILE,
    TICKETDIR_RE,
    TYPES,
    UNANSWERED,
    Checker,
    body_offset,
    content_hash,
    find_root,
    format_report,
    meaningful,
    normalize_ticketdir,
    report_json,
    scan_leaks,
    sections,
    split_frontmatter,
)

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ELICIT_H3 = ("Permintaan Asli", "Fakta", "Log Tanya-Jawab", "Pertanyaan Terbuka")
CARD_H2 = {
    "FEATURE": ("Latar Belakang", "User Story", "Acceptance Criteria", "Aturan Bisnis",
                "Di Luar Cakupan", "Pertanyaan Terbuka", "Lampiran"),
    "BUG": ("Latar Belakang", "Laporan Bug", "Acceptance Criteria", "Aturan Bisnis",
            "Di Luar Cakupan", "Pertanyaan Terbuka", "Lampiran"),
}
CARD_H2["IMPROVEMENT"] = CARD_H2["FEATURE"]
NONE_LINE = "- Tidak ada."
SKIPPED = re.compile(r"^Tidak dibahas — .+")
ELICIT_Q = re.compile(r"^- \*\*Q-(\d+)\*\* \[(MEMBLOKIR|TIDAK MEMBLOKIR)\]: .+ — menunggu: .+$")
LOG_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|(.+)\|(.+)\|(.+)\|\s*$")
STORY = re.compile(r"^Sebagai .+, saya ingin .+, agar .+$")
AC_LINE = re.compile(r"^- \*\*AC-(\d+)\*\*: (.+)$")
GWT = re.compile(r"^(given|dengan kondisi)\b.+\b(when|ketika)\b.+\b(then|maka)\b.+", re.IGNORECASE)
BR_LINE = re.compile(r"^- \*\*BR-(\d+)\*\*: .+")
BR_NONE = re.compile(r"^- Tidak ada aturan khusus — .+")
BR_TOKEN = re.compile(r"\bBR-(\d+)\b")
OOS_LINE = re.compile(r"^- .+ — .+$")
TICKET_Q = re.compile(r"^- \*\*Q-(\d+)\*\*: .+ — asumsi: .+$")
ASSUMPTION = re.compile(r"^\s*(?:[-*]\s+)?Asumsi:")
BUG_FIELDS = ("**Langkah reproduksi**:", "**Yang diharapkan**:", "**Yang terjadi**:", "**Dampak**:")


class DocValidator(Checker):
    def __init__(self, kind: str, ticketdir: str, root: Path):
        super().__init__()
        self.kind = kind
        self.root = root.resolve()
        self.rel = normalize_ticketdir(ticketdir, self.root)
        self.name = TICKET_FILE
        self.path = self.root / self.rel / self.name

    def run_all(self) -> bool:
        if not TICKETDIR_RE.match(self.rel):
            self.add(0, "Letak ticketdir", False, f"`{self.rel}` bukan analyst/tickets/<YYMMDDhhmm>-<slug>",
                     "Pakai ticketdir hasil `ticket.py new`.")
            return False
        if not self.path.is_file():
            self.add(0, f"{self.name} terbaca", False, f"`{self.rel}/{self.name}` tidak ada",
                     "Tulis berkasnya lebih dulu.")
            return False
        self.text = self.path.read_text(encoding="utf-8")
        self.fm, self.body = split_frontmatter(self.text)
        self.h2 = sections(self.body, 2)
        (self._elicit if self.kind == "elicit" else self._ticket)()
        return self.ok

    # ── umum ──
    def _frontmatter_common(self) -> List[str]:
        errors = []
        if self.fm.get("status") not in ("DRAFT", "READY"):
            errors.append(f"status `{self.fm.get('status', '')}` bukan DRAFT|READY")
        if self.fm.get("elicitation") not in ("OPEN", "CLOSED"):
            errors.append(f"elicitation `{self.fm.get('elicitation', '')}` bukan OPEN|CLOSED")
        if self.fm.get("type") not in TYPES:
            errors.append(f"type `{self.fm.get('type', '')}` bukan {'|'.join(TYPES)}")
        slug = self.rel.rsplit("/", 1)[-1].split("-", 1)[-1]
        if self.fm.get("slug") != slug:
            errors.append(f"slug `{self.fm.get('slug', '')}` ≠ slug ticketdir `{slug}`")
        if not DATE.match(str(self.fm.get("created", ""))):
            errors.append("created bukan YYYY-MM-DD")
        if not str(self.fm.get("requester", "")).strip():
            errors.append("requester kosong")
        return errors

    def _placeholder(self, cid: int, parts: dict, skip: tuple) -> None:
        """Placeholder di luar seksi kutipan mentah; autolink `<https://…>` dan `<nama@…>` bukan slot."""
        text = "\n".join(l for h, lines in parts.items() if h not in skip for l in lines)
        hits = sorted({h for h in PLACEHOLDER.findall(text) if "@" not in h and not h.startswith("<http")})
        self.add(cid, "Nol placeholder", not hits, "lolos" if not hits else ", ".join(hits[:5]),
                 "Ganti tiap `<...>`, TBD, TODO dengan isi final.")

    # ── ## Catatan Elisitasi ──
    def _elicit(self) -> None:
        errors = self._frontmatter_common()
        self.add(1, "Frontmatter", not errors, "; ".join(errors) or "lolos",
                 "Ikuti bagian 1 elicit-template.md.")
        closed = self.fm.get("elicitation") == "CLOSED"
        typ = self.fm.get("type", "FEATURE") if self.fm.get("type") in TYPES else "FEATURE"

        h1 = [l for l in self.body.splitlines() if l.startswith("# ")]
        self.h3 = sections("\n".join(self.h2.get(ELICIT_H2, [])), 3)
        errors = []
        if len(h1) != 1:
            errors.append(f"{len(h1)} H1, wajib tepat satu")
        if not self.h2 or list(self.h2)[-1] != ELICIT_H2:
            errors.append(f"`## {ELICIT_H2}` bukan H2 terakhir")
        elif tuple(self.h3) != ELICIT_H3:
            errors.append(f"sub-heading {list(self.h3)} bukan {list(ELICIT_H3)}")
        self.add(2, "Struktur", not errors, "; ".join(errors) or "lolos",
                 f"Satu H1; `## {ELICIT_H2}` sebagai H2 terakhir dengan empat H3 persis urutan template.")

        request = meaningful(self.h3.get("Permintaan Asli", []))
        self.add(3, "Permintaan asli terekam", bool(request) and all(l.startswith(">") for l in request),
                 f"{len(request)} baris kutipan" if request else "kosong",
                 "Kutip permintaan user apa adanya sebagai blockquote `> `.")

        facts = sections("\n".join(self.h3.get("Fakta", [])), 4)
        expected = [p for p in PILLARS_REQUIRED[typ] + PILLARS_OPTIONAL[typ]]
        errors = []
        if list(facts) != expected:
            errors.append(f"pilar {list(facts)} bukan {expected}")
        unanswered, empty = [], []
        for pillar in expected:
            body = meaningful(facts.get(pillar, []))
            joined = "\n".join(body)
            if not body:
                empty.append(pillar)
            elif UNANSWERED in joined:
                unanswered.append(pillar)
            elif joined.startswith("Tidak dibahas"):
                if pillar in PILLARS_REQUIRED[typ]:
                    errors.append(f"{pillar}: pilar wajib tidak boleh `Tidak dibahas`")
                elif not SKIPPED.match(joined):
                    errors.append(f"{pillar}: `Tidak dibahas` tanpa `— <alasan>`")
        if empty:
            errors.append("pilar kosong (tulis `" + UNANSWERED + "`): " + ", ".join(empty))
        if closed and unanswered:
            errors.append("CLOSED dengan pilar belum terjawab: " + ", ".join(unanswered))
        summary = "; ".join(errors) or (f"{len(expected)} pilar" + (f", {len(unanswered)} belum terjawab"
                                                                    if unanswered else ""))
        self.add(4, f"Pilar {typ}", not errors, summary,
                 "Pilar `####` persis urutan template; CLOSED menuntut seluruh pilar terisi, "
                 "pilar opsional boleh `Tidak dibahas — <alasan>`.")

        rows = [l.strip() for l in self.h3.get("Log Tanya-Jawab", []) if l.strip().startswith("|")]
        header_ok = (len(rows) >= 2 and rows[0].count("|") == 6
                     and re.fullmatch(r"\|(\s*:?-{3,}:?\s*\|){5}", rows[1].replace(" ", "")) is not None)
        data = rows[2:] if header_ok else []
        nums, bad = [], []
        for r in data:
            m = LOG_ROW.match(r)
            if not m:
                bad.append(r[:40])
            else:
                nums.append(int(m.group(1)))
        errors = []
        if not header_ok:
            errors.append("tabel log tanpa header lima kolom beserta baris pemisah")
        if bad:
            errors.append(f"{len(bad)} baris log rusak")
        if nums != list(range(1, len(nums) + 1)):
            errors.append(f"nomor log {nums} tidak berurutan dari 1")
        self.add(5, "Log tanya-jawab", not errors, "; ".join(errors) or f"{len(nums)} entri",
                 "Baris `| n | YYYY-MM-DD | pertanyaan | jawaban | sumber |` bernomor urut.")

        qs = meaningful(self.h3.get("Pertanyaan Terbuka", []))
        errors, ids, blocking = [], [], 0
        if qs != [NONE_LINE]:
            for q in qs:
                m = ELICIT_Q.match(q.strip())
                if not m:
                    errors.append(f"format rusak: {q.strip()[:50]}")
                    continue
                ids.append(int(m.group(1)))
                blocking += m.group(2) == "MEMBLOKIR"
            if not qs:
                errors.append("seksi kosong — tulis `- Tidak ada.`")
        if len(set(ids)) != len(ids):
            errors.append("ID Q ganda")
        if closed and blocking:
            errors.append(f"CLOSED dengan {blocking} pertanyaan MEMBLOKIR")
        self.add(6, "Pertanyaan terbuka", not errors,
                 "; ".join(errors) or (f"{len(ids)} terbuka, {blocking} memblokir" if ids else "nihil"),
                 "`- **Q-n** [MEMBLOKIR|TIDAK MEMBLOKIR]: <tanya> — menunggu: <siapa>`, atau `- Tidak ada.`")

        self._placeholder(7, self.h3, ("Permintaan Asli", "Log Tanya-Jawab"))

        terms = self.fm.get("domain_terms", [])
        self.add(8, "domain_terms", isinstance(terms, list), f"{len(terms) if isinstance(terms, list) else '-'} istilah",
                 "Tulis `domain_terms: [<istilah>, ...]` atau `domain_terms: []`.")

        # 9–10 hanya menagih saat CLOSED: selama OPEN, asumsi dan istilah yang belum dikonfirmasi sah.
        assumed = [l.strip()[:50] for l in self.h3.get("Fakta", []) if ASSUMPTION.match(l)]
        self.add(9, "Asumsi terkonfirmasi", not (closed and assumed),
                 f"{len(assumed)} baris `Asumsi:`" + (" pada CLOSED" if closed and assumed else ""),
                 "Konfirmasi tiap `Asumsi:` di Phase 4 elicit (hapus labelnya) atau kembalikan pilarnya ke "
                 "Phase 2 sebelum `elicitation: CLOSED`.")

        trail = "\n".join(self.h3.get("Permintaan Asli", []) + self.h3.get("Log Tanya-Jawab", [])).lower()
        listed = terms if isinstance(terms, list) else []
        untraced = [t for t in listed if t.strip() and not re.search(
            rf"(?<![\w-]){re.escape(t.strip().lower())}(?![\w-])", trail)]
        self.add(10, "domain_terms berjejak", not (closed and untraced),
                 "lolos" if not untraced else "tanpa jejak di Permintaan Asli/Log: " + ", ".join(untraced),
                 "Tiap istilah `domain_terms` wajib muncul di permintaan asli atau baris log konfirmasinya "
                 "(`| n | ... | Apakah \"<istilah>\" nama produk? | Ya | <peminta> |`).")

    # ── kartu tiket ──
    def _ticket(self) -> None:
        errors = self._frontmatter_common()
        if self.fm.get("priority") not in PRIORITIES:
            errors.append(f"priority `{self.fm.get('priority', '')}` bukan {'|'.join(PRIORITIES)}")
        if not str(self.fm.get("revision", "")).isdigit():
            errors.append("revision bukan bilangan")
        self.add(1, "Frontmatter", not errors, "; ".join(errors) or "lolos",
                 "Ikuti bagian 1 elicit-template.md dan field kartu ticket-template.md.")
        typ = self.fm.get("type") if self.fm.get("type") in TYPES else "FEATURE"

        h1 = [l for l in self.body.splitlines() if l.startswith("# ")]
        expected = CARD_H2[typ] + (ELICIT_H2,)
        errors = []
        if len(h1) != 1:
            errors.append(f"{len(h1)} H1, wajib tepat satu")
        elif len(h1[0][2:].split()) > 12:
            errors.append("judul lebih dari 12 kata")
        if tuple(self.h2) != expected:
            errors.append(f"heading {list(self.h2)} bukan {list(expected)}")
        self.add(2, "Struktur", not errors, "; ".join(errors) or "lolos",
                 f"Satu H1, tujuh H2 kartu persis urutan template tipe {typ}, lalu `## {ELICIT_H2}` "
                 "tanpa disentuh.")

        background = meaningful(self.h2.get("Latar Belakang", []))
        if typ == "BUG":
            report = "\n".join(self.h2.get("Laporan Bug", []))
            missing = [f for f in BUG_FIELDS if f not in report]
            steps = re.findall(r"^\s*\d+\. .+", report, re.MULTILINE)
            ok = bool(background) and not missing and bool(steps)
            summary = ("; ".join(filter(None, ["latar belakang kosong" if not background else "",
                                               f"field hilang: {', '.join(missing)}" if missing else "",
                                               "langkah reproduksi tanpa daftar bernomor" if not steps else ""]))
                       or f"{len(steps)} langkah reproduksi")
            self.add(3, "Latar belakang & laporan bug", ok, summary,
                     "Isi keempat field Laporan Bug; langkah reproduksi berupa daftar `1. `.")
        else:
            story = meaningful(self.h2.get("User Story", []))
            ok = bool(background) and len(story) == 1 and bool(STORY.match(story[0].strip()))
            self.add(3, "Latar belakang & user story", ok,
                     "lolos" if ok else f"latar belakang {'ada' if background else 'kosong'}, "
                                        f"{len(story)} baris user story",
                     "Tepat satu kalimat `Sebagai <peran>, saya ingin <kemampuan>, agar <manfaat>.`")

        acs = meaningful(self.h2.get("Acceptance Criteria", []))
        nums, bad, cited = [], [], set()
        for line in acs:
            m = AC_LINE.match(line.strip())
            if not m or not GWT.match(m.group(2)):
                bad.append(line.strip()[:50])
                continue
            nums.append(int(m.group(1)))
            cited.update(int(n) for n in BR_TOKEN.findall(m.group(2)))
        ok = not bad and 1 <= len(nums) <= 10 and nums == list(range(1, len(nums) + 1))
        self.add(4, "Acceptance Criteria", ok,
                 f"{len(nums)} AC" + (f"; {len(bad)} baris tanpa Given/When/Then" if bad else "")
                 + ("" if nums == list(range(1, len(nums) + 1)) else f"; nomor {nums} tidak urut"),
                 "1–10 baris `- **AC-n**: Given …, when …, then …` bernomor urut dari AC-1.")

        brs = meaningful(self.h2.get("Aturan Bisnis", []))
        errors = []
        if len(brs) == 1 and BR_NONE.match(brs[0].strip()):
            br_ids: List[int] = []
        else:
            br_ids = [int(m.group(1)) for m in (BR_LINE.match(l.strip()) for l in brs) if m]
            if len(br_ids) != len(brs) or not brs:
                errors.append("baris aturan rusak atau seksi kosong")
            if br_ids != list(range(1, len(br_ids) + 1)):
                errors.append(f"nomor BR {br_ids} tidak urut dari 1")
        orphan = sorted(set(br_ids) - cited)
        ghost = sorted(cited - set(br_ids))
        if orphan:
            errors.append("BR tanpa AC pemikul: " + ", ".join(f"BR-{n}" for n in orphan))
        if ghost:
            errors.append("AC merujuk BR hantu: " + ", ".join(f"BR-{n}" for n in ghost))
        self.add(5, "Aturan bisnis terpikul", not errors,
                 "; ".join(errors) or (f"{len(br_ids)} BR, seluruhnya dipikul AC" if br_ids else "nihil beralasan"),
                 "`- **BR-n**: <aturan>` bernomor urut dan disebut minimal satu AC, atau "
                 "`- Tidak ada aturan khusus — <alasan>`.")

        oos = meaningful(self.h2.get("Di Luar Cakupan", []))
        ok = bool(oos) and all(OOS_LINE.match(l.strip()) for l in oos)
        self.add(6, "Di luar cakupan bersuara", ok, f"{len(oos)} butir",
                 "Minimal satu `- <yang tidak dikerjakan> — <alasan>`.")

        qs = meaningful(self.h2.get("Pertanyaan Terbuka", []))
        ok = qs == [NONE_LINE] or (bool(qs) and all(TICKET_Q.match(q.strip()) for q in qs))
        ok = ok and "MEMBLOKIR" not in "\n".join(qs)
        attach = meaningful(self.h2.get("Lampiran", []))
        ok = ok and bool(attach) and all(l.strip().startswith("- ") for l in attach)
        self.add(7, "Pertanyaan terbuka & lampiran", ok,
                 f"{0 if qs == [NONE_LINE] else len(qs)} pertanyaan, {len(attach)} baris lampiran",
                 "Pertanyaan `- **Q-n**: <tanya> — asumsi: <asumsi>` (non-blocking saja) atau `- Tidak ada.`; "
                 "Lampiran berupa butir daftar (tautan atau nama dokumen) atau `- Tidak ada.`")

        self._placeholder(8, self.h2, ("Lampiran", ELICIT_H2))

        terms = self.fm.get("domain_terms", [])
        terms = terms if isinstance(terms, list) else [terms]
        leaks = scan_leaks(self.body, terms, skip_sections=("Lampiran", ELICIT_H2),
                           line_offset=body_offset(self.text, self.body))
        self.add(9, "Nol kebocoran teknis", not leaks,
                 "lolos" if not leaks else "; ".join(leaks[:6]) + (f" (+{len(leaks) - 6})" if len(leaks) > 6 else ""),
                 "Tulis ulang dalam bahasa perilaku yang dilihat pengguna; kutip teks layar dalam "
                 "tanda kutip; istilah yang memang kosakata produk dicatat analyst:elicit di "
                 "`domain_terms` lebih dulu.")

        if self.fm.get("status") == "READY":
            current = content_hash(self.text)
            sealed = str(self.fm.get("approved_hash", ""))
            self.add(10, "Konten = yang disetujui", sealed == current,
                     f"approved_hash {sealed or '-'} · konten {current}",
                     "Tiket READY disunting sesudah disetujui: `ticket.py reopen`, atau pulihkan isinya.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validator TICKET.md analyst (catatan elisitasi / kartu)")
    parser.add_argument("--kind", required=True, choices=("elicit", "ticket"))
    parser.add_argument("--ticketdir", required=True, help="analyst/tickets/<YYMMDDhhmm>-<slug>")
    parser.add_argument("--root", default=None, help="root ruang kerja; default root git atau cwd")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    v = DocValidator(args.kind, args.ticketdir, Path(args.root) if args.root else find_root())
    ok = v.run_all()
    print(report_json(v.results, kind=args.kind, ticketdir=v.rel) if args.json
          else format_report(f"validate {v.name} ({args.kind})", v.results))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
