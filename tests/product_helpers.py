"""Pembantu tes plugin `product`: charterdir di tiap keadaan siklus hidup, untuk ketiga mode.

Diimpor tes `tests/product/` (`from product_helpers import …`); fixture `ws` dan `empty_ws` ikut terimpor."""
import re
from pathlib import Path
from typing import Dict, Optional

import pytest

from conftest import PLUGINS, git, run_script

COMMON = PLUGINS / "product" / "skills" / "_common"
CHARTER = COMMON / "charter.py"
VALIDATE = COMMON / "validate_doc.py"
SLUG = "keuangan-umkm"
TD = f"product/{SLUG}"

CONTEXT = {
    "NEW_PRODUCT": ("Pemilik UMKM warung makan", "kas dicatat di buku tulis sehingga laba harian tidak diketahui",
                    "keuangan usaha mikro"),
    "NEW_FEATURE": ("Pemilik warung", "belum bisa melihat laba harian", "menu laporan"),
    "IMPROVEMENT": ("Kasir", "penjualan harus dicatat ulang di buku", "pencatatan penjualan"),
}

FACTS = """### Fakta

#### Purpose
Pemilik warung makan tidak tahu laba harian karena kas dicatat di buku tulis dan sering tidak lengkap.

#### Actors
Pemilik warung mencatat pengeluaran dan melihat laba. Kasir mencatat penjualan harian.

#### Business Process
Kasir mencatat penjualan tiap transaksi; pemilik mencatat pengeluaran belanja; pemilik melihat laba harian.

#### Business Rules
Pengeluaran di atas Rp1.000.000 wajib disertai foto nota.

#### Success Criteria
Pemilik melihat laba harian dalam 1 menit sesudah toko tutup.

#### Scope
Versi pertama: catat penjualan, catat pengeluaran, laporan laba harian. Stok bahan belum.

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|
| 1 | 2026-10-09 | Siapa yang mencatat penjualan? | Kasir | Budi |
| 2 | 2026-10-09 | Kapan laba dilihat? | Sesudah toko tutup | Budi |
"""

ACTORS = {
    "NEW_PRODUCT": ("- **Pemilik Warung** — mencatat pengeluaran dan melihat laba harian\n"
                    "- **Kasir** — mencatat penjualan tiap transaksi"),
    "NEW_FEATURE": ("- **Pemilik Warung** [ADA] — mencatat pengeluaran dan melihat laba harian\n"
                    "- **Kasir** [BARU] — mencatat penjualan tiap transaksi"),
}
ACTORS["IMPROVEMENT"] = ACTORS["NEW_FEATURE"]

STEPS = ("1. **Kasir** mencatat tiap penjualan beserta nominalnya\n"
         "2. **Pemilik Warung** mencatat pengeluaran belanja\n"
         "   - Bila pengeluaran di atas Rp1.000.000, pemilik melampirkan foto nota (BR-1)\n"
         "3. **Sistem** menghitung laba harian\n"
         "4. **Pemilik Warung** melihat laba harian sesudah toko tutup")
PROCESS = {
    "NEW_PRODUCT": STEPS,
    "NEW_FEATURE": STEPS,
    "IMPROVEMENT": ("### Kondisi Sekarang\n\n"
                    "1. **Kasir** mencatat penjualan di layar kasir `src/kasir.go:2`\n"
                    "2. **Pemilik Warung** menyalin penjualan ke buku tulis\n\n"
                    "### Kondisi Target\n\n" + STEPS),
}
RULE = {
    "NEW_PRODUCT": "- **BR-1**: Pengeluaran di atas Rp1.000.000 wajib disertai foto nota — pengecualian: tidak ada",
    "IMPROVEMENT": "- **BR-1** [BARU]: Pengeluaran di atas Rp1.000.000 wajib disertai foto nota — pengecualian: "
                   "tidak ada",
}
RULE["NEW_FEATURE"] = RULE["NEW_PRODUCT"]


def card(mode: str) -> str:
    return f"""## Purpose

Pemilik warung makan tidak tahu laba harian karena kas dicatat di buku tulis dan sering tidak lengkap.

## Actors

{ACTORS[mode]}

## Business Process

{PROCESS[mode]}

## Business Rules

{RULE[mode]}

## Success Criteria

- **SC-1**: Pemilik melihat laba harian tanpa menghitung manual — ukuran: ≤ 1 menit sesudah toko tutup, selama 2 minggu pertama

## Scope

### Termasuk

- **S1**: Pencatatan penjualan oleh kasir
- **S2**: Pencatatan pengeluaran beserta foto nota
- **S3**: Laporan laba harian

### Tidak Termasuk

- Pengelolaan stok bahan — belum dibutuhkan pada versi pertama

"""


def charter(root: Path, *args: str, stdin: str = ""):
    return run_script(CHARTER, *args, cwd=root, stdin=stdin)


