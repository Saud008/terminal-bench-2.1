#!/usr/bin/env bash
set -euo pipefail
S3LC_LIB="${S3LC_LIB:-/app/lib}"
source "${S3LC_LIB}/zq7/m02.sh"
source "${S3LC_LIB}/zq7/m03.sh"
source "${S3LC_LIB}/rules/delete_marker_handler.sh"
source "${S3LC_LIB}/zq7/m04.sh"
source "${S3LC_LIB}/rules/multipart_accountant.sh"
source "${S3LC_LIB}/common.sh"

run_simulation() {
  local staging="$1" rules_path="$2" holds_path="$3" wstart="$4" wend="$5"
  local doc rules holds
  doc="$(cat "$staging")"
  rules="$(cat "$rules_path")"
  holds="$(cat "$holds_path")"
  local objs marked rules_json
  objs="$(echo "$doc" | jq -c '.objects')"
  marked="$(mark_current_versions "$objs")"
  marked="$(dedupe_completed_mpu "$marked")"
  rules_json="$(echo "$rules" | jq -c '.')"
  local -a suppressed=() transitions=() expired=() billable=()
  local row key tags rule age cls nc_age dm_orphan=0
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    key="$(echo "$row" | jq -r '.key')"
    tags="$(echo "$row" | jq -c '.tags')"
    if key_suppressed "$marked" "$key" "$holds" "$wend"; then
      suppressed+=("$key")
      billable+=("$row")
      continue
    fi
    rule="$(pick_winning_rule "$tags" "$rules_json")"
    [[ -z "$rule" ]] && { billable+=("$row"); continue; }
    local lm nc lm_date nc_date
    lm="$(echo "$row" | jq -r '.last_modified')"
    lm_date="${lm:0:10}"
    age="$(days_between "$lm_date" "$wend")"
    cls="$(echo "$row" | jq -r '.storage_class')"
    if [[ "$(echo "$row" | jq -r '.current_version')" == "true" && "$(echo "$row" | jq -r '.is_delete_marker')" == "true" ]]; then
      billable+=("$row")
      continue
    fi
    if is_incomplete_mpu "$row"; then
      billable+=("$row")
      continue
    fi
    cls="$(apply_transitions "$age" "$rule" "$cls")"
    if [[ "$(echo "$row" | jq -r '.current_version')" == "false" ]]; then
      nc="$(echo "$row" | jq -r '.noncurrent_since')"
      nc_date="${nc:0:10}"
      nc_age="$(days_between "$nc_date" "$wend")"
      if should_expire_noncurrent "$nc_age" "$rule"; then
        expired+=("${key}|$(echo "$row" | jq -r '.version_id')")
        continue
      fi
    else
      if should_expire "$age" "$rule"; then
        expired+=("${key}|$(echo "$row" | jq -r '.version_id')")
        continue
      fi
    fi
    transitions+=("${key}|$(echo "$row" | jq -r '.version_id')|${cls}")
    billable+=("$(echo "$row" | jq -c --arg c "$cls" '.storage_class=$c')")
  done < <(echo "$marked" | jq -c '.[]')
  local k
  for k in $(echo "$marked" | jq -r 'map(select(.current_version and .is_delete_marker)|.key)|.[]'); do
    dm_orphan=$((dm_orphan + $(echo "$marked" | jq --arg k "$k" '[.[]|select(.key==$k and (.current_version|not) and (.is_delete_marker|not))]|length')))
  done
  local sup_sorted tran_sorted exp_sorted dig
  sup_sorted="$(printf '%s\n' "${suppressed[@]}" | LC_ALL=C sort -u | jq -R -s -c 'split("\n")|map(select(length>0))')"
  tran_sorted="$(printf '%s\n' "${transitions[@]}" | LC_ALL=C sort | jq -R -s -c 'split("\n")|map(select(length>0))|map(split("|"))|map({key:.[0],version_id:.[1],storage_class:.[2]})')"
  exp_sorted="$(printf '%s\n' "${expired[@]}" | LC_ALL=C sort | jq -R -s -c 'split("\n")|map(select(length>0))|map(split("|"))|map({key:.[0],version_id:.[1]})')"
  dig="$(sha256_hex "${wstart}|${wend}|${tran_sorted}|${exp_sorted}")"
  jq --argjson marked "$marked" --argjson sup "$sup_sorted" --argjson tran "$tran_sorted" \
    --argjson exp "$exp_sorted" --arg ws "$wstart" --arg we "$wend" --argjson orphan "$dm_orphan" --arg dig "$dig" \
    '.objects=$marked | .simulation={window_start:$ws,window_end:$we,suppressed_keys:$sup,transitions_applied:$tran,expired_versions:$exp,delete_marker_orphan_count:$orphan,simulation_digest:$dig}' \
    <<< "$doc" > "${staging}.tmp" && mv "${staging}.tmp" "$staging"
  echo "S3LC:SIM_OK"
}
