"""Prasyarat `fullstack:explore`, `explore.py new`, dan alur laporan ujung ke ujung (Langkah 21 F8)."""
import json

import pytest

from conftest import write_files
from fullstack_helpers import EXPLORE, PRECONDITION, repo, run, satu_proyek

pytestmark = pytest.mark.regression("21 F8")

ROUTER = "".join(f"// baris {i}\n" for i in range(1, 21))


def _pre(root):
    proc, out = run(PRECONDITION, root)
    return proc.returncode, out, {c["id"]: c for c in out["checks"]}


# ------------------------------------------------------------------ prasyarat

def test_prasyarat_pass(tmp_path):
    root = satu_proyek(tmp_path)
    code, out, checks = _pre(root)
    assert code == 0 and out["status"] == "PASS" and all(c["status"] == "PASS" for c in checks.values())
    assert out["resolved"]["profil_valid"] == "2" and out["resolved"]["peta"] == "belum ada"


def test_prasyarat_dalam_repo_dan_kosong(tmp_path):
    root = satu_proyek(tmp_path)
    code, _out, checks = _pre(root / "api")
    assert code == 1 and checks[3]["status"] == "FAIL" and "backend:tech-lead" in checks[3]["action"]
    (tmp_path / "kosong").mkdir()
    code, _out, checks = _pre(tmp_path / "kosong")
    assert code == 1 and checks[3]["status"] == "FAIL"


def test_prasyarat_profil(tmp_path):
    root = tmp_path / "root"
    repo(root, "a")
    repo(root, "b")
    code, _out, checks = _pre(root)
    assert code == 1 and checks[4]["status"] == "FAIL"
    repo(root, "api", be="go")
    code, out, checks = _pre(root)
    assert code == 0 and checks[4]["status"] == "WARN" and out["status"] == "PASS"


def test_prasyarat_layanan_rusak_warn(tmp_path):
    root = satu_proyek(tmp_path)
    write_files(root, {".fullstack/layanan.json": "{"})
    code, _out, checks = _pre(root)
    assert code == 0 and checks[6]["status"] == "WARN"


# ------------------------------------------------------------------ new

def _new(root, *extra):
    args = ["new", "--slug", "order-list", "--objective", "Bagaimana  layar order\nmemuat data?",
            "--lingkup", ".", "--repo", "api,frontend"]
    return run(EXPLORE, root, *(list(extra) or args))


def test_new_menulis_kerangka(tmp_path):
    root = satu_proyek(tmp_path)
    repo(root, "rusak", do_commit=False, files={".claude/profile/backenddev/index.json": "{"})
    repo(root, "pustaka")
    proc, out = _new(root)
    assert proc.returncode == 0, out
    text = (root / out["berkas"]).read_text(encoding="utf-8")
    assert out["berkas"].startswith(".fullstack/explore/") and out["berkas"].endswith("-order-list.md")
    assert "objective: Bagaimana layar order memuat data?\n" in text and "lingkup: .\n" in text
    assert "repo: api@" in text and ", frontend@" in text and "confidence:\n---\n" in text
    assert "| `api` | . | BE | go | VALID |" in text and "| `rusak` | . | BE | - | INVALID_JSON |" in text
    assert "`pustaka`" not in text
    assert [ln for ln in text.splitlines() if ln.startswith("## ")] == [
        "## Jawaban", "## Repo", "## Temuan", "## Endpoint", "## Panggilan", "## Jahitan", "## Celah", "## Arahan Lanjut"]
    proc, out = run(EXPLORE, root, "check", "--report", out["berkas"])
    assert proc.returncode == 1                                    # kerangka belum diisi tidak lolos


@pytest.mark.parametrize("args, alasan", [
    (["--slug", "Order List", "--lingkup", ".", "--repo", "api"], "kebab-case"),
    (["--slug", "x", "--lingkup", "erp", "--repo", "api"], "proyek `erp` tidak ada"),
    (["--slug", "x", "--lingkup", ".", "--repo", "worker"], "repo `worker` tidak ada"),
    (["--slug", "x", "--lingkup", ".", "--repo", "baru"], "tanpa commit"),
])
def test_new_ditolak(tmp_path, args, alasan):
    root = satu_proyek(tmp_path)
    repo(root, "baru", do_commit=False)
    proc, out = run(EXPLORE, root, "new", "--objective", "x", *args)
    assert proc.returncode == 1 and alasan in out["galat"]
    assert not (root / ".fullstack/explore").exists()


