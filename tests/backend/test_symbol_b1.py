"""B1 — `HALT SYMBOL` alarm palsu: simbol di luar anchor jadi peringatan, nama berkualifikasi tipe induk,
blok impl/tipe yang lahir di commit sama, dan fn pendukung (lifecycle test, `main`, `default`) diabaikan."""
import json

import pytest

from conftest import BE_SKILLS, TD, brief, commit, run_script, write_files

SYMBOL_MAP = BE_SKILLS / "architect/scripts/symbol_map.py"
CLOSE = BE_SKILLS / "architect/scripts/close_brief.py"

RS = """pub struct Bar;
pub struct Foo;

impl Default for Bar {
    fn default() -> Self {
        Bar
    }
}

impl Foo {
    pub fn new() -> Self {
        Foo
    }
}
"""
JAVA_TEST = """package com.acme;

class OrderServiceTest {
    private Repo repo;

    @BeforeEach
    void init() {
        repo = new Repo();
    }

    @Test
    void submit() {
        assertTrue(true);
    }
}
"""
GO_MAIN = "package main\n\nfunc main() {\n\tx := 1\n\t_ = x\n}\n\nfunc Submit() {\n\ty := 1\n\t_ = y\n}\n"


def _brief_file(repo, path, anchor, steps="1. Ubah sesuai kontrak."):
    b = repo / "brief-01-x.md"
    b.write_text("---\nstatus: READY\n---\n\n## File scope\n\n"
                 "| Aksi | Path | Anchor | Apa yang berubah |\n|---|---|---|---|\n"
                 f"| modify | `{path}` | {anchor} | ubah |\n\n## Steps\n\n{steps}\n", encoding="utf-8")
    return b


def _map(repo, path, anchor, new_text, steps="1. Ubah sesuai kontrak."):
    b = _brief_file(repo, path, anchor, steps)
    write_files(repo, {path: new_text})
    sha = commit(repo, "edit", path)
    proc = run_script(SYMBOL_MAP, "--root", str(repo), "--sha", sha, "--path", path, "--brief", str(b))
    return proc.returncode, json.loads(proc.stdout)


def _base(make_repo, files):
    repo = make_repo(files)
    commit(repo, "base")
    return repo


@pytest.mark.regression("B1")
def test_impl_trait_baru_untuk_tipe_lain_bukan_deklarasi_lama(make_repo):
    repo = _base(make_repo, {"src/lib.rs": RS})
    new = RS + "\nimpl Default for Foo {\n    fn default() -> Self {\n        Foo::new()\n    }\n}\n"
    code, out = _map(repo, "src/lib.rs", "`Foo`", new, steps="1. Tambah impl trait untuk Foo.")
    assert code == 0, out
    assert out["outside_anchor"] == [] and "default" in out["new_declared"]


@pytest.mark.regression("B1")
def test_fn_di_impl_generik_yang_lahir_di_commit_sama(make_repo):
    repo = _base(make_repo, {"src/lib.rs": RS})
    new = RS + "\nimpl<T> From<T> for Bar {\n    fn from(_v: T) -> Self {\n        Bar\n    }\n}\n"
    code, out = _map(repo, "src/lib.rs", "`Bar`", new, steps="1. Tambah konversi.")
    assert code == 0, out
    assert "from" in out["new_declared"] and out["outside_anchor"] == []


@pytest.mark.regression("B1")
def test_suntingan_fn_lama_di_impl_tetap_di_luar_anchor(make_repo):
    repo = _base(make_repo, {"src/lib.rs": RS})
    code, out = _map(repo, "src/lib.rs", "`Bar`", RS.replace("        Foo\n", "        Foo {}\n"))
    assert code == 1 and [o["symbol"] for o in out["outside_anchor"]] == ["new"]


