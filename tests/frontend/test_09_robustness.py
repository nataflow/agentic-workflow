"""Regresi 09 E12–E16 — frontend: pembanding akar, kesegaran review, subjek, pagar reviewer, `..`."""
import json

import pytest

from conftest import FE_MINOR_TD as TD, FE_SKILLS, PLUGINS, commit, fe_run, load_module, run_script, write_files

LIB = load_module(FE_SKILLS / "_common" / "precondition_lib.py", "fe_lib_09")
GUARD = PLUGINS / "frontend" / "hooks" / "guard_bash.py"
REVIEWER = "frontend:code-reviewer"
TASK = ("---\nstatus: ACTIVE\nlane: HOTFIX_MINOR\nsections: \n---\n# x\n\n## Chain\n\n- [ ] BRIEF\n")
AKAR = ("\n## Riwayat Rantai\n\n- 1 · akar · base 0000000 · lane HOTFIX_MINOR · sections - · akar 000000000000 · "
        "waktu 2026-10-13T00:00:00Z\n")
OTHER_TD = "frontenddev/docs/2609260000-akar"


# --- E12 ---------------------------------------------------------------------------------------

@pytest.mark.regression("E12")
def test_e12_akar_tanpa_subjek_kunci_tetap_dibandingkan(make_repo):
    repo = make_repo({f"{OTHER_TD}/TASK.md": TASK + AKAR})   # pembanding = kejadian `akar`, bukan subjek apa pun
    assert LIB.lane_tamper(repo, OTHER_TD) == ""
    p = repo / OTHER_TD / "TASK.md"
    p.write_text((TASK + AKAR).replace("lane: HOTFIX_MINOR\nsections: ", "lane: FULL_PIPELINE\nsections: flow"),
                 encoding="utf-8")
    assert "berubah di luar akar" in LIB.lane_tamper(repo, OTHER_TD)


@pytest.mark.regression("E12")
def test_e12_akar_belum_terkunci_tanpa_vonis(make_repo):
    repo = make_repo({f"{OTHER_TD}/TASK.md": TASK})
    assert LIB.lane_tamper(repo, OTHER_TD) == ""


# --- E13 ---------------------------------------------------------------------------------------

@pytest.mark.regression("E13")
def test_e13_kode_sesudah_review_basi_apa_pun_subjeknya(fe_minor_chain):
    assert LIB.review_is_fresh(fe_minor_chain, TD) is True
    write_files(fe_minor_chain, {"src/features/order/OrderButton.tsx": "export const OrderButton = () => 1;\n"})
    commit(fe_minor_chain, "chore: rapikan", "src/features/order/OrderButton.tsx")
    assert LIB.review_is_fresh(fe_minor_chain, TD) is False


@pytest.mark.regression("E13")
def test_e13_commit_non_kode_sesudah_review_tetap_segar(fe_minor_chain):
    write_files(fe_minor_chain, {"frontenddev/reviews/audit.md": "# Audit\n"})
    commit(fe_minor_chain, "docs(review): tandai temuan", "frontenddev/reviews/audit.md")
    assert LIB.review_is_fresh(fe_minor_chain, TD) is True


@pytest.mark.regression("24 K9")
def test_review_tanpa_head_tidak_segar(fe_minor_chain):
    review = fe_minor_chain / TD / "REVIEW.md"
    review.write_text(review.read_text(encoding="utf-8").replace("head: ", "head_lama: "), encoding="utf-8")
    assert LIB.review_is_fresh(fe_minor_chain, TD) is False


# --- E14 ---------------------------------------------------------------------------------------

@pytest.mark.regression("E14")
def test_e14_revisi_bersubjek_meleset_tetap_terhitung(make_repo):
    """Subjek commit yang diketik model tidak lagi ada (Langkah 24): tiap kejadian `draft` sesudah yang pertama
    adalah revisi, apa pun yang diketik di sekitarnya; reopen hop lain tetap batas putaran."""
    drafts = "".join(f"- {n} · draft FLOW · sidik {n:012d} · waktu 2026-10-13T00:00:00Z\n" for n in (2, 3, 4))
    repo = make_repo({f"{OTHER_TD}/TASK.md": TASK + AKAR + drafts})
    assert LIB.revisions_since_open(repo, OTHER_TD, "FLOW") == 2
    write_files(repo, {f"{OTHER_TD}/TASK.md": TASK + AKAR + drafts
                       + "- 5 · reopen BRIEF · target BRIEF · waktu 2026-10-13T00:00:00Z · alasan: x\n"
                       + "- 6 · draft FLOW · sidik 000000000006 · waktu 2026-10-13T00:00:00Z\n"})
    assert LIB.revisions_since_open(repo, OTHER_TD, "FLOW") == 0


# --- E16 ---------------------------------------------------------------------------------------

