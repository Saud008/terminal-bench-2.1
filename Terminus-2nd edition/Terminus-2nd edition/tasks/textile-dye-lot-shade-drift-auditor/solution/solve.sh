# Oracle solve — task identity textile-dye-lot-shade-drift-auditor token 01095579
# Oracle solve — textile-dye-lot-shade-drift-audito
#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > /app/lib/xk7r/b02/fc02.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

cie76_delta() {
  python3 - "$@" <<'PY'
import math, sys
l1, a1, b1, l2, a2, b2 = map(float, sys.argv[1:])
dl = l1 - l2
da = a1 - a2
db = b1 - b2
print(f"{math.sqrt(dl*dl + da*da + db*db):.6f}")
PY
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  cie76_delta "$@"
fi
SH
chmod +x /app/lib/xk7r/b02/fc02.sh

cat > /app/lib/xk7r/b03/fc03.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
source "${APP_ROOT}/lib/xk7r/b01/common.sh"

pick_recipe_version() {
  local recipes_json="$1"
  local recipe_name="$2"
  local as_of="$3"
  local override="$4"
  if [[ -n "$override" && "$override" != "null" ]]; then
    echo "$recipes_json" | jq -c --arg v "$override" '.recipes[] | select(.version == $v) | .' | head -n1
    return
  fi
  echo "$recipes_json" | jq -c --arg n "$recipe_name" --argjson t "$as_of" \
    '[.recipes[] | select(.recipe_name == $n and .effective_from_epoch <= $t)] | sort_by(.effective_from_epoch) | .[-1]'
}
SH
chmod +x /app/lib/xk7r/b03/fc03.sh

cat > /app/lib/xk7r/b04/fc04.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

resolve_target_lab() {
  local batches_json="$1"
  local batch_id="$2"
  local cur="$batch_id"
  while [[ -n "$cur" && "$cur" != "null" ]]; do
    tl=$(echo "$batches_json" | jq -c --arg b "$cur" '.batches[] | select(.batch_id == $b) | .target_lab')
    if [[ "$tl" != "null" ]]; then
      echo "$tl"
      return
    fi
    cur=$(echo "$batches_json" | jq -r --arg b "$cur" '.batches[] | select(.batch_id == $b) | .parent_batch_id // empty')
  done
  echo "null"
}
SH
chmod +x /app/lib/xk7r/b04/fc04.sh

cat > /app/lib/xk7r/b05/fc05.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

in_rework_window() {
  local measured="$1"
  local start="$2"
  local end="$3"
  if (( measured >= start && measured <= end )); then
    echo "yes"
  else
    echo "no"
  fi
}
SH
chmod +x /app/lib/xk7r/b05/fc05.sh

cat > /app/lib/xk7r/b08/fc08.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
CORR_SNAP_DIR="${APP_ROOT}/state/shade-correlation"

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

corr_snap="${CORR_SNAP_DIR}/${run_id}.json"
correlated=$(jq -r '.correlated' "$corr_snap")
[[ "$correlated" == "true" ]] || { echo "correlation snapshot not correlated" >&2; exit 3; }

drift_rows=$(jq -c '[.rows[] | {batch_id, reading_id, delta_e, drift_class, recipe_version, rework_applied}] | sort_by(.batch_id, .reading_id)' "$corr_snap")
audit=$(python3 - <<'PY' "$drift_rows"
import hashlib, json, sys
rows = json.loads(sys.argv[1])
print(hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest())
PY
)
jq -n --arg run_id "$run_id" --argjson drift_rows "$drift_rows" --arg audit "$audit" \
  '{run_id: $run_id, drift_rows: $drift_rows, totals: {row_count: ($drift_rows|length)}, audit_digest: $audit}' > "$output"
echo "exported ${run_id}"
SH
chmod +x /app/lib/xk7r/b08/fc08.sh

bash /app/scripts/rebuild-shadedrift.sh
bash /app/scripts/reset-state.sh
/app/bin/shadedrift ingest-scenario --scenario scarlet-base-lot --run-id oracle-smoke
/app/bin/shadedrift correlate --run-id oracle-smoke
/app/bin/shadedrift export-report --run-id oracle-smoke --output /app/output/oracle-smoke.json
