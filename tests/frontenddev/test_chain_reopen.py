"""`chain.py reopen` — kaskade divalidasi sebelum ditulis (L4.5), kuota per hop target (L4.9)."""
import sys

import pytest

from conftest import FE_SKILLS, FE_TD, commit, fe_approved_chain, fe_run, git

TASK = f"{FE_TD}/TASK.md"
CONTRACT = f"{FE_TD}/CONTRACT.md"


def reopen(repo, row, reason="uji"):
    return fe_run(repo, "_common/chain.py", "reopen", "--taskdir", FE_TD, "--row", row, "--reason", reason)


def fake_reopen(repo, rows, reason):
    """Commit ber-subjek reopen atas TASK.md — riwayat kuota tanpa mengubah ledger."""
    p = repo / TASK
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    commit(repo, f"docs(orders-lacak): reopen {rows} — {reason}", TASK)


@pytest.fixture
def approved(fe_chain_repo):
    fe_approved_chain(fe_chain_repo)
    return fe_chain_repo


# ------------------------------------------------------------------ L4.5


def test_reopen_frontmatter_rusak_fail_rapi(approved):
    p = approved / CONTRACT
    p.write_text(p.read_text(encoding="utf-8").replace("sections: [architecture]\n---\n", "sections: [architecture]\n", 1),
                 encoding="utf-8")
    commit(approved, "docs(orders-lacak): rusak", CONTRACT)
    r = reopen(approved, "CONTRACT")
    assert r.returncode == 1 and r.out.startswith("CHAIN REOPEN: [FAIL]") and "Traceback" not in r.out
    assert "git show " in r.out and "Tidak ada berkas yang diubah" in r.out


def test_reopen_gagal_tidak_mengubah_berkas(approved):
    p = approved / CONTRACT
    p.write_text(p.read_text(encoding="utf-8").replace("sections: [architecture]\n---\n", "sections: [architecture]\n", 1),
                 encoding="utf-8")
    commit(approved, "docs(orders-lacak): rusak", CONTRACT)
    reopen(approved, "CONTRACT")
    assert git(approved, "status", "--porcelain").strip() == ""
    assert "- [x] CONTRACT" in (approved / TASK).read_text(encoding="utf-8")


def test_reopen_gagal_tulis_dipulihkan(approved, monkeypatch):
    sys.path.insert(0, str(FE_SKILLS / "_common"))
    import chain as chain_mod
    before = {rel: (approved / rel).read_text(encoding="utf-8") for rel in (TASK, CONTRACT)}
    real = chain_mod.write_keep_newline

    def flaky(path, text):
        if path.name == "TASK.md":
            raise OSError("disk penuh")
        return real(path, text)

    monkeypatch.setattr(chain_mod, "write_keep_newline", flaky)
    with pytest.raises(chain_mod.ChainError, match="dipulihkan"):
        chain_mod.Chain(FE_TD, approved).reopen("CONTRACT", "uji")
    monkeypatch.undo()
    assert {rel: (approved / rel).read_text(encoding="utf-8") for rel in (TASK, CONTRACT)} == before


# ------------------------------------------------------------------ L4.9


def test_kaskade_tidak_memakan_kuota_hop_bawah(approved):
    fake_reopen(approved, "CONTRACT BRIEF", "berkas yatim 1")
    fake_reopen(approved, "CONTRACT BRIEF", "DTO baru")
    fake_reopen(approved, "BRIEF", "unit 01 BLOCKED")
    r = reopen(approved, "BRIEF", "REVIEW BLOCKED")
    assert r.returncode == 0, r.out
    assert "re-entry 2" in r.out


def test_kuota_target_tetap_3(approved):
    for i in range(3):
        fake_reopen(approved, "BRIEF", f"unit BLOCKED {i}")
    r = reopen(approved, "BRIEF")
    assert r.returncode == 1 and "plafon re-entry hop `BRIEF` (3)" in r.out


def test_plafon_taskdir_6_tetap(approved):
    for i in range(6):
        fake_reopen(approved, "CONTRACT BRIEF", f"lingkup {i}")
    r = reopen(approved, "BRIEF")
    assert r.returncode == 1 and "plafon re-entry taskdir (6)" in r.out
