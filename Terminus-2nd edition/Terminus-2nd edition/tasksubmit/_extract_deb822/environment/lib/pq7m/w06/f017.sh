#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/lib/pq7m/w01/f010.sh"
source "${APP_ROOT}/lib/pq7m/w02/f011.sh"
source "${APP_ROOT}/lib/pq7m/w04/f015.sh"

scenario=""
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) scenario="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
done
[[ -n "$scenario" && -n "$run_id" ]] || exit 2

root="${TB3_SCENARIO_ROOT:-${APP_ROOT}/fixtures/scenarios}"
base="${root}/${scenario}"
meta=$(cat "${base}/scenario.json")
origins=$(read_deb822_stanzas "${base}/sources.sources")
prefs=$(python3 - <<'PY' "${base}/pin-rules.pref"
import json, sys
from pathlib import Path
prefs, cur = [], {}
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        if cur:
            prefs.append(cur)
            cur = {}
        continue
    if ":" in line:
        k, v = line.split(":", 1)
        cur[k.strip()] = v.strip()
if cur:
    prefs.append(cur)
print(json.dumps(prefs))
PY
)
ranked=$(rank_origins "$origins")
arch=$(echo "$meta" | jq -r '.target_arch // "amd64"')
queries=$(echo "$meta" | jq -c '.meta_queries // .queries // []')

package_rows="[]"
while IFS= read -r origin; do
  [[ -z "$origin" ]] && continue
  oid=$(echo "$origin" | jq -r '.["X-Source-Id"] // "origin"')
  idx="${base}/indices/${oid}.json"
  [[ -f "$idx" ]] || continue
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    package_rows=$(echo "$package_rows" | jq --argjson row "$row" --arg oid "$oid" \
      '. + [($row + {origin_id: $oid})]')
  done < <(cat "$idx" | jq -c '.[]')
done < <(echo "$ranked" | jq -c '.[]')

origin_fp=$(echo "$ranked" | jq -c '[.[].["X-Source-Id"]] | join("|")' | sha256sum | awk '{print $1}')
body=$(jq -n --arg run_id "$run_id" --arg scenario "$scenario" --arg arch "$arch" \
  --argjson origins "$ranked" --argjson preferences "$prefs" --argjson package_rows "$package_rows" \
  --argjson queries "$queries" --arg origin_fingerprint "$origin_fp" \
  '{run_id, scenario, target_arch: $arch, origins, preferences, package_rows, queries, origin_fingerprint: $origin_fingerprint}')
digest=$(graph_digest "$body")
echo "$body" | jq --arg d "$digest" '. + {graph_digest: $d}' > "${APP_ROOT}/state/deb822-policy-graph.json"
mkdir -p "${APP_ROOT}/work"
echo "$body" > "${APP_ROOT}/work/${run_id}-policy-build.json"
echo "built policy graph for ${scenario} run ${run_id}"
