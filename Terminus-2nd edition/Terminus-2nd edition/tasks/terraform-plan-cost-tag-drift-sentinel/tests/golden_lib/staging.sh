#!/usr/bin/env bash
# Write normalized plan-tag staging snapshot.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/parse_plan.sh"
source "${APP_ROOT}/lib/alias.sh"
source "${APP_ROOT}/lib/moved.sh"
source "${APP_ROOT}/lib/unknowns.sh"

write_staging_snapshot() {
  local plan_path="$1"
  local policy_path="$2"
  local staging_path="$3"
  local resources_json="[]"
  local row
  while IFS= read -r row; do
    [[ -z "${row}" ]] && continue
    local address provider_key scope before_json after_bundle after_json unknown_json
    address="$(jq -r '.address' <<<"${row}")"
    provider_key="$(jq -r '.provider_key // ""' <<<"${row}")"
    scope="$(resolve_provider_scope "${provider_key}" "${policy_path}")"
    before_json="$(effective_before_tags_json "${row}" "${plan_path}" "${policy_path}")"
    after_bundle="$(effective_after_tags_json "${row}" "${policy_path}")"
    after_json="$(jq -c '.tags' <<<"${after_bundle}")"
    unknown_json="$(jq -c '.unknown' <<<"${after_bundle}")"
    local actions_json moved_flag
    actions_json="$(jq -c '.change.actions' <<<"${row}")"
    moved_flag="$(jq -r 'if (.change.actions | index("move")) then true else false end' <<<"${row}")"
    local previous
    previous="$(jq -c '.previous_address' <<<"${row}")"
    local entry
    entry="$(jq -nc \
      --arg address "${address}" \
      --argjson previous "${previous}" \
      --argjson actions "${actions_json}" \
      --arg provider_key "${provider_key}" \
      --arg provider_scope "${scope}" \
      --argjson before "${before_json}" \
      --argjson after "${after_json}" \
      --argjson unknown "${unknown_json}" \
      --argjson moved "${moved_flag}" \
      '{address:$address, previous_address:$previous, actions:$actions, provider_key:$provider_key, provider_scope:$provider_scope, effective_tags_before:$before, effective_tags_after:$after, unknown_keys_after:$unknown, moved:$moved}')"
    resources_json="$(jq -c --argjson entry "${entry}" '. + [$entry]' <<<"${resources_json}")"
  done < <(plan_resources_json "${plan_path}")

  python3 - "${staging_path}" "${plan_path}" "${policy_path}" "${resources_json}" <<'PY'
import json, sys
from pathlib import Path

staging_path = Path(sys.argv[1])
plan_path = Path(sys.argv[2])
policy_path = Path(sys.argv[3])
resources = json.loads(sys.argv[4])
policy = json.loads(policy_path.read_text(encoding="utf-8"))

def digest_file(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()

resources.sort(key=lambda r: r["address"])
doc = {
    "schema": "plan-tag-stage/1",
    "plan_digest": digest_file(plan_path),
    "policy_digest": digest_file(policy_path),
    "evaluated_on": str(policy.get("evaluated_on", "")),
    "resources": resources,
}
staging_path.parent.mkdir(parents=True, exist_ok=True)
staging_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

update_run_registry() {
  local plan_path="$1"
  local registry_path="${2:-/app/state/run-registry.json}"
  python3 - "${plan_path}" "${registry_path}" <<'PY'
import hashlib, json, sys
from pathlib import Path

plan_path = Path(sys.argv[1])
registry_path = Path(sys.argv[2])
digest = hashlib.sha256(plan_path.read_bytes()).hexdigest()
doc = {"runs": []}
if registry_path.is_file():
    doc = json.loads(registry_path.read_text(encoding="utf-8"))
runs = doc.setdefault("runs", [])
if not runs or runs[-1].get("plan_digest") != digest:
    runs.append({"plan_digest": digest, "count": 1})
else:
    runs[-1]["count"] = int(runs[-1].get("count", 0)) + 1
registry_path.parent.mkdir(parents=True, exist_ok=True)
registry_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
