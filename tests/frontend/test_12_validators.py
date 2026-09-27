"""Regresi 12 Tahap 3 — validator dokumen `frontend` (J14, J24–J41, plus J17 untuk TREE review).

`validate_briefs.py` menerima operator shell di `verification` (J14), menghitung brief `BLOCKED` sebagai
pemikul (J24), plafon remedinya dapat dijebol (J27), `CREATE` ganda dan `unit` palsu lolos (J32), Anchor
dua simbol dianggap kosong (J33). Baris SC/AC/temuan/Done Criteria yang salah format hilang diam-diam
(J25, J26, J28, J30, J39); path keluar root diterima (J29); kunci frontmatter ganda lolos (J31); contoh
template gagal di validatornya sendiri (J34); `validate_report` memakai pendeteksi placeholder sendiri
(J35); bukti biner dan audit di luar root berakhir pesan salah atau traceback (J36, J37); alat ukur tanpa
objek lolos (J38); pagar `~~~` dan taskdir tak berpola (J40); bukti AC tidak ditagih (J41).
"""
import json

import pytest

from conftest import FE_FIX, FE_MINOR_TD, FE_SKILLS, FE_TD, commit, fe_brief, fe_profile, fe_review_md, fe_run, \
    git, load_module, write_files

LIB = load_module(FE_SKILLS / "_common/precondition_lib.py", "fe_lib_12d")
VB = "plan/scripts/validate_briefs.py"
B1 = f"{FE_TD}/brief-01-orders-lacak-button.md"
REVIEW = f"{FE_MINOR_TD}/REVIEW.md"
AUDIT = "frontenddev/reviews/2609230900-cart-audit.md"
SC1 = "- [ ] **SC-1**: tombol *Lacak* tampil di detail pesanan — verifikasi: test `OrderDetail.test.tsx` hijau"
PASS_REVIEW = dict(verdict="PASS", p2="0", summary_status="PASS", total="- Total Findings: 0 (0 P1, 0 P2, 0 P3)",
                   findings="", dims=["PASS"] * 9)


def as_checks(proc) -> dict:
    out = proc.stdout + proc.stderr
    assert "Traceback" not in out, out
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


def details(c) -> str:
    return " ".join([c.get("summary", "")] + list(c.get("details", [])))


def edit(repo, rel, old, new, count=1):
    p = repo / rel
    text = p.read_text(encoding="utf-8")
    assert old in text, (rel, old)
    p.write_text(text.replace(old, new, count), encoding="utf-8")


def briefs(repo, *args, taskdir=FE_TD):
    return as_checks(fe_run(repo, VB, "--taskdir", taskdir, "--json", *args))


def doc(repo, kind, taskdir=FE_TD):
    return as_checks(fe_run(repo, "_common/validate_doc.py", "--kind", kind, "--taskdir", taskdir, "--json"))


def task_checks(repo, taskdir=FE_TD):
    return as_checks(fe_run(repo, "task/scripts/validate_task.py", "--taskdir", taskdir, "--json"))


def review(repo, *extra):
    proc = fe_run(repo, "architect/scripts/validate_review.py", "--taskdir", FE_MINOR_TD, "--json", *extra)
    data = json.loads(proc.stdout)
    assert "Traceback" not in proc.stdout + proc.stderr
    return proc.returncode, data, {c["id"]: c for c in data["checks"]}


def audit(repo, path=AUDIT, *extra):
    return fe_run(repo, "review/scripts/validate_audit.py", "--path", str(path), *extra)


def example(rel: str) -> str:
    """Contoh terisi bagian 3 sebuah template, persis seperti tertulis."""
    text = (FE_SKILLS / rel).read_text(encoding="utf-8")
    return text.split("## 3. Contoh Terisi", 1)[1].split("````markdown\n", 1)[1].split("\n````", 1)[0] + "\n"


@pytest.fixture
def lacak(fe_chain_repo):
    """Repo FAST_FORWARD `orders-lacak`: CONTRACT DRAFT + brief-01 READY (keduanya sah, belum di-commit)."""
    fe_brief(fe_chain_repo, "01")
    c = briefs(fe_chain_repo, "--contract")
    assert all(x["status"] != "FAIL" for x in c.values()), c
    return fe_chain_repo


