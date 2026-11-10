#!/usr/bin/env python3
"""Pemakaian token sesi Claude Code per proyek, per fase skill, dan per subagent (dev-only, Langkah 30 U1).

Membaca log sesi lokal `~/.claude/projects/<slug>/*.jsonl` beserta `<sesi>/subagents/agent-*.jsonl` dan
`*.meta.json`-nya, lalu merangkum:

- main loop: pemanggilan API, input, cache write/read, output, biaya relatif, konteks per pemanggilan;
- fase: skill terakhir yang dimuat (`Base directory for this skill: …/<plugin>/<versi>/skills/<skill>`);
- subagent per tipe dan model, serta ukuran balikannya ke main loop;
- compaction (konteks sebelum/sesudah) dan rangkaian skill per sesi;
- subperintah `explorer`: dispatch `code-explorer` per fase, profil (surface/blast), dan kedalaman (Langkah 31 X4).

Biaya dinyatakan dalam "token setara input" dengan bobot relatif (bawaan rasio harga Opus: cache read 0,1×,
cache write 2×, output 5×) yang dapat diganti lewat `--bobot`. Angkanya untuk membandingkan sebelum/sesudah,
bukan tagihan. Skrip tidak pernah mencetak isi prompt, isi dokumen, maupun isi balikan.

    python3 scripts/token_usage.py ringkas --repo ~/work/hkm/wms --turunan
    python3 scripts/token_usage.py ringkas --slug=-home-me-work-app --since 2026-11-01 --json
    python3 scripts/token_usage.py ringkas --repo ~/work/hkm/wms --turunan --since "2026-11-10 15:20+07:00"
    python3 scripts/token_usage.py explorer --repo ~/work/hkm/orderhub --turunan

Dev-only: berkas ini tidak berada di `src/plugins/`, jadi tidak ikut terkirim ke cache plugin.
Zero external dependencies (Python Standard Library only).
"""

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

BOBOT_BAWAAN = {"inp": 1.0, "cw": 2.0, "cr": 0.1, "out": 5.0}
SKILL_RE = re.compile(r"Base directory for this skill: (\S+)")
VERSI_RE = re.compile(r"^\d+(\.\d+)+$")
HANDBACK_RE = re.compile(r'<agent-message from="([^"]+)"')
KEDALAMAN_RE = re.compile(r"Kedalaman\W+(ringkas|menyeluruh)")
PRA_SKILL = "(pra-skill)"


# ============================================================ util

def slug_of(path: str) -> str:
    """Nama direktori proyek Claude Code untuk sebuah path: tiap karakter non-alfanumerik jadi `-`.

    Path dijadikan absolut tanpa resolve symlink, karena Claude Code menamai direktori dari cwd apa adanya
    (di macOS `resolve()` mengubah `/home` jadi `/System/Volumes/Data/home`)."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(os.path.expanduser(path)))


def parse_since(spec: str) -> Optional[datetime]:
    """`YYYY-MM-DD`, `YYYY-MM-DD HH:MM[:SS]`, atau ISO 8601 ber-zona (`2026-11-10T15:20+07:00`, `…Z`).

    Tanpa zona waktu → zona lokal mesin. Hasilnya selalu sadar zona (UTC) supaya bisa dibandingkan dengan
    `timestamp` log yang ditulis dalam UTC.
    """
    spec = (spec or "").strip()
    if not spec:
        return None
    try:
        dt = datetime.fromisoformat(spec.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"--since tidak terbaca: {spec!r} (pakai YYYY-MM-DD, \"YYYY-MM-DD HH:MM\", "
                         "atau ISO 8601 ber-zona seperti 2026-11-10T15:20+07:00)") from None
    if dt.tzinfo is None:
        dt = dt.astimezone()  # zona lokal
    return dt.astimezone(timezone.utc)


def session_start(recs: List[Dict[str, Any]]) -> Optional[datetime]:
    ts = first_timestamp(recs)
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
    except ValueError:
        return None


def is_before(recs: List[Dict[str, Any]], since: Optional[datetime]) -> bool:
    """Sesi dibuang bila mulainya sebelum `since`; sesi tanpa timestamp terbaca juga dibuang saat filter aktif."""
    if since is None:
        return False
    start = session_start(recs)
    return start is None or start < since


def parse_bobot(spec: Optional[str]) -> Dict[str, float]:
    bobot = dict(BOBOT_BAWAAN)
    for part in filter(None, (spec or "").split(",")):
        key, _, val = part.partition("=")
        if key.strip() not in bobot:
            raise ValueError(f"kunci bobot tidak dikenal: {key!r} (pakai inp, cw, cr, out)")
        bobot[key.strip()] = float(val)
    return bobot


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out = []
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict):
                    out.append(rec)
    except OSError:
        pass
    return out


def text_of(message: Dict[str, Any]) -> str:
    c = message.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(x.get("text", "") for x in c if isinstance(x, dict) and isinstance(x.get("text"), str))
    return ""


def content_len(c: Any) -> int:
    if isinstance(c, str):
        return len(c)
    if isinstance(c, list):
        return sum(len(x.get("text", "")) if isinstance(x, dict) else len(str(x)) for x in c)
    return len(str(c)) if c is not None else 0


def skill_label(text: str) -> Optional[str]:
    """`plugin:skill` dari baris `Base directory for this skill:`; segmen versi dilewati."""
    m = SKILL_RE.search(text)
    if not m:
        return None
    parts = [p for p in m.group(1).rstrip("/").split("/") if p]
    if "skills" not in parts or parts.index("skills") + 1 >= len(parts):
        return None
    i = parts.index("skills")
    owner = parts[i - 1] if i >= 1 else "?"
    if VERSI_RE.match(owner) and i >= 2:
        owner = parts[i - 2]
    return f"{owner}:{parts[i + 1]}"


def unique_usage(recs: Iterable[Dict[str, Any]]) -> Iterator[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Satu entri per pesan API: log menulis satu baris per blok konten dengan `message.id` yang sama."""
    seen = set()
    for rec in recs:
        if rec.get("type") != "assistant":
            continue
        msg = rec.get("message") or {}
        usage = msg.get("usage")
        key = msg.get("id") or rec.get("uuid")
        if not usage or key in seen:
            continue
        seen.add(key)
        yield rec, msg


