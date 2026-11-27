"""Review lapangan hkm 2611 — B5 (validate_briefs keras ke Rust/test), B6 (stack Rust membuat unit BLOCKED),
B11 (bukti `path:baris` basename)."""
import json
import re

import pytest

from conftest import (BE_SKILLS, PLUGINS, TD, be_run, brief, commit, git, load_module, run_script,
                      write_files)

VB = "plan/scripts/validate_briefs.py"
GUARD = PLUGINS / "backend/hooks/guard_bash.py"
SCOPE = PLUGINS / "backend/skills/_common/verify_scope.py"
CLOSE = BE_SKILLS / "architect/scripts/close_brief.py"
VD = BE_SKILLS / "_common/validate_doc.py"
IMPL = "backend:code-implementor"

TASK = """---
status: ACTIVE
chain: BRIEF
risk: MINOR
---
# Modul
## Success Criteria
- [ ] **SC-1**: modul terpasang
## Out of Scope
- `src/payment/` — tidak disentuh
"""


def brief_text(rows, steps="1. Ubah modul."):
    return f"""---
title: brief 01
source: TASK.md
risk: MINOR
status: READY
commit_message: "feat(modul): implement modul"
---
# Brief: brief 01 — 2026-01-01
## Objective
Kerjakan modul.

Fulfills: SC-1
## Interfaces
- Produces: `Modul`
## File scope
**File**

| Aksi | Path | Anchor | Apa yang berubah |
|---|---|---|---|
{rows}
## Out of scope
lain
## Steps
{steps}
## Migration
tidak perlu
## Mirrored paths
tidak ada
## Risk & rollback
Rollback: revert commit.
## Work status
| Item | Status | Catatan |
|---|---|---|
| P1-1 | PLANNED | — |
## Analysis trace
Tidak ada.
"""


@pytest.fixture
def vrepo(make_repo):
    return make_repo({f"{TD}/TASK.md": TASK})


def vcheck(repo, cid, rows, *args, steps="1. Ubah modul."):
    write_files(repo, {f"{TD}/brief-01-modul.md": brief_text(rows, steps)})
    proc = be_run(repo, VB, "--root", str(repo), "--taskdir", TD, "--json", *args)
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}[cid]


def violations(c):
    return [d for d in c.get("details") or [] if "TERDEGRADASI" not in d]


def rows(*paths, aksi="create"):
    return "\n".join(f"| {aksi} | `{p}` | — | x |" for p in paths)


# -- B5: Check E membaca slot File Scope bebas ------------------------------------------------------

@pytest.mark.regression("B5")
@pytest.mark.parametrize("scope, paths", [
    ("crates/report/daily/{domain,application,adapter} (modul baru, sesuai PRD) · Cargo.toml root · "
     "src/server/{state.rs,router.rs} · tests/ (test daily_report baru)",
     ["crates/report/daily/domain/src/lib.rs", "crates/report/daily/adapter/src/module.rs",
      "src/server/router.rs", "tests/daily_report_test.rs", "Cargo.lock"]),
    ("crates/transactional/put-away/{domain,application,adapter}; src/server/router.rs; "
     "Cargo.toml root (+Cargo.lock bila dependensi crate berubah); tests/put_away_*_test.rs",
     ["crates/transactional/put-away/domain/src/error.rs", "tests/put_away_error_test.rs", "Cargo.lock"]),
    ("modules/stock/opname/resolution/** · modules/stock/meta/** (baca)",
     ["src/main/java/id/hkm/oms/modules/stock/opname/resolution/followup/FollowUp.java"]),
])
def test_e_file_scope_bebas(vrepo, scope, paths):
    c = vcheck(vrepo, "E", rows(*paths), "--file-scope", scope)
    assert violations(c) == [], c


@pytest.mark.regression("B5")
def test_e_pasangan_test_dari_path_dalam_scope(vrepo):
    scope = ("src/service/report_service.rs, src/main/java/id/hkm/order/OrderService.java, "
             "src/server/router.rs, crates/x/adapter/src/lib.rs")
    paths = ["src/service/report_service_test.rs",
             "src/test/java/id/hkm/order/OrderServiceRollbackTest.java",
             "tests/common/mod.rs", "crates/x/adapter/tests/wiring.rs"]
    assert violations(vcheck(vrepo, "E", rows(*paths), "--file-scope", scope)) == []


