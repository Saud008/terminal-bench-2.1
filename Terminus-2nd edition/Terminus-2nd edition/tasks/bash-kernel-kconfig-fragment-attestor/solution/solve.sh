# Oracle solve — task identity bash-kernel-kconfig-fragment-attestor token kcfg7a2b
#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > /app/lib/attpipe/p02.sh <<'KCFG_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

list_fragments_ordered() {
  local dir="$1"
  find "$dir" -maxdepth 1 -type f -name '*.fragment' -printf '%f\n' | sort
}
KCFG_ORACLE_EOF
chmod +x /app/lib/attpipe/p02.sh
bash -n /app/lib/attpipe/p02.sh

cat > /app/lib/attpipe/p03.sh <<'KCFG_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/p01.sh"
source "$(dirname "${BASH_SOURCE[0]}")/p02.sh"

merge_layers() {
  local defconfig="$1"
  local frag_dir="$2"
  local merged="{}"
  merged=$(parse_kconfig_file "$defconfig")
  while IFS= read -r frag; do
    [[ -z "$frag" ]] && continue
    layer=$(parse_kconfig_file "${frag_dir}/${frag}")
    merged=$(jq -n --argjson base "$merged" --argjson layer "$layer" '$base + $layer')
  done < <(list_fragments_ordered "$frag_dir")
  echo "$merged"
}
KCFG_ORACLE_EOF
chmod +x /app/lib/attpipe/p03.sh
bash -n /app/lib/attpipe/p03.sh

cat > /app/lib/attpipe/p04.sh <<'KCFG_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

apply_deps_closure() {
  local symbols_json="$1"
  local deps_json="$2"
  python3 - <<'PY' "$symbols_json" "$deps_json"
import json, sys

symbols = json.loads(sys.argv[1])
deps = json.loads(sys.argv[2])
requires = deps.get("requires", {})
implies = deps.get("implies", {})
selects = deps.get("selects", {})

def is_enabled(val):
    return val in ("y", "m")

changed = True
while changed:
    changed = False
    for sym, val in list(symbols.items()):
        if not is_enabled(val):
            continue
        for req in requires.get(sym, []):
            if symbols.get(req) != "y":
                symbols[req] = "y"
                changed = True
        for child in implies.get(sym, []):
            if symbols.get(child) != "y":
                symbols[child] = "y"
                changed = True
    for parent, children in selects.items():
        if symbols.get(parent) == "y":
            for child in children:
                if symbols.get(child) != "y":
                    symbols[child] = "y"
                    changed = True
print(json.dumps(dict(sorted(symbols.items())), sort_keys=True))
PY
}
KCFG_ORACLE_EOF
chmod +x /app/lib/attpipe/p04.sh
bash -n /app/lib/attpipe/p04.sh

cat > /app/lib/attpipe/p05.sh <<'KCFG_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail

scan_policy_violations() {
  local symbols_json="$1"
  local policy_json="$2"
  python3 - <<'PY' "$symbols_json" "$policy_json"
import json, sys

symbols = json.loads(sys.argv[1])
policy = json.loads(sys.argv[2])
violations = []
for sym in policy.get("forbidden_if_set", []):
    if symbols.get(sym) in ("y", "m"):
        violations.append({"symbol": sym, "code": "forbidden_set", "detail": "symbol must not be enabled"})
for sym in policy.get("required_n", []):
    val = symbols.get(sym)
    if val not in (None, "n"):
        violations.append({"symbol": sym, "code": "required_n", "detail": "symbol must be disabled"})
for sym in policy.get("max_modular", []):
    if symbols.get(sym) == "y":
        violations.append({"symbol": sym, "code": "max_modular", "detail": "symbol must be modular or disabled"})
violations.sort(key=lambda v: v["symbol"])
print(json.dumps(violations))
PY
}
KCFG_ORACLE_EOF
chmod +x /app/lib/attpipe/p05.sh
bash -n /app/lib/attpipe/p05.sh

cat > /app/lib/attpipe/p08.sh <<'KCFG_ORACLE_EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"

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

stage=$(cat "${APP_ROOT}/state/kcfg-stage.json")
symbols_json=$(echo "$stage" | jq -c '.after_deps')
violations=$(echo "$stage" | jq -c '.policy_violations')

rows=$(python3 - <<'PY' "$symbols_json"
import json, sys
symbols = json.loads(sys.argv[1])
rows = [{"name": k, "value": v, "source_layer": "stage"} for k, v in sorted(symbols.items())]
print(json.dumps(rows))
PY
)

manifest_digest=$(python3 - <<'PY' "$rows"
import hashlib, json, sys
rows = json.loads(sys.argv[1])
slim = [{"name": r["name"], "value": r["value"], "source_layer": r["source_layer"]} for r in rows]
print(hashlib.sha256(json.dumps(slim, sort_keys=True).encode()).hexdigest())
PY
)

jq -n \
  --arg run_id "$run_id" \
  --argjson symbols "$rows" \
  --argjson policy_violations "$violations" \
  --arg manifest_digest "$manifest_digest" \
  '{run_id: $run_id, symbols: $symbols, policy_violations: $policy_violations, totals: {symbols: ($symbols|length), violations: ($policy_violations|length)}, manifest_digest: $manifest_digest}' \
  > "$output"
echo "manifest written to ${output}"
KCFG_ORACLE_EOF
chmod +x /app/lib/attpipe/p08.sh
bash -n /app/lib/attpipe/p08.sh

cat > /app/lib/attpipe/p07.sh <<'KCFG_ORACLE_EOF'
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
  --argjson deps "$deps" \
  --argjson policy "$policy" \
  --arg stage_digest "$digest" \
  '{run_id: $run_id, bundle: $bundle, fragment_order: $fragment_order, raw_merged: $raw_merged, after_deps: $after_deps, policy_violations: $policy_violations, deps: $deps, policy: $policy, stage_digest: $stage_digest}')

echo "$body" > "${APP_ROOT}/state/kcfg-stage.json"
mkdir -p "${APP_ROOT}/work"
echo "$body" > "${APP_ROOT}/work/${run_id}-stage-build.json"
echo "compiled stage for ${bundle} run ${run_id}"
KCFG_ORACLE_EOF
chmod +x /app/lib/attpipe/p07.sh
bash -n /app/lib/attpipe/p07.sh

bash /app/scripts/rebuild-kcfgattest.sh
bash /app/scripts/reset-state.sh

/app/bin/kcfgattest compile-stage --bundle minimal-net --run-id oracle-smoke >/dev/null
test -s /app/state/kcfg-stage.json
/app/bin/kcfgattest emit-manifest --run-id oracle-smoke --output /app/output/oracle-smoke.json >/dev/null
test -s /app/output/oracle-smoke.json