@pytest.mark.regression("E16")
@pytest.mark.parametrize("raw, expected", [
    ("./frontenddev/docs/2609260000-akar/", "frontenddev/docs/2609260000-akar"),
    ("frontenddev/./docs//2609260000-akar", "frontenddev/docs/2609260000-akar"),
    ("frontenddev/docs/../../etc", "frontenddev/docs/../../etc"),
])
def test_e16_normalize_taskdir_mempertahankan_dotdot(raw, expected):
    assert LIB.normalize_taskdir(raw) == expected
    assert bool(LIB.TASKDIR_PATTERN.match(expected)) == (".." not in expected)


@pytest.mark.regression("E16")
def test_e16_review_round_menolak_taskdir_keluar_repo(tmp_path, make_repo):
    repo = make_repo()
    r = fe_run(repo, "_common/review_round.py", "open", "--taskdir", "frontenddev/docs/../../../luar",
               "--gate", "plan")
    assert r.returncode == 1 and "tidak berpola" in r.out and "Traceback" not in r.out
    assert not (tmp_path / "luar").exists()


@pytest.mark.regression("E16")
def test_e16_chain_menolak_taskdir_keluar_repo(make_repo):
    r = fe_run(make_repo(), "_common/chain.py", "status", "--taskdir", "frontenddev/docs/../../x")
    assert r.returncode != 0 and "tidak berpola" in r.out and "Traceback" not in r.out


# --- E15: pagar hook `frontend:code-reviewer` ------------------------------------------------

def hook(repo, *, cmd=None, tool="Bash", file_path=None, agent=REVIEWER):
    ti = {"command": cmd} if tool == "Bash" else {"file_path": file_path, "content": "x"}
    data = {"cwd": str(repo), "tool_name": tool, "tool_input": ti, "hook_event_name": "PreToolUse"}
    if agent:
        data.update(agent_type=agent, agent_id="a1")
    return run_script(GUARD, "hook", stdin=json.dumps(data))


@pytest.fixture
def repo(make_repo):
    root = make_repo({"src/a.ts": "x\n", f"{OTHER_TD}/TASK.md": TASK})
    commit(root, "init")
    return root


def test_e15_hooks_json_mendaftarkan_pagar():
    d = json.loads((PLUGINS / "frontend/hooks/hooks.json").read_text(encoding="utf-8"))
    entry = d["hooks"]["PreToolUse"][0]
    assert entry["matcher"] == "Bash|Edit|Write" and "guard_bash.py" in entry["hooks"][0]["command"]


@pytest.mark.regression("E15")
@pytest.mark.parametrize("cmd", [
    "git diff abc123..HEAD -- src/a.ts", "git log --oneline -5", "git status --porcelain",
    "git --no-pager show HEAD", "ls src",
    # `chain.py` milik plugin ini, bukan sembarang path berakhiran sama (12 J7).
    f"python3 {PLUGINS / 'frontend/skills/_common/chain.py'} files --taskdir " + OTHER_TD,
])
def test_e15_reviewer_boleh_membaca(repo, cmd):
    assert hook(repo, cmd=cmd).returncode == 0


@pytest.mark.regression("E15")
@pytest.mark.parametrize("cmd", [
    "git reset --hard HEAD~3", "git add src/a.ts", "git commit -m x", "git checkout -- src/a.ts",
    "git -c core.pager=sh log", "git diff --output=/tmp/x", "git log; rm -rf src", "npm test",
    "python3 /x/frontend/skills/_common/chain.py approve --taskdir x", "git",
])
def test_e15_reviewer_dilarang_memutasi(repo, cmd):
    r = hook(repo, cmd=cmd)
    assert r.returncode == 2 and "DITOLAK" in r.stderr, (cmd, r.stderr)


@pytest.mark.regression("E15")
@pytest.mark.parametrize("tool, path, code", [
    ("Write", f"{OTHER_TD}/REVIEW.md", 0),
    ("Edit", f"{OTHER_TD}/REVIEW.md", 0),
    ("Edit", "frontenddev/reviews/2609260000-audit.md", 0),
    ("Write", "frontenddev/reviews/2609260000-audit.md", 2),
    ("Edit", "src/a.ts", 2),
    ("Write", f"{OTHER_TD}/TASK.md", 2),
    ("Write", "../luar.md", 2),
])
def test_e15_reviewer_hanya_menulis_review(repo, tool, path, code):
    assert hook(repo, tool=tool, file_path=path).returncode == code


@pytest.mark.regression("E15")
@pytest.mark.parametrize("agent", [None, "frontend:code-implementor", "backend:code-reviewer"])
def test_e15_agent_lain_dan_main_loop_tidak_dipagar(repo, agent):
    assert hook(repo, cmd="git reset --hard HEAD", agent=agent).returncode == 0


@pytest.mark.regression("E15")
def test_e15_input_rusak_untuk_reviewer_fail_closed(repo):
    data = {"cwd": str(repo), "tool_name": "Bash", "tool_input": {}, "agent_type": REVIEWER}
    assert run_script(GUARD, "hook", stdin=json.dumps(data)).returncode == 2
