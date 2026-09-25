#!/usr/bin/env bash
set -euo pipefail

ensure_runtime_dirs() {
  mkdir -p /app/state /app/output
}

read_scan_generation() {
  local f="/app/state/scan_generation.txt"
  if [[ -f "$f" ]]; then
    cat "$f"
  else
    echo "0"
  fi
}

write_scan_generation() {
  echo "$1" > /app/state/scan_generation.txt
}

sha256_hex() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}

fnmatch_case() {
  local pattern="$1" value="$2"
  shopt -s nocasematch
  [[ "$value" == $pattern ]]
  local rc=$?
  shopt -u nocasematch
  return "$rc"
}

principal_specificity() {
  local principal="$1"
  local score=1000
  if [[ "$principal" == *"@"* ]]; then
    score=200
  fi
  if [[ "$principal" == *"*"* || "$principal" == *"?"* ]]; then
    score=400
  fi
  if [[ "$principal" != *"*"* && "$principal" != *"?"* ]]; then
    score=50
  fi
  echo "$score"
}

principal_wildcard_bad() {
  local principal="$1"
  if [[ "$principal" == *"**"* ]]; then
    return 0
  fi
  local left="${principal%%@*}"
  local right="${principal#*@}"
  if [[ "$principal" == *"@"* ]]; then
    if [[ "$left" == *"*"* && "$left" != "*" ]]; then
      return 0
    fi
    if [[ "$right" == *"*"* && "$right" != *".*"* && "$right" != "*" ]]; then
      if [[ "$right" == *"*"* ]]; then
        local after="${right#*\*}"
        [[ -n "$after" && "$after" != "$right" ]] && return 0
      fi
    fi
  else
    if [[ "$principal" == *"*"* && "$principal" != "*" ]]; then
      return 0
    fi
  fi
  return 1
}
