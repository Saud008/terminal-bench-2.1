#!/usr/bin/env bash

: "${SPAM_SPOOL:=/app/work/spool/spam}"
: "${VIRUS_SPOOL:=/app/work/spool/virus}"
: "${RELEASED_SPAM:=/app/work/released/spam}"
: "${RELEASED_VIRUS:=/app/work/released/virus}"
: "${MANIFEST_PATH:=/app/state/spool-manifest.json}"


ingest_scenario() {
  local scenario_dir="$1"
  rm -rf "$SPAM_SPOOL"/* "$VIRUS_SPOOL"/* "$RELEASED_SPAM"/* "$RELEASED_VIRUS"/*
  mkdir -p "$SPAM_SPOOL" "$VIRUS_SPOOL" "$RELEASED_SPAM" "$RELEASED_VIRUS" /app/state
  shopt -s nullglob
  local f
  for f in "${scenario_dir}/spool/spam/"*; do
    [[ -e "$f" ]] && cp -a "$f" "$SPAM_SPOOL/"
  done
  for f in "${scenario_dir}/spool/virus/"*; do
    [[ -e "$f" ]] && cp -a "$f" "$VIRUS_SPOOL/"
  done
  shopt -u nullglob
  echo '{"messages":[]}' > "$MANIFEST_PATH"
}
