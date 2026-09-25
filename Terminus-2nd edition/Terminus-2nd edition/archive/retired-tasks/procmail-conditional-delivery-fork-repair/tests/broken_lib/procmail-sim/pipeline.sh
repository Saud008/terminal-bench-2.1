#!/usr/bin/env bash
# Simulate and audit orchestration for procmail-sim.
set -euo pipefail
SIM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SIM_DIR}/common.sh"
# shellcheck source=env.sh
source "${SIM_DIR}/env.sh"
# shellcheck source=lock.sh
source "${SIM_DIR}/lock.sh"
# shellcheck source=deliver.sh
source "${SIM_DIR}/deliver.sh"
# shellcheck source=fork.sh
source "${SIM_DIR}/fork.sh"
# shellcheck source=audit_export.sh
source "${SIM_DIR}/audit_export.sh"

PM_SKIPPED_JSON='[]'
PM_STATS_EVAL=0
PM_STATS_SKIP=0
PM_STATS_LOCK=0
PM_STATS_ORGMAIL=0

pm_parse_rc_json() {
  local rc="$1"
  python3 - "$rc" <<'PY'
import json, re, sys
from pathlib import Path

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines()
env = {}
idx = 0

def parse_block(parent, pos):
    block = []
    local = 0
    while pos < len(lines):
        line = lines[pos].strip()
        if not line or line.startswith("#"):
            pos += 1
            continue
        if line == "}":
            return block, pos + 1
        if line.startswith("SET "):
            _, rest = line.split(" ", 1)
            n, v = rest.split("=", 1)
            env[n.strip()] = v.strip()
            pos += 1
            continue
        if not line.startswith(":0"):
            pos += 1
            continue
        local += 1
        rid = f"{parent}.{local}" if parent else f"r{local}"
        token = line[2:].strip()
        flags = ""
        lock = None
        for part in token.split():
            if part.startswith("lock="):
                lock = part.split("=", 1)[1]
            else:
                flags += part
        pos += 1
        conds = []
        target = None
        children = []
        while pos < len(lines):
            inner = lines[pos].strip()
            if not inner or inner.startswith("#"):
                pos += 1
                continue
            if inner.startswith(":0") or inner == "}" or inner.startswith("SET "):
                break
            if inner == "{":
                pos += 1
                children, pos = parse_block(rid, pos)
                continue
            if inner.startswith("*"):
                conds.append(inner[1:].strip())
                pos += 1
                continue
            target = inner
            pos += 1
            break
        block.append({
            "rid": rid, "flags": flags, "lock": lock,
            "conditions": conds, "target": target, "children": children,
        })
    return block, pos

recipes, _ = parse_block(None, 0)
print(json.dumps({"env": env, "recipes": recipes}))
PY
}

pm_match_recipe() {
  local flags="$1"
  local conds_json="$2"
  local raw="$3"
  local headers="$4"
  local text="$raw"
  [[ "$flags" == *h* ]] && text="$headers"
  local n
  n="$(jq 'length' <<<"$conds_json")"
  local i=0
  while [[ "$i" -lt "$n" ]]; do
    local cond
    cond="$(jq -r ".[$i]" <<<"$conds_json")"
    if [[ "$cond" =~ ^\? ]]; then
      env_match_var_cond "$cond" "$headers" || return 1
    else
      grep -Eq "$cond" <<<"$text" || return 1
    fi
    i=$((i + 1))
  done
  return 0
}

pm_skip_add() {
  local rid="$1"
  local reason="$2"
  PM_SKIPPED_JSON="$(jq --arg r "$rid" --arg re "$reason" \
    '. + [{recipe_id:$r, reason:$re}]' <<<"$PM_SKIPPED_JSON")"
  PM_STATS_SKIP=$((PM_STATS_SKIP + 1))
}

