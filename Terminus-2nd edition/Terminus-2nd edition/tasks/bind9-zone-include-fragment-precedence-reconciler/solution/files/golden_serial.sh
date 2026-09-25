#!/usr/bin/env bash

bump_soa_serial() {
  local units_json="$1"
  local master_rel="$2"
  local reload_flag="$3"
  python3 - "$units_json" "$master_rel" "$reload_flag" <<'PY'
import json, sys

units = json.loads(sys.argv[1])
master_rel = sys.argv[2]
reload_flag = sys.argv[3] == "1"
serial = None
for unit in units:
    if unit["file"] != master_rel:
        continue
    for rec in unit.get("records", []):
        if rec["type"] == "SOA":
            parts = rec["rdata"].split()
            if len(parts) >= 3 and parts[2].isdigit():
                serial = int(parts[2])
            break
if serial is None:
    serial = 0
source = master_rel
if reload_flag:
    serial += 1
print(json.dumps({"soa_serial": serial, "soa_source": source}))
PY
}
