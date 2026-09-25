#!/usr/bin/env bash
set -euo pipefail

pin_priority_for_pkg() {
  local prefs_json="$1"
  local pkg="$2"
  local ver="$3"
  local best=0
  while IFS= read -r pref; do
    [[ -z "$pref" ]] && continue
    pin_pkg=$(echo "$pref" | jq -r '.Package // "*"')
    [[ "$pin_pkg" != "*" && "$pin_pkg" != "$pkg" ]] && continue
    pin_field=$(echo "$pref" | jq -r '.Pin // ""')
    prio=$(echo "$pref" | jq -r '.["Pin-Priority"] // "0"')
    if [[ "$pin_field" == version* ]]; then
      pat="${pin_field#version }"
      match=$(python3 - <<'PY' "$ver" "$pat"
import fnmatch, sys
v = sys.argv[1].split("-")[0]
if ":" in v:
    v = v.split(":", 1)[1]
print("ok" if fnmatch.fnmatch(v, sys.argv[2]) else "no")
PY
)
      [[ "$match" == "ok" ]] || continue
    fi
    if (( prio > best )); then
      best=$prio
    fi
  done < <(echo "$prefs_json" | jq -c '.[]')
  echo "$best"
}
