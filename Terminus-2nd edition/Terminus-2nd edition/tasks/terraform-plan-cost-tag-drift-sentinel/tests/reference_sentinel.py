"""Independent reference oracle for tf-tag-sentinel."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

KNOWN_AFTER_APPLY = "(known after apply)"
STAGING_SCHEMA = "plan-tag-stage/1"
REPORT_SCHEMA = "tag-violation-report/1"


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_digest(doc: dict[str, Any]) -> str:
    payload = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog(catalog_path: Path) -> dict[str, Any]:
    return load_json(catalog_path)


def canonical_key_map(policy: dict[str, Any]) -> dict[str, str]:
    """Display name -> canonical key."""
    rev: dict[str, str] = {}
    for canon, display in policy.get("tag_key_map", {}).items():
        rev[str(display)] = str(canon)
    return rev


def display_to_canonical(tags: dict[str, Any] | None, policy: dict[str, Any]) -> dict[str, str]:
    if not tags:
        return {}
    rev = canonical_key_map(policy)
    out: dict[str, str] = {}
    for display, value in tags.items():
        if value is None:
            continue
        canon = rev.get(str(display))
        if canon:
            out[canon] = str(value)
    return out


def module_prefixes(address: str) -> list[str]:
    parts = address.split(".")
    prefixes: list[str] = []
    if not parts or parts[0] != "module":
        return prefixes
    for i in range(len(parts) - 1):
        if parts[i] == "module" and i + 1 < len(parts):
            prefixes.append(".".join(parts[: i + 2]))
    return prefixes


def apply_module_defaults(address: str, tags: dict[str, str], policy: dict[str, Any]) -> dict[str, str]:
    rev = canonical_key_map(policy)
    merged = dict(tags)
    defaults = policy.get("module_defaults", [])
    applicable: list[tuple[str, dict[str, str]]] = []
    for entry in defaults:
        prefix = str(entry.get("module_prefix", ""))
        if not prefix:
            continue
        if address == prefix or address.startswith(prefix + "."):
            canon_tags: dict[str, str] = {}
            for display, value in (entry.get("tags") or {}).items():
                canon = rev.get(str(display))
                if canon:
                    canon_tags[canon] = str(value)
            applicable.append((prefix, canon_tags))
    applicable.sort(key=lambda row: len(row[0]))
    for _, canon_tags in applicable:
        for key, value in canon_tags.items():
            if key not in merged:
                merged[key] = value
    return merged


def resolve_provider_scope(provider_key: str, policy: dict[str, Any]) -> str:
    aliases = policy.get("provider_aliases", {})
    return str(aliases.get(provider_key, provider_key))


def is_unknown_value(value: str) -> bool:
    return value == KNOWN_AFTER_APPLY


def plan_index(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for row in plan.get("resource_changes", []):
        idx[str(row["address"])] = row
    return idx


def effective_before_tags(
    row: dict[str, Any],
    plan: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, str]:
    actions = row.get("change", {}).get("actions", [])
    address = str(row["address"])
    before_raw = row.get("change", {}).get("before")
    tags = display_to_canonical((before_raw or {}).get("tags") if before_raw else None, policy)

    if "move" in actions:
        prev = row.get("previous_address")
        if prev:
            prev_row = plan_index(plan).get(str(prev))
            if prev_row:
                prev_before = prev_row.get("change", {}).get("before")
                prev_tags = display_to_canonical(
                    (prev_before or {}).get("tags") if prev_before else None,
                    policy,
                )
                for key, value in prev_tags.items():
                    if key not in tags:
                        tags[key] = value

    return apply_module_defaults(address, tags, policy)


def effective_after_tags(
    row: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[dict[str, str], list[str]]:
    address = str(row["address"])
    after_raw = row.get("change", {}).get("after")
    raw_tags = display_to_canonical((after_raw or {}).get("tags") if after_raw else None, policy)
    unknown: list[str] = []
    known: dict[str, str] = {}
    for key, value in raw_tags.items():
        if is_unknown_value(value):
            unknown.append(key)
        else:
            known[key] = value
    merged = apply_module_defaults(address, known, policy)
    return merged, sorted(unknown)


def normalize_resources(plan: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    for row in plan.get("resource_changes", []):
        actions = list(row.get("change", {}).get("actions", []))
        if actions == ["no-op"]:
            continue
        address = str(row["address"])
        provider_key = str(row.get("provider_key", ""))
        before = effective_before_tags(row, plan, policy)
        after, unknown = effective_after_tags(row, policy)
        resources.append(
            {
                "address": address,
                "previous_address": row.get("previous_address"),
                "actions": actions,
                "provider_key": provider_key,
                "provider_scope": resolve_provider_scope(provider_key, policy),
                "effective_tags_before": dict(sorted(before.items())),
                "effective_tags_after": dict(sorted(after.items())),
                "unknown_keys_after": unknown,
                "moved": "move" in actions,
            }
        )
    resources.sort(key=lambda r: r["address"])
    return resources


def expected_stage(plan_path: Path, policy_path: Path) -> dict[str, Any]:
    plan = load_json(plan_path)
    policy = load_json(policy_path)
    return {
        "schema": STAGING_SCHEMA,
        "plan_digest": file_digest(plan_path),
        "policy_digest": file_digest(policy_path),
        "evaluated_on": str(policy.get("evaluated_on", "")),
        "resources": normalize_resources(plan, policy),
    }


def waiver_matches(
    waiver: dict[str, Any],
    resource: str,
    tag_key: str,
    evaluated_on: str,
) -> bool:
    if tag_key not in waiver.get("keys", []):
        return False
    expires = str(waiver.get("expires", ""))
    if expires and evaluated_on > expires:
        return False
    match = waiver.get("match", {})
    if match.get("resource") == resource:
        return True
    prefix = match.get("module_prefix")
    if prefix and (resource == prefix or resource.startswith(prefix + ".")):
        return True
    return False


def pick_waiver(
    waivers: list[dict[str, Any]],
    resource: str,
    tag_key: str,
    evaluated_on: str,
) -> dict[str, Any] | None:
    resource_matches: list[dict[str, Any]] = []
    prefix_matches: list[dict[str, Any]] = []
    for waiver in waivers:
        if not waiver_matches(waiver, resource, tag_key, evaluated_on):
            continue
        match = waiver.get("match", {})
        if match.get("resource") == resource:
            resource_matches.append(waiver)
        elif match.get("module_prefix"):
            prefix_matches.append(waiver)
    if resource_matches:
        return resource_matches[0]
    if prefix_matches:
        return sorted(prefix_matches, key=lambda w: len(str(w.get("match", {}).get("module_prefix", ""))), reverse=True)[0]
    return None


def expected_report(stage: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    evaluated_on = str(stage.get("evaluated_on", policy.get("evaluated_on", "")))
    violations: list[dict[str, Any]] = []
    waived_rows: list[dict[str, Any]] = []
    waivers = policy.get("waivers", [])
    deny_rules = policy.get("deny_rules", [])

    for res in stage.get("resources", []):
        address = str(res["address"])
        actions = set(res.get("actions", []))
        scope = str(res.get("provider_scope", ""))
        before = res.get("effective_tags_before", {})
        after = res.get("effective_tags_after", {})
        unknown = set(res.get("unknown_keys_after", []))

        for key in sorted(unknown):
            violations.append(
                {
                    "code": "UNKNOWN_EXEMPT",
                    "severity": "info",
                    "resource": address,
                    "tag_key": key,
                    "rule_id": "",
                    "message": f"tag {key} unknown after apply",
                }
            )

        for rule in deny_rules:
            if str(rule.get("provider_scope")) != scope:
                continue
            rule_actions = set(rule.get("on_actions", []))
            if not actions.intersection(rule_actions):
                continue
            rule_id = str(rule.get("id", ""))
            for tag_key in rule.get("require_keys", []):
                if tag_key in unknown:
                    continue
                waiver = pick_waiver(waivers, address, str(tag_key), evaluated_on)
                if waiver:
                    waived_rows.append(
                        {
                            "waiver_id": str(waiver.get("id", "")),
                            "resource": address,
                            "tag_key": str(tag_key),
                        }
                    )
                    continue
                if tag_key not in after:
                    violations.append(
                        {
                            "code": "MISSING_REQUIRED_TAG",
                            "severity": "deny",
                            "resource": address,
                            "tag_key": str(tag_key),
                            "rule_id": rule_id,
                            "message": f"missing required tag {tag_key}",
                        }
                    )

        if "update" in actions:
            for tag_key in sorted(set(before.keys()) - set(after.keys())):
                if tag_key in unknown:
                    continue
                waiver = pick_waiver(waivers, address, tag_key, evaluated_on)
                if waiver:
                    waived_rows.append(
                        {
                            "waiver_id": str(waiver.get("id", "")),
                            "resource": address,
                            "tag_key": tag_key,
                        }
                    )
                    continue
                violations.append(
                    {
                        "code": "TAG_DRIFT_REMOVE",
                        "severity": "deny",
                        "resource": address,
                        "tag_key": tag_key,
                        "rule_id": "",
                        "message": f"tag {tag_key} removed on update",
                    }
                )

    violations.sort(key=lambda v: (v["resource"], v["tag_key"], v["code"]))
    waived_rows.sort(key=lambda w: (w["resource"], w["tag_key"], w["waiver_id"]))
    deny_count = sum(1 for v in violations if v["severity"] == "deny")
    return {
        "schema": REPORT_SCHEMA,
        "plan_digest": stage.get("plan_digest", ""),
        "policy_digest": stage.get("policy_digest", ""),
        "violations": violations,
        "waived": waived_rows,
        "summary": {
            "deny_count": deny_count,
            "waived_count": len(waived_rows),
            "unknown_exempt_count": sum(1 for v in violations if v["code"] == "UNKNOWN_EXEMPT"),
        },
    }


def expected_audit_exit(report: dict[str, Any]) -> int:
    return 2 if report["summary"]["deny_count"] > 0 else 0
