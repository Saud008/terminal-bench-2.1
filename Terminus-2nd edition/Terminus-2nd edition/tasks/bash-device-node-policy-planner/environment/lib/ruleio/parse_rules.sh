#!/usr/bin/env bash
# Parse udev rule files into JSON rule records
set -euo pipefail

UDEV_LIB="${UDEV_LIB:-/app/lib}"
# shellcheck source=../common.sh
source "${UDEV_LIB}/common.sh"

parse_rules_dir() {
  local rules_dir="$1"
  local file_idx=0
  local rules_json='[]'
  local rules_file
  trim_ws() {
    local s="$1"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    printf '%s' "$s"
  }
  while IFS= read -r -d '' rules_file; do
    local base
    base="$(basename "$rules_file")"
    local line_no=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      line_no=$((line_no + 1))
      line="${line%%#*}"
      line="$(trim_ws "$line")"
      [[ -z "$line" ]] && continue
      local priority=$((1000 + file_idx * 100 + line_no))
      local rule_id="${base}:${line_no}"
      local tokens_json='{}'
      IFS=',' read -ra parts <<< "$line"
      for part in "${parts[@]}"; do
        part="$(trim_ws "$part")"
        if [[ "$part" =~ ^OPTIONS\+=\"priority=([0-9]+)\"$ ]]; then
          priority="${BASH_REMATCH[1]}"
        elif [[ "$part" =~ ^ATTR\{([^}]+)\}==\"(.*)\"$ ]]; then
          tokens_json="$(jq -c --arg k "ATTR:${BASH_REMATCH[1]}" --arg v "${BASH_REMATCH[2]}" '. + {($k): $v}' <<< "$tokens_json")"
        elif [[ "$part" =~ ^([A-Z_]+)\+=\"(.*)\"$ ]]; then
          local key="${BASH_REMATCH[1]}"
          local val="${BASH_REMATCH[2]}"
          if [[ "$key" == "SYMLINK" ]] && jq -e '.SYMLINK' <<< "$tokens_json" >/dev/null 2>&1; then
            tokens_json="$(jq -c --arg v "$val" '.SYMLINK += [$v]' <<< "$tokens_json")"
          elif [[ "$key" == "SYMLINK" ]]; then
            tokens_json="$(jq -c --arg v "$val" '. + {SYMLINK: [$v]}' <<< "$tokens_json")"
          else
            tokens_json="$(jq -c --arg k "$key" --arg v "$val" '. + {($k): $v}' <<< "$tokens_json")"
          fi
        elif [[ "$part" =~ ^([A-Z_]+)==\"(.*)\"$ ]]; then
          local key="${BASH_REMATCH[1]}"
          local val="${BASH_REMATCH[2]}"
          tokens_json="$(jq -c --arg k "$key" --arg v "$val" '. + {($k): $v}' <<< "$tokens_json")"
        elif [[ "$part" =~ ^([A-Z_]+)=\"(.*)\"$ ]]; then
          local key="${BASH_REMATCH[1]}"
          local val="${BASH_REMATCH[2]}"
          tokens_json="$(jq -c --arg k "$key" --arg v "$val" '. + {($k): $v}' <<< "$tokens_json")"
        fi
      done
      rules_json="$(jq -c --argjson r "$rules_json" \
        --arg rid "$rule_id" --argjson pri "$priority" --arg sf "$base" --argjson ln "$line_no" \
        --argjson tok "$tokens_json" \
        '$r + [{rule_id:$rid,priority:$pri,source_file:$sf,line_number:$ln,tokens:$tok}]' <<< "$rules_json")"
    done < "$rules_file"
    file_idx=$((file_idx + 1))
  done < <(find "$rules_dir" -maxdepth 1 -type f -name '*.rules' -print0 | sort -z)
  jq -c '.' <<< "$rules_json"
}
