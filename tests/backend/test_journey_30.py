"""Langkah 30 J1: `_common/journey.py` — catatan keputusan antar sesi di `<taskdir>/JOURNEY.md`."""
import json

import pytest

from conftest import BE_SKILLS, TD, git, load_module, run_script

JOURNEY = BE_SKILLS / "_common" / "journey.py"


def _run(root, *args):
    proc = run_script(JOURNEY, *args, "--json", cwd=root)
    return proc, json.loads(proc.stdout)


def test_j1_add_membuat_berkas_dan_menambah_entri(chain_repo):
    proc, out = _run(chain_repo, "add", "--taskdir", TD, "--hop", "prd",
                     "--teks", "PRD APPROVED. User memilih hapus upsert, bukan deprecate.")
    assert proc.returncode == 0 and out["status"] == "PASS" and out["entri"] == 1
    _run(chain_repo, "add", "--taskdir", TD, "--hop", "READY", "--teks", "7 brief READY; brief 07 khusus test.")
    text = (chain_repo / TD / "JOURNEY.md").read_text(encoding="utf-8")
    assert text.startswith("# Journey — 2609240900-order-fix\n")
    assert "disk yang menang" in text
    proc, out = _run(chain_repo, "show", "--taskdir", TD)
    assert out["ada"] is True
    assert [e["hop"] for e in out["entri"]] == ["PRD", "READY"]
    assert out["entri"][0]["teks"].startswith("PRD APPROVED")


def test_j1_show_tanpa_berkas_pass(chain_repo):
    proc, out = _run(chain_repo, "show", "--taskdir", TD)
    assert proc.returncode == 0 and out == {"status": "PASS", "message": f"{TD}/JOURNEY.md belum ada",
                                            "ada": False, "entri": []}


def test_j1_show_teks_mencetak_isi(chain_repo):
    _run(chain_repo, "add", "--taskdir", TD, "--hop", "TECH_LEAD", "--teks", "Lane PLANNING, risk MAJOR.")
    proc = run_script(JOURNEY, "show", "--taskdir", TD, cwd=chain_repo)
    assert proc.returncode == 0 and "· TECH_LEAD · Lane PLANNING, risk MAJOR." in proc.stdout


@pytest.mark.parametrize("teks,alasan", [
    ("", "kosong"),
    ("   ", "kosong"),
    ("a" * 281, "281 karakter"),
    ("baris satu\nbaris dua", "satu baris"),
    ("lihat ```go\nx```", "satu baris"),
    ("lihat ```x```", "blok kode"),
    ("Satu. Dua. Tiga.", "3 kalimat"),
])
def test_j1_teks_ditolak(chain_repo, teks, alasan):
    proc, out = _run(chain_repo, "add", "--taskdir", TD, "--hop", "BRIEF", "--teks", teks)
    assert proc.returncode == 1 and out["status"] == "FAIL" and alasan in out["message"]
    assert not (chain_repo / TD / "JOURNEY.md").exists()


def test_j1_dua_kalimat_dan_versi_lolos(chain_repo):
    proc, out = _run(chain_repo, "add", "--taskdir", TD, "--hop", "ARCHITECT",
                     "--teks", "Rilis v0.19.1 dipakai. Review P2, tidak memblokir.")
    assert proc.returncode == 0, out


def test_j1_hop_tak_dikenal(chain_repo):
    proc, out = _run(chain_repo, "add", "--taskdir", TD, "--hop", "DEPLOY", "--teks", "x")
    assert proc.returncode == 1 and "DEPLOY" in out["message"]


