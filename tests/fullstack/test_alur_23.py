"""Jalur `ALUR` fullstack: laporan `explore.py`, subagent explorer BE/FE, dan template dispatch (Langkah 23)."""
import pytest

from conftest import write_files
from fullstack_helpers import EXPLORE, repo, run

pytestmark = pytest.mark.regression("23 L1")

KODE = "".join(f"// baris {i}\n" for i in range(1, 41))


def _root(tmp_path):
    """`root/{backend-a,backend-b}` seperti laporan user, ditambah satu repo tanpa profil."""
    root = tmp_path / "root"
    repo(root, "backend-a", be="go", files={"internal/order/handler.go": KODE, "internal/order/service.go": KODE})
    repo(root, "backend-b", be="go", files={"internal/stok/service.go": KODE})
    repo(root, "pustaka")
    return root


def _new(root, *extra, repos="backend-a,backend-b"):
    args = ["new", "--slug", "alur-order", "--objective", "Bagaimana order dibuat?", "--lingkup", ".",
            "--repo", repos] + (list(extra) or ["--jalur", "ALUR", "--kedalaman", "ringkas"])
    return run(EXPLORE, root, *args)


def _fill(text, section, body):
    lines = text.splitlines()
    start = lines.index(f"## {section}")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[:start + 1] + ["", body, ""] + lines[end:]) + "\n"


ALUR_A = ("### `backend-a` (BE)\n\n- Entry: `POST /api/v1/orders` — `backend-a/internal/order/handler.go:3`\n"
          "1. Handler — mengikat payload — `backend-a/internal/order/handler.go:3-12`\n"
          "2. Service — menghitung total dan menyimpan dalam transaksi — `backend-a/internal/order/service.go:5-30`")
ALUR_B = ("### `backend-b` (BE)\n\n- Entry: `ReserveStok` — `backend-b/internal/stok/service.go:2`\n"
          "1. Service — mengurangi stok — `backend-b/internal/stok/service.go:2-9`")


def _lengkap(root, path, *, alur=ALUR_A + "\n\n" + ALUR_B, belum="- Tidak ada.", aturan=None, permukaan=None):
    text = path.read_text(encoding="utf-8").replace("confidence:\n", "confidence: high\n")
    text = _fill(text, "Jawaban", "Order dibuat di backend-a lalu stok dipesan di backend-b.")
    text = _fill(text, "Alur", alur)
    text = _fill(text, "Aturan Bisnis", aturan or (
        "| Repo | Aturan | Bukti |\n|---|---|---|\n"
        "| `backend-a` | total order wajib > 0 | `backend-a/internal/order/service.go:8` |"))
    text = _fill(text, "Permukaan", permukaan or (
        "| Repo | Permukaan | Detail | Bukti |\n|---|---|---|---|\n"
        "| `backend-a` | database | tabel `orders`, satu transaksi | `backend-a/internal/order/service.go:5-30` |"))
    text = _fill(text, "Celah", f"### Tidak ditemukan\n\n- Tidak ada.\n\n### Belum disisir\n\n{belum}")
    text = _fill(text, "Arahan Lanjut", "- Ubah aturan total: `cd backend-a` lalu `backend:tech-lead`.")
    path.write_text(text, encoding="utf-8")


def _checks(root, rel):
    proc, out = run(EXPLORE, root, "check", "--report", rel)
    return proc.returncode, {c["id"]: c for c in out["checks"]}


# ------------------------------------------------------------------ new

def test_new_alur_menulis_kerangka(tmp_path):
    root = _root(tmp_path)
    proc, out = _new(root)
    assert proc.returncode == 0, out
    text = (root / out["berkas"]).read_text(encoding="utf-8")
    assert "objective: Bagaimana order dibuat?\njalur: ALUR\nkedalaman: ringkas\ndibuat: " in text
    assert "repo: backend-a@" in text and ", backend-b@" in text and "confidence:\n---\n" in text
    assert [ln for ln in text.splitlines() if ln.startswith("## ")] == [
        "## Jawaban", "## Repo", "## Alur", "## Aturan Bisnis", "## Permukaan", "## Celah", "## Arahan Lanjut"]
    assert "| `backend-a` | . | BE | go | VALID |" in text
    assert _checks(root, out["berkas"])[0] == 1                    # kerangka belum diisi tidak lolos


def test_new_telusur_tidak_berubah(tmp_path):
    root = _root(tmp_path)
    proc, out = _new(root, "--jalur", "TELUSUR")
    assert proc.returncode == 0, out
    text = (root / out["berkas"]).read_text(encoding="utf-8")
    assert "jalur:" not in text and "kedalaman:" not in text and "## Jahitan" in text


@pytest.mark.parametrize("extra, alasan", [
    (["--jalur", "ALUR"], "wajib untuk `--jalur ALUR`"),
    (["--jalur", "ALUR", "--kedalaman", "dalam"], "wajib untuk `--jalur ALUR`"),
    (["--kedalaman", "ringkas"], "hanya untuk `--jalur ALUR`"),
    (["--jalur", "DALAMI", "--kedalaman", "ringkas"], "di luar TELUSUR/ALUR"),
])
def test_new_alur_argumen_ditolak(tmp_path, extra, alasan):
    root = _root(tmp_path)
    proc, out = _new(root, *extra)
    assert proc.returncode == 1 and alasan in out["galat"]
    assert not (root / ".fullstack/explore").exists()


