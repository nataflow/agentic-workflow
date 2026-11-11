"""Langkah 33 J1: `frontend/skills/_common/journey.py` — catatan keputusan antar sesi di `<taskdir>/JOURNEY.md`."""
import ast
import json

import pytest

from conftest import BE_SKILLS, FE_SKILLS, FE_TD, fe_run, git, load_module, run_script

JOURNEY = FE_SKILLS / "_common" / "journey.py"


def _run(root, *args):
    proc = run_script(JOURNEY, *args, "--json", cwd=root)
    return proc, json.loads(proc.stdout)


@pytest.mark.regression("33 J1")
def test_j1_add_membuat_berkas_dan_menambah_entri(fe_chain_repo):
    proc, out = _run(fe_chain_repo, "add", "--taskdir", FE_TD, "--hop", "contract",
                     "--teks", "Opsi B dipilih: query key per order, bukan cache global.")
    assert proc.returncode == 0 and out["status"] == "PASS" and out["entri"] == 1
    _run(fe_chain_repo, "add", "--taskdir", FE_TD, "--hop", "BRIEF", "--teks", "3 brief READY; unit 03 khusus test.")
    text = (fe_chain_repo / FE_TD / "JOURNEY.md").read_text(encoding="utf-8")
    assert text.startswith("# Journey — 2609241200-orders-lacak\n")
    assert "disk yang menang" in text and "Riwayat Rantai" in text
    proc, out = _run(fe_chain_repo, "show", "--taskdir", FE_TD)
    assert out["ada"] is True
    assert [e["hop"] for e in out["entri"]] == ["CONTRACT", "BRIEF"]


def test_j1_show_tanpa_berkas_pass(fe_chain_repo):
    proc, out = _run(fe_chain_repo, "show", "--taskdir", FE_TD)
    assert proc.returncode == 0 and out == {"status": "PASS", "message": f"{FE_TD}/JOURNEY.md belum ada",
                                            "ada": False, "entri": []}


def test_j1_show_teks_mencetak_isi(fe_chain_repo):
    _run(fe_chain_repo, "add", "--taskdir", FE_TD, "--hop", "LEAD", "--teks", "Lane FAST_FORWARD, tanpa ubah layout.")
    proc = run_script(JOURNEY, "show", "--taskdir", FE_TD, cwd=fe_chain_repo)
    assert proc.returncode == 0 and "· LEAD · Lane FAST_FORWARD, tanpa ubah layout." in proc.stdout


@pytest.mark.parametrize("teks,alasan", [
    ("", "kosong"),
    ("a" * 281, "281 karakter"),
    ("baris satu\nbaris dua", "satu baris"),
    ("lihat ```tsx```", "blok kode"),
    ("Satu. Dua. Tiga.", "3 kalimat"),
])
def test_j1_teks_ditolak(fe_chain_repo, teks, alasan):
    proc, out = _run(fe_chain_repo, "add", "--taskdir", FE_TD, "--hop", "BRIEF", "--teks", teks)
    assert proc.returncode == 1 and out["status"] == "FAIL" and alasan in out["message"]
    assert not (fe_chain_repo / FE_TD / "JOURNEY.md").exists()


@pytest.mark.parametrize("hop", ["PRD", "READY", "TECH_LEAD", "DEPLOY"])
def test_j1_hop_backend_atau_asing_ditolak(fe_chain_repo, hop):
    proc, out = _run(fe_chain_repo, "add", "--taskdir", FE_TD, "--hop", hop, "--teks", "x")
    assert proc.returncode == 1 and hop in out["message"]


