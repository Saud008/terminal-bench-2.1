#!/usr/bin/env bash

state_dir() {
  echo "/app/state"
}

cache_file() {
  echo "$(state_dir)/pruned-graph.cache"
}

hash_file() {
  echo "$(state_dir)/config.hash"
}

snapshot_file() {
  echo "$(state_dir)/routing-snapshot.json"
}

deliveries_file() {
  echo "$(state_dir)/deliveries.tsv"
}

ensure_state_files() {
  mkdir -p "$(state_dir)" /app/output /app/tmp
  : > "$(deliveries_file)"
}

config_path() {
  local dir="$1"
  local name="$2"
  echo "${dir%/}/${name}"
}
