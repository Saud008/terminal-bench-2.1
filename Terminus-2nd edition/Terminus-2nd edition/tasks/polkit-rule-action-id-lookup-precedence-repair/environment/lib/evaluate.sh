#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=merge_rules.sh
source "${APP_ROOT}/lib/merge_rules.sh"
# shellcheck source=subject_eval.sh
source "${APP_ROOT}/lib/subject_eval.sh"
# shellcheck source=action_registry.sh
source "${APP_ROOT}/lib/action_registry.sh"
# shellcheck source=challenge.sh
source "${APP_ROOT}/lib/challenge.sh"
# shellcheck source=auth_cache.sh
source "${APP_ROOT}/lib/auth_cache.sh"

cmd_evaluate() {
  local scenario_path=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --scenario) scenario_path="$2"; shift 2 ;;
      *) die "unknown evaluate arg: $1" ;;
    esac
  done
  [[ -n "$scenario_path" && -f "$scenario_path" ]] || die "missing --scenario PATH"

  local scenario_json action_id subject_json stack challenge prior_json seat
  scenario_json="$(cat "$scenario_path")"
  action_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["action_id"])' <<<"$scenario_json")"
  subject_json="$(python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)["subject"]))' <<<"$scenario_json")"
  stack="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["rules_stack"])' <<<"$scenario_json")"
  challenge="$(python3 -c 'import json,sys; c=json.load(sys.stdin).get("challenge"); print("" if c is None else c)' <<<"$scenario_json")"
  prior_json="$(python3 -c 'import json,sys; p=json.load(sys.stdin).get("prior_grant"); print("null" if p is None else json.dumps(p))' <<<"$scenario_json")"
  seat="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["subject"]["seat"])' <<<"$scenario_json")"

  local blocks_json matched source matched_rule token
  blocks_json="$(pk_merge_rules "$stack")"
  matched="$(python3 - "$blocks_json" "$action_id" "$subject_json" <<'PY'
import json, sys

blocks = json.loads(sys.argv[1])
action_id = sys.argv[2]
subject = json.loads(sys.argv[3])

def match_block(block):
    if block.get("action_id") != action_id:
        return False
    user = subject["user"]
    if block.get("user", "*") != "*" and block.get("user") != user:
        return False
    local = subject["local"]
    active = subject["active"]
    bl = block.get("local", "any")
    if bl != "any" and (bl == "true") != bool(local):
        return False
    ba = block.get("active", "any")
    if ba != "any" and (ba == "true") != bool(active):
        return False
    return True

winner = None
for block in blocks:
    if match_block(block):
        winner = block
if winner:
    print(json.dumps({"hit": True, "result": winner["result"], "source_file": winner["source_file"]}))
else:
    print(json.dumps({"hit": False}))
PY
)"

  local hit
  hit="$(python3 -c 'import json,sys; print("1" if json.loads(sys.stdin.read())["hit"] else "0")' <<<"$matched")"

  if [[ "$hit" == "1" ]]; then
    token="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["result"])' <<<"$matched")"
    matched_rule="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["source_file"])' <<<"$matched")"
    source="rule:${matched_rule}"
  else
    matched_rule=""
    local action_row fmt
    action_row="$(pk_lookup_action "$action_id")"
    fmt="$(python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print(d.get("format",""))' <<<"$action_row")"
    if [[ -z "$fmt" ]]; then
      python3 - <<'PY'
import json
print(json.dumps({"decision": "deny", "source": "none", "challenge": None, "implicit": False, "matched_rule": None}))
PY
      return 0
    fi
    local allow_active allow_inactive
    allow_active="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["allow_active"])' <<<"$action_row")"
    allow_inactive="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["allow_inactive"])' <<<"$action_row")"
    token="$(pk_map_subject "$subject_json" "$allow_active" "$allow_inactive")"
    source="action:${fmt}:${action_id}"
  fi

  local outcome decision echoed implicit user
  user="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["user"])' "$subject_json")"
  outcome="$(pk_apply_challenge "$token" "$challenge" "$prior_json" "$seat")"
  decision="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["decision"])' <<<"$outcome")"
  echoed="$(python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print("" if d["challenge"] is None else d["challenge"])' <<<"$outcome")"
  implicit="$(python3 -c 'import json,sys; print("1" if json.loads(sys.stdin.read())["implicit"] else "0")' <<<"$outcome")"

  if [[ "$decision" == "allow" && "$implicit" == "1" ]]; then
    if [[ "$(pk_cache_get "$action_id" "$user" "$seat")" == "1" ]]; then
      python3 - "$matched_rule" <<'PY'
import json, sys
print(json.dumps({"decision": "cached_allow", "source": "cache", "challenge": None, "implicit": True, "matched_rule": None}))
PY
      return 0
    fi
    pk_cache_set "$action_id" "$user" "$seat"
  fi

  python3 - "$decision" "$source" "$echoed" "$implicit" "$matched_rule" <<'PY'
import json, sys
decision, source, echoed, implicit, matched_rule = sys.argv[1:6]
print(json.dumps({
    "decision": decision,
    "source": source,
    "challenge": None if echoed == "" else echoed,
    "implicit": implicit == "1",
    "matched_rule": None if matched_rule == "" else matched_rule,
}))
PY
}
