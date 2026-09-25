#!/usr/bin/env bash

format_nevra() {
  local epoch="$1"
  local name="$2"
  local ver="$3"
  local rel="$4"
  local arch="$5"
  printf '%s-%s-%s.%s' "$name" "$ver" "$rel" "$arch"
}

parse_primary_packages() {
  local primary_xml="$1"
  python3 - "$primary_xml" <<'PY'
import json, sys
import xml.etree.ElementTree as ET
NS = "{http://linux.duke.edu/metadata/common}"
root = ET.parse(sys.argv[1]).getroot()
rows = []
for pkg in root.findall(f"{NS}package"):
    name = pkg.findtext(f"{NS}name", default="")
    arch = pkg.findtext(f"{NS}arch", default="")
    ver = pkg.find(f"{NS}version")
    epoch = ver.get("epoch", "0") if ver is not None else "0"
    version = ver.get("ver", "") if ver is not None else ""
    release = ver.get("rel", "") if ver is not None else ""
    rows.append({
        "name": name,
        "epoch": int(epoch),
        "version": version,
        "release": release,
        "arch": arch,
    })
print(json.dumps(rows))
PY
}
