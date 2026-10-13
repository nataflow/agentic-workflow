"""`workspace.py scan` dan `peta` plugin fullstack (Langkah 21 F2–F3)."""
import json

import pytest

from conftest import PLUGINS, load_module, write_files
from fullstack_helpers import (FE_STRUCTURE, FS_COMMON, WORKSPACE, commit_file, repo, run, satu_proyek)

pytestmark = pytest.mark.regression("21 F2")


def _lib():
    return load_module(FS_COMMON / "fullstack_lib.py", "_fs_lib_test")


def _ws():
    return load_module(WORKSPACE, "_fs_workspace_test")


def _repos(payload):
    return {r["dir"]: r for r in payload["repo"]}


# ------------------------------------------------------------------ scan

def test_scan_satu_proyek(tmp_path):
    root = satu_proyek(tmp_path)
    proc, out = run(WORKSPACE, root, "scan")
    assert proc.returncode == 0, proc.stdout
    assert out["mode"] == "WORKSPACE" and out["valid"] == 2
    r = _repos(out)
    assert set(r) == {"api", "frontend"} and {x["proyek"] for x in r.values()} == {"."}
    assert r["api"]["profil"][0]["peran"] == "BE" and r["api"]["profil"][0]["status"] == "VALID"
    assert len(r["api"]["head"]) >= 7
    assert out["proyek"] == [{"nama": ".", "repo": 2, "be": 1, "fe": 1, "tanpa_profil": 0, "tertinggal": 0}]


def test_scan_multi_proyek_dan_campuran(tmp_path):
    root = tmp_path / "company"
    repo(root, "wms/api", be="go")
    repo(root, "wms/frontend", fe="sveltekit")
    repo(root, "erp/api", be="java-spring")
    repo(root, "shared-lib")
    _proc, out = run(WORKSPACE, root, "scan")
    r = _repos(out)
    assert set(r) == {"wms/api", "wms/frontend", "erp/api", "shared-lib"}
    assert r["wms/api"]["proyek"] == "wms" and r["erp/api"]["proyek"] == "erp" and r["shared-lib"]["proyek"] == "."
    assert [p["nama"] for p in out["proyek"]] == [".", "erp", "wms"]


def test_scan_tidak_turun_ke_dalam_repo_dan_lewati_skip(tmp_path):
    root = tmp_path / "root"
    api = repo(root, "api", be="go")
    repo(api, "nested")                       # repo di dalam repo bukan anggota root
    repo(root, "node_modules")
    repo(root, ".cache")
    repo(root, "proj/.hidden")
    _proc, out = run(WORKSPACE, root, "scan")
    assert set(_repos(out)) == {"api"}


def test_scan_dua_profil_di_satu_repo(tmp_path):
    root = tmp_path / "root"
    repo(root, "app", be="node", fe="react-vite")
    repo(root, "web", fe="sveltekit")
    _proc, out = run(WORKSPACE, root, "scan")
    assert [p["peran"] for p in _repos(out)["app"]["profil"]] == ["BE", "FE"]
    assert out["valid"] == 3


@pytest.mark.parametrize("kind, status", [
    ("absent", None), ("invalid", "INVALID_JSON"), ("legacy", "LEGACY"), ("tanpa-stack", "TIDAK_SAH"),
    ("plugin-lain", "TIDAK_SAH"),
])
def test_scan_status_profil(tmp_path, kind, status):
    root = tmp_path / "root"
    repo(root, "ok", be="go")
    path = repo(root, "x", do_commit=False)
    if kind == "invalid":
        write_files(path, {".claude/profile/backenddev/index.json": "{rusak"})
    elif kind == "legacy":
        write_files(path, {".claude/profile/index.json": json.dumps({"stack": "go"})})
    elif kind == "tanpa-stack":
        write_files(path, {".claude/profile/backenddev/index.json": json.dumps({"plugin": "backenddev"})})
    elif kind == "plugin-lain":
        write_files(path, {".claude/profile/backenddev/index.json": json.dumps({"plugin": "x", "stack": "go"})})
    proc, out = run(WORKSPACE, root, "scan")
    prof = _repos(out)["x"]["profil"]
    if status is None:
        assert prof == []
    else:
        assert prof[0]["status"] == status
    if kind == "legacy":
        assert prof[0]["peran"] == "BE"
    assert proc.returncode == 0 and out["valid"] == 1


def test_scan_tanpa_commit(tmp_path):
    root = tmp_path / "root"
    repo(root, "api", be="go", do_commit=False)
    repo(root, "web", fe="sveltekit")
    _proc, out = run(WORKSPACE, root, "scan")
    api = _repos(out)["api"]
    assert api["head"] is None and api["profil"][0]["tertinggal"] is None


