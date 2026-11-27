"""Review lapangan hkm 2611 — B4 (tiket cepat aditif = kontrak tersepakati) dan B9 (plafon batch 8 brief)."""
import json
import re

import pytest

from conftest import BE_SKILLS, TD, be_run, brief, load_module

SCAFFOLD = "plan/scripts/scaffold_brief.py"


def _read(rel):
    return (BE_SKILLS / rel).read_text(encoding="utf-8")


def _rows(n, start=1):
    return [{"nn": f"{i:02d}", "unit": f"unit-{i}", "title": f"unit {i}", "risk": "MINOR",
             "fulfills": [f"SC-{1 + i % 2}"]} for i in range(start, start + n)]


def _write_matrix(repo, rows, *flags):
    path = repo / TD / ".explore" / "brief-spec.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"briefs": rows}), encoding="utf-8")
    proc = be_run(repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", str(path), *flags)
    return proc.returncode, proc.stdout + proc.stderr


# -- B9: penahan mekanis di --write-matrix ------------------------------------------------------

@pytest.mark.regression("B9")
def test_delapan_brief_lolos(chain_repo):
    code, out = _write_matrix(chain_repo, _rows(8))
    assert code == 0, out


@pytest.mark.regression("B9")
def test_sembilan_brief_ditolak_tanpa_persetujuan(chain_repo):
    code, out = _write_matrix(chain_repo, _rows(9))
    assert code == 1
    assert "BATCH_BESAR" in out and "--batch-besar" in out
    assert not (chain_repo / TD / ".explore" / "brief-matrix.json").exists()


@pytest.mark.regression("B9")
def test_batch_besar_diterima_lolos(chain_repo):
    code, out = _write_matrix(chain_repo, _rows(9), "--batch-besar")
    assert code == 0, out


@pytest.mark.regression("B9")
def test_taskdir_tanpa_chain_tidak_dikenai_plafon(chain_repo):
    task = chain_repo / TD / "TASK.md"
    task.write_text(task.read_text(encoding="utf-8").replace("chain: BRIEF\n", ""), encoding="utf-8")
    code, out = _write_matrix(chain_repo, _rows(9))
    assert code == 0, out


@pytest.mark.regression("B9")
def test_append_hanya_menghitung_baris_baru(chain_repo):
    code, out = _write_matrix(chain_repo, _rows(7))
    assert code == 0, out
    for row in _rows(7):
        brief(chain_repo, row["nn"], row["unit"], "DONE")
    code, out = _write_matrix(chain_repo, _rows(3, start=8), "--append")
    assert code == 0, out
    code, out = _write_matrix(chain_repo, _rows(9, start=8), "--append")
    assert code == 1 and "BATCH_BESAR" in out


@pytest.mark.regression("B9")
def test_plafon_prosa_selaras_konstanta():
    mod = load_module(BE_SKILLS / SCAFFOLD, "scaffold_b9")
    rules = _read("plan/references/entry-rules.md")
    assert "### 1E. Plafon Batch" in rules
    assert re.search(rf"\*\*{mod.BATCH_MAX} brief baru per batch\*\*", rules)
    assert f"lebih dari {mod.BATCH_MAX} baris baru" in rules


@pytest.mark.regression("B9")
def test_vonis_batch_besar_ditangani_analyst_dan_gerbang():
    plan, analyst = _read("plan/SKILL.md"), _read("analyst/SKILL.md")
    assert "`batch_besar`" in plan and "BATCH_BESAR" in plan and "[--batch-besar]" in plan
    assert "1a. **Batch di atas plafon (B9).**" in analyst
    assert "10. **Batch dipecah user (B9)**" in analyst
    assert "Butir 10 (batch dipecah)" in _read("tech-lead/SKILL.md")


# -- B4: tiket cepat aditif menahan PRD dan pemicu eskalasi 1 ---------------------------------------

@pytest.mark.regression("B4")
def test_sumbu_kontrak_mengakui_tiket_cepat_aditif():
    rules = _read("analyst/references/chain-rules.md")
    assert "**Tiket `backend:ticket` sebagai kontrak tersepakati (B4).**" in rules
    # Diteruskan ke plan pada chain BRIEF; tanpa itu pemicu eskalasi 1 menaikkan chain kembali.
    assert "Hop `BRIEF` memikulnya hanya pada chain `BRIEF`" in rules
    assert "pada chain `BRIEF` juga `ticket_source`" in _read("analyst/SKILL.md")


@pytest.mark.regression("B4")
def test_plan_menahan_pemicu_1_atas_delta_tiket():
    assert "**Kontrak dari tiket cepat (B4).**" in _read("plan/references/entry-rules.md")
    assert "- `ticket_source` — string" in _read("plan/SKILL.md")
    assert '"Kontrak dari tiket cepat"' in _read("plan/references/slicing-and-scan.md")
    assert "chain-rules.md` bagian 1.2, B4" in _read("tech-lead/references/gate-scope.md")
