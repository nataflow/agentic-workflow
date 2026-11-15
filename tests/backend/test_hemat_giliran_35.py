"""Langkah 35 — hemat giliran fase `plan`: kerangka sekaligus (G1), `--open-round` membawa state (G2), gerbang
per-brief hanya brief pertama (G3), dan contoh bentuk `brief-spec.json` di SKILL (G4)."""
import json
import re

import pytest

from conftest import BE_SKILLS, TD, be_run, brief, commit, load_module, write_files

SCAFFOLD = "plan/scripts/scaffold_brief.py"
VALIDATE = "plan/scripts/validate_briefs.py"
HALT = ("---\nbrief: brief-02-endpoint.md\nverdict: COMPILE\nsha: abc1234\nbaseline: 1111111 · hijau\n---\n"
        "# HALT — brief-02-endpoint\n\n## Galat\nSyntaxError: invalid syntax\n")


def _row(nn, unit, fulfills, **extra):
    return {"nn": nn, "unit": unit, "title": unit, "risk": "MINOR", "fulfills": fulfills, **extra}


def _matrix(repo, *rows, append=False):
    spec = repo / TD / ".explore" / "brief-spec.json"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps({"briefs": list(rows)}), encoding="utf-8")
    args = ["--taskdir", TD, "--write-matrix", *(["--append"] if append else []), "--spec", str(spec)]
    out = be_run(repo, SCAFFOLD, *args)
    assert out.returncode == 0, out.stdout + out.stderr
    return out


def _all(repo):
    return be_run(repo, SCAFFOLD, "--taskdir", TD, "--all")


def _briefs(repo):
    return sorted(p.name for p in (repo / TD).glob("brief-*.md"))


# -- G1: scaffold_brief.py --all ----------------------------------------------------------------


@pytest.mark.regression("35 G1")
def test_g1_all_identik_dengan_nn_per_brief(chain_repo):
    _matrix(chain_repo, _row("01", "lock", ["SC-1"]), _row("02", "endpoint", ["SC-2"]),
            _row("03", "recap", ["SC-2"], consumes=["brief-02: POST /orders/{id}/recap"]))
    out = _all(chain_repo)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "3 kerangka ditulis" in out.stdout
    sekaligus = {n: (chain_repo / TD / n).read_text(encoding="utf-8") for n in _briefs(chain_repo)}
    assert list(sekaligus) == ["brief-01-lock.md", "brief-02-endpoint.md", "brief-03-recap.md"]
    for name in sekaligus:
        (chain_repo / TD / name).unlink()
    for nn in ("01", "02", "03"):
        assert be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--nn", nn).returncode == 0
    satu_satu = {n: (chain_repo / TD / n).read_text(encoding="utf-8") for n in _briefs(chain_repo)}
    assert sekaligus == satu_satu


@pytest.mark.regression("35 G1")
def test_g1_all_melewati_berkas_ada_dan_brief_terkunci(chain_repo):
    brief(chain_repo, "01", "lock", "DONE", body="# B\n## Objective\nCovers: — (PRD absen)\nFulfills: SC-1\n")
    commit(chain_repo, "fix(order): implement lock")
    _matrix(chain_repo, _row("02", "endpoint", ["SC-2"]), _row("03", "recap", ["SC-2"]), append=True)
    isi_02 = "---\ntitle: sudah diisi\n---\n# jangan ditimpa\n"
    write_files(chain_repo, {f"{TD}/brief-02-endpoint.md": isi_02})
    out = _all(chain_repo)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "1 kerangka ditulis" in out.stdout
    assert "brief-01: `DONE` (terkunci)" in out.stdout and "brief-02-endpoint.md: sudah ada" in out.stdout
    assert (chain_repo / TD / "brief-02-endpoint.md").read_text(encoding="utf-8") == isi_02
    assert (chain_repo / TD / "brief-03-recap.md").is_file()
    again = _all(chain_repo)
    assert again.returncode == 0 and "0 kerangka ditulis" in again.stdout


@pytest.mark.regression("35 G1")
def test_g1_all_atomik_satu_baris_gagal_nol_jejak(chain_repo):
    """Kembar NN di satu baris → tidak ada kerangka, transisi SUPERSEDED, maupun pencabutan HALT yang mendarat."""
    brief(chain_repo, "01", "lock", "DONE")
    brief(chain_repo, "02", "endpoint", "DONE")
    brief(chain_repo, "03", "recap", "READY")
    write_files(chain_repo, {f"{TD}/.explore/brief-matrix.json": json.dumps({"briefs": [
        _row("01", "lock", ["SC-1"]), _row("02", "endpoint", ["SC-2"]), _row("03", "recap", ["SC-2"])]}),
        f"{TD}/HALT.md": HALT})
    commit(chain_repo, "chore(order-fix): tahan rantai di brief-02 (COMPILE)")
    _matrix(chain_repo, _row("04", "endpoint-compile-fix", ["— (perbaikan brief-02, HALT COMPILE)"], repairs="02"),
            _row("05", "recap", ["SC-2"], supersedes=["03"]), append=True)
    twin = chain_repo / TD / "brief-05-lama.md"
    twin.write_text("---\nstatus: READY\n---\n", encoding="utf-8")

    out = _all(chain_repo)
    assert out.returncode == 1
    assert "tidak satu kerangka pun ditulis" in out.stdout and "brief-05" in out.stdout
    assert not (chain_repo / TD / "brief-04-endpoint-compile-fix.md").exists()
    assert "status: READY" in (chain_repo / TD / "brief-03-recap.md").read_text(encoding="utf-8")
    assert "DICABUT" not in (chain_repo / TD / "HALT.md").read_text(encoding="utf-8")

    twin.unlink()
    out = _all(chain_repo)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "2 kerangka ditulis" in out.stdout
    assert "status: SUPERSEDED" in (chain_repo / TD / "brief-03-recap.md").read_text(encoding="utf-8")
    assert "status: DICABUT" in (chain_repo / TD / "HALT.md").read_text(encoding="utf-8")