def tokens(usage: Dict[str, Any]) -> Dict[str, int]:
    return {"inp": int(usage.get("input_tokens") or 0),
            "cw": int(usage.get("cache_creation_input_tokens") or 0),
            "cr": int(usage.get("cache_read_input_tokens") or 0),
            "out": int(usage.get("output_tokens") or 0)}


def cost(t: Dict[str, int], bobot: Dict[str, float]) -> float:
    return sum(t[k] * bobot[k] for k in bobot)


def pct(values: List[int], q: float) -> int:
    if not values:
        return 0
    s = sorted(values)
    return s[min(len(s) - 1, int(len(s) * q))]


# ============================================================ sumber

def session_files(projects: Path, slugs: List[str], turunan: bool) -> List[Path]:
    dirs = []
    if projects.is_dir():
        for d in sorted(projects.iterdir()):
            if d.is_dir() and any(d.name == s or (turunan and d.name.startswith(s + "-")) for s in slugs):
                dirs.append(d)
    return [f for d in dirs for f in sorted(d.glob("*.jsonl"))]


def first_timestamp(recs: List[Dict[str, Any]]) -> str:
    for rec in recs:
        ts = rec.get("timestamp")
        if isinstance(ts, str):
            return ts
    return ""


def subagents(session: Path) -> List[Tuple[str, Path, Dict[str, Any]]]:
    out = []
    for f in sorted(session.with_suffix("").joinpath("subagents").glob("agent-*.jsonl")):
        meta_path = f.with_suffix(".meta.json")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
        except (OSError, ValueError):
            meta = {}
        out.append((f.stem.removeprefix("agent-"), f, meta if isinstance(meta, dict) else {}))
    return out


# ============================================================ ringkas

