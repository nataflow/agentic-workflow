"""Langkah 12 Tahap 5 — orkestrasi & prosa frontend (J42/J43 prosa, J54–J58, sisa tahap 1/3/4, rilis)."""
import json
import re
from types import SimpleNamespace

import pytest

from conftest import FE_SKILLS, PLUGINS, REPO, commit, fe_profile, git, load_module, run_script, write_files

FE = PLUGINS / "frontend"
TD = "frontenddev/docs/2609270900-label"
STATE = FE_SKILLS / "lead" / "scripts" / "taskdir_state.py"
ARCHITECT = FE_SKILLS / "architect" / "scripts" / "check_preconditions.py"
CHAIN = FE_SKILLS / "_common" / "chain.py"
VALIDATE_BRIEFS = FE_SKILLS / "plan" / "scripts" / "validate_briefs.py"

TASK = """---
status: {status}
lane: HOTFIX_MINOR
sections: []
created: 2026-09-27
---

# Label

## Description

Contoh (`src/App.tsx:1`).

## Success Criteria

- [ ] **SC-1**: label benar — verifikasi: test `LabelA.test.tsx` hijau

## Out of Scope

- Lainnya — di luar lingkup

## Chain

{row}
"""
OPEN_ROW = "- [ ] BRIEF    — frontend:plan          → brief-*.md"

BRIEF = """---
status: {status}
slug: label
stack: react-vite
based_on: {base} (2026-09-27)
order: 40
unit: "{nn}"
total_units: "{total}"
depends_on: [{deps}]
fulfills: ["SC-1"]
covers: []
{remedies}files_touched:
  - src/features/label/{name}.tsx
  - src/features/label/{name}.test.tsx
verification:
  - pnpm test
---

# Implementation Brief — Unit {nn}: {name}

Brief implementasi atomik untuk subagent `code-implementor`; satu-satunya acuan kerjanya.

## 1. Intent & Scope Boundaries
- **Intent**: menambah komponen {name}.
- **Akar**: `SC-1` (frontmatter `fulfills`)
- **Strict Scope Boundaries**: hanya berkas `files_touched`.
- **Out of Scope (Dikerjakan pada Unit Lain)**: tidak ada

## 2. Interfaces & Contracts

```typescript
export interface {name}UI {{ label: string }}
```

## 3. Current Repo State & Reference Symbols

| Aksi | Berkas | Anchor |
|---|---|---|
| CREATE | `src/features/label/{name}.tsx` | — |
| CREATE | `src/features/label/{name}.test.tsx` | — |

- **Pola Acuan**: `src/App.tsx:1` komponen fungsi
- **Import Alias**: `@/`

## 4. Implementation Steps
1. Tulis komponen {name} yang merender label.
2. Tulis test render label.

## 5. Done Criteria & Verification Baseline
- [ ] label benar
- [ ] (verifikasi penutup) pnpm test — nol galat baru
"""

REPORT = """---
artifact: UNIT_REPORT
unit: "{nn}"
brief: brief-{nn}-label-a.md
status: DONE
---

# Unit {nn} — label-a

## Changes
- `src/features/label/LabelA.tsx` — CREATE — simbol: `LabelA` — komponen

## Verification
- `pnpm test` → DITUNDA (verifikasi penutup)

## Done Criteria
- label benar → Terpenuhi

## Out of Scope / Mismatch
- Tidak ada

## Rollback
- Tidak perlu
"""


def brief(base: str, nn: str, name: str, status: str = "READY", total: int = 1, deps: str = "",
          remedies: str = "") -> str:
    return BRIEF.format(status=status, base=base, nn=nn, name=name, total=total, deps=deps,
                        remedies=f'remedies: "{remedies}"\n' if remedies else "")


def minor_root(make_repo, status: str = "ACTIVE", row: str = OPEN_ROW):
    root = make_repo({".gitignore": ".explore/\n", f"{TD}/TASK.md": TASK.format(status=status, row=row),
                      "src/App.tsx": "export const App = () => null;\n"})
    fe_profile(root, "react-vite")
    write_files(root, {".claude/profile/frontenddev/commands.md":
                       "| Perintah | Status |\n|---|---|\n| `pnpm test` | OK |\n"})
    git(root, "checkout", "-q", "-b", "main")
    base = commit(root, "docs(label): kunci TASK sebagai akar rantai")
    return root, base


def approve_brief(root):
    proc = run_script(CHAIN, "approve", "--taskdir", TD, "--row", "BRIEF", "--answer", "setuju", cwd=root)
    assert proc.returncode == 0, proc.stdout


def architect(root, *args):
    proc = run_script(ARCHITECT, "--taskdir", TD, "--root", str(root), "--json", *args)
    return json.loads(proc.stdout)


