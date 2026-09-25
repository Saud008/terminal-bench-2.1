#!/usr/bin/env bash

parse_zone_file() {
  local path="$1"
  local origin="${2:-}"
  python3 - "$path" "$origin" <<'PY'
import json, re, sys
from pathlib import Path

path = Path(sys.argv[1])
origin = sys.argv[2]
records = []
directives = {"includes": [], "origin": origin, "ttl": None}
errors = []
for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
    line = raw.strip()
    if not line or line.startswith(";"):
        continue
    if line.startswith("$ORIGIN"):
        parts = line.split(None, 1)
        if len(parts) == 2:
            directives["origin"] = parts[1].strip()
        continue
    if line.startswith("$TTL"):
        parts = line.split(None, 1)
        if len(parts) == 2:
            try:
                directives["ttl"] = int(parts[1].strip())
            except ValueError:
                errors.append({"line": line_no, "reason": "bad_ttl"})
        continue
    if line.startswith("$INCLUDE"):
        parts = line.split(None, 1)
        if len(parts) != 2:
            errors.append({"line": line_no, "reason": "bad_include"})
            continue
        directives["includes"].append({"path": parts[1].strip(), "line": line_no})
        continue
    tokens = line.split()
    if len(tokens) < 4:
        errors.append({"line": line_no, "reason": "malformed_rr"})
        continue
    owner = tokens[0]
    idx = 1
    ttl = directives["ttl"]
    if tokens[idx].isdigit():
        ttl = int(tokens[idx])
        idx += 1
    if idx >= len(tokens) or tokens[idx] != "IN":
        errors.append({"line": line_no, "reason": "missing_class"})
        continue
    idx += 1
    if idx >= len(tokens):
        errors.append({"line": line_no, "reason": "missing_type"})
        continue
    rrtype = tokens[idx]
    idx += 1
    rdata = " ".join(tokens[idx:])
    records.append({
        "owner": owner,
        "class": "IN",
        "type": rrtype,
        "ttl": ttl if ttl is not None else 3600,
        "rdata": rdata,
        "line": line_no,
        "origin": directives["origin"],
    })
print(json.dumps({"file": str(path), "records": records, "includes": directives["includes"], "errors": errors}))
PY
}
