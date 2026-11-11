"""32 C1 — `close_brief.py`: satu vonis penutup per brief (sisa berkas, scope, simbol, lease)."""
import json

import pytest

from conftest import BE_SKILLS, TD, brief, commit, git, run_script, write_files

SCRIPT = BE_SKILLS / "architect/scripts/close_brief.py"
GO = "package order\n\nfunc Submit() {\n\tx := 1\n\t_ = x\n}\n\nfunc Cancel() {\n\ty := 1\n\t_ = y\n}\n"
BODY = """# Brief
## File scope
**File**

| Aksi | Path | Anchor | Apa yang berubah |
|---|---|---|---|
| modify | `src/order.go` | `Submit` | validasi dan helper `Refund` |

## Steps
1. Ubah `Submit` di `src/order.go`, lalu tambah `func Refund()` sesudahnya.
"""


@pytest.fixture
def repo(chain_repo):
    write_files(chain_repo, {"src/order.go": GO})
    commit(chain_repo, "base order", "src/order.go")
    return chain_repo


def _land(repo, code):
    path = brief(repo, "01", "refund", "DONE", body=BODY)
    write_files(repo, code)
    sha = commit(repo, "fix(order): implement refund", *code.keys())
    return path, sha


def _close(repo, path, sha):
    proc = run_script(SCRIPT, "--brief", str(path), "--sha", sha, "--json", cwd=repo)
    return proc.returncode, json.loads(proc.stdout)


@pytest.mark.regression("32 C1")
def test_pass_dengan_deklarasi_baru_dan_lease_dicabut(repo):
    lease = repo / ".git" / "nataflow" / "lease-backend.json"
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text("{}", encoding="utf-8")
    path, sha = _land(repo, {"src/order.go": GO.replace("x := 1", "x := 2") + "\nfunc Refund() {\n\tz := 1\n\t_ = z\n}\n"})
    code, out = _close(repo, path, sha)
    assert code == 0 and out["verdict"] == "PASS", out
    assert out["new_declared"] == ["src/order.go#Refund"] and out["status_brief"] == "DONE"
    assert out["lease"] == "dicabut" and not lease.exists()


@pytest.mark.regression("32 C1")
def test_symbol_di_luar_anchor(repo):
    path, sha = _land(repo, {"src/order.go": GO.replace("y := 1", "y := 2")})
    code, out = _close(repo, path, sha)
    assert code == 1 and out["verdict"] == "SYMBOL"
    assert [s["symbol"] for s in out["simbol"]] == ["Cancel"]


@pytest.mark.regression("32 C1")
def test_scope_berkas_di_luar_file_scope(repo):
    path, sha = _land(repo, {"src/order.go": GO.replace("x := 1", "x := 2"), "src/other.go": "package order\n"})
    code, out = _close(repo, path, sha)
    assert code == 1 and out["verdict"] == "SCOPE" and "src/other.go" in out["scope"]


@pytest.mark.regression("32 C1")
def test_stray_mendahului_vonis_lain(repo):
    path, sha = _land(repo, {"src/order.go": GO.replace("y := 1", "y := 2")})
    write_files(repo, {"src/tmp.go": "package order\n", f"{TD}/.explore/catatan.md": "x\n"})
    code, out = _close(repo, path, sha)
    assert code == 1 and out["verdict"] == "STRAY" and out["stray"] == ["src/tmp.go"]


@pytest.mark.regression("32 C1")
def test_sha_salah_exit_2_json_sah(repo):
    path = brief(repo, "01", "refund", "DONE", body=BODY)
    code, out = _close(repo, path, "deadbeef")
    assert code == 2 and out["verdict"] == "ERROR"


@pytest.mark.regression("32 C1")
def test_teks_satu_baris(repo):
    path, sha = _land(repo, {"src/order.go": GO.replace("x := 1", "x := 2")})
    proc = run_script(SCRIPT, "--brief", str(path), "--sha", sha, cwd=repo)
    assert proc.returncode == 0 and len(proc.stdout.strip().splitlines()) == 1
    assert proc.stdout.startswith("PASS brief-01-refund.md @ ")