@pytest.mark.regression("23 K5")
def test_new_alur_menolak_repo_tanpa_profil_valid(tmp_path):
    root = _root(tmp_path)
    repo(root, "rusak", files={".claude/profile/backenddev/index.json": "{"})
    for dir_ in ("pustaka", "rusak"):
        proc, out = _new(root, repos=f"backend-a,{dir_}")
        assert proc.returncode == 1 and f"repo `{dir_}` tanpa profil VALID" in out["galat"]
    proc, out = _new(root, "--jalur", "TELUSUR", repos="backend-a,pustaka")
    assert proc.returncode == 0, out                               # TELUSUR tetap seperti Langkah 21


# ------------------------------------------------------------------ check

def test_check_alur_lengkap_lolos(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    _lengkap(root, root / out["berkas"])
    code, checks = _checks(root, out["berkas"])
    assert code == 0, checks
    assert checks[4]["name"] == "Alur per repo" and checks[6]["name"] == "Bukti tabel"


def test_check_alur_repo_tanpa_langkah(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    _lengkap(root, root / out["berkas"], alur=ALUR_A)
    code, checks = _checks(root, out["berkas"])
    assert code == 1 and "repo `backend-b` tanpa langkah alur berbukti" in checks[4]["summary"]


def test_check_alur_repo_belum_disisir_lolos(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    _lengkap(root, root / out["berkas"], alur=ALUR_A,
             belum="- `backend-b` — explorer gagal dua kali")
    code, checks = _checks(root, out["berkas"])
    assert code == 0, checks


def test_check_alur_langkah_tanpa_rujukan(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    alur = ALUR_A + "\n3. Repository — menyimpan order\n\n" + ALUR_B
    _lengkap(root, root / out["berkas"], alur=alur)
    code, checks = _checks(root, out["berkas"])
    assert code == 1 and "langkah tanpa rujukan: `3. Repository" in checks[4]["summary"]


def test_check_alur_subjudul_rusak(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    alur = ALUR_A + "\n\n" + ALUR_B + "\n\n### backend-c (BE)\n\n1. x — `backend-a/internal/order/handler.go:1`" \
        "\n\n### Catatan\n\n- bebas"
    _lengkap(root, root / out["berkas"], alur=alur)
    code, checks = _checks(root, out["berkas"])
    assert code == 1
    assert "`### backend-c (BE)` menunjuk repo di luar frontmatter" in checks[4]["summary"]
    assert "`### Catatan`" in checks[4]["summary"]


def test_check_alur_bukti_tabel(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    _lengkap(root, root / out["berkas"],
             aturan="| Repo | Aturan | Bukti |\n|---|---|---|\n| `backend-a` | total > 0 | lihat service |",
             permukaan="| Repo | Permukaan | Detail | Bukti |\n|---|---|---|---|\n"
                       "| `backend-c` | cache | key order | `backend-a/internal/order/service.go:3` |")
    code, checks = _checks(root, out["berkas"])
    assert code == 1
    assert "`## Aturan Bisnis` baris 1 tanpa rujukan" in checks[6]["summary"]
    assert "`## Permukaan` baris 1: repo `backend-c` di luar frontmatter" in checks[6]["summary"]


def test_check_alur_kolom_dan_kedalaman(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    path = root / out["berkas"]
    _lengkap(root, path, aturan="| Repo | Bukti |\n|---|---|\n| `backend-a` | `backend-a/internal/order/service.go:8` |")
    path.write_text(path.read_text(encoding="utf-8").replace("kedalaman: ringkas", "kedalaman: dalam"),
                    encoding="utf-8")
    code, checks = _checks(root, out["berkas"])
    assert code == 1
    assert "`kedalaman` `dalam` wajib ringkas/menyeluruh" in checks[1]["summary"]
    assert "`## Aturan Bisnis` baris 1 punya 2 kolom, wajib 3" in checks[2]["summary"]


def test_check_alur_rujukan_melewati_berkas(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    _lengkap(root, root / out["berkas"], alur=ALUR_A.replace("handler.go:3-12", "handler.go:3-90") + "\n\n" + ALUR_B)
    code, checks = _checks(root, out["berkas"])
    assert code == 1 and "melewati 40 baris" in checks[3]["summary"]


def test_check_jalur_tidak_dikenal(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    path = root / out["berkas"]
    _lengkap(root, path)
    path.write_text(path.read_text(encoding="utf-8").replace("jalur: ALUR", "jalur: DALAMI"), encoding="utf-8")
    code, checks = _checks(root, out["berkas"])
    assert code == 1 and "`jalur` `DALAMI` di luar TELUSUR/ALUR" in checks[1]["summary"]


# ------------------------------------------------------------------ seam & list

@pytest.mark.regression("23 K9")
def test_seam_menolak_laporan_alur(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    rel = out["berkas"]
    before = (root / rel).read_text(encoding="utf-8")
    proc, out = run(EXPLORE, root, "seam", "--report", rel, "--write")
    assert proc.returncode == 1 and "`seam` hanya untuk laporan TELUSUR" in out["galat"]
    assert (root / rel).read_text(encoding="utf-8") == before


@pytest.mark.regression("23 K8")
def test_list_melaporkan_jalur(tmp_path):
    root = _root(tmp_path)
    _proc, out = _new(root)
    _lengkap(root, root / out["berkas"])
    write_files(root, {".fullstack/explore/2601010000-lama.md": (
        "---\nslug: lama\nobjective: x\ndibuat: 2601010000\nlingkup: .\nrepo: backend-a@abc\nconfidence: low\n---\n")})
    _proc, out = run(EXPLORE, root, "list")
    jalur = {r["slug"]: (r["jalur"], r["kedalaman"]) for r in out["laporan"]}
    assert jalur == {"alur-order": ("ALUR", "ringkas"), "lama": ("TELUSUR", "")}
    proc = run(EXPLORE, root, "list", "--json")[0]
    assert proc.returncode == 0