@pytest.mark.regression("B5")
@pytest.mark.parametrize("scope, path", [
    ("src/service/report_service.rs", "src/service/other.rs"),          # produksi di luar batas
    ("src/service/report_service.rs", "Cargo.lock"),                    # tanpa Cargo.toml di batas
    ("src/refund", "src/refundhistory/store_test.go"),                  # segmen, bukan substring
    ("crates/a/src/lib.rs", "crates/b/tests/x.rs"),                     # test crate lain
])
def test_e_kontrol_negatif(vrepo, scope, path):
    c = vcheck(vrepo, "E", rows(path), "--file-scope", scope)
    assert c["status"] == "FAIL" and any(path in d for d in violations(c)), c


@pytest.mark.regression("B5")
def test_e_file_scope_prosa_saja_terdegradasi(vrepo):
    c = vcheck(vrepo, "E", rows("src/x.go"), "--file-scope", "modul baru sesuai PRD")
    assert any("tanpa satu pun pola path" in d for d in c["details"]), c


@pytest.mark.regression("B5")
def test_is_test_path_tests_di_awal():
    mod = load_module(BE_SKILLS / VB, "vb_b5")
    assert mod._is_test_path("tests/common/mod.rs") and mod._is_test_path("test/helper.js")
    assert not mod._is_test_path("src/core/mod.rs")


# -- B5: Check N — berkas kosong dan TOML ----------------------------------------------------------

@pytest.mark.regression("B5")
def test_n_berkas_kosong_sentinel(vrepo):
    write_files(vrepo, {"crates/a/adapter/src/lib.rs": ""})
    row = "| modify | `crates/a/adapter/src/lib.rs` | `(berkas kosong)` | deklarasi modul |"
    c = vcheck(vrepo, "N", row)
    assert c["status"] == "PASS", c
    for anchor in ("berkas kosong, titik sisip baris 1", "crate root kosong"):
        assert vcheck(vrepo, "N", row.replace("(berkas kosong)", anchor))["status"] == "PASS"


@pytest.mark.regression("B5")
def test_n_berkas_kosong_anchor_simbol_gagal_berpetunjuk(vrepo):
    write_files(vrepo, {"crates/a/adapter/src/lib.rs": "\n"})
    c = vcheck(vrepo, "N", "| modify | `crates/a/adapter/src/lib.rs` | `module_init` | x |",
               steps="1. Isi `module_init`.")
    assert c["status"] == "FAIL" and any("(berkas kosong)" in d for d in c["details"]), c


@pytest.mark.regression("B5")
@pytest.mark.parametrize("anchor", ["delivery-order_domain", "[workspace.dependencies]", "members"])
def test_n_toml_kunci_dan_section_deklarasi(vrepo, anchor):
    write_files(vrepo, {"Cargo.toml": '[workspace]\nmembers = [\n  "crates/a",\n]\n\n[workspace.dependencies]\n'
                                      'delivery-order_domain = { path = "crates/do/domain" }\n'})
    c = vcheck(vrepo, "N", f"| modify | `Cargo.toml` | `{anchor}` | tambah anggota |",
               steps=f"1. Sunting `{anchor}` di `Cargo.toml`.")
    assert c["status"] == "PASS", c


# -- B6: aksi delete --------------------------------------------------------------------------------

@pytest.mark.regression("B6")
def test_n_delete_wajib_berkas_ada(vrepo):
    write_files(vrepo, {"src/old.rs": "pub fn old() {}\n"})
    assert vcheck(vrepo, "N", "| delete | `src/old.rs` | — | hapus |")["status"] == "PASS"
    c = vcheck(vrepo, "N", "| delete | `src/hilang.rs` | — | hapus |")
    assert c["status"] == "FAIL" and any("delete" in d for d in c["details"]), c


DEL_BODY = ("# Brief\n## File scope\n**File**\n\n| Aksi | Path | Anchor | Apa |\n|---|---|---|---|\n"
            "| modify | `src/order.go` | `Submit` | lock |\n| delete | `src/old.go` | — | hapus |\n\n## Steps\n1. x\n")


@pytest.fixture
def drepo(chain_repo):
    write_files(chain_repo, {"src/old.go": "package order\n"})
    commit(chain_repo, "old", "src/old.go")
    brief(chain_repo, "01", "lock", "READY", body=DEL_BODY)
    return chain_repo


