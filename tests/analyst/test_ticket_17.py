"""Langkah 17 — tiket teknis `TECH` untuk lead engineer (T1–T6).

Fixture `fixtures/ticket_tech.md` = TICKET.md `TECH` DRAFT, elisitasi OPEN dengan seluruh pilar terisi, kartu
lengkap. Repo fixture memuat berkas kode yang dirujuk `## Kondisi Saat Ini`, karena bukti `file:baris` diperiksa
terhadap disk.
"""
import hashlib
import json
from pathlib import Path

import pytest

from conftest import PLUGINS, git, load_module, run_script, ticket_review

COMMON = PLUGINS / "analyst" / "skills" / "_common"
TICKET = COMMON / "ticket.py"
VALIDATE = COMMON / "validate_doc.py"
TDIR = "analyst/tickets/2610011000-relasi-project-workspace"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ticket_tech.md"
FEATURE = Path(__file__).resolve().parent / "fixtures" / "ticket_valid.md"
CODE = {
    "internal/project/model.go": "".join(f"// baris {n}\n" for n in range(1, 31)),
    "internal/project/repository.go": "".join(f"// baris {n}\n" for n in range(1, 61)),
}
lib = load_module(COMMON / "analyst_lib.py", "analyst_lib_17")


class Run:
    def __init__(self, proc):
        self.code, self.out = proc.returncode, proc.stdout + proc.stderr


@pytest.fixture
def repo(make_repo):
    root = make_repo({f"{TDIR}/TICKET.md": FIXTURE.read_text(encoding="utf-8"), **CODE})
    git(root, "add", "-A")
    git(root, "commit", "-qm", "docs(ticket): fixture")
    return root


@pytest.fixture
def plain(make_repo):
    return make_repo(name="plain", git_init=False)


def tk(root, *args, stdin=""):
    return Run(run_script(TICKET, *args, cwd=root, stdin=stdin))


def checks(root, kind):
    r = run_script(VALIDATE, "--kind", kind, "--ticketdir", TDIR, "--json", cwd=root)
    return r.returncode, {c["id"]: c for c in json.loads(r.stdout)["checks"]}


def failed(root, kind):
    code, by_id = checks(root, kind)
    return code, {i: c["summary"] for i, c in by_id.items() if c["status"] == "FAIL"}


def edit(root, old, new):
    p = root / TDIR / "TICKET.md"
    body = p.read_text(encoding="utf-8")
    assert old in body, old
    p.write_text(body.replace(old, new, 1), encoding="utf-8")


# --- T1: `new` ----------------------------------------------------------------------------------

@pytest.mark.regression("17 T1")
def test_t1_new_tech_wajib_category_dan_kerangkanya_lolos(plain):
    r = tk(plain, "new", "--slug", "relasi", "--type", "TECH", "--requester", "Budi", "--request", "Rapikan relasi.")
    assert r.code == 1 and "wajib `--category" in r.out
    r = tk(plain, "new", "--slug", "relasi", "--type", "tech", "--category", "data_model", "--requester", "Budi",
           "--request", "Rapikan relasi.")
    assert r.code == 0 and "type=TECH · category=DATA_MODEL" in r.out, r.out
    td = next((plain / "analyst" / "tickets").iterdir())
    text = (td / "TICKET.md").read_text(encoding="utf-8")
    fm, _ = lib.split_frontmatter(text)
    assert (fm["type"], fm["category"]) == ("TECH", "DATA_MODEL")
    assert "#### Masalah Teknis\n" in text and "#### Rollout\n" in text and "#### Aktor" not in text
    v = run_script(VALIDATE, "--kind", "elicit", "--ticketdir", f"analyst/tickets/{td.name}", cwd=plain)
    assert v.returncode == 0, v.stdout


