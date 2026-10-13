"""`explore.py` plugin fullstack: list, seam, check, layanan (Langkah 21 F4–F6)."""
import json

import pytest

from conftest import git, load_module, write_files
from fullstack_helpers import EXPLORE, commit_file, repo, run, satu_proyek

ROUTER = "".join(f"// baris {i}\n" for i in range(1, 21))
ORDERS_TS = "".join(f"// baris {i}\n" for i in range(1, 11))


def _ex():
    return load_module(EXPLORE, "_fs_explore_test")


@pytest.fixture
def ws(tmp_path):
    root = tmp_path / "wms"
    repo(root, "api", be="go", files={"internal/http/router.go": ROUTER})
    repo(root, "frontend", fe="sveltekit", source_root="src", files={"src/lib/api/orders.ts": ORDERS_TS})
    return root


def _head(root, d):
    return git(root / d, "rev-parse", "--short=7", "HEAD").strip()


def report(root, *, fm=None, endpoint=None, panggilan=None, jahitan="- Tidak ada.", celah=None, arahan=None,
           repo_rows=None, temuan=None, drop=None):
    fm_data = {"slug": "order-list", "objective": "Bagaimana layar order memuat daftar order?",
               "dibuat": "2610131200", "lingkup": ".",
               "repo": f"api@{_head(root, 'api')}, frontend@{_head(root, 'frontend')}", "confidence": "high"}
    fm_data.update(fm or {})
    sections = {
        "Jawaban": "Layar order memanggil `GET /orders` lewat service HTTP.",
        "Repo": repo_rows or ("| Dir | Proyek | Peran | Stack | Profil | HEAD |\n|---|---|---|---|---|---|\n"
                              "| `api` | . | BE | go | VALID | x |\n| `frontend` | . | FE | sveltekit | VALID | y |"),
        "Temuan": temuan or ("### `api` (BE)\n\n- Prefix route: /api/v1 — `api/internal/http/router.go:3`\n\n"
                             "### `frontend` (FE)\n\n- Base API: /api/v1 (target `PUBLIC_API_URL`) — "
                             "`frontend/src/lib/api/orders.ts:2`"),
        "Endpoint": endpoint if endpoint is not None else (
            "| Repo | Metode | Path | Bukti |\n|---|---|---|---|\n"
            "| `api` | GET | `/api/v1/orders` | `api/internal/http/router.go:5` |"),
        "Panggilan": panggilan if panggilan is not None else (
            "| Pemanggil | Target | Metode | Path | Bukti |\n|---|---|---|---|---|\n"
            "| `frontend` | `PUBLIC_API_URL` | GET | `/orders` | `frontend/src/lib/api/orders.ts:4` |"),
        "Jahitan": jahitan,
        "Celah": celah or "### Tidak ditemukan\n\n- Tidak ada.\n\n### Belum disisir\n\n- Tidak ada.",
        "Arahan Lanjut": arahan or "- Untuk mengubah daftar order: `cd frontend` lalu `frontend:lead`.",
    }
    for key in drop or ():
        sections.pop(key)
    text = "---\n" + "".join(f"{k}: {v}\n" for k, v in fm_data.items()) + "---\n\n"
    text += "\n\n".join(f"## {k}\n\n{v}" for k, v in sections.items()) + "\n"
    path = root / ".fullstack/explore/2610131200-order-list.md"
    write_files(root, {path.relative_to(root).as_posix(): text})
    return path


def _seam_write(root, path):
    proc, out = run(EXPLORE, root, "seam", "--report", str(path), "--write")
    assert proc.returncode == 0, proc.stdout
    return out


def _check(root, path):
    proc, out = run(EXPLORE, root, "check", "--report", str(path))
    return proc.returncode, {c["id"]: c for c in out["checks"]}


# ------------------------------------------------------------------ check + seam --write

@pytest.mark.regression("21 F4")
def test_laporan_utuh_lolos_check(ws):
    path = report(ws)
    out = _seam_write(ws, path)
    assert [r["status"] for r in out["baris"]] == ["COCOK"]
    text = path.read_text(encoding="utf-8")
    assert "| `frontend` | `PUBLIC_API_URL` | GET | `/api/v1/orders` | `api` | COCOK |" in text
    code, checks = _check(ws, path)
    assert code == 0, checks


