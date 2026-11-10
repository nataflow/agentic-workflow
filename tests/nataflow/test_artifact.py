"""Gerbang artifact nataflow: `artifact.py` config/check/list/pull/publish, plus teks SKILL create-artifact."""
import hashlib
import json

import pytest

from conftest import PLUGINS, run_script
from nataflow_fake import KEY, FakeMCP, Nataflow, enable_sync

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
    html = html.replace("</main>", '<a href="https://x.example" target="_blank">x</a>'
                                   '<form action="/kirim"></form>'
                                   "<script>if (window.confirm('ok?')) {}</script></main>")
    proc, out = _check(tmp_path, html)
    assert proc.returncode == 0 and out["status"] == "PASS"
    text = " ".join(out["warnings"])
    for needle in ("prefers-color-scheme", ":root", "confirm", "_blank", "<form action>"):
        assert needle in text, (needle, out["warnings"])


@pytest.mark.parametrize("snippet,needle", [
    ("<script>try { localStorage.setItem('a', 1) } catch (e) {}</script>", "localStorage"),
    ("<script>sessionStorage.clear()</script>", "sessionStorage"),
    ("<script>indexedDB.open('x')</script>", "indexedDB"),
    ("<script>document . cookie = 'a=1'</script>", "document . cookie"),
    ('<button onclick="localStorage.clear()">x</button>', "localStorage"),
], ids=["local-walau-try", "session", "indexeddb", "cookie", "atribut-on"])
def test_storage_fails_in_sandbox(tmp_path, snippet, needle):
    proc, out = _check(tmp_path, GOOD.replace("</main>", snippet + "</main>"))
    assert proc.returncode == 1
    assert any(needle in p and "SecurityError" in p for p in out["problems"]), out["problems"]


def test_storage_words_in_prose_pass(tmp_path):
    html = GOOD.replace("<h1>Ringkasan</h1>", "<h1>Ringkasan</h1><p>localStorage dan alert() dibahas di sini.</p>")
    proc, out = _check(tmp_path, html)
    assert proc.returncode == 0 and out["warnings"] == [], out


def test_dialog_regex_ignores_methods(tmp_path):
    html = GOOD.replace("</main>", "<script>toast.alert('x'); customConfirm(1)</script></main>")
    _, out = _check(tmp_path, html)
    assert not any("confirm" in w for w in out["warnings"]), out["warnings"]


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


@pytest.fixture
def fake():
    with FakeMCP() as f:
        yield f, Nataflow(f)


def art(root, *args):
    proc = run_script(SCRIPT, *args, "--json", cwd=root)
    assert "Traceback" not in proc.stderr, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


@pytest.mark.regression("29 S6")
def test_config_url_key_dan_project(make_repo, fake):
    f, nf = fake
    root = make_repo({"pkg/a.txt": "x"})
    enable_sync(root, f.url)
    code, out = art(root / "pkg", "config")
    assert code == 0 and out["status"] == "PASS" and out["url"] == f.url
    assert out["project_id"] == nf.project["id"] and out["draft_dir"].endswith("nataflow-artifacts")
    assert KEY not in json.dumps(out)


def test_config_absen_wajib_setup(make_repo):
    code, out = art(make_repo(), "config")
    assert code == 1 and "nataflow.json tidak ada" in out["problems"][0] and "nataflow.local.json" in out["problems"][0]


@pytest.mark.parametrize("content,needle", [
    ("{rusak", "bukan JSON sah"), ("[]", "harus objek JSON"),
    (json.dumps({"mcp_server": "nataflow-api"}), "`mcp_server` sudah diganti `url`"),
    (json.dumps({"url": 3}), "harus string")], ids=["json", "array", "mcp_server", "angka"])
def test_config_rusak_gagal(make_repo, content, needle):
    root = make_repo({".claude/nataflow.json": content})
    code, out = art(root, "config")
    assert code == 1 and out["status"] == "FAIL" and needle in out["problems"][0]


def test_config_luar_git_tanpa_cek_ignore(make_repo, fake):
    f, _ = fake
    root = make_repo(git_init=False)
    enable_sync(root, f.url, ignore=False)
    assert art(root, "config")[0] == 0


def test_config_key_tidak_diabaikan_gagal_tanpa_panggilan(make_repo, fake):
    f, _ = fake
    root = make_repo()
    enable_sync(root, f.url, ignore=False)
    code, out = art(root, "config")
    assert code == 1 and "tidak diabaikan git" in out["problems"][0] and f.requests == []


