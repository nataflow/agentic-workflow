"""Teks gerbang `hooks/gate_text.py` kedua plugin (L1.3 butir LEWATI, L1.4 profil)."""
import importlib.util
import json
import sys

import pytest

from conftest import PLUGIN_DIRS, PLUGINS

GATES = {"backenddev": "backend:tech-lead", "frontenddev": "frontend:lead"}
STATES = ("ABSENT", "OK", "INVALID_JSON", "NO_STACK", "UNKNOWN_STACK", "INCOMPLETE", "OTHER_OWNER")


def _load(plugin, name):
    key = f"_gate_test_{plugin}_{name}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, PLUGINS / PLUGIN_DIRS[plugin] / "hooks" / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod  # dataclass butuh modulnya terdaftar saat dimuat
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _verdict(plugin, state, location="own"):
    detect = _load(plugin, "detect")
    stack = detect.STACKS[plugin][0]
    prof = detect.Profile(state, location, stack if state != "NO_STACK" else "",
                          "frontenddev" if plugin == "backenddev" else "backenddev",
                          ["commands.md"] if state == "INCOMPLETE" else [])
    if state == "OTHER_OWNER":
        location = "legacy"
        prof.location = location
    return detect.Verdict(plugin=plugin, root="/x", emit=True, stack=stack, source="package.json", profile=prof)


@pytest.mark.parametrize("plugin", list(GATES))
def test_lewati_mentions_other_plugins(plugin):
    text = _load(plugin, "gate_text").render(_verdict(plugin, "OK"))
    assert "/analyst:*" in text and "/product:*" in text and "/quickdev:*" in text
    assert "/nataflow:*" in text            # 25 R5: create-artifact mengklaim bebas gerbang engineer


@pytest.mark.regression("40 T1")
def test_lewati_tiket_cepat_hanya_backend():
    """Permintaan tiket teknis langsung ke `backend:ticket`; frontend belum punya skill itu (keputusan 40)."""
    be = _load("backenddev", "gate_text").render(_verdict("backenddev", "OK"))
    fe = _load("frontenddev", "gate_text").render(_verdict("frontenddev", "OK"))
    assert "`/backend:ticket`" in be and "LEWATI hanya enam" in be
    assert "ticket" not in fe


@pytest.mark.regression("G1")
@pytest.mark.parametrize("plugin", list(GATES))
def test_lewati_skill_user_di_luar_plugin(plugin):
    """Slash skill user tanpa prefiks plugin (`/planning`) milik skill itu, termasuk eksekusinya (review hkm G1)."""
    text = " ".join(_load(plugin, "gate_text").render(_verdict(plugin, "OK")).split())
    assert "`/planning`" in text and "`/discus-mode`" in text
    assert "diketik user sendiri dan bukan milik plugin" in text
    assert "eksekusi sesudah user menyetujui rencananya" in text
    assert f"jangan memanggil skill `{GATES[plugin].split(':')[0]}:*` sebagai pengganti" in text


@pytest.mark.regression("G1")
@pytest.mark.parametrize("plugin", list(GATES))
def test_lewati_opt_out_sesi(plugin):
    """Frasa opt-out user berlaku untuk sisa sesi sampai user meminta kembali (review hkm G1, keputusan a)."""
    text = " ".join(_load(plugin, "gate_text").render(_verdict(plugin, "OK")).split())
    assert '"abaikan hook"' in text and '"jangan lewat plugin"' in text
    assert "sisa sesi" in text


@pytest.mark.parametrize("plugin", list(GATES))
@pytest.mark.parametrize("state", STATES)
def test_render_all_states_valid(plugin, state):
    text = _load(plugin, "gate_text").render(_verdict(plugin, state))
    json.loads(json.dumps({"additionalContext": text}))
    assert text.startswith("<") and text.rstrip().endswith(">")
    assert GATES[plugin] in text


@pytest.mark.parametrize("plugin", list(GATES))
def test_profile_absent_text_defers_to_gate(plugin):
    text = _load(plugin, "gate_text").render(_verdict(plugin, "ABSENT"))
    assert "BERHENTI SEGERA" not in text
    assert "selain baca-kode" not in text
    assert GATES[plugin] in text
    assert "GENERATE" in text


@pytest.mark.parametrize("plugin", list(GATES))
@pytest.mark.parametrize("state", ["OK", "INCOMPLETE"])
def test_legacy_profile_routes_migrate(plugin, state):
    text = _load(plugin, "gate_text").render(_verdict(plugin, state, location="legacy"))
    assert "MIGRATE" in text


@pytest.mark.parametrize("plugin", list(GATES))
def test_other_owner_text_forbids_overwrite(plugin):
    text = _load(plugin, "gate_text").render(_verdict(plugin, "OTHER_OWNER"))
    assert "jangan ditimpa" in text


def test_no_berhenti_segera_in_hooks():
    for path in PLUGINS.glob("*/hooks/*"):
        if path.is_file() and path.suffix in (".py", ".json", ".sh"):
            assert "BERHENTI SEGERA" not in path.read_text(encoding="utf-8"), path


@pytest.mark.parametrize("plugin", list(GATES))
@pytest.mark.parametrize("location,mode", [("own", "REFRESH"), ("legacy", "GENERATE")])
def test_invalid_json_mode_matches_profile_script(plugin, location, mode):
    """Hook dan prasyarat `profile` sepakat: index.json rusak milik sendiri → REFRESH; lokasi lama → GENERATE."""
    text = _load(plugin, "gate_text").render(_verdict(plugin, "INVALID_JSON", location=location))
    assert mode in text
