"""Fixture bersama untuk seluruh `tests/`.

Semua test memanggil skrip plugin lewat `subprocess` dengan `sys.executable`,
persis seperti hook dan skill memanggilnya, sehingga yang diuji adalah perilaku
berkas yang benar-benar dikirim ke user.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

import pytest

# Jangan tinggalkan __pycache__ di src/plugins/ (lint G1): berlaku untuk import di proses
# pytest dan untuk subprocess yang mewarisi os.environ.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

REPO = Path(__file__).resolve().parents[1]
PLUGINS = REPO / "src" / "plugins"

BE_PROFILE_MD = ("stack", "module-structure", "domain-map", "surface-map", "code-conventions",
                 "anti-patterns", "invariants", "commands")
FE_PROFILE_MD = ("stack", "structure", "surface-map", "invariants", "commands", "layer-adoption",
                 "visual", "drift", "manual-notes")

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
}


def git(repo: Path, *args: str) -> str:
    env = {**os.environ, **GIT_ENV}
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    assert out.returncode == 0, out.stderr
    return out.stdout


def write_files(root: Path, files: Dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def be_profile(root: Path, stack: str, *, legacy: bool = False, source_root: str = "src",
               extra: Optional[dict] = None) -> Path:
    """Profil backenddev lengkap di `.claude/profile/backenddev/` (atau lokasi lama)."""
    d = root / ".claude" / "profile" / ("" if legacy else "backenddev")
    d.mkdir(parents=True, exist_ok=True)
    data = {"project": "x", "stack": stack, "architecture": "layered", "root_namespace": "x",
            "source_root": source_root, "commit_convention": "conventional", "base_branch": "main",
            "branch_convention": "feat/<slug>"}
    if not legacy:
        data = {"plugin": "backenddev", **data}
    data.update(extra or {})
    (d / "index.json").write_text(json.dumps(data) + "\n", encoding="utf-8")
    for f in BE_PROFILE_MD:
        (d / f"{f}.md").write_text(f"# {f}\n", encoding="utf-8")
    return d


def fe_profile(root: Path, stack: str, *, legacy: bool = False, extra: Optional[dict] = None) -> Path:
    """Profil frontenddev lengkap di `.claude/profile/frontenddev/` (atau lokasi lama)."""
    d = root / ".claude" / "profile" / ("" if legacy else "frontenddev")
    d.mkdir(parents=True, exist_ok=True)
    data = {"project": "x", "stack": stack, "platform": "SPA", "framework": "x", "source_root": "src",
            "workspace": "single", "target_app": "", "commit_convention": "conventional"}
    if not legacy:
        data = {"plugin": "frontenddev", **data}
    data.update(extra or {})
    (d / "index.json").write_text(json.dumps(data) + "\n", encoding="utf-8")
    for f in FE_PROFILE_MD:
        (d / f"{f}.md").write_text(f"# {f}\n", encoding="utf-8")
    return d


def run_script(path: Path, *args: str, cwd: Optional[Path] = None, stdin: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, **GIT_ENV}
    return subprocess.run([sys.executable, str(path), *args], input=stdin, capture_output=True,
                          text=True, cwd=str(cwd) if cwd else None, env=env, timeout=60)


def run_hook(plugin: str, cwd: Path, *, stdin: Optional[str] = None, explain: bool = False):
    """Jalankan `hooks/detect.py`. Mengembalikan (proc, payload|None)."""
    if stdin is None:
        stdin = json.dumps({"cwd": str(cwd), "hook_event_name": "SessionStart", "source": "startup"})
    args = ["--plugin", plugin] + (["--explain"] if explain else [])
    proc = run_script(PLUGINS / plugin / "hooks" / "detect.py", *args, stdin=stdin)
    out = proc.stdout.strip()
    return proc, (json.loads(out) if out else None)


def load_module(path: Path, name: str):
    """Muat satu modul skrip per path dengan nama unik, tanpa meninggalkan jejak di `sys.path`.

    backenddev dan frontenddev sama-sama punya `precondition_lib` (dan `detect`). Modul yang
    ikut terimpor lewat direktori induk `path` dibuang dari `sys.modules` sesudahnya, supaya
    test plugin lain di sesi pytest yang sama tidak mendapat salinan plugin yang salah.
    """
    before = set(sys.modules)
    sys.path.insert(0, str(Path(path).parent))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(Path(path).parent))
        for k in set(sys.modules) - before - {name}:
            del sys.modules[k]
    return module


@pytest.fixture
def make_repo(tmp_path):
    """`make_repo(files, name="repo", git_init=True)` → path repo fixture."""
    def _make(files: Optional[Dict[str, str]] = None, name: str = "repo", git_init: bool = True) -> Path:
        root = tmp_path / name
        root.mkdir(parents=True, exist_ok=True)
        if git_init:
            git(root, "init", "-q")
        write_files(root, files or {})
        return root
    return _make


# --- Rantai backenddev (Langkah 2) -------------------------------------------------------------

BE_SKILLS = PLUGINS / "backenddev" / "skills"
TD = "backenddev/docs/2609240900-order-fix"


def brief(repo: Path, nn: str, unit: str, status: str, body: str = "# Brief\n", **extra: str) -> Path:
    """Tulis `{TD}/brief-<nn>-<unit>.md` berfrontmatter minimal; `extra` menambah field."""
    fm = "".join(f"{k}: {v}\n" for k, v in extra.items())
    path = repo / TD / f"brief-{nn}-{unit}.md"
    path.write_text(f"---\ntitle: {unit}\nsource: TASK.md\nrisk: MINOR\nstatus: {status}\n"
                    f'commit_message: "fix(order): implement {unit}"\n{fm}---\n{body}', encoding="utf-8")
    return path


def commit(repo: Path, msg: str, *paths: str) -> str:
    git(repo, "add", *(paths or ("-A",)))
    git(repo, "commit", "-qm", msg)
    return git(repo, "rev-parse", "--short=7", "HEAD").strip()


def be_run(repo: Path, skill_script: str, *args: str) -> subprocess.CompletedProcess:
    """Jalankan `skills/<skill_script>` dengan cwd = repo."""
    return run_script(BE_SKILLS / skill_script, *args, cwd=repo)


def be_checks(repo: Path, skill_script: str, *args: str) -> Dict[int, dict]:
    """Jalankan skrip prasyarat ber-`--json`, kembalikan {id: check}."""
    proc = be_run(repo, skill_script, "--json", *args)
    assert proc.stdout.strip(), proc.stderr
    return {c["id"]: c for c in json.loads(proc.stdout)["checks"]}


@pytest.fixture
def chain_repo(make_repo):
    """Repo ber-profil backenddev (stack go), `{TD}/TASK.md` ter-commit di `main`; HEAD di branch kerja `fix/order-fix`."""
    root = make_repo({
        ".gitignore": ".explore/\n",
        f"{TD}/TASK.md": ("---\nchain: BRIEF\nrisk: MINOR\nstatus: ACTIVE\n---\n# Order fix\n"
                          "## Success Criteria\n- SC-1 lock\n- SC-2 endpoint\n"),
        "src/order.go": "package order\n",
    })
    git(root, "checkout", "-q", "-b", "main")
    be_profile(root, "go")
    write_files(root, {".claude/profile/backenddev/commands.md":
                       "## Commands\n- build: go build ./...\n- test: go test ./...\n"})
    commit(root, "init")
    git(root, "checkout", "-q", "-b", "fix/order-fix")   # rantai berjalan di branch kerja, bukan base
    return root


# --- Rantai frontenddev (Langkah 4) ------------------------------------------------------------

FE_SKILLS = PLUGINS / "frontenddev" / "skills"
FE_FIX = REPO / "tests" / "frontenddev" / "fixtures"
FE_TD = "frontenddev/docs/2609241200-orders-lacak"


def fe_run(repo: Path, skill_script: str, *args: str) -> subprocess.CompletedProcess:
    """Jalankan `frontenddev/skills/<skill_script>` dengan cwd = repo; stdout+stderr digabung di `.out`."""
    proc = run_script(FE_SKILLS / skill_script, *args, cwd=repo)
    proc.out = proc.stdout + proc.stderr
    return proc


def fe_commit(repo: Path, subject: str, *paths: str) -> str:
    """Commit `paths` (default `CONTRACT.md`) dengan subjek `docs(orders-lacak): <subject>`."""
    return commit(repo, f"docs(orders-lacak): {subject}", *(paths or (f"{FE_TD}/CONTRACT.md",)))


def fe_brief(repo: Path, nn: str, status: str = "READY", step: str = "Tambah tombol Lacak di OrderDetail.",
             remedies: str = "", total: int = 1) -> str:
    """Tulis `brief-<nn>-orders-lacak-button.md` dari fixture; kembalikan path relatifnya."""
    rel = f"{FE_TD}/brief-{nn}-orders-lacak-button.md"
    sha = git(repo, "rev-list", "--max-parents=0", "--abbrev=7", "--abbrev-commit", "HEAD").strip()
    text = (FE_FIX / "brief_button.md").read_text(encoding="utf-8")
    for key, value in {"status": status, "sha": sha, "nn": nn, "total": total,
                       "remedies": remedies, "step": step}.items():
        text = text.replace("{" + key + "}", str(value))
    write_files(repo, {rel: text})
    return rel


@pytest.fixture
def fe_chain_repo(make_repo):
    """Repo FAST_FORWARD frontenddev: akar `TASK.md` terkunci di `main`, `CONTRACT.md` DRAFT tertulis (belum di-commit)."""
    root = make_repo({
        ".gitignore": ".explore/\n",
        f"{FE_TD}/TASK.md": (FE_FIX / "task_fast_forward.md").read_text(encoding="utf-8"),
        "src/features/orders/OrderDetail.tsx": "export function OrderDetail() { return null }\n",
    })
    git(root, "checkout", "-q", "-b", "main")
    fe_profile(root, "react-vite")
    write_files(root, {".claude/profile/frontenddev/commands.md":
                       "| Perintah | Status |\n|---|---|\n| `pnpm typecheck` | OK |\n| `pnpm test` | OK |\n"})
    assert fe_run(root, "_common/chain.py", "init", "--taskdir", FE_TD).returncode == 0
    sha = commit(root, "docs(orders-lacak): kunci TASK sebagai akar rantai")
    write_files(root, {f"{FE_TD}/CONTRACT.md":
                       (FE_FIX / "contract_valid.md").read_text(encoding="utf-8").replace("{sha}", sha)})
    return root


def fe_evidence(repo: Path, n, verdict: str = "PASS", mechanical: int = 0, semantic: int = 0) -> str:
    """Balikan `contract-reviewer` ronde `n` di laci `.explore/` (bukti `record --evidence`)."""
    rel = f"{FE_TD}/.explore/contract-review-r{n}.md"
    write_files(repo, {rel: f"## Contract Review\n- Verdict: {verdict}\n- Ronde: {n}\n"
                            f"- BLOCKER: {mechanical} [MEKANIS] · {semantic} [SEMANTIK]\n"})
    return rel


def fe_round(repo: Path, verdict: str = "PASS", gate: str = "contract", mechanical: int = 0,
             semantic: int = 0) -> None:
    """Satu ronde reviewer lengkap: `open` → laporan/bukti → `record`."""
    rr = ("_common/review_round.py",)
    opened = fe_run(repo, *rr, "open", "--taskdir", FE_TD, "--gate", gate)
    assert opened.returncode == 0, opened.out
    n = opened.out.split("ronde ")[1].split("/")[0]
    extra = ["--mechanical", str(mechanical), "--semantic", str(semantic)]
    if gate == "plan":
        write_files(repo, {f"{FE_TD}/REVIEW-PLAN.md":
                           f'---\nverdict: {verdict}\nround: "{n}"\n---\n\n# Plan Review\n'})
    else:
        extra += ["--evidence", fe_evidence(repo, n, verdict, mechanical, semantic)]
    r = fe_run(repo, *rr, "record", "--taskdir", FE_TD, "--gate", gate, "--verdict", verdict, *extra)
    assert r.returncode == 0, r.out


def fe_approved_chain(repo: Path) -> None:
    """CONTRACT dan BRIEF (brief 01) disetujui lewat jalur SKILL: ronde PASS → commit skrip → approve."""
    def run(*args):
        r = fe_run(repo, *args)
        assert r.returncode == 0, r.out
    fe_round(repo)
    run("_common/review_round.py", "commit", "--taskdir", FE_TD, "--gate", "contract",
        "--subject", "docs(orders-lacak): draft CONTRACT.md")
    run("_common/chain.py", "approve", "--taskdir", FE_TD, "--row", "CONTRACT", "--answer", "Setujui")
    fe_brief(repo, "01")
    fe_round(repo, gate="plan")
    run("_common/review_round.py", "commit", "--taskdir", FE_TD, "--gate", "plan",
        "--subject", "docs(orders-lacak): draft breakdown (1 briefs)")
    run("_common/chain.py", "approve", "--taskdir", FE_TD, "--row", "BRIEF", "--answer", "Setujui")


FE_MINOR_TD = "frontenddev/docs/2609231200-order-checkout"


@pytest.fixture
def fe_minor_chain(tmp_path):
    """Rantai HOTFIX_MINOR frontenddev: `closing review PASS` ter-commit, `REPORT.md` tertulis belum di-commit."""
    root = tmp_path / "repo"
    proc = subprocess.run(["bash", str(FE_FIX / "minor_chain_reviewed.sh"), str(root), str(FE_SKILLS)],
                          capture_output=True, text=True, env={**os.environ, **GIT_ENV})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return root


FE_DIMENSIONS = ["Layer Boundaries", "Data Flow & DTO", "API Layer", "State Scope & Ownership",
                 "UI & 6-State Branches", "Platform & Framework Boundary", "Error Handling", "Performance & Leaks",
                 "Test Quality"]
FE_P2_FINDING = ("### [P2-1] Label tidak memakai i18n\n\n> Status: PLANNED\n\n"
                 "- **Location**: `src/features/order/OrderButton.tsx:1`\n"
                 "- **Violation**: Dimensi 5 — label literal di presentasi.\n"
                 "- **Evidence**: `<button>Pesan</button>`\n"
                 "- **Recommendation**: ambil label dari kamus i18n.\n")


def fe_review_md(repo: Path, **over: str) -> str:
    """REVIEW.md rantai `fe_minor_chain` — default: WARNING sah ber-`[P2-1]` PLANNED (fixture positif L4.2).

    `over` menimpa field: taskdir, stack, verdict, p2, reviewed_at, h1, summary_status, total,
    verification, sc_evidence, findings, done, dims (daftar 9 status), dim_names (daftar 9 nama).
    """
    base = git(repo, "log", "--diff-filter=A", "--format=%h", "--", f"{FE_MINOR_TD}/TASK.md").split()[-1]
    # Tanggal commit akar, bukan literal: `reviewed_at` < tanggal akar = FAIL, dan akar lahir saat test jalan.
    born = git(repo, "log", "-1", "--format=%cs", base).strip()
    f = {"taskdir": FE_MINOR_TD, "stack": "react-vite", "verdict": "WARNING", "p2": "1",
         "reviewed_at": born, "h1": "# Review Findings — order-checkout",
         "summary_status": "WARNING", "total": "- Total Findings: 1 (0 P1, 1 P2, 0 P3)",
         "verification": "| `test` | HIJAU | 0 |", "sc_evidence": "`src/features/order/OrderButton.test.tsx:1`",
         "findings": FE_P2_FINDING, "done": "terpenuhi",
         "dims": ["PASS"] * 4 + ["P2"] + ["PASS"] * 4, "dim_names": FE_DIMENSIONS, **over}
    dims = "\n".join(f"| {i + 1} | {n} | {s} |" for i, (n, s) in enumerate(zip(f["dim_names"], f["dims"])))
    return f"""---
