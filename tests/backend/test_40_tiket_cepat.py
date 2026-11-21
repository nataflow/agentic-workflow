"""40 T1–T5 — `backend:ticket`: tiket cepat lokal tanpa commit, segel serah terima, dan cermin nataflow.

Tiket dibuat lewat `skills/ticket/scripts/ticket.py` sungguhan (`new` → isi kartu → `approve`), jadi segel yang dibaca
`ticket_source_verdict` dan identitas task yang diturunkan `sync_payload.ticket_key` tidak bisa bergeser diam-diam dari
penulisnya.
"""
import json
import re

import pytest

from conftest import (BE_SKILLS, TD, be_checks, be_profile, commit, git, load_module, prettier_like, run_script,
                      write_files)
from nataflow_fake import FakeMCP, Nataflow, enable_sync

TICKET_PY = BE_SKILLS / "ticket" / "scripts" / "ticket.py"
PRE = "ticket/scripts/check_preconditions.py"
SP = BE_SKILLS / "_common" / "sync_payload.py"
PL = load_module(BE_SKILLS / "_common" / "precondition_lib.py", "be_precondition_lib_ticket40")
WEB = "aaaaaaaa-0000-4000-8000-000000000001"
MOBILE = "aaaaaaaa-0000-4000-8000-000000000002"

FILLED = {
    "- <isi: satu fakta kode sekarang per butir, berbukti `path:baris` relatif root repo>":
        "- Paket order didefinisikan di `src/order.go:1`; respons belum memuat `username`",
    "- <isi: perubahan yang diminta, menyebut simbol dan berkas sasaran; bukan langkah implementasi>":
        "- Tambah `username` ke respons order",
    "- **AC-1**: <isi: hasil yang bisa diverifikasi dari luar, mis. response, status, data tersimpan>":
        "- **AC-1**: GET /orders/{id} mengembalikan `data.username`\n- **AC-2**: field lain tidak berubah",
    "<isi: aditif | mengubah | menghapus | tidak ada> — <isi: siapa terdampak; catatan lintas repo bila ada>":
        "aditif — frontend DTO Order mungkin menyesuaikan",
}


def tk(repo, *args, stdin=""):
    proc = run_script(TICKET_PY, *args, "--json", cwd=repo, stdin=stdin)
    assert "Traceback" not in proc.stderr, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def new(repo, slug="tambah-username"):
    code, out = tk(repo, "new", "--slug", slug, "--title", "Tambah field username di respons order",
                   "--request", "tambah field username di response API get order")
    assert code == 0, out
    return out["ticketdir"]


def fill(repo, td, **replace):
    path = repo / td / "TICKET.md"
    text = path.read_text(encoding="utf-8")
    for old, new_ in {**FILLED, **replace}.items():
        text = text.replace(old, new_)
    path.write_text(text, encoding="utf-8")
    return path


def ready(repo, slug="tambah-username"):
    td = new(repo, slug)
    fill(repo, td)
    code, out = tk(repo, "approve", "--ticketdir", td)
    assert code == 0, out
    return td


def check7(repo, ticket):
    return be_checks(repo, "task/scripts/check_preconditions.py", "--root", str(repo), "--taskdir", TD,
                     "--lane", "DIRECT_BRIEF", "--chain", "BRIEF", "--ticket-source", ticket)[7]


def bind(repo, td, report=False):
    """`ticket_source` taskdir `TD` menunjuk tiket `td` (dokumen taskdir hanya di disk, Langkah 24)."""
    path = repo / TD / "TASK.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "status: ACTIVE\n", f"status: ACTIVE\nticket_source: {td}/TICKET.md\n"), encoding="utf-8")
    if report:
        write_files(repo, {f"{TD}/REPORT.md": "# Order fix — Report\n"})


# ── new: lokal, tidak di-commit (T2) ─────────────────────────────────────────

