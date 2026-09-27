"""Regresi 11 — robustness plugin backend (H1–H36)."""
import json

import pytest

from conftest import PLUGINS, TD, be_checks, be_run, brief, commit, git, land, run_script, write_files

ARCH = "architect/scripts/check_preconditions.py"
VALIDATE = "plan/scripts/validate_briefs.py"
SCAFFOLD = "plan/scripts/scaffold_brief.py"
SCOPE = "_common/verify_scope.py"
GUARD = PLUGINS / "backend/hooks/guard_bash.py"
IMPL = "backend:code-implementor"
REVIEWER = "backend:code-reviewer"

SCOPE_BODY = ("# Brief\n## File scope\n\n**File**\n\n| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n"
              "| modify | `src/order.go` | `Submit` | pasang lock |\n{extra}\n"
              "## Work status\n\n| Item | Status | Catatan |\n|---|---|---|\n| P1-1 | PLANNED | — |\n")


def hook(repo, cmd, agent=IMPL):
    data = {"cwd": str(repo), "tool_name": "Bash", "tool_input": {"command": cmd},
            "hook_event_name": "PreToolUse", "agent_type": agent, "agent_id": "a1"}
    return run_script(GUARD, "hook", stdin=json.dumps(data))


def scoped_brief(repo, extra=""):
    b = brief(repo, "01", "lock", "READY", body=SCOPE_BODY.format(extra=extra))
    commit(repo, "docs(plan): add 1 briefs for order-fix")
    return b


def checks(repo, script, *args):
    proc = be_run(repo, script, "--json", *args)
    assert proc.stdout.strip(), proc.stderr
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


def verify(repo, sha):
    return be_run(repo, SCOPE, "--brief", f"{TD}/brief-01-lock.md", "--commit", sha)


# --- H1: pagar shell ---------------------------------------------------------------------------

@pytest.mark.regression("H1")
@pytest.mark.parametrize("cmd", [
    "git diff $'--output=/tmp/h1'", "git diff --{out,}put=/tmp/h1", "git log --format=$HOME",
    "git diff \"$(echo x)\"", "git status 2>&1", "git log | head", "git commit -m \"a\" -m \"b <c@d>\"",
])
@pytest.mark.parametrize("agent", [IMPL, REVIEWER])
def test_h1_ekspansi_shell_ditolak(chain_repo, agent, cmd):
    scoped_brief(chain_repo)
    assert run_script(GUARD, "lease", "--brief", f"{TD}/brief-01-lock.md", cwd=chain_repo).returncode == 0
    r = hook(chain_repo, cmd, agent)
    assert r.returncode == 2 and "DITOLAK" in r.stderr, (cmd, r.stderr)


@pytest.mark.regression("H1")
@pytest.mark.parametrize("cmd", ['git log -S "<T>" --oneline', "git log -S 'a->b' --oneline",
                                 "git show HEAD@{1} --stat", 'git commit -m "feat: #482 implement lock"'])
def test_h1_kutip_berisi_operator_tetap_lolos(chain_repo, cmd):
    scoped_brief(chain_repo)
    run_script(GUARD, "lease", "--brief", f"{TD}/brief-01-lock.md", cwd=chain_repo)
    assert hook(chain_repo, cmd).returncode == 0, cmd


# --- H2: satu aturan baris File scope ----------------------------------------------------------

@pytest.mark.regression("H2")
def test_h2_baris_berkolom_kurang_tidak_masuk_lease_dan_gagal_check_s(chain_repo):
    scoped_brief(chain_repo, extra="| modify | `src/pay.go` | `Charge` |")
    assert run_script(GUARD, "lease", "--brief", f"{TD}/brief-01-lock.md", cwd=chain_repo).returncode == 0
    allowed = json.loads((chain_repo / ".git/nataflow/lease-backend.json").read_text())["allowed"]
    assert "src/order.go" in allowed and "src/pay.go" not in allowed
    s = checks(chain_repo, VALIDATE, "--taskdir", TD, "--brief", "01")["S"]
    assert s["status"] == "FAIL" and any("berkolom kurang" in d for d in s["details"]), s