def test_scan_tertinggal_hanya_commit_source_root(tmp_path):
    root = tmp_path / "root"
    api = repo(root, "api", be="go", source_root="internal")
    repo(root, "web", fe="sveltekit")
    commit_file(api, "backenddev/docs/t/TASK.md", "# t\n")       # dokumen rantai: tidak dihitung
    commit_file(api, "internal/order/x.go", "package order\n")
    commit_file(api, "internal/order/y.go", "package order\n")
    _proc, out = run(WORKSPACE, root, "scan")
    assert _repos(out)["api"]["profil"][0]["tertinggal"] == 2


def test_scan_hilang_berkas_profil(tmp_path):
    root = tmp_path / "root"
    api = repo(root, "api", be="go", do_commit=False)
    (api / ".claude/profile/backenddev/commands.md").unlink()
    repo(root, "web", fe="sveltekit")
    _proc, out = run(WORKSPACE, root, "scan")
    assert _repos(out)["api"]["profil"][0]["hilang"] == ["commands.md"]


def test_scan_dalam_repo(tmp_path):
    root = satu_proyek(tmp_path)
    proc, out = run(WORKSPACE, root / "api", "scan")
    assert proc.returncode == 1 and out["mode"] == "DALAM_REPO"
    proc, out = run(WORKSPACE, root / "api" / ".claude", "scan")
    assert proc.returncode == 1 and out["mode"] == "DALAM_REPO"


def test_scan_tanpa_profil_valid_fail(tmp_path):
    root = tmp_path / "root"
    repo(root, "a")
    repo(root, "b")
    proc, out = run(WORKSPACE, root, "scan")
    assert proc.returncode == 1 and out["valid"] == 0 and out["mode"] == "WORKSPACE"
    proc, out = run(WORKSPACE, tmp_path / "root" / "a" / "..", "scan")
    assert out["mode"] == "WORKSPACE"


def test_scan_folder_kosong(tmp_path):
    (tmp_path / "kosong").mkdir()
    proc, out = run(WORKSPACE, tmp_path / "kosong", "scan")
    assert proc.returncode == 1 and out["mode"] == "KOSONG"


def test_plafon_repo(tmp_path):
    lib = _lib()
    root = tmp_path / "root"
    for name in ("a", "b", "p/c", "q/d"):
        (root / name / ".git").mkdir(parents=True)
    lib.MAX_REPO = 2
    kept, cut = lib.find_repos(root)
    assert [k[0] for k in kept] == ["a", "b"] and cut == ["p", "q"]


def test_salinan_konstanta_sama_dengan_detect():
    lib = _lib()
    detect = load_module(PLUGINS / "backend" / "hooks" / "detect.py", "_fs_detect_test")
    assert lib.SKIP_DIRS == detect.SKIP_DIRS
    assert lib.STACKS == detect.STACKS
    assert {k: ("index.json",) + v for k, v in lib.PROFILE_MD.items()} == detect.PROFILE_FILES


# ------------------------------------------------------------------ peta

@pytest.mark.regression("21 F3")
def test_peta_satu_proyek(tmp_path):
    root = satu_proyek(tmp_path)
    proc, out = run(WORKSPACE, root, "peta", "--write")
    assert proc.returncode == 0, proc.stdout
    text = (root / ".fullstack/PETA.md").read_text(encoding="utf-8")
    assert text.startswith("# Peta Aplikasi — wms\n")
    assert "| `(root)` | 1 | 1 | 0 | 0 |" in text
    assert "### `api` — BE · go · layered · HEAD " in text
    assert "| stok | `internal/stok` | http+external | `internal/http/router.go#NewRouter` |" in text
    assert "- Permukaan: http, external, config" in text
    assert "- Panggilan keluar: internal/client/erp.go · http.Client ke ERP_API_URL · sinkron stok" in text
    assert "### `frontend` — FE · sveltekit · x · HEAD " in text
    assert "- Fitur: `src/lib/features/<feature>/` — fitur: `orders`, `stok`" in text
    assert "- Rute: `src/routes/(app)/orders/+page.svelte`; `src/routes/(app)/stok/+page.svelte`" in text
    assert "- Permukaan: Routing & Navigation, HTTP Service" in text
    assert "| `frontend` | — | `api` | satu BE di proyek |" in text
    assert "| `api` | baris `external:` profil | — | belum dipetakan |" in text
    assert text.rstrip().endswith("## Belum terpetakan\n\n- Tidak ada.")
    assert out["berkas"] == ".fullstack/PETA.md"


@pytest.mark.regression("21 F3")
def test_peta_dua_be_tanpa_hubungan_fe_dan_layanan(tmp_path):
    root = tmp_path / "company"
    repo(root, "wms/api", be="go")
    repo(root, "wms/worker", be="go")
    repo(root, "wms/frontend", fe="sveltekit")
    repo(root, "erp/api", be="go")
    write_files(root, {".fullstack/layanan.json": json.dumps(
        {"versi": 1, "peta": [{"pemanggil": "erp/api", "target": "WMS_API_URL", "repo": "wms/api"}]})})
    _proc, out = run(WORKSPACE, root, "peta")
    rows = {(h["pemanggil"], h["penerima"], h["sumber"]) for h in out["hubungan"]}
    assert ("erp/api", "wms/api", "layanan.json") in rows
    assert not any(h["pemanggil"] == "wms/frontend" for h in out["hubungan"])
    assert ("wms/api", "—", "belum dipetakan") in rows and ("erp/api", "—", "belum dipetakan") not in rows


