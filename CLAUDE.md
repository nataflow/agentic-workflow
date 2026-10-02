# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`nataflow` is a Claude Code **plugin marketplace**, not an application. It ships five plugins under
`src/plugins/`: `analyst`, `backend`, `frontend`, `quickdev`, and `nataflow`. Each plugin is a set of skills
(`SKILL.md` prose), subagents (`agents/*.md`), hooks, and stdlib-only Python scripts that skills call to
enforce their gates mechanically. Everything under `src/plugins/<plugin>/` is copied into the user's
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
  `skills/_common/run_verification.py`. Tests assert equality; edit both together. (`guard_bash.py`,
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
  (evidence for `TECH`, question context otherwise). `notulen` turns rough meeting notes into a gitignored
  `NOTULEN.md` (`skills/notulen/scripts/notulen.py`), optionally mirrored to nataflow as a `notes.meeting`
  document. `skills/_common/ticket.py` is the state machine; a READY ticket is handed to
  `backend:tech-lead`/`frontend:lead` as `ticket_source`.
- **backend** — entry `backend:tech-lead` picks a lane/risk/taskdir, then `backend:analyst` orchestrates a
  document chain (TASK → optional BRD → optional PRD → briefs) with reviewer subagents and user approval,
  then `backend:architect` runs READY briefs sequentially through `code-implementor` (commits per brief),
  closing verification, a single `code-reviewer` pass, and `report`. Artifacts live in the *user's* repo
  under `backenddev/docs/<taskdir>/`.
- **frontend** — same shape with entry `frontend:lead`: TASK → FLOW (ux-design) → UI (ui-design) →
  CONTRACT → briefs → architect → review → report, under `frontenddev/docs/<taskdir>/`. Progress is an
  approval **ledger** managed by `_common/chain.py`; reviewer rounds are tracked by
  `_common/review_round.py` with a "sidik" (content fingerprint) that the reviewer must echo.
- **quickdev** — lightweight, no taskdir and no subagents: `repo-profile.md` + one `plan/<task>.md`
  guarded by `_common/plan_lock.py`.
- **nataflow** — direct work against the nataflow server over MCP, no repo artifacts. `create-artifact`
  writes a self-contained HTML page, gates it with `skills/create-artifact/scripts/artifact.py check`, and
  upserts it under the MCP key's project via the `nataflow-api` `*_artifact` MCP tools. Model-invocable.

Repo profiles are per plugin: `.claude/profile/backenddev/` and `.claude/profile/frontenddev/`
(`index.json` + fixed set of `.md` files; see `BE_PROFILE_MD`/`FE_PROFILE_MD` in `tests/conftest.py`).
The legacy flat `.claude/profile/` location is migrated by `migrate_profile.py`.

### Hooks (backend and frontend only)

- **SessionStart** → `hooks/detect.py --plugin <name>` detects stack/profile and injects a gate block
  (text from `hooks/gate_text.py`) telling the model which requests must go through the entry skill.
  Output must be empty or valid JSON. A user-repo `.claude/workflow` file listing plugin names opts
  hooks in/out. `precondition_lib.py` imports `detect.py` so hook and scripts reach the same verdict.
- **PreToolUse** (`Bash|Edit|Write`) → `hooks/guard_bash.py hook` fences the plugin's subagents by
  `agent_type`. It is **fail-closed** (internal error ⇒ deny, exit 2). The implementor may only touch
  paths in a lease file written by `architect` to `<git-dir>/nataflow/lease-<plugin>.json`; explorers may
  only write `.explore/*.md`; reviewers are read-only except their report. Calls without a matching
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
- Chain fixtures: `chain_repo` (backend taskdir on a work branch), `fe_chain_repo`, `fe_approved_chain`,
  `fe_round`, `fe_minor_chain` (built by `tests/frontend/fixtures/minor_chain_reviewed.sh`), and
  `ticket_review` for analyst.
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
