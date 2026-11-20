"""32 T1 — `render_prompt.py`: dispatcher dirender ke laci `.explore/prompt/`, main loop tidak memuat badan template."""
import json
import re

import pytest

from conftest import BE_SKILLS, PLUGINS, run_script

SCRIPT = BE_SKILLS / "_common/render_prompt.py"
DISPATCHERS = sorted(p.relative_to(BE_SKILLS).as_posix() for p in BE_SKILLS.glob("*/dispatcher/*.md"))
TD = "backenddev/docs/2611110712-x"


def _render(tmp_path, template, *slots, out=f"{TD}/.explore/prompt/p.md", extra=()):
    args = ["--template", str(BE_SKILLS / template), "--out", out, "--root", str(tmp_path), "--json", *extra]
    for s in slots:
        args += ["--slot", s]
    proc = run_script(SCRIPT, *args, cwd=tmp_path)
    return proc.returncode, json.loads(proc.stdout)


def _required(template):
    import importlib.util
    spec = importlib.util.spec_from_file_location("be_render_prompt_32", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.slot_table((BE_SKILLS / template).read_text(encoding="utf-8"))


def test_sebelas_dispatcher_tercakup():
    assert len(DISPATCHERS) == 11


@pytest.mark.regression("32 T1")
@pytest.mark.parametrize("template", DISPATCHERS)
def test_tiap_dispatcher_dapat_dirender_tanpa_slot_tabel_mentah(tmp_path, template):
    slots = _required(template)
    values = [f"{k}=<{k}>" for k, wajib in slots.items() if wajib]
    code, out = _render(tmp_path, template, *values)
    assert code == 0, out
    body = (tmp_path / out["out"]).read_text(encoding="utf-8")
    assert not [s for s in slots if "{" + s + "}" in body]
    rujukan = f"Baca dan jalankan instruksi di `{out['out']}`; jangan menyuntingnya."
    awal = " ".join(body.strip().split("\n\n", 1)[0].split()).rstrip(" .,:;")
    harap = f"{awal[:239].rstrip()}… {rujukan}" if len(awal) > 240 else f"{awal}. {rujukan}"
    assert awal and out["prompt"] == harap
    assert "\n" not in out["prompt"]
    text = (BE_SKILLS / template).read_text(encoding="utf-8")
    para = text.split("**Cara dispatch (32 T1).**", 1)[1].split("\n\n", 1)[0]
    assert "render_prompt.py" in para and "${CLAUDE_PLUGIN_ROOT}" not in para


@pytest.mark.regression("32 T1")
def test_slot_wajib_kosong_ditolak_dan_prompt_tidak_ditulis(tmp_path):
    code, out = _render(tmp_path, "plan/dispatcher/explorer.md", "objective=x", "taskdir=" + TD)
    assert code == 1 and out["status"] == "FAIL" and "slot wajib kosong" in out["reason"]
    assert not (tmp_path / TD / ".explore/prompt/p.md").exists()


@pytest.mark.regression("32 T1")
def test_slot_opsional_kosong_menghapus_barisnya(tmp_path):
    code, out = _render(tmp_path, "system-analysis/dispatcher/explorer-surface.md",
                        "objective=Petakan RecallOrderService.process", "permukaan=(a)", "resep_navigasi=- grep",
                        "taskdir=" + TD, "slug=foto")
    body = (tmp_path / out["out"]).read_text(encoding="utf-8")
    assert code == 0 and "Mode delta:" not in body and "Konteks yang sudah diketahui" not in body
    assert set(out["baris_opsional_dihapus"]) == {"konteks_diketahui", "laporan_gerbang", "batas_cakupan"}
    code, out = _render(tmp_path, "system-analysis/dispatcher/explorer-surface.md",
                        "objective=Petakan", "permukaan=(c)", "resep_navigasi=- grep", "taskdir=" + TD, "slug=foto",
                        f"laporan_gerbang={TD}/.explore/gate-foto.md")
    body = (tmp_path / out["out"]).read_text(encoding="utf-8")
    assert f"Mode delta: laporan gerbang {TD}/.explore/gate-foto.md" in body


@pytest.mark.regression("32 T1")
def test_kurawal_bukan_slot_dibiarkan_dan_nilai_tidak_dipindai_ulang(tmp_path):
    code, out = _render(tmp_path, "plan/dispatcher/reviewer.md", f"taskdir={TD}", "target={chain}", "ronde=1",
                        "chain=PRD_BRIEF")
    body = (tmp_path / out["out"]).read_text(encoding="utf-8")
    assert code == 0 and "BR-{n}" in body and "Review dokumen brief berikut: `{chain}`" in body


@pytest.mark.regression("32 T1")
@pytest.mark.parametrize("out", ["src/prompt.md", f"{TD}/.explore/p.md", f"{TD}/.explore/prompt/../x.md", "/tmp/p.md"])
def test_out_di_luar_laci_prompt_ditolak(tmp_path, out):
    code, res = _render(tmp_path, "architect/dispatcher/implementor.md", out=out)
    assert code == 2 and res["status"] == "ERROR"


@pytest.mark.regression("32 T1")
def test_slot_tak_dikenal_ditolak(tmp_path):
    code, out = _render(tmp_path, "architect/dispatcher/implementor.md", "taskdir=x", "brief_path=y", "unit_name=z",
                        "adapter_path=a", "objektif=salah-ketik")
    assert code == 1 and "slot tak dikenal" in out["reason"]


@pytest.mark.regression("32 T1")
def test_slots_json_untuk_nilai_multi_baris(tmp_path):
    slots = tmp_path / "slots.json"
    slots.write_text(json.dumps({"objective": "x", "taskdir": TD, "slug": "s", "konteks_diketahui": "baris 1\nbaris 2",
                                 "resep_navigasi": "- a\n- b"}), encoding="utf-8")
    code, out = _render(tmp_path, "plan/dispatcher/explorer.md", extra=("--slots-json", str(slots)))
    body = (tmp_path / out["out"]).read_text(encoding="utf-8")
    assert code == 0 and "baris 1\nbaris 2" in body and "- a\n- b" in body


@pytest.mark.regression("32 T1")
def test_prompt_jadi_tidak_terpanen_validate_briefs():
    """Prompt `plan` memuat kerangka `### File Map`; ia wajib tinggal di subdirektori yang tidak ikut glob laci."""
    vb = (BE_SKILLS / "plan/scripts/validate_briefs.py").read_text(encoding="utf-8")
    assert 'laci.glob("*.md")' in vb


@pytest.mark.regression("32 T1")
def test_agent_membaca_prompt_berkas_dan_skill_merender():
    for agent in sorted((PLUGINS / "backend/agents").glob("*.md")):
        assert "**Prompt berupa rujukan berkas (32 T1).**" in agent.read_text(encoding="utf-8"), agent.name
    for skill in ("tech-lead", "system-analysis", "plan", "business-analysis", "debug", "architect"):
        text = (BE_SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "render_prompt.py" in text, skill
        assert not re.search(r"[Mm]uat (template|`dispatcher)", text), skill


@pytest.mark.regression("32 T1")
def test_prompt_dispatch_membawa_ringkasan_maksud_satu_baris(tmp_path):
    """Classifier auto mode tidak membaca berkas rujukan: maksud dispatch harus terlihat di prompt `Agent`."""
    obj = "telusuri alur pickup AWB manual\nrecall order di modul logistik"
    code, out = _render(tmp_path, "tech-lead/dispatcher/explorer.md", f"objective={obj}",
                        "konteks_diketahui=k", "batas_cakupan=b", "slug=pickup-awb",
                        out="backenddev/docs/.explore/prompt/pickup-awb.md")
    assert code == 0, out
    assert out["prompt"] == ("Objective: telusuri alur pickup AWB manual recall order di modul logistik. "
                             "Baca dan jalankan instruksi di `backenddev/docs/.explore/prompt/pickup-awb.md`; "
                             "jangan menyuntingnya.")
    teks = run_script(SCRIPT, "--template", str(BE_SKILLS / "tech-lead/dispatcher/explorer.md"),
                      "--out", "backenddev/docs/.explore/prompt/pickup-awb.md", "--root", str(tmp_path),
                      "--slot", f"objective={obj}", "--slot", "konteks_diketahui=k", "--slot", "batas_cakupan=b",
                      "--slot", "slug=pickup-awb", cwd=tmp_path)
    assert teks.returncode == 0 and f'prompt subagent: "{out["prompt"]}"' in teks.stdout


@pytest.mark.regression("32 T1")
def test_ringkasan_objective_panjang_dipangkas(tmp_path):
    code, out = _render(tmp_path, "tech-lead/dispatcher/explorer.md", "objective=" + "x" * 500,
                        "konteks_diketahui=k", "batas_cakupan=b", "slug=s",
                        out="backenddev/docs/.explore/prompt/s.md")
    assert code == 0, out
    awal, rujukan = out["prompt"].split(" Baca dan jalankan instruksi di ", 1)
    assert len(awal) == 240 and awal.endswith("…") and not awal.endswith("….")
    assert awal.startswith("Objective: xxx")
    assert rujukan == "`backenddev/docs/.explore/prompt/s.md`; jangan menyuntingnya."


@pytest.mark.regression("32 T1")
def test_ringkasan_implementor_menyebut_brief(tmp_path):
    code, out = _render(tmp_path, "architect/dispatcher/implementor.md", f"taskdir={TD}",
                        f"brief_path={TD}/brief-01-x.md", "unit_name=01", "adapter_path=a.md",
                        out=f"{TD}/.explore/prompt/implementor-01.md")
    assert code == 0, out
    assert out["prompt"].startswith(f"Eksekusi satu brief implementasi: `{TD}/brief-01-x.md` (unit `01`). Baca ")