pm_eval_block() {
  local block_json="$1"
  local msg_id="$2"
  local raw="$3"
  local headers="$4"
  local scope="$5"
  local any=0
  local count
  count="$(jq 'length' <<<"$block_json")"
  local i=0
  while [[ "$i" -lt "$count" ]]; do
    local recipe
    recipe="$(jq -c ".[$i]" <<<"$block_json")"
    local rid flags lock target children
    rid="$(jq -r '.rid' <<<"$recipe")"
    flags="$(jq -r '.flags' <<<"$recipe")"
    lock="$(jq -r '.lock // empty' <<<"$recipe")"
    target="$(jq -r '.target // empty' <<<"$recipe")"
    children="$(jq -c '.children' <<<"$recipe")"
    local conds
    conds="$(jq -c '.conditions' <<<"$recipe")"
    PM_STATS_EVAL=$((PM_STATS_EVAL + 1))
    local lock_path=""
    if [[ -n "$lock" ]]; then
      lock_path="$(lock_path_for "$scope" "$lock")"
      if ! lock_try_acquire "$lock_path"; then
        pm_skip_add "$rid" "lock_busy"
        i=$((i + 1))
        continue
      fi
      PM_STATS_LOCK=$((PM_STATS_LOCK + 1))
    fi
    local delivered=0
    if pm_match_recipe "$flags" "$conds" "$raw" "$headers"; then
      if [[ "$(jq 'length' <<<"$children")" -gt 0 ]]; then
        local child_scope="$scope"
        [[ "$scope" == "root" ]] && child_scope="$rid" || child_scope="${scope}/${rid}"
        if pm_eval_block "$children" "$msg_id" "$raw" "$headers" "$child_scope"; then
          delivered=1
        else
          fork_orgmail_fallback "$msg_id" "$rid" 0
          delivered=1
        fi
      fi
      if [[ -n "$target" ]]; then
        deliver_record "$msg_id" "$target" "$rid" "match"
        if [[ "$flags" == *h* && "$flags" == *c* ]]; then
          deliver_record "$msg_id" "$target" "$rid" "match"
        fi
        delivered=1
      fi
      if [[ "$delivered" -eq 1 ]]; then
        any=1
        [[ "$flags" != *c* ]] && break
      fi
    fi
    [[ -n "$lock_path" ]] && lock_release "$lock_path"
    i=$((i + 1))
  done
  [[ "$any" -eq 1 ]]
}

run_simulate() {
  local suite="$1"
  local snap="${2:-$SNAPSHOT_DEFAULT}"
  env_load_meta "$suite"
  local parsed
  parsed="$(pm_parse_rc_json "${suite}/procmail.rc")"
  local k v
  for k in HOST HOSTNAME ORGMAIL; do
    v="$(jq -r --arg k "$k" '.env[$k] // empty' <<<"$parsed")"
    if [[ -n "$v" ]]; then
      case "$k" in
        HOST) ENV_HOST="$v" ;;
        HOSTNAME) ENV_HOSTNAME="$v" ;;
        ORGMAIL) ENV_ORGMAIL="$v" ;;
      esac
    fi
  done
  local recipes
  recipes="$(jq -c '.recipes' <<<"$parsed")"
  deliver_reset
  PM_SKIPPED_JSON='[]'
  PM_STATS_EVAL=0
  PM_STATS_SKIP=0
  PM_STATS_LOCK=0
  PM_STATS_ORGMAIL=0
  declare -gA PM_ACTIVE_LOCKS=()
  local suite_id
  suite_id="$(jq -r '.suite_id // ""' "${suite}/suite.meta.json")"
  local msg_total=0
  mapfile -t _parts < <(python3 - "${suite}/messages.mbox" <<'PY'
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
chunks = re.split(r"(?=^From )", text, flags=re.M)
for c in chunks:
    c = c.strip("\n")
    if c.strip():
        print(c.replace("\n", "\\n").replace("\r", ""))
PY
)
  local chunk mid headers
  for chunk in "${_parts[@]}"; do
    chunk="${chunk//$'\\n'/$'\n'}"
    mid="$(grep -i '^Message-ID:' <<<"$chunk" | head -1 | sed 's/^[Mm]essage-[Ii][Dd]:[[:space:]]*//;s/[<>]//g' | pm_trim)"
    [[ -z "$mid" ]] && mid="$(printf '%s' "$chunk" | sha256sum | awk '{print $1}' | cut -c1-12)"
    headers="$(pm_headers_only "$chunk")"
    pm_eval_block "$recipes" "$mid" "$chunk" "$headers" "root" || true
    msg_total=$((msg_total + 1))
  done
  local orgmail_count
  orgmail_count="$(jq '[.[] | select(.reason=="orgmail_fork_fallback")] | length' <<<"$PM_DELIVERIES_JSON")"
  jq -n \
    --arg sid "$suite_id" \
    --arg host "$ENV_HOST" \
    --arg hn "$ENV_HOSTNAME" \
    --arg org "$ENV_ORGMAIL" \
    --argjson deliveries "$PM_DELIVERIES_JSON" \
    --argjson skipped "$PM_SKIPPED_JSON" \
    --argjson mt "$msg_total" \
    --argjson ev "$PM_STATS_EVAL" \
    --argjson sk "$PM_STATS_SKIP" \
    --argjson dc "$(deliver_count)" \
    --argjson ls "$PM_STATS_LOCK" \
    --argjson of "$orgmail_count" \
    --argjson ds "$PM_DUP_SUPPRESSED" \
    '{
      snapshot_version: 1,
      suite_id: $sid,
      environment: {HOST: $host, HOSTNAME: $hn, ORGMAIL: $org},
      deliveries: $deliveries,
      skipped_recipes: $skipped,
      stats: {
        messages_total: $mt,
        recipes_evaluated: $ev,
        recipes_skipped: $sk,
        deliveries_count: $dc,
        lock_serializations: $ls,
        orgmail_fallbacks: $of,
        duplicate_suppressed: $ds
      }
    }' >"$snap"
}

run_audit() {
  local snap="$1"
  local out="$2"
  audit_write "$snap" "$out"
}
