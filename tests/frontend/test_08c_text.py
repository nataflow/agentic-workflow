"""08c item teks — C1 (Not Found di Format laporan), C7 (nama 9 dimensi), C8 (adapter ramping), C9 (dispatch ulang reviewer)."""
import re
from collections import Counter

import pytest

from conftest import FE_SKILLS, PLUGINS, load_module

FE = PLUGINS / "frontend"
EXPLORERS = sorted((FE / "skills").glob("*/dispatcher/explorer.md"))


def read(path):
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", EXPLORERS, ids=lambda p: p.parts[-3])
def test_c1_seksi_balikan_ada_di_format_laporan(path):
    text = read(path)
    handled = set(re.findall(r"^\| `(### [^`]+)`", text, re.M))
    assert handled, "tabel Penanganan Balikan tanpa seksi"
    # heading seksi Format laporan hidup di dalam blok prompt (baris `### <Seksi>` utuh)
    missing = [h for h in handled if not re.search(rf"^\s*{re.escape(h)}\s*$", text, re.M)]
    assert not missing, missing


def test_c1_code_explorer_mengizinkan_not_found():
    assert "`### Not Found` satu-satunya seksi yang boleh ditambahkan" in read(FE / "agents" / "code-explorer.md")


def test_c9_iron_law_architect_tidak_melarang_dispatch_ulang_reviewer():
    text = read(FE / "skills" / "architect" / "SKILL.md")
    assert not re.search(r"code-reviewer[^\n]*tepat sekali", text)
    assert "maksimal satu kali" in text


# --- C7 ---------------------------------------------------------------------------------------

CONTRACT = FE / "skills" / "profile" / "stacks" / "_CONTRACT.md"
ADAPTERS = sorted(p for p in CONTRACT.parent.glob("*.md") if p.name != "_CONTRACT.md")


def canonical():
    body = read(CONTRACT).split("## Sembilan dimensi review", 1)[1].split("\n---", 1)[0]
    rows = re.findall(r"^\| (\d) \| `([a-z-]+)` \| ([^|]+?) \|", body, re.M)
    assert len(rows) == 9
    return [(slug, name) for _, slug, name in rows]


def table_names(path, heading="## 9 Dimensi"):
    names = []
    for block in read(path).split(heading)[1:]:
        names.append(re.findall(r"^\| [1-9] \| ([^|]+?) \| ", block, re.M)[:9])
    return names


def test_c7_nama_kanonik_dipakai_template_validator_reviewer():
    names = [n for _, n in canonical()]
    for tmpl in (FE_SKILLS / "architect/templates/review-template.md", FE_SKILLS / "review/templates/audit-template.md"):
        tables = [t for t in table_names(tmpl) if len(t) == 9]   # tabel penuh; potongan contoh diabaikan
        assert tables and all(t == names for t in tables), (tmpl.name, tables)
    validate_review = load_module(FE_SKILLS / "architect/scripts/validate_review.py", "vr_08c_c7")
    assert validate_review.DIMENSIONS == names
    reviewer = read(FE / "agents" / "code-reviewer.md")
    bold = re.findall(r"^[1-9]\. \*\*([^*]+)\*\* —", reviewer, re.M)   # daftar Fase 2
    assert bold[bold.index(names[0]):][:9] == names
    catalog = read(FE_SKILLS / "review/references/nine-dimensions-catalog.md")
    assert re.findall(r"^## \d\. Dimension \d: (.+) \(`([a-z-]+)`\)$", catalog, re.M) == \
        [(n, s) for s, n in canonical()]


def test_c7_nama_lama_hilang():
    old = ("Platform Semantics", "Test Quality & Coverage", "API Layer Zero", "Data Flow, Typing",
           "Initial, Loading", "Ready, dan Mutating", "touch target <44dp", "DTO Integrity)")
    hits = [(p.relative_to(FE).as_posix(), o) for p in FE.rglob("*.md") for o in old if o in read(p)]
    assert not hits


# --- C8 ---------------------------------------------------------------------------------------

def checklist(path):
    body = read(path).split("## Review checklist", 1)[1].split("\n## ", 1)[0]
    items = re.findall(r"^- \*\*(.+?)\*\*", body, re.M)
    return items, re.findall(r"^#### `([a-z-]+)`", body, re.M)


@pytest.mark.parametrize("path", ADAPTERS, ids=lambda p: p.stem)
def test_c8_adapter_dalam_batas_dan_ambang(path):
    assert len(read(path)) <= 14000
    items, dims = checklist(path)
    assert len(items) >= 12 and len(dims) >= 5
    assert set(dims) <= {s for s, _ in canonical()}


def test_c8_tanpa_butir_umum_di_tiga_adapter_atau_lebih():
    norm = lambda t: re.sub(r"[`\s]+", " ", t.lower()).strip()
    counts = Counter(norm(i) for p in ADAPTERS for i in set(checklist(p)[0]))
    assert not [t for t, n in counts.items() if n >= 3]