@pytest.mark.regression("21 F3")
def test_peta_layanan_rusak_tetap_terbit(tmp_path):
    root = satu_proyek(tmp_path)
    write_files(root, {".fullstack/layanan.json": "{rusak"})
    proc, out = run(WORKSPACE, root, "peta")
    assert proc.returncode == 0
    assert any("layanan.json" in g for g in out["belum_terpetakan"])


@pytest.mark.regression("21 F3")
def test_peta_baris_di_luar_format_dan_repo_rusak(tmp_path):
    root = tmp_path / "root"
    api = repo(root, "api", be="go", do_commit=False)
    write_files(api, {".claude/profile/backenddev/domain-map.md":
                      "# Domain Map\n\norder: internal/order · http · entry a.go#A\nbebas tanpa format\n"})
    web = repo(root, "web", fe="sveltekit", do_commit=False)
    write_files(web, {".claude/profile/frontenddev/structure.md": "# Structure\n\n- **Source Root**: `src/`\n"})
    repo(root, "rusak", do_commit=False, files={".claude/profile/frontenddev/index.json": "{"})
    repo(root, "polos")
    proc, out = run(WORKSPACE, root, "peta")
    assert proc.returncode == 0
    gaps = "\n".join(out["belum_terpetakan"])
    assert "`api`: `domain-map.md` baris 4 di luar format" in gaps
    assert "`web`: butir `**Features Path**` tidak ada" in gaps and "`**Route Definitions**`" in gaps
    assert "`rusak`: profil FE berstatus INVALID_JSON" in gaps and "frontend:profile` mode REFRESH" in gaps
    assert "`polos`: tanpa profil" in gaps


@pytest.mark.regression("21 F3")
def test_peta_deterministik_dan_menimpa(tmp_path):
    root = satu_proyek(tmp_path)
    write_files(root, {".fullstack/PETA.md": "lama\n"})
    run(WORKSPACE, root, "peta", "--write")
    first = (root / ".fullstack/PETA.md").read_text(encoding="utf-8")
    run(WORKSPACE, root, "peta", "--write")
    second = (root / ".fullstack/PETA.md").read_text(encoding="utf-8")
    strip = lambda t: [ln for ln in t.splitlines() if not ln.startswith("Dibangun:")]  # noqa: E731
    assert "lama" not in first and strip(first) == strip(second)


@pytest.mark.regression("21 F3")
def test_peta_dalam_repo_exit_1(tmp_path):
    root = satu_proyek(tmp_path)
    proc, out = run(WORKSPACE, root / "api", "peta")
    assert proc.returncode == 1 and out["mode"] == "DALAM_REPO"


@pytest.mark.regression("21 F3")
def test_render_profil_tertinggal():
    ws = _ws()
    card = {"peran": "BE", "stack": "go", "info": {}, "tertinggal": 51, "plugin": "backenddev", "domain": [],
            "permukaan": [], "external": None, "hilang": []}
    model = {"root": "/x/co", "ringkasan": [], "proyek": [{"nama": "wms", "repo": [
        {"dir": "wms/api", "head": "abc1234", "kartu": [card], "profil": []}]}], "hubungan": [],
        "belum_terpetakan": []}
    text = ws.render(model, "2610130000")
    assert "tertinggal 51 commit — **profil tertinggal**, `cd wms/api` lalu jalankan `backend:profile` mode REFRESH" in text
    card["tertinggal"] = 50
    assert "**profil tertinggal**" not in ws.render(model, "2610130000")


@pytest.mark.regression("21 F3")
def test_kutipan_dipotong_dan_backtick_ditutup():
    ws = _ws()
    long = "- **Features Path**: `" + "a" * 500 + "`\n"
    got = ws.quote_bullet(long, "Features Path")
    assert len(got) <= ws.KUTIPAN_MAX + 1 and got.endswith("`…") and got.count("`") % 2 == 0
    assert ws.quote_bullet(FE_STRUCTURE, "Route Definitions").count(";") == 1
    assert ws.quote_bullet("# x\n", "Features Path") is None


@pytest.mark.regression("21 F3")
def test_parser_domain_map_baris_induk_dan_butir():
    ws = _ws()
    rows, bad = ws.parse_domain_map(
        "# Domain Map\n\n```\ncontoh: a · b · entry c\n```\n"
        "- billing (invoice, payment): internal/billing · http+scheduler · entry cmd/api/routes.go#registerBilling\n"
        "tidak terdeteksi\n")
    assert bad == [] and rows == [{"domain": "billing (invoice, payment)", "path": "internal/billing",
                                   "permukaan": "http+scheduler", "entry": "cmd/api/routes.go#registerBilling"}]