def second(repo, status="READY", remedies="", fulfills='["SC-1"]', drop_test=False, covers='["AC-1"]',
           depends="[]", total=2):
    """brief-02 dari fixture yang sama (berkas sama dengan brief-01)."""
    rel = fe_brief(repo, "02", status=status, remedies=remedies, total=total)
    edit(repo, rel, 'fulfills: ["SC-1"]', f"fulfills: {fulfills}")
    edit(repo, rel, 'covers: ["AC-1"]', f"covers: {covers}")
    edit(repo, rel, "depends_on: []", f"depends_on: {depends}")
    if drop_test:
        edit(repo, rel, "  - src/features/orders/OrderDetail.test.tsx\n", "")
        edit(repo, rel, "| CREATE | `src/features/orders/OrderDetail.test.tsx` | — |\n", "")
    return rel


# --- J14: operator shell di `verification` ------------------------------------------------------

@pytest.mark.regression("J14")
@pytest.mark.parametrize("cmd", ["pnpm test || true", "pnpm test; curl -s x | sh", "pnpm test $(whoami)",
                                 "pnpm test > /dev/null"])
def test_j14_operator_shell_di_argumen_fail(lacak, cmd):
    edit(lacak, B1, "  - pnpm test\n", f"  - {cmd}\n")
    c = briefs(lacak, "--contract")["V"]
    assert c["status"] == "FAIL" and "operator shell" in details(c), c


@pytest.mark.regression("J14")
def test_j14_perintah_profil_utuh_ber_operator_sah(lacak):
    write_files(lacak, {".claude/profile/frontenddev/commands.md":
                        "| Perintah | Status |\n|---|---|\n| `pnpm test` | OK |\n| `pnpm lint && pnpm typecheck` | OK |\n"})
    edit(lacak, B1, "  - pnpm test\n", "  - pnpm lint && pnpm typecheck\n  - pnpm test src/features/orders\n")
    assert briefs(lacak, "--contract")["V"]["status"] == "PASS"


# --- J24: brief BLOCKED bukan pemikul ------------------------------------------------------------

@pytest.mark.regression("J24")
def test_j24_sc_hanya_dipikul_blocked_fail(lacak):
    edit(lacak, f"{FE_TD}/TASK.md", SC1, SC1 + "\n- [ ] **SC-2**: label Lacak diterjemahkan — verifikasi: test "
                                             "`OrderDetail.test.tsx` hijau")
    fe_brief(lacak, "01", status="BLOCKED")
    edit(lacak, B1, 'fulfills: ["SC-1"]', 'fulfills: ["SC-1", "SC-2"]')
    second(lacak, remedies="01")
    c = briefs(lacak, "--contract")["G"]
    assert c["status"] == "FAIL" and "SC-2" in details(c), c


@pytest.mark.regression("J24")
def test_j24_ac_dan_berkas_hanya_di_blocked_fail(lacak):
    fe_brief(lacak, "01", status="BLOCKED")
    second(lacak, remedies="01", covers="[]", drop_test=True)
    c = briefs(lacak, "--contract")
    assert c["C"]["status"] == "FAIL" and "AC-1" in details(c["C"]), c["C"]
    assert c["E"]["status"] == "FAIL" and "OrderDetail.test.tsx" in details(c["E"]), c["E"]


@pytest.mark.regression("J24")
def test_j24_remedi_memikul_ulang_pass(lacak):
    fe_brief(lacak, "01", status="BLOCKED")
    second(lacak, remedies="01")
    c = briefs(lacak, "--contract")
    assert [k for k, v in c.items() if v["status"] == "FAIL"] == [], c


# --- J25: baris SC salah format di akar -----------------------------------------------------------

@pytest.mark.regression("J25")
@pytest.mark.parametrize("line", ["- [ ] SC-2: status kurir tampil — verifikasi: test `T.test.tsx` hijau",
                                  "- [ ] **SC-2** : banner error — verifikasi: test `T.test.tsx` hijau",
                                  "- **SC-2**: banner error — verifikasi: test `T.test.tsx` hijau"])
def test_j25_sc_salah_format_fail(fe_chain_repo, line):
    edit(fe_chain_repo, f"{FE_TD}/TASK.md", SC1, SC1 + "\n" + line)
    c = task_checks(fe_chain_repo)[2]
    assert c["status"] == "FAIL" and "SC-2" in c["summary"], c


