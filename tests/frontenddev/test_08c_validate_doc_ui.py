"""08c C2 — validate_doc.py --kind ui menagih enam cabang PER LAYAR."""
import pytest

from conftest import FE_SKILLS, run_script, write_files

TD = "frontenddev/docs/2609240900-label"

SIX = ["Normal (Data Terisi / Ready)", "Loading (Skeleton Shimmer)", "Kosong (Empty State)",
       "Error (Connection / Server Failure)", "Initial / Idle", "Stale / Mutating (Optimistic Overlay)"]

HEAD = """---
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

"""
TAIL = """
## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)

| Elemen UI | Field Data yang Ditampilkan | Asal Sumber Data | Keterangan & Transformasi |
|---|---|---|---|
| Baris | `name` | View-Model | apa adanya |

## 5. Batasan State Scope & Isolasi Komponen
- **Koordinasi Sentral**: `useLabelPage`.
"""


def validate(make_repo, titles):
    body = "".join(f"### ST-{i}. State {t}\n- Perilaku.\n\n" for i, t in enumerate(titles, 1))
    root = make_repo({f"{TD}/UI.md": HEAD + body + TAIL})
    return run_script(FE_SKILLS / "_common/validate_doc.py", "--kind", "ui", "--taskdir", TD, "--root", str(root))


@pytest.mark.parametrize("titles", [SIX, SIX + SIX, SIX[::-1], SIX + SIX[3:] + SIX[:3],
                                    SIX + [f"{k} — Layar 2: Pembayaran" for k in
                                           ("Normal", "Loading", "Kosong", "Error", "Initial", "Mutating")]])
def test_c2_lolos_bila_tiap_layar_enam_cabang(make_repo, titles):
    proc = validate(make_repo, titles)
    assert proc.returncode == 0, proc.stdout


def test_c2_layar_kedua_hanya_satu_cabang_gagal(make_repo):
    proc = validate(make_repo, SIX + ["Normal — Layar 2: Pembayaran"])
    assert proc.returncode == 1
    assert "layar 2 (ST-7..ST-7): cabang hilang — loading, kosong, error, initial, stale/mutating" in proc.stdout


def test_c2_cabang_ganda_dan_hilang_dalam_satu_layar_gagal(make_repo):
    titles = list(SIX)
    titles[2] = "Loading Ulang (Skeleton)"
    proc = validate(make_repo, titles)
    assert proc.returncode == 1
    assert "cabang `loading` ganda (ST-2, ST-3)" in proc.stdout
    assert "cabang hilang — kosong" in proc.stdout


def test_c2_kurang_dari_enam_tetap_gagal(make_repo):
    proc = validate(make_repo, SIX[:4])
    assert proc.returncode == 1
    assert "cabang hilang — initial, stale/mutating" in proc.stdout


def test_c2_judul_tanpa_jenis_cabang_dilaporkan(make_repo):
    titles = list(SIX)
    titles[4] = "Awalan Layar"
    proc = validate(make_repo, titles)
    assert proc.returncode == 1
    assert "judul `ST-5` tidak menyebut jenis cabang" in proc.stdout
