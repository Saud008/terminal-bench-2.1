#!/usr/bin/env bash
# Export violation report from staging snapshot only.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

write_violation_report() {
  local staging_path="$1"
  local policy_path="$2"
  local out_path="$3"
  python3 - "${staging_path}" "${policy_path}" "${out_path}" <<'PY'
import json, sys
from pathlib import Path

stage = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
policy = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
out_path = Path(sys.argv[3])
evaluated_on = str(stage.get("evaluated_on", policy.get("evaluated_on", "")))
waivers = policy.get("waivers", [])
deny_rules = policy.get("deny_rules", [])

def waiver_matches(waiver, resource, tag_key):
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

def pick_waiver(resource, tag_key):
    resource_hits = []
    prefix_hits = []
    for waiver in waivers:
        if not waiver_matches(waiver, resource, tag_key):
            continue
        match = waiver.get("match", {})
        if match.get("resource") == resource:
            resource_hits.append(waiver)
        elif match.get("module_prefix"):
            prefix_hits.append(waiver)
    if resource_hits:
        return resource_hits[0]
    if prefix_hits:
        return sorted(prefix_hits, key=lambda w: len(str(w.get("match", {}).get("module_prefix", ""))), reverse=True)[0]
    return None

violations = []
waived_rows = []
for res in stage.get("resources", []):
    address = str(res["address"])
    actions = set(res.get("actions", []))
    scope = str(res.get("provider_scope", ""))
    before = res.get("effective_tags_before", {})
    after = res.get("effective_tags_after", {})
    unknown = set(res.get("unknown_keys_after", []))

    for key in sorted(unknown):
        violations.append({
            "code": "UNKNOWN_EXEMPT",
            "severity": "info",
            "resource": address,
            "tag_key": key,
            "rule_id": "",
            "message": f"tag {key} unknown after apply",
        })

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
            waiver = pick_waiver(address, str(tag_key))
            if waiver:
                waived_rows.append({
                    "waiver_id": str(waiver.get("id", "")),
                    "resource": address,
                    "tag_key": str(tag_key),
                })
                continue
            if tag_key not in after:
                violations.append({
                    "code": "MISSING_REQUIRED_TAG",
                    "severity": "deny",
                    "resource": address,
                    "tag_key": str(tag_key),
                    "rule_id": rule_id,
                    "message": f"missing required tag {tag_key}",
                })

    if "update" in actions:
        for tag_key in sorted(set(before.keys()) - set(after.keys())):
            if tag_key in unknown:
                continue
            waiver = pick_waiver(address, tag_key)
            if waiver:
                waived_rows.append({
                    "waiver_id": str(waiver.get("id", "")),
                    "resource": address,
                    "tag_key": tag_key,
                })
                continue
            violations.append({
                "code": "TAG_DRIFT_REMOVE",
                "severity": "deny",
                "resource": address,
                "tag_key": tag_key,
                "rule_id": "",
                "message": f"tag {tag_key} removed on update",
            })

violations.sort(key=lambda v: (v["resource"], v["tag_key"], v["code"]))
waived_rows.sort(key=lambda w: (w["resource"], w["tag_key"], w["waiver_id"]))
deny_count = sum(1 for v in violations if v["severity"] == "deny")
report = {
    "schema": "tag-violation-report/1",
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
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(deny_count)
PY
}
