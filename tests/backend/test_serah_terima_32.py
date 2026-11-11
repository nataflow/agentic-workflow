"""32 H3–H4 — serah terima sesudah PRD `APPROVED` dan rute lanjutan hop terbuka di gerbang."""
import pytest

from conftest import BE_SKILLS, TD, be_checks, commit, write_files

ANALYST = "analyst/scripts/check_preconditions.py"


def _read(rel):
    return (BE_SKILLS / rel).read_text(encoding="utf-8")


def _task(repo, chain, ledger):
    write_files(repo, {f"{TD}/TASK.md": (f"---\nchain: {chain}\nrisk: MAJOR\nstatus: ACTIVE\n---\n# Order split\n"
                                         f"## Success Criteria\n- [ ] **SC-1**: x\n## Chain\n{ledger}")})
    commit(repo, "docs(order-fix): kunci TASK")


def _resume(repo, chain):
    return be_checks(repo, ANALYST, "--taskdir", TD, "--risk", "MAJOR", "--chain", chain)[7]


# --- H4: keadaan disk yang dirutekan baris "hop ledger terbuka" berujung resume `analyst` yang benar -------------

@pytest.mark.regression("32 H4")
def test_prd_approved_brief_terbuka_resume_brief(chain_repo):
    _task(chain_repo, "PRD_BRIEF", "- [x] PRD — backend:system-analysis → PRD.md @ APPROVED a1b2c3d\n"
                                   "- [ ] BRIEF — backend:plan → brief-*.md\n")
    c7 = _resume(chain_repo, "PRD_BRIEF")
    assert c7["status"] == "PASS" and c7["summary"].startswith("Resume: hop BRIEF")


@pytest.mark.regression("32 H4")
def test_sisa_brief_draft_tetap_resume_brief(chain_repo):
    _task(chain_repo, "PRD_BRIEF", "- [x] PRD — backend:system-analysis → PRD.md @ APPROVED a1b2c3d\n"
                                   "- [ ] BRIEF — backend:plan → brief-*.md\n")
    write_files(chain_repo, {f"{TD}/brief-01-order.md": "---\nstatus: DRAFT\n---\n# brief\n"})
    c7 = _resume(chain_repo, "PRD_BRIEF")
    assert c7["status"] == "PASS" and c7["summary"].startswith("Resume: hop BRIEF")


@pytest.mark.regression("32 H4")
def test_brd_approved_prd_belum_berangkat_resume_prd(chain_repo):
    _task(chain_repo, "BRD_PRD_BRIEF", "- [x] BRD — backend:business-analysis → BRD.md @ APPROVED a1b2c3d\n"
                                       "- [ ] PRD — backend:system-analysis → PRD.md\n"
                                       "- [ ] BRIEF — backend:plan → brief-*.md\n")
    c7 = _resume(chain_repo, "BRD_PRD_BRIEF")
    assert c7["status"] == "PASS" and c7["summary"].startswith("Resume: hop PRD")


@pytest.mark.regression("32 H4")
def test_gerbang_punya_baris_hop_terbuka():
    lifecycle = _read("tech-lead/references/gate-lifecycle.md")
    row = next(l for l in lifecycle.splitlines() if l.startswith("| Taskdir berledger `## Chain` dengan hop belum tercentang"))
    assert "`backend:analyst`" in row and "**tanpa** `reentry_reason`" in row and "frontmatter `TASK.md`" in row
    # presedensi: baris DRAFT dan READY tetap di atasnya
    rows = [l for l in lifecycle.splitlines() if l.startswith("| Taskdir")]
    assert rows.index(row) > rows.index(next(l for l in rows if "berstatus `DRAFT`" in l))
    assert rows.index(row) > rows.index(next(l for l in rows if "brief `READY`" in l))
    assert "6. Hop ledger terbuka" in _read("tech-lead/references/decisions.md")
    assert "hop ledger terbuka → `analyst`" in _read("tech-lead/SKILL.md")


@pytest.mark.regression("32 H4")
def test_lanjutan_serah_terima_prd_dan_disk_menang():
    butir4 = _read("tech-lead/references/gate-lifecycle.md").split("## 6a.", 1)[1].split("\n4. ", 1)[1].split("\n5. ", 1)[0]
    assert "ber-hop `READY` atau `PRD`" in butir4 and "Disk menang atas journey" in butir4
    assert "entri `PRD` dengan brief `READY` di disk berangkat ke `architect`" in butir4
    assert "`lane`, `risk`, dan `chain` dari frontmatter `TASK.md`" in butir4


# --- H3: titik henti sesudah PRD ---------------------------------------------------------------------------------

@pytest.mark.regression("32 H3")
def test_analyst_mengembalikan_vonis_hanya_untuk_persetujuan_di_pemanggilan_ini():
    fase4 = _read("analyst/SKILL.md").split("### Fase 4 —", 1)[1].split("### Fase 4a", 1)[0]
    butir7 = fase4.split("\n7. ", 1)[1]
    assert "`PRD_APPROVED_SERAH_TERIMA`" in butir7 and "di pemanggilan ini" in butir7
    assert "Fase 0 resume tidak memicu butir ini" in butir7
    assert "jangan berangkatkan `backend:plan`" in butir7
    assert "Lanjut ke hop berikutnya, kecuali butir 7." in fase4
    output = _read("analyst/SKILL.md").split("## Output [REQUIRED]", 1)[1]
    assert "PLANNING CHAIN REPORT — PRD_APPROVED_SERAH_TERIMA" in output


@pytest.mark.regression("32 H3")
def test_gerbang_mencetak_blok_serah_terima_prd():
    lifecycle = _read("tech-lead/references/gate-lifecycle.md")
    row = next(l for l in lifecycle.splitlines() if l.startswith("   - Pengirim `analyst` bervonis `PRD_APPROVED_SERAH_TERIMA`"))
    assert "bagian 6a butir 5" in row and "Dilarang memanggil `backend:plan` langsung" in row
    butir5 = lifecycle.split("## 6a.", 1)[1].split("\n5. ", 1)[1]
    for wajib in ("TERTAHAN (serah terima PRD)", "/clear → /backend:tech-lead lanjutkan <taskdir>", "/compact",
                  "\"lanjut\"", "Hemat konteks sebelum plan"):
        assert wajib in butir5, wajib
    iron = _read("tech-lead/SKILL.md").split("## THE IRON LAW", 1)[1].split("## Precondition", 1)[0]
    assert "kecuali serah terima eksekusi/PRD" in iron
