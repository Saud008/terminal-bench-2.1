#!/usr/bin/env bash

expand_zone_units() {
  local tree="$1"
  local master_rel="$2"
  local origin="$3"
  python3 - "$tree" "$master_rel" "$origin" <<'PY'
import json, sys
from pathlib import Path

tree = Path(sys.argv[1])
master_rel = sys.argv[2]
origin = sys.argv[3]
processing_order = []
units = []
visited = set()

def walk(abs_path: Path, rel: str, cur_origin: str, depth: int):
    if depth > 16:
        raise ValueError("include depth exceeded")
    key = str(abs_path.resolve())
    if key in visited:
        return
    visited.add(key)
    cur_origin_local = cur_origin
    default_ttl = None
    file_recs = []
    for line_no, raw in enumerate(abs_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("$ORIGIN"):
            parts = line.split(None, 1)
            if len(parts) == 2:
                cur_origin_local = parts[1].strip()
            continue
        if line.startswith("$TTL"):
            parts = line.split(None, 1)
            if len(parts) == 2:
                default_ttl = int(parts[1].strip())
            continue
        if line.startswith("$INCLUDE"):
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            if file_recs:
                processing_order.append(rel)
                units.append({"file": rel, "records": file_recs})
                file_recs = []
            inc_abs = (abs_path.parent / parts[1].strip()).resolve()
            inc_rel = inc_abs.relative_to(tree).as_posix() if inc_abs.is_relative_to(tree) else parts[1].strip()
            if inc_abs.is_file():
                walk(inc_abs, inc_rel, cur_origin_local, depth + 1)
            continue
        tokens = line.split()
        if len(tokens) < 4:
            continue
        owner = tokens[0]
        idx = 1
        ttl = default_ttl if default_ttl is not None else 3600
        if tokens[idx].isdigit():
            ttl = int(tokens[idx])
            idx += 1
        if idx >= len(tokens) or tokens[idx] != "IN":
            continue
        idx += 1
        rtype = tokens[idx]
        idx += 1
        rdata = " ".join(tokens[idx:])
        file_recs.append({
            "owner": owner, "class": "IN", "type": rtype, "ttl": ttl,
            "rdata": rdata, "line": line_no, "origin": cur_origin_local,
        })
    if file_recs:
        processing_order.append(rel)
        units.append({"file": rel, "records": file_recs})

walk(tree / master_rel, master_rel, origin, 0)
print(json.dumps({"processing_order": processing_order, "units": units}))
PY
}
