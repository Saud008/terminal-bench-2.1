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
    g, m = normalize_dn(g), normalize_dn(m)
    graph.setdefault(g, set()).add(m)
    print(f"{g}|{m}")
PY
}
