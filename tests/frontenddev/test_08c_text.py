"""08c item teks — C1 (Not Found di Format laporan), C9 (dispatch ulang reviewer)."""
import re

import pytest

from conftest import PLUGINS

FE = PLUGINS / "frontenddev"
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
