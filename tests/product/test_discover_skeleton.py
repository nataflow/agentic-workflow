"""Kerangka `charter.py new` sama dengan bagian 1 template discover; gerbang `check` memakai berkas plugin nyata."""
import pytest

from conftest import PLUGINS
from product_helpers import CONTEXT, TD, charter, empty_ws, path_of, resolved, validate, ws  # noqa: F401

SKILLS = PLUGINS / "product" / "skills"
SKELETON = SKILLS / "discover" / "templates" / "charter-skeleton.md"
LABELS = {
    "NEW_PRODUCT": ("Untuk siapa", "Masalah utama", "Domain"),
    "NEW_FEATURE": ("Pengguna", "Yang belum bisa dilakukan", "Area"),
    "IMPROVEMENT": ("Yang terdampak", "Yang salah atau kurang", "Fitur"),
}


def _block() -> list:
    text = SKELETON.read_text(encoding="utf-8").split("\n## 1. ", 1)[1]
    return text.split("````markdown\n", 1)[1].split("\n````", 1)[0].splitlines()


def test_kerangka_skrip_sama_dengan_template(ws):
    assert ws.new(request="Tolong buatkan aplikasi kasir.").returncode == 0
    got = path_of(ws.root).read_text(encoding="utf-8").rstrip("\n").splitlines()
    want = _block()
    assert len(got) == len(want), (got, want)
    for w, g in zip(want, got):
        if w.startswith("- **"):                                  # label Konteks Awal berbeda per mode
            continue
        if "<" in w and ">" in w and not w.startswith("|"):      # slot template: cukup awalan barisnya
            assert g.startswith(w.split("<", 1)[0]) and g != w.split("<", 1)[0], (w, g)
        else:
            assert g == w, (w, g)
    konteks = [l for l in got if l.startswith("- **")]
    assert [l.split("**")[1] for l in konteks] == list(LABELS[ws.mode])
    assert [l.split(": ", 1)[1] for l in konteks] == list(CONTEXT[ws.mode])


def test_tabel_label_template_sama_dengan_skrip():
    text = SKELETON.read_text(encoding="utf-8")
    for mode in ("NEW_FEATURE", "IMPROVEMENT"):
        row = next(l for l in text.splitlines() if l.startswith(f"| `{mode}` |"))
        assert [c.strip().strip("`") for c in row.strip("|").split("|")[1:]] == list(LABELS[mode])


@pytest.mark.parametrize("gate", ["discover", "spec"])
def test_berkas_gate_lengkap(empty_ws, gate):
    assert empty_ws.new().returncode == 0
    proc = charter(empty_ws.root, "check", "--gate", gate, "--charterdir", TD)
    line = next(l for l in proc.stdout.splitlines() if "Berkas plugin" in l)
    assert ": PASS" in line, proc.stdout


def test_check_spec_pass_sesudah_close(ws):
    ws.to_closed()
    proc = charter(ws.root, "check", "--gate", "spec", "--charterdir", TD)
    assert proc.returncode == 0, proc.stdout
    r = resolved(proc.stdout)
    assert r["mode"] == ws.mode and r["kartu"] == "belum" and r["ronde"] == "1" and r["review_basi"] == "belum"


def test_check_discover_menolak_charter_tertutup(ws):
    ws.to_closed()
    proc = charter(ws.root, "check", "--gate", "discover", "--charterdir", TD)
    assert proc.returncode == 1 and "reopen --to elicitation" in proc.stdout


TEMPLATE = SKILLS / "spec" / "templates" / "charter-template.md"


def test_contoh_template_improvement_lolos_validator(ws):
    """Contoh terisi bagian 3 template kartu wajib lolos validator: model meniru bentuknya apa adanya."""
    if ws.mode != "IMPROVEMENT":
        pytest.skip("contoh template bermode IMPROVEMENT")
    example = TEMPLATE.read_text(encoding="utf-8").split("\n## 3. ", 1)[1]
    example = example.split("```markdown\n", 1)[1].split("\n```", 1)[0]
    for rel in ("src/retur/form.go", "src/retur/approval.go"):
        (ws.root / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws.root / rel).write_text("package retur\n" * 60, encoding="utf-8")
    ws.to_closed()
    p = path_of(ws.root)
    text = p.read_text(encoding="utf-8")
    head, notes = text.split("# Pencatatan keuangan UMKM\n", 1)
    p.write_text(head + example + "\n\n" + notes.lstrip("\n"), encoding="utf-8")
    proc = validate(ws.root, "charter")
    assert proc.returncode == 0, proc.stdout
