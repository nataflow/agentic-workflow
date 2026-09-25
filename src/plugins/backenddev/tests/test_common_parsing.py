"""Primitif parsing bersama `skills/_common/precondition_lib.py` backenddev (Langkah 5, bagian A)."""
import importlib.util
import json
import os
import sys

import pytest

from conftest import PLUGINS, be_profile, fe_profile, git, write_files

_spec = importlib.util.spec_from_file_location(
    "bd_precondition_lib", PLUGINS / "backenddev/skills/_common/precondition_lib.py")
lib = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = lib
_spec.loader.exec_module(lib)

TD = "backenddev/docs/2601011200-ok"


# -- frontmatter ----------------------------------------------------------------------------

def test_split_frontmatter_bom_crlf():
    raw = b"\xef\xbb\xbf---\r\nstatus: APPROVED\r\n---\r\n# x".decode("utf-8")
    fields, body = lib.split_frontmatter(raw)
    assert fields == {"status": "APPROVED"} and body == "# x"


def test_only_first_block():
    fields, _ = lib.split_frontmatter("---\nstatus: DRAFT\n---\n# x\n---\nstatus: APPROVED\n---\n")
    assert fields["status"] == "DRAFT"


def test_quoted_value_and_trailing_comment():
    fields, _ = lib.split_frontmatter('---\nstatus: "READY"  \nchain: prd_brief # dari analyst\n---\n')
    assert fields == {"status": "READY", "chain": "prd_brief"}


def test_duplicate_key_rejected():
    with pytest.raises(lib.FrontmatterError, match="lebih dari sekali"):
        lib.split_frontmatter("---\nstatus: DRAFT\nstatus: APPROVED\n---\n")


def test_missing_open_or_close_fence():
    with pytest.raises(lib.FrontmatterError) as a:
        lib.split_frontmatter("# x\nstatus: APPROVED\n")
    with pytest.raises(lib.FrontmatterError) as b:
        lib.split_frontmatter("---\nstatus: APPROVED\n# x\n")
    assert str(a.value) != str(b.value)


@pytest.mark.parametrize("text, expect", [
    ("---\nstatus: APPROVED\n---\n# PRD\n- Order dengan status: DRAFT ditolak.\n", ("APPROVED", "")),
    ("---\nstatus: REVIEW\n---\n# BRD\n- Refund status: APPROVED hanya oleh supervisor.\n", (None, "REVIEW")),
    ("---\ntitle: R\n---\n# BRD\nRefund status: APPROVED\n", (None, "tanpa kunci `status`")),
    ("---\nstatus: approved\n---\n", (None, "`approved`")),
])
def test_doc_status_body_sentence_ignored(tmp_path, text, expect):
    p = tmp_path / "BRD.md"
    p.write_text(text, encoding="utf-8")
    status, why = lib.doc_status(p, ("DRAFT", "APPROVED"))
    assert status == expect[0]
    assert expect[1] in why


def test_count_h1_pagar_bersarang():
    text = "---\na: b\n---\n# Judul\n````md\n```\n# bukan\n```\n````\n~~~\n# juga bukan\n~~~\n"
    assert lib.count_h1(text) == 1


def test_count_h1_bom_tanpa_frontmatter():
    assert lib.count_h1("﻿# Refund\n\n## Success Criteria\n") == 1


# -- enum & chain ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["PRD_BRIEF", "prd_brief", '"PRD_BRIEF"', "PRD_BRIEF # x"])
def test_parse_chain_normalisasi(raw):
    fields, _ = lib.split_frontmatter(f"---\nchain: {raw}\n---\n")
    assert lib.parse_chain(fields["chain"]) == ("PRD_BRIEF", "")


@pytest.mark.parametrize("raw", ["—", "-", "", None])
def test_parse_chain_kosong_tanpa_galat(raw):
    assert lib.parse_chain(raw) == (None, "")


@pytest.mark.parametrize("raw", ["PRD_CONVERSION", "PRD-BRIEF"])
def test_parse_chain_menolak_nilai_lane(raw):
    value, err = lib.parse_chain(raw)
    assert value is None and f"chain '{raw}' tidak sah" in err