artifact: REVIEW
taskdir: {f['taskdir']}
stack: {f['stack']}
verdict: {f['verdict']}
p1: 0
p2: {f['p2']}
p3: 0
base: {base}
reviewed_at: {f['reviewed_at']}
---

{f['h1']}

## Summary
- Stack: react-vite
{f['total']}
- Overall Status: {f['summary_status']}

## Verifikasi Penutup
| Perintah | Hasil | Galat baru vs baseline |
|---|---|---|
{f['verification']}

## Cakupan Success Criteria
| SC | Vonis | Bukti |
|---|---|---|
| `SC-1` | terbukti | {f['sc_evidence']} |

## Cakupan Acceptance Criteria
| AC | Vonis | Bukti |
|---|---|---|

## Temuan

{f['findings']}
## Done Criteria DITUNDA
| Brief | Butir | Vonis | Bukti |
|---|---|---|---|
| brief-01 | pnpm test nol galat baru | {f['done']} | HIJAU |

## Umpan balik profil
| Berkas | Pola warisan | Pola pengganti | Sumber |
|---|---|---|---|
| — | — | — | — |

## 9 Dimensi
| # | Dimensi | Status |
|---|---|---|
{dims}
"""


# --- Analyst: blok reviewer tiket (09 E9) ------------------------------------------------------

TICKET_PY = PLUGINS / "analyst" / "skills" / "_common" / "ticket.py"


def ticket_block(root: Path, ticketdir: str, verdict: str, *, sidik: Optional[str] = None,
                 cwd: Optional[Path] = None) -> str:
    """Blok `## Ticket Review` sah untuk `ticket.py review --report -`.

    `sidik` default = keluaran `check --gate spec` sekarang, persis yang disalin pendispatch ke
    prompt reviewer; berikan nilai lain untuk mensimulasikan draft yang berubah sesudah dispatch.
    """
    if sidik is None:
        chk = run_script(TICKET_PY, "check", "--gate", "spec", "--ticketdir", ticketdir, "--json", cwd=cwd or root)
        sidik = json.loads(chk.stdout).get("sidik", "-")
    return (f"## Ticket Review\n- Verdict: {verdict}\n- Sidik: {sidik}\n- Ronde: 1\n"
            f"- BLOCKER: 0 [MEKANIS] · 0 [SEMANTIK]\n\n**BLOCKER:**\n- —\n\n**ADVISORY:**\n- —\n")


def ticket_review(root: Path, ticketdir: str, verdict: str, *, cwd: Optional[Path] = None,
                  sidik: Optional[str] = None) -> subprocess.CompletedProcess:
    """`ticket.py review` dengan blok reviewer bersidik (jalur yang diperintahkan `analyst:spec`)."""
    return run_script(TICKET_PY, "review", "--ticketdir", ticketdir, "--verdict", verdict, "--report", "-",
                      cwd=cwd or root, stdin=ticket_block(root, ticketdir, verdict, sidik=sidik, cwd=cwd))
