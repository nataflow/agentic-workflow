"""Jangkar format profil backend/frontend yang dibaca plugin fullstack (Langkah 21 F9).

`workspace.py peta` mem-parse `domain-map.md`/`surface-map.md` backend dan mengutip `structure.md`/`surface-map.md`
frontend; `repo-scout` membaca baris dan kolom yang sama. Bila `backend:profile` atau `frontend:profile` mengganti
jangkar ini, test di sini gagal dan `peta` serta dispatcher fullstack ikut diperbarui.
"""
import re

import pytest

from conftest import PLUGINS, load_module
from fullstack_helpers import WORKSPACE

pytestmark = pytest.mark.regression("21 F9")

BE_PROFILE = PLUGINS / "backend" / "skills" / "profile"
FE_PROFILE = PLUGINS / "frontend" / "skills" / "profile"


def _ws():
    return load_module(WORKSPACE, "_fs_workspace_anchor")


def _read(path):
    return path.read_text(encoding="utf-8")


def _example(text, heading):
    """Blok ```markdown pertama sesudah judul `heading`."""
    start = text.index(heading)
    m = re.search(r"```markdown\n(.*?)\n```", text[start:], re.S)
    assert m, heading
    return m.group(1)


def test_be_permukaan_kanonik():
    text = _read(BE_PROFILE / "references" / "scan-guide.md")
    section = text[text.index("## 14. Surface Map"):]
    canon = section[section.index("permukaan kanonik"):].split("\n")[1]
    for key in ("`http`", "`external`", "`config`"):
        assert key in canon, key
    assert "`<permukaan>: <path/glob> · <penanda pengenal> · <catatan satu frasa>`" in section


def test_be_format_domain_map():
    text = _read(BE_PROFILE / "references" / "convention-scan.md")
    section = text[text.index("## 15. Domain Map"):]
    for fact in ("**path/glob modul**", "**permukaan aktif**", "**entry `<file>#<simbol>`**"):
        assert fact in section, fact
    assert "| `domain-map.md` | modul bisnis: path · permukaan aktif · entry `<file>#<simbol>` |" in _read(
        BE_PROFILE / "SKILL.md")


def test_be_contoh_template_terbaca_parser():
    ws = _ws()
    text = _read(BE_PROFILE / "templates" / "profile-template.md")
    rows, bad = ws.parse_domain_map(_example(text, "### `.claude/profile/backenddev/domain-map.md`"))
    assert rows and bad == []
    keys, _external = ws.parse_be_surface(_example(text, "### `.claude/profile/backenddev/surface-map.md`"))
    assert "http" in keys
    assert "<permukaan>: <path/glob tempatnya hidup> · <penanda pengenal> · <catatan satu frasa>" in text


def test_fe_butir_structure():
    ws = _ws()
    text = _read(FE_PROFILE / "templates" / "profile-template.md")
    section = text[text.index("## 3. `.claude/profile/frontenddev/structure.md`"):]
    section = section[:section.index("\n## 4.")]
    assert ws.quote_bullet(section, "Features Path")
    assert ws.quote_bullet(section, "Route Definitions")


def test_fe_baris_surface_map():
    ws = _ws()
    text = _read(FE_PROFILE / "templates" / "profile-template.md")
    section = text[text.index("## 4. `.claude/profile/frontenddev/surface-map.md`"):]
    names = ws.parse_fe_surface(section[:section.index("\n## 5.")])
    for row in ("Routing & Navigation", "Data Fetching & Cache", "Shared HTTP Client", "Framework Boundary"):
        assert row in names, (row, names)


def test_fe_baris_layer_adoption():
    ws = _ws()
    text = _read(FE_PROFILE / "templates" / "profile-template.md")
    section = text[text.index("## 7. `.claude/profile/frontenddev/layer-adoption.md`"):]
    names = ws.parse_fe_surface(section[:section.index("\n## 8.")])
    for row in ("HTTP Service Layer", "DTO Isolation"):
        assert row in names, (row, names)
    structure = text[text.index("## 3. `.claude/profile/frontenddev/structure.md`"):]
    assert "`dto/`" in structure and "`services/`" in structure