# --- J26: verdict REVIEW tidak turun karena format -----------------------------------------------

def pass_review_with_done(repo, row: str) -> str:
    text = fe_review_md(repo, **PASS_REVIEW, done="tidak terpenuhi")
    return text.replace("| brief-01 | pnpm test nol galat baru | tidak terpenuhi | HIJAU |", row)


@pytest.mark.regression("J26")
@pytest.mark.parametrize("row", ["| `brief-01` | pnpm test nol galat baru | tidak terpenuhi | MERAH |",
                                 "| brief-01 | pnpm test nol galat baru | tidak terpenuhi | `pnpm test \\| tail` MERAH |"],
                         ids=["brief_berbacktick", "pipa_escaped"])
def test_j26_done_tidak_terpenuhi_tetap_blocked(fe_minor_chain, row):
    write_files(fe_minor_chain, {REVIEW: pass_review_with_done(fe_minor_chain, row)})
    rc, data, _ = review(fe_minor_chain)
    assert rc == 1 and data["derived_verdict"] == "BLOCKED", data


@pytest.mark.regression("J26")
def test_j26_baris_done_tak_terurai_fail(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: pass_review_with_done(fe_minor_chain, "| brief-01 | tidak terpenuhi |")})
    rc, _, c = review(fe_minor_chain)
    assert rc == 1 and c["DC"]["status"] == "FAIL" and "tak terurai" in details(c["DC"]), c["DC"]


@pytest.mark.regression("J26")
@pytest.mark.parametrize("heading", ["###[P1-1] DTO bocor", "### [p1-1] DTO bocor", "### [P1 - 1] DTO bocor"])
def test_j26_heading_temuan_cacat_fail(fe_minor_chain, heading):
    finding = f"{heading}\n\n> Status: PLANNED\n\n- **Violation**: Dimensi 1 — bocor.\n"
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, **{**PASS_REVIEW, "findings": finding})})
    rc, _, c = review(fe_minor_chain)
    assert rc == 1 and c["T"]["status"] == "FAIL" and "tak terurai" in details(c["T"]), c["T"]


@pytest.mark.regression("J26")
@pytest.mark.regression("J17")
def test_j17_tree_review_tak_terbaca_fail(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain)})
    (fe_minor_chain / ".git/index").write_bytes(b"garbage")
    _, _, c = review(fe_minor_chain, "--log", f"{FE_MINOR_TD}/.explore/closing-verification.json")
    assert c["TREE"]["status"] == "FAIL" and "git status" in details(c["TREE"]), c["TREE"]


# --- J27: plafon remedi -----------------------------------------------------------------------------

def blocked_commit(repo, *rels, nn="01"):
    commit(repo, f"docs(orders-lacak): unit {nn} BLOCKED - galat", *rels)


def task_subject(repo, subject):
    edit(repo, f"{FE_TD}/TASK.md", "## Chain", "## Chain\n", 1)
    commit(repo, f"docs(orders-lacak): {subject}", f"{FE_TD}/TASK.md")


@pytest.mark.regression("J27")
def test_j27_remedi_tanpa_field_fail(lacak):
    fe_brief(lacak, "01", status="BLOCKED")
    blocked_commit(lacak, B1)
    second(lacak)
    c = briefs(lacak, "--contract")["M"]
    assert c["status"] == "FAIL" and "remedies" in details(c) and "02" in details(c), c


@pytest.mark.regression("J27")
def test_j27_brief_asli_sebelum_blocked_tidak_ditagih(lacak):
    rel2 = second(lacak, depends='["01"]')
    commit(lacak, "docs(orders-lacak): draft breakdown (2 briefs)", B1, rel2)
    fe_brief(lacak, "01", status="BLOCKED")
    edit(lacak, B1, 'total_units: "1"', 'total_units: "2"')
    blocked_commit(lacak, B1)
    assert briefs(lacak, "--contract")["M"]["status"] != "FAIL"


def three_blocked(repo):
    rels = [fe_brief(repo, "01", status="BLOCKED", total=4), fe_brief(repo, "02", status="BLOCKED", remedies="01", total=4),
            fe_brief(repo, "03", status="BLOCKED", remedies="01", total=4)]
    blocked_commit(repo, *rels, nn="03")
    fe_brief(repo, "04", remedies="01", total=4)


