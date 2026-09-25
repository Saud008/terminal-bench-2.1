#!/usr/bin/env bash
# Environment commit, pending auth env, rollback.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

: "${PAMREPLAY_ENV_JSON:={}}"
: "${PAMREPLAY_ENV_SNAPSHOT:={}}"
: "${PAMREPLAY_PENDING_AUTH_JSON:=[]}"

pamreplay_env_reset() {
  PAMREPLAY_ENV_JSON="{}"
  PAMREPLAY_ENV_SNAPSHOT="{}"
  PAMREPLAY_PENDING_AUTH_JSON="[]"
}

pamreplay_env_snapshot() {
  PAMREPLAY_ENV_SNAPSHOT="${PAMREPLAY_ENV_JSON}"
}

pamreplay_env_apply_args() {
  local phase="$1"
  shift
  local args_json
  args_json="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' -- "$@")"
  python3 - "$phase" "$args_json" "$PAMREPLAY_ENV_JSON" "$PAMREPLAY_PENDING_AUTH_JSON" <<'PY'
import json, sys

phase = sys.argv[1]
args = json.loads(sys.argv[2])
env = json.loads(sys.argv[3])
pending = json.loads(sys.argv[4])

for raw in args:
    if "=" not in raw:
        continue
    key, value = raw.split("=", 1)
    if phase == "auth":
        pending.append([key, value])
    else:
        env[key] = value

print(json.dumps(env))
print(json.dumps(pending))
PY
}

pamreplay_env_read() {
  local phase="$1"
  shift
  local -a _lines=()
  mapfile -t _lines < <(pamreplay_env_apply_args "$phase" "$@")
  PAMREPLAY_ENV_JSON="${_lines[0]}"
  PAMREPLAY_PENDING_AUTH_JSON="${_lines[1]}"
}

pamreplay_env_commit_auth_phase() {
  PAMREPLAY_ENV_JSON="$(python3 - "$PAMREPLAY_ENV_JSON" "$PAMREPLAY_PENDING_AUTH_JSON" <<'PY'
import json, sys
env = json.loads(sys.argv[1])
pending = json.loads(sys.argv[2])
if pending:
    key, value = pending[-1]
    env[key] = value
print(json.dumps(env))
PY
)"
  PAMREPLAY_PENDING_AUTH_JSON="[]"
}

pamreplay_env_discard_auth_pending() {
  echo "${PAMREPLAY_ENV_JSON}"
}

pamreplay_env_rollback() {
  PAMREPLAY_ENV_JSON="${PAMREPLAY_ENV_SNAPSHOT}"
}

pamreplay_env_export_object() {
  echo "${PAMREPLAY_ENV_JSON}"
}