@pytest.mark.regression("B1")
def test_lifecycle_test_ber_annotation_diabaikan(make_repo):
    path = "src/test/java/com/acme/OrderServiceTest.java"
    repo = _base(make_repo, {path: JAVA_TEST})
    new = JAVA_TEST.replace("repo = new Repo();", "repo = new Repo();\n        repo.clear();")
    code, out = _map(repo, path, "`submit`", new)
    assert code == 0 and out["outside_anchor"] == [] and out["diabaikan"] == ["init"]


@pytest.mark.regression("B1")
def test_nama_lifecycle_di_luar_berkas_test_tetap_dinilai(make_repo):
    src = "package app\n\nfunc setUp() {\n\tx := 1\n\t_ = x\n}\n"
    repo = _base(make_repo, {"src/app.go": src})
    code, out = _map(repo, "src/app.go", "`Run`", src.replace("x := 1", "x := 2"))
    assert code == 1 and [o["symbol"] for o in out["outside_anchor"]] == ["setUp"]


@pytest.mark.regression("B1")
def test_main_diabaikan(make_repo):
    repo = _base(make_repo, {"cmd/app/main.go": GO_MAIN})
    code, out = _map(repo, "cmd/app/main.go", "`Submit`", GO_MAIN.replace("x := 1", "x := 2"))
    assert code == 0 and out["diabaikan"] == ["main"] and out["outside_anchor"] == []


# ------------------------------------------------------------------ close_brief: WARN, bukan HALT

GO = "package order\n\nfunc Submit() {\n\tx := 1\n\t_ = x\n}\n\nfunc Cancel() {\n\ty := 1\n\t_ = y\n}\n"
BODY = """# Brief
## File scope
**File**

| Aksi | Path | Anchor | Apa yang berubah |
|---|---|---|---|
| modify | `src/order.go` | `Submit` | validasi |

## Steps
1. Ubah `Submit` di `src/order.go`.
"""


@pytest.fixture
def repo(chain_repo):
    write_files(chain_repo, {"src/order.go": GO})
    commit(chain_repo, "base order", "src/order.go")
    return chain_repo


def _close(repo, code_text, *extra):
    path = brief(repo, "01", "submit", "DONE", body=BODY)
    write_files(repo, {"src/order.go": code_text})
    sha = commit(repo, f"fix(order): submit {len(code_text)}", "src/order.go")
    proc = run_script(CLOSE, "--brief", str(path), "--sha", sha, *extra, cwd=repo)
    return proc, path


@pytest.mark.regression("B1")
def test_warn_menulis_peringatan_di_laci_dan_tidak_menahan(repo):
    lease = repo / ".git" / "nataflow" / "lease-backend.json"
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text("{}", encoding="utf-8")
    proc, path = _close(repo, GO.replace("y := 1", "y := 2"), "--json")
    out = json.loads(proc.stdout)
    assert proc.returncode == 0 and out["verdict"] == "WARN"
    note = repo / TD / ".explore" / "simbol-01.md"
    assert out["peringatan"] == f"{TD}/.explore/simbol-01.md" and note.is_file()
    text = note.read_text(encoding="utf-8")
    assert "`src/order.go` | `Cancel` | 9" in text and "code-reviewer" in text
    assert out["lease"] == "dicabut" and not lease.exists()


@pytest.mark.regression("B1")
def test_pass_ulang_menghapus_peringatan_basi_dan_teks_satu_baris(repo):
    note = repo / TD / ".explore" / "simbol-01.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("basi\n", encoding="utf-8")
    proc, _ = _close(repo, GO.replace("x := 1", "x := 2"))
    assert proc.returncode == 0 and proc.stdout.startswith("PASS ") and not note.exists()
    assert len(proc.stdout.strip().splitlines()) == 1


@pytest.mark.regression("B1")
def test_teks_warn_menyebut_simbol_dan_berkas_peringatan(repo):
    proc, _ = _close(repo, GO.replace("y := 1", "y := 2"))
    assert proc.returncode == 0 and proc.stdout.startswith("WARN brief-01-submit.md @ ")
    assert "Cancel" in proc.stdout and ".explore/simbol-01.md" in proc.stdout