def hook(repo, cmd):
    data = {"cwd": str(repo), "tool_name": "Bash", "tool_input": {"command": cmd},
            "hook_event_name": "PreToolUse", "agent_type": IMPL, "agent_id": "a1"}
    return run_script(GUARD, "hook", stdin=json.dumps(data))


@pytest.mark.regression("B6")
def test_lease_mencatat_delete(drepo):
    out = run_script(GUARD, "lease", "--brief", f"{TD}/brief-01-lock.md", cwd=drepo)
    assert out.returncode == 0 and "1 delete" in out.stdout
    data = json.loads((drepo / ".git/nataflow/lease-backend.json").read_text())
    assert data["delete"] == ["src/old.go"] and "src/old.go" in data["allowed"]


@pytest.mark.regression("B6")
@pytest.mark.parametrize("cmd, rc", [
    ("git rm -- src/old.go", 0),
    ("git rm src/old.go", 0),
    ("git rm -q -- src/old.go", 0),
    ("git rm -- src/order.go", 2),          # baris modify, bukan delete
    ("git rm -- .env", 2),                  # di luar lease
    ("git rm -r -- src/old.go", 2),
    ("git rm -f src/old.go", 2),
    ("git rm --cached -- src/old.go", 2),
    ("git rm", 2),
    ("git rm -- 'src/*.go'", 2),
])
def test_git_rm_hanya_baris_delete(drepo, cmd, rc):
    run_script(GUARD, "lease", "--brief", f"{TD}/brief-01-lock.md", cwd=drepo)
    out = hook(drepo, cmd)
    assert out.returncode == rc, (cmd, out.stderr)


@pytest.mark.regression("B6")
def test_lease_lama_tanpa_delete_menolak_git_rm(drepo):
    lp = drepo / ".git/nataflow/lease-backend.json"
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(json.dumps({"brief": f"{TD}/brief-01-lock.md", "allowed": ["src/old.go"]}))
    assert hook(drepo, "git rm -- src/old.go").returncode == 2


@pytest.mark.regression("B6")
def test_verify_scope_menerima_penghapusan(drepo):
    git(drepo, "rm", "-q", "--", "src/old.go")
    git(drepo, "commit", "-qm", "fix(order): implement lock")
    sha = git(drepo, "rev-parse", "--short=7", "HEAD").strip()
    out = run_script(SCOPE, "--brief", f"{TD}/brief-01-lock.md", "--commit", sha, cwd=drepo)
    assert out.returncode == 0, out.stdout + out.stderr


# -- B6: Cargo.lock pendamping turunan -----------------------------------------------------------

CARGO_BODY = ("# Brief\n## File scope\n**File**\n\n| Aksi | Path | Anchor | Apa |\n|---|---|---|---|\n"
              "| modify | `Cargo.toml` | `members` | anggota baru |\n\n## Steps\n1. Tambah anggota ke `members`.\n")
CARGO = '[workspace]\nmembers = [\n  "crates/a",\n]\n'
LOCK = "version = 3\n"


@pytest.fixture
def crepo(chain_repo):
    write_files(chain_repo, {"Cargo.toml": CARGO, "Cargo.lock": LOCK})
    commit(chain_repo, "cargo", "Cargo.toml", "Cargo.lock")
    path = brief(chain_repo, "01", "anggota", "DONE", body=CARGO_BODY)
    return chain_repo, path


def unit(repo, toml=True):
    write_files(repo, {"Cargo.toml": CARGO.replace('"crates/a",', '"crates/a",\n  "crates/b",')} if toml
                else {"src/order.go": "package order\n// x\n"})
    return commit(repo, "fix(order): implement anggota", "Cargo.toml" if toml else "src/order.go")


def close(repo, path, sha):
    proc = run_script(CLOSE, "--brief", str(path), "--sha", sha, "--json", cwd=repo)
    return proc.returncode, json.loads(proc.stdout)


@pytest.mark.regression("B6")
def test_close_brief_commit_sinkron_cargo_lock(crepo):
    repo, path = crepo
    sha = unit(repo)
    write_files(repo, {"Cargo.lock": LOCK + "[[package]]\nname = \"b\"\n"})   # regenerasi gerbang 3b
    code, out = close(repo, path, sha)
    assert code == 0 and out["verdict"] == "PASS", out
    assert out["stray"] == [] and out["lock_sync"].startswith("Cargo.lock @ ")
    assert git(repo, "log", "-1", "--format=%s").strip() == "chore(order): sinkron Cargo.lock brief-01"
    assert git(repo, "status", "--porcelain").strip() == ""
    assert git(repo, "show", "--name-only", "--format=", "HEAD").split() == ["Cargo.lock"]


