"""08c C3 — chain.py mempertahankan gaya line ending dokumen dan TASK.md, dan hanya menyentuh baris miliknya."""
import difflib
import sys

import pytest

from conftest import FE_SKILLS, fe_seal_root, git, run_script

TD = "frontenddev/docs/2609240900-label"
CHAIN = FE_SKILLS / "_common" / "chain.py"

TASK = """---
status: ACTIVE
lane: FULL_PIPELINE
sections: [ui]
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

- [ ] UI       — frontend:ui-design     → UI.md
- [ ] CONTRACT — frontend:contract      → CONTRACT.md
- [ ] BRIEF    — frontend:plan          → brief-*.md
"""

UI = """---
status: DRAFT
slug: label
order: 20
stack: react-vite
based_on: 3f9c2ab (2026-09-23)
---

# UI Design — Label

Rancangan.

## 1. Mockup Antarmuka (Layout Mockup ASCII)

```
+---+
```

## 2. Hierarki Prioritas Informasi (Information Priority)

| Elemen Antarmuka Pengguna | Tingkat Prioritas | Bobot Visual & Penempatan | Alasan Desain |
|---|---|---|---|
| CTA | Primary (P1) | `button.primary` | Aksi utama |

## 3. Cabang State Tampilan (The 6-State Branches Matrix)

""" + "".join(f"### ST-{i}. State {t}\n- Perilaku.\n\n" for i, t in enumerate(
    ["Normal (Ready)", "Loading (Skeleton)", "Kosong (Empty)", "Error (Failure)", "Initial / Idle",
     "Stale / Mutating"], 1)) + """## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)

| Elemen UI | Field Data yang Ditampilkan | Asal Sumber Data | Keterangan & Transformasi |
|---|---|---|---|
| Baris | `name` | View-Model | apa adanya |

## 5. Batasan State Scope & Isolasi Komponen
- **Koordinasi Sentral**: `useLabelPage`.
"""


def put(root, rel, text, crlf):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\n", "\r\n" if crlf else "\n").encode("utf-8"))


def setup_ui(make_repo, crlf):
    """Akar terkunci di disk dan draft `UI.md` tercatat (`chain.py draft`), seperti jalur `ui-design`."""
    root = make_repo()
    git(root, "checkout", "-q", "-b", "main")
    git(root, "config", "core.autocrlf", "false")
    git(root, "commit", "-q", "--allow-empty", "-m", "init")
    put(root, f"{TD}/TASK.md", TASK, crlf)
    fe_seal_root(root, TD)
    put(root, f"{TD}/UI.md", UI, crlf)
    proc = run_script(CHAIN, "draft", "--taskdir", TD, "--row", "UI", "--root", str(root))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return root


def approve(root):
    return run_script(CHAIN, "approve", "--taskdir", TD, "--row", "UI", "--answer", "Setujui desain",
                      "--root", str(root))


def snapshot(root):
    return {d: (root / TD / d).read_bytes() for d in ("UI.md", "TASK.md")}


def changed(before, after, doc):
    """(baris diganti/dihapus, baris ditambah) antara dua isi berkas."""
    a, b = before[doc].decode("utf-8").splitlines(), after[doc].decode("utf-8").splitlines()
    diff = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    return sum(1 for l in diff if l.startswith("-")), sum(1 for l in diff if l.startswith("+"))


@pytest.mark.parametrize("crlf", [True, False])
def test_c3_approve_hanya_mengubah_satu_baris(make_repo, crlf):
    root = setup_ui(make_repo, crlf)
    before = snapshot(root)
    proc = approve(root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = snapshot(root)
    assert changed(before, after, "UI.md") == (1, 1)                  # baris `status:`
    assert changed(before, after, "TASK.md") == (1, 2)                # baris ledger + satu kejadian Riwayat
    for doc in ("UI.md", "TASK.md"):
        assert (b"\r\n" in after[doc]) is crlf
    verify = run_script(CHAIN, "verify", "--taskdir", TD, "--rows", "UI", "--root", str(root))
    assert verify.returncode == 0, verify.stdout
    assert git(root, "status", "--porcelain") == "", "approve tidak menyentuh git (Langkah 24)"


def test_c3_reopen_mempertahankan_crlf(make_repo):
    root = setup_ui(make_repo, crlf=True)
    assert approve(root).returncode == 0
    before = snapshot(root)
    proc = run_script(CHAIN, "reopen", "--taskdir", TD, "--row", "UI", "--reason", "revisi desain",
                      "--root", str(root))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = snapshot(root)
    assert changed(before, after, "UI.md") == (1, 1) and changed(before, after, "TASK.md") == (1, 2)
    assert all(b"\r\n" in data for data in after.values())


def test_c3_tulis_gagal_memulihkan_byte_persis(make_repo, monkeypatch):
    root = setup_ui(make_repo, crlf=True)
    before = snapshot(root)
    sys.path.insert(0, str(FE_SKILLS / "_common"))
    import chain as chain_mod
    real = chain_mod.write_keep_newline

    def flaky(path, text):
        if path.name == "TASK.md":
            raise OSError("disk penuh")
        return real(path, text)

    monkeypatch.setattr(chain_mod, "write_keep_newline", flaky)
    with pytest.raises(chain_mod.ChainError, match="dipulihkan"):
        chain_mod.Chain(TD, root).approve("UI", "Setujui desain")
    monkeypatch.undo()
    assert snapshot(root) == before
