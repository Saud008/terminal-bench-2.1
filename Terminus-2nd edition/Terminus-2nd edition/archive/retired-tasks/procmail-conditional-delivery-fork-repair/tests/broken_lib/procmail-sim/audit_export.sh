#!/usr/bin/env bash
# Audit JSON export from a delivery snapshot file.
audit_write() {
  local snapshot_path="$1"
  local out_path="$2"
  local raw
  raw="$(cat "$snapshot_path")"
  jq -n \
    --argjson snap "$raw" \
    --arg sha "$(sha256sum "$snapshot_path" | awk '{print $1}')" \
    '{
      audit_version: 1,
      suite_id: $snap.suite_id,
      environment: $snap.environment,
      stats: $snap.stats,
      deliveries: $snap.deliveries,
      skipped_recipes: [],
      snapshot_sha256: $sha
    }' >"$out_path"
}