@pytest.mark.regression("B6")
def test_close_brief_cargo_lock_tanpa_manifest_tetap_stray(crepo):
    repo, path = crepo
    sha = unit(repo, toml=False)
    write_files(repo, {"Cargo.lock": LOCK + "# x\n"})
    code, out = close(repo, path, sha)
    assert code == 1 and out["verdict"] == "STRAY" and out["stray"] == ["Cargo.lock"], out
    assert out["lock_sync"] == ""


@pytest.mark.regression("B6")
def test_close_brief_cargo_lock_bersama_berkas_lain_tetap_stray(crepo):
    repo, path = crepo
    sha = unit(repo)
    write_files(repo, {"Cargo.lock": LOCK + "# x\n", "src/liar.go": "package x\n"})
    code, out = close(repo, path, sha)
    assert code == 1 and out["verdict"] == "STRAY" and set(out["stray"]) == {"Cargo.lock", "src/liar.go"}


@pytest.mark.regression("B6")
def test_verify_scope_cargo_lock_pendamping(crepo):
    repo, path = crepo
    write_files(repo, {"Cargo.toml": CARGO + "\n", "Cargo.lock": LOCK + "# x\n"})
    sha = commit(repo, "fix(order): implement anggota", "Cargo.toml", "Cargo.lock")
    assert run_script(SCOPE, "--brief", str(path), "--commit", sha, cwd=repo).returncode == 0
    vs = load_module(SCOPE, "verify_scope_b6")
    assert vs.lock_companion("Cargo.lock", {"crates/a/Cargo.toml"})
    assert vs.lock_companion("crates/a/Cargo.lock", {"crates/a/Cargo.toml"})
    assert not vs.lock_companion("crates/a/Cargo.lock", {"Cargo.toml"})
    assert not vs.lock_companion("Cargo.lock", {"src/main.rs"})


@pytest.mark.regression("B6")
def test_prasyarat_tech_lead_remediasi_satu_perintah_cargo_lock(crepo):
    repo, _ = crepo
    write_files(repo, {"Cargo.lock": LOCK + "# x\n"})
    proc = be_run(repo, "tech-lead/scripts/check_preconditions.py", "--json", "--root", str(repo), "--re-entry")
    c3 = next(c for c in json.loads(proc.stdout)["checks"] if c["id"] == 3)
    assert c3["status"] == "FAIL" and "git commit" in c3["action"] and "-- Cargo.lock" in c3["action"], c3
    write_files(repo, {"src/liar.go": "package x\n"})
    proc = be_run(repo, "tech-lead/scripts/check_preconditions.py", "--json", "--root", str(repo), "--re-entry")
    c3 = next(c for c in json.loads(proc.stdout)["checks"] if c["id"] == 3)
    assert "Cargo.lock" not in c3["action"]


@pytest.mark.regression("B6")
def test_prosa_rust_dan_implementor_selaras():
    rust = (BE_SKILLS / "profile/stacks/rust.md").read_text(encoding="utf-8")
    assert "tidak boleh dimutasi" not in rust and "close_brief.py" in rust
    impl = (PLUGINS / "backend/agents/code-implementor.md").read_text(encoding="utf-8")
    assert "`BLOCKED` bila brief menuntut dependensi baru pada manifest." not in impl
    assert "git rm -- <path>" in impl
    readme = (PLUGINS / "backend/README.md").read_text(encoding="utf-8")
    assert "git rm [-q] [--] <path>" in readme


# -- B11: bukti path:baris basename ---------------------------------------------------------------

TASK_DOC_FILES = {"src/main/java/x/order/RecallOrderService.java": "class R {}\n" * 20,
                  "src/main/java/x/order/Dockerfile": "FROM x\n"}


def task_doc(description):
    return ("---\nstatus: ACTIVE\nlane: DIRECT_BRIEF\nchain: BRIEF\nrisk: MINOR\n---\n# X\n## Description\n"
            f"{description}\n")


