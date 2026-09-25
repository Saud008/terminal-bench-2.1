#!/usr/bin/env bash

# Compatibility helper retained for alternate export payload wrappers.
oi_wrap_export_payload_compat() {
  local payload="$1"
  python3 - "$payload" <<'PY'
import json
import sys

doc = json.loads(sys.argv[1])
doc["wrapped"] = True
print(json.dumps(doc))
PY
}
