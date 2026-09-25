"""Langkah 5 jalur frontenddev — parser bersama `precondition_lib` dan pembacanya (L5.6–L5.9)."""
import importlib.util
import json
import sys

import pytest

from conftest import FE_SKILLS, commit, fe_run, git, write_files


def load_fe(rel: str, name: str):
    """Muat modul frontenddev lewat path berkas; `precondition_lib` yang diimpornya = milik frontenddev.

    backenddev punya modul bernama sama; impor lewat `sys.path` di satu sesi pytest bisa
    mengambil salinan yang salah dari `sys.modules`.
    """
    saved = sys.modules.get("precondition_lib")
    sys.modules["precondition_lib"] = FE_LIB if rel != "_common/precondition_lib.py" else None
    try:
        spec = importlib.util.spec_from_file_location(name, FE_SKILLS / rel)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        if saved is None:
            sys.modules.pop("precondition_lib", None)
        else:
            sys.modules["precondition_lib"] = saved


FE_LIB = None
FE_LIB = load_fe("_common/precondition_lib.py", "frontenddev_precondition_lib")


# --- L5.8 path non-ASCII dan route group berkurung ------------------------------------------

PROMO_TD = "frontenddev/docs/2601011200-promo"


@pytest.fixture
def promo_repo(make_repo):
    """Rantai `promo`: akar TASK.md, lalu satu commit unit yang menyentuh berkas unicode dan route group."""
    root = make_repo({f"{PROMO_TD}/TASK.md": "---\nstatus: ACTIVE\n---\n# Banner promo\n\n"
                                             "## Success Criteria\n- [ ] **SC-1**: x — verifikasi: test\n"})
    commit(root, "docs(promo): root task")
    write_files(root, {"src/i18n/café.tsx": "export default {}\n",
                       "app/(tabs)/index.tsx": "export default function T(){}\n",
                       "src/components/Kartu Promo.tsx": "export default {}\n"})
    commit(root, "feat(promo): implement unit 01")
    return root


def report_check4(repo, changes: str) -> dict:
    write_files(repo, {f"{PROMO_TD}/REPORT.md":
                       "# Banner promo — Report\n\n## Ringkasan\nBanner promo kini tampil di beranda.\n\n"
                       f"## Perubahan\n{changes}\n"})
    r = fe_run(repo, "report/scripts/validate_report.py", "--taskdir", PROMO_TD, "--json")
    return {c["id"]: c for c in json.loads(r.stdout)["checks"]}[4]


def test_chain_files_unicode_dan_berspasi(promo_repo):
    assert FE_LIB.chain_files(promo_repo, PROMO_TD) == [
        "app/(tabs)/index.tsx", "src/components/Kartu Promo.tsx", "src/i18n/café.tsx"]


@pytest.mark.parametrize("changes", [
    "- Tambah terjemahan bahasa Prancis (src/i18n/café.tsx)\n- Tambah tab beranda baru (app/(tabs))",
    "- Tambah terjemahan bahasa Prancis (src/i18n)\n- Tambah tab beranda baru (app/(tabs)/index.tsx)",
])
def test_report_unicode_dan_route_group_expo_pass(promo_repo, changes):
    changes += "\n- Tambah kartu promo baru (src/components/Kartu Promo.tsx)"
    c4 = report_check4(promo_repo, changes)
    assert c4["status"] == "PASS", c4


def test_bullet_route_group_sveltekit(make_repo):
    root = make_repo({f"{PROMO_TD}/TASK.md": "---\nstatus: ACTIVE\n---\n# Banner promo\n"})
    commit(root, "docs(promo): root task")
    write_files(root, {"src/routes/(app)/+page.svelte": "<h1>x</h1>\n"})
    commit(root, "feat(promo): implement unit 01")
    c4 = report_check4(root, "- Rute promo tampil di beranda (src/routes/(app)/+page.svelte)")
    assert c4["status"] == "PASS", c4


@pytest.mark.parametrize("line,want", [
    ("- Tambah tab (app/(tabs)/index.tsx)", ("Tambah tab", "app/(tabs)/index.tsx")),
    ("- Tab (baru) (app/(tabs)/x.tsx)", ("Tab (baru)", "app/(tabs)/x.tsx")),
    ("- Rute (src/routes/(app)/+page.svelte)", ("Rute", "src/routes/(app)/+page.svelte")),
    ("- Terjemahan (src/i18n)", ("Terjemahan", "src/i18n")),
    ("- Tanpa anotasi", None),
    ("- (src/x.ts)", None),
])
def test_parse_bullet(line, want):
    vr = load_fe("report/scripts/validate_report.py", "fe_validate_report_l58")
    assert vr.parse_bullet(line) == want