@pytest.mark.regression("40 T2")
def test_new_menulis_penanda_dan_tree_tetap_bersih(chain_repo):
    td = new(chain_repo)
    assert re.fullmatch(r"backenddev/tickets/\d{10}-tambah-username", td)
    assert (chain_repo / "backenddev/tickets/.gitignore").read_text(encoding="utf-8").endswith("*\n")
    assert git(chain_repo, "status", "--porcelain") == "", "tiket tidak pernah mengotori working tree"
    text = (chain_repo / td / "TICKET.md").read_text(encoding="utf-8")
    assert "kind: backend-ticket\nstatus: DRAFT\nslug: tambah-username\n" in text
    assert "> tambah field username di response API get order" in text


def test_new_menolak_slug_tidak_sah_dan_kembar_terbuka(chain_repo):
    assert tk(chain_repo, "new", "--slug", "Tambah_User", "--title", "x", "--request", "y")[0] == 1
    td = new(chain_repo)
    code, out = tk(chain_repo, "new", "--slug", "tambah-username", "--title", "x", "--request", "y")
    assert code == 1 and "masih terbuka" in out["problems"][0] and td in out["problems"][0]


def test_slug_dibatalkan_boleh_dipakai_lagi(chain_repo):
    write_files(chain_repo, {"backenddev/tickets/2601010000-tambah-username/TICKET.md":
                             "---\nkind: backend-ticket\nstatus: CANCELLED\n---\n# lama\n"})
    new(chain_repo)


def test_request_dari_stdin(chain_repo):
    code, out = tk(chain_repo, "new", "--slug", "x", "--title", "Judul", "--request", "-", stdin="baris satu\nbaris dua\n")
    assert code == 0
    assert "> baris satu\n> baris dua\n" in (chain_repo / out["ticket"]).read_text(encoding="utf-8")


# ── check ────────────────────────────────────────────────────────────────────

def test_kartu_terisi_lolos(chain_repo):
    td = new(chain_repo)
    assert tk(chain_repo, "check", "--ticketdir", td)[0] == 1, "templat mentah tidak lolos"
    fill(chain_repo, td)
    assert tk(chain_repo, "check", "--ticketdir", f"./{td}/TICKET.md") == (0, {"status": "PASS", "ticketdir": td})


@pytest.mark.parametrize("old, new_, needle", [
    ("`src/order.go:1`", "src/order.go", "tanpa bukti `path:baris`"),
    ("`src/order.go:1`", "`src/hilang.go:1`", "berkas tidak ada di repo"),
    ("`src/order.go:1`", "`src/order.go:9`", "melewati panjang berkas"),
    ("`src/order.go:1`", "`../luar.go:1`", "wajib relatif root repo"),
    ("- **AC-2**:", "- **AC-3**:", "penomoran AC wajib 1..n"),
    ("- **AC-2**: field lain tidak berubah", "- AC-2: field lain tidak berubah", "tidak kanonik"),
    ("- **AC-2**: field lain tidak berubah", "- **AC-2**:", "`AC-2` tanpa isi"),
    ("aditif —", "tambahan —", "wajib diawali jenis"),
    ("- Tambah `username` ke respons order", "- <isi: nanti>", "placeholder templat"),
    ("## Perubahan", "## Rencana", "seksi H2 wajib persis"),
    ("- Tambah `username` ke respons order\n", "- Tambah `username`\n- **AC-9**: nyasar\n", "di luar `## Acceptance"),
])
def test_kartu_cacat_ditolak(chain_repo, old, new_, needle):
    td = new(chain_repo)
    path = fill(chain_repo, td)
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new_, 1), encoding="utf-8")
    code, out = tk(chain_repo, "check", "--ticketdir", td)
    assert code == 1 and any(needle in p for p in out["problems"]), out


@pytest.mark.regression("40 T5")
def test_lebih_dari_lima_ac_bukan_tiket_cepat(chain_repo):
    td = new(chain_repo)
    acs = "\n".join(f"- **AC-{n}**: hasil {n}" for n in range(1, 7))
    fill(chain_repo, td, **{"- **AC-1**: <isi: hasil yang bisa diverifikasi dari luar, mis. response, status, "
                            "data tersimpan>": acs})
    code, out = tk(chain_repo, "check", "--ticketdir", td)
    assert code == 1 and any("melewati batas 5" in p and "backend:tech-lead" in p for p in out["problems"])


