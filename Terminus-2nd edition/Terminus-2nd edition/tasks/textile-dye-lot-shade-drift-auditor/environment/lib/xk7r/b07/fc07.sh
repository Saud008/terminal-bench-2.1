#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/xk7r/b01/common.sh"
        source "${APP_ROOT}/lib/xk7r/b03/fc03.sh"
        source "${APP_ROOT}/lib/xk7r/b04/fc04.sh"
        source "${APP_ROOT}/lib/xk7r/b05/fc05.sh"
        source "${APP_ROOT}/lib/xk7r/b02/fc02.sh"

run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" ]] || exit 2

corr_snap="${CORR_SNAP_DIR}/${run_id}.json"
scenario=$(jq -r '.scenario' "$corr_snap")
root="${TB3_SCENARIO_ROOT:-${APP_ROOT}/fixtures/scenarios}"
base="${root}/${scenario}"
recipes=$(cat "${base}/recipes.json")
batches=$(cat "${base}/batches.json")
policy=$(read_policy)
warn=$(echo "$policy" | jq -r '.warn_delta_e')
fail=$(echo "$policy" | jq -r '.fail_delta_e')

rework_map=$(python3 - <<'PY' "${base}/rework.tsv"
import csv, json, sys
from pathlib import Path
path = Path(sys.argv[1])
rows = []
for line in path.read_text(encoding="utf-8").splitlines()[1:]:
    if not line.strip():
        continue
    b, s, e, reason, sup = line.split("\t")
    rows.append({
        "batch_id": b,
        "rework_start_epoch": int(s),
        "rework_end_epoch": int(e),
        "reason_code": reason,
        "supersedes_reading_before_epoch": int(sup),
    })
print(json.dumps(rows))
PY
)

enriched="[]"
while IFS= read -r row; do
  [[ -z "$row" ]] && continue
  batch_id=$(echo "$row" | jq -r '.batch_id')
  measured=$(echo "$row" | jq -r '.measured_at_epoch')
  batch=$(echo "$batches" | jq -c --arg b "$batch_id" '.batches[] | select(.batch_id == $b)')
  recipe_name=$(echo "$batch" | jq -r '.recipe_name')
  created=$(echo "$batch" | jq -r '.created_at_epoch')
  override=$(echo "$batch" | jq -r '.recipe_version_override // empty')
  as_of="$created"

  rework_applied="false"
  while IFS= read -r rw; do
    [[ -z "$rw" ]] && continue
    rb=$(echo "$rw" | jq -r '.batch_id')
    [[ "$rb" != "$batch_id" ]] && continue
    rs=$(echo "$rw" | jq -r '.rework_start_epoch')
    re=$(echo "$rw" | jq -r '.rework_end_epoch')
    sup=$(echo "$rw" | jq -r '.supersedes_reading_before_epoch')
    if [[ "$(in_rework_window "$measured" "$rs" "$re")" == "yes" ]]; then
      as_of=$(( sup - 1 ))
      rework_applied="true"
    fi
  done < <(echo "$rework_map" | jq -c '.[]')

  recipe=$(pick_recipe_version "$recipes" "$recipe_name" "$as_of" "$override")
  tL=$(echo "$recipe" | jq -r '.target_L')
  ta=$(echo "$recipe" | jq -r '.target_a')
  tb=$(echo "$recipe" | jq -r '.target_b')
  rver=$(echo "$recipe" | jq -r '.version')

  inherited=$(resolve_target_lab "$batches" "$batch_id")
  if [[ "$inherited" != "null" ]]; then
    tL=$(echo "$inherited" | jq -r '.L')
    ta=$(echo "$inherited" | jq -r '.a')
    tb=$(echo "$inherited" | jq -r '.b')
  fi

  L=$(echo "$row" | jq -r '.L')
  a=$(echo "$row" | jq -r '.a')
  b=$(echo "$row" | jq -r '.b')
          delta=$(cie76_delta "$L" "$a" "$b" "$tL" "$ta" "$tb")

  drift="reject"
  awk_ok=$(python3 - <<PY "$delta" "$warn" "$fail"
d,w,f = map(float, __import__("sys").argv[1:])
if d <= w: print("within")
elif d <= f: print("watch")
else: print("reject")
PY
)

  enriched=$(echo "$enriched" | jq --argjson base "$row" --argjson tL "$tL" --argjson ta "$ta" --argjson tb "$tb" \
    --arg rver "$rver" --argjson de "$delta" --arg dc "$awk_ok" --argjson rw "$([[ "$rework_applied" == true ]] && echo true || echo false)" \
    '. + [($base + {target_L: $tL, target_a: $ta, target_b: $tb, recipe_version: $rver, delta_e: $de, drift_class: $dc, rework_applied: $rw})]')
done < <(jq -c '.rows[]' "$corr_snap")

sorted=$(echo "$enriched" | jq 'sort_by(.batch_id, .reading_id)')
cdigest=$(echo "$sorted" | jq -c '.' | sha256sum | awk '{print $1}')
jq --argjson rows "$sorted" --arg cd "$cdigest" '.rows = $rows | .correlated = true | .correlation_digest = $cd' "$corr_snap" > "${corr_snap}.tmp"
mv "${corr_snap}.tmp" "$corr_snap"
echo "correlated ${run_id}"
