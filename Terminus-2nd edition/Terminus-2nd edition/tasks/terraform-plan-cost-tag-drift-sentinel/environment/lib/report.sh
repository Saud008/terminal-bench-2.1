#!/usr/bin/env bash
# BROKEN baseline: ignores waivers and unknown exemptions.
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
deny_rules = policy.get("deny_rules", [])
violations = []
for res in stage.get("resources", []):
    address = str(res["address"])
    actions = set(res.get("actions", []))
    scope = str(res.get("provider_scope", ""))
    after = res.get("effective_tags_after", {})
    for rule in deny_rules:
        if str(rule.get("provider_scope")) != scope:
            continue
        if not actions.intersection(set(rule.get("on_actions", []))):
            continue
        rule_id = str(rule.get("id", ""))
        for tag_key in rule.get("require_keys", []):
            if tag_key not in after:
                violations.append({
                    "code": "MISSING_REQUIRED_TAG",
                    "severity": "deny",
                    "resource": address,
                    "tag_key": str(tag_key),
                    "rule_id": rule_id,
                    "message": f"missing required tag {tag_key}",
                })
violations.sort(key=lambda v: (v["resource"], v["tag_key"], v["code"]))
deny_count = len(violations)
report = {
    "schema": "tag-violation-report/1",
    "plan_digest": stage.get("plan_digest", ""),
    "policy_digest": stage.get("policy_digest", ""),
    "violations": violations,
    "waived": [],
    "summary": {
        "deny_count": deny_count,
        "waived_count": 0,
        "unknown_exempt_count": 0,
    },
}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(deny_count)
PY
}