@pytest.mark.regression("17 T1")
def test_t1_category_ditolak_di_luar_tech(plain):
    r = tk(plain, "new", "--slug", "cicilan", "--type", "FEATURE", "--category", "REFACTOR", "--requester", "Rina",
           "--request", "Tolong bikin fitur cicilan.")
    assert r.code == 1 and "hanya untuk tiket TECH" in r.out
    r = tk(plain, "new", "--slug", "relasi", "--type", "TECH", "--category", "LAINNYA", "--requester", "Budi",
           "--request", "Rapikan relasi.")
    assert r.code == 1


# --- T2: kartu TECH sah -------------------------------------------------------------------------

@pytest.mark.regression("17 T2")
def test_t2_fixture_lolos_kedua_kind_dan_pemindai_kebocoran_mati(repo):
    assert failed(repo, "elicit") == (0, {})
    code, by_id = checks(repo, "ticket")
    assert code == 0, {i: c["summary"] for i, c in by_id.items() if c["status"] == "FAIL"}
    assert by_id[9]["name"] == "Bukti kondisi saat ini" and "2 rujukan" in by_id[9]["summary"]


@pytest.mark.regression("17 T2")
def test_t2_komentar_dan_generik_di_blok_kode_bukan_h1_atau_placeholder(repo):
    edit(repo, "## Keputusan\n", "```sh\n# backfill sekali jalan\nmake backfill\n```\n\n"
                                 "Repository mengembalikan `List<Project>`.\n\n## Keputusan\n")
    assert failed(repo, "ticket") == (0, {})
    assert failed(repo, "elicit") == (0, {})


@pytest.mark.regression("17 T2")
def test_t2_category_wajib_dan_hanya_untuk_tech(repo, make_repo):
    edit(repo, "category: DATA_MODEL\n", "")
    code, fails = failed(repo, "ticket")
    assert code == 1 and "category" in fails[1]
    root = make_repo({"analyst/tickets/2609231400-cicilan/TICKET.md":
                      FEATURE.read_text(encoding="utf-8").replace("type: FEATURE\n", "type: FEATURE\ncategory: REFACTOR\n")},
                     name="feature")
    r = run_script(VALIDATE, "--kind", "elicit", "--ticketdir", "analyst/tickets/2609231400-cicilan", "--json",
                   cwd=root)
    assert r.returncode == 1 and "category hanya untuk tiket TECH" in r.stdout


# --- T3: bukti `file:baris` -----------------------------------------------------------------------

@pytest.mark.regression("17 T3")
@pytest.mark.parametrize("old, new, pesan", [
    ("— `internal/project/model.go:12`", "— dari ingatan", "butir tanpa `path:baris`"),
    ("model.go:12`", "model.go:99`", "`internal/project/model.go:99` melampaui 30 baris"),
    ("model.go:12`", "hilang.go:3`", "`internal/project/hilang.go:3` tidak ada"),
    ("`internal/project/model.go:12`", "`../luar.go:1`", "`../luar.go:1` di luar root repo"),
    ("repository.go:40-48`", "repository.go:48-40`", "`internal/project/repository.go:48-40` melampaui"),
])
def test_t3_bukti_kondisi_saat_ini_harus_ada_di_disk(repo, old, new, pesan):
    (repo.parent / "luar.go").write_text("x\n", encoding="utf-8")
    edit(repo, old, new)
    code, fails = failed(repo, "ticket")
    assert code == 1 and list(fails) == [9] and pesan in fails[9], fails


# --- T4: AC, keputusan, batasan -----------------------------------------------------------------

@pytest.mark.regression("17 T4")
def test_t4_ac_tanpa_verifikasi_gugur(repo):
    edit(repo, " — verifikasi: snapshot test handler daftar project", "")
    code, fails = failed(repo, "ticket")
    assert code == 1 and "1 baris tanpa `— verifikasi:`" in fails[4]


