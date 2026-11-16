"""Langkah 38 — friksi lapangan analyst: sidik tahan format (N1), segel ulang (N2), ticketdir dari cwd (V1),
ekor batch (B1).

Formatter yang memicu DRIFT palsu di lapangan adalah prettier (`yarn run format` atas seluruh repo frontend).
CI tidak punya Node, jadi perubahannya ditiru `conftest.prettier_like`.
"""
import json
from pathlib import Path

import pytest

from conftest import PLUGINS, git, load_module, prettier_like, run_script, ticket_review

COMMON = PLUGINS / "analyst" / "skills" / "_common"
TICKET = COMMON / "ticket.py"
VALIDATE = COMMON / "validate_doc.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
lib = load_module(COMMON / "analyst_lib.py", "analyst_lib_38")


class Run:
    def __init__(self, proc):
        self.code, self.out = proc.returncode, proc.stdout + proc.stderr


def tk(root, *args, cwd=None):
    return Run(run_script(TICKET, *args, cwd=cwd or root))


def path(root):
    return root / TDIR / "TICKET.md"


def state(root):
    r = run_script(TICKET, "state", "--all", "--json", cwd=root)
    return {row["ticketdir"]: row for row in json.loads(r.stdout)["ticketdirs"]}


def failed(root, kind):
    r = run_script(VALIDATE, "--kind", kind, "--ticketdir", TDIR, "--json", cwd=root)
    return {c["id"]: c["summary"] for c in json.loads(r.stdout)["checks"] if c["status"] == "FAIL"}


def fm_of(root):
    return lib.split_frontmatter(path(root).read_text(encoding="utf-8"))[0]


def set_fields(root, **fields):
    p = path(root)
    text = p.read_text(encoding="utf-8")
    for k, v in fields.items():
        text = lib.set_frontmatter_field(text, k, v)
    p.write_text(text, encoding="utf-8")


def reformat(root):
    p = path(root)
    before = p.read_text(encoding="utf-8")
    p.write_text(prettier_like(before), encoding="utf-8")
    assert p.read_text(encoding="utf-8") != before


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    return root


