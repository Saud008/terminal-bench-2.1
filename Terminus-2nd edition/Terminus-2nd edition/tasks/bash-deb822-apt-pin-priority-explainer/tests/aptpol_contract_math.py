"""Independent APT policy contract math for debpol pytest."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any


def read_stanzas(path: Path) -> list[dict[str, str]]:
    stanzas: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    last_key: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            if cur:
                stanzas.append(cur)
                cur, last_key = {}, None
            continue
        if line.startswith(" "):
            if last_key:
                cur[last_key] = (cur.get(last_key, "") + " " + line.strip()).strip()
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            last_key = k.strip()
            cur[last_key] = v.strip()
    if cur:
        stanzas.append(cur)
    return stanzas


def read_prefs(path: Path) -> list[dict[str, str]]:
    prefs: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            if cur:
                prefs.append(cur)
                cur = {}
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            cur[k.strip()] = v.strip()
    if cur:
        prefs.append(cur)
    return prefs


def rank_origins(origins: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(origins, key=lambda s: int(s.get("Default-Pin", "500")), reverse=True)


def arch_allowed(cand_arch: str, target: str) -> bool:
    if not cand_arch:
        return False
    return cand_arch in ("all", target)


def parse_version(v: str) -> tuple[int, str, str]:
    epoch = 0
    if ":" in v:
        e, rest = v.split(":", 1)
        epoch = int(e)
        v = rest
    if "-" in v:
        upstream, deb = v.rsplit("-", 1)
    else:
        upstream, deb = v, "0"
    return epoch, upstream, deb


def _cmp_segment(x: str, y: str) -> int:
    if x == y:
        return 0
    for a, b in zip(x, y):
        if a != b:
            return (a > b) - (a < b)
    return (len(x) < len(y)) - (len(x) > len(y))


def _cmp_upstream(a: str, b: str) -> int:
    aa = a.replace("~", "\x00")
    bb = b.replace("~", "\x00")
    pa, pb = aa.split("."), bb.split(".")
    for x, y in zip(pa, pb):
        if x == y:
            continue
        if x.isdigit() and y.isdigit():
            return (int(x) > int(y)) - (int(x) < int(y))
        return _cmp_segment(x, y)
    return (len(pa) > len(pb)) - (len(pa) < len(pb))


def version_newer(a: str, b: str) -> bool:
    ea, ua, da = parse_version(a)
    eb, ub, db = parse_version(b)
    if ea != eb:
        return ea > eb
    c = _cmp_upstream(ua, ub)
    if c:
        return c > 0
    return _cmp_upstream(da, db) > 0


def effective_pin(prefs: list[dict[str, str]], pkg: str, ver: str) -> int:
    best = 0
    upstream = ver.split("-")[0]
    if ":" in upstream:
        upstream = upstream.split(":", 1)[1]
    for pref in prefs:
        pin_pkg = pref.get("Package", "*")
        if pin_pkg not in ("*", pkg):
            continue
        pin_field = pref.get("Pin", "")
        prio = int(pref.get("Pin-Priority", "0"))
        if pin_field.startswith("version "):
            pat = pin_field[len("version ") :]
            if not fnmatch.fnmatch(upstream, pat):
                continue
        best = max(best, prio)
    return best


def load_rows(scenario_dir: Path, origins: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for origin in origins:
        oid = origin.get("X-Source-Id", "origin")
        idx = scenario_dir / "indices" / f"{oid}.json"
        if not idx.exists():
            continue
        for row in json.loads(idx.read_text(encoding="utf-8")):
            rows.append({**row, "origin_id": oid})
    return rows


def graph_digest(run_id: str, origin_fp: str, rows: list[dict[str, Any]]) -> str:
    body = {
        "run_id": run_id,
        "origin_fingerprint": origin_fp,
        "packages": [
            {"name": p["package"], "version": p["version"], "origin_id": p.get("origin_id", "")}
            for p in rows
        ],
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def pick_candidate(
    prefs: list[dict[str, str]],
    rows: list[dict[str, Any]],
    pkg: str,
    arch: str,
) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_prio = -1
    for cand in rows:
        if cand["package"] != pkg:
            continue
        if not arch_allowed(cand.get("arch", ""), arch):
            continue
        ver = cand["version"]
        prio = effective_pin(prefs, pkg, ver)
        if best is None or prio > best_prio or (prio == best_prio and version_newer(ver, best["version"])):
            best = {"version": ver, "origin_id": cand["origin_id"], "effective_priority": prio}
            best_prio = prio
    return best


def contract_report(scenario_dir: Path, run_id: str) -> dict[str, Any]:
    meta = json.loads((scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    origins = rank_origins(read_stanzas(scenario_dir / "sources.sources"))
    prefs = read_prefs(scenario_dir / "pin-rules.pref")
    rows = load_rows(scenario_dir, origins)
    arch = meta.get("target_arch", "amd64")
    install_rows = []
    for q in meta.get("queries", []):
        pkg = q["package"]
        sel = pick_candidate(prefs, rows, pkg, arch)
        if sel is None:
            install_rows.append(
                {
                    "package": pkg,
                    "chosen_version": None,
                    "origin_id": None,
                    "effective_priority": 0,
                    "verdict": "none",
                }
            )
        else:
            install_rows.append(
                {
                    "package": pkg,
                    "chosen_version": sel["version"],
                    "origin_id": sel["origin_id"],
                    "effective_priority": sel["effective_priority"],
                    "verdict": "selected",
                }
            )
    install_rows.sort(key=lambda r: r["package"])
    audit = hashlib.sha256(json.dumps(install_rows, sort_keys=True).encode()).hexdigest()
    return {
        "run_id": run_id,
        "install_candidates": install_rows,
        "totals": {"queries": len(install_rows)},
        "audit_digest": audit,
    }
