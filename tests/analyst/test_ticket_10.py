"""Regresi Langkah 10 (G1–G9) — skenario = probe issues/10-robustness-analyst.md.

Fixture `fixtures/ticket_valid.md` = TICKET.md DRAFT sah: elisitasi CLOSED dan tersegel, kartu lolos kedua
validator, belum direview.
"""
import json
from pathlib import Path

import pytest

from conftest import PLUGINS, git, load_module, run_script, ticket_review

COMMON = PLUGINS / "analyst" / "skills" / "_common"
TICKET = COMMON / "ticket.py"
VALIDATE = COMMON / "validate_doc.py"
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
lib = load_module(COMMON / "analyst_lib.py", "analyst_lib_10")
be_lib = load_module(PLUGINS / "backend/skills/_common/precondition_lib.py", "be_precondition_lib_10")
LOG_ROW_1 = "| 1 | 2026-09-23 | Invoice mana yang boleh dicicil? | Di atas 50 juta | Rina |"


class Run:
    def __init__(self, proc):
        self.code, self.out = proc.returncode, proc.stdout + proc.stderr
        self.traceback = "Traceback" in proc.stderr


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8")})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    return root


@pytest.fixture
def plain(make_repo):
    return make_repo(name="plain", git_init=False)


def tk(root, *args, stdin=""):
    return Run(run_script(TICKET, *args, cwd=root, stdin=stdin))


def vd(root, kind, ticketdir=TDIR):
    return Run(run_script(VALIDATE, "--kind", kind, "--ticketdir", ticketdir, cwd=root))


def text(root, ticketdir=TDIR):
    return (root / ticketdir / "TICKET.md").read_text(encoding="utf-8")


def edit(root, old, new, count=1):
    p = root / TDIR / "TICKET.md"
    body = p.read_text(encoding="utf-8")
    assert old in body, old
    p.write_text(body.replace(old, new, count), encoding="utf-8")


def check(root):
    return json.loads(run_script(TICKET, "check", "--gate", "spec", "--ticketdir", TDIR, "--json", cwd=root).stdout)


def approve(root, *extra):
    assert ticket_review(root, TDIR, "PASS").returncode == 0
    return tk(root, "approve", "--ticketdir", TDIR, "--answer", "Setujui", *extra)


def block(root, verdict, *, counts=(0, 0), items=(), ronde=None):
    c = check(root)
    bullets = "\n".join(f"- [SEMANTIK] `TICKET.md:{28 + i}` (fokus #1) — {t} — QA menebak"
                        for i, t in enumerate(items)) or "- —"
    return (f"## Ticket Review\n- Verdict: {verdict}\n- Sidik: {c['sidik']}\n- Ronde: {ronde or c['ronde']}\n"
            f"- BLOCKER: {counts[0]} [MEKANIS] · {counts[1]} [SEMANTIK]\n\n**BLOCKER:**\n{bullets}\n\n"
            f"**ADVISORY:**\n- —\n")


def review_with(root, verdict, report):
    return tk(root, "review", "--ticketdir", TDIR, "--verdict", verdict, "--report", "-", stdin=report)


def reopen_elicit(root, reason="batas wilayah"):
    edit(root, "elicitation: CLOSED", "elicitation: OPEN")
    edit(root, LOG_ROW_1, LOG_ROW_1 + f"\n| 2 | 2026-09-27 | Dibuka ulang | {reason} | analyst:spec |")


# --- G1 ------------------------------------------------------------------------------------------

@pytest.mark.regression("G1")
def test_g1_ref_menolak_drift_dan_tidak_meng_commit(repo):
    assert approve(repo).code == 0
    head = git(repo, "rev-parse", "HEAD").strip()
    edit(repo, "minimal Rp 50.000.000.", "minimal Rp 10.000.000.")
    r = tk(repo, "ref", "--ticketdir", TDIR, "--ref", "FIN-7")
    assert r.code == 1 and "DRIFT" in r.out
    assert git(repo, "rev-parse", "HEAD").strip() == head and 'external_ref: "FIN-7"' not in text(repo)