@pytest.mark.regression("17 T4")
@pytest.mark.parametrize("old, new, pesan", [
    (" (C-2)", "", "C tanpa AC pemikul: C-2"),
    (" (C-2)", " (C-3)", "AC merujuk C hantu: C-3"),
    (" — alternatif: kolom `workspace_ids uuid[]`, ditolak karena tanpa FK", "", "baris keputusan rusak"),
    ("- **C-2**:", "- **C-3**:", "nomor C [1, 3] tidak urut"),
])
def test_t4_keputusan_dan_batasan(repo, old, new, pesan):
    edit(repo, old, new)
    code, fails = failed(repo, "ticket")
    assert code == 1 and pesan in fails[5], fails


@pytest.mark.regression("17 T4")
def test_t4_keputusan_dan_batasan_boleh_nihil_beralasan(repo):
    p = repo / TDIR / "TICKET.md"
    body = p.read_text(encoding="utf-8")
    start, end = body.index("## Keputusan\n"), body.index("## Acceptance Criteria\n")
    body = (body[:start] + "## Keputusan\n\n- Tidak ada keputusan baru — mengikuti pola repository yang ada\n\n"
            "## Batasan\n\n- Tidak ada batasan khusus — perubahan internal\n\n" + body[end:])
    p.write_text(body.replace(" (C-1)", "").replace(" (C-2)", ""), encoding="utf-8")
    assert failed(repo, "ticket") == (0, {})


# --- T5: sidik & siklus hidup -------------------------------------------------------------------

@pytest.mark.regression("17 T5")
def test_t5_sidik_tiket_lama_tanpa_category_tidak_bergeser():
    text = FEATURE.read_text(encoding="utf-8")
    fm, body = lib.split_frontmatter(text)
    norm = "\n".join(l.rstrip() for l in body.strip().splitlines())
    old = hashlib.sha256(f"type={fm['type']}\npriority={fm['priority']}\ndomain_terms=\n{norm}".encode()).hexdigest()
    assert lib.content_hash(text) == old[:12]
    tech = FIXTURE.read_text(encoding="utf-8")
    assert lib.content_hash(tech) != lib.content_hash(tech.replace("DATA_MODEL", "REFACTOR"))
    assert lib.content_hash(tech, "elicit") == lib.content_hash(tech.replace("DATA_MODEL", "REFACTOR"), "elicit")


@pytest.mark.regression("17 T5")
def test_t5_siklus_close_review_approve_lalu_category_tersunting_drift(repo):
    r = tk(repo, "close", "--ticketdir", TDIR)
    assert r.code == 0, r.out
    assert ticket_review(repo, TDIR, "PASS").returncode == 0
    r = tk(repo, "approve", "--ticketdir", TDIR, "--answer", "Setujui")
    assert r.code == 0, r.out
    fm, _ = lib.split_frontmatter((repo / TDIR / "TICKET.md").read_text(encoding="utf-8"))
    assert fm["status"] == "READY"
    assert failed(repo, "ticket") == (0, {})
    edit(repo, "category: DATA_MODEL", "category: REFACTOR")
    code, fails = failed(repo, "ticket")
    assert code == 1 and list(fails) == [11]


# --- T6: sinkron nataflow -----------------------------------------------------------------------

@pytest.mark.regression("17 T6")
def test_t6_metadata_sinkron_membawa_category(repo):
    cfg = repo / "analyst" / "nataflow.json"
    cfg.write_text(json.dumps({"workspaces": {"utama": "a3e1d6c4-1f2b-4c3d-9e8f-7a6b5c4d3e2f"}}), encoding="utf-8")
    assert tk(repo, "close", "--ticketdir", TDIR).code == 0
    assert ticket_review(repo, TDIR, "PASS").returncode == 0
    assert tk(repo, "approve", "--ticketdir", TDIR, "--answer", "Setujui").code == 0
    r = run_script(TICKET, "sync-payload", "--ticketdir", TDIR, "--json", cwd=repo)
    meta = json.loads(json.loads(r.stdout)["create"]["metadata"])
    assert (meta["type"], meta["category"]) == ("TECH", "DATA_MODEL")
