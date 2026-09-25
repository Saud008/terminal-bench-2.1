#!/usr/bin/env bash

source /app/lib/rule_lexer.sh
source /app/lib/table_commit_order.sh
source /app/lib/chain_policy_mode.sh
source /app/lib/rule_counter_mode.sh
source /app/lib/nat_mark_bridge.sh
source /app/lib/ct_order_mode.sh
source /app/lib/ingest.sh
source /app/lib/export_gate.sh

simulate_restore() {
  local restore="$1"
  local seed="$2"
  local export_path="$3"
  local staging="/app/state/work/simulate-$$.staging.json"

  if ! ingest_restore "$restore" "$staging"; then
    return 2
  fi

  export_from_staging "$staging" "$seed" "$export_path"
  local rc=$?
  rm -f "$staging" "$(staging_merge_path_for "$staging")"
  return "$rc"
}
