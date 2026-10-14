"""Langkah 26 — sinkron nataflow langsung di titik dokumen disetujui atau tuntas, bukan ditunda ke akhir rantai.

Tiap kasus mengunci bahwa langkah materai/approve sebuah dokumen taskdir diikuti prosedur `nataflow-sync.md` di
butir yang sama (atau butir sesudahnya) di skill pemiliknya, sehingga pemindahan atau penghapusan titik panggil
gagal di sini sebelum nataflow tertinggal dari disk.
"""
import re

import pytest

from conftest import BE_SKILLS, FE_SKILLS

BE_REF = "tech-lead/references/nataflow-sync.md"
FE_REF = "lead/references/nataflow-sync.md"
HEADING = re.compile(r"\n#{2,3} ")


def read(path):
    return path.read_text(encoding="utf-8")


def akhir_seksi(text, start):
    """Heading berikutnya sesudah `start`, melewati baris `###` di dalam blok kode (contoh blok Output)."""
    for m in HEADING.finditer(text, start):
        if text.count("```", start, m.start()) % 2 == 0:
            return m.start()
    return len(text)


def potong(text, heading, anchor, end=None):
    """Teks dari `anchor` (di dalam seksi `heading`) sampai `end` atau akhir seksi itu."""
    h = text.index(heading)
    seksi = text[h: akhir_seksi(text, h + len(heading))]
    i = seksi.index(anchor)
    j = seksi.find(end, i + len(anchor)) if end else -1
    return seksi[i: j if j != -1 else len(seksi)]


# (skill, heading seksi, langkah materai, batas butir, dokumen) — backend
BE_CASES = [
    ("task", "### Fase 5 — Penulisan & Penguncian Akar", "doc_seal.py root --taskdir", "\n6. ", "TASK"),
    ("analyst", "### Fase 4 — Gerbang Dokumen", "doc_seal.py approve --taskdir", "\n5. ", "BRD/PRD"),
    ("analyst", "### Fase 6", "doc_seal.py tick --taskdir", "\n1. ", "BRIEF"),
    ("architect", "### Fase 4 — Gerbang Verifikasi Penutup", "**Dispatch Code Reviewer**", "\n3. ", "REVIEW"),
    ("report", "### Fase 4 — Penulisan Laporan", "templates/report-template.md", "\n5. ", "REPORT"),
]

# frontend
FE_CASES = [
    ("task", "### Phase 4 — Out of Scope", "chain.py root --taskdir", None, "TASK"),
    ("ux-design", "### Phase 5 — Approval User", "chain.py approve --taskdir", "\n4. ", "FLOW"),
    ("ui-design", "### Phase 6 — Approval User", "chain.py approve --taskdir", "\n4. ", "UI"),
    ("contract", "### Phase 6 — Catat Draft & Approval User", "chain.py approve --taskdir", "\n4. ", "CONTRACT"),
    ("plan", "### Phase 5 — Approval User", "chain.py approve --taskdir", "\n4. ", "BRIEF"),
    ("architect", "### Phase 4 — Verifikasi Penutup", "validate_review.py --taskdir", None, "REVIEW"),
    ("report", "### Phase 4 — Penulisan, Validasi", "validate_report.py --taskdir", "\n5. ", "REPORT"),
]


@pytest.mark.regression("26 S1")
@pytest.mark.parametrize("skill,heading,anchor,end,doc", BE_CASES, ids=[c[4] for c in BE_CASES])
def test_backend_sinkron_sesudah_materai(skill, heading, anchor, end, doc):
    teks = potong(read(BE_SKILLS / skill / "SKILL.md"), heading, anchor, end)
    assert BE_REF in teks, f"{skill}: {doc} dimateraikan tanpa sinkron nataflow seketika"


@pytest.mark.regression("26 S6")
@pytest.mark.parametrize("skill,heading,anchor,end,doc", FE_CASES, ids=[c[4] for c in FE_CASES])
def test_frontend_sinkron_sesudah_materai(skill, heading, anchor, end, doc):
    teks = potong(read(FE_SKILLS / skill / "SKILL.md"), heading, anchor, end)
    assert FE_REF in teks, f"{skill}: {doc} disetujui/tuntas tanpa sinkron nataflow seketika"


@pytest.mark.regression("26 S1")
def test_backend_akar_disinkron_task_bukan_analyst():
    """Akar lane `DEFECT_RCA`/backfill `EXEC_BRIEF` tidak melewati `analyst`: sinkronnya milik `task`, dan
    `analyst` Fase 2 hanya membawa segmennya (tanpa sinkron kedua)."""
    fase2 = potong(read(BE_SKILLS / "analyst/SKILL.md"), "### Fase 2", "4. **Sinkron nataflow**", "\n### ")
    assert "TASK ROOT LOCKED" in fase2 and BE_REF not in fase2
    out = potong(read(BE_SKILLS / "task/SKILL.md"), "## Output [REQUIRED]", "### TASK ROOT LOCKED")
    assert "Nataflow <segmen>" in out and "**Nataflow**" in out


@pytest.mark.regression("26 S3")
@pytest.mark.parametrize("plugin_skills,ref", [(BE_SKILLS, BE_REF), (FE_SKILLS, FE_REF)], ids=["backend", "frontend"])
def test_architect_sinkron_penutup_hanya_tanpa_titik_review(plugin_skills, ref):
    """Penutup `architect` hanya menyinkron putaran yang tidak melewati titik review maupun laporan; tidak lagi
    satu sinkron di akhir yang menunda `REVIEW.md` sampai sesudah `REPORT.md`."""
    out = potong(read(plugin_skills / "architect/SKILL.md"), "## Output [REQUIRED]", "Sinkron nataflow")
    assert ref in out and "tanpa melewati satu pun dari keduanya" in out
    assert "satu kali per putaran" not in out


@pytest.mark.regression("26 S5")
def test_tech_lead_tidak_sinkron_ulang_pengirim_tersinkron():
    teks = read(BE_SKILLS / "tech-lead/references/gate-lifecycle.md")
    butir = potong(teks, "## 6.", "2a. **Sinkron nataflow**", "\n3. ")
    assert "jangan sinkron ulang" in butir
    assert "`architect`" in butir and "`READY_FOR_IMPLEMENTATION`" in butir


@pytest.mark.regression("26 S1")
@pytest.mark.parametrize("path,heading,titik", [
    (BE_SKILLS / BE_REF, "## Target per titik panggil", ["`task` Fase 5", "`analyst` Fase 4", "`analyst` Fase 6", "`architect` Fase 4",
                          "`report` Fase 4"]),
    (FE_SKILLS / FE_REF, "## Titik panggil", ["`task`", "`ux-design`, `ui-design`, `contract`, `plan`", "Phase 4 butir 4",
                          "`report`"]),
], ids=["backend", "frontend"])
def test_tabel_titik_panggil_lengkap(path, heading, titik):
    tabel = potong(read(path), heading, "|")
    hilang = [t for t in titik if t not in tabel]
    assert not hilang, f"titik panggil tidak tercatat di {path.name}: {hilang}"
