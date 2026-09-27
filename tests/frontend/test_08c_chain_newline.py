"""08c C3 — chain.py mempertahankan gaya line ending dokumen dan TASK.md."""
import pytest

from conftest import FE_SKILLS, git, run_script

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
    root = make_repo()
    git(root, "checkout", "-q", "-b", "main")
    git(root, "config", "core.autocrlf", "false")
    put(root, f"{TD}/TASK.md", TASK, crlf)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(label): kunci TASK sebagai akar rantai")
    put(root, f"{TD}/UI.md", UI, crlf)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(label): draft UI.md")
    return root


def approve(root):
    return run_script(CHAIN, "approve", "--taskdir", TD, "--row", "UI", "--answer", "Setujui desain",
                      "--root", str(root))


@pytest.mark.parametrize("crlf", [True, False])
def test_c3_approve_hanya_mengubah_satu_baris(make_repo, crlf):
    root = setup_ui(make_repo, crlf)
    proc = approve(root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    stat = git(root, "show", "--numstat", "--format=", "HEAD").split()
    assert stat == ["1", "1", f"{TD}/TASK.md", "1", "1", f"{TD}/UI.md"]
    for doc in ("UI.md", "TASK.md"):
        data = (root / TD / doc).read_bytes()
        assert (b"\r\n" in data) is crlf
    verify = run_script(CHAIN, "verify", "--taskdir", TD, "--rows", "UI", "--root", str(root))
    assert verify.returncode == 0, verify.stdout


def test_c3_reopen_mempertahankan_crlf(make_repo):
    root = setup_ui(make_repo, crlf=True)
    assert approve(root).returncode == 0
    proc = run_script(CHAIN, "reopen", "--taskdir", TD, "--row", "UI", "--reason", "revisi desain",
                      "--root", str(root))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    stat = git(root, "show", "--numstat", "--format=", "HEAD").split()
    assert stat == ["1", "1", f"{TD}/TASK.md", "1", "1", f"{TD}/UI.md"]


def test_c3_commit_gagal_memulihkan_byte_persis(make_repo):
    root = setup_ui(make_repo, crlf=True)
    before = {d: (root / TD / d).read_bytes() for d in ("UI.md", "TASK.md")}
    hook = root / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    proc = approve(root)
    assert proc.returncode == 1 and "gagal" in proc.stdout + proc.stderr
    assert {d: (root / TD / d).read_bytes() for d in before} == before