def test_j1_plafon_entri(fe_chain_repo):
    mod = load_module(JOURNEY, "fe_journey_33")
    lines = [f"- 261111 10:{i % 60:02d} · BRIEF · entri {i}" for i in range(mod.MAX_ENTRI)]
    (fe_chain_repo / FE_TD / "JOURNEY.md").write_text("# Journey — x\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    proc, out = _run(fe_chain_repo, "add", "--taskdir", FE_TD, "--hop", "BRIEF", "--teks", "satu lagi")
    assert proc.returncode == 1 and f"{mod.MAX_ENTRI}/{mod.MAX_ENTRI}" in out["message"]


@pytest.mark.parametrize("taskdir,alasan", [
    ("frontenddev/docs/salah", "tidak berpola"),
    ("frontenddev/docs/2609241200-tidak-ada", "tidak ada"),
    ("frontenddev/docs/../../luar", "tidak berpola"),
])
def test_j1_taskdir_tak_sah(fe_chain_repo, taskdir, alasan):
    proc, out = _run(fe_chain_repo, "add", "--taskdir", taskdir, "--hop", "LEAD", "--teks", "x")
    assert proc.returncode == 1 and alasan in out["message"] and "frontend:lead" in out["message"]


@pytest.mark.regression("33 J1")
def test_j1_taskdir_tanpa_akar_ditolak(fe_chain_repo):
    """Journey sebelum `TASK.md` membuat taskdir tampak kosong di `taskdir_state.py` — ditolak skrip."""
    td = "frontenddev/docs/2609241300-orders-baru"
    (fe_chain_repo / td).mkdir(parents=True)
    proc, out = _run(fe_chain_repo, "add", "--taskdir", td, "--hop", "LEAD", "--teks", "x")
    assert proc.returncode == 1 and "belum berakar" in out["message"]
    assert not (fe_chain_repo / td / "JOURNEY.md").exists()


@pytest.mark.regression("33 J1")
def test_j1_journey_diabaikan_git_tidak_disinkron_tidak_mengubah_vonis(fe_chain_repo):
    """K: JOURNEY.md ikut penanda Langkah 24, bukan tipe dokumen sinkron, dan tidak menggeser `taskdir_state.py`."""
    before = json.loads(fe_run(fe_chain_repo, "lead/scripts/taskdir_state.py", "--taskdir", FE_TD, "--json").stdout)
    _run(fe_chain_repo, "add", "--taskdir", FE_TD, "--hop", "LEAD", "--teks", "Lane FAST_FORWARD.")
    git(fe_chain_repo, "check-ignore", "-q", f"{FE_TD}/JOURNEY.md")  # gagal = CalledProcessError
    assert git(fe_chain_repo, "status", "--porcelain").strip() == ""
    sp = load_module(FE_SKILLS / "_common" / "sync_payload.py", "fe_sync_payload_33")
    assert sp.doc_type("JOURNEY.md") == ""
    after = json.loads(fe_run(fe_chain_repo, "lead/scripts/taskdir_state.py", "--taskdir", FE_TD, "--json").stdout)
    assert after == before and after[0]["state"] == "GATE"


def test_j1_bukan_sumber_gerbang():
    """Tak satu skrip gerbang pun membaca JOURNEY.md."""
    readers = [p.relative_to(FE_SKILLS).as_posix() for p in FE_SKILLS.rglob("*.py")
               if p.name != "journey.py" and "JOURNEY" in p.read_text(encoding="utf-8")]
    assert readers == []


@pytest.mark.regression("33 J1")
def test_j1_aturan_teks_identik_dengan_backend():
    """Plafon dan aturan teks sama dengan journey backend (Langkah 30); hanya hop dan cek taskdir yang berbeda."""
    # Dibandingkan lewat AST, tanpa impor: kedua skrip mengimpor `precondition_lib` yang berbeda, dan salinan
    # plugin lain yang tertinggal di `sys.modules` dari test sebelumnya akan mematahkan impor itu.
    def nodes(path):
        src = path.read_text(encoding="utf-8")
        out = {}
        for node in ast.parse(src).body:
            if isinstance(node, ast.FunctionDef):
                out[node.name] = ast.get_source_segment(src, node)
            elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                out[node.targets[0].id] = ast.get_source_segment(src, node)
        return out

    fe, be = nodes(JOURNEY), nodes(BE_SKILLS / "_common" / "journey.py")
    for name in ("NAME", "MAX_TEKS", "MAX_KALIMAT", "MAX_ENTRI", "ENTRY_RE", "_SENTENCE_END",
                 "entries", "teks_problem", "emit"):
        assert fe[name] == be[name], name
