"""Gerbang artifact nataflow: `artifact.py config` dan `check`, plus teks SKILL create-artifact."""
import hashlib
import json

import pytest

from conftest import PLUGINS, run_script

SKILL_DIR = PLUGINS / "nataflow" / "skills" / "create-artifact"
SCRIPT = SKILL_DIR / "scripts" / "artifact.py"

GOOD = """<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ringkasan Sprint 12</title>
<link rel="preconnect" href="https://fonts.gstatic.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root { --bg: #fff; --fg: #111; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #111; --fg: #eee; } }
body { background: var(--bg); color: var(--fg); }
</style>
</head>
<body><main><h1>Ringkasan</h1><a href="detail">detail</a><img src="data:image/png;base64,AAAA"></main></body>
</html>
"""


def _check(tmp_path, html, *extra, raw=None):
    draft = tmp_path / "draft.html"
    if raw is not None:
        draft.write_bytes(raw)
    else:
        draft.write_text(html, encoding="utf-8")
    proc = run_script(SCRIPT, "check", "--file", str(draft), *extra, "--json", cwd=tmp_path)
    return proc, json.loads(proc.stdout)


def test_check_pass_builds_upsert_args(tmp_path):
    proc, out = _check(tmp_path, GOOD)
    assert proc.returncode == 0, out
    assert out["status"] == "PASS" and out["problems"] == [] and out["warnings"] == []
    assert out["key"] == "ringkasan-sprint-12"
    assert out["title"] == "Ringkasan Sprint 12"
    assert out["content_sha256"] == hashlib.sha256(GOOD.encode("utf-8")).hexdigest()
    assert out["bytes"] == len(GOOD.encode("utf-8"))
    assert json.loads(out["metadata"]) == {"title": "Ringkasan Sprint 12", "source": "nataflow:create-artifact"}
    assert out["metadata"] == '{"title":"Ringkasan Sprint 12","source":"nataflow:create-artifact"}'


def test_check_explicit_key(tmp_path):
    proc, out = _check(tmp_path, GOOD, "--key", "laporan-q3-v2")
    assert proc.returncode == 0 and out["key"] == "laporan-q3-v2"


@pytest.mark.parametrize("key", ["Laporan", "a_b", "-a", "a--b", "a" * 81])
def test_check_rejects_bad_key(tmp_path, key):
    proc, out = _check(tmp_path, GOOD, f"--key={key}")
    assert proc.returncode == 1 and any("--key" in p for p in out["problems"])


def test_slug_folds_accents(tmp_path):
    html = GOOD.replace("Ringkasan Sprint 12", "Évaluasi Café Q3")
    _, out = _check(tmp_path, html)
    assert out["key"] == "evaluasi-cafe-q3"


def test_non_latin_title_requires_key(tmp_path):
    html = GOOD.replace("Ringkasan Sprint 12", "報告書")
    proc, out = _check(tmp_path, html)
    assert proc.returncode == 1 and any("--key" in p for p in out["problems"])
    proc, out = _check(tmp_path, html, "--key", "laporan")
    assert proc.returncode == 0, out


@pytest.mark.parametrize("old,new,needle", [
    ("<!doctype html>\n", "", "doctype"),
    ('<meta charset="utf-8">', "", "charset"),
    ('<meta name="viewport" content="width=device-width, initial-scale=1">', "", "viewport"),
    ("<title>Ringkasan Sprint 12</title>", "<title>  </title>", "<title>"),
    ("<title>Ringkasan Sprint 12</title>", "<title>" + "x" * 121 + "</title>", "120"),
    ("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js", "https://evil.example/x.js",
     "evil.example"),
    ("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js", "app.js", "rujukan relatif"),
    ("https://fonts.googleapis.com/css2?family=Inter", "https://cdn.example/site.css", "Google Fonts"),
    ("data:image/png;base64,AAAA", "logo.png", "rujukan relatif"),
    ("<h1>Ringkasan</h1>", '<h1>Ringkasan</h1><input type="password">', "kredensial"),
], ids=["doctype", "charset", "viewport", "title-kosong", "title-panjang", "cdn-asing", "script-relatif",
        "css-asing", "img-relatif", "password"])
def test_check_fail(tmp_path, old, new, needle):
    assert old in GOOD
    proc, out = _check(tmp_path, GOOD.replace(old, new, 1))
    assert proc.returncode == 1 and out["status"] == "FAIL"
    assert any(needle in p for p in out["problems"]), out["problems"]