# ── approve / reopen / cancel / state ────────────────────────────────────────

@pytest.mark.regression("40 T4")
def test_approve_menuntut_check_lalu_menyegel(chain_repo):
    td = new(chain_repo)
    code, out = tk(chain_repo, "approve", "--ticketdir", td)
    assert code == 1 and out["problems"][0] == "`check` belum PASS"
    fill(chain_repo, td)
    code, out = tk(chain_repo, "approve", "--ticketdir", td)
    text = (chain_repo / td / "TICKET.md").read_text(encoding="utf-8")
    assert code == 0 and out["approved_seal"] == PL.ticket_seal(text)
    assert f"approved_seal_norm: {PL.ticket_seal_norm(text)}\n" in text and "approvals: 1\n" in text
    assert tk(chain_repo, "approve", "--ticketdir", td)[0] == 1, "READY tidak disetujui dua kali"
    assert git(chain_repo, "status", "--porcelain") == ""


def test_reopen_dan_cancel(chain_repo):
    td = ready(chain_repo)
    bind(chain_repo, td)
    code, out = tk(chain_repo, "reopen", "--ticketdir", td)
    text = (chain_repo / td / "TICKET.md").read_text(encoding="utf-8")
    assert code == 0 and "status: DRAFT\n" in text and "approved_seal: -\n" in text and "reopened: 1\n" in text
    assert TD in out["warnings"][0], "reopen memperingatkan taskdir pemakai"
    assert tk(chain_repo, "reopen", "--ticketdir", td)[0] == 1
    code, out = tk(chain_repo, "cancel", "--ticketdir", td)
    assert code == 0 and out["sync"] is True, "pernah READY → cermin perlu dibatalkan"
    assert tk(chain_repo, "cancel", "--ticketdir", td)[0] == 1
    other = new(chain_repo, "lain")
    assert tk(chain_repo, "cancel", "--ticketdir", other)[1]["sync"] is False


def test_state_keadaan_dan_pemakai(chain_repo):
    td = ready(chain_repo)
    bind(chain_repo, td)
    draft = new(chain_repo, "draf")
    write_files(chain_repo, {"backenddev/tickets/2601010000-batal/TICKET.md":
                             "---\nkind: backend-ticket\nstatus: CANCELLED\n---\n# batal\n"})
    (chain_repo / "backenddev/tickets/2601010001-rusak").mkdir()
    (chain_repo / "backenddev/tickets/2601010001-rusak/TICKET.md").write_bytes(b"\xff\xfe bukan utf-8\n")
    rows = {r["ticketdir"]: r for r in tk(chain_repo, "state")[1]["tickets"]}
    assert rows[td]["state"] == "READY" and rows[td]["used_by"] == [TD]
    assert rows[draft]["state"] == "DRAFT" and "backenddev/tickets/2601010000-batal" not in rows
    assert rows["backenddev/tickets/2601010001-rusak"]["state"] == "RUSAK"
    (chain_repo / td / "TICKET.md").write_text(
        (chain_repo / td / "TICKET.md").read_text(encoding="utf-8") + "\nsuntingan\n", encoding="utf-8")
    rows = {r["ticketdir"]: r for r in tk(chain_repo, "state", "--all")[1]["tickets"]}
    assert rows[td]["state"] == "DRIFT" and rows["backenddev/tickets/2601010000-batal"]["state"] == "DIBATALKAN"


# ── serah terima ke `task` check 7 (T4) ──────────────────────────────────────

@pytest.mark.regression("40 T4")
def test_tiket_ready_diterima_check_7(chain_repo):
    td = ready(chain_repo)
    c = check7(chain_repo, f"{td}/TICKET.md")
    assert c["status"] == "PASS" and "READY bersegel" in c["summary"], c


