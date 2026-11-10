"""Alat ukur pemakaian token dev-only `scripts/token_usage.py` (Langkah 30 U1, Langkah 31 X4–X5)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "token_usage.py"
SKILL = "Base directory for this skill: /home/u/.claude/plugins/cache/nataflow/backend/0.19.1/skills/{}\n\n# body"


def _usage(cr, cw=0, out=10, inp=1):
    return {"input_tokens": inp, "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr,
            "output_tokens": out}


def _assistant(mid, usage, content=None):
    return {"type": "assistant", "message": {"id": mid, "model": "claude-opus-5-5", "usage": usage,
                                             "content": content or [{"type": "text", "text": "x"}]}}


def _meta(text):
    return {"type": "user", "isMeta": True, "message": {"role": "user", "content": text}}


def _write(path: Path, recs):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")


@pytest.fixture
def projects(tmp_path):
    root = tmp_path / "projects"
    slug = root / "-repo-api"
    dispatch = {"type": "tool_use", "id": "toolu_1", "name": "Agent",
                "input": {"subagent_type": "backend:code-explorer",
                          "prompt": "Objective: x\nKedalaman: menyeluruh\n### Blast Map"}}
    _write(slug / "s1.jsonl", [
        {"type": "user", "timestamp": "2026-11-05T01:00:00Z", "message": {"role": "user", "content": "halo"}},
        _assistant("m1", _usage(cr=1000)),
        _meta(SKILL.format("tech-lead")),
        # satu pesan API ditulis dua baris (dua blok konten): hanya dihitung sekali
        _assistant("m2", _usage(cr=2000), [dispatch]),
        _assistant("m2", _usage(cr=2000), [{"type": "text", "text": "y"}]),
        _meta('Another Claude session sent a message:\n<agent-message from="abc">\n  ' + "r" * 500),
        {"type": "system", "subtype": "compact_boundary", "compactMetadata": {"trigger": "manual", "preTokens": 9000}},
        _assistant("m3", _usage(cr=500)),
        _meta(SKILL.format("architect")),
        _assistant("m4", _usage(cr=4000, cw=100, out=20)),
    ])
    _write(slug / "s1" / "subagents" / "agent-abc.jsonl", [_assistant("a1", _usage(cr=300, out=40))])
    (slug / "s1" / "subagents" / "agent-abc.meta.json").write_text(
        json.dumps({"agentType": "backend:code-explorer", "toolUseId": "toolu_1"}), encoding="utf-8")
    # sesi lama + slug turunan
    _write(root / "-repo-api-sub" / "s2.jsonl", [
        {"type": "user", "timestamp": "2026-10-01T00:00:00Z", "message": {"role": "user", "content": "lama"}},
        _assistant("z1", _usage(cr=100)),
    ])
    return root


def _run(projects, *args):
    proc = subprocess.run([sys.executable, str(SCRIPT), *args, "--projects-dir", str(projects), "--json"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def test_u1_ringkas_main_fase_subagent(projects):
    r = _run(projects, "ringkas", "--slug=-repo-api")
    assert r["sesi"] == 1
    assert r["main"]["calls"] == 4  # m2 dua baris, satu pesan
    assert r["main"]["cache_read"] == 1000 + 2000 + 500 + 4000
    fase = {f["fase"]: f for f in r["fase"]}
    assert fase["(pra-skill)"]["calls"] == 1
    assert fase["backend:tech-lead"]["calls"] == 2
    assert fase["backend:architect"]["calls"] == 1
    assert fase["backend:architect"]["konteks_rata2"] == 1 + 100 + 4000
    sub = r["subagent"][0]
    assert (sub["tipe"], sub["model"], sub["n"], sub["calls"]) == ("backend:code-explorer", "claude-opus-5-5", 1, 1)
    assert r["balikan"][0]["tipe"] == "backend:code-explorer"
    assert r["compaction"]["manual"] == {"n": 1, "pre_median": 9000, "post_median": 501}
    assert r["rangkaian"][0]["skill"] == "backend:tech-lead → backend:architect"


def test_u1_biaya_memakai_bobot(projects):
    a = _run(projects, "ringkas", "--slug=-repo-api")
    b = _run(projects, "ringkas", "--slug=-repo-api", "--bobot", "cr=0.2")
    assert b["main"]["biaya"] - a["main"]["biaya"] == pytest.approx(0.1 * a["main"]["cache_read"], abs=1)


def test_u1_turunan_dan_since(projects):
    assert _run(projects, "ringkas", "--slug=-repo-api", "--turunan")["sesi"] == 2
    assert _run(projects, "ringkas", "--slug=-repo-api", "--turunan", "--since", "2026-11-01")["sesi"] == 1


def test_u1_tidak_mencetak_isi(projects):
    proc = subprocess.run([sys.executable, str(SCRIPT), "ringkas", "--slug=-repo-api", "--projects-dir",
                           str(projects)], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0
    assert "halo" not in proc.stdout and "rrrr" not in proc.stdout


def test_x4_explorer_per_fase_profil_kedalaman(projects):
    r = _run(projects, "explorer", "--slug=-repo-api")
    (row,) = r["baris"]
    assert (row["fase"], row["profil"], row["kedalaman"], row["n"]) == ("backend:tech-lead", "blast", "menyeluruh", 1)
    assert row["biaya"] > 0  # dipasangkan lewat toolUseId meta
    assert row["balikan_rata2"] > 500
    assert r["per_sesi"]["backend:tech-lead"] == {"sesi": 1, "p50": 1, "maks": 1}


def test_u1_tanpa_slug_gagal_terbaca(tmp_path):
    proc = subprocess.run([sys.executable, str(SCRIPT), "ringkas", "--json"], capture_output=True, text=True,
                          timeout=60)
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["status"] == "FAIL"


def test_u1_slug_dari_path():
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        import token_usage
        assert token_usage.slug_of("/home/u/work/hkm/wms") == "-home-u-work-hkm-wms"
        assert token_usage.skill_label(SKILL.format("plan")) == "backend:plan"
        assert token_usage.skill_label("Base directory for this skill: /x/src/plugins/backend/skills/plan") \
            == "backend:plan"
    finally:
        sys.path.remove(str(SCRIPT.parent))
        sys.modules.pop("token_usage", None)


@pytest.mark.parametrize("since,sesi", [
    ("2026-11-05T01:00:00Z", 1),          # tepat di awal sesi: ikut
    ("2026-11-05T08:00+07:00", 1),        # waktu yang sama dalam GMT+7
    ("2026-11-05T01:30:00Z", 0),          # sesudah sesi mulai: dibuang
    ("2026-11-05 08:30+07:00", 0),        # spasi sebagai pemisah tanggal-jam
    ("2026-10-01", 2),                    # tanggal saja tetap didukung
])
def test_u1_since_menerima_jam_dan_zona(projects, since, sesi):
    assert _run(projects, "ringkas", "--slug=-repo-api", "--turunan", "--since", since)["sesi"] == sesi


def test_u1_since_tak_terbaca(projects):
    proc = subprocess.run([sys.executable, str(SCRIPT), "ringkas", "--slug=-repo-api", "--since", "kemarin",
                           "--projects-dir", str(projects), "--json"], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 2 and "--since tidak terbaca" in json.loads(proc.stdout)["error"]


def _dispatch(tid, blast):
    prompt = "Objective: x\nKedalaman: menyeluruh\n" + ("### Blast Map" if blast else "### Error Surface")
    return {"type": "tool_use", "id": tid, "name": "Agent",
            "input": {"subagent_type": "backend:code-explorer", "prompt": prompt}}


def _ack(tid):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid,
         "content": [{"type": "text", "text": "Async agent launched successfully."}]}]}}


def _handback(aid):
    return _meta(f'<agent-message from="{aid}">\n  ## Explorer Report — x')


def _sesi_explorer(root, name, recs):
    sesi = root / "-repo-sa" / f"{name}.jsonl"
    _write(sesi, [{"type": "user", "timestamp": "2026-11-11T01:00:00Z", "message": {"role": "user", "content": "q"}},
                  _meta(SKILL.format("system-analysis")), *recs])
    for aid, tid in (("s", "t_s"), ("b", "t_b")):
        _write(sesi.with_suffix("") / "subagents" / f"agent-{aid}{name}.jsonl", [_assistant(f"a{aid}", _usage(cr=10))])
        (sesi.with_suffix("") / "subagents" / f"agent-{aid}{name}.meta.json").write_text(
            json.dumps({"agentType": "backend:code-explorer", "toolUseId": f"{tid}{name}"}), encoding="utf-8")


@pytest.mark.regression("31 X5")
@pytest.mark.parametrize("pola, harap", [("satu_pesan", 1), ("sebelum_balik", 1), ("berurutan", 0)])
def test_x5_blast_tumpang_tindih_surface(tmp_path, pola, harap):
    n = pola
    if pola == "satu_pesan":  # dua blok tool_use satu pesan API ditulis dua baris, blast lebih dulu
        recs = [_assistant("m1", _usage(cr=1), [_dispatch(f"t_b{n}", True)]),
                _assistant("m1", _usage(cr=1), [_dispatch(f"t_s{n}", False)]),
                _ack(f"t_b{n}"), _ack(f"t_s{n}"), _handback(f"s{n}"), _handback(f"b{n}")]
    elif pola == "sebelum_balik":  # pesan berbeda, tapi surface baru sebatas `Async agent launched`
        recs = [_assistant("m1", _usage(cr=1), [_dispatch(f"t_s{n}", False)]), _ack(f"t_s{n}"),
                _assistant("m2", _usage(cr=1), [_dispatch(f"t_b{n}", True)]), _ack(f"t_b{n}"),
                _handback(f"s{n}"), _handback(f"b{n}")]
    else:
        recs = [_assistant("m1", _usage(cr=1), [_dispatch(f"t_s{n}", False)]), _ack(f"t_s{n}"), _handback(f"s{n}"),
                _assistant("m2", _usage(cr=1), [_dispatch(f"t_b{n}", True)]), _ack(f"t_b{n}"), _handback(f"b{n}")]
    _sesi_explorer(tmp_path, n, recs)
    r = _run(tmp_path, "explorer", "--slug=-repo-sa")
    rows = {b["profil"]: b for b in r["baris"]}
    assert rows["blast"]["n"] == 1 and rows["surface"]["n"] == 1
    assert rows["blast"]["tumpang_tindih"] == harap and rows["surface"]["tumpang_tindih"] == 0