def test_declared_chain_frontmatter_rusak(tmp_path):
    (tmp_path / "TASK.md").write_text("---\nchain: BRIEF\nchain: PRD_BRIEF\n---\n", encoding="utf-8")
    value, err = lib.declared_chain(tmp_path)
    assert value is None and "lebih dari sekali" in err


def test_declared_chain_tanpa_task(tmp_path):
    assert lib.declared_chain(tmp_path) == (None, "")


# -- taskdir --------------------------------------------------------------------------------

@pytest.fixture
def td_repo(make_repo, tmp_path):
    root = make_repo({f"{TD}/.keep": "", "src/a.go": "package a\n",
                      "backenddev/docs/2601011200-berkas": "x\n"})
    link = tmp_path / "repo.link"
    link.symlink_to(root)
    return root, link


@pytest.mark.parametrize("arg, ok", [
    ("src", False), ("/tmp", False), (".", False),
    ("backenddev/docs/2601011200-belum-ada", False), ("backenddev/docs/2601011200-berkas", False),
    ("x/backenddev/docs/2601011200-ok", False), ("LINK", True), (f"./{TD}/", True), (TD, True),
])
def test_check_taskdir_matrix(td_repo, arg, ok):
    root, link = td_repo
    if arg == "LINK":
        arg = f"{link}/{TD}"
    v = lib.check_taskdir(root, arg)
    assert v.ok is ok, v.summary
    if ok:
        assert v.rel == TD


def test_must_exist_false(td_repo):
    root, _ = td_repo
    assert lib.check_taskdir(root, "backenddev/docs/2601011200-belum-ada", must_exist=False).ok


def test_outside_root(td_repo):
    root, _ = td_repo
    assert "di luar root repo" in lib.check_taskdir(root, "/tmp").summary


def test_taskdir_berkas_dan_pola(td_repo):
    root, _ = td_repo
    assert "bukan direktori" in lib.check_taskdir(root, "backenddev/docs/2601011200-berkas").summary
    assert "pola kanonik" in lib.check_taskdir(root, "src").summary


# -- git ------------------------------------------------------------------------------------

def test_dirty_paths_unicode_dan_spasi(make_repo):
    root = make_repo({"a.txt": "a\n"})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    write_files(root, {f"{TD}/café.md": "x\n", f"{TD}/catatan rapat.md": "x\n"})
    assert sorted(lib.dirty_paths(root)) == [f"{TD}/café.md", f"{TD}/catatan rapat.md"]


def test_dirty_paths_rename_mengambil_tujuan(make_repo):
    root = make_repo({"a": "isi\n"})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    git(root, "mv", "a", "b")
    assert lib.dirty_paths(root) == ["b"]


def test_dirty_paths_nama_berpanah(make_repo):
    root = make_repo({"x": "x\n"})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    write_files(root, {"src/a -> b.go": "x\n"})
    assert lib.dirty_paths(root) == ["src/a -> b.go"]


def test_scratch_hanya_laci_taskdir(make_repo):
    root = make_repo({"x": "x\n"})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    write_files(root, {f"{TD}/.explore/a.md": "x\n", "backenddev/docs/.explore/b.md": "x\n",
                       "internal/.explore/q.go": "x\n"})
    assert lib.dirty_paths(root) == ["internal/.explore/q.go"]
    assert len(lib.dirty_paths(root, exclude_scratch=False)) == 3


def test_dirty_paths_bukan_repo(make_repo):
    with pytest.raises(lib.GitError):
        lib.dirty_paths(make_repo(git_init=False))


def test_find_repo_root_dari_subdir(make_repo):
    root = make_repo({f"{TD}/.keep": ""})
    assert lib.find_repo_root(root / "backenddev" / "docs") == root.resolve()


def test_find_repo_root_bukan_repo(make_repo):
    plain = make_repo(git_init=False)
    assert lib.find_repo_root(plain) == plain.resolve()


