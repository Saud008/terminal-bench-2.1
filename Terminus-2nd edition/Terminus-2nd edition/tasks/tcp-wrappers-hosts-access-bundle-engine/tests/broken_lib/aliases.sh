#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

load_alias_map() {
  local root="$1"
  local alias_file="${root}/daemon-aliases.json"
  if [[ ! -f "$alias_file" ]]; then
    manifest="$(read_manifest "$root")"
    alias_rel="$(python3 - "$alias_file" "$manifest" <<'PY'
import json, sys, os
root, manifest_path = sys.argv[1], sys.argv[2]
manifest = json.load(open(manifest_path, encoding="utf-8"))
rel = manifest.get("daemon_aliases", "")
print(os.path.join(os.path.dirname(manifest_path), rel) if rel else "")
PY
)"
    if [[ -n "$alias_rel" && -f "$alias_rel" ]]; then
      alias_file="$alias_rel"
    fi
  fi
  python3 - "$alias_file" <<'PY'
import json, sys, os
path = sys.argv[1]
if not os.path.isfile(path):
    print("{}")
else:
    print(json.dumps(json.load(open(path, encoding="utf-8"))))
PY
}

canonical_daemon() {
  local alias_json="$1"
  local name="$2"
  python3 - "$alias_json" "$name" <<'PY'
import json, sys
aliases = json.loads(sys.argv[1])
name = sys.argv[2]
for canon, spellings in aliases.items():
    if name == canon or name in spellings:
        print(canon)
        raise SystemExit
print(name)
PY
}

daemon_rule_match() {
  local alias_json="$1"
  local query="$2"
  local rule_daemon="$3"
  local canon
  canon="$(canonical_daemon "$alias_json" "$query")"
  if [[ "$rule_daemon" == "ALL" ]]; then
    return 0
  fi
  [[ "$rule_daemon" == "$canon" ]]
}

expand_rule_daemons() {
  local alias_json="$1"
  local csv="$2"
  python3 - "$alias_json" "$csv" <<'PY'
import json, sys
aliases = json.loads(sys.argv[1])
raw = [p.strip() for p in sys.argv[2].split(",") if p.strip()]
out = []
for token in raw:
    if token == "ALL":
        out.append("ALL")
        continue
    canon = token
    for key, vals in aliases.items():
        if token == key or token in vals:
            canon = key
            break
    if canon not in out:
        out.append(canon)
print(json.dumps(out))
PY
}
