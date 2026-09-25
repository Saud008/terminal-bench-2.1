#!/usr/bin/env bash
set -euo pipefail

pam_result_name() {
  case "$1" in
    0) echo "success" ;;
    1) echo "ignore" ;;
    2) echo "auth_err" ;;
    4) echo "cred_insufficient" ;;
    6) echo "perm_denied" ;;
    7) echo "acct_expired" ;;
    9) echo "user_unknown" ;;
    *) echo "unknown" ;;
  esac
}

walk_auth_stack() {
  local modules_json="$1"
  local outcomes_json="$2"
  local subject="$3"
  python3 - "$modules_json" "$outcomes_json" "$subject" <<'PY'
import json, sys

modules = json.loads(sys.argv[1])
outcomes = json.loads(sys.argv[2])
subject = sys.argv[3]

def mod_base(name):
    return name.split("/")[-1]

def lookup(module, subject):
    base = mod_base(module)
    table = outcomes.get(base) or outcomes.get(module) or {}
    raw = table.get(subject, table.get("*", 0))
    if isinstance(raw, str):
        mapping = {
            "success": 0, "ignore": 1, "auth_err": 2,
            "cred_insufficient": 4, "perm_denied": 6,
            "acct_expired": 7, "user_unknown": 9,
        }
        return mapping.get(raw, 16)
    return int(raw)

def result_name(code):
    return {
        0: "success", 1: "ignore", 2: "auth_err", 4: "cred_insufficient",
        6: "perm_denied", 7: "acct_expired", 9: "user_unknown",
    }.get(code, "unknown")

steps = []
required_failed = False
first_required_code = 0
final_code = 0
final_reason = "ok"
short_circuited = False

auth_modules = [m for m in modules if m.get("type") == "auth"]

for idx, mod in enumerate(auth_modules):
    code = lookup(mod["module"], subject)
    control = mod["control"]
    step = {
        "index": idx,
        "module": mod["module"],
        "control": control,
        "result_code": code,
        "result": result_name(code),
    }
    steps.append(step)

    if short_circuited:
        continue

    if control == "requisite" and code != 0:
        final_code = code
        final_reason = "requisite_failure"
        short_circuited = True
        continue
    if control == "required" and code != 0:
        required_failed = True
        if first_required_code == 0:
            first_required_code = code
    if control == "sufficient" and code == 0 and not required_failed:
        final_code = 0
        final_reason = "sufficient_success"
        short_circuited = True

if not short_circuited:
    if required_failed:
        final_code = first_required_code
        final_reason = "required_failure"
    else:
        final_code = 0
        final_reason = "ok"

print(json.dumps({
    "steps": steps,
    "verdict_code": final_code,
    "verdict": result_name(final_code),
    "reason": final_reason,
}))
PY
}
