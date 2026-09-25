#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_analyze_uid_graph() {
  local merged_json="$1"
  python3 - "${merged_json}" <<'PY'
import json, re, sys

merged = json.loads(sys.argv[1])
uid_re = re.compile(r'uid="(uid://[^"]+)"')
root_uids = {}
edges = []

for rel, text in merged.items():
    for line in text.splitlines():
        if line.startswith("[gd_scene") and 'uid="' in line:
            m = uid_re.search(line)
            if m:
                root_uids[rel] = m.group(1)
            break

for rel, text in merged.items():
    src = root_uids.get(rel)
    if not src:
        continue
    for line in text.splitlines():
        if not line.startswith("[ext_resource"):
            continue
        if 'type="PackedScene"' not in line:
            continue
        m = uid_re.search(line)
        if m:
            edges.append((src, m.group(1)))

graph = {}
for a, b in edges:
    graph.setdefault(a, set()).add(b)

cycles = []
visited = set()
stack = set()
path = []

def dfs(node):
    if node in stack:
        idx = path.index(node)
        cycles.append(path[idx:] + [node])
        return
    if node in visited:
        return
    visited.add(node)
    stack.add(node)
    path.append(node)
    for nxt in graph.get(node, ()):
        dfs(nxt)
    path.pop()
    stack.remove(node)

for node in graph:
    dfs(node)

uid_graph_ok = len(cycles) == 0
print(json.dumps({"uid_graph_ok": uid_graph_ok, "cycles": cycles}))
PY
}