@pytest.mark.regression("J27")
def test_j27_reopen_sebelum_blocked_tidak_menaikkan_plafon(lacak):
    task_subject(lacak, "reopen CONTRACT — revisi desain sebelum eksekusi")
    three_blocked(lacak)
    c = briefs(lacak, "--contract")["M"]
    assert c["status"] == "FAIL" and "plafon" in details(c), c


@pytest.mark.regression("J27")
def test_j27_reopen_sesudah_blocked_menaikkan_plafon(lacak):
    three_blocked(lacak)
    task_subject(lacak, "reopen CONTRACT — remedi ketiga atas unit 01")
    assert briefs(lacak, "--contract")["M"]["status"] == "PASS"


# --- J28: satu pengurai AC -----------------------------------------------------------------------

@pytest.mark.regression("J28")
def test_j28_ac_tanpa_pipa_penutup_divalidasi(fe_chain_repo):
    with open(fe_chain_repo / FE_TD / "CONTRACT.md", "a", encoding="utf-8") as fh:
        fh.write("| `AC-2` | Hantu | dinilai layak | `SC-9`\n")
    c = doc(fe_chain_repo, "contract")["C"]
    assert c["status"] == "FAIL" and "AC-2" in details(c) and "SC-9" in details(c), c


@pytest.mark.regression("J28")
def test_j28_ac_sel_kurang_fail_di_doc_dan_briefs(lacak):
    with open(lacak / FE_TD / "CONTRACT.md", "a", encoding="utf-8") as fh:
        fh.write("| `AC-2` | Hantu | test otomatis |\n")
    assert doc(lacak, "contract")["C"]["status"] == "FAIL"
    c = briefs(lacak, "--contract")["C"]
    assert c["status"] == "FAIL" and "AC-2" in details(c), c


@pytest.mark.regression("J28")
def test_j28_ac_rows_pengurai_bersama():
    body = ("## 5. Acceptance Criteria\n\n| ID | Skenario | Cara verifikasi | Sumber |\n|---|---|---|---|\n"
            "| `AC-1` | a \\| b | test otomatis | `SC-1` |\n"
            "| AC-2 | c | QA manual: klik | `SC-1`\n"
            "| `AC-3` | d | test otomatis |\n"
            "| x | `AC-4` salah kolom | test otomatis | `SC-1` |\n")
    rows, problems = LIB.ac_rows(body)
    assert [r[0] for r in rows] == ["AC-1", "AC-2", "AC-3"]
    assert rows[0][1] == ["a | b", "test otomatis", "`SC-1`"]
    assert any("AC-3" in p for p in problems) and any("AC-4" in p for p in problems), problems


# --- J29: path keluar root -------------------------------------------------------------------------

@pytest.mark.regression("J29")
@pytest.mark.parametrize("path", ["../luar.ts", "/tmp/luar.ts", "src/../../luar.ts"])
def test_j29_files_touched_keluar_root_fail(lacak, path):
    (lacak.parent / "luar.ts").write_text("x\n", encoding="utf-8")
    edit(lacak, B1, "  - src/features/orders/OrderDetail.test.tsx\n",
         f"  - src/features/orders/OrderDetail.test.tsx\n  - {path}\n")
    edit(lacak, B1, "| CREATE | `src/features/orders/OrderDetail.test.tsx` | — |",
         f"| CREATE | `src/features/orders/OrderDetail.test.tsx` | — |\n| MODIFY | `{path}` | `x` |")
    edit(lacak, f"{FE_TD}/CONTRACT.md", "- `CREATE` `src/features/orders/OrderDetail.test.tsx`",
         f"- `CREATE` `src/features/orders/OrderDetail.test.tsx`\n- `MODIFY` `{path}`")
    c = briefs(lacak, "--contract")
    assert c["R"]["status"] == "FAIL" and "di luar root" in details(c["R"]), c["R"]
    e = doc(lacak, "contract")["E"]
    assert e["status"] == "FAIL" and "di luar root" in details(e), e


@pytest.mark.regression("J29")
def test_j29_bukti_task_keluar_root_fail(fe_chain_repo):
    (fe_chain_repo.parent / "luar.ts").write_text("x\n", encoding="utf-8")
    edit(fe_chain_repo, f"{FE_TD}/TASK.md", "`src/features/orders/OrderDetail.tsx:1`", "`../luar.ts:1`")
    c = task_checks(fe_chain_repo)[4]
    assert c["status"] == "FAIL" and "di luar root" in c["summary"], c


