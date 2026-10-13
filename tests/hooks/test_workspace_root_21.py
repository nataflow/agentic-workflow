"""Hook SessionStart di root multi-repo (Langkah 21 F1).

Root multi-repo = folder non-git yang menampung >= 2 repo git (`wms/api`, `wms/frontend`). Gerbang
backend/frontend dulu menyala di sana dan mengklaim "jalan lebih dulu", padahal skrip prasyaratnya
butuh repo git. Kini keduanya hanya menunjuk repo miliknya.
"""
import json

import pytest

from conftest import be_profile, fe_profile, git, run_hook, write_files

GIN_GOMOD = "module x\n\ngo 1.22\n\nrequire github.com/gin-gonic/gin v1.10.0\n"
SVELTEKIT = json.dumps({"devDependencies": {"@sveltejs/kit": "^2", "svelte": "^5", "vite": "^6"}})
EXPRESS = json.dumps({"dependencies": {"express": "^4"}})


def _repo(path, files=None):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    write_files(path, files or {})
    return path


def _context(plugin, cwd):
    proc, payload = run_hook(plugin, cwd)
    assert proc.returncode == 0, proc.stderr
    return payload["hookSpecificOutput"]["additionalContext"] if payload else None


def _explain(plugin, cwd):
    proc, _ = run_hook(plugin, cwd, explain=True)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.fixture
def satu_proyek(tmp_path):
    root = tmp_path / "wms"
    _repo(root / "api", {"go.mod": GIN_GOMOD})
    _repo(root / "frontend", {"package.json": SVELTEKIT})
    return root


@pytest.mark.regression("21 F1")
@pytest.mark.parametrize("plugin, gate, repo, stack", [
    ("backenddev", "backend-tech-lead-gate", "api", "go"),
    ("frontenddev", "frontend-lead-gate", "frontend", "sveltekit"),
])
def test_root_satu_proyek_bukan_gerbang(satu_proyek, plugin, gate, repo, stack):
    text = _context(plugin, satu_proyek)
    assert text.startswith(f"<{gate}>") and text.endswith(f"</{gate}>")
    assert "root multi-repo" in text and "berisi 2 repo" in text
    assert f"`{repo}/` ({stack}," in text
    assert "/fullstack:explore" in text
    assert "jalan lebih dulu" not in text and "WAJIB lewat gerbang" not in text


@pytest.mark.regression("21 F1")
def test_root_profil_anak_terbaca(satu_proyek):
    be_profile(satu_proyek / "api", "go")
    fe_profile(satu_proyek / "frontend", "sveltekit")
    for plugin, repo, stack in (("backenddev", "api", "go"), ("frontenddev", "frontend", "sveltekit")):
        v = _explain(plugin, satu_proyek)
        assert v["emit"] is True and v["source"] == "workspace" and v["workspace_size"] == 2
        assert v["workspace"] == [{"dir": repo, "stack": stack, "source": "profile"}]
        assert "sumber: profil" in _context(plugin, satu_proyek)


@pytest.mark.regression("21 F1")
def test_root_tanpa_repo_milik_plugin_diam(tmp_path):
    root = tmp_path / "root"
    _repo(root / "web", {"package.json": SVELTEKIT})
    _repo(root / "admin", {"package.json": SVELTEKIT})
    assert _context("backenddev", root) is None
    assert "`admin/`" in _context("frontenddev", root) and "`web/`" in _context("frontenddev", root)


@pytest.mark.regression("21 F1")
def test_root_satu_anak_git_perilaku_lama(tmp_path):
    root = tmp_path / "root"
    _repo(root / "api", {"go.mod": GIN_GOMOD})
    v = _explain("backenddev", root)
    assert v["workspace_size"] == 0 and v["source"] == "api/go.mod"
    assert "jalan lebih dulu" in _context("backenddev", root)


@pytest.mark.regression("21 F1")
def test_root_multi_proyek_tetap_diam(tmp_path):
    root = tmp_path / "company"
    for proyek in ("wms", "erp"):
        _repo(root / proyek / "api", {"go.mod": GIN_GOMOD})
        _repo(root / proyek / "frontend", {"package.json": SVELTEKIT})
    assert _context("backenddev", root) is None
    assert _context("frontenddev", root) is None


@pytest.mark.regression("21 F1")
def test_repo_git_biasa_tidak_berubah(tmp_path):
    """Repo git yang kebetulan berisi dua sub-repo (submodule/vendored) bukan root multi-repo."""
    root = _repo(tmp_path / "mono", {"package.json": EXPRESS})
    _repo(root / "a")
    _repo(root / "b")
    v = _explain("backenddev", root)
    assert v["workspace_size"] == 0 and v["workspace"] == [] and v["source"] == "package.json"


@pytest.mark.regression("21 F1")
def test_folder_tersembunyi_dan_skip_tidak_dihitung(tmp_path):
    root = tmp_path / "root"
    _repo(root / "api", {"go.mod": GIN_GOMOD})
    _repo(root / ".cache")
    _repo(root / "node_modules")
    assert _explain("backenddev", root)["workspace_size"] == 0


@pytest.mark.regression("21 F1")
def test_opt_out_tetap_membungkam(satu_proyek):
    write_files(satu_proyek, {".claude/workflow": "fullstack\n"})
    assert _context("backenddev", satu_proyek) is None
    assert _context("frontenddev", satu_proyek) is None


@pytest.mark.regression("23 L5")
@pytest.mark.parametrize("plugin", ["backenddev", "frontenddev"])
def test_root_menunjuk_fullstack_untuk_semua_penelusuran(satu_proyek, plugin):
    text = _context(plugin, satu_proyek)
    assert "alur di dalam satu repo" in text and "jahitan lintas repo" in text
    assert "bukan subagent `Explore` atau `general-purpose` bawaan" in text
