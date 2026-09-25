#!/usr/bin/env bash
set -euo pipefail

ensure_runtime_dirs() {
  mkdir -p /app/state /app/output
}

sha256_hex() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}

iso_to_epoch() {
  date -u -d "$1" +%s 2>/dev/null || date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$1" +%s
}

days_between() {
  local start="$1" end="$2"
  local se ee
  se="$(iso_to_epoch "${start}T00:00:00Z")"
  ee="$(iso_to_epoch "${end}T00:00:00Z")"
  echo $(( (ee - se) / 86400 ))
}

days_in_month() {
  local ymd="$1"
  local y m
  y="${ymd%%-*}"
  m="${ymd#*-}"; m="${m%%-*}"
  date -u -d "${y}-${m}-01 +1 month -1 day" +%d 2>/dev/null || echo 30
}

money2() {
  printf '%.2f' "$1"
}
