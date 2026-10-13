"""08c C4 — taskdir_state.py: vonis tidak menyesatkan, tanpa kode mati."""
import json

from conftest import FE_SKILLS, commit, fe_profile, fe_seal_root, run_script, write_files

SCRIPT = FE_SKILLS / "lead" / "scripts" / "taskdir_state.py"
TD = "frontenddev/docs/2609240900-label"

TASK = """---
status: ACTIVE
lane: HOTFIX_MINOR
sections: []
created: 2026-09-24
---

# Label

## Description

Contoh.

## Success Criteria

- [ ] **SC-1**: label benar — verifikasi: test `A.test.ts` hijau

## Out of Scope

- Lainnya — di luar lingkup

## Chain

{row}
"""
OPEN_ROW = "- [ ] BRIEF    — frontend:plan          → brief-*.md"
BRIEF = "---\nstatus: {}\nfiles_touched: [src/a.ts]\n---\n\n# Brief\n"
# Brief MINOR yang lolos `validate_briefs.py` — approval ledger lewat `chain.py approve` sungguhan (12 J46).
VALID_BRIEF = """---
status: {status}
slug: label
stack: react-vite
based_on: {base} (2026-09-24)
order: 40
unit: "{nn}"
total_units: "2"
depends_on: []
fulfills: ["SC-1"]
covers: []
files_touched:
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


def state(root, *args):
    return run_script(SCRIPT, "--root", str(root), *args)


def test_c4_taskdir_yang_tidak_ada_bukan_akar(make_repo):
    proc = state(make_repo(), "--taskdir", "frontenddev/docs/2609240900-tidak-ada")
    assert "RUSAK" in proc.stdout and "direktori tidak ada" in proc.stdout
    assert "AKAR" not in proc.stdout


def test_c4_nama_di_luar_pola_dilaporkan_saat_pindai(make_repo):
    root = make_repo({"frontenddev/docs/2609240900-Order-Checkout/TASK.md": TASK.format(row=OPEN_ROW)})
    proc = state(root)
    assert "nol taskdir terbuka" not in proc.stdout
    assert "2609240900-Order-Checkout" in proc.stdout and "RUSAK" in proc.stdout


def test_c4_direktori_non_pola_kosong_tetap_diabaikan(make_repo):
    root = make_repo()
    (root / "frontenddev/docs/catatan").mkdir(parents=True)
    assert "nol taskdir terbuka" in state(root).stdout


def test_c4_repo_non_git_gagal_eksplisit(make_repo):
    root = make_repo({f"{TD}/TASK.md": TASK.format(row=OPEN_ROW)}, git_init=False)
    proc = state(root)
    assert proc.returncode == 1 and "bukan repo git" in proc.stdout
    proc = state(root, "--json")
    assert proc.returncode == 1 and json.loads(proc.stdout)["status"] == "FAIL"


def test_c4_blocked_tanpa_remedi_menang_atas_ready(make_repo):
    """Dulu ledger dicentang dengan materai tulisan tangan; sejak 12 J46 materai tanpa sidik tidak sah, jadi
    breakdown dicatat dan disetujui lewat `chain.py draft`/`approve` sungguhan (Langkah 24: tanpa commit)."""
    root = make_repo({"src/App.tsx": "export const App = () => null;\n"})
    fe_profile(root, "react-vite")
    write_files(root, {".claude/profile/frontenddev/commands.md": "| Perintah | Status |\n|---|---|\n| `pnpm test` | OK |\n"})
    base = commit(root, "init")
    write_files(root, {f"{TD}/TASK.md": TASK.format(row=OPEN_ROW)})
    fe_seal_root(root, TD)
    write_files(root, {f"{TD}/brief-01-label-a.md": VALID_BRIEF.format(status="READY", base=base, nn="01", name="LabelA"),
                       f"{TD}/brief-02-label-b.md": VALID_BRIEF.format(status="READY", base=base, nn="02", name="LabelB")})
    for args in (("draft", "--row", "BRIEF"), ("approve", "--row", "BRIEF", "--answer", "setuju")):
        proc = run_script(FE_SKILLS / "_common" / "chain.py", *args, "--taskdir", TD, cwd=root)
        assert proc.returncode == 0, proc.stdout
    write_files(root, {f"{TD}/brief-02-label-b.md": VALID_BRIEF.format(status="BLOCKED", base=base, nn="02",
                                                                     name="LabelB")})
    proc = state(root, "--taskdir", TD)
    assert "TERHENTI" in proc.stdout, proc.stdout


def test_c4_kode_mati_dibuang():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "def followups" not in src and "DILANJUTKAN" not in src and "successors" not in src


def test_24_akar_belum_terkunci_ke_task(make_repo):
    root = make_repo({f"{TD}/TASK.md": TASK.format(row=OPEN_ROW)})
    commit(root, "init", ".gitignore") if (root / ".gitignore").exists() else None
    proc = state(root, "--taskdir", TD)
    assert "AKAR" in proc.stdout and "chain.py root" in proc.stdout, proc.stdout


def test_24_warisan_era_git(make_repo):
    """Taskdir era git (tanpa `base_commit`/Riwayat): tuntas → TUNTAS warisan; berjalan → RUSAK (abandon)."""
    done = "frontenddev/docs/2609010000-lama"
    root = make_repo({f"{done}/TASK.md": TASK.format(row="- [x] BRIEF    — frontend:plan          → brief-*.md "
                                                         "@ READY abc1234"),
                      f"{done}/REPORT.md": "# Label — Report\n",
                      f"{TD}/TASK.md": TASK.format(row="- [x] BRIEF    — frontend:plan          → brief-*.md "
                                                       "@ READY abc1234")})
    rows = {r["taskdir"]: r for r in json.loads(state(root, "--all", "--json").stdout)}
    assert rows[done]["state"] == "TUNTAS" and "warisan" in rows[done]["detail"], rows[done]
    assert rows[TD]["state"] == "RUSAK" and "abandon" in rows[TD]["next"], rows[TD]


def test_24_dokumen_ter_track_rute_migrasi(make_repo):
    root = make_repo({f"{TD}/TASK.md": TASK.format(row=OPEN_ROW)})
    commit(root, "docs: era git")
    proc = state(root, "--json")
    assert proc.returncode == 1 and "MIGRASI" in json.loads(proc.stdout)["error"]
