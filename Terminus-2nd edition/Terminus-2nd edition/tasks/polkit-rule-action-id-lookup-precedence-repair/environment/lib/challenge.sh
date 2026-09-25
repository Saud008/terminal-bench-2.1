#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pk_apply_challenge() {
  local token="$1"
  local challenge="$2"
  local prior_json="$3"
  local seat="$4"
  python3 - "$token" "$challenge" "$prior_json" "$seat" <<'PY'
import json, sys

token = sys.argv[1]
challenge = sys.argv[2] if sys.argv[2] not in ("null", "") else None
prior_raw = sys.argv[3]
seat = sys.argv[4]
prior = json.loads(prior_raw) if prior_raw not in ("null", "") else None

def finish(decision, echoed, implicit):
    print(json.dumps({"decision": decision, "challenge": echoed, "implicit": implicit}))

if challenge is None:
    if token == "yes":
        finish("allow", None, True)
    elif token == "no":
        finish("deny", None, False)
    else:
        finish("challenge", token, False)
    raise SystemExit

if challenge == "auth_self":
    if prior and prior.get("challenge") == "auth_admin_keep" and prior.get("seat") == seat:
        finish("allow", None, False)
        raise SystemExit
    if prior and prior.get("challenge") == "auth_admin" and prior.get("seat") == seat and token in {"auth_self", "auth_admin"}:
        finish("allow", None, False)
        raise SystemExit
    if token == "no":
        finish("deny", None, False)
    else:
        finish("challenge", "auth_self", False)
    raise SystemExit

if challenge in {"auth_admin", "auth_admin_keep"}:
    if token == "no":
        finish("deny", None, False)
        raise SystemExit
    if prior and prior.get("seat") == seat:
        if prior.get("challenge") == challenge:
            finish("allow", None, False)
            raise SystemExit
        if challenge == "auth_admin" and prior.get("challenge") == "auth_admin_keep":
            finish("allow", None, False)
            raise SystemExit
    finish("challenge", challenge, False)
    raise SystemExit

finish("challenge", challenge, False)
PY
}
