#!/usr/bin/env bash
# Topological mount ordering over the dependency->dependent graph.
#
# Kahn layer-by-layer with ASCII-ascending ordering inside each ready batch,
# producing a dependency-first mount order. On a cycle, walk from the
# lexicographically smallest remaining node following the lex-first outgoing
# neighbour, emitting the path (including the return to the start).
#
# Sets:
#   TOPO_ORDER   array with mount orde
#   TOPO_CYCLES  array with cycle path strings

topo_sort_mount_order() {
  local graph_file="$1"
  local staged_tsv="$2"
  local ofile cfile
  ofile="$(mktemp)"
  cfile="$(mktemp)"
  python3 - "${graph_file}" "${staged_tsv}" "${ofile}" "${cfile}" <<'PY'
import sys

graph_path, staged, order_path, cycle_path = sys.argv[1:5]

nodes = []
nodeset = set()
with open(staged, encoding="utf-8") as fh:
    for raw in fh:
        parts = raw.rstrip("\n").split("\t")
        if parts and parts[0] == "MOD":
            mid = parts[1] if len(parts) > 1 else ""
            if mid and mid not in nodeset:
                nodes.append(mid)
                nodeset.add(mid)

adj = {n: [] for n in nodes}
indeg = {n: 0 for n in nodes}
try:
    with open(graph_path, encoding="utf-8") as fh:
        for raw in fh:
            p = raw.rstrip("\n").split("\t")
            if len(p) < 2:
                continue
            a, b = p[0], p[1]
            adj.setdefault(a, []).append(b)
            indeg[b] = indeg.get(b, 0) + 1
except FileNotFoundError:
    pass

order = []
processed = set()
indeg2 = dict(indeg)
ready = sorted([n for n in nodes if indeg2.get(n, 0) == 0])
while ready:
    for n in ready:
        order.append(n)
        processed.add(n)
    new_ready = []
    for n in ready:
        for m in sorted(adj.get(n, [])):
            indeg2[m] -= 1
            if indeg2[m] == 0 and m not in processed:
                new_ready.append(m)
    ready = sorted(set(new_ready))

cycles = []
if len(processed) < len(nodes):
    remaining = sorted([n for n in nodes if n not in processed])
    start = remaining[0]
    path = []
    seen = {}
    cur = start
    while cur not in seen:
        seen[cur] = len(path)
        path.append(cur)
        nbrs = sorted(adj.get(cur, []))
        if not nbrs:
            break
        cur = nbrs[0]
    if cur in seen:
        idx = seen[cur]
        cyc = path[idx:] + [cur]
        cycles.append("->".join(cyc))

with open(order_path, "w", encoding="utf-8") as oh:
    for n in order:
        oh.write(n + "\n")
with open(cycle_path, "w", encoding="utf-8") as ch:
    for c in cycles:
        ch.write(c + "\n")
PY
  TOPO_ORDER=()
  TOPO_CYCLES=()
  [[ -s "${ofile}" ]] && mapfile -t TOPO_ORDER < "${ofile}"
  [[ -s "${cfile}" ]] && mapfile -t TOPO_CYCLES < "${cfile}"
  rm -f "${ofile}" "${cfile}"
}
