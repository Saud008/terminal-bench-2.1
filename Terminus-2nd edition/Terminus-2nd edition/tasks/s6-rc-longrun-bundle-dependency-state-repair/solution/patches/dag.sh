#!/usr/bin/env bash
# DAG validation and topological plan (fixed).

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
edges = {n: [] for n in names}
for child, parent in bundle.get("hard_deps", []):
    if child in names and parent in names and child != parent:
        edges[child].append(parent)
for unit in edges:
    edges[unit].sort()
indeg = {n: 0 for n in names}
children = {n: [] for n in names}
for unit, deps in edges.items():
    for dep in deps:
        children[dep].append(unit)
        indeg[unit] += 1
queue = sorted(n for n in names if indeg[n] == 0)
order = []
while queue:
    node = queue.pop(0)
    order.append(node)
    for child in sorted(children.get(node, [])):
        indeg[child] -= 1
        if indeg[child] == 0:
            queue.append(child)
            queue.sort()
print(json.dumps({"bundle": bundle["name"], "order": order}))
PY
}

run_validate() {
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

run_plan() {
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
  topo_plan "${tmp}" > "${out}"
  rm -f "${tmp}"
  return 0
}

run_validate_with_cycle() {
  run_validate "$@"
}
