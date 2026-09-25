#!/usr/bin/env bash

merge_records_from_units() {
  local units_json="$1"
  python3 - "$units_json" <<'PY'
import json, sys

units = json.loads(sys.argv[1])
merged = {}
sources = {}
order = []
for unit in units:
    for rec in unit.get("records", []):
        key = (rec["owner"], rec["class"], rec["type"])
        merged[key] = rec
        sources["/".join(key)] = {"file": unit["file"], "line": rec["line"]}
        order.append(key)
records = list(merged.values())
print(json.dumps({"records": records, "sources": sources}))
PY
}

build_snapshot() {
  local tree="$1"
  local seed="$2"
  local snap="$3"
  local reload="${4:-0}"
  python3 - "$tree" "$seed" "$snap" "$reload" <<'PY'
import json, subprocess, sys
from pathlib import Path

tree = Path(sys.argv[1])
seed = sys.argv[2]
snap = Path(sys.argv[3])
reload_flag = sys.argv[4]

manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
origin = manifest.get("origin", "example.com.")

def bash_fn(script, fn, *args):
    cmd = ["bash", "-c", f'source /app/lib/common.sh; source /app/lib/{script}; {fn} "$@"', "bash", *args]
    return subprocess.check_output(cmd, text=True).strip()

cache_key = bash_fn("cache.sh", "zone_cache_key", str(tree), seed)
cached = json.loads(bash_fn("cache.sh", "zone_cache_get", cache_key))
if cached.get("zone_hash") and cached.get("include_fingerprint"):
    fp = bash_fn("cache.sh", "include_fingerprint", str(tree))
    if cached.get("include_fingerprint") == fp:
        snap.parent.mkdir(parents=True, exist_ok=True)
        snap.write_text(json.dumps(cached, indent=2) + "\n", encoding="utf-8")
        sys.exit(0)

expanded = json.loads(bash_fn("include.sh", "expand_zone_units", str(tree), manifest["master"], origin))
units = expanded["units"]
merged = json.loads(bash_fn("merge.sh", "merge_records_from_units", json.dumps(units)))
records = merged["records"]

wild = json.loads(bash_fn("wildcard.sh", "detect_wildcard_apex_overlap", json.dumps(units[-1]["records"] if units else [])))
serial = json.loads(bash_fn("serial.sh", "bump_soa_serial", json.dumps(units), manifest["master"], reload_flag))
nsec = json.loads(bash_fn("nsec.sh", "validate_nsec_chain", json.dumps(units)))
fp = bash_fn("cache.sh", "include_fingerprint", str(tree))

for rec in records:
    if rec["type"] == "SOA" and reload_flag == "1":
        parts = rec["rdata"].split()
        if parts:
            parts[0] = str(serial["soa_serial"])
            rec["rdata"] = " ".join(parts)

doc = {
    "snapshot_version": 1,
    "tree_path": str(tree),
    "tree": tree.name,
    "seed": seed,
    "origin": origin,
    "processing_order": expanded["processing_order"],
    "records": records,
    "sources": merged["sources"],
    "wildcard_conflicts": wild,
    "soa_serial": serial["soa_serial"],
    "soa_source": serial["soa_source"],
    "nsec_valid": nsec["valid"],
    "nsec_breaks": nsec.get("breaks", []),
    "include_fingerprint": fp,
    "stats": {
        "records": len(records),
        "units": len(units),
        "wildcard_conflicts": len(wild),
    },
}
import hashlib
doc["zone_hash"] = hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

snap.parent.mkdir(parents=True, exist_ok=True)
snap.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
bash_fn("cache.sh", "zone_cache_put", cache_key, json.dumps(doc))
PY
  write_merge_staging "$snap"
}