# --- J30: audit ---------------------------------------------------------------------------------------

@pytest.fixture
def audited(make_repo):
    repo = make_repo({AUDIT: (FE_FIX / "audit_valid.md").read_text(encoding="utf-8")})
    commit(repo, "docs(review): audit cart-audit")
    return repo


@pytest.mark.regression("J30")
def test_j30_temuan_tanpa_judul_fail(audited):
    edit(audited, AUDIT, "### [P1-1] DTO bocor ke komponen presentasi", "### [P1-1]")
    edit(audited, AUDIT, "verdict: BLOCKED", "verdict: PASS")
    edit(audited, AUDIT, "p1: 1", "p1: 0")
    edit(audited, AUDIT, "- Total Findings: 1 (1 P1, 0 P2, 0 P3)", "- Total Findings: 0 (0 P1, 0 P2, 0 P3)")
    edit(audited, AUDIT, "- Overall Status: BLOCKED", "- Overall Status: PASS")
    r = audit(audited)
    assert r.returncode == 1 and "tak terurai" in r.stdout, r.stdout


@pytest.mark.regression("J30")
@pytest.mark.parametrize("old, new", [("- Overall Status: BLOCKED", "- Overall Status: PASS"),
                                      ("- Total Findings: 1 (1 P1, 0 P2, 0 P3)", "- Total Findings: 0 (0 P1, 0 P2, 0 P3)")])
def test_j30_summary_tak_selaras_fail(audited, old, new):
    edit(audited, AUDIT, old, new)
    r = audit(audited)
    assert r.returncode == 1 and "Summary" in r.stdout, r.stdout


# --- J31: kunci frontmatter ganda ---------------------------------------------------------------------

DUP = "---\nstatus: DRAFT\nslug: x\nstatus: APPROVED\n---\n# x\n"


@pytest.mark.regression("J31")
def test_j31_kunci_ganda_fail_strict():
    with pytest.raises(LIB.FrontmatterError, match="lebih dari sekali"):
        LIB.split_frontmatter(DUP, strict=True)


@pytest.mark.regression("J31")
def test_j31_read_status_sentinel(tmp_path):
    p = tmp_path / "CONTRACT.md"
    p.write_text(DUP, encoding="utf-8")
    assert LIB.read_status(p) not in ("", "DRAFT", "APPROVED")


@pytest.mark.regression("J31")
def test_j31_status_ganda_terdeteksi_drift():
    one = "---\nstatus: APPROVED\nslug: x\n---\n# x\n"
    two = "---\nstatus: APPROVED\nstatus: DRAFT\nslug: x\n---\n# x\n"
    assert LIB.strip_status_line(two) != LIB.strip_status_line(one)
    assert LIB.strip_status_line(one) == "---\nslug: x\n---\n# x\n"


@pytest.mark.regression("J31")
def test_j31_validate_doc_kunci_ganda_fail(fe_chain_repo):
    edit(fe_chain_repo, f"{FE_TD}/CONTRACT.md", "status: DRAFT\n", "status: DRAFT\nstatus: APPROVED\n")
    c = doc(fe_chain_repo, "contract")
    assert any(x["status"] == "FAIL" and "lebih dari sekali" in details(x) for x in c.values()), c


@pytest.mark.regression("J31")
def test_j31_validate_task_kunci_ganda_fail(fe_chain_repo):
    edit(fe_chain_repo, f"{FE_TD}/TASK.md", "status: ACTIVE\n", "status: ACTIVE\nlane: HOTFIX_MINOR\n")
    c = task_checks(fe_chain_repo)[1]
    assert c["status"] == "FAIL" and "lebih dari sekali" in c["summary"], c


# --- J32: CREATE ganda & `unit` ----------------------------------------------------------------------

@pytest.mark.regression("J32")
def test_j32_create_ganda_fail(lacak):
    edit(lacak, B1, 'total_units: "1"', 'total_units: "2"')
    second(lacak, depends='["01"]')
    c = briefs(lacak, "--contract")["R"]
    assert c["status"] == "FAIL" and "CREATE" in details(c) and "OrderDetail.test.tsx" in details(c), c