@pytest.mark.regression("21 F4")
def test_check_frontmatter(ws):
    path = report(ws, fm={"slug": "Bukan Slug", "dibuat": "kemarin", "confidence": "yakin", "lingkup": "erp",
                          "repo": "api@abc1234, worker@def5678, frontend"})
    code, checks = _check(ws, path)
    s = checks[1]["summary"]
    assert code == 1 and "kebab-case" in s and "YYMMDDhhmm" in s and "high/medium/low" in s
    assert "`lingkup` `erp`" in s and "`worker` tidak ada" in s and "tanpa SHA" in s


@pytest.mark.regression("21 F4")
def test_check_seksi_dan_tabel(ws):
    path = report(ws, drop=["Celah"])
    code, checks = _check(ws, path)
    assert code == 1 and "seksi wajib berurutan" in checks[2]["summary"]
    path = report(ws, endpoint="| Repo | Metode | Path | Bukti |\n|---|---|---|---|\n| `api` | FETCH | `/x` |")
    _code, checks = _check(ws, path)
    assert "punya 3 kolom" in checks[2]["summary"]
    path = report(ws, panggilan="bebas")
    _code, checks = _check(ws, path)
    assert "`## Panggilan` wajib tabel" in checks[2]["summary"]


@pytest.mark.regression("21 F4")
def test_check_rujukan(ws):
    temuan = ("### `api` (BE)\n\n- a — `api/internal/http/router.go:21`\n- b — `api/tidak/ada.go:1`\n"
              "- c — `erp/api/x.go:1`\n- d — `internal/http/router.go:3`\n- jam `10:30` dan host `localhost:8080`\n"
              "- rentang — `api/internal/http/router.go:2-20`")
    path = report(ws, temuan=temuan)
    _seam_write(ws, path)
    code, checks = _check(ws, path)
    s = checks[3]["summary"]
    assert code == 1 and "router.go:21` melewati 20 baris" in s and "`api/tidak/ada.go` tidak ada" in s
    assert "`erp/api/x.go:1` menunjuk repo di luar" in s and "`internal/http/router.go:3` menunjuk repo" in s
    assert "10:30" not in s and "localhost" not in s and "2-20" not in s


@pytest.mark.regression("21 F4")
def test_check_jahitan_dikarang_model_gagal(ws):
    path = report(ws, jahitan="| Pemanggil | Target | Metode | Path | Penerima | Status |\n|---|---|---|---|---|---|\n"
                              "| `frontend` | `PUBLIC_API_URL` | GET | `/orders` | `api` | COCOK |")
    code, checks = _check(ws, path)
    assert code == 1 and "seam --write" in checks[4]["summary"]


@pytest.mark.regression("21 F4")
def test_check_arahan_profil_dan_celah(ws):
    rows = ("| Dir | Proyek | Peran | Stack | Profil | HEAD |\n|---|---|---|---|---|---|\n"
            "| `api` | . | BE | go | VALID | x |\n| `legacy-app` | . | ? | - | LEGACY | y |")
    path = report(ws, repo_rows=rows)
    _seam_write(ws, path)
    code, checks = _check(ws, path)
    assert code == 1 and "`legacy-app` berprofil LEGACY" in checks[5]["summary"]


@pytest.mark.regression("21 F4")
def test_check_placeholder(ws):
    path = report(ws, arahan="- TODO isi nanti")
    _seam_write(ws, path)
    code, checks = _check(ws, path)
    assert code == 1 and "`TODO`" in checks[7]["summary"]


@pytest.mark.regression("21 F4")
def test_check_laporan_tidak_ada(ws):
    proc, out = run(EXPLORE, ws, "check", "--report", ".fullstack/explore/x.md")
    assert proc.returncode == 1 and out["status"] == "FAIL"


@pytest.mark.regression("21 F5")
def test_tanpa_panggilan_dan_endpoint(ws):
    path = report(ws, endpoint="- Tidak ada.", panggilan="- Tidak ada.")
    out = _seam_write(ws, path)
    assert out["baris"] == [] and "## Jahitan\n\n- Tidak ada.\n" in path.read_text(encoding="utf-8")
    assert _check(ws, path)[0] == 0


# ------------------------------------------------------------------ seam (modul)

def _sc(*repos):
    """Scan sintetis: (dir, proyek, peran...)."""
    return {"repo": [{"dir": d, "proyek": p, "profil": [{"peran": r, "status": "VALID"} for r in roles]}
                     for d, p, *roles in repos]}