def test_j1_plafon_entri(chain_repo):
    mod = load_module(JOURNEY, "be_journey_30")
    lines = [f"- 261110 10:{i % 60:02d} · BRIEF · entri {i}" for i in range(mod.MAX_ENTRI)]
    (chain_repo / TD / "JOURNEY.md").write_text("# Journey — x\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    proc, out = _run(chain_repo, "add", "--taskdir", TD, "--hop", "BRIEF", "--teks", "satu lagi")
    assert proc.returncode == 1 and f"{mod.MAX_ENTRI}/{mod.MAX_ENTRI}" in out["message"]


@pytest.mark.parametrize("taskdir", ["backenddev/docs/salah", "backenddev/docs/2609240900-tidak-ada", "../luar"])
def test_j1_taskdir_tak_sah(chain_repo, taskdir):
    proc, out = _run(chain_repo, "add", "--taskdir", taskdir, "--hop", "TASK", "--teks", "x")
    assert proc.returncode == 1 and "tech-lead" in out["message"]


def test_j1_journey_diabaikan_git_dan_tidak_disinkron(chain_repo):
    """K7: JOURNEY.md ikut penanda Langkah 24 dan bukan tipe dokumen sinkron."""
    git(chain_repo, "check-ignore", "-q", f"{TD}/JOURNEY.md")  # gagal = CalledProcessError
    sp = load_module(BE_SKILLS / "_common" / "sync_payload.py", "be_sync_payload_30")
    assert sp.doc_type("JOURNEY.md") == ""


def test_j1_bukan_sumber_gerbang():
    """K5: tak satu skrip gerbang pun membaca JOURNEY.md."""
    readers = [p.relative_to(BE_SKILLS).as_posix() for p in BE_SKILLS.rglob("*.py")
               if p.name != "journey.py" and "JOURNEY" in p.read_text(encoding="utf-8")]
    assert readers == []


# --- J2, J3, H1, H2: prosa skill ---------------------------------------------------------------

def _read(rel):
    return (BE_SKILLS / rel).read_text(encoding="utf-8")


def _hops_in(text):
    import re
    return set(re.findall(r"journey\.py[»`]? add [^\n]*?--hop ([A-Z_<|>]+)", text))


@pytest.mark.regression("30 J2")
def test_j2_penulis_journey_memakai_hop_sah():
    mod = load_module(JOURNEY, "be_journey_30_j2")
    found = {
        "analyst/SKILL.md": {"<BRD|PRD>", "READY"},
        "architect/SKILL.md": {"ARCHITECT"},
        "tech-lead/references/gate-lifecycle.md": {"TECH_LEAD"},
    }
    for rel, hops in found.items():
        assert _hops_in(_read(rel)) == hops, rel
        for h in hops:
            assert set(h.strip("<>").split("|")) <= set(mod.HOPS), (rel, h)
    assert "hop `REVIEW`" in _read("tech-lead/references/gate-lifecycle.md")
    assert "catat journey `REVIEW`" in _read("tech-lead/SKILL.md")
    assert "Catat journey `TECH_LEAD`" in _read("tech-lead/SKILL.md")


@pytest.mark.regression("30 J3")
def test_j3_pembaca_journey_dan_disk_menang():
    arch = _read("architect/SKILL.md")
    fase0 = arch.split("### Fase 0", 1)[1].split("### Fase 1", 1)[0]
    assert "journey.py show" in fase0 and "disk menang" in fase0
    six_a = _read("tech-lead/references/gate-lifecycle.md").split("## 6a.", 1)[1]
    assert "journey.py» show" in six_a and "disk menang" in six_a
    assert "baca journey-nya" in _read("tech-lead/SKILL.md").split("### Fase 0", 1)[1].split("### Fase 1", 1)[0]


@pytest.mark.regression("30 H1")
def test_h1_titik_serah_terima_satu_dan_pilihan_user():
    lifecycle = _read("tech-lead/references/gate-lifecycle.md")
    row = next(l for l in lifecycle.splitlines() if l.startswith("   - Pengirim `analyst` bervonis `READY_FOR_IMPLEMENTATION`"))
    assert "bagian 6a" in row and "titik serah terima eksekusi" in row
    six_a = lifecycle.split("## 6a.", 1)[1]
    for wajib in ("/clear", "/compact", "/model sonnet", "/backend:tech-lead lanjutkan <taskdir>",
                  "TERTAHAN (serah terima)", "\"lanjut\"", "pilihannya milik user"):
        assert wajib in six_a, wajib
    # IRON LAW memuat pengecualian eksplisit, bukan menghapus aturannya
    iron = _read("tech-lead/SKILL.md").split("## THE IRON LAW", 1)[1].split("## Precondition", 1)[0]
    assert "giliran yang sama — kecuali serah terima eksekusi" in iron
    # analyst tidak memberangkatkan architect sendiri
    fase6 = _read("analyst/SKILL.md").split("### Fase 6", 1)[1].split("## Guardrails", 1)[0]
    assert "serah terima eksekusi" in fase6 and "Dilarang memanggil `architect`" in fase6


@pytest.mark.regression("30 H2")
def test_h2_lanjutan_melewati_eksplorasi_dan_baseline_gerbang():
    butir4 = _read("tech-lead/references/gate-lifecycle.md").split("## 6a.", 1)[1].split("\n4. ", 1)[1]
    assert "Fase 1–4 dilewati" in butir4 and "--re-entry" in butir4
    assert "tanpa baseline build gerbang" in butir4 and "permukaan baru" in butir4
