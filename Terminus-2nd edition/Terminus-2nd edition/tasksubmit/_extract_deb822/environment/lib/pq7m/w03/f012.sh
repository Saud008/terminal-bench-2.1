#!/usr/bin/env bash
set -euo pipefail

effective_pin() {
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
      # Baseline uses prefix match for version pins.
      if [[ "$ver" != "$pat"* ]]; then
        continue
      fi
    fi
    if (( prio > best )); then
      best=$prio
    fi
  done < <(echo "$prefs_json" | jq -c '.[]')
  echo "$best"
}
