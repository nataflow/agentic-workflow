"""B3, B10 — status brief dan slot dispatcher lewat skrip (bukan grep/sed `.md` di Bash), peta skrip `«nama.py»`
di SKILL.md (references tidak disubstitusi), dan perintah lengkap di titik pakai."""
import importlib.util
import json
import re

import pytest

from conftest import BE_SKILLS, TD, brief, land, run_script

BRIEF_STATUS = BE_SKILLS / "_common/brief_status.py"
RENDER = BE_SKILLS / "_common/render_prompt.py"
DISPATCHERS = sorted(BE_SKILLS.glob("*/dispatcher/*.md"))
PETA_SKILLS = ("tech-lead", "architect", "plan", "analyst")
GUARD_SKILLS = ("tech-lead", "architect", "plan")


def _status(repo, *extra):
    proc = run_script(BRIEF_STATUS, "--taskdir", TD, *extra, cwd=repo)
    return proc


# ------------------------------------------------------------------ B3 — brief_status.py --taskdir


@pytest.mark.regression("B3")
def test_tabel_status_brief_dari_disk_dan_git(chain_repo):
    b1 = brief(chain_repo, "01", "repo", "READY", sidik_kontrak="a" * 64)
    land(chain_repo, b1)
    brief(chain_repo, "02", "endpoint", "BLOCKED")
    brief(chain_repo, "03", "endpoint-v2", "READY", supersedes="brief-02")
    proc = _status(chain_repo, "--json")
    out = json.loads(proc.stdout)
    assert proc.returncode == 0 and out["status"] == "PASS", out
    rows = {r["nn"]: r for r in out["brief"]}
    assert rows["01"]["status"] == "DONE" and rows["01"]["commit"] and rows["01"]["sidik"] == "a" * 12
    assert rows["01"]["risk"] == "MINOR"
    assert rows["03"]["tautan"] == "supersedes brief-02" and rows["03"]["commit"] == ""
    assert out["halt"] == "tidak ada" and out["review"]["segar"] is False
    assert any("supersedes brief-02" in p for p in out["tautan_bermasalah"])


@pytest.mark.regression("B3")
def test_teks_tabel_dan_halt_aktif(chain_repo):
    brief(chain_repo, "01", "repo", "DONE")
    (chain_repo / TD / "HALT.md").write_text("---\nbrief: brief-01-repo.md\nverdict: SCOPE\nsha: abc1234\n---\n",
                                             encoding="utf-8")
    proc = _status(chain_repo)
    assert proc.returncode == 0
    head, *rest = proc.stdout.splitlines()
    assert head.startswith(f"BRIEF_STATUS {TD}: 1 brief (DONE 1)") and "HALT AKTIF verdict SCOPE" in head
    assert rest[0].startswith("| NN | Berkas | Status |") and "| 01 | brief-01-repo.md | DONE |" in rest[2]


@pytest.mark.regression("B3")
def test_taskdir_tak_sah_fail_json(chain_repo):
    proc = run_script(BRIEF_STATUS, "--taskdir", "backenddev/docs/x", "--json", cwd=chain_repo)
    assert proc.returncode == 1 and json.loads(proc.stdout)["status"] == "FAIL"


# ------------------------------------------------------------------ B3 — render_prompt.py --list-slots


