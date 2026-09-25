#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/lib/bundleio/resolve.sh"
source "${APP_ROOT}/lib/attpipe/p01.sh"
source "${APP_ROOT}/lib/attpipe/p02.sh"
source "${APP_ROOT}/lib/attpipe/p03.sh"
source "${APP_ROOT}/lib/attpipe/p04.sh"
source "${APP_ROOT}/lib/attpipe/p05.sh"
source "${APP_ROOT}/lib/attpipe/p06.sh"

bundle=""
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle) bundle="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
done
[[ -n "$bundle" && -n "$run_id" ]] || exit 2

base=$(resolve_bundle_base "$bundle")
meta=$(load_bundle_json "$bundle")
defconfig="${base}/defconfig"
frag_dir="${base}/fragments"
deps=$(cat "${base}/deps.json")
policy=$(cat "${base}/policy.json")

frag_order="[]"
while IFS= read -r frag; do
  [[ -z "$frag" ]] && continue
  frag_order=$(echo "$frag_order" | jq --arg f "$frag" '. + [$f]')
done < <(list_fragments_ordered "$frag_dir")

raw_merged=$(merge_layers "$defconfig" "$frag_dir")
after_deps=$(apply_deps_closure "$raw_merged" "$deps")
violations=$(scan_policy_violations "$after_deps" "$policy")
digest=$(stage_digest "$run_id" "$bundle" "$frag_order" "$after_deps")

body=$(jq -n \
  --arg run_id "$run_id" \
  --arg bundle "$bundle" \
  --argjson fragment_order "$frag_order" \
  --argjson raw_merged "$raw_merged" \
  --argjson after_deps "$after_deps" \
  --argjson policy_violations "$violations" \
  --arg deps "$deps" \
  --arg policy "$policy" \
  --arg stage_digest "$digest" \
  '{run_id, bundle, fragment_order, raw_merged, after_deps, policy_violations, deps, policy, stage_digest}')

echo "$body" > "${APP_ROOT}/state/kcfg-stage.json"
mkdir -p "${APP_ROOT}/work"
echo "$body" > "${APP_ROOT}/work/${run_id}-stage-build.json"
echo "compiled stage for ${bundle} run ${run_id}"