def analyze(files: List[Path], bobot: Dict[str, float], since: Optional[datetime] = None) -> Dict[str, Any]:
    main = Counter()
    ctx_all: List[int] = []
    peaks: List[int] = []
    phase: Dict[str, Counter] = defaultdict(Counter)
    sub: Dict[Tuple[str, str], Counter] = defaultdict(Counter)
    returns: Dict[str, Counter] = defaultdict(Counter)
    loads: Dict[str, Counter] = defaultdict(Counter)
    combos = Counter()
    compactions: List[Dict[str, Any]] = []
    n_sessions = 0

    for f in files:
        recs = read_jsonl(f)
        if is_before(recs, since):
            continue
        n_sessions += 1
        agents = subagents(f)
        agent_type = {aid: str(meta.get("agentType") or "?") for aid, _, meta in agents}
        tool_type: Dict[str, str] = {}
        current = PRA_SKILL
        seq: List[str] = []
        peak = 0
        pending_compact: Optional[Dict[str, Any]] = None
        seen = set()

        for rec in recs:
            msg = rec.get("message") or {}
            rtype = rec.get("type")
            if rtype == "system" and rec.get("subtype") == "compact_boundary":
                meta = rec.get("compactMetadata") or {}
                pending_compact = {"trigger": meta.get("trigger") or "?", "pre": int(meta.get("preTokens") or 0),
                                   "post": None}
                compactions.append(pending_compact)
            if rtype == "user" and rec.get("isMeta"):
                text = text_of(msg)
                label = skill_label(text)
                if label:
                    current = label
                    loads[label]["n"] += 1
                    loads[label]["chars"] += len(text)
                    if label not in seq:
                        seq.append(label)
                hb = HANDBACK_RE.search(text)
                if hb:
                    kind = agent_type.get(hb.group(1), "?")
                    returns[kind]["n"] += 1
                    returns[kind]["chars"] += len(text)
            if rtype == "assistant" and isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") in ("Agent", "Task"):
                        tool_type[block.get("id", "")] = str((block.get("input") or {}).get("subagent_type") or "?")
            if rtype == "user" and isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("tool_use_id") in tool_type:
                        kind = tool_type[block["tool_use_id"]]
                        returns[kind]["n"] += 1
                        returns[kind]["chars"] += content_len(block.get("content"))
            if rtype == "assistant":
                usage = msg.get("usage")
                key = msg.get("id") or rec.get("uuid")
                if not usage or key in seen:
                    continue
                seen.add(key)
                t = tokens(usage)
                ctx = t["inp"] + t["cw"] + t["cr"]
                c = cost(t, bobot)
                main.update(t)
                main["calls"] += 1
                main["cost"] += c
                ctx_all.append(ctx)
                peak = max(peak, ctx)
                ph = phase[current]
                ph["calls"] += 1
                ph["ctx"] += ctx
                ph["cr"] += t["cr"]
                ph["cost"] += c
                if pending_compact is not None and pending_compact["post"] is None:
                    pending_compact["post"] = ctx
                    pending_compact = None

        peaks.append(peak)
        if seq:
            combos[" → ".join(seq)] += 1
        for _, path, meta in agents:
            kind = (str(meta.get("agentType") or "?"), "?")
            st = Counter()
            for _, amsg in unique_usage(read_jsonl(path)):
                if kind[1] == "?":
                    kind = (kind[0], str(amsg.get("model") or "?"))
                t = tokens(amsg.get("usage") or {})
                st.update(t)
                st["calls"] += 1
                st["cost"] += cost(t, bobot)
            sub[kind].update(st)
            sub[kind]["n"] += 1

    sub_cost = sum(v["cost"] for v in sub.values())
    total = main["cost"] + sub_cost

    def comp(trigger: str) -> Dict[str, Any]:
        rows = [c for c in compactions if c["trigger"] == trigger and c["pre"] and c["post"]]
        return {"n": len(rows),
                "pre_median": int(statistics.median(c["pre"] for c in rows)) if rows else 0,
                "post_median": int(statistics.median(c["post"] for c in rows)) if rows else 0}

    return {
        "bobot": bobot,
        "sesi": n_sessions,
        "main": {"calls": main["calls"], "input": main["inp"], "cache_write": main["cw"], "cache_read": main["cr"],
                 "output": main["out"], "biaya": round(main["cost"]),
                 "porsi_total": round(100 * main["cost"] / total, 1) if total else 0.0,
                 "konteks_rata2": int(sum(ctx_all) / len(ctx_all)) if ctx_all else 0,
                 "puncak_sesi_p50": pct(peaks, 0.5), "puncak_sesi_p90": pct(peaks, 0.9),
                 "puncak_maks": max(peaks) if peaks else 0},
        "subagent_total": {"calls": sum(v["calls"] for v in sub.values()), "biaya": round(sub_cost)},
        "fase": [{"fase": k, "calls": v["calls"], "konteks_rata2": int(v["ctx"] / v["calls"]) if v["calls"] else 0,
                  "biaya": round(v["cost"]),
                  "porsi_main": round(100 * v["cost"] / main["cost"], 1) if main["cost"] else 0.0}
                 for k, v in sorted(phase.items(), key=lambda kv: -kv[1]["cost"])],
        "subagent": [{"tipe": k[0], "model": k[1], "n": v["n"], "calls": v["calls"], "output": v["out"],
                      "biaya": round(v["cost"]), "biaya_per_agent": round(v["cost"] / v["n"]) if v["n"] else 0,
                      "porsi_subagent": round(100 * v["cost"] / sub_cost, 1) if sub_cost else 0.0}
                     for k, v in sorted(sub.items(), key=lambda kv: -kv[1]["cost"])],
        "balikan": [{"tipe": k, "n": v["n"], "karakter": v["chars"],
                     "rata2": int(v["chars"] / v["n"]) if v["n"] else 0}
                    for k, v in sorted(returns.items(), key=lambda kv: -kv[1]["chars"])],
        "skill_dimuat": [{"skill": k, "n": v["n"], "karakter_rata2": int(v["chars"] / v["n"]) if v["n"] else 0}
                         for k, v in sorted(loads.items(), key=lambda kv: -kv[1]["chars"])],
        "compaction": {"manual": comp("manual"), "auto": comp("auto")},
        "rangkaian": [{"n": n, "skill": k} for k, n in combos.most_common(10)],
    }