@pytest.fixture
def ready(repo):
    assert ticket_review(repo, TDIR, "PASS").returncode == 0
    r = tk(repo, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    assert r.code == 0, r.out
    return repo


def legacy_ready(root):
    """Tiket READY seperti ditulis analyst ≤ 0.19.1: sidik lama, tanpa `approved_seal_norm`."""
    text = path(root).read_text(encoding="utf-8")
    set_fields(root, approved_hash=lib.content_hash_legacy(text), approved_seal=lib.ticket_seal(text))
    p = path(root)
    lines = p.read_text(encoding="utf-8").split("\n")
    p.write_text("\n".join(l for l in lines if not l.startswith("approved_seal_norm:")), encoding="utf-8")
    assert "approved_seal_norm" not in fm_of(root)


# --- N1: sidik tahan format -------------------------------------------------------------------------

@pytest.mark.regression("38 N1")
def test_n1_norm_md_menyamakan_format_dan_tetap_peka_isi():
    a = "# Judul\nIsi *miring* dan  dua spasi.\n| # | A |\n|---|---|\n| 1 | x |\n> baris 1\n> baris 2\n* butir\n"
    b = "# Judul\n\nIsi _miring_ dan dua spasi.\n\n| #   | A   |\n| --- | --- |\n| 1   | x   |\n\n> baris 1\n>\n> baris 2\n\n- butir\n"
    assert lib.norm_md(a) == lib.norm_md(b)
    assert lib.norm_md(a) != lib.norm_md(a.replace("| 1 | x |", "| 1 | y |"))
    assert lib.norm_md(a) != lib.norm_md(a.replace("dua spasi", "tiga spasi"))


@pytest.mark.regression("38 N1")
def test_n1_approve_menulis_segel_tahan_format(ready):
    fm = fm_of(ready)
    text = path(ready).read_text(encoding="utf-8")
    assert fm["approved_hash"] == lib.content_hash(text)
    assert fm["approved_seal"] == lib.ticket_seal(text)
    assert fm["approved_seal_norm"] == lib.ticket_seal_norm(text)


@pytest.mark.regression("38 N1")
def test_n1_tiket_ready_yang_diformat_tetap_ready(ready):
    reformat(ready)
    assert state(ready)[TDIR]["state"] == "READY"
    assert failed(ready, "ticket") == {}
    assert failed(ready, "elicit") == {}


@pytest.mark.regression("38 N1")
def test_n1_suntingan_isi_sesudah_format_tetap_drift(ready):
    reformat(ready)
    p = path(ready)
    p.write_text(p.read_text(encoding="utf-8").replace("50.000.000", "10.000.000", 1), encoding="utf-8")
    assert state(ready)[TDIR]["state"] == "DRIFT"
    assert 11 in failed(ready, "ticket")


@pytest.mark.regression("38 N1")
def test_n1_tiket_lama_tetap_ready_tanpa_format_dan_drift_bila_diformat(ready):
    legacy_ready(ready)
    assert state(ready)[TDIR]["state"] == "READY"
    assert failed(ready, "ticket") == {}
    reformat(ready)        # batasan yang diterima: teks yang disetujui tidak tersimpan, jadi tidak dapat dibuktikan
    assert state(ready)[TDIR]["state"] == "DRIFT"


@pytest.mark.regression("38 N1")
def test_n1_draft_bersidik_review_lama_tetap_dapat_disetujui(repo):
    assert ticket_review(repo, TDIR, "PASS").returncode == 0
    text = path(repo).read_text(encoding="utf-8")
    legacy = f"{lib.content_hash_legacy(text, 'card')}/{lib.content_hash_legacy(text, 'elicit')}"
    set_fields(repo, review=f"PASS @{legacy}", elicit_hash=lib.content_hash_legacy(text, "elicit"))
    r = tk(repo, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    assert r.code == 0, r.out


@pytest.mark.regression("38 N1")
def test_n1_permintaan_asli_diformat_bukan_perubahan():
    text = FIXTURE.read_text(encoding="utf-8")
    quote = next(l for l in text.splitlines() if l.startswith("> "))
    multi = text.replace(quote, quote + "\n> baris kedua dengan *penekanan*", 1)
    sealed = lib.request_digest(multi)
    formatted = multi.replace(quote + "\n> baris", quote + "\n>\n> baris", 1).replace("*penekanan*", "_penekanan_")
    assert lib.request_digest(formatted) == sealed
    assert lib.request_digest(multi.replace("baris kedua", "baris ketiga")) != sealed


# --- N2: `reseal` -------------------------------------------------------------------------------------

@pytest.mark.regression("38 N2")
def test_n2_reseal_tiket_lama_lalu_tahan_format(ready):
    legacy_ready(ready)
    body = path(ready).read_text(encoding="utf-8").split("\n---\n", 1)[1]
    r = tk(ready, "reseal", "--all")
    assert r.code == 0 and "1 disegel ulang" in r.out and "commit" in r.out, r.out
    text = path(ready).read_text(encoding="utf-8")
    assert text.split("\n---\n", 1)[1] == body                      # isi tidak berubah
    fm = fm_of(ready)
    assert fm["approved_hash"] == lib.content_hash(text) and fm["approved_seal_norm"] == lib.ticket_seal_norm(text)
    assert "segel ulang cicilan" in git(ready, "log", "-1", "--format=%s")
    reformat(ready)
    assert state(ready)[TDIR]["state"] == "READY"


@pytest.mark.regression("38 N2")
def test_n2_reseal_idempoten(ready):
    assert tk(ready, "reseal", "--all").code == 0          # fixture: `elicit_hash` masih sidik lama
    head = git(ready, "rev-parse", "HEAD")
    r = tk(ready, "reseal", "--ticketdir", TDIR)
    assert r.code == 0 and "0 disegel ulang · 1 sudah tahan format" in r.out, r.out
    assert git(ready, "rev-parse", "HEAD") == head


@pytest.mark.regression("38 N2")
def test_n2_reseal_tiket_terbuka_menaikkan_sidik_permintaan_dan_elisitasi(repo):
    p = path(repo)
    text = p.read_text(encoding="utf-8")
    quote = next(l for l in text.splitlines() if l.startswith("> "))
    text = text.replace(quote, quote + "\n> baris kedua permintaan", 1)
    text = lib.set_frontmatter_field(text, "request_hash", lib.request_digest_legacy(text))
    text = lib.set_frontmatter_field(text, "elicit_hash", lib.content_hash_legacy(text, "elicit"))
    p.write_text(text, encoding="utf-8")
    assert failed(repo, "elicit") == {}
    r = tk(repo, "reseal", "--ticketdir", TDIR)
    assert r.code == 0 and "1 disegel ulang" in r.out, r.out
    fm = fm_of(repo)
    assert fm["request_hash"] == lib.request_digest(text) and fm["elicit_hash"] == lib.content_hash(text, "elicit")
    assert "approved_seal_norm" not in fm                          # bukan READY: segel persetujuan tidak ditulis
    reformat(repo)
    assert failed(repo, "elicit") == {}
    r = tk(repo, "check", "--gate", "spec", "--ticketdir", TDIR)
    assert r.code == 0, r.out


@pytest.mark.regression("38 N2")
def test_n2_reseal_tidak_menyentuh_drift(ready):
    legacy_ready(ready)
    reformat(ready)
    before = path(ready).read_text(encoding="utf-8")
    r = tk(ready, "reseal", "--all")
    assert r.code == 0 and "DRIFT 1" in r.out and "analyst:spec REVISE" in r.out and TDIR in r.out, r.out
    assert path(ready).read_text(encoding="utf-8") == before
    r = tk(ready, "reseal", "--ticketdir", TDIR)
    assert r.code == 1 and "DRIFT" in r.out, r.out


@pytest.mark.regression("38 N2")
def test_n2_reseal_menolak_tanpa_atau_dengan_dua_sasaran(ready):
    assert tk(ready, "reseal").code == 1
    assert tk(ready, "reseal", "--all", "--ticketdir", TDIR).code == 1


# --- V1: ticketdir dari cwd ---------------------------------------------------------------------------

@pytest.mark.regression("38 V1")
@pytest.mark.parametrize("arg", [".", "./", "../2609231400-cicilan"])
def test_v1_ticketdir_relatif_dari_dalam_ticketdir(repo, arg):
    inside = repo / TDIR
    r = run_script(VALIDATE, "--kind", "elicit", "--ticketdir", arg, cwd=inside)
    assert r.returncode == 0 and "Letak ticketdir" not in r.stdout, r.stdout
    r = tk(repo, "check", "--gate", "spec", "--ticketdir", arg, cwd=inside)
    assert r.code == 0 and TDIR in r.out, r.out


@pytest.mark.regression("38 V1")
def test_v1_di_luar_git_root_naik_dari_ticketdir(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")}, name="tanpa-git", git_init=False)
    inside = root / TDIR
    r = run_script(TICKET, "state", "--json", cwd=inside)
    assert json.loads(r.stdout)["root"] == str(root.resolve()), r.stdout
    r = tk(root, "check", "--gate", "spec", "--ticketdir", ".", cwd=inside)
    assert r.code == 0 and f"root={root.resolve()}" in r.out, r.out


@pytest.mark.regression("38 V1")
def test_v1_path_root_relatif_tetap_dibaca_terhadap_root(repo):
    sub = repo / "analyst"
    r = run_script(VALIDATE, "--kind", "elicit", "--ticketdir", TDIR, cwd=sub)
    assert r.returncode == 0, r.stdout
    r = run_script(VALIDATE, "--kind", "elicit", "--ticketdir", "bukan/ticketdir", cwd=repo)
    assert r.returncode == 1 and "Letak ticketdir" in r.stdout


# --- B1: ekor batch -----------------------------------------------------------------------------------

@pytest.mark.regression("38 B1")
def test_b1_elisitasi_tanpa_log_bertanda_belum_disentuh(make_repo):
    root = make_repo(name="batch")
    for k in (1, 2):
        args = ["new", "--slug", f"tujuan-{k}", "--type", "FEATURE", "--requester", "Rina", "--request",
                f"Tujuan {k}.", "--urutan", f"{k}/2"]
        if k == 2:
            args += ["--batch", batch]
        r = tk(root, *args)
        assert r.code == 0, r.out
        if k == 1:
            batch = r.out.split("batch=")[1].split()[0]
    rows = {Path(rel).name.split("-", 1)[1]: row for rel, row in state(root).items()}
    assert rows["tujuan-1"]["state"] == rows["tujuan-2"]["state"] == "ELISITASI"
    assert "belum disentuh sejak" in rows["tujuan-2"]["route"] and "keputusan user" in rows["tujuan-2"]["route"]


@pytest.mark.regression("38 B1")
def test_b1_elisitasi_berlog_tetap_rute_lama(repo):
    p = path(repo)
    p.write_text(lib.set_frontmatter_field(p.read_text(encoding="utf-8"), "elicitation", "OPEN"), encoding="utf-8")
    row = state(repo)[TDIR]
    assert row["state"] == "ELISITASI" and row["route"] == "analyst:elicit (lanjutkan pertanyaan terbuka)"