@pytest.mark.regression("35 G1")
def test_g1_all_tanpa_matriks_dan_kombinasi_flag_ditolak(chain_repo):
    out = _all(chain_repo)
    assert out.returncode == 1 and "Matriks alokasi belum ada" in out.stdout
    assert be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--all", "--nn", "01").returncode == 2
    assert be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--all", "--force").returncode == 2


# -- G2: --open-round membawa state ronde -------------------------------------------------------


def _open(repo):
    return be_run(repo, VALIDATE, "--taskdir", TD, "--open-round")


def _state(repo):
    return json.loads((repo / TD / ".explore" / "brief-review-state.json").read_text(encoding="utf-8"))


@pytest.mark.regression("35 G2")
def test_g2_open_round_mencetak_state_dan_slot(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    out = _open(chain_repo)
    assert out.returncode == 0, out.stdout
    assert "ronde 1 dibuka" in out.stdout
    assert "ronde terpakai 0/2 (sisa 2, termasuk ronde ini) · taskdir 0/4" in out.stdout
    assert "brief berubah sejak ronde terakhir: brief-01-lock.md" in out.stdout
    assert "`{ronde}` = 1." in out.stdout and "{brief_berubah}" not in out.stdout


@pytest.mark.regression("35 G2")
def test_g2_ronde_lanjutan_tanpa_brief_berubah_tidak_dibuka(chain_repo):
    path = brief(chain_repo, "01", "lock", "READY")
    assert _open(chain_repo).returncode == 0
    assert be_run(chain_repo, VALIDATE, "--taskdir", TD, "--record-round", "Issues Found").returncode == 0
    before = _state(chain_repo)

    out = _open(chain_repo)
    assert out.returncode == 0, out.stdout
    assert "ronde tidak dibuka" in out.stdout and "tutup self-review tanpa dispatch" in out.stdout
    assert _state(chain_repo) == before, "state tidak disentuh"

    path.write_text(path.read_text(encoding="utf-8") + "\nperbaikan BLOCKER\n", encoding="utf-8")
    out = _open(chain_repo)
    assert out.returncode == 0, out.stdout
    assert "ronde 2 dibuka" in out.stdout and "ronde terpakai 1/2 (sisa 1" in out.stdout
    assert "brief berubah sejak ronde terakhir: brief-01-lock.md" in out.stdout
    assert "`{ronde}` = 2, `{brief_berubah}` = baris di atas." in out.stdout


@pytest.mark.regression("35 G2")
def test_g2_ronde_menggantung_diperingatkan(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    assert _open(chain_repo).returncode == 0
    out = _open(chain_repo)
    assert out.returncode == 0, out.stdout
    assert "ronde 1 dibuka" in out.stdout
    assert "ronde 1 sebelumnya terbuka tanpa vonis" in out.stdout


# -- G3/G4: prosa -------------------------------------------------------------------------------


def _skill():
    return (BE_SKILLS / "plan" / "SKILL.md").read_text(encoding="utf-8")


@pytest.mark.regression("35 G3")
def test_g3_gerbang_per_brief_hanya_brief_pertama():
    fase3 = _skill().split("### Fase 3", 1)[1].split("### Fase 4", 1)[0]
    assert "**Gerbang Brief Pertama**" in fase3
    assert "brief **pertama** batch" in fase3
    assert "tepat sesudah tiap brief selesai diisi" not in fase3
    fase5 = _skill().split("### Fase 5", 1)[1].split("## Guardrails", 1)[0]
    assert "--review-state`, buka ronde" not in fase5 and "--open-round" in fase5
    reviewer = (BE_SKILLS / "plan" / "dispatcher" / "reviewer.md").read_text(encoding="utf-8")
    slots = [line for line in reviewer.splitlines() if line.startswith(("| `{ronde}`", "| `{brief_berubah}`"))]
    assert len(slots) == 2 and all("--open-round" in s and "--review-state" not in s for s in slots)


@pytest.mark.regression("35 G4")
def test_g4_contoh_spec_di_skill_sah_bentuknya():
    fase3 = _skill().split("### Fase 3", 1)[1].split("### Fase 4", 1)[0]
    block = re.search(r"```json\n(.*?)```", fase3, re.S)
    assert block, "contoh brief-spec.json ada di Fase 3"
    spec = json.loads(block.group(1))
    mod = load_module(BE_SKILLS / "plan" / "scripts" / "scaffold_brief.py", "scaffold_brief_35")
    assert mod.spec_shape_problems(spec) == []
    known = set(mod.SPEC_LIST_FIELDS) | set(mod.SPEC_STR_FIELDS) | {"supersedes"}
    for row in spec["briefs"]:
        assert set(row) <= known, set(row) - known
        assert {"nn", "unit", "title", "risk", "covers", "fulfills", "consumes", "produces", "explore"} <= set(row)
        assert re.fullmatch(r"\d{2}", row["nn"]) and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", row["unit"])
