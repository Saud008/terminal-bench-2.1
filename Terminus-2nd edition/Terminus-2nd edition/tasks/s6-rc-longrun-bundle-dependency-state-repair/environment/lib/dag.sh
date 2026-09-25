#!/usr/bin/env bash
# DAG validation and topological plan.

set -euo pipefail

source /app/lib/common.sh
source /app/lib/ingest.sh

detect_cycle() {
  local bundle_json="$1"
  python3 - "${bundle_json}" <<'PY'
import json, sys
from pathlib import Path

bundle = json.loads(Path(sys.argv[1]).read_text())
names = [s["name"] for s in bundle["services"]]
edges = {n: set() for n in names}
for child, parent in bundle.get("hard_deps", []):
    if child in names and parent in names and child != parent:
        edges[child].add(parent)

state = {}
stack = []
cycle = []

def dfs(node):
    state[node] = 1
    stack.append(node)
    for dep in sorted(edges.get(node, set())):
        if dep not in state:
            dfs(dep)
        elif state[dep] == 1:
            i = stack.index(dep)
            cycle.extend(stack[i:] + [dep])
            return
    state[node] = 2
    stack.pop()

for node in sorted(names):
    if node not in state:
        dfs(node)
    if cycle:
        print(",".join(cycle))
        sys.exit(0)
print("")
PY
}

topo_plan() {
  local bundle_json="$1"
  python3 - "${bundle_json}" <<'PY'
import json, sys
from pathlib import Path

bundle = json.loads(Path(sys.argv[1]).read_text())
names = sorted(s["name"] for s in bundle["services"])
print(json.dumps({"bundle": bundle["name"], "order": names}))
PY
}

run_validate() {
  local tree="$1"
  local bundle="$2"
  local tmp
  tmp="$(mktemp)"
  load_bundle "${tree}" "${bundle}" > "${tmp}"
  rm -f "${tmp}"
  return 0
}

run_plan() {
  local tree="$1"
  local bundle="$2"
  local out="$3"
  local tmp
  tmp="$(mktemp)"
  load_bundle "${tree}" "${bundle}" > "${tmp}"
  topo_plan "${tmp}" > "${out}"
  rm -f "${tmp}"
  return 0
}

run_validate_with_cycle() {
  local tree="$1"
  local bundle="$2"
  local tmp cycle
  tmp="$(mktemp)"
  load_bundle "${tree}" "${bundle}" > "${tmp}"
  cycle="$(detect_cycle "${tmp}")"
  rm -f "${tmp}"
  if [[ -n "${cycle}" ]]; then
    echo "cycle:${cycle}" >&2
    return 2
  fi
  return 0
}