def check(data, cid):
    return next(c for c in data["checks"] if c["id"] == cid)


def read(path):
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


# --- Sisa tahap 3: TERHENTI tidak tertutupi validate_briefs ----------------------------------

@pytest.mark.regression("J20")
def test_architect_terhenti_dilaporkan_sebelum_validate_briefs(make_repo):
    """Brief tunggal BLOCKED: SC-1 tak lagi dipikul (Check G FAIL), tetapi fase yang dilaporkan tetap
    `TERHENTI` beserta rute reopen BRIEF → plan APPEND, bukan "validate_briefs.py FAIL"."""
    root, base = minor_root(make_repo)
    write_files(root, {f"{TD}/brief-01-label-a.md": brief(base, "01", "LabelA")})
    commit(root, "docs(label): draft breakdown (1 briefs)")
    approve_brief(root)
    write_files(root, {f"{TD}/brief-01-label-a.md": brief(base, "01", "LabelA", status="BLOCKED")})
    commit(root, "docs(label): unit 01 BLOCKED - galat")
    data = architect(root)
    c4 = check(data, 4)
    assert data["phase"] == "TERHENTI (brief-01 BLOCKED)", c4
    assert c4["status"] == "FAIL" and "BLOCKED tanpa remedi" in c4["summary"], c4
    assert "reopen --row BRIEF" in c4["action"] and "APPEND" in c4["action"]


# --- J58(c): DAG buntu ---------------------------------------------------------------------

def dag_taskdir(make_repo):
    """Ledger BRIEF `[x]`; brief 01 BLOCKED, remedinya 02 READY bergantung pada 01 — tidak pernah dapat berangkat."""
    lib = load_module(FE_SKILLS / "_common" / "precondition_lib.py", "pl_12_dag")
    root, base = minor_root(make_repo, row=lib.chain_line("BRIEF", "x", "READY abc1234"))
    write_files(root, {f"{TD}/brief-01-label-a.md": brief(base, "01", "LabelA", status="BLOCKED", total=2),
                       f"{TD}/brief-02-label-b.md": brief(base, "02", "LabelB", total=2, deps='"01"',
                                                          remedies="01")})
    commit(root, "docs(label): brief legacy")
    return root, base


@pytest.mark.regression("J58")
def test_j58c_runnable_briefs(make_repo):
    root, base = dag_taskdir(make_repo)
    lib = load_module(FE_SKILLS / "_common" / "precondition_lib.py", "pl_12_run")
    assert lib.runnable_briefs(root / TD, root) == []
    write_files(root, {f"{TD}/brief-02-label-b.md": brief(base, "02", "LabelB", total=2, remedies="01")})
    assert lib.runnable_briefs(root / TD, root) == ["02"]


@pytest.mark.regression("J58")
def test_j58c_taskdir_state_dag_terhenti(make_repo, monkeypatch):
    root, _ = dag_taskdir(make_repo)
    mod = load_module(STATE, "tds_12_dag")
    monkeypatch.setattr(mod, "verify_chain_row", lambda *a, **k: "")   # ledger legacy dianggap sah
    out = mod.classify(root, TD)
    assert out["state"] == "TERHENTI" and "DAG" in out["detail"], out
    assert "reopen --row BRIEF" in out["next"] and "APPEND" in out["next"]


@pytest.mark.regression("J58")
def test_j58c_check_d_menolak_remedi_bergantung_pada_unit_asal(make_repo):
    root, _ = dag_taskdir(make_repo)
    proc = run_script(VALIDATE_BRIEFS, "--taskdir", TD, "--root", str(root), "--json")
    d = next(c for c in json.loads(proc.stdout)["checks"] if c["id"] == "D")
    assert d["status"] == "FAIL", d
    assert any("brief-02" in x and "01" in x and "remedi" in x for x in d["details"]), d


# --- J58(b): RUSAK punya jalan keluar per jenis --------------------------------------------

@pytest.mark.regression("J58")
def test_j58b_rusak_nama_di_luar_pola_dipindah_bukan_abandon(make_repo):
    root = make_repo({"frontenddev/docs/2609270900-Label/TASK.md": TASK.format(status="ACTIVE", row=OPEN_ROW)})
    commit(root, "docs(Label): kunci TASK sebagai akar rantai")
    out = run_script(STATE, "--root", str(root), "--json")
    row = json.loads(out.stdout)[0]
    assert row["state"] == "RUSAK"
    assert "abandon" not in row["next"] and "memindahkan" in row["next"], row


