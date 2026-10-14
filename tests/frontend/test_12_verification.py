"""Regresi 12 Tahap 2 — verifikasi penutup & prasyarat `frontend` (J11–J13, J15–J23).

`run_verification.py` menelan exit sisi kiri pipa (J11), memaafkan galat kembar baseline (J12), dan
tidak mengikat baseline ke commit (J13). Prasyarat architect meloloskan `DONE` tanpa kode (J15), brief
beda stack (J16), tree tak terbaca (J17), dan crash pada remedi siklik (J20); `lane_tamper` dapat
ditipu subjek tiruan (J18); `cli()` belum menangkap `OSError` (J19); migrasi menimpa berkas tujuan
(J21); `REPORT.md` tertunda disebut kerja user (J22); NAMA ganda dan race `killpg` (J23).
Salinan backend berkas kembar diuji di `tests/backend/test_12_verification.py`.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from conftest import FE_MINOR_TD as TD, FE_SKILLS, PLUGINS, commit, fe_base_commit, fe_profile, fe_review_md, \
    fe_run, git, load_module, run_script, write_files

RUNV = FE_SKILLS / "_common/run_verification.py"
ARCH = "architect/scripts/check_preconditions.py"
BRIEF = f"{TD}/brief-01-order-button.md"
MIGRATE = FE_SKILLS / "profile/scripts/migrate_profile.py"
LIB = load_module(FE_SKILLS / "_common/precondition_lib.py", "fe_lib_12v")
OTHER_TD = "frontenddev/docs/2609260000-akar"
TASK = ("---\nstatus: ACTIVE\nlane: HOTFIX_MINOR\nsections: \n---\n# x\n\n## Chain\n\n- [ ] BRIEF\n\n"
        "## Riwayat Rantai\n\n- 1 · akar · base 0000000 · lane HOTFIX_MINOR · sections - · akar 000000000000 · "
        "waktu 2026-10-13T00:00:00Z\n")


def runv(tmp, mode, *cmds, timeout=5, env=None):
    args = [sys.executable, str(RUNV), mode, "--taskdir", "td", "--timeout", str(timeout)]
    for c in cmds:
        args += ["--cmd", c]
    return subprocess.run(args, cwd=tmp, capture_output=True, text=True, env=env)


def checks(proc):
    assert "Traceback" not in proc.stdout + proc.stderr, proc.stdout + proc.stderr
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


def arch(repo, *args):
    return checks(fe_run(repo, ARCH, "--taskdir", TD, "--json", *args))


def at_approve(repo):
    """Mundur ke sesudah approve breakdown: brief-01 `READY`, belum ada unit mendarat (commit kode dibuang,
    laporan dan review dihapus dari disk — dokumen taskdir tidak di-commit, Langkah 24)."""
    for name in ("REPORT.md", "REVIEW.md", "report-01.md"):
        (repo / TD / name).unlink()
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    set_status(repo, BRIEF, "READY")


def set_status(repo, rel, status, **extra):
    text = (repo / rel).read_text(encoding="utf-8")
    text = re.sub(r"^status: \w+$", f"status: {status}", text, count=1, flags=re.M)
    for k, v in extra.items():
        text = text.replace('unit: "01"', f'unit: "01"\n{k}: {v}', 1)
    (repo / rel).write_text(text, encoding="utf-8")


# --- J11: pipa tidak menelan exit ----------------------------------------------------------------

@pytest.mark.regression("J11")
@pytest.mark.parametrize("cmd", ["t=false | cat", "t=sh -c 'exit 3' | cat"])
def test_j11_pipa_tidak_menelan_exit(tmp_path, cmd):
    r = runv(tmp_path, "closing", cmd)
    assert r.returncode == 1 and "MERAH" in r.stdout, r.stdout


@pytest.mark.regression("J11")
def test_j11_tanpa_bash_pipa_ditolak(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for tool in ("sh", "true", "cat"):
        (bindir / tool).symlink_to(shutil.which(tool))
    env = {**os.environ, "PATH": str(bindir)}
    r = runv(tmp_path, "closing", "t=true | cat", env=env)
    assert r.returncode == 2 and "bash" in r.stderr and "Traceback" not in r.stderr, r.stderr
    assert runv(tmp_path, "closing", "t=true", env=env).returncode == 0


# --- J12: galat kembar baseline tetap galat baru ------------------------------------------------

@pytest.mark.regression("J12")
def test_j12_galat_kembar_baseline_terhitung_baru(tmp_path):
    runv(tmp_path, "baseline", "tc=printf 'src/a.ts:10:5 - error TS2322: bad\\n'; exit 2")
    r = runv(tmp_path, "closing",
             "tc=printf 'src/a.ts:10:5 - error TS2322: bad\\nsrc/a.ts:48:3 - error TS2322: bad\\n'; exit 2")
    assert r.returncode == 1 and "baru=1" in r.stdout, r.stdout


@pytest.mark.regression("J12")
def test_j12_ekor_log_tetap_himpunan(tmp_path):
    runv(tmp_path, "baseline", "b=echo alpha; echo alpha; exit 3")
    assert runv(tmp_path, "closing", "b=echo alpha; exit 3").returncode == 0


# --- J13: baseline terikat commit ---------------------------------------------------------------

@pytest.mark.regression("J13")
def test_j13_baseline_dan_log_mencatat_head(make_repo):
    repo = make_repo({"a.txt": "a\n"})
    commit(repo, "init")
    head = git(repo, "rev-parse", "HEAD").strip()
    runv(repo, "baseline", "t=true")
    base = json.loads((repo / "td/.explore/verification-baseline.json").read_text(encoding="utf-8"))
    assert base["t"]["head"] == head
    runv(repo, "closing", "t=true")
    log = json.loads((repo / "td/.explore/closing-verification.json").read_text(encoding="utf-8"))
    assert log[0]["baseline_head"] == head


def review_log(repo, head):
    (repo / TD / "REPORT.md").unlink()
    write_files(repo, {f"{TD}/REVIEW.md": fe_review_md(repo)})
    entry = {"cmd": "test", "status": "HIJAU", "new_errors": 0, "baseline_status": "HIJAU"}
    if head is not None:
        entry["baseline_head"] = head
    rel = f"{TD}/.explore/closing-verification.json"
    write_files(repo, {rel: json.dumps([entry])})
    r = fe_run(repo, "architect/scripts/validate_review.py", "--taskdir", TD, "--json", "--log", rel)
    return r.returncode, checks(r)["LOG"]


@pytest.mark.regression("J13")
def test_j13_baseline_sesudah_unit_mendarat_fail(fe_minor_chain):
    unit = git(fe_minor_chain, "log", "--format=%H", "--grep=implement unit 01").split()[0]
    rc, c = review_log(fe_minor_chain, unit)
    assert rc == 1 and any("sesudah unit pertama" in d for d in c["details"]), c


@pytest.mark.regression("J13")
def test_j13_baseline_tanpa_head_fail(fe_minor_chain):
    rc, c = review_log(fe_minor_chain, None)
    assert rc == 1 and any("tanpa `baseline_head`" in d for d in c["details"]), c


@pytest.mark.regression("J13")
def test_j13_baseline_di_akar_pass(fe_minor_chain):
    rc, c = review_log(fe_minor_chain, fe_base_commit(fe_minor_chain, TD))
    assert c["status"] == "PASS", c


# --- J15: DONE wajib mendarat bersama kode -------------------------------------------------------

@pytest.mark.regression("J15")
def test_j15_done_tanpa_kode_fail(fe_minor_chain):
    at_approve(fe_minor_chain)
    set_status(fe_minor_chain, BRIEF, "DONE")
    write_files(fe_minor_chain, {f"{TD}/report-01.md": "---\nunit: \"01\"\nstatus: DONE\n---\n# Unit 01\n"})
    git(fe_minor_chain, "commit", "-q", "--allow-empty", "-m", "feat(order-checkout): implement unit 01 - order button")
    c = arch(fe_minor_chain)[4]
    assert c["status"] == "FAIL" and "01" in c["summary"], c
    rep = checks(fe_run(fe_minor_chain, "report/scripts/check_preconditions.py", "--taskdir", TD, "--json"))[4]
    assert rep["status"] == "FAIL" and "tanpa commit unit berkode" in rep["summary"], rep


@pytest.mark.regression("J15")
def test_j15_done_berkode_tetap_sah(fe_minor_chain):
    (fe_minor_chain / TD / "REPORT.md").unlink()
    assert arch(fe_minor_chain)[4]["status"] == "PASS"


# --- J16: stack brief = stack profil -------------------------------------------------------------

@pytest.mark.regression("J16")
def test_j16_stack_brief_beda_profil_fail(fe_minor_chain):
    at_approve(fe_minor_chain)
    write_files(fe_minor_chain, {".claude/profile/index.json": '{"stack":"svelte-vite","source_root":"src"}\n'})
    commit(fe_minor_chain, "chore: profil refresh", ".claude/profile/index.json")
    c = arch(fe_minor_chain, "--brief", "01")[10]
    assert c["status"] == "FAIL" and "svelte-vite" in c["summary"], c


# --- J17: tree tak terbaca tidak pernah bersih ---------------------------------------------------

@pytest.mark.regression("J17")
def test_j17_index_rusak_bukan_bersih(fe_minor_chain):
    (fe_minor_chain / ".git/index").write_bytes(b"garbage")
    c = arch(fe_minor_chain)[8]
    assert c["status"] == "FAIL" and "git status" in c["summary"], c


@pytest.mark.regression("J17")
def test_j17_is_committed_false_bila_status_gagal(fe_minor_chain):
    (fe_minor_chain / ".git/index").write_bytes(b"garbage")
    assert LIB.is_committed(fe_minor_chain, f"{TD}/TASK.md") is False


# --- J18: lane_tamper me-replay riwayat ----------------------------------------------------------

@pytest.fixture
def akar(make_repo):
    return make_repo({f"{OTHER_TD}/TASK.md": TASK})


def retask(repo, lane, sections, event=""):
    """Geser frontmatter lane/sections; `event` = baris kejadian Riwayat yang ikut ditambahkan (tulisan tangan)."""
    p = repo / OTHER_TD / "TASK.md"
    text = re.sub(r"lane: .*\nsections: .*", f"lane: {lane}\nsections: {sections}", p.read_text(encoding="utf-8"))
    p.write_text(text + (event + "\n" if event else ""), encoding="utf-8")


@pytest.mark.regression("J18")
def test_j18_subjek_akar_tiruan_tetap_tamper(akar):
    retask(akar, "FULL_PIPELINE", "[flow, architecture]")
    assert "berubah di luar" in LIB.lane_tamper(akar, OTHER_TD)


@pytest.mark.regression("J18")
def test_j18_eskalasi_turun_atau_badan_palsu_tamper(akar):
    retask(akar, "FAST_FORWARD", "[architecture]", "- 2 · eskalasi · lane HOTFIX_MINOR → FAST_FORWARD · "
           "sections - → architecture · akar 000000000000 · waktu 2026-10-13T00:00:00Z · alasan: x")
    assert LIB.lane_tamper(akar, OTHER_TD) == ""
    retask(akar, "HOTFIX_MINOR", "", "- 3 · eskalasi · lane FAST_FORWARD → HOTFIX_MINOR · "
           "sections architecture → - · akar 000000000000 · waktu 2026-10-13T00:00:00Z · alasan: x")
    assert "tidak monoton" in LIB.lane_tamper(akar, OTHER_TD)


@pytest.mark.regression("J18")
def test_j18_eskalasi_tidak_berangkat_dari_pasangan_terakhir(akar):
    retask(akar, "FULL_PIPELINE", "[flow, architecture]", "- 2 · eskalasi · lane FAST_FORWARD → FULL_PIPELINE · "
           "sections architecture → architecture,flow · akar 000000000000 · waktu 2026-10-13T00:00:00Z · alasan: x")
    assert "tidak berangkat" in LIB.lane_tamper(akar, OTHER_TD)


@pytest.mark.regression("J18")
def test_j18_eskalasi_chain_py_sah(fe_minor_chain):
    (fe_minor_chain / TD / "REPORT.md").unlink()
    ch = "_common/chain.py"
    assert fe_run(fe_minor_chain, ch, "reopen", "--taskdir", TD, "--row", "BRIEF", "--reason", "x").returncode == 0
    r = fe_run(fe_minor_chain, ch, "escalate", "--taskdir", TD, "--lane", "FAST_FORWARD",
               "--sections", "architecture", "--reason", "butuh kontrak")
    assert r.returncode == 0, r.out
    assert LIB.lane_tamper(fe_minor_chain, TD) == ""


# --- J19: `cli()` menangkap OSError --------------------------------------------------------------

@pytest.mark.regression("J19")
def test_j19_root_tidak_ada_json_fail(tmp_path):
    r = run_script(FE_SKILLS / "profile/scripts/check_preconditions.py", "--root", str(tmp_path / "tidak-ada"),
                   "--json")
    assert r.returncode == 1 and json.loads(r.stdout)["status"] == "FAIL", r.stdout + r.stderr


@pytest.mark.regression("J19")
def test_j19_patch_tanpa_git_json_fail(make_repo, tmp_path):
    repo = make_repo({"package.json": json.dumps({"dependencies": {"react": "^19"},
                                                  "devDependencies": {"vite": "^6"}})})
    fe_profile(repo, "react-vite")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    env = {**os.environ, "PATH": str(bindir)}
    r = subprocess.run([sys.executable, str(FE_SKILLS / "profile/scripts/check_preconditions.py"), "--root",
                        str(repo), "--mode", "patch", "--json"], capture_output=True, text=True, env=env)
    c = checks(r)[6]
    assert r.returncode == 1 and c["status"] == "FAIL", c


# --- J20: remedi siklik tanpa RecursionError -----------------------------------------------------

@pytest.mark.regression("J20")
def test_j20_remedi_siklik_tanpa_traceback(fe_minor_chain):
    (fe_minor_chain / TD / "REPORT.md").unlink()
    text = (fe_minor_chain / BRIEF).read_text(encoding="utf-8")
    write_files(fe_minor_chain, {
        f"{TD}/brief-02-order-two.md": text.replace('unit: "01"', 'unit: "02"\nremedies: "01"')
        .replace("status: DONE", "status: BLOCKED"),
        f"{TD}/brief-03-order-three.md": text.replace('unit: "01"', 'unit: "03"')
        .replace("status: DONE", "status: READY").replace("depends_on: []", 'depends_on: ["01"]')})
    set_status(fe_minor_chain, BRIEF, "BLOCKED", remedies='"02"')
    c = arch(fe_minor_chain, "--brief", "03")[11]
    assert c["status"] == "FAIL" and "01" in c["summary"], c


# --- J21: migrasi tidak menimpa berkas tujuan ----------------------------------------------------

@pytest.mark.regression("J21")
def test_j21_tujuan_berisi_tidak_ditimpa(make_repo):
    root = make_repo()
    fe_profile(root, "react-vite", legacy=True)
    commit(root, "profil lama")
    write_files(root, {".claude/profile/frontenddev/visual.md": "# suntingan user\n"})
    r = run_script(MIGRATE, "--root", str(root), "--json")
    assert r.returncode == 1 and "visual.md" in json.loads(r.stdout)["error"], r.stdout
    assert (root / ".claude/profile/frontenddev/visual.md").read_text(encoding="utf-8") == "# suntingan user\n"
    assert (root / ".claude/profile/index.json").is_file() and (root / ".claude/profile/stack.md").is_file()


@pytest.mark.regression("J21")
def test_j21_tujuan_identik_salinan_lama_dibuang(make_repo):
    root = make_repo()
    fe_profile(root, "react-vite", legacy=True)
    commit(root, "profil lama")
    write_files(root, {".claude/profile/frontenddev/visual.md": "# visual\n"})
    r = run_script(MIGRATE, "--root", str(root), "--json")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (root / ".claude/profile/visual.md").exists()
    assert (root / ".claude/profile/frontenddev/index.json").is_file()


@pytest.mark.regression("J21")
def test_j21_migrasi_terputus_disarankan_lanjut(fe_minor_chain):
    (fe_minor_chain / TD / "REPORT.md").unlink()
    (fe_minor_chain / ".claude/profile/frontenddev").mkdir()
    git(fe_minor_chain, "mv", ".claude/profile/stack.md", ".claude/profile/frontenddev/stack.md")
    c = arch(fe_minor_chain)[5]
    assert c["status"] == "FAIL" and "migrate_profile.py" in c["action"], c


# --- J22: REPORT.md tertunda milik rantai --------------------------------------------------------

@pytest.mark.regression("J22")
def test_j22_report_tertunda_bukan_kerja_user(fe_minor_chain):
    write_files(fe_minor_chain, {f"{TD}/REPORT.md": "# Order button — perbaikan label — Report\n\n## Ringkasan\n"})
    c = checks(fe_run(fe_minor_chain, "report/scripts/check_preconditions.py", "--taskdir", TD, "--json"))
    assert c[7]["status"] == "PASS", c[7]                         # dokumen taskdir diabaikan git (Langkah 24)
    assert c[5]["status"] == "FAIL" and "tertunda" in c[5]["summary"] and "Phase 5 butir 4" in c[5]["action"], c[5]


# --- J23: NAMA ganda, race killpg ----------------------------------------------------------------

@pytest.mark.regression("J23")
def test_j23_nama_ganda_ditolak(tmp_path):
    r = runv(tmp_path, "baseline", "t=true", "t=false")
    assert r.returncode == 2 and "ganda" in r.stderr and "Traceback" not in r.stderr, r.stderr


@pytest.mark.regression("J23")
def test_j23_timeout_proses_sudah_keluar(tmp_path, monkeypatch):
    rv = load_module(RUNV, "fe_runv_j23")

    def gone(*_a):
        raise ProcessLookupError

    monkeypatch.setattr(rv.os, "killpg", gone)
    res = rv.run_one("t", "sleep 2", 1, tmp_path, tmp_path)
    assert res["status"] == "TIMEOUT"


@pytest.mark.regression("J23")
def test_j23_log_besar_ekor_dan_tanda_utuh(tmp_path):
    r = runv(tmp_path, "closing", "t=seq 1 200000; echo 'src/z.ts:1:1 - error TS1: x'; exit 1", timeout=30)
    md = (tmp_path / "td/.explore/closing-verification.md").read_text(encoding="utf-8")
    assert r.returncode == 1 and "199999" in md and "src/z.ts" in md, md[-500:]