def t5(repo, description):
    write_files(repo, {f"{TD}/TASK.md": task_doc(description)})
    proc = run_script(VD, "--kind", "task", "--taskdir", TD, "--root", str(repo), "--json")
    return next(c for c in json.loads(proc.stdout)["checks"] if c["id"] == "T5")


@pytest.fixture
def trepo(make_repo):
    root = make_repo(TASK_DOC_FILES)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    return root


@pytest.mark.regression("B11")
def test_t5_basename_unik_diresolve(trepo):
    c = t5(trepo, "Recall di `RecallOrderService.java:7` dan `order/RecallOrderService.java:9`.")
    assert c["status"] == "PASS", c
    assert "src/main/java/x/order/RecallOrderService.java" in c["summary"]


@pytest.mark.regression("B11")
def test_t5_basename_ambigu_dan_hilang(trepo):
    write_files(trepo, {"src/main/java/y/RecallOrderService.java": "class R {}\n"})
    git(trepo, "add", "-A")
    git(trepo, "commit", "-qm", "dua")
    c = t5(trepo, "Recall di `RecallOrderService.java:1`.")
    assert c["status"] == "FAIL" and "ambigu" in c["summary"], c
    c = t5(trepo, "Recall di `Hilang.java:1`.")
    assert c["status"] == "FAIL" and "berkas tidak ada" in c["summary"], c
    c = t5(trepo, "Recall di `RecallOrderService.java:1`.".replace("RecallOrderService", "src/main/java/y/RecallOrderService"))
    assert c["status"] == "PASS", c


@pytest.mark.regression("B11")
def test_t5_host_port_bukan_bukti(trepo):
    c = t5(trepo, "Server di `0.0.0.0:4729`, kode di `RecallOrderService.java:2`.")
    assert c["status"] == "PASS", c
    c = t5(trepo, "Server di `0.0.0.0:4729` saja.")
    assert c["status"] == "FAIL" and "tanpa rujukan" in c["summary"], c


@pytest.mark.regression("B11")
def test_resolve_evidence_path_unit(trepo):
    pl = load_module(BE_SKILLS / "_common/precondition_lib.py", "be_pl_b11")
    assert pl.resolve_evidence_path(trepo, "amazoncorretto") == ("bukan", "")
    assert pl.resolve_evidence_path(trepo, "Dockerfile") == ("suffix", "src/main/java/x/order/Dockerfile")
    assert pl.resolve_evidence_path(trepo, "./src/main/java/x/order/Dockerfile")[0] == "ok"
    assert pl.resolve_evidence_path(trepo, "src/gone.go") == ("hilang", "")


TICKET_PY = BE_SKILLS / "ticket" / "scripts" / "ticket.py"


@pytest.mark.regression("B11")
def test_ticket_basename_dan_tag_image(chain_repo):
    proc = run_script(TICKET_PY, "new", "--slug", "base-image", "--title", "Ganti base image",
                      "--request", "ganti base image", "--json", cwd=chain_repo)
    td = json.loads(proc.stdout)["ticketdir"]
    path = chain_repo / td / "TICKET.md"
    text = path.read_text(encoding="utf-8")
    fills = {
        "- <isi: satu fakta kode sekarang per butir, berbukti `path:baris` relatif root repo>":
            "- Paket order di `order.go:1`; base image `amazoncorretto:21`",
        "- <isi: perubahan yang diminta, menyebut simbol dan berkas sasaran; bukan langkah implementasi>":
            "- Ganti base image",
        "- **AC-1**: <isi: hasil yang bisa diverifikasi dari luar, mis. response, status, data tersimpan>":
            "- **AC-1**: image terbangun",
        "<isi: aditif | mengubah | menghapus | tidak ada> — <isi: siapa terdampak; catatan lintas repo bila ada>":
            "tidak ada — internal",
    }
    for old, new in fills.items():
        assert old in text
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    proc = run_script(TICKET_PY, "check", "--ticketdir", td, "--json", cwd=chain_repo)
    assert proc.returncode == 0, proc.stdout
    path.write_text(text.replace("`order.go:1`", "`order.go:9`"), encoding="utf-8")
    proc = run_script(TICKET_PY, "check", "--ticketdir", td, "--json", cwd=chain_repo)
    out = json.loads(proc.stdout)
    assert proc.returncode == 1 and any("melewati panjang berkas" in p for p in out["problems"]), out
    assert not any("amazoncorretto" in p for p in out["problems"])
