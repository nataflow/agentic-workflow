"""Langkah 19 — batch intake analyst (B1–B4).

Beberapa tujuan dalam satu pesan dialokasikan sekaligus oleh `ticket.py new --urutan <k>/<N> [--batch <id>]`. Urutan
batch disimpan di frontmatter (`batch`, `urutan`) sebagai field pembukuan, di luar sidik isi dan segel, sehingga
`state` dapat melanjutkan batch dari tiket terbuka berurutan terkecil tanpa menyentuh rantai persetujuan.
"""
import json
import shutil
from pathlib import Path

import pytest

from conftest import PLUGINS, git, load_module, run_script, ticket_review

ANALYST = PLUGINS / "analyst"
COMMON = ANALYST / "skills" / "_common"
TICKET = COMMON / "ticket.py"
VALIDATE = COMMON / "validate_doc.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
TDIR = "analyst/tickets/2609231400-cicilan"
BATCH_FM = "batch: 2609231400-cicilan\nurutan: 1/2\n"
lib = load_module(COMMON / "analyst_lib.py", "analyst_lib_19")


class Run:
    def __init__(self, proc):
        self.code, self.out = proc.returncode, proc.stdout + proc.stderr


def tk(root, *args, stdin=""):
    return Run(run_script(TICKET, *args, cwd=root, stdin=stdin))


def new(root, slug, *extra, ticket_type="FEATURE", request="Tolong catat permintaan ini."):
    return tk(root, "new", "--slug", slug, "--type", ticket_type, "--requester", "Rina", "--request", "-", *extra,
              stdin=request)


def tickets(root):
    base = root / "analyst" / "tickets"
    return sorted(p.name for p in base.iterdir()) if base.is_dir() else []


def fm_of(root, name):
    return lib.split_frontmatter((root / "analyst" / "tickets" / name / "TICKET.md").read_text(encoding="utf-8"))[0]


def state(root, *args):
    return json.loads(tk(root, "state", "--json", *args).out)["ticketdirs"]


def frontmatter_check(root, tdir=TDIR, kind="elicit"):
    r = run_script(VALIDATE, "--kind", kind, "--ticketdir", tdir, "--json", cwd=root)
    return {c["id"]: c for c in json.loads(r.stdout)["checks"]}[1]


def with_fm(lines, text=None):
    text = text or FIXTURE.read_text(encoding="utf-8")
    return text.replace("elicit_log: 1\n", f"elicit_log: 1\n{lines}", 1)


@pytest.fixture
def plain(make_repo):
    return make_repo(name="plain", git_init=False)


@pytest.fixture
def batch3(plain):
    """Batch tiga tiket; slug sengaja tidak urut abjad supaya urutan batch berbeda dari urutan nama."""
    assert new(plain, "zeta", "--urutan", "1/3").code == 0
    head = tickets(plain)[0]
    assert new(plain, "alpha", "--urutan", "2/3", "--batch", head).code == 0
    assert new(plain, "beta", "--urutan", "3/3", "--batch", head, ticket_type="BUG").code == 0
    return plain, head


# --- B1: new ------------------------------------------------------------------------------------

@pytest.mark.regression("19 B1")
def test_b1_urutan_1_menulis_batch_nama_ticketdir_sendiri(plain):
    r = new(plain, "cicilan", "--urutan", "1/3")
    assert r.code == 0, r.out
    head = tickets(plain)[0]
    assert f"batch={head} urutan=1/3" in r.out
    fm = fm_of(plain, head)
    assert fm["batch"] == head and fm["urutan"] == "1/3"
    lines = (plain / "analyst/tickets" / head / "TICKET.md").read_text(encoding="utf-8").splitlines()
    assert lines[lines.index(f"request_hash: {fm['request_hash']}") + 1:][:3] == [f"batch: {head}", "urutan: 1/3",
                                                                                   "---"]


@pytest.mark.regression("19 B1")
def test_b1_anggota_batch_merujuk_tiket_urutan_1(batch3):
    root, head = batch3
    for name in tickets(root):
        assert fm_of(root, name)["batch"] == head
    assert {fm_of(root, n)["urutan"] for n in tickets(root)} == {"1/3", "2/3", "3/3"}


@pytest.mark.regression("19 B1")
@pytest.mark.parametrize("extra,needle", [
    (("--urutan", "1/6"), "2 ≤ N ≤ 5"),
    (("--urutan", "1/1"), "2 ≤ N ≤ 5"),
    (("--urutan", "4/3"), "1 ≤ k ≤ N"),
    (("--urutan", "dua"), "bukan <k>/<N>"),
    (("--batch", "HEAD"), "--batch tanpa --urutan"),
    (("--urutan", "1/3", "--batch", "HEAD"), "--batch dilarang untuk urutan 1"),
    (("--urutan", "3/3"), "wajib `--batch <id>`"),
    (("--urutan", "3/3", "--batch", "2601010000-tidak-ada"), "tidak dikenal"),
    (("--urutan", "3/4", "--batch", "HEAD"), "bukan tiket urutan 1/4"),
    (("--urutan", "2/3", "--batch", "HEAD"), "sudah dipakai"),
])
def test_b1_alokasi_batch_tidak_sah_ditolak_tanpa_menulis(plain, extra, needle):
    assert new(plain, "zeta", "--urutan", "1/3").code == 0
    head = tickets(plain)[0]
    assert new(plain, "alpha", "--urutan", "2/3", "--batch", head).code == 0
    before = tickets(plain)
    r = new(plain, "gamma", *[head if a == "HEAD" else a for a in extra])
    assert r.code == 1 and "NEW FAIL" in r.out and needle in r.out, r.out
    assert tickets(plain) == before