def test_non_loading_links_are_not_relative_refs(tmp_path):
    html = GOOD.replace("<title>", '<link rel="canonical" href="/a"><title>')
    proc, out = _check(tmp_path, html)
    assert proc.returncode == 0, out


def test_warnings_do_not_fail(tmp_path):
    html = GOOD.replace("@media (prefers-color-scheme: dark)", "@media print")
    html = html.replace(":root { --bg: #fff; --fg: #111; }", "body { margin: 0 }")
    html = html.replace("</main>", "<script>localStorage.setItem('a', 1)</script></main>")
    proc, out = _check(tmp_path, html)
    assert proc.returncode == 0 and out["status"] == "PASS"
    text = " ".join(out["warnings"])
    assert "prefers-color-scheme" in text and ":root" in text and "try/catch" in text


@pytest.mark.parametrize("raw,needle", [
    (b"", "kosong"),
    (b"\xff\xfe<html>", "UTF-8"),
    (b"\xef\xbb\xbf" + GOOD.encode("utf-8"), "BOM"),
], ids=["kosong", "bukan-utf8", "bom"])
def test_check_bytes(tmp_path, raw, needle):
    proc, out = _check(tmp_path, "", raw=raw)
    assert proc.returncode == 1 and any(needle in p for p in out["problems"]), out


def test_check_size_cap(tmp_path):
    html = GOOD.replace("</main>", "<p>" + "a" * (1024 * 1024) + "</p></main>")
    proc, out = _check(tmp_path, html)
    assert proc.returncode == 1 and any("byte" in p for p in out["problems"])


def test_check_missing_file(tmp_path):
    proc = run_script(SCRIPT, "check", "--file", str(tmp_path / "tidak-ada.html"), "--json", cwd=tmp_path)
    out = json.loads(proc.stdout)
    assert proc.returncode == 1 and "tidak bisa dibaca" in out["problems"][0]


def test_config_default(make_repo):
    root = make_repo()
    proc = run_script(SCRIPT, "config", "--json", cwd=root)
    out = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert out["mcp_server"] == "nataflow-api" and out["config_source"] == "default"
    assert out["draft_dir"].endswith("nataflow-artifacts")


def test_config_reads_repo_root_from_subdir(make_repo):
    root = make_repo({".claude/nataflow.json": json.dumps({"mcp_server": "nataflow-staging",
                                                           "workspaces": {}}),
                      "pkg/a.txt": "x"})
    proc = run_script(SCRIPT, "config", "--json", cwd=root / "pkg")
    out = json.loads(proc.stdout)
    assert proc.returncode == 0 and out["mcp_server"] == "nataflow-staging"


@pytest.mark.parametrize("content", ["{rusak", "[]", json.dumps({"mcp_server": "ada spasi"}),
                                     json.dumps({"mcp_server": 3})], ids=["json", "array", "spasi", "angka"])
def test_config_broken_fails(make_repo, content):
    root = make_repo({".claude/nataflow.json": content})
    proc = run_script(SCRIPT, "config", "--json", cwd=root)
    out = json.loads(proc.stdout)
    assert proc.returncode == 1 and out["status"] == "FAIL" and out["problems"]


def test_config_outside_git(make_repo):
    root = make_repo(git_init=False)
    proc = run_script(SCRIPT, "config", "--json", cwd=root)
    assert proc.returncode == 0 and json.loads(proc.stdout)["mcp_server"] == "nataflow-api"


# ── teks SKILL ────────────────────────────────────────────────────────────────

def _skill():
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def test_skill_model_invocable():
    front = _skill().split("---\n", 2)[1]
    assert "disable-model-invocation" not in front and "user-invocable" not in front
    assert not front.split("description:", 1)[1].lstrip().startswith("Dipanggil")


def test_skill_names_all_tools_and_project_parent():
    text = _skill()
    for tool in ("get_project_info", "list_artifacts", "get_artifact", "upsert_artifact"):
        assert tool in text, tool
    assert "`reference_table` = `project`" in text
    assert "content_sha256" in text


def test_page_contract_hosts_match_script():
    """Daftar CDN di kontrak halaman dan di skrip harus sama."""
    contract = (SKILL_DIR / "references" / "page-contract.md").read_text(encoding="utf-8")
    source = SCRIPT.read_text(encoding="utf-8")
    for host in ("https://cdnjs.cloudflare.com/", "https://cdn.jsdelivr.net/npm/", "https://unpkg.com/",
                 "https://cdn.tailwindcss.com", "https://code.jquery.com/", "https://fonts.googleapis.com/"):
        assert host in contract and f'"{host}"' in source, host
