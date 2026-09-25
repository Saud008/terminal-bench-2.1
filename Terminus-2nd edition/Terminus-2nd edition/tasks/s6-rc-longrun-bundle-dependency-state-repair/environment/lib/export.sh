#!/usr/bin/env bash
# Export effective service graph.

set -euo pipefail

source /app/lib/common.sh
source /app/lib/ingest.sh
source /app/lib/dag.sh

run_export() {
  local tree="$1"
  local bundle="$2"
  local out="$3"
  local tmp cycle
  tmp="$(mktemp)"
  load_bundle "${tree}" "${bundle}" > "${tmp}"
  cycle="$(detect_cycle "${tmp}")"
  if [[ -n "${cycle}" ]]; then
    echo "cycle:${cycle}" >&2
    rm -f "${tmp}"
    return 2
  fi
  python3 - "${tmp}" > "${out}" <<'PY'
import json, sys
from pathlib import Path

bundle = json.loads(Path(sys.argv[1]).read_text())
nodes = sorted(s["name"] for s in bundle["services"])
edges = []
for child, parent in bundle.get("hard_deps", []):
    edges.append({"from": child, "to": parent, "kind": "hard"})
edges.sort(key=lambda e: (e["from"], e["to"], e["kind"]))
print(json.dumps({
    "bundle": bundle["name"],
    "nodes": nodes,
    "edges": edges,
    "edge_count": len(edges),
}, indent=2))
PY
  rm -f "${tmp}"
  return 0
}
