#!/usr/bin/env bash
set -euo pipefail
LDAPRM_LIB="${LDAPRM_LIB:-/app/internal/dirauth}"
source "${LDAPRM_LIB}/dn/normalize.sh"

expand_group_closure() {
  local file="$1"
  python3 - "$file" <<'PY'
import sys
from pathlib import Path

def normalize_dn(dn):
    parts = []
    for rdn in dn.split(","):
        rdn = rdn.strip()
        if not rdn:
            continue
        if "=" in rdn:
            a, v = rdn.split("=", 1)
            parts.append(f"{a.strip().lower()}={v.strip()}")
        else:
            parts.append(rdn.lower())
    return ",".join(parts)

graph = {}
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    g, m = line.split("\t", 1)
    graph.setdefault(normalize_dn(g), set()).add(normalize_dn(m))

cache = {}
def members(node, stack):
    if node in cache:
        return cache[node]
    if node in stack:
        return set()
    stack = set(stack)
    stack.add(node)
    out = set()
    for m in graph.get(node, set()):
        if m in graph:
            out |= members(m, stack)
        else:
            out.add(m)
    cache[node] = out
    return out

for g in sorted(graph):
    for m in sorted(members(g, set())):
        print(f"{g}|{m}")
PY
}