def test_publish_baru_lalu_tabrakan_lalu_timpa(tmp_path, make_repo, fake):
    f, nf = fake
    root = make_repo()
    enable_sync(root, f.url)
    draft = tmp_path / "d.html"
    draft.write_text(GOOD, encoding="utf-8")
    code, out = art(root, "publish", "--file", str(draft))
    assert code == 0 and out["status"] == "CREATED" and out["key"] == "ringkasan-sprint-12", out
    doc = nf.docs[0]
    assert (doc["type"], doc["mimetype"], doc["content"]) == ("artifact", "text/html", GOOD)
    assert "<main>" not in json.dumps(out), "isi HTML tidak dicetak"
    code, out = art(root, "publish", "--file", str(draft))
    assert out["status"] == "TABRAKAN" and out["existing_title"] == "Ringkasan Sprint 12"
    assert f.writes() == ["upsert_artifact"], "tabrakan tidak menulis"
    code, out = art(root, "publish", "--file", str(draft), "--overwrite")
    assert out["status"] == "UNCHANGED"
    draft.write_text(GOOD.replace("<h1>Ringkasan</h1>", "<h1>Ringkasan baru</h1>"), encoding="utf-8")
    assert art(root, "publish", "--file", str(draft), "--overwrite")[1]["status"] == "UPDATED"


def test_publish_tidak_menimpa_dokumen_non_artifact(tmp_path, make_repo, fake):
    f, nf = fake
    root = make_repo()
    enable_sync(root, f.url)
    nf.add_doc("project", nf.project["id"], "ringkasan-sprint-12", "notes.meeting", "x", {})
    draft = tmp_path / "d.html"
    draft.write_text(GOOD, encoding="utf-8")
    code, out = art(root, "publish", "--file", str(draft), "--overwrite")
    assert code == 0 and out["status"] == "TABRAKAN_DOKUMEN" and out["existing_type"] == "notes.meeting"
    assert f.writes() == []


def test_publish_draft_gagal_check_tanpa_jaringan(tmp_path, make_repo, fake):
    f, _ = fake
    root = make_repo()
    enable_sync(root, f.url)
    draft = tmp_path / "d.html"
    draft.write_text(GOOD.replace('<meta charset="utf-8">', ""), encoding="utf-8")
    code, out = art(root, "publish", "--file", str(draft))
    assert code == 1 and out["problems"] and f.requests == []


def test_list_dan_pull(tmp_path, make_repo, fake):
    f, nf = fake
    root = make_repo()
    enable_sync(root, f.url)
    nf.add_doc("project", nf.project["id"], "dash", "artifact", GOOD, {"title": "Dasbor"}, mimetype="text/html")
    code, out = art(root, "list")
    assert code == 0 and out["artifacts"] == [{"key": "dash", "title": "Dasbor"}]
    draft = tmp_path / "x" / "dash.html"
    code, out = art(root, "pull", "--key", "dash", "--file", str(draft))
    assert code == 0 and out["status"] == "PASS" and draft.read_text(encoding="utf-8") == GOOD
    assert out["content_sha256"] == hashlib.sha256(GOOD.encode()).hexdigest() and "<main>" not in json.dumps(out)
    code, out = art(root, "pull", "--key", "tidak-ada", "--file", str(draft))
    assert code == 0 and out["status"] == "NOT_FOUND"


def test_key_banyak_project_gagal(make_repo, fake):
    f, nf = fake
    root = make_repo()
    enable_sync(root, f.url)
    f.tools["get_project_info"] = lambda a: [nf.project, dict(nf.project, id="lain")]
    code, out = art(root, "config")
    assert code == 1 and "key menjangkau 2 project" in out["problems"][0]


# ── teks SKILL ────────────────────────────────────────────────────────────────

def _skill():
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def test_skill_model_invocable():
    front = _skill().split("---\n", 2)[1]
    assert "disable-model-invocation" not in front and "user-invocable" not in front
    assert not front.split("description:", 1)[1].lstrip().startswith("Dipanggil")


def test_skill_names_all_tools_and_project_parent():
    text = _skill()
    for tool in ("get_project_info", "list_artifacts", "get_artifact", "upsert_artifact", "get_document"):
        assert tool in text, tool
    assert "`reference_table` = `project`" in text
    assert "content_sha256" in text


def test_skill_collision_check_uses_get_document():
    """upsert_artifact menimpa dokumen non-artifact ber-key sama; get_artifact tidak melihatnya."""
    text = _skill()
    fase4 = text.split("### Fase 4", 1)[1].split("## Larangan", 1)[0]
    assert "`get_document` dengan `reference_table`, `reference_id`, dan `key`" in fase4
    assert "jangan tawarkan timpa" in fase4


def test_page_contract_hosts_match_script():
    """Daftar CDN di kontrak halaman dan di skrip harus sama."""
    contract = (SKILL_DIR / "references" / "page-contract.md").read_text(encoding="utf-8")
    source = SCRIPT.read_text(encoding="utf-8")
    for host in ("https://cdnjs.cloudflare.com/", "https://cdn.jsdelivr.net/npm/", "https://unpkg.com/",
                 "https://cdn.tailwindcss.com", "https://code.jquery.com/", "https://fonts.googleapis.com/"):
        assert host in contract and f'"{host}"' in source, host
