"""Pengecualian proyek/repo lewat `.fullstack/abaikan` (Langkah 22 A1–A4)."""
import pytest

from conftest import load_module, write_files
from fullstack_helpers import EXPLORE, FS_COMMON, PRECONDITION, WORKSPACE, repo, run

ABAIKAN = ".fullstack/abaikan"


@pytest.fixture
def company(tmp_path):
    root = tmp_path / "company"
    repo(root, "wms/api", be="go")
    repo(root, "wms/web", fe="sveltekit")
    repo(root, "wms/infra")
    repo(root, "erp/api", be="go")
    repo(root, "legacy/api", be="go")
    repo(root, "legacy/web", fe="sveltekit")
    repo(root, "api-lama", be="go")
    return root


def _lib():
    return load_module(FS_COMMON / "fullstack_lib.py", "_fs_lib_abaikan")


def _dirs(out):
    return sorted(r["dir"] for r in out["repo"])


# ------------------------------------------------------------------ A1 scan

@pytest.mark.regression("22 A1")
def test_scan_mengecualikan_proyek_repo_dan_glob(company):
    write_files(company, {ABAIKAN: "# warisan\n\nlegacy/\n*/infra\napi-lama\n"})
    proc, out = run(WORKSPACE, company, "scan")
    assert proc.returncode == 0
    assert _dirs(out) == ["erp/api", "wms/api", "wms/web"]
    assert out["dikecualikan"] == [
        {"dir": "api-lama", "jenis": "repo", "pola": "api-lama"},
        {"dir": "legacy", "jenis": "proyek", "pola": "legacy", "repo": 2},
        {"dir": "wms/infra", "jenis": "repo", "pola": "*/infra"},
    ]
    assert out["abaikan"]["pola"] == ["legacy", "*/infra", "api-lama"] and out["abaikan"]["galat"] == []


@pytest.mark.regression("22 A1")
def test_pola_nama_mengena_di_dua_tingkat(tmp_path):
    root = tmp_path / "root"
    repo(root, "lama", be="go")
    repo(root, "wms/lama", be="go")
    repo(root, "wms/api", be="go")
    write_files(root, {ABAIKAN: "lama\n"})
    _proc, out = run(WORKSPACE, root, "scan")
    assert _dirs(out) == ["wms/api"]


@pytest.mark.regression("22 A1")
def test_pola_path_hanya_path_itu(company):
    write_files(company, {ABAIKAN: "wms/api\n"})
    _proc, out = run(WORKSPACE, company, "scan")
    assert "wms/api" not in _dirs(out) and "erp/api" in _dirs(out)


@pytest.mark.regression("22 A1")
def test_pola_tidak_sah_dilaporkan_dan_dilewati(company):
    write_files(company, {ABAIKAN: "../luar\n~/x\na/b/c\n/legacy/\n"})
    _proc, out = run(WORKSPACE, company, "scan")
    galat = "\n".join(out["abaikan"]["galat"])
    assert "baris 1" in galat and "baris 2" in galat and "baris 3" in galat
    assert out["abaikan"]["pola"] == ["legacy"]          # `/` di awal dan akhir dibuang
    assert "legacy/api" not in _dirs(out)


@pytest.mark.regression("22 A1")
def test_berkas_tak_terbaca_tanpa_pengecualian(company):
    (company / ".fullstack").mkdir()
    (company / ABAIKAN).write_bytes(b"\xff\xfe legacy\n")
    proc, out = run(WORKSPACE, company, "scan")
    assert proc.returncode == 0 and "legacy/api" in _dirs(out)
    assert "tidak terbaca" in out["abaikan"]["galat"][0]


@pytest.mark.regression("22 A1")
def test_tanpa_berkas(company):
    _proc, out = run(WORKSPACE, company, "scan")
    assert out["dikecualikan"] == [] and out["abaikan"]["ada"] is False


@pytest.mark.regression("22 A1")
def test_plafon_tidak_menghitung_yang_dikecualikan(tmp_path):
    lib = _lib()
    root = tmp_path / "root"
    for name in ("a", "b", "c", "old/x", "old/y"):
        (root / name / ".git").mkdir(parents=True)
    lib.MAX_REPO = 2
    kept, cut, excluded = lib.find_repos(root, ["old", "a"])
    assert [k[0] for k in kept] == ["b", "c"] and cut == []
    assert [e["dir"] for e in excluded] == ["a", "old"]


# ------------------------------------------------------------------ A2 abaikan CLI

@pytest.mark.regression("22 A2")
def test_tambah_list_hapus(company):
    write_files(company, {ABAIKAN: "# dijaga\n"})
    proc, out = run(WORKSPACE, company, "abaikan", "tambah", "legacy/")
    assert proc.returncode == 0 and out["pola"] == "legacy" and out["terkena"] == ["legacy (proyek)"]
    proc, out = run(WORKSPACE, company, "abaikan", "tambah", "*/infra")
    assert out["terkena"] == ["wms/infra"]
    proc, out = run(WORKSPACE, company, "abaikan", "list")
    assert [d["pola"] for d in out["daftar"]] == ["legacy", "*/infra"]
    proc, out = run(WORKSPACE, company, "abaikan", "hapus", "legacy")
    assert proc.returncode == 0
    assert (company / ABAIKAN).read_text(encoding="utf-8") == "# dijaga\n*/infra\n"