def test_is_under_per_segmen():
    assert lib.is_under("src/refund/a.go", "src/refund/")
    assert not lib.is_under("src/refundhistory/a.go", "src/refund")
    assert not lib.is_under("src/a.go", "")


# -- profil & berkas plugin -----------------------------------------------------------------

def test_load_profile_index_tujuh_kunci(make_repo):
    root = make_repo()
    d = be_profile(root, "go")
    data = json.loads((d / "index.json").read_text())
    del data["branch_convention"]
    (d / "index.json").write_text(json.dumps(data))
    prof = lib.load_profile_index(root)
    assert prof.data is None and prof.kind == "incomplete" and "branch_convention" in prof.error


def test_load_profile_index_subset(make_repo):
    root = make_repo()
    d = be_profile(root, "go")
    (d / "index.json").write_text(json.dumps({"plugin": "backenddev", "stack": "go"}))
    assert lib.load_profile_index(root, required=("stack",)).data["stack"] == "go"


def test_load_profile_index_bom_dan_milik_lain(make_repo):
    root = make_repo()
    d = be_profile(root, "go")
    (d / "index.json").write_text("﻿" + (d / "index.json").read_text(), encoding="utf-8")
    assert lib.load_profile_index(root).ok
    other = make_repo(name="other")
    fe_profile(other, "react-vite", legacy=True)
    assert lib.load_profile_index(other).kind == "missing"


def test_load_profile_index_legacy_note(make_repo):
    root = make_repo()
    be_profile(root, "go", legacy=True)
    prof = lib.load_profile_index(root)
    assert prof.ok and "MIGRATE" in prof.note


@pytest.mark.xfail(strict=True, reason="L5.5: tech-lead masih memakai kandidat path ~/.gemini")
def test_find_agent_tanpa_fallback_home(tmp_path, make_repo):
    """Reproduksi L5.5 #2: salinan `~/.gemini` tidak menutupi agent yang hilang dari plugin."""
    import shutil
    plug = tmp_path / "plug"
    shutil.copytree(PLUGINS / "backenddev", plug, ignore=shutil.ignore_patterns("__pycache__", "tests"))
    (plug / "agents" / "code-explorer.md").unlink()
    home = tmp_path / "home"
    write_files(home, {".gemini/config/plugins/backenddev/agents/code-explorer.md": "# lama\n",
                       ".claude/plugins/backenddev/agents/code-explorer.md": "# lama\n"})
    repo = make_repo()
    from conftest import run_script
    env_home = os.environ.get("HOME")
    for h in (tmp_path / "emptyhome", home):
        os.environ["HOME"] = str(h)
        try:
            proc = run_script(plug / "skills/tech-lead/scripts/check_preconditions.py",
                              "--root", str(repo), "--json")
        finally:
            os.environ["HOME"] = env_home
        checks = {c["id"]: c for c in json.loads(proc.stdout)["checks"]}
        assert checks[6]["status"] == "FAIL", checks[6]


# -- keluaran -------------------------------------------------------------------------------

def test_format_text_banner_dan_header():
    res = [{"id": 1, "name": "A", "status": "PASS", "summary": "ok", "action": ""},
           {"id": 2, "name": "B", "status": "FAIL", "summary": "no", "action": "perbaiki"}]
    out = lib.format_text("x", res, banner=lib.freshness_banner(("BASI", "3 commit"))).splitlines()
    assert out[0].startswith("[TERDEGRADASI]") and "(1/2 passed)" in out[1]
    assert out[-1] == "    * Tindakan: perbaiki"


def test_format_text_titik_masuk():
    res = [{"id": 1, "name": "A", "status": "PASS", "summary": "ok", "action": "mulai di Fase 2"}]
    assert "    * Titik masuk: mulai di Fase 2" in lib.format_text("x", res, entry_label="Titik masuk")
    assert "Fase 2" not in lib.format_text("x", res)


def test_to_json_urutan_kunci():
    out = json.loads(lib.to_json("/r", [], taskdir="x"))
    assert list(out) == ["status", "passed_count", "total_count", "root", "taskdir", "checks"]
