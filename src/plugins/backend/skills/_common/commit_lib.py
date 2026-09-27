"""Pesan commit brief dari `commit_template` profil — satu sumber untuk scaffold dan validator.

`commit_template` (opsional, `.claude/profile/backenddev/index.json`) memakai slot `{type}`,
`{scope}`, `{subject}`, dan `{ticket}`; `{subject}` wajib ada. Contoh: `"{type}({scope}): {subject}"`
atau `"{ticket}: {subject}"`. Template absen atau tidak sah → Conventional Commits
(`DEFAULT_TEMPLATE`). Field prosa `commit_convention` tetap acuan manusia dan tidak dibaca di sini.

Subjek brief selalu `implement <unit>`; `scaffold_brief.py` merender pesannya, `validate_briefs.py`
Check S mencocokkannya dengan regex yang diturunkan dari template yang sama.
Hanya pustaka standar.
"""
import re
from typing import Any, Dict, Optional, Pattern

COMMIT_TYPES = ("feat", "fix", "refactor", "perf", "test", "chore", "docs")
DEFAULT_TEMPLATE = "{type}({scope}): {subject}"
_SLOT = re.compile(r"\{(type|scope|subject|ticket)\}")
_UNKNOWN_SLOT = re.compile(r"\{(?!(?:type|scope|subject|ticket)\})[^}]*\}")
_SLOT_PATTERN = {
    "type": "(?:" + "|".join(COMMIT_TYPES) + ")",
    "scope": r"[a-z0-9_.-]+",
    "subject": r"implement\s+\S.*",
    "ticket": r"[A-Z][A-Z0-9]+-\d+",
}


def commit_template(index: Optional[Dict[str, Any]]) -> str:
    """Template sah dari index profil, atau `DEFAULT_TEMPLATE`."""
    tpl = str((index or {}).get("commit_template") or "").strip()
    if tpl and "{subject}" in tpl and not _UNKNOWN_SLOT.search(tpl):
        return tpl
    return DEFAULT_TEMPLATE


def default_commit_type(lane: Optional[str], finding_source: Optional[str]) -> str:
    """`fix` untuk akar perbaikan (lane `DEFECT_RCA` atau akar ber-`finding_source`), selain itu `feat`."""
    return "fix" if (lane or "").strip().upper() == "DEFECT_RCA" or (finding_source or "").strip() else "feat"


def render(tpl: str, *, ctype: str, scope: str, unit: str, ticket: Optional[str] = None) -> str:
    if ctype not in COMMIT_TYPES:
        raise ValueError(f"commit_type '{ctype}' di luar {', '.join(COMMIT_TYPES)}")
    if "{ticket}" in tpl and not ticket:
        raise ValueError("commit_template memuat {ticket} tetapi spec tidak memberi `ticket`")
    return tpl.format(type=ctype, scope=scope, subject=f"implement {unit}", ticket=ticket or "")


def pattern(tpl: str) -> Pattern[str]:
    """Regex penuh (`^…$`) yang menerima pesan hasil `render(tpl, …)`."""
    parts, pos = [], 0
    for m in _SLOT.finditer(tpl):
        parts.append(re.escape(tpl[pos:m.start()]))
        parts.append(_SLOT_PATTERN[m.group(1)])
        pos = m.end()
    parts.append(re.escape(tpl[pos:]))
    return re.compile("^" + "".join(parts) + "$")
