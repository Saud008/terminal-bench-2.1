#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/pk87/matrix/matrix_expand.sh"
source "${APP_ROOT}/internal/pk87/rules/rules_eval.sh"
source "${APP_ROOT}/internal/pk87/needs/stage_order.sh"
source "${APP_ROOT}/internal/pk87/needs/needs_graph.sh"
source "${APP_ROOT}/internal/pk87/needs/artifact_closure.sh"
source "${APP_ROOT}/internal/pk87/staging/staging_writer.sh"

run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" ]] || exit 2

ingest="${APP_ROOT}/work/${run_id}-ingest.json"
pipeline=$(cat "$ingest")
stages=$(echo "$pipeline" | jq -c '.stages // []')

jobs_json="[]"
names_seen="[]"
while IFS= read -r item; do
  base=$(echo "$item" | jq -r '.base')
  row=$(echo "$item" | jq -c '.matrix_row')
  if [[ "$row" == "null" ]]; then
    jname="$base"
  else
    jname=$(matrix_expand_name "$base" "$row")
  fi
  if echo "$names_seen" | jq -e --arg n "$jname" 'index($n) != null' >/dev/null; then
    dup=true
  else
    dup=false
    names_seen=$(echo "$names_seen" | jq --arg n "$jname" '. + [$n]')
  fi
  job_def=$(echo "$pipeline" | jq --arg b "$base" '.[$b]')
  stage=$(echo "$job_def" | jq -r '.stage // "test"')
  rules=$(echo "$job_def" | jq -c '.rules // []')
  when_val=$(rules_pick_when "$rules")
  active=$(rules_job_active "$when_val")
  needs=$(parse_needs "$(echo "$job_def" | jq -c '.needs // null')")
  jobs_json=$(echo "$jobs_json" | jq             --arg name "$jname" --arg stage "$stage" --arg when "$when_val" --arg active "$active"             --argjson needs "$needs" --argjson dup "$dup"             '. + [{name: $name, stage: $stage, when: $when, active: ($active == "true"), needs: $needs, duplicate: $dup, artifacts: {paths: []}}]')
done < <(expand_matrix_jobs "$pipeline" | jq -c '.[]')

body=$(jq -n --arg run_id "$run_id" --argjson jobs "$jobs_json" --arg rules_fp "" \
  '{run_id: $run_id, jobs: $jobs, rules_fingerprint: $rules_fp, stages: '"$stages"'}')
digest=$(staging_digest "$body")
echo "$body" | jq --arg d "$digest" '. + {staging_digest: $d}' > "${APP_ROOT}/state/gclint-staging.json"
