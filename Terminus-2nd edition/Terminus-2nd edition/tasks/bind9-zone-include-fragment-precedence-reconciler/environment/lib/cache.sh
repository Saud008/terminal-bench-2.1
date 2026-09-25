#!/usr/bin/env bash

CACHE_DIR="${ZONE_CACHE_DIR:-/app/state/.zone-cache}"

# Zone compile cache keys and invalidation helpers.
zone_cache_key() {
  local tree="$1"
  local seed="$2"
  python3 - "$tree" "$seed" <<'PY'
import hashlib, sys
from pathlib import Path

tree, seed = sys.argv[1], sys.argv[2]
print(hashlib.sha256(f"{tree}:{seed}".encode()).hexdigest())
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
  python3 - "$tree" <<'PY'
import hashlib, json, sys
from pathlib import Path

tree = Path(sys.argv[1])
manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
master = manifest["master"]
parts = [master]
for zone in sorted(tree.rglob("*.zone")):
    rel = zone.relative_to(tree).as_posix()
    if rel == master:
        continue
    parts.append(f"{rel}:{hashlib.sha256(zone.read_bytes()).hexdigest()[:16]}")
print(hashlib.sha256("|".join(parts).encode()).hexdigest())
PY
}
