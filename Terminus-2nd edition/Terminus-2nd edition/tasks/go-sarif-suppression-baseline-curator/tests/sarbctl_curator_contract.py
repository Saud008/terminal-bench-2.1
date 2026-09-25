"""Independent reference math for SARIF baseline curator contracts."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

DIGEST_KEYS = (
    "finding_id",
    "tool",
    "rule_id",
    "level",
    "uri",
    "start_line",
    "start_column",
    "fingerprint",
    "observed_at",
)


def canonical_line(finding: dict[str, Any]) -> str:
    ordered = {k: finding[k] for k in DIGEST_KEYS}
    return json.dumps(ordered, separators=(",", ":"))


def compute_findings_digest(findings: list[dict[str, Any]]) -> str:
    ordered = sorted(findings, key=lambda f: (f["observed_at"], f["finding_id"]))
    body = "".join(canonical_line(fr) + "\n" for fr in ordered)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_rule_key(tool: str, rule_id: str, catalog: dict[str, Any]) -> str:
    t = tool.lower().strip()
    r = rule_id.strip()
    aliases = (catalog or {}).get("aliases") or {}
    if r in aliases:
        r = aliases[r]
    r = re.sub(r"@v[0-9]+$", "", r)
    r = re.sub(r"/v[0-9]+$", "", r)
    return f"{t}:{r}"


def remap_uri(uri: str, cfg: dict[str, Any]) -> str:
    out = uri.replace("\\", "/")
    strips = sorted(cfg.get("prefix_strip") or [], key=len, reverse=True)
    for prefix in strips:
        p = prefix.replace("\\", "/")
        if out.startswith(p):
            out = out[len(p) :]
    rewrites = cfg.get("rewrite") or {}
    for key in sorted(rewrites, key=len, reverse=True):
        if out.startswith(key):
            out = rewrites[key] + out[len(key) :]
            break
    if out.startswith("/"):
        out = out[1:]
    return out


def physical_fingerprint(rule_key: str, uri: str, line: int, col: int) -> str:
    body = f"{uri.lower()}|{rule_key}|{line}:{col}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def parse_instant(raw: str, tz: str) -> datetime:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt.astimezone(ZoneInfo(tz))


def is_suppressed(policy: dict[str, Any], rule_key: str, uri: str, observed_at: str) -> bool:
    obs = parse_instant(observed_at, policy["timezone"])
    for row in policy.get("suppress_until") or []:
        if row["rule_key"] != rule_key:
            continue
        if not uri.startswith(row["uri_prefix"]):
            continue
        until = parse_instant(row["until"], policy["timezone"])
        if obs <= until:
            return True
    return False


def is_expired(policy: dict[str, Any], rule_key: str, uri: str, observed_at: str) -> bool:
    obs = parse_instant(observed_at, policy["timezone"])
    for row in policy.get("suppress_until") or []:
        if row["rule_key"] != rule_key:
            continue
        if not uri.startswith(row["uri_prefix"]):
            continue
        until = parse_instant(row["until"], policy["timezone"])
        return obs > until
    return False


LEVEL_RANK = {"error": 3, "warning": 2, "note": 1}


def collapse_findings(
    findings: list[dict[str, Any]],
    policy: dict[str, Any],
    remap_cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    catalog = policy.get("rules_catalog") or {}
    for f in findings:
        rk = canonical_rule_key(f["tool"], f["rule_id"], catalog)
        uri = remap_uri(f["uri"], remap_cfg)
        key = f"{rk}|{uri}|{f['start_line']}"
        buckets.setdefault(key, []).append(f)
    out: list[dict[str, Any]] = []
    for group in buckets.values():
        best = group[0]
        for cand in group[1:]:
            br = LEVEL_RANK.get(best["level"], 0)
            cr = LEVEL_RANK.get(cand["level"], 0)
            if cr > br or (cr == br and cand["finding_id"] < best["finding_id"]):
                best = cand
        out.append(best)
    return sorted(out, key=lambda f: f["finding_id"])


def load_sarif_findings(path: Path) -> list[dict[str, Any]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    run = doc["runs"][0]
    tool = run["tool"]["driver"]["name"]
    out: list[dict[str, Any]] = []
    for r in run["results"]:
        loc = r["locations"][0]["physicalLocation"]
        props = r.get("properties") or {}
        out.append(
            {
                "finding_id": props["finding_id"],
                "tool": tool,
                "rule_id": r["ruleId"],
                "level": r["level"],
                "message": r["message"]["text"],
                "uri": loc["artifactLocation"]["uri"],
                "start_line": loc["region"]["startLine"],
                "start_column": loc["region"]["startColumn"],
                "fingerprint": r["partialFingerprints"]["primaryLocationLineHash"],
                "observed_at": props["observed_at"],
            }
        )
    return out


def reference_delta(
    findings: list[dict[str, Any]],
    baseline: dict[str, Any],
    policy: dict[str, Any],
    remap_cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    catalog = policy.get("rules_catalog") or {}
    collapsed = collapse_findings(findings, policy, remap_cfg)
    curated: dict[str, dict[str, Any]] = {}
    for f in collapsed:
        rk = canonical_rule_key(f["tool"], f["rule_id"], catalog)
        uri = remap_uri(f["uri"], remap_cfg)
        if is_expired(policy, rk, uri, f["observed_at"]):
            continue
        key = f"{rk}|{uri}|{f['start_line']}"
        base_row = None
        for b in baseline["findings"]:
            brk = canonical_rule_key(b["tool"], b["rule_id"], catalog)
            buri = remap_uri(b["uri"], remap_cfg)
            if f"{brk}|{buri}|{b['start_line']}" == key:
                base_row = b
                break
        drift = bool(
            base_row
            and f["fingerprint"]
            and base_row["fingerprint"]
            and f["fingerprint"] != base_row["fingerprint"]
        )
        sup = is_suppressed(policy, rk, uri, f["observed_at"])
        if drift:
            cat = "drift"
        elif base_row is None:
            cat = "new"
        elif sup:
            cat = "suppressed"
        else:
            cat = "unchanged"
        curated[key] = {
            "finding_id": f["finding_id"],
            "rule_key": rk,
            "uri": uri,
            "start_line": f["start_line"],
            "category": cat,
            "fingerprint": f["fingerprint"],
        }
    base_keys: dict[str, dict[str, Any]] = {}
    for b in baseline["findings"]:
        rk = canonical_rule_key(b["tool"], b["rule_id"], catalog)
        uri = remap_uri(b["uri"], remap_cfg)
        base_keys[f"{rk}|{uri}|{b['start_line']}"] = b
    rows = list(curated.values())
    for key, b in base_keys.items():
        if key in curated:
            continue
        rk = canonical_rule_key(b["tool"], b["rule_id"], catalog)
        uri = remap_uri(b["uri"], remap_cfg)
        rows.append(
            {
                "finding_id": b["finding_id"],
                "rule_key": rk,
                "uri": uri,
                "start_line": b["start_line"],
                "category": "removed",
                "fingerprint": b["fingerprint"],
            }
        )
    return sorted(rows, key=lambda r: (r["category"], r["finding_id"]))
