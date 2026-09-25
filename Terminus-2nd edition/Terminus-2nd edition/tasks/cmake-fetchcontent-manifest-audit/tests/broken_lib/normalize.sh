#!/usr/bin/env bash
# Path normalization helpers.

normalize_rel() {
  local raw="$1"
  raw="${raw//\\//}"
  while [[ "$raw" == ./* ]]; do raw="${raw#./}"; done
  while [[ "$raw" == ../* ]]; do raw="${raw#../}"; done
  echo "$raw"
}

join_rel() {
  local base="$1"
  local rel="$2"
  if [[ "$rel" == /* ]]; then
    echo "$(normalize_rel "${rel#/}")"
    return
  fi
  echo "$(normalize_rel "${base%/}/${rel}")"
}
