"""Helper test plugin `fullstack` (Langkah 21): root multi-repo berisi repo git berprofil."""
import json
from pathlib import Path
from typing import Dict, Optional

from conftest import PLUGINS, be_profile, fe_profile, git, run_script, write_files

FS_COMMON = PLUGINS / "fullstack" / "skills" / "_common"
WORKSPACE = FS_COMMON / "workspace.py"
EXPLORE = FS_COMMON / "explore.py"
PRECONDITION = PLUGINS / "fullstack" / "skills" / "explore" / "scripts" / "check_preconditions.py"

BE_DOMAIN = (
    "# Domain Map\n\n"
    "order: internal/order · http · entry internal/http/router.go#NewRouter\n"
    "stok: internal/stok · http+external · entry internal/http/router.go#NewRouter\n"
)
BE_SURFACE = (
    "# Surface Map\n\n"
    "http: internal/http/router.go · chi r.Route(\"/api/v1\") · handler per fitur\n"
    "external: internal/client/erp.go · http.Client ke ERP_API_URL · sinkron stok\n"
    "config: internal/config/config.go#Load · os.LookupEnv · .env.example sebagai daftar\n"
)
BE_SURFACE_NO_EXT = "# Surface Map\n\nhttp: internal/http/router.go · chi · handler per fitur\n"
FE_STRUCTURE = (
    "# Structure\n\n"
    "- **Source Root**: `src/`\n"
    "- **Features Path**: `src/lib/features/<feature>/` — fitur: `orders`, `stok`\n"
    "  - `dto/`: payload backend\n"
    "- **Route Definitions**:\n"
    "  - `src/routes/(app)/orders/+page.svelte`\n"
    "  - `src/routes/(app)/stok/+page.svelte`\n"
    "- **Shared Utilities & Libs**: `src/lib/utils.ts`\n"
)
FE_SURFACE = (
    "# Surface Map\n\n"
    "| Surface Domain | Pola | Lokasi | Penanda | Bukti |\n"
    "|---|---|---|---|---|\n"
    "| **Routing & Navigation** | file-system | `src/routes/**` | `+page.svelte` | `src/routes/+layout.svelte` |\n"
    "| **HTTP Service** | axios | `src/lib/api/*.ts` | `apiClient.get<` | `src/lib/api/orders.ts#fetchOrders` |\n"
)


def repo(root: Path, rel: str, *, be: Optional[str] = None, fe: Optional[str] = None,
         files: Optional[Dict[str, str]] = None, do_commit: bool = True, source_root: str = "internal") -> Path:
    """Repo git `root/rel` dengan profil BE (`be` = stack) dan/atau FE (`fe` = stack) berisi contoh nyata."""
    path = root / rel
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    if be:
        d = be_profile(path, be, source_root=source_root)
        write_files(d, {"domain-map.md": BE_DOMAIN, "surface-map.md": BE_SURFACE})
    if fe:
        d = fe_profile(path, fe)
        write_files(d, {"structure.md": FE_STRUCTURE, "surface-map.md": FE_SURFACE})
    write_files(path, files or {"README.txt": "x\n"})
    if do_commit:
        git(path, "add", "-A")
        git(path, "commit", "-q", "-m", "chore: init")
    return path


def commit_file(path: Path, rel: str, text: str) -> None:
    write_files(path, {rel: text})
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", f"chore: {rel}")


def satu_proyek(tmp_path: Path) -> Path:
    root = tmp_path / "wms"
    repo(root, "api", be="go")
    repo(root, "frontend", fe="sveltekit", source_root="src")
    return root


def run(script: Path, root: Path, *args: str):
    """(proc, payload JSON atau None). `--json` ditambahkan bila belum ada."""
    argv = list(args) + ([] if "--json" in args else ["--json"])
    proc = run_script(script, *argv, cwd=root)
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        payload = None
    return proc, payload
