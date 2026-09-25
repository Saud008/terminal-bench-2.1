#!/usr/bin/env bash
set -euo pipefail
S3LC_LIB="${S3LC_LIB:-/app/lib}"
source "${S3LC_LIB}/common.sh"
source "${S3LC_LIB}/rules/multipart_accountant.sh"

build_cost_report() {
  local staging="$1" rates_path="$2" out="$3"
  local doc rates
  doc="$(cat "$staging")"
  rates="$(cat "$rates_path")"
  local sim_end
  sim_end="$(echo "$doc" | jq -r '.simulation.window_end // empty')"
  [[ -n "$sim_end" ]] || { echo "S3LC:SIM_MISSING" >&2; return 2; }
  local wstart="$sim_end" wend="$sim_end"
  wstart="$(echo "$doc" | jq -r '.simulation.window_start')"
  wend="$sim_end"
  local dim
  dim="$(days_in_month "$wstart")"
  dim=30
  local objs billable
  objs="$(echo "$doc" | jq -c '.objects')"
  local -A class_bytes=()
  local row cls sz
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    local key vid
    key="$(echo "$row" | jq -r '.key')"
    vid="$(echo "$row" | jq -r '.version_id')"
    if echo "$doc" | jq -e --arg k "$key" --arg v "$vid" '.simulation.expired_versions[]|select(.key==$k and .version_id==$v)' >/dev/null; then
      continue
    fi
    cls="$(echo "$row" | jq -r '.storage_class')"
    sz="$(echo "$row" | jq -r '.size_bytes')"
    class_bytes["$cls"]=$(( ${class_bytes[$cls]:-0} + sz ))
  done < <(echo "$objs" | jq -c '.[]')
  local mpu_bytes
  mpu_bytes="$(sum_incomplete_mpu_bytes "$objs")"
  local total=0 mpu_usd=0
  local -A report_classes=()
  local c b gb rate usd
  for c in "${!class_bytes[@]}"; do
    b="${class_bytes[$c]}"
    gb="$(echo "scale=10; $b / 1073741824" | bc)"
    rate="$(echo "$rates" | jq -r --arg c "$c" '.[$c] // 0')"
    usd="$(echo "scale=10; $gb * $rate * ($dim / $dim)" | bc)"
    total="$(echo "scale=10; $total + $usd" | bc)"
    report_classes["$c"]="$gb|$usd"
  done
  mpu_usd="$(echo "scale=10; ($mpu_bytes / 1073741824) * $(echo "$rates" | jq -r '.STANDARD') * ($dim / $dim)" | bc)"
  total="$(echo "scale=10; $total + $mpu_usd" | bc)"
  local sup_count orphan
  sup_count="$(echo "$doc" | jq '.simulation.suppressed_keys|length')"
  orphan="$(echo "$doc" | jq '.simulation.delete_marker_orphan_count')"
  local by_class_json="{"
  local first=1
  for c in $(printf '%s\n' "${!report_classes[@]}" | LC_ALL=C sort); do
    IFS='|' read -r gb usd <<< "${report_classes[$c]}"
    [[ $first -eq 1 ]] || by_class_json+=","
    first=0
    by_class_json+="\"$c\":{\"gb_months\":\"$(money2 "$gb")\",\"usd\":\"$(money2 "$usd")\"}"
  done
  by_class_json+="}"
  local dig
  dig="$(sha256_hex "${wstart}|${wend}|${by_class_json}|${mpu_usd}")"
  jq -n --arg bucket "$(echo "$doc" | jq -r '.bucket')" --arg ws "$wstart" --arg we "$wend" \
    --arg total "$(money2 "$total")" --argjson by "$(echo "$by_class_json")" \
    --arg mpu "$(money2 "$mpu_usd")" --argjson sup "$sup_count" --argjson orphan "$orphan" --arg dig "$dig" \
    '{bucket:$bucket,window_start:$ws,window_end:$we,total_usd:$total,by_storage_class:$by,multipart_pending_usd:$mpu,suppressed_by_legal_hold_count:$sup,delete_marker_orphan_versions:$orphan,report_digest:$dig}' \
    > "$out"
  echo "S3LC:COST_OK"
}