@pytest.mark.regression("22 A2")
@pytest.mark.parametrize("aksi, pola, alasan", [
    ("tambah", "../x", "`..`"), ("tambah", "a/b/c", "dua tingkat"), ("tambah", "", "pola kosong"),
    ("hapus", "tidak-ada", "tidak ada di"),
])
def test_abaikan_ditolak(company, aksi, pola, alasan):
    proc, out = run(WORKSPACE, company, "abaikan", aksi, pola)
    assert proc.returncode == 1 and alasan in out["galat"]


@pytest.mark.regression("22 A2")
def test_tambah_duplikat_dan_tanpa_kecocokan(company):
    run(WORKSPACE, company, "abaikan", "tambah", "legacy")
    proc, out = run(WORKSPACE, company, "abaikan", "tambah", "legacy")
    assert proc.returncode == 1 and "sudah ada" in out["galat"]
    proc, out = run(WORKSPACE, company, "abaikan", "tambah", "repo-masa-depan")
    assert proc.returncode == 0 and out["terkena"] == [] and out["peringatan"]


@pytest.mark.regression("22 A2")
def test_abaikan_dalam_repo(company):
    proc, out = run(WORKSPACE, company / "wms/api", "abaikan", "list")
    assert proc.returncode == 1 and "dalam repo git" in out["galat"]


# ------------------------------------------------------------------ A3 peta, laporan, prasyarat

@pytest.mark.regression("22 A3")
def test_peta_menyebut_yang_dikecualikan(company):
    write_files(company, {ABAIKAN: "legacy\n*/infra\nx/y/z\n"})
    run(WORKSPACE, company, "peta", "--write")
    text = (company / ".fullstack/PETA.md").read_text(encoding="utf-8")
    assert "· 3 repo dikecualikan ·" in text
    assert "| `legacy` (proyek, 2 repo) | `legacy` |" in text and "| `wms/infra` | `*/infra` |" in text
    assert "### `legacy/api`" not in text
    assert text.index("## Dikecualikan") < text.index("## Belum terpetakan")
    assert "baris 3 `x/y/z`" in text.split("## Belum terpetakan", 1)[1]


@pytest.mark.regression("22 A3")
def test_peta_tanpa_pengecualian(company):
    run(WORKSPACE, company, "peta", "--write")
    text = (company / ".fullstack/PETA.md").read_text(encoding="utf-8")
    assert "## Dikecualikan\n\n- Tidak ada.\n" in text and "dikecualikan ·" not in text


@pytest.mark.regression("22 A3")
def test_new_dan_layanan_menolak_yang_dikecualikan(company):
    write_files(company, {ABAIKAN: "legacy\n"})
    proc, out = run(EXPLORE, company, "new", "--slug", "x", "--objective", "x", "--lingkup", "legacy",
                    "--repo", "legacy/api")
    assert proc.returncode == 1
    assert "proyek `legacy` dikecualikan `.fullstack/abaikan` (pola `legacy`)" in out["galat"]
    assert "repo `legacy/api` dikecualikan" in out["galat"]
    proc, out = run(EXPLORE, company, "layanan", "set", "--pemanggil", "erp/api", "--target", "T",
                    "--repo", "legacy/api")
    assert proc.returncode == 1 and "dikecualikan" in out["galat"]


@pytest.mark.regression("22 A3")
def test_check_menolak_laporan_yang_merujuk_repo_dikecualikan(company):
    _proc, out = run(EXPLORE, company, "new", "--slug", "x", "--objective", "x", "--lingkup", "wms",
                     "--repo", "wms/api")
    write_files(company, {ABAIKAN: "wms/api\n"})
    proc, res = run(EXPLORE, company, "check", "--report", out["berkas"])
    checks = {c["id"]: c for c in res["checks"]}
    assert proc.returncode == 1 and "repo `wms/api` dikecualikan" in checks[1]["summary"]


@pytest.mark.regression("22 A3")
def test_prasyarat_mencatat_dan_memperingatkan(company):
    write_files(company, {ABAIKAN: "legacy\nx/y/z\n"})
    proc, out = run(PRECONDITION, company)
    checks = {c["id"]: c for c in out["checks"]}
    assert proc.returncode == 0 and out["resolved"]["dikecualikan"] == "1"
    assert checks[7]["status"] == "WARN" and "x/y/z" in checks[7]["summary"]
    write_files(company, {ABAIKAN: "legacy\n"})
    _proc, out = run(PRECONDITION, company)
    assert {c["id"]: c for c in out["checks"]}[7]["status"] == "PASS"
