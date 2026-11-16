"""Langkah 36 — friksi lapangan frontend: verdict reviewer (V1), plafon journey di prosa (J1), keluaran prasyarat
architect terstruktur (S1), format otomatis (F1), aksi DELETE (D1), ronde tambahan (T1), lead ramping (L1)."""
import json
import re

import pytest

from conftest import FE_SKILLS, FE_TD, PLUGINS, commit, fe_approved_chain, fe_base_commit, fe_draft as draft, fe_open_sidik, \
    fe_round as round_, fe_run, load_module, write_files

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


# ------------------------------------------------------------------ S1 — keluaran prasyarat architect terstruktur


def arch(repo, *args):
    return fe_run(repo, "architect/scripts/check_preconditions.py", "--taskdir", FE_TD, *args)


@pytest.mark.regression("36 S1")
def test_s1_rantai_dan_base_commit_dari_skrip(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    r = arch(repo)
    base = fe_base_commit(repo)[:7]
    assert f"base_commit={base}" in r.out, r.out
    rantai = r.out.split("\nRantai:\n", 1)[1]
    assert rantai.splitlines()[0] == ("- 01 · orders-lacak-button · READY · CREATE: src/features/orders/"
                                      "OrderDetail.test.tsx · MODIFY: src/features/orders/OrderDetail.tsx · "
                                      "depends_on []"), rantai
    data = json.loads(arch(repo, "--json").out)
    assert data["base_commit"] == base
    assert data["briefs"][0]["files"] == {"CREATE": ["src/features/orders/OrderDetail.test.tsx"],
                                          "MODIFY": ["src/features/orders/OrderDetail.tsx"]}


@pytest.mark.regression("36 S1")
def test_s1_ingest_mencetak_berkas_unit(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    r = arch(repo, "--brief", "01")
    assert "Berkas unit 01: CREATE: src/features/orders/OrderDetail.test.tsx · MODIFY: " in r.out, r.out
    assert "\nRantai:" not in r.out
    data = json.loads(arch(repo, "--brief", "01", "--json").out)
    assert data["files"]["MODIFY"] == ["src/features/orders/OrderDetail.tsx"]


def test_s1_prosa_architect_tidak_lagi_sed_atas_task_md():
    skill = _read("architect/SKILL.md")
    assert "sed -n 's/^base_commit" not in skill
    phase0 = skill.split("### Phase 0", 1)[1].split("### Phase 1", 1)[0]
    assert "`Rantai:`" in phase0 and "`base_commit=`" in phase0


# ------------------------------------------------------------------ F1 — format otomatis sebelum commit unit

COMMANDS = ".claude/profile/frontenddev/commands.md"


@pytest.mark.regression("36 F1")
def test_f1_format_dari_profil_atau_strip(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    assert "format=-" in arch(repo).out
    assert json.loads(arch(repo, "--json").out)["format"] == ""
    text = (repo / COMMANDS).read_text(encoding="utf-8")
    write_files(repo, {COMMANDS: text + "\n- `format`: `pnpm prettier --write --ignore-unknown` — repo bersih format\n"})
    commit(repo, "chore: profil format", COMMANDS)
    r = arch(repo)
    assert "format=pnpm prettier --write --ignore-unknown" in r.out, r.out
    assert json.loads(arch(repo, "--json").out)["format"] == "pnpm prettier --write --ignore-unknown"


def test_f1_format_command_tanpa_fallback_adapter(tmp_path):
    lib = load_module(FE_SKILLS / "_common" / "precondition_lib.py", "fe_lib_36_f1")
    assert lib.format_command(tmp_path) == ""
    (tmp_path / "commands.md").write_text("- `typecheck-per-brief`: `ya`\n", encoding="utf-8")
    assert lib.format_command(tmp_path) == ""


def test_f1_prosa_format_unit_sebelum_commit_unit():
    proto = _read("architect/references/execution-protocol.md")
    bagian3 = proto.split("## 3.", 1)[1].split("## 4.", 1)[0]
    assert bagian3.index("**Format unit**") < bagian3.index("**Commit unit**")
    for wajib in ("`format=`", "verify_scope.py", "`## Triase`", "bukan verifikasi"):
        assert wajib in bagian3, wajib
    guard = _read("architect/SKILL.md").split("## Guardrails", 1)[1]
    assert "**Format unit**" in guard.split("\n- **SEKUENSIAL", 1)[0]
    tpl = _read("profile/templates/profile-template.md").split("## 6.", 1)[1].split("## 7.", 1)[0]
    assert "- `format`:" in tpl and "opsional" in tpl
