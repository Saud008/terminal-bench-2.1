#!/usr/bin/env bash
# Build unit dependency DAG and topological order.

set -euo pipefail

source /app/lib/common.sh
source /app/lib/parse.sh

detect_cycle() {
  local parse_json="$1"
  python3 - "${parse_json}" <<'PY'
import json, sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
units = data["units"]
names = sorted(units.keys())

edges = {n: set() for n in names}
for unit, meta in units.items():
    u = meta.get("unit", {})
    for key in ("After", "Wants"):
        for dep in u.get(key, []):
            if dep in names and dep != unit:
                edges[unit].add(dep)
                edges[dep].add(unit)

state = {}
stack = []
cycle = []

def dfs(node):
    state[node] = 1
    stack.append(node)
    for nxt in sorted(edges.get(node, [])):
        if nxt not in state:
            dfs(nxt)
        elif state[nxt] == 1:
            i = stack.index(nxt)
            cycle.extend(stack[i:] + [nxt])
            return
    state[node] = 2
    stack.pop()

for node in names:
    if node not in state:
        dfs(node)
    if cycle:
        print(",".join(cycle))
        sys.exit(0)
print("")
PY
}

topo_order() {
  local parse_json="$1"
  python3 - "${parse_json}" <<'PY'
import json, sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
names = sorted(data["units"].keys(), reverse=True)
print(json.dumps({"tree": data["tree"], "order": names}))
PY
}

run_order() {
  local tree="$1"
  local out="$2"
  local tmp
  tmp="$(mktemp)"
  run_parse "${tree}" "${tmp}"
  local cycle
  cycle="$(detect_cycle "${tmp}")"
  if [[ -n "${cycle}" ]]; then
    echo "cycle:${cycle}" >&2
    rm -f "${tmp}"
    return 2
  fi
  topo_order "${tmp}" > "${out}"
  rm -f "${tmp}"
  return 0
}
