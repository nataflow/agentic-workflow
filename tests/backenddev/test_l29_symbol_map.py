"""L2.9 — `symbol_map.py` memetakan baris diff ke method yang benar, bukan ke hunk header."""
import json

from conftest import BE_SKILLS, commit, run_script, write_files

SCRIPT = BE_SKILLS / "architect/scripts/symbol_map.py"
JAVA = """package com.acme.order;

public class OrderService {
    private final Repo repo;

    public OrderService(Repo repo) {
        this.repo = repo;
    }

    public void submit(Order o) {
        validate(o);
        repo.save(o);
    }

    public void cancel(Order o) {
        o.setStatus("CANCELLED");
        repo.save(o);
    }
}
"""
PHP = """<?php
namespace App\\Order;

class OrderService
{
    public function submit(Order $o): void
    {
        $this->validate($o);
        $this->repo->save($o);
    }

    public function cancel(Order $o): void
    {
        $o->status = 'CANCELLED';
        $this->repo->save($o);
    }
}
"""


def _map(repo, path, anchor=None):
    sha = commit(repo, "edit")
    args = ["--root", str(repo), "--sha", sha, "--path", path] + (["--anchor", anchor] if anchor is not None else [])
    proc = run_script(SCRIPT, *args)
    return proc.returncode, json.loads(proc.stdout)


def _fn_symbols(out):
    return {s["symbol"] for s in out["symbols"] if s["kind"] == "fn"}


def _base(make_repo, files):
    repo = make_repo(files)
    commit(repo, "base")
    return repo


def test_java_two_methods_distinct(make_repo):
    repo = _base(make_repo, {"src/OrderService.java": JAVA})
    write_files(repo, {"src/OrderService.java": JAVA.replace("validate(o);", "validate(o);\n        audit(o);")
                       .replace('o.setStatus("CANCELLED");', 'o.setStatus("CANCELLED");\n        audit(o);')})
    code, out = _map(repo, "src/OrderService.java", anchor="`submit`")
    assert _fn_symbols(out) == {"submit", "cancel"}
    assert code == 1 and [o["symbol"] for o in out["outside_anchor"]] == ["cancel"]
    assert out["outside_anchor"][0]["lines"] == [18]


def test_php_psr12_brace_next_line(make_repo):
    repo = _base(make_repo, {"src/OrderService.php": PHP})
    write_files(repo, {"src/OrderService.php": PHP.replace("$this->validate($o);", "$this->validate($o);\n        $this->audit($o);")
                       .replace("$o->status = 'CANCELLED';", "$o->status = 'CANCELLED';\n        $this->audit($o);")})
    _, out = _map(repo, "src/OrderService.php")
    assert _fn_symbols(out) == {"submit", "cancel"}


def test_signature_change_maps_to_own_method(make_repo):
    repo = _base(make_repo, {"src/OrderService.java": JAVA})
    write_files(repo, {"src/OrderService.java": JAVA.replace("public void cancel(Order o) {",
                                                             "public void cancel(Order o, String reason) {")})
    code, out = _map(repo, "src/OrderService.java", anchor="cancel")
    assert [(l["line"], l["symbol"]) for l in out["lines"]] == [(15, "cancel")]
    assert code == 0


def test_new_method_maps_to_new_symbol(make_repo):
    repo = _base(make_repo, {"src/OrderService.java": JAVA})
    write_files(repo, {"src/OrderService.java": JAVA[:-2] + "\n    public void refund(Order o) {\n        repo.refund(o);\n    }\n}\n"})
    _, out = _map(repo, "src/OrderService.java")
    assert "refund" in _fn_symbols(out) and "cancel" not in _fn_symbols(out)


def test_pure_deletion_maps_old_side(make_repo):
    repo = _base(make_repo, {"src/OrderService.java": JAVA})
    write_files(repo, {"src/OrderService.java": JAVA.replace("        validate(o);\n", "")})
    _, out = _map(repo, "src/OrderService.java")
    assert out["lines"] == [{"side": "old", "line": 11, "symbol": "submit", "kind": "fn", "decl_line": 10}]


def test_go_rust_kotlin_ts(make_repo):
    files = {
        "src/o.go": "package order\n\ntype S struct{}\n\nfunc (s *S) Submit() {\n\tx := 1\n\t_ = x\n}\n",
        "src/o.rs": "pub struct S;\n\nimpl S {\n    pub fn submit(&self) {\n        let x = 1;\n    }\n}\n",
        "src/o.kt": "class S {\n    fun submit() {\n        val x = 1\n    }\n}\n",
        "src/o.ts": "export class S {\n  submit(o: Order): void {\n    const x = 1;\n  }\n}\n",
    }
    repo = _base(make_repo, files)
    write_files(repo, {k: v.replace("1", "2") for k, v in files.items()})
    sha = commit(repo, "edit")
    for path, name in (("src/o.go", "Submit"), ("src/o.rs", "submit"), ("src/o.kt", "submit"), ("src/o.ts", "submit")):
        out = json.loads(run_script(SCRIPT, "--root", str(repo), "--sha", sha, "--path", path).stdout)
        assert _fn_symbols(out) == {name}, (path, out)


def test_string_with_brace_ignored(make_repo):
    src = JAVA.replace('o.setStatus("CANCELLED");', 'o.setStatus("CANCELLED {");')
    repo = _base(make_repo, {"src/OrderService.java": src})
    write_files(repo, {"src/OrderService.java": src.replace("        repo.save(o);\n    }\n}", "        repo.save(o);\n        audit(o);\n    }\n}")})
    _, out = _map(repo, "src/OrderService.java")
    assert _fn_symbols(out) == {"cancel"}


def test_unknown_extension_degrades(make_repo):
    repo = _base(make_repo, {"src/a.py": "def a():\n    return 1\n"})
    write_files(repo, {"src/a.py": "def a():\n    return 2\n"})
    code, out = _map(repo, "src/a.py")
    assert code == 2 and out["status"] == "DEGRADED"