def _rep(ex, endpoints, calls, lingkup="", bases=None):
    temuan = "\n".join(f"### `{d}` (FE)\n\n- Base API: {b} (target `X`) — `{d}/a.ts:1`\n" for d, b in (bases or {}).items())
    ep = "| Repo | Metode | Path | Bukti |\n|---|---|---|---|\n" + "\n".join(
        f"| `{r}` | {m} | `{p}` | `{r}/r.go:1` |" for r, m, p in endpoints)
    cl = "| Pemanggil | Target | Metode | Path | Bukti |\n|---|---|---|---|---|\n" + "\n".join(
        f"| `{c}` | `{t}` | {m} | `{p}` | `{c}/c.go:1` |" for c, t, m, p in calls)
    text = (f"---\nlingkup: {lingkup}\n---\n\n## Temuan\n\n{temuan}\n\n## Endpoint\n\n{ep}\n\n"
            f"## Panggilan\n\n{cl}\n\n## Jahitan\n\n- Tidak ada.\n")
    return ex.parse_report(text)


def _status(rows):
    return [(r["pemanggil"], r["penerima"], r["status"]) for r in rows]


@pytest.mark.regression("21 F5")
@pytest.mark.parametrize("raw, want", [
    ("/projects/${id}", "/projects/{}"), ("/projects/:id/", "/projects/{}"), ("/a/[slug]/b", "/a/{}/b"),
    ("/a/<id>", "/a/{}"), ("https://api.x.com/v1/a?q=1", "/v1/a"), ("orders", "/orders"),
    ("/items/item-${id}", "/items/item-{}"), ("/a/{orderId}", "/a/{}"),
])
def test_norm_path(raw, want):
    assert _ex().norm_path(raw) == want


@pytest.mark.regression("21 F5")
def test_match_akhiran_batas_segmen():
    ex = _ex()
    assert ex._match("/stok/{}", "/api/v1/stok/{}", exact=False)
    assert not ex._match("/stok", "/api/v1/restok", exact=False)
    assert not ex._match("/stok/{}", "/api/v1/stok/{}", exact=True)
    assert not ex._match("/", "/api/v1", exact=False)


@pytest.mark.regression("21 F5")
def test_fe_satu_be_cocok_dan_tidak_ada():
    ex = _ex()
    sc = _sc(("wms/api", "wms", "BE"), ("wms/web", "wms", "FE"), ("erp/api", "erp", "BE"))
    rep = _rep(ex, [("wms/api", "GET", "/api/v1/orders/{id}"), ("erp/api", "GET", "/api/v1/stok")],
               [("wms/web", "API_URL", "GET", "/orders/${id}"), ("wms/web", "API_URL", "GET", "/stok"),
                ("wms/web", "API_URL", "POST", "/orders/1")], bases={"wms/web": "/api/v1"})
    rows = ex.seam_rows(rep, sc, [])
    assert _status(rows) == [("wms/web", "wms/api", "COCOK"), ("wms/web", "wms/api", "TIDAK_ADA_DI_TARGET"),
                             ("wms/web", "wms/api", "TIDAK_ADA_DI_TARGET"), ("—", "erp/api", "TAK_TERPANGGIL")]
    assert rows[0]["path"] == "/api/v1/orders/{}"


@pytest.mark.regression("21 F5")
def test_fe_dua_be_dugaan_ambigu_tanpa_lintas_proyek():
    ex = _ex()
    sc = _sc(("wms/api", "wms", "BE"), ("wms/worker", "wms", "BE"), ("wms/web", "wms", "FE"), ("erp/api", "erp", "BE"))
    rep = _rep(ex, [("wms/api", "GET", "/api/v1/orders"), ("wms/worker", "GET", "/api/v1/health"),
                    ("wms/api", "GET", "/api/v1/health"), ("erp/api", "GET", "/api/v1/stok")],
               [("wms/web", "API_URL", "GET", "/orders"), ("wms/web", "API_URL", "GET", "/health"),
                ("wms/web", "API_URL", "GET", "/stok")], bases={"wms/web": "/api/v1"})
    rows = ex.seam_rows(rep, sc, [])
    assert _status(rows)[:3] == [("wms/web", "wms/api", "DUGAAN"), ("wms/web", "wms/api, wms/worker", "AMBIGU"),
                                 ("wms/web", "—", "TAK_DIKENAL")]