@pytest.mark.regression("19 B1")
def test_b1_ticketdir_kosong_dipakai_ulang_tetap_bertanda_batch(plain):
    kosong = plain / "analyst/tickets/2609231600-cicilan"
    kosong.mkdir(parents=True)
    r = new(plain, "cicilan", "--urutan", "1/2")
    assert r.code == 0 and "KOSONG dipakai ulang" in r.out
    assert fm_of(plain, "2609231600-cicilan")["batch"] == "2609231600-cicilan"


@pytest.mark.regression("19 B1")
def test_b1_field_batch_di_luar_sidik_dan_segel():
    plain_text = FIXTURE.read_text(encoding="utf-8")
    batch_text = with_fm(BATCH_FM)
    assert batch_text != plain_text
    for part in ("card", "elicit", "all"):
        assert lib.content_hash(batch_text, part) == lib.content_hash(plain_text, part)
    assert lib.ticket_seal(batch_text) == lib.ticket_seal(plain_text)


@pytest.mark.regression("19 B1")
def test_b1_tiket_batch_melewati_review_dan_approve(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": with_fm(BATCH_FM)})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture batch")
    assert ticket_review(root, TDIR, "PASS").returncode == 0
    r = tk(root, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    assert r.code == 0, r.out
    assert [(row["state"], row["batch"]) for row in state(root, "--all")] == [("READY", "2609231400-cicilan")]


# --- B2: state ----------------------------------------------------------------------------------

@pytest.mark.regression("19 B2")
def test_b2_state_mengurutkan_batch_menurut_urutan(batch3):
    root, head = batch3
    assert new(root, "aaa").code == 0                                   # tiket tunggal, nama paling awal
    rows = state(root)
    assert [r["ticketdir"].split("-", 1)[1] for r in rows] == ["aaa", "zeta", "alpha", "beta"]
    assert [r["urutan"] for r in rows] == ["-", "1/3", "2/3", "3/3"]
    assert rows[0]["batch"] == "-" and {r["batch"] for r in rows[1:]} == {head}
    text = tk(root, "state").out
    assert f"· batch {head} 2/3" in text and "Aaa\n" in text


@pytest.mark.regression("19 B2")
def test_b2_state_batch_menyaring_satu_batch_semua_keadaan(batch3):
    root, head = batch3
    assert new(root, "lain", "--urutan", "1/2").code == 0
    beta = next(n for n in tickets(root) if n.endswith("-beta"))
    assert tk(root, "cancel", "--ticketdir", f"analyst/tickets/{beta}", "--reason", "tidak jadi").code == 0
    rows = state(root, "--batch", head)
    assert [(r["urutan"], r["state"]) for r in rows] == [("1/3", "ELISITASI"), ("2/3", "ELISITASI"),
                                                         ("3/3", "DIBATALKAN")]
    assert "beta" not in json.dumps(state(root))                         # tanpa --batch: DIBATALKAN tetap tersaring
    assert "nihil ticketdir di batch 2601010000-x" in tk(root, "state", "--batch", "2601010000-x").out


# --- B3: validator ------------------------------------------------------------------------------

@pytest.mark.regression("19 B3")
@pytest.mark.parametrize("lines,needle", [
    ("batch: 2609231400-cicilan\n", "berpasangan"),
    ("urutan: 1/2\n", "berpasangan"),
    ("batch: 2609231400-cicilan\nurutan: 7/3\n", "bukan <k>/<N>"),
    ("batch: cicilan\nurutan: 2/3\n", "bukan nama ticketdir"),
    ("batch: 2609231300-lain\nurutan: 1/3\n", "nama ticketdir sendiri"),
])
def test_b3_field_batch_rusak_gagal_frontmatter(make_repo, lines, needle):
    root = make_repo({f"{TDIR}/TICKET.md": with_fm(lines)}, git_init=False)
    for kind in ("elicit", "ticket"):
        c = frontmatter_check(root, kind=kind)
        assert c["status"] == "FAIL" and needle in c["summary"], (kind, c)


@pytest.mark.regression("19 B3")
@pytest.mark.parametrize("lines", ["", BATCH_FM, "batch: 2609231300-lain\nurutan: 2/3\n"])
def test_b3_field_batch_sah_atau_absen_lolos(make_repo, lines):
    root = make_repo({f"{TDIR}/TICKET.md": with_fm(lines)}, git_init=False)
    for kind in ("elicit", "ticket"):
        assert frontmatter_check(root, kind=kind)["status"] == "PASS"
