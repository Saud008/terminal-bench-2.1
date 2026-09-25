#!/usr/bin/env bash

CACHE_DIR="${ZONE_CACHE_DIR:-/app/state/.zone-cache}"

zone_cache_key() {
  local tree="$1"
  local seed="$2"
  local fp="$3"
  local reload_flag="${4:-0}"
  python3 - "$tree" "$seed" "$fp" "$reload_flag" <<'PY'
import hashlib, sys
tree, seed, fp, reload_flag = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
print(hashlib.sha256(f"{tree}:{seed}:{fp}:{reload_flag}".encode()).hexdigest())
PY
}

zone_cache_get() {
  local key="$1"
  local path="${CACHE_DIR}/${key}.json"
  if [[ -f "$path" ]]; then
    cat "$path"
    return 0
  fi
  echo "{}"
}

zone_cache_put() {
  local key="$1"
  local body="$2"
  mkdir -p "$CACHE_DIR"
  printf '%s\n' "$body" > "${CACHE_DIR}/${key}.json"
}

include_fingerprint() {
  local tree="$1"
  local master_rel="$2"
  python3 - "$tree" "$master_rel" <<'PY'
import hashlib, json, sys
from pathlib import Path

tree = Path(sys.argv[1])
master = sys.argv[2]
parts = [master]
for zone in sorted(tree.rglob("*.zone")):
    rel = zone.relative_to(tree).as_posix()
    if rel == master:
        continue
    parts.append(f"{rel}:{hashlib.sha256(zone.read_bytes()).hexdigest()[:16]}")
print(hashlib.sha256("|".join(parts).encode()).hexdigest())
PY
}