# ------------------------------------------------------------------ ujung ke ujung

def _fill(text, section, body):
    lines = text.splitlines()
    start = lines.index(f"## {section}")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[:start + 1] + ["", body, ""] + lines[end:]) + "\n"


def test_alur_laporan_lengkap(tmp_path):
    root = tmp_path / "company"
    repo(root, "wms/api", be="go", files={"internal/http/router.go": ROUTER})
    repo(root, "wms/web", fe="sveltekit", files={"src/lib/api/stok.ts": ROUTER})
    repo(root, "erp/api", be="go", files={"internal/client/wms.go": ROUTER})
    proc, out = run(EXPLORE, root, "new", "--slug", "sinkron-stok", "--objective", "Bagaimana stok mengalir?",
                    "--lingkup", "wms,erp", "--repo", "wms/api,wms/web,erp/api")
    path = root / out["berkas"]
    text = path.read_text(encoding="utf-8").replace("confidence:\n", "confidence: medium\n")
    text = _fill(text, "Jawaban", "Layar stok memanggil API WMS; ERP menarik stok dari API WMS.")
    text = _fill(text, "Temuan",
                 "### `wms/web` (FE)\n\n- Base API: /api/v1 (target `PUBLIC_API_URL`) — `wms/web/src/lib/api/stok.ts:2`\n"
                 "- P1 — layar stok memuat daftar — `wms/web/src/lib/api/stok.ts:5`\n\n"
                 "### `erp/api` (BE)\n\n- Prefix route: - \n- P1 — klien WMS — `erp/api/internal/client/wms.go:3-9`")
    text = _fill(text, "Endpoint", "| Repo | Metode | Path | Bukti |\n|---|---|---|---|\n"
                                   "| `wms/api` | GET | `/api/v1/stok/{id}` | `wms/api/internal/http/router.go:7` |")
    text = _fill(text, "Panggilan",
                 "| Pemanggil | Target | Metode | Path | Bukti |\n|---|---|---|---|---|\n"
                 "| `wms/web` | `PUBLIC_API_URL` | GET | `/stok/${id}` | `wms/web/src/lib/api/stok.ts:5` |\n"
                 "| `erp/api` | `WMS_API_URL` | GET | `/stok/:id` | `erp/api/internal/client/wms.go:4` |")
    text = _fill(text, "Celah", "### Tidak ditemukan\n\n- Tidak ada.\n\n### Belum disisir\n\n- Tidak ada.\n\n"
                                "### Belum dipetakan\n\n- `erp/api` → `WMS_API_URL`: penerima belum dikonfirmasi.")
    text = _fill(text, "Arahan Lanjut", "- Ubah sinkron stok: `cd erp/api` lalu `backend:tech-lead`.")
    path.write_text(text, encoding="utf-8")

    proc, out = run(EXPLORE, root, "seam", "--report", str(path), "--write")
    assert [(r["pemanggil"], r["status"]) for r in out["baris"]] == [("wms/web", "COCOK"), ("erp/api", "DUGAAN")]
    proc, out = run(EXPLORE, root, "check", "--report", str(path))
    assert proc.returncode == 0, out

    run(EXPLORE, root, "layanan", "set", "--pemanggil", "erp/api", "--target", "WMS_API_URL", "--repo", "wms/api",
        "--prefix", "/api/v1")
    proc, out = run(EXPLORE, root, "seam", "--report", str(path), "--write")
    assert [r["status"] for r in out["baris"]] == ["COCOK", "COCOK"]
    assert run(EXPLORE, root, "check", "--report", str(path))[0].returncode == 0
    _proc, out = run(EXPLORE, root, "list")
    assert out["laporan"][0]["slug"] == "sinkron-stok" and out["laporan"][0]["basi"] is False
    assert json.loads((root / ".fullstack/layanan.json").read_text(encoding="utf-8"))["peta"][0]["prefix"] == "/api/v1"
