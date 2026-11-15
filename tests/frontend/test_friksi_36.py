"""Langkah 36 — friksi lapangan frontend: verdict reviewer (V1), plafon journey di prosa (J1), keluaran prasyarat
architect terstruktur (S1), format otomatis (F1), aksi DELETE (D1), ronde tambahan (T1), lead ramping (L1)."""
import re

import pytest

from conftest import FE_SKILLS, FE_TD, PLUGINS, fe_draft as draft, fe_open_sidik, fe_round as round_, fe_run, \
    load_module, write_files

JOURNEY = FE_SKILLS / "_common" / "journey.py"


def _read(rel):
    return (FE_SKILLS / rel).read_text(encoding="utf-8")


def rr(repo, *args, gate="contract"):
    return fe_run(repo, "_common/review_round.py", *args, "--taskdir", FE_TD, "--gate", gate)


# ------------------------------------------------------------------ V1 — verdict reviewer kontrak


def _evidence(repo, n, verdict_line, sidik):
    rel = f"{FE_TD}/.explore/contract-review-r{n}.md"
    write_files(repo, {rel: f"## Contract Review\n{verdict_line}\n- Ronde: {n}\n- Sidik: {sidik}\n"
                            "- BLOCKER: 0 [MEKANIS] · 0 [SEMANTIK]\n\n**BLOCKER:**\n- —\n"})
    return rel


@pytest.mark.regression("36 V1")
def test_v1_verdict_dengan_komentar_em_dash_diterima(fe_chain_repo):
    repo = fe_chain_repo
    assert rr(repo, "open").returncode == 0
    rel = _evidence(repo, 1, "- Verdict: PASS — nol temuan", fe_open_sidik(repo))
    r = rr(repo, "record", "--verdict", "PASS", "--evidence", rel)
    assert r.returncode == 0, r.out
    assert draft(repo).returncode == 0


@pytest.mark.regression("36 V1")
@pytest.mark.parametrize("line", ["- Verdict: PASS | BLOCKED", "- **Verdict:** PASS", "- Verdict: PASS nol temuan"])
def test_v1_bentuk_lain_tetap_ditolak(fe_chain_repo, line):
    repo = fe_chain_repo
    assert rr(repo, "open").returncode == 0
    rel = _evidence(repo, 1, line, fe_open_sidik(repo))
    r = rr(repo, "record", "--verdict", "PASS", "--evidence", rel)
    assert r.returncode == 1 and "- Verdict:" in r.out, r.out


def test_v1_agent_tidak_lagi_menyuruh_teks_di_baris_verdict():
    agent = (PLUGINS / "frontend" / "agents" / "contract-reviewer.md").read_text(encoding="utf-8")
    assert "PASS — nol temuan" not in agent
    assert "`- Verdict: PASS`" in agent and "dibaca mesin" in agent


# ------------------------------------------------------------------ J1 — plafon journey di prosa


@pytest.mark.regression("36 J1")
def test_j1_tiap_titik_panggil_menyebut_plafon():
    mod = load_module(JOURNEY, "fe_journey_36_j1")
    slot = f"≤{mod.MAX_KALIMAT} kalimat, ≤{mod.MAX_TEKS} karakter"
    for rel in ("lead/SKILL.md", "ux-design/SKILL.md", "ui-design/SKILL.md", "contract/SKILL.md",
                "plan/SKILL.md", "architect/SKILL.md", "lead/references/lane-routing-matrix.md"):
        text = _read(rel)
        calls = re.findall(r"journey\.py[»`]? add [^\n]*", text)
        assert calls, rel
        for line in calls:
            assert slot in line, (rel, line[:120])
    four_a = _read("lead/references/lane-routing-matrix.md").split("## 4a.", 1)[1].split("\n---\n", 1)[0]
    for wajib in (f"**{mod.MAX_KALIMAT} kalimat**", f"**{mod.MAX_TEKS} karakter**", f"{mod.MAX_ENTRI} entri"):
        assert wajib in four_a, wajib


def test_j1_architect_tidak_menyalin_status_ke_journey():
    phase5 = _read("architect/SKILL.md").split("### Phase 5", 1)[1].split("## Guardrails", 1)[0]
    assert "hasil akhir" not in phase5 and "tidak ditulis ulang" in phase5