def test_suntingan_sesudah_approve_drift_dan_format_lolos(chain_repo):
    td = ready(chain_repo)
    path = chain_repo / td / "TICKET.md"
    original = path.read_text(encoding="utf-8")
    path.write_text(prettier_like(original), encoding="utf-8")
    assert check7(chain_repo, f"{td}/TICKET.md")["status"] == "PASS", "hanya format yang berubah (38 N1)"
    path.write_text(original.replace("data.username", "data.user_name"), encoding="utf-8")
    c = check7(chain_repo, f"{td}/TICKET.md")
    assert c["status"] == "FAIL" and "DRIFT" in c["summary"] and "backend:ticket" in c["action"], c


@pytest.mark.parametrize("mutate, needle", [
    (lambda t: t.replace("status: READY", "status: DRAFT"), "wajib `READY`"),
    (lambda t: re.sub(r"approved_seal: \w+", "approved_seal: -", t), "tanpa `approved_seal`"),
])
def test_tiket_belum_sah_ditolak_check_7(chain_repo, mutate, needle):
    td = ready(chain_repo)
    path = chain_repo / td / "TICKET.md"
    path.write_text(mutate(path.read_text(encoding="utf-8")), encoding="utf-8")
    c = check7(chain_repo, f"{td}/TICKET.md")
    assert c["status"] == "FAIL" and needle in c["summary"], c


def test_path_tiket_backend_tidak_ada(chain_repo):
    c = check7(chain_repo, "backenddev/tickets/2601010000-hilang/TICKET.md")
    assert c["status"] == "FAIL" and "tidak ada di disk" in c["summary"] and "backend:ticket" in c["action"]


def test_ac_tiket_dipikul_tac(chain_repo):
    td = ready(chain_repo)
    rel = f"{td}/TICKET.md"
    assert PL.ticket_carry_problems(chain_repo, rel, "- SC-1 (TAC-1, TAC-2)", "") == []
    assert PL.ticket_carry_problems(chain_repo, rel, "- SC-1 (TAC-1)", "") == [
        "TAC tanpa SC pemikul maupun `## Out of Scope`: TAC-2"]


# ── prasyarat skill ──────────────────────────────────────────────────────────

def test_prasyarat_lolos_di_repo_berprofil(chain_repo):
    checks = be_checks(chain_repo, PRE)
    assert [c["status"] for c in checks.values()] == ["PASS"] * 5


def test_prasyarat_gagal_tanpa_profil_dan_bukan_git(make_repo):
    root = make_repo({"x.go": "package x\n"})
    checks = be_checks(root, PRE)
    assert checks[1]["status"] == "PASS" and checks[2]["status"] == "FAIL"
    plain = make_repo({}, name="bukan-git", git_init=False)
    assert be_checks(plain, PRE)[1]["status"] == "FAIL"


def test_prasyarat_gagal_bila_tiket_ter_track(chain_repo):
    td = new(chain_repo)
    git(chain_repo, "add", "-f", f"{td}/TICKET.md")
    commit(chain_repo, "chore: tiket ter-commit tak sengaja")
    c = be_checks(chain_repo, PRE)[5]
    assert c["status"] == "FAIL" and "git rm -r --cached" in c["action"]


# ── cermin nataflow (T3) ─────────────────────────────────────────────────────

@pytest.fixture
def fake():
    with FakeMCP() as f:
        yield f, Nataflow(f, workspaces=[WEB])


def push(repo, td, *extra):
    return tk(repo, "sync", "--ticketdir", td, "--push", *extra)


def test_sync_tanpa_config_dilewati(chain_repo):
    td = ready(chain_repo)
    assert tk(chain_repo, "sync", "--ticketdir", td)[1]["status"] == "SKIP"
    code, out = push(chain_repo, td)
    assert (code, out["status"], out["segment"]) == (0, "SKIP", "nataflow dilewati")


