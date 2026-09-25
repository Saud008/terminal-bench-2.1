#!/usr/bin/env bash

die() {
  echo "zonefrag: $*" >&2
  exit "${2:-1}"
}

json_get() {
  python3 - "$@" <<'PY'
import json, sys
doc = json.loads(open(sys.argv[1], encoding="utf-8").read())
for key in sys.argv[2:]:
    doc = doc[key]
print(doc if not isinstance(doc, (dict, list)) else json.dumps(doc))
PY
}