@pytest.mark.regression("21 F5")
def test_be_ke_be_tanpa_dan_dengan_pemetaan():
    ex = _ex()
    sc = _sc(("wms/api", "wms", "BE"), ("erp/api", "erp", "BE"), ("crm/api", "crm", "BE"))
    eps = [("wms/api", "GET", "/api/v1/stok/{id}"), ("crm/api", "GET", "/api/v1/health"),
           ("wms/api", "GET", "/api/v1/health"), ("erp/api", "GET", "/api/v1/stok/{id}")]
    calls = [("erp/api", "WMS_URL", "GET", "/stok/${id}"), ("erp/api", "X", "GET", "/health"),
             ("erp/api", "PAY_URL", "POST", "/charge")]
    rows = ex.seam_rows(_rep(ex, eps, calls), sc, [])
    assert _status(rows)[:3] == [("erp/api", "wms/api", "DUGAAN"), ("erp/api", "crm/api, wms/api", "AMBIGU"),
                                 ("erp/api", "—", "TAK_DIKENAL")]
    peta = [{"pemanggil": "erp/api", "target": "WMS_URL", "repo": "wms/api", "prefix": "/api/v1"},
            {"pemanggil": "erp/api", "target": "PAY_URL", "repo": "crm/api", "prefix": ""}]
    rows = ex.seam_rows(_rep(ex, eps, calls), sc, peta)
    assert _status(rows)[:3] == [("erp/api", "wms/api", "COCOK"), ("erp/api", "crm/api, wms/api", "AMBIGU"),
                                 ("erp/api", "crm/api", "TIDAK_ADA_DI_TARGET")]
    assert rows[0]["path"] == "/api/v1/stok/{}"
    assert ("—", "erp/api", "TAK_TERPANGGIL") in _status(rows)       # BE bukan penerima panggilannya sendiri


@pytest.mark.regression("21 F5")
def test_prefix_pemetaan_mewajibkan_kecocokan_persis():
    ex = _ex()
    sc = _sc(("a", ".", "BE"), ("b", ".", "BE"))
    peta = [{"pemanggil": "a", "target": "B_URL", "repo": "b", "prefix": "/v2"}]
    rows = ex.seam_rows(_rep(ex, [("b", "GET", "/api/v1/x")], [("a", "B_URL", "GET", "/x")]), sc, peta)
    assert _status(rows)[0] == ("a", "b", "TIDAK_ADA_DI_TARGET")


@pytest.mark.regression("21 F5")
def test_lingkup_membatasi_calon():
    ex = _ex()
    sc = _sc(("wms/api", "wms", "BE"), ("erp/api", "erp", "BE"), ("crm/api", "crm", "BE"))
    rep = _rep(ex, [("crm/api", "GET", "/x")], [("erp/api", "T", "GET", "/x")], lingkup="wms, erp")
    assert _status(ex.seam_rows(rep, sc, []))[0] == ("erp/api", "—", "TAK_DIKENAL")


# ------------------------------------------------------------------ list

@pytest.mark.regression("21 F4")
def test_list_basi_dan_rusak(ws):
    report(ws)
    write_files(ws, {".fullstack/explore/2610131100-rusak.md": "tanpa frontmatter\n"})
    _proc, out = run(EXPLORE, ws, "list")
    assert [r["berkas"] for r in out["laporan"]] == [".fullstack/explore/2610131200-order-list.md"]
    assert out["laporan"][0]["basi"] is False and out["laporan"][0]["lingkup"] == ["."]
    assert out["rusak"][0]["berkas"].endswith("rusak.md")
    commit_file(ws / "api", "internal/x.go", "package x\n")
    _proc, out = run(EXPLORE, ws, "list")
    lap = out["laporan"][0]
    assert lap["basi"] is True and [r["basi"] for r in lap["repo"]] == [True, False]


@pytest.mark.regression("21 F4")
def test_list_kosong_dan_dalam_repo(ws):
    proc, out = run(EXPLORE, ws, "list")
    assert proc.returncode == 0 and out["laporan"] == []
    proc, out = run(EXPLORE, ws / "api", "list")
    assert proc.returncode == 1 and out["mode"] == "DALAM_REPO"