def render(r: Dict[str, Any], top: int) -> str:
    m = r["main"]
    lines = [
        f"Sesi: {r['sesi']} · bobot cr={r['bobot']['cr']} cw={r['bobot']['cw']} out={r['bobot']['out']}",
        f"Main loop: {m['calls']} pemanggilan · cache read {m['cache_read']:,} · cache write {m['cache_write']:,} "
        f"· output {m['output']:,} · biaya {m['biaya']:,} ({m['porsi_total']}% total)",
        f"Konteks: rata-rata {m['konteks_rata2']:,} · puncak sesi p50 {m['puncak_sesi_p50']:,} "
        f"p90 {m['puncak_sesi_p90']:,} maks {m['puncak_maks']:,}",
        f"Subagent: {r['subagent_total']['calls']} pemanggilan · biaya {r['subagent_total']['biaya']:,}",
        "", "Fase (skill terakhir dimuat):",
    ]
    lines += [f"  {f['fase']:32} calls={f['calls']:6} konteks={f['konteks_rata2']:8,} "
              f"biaya={f['biaya']:13,} ({f['porsi_main']:4}% main)" for f in r["fase"][:top]]
    lines += ["", "Subagent:"]
    lines += [f"  {s['tipe']:30} {s['model'][:18]:18} n={s['n']:4} calls={s['calls']:6} "
              f"per-agent={s['biaya_per_agent']:10,} ({s['porsi_subagent']:4}% subagent)" for s in r["subagent"][:top]]
    lines += ["", "Balikan subagent ke main loop:"]
    lines += [f"  {b['tipe']:30} n={b['n']:4} rata-rata={b['rata2']:7,} karakter" for b in r["balikan"][:top]]
    lines += ["", "Body skill dimuat:"]
    lines += [f"  {s['skill']:32} n={s['n']:4} rata-rata={s['karakter_rata2']:7,} karakter"
              for s in r["skill_dimuat"][:top]]
    c = r["compaction"]
    lines += ["", f"Compaction: manual {c['manual']['n']} ({c['manual']['pre_median']:,} → {c['manual']['post_median']:,}) "
                  f"· auto {c['auto']['n']} ({c['auto']['pre_median']:,} → {c['auto']['post_median']:,})"]
    lines += ["", "Rangkaian skill per sesi:"]
    lines += [f"  {x['n']:3}× {x['skill']}" for x in r["rangkaian"]]
    return "\n".join(lines)


# ============================================================ explorer (Langkah 31 X4)