@pytest.mark.regression("J58")
def test_j58b_rusak_berakar_ditutup_lewat_abandon(make_repo):
    root, _ = minor_root(make_repo, status="PAUSED")
    row = json.loads(run_script(STATE, "--root", str(root), "--json").stdout)[0]
    assert row["state"] == "RUSAK" and "abandon" in row["next"] and "taskdir baru" in row["next"], row


# --- J55: artefak verifikasi di tree -------------------------------------------------------

@pytest.mark.regression("J55")
def test_j55_artefak_verifikasi_ditahan_sebelum_reviewer(make_repo):
    root, base = minor_root(make_repo)
    rel = f"{TD}/brief-01-label-a.md"
    write_files(root, {rel: brief(base, "01", "LabelA")})
    commit(root, "docs(label): draft breakdown (1 briefs)")
    approve_brief(root)
    write_files(root, {rel: brief(base, "01", "LabelA", status="DONE"),
                       f"{TD}/report-01.md": REPORT.format(nn="01"),
                       "src/features/label/LabelA.tsx": "export const LabelA = () => null;\n",
                       "src/features/label/LabelA.test.tsx": "it('x', () => expect(1).toBe(1));\n"})
    commit(root, "feat(label): implement unit 01 - label-a")
    assert architect(root)["phase"] == "PENUTUP"
    write_files(root, {"src/features/label/__snapshots__/LabelA.test.tsx.snap": "// snap\n"})
    data = architect(root)
    c8 = check(data, 8)
    assert c8["status"] == "FAIL" and "__snapshots__" in c8["summary"], c8
    assert "verifikasi penutup" in c8["action"] and "AskUserQuestion" in c8["action"], c8


def test_j55_prosa_prasyarat_diulang_sebelum_reviewer():
    phase4 = section(read(FE_SKILLS / "architect" / "SKILL.md"), "### Phase 4")
    assert "check_preconditions.py --taskdir" in phase4 and "Check 8" in phase4
    assert phase4.index("Tree sesudah verifikasi") < phase4.index("dispatcher/reviewer.md")
    assert "Check 8" in read(FE_SKILLS / "architect" / "dispatcher" / "reviewer.md")
    assert "Check 8" in section(read(FE_SKILLS / "architect" / "references" / "execution-protocol.md"),
                                "## 7. Verifikasi Penutup")


# --- J54: merah tanpa berkas punya rute ----------------------------------------------------

@pytest.mark.regression("J54")
def test_j54_merah_tanpa_berkas_punya_rute():
    skill = read(FE_SKILLS / "architect" / "SKILL.md")
    phase4 = section(skill, "### Phase 4")
    for token in ("126/127", "`TIMEOUT`", "ekor log", "AskUserQuestion"):
        assert token in phase4, token
    fp5 = skill.split("5. **Perintah verifikasi melewati batas waktu**", 1)[1].split("\n6. ", 1)[0]
    assert "3× lipat" in fp5 and "AskUserQuestion" in fp5 and "tidak punya opsi" in fp5
    proto = section(read(FE_SKILLS / "architect" / "references" / "execution-protocol.md"),
                    "## 7. Verifikasi Penutup")
    for token in ("126/127", "`TIMEOUT`", "ekor log"):
        assert token in proto, token


# --- J56: dispatcher explorer memakai git check-ignore -------------------------------------

@pytest.mark.regression("J56")
@pytest.mark.parametrize("skill", ["lead", "ux-design", "ui-design", "contract", "plan"])
def test_j56_explorer_memakai_check_ignore(skill):
    text = read(FE_SKILLS / skill / "dispatcher" / "explorer.md")
    assert "git check-ignore -q" in text
    assert "memuat baris `.frontenddev/`" not in text


# --- J57: satu profil, satu app ------------------------------------------------------------

@pytest.mark.regression("J57")
def test_j57_prosa_tidak_menjanjikan_profil_per_app():
    matrix = read(FE_SKILLS / "lead" / "references" / "lane-routing-matrix.md")
    assert "masing-masing dengan profil app-nya" not in matrix
    assert "Satu Profil, Satu App" in matrix


# --- J58 (a), (d)–(h) ----------------------------------------------------------------------

@pytest.mark.regression("J58")
def test_j58a_chain_tidak_merujuk_phase_7():
    assert "Phase 7" not in read(CHAIN)


@pytest.mark.regression("J58")
@pytest.mark.parametrize("skill", ["lead", "ux-design", "ui-design", "contract", "plan"])
def test_j58d_subagent_type_explorer_disebut(skill):
    assert "`frontend:code-explorer`" in read(FE_SKILLS / skill / "SKILL.md")


@pytest.mark.regression("J58")
def test_j58e_review_adapter_hilang_berhenti_di_prasyarat():
    fp = read(FE_SKILLS / "review" / "SKILL.md").split("## Failure path", 1)[1]
    assert "dimensi generik saja, tandai" not in fp and "hentikan di Precondition" in fp


