"""Langkah 24 — `## Riwayat Rantai` frontend: akar dikunci di disk (`chain.py root`), amandemen akar, draft yang
diajukan, keutuhan Riwayat, dan `sidik_kontrak` brief. Dokumen taskdir tidak pernah di-commit."""
import json

import pytest

from conftest import FE_FIX, FE_SKILLS, FE_TD, commit, fe_approved_chain, fe_draft, fe_lib, fe_profile, fe_round, fe_run, git, \
    write_files

TASK = f"{FE_TD}/TASK.md"
CONTRACT = f"{FE_TD}/CONTRACT.md"
B1 = f"{FE_TD}/brief-01-orders-lacak-button.md"


def chain(repo, *args):
    return fe_run(repo, "_common/chain.py", *args, "--taskdir", FE_TD)


def riwayat(repo):
    return fe_lib().read_history((repo / TASK).read_text(encoding="utf-8"))


def edit(repo, rel, old, new):
    p = repo / rel
    text = p.read_text(encoding="utf-8")
    assert old in text, (rel, old)
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


@pytest.fixture
def unlocked(make_repo):
    """Akar `TASK.md` tertulis dan ber-ledger (`chain.py init`), belum dikunci."""
    root = make_repo({".gitignore": ".explore/\n",
                      "src/features/orders/OrderDetail.tsx": "export function OrderDetail() { return null }\n"})
    git(root, "checkout", "-q", "-b", "main")
    fe_profile(root, "react-vite")
    commit(root, "init")
    write_files(root, {TASK: (FE_FIX / "task_fast_forward.md").read_text(encoding="utf-8")})
    assert chain(root, "init").returncode == 0
    return root


@pytest.mark.regression("24 K6")
def test_root_menulis_base_commit_dan_kejadian_akar(unlocked):
    r = chain(unlocked, "root")
    assert r.returncode == 0 and "Riwayat #1" in r.out, r.out
    head = git(unlocked, "rev-parse", "HEAD").strip()
    assert f"base_commit: {head}" in (unlocked / TASK).read_text(encoding="utf-8")
    events, problem = riwayat(unlocked)
    assert not problem and [e["kind"] for e in events] == ["akar"]
    assert events[0]["fields"]["lane"] == "FAST_FORWARD" and events[0]["fields"]["sections"] == "architecture"
    assert git(unlocked, "status", "--porcelain") == "", "akar di disk, diabaikan git"
    r = chain(unlocked, "root")
    assert r.returncode == 1 and "sudah terkunci" in r.out


def test_root_menuntut_validate_task(unlocked):
    edit(unlocked, TASK, "- Peta kurir real-time — opsi yang ditolak", "- TBD")
    r = chain(unlocked, "root")
    assert r.returncode == 1 and "validate_task.py" in r.out, r.out
    assert "base_commit" not in (unlocked / TASK).read_text(encoding="utf-8")


@pytest.mark.regression("24 G2")
def test_root_menolak_dokumen_ter_track(unlocked):
    commit(unlocked, "docs: era git", TASK)
    r = chain(unlocked, "root")
    assert r.returncode == 1 and "MIGRASI" in r.out, r.out


@pytest.mark.regression("24 K5")
def test_gerbang_hilir_menolak_akar_belum_terkunci(unlocked):
    r = fe_run(unlocked, "contract/scripts/check_preconditions.py", "--taskdir", FE_TD, "--json")
    c2 = next(c for c in json.loads(r.stdout)["checks"] if c["id"] == 2)
    assert c2["status"] == "FAIL" and "akar belum terkunci" in c2["summary"], c2


@pytest.mark.regression("24 K5")
def test_akar_disunting_tanpa_amandemen_ditolak_lalu_amend(fe_chain_repo):
    repo = fe_chain_repo
    edit(repo, TASK, "## Out of Scope\n", "- [ ] **SC-2**: riwayat lacak tampil — verifikasi: test "
                                          "`OrderDetail.test.tsx` hijau\n\n## Out of Scope\n")
    r = fe_run(repo, "contract/scripts/check_preconditions.py", "--taskdir", FE_TD, "--json")
    c2 = next(c for c in json.loads(r.stdout)["checks"] if c["id"] == 2)
    assert c2["status"] == "FAIL" and "chain.py amend" in c2["action"], c2
    assert chain(repo, "draft", "--row", "CONTRACT").returncode == 1
    r = chain(repo, "amend", "--reason", "user menambah SC-2")
    assert r.returncode == 0 and "Riwayat #2" in r.out, r.out
    r = fe_run(repo, "contract/scripts/check_preconditions.py", "--taskdir", FE_TD, "--json")
    assert next(c for c in json.loads(r.stdout)["checks"] if c["id"] == 2)["status"] == "PASS"
    r = chain(repo, "amend", "--reason", "ulang")
    assert r.returncode == 1 and "tidak berubah" in r.out