@pytest.mark.regression("G1")
def test_g1_tiket_lama_tanpa_segel_tidak_tercuci_ref(repo):
    """Probe G1: tiket tanpa `approved_seal` + suntingan + `ref` → dulu PASS di penerima backend."""
    assert approve(repo).code == 0
    edit(repo, f"approved_seal: {lib.ticket_seal(text(repo))}", "approved_seal: -")
    git(repo, "commit", "-qam", "docs(ticket): kunci TICKET cicilan READY")
    edit(repo, "minimal Rp 50.000.000.", "minimal Rp 10.000.000.")
    assert tk(repo, "ref", "--ticketdir", TDIR, "--ref", "FIN-7").code == 1
    status, summary, _ = be_lib.ticket_source_verdict(repo, f"{TDIR}/TICKET.md")
    assert status == "FAIL" and "DRIFT" in summary


@pytest.mark.regression("G1")
def test_g1_ref_pada_draft_tidak_meng_commit(repo):
    edit(repo, "hanya mengenal status Belum Bayar", "baru mengenal status Belum Bayar")  # draft belum di-commit
    head = git(repo, "rev-parse", "HEAD").strip()
    r = tk(repo, "ref", "--ticketdir", TDIR, "--ref", "FIN-8")
    assert r.code == 0 and "tanpa commit" in r.out
    assert git(repo, "rev-parse", "HEAD").strip() == head and 'external_ref: "FIN-8"' in text(repo)


# --- G2 ------------------------------------------------------------------------------------------

@pytest.mark.regression("G2")
def test_g2_catatan_disunting_sesudah_close_menahan_spec_review_approve(repo):
    edit(repo, "#### Aktor\n", "#### Aktor\n\n")                  # satu baris kosong di catatan
    c = {x["id"]: x for x in check(repo)["checks"]}
    assert c[5]["status"] == "FAIL" and "berubah sesudah ditutup" in c[5]["summary"]
    r = ticket_review(repo, TDIR, "PASS")
    assert r.returncode == 1 and "berubah sesudah ditutup" in r.stdout
    edit(repo, "#### Aktor\n\n", "#### Aktor\n")
    assert approve(repo).code == 0


@pytest.mark.regression("G2")
def test_g2_plafon_ronde_tidak_reset_oleh_suntingan_catatan(repo):
    for _ in range(2):
        assert ticket_review(repo, TDIR, "BLOCKED").returncode == 0
    edit(repo, "#### Aktor\n", "#### Aktor\n\n")
    r = ticket_review(repo, TDIR, "PASS")
    assert r.returncode == 1 and "ronde 1/2" not in r.stdout


@pytest.mark.regression("G2")
def test_g2_close_menutup_menyegel_dan_meng_commit(repo):
    edit(repo, "elicitation: CLOSED", "elicitation: OPEN")
    r = tk(repo, "close", "--ticketdir", TDIR)
    assert r.code == 0 and "elicitation CLOSED" in r.out
    fm, _ = lib.split_frontmatter(text(repo))
    assert fm["elicitation"] == "CLOSED" and fm["elicit_hash"] == lib.content_hash(text(repo), "elicit")
    assert fm["elicit_log"] == "1"
    assert "tanpa perubahan" in r.out                                 # identik dengan fixture ter-commit
    reopen_elicit(repo)
    r = tk(repo, "close", "--ticketdir", TDIR)
    assert r.code == 0 and git(repo, "log", "-1", "--format=%s").strip() == "docs(ticket): elisitasi cicilan"
    assert not git(repo, "status", "--porcelain").strip()
    assert tk(repo, "close", "--ticketdir", TDIR).code == 0          # idempoten: tertutup dan cocok


@pytest.mark.regression("G2")
def test_g2_close_gagal_validator_mengembalikan_berkas(repo):
    reopen_elicit(repo)
    edit(repo, "Tinggi — dua klien besar menunggu.", "_(belum terjawab)_")
    before = text(repo)
    r = tk(repo, "close", "--ticketdir", TDIR)
    assert r.code == 1 and "CLOSED dengan pilar belum terjawab" in r.out
    assert text(repo) == before