@pytest.mark.regression("J32")
def test_j32_unit_beda_nama_berkas_fail(lacak):
    edit(lacak, B1, 'unit: "01"', 'unit: "07"')
    c = briefs(lacak, "--contract")["S"]
    assert c["status"] == "FAIL" and "unit" in details(c), c


# --- J33: Anchor dua simbol ----------------------------------------------------------------------------

@pytest.mark.regression("J33")
@pytest.mark.parametrize("anchor", ["`OrderDetail`, `TRACK_LABEL`", "`OrderDetail` (ekspor default)"])
def test_j33_anchor_dua_simbol_sah(lacak, anchor):
    edit(lacak, B1, "| `OrderDetail` |", f"| {anchor} |")
    assert briefs(lacak, "--contract")["R"]["status"] == "PASS"


@pytest.mark.regression("J33")
def test_j33_anchor_kosong_tetap_fail(lacak):
    edit(lacak, B1, "| `OrderDetail` |", "| — |")
    assert briefs(lacak, "--contract")["R"]["status"] == "FAIL"


# --- J34: contoh terisi tiap template lolos validatornya -----------------------------------------------

TRACK_TD = "frontenddev/docs/2609231200-order-tracking"
CHECKOUT_TD = "frontenddev/docs/2609241000-order-checkout"


def numbered(n: int) -> str:
    return "".join(f"// {i}\n" for i in range(n))


@pytest.fixture
def tracking(make_repo):
    """Repo contoh `order-tracking`: berkas bukti Description ada, akar `TASK.md` contoh ter-commit."""
    repo = make_repo({"src/features/orders/OrderDetail.tsx": numbered(100), "src/app/router.tsx": numbered(50)})
    commit(repo, "init")
    write_files(repo, {f"{TRACK_TD}/TASK.md": example("task/templates/task-template.md")})
    commit(repo, "docs(order-tracking): kunci TASK sebagai akar rantai")
    return repo


@pytest.mark.regression("J34")
def test_j34_contoh_task_template_pass(tracking):
    c = task_checks(tracking, TRACK_TD)
    assert [k for k, v in c.items() if v["status"] != "PASS"] == [], c


@pytest.mark.regression("J34")
def test_j34_contoh_report_template_pass(tracking):
    files = {"src/app/router.tsx": numbered(51), "src/features/orders/OrderDetail.tsx": numbered(101),
             "src/features/orders/OrderDetail.test.tsx": "x\n", "src/features/tracking/TrackingScreen.tsx": "x\n",
             "src/features/tracking/TrackingScreen.test.tsx": "x\n"}
    write_files(tracking, files)
    commit(tracking, "feat(order-tracking): implement unit 01 - tracking", *files)
    write_files(tracking, {f"{TRACK_TD}/REPORT.md": example("report/templates/report-template.md")})
    c = as_checks(fe_run(tracking, "report/scripts/validate_report.py", "--taskdir", TRACK_TD, "--json"))
    assert [k for k, v in c.items() if v["status"] != "PASS"] == [], c


@pytest.fixture
def checkout(make_repo):
    """Taskdir contoh `order-checkout`: TASK (SC-1, SC-2; flow+ui), FLOW, UI, CONTRACT contoh."""
    task = example("task/templates/task-template.md")
    task = "\n".join(l for l in task.splitlines() if "**SC-3**" not in l) + "\n"
    repo = make_repo({f"{CHECKOUT_TD}/TASK.md": task,
                      f"{CHECKOUT_TD}/FLOW.md": example("ux-design/templates/flow-template.md"),
                      f"{CHECKOUT_TD}/UI.md": example("ui-design/templates/ui-template.md"),
                      f"{CHECKOUT_TD}/CONTRACT.md": example("contract/templates/contract-template.md")})
    commit(repo, "init")
    return repo


@pytest.mark.regression("J34")
@pytest.mark.parametrize("kind", ["flow", "ui", "contract"])
def test_j34_contoh_dokumen_gate_pass(checkout, kind):
    c = doc(checkout, kind, CHECKOUT_TD)
    assert [k for k, v in c.items() if v["status"] != "PASS"] == [], c