def validate(root: Path, kind: str, td: str = TD):
    return run_script(VALIDATE, "--kind", kind, "--charterdir", td, cwd=root)


def path_of(root: Path, td: str = TD) -> Path:
    return root / td / "CHARTER.md"


def edit(root: Path, old: str, new: str, td: str = TD, count: int = 1) -> None:
    p = path_of(root, td)
    text = p.read_text(encoding="utf-8")
    assert old in text, old
    p.write_text(text.replace(old, new, count), encoding="utf-8")


def resolved(out: str) -> Dict[str, str]:
    line = next(l for l in out.splitlines() if l.startswith("Terselesaikan: "))
    return dict(kv.split("=", 1) for kv in line[len("Terselesaikan: "):].split("; "))


def review_block(verdict: str, sidik: str, rnd: int = 1, blockers: int = 0) -> str:
    items = "\n".join(f"- [SEMANTIK] `CHARTER.md:{10 + i}` (fokus #1) — cacat — akibat" for i in range(blockers))
    return (f"## Charter Review\n- Verdict: {verdict}\n- Sidik: {sidik}\n- Ronde: {rnd}\n"
            f"- BLOCKER: 0 [MEKANIS] · {blockers} [SEMANTIK]\n\n**BLOCKER:**\n{items or '- —'}\n\n"
            f"**ADVISORY:**\n- —\n")


class Workspace:
    """Ruang kerja sementara beserta pembantu siklus hidup satu charter."""

    def __init__(self, root: Path, mode: str):
        self.root = root
        self.mode = mode

    def new(self, slug: str = SLUG, request: str = "saya ingin membuat aplikasi keuangan untuk UMKM",
            extra: tuple = ()):
        untuk, masalah, lingkup = CONTEXT[self.mode]
        return charter(self.root, "new", "--slug", slug, "--mode", self.mode, "--untuk", untuk, "--masalah",
                       masalah, "--lingkup", lingkup, "--requester", "Budi (PO)", "--title",
                       "Pencatatan keuangan UMKM", "--request", "-", *extra, stdin=request)

    def answer(self, td: str = TD) -> None:
        """Isi keenam pilar dan log seperti hasil product:discover."""
        p = path_of(self.root, td)
        text = p.read_text(encoding="utf-8")
        text = re.sub(r"### Fakta\n.*?(?=### Pertanyaan Terbuka)", FACTS + "\n", text, flags=re.S)
        p.write_text(text, encoding="utf-8")

    def write_card(self, td: str = TD) -> None:
        edit(self.root, "## Catatan Elisitasi", card(self.mode) + "## Catatan Elisitasi", td)

    def sidik(self, td: str = TD) -> str:
        proc = charter(self.root, "check", "--gate", "spec", "--charterdir", td)
        return resolved(proc.stdout)["sidik"]

    def review(self, verdict: str = "PASS", td: str = TD, sidik: Optional[str] = None, rnd: int = 1,
               blockers: int = 0):
        block = review_block(verdict, sidik or self.sidik(td), rnd, blockers)
        return charter(self.root, "review", "--charterdir", td, "--verdict", verdict, "--report", "-", stdin=block)

    def to_closed(self) -> None:
        assert self.new().returncode == 0
        self.answer()
        proc = charter(self.root, "close", "--charterdir", TD)
        assert proc.returncode == 0, proc.stdout

    def to_reviewed(self) -> None:
        self.to_closed()
        self.write_card()
        proc = self.review()
        assert proc.returncode == 0, proc.stdout

    def to_approved(self) -> None:
        self.to_reviewed()
        proc = charter(self.root, "approve", "--charterdir", TD, "--answer", "Setujui")
        assert proc.returncode == 0, proc.stdout


def _seed(root: Path, mode: str) -> None:
    if mode != "NEW_PRODUCT":
        (root / "src").mkdir()
        (root / "src" / "kasir.go").write_text("package kasir\n\nfunc Catat() {}\n", encoding="utf-8")


@pytest.fixture(params=["NEW_PRODUCT", "NEW_FEATURE", "IMPROVEMENT"])
def ws(request, tmp_path) -> Workspace:
    """Ruang kerja git ber-commit untuk tiap mode; mode codebase berisi satu berkas sumber."""
    root = tmp_path / "repo"
    root.mkdir()
    _seed(root, request.param)
    git(root, "init", "-q", "-b", "main")
    (root / "README.txt").write_text("fixture\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "chore: init")
    return Workspace(root, request.param)


@pytest.fixture
def empty_ws(tmp_path) -> Workspace:
    """Folder kosong tanpa git — tempat inisiasi produk baru."""
    root = tmp_path / "kosong"
    root.mkdir()
    return Workspace(root, "NEW_PRODUCT")
