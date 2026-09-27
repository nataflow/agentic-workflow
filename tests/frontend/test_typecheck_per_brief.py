"""L4.10 — satu resolver `typecheck-per-brief`: profil menang, fallback adapter, lalu `tidak`."""
import importlib.util
import sys

import pytest

from conftest import FE_MINOR_TD, FE_SKILLS, fe_run

# Dimuat per path, bukan lewat sys.path: backend punya modul bernama sama
# (`precondition_lib`) yang mungkin sudah terdaftar di sys.modules sesi pytest ini.
_spec = importlib.util.spec_from_file_location("fe_precondition_lib", FE_SKILLS / "_common/precondition_lib.py")
_lib = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _lib
_spec.loader.exec_module(_lib)
typecheck_per_brief = _lib.typecheck_per_brief


@pytest.mark.parametrize("commands, stack, expected", [
    ("- `typecheck-per-brief`: `ya — svelte-check 8 dtk`\n", "sveltekit", ("ya", "profil")),
    ("| Perintah | Status |\n", "react-vite", ("ya", "adapter")),
    ("- `typecheck-per-brief`: `tidak — tsc 90 dtk`\n", "react-vite", ("tidak", "profil")),
    ("", "sveltekit", ("tidak", "adapter")),
    ("", "stack-asing", ("tidak", "bawaan")),
])
def test_resolver(tmp_path, commands, stack, expected):
    (tmp_path / "commands.md").write_text(commands, encoding="utf-8")
    assert typecheck_per_brief(tmp_path, stack) == expected


def test_resolver_tanpa_commands_md(tmp_path):
    assert typecheck_per_brief(tmp_path, "react-vite") == ("ya", "adapter")


def test_architect_menyerahkan_nilai_profil(fe_minor_chain):
    out = fe_run(fe_minor_chain, "architect/scripts/check_preconditions.py", "--taskdir", FE_MINOR_TD).out
    assert "typecheck_per_brief=ya (profil)" in out
    cmds = fe_minor_chain / ".claude/profile/commands.md"
    cmds.write_text(cmds.read_text(encoding="utf-8").replace("`ya`", "`tidak — tsc 90 dtk`"), encoding="utf-8")
    out = fe_run(fe_minor_chain, "architect/scripts/check_preconditions.py", "--taskdir", FE_MINOR_TD).out
    assert "typecheck_per_brief=tidak (profil)" in out
