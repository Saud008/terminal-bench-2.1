#!/usr/bin/env bash
# Ingest stage: parse manifest VDF and commit staging artifacts.

ingest_manifest_to_staging() {
  local manifest_file="$1"
  # shellcheck source=/app/lib/vdf_parse.sh
  source /app/lib/vdf_parse.sh
  mkdir -p /app/output
  vdf_parse_manifest "${manifest_file}" > /app/output/parsed-manifest.tsv
}
