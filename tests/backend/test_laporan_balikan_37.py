"""Langkah 37 — laporan unit lewat balikan (backend B1–B2): implementor membawa badan laporan jalur gagal di amplop,
`architect` menyimpannya ke `report-NN.md`.

Harness Claude Code menolak subagent menulis berkas laporan ("Subagents should return findings as text"), sehingga
jalur `BLOCKED` — satu-satunya jalur yang menulis `report-NN.md` — kehilangan laporannya.
"""
import pytest

from conftest import PLUGINS

BE = PLUGINS / "backend"
SECTIONS = ("## Stop condition / Trigger", "## Evidence", "## Working Tree & Partial Changes",
            "## Root Cause & Recommended Action")


def _read(rel):
    return (BE / rel).read_text(encoding="utf-8")


@pytest.mark.regression("37 B1")
def test_b1_implementor_membawa_badan_laporan_di_amplop():
    agent = _read("agents/code-implementor.md")
    assert "Tulis alasannya ke `{taskdir}/report-{NN}.md`" not in agent
    assert "Report File:" not in agent
    assert "Berkas laporan `{taskdir}/report-{NN}.md` tidak pernah kau tulis" in agent
    out = agent.split("## Format Output", 1)[1]
    assert "**badan laporan** utuh" in out and "Plafon 10 baris hanya untuk jalur sukses" in out
    assert all(f"`{s}`" in out for s in SECTIONS) and "Umpan balik profil:" in out
    disp = _read("skills/architect/dispatcher/implementor.md")
    assert "jangan menulis `report-<NN>.md`" in disp and "lebih dulu lalu\n  menyebut path-nya" not in disp


@pytest.mark.regression("37 B2")
def test_b2_architect_menyimpan_laporan_sebelum_matriks():
    recovery = _read("skills/architect/references/lifecycle-recovery.md")
    matriks = recovery.split("### Matriks Bukti Disk untuk Amplop `BLOCKED`", 1)[1].split("| --- |", 1)[0]
    assert "**disalin persis**" in matriks and "badan laporan tidak dikirim implementor" in matriks
    struktur = recovery.split("### Struktur Laporan Kegagalan", 1)[1]
    assert "ditulis `architect`, salinan persis badan laporan amplop `code-implementor`" in struktur
    triase = _read("skills/architect/SKILL.md").split("3. **Triase `BLOCKED`**", 1)[1].split("\n", 1)[0]
    assert "simpan dulu `{taskdir}/report-<NN>.md`" in triase and "salin persis" in triase


@pytest.mark.regression("37 B2")
def test_b2_lease_tanpa_report_nn():
    guard = _read("hooks/guard_bash.py")
    assert 'f"report-{nn.group(1)}.md"' not in guard
    assert "tanpa `report-NN.md`" in guard


# ------------------------------------------------------------------ E1 — slug laci explorer tanpa awalan `report`

@pytest.mark.regression("37 E1")
@pytest.mark.parametrize("slug, code", [("report-dcc-hasil", 1), ("Report-mingguan", 1), ("telusur-report-dcc", 0),
                                        ("order-report", 0)])
def test_e1_render_prompt_menolak_slug_berawalan_report(tmp_path, slug, code):
    import json
    import subprocess
    import sys
    td = "backenddev/docs/2611160900-x"
    out = subprocess.run([sys.executable, str(BE / "skills/_common/render_prompt.py"),
                          "--template", str(BE / "skills/plan/dispatcher/explorer.md"),
                          "--slot", "objective=o", "--slot", f"taskdir={td}", "--slot", f"slug={slug}",
                          "--slot", "resep_navigasi=- r",
                          "--out", f"{td}/.explore/prompt/p.md", "--root", str(tmp_path), "--json"],
                         capture_output=True, text=True)
    assert out.returncode == code, out.stdout + out.stderr
    if code:
        assert "telusur-" in json.loads(out.stdout)["reason"]
