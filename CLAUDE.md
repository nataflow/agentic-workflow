# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`nataflow` is a Claude Code **plugin marketplace**, not an application. It ships seven plugins under
`src/plugins/`: `analyst`, `backend`, `frontend`, `quickdev`, `nataflow`, `product`, and `fullstack`. Each
plugin is a set of skills (`SKILL.md` prose), subagents (`agents/*.md`), hooks, and stdlib-only Python scripts
that skills call to enforce their gates mechanically. Everything under `src/plugins/<plugin>/` is copied into the user's
plugin cache, so dev-only files (tests, `__pycache__`, `src/plugins` paths in prose) must not live there.

All prose, skill text, commit messages, and issue docs are written in **Indonesian**. Keep that language
when editing them.

## Commands

pytest is not installed in the system Python here; run it through `uvx` (or `python3 -m pytest` if
available).

```sh
uvx pytest                                         # full suite (testpaths = tests)
uvx pytest tests/backend/test_12_guard.py          # one file
uvx pytest tests/backend/test_12_guard.py -k j8    # tests matching a keyword
uvx --python 3.9 pytest -q                         # check against the 3.9 minimum
python3 scripts/lint_plugins.py                    # static lint; --json, --strict, --ignore IDs, --base origin/main
claude plugin validate .                           # before a release
```

CI (`.github/workflows/ci.yml`) runs pytest on Python 3.9–3.13 plus macOS, validates every
`plugin.json`/`marketplace.json`/`hooks.json` as JSON, runs shellcheck on tracked `*.sh`, and runs
`lint_plugins.py` with an empty `LINT_IGNORE` and `--base origin/<base>` on PRs.

## Hard constraints

- **Python ≥ 3.9, stdlib only** for every script and hook. No `match`, no `X | Y` type unions, no
  third-party imports. `tomllib` is optional (3.11+) and must degrade gracefully.
- **Version bump per PR.** `version` lives only in `src/plugins/<plugin>/.claude-plugin/plugin.json`,
  never in `marketplace.json`. Any change under `src/plugins/<plugin>/` requires bumping that plugin's
  version; lint M7 (`--base`) enforces it. Releases are usually a separate `chore(release)` commit.
- `description` and `author` in each `marketplace.json` entry must equal `plugin.json` (lint M4).
- A skill whose description starts with "Dipanggil …" is internal and must set `user-invocable: false`
  (lint F3). quickdev skills use `disable-model-invocation: true` so only the user can invoke them.
- Skill/agent frontmatter may only use the fields whitelisted in `scripts/lint_plugins.py`
  (`SKILL_FIELDS`, `AGENT_FIELDS`); description length cap is 1536.
- Paths referenced in prose as `${CLAUDE_PLUGIN_ROOT}/...` or backticked relative paths are checked for
  existence by the lint (R-checks). Rename a file → update every reference.
- **Byte-identical copies across `backend` and `frontend`**: `hooks/detect.py`,
  `skills/profile/scripts/migrate_profile.py`, `skills/_common/verify_scope.py`,
  `skills/_common/run_verification.py`, `skills/_common/docs_git.py`. Tests assert equality; edit both together. (`guard_bash.py`,
  `precondition_lib.py`, and `validate_doc.py` are plugin-specific and differ on purpose, though some
  helper functions in `guard_bash.py` are asserted identical.)

## Architecture

### Skills are prose; scripts are the gates

Each skill's `SKILL.md` describes phases, but the correctness guarantees live in Python:
`skills/<skill>/scripts/check_preconditions.py` (exit 0 = PASS, 1 = FAIL, `--json` for machine output)
runs before a skill's first phase, and `skills/_common/*.py` holds the shared state machines, validators,
and verification runners. When SKILL prose and a script disagree, the script is the contract; many recent
fixes are "prosa selaras skrip" (prose aligned to script). Changing a gate means changing the script, its
tests, and the SKILL/README/`flow/*.md` text together.

Skill subdirectories follow a fixed convention: `references/` (loaded on demand), `templates/` (document
skeletons), `dispatcher/` (prompts used to dispatch subagents), `scripts/`, and for `profile`, `stacks/`
(per-stack adapters that must satisfy `stacks/_CONTRACT.md`).

### The plugins

- **analyst** — turns a stakeholder request into a non-technical `TICKET.md` (`intake` → `elicit` →
  `spec`, reviewed by `ticket-reviewer`). `elicit` reads code only through the shallow `code-scout` subagent
  (evidence for `TECH`, question context otherwise). Two to five requests in one message become a batch
  (`skills/intake/references/batch.md`): `ticket.py new --urutan k/N` allocates every ticketdir up front, scouts
  run in parallel, then tickets finish one at a time. `notulen` turns rough meeting notes into a gitignored
  `NOTULEN.md` (`skills/notulen/scripts/notulen.py`), may dispatch `code-scout` in `KONTEKS` mode to sharpen
  clarifying questions (never as notulen content; `check` rejects `path:baris`), and is optionally mirrored to
  nataflow as a `notes.meeting` document. `skills/_common/ticket.py` is the state machine; a READY ticket is handed to
  `backend:tech-lead`/`frontend:lead` as `ticket_source`.
