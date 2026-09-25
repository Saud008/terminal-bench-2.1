#!/usr/bin/env bash
set -euo pipefail

UDEV_LIB="${UDEV_LIB:-/app/lib}"

sha256_lines() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}

glob_match() {
  local pattern="$1"
  local value="$2"
  case "$value" in
    $pattern) return 0 ;;
    *) return 1 ;;
  esac
}

ensure_state_dir() {
  mkdir -p /app/state /app/output
}

read_replay_seq() {
  local f="/app/state/replay.seq"
  if [[ -f "$f" ]]; then
    tr -d '[:space:]' < "$f"
  else
    echo 0
  fi
}

write_replay_seq() {
  local val="$1"
  ensure_state_dir
  printf '%s\n' "$val" > /app/state/replay.seq
}
