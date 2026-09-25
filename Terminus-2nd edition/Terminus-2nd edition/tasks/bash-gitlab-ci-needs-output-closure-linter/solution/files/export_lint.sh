#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/lib/gclint/stage_order.sh"
source "${APP_ROOT}/lib/gclint/needs_graph.sh"

run_id=""
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" && -n "$output" ]] || exit 2

staging="${APP_ROOT}/state/gclint-staging.json"
snap=$(cat "$staging")
stages=$(echo "$snap" | jq -c '.stages // []')
jobs=$(echo "$snap" | jq -c '.jobs // []')

findings="[]"
# duplicate matrix
while IFS= read -r job; do
  name=$(echo "$job" | jq -r '.name')
  if [[ "$(echo "$job" | jq -r '.duplicate')" == "true" ]]; then
    findings=$(echo "$findings" | jq --arg n "$name" \
      '. + [{code:"MATRIX_DUPLICATE",severity:"error",job:$n,message:"duplicate matrix expansion"}]')
  fi
done < <(echo "$jobs" | jq -c '.[]')

# stage order + missing needs
while IFS= read -r job; do
  active=$(echo "$job" | jq -r '.active')
  [[ "$active" != "true" ]] && continue
  jname=$(echo "$job" | jq -r '.name')
  jstage=$(echo "$job" | jq -r '.stage')
  while IFS= read -r edge; do
    [[ -z "$edge" ]] && continue
    opt=$(echo "$edge" | jq -r '.optional // false')
    [[ "$opt" == "true" ]] && continue
    need=$(echo "$edge" | jq -r '.job')
    prod=$(echo "$jobs" | jq -c --arg n "$need" '.[] | select(.name==$n)')
    if [[ -z "$prod" ]]; then
      findings=$(echo "$findings" | jq --arg j "$jname" --arg n "$need" \
        '. + [{code:"NEED_MISSING",severity:"error",job:$j,message:("missing need "+$n)}]')
      continue
    fi
    pstage=$(echo "$prod" | jq -r '.stage')
    if ! needs_stage_ok "$stages" "$jstage" "$pstage"; then
      findings=$(echo "$findings" | jq --arg j "$jname" --arg n "$need" \
        '. + [{code:"STAGE_ORDER",severity:"error",job:$j,message:("need "+$n+" stage order violation")}]')
    fi
  done < <(echo "$job" | jq -c '.needs[]?')
done < <(echo "$jobs" | jq -c '.[]')

findings=$(python3 - <<'PY' "$findings")
import hashlib, json, sys
findings = json.loads(sys.argv[1])
findings.sort(key=lambda f: (f["job"], f["code"]))
summary = {"error": 0, "warn": 0, "info": 0}
for f in findings:
    summary[f["severity"]] = summary.get(f["severity"], 0) + 1
audit = hashlib.sha256(json.dumps({"codes": [f["code"] for f in findings], "summary": summary}, sort_keys=True).encode()).hexdigest()
print(json.dumps({"findings": findings, "summary": summary, "audit_digest": audit}))
PY

err=$(echo "$findings" | jq -r '.summary.error')
warn=$(echo "$findings" | jq -r '.summary.warn')
info=$(echo "$findings" | jq -r '.summary.info')
audit=$(echo "$findings" | jq -r '.audit_digest')
findings=$(echo "$findings" | jq -c '.findings')

jq -n --arg run_id "$run_id" --argjson findings "$findings" \
  --argjson summary "$(jq -n --argjson e "$err" --argjson w "$warn" --argjson i "$info" '{error:$e,warn:$w,info:$i}')" \
  --arg audit "$audit" \
  '{run_id:$run_id,findings:$findings,summary:$summary,audit_digest:$audit}' > "$output"