def analyze_explorer(files: List[Path], bobot: Dict[str, float], since: Optional[datetime] = None,
                     agent: str = "backend:code-explorer") -> Dict[str, Any]:
    """Dispatch `agent` per fase/profil/kedalaman, biaya agentnya, dan ukuran balikannya."""
    rows: Dict[Tuple[str, str, str], Counter] = defaultdict(Counter)
    per_session: Dict[str, List[int]] = defaultdict(list)
    for f in files:
        recs = read_jsonl(f)
        if is_before(recs, since):
            continue
        # `meta.json` agent menyimpan `toolUseId` dispatch-nya: biaya dan balikan dipasangkan lewat id itu.
        cost_by_tool: Dict[str, float] = {}
        tool_by_agent: Dict[str, str] = {}
        for aid, path, meta in subagents(f):
            if meta.get("agentType") != agent or not meta.get("toolUseId"):
                continue
            tool_by_agent[aid] = meta["toolUseId"]
            cost_by_tool[meta["toolUseId"]] = sum(cost(tokens(m.get("usage") or {}), bobot)
                                                  for _, m in unique_usage(read_jsonl(path)))
        current = PRA_SKILL
        count = Counter()
        tool_key: Dict[str, Tuple[str, str, str]] = {}
        for rec in recs:
            msg = rec.get("message") or {}
            if rec.get("type") == "user" and rec.get("isMeta"):
                text = text_of(msg)
                current = skill_label(text) or current
                hb = HANDBACK_RE.search(text)
                if hb and tool_by_agent.get(hb.group(1)) in tool_key:
                    rows[tool_key[tool_by_agent[hb.group(1)]]]["balikan"] += len(text)
            if rec.get("type") == "assistant" and isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if not (isinstance(block, dict) and block.get("type") == "tool_use"
                            and block.get("name") in ("Agent", "Task")):
                        continue
                    inp = block.get("input") or {}
                    if inp.get("subagent_type") != agent:
                        continue
                    prompt = str(inp.get("prompt") or "")
                    profil = "blast" if re.search(r"Blast Map|Profil B", prompt) else "surface"
                    kd = KEDALAMAN_RE.search(prompt)
                    key = (current, profil, kd.group(1) if kd else "?")
                    row = rows[key]
                    row["n"] += 1
                    row["biaya"] += cost_by_tool.get(block.get("id", ""), 0)
                    count[current] += 1
                    tool_key[block.get("id", "")] = key
            if rec.get("type") == "user" and isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("tool_use_id") in tool_key:
                        rows[tool_key[block["tool_use_id"]]]["balikan"] += content_len(block.get("content"))
        for ph, n in count.items():
            per_session[ph].append(n)
    return {
        "agent": agent,
        "baris": [{"fase": k[0], "profil": k[1], "kedalaman": k[2], "n": v["n"], "biaya": round(v["biaya"]),
                   "biaya_rata2": round(v["biaya"] / v["n"]) if v["n"] else 0,
                   "balikan_rata2": int(v["balikan"] / v["n"]) if v["n"] else 0}
                  for k, v in sorted(rows.items(), key=lambda kv: -kv[1]["n"])],
        "per_sesi": {ph: {"sesi": len(v), "p50": pct(v, 0.5), "maks": max(v)} for ph, v in per_session.items()},
    }


def render_explorer(r: Dict[str, Any]) -> str:
    lines = [f"Dispatch {r['agent']} (fase · profil · kedalaman):"]
    lines += [f"  {b['n']:4}× {b['fase']:28} {b['profil']:8} {b['kedalaman']:10} biaya/agent={b['biaya_rata2']:9,} "
              f"balikan={b['balikan_rata2']:6,} karakter" for b in r["baris"]]
    lines += ["", "Dispatch per sesi:"]
    lines += [f"  {ph:28} sesi={v['sesi']:4} p50={v['p50']} maks={v['maks']}" for ph, v in r["per_sesi"].items()]
    return "\n".join(lines)


# ============================================================ CLI

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Pemakaian token sesi Claude Code (dev-only)")
    ap.add_argument("perintah", choices=("ringkas", "explorer"))
    ap.add_argument("--repo", action="append", default=[], help="Path repo/workspace; diterjemahkan ke slug proyek")
    ap.add_argument("--slug", action="append", default=[], help="Nama direktori di bawah --projects-dir; tulis --slug=<slug> karena slug diawali `-`")
    ap.add_argument("--turunan", action="store_true", help="Ikutkan slug turunan (sub-repo di bawah path itu)")
    ap.add_argument("--projects-dir", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--since", default="", help="Hanya sesi yang mulai pada/sesudah waktu ini: YYYY-MM-DD, \"YYYY-MM-DD HH:MM\" (zona lokal), "
                    "atau ISO 8601 ber-zona (2026-11-10T15:20+07:00)")
    ap.add_argument("--bobot", default="", help="Mis. cr=0.1,cw=2,out=5 (relatif terhadap input)")
    ap.add_argument("--agent", default="backend:code-explorer", help="Tipe subagent untuk perintah explorer")
    ap.add_argument("--top", type=int, default=14)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        bobot = parse_bobot(args.bobot)
        since = parse_since(args.since)
    except ValueError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}) if args.json else f"FAIL: {exc}")
        return 2
    slugs = [slug_of(p) for p in args.repo] + args.slug
    if not slugs:
        msg = "sebutkan minimal satu --repo atau --slug"
        print(json.dumps({"status": "FAIL", "error": msg}) if args.json else f"FAIL: {msg}")
        return 2
    files = session_files(Path(args.projects_dir).expanduser(), slugs, args.turunan)
    if args.perintah == "ringkas":
        result = analyze(files, bobot, since)
        text = render(result, args.top)
    else:
        result = analyze_explorer(files, bobot, since, args.agent)
        text = render_explorer(result)
    if args.json:
        print(json.dumps({"status": "PASS", "slug": slugs, **result}, ensure_ascii=False, indent=2))
    else:
        print(text if files else "Tidak ada sesi untuk slug: " + ", ".join(slugs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
