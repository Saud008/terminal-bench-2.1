#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

config_dir="$1"
reload_mode="${2:-full}"

filters="$(config_path "$config_dir" filters.conf)"
graph="$(config_path "$config_dir" graph.conf)"
rewrites="$(config_path "$config_dir" rewrites.conf)"

new_hash="$(cat "$filters" "$graph" "$rewrites" | sha256sum | awk '{print $1}')"
old_hash=""
if [ -f "$(hash_file)" ]; then
  old_hash="$(cat "$(hash_file)")"
fi

reuse=0
if [ "$reload_mode" = "full" ]; then
  reuse=0
elif [ "$new_hash" = "$old_hash" ] && [ -f "$(cache_file)" ]; then
  reuse=1
else
  reuse=0
fi

if [ "$reuse" -eq 1 ]; then
  echo "reuse"
else
  echo "$new_hash" > "$(hash_file)"
  tmp_prune="$(mktemp)"
  tmp_branch="$(mktemp)"
  bash /app/lib/prune.sh "$config_dir" "$tmp_prune"
  bash /app/lib/branch.sh "$config_dir" "$tmp_prune" "$tmp_branch"
  mv "$tmp_branch" "$(cache_file)"
  rm -f "$tmp_prune"
  echo "rebuild"
fi