@pytest.mark.regression("J58")
def test_j58f_explore_fact_tanpa_profil():
    gate_text = load_module(FE / "hooks" / "gate_text.py", "gt_12_fe")
    prof = SimpleNamespace(state="ABSENT", location="own", stack="", owner="", missing=[])
    text = gate_text.render(SimpleNamespace(stack="react-vite", source="package.json", hits=[], profile=prof))
    assert "EXPLORE_FACT" in text and "GENERATE" in text
    lead = read(FE_SKILLS / "lead" / "SKILL.md")
    assert "EXPLORE_FACT" in lead.split("## Failure path", 1)[1].split("\n2. ", 1)[0]


@pytest.mark.regression("J58")
def test_j58g_plan_tidak_menjalankan_perintah():
    plan = read(FE_SKILLS / "plan" / "SKILL.md")
    assert "jalankan perintah `commands.md` profil sekali" not in plan
    assert "plan **tidak** menjalankan perintah" in plan


WORDS = {"lima": 5, "enam": 6, "tujuh": 7, "delapan": 8}


@pytest.mark.regression("J58")
def test_j58h_hitungan_readme_sesuai_tabel():
    body = section(read(FE / "README.md"), "## Mechanical Enforcement")
    m = re.search(r"Di atasnya (\w+) penjaga", body)
    assert m, "kalimat hitungan penjaga tidak ditemukan"
    table = body.split(m.group(0), 1)[1].split("\n\n", 2)[1]
    rows = [l for l in table.splitlines() if l.startswith("| `")]
    assert WORDS[m.group(1)] == len(rows), (m.group(1), len(rows))


# --- J42/J43 prosa (H28) -------------------------------------------------------------------

@pytest.mark.regression("J43")
def test_j43_amandemen_akar_bukan_jalan_keluar_plafon():
    hits = [str(p.relative_to(FE)) for p in FE.rglob("*.md")
            if "klarifikasi lingkup: amandemen akar" in read(p) or "amandemen akar / abandon" in read(p)]
    assert not hits, hits
    lead = read(FE_SKILLS / "lead" / "SKILL.md")
    phase8 = section(lead, "### Phase 8")
    assert "Plafon habis" in phase8 and "taskdir baru" in phase8 and "AskUserQuestion" in phase8


@pytest.mark.regression("J42")
def test_j42_putaran_baru_sesudah_reopen_hulu_disebut():
    for rel in ("contract/SKILL.md", "plan/SKILL.md", "lead/references/lane-routing-matrix.md"):
        assert "hop di atasnya" in read(FE_SKILLS / rel), rel


# --- Sisa tahap 4 --------------------------------------------------------------------------

@pytest.mark.regression("J45")
def test_j45_contract_reviewer_menggemakan_sidik():
    fmt = read(FE / "agents" / "contract-reviewer.md").split("## Format Output", 1)[1]
    assert "- Sidik:" in fmt


@pytest.mark.regression("J49")
def test_j49_lead_sufiks_slug_kembar():
    assert "`-2`" in section(read(FE_SKILLS / "lead" / "SKILL.md"), "### Phase 5")


# --- Sisa tahap 1 & rilis ------------------------------------------------------------------

@pytest.mark.regression("J4")
def test_j4_pola_ignore_berjangkar_di_protokol():
    proto = read(FE_SKILLS / "architect" / "references" / "execution-protocol.md")
    assert "`/.frontenddev/`" in proto and "`frontenddev/docs/**/.explore/`" in proto


@pytest.mark.regression("J1")
def test_readme_pagar_sesuai_hook():
    readme = read(FE / "README.md")
    guard = [l for l in readme.splitlines() if l.startswith("| `hooks/guard_bash.py`")]
    assert guard and "`grep`" not in guard[0]
    assert "code-implementor" in guard[0] and "doc-reviewer" in guard[0] and "code-explorer" in guard[0]


def test_readme_catatan_upgrade():
    readme = read(FE / "README.md")
    assert "0.8.0" in readme and "Sidik:" in readme and "`head`" in readme


def test_versi_rilis():
    fe = json.loads(read(FE / ".claude-plugin" / "plugin.json"))
    be = json.loads(read(PLUGINS / "backend" / ".claude-plugin" / "plugin.json"))
    assert (fe["version"], be["version"]) == ("0.9.0", "0.10.0")


def test_flow_frontend_menyebut_perilaku_baru():
    flow = read(REPO / "flow" / "frontend.md")
    for token in ("Sidik:", "TERHENTI", "DAG", "126/127", "git check-ignore", "taskdir baru"):
        assert token in flow, token