@pytest.mark.regression("40 T3")
def test_sync_membuat_lalu_memperbarui_task_yang_sama(chain_repo, fake):
    f, nf = fake
    enable_sync(chain_repo, f.url, extra={"repo": "tim/api"})
    td = ready(chain_repo)
    code, out = push(chain_repo, td)
    assert code == 0 and out["segment"] == "nataflow dibuat #1", out
    task = nf.tasks[0]
    assert task["metadata"]["source"] == "backenddev" and task["metadata"]["ticket_key"] == td
    assert task["metadata"]["repo"] == "tim/api" and task["metadata"]["dampak_kontrak"] == "aditif"
    assert task["title"] == "Tambah field username di respons order" and "## Kondisi Sekarang" in task["description"]
    assert "Kondisi Sekarang" not in json.dumps(out), "isi tiket tidak dicetak"
    tk(chain_repo, "reopen", "--ticketdir", td)
    path = chain_repo / td / "TICKET.md"
    path.write_text(path.read_text(encoding="utf-8").replace("field lain tidak berubah", "field lain tetap"),
                    encoding="utf-8")
    assert tk(chain_repo, "approve", "--ticketdir", td)[0] == 0
    code, out = push(chain_repo, td)
    assert out["segment"] == "nataflow diperbarui #1" and len(nf.tasks) == 1
    assert "field lain tetap" in nf.tasks[0]["description"]


def test_sync_draft_ditolak_dan_batal_membatalkan_task(chain_repo, fake):
    f, nf = fake
    enable_sync(chain_repo, f.url)
    draft = new(chain_repo, "draf")
    code, out = push(chain_repo, draft)
    assert code == 1 and "hanya tiket READY" in out["segment"] and f.writes() == []
    td = ready(chain_repo)
    push(chain_repo, td)
    tk(chain_repo, "cancel", "--ticketdir", td)
    code, out = push(chain_repo, td)
    assert out["segment"] == "nataflow dibatalkan #1" and nf.tasks[0]["status"] == "cancelled"


def test_sync_kembar_dan_pilihan_workspace_tanpa_tulisan(chain_repo, fake):
    f, nf = fake
    enable_sync(chain_repo, f.url, extra={"workspaces": {"web": WEB, "mobile": MOBILE}})
    td = ready(chain_repo)
    code, out = push(chain_repo, td)
    assert out["status"] == "PILIH_WORKSPACE" and f.writes() == []
    nf.workspaces.append(MOBILE)
    assert push(chain_repo, td, "--workspace", "mobile")[1]["segment"] == "nataflow dibuat #1"
    assert nf.tasks[0]["workspace_id"] == MOBILE
    nf.add_task({"source": "backenddev", "ticket_key": td})
    f.calls.clear()
    code, out = push(chain_repo, td, "--workspace", "mobile")
    assert code == 1 and "2 task ber-ticket_key sama" in out["segment"] and f.writes() == []


@pytest.mark.regression("40 T3")
def test_taskdir_bertiket_backend_menempel_ke_task_tiket(chain_repo, fake):
    f, nf = fake
    enable_sync(chain_repo, f.url, extra={"repo": "tim/api"})
    td = ready(chain_repo)
    push(chain_repo, td)
    bind(chain_repo, td, report=True)
    r = run_script(SP, "--taskdir", TD, "--json", cwd=chain_repo)
    out = json.loads(r.stdout)
    ident = {"source": "backenddev", "ticket_key": td}
    assert out["task"]["lookup"]["metadata"] == json.dumps(ident, separators=(",", ":")), out
    assert json.loads(out["workdir"]["metadata"])["ticket_key"] == td
    r = run_script(SP, "--taskdir", TD, "--push", "--json", cwd=chain_repo)
    assert json.loads(r.stdout)["status"] == "PASS", r.stdout
    assert len(nf.tasks) == 1 and nf.workdirs[0]["task_id"] == nf.tasks[0]["id"]
    assert nf.tasks[0]["status"] == "done", "satu-satunya workdir tuntas → task tiket done lewat siblings"