- **backend** — entry `backend:tech-lead` picks a lane/risk/taskdir, then `backend:analyst` orchestrates a
  document chain (TASK → optional BRD → optional PRD → briefs) with reviewer subagents and user approval,
  then `backend:architect` runs READY briefs sequentially through `code-implementor` (commits per brief),
  closing verification, a single `code-reviewer` pass, and `report`. Artifacts live in the *user's* repo
  under `backenddev/docs/<taskdir>/`, which is gitignored and never committed (step 24). Integrity is a content
  seal on disk written by `skills/_common/doc_seal.py`: `root` (`base_commit` = HEAD), `approve` (BRD/PRD
  `approved_seal` + ledger tick `@ APPROVED <sidik12>`), `lock-briefs` (`sidik_kontrak`), `tick --hop BRIEF`,
  `cabut-halt` (`HALT.md` `status: DICABUT`). Brief DONE is proven by a code commit with the brief's
  `commit_message` in `base_commit..HEAD`; `REVIEW.md` is stale once code lands after its `range:` head.
- **frontend** — same shape with entry `frontend:lead`: TASK → FLOW (ux-design) → UI (ui-design) →
  CONTRACT → briefs → architect → review → report, under `frontenddev/docs/<taskdir>/` (gitignored, never
  committed). Progress is an approval **ledger** managed by `_common/chain.py`, which also writes the
  numbered `## Riwayat Rantai` event log at the end of `TASK.md` (`akar`, `draft`, `approve`, `reopen`,
  `eskalasi`, `amandemen`, `abandon`) that replaces doc commits: approval stamps, caps, review epochs, and lane
  replay are read from it, and a malformed log fails every gate closed. `chain.py root` locks the root
  (`base_commit` + root sidik), `draft` records presented content, `amend` re-seals a root amendment; no
  subcommand runs git commit. Reviewer rounds are tracked by `_common/review_round.py` with a "sidik"
  (content fingerprint) that the reviewer must echo. Only code commits remain
  (`feat(<slug>): implement unit NN - …`), and `REVIEW.md` carries `head:` for freshness.
- **quickdev** — lightweight, no taskdir and no subagents: `repo-profile.md` + one `plan/<task>.md`
  guarded by `_common/plan_lock.py`.
- **nataflow** — direct work against the nataflow server over MCP, no repo artifacts. `create-artifact`
  writes a self-contained HTML page, gates it with `skills/create-artifact/scripts/artifact.py check`, and
  upserts it under the MCP key's project via the `nataflow-api` `*_artifact` MCP tools. Model-invocable.
- **product** — initiation of a new product (empty folder, mode `NEW_PRODUCT`), a new feature, or an
  improvement (codebase, `NEW_FEATURE`/`IMPROVEMENT`) into `product/<slug>/CHARTER.md` with six pillars
  (Purpose, Actors, Business Process, Business Rules, Success Criteria, Scope). Entry `product:init` runs a
  minimum-context guard (`charter.py guard`) that rejects over-general requests before any folder exists, then
  `product:discover` (elicitation; `code-scout` maps current roles/flow/rules in codebase modes) and
  `product:spec` (card, `charter-reviewer`, approval). `skills/_common/charter.py` is the state machine; scope
  items carry stable `S<n>` IDs prepared for a future hand-off to `analyst`. The backend/frontend gate texts
  exempt `/product:*`.
- **fullstack** — read-only understanding of many repos from a non-git root that holds them (`<root>/<repo>` or
  `<root>/<proyek>/<repo>`), driven by each repo's backend/frontend profile. One skill `fullstack:explore` with three
  paths: `PETA` (`skills/_common/workspace.py peta` writes `<root>/.fullstack/PETA.md` from profiles and git only,
  no code reading), `TELUSUR` (parallel `repo-scout` subagents per repo, report under `.fullstack/explore/` built
  by `explore.py new`, FE→BE and API→API seams computed by `explore.py seam`, gated by `explore.py check`), and
  `ALUR` (how something works inside a repo: parallel `backend-explorer`/`frontend-explorer` subagents, sonnet,
  `Read`/`Grep`/`Glob` only, adapted from the backend/frontend `code-explorer`; report built by `explore.py new
  --jalur ALUR`, no seam; a test pins the read-window numbers to the source agents). Reports without a `jalur`
  frontmatter field are `TELUSUR`. Target
  repos for API→API calls are certain only via user-confirmed `.fullstack/layanan.json`; projects/repos listed
  in `.fullstack/abaikan` (gitignore-style patterns) are skipped by every script. `fullstack_lib.py` copies
  `SKIP_DIRS`/`STACKS` from backend `hooks/detect.py` (a test asserts equality), and `tests/fullstack/
  test_profile_anchor_21.py` pins the backend/frontend profile-template anchors the parser reads. No hooks.