# ------------------------------------------------------------------ layanan

@pytest.fixture
def company(tmp_path):
    root = tmp_path / "company"
    repo(root, "wms/api", be="go")
    repo(root, "wms/web", fe="sveltekit")
    repo(root, "erp/api", be="go")
    return root


@pytest.mark.regression("21 F6")
def test_layanan_set_list_timpa_hapus(company):
    proc, _ = run(EXPLORE, company, "layanan", "set", "--pemanggil", "erp/api", "--target", "WMS_URL",
                  "--repo", "wms/api", "--prefix", "/api/v1")
    assert proc.returncode == 0
    run(EXPLORE, company, "layanan", "set", "--pemanggil", "erp/api", "--target", "WMS_URL", "--repo", "wms/api")
    _proc, out = run(EXPLORE, company, "layanan", "list")
    assert out["peta"] == [{"pemanggil": "erp/api", "target": "WMS_URL", "repo": "wms/api", "prefix": ""}]
    data = json.loads((company / ".fullstack/layanan.json").read_text(encoding="utf-8"))
    assert data == {"versi": 1, "peta": [{"pemanggil": "erp/api", "target": "WMS_URL", "repo": "wms/api"}]}
    proc, _ = run(EXPLORE, company, "layanan", "hapus", "--pemanggil", "erp/api", "--target", "WMS_URL")
    assert proc.returncode == 0
    assert run(EXPLORE, company, "layanan", "list")[1]["peta"] == []
    proc, out = run(EXPLORE, company, "layanan", "hapus", "--pemanggil", "erp/api", "--target", "WMS_URL")
    assert proc.returncode == 1 and "tidak ada" in out["galat"]


@pytest.mark.regression("21 F6")
@pytest.mark.parametrize("args, alasan", [
    (["--pemanggil", "x/api", "--target", "T", "--repo", "wms/api"], "bukan repo di root"),
    (["--pemanggil", "erp/api", "--target", "T", "--repo", "x/api"], "bukan repo di root"),
    (["--pemanggil", "erp/api", "--target", "T", "--repo", "wms/web"], "bukan repo BE"),
    (["--pemanggil", "wms/api", "--target", "T", "--repo", "wms/api"], "sama dengan"),
    (["--pemanggil", "erp/api", "--target", "T", "--repo", "wms/api", "--prefix", "api"], "diawali `/`"),
    (["--pemanggil", "erp/api", "--repo", "wms/api"], "--target wajib"),
])
def test_layanan_set_ditolak(company, args, alasan):
    proc, out = run(EXPLORE, company, "layanan", "set", *args)
    assert proc.returncode == 1 and alasan in out["galat"]
    assert not (company / ".fullstack/layanan.json").exists()


@pytest.mark.regression("21 F6")
@pytest.mark.parametrize("isi", ["{rusak", json.dumps({"versi": 2, "peta": []}),
                                 json.dumps({"versi": 1, "peta": [{"pemanggil": "a"}]})])
def test_layanan_rusak(company, isi):
    write_files(company, {".fullstack/layanan.json": isi})
    proc, out = run(EXPLORE, company, "layanan", "list")
    assert proc.returncode == 1 and out["galat"]
    proc, _ = run(EXPLORE, company, "layanan", "set", "--pemanggil", "erp/api", "--target", "T", "--repo", "wms/api")
    assert proc.returncode == 1


@pytest.mark.regression("21 F6")
def test_seam_berhenti_bila_layanan_rusak(ws):
    path = report(ws)
    write_files(ws, {".fullstack/layanan.json": "{"})
    proc, out = run(EXPLORE, ws, "seam", "--report", str(path))
    assert proc.returncode == 1 and "layanan.json" in out["galat"]


@pytest.mark.regression("21 F4")
def test_check_dugaan_wajib_di_celah(ws):
    repo(ws, "worker", be="go")
    path = report(ws)
    out = _seam_write(ws, path)
    assert out["baris"][0]["status"] == "DUGAAN"
    code, checks = _check(ws, path)
    assert code == 1 and "DUGAAN `frontend` → `PUBLIC_API_URL`" in checks[6]["summary"]
    path = report(ws, celah="### Belum dipetakan\n\n- `frontend` → `PUBLIC_API_URL`: penerima belum dikonfirmasi.")
    _seam_write(ws, path)
    assert _check(ws, path)[0] == 0
