#!/usr/bin/env bash

wt_die() {
  echo "wtstatus-export: $*" >&2
  exit 1
}

wt_require_file() {
  local path="$1"
  [[ -f "${path}" ]] || wt_die "missing file: ${path}"
}

wt_json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<<"$1"
}
