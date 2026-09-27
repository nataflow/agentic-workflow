"""L3.1/L3.2 — isi `## Commands` adapter diuji sebagai data: migrasi terpisah status/apply, build PHP dengan dev."""
import os
import re
import shutil
import subprocess

import pytest

from conftest import BE_SKILLS

STACKS = BE_SKILLS / "profile" / "stacks"
APPLY = re.compile(r"migrate\s+(deploy|dev|reset|run)\b|migration:run|migration (run|revert|redo)\b|"
                   r"flyway:(migrate|clean)|flyway(Migrate|Clean)|liquibase:(update|dropAll)|db push|"
                   r"drizzle-kit (migrate|push)|migrations:migrate|schema:update --force|"
                   r"(artisan|spark) migrate(?![:\w])|-database\s+\S+\s+up\b|goose[^|`]*\sup\b|"
                   r"migrate:(latest|fresh|refresh|reset|rollback)|migrate (up|down|fresh|refresh|reset)\b|"
                   r"atlas (migrate|schema) apply")
ADAPTERS = sorted(STACKS.glob("[!_]*.md"))


def rows(md: str) -> dict:
    sec = md.split("\n## Commands\n", 1)[1].split("\n## ", 1)[0]
    return {c[0]: "|".join(c[1:]) for c in (
        [x.strip() for x in ln.strip().strip("|").split("|")] for ln in sec.splitlines() if ln.startswith("| "))}


def test_seven_adapters_present():
    assert len(ADAPTERS) == 7


@pytest.mark.parametrize("adapter", ADAPTERS, ids=lambda p: p.stem)
def test_migration_split_and_no_apply_outside_apply_row(adapter):
    r = rows(adapter.read_text(encoding="utf-8"))
    assert "migration" not in r, f"{adapter.name}: baris `migration` lama masih ada"
    assert {"migration-status", "migration-apply"} <= r.keys(), adapter.name
    assert "tidak pernah dijalankan plugin" in r["migration-apply"]
    for key, val in r.items():
        if key != "migration-apply":
            assert not APPLY.search(val), f"{adapter.name}: perintah apply di baris `{key}`: {val}"


@pytest.mark.parametrize("adapter", ADAPTERS, ids=lambda p: p.stem)
def test_build_keeps_dev_dependencies(adapter):
    build = rows(adapter.read_text(encoding="utf-8"))["build"]
    cmds = [c for c in re.findall(r"`([^`]+)`", build) if " " in c]
    assert cmds and not any("--no-dev" in c for c in cmds), f"{adapter.name}: {build}"


@pytest.mark.parametrize("cmd,is_apply", [
    ("migrate -path db -database \"$DATABASE_URL\" version", False),
    ("goose -dir db status", False),
    ("php artisan migrate:status", False),
    ("php spark migrate:status", False),
    ("./mvnw flyway:info", False),
    ("npx --no-install prisma migrate status", False),
    ("sqlx migrate info", False),
    ("sea-orm-cli migrate status", False),
    ("migrate -path db -database $DATABASE_URL up", True),
    ("goose -dir db up", True),
    ("php artisan migrate", True),
    ("php spark migrate", True),
    ("npx prisma migrate deploy", True),
    ("sqlx migrate run", True),
    ("sea-orm-cli migrate up", True),
    ("atlas migrate apply", True),
])
def test_apply_regex(cmd, is_apply):
    assert bool(APPLY.search(cmd)) is is_apply


def test_profile_never_executes_apply():
    skill = (BE_SKILLS / "profile/SKILL.md").read_text(encoding="utf-8")
    fase4 = skill.split("### Fase 4", 1)[1].split("\n### ", 1)[0]
    assert "`migration-status`" in fase4 and "AskUserQuestion" in fase4
    run_list = fase4.split("1. Susun daftar eksekusi:", 1)[1].split(".", 1)[0]
    assert "migration-apply" not in run_list
    for path in ("profile/references/scan-guide.md", "profile/stacks/_CONTRACT.md",
                 "profile/templates/profile-template.md"):
        text = (BE_SKILLS / path).read_text(encoding="utf-8")
        for line in re.findall(r"^migration(?:-status)?:.*$", text, re.M):
            assert not APPLY.search(line.split("migration-apply:", 1)[0]), f"{path}: {line}"
        assert "`migration`" not in text.replace("`migration` ·", ""), path


def _php_build_cmd(adapter: str) -> str:
    val = rows((STACKS / adapter).read_text(encoding="utf-8"))["build"]
    return re.search(r"`([^`]+)`", val).group(1)


@pytest.mark.skipif(shutil.which("composer") is None, reason="composer tidak terpasang")
@pytest.mark.parametrize("adapter", ["php.md", "php-codeigniter.md"])
def test_php_build_keeps_dev(tmp_path, adapter):
    """Reproduksi L3.2 offline: paket dev palsu dari path repository lokal tetap ada sesudah `build`."""
    pkg = tmp_path / "pkgs" / "fake-phpunit"
    (pkg / "bin").mkdir(parents=True)
    (pkg / "composer.json").write_text('{"name":"fake/phpunit","version":"1.0.0","bin":["bin/phpunit"]}')
    (pkg / "bin" / "phpunit").write_text('#!/bin/sh\necho "fake phpunit OK"\n')
    (pkg / "bin" / "phpunit").chmod(0o755)
    app = tmp_path / "app"
    (app / "src").mkdir(parents=True)
    (app / "composer.json").write_text(
        '{"name":"demo/app","repositories":[{"type":"path","url":"../pkgs/*","options":{"symlink":false}}],'
        '"require":{},"require-dev":{"fake/phpunit":"1.0.0"},"autoload":{"psr-4":{"App\\\\":"src/"}}}')
    env = {"COMPOSER_HOME": str(tmp_path / ".composer"), "COMPOSER_NO_INTERACTION": "1",
           "PATH": os.environ["PATH"], "HOME": str(tmp_path)}
    subprocess.run(["composer", "install", "-q"], cwd=app, env=env, check=True)
    subprocess.run(_php_build_cmd(adapter) + " -q", shell=True, cwd=app, env=env, check=True)
    out = subprocess.run(["vendor/bin/phpunit"], cwd=app, env=env, capture_output=True, text=True)
    assert out.returncode == 0 and "fake phpunit OK" in out.stdout


def _contract_keys() -> list:
    """Kunci yang dideklarasikan `_CONTRACT.md` bagian 2 (kalimat pembuka `Sembilan baris perintah: …`)."""
    sec = (STACKS / "_CONTRACT.md").read_text(encoding="utf-8").split("### 2. `## Commands`", 1)[1]
    head = sec.split("baris perintah:", 1)[1].split(". Tulis", 1)[0]
    return re.findall(r"`([a-z-]+)`", head)


def test_b17_contract_lists_nine_keys():
    assert _contract_keys() == ["build", "test", "test-single", "lint", "typecheck", "typecheck-scoped",
                                "typecheck-per-brief", "migration-status", "migration-apply"]


@pytest.mark.parametrize("adapter", ADAPTERS, ids=lambda p: p.stem)
def test_b17_adapter_commands_match_contract(adapter):
    keys = [k for k in rows(adapter.read_text(encoding="utf-8")) if k != "Perintah"]
    assert sorted(keys) == sorted(_contract_keys()), f"{adapter.name}: {keys}"
