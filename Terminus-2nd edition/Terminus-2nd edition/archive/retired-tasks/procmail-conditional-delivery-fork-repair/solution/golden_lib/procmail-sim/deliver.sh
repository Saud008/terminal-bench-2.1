#!/usr/bin/env bash
# Delivery record accumulation for snapshot export.
PM_DELIVERIES_JSON='[]'
PM_DUP_SUPPRESSED=0

deliver_reset() {
  PM_DELIVERIES_JSON='[]'
  PM_DUP_SUPPRESSED=0
}

deliver_record() {
  local msg_id="$1" mbox="$2" rid="$3" reason="$4"
  local exists
  exists="$(jq --arg m "$msg_id" --arg b "$mbox" --arg r "$rid" \
    '[.[] | select(.message_id==$m and .mbox==$b and .recipe_id==$r)] | length' <<<"$PM_DELIVERIES_JSON")"
  if [[ "$exists" != "0" ]]; then
    PM_DUP_SUPPRESSED=$((PM_DUP_SUPPRESSED + 1))
    return 0
  fi
  PM_DELIVERIES_JSON="$(jq --arg m "$msg_id" --arg b "$mbox" --arg r "$rid" --arg re "$reason" \
    '. + [{message_id:$m, mbox:$b, recipe_id:$r, reason:$re}]' <<<"$PM_DELIVERIES_JSON")"
}

deliver_count() {
  jq 'length' <<<"$PM_DELIVERIES_JSON"
}
