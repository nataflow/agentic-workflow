"""Langkah 20 — `analyst:notulen` memakai `code-scout` sebagai konteks klarifikasi (S1–S3).

Scout didispatch mode `KONTEKS` lewat `skills/notulen/dispatcher/scout.md`. Balikannya bahan bertanya ke pencatat,
bukan isi notulen, jadi `notulen.py check` menolak rujukan `path:baris` di seksi notulen (check 10). `## Catatan Asli`
dikecualikan karena dimateraikan dan berasal dari pencatat.
"""
import json

import pytest

from conftest import PLUGINS, load_module, run_script

ANALYST = PLUGINS / "analyst"
NOTULEN = ANALYST / "skills" / "notulen" / "scripts" / "notulen.py"
SKILL = ANALYST / "skills" / "notulen" / "SKILL.md"
DISPATCHER = ANALYST / "skills" / "notulen" / "dispatcher" / "scout.md"
AGENT = ANALYST / "agents" / "code-scout.md"
NOTES = "rapat sprint\n- budi: export csv minggu depan\n\nputus: rilis jumat\n"
FILLED = {
    "## Ringkasan\n\n_(belum ditulis)_": "## Ringkasan\n\nTim menyepakati rilis Jumat dan ekspor CSV untuk Finance.",
    "## Peserta\n\n_(belum ditulis)_": "## Peserta\n\n- Budi (PM)\n- Rina (Finance)",
    "## Agenda\n\n_(belum ditulis)_": "## Agenda\n\n1. Status sprint\n2. Ekspor laporan",
    "## Pembahasan\n\n_(belum ditulis)_": "## Pembahasan\n\n- Finance butuh ekspor CSV untuk rekap bulanan.",
    "## Keputusan\n\n- Tidak ada.": "## Keputusan\n\n- **D-1**: Rilis dilakukan Jumat.",
    "| ID | Tindakan | PIC | Tenggat |\n|---|---|---|---|\n":
        "| ID | Tindakan | PIC | Tenggat |\n|---|---|---|---|\n| A-1 | Siapkan ekspor CSV | Budi | 2026-10-09 |\n",
}
lib = load_module(ANALYST / "skills" / "_common" / "analyst_lib.py", "analyst_lib_20s")


def new(root, notes=NOTES):
    r = run_script(NOTULEN, "new", "--slug", "sprint-review", "--title", "Sprint review", "--date", "2026-10-02",
                   "--notes", "-", cwd=root, stdin=notes)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout.split("NEW PASS: ", 1)[1].split(" ·", 1)[0]


def edit(root, rel, old, new_text):
    p = root / rel / "NOTULEN.md"
    text = p.read_text(encoding="utf-8")
    assert old in text, old
    p.write_text(text.replace(old, new_text, 1), encoding="utf-8")


def filled(root, notes=NOTES):
    rel = new(root, notes)
    for old, new_text in FILLED.items():
        edit(root, rel, old, new_text)
    return rel


def failed(root, rel, *extra):
    r = run_script(NOTULEN, "check", "--notulendir", rel, "--json", *extra, cwd=root)
    return r.returncode, {c["id"]: c["summary"] for c in json.loads(r.stdout)["checks"] if c["status"] == "FAIL"}


@pytest.fixture
def plain(make_repo):
    return make_repo(name="plain", git_init=False)


# --- S1: pagar `path:baris` ---------------------------------------------------------------------

@pytest.mark.regression("20 S1")
def test_s1_notulen_tanpa_rujukan_kode_lolos(plain):
    rel = filled(plain)
    assert failed(plain, rel) == (0, {})


@pytest.mark.regression("20 S1")
@pytest.mark.parametrize("old,new_text", [
    ("- Finance butuh ekspor CSV untuk rekap bulanan.",
     "- Finance butuh ekspor CSV di layar laporan (`src/routes/report/+page.svelte:12`)."),
    ("| Siapkan ekspor CSV |", "| Siapkan ekspor CSV di `internal/report/export.go:40-60` |"),
    ("- **D-1**: Rilis dilakukan Jumat.", "- **D-1**: Rilis dilakukan Jumat, termasuk `web/app.ts:7`."),
])
def test_s1_path_baris_di_seksi_notulen_gagal(plain, old, new_text):
    rel = filled(plain)
    edit(plain, rel, old, new_text)
    code, fails = failed(plain, rel)
    assert code == 1 and set(fails) == {10}, fails
    assert "path:baris" in fails[10]


@pytest.mark.regression("20 S1")
def test_s1_jam_dalam_backtick_bukan_rujukan_berkas(plain):
    rel = filled(plain)
    edit(plain, rel, "- Finance butuh", "- Rapat ditutup `17:00`. Finance butuh")
    assert failed(plain, rel) == (0, {})


@pytest.mark.regression("20 S1")
def test_s1_catatan_asli_dikecualikan(plain):
    rel = filled(plain, notes="rapat bug\n- budi: error di `internal/report/export.go:42`\n")
    assert failed(plain, rel) == (0, {})


@pytest.mark.regression("20 S1")
def test_s1_final_menolak_rujukan_kode(plain):
    rel = filled(plain)
    edit(plain, rel, "- Finance butuh", "- Finance (`src/finance/page.ts:3`) butuh")
    r = run_script(NOTULEN, "final", "--notulendir", rel, "--answer", "Final", cwd=plain)
    assert r.returncode == 1 and "FINAL FAIL" in r.stdout
    fm, _ = lib.split_frontmatter((plain / rel / "NOTULEN.md").read_text(encoding="utf-8"))
    assert fm["status"] == "DRAFT"


# --- S2: dispatcher dan agent -------------------------------------------------------------------

@pytest.mark.regression("20 S2")
def test_s2_dispatcher_notulen_mode_konteks_merujuk_agent():
    text = DISPATCHER.read_text(encoding="utf-8")
    assert "agents/code-scout.md" in text
    assert "- Mode: `KONTEKS`" in text and "{mode}" not in text
    for slot in ("{root}", "{batas}", "{pertanyaan}"):
        assert slot in text
    assert "Plafon 2 dispatch per notulen" in text


@pytest.mark.regression("20 S2")
def test_s2_agent_mengenal_notulen():
    fm, body = lib.split_frontmatter(AGENT.read_text(encoding="utf-8"))
    assert "analyst:notulen" in fm["description"]
    assert [t.strip() for t in fm["tools"].split(",")] == ["Read", "Grep", "Glob"]
    assert "notulen rapat" in body


# --- S3: skill ----------------------------------------------------------------------------------

@pytest.mark.regression("20 S3")
def test_s3_skill_merujuk_dispatcher_dan_kode_sebagai_konteks():
    text = SKILL.read_text(encoding="utf-8")
    assert "`dispatcher/scout.md`" in text and "analyst:code-scout" in text
    assert "KODE SEBAGAI KONTEKS" in text
    assert "dilarang membaca kode repo, menulis" not in text