@pytest.mark.regression("H2")
def test_h2_heading_beda_huruf_dibaca_lease_dan_ditolak_check_s(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY", body=SCOPE_BODY.format(extra="").replace("## File scope", "## File Scope"))
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    assert run_script(GUARD, "lease", "--brief", str(b.relative_to(chain_repo)), cwd=chain_repo).returncode == 0
    s = checks(chain_repo, VALIDATE, "--taskdir", TD, "--brief", "01")["S"]
    assert any("`## File Scope` wajib ditulis persis `## File scope`" in d for d in s["details"]), s


# --- H3/H4: verify_scope membaca brief sebelum unit ---------------------------------------------

@pytest.mark.regression("H3")
def test_h3_brief_diperluas_pelaksana_ditolak(chain_repo):
    b = scoped_brief(chain_repo)
    b.write_text(b.read_text().replace("| pasang lock |\n", "| pasang lock |\n| modify | `src/other.go` | `X` | y |\n"))
    write_files(chain_repo, {"src/other.go": "package order // liar\n"})
    git(chain_repo, "add", "src/other.go")                 # ikut commit unit di bawah
    r = verify(chain_repo, land(chain_repo, b))
    assert r.returncode == 1 and "disunting di luar" in r.stdout, r.stdout


@pytest.mark.regression("H3")
def test_h3_anchor_diubah_pelaksana_ditolak(chain_repo):
    b = scoped_brief(chain_repo)
    b.write_text(b.read_text().replace("`Submit`", "`Submit`, `Keep`"))
    sha = land(chain_repo, b)
    r = verify(chain_repo, sha)
    assert r.returncode == 1 and "disunting di luar" in r.stdout, r.stdout


@pytest.mark.regression("H3")
def test_h3_status_dan_work_status_sah_disunting(chain_repo):
    b = scoped_brief(chain_repo)
    b.write_text(b.read_text().replace("| P1-1 | PLANNED | — |", "| P1-1 | FIXED | lock terpasang |"))
    sha = land(chain_repo, b)
    r = verify(chain_repo, sha)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.regression("H4")
def test_h4_rename_dari_luar_scope_ditolak(chain_repo):
    write_files(chain_repo, {"src/important.go": "package order\n\nfunc Important() {}\n"})
    commit(chain_repo, "chore: berkas lain", "src/important.go")
    b = scoped_brief(chain_repo, extra="| create | `src/new.go` | — | berkas baru |")
    git(chain_repo, "mv", "src/important.go", "src/new.go")      # rename sungguhan: tujuan belum ada
    b.write_text(b.read_text().replace("status: READY", "status: DONE"))
    sha = commit(chain_repo, "fix(order): implement lock", str(b.relative_to(chain_repo)))
    r = verify(chain_repo, sha)
    assert r.returncode == 1 and "src/important.go" in r.stdout, r.stdout


@pytest.mark.regression("H4")
def test_h4_path_non_ascii_di_scope_lolos(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY", body=SCOPE_BODY.format(extra="").replace("src/order.go", "src/café.go"))
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    r = verify(chain_repo, land(chain_repo, b, code="src/café.go"))
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.regression("H4")
def test_h4_commit_merge_ditolak(chain_repo):
    scoped_brief(chain_repo)
    git(chain_repo, "checkout", "-q", "-b", "side")
    write_files(chain_repo, {"src/side.go": "package order\n"})
    commit(chain_repo, "side", "src/side.go")
    git(chain_repo, "checkout", "-q", "fix/order-fix")
    write_files(chain_repo, {"src/order.go": "package order // lock\n"})
    commit(chain_repo, "fix(order): implement lock", "src/order.go")
    git(chain_repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    r = verify(chain_repo, git(chain_repo, "rev-parse", "HEAD").strip())
    assert r.returncode == 2 and "merge" in r.stderr, r.stderr


# --- H5: koreksi status resmi -------------------------------------------------------------------

@pytest.mark.regression("H5")
def test_h5_koreksi_resmi_diterima_sesi_berikutnya(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    write_files(chain_repo, {"src/order.go": "package order // lock\n"})
    sha = commit(chain_repo, "fix(order): implement lock", "src/order.go")      # status tertinggal
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["entry"] == f"KOREKSI:01:{sha}"
    b.write_text(b.read_text().replace("status: READY", "status: DONE"))
    commit(chain_repo, f"chore(order-fix): koreksi status brief-01 ke DONE ({sha})", str(b.relative_to(chain_repo)))
    brief(chain_repo, "02", "endpoint", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "PASS" and c3["entry"] == "FASE_3:02", c3


@pytest.mark.regression("H5")
def test_h5_done_dokumen_tanpa_commit_unit_tetap_ditolak(chain_repo):
    b = brief(chain_repo, "01", "lock", "READY")
    commit(chain_repo, "docs(plan): add 1 briefs for order-fix")
    b.write_text(b.read_text().replace("status: READY", "status: DONE"))
    commit(chain_repo, "chore(order-fix): koreksi status brief-01 ke DONE (abc1234)", str(b.relative_to(chain_repo)))
    assert be_checks(chain_repo, ARCH, "--taskdir", TD)[3]["status"] == "FAIL"


# --- H6/H7: identitas brief ---------------------------------------------------------------------

@pytest.mark.regression("H6")
def test_h6_commit_message_ganda_gagal_check_c(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    brief(chain_repo, "02", "lock-lagi", "READY", commit_scope="order")
    p = chain_repo / TD / "brief-02-lock-lagi.md"
    p.write_text(p.read_text().replace("implement lock-lagi", "implement lock"))
    c = checks(chain_repo, VALIDATE, "--taskdir", TD)["C"]
    assert c["status"] == "FAIL" and any("`commit_message` sama" in d for d in c["details"]), c


@pytest.mark.regression("H6")
def test_h6_unit_ganda_ditolak_matriks(chain_repo):
    spec = chain_repo / TD / ".explore/brief-spec.json"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps({"briefs": [
        {"nn": "01", "unit": "stock-index", "title": "a", "risk": "MINOR", "fulfills": ["SC-1"]},
        {"nn": "02", "unit": "stock-index", "title": "b", "risk": "MINOR", "fulfills": ["SC-2"]}]}))
    r = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", str(spec))
    assert r.returncode == 1 and "sudah dipakai brief 01" in r.stdout, r.stdout


@pytest.mark.regression("H7")
def test_h7_nn_ganda_gagal_check_c_dan_architect(chain_repo):
    brief(chain_repo, "01", "order-guard", "READY")
    brief(chain_repo, "01", "order-lock", "READY")
    commit(chain_repo, "docs(plan): add 2 briefs for order-fix")
    c = checks(chain_repo, VALIDATE, "--taskdir", TD)["C"]
    assert any("brief-01 dipakai 2 berkas" in d for d in c["details"]), c
    c3 = be_checks(chain_repo, ARCH, "--taskdir", TD)[3]
    assert c3["status"] == "FAIL" and "dipakai 2 berkas" in c3["summary"], c3


@pytest.mark.regression("H7")
def test_h7_brief_ready_di_luar_matriks_gagal(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    brief(chain_repo, "02", "endpoint", "READY")
    write_files(chain_repo, {f"{TD}/.explore/brief-matrix.json": json.dumps(
        {"briefs": [{"nn": "01", "unit": "lock"}]})})
    c = checks(chain_repo, VALIDATE, "--taskdir", TD)["C"]
    assert any("brief-02-endpoint.md: brief READY tidak ada di matriks" in d for d in c["details"]), c


@pytest.mark.regression("H7")
def test_h7_scaffold_menolak_nn_yang_dipakai_unit_lain(chain_repo):
    brief(chain_repo, "01", "order-guard", "READY")
    write_files(chain_repo, {f"{TD}/.explore/brief-matrix.json": json.dumps({"briefs": [
        {"nn": "01", "unit": "order-lock", "title": "t", "risk": "MINOR"}]})})
    r = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--nn", "01")
    assert r.returncode != 0 and "brief-01 sudah dipakai brief-01-order-guard.md" in r.stdout + r.stderr, r.stdout


# --- Tahap 2 -----------------------------------------------------------------------------------

def sections(**over):
    """Badan brief sepuluh seksi; `over` menimpa isi seksi (kunci = judul tanpa spasi/&)."""
    base = {"Objective": "Covers: —\nFulfills: SC-1", "Interfaces": "- Produces: —",
            "File scope": "| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n"
                          "| modify | `src/order.go` | `Submit` | x |",
            "Out of scope": "tidak ada", "Steps": "1. Ubah `Submit`.", "Migration": "tidak perlu",
            "Mirrored paths": "tidak ada", "Risk & rollback": "revert commit", "Work status": "| P1-1 | PLANNED | — |",
            "Analysis trace": "—"}
    base.update({k.replace("_", " "): v for k, v in over.items()})
    return "# Brief\n" + "".join(f"## {k}\n{v}\n\n" for k, v in base.items())


@pytest.mark.regression("H8")
def test_h8_ddl_destruktif_di_steps_menuntut_breaking(chain_repo):
    brief(chain_repo, "01", "lock", "READY", body=sections(Steps="1. Jalankan `ALTER TABLE stock DROP COLUMN qty` di `Submit`."))
    k = checks(chain_repo, VALIDATE, "--taskdir", TD, "--brief", "01")["K"]
    assert k["status"] == "FAIL" and any("`## Steps` memuat DROP COLUMN" in d for d in k["details"]), k


@pytest.mark.regression("H8")
def test_h8_kata_update_di_prosa_bukan_ddl(chain_repo):
    body = sections(File_scope="| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n"
                               "| create | `db/migrations/0001_x.up.sql` | — | x |",
                    Migration="Sesuai langkah 2; update skema stok.\n1. Deploy aplikasi.")
    brief(chain_repo, "01", "lock", "READY", body=body)
    j = checks(chain_repo, VALIDATE, "--taskdir", TD)["J"]
    assert any("tidak memuat DDL konkret" in d for d in j["details"]), j


@pytest.mark.regression("H9")
@pytest.mark.parametrize("state", ["{", "[]", '{"generations": [], "open": null}', '{"total_rounds": "dua"}'])
def test_h9_state_ronde_rusak_fail_terbaca(chain_repo, state):
    brief(chain_repo, "01", "lock", "READY")
    write_files(chain_repo, {f"{TD}/.explore/brief-review-state.json": state})
    r = be_run(chain_repo, VALIDATE, "--taskdir", TD, "--review-state")
    assert r.returncode == 1 and "REVIEW STATE: [FAIL]" in r.stdout and "Traceback" not in r.stderr, (r.stdout, r.stderr)


@pytest.mark.regression("H9")
def test_h9_record_tanpa_open_tidak_melewati_plafon(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    for verdict in ("Issues Found", "Issues Found"):
        assert be_run(chain_repo, VALIDATE, "--taskdir", TD, "--open-round").returncode == 0
        assert be_run(chain_repo, VALIDATE, "--taskdir", TD, "--record-round", verdict).returncode == 0
    r = be_run(chain_repo, VALIDATE, "--taskdir", TD, "--record-round", "Approved")
    assert r.returncode == 1 and "plafon habis" in r.stdout, r.stdout


@pytest.mark.regression("H10")
def test_h10_modify_berkas_buatan_brief_sebelumnya_sah(chain_repo):
    brief(chain_repo, "01", "thing", "READY", body=sections(
        File_scope="| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n| create | `src/thing.go` | — | x |",
        Steps="1. Buat `NewThing` di `src/thing.go`."))
    brief(chain_repo, "02", "wire", "READY", body=sections(
        File_scope="| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n| modify | `src/thing.go` | `NewThing` | x |",
        Steps="1. Panggil `NewThing` dari handler."))
    n = checks(chain_repo, VALIDATE, "--taskdir", TD)["N"]
    assert not any("src/thing.go" in d for d in n["details"]), n


@pytest.mark.regression("H10")
def test_h10_create_ganda_gagal_check_c(chain_repo):
    scope = "| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n| create | `src/thing.go` | — | x |"
    brief(chain_repo, "01", "thing", "READY", body=sections(File_scope=scope))
    brief(chain_repo, "02", "thing-lagi", "READY", body=sections(File_scope=scope))
    c = checks(chain_repo, VALIDATE, "--taskdir", TD)["C"]
    assert any("`src/thing.go` di-`create` 2 brief" in d for d in c["details"]), c


SYMBOL_MAP = PLUGINS / "backend/skills/architect/scripts/symbol_map.py"
JAVA = ("package a;\n\npublic class S {\n    public void submit() {\n        save();\n    }\n\n"
        "    public void cancel() {\n        drop();\n    }\n}\n")


@pytest.mark.regression("H11")
def test_h11_method_lain_yang_dihapus_di_hunk_campuran_tertangkap(make_repo):
    repo = make_repo({"src/S.java": JAVA})
    commit(repo, "base")
    write_files(repo, {"src/S.java": JAVA.replace("public void cancel() {\n        drop();",
                                                 "public void abort() {\n        stop();")})
    sha = commit(repo, "edit")
    r = run_script(SYMBOL_MAP, "--root", str(repo), "--sha", sha, "--path", "src/S.java", "--anchor", "abort")
    out = json.loads(r.stdout)
    assert r.returncode == 1 and "cancel" in {o["symbol"] for o in out["outside_anchor"]}, out


@pytest.mark.regression("H11")
def test_h11_berkas_latin1_tidak_crash_berkode_1(make_repo):
    repo = make_repo()
    (repo / "src").mkdir()
    (repo / "src/S.java").write_bytes(JAVA.replace("save();", "save(); // caf\xe9").encode("latin-1"))
    commit(repo, "base")
    (repo / "src/S.java").write_bytes(JAVA.replace("save();", "save(); // d\xe9j\xe0").encode("latin-1"))
    sha = commit(repo, "edit")
    r = run_script(SYMBOL_MAP, "--root", str(repo), "--sha", sha, "--path", "src/S.java", "--anchor", "submit")
    assert r.returncode == 0 and json.loads(r.stdout)["status"] == "PASS", (r.stdout, r.stderr)


@pytest.mark.regression("H12")
def test_h12_status_huruf_kecil_gagal_check_s(chain_repo):
    brief(chain_repo, "01", "lock", "ready")
    s = checks(chain_repo, VALIDATE, "--taskdir", TD, "--brief", "01")["S"]
    assert any("`status: ready`" in d for d in s["details"]), s


def _profile_template(repo, tpl):
    idx = repo / ".claude/profile/backenddev/index.json"
    data = json.loads(idx.read_text())
    data["commit_template"] = tpl
    idx.write_text(json.dumps(data))


@pytest.mark.regression("H12")
def test_h12_ticket_github_dirender_dan_lolos_check_s(chain_repo):
    _profile_template(chain_repo, "{ticket}: {subject}")
    spec = chain_repo / TD / ".explore/brief-spec.json"
    write_files(chain_repo, {str(spec.relative_to(chain_repo)): json.dumps({"ticket": "#482", "briefs": [
        {"nn": "01", "unit": "lock", "title": "t", "risk": "MINOR", "fulfills": ["SC-1", "SC-2"]}]})})
    assert be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", str(spec)).returncode == 0
    assert be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--nn", "01").returncode == 0
    s = checks(chain_repo, VALIDATE, "--taskdir", TD, "--brief", "01")["S"]
    assert not any("commit_message" in d for d in s["details"]), s


@pytest.mark.regression("H12")
def test_h12_domain_tak_sah_ditolak_sebelum_dirender(chain_repo):
    spec = chain_repo / TD / ".explore/brief-spec.json"
    write_files(chain_repo, {str(spec.relative_to(chain_repo)): json.dumps({"briefs": [
        {"nn": "01", "unit": "lock", "title": "t", "risk": "MINOR", "domain": "Order Stock",
         "fulfills": ["SC-1", "SC-2"]}]})})
    r = be_run(chain_repo, SCAFFOLD, "--taskdir", TD, "--write-matrix", "--spec", str(spec))
    assert r.returncode == 1 and "`domain` \"Order Stock\"" in r.stdout, r.stdout


COUNTERS = "analyst/scripts/chain_counters.py"
ANALYST = "analyst/scripts/check_preconditions.py"


@pytest.mark.regression("H13")
def test_h13_bump_menolak_tabel_yang_diturunkan_tangan(chain_repo):
    task = chain_repo / TD / "TASK.md"
    for _ in range(2):
        assert be_run(chain_repo, COUNTERS, "--taskdir", TD, "--bump", "reject:PRD").returncode == 0
    commit(chain_repo, "docs(order-fix): counters", f"{TD}/TASK.md")
    task.write_text(task.read_text().replace("| reject:PRD | 2 |", "| reject:PRD | 0 |"))
    r = be_run(chain_repo, COUNTERS, "--taskdir", TD, "--bump", "reject:PRD")
    assert r.returncode == 1 and "disunting tangan" in r.stdout, r.stdout
    c7 = checks(chain_repo, ANALYST, "--taskdir", TD, "--risk", "MINOR", "--chain", "BRIEF")[7]
    assert c7["status"] == "FAIL" and "reject:PRD turun 2 → 0" in c7["summary"], c7


# --- Tahap 3: run_verification (be=fe) ---------------------------------------------------------

RUNV = PLUGINS / "backend/skills/_common/run_verification.py"


def runv(tmp_path, mode, *cmds, timeout=None):
    args = [mode, "--taskdir", str(tmp_path / "td")] + [a for c in cmds for a in ("--cmd", c)]
    return run_script(RUNV, *args, *(["--timeout", str(timeout)] if timeout else []), cwd=tmp_path)


@pytest.mark.regression("H14")
def test_h14_diagnostik_kompilator_tanpa_kata_galat_terhitung_baru(tmp_path):
    assert runv(tmp_path, "baseline", "build=printf 'a/a.go:2:23: undefined: x\\n'; exit 1").returncode == 0
    r = runv(tmp_path, "closing",
             "build=printf 'a/a.go:2:23: undefined: x\\nb/b.go:5:1: undefined: brokenY\\n'; exit 1")
    assert r.returncode == 1 and "baru=1" in r.stdout, r.stdout


@pytest.mark.regression("H14")
@pytest.mark.parametrize("closing,rc", [("echo alpha; exit 3", 0), ("echo beta; exit 3", 1)])
def test_h14_merah_tanpa_tanda_dibandingkan_lewat_ekor_log(tmp_path, closing, rc):
    assert runv(tmp_path, "baseline", "build=echo alpha; exit 3").returncode == 0
    assert runv(tmp_path, "closing", f"build={closing}").returncode == rc


@pytest.mark.regression("H14")
def test_h14_perintah_tidak_ditemukan_selalu_merah(tmp_path):
    runv(tmp_path, "baseline", "test=./mvnw-tidak-ada test")
    r = runv(tmp_path, "closing", "test=./mvnw-tidak-ada test")
    assert r.returncode == 1 and "exit=127" in r.stdout, r.stdout


@pytest.mark.regression("H15")
def test_h15_timeout_warisan_memberi_jalan_keluar(tmp_path):
    b = runv(tmp_path, "baseline", "test=sleep 3", timeout=1)
    assert "--timeout 3 --force" in b.stdout, b.stdout
    r = runv(tmp_path, "closing", "test=sleep 3", timeout=1)
    md = (tmp_path / "td/.explore/closing-verification.md").read_text()
    assert r.returncode == 1 and "TIMEOUT warisan" in md, md


@pytest.mark.regression("H16")
def test_h16_nama_perintah_berisi_garis_miring_ditolak_rapi(tmp_path):
    r = runv(tmp_path, "baseline", "a/b=true")
    assert r.returncode == 2 and "NAMA --cmd" in r.stderr and "Traceback" not in r.stderr, r.stderr


@pytest.mark.regression("H16")
def test_h16_baseline_bukan_objek_dianggap_rusak(tmp_path):
    (tmp_path / "td/.explore").mkdir(parents=True)
    (tmp_path / "td/.explore/verification-baseline.json").write_text("[]")
    r = runv(tmp_path, "closing", "build=true")
    assert r.returncode == 0 and "PERINGATAN" in r.stdout and "Traceback" not in r.stderr, r.stderr


# --- Tahap 4: prasyarat & gerbang dokumen ------------------------------------------------------

import os          # noqa: E402
import subprocess  # noqa: E402
import sys         # noqa: E402

from conftest import be_profile, load_module  # noqa: E402

SA = "system-analysis/scripts/check_preconditions.py"
BA = "business-analysis/scripts/check_preconditions.py"
PLAN_PRE = "plan/scripts/check_preconditions.py"
TASK_PRE = "task/scripts/check_preconditions.py"
TECH = "tech-lead/scripts/check_preconditions.py"
TD2 = "backenddev/docs/2601011200-refund"


@pytest.fixture
def spec_repo(make_repo):
    """Taskdir `refund` ber-TASK `chain: BRD_PRD_BRIEF` di branch kerja `feat/refund`."""
    root = make_repo({f"{TD2}/TASK.md": "---\nchain: BRD_PRD_BRIEF\nrisk: MAJOR\n---\n# T\n", "src/a.go": "package a\n"})
    git(root, "checkout", "-q", "-b", "main")
    be_profile(root, "go")
    commit(root, "init")
    git(root, "checkout", "-q", "-b", "feat/refund")
    return root


def sa_c(repo, *extra):
    return checks(repo, SA, "--root", str(repo), "--taskdir", TD2, "--risk-level", "MAJOR", *extra)


BRD_OK = "---\ntitle: Refund\nrequester: ops\nstatus: APPROVED\n---\n# BRD\n\n## Business rules\n- **BR-1**: x.\n"


@pytest.mark.regression("H17")
def test_h17_brd_approved_tanpa_commit_approve_ditolak(spec_repo):
    write_files(spec_repo, {f"{TD2}/BRD.md": BRD_OK})
    c = sa_c(spec_repo)[1]
    assert c["status"] == "FAIL" and "belum ter-commit" in c["summary"], c
    commit(spec_repo, "docs(spec): draft BRD refund", f"{TD2}/BRD.md")      # APPROVED di commit draft
    c = sa_c(spec_repo)[1]
    assert c["status"] == "FAIL" and "tidak terikat persetujuan user" in c["summary"], c


@pytest.mark.regression("H17")
def test_h17_brd_disunting_sesudah_approve_ditolak(spec_repo):
    write_files(spec_repo, {f"{TD2}/BRD.md": BRD_OK})
    commit(spec_repo, "docs(spec): approve BRD refund", f"{TD2}/BRD.md")
    assert sa_c(spec_repo)[1]["status"] == "PASS"
    write_files(spec_repo, {f"{TD2}/BRD.md": BRD_OK.replace("x.", "berubah sesudah approval.")})
    c = sa_c(spec_repo)[1]
    assert c["status"] == "FAIL" and "berubah sesudah commit terakhirnya" in c["summary"], c


@pytest.mark.regression("H17")
def test_h17_prd_approved_tanpa_commit_approve_ditolak_plan(spec_repo):
    write_files(spec_repo, {f"{TD2}/PRD.md": "---\ntitle: R\nsource_brd: x\nstatus: APPROVED\n---\n# PRD\n"})
    commit(spec_repo, "docs(spec): draft PRD refund", f"{TD2}/PRD.md")
    c = checks(spec_repo, PLAN_PRE, "--root", str(spec_repo), "--taskdir", TD2, "--entry-mode", "PRD",
               "--chain", "BRD_PRD_BRIEF")[3]
    assert c["status"] == "FAIL" and "tidak terikat" in c["summary"], c


@pytest.mark.regression("H18")
def test_h18_parameter_chain_tidak_boleh_melompati_ledger(spec_repo):
    c = sa_c(spec_repo, "--chain", "PRD_BRIEF")[1]
    assert c["status"] == "FAIL" and "berbeda dari parameter PRD_BRIEF" in c["summary"], c


@pytest.mark.regression("H18")
def test_h18_kunci_chain_ganda_tetap_dilaporkan_walau_parameter_diisi(spec_repo):
    write_files(spec_repo, {f"{TD2}/TASK.md": "---\nchain: BRD_PRD_BRIEF\nchain: PRD_BRIEF\n---\n# T\n"})
    assert sa_c(spec_repo, "--chain", "BRD_PRD_BRIEF")[1]["status"] == "FAIL"
    ba = checks(spec_repo, BA, "--root", str(spec_repo), "--taskdir", TD2, "--chain", "BRD_PRD_BRIEF")[7]
    assert ba["status"] == "FAIL", ba


@pytest.mark.regression("H19")
def test_h19_perubahan_ter_stage_di_luar_taskdir_ditolak(spec_repo):
    write_files(spec_repo, {"src/a.go": "package a // staged\n"})
    git(spec_repo, "add", "src/a.go")
    assert "src/a.go" in sa_c(spec_repo)[6]["summary"]
    ba = checks(spec_repo, BA, "--root", str(spec_repo), "--taskdir", TD2, "--chain", "BRD_PRD_BRIEF")[5]
    assert ba["status"] == "FAIL" and "src/a.go" in ba["summary"], ba


@pytest.mark.regression("H20")
@pytest.mark.parametrize("branch", ["main", "feat/other-chain"])
def test_h20_akar_tidak_di_commit_di_luar_branch_taskdir(spec_repo, branch):
    git(spec_repo, "checkout", "-q", "-B", branch)
    c = checks(spec_repo, TASK_PRE, "--root", str(spec_repo), "--taskdir", TD2, "--lane", "PRD_CONVERSION",
               "--chain", "PRD_BRIEF")[5]
    assert c["status"] == "FAIL", c


@pytest.mark.regression("H21")
def test_h21_root_tidak_ada_json_fail(tmp_path):
    r = be_run(tmp_path, TECH, "--root", str(tmp_path / "tidak-ada"), "--json")
    assert json.loads(r.stdout)["status"] == "FAIL" and "Traceback" not in r.stderr, r.stderr


@pytest.mark.regression("H21")
def test_h21_git_tidak_di_path_json_fail(spec_repo, tmp_path):
    env = {**os.environ, "PATH": str(tmp_path)}
    r = subprocess.run([sys.executable, str(PLUGINS / "backend/skills" / TECH), "--read-only", "--json"],
                       cwd=spec_repo, capture_output=True, text=True, env=env, timeout=60)
    assert r.stdout.strip() and json.loads(r.stdout)["status"] == "FAIL" and "Traceback" not in r.stderr, r.stderr


@pytest.mark.regression("H22")
def test_h22_index_bertipe_salah_fail_terbaca(spec_repo):
    idx = spec_repo / ".claude/profile/backenddev/index.json"
    data = json.loads(idx.read_text())
    data["source_root"] = ["src"]
    idx.write_text(json.dumps(data))
    r = be_run(spec_repo, TECH, "--root", str(spec_repo), "--read-only", "--json")
    c1 = {c["id"]: c for c in json.loads(r.stdout)["checks"]}[1]
    assert "Traceback" not in r.stderr and "wajib string" in c1["summary"], (c1, r.stderr)


@pytest.mark.regression("H23")
def test_h23_source_brd_tidak_ada_padahal_brd_ada_gagal_p1(spec_repo):
    write_files(spec_repo, {f"{TD2}/BRD.md": BRD_OK,
                            f"{TD2}/PRD.md": "---\ntitle: R\nsource_brd: tidak ada\nstatus: DRAFT\n---\n# PRD\n"})
    r = be_run(spec_repo, "_common/validate_doc.py", "--kind", "prd", "--taskdir", TD2, "--root", str(spec_repo), "--json")
    p1 = {c["id"]: c for c in json.loads(r.stdout)["checks"]}["P1"]
    assert p1["status"] == "FAIL", p1


@pytest.mark.regression("H24")
def test_h24_migrasi_terputus_dapat_dilanjutkan(make_repo, monkeypatch):
    root = make_repo()
    be_profile(root, "go", legacy=True)
    commit(root, "profil lama")
    mp = load_module(PLUGINS / "backend/skills/profile/scripts/migrate_profile.py", "mp_h24")
    calls = {"n": 0}

    def putus(*_a, **_k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise KeyboardInterrupt
        return False
    monkeypatch.setattr(mp, "_git_mv", putus)
    with pytest.raises(KeyboardInterrupt):
        mp.migrate(root)
    assert (root / ".claude/profile/index.json").is_file()        # index.json belum dipindah
    monkeypatch.undo()
    moved, _ = mp.migrate(root)
    assert "index.json" in moved and (root / ".claude/profile/backenddev/index.json").is_file()


@pytest.mark.regression("H25")
def test_h25_set_frontmatter_menimpa_kunci_berspasi(tmp_path):
    bs = load_module(PLUGINS / "backend/skills/_common/brief_status.py", "bs_h25")
    f = tmp_path / "brief-01-x.md"
    f.write_text("--- \nstatus : READY\ntitle: x\n---\nbody\n")
    bs.set_frontmatter(f, status="SUPERSEDED")
    assert bs.read_frontmatter(f) == {"status": "SUPERSEDED", "title": "x"}


# --- Tahap 5: orkestrasi -------------------------------------------------------------------------

from conftest import run_hook  # noqa: E402

BE = PLUGINS / "backend"


@pytest.mark.regression("H26")
def test_h26_taskdir_tanpa_ledger_gagal_check_7(chain_repo):
    task = chain_repo / TD / "TASK.md"
    task.write_text("---\nlane: DEFECT_RCA\nrisk: MINOR\nstatus: ACTIVE\n---\n# Fix\n## Success Criteria\n- SC-1 x\n")
    commit(chain_repo, "docs(order-fix): akar", f"{TD}/TASK.md")
    c7 = checks(chain_repo, ANALYST, "--taskdir", TD, "--risk", "MINOR", "--chain", "BRIEF")[7]
    assert c7["status"] == "FAIL" and "tanpa ledger" in c7["summary"] and "RCA" in c7["action"], c7


@pytest.mark.regression("H26")
def test_h26_gerbang_merutekan_taskdir_tanpa_ledger_ke_rca():
    lifecycle = (BE / "skills/tech-lead/references/gate-lifecycle.md").read_text(encoding="utf-8")
    skill = (BE / "skills/tech-lead/SKILL.md").read_text(encoding="utf-8")
    assert "Taskdir **tanpa ledger `## Chain`**" in lifecycle and "`entry_mode: RCA`" in lifecycle
    assert "kecuali taskdir **tanpa ledger `## Chain`**" in skill


@pytest.mark.regression("H27")
def test_h27_penolakan_user_menolkan_ronde_reviewer_hop(chain_repo):
    for key in ("review_round:BRD", "review_round:BRD"):
        assert be_run(chain_repo, COUNTERS, "--taskdir", TD, "--bump", key).returncode == 0
    commit(chain_repo, "docs(order-fix): ronde", f"{TD}/TASK.md")
    r = be_run(chain_repo, COUNTERS, "--taskdir", TD, "--bump", "reject:BRD")
    assert r.returncode == 0 and "review_round:BRD dinolkan" in r.stdout, r.stdout
    commit(chain_repo, "docs(order-fix): tolak", f"{TD}/TASK.md")
    assert be_run(chain_repo, COUNTERS, "--taskdir", TD, "--bump", "review_round:BRD").returncode == 0
    assert be_run(chain_repo, COUNTERS, "--taskdir", TD, "--check").returncode == 0      # bukan tamper


@pytest.mark.regression("H27")
def test_h27_reentry_membuka_generasi_ronde_brief_baru(chain_repo):
    brief(chain_repo, "01", "lock", "READY")
    for _ in range(2):
        assert be_run(chain_repo, VALIDATE, "--taskdir", TD, "--open-round").returncode == 0
        assert be_run(chain_repo, VALIDATE, "--taskdir", TD, "--record-round", "Issues Found").returncode == 0
    assert be_run(chain_repo, VALIDATE, "--taskdir", TD, "--open-round").returncode == 1
    assert be_run(chain_repo, COUNTERS, "--taskdir", TD, "--bump", "reentry").returncode == 0
    r = be_run(chain_repo, VALIDATE, "--taskdir", TD, "--open-round")
    assert r.returncode == 0 and "ronde 1 dibuka" in r.stdout, r.stdout


@pytest.mark.regression("H28")
def test_h28_plafon_tertembus_punya_jalan_keluar_user():
    skill = (BE / "skills/tech-lead/SKILL.md").read_text(encoding="utf-8")
    assert "**Plafon tertembus**" in skill and "**rumuskan ulang di taskdir baru**" in skill
    analyst = (BE / "skills/analyst/SKILL.md").read_text(encoding="utf-8")
    assert "mengklasifikasi ulang permintaan dari awal" not in analyst


@pytest.mark.regression("H29")
@pytest.mark.parametrize("value", ["backend", "backenddev"])
def test_h29_nilai_plugin_nama_tampilan_milik_sendiri(make_repo, value):
    root = make_repo({"go.mod": "module x\n\ngo 1.22\n"})
    be_profile(root, "go", extra={"plugin": value})
    proc, _ = run_hook("backenddev", root, explain=True)
    assert json.loads(proc.stdout)["profile"]["state"] == "OK", proc.stdout
    text = (BE / "skills/profile/templates/profile-template.md").read_text(encoding="utf-8")
    assert '`plugin` selalu `"backenddev"`' in text


@pytest.mark.regression("H30")
def test_h30_audit_dan_api_docs_tanpa_branch_baru():
    skill = (BE / "skills/tech-lead/SKILL.md").read_text(encoding="utf-8")
    assert "`AUDIT_SWEEP` (di `base_branch`) dan `API_DOCS` (di branch aktif): butir 0 saja, tanpa branch baru" in skill
    decisions = (BE / "skills/tech-lead/references/decisions.md").read_text(encoding="utf-8")
    assert "`AUDIT_SWEEP` dan `API_DOCS` tidak membuat branch kerja maupun taskdir" in decisions


@pytest.mark.regression("H20")
def test_h20_akar_defect_rca_sesudah_isolasi_branch():
    skill = (BE / "skills/tech-lead/SKILL.md").read_text(encoding="utf-8")
    assert skill.index("2. **Isolasi branch**") < skill.index("2a. **Akar `DEFECT_RCA`**")
    assert "Lane `DEFECT_RCA` → panggil `backend:task` di sini" not in skill


@pytest.mark.regression("H31")
def test_h31_instruksi_agent_selaras_dengan_pagar():
    impl = (BE / "agents/code-implementor.md").read_text(encoding="utf-8")
    rev = (BE / "agents/code-reviewer.md").read_text(encoding="utf-8")
    assert "Nomor migrasi bentrok → ambil nomor berikutnya" not in impl and "tanpa trailer" in impl
    assert "$(git merge-base" not in rev
    disp = (BE / "skills/architect/dispatcher/reviewer.md").read_text(encoding="utf-8")
    assert "`git merge-base {base_branch} HEAD`..`HEAD`" not in disp and "bukan substitusi" in disp


@pytest.mark.regression("H33")
def test_h33_reviewer_punya_edit_dan_hook_mengizinkannya(chain_repo):
    assert "tools: Read, Grep, Glob, Bash, Write, Edit" in (BE / "agents/code-reviewer.md").read_text(encoding="utf-8")
    data = {"cwd": str(chain_repo), "tool_name": "Edit", "hook_event_name": "PreToolUse", "agent_type": REVIEWER,
            "tool_input": {"file_path": str(chain_repo / "backenddev/issues/README.md"), "old_string": "a",
                           "new_string": "b"}}
    assert run_script(GUARD, "hook", stdin=json.dumps(data)).returncode == 0


@pytest.mark.regression("H36")
def test_h36_gate_text_gagal_tetap_menyuntik_gerbang(make_repo, tmp_path):
    import shutil
    plugin = tmp_path / "plug"
    shutil.copytree(BE / "hooks", plugin / "hooks")
    shutil.copytree(BE / "skills/_common", plugin / "skills/_common")
    (plugin / "hooks/gate_text.py").write_text("def render(v):\n    raise RuntimeError('rusak')\n")
    root = make_repo({"go.mod": "module x\n\ngo 1.22\n"})
    be_profile(root, "go")
    r = run_script(plugin / "hooks/detect.py", "--plugin", "backend",
                   stdin=json.dumps({"cwd": str(root), "hook_event_name": "SessionStart"}))
    out = json.loads(r.stdout)
    assert r.returncode == 0 and "gagal dirender" in out["hookSpecificOutput"]["additionalContext"], (r.stdout, r.stderr)
