"""Pustaka `_common/brief_status.py` (L2.2, L2.3, L2.4, L2.10)."""
import sys

from conftest import BE_SKILLS, TD, brief, commit, write_files

sys.path.insert(0, str(BE_SKILLS / "_common"))
import brief_status as bs  # noqa: E402


def test_read_frontmatter_ignores_body_status(tmp_path):
    p = tmp_path / "brief-01-x.md"
    p.write_text("---\ntitle: x\nstatus: READY\n---\n# B\nstatus: DONE\n", encoding="utf-8")
    assert bs.read_frontmatter(p)["status"] == "READY"
    p.write_bytes("﻿---\r\ntitle: x\r\nstatus: BLOCKED\r\n---\r\n# B\r\n".encode("utf-8"))
    assert bs.read_frontmatter(p) == {"title": "x", "status": "BLOCKED"}


def test_set_frontmatter_preserves_crlf_and_body(tmp_path):
    p = tmp_path / "brief-01-x.md"
    body = "# B\r\nstatus: READY\r\ntail\r\n"
    p.write_bytes(f"---\r\ntitle: x\r\nstatus: READY\r\n---\r\n{body}".encode("utf-8"))
    bs.set_frontmatter(p, status="SUPERSEDED", superseded_by="brief-04")
    raw = p.read_bytes().decode("utf-8")
    assert raw.endswith(body)
    assert raw.startswith("---\r\ntitle: x\r\nstatus: SUPERSEDED\r\nsuperseded_by: brief-04\r\n---\r\n")


def _b(nn, status, superseded_by=(), supersedes=()):
    return {"nn": nn, "name": f"brief-{nn}-u.md", "status": status,
            "superseded_by": list(superseded_by), "supersedes": list(supersedes)}


def test_validate_links_requires_bidirectional():
    ok = [_b("02", "SUPERSEDED", ["04"]), _b("04", "READY", supersedes=["02"])]
    assert bs.validate_links(ok) == []
    one_way = [_b("02", "SUPERSEDED", ["04"]), _b("04", "READY")]
    assert len(bs.validate_links(one_way)) == 1
    nn_down = [_b("01", "READY", supersedes=["02"]), _b("02", "SUPERSEDED", ["01"])]
    assert len(bs.validate_links(nn_down)) == 1
    blocked_tgt = [_b("02", "SUPERSEDED", ["04"]), _b("04", "BLOCKED", supersedes=["02"])]
    assert len(bs.validate_links(blocked_tgt)) == 1


def test_review_freshness_matrix(chain_repo):
    root = chain_repo
    brief(root, "01", "lock", "DONE")
    commit(root, "fix(order): implement lock")
    write_files(root, {f"{TD}/REVIEW.md": "r\n"})
    assert bs.review_freshness(root, TD) == (False, "REVIEW.md belum ter-commit")
    commit(root, "docs(order-fix): add final review report")
    assert bs.review_freshness(root, TD)[0]
    write_files(root, {".claude/profile/backenddev/commands.md": "# c2\n", "backenddev/issues/README.md": "x\n",
                       f"{TD}/REPORT.md": "r\n"})
    commit(root, "docs: profile + index + report")
    assert bs.review_freshness(root, TD)[0]
    brief(root, "02", "fix", "DONE")
    write_files(root, {"src/order.go": "package order\n// fix\n"})
    commit(root, "fix(order): implement fix")
    fresh, why = bs.review_freshness(root, TD)
    assert not fresh and "1 commit brief/kode" in why


def test_landed_sha_exact_subject(chain_repo):
    root = chain_repo
    brief(root, "01", "lock", "READY")
    commit(root, "docs(plan): add 1 briefs for order-fix")
    rel = f"{TD}/brief-01-lock.md"
    write_files(root, {"src/order.go": "package order\n// v2\n"})
    commit(root, "fix(order): implement lock-v2")
    assert bs.landed_sha(root, rel, "fix(order): implement lock") == ""
    write_files(root, {"src/order.go": "package order\n// v3\n"})
    sha = commit(root, "fix(order): implement lock")
    assert bs.landed_sha(root, rel, "fix(order): implement lock") == sha


def test_halted_nn(tmp_path):
    assert bs.halted_nn(tmp_path) is None
    (tmp_path / "HALT.md").write_text("---\nbrief: brief-02-endpoint.md\nverdict: COMPILE\n---\n# HALT\n")
    assert bs.halted_nn(tmp_path) == "02"
