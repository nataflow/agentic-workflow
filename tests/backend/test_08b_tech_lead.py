"""B14 — tech-lead check 5 mem-parse `kunci: nilai` commands.md; check 6 menilai base_branch dan branch_convention."""
import json

import pytest

from conftest import PLUGINS, be_checks, commit, load_module, write_files

TL = "tech-lead/scripts/check_preconditions.py"
LIB = load_module(PLUGINS / "backend/skills/_common/precondition_lib.py", "pl_b14")
TEMPLATE_EXAMPLE = ("# Commands\n\n"
                    "build: go build ./... [OK] · typecheck: go vet ./... [OK] · lint: golangci-lint run [FAIL]\n"
                    "typecheck-scoped: go build ./<paket>/... [OK] · typecheck-per-brief: ya — inkremental\n"
                    "test: go test ./... [OK] · test-single: go test ./internal/order -run <TestName> [OK]\n"
                    "migration-status: migrate version [DILEWATI (tanpa izin)] · folder db/migrations\n")
CMDS = ".claude/profile/backenddev/commands.md"


def test_b14_parse_contoh_template():
    c = LIB.parse_commands(TEMPLATE_EXAMPLE)
    assert c["build"] == "go build ./... [OK]" and c["test"] == "go test ./... [OK]"
    assert "folder" not in c and c["typecheck-per-brief"].startswith("ya")


def test_b14_parse_abaikan_fence_dan_heading():
    c = LIB.parse_commands("﻿# build: x\n\n```\ntest: palsu\n```\n- test: go test ./...\n")
    assert c == {"test": "go test ./..."}


def _tl(repo, **files):
    write_files(repo, files)
    commit(repo, "c")
    return be_checks(repo, TL, "--root", str(repo))


@pytest.mark.parametrize("text", [
    "# Commands\n\nTidak ada perintah yang bisa dijalankan; build belum disiapkan. Protest dari tim ops.\n",
    "# Commands\n\nbuild: go build ./... [OK]\n",
    "# Commands\n\nbuild: tidak berlaku · test: tidak berlaku\n"])
def test_b14_commands_tanpa_build_test_sah_fail(chain_repo, text):
    assert _tl(chain_repo, **{CMDS: text})[5]["status"] == "FAIL"


@pytest.mark.parametrize("text", [TEMPLATE_EXAMPLE, "# Commands\n\nbuild: tidak berlaku · test: bun test [OK]\n"])
def test_b14_commands_sah_pass(chain_repo, text):
    assert _tl(chain_repo, **{CMDS: text})[5]["status"] == "PASS"


def _index(repo, **kv):
    p = repo / ".claude/profile/backenddev/index.json"
    return json.dumps({**json.loads(p.read_text()), **kv})


def test_b14_branch_convention_tanpa_slug_fail(chain_repo):
    c = _tl(chain_repo, **{".claude/profile/backenddev/index.json": _index(chain_repo, branch_convention="feature-branch")})[6]
    assert c["status"] == "FAIL" and "<slug>" in c["summary"]


def test_b14_base_branch_tidak_resolve_fail(chain_repo):
    c = _tl(chain_repo, **{".claude/profile/backenddev/index.json": _index(chain_repo, base_branch="develop")})[6]
    assert c["status"] == "FAIL" and "tidak resolve" in c["summary"]


def test_b14_branch_sah_pass(chain_repo):
    c = be_checks(chain_repo, TL, "--root", str(chain_repo))[6]
    assert c["status"] == "PASS" and "feat/<slug>" in c["summary"]
