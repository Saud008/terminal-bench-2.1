#!/usr/bin/env bash
# Ingest stage: parse manifest VDF and commit staging artifacts.

ingest_manifest_to_staging() {
  local manifest_file="$1"
  local parsed_file
  parsed_file="$(mktemp)"
  # shellcheck source=/app/lib/vdf_parse.sh
  source /app/lib/vdf_parse.sh
  vdf_parse_manifest "${manifest_file}" > "${parsed_file}"
  # shellcheck source=/app/lib/staging.sh
  source /app/lib/staging.sh
  staging_commit_parsed "${parsed_file}"
  rm -f "${parsed_file}"
}