Repo profiles are per plugin: `.claude/profile/backenddev/` and `.claude/profile/frontenddev/`
(`index.json` + fixed set of `.md` files; see `BE_PROFILE_MD`/`FE_PROFILE_MD` in `tests/conftest.py`).
The legacy flat `.claude/profile/` location is migrated by `migrate_profile.py`.

Taskdir docs live outside git (step 24): `skills/_common/docs_git.py` writes the self-ignoring marker
`<prefix>/docs/.gitignore` (`*`) from the entry gates (backend `tech-lead` check 3, frontend `task` check 10)
and runs the one-time `migrate` for repos that still track taskdir docs (route `MIGRASI`). Without
`.claude/nataflow.json` the `task` gate warns that taskdir docs exist only on that disk. Profiles and
repo-level docs (`backenddev/issues/`, `docs/api/`, `frontenddev/reviews/`) stay committed.

### Hooks (backend and frontend only)

- **SessionStart** → `hooks/detect.py --plugin <name>` detects stack/profile and injects a gate block
  (text from `hooks/gate_text.py`) telling the model which requests must go through the entry skill.
  Output must be empty or valid JSON. A non-git cwd with ≥ 2 direct git children is a multi-repo root:
  the block only points at the plugin's child repo(s) and `/fullstack:explore` (for all code understanding there,
  not the built-in `Explore` subagent) instead of gating. A
  user-repo `.claude/workflow` file listing plugin names opts hooks in/out. `precondition_lib.py` imports `detect.py` so hook and scripts reach the same verdict.
- **PreToolUse** (`Bash|Edit|Write`) → `hooks/guard_bash.py hook` fences the plugin's subagents by
  `agent_type`. It is **fail-closed** (internal error ⇒ deny, exit 2). The implementor may only touch
  paths in a lease file written by `architect` to `<git-dir>/nataflow/lease-<plugin>.json`; explorers may
  only write `.explore/*.md`; reviewers are read-only except their report. The frontend implementor may
  write its taskdir `report-NN.md` even though the path is gitignored. Calls without a matching
  `agent_type` pass through.

### Reference docs in this repo

- `flow/<plugin>.md` — the authoritative end-to-end map of each plugin (component table, per-skill flow,
  artifacts and status lifecycles, hooks, failure/recovery). Update it when behavior changes.
- `issues/NN-*.md` — work plans per "Langkah" (step), each with blast radius, decisions, and stages.
  Finding IDs (e.g. `12 J42`, `13 Q7`, `11 H20`) are cited in commit subjects and test names.
  `ISSUES.md` at the root is gitignored scratch.

## Tests

Tests live outside `src/` so they never ship. They invoke plugin scripts via `subprocess` with
`sys.executable` (the same way hooks/skills do) against temporary git repos built by fixtures in
`tests/conftest.py`:

- `make_repo`, `be_profile`/`fe_profile`, `run_script`, `run_hook`, `git`, `commit`.
- Chain fixtures: `chain_repo` (backend taskdir on a work branch, root sealed on disk via `base_commit`),
  `fe_chain_repo` (root locked with `chain.py root`), `fe_approved_chain`, `fe_round`, `fe_minor_chain` (built by
  `tests/frontend/fixtures/minor_chain_reviewed.sh`), and `ticket_review` for analyst. Taskdir docs are never
  committed in fixtures (the ignore marker makes `commit()` without paths skip them), and helpers `fe_lock_root`/`fe_seal_root`/`fe_draft`
  drive `chain.py`.
- product tests import `tests/product_helpers.py` (`from product_helpers import …`): fixture `ws` runs each test
  once per mode (`NEW_PRODUCT`/`NEW_FEATURE`/`IMPROVEMENT`), `empty_ws` is an empty non-git folder, and
  `Workspace.to_closed()`/`to_reviewed()`/`to_approved()` build a charter in each lifecycle state.
- fullstack tests import `tests/fullstack_helpers.py`: `repo(root, rel, be=…, fe=…)` builds a git repo with a
  realistic profile under a multi-repo root, `satu_proyek()` builds `wms/{api,frontend}`, and `run()` returns
  `(proc, json)`.
- `load_module(path, name)` imports a plugin script under a unique name and purges sibling modules,
  because backend and frontend have same-named modules (`precondition_lib`, `detect`).

pytest runs with `--import-mode=importlib` (duplicate test filenames across plugins) and
`xfail_strict = true`. Mark regression tests with `@pytest.mark.regression("<ID>")`. `tests/test_smoke.py`
runs every CLI script across four repo states (normal, no commits, detached HEAD, not a git repo) and
requires `--json` output to always be valid JSON — add new CLI scripts to its `CASES`.
`tests/test_lint_plugins.py` keeps a `deferred` set that must stay in sync with CI's `LINT_IGNORE`.
Keep shell fixtures portable to BSD/macOS (e.g. no `sed -i`).

## Commits

Conventional commits in Indonesian with the issue step and finding IDs in parentheses, e.g.
`fix(frontend): ledger berjangkar commit approve, … (12 J42–J53)` or
`chore(release): naikkan versi frontend ke 0.9.0 dan backend ke 0.10.0 (12)`.