@pytest.mark.regression("G2")
def test_g2_tutup_ulang_menuntut_baris_dibuka_ulang(repo):
    edit(repo, "elicitation: CLOSED", "elicitation: OPEN")
    edit(repo, "Hanya pelanggan korporat.", "Hanya pelanggan korporat di Jabodetabek.")
    r = tk(repo, "close", "--ticketdir", TDIR, "--no-commit")
    assert r.code == 1 and "Dibuka ulang" in r.out
    edit(repo, LOG_ROW_1, LOG_ROW_1 + "\n| 2 | 2026-09-27 | Dibuka ulang | batas wilayah | analyst:spec |")
    assert tk(repo, "close", "--ticketdir", TDIR, "--no-commit").code == 0
    assert lib.split_frontmatter(text(repo))[0]["elicit_log"] == "2"


@pytest.mark.regression("G2")
def test_g2_tiket_lama_diadopsi_sekali(repo):
    edit(repo, "elicit_hash: 349039f58360\nelicit_log: 1\n", "")
    c = {x["id"]: x for x in check(repo)["checks"]}
    assert c[5]["status"] == "FAIL" and "tanpa segel" in c[5]["summary"] and "ticket.py close" in c[5]["action"]
    r = tk(repo, "close", "--ticketdir", TDIR, "--no-commit")
    assert r.code == 0 and "diadopsi" in r.out
    assert check(repo)["status"] == "PASS"


@pytest.mark.regression("G2")
def test_g2_adopsi_ditolak_bila_catatan_berubah_sesudah_review(repo):
    edit(repo, "elicit_hash: 349039f58360\nelicit_log: 1\n", "")
    body = text(repo)
    digest = f"{lib.content_hash(body, 'card')}/{lib.content_hash(body, 'elicit')}"
    edit(repo, "review: -", f"review: BLOCKED @{digest}")
    edit(repo, "Hanya pelanggan korporat.", "Hanya pelanggan korporat di Jabodetabek.")
    r = tk(repo, "close", "--ticketdir", TDIR, "--no-commit")
    assert r.code == 1 and "berubah sesudah review terakhir" in r.out


# --- G3 ------------------------------------------------------------------------------------------

@pytest.mark.regression("G3")
def test_g3_pass_dengan_blocker_ditolak(repo):
    """Probe G3: dulu tercatat PASS lalu `approve` READY."""
    report = block(repo, "PASS", counts=(0, 2), items=("then tidak teramati", "aturan rekaan"))
    r = review_with(repo, "PASS", report)
    assert r.code == 1 and "Verdict PASS dengan 2 BLOCKER" in r.out
    r = tk(repo, "approve", "--ticketdir", TDIR, "--answer", "ok", "--no-commit")
    assert r.code == 1 and "status: DRAFT" in text(repo)


@pytest.mark.regression("G3")
@pytest.mark.parametrize("verdict, counts, items, needle", [
    ("BLOCKED", (0, 2), ("then tidak teramati",), "hitungan BLOCKER 2 ≠ 1 butir"),
    ("BLOCKED", (0, 0), (), "BLOCKED tanpa satu BLOCKER"),
    ("PASS", (1, 0), (), "Verdict PASS dengan 1 BLOCKER"),
])
def test_g3_blok_tidak_konsisten_ditolak(repo, verdict, counts, items, needle):
    r = review_with(repo, verdict, block(repo, verdict, counts=counts, items=items))
    assert r.code == 1 and needle in r.out
    assert "review: -" in text(repo)


@pytest.mark.regression("G3")
def test_g3_tanpa_baris_hitungan_ditolak(repo):
    report = block(repo, "PASS").replace("- BLOCKER: 0 [MEKANIS] · 0 [SEMANTIK]\n", "")
    r = review_with(repo, "PASS", report)
    assert r.code == 1 and "tanpa baris `- BLOCKER:" in r.out


@pytest.mark.regression("G3")
def test_g3_ronde_dicocokkan_dengan_check(repo):
    assert check(repo)["ronde"] == "1"
    r = review_with(repo, "PASS", block(repo, "PASS", ronde="2"))
    assert r.code == 1 and "ronde yang dicatat 1" in r.out
    assert review_with(repo, "BLOCKED", block(repo, "BLOCKED", counts=(0, 1), items=("x",))).code == 0
    assert check(repo)["ronde"] == "2"
    assert review_with(repo, "BLOCKED", block(repo, "BLOCKED", counts=(0, 1), items=("x",))).code == 0
    assert check(repo)["ronde"] == "habis"