@pytest.mark.regression("24 K5")
def test_riwayat_rusak_fail_closed(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    edit(repo, TASK, "- 3 · approve CONTRACT", "- 7 · approve CONTRACT")
    r = chain(repo, "verify")
    assert r.returncode == 1 and "Riwayat Rantai` rusak" in r.out, r.out
    r = chain(repo, "reopen", "--row", "BRIEF", "--reason", "x")
    assert r.returncode == 1 and "Riwayat Rantai` rusak" in r.out
    state = fe_run(repo, "lead/scripts/taskdir_state.py", "--taskdir", FE_TD)
    assert "RUSAK" in state.out and "Riwayat" in state.out, state.out


def test_draft_konten_sama_tidak_dicatat_ulang(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo)
    assert fe_draft(repo).returncode == 0
    r = fe_draft(repo)
    assert r.returncode == 1 and "sudah tercatat" in r.out, r.out


def test_jawaban_berpemisah_tidak_merusak_riwayat(fe_chain_repo):
    repo = fe_chain_repo
    fe_round(repo)
    assert fe_draft(repo).returncode == 0
    answer = "Setujui · alasan: palsu · sidik 0000"
    r = chain(repo, "approve", "--row", "CONTRACT", "--answer", answer)
    assert r.returncode == 0, r.out
    events, problem = riwayat(repo)
    assert not problem and events[-1]["free"] == ("persetujuan", answer)
    assert chain(repo, "verify", "--rows", "CONTRACT").returncode == 0


@pytest.mark.regression("24 K10")
def test_approve_brief_mengunci_kontrak_tanpa_menggeser_sidik(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    text = (repo / B1).read_text(encoding="utf-8")
    assert "sidik_kontrak: " in text
    assert chain(repo, "verify").returncode == 0, "sidik_kontrak di luar sidik konten yang disetujui"
    write_files(repo, {"src/features/orders/OrderDetail.tsx": "export function OrderDetail() { return 1 }\n"})
    ok = fe_run(repo, "_common/verify_scope.py", "--brief", B1, "--worktree")
    assert ok.returncode == 0, ok.out
    edit(repo, B1, "Tambah tombol Lacak di OrderDetail.", "Tambah tombol Lacak dan ubah router.")
    bad = fe_run(repo, "_common/verify_scope.py", "--brief", B1, "--worktree")
    assert bad.returncode == 1 and "disunting di luar" in bad.out, bad.out


def test_strip_sidik_kontrak_baris_terakhir_frontmatter():
    lib = fe_lib()
    base = "---\nstatus: READY\nslug: x\nverification:\n  - pnpm test\n---\n# Brief\n"
    sealed = lib.set_frontmatter_field(base, "sidik_kontrak", "abc")
    assert sealed != base and lib.strip_status_line(sealed) == lib.strip_status_line(base)


@pytest.mark.regression("24 K7")
def test_done_tanpa_commit_unit_ditolak_lalu_sah_sesudah_commit_kode(fe_chain_repo):
    repo = fe_chain_repo
    fe_approved_chain(repo)
    edit(repo, B1, "status: READY", "status: DONE")
    write_files(repo, {f"{FE_TD}/report-01.md": '---\nunit: "01"\nstatus: DONE\n---\n# Unit 01\n'})
    arch = fe_run(repo, "architect/scripts/check_preconditions.py", "--taskdir", FE_TD, "--json")
    data = json.loads(arch.stdout)
    c4 = next(c for c in data["checks"] if c["id"] == 4)
    # 25 R6: bukan FAIL (yang memantul ke lead), tetapi fase TERPUTUS di unit itu — tetap tidak dihitung DONE.
    assert c4["status"] == "WARN" and "01" in c4["summary"], c4
    assert data["phase"] == "TERPUTUS" and data["next_unit"] == "01", data
    write_files(repo, {"src/features/orders/OrderDetail.tsx": "export function OrderDetail() { return 1 }\n"})
    commit(repo, "feat(orders-lacak): implement unit 01 - tombol lacak", "src/features/orders/OrderDetail.tsx")
    arch = fe_run(repo, "architect/scripts/check_preconditions.py", "--taskdir", FE_TD, "--json")
    data = json.loads(arch.stdout)
    assert next(c for c in data["checks"] if c["id"] == 4)["status"] == "PASS" and data["phase"] == "PENUTUP", data


def _template_section_1() -> str:
    text = (FE_SKILLS / "task/templates/task-template.md").read_text(encoding="utf-8")
    return text.split("## 1. Template Kanonik TASK.md", 1)[1].split("````markdown\n", 1)[1].split("\n````", 1)[0]


@pytest.mark.regression("25 R4")
def test_r4_template_kanonik_tanpa_base_commit_dan_riwayat():
    body = _template_section_1()
    assert "base_commit" not in body
    assert "## Riwayat Rantai" not in body


@pytest.fixture
def akar_bertemplate_lama(make_repo):
    """Akar baru tertulis dengan placeholder `## Riwayat Rantai` dari template lama, belum di-`init`."""
    root = make_repo({"src/features/orders/OrderDetail.tsx": "export function OrderDetail() { return null }\n"})
    git(root, "checkout", "-q", "-b", "main")
    fe_profile(root, "react-vite")
    commit(root, "init")
    task = (FE_FIX / "task_fast_forward.md").read_text(encoding="utf-8").rstrip("\n")
    write_files(root, {TASK: task + "\n\n## Riwayat Rantai\n\n<ditulis `chain.py root` dan subperintah "
                                     "sesudahnya — dilarang diketik atau disunting dengan tangan>\n"})
    return root


@pytest.mark.regression("25 R4")
def test_r4_init_membuang_placeholder_riwayat_lalu_root_mengunci(akar_bertemplate_lama):
    root = akar_bertemplate_lama
    r = chain(root, "init")
    assert r.returncode == 0, r.out
    text = (root / TASK).read_text(encoding="utf-8")
    assert "## Riwayat Rantai" not in text and "## Chain" in text
    r = chain(root, "root")
    assert r.returncode == 0, r.out
    events, problem = riwayat(root)
    assert problem == "" and [e["kind"] for e in events] == ["akar"]


@pytest.mark.regression("25 R4")
def test_r4_riwayat_berisi_baris_asing_tetap_rusak(akar_bertemplate_lama):
    root = akar_bertemplate_lama
    edit(root, TASK, "<ditulis `chain.py root`", "- 1 · akar sunting tangan\n<ditulis `chain.py root`")
    r = chain(root, "init")
    assert r.returncode == 1 and "Riwayat Rantai` rusak" in r.out