def _slot_table(path):
    spec = importlib.util.spec_from_file_location("be_render_prompt_b3", RENDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.slot_table(path.read_text(encoding="utf-8"))


@pytest.mark.regression("B3")
@pytest.mark.parametrize("template", DISPATCHERS, ids=lambda p: p.relative_to(BE_SKILLS).as_posix())
def test_list_slots_sama_dengan_tabel_slot_hidrasi(tmp_path, template):
    proc = run_script(RENDER, "--template", str(template), "--list-slots", "--json", cwd=tmp_path)
    out = json.loads(proc.stdout)
    assert proc.returncode == 0 and out["status"] == "PASS"
    assert {r["nama"]: r["wajib"] for r in out["slot"]} == _slot_table(template)
    assert all(r["sumber"] for r in out["slot"])
    assert not list(tmp_path.rglob("*.md")), "list-slots tidak menulis apa pun"


@pytest.mark.regression("B3")
def test_list_slots_teks_dan_out_wajib_tanpanya(tmp_path):
    tpl = BE_SKILLS / "architect/dispatcher/implementor.md"
    proc = run_script(RENDER, "--template", str(tpl), "--list-slots", cwd=tmp_path)
    assert proc.returncode == 0 and proc.stdout.startswith("SLOT implementor.md: 4 slot (4 wajib)")
    assert "- {brief_path} WAJIB — " in proc.stdout
    proc = run_script(RENDER, "--template", str(tpl), "--json", cwd=tmp_path)
    assert proc.returncode == 2 and "--out" in json.loads(proc.stdout)["reason"]


# ------------------------------------------------------------------ B3 — guardrail baca `.md`


@pytest.mark.regression("B3")
@pytest.mark.parametrize("skill", GUARD_SKILLS)
def test_guardrail_baca_md_lewat_read(skill):
    text = (BE_SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    line = next((l for l in text.splitlines() if "(B3" in l and l.startswith("- **")), "")
    assert line, skill
    assert "`Read`" in line and "brief_status.py" in line and "grep" in line


# ------------------------------------------------------------------ B10 — peta skrip dan perintah lengkap


def _peta_line(skill):
    text = (BE_SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    return next((l for l in text.splitlines() if "B10" in l and "«nama.py»" in l), "")


@pytest.mark.regression("B10")
@pytest.mark.parametrize("skill", PETA_SKILLS)
def test_skill_memetakan_rujukan_guillemet_ke_path_tersubstitusi(skill):
    line = _peta_line(skill)
    assert "${CLAUDE_PLUGIN_ROOT}/skills/_common/<nama>.py" in line and "--help" in line, skill


@pytest.mark.regression("B10")
def test_tiap_rujukan_guillemet_berpeta_dan_skripnya_ada():
    for skill_dir in sorted(p for p in BE_SKILLS.iterdir() if p.is_dir()):
        names = set()
        for md in skill_dir.rglob("*.md"):
            names |= set(re.findall(r"«([a-z_]+\.py)»", md.read_text(encoding="utf-8")))
        if not names:
            continue
        assert skill_dir.name in PETA_SKILLS, f"{skill_dir.name} memakai «…» tanpa peta skrip: {sorted(names)}"
        for name in names - {"nama.py"}:   # placeholder di baris peta itu sendiri
            assert (BE_SKILLS / "_common" / name).is_file(), (skill_dir.name, name)


@pytest.mark.regression("B10")
def test_references_tidak_lagi_merantai_awalan():
    for md in BE_SKILLS.glob("*/references/*.md"):
        text = md.read_text(encoding="utf-8")
        assert "awalan sama dengan `«" not in text and "awalan yang sama dengan `«" not in text, md.name
        assert "awalan yang sama dengan path skrip prasyarat" not in text, md.name


@pytest.mark.regression("B10")
def test_dispatcher_menunjuk_perintah_lengkap_dan_list_slots():
    for tpl in DISPATCHERS:
        text = tpl.read_text(encoding="utf-8")
        assert "--list-slots" in text and "awalan path yang sama" not in text, tpl.name


@pytest.mark.regression("B10")
@pytest.mark.parametrize("skill,template", [
    ("architect", "architect/dispatcher/implementor.md"),
    ("architect", "architect/dispatcher/reviewer.md"),
    ("plan", "plan/dispatcher/explorer.md"),
    ("plan", "plan/dispatcher/reviewer.md"),
    ("tech-lead", "tech-lead/dispatcher/explorer.md"),
])
def test_perintah_render_lengkap_di_skill(skill, template):
    text = (BE_SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    cmd = f"python3 ${{CLAUDE_PLUGIN_ROOT}}/skills/_common/render_prompt.py --template ${{CLAUDE_PLUGIN_ROOT}}/skills/{template}"
    assert cmd in text, (skill, template)
    wajib = [n for n, w in _slot_table(BE_SKILLS / template).items() if w]
    line = text[text.index(cmd):].split("`", 1)[0]
    for slot in wajib:
        assert f"--slot {slot}=" in line, (template, slot)