@pytest.mark.regression("J34")
def test_j34_contoh_brief_template_pass(make_repo):
    td = "frontenddev/docs/2609240900-item-catalog"
    brief = example("plan/templates/brief-template.md").replace('total_units: "03"', 'total_units: "01"')
    task = ("---\nstatus: ACTIVE\nlane: HOTFIX_MINOR\nsections: []\ncreated: 2026-09-24\n---\n\n# Katalog\n\n"
            "## Success Criteria\n\n- [ ] **SC-1**: daftar item tampil — verifikasi: test `item.service.test.ts` hijau\n")
    repo = make_repo({f"{td}/TASK.md": task, f"{td}/brief-01-data-transport.md": brief})
    fe_profile(repo, "react-vite")
    write_files(repo, {".claude/profile/frontenddev/commands.md":
                       "| Perintah | Status |\n|---|---|\n| `pnpm typecheck` | OK |\n| `pnpm lint` | OK |\n"
                       "| `pnpm test` | OK |\n"})
    c = briefs(repo, taskdir=td)
    assert [k for k, v in c.items() if v["status"] not in ("PASS", "SKIP")] == [], c


@pytest.mark.regression("J34")
def test_j34_contoh_audit_template_pass(make_repo):
    repo = make_repo({AUDIT: example("review/templates/audit-template.md")})
    commit(repo, "docs(review): audit cart-audit")
    r = audit(repo)
    assert r.returncode == 0, r.stdout


# --- J35: placeholder REPORT = pendeteksi bersama ----------------------------------------------------

@pytest.mark.regression("J35")
def test_j35_perbandingan_bukan_placeholder(fe_minor_chain):
    edit(fe_minor_chain, f"{FE_MINOR_TD}/REPORT.md", "Tombol order kini berlabel Pesan.",
         "Tombol order kini merender label dalam waktu < 300 ms untuk jumlah item > 0.")
    c = as_checks(fe_run(fe_minor_chain, "report/scripts/validate_report.py", "--taskdir", FE_MINOR_TD, "--json"))
    assert c[6]["status"] == "PASS", c[6]


@pytest.mark.regression("J35")
def test_j35_slot_template_tetap_ditolak(fe_minor_chain):
    edit(fe_minor_chain, f"{FE_MINOR_TD}/REPORT.md", "Tombol order kini berlabel Pesan.",
         "Tombol order kini berlabel <nama label> di `src/features/<slug>/x.tsx`.")
    c = as_checks(fe_run(fe_minor_chain, "report/scripts/validate_report.py", "--taskdir", FE_MINOR_TD, "--json"))
    assert c[6]["status"] == "FAIL" and "<slug>" in c[6]["summary"], c[6]


# --- J36: bukti berkas biner -------------------------------------------------------------------------

@pytest.mark.regression("J36")
def test_j36_bukti_biner_ditolak_terbaca(fe_minor_chain):
    (fe_minor_chain / "src/assets").mkdir(parents=True)
    (fe_minor_chain / "src/assets/logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe\x00\x01")
    commit(fe_minor_chain, "feat(order-checkout): implement unit 02 - logo", "src/assets/logo.png")
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain, sc_evidence="`src/assets/logo.png:1`")})
    rc, _, c = review(fe_minor_chain)
    assert rc == 1 and c["SC"]["status"] == "FAIL" and "bukan berkas teks" in details(c["SC"]), c["SC"]
    assert c["S"]["status"] == "PASS", c["S"]


# --- J37: audit --only-status-changed ---------------------------------------------------------------

@pytest.mark.regression("J37")
def test_j37_path_luar_root_tanpa_traceback(audited, tmp_path):
    outside = tmp_path / "luar.md"
    outside.write_text((audited / AUDIT).read_text(encoding="utf-8"), encoding="utf-8")
    r = audit(audited, outside, "--only-status-changed")
    assert r.returncode == 1 and "Traceback" not in r.stdout + r.stderr and "di luar root" in r.stdout, r.stdout + r.stderr


@pytest.mark.regression("J37")
def test_j37_untracked_fail(make_repo):
    repo = make_repo({"README.md": "x\n"})
    commit(repo, "init")
    write_files(repo, {AUDIT: (FE_FIX / "audit_valid.md").read_text(encoding="utf-8")})
    r = audit(repo, AUDIT, "--only-status-changed")
    assert r.returncode == 1 and "belum ter-commit" in r.stdout, r.stdout


