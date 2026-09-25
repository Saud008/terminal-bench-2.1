"""Independent reference for YARA suppression window correlator pipeline."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

TIER_ORDER = ["low", "medium", "high", "critical"]


def load_policy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))
    return events


def policy_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Exact field order for events_digest lines (event-staging.md).
_EVENT_DIGEST_FIELDS = (
    "event_id",
    "asset_id",
    "sample_sha256",
    "rule_name",
    "rule_revision",
    "detected_ms",
    "scanner_host",
)


def _event_digest_line(ev: dict[str, Any]) -> dict[str, Any]:
    return {k: ev[k] for k in _EVENT_DIGEST_FIELDS}


def compute_events_digest(events: list[dict[str, Any]]) -> str:
    ordered = sorted(events, key=lambda e: (int(e["detected_ms"]), e["event_id"]))
    body = "".join(
        json.dumps(_event_digest_line(ev), separators=(",", ":")) + "\n" for ev in ordered
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def revision_active(policy: dict[str, Any], ev: dict[str, Any]) -> bool:
    for rev in policy.get("rule_revisions") or []:
        if rev["rule_name"] != ev["rule_name"] or rev["revision_id"] != ev["rule_revision"]:
            continue
        detected = int(ev["detected_ms"])
        if detected < int(rev["effective_ms"]):
            return False
        if detected > int(rev["retired_ms"]):
            return False
        return True
    return False


def ticket_matches(policy: dict[str, Any], ev: dict[str, Any]) -> tuple[bool, str]:
    for ticket in policy.get("suppression_tickets") or []:
        if ticket["rule_name"] != ev["rule_name"]:
            continue
        if ticket.get("asset_id") and ticket["asset_id"] != ev["asset_id"]:
            continue
        if ticket.get("sample_sha256") and ticket["sample_sha256"] != ev["sample_sha256"]:
            continue
        detected = int(ev["detected_ms"])
        if detected < int(ticket["start_ms"]):
            continue
        if detected > int(ticket["end_ms"]):
            continue
        return True, str(ticket["ticket_id"])
    return False, ""


def classify_duplicates(events: list[dict[str, Any]]) -> set[str]:
    best: dict[tuple[str, str, str], tuple[int, str]] = {}
    dupes: set[str] = set()
    for ev in events:
        key = (ev["asset_id"], ev["rule_name"], ev["sample_sha256"])
        detected = int(ev["detected_ms"])
        eid = ev["event_id"]
        if key not in best:
            best[key] = (detected, eid)
            continue
        prev_ms, prev_id = best[key]
        if detected < prev_ms or (detected == prev_ms and eid < prev_id):
            dupes.add(prev_id)
            best[key] = (detected, eid)
        else:
            dupes.add(eid)
    return dupes


def escalate_one(tier: str) -> str:
    if tier in TIER_ORDER:
        idx = TIER_ORDER.index(tier)
        if idx + 1 < len(TIER_ORDER):
            return TIER_ORDER[idx + 1]
    return tier


def effective_tier(policy: dict[str, Any], ev: dict[str, Any], default_tier: str = "low") -> str:
    base = default_tier
    for row in policy.get("asset_criticality") or []:
        if row["asset_id"] == ev["asset_id"]:
            base = row["tier"]
            if int(ev["detected_ms"]) >= int(row["escalation_ms"]):
                return escalate_one(base)
            return base
    return base


def is_quarantined(policy: dict[str, Any], ev: dict[str, Any]) -> bool:
    detected = int(ev["detected_ms"])
    for row in policy.get("quarantine_states") or []:
        if row["asset_id"] != ev["asset_id"] or row["sample_sha256"] != ev["sample_sha256"]:
            continue
        if row["state"] != "active":
            continue
        if detected < int(row["entered_ms"]):
            continue
        cleared = int(row.get("cleared_ms") or 0)
        if cleared > 0 and detected >= cleared:
            continue
        return True
    return False


def _normalize_json(value: Any) -> Any:
    """Recursive normalize for bundle_digest (incident-bundle-export.md)."""
    if isinstance(value, float) and value == int(value):
        return int(value)
    if isinstance(value, dict):
        return {k: _normalize_json(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize_json(v) for v in value]
    return value


def bundle_digest(body: dict[str, Any]) -> str:
    # Key absent (not empty); recursive normalize over nested dicts/lists.
    payload = {k: v for k, v in body.items() if k != "bundle_digest"}
    raw = json.dumps(_normalize_json(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def reference_correlate(
    policy: dict[str, Any],
    events: list[dict[str, Any]],
    *,
    correlate_generation: int = 1,
    staging_generation: int = 1,
    default_tier: str = "low",
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    valid_events = [ev for ev in events if revision_active(policy, ev)]
    dupes = classify_duplicates(valid_events)
    rejected: list[dict[str, Any]] = []
    incidents: list[dict[str, Any]] = []
    for ev in events:
        if not revision_active(policy, ev):
            rejected.append({"event_id": ev["event_id"], "reason": "stale_rule_revision"})
            continue
        row = {
            "event_id": ev["event_id"],
            "asset_id": ev["asset_id"],
            "sample_sha256": ev["sample_sha256"],
            "rule_name": ev["rule_name"],
            "rule_revision": ev["rule_revision"],
            "detected_ms": int(ev["detected_ms"]),
            "severity_tier": effective_tier(policy, ev, default_tier),
            "actionable": True,
            "suppressed": False,
            "suppression_reason": "",
        }
        if ev["event_id"] in dupes:
            row["suppressed"] = True
            row["suppression_reason"] = "duplicate_sample"
            row["actionable"] = False
        ok, ticket = ticket_matches(policy, ev)
        if ok:
            row["suppressed"] = True
            row["suppression_reason"] = f"suppression_ticket:{ticket}"
            row["actionable"] = False
        if is_quarantined(policy, ev):
            row["suppressed"] = True
            row["suppression_reason"] = "quarantine_active"
            row["actionable"] = False
        incidents.append(row)
    incidents.sort(key=lambda r: (r["detected_ms"], r["event_id"]))
    bundle = {
        "correlate_generation": correlate_generation,
        "staging_generation": staging_generation,
        "incidents": incidents,
    }
    bundle["bundle_digest"] = bundle_digest(bundle)
    return bundle, rejected


def reference_bundle_from_gen(gen: dict[str, Any], staging_generation: int) -> dict[str, Any]:
    bundle = {
        "correlate_generation": gen["generation"],
        "staging_generation": staging_generation,
        "incidents": deepcopy(gen["incidents"]),
    }
    bundle["bundle_digest"] = bundle_digest(bundle)
    return bundle
