"""Independent reference math for xsnapctl xDS snapshot normalization and diff."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

WEIGHT_SCALE_DEFAULT = 100


def tb3_weight_scale() -> int:
    raw = os.environ.get("TB3_WEIGHT_SCALE", "")
    return int(raw) if raw else WEIGHT_SCALE_DEFAULT


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_pair(root: Path, scenario: str) -> tuple[dict[str, Any], dict[str, Any]]:
    base = root / "scenarios" / scenario
    return read_json(base / "left.json"), read_json(base / "right.json")


def reference_staging(scenario: str, root: Path) -> dict[str, Any]:
    left, right = read_pair(root, scenario)
    blob = {"left": left, "right": right, "scenario": scenario}
    digest = hashlib.sha256(json.dumps(blob, separators=(",", ":")).encode()).hexdigest()
    return {"engine": "xsnapctl", "scenario": scenario, "left": left, "right": right, "staging_digest": digest}


def rank_route(rule: dict[str, Any]) -> int:
    m = rule["match"]
    return 1_000_000 + len(m["path"]) if m.get("path") else len(m.get("prefix", ""))


def collapse_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for rule in routes:
        c = rule["cluster"]
        cur = best.get(c)
        if cur is None or rank_route(rule) > rank_route(cur):
            best[c] = rule
        elif rank_route(rule) == rank_route(cur) and rule.get("precedence", 0) > cur.get("precedence", 0):
            best[c] = rule
    return sorted(best.values(), key=lambda r: r["cluster"])


def scale_endpoints(eps: list[dict[str, Any]], scale: int | None = None) -> list[dict[str, Any]]:
    scale = tb3_weight_scale() if scale is None else scale
    total = sum(int(e["weight"]) for e in eps)
    if total == 0:
        return eps
    raw = [scale * int(e["weight"]) / total for e in eps]
    ints = [int(x) for x in raw]
    rem = scale - sum(ints)
    if rem:
        for i in sorted(range(len(raw)), key=lambda j: raw[j] - ints[j], reverse=True)[:rem]:
            ints[i] += 1
    return [{"host": e["host"], "weight": ints[i]} for i, e in enumerate(eps)]


def sort_filters(filters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    net = sorted([f for f in filters if f.get("type") == "network"], key=lambda f: f["name"])
    http = sorted([f for f in filters if f.get("type") == "http"], key=lambda f: f["name"])
    return net + http


def canon_secret(raw: str) -> str:
    s = raw.strip().lower()
    return s if s.startswith("secret/") else "secret/" + s


def normalize_snapshot(snap: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(snap))
    for ln in out.get("listeners", []):
        for ch in ln.get("filter_chains", []):
            ch["filters"] = sort_filters(ch.get("filters", []))
    for rg in out.get("routes", []):
        rg["routes"] = collapse_routes(rg.get("routes", []))
    for cl in out.get("clusters", []):
        cl["endpoints"] = scale_endpoints(cl.get("endpoints", []))
    out["secrets"] = [{"name": s["name"], "secret_id": canon_secret(s["secret_id"])} for s in out.get("secrets", [])]
    return out


def route_fingerprints(snap: dict[str, Any]) -> dict[str, str]:
    fp: dict[str, str] = {}
    for rg in snap.get("routes", []):
        for rule in rg.get("routes", []):
            m = rule["match"]
            fp[rule["cluster"]] = rule["cluster"] + ":" + m.get("prefix", "") + m.get("path", "")
    return fp


def diff_route_changes(left: dict[str, Any], right: dict[str, Any]) -> list[dict[str, Any]]:
    lmap, rmap = route_fingerprints(left), route_fingerprints(right)
    changes: list[dict[str, Any]] = []
    for c, rv in rmap.items():
        if c not in lmap:
            changes.append({"path": f"/routes/{c}", "change_type": "added", "right_value": rv})
        elif lmap[c] != rv:
            changes.append(
                {"path": f"/routes/{c}", "change_type": "modified", "left_value": lmap[c], "right_value": rv}
            )
    for c, lv in lmap.items():
        if c not in rmap:
            changes.append({"path": f"/routes/{c}", "change_type": "removed", "left_value": lv})
    changes.sort(key=lambda x: x["path"])
    return changes


def reference_diff_report(scenario: str, root: Path) -> dict[str, Any]:
    left, right = read_pair(root, scenario)
    nl, nr = normalize_snapshot(left), normalize_snapshot(right)
    changes = diff_route_changes(nl, nr)
    report = {"scenario": scenario, "change_count": len(changes), "changes": changes}
    payload = {"change_count": report["change_count"], "changes": changes, "scenario": scenario}
    report["report_digest"] = hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()
    return report