# --- J38: alat ukur tanpa objek ----------------------------------------------------------------------

@pytest.mark.regression("J38")
@pytest.mark.parametrize("measure", ["test", "build", "QA manual:", "typecheck "])
def test_j38_alat_ukur_tanpa_objek_fail(fe_chain_repo, measure):
    edit(fe_chain_repo, f"{FE_TD}/TASK.md", "— verifikasi: test `OrderDetail.test.tsx` hijau",
         f"— verifikasi: {measure}")
    c = task_checks(fe_chain_repo)[3]
    assert c["status"] == "FAIL" and "SC-1" in c["summary"], c


# --- J39: baris Verifikasi Penutup pendek ------------------------------------------------------------

@pytest.mark.regression("J39")
def test_j39_baris_verifikasi_pendek_fail(fe_minor_chain):
    write_files(fe_minor_chain, {REVIEW: fe_review_md(fe_minor_chain,
                                                      verification="| `test` | HIJAU | 0 |\n| `lint` | MERAH |")})
    rc, data, c = review(fe_minor_chain)
    assert rc == 1 and c["VP"]["status"] == "FAIL" and data["derived_verdict"] == "BLOCKED", c["VP"]


# --- J40: pagar `~~~`, normalisasi taskdir, pola taskdir ------------------------------------------------

TILDE = "## A\n~~~\n## B\n~~~\nisi\n## C\nx\n"


@pytest.mark.regression("J40")
def test_j40_pagar_tilde_tidak_memotong_seksi():
    assert "isi" in LIB.section_lines(TILDE, "## A")
    vb = load_module(FE_SKILLS / VB, "fe_vb_12d")
    assert "isi" in vb.read_section(TILDE, "## A")


@pytest.mark.regression("J40")
def test_j40_taskdir_ganda_garis_miring_dinormalisasi(lacak):
    proc = fe_run(lacak, VB, "--taskdir", "frontenddev//docs/2609241200-orders-lacak/", "--json")
    data = json.loads(proc.stdout)
    assert data["fatal"] is None and data["status"] == "PASS", data


@pytest.mark.regression("J40")
def test_j40_taskdir_dotdot_briefs_ditolak(lacak):
    proc = fe_run(lacak, VB, "--taskdir", "frontenddev/docs/../docs/2609241200-orders-lacak", "--json")
    assert proc.returncode == 1 and "tidak berpola" in json.loads(proc.stdout)["fatal"]


@pytest.mark.regression("J40")
def test_j40_validate_doc_taskdir_tak_berpola_fail(make_repo):
    repo = make_repo({"frontenddev/docs/orders/FLOW.md": example("ux-design/templates/flow-template.md")})
    c = doc(repo, "flow", "frontenddev/docs/orders")
    assert any(x["status"] == "FAIL" and "tidak berpola" in details(x) for x in c.values()), c


# --- J41: bukti AC ------------------------------------------------------------------------------------

CONTRACT_AC = ("---\nstatus: APPROVED\n---\n\n# Contract — Order\n\n## 5. Acceptance Criteria\n\n"
               "| ID | Skenario | Cara verifikasi | Sumber |\n|---|---|---|---|\n"
               "| `AC-1` | label Pesan tampil | test otomatis | `SC-1` |\n")
AC_HEAD = "## Cakupan Acceptance Criteria\n| AC | Vonis | Bukti |\n|---|---|---|\n"


@pytest.mark.regression("J41")
@pytest.mark.parametrize("evidence, ok", [("sudah dicek", False),
                                          ("`src/features/order/OrderButton.tsx:1`", False),
                                          ("`test`", False),
                                          ("`src/features/order/OrderButton.test.tsx:1`", True)])
def test_j41_bukti_ac_ditagih(fe_minor_chain, evidence, ok):
    write_files(fe_minor_chain, {f"{FE_MINOR_TD}/CONTRACT.md": CONTRACT_AC})
    text = fe_review_md(fe_minor_chain).replace(AC_HEAD, AC_HEAD + f"| `AC-1` | terbukti | {evidence} |\n")
    write_files(fe_minor_chain, {REVIEW: text})
    _, _, c = review(fe_minor_chain)
    assert (c["AC"]["status"] == "PASS") is ok, c["AC"]
